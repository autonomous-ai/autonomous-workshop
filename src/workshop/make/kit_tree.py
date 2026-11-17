"""The host's check of a Made kit's Assembly Tree gates (ADR 0092 decision 8).

Make installs a schema 7 Design Contract's Assembly Tree into its CAD project
(``tree/kit.json``: the tree, the geometries, the Print Pieces and the
catalogue entries the Wish sealed beside the contract), checks each
Component's Parts in its component rounds and the joins across Components in
assembly rounds, and final verification writes ``measure/tree-report.json``.
Before Make is accepted the host checks, on the exact sealed bytes and
without rebuilding any geometry (ADR 0061), that

- the installed tree is the one the sealed contract and catalogue give;
- the final report is for that tree, passed, and reconciled every leaf:
  every printed Part, every Bought Part and every Print Piece;
- no contract tree defect of that tree is on record: in the pilot a
  contract tree defect stops the run for the owner (ADR 0092 decision 10),
  so a Make that carries one is never accepted. A labelling slip (built
  bodies that do not match a sound tree, owner decision Q28) is never
  recorded there: it fails its round and the final report, and is repaired;
- ``measure/not-printed.json`` lists exactly the Bought Part bodies the tree
  gives, each with its catalogue id, in the reserved not-printed colour
  (owner decision Q29); its bodies join the account the receipt carries.
- every snap step across Components (ADR 0104 amendment 2026-11-17) has a
  passing record in the final report for each copy, for the sealed Part,
  catch and region, no deeper than its catch, clear at its seat and
  overlapping on the way in (:func:`check_snaps`).

The run-local tool is ``make-round/scripts/kit_tree.py``; the install
document here is built the same way, and a test holds the two together.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from workshop.errors import ContractError
from workshop.wish.catalogues import BOUGHT_PART_HEX

TREE_SCHEMA_VERSION = 7
INSTALL_PATH = "tree/kit.json"
REPORT_PATH = "measure/tree-report.json"
DEFECTS_PATH = "measure/tree-defects.json"
NOT_PRINTED_PATH = "measure/not-printed.json"
NOT_PRINTED_KIND = "kit-not-printed"
KIT_KIND = "kit-tree"
REPORT_KIND = "kit-tree-report"
INSTALL_SCHEMA = 1


def has_assembly_tree(contract: Any) -> bool:
    """Whether a sealed Design Contract is a kit: schema 7 always has an
    Assembly Tree (ADR 0092), and a schema 8 contract has one when it is a
    kit (ADR 0093). No earlier schema has one."""

    if not isinstance(contract, Mapping):
        return False
    schema = contract.get("schema_version")
    return (
        type(schema) is int and schema >= TREE_SCHEMA_VERSION
        and isinstance(contract.get("assembly_tree"), Mapping)
    )


def install_document(contract: Mapping[str, Any], catalogue: Any) -> dict[str, Any]:
    """The install a sealed schema 7 contract and its catalogue snapshot give."""

    section = contract.get("print")
    return {
        "kind": KIT_KIND,
        "schema_version": INSTALL_SCHEMA,
        "assembly_tree": contract.get("assembly_tree"),
        "geometries": contract.get("geometries"),
        "pieces": (section.get("pieces") if isinstance(section, Mapping) else None) or [],
        "catalogue": catalogue,
    }


def tree_digest(document: Mapping[str, Any]) -> str:
    data = (json.dumps(document, indent=1, sort_keys=True) + "\n").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _leaves(contract: Mapping[str, Any]) -> dict[str, list[str]]:
    tree = contract["assembly_tree"]
    section = contract.get("print")
    pieces = section.get("pieces") if isinstance(section, Mapping) else None
    return {
        "printed": sorted(item["id"] for item in tree["parts"] if "filament" in item),
        "bought": sorted(item["id"] for item in tree["parts"] if "bought" in item),
        "pieces": sorted(item["id"] for item in pieces or ()),
    }


def tree_totals(tree: Mapping[str, Any]) -> dict[str, int]:
    """How many times the toy uses each node of an Assembly Tree, from the
    tree alone, as the run-local ``Plan.totals`` counts it."""

    steps = list(tree["steps"])
    totals: dict[str, int] = {steps[-1]["id"]: int(steps[-1]["count"])}
    for item in reversed(steps):
        node = item["id"]
        totals.setdefault(node, int(item["count"]))
        for entry in item["inputs"]:
            totals[entry["id"]] = totals[node] * int(entry.get("count", 1))
    return totals


# How far a snap's measured depth may pass its declared catch: the run-local
# tool's SNAP_TOLERANCE_MM, float noise only. Its seat is held to the sweep's
# 0.001 mm3 contact limit.
SNAP_TOLERANCE_MM = 1e-3
SEATED_MM3 = 0.001


def _snap_spans(tree: Mapping[str, Any]) -> dict[str, tuple[Mapping[str, Any], str]]:
    """Every snap step final verification sweeps, the ones across
    Components: step id -> (its snap, the input that snaps in). A snap
    wholly inside one Component is checked in that Component's rounds."""

    children = {item["id"]: [entry["id"] for entry in item["inputs"]] for item in tree["steps"]}
    owner = {part: item["geometry"] for item in tree["components"] for part in item["parts"]}

    def leaves(node: str) -> set[str]:
        if node not in children:
            return {node}
        return set().union(*(leaves(child) for child in children[node]))

    found = {}
    for item in tree["steps"]:
        if item.get("joint") != "snap":
            continue
        if len({owner[leaf] for leaf in leaves(item["id"]) if leaf in owner}) < 2:
            continue
        snap = item["snap"]
        moving = next(entry["id"] for entry in item["inputs"][1:] if snap["part"] in leaves(entry["id"]))
        found[item["id"]] = (snap, moving)
    return found


def check_snaps(tree: Mapping[str, Any], records: Any) -> None:
    """The host's mirror of the snap rule (ADR 0104 amendment 2026-11-17) on
    the final report, without geometry: every copy of every snap across
    Components has its record, for the sealed Part, catch and region; it
    overlapped its catch on the way in, no deeper than the catch; its seat is
    clear; and no other step was let overlap. Raises ContractError."""

    spans = _snap_spans(tree)
    totals = tree_totals(tree)
    records = records or []
    if not isinstance(records, list) or not all(isinstance(item, Mapping) for item in records):
        raise ContractError("%s lists its snaps wrongly" % REPORT_PATH)
    for record in records:
        if record.get("step") not in spans:
            raise ContractError("%s lets %s overlap as a snap, but the sealed tree declares no snap there"
                                % (REPORT_PATH, record.get("step")))
    for step, (snap, moving) in sorted(spans.items()):
        mine = [record for record in records if record.get("step") == step]
        if len(mine) != totals[moving]:
            raise ContractError("%s records %d snap pass(es) for %s, not one for each of its %d %s"
                                % (REPORT_PATH, len(mine), step, totals[moving], moving))
        for record in mine:
            label = "%s: %s" % (step, record.get("input"))
            if (record.get("part"), record.get("catch"), record.get("catch_mm"), record.get("region_mm")) != (
                    snap["part"], snap["catch"], snap["catch_mm"], snap.get("region_mm")):
                raise ContractError("%s's snap record is not the sealed snap of %s into %s"
                                    % (label, snap["part"], snap["catch"]))
            depth, seated, seen = record.get("max_depth_mm"), record.get("seated_mm3"), record.get("overlapping_samples")
            if record.get("verdict") != "PASS" or not all(
                    isinstance(v, (int, float)) and not isinstance(v, bool) for v in (depth, seated, seen)):
                raise ContractError("%s's snap did not pass" % label)
            if seen < 1:
                raise ContractError("%s never overlapped its catch %s: it is no snap" % (label, snap["catch"]))
            if depth > snap["catch_mm"] + SNAP_TOLERANCE_MM:
                raise ContractError("%s passed %s %.3f mm deep, deeper than its sealed %.3g mm catch"
                                    % (label, snap["catch"], depth, snap["catch_mm"]))
            if seated > SEATED_MM3:
                raise ContractError("%s is not clear of %s at its seat (%.4g mm3)" % (label, snap["catch"], seated))


def not_printed(contract: Mapping[str, Any], catalogue: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Every Bought Part body of the toy, ``<id>#n`` across the whole toy, as
    the run-local ``kit_tree.not_printed`` lists it: the count is the Part's
    occurrences under the root, from the tree alone."""

    tree = contract["assembly_tree"]
    totals = tree_totals(tree)
    owner = {part: item["geometry"] for item in tree["components"] for part in item["parts"]}
    entries = catalogue.get("bought_parts") or {}
    found = []
    for part in sorted(item["id"] for item in tree["parts"] if "bought" in item):
        catalogue_id = next(item["bought"] for item in tree["parts"] if item["id"] == part)
        for n in range(1, totals.get(part, 0) + 1):
            found.append({"body": "%s#%d" % (part, n), "part": part, "bought": catalogue_id,
                          "name": str((entries.get(catalogue_id) or {}).get("name", "")),
                          "component": owner.get(part)})
    return found


def verify_made_tree(
    run_root: Path,
    made: Any,
    contract: Mapping[str, Any] | None,
    catalogue: Any,
) -> dict[str, Any] | None:
    """The accepted tree's account, or None for a contract without an Assembly Tree.
    ``catalogue`` is the Wish's sealed ``kit_catalogue``. Raises
    ContractError naming what is wrong."""

    if not has_assembly_tree(contract):
        return None
    if not isinstance(catalogue, Mapping):
        raise ContractError("the Wish seals no kit_catalogue beside its kit Design Contract")
    product_root = Path(run_root).joinpath(*PurePosixPath(made.product_root).parts)
    entries = {entry.path: entry for entry in made.product_manifest.entries}
    prefix = PurePosixPath(made.cad_project_path)

    def json_file(relative: str, missing: str) -> Any:
        path = (prefix / relative).as_posix()
        entry = entries.get(path)
        if entry is None:
            raise ContractError(missing)
        content = product_root.joinpath(*PurePosixPath(path).parts).read_bytes()
        if len(content) != entry.bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
            raise ContractError("the kit tree file %s differs from the Made manifest" % relative)
        try:
            return json.loads(content.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise ContractError("the kit tree file %s is not JSON" % relative) from exc

    expected = install_document(contract, catalogue)
    installed = json_file(INSTALL_PATH, "the Made CAD project lacks its installed Assembly Tree, %s" % INSTALL_PATH)
    if installed != expected:
        raise ContractError("%s is not the sealed Design Contract's Assembly Tree" % INSTALL_PATH)
    digest = tree_digest(expected)
    if (prefix / DEFECTS_PATH).as_posix() in entries:
        record = json_file(DEFECTS_PATH, "")
        if isinstance(record, Mapping) and record.get("tree_sha256") == digest:
            raise ContractError(
                "a tree defect of this Assembly Tree is on record (ADR 0092 decision 10): %s"
                % str(record.get("need", ""))[:400]
            )
    report = json_file(REPORT_PATH, "final verification wrote no %s for the Assembly Tree" % REPORT_PATH)
    if not isinstance(report, Mapping) or report.get("kind") != REPORT_KIND or report.get("scope") != "final":
        raise ContractError("%s is not a final kit tree report" % REPORT_PATH)
    if report.get("tree_sha256") != digest:
        raise ContractError("%s checked another Assembly Tree than the sealed one" % REPORT_PATH)
    defects, failures = report.get("defects"), report.get("failures")
    if report.get("verdict") != "PASS" or defects or failures:
        shown = "; ".join(
            [str(item.get("detail", item)) if isinstance(item, Mapping) else str(item) for item in defects or ()]
            + [str(item) for item in failures or ()]
        )[:400] or "it did not pass"
        raise ContractError("the Assembly Tree gates did not pass: %s" % shown)
    if report.get("slips"):
        raise ContractError("the Assembly Tree gates did not pass: a labelling slip is open")
    check_snaps(contract["assembly_tree"], report.get("snaps"))
    leaves = _leaves(contract)
    if report.get("leaves") != leaves:
        raise ContractError("%s does not account for every leaf of the sealed tree" % REPORT_PATH)
    # Q29: the Bought Part bodies, bought and never printed, listed beside
    # the STEP for the receipt and the Release archive.
    bodies = not_printed(contract, catalogue)
    listed = json_file(NOT_PRINTED_PATH, "final verification wrote no %s for the Bought Parts" % NOT_PRINTED_PATH)
    if (
        not isinstance(listed, Mapping)
        or listed.get("kind") != NOT_PRINTED_KIND
        or listed.get("tree_sha256") != digest
        or listed.get("colour") != BOUGHT_PART_HEX
        or listed.get("bodies") != bodies
        or report.get("not_printed") != bodies
    ):
        raise ContractError("%s is not the sealed tree's list of Bought Part bodies" % NOT_PRINTED_PATH)
    conditions = report.get("conditions") or []
    return {
        "printed_parts": len(leaves["printed"]),
        "bought_parts": len(leaves["bought"]),
        "print_pieces": len(leaves["pieces"]),
        "insertions_across_components": sum(
            len((item.get("inputs") or {}).get("steps") or ()) for item in conditions if isinstance(item, Mapping)
        ),
        "lead_routes_across_components": len(report.get("routes") or []),
        "report": (prefix / REPORT_PATH).as_posix(),
        "not_printed": {
            "path": (prefix / NOT_PRINTED_PATH).as_posix(),
            "colour": BOUGHT_PART_HEX,
            "bodies": [{"body": item["body"], "bought": item["bought"]} for item in bodies],
        },
    }


__all__ = ["check_snaps", "install_document", "not_printed", "tree_digest", "tree_totals", "verify_made_tree"]
