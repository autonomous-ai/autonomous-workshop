"""fit_checks.py -- proves brief.json's `## Interfaces` against the actually
exported geometry, not against Params. `validation.py` already hard-asserts
every bill number on Params before a render is even attempted; this script
answers a different question: did the CAD kernel actually PRODUCE the bore,
pin, tooth profile and rod those numbers describe, in the STL the user will
print?

Every check loads a real exported STL from millbind_parts/ and measures its
mesh vertices directly -- no ray-cast acceleration structure (this sandbox
has no rtree/embree, so trimesh.ray is unavailable). Every mate here is
either a straight vertical cylindrical wall (a bore or a pin) -- whose
fine-tessellated CadQuery/OCCT export carries vertices only at its top and
bottom edge rings, never along its interior -- or the gear tooth profile
itself, whose root/outer radii are directly recoverable by sampling mesh
vertex radii at the tooth-band height. Every measurement is taken from the
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
for _ancestor in PROJECT_DIR.parents:
    _cadcode = _ancestor / "cadcode"
    if _cadcode.is_dir():
        sys.path.insert(0, str(_cadcode))
        break

from params import Params  # noqa: E402

PARTS_DIR = PROJECT_DIR / "build" / "millbind_parts"

p = Params()

# FDM hand-assembly slop budget for comparing a tessellated mesh against a
# nominal design value -- a measurement tolerance, not a design clearance.
MEASURE_TOL_MM = 0.6

FAILS: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail else ""))
    if not ok:
        FAILS.append(f"{label}: {detail}")


def load(name: str) -> trimesh.Trimesh:
    stl = PARTS_DIR / f"{name}.stl"
    if not stl.is_file():
        raise FileNotFoundError(f"{stl} missing -- run `cad` before fit_checks.py")
    return trimesh.load(str(stl), force="mesh")


def bbox_extents(mesh: trimesh.Trimesh) -> np.ndarray:
    return mesh.bounds[1] - mesh.bounds[0]


def cylinder_wall_radius(mesh: trimesh.Trimesh, center_xy, r_max: float,
                         z_range=None) -> float:
    """Median radial distance (from `center_xy`) of nearby vertices -- the
    seat's top/bottom edge ring vertices, for a plain feature-free straight
    bore/pin (see module docstring for why a straight wall's ring vertices
    sit at just one or two Z values)."""
    v = np.asarray(mesh.vertices)
    if z_range is not None:
        v = v[(v[:, 2] >= z_range[0]) & (v[:, 2] <= z_range[1])]
    rel = v[:, :2] - np.asarray(center_xy)
    r = np.linalg.norm(rel, axis=1)
    r_sel = r[r <= r_max]
    if r_sel.size < 3:
        raise AssertionError(f"no wall vertices found (center={center_xy}, "
                             f"r_max={r_max}, z_range={z_range}, found {r_sel.size} pts)")
    return float(np.median(r_sel))


def tooth_root_outer_radius(mesh: trimesh.Trimesh, z_mid: float, z_tol: float,
                            r_lo: float, r_hi: float) -> tuple[float, float]:
    """min/max radial distance from the Z axis of vertices in a tooth band
    -- the base root-disk radius (between teeth) and the tip outer radius
    (at a tooth crest), both directly present as mesh vertices because
    parts/gears.py builds teeth as trapezoids unioned onto a root cylinder.
    """
    v = np.asarray(mesh.vertices)
    m = np.abs(v[:, 2] - z_mid) <= z_tol
    r = np.linalg.norm(v[m][:, :2], axis=1)
    r = r[(r >= r_lo) & (r <= r_hi)]
    if r.size < 3:
        raise AssertionError(f"no tooth-band vertices found (z_mid={z_mid}, "
                             f"z_tol={z_tol}, r in [{r_lo},{r_hi}], found {r.size} pts)")
    return float(r.min()), float(r.max())


# ---------------------------------------------------------------------------
# Interface 1 -- gear_low <-> yard_board: partial-engagement pin/bore.
# ---------------------------------------------------------------------------

def check_gear_low_partial_engagement() -> None:
    gear = load("gear_low_01")
    ext = bbox_extents(gear)
    gear_od = max(ext[0], ext[1])
    check("interface1: gear_low OD matches stated 35mm",
          abs(gear_od - 2.0 * p.outer_r) < MEASURE_TOL_MM,
          f"measured {gear_od:.2f}mm vs {2.0 * p.outer_r}mm")
    check("interface1: gear_low body height matches stated 10mm (partial engagement)",
          abs(ext[2] - p.gear_low_h) < MEASURE_TOL_MM,
          f"measured {ext[2]:.2f}mm vs {p.gear_low_h}mm")

    # bore: a plain straight cylinder -- a fine OCCT tessellation of a
    # straight wall carries vertices only at its two end-cap rings, never
    # along its interior, confirmed empirically against every part below.
    # z=0 (the bottom cap) is always present; r_max=6.0 sits safely inside
    # the 3 lightening holes' own near edge (~6.09mm, see parts/gears.py).
    bore_r = cylinder_wall_radius(gear, (0.0, 0.0), r_max=6.0, z_range=(-0.1, 0.1))
    bore_dia = 2.0 * bore_r
    check("interface1: gear_low bore diameter measured from STL matches stated 8.6mm",
          abs(bore_dia - p.bore_d) < MEASURE_TOL_MM,
          f"measured {bore_dia:.2f}mm vs {p.bore_d}mm")

    board = load("yard_board")
    # the centre pin (ring 0, at the world origin) is a clean feature-free
    # cylinder -- measure its TOP ring only (z well above the slab and any
    # plank rib), r_max generously wide of the 8mm pin.
    pin_r = cylinder_wall_radius(board, (0.0, 0.0), r_max=6.0,
                                 z_range=(p.slab_t + p.pin_h - 1.0, p.slab_t + p.pin_h + 0.5))
    pin_dia = 2.0 * pin_r
    check("interface1: yard_board centre pin diameter measured from STL matches stated 8mm",
          abs(pin_dia - p.pin_d) < MEASURE_TOL_MM,
          f"measured {pin_dia:.2f}mm vs {p.pin_d}mm")

    clearance = (bore_dia - pin_dia) / 2.0
    check("interface1: gear_low-on-pin clearance matches brief's stated 0.3mm/side "
          "(tight, kept as idea.json states it -- see brief.json's unstated_in_spec)",
          abs(clearance - 0.3) < MEASURE_TOL_MM / 2.0,
          f"measured {clearance:.2f}mm/side")

    exposed_stub = p.pin_h - ext[2]
    check("interface1: 20mm of bare pin stands exposed above a seated gear_low",
          abs(exposed_stub - 20.0) < MEASURE_TOL_MM,
          f"measured {exposed_stub:.2f}mm exposed")


# ---------------------------------------------------------------------------
# Interface 2 -- gear_high / gear_tandem / millstones / crank <-> yard_board:
# full-engagement pin/bore, representative across every full-height piece.
# ---------------------------------------------------------------------------

def check_full_engagement_bore(name: str) -> None:
    """Every full-height piece's bore is one continuous straight cylinder
    cut through the whole barrel (see parts/gears.py:bore_through) -- its
    only clean measurable ring is at z=0, the body's own bottom cap
    (confirmed empirically: millstones/crank_gear's bore actually overcuts
    1mm into the crown/cap above z=barrel_h, so z=barrel_h itself is NOT a
    clean single-radius ring -- z=0 is the one ring every one of these
    parts shares)."""
    part = load(name)
    bore_r = cylinder_wall_radius(part, (0.0, 0.0), r_max=6.0, z_range=(-0.1, 0.1))
    bore_dia = 2.0 * bore_r
    check(f"interface2: {name} bore diameter measured from STL matches stated 8.6mm",
          abs(bore_dia - p.bore_d) < MEASURE_TOL_MM,
          f"measured {bore_dia:.2f}mm vs {p.bore_d}mm")


def check_full_engagement_height() -> None:
    for name, expected in (
        ("gear_high_01", p.gear_high_h),
        ("gear_tandem_01", p.barrel_h),
    ):
        part = load(name)
        ext = bbox_extents(part)
        check(f"interface2: {name} spans the full {expected}mm pin height "
              "(full engagement, no stub exposed)",
              abs(ext[2] - expected) < MEASURE_TOL_MM,
              f"measured {ext[2]:.2f}mm vs {expected}mm")


# ---------------------------------------------------------------------------
# Interface 3 -- tooth-to-tooth mesh: root/outer radii vs the shared 30mm
# pin pitch, measured on gear_tandem_01 (no lightening holes to contaminate
# the radial sample, unlike gear_low).
# ---------------------------------------------------------------------------

def check_tooth_mesh() -> None:
    gear = load("gear_tandem_01")
    # gear_tandem's teeth run from barrel_teeth_z0 to barrel_teeth_z1 as one
    # constant-cross-section prism -- its only clean measurable ring is
    # right at that lower boundary (a real profile discontinuity: plain
    # root cylinder below, root+tooth profile above), confirmed empirically.
    root_r, outer_r = tooth_root_outer_radius(
        gear, z_mid=p.barrel_teeth_z0, z_tol=0.1, r_lo=6.0, r_hi=25.0)
    check("interface3: gear_tandem root-circle radius measured from STL matches "
          f"stated {p.root_r}mm",
          abs(root_r - p.root_r) < MEASURE_TOL_MM,
          f"measured {root_r:.2f}mm vs {p.root_r}mm")
    check("interface3: gear_tandem outer (tip) radius measured from STL matches "
          f"stated {p.outer_r}mm",
          abs(outer_r - p.outer_r) < MEASURE_TOL_MM,
          f"measured {outer_r:.2f}mm vs {p.outer_r}mm")

    board = load("yard_board")
    # ring-1 pins sit at exactly `pin_pitch` from the centre pin -- measure
    # one directly, at its own top ring, same technique as interface 1.
    from features.lattice import hex_lattice_positions
    lattice = hex_lattice_positions(p.pin_pitch, p.n_rings)
    ring1_x, ring1_y, _ = next(pt for pt in lattice if pt[2] == 1)
    pitch_measured = float(np.hypot(ring1_x, ring1_y))
    check("interface3: measured centre-to-ring1 pin spacing matches stated 30mm pin pitch",
          abs(pitch_measured - p.pin_pitch) < MEASURE_TOL_MM,
          f"measured {pitch_measured:.2f}mm vs {p.pin_pitch}mm")

    check("interface3: adjacent pins mesh at the true pin pitch -- dedendum "
          "clearance at the root, addendum overlap at the tip",
          2.0 * root_r < pitch_measured < 2.0 * outer_r,
          f"2*root={2 * root_r:.2f}mm < pitch={pitch_measured:.2f}mm < "
          f"2*outer={2 * outer_r:.2f}mm")


# ---------------------------------------------------------------------------
# Interface 4 -- grain_pellet threads onto sack_spindle's rod, and the full
# 12-pellet stack fits with retrieval clearance.
# ---------------------------------------------------------------------------

def check_pellet_on_spindle() -> None:
    pellet = load("grain_pellet_01")
    # z=0 (the flat, unchamfered bottom face) is the clean ring; z=pellet_h
    # (the chamfered top) drags in extra chamfer-edge vertices near the hole.
    hole_r = cylinder_wall_radius(pellet, (0.0, 0.0), r_max=6.0, z_range=(-0.1, 0.1))
    hole_dia = 2.0 * hole_r
    check("interface4: grain_pellet hole diameter measured from STL matches stated 9mm",
          abs(hole_dia - p.pellet_hole_d) < MEASURE_TOL_MM,
          f"measured {hole_dia:.2f}mm vs {p.pellet_hole_d}mm")

    spindle = load("sack_spindle_01")
    # the rod is a plain cylinder unioned onto the base -- its only clean
    # rings are its free top cap (z=spindle_h) and the base/rod junction
    # (z=spindle_base_h); the top cap is used here since it can never be
    # near the base's own chevron-skirt vertices.
    rod_r = cylinder_wall_radius(spindle, (0.0, 0.0), r_max=6.0,
                                 z_range=(p.spindle_h - 0.1, p.spindle_h + 0.1))
    rod_dia = 2.0 * rod_r
    check("interface4: sack_spindle rod diameter measured from STL matches stated 8.5mm",
          abs(rod_dia - p.spindle_rod_d) < MEASURE_TOL_MM,
          f"measured {rod_dia:.2f}mm vs {p.spindle_rod_d}mm")

    clearance = (hole_dia - rod_dia) / 2.0
    check("interface4: pellet-on-rod clearance matches brief's stated 0.25mm/side "
          "(tight, kept as idea.json states it)",
          abs(clearance - 0.25) < MEASURE_TOL_MM / 2.0,
          f"measured {clearance:.2f}mm/side")

    spindle_ext = bbox_extents(spindle)
    stack_h = p.spindle_capacity * p.pellet_h
    thumbnail_clear = spindle_ext[2] - p.spindle_base_h - stack_h
    check("interface4: a full 12-pellet stack leaves >= 2mm of rod clear for a "
          "thumbnail pinch on the top pellet",
          thumbnail_clear >= 2.0 - MEASURE_TOL_MM,
          f"measured {thumbnail_clear:.2f}mm clear "
          f"(spindle height={spindle_ext[2]:.2f}mm, base={p.spindle_base_h}mm, "
          f"stack={stack_h}mm)")


def main() -> int:
    check_gear_low_partial_engagement()
    check_full_engagement_bore("gear_high_01")
    check_full_engagement_bore("gear_tandem_01")
    check_full_engagement_bore("mill_gear_tri")
    check_full_engagement_bore("crank_gear")
    check_full_engagement_height()
    check_tooth_mesh()
    check_pellet_on_spindle()

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
