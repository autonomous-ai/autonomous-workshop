#!/usr/bin/env python3
"""Tally a Workshop run's component rounds, with repeats split three ways.

    uv run python tally.py <wish-id> [--json]
    python3 tally.py --workspace <run-workspace> [--json]

Each failing round is classified by what failed:

- print gate: a thickness or overhang defect on the built B-rep. A repeat is a
  failing round whose gate defect (feature at a location) also failed the
  previous failing round of that Component: a Repeated Print Defect.
- Detail Refusal: print-details refused a detail at build, before any gate
  (CONTEXT.md, issue #86). A repeat is the same feature refused at the same
  call site (runs after #86) or for the same reason (older runs, which log no
  site) in the previous failing round. Not a print defect.
- build error: any other exception (ValueError, a cadgen contract). A repeat is
  the same error class and message start.

Also per round: reviewer agreement, Shape Round, lock, camera mismatch and the
number of Reference Conflicts the review recorded.

`--json` prints the totals the build-a-toy ledger records for an attempt's
progress: `locked` (Components whose latest round is locked) and
`repeated_print_defects`.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from runpaths import make_dir, resolve_workspace  # noqa: E402


def refusal_key(feature: str, text: str) -> str:
    """An older run's refusal: feature plus the words before its first number."""
    reason = re.split(r"-?\d", text.strip(), maxsplit=1)[0].strip(" :;,") or "measure"
    return f"{feature}:{reason}"


def classify(summary: dict, comp_dir: str) -> tuple[set, set, set]:
    gate, refused, build = set(), set(), set()
    detail = ((summary.get("build") or {}).get(os.path.basename(os.path.dirname(comp_dir))) or {})
    for item in detail.get("detail_refusals") or []:  # runs after #86
        refused.add(f"{item.get('feature')}@{item.get('site')}")
    for log in sorted(glob.glob(f"{comp_dir}/gen-*.log")):
        with open(log, errors="replace") as handle:
            for line in handle:
                m = re.search(r"FAILED: (\w+): (.*)", line)
                if not m:
                    continue
                kind, text = m.group(1), m.group(2)
                if kind == "PrintLimitError":
                    feature, _, rest = text.partition(": ")
                    if not detail.get("detail_refusals"):
                        refused.add(refusal_key(feature.strip(), rest))
                elif kind != "DetailRefusals":
                    build.add(f"{kind}: {text[:40]}")
    for _comp, p in (summary.get("print") or {}).items():
        for name in ("thickness", "overhang"):
            g = p.get(name) or {}
            if g.get("verdict") == "FAIL" and "build failed" not in (g.get("failures") or []):
                for x in g.get("defects") or [""]:
                    gate.add(f"{name}:{x}")
    return gate, refused, build


def conflicts(comp_dir: str) -> int:
    path = os.path.join(comp_dir, "reference-conflicts.json")
    try:
        with open(path) as handle:
            return len(json.load(handle))
    except (OSError, ValueError):
        return 0


def collect(make: Path) -> dict[str, list[dict]]:
    rows: dict[str, list[dict]] = {}
    pattern = f"{make}/r*/product/cad/measure/component-rounds/*/r*/summary.json"
    for s in sorted(glob.glob(pattern)):
        comp_dir = os.path.dirname(s)
        comp, rnd = s.split(os.sep)[-3], s.split(os.sep)[-2]
        with open(s) as handle:
            d = json.load(handle)
        rv = d.get("review") or {}
        if not rv and os.path.exists(os.path.join(comp_dir, "review.json")):
            with open(os.path.join(comp_dir, "review.json")) as handle:
                rv = json.load(handle)
        fail = not d.get("print") or not all(p.get("verdict") == "PASS" for p in d["print"].values())
        gate, refused, build = classify(d, comp_dir)
        rows.setdefault(comp, []).append(dict(
            r=rnd, fail=fail, gate=gate, refused=refused, build=build, agrees=rv.get("agrees"),
            cam="camera_mismatch" in json.dumps(rv), shape=d.get("shape_round"),
            locked=bool(d.get("locked")), rc=conflicts(comp_dir)))
    return rows


def tally(rows: dict[str, list[dict]]) -> tuple[list[str], dict]:
    lines = []
    tot = failing = 0
    rep = {"gate": 0, "refused": 0, "build": 0}
    for comp, rs in rows.items():
        prev = {"gate": set(), "refused": set(), "build": set()}
        for x in rs:
            tot += 1
            failing += x["fail"]
            flags = []
            for kind, label in (("gate", "PRINT"), ("refused", "REFUSAL"), ("build", "BUILD")):
                hit = x["fail"] and bool(x[kind] & prev[kind])
                rep[kind] += hit
                if hit:
                    flags.append(label)
            lines.append(
                f"{comp:14} {x['r']} {'FAIL' if x['fail'] else 'pass'} {'+'.join(flags) or '-':14} "
                f"agrees={x['agrees']} shape={x['shape']} locked={x['locked']} cam={x['cam']} rc={x['rc']} "
                f"gate={sorted(x['gate'])} refused={sorted(x['refused'])} build={sorted(x['build'])}")
            if x["fail"]:
                prev = {k: x[k] for k in prev}
    locked = sorted(comp for comp, rs in rows.items() if rs and rs[-1]["locked"])
    totals = {
        "component_rounds": tot,
        "failing_rounds": failing,
        "repeated_print_defects": rep["gate"],
        "repeated_detail_refusals": rep["refused"],
        "repeated_build_errors": rep["build"],
        "locked": len(locked),
        "locked_components": locked,
    }
    return lines, totals


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tally a run's component rounds.")
    parser.add_argument("wish_id", nargs="?")
    parser.add_argument("--workspace", help="the run workspace, instead of a wish id")
    parser.add_argument("--json", action="store_true", help="print only the totals, as JSON")
    args = parser.parse_args(argv)
    rows = collect(make_dir(resolve_workspace(args.wish_id, args.workspace)))
    lines, totals = tally(rows)
    if args.json:
        print(json.dumps(totals, indent=2))
        return 0
    for line in lines:
        print(line)
    tot, failing = totals["component_rounds"], totals["failing_rounds"]
    print(f"\nrounds={tot} failing={failing} ({100 * failing // max(tot, 1)}%)")
    print(f"repeated print defects={totals['repeated_print_defects']}  "
          f"repeated Detail Refusals={totals['repeated_detail_refusals']}  "
          f"repeated build errors={totals['repeated_build_errors']}")
    print(f"locked={totals['locked']} {totals['locked_components']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
