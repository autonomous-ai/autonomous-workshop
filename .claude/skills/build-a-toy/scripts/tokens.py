#!/usr/bin/env python3
"""Tokens and cost units a Claude Code run spent, by agent type, from its transcripts.

    uv run python tokens.py <wish-id> [--json]
    python3 tokens.py --transcripts <claude-project-dir> [--json]

Cost units weight each million tokens by what it costs relative to fresh
input: input 1, cache write 1.25, cache read 0.1, output 5. The build-a-toy
ledger sums them per attempt into `cost_units`. A message is counted once
per transcript file, however many times it was streamed.
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from runpaths import claude_project_dir, resolve_workspace  # noqa: E402

WEIGHTS = {"in": 1.0, "cw": 1.25, "cr": 0.1, "out": 5.0}


def collect(transcripts: Path) -> dict[str, collections.Counter]:
    agg: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    seen = set()
    for f in sorted(glob.glob(f"{transcripts}/**/*.jsonl", recursive=True)):
        meta = f[:-6] + ".meta.json"
        who = "root"
        if os.path.exists(meta):
            with open(meta) as handle:
                who = json.load(handle).get("agentType", "?")
        with open(f, errors="replace") as handle:
            for line in handle:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                m = d.get("message") or {}
                u, mid = m.get("usage"), m.get("id")
                if not u or not mid or (f, mid) in seen:
                    continue
                seen.add((f, mid))
                c = agg[who]
                c["in"] += u.get("input_tokens", 0)
                c["cw"] += u.get("cache_creation_input_tokens", 0)
                c["cr"] += u.get("cache_read_input_tokens", 0)
                c["out"] += u.get("output_tokens", 0)
                c["n"] += 1
    return agg


def cost_units(c: collections.Counter) -> float:
    return sum(WEIGHTS[k] * c[k] for k in WEIGHTS) / 1e6


def report(agg: dict[str, collections.Counter]) -> dict:
    agents = {}
    total = collections.Counter()
    for who, c in sorted(agg.items()):
        total.update(c)
        agents[who] = {
            "messages": c["n"],
            "tokens": c["in"] + c["cw"] + c["cr"] + c["out"],
            "cache_read": c["cr"],
            "cache_write": c["cw"],
            "output": c["out"],
            "cost_units": round(cost_units(c), 2),
        }
    return {
        "agents": agents,
        "tokens": total["in"] + total["cw"] + total["cr"] + total["out"],
        "cost_units": round(cost_units(total), 2),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tokens and cost units from a run's transcripts.")
    parser.add_argument("wish_id", nargs="?")
    parser.add_argument("--workspace", help="the run workspace, instead of a wish id")
    parser.add_argument("--transcripts", help="the Claude Code project directory itself")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.transcripts:
        transcripts = Path(args.transcripts).expanduser()
    else:
        transcripts = claude_project_dir(resolve_workspace(args.wish_id, args.workspace))
    result = report(collect(transcripts))
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    for who, a in result["agents"].items():
        print(f"{who:20} msgs={a['messages']:5} total={a['tokens'] / 1e6:6.1f}M "
              f"cr={a['cache_read'] / 1e6:5.1f}M cw={a['cache_write'] / 1e6:5.2f}M "
              f"out={a['output'] / 1e3:6.0f}k cost_units={a['cost_units']:5.2f}")
    print(f"{'all':20} total={result['tokens'] / 1e6:6.1f}M cost_units={result['cost_units']:5.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
