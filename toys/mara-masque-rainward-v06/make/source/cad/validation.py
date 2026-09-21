"""Algebraic parameter checks. These run before any geometry is built."""
from math import cos, degrees, radians, sin, sqrt

import params as P
import profiles as G

LUMA = (0.2126, 0.7152, 0.0722)
MIN_TONE_GAP = 0.09          # separation required between neighbouring values
MIN_FLAMES, MAX_FLAMES = 32, 48
MIN_LENGTH_RATIO = 4.0       # [specified] shortest to tallest
TURN_LO, TURN_HI = 37.0, 44.0            # [specified] root to tip, degrees
INNER_SHARE_LO, INNER_SHARE_HI = 0.43, 0.47   # [specified] about 45 per cent
TIP_ACROSS_LO, TIP_ACROSS_HI = 2.60, 4.10     # [specified] tip cap, mm
TIP_Z_MIN = 3.0              # [specified] tip at least 3.0 mm tall in Z
ROOT_FRACTION_MAX = 0.55     # [specified] root over root-to-root arc
MAX_ENVELOPE = 194.0         # [specified]


def luma(colour):
    return sum(w * c for w, c in zip(LUMA, colour))


def _close(a, b, label):
    assert abs(a - b) < 1e-6, "%s: %r != %r" % (label, a, b)


def _point_in_polygon(point, polygon):
    x, y = point
    inside = False
    count = len(polygon)
    for i in range(count):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % count]
        if (y0 > y) != (y1 > y):
            t = (y - y0) / (y1 - y0)
            if x < x0 + t * (x1 - x0):
                inside = not inside
    return inside


def check_heights():
    _close(P.POCKET_FLOOR + P.TILE_T, P.LANE_TOP, "tile top")
    _close(P.POCKET_FLOOR, 3.8, "solid body under the pocket")
    _close(P.LANE_TOP - P.DECK, 0.6, "tile proud of the body")
    _close(P.BAR_TOP - P.LANE_TOP, 0.2, "centre bar above the lane tops")
    _close(P.GAP_FLOOR, 5.4, "gap floor")
    _close(P.SUN_H, 6.2, "overall Sun height")
    _close(P.CORONA_TOP, 5.4, "flame root height")
    layers = [round(P.LANE_TOP + i * P.DROP_H, 3) for i in range(3)]
    assert layers == [6.0, 10.5, 15.0], layers
    assert P.POCKET_FLOOR - P.KEY_RECESS_D > 2.5, "the key recess thins the deck"


def check_fit_chain():
    _close(P.POCKET_INNER, P.LANE_INNER - P.CLEAR, "pocket inner clearance")
    _close(P.TILE_OUTER, P.SUN_R - P.CLEAR, "tile outer clearance")
    _close(P.TILE_OUTER, 79.55, "tile fan arc radius")
    _close(P.KEY_RECESS_D - P.KEY_H, 0.2, "key bottom clearance")
    assert P.KEY_CLEAR == P.CLEAR, "one clearance value for the whole seat"
    _close(P.LIP_T, P.LANE_TOP - P.RIM_TOP, "tile lip thickness")
    assert P.LIP_T >= 2 * P.NOZZLE + 0.2, "tile lip is too close to the wall limit"
    assert P.SUN_R - P.RIM_INNER >= 2.0, "rim ring is too narrow to carry the lips"
    _close(P.CHANNEL_W, 0.70, "constant orange margin")
    _close(P.BANK_W, P.CHANNEL_W, "the orange margin is constant")
    assert P.BOUNDARY_DRAFT / (P.DECK - P.POCKET_FLOOR) >= 0.25, (
        "the 0.70 mm margin needs enough draft to be a wedge, not a fin")
    assert P.MARKER_W >= 2 * P.NOZZLE, "bank marker is under two lines"
    assert P.MARKER_OUTER < P.BAR_R, "a bank marker runs off the centre bar"
    assert P.MARKER_DEPTH < P.BAR_TOP - P.DECK + 1.0, "the tick cuts through the bar"
    assert 2 * P.CORONA_TIP_MIN >= 2 * P.NOZZLE + 0.4, "a flame tip is a knife edge"
    # the outermost counter has to land wholly on its own tile
    assert P.RADII[0] + P.DROP_L / 2.0 < P.TILE_OUTER, (
        "the outermost counter overhangs the tile")
    assert P.RADII[-1] - P.DROP_L / 2.0 > P.LANE_INNER, (
        "the innermost counter overhangs the tile")


def check_tones():
    ordered = [
        ("single_beige_counter", P.SINGLE_COLOR),
        ("lane_light_yellow", P.LANE_LIGHT_COLOR),
        ("sun_body_orange", P.SUN_COLOR),
        ("lane_dark_cocoa", P.LANE_DARK_COLOR),
        ("fork_dark_brown_counter", P.FORK_COLOR),
    ]
    values = [(name, luma(colour)) for name, colour in ordered]
    for (an, av), (bn, bv) in zip(values, values[1:]):
        assert av - bv >= MIN_TONE_GAP, "%s and %s collide in value (%.3f, %.3f)" % (
            an, bn, av, bv)
    light = luma(P.LANE_LIGHT_COLOR)
    dark = luma(P.LANE_DARK_COLOR)
    body = luma(P.SUN_COLOR)
    assert light > body > dark, "the body must sit between the two lane tones"
    assert luma(P.FORK_COLOR) < dark and light < luma(P.SINGLE_COLOR)
    return dict(values)


def check_corona():
    """The separated-flame contract, measured on the plan the CAD extrudes."""
    n = P.CORONA_COUNT
    assert MIN_FLAMES <= n <= MAX_FLAMES, n
    assert len(P.CORONA_PLAN) == n, "one plan row per flame"

    # 1. the base circle is continuous and every flame lives outside it
    starts = [row[0] for row in P.CORONA_PLAN]
    assert starts == sorted(starts) and 0.0 <= starts[0] and starts[-1] < 360.0
    roots = [G.root_arc_mm(i) for i in range(n)]
    valleys = [G.valley_arc_mm(i) for i in range(n)]
    pitches = [G.pitch_arc_mm(i) for i in range(n)]
    _close(sum(pitches), 2.0 * 3.141592653589793 * P.CORONA_BASE_R,
           "the roots and valleys close the base circle")

    # 2. adjacent roots no longer touch, and no valley is a bare arc longer
    #    than either flame's own root
    for i in range(n):
        assert valleys[i] > 0.0, "flames %d and %d still touch" % (i, (i + 1) % n)
        assert valleys[i] <= min(roots[i], roots[(i + 1) % n]) + 1e-9, (
            "valley %d is a bare arc wider than a flame root" % i)
        assert roots[i] / pitches[i] <= ROOT_FRACTION_MAX + 1e-9, (
            "flame %d root is %.3f of its root-to-root arc"
            % (i, roots[i] / pitches[i]))

    # 3. lengths span more than four to one, the tall ones are a quarter of the
    #    ring, and the sequence is neither sorted, periodic nor mirrored
    rises = [G.flame_rise(i) for i in range(n)]
    assert max(rises) / min(rises) >= MIN_LENGTH_RATIO, max(rises) / min(rises)
    _close(P.CORONA_BASE_R + max(rises), P.CORONA_MAX_R, "tallest flame tip radius")
    assert len({round(v, 2) for v in rises}) == n, "two flames are one length"
    assert len(P.CORONA_TALL) * 4 == n, "the tall flames are not one in four"
    spacing = [(P.CORONA_TALL[(k + 1) % len(P.CORONA_TALL)] - P.CORONA_TALL[k]) % n
               for k in range(len(P.CORONA_TALL))]
    assert len(set(spacing)) >= 3, "the tall flames are evenly spaced"
    for k in range(1, n):
        assert max(abs(rises[i] - rises[(i + k) % n]) for i in range(n)) > 1.0, \
            "the length sequence repeats at shift %d" % k
    for k in range(n):
        assert max(abs(rises[i] - rises[(k - i) % n]) for i in range(n)) > 1.0, \
            "the length sequence mirrors about %d" % k
    run = best = 1
    for i in range(1, 2 * n):
        run = run + 1 if rises[i % n] > rises[(i - 1) % n] else 1
        best = max(best, run)
    assert best <= 5, "the lengths are sorted over a run of %d" % best

    # 4. the approved flame curve, measured on the built spine
    senses = {G.tongue_frame(i)["sense"] for i in range(n)}
    assert len(senses) == 1, "the flames do not all turn the same way"
    _close(P.CORONA_TURN_EXP, 1.15, "turn exponent")
    turns = [G.tongue_turn(i) for i in range(n)]
    assert TURN_LO <= min(t[0] for t in turns), min(t[0] for t in turns)
    assert max(t[0] for t in turns) <= TURN_HI, max(t[0] for t in turns)
    shares = [1.0 - t[1] / t[0] for t in turns]
    assert INNER_SHARE_LO <= min(shares) and max(shares) <= INNER_SHARE_HI, (
        [min(shares), max(shares)])

    # 5. blunt tips, a falling top, and nothing under the stated caps
    tips = [G.tongue_tip_thickness(i) for i in range(n)]
    assert min(tips) >= TIP_ACROSS_LO - 1e-9, min(tips)
    assert max(tips) <= TIP_ACROSS_HI + 1e-9, max(tips)
    ramps = [G.tongue_ramp(i) for i in range(n)]
    assert min(r["tip_z"] for r in ramps) >= TIP_Z_MIN, "a tip falls below 3.0"
    assert max(r["tip_z"] for r in ramps) <= 5.0, "a tip stands above 5.0"
    heights = [r["tip_z"] for r in ramps]
    assert len({round(z, 2) for z in heights}) >= 0.75 * n, \
        "the tip heights bunch onto a few values"
    assert min(abs(heights[i] - heights[(i + 1) % n]) for i in range(n)) > 0.01, \
        "two neighbouring flames share a tip height"
    assert all(r["slope"] > 0.0 for r in ramps), "a flame top does not fall"
    assert all(r["hold_mm"] == 0.0 for r in ramps), "a flame top holds before it falls"

    # 6. the envelope, and nothing inside the base circle
    xs, ys, radii = [], [], []
    for i in range(n):
        for x, y in G.tongue_face_outline(i, 48):
            xs.append(x)
            ys.append(y)
            radii.append(sqrt(x * x + y * y))
    envelope = (max(xs) - min(xs), max(ys) - min(ys))
    assert max(envelope) <= MAX_ENVELOPE, envelope
    assert min(radii) >= P.CORONA_BASE_R - 1e-6, "a flame dips inside the disc"
    return {
        "flames": n,
        "base_circle_radius_mm": P.CORONA_BASE_R,
        "root_arc_mm": [round(min(roots), 3), round(max(roots), 3)],
        "valley_arc_mm": [round(min(valleys), 3), round(max(valleys), 3)],
        "max_root_over_pitch": round(max(r / p for r, p in zip(roots, pitches)), 4),
        "max_valley_over_smaller_root": round(
            max(valleys[i] / min(roots[i], roots[(i + 1) % n]) for i in range(n)), 4),
        "flame_rise_mm": [round(min(rises), 3), round(max(rises), 3)],
        "flame_length_ratio": round(max(rises) / min(rises), 3),
        "tall_flames": len(P.CORONA_TALL),
        "turn_root_to_tip_deg": [round(min(t[0] for t in turns), 2),
                                 round(max(t[0] for t in turns), 2)],
        "turn_share_in_the_inner_half": round(sum(shares) / n, 4),
        "tip_cap_across_mm": [round(min(tips), 3), round(max(tips), 3)],
        "tip_height_mm": [round(min(r["tip_z"] for r in ramps), 3),
                          round(max(r["tip_z"] for r in ramps), 3)],
        "envelope_mm": [round(envelope[0], 3), round(envelope[1], 3)],
        "closed_loops": 0,
    }


def check_locating_key():
    """The key stays under its tile seat and out of every counter region."""
    half_l = P.KEY_L / 2.0 + P.KEY_W / 2.0 + P.KEY_CLEAR
    half_w = P.KEY_W / 2.0 + P.KEY_CLEAR
    lo_y = P.KEY_OFFSET - half_w
    assert lo_y > P.DROP_W / 2.0 + 1.0, "the key reaches a counter landing region"
    margin = None
    for point in range(1, P.LANES + 1):
        seat = G.sector_profile(point, P.LANE_INNER, P.SEAT_OUTER, P.CLEAR)
        angle = G.theta(point)
        for dx in (-half_l, half_l):
            for dy in (-half_w, half_w):
                lx, ly = P.KEY_R + dx, P.KEY_OFFSET + dy
                wx = lx * cos(radians(angle)) - ly * sin(radians(angle))
                wy = lx * sin(radians(angle)) + ly * cos(radians(angle))
                assert _point_in_polygon((wx, wy), seat), (point, lx, ly)
        clearance = lo_y - P.DROP_W / 2.0
        margin = clearance if margin is None else min(margin, clearance)
    return {"key_to_landing_clearance_mm": round(margin, 3)}


def check():
    check_heights()
    check_fit_chain()
    report = {"tone_luma": check_tones()}
    report.update(check_corona())
    report.update(check_locating_key())
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(check(), indent=2, sort_keys=True))
