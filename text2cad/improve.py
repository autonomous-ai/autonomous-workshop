#!/usr/bin/env python3
"""Weekly self-improvement session (circuit Loop-4 style, PR-gated for code).

Cron (panda, UTC):  0 1 * * 0  cd /root/text2cad && ./improve.py >> logs/improve.log 2>&1

Authority tiers (Tam 2026-08-11):
- lessons.md / discover_lessons.md / BLOCKS.md doc text  -> commit to main
- ANY code change (text2cad, gate.py, blocks/*.py, ...)  -> branch + PR for Tam

Hard rule: blocks/testbench.py must be ALL PASS before anything is kept.
"""
import datetime
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC_TIER = {"lessons.md", "discover_lessons.md", "blocks/BLOCKS.md", "README.md"}


def sh(cmd, **kw):
    return subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, **kw)


def load_env():
    for line in (HERE / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


PROMPT = """IMPORTANT — one-shot unattended headless session; keep issuing tool
calls until done, never assume a future turn.

You are the weekly SELF-IMPROVEMENT session of the text2cad pipeline (repo at
{here}). Your job: make next week's cycles cheaper, more reliable, and better
selling — based on EVIDENCE from this week, not speculation.

EVIDENCE — read first:
- logs/cycle-*.log and out/*/run.json from the last 7 days (cost, turns,
  failures, escalations, panel verdicts)
- lessons.md + discover_lessons.md (which lessons repeat? repeat = must
  graduate to code)
- blocks/BLOCKS.md (library gaps: what did builds hand-roll that deserves a
  verified block?)

THEN improve, in priority order:
1. Graduate any REPEATED lesson into code (gate linter check, block, or brief
   constraint) — never leave it as advisory text twice.
2. Tighten prompts in `text2cad` where logs show wasted turns or repeated
   misunderstandings.
3. Propose new golden blocks ONLY as code + testbench cases (they ship via PR
   and require Tam's approval — per BLOCKS.md policy).
4. Trim dead code / stale lessons.

RULES:
- Work directly in the repo files. Keep changes SMALL and evidence-linked:
  cite the log/run.json that motivated each change in the commit message body.
- MUST run `.venv/bin/python blocks/testbench.py` and get ALL PASS before you
  finish. If your change breaks it, fix or revert.
- Do NOT touch .env, out/, or credentials. Do NOT git commit/push — the
  wrapper handles git.

Reply with ONE line: a <=60-char summary of what you improved (or NO-CHANGE)."""


def dirty_files() -> set:
    """Paths `git status` calls modified or untracked, right now."""
    out = sh(["git", "status", "--porcelain", "--untracked-files=all"]).stdout
    return {l[3:].strip() for l in out.splitlines() if l.strip()}


def main() -> int:
    load_env()
    today = datetime.date.today().isoformat()
    branch = f"improve/{today}"
    sh(["git", "checkout", "main"])
    sh(["git", "pull"])
    # The working tree carries operational files that are deliberately NOT in
    # main (tg_bridge.py, qwen_proxy.py, gen_howto_video.py, ...) and owner
    # edits not yet committed. 2026-08-23 this script `git add -A`-ed all of
    # them into the improve branch and `git checkout main` then REMOVED them
    # from the working tree - the Telegram bridge, the video chain and the
    # owner's concept_image.py edits vanished until a session restored them
    # from the branch. Snapshot the pre-existing dirt; only what the SESSION
    # changes is ever staged, and the dirt rides across the checkout untouched.
    pre_dirty = dirty_files()
    if pre_dirty:
        print(f"[{today}] pre-existing untracked/modified (left alone): {sorted(pre_dirty)}")
    sh(["git", "checkout", "-B", branch])

    env = dict(os.environ)
    env["PATH"] = f"{Path.home()}/.local/bin:" + env.get("PATH", "")
    allowed = "Bash,Read,Write,Edit,Glob,Grep,TodoWrite"
    r = subprocess.run(["claude", "-p", PROMPT.format(here=HERE),
                        "--model", "claude-sonnet-5", "--allowedTools", allowed,
                        "--add-dir", str(HERE), "--max-turns", "80",
                        "--output-format", "json"],
                       cwd=HERE, env=env, capture_output=True, text=True,
                       timeout=2 * 3600)
    print(f"[{today}] session tail: {r.stdout[-400:]}")

    tb = sh([str(HERE / ".venv/bin/python"), "blocks/testbench.py"], timeout=600)
    if "ALL PASS" not in tb.stdout:
        print("testbench FAILED after session — reverting everything")
        sh(["git", "checkout", "--", "."])
        sh(["git", "checkout", "main"])
        return 1

    changed = sorted(dirty_files() - pre_dirty)
    if not changed:
        print("no changes"); sh(["git", "checkout", "main"]); return 0

    sh(["git", "add", "--", *changed])
    sh(["git", "commit", "-m", f"improve: weekly session {today}"])
    if set(changed) <= DOC_TIER:
        sh(["git", "checkout", "main"])
        sh(["git", "merge", branch])
        sh(["git", "push"])
        sh(["git", "branch", "-D", branch])
        print(f"doc-tier changes merged to main: {changed}")
    else:
        sh(["git", "push", "-u", "origin", branch])
        pr = sh(["gh", "pr", "create", "--title", f"improve: weekly session {today}",
                 "--body", "Automated self-improvement session. Code-tier changes "
                 f"require Tam's review.\n\nChanged: {', '.join(changed)}\n\n"
                 "Testbench: ALL PASS.", "--base", "main"])
        sh(["git", "checkout", "main"])
        print(f"code-tier changes -> PR: {pr.stdout.strip() or pr.stderr[-200:]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
