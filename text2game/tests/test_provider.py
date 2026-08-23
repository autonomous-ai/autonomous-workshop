#!/usr/bin/env python3
"""Provider routing and the codex event-stream parser.

    python3 tests/test_provider.py

No network, no CLI: the codex fixture below is a real `codex exec --json`
stream captured on this box (v0.148.0), trimmed. The point of these cases is
that a run LABEL must resolve like its JOB - the bug that put every phase 2
and 3 job on sonnet, and revise-r1/r2 on sonnet while .env asked for opus.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402


class Ran:
    """Stands in for a CompletedProcess."""

    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout, self.stderr, self.returncode = stdout, stderr, returncode


CODEX_OK = "\n".join([
    '{"type":"thread.started","thread_id":"01a01976-b4fc-7a50-9cd6-337cb8924a0c"}',
    '{"type":"turn.started"}',
    '{"type":"item.completed","item":{"id":"item_0","type":"agent_message",'
    '"text":"working on it"}}',
    '{"type":"item.completed","item":{"id":"item_1","type":"file_change",'
    '"changes":[{"path":"referee.md","kind":"add"}],"status":"completed"}}',
    '{"type":"item.completed","item":{"id":"item_2","type":"agent_message",'
    '"text":"FINDINGS"}}',
    '{"type":"turn.completed","usage":{"input_tokens":45345,'
    '"cached_input_tokens":36096,"cache_write_input_tokens":0,'
    '"output_tokens":242,"reasoning_output_tokens":131}}',
])

CODEX_FAIL = "\n".join([
    '{"type":"thread.started","thread_id":"x"}',
    '{"type":"turn.started"}',
    '{"type":"turn.failed","error":{"message":"You have hit your usage limit."}}',
])


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label}: {got!r}" +
          ("" if ok else f" (want {want!r})"))
    return ok


def env(**kw):
    for k in ("CODEX_JOBS", "CODEX_MODEL", "REVISE_MODEL", "BUILD_MODEL"):
        os.environ.pop(k, None)
    os.environ.update({k: v for k, v in kw.items() if v is not None})


def main() -> int:
    r = []

    print("job_of - a run label resolves like its job")
    for label, job in (("referee-r2", "referee"), ("referee-r1-retry", "referee"),
                       ("build-g3", "build"), ("repair-g2-1", "repair"),
                       ("judge-1", "judge"), ("propose-market-r2", "propose"),
                       ("art_direction", "art_direction"),
                       ("video_spec", "video_spec"), ("gdd", "gdd")):
        r.append(check(label, harness.job_of(label), job))

    print("\nmodel_for - the round label must not fall through to the default")
    env(REVISE_MODEL="claude-opus-5", BUILD_MODEL="claude-sonnet-5")
    r.append(check("revise-r1", harness.model_for("revise-r1"), "claude-opus-5"))
    r.append(check("build-g3", harness.model_for("build-g3"), "claude-sonnet-5"))
    r.append(check("unset job falls back", harness.model_for("critic-r9"),
                   "claude-sonnet-5"))

    print("\nprovider_for - CODEX_JOBS")
    env()
    r.append(check("unset -> claude", harness.provider_for("referee"), "claude"))
    env(CODEX_JOBS="none")
    r.append(check("'none' -> claude", harness.provider_for("referee"), "claude"))
    env(CODEX_JOBS="referee,critic")
    r.append(check("named job", harness.provider_for("referee"), "codex"))
    r.append(check("unnamed job", harness.provider_for("gdd"), "claude"))
    env(CODEX_JOBS="phase1")
    r.append(check("alias phase1 covers revise", harness.provider_for("revise"), "codex"))
    r.append(check("alias phase1 leaves build", harness.provider_for("build"), "claude"))
    env(CODEX_JOBS="phase23")
    r.append(check("alias phase23 covers build", harness.provider_for("build"), "codex"))
    r.append(check("alias phase23 covers rulebook", harness.provider_for("rulebook"), "codex"))
    r.append(check("alias phase23 leaves gdd", harness.provider_for("gdd"), "claude"))
    r.append(check("alias phase23 leaves judge", harness.provider_for("judge"), "claude"))
    env(CODEX_JOBS="phase1,phase23")
    r.append(check("aliases compose", harness.provider_for("gdd"), "codex"))
    r.append(check("aliases compose", harness.provider_for("coherence"), "codex"))
    env(CODEX_JOBS="all")
    r.append(check("'all' covers coherence", harness.provider_for("coherence"), "codex"))
    r.append(check("'all' covers build", harness.provider_for("build"), "codex"))
    r.append(check("'all' covers repair", harness.provider_for("repair"), "codex"))

    print("\nprompts.skill - codex is handed the handbook, claude is told its name")
    import prompts  # noqa: E402
    env(CODEX_JOBS="none")
    r.append(check("claude gets the skill NAME",
                   prompts.skill("build"), "Use the cadcode skill."))
    env(CODEX_JOBS="all")
    block = prompts.skill("build")
    r.append(check("codex gets SKILL.md by path", "SKILL.md" in block, True))
    r.append(check("codex gets the same scripts the gate runs",
                   "scripts/measure" in block and "--with cadquery" in block, True))

    print("\n_parse_codex - the event stream, not one JSON object")
    tmp = Path(os.environ.get("TMPDIR", "/tmp")) / "test_provider_last.txt"
    tmp.write_text("FINDINGS\n3 unresolvable states\n", encoding="utf-8")
    got = harness._parse_codex(Ran(CODEX_OK), tmp)
    r.append(check("result comes from -o", got["result"].splitlines()[0], "FINDINGS"))
    r.append(check("subtype", got["subtype"], "success"))
    r.append(check("no turn count exists", got["num_turns"], None))
    r.append(check("items counted", got["items"], 3))
    r.append(check("cache_read <- cached_input_tokens", got["cache_read"], 36096))
    r.append(check("out_tokens", got["out_tokens"], 242))
    r.append(check("subscription, no marginal cost", got["cost_usd"], 0.0))
    r.append(check("clean run is not an error", got["is_error"], False))

    tmp.unlink()
    got = harness._parse_codex(Ran(CODEX_OK), tmp)
    r.append(check("falls back to last agent_message", got["result"], "FINDINGS"))

    got = harness._parse_codex(Ran(CODEX_FAIL, returncode=1), tmp)
    r.append(check("turn.failed is an error", got["is_error"], True))
    r.append(check("failure subtype", got["subtype"], "error_during_execution"))
    # This blob is what the quota regex in run_phase reads.
    r.append(check("quota text survives into error",
                   "usage limit" in got["error"], True))

    print("\n_codex_cmd - the flags that were verified on this box")
    cmd = harness._codex_cmd("hi", "gpt-5.6-sol", Path("/tmp/out"), Path("/tmp/l"))
    r.append(check("web_search on", "tools.web_search=true" in cmd, True))
    r.append(check("no --max-turns is passed", "--max-turns" in cmd, False))
    r.append(check("last message captured", "-o" in cmd, True))
    r.append(check("effort raised off 'none'",
                   any(c.startswith("model_reasoning_effort=") for c in cmd), True))

    print("\nconfirm - the decisions that must reach a human")
    r.append(check("harness.confirm exists", callable(getattr(harness, "confirm", None)), True))
    sent, tele = [], harness.telegram
    harness.telegram = lambda m: sent.append(m)
    try:
        harness.confirm("phase 2 stopped", "two repairs did not clear it", "loosen or drop")
    finally:
        harness.telegram = tele
    r.append(check("it is marked as blocking, not status",
                   "DECISION NEEDED" in sent[0], True))
    r.append(check("it says what to reply", "loosen or drop" in sent[0], True))
    # Every module that calls it must import it, or the call is a NameError
    # reached only at the moment something has already gone wrong. That is
    # exactly how it shipped broken once: the function was written, then a
    # later write of a stale buffer dropped it and left the call sites.
    import re as _re
    for mod in ("harness.py", "text2game", "phase2.py", "phase3.py"):
        src = (HERE / mod).read_text(encoding="utf-8")
        calls = _re.findall(r"(?:harness\.)?confirm\(", src)
        if not calls:
            continue
        defined = "def confirm(" in src or "import harness" in src
        r.append(check(f"{mod} can reach confirm()", defined, True))

    print("\nfallback - a codex failure must not cost the phase")
    import tempfile
    from pathlib import Path as _P

    class Ran2:
        def __init__(s, rc, out="", err=""):
            s.returncode, s.stdout, s.stderr = rc, out, err

    CLAUDE_OK = json.dumps({"result": "claude did it", "num_turns": 3,
                            "subtype": "success", "total_cost_usd": 0.4,
                            "is_error": False})

    def with_fake(codex_rc, fallback="1"):
        """Run one phase with codex forced to a given exit code."""
        calls, real, tele = [], harness.subprocess.run, harness.telegram

        def fake(cmd, **kw):
            calls.append("codex" if cmd[0].endswith("codex") or cmd[0] == "/bin/false"
                         else cmd[0])
            if calls[-1] == "codex":
                return Ran2(codex_rc, "", "codex exploded")
            return Ran2(0, CLAUDE_OK)

        harness.subprocess.run = fake
        harness.telegram = lambda *a, **k: None
        bin_was, harness.CODEX_BIN = harness.CODEX_BIN, "/bin/false"
        os.environ["CODEX_JOBS"] = "all"
        os.environ["CODEX_FALLBACK"] = fallback
        try:
            with tempfile.TemporaryDirectory() as d:
                log = {}
                out = harness.run_phase("gdd", "WRITE x", _P(d), 60, log, timeout_s=5)
                return calls, out, log
        finally:
            harness.subprocess.run, harness.telegram = real, tele
            harness.CODEX_BIN = bin_was
            os.environ.pop("CODEX_FALLBACK", None)

    calls, out, log = with_fake(codex_rc=1)
    r.append(check("codex is tried first", calls[0], "codex"))
    r.append(check("then claude", calls[1:], ["claude"]))
    r.append(check("the phase still returns work", out, "claude did it"))
    r.append(check("the entry is the claude one", log["gdd"]["provider"], "claude"))
    r.append(check("and it is not an error", log["gdd"]["is_error"], False))
    # A silent fallback that looked like a clean codex run would make the
    # provider comparison a lie, so the dead attempt stays in the ledger.
    r.append(check("the failed codex attempt is kept",
                   log["gdd#codex-failed"]["provider"], "codex"))
    r.append(check("only ONE retry", len(calls), 2))

    calls, out, log = with_fake(codex_rc=0)
    r.append(check("a codex run that works is not retried", calls, ["codex"]))

    calls, out, log = with_fake(codex_rc=1, fallback="0")
    r.append(check("CODEX_FALLBACK=0 disables it", calls, ["codex"]))
    r.append(check("and the failure surfaces", log["gdd"]["is_error"], True))

    print("\nrun.json entry shape is unchanged for claude")
    got = harness._parse_claude(Ran(json.dumps(
        {"result": "done", "num_turns": 8, "subtype": "success",
         "total_cost_usd": 3.07, "is_error": False,
         "usage": {"cache_read_input_tokens": 12, "output_tokens": 34}})))
    r.append(check("claude result", got["result"], "done"))
    r.append(check("claude turns", got["num_turns"], 8))
    r.append(check("claude cost", got["cost_usd"], 3.07))

    print(f"\n{sum(r)}/{len(r)} passed")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
