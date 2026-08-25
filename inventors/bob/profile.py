#!/usr/bin/env python3
"""Bob's thin, canonical moving-machines Workshop profile.

Bob reserves a custom Make seam. The preserved board-game harness is unrelated
to that typed seam and is never installed automatically.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from inventor_workshop.jobs import Need, WaitingFor
from inventor_workshop.make import Wish, generate_wish_id
from inventor_workshop.agent_invent import configured_workshop_tools
from inventor_workshop.workshop import Workshop, WorkshopTools


INVENTOR_ROOT = Path(__file__).resolve().parent
LANE = "moving-machines"
PROFILE = {
    "schema_version": 1,
    "inventor_id": "bob",
    "lane": LANE,
    "customization": "custom-Make",
    "workshop_level": "custom-make",
    "make": "Bob-owned typed waiting seam",
    "playtest": "Workshop default",
}


def bob_make(context):
    """Typed fail-closed seam for Bob's not-yet-written machine Make."""

    del context
    raise WaitingFor(
        Need(
            "make",
            "bob-moving-machine-make",
            "Bob owns moving-machine Make, but no typed implementation exists yet.",
            "Implement MakeContext -> Made for kinetic mechanisms; never route this Wish into bob.py's board-game harness.",
        )
    )


def create_wish(product_id: str, objective: str) -> Wish:
    return Wish.create(
        product_id,
        objective,
        constraints={"lane": LANE, "audience": "grown-ups-14-plus"},
        context={"inventor_id": "bob"},
    )


def describe() -> dict:
    workshop = build_workshop()
    return {
        **PROFILE,
        "taste_sha256": workshop.taste.sha256,
        "blueprint_sha256": workshop.blueprint.sha256,
        "adapter_status": "waiting",
        "next_need": "typed implementation for Bob's custom moving-machine Make",
    }


def build_workshop(
    *,
    tools: Optional[WorkshopTools] = None,
    make=None,
    runtime_root: Optional[Path] = None,
    max_rounds: int = 4,
) -> Workshop:
    """Install Bob's reviewed moving-machine Make and shared Playtest."""

    return Workshop(
        INVENTOR_ROOT,
        LANE,
        tools=configured_workshop_tools(tools),
        make=bob_make if make is None else make,
        runtime_root=runtime_root,
        max_rounds=max_rounds,
    )


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
        if not args.product_id:
            parser.error("%s requires a quoted Wish" % args.command)
        product_id, objective = (
            (generate_wish_id(), args.product_id)
            if args.objective is None
            else (args.product_id, args.objective)
        )
        wish = create_wish(product_id, objective)
        if args.command == "wish":
            if args.playtest_rounds is not None:
                parser.error("--playtest-rounds belongs to run, not the Wish")
            result = wish.to_dict()
        elif args.command == "preview":
            if args.playtest_rounds is not None:
                parser.error("--playtest-rounds belongs to run, not preview")
            result = build_workshop().preview(wish)
        else:
            result = build_workshop().run(
                wish, playtest_rounds=args.playtest_rounds
            ).to_dict()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
