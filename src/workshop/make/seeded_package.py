"""The seeded batch's mechanical project and package steps (ADR 0098).

Run by the host as batch steps, in a credential-free environment:

    python -m workshop.make.seeded_package prepare RUN_ROOT --project DIR
    python -m workshop.make.seeded_package product RUN_ROOT --project DIR --product-root DIR --source FILE
    python -m workshop.make.seeded_package parts --project DIR --product-root DIR
    python -m workshop.make.seeded_package check --project DIR

``prepare`` copies the sealed seed's CAD project into the run's CAD project
and installs the run's own ``print_details.py`` (ADR 0096 decision 1b: a
changed library rebuilds, and a changed shape is then a seed deviation the
component rounds report). ``product`` writes what the Make finalizer reads
and no model needs to author: ``product.json`` (title and summary from the
Proof's ``SEED-PRODUCT.json``, the title from the Wish's name line when it
has one), the Spark source (the host assignment's inventor and ranking and
the sealed concept and research), the root ``assembled.step`` copies of the
final verifier's combined STEP, and a powered toy's README carrying its
Electrical assembly text verbatim. ``parts`` writes the production solid of
every printed occurrence of a multi-part package, ``parts/<name>.step``,
from the Component STEP the print gates passed: a one-solid Component's
file is copied byte for byte (each instance gets the same bytes), and a
Component whose STEP holds several labelled solids is split by label. An
occurrence that names no Component, or more than one, is a check failure
that names it. ``check`` is the design batch's packaging check on a Proof:
the colour names and the same resolution, with nothing written.

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


def assembly_descriptor(project: Path) -> Path:
    """The assembly package final verification's ``gen --write`` wrote for
    the entry: cadgen keys it by the entry source's file name, under
    ``__cadgen__/models/<entry>.step.py/assembly.json``."""

    return project / "__cadgen__" / "models" / (_entry_step(project).name + ".py") / "assembly.json"


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
    package = assembly_descriptor(project)
    for path, name in ((step, "assembled.step"), (package, "assembled.step.json")):
        if not path.is_file():
            raise PackageError("final verification wrote no %s" % path.relative_to(project))
        shutil.copyfile(path, product_root / name)
    electrical = project / ELECTRICAL_ASSEMBLY
    if electrical.is_file():
        (product_root / "README.md").write_bytes(electrical.read_bytes())
    return {"title": title}


def _occurrence_label(name: str, colour: str) -> str:
    """The part half of ``<part>_<colour>`` (a hyphen separates the same)."""

    return name[: len(name) - len(colour) - 1]


def _instance_base(label: str) -> Optional[str]:
    match = re.fullmatch(r"(.+)-([1-9][0-9]*)", label)
    return match.group(1) if match else None


def _read_package(path: Path):
    from workshop.errors import ContractError
    from workshop.make.assembly_package import read_assembly_package

    try:
        return read_assembly_package(path.read_bytes())
    except (OSError, ContractError) as exc:
        raise PackageError("%s is not an assembly package: %s" % (path.name, exc)) from exc


def _default_tools(read_parts, export_leaf):
    if read_parts is None or export_leaf is None:
        from workshop.make import proof_diff
        import build123d as bd

        read_parts = read_parts or proof_diff.read_parts
        export_leaf = export_leaf or (lambda shape, path: bd.export_step(shape, str(path)))
    return read_parts, export_leaf


def _parts_plan(project: Path, package, read_parts) -> tuple:
    """``(plan, leaves)``: for each printed occurrence of a multi-part
    package, ``(name, component STEP, leaf label or None)``. One unresolved
    or ambiguous occurrence refuses the whole plan, naming each."""

    printed = package.printed_occurrences
    if len(printed) < 2:
        return [], {}
    entry = _entry_step(project).name
    files = {path.name[len("part_"):-len(".step")]: path for path in sorted(project.glob("part_*.step"))
             if path.name != entry}
    leaves = {}
    unresolved, ambiguous = [], []
    plan = []
    for occurrence in printed:
        colour = occurrence.colour_name
        if colour is None:
            raise PackageError("occurrence %s is not named <part>_<colour>" % occurrence.name)
        label = _occurrence_label(occurrence.name, colour)
        whole = [role for role in files if role in (label, _instance_base(label))]
        if whole and len(whole) == 1:
            role = whole[0]
            if role not in leaves:
                leaves[role] = read_parts(files[role])
            if len(leaves[role]) == 1:
                plan.append((occurrence.name, files[role], None))
                continue
        found = []
        for role, path in files.items():
            if role not in leaves:
                leaves[role] = read_parts(path)
            found += [(role, path, leaf) for leaf in leaves[role] if leaf == label and len(leaves[role]) > 1]
        if len(found) == 1:
            plan.append((occurrence.name, found[0][1], found[0][2]))
        elif found:
            ambiguous.append("%s (in %s)" % (occurrence.name, ", ".join(sorted(item[0] for item in found))))
        else:
            unresolved.append(occurrence.name)
    if unresolved or ambiguous:
        raise PackageError("cannot export production parts: %s" % "; ".join(
            [*(["no Component STEP holds %s" % ", ".join(unresolved)] if unresolved else []),
             *(["more than one Component STEP holds %s" % ", ".join(ambiguous)] if ambiguous else [])]))
    return plan, leaves


def export_parts(project: Path, product_root: Path, *, read_parts=None, export_leaf=None) -> list:
    """Write ``parts/<occurrence>.step`` for every printed occurrence of a
    multi-part package; return the names written. A package of fewer than
    two printed occurrences needs no production parts."""

    package = _read_package(product_root / "assembled.step.json")
    if len(package.printed_occurrences) < 2:
        return []
    read_parts, export_leaf = _default_tools(read_parts, export_leaf)
    plan, leaves = _parts_plan(project, package, read_parts)
    out = product_root / "parts"
    out.mkdir(parents=True, exist_ok=True)
    for name, path, leaf in plan:
        target = out / ("%s.step" % name)
        if leaf is None:
            shutil.copyfile(path, target)
        else:
            export_leaf(leaves[path.name[len("part_"):-len(".step")]][leaf], target)
        target.chmod(0o644)
    return [name for name, unused, unused_leaf in plan]


def check_package(project: Path, *, read_parts=None) -> list:
    """The design batch's packaging check on a Proof (ADR 0098): the
    assembly package its final verification wrote names every printed
    occurrence of a multi-part model for a stocked colour, and each resolves
    to exactly one Component STEP solid, as ``parts`` will export it in the
    run. Writes nothing; returns the occurrence names."""

    from workshop.errors import ContractError
    from workshop.make.assembly_package import validate_occurrence_colour_names

    descriptor = assembly_descriptor(project)
    if not descriptor.is_file():
        raise PackageError("final verification wrote no %s" % descriptor.relative_to(project))
    package = _read_package(descriptor)
    try:
        validate_occurrence_colour_names(package)
    except ContractError as exc:
        raise PackageError(str(exc)) from exc
    if len(package.printed_occurrences) < 2:
        return []
    plan, _leaves = _parts_plan(project, package, _default_tools(read_parts, lambda *_: None)[0])
    return [name for name, unused, unused_leaf in plan]


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
    p = sub.add_parser("parts")
    p.add_argument("--project", type=Path, required=True)
    p.add_argument("--product-root", type=Path, required=True)
    p = sub.add_parser("check")
    p.add_argument("--project", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            changed = prepare(args.run_root, args.project)
            print("seeded_package: prepared %s%s" % (args.project, "; installed %s" % ", ".join(changed)
                                                    if changed else ""))
        elif args.command == "check":
            names = check_package(args.project)
            print("seeded_package: the package resolves %d production part(s)" % len(names))
        elif args.command == "parts":
            written = export_parts(args.project, args.product_root)
            print("seeded_package: wrote %d production part(s)" % len(written))
        else:
            done = product(args.run_root, args.project, args.product_root, args.source)
            print("seeded_package: packaged %r" % done["title"])
    except (PackageError, OSError, ValueError) as exc:
        print("seeded_package: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
