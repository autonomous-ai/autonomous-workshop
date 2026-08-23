#!/usr/bin/env python3
"""improve.py — the periodic self-improvement session, with authority split by
what a change can break.

    python3 board-game/tools/improve.py            # run a session
    python3 board-game/tools/improve.py --dry-run  # just show the evidence

Two tiers, decided mechanically rather than by anyone's judgement about what
counts as a big change:

  DOC tier   lessons, BLOCKS.md prose, pain points, README
             -> committed to the working branch directly
  CODE tier  gates, thresholds, blocks, agents, commands, this file
             -> branch + PR, because a human has to read it

  FORBIDDEN  TASTE.md, the threshold baseline, the queue, ideas, .env
             -> never, by any path

The forbidden list is not squeamishness. `TASTE.md` is the owner's own words
and the only signal here that does not come from a model — a pipeline that can
edit it can talk itself into anything. `thresholds_baseline.json` is what
`audit.py` compares against to catch the gate being loosened; a session that
could re-record the baseline could loosen every gate and leave the audit
green.

Nothing is kept unless all three suites pass. If the session breaks them, the
whole working tree is reverted — there is no partial credit for a change that
broke the checks that prove the change was safe.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PY = REPO_ROOT / ".venv" / "bin" / "python"

DOC_TIER = {
    "board-game/lessons.md",
    "board-game/blocks/BLOCKS.md",
    "board-game/PAIN_POINTS.md",
    "README.md",
}

FORBIDDEN = {
    "board-game/TASTE.md",
    "board-game/tools/thresholds_baseline.json",
    "board-game/QUEUE.json",
    ".env",
}
FORBIDDEN_PREFIXES = ("board-game/ideas/", "board-game/history/",
                      "board-game/archive/", "cadcode/", ".venv/")

SUITES = [
    ("gate", ["board-game/tools/test_gate.py"]),
    # blocks.py is CODE tier, so a session may add a helper to it. The closure
    # table in here fails on a block whose compositions nobody has accounted
    # for, which is what stops the library growing faster than its tested space.
    ("checks", ["board-game/tools/test_checks.py"]),
    ("blocks", ["board-game/blocks/testbench.py"]),
    # A session can edit gate.py and rewrite lessons.md in the same run, so it
    # is able to delete the code a lesson graduated into and leave the marker
    # claiming otherwise. That failure is silent and permanent: the lesson is
    # out of the build prompts precisely because it graduated.
    ("graduations", ["board-game/tools/graduation_check.py"]),
]


def sh(cmd: list, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, **kw)


# Words too common in this domain to signal that two lessons are the same one.
_STOP = frozenset("""a an and are as at be by every for from in into is it its must
never not of on one or so that the them then there this to when with you your
always part parts piece pieces build built model""".split())

_VERBATIM_RATIO = 0.75   # near-verbatim re-append: measured 0.805 on a real pair
# Deliberately low. The two errors here cost wildly different amounts: a missed
# repeat means a lesson never graduates, which is the precise failure this
# whole mechanism exists to prevent, while a false positive costs one line in a
# prompt that the session reads and dismisses. A real paraphrase pair measured
# 0.44, so anything at or above a third of the smaller lesson's content words
# is worth putting in front of the session.
_OVERLAP_RATIO = 0.35


def _content_words(line: str) -> set:
    return {w for w in re.findall(r"[a-z_]{3,}", line.lower()) if w not in _STOP}


def repeated_lessons() -> list[str]:
    """Lessons that have shown up twice, by two different measures.

    The graduation rule — a lesson that repeats must become code — only works
    if repetition is caught mechanically. Left to judgement, the second
    occurrence reads as a fresh insight every time, which is exactly how the
    old pipeline knew one fact for three turns and changed nothing.

    Be clear about the limit: this is a floor, not a ceiling. Measured on a
    real pair, a near-verbatim re-append scores 0.805 on character similarity
    while a genuine paraphrase of the same lesson scores 0.536 — no lexical
    threshold separates that paraphrase from an unrelated line. Content-word
    overlap catches some of the rest, and the session is told explicitly to
    look for semantic repeats itself, because the case that matters most is
    the one this function cannot see.
    """
    path = REPO_ROOT / "board-game" / "lessons.md"
    if not path.is_file():
        return []
    lines = [ln.strip("- ").strip() for ln in path.read_text(encoding="utf-8").splitlines()
             if ln.strip().startswith("-") and len(ln) > 40]
    dupes = []
    for i, a in enumerate(lines):
        for b in lines[i + 1:]:
            reason = None
            if difflib.SequenceMatcher(None, a, b).ratio() >= _VERBATIM_RATIO:
                reason = "near-verbatim"
            else:
                wa, wb = _content_words(a), _content_words(b)
                if wa and wb:
                    overlap = len(wa & wb) / min(len(wa), len(wb))
                    if overlap >= _OVERLAP_RATIO:
                        reason = f"content overlap {overlap:.0%}"
            if reason:
                dupes.append(f"[{reason}] {a[:100]}  ~=  {b[:100]}")
    return dupes


def evidence() -> dict:
    """What actually happened, as opposed to what anyone remembers happening."""
    queue_path = REPO_ROOT / "board-game" / "QUEUE.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8")) if queue_path.is_file() else {"ideas": {}}
    states: dict[str, int] = {}
    for item in queue.get("ideas", {}).values():
        states[item["state"]] = states.get(item["state"], 0) + 1

    gate_fails: dict[str, int] = {}
    for report in (REPO_ROOT / "board-game" / "ideas").glob("*/project/gate.json"):
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for fail in data.get("fails") or []:
            kind = fail.split(":", 1)[0]
            gate_fails[kind] = gate_fails.get(kind, 0) + 1

    return {"queue_states": states,
            "gate_failure_kinds": dict(sorted(gate_fails.items(),
                                              key=lambda kv: -kv[1])),
            "repeated_lessons": repeated_lessons()}


PROMPT = """IMPORTANT — one-shot unattended session. Keep issuing tool calls
until the work is done; no future turn will wake you.

You are the periodic self-improvement session for the board-game pipeline at
{root}. The pipeline's goal is a good CAD model: one that prints, one that
plays, one the owner approves. Improving the agents is only how we get there,
so prefer a change that makes the next build better over a change that makes
the process more elegant.

EVIDENCE — read this first, and work only from it:

{evidence}

Also read: board-game/PAIN_POINTS.md (friction the agents reported),
board-game/lessons.md, board-game/blocks/BLOCKS.md, and the gate.json of any
idea that failed.

IN PRIORITY ORDER:

1. GRADUATE REPEATED LESSONS. Any lesson in `repeated_lessons` above has now
   cost two builds and must stop being prose: turn it into a lint rule in
   board-game/tools/gate.py, a threshold, a golden block, or a constraint in
   the brief-writer's template. Then collapse the duplicate lines into the one
   graduated entry, marked [GRADUATED -> where].
   The marker must name something graduation_check.py can find — `module.SYMBOL`
   or `module:"literal text"`, per the grammar at the top of lessons.md. One it
   cannot resolve fails the suite, and rightly: graduating a lesson is what
   takes it OUT of the build prompts, so a claim nothing verifies leaves that
   lesson neither enforced nor remembered.
   LAND IT AS FAR UPSTREAM AS IT WILL GO. The tier ladder is in lessons.md:
   planner, then block, then brief, then prompt, then check. A gate check is
   the cheapest thing to write and the weakest thing to have — it means every
   build still writes the defect and still spends a repair round undoing it.
   Ask what would stop the defect being BUILT, not what would catch it, and
   say in the commit body which tier you landed at and which ones you ruled
   out. If check really is the ceiling, add `| ceiling: <why nothing upstream
   can hold this>` to the marker; audit.py raises every check-only graduation
   that has no such reason.
   That list is a FLOOR, not the answer. It compares wording, and two lessons
   that say the same thing in different words score no higher than two
   unrelated ones — measured, not assumed. So read lessons.md yourself and
   graduate any lesson that repeats in MEANING, whether or not it appears
   above. This is the single highest-value thing you do: the pipeline this
   replaced knew one fact for three turns and changed nothing.
2. FIX WHAT THE AGENTS REPORTED. Pain points naming an ambiguous instruction,
   a wrong path, or a missing block are cheap and high value.
3. PROPOSE A BLOCK for geometry that builds keep hand-rolling — as code plus a
   testbench case, never as prose. blocks/ is human-approved, so this ships as
   a PR and that is correct. A new block also owes an entry in
   test_checks.COMPOSITIONS for every pairing with an existing one, saying
   where it composes or why it cannot; the suite fails until it does. That is
   deliberate. A library that grows faster than its tested space is how a
   builder ends up composing two blocks nobody has ever run together.
4. TIGHTEN AN AGENT'S INSTRUCTIONS where the record shows repeated
   misunderstanding.

RULES:
- Cite the evidence for each change in the commit body. A change with no
  evidence behind it is a preference.
- NEVER touch: board-game/TASTE.md, board-game/tools/thresholds_baseline.json,
  board-game/QUEUE.json, board-game/ideas/, .env. TASTE.md is the owner's own
  words; the baseline is what catches the gates being loosened.
- You may TIGHTEN a threshold with evidence. Loosening one is a PR for a human
  to decide, and you must say so rather than doing it.
- Do not git commit or push. The wrapper handles git.
- All three test suites must pass when you are done. If your change breaks
  one, fix it or revert it.

Reply with ONE line: a <=70-char summary, or NO-CHANGE."""


def classify(changed: list[str]) -> tuple[list, list, list]:
    forbidden = [f for f in changed
                 if f in FORBIDDEN or f.startswith(FORBIDDEN_PREFIXES)]
    doc = [f for f in changed if f in DOC_TIER and f not in forbidden]
    code = [f for f in changed if f not in DOC_TIER and f not in forbidden]
    return doc, code, forbidden


def run_suites() -> tuple[bool, str]:
    python = str(PY) if PY.is_file() else sys.executable
    for label, cmd in SUITES:
        r = sh([python, *cmd], timeout=1800)
        if "ALL PASS" not in r.stdout:
            return False, f"{label}: {(r.stdout + r.stderr)[-400:]}"
    return True, "all suites ALL PASS"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--model", default="claude-sonnet-5")
    args = ap.parse_args()

    ev = evidence()
    if args.dry_run:
        print(json.dumps(ev, indent=2))
        return 0

    if sh(["git", "status", "--porcelain"]).stdout.strip():
        print("working tree is dirty — commit or stash first")
        return 1

    today = date.today().isoformat()
    prompt = PROMPT.format(root=REPO_ROOT, evidence=json.dumps(ev, indent=2))
    env = {**os.environ, "PATH": f"{Path.home()}/.local/bin:" + os.environ.get("PATH", "")}
    r = subprocess.run(
        ["claude", "-p", prompt, "--model", args.model,
         "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
         "--add-dir", str(REPO_ROOT), "--max-turns", "80",
         "--output-format", "json"],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=2 * 3600)
    print(f"session: {r.stdout[-400:]}")

    ok, detail = run_suites()
    if not ok:
        print(f"suites FAILED after the session — reverting everything\n  {detail}")
        sh(["git", "checkout", "--", "."])
        sh(["git", "clean", "-fd"])
        return 1

    changed = [ln[3:] for ln in sh(["git", "status", "--porcelain"]).stdout.splitlines()
               if ln.strip()]
    if not changed:
        print("no changes")
        return 0

    doc, code, forbidden = classify(changed)
    if forbidden:
        print(f"session touched forbidden paths {forbidden} — reverting everything")
        sh(["git", "checkout", "--", "."])
        sh(["git", "clean", "-fd"])
        return 1

    if code:
        branch = f"improve/{today}"
        sh(["git", "checkout", "-B", branch])
        sh(["git", "add", "-A"])
        sh(["git", "commit", "-m", f"improve: session {today}"])
        sh(["git", "push", "-u", "origin", branch])
        pr = sh(["gh", "pr", "create", "--title", f"improve: session {today}",
                 "--body", f"Automated self-improvement session.\n\n"
                           f"Code-tier changes need review: {', '.join(code)}\n"
                           f"Doc-tier in the same branch: {', '.join(doc) or 'none'}\n\n"
                           f"All {len(SUITES)} suites: ALL PASS."])
        print(f"code-tier -> PR: {(pr.stdout or pr.stderr).strip()[-200:]}")
    else:
        sh(["git", "add", *doc])
        sh(["git", "commit", "-m", f"improve: doc-tier session {today}\n\n"
                                   f"{', '.join(doc)}"])
        print(f"doc-tier committed: {doc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
