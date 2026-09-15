"""Extract exact B-rep facts from a STEP file as JSON.

This is the measuring stage: it reports only what the kernel can prove about
the shape. It never guesses a feature decomposition -- that judgement belongs
to the caller reading this report.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_REVERSED, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Shape

SURFACE_KIND = {
    0: "plane", 1: "cylinder", 2: "cone", 3: "sphere", 4: "torus",
    5: "bezier", 6: "bspline", 7: "revolution", 8: "extrusion", 9: "offset",
}
CURVE_KIND = {
    0: "line", 1: "circle", 2: "ellipse", 3: "hyperbola", 4: "parabola",
    5: "bezier", 6: "bspline", 7: "offset", 8: "other",
}
ANALYTIC = {"plane", "cylinder", "cone", "sphere", "torus"}
TOL = 1e-6


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
    return [_r(c, digits) for c in v]


def read_step(path: Path) -> TopoDS_Shape:
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise SystemExit(f"cannot read STEP: {path}")
    reader.TransferRoots()
    return reader.OneShape()


def _explore(shape, kind):
    exp = TopExp_Explorer(shape, kind)
    while exp.More():
        yield exp.Current()
        exp.Next()


def bbox(shape, digits):
    box = Bnd_Box()
    BRepBndLib.Add_s(shape, box)
    xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    return {
        "min": [_r(xmin, digits), _r(ymin, digits), _r(zmin, digits)],
        "max": [_r(xmax, digits), _r(ymax, digits), _r(zmax, digits)],
        "size": [_r(xmax - xmin, digits), _r(ymax - ymin, digits), _r(zmax - zmin, digits)],
    }


def mass_props(shape, digits):
    vol, area = GProp_GProps(), GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, vol)
    BRepGProp.SurfaceProperties_s(shape, area)
    return {
        "volume": _r(vol.Mass(), digits),
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
    elif kind == "cylinder":
        cyl = adaptor.Cylinder()
        params["origin"] = _pt(cyl.Location(), digits)
        params["axis"] = _canonical_dir(cyl.Axis().Direction(), digits)
        params["radius"] = _r(cyl.Radius(), digits)
    elif kind == "cone":
        cone = adaptor.Cone()
        params["origin"] = _pt(cone.Location(), digits)
        params["axis"] = _canonical_dir(cone.Axis().Direction(), digits)
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
        params["majorRadius"] = _r(tor.MajorRadius(), digits)
        params["minorRadius"] = _r(tor.MinorRadius(), digits)
    params["uPeriodic"] = bool(adaptor.IsUPeriodic())
    params["uSpanDeg"] = _r(math.degrees(adaptor.LastUParameter() - adaptor.FirstUParameter()), 1) \
        if kind in {"cylinder", "cone", "torus", "sphere"} else None
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
    for edge in _explore(shape, TopAbs_EDGE):
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
        closed = span > 359.0
        inward = all(m["reversed"] for m in members)
        bands.append({
            "axis": list(axis),
            "axisPoint": list(perp),
            "radius": radius,
            "diameter": _r(radius * 2, digits),
            "faceIndices": sorted(m["index"] for m in members),
            "spanDeg": _r(span, 1),
            "closed": closed,
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
    """Conical faces between two surfaces are chamfers or countersinks."""
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
            "reading": "45 deg chamfer" if abs(angle - 45) < 0.5 else
                       (f"countersink-like taper, {angle:.1f} deg half-angle"
                        if 35 <= angle < 45 else f"taper, {angle:.1f} deg half-angle"),
        })
    return out


def detect_fillets(faces, digits):
    """Torus faces are fillets outright; cylinders can be edge fillets too."""
    out = []
    for face in faces:
        if face["kind"] == "torus":
            out.append({"faceIndex": face["index"], "radius": face["minorRadius"],
                        "evidence": "torus minor radius", "confidence": "certain"})
    radii = defaultdict(list)
    for entry in out:
        radii[entry["radius"]].append(entry["faceIndex"])
    return {"candidates": out,
            "radiiSeen": {str(k): v for k, v in sorted(radii.items())}}


def prismatic_axis(faces, digits):
    """Find a direction the shape could be extruded along.

    The part is prismatic along d when every planar face is either
    perpendicular to d (a cap) or parallel to d (a side wall), and every
    cylinder/cone axis is parallel to d.
    """
    candidates = []
    for face in faces:
        if face["kind"] == "plane":
            candidates.append(tuple(face["normal"]))
        elif face["kind"] in {"cylinder", "cone"}:
            candidates.append(tuple(face["axis"]))
    results = []
    for direction in sorted(set(candidates)):
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
            elif face["kind"] in {"cylinder", "cone"}:
                dot = abs(sum(face["axis"][i] * direction[i] for i in range(3)))
                if dot < 1 - 1e-4:
                    ok = False
                    break
            else:
                ok = False
                break
        if ok:
            # A cone shares the axis but tapers along it, so a constant
            # cross-section cannot reproduce it. Axis-aligned is necessary for
            # slab decomposition; it is not sufficient.
            blockers = sorted({f["kind"] for f in faces
                               if f["kind"] not in {"plane", "cylinder"}})
            results.append({"direction": list(direction), "capFaces": caps,
                            "wallFaces": walls,
                            "slabDecomposable": not blockers,
                            "blockingSurfaceKinds": blockers})
    return results


def analyse(shape, digits, max_faces):
    faces = [face_report(f, i, digits) for i, f in enumerate(_explore(shape, TopAbs_FACE))]
    kinds = defaultdict(int)
    for face in faces:
        kinds[face["kind"]] += 1
    analytic = sum(v for k, v in kinds.items() if k in ANALYTIC)
    total = len(faces) or 1
    solids = list(_explore(shape, TopAbs_SOLID))

    bands, stepped, arcs = detect_bands(faces, digits)

    report = {
        "faceCount": len(faces),
        "solidCount": len(solids),
        "faceKinds": dict(sorted(kinds.items(), key=lambda kv: -kv[1])),
        "analyticFraction": round(analytic / total, 4),
        "recoverable": analytic == total,
        "bbox": bbox(shape, digits),
        "mass": mass_props(shape, digits),
        "edgeKinds": edge_kinds(shape),
        "cylindricalBands": bands,
        "steppedBores": stepped,
        "arcSlots": arcs,
        "chamfers": detect_chamfers(faces, digits),
        "fillets": detect_fillets(faces, digits),
        "prismaticAxes": prismatic_axis(faces, digits),
    }
    report["faces"] = faces if len(faces) <= max_faces else faces[:max_faces]
    report["facesTruncated"] = len(faces) > max_faces
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="step_probe.py",
        description="Dump exact B-rep facts from a STEP file as JSON.")
    parser.add_argument("step", type=Path, help="STEP/STP file to measure.")
    parser.add_argument("--digits", type=int, default=4,
                        help="Rounding for reported coordinates (default 4).")
    parser.add_argument("--max-faces", type=int, default=400,
                        help="Cap on individually listed faces (default 400).")
    parser.add_argument("--summary", action="store_true",
                        help="Print a short human summary instead of JSON.")
    args = parser.parse_args(argv)

    report = analyse(read_step(args.step), args.digits, args.max_faces)
    report["source"] = str(args.step)

    if not args.summary:
        print(json.dumps(report, indent=2))
        return 0

    print(f"{args.step.name}: {report['faceCount']} faces, "
          f"{report['solidCount']} solid(s)")
    print("  kinds:      " + ", ".join(f"{k}={v}" for k, v in report["faceKinds"].items()))
    print(f"  analytic:   {report['analyticFraction'] * 100:.1f}%"
          f"{'  (exactly rebuildable)' if report['recoverable'] else '  (has freeform faces)'}")
    print(f"  bbox size:  {report['bbox']['size']}")
    print(f"  volume:     {report['mass']['volume']}")
    holes = [b for b in report["cylindricalBands"] if b["role"] == "hole"]
    other = [b for b in report["cylindricalBands"] if b["role"] != "hole"]
    print(f"  holes:      {len(holes)} through/blind bores, "
          f"{len(other)} other cylindrical walls")
    for bore in holes[:10]:
        print(f"                dia {bore['diameter']:.3f} axis {bore['axis']} "
              f"through {bore['axisPoint']}")
    halves = [b for b in report["cylindricalBands"] if b["role"].startswith("half")]
    for band in halves[:6]:
        print(f"                dia {band['diameter']:.3f} half-cylinder at {band['axisPoint']} "
              f"(mirror seam)")
    for arc in report["arcSlots"][:6]:
        print(f"  arc slot:   radii {arc['radii']} at {arc['axisPoint']}")
    for step in report["steppedBores"]:
        print(f"                stepped bore {step['diameters']} at {step['axisPoint']}")
    for ch in report["chamfers"][:6]:
        print(f"  chamfer:    face {ch['faceIndex']}: {ch['reading']}")
    fillets = report["fillets"]["radiiSeen"]
    print(f"  fillets:    {fillets if fillets else 'none (no torus faces)'}")
    axes = report["prismaticAxes"]
    if axes:
        print("  prismatic:  yes, along " + " or ".join(str(a["direction"]) for a in axes))
        blockers = axes[0]["blockingSurfaceKinds"]
        if blockers:
            print(f"              but {', '.join(blockers)} faces taper or curve along "
                  f"that axis -> slab decomposition would drop them")
        else:
            print("              slab decomposition can reproduce this exactly")
    else:
        print("  prismatic:  no single extrusion direction")
    return 0


if __name__ == "__main__":
    sys.exit(main())
