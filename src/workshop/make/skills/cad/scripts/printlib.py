#!/usr/bin/env python3
"""Printable-entry discovery and source->mesh tessellation.

`check_fit` and the mesh gates (`check_mesh`, `check_overhang`,
`check_thickness`, `repair_mesh`) must agree on two things, or they quietly
check different models:

    which entries are print targets     PRINTABLE, part_* vs combined, the
                                        single-assembly fallback
    what mesh those entries produce     the tessellation the gates measure

Both answers live here once and every gate imports them, for the same reason
`meshlib` owns the weld tolerance: two nearly-identical answers is worse than
one, because neither side looks wrong on its own.

This repository writes STEP and nothing else, so there is no mesh artifact to
read. The gates build the entry from source and tessellate the B-rep here. That
costs the old pair's staleness check -- when the gates read an exported STL,
`check_fit` reading source and `check_mesh` reading the artifact disagreed
exactly when the export was stale -- but with no artifact to go stale there is
nothing left for that pair to catch. What the mesh gates still answer is what
they always answered: whether the solid, at slicing resolution, is watertight,
manifold, thick enough for the nozzle, and supportable.

Tessellation deviation matters. `BRepMesh` discretises a shared edge once and
both adjacent faces use that discretisation, so a sound solid tessellates to a
watertight mesh; a mesh gate failing watertightness on a source-fed mesh is
reporting a real defect in the solid, not a tessellation artifact.

    python "$CAD_SKILL_ROOT/scripts/printlib.py"        # self-check
"""

from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import math
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PACKAGES_DIR = SCRIPTS_DIR / "packages"
CADPY_SRC_DIR = PACKAGES_DIR / "cadgen" / "src"
for _runtime_path in (SCRIPTS_DIR, PACKAGES_DIR, CADPY_SRC_DIR):
    _text = str(_runtime_path)
    if _runtime_path.is_dir() and _text not in sys.path:
        sys.path.insert(0, _text)

ENTRY_SUFFIX = ".step.py"
PART_PREFIX = "part_"

# Tessellation defaults. 0.02 mm chord deviation is well under a 0.4 mm nozzle
# and under the 0.05 mm thickness resolution the thickness gate works at, so the
# mesh is not the limiting factor in any measurement a gate reports.
MESH_DEVIATION = 0.02      # mm; max chord distance from the true surface
MESH_ANGULAR = 0.2         # rad; max normal deviation across one triangle

IGNORED_DIR_NAMES = {
    "__cadgen__",
    "__pycache__",
    ".cache",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "measure",
    "node_modules",
    "ref",
    "skills",
    "snaps",
}

# Built at runtime for the same reason as check_layout's marker: cadgen's
# discovery scan treats any worktree file carrying these bytes as a generator
# candidate, and would log a spurious "invalid CAD source" on every gen run.
GEN_FUNC = "gen_" + "step"

# A multi-colour print entry returns its colour regions as separate solids --
# what a multi-material slicer loads -- and they share every face they meet on.
# Tessellated as one mesh, those shared faces read as non-manifold edges and
# flip every inside/outside count, so the mesh gates would measure the plate,
# not the object. Such an entry also defines this function, returning the
# printed object as one solid (the union built from the primitives, not by
# re-fusing the regions: see `wiki show fdm-multi-material-design`), and the
# mesh gates measure that. `gen_step()` stays the colour plate.
PRINT_UNION_FUNC = "gen_print_union"

# Workshop: the mesh gates measure that union in place of the plate `gen_step()`
# exports, so it has to be the plate's own material -- the regions' summed
# volume inside the regions' bounding box. A stand-in that prints more easily (a
# region left out, a wall thickened, the body moved) would otherwise pass every
# print gate, the host's print-ready rerun included, for an object nobody ships.
PRINT_UNION_VOLUME_MM3 = 1e-3
PRINT_UNION_VOLUME_RELATIVE = 1e-5
PRINT_UNION_BOX_MM = 0.01


def declared_printable(path: Path) -> bool | None:
    """Read an optional module-level ``PRINTABLE = bool`` without importing CAD."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        value = None
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "PRINTABLE"
            for target in node.targets
        ):
            value = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "PRINTABLE"
        ):
            value = node.value
        if value is not None:
            if isinstance(value, ast.Constant) and isinstance(value.value, bool):
                return value.value
            raise ValueError(f"{path}: PRINTABLE must be the literal True or False")
    return None


def iter_printable_entries(root: Path) -> dict[Path, list[Path]]:
    """Yield actual print targets, grouped by their project directory."""
    entries_by_dir: dict[Path, list[Path]] = {}
    for path in sorted(root.rglob("*" + ENTRY_SUFFIX)):
        rel_parts = path.relative_to(root).parts[:-1]
        if any(part in IGNORED_DIR_NAMES for part in rel_parts):
            continue
        if GEN_FUNC not in path.read_text(encoding="utf-8", errors="replace"):
            continue
        entries_by_dir.setdefault(path.parent, []).append(path)

    by_dir: dict[Path, list[Path]] = {}
    for project, entries in entries_by_dir.items():
        parts = [path for path in entries if path.name.startswith(PART_PREFIX)]
        assemblies = [path for path in entries if not path.name.startswith(PART_PREFIX)]
        selected = [path for path in parts if declared_printable(path) is not False]
        if parts:
            selected.extend(
                path for path in assemblies if declared_printable(path) is True
            )
        elif len(assemblies) == 1 and declared_printable(assemblies[0]) is not False:
            selected.append(assemblies[0])
        if selected:
            by_dir[project] = sorted(selected)
    return by_dir


def explicit_entries(root: Path, raw_entries: list[str]) -> dict[Path, list[Path]]:
    """Resolve explicitly selected printable entries beneath ``root``."""
    by_dir: dict[Path, list[Path]] = {}
    cwd = Path.cwd().resolve()
    for raw in raw_entries:
        candidate = Path(raw)
        if not candidate.is_absolute():
            from_cwd = (cwd / candidate).resolve()
            candidate = from_cwd if from_cwd.is_file() else (root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ValueError(f"entry must stay inside {root}: {candidate}") from error
        if not candidate.is_file() or not candidate.name.endswith(ENTRY_SUFFIX):
            raise ValueError(f"not a *{ENTRY_SUFFIX} entry: {candidate}")
        if GEN_FUNC not in candidate.read_text(encoding="utf-8", errors="replace"):
            raise ValueError(f"{candidate} defines no {GEN_FUNC}()")
        if declared_printable(candidate) is False:
            raise ValueError(f"{candidate} declares PRINTABLE = False")
        by_dir.setdefault(candidate.parent, []).append(candidate)
    return by_dir


@contextlib.contextmanager
def project_on_path(project: Path):
    """Put a project directory on sys.path for the duration of a build.

    An entry imports its `*_lib` sibling by bare name, and a generator may defer
    that import until it is called, so the path has to stay in place across the
    build and not only across the import. Removed again only if it was inserted
    here, so a caller managing the path around its own loop keeps it.
    """
    text = str(project)
    inserted = text not in sys.path
    if inserted:
        sys.path.insert(0, text)
    try:
        yield
    finally:
        if inserted:
            with contextlib.suppress(ValueError):
                sys.path.remove(text)


def load_entry(path: Path, namespace: str):
    """Import one entry generator with its project directory on sys.path."""
    module_name = f"_printlib_{namespace}_{path.name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def purge_project_modules(project: Path) -> None:
    """Drop every module imported from this project so the next one is clean."""
    project_text = str(project)
    for name, module in list(sys.modules.items()):
        origin = getattr(module, "__file__", None)
        if origin and str(Path(origin).resolve()).startswith(project_text):
            sys.modules.pop(name, None)


def build_entry(path: Path, namespace: str, *, printed: bool = False):
    """Build one entry and return its shape, with generator stdout swallowed.

    `printed=True` is the mesh gates' view: the entry's `gen_print_union()` when
    it defines one (a multi-colour plate), otherwise `gen_step()`.
    """
    sink = io.StringIO()
    with project_on_path(path.parent), contextlib.redirect_stdout(sink):
        module = load_entry(path, namespace)
        name = GEN_FUNC
        if printed and callable(getattr(module, PRINT_UNION_FUNC, None)):
            name = PRINT_UNION_FUNC
        builder = getattr(module, name, None)
        if builder is None:
            raise AttributeError(f"{path.name} defines no {name}()")
        shape = builder()
        plate = None
        if name == PRINT_UNION_FUNC and shape is not None:
            exported = getattr(module, GEN_FUNC, None)
            if exported is None:
                raise AttributeError(f"{path.name} defines no {GEN_FUNC}()")
            plate = exported()
    if shape is None:
        raise ValueError(f"{path.name} {name}() returned None")
    if name == PRINT_UNION_FUNC:
        if plate is None:
            raise ValueError(f"{path.name} {GEN_FUNC}() returned None")
        check_print_union(path, plate, shape)
    return shape


def check_print_union(path: Path, plate, union) -> None:
    """Refuse a `gen_print_union()` that is not the material `gen_step()` exports.

    Volume and bounding box, not a Boolean difference: two integrations and two
    boxes cost nothing beside the gates they guard, and together they catch a
    region left out, material added, or the body moved or resized.
    """
    plate_solids, union_solids = list(plate.solids()), list(union.solids())
    if not plate_solids or not union_solids:
        raise ValueError(
            f"{path.name}: {GEN_FUNC}() and {PRINT_UNION_FUNC}() must both return solids"
        )
    plate_volume = math.fsum(float(solid.volume) for solid in plate_solids)
    union_volume = math.fsum(float(solid.volume) for solid in union_solids)
    tolerance = max(PRINT_UNION_VOLUME_MM3, PRINT_UNION_VOLUME_RELATIVE * plate_volume)
    if not math.isfinite(union_volume) or abs(union_volume - plate_volume) > tolerance:
        raise ValueError(
            f"{path.name}: {PRINT_UNION_FUNC}() holds {union_volume:.4f} mm3 but the "
            f"regions {GEN_FUNC}() exports hold {plate_volume:.4f} mm3. The print gates "
            f"measure the union in place of the plate, so it must be the plate's own "
            "material: build it from the primitives the regions were cut from"
        )
    a, b = plate.bounding_box(), union.bounding_box()
    drift = max(
        abs(a.min.X - b.min.X), abs(a.min.Y - b.min.Y), abs(a.min.Z - b.min.Z),
        abs(a.max.X - b.max.X), abs(a.max.Y - b.max.Y), abs(a.max.Z - b.max.Z),
    )
    if drift > PRINT_UNION_BOX_MM:
        raise ValueError(
            f"{path.name}: {PRINT_UNION_FUNC}() sits {drift:.4f} mm off the bounding box "
            f"of the regions {GEN_FUNC}() exports. The print gates measure the union in "
            "place of the plate, so it must occupy the plate's own place"
        )


def tessellate(shape, *, deviation: float = MESH_DEVIATION,
               angular: float = MESH_ANGULAR):
    """Return an (N, 3, 3) triangle-soup array for a built shape, in mm.

    The soup layout, not an indexed mesh, because `meshlib.weld` owns the
    vertex identity question and every gate goes through it.
    """
    import numpy as np

    vectors, triangles = shape.tessellate(deviation, angular)
    if not triangles:
        raise ValueError("tessellation produced no triangles")
    points = np.asarray(
        [[vector.X, vector.Y, vector.Z] for vector in vectors], dtype=np.float64
    )
    faces = np.asarray(triangles, dtype=np.int64)
    return points[faces]


def entry_mesh(path: Path, namespace: str, *, deviation: float = MESH_DEVIATION,
               angular: float = MESH_ANGULAR):
    """Build one printable entry from source -- its printed object, see
    PRINT_UNION_FUNC -- and tessellate it in one step."""
    return tessellate(build_entry(path, namespace, printed=True), deviation=deviation,
                      angular=angular)


def entry_shape(path: Path, namespace: str):
    """Build one printable entry's printed object -- see PRINT_UNION_FUNC."""
    return build_entry(path, namespace, printed=True)


# Workshop (#82): the one finer retry a valid solid with an open tessellation
# gets. A quarter of the chord deviation and half the angle: BRepMesh then
# rediscretises every edge, which closes a seam two faces discretised apart.
FINE_DEVIATION = MESH_DEVIATION / 4
FINE_ANGULAR = MESH_ANGULAR / 2
# How many invalid faces a report lists.
INVALID_FACES_SHOWN = 8


def invalid_faces(shape) -> list[dict] | None:
    """None for a valid B-rep; otherwise every face BRepCheck refuses.

    The list may be empty: a solid can be invalid in its shell or its
    orientation with every face sound on its own. Each entry names the face's
    index in `shape.faces()`, its surface type and where it is.
    """
    if shape is None or shape.is_valid:
        return None
    from OCP.BRepCheck import BRepCheck_Analyzer

    bad = []
    for index, face in enumerate(shape.faces()):
        if BRepCheck_Analyzer(face.wrapped).IsValid():
            continue
        bad.append(describe_face(face, index))
    return bad


def describe_face(face, index: int) -> dict:
    """A face as a report names it: index, surface type, area and centre.

    The centre is its bounding box's: an invalid face has no mass centre."""
    centre = face.bounding_box().center()
    try:
        area = float(face.area)
    except Exception:  # an invalid face may not integrate
        area = float("nan")
    return {
        "index": index,
        "type": str(face.geom_type).split(".")[-1].lower(),
        "area": area,
        "centre": (float(centre.X), float(centre.Y), float(centre.Z)),
    }


def printed_mesh(shape, *, mesh=None) -> dict:
    """Tessellate a built shape for the mesh gates, closing it if it can be closed.

    A sound solid tessellates watertight at the default deviation. When the
    mesh comes back open, the B-rep says which of two things went wrong
    (issue #82):

        invalid        the solid itself is broken. Report its bad faces, so
                       the worker repairs the generator where it broke.
        closed         the solid is valid and one finer tessellation closed
                       the seam the default one left open. Measure that.
        unmeasurable   the solid is valid and the finer mesh is still open.
                       Neither inside nor outside is defined, so no gate can
                       measure it -- and nothing says the part fails to print.

    Returns `{"status", "verts", "faces", "open_edges", "deviation",
    "retessellated", "invalid_faces"}`; `verts`/`faces` are None unless the
    status is `closed`. `mesh(shape, deviation, angular)` returns a triangle
    soup, `tessellate` by default; a test passes its own.
    """
    from meshlib import summarize, weld

    mesh = mesh or (lambda subject, deviation, angular: tessellate(
        subject, deviation=deviation, angular=angular))
    record = {"status": "closed", "verts": None, "faces": None, "open_edges": 0,
              "deviation": MESH_DEVIATION, "retessellated": False, "invalid_faces": None}
    verts, faces = weld(mesh(shape, MESH_DEVIATION, MESH_ANGULAR))
    record["open_edges"] = summarize(verts, faces)["boundary"]
    if not record["open_edges"]:
        record.update(verts=verts, faces=faces)
        return record
    bad = invalid_faces(shape)
    if bad is not None:
        record.update(status="invalid", invalid_faces=bad)
        return record
    verts, faces = weld(mesh(shape, FINE_DEVIATION, FINE_ANGULAR))
    still_open = summarize(verts, faces)["boundary"]
    record.update(deviation=FINE_DEVIATION, retessellated=True)
    if still_open:
        record.update(status="unmeasurable", open_edges=still_open)
        return record
    record.update(verts=verts, faces=faces)
    return record


def mesh_refusal(name: str, record: dict) -> list[str]:
    """The lines a mesh gate prints when `printed_mesh` gave it nothing to measure."""
    if record["status"] == "invalid":
        bad = record["invalid_faces"] or []
        lines = [f"{name}: the B-rep is not a valid solid, so its tessellation has "
                 f"{record['open_edges']} open edge(s). Repair the generator where the solid "
                 "breaks: an overlapping trim, a zero-thickness seam or a self-intersecting "
                 "sweep, not the mesh."]
        if bad:
            lines.append(f"  {len(bad)} invalid face(s):")
            for item in bad[:INVALID_FACES_SHOWN]:
                x, y, z = item["centre"]
                lines.append(f"    face {item['index']} ({item['type']}, {item['area']:.2f} mm2) "
                             f"centred at ({x:.1f}, {y:.1f}, {z:.1f})")
            if len(bad) > INVALID_FACES_SHOWN:
                lines.append(f"    ... and {len(bad) - INVALID_FACES_SHOWN} more")
        else:
            lines.append("  every face is valid on its own: the shell or its orientation is "
                         "broken (two solids touching along an edge, or an inside-out shell)")
        return lines
    return [f"{name}: the B-rep is a valid solid, but its tessellation stays open at "
            f"{record['open_edges']} edge(s) even at {FINE_DEVIATION:g} mm deviation. Inside "
            "and outside are undefined on an open mesh, so this part cannot be measured; it "
            "has not failed a print limit. Simplify the faces where the mesh is open (a "
            "tangent seam, a sliver face from a fillet or a trim) and rerun."]


# Workshop (#82): a print gate names the feature a failing region belongs to.
# print-details records every feature it makes in its module's
# `PRINT_DETAIL_TAGS`; a region within this distance of a tagged feature is
# reported as that feature, else as the nearest B-rep face.
TAG_REGISTRY = "PRINT_DETAIL_TAGS"
NEAR_FEATURE_MM = 1.0


def feature_tags() -> list[dict]:
    """Every feature print-details tagged while the entry was built.

    Read from whichever loaded module carries the registry -- the project's
    installed `features/print_details.py` under any import name -- so the gate
    needs no import path of its own. A tag holds `kind`, `name`, `site` and
    the feature's `shape` in the generator's coordinates.
    """
    tags, seen = [], set()
    for module in list(sys.modules.values()):
        registry = getattr(module, TAG_REGISTRY, None)
        if not isinstance(registry, list) or id(registry) in seen:
            continue
        seen.add(id(registry))
        tags.extend(tag for tag in registry
                    if isinstance(tag, dict) and {"kind", "name", "site", "shape"} <= tag.keys())
    return tags


def _distance(shape, point) -> float:
    from build123d import Vector, Vertex

    try:
        return float(shape.distance_to(Vertex(Vector(*point))))
    except Exception:  # an empty or degenerate tag shape locates nothing
        return float("inf")


def nearest_feature(shape, point, tags, near: float = NEAR_FEATURE_MM) -> dict | None:
    """Name what a failing region at `point` belongs to.

    The nearest tagged print-details feature within `near` mm, else the
    nearest face of `shape`. `key` is what a later round compares to find the
    same defect again: a tagged feature by its kind and call site, a face by
    its surface type and centre to the millimetre. None without a shape.
    """
    best = None
    for tag in tags:
        distance = _distance(tag["shape"], point)
        if distance <= near and (best is None or distance < best[0]):
            best = (distance, tag)
    if best is not None:
        distance, tag = best
        return {"kind": "feature", "key": f"{tag['kind']}@{tag['site']}",
                "label": f"{tag['name']} ({tag['site']})", "distance": distance}
    if shape is None:
        return None
    faces = shape.faces()
    if not faces:
        return None
    from build123d import Vector

    p = Vector(*point)
    lo = min(_distance(shape, point), float("inf"))
    found = None
    for index, face in enumerate(faces):
        box = face.bounding_box()
        gap = max(box.min.X - p.X, p.X - box.max.X, box.min.Y - p.Y, p.Y - box.max.Y,
                  box.min.Z - p.Z, p.Z - box.max.Z, 0.0)
        if gap > lo + 1e-3:
            continue
        distance = _distance(face, point)
        if found is None or distance < found[0] - 1e-9:
            found = (distance, index, face)
    if found is None:
        return None
    distance, index, face = found
    item = describe_face(face, index)
    x, y, z = item["centre"]
    key = f"{item['type']}@({round(x) + 0},{round(y) + 0},{round(z) + 0})"
    return {"kind": "face", "key": key,
            "label": f"face {index} ({item['type']}, {item['area']:.1f} mm2, centre "
                     f"({x:.1f}, {y:.1f}, {z:.1f}); no print-details feature within {near:g} mm)",
            "distance": distance}


def feature_line(found: dict | None) -> str:
    """The `at ...` text a gate prints under a region; the first word after
    `at feature`/`at face` is the region's repeat key."""
    if found is None:
        return ""
    return f"at {found['kind']} {found['key']} -- {found['label']}, {found['distance']:.2f} mm away"


def resolve_single_entry(target: str) -> Path:
    """Resolve a CLI target to exactly one printable entry.

    The mesh gates stay single-subject on purpose: a project prints one part at
    a time and each is sliced on its own, so one report per part is the honest
    unit. `verify_project` owns the sweep across parts. A directory is accepted
    only when it leaves no choice to guess at.
    """
    path = Path(target).resolve()
    if path.is_file():
        if not path.name.endswith(ENTRY_SUFFIX):
            raise SystemExit(f"not a *{ENTRY_SUFFIX} entry: {path}")
        if GEN_FUNC not in path.read_text(encoding="utf-8", errors="replace"):
            raise SystemExit(f"{path} defines no {GEN_FUNC}()")
        if declared_printable(path) is False:
            raise SystemExit(f"{path} declares PRINTABLE = False")
        return path
    if not path.is_dir():
        raise SystemExit(f"no such entry or project directory: {path}")

    found = iter_printable_entries(path).get(path, [])
    if not found:
        raise SystemExit(f"{path}: no printable entries")
    if len(found) > 1:
        listed = "\n  ".join(entry.name for entry in found)
        raise SystemExit(
            f"{path} has {len(found)} printable entries; name the one to check:\n"
            f"  {listed}"
        )
    return found[0]


def entry_role(path: Path) -> str:
    """The short name a report uses for an entry: `part_base.step.py` -> `base`."""
    role = path.name.removesuffix(ENTRY_SUFFIX)
    return role.removeprefix(PART_PREFIX) if role.startswith(PART_PREFIX) else role


def _self_check() -> int:
    import numpy as np
    from build123d import Box, Cylinder

    from meshlib import summarize, weld

    ok = True

    shape = Box(20, 10, 5) - Cylinder(3, 10)
    soup = tessellate(shape)
    verts, faces = weld(soup)
    metrics = summarize(verts, faces)
    watertight = (
        metrics["boundary"] == 0
        and metrics["nonmanifold_edges"] == 0
        and metrics["flipped"] == 0
        and metrics["shells"] == 1
    )
    print(f"{'ok  ' if watertight else 'FAIL'} a sound solid tessellates watertight, "
          f"manifold and consistently wound")
    ok &= watertight

    # The mesh has to measure the solid, not merely be sound: a deviation that
    # is too coarse silently shrinks a bored part and every downstream
    # measurement inherits the error.
    error = abs(metrics["volume"] - shape.volume) / shape.volume
    close = error < 1e-3
    print(f"{'ok  ' if close else 'FAIL'} tessellated volume within 0.1% of exact "
          f"({error * 100:.3f}%)")
    ok &= close

    box = np.asarray([20.0, 10.0, 5.0])
    exact_size = np.allclose(metrics["size"], box, atol=1e-6)
    print(f"{'ok  ' if exact_size else 'FAIL'} planar extents survive tessellation exactly")
    ok &= exact_size

    # build123d raises on a genuinely empty shape, so the guard here only
    # catches a shape that tessellates to nothing without complaining. Test it
    # with a stub rather than pretending a real shape reaches that state.
    class _NoTriangles:
        def tessellate(self, deviation, angular):
            return [], []

    empty = False
    try:
        tessellate(_NoTriangles())
    except ValueError:
        empty = True
    print(f"{'ok  ' if empty else 'FAIL'} a shape that tessellates to no triangles "
          f"raises instead of returning an empty mesh")
    ok &= empty

    # A colour plate (a block with an inlay cut into it) is two solids sharing
    # faces: as one mesh it is non-manifold. With gen_print_union() the mesh
    # gates measure the block instead, and gen_step() still returns the plate.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        entry = Path(tmp) / "part_plate.step.py"
        entry.write_text(
            "from build123d import Box, Compound, Pos\n"
            "PRINTABLE = True\n"
            "def _parts():\n"
            "    block = Pos(0, 0, 5) * Box(20, 20, 10)\n"
            "    inlay = Pos(0, 0, 9.5) * Box(6, 6, 1)\n"
            "    return block, inlay\n"
            f"def {GEN_FUNC}():\n"
            "    block, inlay = _parts()\n"
            "    return Compound(children=[block - inlay, inlay])\n"
            f"def {PRINT_UNION_FUNC}():\n"
            "    return _parts()[0]\n",
            encoding="utf-8",
        )
        plate = build_entry(entry, "selfcheck_plate")
        two = len(plate.solids()) == 2
        print(f"{'ok  ' if two else 'FAIL'} gen_step() of a colour plate returns its regions")
        ok &= two
        v, f = weld(entry_mesh(entry, "selfcheck_plate"))
        m = summarize(v, f)
        union = m["nonmanifold_edges"] == 0 and m["shells"] == 1 and abs(m["volume"] - 4000) < 1
        print(f"{'ok  ' if union else 'FAIL'} the mesh gates measure gen_print_union(), "
              f"the printed object, not the plate")
        ok &= union

        # Workshop: a union that is not the plate's own material is refused, so
        # the gates cannot measure a stand-in that prints more easily.
        stand_ins = {
            "leaves the inlay out": "_parts()[0] - _parts()[1]",
            "is the block moved 1 mm": "Pos(1, 0, 0) * _parts()[0]",
        }
        for index, (what, body) in enumerate(stand_ins.items()):
            entry.write_text(
                "from build123d import Box, Compound, Pos\n"
                "PRINTABLE = True\n"
                "def _parts():\n"
                "    block = Pos(0, 0, 5) * Box(20, 20, 10)\n"
                "    inlay = Pos(0, 0, 9.5) * Box(6, 6, 1)\n"
                "    return block, inlay\n"
                f"def {GEN_FUNC}():\n"
                "    block, inlay = _parts()\n"
                "    return Compound(children=[block - inlay, inlay])\n"
                f"def {PRINT_UNION_FUNC}():\n"
                f"    return {body}\n",
                encoding="utf-8",
            )
            refused = False
            try:
                entry_mesh(entry, f"selfcheck_stand_in_{index}")
            except ValueError as error:
                refused = PRINT_UNION_FUNC in str(error)
            print(f"{'ok  ' if refused else 'FAIL'} a print union that {what} is refused")
            ok &= refused

    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_self_check())
