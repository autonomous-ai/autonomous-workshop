"""Telegram — Dee's kill switch and taste channel, nothing more.

CONTRACTS §2: `send(text, buttons=None)` and `poll_decisions()`. The design
stance comes from ARCHITECTURE.md: the human "is a kill switch and a taste
signal, not a turnstile". So this module never blocks the pipeline waiting
for a reply, and it never EXECUTES a decision — it parses, state-checks, and
returns them. Execution belongs to the caller (bob.py / harness.send): a chat
parser that can unpublish a game by itself is one regex bug away from being
an unaudited write path into the queue.

The closed verb set {unpublish, park, note} is a wall, not a convention:
vibe-ideas took a stray Telegram tap as a state command once — the fix that
stuck was (a) refusing every verb outside a tiny allowlist and (b) stripping
the inline keyboard the moment a button is tapped, so a week-old message
can't fire a week-stale command twice (the stale-button receipt).

No-op mode: with BOB_TELEGRAM_TOKEN/BOB_TELEGRAM_CHAT unset, send() warns on
stderr and returns None (CONTRACTS §2). Bob must run headless without creds;
a missing notifier is a degraded mode, never a crash.

All network goes through one `_http()` seam so tests monkeypatch it and
never touch api.telegram.org.
"""

import json
import os
import sys
import urllib.error
import urllib.request

from harness import queue

# The ONLY verbs a chat message may fire. Everything else is refused with a
# reason (valid=False) so the daybook shows the attempt — refused, not
# silently dropped, per CONTRACTS §6 "every error message says what to do".
VERBS = frozenset(["unpublish", "park", "note"])

# getUpdates offset ledger. A lost offset re-delivers old updates; a
# re-delivered "unpublish" is exactly the replay the state checks below
# exist to absorb, so plain best-effort persistence is enough.
OFFSET_FILE = ".tg-offset"

# 30s: Telegram answers sendMessage in well under a second; a hung socket
# should fail the tick, not stall the 30-min launchd cadence.
HTTP_TIMEOUT_S = 30
SEND_PROJECTION_FILE = "send.json"
LEGACY_LAUNCH_PROJECTION_FILE = "launch.json"
LEGACY_PUBLICATION_PROJECTION_FILE = "published.json"

# v0.2 source compatibility for operator scripts.
LAUNCH_PROJECTION_FILE = LEGACY_LAUNCH_PROJECTION_FILE


def _home():
    # Env read inside functions, never at import (CONTRACTS §6).
    return os.environ.get("BOB_HOME") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))


def _creds():
    return (os.environ.get("BOB_TELEGRAM_TOKEN"),
            os.environ.get("BOB_TELEGRAM_CHAT"))


def _offset_path():
    return os.path.join(_home(), "state", OFFSET_FILE)


def _http(method, payload, token):
    """POST one Bot API method as JSON. Returns the decoded response dict.

    Single seam for ALL Telegram traffic (tests monkeypatch this). Errors
    return {"ok": False, "description": ...} instead of raising — a downed
    notifier must never kill a publish that already succeeded.
    """
    url = "https://api.telegram.org/bot%s/%s" % (token, method)
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return json.loads(exc.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "description": "HTTP %s" % exc.code}
    except Exception as exc:  # URLError, timeout, bad JSON — degraded mode
        return {"ok": False, "description": str(exc)}


def _keyboard(buttons):
    """One button per row. Strings become their own callback_data (the caller
    passes the literal command, e.g. 'unpublish gravity-well', so the tap IS
    the command text — no second mapping to drift)."""
    rows = []
    for b in buttons:
        if isinstance(b, dict):
            rows.append([b])
        else:
            rows.append([{"text": str(b), "callback_data": str(b)}])
    return {"inline_keyboard": rows}


def send(text, buttons=None):
    """Send one message to the owner chat; optional inline buttons.

    Returns the sent message dict, or None in no-op mode / on failure.
    """
    token, chat = _creds()
    if not token or not chat:
        sys.stderr.write(
            "telegram: no-op (BOB_TELEGRAM_TOKEN/BOB_TELEGRAM_CHAT unset) — "
            "would have sent: %s\n" % text[:200])
        return None
    payload = {"chat_id": chat, "text": text}
    if buttons:
        payload["reply_markup"] = _keyboard(buttons)
    resp = _http("sendMessage", payload, token)
    if not resp.get("ok"):
        sys.stderr.write("telegram: send failed: %s\n"
                         % resp.get("description", "unknown"))
        return None
    return resp.get("result")


def _parse_command(text):
    """'unpublish my-game because reason' -> (verb, slug, rest)."""
    parts = (text or "").strip().split(None, 2)
    if not parts:
        return None, None, ""
    verb = parts[0].lower().lstrip("/")
    slug = parts[1] if len(parts) > 1 else None
    rest = parts[2] if len(parts) > 2 else ""
    return verb, slug, rest


def _state_check(verb, slug, games):
    """Is this verb legal against the game's CURRENT state? Returns
    (valid, reason). The queue's state is the truth (queue.advance's rule);
    a button tapped after the world moved on must bounce here."""
    game = games.get(slug or "")
    if game is None:
        return False, ("no game '%s' in the queue — stale or mistyped slug"
                       % slug)
    state = game.get("state")
    if verb == "unpublish":
        # Only a game that actually reached the storefront can come off it.
        if state not in ("published", "live"):
            return False, ("'%s' is %s, not published/live — nothing to "
                           "unpublish" % (slug, state))
        game_dir = os.path.join(_home(), "games", slug)
        projections = [
            os.path.join(game_dir, SEND_PROJECTION_FILE),
            os.path.join(game_dir, LEGACY_LAUNCH_PROJECTION_FILE),
            os.path.join(game_dir, LEGACY_PUBLICATION_PROJECTION_FILE),
        ]
        existing = [path for path in projections if os.path.exists(path)]
        if len(existing) > 1:
            return False, (
                "'%s' has multiple send projections (%s); resolve the split "
                "authority before using the kill switch"
                % (slug, ", ".join(os.path.basename(path) for path in existing))
            )
        if not existing:
            return False, ("'%s' has no send projection — it never "
                           "left the building" % slug)
        return True, ""
    if verb == "park":
        if state in queue.TERMINAL:
            return False, ("'%s' is already %s — parking is for in-flight "
                           "games" % (slug, state))
        return True, ""
    if verb == "note":
        # A taste note attaches to any existing game, whatever its state —
        # owner verdicts are calibration data even on dead games.
        return True, ""
    return False, "verb '%s' outside the closed set %s" % (
        verb, sorted(VERBS))


def _read_offset():
    try:
        with open(_offset_path(), "r") as fh:
            return int(fh.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def _write_offset(offset):
    path = _offset_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(str(offset))
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def poll_decisions():
    """Drain pending updates; return validated decision dicts.

    Each decision: {verb, slug, args, valid, reason, source}. The caller
    acts ONLY on valid=True rows; invalid rows are returned too so the tick
    log shows every refused command (a refused kill-switch press is the one
    thing that must never vanish silently).

    Side effects: advances state/.tg-offset (so a command is delivered
    once) and strips the inline keyboard off any tapped message (the
    stale-button receipt: a live button on an old message is a replayable
    command).
    """
    token, chat = _creds()
    if not token or not chat:
        sys.stderr.write("telegram: poll no-op (creds unset)\n")
        return []

    offset = _read_offset()
    resp = _http("getUpdates", {"offset": offset, "timeout": 0}, token)
    if not resp.get("ok"):
        sys.stderr.write("telegram: getUpdates failed: %s\n"
                         % resp.get("description", "unknown"))
        return []
    updates = resp.get("result") or []
    if not updates:
        return []

    games = queue.load().get("games", {})
    decisions = []
    max_id = offset - 1
    for upd in updates:
        max_id = max(max_id, int(upd.get("update_id", 0)))
        text, source, cb = None, None, None
        if "callback_query" in upd:
            cb = upd["callback_query"]
            text = cb.get("data", "")
            source = "button"
        elif "message" in upd:
            msg = upd["message"]
            # Only the owner chat commands Bob. Anything else is noise —
            # this bot must never take orders from an unknown chat id.
            if str(msg.get("chat", {}).get("id", "")) != str(chat):
                continue
            text = msg.get("text", "")
            source = "message"
        else:
            continue

        verb, slug, rest = _parse_command(text)
        if verb is None:
            continue
        if verb not in VERBS:
            decisions.append({
                "verb": verb, "slug": slug, "args": rest, "valid": False,
                "reason": "verb '%s' outside closed set %s — refused"
                          % (verb, sorted(VERBS)),
                "source": source,
            })
        else:
            valid, reason = _state_check(verb, slug, games)
            decisions.append({"verb": verb, "slug": slug, "args": rest,
                              "valid": valid, "reason": reason,
                              "source": source})

        if cb is not None:
            # Strip the keyboard NOW, before the command is even executed:
            # the tap is consumed whether or not the action succeeds, and a
            # failed action gets a fresh message with fresh buttons.
            msg = cb.get("message") or {}
            if msg.get("message_id") is not None:
                _http("editMessageReplyMarkup", {
                    "chat_id": msg.get("chat", {}).get("id", chat),
                    "message_id": msg["message_id"],
                    "reply_markup": {"inline_keyboard": []},
                }, token)
            if cb.get("id"):
                _http("answerCallbackQuery", {"callback_query_id": cb["id"]},
                      token)

    _write_offset(max_id + 1)
    return decisions
