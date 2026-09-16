"""Spherical relief helpers for the Planet Shear globe.

A raised patch is the 1 mm shell between two concentric spheres, trimmed by a
solid drawn through the patch outline.  How the side wall of that solid leans
decides whether the patch prints, and the rule is local, not global:

    a wall is a down-facing ledge exactly where the outline's outward normal
    points south hard enough that |north component| * cos(latitude) > cos 45.

Nowhere else.  An east- or west-facing wall is vertical whatever the latitude,
and a north-facing wall always looks up.  So each outline vertex gets its own
wall direction: radial by default, and tilted toward the nearer pole by the
smallest amount that clears the gate where the boundary does face south.  A
single tilted cone would instead lean every wall, which leaves thin cantilevered
lips along the diagonal coastlines.

The solid is still a ruled loft between two planar sections, one well inside the
globe and one well outside it, with each vertex placed where the line through
its own two shell points crosses that plane.  Both sections are trimmed away by
the shell, so only the wall between them survives.
"""
import math

from build123d import Align, Cone, Plane, Polygon, Pos, Vector, loft

DOWN_FACE_LIMIT = math.cos(math.radians(45.0))
TILT_TARGET = math.cos(math.radians(51.0))   # aim past the gate, not at it: a tessellated
                                             # facet sits a degree or two off its own surface
MAX_TILT = 3.0              # never lean a wall further than this, in globe radii
MIN_CENTRE_COS = 0.2        # a ring may not span more than ~78 deg from its centre
INNER_PLANE = 0.60          # section plane distances, in globe radii
OUTER_PLANE = 1.30
TILT_SPREAD = 0.50          # how far a vertex's lean carries to its neighbours
TILT_SPREAD_PASSES = 4
NORTH_FACING_CUTOFF = 0.35   # a wall facing north past this borrows no lean at all


def unit_dir(lon_deg, lat_deg):
    """Unit vector for a longitude/latitude pair, +Z through the north pole."""
    lo, la = math.radians(lon_deg), math.radians(lat_deg)
    return Vector(math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))


def _outward_north(ring, index):
    """North component of the outward normal at one vertex of a CCW lon/lat ring."""
    lon, lat = ring[index]
    prev_lon, prev_lat = ring[index - 1]
    next_lon, next_lat = ring[(index + 1) % len(ring)]
    cos_lat = math.cos(math.radians(lat))
    east, north = (next_lon - prev_lon) * cos_lat, next_lat - prev_lat
    span = math.hypot(east, north)
    if span == 0.0:
        return 0.0
    # interior lies left of travel, so the outward normal is travel turned right
    return -east / span


def wall_tilt(lat_deg, outward_north):
    """Smallest lean, in globe radii of vertical offset, that clears the gate.

    The wall normal's downward component is |b| cos(lat) / |radial + c * up|;
    solving that against TILT_TARGET gives the lean, and the smaller root is the
    one that leaves the patch closest to the shape it was drawn as.
    """
    lat = math.radians(lat_deg)
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)
    b = outward_north
    if b >= 0.0 or abs(b) * cos_lat <= DOWN_FACE_LIMIT:
        return 0.0
    target = TILT_TARGET ** 2
    quad_a = target * (sin_lat ** 2 + (cos_lat * b) ** 2)
    quad_b = target * sin_lat
    quad_c = target - (b * cos_lat) ** 2
    disc = quad_b ** 2 - quad_a * quad_c
    if disc <= 0.0 or quad_a == 0.0:
        return 0.0
    root = math.sqrt(disc)
    toward_pole = 1.0 if lat_deg >= 0.0 else -1.0
    same_side = [c for c in ((-quad_b + root) / quad_a, (-quad_b - root) / quad_a)
                 if c * toward_pole > 0.0]
    if not same_side:
        return 0.0
    return max(-MAX_TILT, min(MAX_TILT, min(same_side, key=abs)))


def _spread_tilts(raw, facings):
    """Carry each lean out to its neighbours so the wall turns gradually.

    A lean that appears at one vertex and vanishes at the next makes the two
    wall lines cross, and the section polygon built from them self-intersects.
    Spreading never lowers a vertex below what it needs.

    A vertex that needs no lean of its own still borrows its neighbours' -- except
    where its boundary faces north, which is where a borrowed lean would push the
    top of the patch out past its base.  That is an undercut lip hanging over the
    ocean: it chips off a handled piece, and in a render it reads as the relief
    lifting clear of the sphere.
    """
    positive = [max(t, 0.0) for t in raw]
    negative = [min(t, 0.0) for t in raw]
    count = len(raw)
    for _ in range(TILT_SPREAD_PASSES):
        positive = [max(positive[i], TILT_SPREAD * max(positive[i - 1], positive[(i + 1) % count]))
                    for i in range(count)]
        negative = [min(negative[i], TILT_SPREAD * min(negative[i - 1], negative[(i + 1) % count]))
                    for i in range(count)]
    spread = [p if p >= -n else n for p, n in zip(positive, negative)]
    out = []
    for own, borrowed, facing in zip(raw, spread, facings):
        if own:
            out.append(borrowed)
        else:
            damp = (NORTH_FACING_CUTOFF - facing) / NORTH_FACING_CUTOFF
            out.append(borrowed * max(0.0, min(1.0, damp)))
    return out


def _shell_points(ring, radius, relief, lean):
    """Inner and outer wall anchor points for every vertex."""
    inner, outer = [], []
    outer_radius = radius + relief
    if lean:
        facings = [_outward_north(ring, i) for i in range(len(ring))]
        tilts = _spread_tilts([wall_tilt(lat, facing)
                               for (_lon, lat), facing in zip(ring, facings)], facings)
    else:
        tilts = [0.0] * len(ring)
    for index, (lon, lat) in enumerate(ring):
        base = unit_dir(lon, lat) * radius
        direction = (unit_dir(lon, lat) + Vector(0, 0, tilts[index])).normalized()
        along = base.dot(direction)
        step = -along + math.sqrt(along * along + outer_radius ** 2 - radius ** 2)
        inner.append(base)
        outer.append(base + direction * step)
    return inner, outer


def _frame(points):
    count = len(points)
    centre = Vector(
        sum(p.X for p in points) / count,
        sum(p.Y for p in points) / count,
        sum(p.Z for p in points) / count,
    ).normalized()
    seed = Vector(0, 0, 1) if abs(centre.Z) < 0.9 else Vector(1, 0, 0)
    east = (seed - centre * seed.dot(centre)).normalized()
    return centre, east, centre.cross(east)


def relief_blank(ring_lonlat, radius, relief, lean=True):
    """Solid whose side wall carries the patch outline from `radius` outward.

    `lean=False` keeps every wall radial.  Use it for an outline that only ever
    cuts colour inside another patch, where no wall of its own is ever exposed
    and the lean would only risk collapsing a small shape.
    """
    inner, outer = _shell_points(ring_lonlat, radius, relief, lean)
    centre, east, north = _frame(inner)
    for point in inner:
        if point.normalized().dot(centre) <= MIN_CENTRE_COS:
            raise ValueError("relief ring spans too far from its own centre")
    sections = []
    for plane_at in (INNER_PLANE * radius, OUTER_PLANE * radius):
        flat = []
        for start, end in zip(inner, outer):
            run = end - start
            travel = run.dot(centre)
            if abs(travel) < 1e-9:
                raise ValueError("relief wall runs parallel to its own section plane")
            crossing = start + run * ((plane_at - start.dot(centre)) / travel)
            flat.append((crossing.dot(east), crossing.dot(north)))
        plane = Plane(origin=(centre * plane_at).to_tuple(),
                      x_dir=east.to_tuple(), z_dir=centre.to_tuple())
        sections.append(plane * Polygon(*flat, align=None))
    return loft(sections, ruled=True)


def polar_cap_cone(lat_deg, radius, far):
    """Radial cone through the parallel at `lat_deg`, for a patch enclosing the pole.

    A cap has no lon/lat ring, and its own boundary faces south only gently, so
    the plain radial wall already clears the overhang gate.

    The cap on its own ends on an exact circle of latitude; the lobes in the
    atlas are what break that rim into an ice field.
    """
    lat = math.radians(lat_deg)
    slope = math.cos(lat) / math.sin(lat)
    return Cone(0.0, slope * far, far, align=(Align.CENTER, Align.CENTER, Align.MIN))
