#!/usr/bin/env python3
"""A kit's print layout, the STEP Factory weighs (Workshop ADR 0104 decision 4).

    kit_print.py layout <project>

Final verification runs it after the Sheet gate on every kit with an
installed Assembly Tree. It writes ``measure/kit/print.step``: every Sheet
of the tree as ``sheet()`` builds it, and one copy in its print stance of
every printed Part on no Sheet for each time the toy uses it, plus the
spares the Part declares (``spares``, 2026-11-16), laid apart on the
plane. No Bought Part is in it. Its leaves are named

- ``<Sheet id>``: the whole Sheet, its frame, runners, tags, gate bars and
  every copy fused into one connected solid, as it leaves the printer;
- ``loose/<Part id>#<n>``: the n-th loose copy of a Part, one connected
  solid (2026-11-16: a loose Part of several pieces fails the layout),

each in its filament's catalogue colour. Factory splits a STEP into its
solids and slices each one on its own, so a Sheet left in pieces would be
priced and arranged as loose Parts; fused, it is one flat plate on one bed
(schema 2, 2026-11-14). A Sheet that does not fuse into one connected solid
fails: some copy or gate touches nothing. ``measure/kit/print.json``
records the file's sha256, the tree it was laid out for and the copies it
holds. The host checks both against the sealed tree before Make is
accepted, and Release ships the file under ``parts/``, the one set Factory
prices. A failure prints one ``FAIL`` line and exits 1.

It also writes ``measure/kit/scene.step`` (2026-11-23): the toy's assembly
STEP without the Bought Part bodies ``measure/not-printed.json`` lists, every
printed body exactly as the scene holds it. Release ships it as the root
``assembled.step`` the shop's 3D viewer shows. ``print.json`` records it
under ``printed_scene`` with the scene it was cut from and what it removed.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

KIND = "kit-print-layout"
SCHEMA_VERSION = 2
STEP_PATH = "measure/kit/print.step"
REPORT_PATH = "measure/kit/print.json"
SCENE_STEP_PATH = "measure/kit/scene.step"
NOT_PRINTED_PATH = "measure/not-printed.json"
LOOSE = "loose"
GAP_MM = 10.0
ROW_MM = 600.0


def _sibling(name: str):
    spec = importlib.util.spec_from_file_location("kit_print_" + name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _colour(plan, filament: str):
    from build123d import Color

    value = str(((plan.catalogue.get("filaments") or {}).get(filament) or {}).get("hex") or "#808080")
    return Color(*(int(value.lstrip("#")[i:i + 2], 16) / 255.0 for i in (0, 2, 4)))


def expected_copies(kit: dict) -> tuple[list[dict], dict]:
    """``(sheets, loose)``: each Sheet's ``{id, filament, copies}`` from the
    tree, and ``{Part id: count}`` for every printed Part on no Sheet: the
    toy's total plus the Part's ``spares``."""

    plan = _sibling("kit_tree").Plan(kit)
    sheets = []
    on_sheet = set()
    for sheet in (kit.get("assembly_tree") or {}).get("sheets") or []:
        copies = {}
        for entry in sheet["parts"]:
            copies[entry["id"]] = copies.get(entry["id"], 0) + int(entry["count"])
            on_sheet.add(entry["id"])
        sheets.append({"id": sheet["id"], "filament": sheet["filament"], "copies": copies})
    loose = {part: plan.totals.get(part, 0) + int(plan.parts[part].get("spares", 0)) for part in sorted(plan.printed)
             if part not in on_sheet and plan.totals.get(part, 0) > 0}
    return sheets, loose


def _place(items):
    """Translate each ``(name, shape)`` group onto the plane in rows."""

    from build123d import Pos

    x = y = row = 0.0
    placed = []
    for group in items:
        boxes = [shape.bounding_box() for _name, shape, _colour in group]
        lo_x = min(b.min.X for b in boxes)
        lo_y = min(b.min.Y for b in boxes)
        lo_z = min(b.min.Z for b in boxes)
        width = max(b.max.X for b in boxes) - lo_x
        depth = max(b.max.Y for b in boxes) - lo_y
        if x > 0 and x + width > ROW_MM:
            x, y, row = 0.0, y + row + GAP_MM, 0.0
        move = Pos(x - lo_x, y - lo_y, -lo_z)
        placed.append([(name, move * shape, colour) for name, shape, colour in group])
        x += width + GAP_MM
        row = max(row, depth)
    return placed


def _solids(shape) -> list:
    return list(shape.solids()) or [shape]


def fused(sheet_id: str, pieces: list):
    """One Sheet's frame, gate bars and copies fused into one connected
    solid, or ValueError naming how many pieces it stays in."""

    sheet = pieces[0].fuse(*pieces[1:]) if len(pieces) > 1 else pieces[0]
    solids = sheet.solids()
    if len(solids) != 1 or outer_shells(solids[0]) != 1:
        raise ValueError("Sheet %s does not fuse into one connected solid but %d piece(s): join every runner "
                         "into one frame and every copy to it by its gates"
                         % (sheet_id, max(len(solids), sum(outer_shells(s) for s in solids))))
    return solids[0]


def outer_shells(solid) -> int:
    """Shells of ``solid`` that bound material outward; a void does not count."""

    return _sibling("kit_sheets").outer_shells(solid)


def removed_names(requested: list, scene_names: list) -> dict:
    """``{scene leaf name: not-printed body}``: each not-printed body
    ``<Part>#<n>`` matched to exactly one scene leaf. A Part the scene holds
    once may be written without its ``#1``."""

    counts = {}
    for name in scene_names:
        counts[name] = counts.get(name, 0) + 1
    found, errors = {}, []
    for body in requested:
        match = body
        if body not in counts and body.endswith("#1"):
            match = body[: -len("#1")]
        if counts.get(match, 0) != 1 or match in found:
            errors.append("%s is %d leaf bodies of the scene, not one" % (body, counts.get(match, 0)))
            continue
        found[match] = body
    if errors:
        raise ValueError("the not-printed bodies do not match the assembly STEP: " + "; ".join(errors))
    return found


def printed_scene(project: Path) -> dict:
    """Write ``measure/kit/scene.step``: the assembly STEP without the
    bodies ``measure/not-printed.json`` lists. Return its record."""

    bought = _sibling("bought_model")
    scene = bought._entry_scene(project)
    listed = json.loads((project / NOT_PRINTED_PATH).read_text(encoding="utf-8"))
    requested = [str(item["body"]) for item in listed.get("bodies") or []]
    out = project / SCENE_STEP_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    if requested:
        _tool, nodes = bought._walk(bought._read_xcaf(scene))
        names = removed_names(requested, [node[3] for node in nodes if not node[4]])
        removed = bought.write_printed_only(scene, out, removed_name=lambda name: name in names)
        if sorted(removed) != sorted(names):
            raise ValueError("the printed-only scene removed %s, not exactly the not-printed bodies %s"
                             % (sorted(removed), sorted(names)))
    else:
        out.write_bytes(scene.read_bytes())
    return {"step": SCENE_STEP_PATH, "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
            "scene": scene.name, "scene_sha256": hashlib.sha256(scene.read_bytes()).hexdigest(),
            "removed": sorted(requested)}


def layout(project: Path) -> dict:
    sheets_tool = _sibling("kit_sheets")
    sheets_tool._runtime_paths()
    tree_tool = _sibling("kit_tree")
    kit = tree_tool.read_install(project)
    if not isinstance(kit, dict):
        raise ValueError("the Assembly Tree is not installed (tree/kit.json)")
    plan = tree_tool.Plan(kit)
    sheets, loose = expected_copies(kit)
    groups = []
    import contextlib
    import io

    from build123d import Compound
    from printlib import detail_build, load_entry, project_on_path

    for sheet in sheets:
        entry = project / ("sheet_%s.py" % sheet["id"])
        with project_on_path(project), contextlib.redirect_stdout(io.StringIO()), detail_build():
            built = load_entry(entry, "kit_print_sheet").sheet()
        colour = _colour(plan, sheet["filament"])
        seen = {}
        for item in built["parts"]:
            seen[item["id"]] = seen.get(item["id"], 0) + 1
        if seen != sheet["copies"]:
            raise ValueError("sheet_%s.py holds %s, not its contract copies %s: run kit_sheets.py check"
                             % (sheet["id"], seen, sheet["copies"]))
        pieces = [*_solids(built["frame"]),
                  *[solid for item in built["parts"]
                    for shape in (item["shape"], *(g["shape"] for g in item["gates"])) for solid in _solids(shape)]]
        groups.append([(sheet["id"], fused(sheet["id"], pieces), colour)])
    shapes, fails = sheets_tool.print_shapes(project, plan)
    if fails:
        raise ValueError("; ".join(fails))
    for part, count in loose.items():
        if part not in shapes:
            raise ValueError("no print_parts() shape for loose Part %s" % part)
        found = sheets_tool.pieces(shapes[part])
        if found != 1:
            raise ValueError("loose Part %s is %d solids, not one connected solid: join its pieces into one "
                             "body, or Factory splits them apart and prints the strays" % (part, found))
        colour = _colour(plan, plan.parts[part]["filament"])
        for n in range(1, count + 1):
            groups.append([("%s/%s#%d" % (LOOSE, part, n), shapes[part], colour)])
    children, names = [], []
    for group in _place(groups):
        for name, shape, colour in group:
            shape.label, shape.color = name, colour
            children.append(shape)
            names.append(name)
    root = Compound(children=children)
    root.label = "print"
    path = project / STEP_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    from cadgen.step_export import export_build123d_step_file

    export_build123d_step_file(root, path)
    copies = {}
    for sheet in sheets:
        for part, count in sheet["copies"].items():
            copies[part] = copies.get(part, 0) + count
    for part, count in loose.items():
        copies[part] = copies.get(part, 0) + count
    report = {"kind": KIND, "schema_version": SCHEMA_VERSION, "tree_sha256": tree_tool.tree_digest(kit),
              "step": STEP_PATH, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "sheets": sheets, "loose": loose, "copies": dict(sorted(copies.items())),
              "bodies": sorted(names), "printed_scene": printed_scene(project)}
    (project / REPORT_PATH).write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] != "layout":
        print("usage: kit_print.py layout <project>", file=sys.stderr)
        return 2
    try:
        report = layout(Path(args[1]).resolve())
    except Exception as error:  # noqa: BLE001 - the CLI boundary
        print("FAIL kit print layout: %s: %s" % (type(error).__name__, str(error)[:400]))
        return 1
    print("kit print layout: %d bodies, %d Sheet(s), %d loose Part(s) -> %s; printed-only scene -> %s"
          % (len(report["bodies"]), len(report["sheets"]), len(report["loose"]), STEP_PATH, SCENE_STEP_PATH))
    return 0


if __name__ == "__main__":
    try:  # timed in the Workshop timing ledger (ADR 0106); it only records
        from workshop.runtime.timing_ledger import script_main
    except Exception:  # noqa: BLE001 - a bare run copy has no ledger
        script_main = None
    raise SystemExit(main() if script_main is None else script_main('kit_print', main))
