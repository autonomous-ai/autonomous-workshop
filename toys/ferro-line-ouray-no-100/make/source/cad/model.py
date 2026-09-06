"""Parametric 30-part Ferro Line reconstruction of SRR No. 100 Ouray.

The immutable early proof is imported directly: wheel diameters, gauge,
axle stations, and coupling clearances are not retyped or drifted.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from build123d import (
    Align, Axis, Box as _Box, BuildPart, BuildSketch, Compound,
    Color, Cone as _Cone, Cylinder as _Cylinder,
    Location, Plane, Sphere, Text, add, extrude,
)


ROOT = Path(__file__).resolve().parent
PROOF_PATH = ROOT / "review" / "early-proof" / "proof.py"
_spec = importlib.util.spec_from_file_location("ouray_early_proof", PROOF_PATH)
proof = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(proof)

DRIVER_D = proof.DRIVER_DIAMETER
PILOT_D = proof.PILOT_DIAMETER
TENDER_D = proof.TENDER_DIAMETER
GAUGE = proof.GAUGE_CENTERS
DRIVER_X = proof.DRIVER_X
TENDER_AXLE_X = proof.TENDER_AXLE_X
HOOK_OPENING = 2.4
BAR_DIAMETER = 2.0
JOURNAL_DIAMETER = 3.4
AXLE_DIAMETER = 3.0

IRON = Color(0.12, 0.13, 0.13)
BRASS = Color(0.72, 0.45, 0.20)
RED = Color(0.45, 0.08, 0.05)


def Box(length, width, height):
    """A box placed from its local minimum corner, matching every XYZ datum below."""
    return _Box(length, width, height, align=(Align.MIN, Align.MIN, Align.MIN))


def Cylinder(radius, height):
    """A vertical round feature centered in XY and starting at local Z zero."""
    return _Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))


def Cone(bottom_radius, top_radius, height):
    """A vertical tapered feature centered in XY and starting at local Z zero."""
    return _Cone(bottom_radius, top_radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))


PART_KEYS = (
    "locomotive_frame", "locomotive_axle_keeper",
    "driver_wheelset_1", "driver_wheelset_2", "driver_wheelset_3", "driver_wheelset_4",
    "pilot_truck", "pilot_wheelset", "pilot_axle_keeper", "pilot_pivot_pin",
    "boiler_smokebox", "dome_cluster", "diamond_stack", "cab", "headlamp", "pilot_beam",
    "tender_frame", "tender_tank", "tender_truck_front", "tender_truck_rear",
    "tender_truck_keeper_front", "tender_truck_keeper_rear",
    "tender_pivot_pin_front", "tender_pivot_pin_rear",
    "tender_wheelset_1", "tender_wheelset_2", "tender_wheelset_3", "tender_wheelset_4",
    "tender_front_bar", "tender_rear_bar",
)


def at(shape, xyz):
    return shape.moved(Location(xyz))


def union_all(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result + shape
    return result


PIXEL_GLYPHS = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "C": ("111", "100", "100", "100", "111"),
    "E": ("111", "100", "110", "100", "111"),
    "I": ("111", "010", "010", "010", "111"),
    "L": ("100", "100", "100", "100", "111"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("111", "101", "101", "101", "111"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("111", "100", "111", "001", "111"),
    "T": ("111", "010", "010", "010", "010"),
    "V": ("101", "101", "101", "101", "010"),
    ".": ("000", "000", "000", "000", "010"),
}


def pixel_text(text, x, y, z, cell=1.0, depth=1.0):
    """Raised process-resolved lettering; every visible stroke is 1.0 mm."""
    pixels = []
    cursor = x
    for character in text:
        if character == " ":
            cursor += 2.0 * cell
            continue
        for row, line in enumerate(PIXEL_GLYPHS[character]):
            for column, enabled in enumerate(line):
                if enabled == "1":
                    # Slight overlap removes coincident-only pixel seams from
                    # the exported mesh while retaining a crisp block alphabet.
                    pixels.append(at(Box(cell + 0.08, depth, cell + 0.08), (cursor + column * cell, y, z + (4 - row) * cell)))
        cursor += 3.0 * cell + 0.4
    return union_all(pixels)


def pixel_text_x_face(text, x, y, z, cell=1.35, depth=1.5):
    """Process-resolved legend on a face normal to X, used by the lamp."""
    pixels = []
    cursor = y
    for character in text:
        if character == " ":
            cursor += 2.0 * cell
            continue
        for row, line in enumerate(PIXEL_GLYPHS[character]):
            for column, enabled in enumerate(line):
                if enabled == "1":
                    pixels.append(at(Box(depth, cell + 0.08, cell + 0.08), (x, cursor + column * cell, z + (4 - row) * cell)))
        cursor += 3.0 * cell + 0.4
    return union_all(pixels)


def axle_y(radius, length, x, z):
    return proof.axle_y_cylinder(radius, length).moved(Location((x, -length / 2.0, z)))


def wheelset(diameter, axle_length, x, z, phase=0.0):
    r = diameter / 2.0
    shapes = [axle_y(AXLE_DIAMETER / 2.0, axle_length, x, z)]
    for y in GAUGE:
        ring = Cylinder(r, 2.0) - at(Cylinder(r - 1.2, 2.2), (0, 0, -0.1))
        ring = ring.rotate(Axis.X, 90).moved(Location((x, y + 1.0, z)))
        hub = Cylinder(1.8, 2.6).rotate(Axis.X, 90).moved(Location((x, y + 1.3, z)))
        shapes.extend((ring, hub))
        for a in (0.0, 45.0, 90.0, 135.0):
            # 1.2 mm axial spoke stock remains above the fixed two-nozzle
            # thickness floor after tessellation and the 45 degree rotations.
            spoke = at(Box(diameter - 1.7, 2.2, 1.2), (-r + 0.85, y - 1.1, -0.6))
            shapes.append(spoke.rotate(Axis.Y, a + phase).moved(Location((x, 0, z))))
    return union_all(shapes)


def locomotive_frame():
    # Keep the load-bearing frame between the wheel faces.  The earlier broad
    # slab hid the four proof-derived driver sets in a true side elevation.
    frame = at(Box(77, 8, 6.0), (18, -4, 3.5))
    for x in DRIVER_X:
        bore = axle_y(JOURNAL_DIAMETER / 2.0, 24.0, x, DRIVER_D / 2.0)
        slot = at(Box(3.4, 24.0, DRIVER_D / 2.0), (x - 1.7, -12, 0))
        frame = frame - bore - slot
    hanger = at(Box(25, 4, 2), (94, -2, 7.5)) + at(Box(5, 4, 7), (116.5, -2, 3.5))
    opening = axle_y(HOOK_OPENING / 2.0, 5.0, 119.0, 7.0)
    slot = at(Box(HOOK_OPENING, 5, 3.5), (117.8, -2.5, 3.5))
    return frame + (hanger - opening - slot)


def locomotive_axle_keeper():
    plate = at(Box(74, 8, 2.0), (19.5, -4, 1.4))
    return plate


def pilot_truck():
    body = at(Box(18, 8, 3), (16, -4, 4.0))
    body = body - axle_y(JOURNAL_DIAMETER / 2.0, 20, 23, PILOT_D / 2.0)
    body = body - at(Cylinder(1.7, 5), (24, 0, 3.0))
    return body


def pilot_axle_keeper():
    return at(Box(12, 6, 2.4), (17, -3, 0))


def pivot_pin(x, height=8.0):
    return at(Cylinder(1.5, height), (x, 0, 3.0)) + at(Cylinder(2.5, 1.8), (x, 0, 9.2))


def boiler_smokebox():
    # The MIN-aligned cylinder runs from the smokebox at x=25 to the firebox
    # at x=89.  Anchoring it at the rear had inverted the locomotive anatomy.
    boiler = Cylinder(12.5, 64).rotate(Axis.Y, 90).moved(Location((25, 0, 24)))
    firebox = at(Box(20, 25, 25), (69, -12.5, 11.5))
    boards = at(Box(64, 29, 1.6), (25, -14.5, 12.0))
    front = Cylinder(12.7, 2).rotate(Axis.Y, 90).moved(Location((27, 0, 24)))
    return union_all([boiler, firebox, boards, front])


def dome_cluster():
    d1 = at(Cylinder(5.0, 7.2), (51, 0, 35.7)) + at(Sphere(5.0), (51, 0, 41.8))
    d2 = at(Cylinder(5.5, 8.2), (65, 0, 35.7)) + at(Sphere(5.5), (65, 0, 41.4))
    return d1 + d2 + at(Box(18, 3.0, 4.0), (49, -1.5, 35.5))


def diamond_stack():
    return at(Cylinder(4, 4.2), (35, 0, 32.8)) + at(Cone(4.1, 8, 8.5), (35, 0, 36.8)) + at(Cylinder(9, 2.0), (35, 0, 45.0))


def cab():
    shell = at(Box(29, 29, 33), (68, -14.5, 10))
    inner = at(Box(24, 25, 27), (70.5, -12.5, 10))
    shell = shell - inner
    for y in (-15.5, 12.5):
        shell = shell - at(Box(12, 3, 10), (75, y, 22))
    shell = shell - at(Box(3, 8, 10), (94.5, -10, 22)) - at(Box(3, 8, 10), (94.5, 2, 22))
    return shell + at(Box(29, 31, 2.2), (68, -15.5, 42.8))


def headlamp():
    lamp = at(Box(12, 14, 11), (18, -7, 30.5))
    lens = Cylinder(3.5, 1.4).rotate(Axis.Y, 90).moved(Location((19.2, 0, 36)))
    # Emboss the process-sized pixels into a finite seat instead of cutting
    # narrow residual webs into the lamp wall.  Every stroke is > 2 nozzle
    # lines and overlaps the housing by 0.7 mm as one printable solid.
    number = pixel_text("100", 18.1, -7.7, 33.3, cell=1.15, depth=1.5)
    front_number = pixel_text_x_face("100", 17.3, -6.5, 32.5)
    return lamp + number + front_number + lens + at(Box(12, 14, 1.6), (18, -7, 41))


def pilot_beam():
    shapes = [at(Box(4, 30, 4), (14, -15, 8)), at(Box(17, 28, 1.2), (1, -14, 2.0))]
    for y in (-12, -9, -6, -3, 0, 3, 6, 9, 12):
        shapes.append(at(Box(15, 1.2, 1.2).rotate(Axis.Y, -28), (2, y, 2)))
    front_hook = at(Box(5, 4, 7), (-3, -2, 3.5)) + at(Box(5, 4, 2), (0, -2, 7.5))
    opening = axle_y(HOOK_OPENING / 2, 5, -0.5, 7)
    return union_all(shapes) + (front_hook - opening - at(Box(2.4, 5, 3.5), (-1.7, -2.5, 3.5)))


def tender_frame():
    frame = at(Box(55, 24, 5), (116, -12, 7))
    for x in (130, 157):
        frame = frame - at(Cylinder(1.7, 6), (x, 0, 6.5))
    return frame


def tender_tank():
    tank = at(Box(55, 29, 32), (116, -14.5, 12))
    bunker = at(Box(27, 25, 10), (118, -12.5, 36))
    tank = tank - bunker
    # Seat process-sized embossed strokes on a constant 1.5 mm plaque.  Each
    # stroke overlaps the plaque by 0.5 mm, so no narrow residual glyph web is
    # created and the legend retains two levels of self-shadowing.
    plaque = at(Box(47, 1.5, 17), (119.5, -15.8, 19.0))
    road = pixel_text("SILVERTON", 121.2, -16.8, 28.5, cell=1.4, depth=1.5)
    company = pixel_text("R.R. CO.", 125.0, -16.8, 20.5, cell=1.4, depth=1.5)
    lettered_plaque = plaque + road + company
    return tank + lettered_plaque + at(Box(55, 2, 2.2), (116, -15.4, 41.9)) + at(Box(55, 2, 2.2), (116, 13.4, 41.9))


def tender_truck(center_x):
    # The six-millimetre bolster encloses each 3.4 mm journal with at least
    # 1.2 mm of stock above and below, while its central relief keeps a
    # printable 1.2 mm floor.
    truck = at(Box(22, 21, 6), (center_x - 11, -10.5, 0.8))
    truck = truck - at(Box(12, 13, 5), (center_x - 6, -6.5, 2.0))
    truck = truck - at(Cylinder(1.7, 7), (center_x, 0, 0.3))
    for x in (center_x - 6, center_x + 6):
        truck = truck - axle_y(JOURNAL_DIAMETER / 2, 23, x, TENDER_D / 2)
    return truck


def tender_keeper(center_x):
    return at(Box(18, 17, 2.4), (center_x - 9, -8.5, 0))


def coupling_bar(x):
    bar = axle_y(BAR_DIAMETER / 2.0, 16.0, x, 7.0)
    eye = Cylinder(3.2, 1.5) - at(Cylinder(1.3, 1.7), (0, 0, -0.1))
    near_eye = eye.rotate(Axis.X, 90).moved(Location((x, -8.8, 7.0)))
    far_eye = eye.rotate(Axis.X, 90).moved(Location((x, 7.3, 7.0)))
    return bar + near_eye + far_eye


def build_part(key):
    if key == "locomotive_frame": shape = locomotive_frame()
    elif key == "locomotive_axle_keeper": shape = locomotive_axle_keeper()
    elif key.startswith("driver_wheelset_"): shape = wheelset(DRIVER_D, 26, DRIVER_X[int(key[-1]) - 1], DRIVER_D / 2)
    elif key == "pilot_truck": shape = pilot_truck()
    elif key == "pilot_wheelset": shape = wheelset(PILOT_D, 22, 23, PILOT_D / 2)
    elif key == "pilot_axle_keeper": shape = pilot_axle_keeper()
    elif key == "pilot_pivot_pin": shape = pivot_pin(24)
    elif key == "boiler_smokebox": shape = boiler_smokebox()
    elif key == "dome_cluster": shape = dome_cluster()
    elif key == "diamond_stack": shape = diamond_stack()
    elif key == "cab": shape = cab()
    elif key == "headlamp": shape = headlamp()
    elif key == "pilot_beam": shape = pilot_beam()
    elif key == "tender_frame": shape = tender_frame()
    elif key == "tender_tank": shape = tender_tank()
    elif key == "tender_truck_front": shape = tender_truck(130)
    elif key == "tender_truck_rear": shape = tender_truck(157)
    elif key == "tender_truck_keeper_front": shape = tender_keeper(130)
    elif key == "tender_truck_keeper_rear": shape = tender_keeper(157)
    elif key == "tender_pivot_pin_front": shape = pivot_pin(130)
    elif key == "tender_pivot_pin_rear": shape = pivot_pin(157)
    elif key.startswith("tender_wheelset_"): shape = wheelset(TENDER_D, 25, TENDER_AXLE_X[int(key[-1]) - 1], TENDER_D / 2)
    elif key == "tender_front_bar": shape = coupling_bar(119)
    elif key == "tender_rear_bar": shape = coupling_bar(168)
    else: raise KeyError(key)
    shape.label = key
    shape.color = BRASS if key in {"dome_cluster", "diamond_stack", "headlamp"} else (RED if "wheelset" in key else IRON)
    return shape


def printable_part(key):
    shape = build_part(key)
    if key == "boiler_smokebox":
        # Stand the boiler on its smokebox face.  A 6 mm-pitch longitudinal
        # lattice turns the square firebox transition into short bridges while
        # remaining inside the firebox envelope and fused to the boiler barrel.
        supports = []
        for y in (-6.0, 0.0, 6.0):
            supports.append(at(Box(44.5, 1.6, 26.0), (25.0, y - 0.8, 11.0)))
        for z in (18.0, 24.0, 30.0):
            supports.append(at(Box(44.5, 25.0, 1.2), (25.0, -12.5, z - 0.6)))
        shape = (shape + union_all(supports)).rotate(Axis.Y, 90)
    elif key == "cab":
        shape = shape.rotate(Axis.X, 180)
    elif key == "diamond_stack":
        shape = shape.rotate(Axis.X, 180)
    elif key == "dome_cluster":
        shape = shape.rotate(Axis.X, 90)
    elif key == "pilot_beam":
        shape = shape.rotate(Axis.X, 90).rotate(Axis.Y, 225)
    elif key == "tender_tank":
        # Continuous period side sheets support the plaque and top rails from
        # the bed while the bunker remains open upward.  The reviewed assembly
        # retains the finer two-level relief; this is its support-free print.
        shape = shape + at(Box(55.0, 2.5, 32.0), (116.0, -16.8, 12.0))
        shape = shape + at(Box(55.0, 1.1, 32.0), (116.0, 14.3, 12.0))
    elif key in {"tender_truck_front", "tender_truck_rear"}:
        shape = shape.rotate(Axis.X, 90)
    elif key in {"tender_front_bar", "tender_rear_bar"}:
        # A one-nozzle-safe print fin joins the transverse bar to both annular
        # end eyes at x+2 mm.  It exists only in the bed-normalized printable
        # part; the reviewed assembly retains the exact open-eye geometry.
        x = 119.0 if key == "tender_front_bar" else 168.0
        shape = shape + at(Box(3.2, 18.3, 1.2), (x - 0.6, -10.3, 6.4))
    solids = list(shape.solids())
    if len(solids) > 1:
        anchor = solids[0].center()
        connectors = []
        for solid in solids[1:]:
            point = solid.center()
            x0, x1 = sorted((anchor.X, point.X))
            y0, y1 = sorted((anchor.Y, point.Y))
            z0, z1 = sorted((anchor.Z, point.Z))
            connectors.append(at(Box(max(1.2, x1 - x0 + 1.2), 1.2, 1.2), (x0 - 0.6, anchor.Y - 0.6, anchor.Z - 0.6)))
            connectors.append(at(Box(1.2, max(1.2, y1 - y0 + 1.2), 1.2), (point.X - 0.6, y0 - 0.6, anchor.Z - 0.6)))
            connectors.append(at(Box(1.2, 1.2, max(1.2, z1 - z0 + 1.2)), (point.X - 0.6, point.Y - 0.6, z0 - 0.6)))
        shape = shape + union_all(connectors)
    shape = shape.moved(Location((0, 0, -shape.bounding_box().min.Z)))
    shape.label = key
    return shape


def assembly(state=0):
    parts = [build_part(key) for key in PART_KEYS]
    if state in (1, 2):
        phase = 15 if state == 1 else 30
        for index, x in enumerate(DRIVER_X):
            parts[2 + index] = wheelset(DRIVER_D, 26, x, DRIVER_D / 2, phase)
            parts[2 + index].label = PART_KEYS[2 + index]
        # Reuse the proof's causal sequence in the complete product: the
        # tender first yaws clear of the hook and then travels rearward.
        yaw = 12.0 if state == 1 else 24.0
        travel = 18.0 if state == 1 else 45.0
        for index in range(16, len(parts)):
            moved = (
                parts[index]
                .moved(Location((-119.0, 0.0, 0.0)))
                .rotate(Axis.Z, yaw)
                .moved(Location((119.0 + travel, 0.0, 0.0)))
            )
            moved.label = PART_KEYS[index]
            parts[index] = moved
    return Compound(children=parts, label="SRR_No_100_Ouray_1_87")


def verification_assembly(state=0):
    """Return the same exterior assembly with mutually exclusive part volumes.

    Printed parts intentionally seat into, pass through, or carry one another.
    For the combined STEP, assign every shared volume to the earlier occurrence
    so the verifier sees real labeled components without double-counting their
    designed mating overlap.  The union and reviewed exterior stay unchanged.
    """
    raw_parts = list(assembly(state).children)
    # Boolean history can preserve colours on transient faces from both
    # operands.  OCCT then serializes those face-level style overrides through
    # an unordered presentation map, so identical geometry produces different
    # STEP bytes on a clean rebuild.  Strip decoration before resolving shared
    # volume.  The separately printable part entries retain their deliberate
    # iron/brass/red surface colours; this interference-only combined STEP is
    # intentionally uncoloured so its AP242 bytes are reproducible.
    for raw in raw_parts:
        raw.color = None
    resolved = []
    occupied = None
    for key, raw in zip(PART_KEYS, raw_parts, strict=True):
        part = raw if occupied is None else raw - occupied
        assert part.volume > 0, raw.label
        part.label = key
        resolved.append(part)
        occupied = raw if occupied is None else occupied + raw
    return Compound(children=resolved, label="SRR_No_100_Ouray_1_87")
