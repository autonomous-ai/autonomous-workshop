"""Turn a triangle mesh into a STEP solid, and measure what that cost.

A mesh and a B-rep are not two encodings of the same thing. An STL holds
triangles and nothing else: no bore radius, no plane, no axis, no units. Every
curved surface in it has already been replaced by flat facets, and no converter
puts them back by reading the file harder. So the honest description of what
happens here is a change of container -- the triangles become faces of a valid
solid -- plus, on one backend, a bounded attempt to recognise a few complete
primitives and restore them.

What that buys is real: a solid can be measured, cut, mounted against and
checked for interference, and a mesh cannot. What it does not buy is source,
or a parametric model, or exact curved geometry. The verification here reports
the difference between the mesh it read and the solid it wrote, so the claim
that the conversion was faithful is measured rather than assumed.

Three backends, tried in this order:

    2step      github.com/yaneony/2STEP-Converter -- OpenCASCADE behind its own
               environment; repairs the mesh, sews, merges coplanar faces and
               restores complete spheres/cylinders/cones and straight holes as
               analytic surfaces. The best output, and a ~7.6 GB install.
    stltostp   github.com/slugdev/stltostp -- a small C++ tool, no dependencies,
               triangle-to-triangle with coplanar merging. No analytic surfaces.
    sew        this file, on the OCP already required by the CAD skill. Same
               idea as stltostp, always available, and what the self-checks use
               so they need no network.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from OCP.BRep import BRep_Builder
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeSolid,
    BRepBuilderAPI_Sewing, BRepBuilderAPI_Transform,
)
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.IFSelect import IFSelect_RetDone
from OCP.Interface import Interface_Static
from OCP.Message import Message, Message_Gravity
from OCP.Poly import Poly_Triangulation
from OCP.RWStl import RWStl
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Reader, STEPControl_Writer
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.StlAPI import StlAPI_Writer
from OCP.TopAbs import TopAbs_FACE, TopAbs_SHELL, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Compound
from OCP.gp import gp_Trsf

# The STEP writer reports every transfer on stdout through OpenCASCADE's own
# messenger, which would land in the middle of this toolchain's output.
for _printer in Message.DefaultMessenger_s().Printers():
    _printer.SetTraceLevel(Message_Gravity.Message_Fail)

# Tool checkouts live outside the worktree on purpose: this repository's entry
# resolver scans the whole tree, and a cloned converter full of .py files is
# exactly the kind of stale envelope that breaks unrelated validation.
CACHE = Path(os.environ.get("CAD_TOOL_CACHE",
                            Path.home() / ".cache" / "autonomous-cad" / "step-tools"))

UNIT_SCALE = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "ft": 304.8}


# --------------------------------------------------------------------------
# reading and measuring a mesh
# --------------------------------------------------------------------------

# Mesh containers this reader does not open. Naming them is not a limitation
# being apologised for: the reader is STL-only, and a 3MF handed to it failed
# with OCP's "premature end of file", which reads as a corrupt STL rather than
# as the wrong format. An STL with an unusual or absent extension still passes
# through to the reader, so this refuses formats rather than policing names.
UNREADABLE_MESH_SUFFIXES = {".3mf", ".obj", ".amf", ".ply", ".glb", ".gltf", ".fbx", ".off"}


def read_stl(path):
    """Read an STL, binary or ASCII, as a triangulation."""
    suffix = Path(path).suffix.lower()
    if suffix in UNREADABLE_MESH_SUFFIXES:
        raise SystemExit(
            f"{suffix} is not read here; this converts STL only. "
            f"Export {Path(path).name} to STL and convert that: {path}"
        )
    triangulation = RWStl.ReadFile_s(str(path))
    if triangulation is None or triangulation.NbTriangles() == 0:
        raise SystemExit(f"cannot read STL, or it holds no triangles: {path}")
    return triangulation


def crossing_pairs(triangulation, max_entries=8_000_000):
    """Triangle pairs that pass through each other. ``None`` when not measured.

    This is the defect the edge counts cannot see. A mesh can be closed and
    manifold and still have surfaces that cut through one another -- a sculpt,
    a boolean that was never cleaned, scales laid into a body -- and every
    backend sews it into a solid that looks fine: the volume is right, the box
    is right, ``BRepCheck_Analyzer`` calls it valid. What it is not is usable,
    because the kernel's BOP self-intersection check fails it, which takes a
    boolean, a fillet, an offset and this repository's ``validate`` gate down
    with it. Finding that here costs seconds; finding it after a conversion and
    a pipeline round costs an hour.

    Two tests over candidates from a uniform grid on the triangle boxes -- a
    single search radius is no use on a mesh whose facets span two orders of
    magnitude, which is most of them. Where the two planes meet at an angle,
    Moller's interval overlap. Where they are the same plane, a 2D overlap of
    positive area, which is a separate mechanism and the one that matters on a
    mesh built by sculpting or by an uncleaned boolean: counting only the
    angled kind found 3 crossings in a body whose exact conversion had 22
    self-intersecting solids.

    Pairs sharing a vertex are skipped, since neighbours touch by construction,
    and so is contact of zero area -- triangles tiling a flat region meet along
    edges, and that is not a defect. The count remains a floor rather than a
    total: it counts pairs, and one crossing region spans many of them.

    ``None`` is deliberately distinct from 0. "Not established" must never read
    as "passed".
    """
    try:
        import numpy as np
    except ImportError:                      # numpy rides in with build123d
        return None

    count = triangulation.NbTriangles()
    if count < 2:
        return 0
    verts = np.empty((count, 3, 3))
    for index in range(1, count + 1):
        nodes = triangulation.Triangle(index).Get()
        for slot, node in enumerate(nodes):
            point = triangulation.Node(node)
            verts[index - 1, slot] = (point.X(), point.Y(), point.Z())

    # Identity is the coordinate, not the node index. A tessellation gives each
    # face its own nodes, so two triangles meeting across a face boundary share
    # a vertex geometrically and no index at all -- and their common edge then
    # reads as a crossing, which made a clean block report a thousand of them.
    _, ids = np.unique(np.round(verts.reshape(count * 3, 3), 4),
                       axis=0, return_inverse=True)
    ids = ids.reshape(count, 3)

    lo, hi = verts.min(axis=1), verts.max(axis=1)
    extent = (hi - lo).max(axis=1)
    cell = max(float(np.median(extent)) * 2.0, 1e-9)
    origin = lo.min(axis=0)
    for _ in range(8):                       # a coarser grid rather than an OOM
        low = np.floor((lo - origin) / cell).astype(np.int64)
        high = np.floor((hi - origin) / cell).astype(np.int64)
        if int(np.prod(high - low + 1, axis=1).sum()) <= max_entries:
            break
        cell *= 2.0
    else:
        return None

    dims = high.max(axis=0) + 1
    keys, owners = [], []
    for index in range(count):
        a, b = low[index], high[index]
        gx, gy, gz = np.meshgrid(np.arange(a[0], b[0] + 1),
                                 np.arange(a[1], b[1] + 1),
                                 np.arange(a[2], b[2] + 1), indexing="ij")
        flat = (gx.ravel() * dims[1] + gy.ravel()) * dims[2] + gz.ravel()
        keys.append(flat)
        owners.append(np.full(flat.size, index, dtype=np.int64))
    keys = np.concatenate(keys)
    owners = np.concatenate(owners)
    order = np.argsort(keys, kind="stable")
    keys, owners = keys[order], owners[order]
    starts = np.flatnonzero(np.r_[True, keys[1:] != keys[:-1]])
    ends = np.r_[starts[1:], keys.size]

    blocks = []
    for start, end in zip(starts, ends):
        width = end - start
        if width < 2:
            continue
        bucket = owners[start:end]
        left, right = np.triu_indices(width, 1)
        blocks.append(np.stack([bucket[left], bucket[right]], axis=1))
    if not blocks:
        return 0
    pairs = np.unique(np.sort(np.concatenate(blocks), axis=1), axis=0)
    left, right = pairs[:, 0], pairs[:, 1]
    shares = (ids[left][:, :, None] == ids[right][:, None, :]).any(axis=(1, 2))
    left, right = left[~shares], right[~shares]

    def _sides(near, far):
        """Signed distances of ``far``'s vertices to ``near``'s plane."""
        normal = np.cross(near[:, 1] - near[:, 0], near[:, 2] - near[:, 0])
        offset = -np.einsum("ij,ij->i", normal, near[:, 0])
        return normal, np.einsum("ij,kij->ki", normal,
                                 far.transpose(1, 0, 2)).T + offset[:, None]

    def _interval(axis_coord, distance):
        """Where each triangle meets the two planes' intersection line."""
        low_ = np.full(len(axis_coord), np.nan)
        high_ = np.full(len(axis_coord), np.nan)
        for u, v in ((0, 1), (1, 2), (2, 0)):
            crosses = (distance[:, u] * distance[:, v]) < 0
            span = np.where(crosses, distance[:, u] - distance[:, v], 1.0)
            cut = np.where(crosses,
                           axis_coord[:, u] + (axis_coord[:, v] - axis_coord[:, u])
                           * distance[:, u] / span, np.nan)
            low_, high_ = np.fmin(low_, cut), np.fmax(high_, cut)
            on_plane = np.abs(distance[:, u]) <= 1e-12
            touch = np.where(on_plane, axis_coord[:, u], np.nan)
            low_, high_ = np.fmin(low_, touch), np.fmax(high_, touch)
        return low_, high_

    def _overlaps_2d(flat_a, flat_b, eps):
        """Do two coplanar triangles share area? Separating axis, 6 axes.

        The tolerance decides the whole test: two triangles tiling a flat
        region meet exactly along an edge, so the axis normal to it separates
        them by zero. Counting that as an overlap reports every flat surface in
        the mesh as a defect.
        """
        apart = np.zeros(len(flat_a), dtype=bool)
        for tri in (flat_a, flat_b):
            for u, v in ((0, 1), (1, 2), (2, 0)):
                edge = tri[:, v] - tri[:, u]
                axis = np.stack([-edge[:, 1], edge[:, 0]], axis=1)
                length = np.linalg.norm(axis, axis=1)
                safe = np.maximum(length, 1e-300)
                axis = axis / safe[:, None]
                pa = np.einsum("ijk,ik->ij", flat_a, axis)
                pb = np.einsum("ijk,ik->ij", flat_b, axis)
                apart |= (pa.max(1) <= pb.min(1) + eps) | (pb.max(1) <= pa.min(1) + eps)
        return ~apart

    diag = float(np.linalg.norm(hi.max(axis=0) - lo.min(axis=0)))
    touch_eps = max(diag * 1e-9, 1e-12)
    found = 0
    chunk = 1_000_000
    for start in range(0, len(left), chunk):
        first = verts[left[start:start + chunk]]
        second = verts[right[start:start + chunk]]
        normal_a, dist_b = _sides(first, second)
        normal_b, dist_a = _sides(second, first)
        eps = 1e-9
        live = ~((dist_b > eps).all(1) | (dist_b < -eps).all(1)
                 | (dist_a > eps).all(1) | (dist_a < -eps).all(1))
        if not live.any():
            continue
        direction = np.cross(normal_a, normal_b)
        scale = np.linalg.norm(normal_a, axis=1) * np.linalg.norm(normal_b, axis=1)
        angled = np.linalg.norm(direction, axis=1) > 1e-9 * np.maximum(scale, 1e-30)

        # planes meeting at an angle: the intersection line, and whether both
        # triangles cut overlapping pieces out of it
        pick = live & angled
        if pick.any():
            cut_a, cut_b = first[pick], second[pick]
            da, db = dist_a[pick], dist_b[pick]
            axis = np.abs(direction[pick]).argmax(axis=1)
            take = axis[:, None, None].repeat(3, 1)
            low_a, high_a = _interval(np.take_along_axis(cut_a, take, 2)[:, :, 0], da)
            low_b, high_b = _interval(np.take_along_axis(cut_b, take, 2)[:, :, 0], db)
            usable = np.isfinite(low_a) & np.isfinite(low_b)
            found += int((usable & (np.minimum(high_a, high_b)
                                    - np.maximum(low_a, low_b) > touch_eps)).sum())

        # the same plane twice: drop the dominant axis and overlap in 2D
        pick = live & ~angled
        if pick.any():
            unit = np.linalg.norm(normal_a[pick], axis=1)
            coincident = (np.abs(dist_b[pick])
                          <= touch_eps * np.maximum(unit, 1e-300)[:, None]).all(1)
            if coincident.any():
                flat_a = first[pick][coincident]
                flat_b = second[pick][coincident]
                drop = np.abs(normal_a[pick][coincident]).argmax(axis=1)
                keep = np.stack([(drop + 1) % 3, (drop + 2) % 3], axis=1)
                take = keep[:, None, :].repeat(3, 1)
                found += int(_overlaps_2d(np.take_along_axis(flat_a, take, 2),
                                          np.take_along_axis(flat_b, take, 2),
                                          touch_eps).sum())
    return found


def mesh_report(triangulation, digits=4, crossings=True):
    """Everything about the mesh that decides whether it can become a solid.

    The decisive number is not the triangle count, it is the boundary edge
    count. A closed mesh has every edge shared by exactly two triangles; one
    unshared edge is a hole, and a hole means the sewn result is a shell with
    no inside, which no boolean and no volume measurement can use. Edges shared
    by three or more triangles are the other way the same claim fails, and both
    are cheap to count here and expensive to discover after a conversion.

    ``crossingPairs`` answers the question the edge counts cannot: see
    ``crossing_pairs``. Pass ``crossings=False`` to skip it.
    """
    nodes = triangulation.NbNodes()
    count = triangulation.NbTriangles()
    edges = defaultdict(int)
    volume = 0.0
    area = 0.0
    degenerate = 0
    for index in range(1, count + 1):
        i1, i2, i3 = triangulation.Triangle(index).Get()
        p1, p2, p3 = (triangulation.Node(i1), triangulation.Node(i2),
                      triangulation.Node(i3))
        # Signed tetrahedron against the origin: summed over a closed mesh this
        # is the enclosed volume, and it needs no solid to compute.
        volume += (p1.X() * (p2.Y() * p3.Z() - p3.Y() * p2.Z())
                   - p1.Y() * (p2.X() * p3.Z() - p3.X() * p2.Z())
                   + p1.Z() * (p2.X() * p3.Y() - p3.X() * p2.Y())) / 6.0
        ux, uy, uz = p2.X() - p1.X(), p2.Y() - p1.Y(), p2.Z() - p1.Z()
        vx, vy, vz = p3.X() - p1.X(), p3.Y() - p1.Y(), p3.Z() - p1.Z()
        cross = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
        facet = math.sqrt(sum(c * c for c in cross)) / 2.0
        area += facet
        if facet < 1e-12:
            degenerate += 1
        for a, b in ((i1, i2), (i2, i3), (i3, i1)):
            edges[(min(a, b), max(a, b))] += 1

    boundary = sum(1 for n in edges.values() if n == 1)
    non_manifold = sum(1 for n in edges.values() if n > 2)
    xs = [triangulation.Node(i).X() for i in range(1, nodes + 1)]
    ys = [triangulation.Node(i).Y() for i in range(1, nodes + 1)]
    zs = [triangulation.Node(i).Z() for i in range(1, nodes + 1)]
    return {
        "triangles": count,
        "nodes": nodes,
        "crossingPairs": crossing_pairs(triangulation) if crossings else None,
        "volume": round(abs(volume), digits),
        "area": round(area, digits),
        "bbox": {"min": [round(min(xs), digits), round(min(ys), digits), round(min(zs), digits)],
                 "max": [round(max(xs), digits), round(max(ys), digits), round(max(zs), digits)],
                 "size": [round(max(xs) - min(xs), digits), round(max(ys) - min(ys), digits),
                          round(max(zs) - min(zs), digits)]},
        "boundaryEdges": boundary,
        "nonManifoldEdges": non_manifold,
        "degenerateTriangles": degenerate,
        "watertight": boundary == 0 and non_manifold == 0,
    }


# --------------------------------------------------------------------------
# STEP in and out
# --------------------------------------------------------------------------

def read_step(path):
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise SystemExit(f"cannot read STEP: {path}")
    reader.TransferRoots()
    shape = reader.OneShape()
    if shape.IsNull():
        raise SystemExit(f"STEP read as empty: {path}")
    return shape


# A STEP file carries its geometry inside a product structure, and a writer
# that omits it produces a file that is textually complete and, to
# OpenCASCADE, empty: the reader finds no root to transfer and hands back
# nothing. stltostp writes such a file. The wrapper below is the smallest one
# AP214 accepts, and adding it is a repair of the container, never of the
# geometry -- not one coordinate is touched.
PRODUCT_WRAPPER = """#{b} = APPLICATION_CONTEXT('automotive design');
#{b1} = APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#{b});
#{b2} = PRODUCT_CONTEXT('',#{b},'mechanical');
#{b3} = PRODUCT('{name}','{name}','',(#{b2}));
#{b4} = PRODUCT_DEFINITION_FORMATION('','',#{b3});
#{b5} = PRODUCT_DEFINITION_CONTEXT('part definition',#{b},'design');
#{b6} = PRODUCT_DEFINITION('','',#{b4},#{b5});
#{b7} = PRODUCT_DEFINITION_SHAPE('','',#{b6});
#{b8} = SHAPE_DEFINITION_REPRESENTATION(#{b7},#{rep});
"""
REPRESENTATION = re.compile(
    r"#(\d+)\s*=\s*(?:ADVANCED_BREP_SHAPE_REPRESENTATION|"
    r"MANIFOLD_SURFACE_SHAPE_REPRESENTATION|GEOMETRICALLY_BOUNDED_SURFACE_"
    r"SHAPE_REPRESENTATION|SHAPE_REPRESENTATION)\s*\(")


def add_product_structure(path, destination, name="part"):
    """Wrap a bare shape representation in the product entities a reader needs."""
    text = Path(path).read_text(errors="replace")
    match = REPRESENTATION.search(text)
    if match is None or "SHAPE_DEFINITION_REPRESENTATION" in text:
        return None
    ids = [int(n) for n in re.findall(r"^#(\d+)\s*=", text, re.M)]
    base = (max(ids) if ids else 0) + 1
    wrapper = PRODUCT_WRAPPER.format(
        b=base, b1=base + 1, b2=base + 2, b3=base + 3, b4=base + 4, b5=base + 5,
        b6=base + 6, b7=base + 7, b8=base + 8, rep=match.group(1), name=name)
    index = text.rfind("ENDSEC;")
    if index < 0:
        return None
    Path(destination).write_text(text[:index] + wrapper + text[index:])
    return Path(destination)


def read_step_any(path):
    """Read a STEP, repairing the container when a writer left it incomplete.

    Returns the shape and the list of repairs applied, which the caller reports:
    a file that had to be repaired to be read is a fact about that backend, not
    a detail to swallow.
    """
    repairs = []
    try:
        return read_step(path), repairs
    except SystemExit:
        pass
    patched = add_product_structure(path, Path(str(path) + ".wrapped"),
                                    Path(path).stem[:60])
    if patched is None:
        raise SystemExit(f"STEP read as empty and has no representation to wrap: {path}")
    try:
        shape = read_step(patched)
    finally:
        patched.unlink(missing_ok=True)
    repairs.append("added the missing product structure the writer omitted")
    return shape, repairs


def promote_to_solid(shape, tolerance=1e-6):
    """Sew loose faces or an open shell into a solid, when there is one to find.

    Some writers export a surface model: the faces are right, the topology says
    nothing encloses anything, and every downstream check that needs an inside
    fails. Sewing answers whether the faces actually close. If they do not, this
    changes nothing and the verification says so.
    """
    if any(True for _ in explore(shape, TopAbs_SOLID)):
        return shape, []
    faces = [TopoDS.Face_s(f) for f in explore(shape, TopAbs_FACE)]
    if not faces:
        return shape, []
    sewing = BRepBuilderAPI_Sewing(tolerance)
    for face in faces:
        sewing.Add(face)
    sewing.Perform()
    sewn = sewing.SewedShape()
    shells = [TopoDS.Shell_s(s) for s in explore(sewn, TopAbs_SHELL)]
    if not shells:
        return shape, []
    solids = []
    for shell in shells:
        solid = ShapeFix_Solid().SolidFromShell(shell)
        if solid is not None:
            solids.append(solid)
    if not solids:
        return shape, []
    if len(solids) == 1:
        result = solids[0]
    else:
        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        for solid in solids:
            builder.Add(compound, solid)
        result = compound
    return result, [f"sewed {len(faces)} loose faces into {len(solids)} solid(s)"]


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


def write_step(shape, path, schema="AP214"):
    Interface_Static.SetCVal_s("write.step.schema", schema)
    # A planar face's pcurves are exact projections every reader recomputes;
    # on a faceted solid they are over half the file. Curved faces keep them.
    Interface_Static.SetIVal_s("write.surfacecurve.mode", 0 if all_planar(shape) else 1)
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    if writer.Write(str(path)) != IFSelect_RetDone:
        raise SystemExit(f"cannot write STEP: {path}")
    return Path(path)


def explore(shape, kind):
    exp = TopExp_Explorer(shape, kind)
    while exp.More():
        yield exp.Current()
        exp.Next()


def volume_of(shape):
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return abs(props.Mass())


def bbox_of(shape, digits=4):
    box = Bnd_Box()
    BRepBndLib.Add_s(shape, box)
    xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    return [round(xmax - xmin, digits), round(ymax - ymin, digits), round(zmax - zmin, digits)]


def scale_shape(shape, factor):
    if factor == 1.0:
        return shape
    trsf = gp_Trsf()
    trsf.SetScaleFactor(factor)
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


# --------------------------------------------------------------------------
# the built-in backend: sew the triangles
# --------------------------------------------------------------------------

from OCP.BRepAdaptor import BRepAdaptor_Surface  # noqa: E402
from OCP.ShapeFix import ShapeFix_Solid  # noqa: E402

SURFACE_KIND = {0: "plane", 1: "cylinder", 2: "cone", 3: "sphere", 4: "torus",
                5: "bezier", 6: "bspline", 7: "revolution", 8: "extrusion", 9: "offset"}


def face_kinds(shape):
    kinds = defaultdict(int)
    for face in explore(shape, TopAbs_FACE):
        kinds[SURFACE_KIND.get(int(BRepAdaptor_Surface(TopoDS.Face_s(face)).GetType()),
                               "other")] += 1
    return dict(sorted(kinds.items(), key=lambda kv: -kv[1]))


def sew_solid(triangulation, tolerance=1e-6, merge=True):
    """Triangles -> sewn shell -> solid, with coplanar faces merged.

    Merging is not cosmetic. A tessellated cube arrives as twelve triangles and
    leaves as six faces, and every downstream selector, seat and interference
    check works on faces -- twelve of them where there is one surface is a model
    that is technically valid and practically unusable.
    """
    sewing = BRepBuilderAPI_Sewing(tolerance)
    added = skipped = 0
    for index in range(1, triangulation.NbTriangles() + 1):
        i1, i2, i3 = triangulation.Triangle(index).Get()
        try:
            wire = BRepBuilderAPI_MakePolygon(
                triangulation.Node(i1), triangulation.Node(i2),
                triangulation.Node(i3), True).Wire()
            sewing.Add(BRepBuilderAPI_MakeFace(wire).Face())
            added += 1
        except Exception:        # a degenerate facet has no face to make
            skipped += 1
    sewing.Perform()
    sewn = sewing.SewedShape()

    shells = [TopoDS.Shell_s(s) for s in explore(sewn, TopAbs_SHELL)]
    if not shells:
        raise SystemExit("sewing produced no shell: the triangles do not join at "
                         "this tolerance. Run mesh_probe on the file first.")
    solids = []
    for shell in shells:
        fixer = ShapeFix_Solid()
        solid = fixer.SolidFromShell(shell)
        solids.append(solid if solid is not None else BRepBuilderAPI_MakeSolid(shell).Solid())

    if len(solids) == 1:
        shape = solids[0]
    else:
        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        for solid in solids:
            builder.Add(compound, solid)
        shape = compound

    if merge:
        unify = ShapeUpgrade_UnifySameDomain(shape, True, True, False)
        unify.Build()
        shape = unify.Shape()
    return shape, {"facesAdded": added, "facetsSkipped": skipped, "shells": len(shells)}


# --------------------------------------------------------------------------
# verifying a conversion, whichever backend made it
# --------------------------------------------------------------------------

def scale_mesh_report(mesh, factor):
    """The same mesh read in different units.

    Scaling the solid without scaling what it is checked against would fail
    every conversion that declared units, which is the shape of bug that ends
    with the check being switched off rather than fixed.
    """
    if factor == 1.0:
        return mesh
    scaled = dict(mesh)
    scaled["volume"] = round(mesh["volume"] * factor ** 3, 4)
    scaled["area"] = round(mesh["area"] * factor ** 2, 4)
    scaled["bbox"] = {key: [round(v * factor, 4) for v in value]
                      for key, value in mesh["bbox"].items()}
    return scaled


def self_intersecting_solids(solids, budget=120.0):
    """Count the solids the kernel's BOP check calls self-intersecting.

    This is the check the rest of this file was missing, and the gap it closes
    is a whole pipeline round wide. ``BRepCheck_Analyzer.IsValid()`` -- the
    thing this module prints as ``valid`` -- does not look for faces that pass
    through one another at all. A conversion can therefore report a solid
    count, a matching volume, an exact bounding box and ``valid``, and then be
    rejected hours later by this repository's ``validate`` gate, which checks
    ``BOPAlgo_SelfIntersect`` through ``BRepAlgoAPI_Check``. Two different
    notions of the word, and the one printed here was the weaker.

    So this asks the same question the gate asks, with the same keying:
    ``IsValid()`` on the BOP checker is False for several unrelated faults
    (bad type, too-small edge, invalid curve-on-surface), and reporting those
    as self-intersections would be its own kind of wrong.

    Per solid rather than on the whole shape, because "67 of 100" and "the
    shape is bad" are different findings: the first says which bodies to avoid
    booleans against and leaves the rest usable, and it is also what lets a
    budget stop early with a partial answer instead of no answer. A count of
    ``None`` means the check did not run, which is never the same as zero.
    """
    try:
        from OCP.BOPAlgo import BOPAlgo_CheckStatus
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
    except ImportError:
        return None

    started = time.monotonic()
    found = checked = failed = 0
    for solid in solids:
        if budget and time.monotonic() - started > budget:
            break
        try:
            checker = BRepAlgoAPI_Check(solid, True, True)
            checker.Perform()
            if not checker.IsValid() and any(
                    result.GetCheckStatus() == BOPAlgo_CheckStatus.BOPAlgo_SelfIntersect
                    for result in checker.Result()):
                found += 1
        except Exception:      # a body the checker cannot handle is not a clean body
            failed += 1
            continue
        checked += 1
    return {"selfIntersecting": found, "checked": checked, "unchecked": failed,
            "total": len(solids), "complete": checked + failed == len(solids),
            "seconds": round(time.monotonic() - started, 1)}


def verify_conversion(mesh, step_path, volume_tolerance=1.0, digits=4,
                      self_intersection_budget=120.0):
    """Compare the STEP that came back against the mesh that went in.

    Volume is the right measure here, unlike in a source recovery: the two
    shapes are meant to bound the same material, and a conversion that loses or
    gains any of it has gone wrong in a way that shows up nowhere else. A
    faceted conversion should match the mesh exactly; a backend that restores a
    cylinder where facets were will differ by the facet error, which is why the
    tolerance is a percentage rather than zero and why the number is always
    printed instead of only its verdict.

    The bounding box gets the same percentage for the same reason. A backend
    that does more than re-container the triangles does not hand back the same
    vertices: repairing a mesh moves them, and a restored cylinder stands
    outside the polygon that approximated it by the sagitta, a facet being a
    chord. The volume tolerance exists for exactly that, and the box is a
    sample of the same surface taken at its six extremes, so it moves for the
    same reasons and needs the same allowance. Held to a rounding epsilon it
    instead rejected the only backend that repairs or restores anything, while
    the error it is really there to catch -- a units claim that is wrong -- is a
    factor of 25.4 and survives any percentage.
    """
    shape = read_step(step_path)
    solids = [TopoDS.Solid_s(s) for s in explore(shape, TopAbs_SOLID)]
    volume = volume_of(shape)
    mesh_volume = mesh["volume"] or 1.0
    report = {
        "solids": len(solids),
        "valid": bool(BRepCheck_Analyzer(shape).IsValid()),
        "faces": sum(1 for _ in explore(shape, TopAbs_FACE)),
        "faceKinds": face_kinds(shape),
        "volumeMesh": mesh["volume"],
        "volumeStep": round(volume, digits),
        "volumeDeltaPct": round(100 * (volume - mesh["volume"]) / mesh_volume, 4),
        "bboxMesh": mesh["bbox"]["size"],
        "bboxStep": bbox_of(shape, digits),
    }
    report["analyticSurfaces"] = sum(v for k, v in report["faceKinds"].items()
                                     if k in {"cylinder", "cone", "sphere", "torus"})

    problems = []
    if not solids:
        problems.append("no solid in the output: the result is a shell or loose faces, "
                        "which cannot be cut, mounted against or measured for volume")
    if not report["valid"]:
        problems.append("the kernel reports the shape as invalid")
    if abs(report["volumeDeltaPct"]) > volume_tolerance:
        problems.append(f"volume moved {report['volumeDeltaPct']:+.4f}% against the mesh, "
                        f"tolerance is {volume_tolerance}%")
    if report["bboxMesh"] != report["bboxStep"]:
        floor = 10 ** -digits * 10
        over = [abs(a - b) for a, b in zip(report["bboxMesh"], report["bboxStep"])
                if abs(a - b) > max(floor, abs(a) * volume_tolerance / 100)]
        if over:
            problems.append(f"bounding box moved: {report['bboxMesh']} -> "
                            f"{report['bboxStep']}, worst axis {max(over):.4f} mm "
                            f"against a {volume_tolerance}% allowance")
    report["problems"] = problems
    report["ok"] = not problems

    # Only the conversion that otherwise passed pays for this, which is also
    # the one the chain is about to keep: a backend already rejected on volume
    # or box does not need a second reason.
    #
    # It is reported, not counted as a problem, and that is a deliberate
    # asymmetry. A self-intersection is usually inherited from the mesh -- an
    # exact conversion, volume and box to the digit, still carried them on the
    # body this was written for -- so failing here would send the chain through
    # every remaining backend, an hour of work, to arrive at the same defect
    # and then write nothing at all. A faceted reference that reproduces the
    # object is worth having with the defect recorded; what is not acceptable
    # is calling it valid.
    if report["ok"] and self_intersection_budget:
        report["selfIntersection"] = self_intersecting_solids(
            solids, self_intersection_budget)
    else:
        report["selfIntersection"] = None
    return report


# --------------------------------------------------------------------------
# backends
# --------------------------------------------------------------------------

TOOLS = {
    "2step": {
        "repo": "https://github.com/yaneony/2STEP-Converter",
        "dir": CACHE / "2STEP-Converter",
        "launcher": "2STEP-Converter.sh",
        "cost": "~7.6 GB and 5-15 minutes on first run (it installs its own "
                "micromamba environment)",
        "gives": "mesh repair, coplanar merging, and complete spheres, cylinders, "
                 "cones and straight holes restored as analytic surfaces",
    },
    "stltostp": {
        "repo": "https://github.com/slugdev/stltostp",
        "dir": CACHE / "stltostp",
        "binary": "build/stltostp",
        "cost": "a few seconds: a C++ build with no dependencies",
        "gives": "triangle-to-triangle conversion with coplanar merging, no "
                 "analytic surfaces",
    },
    "sew": {
        "repo": None,
        "dir": None,
        "cost": "nothing: it runs on the OCP the CAD skill already requires",
        "gives": "the same idea as stltostp, in process, with no network",
    },
}
ORDER = ("2step", "stltostp", "sew")


def tool_path(name):
    """Where a backend is, or None. Honours an explicit override first."""
    if name == "sew":
        return Path(__file__).resolve()
    override = os.environ.get(f"{name.upper().replace('2', 'TWO')}_HOME")
    roots = [Path(override)] if override else []
    roots.append(TOOLS[name]["dir"])
    for root in roots:
        if name == "2step":
            launcher = root / TOOLS[name]["launcher"]
            if launcher.exists():
                return launcher
        else:
            binary = root / TOOLS[name]["binary"]
            if binary.exists():
                return binary
    if name == "stltostp":
        found = shutil.which("stltostp")
        if found:
            return Path(found)
    return None


def _run(command, timeout, cwd=None):
    try:
        done = subprocess.run(command, capture_output=True, text=True,
                              timeout=timeout, cwd=cwd)
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout}s"
    except OSError as exc:
        return False, f"{type(exc).__name__}: {exc}"
    if done.returncode != 0:
        tail = (done.stderr or done.stdout or "").strip().splitlines()
        return False, f"exit {done.returncode}" + (f": {tail[-1][:200]}" if tail else "")
    return True, ""


_HELP_CACHE = {}


def _supported_flags(launcher, timeout=300):
    """Ask the tool which flags it takes instead of assuming.

    This backend is driven, not vendored: its CLI belongs to another project and
    can change between releases. Sending a flag it does not know turns a working
    conversion into an argparse error and a silent fall-through to the next
    backend, so the flags come from its own --help.
    """
    key = str(launcher)
    if key not in _HELP_CACHE:
        try:
            done = subprocess.run([str(launcher), "--no-pause", "--help"],
                                  capture_output=True, text=True, timeout=timeout,
                                  cwd=str(Path(launcher).parent))
            _HELP_CACHE[key] = (done.stdout or "") + (done.stderr or "")
        except (subprocess.TimeoutExpired, OSError):
            _HELP_CACHE[key] = ""
    return _HELP_CACHE[key]


def backend_2step(stl, out, options):
    launcher = tool_path("2step")
    if launcher is None:
        return False, "not installed"
    # Alone among the backends this one runs from its own checkout, so a
    # caller's relative path would resolve under the tool cache: the input comes
    # back "File not found" and the output would be written into the cache.
    stl, out = Path(stl).resolve(), Path(out).resolve()
    help_text = _supported_flags(launcher, min(options["timeout"], 600))

    def takes(flag):
        # With no help text to read, keep to the two flags the project's own
        # README documents and this backend cannot work without.
        return flag in help_text if help_text else flag in ("--output", "--tolerance")

    command = [str(launcher)]
    for flag in ("--no-pause", "--no-preview", "--batch", "--force"):
        if takes(flag):
            command.append(flag)
    if takes("--format"):
        command += ["--format", options["schema"].lower()]
    if takes("--tolerance"):
        command += ["--tolerance", str(options["tolerance"])]
    command += ["--output", str(out)]
    command += (["--input", str(stl)] if takes("--input") and "[files]" not in help_text
                else [str(stl)])

    ok, detail = _run(command, options["timeout"], cwd=str(launcher.parent))
    if ok and not Path(out).exists():
        return False, "reported success but wrote no file"
    return ok, detail or ("flags: " + " ".join(command[1:-1]) if help_text else "")


def backend_stltostp(stl, out, options):
    binary = tool_path("stltostp")
    if binary is None:
        return False, "not installed"
    ok, detail = _run([str(binary), str(stl), str(out),
                       "tol", str(options["tolerance"]),
                       "units", "mm",
                       "schema", "214" if options["schema"].upper() == "AP214" else "203",
                       "mergeplanar"], options["timeout"])
    if ok and not Path(out).exists():
        return False, "reported success but wrote no file"
    return ok, detail


_SELF = Path(__file__).resolve()


def _stage(name, out, arguments, timeout):
    """Run one OpenCASCADE stage in a child process, so it can be stopped.

    Sewing is a single C++ call that never returns to the interpreter until it
    is done, so a signal-based deadline does not land until the call is already
    over: there is nothing in this process that can cut it short. A child can be
    killed. That is the only reason this indirection exists, and it is what
    makes --timeout mean the same thing on the built-in backend as on the two
    that already shell out.
    """
    report = Path(out).with_suffix(".stage.json")
    report.unlink(missing_ok=True)
    command = [sys.executable, str(_SELF), name] + [str(a) for a in arguments]
    ok, detail = _run(command, timeout)
    if not ok:
        report.unlink(missing_ok=True)
        return False, detail, {}
    try:
        payload = json.loads(report.read_text())
    except (OSError, ValueError) as exc:
        return False, f"{name} stage left no report: {type(exc).__name__}", {}
    finally:
        report.unlink(missing_ok=True)
    return True, "", payload


def backend_sew(stl, out, options):
    ok, detail, stats = _stage("sew", out,
                               [stl, out, options["tolerance"], options["schema"]],
                               options["timeout"])
    if not ok:
        return False, detail
    return True, f"{stats['shells']} shell(s), {stats['facetsSkipped']} facets skipped"


BACKENDS = {"2step": backend_2step, "stltostp": backend_stltostp, "sew": backend_sew}


def convert(stl, out, options, order=ORDER):
    """Try the backends in order and keep the first result that verifies.

    A backend that exits cleanly and writes an unusable STEP has failed, so the
    verification runs inside the chain rather than after it: that is the whole
    point of having a chain. Every attempt is reported, including the ones that
    were skipped for not being installed, because "it fell back" and "it was
    never there" are different problems with different fixes.
    """
    mesh = mesh_report(read_stl(stl))
    scale = UNIT_SCALE[options["units"]]
    attempts = []
    for name in order:
        if name not in BACKENDS:
            raise SystemExit(f"unknown backend: {name}")
        candidate = Path(out).with_suffix(f".{name}.tmp.step")
        try:
            ok, detail = BACKENDS[name](stl, candidate, options)
        except Exception as exc:                       # a backend must not take the chain down
            ok, detail = False, f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}"
        if not ok:
            # "never installed" and "ran and failed" are different problems with
            # different fixes, and the trail has to keep them apart.
            attempts.append({"backend": name, "ok": False,
                             "stage": "skip" if detail == "not installed" else "convert",
                             "detail": detail})
            candidate.unlink(missing_ok=True)
            continue

        # Promoting a surface model to a solid sews too, on however many faces
        # the backend wrote, so it gets the same budget for the same reason.
        ok, detail, payload = _stage("finish", candidate,
                                     [candidate, candidate, options["tolerance"],
                                      scale, options["schema"]],
                                     options["timeout"])
        if not ok:
            attempts.append({"backend": name, "ok": False, "stage": "read",
                             "detail": detail})
            candidate.unlink(missing_ok=True)
            continue
        repairs = payload["repairs"]

        try:
            verified = verify_conversion(scale_mesh_report(mesh, scale), candidate,
                                         options["volume_tolerance"],
                                         self_intersection_budget=options[
                                             "self_intersection_budget"])
        except Exception as exc:
            attempts.append({"backend": name, "ok": False, "stage": "read",
                             "detail": f"{type(exc).__name__}: "
                                       f"{str(exc).splitlines()[0][:160]}"})
            candidate.unlink(missing_ok=True)
            continue
        verified["repairs"] = repairs
        if not verified["ok"]:
            attempts.append({"backend": name, "ok": False, "stage": "verify",
                             "detail": "; ".join(verified["problems"]),
                             "report": verified})
            candidate.unlink(missing_ok=True)
            continue

        candidate.replace(out)
        attempts.append({"backend": name, "ok": True, "stage": "verify",
                         "detail": detail, "report": verified})
        return {"mesh": mesh, "attempts": attempts, "backend": name,
                "report": verified, "output": str(out), "scale": scale}
    return {"mesh": mesh, "attempts": attempts, "backend": None,
            "report": None, "output": None, "scale": scale}


def install(name, timeout=1800):
    """Fetch and build a backend into the cache. Callers state the cost first."""
    spec = TOOLS[name]
    if spec["repo"] is None:
        return True, "built in: nothing to install"
    spec["dir"].parent.mkdir(parents=True, exist_ok=True)
    if not spec["dir"].exists():
        ok, detail = _run(["git", "clone", "--depth", "1", spec["repo"], str(spec["dir"])],
                          timeout)
        if not ok:
            return False, f"clone failed: {detail}"
    if name == "stltostp":
        ok, detail = _run(["cmake", "-S", str(spec["dir"]), "-B", str(spec["dir"] / "build")],
                          timeout)
        if not ok:
            return False, f"cmake configure failed: {detail}"
        ok, detail = _run(["cmake", "--build", str(spec["dir"] / "build")], timeout)
        if not ok:
            return False, f"build failed: {detail}"
    else:
        launcher = spec["dir"] / spec["launcher"]
        launcher.chmod(0o755)
        # The launcher bootstraps its own environment on first run; --version is
        # the cheapest thing that makes it do so.
        ok, detail = _run([str(launcher), "--no-pause", "--version"], timeout,
                          cwd=str(spec["dir"]))
        if not ok:
            return False, f"environment bootstrap failed: {detail}"
    found = tool_path(name)
    return (found is not None), (str(found) if found else "installed but not found on disk")


# --------------------------------------------------------------------------
# fixtures for the self-checks
# --------------------------------------------------------------------------
# Built here from primitives and meshed on the spot, so the self-checks prove a
# property of this toolchain on geometry they own, need no network, and keep
# working in a repository with no projects in it.

from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut  # noqa: E402
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder  # noqa: E402
from OCP.TopTools import TopTools_ListOfShape  # noqa: E402
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt  # noqa: E402


def _cut(a, b):
    builder = BRepAlgoAPI_Cut()
    first, second = TopTools_ListOfShape(), TopTools_ListOfShape()
    first.Append(a)
    second.Append(b)
    builder.SetArguments(first)
    builder.SetTools(second)
    builder.Build()
    return builder.Shape()


def fixture_shape(name):
    if name == "block_with_bore":
        return _cut(BRepPrimAPI_MakeBox(gp_Pnt(0, 0, 0), 30, 20, 10).Shape(),
                    BRepPrimAPI_MakeCylinder(
                        gp_Ax2(gp_Pnt(15, 10, -5), gp_Dir(0, 0, 1)), 4, 20).Shape())
    if name == "coplanar_overlap":
        # The other mechanism, on its own: two triangles in one plane, sharing
        # area and no vertex. Nothing about this is visible to an edge count.
        return None
    if name == "crossing_bodies":
        # Two boxes that overlap and were never booleaned: each is closed and
        # manifold, and their facets cut straight through one another. This is
        # what a sculpt or an uncleaned boolean hands over.
        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        builder.Add(compound, BRepPrimAPI_MakeBox(gp_Pnt(0, 0, 0), 10, 10, 10).Shape())
        builder.Add(compound, BRepPrimAPI_MakeBox(gp_Pnt(5, 5, 5), 10, 10, 10).Shape())
        return compound
    if name == "two_bodies":
        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        builder.Add(compound, BRepPrimAPI_MakeBox(gp_Pnt(0, 0, 0), 10, 10, 10).Shape())
        builder.Add(compound, BRepPrimAPI_MakeBox(gp_Pnt(20, 0, 0), 6, 6, 6).Shape())
        return compound
    raise SystemExit(f"unknown fixture: {name}")


def triangles_of(triangulation):
    out = []
    for index in range(1, triangulation.NbTriangles() + 1):
        i1, i2, i3 = triangulation.Triangle(index).Get()
        out.append([(triangulation.Node(i).X(), triangulation.Node(i).Y(),
                     triangulation.Node(i).Z()) for i in (i1, i2, i3)])
    return out


def write_stl_ascii(triangles, path):
    lines = ["solid fixture"]
    for (ax, ay, az), (bx, by, bz), (cx, cy, cz) in triangles:
        lines += ["facet normal 0 0 0", "  outer loop",
                  f"    vertex {ax:.6f} {ay:.6f} {az:.6f}",
                  f"    vertex {bx:.6f} {by:.6f} {bz:.6f}",
                  f"    vertex {cx:.6f} {cy:.6f} {cz:.6f}",
                  "  endloop", "endfacet"]
    lines.append("endsolid fixture")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return Path(path)


def fixture_stl(name, directory, deflection=0.05):
    """Write a fixture as an STL, the way a user's slicer would hand one over."""
    directory = Path(directory)
    if name == "open_mesh":
        # The same block with a few facets missing: a hole in the surface, which
        # is the single most common reason a real STL cannot become a solid.
        source = fixture_stl("block_with_bore", directory, deflection)
        triangles = triangles_of(read_stl(source))
        return write_stl_ascii(triangles[:-4], directory / "open_mesh.stl")
    if name == "coplanar_overlap":
        return write_stl_ascii(
            [[(0, 0, 0), (10, 0, 0), (0, 10, 0)],
             [(2, 2, 0), (12, 2, 0), (2, 12, 0)]],
            directory / "coplanar_overlap.stl")
    if name == "dented_box":
        # One body that passes through itself, which is a different fixture
        # from two bodies that pass through each other: a box whose top face is
        # replaced by a dent driven to an apex below the floor, so the dent
        # walls cut the bottom face from inside. The shell stays closed and
        # every edge still meets exactly two facets, so it sews into a single
        # solid and BRepCheck_Analyzer calls it well-formed -- which is the
        # whole point. Only the BOP check sees what is wrong with it.
        b = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)]
        t = [(0, 0, 10), (10, 0, 10), (10, 10, 10), (0, 10, 10)]
        apex = (5, 5, -5)
        triangles = [[b[0], b[3], b[2]], [b[0], b[2], b[1]]]
        for i in range(4):
            j = (i + 1) % 4
            triangles += [[b[i], b[j], t[j]], [b[i], t[j], t[i]]]
            triangles.append([t[i], t[j], apex])
        return write_stl_ascii(triangles, directory / "dented_box.stl")
    shape = fixture_shape(name)
    BRepMesh_IncrementalMesh(shape, deflection, False, 0.2, True)
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    path = directory / f"{name}.stl"
    if not writer.Write(shape, str(path)):
        raise SystemExit(f"could not write the {name} fixture")
    return path


DEFAULTS = {"tolerance": 1e-6, "schema": "AP214", "units": "mm",
            "volume_tolerance": 1.0, "timeout": 900,
            # Seconds for the BOP self-intersection count on the winning
            # conversion. 0 turns it off and forfeits the answer; it does not
            # make the shape clean. Roughly 20 s for 100 solids over 49k faces,
            # so the default carries a body of that size and says so when it
            # runs out rather than reporting a partial count as the whole.
            "self_intersection_budget": 120.0}


def options(**overrides):
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in overrides.items() if v is not None})
    return merged


# --------------------------------------------------------------------------
# the child side of _stage: one bounded OpenCASCADE step, then a report
# --------------------------------------------------------------------------

def _stage_main(argv):
    """Do one stage and leave its numbers beside the output for the parent.

    The report is a file rather than stdout because a killed child has no
    stdout worth reading, and its absence is how the parent tells "finished"
    from "ran out of time".
    """
    name, out = argv[0], Path(argv[2])
    if name == "sew":
        stl, tolerance, schema = Path(argv[1]), float(argv[3]), argv[4]
        shape, payload = sew_solid(read_stl(stl), tolerance, merge=True)
        write_step(shape, out, schema)
    elif name == "finish":
        source, tolerance = Path(argv[1]), float(argv[3])
        scale, schema = float(argv[4]), argv[5]
        shape, repairs = read_step_any(source)
        promoted, promotions = promote_to_solid(shape, tolerance)
        repairs += promotions
        # A faceted result is rewritten even when nothing changed: the backend's
        # own writer keeps two pcurves per edge, which is over half the file.
        if repairs or scale != 1.0 or all_planar(promoted):
            write_step(scale_shape(promoted, scale), out, schema)
        payload = {"repairs": repairs}
    else:
        raise SystemExit(f"unknown stage: {name}")
    out.with_suffix(".stage.json").write_text(json.dumps(payload))
    return 0


if __name__ == "__main__":
    sys.exit(_stage_main(sys.argv[1:]))
