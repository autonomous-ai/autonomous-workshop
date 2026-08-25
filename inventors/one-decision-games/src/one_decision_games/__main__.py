import argparse
import json
import os
import sysconfig
from pathlib import Path
from typing import Optional

from inventor_workshop import WORKSHOP_JOBS, Wish, Workshop, WorkshopTools
from inventor_workshop.agent_invent import configured_workshop_tools

from .inventor import make as CUSTOM_MAKE
from .inventor import playtest as CUSTOM_PLAYTEST


INVENTOR_ID = 'one-decision-games'
LANE = 'invented-games'
DECLARED_LEVEL = 'custom-playtest'


def inventor_root() -> Path:
    package_file = Path(__file__).resolve()
    packaged = package_file.parent / "_identity"
    if (packaged / "inventor.json").is_file() and (packaged / "TASTE.md").is_file():
        return packaged.resolve()
    root = next(
        (parent for parent in package_file.parents if (parent / "inventor.json").is_file()),
        None,
    )
    if root is None:
        installed = Path(sysconfig.get_path("data")) / "share" / "autonomous-workshop" / INVENTOR_ID
        if (installed / "inventor.json").is_file() and (installed / "TASTE.md").is_file():
            return installed.resolve()
        raise RuntimeError("cannot locate this inventor's installed identity")
    return root.resolve()


def default_runtime_root() -> Path:
    configured = os.environ.get("ONE_DECISION_GAMES_RUNTIME")
    if configured:
        root = Path(configured).expanduser()
        if not root.is_absolute():
            raise ValueError("ONE_DECISION_GAMES_RUNTIME must be an absolute path")
        return root
    identity = inventor_root()
    if (identity / "pyproject.toml").is_file():
        return identity / ".workshop"
    return Path.home() / ".local" / "share" / "autonomous-workshop" / INVENTOR_ID


def create_wish(product_id: str, objective: str) -> Wish:
    return Wish.create(
        product_id,
        objective,
        constraints={"lane": LANE, "audience": "grown-ups-14-plus"},
        context={"inventor_id": INVENTOR_ID},
    )


def build_workshop(
    *,
    tools: Optional[WorkshopTools] = None,
    runtime_root: Optional[Path] = None,
    max_rounds: int = 4,
) -> Workshop:
    selected_runtime = runtime_root if runtime_root is not None else default_runtime_root()
    return Workshop(
        inventor_root(),
        LANE,
        tools=configured_workshop_tools(
            tools,
            inventor_id=INVENTOR_ID,
            runtime_root=selected_runtime,
        ),
        make=CUSTOM_MAKE,
        playtest=CUSTOM_PLAYTEST,
        runtime_root=selected_runtime,
        max_rounds=max_rounds,
    )


def describe():
    workshop = build_workshop()
    return {
        "schema_version": 1,
        "inventor_id": INVENTOR_ID,
        "lane": workshop.lane,
        "customization_level": workshop.customization_level,
        "jobs": list(WORKSHOP_JOBS),
        "taste_sha256": workshop.taste.sha256,
        "blueprint_sha256": workshop.blueprint.sha256,
        "production_ready": False,
        "default_behavior": "preview is read-only; run waits for every missing capability",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        nargs="?",
        default="profile",
        choices=("profile", "wish", "preview", "run"),
    )
    parser.add_argument("product_id", nargs="?")
    parser.add_argument("objective", nargs="?")
    parser.add_argument(
        "--playtest-rounds",
        type=int,
        choices=range(1, 101),
        metavar="N",
        help="trusted per-Wish Playtest allowance (1-100; run only)",
    )
    args = parser.parse_args(argv)
    if args.command == "profile":
        if args.playtest_rounds is not None:
            parser.error("--playtest-rounds belongs to run, not profile")
        result = describe()
    else:
        if not args.product_id or not args.objective:
            parser.error("%s requires product_id and a quoted Wish" % args.command)
        wish = create_wish(args.product_id, args.objective)
        if args.command == "wish":
            if args.playtest_rounds is not None:
                parser.error("--playtest-rounds belongs to run, not the Wish")
            result = wish.to_dict()
        else:
            workshop = build_workshop()
            if args.command == "preview":
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
