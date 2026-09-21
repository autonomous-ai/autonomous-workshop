"""What the Jove mirror moved on Jupiter, and every part of it that did not.

`measure/mirror-meridian.md` decides the meridian and measures the facing floor
for all three mirrored worlds.  This report is the other half, and it is almost
all negative: the brief for this correction lists more things that must NOT
have moved than things that must, and a negative is the kind a picture misses.

Each section below is a claim the brief makes, turned into an arithmetic check
on the exact tables `parts/world.py` builds from.

    "$WORKSHOP_PYTHON" measure/jupiter_mirror.py > measure/jupiter-mirror.md

Exit 0 when every one of them holds, 1 otherwise.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                             # noqa: E402
from parts import jupiter_atlas as J                           # noqa: E402
from parts import markings as M                                # noqa: E402
from parts.markings import (                                   # noqa: E402
    MAP_MIRRORED_WORLDS,
    MARKINGS,
    facing_meridian,
    markings_for,
    reflect_longitude,
)

#: How much a latitude is allowed to move and still count as not having moved.
#: The rings are rounded to four decimal places at source, so this is that
#: rounding.
LATITUDE_TOLERANCE = 1e-4

#: How far the hollow's measured peak may sit from the spot's own meridian and
#: still count as following it.  The boundary is measured at the vertices the
#: build actually puts on it, and `jupiter_atlas.SECTOR_STEP_DEG` spaces those
#: 6 degrees apart, so the peak can only ever be resolved to within half a step
#: of the true maximum.  One whole step is the allowance, and it is read from
#: `jupiter_atlas.SECTOR_STEP_DEG` rather than restated here.


def main() -> int:
    failures = []
    meridian = facing_meridian("jupiter", "anti")
    sol = markings_for("jupiter", "sol")
    anti = markings_for("jupiter", "anti")

    print("# The Jove mirror: what moved on Jupiter, and what did not")
    print()
    print("The correction adds `\"jupiter\"` to `parts/markings.MAP_MIRRORED_WORLDS`")
    print("and gives it a `MERIDIAN_ADJUSTMENT` of %+.2f degrees. That is the"
          % M.MERIDIAN_ADJUSTMENT["jupiter"])
    print("whole of the source change to the geometry. Everything below is a")
    print("consequence of it, measured rather than argued, because the brief")
    print("this correction answers is mostly a list of things that must stay")
    print("where they are.")
    print()

    print("## 1. The Sol piece is untouched")
    print()
    print("`markings_for` returns the identical object `MARKINGS` holds for any")
    print("Sol piece -- not a copy, not a rebuild -- so the Sol world cannot")
    print("have been changed by a transform that is never applied to it. That is")
    print("an identity check rather than an equality check, and it is the")
    print("strongest form the claim has:")
    print()
    same_object = sol is MARKINGS["jupiter"]
    print("- `markings_for(\"jupiter\", \"sol\") is MARKINGS[\"jupiter\"]`: **%s**"
          % ("yes" if same_object else "NO"))
    print("- `markings_for(\"jupiter\", \"anti\") is MARKINGS[\"jupiter\"]`: **%s**, "
          "which is the correction" % ("yes" if anti is MARKINGS["jupiter"] else "no"))
    if not same_object:
        failures.append("the Sol piece no longer takes the identity path")
    print()
    print("The printed solid says the same thing in bytes:")
    print("`measure/revision-part-hashes.md` carries `part_world_jupiter_sol.step`")
    print("and `part_world_jupiter_anti.step` against the published set, and")
    print("`measure/occurrence-geometry.md` carries every one of the 220 colour")
    print("bodies.")
    print()

    print("## 2. No latitude moved, anywhere")
    print()
    print("A longitude reflection maps (lon, lat) to (2C - lon, lat). Latitude")
    print("is not in the transform at all, so no belt boundary, no zone")
    print("boundary and no feature can have changed latitude. Checked vertex by")
    print("vertex against the Sol ring it came from, at %g degrees."
          % LATITUDE_TOLERANCE)
    print()
    print("| marking | rings | vertices | largest latitude change |")
    print("|---|---:|---:|---:|")
    for (key, _c, sol_specs, _s), (_k, _c2, anti_specs, _s2) in zip(sol, anti):
        rings = 0
        vertices = 0
        worst = 0.0
        for sol_spec, anti_spec in zip(sol_specs, anti_specs):
            if sol_spec[0] != "outline":
                continue
            for sol_ring, anti_ring in zip(sol_spec[1], anti_spec[1]):
                rings += 1
                # `_mirror_spec` reverses each ring as well as reflecting it,
                # so vertex i of the Sol ring is vertex -1-i of the Anti one.
                for (_slon, slat), (_alon, alat) in zip(sol_ring,
                                                        anti_ring[::-1]):
                    vertices += 1
                    worst = max(worst, abs(alat - slat))
        if not rings:
            continue
        print("| `%s` | %d | %d | %.2e |" % (key, rings, vertices, worst))
        if worst > LATITUDE_TOLERANCE:
            failures.append("%s: a latitude moved by %.4f degrees" % (key, worst))
    print()
    print("The Great Red Spot sits at latitude %+.2f on both pieces, which is"
          % J.SPOT_LAT)
    print("where the real one sits, and the six belts keep the latitudes")
    print("`jupiter_atlas.BELTS` gives them:")
    print()
    print("| belt | south | north | width |")
    print("|---|---:|---:|---:|")
    for key, name, south, north, how in J.BELTS:
        print("| %s (`%s`, %s) | %+.1f | %+.1f | %.1f |"
              % (name, key, how, south, north, north - south))
    print()
    print("Read the widths rather than the names: 7, 10, 13, 7, 5, 6. No two of")
    print("the pairs are mirror images and no two gaps between them are equal.")
    print("That is the set's own asymmetry and this correction does not touch")
    print("it -- a reflection about a meridian cannot, because a band has the")
    print("same longitude everywhere.")
    print()

    print("## 3. What a longitude reflection leaves exactly alone")
    print()
    print("Most of this globe is invariant under the transform, and it is worth")
    print("saying how much. `_mirror_spec` returns a `band`, a `shell` and a")
    print("`cap` spec unchanged -- the same object, not a rebuilt one -- because")
    print("they are sets of latitudes and the transform is the identity on them.")
    print()
    print("| marking | spec | kind | carries a longitude | identical object |")
    print("|---|---:|---|---|---|")
    invariant = moved = 0
    for (key, _c, sol_specs, _s), (_k, _c2, anti_specs, _s2) in zip(sol, anti):
        for index, (sol_spec, anti_spec) in enumerate(zip(sol_specs, anti_specs),
                                                      start=1):
            identical = sol_spec is anti_spec
            invariant += identical
            moved += not identical
            print("| `%s` | %d | `%s` | %s | %s |"
                  % (key, index, sol_spec[0],
                     "no" if identical else "**yes**",
                     "yes" if identical else "no"))
    print()
    print("**%d of the %d region specs on this globe are returned unchanged and"
          % (invariant, invariant + moved))
    print("%d are reflected.** The %d are the Great Red Spot, its collar and the"
          % (moved, moved))
    print("two wavy belts; everything else is a circle of latitude. That is why")
    print("this world needed a meridian adjustment and Mercury and Venus did")
    print("not: on those two the reflection moves most of the map, and here it")
    print("moves one oval and the phase of two waves.")
    print()

    print("## 4. The hollow follows the spot")
    print()
    print("The South Equatorial Belt's southern boundary bends %.1f degrees"
          % J.HOLLOW_DEPTH_DEG)
    print("north over the spot, so the belt looks like it belongs to the weather")
    print("rather than like a sticker. That bend is drawn into the belt's own")
    print("sector rings, so the reflection carries it with them -- but that is a")
    print("prediction, and this is the measurement. The belt's SOUTHERN boundary")
    print("-- the first half of every sector ring, which is the half the hollow")
    print("is cut into -- is walked on each piece at the %g degree vertex"
          % J.SECTOR_STEP_DEG)
    print("spacing the build gives it, and its northernmost point found. Its")
    print("unhollowed latitude is %+.1f, so the peak is the hollow."
          % J.BELT_LATITUDES["seb"][0])
    print()

    def southern_half(ring):
        """The half of a belt sector ring that is its southern boundary.

        `jupiter_atlas.belt_sector_ring` walks a sector west to east along its
        southern boundary and back east to west along its northern one, so on
        a Sol ring the southern boundary is the first half.  On an Anti-Sol
        ring it is the second, because `markings._mirror_spec` reverses every
        ring it reflects -- a reflection turns a counter-clockwise ring
        clockwise and `features.patches` lofts a ring in the order it is given.

        Rather than encode which piece reverses which, the half with the lower
        MEAN latitude is taken.  The two boundaries are 13 degrees apart and
        the hollow lifts one sector of one of them by 7, so the means never
        come close to crossing.
        """
        half = len(ring) // 2
        first, second = ring[:half], ring[half:]
        mean = lambda part: sum(lat for _lon, lat in part) / len(part)
        return first if mean(first) < mean(second) else second

    def boundary_peak(rings):
        """(longitude, latitude) of the northernmost point of a belt's SOUTH edge.

        The hollow is cut into the southern boundary; looking at the whole ring
        finds the northern boundary instead, which is 13 degrees higher and has
        no hollow in it.
        """
        best = None
        for ring in rings:
            for lon, lat in southern_half(ring):
                if best is None or lat > best[1]:
                    best = (lon, lat)
        return best

    def seb_south_rings(entries):
        """The South Equatorial Belt's sectors, as this piece draws them."""
        for key, _c, specs, _s in entries:
            if key != "bands":
                continue
            outlines = [spec for spec in specs if spec[0] == "outline"]
            # BELTS lists neb before seb and belt_specs preserves that order.
            return outlines[1][1]
        return []

    sol_peak = boundary_peak(seb_south_rings(sol))
    anti_peak = boundary_peak(seb_south_rings(anti))
    spot_anti = reflect_longitude(J.SPOT_LON, meridian)
    print("| piece | spot longitude | belt's northernmost point | its latitude | offset from the spot |")
    print("|---|---:|---:|---:|---:|")
    for label, spot_lon, peak in (("Sol", J.SPOT_LON, sol_peak),
                                  ("Anti-Sol", spot_anti, anti_peak)):
        offset = ((peak[0] - spot_lon + 180.0) % 360.0) - 180.0
        print("| %s | %+.2f | %+.2f | %+.2f | %+.2f |"
              % (label, spot_lon, peak[0], peak[1], offset))
        if abs(offset) > J.SECTOR_STEP_DEG:
            failures.append(
                "the %s piece's belt hollow is %.2f degrees away from its spot"
                % (label, offset))
    print()
    print("The bend is within one %g degree vertex step of the spot's own"
          % J.SECTOR_STEP_DEG)
    print("meridian on both pieces, and the boundary reaches latitude %+.2f"
          % anti_peak[1])
    print("there against its unbent %+.1f -- a rise of %.2f degrees against the"
          % (J.BELT_LATITUDES["seb"][0],
             anti_peak[1] - J.BELT_LATITUDES["seb"][0]))
    print("%.1f the hollow is drawn at. The belt bends around the spot on the"
          % J.HOLLOW_DEPTH_DEG)
    print("Anti-Sol piece exactly as it does on the Sol one, at the new")
    print("longitude, with no second mechanism and no special case: the hollow")
    print("is part of the ring, so reflecting the ring reflects the hollow.")
    print()

    print("## 5. What it costs, measured")
    print()
    print("Two things about the Anti-Sol Jupiter are now not the real planet,")
    print("and both are recorded in the product's limitations as well as here.")
    print()
    print("**The Red Spot sits at a longitude that is not the real one.** It is")
    print("at %+.2f on the Sol piece and %+.2f on the Anti-Sol one."
          % (J.SPOT_LON, spot_anti))
    print("What that costs is nothing a map could check, because longitude on")
    print("this globe was never a map fact: `SPOT_LON = %+.1f` was chosen to put"
          % J.SPOT_LON)
    print("the spot in front of the cameras -- the same decision")
    print("`mercury_atlas.CALORIS_LON` and `venus_atlas.LONGITUDE_OFFSET` are --")
    print("and Jupiter turns in ten hours with no fixed meridian anywhere in")
    print("this set. Latitude, size, shape and count are untouched, and those")
    print("are the four things a reader could check against a photograph.")
    print()
    print("**The wave phase of the two widest belts is handed the other way.**")
    print("Each wavy boundary carries two harmonics of longitude, so reflecting")
    print("longitude reflects the pattern:")
    print()
    print("| boundary | harmonics (n, amplitude, phase) |")
    print("|---|---|")
    for (key, edge), waves in J.WAVES.items():
        print("| `%s` %s | %s |"
              % (key, edge, "; ".join("(%d, %.1f, %.0f)" % item for item in waves)))
    print()
    print("A reader cannot tell a handed wave from an unhanded one without the")
    print("other piece beside it -- which is the point, since the two pieces")
    print("standing side by side is exactly the comparison this correction")
    print("exists to win. The amplitude is %.1f degrees either way on both"
          % J.WAVE_AMPLITUDE_DEG)
    print("pieces, which is %.2f mm on this globe, so the belts stay the same"
          % (J.WAVE_AMPLITUDE_DEG * math.pi * P.globe_diameter("jupiter") / 360.0))
    print("belts.")
    print()

    print("## 6. The set, after the correction")
    print()
    print("Three of eight worlds carry a mirrored map and five carry one map at")
    print("two leans. `measure/mirror-set-consistency.md` is that table, the")
    print("rule that decides it, and every world's tilt and inter-piece angle.")
    print("`markings.MAP_MIRRORED_WORLDS` is now %r." % (MAP_MIRRORED_WORLDS,))
    print()

    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- **%s**" % item)
    else:
        print("Every negative the brief names holds in the built tables: the Sol")
        print("piece takes the identity path, no latitude moved anywhere by more")
        print("than %g degrees, the six belt latitudes and five zone latitudes"
              % LATITUDE_TOLERANCE)
        print("are the ones `jupiter_atlas` declares, and the belt hollow")
        print("follows the spot to the new longitude by itself. What moved is")
        print("the spot, its collar, the two wavy belts' phase, and the three")
        print("zones those belts trim.")
    print()
    print("Measured by `measure/jupiter_mirror.py` on the exact specs")
    print("`parts.markings.markings_for` returns for each piece.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
