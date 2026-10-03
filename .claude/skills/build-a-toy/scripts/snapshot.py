#!/usr/bin/env python3
"""One line of a run's state, for watch.sh and the unattended loop.

    uv run -q workshop status <wish-id> --json | uv run python snapshot.py <wish-id>

Reads `workshop status --json` on stdin and counts what the run's own files
show: Component Worker spawns (from the Claude Code transcripts), Blocked
Reports still open or waiting, Reference Camera mismatches and Reference
Conflict entries. Exits 10 once the run has stopped (a status other than
`active`, or an active run whose `stop_category` names a real stop such as
`budget`), so a watcher knows to diagnose it. `workshop status` gives every
run that is not complete a `stop_category`, so an active run's
`unclassified` or `inspection-in-progress` is not a stop.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from runpaths import claude_project_dir, make_dir, run_workspace  # noqa: E402

STOPPED = 10
OPEN_BLOCKED = {"open", "waiting"}
RUNNING_CATEGORIES = {None, "unclassified", "inspection-in-progress"}


def count_files(root: Path, pattern: str, needle: str) -> int:
    hits = 0
    for path in glob.glob(str(root / "**" / pattern), recursive=True):
        try:
            with open(path, errors="replace") as handle:
                if needle in handle.read():
                    hits += 1
        except OSError:
            continue
    return hits


def reference_conflicts(make: Path) -> int:
    total = 0
    for path in glob.glob(str(make / "**" / "reference-conflicts.json"), recursive=True):
        try:
            with open(path) as handle:
                total += len(json.load(handle))
        except (OSError, ValueError):
            continue
    return total


def snapshot(status: dict, workspace: Path, transcripts: Path) -> dict:
    make = make_dir(workspace)
    budget = status.get("budget") or {}
    blocked = status.get("blocked_reports") or []
    return {
        "status": status.get("status"),
        "stage": status.get("stage"),
        "stop": status.get("stop_category"),
        "tokens_m": int((budget.get("used_tokens") or 0) / 1e6),
        "limit_m": int((budget.get("limit_tokens") or 0) / 1e6),
        "blocked_open": sum(1 for b in blocked if b.get("status") in OPEN_BLOCKED),
        "needs": len(status.get("needs") or []),
        "amendments": len(status.get("contract_amendments") or []),
        "acceptances": len(status.get("component_acceptances") or []),
        "workers": count_files(transcripts, "*.meta.json", '"component-worker"'),
        "camera_mismatch": count_files(make, "review*.json", '"camera_mismatch"'),
        "reference_conflicts": reference_conflicts(make),
    }


def stopped(status: dict) -> bool:
    if status.get("status") != "active":
        return True
    return status.get("stop_category") not in RUNNING_CATEGORIES


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: workshop status <id> --json | snapshot.py <wish-id>")
    status = json.load(sys.stdin)
    workspace = run_workspace(argv[1])
    line = snapshot(status, workspace, claude_project_dir(workspace))
    print(" ".join(f"{k}={v}" for k, v in line.items()))
    return STOPPED if stopped(status) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
