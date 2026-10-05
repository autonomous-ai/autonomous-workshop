#!/usr/bin/env python
"""One build's B-rep, kept so a round's checks read it instead of rebuilding.

A make_round component round used to hand the same `part_<id>.step.py` to
seven tools, and each one called `gen_step()` again: the round built its
Component seven times for checks that take seconds (issue #101). Now one
process builds it, beside `gen`, and keeps what it built here:

    brepbundle.py build <project>/part_<id>.step.py --out DIR/base

    DIR/base/manifest.json   what was built, from which entry, its identities
    DIR/base/shapes.bin      the shapes, one native BREP container

and every later check of the round loads it. It builds the source as a print
gate does (`printlib.build_entry`), in a fresh process, and keeps the shape
with the mesh its build left on it. It prints one JSON line, `{"brepBundle":
{"identity", "builtIdentity", "maxDriftMm", ...}}`; make_round uses the
bundle only when `builtIdentity` is the identity `gen` reported for its
build.

Native BREP (`BinTools`), not STEP: it keeps the doubles, tolerances, pcurves,
face types and mesh as built. One thing moves: a direction is normalized
again when it is read, so a line or an axis can come back one unit in the
last place off, and the read shape's B-rep identity
(`cadgen.inspection_runtime.shape_identity`) can differ from the built one's.
The manifest records both -- `built_identity`, the build's, and `identity`,
what every read of these bytes returns -- and the largest sampled difference
between them (`max_drift_mm`, at most MAX_DRIFT_MM, or no bundle is
written). Every check of the round reads the same bytes, so every check reads
the same B-rep. A tessellation can still notice the drift: on Broken God's
wing a check that meshes the read shape at 0.02 mm drew 277560 thickness
samples where a rebuild drew 277725, and 1-8 render pixels moved by 1-2 of
255, with every verdict and region unchanged; on spine-housing every report
and image was byte-identical. The bundle also keeps what a check reads besides geometry:
every build123d node's label, colour and children (a render's colours and
placements come from them), and the print-details feature tags the build
recorded (a print gate names a failing region by them). A writer reloads what
it wrote and refuses a bundle whose nodes do not come back with the topology,
label, colour and class they were built with.

A check finds its bundle through the environment make_round sets for it:

    WORKSHOP_BREP_BUNDLE    the bundle directory of the round's Component
    WORKSHOP_BREP_IDENTITY  the identity that bundle reads back as

`for_entry(entry)` returns the bundle only when it was built from that very
entry; a check of anything else builds from source as before. A bundle whose
loaded identity is not the one recorded is an error, never a silent rebuild.
Every read prints one line on stderr,

    [brep] <purpose> read <entry> <base|instance-N> identity <sha256>

so the round records the B-rep identity each of its checks read.

An entry that defines `gen_print_union()` keeps building its printed object
from source: the bundle holds `gen_step()`'s shape, which for such an entry
is the colour plate, not what the print gates measure.

An instance of a geometry whose count is above 1 is built by its own process,
as check_envelope and the Display Pose build it:

    brepbundle.py build <project>/part_<id>.step.py --instance N --out DIR/instance-N

When `gen_step` takes no instance every instance is `gen_step()`'s shape, and
the instance bundle says so (`"alias": "base"`) without building anything.

Self-check (builds a small coloured assembly in a temporary directory):

    .venv/bin/python "$CAD_SKILL_ROOT/scripts/brepbundle.py" --self-check
"""
from __future__ import annotations

import contextlib
import hashlib
import inspect
import io
import json
import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
for _runtime_path in (SCRIPTS_DIR, SCRIPTS_DIR / "packages", SCRIPTS_DIR / "packages" / "cadgen" / "src"):
    if _runtime_path.is_dir() and str(_runtime_path) not in sys.path:
        sys.path.insert(0, str(_runtime_path))

SCHEMA = 1
ENV_BUNDLE = "WORKSHOP_BREP_BUNDLE"
ENV_IDENTITY = "WORKSHOP_BREP_IDENTITY"
BASE = "base"
MANIFEST = "manifest.json"
SHAPES = "shapes.bin"
PRINT_UNION_FUNC = "gen_print_union"
INSTANCE_PARAM = "instance"
GEN_FUNC = "gen_" + "step"
# The build123d classes a node may come back as; anything else comes back as
# what OCCT says it is.
NODE_CLASSES = ("Compound", "Part", "Sketch", "Curve", "Solid", "Shell", "Face", "Wire", "Edge",
                "Vertex")
READ_LINE = "[brep] %s read %s %s identity %s"
# How far a read-back sample may sit from the built one: a few units in the
# last place of a toy's coordinates, nowhere near anything a check resolves.
MAX_DRIFT_MM = 1e-9


def instance_dir(instance: int | None) -> str:
    return BASE if instance is None else "instance-%d" % instance


def identity(shape) -> str:
    """The B-rep identity `gen --json` reports (ADR 0073)."""
    from cadgen.inspection_runtime import shape_identity

    return shape_identity(getattr(shape, "wrapped", shape))


def _colour(shape):
    colour = getattr(shape, "color", None)
    return None if colour is None else [float(value) for value in tuple(colour)]


def _nodes(shape) -> list:
    """Every build123d node under `shape`, depth first, root first."""
    found = [shape]
    for child in list(getattr(shape, "children", ()) or ()):
        found.extend(_nodes(child))
    return found


def _base_class(shape) -> str | None:
    """The build123d topology class a node is (a `Box` is a `Part`), or None."""
    for cls in type(shape).__mro__:
        if cls.__name__ in NODE_CLASSES and cls.__module__.startswith("build123d"):
            return cls.__name__
    return None


def _describe(shape) -> dict:
    return {"class": _base_class(shape), "label": str(getattr(shape, "label", "") or ""),
            "color": _colour(shape), "material": str(getattr(shape, "material", "") or ""),
            "children": len(list(getattr(shape, "children", ()) or ()))}


def _container(shapes):
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Compound

    container, builder = TopoDS_Compound(), BRep_Builder()
    builder.MakeCompound(container)
    for shape in shapes:
        builder.Add(container, shape.wrapped)
    return container


def _members(container) -> list:
    from OCP.TopoDS import TopoDS_Iterator

    # Neither orientation nor location is composed: each member comes back
    # exactly as it was added.
    iterator, members = TopoDS_Iterator(container, False, False), []
    while iterator.More():
        members.append(iterator.Value())
        iterator.Next()
    return members


def _node(raw, describe: dict, children: list):
    import build123d
    from build123d import Color
    from build123d.topology.shape_core import downcast

    name = describe.get("class")
    cls = getattr(build123d, name) if name in NODE_CLASSES else None
    obj = downcast(raw)
    if children:
        node = (cls if cls is not None and issubclass(cls, build123d.Compound) else build123d.Compound)(
            children=children)
        node.wrapped = obj          # the exact compound, with its own location
    elif cls is not None:
        node = cls(obj)
    else:
        node = build123d.Shape.cast(obj)
    if node is None:
        raise RuntimeError("a cached node of class %r cannot be rebuilt" % name)
    node.label = describe.get("label") or ""
    if describe.get("color") is not None:
        node.color = Color(*describe["color"])
    if describe.get("material") and hasattr(node, "material"):
        node.material = describe["material"]
    return node


def _rebuild(raws: list, describes: list, start: int = 0):
    """`(node, next index)` for the node at `start` of the depth-first list."""
    children, index = [], start + 1
    for _ in range(describes[start]["children"]):
        child, index = _rebuild(raws, describes, index)
        children.append(child)
    return _node(raws[start], describes[start], children), index


@dataclass
class Bundle:
    directory: Path
    manifest: dict
    shape: object
    tags: list = field(default_factory=list)

    @property
    def identity(self) -> str:
        return self.manifest["identity"]

    @property
    def printed(self) -> bool:
        return bool(self.manifest.get("printed"))


def _versions() -> dict:
    from importlib.metadata import version

    try:
        return {"build123d": version("build123d"), "cadquery_ocp": version("cadquery-ocp")}
    except Exception:  # noqa: BLE001 - a version is a record, not a key
        return {}


def _samples(shape) -> list:
    """What `shape_identity` hashes, in traversal order and unhashed: every
    vertex point, every edge's curve type, orientation, parameter range and
    five points, every face's surface type, orientation, parameter box and
    nine points."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_VERTEX
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS

    raw = getattr(shape, "wrapped", shape)

    def subshapes(kind):
        explorer = TopExp_Explorer(raw, kind)
        while explorer.More():
            yield explorer.Current()
            explorer.Next()

    def xyz(p):
        return (p.X(), p.Y(), p.Z())

    found = [("shape", int(raw.ShapeType()), 0, ())]
    for item in subshapes(TopAbs_VERTEX):
        found.append(("vertex", 0, 0, xyz(BRep_Tool.Pnt_s(TopoDS.Vertex_s(item)))))
    for item in subshapes(TopAbs_EDGE):
        curve = BRepAdaptor_Curve(TopoDS.Edge_s(item))
        first, last = curve.FirstParameter(), curve.LastParameter()
        values = [first, last]
        for i in range(5):
            values.extend(xyz(curve.Value(first + (last - first) * i / 4)))
        found.append(("edge", int(curve.GetType()), int(item.Orientation()), tuple(values)))
    for item in subshapes(TopAbs_FACE):
        surface = BRepAdaptor_Surface(TopoDS.Face_s(item))
        u0, u1 = surface.FirstUParameter(), surface.LastUParameter()
        v0, v1 = surface.FirstVParameter(), surface.LastVParameter()
        values = [u0, u1, v0, v1]
        for i in range(3):
            for j in range(3):
                values.extend(xyz(surface.Value(u0 + (u1 - u0) * i / 2, v0 + (v1 - v0) * j / 2)))
        found.append(("face", int(surface.GetType()), int(item.Orientation()), tuple(values)))
    return found


def drift(built, loaded) -> float | None:
    """The largest difference between two shapes' sampled geometry, or None
    when their topology, curve and surface types or orientations differ."""
    a, b = _samples(built), _samples(loaded)
    if len(a) != len(b):
        return None
    largest = 0.0
    for (kind, type_a, orient_a, values_a), (kind_b, type_b, orient_b, values_b) in zip(a, b):
        if (kind, type_a, orient_a, len(values_a)) != (kind_b, type_b, orient_b, len(values_b)):
            return None
        for x, y in zip(values_a, values_b):
            if x != y:
                if not (math.isfinite(x) and math.isfinite(y)):
                    return None
                largest = max(largest, abs(x - y))
    return largest


def write(directory, entry, shape, *, built_identity: str | None = None, instance: int | None = None,
          tags=(), printed: bool = True) -> dict:
    """Write one build's bundle and prove what it reads back as; its manifest.

    `BinTools` keeps every double it writes, but reading a direction back
    normalizes it again, so a line or an axis can come back one unit in the
    last place off and the read B-rep hashes differently from the built one.
    The bundle records both: `built_identity`, what the build returned, and
    `identity`, what every read of these bytes returns. It is written only
    when every node reads back with the topology, types, orientations, label,
    colour and class it was built with, its geometry within MAX_DRIFT_MM, and
    two reads agree."""
    from OCP.BinTools import BinTools

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / MANIFEST
    if manifest_path.exists():
        manifest_path.unlink()
    nodes = _nodes(shape)
    built = identity(shape)
    if built_identity is not None and built != built_identity:
        raise RuntimeError("the shape to cache has identity %s, not the build's %s"
                           % (built[:12], built_identity[:12]))
    tags = [tag for tag in tags if getattr(tag.get("shape"), "wrapped", None) is not None]
    container = _container([*nodes, *(tag["shape"] for tag in tags)])
    target = directory / SHAPES
    tmp = target.with_suffix(".tmp")
    # With its triangulation: a shape is kept as gen_step() returned it, and a
    # mesh its build left behind is part of what a fresh build gives a check.
    if not BinTools.Write_s(container, str(tmp)):
        raise RuntimeError("could not write %s" % target)
    os.replace(tmp, target)
    manifest = {
        "schema": SCHEMA, "entry": str(Path(entry).resolve()), "instance": instance,
        "built_identity": built, "nodes": [_describe(node) for node in nodes],
        "tags": [{**{key: str(tag[key]) for key in ("kind", "name", "site")},
                  "class": _base_class(tag["shape"])} for tag in tags],
        "printed": bool(printed), "shapes_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "toolchain": _versions(),
    }
    try:
        loaded = _load(directory, manifest)
        largest = 0.0
        loaded_nodes = _nodes(loaded.shape)
        if len(loaded_nodes) != len(nodes):
            raise RuntimeError("%d nodes read back, %d built" % (len(loaded_nodes), len(nodes)))
        for node, back in zip(nodes, loaded_nodes):
            if _describe(back) != _describe(node):
                raise RuntimeError("a node reads back as %r, built as %r" % (_describe(back), _describe(node)))
            moved = drift(node, back)
            if moved is None or moved > MAX_DRIFT_MM:
                raise RuntimeError("a node's geometry reads back %s" % (
                    "with another topology" if moved is None else "%.3g mm off" % moved))
            largest = max(largest, moved)
        read_back = identity(loaded.shape)
        if identity(_load(directory, manifest).shape) != read_back:
            raise RuntimeError("two reads of the same bytes disagree")
    except Exception:
        target.unlink()
        raise
    manifest.update(identity=read_back, max_drift_mm=largest)
    tmp = manifest_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, manifest_path)   # the manifest lands last: a bundle exists only once whole
    return manifest


def write_alias(directory, entry, instance: int) -> dict:
    """An instance that is `gen_step()`'s shape: read the base bundle."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": SCHEMA, "entry": str(Path(entry).resolve()), "instance": instance, "alias": BASE}
    (directory / MANIFEST).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _load(directory: Path, manifest: dict) -> Bundle:
    from OCP.BinTools import BinTools
    from OCP.TopoDS import TopoDS_Shape

    target = directory / SHAPES
    if hashlib.sha256(target.read_bytes()).hexdigest() != manifest["shapes_sha256"]:
        raise RuntimeError("%s changed after it was written" % target)
    container = TopoDS_Shape()
    if not BinTools.Read_s(container, str(target)) or container.IsNull():
        raise RuntimeError("unreadable B-rep bundle %s" % target)
    raws, describes = _members(container), manifest["nodes"]
    if len(raws) != len(describes) + len(manifest["tags"]):
        raise RuntimeError("%s holds %d shapes, its manifest %d" % (
            target, len(raws), len(describes) + len(manifest["tags"])))
    shape, _end = _rebuild(raws, describes)
    tags = []
    for raw, tag in zip(raws[len(describes):], manifest["tags"]):
        # A tag is read for its distance to a point: its wrapped shape, no tree.
        shape_of_tag = _node(raw, {"class": tag.get("class"), "children": 0}, [])
        tags.append({**{key: tag[key] for key in ("kind", "name", "site")}, "shape": shape_of_tag})
    return Bundle(directory, manifest, shape, tags)


def read(directory) -> Bundle:
    """A bundle as written, its shape's identity checked against the manifest."""
    directory = Path(directory)
    manifest = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA:
        raise RuntimeError("%s: unknown bundle schema %r" % (directory, manifest.get("schema")))
    if manifest.get("alias") == BASE:
        base = read(directory.parent / BASE)
        if base.manifest["entry"] != manifest["entry"]:
            raise RuntimeError("%s names a base bundle of another entry" % directory)
        return base
    bundle = _load(directory, manifest)
    found = identity(bundle.shape)
    if found != manifest["identity"]:
        raise RuntimeError("%s reads back as B-rep %s, not the %s it was written as"
                           % (directory, found[:12], manifest["identity"][:12]))
    return bundle


def for_entry(entry, *, instance: int | None = None, purpose: str = "check") -> Bundle | None:
    """The round's bundle of this entry (or instance), or None to build from source."""
    root = os.environ.get(ENV_BUNDLE)
    if not root:
        return None
    directory = Path(root) / instance_dir(instance)
    try:
        manifest = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if manifest.get("entry") != str(Path(entry).resolve()):
        return None
    bundle = read(directory)
    expected = os.environ.get(ENV_IDENTITY)
    if bundle.directory.name == BASE and expected and bundle.identity != expected:
        raise RuntimeError("the B-rep bundle %s is %s, not the round's build %s"
                           % (bundle.directory, bundle.identity[:12], expected[:12]))
    print(READ_LINE % (purpose, Path(entry).name, instance_dir(instance), bundle.identity),
          file=sys.stderr, flush=True)
    return bundle


def defines_print_union(entry) -> bool:
    """Whether the entry names a printed object of its own (see printlib)."""
    return PRINT_UNION_FUNC in Path(entry).read_text(encoding="utf-8", errors="replace")


def _takes_instance(function) -> bool:
    try:
        return INSTANCE_PARAM in inspect.signature(function).parameters
    except (TypeError, ValueError):
        return False


def build_base(entry: Path, directory: Path) -> dict:
    """Build `gen_step()` once, as a print gate builds it, and keep it with the
    feature tags the build recorded."""
    from printlib import build_entry, feature_tags

    shape = build_entry(entry, "brepbundle")
    return write(directory, entry, shape, tags=feature_tags(), printed=not defines_print_union(entry))


def build_instance(entry: Path, instance: int, directory: Path) -> dict:
    """Build `gen_step(instance=N)` once and keep it, or alias the base build."""
    from printlib import load_entry, project_on_path

    with project_on_path(entry.parent), contextlib.redirect_stdout(io.StringIO()):
        module = load_entry(entry, "brepbundle")
        build = getattr(module, GEN_FUNC)
        if not _takes_instance(build):
            return write_alias(directory, entry, instance)
        shape = build(instance=instance)
    if shape is None:
        raise ValueError("%s %s(instance=%d) returned None" % (entry.name, GEN_FUNC, instance))
    return write(directory, entry, shape, instance=instance, printed=False)


def _self_check() -> int:
    import tempfile

    from build123d import Box, Color, Compound, Cylinder, Pos, Rot

    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print("%s %s%s" % ("ok  " if ok else "FAIL", label, ("  - " + detail) if detail else ""))
        if not ok:
            failures.append(label)

    with tempfile.TemporaryDirectory(prefix="brepbundle-self-check-") as tmp:
        root = Path(tmp)
        entry = root / "part_toy.step.py"
        entry.write_text("def gen_step():\n    pass\n")
        red, blue = Box(10, 10, 2), Pos(0, 0, 6) * Cylinder(3, 8)
        red.color, red.label = Color(1, 0, 0), "plate"
        blue.color, blue.label = Color(0, 0, 1), "post"
        toy = Rot(0, 0, 30) * Compound(children=[red, blue], label="toy")
        tag = {"kind": "chamfer", "name": "chamfer-1", "site": "part_toy.step.py:3", "shape": Box(1, 1, 1)}
        # A mesh the build left behind comes back with the shape.
        from OCP.BRep import BRep_Tool
        from OCP.BRepMesh import BRepMesh_IncrementalMesh
        from OCP.TopLoc import TopLoc_Location

        BRepMesh_IncrementalMesh(toy.wrapped, 2.0)
        manifest = write(root / BASE, entry, toy, built_identity=identity(toy), tags=[tag])
        bundle = read(root / BASE)
        check("a mesh the build left comes back with it",
              all(BRep_Tool.Triangulation_s(face.wrapped, TopLoc_Location()) is not None
                  for face in bundle.shape.faces()))
        check("the bundle records the build's identity and what it reads back as",
              manifest["built_identity"] == identity(toy) and bundle.identity == manifest["identity"]
              == identity(read(root / BASE).shape))
        check("every node keeps label, colour, class and its geometry",
              [_describe(n) for n in _nodes(bundle.shape)] == [_describe(n) for n in _nodes(toy)]
              and all(drift(a, b) is not None and drift(a, b) <= MAX_DRIFT_MM
                      for a, b in zip(_nodes(toy), _nodes(bundle.shape))),
              "max drift %r mm" % manifest["max_drift_mm"])
        check("volume is exact", abs(bundle.shape.volume - toy.volume) < 1e-9,
              "%r vs %r" % (bundle.shape.volume, toy.volume))
        moved = Pos(5, 0, 0) * bundle.shape
        check("a loaded shape places as the built one does",
              drift(moved, Pos(5, 0, 0) * toy) is not None and drift(moved, Pos(5, 0, 0) * toy) <= MAX_DRIFT_MM)
        check("feature tags come back", [t["name"] for t in bundle.tags] == ["chamfer-1"]
              and abs(bundle.tags[0]["shape"].volume - 1.0) < 1e-9)
        os.environ[ENV_BUNDLE] = str(root)
        os.environ[ENV_IDENTITY] = bundle.identity
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            found = for_entry(entry, purpose="self-check")
            other = for_entry(root / "part_other.step.py")
        check("the round's entry reads its bundle and says so",
              found is not None and ("identity %s" % bundle.identity) in stderr.getvalue())
        check("another entry builds from source", other is None)
        write_alias(root / instance_dir(2), entry, 2)
        check("an alias instance reads the base build", for_entry(entry, instance=2).identity == bundle.identity)
        os.environ[ENV_IDENTITY] = "0" * 64
        try:
            for_entry(entry)
        except RuntimeError:
            check("a bundle that is not the round's build is refused", True)
        else:
            check("a bundle that is not the round's build is refused", False)
        (root / BASE / SHAPES).write_bytes(b"tampered")
        try:
            read(root / BASE)
        except RuntimeError:
            check("a changed bundle is refused", True)
        else:
            check("a changed bundle is refused", False)
    print("\n%d failed" % len(failures) if failures else "\nall checks passed")
    return 1 if failures else 0


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-check", action="store_true")
    sub = parser.add_subparsers(dest="command")
    build = sub.add_parser("build", help="build an entry (or one instance) once and keep its B-rep")
    build.add_argument("entry", type=Path)
    build.add_argument("--instance", type=int)
    build.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.self_check:
        return _self_check()
    if args.command != "build":
        parser.error("a command is required: build")
    if args.instance is not None and args.instance < 1:
        parser.error("--instance counts from 1")
    entry = args.entry.resolve()
    if not entry.is_file():
        parser.error("no such entry: %s" % entry)
    what = "%s %s" % (entry.name, instance_dir(args.instance))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            manifest = (build_base(entry, args.out) if args.instance is None
                        else build_instance(entry, args.instance, args.out))
    except Exception as exc:  # noqa: BLE001 - the checks that need it build from source instead
        print("brepbundle: %s not kept: %s: %s" % (what, type(exc).__name__, exc), file=sys.stderr)
        return 1
    kept = {"path": str(args.out.resolve()), "identity": manifest.get("identity"), "alias": manifest.get("alias"),
            "builtIdentity": manifest.get("built_identity"), "maxDriftMm": manifest.get("max_drift_mm")}
    print(json.dumps({"instance": args.instance, "brepBundle": kept}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
