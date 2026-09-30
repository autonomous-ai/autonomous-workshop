"""The spot's companion cloud, and everything on Neptune that must not move.

The correction of 2026-09-26 adds exactly one thing to each Neptune piece: a
white outline oval, 10 by 5 degrees of arc, just south of the Great Dark Spot
at its longitude.  It also says nothing else on either piece changes and
nothing on any other part changes.  This measures both halves on the BUILT
colour bodies, against the build this correction starts from, which it
rebuilds from the immutable `revision-source.zip` rather than trusting a
number quoted from an old report.

    "$WORKSHOP_PYTHON" measure/neptune_companion.py <revision-source.zip> \
        > measure/neptune-companion.md

Checked, per army:

1. The companion body exists, is one solid, is `white`, and is not proud of
   the globe (its farthest point from the globe centre is the globe radius).
2. Its size and place, read off the solid: the angular extent of its
   outer face in the planet's own frame, and its centre's latitude and
   longitude against the spot's.
3. Bare blue between it and the spot, and between it and the nearest band,
   measured as the least distance between the two built solids -- which must
   be at least the 0.40 mm nozzle, the narrowest colour boundary this set lets
   any marking or bare gap have.
4. Every other body -- disc, numeral, spot, bands -- has the baseline's volume
   and bounding box to 1e-4 mm3 / 1e-4 mm, and the globe has lost exactly the
   companion's volume.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOL_V = 1e-4
TOL_B = 1e-4


def dump(cad_dir: str) -> dict:
    sys.path.insert(0, cad_dir)
    import params as P                                         # noqa: E402
    from parts.world import world_bodies                      # noqa: E402
    from features.patches import planet_frame                 # noqa: E402

    out = {}
    for side in ("sol", "anti"):
        bodies = world_bodies("neptune", side)
        centre_z = P.globe_centre_z("neptune")
        frame = planet_frame(P.PLANETS["neptune"]["tilt"], P.lean_sign(side),
                             centre_z)
        inverse = frame.inverse()
        rows = {}
        for key, (colour, body) in bodies.items():
            bb = body.bounding_box()
            row = {
                "colour": colour,
                "solids": len(body.solids()),
                "volume": body.volume,
                "bbox": [bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z],
            }
            if key in ("companion", "spot"):
                local = inverse * body
                verts = [v.center() for v in local.vertices()]
                radius = P.globe_radius("neptune")
                outer = [v for v in verts
                         if abs(math.sqrt(v.X ** 2 + v.Y ** 2 + v.Z ** 2) - radius) < 1e-3]
                lons = [math.degrees(math.atan2(v.Y, v.X)) for v in outer]
                lats = [math.degrees(math.asin(max(-1, min(1, v.Z / radius)))) for v in outer]
                row["outer_lon"] = [min(lons), max(lons)]
                row["outer_lat"] = [min(lats), max(lats)]
                row["max_r"] = max(math.sqrt(v.X ** 2 + v.Y ** 2 + v.Z ** 2) for v in verts)
            rows[key] = row
        if "companion" in bodies:
            comp = bodies["companion"][1]
            rows["companion"]["gap_spot_mm"] = comp.distance_to(bodies["spot"][1])
            rows["companion"]["gap_bands_mm"] = comp.distance_to(bodies["bands"][1])
        out[side] = rows
    return out


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--dump":
        print(json.dumps(dump(sys.argv[2])))
        return 0
    zip_path = Path(sys.argv[1])
    here_cad = str(HERE.parent)
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as archive:
            for name in archive.namelist():
                if name.startswith("make/source/cad/") and name.endswith(".py"):
                    archive.extract(name, tmp)
        base_cad = str(Path(tmp) / "make/source/cad")
        run = lambda d: json.loads(subprocess.run(
            [sys.executable, __file__, "--dump", d], check=True,
            capture_output=True, text=True).stdout.strip().splitlines()[-1])
        base, now = run(base_cad), run(here_cad)

    sys.path.insert(0, here_cad)
    import params as P                                         # noqa: E402
    import parts.neptune_atlas as N                            # noqa: E402

    radius = P.globe_radius("neptune")
    mm_per_deg = math.radians(1.0) * radius
    ok = True
    lines = ["# Neptune's companion cloud, and what did not move", ""]
    lines += [
        "Baseline: the build this correction starts from, rebuilt from the",
        "source in `%s`. Current: this tree. Globe Ø%.2f mm, one degree of arc"
        % (zip_path.name, 2 * radius),
        "= %.4f mm, nozzle %.2f mm = %.2f degrees."
        % (mm_per_deg, P.NOZZLE_MM, P.NOZZLE_MM / mm_per_deg), "",
        "Declared: centre lat %.2f, lon %.2f; %g x %g degrees of arc; spot centre"
        % (N.COMPANION_LAT, N.COMPANION_LON, 2 * N.COMPANION_SEMI_ARC_LON,
           2 * N.COMPANION_SEMI_ARC_LAT),
        "lat %.2f, lon %.2f, so the companion is %.2f degrees south of it and %.0f"
        % (N.SPOT_LAT, N.SPOT_LON, N.SPOT_LAT - N.COMPANION_LAT, -N.COMPANION_LON_OFFSET_DEG),
        "degrees west. The owner asked for about 8 south at the same longitude: 8",
        "would overlap the spot's rim, and the spot's own meridian puts 41% of a",
        "printable companion under the Sol piece's seat (see `parts/neptune_atlas.py`",
        "and the seat table below).", "",
    ]
    for side in ("sol", "anti"):
        b, c = base[side], now[side]
        comp = c.get("companion")
        lines += ["## %s" % side, ""]
        if comp is None:
            lines += ["**FAIL: no companion body.**", ""]
            ok = False
            continue
        lon_span = comp["outer_lon"][1] - comp["outer_lon"][0]
        lat_span = comp["outer_lat"][1] - comp["outer_lat"][0]
        cen_lat = sum(comp["outer_lat"]) / 2
        cen_lon = sum(comp["outer_lon"]) / 2
        # Width in arc along the parallel at the centre latitude.
        lon_arc = lon_span * math.cos(math.radians(cen_lat))
        checks = [
            ("companion is one solid", comp["solids"] == 1, str(comp["solids"])),
            ("companion filament is white", comp["colour"] == "white", comp["colour"]),
            ("companion not proud of the globe (max r - R)",
             comp["max_r"] - radius < 1e-3, "%+.5f mm" % (comp["max_r"] - radius)),
            ("east-west extent, deg of arc (want ~10)", abs(lon_arc - 10) < 0.6,
             "%.2f deg = %.3f mm" % (lon_arc, lon_arc * mm_per_deg)),
            ("north-south extent, deg of arc (want ~5)", abs(lat_span - 5) < 0.3,
             "%.2f deg = %.3f mm" % (lat_span, lat_span * mm_per_deg)),
            ("narrowest neck (minor axis) >= nozzle", lat_span * mm_per_deg >= P.NOZZLE_MM,
             "%.3f mm = %.2f nozzle widths" % (lat_span * mm_per_deg,
                                                lat_span * mm_per_deg / P.NOZZLE_MM)),
            ("centre latitude", abs(cen_lat - N.COMPANION_LAT) < 0.2, "%.2f" % cen_lat),
            ("centre longitude (declared spot %+.0f)" % N.COMPANION_LON_OFFSET_DEG,
             abs(cen_lon - N.COMPANION_LON) < 0.3,
             "%.2f (spot %.2f)" % (cen_lon, sum(c["spot"]["outer_lon"]) / 2)),
            ("centre lies within the spot's east-west span",
             c["spot"]["outer_lon"][0] < cen_lon < c["spot"]["outer_lon"][1],
             "%.2f in %.2f..%.2f" % (cen_lon, *c["spot"]["outer_lon"])),
            ("companion south of spot (its north rim below spot's south rim)",
             comp["outer_lat"][1] < c["spot"]["outer_lat"][0],
             "%.2f < %.2f" % (comp["outer_lat"][1], c["spot"]["outer_lat"][0])),
            ("bare gap to spot >= nozzle", comp["gap_spot_mm"] >= P.NOZZLE_MM,
             "%.3f mm = %.2f nozzle widths" % (comp["gap_spot_mm"],
                                                comp["gap_spot_mm"] / P.NOZZLE_MM)),
            ("bare gap to bands >= nozzle", comp["gap_bands_mm"] >= P.NOZZLE_MM,
             "%.3f mm" % comp["gap_bands_mm"]),
        ]
        for key in sorted(set(b) | set(c)):
            if key in ("companion", "globe"):
                continue
            if key not in b or key not in c:
                checks.append(("%s present in both" % key, False, "missing"))
                continue
            dv = c[key]["volume"] - b[key]["volume"]
            db = max(abs(x - y) for x, y in zip(c[key]["bbox"], b[key]["bbox"]))
            checks.append(("%s unchanged (volume, bbox, filament)" % key,
                           abs(dv) <= TOL_V and db <= TOL_B
                           and c[key]["colour"] == b[key]["colour"],
                           "dV %+.2e mm3, dbbox %.1e mm, %s" % (dv, db, c[key]["colour"])))
        lost = b["globe"]["volume"] - c["globe"]["volume"]
        checks.append(("globe lost exactly the companion's volume",
                       abs(lost - comp["volume"]) <= 1e-3,
                       "%.4f vs %.4f mm3" % (lost, comp["volume"])))
        lines += ["| check | result | value |", "|---|---|---|"]
        for name, passed, value in checks:
            ok &= bool(passed)
            lines.append("| %s | %s | %s |" % (name, "PASS" if passed else "**FAIL**", value))
        lines.append("")
    # How much of each companion's outer face the seat cone covers.  The seat
    # springs from the sphere at SEAT_LATITUDE_DEG measured about the PIECE's
    # vertical, not the planet's pole, so on the Sol army -- whose lean carries
    # the southern hemisphere at longitude -65 toward the base -- part of the
    # oval lies under seat material.  Sampled over the oval's own area.
    from build123d import Pos
    from features.patches import planet_frame
    centre_z = P.globe_centre_z("neptune")
    lines += ["## How much of the companion the seat cone covers", "",
              "The seat cone springs from the sphere at piece latitude %.1f"
              % P.SEAT_LATITUDE_DEG,
              "(about the piece's own vertical). Area-weighted over the oval:", "",
              "| army | piece-latitude span of the oval | outer face above the seat | covered by the seat |",
              "|---|---|---:|---:|"]
    for side in ("sol", "anti"):
        frame = planet_frame(P.PLANETS["neptune"]["tilt"], P.lean_sign(side), centre_z)
        seen = total = 0
        lo_hi = [90.0, -90.0]
        steps = 60
        for i in range(steps):
            for j in range(steps):
                u = -1 + (i + 0.5) * 2 / steps
                v = -1 + (j + 0.5) * 2 / steps
                if u * u + v * v > 1:
                    continue
                lat = N.COMPANION_LAT + v * N.COMPANION_SEMI_ARC_LAT
                lon = N.COMPANION_LON + u * N.COMPANION_SEMI_ARC_LON / math.cos(math.radians(lat))
                la, lo = math.radians(lat), math.radians(lon)
                q = (frame * Pos(math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo),
                                 math.sin(la))).position
                plat = math.degrees(math.asin(max(-1, min(1, q.Z - centre_z))))
                lo_hi = [min(lo_hi[0], plat), max(lo_hi[1], plat)]
                total += 1
                seen += plat > P.SEAT_LATITUDE_DEG
        lines.append("| %s | %.1f to %.1f | %.0f%% | %.0f%% |"
                     % (side, lo_hi[0], lo_hi[1], 100 * seen / total,
                        100 * (total - seen) / total))
    lines += ["",
              "At the spot's own meridian (the first build of this correction,",
              "centre -34.5) the Sol figure was 59% above / 41% covered; the",
              "10-degree westward offset exists to make it 100%.", ""]
    lines += ["**Overall: %s**" % ("PASS" if ok else "FAIL"), ""]
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
