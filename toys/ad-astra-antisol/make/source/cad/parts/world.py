"""One world: a disc, a numeral, a globe, and the markings that name it.

Each piece is a single printed part in several filaments.  It is built here as
the set of single-colour bodies the shop prints it from, keyed by the role they
play, so the assembly can address and colour each of them and the print gates
can measure the fused whole.

Ownership lives in three places, none of which touches the planet's own
appearance: the direction the globe leans (its true obliquity, mirrored), the
direction the disc's wall drafts, and the disc's colour.
"""

from __future__ import annotations

import math

from build123d import (
    Align,
    Axis,
    Cone,
    Cylinder,
    Location,
    Plane,
    Pos,
    Rectangle,
    Rot,
    Sphere,
    extrude,
    fillet,
    loft,
)

import bool3d as X
import params as P
from features import (
    blob_tool,
    latitude_band_tool,
    planet_frame,
    seven_segment_sketch,
)
from parts.markings import MARKINGS


# ------------------------------------------------------------------- disc ---
def _disc_solid(side: str):
    bottom = (P.DISC_D_BOT_SOL if side == "sol" else P.DISC_D_BOT_ANTI) / 2.0
    top = (P.DISC_D_TOP_SOL if side == "sol" else P.DISC_D_TOP_ANTI) / 2.0
    cone = Cone(
        bottom_radius=bottom,
        top_radius=top,
        height=P.DISC_H,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    top_edge = cone.edges().filter_by(Axis.Z, reverse=True).group_by(Axis.Z)[-1]
    return fillet(top_edge, P.DISC_TOP_ROUND)


def _numeral_tools(planet: str, side: str):
    """The digit prisms, at 0 and 180 degrees, as cutting tools."""
    digit = P.PLANETS[planet]["rank"]
    sketch = seven_segment_sketch(digit, P.NUMERAL_H, P.NUMERAL_W, P.NUMERAL_STROKE)
    reach = P.DISC_NOMINAL_D  # far enough to cross the wall from either side
    # The players sit at -Y and +Y, so the digit faces them.  On the +Y face a
    # seated eye reads sketch +x as world -X and sketch +y as world +Z.
    plane = Plane(origin=(0, 0, P.NUMERAL_Z), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))
    prism = extrude(plane * sketch, reach)
    return [prism, Rot(0, 0, 180.0) * prism]


def _numeral_inlay(disc, planet: str, side: str):
    """The flush colour inlay: the shell the digit pocket takes out of the wall.

    The numeral is an inlay rather than relief because a 0.45 mm raised stroke
    on a 1.00 mm seven-segment glyph cannot be drafted to the overhang gate at
    this size, and because the set's own reference images read the numeral as
    flush colour.  Flush keeps all three rank channels and costs no ledge.
    """
    bottom = (P.DISC_D_BOT_SOL if side == "sol" else P.DISC_D_BOT_ANTI) / 2.0
    top = (P.DISC_D_TOP_SOL if side == "sol" else P.DISC_D_TOP_ANTI) / 2.0
    shrunk = Cone(
        bottom_radius=bottom - P.NUMERAL_DEPTH,
        top_radius=top - P.NUMERAL_DEPTH,
        height=P.DISC_H,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    shell = disc - shrunk
    tools = _numeral_tools(planet, side)
    inlay = shell & (tools[0] + tools[1:])
    return inlay


# ------------------------------------------------------------------ globe ---
def _globe_solid(planet: str):
    radius = P.globe_radius(planet)
    centre = P.globe_centre_z(planet)
    ball = Pos(0, 0, centre) * Sphere(radius)
    seat = Pos(0, 0, P.DISC_H) * Cone(
        bottom_radius=P.seat_land_radius(planet),
        top_radius=P.seat_contact_radius(planet),
        height=P.seat_contact_z(planet) - P.DISC_H,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return ball + seat


def _region_tool(planet: str, spec):
    radius = P.globe_radius(planet)
    depth = P.RELIEF_DEPTH
    kind = spec[0]
    if kind == "blob":
        return blob_tool(radius, spec[1], depth)
    if kind == "band":
        return latitude_band_tool(radius, spec[1], spec[2], depth)
    raise ValueError("unknown region kind %r" % kind)


# The graded widening the clip loop below reaches for, in degrees of arc per
# patch index.  The largest of them puts the sixteenth patch of a marking 1.76
# deg wider than it was drawn, which on the smallest globe in the set is 0.21
# mm of arc -- one layer, and under the 0.4 mm nozzle that would have to print
# the colour boundary.
_CLIP_NUDGES = (0.0, 0.013, 0.031, 0.057, -0.021, 0.083, -0.047, 0.11)


def _region_pieces(planet: str, spec, nudge: float, first: int = 0):
    """One tool per patch, so each can be clipped on its own.

    A `blob` spec is several round patches that overlap.  Fusing them first and
    intersecting the union with the globe's own sphere is what the earlier
    build did, and `inspect validate` measured the result as self-intersecting
    on Mercury, Mars and Venus: the union's outer face IS the globe sphere, and
    a neighbouring patch's tool sphere runs tangent to it along the seam where
    two patches meet.  Clipping each patch separately gives a stack of clean
    lenses whose fuse meets along ordinary edges instead.

    `nudge` widens patch *n* by `n * nudge` degrees rather than widening them
    all equally.  A common widening slides every seam along by the same amount
    and can land a second pair on the tangency it just left; a graded one
    cannot, because no two patches move together.
    """
    radius = P.globe_radius(planet)
    depth = P.RELIEF_DEPTH
    kind = spec[0]
    if kind == "blob":
        return [
            blob_tool(radius, [(lat, lon, ang + nudge * (first + n))], depth)
            for n, (lat, lon, ang) in enumerate(spec[1])
        ]
    return [_region_tool(planet, spec)]


def _marking_raw_union(planet: str):
    """Every marking region of one planet, fused before any of them is sliced.

    This is what actually gets carved out of the globe.  Fusing the plain balls
    and cylinders is well conditioned; fusing the shell slices afterwards is
    not, because neighbouring slices share the band's own spherical faces.
    """
    pieces = []
    for _key, _colour, specs, _subtract in MARKINGS[planet]:
        for spec in specs:
            pieces.append(_region_tool(planet, spec))
    return pieces[0] + pieces[1:] if len(pieces) > 1 else pieces[0]


def _marking_regions(planet: str, nudge: float = 0.0):
    """key -> region solid in the planet's own frame, disjoint from its peers.

    Regions are made disjoint HERE, while they are still plain balls and
    cylinders.  Two shell slices carved out of the same band share that band's
    two spherical faces, and a boolean between coincident faces is the one the
    kernel answers wrongly rather than slowly -- which is how a marking, or a
    whole globe, silently disappears.
    """
    raw = {}
    for key, _colour, specs, _subtract in MARKINGS[planet]:
        pieces = [_region_tool(planet, spec) for spec in specs]
        raw[key] = pieces[0] + pieces[1:] if len(pieces) > 1 else pieces[0]

    # Every region is clipped to the globe's own sphere before it cuts
    # anything.  Left unclipped a marking also selects the seat cone the globe
    # stands on -- measured at 40% of Neptune's dark spot and 41% of Earth's
    # dryland -- and a continent that runs down onto the mounting collar breaks
    # the planet's silhouette exactly where it should be cleanest.
    #
    # The clip is done one patch at a time and the lenses fused afterwards.
    # Subtracting a sibling region commutes with the clip -- (A n B) - C is
    # (A - C) n B -- so the order here keeps the documented meaning while
    # giving the kernel only well conditioned operands.  The result is then
    # measured, not assumed: if the fuse still crosses itself the whole
    # marking is widened by a fraction of a degree and the clip retried, which
    # moves every seam off the tangency without moving what the eye sees.
    ball = Sphere(P.globe_radius(planet))
    regions = {}
    for key, _colour, specs, subtract in MARKINGS[planet]:
        lenses = []
        first = 0
        for spec in specs:
            pieces = _region_pieces(planet, spec, nudge, first)
            first += len(pieces)
            for tool in pieces:
                lens = _sane(X.shape(X.meet(tool, ball)))
                if lens is not None:
                    lenses.append(lens)
        if not lenses:
            continue
        region = lenses[0] + lenses[1:] if len(lenses) > 1 else lenses[0]
        for other in subtract:
            region = region - raw[other]
        region = _sane(region)
        if region is not None:
            regions[key] = region
    return regions


# --------------------------------------------------------- Saturn's rings ---
def _ring_plate(planet: str):
    radius = P.globe_radius(planet)
    inner = radius - P.RING_GLOBE_BITE
    outer = P.RING_OUTER_D / 2.0
    plate = Cylinder(
        radius=outer, height=P.RING_THICKNESS, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    )
    bore = Cylinder(
        radius=inner, height=P.RING_THICKNESS * 3.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return plate - bore


def _web_section(azimuth: float, base: float, plane_a: float, plane_b: float,
                 inner_rho: float, rho_out: float, slope: float, lift: float):
    """One radial cross-section of the web, in the vertical plane at `azimuth`.

    Bounded below by the 47-degree cone from the ring's lower outer rim and
    above by the ring's own bottom plane; both are straight lines in this
    plane, so the section is a quadrilateral.  Returns None where the two
    bounds have already crossed.
    """
    gap = slope - plane_b
    if gap <= 1e-6:
        return None
    rho_end = min(rho_out, (plane_a + lift - base) / gap)
    if rho_end <= inner_rho + 0.05:
        return None
    top_inner = plane_a + lift + plane_b * inner_rho
    if top_inner - (base + slope * inner_rho) <= 1e-6:
        return None
    radial = (math.cos(math.radians(azimuth)), math.sin(math.radians(azimuth)), 0.0)
    normal = (math.sin(math.radians(azimuth)), -math.cos(math.radians(azimuth)), 0.0)
    plane = Plane(origin=(0, 0, 0), x_dir=radial, z_dir=normal)
    profile = [
        (inner_rho, base + slope * inner_rho),
        (rho_end, base + slope * rho_end),
        (rho_end, plane_a + lift + plane_b * rho_end),
        (inner_rho, top_inner),
    ]
    return plane * _polygon_sketch(profile)


def _ring_web(planet: str, sign: float):
    """Solid fill under the ring, bounded below by a 47-degree cone.

    A flat annulus tilted at Saturn's obliquity presents an underside the
    printer cannot hold, so the volume between that underside and the first
    thing below it is filled, and the fill's own outer surface is held steeper
    than the overhang gate.  The fill is deepest at the ring's low azimuth,
    where it runs down to the disc, and thins to a fraction of a millimetre at
    the high azimuth, where the globe already carries the ring.

    Each sector is a ruled loft between the exact sections at its own two
    azimuths, so neighbouring sectors share a section and the underside comes
    out smooth.  Built as revolved sectors instead -- one constant profile per
    sector -- the same web renders as a visible spiral staircase.
    """
    centre_z = P.globe_centre_z(planet)
    outer = P.RING_OUTER_D / 2.0
    tilt = math.radians(sign * P.PLANETS[planet]["tilt"])
    half_t = P.RING_THICKNESS / 2.0
    slope = P.RING_WEB_SLOPE
    inner_rho = P.RING_WEB_INNER_R
    lift = P.RING_WEB_OVERLAP
    plane_a = centre_z - half_t / math.cos(tilt)

    def at(psi: float):
        """(azimuth deg, plan radius, height) of the ring's lower outer rim."""
        px, py, pz = outer * math.cos(psi), outer * math.sin(psi), -half_t
        x = px * math.cos(tilt) + pz * math.sin(tilt)
        z = centre_z - px * math.sin(tilt) + pz * math.cos(tilt)
        return math.degrees(math.atan2(py, x)), math.hypot(x, py), z

    count = P.RING_WEB_SECTORS
    rims = [at(2.0 * math.pi * index / count) for index in range(count + 1)]
    sections = []
    for azimuth, rho, height in rims:
        sections.append(
            _web_section(
                azimuth,
                height - slope * rho - P.RING_WEB_DROP,
                plane_a,
                -math.cos(math.radians(azimuth)) * math.tan(tilt),
                inner_rho,
                rho,
                slope,
                lift,
            )
        )

    sectors = []
    for index in range(count):
        first, second = sections[index], sections[index + 1]
        if first is None or second is None:
            continue
        sectors.append(loft([first, second], ruled=True))
    if not sectors:
        return None
    return sectors[0] + sectors[1:]


def _polygon_sketch(points):
    from build123d import Polygon

    return Polygon(*points, align=None)


def _ring_body(planet: str, sign: float, globe, disc):
    """Saturn's ring and its web, as the one white body they print as."""
    if planet != "saturn":
        return None
    frame = planet_frame(P.PLANETS[planet]["tilt"], sign, P.globe_centre_z(planet))
    plate = frame * _ring_plate(planet)
    web = _ring_web(planet, sign)
    body = plate if web is None else plate + web
    body = body - globe - disc
    return body - Pos(0, 0, P.DISC_H) * Cylinder(
        radius=P.DISC_NOMINAL_D, height=P.DISC_H * 4.0,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )


# ------------------------------------------------------------------ piece ---
def world_bodies(planet: str, side: str) -> dict[str, tuple[str, object]]:
    """role -> (filament, solid) for one world, in print orientation.

    Bed datum Z = 0 is the disc's bed face.  Returned bodies are disjoint: they
    share surfaces and never overlap, so the assembly can address them
    separately and the fused whole is one printed part.
    """
    sign = P.lean_sign(side)
    radius = P.globe_radius(planet)
    centre_z = P.globe_centre_z(planet)
    frame = planet_frame(P.PLANETS[planet]["tilt"], sign, centre_z)

    disc = _disc_solid(side)
    inlay = _numeral_inlay(disc, planet, side)
    disc = disc - inlay

    # The ball is sunk two millimetres into the disc, so the two bodies would
    # otherwise occupy the same 78 mm3 -- a clash the assembly check would
    # report and the shop would print twice.  The disc owns that volume.
    # Cut at the disc's top face rather than with the disc itself: below Z =
    # DISC_H the ball is entirely inside the disc's own footprint, so the
    # answer is the same and the tool is a plain cylinder instead of a
    # filleted cone with two lettering pockets in its wall.
    under_disc = Pos(0, 0, P.DISC_H) * Cylinder(
        radius=P.DISC_NOMINAL_D, height=P.DISC_H * 4.0,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )
    globe = X.shape(X.cut(_globe_solid(planet), under_disc))

    bodies: dict[str, tuple[str, object]] = {}
    ring_body = _ring_body(planet, sign, globe, disc)

    # Markings are colour inlays in the globe's own sphere: the outer surface
    # stays a true sphere and nothing a marking adds can face downward.  Every
    # region tool is a ball or a torus sized to reach exactly RELIEF_DEPTH
    # below the surface, so the patch IS the whole lens -- no shell to clip and
    # no core to weld back on.
    #
    # The globe is partitioned by splitting it once per marking and carrying
    # the remainder forward.  Computing the patches and the bare globe as two
    # independent boolean runs lets them disagree; taking both halves of one
    # split cannot.
    # The accept test is applied to the bodies this returns, not to the region
    # tools that made them: a region that does not cross itself can still hand
    # back a patch or a remainder that does, because the split introduces the
    # globe's own sphere as a second face of each half.  `inspect validate`
    # asks the question of the bodies, so this asks it of the bodies too, and
    # widens the patches by a graded fraction of a degree until the answer is
    # no.  Nothing here is accepted on the strength of a proxy.
    before_markings = X.volume(globe)
    whole = globe
    accepted = None
    faults: list[str] = []
    for nudge in _CLIP_NUDGES:
        regions = _marking_regions(planet, nudge)
        remaining = [whole]
        patches = {}
        for key, colour, _specs, _subtract in MARKINGS[planet]:
            if key not in regions:
                continue
            inside, remaining = X.split(remaining, frame * regions[key])
            patch = X.shape(inside)
            if patch is not None:
                patches[key] = (colour, patch)
        rest = X.shape(remaining)
        if rest is None:
            raise RuntimeError(
                "%s %s: the markings consumed the whole globe" % (planet, side)
            )
        # Coverage is the first question and it is fatal for this nudge, not
        # for the build: a widening that makes the kernel drop material is
        # simply the wrong widening, so it is rejected the same way a crossing
        # body is and the next one is tried.
        split_total = X.volume(rest) + sum(X.volume(s) for _c, s in patches.values())
        if abs(split_total - before_markings) > max(0.002 * before_markings, 0.3):
            faults.append(
                "nudge %+.3f lost material (%.2f of %.2f)"
                % (nudge, split_total, before_markings)
            )
            continue
        crossing = [
            key
            for key, (_c, body) in list(patches.items()) + [("globe", (None, rest))]
            if X.self_intersecting(body) is not False
        ]
        if not crossing:
            accepted = (rest, patches)
            break
        faults.append("nudge %+.3f still crossing: %s" % (nudge, ", ".join(crossing)))
    if accepted is None:
        raise RuntimeError(
            "%s %s: no clip nudge produced a sound colour split -- %s"
            % (planet, side, "; ".join(faults))
        )
    globe, patches = accepted

    bodies["disc"] = (P.DISC_COLOUR[side], disc)
    bodies["numeral"] = (P.NUMERAL_COLOUR[side], inlay)
    bodies["globe"] = (P.GLOBE_COLOUR[planet], globe)
    for key, (colour, patch) in patches.items():
        bodies[key] = (colour, patch)
    if ring_body is not None:
        bodies["ring"] = ("white", ring_body)
    return bodies


def _sane(shape):
    """Drop a boolean result that is empty, degenerate, or too small to print.

    A near-tangent intersection can succeed and return a sliver whose volume is
    a rounding error; subtracting one of those from the globe is how a whole
    sphere quietly disappears.  Nothing under a fifth of a nozzle-width cube is
    a marking anybody could print, so it is not one.
    """
    if shape is None:
        return None
    if not shape.solids():
        return None
    if shape.volume <= 0.05:
        return None
    return shape


def build_world(planet: str, side: str):
    """The whole printed part: what the print gates measure.

    Built from the disc and the ball directly rather than by fusing the colour
    bodies back together.  The two paths describe the same solid, and this one
    is three booleans instead of fifteen -- welding fifteen lens-shaped pieces
    onto a sphere along their own curved faces is where the kernel starts
    returning bodies that are 400 mm3 too large and then 1800 mm3 too small.
    `world_bodies` proves the colour split covers this same volume exactly.
    """
    disc = _disc_solid(side)
    globe = _globe_solid(planet)
    body = X.union(disc, globe)
    ring = _ring_body(planet, P.lean_sign(side), globe, disc)
    if ring is not None:
        body = X.union(body, ring)
    solids = X.parts(body)
    if len(solids) != 1:
        raise RuntimeError(
            "%s %s: the printed part came out as %d solids" % (planet, side, len(solids))
        )
    body = solids[0]
    body.label = "world_%s_%s" % (planet, side)
    return body
