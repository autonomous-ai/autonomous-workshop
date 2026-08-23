"""claude-CLI runner: every LLM call in Bob goes through run_agent().

Why this module exists at all (instead of subprocess.run inline everywhere):
text2cad's ledger says 58% of $430 was lost to harness bugs, not bad
products — and most of those bugs were exactly the things this file
centralizes:

- Cost telemetry from the CLI's own JSON, persisted crash-safe after EVERY
  call, never overwritten (text2cad's run.json under-reported a cycle by 12%
  because repeated phases clobbered earlier rows — hence the #2 suffixes).
- Starved vs crashed, mechanically distinguished (text2cad receipt: "$49
  went to phases that were starved rather than wrong", and the pipeline
  "paid for a retry at the SAME cap"). Starved raises Starved; callers must
  raise the cap or cut the task, NEVER retry unchanged.
- Quota death as a first-class exception, never a retry ("once the weekly
  cap hits, each 'retry' burns wall-clock and produces nothing").
- Process-group kill on overrun (start_new_session + SIGTERM, 5s grace,
  SIGKILL) — the warm-daemon receipt: a plain .kill() leaves the CLI's
  child processes alive and the "dead" phase keeps burning tokens.
- BOB_MOCK_AGENTS=1 short-circuits the subprocess entirely and reads the
  reply from tests/fixtures/<name>.txt — required for tests and dry runs,
  so no test can ever hit the real CLI or the real wallet.

Stdlib only, Python 3.9. No env reads at import time (testability — every
test builds its own BOB_HOME and flips env per-case).
"""

import fcntl
import json
import os
import re
import shlex
import signal
import subprocess
import time
from collections import namedtuple
from datetime import datetime, timezone

# The three CLI failure classes have OPPOSITE correct responses, so they are
# distinct exception types — a caller that catches the wrong one repeats
# text2cad's most expensive mistakes.

class AgentError(Exception):
    """Transient crash (CLI died, bad JSON, error_during_execution).

    Retryable ONCE by the caller — text2cad's lens-crash graduated to
    exactly one retry after "lens:fidelity FAIL no output" cost 3 repair
    tiers across 3 recurrences.
    """


class Starved(AgentError):
    """The agent hit its turn cap (subtype == 'error_max_turns').

    NOT retryable at the same cap: "a cap that binds 3 times out of 3 is
    not a safety limit, it is the real constraint on the work" (text2cad,
    08-17: every scram repair ended at 71/70 turns). Raise the cap or cut
    the task down.
    """


class QuotaExhausted(Exception):
    """The subscription window is exhausted (usage/rate limit).

    Callers set DAYBOOK quota_until (now + 60 min) and the tick loop
    no-ops until then. Never retry into a wall — the 08-13 text2cad cycle
    died this way silently, burning wall-clock for nothing.

    Deliberately NOT a subclass of AgentError: a generic "retry once on
    AgentError" handler must never swallow a quota death.
    """


# Fields per the task contract (supersets CONTRACTS §2 with num_turns +
# subtype, which the daybook and the starved/crashed split both need).
AgentResult = namedtuple(
    "AgentResult",
    ["text", "cost_usd", "minutes", "num_turns", "transcript_path", "subtype"],
)

# Rate-limit fingerprints per CONTRACTS §6. Case-insensitive because the CLI
# has emitted "Usage limit reached" and "rate limit" in different casings.
QUOTA_RE = re.compile(r"usage limit|limit reached|rate limit|session limit|hit your (session|usage|weekly)? ?limit", re.IGNORECASE)

# 5s between SIGTERM and SIGKILL: long enough for the CLI to flush its JSON
# result line, short enough that an overrun tick doesn't blow the launchd
# window (the warm-daemon receipt).
KILL_GRACE_S = 5.0

# Default model when neither the caller nor env says otherwise. Sonnet is
# the cheap default; phases that cascade errors downstream get routed to a
# bigger model via BOB_<PHASE>_MODEL (per-phase routing IS the cost model —
# text2cad §a10).
DEFAULT_MODEL = "claude-sonnet-5"

# Tools granted only when the agent is given a working directory: a cwd
# means "go do repo work"; a prompt-only call gets no tools at all, which
# keeps pure-judge calls unable to touch the filesystem (judge isolation,
# REWARD.md "judges read artifacts only").
CWD_TOOLS = "Bash,Read,Write,Edit,Glob,Grep"


def _bob_home():
    """Repo root. BOB_HOME overrides (tests point it at a temp dir).

    Read at call time, never import time (CONTRACTS §6).
    """
    env = os.environ.get("BOB_HOME")
    if env:
        return os.path.abspath(env)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _utc_now():
    return datetime.now(timezone.utc)


def _atomic_write(path, data):
    """tmp + os.replace per CONTRACTS: a crash mid-write must never leave a
    half-JSON state file (that is how ledgers silently rot)."""
    tmp = "{}.tmp.{}".format(path, os.getpid())
    with open(tmp, "w") as f:
        f.write(data)
    os.replace(tmp, path)


def resolve_model(name, explicit=None):
    """Model resolution order: explicit arg > BOB_<PHASE>_MODEL > default.

    PHASE strips one leading ``bob-`` from Bob-owned role names, then maps
    dashes to underscores. Thus ``bob-ideator`` uses
    ``BOB_IDEATOR_MODEL`` rather than the accidental doubled-prefix
    ``BOB_BOB_IDEATOR_MODEL``. The doubled spelling remains a fallback for
    deployed env files, but setting both spellings differently fails closed.
    Other role names still map directly (``rules-lens`` uses
    ``BOB_RULES_LENS_MODEL``). Per-phase routing is the whole cost model:
    text2cad ran Opus only where "spec/code errors cascade downstream" and
    Sonnet everywhere re-gated/rescored anyway.
    """
    if explicit:
        return explicit
    raw_phase = name.upper().replace("-", "_")
    phase = raw_phase[4:] if raw_phase.startswith("BOB_") else raw_phase
    canonical_name = "BOB_{}_MODEL".format(phase)
    legacy_name = "BOB_{}_MODEL".format(raw_phase)
    canonical = os.environ.get(canonical_name)
    legacy = os.environ.get(legacy_name) if legacy_name != canonical_name else None
    if canonical is not None and legacy is not None and canonical != legacy:
        raise AgentError(
            "%s and legacy %s disagree" % (canonical_name, legacy_name)
        )
    selected = canonical if canonical is not None else legacy
    if selected:
        return selected
    return DEFAULT_MODEL


def _transcript_path(name, when):
    """state/transcripts/<utc-ts>-<name>.json. Microseconds in the stamp so
    two calls in the same second never collide (never overwrite)."""
    tdir = os.path.join(_bob_home(), "state", "transcripts")
    os.makedirs(tdir, exist_ok=True)
    ts = when.strftime("%Y%m%dT%H%M%S.%f")
    return os.path.join(tdir, "{}-{}.json".format(ts, name))


def _append_daybook(step):
    """Append one telemetry row to today's steps in state/DAYBOOK.json.

    Under its own tiny flock (state/.daybook.lock) so concurrent panel
    calls can't lose rows, and with the #2 suffix pattern instead of
    overwriting — text2cad's run.json "reported $102.25 for a cycle that
    actually spent $116.67 — every figure the pipeline published about
    itself was 12% low" because repeated phase names clobbered rows.
    """
    home = _bob_home()
    state_dir = os.path.join(home, "state")
    os.makedirs(state_dir, exist_ok=True)
    lock_path = os.path.join(state_dir, ".daybook.lock")
    book_path = os.path.join(state_dir, "DAYBOOK.json")

    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            book = {}
            if os.path.exists(book_path):
                try:
                    with open(book_path) as f:
                        book = json.load(f)
                except (ValueError, OSError):
                    # A corrupt daybook must not block telemetry (the
                    # postmortem principle: accounting "always runs").
                    # Preserve the wreck for forensics instead of erasing.
                    os.replace(book_path, book_path + ".corrupt")
                    book = {}
            today = _utc_now().strftime("%Y-%m-%d")
            day = book.setdefault(
                today, {"ticks": 0, "cost_usd": 0.0, "steps": []}
            )
            # #2 suffixing: count rows already carrying this base name.
            base = step["name"]
            n = sum(
                1
                for s in day["steps"]
                if s.get("name") == base or str(s.get("name", "")).startswith(base + "#")
            )
            if n:
                step = dict(step)
                step["name"] = "{}#{}".format(base, n + 1)
            day["steps"].append(step)
            day["cost_usd"] = round(
                day.get("cost_usd", 0.0) + float(step.get("cost_usd") or 0.0), 6
            )
            _atomic_write(book_path, json.dumps(book, indent=1))
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _log_call(name, model, wall_s, num_turns, cost_usd, subtype):
    """Every call — success, starved, crashed, quota, killed — gets a row.

    Failures are logged BEFORE their exception is raised, so a cycle that
    dies still accounts for where the money went (text2cad postmortem runs
    'including on a cycle that died because the key was exhausted')."""
    _append_daybook(
        {
            "name": name,
            "model": model,
            "wall_s": round(wall_s, 3),
            "num_turns": num_turns,
            "cost_usd": cost_usd,
            "subtype": subtype,
        }
    )


def _mock_result(name, model, started):
    """BOB_MOCK_AGENTS=1: canned reply, zero subprocess, near-zero cost.

    Fixture lookup prefers BOB_HOME/tests/fixtures (a test home may plant
    its own replies) and falls back to the repo's tests/fixtures. Cost is
    a fixed $0.01 so budget math in tests exercises real (non-zero)
    accumulation without ever touching the wallet.
    """
    candidates = [
        os.path.join(_bob_home(), "tests", "fixtures", name + ".txt"),
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "tests",
            "fixtures",
            name + ".txt",
        ),
    ]
    fixture = None
    for c in candidates:
        if os.path.exists(c):
            fixture = c
            break
    if fixture is None:
        raise AgentError(
            "BOB_MOCK_AGENTS=1 but no fixture for agent '{}'. "
            "Create tests/fixtures/{}.txt with the canned reply.".format(name, name)
        )
    with open(fixture) as f:
        text = f.read()
    wall_s = time.monotonic() - started
    tpath = _transcript_path(name, _utc_now())
    _atomic_write(
        tpath,
        json.dumps(
            {
                "mock": True,
                "fixture": fixture,
                "result": text,
                "total_cost_usd": 0.01,
                "num_turns": 1,
                "subtype": "success",
            },
            indent=1,
        ),
    )
    _log_call(name, model, wall_s, 1, 0.01, "success")
    return AgentResult(
        text=text,
        cost_usd=0.01,
        minutes=wall_s / 60.0,
        num_turns=1,
        transcript_path=tpath,
        subtype="success",
    )


def _claude_argv():
    """The CLI to shell. BOB_CLAUDE_BIN (shlex-split) overrides 'claude' so
    tests can point at a stub script — the only sanctioned way to unit-test
    the starved/crashed/quota classification without a real CLI."""
    override = os.environ.get("BOB_CLAUDE_BIN")
    if override:
        return shlex.split(override)
    return ["claude"]


def _kill_process_group(proc):
    """SIGTERM the whole group, wait KILL_GRACE_S, then SIGKILL.

    start_new_session=True put the CLI in its own group, so this reaps its
    children too — the warm-daemon receipt: killing only the parent leaves
    orphaned workers burning tokens with no ledger row.
    """
    try:
        pgid = os.getpgid(proc.pid)
    except (ProcessLookupError, PermissionError):
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return
    deadline = time.monotonic() + KILL_GRACE_S
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(0.05)
    try:
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def _tick_budget_remaining():
    """Minutes left in the open tick budget, or None when no budget ledger
    is open (manual runs, tests) — then the budget is unenforced by design.
    Lazy import so harness.timebudget never becomes an import cycle."""
    from harness import timebudget
    try:
        return timebudget.report()["remaining_minutes"]
    except (timebudget.BudgetExhausted, ValueError, OSError, KeyError):
        return None


def run_agent(name, prompt, *, model=None, max_minutes=15, cwd=None,
              max_turns=40, tools=None):
    """Run one headless claude call; return AgentResult or raise.

    When a tick budget is open (harness.timebudget.open_run), max_minutes
    is capped to the minutes remaining, and a spent budget refuses BEFORE
    the call — the with_budget contract was dead code until this check
    (review 2026-08-22); an unenforced 25-min wall means overlapping ticks.

    Raises:
      Starved        — turn cap hit; raise the cap or cut the task, never
                       retry the same cap.
      QuotaExhausted — usage/rate limit; caller sets DAYBOOK quota_until.
      AgentError     — anything else transient; retryable once. Also raised
                       (before any spend) when the tick budget is spent.
    """
    started = time.monotonic()
    resolved = resolve_model(name, model)

    remaining = _tick_budget_remaining()
    if remaining is not None:
        if remaining <= 0:
            raise AgentError("tick budget spent — resume next tick")
        max_minutes = min(max_minutes, remaining)

    if os.environ.get("BOB_MOCK_AGENTS") == "1":
        return _mock_result(name, resolved, started)

    argv = _claude_argv() + [
        "-p",
        prompt,
        "--model",
        resolved,
        "--max-turns",
        str(max_turns),
        "--output-format",
        "json",
    ]
    if cwd:
        # Tools only when there is a workspace to use them in; pure judge
        # calls stay tool-less (REWARD.md: judges read artifacts only).
        argv += ["--allowedTools", CWD_TOOLS]
    elif tools:
        # A judge may still need a NAMED tool set — the novelty judge's
        # whole evidence rule ("a kill needs a URL you actually opened")
        # was dead on the first live game because headless calls carry no
        # web permission at all (g0001, 2026-08-22: six UNKNOWNs, $1.50,
        # zero URLs opened). Explicit names only, never the cwd toolbox.
        argv += ["--allowedTools", tools]

    proc = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        start_new_session=True,  # own process group => killable as a unit
        text=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=max_minutes * 60.0)
    except subprocess.TimeoutExpired:
        _kill_process_group(proc)
        try:
            stdout, stderr = proc.communicate(timeout=KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            stdout, stderr = "", ""
        wall_s = time.monotonic() - started
        tpath = _transcript_path(name, _utc_now())
        _atomic_write(
            tpath,
            json.dumps(
                {
                    "killed": "overrun",
                    "max_minutes": max_minutes,
                    "stdout": stdout,
                    "stderr": stderr,
                },
                indent=1,
            ),
        )
        _log_call(name, resolved, wall_s, None, 0.0, "killed_overrun")
        raise AgentError(
            "Agent '{}' overran its {}-minute wall ceiling and was killed "
            "(SIGTERM then SIGKILL after {}s grace). Retry once with a "
            "smaller task or a bigger ceiling — a ceiling that binds is the "
            "real constraint, not a safety limit.".format(
                name, max_minutes, KILL_GRACE_S
            )
        )

    wall_s = time.monotonic() - started
    tpath = _transcript_path(name, _utc_now())
    # Full stdout is the transcript, verbatim — the CLI's JSON is the source
    # of truth for cost (text2cad §d1: the CLI's own numbers, crash-safe).
    _atomic_write(tpath, stdout if stdout else json.dumps({"stderr": stderr}))

    try:
        payload = json.loads(stdout)
    except ValueError:
        blob = (stdout or "") + "\n" + (stderr or "")
        if QUOTA_RE.search(blob):
            _log_call(name, resolved, wall_s, None, 0.0, "quota")
            raise QuotaExhausted(
                "Agent '{}' hit the usage/rate limit (unparseable CLI "
                "output). Set DAYBOOK quota_until = now + 60 min and no-op "
                "ticks until then; never retry into the wall.".format(name)
            )
        _log_call(name, resolved, wall_s, None, 0.0, "crashed_no_json")
        raise AgentError(
            "Agent '{}' produced no parseable JSON (exit {}). Retry once; "
            "stderr tail: {!r}".format(name, proc.returncode, (stderr or "")[-500:])
        )

    cost = float(payload.get("total_cost_usd") or 0.0)
    num_turns = payload.get("num_turns")
    subtype = payload.get("subtype") or (
        "success" if proc.returncode == 0 else "error_during_execution"
    )
    text = payload.get("result") or ""

    if subtype == "error_max_turns":
        # Starved, not crashed: "$49 went to phases that were starved
        # rather than wrong" and every same-cap retry bought the same wall.
        _log_call(name, resolved, wall_s, num_turns, cost, subtype)
        raise Starved(
            "Agent '{}' ran out of turns ({} used, cap {}). Raise the cap "
            "or cut the task down — NEVER retry at the same cap.".format(
                name, num_turns, max_turns
            )
        )

    is_error = bool(payload.get("is_error")) or subtype.startswith("error")
    if is_error:
        blob = text + "\n" + (stderr or "")
        if QUOTA_RE.search(blob):
            _log_call(name, resolved, wall_s, num_turns, cost, "quota")
            raise QuotaExhausted(
                "Agent '{}' hit the usage/rate limit. Set DAYBOOK "
                "quota_until = now + 60 min; the tick loop must no-op "
                "until then. Never retry into a wall.".format(name)
            )
        _log_call(name, resolved, wall_s, num_turns, cost, subtype)
        raise AgentError(
            "Agent '{}' crashed (subtype={}). Transient — retry once; if "
            "it recurs, park the game and file the transcript: {}".format(
                name, subtype, tpath
            )
        )

    _log_call(name, resolved, wall_s, num_turns, cost, subtype)
    return AgentResult(
        text=text,
        cost_usd=cost,
        minutes=wall_s / 60.0,
        num_turns=num_turns,
        transcript_path=tpath,
        subtype=subtype,
    )
