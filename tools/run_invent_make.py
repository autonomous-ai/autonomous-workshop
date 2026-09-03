#!/usr/bin/env python3
"""Run a real fixed-Wish Invent/Concept/Make acceptance test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from workshop.errors import WorkshopError  # noqa: E402
from workshop.wish import Wish, generate_wish_id  # noqa: E402
from workshop.workflow import (  # noqa: E402
    native_run_paths,
    resume_native_phase_test,
    start_native_phase_test,
)


DEFAULT_WISH = (
    "A geometry-readable orthodox chess set that turns six Ho Chi Minh City "
    "landmarks into a complete 32-piece skyline, with round River and square "
    "Grid plinths distinguishing the two sides without relying on color."
)
MODELS = ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")
REASONING_EFFORTS = ("low", "medium", "high", "xhigh")


def arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run only Workshop Invent (including Concept) and Make for one fixed "
            "Wish. The run uses real native Codex and deterministic host gates, "
            "then stops before Release or publication."
        )
    )
    parser.add_argument(
        "wish",
        nargs="?",
        default=DEFAULT_WISH,
        help="fixed Wish text (defaults to the Ho Chi Minh City landmark chess set)",
    )
    parser.add_argument("--model", choices=MODELS, default="gpt-5.6-sol")
    parser.add_argument(
        "--effort",
        dest="reasoning_effort",
        choices=REASONING_EFFORTS,
        default="medium",
        help="Codex reasoning effort (default: medium)",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=4,
        metavar="N",
        help="bounded Invent/Make revision budget (default: 4)",
    )
    parser.add_argument(
        "--stop-after",
        choices=("concept", "make"),
        default="make",
        help="last phase to execute for a new test (default: make)",
    )
    parser.add_argument(
        "--resume",
        metavar="PRODUCT_ID",
        help="resume an existing focused test with its frozen model and effort",
    )
    parser.add_argument("--json", action="store_true", help="emit one JSON receipt")
    return parser.parse_args(argv)


def _activity(value: str) -> None:
    print("phase test: %s" % value, file=sys.stderr, flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    options = arguments(argv)
    if not 1 <= options.max_rounds <= 100:
        print("--max-rounds must be from 1 through 100", file=sys.stderr)
        return 2
    try:
        if options.resume:
            receipt = resume_native_phase_test(
                options.resume,
                activity_observer=_activity,
            )
        else:
            wish = Wish.create(
                generate_wish_id(),
                options.wish,
                context={"source": "invent-make-phase-test"},
            )
            receipt = start_native_phase_test(
                wish,
                model=options.model,
                reasoning_effort=options.reasoning_effort,
                stop_after=options.stop_after,
                max_rounds=options.max_rounds,
                activity_observer=_activity,
            )
    except (WorkshopError, RuntimeError, ValueError) as exc:
        print("Invent/Make phase test failed: %s" % exc, file=sys.stderr)
        return 1

    product_id = str(receipt["product_id"])
    paths = native_run_paths(product_id)
    output = {
        **receipt,
        "workspace": str(paths.workspace),
        "host_state": str(paths.host_state),
    }
    if options.json:
        print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    else:
        phase = output["phase_test"]
        print("Invent/Make phase test: %s" % phase["status"])
        print("Wish: %s" % product_id)
        print("Model: %s" % phase["model"])
        print("Reasoning effort: %s" % phase["reasoning_effort"])
        print("Stopped after: %s" % phase["stop_after"])
        print("Completed stages: %s" % ", ".join(phase["completed_stages"]))
        print("Workspace: %s" % paths.workspace)
        if phase["status"] != "complete":
            print("Resume: %s --resume %s" % (Path(__file__).name, product_id))
    if output["phase_test"]["status"] == "complete":
        return 0
    return 2 if output["status"] == "waiting" else 1


if __name__ == "__main__":
    raise SystemExit(main())
