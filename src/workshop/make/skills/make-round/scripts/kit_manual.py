#!/usr/bin/env python3
"""Write a schema 7 kit's Manual from its Assembly Tree (ADR 0092 decision 9).

    kit_manual.py <cad-project> [--company FILE] [--json]
    kit_manual.py --self-check

The Manual is the Rolife-style assembly book that ships in the box. This tool
writes it deterministically from the installed Assembly Tree
(``tree/kit.json``, the sealed contract's tree, Print Pieces and catalogue
entries) and from the built geometry, so the same tree and the same build give
the same bytes. No agent writes or places anything in it. Every sentence a
buyer reads is the contract's own short English (each step's ``text``, each
Check Step's ``text``, each lead's ``exit``), a name from the contract or the
sealed catalogue, or a fixed label of this tool. The company facts (the
after-sales contact and the safety warnings) come from the company
configuration, ``make-round/company.json``.

It writes ``manual/manual.pdf`` and ``manual/manual.json`` (the layout, every
section's material list and every check) into the CAD project. Final
verification runs it after the tree gates and the Print Sheets; the host
checks the report and the PDF's hash before Make is accepted, and Release
ships the PDF beside the STEP files and ``print/``.

What the Manual holds, in order
-------------------------------
1. **Front page.** The included tools: the tree's ``materials`` (tweezers,
   foam tape and dots, glue), and a screwdriver whenever a Bought Part is a
   screw (a fastener with a ``thread`` size) or a power source. The
   self-prepared items: scissors when there are Print Pieces, and batteries
   for each power source. The company's warnings (small parts always,
   batteries with a power source) and "check all Parts first". Printed jigs
   are not in the tree's schema yet, so none is listed.
2. **Check Steps** (``assembly_tree.checks``), each with the Parts it
   connects and a picture of them where they sit in the toy.
3. **One section per Component**, in the Manual order of its first step: its
   bag (bags are numbered by section), a picture of the finished Component,
   a three-column material list (printed / paper / bought) with counts per
   toy, a 1:1 gauge for every Bought Part with a fixed length (wire, pins,
   tubes: a catalogue ``length`` size), and its steps.
4. **One join section per step across Components**, in Manual order, each
   with its own material list.
5. **Completion picture**, and the after-sales contact.

Every step is drawn as one panel: its id (the Sub-assembly label every later
step uses), its output, how many to make, its joint, its inputs (an earlier
Sub-assembly by its label; a Print Piece with its printed-side or peel mark),
its instruction, where each enclosed lead comes out, and an exploded picture.

Pictures
--------
Every picture is the build's own bodies, in the assembly frame, shaded by
``render_review``'s software rasteriser from one fixed camera. A step's
exploded picture shows copy 1 of its Sub-assembly with every moving input
(every input after the first of a joining or ``paper`` step) drawn backed out
along its declared insertion direction: as far as the tree gate starts its
sweep (wholly outside the rest of the Sub-assembly, plus 1 mm) plus a quarter
of the Sub-assembly's size, with an arrow to its seat. Enclosed leads are
drawn along their declared routes. Print Pieces have no body, so a picture
never shows paper; the panel names the piece instead.

A step marked ``error_prone`` adds a correct/incorrect pair. The incorrect
picture is defined deterministically as the same exploded view with every
moving input turned half a turn about the axis across its insertion
direction (the cross product of the direction and the world axis least
aligned with it), about the centre of its bounds. When that turn leaves the
picture unchanged (fewer than ``SAME_PICTURE_FRACTION`` of its pixels differ),
the input looks the same either way round, and the pair is replaced by a
fixed placeholder; so is a step with no moving body.

The geometry is an injected dependency. ``meshes`` maps every body's scope
key (``A05-leg#3``, numbered as ``kit_tree.py`` numbers them) to a triangle
mesh. The real source builds every Component from its source, placed by its
``assembly_pose``, exactly as the final tree gate built and reconciled it
(``kit_tree.CadGeometry``), and tessellates each body; tests pass meshes of
their own.

Exit status: 0 written, 1 the tree cannot be written as a Manual (a step
without an instruction, an unknown Part id, a leaf in no or two material
lists; the report is written, the PDF is not), 2 bad usage.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import math
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
KIT_TREE_SCRIPT = SCRIPTS / "kit_tree.py"
RENDER_REVIEW_SCRIPT = SCRIPTS.parents[1] / "cad" / "scripts" / "render_review"
COMPANY_FILE = SCRIPTS.parent / "company.json"

KIND = "kit-manual"
SCHEMA_VERSION = 1
COMPANY_KIND = "workshop-company"
MANUAL_DIR = "manual"
PDF_NAME = "manual.pdf"
REPORT_NAME = "manual.json"

CAMERA = (-45.0, 35.264)          # render_review's iso view
PANEL_PX = 640
PAIR_PX = 400
HEADER_PX = 560
PAD = 0.06
EXPLODE_FRACTION = 0.25
SAME_PICTURE_FRACTION = 0.002
TESSELLATION_MM = 0.08
BOUGHT_GREY = (150, 150, 150)

PAGE_MM = (210.0, 297.0)
MARGIN_MM = 12.0
FOOTER_MM = 14.0
LINE_MM = 4.4
ACCENT = (0.93, 0.47, 0.13)       # Rolife's orange tabs and page numbers
WRONG = (0.80, 0.12, 0.12)
RIGHT = (0.13, 0.55, 0.20)

JOINS = ("peg-socket", "tab-slot", "pin-hinge", "foam-tape", "glue")
PAPER = "paper"
SWEPT = JOINS + (PAPER,)
JOINT_LABELS = {
    "peg-socket": "Press-fit", "tab-slot": "Tab into slot", "pin-hinge": "Pin hinge",
    "foam-tape": "Foam tape", "glue": "Glue", "paper": "Paper", "fold": "Fold", "cut": "Cut",
    "bend": "Bend", "roll": "Roll", "leads": "Join the leads",
}
CHECK_PARTS_FIRST = "Check all Parts against the material lists before you start."
PEEL = "peel"
PRINTED_SIDE = "printed side out"


class UsageError(Exception):
    """The project cannot be read at all."""


def _load(name: str, path: Path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


_MODULES: dict = {}


def kit_tree():
    if "kit_tree" not in _MODULES:
        _MODULES["kit_tree"] = _load("kit_manual_kit_tree", KIT_TREE_SCRIPT)
    return _MODULES["kit_tree"]


def render_review():
    if "render_review" not in _MODULES:
        _MODULES["render_review"] = _load("kit_manual_render_review", RENDER_REVIEW_SCRIPT)
    return _MODULES["render_review"]


# ---------------------------------------------------------------------------
# company configuration


def load_company(path: Path) -> dict:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise UsageError("the company configuration %s cannot be read: %s" % (path, exc)) from exc
    after = document.get("after_sales") if isinstance(document, dict) else None
    warnings = document.get("warnings") if isinstance(document, dict) else None
    if (
        not isinstance(document, dict) or document.get("kind") != COMPANY_KIND
        or not isinstance(document.get("name"), str)
        or not isinstance(after, dict) or not isinstance(after.get("contact"), str)
        or not after["contact"].strip() or not isinstance(after.get("confirmed"), bool)
        or not isinstance(warnings, dict)
        or not all(isinstance(warnings.get(key), str) and warnings[key].strip()
                   for key in ("small_parts", "batteries"))
    ):
        raise UsageError("%s is not a company configuration: kind %s with name, after_sales "
                         "{contact, confirmed} and warnings {small_parts, batteries}" % (path, COMPANY_KIND))
    return document


# ---------------------------------------------------------------------------
# the plan: what the Manual says, read from the tree alone


def _bought_entry(plan, part: str) -> dict:
    return (plan.catalogue.get("bought_parts") or {}).get(plan.parts[part].get("bought"), {}) or {}


def _category(plan, part: str) -> str | None:
    return _bought_entry(plan, part).get("category") if part in plan.bought else None


def _length_mm(entry: dict) -> float | None:
    for size in entry.get("sizes") or ():
        if isinstance(size, dict) and size.get("what") == "length" and size.get("mm"):
            value = size["mm"][0]
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
                return float(value)
    return None


def _kind(plan, leaf: str) -> str | None:
    if leaf in plan.printed:
        return "printed"
    if leaf in plan.pieces:
        return "paper"
    if leaf in plan.bought:
        return "bought"
    return None


def piece_mark(piece: dict) -> str:
    """A sticker is peeled; every other piece shows which side is printed."""

    return PEEL if piece.get("stock") == "sticker" or piece.get("way") == "sticker" else PRINTED_SIDE


def plan_manual(kit: dict, company: dict) -> dict:
    """The Manual's content and every check, without geometry. ``failures``
    lists every reason the tree cannot be written as a Manual."""

    tool = kit_tree()
    plan = tool.Plan(kit)
    tree = kit["assembly_tree"]
    failures: list[str] = []
    known = set(plan.parts) | set(plan.pieces)
    earlier: set[str] = set()
    for item in plan.steps:
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            failures.append("%s has no instruction: every step's text is the contract's own" % item["id"])
        for entry in item["inputs"]:
            child = entry["id"]
            if child not in known and child not in earlier:
                failures.append("%s takes %r, which is no Part, Print Piece or earlier step of the tree"
                                % (item["id"], child))
        earlier.add(item["id"])

    # Every step belongs to one section: its Component's, the join section
    # of a step across Components, or (a step holding no Part, such as a fold
    # of a Print Piece) the section of the step it feeds.
    sections: dict[str, dict] = {}
    order: list[str] = []
    step_section: dict[str, str] = {}

    def section_of(step: str) -> str:
        if step in step_section:
            return step_section[step]
        owners = sorted(plan.owners(step))
        if len(owners) == 1:
            key = "component:%s" % owners[0]
        elif owners:
            key = "join:%s" % step
        elif step in plan.parent:
            key = section_of(plan.parent[step][0])
        else:
            key = "join:%s" % step
        step_section[step] = key
        return key

    for item in plan.steps:
        section_of(item["id"])
    components = []
    joins = []
    for item in plan.steps:
        key = step_section[item["id"]]
        if key not in sections:
            sections[key] = {"id": key, "steps": []}
            (components if key.startswith("component:") else joins).append(key)
        sections[key]["steps"].append(item["id"])
    order = components + joins

    seen: dict[str, str] = {}
    bag = 0
    for key in order:
        section = sections[key]
        if key.startswith("component:"):
            geometry = key.split(":", 1)[1]
            info = plan.geometries.get(geometry, {})
            section["title"] = str(info.get("name") or geometry)
            section["geometry"] = geometry
            section["make"] = int(info.get("count", 1))
            section["picture"] = plan.instance_root(geometry)
        else:
            step = key.split(":", 1)[1]
            section["title"] = str(plan.step[step].get("output", step))
            section["make"] = int(plan.totals.get(step, 1))
            section["picture"] = None
        materials = {"printed": [], "paper": [], "bought": []}
        gauges = []
        for step in section["steps"]:
            for entry in plan.inputs[step]:
                leaf = entry["id"]
                kind = _kind(plan, leaf)
                if kind is None:
                    continue
                if leaf in seen:
                    failures.append("%s is in the material lists of %s and %s: every leaf is in exactly one"
                                    % (leaf, seen[leaf], key))
                    continue
                seen[leaf] = key
                materials[kind].append({"id": leaf, "count": int(plan.totals.get(leaf, 1))})
                if kind == "bought":
                    length = _length_mm(_bought_entry(plan, leaf))
                    if length is not None:
                        gauges.append({"id": leaf, "length_mm": length})
        for column in materials.values():
            column.sort(key=lambda row: row["id"])
        gauges.sort(key=lambda row: row["id"])
        section["materials"] = materials
        section["gauges"] = gauges
        if any(materials.values()):
            bag += 1
            section["bag"] = bag
        else:
            section["bag"] = None
    for leaf in sorted(set(plan.printed) | set(plan.bought) | set(plan.pieces)):
        if leaf not in seen:
            failures.append("%s is in no section's material list: it is the input of no step" % leaf)

    checks = []
    for index, item in enumerate(tree.get("checks") or ()):
        label = item.get("id", "checks[%d]" % index) if isinstance(item, dict) else "checks[%d]" % index
        if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not item["text"].strip():
            failures.append("Check Step %s has no instruction" % label)
            continue
        parts = list(item.get("parts") or ())
        for part in parts:
            if part not in plan.bought:
                failures.append("Check Step %s names %r, which is no Bought Part of the tree" % (label, part))
        checks.append({"id": label, "text": item["text"], "parts": parts,
                       "bags": sorted({sections[step_section[plan.parent[part][0]]]["bag"]
                                       for part in parts if part in plan.parent
                                       and sections[step_section[plan.parent[part][0]]]["bag"]})})

    materials = list(tree.get("materials") or ())
    snapshot = plan.catalogue.get("bought_parts") or {}
    included = [str((snapshot.get(name) or {}).get("name") or name) for name in materials]
    power = [part for part in sorted(plan.bought) if _category(plan, part) == "power"]
    screws = [part for part in sorted(plan.bought) if _category(plan, part) == "fastener"
              and any(isinstance(size, dict) and size.get("what") == "thread"
                      for size in _bought_entry(plan, part).get("sizes") or ())]
    has_driver = any((snapshot.get(name) or {}).get("category") == "tool" and "screwdriver" in name
                     for name in materials)
    if (power or screws) and not has_driver:
        included.append("Screwdriver")
    prepared = (["Scissors"] if plan.pieces else []) + [
        "Batteries for %s (%s)" % (part, _bought_entry(plan, part).get("name", part)) for part in power]
    warnings = [company["warnings"]["small_parts"]] + ([company["warnings"]["batteries"]] if power else [])

    return {
        "kind": KIND,
        "schema_version": SCHEMA_VERSION,
        "title": str(kit.get("title") or "") or plan.step[plan.root].get("output", ""),
        "tree_sha256": tool.tree_digest(kit),
        "front": {"included": included, "self_prepared": prepared, "warnings": warnings,
                  "check_first": CHECK_PARTS_FIRST},
        "checks": checks,
        "sections": [sections[key] for key in order],
        "completion": plan.root,
        "company": {"name": company["name"], "after_sales": company["after_sales"]["contact"],
                    "confirmed": company["after_sales"]["confirmed"]},
        "failures": failures,
        "passed": not failures,
    }


# ---------------------------------------------------------------------------
# pictures


class Mesh:
    """One body's triangles in the assembly frame and its colour."""

    def __init__(self, points, faces, colour) -> None:
        import numpy as np

        self.points = np.asarray(points, dtype=float)
        self.faces = np.asarray(faces, dtype=np.int64)
        self.colour = tuple(int(c) for c in colour)


def _hex(value) -> tuple | None:
    if isinstance(value, str) and len(value) == 7 and value.startswith("#"):
        try:
            return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))
        except ValueError:
            return None
    return None


def part_colour(plan, leaf: str):
    """A printed Part in its sealed filament's colour."""

    if leaf in plan.printed:
        filament = (plan.catalogue.get("filaments") or {}).get(plan.parts[leaf]["filament"]) or {}
        return _hex(filament.get("hex"))
    return None


def cad_meshes(project: Path, plan) -> dict:
    """The real geometry: every Component built from its source and placed
    by its assembly_pose, as the final tree gate built it, one mesh per body."""

    import numpy as np

    tool = kit_tree()
    review = render_review()
    review._runtime_paths()
    geometry = tool.CadGeometry(project, {key: int(item["count"]) for key, item in plan.geometries.items()})
    bodies = {}
    for role in sorted(plan.component_parts):
        for instance in range(1, int(plan.geometries[role]["count"]) + 1):
            bodies.update(tool.keyed(plan, role, geometry.component(role, instance), instance))
    meshes = {}
    for key in sorted(bodies):
        occurrences = review.tessellate_occurrences(bodies[key].shape, TESSELLATION_MM)
        points, faces, offset = [], [], 0
        for occurrence_points, occurrence_faces, _colour in occurrences:
            points.append(occurrence_points)
            faces.append(np.asarray(occurrence_faces) + offset)
            offset += len(occurrence_points)
        leaf = key.split("#", 1)[0]
        colour = part_colour(plan, leaf) or (occurrences[0][2] if leaf in plan.printed else BOUGHT_GREY)
        meshes[key] = Mesh(np.concatenate(points), np.concatenate(faces), colour)
    return meshes


def _bounds(points):
    return (tuple(float(v) for v in points.min(axis=0)), tuple(float(v) for v in points.max(axis=0)))


def _flip_axis(direction):
    """The axis a wrong-way-round input turns about: across its direction."""

    import numpy as np

    unit = np.asarray(direction, dtype=float)
    unit = unit / np.linalg.norm(unit)
    world = min(range(3), key=lambda axis: (abs(unit[axis]), axis))
    axis = np.cross(unit, np.eye(3)[world])
    return axis / np.linalg.norm(axis)


def step_scene(plan, meshes: dict, step: str, *, flipped: bool = False) -> dict | None:
    """Copy 1 of a step's Sub-assembly, exploded: ``{"bodies": [(key,
    points)], "arrows": [(start, end)], "routes": [[point]]}``, or None when
    it holds no body."""

    import numpy as np

    tool = kit_tree()
    item = plan.step[step]
    whole = ["%s#%d" % pair for pair in plan.occurrences(step, 1)]
    whole = [key for key in whole if key in meshes]
    if not whole:
        return None
    moved: dict[str, object] = {}
    arrows = []
    moving_groups = []
    if item.get("joint") in SWEPT:
        for entry in plan.inputs[step][1:]:
            if "direction" not in entry:
                continue
            per = int(entry.get("count", 1))
            for j in range(1, per + 1):
                keys = ["%s#%d" % pair for pair in plan.occurrences(entry["id"], j)]
                keys = [key for key in keys if key in meshes]
                if keys:
                    moving_groups.append((entry, keys))
    every = np.concatenate([meshes[key].points for key in whole])
    lo, hi = _bounds(every)
    span = max(hi[a] - lo[a] for a in range(3))
    for entry, keys in moving_groups:
        direction = tool._unit(entry["direction"])
        group = np.concatenate([meshes[key].points for key in keys])
        others = [key for key in whole if key not in keys]
        travel = EXPLODE_FRACTION * span
        if others:
            travel += tool.travel_mm(_bounds(group), _bounds(np.concatenate([meshes[k].points for k in others])),
                                     direction)
        shift = -np.asarray(direction) * travel
        centre = (group.min(axis=0) + group.max(axis=0)) / 2.0
        rotation = None
        if flipped:
            axis = _flip_axis(direction)
            rotation = 2.0 * np.outer(axis, axis) - np.eye(3)
        for key in keys:
            points = meshes[key].points
            if rotation is not None:
                points = (points - centre) @ rotation.T + centre
            moved[key] = points + shift
        arrows.append((centre + shift, centre))
    routes = [lead["route_mm"] for lead in item.get("leads") or ()]
    return {"bodies": [(key, moved.get(key, meshes[key].points)) for key in whole], "arrows": arrows,
            "routes": routes}


def seated_scene(meshes: dict, keys) -> dict | None:
    keys = [key for key in keys if key in meshes]
    if not keys:
        return None
    return {"bodies": [(key, meshes[key].points) for key in keys], "arrows": [], "routes": []}


def _projector(points, size: int):
    """render_review's own orthographic framing, so overlays land on the
    shaded image."""

    import numpy as np

    review = render_review()
    toward, right, up = review.camera_basis(*CAMERA)
    sx, sy = points @ right, points @ up
    width, height = float(sx.max() - sx.min()), float(sy.max() - sy.min())
    span = max(width, height, 1e-9)
    scale = (1.0 - 2.0 * PAD) * size / span
    x_offset = (size - width * scale) / 2.0 - float(sx.min()) * scale
    y_offset = (size - height * scale) / 2.0 + float(sy.max()) * scale

    def project(point):
        point = np.asarray(point, dtype=float)
        return (float(point @ right * scale + x_offset), float(y_offset - point @ up * scale))

    return project


def draw_scene(scene: dict, meshes: dict, size: int, framing=None):
    """Shade one scene with render_review and draw its arrows and lead
    routes over it. ``framing`` frames several scenes alike."""

    import numpy as np
    from PIL import ImageDraw

    review = render_review()
    occurrences = [(points, meshes[key].faces, meshes[key].colour) for key, points in scene["bodies"]]
    if framing is None:
        framing = scene_points(scene)
    image = review.render(occurrences, CAMERA[0], CAMERA[1], size, PAD, framing=framing)
    project = _projector(np.asarray(framing, dtype=float), size)
    draw = ImageDraw.Draw(image)
    width = max(2, size // 160)
    for route in scene["routes"]:
        draw.line([project(point) for point in route], fill=(200, 30, 30), width=width)
    for start, end in scene["arrows"]:
        a, b = project(start), project(end)
        draw.line([a, b], fill=(235, 120, 30), width=width)
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        if length > 1e-6:
            ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
            head = 4.0 * width
            left = (b[0] - head * ux + head * 0.5 * uy, b[1] - head * uy - head * 0.5 * ux)
            right = (b[0] - head * ux - head * 0.5 * uy, b[1] - head * uy + head * 0.5 * ux)
            draw.polygon([b, left, right], fill=(235, 120, 30))
    return image


def scene_points(scene: dict):
    import numpy as np

    blocks = [points for _key, points in scene["bodies"]]
    for route in scene["routes"]:
        blocks.append(np.asarray(route, dtype=float))
    return np.concatenate(blocks)


def _differing(a, b) -> float:
    import numpy as np

    left, right = np.asarray(a), np.asarray(b)
    return float(np.any(left != right, axis=2).mean())


def png_bytes(image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def pictures(document: dict, plan, meshes: dict) -> dict:
    """Every picture the Manual prints, by name, as PIL images. Records in
    ``document`` what each step's pictures are."""

    import numpy as np

    images: dict = {}
    steps: dict = {}
    for section in document["sections"]:
        if section.get("picture"):
            scene = seated_scene(meshes, ["%s#%d" % pair for pair in plan.occurrences(section["picture"], 1)])
            if scene is not None:
                images["section:%s" % section["id"]] = draw_scene(scene, meshes, HEADER_PX)
        for step in section["steps"]:
            record = {"picture": None, "error_picture": None}
            scene = step_scene(plan, meshes, step)
            if scene is not None:
                images["step:%s" % step] = draw_scene(scene, meshes, PANEL_PX)
                record["picture"] = "exploded"
            if plan.step[step].get("error_prone"):
                wrong = step_scene(plan, meshes, step, flipped=True)
                if scene is None or wrong is None or not scene["arrows"]:
                    record["error_picture"] = "no-moving-body"
                else:
                    framing = np.concatenate([scene_points(scene), scene_points(wrong)])
                    right = draw_scene(scene, meshes, PAIR_PX, framing)
                    flipped = draw_scene(wrong, meshes, PAIR_PX, framing)
                    if _differing(right, flipped) < SAME_PICTURE_FRACTION:
                        record["error_picture"] = "same-either-way"
                    else:
                        images["right:%s" % step] = right
                        images["wrong:%s" % step] = flipped
                        record["error_picture"] = "half-turn"
            steps[step] = record
    for check in document["checks"]:
        scene = seated_scene(meshes, ["%s#1" % part for part in check["parts"]])
        if scene is not None:
            images["check:%s" % check["id"]] = draw_scene(scene, meshes, PAIR_PX)
    scene = seated_scene(meshes, ["%s#%d" % pair for pair in plan.occurrences(document["completion"], 1)])
    if scene is not None:
        images["completion"] = draw_scene(scene, meshes, PANEL_PX)
    document["steps"] = steps
    document["pictures"] = {name: hashlib.sha256(png_bytes(image)).hexdigest()
                            for name, image in sorted(images.items())}
    return images


# ---------------------------------------------------------------------------
# the PDF


def _mm(value: float) -> float:
    return value * 72.0 / 25.4


class Pages:
    """A top-down flow of blocks on A4 pages, numbered in a circle."""

    def __init__(self, canvas) -> None:
        self.canvas = canvas
        self.number = 0
        self.y = 0.0
        self.new_page()

    @property
    def bottom(self) -> float:
        return MARGIN_MM + FOOTER_MM

    def new_page(self) -> None:
        if self.number:
            self.canvas.showPage()
        self.number += 1
        self.y = PAGE_MM[1] - MARGIN_MM
        c = self.canvas
        c.setFillColorRGB(*ACCENT)
        c.circle(_mm(PAGE_MM[0] / 2), _mm(MARGIN_MM + 3), _mm(4), stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(_mm(PAGE_MM[0] / 2), _mm(MARGIN_MM + 1.9), str(self.number))
        c.setFillColorRGB(0, 0, 0)

    def need(self, height: float) -> float:
        """The top of a block ``height`` mm tall, on a new page if needed."""

        if self.y - height < self.bottom and self.y < PAGE_MM[1] - MARGIN_MM - 1e-6:
            self.new_page()
        top = self.y
        self.y -= height
        return top


def _lines(text: str, font: str, size: float, width_mm: float) -> list[str]:
    from reportlab.lib.utils import simpleSplit

    return simpleSplit(text, font, size, _mm(width_mm)) or [""]


def _text(c, x: float, y: float, lines, font="Helvetica", size=9.0, colour=(0, 0, 0)) -> float:
    c.setFillColorRGB(*colour)
    c.setFont(font, size)
    for line in lines:
        c.drawString(_mm(x), _mm(y), line)
        y -= size * 0.3528 * 1.3
    c.setFillColorRGB(0, 0, 0)
    return y


def _image(c, readers: dict, images: dict, name: str, x: float, top: float, size_mm: float) -> bool:
    from reportlab.lib.utils import ImageReader

    if name not in images:
        return False
    if name not in readers:
        readers[name] = ImageReader(io.BytesIO(png_bytes(images[name])))
    c.drawImage(readers[name], _mm(x), _mm(top - size_mm), _mm(size_mm), _mm(size_mm))
    return True


def _placeholder(c, x: float, top: float, size_mm: float, label: str) -> None:
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setDash(_mm(1.5), _mm(1.0))
    c.rect(_mm(x), _mm(top - size_mm), _mm(size_mm), _mm(size_mm), stroke=1, fill=0)
    c.setDash()
    c.setStrokeColorRGB(0, 0, 0)
    _text(c, x + 2, top - size_mm / 2, _lines(label, "Helvetica-Oblique", 7.5, size_mm - 4),
          "Helvetica-Oblique", 7.5, (0.4, 0.4, 0.4))


def _material_rows(document: dict, plan, section: dict) -> list[list[tuple]]:
    """The three columns, each a list of (text, swatch colour or None)."""

    filaments = plan.catalogue.get("filaments") or {}
    printed = []
    for row in section["materials"]["printed"]:
        part = plan.parts[row["id"]]
        filament = filaments.get(part["filament"]) or {}
        printed.append(("%s  %s  x%d" % (row["id"], part["name"], row["count"]), _hex(filament.get("hex"))))
        printed.append(("      %s" % filament.get("name", part["filament"]), None))
    paper = []
    for row in section["materials"]["paper"]:
        piece = plan.pieces[row["id"]]
        paper.append(("%s  x%d" % (row["id"], row["count"]), None))
        paper.append(("      %s, %s" % (piece.get("stock", "?"), piece_mark(piece)), None))
    bought = []
    for row in section["materials"]["bought"]:
        entry = _bought_entry(plan, row["id"])
        bought.append(("%s  x%d" % (row["id"], row["count"]), None))
        bought.append(("      %s" % entry.get("name", plan.parts[row["id"]]["bought"]), None))
    return [printed, paper, bought]


def _input_label(plan, entry: dict) -> str:
    child = entry["id"]
    count = int(entry.get("count", 1))
    times = " x%d" % count if count > 1 else ""
    if child in plan.step:
        return "%s (%s)%s" % (child.split("-", 1)[0], plan.step[child].get("output", child), times)
    if child in plan.pieces:
        return "%s [%s]%s" % (child, piece_mark(plan.pieces[child]), times)
    return "%s%s" % (child, times)


def draw_pdf(document: dict, plan, images: dict, path: Path) -> int:
    """Write the Manual; returns its page count."""

    from reportlab.pdfgen import canvas as pdf_canvas

    c = pdf_canvas.Canvas(str(path), pagesize=(_mm(PAGE_MM[0]), _mm(PAGE_MM[1])), invariant=1)
    c.setTitle("%s Manual" % document["title"])
    c.setCreator("kit_manual.py (ADR 0092)")
    readers: dict = {}
    pages = Pages(c)
    left, width = MARGIN_MM, PAGE_MM[0] - 2 * MARGIN_MM

    # -- front page -----------------------------------------------------------
    front = document["front"]
    top = pages.need(30)
    _text(c, left, top - 12, [document["title"]], "Helvetica-Bold", 22)
    _text(c, left, top - 21, ["Assembly Manual"], "Helvetica", 13, ACCENT)
    if "completion" in images:
        top = pages.need(110)
        _image(c, readers, images, "completion", left + (width - 105) / 2, top, 105)
    for heading, rows in (("Included tools", front["included"]), ("Self-prepared", front["self_prepared"]),
                          ("Warnings", front["warnings"])):
        if not rows:
            continue
        lines = [line for row in rows for line in _lines("- " + row, "Helvetica", 10, width)]
        top = pages.need(8 + LINE_MM * len(lines))
        _text(c, left, top - 5, [heading], "Helvetica-Bold", 11, ACCENT)
        _text(c, left, top - 10, lines, "Helvetica", 10)
    top = pages.need(12)
    _text(c, left, top - 7, [front["check_first"]], "Helvetica-Bold", 11)
    legend = ["! = watch this step: compare it with the correct and incorrect pictures",
              "[%s] = peel the backing   [%s] = the printed side faces out" % (PEEL, PRINTED_SIDE),
              "S01, S02 ... = the part you made in that step"]
    top = pages.need(6 + LINE_MM * len(legend))
    _text(c, left, top - 4, legend, "Helvetica", 8.5, (0.3, 0.3, 0.3))

    # -- Check Steps ------------------------------------------------------------
    for check in document["checks"]:
        pages.new_page()
        top = pages.need(12)
        _band(c, top, "Light check")
        top = pages.need(72)
        _image(c, readers, images, "check:%s" % check["id"], left, top, 66) or _placeholder(
            c, left, top, 66, "No picture")
        text = _lines(check["text"], "Helvetica-Bold", 10, width - 72)
        y = _text(c, left + 72, top - 5, text, "Helvetica-Bold", 10)
        bags = ", ".join("bag %d" % bag for bag in check["bags"])
        rows = ["%s  %s" % (part, _bought_entry(plan, part).get("name", part)) for part in check["parts"]]
        y = _text(c, left + 72, y - 2, ["You need%s:" % (" (from %s)" % bags if bags else "")],
                  "Helvetica", 9, (0.3, 0.3, 0.3))
        lines = [line for row in rows for line in _lines(row, "Helvetica", 9, width - 72)]
        _text(c, left + 72, y, lines, "Helvetica", 9)

    # -- sections -----------------------------------------------------------------
    for number, section in enumerate(document["sections"], start=1):
        pages.new_page()
        top = pages.need(12)
        make = " - make %d" % section["make"] if section["make"] > 1 else ""
        bag = "Bag %d" % section["bag"] if section["bag"] else ""
        _band(c, top, "%d  %s%s" % (number, section["title"], make), bag)
        if "section:%s" % section["id"] in images:
            top = pages.need(62)
            _image(c, readers, images, "section:%s" % section["id"], left + (width - 58) / 2, top, 58)
        _materials(c, pages, _material_rows(document, plan, section), left, width)
        for gauge in section["gauges"]:
            _gauge(c, pages, gauge, left, width)
        for step in section["steps"]:
            _step(c, pages, readers, images, plan, document, step, left, width)

    # -- completion -------------------------------------------------------------------
    pages.new_page()
    top = pages.need(12)
    _band(c, top, "Completion")
    top = pages.need(160)
    _image(c, readers, images, "completion", left + (width - 150) / 2, top, 150) or _placeholder(
        c, left, top, 150, "No picture")
    company = document["company"]
    top = pages.need(18)
    _text(c, left, top - 6, ["After-sales"], "Helvetica-Bold", 11, ACCENT)
    _text(c, left, top - 11, _lines("%s: %s" % (company["name"], company["after_sales"]),
                                    "Helvetica", 10, width), "Helvetica", 10)
    c.showPage()
    c.save()
    return pages.number


def _band(c, top: float, title: str, badge: str = "") -> None:
    left, width = MARGIN_MM, PAGE_MM[0] - 2 * MARGIN_MM
    c.setFillColorRGB(*ACCENT)
    c.rect(_mm(left), _mm(top - 10), _mm(width), _mm(9), stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(_mm(left + 3), _mm(top - 7.3), title)
    if badge:
        c.drawRightString(_mm(left + width - 3), _mm(top - 7.3), badge)
    c.setFillColorRGB(0, 0, 0)


def _materials(c, pages: Pages, columns, left: float, width: float) -> None:
    headings = ("Printed", "Paper", "Bought")
    column_w = width / 3.0
    rows = max(len(column) for column in columns) if any(columns) else 1
    per_page = int((PAGE_MM[1] - 2 * MARGIN_MM - FOOTER_MM - 12) // LINE_MM)
    for start in range(0, rows, per_page):
        chunk = min(per_page, rows - start)
        height = 9 + LINE_MM * chunk + 2
        top = pages.need(height + 2)
        c.setStrokeColorRGB(*ACCENT)
        c.roundRect(_mm(left), _mm(top - height), _mm(width), _mm(height), _mm(2), stroke=1, fill=0)
        c.setStrokeColorRGB(0, 0, 0)
        for index, (heading, column) in enumerate(zip(headings, columns)):
            x = left + index * column_w + 2
            _text(c, x, top - 5, [heading + ("" if start == 0 else " (cont.)")], "Helvetica-Bold", 9, ACCENT)
            y = top - 9.5
            if not column and start == 0:
                _text(c, x, y, ["-"], "Helvetica", 8)
            for text, swatch in column[start:start + chunk]:
                if swatch is not None:
                    c.setFillColorRGB(*(v / 255.0 for v in swatch))
                    c.rect(_mm(x), _mm(y - 0.4), _mm(2.6), _mm(2.6), stroke=1, fill=1)
                    c.setFillColorRGB(0, 0, 0)
                shown = _lines(text, "Helvetica", 7.5, column_w - 8)[0]
                _text(c, x + (3.5 if swatch is not None else 0), y, [shown], "Helvetica", 7.5)
                y -= LINE_MM


def _gauge(c, pages: Pages, gauge: dict, left: float, width: float) -> None:
    """A 1:1 line of the Part's length, folded into rows of the page width."""

    usable = width - 4
    length = gauge["length_mm"]
    rows = max(1, math.ceil(length / usable - 1e-9))
    top = pages.need(8 + 5 * rows)
    _text(c, left, top - 4, ["%s: %g mm, 1:1 (print at 100%%)" % (gauge["id"], length)], "Helvetica-Bold", 8)
    c.setLineWidth(_mm(0.5))
    for row in range(rows):
        run = min(usable, length - row * usable)
        y = top - 9 - 5 * row
        c.line(_mm(left), _mm(y), _mm(left + run), _mm(y))
        for tick in range(0, int(run) + 1, 5):
            c.line(_mm(left + tick), _mm(y), _mm(left + tick), _mm(y + (1.8 if tick % 10 == 0 else 1.0)))
        c.line(_mm(left + run), _mm(y - 1.2), _mm(left + run), _mm(y + 1.2))
    c.setLineWidth(1)


def _step(c, pages: Pages, readers, images, plan, document, step: str, left: float, width: float) -> None:
    item = plan.step[step]
    record = document["steps"].get(step, {})
    picture = 64.0
    text_x, text_w = left + picture + 4, width - picture - 4
    code = step.split("-", 1)[0]
    body = ["%s%s" % (JOINT_LABELS.get(item.get("joint"), item.get("joint")),
                      "  -  make %d" % item["count"] if int(item.get("count", 1)) > 1 else "")]
    inputs = [_input_label(plan, entry) for entry in plan.inputs[step]]
    instruction = _lines(item["text"], "Helvetica-Bold", 10, text_w)
    leads = [line for lead in item.get("leads") or ()
             for line in _lines("Lead of %s comes out: %s" % (lead["lamp"], lead["exit"]), "Helvetica", 8.5, text_w)]
    input_lines = [line for label in inputs for line in _lines(label, "Helvetica", 8.5, text_w)]
    text_h = 16 + LINE_MM * (len(instruction) + len(input_lines) + len(leads) + 2)
    pair = record.get("error_picture") is not None
    height = max(picture, text_h) + 4 + (52 if pair else 0)
    top = pages.need(height)
    if not _image(c, readers, images, "step:%s" % step, left, top, picture):
        _placeholder(c, left, top, picture, "Paper only: see the Print Sheets")
    c.setFillColorRGB(*ACCENT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(_mm(text_x), _mm(top - 7), code + ("  !" if item.get("error_prone") else ""))
    c.setFillColorRGB(0, 0, 0)
    y = _text(c, text_x, top - 12, ["-> %s %s" % (code, item.get("output", ""))], "Helvetica-Bold", 9)
    y = _text(c, text_x, y, body, "Helvetica", 8.5, (0.3, 0.3, 0.3))
    y = _text(c, text_x, y - 1, input_lines, "Helvetica", 8.5)
    y = _text(c, text_x, y - 1.5, instruction, "Helvetica-Bold", 10)
    _text(c, text_x, y - 1, leads, "Helvetica", 8.5, (0.6, 0.1, 0.1))
    if pair:
        row = top - max(picture, text_h) - 4
        if record["error_picture"] == "half-turn":
            for index, (name, label, colour) in enumerate((("right:%s" % step, "Correct", RIGHT),
                                                          ("wrong:%s" % step, "Incorrect", WRONG))):
                x = left + index * 70
                _image(c, readers, images, name, x, row - 5, 46)
                _text(c, x, row - 3, [label], "Helvetica-Bold", 9, colour)
        else:
            label = ("No incorrect picture: this input looks the same either way round"
                     if record["error_picture"] == "same-either-way"
                     else "No incorrect picture: nothing in this step moves into place")
            _text(c, left, row - 4, [label], "Helvetica-Oblique", 8.5, (0.4, 0.4, 0.4))


# ---------------------------------------------------------------------------
# the whole run


def write_manual(project: Path, kit: dict, company: dict, meshes=None) -> tuple[dict, int]:
    """Plan, picture and write the Manual into ``<project>/manual``.
    ``meshes`` is the injected geometry; None builds it from the project."""

    project = Path(project)
    document = plan_manual(kit, company)
    out = project / MANUAL_DIR
    out.mkdir(parents=True, exist_ok=True)
    pdf = out / PDF_NAME
    if document["failures"]:
        if pdf.exists():
            pdf.unlink()
        (out / REPORT_NAME).write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        return document, 1
    plan = kit_tree().Plan(kit)
    if meshes is None:
        meshes = cad_meshes(project, plan)
    images = pictures(document, plan, meshes)
    document["pages"] = draw_pdf(document, plan, images, pdf)
    document["pdf"] = {"file": PDF_NAME, "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()}
    (out / REPORT_NAME).write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return document, 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("project", nargs="?", help="the CAD project")
    parser.add_argument("--company", type=Path, default=COMPANY_FILE, help="the company configuration")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.project:
        parser.error("give the CAD project")
    project = Path(args.project)
    try:
        kit = kit_tree().read_install(project)
        if kit is None:
            raise UsageError("the Assembly Tree is not installed: run kit_tree.py --install first")
        company = load_company(args.company)
        document, code = write_manual(project, kit, company)
    except (OSError, UsageError, KeyError, TypeError, ValueError) as error:
        print("kit_manual: %s" % error, file=sys.stderr)
        return 2
    except Exception as error:  # noqa: BLE001 - a Component's own source failed to build or place
        print("kit_manual: building the Components failed: %s: %s" % (type(error).__name__, error))
        print("kit_manual: building the Components failed: %s: %s" % (type(error).__name__, error), file=sys.stderr)
        return 1
    for failure in document["failures"]:
        print("FAIL %s" % failure)
    if code == 0:
        print("PASS kit manual: %d page(s), %d section(s), %d Check Step(s); after-sales contact %s"
              % (document["pages"], len(document["sections"]), len(document["checks"]),
                 "confirmed" if document["company"]["confirmed"] else "UNCONFIRMED (owner placeholder)"))
    else:
        print("FAIL kit manual: %d failure(s); no PDF written" % len(document["failures"]))
    if args.json:
        print(json.dumps(document, sort_keys=True))
    return code


def self_check() -> int:
    """The plan, without geometry or a PDF."""

    kit = {
        "kind": "kit-tree", "schema_version": 1, "pieces": [],
        "geometries": [{"id": "box", "name": "Box", "count": 1, "wall_min_mm": 1.2}],
        "catalogue": {"filaments": {"oak": {"hex": "#b5834f", "name": "Oak"}}, "bought_parts": {}},
        "assembly_tree": {
            "parts": [{"id": "A01-box", "name": "Box", "filament": "oak"},
                      {"id": "A02-peg", "name": "Peg", "filament": "oak"}],
            "steps": [{"id": "S01-pegs", "output": "Box", "count": 1, "joint": "peg-socket", "text": "Pegs in.",
                       "inputs": [{"id": "A01-box"}, {"id": "A02-peg", "count": 2, "direction": [0, 0, -1]}]}],
            "components": [{"geometry": "box", "parts": ["A01-box", "A02-peg"]}],
        },
    }
    company = {"kind": COMPANY_KIND, "name": "Co", "after_sales": {"contact": "x", "confirmed": False},
               "warnings": {"small_parts": "s", "batteries": "b"}}
    document = plan_manual(kit, company)
    problems = []
    if document["failures"] or [s["id"] for s in document["sections"]] != ["component:box"]:
        problems.append("sections")
    if document["sections"][0]["materials"]["printed"] != [{"id": "A01-box", "count": 1},
                                                          {"id": "A02-peg", "count": 2}]:
        problems.append("materials")
    for problem in problems:
        print("kit_manual self-check failed: %s" % problem, file=sys.stderr)
    if not problems:
        print("kit_manual self-check: ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
