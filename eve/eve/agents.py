"""claude-CLI runner: every LLM call in Eve goes through run_agent().

Port of Bob's harness (bob/harness/agents.py) with Eve's env knobs. The
lessons it encodes are the org's own receipts:

- Cost telemetry from the CLI's own JSON, persisted crash-safe after EVERY
  call, never overwritten (repeated phase names get a #2 suffix so rows are
  never clobbered — text2cad's run.json under-reported a cycle by 12%).
- Starved vs crashed, mechanically distinguished: starved raises Starved,
  callers must raise the cap or cut the task, NEVER retry at the same cap.
- Quota death is a first-class exception (QuotaExhausted), never a retry:
  once the window is spent, "retrying" just burns wall-clock.
- Process-group kill on overrun (start_new_session + SIGTERM, 5s grace,
  SIGKILL) so a killed phase can't leave orphaned children burning tokens.
- EVE_MOCK_AGENTS=1 short-circuits the subprocess and reads the reply from
  tests/fixtures/<name>.txt — required for tests and dry runs, so no test
  can ever hit the real CLI or the real wallet.

Stdlib only, Python 3.9. No env reads at import time (each test builds its
own EVE_HOME and flips env per case).
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


class AgentError(Exception):
    """Transient crash (CLI died, bad JSON, error_during_execution).

    Retryable ONCE by the caller — a lens crash graduates to exactly one
    retry, never an unbounded repair spiral.
    """


class Starved(AgentError):
    """The agent hit its turn cap (subtype == 'error_max_turns').

    NOT retryable at the same cap: a cap that binds 3 times out of 3 is the
    real constraint on the work, not a safety limit (text2cad: every scram
    repair ended at 71/70 turns). Raise the cap or cut the task down.
    """


class QuotaExhausted(Exception):
    """The subscription window is exhausted (usage/rate limit).

    Callers set the DAYBOOK quota_until (now + 60 min) and the tick loop
    no-ops until then. Never retry into a wall.

    Deliberately NOT a subclass of AgentError so a generic "retry once on
    AgentError" handler can never swallow a quota death.
    """


AgentResult = namedtuple(
    "AgentResult",
    ["text", "cost_usd", "minutes", "num_turns", "transcript_path", "subtype"],
)

QUOTA_RE = re.compile(r"usage limit|limit reached|rate limit", re.IGNORECASE)

KILL_GRACE_S = 5.0

DEFAULT_MODEL = "claude-sonnet-5"

# Tools granted only when the agent is given a working directory: a cwd means
# "go do repo work"; a prompt-only call gets no tools (judge/generator
# isolation — a lens that can edit its own score is a lens that cheats).
CWD_TOOLS = "Bash,Read,Write,Edit,Glob,Grep"


def _eve_home():
    """Repo root (cfg.root). EVE_HOME overrides (tests point it at a temp dir).

    Read at call time, never import time.
    """
    env = os.environ.get("EVE_HOME")
    if env:
        return os.path.abspath(env)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _utc_now():
    return datetime.now(timezone.utc)


def _atomic_write(path, data):
    """tmp + os.replace: a crash mid-write must never leave a half-JSON file
    (that is how ledgers silently rot)."""
    tmp = "{}.tmp.{}".format(path, os.getpid())
    with open(tmp, "w") as f:
        f.write(data)
    os.replace(tmp, path)


def resolve_model(name, explicit=None):
    """Explicit arg > EVE_<PHASE>_MODEL > default. PHASE is the agent name
    uppercased with dashes -> underscores, so 'build-lens' maps 1:1 to
    EVE_BUILD_LENS_MODEL. Per-phase routing is the cost model: run the big
    model only where a bad spec cascades downstream."""
    if explicit:
        return explicit
    phase = name.upper().replace("-", "_")
    env = os.environ.get("EVE_{}_MODEL".format(phase))
    if env:
        return env
    return DEFAULT_MODEL


def _transcript_path(name, when):
    """state/transcripts/<utc-ts>-<name>.json. Microseconds in the stamp so
    two calls in the same second never collide (never overwrite)."""
    tdir = os.path.join(_eve_home(), "state", "transcripts")
    os.makedirs(tdir, exist_ok=True)
    ts = when.strftime("%Y%m%dT%H%M%S.%f")
    return os.path.join(tdir, "{}-{}.json".format(ts, name))


def _append_daybook(step):
    """Append one telemetry row to today's steps in state/DAYBOOK.json.

    Under its own tiny flock (state/.daybook.lock) so concurrent calls can't
    lose rows; #2 suffixing instead of overwriting keeps every call's cost
    (text2cad's run.json reported $102.25 for a cycle that actually spent
    $116.67 because repeated phase names clobbered earlier rows).
    """
    home = _eve_home()
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
                    # A corrupt daybook must not block telemetry; preserve the
                    # wreck for forensics instead of erasing.
                    os.replace(book_path, book_path + ".corrupt")
                    book = {}
            today = _utc_now().strftime("%Y-%m-%d")
            day = book.setdefault(
                today, {"ticks": 0, "cost_usd": 0.0, "steps": []}
            )
            base = step["name"]
            n = sum(
                1
                for s in day["steps"]
                if s.get("name") == base
                or str(s.get("name", "")).startswith(base + "#")
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
    """Every call — success, starved, crashed, quota, killed — gets a row,
    logged BEFORE its exception is raised so a dead cycle still accounts for
    where the money went."""
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
    """EVE_MOCK_AGENTS=1: canned reply, zero subprocess, near-zero cost.

    Fixture lookup prefers EVE_HOME/tests/fixtures and falls back to the
    repo's tests/fixtures. Cost is a fixed $0.01 so budget math is exercised
    with real (non-zero) accumulation without ever touching the wallet.
    """
    candidates = [
        os.path.join(_eve_home(), "tests", "fixtures", name + ".txt"),
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
            "EVE_MOCK_AGENTS=1 but no fixture for agent '{}'. "
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
    """The CLI to shell. EVE_CLAUDE_BIN (shlex-split) overrides 'claude' so
    tests can point at a stub script — the only sanctioned way to unit-test
    the starved/crashed/quota classification without a real CLI."""
    override = os.environ.get("EVE_CLAUDE_BIN")
    if override:
        return shlex.split(override)
    return ["claude"]


def _kill_process_group(proc):
    """SIGTERM the whole group, wait KILL_GRACE_S, then SIGKILL. Killing only
    the parent leaves orphaned workers burning tokens with no ledger row."""
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


def run_agent(name, prompt, *, model=None, max_minutes=15, cwd=None, max_turns=40):
    """Run one Claude agent for `name`, return an AgentResult.

    Failure classification (differing correct responses):
      Starved      — never retry at the same cap; raise or cut.
      QuotaExhausted — a state, not an error; caller sets DAYBOOK quota_until.
      AgentError   — anything else transient; retryable once.
    """
    started = time.monotonic()
    resolved = resolve_model(name, model)

    if os.environ.get("EVE_MOCK_AGENTS") == "1":
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
        argv += ["--allowedTools", CWD_TOOLS]

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
            "smaller task or a bigger ceiling.".format(name, max_minutes, KILL_GRACE_S)
        )

    wall_s = time.monotonic() - started
    tpath = _transcript_path(name, _utc_now())
    _atomic_write(tpath, stdout if stdout else json.dumps({"stderr": stderr}))

    try:
        payload = json.loads(stdout)
    except ValueError:
        blob = (stdout or "") + "\n" + (stderr or "")
        if QUOTA_RE.search(blob):
            _log_call(name, resolved, wall_s, None, 0.0, "quota")
            raise QuotaExhausted(
                "Agent '{}' hit the usage/rate limit (unparseable CLI "
                "output). Set DAYBOOK quota_until = now + 60 min; never "
                "retry into the wall.".format(name)
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
                "quota_until = now + 60 min; never retry into a wall.".format(name)
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
