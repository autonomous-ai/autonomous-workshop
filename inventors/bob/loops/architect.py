"""L3 architect loop — weekly harness study; notes and proposals, never code.

Why weekly and why proposals-only (ARCHITECTURE.md L3): the outside world's
harness lessons (Anthropic engineering, the sibling inventors vibe-ideas and
text2cad, autonomous-org canon) change on a weeks scale, and "an architect
who edits the running pipeline is just a second improver with less
oversight" (bob-architect prompt). So this loop:

- runs AT MOST weekly, gated by a last-run stamp in state/DAYBOOK.json
  (module state dies with the process; launchd ticks are separate
  processes, so only a file can throttle),
- calls bob-architect WITHOUT cwd — run_agent grants a prompt-only call no
  tools (harness/agents.py), so the agent physically cannot edit anything,
- appends the reply to knowledge/architecture-notes.md (memory) and lifts
  its `## P-...` sections into knowledge/PROPOSALS.md (advocacy) — the
  meta loop and a human decide what lands.

The stamp is written only AFTER a successful sweep: a crashed or empty run
retries next tick instead of silently skipping a week (text2cad blackout
receipt: a silent channel must not look like a quiet one).

Stdlib only, Python 3.9. No env reads at import time (CONTRACTS §6).
"""

import fcntl
import json
import os
import re
from datetime import datetime, timezone

from harness import agents

# At-most-weekly. 7 days exactly — launchd fires every 30 min, so the
# sweep lands within half an hour of the boundary; no need for slop.
INTERVAL_SECONDS = 7 * 24 * 3600.0

# DAYBOOK key for the last successful sweep (UTC ISO-8601).
STAMP_KEY = "architect_last_run"

# How much of the notes tail the agent sees, so it can tell "new since my
# last visit" from "already carded" without rereading a growing file.
NOTES_TAIL_CHARS = 3000

# A proposal section in the reply, per the bob-architect output contract:
# "## P-<date>-<n>: <title>". Captured through to the next H2 or EOF.
_PROPOSAL_RE = re.compile(
    r"^##\s+P-.*?(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)

AGENT = "bob-architect"


def _home():
    return os.environ.get("BOB_HOME") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _now():
    return datetime.now(timezone.utc)


def _atomic_write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "{}.tmp.{}".format(path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _read_daybook():
    path = os.path.join(_home(), "state", "DAYBOOK.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except ValueError:
        return {}


def _stamp_last_run():
    """Write the stamp under the daybook's own flock (state/.daybook.lock,
    same lock agents.py telemetry uses) so we can't drop a concurrent
    cost row in the read-modify-write."""
    state_dir = os.path.join(_home(), "state")
    os.makedirs(state_dir, exist_ok=True)
    lock_path = os.path.join(state_dir, ".daybook.lock")
    book_path = os.path.join(state_dir, "DAYBOOK.json")
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            book = _read_daybook()
            book[STAMP_KEY] = _now().isoformat()
            _atomic_write(book_path, json.dumps(book, indent=1))
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _due():
    """True when no successful sweep in the last INTERVAL_SECONDS.
    An unparseable stamp counts as due — better one extra sweep than a
    throttle wedged shut by a corrupt timestamp."""
    stamp = _read_daybook().get(STAMP_KEY)
    if not stamp:
        return True
    try:
        ts = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except ValueError:
        return True
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (_now() - ts).total_seconds() >= INTERVAL_SECONDS


def _read(path):
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _prompt_file():
    for base in (_home(), _repo_root()):
        p = os.path.join(base, ".claude", "agents", AGENT + ".md")
        if os.path.exists(p):
            content = _read(p)
            if content:
                return content
    return ""


def _append_section(path, section):
    """Append one block to a knowledge file, whole-file atomic replace
    (files are small; this keeps the CONTRACTS atomicity rule without a
    per-file locking scheme — the architect is the only weekly writer,
    serialized by the throttle itself)."""
    existing = _read(path)
    if existing and not existing.endswith("\n"):
        existing += "\n"
    _atomic_write(path, existing + section)


def tick():
    """One architect tick: weekly sweep or no-op.

    Contract (CONTRACTS §2): tick() -> None; the summary dict is a
    test/CLI superset. Never edits code — the only files this function
    writes are architecture-notes.md, PROPOSALS.md, and the DAYBOOK stamp,
    and the agent itself runs tool-less.
    """
    if not _due():
        return {"outcome": "throttled"}

    home = _home()
    sources = _read(os.path.join(home, "knowledge", "SOURCES.md"))
    if not sources.strip():
        # Misconfiguration, not a completed sweep: no stamp, so the loop
        # retries as soon as the file exists instead of sleeping a week.
        return {"outcome": "no_sources",
                "error": "knowledge/SOURCES.md missing or empty under "
                         "BOB_HOME={} — restore it from git.".format(home)}

    notes_path = os.path.join(home, "knowledge", "architecture-notes.md")
    notes_tail = _read(notes_path)[-NOTES_TAIL_CHARS:]

    prompt = "".join([
        _prompt_file(),
        "\n## knowledge/SOURCES.md (the sweep list)\n\n", sources,
        "\n## Tail of knowledge/architecture-notes.md (your last visits)"
        "\n\n", notes_tail or "(empty — this is the first sweep)",
        "\n\n## Output rule (harness contract)\n\nYou have no tools this "
        "session. Return your findings as markdown: the dated notes body, "
        "then any proposals as `## P-<date>-<n>: <title>` sections in the "
        "prescribed format. The harness appends notes and proposals to "
        "their files — not you. A sweep that found nothing new returns "
        "one dated line saying so.\n",
    ])

    try:
        result = agents.run_agent(AGENT, prompt)
        text = (result.text or "").strip()
    except agents.QuotaExhausted:
        raise  # tick-level state; the driver sets quota_until
    except agents.AgentError:
        # No stamp: a crashed sweep must retry next tick, not skip a week.
        return {"outcome": "agent_error"}

    if not text:
        return {"outcome": "empty_reply"}

    today = _now().strftime("%Y-%m-%d")
    _append_section(
        notes_path, "\n## Sweep {}\n\n{}\n".format(today, text))

    proposals = _PROPOSAL_RE.findall(text)
    if proposals:
        block = "\n" + "\n".join(p.strip() + "\n" for p in proposals)
        _append_section(
            os.path.join(home, "knowledge", "PROPOSALS.md"), block)

    _stamp_last_run()
    return {"outcome": "swept", "proposals": len(proposals)}
