#!/usr/bin/env python3
"""Emit every actionable line across ALL text2game logs, including logs that do
not exist yet.

Written 2026-08-20 after the monitor spent 35 minutes tailing full-run.log,
which stopped being written the moment the phase 1 driver exited: phase 2 had
been launched separately into its own file and a failure there would not have
reached anyone. `tail -f <one file>` is only correct while that file is the one
being written, and in a pipeline that spawns a process per phase it stops being
true without any error. Scan the DIRECTORY and keep a per-file offset instead.
"""
import re
import sys
import time
from pathlib import Path

LOGS = Path(__file__).resolve().parent / "logs"
SKIP = ("watch", "manim", "install")          # our own noise

# Progress worth seeing, plus every failure signature we would act on. Silence
# has to mean "nothing happened", never "the watcher was looking elsewhere".
PAT = re.compile(
    r"^== |WINNER|ABORT|FAILED|DECISION NEEDED|falling back to claude|"
    r"failed on BOTH|=> consistency|=> design|AMBIGUOUS|CHECKPOINT|panel:|"
    r"stopped at|GATE FAIL|Traceback|quota|PROPOSAL|phase 1 exited|"
    r"coherence |\[gate\]|\[plates\]|high after|timed out|Killed|MemoryError|"
    r"no legal|is not printable|rc=", re.I)

seen = {}
while True:
    for f in sorted(LOGS.glob("*.log")):
        if any(s in f.name for s in SKIP):
            continue
        try:
            size = f.stat().st_size
        except OSError:
            continue
        pos = seen.get(f.name)
        if pos is None:
            seen[f.name] = size          # start at the end of pre-existing logs
            continue
        if size < pos:                   # truncated/rotated
            pos = 0
        if size > pos:
            with f.open("r", encoding="utf-8", errors="replace") as fh:
                fh.seek(pos)
                chunk = fh.read()
                seen[f.name] = fh.tell()
            for line in chunk.splitlines():
                if PAT.search(line):
                    print(f"[{f.name}] {line.strip()[:400]}", flush=True)
    time.sleep(10)
