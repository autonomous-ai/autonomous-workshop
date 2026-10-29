#!/usr/bin/env python3
"""The model half of the Print Sheet gate for one part entry (ADR 0091).

    check_print_pieces.py <part_<geometry>.step.py | cad-project>

Every Print Piece the installed print section (`<cad-project>/print/
pieces.json`) lands on this part's Unique Geometry must have a print feature
in the part: a recess for a `flat` or `sticker` piece, a slot for a `stand`
card, a checked block, ball or fold face for a `wrap`, `sphere` or `fold`
piece. Each feature is made by a print-details call that reads the piece's
sizes from the contract and tags what it made with the piece and the digest
of its contract entry. This gate builds the part (or reads the round's kept
B-rep), then for every tag checks that

- the piece is still in the contract with the same entry (no stale size);
- the piece lands on this part (under a schema 7 tree, ADR 0092: on one of
  its printed Parts or on a Sub-assembly inside its Component, or on a
  Sub-assembly across Components that includes it, where assembly rounds
  and final verification need exactly one part to carry it; a piece on a
  Bought Part has no printed feature and passes as such);
- a recess or slot is still open: at most 1 % of it is solid in the
  finished part;
- a block or ball is still in the part: at least 98 % of it is solid;
- a fold face is still on the part's surface.

It prints one PASS or FAIL line per piece and exits 0 when every hosted
piece passes, 1 when any fails, and 0 with SKIP when the part hosts none.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CAD_SCRIPTS = Path(__file__).resolve().parents[2] / "cad" / "scripts"
HERE = Path(__file__).resolve().parent
OPEN_LIMIT = 0.01
PRESENT_LIMIT = 0.98
ON_SURFACE_MM = 0.05


def _library():
    sys.path.insert(0, str(HERE))
    import print_details

    return print_details


# ADR 0092: under a schema 7 Design Contract a piece's `on` names a printed
# Part, a Bought Part or a Sub-assembly, and the installed Assembly Tree
# (`tree/kit.json`, make-round's kit_tree.py) says which Component carries it.
KIT_TREE = Path(__file__).resolve().parents[2] / "make-round" / "scripts" / "kit_tree.py"
KIT_INSTALL = Path("tree") / "kit.json"


def kit_hosts(project: Path, role: str) -> dict | None:
    """``{"hosted", "bought", "spanning"}`` piece ids for this Component
    under a schema 7 tree, or None without one."""

    path = project / KIT_INSTALL
    if not path.is_file() or not KIT_TREE.is_file():
        return None
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_print_pieces_kit_tree", KIT_TREE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plan = module.paper_plan(json.loads(path.read_text(encoding="utf-8")))
    return {"hosted": set(plan["hosted"].get(role, ())), "bought": set(plan["bought"].get(role, ())),
            "spanning": {piece for piece, owners in plan["spanning"].items() if role in owners}}


def hosted_pieces(section: dict, role: str, kit: dict | None = None) -> list:
    if kit is not None:
        return [piece for piece in section["pieces"] if piece["id"] in kit["hosted"]]
    return [piece for piece in section["pieces"] if str(piece["on"]).split("#")[0] == role]


def carries(spec: dict, role: str, kit: dict | None) -> bool:
    """Whether this Component's part may carry the piece's feature."""

    if kit is not None:
        return spec["id"] in kit["hosted"] or spec["id"] in kit["spanning"]
    return str(spec["on"]).split("#")[0] == role


def read_tag(tag: dict) -> tuple | None:
    """``(kind, piece, digest)`` from a print tag's name, else None."""

    parts = str(tag.get("name", "")).split(":")
    if len(parts) != 3 or parts[0] != tag.get("kind"):
        return None
    return tuple(parts)


def common_volume(shape, other) -> float:
    """The volume ``shape`` and ``other`` share; an empty common is None in
    build123d."""

    common = shape & other
    return 0.0 if common is None else float(common.volume)


def measure(kind: str, tag_shape, shape) -> str | None:
    """Why the finished part no longer carries this feature, else None."""

    if kind in ("print-recess", "print-slot"):
        volume = tag_shape.volume
        filled = common_volume(shape, tag_shape) if volume > 0 else 0.0
        if volume <= 0 or filled > OPEN_LIMIT * volume:
            return "its %s is filled again: %.0f%% of it is solid in the finished part" % (
                kind.removeprefix("print-"), 100.0 * filled / volume if volume > 0 else 100.0)
        return None
    if kind in ("print-block", "print-sphere"):
        volume = tag_shape.volume
        kept = common_volume(shape, tag_shape) if volume > 0 else 0.0
        if volume <= 0 or kept < PRESENT_LIMIT * volume:
            return "its %s is not in the finished part: %.0f%% of it is solid" % (
                kind.removeprefix("print-"), 100.0 * kept / volume if volume > 0 else 0.0)
        return None
    if kind == "print-fold":
        from build123d import Vertex

        if shape.distance_to(Vertex(tag_shape.center())) > ON_SURFACE_MM:
            return "its page face is no longer on the finished part's surface"
        return None
    return "an unknown print feature %s" % kind


def check(entry: Path) -> tuple[list, list]:
    """``(passes, failures)`` for one part entry; both empty when it hosts
    no piece."""

    sys.path.insert(0, str(CAD_SCRIPTS))
    import printlib

    library = _library()
    role = printlib.entry_role(entry)
    project = entry.parent
    if not (project / library.PRINT_DIR / library.PRINT_PIECES_FILE).is_file():
        return [], []
    section = library.print_pieces(project)["print"]
    pieces = {piece["id"]: piece for piece in section["pieces"]}
    kit = kit_hosts(project, role)
    hosted = hosted_pieces(section, role, kit)
    shape = printlib.entry_shape(entry, role)
    tags = [tag for tag in printlib.feature_tags() if tag.get("kind") in library.PRINT_TAG_KINDS]
    bought = sorted(kit["bought"]) if kit is not None else []
    if not hosted and not tags and not bought:
        return [], []
    passes, failures = [], []
    for piece_id in bought:
        # A piece on a Bought Part lands on what the maker buys: no printed
        # feature can carry it, so none is required or allowed.
        passes.append("%s: on Bought Part %s; no printed feature carries it"
                      % (piece_id, pieces[piece_id]["on"]))
    seen = set()
    for tag in tags:
        read = read_tag(tag)
        if read is None:
            failures.append("%s at %s carries no piece id" % (tag.get("kind"), tag.get("site")))
            continue
        kind, piece_id, digest = read
        spec = pieces.get(piece_id)
        where = "%s at %s" % (kind, tag.get("site"))
        if spec is None:
            failures.append("%s: %s names a piece the contract does not have" % (piece_id, where))
            continue
        if library.piece_digest(spec) != digest:
            failures.append("%s: %s was made from another contract entry; rebuild it from the "
                            "installed print/pieces.json" % (piece_id, where))
            continue
        if not carries(spec, role, kit):
            failures.append("%s: %s is in part_%s, but the contract puts it on %s"
                            % (piece_id, where, role, spec["on"]))
            continue
        why = measure(kind, tag["shape"], shape)
        if why is not None:
            failures.append("%s: %s; %s" % (piece_id, where, why))
            continue
        seen.add(piece_id)
        passes.append("%s: %s" % (piece_id, where))
    for piece in hosted:
        if piece["id"] not in seen and not any(f.startswith(piece["id"] + ":") for f in failures):
            failures.append("%s: part_%s makes no print feature for this %s piece; add it with "
                            "pd.%s(...)" % (piece["id"], role, piece["way"],
                                            library._PRINT_CALLS[piece["way"]]))
    return passes, failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("entry", help="a part_*.step.py entry, or a project holding exactly one")
    args = parser.parse_args(argv)
    sys.path.insert(0, str(CAD_SCRIPTS))
    import printlib

    try:
        entry = printlib.resolve_single_entry(args.entry)
    except SystemExit as exc:
        print("check_print_pieces: %s" % exc, file=sys.stderr)
        return 2
    passes, failures = check(entry)
    role = printlib.entry_role(entry)
    if not passes and not failures:
        print("SKIP %s hosts no Print Piece" % role)
        return 0
    for line in passes:
        print("PASS %s" % line)
    for line in failures:
        print("FAIL %s" % line)
    print("check_print_pieces %s: %s, %d piece feature(s) pass, %d fail"
          % (role, "FAIL" if failures else "PASS", len(passes), len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
