#!/usr/bin/env python3
"""Leo's canonical invented-games Workshop profile."""

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
LANE = "invented-games"
PROFILE = {
    "schema_version": 1,
    "inventor_id": "leo",
    "lane": LANE,
    "customization": "custom-Make+Playtest",
    "workshop_level": "custom-playtest",
    "make": "Leo-owned typed waiting seam",
    "playtest": "Leo-owned typed waiting seam",
    "release_gate": "1,000 seeded AI games across four player styles",
}


def leo_make(context):
    """Typed fail-closed seam for Leo's not-yet-written custom Make."""

    del context
    raise WaitingFor(
        Need(
            "make",
            "leo-custom-make-adapter",
            "Leo owns invented-game Make, but no implementation returns Workshop Made records yet.",
            "Implement Leo's candidates, rules, CAD, and artifacts as MakeContext -> Made.",
        )
    )


def leo_playtest(context):
    """Typed fail-closed seam for Leo's custom AI-player Playtest."""

    del context
    raise WaitingFor(
        Need(
            "playtest",
            "leo-custom-playtest-adapter",
            "Leo owns invented-game Playtest, but no implementation returns Workshop Playtested records yet.",
            "Bind Leo's exact game evidence and feedback from PlaytestContext to Playtested.",
        ),
    )


def create_wish(product_id: str, objective: str) -> Wish:
    return Wish.create(
        product_id,
        objective,
        constraints={"lane": LANE, "audience": "grown-ups-14-plus"},
        context={"inventor_id": "leo"},
    )


def build_workshop(
    *,
    tools: Optional[WorkshopTools] = None,
    make=None,
    playtest=None,
    runtime_root: Optional[Path] = None,
    max_rounds: int = 4,
) -> Workshop:
    return Workshop(
        INVENTOR_ROOT,
        LANE,
        tools=configured_workshop_tools(tools),
        make=leo_make if make is None else make,
        playtest=leo_playtest if playtest is None else playtest,
        runtime_root=runtime_root,
        max_rounds=max_rounds,
    )


def describe() -> dict:
    workshop = build_workshop()
    return {
        **PROFILE,
        "taste_sha256": workshop.taste.sha256,
        "blueprint_sha256": workshop.blueprint.sha256,
        "adapter_status": "waiting",
        "next_need": "typed implementations for Leo's custom Make and Playtest",
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
