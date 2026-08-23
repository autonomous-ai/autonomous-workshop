#!/usr/bin/env python3
"""telegram.py — the owner's two approval gates, and the two escalations.

    python3 board-game/tools/telegram.py gate1       <slug>
    python3 board-game/tools/telegram.py gate2       <slug>
    python3 board-game/tools/telegram.py arbitration <slug>
    python3 board-game/tools/telegram.py stuck       <slug>
    python3 board-game/tools/telegram.py heartbeat
    python3 board-game/tools/telegram.py watchdog --max-hours 28
    python3 board-game/tools/telegram.py listen

Every message carries the reply commands ready to paste. There is no webhook:
the owner answers by running one line, which means this whole channel is a
`curl` and a file, with nothing that has to be built to keep it alive. `poll`
still runs once per pipeline step for that reason, but a button's reply
textbox only opens once something reacts to the tap — run `listen` in the
background (it long-polls, no server needed) if you want that to happen in
real time instead of on the pipeline's own schedule.

Without TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_DM the message is printed to stdout
instead of being sent. That is a deliberate fallback rather than a silent
skip — the gate still happens, it just happens in the terminal, and the
pipeline is usable before anyone sets up a bot.

Reads .env from the repo root if present.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IDEAS = REPO_ROOT / "board-game" / "ideas"
HEARTBEAT = REPO_ROOT / "board-game" / ".heartbeat"
OFFSET_FILE = REPO_ROOT / "board-game" / ".telegram_offset"
PENDING_FILE = REPO_ROOT / "board-game" / ".telegram_pending.json"
MESSAGES_FILE = REPO_ROOT / "board-game" / ".telegram_messages.json"
PY = ".venv/bin/python"
Q = "board-game/tools/pipeline_queue.py"
PY_ABS = REPO_ROOT / ".venv" / "bin" / "python"
QUEUE_SCRIPT = REPO_ROOT / "board-game" / "tools" / "pipeline_queue.py"
PUBLISH_SCRIPT = REPO_ROOT / "board-game" / "tools" / "publish.py"

# The four gate-reply verbs a Telegram message ever asks the owner to run,
# plus `amend` (arbitration's one reply). Deliberately not the full
# pipeline_queue.py surface — `poll` only ever executes what a gate message
# itself offered, button or pasted text.
ALLOWED_VERBS = {"approve", "reject", "rework", "ship", "amend"}
NEEDS_REASON = {"reject", "rework"}
# `publish` is the one verb that is not a queue transition: it runs publish.py,
# which imports the shipped game into Panda Social as a draft. It is offered
# only AFTER a ship succeeds — shipping is the decision, publishing is the
# consequence, and keeping them two taps means a ship can still be recorded on
# a machine where publishing is not configured.
PUBLISH_VERB = "publish"
REPLY_VERBS = ALLOWED_VERBS | {PUBLISH_VERB}
# Publishing uploads the whole project folder to the CDN, so it is minutes, not
# seconds. `poll`/`listen` block for that whole time — acceptable because it
# happens once per game, and a job queue for one upload would be its own thing
# to keep alive.
PUBLISH_TIMEOUT = 1800


def load_env() -> None:
    env_file = REPO_ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def creds() -> tuple[str, str]:
    return (os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
            os.environ.get("TELEGRAM_CHAT_DM", "").strip())


def split_for_caption(text: str, limit: int = 1024) -> tuple[str, str]:
    """Split `text` so a media caption ends on a clean boundary instead of
    wherever character 1024 happens to land — a hard character cut regularly
    lands mid-word (a caption ending "...w)." with the rest starting "w) — an
    open shelf") and reads as broken. Prefer a paragraph break, then a line
    break, then a word boundary, only falling back to a hard cut if none of
    those exist within the limit."""
    if len(text) <= limit:
        return text, ""
    cut = text.rfind("\n\n", 0, limit)
    if cut == -1:
        cut = text.rfind("\n", 0, limit)
    if cut == -1:
        cut = text.rfind(" ", 0, limit)
    if cut == -1:
        cut = limit
    return text[:cut].rstrip(), text[cut:].lstrip()


def _message_id(raw: str) -> int | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return (data.get("result") or {}).get("message_id") if data.get("ok") else None


def _checked(result: subprocess.CompletedProcess, method: str) -> None:
    """Raise when Telegram or curl rejected a send; never mark failed media sent."""
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        detail = result.stderr.strip() or f"curl exit {result.returncode}"
        raise RuntimeError(
            f"Telegram {method} returned invalid JSON ({detail}): "
            f"{result.stdout[:200]}") from exc
    if result.returncode or payload.get("ok") is not True:
        detail = payload.get("description") or result.stderr.strip() or "unknown error"
        raise RuntimeError(f"Telegram {method} failed: {detail}")


def send(text: str, photo: Path | None = None, video: Path | None = None,
         chat: str | None = None,
          buttons: list[list[dict]] | None = None,
          parse_mode: str | None = None) -> int | None:
    """Send text with at most one photo or video attachment.

    `chat` overrides the destination. The rules-ready journal notice uses
    this to keep the gate channel reserved for messages needing a decision.
    `buttons` is an inline-keyboard row list
    (`[[{"text": ..., "callback_data": ...}, ...]]`) — attached to the photo
    when there is one, otherwise to the text message. Returns the sent
    message's id (the button-bearing one, if there is one) so a caller can
    track it for later — see `track_message`/`disable_stale`."""
    if photo is not None and video is not None:
        raise ValueError("send accepts either photo or video, not both")
    token, default_chat = creds()
    chat = chat or default_chat
    if not (token and chat):
        print("--- telegram not configured; the gate is here instead ---")
        if photo:
            print(f"[render] {photo}")
        if video:
            print(f"[video] {video}")
        print(text)
        return None
    markup = json.dumps({"inline_keyboard": buttons}) if buttons else None
    message_id = None
    media = (photo or video).resolve() if (photo or video) else None
    if media and media.is_file():
        caption, rest = split_for_caption(text)
        method = "sendPhoto" if photo else "sendVideo"
        field = "photo" if photo else "video"
        staged = None
        upload = media
        if video:
            with tempfile.NamedTemporaryFile(
                    prefix="board-game-rules-", suffix=media.suffix,
                    delete=False) as handle:
                staged = Path(handle.name)
            shutil.copyfile(media, staged)
            upload = staged
        cmd = ["curl", "-sS", f"https://api.telegram.org/bot{token}/{method}",
               "--form-string", f"chat_id={chat}",
               "-F", f"{field}=@{upload}",
               "--form-string", f"caption={caption}"]
        if parse_mode:
            cmd += ["--form-string", f"parse_mode={parse_mode}"]
        if markup:
            cmd += ["--form-string", f"reply_markup={markup}"]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120)
        finally:
            if staged:
                staged.unlink(missing_ok=True)
        _checked(result, method)
        message_id = _message_id(result.stdout)
        if rest:
            send_text_only(token, chat, rest, parse_mode=parse_mode)
    else:
        message_id = send_text_only(
            token, chat, text, buttons=buttons, parse_mode=parse_mode)
    print(f"sent ({len(text)} chars"
          f"{', with render' if photo else ''}"
          f"{', with video' if video else ''}"
          f"{', with buttons' if buttons else ''})")
    return message_id


def send_text_only(token: str, chat: str, text: str,
                    buttons: list[list[dict]] | None = None,
                    parse_mode: str | None = None) -> int | None:
    chunks = [text[i:i + 3500] for i in range(0, len(text), 3500)] or [""]
    message_id = None
    for i, chunk in enumerate(chunks):
        cmd = ["curl", "-sS", f"https://api.telegram.org/bot{token}/sendMessage",
               "-d", f"chat_id={chat}",
               "--data-urlencode", f"text={chunk}"]
        if parse_mode:
            cmd += ["-d", f"parse_mode={parse_mode}"]
        if buttons and i == len(chunks) - 1:
            markup = json.dumps({"inline_keyboard": buttons})
            cmd += ["--data-urlencode", f"reply_markup={markup}"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        _checked(result, "sendMessage")
        message_id = _message_id(result.stdout)
    return message_id


def load_messages() -> dict:
    return json.loads(MESSAGES_FILE.read_text()) if MESSAGES_FILE.is_file() else {}


def save_messages(data: dict) -> None:
    MESSAGES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def track_message(slug: str, chat: str, message_id: int | None) -> None:
    """Remember the last button-bearing message sent for `slug`, so a later
    gate (or `disable`) can strip its buttons instead of leaving a stale
    decision point live in chat history."""
    if message_id is None:
        return
    data = load_messages()
    data[slug] = {"chat": chat, "message_id": message_id}
    save_messages(data)


def disable_stale(slug: str) -> bool:
    """Strip the buttons off the last tracked message for `slug`. Called
    automatically before a new gate message goes out for the same slug, and
    exposed as `telegram.py disable <slug>` for a manual one-off. Only works
    for messages sent after this tracking existed — anything older has no
    recorded message_id and has to be deleted by hand in the client."""
    data = load_messages()
    entry = data.pop(slug, None)
    if not entry:
        return False
    token, _ = creds()
    if token:
        api_call(token, "editMessageReplyMarkup", {
            "chat_id": entry["chat"], "message_id": entry["message_id"],
            "reply_markup": json.dumps({"inline_keyboard": []})})
    save_messages(data)
    return True


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def find_hero(slug: str) -> Path | None:
    """The cover render cadcode's review pass writes (`_assembled.png`), or
    any hero we have. Renders are the entire point of gate 1 — the owner is
    judging an object, not a paragraph."""
    home = IDEAS / slug
    for pattern in ("**/_assembled.png", "**/cover.png", "**/*_qa.png"):
        found = sorted(home.glob(pattern))
        if found:
            return found[0]
    return None


def rules_summary(idea: dict) -> str:
    """One screen. If it does not fit on a phone it will not be read, and a
    gate nobody reads is a gate that always says yes."""
    players = idea.get("players") or {}
    lines = [
        idea.get("concept", "").strip(),
        "",
        f"{players.get('min', '?')}-{players.get('max', '?')} players · "
        f"~{idea.get('playtime_min', '?')} min",
        "",
        "TURN:",
    ]
    for step in (idea.get("rules") or {}).get("turn") or []:
        lines.append(f"  · {step.get('text', '')}")
    win = (idea.get("rules") or {}).get("win") or {}
    lines += ["", f"WIN: {win.get('text', '?')}", "", "BOX:"]
    for c in idea.get("components") or []:
        lines.append(f"  {c.get('qty', '?')}x {c.get('name', '?')}")
    return "\n".join(lines)


def cmd_gate1(args) -> int:
    """Two messages, deliberately: the photo caption is a short, fixed-length
    header (title + one-liner) so it always fits Telegram's 1024-char caption
    cap, and the buttons live there. The full rules text — which regularly
    runs past that cap on its own — goes out as a plain follow-up message
    instead of being cut wherever the caption limit happens to land."""
    slug = args.slug
    disable_stale(slug)
    idea = read_json(IDEAS / slug / "idea.json")
    title = idea.get("title", slug)
    header = f"BOARD GAME — worth building?\n{title} ({slug})"
    body = (f"{rules_summary(idea)}\n\n"
            f"Real CadQuery draft, not an illustration — a yes holds the "
            f"final build to matching it.")
    buttons = [[
        {"text": "✅ Approve", "callback_data": f"approve:{slug}"},
        {"text": "❌ Reject", "callback_data": f"reject:{slug}"},
        {"text": "🔧 Rework", "callback_data": f"rework:{slug}"},
    ]]
    mid = send(header, find_hero(slug), buttons=buttons)
    _, chat = creds()
    track_message(slug, chat, mid)
    send(body)
    return 0


def cmd_gate2(args) -> int:
    slug = args.slug
    disable_stale(slug)
    idea = read_json(IDEAS / slug / "idea.json")
    gate = read_json(IDEAS / slug / "project" / "gate.json")
    verdicts = []
    for lens in ("printability", "fidelity", "playability"):
        path = IDEAS / slug / f"review_{lens}.md"
        first = (path.read_text(encoding="utf-8").splitlines() or [""])[0] \
            if path.is_file() else "no verdict"
        verdicts.append(f"  {lens}: {first.replace('Verdict:', '').strip()}")

    parts = gate.get("part_count", "?")
    shapes = gate.get("distinct_shapes", "?")
    sliced = [v for v in (gate.get("slice") or {}).values() if v.get("print_min")]
    hours = sum(v["print_min"] for v in sliced) / 60.0 if sliced else None

    # A pass that could not measure something is not a clean pass, and the
    # owner has to see that BEFORE tapping Ship rather than in the refusal
    # afterwards. The button cannot carry a reason, so the command is spelled
    # out to paste.
    unmeasured = gate.get("unmeasured") or []
    caveat = ""
    if unmeasured:
        caveat = ("\n\nNOT MEASURED — the gate could not reach a verdict on:\n"
                  + "\n".join(f"  • {note}" for note in unmeasured)
                  + f"\nShipping needs you to accept that explicitly:\n"
                    f"  ship {slug} --accept-unmeasured \"why this is fine\"")

    header = f"BOARD GAME — ship it?\n{idea.get('title', slug)} ({slug})"
    body = (f"GATE PASS · {parts} pieces, {shapes} distinct shapes"
            + (f" · ~{hours:.1f}h of printing\n" if hours else "\n")
            + "\n".join(verdicts)
            + f"\n\nFiles: board-game/ideas/{slug}/project/"
            + caveat)
    buttons = [[
        {"text": "🚀 Ship", "callback_data": f"ship:{slug}"},
        {"text": "❌ Reject", "callback_data": f"reject:{slug}"},
    ]]
    mid = send(header, find_hero(slug), buttons=buttons)
    _, chat = creds()
    track_message(slug, chat, mid)
    send(body)
    return 0


def cmd_arbitration(args) -> int:
    slug = args.slug
    disable_stale(slug)
    proposal = read_json(IDEAS / slug / "brief_proposed.json")
    amendments = proposal.get("amendments") or []
    text = (f"ARBITRATION — {slug}\n\n"
            f"The repair budget is spent and what is left looks like a spec "
            f"conflict, not a build defect: the brief is asking for things "
            f"that cannot all be true at once.\n\nProposed changes:\n"
            + "\n".join(f"  · {a}" for a in amendments)
            + f"\n\nDetails: board-game/ideas/{slug}/brief_proposed.json\n\n"
              f"APPLY:  {PY} {Q} amend {slug}\n"
              f"DROP:   rm board-game/ideas/{slug}/brief_proposed.json")
    buttons = [[{"text": "✅ Apply amendment", "callback_data": f"amend:{slug}"}]]
    mid = send(text, buttons=buttons)
    _, chat = creds()
    track_message(slug, chat, mid)
    return 0


def cmd_stuck(args) -> int:
    slug = args.slug
    gate = read_json(IDEAS / slug / "project" / "gate.json")
    fails = gate.get("fails") or ["(no gate report)"]
    text = (f"STUCK — {slug}\n\n"
            f"Repair budget spent and this is not a spec conflict, so it needs "
            f"a look. Still failing:\n"
            + "\n".join(f"  · {f}" for f in fails[:10])
            + f"\n\n{PY} {Q} list")
    send(text)
    return 0


def cmd_heartbeat(args) -> int:
    HEARTBEAT.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
    print(f"heartbeat {HEARTBEAT}")
    return 0


def cmd_watchdog(args) -> int:
    """Silence has to be alarmable. A pipeline that stops running looks exactly
    like a pipeline with nothing to do, until you check a month later."""
    if not HEARTBEAT.is_file():
        send("WATCHDOG — the board-game pipeline has never checked in.")
        return 1
    last = datetime.fromisoformat(HEARTBEAT.read_text(encoding="utf-8").strip())
    stale = datetime.now(timezone.utc) - last
    if stale > timedelta(hours=args.max_hours):
        send(f"WATCHDOG — the board-game pipeline has been silent for "
             f"{stale.total_seconds() / 3600:.0f}h (last {last.isoformat()}).")
        return 1
    print(f"ok, last heartbeat {stale.total_seconds() / 3600:.1f}h ago")
    return 0


def api_call(token: str, method: str, data: dict | None = None) -> dict:
    cmd = ["curl", "-s", f"https://api.telegram.org/bot{token}/{method}"]
    for k, v in (data or {}).items():
        cmd += ["--data-urlencode", f"{k}={v}"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "raw": result.stdout}


def load_offset() -> int:
    return int(OFFSET_FILE.read_text().strip()) if OFFSET_FILE.is_file() else 0


def save_offset(update_id: int) -> None:
    OFFSET_FILE.write_text(str(update_id), encoding="utf-8")


def load_pending() -> dict:
    return json.loads(PENDING_FILE.read_text()) if PENDING_FILE.is_file() else {}


def save_pending(pending: dict) -> None:
    PENDING_FILE.write_text(json.dumps(pending, indent=2), encoding="utf-8")


def run_pipeline(cmd_args: list[str]) -> str:
    """Run one owner command exactly as they would paste it, and return its
    combined output. Two scripts are reachable and no others: pipeline_queue.py
    for a state transition, publish.py for `publish <slug>` — which is why the
    verb is checked against REPLY_VERBS before anything gets here."""
    verb, rest = cmd_args[0], cmd_args[1:]
    if verb == PUBLISH_VERB:
        cmd, timeout = [str(PY_ABS), str(PUBLISH_SCRIPT)] + rest, PUBLISH_TIMEOUT
    else:
        cmd, timeout = [str(PY_ABS), str(QUEUE_SCRIPT)] + cmd_args, 60
    try:
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True,
                                text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"{verb}: timed out after {timeout}s — check the terminal"
    return (result.stdout + result.stderr).strip()


def offer_publish(chat: str, slug: str, out: str) -> None:
    """After a ship lands, hand over the one button that carries it out of the
    repo. Silent when the ship did not actually happen, so a refused transition
    never gets a publish button anyway."""
    if "SHIPPED" not in out.upper():
        return
    send(f"{slug} is shipped. Put it on Panda Social as a draft?",
         chat=chat,
         buttons=[[{"text": "📦 Publish", "callback_data": f"{PUBLISH_VERB}:{slug}"}]])


def send_reply_prompt(token: str, chat: str, action: str, slug: str) -> int | None:
    label = "rejection" if action == "reject" else "rework"
    resp = api_call(token, "sendMessage", {
        "chat_id": chat,
        "text": f"Reply with the {label} reason for {slug}:",
        "reply_markup": json.dumps({"force_reply": True, "selective": True}),
    })
    return resp.get("result", {}).get("message_id") if resp.get("ok") else None


def handle_callback(token: str, chat: str, cq: dict, pending: dict) -> bool:
    """One button tap. Always answers the callback (Telegram leaves the button
    spinning otherwise) and strips the keyboard off the original message so
    it cannot be tapped twice."""
    cq_id = cq["id"]
    msg_id = (cq.get("message") or {}).get("message_id")
    action, _, slug = (cq.get("data") or "").partition(":")

    if action not in REPLY_VERBS or not slug:
        api_call(token, "answerCallbackQuery",
                 {"callback_query_id": cq_id, "text": "unrecognized button"})
        return False

    if msg_id is not None:
        api_call(token, "editMessageReplyMarkup", {
            "chat_id": chat, "message_id": msg_id,
            "reply_markup": json.dumps({"inline_keyboard": []})})
    messages = load_messages()
    if messages.pop(slug, None) is not None:
        save_messages(messages)

    if action in NEEDS_REASON:
        prompt_id = send_reply_prompt(token, chat, action, slug)
        if prompt_id is not None:
            pending[str(prompt_id)] = {"action": action, "slug": slug}
        api_call(token, "answerCallbackQuery",
                 {"callback_query_id": cq_id, "text": "reply with your reason below"})
        return True

    if action == PUBLISH_VERB:
        # Telegram drops a callback that is not answered within seconds, and
        # this one runs for minutes — so answer first, then upload.
        api_call(token, "answerCallbackQuery",
                 {"callback_query_id": cq_id,
                  "text": "publishing — this takes a few minutes"})
        send(run_pipeline([PUBLISH_VERB, slug]) or f"published {slug}", chat=chat)
        return True

    out = run_pipeline([action, slug])
    api_call(token, "answerCallbackQuery",
             {"callback_query_id": cq_id, "text": (out or action)[:200]})
    send(out or f"{action} {slug}: done", chat=chat)
    if action == "ship":
        offer_publish(chat, slug, out)
    return True


def process_update(token: str, chat: str, update: dict, pending: dict) -> bool:
    """Handle one getUpdates item — a button tap or a free-text message —
    shared by `poll` (one pass) and `listen` (continuous). Returns whether it
    was something this bot acts on, so callers can count `handled`.

    Still accepts a raw pasted command line too (`approve armillary`, or the
    full line a gate message prints) — the button is a shortcut, not a
    replacement for the paste-it-yourself path the pipeline started with."""
    cq = update.get("callback_query")
    if cq:
        return handle_callback(token, chat, cq, pending)

    msg = update.get("message")
    if not msg or str(msg.get("chat", {}).get("id", "")) != chat:
        return False
    text = (msg.get("text") or "").strip()
    if not text:
        return False

    reply_to = (msg.get("reply_to_message") or {}).get("message_id")
    if reply_to is not None and str(reply_to) in pending:
        entry = pending.pop(str(reply_to))
        out = run_pipeline([entry["action"], entry["slug"], "--reason", text])
        send(out or f"{entry['action']} {entry['slug']}: done", chat=chat)
        return True

    try:
        tokens = shlex.split(text)
    except ValueError:
        tokens = text.split()
    verb_idx = next((i for i, t in enumerate(tokens) if t in REPLY_VERBS), None)
    if verb_idx is not None:
        out = run_pipeline(tokens[verb_idx:])
        send(out or f"{tokens[verb_idx]}: done", chat=chat)
        if tokens[verb_idx] == "ship" and len(tokens) > verb_idx + 1:
            offer_publish(chat, tokens[verb_idx + 1], out)
        return True
    return False


def cmd_poll(args) -> int:
    """One poll of Telegram for new owner replies — button taps and, for
    reject/rework, the free-text reason that follows — run as pipeline_queue.py
    commands. One pass per invocation, called from a loop step or a cron tick.

    This alone means a button tap can sit unanswered until the next `/bg`
    step happens to run `poll`, which can be minutes away — the reply textbox
    (Telegram's force_reply) only opens once `poll` reacts to the tap. Run
    `listen` alongside this for an owner who wants that to happen within a
    second or two instead."""
    token, chat = creds()
    if not (token and chat):
        print("telegram not configured; nothing to poll")
        return 0

    offset = load_offset()
    resp = api_call(token, "getUpdates", {"offset": str(offset + 1), "timeout": "0"})
    if not resp.get("ok"):
        print(f"getUpdates failed: {resp}")
        return 1

    pending = load_pending()
    handled = 0
    for update in resp.get("result", []):
        offset = update["update_id"]
        if process_update(token, chat, update, pending):
            handled += 1

    save_offset(offset)
    save_pending(pending)
    print(f"polled, {handled} update(s) handled")
    return 0


def cmd_listen(args) -> int:
    """Long-poll Telegram forever so a button tap gets its reply textbox (or
    its pipeline command) run within a second or two, instead of waiting on
    the next `/bg` step's one-shot `poll`. Meant to be started once and left
    running (e.g. `nohup ... telegram.py listen &`) alongside the pipeline
    loop, not driven by it — Ctrl-C or a kill signal stops it cleanly."""
    token, chat = creds()
    if not (token and chat):
        print("telegram not configured; nothing to listen for")
        return 0

    print("listening for Telegram replies (Ctrl-C to stop)...")
    try:
        while True:
            offset = load_offset()
            resp = api_call(token, "getUpdates",
                             {"offset": str(offset + 1), "timeout": "25"})
            if not resp.get("ok"):
                print(f"getUpdates failed: {resp}")
                continue

            pending = load_pending()
            for update in resp.get("result", []):
                offset = update["update_id"]
                if process_update(token, chat, update, pending):
                    print(f"handled update {offset}")
            save_offset(offset)
            save_pending(pending)
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


def cmd_disable(args) -> int:
    """Strip the buttons off the last tracked gate message for a slug, on
    demand — for a message that's no longer the live decision point but is
    still sitting in chat history with tappable buttons."""
    if disable_stale(args.slug):
        print(f"{args.slug}: buttons removed from its last tracked message")
    else:
        print(f"{args.slug}: no tracked message on record — it may predate "
              f"this feature, or was already handled; delete it by hand in "
              f"the client if it still has live buttons")
    return 0


def main() -> int:
    load_env()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("gate1", cmd_gate1), ("gate2", cmd_gate2),
                     ("arbitration", cmd_arbitration), ("stuck", cmd_stuck)):
        p = sub.add_parser(name)
        p.add_argument("slug")
        p.set_defaults(fn=fn)
    sub.add_parser("heartbeat").set_defaults(fn=cmd_heartbeat)
    p = sub.add_parser("watchdog")
    p.add_argument("--max-hours", type=float, default=28.0)
    p.set_defaults(fn=cmd_watchdog)
    sub.add_parser("poll").set_defaults(fn=cmd_poll)
    sub.add_parser("listen").set_defaults(fn=cmd_listen)
    p = sub.add_parser("disable")
    p.add_argument("slug")
    p.set_defaults(fn=cmd_disable)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
