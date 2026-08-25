"""Create a thin inventor profile on top of the shared Toy Workshop."""

from __future__ import annotations

import json
import keyword
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional

from .errors import ContractError, StateConflict
from .toys import PLAYTHING_LANES, WORKSHOP_JOBS
from .workshop import CUSTOMIZATION_LEVELS


_ID = re.compile(r"^(?=.{2,63}$)[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
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


def _rpc_hook_source(level: str, package: str) -> Optional[str]:
    """Return the stage-only child executable for declared custom seams."""

    if level == "taste-only":
        return None
    imports = "from %s.inventor import make" % package
    arguments = "make=make"
    if level == "custom-playtest":
        imports += ", playtest"
        arguments += ", playtest=playtest"
    return '''"""Bounded custom contribution worker; not the Workshop orchestrator."""

from pathlib import Path

from inventor_workshop.contribution_rpc import contribution_hook_main
{imports}


if __name__ == "__main__":
    raise SystemExit(
        contribution_hook_main(Path(__file__).resolve().parent, {arguments})
    )
'''.format(imports=imports, arguments=arguments)


def _files(
    inventor_id: str,
    name: str,
    niche: str,
    lane: str,
    level: str,
    *,
    taste_content: Optional[str] = None,
) -> Dict[str, str]:
    package = inventor_id.replace("-", "_")
    env = inventor_id.upper().replace("-", "_")
    lane_guidance = _LANE_GUIDANCE[lane]
    # Capabilities describe the Inventor's public lane and chosen override
    # level—not shared intake or engine components inherited automatically.
    capabilities = [lane, level]
    manifest = {
        "schema_version": 5,
        "id": inventor_id,
        "status": "experimental",
        # This local bootstrap works before the generated package is installed.
        # The console script declared below remains the installed-package entrypoint.
        "entrypoint": ["python3", "run.py"],
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
            "This inventor contributes only `TASTE.md`. Workshop supplies Invent, "
            "Make, Playtest, Instructions, Deliver, the improvement loops, and "
            "durable state."
        ),
        "custom-make": (
            "This inventor contributes `TASTE.md` and explicitly overrides Make with "
            "`inventor.py:make`. Workshop supplies Invent, Playtest, Instructions, "
            "Deliver, the improvement loops, and durable state."
        ),
        "custom-playtest": (
            "This inventor contributes `TASTE.md` and explicitly overrides Make and "
            "Playtest with `inventor.py:make` and `inventor.py:playtest`. Workshop "
            "still supplies Invent, the feedback loop, Instructions, Deliver, artifact "
            "identity, and durable state."
        ),
    }[level]
    hook_step = {
        "taste-only": (
            "2. Use the Workshop-owned shared engine; do not copy Invent, "
            "Make, or Playtest machinery into this folder."
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
    identity_files = ["inventor.json", "TASTE.md", "run.py"]
    if level != "taste-only":
        identity_files.append("hook.py")
    identity_files_source = "(" + ", ".join(
        json.dumps(filename) for filename in identity_files
    ) + ")"
    packaged_contribution = ""
    if level != "taste-only":
        packaged_contribution = '''
        contribution = project / "src" / "{package}"
        shutil.copytree(
            contribution,
            destination / "contribution_src" / "{package}",
        )
'''.format(package=package)

    generated_taste = """---
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
    )

    files = {
        "inventor.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        "TASTE.md": generated_taste if taste_content is None else taste_content,
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

## Start inventing

Enter through the Workshop Manager so the exact assignment, durable status,
and safe continuation are all recorded. Python 3.11 or newer is required
because the common Workshop path includes the shared CAD runtime.

```bash
uv run workshop check . --run
uv run workshop wish --root ../.. "I wish for a small surprise on my desk"
```

The Wish ID and Inventor match are automatic. If a real model, CAD, evidence,
Factory, production, or carrier provider is unavailable, that common component
returns a typed `waiting` result instead of pretending the work happened.
Runtime state and credentials stay in `.workshop/` and are never committed.

`python run.py profile` is a local developer check for the thin Inventor
connection; it is not the customer Wish entrance.
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
requires-python = ">=3.11"
dependencies = ["inventor-workshop>=0.5,<0.6"]

[project.scripts]
{package} = "{package}.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]
""".format(inventor_id=inventor_id, package=package),
        "MANIFEST.in": "include %s\n" % " ".join(identity_files),
        "run.py": """\"\"\"Run this Inventor directly from a checkout or installed identity.\"\"\"

from pathlib import Path
import sys


source = Path(__file__).resolve().parent / "src"
if source.is_dir():
    sys.path.insert(0, str(source))

from {package}.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
""".format(package=package),
        "setup.py": """from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        super().run()
        project = Path(__file__).resolve().parent
        destination = (
            Path(self.build_lib) / "{package}" / "_identity" / "{inventor_id}"
        )
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        for filename in {identity_files_source}:
            shutil.copy2(project / filename, destination / filename)
{packaged_contribution}


setup(cmdclass={{"build_py": build_py}})
""".format(
            package=package,
            inventor_id=inventor_id,
            identity_files_source=identity_files_source,
            packaged_contribution=packaged_contribution,
        ),
        "src/{package}/__init__.py".format(package=package): (
            repr("%s: a %s inventor built on the shared Toy Workshop." % (name, lane))
            + "\n"
        ),
        "src/{package}/__main__.py".format(package=package): """import argparse
import json
import os
import sys
import sysconfig
from pathlib import Path
from typing import Optional

from inventor_workshop import WORKSHOP_JOBS, Wish, Workshop
from inventor_workshop.handoff import (
    bind_manager_assignment_result,
    read_manager_assignment,
)
from inventor_workshop.make import generate_wish_id

{custom_import}


INVENTOR_ID = {inventor_id_literal}
LANE = {lane_literal}
DECLARED_LEVEL = {level_literal}


def inventor_root() -> Path:
    package_file = Path(__file__).resolve()
    packaged = package_file.parent / "_identity" / INVENTOR_ID
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
    runtime_root: Optional[Path] = None,
    max_rounds: int = 4,
    world_inputs=None,
    world_evidence=None,
) -> Workshop:
    selected_runtime = runtime_root if runtime_root is not None else default_runtime_root()
    return Workshop(
        inventor_root(),
        LANE,
        make=CUSTOM_MAKE,
        playtest=CUSTOM_PLAYTEST,
        runtime_root=selected_runtime,
        max_rounds=max_rounds,
        world_inputs=world_inputs,
        world_evidence=world_evidence,
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
        choices=("profile", "wish", "preview", "run", "resume"),
        metavar="{{profile,wish,preview,run}}",
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
    parser.add_argument(
        "--assignment-stdin",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_intermixed_args(argv)
    if args.assignment_stdin:
        if (
            args.command not in ("run", "resume")
            or args.product_id is not None
            or args.objective is not None
            or args.playtest_rounds is not None
        ):
            parser.error("--assignment-stdin is an internal Manager handoff")
        handoff = read_manager_assignment(
            sys.stdin, expected_inventor_id=INVENTOR_ID
        )
        identity = inventor_root()
        handoff.assert_inventor_current(identity)
        workshop = build_workshop(
            world_inputs=handoff.world_inputs,
            world_evidence=handoff.world_evidence,
        )
        resumed = (
            workshop.resume(handoff.wish)
            if args.command == "resume"
            else workshop.run(
                handoff.wish, playtest_rounds=handoff.playtest_rounds
            )
        )
        handoff.assert_inventor_current(identity)
        result = bind_manager_assignment_result(
            resumed.to_dict(),
            handoff,
        )
    elif args.command == "resume":
        parser.error("resume is an internal Manager-only action")
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

from inventor_workshop import WORKSHOP_JOBS, Workshop, load_taste
from {package}.__main__ import (
    build_workshop,
    create_wish,
    default_runtime_root,
    main,
)


class SmokeTest(unittest.TestCase):
    def test_profile_is_a_thin_workshop_configuration(self):
        workshop = build_workshop()
        self.assertIsInstance(workshop, Workshop)
        self.assertEqual(workshop.lane, {lane_literal})
        self.assertEqual(workshop.customization_level, {level_literal})
        self.assertEqual(
            tuple(WORKSHOP_JOBS),
            ("wish", "invent", "make", "playtest", "instructions", "deliver"),
        )
        profile = load_taste(Path(__file__).resolve().parents[1])
        self.assertEqual(profile.name, {name_literal})
        self.assertTrue(profile.content.strip())

    def test_preview_is_read_only_and_an_explicitly_disabled_engine_waits_truthfully(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "workshop"
            with mock.patch.dict(
                os.environ,
                {{
                    "{env}_RUNTIME": str(runtime),
                    "WORKSHOP_AGENT_WORKERS": "disabled",
                }},
            ):
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
            name_literal=repr(name),
            package=package,
        ),
    }
    hook = _hook_source(level)
    if hook is not None:
        files["src/{package}/inventor.py".format(package=package)] = hook
        files["hook.py"] = _rpc_hook_source(level, package)
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
    name: Optional[str] = None,
    description: Optional[str] = None,
    *,
    lane: Optional[str] = None,
    level: str = "taste-only",
    template: Optional[str] = None,
    taste_path: Optional[Path] = None,
    run_checks: bool = True,
) -> Path:
    """Create and validate one inventor before atomically joining the catalog.

    When ``taste_path`` is supplied, its strict discovery header supplies the
    Inventor's name and description and its complete exact bytes become the
    generated profile's ``TASTE.md``. This is the zero-custom-code path: the
    generated profile inherits every shared Workshop stage.
    """

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
    if (
        keyword.iskeyword(package)
        or package in _RESERVED_PACKAGES
        or package in sys.stdlib_module_names
    ):
        raise ContractError("inventor id maps to a reserved Python package name")
    source_taste = None
    if taste_path is not None:
        requested_taste = Path(taste_path)
        if requested_taste.name != "TASTE.md" or requested_taste.is_symlink():
            raise ContractError(
                "existing Taste must be a regular file named TASTE.md: %s"
                % requested_taste
            )
        try:
            resolved_taste = requested_taste.resolve(strict=True)
        except OSError as exc:
            raise ContractError(
                "cannot resolve existing TASTE.md: %s" % requested_taste
            ) from exc
        if resolved_taste.name != "TASTE.md":
            raise ContractError(
                "existing Taste must be a regular file named TASTE.md: %s"
                % requested_taste
            )
        from .taste import load_taste

        source_taste = load_taste(resolved_taste.parent)
        if source_taste.path != resolved_taste:
            raise ContractError(
                "existing Taste must be the root TASTE.md in its folder: %s"
                % requested_taste
            )
        if name is not None and _display_text(name, "name", 200) != source_taste.name:
            raise ContractError(
                "inventor name conflicts with the name in the existing TASTE.md"
            )
        if (
            description is not None
            and _display_text(description, "description", 500)
            != source_taste.description
        ):
            raise ContractError(
                "inventor description conflicts with the description in the existing TASTE.md"
            )
        name = source_taste.name
        description = source_taste.description
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
            inventor_id,
            name,
            description,
            lane,
            level,
            taste_content=(source_taste.content if source_taste is not None else None),
        ).items():
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative == "TASTE.md":
                # Preserve an imported creative constitution byte for byte.
                target.write_bytes(content.encode("utf-8"))
            else:
                target.write_text(content, encoding="utf-8")

        # Validate exactly the folder that will be made visible. Declared smoke
        # checks run in staging, so failure leaves no half-created inventor.
        from .contribution import run_declared_checks, validate_contribution
        from .manifest import load_manifest
        from .taste import load_taste

        manifest = load_manifest(temporary / "inventor.json")
        problems = validate_contribution(manifest)
        generated_taste = load_taste(temporary)
        if source_taste is not None:
            try:
                source_taste.assert_current()
            except ContractError as exc:
                raise ContractError(
                    "existing TASTE.md changed during Inventor creation; retry"
                ) from exc
            if (
                generated_taste.sha256 != source_taste.sha256
                or generated_taste.content != source_taste.content
            ):
                raise ContractError(
                    "created inventor did not preserve the existing TASTE.md exactly"
                )
        if not problems and run_checks:
            problems = run_declared_checks(manifest)
        if problems:
            raise ContractError("inventor creation failed validation: %s" % "; ".join(problems))

        # The staged collection must be Manager-discoverable before publication.
        from .manager import discover_inventor_catalog

        staged_catalog = discover_inventor_catalog(staging_root)
        if not staged_catalog.card(inventor_id).routable:
            raise ContractError("created inventor is not routable")
        if source_taste is not None:
            # Do not publish a profile if the person's source Taste changed
            # while the generated smoke checks were running.
            try:
                source_taste.assert_current()
            except ContractError as exc:
                raise ContractError(
                    "existing TASTE.md changed during Inventor creation; retry"
                ) from exc
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
