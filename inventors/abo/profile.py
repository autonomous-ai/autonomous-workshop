#!/usr/bin/env python3
"""Abstract Boardgame Oracle's invented-games Workshop profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from inventor_workshop.make import Wish
from inventor_workshop.workshop import Workshop, WorkshopTools

from concept import AboConcept
from make import AboMake
from playtest_job import AboPlaytest, abo_playtest


INVENTOR_ROOT = Path(__file__).resolve().parent
LANE = "invented-games"
PROFILE = {
    "schema_version": 1,
    "inventor_id": "abo",
    "lane": LANE,
    "customization": "custom-Concept+Make+Playtest",
    "workshop_level": "custom-playtest",
    "concept": "ABO-owned: invents the game, seals the rules with the pixels",
    "make": "ABO-owned: compiles the sealed rules and builds STEP-first CAD",
    "playtest": "ABO-owned: seeded simulation connected; three results still waiting",
    "engine_protocol": "the imported harness contract, not gameplay.py's",
    "release_gate": "1,000 completed seeded games across four player styles",
}


def create_wish(product_id: str, objective: str) -> Wish:
    return Wish.create(
        product_id,
        objective,
        constraints={"lane": LANE, "audience": "grown-ups-14-plus"},
        context={"inventor_id": "abo"},
    )


def build_workshop(
    *,
    tools: Optional[WorkshopTools] = None,
    concept_artist=None,
    explode_inspector=None,
    game_inventor=None,
    engine_compiler=None,
    cad_builder=None,
    simulation_settings=None,
    make=None,
    playtest=None,
    runtime_root: Optional[Path] = None,
    max_rounds: int = 4,
) -> Workshop:
    """Wire ABO's Concept hook and its two seams.

    The shared capabilities Concept needs — the image provider and the
    exploded-view check — are installed the same way they are for every other
    inventor. What ABO adds is the game inventor behind them, because for an
    abstract game there is nothing to draw until the game exists.
    """

    return Workshop(
        INVENTOR_ROOT,
        LANE,
        tools=tools,
        concept=AboConcept(concept_artist, explode_inspector, game_inventor),
        make=AboMake(engine_compiler, cad_builder) if make is None else make,
        playtest=(
            AboPlaytest(simulation_settings=simulation_settings)
            if playtest is None
            else playtest
        ),
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
        "next_need": "ABO's agent-playtest and manufacturing adapters over the imported harness",
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
            result = workshop.run(wish, playtest_rounds=args.playtest_rounds).to_dict()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
