#!/usr/bin/env python3
"""A kit's print layout, the STEP Factory weighs (Workshop ADR 0104 decision 4).

    kit_print.py layout <project>

Final verification runs it after the Sheet gate on every kit with an
installed Assembly Tree. It writes ``measure/kit/print.step``: every Sheet
of the tree as ``sheet()`` builds it, and one copy in its print stance of
every printed Part on no Sheet for each time the toy uses it, laid apart on
the plane. No Bought Part is in it. Its leaves are named

- ``<Sheet id>/frame``: the frame with its runners, tags and gate bars;
- ``<Sheet id>/<Part id>#<n>``: the Sheet's n-th copy of a Part;
- ``loose/<Part id>#<n>``: the n-th loose copy of a Part,

each in its filament's catalogue colour. ``measure/kit/print.json``
records the file's sha256, the tree it was laid out for and the copies it
holds. The host checks both against the sealed tree before Make is
accepted, and Release ships the file as the Factory primary. A failure
prints one ``FAIL`` line and exits 1.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

KIND = "kit-print-layout"
SCHEMA_VERSION = 1
STEP_PATH = "measure/kit/print.step"
REPORT_PATH = "measure/kit/print.json"
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
    tree, and ``{Part id: count}`` for every printed Part on no Sheet."""

    plan = _sibling("kit_tree").Plan(kit)
    sheets = []
    on_sheet = set()
    for sheet in (kit.get("assembly_tree") or {}).get("sheets") or []:
        copies = {}
        for entry in sheet["parts"]:
            copies[entry["id"]] = copies.get(entry["id"], 0) + int(entry["count"])
            on_sheet.add(entry["id"])
        sheets.append({"id": sheet["id"], "filament": sheet["filament"], "copies": copies})
    loose = {part: plan.totals.get(part, 0) for part in sorted(plan.printed)
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
        frame = Compound([built["frame"], *[g["shape"] for item in built["parts"] for g in item["gates"]]])
        group, seen = [("%s/frame" % sheet["id"], frame, colour)], {}
        for item in built["parts"]:
            seen[item["id"]] = seen.get(item["id"], 0) + 1
            group.append(("%s/%s#%d" % (sheet["id"], item["id"], seen[item["id"]]), item["shape"], colour))
        if seen != sheet["copies"]:
            raise ValueError("sheet_%s.py holds %s, not its contract copies %s: run kit_sheets.py check"
                             % (sheet["id"], seen, sheet["copies"]))
        groups.append(group)
    shapes, fails = sheets_tool.print_shapes(project, plan)
    if fails:
        raise ValueError("; ".join(fails))
    for part, count in loose.items():
        if part not in shapes:
            raise ValueError("no print_parts() shape for loose Part %s" % part)
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
              "bodies": sorted(names)}
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
    print("kit print layout: %d bodies, %d Sheet(s), %d loose Part(s) -> %s"
          % (len(report["bodies"]), len(report["sheets"]), len(report["loose"]), STEP_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
