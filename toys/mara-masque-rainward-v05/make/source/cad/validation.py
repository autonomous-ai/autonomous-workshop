"""Algebraic parameter checks. These run before any geometry is built."""
from math import cos, degrees, radians, sin, sqrt

import params as P
import profiles as G

TOL = 1e-9
LUMA = (0.2126, 0.7152, 0.0722)
MIN_TONE_GAP = 0.09          # separation required between neighbouring values
MIN_TONGUES, MAX_TONGUES = 32, 44
MIN_ROOT_MM = 6.0            # narrowest tongue root the Wish allows
MIN_ROOT_SHARE = 0.60        # root width as a share of that tongue's length
MIN_DEEP_TROUGHS = 5         # troughs that must reach 9 mm of flame depth


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
    _close(P.LANE_TOP - P.DECK, 0.8, "tile proud of the body")
    _close(P.BAR_TOP - P.LANE_TOP, 0.2, "centre bar above the lane tops")
    _close(P.MARKER_TOP, P.BAR_TOP, "marker maximum")
    _close(P.GAP_FLOOR, 8.0, "gap floor")
    _close(P.SUN_H, 9.0, "overall Sun height")
    layers = [P.LANE_TOP + i * P.DROP_H for i in range(3)]
    assert layers == [8.8, 12.8, 16.8], layers
    assert P.POCKET_FLOOR - P.KEY_RECESS_D > 3.0, "deepest pocket would thin the deck"


def check_fit_chain():
    _close(P.POCKET_INNER, P.LANE_INNER - P.CLEAR, "pocket inner clearance")
    _close(P.TILE_OUTER, P.SUN_R - P.CLEAR, "tile outer clearance")
    _close(P.KEY_RECESS_D - P.KEY_H, 0.2, "key bottom clearance")
    assert P.KEY_CLEAR == P.CLEAR, "one clearance value for the whole seat"
    _close(P.LIP_T, P.LANE_TOP - P.RIM_TOP, "tile lip thickness")
    assert P.LIP_T >= 2 * P.NOZZLE + 0.2, "tile lip is too close to the wall limit"
    assert P.SUN_R - P.RIM_INNER >= 2.0, "rim ring is too narrow to carry the lips"
    assert P.CHANNEL_W >= 2 * P.NOZZLE, "ordinary boundary body is under two lines"
    assert P.MARKER_W >= 2 * P.NOZZLE, "marker is under two lines"
    assert 2 * P.CORONA_TIP_MIN >= 2 * P.NOZZLE + 0.4, "corona tip is a knife edge"
    assert 2 * P.HERO_HALF >= 2 * P.NOZZLE + 0.4, "the hero band is a knife edge"
    assert min(r for _, r, _ in P.CORONA_TROUGHS) - P.RIM_INNER >= 2.0, \
        "a trough floor leaves too little body over the pocket wall"
    # the marker keeps clear of both neighbouring tiles inside the wide boundary
    side = (P.BANK_W - P.MARKER_W) / 2.0 + P.CLEAR
    assert side >= 0.5, side


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
    # both lane tones must stay between the two counter values
    light = luma(P.LANE_LIGHT_COLOR)
    dark = luma(P.LANE_DARK_COLOR)
    body = luma(P.SUN_COLOR)
    assert light > body > dark, "one lane tone lighter, one darker than the body"
    assert luma(P.FORK_COLOR) < dark and light < luma(P.SINGLE_COLOR)
    return dict(values)


def _tongue_lengths():
    n = P.CORONA_COUNT
    return [P.CORONA_TIPS[i]
            - 0.5 * (P.CORONA_TROUGHS[i][1] + P.CORONA_TROUGHS[(i + 1) % n][1])
            for i in range(n)]


def check_corona():
    """The skirt contract: unbroken, uneven, broad-rooted, and one hero loop."""
    n = P.CORONA_COUNT
    assert MIN_TONGUES <= n <= MAX_TONGUES, n
    assert len(P.CORONA_TIPS) == n, "one tip radius per tongue"

    angles = [a for a, _, _ in P.CORONA_TROUGHS]
    assert angles == sorted(angles) and 0.0 <= angles[0] and angles[-1] < 360.0
    gaps = [(angles[(i + 1) % n] - angles[i]) % 360.0 for i in range(n)]
    assert min(gaps) >= 6.0, "two troughs are closer than one root width"
    assert max(gaps) <= 17.5, "a tongue spans more than one and a half lanes"
    assert max(gaps) - min(gaps) >= 4.0, "the trough rhythm reads as regular"

    # a trough that cuts inside the tile edge also notches that tile, so it has
    # to sit on a lane boundary where no outer counter has any footprint
    for angle, radius, _ in P.CORONA_TROUGHS:
        if radius < P.CORONA_NOTCH_LIMIT:
            offset = (angle - (P.START_ANGLE - P.PITCH / 2.0)) % P.PITCH
            offset = min(offset, P.PITCH - offset)
            assert offset <= P.CORONA_NOTCH_WINDOW, (
                "trough at %.2f cuts a tile under a counter" % angle)

    lengths = _tongue_lengths()
    assert min(lengths) > 0.0, "a tongue does not reach past its own troughs"
    assert max(lengths) / min(lengths) >= 2.0, "tongue lengths barely vary"
    assert len({round(v, 2) for v in lengths}) == n, "two tongues are one length"
    for k in range(1, n):
        assert max(abs(lengths[i] - lengths[(i + k) % n]) for i in range(n)) > 1.0, \
            "the length sequence repeats at shift %d" % k
    for k in range(n):
        assert max(abs(lengths[i] - lengths[(k - i) % n]) for i in range(n)) > 1.0, \
            "the length sequence mirrors about %d" % k
    run = best = 1
    for i in range(1, 2 * n):
        run = run + 1 if lengths[i % n] > lengths[(i - 1) % n] else 1
        best = max(best, run)
    assert best <= 5, "the lengths are sorted over a run of %d" % best

    roots = []
    max_radius = 0.0
    xs, ys = [], []
    for i in range(n):
        frame = G.tongue_frame(i)
        roots.append(frame["root_width"])
        assert frame["root_width"] >= MIN_ROOT_MM, (
            "tongue %d has a %.2f mm root" % (i, frame["root_width"]))
        assert frame["root_width"] >= MIN_ROOT_SHARE * lengths[i], (
            "tongue %d is narrower than its own length allows" % i)
        assert frame["span"] > 0.0, "tongue %d has no span" % i
        max_radius = max(max_radius, frame["tip_radius"])
    assert len({round(r, 3) for r in roots}) == n, "two tongues share a root width"
    assert max_radius <= P.CORONA_MAX_R + 1e-9, max_radius

    # every tongue turns the same way round the ring, and the hero crest
    # leans with them
    assert P.HERO_SKEW > 1.0, "the hero crest must lean the way tongues do"
    assert P.HERO_DOME < 1.0, "the hero crest must be domed, not flat"
    senses = {G.tongue_frame(i)["sense"] for i in range(n)}
    assert len(senses) == 1, "the tongues do not all turn the same way"

    # the Wish's three shape clauses, measured on the built plan and ramp
    turns = [G.tongue_turn(i) for i in range(n)]
    assert min(t[0] for t in turns) >= 25.0, min(t[0] for t in turns)
    assert max(t[0] for t in turns) <= 45.0, max(t[0] for t in turns)
    assert min(t[1] for t in turns) >= 20.0, min(t[1] for t in turns)
    assert min(G.tongue_tip_thickness(i) for i in range(n)) >= 1.3, "tip too thin"
    widths = [G.tongue_mid_width(i) / G.tongue_frame(i)["root_width"]
              for i in range(n)]
    assert max(widths) <= 0.5, "the outer half is not slender at mid length"
    ramps = [G.tongue_ramp(i) for i in range(n)]
    assert min(r["tip_z"] for r in ramps) >= 3.5, "a tip falls below 3.5"
    assert max(r["tip_z"] for r in ramps) <= 5.0, "a tip stays above 5.0"
    assert len({round(r["tip_z"], 3) for r in ramps}) == n, \
        "two tongues share a tip height"
    assert all(r["slope"] > 0.0 for r in ramps), "a tongue top does not fall"
    assert all(r["axial_max_mm"] > r["hold_mm"] for r in ramps), "a tongue has no ramp"

    depths = [max(P.CORONA_TIPS[i], P.CORONA_TIPS[(i - 1) % n])
              - P.CORONA_TROUGHS[i][1] for i in range(n)]
    assert sum(1 for d in depths if d >= 9.0) >= MIN_DEEP_TROUGHS, sorted(depths)[-6:]

    for x, y in G.skirt_outline() + G.hero_profile():
        xs.append(x)
        ys.append(y)
        max_radius = max(max_radius, sqrt(x * x + y * y))
    envelope = (max(xs) - min(xs), max(ys) - min(ys))
    assert max(envelope) <= 194.0 - 0.5, envelope
    return {"max_radius_mm": round(max_radius, 3),
            "envelope_mm": [round(envelope[0], 3), round(envelope[1], 3)],
            "tongue_count": n,
            "min_root_width_mm": round(min(roots), 3),
            "tongue_length_mm": [round(min(lengths), 3), round(max(lengths), 3)],
            "deepest_flame_depth_mm": round(max(depths), 3),
            "troughs_at_or_over_9mm": sum(1 for d in depths if d >= 9.0),
            "min_tip_thickness_mm": 2 * P.CORONA_TIP_MIN,
            "tongue_turn_deg": [round(min(t[0] for t in turns), 2),
                                round(max(t[0] for t in turns), 2)],
            "tongue_outer_half_turn_deg": [round(min(t[1] for t in turns), 2),
                                           round(max(t[1] for t in turns), 2)],
            "tongue_tip_height_mm": [round(min(r["tip_z"] for r in ramps), 2),
                                     round(max(r["tip_z"] for r in ramps), 2)],
            "tongue_mid_width_over_root": round(max(widths), 3)}


def check_locating_key():
    """The key stays under its tile and out of every counter landing region."""
    half_l = P.KEY_L / 2.0 + P.KEY_W / 2.0 + P.KEY_CLEAR
    half_w = P.KEY_W / 2.0 + P.KEY_CLEAR
    lo_y = P.KEY_OFFSET - half_w
    assert lo_y > P.DROP_W / 2.0 + 1.0, "the key reaches a counter landing region"
    margin = None
    for point in range(1, P.LANES + 1):
        tile = G.sector_profile(point, P.LANE_INNER, P.TILE_OUTER, P.CLEAR)
        angle = G.theta(point)
        for dx in (-half_l, half_l):
            for dy in (-half_w, half_w):
                lx, ly = P.KEY_R + dx, P.KEY_OFFSET + dy
                wx = lx * cos(radians(angle)) - ly * sin(radians(angle))
                wy = lx * sin(radians(angle)) + ly * cos(radians(angle))
                assert _point_in_polygon((wx, wy), tile), (point, lx, ly)
        clearance = lo_y - P.DROP_W / 2.0
        margin = clearance if margin is None else min(margin, clearance)
    return {"key_to_landing_clearance_mm": margin}


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
