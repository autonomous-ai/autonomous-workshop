"""The seeded batch's mechanical project and package steps (ADR 0098).

Run by the host as batch steps, in a credential-free environment:

    python -m workshop.make.seeded_package prepare RUN_ROOT --project DIR
    python -m workshop.make.seeded_package product RUN_ROOT --project DIR --product-root DIR --source FILE

``prepare`` copies the sealed seed's CAD project into the run's CAD project
and installs the run's own ``print_details.py`` (ADR 0096 decision 1b: a
changed library rebuilds, and a changed shape is then a seed deviation the
component rounds report). ``product`` writes what the Make finalizer reads
and no model needs to author: ``product.json`` (title and summary from the
Proof's ``SEED-PRODUCT.json``, the title from the Wish's name line when it
has one), the Spark source (the host assignment's inventor and ranking and
the sealed concept and research), the root ``assembled.step`` copies of the
final verifier's combined STEP, and a powered toy's README carrying its
Electrical assembly text verbatim.

Nothing here judges or edits a shape. Exit 0 on success, 1 when an input
the step needs is absent or malformed (a check failure, named), anything
else is a harness failure.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping, Optional

from workshop.make.seeded_batch import compose_spark_source

SEED = "seed"
# Not part of the CAD project: the approval, its review and checklist, the
# approved STEP copies the host diffs against, and the product source.
NOT_PROJECT = ("APPROVAL.json", "CRITIC.json", "CONCEPT-CHECKLIST.md", "SEED-PRODUCT.json")
NOT_PROJECT_DIRS = ("approved",)
PRINT_DETAILS = ".agents/skills/print-details/scripts/print_details.py"
NAME_LINE = re.compile(r"Name this (?:toy|revision) exactly: (.+?)\.?\s*$")
ELECTRICAL_ASSEMBLY = "measure/electrical/assembly.md"


class PackageError(Exception):
    pass


def prepare(run_root: Path, project: Path) -> list:
    """Copy the seed's project files into ``project``; return what changed
    from the seed (only ever the print-details library)."""

    seed = run_root / SEED
    if not seed.is_dir():
        raise PackageError("the run has no seed/ directory")
    project.mkdir(parents=True, exist_ok=True)
    for path in sorted(seed.rglob("*")):
        relative = path.relative_to(seed)
        if not path.is_file() or relative.as_posix() in NOT_PROJECT or relative.parts[0] in NOT_PROJECT_DIRS:
            continue
        if relative.as_posix() == "features/print_details.py" and (run_root / PRINT_DETAILS).is_file():
            continue  # installed from the run's library below, never copied over it
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != path.read_bytes():
            shutil.copyfile(path, target)
            target.chmod(0o644)
    changed = []
    library = run_root / PRINT_DETAILS
    installed = project / "features/print_details.py"
    if library.is_file() and (not installed.is_file() or installed.read_bytes() != library.read_bytes()):
        installed.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(library, installed)
        changed.append("features/print_details.py")
    return changed


def wish_name(run_root: Path) -> Optional[str]:
    """The exact name the Wish's first line gives, or None."""

    wish = json.loads((run_root / "WISH.json").read_text(encoding="utf-8"))
    objective = wish.get("objective") if isinstance(wish, dict) else None
    first = objective.split("\n", 1)[0] if isinstance(objective, str) else ""
    match = NAME_LINE.fullmatch(first.strip())
    return match.group(1).strip() if match else None


def assignment(run_root: Path) -> Mapping[str, Any]:
    stage = json.loads((run_root / "STAGE.json").read_text(encoding="utf-8"))
    try:
        return stage["inputs"]["workshop_selection"]["assignment"]
    except (KeyError, TypeError) as exc:
        raise PackageError("STAGE.json has no Workshop inventor assignment") from exc


def _entry_step(project: Path) -> Path:
    entries = sorted(path for path in project.glob("*.step.py") if not path.name.startswith("part_"))
    if len(entries) != 1:
        raise PackageError("the CAD project needs exactly one assembly entry *.step.py; found %d" % len(entries))
    return entries[0].with_suffix("")


def product(run_root: Path, project: Path, product_root: Path, source: Path) -> dict:
    """Write product.json, the Spark source, the assembled copies and a
    powered toy's README."""

    from workshop.errors import ContractError
    from workshop.wish.seed import SEED_PRODUCT, check_seed_product

    try:
        sealed = check_seed_product((run_root / SEED / SEED_PRODUCT).read_bytes())
    except (OSError, ContractError) as exc:
        raise PackageError(str(exc)) from exc
    title = wish_name(run_root) or sealed["title"]
    product_root.mkdir(parents=True, exist_ok=True)
    (product_root / "product.json").write_text(
        json.dumps({"title": title, "summary": sealed["summary"]}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps(compose_spark_source(sealed, assignment(run_root)), indent=2, ensure_ascii=False)
                      + "\n", encoding="utf-8")
    step = _entry_step(project)
    package = step.with_name(step.name + ".json")
    for path, name in ((step, "assembled.step"), (package, "assembled.step.json")):
        if not path.is_file():
            raise PackageError("final verification wrote no %s" % path.relative_to(project))
        shutil.copyfile(path, product_root / name)
    electrical = project / ELECTRICAL_ASSEMBLY
    if electrical.is_file():
        (product_root / "README.md").write_bytes(electrical.read_bytes())
    return {"title": title}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("run_root", type=Path)
    p.add_argument("--project", type=Path, required=True)
    p = sub.add_parser("product")
    p.add_argument("run_root", type=Path)
    p.add_argument("--project", type=Path, required=True)
    p.add_argument("--product-root", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            changed = prepare(args.run_root, args.project)
            print("seeded_package: prepared %s%s" % (args.project, "; installed %s" % ", ".join(changed)
                                                    if changed else ""))
        else:
            done = product(args.run_root, args.project, args.product_root, args.source)
            print("seeded_package: packaged %r" % done["title"])
    except (PackageError, OSError, ValueError) as exc:
        print("seeded_package: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
