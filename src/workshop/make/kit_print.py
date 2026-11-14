"""The host's check of a Made kit's print layout (ADR 0104 decision 4).

Final verification lays every Sheet of a kit and every loose printed Part
copy into ``measure/kit/print.step`` and records it in
``measure/kit/print.json`` (``make-round/scripts/kit_print.py``). Before
Make is accepted the host checks, on the sealed bytes and without
rebuilding geometry (ADR 0061), that

- the record is for the sealed tree and names the sealed STEP by hash;
- its Sheets are the tree's Sheets with their contract copies, and its loose
  copies are every printed Part on no Sheet, as many as the toy uses;
- the STEP's leaves are exactly ``<Sheet>/frame``, ``<Sheet>/<Part>#n`` and
  ``loose/<Part>#n`` for those copies, so no Bought Part body is in it, each
  leaf holds a solid, and every copy of one Part has the same volume and area.

The accepted record names the file Release ships as the Factory primary in
place of the assembled scene, so Factory weighs the filament the maker
prints, frames included. A kit with Sheets must have one; a kit without
Sheets is checked when final verification wrote one (current tools always
do) and otherwise keeps its scene.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from workshop.errors import ContractError
from workshop.make.kit_tree import has_assembly_tree, install_document, not_printed, tree_digest, tree_totals

KIND = "kit-print-layout"
SCHEMA_VERSION = 1
STEP_PATH = "measure/kit/print.step"
REPORT_PATH = "measure/kit/print.json"
SCENE_PATH = "assembled.step"
LOOSE = "loose"
_TOLERANCE = 1e-5


def expected_copies(contract: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """``(sheets, loose)`` the sealed tree gives, as the run-local tool
    writes them."""

    tree = contract["assembly_tree"]
    totals = tree_totals(tree)
    sheets, on_sheet = [], set()
    for sheet in tree.get("sheets") or []:
        copies: dict[str, int] = {}
        for entry in sheet["parts"]:
            copies[entry["id"]] = copies.get(entry["id"], 0) + int(entry["count"])
            on_sheet.add(entry["id"])
        sheets.append({"id": sheet["id"], "filament": sheet["filament"], "copies": copies})
    printed = sorted(item["id"] for item in tree["parts"] if "filament" in item)
    loose = {part: totals.get(part, 0) for part in printed if part not in on_sheet and totals.get(part, 0) > 0}
    return sheets, loose


def expected_bodies(sheets, loose) -> list[str]:
    names = []
    for sheet in sheets:
        names.append("%s/frame" % sheet["id"])
        for part, count in sheet["copies"].items():
            names += ["%s/%s#%d" % (sheet["id"], part, n) for n in range(1, count + 1)]
    for part, count in loose.items():
        names += ["%s/%s#%d" % (LOOSE, part, n) for n in range(1, count + 1)]
    return sorted(names)


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(1e-6, _TOLERANCE * max(abs(a), abs(b)))


def check_layout_step(content: bytes, names: list[str]) -> int:
    """Refuse a layout STEP whose leaves are not exactly ``names``, hold no
    solid, or whose copies of one Part differ; return its leaf count."""

    from workshop.release.printed_primary import scene_bodies

    bodies = scene_bodies(content)
    found = sorted(body.name for body in bodies)
    if found != names:
        missing = sorted(set(names) - set(found))
        extra = sorted(set(found) - set(names))
        raise ContractError(
            "%s does not hold exactly the kit's Sheets and loose copies: missing %s; extra %s"
            % (STEP_PATH, ", ".join(missing[:6]) or "none", ", ".join(extra[:6]) or "none")
        )
    by_part: dict[str, list] = defaultdict(list)
    for body in bodies:
        if not body.solids or body.total[0] <= 0:
            raise ContractError("%s leaf %s holds no solid" % (STEP_PATH, body.name))
        if not body.name.endswith("/frame"):
            by_part[body.name.split("/", 1)[1].rsplit("#", 1)[0]].append(body)
    for part, copies in by_part.items():
        first = copies[0].total
        if any(not (_close(c.total[0], first[0]) and _close(c.total[1], first[1])) for c in copies[1:]):
            raise ContractError("%s copies of %s differ in volume or area" % (STEP_PATH, part))
    return len(bodies)


def verify_made_print_layout(
    run_root: Path,
    made: Any,
    contract: Mapping[str, Any] | None,
    catalogue: Any,
) -> dict[str, Any] | None:
    """The printed-only primary record of a kit's layout, or None for a
    contract without an Assembly Tree or a kit without Sheets that wrote no
    layout. Raises ContractError naming what is wrong."""

    if not has_assembly_tree(contract) or not isinstance(catalogue, Mapping):
        return None
    product_root = Path(run_root).joinpath(*PurePosixPath(made.product_root).parts)
    entries = {entry.path: entry for entry in made.product_manifest.entries}
    prefix = PurePosixPath(made.cad_project_path)
    report_path = (prefix / REPORT_PATH).as_posix()
    if report_path not in entries:
        if contract["assembly_tree"].get("sheets"):
            raise ContractError(
                "final verification wrote no %s: a kit with Sheets ships its print layout as the "
                "Factory primary (ADR 0104 decision 4)" % REPORT_PATH
            )
        return None

    def sealed(path: str, missing: str) -> tuple[bytes, str]:
        entry = entries.get(path)
        if entry is None:
            raise ContractError(missing)
        data = product_root.joinpath(*PurePosixPath(path).parts).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != entry.bytes or digest != entry.sha256:
            raise ContractError("the Made file %s differs from the Made manifest" % path)
        return data, digest

    raw, report_sha256 = sealed(report_path, "")
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ContractError("%s is not JSON" % REPORT_PATH) from exc
    if not isinstance(report, Mapping) or report.get("kind") != KIND or report.get("schema_version") != SCHEMA_VERSION:
        raise ContractError("%s is not a kit print layout record" % REPORT_PATH)
    if report.get("tree_sha256") != tree_digest(install_document(contract, catalogue)):
        raise ContractError("%s was laid out for another Assembly Tree than the sealed one" % REPORT_PATH)
    sheets, loose = expected_copies(contract)
    names = expected_bodies(sheets, loose)
    copies: dict[str, int] = defaultdict(int)
    for sheet in sheets:
        for part, count in sheet["copies"].items():
            copies[part] += count
    for part, count in loose.items():
        copies[part] += count
    if report.get("sheets") != sheets or report.get("loose") != loose or report.get("copies") != dict(
        sorted(copies.items())
    ) or report.get("bodies") != names:
        raise ContractError(
            "%s does not lay out the sealed tree's Sheets and loose copies (each printed Part on no "
            "Sheet, as many times as the toy uses it)" % REPORT_PATH
        )
    if report.get("step") != STEP_PATH:
        raise ContractError("%s names another STEP than %s" % (REPORT_PATH, STEP_PATH))
    step_path = (prefix / STEP_PATH).as_posix()
    content, step_sha256 = sealed(step_path, "the Made CAD project lacks %s" % STEP_PATH)
    if report.get("sha256") != step_sha256:
        raise ContractError("%s is not the layout %s names" % (STEP_PATH, REPORT_PATH))
    leaves = check_layout_step(content, names)
    _scene, scene_sha256 = sealed(SCENE_PATH, "the Made product lacks %s" % SCENE_PATH)
    removed = [item["body"] for item in not_printed(contract, catalogue)]
    return {
        "path": step_path,
        "sha256": step_sha256,
        "scene_path": SCENE_PATH,
        "scene_sha256": scene_sha256,
        "removed": removed,
        "printed_bodies": leaves,
        "removed_bodies": len(removed),
        "layout_path": report_path,
        "layout_sha256": report_sha256,
    }


__all__ = ["REPORT_PATH", "STEP_PATH", "check_layout_step", "expected_bodies", "expected_copies",
           "verify_made_print_layout"]
