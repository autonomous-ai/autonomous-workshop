"""Surface-colour patches on a globe.

Every marking in this set is a flush colour inlay: the region is a different
filament through the outer millimetre or so of the ball, so the globe's outer
surface stays a true sphere and nothing a marking adds can face downward.

A region tool is therefore a solid that meets the sphere in the outline the
marking wants and reaches only a controlled depth below it.  Both shapes here
are built from the same piece of arithmetic.  Given a chord half-width
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

from build123d import Location, Pos, Rot, Sphere, Torus


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


def blob_tool(radius: float, blobs, depth: float):
    """A union of round patches -- how every irregular marking here is drawn."""
    tools = [spot_tool(radius, lat, lon, ang, depth) for lat, lon, ang in blobs]
    return tools[0] if len(tools) == 1 else tools[0] + tools[1:]
