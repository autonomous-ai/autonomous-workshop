"""Measure a STEP solid, and rebuild editable source from what it proves.

A STEP file is a boundary representation: exact surfaces with no feature
history. Nothing in it records that a face was an extrude, a hole or a fillet,
and nothing records a parameter name or the relationship between two
dimensions. So there is no decompile here. What there is:

    measure     every surface's analytic parameters, exactly as the kernel
                holds them -- plane origins, cylinder axes and radii, cone
                half-angles, torus minor radii
    rebuild     a solid whose every lateral face is parallel to one direction
                is a stack of prisms; the cross-section between consecutive cap
                planes reproduces each prism exactly, so slab decomposition
                emits source that *is* the original rather than resembling it
    prove       the recovered source is run and the result compared against the
                STEP by symmetric difference, so the claim is measured

The third stage is what makes the first two usable. Volume agreement alone
passes shapes that are wrong in compensating ways -- a hole moved, a boss
grown and a pocket deepened -- so every comparison here is the material in one
solid and not the other, both ways round.
"""
from __future__ import annotations

import hashlib
import importlib.util
import math
import sys
from collections import defaultdict
from pathlib import Path

from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Section
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepGProp import BRepGProp
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.IFSelect import IFSelect_RetDone
from OCP.Interface import Interface_Static
from OCP.Message import Message, Message_Gravity
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Reader, STEPControl_Writer
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_REVERSED, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopTools import TopTools_HSequenceOfShape, TopTools_ListOfShape
from OCP.TopoDS import TopoDS
from OCP.gp import gp_Ax1, gp_Dir, gp_Pln, gp_Pnt, gp_Trsf, gp_Vec

SURFACE_KIND = {
    0: "plane", 1: "cylinder", 2: "cone", 3: "sphere", 4: "torus",
    5: "bezier", 6: "bspline", 7: "revolution", 8: "extrusion", 9: "offset",
}
CURVE_KIND = {
    0: "line", 1: "circle", 2: "ellipse", 3: "hyperbola", 4: "parabola",
    5: "bezier", 6: "bspline", 7: "offset", 8: "other",
}
ANALYTIC = {"plane", "cylinder", "cone", "sphere", "torus"}
# Surfaces a constant cross-section reproduces exactly. A cone shares the
# extrusion axis but tapers along it, so axis-aligned is necessary for slab
# decomposition and not sufficient.
EXTRUDABLE = {"plane", "cylinder"}
# Surfaces a ruled loft between two sections reproduces exactly. A cone is
# straight along its generatrices, so lofting the slab it lives in is not an
# approximation; a torus is curved along them, so lofting a fillet is one, and
# that difference decides which recoveries need a flag and which do not.
RULED = {"cone"}
# Surfaces that have an axis at all. A fillet around a bore or a rim is a torus
# sharing the part's axis: it cannot be extruded and it does not stop the rest
# of the part from being, so it has to reach the slab that contains it rather
# than disqualify every direction up front.
AXIAL = {"cylinder", "cone", "torus"}
TOL = 1e-6


# --------------------------------------------------------------------------
# reading and writing
# --------------------------------------------------------------------------

# The STEP writer prints a transfer report to stdout through OpenCASCADE's own
# messenger, which would land in the middle of this toolchain's JSON. Raise the
# trace level so only failures speak.
for _printer in Message.DefaultMessenger_s().Printers():
    _printer.SetTraceLevel(Message_Gravity.Message_Fail)


def read_step(path):
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise SystemExit(f"cannot read STEP: {path}")
    reader.TransferRoots()
    return reader.OneShape()


def all_planar(shape):
    """True when the shape has faces and every one of them is planar."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Plane
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    if not explorer.More():
        return False
    while explorer.More():
        if BRepAdaptor_Surface(TopoDS.Face_s(explorer.Current())).GetType() != GeomAbs_Plane:
            return False
        explorer.Next()
    return True


def write_step(shape, path):
    Interface_Static.SetCVal_s("write.step.schema", "AP214")
    # A planar face's pcurves are exact projections every reader recomputes;
    # on a faceted solid they are over half the file. Curved faces keep them.
    Interface_Static.SetIVal_s("write.surfacecurve.mode", 0 if all_planar(shape) else 1)
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    if writer.Write(str(path)) != IFSelect_RetDone:
        raise SystemExit(f"cannot write STEP: {path}")
    return Path(path)


def load_entry(path):
    """Run a `<name>.step.py` entry and return its TopoDS shape.

    The entry convention is the repository's: exactly one module-level
    `gen_step()` returning the shape. Recovered source obeys it so that the
    file which proves the recovery is the same file the CAD skill builds.
    """
    path = Path(path).resolve()
    name = "recovered_" + path.name.replace(".", "_").replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    # Seed sys.path with the entry's own folder so a Tier 3 entry's module-top
    # imports (its sibling params/parts/features packages) resolve, the way the
    # CAD skill's generator loader does. Without it this function can only load
    # a single-file entry, which is not the file the CAD skill builds.
    original_sys_path = list(sys.path)
    entry_dir = str(path.parent)
    if entry_dir not in sys.path:
        sys.path.insert(0, entry_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = original_sys_path
        sys.modules.pop(name, None)
    if not hasattr(module, "gen_step"):
        raise SystemExit(f"{path} defines no module-level gen_step()")
    return to_topods(module.gen_step())


def to_topods(shape):
    """Accept a build123d/cadquery object or a raw TopoDS shape."""
    for attribute in ("wrapped",):
        if hasattr(shape, attribute):
            inner = getattr(shape, attribute)
            if inner is not None:
                return inner
    if hasattr(shape, "val"):          # a cadquery Workplane
        return to_topods(shape.val())
    return shape


def load_shape(path):
    path = Path(path)
    if path.name.endswith(".py"):
        return load_entry(path)
    return read_step(path)


def digest(path, length=12):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:length]


# --------------------------------------------------------------------------
# measuring
# --------------------------------------------------------------------------

def explore(shape, kind):
    exp = TopExp_Explorer(shape, kind)
    while exp.More():
        yield exp.Current()
        exp.Next()


def _r(value, digits):
    return round(float(value), digits)


def _pt(p, digits):
    return [_r(p.X(), digits), _r(p.Y(), digits), _r(p.Z(), digits)]


def _canonical_dir(d, digits):
    """Direction with a deterministic sign, so +Z and -Z group together."""
    v = [d.X(), d.Y(), d.Z()]
    for component in v:
        if abs(component) > TOL:
            if component < 0:
                v = [-c for c in v]
            break
    return [_r(c, digits) + 0.0 for c in v]


def bbox(shape, digits=4):
    box = Bnd_Box()
    BRepBndLib.Add_s(shape, box)
    xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    return {
        "min": [_r(xmin, digits), _r(ymin, digits), _r(zmin, digits)],
        "max": [_r(xmax, digits), _r(ymax, digits), _r(zmax, digits)],
        "size": [_r(xmax - xmin, digits), _r(ymax - ymin, digits), _r(zmax - zmin, digits)],
    }


def volume(shape):
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return abs(props.Mass())


def mass_props(shape, digits=4):
    vol, area = GProp_GProps(), GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, vol)
    BRepGProp.SurfaceProperties_s(shape, area)
    return {
        "volume": _r(abs(vol.Mass()), digits),
        "area": _r(area.Mass(), digits),
        "centerOfMass": _pt(vol.CentreOfMass(), digits),
    }


def surface_params(face, digits):
    adaptor = BRepAdaptor_Surface(face)
    kind = SURFACE_KIND.get(int(adaptor.GetType()), "other")
    params = {"kind": kind}
    if kind == "plane":
        plane = adaptor.Plane()
        params["origin"] = _pt(plane.Location(), digits)
        params["normal"] = _canonical_dir(plane.Axis().Direction(), digits)
        # Full precision alongside the readable value: four decimals of a
        # direction is a tilt of tens of microradians, and a section cut
        # through a cylinder on a tilted axis is an ellipse.
        params["normalExact"] = _canonical_dir(plane.Axis().Direction(), 12)
    elif kind == "cylinder":
        cyl = adaptor.Cylinder()
        params["origin"] = _pt(cyl.Location(), digits)
        params["axis"] = _canonical_dir(cyl.Axis().Direction(), digits)
        params["axisExact"] = _canonical_dir(cyl.Axis().Direction(), 12)
        params["radius"] = _r(cyl.Radius(), digits)
    elif kind == "cone":
        cone = adaptor.Cone()
        params["origin"] = _pt(cone.Location(), digits)
        params["axis"] = _canonical_dir(cone.Axis().Direction(), digits)
        params["axisExact"] = _canonical_dir(cone.Axis().Direction(), 12)
        params["semiAngleDeg"] = _r(math.degrees(cone.SemiAngle()), digits)
        params["refRadius"] = _r(cone.RefRadius(), digits)
    elif kind == "sphere":
        sph = adaptor.Sphere()
        params["center"] = _pt(sph.Location(), digits)
        params["radius"] = _r(sph.Radius(), digits)
    elif kind == "torus":
        tor = adaptor.Torus()
        params["center"] = _pt(tor.Location(), digits)
        params["axis"] = _canonical_dir(tor.Axis().Direction(), digits)
        params["axisExact"] = _canonical_dir(tor.Axis().Direction(), 12)
        params["majorRadius"] = _r(tor.MajorRadius(), digits)
        params["minorRadius"] = _r(tor.MinorRadius(), digits)
    params["uPeriodic"] = bool(adaptor.IsUPeriodic())
    params["uSpanDeg"] = (
        _r(math.degrees(adaptor.LastUParameter() - adaptor.FirstUParameter()), 1)
        if kind in {"cylinder", "cone", "torus", "sphere"} else None)
    return params


def face_report(face, index, digits):
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(face, props)
    entry = {"index": index, "area": _r(props.Mass(), digits),
             "center": _pt(props.CentreOfMass(), digits),
             "reversed": face.Orientation() == TopAbs_REVERSED}
    entry.update(surface_params(TopoDS.Face_s(face), digits))
    return entry


def edge_kinds(shape):
    counts = defaultdict(int)
    for edge in explore(shape, TopAbs_EDGE):
        adaptor = BRepAdaptor_Curve(TopoDS.Edge_s(edge))
        counts[CURVE_KIND.get(int(adaptor.GetType()), "other")] += 1
    return dict(counts)


def _band_role(span, inward):
    """Name a cylindrical band from its sweep and which way it faces.

    On a mirrored half-part a bore is cut in two, so a 180 degree band is
    reported as a half bore rather than forced into hole/boss -- and the
    inward flag is unreliable there, which the name says out loud.
    """
    if span > 359.0:
        return "hole" if inward else "boss"
    if 170.0 <= span <= 190.0:
        return "half cylinder (mirror seam: bore or boss, check the mating half)"
    return "pocket wall" if inward else "arc wall"


def detect_bands(faces, digits):
    """Group cylindrical faces into coaxial, equal-radius bands.

    Two patches of one bore split at the seam must land in the same band, so
    the key is the axis *line* plus the radius -- not the face origin, which
    sits anywhere along the axis.
    """
    groups = defaultdict(list)
    for face in faces:
        if face["kind"] != "cylinder":
            continue
        axis = tuple(face["axis"])
        origin = face["origin"]
        # Drop the along-axis component so a patch anywhere on the bore keys
        # to the same point.
        dot = sum(origin[i] * axis[i] for i in range(3))
        perp = tuple(round(origin[i] - dot * axis[i], 3) for i in range(3))
        groups[(axis, perp, round(face["radius"], 4))].append(face)

    bands = []
    for (axis, perp, radius), members in groups.items():
        span = sum(m["uSpanDeg"] or 0 for m in members)
        # A hole's wall faces the axis: every patch is reversed, and the
        # patches together close a full turn.
        inward = all(m["reversed"] for m in members)
        bands.append({
            "axis": list(axis),
            "axisPoint": list(perp),
            "radius": radius,
            "diameter": _r(radius * 2, digits),
            "faceIndices": sorted(m["index"] for m in members),
            "spanDeg": _r(span, 1),
            "closed": span > 359.0,
            "inward": inward,
            "role": _band_role(span, inward),
        })
    bands.sort(key=lambda b: (b["axis"], b["axisPoint"], b["radius"]))

    # Coaxial holes of differing radius are one stepped bore.
    stepped = defaultdict(list)
    for band in bands:
        if band["role"] == "hole":
            stepped[(tuple(band["axis"]), tuple(band["axisPoint"]))].append(band["diameter"])
    steps = [{"axis": list(k[0]), "axisPoint": list(k[1]), "diameters": sorted(v)}
             for k, v in stepped.items() if len(v) > 1]

    # Concentric partial bands are an arc slot or arch, not two separate walls.
    concentric = defaultdict(list)
    for band in bands:
        if not band["closed"]:
            concentric[(tuple(band["axis"]), tuple(band["axisPoint"]))].append(band)
    arcs = [{"axis": list(k[0]), "axisPoint": list(k[1]),
             "radii": sorted(b["radius"] for b in members),
             "reading": "concentric arc pair -> arc slot / arch of "
                        f"{max(b['radius'] for b in members) - min(b['radius'] for b in members):.4g} wall"}
            for k, members in concentric.items() if len(members) > 1]
    return bands, steps, arcs


def detect_chamfers(faces, digits):
    """Conical faces are chamfers, countersinks or draft -- read by half-angle."""
    out = []
    for face in faces:
        if face["kind"] != "cone":
            continue
        angle = abs(face["semiAngleDeg"])
        out.append({
            "faceIndex": face["index"],
            "semiAngleDeg": face["semiAngleDeg"],
            "axis": face["axis"],
            "refRadius": face["refRadius"],
            "inward": face["reversed"],
            "reading": "45 deg chamfer" if abs(angle - 45) < 0.5 else
                       (f"countersink-like taper, {angle:.1f} deg half-angle"
                        if 35 <= angle < 45 else f"taper, {angle:.1f} deg half-angle"),
        })
    return out


def detect_fillets(faces, digits):
    """Torus faces are fillets outright, and carry the radius to re-apply."""
    out = [{"faceIndex": f["index"], "radius": f["minorRadius"],
            "evidence": "torus minor radius", "confidence": "certain"}
           for f in faces if f["kind"] == "torus"]
    radii = defaultdict(list)
    for entry in out:
        radii[entry["radius"]].append(entry["faceIndex"])
    return {"candidates": out, "radiiSeen": {str(k): v for k, v in sorted(radii.items())}}


def extrusion_axes(faces):
    """Directions along which a constant cross-section could sweep the solid.

    A direction qualifies when every planar face is either perpendicular to it
    (a cap) or parallel to it (a wall), and every cylinder or cone shares it.
    `slabDecomposable` is the stricter question -- whether the cross-section is
    genuinely constant -- and it is false as soon as any face tapers or curves
    along the axis, however well aligned that face is.
    """
    candidates = {}
    for face in faces:
        if face["kind"] == "plane":
            candidates.setdefault(tuple(face["normal"]), tuple(face["normalExact"]))
        elif face["kind"] in AXIAL:
            candidates.setdefault(tuple(face["axis"]), tuple(face["axisExact"]))
    results = []
    for direction in sorted(candidates):
        caps, walls, ok = [], [], True
        for face in faces:
            if face["kind"] == "plane":
                dot = abs(sum(face["normal"][i] * direction[i] for i in range(3)))
                if dot > 1 - 1e-4:
                    caps.append(face["index"])
                elif dot < 1e-4:
                    walls.append(face["index"])
                else:
                    ok = False
                    break
            elif face["kind"] in AXIAL:
                if abs(sum(face["axis"][i] * direction[i] for i in range(3))) < 1 - 1e-4:
                    ok = False
                    break
            else:
                ok = False
                break
        if ok:
            blockers = sorted({f["kind"] for f in faces if f["kind"] not in EXTRUDABLE})
            results.append({"direction": list(direction),
                            "directionExact": list(candidates[direction]),
                            "capFaces": caps, "wallFaces": walls,
                            "slabDecomposable": not blockers,
                            "blockingSurfaceKinds": blockers})
    return results


def analyse(shape, digits=4, max_faces=400):
    faces = [face_report(f, i, digits) for i, f in enumerate(explore(shape, TopAbs_FACE))]
    kinds = defaultdict(int)
    for face in faces:
        kinds[face["kind"]] += 1
    analytic = sum(v for k, v in kinds.items() if k in ANALYTIC)
    total = len(faces) or 1
    bands, stepped, arcs = detect_bands(faces, digits)

    report = {
        "faceCount": len(faces),
        "solidCount": len(list(explore(shape, TopAbs_SOLID))),
        "faceKinds": dict(sorted(kinds.items(), key=lambda kv: -kv[1])),
        "analyticFraction": round(analytic / total, 4),
        "allAnalytic": analytic == total,
        "bbox": bbox(shape, digits),
        "mass": mass_props(shape, digits),
        "edgeKinds": edge_kinds(shape),
        "cylindricalBands": bands,
        "steppedBores": stepped,
        "arcSlots": arcs,
        "chamfers": detect_chamfers(faces, digits),
        "fillets": detect_fillets(faces, digits),
        "extrusionAxes": extrusion_axes(faces),
    }
    report["faces"] = faces if len(faces) <= max_faces else faces[:max_faces]
    report["facesTruncated"] = len(faces) > max_faces
    return report


# --------------------------------------------------------------------------
# slab decomposition
# --------------------------------------------------------------------------

class RecoveryError(RuntimeError):
    """Raised when the source cannot be rebuilt without silently differing."""


def align_to_z(shape, direction):
    """Rotate `shape` so `direction` becomes +Z.

    Returns the rotated shape and the undo rotation, because a part recovered
    in the rotated frame is not the part the STEP holds: the emitted source
    rotates back, so the recovery can be compared against the original file in
    its own pose rather than only in shape.
    """
    d = gp_Dir(*direction)
    z = gp_Dir(0, 0, 1)
    if d.IsParallel(z, 1e-7):
        return shape, None
    axis_vec = gp_Vec(d).Crossed(gp_Vec(z))
    angle = gp_Vec(d).Angle(gp_Vec(z))
    trsf = gp_Trsf()
    trsf.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(axis_vec)), angle)
    moved = BRepBuilderAPI_Transform(shape, trsf, True).Shape()
    undo = ((round(axis_vec.X(), 9), round(axis_vec.Y(), 9), round(axis_vec.Z(), 9)),
            round(math.degrees(angle), 9))
    return moved, undo


def slab_boundaries(shape, tol=1e-6):
    """Z values where the cross-section is allowed to change.

    Every plane perpendicular to Z is one, which is the whole story for a
    prismatic part. It is not the whole story for a chamfer: the circle where a
    cone meets the cylinder below it is an edge, not a face, so a boundary set
    read from planes alone spans the taper across the entire part and a single
    loft replaces the post with a cone. Adding the top and bottom of every face
    that is not extrudable confines each taper to its own slab, where a ruled
    loft reproduces it exactly.

    Heights within `tol` are one boundary: two planes a nanometre apart are a
    tolerance artefact, and treating them as two emits a slab of zero height
    that no kernel can extrude.
    """
    heights = set()
    for face in explore(shape, TopAbs_FACE):
        adaptor = BRepAdaptor_Surface(TopoDS.Face_s(face))
        kind = SURFACE_KIND.get(int(adaptor.GetType()), "other")
        if kind == "plane":
            if abs(abs(adaptor.Plane().Axis().Direction().Z()) - 1.0) < 1e-7:
                heights.add(round(adaptor.Plane().Location().Z(), 9))
        elif kind not in EXTRUDABLE:
            box = bbox(face, 9)
            heights.add(box["min"][2])
            heights.add(box["max"][2])

    merged = []
    for z in sorted(heights):
        if merged and z - merged[-1] <= tol:
            continue
        merged.append(z)
    return merged


def section_wires(shape, z):
    """Closed wires of the solid's cross-section at height z."""
    section = BRepAlgoAPI_Section(shape, gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1)), False)
    section.ComputePCurveOn1(True)
    section.Approximation(True)
    section.Build()
    if not section.IsDone():
        return []
    edges = TopTools_HSequenceOfShape()
    for edge in explore(section.Shape(), TopAbs_EDGE):
        edges.Append(edge)
    if edges.Length() == 0:
        return []
    wires = TopTools_HSequenceOfShape()
    ShapeAnalysis_FreeBounds.ConnectEdgesToWires_s(edges, 1e-6, False, wires)
    return [TopoDS.Wire_s(wires.Value(i)) for i in range(1, wires.Length() + 1)]


def ordered_edges(wire):
    """Edges of a wire in connection order, oriented as the wire runs.

    TopExp_Explorer returns them in storage order with their own orientation,
    which is enough to count edges and wrong for anything that needs the walk:
    one reversed edge sampled from its stored start makes a crossed polygon,
    whose area and containment are both meaningless.
    """
    edges = []
    explorer = BRepTools_WireExplorer(wire)
    while explorer.More():
        edges.append(explorer.Current())
        explorer.Next()
    if not edges:        # the explorer refuses a wire it considers degenerate
        edges = [TopoDS.Edge_s(e) for e in explore(wire, TopAbs_EDGE)]
    return edges


def edge_range(edge):
    """Parameter range of an edge in the direction the wire traverses it."""
    curve = BRepAdaptor_Curve(edge)
    first, last = curve.FirstParameter(), curve.LastParameter()
    if edge.Orientation() == TopAbs_REVERSED:
        first, last = last, first
    return curve, first, last


def wire_points(wire, per_arc=16):
    """Polyline approximation of a wire, for area and containment only."""
    pts = []
    for edge in ordered_edges(wire):
        curve, first, last = edge_range(edge)
        steps = 1 if int(curve.GetType()) == 0 else per_arc
        for i in range(steps):
            p = curve.Value(first + (last - first) * i / steps)
            pts.append((p.X(), p.Y()))
    return pts


def polygon_area(pts):
    if len(pts) < 3:
        return 0.0
    total = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0


def polygon_centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    for i in range(len(polygon)):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % len(polygon)]
        if (y0 > y) != (y1 > y):
            if x < (x1 - x0) * (y - y0) / (y1 - y0 + 1e-300) + x0:
                inside = not inside
    return inside


def group_regions(wires):
    """Sort a section's wires into (outer, inners) regions by nesting depth.

    Ranking by area alone mistakes an island for a hole: a boss standing inside
    a pocket is depth 2, not a second cut. Counting how many wires enclose each
    one separates them, and each hole is then attached to the smallest wire
    that actually contains it rather than to whichever is biggest.
    """
    polys = [wire_points(w) for w in wires]
    areas = [polygon_area(p) for p in polys]
    depth = []
    for i, poly in enumerate(polys):
        probe = poly[0]
        depth.append(sum(1 for j, other in enumerate(polys)
                         if j != i and point_in_polygon(probe, other)))

    regions = []
    for i in sorted(range(len(wires)), key=lambda k: -areas[k]):
        if depth[i] % 2 == 0:
            regions.append({"outer": wires[i], "outerPoly": polys[i],
                            "area": areas[i], "inners": []})
    for i in range(len(wires)):
        if depth[i] % 2 == 0:
            continue
        holders = [r for r in regions if point_in_polygon(polys[i][0], r["outerPoly"])]
        if not holders:
            continue
        min(holders, key=lambda r: r["area"])["inners"].append(wires[i])
    return regions


def wire_segments(wire, digits):
    """Ordered segments of a wire, as dicts the emitter renders.

    Arcs are exported as three-point arcs: the midpoint carries the sweep
    direction and the major/minor choice implicitly, so no sign convention has
    to survive the round trip.
    """
    segments = []
    for edge in ordered_edges(wire):
        curve, first, last = edge_range(edge)
        start, end = curve.Value(first), curve.Value(last)
        mid = curve.Value(first + (last - first) / 2.0)
        kind = int(curve.GetType())
        seg = {"start": (round(start.X(), digits), round(start.Y(), digits)),
               "end": (round(end.X(), digits), round(end.Y(), digits)),
               "mid": (round(mid.X(), digits), round(mid.Y(), digits))}
        if kind == 0:
            seg["kind"] = "line"
        elif kind == 1:
            circle = curve.Circle()
            seg["kind"] = "arc"
            seg["radius"] = round(circle.Radius(), digits)
            seg["center"] = (round(circle.Location().X(), digits),
                             round(circle.Location().Y(), digits))
            seg["full"] = abs(abs(last - first) - 2 * math.pi) < 1e-7
        else:
            seg["kind"] = "unsupported"
            seg["curveType"] = CURVE_KIND.get(kind, str(kind))
        segments.append(seg)
    return segments


def is_full_circle(segments):
    return len(segments) == 1 and segments[0]["kind"] == "arc" and segments[0]["full"]


def slab_blockers(shape, z0, z1, digits=4):
    """Surface kinds inside this slab that a constant cross-section misses.

    Asked per slab rather than per part: a chamfer at one end does not stop the
    other five slabs from being reproduced exactly, and saying which slab is
    approximate is the difference between a usable file and a rejected one.
    """
    margin = min((z1 - z0) * 0.01, 1e-3)
    kinds = set()
    for face in explore(shape, TopAbs_FACE):
        kind = SURFACE_KIND.get(int(BRepAdaptor_Surface(TopoDS.Face_s(face)).GetType()), "other")
        if kind in EXTRUDABLE:
            continue
        box = bbox(face, 6)
        if box["max"][2] > z0 + margin and box["min"][2] < z1 - margin:
            kinds.add(kind)
    return sorted(kinds)


def regions_at(shape, z, digits):
    out = []
    for region in group_regions(section_wires(shape, z)):
        out.append({
            "outer": wire_segments(region["outer"], digits),
            "inners": [wire_segments(w, digits) for w in region["inners"]],
            "centroid": polygon_centroid(region["outerPoly"]),
            "innerCentroids": [polygon_centroid(wire_points(w)) for w in region["inners"]],
        })
    return out


def _pair_regions(lower, upper, z0, z1):
    """Match the regions of two sections by nearest centre.

    Two sections of one taper have the same layout, so nearest-centre pairing
    is unambiguous; a differing count means the cross-section changes topology
    inside the slab, which no single loft reproduces.
    """
    if len(lower) != len(upper):
        raise RecoveryError(
            f"the slab z {z0:g}..{z1:g} has {len(lower)} regions at the bottom and "
            f"{len(upper)} at the top: its cross-section changes topology, which no "
            f"single loft reproduces. Give the feature its own cap plane, or author "
            f"it by hand.")
    remaining = list(range(len(upper)))
    pairs = []
    for index, low in enumerate(lower):
        cx, cy = low["centroid"]
        best = min(remaining,
                   key=lambda j: (upper[j]["centroid"][0] - cx) ** 2
                   + (upper[j]["centroid"][1] - cy) ** 2)
        remaining.remove(best)
        pairs.append((index, best))
    return pairs


def build_slabs(shape, digits=4, loft_tapers=False):
    """Cut the solid at every cap plane and describe each slab for the emitter."""
    heights = slab_boundaries(shape)
    if len(heights) < 2:
        raise RecoveryError(
            "no pair of boundaries perpendicular to the extrusion axis: there "
            "is nothing to extrude between. Run step_probe for the fact sheet.")

    slabs = []
    for index, (z0, z1) in enumerate(zip(heights, heights[1:])):
        height = z1 - z0
        blockers = slab_blockers(shape, z0, z1, digits)
        curved = [k for k in blockers if k not in RULED]
        if curved and not loft_tapers:
            raise RecoveryError(
                f"the slab z {z0:g}..{z1:g} contains {', '.join(curved)} faces, which "
                f"curve along the extrusion axis. A loft across them is an "
                f"approximation, not a rebuild, so it is not done unsolicited.\n"
                f"  fillets: recover the sharp body and re-apply fillet() in source -- "
                f"step_probe reports every radius, and the result verifies to zero\n"
                f"  freeform: keep the STEP as a purchased part under <project>/ref/\n"
                f"  either way: --loft-tapers emits the approximation and the round "
                f"trip reports what it costs")
        if not blockers:
            regions = regions_at(shape, (z0 + z1) / 2.0, digits)
            if not regions:
                continue            # a genuine void between two solid regions
            slabs.append({"kind": "extrude", "i0": index, "i1": index + 1,
                          "z0": z0, "z1": z1, "regions": regions, "blockers": []})
            continue

        # Tapered slab: measure just inside each cap so the section is taken on
        # unambiguous geometry, then loft between the two. The inset is 1e-5 of
        # the slab height, which moves a 45 degree wall by the same fraction of
        # a millimetre -- far below what the verifier's tolerance cares about,
        # and reported in the emitted file either way.
        inset = max(height * 1e-5, 1e-7)
        lower = regions_at(shape, z0 + inset, digits)
        upper = regions_at(shape, z1 - inset, digits)
        if not lower or not upper:
            continue
        pairs = _pair_regions(lower, upper, z0, z1)
        matched = []
        for li, ui in pairs:
            low, up = lower[li], upper[ui]
            if len(low["inners"]) != len(up["inners"]):
                raise RecoveryError(
                    f"the slab z {z0:g}..{z1:g} has {len(low['inners'])} holes at the "
                    f"bottom and {len(up['inners'])} at the top: a hole that starts or "
                    f"ends inside a taper needs its own cap plane. Author it by hand.")
            inner_pairs = []
            used = list(range(len(up["inners"])))
            for k, centroid in enumerate(low["innerCentroids"]):
                best = min(used, key=lambda j: (up["innerCentroids"][j][0] - centroid[0]) ** 2
                           + (up["innerCentroids"][j][1] - centroid[1]) ** 2)
                used.remove(best)
                inner_pairs.append((low["inners"][k], up["inners"][best]))
            matched.append({"outer": (low["outer"], up["outer"]), "inners": inner_pairs})
        slabs.append({"kind": "loft", "i0": index, "i1": index + 1,
                      "z0": z0, "z1": z1, "regions": matched,
                      "blockers": blockers, "inset": inset})
    if not slabs:
        raise RecoveryError("every slab was empty: the solid has no material between "
                            "its cap planes, which means the extrusion axis is wrong.")
    return heights, slabs


# --------------------------------------------------------------------------
# emitting source
# --------------------------------------------------------------------------

# The emitted header carries the round-trip result, so the file states how far
# it is from the STEP instead of leaving the reader to assume. It can only be
# filled in once the file exists and has been run, so it goes in as a marker.
ROUNDTRIP_MARKER = "<not measured>"


def stamp_roundtrip(source, text):
    return source.replace(ROUNDTRIP_MARKER, text, 1)


def _profile_lines(segments, indent, subtract):
    pad = " " * indent
    mode = ", mode=Mode.SUBTRACT" if subtract else ""
    if is_full_circle(segments):
        cx, cy = segments[0]["center"]
        return [f"{pad}with Locations(({cx:g}, {cy:g})):",
                f"{pad}    Circle({segments[0]['radius']:g}{mode})"]
    out = [f"{pad}with BuildLine():"]
    for seg in segments:
        sx, sy = seg["start"]
        ex, ey = seg["end"]
        if seg["kind"] == "line":
            out.append(f"{pad}    Line(({sx:g}, {sy:g}), ({ex:g}, {ey:g}))")
        elif seg["kind"] == "arc":
            mx, my = seg["mid"]
            out.append(f"{pad}    ThreePointArc((({sx:g}, {sy:g}), ({mx:g}, {my:g}), "
                       f"({ex:g}, {ey:g})))")
        else:
            raise RecoveryError(
                f"a {seg.get('curveType')} curve is in the cross-section: the profile "
                f"is not made of lines and arcs, so it cannot be written as source "
                f"without approximating the curve. Author this profile by hand.")
    out.append(f"{pad}make_face({'mode=Mode.SUBTRACT' if subtract else ''})")
    return out


def _sketch(plane_expr, rings, indent):
    lines = [f"{' ' * indent}with BuildSketch({plane_expr}):"]
    lines.extend(_profile_lines(rings[0], indent + 4, False))
    for inner in rings[1]:
        lines.extend(_profile_lines(inner, indent + 4, True))
    return lines


def emit_source(heights, slabs, undo, meta):
    """Write the recovered solid as a repository entry.

    The file is a `<name>.step.py` with one module-level `gen_step()` because
    that is what the CAD skill builds and verifies: a recovery that cannot be
    fed straight into `gen` would have to be transcribed by hand, and a
    transcription is exactly the step that loses the numbers.
    """
    lofted = sum(1 for s in slabs if s["kind"] == "loft")
    axis = ", ".join(f"{c:g}" for c in meta["axis"])
    head = [f'"""{meta["stem"]} -- recovered from {meta["source"]} by skills/step-to-source.',
            "",
            f"Slab decomposition along ({axis}): {len(slabs)} slabs"
            + (f", {lofted} of them lofted across a taper." if lofted else "."),
            "",
            "The B-rep held exact geometry and no feature history, so every number",
            "below is a measurement of that file, not a design intent. No parameter",
            "name, no relationship between two dimensions and no clearance survived",
            "the export that made it: editing one number here moves only the faces",
            "measured from it. Re-parameterise before treating this as the project's",
            "parametric source.",
            ""]
    if lofted:
        head += ["A lofted slab is measured just inside each boundary, so a straight",
                 "taper is reproduced and a curved one is approximated -- the round",
                 "trip below is what says which happened here. Either way the result",
                 "is geometry, not a feature: to get a parametric chamfer or fillet,",
                 "flatten the slab back to its untapered profile and re-apply",
                 "chamfer() or fillet() in source.",
                 ""]
    head += [f"Source STEP: {meta['source']} (sha256 {meta['digest']}, "
             f"{meta['faces']} faces, {meta['solids']} solid(s))",
             f"Round trip at recovery: {ROUNDTRIP_MARKER}",
             "That number is this file as it was written. Re-run",
             "skills/step-to-source/scripts/step_verify after every edit.",
             '"""',
             "from build123d import *",
             "",
             "PRINTABLE = False  # recovered in the STEP's own pose, not on a Z=0 bed datum",
             "",
             f"# Slab boundaries measured from {meta['source']}, mm: every plane across",
             "# the extrusion axis, plus the top and bottom of every taper.",
             "SLAB_Z = [" + ", ".join(f"{z:g}" for z in heights) + "]",
             "",
             "",
             "def gen_step():",
             "    with BuildPart() as part:"]

    body = []
    for slab in slabs:
        z0 = f"SLAB_Z[{slab['i0']}]"
        z1 = f"SLAB_Z[{slab['i1']}]"
        if slab["kind"] == "extrude":
            body.append(f"        # slab {slab['i0']}: z {slab['z0']:g} -> {slab['z1']:g}")
            for region in slab["regions"]:
                body.extend(_sketch(f"Plane.XY.offset({z0})",
                                    (region["outer"], region["inners"]), 8))
                body.append(f"        extrude(amount={z1} - {z0})")
        else:
            body.append(f"        # slab {slab['i0']}: z {slab['z0']:g} -> {slab['z1']:g}, "
                        f"{'/'.join(slab['blockers'])} walls; lofted between sections")
            body.append(f"        # measured {slab['inset']:g} mm inside each boundary")
            for region in slab["regions"]:
                low, up = region["outer"]
                body.extend(_sketch(f"Plane.XY.offset({z0})", (low, []), 8))
                body.extend(_sketch(f"Plane.XY.offset({z1})", (up, []), 8))
                body.append("        loft(ruled=True)")
                for inner_low, inner_up in region["inners"]:
                    body.extend(_sketch(f"Plane.XY.offset({z0})", (inner_low, []), 8))
                    body.extend(_sketch(f"Plane.XY.offset({z1})", (inner_up, []), 8))
                    body.append("        loft(ruled=True, mode=Mode.SUBTRACT)")

    tail = []
    if undo:
        (ax, ay, az), angle = undo
        tail += ["",
                 f"    # the source STEP is extruded along ({axis}); the stack above was",
                 "    # built on +Z, so rotate it back into the file's own pose",
                 f"    return part.part.rotate(Axis((0, 0, 0), ({ax:g}, {ay:g}, {az:g})), "
                 f"{-angle:g})"]
    else:
        tail += ["", "    return part.part"]
    return "\n".join(head + body + tail) + "\n"


def recover(step_path, digits=4, loft_tapers=False):
    """STEP -> entry source. Returns (source_text, slabs, report)."""
    step_path = Path(step_path)
    shape = read_step(step_path)
    report = analyse(shape, digits, 0)
    axes = report["extrusionAxes"]
    if not axes:
        kinds = ", ".join(f"{k}={v}" for k, v in report["faceKinds"].items())
        raise RecoveryError(
            f"{step_path.name}: no direction leaves every face parallel or "
            f"perpendicular to it, so the solid is not a stack of prisms in any "
            f"orientation ({kinds}).\nSlab decomposition has nothing to offer here. "
            f"Run step_probe for the fact sheet and author the source against it, or "
            f"keep the STEP as a purchased part under <project>/ref/.")
    exact = [a for a in axes if a["slabDecomposable"]]
    chosen = (exact or axes)[0]
    direction = chosen["directionExact"]
    aligned, undo = align_to_z(shape, direction)
    heights, slabs = build_slabs(aligned, digits, loft_tapers)
    meta = {"stem": step_path.stem, "source": step_path.name,
            "digest": digest(step_path), "axis": chosen["direction"],
            "faces": report["faceCount"], "solids": report["solidCount"]}
    return emit_source(heights, slabs, undo, meta), slabs, report


# --------------------------------------------------------------------------
# proving the recovery
# --------------------------------------------------------------------------

# OpenCASCADE booleans go degenerate when two solids share many coincident
# faces, which is exactly the case here: a good recovery matches the original
# almost everywhere. Rather than hide that behind one loose tolerance, escalate
# the fuzzy value only as far as needed and report which one was used, so the
# precision floor under every number below stays visible.
FUZZ_LADDER = (0.0, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3)


def _as_list(shape):
    items = TopTools_ListOfShape()
    items.Append(shape)
    return items


def _boolean(op, a, b, fuzz):
    builder = op()
    builder.SetArguments(_as_list(a))
    builder.SetTools(_as_list(b))
    if fuzz:
        builder.SetFuzzyValue(fuzz)
    builder.Build()
    return builder.Shape() if builder.IsDone() else None


def _booleans_at(a, b, fuzz):
    shared = _boolean(BRepAlgoAPI_Common, a, b, fuzz)
    missing = _boolean(BRepAlgoAPI_Cut, a, b, fuzz)
    extra = _boolean(BRepAlgoAPI_Cut, b, a, fuzz)
    if shared is None or missing is None or extra is None:
        return None
    return volume(shared), volume(missing), volume(extra)


def compare(original, rebuilt, digits=4):
    """Symmetric difference between two solids, as a fraction of the original.

    Volume agreement is not evidence: a hole moved 3 mm changes no volume at
    all. What decides here is the material in one solid and not the other, both
    ways round, which no compensating pair of errors can hide.
    """
    vol_a, vol_b = volume(original), volume(rebuilt)
    result, used_fuzz = None, None
    for fuzz in FUZZ_LADDER:
        attempt = _booleans_at(original, rebuilt, fuzz)
        if attempt is None:
            continue
        # Two solids of positive volume sharing a bounding box cannot have an
        # empty intersection: an empty one means the boolean gave up quietly.
        if attempt[0] > 0 or not vol_a or not vol_b:
            result, used_fuzz = attempt, fuzz
            break

    box_a, box_b = bbox(original, digits), bbox(rebuilt, digits)
    face_a, face_b = analyse(original, digits, 0), analyse(rebuilt, digits, 0)
    report = {
        "volumeOriginal": round(vol_a, digits),
        "volumeRebuilt": round(vol_b, digits),
        "volumeDeltaPct": round(100 * (vol_b - vol_a) / (vol_a or 1.0), 4),
        "bboxOriginal": box_a["size"],
        "bboxRebuilt": box_b["size"],
        "bboxMatch": box_a["size"] == box_b["size"],
        "faceCountOriginal": face_a["faceCount"],
        "faceCountRebuilt": face_b["faceCount"],
        "faceKindsOriginal": face_a["faceKinds"],
        "faceKindsRebuilt": face_b["faceKinds"],
        "faceKindsMatch": face_a["faceKinds"] == face_b["faceKinds"],
    }
    if result is None:
        report.update({"method": "failed",
                       "symmetricDifferencePct": float("nan"),
                       "matchPct": float("nan")})
        return report
    shared, missing, extra = result
    error = (missing + extra) / (vol_a or 1.0)
    report.update({
        "method": "exact boolean",
        "fuzzyValueMm": used_fuzz,
        "missingVolume": round(missing, digits),
        "extraVolume": round(extra, digits),
        "sharedVolume": round(shared, digits),
        "symmetricDifferencePct": round(100 * error, 6),
        "matchPct": round(100 * (1 - error), 6),
    })
    return report


# --------------------------------------------------------------------------
# fixtures for the self-checks
# --------------------------------------------------------------------------
# Every fixture is built here from primitives rather than read from a project,
# so the self-checks prove a property of this toolchain on geometry they own,
# and keep proving it in a repository that has no projects in it at all.

from OCP.BRepPrimAPI import (  # noqa: E402
    BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCone, BRepPrimAPI_MakeCylinder,
    BRepPrimAPI_MakeSphere,
)
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse  # noqa: E402
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet  # noqa: E402
from OCP.gp import gp_Ax2  # noqa: E402


def _box(x, y, z, dx, dy, dz):
    return BRepPrimAPI_MakeBox(gp_Pnt(x, y, z), dx, dy, dz).Shape()


def _cyl(radius, height, at=(0, 0, 0), axis=(0, 0, 1)):
    return BRepPrimAPI_MakeCylinder(
        gp_Ax2(gp_Pnt(*at), gp_Dir(*axis)), radius, height).Shape()


def _cone(r_bottom, r_top, height, at=(0, 0, 0), axis=(0, 0, 1)):
    return BRepPrimAPI_MakeCone(
        gp_Ax2(gp_Pnt(*at), gp_Dir(*axis)), r_bottom, r_top, height).Shape()


def _fuse(a, b):
    return _boolean(BRepAlgoAPI_Fuse, a, b, 0.0)


def _cut(a, b):
    return _boolean(BRepAlgoAPI_Cut, a, b, 0.0)


def fixture_plate():
    """Planes and cylinders only: two slabs, two bores, one boss."""
    body = _fuse(_box(0, 0, 0, 40, 30, 6), _box(14, 9, 6, 12, 12, 4))
    for x, y in ((8, 15), (32, 15)):
        body = _cut(body, _cyl(2.5, 20, (x, y, -5)))
    return body


def fixture_moved_hole():
    """The plate with one bore 3 mm out of place -- same volume, wrong part."""
    body = _fuse(_box(0, 0, 0, 40, 30, 6), _box(14, 9, 6, 12, 12, 4))
    for x, y in ((8, 15), (29, 15)):
        body = _cut(body, _cyl(2.5, 20, (x, y, -5)))
    return body


def fixture_tilted():
    """The same plate, extruded along a direction that is not +Z."""
    trsf = gp_Trsf()
    trsf.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)), math.radians(30))
    return BRepBuilderAPI_Transform(fixture_plate(), trsf, True).Shape()


def fixture_chamfered():
    """A post with a 45 degree chamfer: one cone face blocks exact extrusion."""
    return _fuse(_cyl(10, 8), _cone(10, 8, 2, (0, 0, 8)))


def fixture_countersunk():
    """A countersink: the taper is inside a hole, not on the outside wall."""
    body = _cut(_box(0, 0, 0, 30, 30, 8), _cyl(2.5, 30, (15, 15, -5)))
    return _cut(body, _cone(2.5, 5.0, 2.5, (15, 15, 5.5)))


def fixture_nested():
    """A pocket holding an island, and a slot with arc ends.

    The island is inside a hole, two levels down, which is what separates
    nesting depth from area ranking: ranked by area alone it reads as a second
    cut and the boss disappears. The slot keeps arcs in the emitted profile.
    """
    body = _cut(_box(0, 0, 0, 60, 40, 8), _box(10, 10, 4, 24, 20, 10))
    body = _fuse(body, _box(18, 16, 4, 8, 8, 4))
    slot = _fuse(_cyl(3, 20, (44, 12, -5)), _cyl(3, 20, (44, 28, -5)))
    return _cut(body, _fuse(slot, _box(41, 12, -5, 6, 16, 20)))


def fixture_filleted():
    """A post with a rolled top edge: one torus face, curved along the axis."""
    post = _cyl(10, 10)
    maker = BRepFilletAPI_MakeFillet(post)
    for edge in explore(post, TopAbs_EDGE):
        box = bbox(edge, 6)
        if abs(box["min"][2] - 10) < 1e-6 and abs(box["max"][2] - 10) < 1e-6:
            maker.Add(2.0, TopoDS.Edge_s(edge))
    return maker.Shape()


def fixture_sphere():
    """No extrusion axis in any orientation."""
    return BRepPrimAPI_MakeSphere(gp_Pnt(0, 0, 0), 10.0).Shape()


def _turned(shape, at, axis, degrees):
    trsf = gp_Trsf()
    trsf.SetRotation(gp_Ax1(gp_Pnt(*at), gp_Dir(*axis)), math.radians(degrees))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def fixture_faceted_prism():
    """Planes only, every one parallel or perpendicular to one axis.

    This is the shape a PRISMATIC mesh has after conversion: the curves are
    gone and only facets are left, so a bore that was round arrives as a
    polygon. Being all-planar is not itself what blocks a recovery -- this one
    is a stack of prisms and comes back exact.
    """
    body = _box(-15, -15, 0, 30, 30, 10)
    for i in range(8):                       # an octagonal outline
        body = _cut(body, _turned(_box(12.1, -40, -5, 40, 80, 20),
                                  (0, 0, 0), (0, 0, 1), 45 * i))
    for i in range(3):                       # and a hexagonal bore
        body = _cut(body, _turned(_box(-4.0, -4.0, -5, 8.0, 8.0, 20),
                                  (0, 0, 0), (0, 0, 1), 60 * i))
    return body


def fixture_faceted_dome():
    """Planes only, pointing in every direction: a tessellated curved surface.

    The same conversion applied to a FREEFORM mesh. No direction leaves every
    facet parallel or perpendicular to it, so there is no stack of prisms to
    find, and recovery is refused however many facets are offered. This is the
    branch the mesh route turns on, and it is a property of the surface, not
    of the facet count.
    """
    body = _box(-12, -12, 0, 24, 24, 14)
    for axis in ((1, 1, 0), (-1, 1, 0), (1, -1, 0), (-1, -1, 0)):
        body = _cut(body, _turned(_box(-40, -40, 14, 80, 80, 40),
                                  (0, 0, 9), axis, 38))
    return body


FIXTURES = {
    "plate": fixture_plate,
    "moved_hole": fixture_moved_hole,
    "tilted": fixture_tilted,
    "chamfered": fixture_chamfered,
    "countersunk": fixture_countersunk,
    "nested": fixture_nested,
    "filleted": fixture_filleted,
    "sphere": fixture_sphere,
    "faceted_prism": fixture_faceted_prism,
    "faceted_dome": fixture_faceted_dome,
}


def fixture_step(name, directory):
    """Write a named fixture to `directory` and return the path."""
    return write_step(FIXTURES[name](), Path(directory) / f"{name}.step")


# --------------------------------------------------------------------------
# reporting a comparison
# --------------------------------------------------------------------------

def render(report, original, rebuilt):
    lines = [f"original : {original}", f"rebuilt  : {rebuilt}"]
    fuzz = report.get("fuzzyValueMm")
    lines.append(f"  method            {report['method']}"
                 + (f" (fuzz {fuzz:g} mm)" if fuzz else ""))
    lines.append(f"  volume            {report['volumeOriginal']}  ->  "
                 f"{report['volumeRebuilt']}   ({report['volumeDeltaPct']:+.4f}%)")
    if "missingVolume" in report:
        lines.append(f"  missing material  {report['missingVolume']}")
        lines.append(f"  extra material    {report['extraVolume']}")
        lines.append(f"  symmetric diff    {report['symmetricDifferencePct']:.6f}%")
        lines.append(f"  MATCH             {report['matchPct']:.6f}%")
    lines.append(f"  bbox              {report['bboxOriginal']} -> {report['bboxRebuilt']}"
                 f"   {'same' if report['bboxMatch'] else 'DIFFERENT'}")
    lines.append(f"  faces             {report['faceCountOriginal']} -> "
                 f"{report['faceCountRebuilt']}"
                 f"   {'same kinds' if report['faceKindsMatch'] else 'DIFFERENT kinds'}")
    lines.append(f"    original        {report['faceKindsOriginal']}")
    lines.append(f"    rebuilt         {report['faceKindsRebuilt']}")
    return "\n".join(lines)


def verdict(report, tolerance):
    """Return (ok, message). A difference the booleans refused to compute is
    not a pass: the gate says so rather than reporting a number it does not have."""
    if report["method"] == "failed":
        return False, ("FAIL: the booleans failed at every tolerance, so the difference "
                       "is unmeasured. Check that both shapes are valid solids "
                       "(scripts/inspect validate in the cad skill).")
    difference = report["symmetricDifferencePct"]
    if difference > tolerance:
        return False, (f"FAIL: {difference:.6f}% of the original volume differs, "
                       f"tolerance is {tolerance}%")
    if not report["faceKindsMatch"]:
        return True, (f"PASS on volume ({difference:.6f}%), but the surface kinds "
                      f"differ: a taper or blend was rebuilt as a different surface. "
                      f"Read the two face-kind lines before calling this a rebuild.")
    return True, f"PASS: {difference:.6f}% differs, tolerance is {tolerance}%"
