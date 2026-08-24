"""Create a Workshop-connected inventor without copying another harness."""

from __future__ import annotations

import hashlib
import json
import keyword
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict

from .errors import ContractError, StateConflict

_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
_RESERVED_PACKAGES = frozenset(
    ("inventor_core", "inventor_foundation", "inventor_workshop", "test", "tests")
)
_TEMPLATES = {
    "board-game": "game-design",
    "physical-product": "product-design",
    "custom": "domain-design",
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


def _files(
    inventor_id: str, name: str, niche: str, template: str
) -> Dict[str, str]:
    package = inventor_id.replace("-", "_")
    capability = _TEMPLATES[template]
    objective_literal = repr(
        "Invent %s guided by %s's TASTE.md." % (niche, name)
    )
    template_literal = repr(template)
    offline_inspection_config_literal = repr(
        hashlib.sha256(b"workshop-offline-workshop-v1").hexdigest()
    )
    manifest = {
        "schema_version": 4,
        "id": inventor_id,
        "name": name,
        "niche": niche,
        "summary": "An autonomous inventor for %s." % niche,
        "autonomy": "human-checkpointed",
        "status": "experimental",
        "entrypoint": ["python3", "-m", package],
        "capabilities": [capability, "offline-make"],
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
    return {
        "inventor.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        "TASTE.md": """# {name}'s taste

This file is {name}'s creative constitution. Humans own changes to it; agents
may propose revisions from verified outcomes but may not edit it autonomously.

## North star

Create {niche} that people understand, value, and choose to experience again.

## Starting defaults

- Prefer a clear, ownable idea over a bundle of familiar features.
- Make function and interaction carry the identity; ornament cannot rescue a
  generic product.
- Favor evidence from real use, production, and external outcomes over a
  generator's or evaluator's confidence.
- Kill a weak candidate rather than lower a gate because work was already spent.

## Define before autonomous release

- Who is this inventor specifically for?
- What three qualities should make its work recognizable without a logo?
- Which familiar defaults, themes, forms, or mechanics are instant rejects?
- What is the one signature interaction or product moment to optimize for?
- What observed behavior counts as delight, and what evidence can change this
  taste?
""".format(name=name, niche=niche),
        "README.md": """# {name}

{name} is an experimental inventor for **{niche}** built in Autonomous
Workshop from one Wish, a distinct Taste, and a Make/Inspect loop.

Read [`TASTE.md`](TASTE.md) before proposing a product. It defines this
inventor's creative constitution and remains human-owned.

## Make this inventor yours

1. Finish `TASTE.md` with recognizable preferences and explicit rejects.
2. Edit `src/{package}/workflow.py`: this is the inventor-owned loop between
   Make and Inspect.
3. Connect the real model, CAD, and evaluation tools this inventor needs.
4. Tune Taste and the Make/Inspect loop using artifact-bound evidence.

## Run locally

```bash
python3 -m pip install -e ../.. -e .
{package} doctor
{package} make first-product
{package} status
workshop check . --run
```

`make` is deterministic, credential-free, and deliberately not production CAD.
It calls `Workbench.make()` and `Workbench.inspect()` separately, writes
`make.json` and `inspection.json`, and records the artifact-bound Inspection in
the local `.workshop/` runtime. Runtime state and credentials are never committed.

## Before autonomous or public operation

Keep every Inspection bound to exact artifact bytes. Add real slicer, form,
safety, and physical evidence. Configure budgets and scoped credentials before
allowing autonomous external effects.
""".format(name=name, niche=niche, package=package, template=template),
        ".gitignore": ".workshop/\n__pycache__/\n*.py[cod]\n",
        "pyproject.toml": """[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "inventor-{inventor_id}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["inventor-workshop>=0.3,<0.4"]

[project.scripts]
{package} = "{package}.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]
""".format(inventor_id=inventor_id, package=package),
        "MANIFEST.in": "include inventor.json TASTE.md setup.py\n",
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
            repr("%s: inventor-specific Taste and workflow on Workshop." % name)
            + "\n"
        ),
        "src/{package}/workflow.py".format(package=package): """from inventor_workshop import InspectionPolicy, Wish, Workflow, WorkflowSpec


WORKFLOW = Workflow(
    WorkflowSpec(
        initial_stage="make",
        stages=("make", "inspect"),
        edges={{
            "make": ("inspect",),
            "inspect": ("make",),
        }},
        required_gates={{"inspect": ("workshop-starter",)}},
        gate_policies={{
            "workshop-starter": InspectionPolicy(
                "workshop-starter",
                "workshop-offline-workshop",
                "1.0.0",
                {offline_inspection_config_literal},
            )
        }},
    )
)


def wish(product_id):
    # This function is inventor-owned. Encode the inputs that give this
    # inventor a recognizable point of view.
    return Wish.create(
        product_id,
        {objective_literal},
        constraints={{"template": {template_literal}}},
    )
""".format(
            objective_literal=objective_literal,
            offline_inspection_config_literal=offline_inspection_config_literal,
            template_literal=template_literal,
        ),
        "src/{package}/__main__.py".format(package=package): """import argparse
import hashlib
import json
import os
import sysconfig
from datetime import datetime, timezone
from pathlib import Path

from inventor_workshop import Clockwork, MakerMark, discover_skills, load_taste
from inventor_workshop.offline import offline_workbench
from .workflow import WORKFLOW, wish


def inventor_root():
    package_file = Path(__file__).resolve()
    packaged = package_file.parent / "_identity"
    if (packaged / "inventor.json").is_file() and (packaged / "TASTE.md").is_file():
        return packaged.resolve()
    root = next(
        (parent for parent in package_file.parents if (parent / "inventor.json").is_file()),
        None,
    )
    if root is None:
        installed = Path(sysconfig.get_path("data")) / "share" / "inventor-{inventor_id}"
        if (installed / "inventor.json").is_file() and (installed / "TASTE.md").is_file():
            return installed.resolve()
        raise RuntimeError("cannot locate this inventor's installed identity")
    return root.resolve()


def runtime_root():
    configured = os.environ.get("{env}_RUNTIME")
    if configured:
        root = Path(configured).expanduser()
        if not root.is_absolute():
            raise ValueError("{env}_RUNTIME must be an absolute path")
        return root
    identity = inventor_root()
    if (identity / "pyproject.toml").is_file():
        return identity / ".workshop"
    return Path.home() / ".local" / "share" / "autonomous-inventors" / "{inventor_id}"


def database_path():
    return runtime_root() / "clockwork.sqlite3"


def doctor():
    taste = load_taste(inventor_root())
    skills = discover_skills()
    print("taste %s %d-bytes" % (taste.sha256, taste.byte_count))
    print("skills " + ", ".join(skill.name for skill in skills))
    print("workshop ready (offline; no credentials required; no state changed)")


def make(product_id):
    started_at = datetime.now(timezone.utc).isoformat()
    clockwork = Clockwork(database_path())
    try:
        clockwork.get_product(product_id)
    except KeyError:
        pass
    else:
        raise ValueError("product already exists: %s" % product_id)
    run_root = runtime_root() / "runs" / product_id
    workbench = offline_workbench()
    made = workbench.make(
        wish(product_id),
        inventor_root(),
        run_root,
        budget_micros=1,
    )
    inspection = workbench.inspect(made)
    wish_sha256 = hashlib.sha256(
        json.dumps(
            made.wish.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    mark = MakerMark(
        schema_version=1,
        inventor_id="{inventor_id}",
        run_id="offline-" + made.artifact_manifest.artifact_sha256[:24],
        mode="offline",
        tool="workshop-offline-muse",
        tool_version="0.4.0",
        authenticated=False,
        taste_sha256=made.taste.sha256,
        artifact_sha256=made.artifact_manifest.artifact_sha256,
        input_sha256={{"wish": wish_sha256}},
        agent_calls=1,
        actual_cost_micros=0,
        synthetic_cost_micros=0,
        started_at=started_at,
        completed_at=datetime.now(timezone.utc).isoformat(),
        limitations=(
            "Deterministic offline starter; no authenticated live model was used.",
            "Not production CAD and no physical print or human test was performed.",
        ),
    )
    mark.assert_artifact(made.artifact_manifest.artifact_sha256)
    product = WORKFLOW.register(
        clockwork,
        product_id,
        metadata={{
            "offline_make": True,
            "taste_sha256": made.taste.sha256,
            "concept_sha256": made.concept_sha256,
        }},
        artifact_sha256=made.artifact_manifest.artifact_sha256,
    )
    WORKFLOW.advance(
        clockwork,
        product_id,
        "inspect",
        product["revision"],
        inspection=inspection,
    )
    (run_root / "make.json").write_text(
        json.dumps(made.to_dict(), indent=2, sort_keys=True) + "\\n",
        encoding="utf-8",
    )
    (run_root / "inspection.json").write_text(
        json.dumps(inspection.to_dict(), indent=2, sort_keys=True) + "\\n",
        encoding="utf-8",
    )
    (run_root / "maker-mark.json").write_text(
        mark.to_json() + "\\n",
        encoding="utf-8",
    )
    print("made and inspected %s -> %s" % (product_id, inspection.artifact_sha256))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="{package}")
    parser.add_argument("command", choices=("init", "make", "doctor", "status"))
    parser.add_argument("product_id", nargs="?")
    args = parser.parse_args(argv)
    if args.command == "doctor":
        doctor()
        return 0
    if args.command == "make":
        if not args.product_id:
            parser.error("make requires product_id")
        make(args.product_id)
        return 0
    if args.command == "status" and not database_path().is_file():
        print("no Clockwork state yet: %s" % database_path())
        return 0
    clockwork = Clockwork(database_path())
    if args.command == "init":
        print(database_path())
        return 0
    products = clockwork.list_products()
    print("state database: %s" % database_path())
    for product in products:
        print("%s %s@%s %s" % (
            product["id"],
            product["stage"],
            product["revision"],
            product.get("artifact_sha256") or "unbound",
        ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""".format(
            env=inventor_id.upper().replace("-", "_"),
            inventor_id=inventor_id,
            package=package,
        ),
        "tests/test_smoke.py": """import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop import load_taste
from {package}.__main__ import database_path, main
from {package}.workflow import WORKFLOW


class SmokeTest(unittest.TestCase):
    def test_workflow_exposes_direct_workshop_route(self):
        self.assertEqual(WORKFLOW.legal_targets("make"), ("inspect",))
        self.assertEqual(WORKFLOW.legal_targets("inspect"), ("make",))

    def test_root_taste_is_the_runtime_source(self):
        profile = load_taste(Path(__file__).resolve().parents[1])
        self.assertIn("creative constitution", profile.content)

    def test_offline_make_binds_taste_and_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict(os.environ, {{"{env}_RUNTIME": temporary}}):
                self.assertEqual(main(("make", "made-product")), 0)
                self.assertTrue(database_path().is_file())
                run = Path(temporary) / "runs/made-product"
                made = json.loads((run / "make.json").read_text(encoding="utf-8"))
                inspected = json.loads(
                    (run / "inspection.json").read_text(encoding="utf-8")
                )
                maker_mark = json.loads(
                    (run / "maker-mark.json").read_text(encoding="utf-8")
                )
                self.assertEqual(
                    made["artifact_manifest"]["artifact_sha256"],
                    inspected["artifact_sha256"],
                )
                self.assertEqual(
                    [item["inspection_id"] for item in inspected["results"]],
                    ["workshop-starter"],
                )
                self.assertIsNotNone(inspected["cad_release_sha256"])
                self.assertEqual(
                    maker_mark["artifact_sha256"],
                    made["artifact_manifest"]["artifact_sha256"],
                )
                self.assertEqual(maker_mark["mode"], "offline")

    def test_doctor_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "not-created"
            with mock.patch.dict(os.environ, {{"{env}_RUNTIME": str(runtime)}}):
                self.assertEqual(main(("doctor",)), 0)
                self.assertFalse(runtime.exists())


if __name__ == "__main__":
    unittest.main()
""".format(package=package, env=inventor_id.upper().replace("-", "_")),
    }


def scaffold_inventor(
    root: Path,
    inventor_id: str,
    name: str,
    niche: str,
    *,
    template: str = "physical-product",
) -> Path:
    root = Path(root).resolve()
    if not _ID.fullmatch(inventor_id):
        raise ContractError("inventor id must match %s" % _ID.pattern)
    package = inventor_id.replace("-", "_")
    if keyword.iskeyword(package) or package in _RESERVED_PACKAGES:
        raise ContractError("inventor id maps to a reserved Python package name")
    name = _display_text(name, "name", 200)
    niche = _display_text(niche, "niche", 500)
    if template not in _TEMPLATES:
        raise ContractError(
            "inventor template must be one of %s" % sorted(_TEMPLATES)
        )
    root.mkdir(parents=True, exist_ok=True)
    destination = root / inventor_id
    if destination.exists():
        raise StateConflict("inventor folder already exists: %s" % destination)
    temporary = Path(tempfile.mkdtemp(prefix=".%s." % inventor_id, dir=str(root)))
    try:
        for relative, content in _files(
            inventor_id, name, niche, template
        ).items():
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        os.replace(str(temporary), str(destination))
    finally:
        if temporary.exists():
            shutil.rmtree(str(temporary))
    return destination
