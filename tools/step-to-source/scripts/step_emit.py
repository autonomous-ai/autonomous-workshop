"""Emit editable CAD source from a prismatic STEP solid.

Strategy -- slab decomposition. When every face of the solid is either
perpendicular to one direction d or parallel to it, the solid is a stack of
prisms. Cutting between consecutive cap planes yields the exact cross-section
of each slab, so extruding those sections and fusing them reproduces the
original solid rather than approximating it.

A part that fails the prismatic test is reported, not guessed at: this script
refuses instead of emitting source that silently differs from the STEP.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_REVERSED
from OCP.TopExp import TopExp_Explorer
from OCP.TopTools import TopTools_HSequenceOfShape
from OCP.TopoDS import TopoDS
from OCP.gp import gp_Ax3, gp_Dir, gp_Pln, gp_Pnt, gp_Trsf, gp_Vec

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step_probe import (  # noqa: E402
    analyse, read_step, _explore,
)

EPS = 1e-6


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------

def align_to_z(shape, direction):
    """Rotate `shape` so `direction` becomes +Z. Returns (shape, inverse_deg)."""
    d = gp_Dir(*direction)
    z = gp_Dir(0, 0, 1)
    if d.IsParallel(z, 1e-7):
        return shape, None
    axis = gp_Vec(d).Crossed(gp_Vec(z))
    angle = gp_Vec(d).Angle(gp_Vec(z))
    trsf = gp_Trsf()
    trsf.SetRotation(
        gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(axis)).Axis(), angle)
    moved = BRepBuilderAPI_Transform(shape, trsf, True).Shape()
    return moved, (list(direction), math.degrees(angle))


def cap_heights(shape):
    """Z values of every face perpendicular to Z -- the slab boundaries."""
    heights = set()
    for face in _explore(shape, TopAbs_FACE):
        adaptor = BRepAdaptor_Surface(TopoDS.Face_s(face))
        if int(adaptor.GetType()) != 0:  # GeomAbs_Plane
            continue
        plane = adaptor.Plane()
        if abs(abs(plane.Axis().Direction().Z()) - 1.0) < 1e-7:
            heights.add(round(plane.Location().Z(), 6))
    return sorted(heights)


def section_wires(shape, z):
    """Closed wires of the solid's cross-section at height z."""
    plane = gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1))
    section = BRepAlgoAPI_Section(shape, plane, False)
    section.ComputePCurveOn1(True)
    section.Approximation(True)
    section.Build()
    if not section.IsDone():
        return []
    edges = TopTools_HSequenceOfShape()
    for edge in _explore(section.Shape(), TopAbs_EDGE):
        edges.Append(edge)
    if edges.Length() == 0:
        return []
    wires = TopTools_HSequenceOfShape()
    ShapeAnalysis_FreeBounds.ConnectEdgesToWires_s(edges, 1e-6, False, wires)
    return [TopoDS.Wire_s(wires.Value(i)) for i in range(1, wires.Length() + 1)]


def ordered_edges(wire):
    """Edges of a wire in connected traversal order.

    TopExp_Explorer yields a wire's edges in storage order, not walk order.
    Feeding that to a polygon test or a profile emitter produces a scrambled
    outline that still looks plausible, so every wire traversal here goes
    through BRepTools_WireExplorer instead.
    """
    explorer = BRepTools_WireExplorer(wire)
    edges = []
    while explorer.More():
        edges.append(explorer.Current())
        explorer.Next()
    return edges


def wire_area(wire):
    """Signed-magnitude area of a planar wire, via the shoelace on its points."""
    pts = wire_points(wire)
    if len(pts) < 3:
        return 0.0
    total = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0


def wire_points(wire, per_arc=8):
    """Polyline approximation of a wire, for area and containment only."""
    pts = []
    for edge in ordered_edges(wire):
        curve = BRepAdaptor_Curve(edge)
        first, last = curve.FirstParameter(), curve.LastParameter()
        if edge.Orientation() == TopAbs_REVERSED:
            first, last = last, first
        steps = 1 if int(curve.GetType()) == 0 else per_arc
        for i in range(steps):
            p = curve.Value(first + (last - first) * i / steps)
            pts.append((p.X(), p.Y()))
    return pts


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    n = len(polygon)
    for i in range(n):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xin = (x1 - x0) * (y - y0) / (y1 - y0 + 1e-300) + x0
            if x < xin:
                inside = not inside
    return inside


def ring_inside(inner_points, outer_polygon):
    """Is this ring enclosed by the outer one?

    A single probe point is not enough. Ring points sit on circle extremes --
    a bore's first point shares its exact y with the bore centre -- and a
    horizontal polygon edge at that same y makes one ray cast flip the wrong
    way. Vote across several points, each nudged onto its own scanline, so no
    individual degeneracy can decide the answer.
    """
    if not inner_points:
        return False
    step = max(1, len(inner_points) // 9)
    samples = inner_points[::step][:9]
    votes = 0
    for index, (x, y) in enumerate(samples):
        nudge = (index + 1) * 1e-7
        votes += point_in_polygon((x, y + nudge), outer_polygon)
    return votes * 2 > len(samples)


# --------------------------------------------------------------------------
# wire -> segment list
# --------------------------------------------------------------------------

def wire_segments(wire, digits):
    """Ordered segments of a wire as dicts the emitters can render.

    Arcs are exported as three-point arcs: the midpoint carries the sweep
    direction and the major/minor choice implicitly, so no sign convention has
    to survive the round trip.
    """
    segments = []
    for edge in ordered_edges(wire):
        curve = BRepAdaptor_Curve(edge)
        first, last = curve.FirstParameter(), curve.LastParameter()
        if edge.Orientation() == TopAbs_REVERSED:
            first, last = last, first
        start, end = curve.Value(first), curve.Value(last)
        mid = curve.Value(first + (last - first) / 2.0)
        kind = int(curve.GetType())
        seg = {
            "start": (round(start.X(), digits), round(start.Y(), digits)),
            "end": (round(end.X(), digits), round(end.Y(), digits)),
            "mid": (round(mid.X(), digits), round(mid.Y(), digits)),
        }
        if kind == 0:
            seg["kind"] = "line"
        elif kind == 1:
            circle = curve.Circle()
            seg["kind"] = "arc"
            seg["radius"] = round(circle.Radius(), digits)
            seg["center"] = (round(circle.Location().X(), digits),
                             round(circle.Location().Y(), digits))
            seg["full"] = abs((last - first) - 2 * math.pi) < 1e-7
        else:
            seg["kind"] = "unsupported"
            seg["curveType"] = kind
        segments.append(seg)
    return segments


def is_full_circle(segments):
    return len(segments) == 1 and segments[0]["kind"] == "arc" and segments[0]["full"]


# --------------------------------------------------------------------------
# emitters
# --------------------------------------------------------------------------

def emit_cadquery(slabs, name, digits, note):
    lines = ['"""Recovered from STEP by step-to-source.',
             "",
             "Dimensions are exact; feature names and parameter relationships are not",
             "recoverable from a B-rep and have been left as literals.",
             '"""',
             "import cadquery as cq",
             ""]
    if note:
        lines.append(f"# source axis {note[0]} rotated {note[1]:.4g} deg onto +Z")
        lines.append("")
    lines.append(f"def {name}():")
    lines.append("    result = None")
    for index, slab in enumerate(slabs):
        z0, z1, rings = slab
        lines.append(f"    # slab {index}: z {z0:g} -> {z1:g}")
        lines.append(f"    wp = cq.Workplane('XY').workplane(offset={z0:g})")
        outer, inners = rings
        lines.append("    slab = " + _cq_profile(outer, digits, indent=8)
                     + f".extrude({z1 - z0:g})")
        for inner in inners:
            lines.append("    cutter = " + _cq_profile(inner, digits, indent=8)
                         + f".extrude({z1 - z0:g})")
            lines.append("    slab = slab.cut(cutter)")
        lines.append("    result = slab if result is None else result.union(slab)")
    lines.append("    return result")
    lines.append("")
    lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append(f"    cq.exporters.export({name}(), '{name}.step')")
    return "\n".join(lines) + "\n"


def _cq_profile(segments, digits, indent):
    pad = "\n" + " " * indent
    if is_full_circle(segments):
        seg = segments[0]
        cx, cy = seg["center"]
        return (f"({pad}wp{pad}.center({cx:g}, {cy:g}){pad}.circle({seg['radius']:g})"
                f"{pad}.center({-cx:g}, {-cy:g}){pad})")
    parts = [f"({pad}wp"
             f"{pad}.moveTo({segments[0]['start'][0]:g}, {segments[0]['start'][1]:g})"]
    for seg in segments:
        ex, ey = seg["end"]
        if seg["kind"] == "line":
            parts.append(f"{pad}.lineTo({ex:g}, {ey:g})")
        elif seg["kind"] == "arc":
            mx, my = seg["mid"]
            parts.append(f"{pad}.threePointArc(({mx:g}, {my:g}), ({ex:g}, {ey:g}))")
        else:
            raise SystemExit(f"unsupported curve type {seg.get('curveType')} in profile")
    parts.append(f"{pad}.close(){pad})")
    return "".join(parts)


def emit_build123d(slabs, name, digits, note):
    lines = ['"""Recovered from STEP by step-to-source.',
             "",
             "Dimensions are exact; feature names and parameter relationships are not",
             "recoverable from a B-rep and have been left as literals.",
             '"""',
             "from build123d import *",
             ""]
    if note:
        lines.append(f"# source axis {note[0]} rotated {note[1]:.4g} deg onto +Z")
        lines.append("")
    lines.append(f"def {name}():")
    lines.append("    with BuildPart() as part:")
    for index, slab in enumerate(slabs):
        z0, z1, rings = slab
        outer, inners = rings
        lines.append(f"        # slab {index}: z {z0:g} -> {z1:g}")
        lines.append(f"        with BuildSketch(Plane.XY.offset({z0:g})):")
        lines.extend(_b3d_profile(outer, digits, indent=12, mode=None))
        for inner in inners:
            lines.extend(_b3d_profile(inner, digits, indent=12, mode="Mode.SUBTRACT"))
        lines.append(f"        extrude(amount={z1 - z0:g})")
    lines.append("    return part.part")
    lines.append("")
    lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append(f"    export_step({name}(), '{name}.step')")
    return "\n".join(lines) + "\n"


def _b3d_profile(segments, digits, indent, mode):
    pad = " " * indent
    suffix = f", mode={mode}" if mode else ""
    if is_full_circle(segments):
        seg = segments[0]
        cx, cy = seg["center"]
        return [f"{pad}with Locations(({cx:g}, {cy:g})):",
                f"{pad}    Circle({seg['radius']:g}{suffix})"]
    out = [f"{pad}with BuildLine():"]
    for seg in segments:
        sx, sy = seg["start"]
        ex, ey = seg["end"]
        if seg["kind"] == "line":
            out.append(f"{pad}    Line(({sx:g}, {sy:g}), ({ex:g}, {ey:g}))")
        elif seg["kind"] == "arc":
            mx, my = seg["mid"]
            out.append(f"{pad}    ThreePointArc((({sx:g}, {sy:g}), "
                       f"({mx:g}, {my:g}), ({ex:g}, {ey:g})))")
        else:
            raise SystemExit(f"unsupported curve type {seg.get('curveType')} in profile")
    out.append(f"{pad}make_face({'mode=' + mode if mode else ''})")
    return out


EMITTERS = {"cadquery": emit_cadquery, "build123d": emit_build123d}


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------

def build_slabs(shape, digits):
    heights = cap_heights(shape)
    if len(heights) < 2:
        raise SystemExit("no pair of cap planes found: nothing to extrude between")
    slabs = []
    for z0, z1 in zip(heights, heights[1:]):
        if z1 - z0 < 1e-7:
            continue
        wires = section_wires(shape, (z0 + z1) / 2.0)
        if not wires:
            continue  # a genuine void between two solid regions
        ranked = sorted(wires, key=wire_area, reverse=True)
        outer_wire = ranked[0]
        outer_poly = wire_points(outer_wire)
        outer = wire_segments(outer_wire, digits)
        inners = []
        for wire in ranked[1:]:
            if ring_inside(wire_points(wire), outer_poly):
                inners.append(wire_segments(wire, digits))
            else:
                # A disjoint island in the same slab: emit it as its own slab
                # so it is unioned rather than subtracted.
                slabs.append((z0, z1, (wire_segments(wire, digits), [])))
        slabs.append((z0, z1, (outer, inners)))
    return slabs


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="step_emit.py",
        description="Emit CadQuery or build123d source from a prismatic STEP solid.")
    parser.add_argument("step", type=Path)
    parser.add_argument("-o", "--out", type=Path, help="Write source here (default stdout).")
    parser.add_argument("--dialect", choices=sorted(EMITTERS), default="build123d")
    parser.add_argument("--name", default=None, help="Generated function name.")
    parser.add_argument("--digits", type=int, default=4)
    parser.add_argument("--force", action="store_true",
                        help="Emit even when the prismatic test fails (output will differ).")
    args = parser.parse_args(argv)

    shape = read_step(args.step)
    report = analyse(shape, args.digits, 0)
    axes = report["prismaticAxes"]
    usable = [a for a in axes if a["slabDecomposable"]]
    if not usable and not args.force:
        kinds = ", ".join(f"{k}={v}" for k, v in report["faceKinds"].items())
        if not axes:
            reason = "no single direction leaves every face parallel or perpendicular to it"
        else:
            blockers = ", ".join(axes[0]["blockingSurfaceKinds"])
            reason = (f"the axis {axes[0]['direction']} works for planes and cylinders, "
                      f"but its {blockers} faces taper or curve along it")
        raise SystemExit(
            f"{args.step.name}: slab decomposition cannot reproduce this exactly.\n"
            f"  faces: {kinds}\n"
            f"  reason: {reason}\n"
            f"Emitting anyway would silently drop those features -- run step_probe.py "
            f"for the fact sheet (it reports chamfer angles and fillet radii) and add "
            f"them to the source by hand, or pass --force and check the result with "
            f"step_verify.py.")
    direction = (usable or axes or [{"direction": [0.0, 0.0, 1.0]}])[0]["direction"]
    aligned, note = align_to_z(shape, direction)

    name = args.name or args.step.stem.replace("-", "_").replace(".", "_")
    slabs = build_slabs(aligned, args.digits)
    source = EMITTERS[args.dialect](slabs, name, args.digits, note)

    if args.out:
        args.out.write_text(source, encoding="utf-8")
        print(f"wrote {args.out} ({len(slabs)} slabs, {args.dialect})", file=sys.stderr)
    else:
        sys.stdout.write(source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
