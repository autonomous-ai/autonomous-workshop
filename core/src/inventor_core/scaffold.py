"""Create a core-connected inventor package without copying another harness."""

from __future__ import annotations

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
_RESERVED_PACKAGES = frozenset(("inventor_core", "test", "tests"))


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


def _files(inventor_id: str, name: str, niche: str) -> Dict[str, str]:
    package = inventor_id.replace("-", "_")
    manifest = {
        "schema_version": 1,
        "id": inventor_id,
        "name": name,
        "niche": niche,
        "summary": "A core-connected autonomous inventor for %s." % niche,
        "autonomy": "autonomous",
        "status": "experimental",
        "entrypoint": ["python3", "-m", package],
        "capabilities": [
            "research",
            "game-design",
            "simulation",
            "cad",
            "publishing",
        ],
        "core_features": [
            "state.sqlite",
            "lifecycle.receipts",
            "artifacts.content-addressed",
            "publishing.panda",
            "skills.product-to-cad",
        ],
        "source": {"kind": "local"},
    }
    return {
        "inventor.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        "README.md": """# {name}

{name} is an autonomous inventor for **{niche}**.

## Thesis

Write the niche-specific creative thesis, target player, taste, mechanism
families, and reward hypothesis here. This folder owns those choices. Shared
state, leases, budgets, artifact identity, CAD evidence, and Panda publication
belong to `../core`.

## Run locally

```bash
python3 -m pip install -e ../core -e .
{package} init
{package} create first-product
{package} status
```

`init` creates `.runtime/state.sqlite`; runtime state and credentials are never
committed. Implement the next legal pipeline step in `workflow.py`, keep every
gate bound to exact artifact bytes, and publish draft-first through core.

## Pipeline

The starter uses core's conservative board-game lifecycle. Replace or extend
the graph only in code, with tests for legal edges, required evidence, repair
budgets, terminal states, and “no viable product” outcomes.
""".format(name=name, niche=niche, package=package),
        "pyproject.toml": """[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "autonomous-inventor-{inventor_id}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["autonomous-inventor-core>=0.1,<0.2"]

[project.scripts]
{package} = "{package}.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]
""".format(inventor_id=inventor_id, package=package),
        "src/{package}/__init__.py".format(package=package): (
            repr("%s: niche logic layered over inventor_core." % name) + "\n"
        ),
        "src/{package}/workflow.py".format(package=package): """from inventor_core import Pipeline, PipelineSpec


PIPELINE = Pipeline(PipelineSpec.board_game())
""",
        "src/{package}/__main__.py".format(package=package): """import argparse
import os
from pathlib import Path

from inventor_core import InventorStore
from .workflow import PIPELINE


def database_path():
    configured = os.environ.get("{env}_RUNTIME")
    if configured:
        root = Path(configured).expanduser()
        if not root.is_absolute():
            raise ValueError("{env}_RUNTIME must be an absolute path")
    else:
        package_file = Path(__file__).resolve()
        inventor_root = next(
            (parent for parent in package_file.parents if (parent / "inventor.json").is_file()),
            None,
        )
        root = (
            inventor_root / ".runtime"
            if inventor_root is not None
            else Path.home() / ".local" / "share" / "autonomous-inventors" / "{inventor_id}"
        )
    return root / "state.sqlite"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="{package}")
    parser.add_argument("command", choices=("init", "create", "status"))
    parser.add_argument("product_id", nargs="?")
    args = parser.parse_args(argv)
    store = InventorStore(database_path())
    if args.command == "init":
        print(database_path())
        return 0
    if args.command == "create":
        if not args.product_id:
            parser.error("create requires product_id")
        product = PIPELINE.register(store, args.product_id)
        print("created %s at %s@%s" % (
            product["id"], product["stage"], product["revision"]
        ))
        return 0
    products = store.list_products()
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
        "tests/test_smoke.py": """import unittest

from {package}.workflow import PIPELINE


class SmokeTest(unittest.TestCase):
    def test_pipeline_has_safe_publication_edge(self):
        self.assertEqual(PIPELINE._edges["draft"], {{"live", "killed"}})


if __name__ == "__main__":
    unittest.main()
""".format(package=package),
    }


def scaffold_inventor(root: Path, inventor_id: str, name: str, niche: str) -> Path:
    root = Path(root).resolve()
    if not _ID.fullmatch(inventor_id):
        raise ContractError("inventor id must match %s" % _ID.pattern)
    package = inventor_id.replace("-", "_")
    if keyword.iskeyword(package) or package in _RESERVED_PACKAGES:
        raise ContractError("inventor id maps to a reserved Python package name")
    name = _display_text(name, "name", 200)
    niche = _display_text(niche, "niche", 500)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / inventor_id
    if destination.exists():
        raise StateConflict("inventor folder already exists: %s" % destination)
    temporary = Path(tempfile.mkdtemp(prefix=".%s." % inventor_id, dir=str(root)))
    try:
        for relative, content in _files(inventor_id, name, niche).items():
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        os.replace(str(temporary), str(destination))
    finally:
        if temporary.exists():
            shutil.rmtree(str(temporary))
    return destination
