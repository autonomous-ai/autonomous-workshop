"""Landmark ledger: every defining feature of the piece has its own target.

Each row measures the geometry that was actually returned -- bounding boxes,
face radii, vertex positions, solid counts -- rather than restating the
arithmetic that produced it. Sabotaging a builder makes a row report the
sabotaged number.
"""
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from build123d import import_step  # noqa: E402

import planet_shear_lib as lib  # noqa: E402

TOL = 0.02
rows, bad = [], 0


def check(name, ok, detail):
    global bad
    rows.append(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        bad += 1


def near(a, b, tol=TOL):
    return abs(a - b) <= tol


def sphere_radii(shape, centre_z):
    """Distances from the globe centre to every vertex of `shape`."""
    return [math.dist((v.X, v.Y, v.Z), (0.0, 0.0, centre_z)) for v in shape.vertices()]


def main():
    global bad
    piece_step = PROJECT / "part_piece.step"
    base = lib.build_base()
    seat = lib.build_seat()
    ocean = lib.build_ocean()
    relief = lib.build_relief()
    ice = relief["polar_ice"]
    land = [v for k, v in relief.items() if k.startswith("land_")]
    dryland = [v for k, v in relief.items() if k.startswith("dryland_")]
    numeral = lib.rank_numeral()

    # --- disc base -------------------------------------------------------
    box = base.bounding_box()
    check("disc diameter", near(box.size.X, lib.BASE_DIAMETER),
          f"{box.size.X:.3f} mm across X, want {lib.BASE_DIAMETER}")
    check("disc height", near(box.max.Z, lib.BASE_HEIGHT) and near(box.min.Z, 0.0),
          f"Z {box.min.Z:.3f} to {box.max.Z:.3f}, want 0 to {lib.BASE_HEIGHT}")
    check("bed datum", near(box.min.Z, 0.0), f"lowest disc point at Z {box.min.Z:.3f}")
    rims = [e for e in base.edges()
            if e.geom_type.name == "CIRCLE" and near(e.radius, lib.BASE_RADIUS, 1e-6)
            and near(e.center().Z, lib.BASE_HEIGHT - lib.BASE_TOP_ROUND, 1e-6)]
    check("disc top round", len(rims) == 1,
          f"{len(rims)} circle(s) of radius {lib.BASE_RADIUS} at the start of the round")

    # --- rank numeral ----------------------------------------------------
    gbox = numeral.bounding_box()
    check("numeral stands proud", near(-gbox.min.Y, lib.BASE_RADIUS + lib.GLYPH_RELIEF),
          f"reaches Y {gbox.min.Y:.3f}, want {-(lib.BASE_RADIUS + lib.GLYPH_RELIEF):.3f}")
    check("numeral on the front wall", near(gbox.center().X, 0.0, 0.05) and gbox.min.Y < 0,
          f"centred at X {gbox.center().X:.3f} on the -Y face")
    # the drafted blank meets a curved wall, so the band runs a little past the
    # nominal box at the ends of the widest stroke
    check("numeral height band",
          near(gbox.min.Z, lib.GLYPH_BOTTOM, 0.15)
          and near(gbox.max.Z, lib.GLYPH_BOTTOM + lib.GLYPH_HEIGHT, 0.15),
          f"Z {gbox.min.Z:.3f} to {gbox.max.Z:.3f} on a {lib.BASE_HEIGHT} mm wall")
    # Read the digit off the outward faces of the strokes: which heights carry
    # raised material at which side of the glyph.  A 4 is two strokes with a gap
    # between them at the top, a bar right across the middle, and a single
    # right-hand stroke below it.
    proud_radius = lib.BASE_RADIUS + lib.GLYPH_RELIEF - 0.02
    proud_faces = []
    for face in numeral.faces():
        centre = face.center()
        if math.hypot(centre.X, centre.Y) < proud_radius:
            continue
        fbox = face.bounding_box()
        proud_faces.append((fbox.min.Z, fbox.max.Z, fbox.min.X, fbox.max.X))

    def raised_at(x, z):
        return any(zlo - 0.01 <= z <= zhi + 0.01 and xlo - 0.01 <= x <= xhi + 0.01
                   for zlo, zhi, xlo, xhi in proud_faces)

    rise = lib.GLYPH_RELIEF * lib.GLYPH_RAMP
    arm = lib.GLYPH_HEIGHT / 2.0
    left = -(lib.GLYPH_WIDTH - lib.GLYPH_STROKE) / 2.0
    right = (lib.GLYPH_WIDTH - lib.GLYPH_STROKE) / 2.0
    z_top = lib.GLYPH_BOTTOM + arm + arm / 2.0
    z_mid = lib.GLYPH_BOTTOM + arm + rise / 2.0
    z_low = lib.GLYPH_BOTTOM + arm / 2.0 + rise / 2.0

    check("numeral top: two strokes with a gap",
          raised_at(left, z_top) and raised_at(right, z_top) and not raised_at(0.0, z_top),
          f"at Z {z_top:.2f} raised at X {left:.2f} and {right:.2f}, clear at X 0")
    check("numeral middle: one bar across",
          raised_at(left, z_mid) and raised_at(0.0, z_mid) and raised_at(right, z_mid),
          f"at Z {z_mid:.2f} raised right across the glyph")
    check("numeral below: right-hand stroke only",
          raised_at(right, z_low) and not raised_at(left, z_low),
          f"at Z {z_low:.2f} raised at X {right:.2f}, clear at X {left:.2f}")

    # --- ice seat --------------------------------------------------------
    sbox = seat.bounding_box()
    check("ocean seat height", near(sbox.min.Z, lib.BASE_HEIGHT) and near(sbox.max.Z, lib.SEAT_TOP_Z),
          f"Z {sbox.min.Z:.3f} to {sbox.max.Z:.3f}, want {lib.BASE_HEIGHT} to {lib.SEAT_TOP_Z:.3f}")
    check("ocean seat lands wider than it starts", near(sbox.size.X / 2, lib.SEAT_BASE_RADIUS),
          f"widest radius {sbox.size.X / 2:.3f} at the disc face, want {lib.SEAT_BASE_RADIUS:.3f}")
    seat_rim = [e for e in seat.edges()
                if e.geom_type.name == "CIRCLE" and near(e.center().Z, lib.SEAT_TOP_Z, 1e-6)]
    check("ocean seat meets the globe at the seat latitude",
          len(seat_rim) == 1 and near(seat_rim[0].radius, lib.SEAT_TOP_RADIUS),
          f"{len(seat_rim)} rim circle(s) at Z {lib.SEAT_TOP_Z:.3f}, radius "
          f"{seat_rim[0].radius:.3f} vs the globe's {lib.SEAT_TOP_RADIUS:.3f}"
          if seat_rim else "no rim circle where the seat should meet the globe")

    # --- ocean globe -----------------------------------------------------
    obox = ocean.bounding_box()
    check("globe diameter", near(obox.size.X, lib.GLOBE_DIAMETER)
          and near(obox.size.Z, lib.GLOBE_DIAMETER),
          f"{obox.size.X:.3f} x {obox.size.Z:.3f}, want {lib.GLOBE_DIAMETER}")
    check("globe centre height", near(obox.center().Z, lib.GLOBE_CENTRE_Z),
          f"centre at Z {obox.center().Z:.3f}, want {lib.GLOBE_CENTRE_Z:.3f}")
    # --- relief ----------------------------------------------------------
    relief_radii = []
    for group in list(relief.values()):
        relief_radii += sphere_radii(group, lib.GLOBE_CENTRE_Z)
    check("relief stands 1.0 mm proud",
          near(max(relief_radii), lib.RELIEF_RADIUS, 0.03)
          and near(min(relief_radii), lib.GLOBE_RADIUS, 0.03),
          f"relief spans radius {min(relief_radii):.3f} to {max(relief_radii):.3f}, "
          f"want {lib.GLOBE_RADIUS} to {lib.RELIEF_RADIUS}")
    floor_z = lib.GLOBE_CENTRE_Z + lib.GLOBE_RADIUS * math.sin(math.radians(lib.RELIEF_FLOOR_LAT))
    seated = [v.Z for group in relief.values() for v in group.vertices()
              if near(math.dist((v.X, v.Y, v.Z), (0.0, 0.0, lib.GLOBE_CENTRE_Z)),
                      lib.GLOBE_RADIUS, 0.05)]
    check("relief outlines stop at the declared floor", min(seated) >= floor_z - 0.05,
          f"lowest outline vertex Z {min(seated):.3f}, floor latitude "
          f"{lib.RELIEF_FLOOR_LAT} is Z {floor_z:.3f}")
    lowest = min(v.Z for group in relief.values() for v in group.vertices())
    check("relief stays clear of the disc face", lowest > lib.BASE_HEIGHT + 1.0,
          f"lowest relief vertex Z {lowest:.3f}, disc face at {lib.BASE_HEIGHT}")
    check("continents are separate landmasses",
          len(land) == 4 and all(len(g.solids()) == 1 for g in land),
          f"{len(land)} named landmass group(s), each one body")
    check("drylands cut into the continents",
          len(dryland) == 5 and all(len(g.solids()) == 1 for g in dryland),
          f"{len(dryland)} named dryland group(s), each one body")
    ice_fields = len(ice.solids())
    check("polar ice is one field", ice_fields == 1,
          f"{ice_fields} ice solid(s)")
    rim_lats = sorted({round(math.degrees(math.asin(
        max(-1.0, min(1.0, (v.Z - lib.GLOBE_CENTRE_Z) / max(1e-9, math.dist(
            (v.X, v.Y, v.Z), (0.0, 0.0, lib.GLOBE_CENTRE_Z))))))), 0)
        for v in ice.vertices()})
    check("polar ice rim is not a single parallel", len(rim_lats) >= 6,
          f"ice vertices sit at {len(rim_lats)} distinct latitudes from "
          f"{rim_lats[0]:.0f} to {rim_lats[-1]:.0f}")
    cap_top = max(v.Z for v in ice.vertices())
    check("polar ice caps the globe", cap_top > lib.GLOBE_CENTRE_Z + lib.GLOBE_RADIUS,
          f"ice reaches Z {cap_top:.3f}, above the bare globe top "
          f"{lib.GLOBE_CENTRE_Z + lib.GLOBE_RADIUS:.3f}")
    shell_volume = lib.relief_shell().volume
    coverage = sum(g.volume for g in relief.values()) / shell_volume
    check("land covers a plausible fraction", 0.20 <= coverage <= 0.38,
          f"{coverage * 100:.1f}% of the shell is raised")

    # --- the colour partition covers the printed body exactly ------------
    if piece_step.exists():
        printed = import_step(str(piece_step))
        group_sum = sum(g.volume for g in (base, seat, ocean, *relief.values()))
        check("colour groups tile the printed part",
              abs(group_sum - printed.volume) < 0.01,
              f"groups {group_sum:.3f} mm3 vs printed {printed.volume:.3f} mm3")
        check("printed part is one body", len(printed.solids()) == 1,
              f"{len(printed.solids())} solid(s) in part_piece.step")
    else:
        check("printed part present", False, f"{piece_step} has not been written")

    print("\n".join(rows))
    print(f"RESULT: {len(rows)} landmark(s), {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
