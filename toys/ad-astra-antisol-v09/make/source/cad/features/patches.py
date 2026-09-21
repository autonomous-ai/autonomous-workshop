"""Surface-colour patches on a globe.

Every marking in this set is a flush colour inlay: the region is a different
filament through the outer millimetre or so of the ball, so the globe's outer
surface stays a true sphere and nothing a marking adds can face downward.

A region tool is therefore a solid that meets the sphere in the outline the
marking wants and reaches only a controlled depth below it.  There are two
ways of drawing that outline here, and the choice is about what the marking
IS rather than about how hard it is to build.

A round patch, or a union of them, is drawn with `spot_tool`: a ball resting
against the globe.  That is the honest shape for an albedo map, a cloud
pattern or a storm, because a blob union is what Mercury's plains, Venus's
cloud Y and Neptune's dark spot actually are.

A coastline is drawn with `outline_tool`: a radial cone through a closed
lon/lat ring.  Earth is the one world in this set whose real surface has an
outline a player already knows by heart, and a blob union throws that
recognition away.

The circle tools share one piece of arithmetic.  Given a chord half-width
``q = R sin a`` and a wanted depth ``p``, a circle of radius

    rb = (q**2 + d**2) / (2 d)      with d = p - R (1 - cos a)

meets the sphere at exactly ``a`` degrees from its own axis and dips exactly
``p`` below the surface.  Small ``a`` gives a small ball; large ``a`` gives a
big, shallow one.  That is what lets a 33-degree albedo patch be one solid and
still be 1.2 mm deep instead of half the planet.

All tools are built in the planet's own frame: +Z is the planet's north pole,
the equator is Z = 0, longitude 0 faces +X.  `planet_frame` carries that frame
into the piece.
"""

from __future__ import annotations

import math

from build123d import (
    Align,
    Cone,
    Location,
    Plane,
    Polygon,
    Pos,
    Rot,
    Sphere,
    Torus,
    loft,
)


def planet_frame(tilt_deg: float, sign: float, centre_z: float) -> Location:
    """Planet frame -> piece frame.

    The globe is rotated about +Y by its true obliquity; `sign` is +1 for a Sol
    world (north pole toward +X) and -1 for its Anti-Sol mirror.
    """
    return Location((0, 0, centre_z)) * Rot(0, sign * tilt_deg, 0)


#: The least a tool may dip below the chord it cuts.  Squeeze this toward zero
#: and the tool grows without bound -- a 33-degree patch at 0.09 mm of extra
#: depth wants a ball of radius 77 mm to cut a globe of radius 6.9, and a
#: cutting surface that flat is where this kernel starts returning wrong
#: answers.  Holding it at 0.45 keeps every tool within a few globe radii.
MIN_TOOL_BITE = 0.45
MAX_PATCH_DEG = 24.0


def cap_circle(radius: float, angular_radius_deg: float, depth: float):
    """(tube radius, centre distance) of the circle that cuts `depth` deep."""
    half = math.radians(min(max(angular_radius_deg, 0.6), MAX_PATCH_DEG))
    chord = radius * math.sin(half)
    sagitta = radius * (1.0 - math.cos(half))
    extra = max(depth - sagitta, MIN_TOOL_BITE)
    tube = (chord * chord + extra * extra) / (2.0 * extra)
    reach = radius * math.cos(half) + math.sqrt(max(tube * tube - chord * chord, 0.0))
    return tube, reach


def spot_tool(radius: float, lat_deg: float, lon_deg: float, angular_radius_deg: float,
              depth: float):
    """A round patch centred on one latitude and longitude.

    A ball resting against the globe, sized so it meets the surface at the
    asked-for angular radius and reaches `depth` below it.  Balls rather than
    cones: a marking is usually several overlapping blobs, and a dozen cones
    all sharing one apex at the globe centre is a boolean the kernel answers
    wrongly rather than slowly.
    """
    tube, reach = cap_circle(radius, angular_radius_deg, depth)
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    centre = (
        reach * math.cos(lat) * math.cos(lon),
        reach * math.cos(lat) * math.sin(lon),
        reach * math.sin(lat),
    )
    # A revolved primitive carries a seam at its own local +X, and a sphere
    # used as a cutting tool whose seam ends up INSIDE the remaining material
    # returns an invalid solid -- measured here as a 49 mm3 blob removing
    # 45.7 mm3 where the true lens is 21.5.  Turn the seam radially outward,
    # where it leaves the part.
    return (
        Pos(*centre)
        * Rot(0, 0, lon_deg)
        * Rot(0, -lat_deg, 0)
        * Sphere(tube)
    )


def latitude_band_tool(radius: float, lat_low_deg: float, lat_high_deg: float,
                       depth: float):
    """A belt of latitude: the same circle as a spot, swept round the pole."""
    if lat_high_deg <= lat_low_deg:
        raise ValueError("a latitude band runs south to north")
    middle = 0.5 * (lat_low_deg + lat_high_deg)
    half = 0.5 * (lat_high_deg - lat_low_deg)
    tube, reach = cap_circle(radius, half, depth)
    major = reach * math.cos(math.radians(middle))
    if major <= tube * 1.02:
        return spot_tool(radius, 90.0 if middle > 0 else -90.0, 0.0, half, depth)
    return Pos(0, 0, reach * math.sin(math.radians(middle))) * Torus(major, tube)


def latitude_shell_tool(radius: float, lat_low_deg: float, lat_high_deg: float,
                        depth: float, solid: bool = False):
    """A belt of latitude at one CONSTANT depth, not a tapering lens.

    `latitude_band_tool` draws a circle that meets the sphere at the band's two
    edges and dips `depth` below the surface at its middle, so the lens it cuts
    is thickest in the middle and vanishes at the edges.  That is the right
    shape for a band that is drawn where it is shown -- Saturn's belts,
    Neptune's streaks -- and it is the wrong shape for a band that is drawn
    wider than it is shown and trimmed by a neighbour.  Two things go wrong.
    The trimmed edge lands where the lens has whatever depth it happens to
    have, which can be a fraction of a layer; and where the trim line falls
    near the tool's own middle, its floor osculates the sphere at
    ``radius - depth`` -- which is exactly the floor every outline lens has --
    and the two coincident surfaces leave a spline sliver with no area to
    triangulate.  Measured on Jupiter: a 0.0016 mm2 face on the North
    Equatorial Belt's northern boundary that took the whole set's renderer down
    with a null triangulation.

    This tool has no middle.  It is the frustum swept by the radial lines
    through the two parallels, hollowed by the depth sphere, so it reaches
    exactly `depth` at every latitude in the band and its floor IS the sphere
    the outline lenses stop at.  Two markings that share a boundary therefore
    share one surface rather than two descriptions of it.

    `solid` returns the whole frustum instead of the shell slice, the same way
    `outline_tool` does, for a sibling that has to subtract this one.
    """
    from build123d import Axis, revolve

    if lat_high_deg <= lat_low_deg:
        raise ValueError("a latitude shell runs south to north")
    inner = (radius - depth) * _OUTLINE_IN
    outer = radius * _OUTLINE_OUT
    low = math.radians(lat_low_deg)
    high = math.radians(lat_high_deg)
    profile = [
        (inner * math.cos(low), inner * math.sin(low)),
        (outer * math.cos(low), outer * math.sin(low)),
        (outer * math.cos(high), outer * math.sin(high)),
        (inner * math.cos(high), inner * math.sin(high)),
    ]
    frustum = revolve(Plane.XZ * Polygon(*profile, align=None), Axis.Z)
    if solid:
        return frustum
    return frustum - Sphere(radius - depth)


def blob_tool(radius: float, blobs, depth: float):
    """A union of round patches -- how every irregular marking here is drawn."""
    tools = [spot_tool(radius, lat, lon, ang, depth) for lat, lon, ang in blobs]
    return tools[0] if len(tools) == 1 else tools[0] + tools[1:]


# ------------------------------------------------------------- outlines ---
#: How far outside the globe an outline tool's outer section plane sits, and
#: how far inside the depth surface its inner one does, as fractions.  Both
#: are only margins: the section planes must clear the two spheres the shell
#: arithmetic trims against, and nothing else about them is visible.
_OUTLINE_OUT = 1.05
_OUTLINE_IN = 0.95

#: How close to the horizon a ring vertex may sit, measured from the ring's
#: own axis.  A vertex at 90 degrees has a radial line parallel to the section
#: planes and no crossing point at all; this is where the construction stops
#: being well conditioned.  Asia, the widest ring in Earth's atlas, reaches
#: 50 degrees.
_OUTLINE_MAX_HALF = 72.0


def direction(lon_deg: float, lat_deg: float) -> tuple[float, float, float]:
    """The unit vector of one longitude and latitude in the planet's frame."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    return (
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat),
    )


def _dot(one, other):
    return one[0] * other[0] + one[1] * other[1] + one[2] * other[2]


def _cross(one, other):
    return (
        one[1] * other[2] - one[2] * other[1],
        one[2] * other[0] - one[0] * other[2],
        one[0] * other[1] - one[1] * other[0],
    )


def _norm(vector):
    length = math.sqrt(_dot(vector, vector))
    if length < 1e-12:
        raise ValueError("a ring whose vertices average to nothing has no axis")
    return (vector[0] / length, vector[1] / length, vector[2] / length)


def _ring_axis(directions):
    """The direction the ring surrounds: the mean of its own vertices."""
    total = (
        sum(item[0] for item in directions),
        sum(item[1] for item in directions),
        sum(item[2] for item in directions),
    )
    return _norm(total)


def _widen(vector, axis, delta_deg: float):
    """The same direction, tilted `delta_deg` further from `axis`."""
    if abs(delta_deg) < 1e-9:
        return vector
    along = _dot(vector, axis)
    across = (
        vector[0] - along * axis[0],
        vector[1] - along * axis[1],
        vector[2] - along * axis[2],
    )
    if _dot(across, across) < 1e-18:
        return vector
    across = _norm(across)
    angle = math.acos(max(-1.0, min(1.0, along))) + math.radians(delta_deg)
    angle = max(0.0, min(math.radians(_OUTLINE_MAX_HALF), angle))
    return tuple(
        math.cos(angle) * axis[index] + math.sin(angle) * across[index]
        for index in range(3)
    )


def _radial_prism(radius: float, ring, depth: float, widen: float):
    """The solid swept by the radial lines through one closed ring.

    Two planar sections, both square to the ring's own axis: one placed well
    inside the depth surface, one well outside the globe.  Each ring vertex
    contributes the point where its radial line crosses that plane, and the
    two polygons are lofted ruled.  Because both of a vertex's points lie on
    the same radial line, each side of the loft is the plane through the globe
    centre and one ring edge -- so the lateral surface IS the radial cone
    through the ring, and the shell arithmetic below can trim it to depth
    without the tool leaning anywhere.
    """
    directions = [direction(lon, lat) for lon, lat in ring]
    if len(directions) < 3:
        raise ValueError("an outline ring needs at least three vertices")
    axis = _ring_axis(directions)
    directions = [_widen(item, axis, widen) for item in directions]
    cosines = [_dot(item, axis) for item in directions]
    least = min(cosines)
    if least <= math.cos(math.radians(_OUTLINE_MAX_HALF)):
        raise ValueError(
            "an outline ring reaches %.1f degrees from its own axis, past the "
            "%.1f degree limit of this construction"
            % (math.degrees(math.acos(max(-1.0, min(1.0, least)))), _OUTLINE_MAX_HALF)
        )
    inner = (radius - depth) * least * _OUTLINE_IN
    outer = radius * _OUTLINE_OUT

    # Any vector square to the axis will do: the two sections are read in the
    # same frame, so the loft cannot twist whichever one is picked.
    seed = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (1.0, 0.0, 0.0)
    x_dir = _norm(_cross(seed, axis))
    y_dir = _cross(axis, x_dir)

    sections = []
    for reach in (inner, outer):
        points = [
            [(reach / cosine) * item[index] for index in range(3)]
            for item, cosine in zip(directions, cosines)
        ]
        flat = [(_dot(point, x_dir), _dot(point, y_dir)) for point in points]
        plane = Plane(
            origin=(reach * axis[0], reach * axis[1], reach * axis[2]),
            x_dir=x_dir,
            z_dir=axis,
        )
        sections.append(plane * Polygon(*flat, align=None))
    return loft(sections, ruled=True)


def outline_tool(radius: float, ring, depth: float, widen: float = 0.0,
                 solid: bool = False):
    """A patch the shape of one closed lon/lat ring, `depth` deep.

    What `spot_tool` is for a circle, this is for a coastline.  `widen` tilts
    every vertex that many degrees further from the ring's own axis, which is
    how the clip loop moves a seam without moving what the eye sees.

    `solid` returns the whole radial cone instead of the shell slice.  That
    form is only ever a cutting tool: a sibling marking subtracts it to stay
    out of this one's way, and a cone has no spherical face to share with the
    lens it is cutting.
    """
    prism = _radial_prism(radius, ring, depth, widen)
    if solid:
        return prism
    return prism - Sphere(radius - depth)


def polar_cap_tool(radius: float, boundary_lat_deg: float, depth: float,
                   widen: float = 0.0, solid: bool = False,
                   pole: str = "north"):
    """The cap above one parallel: the radial cone through that circle.

    A cap encloses the pole, so it has no ring to trace.  Its boundary is the
    parallel itself, and the tool is the cone the globe centre throws through
    it.  `widen` drops the boundary latitude, the same seam-moving nudge the
    rings take.

    `pole` names which pole the cap encloses, and `boundary_lat_deg` is read as
    a distance from THAT pole's own equator-side boundary in both cases: a
    south cap at 55 is everything below latitude -55, the mirror of the north
    cap at +55.  Signing the latitude instead would be ambiguous -- "the cap
    above -55" is most of the globe -- so the pole is named rather than
    inferred.  North is every cap this project wrote before Uranus, whose two
    hoods are the reason the argument exists: the obliquity hides one pole of
    each army at both photographed frames, and a hood on the hidden pole alone
    is a marking no player would ever see.
    """
    if pole not in ("north", "south"):
        raise ValueError("a cap encloses the north or the south pole, not %r" % pole)
    half = math.radians(min(90.0 - boundary_lat_deg + widen, _OUTLINE_MAX_HALF))
    spread = math.tan(half)
    low = (radius - depth) * math.cos(half) * _OUTLINE_IN
    high = radius * _OUTLINE_OUT
    if pole == "north":
        cone = Pos(0, 0, low) * Cone(
            bottom_radius=low * spread,
            top_radius=high * spread,
            height=high - low,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    else:
        # The southern cone is built pointing down rather than built pointing
        # up and turned over, and that is `spot_tool`'s lesson again rather
        # than a preference.  A revolved primitive carries a seam at its own
        # local +X; `Rot(0, 180, 0)` puts the cone's seam at -X while the
        # depth sphere and the globe keep theirs at +X, and the boolean across
        # that disagreement is answered wrongly.  Measured on Uranus's southern
        # hood: the lens came out at the correct 147.93 mm3 either way, and
        # `globe.cut(lens)` came back 3521 mm3 light with the turned cone and
        # exact with this one.  Revolving the cone the other way costs nothing
        # and keeps every seam in the set on the same meridian.
        cone = Pos(0, 0, -high) * Cone(
            bottom_radius=high * spread,
            top_radius=low * spread,
            height=high - low,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    if solid:
        return cone
    return cone - Sphere(radius - depth)
