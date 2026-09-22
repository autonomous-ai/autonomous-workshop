"""The corona: forty separate flames standing off one unbroken base circle.

No CAD kernel here, so the plan audits can import it.

The disc keeps its own circular edge all the way round. Each flame is rooted on
its own arc of that circle and closes on it, so the union of the disc and the
flames touches along the circle and nowhere else: between two flames the
boundary is the bare base circle, which is the valley floor. Consecutive
flames no longer share a root point, and nothing on this part is a closed loop.

A flame is a swept blade. Its spine leaves the root chord along that chord's
outward normal and turns steadily one way, the heading rising as t**1.15, so
the curvature is continuous from root to tip -- one smooth arc, a comma or a
breaking wave, not a straight shaft with a hook on the end. Its half width
falls from the root chord to a blunt tip cap. The top of the solid then falls
from the deck height at the root to a lower tip, cut by a single plane so the
ramp stays flat and its meeting with each vertical flank stays a crisp line.
"""
from functools import lru_cache
from math import atan2, cos, degrees, hypot, radians, sin, sqrt

import params as P
from geom import (
    _bezier_point,
    _centred_arc,
    _fit_cubic,
    _rotate,
    _three_point_arc,
    _unit,
    _unwrap,
    theta,
    xy,
)


def flame_plan(index):
    """(root start angle, root end angle, tip radius) of one flame."""
    return P.CORONA_PLAN[index % P.CORONA_COUNT]


def valley(index):
    """(start angle, end angle) of the bare base arc after flame `index`."""
    _, end, _ = flame_plan(index)
    start_next, _, _ = flame_plan(index + 1)
    if start_next <= end:
        start_next += 360.0
    return end, start_next


def _jitter(index, step, low, high):
    return low + (high - low) * ((step * (index + 1)) % 1.0)


def flame_rise(index):
    return flame_plan(index)[2] - P.CORONA_BASE_R


def flame_cap(index):
    """Tip cap radius: 2.05 mm on the shortest flame, 1.30 mm on the tallest.

    The falloff is squared, so only the shortest nubs carry the widest cap and
    the long licks spend most of their length already near the 2.60 mm one.
    """
    lo, hi = P.CORONA_RISE_SHORT[0], P.CORONA_RISE_TALL[1]
    t = (flame_rise(index) - lo) / (hi - lo)
    return P.CORONA_TIP_MIN + (P.CORONA_TIP_MAX - P.CORONA_TIP_MIN) * (1.0 - t) ** 2


@lru_cache(maxsize=None)
def tongue_frame(index):
    """The measured frame of one flame, from its root arc outward."""
    start, end, tip_rad = flame_plan(index)
    A = xy(P.CORONA_BASE_R, start)
    B = xy(P.CORONA_BASE_R, end)
    root_width = hypot(B[0] - A[0], B[1] - A[1])
    root_arc = radians(end - start) * P.CORONA_BASE_R
    cap = flame_cap(index)
    M = (0.5 * (A[0] + B[0]), 0.5 * (A[1] + B[1]))
    edge = _unit((B[0] - A[0], B[1] - A[1]))
    u0 = (edge[1], -edge[0])
    if u0[0] * M[0] + u0[1] * M[1] < 0.0:
        u0 = (-u0[0], -u0[1])
    m0 = _unit((A[0] - M[0], A[1] - M[1]))
    # one sense of turn the whole way round: every flame curls toward the
    # neighbour it faces at B, which is the direction the ring is numbered
    sense = -1.0 if u0[0] * m0[1] - u0[1] * m0[0] > 0.0 else 1.0
    turn = _jitter(index, P.CORONA_TURN_JITTER, P.CORONA_TURN_MIN, P.CORONA_TURN_MAX)
    phi0 = degrees(atan2(u0[1], u0[0]))
    length = _solve_spine_length(M, phi0, sense, turn, tip_rad - cap)
    return {
        "start": start, "end": end, "span": end - start,
        "rise": flame_rise(index), "tip_radius": tip_rad, "cap": cap,
        "A": A, "B": B, "M": M, "u0": u0, "m0": m0, "edge": edge,
        "sense": sense, "turn": turn, "phi0": phi0, "length": length,
        "root_width": root_width, "root_arc": root_arc,
    }


def _heading(phi0, sense, turn, t):
    return phi0 + sense * turn * (t ** P.CORONA_TURN_EXP)


def _spine_end(M, phi0, sense, turn, length):
    return spine_point({"M": M, "phi0": phi0, "sense": sense, "turn": turn,
                        "length": length}, 1.0)


def _solve_spine_length(M, phi0, sense, turn, target_radius):
    """Spine length that puts the tip cap centre on `target_radius`."""
    lo, hi = 0.01, 60.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        end = _spine_end(M, phi0, sense, turn, mid)
        if hypot(*end) < target_radius:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def spine_point(frame, t):
    """Point on the flame spine at arc-length fraction t."""
    n = P.CORONA_SPINE_SAMPLES
    x, y = frame["M"]
    for i in range(n):
        mid = t * (i + 0.5) / n
        a = radians(_heading(frame["phi0"], frame["sense"], frame["turn"], mid))
        x += t * frame["length"] / n * cos(a)
        y += t * frame["length"] / n * sin(a)
    return (x, y)


def tongue_half_width(frame, t):
    """Half width at t: the root chord at the base, the tip cap at the point."""
    surplus = 0.5 * frame["root_width"] - frame["cap"]
    u = 1.0 - min(max(t, 0.0), 1.0)
    return frame["cap"] + surplus * u ** P.CORONA_TAPER_EXP


def tongue_normal(frame, t):
    """Unit vector from the spine toward the A flank at t."""
    return _rotate(frame["m0"],
                   frame["sense"] * frame["turn"] * (t ** P.CORONA_TURN_EXP))


def tongue_flank(index, side, samples):
    """Sampled flank from the root to the tip cap. side is 'A' or 'B'."""
    frame = tongue_frame(index)
    sign = 1.0 if side == "A" else -1.0
    out = []
    for i in range(samples + 1):
        t = i / samples
        px, py = spine_point(frame, t)
        nx, ny = tongue_normal(frame, t)
        half = tongue_half_width(frame, t)
        out.append((px + sign * half * nx, py + sign * half * ny))
    return out


def tongue_tip(index):
    """(cap centre, A-side shoulder, outermost cap point, B-side shoulder)."""
    frame = tongue_frame(index)
    centre = spine_point(frame, 1.0)
    normal = tongue_normal(frame, 1.0)
    head = _rotate((frame["u0"][0], frame["u0"][1]),
                   frame["sense"] * frame["turn"])
    cap = frame["cap"]
    return (centre,
            (centre[0] + cap * normal[0], centre[1] + cap * normal[1]),
            (centre[0] + cap * head[0], centre[1] + cap * head[1]),
            (centre[0] - cap * normal[0], centre[1] - cap * normal[1]))


def _flank_samples(index, side, samples=192):
    """Dense analytic flank plus its unit tangent at every sample."""
    points = tongue_flank(index, side, samples)
    points[-1] = tongue_tip(index)[1 if side == "A" else 3]
    tangents = []
    for i in range(len(points)):
        j = max(i - 1, 0)
        k = min(i + 1, len(points) - 1)
        tangents.append(_unit((points[k][0] - points[j][0],
                               points[k][1] - points[j][1])))
    frame = tongue_frame(index)
    tangents[-1] = _rotate(frame["u0"], frame["sense"] * frame["turn"])
    return points, tangents


@lru_cache(maxsize=None)
def tongue_flank_beziers(index, side):
    """One flank as a short chain of exact cubic Beziers."""
    points, tangents = _flank_samples(index, side)
    spans = [(0, len(points) - 1)]
    for _ in range(4):
        worst = 0.0
        rebuilt = []
        for lo, hi in spans:
            control, error = _fit_cubic(points[lo:hi + 1], tangents[lo],
                                        tangents[hi])
            worst = max(worst, error)
            rebuilt.append((lo, hi, control, error))
        if worst <= P.CORONA_FLANK_TOL:
            return tuple((control, error) for _, _, control, error in rebuilt)
        spans = []
        for lo, hi, _, error in rebuilt:
            if error > P.CORONA_FLANK_TOL and hi - lo >= 8:
                mid = (lo + hi) // 2
                spans += [(lo, mid), (mid, hi)]
            else:
                spans.append((lo, hi))
    return tuple((_fit_cubic(points[lo:hi + 1], tangents[lo], tangents[hi]))
                 for lo, hi in spans)


def tongue_curves(index):
    """Flame i as exact curves: A flank, tip cap arc, B flank. Root open."""
    _, shoulder_a, nose, shoulder_b = tongue_tip(index)
    out = [("bezier", control) for control, _ in tongue_flank_beziers(index, "A")]
    out.append(("arc3", (shoulder_a, nose, shoulder_b)))
    out += [("bezier", tuple(reversed(control)))
            for control, _ in reversed(tongue_flank_beziers(index, "B"))]
    return out


def tongue_face_curves(index):
    """One flame as a closed plan face, closed by its own arc of the base circle.

    The closing curve is the base circle itself, so the flame face lies wholly
    outside radius CORONA_BASE_R and meets the disc along that arc alone.
    """
    frame = tongue_frame(index)
    return tongue_curves(index) + [
        ("arc", ((0.0, 0.0), P.CORONA_BASE_R, frame["end"], frame["start"]))]


def tongue_outline(index, samples):
    """Flame i sampled from the root at A round the tip to the root at B."""
    points = []
    for kind, args in tongue_curves(index):
        if kind == "bezier":
            segment = [_bezier_point(args, i / samples) for i in range(samples + 1)]
        else:
            segment = _three_point_arc(args[0], args[1], args[2], 8)
        if points:
            segment = segment[1:]
        points.extend(segment)
    return points


def tongue_face_outline(index, samples=None):
    """The closed plan face of flame i, sampled, for the plan audits."""
    samples = P.CORONA_SAMPLES if samples is None else samples
    frame = tongue_frame(index)
    points = tongue_outline(index, samples)
    arc = _centred_arc((0.0, 0.0), P.CORONA_BASE_R, frame["end"], frame["start"], 8)
    return points + arc[1:-1]


def flank_fit_error():
    """Worst distance between a fitted flank Bezier and its analytic flank."""
    return max(error for i in range(P.CORONA_COUNT) for side in ("A", "B")
               for _, error in tongue_flank_beziers(i, side))


def flank_edge_count():
    return sum(len(tongue_flank_beziers(i, side))
               for i in range(P.CORONA_COUNT) for side in ("A", "B"))


@lru_cache(maxsize=1)
def _tip_height_table():
    """A tip height for every flame, longest lowest, with a jittered quarter.

    That keeps the fall roughly as steep on a short flame as on a long one, so
    the whole crown lies back at one attitude instead of a few stubs dropping
    off a cliff.
    """
    order = sorted(range(P.CORONA_COUNT), key=_axial_reach)
    span = P.CORONA_TIP_Z_MAX - P.CORONA_TIP_Z_MIN
    table = {}
    for rank, index in enumerate(order):
        short = 1.0 - rank / (P.CORONA_COUNT - 1)
        mix = _jitter(index, P.CORONA_TIP_Z_JITTER, 0.0, 1.0)
        table[index] = P.CORONA_TIP_Z_MIN + span * (0.78 * short + 0.22 * mix)
    return table


def _axial_reach(index):
    """Perpendicular distance from a flame's root chord to its outermost point."""
    frame = tongue_frame(index)
    M, u0 = frame["M"], frame["u0"]
    nose = tongue_tip(index)[2]
    return (nose[0] - M[0]) * u0[0] + (nose[1] - M[1]) * u0[1]


@lru_cache(maxsize=None)
def tongue_ramp(index):
    """The single plane that takes the top off one flame as it runs outward."""
    frame = tongue_frame(index)
    M, u0 = frame["M"], frame["u0"]
    axial_max = _axial_reach(index)
    tip_z = _tip_height_table()[index % P.CORONA_COUNT]
    crest = (M[0], M[1])
    foot = (M[0] + axial_max * u0[0], M[1] + axial_max * u0[1])
    return {
        "hold_mm": 0.0,
        "axial_max_mm": axial_max,
        "tip_z": tip_z,
        "slope": (P.CORONA_TOP - tip_z) / axial_max,
        "crest": (crest[0], crest[1], P.CORONA_TOP),
        "crest_side": (crest[0] + frame["edge"][0], crest[1] + frame["edge"][1],
                       P.CORONA_TOP),
        "foot": (foot[0], foot[1], tip_z),
    }


def tongue_top_z(index, point):
    """Height of the ramped top over one plan point of flame i."""
    frame = tongue_frame(index)
    ramp = tongue_ramp(index)
    M, u0 = frame["M"], frame["u0"]
    axial = (point[0] - M[0]) * u0[0] + (point[1] - M[1]) * u0[1]
    return min(P.CORONA_TOP, P.CORONA_TOP - ramp["slope"] * axial)


# --- measured flame properties, for the plan audits -----------------------

def spine_heading(frame, t, h=1.0e-4):
    """Tangent direction of the built spine at t, by finite difference."""
    lo, hi = max(t - h, 0.0), min(t + h, 1.0)
    a = spine_point(frame, lo)
    b = spine_point(frame, hi)
    return degrees(atan2(b[1] - a[1], b[0] - a[0]))


def tongue_turn(index):
    """(total turn, turn inside the outer half) of one built spine, degrees.

    Measured from the tangent of the sampled spine the CAD extrudes, at the
    root, the half-length point and the tip, rather than read back from the
    parameter.
    """
    frame = tongue_frame(index)
    root = spine_heading(frame, 0.0)
    half = spine_heading(frame, 0.5)
    tip = spine_heading(frame, 1.0)
    return abs(_unwrap(tip - root, 0.0)), abs(_unwrap(tip - half, 0.0))


def tongue_tip_thickness(index):
    return 2.0 * tongue_frame(index)["cap"]


def tongue_mid_width(index):
    return 2.0 * tongue_half_width(tongue_frame(index), 0.5)


def root_arc_mm(index):
    return tongue_frame(index)["root_arc"]


def valley_arc_mm(index):
    start, end = valley(index)
    return radians(end - start) * P.CORONA_BASE_R


def pitch_arc_mm(index):
    """Arc from one flame's root start to the next flame's root start."""
    return root_arc_mm(index) + valley_arc_mm(index)
