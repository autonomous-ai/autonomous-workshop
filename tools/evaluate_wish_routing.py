#!/usr/bin/env python3
"""Run the five canonical Wishes through the real customer CLI and Manager."""

from __future__ import annotations

import argparse
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cli.main import main as workshop_main


CASES = (
    (
        "alice",
        "I wish for a chess set where every piece is someone in my family, "
        "with the classic rules unchanged",
    ),
    (
        "bob",
        "I wish for a wind-up version of my dog that walks across my desk",
    ),
    (
        "eve",
        "I wish for a tiny playable world of the coffee shop where my partner "
        "and I first met",
    ),
    (
        "ivy",
        "I wish for a hand-held model that lets me turn the Moon and feel why "
        "eclipses do not happen every month",
    ),
    (
        "leo",
        "I wish for a brand-new two-player strategy game about rival lighthouse "
        "keepers signaling through a storm",
    ),
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    results = []
    failed = False
    for expected, objective in CASES:
        output = io.StringIO()
        with redirect_stdout(output):
            status = workshop_main(
                ("wish", objective, "--root", str(args.root), "--json")
            )
        receipt = json.loads(output.getvalue())
        actual = receipt.get("match", {}).get("inventor_id")
        passed = status == 0 and actual == expected
        failed = failed or not passed
        results.append(
            {
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "score": receipt.get("match", {}).get("score"),
                "status": receipt.get("status"),
                "stopped_at": receipt.get("result", {}).get("job"),
            }
        )
        print("%s  expected=%s actual=%s" % ("PASS" if passed else "FAIL", expected, actual))
    print(json.dumps({"schema_version": 1, "results": results}, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
