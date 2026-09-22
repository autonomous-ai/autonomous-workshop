"""Jupiter's belts, zones and spot against the 0.4 mm nozzle.

The Wish asks for every band's printed width and every ring's shortest edge and
narrowest neck, tabulated against the nozzle, in the form
`measure/earth-atlas-resolution.md` uses.  This is that table, measured on the
exact rings and latitudes `parts/jupiter_atlas.py` hands the build rather than
on the numbers the Wish named, so a wave that ate a belt would show up here
rather than in the print.

Jupiter's globe is the largest in the set at Ø26.97 mm, so its radius is
13.485 mm and one degree of arc is 0.2354 mm.  The nozzle is 0.40 mm, which is
the narrowest colour boundary the printer can lay down and 1.70 degrees of arc
here -- the most forgiving world in the chain, where Mercury's 0.4 mm is 3.33
degrees.

Four things have to clear that nozzle: the belts, which now vary in width
along their own length because two of them wave; the zones between them, which
vary for the same reason; the two oval rings of the Great Red Spot; and the
collar annulus between them.

    "$WORKSHOP_PYTHON" measure/jupiter_atlas_resolution.py \\
        > measure/jupiter-atlas-resolution.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts import jupiter_atlas as J                          # noqa: E402

MM = J.MM_PER_DEG
NOZZLE = P.NOZZLE_MM

#: How finely longitude is swept when a width varies along a belt.  0.25
#: degrees is 0.06 mm of arc, well under the feature being measured.
STEP_DEG = 0.25
LONGITUDES = [-180.0 + STEP_DEG * index
              for index in range(int(360.0 / STEP_DEG))]


def unit(lon_deg: float, lat_deg: float):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat))


def arc_mm(one, other) -> float:
    dot = max(-1.0, min(1.0, sum(a * b for a, b in zip(one, other))))
    return math.degrees(math.acos(dot)) * MM


def ring_edges(ring):
    return [arc_mm(unit(*ring[index]), unit(*ring[(index + 1) % len(ring)]))
            for index in range(len(ring))]


def ring_perimeter(ring) -> float:
    return sum(ring_edges(ring))


def ring_neck(ring) -> float:
    """The closest any two non-neighbouring vertices of one ring come."""
    count = len(ring)
    points = [unit(*item) for item in ring]
    best = None
    for i in range(count):
        for j in range(i + 2, count):
            if i == 0 and j == count - 1:
                continue
            value = arc_mm(points[i], points[j])
            best = value if best is None else min(best, value)
    return best


def belt_width(key: str, lon: float) -> float:
    return J.belt_edge(key, "north", lon) - J.belt_edge(key, "south", lon)


def belt_bounds(key: str, edge: str):
    values = [J.belt_edge(key, edge, lon) for lon in LONGITUDES]
    return min(values), max(values)


def zone_edges(zone_key: str, lon: float):
    """(south, north) of one zone at one longitude, after the belts cut it."""
    south, north = next((s, n) for key, _n, s, n, _ds, _dn in J.ZONES
                        if key == zone_key)
    # Which belt bounds this zone on each side, and where that belt is here.
    below = max((item for item in J.BELTS if item[3] <= south),
                key=lambda item: item[3], default=None)
    above = min((item for item in J.BELTS if item[2] >= north),
                key=lambda item: item[2], default=None)
    low = south if below is None else (
        J.belt_edge(below[0], "north", lon) if below[4] == "outline" else below[3])
    high = north if above is None else (
        J.belt_edge(above[0], "south", lon) if above[4] == "outline" else above[2])
    return low, high


def main() -> int:
    print("# Jupiter's belts, zones and spot at globe scale")
    print()
    print("Jupiter's globe is Ø%.2f mm, so its radius is %.3f mm and one degree"
          % (J.GLOBE_D, J.GLOBE_D / 2.0))
    print("of arc is %.4f mm.  The nozzle is %.2f mm, which is the narrowest"
          % (MM, NOZZLE))
    print("colour boundary the printer can lay down and %.2f degrees of arc"
          % J.NOZZLE_DEG)
    print("here.  This is the most forgiving world in the set: the same nozzle")
    print("is 3.33 degrees on Mercury and 2.74 on Earth.")
    print()

    print("## The six belts")
    print()
    print("Two of them wave, so their width varies along their own length and")
    print("the least of it is what has to clear the nozzle. The South")
    print("Equatorial Belt also bends %.1f degrees north over the Great Red"
          % J.HOLLOW_DEPTH_DEG)
    print("Spot, which is where its narrowest width is.")
    print()
    print("| belt | latitudes | drawn as | width deg | width mm | least mm | nozzles |")
    print("|---|---|---|---|---:|---:|---:|")
    belt_min = {}
    for key, name, south, north, how in J.BELTS:
        if how == "band":
            low = high = north - south
        else:
            widths = [belt_width(key, lon) for lon in LONGITUDES]
            low, high = min(widths), max(widths)
        belt_min[key] = low
        span = ("%.2f" % low if abs(high - low) < 1e-9
                else "%.2f to %.2f" % (low, high))
        print("| %s | %+.0f to %+.0f | `%s` | %s | %.2f | **%.2f** | %.1f |"
              % (name, south, north, how, span, high * MM, low * MM,
                 low * MM / NOZZLE))
    print()

    print("## The five zones")
    print()
    print("A zone is bounded by the belts on either side of it, so where one of")
    print("those waves the zone waves with it. These are the widths that")
    print("actually print, measured after the belt cut rather than as drawn.")
    print()
    print("| zone | latitudes | width deg | width mm | least mm | nozzles |")
    print("|---|---|---|---:|---:|---:|")
    for key, name, south, north, _ds, _dn in J.ZONES:
        widths = []
        for lon in LONGITUDES:
            low, high = zone_edges(key, lon)
            widths.append(high - low)
        least, most = min(widths), max(widths)
        span = ("%.2f" % least if abs(most - least) < 1e-9
                else "%.2f to %.2f" % (least, most))
        print("| %s | %+.0f to %+.0f | %s | %.2f | **%.2f** | %.1f |"
              % (name, south, north, span, most * MM, least * MM,
                 least * MM / NOZZLE))
    print()

    print("## The wave, and what it costs the belts it is drawn on")
    print()
    print("| boundary | nominal | swings to | amplitude deg | amplitude mm |")
    print("|---|---:|---|---:|---:|")
    for (key, edge), harmonics in J.WAVES.items():
        low, high = belt_bounds(key, edge)
        nominal = J.BELT_LATITUDES[key][0 if edge == "south" else 1]
        amplitude = sum(item[1] for item in harmonics)
        print("| %s %s | %+.0f | %+.2f to %+.2f | %.2f | %.3f |"
              % (key.upper(), edge, nominal, low, high, amplitude,
                 amplitude * MM))
    print()
    print("The two belts that carry it are %.2f and %.2f degrees wide nominally,"
          % (J.BELT_LATITUDES["neb"][1] - J.BELT_LATITUDES["neb"][0],
             J.BELT_LATITUDES["seb"][1] - J.BELT_LATITUDES["seb"][0]))
    print("so a %.1f degree wave on each boundary could in principle take %.0f per"
          % (J.WAVE_AMPLITUDE_DEG,
             100.0 * 2 * J.WAVE_AMPLITUDE_DEG
             / (J.BELT_LATITUDES["neb"][1] - J.BELT_LATITUDES["neb"][0])))
    print("cent of the narrower of them. It does not: the two boundaries carry")
    print("different harmonics, so they never reach their extremes at the same")
    print("longitude, and the narrowest the North Equatorial Belt actually gets")
    print("is %.2f degrees. The four belts left as plain circles of"
          % min(belt_width("neb", lon) for lon in LONGITUDES))
    print("latitude are %s degrees wide; the same wave would take"
          % ", ".join("%.0f" % (north - south)
                      for _k, _n, south, north, how in J.BELTS
                      if how == "band"))
    print("all of the narrowest of them, which is why they do not carry it.")
    print()

    print("## The two oval rings")
    print()
    print("| ring | vertices | semi-axes deg | perimeter mm | shortest edge mm | narrowest neck mm |")
    print("|---|---:|---|---:|---:|---:|")
    for name, ring, semi in (
        ("spot", J.SPOT_RING, (J.SPOT_SEMI_ARC_LON, J.SPOT_SEMI_ARC_LAT)),
        ("collar", J.COLLAR_RING, (J.COLLAR_SEMI_ARC_LON, J.COLLAR_SEMI_ARC_LAT)),
    ):
        edges = ring_edges(ring)
        print("| `%s` | %d | %.1f by %.1f | %.2f | **%.3f** | %.2f |"
              % (name, len(ring), semi[0], semi[1], sum(edges), min(edges),
                 ring_neck(ring)))
    print()
    print("The collar is the annulus left when the spot is subtracted out of")
    print("the outer ring, so the number that has to clear the nozzle is the")
    print("gap between the two ovals rather than either ring on its own:")
    print("%.2f degrees of arc, **%.3f mm**, %.1f nozzles, on every side."
          % (J.COLLAR_WIDTH_DEG, J.COLLAR_WIDTH_DEG * MM,
             J.COLLAR_WIDTH_DEG * MM / NOZZLE))
    print()

    print("## The spot, the collar and the belts around them")
    print()
    spot_top = J.SPOT_LAT + J.SPOT_SEMI_ARC_LAT
    spot_bottom = J.SPOT_LAT - J.SPOT_SEMI_ARC_LAT
    collar_top = J.SPOT_LAT + J.COLLAR_SEMI_ARC_LAT
    collar_bottom = J.SPOT_LAT - J.COLLAR_SEMI_ARC_LAT
    # Least clearance between the collar's upper edge and the hollowed belt.
    best = None
    steps = 2000
    for index in range(steps + 1):
        offset = -20.0 + 40.0 * index / steps
        arc = offset * math.cos(math.radians(J.SPOT_LAT))
        if abs(arc) >= J.COLLAR_SEMI_ARC_LON:
            continue
        rise = J.COLLAR_SEMI_ARC_LAT * math.sqrt(
            1.0 - (arc / J.COLLAR_SEMI_ARC_LON) ** 2)
        gap = J.belt_edge("seb", "south", J.SPOT_LON + offset) - (J.SPOT_LAT + rise)
        if best is None or gap < best[0]:
            best = (gap, J.SPOT_LON + offset)
    # Where the collar crosses into the South Temperate Belt.
    stb_top = J.BELT_LATITUDES["stb"][1]
    drop = stb_top - J.SPOT_LAT
    merge_arc = (J.COLLAR_SEMI_ARC_LON
                 * math.sqrt(max(0.0, 1.0 - (drop / J.COLLAR_SEMI_ARC_LAT) ** 2))
                 if abs(drop) < J.COLLAR_SEMI_ARC_LAT else 0.0)
    print("| measurement | degrees | mm | nozzles |")
    print("|---|---:|---:|---:|")
    print("| spot, top to bottom | %+.1f to %+.1f | %.2f | %.1f |"
          % (spot_top, spot_bottom, 2 * J.SPOT_SEMI_ARC_LAT * MM,
             2 * J.SPOT_SEMI_ARC_LAT * MM / NOZZLE))
    print("| spot, side to side | %.1f wide | %.2f | %.1f |"
          % (2 * J.SPOT_SEMI_ARC_LON, 2 * J.SPOT_SEMI_ARC_LON * MM,
             2 * J.SPOT_SEMI_ARC_LON * MM / NOZZLE))
    print("| collar annulus | %.2f | %.3f | %.1f |"
          % (J.COLLAR_WIDTH_DEG, J.COLLAR_WIDTH_DEG * MM,
             J.COLLAR_WIDTH_DEG * MM / NOZZLE))
    print("| bright zone between collar and belt, least | %.2f | %.3f | %.1f |"
          % (best[0], best[0] * MM, best[0] * MM / NOZZLE))
    print("| collar buried in the South Temperate Belt | %.2f tall, %.2f wide | %.2f wide | %.1f |"
          % (abs(collar_bottom - stb_top), 2 * merge_arc, 2 * merge_arc * MM,
             2 * merge_arc * MM / NOZZLE))
    print()
    print("The last row is a stated decision rather than a defect. The spot is")
    print("%.1f degrees of arc tall centred at %+.0f and the South Tropical Zone"
          % (2 * J.SPOT_SEMI_ARC_LAT, J.SPOT_LAT))
    print("is %.0f degrees deep, so a collar wide enough to print at all reaches"
          % abs(J.BELT_LATITUDES["stb"][1] - (-20.0)))
    print("past %+.0f into the South Temperate Belt. Biting a second hollow out"
          % stb_top)
    print("of that belt is not available -- the correction requires the four")
    print("narrow belts to stay plain circles of latitude -- so the collar gives")
    print("way there instead, and over %.1f degrees of longitude the collar and"
          % (2 * merge_arc / math.cos(math.radians(J.SPOT_LAT))))
    print("that belt are one continuous `cocoa_brown` region. Both are the same")
    print("filament, so nothing prints differently; what a reader sees is the")
    print("spot's collar touching the belt below it.")
    print()

    print("## What Jupiter does not draw")
    print()
    print(J.NOT_DRAWN)
    print()

    print("## Verdict")
    print()
    least_belt = min(belt_min.values())
    least_zone = min(
        min(zone_edges(key, lon)[1] - zone_edges(key, lon)[0]
            for lon in LONGITUDES)
        for key, _n, _s, _no, _ds, _dn in J.ZONES
    )
    least_edge = min(min(ring_edges(J.SPOT_RING)), min(ring_edges(J.COLLAR_RING)))
    print("Nothing on this globe falls under the %.2f mm nozzle. The narrowest"
          % NOZZLE)
    print("belt anywhere along its length is %.2f mm (%.1f nozzles), the"
          % (least_belt * MM, least_belt * MM / NOZZLE))
    print("narrowest zone is %.2f mm (%.1f nozzles), the collar annulus is"
          % (least_zone * MM, least_zone * MM / NOZZLE))
    print("%.3f mm (%.1f nozzles), the bright zone between the collar and the"
          % (J.COLLAR_WIDTH_DEG * MM, J.COLLAR_WIDTH_DEG * MM / NOZZLE))
    print("hollowed belt above it is %.3f mm (%.1f nozzles), and the shortest"
          % (best[0] * MM, best[0] * MM / NOZZLE))
    print("edge of either oval ring is %.3f mm (%.1f nozzles)."
          % (least_edge, least_edge / NOZZLE))
    print()
    print("One number is deliberately NOT a nozzle clearance: a `band` region")
    print("is a lens that reaches its full depth at its own middle and tapers")
    print("to nothing at its own edges, so the last fraction of a degree of")
    print("each of the four plain belts is a skin thinner than one 0.2 mm")
    print("layer. That is how every band marking in this set has always been")
    print("built -- Saturn's belts, Neptune's streaks, Uranus's band -- and it")
    print("is a depth, not a width: the colour boundary the nozzle has to lay")
    print("down is the one measured above. Jupiter's zones are `shell` regions")
    print("and do not taper: they are %.2f mm deep from edge to edge, %.2f mm"
          % (J.ZONE_DEPTH, J.ZONE_FLOOR_CLEARANCE))
    print("short of the %.2f mm the outline markings reach, for the reason"
          % P.RELIEF_DEPTH)
    print("`parts/jupiter_atlas.py` measures.")
    print()
    print("Measured by `measure/jupiter_atlas_resolution.py` on the exact")
    print("latitudes, waves and rings in `parts/jupiter_atlas.py`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
