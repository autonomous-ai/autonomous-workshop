#!/usr/bin/env python3
"""Printable decorative detail: rivets, bosses, low domes, bands, rims, pipe
ribs, inset panels, lancet windows, grille slits and teardrop bores -- and the
blunt free edge every point, chisel, keel or rib end needs.

A Component Worker adds requested surface detail with these instead of
modelling it by hand. Every feature

- refuses a size below the wiki's limit for the run's nozzle, naming the limit
  and the page it comes from (`limits()` lists them all);
- grows a root into the host, so it never stands on a feather edge where the
  host curves away under it;
- gives every face that would look down a 52 deg slope in the declared print
  direction: a cone of material under a rivet or boss on a wall, a drafted
  flank on the low side of a band or rib, a sloped roof over a recess, a
  pointed top on a window (the overhangs page's 52 deg rule, 7 deg inside the
  45 deg gate), and checks every new face of its own tessellation for it;
- ends in a step or a chamfer whose flat stays at least one minimum wall wide;
- returns one valid solid, or raises `PrintLimitError`;
- tags what it made in `PRINT_DETAIL_TAGS`, so a print gate that fails a
  region on or beside it names the feature and the line that made it.

A part entry uses it after the Workshop Manager has copied it into the CAD
project (`print_details.py --install <cad-project>` writes
`features/print_details.py`, so the sealed project stays self-contained):

    from build123d import Axis
    from features import print_details
    pd = print_details.Details(nozzle=0.4)        # up=(0, 0, 1): the print stance
    body = pd.rivets(body, pd.around(Axis.Z, 12.0, 8, z=6.0), d=2.4, h=0.8)
    body = pd.band(body, pd.ring(Axis((0, 0, 4), (0, 0, 1)), 12.0), width=2.0, height=1.0)
    body = pd.window(body, (0, -12, 8), width=4, height=10, depth=1.6)

A point is on the host's surface; the outward normal there is read from the
nearest face. `up` is the direction the print grows in the generator's own
coordinates: +Z for an entry already in its print stance.

    python print_details.py --limits [--nozzle 0.4]
    python print_details.py --install <cad-project>
    python print_details.py --self-check [--nozzle 0.4] [--overhang-angle 45]

The self-check builds every feature at its minimum and default sizes, on a
top face and on a side wall, and runs the cad skill's own `check_thickness`
and `check_overhang` on each. It exits non-zero on any failure.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = ["Details", "PrintLimitError", "Ring", "Segment", "limits", "PRINT_DETAIL_TAGS"]

# Every feature this library made in this process, oldest first: `kind`,
# `name` (`rivet-2`), `site` (`part_x.step.py:42`, the line that asked for it)
# and `shape` (what it added, cut, or the land it left, in the generator's
# coordinates). `check_thickness` and `check_overhang` read it after building
# the entry and name the feature nearest each failing region (issue #82).
PRINT_DETAIL_TAGS: list = []

WIKI = ".agents/skills/wiki/pages/"
WALL_PAGE = "printing/wall-thickness-and-hollowing.md"
FEATURE_PAGE = "printing/fdm-minimum-feature-sizes.md"
OVERHANG_PAGE = "printing/overhangs-and-print-orientation.md"

# A face designed at the gate's limit fails it: tessellated, its facets land
# just past the angle (overhangs page, "Do not design at the limit": a 52 deg
# rise passes at any tolerance). Design 7 deg inside. The check reads the
# gates' own tessellation, whose facets on a small round stray a few degrees
# past the design angle, so it holds them to 1 deg inside the gate.
_DESIGN_MARGIN = 7.0
_VERIFY_MARGIN = 1.0
# A host face that looks further down than this already hangs over the bed.
_MIN_ELEVATION = -10.0
_CHAMFER_ANGLE = 60.0          # a chamfer's generatrix from the feature axis
_TESSELLATION = (0.02, 0.2)    # the print gates' own deviation (printlib)
# check_overhang lets a down-facing region under 1 mm2 pass as a trace; a
# sliver facet where two faces are trimmed is one. Allow a quarter of that.
_TRACE_AREA = 0.25             # mm2
_ROOT = 0.15                   # how far a raised root reaches below contact
_LIFT = 0.3                    # how far a cut starts outside the surface


class PrintLimitError(ValueError):
    """A detail that cannot print at this nozzle, or cannot print here."""


def _call_site() -> str:
    """`file.py:line` of the first caller outside this library."""
    import os
    import sys
    here = os.path.normcase(os.path.abspath(__file__))
    frame = sys._getframe(1)
    while frame is not None and os.path.normcase(os.path.abspath(frame.f_code.co_filename)) == here:
        frame = frame.f_back
    if frame is None:
        return "unknown"
    return f"{os.path.basename(frame.f_code.co_filename)}:{frame.f_lineno}"


def _tag(kind: str, shapes) -> None:
    """Record one feature for the print gates; see PRINT_DETAIL_TAGS."""
    b = _b3d()
    shapes = [shape for shape in shapes if shape is not None]
    if not shapes:
        return
    shape = shapes[0] if len(shapes) == 1 else b.Compound(children=shapes)
    number = 1 + sum(1 for tag in PRINT_DETAIL_TAGS if tag["kind"] == kind)
    PRINT_DETAIL_TAGS.append({"kind": kind, "name": f"{kind}-{number}", "site": _call_site(),
                              "shape": shape})


def _line(nozzle: float) -> float:
    if not nozzle > 0:
        raise ValueError(f"nozzle must be positive, got {nozzle}")
    return float(nozzle)


def limits(nozzle: float = 0.4, overhang_angle: float = 45.0) -> dict:
    """Every limit the features enforce: name -> (value, unit, wiki page, why)."""
    line = _line(nozzle)
    return {
        "min_wall": (2 * line, "mm", WALL_PAGE,
                     "two extruded lines; a flat, crest or web narrower than this is dropped"),
        "min_feature": (max(2.0, 4 * line), "mm", FEATURE_PAGE,
                        "a rivet, boss or dome across: 2 mm (3D Hubs), 4 line widths (Hydra Research)"),
        "min_relief_width": (2.25 * line, "mm", FEATURE_PAGE,
                             "a raised band, rim or rib across: > 0.9 mm at 0.4 mm lines (Hydra Research)"),
        "min_relief_height": (0.5, "mm", FEATURE_PAGE,
                              "raised detail out of the surface: 0.5 mm (Forge Labs)"),
        "min_cut_width": (1.25 * line, "mm", FEATURE_PAGE,
                          "an engraved groove, slit or gap: > 0.5 mm at 0.4 mm lines (Hydra Research, Forge Labs)"),
        "min_cut_depth": (0.5, "mm", FEATURE_PAGE,
                          "an engraved or inset cut: >= 0.5 mm deep (HLH Rapid)"),
        "min_web": (4 * line, "mm", WALL_PAGE,
                    "material between two cut copies: twice the minimum wall, the gate reads low by a step"),
        "overhang_angle": (float(overhang_angle), "deg", OVERHANG_PAGE,
                           "no face may look down more than this from vertical"),
        "design_overhang": (overhang_angle - _DESIGN_MARGIN, "deg", OVERHANG_PAGE,
                            "the most any face is designed to look down: a 52 deg rise"),
    }


def _refuse(feature: str, what: str, value: float, name: str, table: dict) -> None:
    limit, unit, page, why = table[name]
    raise PrintLimitError(
        f"{feature}: {what} {value:.2f} {unit} is below the {name.replace('_', ' ')} "
        f"of {limit:.2f} {unit} ({why}; {WIKI}{page})")


@dataclass(frozen=True)
class Segment:
    """A straight path on one host face, from `start` to `end` (both on it)."""
    start: tuple
    end: tuple


@dataclass(frozen=True)
class Ring:
    """A circle of `radius` about `axis`, in the plane through its origin.

    `normal="radial"` runs it round a wall (a band on a cylinder);
    `normal="axial"` stands it on a face across the axis (a rim on a disc),
    on the side the axis direction points to.
    """
    axis: object
    radius: float
    normal: str = "radial"


# ---------------------------------------------------------------- geometry ---

def _b3d():
    import build123d
    return build123d


def _vec(value):
    b = _b3d()
    return value if isinstance(value, b.Vector) else b.Vector(*value)


def _unit(v):
    if v.length < 1e-9:
        raise ValueError("zero-length direction")
    return v / v.length


def _elevation(normal, up) -> float:
    """Degrees a direction points above level."""
    return math.degrees(math.asin(max(-1.0, min(1.0, normal.dot(up)))))


def _side_beta(across: float, out: float, design: float):
    """The least lean off the outward axis, in degrees, that keeps a flank
    within `design` deg of looking down.

    The flank's outward normal is `cos(beta) * side + sin(beta) * normal`;
    `across` and `out` are the up-components of `side` and `normal`. None
    when no lean below 85 deg is enough.
    """
    limit = math.sin(math.radians(design))
    for tenth in range(0, 851):
        beta = math.radians(tenth / 10)
        if -(math.cos(beta) * across + math.sin(beta) * out) <= limit + 1e-12:
            return tenth / 10
    return None


def _profile_face(items):
    """A closed face in the local XZ plane from (u, w) items: a point, or
    ("arc", (u_mid, w_mid), (u_end, w_end)). The first item is a point."""
    b = _b3d()
    edges = []
    cursor = b.Vector(items[0][0], 0, items[0][1])
    for item in list(items[1:]) + [items[0]]:
        if isinstance(item[0], str):
            mid = b.Vector(item[1][0], 0, item[1][1])
            end = b.Vector(item[2][0], 0, item[2][1])
            edges.append(b.Edge.make_three_point_arc(cursor, mid, end))
        else:
            end = b.Vector(item[0], 0, item[1])
            if (end - cursor).length < 1e-9:
                continue
            edges.append(b.Edge.make_line(cursor, end))
        cursor = end
    return b.Face(b.Wire(edges))


def _end(item):
    return item[2] if isinstance(item[0], str) else item


def _join(right, left):
    """A closed profile from two halves, each running from the axis at the
    bottom, out, up and back to the axis at the top; `left` is drawn on +u
    and mirrored."""
    back = []
    for index in range(len(left) - 1, 0, -1):
        item = left[index]
        target = _end(left[index - 1])
        if isinstance(item[0], str):
            back.append(("arc", (-item[1][0], item[1][1]), (-target[0], target[1])))
        else:
            back.append((-target[0], target[1]))
    return list(right) + back


def _half_flat(a, h, beta, chamfer, root):
    """One half of a relief `h` high whose shoulder is `a` out from its axis,
    with a chamfer `chamfer` high on top and its flank leaning `beta`, so
    its foot spreads past `a`: (items, top half-width)."""
    t = math.tan(math.radians(beta))
    foot = a + (h - chamfer) * t
    items = [(0.0, -root), (foot + root * t, -root), (foot, 0.0), (a, h - chamfer)]
    top = a
    if chamfer > 0:
        top = a - chamfer * math.tan(math.radians(max(_CHAMFER_ANGLE, beta)))
        items.append((top, h))
    items.append((0.0, h))
    return items, top


def _half_round(r, beta, root):
    """One half of a round relief of radius `r`; where its arc would lean less
    than `beta` off vertical it continues down its tangent instead."""
    th = math.radians(90.0 - beta)
    t = math.tan(math.radians(beta))
    a = r if beta <= 1e-3 else r / math.sin(th)
    items = [(0.0, -root), (a + root * t, -root), (a, 0.0)]
    if beta > 1e-3:
        items.append((r * math.sin(th), r * math.cos(th)))
    items.append(("arc", (r * math.sin(th / 2), r * math.cos(th / 2)), (0.0, r)))
    return items, a


def _half_dome(a, h, root):
    """One half of a spherical cap: (items, rim angle in degrees)."""
    radius = (a * a + h * h) / (2 * h)
    centre = h - radius
    alpha = math.asin(min(1.0, a / radius))
    mid = alpha / 2
    items = [(0.0, -root), (a, -root), (a, 0.0),
             ("arc", (radius * math.sin(mid), centre + radius * math.cos(mid)), (0.0, h))]
    return items, math.degrees(alpha)


def _revolved(half):
    b = _b3d()
    return b.revolve(_profile_face(half), b.Axis.Z, 360)


def _as_face(outline):
    b = _b3d()
    if isinstance(outline, b.Face):
        return outline
    faces = outline.faces()
    if len(faces) != 1:
        raise ValueError("an outline is one face")
    return faces[0]


@dataclass(frozen=True)
class _Spot:
    point: object
    normal: object
    x: object

    def plane(self):
        b = _b3d()
        return b.Plane(origin=self.point, x_dir=self.x, z_dir=self.normal)


# ----------------------------------------------------------------- details ---

class Details:
    """The feature library bound to one nozzle and one print direction."""

    def __init__(self, nozzle: float = 0.4, up=(0, 0, 1), overhang_angle: float = 45.0):
        self.nozzle = _line(nozzle)
        self.up = _unit(_vec(up))
        self.overhang_angle = float(overhang_angle)
        self.design = self.overhang_angle - _DESIGN_MARGIN
        self.table = limits(self.nozzle, self.overhang_angle)

    def limit(self, name: str) -> float:
        return self.table[name][0]

    def _at_least(self, feature, what, value, name):
        if value < self.limit(name) - 1e-9:
            _refuse(feature, what, value, name, self.table)

    # -- placement ------------------------------------------------------------

    def spot(self, host, point, angle: float = 0.0) -> _Spot:
        """The host's outward normal at `point`, and the feature's local X.

        Local Y runs uphill on the face (the print direction projected onto
        it), so an arch or a gable points up; `angle` turns the feature about
        the normal from there.
        """
        b = _b3d()
        p = _vec(point)
        face = min(host.faces(), key=lambda f: f.distance_to(p))
        if face.distance_to(p) > 0.05:
            raise ValueError(f"point {tuple(round(c, 3) for c in p)} is not on the host's surface")
        n = _unit(face.normal_at(p))
        if host.is_inside(p + n * 0.02) and not host.is_inside(p - n * 0.02):
            n = -n
        uphill = self.up - n * self.up.dot(n)
        if uphill.length < 1e-6:
            ref = b.Vector(1, 0, 0) if abs(n.X) < 0.9 else b.Vector(0, 1, 0)
            x = _unit(ref - n * ref.dot(n))
        else:
            x = _unit(_unit(uphill).cross(n))
        if angle:
            x = _unit(x.rotate(b.Axis((0, 0, 0), tuple(n)), angle))
        return _Spot(p, n, x)

    def around(self, axis, radius: float, count: int, z: float = 0.0, phase: float = 0.0) -> list:
        """`count` points evenly round a circle of `radius` about `axis`, `z`
        along it: on a cylinder wall of that radius, or on a face across it."""
        origin = axis.position + axis.direction * z
        e1, e2 = self._across(axis.direction)
        return [origin + (e1 * math.cos(a) + e2 * math.sin(a)) * radius
                for a in (math.radians(phase) + 2 * math.pi * i / count for i in range(count))]

    @staticmethod
    def along(start, end, count: int) -> list:
        """`count` points evenly from `start` to `end`, both included."""
        s, e = _vec(start), _vec(end)
        if count == 1:
            return [(s + e) * 0.5]
        return [s + (e - s) * (i / (count - 1)) for i in range(count)]

    @staticmethod
    def ring(axis, radius: float, normal: str = "radial") -> Ring:
        return Ring(axis, radius, normal)

    @staticmethod
    def segment(start, end) -> Segment:
        return Segment(tuple(start), tuple(end))

    @staticmethod
    def _across(direction):
        b = _b3d()
        d = _unit(direction)
        ref = b.Vector(1, 0, 0) if abs(d.X) < 0.9 else b.Vector(0, 1, 0)
        e1 = _unit(ref - d * ref.dot(d))
        return e1, d.cross(e1)

    # -- point features, revolved about the surface normal --------------------

    def boss(self, host, at, d: float = 4.0, h: float = 1.5):
        """A round boss ending in a step: a flat top. `at` may be a list."""
        return self._relief_points(host, at, "boss", d, h, chamfer=0.0)

    def rivet(self, host, at, d: float = 3.0, h: float = 1.0):
        """A rivet: a round boss with its top edge chamfered. `at` may be a
        list of points (a ring, a row), placed in one operation."""
        return self._relief_points(host, at, "rivet", d, h, chamfer=self._chamfer(d, h * 0.4))

    rivets = rivet

    def dome(self, host, at, d: float = 8.0, h: float = 1.2):
        """A low dome: a spherical cap `d` across and `h` high. Off a top face
        its rim must meet the surface within the design angle, so it is lower
        there; the error names the height that fits."""
        name = "dome"
        self._at_least(name, "diameter", d, "min_feature")
        self._at_least(name, "height", h, "min_relief_height")
        if h > d / 2:
            raise PrintLimitError(f"{name}: height {h:.2f} mm is more than a hemisphere {d:.2f} mm across")

        def build(elevation, root, buttress):
            half, alpha = _half_dome(d / 2, h, root)
            allowed = min(90.0, self.design + elevation)
            if alpha > allowed + 1e-6:
                lower = d / 2 * math.tan(math.radians(allowed) / 2)
                raise PrintLimitError(
                    f"{name}: its rim meets the surface at {alpha:.1f} deg, more than the "
                    f"{allowed:.1f} deg this face allows before its lower edge looks down past "
                    f"{self.design:.0f} deg; make it at most {lower:.2f} mm high here "
                    f"({WIKI}{OVERHANG_PAGE})")
            return _revolved(half)
        return self._place_points(host, at, name, build, d, h, buttressed=False)

    def _chamfer(self, across, wanted):
        """The largest chamfer up to `wanted` that leaves a top flat at least
        one minimum wall across; none when that is under 0.05 mm."""
        room = (across - self.limit("min_wall")) / (2 * math.tan(math.radians(_CHAMFER_ANGLE)))
        chamfer = min(wanted, room)
        return chamfer if chamfer >= 0.05 else 0.0

    def _relief_points(self, host, at, name, d, h, chamfer):
        self._at_least(name, "diameter", d, "min_feature")
        self._at_least(name, "height", h, "min_relief_height")
        _, top = _half_flat(d / 2, h, 0.0, chamfer, _ROOT)
        if 2 * top < self.limit("min_wall") - 1e-9:
            _refuse(name, "top flat", 2 * top, "min_wall", self.table)

        def build(elevation, root, buttress):
            body = _revolved(_half_flat(d / 2, h, 0.0, chamfer, root)[0])
            if buttress is not None:
                supported = body + self._support(d / 2, h - chamfer, root, buttress)
                if len(supported.solids()) != 1 or supported.volume < body.volume + 1e-3:
                    raise PrintLimitError(f"{name}: its support did not join it")
                body = supported
            return body
        return self._place_points(host, at, name, build, d, h, buttressed=True)

    @staticmethod
    def _support(radius, height, root, gamma):
        """Material under a round relief on a wall: its shoulder disc swept
        down into the host along a 52 deg slope (overhangs page: put material
        under the feature), so its lower flank never faces down."""
        b = _b3d()
        g = math.radians(gamma)
        # sunk past the root's floor: coincident faces would drop the fuse
        reach = (height + root + 0.1) / math.sin(g)
        # a hair outside the relief's own radius: two equal round flanks
        # would touch along a line, and that tangency tessellates open
        disc = b.Plane.XY.offset(height) * b.Circle(radius + 0.03)
        return b.extrude(disc, reach, dir=(0, -math.cos(g), -math.sin(g)))

    def _gamma(self, elevation):
        """How steeply material under a wall feature dives into the host, or
        None where the face is steep enough to need none."""
        gamma = elevation + self.design
        return None if gamma >= 89.999 else gamma

    # -- path features --------------------------------------------------------

    def band(self, host, path, width: float = 2.0, height: float = 1.0):
        """A raised band, chamfered on top, along a `Segment` or round a `Ring`."""
        name = "band"
        self._at_least(name, "width", width, "min_relief_width")
        self._at_least(name, "height", height, "min_relief_height")
        chamfer = self._chamfer(width, min(height * 0.4, width * 0.15))

        def half(beta, root):
            items, top = _half_flat(width / 2, height, beta, chamfer, root)
            if 2 * top < self.limit("min_wall") - 1e-9:
                _refuse(name, "top flat after its draft on this face", 2 * top, "min_wall", self.table)
            return items, top
        return self._place_path(host, path, name, half, width / 2, height)

    def rim(self, host, axis, radius: float, width: float = 2.0, height: float = 1.0):
        """A raised rim standing on the face across `axis`: a band on an
        axial `Ring`."""
        return self.band(host, Ring(axis, radius, "axial"), width, height)

    def pipe(self, host, path, d: float = 1.5):
        """A half-round pipe rib `d` across along a `Segment` or round a
        `Ring`. Where its underside would look down it continues as a drafted
        flank instead, so it is wider at its foot on that side."""
        name = "pipe"
        self._at_least(name, "diameter", d, "min_relief_width")
        self._at_least(name, "height", d / 2, "min_relief_height")

        def half(beta, root):
            return _half_round(d / 2, beta, root)
        return self._place_path(host, path, name, half, d / 2, d / 2)

    # -- cut features: an outline cut into the host ---------------------------

    def panel(self, host, at, width: float = 8.0, height: float = 12.0,
              depth: float = 0.8, arch: str = "flat", angle: float = 0.0):
        """An inset panel: a blind recess, `flat` or `lancet` (pointed arch)
        topped. On a wall its roof rises outward at 52 deg."""
        name = "panel"
        self._at_least(name, "width", width, "min_cut_width")
        self._at_least(name, "depth", depth, "min_cut_depth")
        return self._place_cuts(host, at, name, (width, height, arch), depth, False, angle)

    def window(self, host, at, width: float = 4.0, height: float = 10.0,
               depth: float = 2.0, arch: str = "lancet", angle: float = 0.0):
        """A window through a wall `depth` thick, `lancet`, `gable` or `flat`
        topped. Off a top face only a pointed top prints: a flat one roofs it."""
        name = "window"
        self._at_least(name, "width", width, "min_cut_width")
        return self._place_cuts(host, at, name, (width, height, arch), depth, True, angle)

    def slit(self, host, at, width: float = 1.2, length: float = 8.0,
             depth: float = 1.0, through: bool = False, angle: float = 0.0):
        """A grille slit `length` long running uphill (turn it with `angle`).
        A blind slit's upper end is roofed at 52 deg; a through slit has
        pointed ends. `at` may be a list of points: a grille in one operation."""
        name = "slit"
        self._at_least(name, "width", width, "min_cut_width")
        if not through:
            self._at_least(name, "depth", depth, "min_cut_depth")
        shape = (width, length, "pointed" if through else "flat")
        return self._place_cuts(host, at, name, shape, depth, through, angle)

    slits = slit

    def bore(self, host, at, d: float = 3.0, depth: float = 2.0, through: bool = True):
        """A round bore `d` across into the host at `at`, `depth` deep (the
        wall's thickness when `through`). On a wall its roof runs straight to a
        point at 52 deg where the circle would look down (a teardrop), so a
        bore through a wall, a vault or a pointed roof needs no support."""
        name = "bore"
        self._at_least(name, "diameter", d, "min_cut_width")
        if not through:
            self._at_least(name, "depth", depth, "min_cut_depth")
        rise = d / 2 * (1 + 1 / math.cos(math.radians(90.0 - self.design)))
        return self._place_cuts(host, at, name, (d, rise, "teardrop"), depth, through, 0.0)

    # -- blunt free edges ------------------------------------------------------

    def blunt_tip(self, host, tip, toward, reach: float = 6.0, back: float = 12.0):
        """End a point, chisel, keel or V underside in a flat land one minimum
        wall across (0.8 mm at a 0.4 nozzle), which is what `check_thickness`
        needs: it counts every straight knife edge as a wall.

        `tip` is the sharpest point of the host (a point, or one point on a
        chisel edge or ridge), `toward` the direction it points, out of the
        material. The host is cut square to `toward` where its section within
        `reach` of the tip first spans a minimum wall in every direction, at
        most `back` behind the tip; only material within `reach` of the tip,
        sideways, is removed. A land that
        faces down must rest on the bed: a flat underside in the air is an
        overhang."""
        b = _b3d()
        name = "blunt tip"
        p, axis = _vec(tip), _unit(_vec(toward))
        if host.distance_to(b.Vertex(p)) > 0.05:
            raise ValueError(f"{name}: {tuple(round(c, 3) for c in p)} is not on the host")
        land = self.limit("min_wall")

        def width(depth):
            return self._section_width(host, p - axis * depth, axis, reach)
        step, depth = 0.05, 0.0
        while width(depth) < land:
            depth += step
            if depth > back:
                raise PrintLimitError(
                    f"{name}: the host never spans {land:.2f} mm across within {back:.1f} mm of "
                    f"the tip; give it a fuller tip or a larger `back` ({WIKI}{WALL_PAGE})")
        low, high = max(0.0, depth - step), depth
        for _ in range(6):
            middle = (low + high) / 2
            low, high = (middle, high) if width(middle) < land else (low, middle)
        origin = p - axis * high
        self._land_faces_down(name, host, origin, axis)
        result = self._trim(host, origin, axis, reach, name)
        _tag("blunt-tip", [self._section(result, origin, axis, reach + 1.0)])
        return result

    def rib_end(self, rib, end, toward, reach: float | None = None):
        """End a rib, fin or offset layer you built yourself cleanly at `end`,
        before you fuse it: everything of `rib` past the plane through `end`
        square to `toward` (the direction the rib runs out) is cut away, so
        no sliver is left where an offset or a trim ran out. The end face must
        span a minimum wall in every direction. An end that would look down
        past 52 deg is ramped back instead, like a band's downhill end.

        `reach` bounds the cut sideways (default: the whole rib); do not pass
        the fused host, or the cut takes the host with it."""
        name = "rib end"
        p, axis = _vec(end), _unit(_vec(toward))
        if reach is None:
            reach = rib.bounding_box().diagonal
        if -axis.dot(self.up) > math.sin(math.radians(self.design)) + 1e-9:
            # turn the end face up until it looks down only the design angle:
            # a ramp, not a ceiling. Straight down, any level direction will do.
            level = axis - self.up * axis.dot(self.up)
            level = _unit(level) if level.length > 1e-9 else self._across(self.up)[0]
            lean = math.radians(self.design)
            axis = _unit(level * math.cos(lean) - self.up * math.sin(lean))
        section = self._section(rib, p, axis, reach)
        if section is None:
            raise ValueError(f"{name}: the plane through {tuple(round(c, 3) for c in p)} misses the rib")
        across = min(self._min_width(face, p, axis) for face in section.faces())
        if across < self.limit("min_wall") - 1e-9:
            _refuse(name, "end face across", across, "min_wall", self.table)
        result = self._trim(rib, p, axis, reach, name)
        _tag("rib-end", [section])
        return result

    def _land_faces_down(self, name, host, origin, axis):
        """Refuse a land that looks down past the design angle off the bed."""
        if -axis.dot(self.up) <= math.sin(math.radians(self.design)) + 1e-9:
            return
        box = host.bounding_box()
        bed = min(corner.dot(self.up) for corner in (
            _vec((x, y, z)) for x in (box.min.X, box.max.X)
            for y in (box.min.Y, box.max.Y) for z in (box.min.Z, box.max.Z)))
        if origin.dot(self.up) - bed > 0.2 + 1e-9:
            raise PrintLimitError(
                f"{name}: its land would face down {origin.dot(self.up) - bed:.2f} mm above "
                f"the bed, a flat ceiling with nothing under it; print the part so the tip rests on "
                f"the bed or points up or sideways ({WIKI}{OVERHANG_PAGE})")

    def _cutter(self, origin, axis, reach):
        """The half-space past the plane through `origin` square to `axis`,
        `reach` either side of it."""
        b = _b3d()
        plane = b.Plane(origin=origin, z_dir=axis)
        return plane.location * b.Box(2 * reach, 2 * reach, 4 * reach,
                                      align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))

    def _trim(self, solid, origin, axis, reach, name):
        return self._one_solid(solid.cut(self._cutter(origin, axis, reach)), name)

    @staticmethod
    def _section(solid, origin, axis, reach):
        """The faces where the plane through `origin` square to `axis` cuts
        `solid` within `reach` of `origin`, or None."""
        b = _b3d()
        plane = b.Plane(origin=origin, z_dir=axis)
        window = plane.location * b.Face(b.Wire.make_rect(2 * reach, 2 * reach))
        try:
            cut = solid & window
        except Exception:
            return None
        faces = cut.faces() if cut is not None else []
        if not faces:
            return None
        return faces[0] if len(faces) == 1 else b.Compound(children=faces)

    def _section_width(self, solid, origin, axis, reach):
        """The narrowest the section through `origin` spans, in any direction
        across `axis`: 0 where the plane misses the solid."""
        section = self._section(solid, origin, axis, reach)
        if section is None:
            return 0.0
        return min(self._min_width(face, origin, axis) for face in section.faces())

    @staticmethod
    def _min_width(face, origin, axis):
        """A planar face's least caliper width: the narrowest gap between two
        parallel lines that hold it, over every direction in its plane."""
        import numpy as np
        b = _b3d()
        vertices, _ = face.tessellate(0.005, 0.05)
        points = [tuple(v) for v in vertices] + [tuple(v.center()) for v in face.vertices()]
        if len(points) < 3:
            return 0.0
        plane = b.Plane(origin=origin, z_dir=axis)
        local = np.array([tuple(plane.to_local_coords(b.Vector(*q)))[:2] for q in points])
        angles = np.radians(np.arange(0.0, 180.0, 0.5))
        directions = np.stack([np.cos(angles), np.sin(angles)], axis=1)
        spans = local @ directions.T
        return float((spans.max(axis=0) - spans.min(axis=0)).min())

    def _outline(self, name, width, height, arch, angle=0.0, stretch=0.0, roofed=False):
        """The outline face in the local XY plane, centred, +Y uphill, turned
        `angle` about the normal, its top raised `stretch` with its bottom kept.

        A roofed outline (a blind cut on a wall) is turned only in quarter
        turns of a flat outline, so it can be stretched uphill as one shape.
        """
        b = _b3d()
        quarter = abs(angle / 90.0 - round(angle / 90.0)) < 1e-9
        if roofed and (not quarter or (arch != "flat" and round(angle / 90.0) % 4)):
            raise PrintLimitError(
                f"{name}: on a wall a recess is roofed at 52 deg uphill, so only a flat outline turns, "
                f"in quarter turns, and an arch points up ({WIKI}{OVERHANG_PAGE})")
        if arch == "flat" and quarter and round(angle / 90.0) % 2:
            width, height, angle = height, width, 0.0
        elif quarter and arch == "flat":
            angle = 0.0
        if height < self.limit("min_cut_width") - 1e-9:
            _refuse(name, "height", height, "min_cut_width", self.table)
        face = self._shape(name, width, height + stretch, arch, roofed)
        face = face.moved(b.Location((0, stretch / 2, 0)))
        return face.rotate(b.Axis.Z, angle) if angle else face

    def _shape(self, name, width, height, arch, jambs):
        b = _b3d()
        w2, y0, y1 = width / 2, -height / 2, height / 2
        if arch == "flat":
            return _as_face(b.Rectangle(width, height))
        if arch == "lancet":
            # a pointed arch: each side an arc of radius `width` from its
            # springing point until it leans 52 deg, then straight to the apex,
            # so no part of its roof is flatter than the overhang rule allows
            lean = math.radians(self.design)
            x_end = w2 - width * (1 - math.cos(lean))
            arc_rise = width * math.sin(lean)
            rise = arc_rise + x_end * math.tan(math.pi / 2 - lean)
            if height < rise or (jambs and height - rise < 0.05):
                raise PrintLimitError(
                    f"{name}: a {width:.2f} mm lancet needs more than {rise:.2f} mm of height for its arch")
            ys = y1 - rise
            half = lean / 2
            mid_x = w2 - width * (1 - math.cos(half))
            mid_y = ys + width * math.sin(half)
            edges = [b.Edge.make_line((-w2, y0, 0), (w2, y0, 0))]
            if ys - y0 > 1e-6:
                edges.append(b.Edge.make_line((w2, y0, 0), (w2, ys, 0)))
            edges += [
                b.Edge.make_three_point_arc((w2, ys, 0), (mid_x, mid_y, 0), (x_end, ys + arc_rise, 0)),
                b.Edge.make_line((x_end, ys + arc_rise, 0), (0, y1, 0)),
                b.Edge.make_line((0, y1, 0), (-x_end, ys + arc_rise, 0)),
                b.Edge.make_three_point_arc((-x_end, ys + arc_rise, 0), (-mid_x, mid_y, 0), (-w2, ys, 0)),
            ]
            if ys - y0 > 1e-6:
                edges.append(b.Edge.make_line((-w2, ys, 0), (-w2, y0, 0)))
            return b.Face(b.Wire(edges))
        if arch == "teardrop":
            # a round bore whose roof runs straight to a point once the circle
            # looks down past the design angle: the classic printable hole
            r = w2
            phi = math.radians(90.0 - self.design)       # tangent point from the top
            tx, ty = r * math.sin(phi), r * math.cos(phi)
            apex = r / math.cos(phi)
            cy = -height / 2 + r                         # the circle's centre
            # counter-clockwise, so the face's normal is the local +Z a cut extrudes along
            return b.Face(b.Wire([
                b.Edge.make_line((0, cy + apex, 0), (-tx, cy + ty, 0)),
                b.Edge.make_three_point_arc((-tx, cy + ty, 0), (-r, cy, 0), (0, cy - r, 0)),
                b.Edge.make_three_point_arc((0, cy - r, 0), (r, cy, 0), (tx, cy + ty, 0)),
                b.Edge.make_line((tx, cy + ty, 0), (0, cy + apex, 0)),
            ]))
        if arch in ("gable", "pointed"):
            rise = w2 * math.tan(math.radians(60))
            low = rise if arch == "pointed" else 0.0
            if height < rise + low or (jambs and height - rise - low < 0.05):
                raise PrintLimitError(
                    f"{name}: a {width:.2f} mm pointed end needs more than {rise + low:.2f} mm of length")
            bottom = [(0, y0)] if low else [(-w2, y0), (w2, y0)]
            points = [*bottom, (w2, y0 + low), (w2, y1 - rise), (0, y1), (-w2, y1 - rise), (-w2, y0 + low)]
            unique = []
            for point in points:
                if not unique or math.dist(unique[-1], point) > 1e-9:
                    unique.append(point)
            if math.dist(unique[0], unique[-1]) < 1e-9:
                unique.pop()
            return _as_face(b.Polygon(*unique, align=None))
        raise ValueError("arch is 'flat', 'lancet', 'gable' or 'teardrop'")

    # -- engines --------------------------------------------------------------

    @staticmethod
    def _points(at):
        if isinstance(at, (list, tuple)) and at and not isinstance(at[0], (int, float)):
            return [_vec(p) for p in at]
        return [_vec(at)]

    def _face_allows(self, name, elevation):
        if elevation < _MIN_ELEVATION:
            raise PrintLimitError(
                f"{name}: this face looks {-elevation:.0f} deg down in the print direction; "
                f"detail on it hangs over the bed ({WIKI}{OVERHANG_PAGE})")

    def _sag(self, host, plane, offsets):
        """(below, above): how far the host's surface falls below the tangent
        plane, and rises above it, at the footprint's boundary points."""
        b = _b3d()
        surface = b.Compound(host.faces())
        below = above = 0.0
        for u, v in offsets:
            p = plane.from_local_coords(b.Vector(u, v, 0))
            distance = surface.distance_to(p)
            if host.is_inside(p):
                above = max(above, distance)
            else:
                below = max(below, distance)
        return below, above

    def _relief_root(self, name, below, above, height):
        """The root depth that reaches the host everywhere under a relief."""
        if height - above < self.limit("min_relief_height") - 1e-9:
            _refuse(name, "height left above this concave surface", height - above,
                    "min_relief_height", self.table)
        if below > height:
            raise PrintLimitError(
                f"{name}: the host falls {below:.2f} mm away under its edge, more than its "
                f"{height:.2f} mm height; place it on a flatter spot or make it smaller "
                f"({WIKI}{WALL_PAGE}, 'A groove through a rounded rim leaves a sliver')")
        return max(_ROOT, below + 0.1)

    def _spacing(self, name, spots, extent, raised):
        """The gap (raised) or web (cut) between neighbouring copies."""
        if len(spots) < 2:
            return
        between = min(
            (a.point - c.point).length - extent(a, _unit(c.point - a.point)) / 2
            - extent(c, _unit(a.point - c.point)) / 2
            for i, a in enumerate(spots) for c in spots[i + 1:])
        if raised:
            if between < self.limit("min_cut_width") - 1e-9:
                _refuse(name, "gap between copies", between, "min_cut_width", self.table)
        elif between < self.limit("min_web") - 1e-9:
            _refuse(name, "web between copies", between, "min_web", self.table)

    def _place_points(self, host, at, name, build, d, h, buttressed):
        spots = [self.spot(host, p) for p in self._points(at)]
        solids = []
        reach = 0.0
        for spot in spots:
            elevation = _elevation(spot.normal, self.up)
            self._face_allows(name, elevation)
            gamma = self._gamma(elevation) if buttressed else None
            footprint = [(d / 2 * math.cos(t), d / 2 * math.sin(t)) for t in (math.pi * k / 4 for k in range(8))]
            if gamma is not None:
                reach = (h + 1.0) / math.tan(math.radians(gamma))
                footprint += [(0.0, -d / 2 - reach * f) for f in (0.5, 1.0)]
            root = self._relief_root(name, *self._sag(host, spot.plane(), footprint), h)
            solids.append(spot.plane().location * build(elevation, root, gamma))
        self._spacing(name, spots, lambda s, direction: d + reach * abs(direction.dot(
            _unit(s.normal.cross(s.x)))), raised=True)
        result = self._fuse(host, solids, name)
        _tag(name, solids)
        return result

    def _place_cuts(self, host, at, name, shape, depth, through, angle):
        b = _b3d()
        spots = [self.spot(host, p) for p in self._points(at)]
        tools = []
        roof = 0.0
        box = None
        for spot in spots:
            elevation = _elevation(spot.normal, self.up)
            self._face_allows(name, elevation)
            # a teardrop's roof is already pointed: it needs no sloped roof
            gamma = None if through or shape[2] == "teardrop" else self._gamma(elevation)
            outline = self._outline(name, *shape, angle=angle, roofed=gamma is not None)
            box = outline.bounding_box()
            corners = [(box.min.X, box.min.Y), (box.max.X, box.min.Y), (box.max.X, box.max.Y),
                       (box.min.X, box.max.Y), (0, box.min.Y), (0, box.max.Y), (box.min.X, 0), (box.max.X, 0)]
            below, above = self._sag(host, spot.plane(), corners)
            lift = above + _LIFT
            if through:
                tool = b.Pos(0, 0, -depth - _LIFT) * b.extrude(outline, depth + _LIFT + lift)
            else:
                if depth - below < self.limit("min_cut_depth") - 1e-9:
                    _refuse(name, "depth left where the host curves away", depth - below,
                            "min_cut_depth", self.table)
                if gamma is None:
                    tool = b.Pos(0, 0, -depth) * b.extrude(outline, depth + lift)
                else:
                    # the recess's upper wall would be a roof: slope it so it
                    # rises outward at 52 deg (overhangs page: roof a slot)
                    shift = (depth + lift) / math.tan(math.radians(gamma))
                    roof = max(roof, shift * depth / (depth + lift))   # at the surface
                    mouth = self._outline(name, *shape, angle=angle, stretch=shift, roofed=True)
                    tool = b.Solid.make_loft([
                        outline.outer_wire().moved(b.Location((0, 0, -depth))),
                        mouth.outer_wire().moved(b.Location((0, 0, lift)))], ruled=True)
            tools.append(spot.plane().location * tool)

        def extent(spot, direction):
            y = spot.normal.cross(spot.x)
            return abs(direction.dot(spot.x)) * box.size.X + abs(direction.dot(y)) * (box.size.Y + roof)
        self._spacing(name, spots, extent, raised=False)
        self._check_overhang(name, tools, host, cut=True)
        result = self._one_solid(host.cut(*tools), name)
        _tag(name, tools)
        return result

    def _flank_betas(self, frames):
        """(+u, -u) leans for a profile whose (u, n) frames are `frames`."""
        betas = [0.0, 0.0]
        for u, n in frames:
            for index, sign in enumerate((1.0, -1.0)):
                beta = _side_beta(sign * u.dot(self.up), n.dot(self.up), self.design)
                if beta is None:
                    return None
                betas[index] = max(betas[index], beta)
        return betas

    def _place_path(self, host, path, name, half_for, a0, height):
        b = _b3d()
        if isinstance(path, Segment):
            start, end = _vec(path.start), _vec(path.end)
            mid = (start + end) * 0.5
            n = self.spot(host, mid).normal
            run = end - start
            run = run - n * run.dot(n)
            length = run.length
            if length < 1e-6:
                raise ValueError(f"{name}: the segment is empty")
            s = _unit(run)
            x = s.cross(n)
            plane = b.Plane(origin=mid, x_dir=x, z_dir=n)
            elevation = min(_elevation(self.spot(host, p).normal, self.up) for p in (start, mid, end))
            self._face_allows(name, elevation)
            betas = self._flank_betas([(x, n)])
            ends = [_side_beta(sign * s.dot(self.up), n.dot(self.up), self.design) for sign in (1.0, -1.0)]
            if betas is None or None in ends:
                raise PrintLimitError(f"{name}: this face leans too far over the bed ({WIKI}{OVERHANG_PAGE})")
            reach = max(a0 + height * math.tan(math.radians(beta)) for beta in betas)
            footprint = [(u, v) for u in (-reach, reach) for v in (-length / 2, 0, length / 2)]
            root = self._relief_root(name, *self._sag(host, plane, footprint), height)
            (right, _), (left, _) = half_for(betas[0], root), half_for(betas[1], root)
            extra = height + root + 1.0
            body = b.extrude(_profile_face(_join(right, left)), length / 2 + extra, dir=(0, 1, 0), both=True)
            for sign, beta in zip((1.0, -1.0), ends):
                # a ramped end: a plane through the path's end leaning `beta`
                # back from it, so an end that faces downhill rises at 52 deg
                normal = b.Vector(0, sign * math.cos(math.radians(beta)), math.sin(math.radians(beta)))
                origin = b.Vector(0, sign * length / 2, 0)
                keep = b.Plane(origin=origin, z_dir=-normal)
                body = body.split(keep, keep=b.Keep.TOP)
            solid = plane.location * body
        elif isinstance(path, Ring):
            if path.normal not in ("radial", "axial"):
                raise ValueError("a Ring's normal is 'radial' or 'axial'")
            axis = path.axis
            d = _unit(axis.direction)
            origin = axis.position
            e1, _e2 = self._across(d)
            frames = []
            for p in self.around(axis, path.radius, 24):
                radial = _unit(p - origin)
                frames.append((d, radial) if path.normal == "radial" else (radial, d))
            u0, n0 = (d, e1) if path.normal == "radial" else (e1, d)
            p0 = origin + e1 * path.radius
            self.spot(host, p0)                       # on the host, or raise
            elevation = min(_elevation(n, self.up) for _, n in frames)
            self._face_allows(name, elevation)
            betas = self._flank_betas(frames)
            if betas is None:
                raise PrintLimitError(f"{name}: this ring leans too far over the bed ({WIKI}{OVERHANG_PAGE})")
            plane = b.Plane(origin=p0, x_dir=u0, z_dir=n0)
            reach = [a0 + height * math.tan(math.radians(beta)) for beta in betas]
            root = self._relief_root(name, *self._sag(host, plane, [(reach[0], 0), (-reach[1], 0)]), height)
            (right, _), (left, _) = half_for(betas[0], root), half_for(betas[1], root)
            face = plane.location * _profile_face(_join(right, left))
            solid = b.revolve(face, b.Axis(tuple(origin), tuple(d)), 360)
        else:
            raise TypeError(f"{name}: a path is a Segment or a Ring")
        result = self._fuse(host, [solid], name)
        _tag(name, [solid])
        return result

    def _fuse(self, host, solids, name):
        self._check_overhang(name, solids, host, cut=False)
        return self._one_solid(host.fuse(*solids).clean(), name)

    @staticmethod
    def _one_solid(result, name):
        solids = result.solids()
        if len(solids) != 1 or not solids[0].is_valid:
            raise PrintLimitError(
                f"{name}: the result is {len(solids)} solid(s); a detail must join its host as "
                f"one valid solid (a detached or overlapping feature)")
        return solids[0]

    def _check_overhang(self, name, shapes, host, cut):
        """Refuse a feature with any new face that looks down past the limit.

        A face on the host's own surface is contact (raised) or mouth (cut),
        not new surface. A cut's faces are read with their normals turned: the
        part's surface there faces into the void.
        """
        import numpy as np
        b = _b3d()
        surface = b.Compound(host.faces())
        limit = self.overhang_angle - _VERIFY_MARGIN
        up = np.array(tuple(self.up))
        worst, steep_area = 0.0, 0.0
        for shape in shapes:
            region = (shape & host) if cut else (shape - host)
            for face in region.faces():
                if all(surface.distance_to(face.position_at(u, v)) < 1e-4
                       for u, v in ((0.5, 0.5), (0.2, 0.2), (0.8, 0.8), (0.2, 0.8), (0.8, 0.2))):
                    continue
                vertices, triangles = face.tessellate(*_TESSELLATION)
                if not triangles:
                    continue
                v = np.array([tuple(p) for p in vertices])
                t = np.array(triangles)
                normals = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
                lengths = np.linalg.norm(normals, axis=1)
                keep = lengths > 1e-12
                normals = normals[keep] / lengths[keep, None]
                if cut:
                    normals = -normals
                if len(normals):
                    down = np.degrees(np.arcsin(np.clip(-(normals @ up), -1, 1)))
                    steep = down > limit
                    steep_area += float(lengths[keep][steep].sum()) / 2
                    if steep.any():
                        worst = max(worst, float(down[steep].max()))
        if steep_area > _TRACE_AREA:
            raise PrintLimitError(
                f"{name}: {steep_area:.2f} mm2 of it would look down as far as {worst:.1f} deg in the "
                f"print direction, past the {limit:.0f} deg allowed under the {self.overhang_angle:.0f} "
                f"deg gate; place it on a face nearer the print direction or choose a pointed shape "
                f"({WIKI}{OVERHANG_PAGE})")


# -------------------------------------------------------------- self-check ---

def _cad_scripts():
    from pathlib import Path
    return Path(__file__).resolve().parents[2] / "cad" / "scripts"


def install(project) -> str:
    """Copy this library into `project/features/print_details.py`, so a part
    entry imports it from inside the sealed CAD project. Returns its sha256.
    An existing copy with other bytes is refused: the copy is never edited."""
    import hashlib
    from pathlib import Path
    source = Path(__file__).resolve()
    data = source.read_bytes()
    project = Path(project)
    if not project.is_dir():
        raise SystemExit(f"{project}: not a CAD project directory")
    target = project / "features" / "print_details.py"
    if target.exists() and target.read_bytes() != data:
        raise SystemExit(f"{target}: exists with other bytes; the library is copied, never edited")
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


# Each case: (name, host, call). `host` is a build123d expression standing on
# the bed; `call` uses `pd` and `host` and the sizes in `S`. Sizes are given
# at the minimum the limits allow and at the defaults.
_HOSTS = {
    "block": "Pos(0, 0, 6) * Box(24, 24, 12)",
    "drum": "Pos(0, 0, 8) * Cylinder(10, 16)",
    "tray": "Pos(0, 0, 7) * Box(24, 24, 14) - Pos(0, 0, 9) * Box(20, 20, 14)",
    # a wing tip printed flat: a 30 mm chisel whose knife edge lies on the bed
    "chisel": "extrude(Plane.XZ * Polygon((0, 0), (30, 0), (30, 3), align=None), 10, both=True)",
    # a spike on a post, pointing up
    "spike": "Pos(0, 0, 2) * Cylinder(4, 4) + Pos(0, 0, 10) * Cone(4, 0, 12)",
    # a pointed vault: 50 deg flanks to a knife ridge at VAULT
    "vault": "extrude(Plane.XZ * Polygon((-5, 0), (5, 0), (5, 4), (0, VAULT), (-5, 4), align=None), 10, both=True)",
}
_TOP, _WALL = "(0, 0, 12)", "(0, -12, 6)"
_CASES = (
    ("boss-top", "block", "pd.boss(host, %s, **S)" % _TOP, {"min": "d=MF, h=MH", "default": ""}),
    ("boss-wall", "block", "pd.boss(host, %s, **S)" % _WALL, {"min": "d=MF, h=MH", "default": ""}),
    ("rivet-top", "block", "pd.rivet(host, %s, **S)" % _TOP, {"min": "d=MF, h=MH", "default": ""}),
    ("rivet-wall", "block", "pd.rivet(host, %s, **S)" % _WALL, {"min": "d=MF, h=MH", "default": ""}),
    ("rivet-ring", "drum", "pd.rivets(host, pd.around(Axis.Z, 10, 12, z=8), **S)",
     {"min": "d=MF, h=MH", "default": ""}),
    ("dome-top", "block", "pd.dome(host, %s, **S)" % _TOP, {"min": "d=MF, h=MH", "default": ""}),
    ("dome-wall", "block", "pd.dome(host, %s, **S)" % _WALL, {"min": "d=3.0, h=MH", "default": ""}),
    ("band-top", "block", "pd.band(host, pd.segment((-8, 0, 12), (8, 0, 12)), **S)",
     {"min": "width=MRW, height=MH", "default": ""}),
    ("band-wall-level", "block", "pd.band(host, pd.segment((-8, -12, 6), (8, -12, 6)), **S)",
     {"min": "width=MRW, height=MH", "default": ""}),
    ("band-wall-rising", "block", "pd.band(host, pd.segment((-4, -12, 2), (4, -12, 10)), **S)",
     {"min": "width=MRW, height=MH", "default": ""}),
    ("band-ring", "drum", "pd.band(host, pd.ring(Axis((0, 0, 8), (0, 0, 1)), 10), **S)",
     {"min": "width=MRW, height=MH", "default": ""}),
    ("rim", "drum", "pd.rim(host, Axis((0, 0, 16), (0, 0, 1)), 7, **S)",
     {"min": "width=MRW, height=MH", "default": ""}),
    ("pipe-wall-level", "block", "pd.pipe(host, pd.segment((-8, -12, 6), (8, -12, 6)), **S)",
     {"min": "d=max(MRW, 2 * MH)", "default": ""}),
    ("pipe-ring", "drum", "pd.pipe(host, pd.ring(Axis((0, 0, 5), (0, 0, 1)), 10), **S)",
     {"min": "d=max(MRW, 2 * MH)", "default": ""}),
    ("panel-top", "block", "pd.panel(host, %s, **S)" % _TOP, {"min": "width=MCW, height=MCW, depth=MCD", "default": ""}),
    ("panel-wall", "block", "pd.panel(host, %s, **S)" % _WALL, {"min": "width=MCW, height=MCW, depth=MCD", "default": ""}),
    ("panel-lancet-wall", "block", "pd.panel(host, %s, arch='lancet', **S)" % _WALL,
     {"min": "width=MCW, height=2 * MCW, depth=MCD", "default": ""}),
    ("window-wall", "tray", "pd.window(host, (0, -12, 8), **S)", {"min": "width=MCW, height=2 * MCW", "default": ""}),
    ("window-floor", "tray", "pd.window(host, (0, 0, 2), arch='flat', **S)",
     {"min": "width=MCW, height=MCW", "default": ""}),
    ("grille-wall", "block", "pd.slits(host, pd.along((-6, -12, 6), (6, -12, 6), 5), **S)",
     {"min": "width=MCW, length=4 * MCW, depth=MCD", "default": ""}),
    ("slits-level-wall", "block", "pd.slits(host, pd.along((0, -12, 3), (0, -12, 8), 2), angle=90, **S)",
     {"min": "width=MCW, length=4 * MCW, depth=MCD", "default": ""}),
    ("slit-through-wall", "tray", "pd.slit(host, (0, -12, 8), through=True, depth=2.0, **S)",
     {"min": "width=MCW, length=4 * MCW", "default": ""}),
    ("bore-wall", "tray", "pd.bore(host, (0, -12, 8), **S)", {"min": "d=MCW", "default": ""}),
    ("bore-blind-wall", "block", "pd.bore(host, %s, depth=3, through=False, **S)" % _WALL,
     {"min": "d=MCW", "default": ""}),
    ("blunt-chisel", "chisel", "pd.blunt_tip(host, (0, 0, 0), (-1, 0, 0), reach=12)", {"default": ""}),
    ("blunt-spike", "spike", "pd.blunt_tip(host, (0, 0, 16), (0, 0, 1))", {"default": ""}),
    ("blunt-vault", "vault", "pd.blunt_tip(host, (0, 0, VAULT), (0, 0, 1), reach=12)", {"default": ""}),
    ("bore-vault", "vault",
     "pd.bore(pd.blunt_tip(host, (0, 0, VAULT), (0, 0, 1), reach=12), (0, -10, 3.5), depth=20, **S)",
     {"min": "d=MCW", "default": ""}),
    # an offset rib whose trim ran out in a sliver, ended square and ramped
    # where it runs down a wall
    ("rib-end-wall", "block",
     "host + pd.rib_end(Pos(0, -12.6, 6) * Box(2, 1.2, 10) - Pos(0, -12.6, 1) * Rot(30, 0, 0) * Box(4, 6, 2), "
     "(0, -12.6, 3), (0, 0, -1))", {"default": ""}),
)


def _entry(nozzle, overhang_angle, host, call, sizes):
    return f"""import math

from build123d import *
from features import print_details

pd = print_details.Details(nozzle={nozzle!r}, overhang_angle={overhang_angle!r})
MF, MH = pd.limit("min_feature"), pd.limit("min_relief_height")
MRW, MCW, MCD = pd.limit("min_relief_width"), pd.limit("min_cut_width"), pd.limit("min_cut_depth")
VAULT = 4 + 5 * math.tan(math.radians(50))


def gen_step():
    host = {_HOSTS[host]}
    S = dict({sizes})
    return {call}
"""


def _refusals(pd):
    """Every size below a limit is refused, naming the limit and its page."""
    b = _b3d()
    host = b.Pos(0, 0, 6) * b.Box(24, 24, 12)
    top = (0, 0, 12)
    eps = 0.01
    probes = (
        ("rivet", lambda: pd.rivet(host, top, d=pd.limit("min_feature") - eps), "min feature", FEATURE_PAGE),
        ("boss", lambda: pd.boss(host, top, h=pd.limit("min_relief_height") - eps), "min relief height", FEATURE_PAGE),
        ("dome", lambda: pd.dome(host, top, d=pd.limit("min_feature") - eps, h=0.6), "min feature", FEATURE_PAGE),
        ("band", lambda: pd.band(host, pd.segment((-5, 0, 12), (5, 0, 12)),
                                 width=pd.limit("min_relief_width") - eps), "min relief width", FEATURE_PAGE),
        ("pipe", lambda: pd.pipe(host, pd.segment((-5, 0, 12), (5, 0, 12)),
                                 d=pd.limit("min_relief_width") - eps), "min relief width", FEATURE_PAGE),
        ("slit", lambda: pd.slit(host, top, width=pd.limit("min_cut_width") - eps), "min cut width", FEATURE_PAGE),
        ("panel", lambda: pd.panel(host, top, depth=pd.limit("min_cut_depth") - eps), "min cut depth", FEATURE_PAGE),
        ("grille", lambda: pd.slits(host, pd.along((-2, 0, 12), (2, 0, 12), 3), width=1.2),
         "min web", WALL_PAGE),
        ("rivets", lambda: pd.rivets(host, pd.along((-2, 0, 12), (2, 0, 12), 3), d=2.0, h=0.6),
         "min cut width", FEATURE_PAGE),
        ("bore", lambda: pd.bore(host, top, d=pd.limit("min_cut_width") - eps), "min cut width", FEATURE_PAGE),
        ("rib end", lambda: pd.rib_end(b.Box(10, pd.limit("min_wall") - eps, 2), (3, 0, 0), (1, 0, 0)),
         "min wall", WALL_PAGE),
        ("hanging tip", lambda: pd.blunt_tip(host + b.Pos(0, 0, 30) * b.Cone(0, 3, 8), (0, 0, 26), (0, 0, -1)),
         "face down", OVERHANG_PAGE),
    )
    failures = []
    for name, probe, limit, page in probes:
        try:
            probe()
        except PrintLimitError as error:
            if limit not in str(error) or page not in str(error):
                failures.append(f"{name}: refused without naming {limit} and {page}: {error}")
        else:
            failures.append(f"{name}: a size below its {limit} was accepted")
    return failures


def _run_gate(command, cwd, timeout):
    import subprocess
    try:
        done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 1, "timed out"
    tail = [line for line in done.stdout.splitlines() if line.strip().startswith(("FAIL", "RESULT"))]
    return done.returncode, " | ".join(tail) or (done.stderr.strip().splitlines() or ["no output"])[-1]


def self_check(nozzle=0.4, overhang_angle=45.0, jobs=None, keep=None, only=None) -> int:
    import os
    import sys
    import tempfile
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path

    failures = _refusals(Details(nozzle=nozzle, overhang_angle=overhang_angle))
    for failure in failures:
        print("FAIL  " + failure)
    cad = _cad_scripts()
    if not (cad / "check_thickness").is_file() or not (cad / "check_overhang").is_file():
        print(f"FAIL  the cad skill's print gates are not at {cad}")
        return 1
    temporary = None if keep else tempfile.TemporaryDirectory(prefix="print-details-")
    project = Path(keep or temporary.name)
    project.mkdir(parents=True, exist_ok=True)
    install(project)
    jobs = jobs or max(1, min(8, (os.cpu_count() or 2) // 2))

    def one(case, size):
        name, host, call, sizes = case
        entry = project / f"part_{name}-{size}.step.py"
        entry.write_text(_entry(nozzle, overhang_angle, host, call, sizes[size]), encoding="utf-8")
        results = []
        for gate, extra in (("check_thickness", ["--nozzle", str(nozzle)]),
                            ("check_overhang", ["--angle", str(overhang_angle)])):
            code, detail = _run_gate([sys.executable, str(cad / gate), entry.name, *extra], project, 600)
            results.append((gate, code, detail))
        return f"{name}-{size}", results

    work = [(case, size) for case in _CASES for size in ("min", "default")
            if size in case[3] and (not only or case[0] in only)]
    try:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            for label, results in pool.map(lambda item: one(*item), work):
                for gate, code, detail in results:
                    verdict = "PASS" if code == 0 else "FAIL"
                    print(f"{verdict}  {label:28s} {gate:16s} {detail if code else ''}".rstrip())
                    if code:
                        failures.append(f"{label} {gate}")
    finally:
        if temporary is not None:
            temporary.cleanup()
    total = 2 * len(work)
    if failures:
        print(f"print-details self-check: {len(failures)} failure(s) of {total} gate runs and the limit probes")
        return 1
    print(f"print-details self-check: all {len(work)} features pass both print gates, and every limit refuses")
    return 0


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Printable decorative detail for Component Workers.")
    parser.add_argument("--nozzle", type=float, default=0.4, help="mm (default 0.4)")
    parser.add_argument("--overhang-angle", type=float, default=45.0, help="deg (default 45)")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--limits", action="store_true", help="print every limit with its wiki page")
    action.add_argument("--install", metavar="CAD_PROJECT",
                        help="copy the library to CAD_PROJECT/features/print_details.py")
    action.add_argument("--self-check", action="store_true",
                        help="build every feature and run the real print gates on it")
    parser.add_argument("--jobs", type=int, default=None, help="self-check: parallel entries")
    parser.add_argument("--keep", default=None, help="self-check: build the entries in this directory")
    parser.add_argument("--only", action="append", default=None, help="self-check: one case by name")
    args = parser.parse_args(argv)
    if args.limits:
        for name, (value, unit, page, why) in limits(args.nozzle, args.overhang_angle).items():
            print(f"{name:18s} {value:6.2f} {unit:3s}  {why}  ({WIKI}{page})")
        return 0
    if args.install:
        digest = install(args.install)
        print(f"installed features/print_details.py sha256 {digest}")
        return 0
    return self_check(args.nozzle, args.overhang_angle, args.jobs, args.keep, args.only)


if __name__ == "__main__":
    raise SystemExit(main())
