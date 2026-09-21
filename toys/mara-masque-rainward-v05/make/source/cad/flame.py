"""The corona skirt: one swept blade per tongue, and the band they form.

No CAD kernel here, so the plan audits can import it.
"""
from functools import lru_cache
from math import atan2, cos, degrees, hypot, pi, radians, sin, sqrt

import params as P
from geom import (
    _bezier_point,
    _centred_arc,
    _chord_parameters,
    _fit_cubic,
    _rotate,
    _three_point_arc,
    _unit,
    _unwrap,
    theta,
    xy,
)


# --- corona skirt ----------------------------------------------------------
# One closed boundary runs round the whole body: trough floor, tongue, trough
# floor, tongue. Consecutive tongues share their root points, so the flame is a
# continuous band of material and every notch is a trough cut into that band.
#
# A tongue is a swept blade. Its spine leaves the root chord along that chord's
# outward normal and turns one way, all the turn back-loaded into the outer
# half; its width is taken off early, so the outer half is already slender
# while the root keeps the full width of the chord it shares with both of its
# neighbours. The top of the solid then falls from the deck height at the root
# to a lower tip, cut by a single plane so the ramp stays flat and its meeting
# with each vertical flank stays a crisp straight line.


def trough(index):
    """(root angle, floor radius, floor half-arc) of one trough."""
    return P.CORONA_TROUGHS[index % P.CORONA_COUNT]


def _jitter(index, step, low, high):
    """A repeatable irrational walk over [low, high); no two neighbours equal."""
    return low + (high - low) * ((step * (index + 1)) % 1.0)


@lru_cache(maxsize=None)
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
    A = xy(a_rad, start)
    B = xy(b_rad, end)
    root_width = hypot(B[0] - A[0], B[1] - A[1])
    cap = min(P.CORONA_TIP_MAX, max(P.CORONA_TIP_MIN, P.CORONA_TIP_FRAC * rise),
              P.CORONA_TIP_SHARE * root_width)
    M = (0.5 * (A[0] + B[0]), 0.5 * (A[1] + B[1]))
    # the spine leaves along the chord's outward normal, so the two flanks
    # start exactly on the two trough floor ends this tongue shares
    edge = _unit((B[0] - A[0], B[1] - A[1]))
    u0 = (edge[1], -edge[0])
    if u0[0] * M[0] + u0[1] * M[1] < 0.0:
        u0 = (-u0[0], -u0[1])
    m0 = _unit((A[0] - M[0], A[1] - M[1]))
    # one sense of turn the whole way round: every tongue curls toward the
    # neighbour it meets at B, which is the direction the ring is numbered
    sense = -1.0 if u0[0] * m0[1] - u0[1] * m0[0] > 0.0 else 1.0
    turn = _jitter(index, P.CORONA_TURN_JITTER, P.CORONA_TURN_MIN, P.CORONA_TURN_MAX)
    phi0 = degrees(atan2(u0[1], u0[0]))
    length = _solve_spine_length(M, phi0, sense, turn, tip_rad - cap)
    return {
        "start": start, "end": end, "span": span, "rise": rise,
        "tip_radius": tip_rad, "cap": cap, "A": A, "B": B, "M": M,
        "u0": u0, "m0": m0, "edge": edge, "sense": sense, "turn": turn,
        "phi0": phi0, "length": length, "root_width": root_width,
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
    """Point on the tongue spine at arc-length fraction t.

    The same fixed midpoint rule at every t, so the spine is one smooth curve
    rather than a family of curves that disagree by a fraction of a step.
    """
    n = P.CORONA_SPINE_SAMPLES
    x, y = frame["M"]
    for i in range(n):
        mid = t * (i + 0.5) / n
        a = radians(_heading(frame["phi0"], frame["sense"], frame["turn"], mid))
        x += t * frame["length"] / n * cos(a)
        y += t * frame["length"] / n * sin(a)
    return (x, y)


def tongue_half_width(frame, t):
    """Half width at t: full at the root, slender through the outer half.

    The surplus over the tip falls as (1 - t) ** exp, so the width comes off
    at once where the tongue leaves its trough -- which is what makes the notch
    between two tongues a V rather than a scallop -- and the outer half is
    already down to under a third of the root. The exponent is above one, so
    the flank still arrives at the tip cap tangentially instead of as a point.
    """
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
    # the tip tangent is pinned to the tip axis so each flank meets the cap
    # arc tangentially; the root tangent is whatever the taper actually leaves
    frame = tongue_frame(index)
    tangents[-1] = _rotate(frame["u0"], frame["sense"] * frame["turn"])
    return points, tangents


@lru_cache(maxsize=None)
def tongue_flank_beziers(index, side):
    """One flank as a short chain of exact cubic Beziers.

    Splitting only where the fit needs it keeps the flank to two or three
    exact edges instead of a dense spline, which is what keeps the exported
    solid small while the sampled plan audits still measure the built curve.
    """
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
    """Tongue i as exact curves: A flank Beziers, tip cap arc, B flank Beziers."""
    _, shoulder_a, nose, shoulder_b = tongue_tip(index)
    out = [("bezier", control) for control, _ in tongue_flank_beziers(index, "A")]
    out.append(("arc3", (shoulder_a, nose, shoulder_b)))
    out += [("bezier", tuple(reversed(control)))
            for control, _ in reversed(tongue_flank_beziers(index, "B"))]
    return out


def tongue_outline(index, samples):
    """Tongue i sampled from the root at A round the tip to the root at B.

    Sampled from the exact curves the CAD extrudes, not from the analytic
    flank they were fitted to, so every plan audit measures the built shape.
    """
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


def flank_fit_error():
    """Worst distance between a fitted flank Bezier and its analytic flank."""
    return max(error for i in range(P.CORONA_COUNT) for side in ("A", "B")
               for _, error in tongue_flank_beziers(i, side))


def flank_edge_count():
    return sum(len(tongue_flank_beziers(i, side))
               for i in range(P.CORONA_COUNT) for side in ("A", "B"))


def core_curves():
    """The deck core: trough floor arcs closed by each tongue's root chord."""
    out = []
    for index in range(P.CORONA_COUNT):
        ang, rad, half = trough(index)
        frame = tongue_frame(index)
        out.append(("arc", ((0.0, 0.0), rad, ang - half, ang + half)))
        out.append(("line", (frame["A"], frame["B"])))
    return out


def tongue_face_curves(index):
    """One tongue as a closed plan face: both flanks, the cap, the root chord."""
    frame = tongue_frame(index)
    return tongue_curves(index) + [("line", (frame["B"], frame["A"]))]


def _axial_reach(index):
    """Perpendicular distance from a tongue's root chord to its outermost point."""
    frame = tongue_frame(index)
    M, u0 = frame["M"], frame["u0"]
    nose = tongue_tip(index)[2]
    return (nose[0] - M[0]) * u0[0] + (nose[1] - M[1]) * u0[1]


@lru_cache(maxsize=1)
def _tip_height_table():
    """A tip height for every tongue, between the Wish's 3.5 and 5.0 floor/ceiling.

    Heights are dealt out against how far a tongue actually reaches, longest
    lowest, with a jittered quarter mixed in so the ring is not a straight
    ramp of heights. That keeps the fall roughly as steep on a short tongue as
    on a long one, so the whole crown lies back at one attitude instead of a
    few stubs dropping off a cliff.
    """
    order = sorted(range(P.CORONA_COUNT), key=_axial_reach)
    span = P.CORONA_TIP_Z_MAX - P.CORONA_TIP_Z_MIN
    table = {}
    for rank, index in enumerate(order):
        short = 1.0 - rank / (P.CORONA_COUNT - 1)
        mix = _jitter(index, P.CORONA_TIP_Z_JITTER, 0.0, 1.0)
        table[index] = P.CORONA_TIP_Z_MIN + span * (0.78 * short + 0.22 * mix)
    return table


@lru_cache(maxsize=None)
def tongue_ramp(index):
    """The single plane that takes the top off one tongue as it runs outward.

    The plane holds the deck height out to the radius where the tile lip ends
    and the body first shows, then falls in a straight line to the tip height.
    Nothing is taken off the underside, so the tongue still sits flat on the
    bed and no face overhangs.
    """
    frame = tongue_frame(index)
    M, u0 = frame["M"], frame["u0"]

    def axial(point):
        return (point[0] - M[0]) * u0[0] + (point[1] - M[1]) * u0[1]

    nose = tongue_tip(index)[2]
    axial_max = axial(nose)
    hold = 0.0
    if hypot(*M) < P.CORONA_HOLD_R:
        lo, hi = 0.0, 1.0
        for _ in range(48):
            mid = 0.5 * (lo + hi)
            if hypot(*spine_point(frame, mid)) < P.CORONA_HOLD_R:
                lo = mid
            else:
                hi = mid
        hold = max(0.0, axial(spine_point(frame, 0.5 * (lo + hi))))
    hold = min(hold, P.CORONA_HOLD_MAX_FRAC * axial_max)
    tip_z = _tip_height_table()[index % P.CORONA_COUNT]
    crest = (M[0] + hold * u0[0], M[1] + hold * u0[1])
    foot = (M[0] + axial_max * u0[0], M[1] + axial_max * u0[1])
    return {
        "hold_mm": hold,
        "axial_max_mm": axial_max,
        "tip_z": tip_z,
        "slope": (P.CORONA_TOP - tip_z) / (axial_max - hold),
        "crest": (crest[0], crest[1], P.CORONA_TOP),
        "crest_side": (crest[0] + frame["edge"][0], crest[1] + frame["edge"][1],
                       P.CORONA_TOP),
        "foot": (foot[0], foot[1], tip_z),
    }


def tongue_top_z(index, point):
    """Height of the ramped top over one plan point of tongue i."""
    frame = tongue_frame(index)
    ramp = tongue_ramp(index)
    M, u0 = frame["M"], frame["u0"]
    axial = (point[0] - M[0]) * u0[0] + (point[1] - M[1]) * u0[1]
    return min(P.CORONA_TOP, P.CORONA_TOP - ramp["slope"] * (axial - ramp["hold_mm"]))


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
    for index in range(P.CORONA_COUNT):
        ang, rad, half = trough(index)
        segment = _centred_arc((0.0, 0.0), rad, ang - half, ang + half, 6)
        if points:
            segment = segment[1:]
        points.extend(segment)
        points.extend(tongue_outline(index, samples)[1:])
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
    return table


def skirt_radius(angle, window=0.25):
    """Smallest boundary radius within +/- `window` degrees of `angle`.

    The lane boundary buttresses are limited by this, so taking the minimum
    over a small window keeps a ridge from hanging out over a trough.
    """
    table = _skirt_table()
    lo, hi = table[0][0], table[-1][0]
    best = None
    for shift in (-360.0, 0.0, 360.0):
        a = angle + shift
        if a < lo - window or a > hi + window:
            continue
        for value, radius in table:
            if a - window <= value <= a + window:
                best = radius if best is None else min(best, radius)
    return P.SUN_R if best is None else best


def boundary_radius_limit(point):
    """How far a lane boundary ridge may run before the skirt has cut it away."""
    ray = theta(point) - P.PITCH / 2.0
    return min([P.SUN_R] + [skirt_radius(ray + step * 0.3) for step in range(-4, 5)])


# --- measured tongue properties, for the plan audits ----------------------

def tongue_turn(index, samples=64):
    """(total turn, turn inside the outer half) of one tongue spine, degrees.

    Measured from the built spine rather than read back from the parameter, so
    the audit reports the shape the CAD actually extrudes.
    """
    frame = tongue_frame(index)
    points = [spine_point(frame, i / samples) for i in range(samples + 1)]
    headings = []
    for i in range(samples):
        dx = points[i + 1][0] - points[i][0]
        dy = points[i + 1][1] - points[i][1]
        headings.append(degrees(atan2(dy, dx)))
    total = _unwrap(headings[-1] - headings[0], 0.0)
    outer = _unwrap(headings[-1] - headings[samples // 2], 0.0)
    return abs(total), abs(outer)


def tongue_tip_thickness(index):
    return 2.0 * tongue_frame(index)["cap"]


def tongue_mid_width(index):
    return 2.0 * tongue_half_width(tongue_frame(index), 0.5)
