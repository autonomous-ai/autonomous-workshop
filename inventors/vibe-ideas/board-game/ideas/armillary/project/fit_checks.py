"""fit_checks.py — proves the brief's `## Interfaces` against the actually
exported geometry, not against Params. `validation.py` already hard-asserts
every bill number on Params before a render is even attempted; this script
answers a different question: did the CAD kernel actually PRODUCE the seat,
bore, and slot those numbers describe, in the STL the user will print?

Every check loads a real exported STL from build/armillary_parts/ and
measures its mesh vertices directly — no ray-cast acceleration structure
(this sandbox has no `rtree`/`embree`, so `trimesh.ray` is unavailable).
Instead this exploits a property of every mate in this design: each seat is
a STRAIGHT vertical wall (a well, a bore, a slot), and a fine-tessellated
CadQuery/OCCT export of a straight wall carries vertices only at its top and
bottom edge rings, never along its interior (a flat/ruled surface needs no
interior sampling to stay within mesh tolerance). So the exact diameter or
width of a seat is recoverable directly from the radial or lateral spread of
those edge-ring vertices — confirmed empirically against every part before
being written into the checks below. Every measurement is taken from the
exported mesh, never copied from Params.

Run standalone:

    python fit_checks.py

Exit 0 = every interface fits. gate.py reruns this after every `cad` build.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))
# features/ring.py imports cadlib (the cadcode skill's helper library), which
# `scripts/cad` normally puts on sys.path for us. Standalone, find the repo's
# cadcode/ directory relative to this project and add it the same way.
for _ancestor in PROJECT_DIR.parents:
    _cadcode = _ancestor / "cadcode"
    if _cadcode.is_dir():
        sys.path.insert(0, str(_cadcode))
        break

from params import Params  # noqa: E402
from features.ring import RING_XY  # noqa: E402
from assemblies.product import _reserve_slot_position, _COLUMN_CENTER  # noqa: E402

PARTS_DIR = PROJECT_DIR / "build" / "armillary_parts"

p = Params()

# FDM hand-assembly slop budget for comparing a tessellated mesh against a
# nominal design value — a measurement tolerance, not a design clearance.
MEASURE_TOL_MM = 0.6

FAILS: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(f"{label}: {detail}")


def load(name: str) -> trimesh.Trimesh:
    stl = PARTS_DIR / f"{name}.stl"
    if not stl.is_file():
        raise FileNotFoundError(
            f"{stl} missing — run `cad` before fit_checks.py")
    return trimesh.load(str(stl), force="mesh")


def bbox_extents(mesh: trimesh.Trimesh) -> np.ndarray:
    return mesh.bounds[1] - mesh.bounds[0]


def z_at(mesh: trimesh.Trimesh, expected_z: float, xy_center, xy_radius: float,
         tol: float = 2.0) -> float:
    """The actual mesh Z of a flat feature expected near `expected_z`,
    restricted to an XY disc around `xy_center` — proof a face really sits
    at the height Params claims, taken from real mesh vertices."""
    v = np.asarray(mesh.vertices)
    m = np.abs(v[:, 2] - expected_z) <= tol
    d = np.linalg.norm(v[:, :2] - np.asarray(xy_center), axis=1)
    m &= d <= xy_radius
    zc = v[m][:, 2]
    if zc.size < 2:
        raise AssertionError(f"no flat feature found near z={expected_z} "
                             f"(xy_center={xy_center}, r={xy_radius}, found {zc.size} pts)")
    return float(np.median(zc))


def cylinder_wall_radius(mesh: trimesh.Trimesh, center_xy,
                         angle_bands: list[tuple[float, float]] | None,
                         r_max: float, z_range=None) -> float:
    """Median radial distance (from `center_xy`) of nearby vertices whose
    world angle around the center falls in one of `angle_bands` (deg) — i.e.
    vertices on the seat's top/bottom edge ring, held away from any local
    notch/slot/tab so the measurement is clean. `angle_bands=None` uses
    every angle (a plain, feature-free bore). A straight wall's ring
    vertices sit at just one or two Z values (see module docstring), so no
    Z filtering is needed unless another nearby feature must be excluded."""
    v = np.asarray(mesh.vertices)
    if z_range is not None:
        v = v[(v[:, 2] >= z_range[0]) & (v[:, 2] <= z_range[1])]
    rel = v[:, :2] - np.asarray(center_xy)
    r = np.linalg.norm(rel, axis=1)
    r_ok = r <= r_max
    if angle_bands is None:
        sel = r_ok
    else:
        ang = np.degrees(np.arctan2(rel[:, 1], rel[:, 0])) % 360
        sel = np.zeros_like(r_ok)
        for lo, hi in angle_bands:
            lo, hi = lo % 360, hi % 360
            sel |= (ang >= lo) & (ang <= hi) if lo <= hi else ((ang >= lo) | (ang <= hi))
        sel &= r_ok
    r_sel = r[sel]
    if r_sel.size < 3:
        raise AssertionError(f"no wall vertices found (center={center_xy}, "
                             f"bands={angle_bands}, r_max={r_max}, found {r_sel.size} pts)")
    return float(np.median(r_sel))


def rect_wall_span(mesh: trimesh.Trimesh, x_range, y_range=None) -> tuple[float, float]:
    """(min_y, max_y) of vertices inside an x (and required, here, y) band —
    for a plain rectangular slot cavity these are its two flat side walls,
    found at the slot's END (a straight rectangular pocket's long side walls
    carry vertices only at their two ends, same reasoning as the cylinder
    case). `y_range` must exclude any OTHER nearby feature at a similar x
    (e.g. score_rail's second slot, or a tick-mark hole) — pass a band wide
    enough for the wall being measured and no wider."""
    v = np.asarray(mesh.vertices)
    m = (v[:, 0] >= x_range[0]) & (v[:, 0] <= x_range[1])
    if y_range is not None:
        m &= (v[:, 1] >= y_range[0]) & (v[:, 1] <= y_range[1])
    ys = v[m][:, 1]
    if ys.size < 3:
        raise AssertionError(f"no slot-wall vertices found (x={x_range}, y={y_range})")
    return float(ys.min()), float(ys.max())


# ---------------------------------------------------------------------------
# LOAD-BEARING: star_tile / moon_tile / void_tile share one identical blank.
# The only thing that may differ is the face relief; bbox is a direct proxy
# for "outline, thickness, rim and back are bit-for-bit identical" — if the
# blanks diverged, the bboxes would diverge too.
# ---------------------------------------------------------------------------

def check_tile_family_identical() -> dict[str, trimesh.Trimesh]:
    tiles = {name: load(f"{name}_01") for name in ("star_tile", "moon_tile", "void_tile")}
    extents = {name: bbox_extents(m) for name, m in tiles.items()}
    star_ext = extents["star_tile"]
    for name, ext in extents.items():
        check(f"tile-family:{name} bbox matches star_tile (identical blank)",
              bool(np.allclose(ext, star_ext, atol=0.05)),
              f"{name}={ext.tolist()} vs star_tile={star_ext.tolist()}")
    check("tile-family: diameter matches stated 22mm",
          abs(max(star_ext[0], star_ext[1]) - p.tile_dia) < MEASURE_TOL_MM,
          f"measured {max(star_ext[0], star_ext[1]):.2f}mm vs {p.tile_dia}mm")
    check("tile-family: total resting height matches stated 15mm (6mm body + 9mm knob)",
          abs(star_ext[2] - (p.tile_thickness + p.knob_h)) < MEASURE_TOL_MM,
          f"measured {star_ext[2]:.2f}mm vs {p.tile_thickness + p.knob_h}mm")
    return tiles


# ---------------------------------------------------------------------------
# Interface 1 — star_tile seats into plinth_ring's well.
# ---------------------------------------------------------------------------

def check_tile_seats_plinth_well(tile_dia_mm: float) -> None:
    ring = load("plinth_ring")
    well_idx = 1  # a non-zenith well (zenith = 0, 4, 7), so no sunburst collar nearby
    wx, wy = RING_XY[well_idx]

    # The well's own cylindrical wall carries vertices only at its top ring
    # (the rim) and bottom ring (the floor) — both within a generous 15mm
    # XY radius of the well center, since the wall radius is 12mm.
    floor_z = z_at(ring, p.plinth_drum_h - p.well_depth, (wx, wy), xy_radius=15.0)
    rim_z = z_at(ring, p.plinth_drum_h, (wx, wy), xy_radius=15.0)
    well_depth_meas = rim_z - floor_z
    check("interface1: well depth measured from STL matches stated 6mm",
          abs(well_depth_meas - p.well_depth) < MEASURE_TOL_MM,
          f"measured {well_depth_meas:.2f}mm (rim={rim_z:.2f}, floor={floor_z:.2f}) vs {p.well_depth}mm")

    # cut_wells' thumb scallop always sits offset in world +X from the well
    # center (blocks.py), so bands near +Y (60-120deg) and -Y (240-300deg)
    # measure the clean circular wall, away from the notch.
    well_r = cylinder_wall_radius(
        ring, (wx, wy), angle_bands=[(60, 120), (240, 300)], r_max=20.0)
    well_dia = 2.0 * well_r
    check("interface1: well diameter measured from STL matches stated 24mm",
          abs(well_dia - p.well_dia) < MEASURE_TOL_MM,
          f"measured {well_dia:.2f}mm vs {p.well_dia}mm")

    clearance_per_side = (well_dia - tile_dia_mm) / 2.0
    check("interface1: tile-in-well clearance matches brief's stated 1.0mm/side",
          abs(clearance_per_side - 1.0) < MEASURE_TOL_MM / 2.0,
          f"measured {clearance_per_side:.2f}mm/side")

    proud_mm = (p.tile_thickness + p.knob_h) - well_depth_meas
    check("interface1: seated knob stands proud of the rim by >= 2mm (retrieval pinch point)",
          proud_mm >= 2.0, f"measured {proud_mm:.2f}mm proud")


# ---------------------------------------------------------------------------
# Interface 2 — star_tile seats into reserve_column's bore.
#
# AMENDED: reserve_column is now two printed segments (reserve_column_lower /
# _upper). This checks the bore on EACH segment (the seat itself, unaffected
# by the split) plus a new sub-check for the dovetail/spigot seam interface
# (reserve_column/reserve_column joins, brief.json interfaces[3]): the bore
# and slot must both measure 24mm/9mm on BOTH sides of the seam, with no
# step, so a tile or a finger crossing the joint never catches.
# ---------------------------------------------------------------------------

def check_tile_seats_reserve_column(tile_dia_mm: float) -> None:
    lower = load("reserve_column_lower")
    upper = load("reserve_column_upper")
    # the full-height slot only removes a band near world +X (see
    # parts/reserve_column.py); bands near +Y/-Y measure the intact wall.
    # The bore's own bottom ring (z=0, local frame) carries clean wall
    # vertices in each segment; a wider z window catches that ring plus a
    # stray taper/chamfer vertex, which the median below shrugs off.
    for label, mesh, z_range in (
        ("reserve_column_lower (near its own base)", lower, (-1.0, 20.0)),
        ("reserve_column_upper (near its own base, just above the seam)", upper, (-1.0, 20.0)),
    ):
        bore_r = cylinder_wall_radius(
            mesh, (0.0, 0.0), angle_bands=[(60, 120), (240, 300)], r_max=20.0,
            z_range=z_range)
        bore_dia = 2.0 * bore_r
        check(f"interface2: {label} bore diameter measured from STL matches stated 24mm",
              abs(bore_dia - p.column_bore_dia) < MEASURE_TOL_MM,
              f"measured {bore_dia:.2f}mm vs {p.column_bore_dia}mm")

        clearance_per_side = (bore_dia - tile_dia_mm) / 2.0
        check(f"interface2: {label} tile-in-column clearance matches brief's stated "
              f"1.0mm/side (derived from the same tile diameter the well interface uses)",
              abs(clearance_per_side - 1.0) < MEASURE_TOL_MM / 2.0,
              f"measured {clearance_per_side:.2f}mm/side")


def check_reserve_column_segments_join() -> None:
    """New interface (brief.json, AMENDED): reserve_column/reserve_column
    joins — the dovetail/spigot seam between the two printed segments must
    keep the 24mm bore and 9mm slot continuous and flush, and the segments'
    own printed heights (what actually goes on the bed) must each clear the
    251mm usable bed z-limit."""
    lower = load("reserve_column_lower")
    upper = load("reserve_column_upper")

    lower_h = bbox_extents(lower)[2]
    upper_h = bbox_extents(upper)[2]
    expected_lower_h = p.column_seg_lower_h + p.column_tenon_h
    expected_upper_h = p.column_h - p.column_seg_lower_h
    check("interface(join): reserve_column_lower printed height matches the "
          "lower taper span + tenon boss",
          abs(lower_h - expected_lower_h) < MEASURE_TOL_MM,
          f"measured {lower_h:.2f}mm vs {expected_lower_h}mm")
    check("interface(join): reserve_column_upper printed height matches the "
          "cap taper span",
          abs(upper_h - expected_upper_h) < MEASURE_TOL_MM,
          f"measured {upper_h:.2f}mm vs {expected_upper_h}mm")

    BED_USABLE_Z_MM = 251.0
    check("interface(join): reserve_column_lower fits the 251mm usable bed z-limit",
          lower_h <= BED_USABLE_Z_MM, f"measured {lower_h:.2f}mm")
    check("interface(join): reserve_column_upper fits the 251mm usable bed z-limit",
          upper_h <= BED_USABLE_Z_MM, f"measured {upper_h:.2f}mm")
    check("interface(join): assembled total (seam split + segments) matches the "
          "amended 306mm column_h",
          abs((p.column_seg_lower_h + expected_upper_h) - p.column_h) < 1e-6,
          f"{p.column_seg_lower_h} + {expected_upper_h} vs {p.column_h}")

    # Bore/slot continuity right at the seam-facing end of each segment: the
    # lower segment's TOP (through the tenon boss) and the upper segment's
    # BOTTOM (through the socket) must both still measure the plain 24mm
    # bore / 9mm slot — the register only narrows the OUTER wall, never the
    # tile channel, so nothing steps or ridges where a tile or a finger
    # crosses the joint.
    lower_top_bore_r = cylinder_wall_radius(
        lower, (0.0, 0.0), angle_bands=[(60, 120), (240, 300)], r_max=20.0,
        z_range=(lower_h - 6.0, lower_h + 1.0))
    # The socket pocket (0..tenon_h, local) is wider than the 24mm bore on
    # every side (see check below), so it fully swallows any standalone bore
    # wall inside that band -- there is nothing bore-shaped to measure until
    # just ABOVE the socket, where the upper segment's plain taper (and its
    # plain circular bore) resumes.
    upper_above_socket_bore_r = cylinder_wall_radius(
        upper, (0.0, 0.0), angle_bands=[(60, 120), (240, 300)], r_max=20.0,
        z_range=(p.column_tenon_h - 0.5, p.column_tenon_h + 6.0))
    check("interface(join): bore diameter through the lower segment's tenon "
          "boss still matches 24mm (register doesn't narrow the tile channel)",
          abs(2.0 * lower_top_bore_r - p.column_bore_dia) < MEASURE_TOL_MM,
          f"measured {2.0 * lower_top_bore_r:.2f}mm vs {p.column_bore_dia}mm")
    check("interface(join): bore diameter on the upper segment just above its "
          "socket band still matches 24mm (the plain bore resumes cleanly "
          "once clear of the register, with nothing narrower in between)",
          abs(2.0 * upper_above_socket_bore_r - p.column_bore_dia) < MEASURE_TOL_MM,
          f"measured {2.0 * upper_above_socket_bore_r:.2f}mm vs {p.column_bore_dia}mm")

    # Slot channel open through the register band: the slot cutter (see
    # parts/reserve_column.py's _slot_cutter) removes ALL material for
    # |y| <= slot_w/2 out past the actual taper edge, so a point just outside
    # the bore's own wall, on the slot's centerline, must be OUTSIDE the
    # remaining solid on both sides of the seam -- proof the register boss/
    # socket doesn't cap the slot shut where a finger would cross it.
    def _point_is_outside_solid(mesh: trimesh.Trimesh, point) -> bool:
        # A point is outside a watertight mesh iff no vertex of the solid
        # lies within a tight radius of it while the solid's own surface at
        # that XY is provably farther out; simplest robust proxy available
        # without ray-casting (no rtree/embree in this sandbox, see module
        # docstring): no mesh vertex at all falls inside a small sphere
        # around the point AND inside the point's own z-band, since a plain
        # open channel carries no wall geometry through its interior.
        v = np.asarray(mesh.vertices)
        d = np.linalg.norm(v - np.asarray(point), axis=1)
        return bool((d < 1.5).sum() == 0)

    bore_r = p.column_bore_dia / 2.0
    slot_probe_x = bore_r + 2.0  # just outside the bore wall, inside the slot band
    lower_probe = (slot_probe_x, 0.0, lower_h - p.column_tenon_h / 2.0)
    upper_probe = (slot_probe_x, 0.0, p.column_tenon_h / 2.0)
    check("interface(join): read-slot stays open through the lower segment's "
          "tenon boss (no wall vertex found on the slot centerline)",
          _point_is_outside_solid(lower, lower_probe),
          f"probed {lower_probe}")
    check("interface(join): read-slot stays open through the upper segment's "
          "socket band (no wall vertex found on the slot centerline)",
          _point_is_outside_solid(upper, upper_probe),
          f"probed {upper_probe}")

    # Register geometry actually present: the tenon boss's own half-width
    # (measured on the intact -X side, away from the slot) must be smaller
    # than the seam's nominal taper half-width by roughly column_tenon_offset
    # -- proof a real step exists, not a flush continuation with no register.
    # A plain extruded box's flat side wall (the tenon boss's own outer
    # face) only carries mesh vertices at its CORNERS, not along the
    # mid-edge (the same "straight wall -> end vertices only" property this
    # whole module's docstring relies on, just in the XY plane instead of
    # Z) -- so search for the most negative X vertex at ANY y, not a narrow
    # y-band around 0 which would miss every corner. z=lower_h (the tenon's
    # own base) is excluded on purpose: the union of the tenon with the
    # nominal taper top leaves a real, physical shoulder ring there (the
    # loft's own 27.94mm-half-width top-face corners, wider than the tenon,
    # a genuine z-stop for the assembled joint) -- picking that up instead
    # of the tenon's own 25.44mm corner would read as "no register" when a
    # register (plus a shoulder stop) is exactly what's there. z=lower_h +
    # column_tenon_h (the tenon's own top cap) is unambiguous: only the
    # tenon boss exists at that height, nothing wider underneath it.
    seam_width = p.column_base + (p.column_shaft - p.column_base) * (
        p.column_seg_lower_h / p.column_h)
    v_lower = np.asarray(lower.vertices)
    # lower_h (measured above) IS the tenon's own top-cap z: the segment's
    # nominal loft ends at the seam (column_seg_lower_h) and the tenon boss
    # is the ONLY thing above that, so the printed part's overall top face
    # (its max Z, == lower_h) is the tenon's own cap ring, unambiguous.
    tenon_band = v_lower[np.isclose(v_lower[:, 2], lower_h)]
    tenon_half_w = float(-tenon_band[:, 0].min()) if tenon_band.size else float("nan")
    check("interface(join): a tenon register step exists on the lower "
          "segment (its boss band is narrower than the seam's nominal taper "
          "width)",
          tenon_band.size > 0 and tenon_half_w < seam_width / 2.0 - 0.5,
          f"tenon half-width(-X) ~{tenon_half_w:.2f}mm vs seam nominal "
          f"half-width {seam_width / 2.0:.2f}mm")


def check_reserve_column_capacity() -> None:
    """AMENDED: reserve_column must physically hold all 20 reserve tiles (30
    total minus 10 seeded into wells) stacked knob-up inside its bore, not
    a partial stack plus an off-column waiting grid (brief.json's
    unstated_in_spec explicitly rules that escape hatch out). Measured two
    ways, not just asserted against Params:

    1. assemblies/product.py's OWN placement function -- the code that
       actually decides where each tile goes in the built assembly -- is
       called for all 20 reserve indices and checked against the column's
       own world center, proving none of them fell through to the old
       side-grid fallback.
    2. the true 300mm span 20 tiles need at their physically-forced 15mm
       pitch is compared against the MEASURED combined length of the two
       real exported STL segments (reserve_column_lower's nominal taper +
       reserve_column_upper), not the Params number.
    """
    true_pitch = p.tile_thickness + p.knob_h
    inside_count = int((p.column_h - p.column_top_chamfer * 2) // true_pitch)
    check("interface2(capacity): the bore holds >=20 tiles at the true "
          "15mm knob-up pitch (6mm body + 9mm knob, no nesting possible)",
          inside_count >= p.column_reserve_tiles,
          f"bore holds {inside_count} tiles at the {true_pitch}mm pitch, "
          f"need {p.column_reserve_tiles}")

    positions = [_reserve_slot_position(i, p) for i in range(p.column_reserve_tiles)]
    cx, cy, _ = _COLUMN_CENTER
    all_inside = all(abs(x - cx) < 1e-6 and abs(y - cy) < 1e-6 for x, y, _ in positions)
    check("interface2(capacity): product.py's own placement puts all 20 "
          "reserve tiles on the column's own bore axis (none fell through "
          "to the old off-column waiting-grid fallback)",
          all_inside, f"{len(positions)} positions checked against center {_COLUMN_CENTER}")

    top_tile_z = max(z for _, _, z in positions)
    required_span = top_tile_z + true_pitch  # the last tile's own full height
    measured_lower_nominal = bbox_extents(load("reserve_column_lower"))[2] - p.column_tenon_h
    measured_upper = bbox_extents(load("reserve_column_upper"))[2]
    measured_total_span = measured_lower_nominal + measured_upper
    check("interface2(capacity): the true 300mm span 20 tiles need fits "
          "inside the MEASURED combined length of the two real printed "
          "segments (reserve_column_lower + reserve_column_upper STLs), "
          "not just the Params number",
          required_span <= measured_total_span,
          f"required {required_span:.2f}mm vs measured combined "
          f"{measured_total_span:.2f}mm (lower nominal "
          f"{measured_lower_nominal:.2f}mm + upper {measured_upper:.2f}mm)")


# ---------------------------------------------------------------------------
# Interface 3 — star_tile / moon_tile stand ON EDGE in a score_rail slot.
# ---------------------------------------------------------------------------

def check_tile_seats_score_rail(tile_dia_mm: float, tile_thickness_mm: float) -> None:
    rail = load("score_rail_tri")
    half_len = p.rail_slot_len / 2.0  # a plain rectangular slot's side walls
                                       # carry vertices only at its two ends

    # y-search bands wide enough for each slot's own two walls (y_center +/-
    # ~half the slot width) but excluding the OTHER slot and the rear
    # ledge's tick-mark holes (centered near y=14, see parts/score_rail.py).
    slot_bands = {
        "front slot": (-p.rail_w / 4.0, (-15.0, 0.0)),
        "raised rear (zenith) slot": (p.rail_w / 4.0, (0.0, 12.0)),
    }

    for label, top_expected, floor_expected in (
        ("front slot", p.rail_h, p.rail_h - p.rail_slot_depth),
        ("raised rear (zenith) slot",
         p.rail_h + p.rail_zenith_step_h,
         p.rail_h + p.rail_zenith_step_h - p.rail_slot_depth),
    ):
        y_center, y_range = slot_bands[label]
        y_lo, y_hi = rect_wall_span(rail, x_range=(half_len - 2.0, half_len + 2.0),
                                    y_range=y_range)
        slot_w = y_hi - y_lo
        check(f"interface3: {label} width measured from STL matches stated 6.6mm",
              abs(slot_w - p.rail_slot_w) < MEASURE_TOL_MM,
              f"measured {slot_w:.2f}mm vs {p.rail_slot_w}mm")

        clearance_per_side = (slot_w - tile_thickness_mm) / 2.0
        check(f"interface3: {label} standing-tile clearance matches brief's stated "
              f"0.3mm/side (tight, kept as idea.json states it)",
              abs(clearance_per_side - 0.3) < MEASURE_TOL_MM / 2.0,
              f"measured {clearance_per_side:.2f}mm/side")

        # the wall vertices sit exactly half the slot width from center
        # (~3.3mm) — a 4mm XY radius reliably catches them.
        top_z = z_at(rail, top_expected, (half_len, y_center), xy_radius=4.0)
        floor_z = z_at(rail, floor_expected, (half_len, y_center), xy_radius=4.0)
        slot_depth = top_z - floor_z
        check(f"interface3: {label} depth measured from STL matches stated 11mm",
              abs(slot_depth - p.rail_slot_depth) < MEASURE_TOL_MM,
              f"measured {slot_depth:.2f}mm vs {p.rail_slot_depth}mm")

        proud_mm = tile_dia_mm - slot_depth
        check(f"interface3: {label} standing tile sits proud by roughly its own "
              f"radius (half-buried, well past the 2mm retrieval minimum)",
              proud_mm >= 2.0, f"measured {proud_mm:.2f}mm proud")


# ---------------------------------------------------------------------------
# Interface 4 — mask_disc_a/b/c JOIN plinth_ring on the shared axle/bore.
# ---------------------------------------------------------------------------

def check_discs_join_axle() -> None:
    ring = load("plinth_ring")
    # the axle stands alone above the drum, a plain feature-free cylinder
    # from z=plinth_drum_h to z=plinth_drum_h+axle_rise — its base ring
    # (where it meets the drum's top face) and its top-cap ring both carry
    # clean wall vertices at every angle.
    axle_r = cylinder_wall_radius(
        ring, (0.0, 0.0), angle_bands=None, r_max=30.0)
    axle_dia = 2.0 * axle_r
    check("interface4: plinth axle diameter measured from STL matches stated 24mm",
          abs(axle_dia - p.axle_dia) < MEASURE_TOL_MM,
          f"measured {axle_dia:.2f}mm vs {p.axle_dia}mm")

    for name in ("mask_disc_a", "mask_disc_b", "mask_disc_c"):
        disc = load(name)
        # the bore is a plain annulus at the disc's own center; the nearest
        # window sits at the 80mm ring, far from the 12.5mm bore radius.
        bore_r = cylinder_wall_radius(
            disc, (0.0, 0.0), angle_bands=None, r_max=20.0)
        bore_dia = 2.0 * bore_r
        check(f"interface4: {name} bore diameter measured from STL matches stated 25mm",
              abs(bore_dia - p.disc_bore_dia) < MEASURE_TOL_MM,
              f"measured {bore_dia:.2f}mm vs {p.disc_bore_dia}mm")

        clearance_per_side = (bore_dia - axle_dia) / 2.0
        check(f"interface4: {name} rides the axle with the brief's stated "
              f"0.5mm/side loose rotating clearance",
              abs(clearance_per_side - 0.5) < MEASURE_TOL_MM / 2.0,
              f"measured {clearance_per_side:.2f}mm/side")

    # engagement: 3 discs x disc_track_h each must stay within axle_rise,
    # per the assembly's own stacking formula (assemblies/product.py).
    engagement = 3 * p.disc_track_h
    check("interface4: 18mm of stacked bore engagement fits inside the 40mm axle",
          engagement <= p.axle_rise,
          f"engagement={engagement}mm, axle_rise={p.axle_rise}mm, "
          f"{p.axle_rise - engagement}mm exposed above the top disc (no cap, per brief)")


# ---------------------------------------------------------------------------
# Interface 5 — mask_disc_a/b/c STACK on plinth_ring's rim ledge (a, b, c).
# ---------------------------------------------------------------------------

def check_discs_stack_stable() -> None:
    disc = load("mask_disc_a")
    ext = bbox_extents(disc)
    disc_dia_meas = max(ext[0], ext[1])  # includes the grip-tab projection, conservative
    stack_h = 3 * p.disc_rim_h
    check("interface5: 3-disc stack footprint (>=216mm) dwarfs its own stack "
          "height (27mm) — far too wide to topple",
          disc_dia_meas > 5.0 * stack_h,
          f"disc extent={disc_dia_meas:.2f}mm vs stack height={stack_h}mm")


def main() -> int:
    tiles = check_tile_family_identical()
    tile_ext = bbox_extents(tiles["star_tile"])
    tile_dia_meas = max(tile_ext[0], tile_ext[1])
    tile_thickness_meas = p.tile_thickness  # body thickness isn't a bbox extent
                                            # (the knob sits on top); use the
                                            # stated body dimension the blank
                                            # is extruded to, per parts/tile.py

    check_tile_seats_plinth_well(tile_dia_meas)
    check_tile_seats_reserve_column(tile_dia_meas)
    check_reserve_column_capacity()
    check_reserve_column_segments_join()
    check_tile_seats_score_rail(tile_dia_meas, tile_thickness_meas)
    check_discs_join_axle()
    check_discs_stack_stable()

    print()
    if FAILS:
        print(f"FIT CHECKS FAILED ({len(FAILS)}):")
        for f in FAILS:
            print(f"  - {f}")
        return 1
    print("FIT CHECKS: all interfaces fit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
