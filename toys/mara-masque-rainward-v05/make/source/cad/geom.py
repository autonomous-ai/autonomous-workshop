"""Shared plan geometry: lane frames, sector outlines and curve maths.

No CAD kernel here, so the plan audits can import it.
"""
from math import atan2, cos, degrees, hypot, radians, sin, sqrt

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


def sector_corners(point, inner_radius, outer_radius, inset):
    """The four corners of one lane sector, in world coordinates.

    The straight sides are parallel to the two boundary rays, exactly as the
    cloned board's channels were; `inset` is the clearance taken off each side
    beyond half of that boundary's exposed body width.
    """
    start_ray = theta(point) - P.PITCH / 2.0
    end_ray = theta(point) + P.PITCH / 2.0
    start_off = boundary_width(point) / 2.0 + inset
    end_off = boundary_width(next_point(point)) / 2.0 + inset
    return {
        "a_in": _line_point(start_ray, start_off, inner_radius),
        "a_out": _line_point(start_ray, start_off, outer_radius),
        "b_out": _line_point(end_ray, -end_off, outer_radius),
        "b_in": _line_point(end_ray, -end_off, inner_radius),
    }


def sector_curves(point, inner_radius, outer_radius, inset):
    """One lane sector as exact curves: line, outer arc, line, inner arc.

    The outer edge is an exact circular arc of `outer_radius` centred on the
    board, so the twenty-four tiles finish on one continuous circle with no
    notch, scallop or bay cut into any of them. Exact curves also keep the
    exported solid small: four edges instead of forty chords.
    """
    c = sector_corners(point, inner_radius, outer_radius, inset)
    ref = theta(point)
    out_start = _unwrap(degrees(atan2(c["a_out"][1], c["a_out"][0])), ref)
    out_end = _unwrap(degrees(atan2(c["b_out"][1], c["b_out"][0])), ref)
    in_end = _unwrap(degrees(atan2(c["b_in"][1], c["b_in"][0])), ref)
    in_start = _unwrap(degrees(atan2(c["a_in"][1], c["a_in"][0])), ref)
    return [
        ("line", (c["a_in"], c["a_out"])),
        ("arc", ((0.0, 0.0), outer_radius, out_start, out_end)),
        ("line", (c["b_out"], c["b_in"])),
        ("arc", ((0.0, 0.0), inner_radius, in_end, in_start)),
    ]


def sector_profile(point, inner_radius, outer_radius, inset, samples=48):
    """The same sector sampled as a closed polygon, for the plan audits."""
    c = sector_corners(point, inner_radius, outer_radius, inset)
    ref = theta(point)
    out_start = _unwrap(degrees(atan2(c["a_out"][1], c["a_out"][0])), ref)
    out_end = _unwrap(degrees(atan2(c["b_out"][1], c["b_out"][0])), ref)
    in_end = _unwrap(degrees(atan2(c["b_in"][1], c["b_in"][0])), ref)
    in_start = _unwrap(degrees(atan2(c["a_in"][1], c["a_in"][0])), ref)
    points = [c["a_in"]]
    points += _arc_points(outer_radius, out_start, out_end, samples)
    points += [c["b_in"]]
    points += _arc_points(inner_radius, in_end, in_start, 16)[1:-1]
    return points


# --- curve maths -----------------------------------------------------------

def _unit(v):
    n = sqrt(v[0] * v[0] + v[1] * v[1])
    return (v[0] / n, v[1] / n)


def _rotate(v, angle_deg):
    c, s = cos(radians(angle_deg)), sin(radians(angle_deg))
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def _centred_arc(centre, radius, a0, a1, samples):
    return [(centre[0] + radius * cos(radians(a0 + (a1 - a0) * i / samples)),
             centre[1] + radius * sin(radians(a0 + (a1 - a0) * i / samples)))
            for i in range(samples + 1)]


def _three_point_arc(p0, p1, p2, samples):
    """Sample the circle through three points, from p0 to p2 the short way."""
    ax, ay = p0
    bx, by = p1
    cx, cy = p2
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return [p0, p1, p2]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay)
          + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx)
          + (cx * cx + cy * cy) * (bx - ax)) / d
    centre = (ux, uy)
    radius = hypot(ax - ux, ay - uy)
    a0 = degrees(atan2(ay - uy, ax - ux))
    a1 = _unwrap(degrees(atan2(by - uy, bx - ux)), a0)
    a2 = _unwrap(degrees(atan2(cy - uy, cx - ux)), a1)
    return _centred_arc(centre, radius, a0, a2, samples)


def _chord_parameters(points):
    total = [0.0]
    for i in range(1, len(points)):
        total.append(total[-1] + hypot(points[i][0] - points[i - 1][0],
                                       points[i][1] - points[i - 1][1]))
    return [value / total[-1] for value in total]


def _bezier_point(control, t):
    u = 1.0 - t
    return tuple(u ** 3 * control[0][k] + 3 * u * u * t * control[1][k]
                 + 3 * u * t * t * control[2][k] + t ** 3 * control[3][k]
                 for k in (0, 1))


def _fit_cubic(points, head, tail):
    """One cubic Bezier through `points`, leaving along `head`, arriving on `tail`.

    Least squares on the two handle lengths only, so the end points and both
    end tangents are exact. One cubic per flank keeps each flank a single
    exact edge, which is what keeps the exported solid small.
    """
    p0, p3 = points[0], points[-1]
    us = _chord_parameters(points)
    a11 = a12 = a22 = b1 = b2 = 0.0
    for point, u in zip(points, us):
        w = 1.0 - u
        f0, f1 = w ** 3, 3 * w * w * u
        f2, f3 = 3 * w * u * u, u ** 3
        va = (f1 * head[0], f1 * head[1])
        vb = (-f2 * tail[0], -f2 * tail[1])
        rx = point[0] - (f0 + f1) * p0[0] - (f2 + f3) * p3[0]
        ry = point[1] - (f0 + f1) * p0[1] - (f2 + f3) * p3[1]
        a11 += va[0] * va[0] + va[1] * va[1]
        a12 += va[0] * vb[0] + va[1] * vb[1]
        a22 += vb[0] * vb[0] + vb[1] * vb[1]
        b1 += va[0] * rx + va[1] * ry
        b2 += vb[0] * rx + vb[1] * ry
    det = a11 * a22 - a12 * a12
    span = hypot(p3[0] - p0[0], p3[1] - p0[1])
    if abs(det) < 1e-12:
        alpha = beta = span / 3.0
    else:
        alpha = (b1 * a22 - b2 * a12) / det
        beta = (a11 * b2 - a12 * b1) / det
    alpha = min(max(alpha, 0.05 * span), 1.2 * span)
    beta = min(max(beta, 0.05 * span), 1.2 * span)
    control = (p0,
               (p0[0] + alpha * head[0], p0[1] + alpha * head[1]),
               (p3[0] - beta * tail[0], p3[1] - beta * tail[1]),
               p3)
    error = max(hypot(point[0] - _bezier_point(control, u)[0],
                      point[1] - _bezier_point(control, u)[1])
                for point, u in zip(points, us))
    return control, error


def polar_extent(profile):
    """(min angle, max angle, max radius) of one profile, angles unwrapped."""
    ref = degrees(atan2(profile[0][1], profile[0][0]))
    angles = [_unwrap(degrees(atan2(y, x)), ref) for x, y in profile]
    radii = [sqrt(x * x + y * y) for x, y in profile]
    return min(angles), max(angles), max(radii)
