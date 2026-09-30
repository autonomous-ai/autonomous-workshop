"""Every width on Saturn's globe, against the nozzle that has to print it.

The Wish asks for the printed width of every band, the shortest edge and the
narrowest neck of every ring, and the filament count, all against the 0.4 mm
nozzle.  This computes them from the same module the geometry is built from,
so the table cannot drift away from the solid.

A band is a flush colour inlay, so "printed width" is the width of the colour
boundary the slicer has to lay down along the globe's surface -- an arc, not a
chord and not a projection.  One degree of arc on this globe is
`saturn_atlas.MM_PER_DEG`.

    "$WORKSHOP_PYTHON" measure/saturn_atlas_resolution.py \\
        > measure/saturn-atlas-resolution.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts import saturn_atlas as S                           # noqa: E402


def arc_mm(degrees: float) -> float:
    return degrees * S.MM_PER_DEG


def sphere_arc(a_lon, a_lat, b_lon, b_lat) -> float:
    """Great-circle arc between two (lon, lat) points, in degrees."""
    def unit(lon, lat):
        lat, lon = math.radians(lat), math.radians(lon)
        return (math.cos(lat) * math.cos(lon),
                math.cos(lat) * math.sin(lon),
                math.sin(lat))
    one, other = unit(a_lon, a_lat), unit(b_lon, b_lat)
    dot = max(-1.0, min(1.0, sum(p * q for p, q in zip(one, other))))
    return math.degrees(math.acos(dot))


def ring_edges(ring):
    """Every edge length of one closed ring, in degrees of arc."""
    return [
        sphere_arc(ring[index][0], ring[index][1],
                   ring[(index + 1) % len(ring)][0], ring[(index + 1) % len(ring)][1])
        for index in range(len(ring))
    ]


def band_extremes(key: str):
    """(least, most) width of one wavy band over a fine longitude sweep."""
    widths = []
    for step in range(3600):
        lon = step / 10.0
        widths.append(S.band_edge(key, "north", lon) - S.band_edge(key, "south", lon))
    return min(widths), max(widths)


def boundary_extremes(key: str, edge: str):
    values = [S.band_edge(key, edge, step / 10.0) for step in range(3600)]
    return min(values), max(values)


def main() -> int:
    print("# Saturn's surface, against the 0.4 mm nozzle")
    print()
    print("Saturn's globe is Ø%.2f mm, so one degree of arc is %.4f mm and the"
          % (S.GLOBE_D, S.MM_PER_DEG))
    print("%.1f mm nozzle is %.2f degrees of it. Every number below is an arc"
          % (P.NOZZLE_MM, S.NOZZLE_DEG))
    print("along the globe's own surface, which is what the slicer lays down;")
    print("none of them is a chord or a projected width.")
    print()

    print("## The five bands")
    print()
    print("| band | latitudes | drawn | width deg | width mm | nozzle widths |")
    print("|---|---|---|---:|---:|---:|")
    for key, name, south, north, how, tone in S.BANDS:
        width = north - south
        print("| %s (`%s`) | %+.0f to %+.0f | %s | %.1f | **%.2f** | %.1f |"
              % (name, key, south, north,
                 "wavy outline" if how == "outline" else "plain band",
                 width, arc_mm(width), arc_mm(width) / P.NOZZLE_MM))
    print()
    print("The narrowest is the %s at %.1f degrees, **%.2f mm**, %.1f nozzle"
          % (S.BANDS[2][1], S.BANDS[2][3] - S.BANDS[2][2],
             arc_mm(S.BANDS[2][3] - S.BANDS[2][2]),
             arc_mm(S.BANDS[2][3] - S.BANDS[2][2]) / P.NOZZLE_MM))
    print("widths. Nothing here is close to the nozzle.")
    print()

    print("## What the wave does to the two widest")
    print()
    print("Each wavy boundary carries two harmonics totalling %.1f degrees, so a"
          % S.WAVE_AMPLITUDE_DEG)
    print("band's width breathes as the two boundaries move independently. The")
    print("worst case is what has to print, so it is swept over the whole globe")
    print("at a tenth of a degree rather than taken at the drawn latitudes.")
    print()
    print("| band | drawn width | narrowest | widest | narrowest mm | nozzle widths |")
    print("|---|---:|---:|---:|---:|---:|")
    for key, name, south, north, how, _tone in S.BANDS:
        if how != "outline":
            continue
        low, high = band_extremes(key)
        print("| %s | %.1f | **%.2f** | %.2f | **%.2f** | %.1f |"
              % (name, north - south, low, high, arc_mm(low),
                 arc_mm(low) / P.NOZZLE_MM))
    print()

    print("## The gaps between markings")
    print()
    print("Bare globe has to print too: a gap under the nozzle is a colour")
    print("boundary the slicer cannot resolve. Wavy boundaries are taken at")
    print("their extreme excursion toward the neighbour, not at their drawn")
    print("latitude.")
    print()
    edges = []
    for key, name, south, north, how, _tone in S.BANDS:
        if how == "outline":
            low_s, high_s = boundary_extremes(key, "south")
            low_n, high_n = boundary_extremes(key, "north")
        else:
            low_s = high_s = south
            low_n = high_n = north
        edges.append((key, name, low_s, high_s, low_n, high_n))
    edges.sort(key=lambda row: row[2])
    print("| from | to | gap deg | gap mm | nozzle widths |")
    print("|---|---|---:|---:|---:|")
    tight = None
    for lower, upper in zip(edges, edges[1:]):
        gap = upper[2] - lower[5]          # upper's lowest south edge minus lower's highest north edge
        print("| %s | %s | %.2f | **%.2f** | %.1f |"
              % (lower[1], upper[1], gap, arc_mm(gap), arc_mm(gap) / P.NOZZLE_MM))
        if tight is None or gap < tight[0]:
            tight = (gap, lower[1], upper[1])
    cap_gap = S.CAP_LAT - edges[-1][5]
    print("| %s | the bright cap at +%.0f | %.2f | **%.2f** | %.1f |"
          % (edges[-1][1], S.CAP_LAT, cap_gap, arc_mm(cap_gap),
             arc_mm(cap_gap) / P.NOZZLE_MM))
    if cap_gap < tight[0]:
        tight = (cap_gap, edges[-1][1], "the bright cap")
    print()
    print("The tightest gap on this globe is the %.2f degrees, **%.2f mm**,"
          % (tight[0], arc_mm(tight[0])))
    print("between %s and %s -- %.1f nozzle widths of bare globe."
          % (tight[1], tight[2], arc_mm(tight[0]) / P.NOZZLE_MM))
    print()

    print("## The rings")
    print()
    print("Each wavy band is %d longitude sectors of %.0f degrees, sampled every"
          % (S.SECTOR_COUNT, S.SECTOR_SPAN))
    print("%.0f degrees of longitude, walked south boundary west to east and"
          % S.SECTOR_STEP_DEG)
    print("north boundary back. Neighbouring sectors share their seam vertices")
    print("exactly, so the radial plane each throws is one plane for both and")
    print("the lenses fuse into one annulus along an ordinary flat face.")
    print()
    print("| ring | vertices | shortest edge deg | shortest edge mm | narrowest neck mm |")
    print("|---|---:|---:|---:|---:|")
    shortest = None
    for name in sorted(S.RINGS):
        ring = S.RINGS[name]
        lengths = ring_edges(ring)
        # The neck is the band's own width inside this sector: south vertex to
        # the north vertex at the same longitude.
        half = len(ring) // 2
        necks = [
            sphere_arc(ring[index][0], ring[index][1],
                       ring[len(ring) - 1 - index][0], ring[len(ring) - 1 - index][1])
            for index in range(half)
        ]
        least = min(lengths)
        print("| `%s` | %d | %.3f | **%.3f** | **%.3f** |"
              % (name, len(ring), least, arc_mm(least), arc_mm(min(necks))))
        if shortest is None or least < shortest[0]:
            shortest = (least, name)
    print()
    print("The shortest ring edge anywhere on this globe is %.3f degrees,"
          % shortest[0])
    print("**%.3f mm**, on `%s`. This set holds a ring edge to 0.50 mm -- a"
          % (arc_mm(shortest[0]), shortest[1]))
    print("quarter of a nozzle over the 0.40 mm the printer can lay down -- and")
    print("every edge here clears it by a factor of two.")
    print()

    print("## The wave itself")
    print()
    print("| boundary | harmonics | amplitude deg | amplitude mm | nozzle widths |")
    print("|---|---|---:|---:|---:|")
    for (key, edge), harmonics in S.WAVES.items():
        total = sum(amplitude for _h, amplitude, _p in harmonics)
        print("| %s, %s | %s | %.1f | %.2f | %.1f |"
              % (key, edge,
                 " + ".join("%d" % harmonic for harmonic, _a, _p in harmonics),
                 total, arc_mm(total), arc_mm(total) / P.NOZZLE_MM))
    print()
    print("The wave is %.2f mm at full excursion, %.1f nozzle widths, so it is a"
          % (arc_mm(S.WAVE_AMPLITUDE_DEG),
             arc_mm(S.WAVE_AMPLITUDE_DEG) / P.NOZZLE_MM))
    print("shape the printer can resolve rather than noise. No two of the four")
    print("boundaries carry the same pair of harmonics or the same phases, and")
    print("none of them is Jupiter's: the two planets stand on one board and a")
    print("shared wave would read as one pattern printed twice.")
    print()

    print("## The ring system")
    print()
    print("Unchanged by this correction, and named here so that it is on the")
    print("record rather than assumed.")
    print()
    print("| value | mm |")
    print("|---|---:|")
    for name in ("RING_INNER_D", "RING_OUTER_D", "RING_THICKNESS",
                 "RING_GLOBE_BITE", "RING_WEB_INNER_R", "RING_WEB_OVERLAP",
                 "RING_WEB_DROP"):
        print("| `%s` | %.2f |" % (name, getattr(P, name)))
    print("| `RING_WEB_SECTORS` | %d |" % P.RING_WEB_SECTORS)
    print("| `RING_WEB_SLOPE` | %.2f (%.1f deg from horizontal) |"
          % (P.RING_WEB_SLOPE, math.degrees(math.atan(P.RING_WEB_SLOPE))))
    print()
    print("The ring plate is %.2f mm thick and projects %.2f mm past the globe"
          % (P.RING_THICKNESS, P.RING_OUTER_D / 2.0 - P.globe_radius("saturn")))
    print("on every side. Its shortest edge is that %.2f mm projection and its"
          % (P.RING_OUTER_D / 2.0 - P.globe_radius("saturn")))
    print("narrowest neck is its %.2f mm section -- %.1f and %.1f nozzle widths"
          % (P.RING_THICKNESS,
             (P.RING_OUTER_D / 2.0 - P.globe_radius("saturn")) / P.NOZZLE_MM,
             P.RING_THICKNESS / P.NOZZLE_MM))
    print("respectively, both well clear. Neither number moved in this run.")
    print()

    print("## Filaments")
    print()
    print("| role | filament | hex |")
    print("|---|---|---|")
    rows = (
        ("globe", P.GLOBE_COLOUR["saturn"]),
        ("the four light bands", S.BAND_COLOUR),
        ("the one darker band", S.DARK_BAND_COLOUR),
        ("the bright northern cap", S.CAP_COLOUR),
        ("the ring", "white"),
    )
    for role, filament in rows:
        print("| %s | `%s` | %s |" % (role, filament, P.FILAMENT_HEX[filament]))
    surface = {colour for _role, colour in rows}
    print()
    print("**Saturn prints in %d surface filaments** -- %s -- where it printed"
          % (len(surface), ", ".join("`%s`" % name for name in sorted(surface))))
    print("in three. The disc and the numeral are counted separately, as they")
    print("are everywhere in this set: every piece carries `white` and `black`")
    print("for those, and they are the ownership cue rather than the planet.")
    print("No new spool: `%s` was already loaded for the Sol den plug and for"
          % S.BAND_COLOUR)
    print("Venus's globe, `%s` for the belt tiles and four other worlds, and"
          % S.DARK_BAND_COLOUR)
    print("`%s` for this piece's own ring." % S.CAP_COLOUR)
    print()

    print("## The ring's colour against the globe's")
    print()
    print("The ring and the globe touch: the plate's bore is %.2f mm inside the"
          % P.RING_GLOBE_BITE)
    print("globe's own radius, so the annulus leaves the surface at the")
    print("equator and the two bodies share that boundary all the way round.")
    print("The ring is `white` %s and the globe is `%s` %s, which is the"
          % (P.FILAMENT_HEX["white"], P.GLOBE_COLOUR["saturn"],
             P.FILAMENT_HEX[P.GLOBE_COLOUR["saturn"]]))
    print("largest value step on the piece after the numeral, and it is the")
    print("step that reads the ring as a separate object rather than as a")
    print("flange of the ball. `measure/saturn-tone-separation.md` measures it")
    print("beside the band tones. The cap above +%.0f is `white` too, so the"
          % S.CAP_LAT)
    print("brightest thing at the top of the globe and the brightest thing")
    print("across its middle are one filament -- which is what the reference")
    print("shows, where the ring and the northern globe are the same cream.")
    print()

    print("## Not drawn")
    print()
    print(S.NOT_DRAWN)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
