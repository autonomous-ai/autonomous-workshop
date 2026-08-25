#!/usr/bin/env python3
"""Eve's taste-only personalized little-worlds Workshop profile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from inventor_workshop.make import Wish, generate_wish_id
from inventor_workshop.agent_invent import configured_workshop_tools
from inventor_workshop.handoff import (
    bind_manager_assignment_result,
    read_manager_assignment,
)
from inventor_workshop.workshop import Workshop, WorkshopTools


INVENTOR_ROOT = Path(__file__).resolve().parent
LANE = "little-worlds"
PROFILE = {
    "schema_version": 1,
    "inventor_id": "eve",
    "lane": LANE,
    "customization": "taste-only",
    "workshop_level": "taste-only",
    "make": "Workshop default",
    "playtest": "Workshop default",
}


def create_wish(product_id: str, objective: str) -> Wish:
    return Wish.create(
        product_id,
        objective,
        constraints={"lane": LANE, "audience": "grown-ups-14-plus"},
        context={"inventor_id": "eve"},
    )


def build_workshop(
    *,
    tools: Optional[WorkshopTools] = None,
    runtime_root: Optional[Path] = None,
    max_rounds: int = 4,
) -> Workshop:
    selected_runtime = runtime_root or (INVENTOR_ROOT / ".workshop")
    return Workshop(
        INVENTOR_ROOT,
        LANE,
        tools=configured_workshop_tools(
            tools, inventor_id="eve", runtime_root=selected_runtime
        ),
        runtime_root=selected_runtime,
        max_rounds=max_rounds,
    )


def describe() -> dict:
    workshop = build_workshop()
    return {
        **PROFILE,
        "taste_sha256": workshop.taste.sha256,
        "blueprint_sha256": workshop.blueprint.sha256,
        "adapter_status": "shared Workshop engine",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", nargs="?", default="profile", choices=("profile", "wish", "preview", "run")
    )
    parser.add_argument("product_id", nargs="?")
    parser.add_argument("objective", nargs="?")
    parser.add_argument("--playtest-rounds", type=int)
    parser.add_argument("--assignment-stdin", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.assignment_stdin:
        if (
            args.command != "run"
            or args.product_id is not None
            or args.objective is not None
            or args.playtest_rounds is not None
        ):
            parser.error("--assignment-stdin is an internal run-only handoff")
        handoff = read_manager_assignment(sys.stdin, expected_inventor_id="eve")
        result = bind_manager_assignment_result(
            build_workshop().run(
                handoff.wish, playtest_rounds=handoff.playtest_rounds
            ).to_dict(),
            handoff,
        )
    elif args.command == "profile":
        if args.playtest_rounds is not None:
            parser.error("--playtest-rounds belongs to run, not profile")
        result = describe()
    else:
        if not args.product_id:
            parser.error("%s requires a quoted Wish" % args.command)
        product_id, objective = (
            (generate_wish_id(), args.product_id)
            if args.objective is None
            else (args.product_id, args.objective)
        )
        wish = create_wish(product_id, objective)
        workshop = build_workshop()
        if args.command == "wish":
            if args.playtest_rounds is not None:
                parser.error("--playtest-rounds belongs to run, not the Wish")
            result = wish.to_dict()
        elif args.command == "preview":
            if args.playtest_rounds is not None:
                parser.error("--playtest-rounds belongs to run, not preview")
            result = workshop.preview(wish)
        else:
            result = workshop.run(
                wish, playtest_rounds=args.playtest_rounds
            ).to_dict()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
