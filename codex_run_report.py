#!/usr/bin/env python3
"""Report what a Codex product run actually spent, from its own rollouts.

    python3 codex_run_report.py <wish-id> [<wish-id> ...]
    python3 codex_run_report.py --latest

`compare_runs.py` reads Claude transcripts; this reads the Codex rollout JSONL
that a native run leaves in ``~/.codex/sessions``, plus the host's budget and
progress records. It surfaces the numbers that separated a finished Make from a
stuck one on 2026-09-08:

* compaction count -- six in a run that finished Make in one turn, sixteen in
  one that never finished, because a 64k ceiling could not hold a complex Make's
  working state;
* input-to-output ratio -- reported for context, NOT a health signal: every run
  here is input-dominated because each tool call re-sends the whole session, and
  the finished run's 144:1 is higher than either stuck run's 112:1 and 133:1;
* repeated identical commands -- nineteen identical finalizer probes in one run,
  which is a Goal rebuilding state a compaction dropped;
* empty polls -- 64 of 180 tool calls in one run waiting on a verifier, each
  one re-sending the whole session context.

Read total spend, attempt count, compactions and repeated commands together.
Many compactions with repeated identical commands is a run rediscovering what it
already knew. The ratio on its own says nothing.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

HOME = Path.home()
STATE = HOME / "Library/Application Support/Autonomous Workshop/state"
SESSIONS = HOME / ".codex/sessions"


def _load_json(path: Path):
    try:
        return json.loads(path.read_bytes())
    except (OSError, ValueError):
        return None


def host_records(wish_id: str) -> dict:
    """Read the host's own view: budget, progress and per-stage usage."""

    root = STATE / wish_id
    budget = _load_json(root / "native-budget.json") or {}
    progress = _load_json(root / "native-progress.json") or {}
    usage = _load_json(root / "native-token-usage.json") or {}
    observation = (budget.get("budget") or {}).get("observation") or {}
    return {
        "limit": (budget.get("budget") or {}).get("limit_tokens"),
        "used": (budget.get("budget") or {}).get("used_tokens"),
        "threads": [
            thread["thread_id"] for thread in observation.get("threads", [])
        ],
        "root_thread": observation.get("root_thread_id"),
        "activity": progress.get("activity"),
        "stage": progress.get("checkpoint_stage"),
        "attempt": progress.get("stage_attempt"),
        "native_turns": progress.get("native_turns"),
        "stages": usage.get("stages") or {},
        "stopped": _load_json(root / "token-budget-stop.json"),
    }


def rollout_paths(thread_ids) -> list[Path]:
    wanted = set(thread_ids)
    found = []
    for path in SESSIONS.rglob("rollout-*.jsonl"):
        for thread in wanted:
            if path.name.endswith(thread + ".jsonl"):
                found.append(path)
    return sorted(found)


def rollout_report(path: Path) -> dict:
    requests = []
    compactions = 0
    calls = []
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        kind = row.get("type")
        payload = row.get("payload") or {}
        if kind == "token_usage_record":
            usage = payload.get("usage") or {}
            requests.append(
                (usage.get("input_tokens", 0), usage.get("output_tokens", 0))
            )
        elif kind == "compacted":
            compactions += 1
        elif kind == "response_item" and payload.get("type") in (
            "custom_tool_call",
            "function_call",
        ):
            calls.append(payload.get("input") or payload.get("arguments") or "")
    inputs = [value for value, _ in requests]
    outputs = [value for _, value in requests]
    polls = [call for call in calls if "write_stdin" in call]
    # Collapse each call to its leading command text so genuine repeats group.
    signatures = collections.Counter(
        " ".join(call[:160].split()) for call in calls
    )
    return {
        "path": path,
        "requests": len(requests),
        "input": sum(inputs),
        "output": sum(outputs),
        "ratio": (sum(inputs) / sum(outputs)) if sum(outputs) else None,
        "max_request_input": max(inputs) if inputs else 0,
        "compactions": compactions,
        "calls": len(calls),
        "polls": len(polls),
        "repeats": [
            (count, text)
            for text, count in signatures.most_common(8)
            if count > 1
        ],
    }


def _thousands(value) -> str:
    return "-" if value is None else format(value, ",")


def report(wish_id: str) -> None:
    host = host_records(wish_id)
    print("=" * 78)
    print(wish_id)
    print("  stage %s, activity %s, attempt %s, native turns %s"
          % (host["stage"], host["activity"], host["attempt"],
             host["native_turns"]))
    print("  budget %s of %s tokens"
          % (_thousands(host["used"]), _thousands(host["limit"])))
    if host["stopped"]:
        print("  STOPPED: %s" % host["stopped"].get("reason"))
    for stage, values in sorted(host["stages"].items()):
        print("  stage %-9s turns %-3s input %-12s output %s"
              % (stage, values.get("turns"),
                 _thousands(values.get("input_tokens")),
                 _thousands(values.get("output_tokens"))))
    paths = rollout_paths(host["threads"])
    if not paths:
        print("  no Codex rollout found for this run's threads")
        return
    for path in paths:
        data = rollout_report(path)
        role = "root" if path.name.endswith(
            (host["root_thread"] or "") + ".jsonl"
        ) else "child"
        print("  --- %s rollout %s" % (role, path.name[-41:-6]))
        print("      requests %-5d input %-12s output %-9s ratio %s"
              % (data["requests"], _thousands(data["input"]),
                 _thousands(data["output"]),
                 "-" if data["ratio"] is None
                 else "%.1f:1" % data["ratio"]))
        print("      largest single request %s input tokens"
              % _thousands(data["max_request_input"]))
        print("      compactions %-4d tool calls %-5d empty polls %d (%s)"
              % (data["compactions"], data["calls"], data["polls"],
                 "-" if not data["calls"]
                 else "%.0f%%" % (100 * data["polls"] / data["calls"])))
        for count, text in data["repeats"]:
            print("      repeated %2dx  %s" % (count, text[:96]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wish_ids", nargs="*")
    parser.add_argument("--latest", action="store_true",
                        help="report the most recently active run")
    arguments = parser.parse_args()
    identifiers = list(arguments.wish_ids)
    if arguments.latest or not identifiers:
        candidates = [
            path for path in STATE.iterdir()
            if path.is_dir() and re.fullmatch(r"wish-[0-9]{8}-[0-9]{6}-[0-9a-f]{8}",
                                              path.name)
        ]
        if not candidates:
            print("no runs found", file=sys.stderr)
            return 1
        newest = max(
            candidates,
            key=lambda path: (path / "native-progress.json").stat().st_mtime
            if (path / "native-progress.json").exists()
            else path.stat().st_mtime,
        )
        identifiers.append(newest.name)
    for wish_id in identifiers:
        report(wish_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
