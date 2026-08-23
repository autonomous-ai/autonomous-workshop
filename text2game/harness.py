"""Headless `claude -p` phase runner.

Ported from text2cad, minus the CAD-specific env. The accounting comments there
were paid for in real incidents, so the fields they justify are kept verbatim:
`subtype` (the CLI verdict on HOW a phase ended), the cache read/write split
(one agent in a fan-out writes the prefix and the rest ride free — without this
a healthy judge looks broken), and the history-preserving run.json write (a
re-run used to silently delete the cost of the attempt it replaced).
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import trace_log

HERE = Path(__file__).resolve().parent
_LOG_LOCK = threading.Lock()

HEADLESS = (
    "IMPORTANT - this is a one-shot, unattended, headless session. No future "
    "turn will wake you: never end your turn assuming something checks back. "
    "Write every file you were asked for before you finish. If you cannot "
    "finish the whole task, write what you have and say plainly what is "
    "missing - a partial file on disk beats a perfect plan in your reply."
)


def telegram(text: str) -> None:
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_DM", "").strip()
    if tok and chat:
        subprocess.run(["curl", "-s", f"https://api.telegram.org/bot{tok}/sendMessage",
                        "-d", f"chat_id={chat}", "--data-urlencode", f"text={text}"],
                       capture_output=True, timeout=30)


def confirm(subject: str, detail: str, reply_with: str = "") -> None:
    """Alert a human that the pipeline needs a DECISION, not just a status.

    The loop runs unattended, so the handful of calls only a human can make
    have to leave the box and say what to answer. Everything in this pipeline
    already telegrams status; this marks the subset that is BLOCKING, so a
    decision request cannot be lost in a scroll of progress lines.
    """
    msg = f"CAN QUYET DINH / DECISION NEEDED - text2game: {subject}\n\n{detail}"
    if reply_with:
        msg += f"\n\nTra loi / reply: {reply_with}"
    print("\n" + msg + "\n", flush=True)
    telegram(msg[:3900])


# --- where the sibling toolchain lives -------------------------------------
# text2game leans on the text2cad checkout for gate.py, the cadcode skill, the
# CAD venv, concept_image.py, gen_howto_video.py, md2html.py and the publish
# uploaders. Every script asks these two helpers instead of spelling a path,
# so one TEXT2CAD_DIR / TEXT2CAD_PY in .env moves the whole pipeline.
def text2cad_dir() -> Path:
    return Path(os.environ.get("TEXT2CAD_DIR", "/root/text2cad")).expanduser()


def text2cad_py() -> str:
    """The CAD venv interpreter (cadquery, trimesh, numpy, matplotlib)."""
    return os.environ.get("TEXT2CAD_PY", "").strip() or \
        str(text2cad_dir() / ".venv" / "bin" / "python")


def load_env() -> None:
    f = HERE / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            # Strip a TRAILING comment, but only when the # is preceded by
            # whitespace: .env.example has always shipped `BED_X=256  # printer
            # bed`, and without this the value is the whole string and
            # float(BED_X) dies. Requiring the space keeps a `#` that is part of
            # a real value (a token, a hex colour) intact.
            v = re.split(r"\s#", v, 1)[0]
            os.environ.setdefault(k.strip(), v.strip().strip(chr(34)).strip(chr(39)))


# One line, one write. run_phase runs inside a ThreadPoolExecutor - three
# propose lanes, then three judges - and print() is TWO writes, the message and
# then the newline, so a sibling thread lands between them. Measured 2026-08-20
# on the first opus panel:
#
#   [propose-legacy] provider=claude ... ...[propose-family] provider=claude ...
#
# both banners on one line, and one of them would have been invisible to a
# `^\[propose-` match. This log is not decoration: watchdog.py reads it to tell
# a stalled run from a dead one, and for a parallel phase it is the only record
# of what happened that exists.
_LOG_LOCK = threading.Lock()


def log(msg: str) -> None:
    """print(), serialised so two concurrent phases cannot share a line."""
    with _LOG_LOCK:
        print(msg, flush=True)


def job_of(label: str) -> str:
    """Run LABEL -> JOB name. referee-r2-retry -> referee, build-g3 -> build.

    The round/group suffix is a per-invocation label, not a configurable thing:
    REFEREE-R2_MODEL is not a settable env name. Every job name in this
    pipeline is hyphen-free (art_direction, video_spec use underscores), so the
    first hyphen is an unambiguous cut.
    """
    return label.split("-", 1)[0]


def model_for(phase: str) -> str:
    """Phase name -> model, resolved by JOB so a run label cannot silently miss.

    2026-08-19: phase 2 and 3 were found entirely on sonnet because
    model_for("build-g3") looked up BUILD-G3_MODEL; those two call sites were
    fixed by passing model_for("build") by hand, but the phase 1 round labels
    were not - run.json for keep-the-light-relay shows revise-r1 and revise-r2
    on claude-sonnet-5 while .env asked for claude-opus-5 both times. Normalise
    here instead, so the fix cannot be forgotten at a new call site.
    """
    return os.environ.get(f"{job_of(phase).upper()}_MODEL", "claude-sonnet-5")


# ------------------------------------------------------------------ providers
#
# A phase runs on `claude -p` or on `codex exec`. The choice is per JOB and
# comes from CODEX_JOBS (driver flag --codex), so nothing above run_phase
# learns that a second provider exists: same call signature, same run.json
# entry shape, same return value.

CODEX_BIN = os.environ.get("CODEX_BIN", "codex")
CODEX_MODEL_DEFAULT = "gpt-5.6-sol"

# Jobs that cannot run on codex at all. Empty since 2026-08-19: build and
# repair used to sit here because their prompt said "Use the cadcode skill" and
# codex has no skills - but the gap was the INSTRUCTIONS, not the capability.
# prompts.skill() now hands codex the handbook by path and the same shell
# scripts the gate runs, so nothing is claude-only. Kept as the hook for the
# next thing that genuinely is.
SKILL_BOUND = set()

PHASE1_JOBS = ("mechanism", "gdd", "manifest", "todo",
               "referee", "critic", "evaluate", "revise", "priorart")

# Everything downstream of the human checkpoint: geometry, the visual gate and
# the print-kit writing.
PHASE23_JOBS = ("art_direction", "build", "repair", "coherence",
                "rulebook", "video_spec")


ALIASES = {"phase1": PHASE1_JOBS, "phase23": PHASE23_JOBS}


def codex_jobs() -> set:
    """The CODEX_JOBS set, expanded. Aliases: phase1, phase23, all, none."""
    raw = {j.strip().lower() for j in os.environ.get("CODEX_JOBS", "").split(",")
           if j.strip()}
    if not raw or "none" in raw:
        return set()
    for name, jobs in ALIASES.items():
        if name in raw:
            raw.discard(name)
            raw |= set(jobs)
    return raw


def codex_ready() -> str:
    """Empty if a codex phase can run, else the reason it cannot.

    Worth a preflight: routing is decided per job, so a missing binary or a
    logged-out account would not surface until the first codex phase - which
    on this pipeline can be an hour into a run.
    """
    if not shutil.which(CODEX_BIN):
        return f"{CODEX_BIN} is not on PATH"
    if not (Path.home() / ".codex" / "auth.json").exists():
        return "~/.codex/auth.json is missing - run `codex login`"
    return ""


def provider_for(job: str) -> str:
    jobs = codex_jobs()
    if not jobs:
        return "claude"
    if job in SKILL_BOUND:
        # `all` never sweeps these up; naming one is the operator's call.
        if job in jobs:
            print(f"[warn] job '{job}' routed to codex, but its prompt uses the "
                  f"cadcode Claude skill - expect it to build nothing", flush=True)
            return "codex"
        return "claude"
    return "codex" if ("all" in jobs or job in jobs) else "claude"


def plan(job: str) -> str:
    """job=provider:model, for the header a phase prints before it starts.

    It used to print model_for() unconditionally, which named a claude model
    while codex did the work - the log lied about the run it was logging.
    """
    prov = provider_for(job)
    model = (os.environ.get("CODEX_MODEL", "").strip() or CODEX_MODEL_DEFAULT) \
        if prov == "codex" else model_for(job)
    return f"{job}={prov}:{model}"


def phase_env() -> dict:
    env = dict(os.environ)
    env["PATH"] = (f"{Path.home()}/.local/bin:/root/.local/bin:"
                   + env.get("PATH", ""))
    # text2cad 2026-08-17: four BUILD attempts died on "response exceeded the
    # 64000 output token maximum" having written nothing. Phase 1 is all prose
    # and JSON, but a 16-part manifest is a long single write - same ceiling.
    env.setdefault("CLAUDE_CODE_MAX_OUTPUT_TOKENS", "128000")
    return env


BLANK = {"result": "", "error": "", "num_turns": None, "subtype": None,
         "cost_usd": None, "cache_write": None, "cache_read": None,
         "out_tokens": None, "is_error": False}


def _claude_cmd(prompt: str, model: str, out_dir: Path, max_turns: int) -> list:
    allowed = ("Bash,Read,Write,Edit,Glob,Grep,TodoWrite,WebSearch,WebFetch,"
               "mcp__second-brain__memory_search,mcp__second-brain__memory_get")
    return ["claude", "-p", prompt, "--model", model,
            "--allowedTools", allowed,
            "--add-dir", str(out_dir), "--add-dir", str(HERE),
            "--max-turns", str(max_turns), "--output-format", "json"]


def _parse_claude(r) -> dict:
    try:
        data = json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        data = {"result": r.stdout[-2000:], "error": r.stderr[-2000:]}
    usage = data.get("usage") or {}
    return dict(BLANK, result=(data.get("result") or "").strip(),
                error=str(data.get("error") or ""),
                num_turns=data.get("num_turns"), subtype=data.get("subtype"),
                cost_usd=data.get("total_cost_usd"),
                cache_write=usage.get("cache_creation_input_tokens"),
                cache_read=usage.get("cache_read_input_tokens"),
                out_tokens=usage.get("output_tokens"),
                is_error=data.get("is_error", r.returncode != 0))


def _codex_cmd(prompt: str, model: str, out_dir: Path, last: Path) -> list:
    # No --max-turns equivalent exists: for a codex phase the TIMEOUT is the
    # only bound, which is why the entry below keeps num_turns None rather than
    # inventing one (postmortem reads num_turns vs max_turns to tell a starved
    # phase from a crashed one, and a fake number there would lie).
    return [CODEX_BIN, "exec", prompt, "--model", model,
            "-C", str(out_dir), "--add-dir", str(HERE),
            "--skip-git-repo-check",
            "--sandbox", os.environ.get("CODEX_SANDBOX", "danger-full-access"),
            # Off by default in codex; priorart and the discover judges are
            # nothing without it.
            "-c", "tools.web_search=true",
            # gpt-5.6-sol ships with reasoning effort "none".
            "-c", f"model_reasoning_effort={os.environ.get('CODEX_EFFORT', 'high')}",
            "--json", "-o", str(last)]


def _parse_codex(r, last: Path) -> dict:
    """codex --json is an event STREAM, not one JSON object like claude's."""
    usage, subtype, items, errs, msgs = {}, None, 0, [], []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "item.completed":
            items += 1
            item = ev.get("item") or {}
            if item.get("type") == "agent_message" and item.get("text"):
                msgs.append(item["text"])
        elif t == "turn.completed":
            usage, subtype = ev.get("usage") or {}, subtype or "success"
        elif t in ("turn.failed", "error"):
            subtype = "error_during_execution"
            errs.append(json.dumps(ev.get("error") or ev)[:800])
    result = ""
    if last.exists():
        result = last.read_text(encoding="utf-8", errors="replace").strip()
    if not result and msgs:  # -o is the contract, the stream is the safety net
        result = msgs[-1].strip()
    return dict(BLANK, result=result, items=items,
                error="\n".join(errs + [r.stderr[-2000:]]).strip(),
                num_turns=None, subtype=subtype or "unknown",
                # This account is a ChatGPT Pro subscription: a codex phase has
                # no marginal price. text2cad's self-host lane learned to record
                # the real 0 rather than a CLI's Anthropic-priced fiction.
                cost_usd=0.0,
                cache_read=usage.get("cached_input_tokens"),
                cache_write=usage.get("cache_write_input_tokens"),
                out_tokens=usage.get("output_tokens"),
                is_error=(r.returncode != 0 or subtype == "error_during_execution"))


def run_phase(name: str, prompt: str, out_dir: Path, max_turns: int, run_log: dict,
              timeout_s: int = 3600, model: str = "") -> str:
    job = job_of(name)
    provider = provider_for(job)
    if provider == "codex":
        # A claude model string means nothing to codex, so an explicit model=
        # from a caller (phase2 build, discover judges) is deliberately dropped.
        model = os.environ.get("CODEX_MODEL", "").strip() or CODEX_MODEL_DEFAULT
    else:
        model = model or model_for(job)
    def attempt(prov: str, mdl: str) -> tuple:
        tmp = None
        try:
            if prov == "codex":
                tmp = tempfile.TemporaryDirectory(prefix="codex-phase-")
                last = Path(tmp.name) / "last.txt"
                cmd = _codex_cmd(prompt, mdl, out_dir, last)
            else:
                cmd = _claude_cmd(prompt, mdl, out_dir, max_turns)
            try:
                # stdin=DEVNULL: without it codex prints "Reading additional
                # input from stdin" and waits, which in a subprocess is a hang
                # that only ends at the phase timeout.
                r = subprocess.run(cmd, capture_output=True, text=True, cwd=out_dir,
                                   env=phase_env(), timeout=timeout_s,
                                   stdin=subprocess.DEVNULL)
                return (_parse_codex(r, last) if prov == "codex"
                        else _parse_claude(r)), time.time()
            except subprocess.TimeoutExpired:
                return dict(BLANK, error=f"phase timed out after {timeout_s}s",
                            subtype="timeout", is_error=True), time.time()
            except OSError as e:      # binary missing, fork failure
                return dict(BLANK, error=f"could not run {prov}: {e}",
                            subtype="spawn_failed", is_error=True), time.time()
        finally:
            if tmp:
                tmp.cleanup()

    log(f"[{name}] provider={provider} model={model} max_turns={max_turns} "
        f"timeout={timeout_s}s ...")
    t0 = time.time()
    got, t1 = attempt(provider, model)

    # Provider fallback. A codex phase that fails must not cost the run: the
    # same prompt goes to claude once, and BOTH attempts stay in the ledger so
    # a silent fallback cannot be mistaken for a clean codex run. Only one
    # retry - if both providers fail, the failure is the phase, not the lane.
    if (provider == "codex" and got["is_error"]
            and os.environ.get("CODEX_FALLBACK", "1") != "0"):
        with _LOG_LOCK:
            run_log[f"{name}#codex-failed"] = {
                "provider": "codex", "model": model,
                "wall_s": round(t1 - t0, 1), "subtype": got["subtype"],
                "is_error": True, "error": got["error"][:300]}
        log(f"[{name}] codex failed ({got['subtype']}) - falling back to claude")
        telegram(f"text2game [{name}]: codex failed ({got['subtype']}), "
                 f"retrying on claude")
        provider, model = "claude", model_for(job)
        got, _ = attempt(provider, model)

    entry = {"provider": provider, "model": model,
             "wall_s": round(time.time() - t0, 1),
             "num_turns": got["num_turns"], "max_turns": max_turns,
             "subtype": got["subtype"], "cost_usd": got["cost_usd"],
             "cache_write": got["cache_write"], "cache_read": got["cache_read"],
             "out_tokens": got["out_tokens"], "is_error": got["is_error"]}
    if provider == "codex":
        # No turn cap exists, so max_turns above is the caller's intent
        # only. This is the one number that shows a runaway session.
        entry["codex_items"] = got.get("items")
    with _LOG_LOCK:
        prev = run_log.get(name)
        if isinstance(prev, dict) and "wall_s" in prev:
            n = 2
            while f"{name}#{n}" in run_log:
                n += 1
            run_log[f"{name}#{n}"] = prev
        run_log[name] = entry
        (out_dir / "run.json").write_text(json.dumps(run_log, indent=2), encoding="utf-8")
    if entry["is_error"] and f"{name}#codex-failed" in run_log:
        confirm(f"[{name}] failed on BOTH providers",
                f"codex: {run_log[f'{name}#codex-failed'].get('subtype')}\n"
                f"claude: {entry.get('subtype')} after {entry['wall_s']}s\n"
                f"There is no third lane to try.",
                "retry this phase, skip it, or stop the run")
    result = got["result"]
    # The prompt a phase was actually GIVEN, beside what it returned. run.json
    # records what a phase cost; without this pair you cannot re-read the
    # instruction later without reconstructing it from source that has moved on.
    try:
        trace_log.write(out_dir, trace_log.next_seq(out_dir), name, prompt,
                        result, entry)
    except OSError as e:
        log(f"[{name}] trace not written: {e}")
    tail = result.splitlines()[-1][:120] if result else "(no output)"
    log(f"[{name}] {entry['wall_s']}s, turns={entry['num_turns']}, "
        f"${entry['cost_usd']}: {tail}")
    # text2cad 2026-08-13: the weekly cap hit mid-cycle and every subsequent
    # phase burned wall-clock producing nothing, SILENTLY. Alarm and abort.
    if entry["is_error"]:
        blob = (result + " " + got["error"])[:2000]
        if re.search(r"usage limit|limit reached|rate limit|rate_limit|quota exceeded",
                     blob, re.I):
            msg = (f"text2game: {provider} quota exhausted during [{name}] - "
                   f"aborting. {blob[:200]}")
            confirm("quota exhausted",
                    f"[{name}] died on {provider} quota" +
                    (" AND the codex fallback was already spent"
                     if f"{name}#codex-failed" in run_log else "") +
                    f"\n{blob[:300]}",
                    "top up, or say which provider to switch to")
            log(msg)
            telegram(msg)
            raise SystemExit(4)
    return result


def postmortem(out_dir: Path) -> str:
    """A run.json is a ledger; this is the sentence you read at 2am.

    text2cad grew write_postmortem after a cycle died and left only per-phase
    rows: the question "which phase actually killed it, and was it starved or
    crashed" needed max_turns and subtype read together, every time, by hand.
    """
    f = out_dir / "run.json"
    if not f.exists():
        return "no run.json"
    log = json.loads(f.read_text(encoding="utf-8"))
    rows, cost = [], 0.0
    for name, e in log.items():
        if not isinstance(e, dict) or "wall_s" not in e:
            continue
        cost += e.get("cost_usd") or 0.0
        if e.get("is_error"):
            # num_turns at the cap is a BUDGET failure and needs a bigger cap;
            # below it is a real crash and needs a retry. They look identical
            # without both numbers.
            starved = (e.get("provider", "claude") == "claude"
                       and (e.get("num_turns") or 0) >= (e.get("max_turns") or 0))
            rows.append(f"{name}: {'STARVED' if starved else 'CRASHED'} "
                        f"on {e.get('provider', 'claude')} "
                        f"({e.get('num_turns')}/{e.get('max_turns')} turns, "
                        f"{e.get('subtype')}, {e.get('wall_s')}s)")
    head = f"{len(log)} phases, ${cost:.2f}"
    return head + ("\n" + "\n".join(rows) if rows else "\nno failed phase")
