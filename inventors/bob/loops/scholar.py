"""L2 scholar loop — one corpus card per tick, alternating two lanes.

Why this loop exists: 5,000 years of board games are free training data
nobody else is using (ARCHITECTURE.md L2). The scholar lane compresses
history (corpus/STUDY_QUEUE.json, agent bob-scholar); the librarian lane
compresses the design books through public materials only
(corpus/BOOK_QUEUE.json, agent bob-librarian — the honesty rule lives in
that file's comment and in the agent prompt). Cards are the ideator's raw
material and the novelty judge's comparison corpus.

Design decisions, with reasons:

- ALL file mutations happen HERE, in code, not in the agent. The agent is
  called without cwd, so run_agent grants it no tools (harness/agents.py:
  a prompt-only call gets no tools at all) — it returns card text and
  nothing else. A crashed agent therefore can never leave the queue
  half-mutated ("a stage is complete when this file says so, not when a
  model reports success" — vibe-ideas receipt, same creed as queue.py).
- Lane alternation via a cursor in state/DAYBOOK.json, not module state:
  ticks are separate processes under launchd; only a file survives.
- A short/empty card marks the unit 'retry' once, then 'failed' — NEVER
  silently done. "An absent lens verdict is not a passing one" (the
  one-way-newsreel lesson, docs/REWARD.md) applies to study cards too:
  a unit marked done with no card would poison the ideator's corpus
  index with a phantom citation.

Stdlib only, Python 3.9. No env reads at import time (CONTRACTS §6).
"""

import fcntl
import json
import os
import re
from datetime import datetime, timezone

from harness import agents

# The two lanes. Prefixes double as card-filename lane tags
# (corpus/cards/<lane>-<id>-<slug>.md, pinned by the build task).
LANES = ("study", "book")
LANE_SPEC = {
    "study": {"queue": os.path.join("corpus", "STUDY_QUEUE.json"),
              "agent": "bob-scholar"},
    "book": {"queue": os.path.join("corpus", "BOOK_QUEUE.json"),
             "agent": "bob-librarian"},
}

# Below this a "card" is a stub, an apology, or an error message — not
# study. 500 chars is well under any real card (the format alone has five
# required sections) but well over every observed failure blob.
MIN_CARD_CHARS = 500

# DAYBOOK key holding the lane that ran LAST (next tick prefers the other).
CURSOR_KEY = "scholar_lane"

# Filename slugs stay short so `ls corpus/cards/` remains a readable index.
SLUG_MAX_CHARS = 48


def _home():
    """BOB_HOME override or repo root. Read at call time (CONTRACTS §6)."""
    return os.environ.get("BOB_HOME") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))


def _repo_root():
    """The real checkout — fallback for prompt files when BOB_HOME is a
    test's temp dir (same two-candidate pattern as agents._mock_result)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _now():
    return datetime.now(timezone.utc)


def _atomic_write(path, data):
    """tmp + os.replace (CONTRACTS: a crash mid-write must never leave a
    half-written queue or card)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "{}.tmp.{}".format(path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _update_daybook(key, value):
    """Set one top-level DAYBOOK key under the same flock agents.py uses
    (state/.daybook.lock) — the daybook has concurrent writers (telemetry
    rows land after every agent call), so an unlocked read-modify-write
    here could drop a cost row. Same lock, no lost updates."""
    state_dir = os.path.join(_home(), "state")
    os.makedirs(state_dir, exist_ok=True)
    lock_path = os.path.join(state_dir, ".daybook.lock")
    book_path = os.path.join(state_dir, "DAYBOOK.json")
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            book = _read_daybook()
            book[key] = value
            _atomic_write(book_path, json.dumps(book, indent=1))
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _read_daybook():
    path = os.path.join(_home(), "state", "DAYBOOK.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except ValueError:
        # A corrupt daybook must not stop study; telemetry code preserves
        # the wreck (agents._append_daybook), we just proceed stateless.
        return {}


def _queue_path(lane):
    return os.path.join(_home(), LANE_SPEC[lane]["queue"])


def _load_queue(lane):
    path = _queue_path(lane)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except ValueError:
        # Corrupt queue: skip the lane rather than crash the tick — the
        # other lane can still study. The corrupt file stays for a human.
        return None


def _save_queue(lane, q):
    _atomic_write(_queue_path(lane), json.dumps(q, indent=2))


def _next_unit(q):
    """First unit that still needs work. 'retry' units are re-attempted in
    natural queue order — a retry is a todo with one strike, not a park."""
    if not q:
        return None
    for unit in q.get("units", []):
        if unit.get("status") in ("todo", "retry"):
            return unit
    return None


def _slugify(text):
    """Filename slug from a unit topic: lowercase, alnum+dash, capped.
    First words only — the id already disambiguates, the slug is for
    humans scanning the cards directory."""
    text = (text or "unit").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if len(text) > SLUG_MAX_CHARS:
        text = text[:SLUG_MAX_CHARS].rsplit("-", 1)[0]
    return text or "unit"


def _prompt_file(agent_name):
    """The roster prompt for this agent, BOB_HOME first (tests may plant
    their own), repo checkout second."""
    for base in (_home(), _repo_root()):
        p = os.path.join(base, ".claude", "agents", agent_name + ".md")
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError:
                pass
    return ""


def _compose_prompt(lane, unit):
    """Agent prompt = roster prompt + the one unit + a hard output rule.

    The output rule overrides the roster prompt's "write files yourself"
    instructions because this harness centralizes all writes (see module
    docstring) — the agent gets no tools either way, so the rule just
    makes the contract explicit instead of letting it fail confusingly.
    """
    parts = [_prompt_file(LANE_SPEC[lane]["agent"])]
    parts.append(
        "\n## Your unit for this tick (from {})\n\n{}\n".format(
            LANE_SPEC[lane]["queue"], json.dumps(unit, indent=2)))
    parts.append(
        "\n## Output rule (harness contract — overrides any file-writing "
        "instruction above)\n\nYou have no tools this session. Return ONLY "
        "the finished card markdown as your reply text. The harness writes "
        "the card file, updates corpus/INDEX.md, and marks the unit done — "
        "not you.\n")
    return "".join(parts)


def _card_title(text, fallback):
    """First markdown H1 in the card, else the unit topic — the INDEX.md
    line must name the card the way the card names itself."""
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _append_index_line(line):
    """One line per card in corpus/INDEX.md. Read-modify-replace atomically
    (the file is small; whole-file replace keeps the CONTRACTS atomicity
    rule without a second locking scheme)."""
    path = os.path.join(_home(), "corpus", "INDEX.md")
    existing = ""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = f.read()
    if existing and not existing.endswith("\n"):
        existing += "\n"
    _atomic_write(path, existing + line + "\n")


def _mark(unit, status, **extra):
    unit["status"] = status
    unit.update(extra)


def tick():
    """One scholar tick: study one unit from the lane whose turn it is.

    Contract (CONTRACTS §2): tick() -> None. Returns a small summary dict
    as a superset for tests and the CLI's status line; callers that expect
    None lose nothing by ignoring it.

    QuotaExhausted propagates — quota is a tick-level state the driver
    owns (ARCHITECTURE.md: "quota is a first-class state, not an error"),
    not something a study loop should paper over.
    """
    last = _read_daybook().get(CURSOR_KEY)
    if last in LANES:
        preferred = LANES[(LANES.index(last) + 1) % len(LANES)]
    else:
        preferred = LANES[0]
    order = [preferred, LANES[(LANES.index(preferred) + 1) % len(LANES)]]

    lane = None
    q = None
    unit = None
    for candidate in order:
        cq = _load_queue(candidate)
        cu = _next_unit(cq)
        if cu is not None:
            lane, q, unit = candidate, cq, cu
            break
    if unit is None:
        return {"lane": None, "unit": None, "outcome": "empty"}

    prompt = _compose_prompt(lane, unit)
    agent = LANE_SPEC[lane]["agent"]
    try:
        result = agents.run_agent(agent, prompt)
        text = (result.text or "").strip()
    except agents.QuotaExhausted:
        raise  # driver's problem: set quota_until, never retry into a wall
    except agents.AgentError:
        # Crash/starvation counts as a failed attempt: the unit burns one
        # of its two strikes rather than looping forever on a broken topic.
        text = ""

    today = _now().strftime("%Y-%m-%d")

    if len(text) < MIN_CARD_CHARS:
        # Empty or stub reply: retry once, then failed — never silently
        # done (a phantom done poisons the ideator's citation index).
        if unit.get("status") == "retry":
            _mark(unit, "failed", failed=today,
                  fail_reason="card under {} chars twice".format(
                      MIN_CARD_CHARS))
            outcome = "failed"
        else:
            _mark(unit, "retry", retry_marked=today)
            outcome = "retry"
        _save_queue(lane, q)
        _update_daybook(CURSOR_KEY, lane)  # a failed attempt still used
        # the lane's turn: alternation is about spend fairness, not success
        return {"lane": lane, "unit": unit.get("id"), "outcome": outcome}

    topic = unit.get("topic") or unit.get("book") or "unit"
    slug = _slugify(topic)
    card_name = "{}-{}-{}.md".format(lane, unit.get("id"), slug)
    card_path = os.path.join(_home(), "corpus", "cards", card_name)
    _atomic_write(card_path, text if text.endswith("\n") else text + "\n")

    title = _card_title(text, topic)
    _append_index_line("- {} — {} ({} unit {}, {})".format(
        card_name, title, lane, unit.get("id"), today))

    _mark(unit, "done", studied=today, card=card_name)
    _save_queue(lane, q)
    _update_daybook(CURSOR_KEY, lane)
    return {"lane": lane, "unit": unit.get("id"), "outcome": "done",
            "card": card_name}
