"""Pure-geometry plan outlines. No CAD kernel here, so the audits can import it."""
from functools import lru_cache
from math import atan2, cos, degrees, pi, radians, sin, sqrt

import params as P


# --- lane frames -----------------------------------------------------------

def theta(point):
    """Preserved lane axis angle in degrees for printed point 1..24."""
    return P.START_ANGLE + P.PITCH * (point - 1)


def xy(radius, angle_deg):
    return (radius * cos(radians(angle_deg)), radius * sin(radians(angle_deg)))


def boundary_width(point):
    """1.6 mm of body at the four bank boundaries, 0.8 mm at the other twenty.

    The boundary indexed by `point` lies at theta(point) - 7.5 degrees, so the
    wide ones are the 24/1, 6/7, 12/13 and 18/19 boundaries.
    """
    return P.BANK_W if point % 6 == 1 else P.CHANNEL_W


def bank_boundary_points():
    return (1, 7, 13, 19)


def next_point(point):
    return point + 1 if point < P.LANES else 1


# --- annular-sector plan profile ------------------------------------------

def _line_point(ray_deg, offset, radius):
    """Point at `radius` on the line parallel to `ray_deg`, offset sideways.

    A positive offset moves toward increasing angle.
    """
    u = (cos(radians(ray_deg)), sin(radians(ray_deg)))
    n = (-sin(radians(ray_deg)), cos(radians(ray_deg)))
    s = sqrt(max(radius * radius - offset * offset, 0.0))
    return (s * u[0] + offset * n[0], s * u[1] + offset * n[1])


def _unwrap(angle, reference):
    while angle - reference > 180.0:
        angle -= 360.0
    while angle - reference < -180.0:
        angle += 360.0
    return angle


def _arc_points(radius, start_deg, end_deg, samples):
    step = (end_deg - start_deg) / samples
    return [xy(radius, start_deg + step * i) for i in range(samples + 1)]


def sector_profile(point, inner_radius, outer_radius, inset, clipped=False):
    """Plan outline of one lane sector in world coordinates.

    The straight sides are parallel to the two boundary rays, exactly as the
    cloned board's channels were; `inset` is the clearance taken off each side
    beyond half of that boundary's exposed body width. With `clipped`, the
    outer edge follows the skirt instead of a circle, so a tile retreats into
    the troughs that cut inside radius 90 and never overhangs one.
    """
    start_ray = theta(point) - P.PITCH / 2.0
    end_ray = theta(point) + P.PITCH / 2.0
    start_off = boundary_width(point) / 2.0 + inset
    end_off = boundary_width(next_point(point)) / 2.0 + inset

    def outer_at(angle):
        return min(outer_radius, tile_outer_radius(angle)) if clipped else outer_radius

    def side_outer(ray, offset):
        radius = outer_radius
        for _ in range(4):
            point_xy = _line_point(ray, offset, radius)
            radius = outer_at(degrees(atan2(point_xy[1], point_xy[0])))
        return _line_point(ray, offset, radius)

    a_in = _line_point(start_ray, start_off, inner_radius)
    a_out = side_outer(start_ray, start_off)
    b_out = side_outer(end_ray, -end_off)
    b_in = _line_point(end_ray, -end_off, inner_radius)

    ref = theta(point)
    out_start = _unwrap(degrees(atan2(a_out[1], a_out[0])), ref)
    out_end = _unwrap(degrees(atan2(b_out[1], b_out[0])), ref)
    in_end = _unwrap(degrees(atan2(b_in[1], b_in[0])), ref)
    in_start = _unwrap(degrees(atan2(a_in[1], a_in[0])), ref)

    points = [a_in, a_out]
    steps = 180 if clipped else 28
    for i in range(1, steps):
        angle = out_start + (out_end - out_start) * i / steps
        points.append(xy(outer_at(angle), angle))
    points += [b_out, b_in]
    points += _arc_points(inner_radius, in_end, in_start, 12)[1:-1]
    return points


# --- corona skirt ----------------------------------------------------------
# One closed boundary runs round the whole body: trough floor, tongue, trough
# floor, tongue. Consecutive tongues share their root points, so the flame is a
# continuous band of material and every notch is a trough cut into that band.


def _unit(v):
    n = sqrt(v[0] * v[0] + v[1] * v[1])
    return (v[0] / n, v[1] / n)


def _bezier(p0, p1, p2, p3, samples):
    out = []
    for i in range(samples + 1):
        t = i / samples
        u = 1.0 - t
        out.append(tuple(
            u ** 3 * p0[k] + 3 * u * u * t * p1[k] + 3 * u * t * t * p2[k]
            + t ** 3 * p3[k] for k in (0, 1)))
    return out


def _centred_arc(centre, radius, a0, a1, samples):
    return [(centre[0] + radius * cos(radians(a0 + (a1 - a0) * i / samples)),
             centre[1] + radius * sin(radians(a0 + (a1 - a0) * i / samples)))
            for i in range(samples + 1)]


def trough(index):
    """(root angle, floor radius, floor half-arc) of one trough."""
    return P.CORONA_TROUGHS[index % P.CORONA_COUNT]


def tongue_frame(index):
    """The measured frame of the tongue that runs from trough i to trough i+1."""
    a_ang, a_rad, a_half = trough(index)
    b_ang, b_rad, b_half = trough(index + 1)
    if b_ang <= a_ang:
        b_ang += 360.0
    start = a_ang + a_half
    end = b_ang - b_half
    span = end - start
    tip_rad = P.CORONA_TIPS[index % P.CORONA_COUNT]
    rise = tip_rad - 0.5 * (a_rad + b_rad)
    root_width = sqrt((xy(b_rad, end)[0] - xy(a_rad, start)[0]) ** 2
                      + (xy(b_rad, end)[1] - xy(a_rad, start)[1]) ** 2)
    cap = min(P.CORONA_TIP_MAX, max(P.CORONA_TIP_MIN, P.CORONA_TIP_FRAC * rise),
              P.CORONA_TIP_SHARE * root_width)
    # a narrow tongue leans less, so its tip never swings past its own root
    lean = P.CORONA_LEAN_DEG * min(1.0, span / P.CORONA_LEAN_FULL_SPAN)
    psi = 0.5 * (start + end) + P.CORONA_LEAN_FRAC * span + lean
    A = xy(a_rad, start)
    B = xy(b_rad, end)
    C = xy(tip_rad - cap, psi)
    u = (cos(radians(psi)), sin(radians(psi)))
    normal = (-u[1], u[0])
    return {
        "start": start, "end": end, "span": span, "psi": psi, "rise": rise,
        "tip_radius": tip_rad, "cap": cap, "A": A, "B": B, "C": C, "u": u,
        "root_width": root_width,
        "shoulder_a": (C[0] - cap * normal[0], C[1] - cap * normal[1]),
        "shoulder_b": (C[0] + cap * normal[0], C[1] + cap * normal[1]),
    }


def tongue_curves(index):
    """Tongue i as exact curves: rising flank, rounded tip cap, falling flank.

    Both flanks meet the cap along the tip axis, so the tip is tangent-smooth.
    """
    f = tongue_frame(index)
    pull = max(f["rise"], 0.6)
    ra, rb = _unit(f["A"]), _unit(f["B"])
    p1 = (f["A"][0] + P.CORONA_ROOT_PULL * pull * ra[0],
          f["A"][1] + P.CORONA_ROOT_PULL * pull * ra[1])
    p2 = (f["shoulder_a"][0] - P.CORONA_TIP_PULL * pull * f["u"][0],
          f["shoulder_a"][1] - P.CORONA_TIP_PULL * pull * f["u"][1])
    q1 = (f["shoulder_b"][0] - P.CORONA_TIP_PULL * pull * f["u"][0],
          f["shoulder_b"][1] - P.CORONA_TIP_PULL * pull * f["u"][1])
    q2 = (f["B"][0] + P.CORONA_ROOT_PULL * pull * rb[0],
          f["B"][1] + P.CORONA_ROOT_PULL * pull * rb[1])
    return [("bezier", (f["A"], p1, p2, f["shoulder_a"])),
            ("arc", (f["C"], f["cap"], f["psi"] - 90.0, f["psi"] + 90.0)),
            ("bezier", (f["shoulder_b"], q1, q2, f["B"]))]


def skirt_curves():
    """The body's complete outer boundary, trough floor then tongue, all round."""
    out = []
    for index in range(P.CORONA_COUNT):
        ang, rad, half = trough(index)
        out.append(("arc", ((0.0, 0.0), rad, ang - half, ang + half)))
        out.extend(tongue_curves(index))
    return out


def skirt_outline(samples=None):
    """The same boundary sampled as a closed polygon, for the plan audits."""
    samples = P.CORONA_SAMPLES if samples is None else samples
    points = []
    for kind, args in skirt_curves():
        if kind == "bezier":
            segment = _bezier(*args, samples=samples)
        else:
            centre, radius, a0, a1 = args
            n = 6 if centre == (0.0, 0.0) else 10
            segment = _centred_arc(centre, radius, a0, a1, n)
        if points and abs(segment[0][0] - points[-1][0]) < 1e-9 \
                and abs(segment[0][1] - points[-1][1]) < 1e-9:
            segment = segment[1:]
        points.extend(segment)
    if abs(points[0][0] - points[-1][0]) < 1e-9 \
            and abs(points[0][1] - points[-1][1]) < 1e-9:
        points.pop()
    return points


@lru_cache(maxsize=1)
def _skirt_table():
    """Boundary radius against unwrapped angle, ascending. Single valued."""
    table = []
    base = None
    for x, y in skirt_outline(samples=48):
        a = degrees(atan2(y, x))
        if base is not None:
            a = _unwrap(a, base)
        base = a
        table.append((a, sqrt(x * x + y * y)))
    if table[-1][0] < table[0][0]:
        table.reverse()
    assert all(table[i + 1][0] >= table[i][0] - 1e-9 for i in range(len(table) - 1)), \
        "the skirt boundary must stay single valued in angle"
    return table


def skirt_radius(angle, window=0.25):
    """Smallest boundary radius within +/- `window` degrees of `angle`.

    The tiles are clipped against this, so taking the minimum over a small
    window keeps a sampled tile edge inside the body even at a trough.
    """
    table = _skirt_table()
    lo, hi = table[0][0], table[-1][0]
    best = None
    for shift in (-360.0, 0.0, 360.0):
        a = angle + shift
        if a < lo - window or a > hi + window:
            continue
        left, right = 0, len(table) - 1
        while left < right:
            mid = (left + right) // 2
            if table[mid][0] < a - window:
                left = mid + 1
            else:
                right = mid
        i = left
        while i < len(table) and table[i][0] <= a + window:
            best = table[i][1] if best is None else min(best, table[i][1])
            i += 1
        if best is None and 0 < left < len(table):
            best = min(table[left - 1][1], table[left][1])
    return P.SUN_R if best is None else best


def boundary_radius_limit(point):
    """How far a lane boundary ridge may run before the skirt has cut it away."""
    ray = theta(point) - P.PITCH / 2.0
    return min([P.SUN_R] + [skirt_radius(ray + step * 0.3) for step in range(-4, 5)])


def boundary_bay_radius(angle):
    """How far back the tile pulls in the free window at a lane boundary.

    The window is centred on the boundary ray and closes well before the
    footprint of any counter at the outermost station, so the bay exposes the
    crown's base without taking flat support from anything.
    """
    offset = (angle - (P.START_ANGLE - P.PITCH / 2.0)) % P.PITCH
    offset = min(offset, P.PITCH - offset)
    if offset <= P.TILE_BAY_INNER:
        return P.TILE_BAY_R
    if offset >= P.TILE_BAY_OUTER:
        return P.TILE_OUTER
    u = (offset - P.TILE_BAY_INNER) / (P.TILE_BAY_OUTER - P.TILE_BAY_INNER)
    return P.TILE_BAY_R + (P.TILE_OUTER - P.TILE_BAY_R) * u * u * (3.0 - 2.0 * u)


def tile_outer_radius(angle):
    """Where a tile's outer edge sits: the rim, a trough that cuts it, or a bay."""
    return min(P.TILE_OUTER, skirt_radius(angle) - P.CLEAR,
               boundary_bay_radius(angle))


# --- the hero arch ---------------------------------------------------------

def _hero_spine(t):
    """Steep legs under a domed crest, the crest leaning the way tongues sweep."""
    rise = sin(pi * min(max(t, 0.0), 1.0) ** P.HERO_SKEW) ** P.HERO_DOME
    return P.HERO_FOOT_R + (P.HERO_APEX_R - P.HERO_FOOT_R) * rise


def hero_profile():
    """The hero arch as a polar strip: it cannot self-intersect.

    The outer edge is the arch itself. The inner edge thickens exactly where a
    leg dives, so each foot keeps its full 2.8 mm across where it enters the
    body instead of touching the skirt at a point.
    """
    outer, inner = [], []
    n = P.HERO_SAMPLES
    for i in range(n + 1):
        t = i / n
        angle = P.HERO_START + P.HERO_SPAN * t
        r = _hero_spine(t)
        eps = 1.0 / (2 * n)
        t0, t1 = max(t - eps, 0.0), min(t + eps, 1.0)
        ds = r * radians(P.HERO_SPAN * (t1 - t0))
        slope = abs((_hero_spine(t1) - _hero_spine(t0)) / ds) if ds else 0.0
        deep = min(P.HERO_HALF * sqrt(1.0 + slope * slope), P.HERO_ROOT_CAP)
        outer.append(xy(r + P.HERO_HALF, angle))
        inner.append(xy(r - deep, angle))
    return outer + list(reversed(inner))


def polar_extent(profile):
    """(min angle, max angle, max radius) of one profile, angles unwrapped."""
    ref = degrees(atan2(profile[0][1], profile[0][0]))
    angles = [_unwrap(degrees(atan2(y, x)), ref) for x, y in profile]
    radii = [sqrt(x * x + y * y) for x, y in profile]
    return min(angles), max(angles), max(radii)
