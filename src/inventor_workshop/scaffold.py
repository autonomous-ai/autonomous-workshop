"""Create a thin inventor profile on top of the shared Toy Workshop."""

from __future__ import annotations

import json
import keyword
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional

from .errors import ContractError, StateConflict
from .toys import PLAYTHING_LANES, WORKSHOP_JOBS
from .workshop import CUSTOMIZATION_LEVELS


_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
_RESERVED_PACKAGES = frozenset(
    ("inventor_core", "inventor_foundation", "inventor_workshop", "test", "tests")
)

# Accepted only for old automation. New callers choose an explicit toy lane.
_LEGACY_TEMPLATES = {
    "board-game": "invented-games",
    "physical-product": "moving-machines",
    "custom": "little-worlds",
}

_LANE_GUIDANCE = {
    "classics-made-yours": (
        "Begin with a public-domain or properly licensed classic whose rules are "
        "already known. The invention is the Wish-shaped physical set—its pieces, "
        "board, materials, story, and personal details—not unnecessary rules churn."
    ),
    "invented-games": (
        "Invented games are experimental rules craft. Make the rules complete and "
        "executable, then Playtest at least 1,000 seeded games with optimizing, "
        "social, exploratory, and adversarial AI players. Customer reactions arrive "
        "after Deliver as Reviews and may improve a future Make."
    ),
    "moving-machines": (
        "Make motion the magic: one legible mechanism should invite a hand, reward "
        "repetition, and feel better in the exact printed object than in a render."
    ),
    "holdable-science": (
        "Turn a real mathematical or scientific phenomenon into something a person "
        "can hold, manipulate, and understand through physical cause and effect."
    ),
    "little-worlds": (
        "Build a specific character, scene, vehicle, or tiny world whose geometry "
        "carries the person's Wish instead of resembling a generic collectible."
    ),
}


def _display_text(value: str, label: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ContractError("inventor %s must be a string" % label)
    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in normalized)
    ):
        raise ContractError(
            "inventor %s must be one control-free line of at most %d characters"
            % (label, maximum)
        )
    return normalized


def _hook_source(level: str) -> Optional[str]:
    if level == "taste-only":
        return None
    make_hook = '''"""The creative seams this inventor chooses to own.

Return exact Workshop records when the implementation is ready. Until then,
waiting is honest: never invent CAD, print, or play evidence.
"""

from inventor_workshop import Made, MakeContext, Need, WaitingFor


def make(context: MakeContext) -> Made:
    """Replace this wait with this inventor's artifact-producing Make."""

    # The trusted checkout/tier supplies this per-Wish allowance. Custom Make
    # receives it on every round; never infer or increase it from Wish text.
    playtest_rounds = context.playtest_rounds
    del playtest_rounds
    raise WaitingFor(
        Need(
            "make",
            "inventor-make",
            "This inventor's custom Make has not been connected yet.",
            "Implement make(context) and return a Made record bound to exact artifact bytes.",
        )
    )
'''
    if level == "custom-make":
        return make_hook
    return make_hook + '''

from inventor_workshop import PlaytestContext, Playtested


def playtest(context: PlaytestContext) -> Playtested:
    """Replace this wait with this inventor's evidence-producing Playtest."""

    # This is the same trusted per-Wish allowance received by custom Make.
    playtest_rounds = context.playtest_rounds
    del playtest_rounds
    raise WaitingFor(
        Need(
            "playtest",
            "inventor-playtest",
            "This inventor's custom Playtest has not been connected yet.",
            "Implement playtest(context) and return Playtested evidence for the exact Make.",
        )
    )
'''


def _files(
    inventor_id: str,
    name: str,
    niche: str,
    lane: str,
    level: str,
) -> Dict[str, str]:
    package = inventor_id.replace("-", "_")
    env = inventor_id.upper().replace("-", "_")
    lane_guidance = _LANE_GUIDANCE[lane]
    capabilities = [*WORKSHOP_JOBS, lane, level]
    manifest = {
        "schema_version": 5,
        "id": inventor_id,
        "status": "experimental",
        "entrypoint": ["python3", "-m", package],
        "capabilities": capabilities,
        "checks": [
            [
                "python3",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-p",
                "test_*.py",
                "-v",
            ]
        ],
        "source": {"kind": "local"},
    }

    ownership = {
        "taste-only": (
            "This inventor owns only `TASTE.md`. Workshop supplies Make, Playtest, "
            "Instructions, Deliver, the improvement loop, and durable state."
        ),
        "custom-make": (
            "This inventor owns `TASTE.md` and `inventor.py:make`. Workshop supplies "
            "Playtest, Instructions, Deliver, the improvement loop, and durable state."
        ),
        "custom-playtest": (
            "This inventor owns `TASTE.md`, `inventor.py:make`, and "
            "`inventor.py:playtest`. Workshop still owns the loop, Instructions, Deliver, "
            "artifact identity, and durable state."
        ),
    }[level]
    hook_step = {
        "taste-only": (
            "2. Configure shared `WorkshopTools` once for every inventor; do not copy a "
            "Make or Playtest harness into this folder."
        ),
        "custom-make": (
            "2. Implement the typed `make(context)` seam in `src/%s/inventor.py`."
            % package
        ),
        "custom-playtest": (
            "2. Implement the typed `make(context)` and `playtest(context)` seams "
            "in `src/%s/inventor.py`." % package
        ),
    }[level]

    custom_import = {
        "taste-only": "CUSTOM_MAKE = None\nCUSTOM_PLAYTEST = None",
        "custom-make": (
            "from .inventor import make as CUSTOM_MAKE\n\nCUSTOM_PLAYTEST = None"
        ),
        "custom-playtest": (
            "from .inventor import make as CUSTOM_MAKE\n"
            "from .inventor import playtest as CUSTOM_PLAYTEST"
        ),
    }[level]

    files = {
        "inventor.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        "TASTE.md": """---
name: {name_header}
description: {description_header}
---
# {name}'s Taste

This is {name}'s creative constitution for the **{lane}** lane. Humans own
changes to Taste. The inventor may propose revisions from verified outcomes, but it
must not silently rewrite what it values.

## North star

Create {niche} for grown-ups (14+) that invite play, surprise, and return
visits. Nothing may be merely useful: a useful Wish receives the playful version.

## The product bar

The finished object must answer: **why couldn't someone have bought this
before this Wish?** The Wish must materially shape its geometry, mechanism,
rules, secret, or little world. Reject generic figurines, stock-like trinkets,
and anything that is effectively the same object for everyone. The standard
is simple: **I couldn't have bought it before this Wish.**

## Lane promise

{lane_guidance}

## Starting preferences

- Cool beats cute. Charm is welcome only when the idea is specific and surprising.
- Give every object one clear signature interaction, character, or secret.
- Prefer a recognizable silhouette and satisfying physical behavior over ornament.
- Make the first delightful moment easy to discover without coaching.
- Treat printability, assembly, safety, and truthful presentation as part of beauty.
- Let artifact-bound Playtest evidence improve the product without averaging away
  this inventor's point of view.

## Define before autonomous release

- Which three qualities should make this inventor's work recognizable without a logo?
- Which familiar themes, shapes, mechanics, or gimmicks are instant rejects?
- What should a person feel in the first ten seconds and on the tenth play?
- What physical and human evidence is strong enough to change this Taste?
""".format(
            name=name,
            name_header=json.dumps(name, ensure_ascii=False),
            niche=niche,
            description_header=json.dumps(niche, ensure_ascii=False),
            lane=lane,
            lane_guidance=lane_guidance,
        ),
        "README.md": """# {name}

{name} is the **{lane}** inventor for **{niche}**. {ownership}

This Workshop makes physical magic, not a catalog of generic prints. Every Make
must clear the product bar: the exact object couldn't have been bought
before this Wish. Cool beats cute, and Wish-shaped substance beats decoration.
No generic, off-the-shelf prints.

**Lane promise:** {lane_guidance}

```text
Wish -> Invent -> Make <-> Playtest -> Instructions -> Deliver
          ^          |
          + feedback +
```

## Make this inventor yours

1. Turn [`TASTE.md`](TASTE.md) into a recognizable point of view.
{hook_step}
3. Keep missing model, CAD, physical, human, media, production, and carrier
   capabilities as explicit waits. Never turn a preview into production proof.

## Try the profile

Generated inventors use the installable `{package}` module for their profile entrypoint,
so the manifest, source checkout, and built package all run the same thin wrapper.

```bash
python3 -m pip install -e ../.. -e .
{package} profile
{package} wish first-toy "I wish for a small surprise on my desk"
{package} preview first-toy "I wish for a small surprise on my desk"
{package} run --playtest-rounds 4 first-toy "I wish for a small surprise on my desk"
workshop check . --run
```

`preview` is read-only and shows the exact Wish-, Taste-, and lane-bound brief.
`run` uses `Workshop` and `WorkshopTools`; an unconfigured capability returns a
typed `waiting` result instead of pretending a product was made or tested.
The trusted checkout or product tier supplies `--playtest-rounds` for each Wish;
it is an allowance from 1 to 100, not a value the Wish or inventor may raise.
Runtime state and credentials stay in `.workshop/` and are never committed.
""".format(
            name=name,
            niche=niche,
            lane=lane,
            ownership=ownership,
            hook_step=hook_step,
            lane_guidance=lane_guidance,
            package=package,
        ),
        ".gitignore": ".workshop/\n__pycache__/\n*.py[cod]\n",
        "pyproject.toml": """[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "inventor-{inventor_id}"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = ["inventor-workshop>=0.5,<0.6"]

[project.scripts]
{package} = "{package}.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]
""".format(inventor_id=inventor_id, package=package),
        "MANIFEST.in": "include inventor.json TASTE.md\n",
        "setup.py": """from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        super().run()
        project = Path(__file__).resolve().parent
        destination = Path(self.build_lib) / "{package}" / "_identity"
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        for filename in ("inventor.json", "TASTE.md"):
            shutil.copy2(project / filename, destination / filename)


setup(cmdclass={{"build_py": build_py}})
""".format(package=package),
        "src/{package}/__init__.py".format(package=package): (
            repr("%s: a %s inventor built on the shared Toy Workshop." % (name, lane))
            + "\n"
        ),
        "src/{package}/__main__.py".format(package=package): """import argparse
import json
import os
import sysconfig
from pathlib import Path
from typing import Optional

from inventor_workshop import WORKSHOP_JOBS, Wish, Workshop, WorkshopTools
from inventor_workshop.agent_invent import configured_workshop_tools
from inventor_workshop.make import generate_wish_id

{custom_import}


INVENTOR_ID = {inventor_id_literal}
LANE = {lane_literal}
DECLARED_LEVEL = {level_literal}


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
    configured = os.environ.get("{env}_RUNTIME")
    if configured:
        root = Path(configured).expanduser()
        if not root.is_absolute():
            raise ValueError("{env}_RUNTIME must be an absolute path")
        return root
    identity = inventor_root()
    if (identity / "pyproject.toml").is_file():
        return identity / ".workshop"
    return Path.home() / ".local" / "share" / "autonomous-workshop" / INVENTOR_ID


def create_wish(product_id: str, objective: str) -> Wish:
    return Wish.create(
        product_id,
        objective,
        constraints={{"lane": LANE, "audience": "grown-ups-14-plus"}},
        context={{"inventor_id": INVENTOR_ID}},
    )


def build_workshop(
    *,
    tools: Optional[WorkshopTools] = None,
    runtime_root: Optional[Path] = None,
    max_rounds: int = 4,
) -> Workshop:
    return Workshop(
        inventor_root(),
        LANE,
        tools=configured_workshop_tools(tools),
        make=CUSTOM_MAKE,
        playtest=CUSTOM_PLAYTEST,
        runtime_root=runtime_root if runtime_root is not None else default_runtime_root(),
        max_rounds=max_rounds,
    )


def describe():
    workshop = build_workshop()
    return {{
        "schema_version": 1,
        "inventor_id": INVENTOR_ID,
        "lane": workshop.lane,
        "customization_level": workshop.customization_level,
        "jobs": list(WORKSHOP_JOBS),
        "taste_sha256": workshop.taste.sha256,
        "blueprint_sha256": workshop.blueprint.sha256,
        "production_ready": False,
        "default_behavior": "preview is read-only; run waits for every missing capability",
    }}


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
""".format(
            custom_import=custom_import,
            env=env,
            inventor_id_literal=repr(inventor_id),
            lane_literal=repr(lane),
            level_literal=repr(level),
        ),
        "tests/test_smoke.py": """import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from inventor_workshop import WORKSHOP_JOBS, Workshop, WorkshopTools, load_taste
from {package}.__main__ import (
    build_workshop,
    create_wish,
    default_runtime_root,
    main,
)


class SmokeTest(unittest.TestCase):
    def test_profile_is_a_thin_workshop_configuration(self):
        workshop = build_workshop(tools=WorkshopTools())
        self.assertIsInstance(workshop, Workshop)
        self.assertEqual(workshop.lane, {lane_literal})
        self.assertEqual(workshop.customization_level, {level_literal})
        self.assertEqual(
            tuple(WORKSHOP_JOBS),
            ("wish", "invent", "make", "playtest", "instructions", "deliver"),
        )
        profile = load_taste(Path(__file__).resolve().parents[1])
        self.assertIn("creative constitution", profile.content)

    def test_preview_is_read_only_and_run_waits_truthfully(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "workshop"
            with mock.patch.dict(os.environ, {{"{env}_RUNTIME": str(runtime)}}):
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(
                        main(("preview", "first-toy", "I wish for a tiny surprise")),
                        0,
                    )
                preview = json.loads(output.getvalue())
                self.assertEqual(preview["blueprint"]["lane"], {lane_literal})
                self.assertFalse(runtime.exists())

                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(
                        main((
                            "run",
                            "--playtest-rounds",
                            "2",
                            "waiting-toy",
                            "I wish for a tiny surprise",
                        )),
                        0,
                    )
                result = json.loads(output.getvalue())
                self.assertEqual(result["status"], "waiting")
                self.assertEqual(result["job"], "invent")
                self.assertEqual(result["playtest_rounds"], 2)
                self.assertIsNone(result["artifact_sha256"])
                self.assertTrue(result["needs"])
                self.assertTrue((default_runtime_root() / "workshop.sqlite3").is_file())

    def test_wish_keeps_the_persons_words_and_lane(self):
        wish = create_wish("joy", "I wish my cable holder could make me laugh")
        self.assertEqual(wish.objective, "I wish my cable holder could make me laugh")
        self.assertEqual(wish.constraints["lane"], {lane_literal})


if __name__ == "__main__":
    unittest.main()
""".format(
            env=env,
            lane_literal=repr(lane),
            level_literal=repr(level),
            package=package,
        ),
    }
    hook = _hook_source(level)
    if hook is not None:
        files["src/{package}/inventor.py".format(package=package)] = hook
    return files


def scaffold_inventor(
    root: Path,
    inventor_id: str,
    name: str,
    niche: str,
    *,
    lane: Optional[str] = None,
    level: str = "taste-only",
    template: Optional[str] = None,
) -> Path:
    """Compatibility wrapper for the former ``workshop new`` command."""

    Path(root).mkdir(parents=True, exist_ok=True)
    return create_inventor(
        root,
        inventor_id,
        name,
        niche,
        lane=lane,
        level=level,
        template=template,
        run_checks=False,
    )


def prepare_inventor_collection(root: Path) -> Path:
    """Return ``inventors/`` for creation, bootstrapping it when needed.

    A path already named ``inventors`` is treated as the collection itself.
    Every other existing directory is treated as a repository/workspace root.
    """

    requested = Path(root)
    if requested.is_symlink():
        raise ContractError("inventor creation root must not be a symlink: %s" % requested)
    try:
        resolved = requested.resolve(strict=True)
    except OSError as exc:
        raise ContractError("inventor creation root must already exist: %s" % requested) from exc
    if not resolved.is_dir():
        raise ContractError("inventor creation root must be a directory: %s" % resolved)
    collection = resolved if resolved.name == "inventors" else resolved / "inventors"
    if collection.is_symlink():
        raise ContractError("inventors collection must not be a symlink: %s" % collection)
    if collection.exists() and not collection.is_dir():
        raise ContractError("inventors collection must be a directory: %s" % collection)
    collection.mkdir(mode=0o755, exist_ok=True)
    return collection.resolve(strict=True)


def create_inventor(
    root: Path,
    inventor_id: str,
    name: str,
    description: str,
    *,
    lane: Optional[str] = None,
    level: str = "taste-only",
    template: Optional[str] = None,
    run_checks: bool = True,
) -> Path:
    """Create and validate one inventor before atomically joining the catalog."""

    requested_root = Path(root)
    if requested_root.is_symlink():
        raise ContractError("inventor collection must not be a symlink: %s" % requested_root)
    try:
        root = requested_root.resolve(strict=True)
    except OSError as exc:
        raise ContractError("inventor collection must already exist: %s" % requested_root) from exc
    if not root.is_dir():
        raise ContractError("inventor collection must be a directory: %s" % root)
    if not _ID.fullmatch(inventor_id):
        raise ContractError("inventor id must match %s" % _ID.pattern)
    package = inventor_id.replace("-", "_")
    if keyword.iskeyword(package) or package in _RESERVED_PACKAGES:
        raise ContractError("inventor id maps to a reserved Python package name")
    name = _display_text(name, "name", 200)
    description = _display_text(description, "description", 500)
    if type(run_checks) is not bool:
        raise ContractError("run_checks must be a boolean")
    if template is not None:
        if template not in _LEGACY_TEMPLATES:
            raise ContractError(
                "legacy inventor template must be one of %s"
                % sorted(_LEGACY_TEMPLATES)
            )
        legacy_lane = _LEGACY_TEMPLATES[template]
        if lane is not None and lane != legacy_lane:
            raise ContractError("--lane conflicts with legacy --template")
        lane = legacy_lane
    if lane not in PLAYTHING_LANES:
        raise ContractError(
            "inventor lane must be one of %s" % ", ".join(PLAYTHING_LANES)
        )
    if level not in CUSTOMIZATION_LEVELS:
        raise ContractError(
            "inventor level must be one of %s" % ", ".join(CUSTOMIZATION_LEVELS)
        )

    destination = root / inventor_id
    if destination.exists():
        raise StateConflict("inventor folder already exists: %s" % destination)

    # Refuse to add one good profile to a catalog that is already malformed.
    # This prevents a successful-looking creation receipt for a Manager catalog
    # that cannot actually be searched.
    has_existing_profile = any(
        child.is_symlink()
        or (
            child.is_dir()
            and (
                (child / "inventor.json").exists()
                or (child / "TASTE.md").exists()
            )
        )
        for child in root.iterdir()
    )
    if has_existing_profile:
        from .manager import discover_inventor_catalog

        discover_inventor_catalog(root)

    staging_root = Path(tempfile.mkdtemp(prefix=".%s." % inventor_id, dir=str(root)))
    temporary = staging_root / inventor_id
    temporary.mkdir(mode=0o755)
    try:
        for relative, content in _files(
            inventor_id, name, description, lane, level
        ).items():
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        # Validate exactly the folder that will be made visible. Declared smoke
        # checks run in staging, so failure leaves no half-created inventor.
        from .contribution import run_declared_checks, validate_contribution
        from .manifest import load_manifest
        from .taste import load_taste

        manifest = load_manifest(temporary / "inventor.json")
        problems = validate_contribution(manifest)
        load_taste(temporary)
        if not problems and run_checks:
            problems = run_declared_checks(manifest)
        if problems:
            raise ContractError("inventor creation failed validation: %s" % "; ".join(problems))

        # The staged collection must be Manager-discoverable before publication.
        from .manager import discover_inventor_catalog

        staged_catalog = discover_inventor_catalog(staging_root)
        if not staged_catalog.card(inventor_id).routable:
            raise ContractError("created inventor is not routable")
        os.replace(str(temporary), str(destination))
    finally:
        if staging_root.exists():
            shutil.rmtree(str(staging_root))
    return destination


__all__ = [
    "create_inventor",
    "prepare_inventor_collection",
    "scaffold_inventor",
]
