#!/usr/bin/env python3
"""Ivy's taste-only holdable-science Workshop profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from inventor_workshop.make import Wish
from inventor_workshop.workshop import Workshop, WorkshopTools


INVENTOR_ROOT = Path(__file__).resolve().parent
LANE = "holdable-science"
PROFILE = {
    "schema_version": 1,
    "inventor_id": "ivy",
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
        context={"inventor_id": "ivy"},
    )


def build_workshop(
    *,
    tools: Optional[WorkshopTools] = None,
    runtime_root: Optional[Path] = None,
    max_rounds: int = 4,
) -> Workshop:
    return Workshop(
        INVENTOR_ROOT,
        LANE,
        tools=tools,
        runtime_root=runtime_root,
        max_rounds=max_rounds,
    )


def describe() -> dict:
    workshop = build_workshop()
    return {
        **PROFILE,
        "taste_sha256": workshop.taste.sha256,
        "blueprint_sha256": workshop.blueprint.sha256,
        "adapter_status": "shared Workshop tools required",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", nargs="?", default="profile", choices=("profile", "wish", "preview", "run")
    )
    parser.add_argument("product_id", nargs="?")
    parser.add_argument("objective", nargs="?")
    parser.add_argument("--playtest-rounds", type=int)
    args = parser.parse_args(argv)
    if args.command == "profile":
        if args.playtest_rounds is not None:
            parser.error("--playtest-rounds belongs to run, not profile")
        result = describe()
    else:
        if not args.product_id or not args.objective:
            parser.error("%s requires product_id and a quoted objective" % args.command)
        wish = create_wish(args.product_id, args.objective)
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
