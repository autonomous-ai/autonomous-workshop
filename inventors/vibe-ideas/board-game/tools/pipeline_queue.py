#!/usr/bin/env python3
"""queue.py — the pipeline's state, and the only thing allowed to decide what
happens next.

    python3 board-game/tools/pipeline_queue.py next          # what should run now
    python3 board-game/tools/pipeline_queue.py next --peek   # ...without claiming it
    python3 board-game/tools/pipeline_queue.py list
    python3 board-game/tools/pipeline_queue.py add <slug> --title "..."
    python3 board-game/tools/pipeline_queue.py advance <slug> --to built --note "..."
    python3 board-game/tools/pipeline_queue.py repair <slug>        # consume one round
    python3 board-game/tools/pipeline_queue.py gate_rework <slug> --stage rules_check --reason "..."
    python3 board-game/tools/pipeline_queue.py gate_rework <slug> --stage lens_rules --reason "..." --disposition clarify
    python3 board-game/tools/pipeline_queue.py release <slug>       # step ended, no move
    python3 board-game/tools/pipeline_queue.py ship <slug>          # owner: gate 2 yes
    python3 board-game/tools/pipeline_queue.py ship <slug> --accept-unmeasured "..."
    python3 board-game/tools/pipeline_queue.py reject <slug> --reason "..."
    python3 board-game/tools/pipeline_queue.py rework <slug> --reason "..."

An idea lives here across many turns. That is the change the whole rebuild
turns on: for fifteen turns an idea that died of an infrastructure fault was
replaced by a fresh one and nothing was ever finished. Now the unit of work is
an idea, not a turn, and an idea only leaves the queue by shipping or by being
killed for a stated reason.

Why this is Python and not instructions in a prompt: the repair budget lives
here. An agent that can read its own budget in its own prompt is an agent that
will negotiate with it. Same for state transitions — a stage is complete when
this file says so, not when a model reports success.

Two drivers can run at once — `/loop /bg` on a short interval is enough on its
own, since a step that spawns an agent takes minutes and the loop does not
wait for it. So the queue guards itself twice:

  * a **lock** around every read-modify-write, because two unsynchronised
    load/save pairs lose one of the two transitions outright; and
  * a **claim** on whatever `next` hands out, because `state` does not change
    until a step *finishes* — so without one, every tick during a running step
    is handed the same work again and spawns a second agent onto the same
    files. A claim is a lease with an expiry, so a driver that dies mid-step
    releases its idea instead of stranding it.
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import socket
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import journal  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
QUEUE = REPO_ROOT / "board-game" / "QUEUE.json"
LOCK = REPO_ROOT / "board-game" / ".queue.lock"
IDEAS = REPO_ROOT / "board-game" / "ideas"
TASTE = REPO_ROOT / "board-game" / "TASTE.md"

# Two repair rounds, then arbitration. Not a technical ceiling — text2cad's
# evidence is that past two rounds the problem is usually the spec rather than
# the code, and more repair rounds spend effort at the wrong address.
REPAIR_BUDGET = 2

# Rules-gate reworks permitted before the next failed gate kills the idea.
# Three rounds: each rework gets the full rules_check, lens-rules, engine,
# playtest and table gate again, so more rounds multiply that cost, and an
# idea still failing after three balancing passes is a shape problem, not a
# tuning one.
REWORK_BUDGET = 3

# Clarification rounds are granted when a gate's finding is ambiguity or
# incompleteness rather than a defect in how the game functions: the fix is
# rule text, not the mechanic, so it does not spend the rework budget. They are
# bounded anyway, because an unbounded free lane is how a design flaw gets
# laundered: a flaw "clarified" one round at a time never reaches the budget.
# Three passes at making a game coherent is plenty; if it still cannot be
# described unambiguously after three, the problem is the game, not the words.
CLARIFY_BUDGET = 3

# How long a claim taken by `next` stays valid without being advanced or
# released. The whole point of a claim is that `next` stops handing the same
# work to a second driver while the first one's agent is still running — but a
# claim that never expires would strand an idea forever the moment a driver
# crashes mid-step, which is a worse failure than doing the work twice. So a
# claim is a *lease*: long enough that no honest step outlives it (the slowest
# real step, a full build with two repair rounds, runs well under this), short
# enough that a dead driver's work is picked back up the same hour.
CLAIM_TTL_SECONDS = 45 * 60

# How long to wait for the queue lock before giving up. Every holder does
# local file I/O only, so real contention is milliseconds and anything
# approaching this timeout means a stuck process, not a busy one.
LOCK_TIMEOUT_SECONDS = 30.0

# state -> (what to run next, state it moves to on success)
# `None` action means the pipeline is waiting on the owner and this idea is
# skipped by `next` — which is exactly why a queue exists: one idea waiting on
# a human must never stall the others.
PIPELINE: dict[str, tuple[str | None, str]] = {
    "proposed":       ("rules_gate", "rules_ok"),
    "rules_ok":       ("brief", "briefed"),
    "briefed":        ("draft", "drafted"),
    "drafted":        ("owner_gate_1", "awaiting_owner"),
    "awaiting_owner": (None, "awaiting_owner"),
    "approved":       ("build", "built"),
    "built":          ("panel", "reviewed"),
    "reviewed":       ("owner_gate_2", "awaiting_ship"),
    "awaiting_ship":  (None, "awaiting_ship"),
    "repairing":      ("repair", "built"),
    "shipped":        (None, "shipped"),
    "killed":         (None, "killed"),
    "blocked":        (None, "blocked"),
}

# Ideas closest to shipping go first: finishing something beats starting
# something. `proposed` sits last so a backlog never crowds out a build.
PRIORITY = ["reviewed", "built", "repairing", "approved", "drafted", "briefed",
            "rules_ok", "proposed"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_ts(stamp: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(stamp)
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def load() -> dict:
    if not QUEUE.is_file():
        return {"ideas": {}}
    return json.loads(QUEUE.read_text(encoding="utf-8"))


def save(data: dict) -> None:
    """Write the queue atomically.

    `dashboard.py` re-reads QUEUE.json on every page load without taking the
    lock, so a plain in-place write leaves a window where a reader can catch a
    half-written file and fail to parse it. Writing a sibling temp file and
    renaming it means a reader always sees either the whole old file or the
    whole new one.
    """
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUEUE.with_suffix(QUEUE.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, QUEUE)


def rule_complexity(idea: dict) -> dict:
    """Small, reproducible complexity receipt for each rules iteration."""
    rules = idea.get("rules") or {}
    texts: list[str] = []
    steps = 0
    for phase in ("setup", "turn", "end", "win"):
        block = rules.get(phase)
        blocks = block if isinstance(block, list) else ([block] if block else [])
        for step in blocks:
            if isinstance(step, dict):
                text = str(step.get("text", "")).strip()
                if text:
                    texts.append(text)
                    steps += 1
    return {
        "rule_words": sum(len(text.split()) for text in texts),
        "rule_steps": steps,
        "action_types": len(idea.get("action_types") or []),
        "components": len(idea.get("components") or []),
    }


def table_experience(idea_path: Path) -> dict | None:
    """Capture player-facing evidence from the current rules iteration.

    It is deliberately smaller than the table summary: later players may be
    given prior players' experience, but never the engine, scripted metrics,
    reviewer verdict, or hidden state. A summary older than idea.json belongs
    to a previous rules version and must not be archived as this iteration.
    """
    table = idea_path.parent / "playtest" / "table"
    summaries = sorted(table.glob("run_*.json"),
                       key=lambda path: path.stat().st_mtime)
    if not summaries or summaries[-1].stat().st_mtime < idea_path.stat().st_mtime:
        return None
    source = summaries[-1]
    try:
        run = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return {
        "source": str(source.relative_to(idea_path.parent)),
        "model": run.get("model"),
        "games": [
            {key: game.get(key) for key in
             ("label", "seats", "scores", "winners", "finished")}
            for game in run.get("games") or []
        ],
        "debriefs": run.get("debriefs") or [],
        "rules_questions": run.get("rules_questions") or [],
    }


def snapshot_before_rework(slug: str, rework_number: int | None = None,
                           disposition: str | None = None,
                           request: dict | None = None) -> None:
    """Preserve the current proposal so a later rules-ready notice can show
    exactly what changed. `.idea_before_rework.json` remains the immediately
    preceding iteration used by notifications, while an immutable copy goes
    under `history/reworks/` so the design's evolution is never overwritten.

    `disposition` ("clarify" or "rework") records what kind of round this
    snapshot opens, and `mech_surface` freezes the mechanic-defining fields at
    that moment so the queue can detect, later, if a clarify round actually
    changed a mechanic."""
    idea_path = IDEAS / slug / "idea.json"
    if not idea_path.is_file():
        raise SystemExit(
            f"cannot snapshot {slug} before rework: {idea_path} is missing")
    idea = json.loads(idea_path.read_text(encoding="utf-8"))
    snapshot_path = idea_path.parent / ".idea_before_rework.json"
    snapshot = {
        "rework_number": rework_number,
        "idea": idea,
        "disposition": disposition,
        "mech_surface": mech_surface(idea),
        "complexity_before": rule_complexity(idea),
        "request": request,
        "table_experience": table_experience(idea_path),
    }
    history = idea_path.parent / "history" / "reworks"
    history.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    label = disposition or "owner"
    number = rework_number if rework_number is not None else 0
    archive_path = history / f"{stamp}-{label}-{number:02d}.json"
    snapshot["archive_path"] = str(archive_path.relative_to(idea_path.parent))
    tmp = snapshot_path.with_suffix(snapshot_path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    os.replace(tmp, snapshot_path)
    archive_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def _write_rework_request(slug: str, request: dict) -> None:
    path = IDEAS / slug / ".rework_request.json"
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(request, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _validate_rework_plan(slug: str, snapshot: dict) -> dict:
    """Require diagnosis and alternatives before accepting a mechanic edit."""
    request = snapshot.get("request") or {}
    if not request.get("problem_id"):
        return {}  # legacy/owner snapshots predate structured rework requests
    path = IDEAS / slug / "rework_plan.json"
    if not path.is_file():
        raise SystemExit(
            f"{slug}: rework_plan.json is missing. Diagnose the recorded problem, "
            f"compare subtract/rollback/replace options, and choose a strategy "
            f"before this rules iteration can be accepted.")
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"{slug}: rework_plan.json is unreadable: {exc}")
    required = (
        "problem_id", "observation", "hypothesis", "test_question",
        "confounds", "options", "chosen_strategy", "expected_experience_change",
        "falsification_condition", "change_level", "must_preserve_checks",
        "anti_goal_checks", "secondary_risks",
    )
    missing = [key for key in required if not plan.get(key)]
    if missing:
        raise SystemExit(f"{slug}: rework_plan.json is missing {', '.join(missing)}")
    if plan["problem_id"] != request["problem_id"]:
        raise SystemExit(
            f"{slug}: rework_plan problem_id '{plan['problem_id']}' does not match "
            f"the gate's '{request['problem_id']}'")
    options = plan.get("options") or []
    strategies = {str(option.get("strategy", "")) for option in options
                  if isinstance(option, dict)}
    if "subtract" not in strategies or not strategies.intersection(
            {"rollback", "replace"}):
        raise SystemExit(
            f"{slug}: rework_plan options must include subtraction and at least "
            f"one rollback or replacement; a patch is not a diagnosis")
    chosen = str(plan.get("chosen_strategy", ""))
    allowed = {"patch", "subtract", "rollback", "replace"}
    if chosen not in allowed:
        raise SystemExit(
            f"{slug}: chosen_strategy must be one of {sorted(allowed)}, got '{chosen}'")
    if request.get("required_strategy") == "structural" and chosen == "patch":
        raise SystemExit(
            f"{slug}: problem '{request['problem_id']}' has recurred "
            f"{request['occurrence']} times; another additive patch is forbidden. "
            f"Choose subtract, rollback, or replace, or kill/fork the idea.")
    change_level = str(plan.get("change_level", ""))
    if change_level not in {"low", "medium", "high"}:
        raise SystemExit(
            f"{slug}: change_level must be low, medium, or high, got "
            f"'{change_level}'")
    if change_level == "high":
        raise SystemExit(
            f"{slug}: this plan declares a high-level change. It invalidates "
            f"the current evidence baseline and may not be accepted as another "
            f"rework of the same game. Fork or kill the idea instead.")
    for field in ("must_preserve_checks", "anti_goal_checks"):
        checks = plan.get(field)
        if not isinstance(checks, list) or not checks:
            raise SystemExit(f"{slug}: {field} must be a non-empty list")
        if any(not isinstance(check, dict)
               or not str(check.get("property", "")).strip()
               or not str(check.get("test", "")).strip()
               for check in checks):
            raise SystemExit(
                f"{slug}: every {field} entry needs property and test")
    if not isinstance(plan.get("secondary_risks"), list):
        raise SystemExit(f"{slug}: secondary_risks must be a list")
    return plan


def mech_surface(idea: dict) -> str:
    """Fingerprint of what a game's *mechanics* are, so a clarify round can be
    checked against it after the fact.

    A clarification is only a clarification if the fix never changed how the
    game functions. The way to test that without trusting the fixer's word for
    it is to compare, before and after the round, the fields that *define* the
    mechanics — and only those. The set is deliberately narrow:

      * `action_types` — the player-elected action procedures. Adding a step of
        prose is fine; adding a new kind of move is a new game.
      * `rules.win` — who wins and how a tie resolves. Rewriting the sentence
        is prose; changing the winner is the mechanic.
      * `players` — the min and max of the range. A game for two-to-four is a
        different game from one for three-to-five; the winner arithmetic, the
        table, and the elimination math all move with it.
      * each component's `name`, `qty`, and `per_player` — the physical shape
        of the game and how much of it each hand gets. "Each player takes 5"
        is a mechanic, not flavour.

    What is deliberately *not* in the surface: `desc` on any component (flavour
    text), the wording or ordering of individual rule steps (a step may be
    clarified, split, or reworded freely), `concept`, `title`, and
    `art_direction`. Those are exactly the fields a clarification is allowed to
    touch, so fingerprinting them would convert every honest round into a
    violation and the freeze would stop meaning anything.

    The fingerprint is a hash, not the raw fields: it is stable to read back
    from a saved snapshot without the snapshot's file path leaking into the
    comparison, and a one-line diff is a far clearer violation than a page of
    them.
    """
    parts: list = []
    actions = idea.get("action_types")
    if actions is not None:
        parts.append("actions=" + json.dumps(sorted(str(a) for a in actions)))
    win = (idea.get("rules") or {}).get("win")
    if win is not None:
        # Compare the whole win block (text plus any tie-break structure),
        # because a change to how a tie is settled is a change to the winner.
        parts.append("win=" + json.dumps(win, sort_keys=True))
    players = idea.get("players")
    if players is not None:
        try:
            parts.append("players=" + json.dumps(
                [int(players.get("min")), int(players.get("max"))],
                sort_keys=True))
        except (TypeError, ValueError):
            # A players block that does not parse is already a rules_check
            # failure; the surface just must not crash while checking it.
            parts.append("players=unparseable:" + json.dumps(players))
    for item in idea.get("components") or []:
        per = item.get("per_player")
        parts.append("comp=" + json.dumps([
            str(item.get("name", "")),
            int(item.get("qty", item.get("quantity", 0))),
            int(per) if per is not None else None,
        ]))
    canonical = "\n".join(sorted(parts))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@contextlib.contextmanager
def locked(timeout: float = LOCK_TIMEOUT_SECONDS):
    """Hold an exclusive lock on the queue for the body of the block.

    Every command here is a read-modify-write of one small JSON file. Without
    a lock, two drivers running at once interleave as load/load/save/save and
    the second save silently discards the first one's transition — the classic
    lost update, and in this pipeline a lost update means a stage that ran but
    left no trace that it ran.
    """
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    handle = LOCK.open("w")
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except OSError:
            if time.monotonic() >= deadline:
                handle.close()
                raise SystemExit(
                    f"queue is locked by another process and did not free it "
                    f"within {timeout:.0f}s ({LOCK}) — if nothing else is "
                    f"running, delete that file")
            time.sleep(0.05)
    try:
        yield
    finally:
        fcntl.flock(handle, fcntl.LOCK_UN)
        handle.close()


# Journal entries queued during a transaction and written once the lock is
# released. Routine entries are local dashboard history only. The sole
# Telegram journal event is emitted explicitly by `journal.py rules_ready`
# after every pre-table gate has passed.
_pending_journal: list[dict] = []


@contextlib.contextmanager
def transaction(timeout: float = LOCK_TIMEOUT_SECONDS):
    """Load the queue, let the caller mutate it, save it — all under the lock.

    The queue is only ever written from inside one of these. Nothing may call
    `save()` on its own.
    """
    _pending_journal.clear()
    try:
        with locked(timeout):
            data = load()
            yield data
            save(data)
    finally:
        pending, _pending_journal[:] = list(_pending_journal), []
        for item in pending:
            journal.append(**item)


def entry(data: dict, slug: str) -> dict:
    try:
        return data["ideas"][slug]
    except KeyError:
        raise SystemExit(f"no idea '{slug}' in the queue")


# ---------------------------------------------------------------------------
# Claims — "this idea is being worked on right now"
#
# `state` says where an idea has *got to*; a claim says someone is *in the
# middle of moving it*. They are deliberately two different fields. A driver
# spawns an agent that runs for minutes, and only writes the new state once
# that agent's output has passed its checker — so for the whole length of a
# step, `state` still reads exactly what it read before the step began. Under
# `/loop /bg` that is enough for the next tick to be handed the same work and
# spawn a second agent onto the same files.
#
# The claim is not folded into `state` (as an `in_progress` value) because
# `state` is the one field every other command reasons about: `require_state`
# guards the owner's replies with it, `advance` moves it, `PRIORITY` orders by
# it. Overwriting it would mean stashing the real state somewhere anyway and
# restoring it correctly on every exit path, including the crash paths. A
# separate lease that expires needs no restore — it just lapses.

def claim_of(item: dict) -> dict | None:
    """The item's claim if one is live, else None. An expired claim is dead:
    the driver that took it is gone or wedged, and the work is free again."""
    claim = item.get("claim")
    if not claim:
        return None
    expires = parse_ts(claim.get("expires", ""))
    if expires is None or expires <= datetime.now(timezone.utc):
        return None
    return claim


def claim_age(claim: dict) -> str:
    started = parse_ts(claim.get("at", ""))
    if started is None:
        return "?"
    seconds = int((datetime.now(timezone.utc) - started).total_seconds())
    return f"{seconds // 60}m" if seconds >= 60 else f"{seconds}s"


def take_claim(item: dict, action: str, state: str) -> dict:
    claim = {
        "action": action,
        "state": state,
        "at": now(),
        "expires": (datetime.now(timezone.utc)
                    + timedelta(seconds=CLAIM_TTL_SECONDS)).isoformat(),
        "by": f"{socket.gethostname()}:{os.getpid()}",
    }
    item["claim"] = claim
    return claim


def drop_claim(item: dict) -> dict | None:
    return item.pop("claim", None)


# Which state each owner-reply command is only ever valid from. A one-tap
# Telegram button makes it far easier to act on a stale message (one sitting
# in chat history from days ago, already superseded) than a pasted command
# ever was — these commands used to mutate state unconditionally regardless
# of where the idea actually was, so a stray tap could silently corrupt it
# (e.g. `approve` freezing a pre-rework render as the reference). Refuse
# instead of guessing.
EXPECTED_STATE = {
    "approve":     {"awaiting_owner"},
    "rework":      {"awaiting_owner"},
    "gate_rework": {"proposed"},
    "reject":      {"awaiting_owner", "awaiting_ship"},
    "ship":        {"awaiting_ship"},
    "amend":       {"blocked"},
}


def require_state(item: dict, slug: str, cmd: str) -> None:
    allowed = EXPECTED_STATE[cmd]
    if item["state"] not in allowed:
        raise SystemExit(
            f"{slug} is '{item['state']}', not {sorted(allowed)} — refusing "
            f"'{cmd}'. This is usually a reply to a stale message; check "
            f"`pipeline_queue.py list` for the current state.")


def log(item: dict, frm: str, to: str, note: str = "",
        by: str = "pipeline", kind: str = "state") -> None:
    """Record a transition in the queue and in the local dashboard journal.

    Both are written from one place so dashboard history cannot quietly fall
    behind queue state. Telegram is deliberately not involved here.
    """
    item.setdefault("log", []).append(
        {"at": now(), "from": frm, "to": to, "note": note})
    _pending_journal.append({
        "slug": item["slug"], "kind": kind, "by": by,
        "summary": f"{frm} → {to}" + (f"\n{note}" if note else ""),
        "title": item.get("title", item["slug"]),
    })


def gate_unmeasured(slug: str) -> list:
    """What the deterministic gate could not reach a verdict on, last run.

    gate.py records these and deliberately does not fail on them: pieces
    resting in contact legitimately merge in the assembled mesh, so failing
    would be a false alarm on correct designs and the gate would be routed
    around inside a week. The cost has to land somewhere though, or "we did not
    look" is free — so it lands here, where it follows the idea through the
    queue and stops at `ship` until a human accepts it by name.

    Read from the file rather than taken from the driver's report, because a
    step that can report this itself is a step that can forget to.
    """
    report = IDEAS / slug / "project" / "gate.json"
    if not report.is_file():
        return []
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"gate.json could not be read ({type(exc).__name__}), so not even "
                f"the list of what went unmeasured is known"]
    if "unmeasured" in data:
        return [str(note) for note in data.get("unmeasured") or []]
    # A gate.json written before the field existed. Dig the notes out of where
    # they used to live; reporting a clean run would be the one wrong answer.
    return [f"interference: {note}"
            for note in (data.get("interference") or {}).get("inconclusive") or []]


# ---------------------------------------------------------------------------

def cmd_add(args) -> int:
    with transaction() as data:
        if args.slug in data["ideas"]:
            raise SystemExit(f"'{args.slug}' is already in the queue")
        data["ideas"][args.slug] = {
            "slug": args.slug, "title": args.title or args.slug,
            "state": "proposed", "repairs_used": 0, "rework_used": 0,
            "clarify_used": 0,
            "created": now(), "log": [],
        }
        # The idea now exists, so the propose slot this driver was holding has
        # done its job and the next tick is free to propose again.
        data.pop("propose_claim", None)
        (IDEAS / args.slug).mkdir(parents=True, exist_ok=True)
        _pending_journal.append({
            "slug": args.slug, "kind": "proposed", "by": "pipeline",
            "summary": f"entered the queue as “{args.title or args.slug}”",
            "title": args.title or args.slug,
        })
    print(f"added {args.slug} (proposed)")
    return 0


def _rules_ok_gate_complete(slug: str) -> str | None:
    """Return a refusal reason when an idea is not allowed to leave the rules
    gate, or None when it may.

    The rules gate is not over when `rules_check.py` and `board-game-lens-rules`
    pass. The gate only finishes when the game has actually been played —
    by scripted policies (`playtest.py`) and by LLM players at the table
    (`table_run.py`) — and `board-game-lens-playtest` has written its verdict.
    `review_playtest.md` is that verdict. If it is missing, or older than the
    rules it judged, the idea is still at the gate: it has never had players sit
    at it under these rules. The `advance --to rules_ok` must refuse so this gap
    can never be walked through silently.
    """
    try:
        idea = IDEAS / slug / "idea.json"
        review = IDEAS / slug / "review_playtest.md"
        if not review.is_file():
            return (f"refusing proposed -> rules_ok: no "
                    f"board-game/ideas/{slug}/review_playtest.md — the game has "
                    f"not been played by LLM players and judged by "
                    f"board-game-lens-playtest. Run playtest.py, table_run.py, "
                    f"then the lens before advancing.")
        if review.stat().st_mtime < idea.stat().st_mtime:
            return (f"refusing proposed -> rules_ok: review_playtest.md is older "
                    f"than idea.json — the rules changed after the last playtest "
                    f"and the verdict no longer judges them. Re-run the gate "
                    f"(playtest.py, table_run.py, board-game-lens-playtest).")
        snapshot_path = IDEAS / slug / ".idea_before_rework.json"
        if snapshot_path.is_file():
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            request = snapshot.get("request") or {}
            if snapshot.get("disposition") == "rework" and request.get(
                    "problem_id"):
                verdict = review.read_text(encoding="utf-8")
                target = re.search(
                    r"^Target-result:\s*(fixed|not-fixed)\s*$",
                    verdict, re.M | re.I)
                regression = re.search(
                    r"^Regression-result:\s*(clean|regressed)\s*$",
                    verdict, re.M | re.I)
                clean_games = re.search(
                    r"^Clean-games:\s*(\d+)\s*$", verdict, re.M | re.I)
                if not target or not regression or not clean_games:
                    return ("refusing proposed -> rules_ok: the post-rework "
                            "review must report Target-result, "
                            "Regression-result, and Clean-games")
                if target.group(1).lower() != "fixed":
                    return ("refusing proposed -> rules_ok: the review says the "
                            "rework target was not fixed")
                if regression.group(1).lower() != "clean":
                    return ("refusing proposed -> rules_ok: the review reports "
                            "a regression; classify it through gate_rework")
                if int(clean_games.group(1)) < 2:
                    return ("refusing proposed -> rules_ok: a reworked candidate "
                            "needs at least two clean table games before it "
                            "becomes the new baseline")
    except FileNotFoundError:
        return f"refusing proposed -> rules_ok: idea.json is missing for {slug}"
    return None


def cmd_advance(args) -> int:
    """Move an idea to its next state — and, with it, end the step.

    A step is over exactly when its state changes, so this is where the claim
    is dropped. Any driver that was blocked out of this idea while the step ran
    is free to pick up the next one immediately, with no wait for the lease.

    It is also where the gate's `unmeasured` list is picked up. A state change
    is the one moment every step passes through, so attaching it here means no
    driver has to remember to carry it and none of them can decline to.
    """
    with transaction() as data:
        item = entry(data, args.slug)
        frm = item["state"]
        if args.to not in PIPELINE:
            raise SystemExit(f"unknown state '{args.to}'")
        if frm == "proposed" and args.to not in {"proposed", "blocked"}:
            # Leaving the rules gate settles the previous round's snapshot,
            # which is what this advance is about to replace. A clarify that
            # quietly changed a mechanic is charged here, not on the next
            # idea's schedule. `blocked` is deliberately exempt: an ideator
            # that correctly refuses a high-level same-slug rewrite has made
            # no candidate to settle, and blocking is how it asks for the
            # explicit fork/kill decision.
            _settle_open_round(item, args.slug)
        if args.to == "rules_ok":
            block = _rules_ok_gate_complete(args.slug)
            if block:
                raise SystemExit(block)
        item["state"] = args.to
        unmeasured = gate_unmeasured(args.slug)
        item["unmeasured"] = unmeasured
        drop_claim(item)
        note = args.note or ""
        if unmeasured:
            note = (note + " · " if note else "") + (
                f"{len(unmeasured)} gate check(s) reached no verdict — carried, "
                f"and ship will ask for an explicit acceptance")
        log(item, frm, args.to, note)
    print(f"{args.slug}: {frm} -> {args.to}"
          + (f" ({len(unmeasured)} unmeasured)" if unmeasured else ""))
    return 0


def cmd_repair(args) -> int:
    """Consume one repair round. Refuses past the budget — the caller is meant
    to escalate to arbitration, not to keep going."""
    with transaction() as data:
        item = entry(data, args.slug)
        used = int(item.get("repairs_used", 0))
        if used >= REPAIR_BUDGET:
            print(f"BUDGET EXHAUSTED {args.slug}: {used}/{REPAIR_BUDGET} repair "
                  f"rounds spent — escalate to arbitration, do not repair again")
            return 1
        item["repairs_used"] = used + 1
        frm = item["state"]
        item["state"] = "repairing"
        # A repair happens *inside* the step that called it: the driver is
        # still holding this idea and is about to run the builder again. Renew
        # the lease rather than dropping it, so the extra rounds cannot outlive
        # the claim and let a second driver in mid-repair.
        if claim_of(item):
            take_claim(item, "repair", "repairing")
        log(item, frm, "repairing", f"repair round {used + 1}/{REPAIR_BUDGET}",
            kind="repair")
    print(f"{args.slug}: repair round {used + 1}/{REPAIR_BUDGET}")
    return 0


def _settle_clarify_round(item: dict, slug: str) -> None:
    """Check, after the fact, that the round just finished kept its word.

    Called from the two queue actions an idea in `proposed` can take next
    (another round, or advance out of the gate), while the previous round's
    snapshot is still the one on disk. A clarify round promised not to change
    how the game functions; the mechanic surface frozen when the round was
    granted is the receipt. If it moved, the gate's classification is void —
    the fix *was* a mechanic change, which is a rework. Charge the rework
    budget, refund the clarify budget, and say so in the log. The rework
    counter now stands where an honest rework would have put it, so the next
    failed gate kills the idea the way it would have: the laundered round is
    not free, it is just discovered late.

    This is why the disposition is the gate's to assign and the queue's to
    enforce, not the fixer's to claim: the fixer writes the new `idea.json`
    and cannot see this check, and the fingerprint is computed here from the
    files, not from anything the fixer declared.
    """
    snapshot_path = IDEAS / slug / ".idea_before_rework.json"
    if not snapshot_path.is_file():
        return
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    # A snapshot is settled at most once. The idea's next action is either
    # another round or leaving the gate, never both, so this should be
    # redundant — but a double-charge would kill an idea over bookkeeping,
    # and this feature exists precisely so the accounting is bulletproof.
    if snapshot.get("settled") or snapshot.get("disposition") != "clarify":
        return
    frozen = snapshot.get("mech_surface")
    idea_path = IDEAS / slug / "idea.json"
    if not frozen or not idea_path.is_file():
        return
    idea = json.loads(idea_path.read_text(encoding="utf-8"))
    if mech_surface(idea) == frozen:
        return
    snapshot["settled"] = True
    tmp = snapshot_path.with_suffix(snapshot_path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    os.replace(tmp, snapshot_path)
    item["clarify_used"] = max(0, int(item.get("clarify_used", 0)) - 1)
    item["rework_used"] = int(item.get("rework_used", 0)) + 1
    spent = item["rework_used"]
    note = (f"clarify round converted to rework: the mechanic surface changed "
            f"during a clarification round — {spent}/{REWORK_BUDGET} reworks "
            f"now spent"
            + ("; budget already exhausted" if spent >= REWORK_BUDGET else ""))
    log(item, item["state"], item["state"], note, kind="rework")


def _settle_rework_round(item: dict, slug: str) -> None:
    """Validate the design reasoning and record the actual complexity delta."""
    snapshot_path = IDEAS / slug / ".idea_before_rework.json"
    if not snapshot_path.is_file():
        return
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot.get("settled") or snapshot.get("disposition") != "rework":
        return
    plan = _validate_rework_plan(slug, snapshot)
    if not plan:  # legacy snapshot with no structured request
        return
    idea_path = IDEAS / slug / "idea.json"
    if not idea_path.is_file():
        raise SystemExit(f"{slug}: idea.json is missing while settling rework")
    current_idea = json.loads(idea_path.read_text(encoding="utf-8"))
    before_contract = (snapshot.get("idea") or {}).get("design_contract")
    after_contract = current_idea.get("design_contract")
    if before_contract != after_contract and not plan.get("contract_change_reason"):
        raise SystemExit(
            f"{slug}: the rework changed design_contract without a non-empty "
            f"contract_change_reason in rework_plan.json")
    after = rule_complexity(current_idea)
    before = snapshot.get("complexity_before") or {}
    snapshot["complexity_after"] = after
    snapshot["complexity_delta"] = {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in sorted(set(before) | set(after))
    }
    snapshot["rework_plan"] = plan
    snapshot["settled"] = True
    tmp = snapshot_path.with_suffix(snapshot_path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    os.replace(tmp, snapshot_path)
    relative = snapshot.get("archive_path")
    if relative:
        archive = IDEAS / slug / relative
        archive.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def _settle_open_round(item: dict, slug: str) -> None:
    _settle_clarify_round(item, slug)
    _settle_rework_round(item, slug)


def cmd_gate_rework(args) -> int:
    """Consume one rules-gate round. The gate's Disposition decides which
    budget pays for it.

    This is `rules_gate`'s counterpart to `cmd_repair`: same shape, earlier
    loop. `rules_check.py`, `board-game-lens-rules`, and
    `board-game-lens-playtest` all funnel a failing idea back here before the
    caller reworks it. A round dispositioned `clarify` spends the clarify
    budget — the finding was ambiguity, and the fix is rule text; a round
    dispositioned `rework` spends the rework budget — the finding is a defect
    in how the game functions. Each budget, once exhausted, kills the idea on
    the next failed gate instead of granting another round.

    A clarify round's promise is checked after the fact by
    `_settle_clarify_round`, on the idea's next queue action.
    """
    with transaction() as data:
        item = entry(data, args.slug)
        require_state(item, args.slug, "gate_rework")
        # Settle the previous round before the new one overwrites its
        # snapshot: if it was a clarify that changed the mechanics, it pays
        # out of the rework budget before this round is granted.
        _settle_open_round(item, args.slug)
        if args.disposition == "clarify":
            used, budget = int(item.get("clarify_used", 0)), CLARIFY_BUDGET
            counter, label = "clarify_used", "clarify"
        else:
            used, budget = int(item.get("rework_used", 0)), REWORK_BUDGET
            counter, label = "rework_used", "rework"
        frm = item["state"]
        if used >= budget:
            item["state"] = "killed"
            item["kill_reason"] = (
                f"{label} budget exhausted ({used}/{budget} {label} rounds) and "
                f"still failing {args.stage}: {args.reason}")
            drop_claim(item)
            log(item, frm, "killed", item["kill_reason"], kind=label)
            print(f"{label.upper()} BUDGET EXHAUSTED {args.slug}: {used}/{budget} "
                  f"{label} rounds spent — killed, do not send to the ideator "
                  f"again. Record the reason in TASTE.md.")
            return 1
        request = None
        if label == "rework":
            problem_id = str(getattr(args, "problem_id", "") or "").strip()
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", problem_id):
                raise SystemExit(
                    "rework rounds require --problem-id as stable kebab-case "
                    "diagnosis (for example opening-script or unreachable-ending)")
            history = item.setdefault("problem_history", [])
            previous = history[-1] if history else None
            lineage = str(getattr(args, "lineage", "") or "").strip()
            severity = str(getattr(args, "severity", "") or "").strip()
            if previous and previous.get("problem_id") == problem_id:
                lineage = "target-persisted"
                severity = severity or "equal"
            elif previous:
                if lineage not in {"caused-regression", "new-independent"}:
                    raise SystemExit(
                        "a new Problem-ID after a rework requires --lineage "
                        "caused-regression or --lineage new-independent; this "
                        "prevents A -> B -> C repair chains from looking like "
                        "unrelated first findings")
                if severity not in {"lower", "equal", "higher", "contract"}:
                    raise SystemExit(
                        "a new Problem-ID after a rework requires --severity "
                        "lower, equal, higher, or contract")
                if lineage == "caused-regression" and severity in {
                        "equal", "higher", "contract"}:
                    frm = item["state"]
                    item["state"] = "blocked"
                    item["cascade_block"] = {
                        "prior_problem_id": previous.get("problem_id"),
                        "problem_id": problem_id,
                        "severity": severity,
                        "stage": args.stage,
                        "reason": args.reason,
                        "at": now(),
                    }
                    drop_claim(item)
                    severity_phrase = (
                        "a contract" if severity == "contract"
                        else f"an {severity}")
                    note = (
                        f"cascade stopped: the last candidate for "
                        f"{previous.get('problem_id')} caused {problem_id}, "
                        f"{severity_phrase} regression. Revert that candidate or fork/"
                        f"kill the design; do not add a compensating rule.")
                    log(item, frm, "blocked", note, kind="rework")
                    print(f"CASCADE STOP {args.slug}: {note}")
                    return 2
            else:
                lineage = "initial"
                severity = severity or "unknown"
            occurrence = 1 + sum(
                1 for previous in history
                if previous.get("problem_id") == problem_id)
            request = {
                "problem_id": problem_id,
                "occurrence": occurrence,
                "required_strategy": "structural" if occurrence >= 2 else "any",
                "lineage": lineage,
                "severity": severity,
                "prior_problem_id": previous.get("problem_id") if previous else None,
                "stage": args.stage,
                "reason": args.reason,
                "at": now(),
            }
            history.append(request)
            _write_rework_request(args.slug, request)
        snapshot_before_rework(
            args.slug, used + 1, disposition=label, request=request)
        item[counter] = used + 1
        strategy_note = (
            f"; recurring problem {request['problem_id']} requires "
            f"subtract/rollback/replace"
            if request and request["required_strategy"] == "structural" else "")
        log(item, frm, frm,
            f"{label} round {used + 1}/{budget} ({args.stage}): {args.reason}"
            f"{strategy_note}",
            kind=label)
    suffix = (
        f" — {request['problem_id']} occurrence {request['occurrence']}; "
        f"structural change required"
        if request and request["required_strategy"] == "structural" else "")
    print(f"{args.slug}: {label} round {used + 1}/{budget}{suffix}")
    return 0


def cmd_release(args) -> int:
    """Give up a claim without moving the idea.

    The counterpart to `advance` for every way a step can end without
    finishing: a gate that failed, an agent that errored, a driver shutting
    down. Without it a dead step's idea is invisible to `next` until the lease
    lapses, which is correct but slow — this makes it immediate.
    """
    with transaction() as data:
        if args.slug == "propose":
            existed = data.pop("propose_claim", None) is not None
        else:
            existed = drop_claim(entry(data, args.slug)) is not None
    print(f"{args.slug}: claim released" if existed
          else f"{args.slug}: no claim to release")
    return 0


def cmd_approve(args) -> int:
    """Gate 1: the owner looked at the draft and said build it.

    The approved renders become `reference/` — a visual contract the final
    build is held to. This is the one moment a human agrees the design is
    worth making, so it is worth freezing rather than remembering.
    """
    with transaction() as data:
        item = entry(data, args.slug)
        require_state(item, args.slug, "approve")
        home = IDEAS / args.slug
        reference = home / "reference"
        reference.mkdir(parents=True, exist_ok=True)
        copied = 0
        for png in sorted((home / "draft").rglob("*.png")):
            (reference / png.name).write_bytes(png.read_bytes())
            copied += 1
        if not copied:
            print(f"warning: no draft renders found under {home / 'draft'} — the "
                  f"build will have no visual contract to match")
        frm = item["state"]
        item["state"] = "approved"
        drop_claim(item)
        log(item, frm, "approved", f"owner approved the draft; {copied} renders frozen",
            by="owner", kind="owner")
    print(f"{args.slug}: approved — {copied} render(s) frozen as reference/")
    return 0


def cmd_amend(args) -> int:
    """Apply an arbitration proposal the owner accepted.

    This resets the repair budget, and that is not a loophole: an amended
    brief is a different design, not a fourth attempt at the old one. The
    reset happens only because a human read the proposal and applied it — an
    agent cannot reach this path on its own.
    """
    with transaction() as data:
        item = entry(data, args.slug)
        require_state(item, args.slug, "amend")
        home = IDEAS / args.slug
        proposed = home / "brief_proposed.json"
        if not proposed.is_file():
            raise SystemExit(f"no brief_proposed.json for '{args.slug}'")
        (home / "brief.json").write_text(proposed.read_text(encoding="utf-8"),
                                         encoding="utf-8")
        proposed.unlink()
        frm = item["state"]
        item["state"] = "approved"
        item["repairs_used"] = 0
        drop_claim(item)
        log(item, frm, "approved", "owner applied the arbitration amendment; "
            "budget reset for the amended design", by="owner", kind="owner")
    print(f"{args.slug}: brief amended, repair budget reset")
    return 0


def cmd_ship(args) -> int:
    """Gate 2: the owner said make it real.

    Refuses while the gate has a check that reached no verdict, unless the
    owner names what they are accepting. This is the only place in the pipeline
    where "nothing looked at this" costs anything — gate.py cannot charge for
    it without failing correct designs — and it is deliberately a human's to
    spend: no agent has a path to this command.
    """
    with transaction() as data:
        item = entry(data, args.slug)
        require_state(item, args.slug, "ship")
        unmeasured = gate_unmeasured(args.slug)
        item["unmeasured"] = unmeasured
        if unmeasured and not args.accept_unmeasured:
            listed = "\n".join(f"  - {note}" for note in unmeasured)
            raise SystemExit(
                f"{args.slug}: the gate passed, but {len(unmeasured)} check(s) "
                f"never reached a verdict:\n{listed}\n"
                f"Shipping now means shipping something nothing looked at. If "
                f"that is the call, say what you are accepting:\n"
                f"  ship {args.slug} --accept-unmeasured \"why this is fine\"")
        frm = item["state"]
        item["state"] = "shipped"
        item["shipped_at"] = now()
        note = "owner approved"
        if unmeasured:
            item["unmeasured_accepted"] = {
                "at": now(), "reason": args.accept_unmeasured, "items": unmeasured}
            note += (f"; accepted {len(unmeasured)} unmeasured check(s): "
                     f"{args.accept_unmeasured}")
        drop_claim(item)
        log(item, frm, "shipped", note, by="owner", kind="owner")
    print(f"{args.slug}: SHIPPED")
    # Shipping is a decision, not a publication. Say where the decision goes
    # next so a shipped game does not quietly sit in the repo forever.
    print(f"  next: .venv/bin/python board-game/tools/publish.py {args.slug}")
    return 0


def cmd_reject(args) -> int:
    """The owner said no. The reason is the single most valuable sentence in
    this pipeline: it is the only signal that comes from a human, and it goes
    into TASTE.md where every future ideation reads it."""
    with transaction() as data:
        item = entry(data, args.slug)
        require_state(item, args.slug, "reject")
        frm = item["state"]
        item["state"] = "killed"
        item["kill_reason"] = args.reason
        drop_claim(item)
        log(item, frm, "killed", args.reason, by="owner", kind="owner")

    if not TASTE.is_file():
        TASTE.write_text(
            "# TASTE — the owner's own words\n\n"
            "Every line here is a rejection reason, verbatim. This is the only\n"
            "signal in the pipeline that does not come from a model, so it\n"
            "outranks every heuristic an agent has learned on its own.\n"
            "`board-game-ideator` reads this file before it invents anything.\n\n",
            encoding="utf-8")
    with TASTE.open("a", encoding="utf-8") as fh:
        fh.write(f"- REJECTED **{item.get('title', args.slug)}** "
                 f"({args.slug}): {args.reason}\n")
    print(f"{args.slug}: killed — reason recorded in TASTE.md")
    return 0


def cmd_rework(args) -> int:
    with transaction() as data:
        item = entry(data, args.slug)
        require_state(item, args.slug, "rework")
        snapshot_before_rework(args.slug)
        frm = item["state"]
        item["state"] = "proposed"
        item["rework_reason"] = args.reason
        drop_claim(item)
        log(item, frm, "proposed", f"owner asked for a rules change: {args.reason}",
            by="owner", kind="owner")
    print(f"{args.slug}: back to proposed for rework")
    return 0


def cmd_next(args) -> int:
    """Print the one thing that should happen now, as JSON, and claim it.

    The driver reads this and does exactly that — it does not get to pick. And
    because handing out the work and marking it taken happen together, under
    the lock, two drivers running at once cannot be handed the same step: the
    second one is told to wait.

    `--peek` reports without claiming, for looking at the queue without
    disturbing it. Never run the driver off a peek.
    """
    claim_this = not args.peek
    with transaction() as data:
        in_progress = []
        for state in PRIORITY:
            for slug, item in sorted(data["ideas"].items()):
                if item["state"] != state:
                    continue
                action, to = PIPELINE[state]
                if action is None:
                    continue
                held = claim_of(item)
                if held:
                    in_progress.append(
                        f"{slug} ({held['action']}, {claim_age(held)} in, "
                        f"by {held.get('by', '?')})")
                    continue
                out = {
                    "slug": slug, "title": item.get("title", slug),
                    "state": state, "action": action, "next_state": to,
                    "repairs_used": item.get("repairs_used", 0),
                    "repair_budget": REPAIR_BUDGET,
                    "rework_used": item.get("rework_used", 0),
                    "rework_budget": REWORK_BUDGET,
                    "clarify_used": item.get("clarify_used", 0),
                    "clarify_budget": CLARIFY_BUDGET,
                    "dir": str(IDEAS / slug),
                }
                if claim_this:
                    out["claim"] = take_claim(item, action, state)
                print(json.dumps(out, indent=2))
                return 0

        # Nothing advanceable. Before falling back to proposing a new idea,
        # check whether that is also already being done — `propose` has no slug
        # to hang a claim on, so it gets one of its own. Without it, a fast
        # loop with everything else in progress would spawn an ideator every
        # single tick.
        propose_held = data.get("propose_claim")
        if propose_held:
            expires = parse_ts(propose_held.get("expires", ""))
            if expires is None or expires <= datetime.now(timezone.utc):
                propose_held = None
        if propose_held:
            in_progress.append(
                f"propose ({claim_age(propose_held)} in, "
                f"by {propose_held.get('by', '?')})")

        if in_progress:
            print(json.dumps({
                "action": "wait",
                "reason": "every advanceable idea is already being worked on",
                "in_progress": in_progress}, indent=2))
            return 0

        waiting = [s for s, i in data["ideas"].items()
                   if i["state"] in ("awaiting_owner", "awaiting_ship")]
        out = {"action": "propose",
               "reason": ("every idea in the queue is waiting on the owner"
                          if waiting else "the queue has nothing to advance"),
               "waiting_on_owner": waiting}
        if claim_this:
            holder = {
                "action": "propose", "at": now(),
                "expires": (datetime.now(timezone.utc)
                            + timedelta(seconds=CLAIM_TTL_SECONDS)).isoformat(),
                "by": f"{socket.gethostname()}:{os.getpid()}",
            }
            data["propose_claim"] = holder
            out["claim"] = holder
        print(json.dumps(out, indent=2))
    return 0


def cmd_list(args) -> int:
    data = load()
    if not data["ideas"]:
        print("queue is empty")
        return 0
    width = max(len(s) for s in data["ideas"])
    for slug, item in sorted(data["ideas"].items(),
                             key=lambda kv: PRIORITY.index(kv[1]["state"])
                             if kv[1]["state"] in PRIORITY else 99):
        repairs = item.get("repairs_used", 0)
        rework = item.get("rework_used", 0)
        clarify = item.get("clarify_used", 0)
        tail = f"  repairs {repairs}/{REPAIR_BUDGET}" if repairs else ""
        tail += f"  reworks {rework}/{REWORK_BUDGET}" if rework else ""
        tail += f"  clarifies {clarify}/{CLARIFY_BUDGET}" if clarify else ""
        note = f"  — {item['kill_reason']}" if item.get("kill_reason") else ""
        held = claim_of(item)
        busy = f"  [in progress: {held['action']}, {claim_age(held)}]" if held else ""
        # Visible without being alarming: an unmeasured check is not a failure,
        # but an idea sitting one tap from `shipped` carrying two of them is
        # something the owner should meet here rather than at the refusal.
        skipped = item.get("unmeasured") or []
        gap = (f"  ({len(skipped)} unmeasured{', accepted' if item.get('unmeasured_accepted') else ''})"
               if skipped else "")
        print(f"  {slug:<{width}}  {item['state']:<14}{tail}{busy}{gap}{note}")
    if data.get("propose_claim"):
        held = data["propose_claim"]
        expires = parse_ts(held.get("expires", ""))
        if expires and expires > datetime.now(timezone.utc):
            print(f"  {'(propose)':<{width}}  {'—':<14}"
                  f"  [in progress: propose, {claim_age(held)}]")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add"); p.add_argument("slug"); p.add_argument("--title")
    p.set_defaults(fn=cmd_add)
    p = sub.add_parser("advance"); p.add_argument("slug")
    p.add_argument("--to", required=True); p.add_argument("--note")
    p.set_defaults(fn=cmd_advance)
    p = sub.add_parser("repair"); p.add_argument("slug"); p.set_defaults(fn=cmd_repair)
    p = sub.add_parser("gate_rework"); p.add_argument("slug")
    p.add_argument("--stage", required=True,
                   choices=["rules_check", "lens_rules", "lens_playtest"])
    p.add_argument("--disposition", default="rework",
                   choices=["clarify", "rework"],
                   help="what the failing gate classified the round as: clarify "
                        "spends the clarify budget (ambiguity only), rework the "
                        "rework budget (mechanic defect). Default rework, so a "
                        "gate that does not say is never free.")
    p.add_argument("--problem-id",
                   help="stable kebab-case diagnosis for a rework; repeated IDs "
                        "force subtraction, rollback, or replacement")
    p.add_argument("--lineage",
                   choices=["caused-regression", "new-independent"],
                   help="required when a post-rework failure has a new "
                        "Problem-ID")
    p.add_argument("--severity",
                   choices=["lower", "equal", "higher", "contract"],
                   help="required with --lineage; contract means a "
                        "must_preserve or anti_goal regression")
    p.add_argument("--reason", required=True); p.set_defaults(fn=cmd_gate_rework)
    p = sub.add_parser("release", help="drop a claim without moving the idea")
    p.add_argument("slug", help="the idea's slug, or 'propose'")
    p.set_defaults(fn=cmd_release)
    p = sub.add_parser("approve"); p.add_argument("slug"); p.set_defaults(fn=cmd_approve)
    p = sub.add_parser("amend"); p.add_argument("slug"); p.set_defaults(fn=cmd_amend)
    p = sub.add_parser("ship"); p.add_argument("slug")
    p.add_argument("--accept-unmeasured", metavar="REASON",
                   help="ship even though the gate could not measure something; "
                        "the reason is recorded on the idea")
    p.set_defaults(fn=cmd_ship)
    p = sub.add_parser("reject"); p.add_argument("slug")
    p.add_argument("--reason", required=True); p.set_defaults(fn=cmd_reject)
    p = sub.add_parser("rework"); p.add_argument("slug")
    p.add_argument("--reason", required=True); p.set_defaults(fn=cmd_rework)
    p = sub.add_parser("next")
    p.add_argument("--peek", action="store_true",
                   help="report without claiming — for looking, not for driving")
    p.set_defaults(fn=cmd_next)
    sub.add_parser("list").set_defaults(fn=cmd_list)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
