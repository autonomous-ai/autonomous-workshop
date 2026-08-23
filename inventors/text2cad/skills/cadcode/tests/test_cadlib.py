"""Tests for the cadlib helper library + recipes.

These run each helper with representative params through the real sandbox
(``scripts/cad``) — same path the agent uses — so they catch sandbox
allow-list regressions and helper bugs in one shot.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"


def _run_cad(*args: str, timeout: int = 40) -> dict:
    cmd = [sys.executable, str(SCRIPTS / "cad"), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    out = (proc.stdout or "").strip().splitlines()
    if not out:
        return {
            "ok": False,
            "error": {
                "code": "RUNTIME_ERROR",
                "message": f"no stdout (stderr: {proc.stderr[:300]!r})",
            },
        }
    return json.loads(out[-1])


def _err_message(payload: dict) -> str:
    """Pull the human-readable string out of contract §3's error shape."""
    err = payload.get("error")
    if isinstance(err, dict):
        return str(err.get("message", ""))
    return str(err or "")


# -- Helpers compile in the sandbox -------------------------------------------

HELPER_PROBES = {
    "enclosure.hollow_box": """
from cadlib.enclosure import hollow_box
result = hollow_box(length=60, width=40, height=20, wall=2, corner_radius=3)
""",
    "enclosure.add_lid_lip": """
from cadlib.enclosure import add_lid_lip, hollow_box
base = hollow_box(length=60, width=40, height=20, wall=2)
result = add_lid_lip(base, length=60, width=40, wall=2)
""",
    "enclosure.lid_plate": """
from cadlib.enclosure import lid_plate
result = lid_plate(length=60, width=40, thickness=3, lip_clearance=0.3, wall=2, lip_height=2)
""",
    "mounting.add_screw_post": """
from cadlib.mounting import add_screw_post
from cadlib.layout import four_corner_points
import cadquery as cq
body = cq.Workplane("XY").box(40, 40, 4)
result = add_screw_post(
    body,
    positions=four_corner_points(length=40, width=40, margin=5),
    screw_size="M3", boss_height=8,
)
""",
    "mounting.add_heat_set_pocket": """
from cadlib.mounting import add_heat_set_pocket
import cadquery as cq
body = cq.Workplane("XY").box(40, 40, 12)
result = add_heat_set_pocket(body, positions=[(0, 0)], insert_size="M3")
""",
    "mounting.add_nut_trap": """
from cadlib.mounting import add_nut_trap
import cadquery as cq
body = cq.Workplane("XY").box(30, 30, 10)
result = add_nut_trap(body, positions=[(0, 0)], nut_size="M3")
""",
    "cutouts.add_press_fit_pocket": """
from cadlib.cutouts import add_press_fit_pocket
import cadquery as cq
body = cq.Workplane("XY").box(40, 40, 10)
result = add_press_fit_pocket(body, positions=[(0, 0)], insert_diameter=8, insert_depth=6)
""",
    "cutouts.add_magnet_pocket": """
from cadlib.cutouts import add_magnet_pocket
import cadquery as cq
body = cq.Workplane("XY").box(40, 40, 8)
result = add_magnet_pocket(body, positions=[(0, 0)], magnet_size="10x3")
""",
    "cutouts.add_bearing_seat": """
from cadlib.cutouts import add_bearing_seat
import cadquery as cq
body = cq.Workplane("XY").box(40, 40, 12)
result = add_bearing_seat(body, positions=[(0, 0)], bearing="608")
""",
    "cutouts.add_cable_channel": """
from cadlib.cutouts import add_cable_channel
import cadquery as cq
body = cq.Workplane("XY").box(60, 40, 8)
result = add_cable_channel(body, centerline=[(-25, 0), (25, 0)], cable_diameter=4.5)
""",
    "mechanical.add_dovetail_slot": """
from cadlib.mechanical import add_dovetail_slot
import cadquery as cq
body = cq.Workplane("XY").box(50, 30, 10)
result = add_dovetail_slot(body, position=(0, 0, 5), length=50, base_width=10, depth=4)
""",
    "mechanical.add_rib_stiffener": """
from cadlib.mechanical import add_rib_stiffener
import cadquery as cq
body = cq.Workplane("XY").box(60, 40, 2)
result = add_rib_stiffener(body, start=(-25, 0, 1), end=(25, 0, 1), height=8, thickness=1.2)
""",
    "layout.four_corner_points": """
import cadquery as cq
from cadlib.layout import four_corner_points
pts = four_corner_points(length=40, width=30, margin=5)
assert len(pts) == 4
result = cq.Workplane("XY").pushPoints(pts).circle(2).extrude(5)
""",
    "layout.grid_points": """
import cadquery as cq
from cadlib.layout import grid_points
pts = grid_points(n_x=3, n_y=2, pitch_x=10)
result = cq.Workplane("XY").pushPoints(pts).circle(2).extrude(5)
""",
    "kinematics.four_bar_loop": """
import cadquery as cq
from cadlib.kinematics import solve_fourbar, place_two_point
COUPLER, ROCKER = 20.0, 20.0
B, D = (8.0, -13.0), (-16.0, -13.0)           # crank pin, ground pivot (X-Z)
C = solve_fourbar(crank_pin=B, ground_pivot=D, coupler=COUPLER, rocker=ROCKER, branch="right")
w = lambda p: (p[0], 0.0, p[1])               # X-Z plane at one Y station -> 3D
def bar(length):
    b = cq.Workplane("XY").center(length/2, 0).box(length, 6, 4, centered=(True, True, False))
    b = b.union(cq.Workplane("XY").circle(4).extrude(4))
    b = b.union(cq.Workplane("XY").center(length, 0).circle(4).extrude(4))
    return b
leg = place_two_point(bar(COUPLER), p0_local=(0,0,0), p1_local=(COUPLER,0,0), p0_world=w(B), p1_world=w(C))
rk  = place_two_point(bar(ROCKER),  p0_local=(0,0,0), p1_local=(ROCKER,0,0),  p0_world=w(D), p1_world=w(C))
result = leg.union(rk)
assert len(result.solids().vals()) == 1, "linkage did not close into one solid"
""",
}


@pytest.mark.parametrize("name,code", list(HELPER_PROBES.items()), ids=list(HELPER_PROBES))
def test_helper_compiles(name: str, code: str):
    """Each helper produces a valid solid when called with representative params."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"{name.replace('.', '_')}.py"
        src.write_text(code)
        payload = _run_cad(str(src), "--out-dir", tmp)
        assert payload.get("ok"), f"{name} failed: {payload}"
        assert payload.get("is_solid"), f"{name} produced non-solid"
        assert payload.get("volume_mm3", 0) > 0


# -- Recipes produce STLs -----------------------------------------------------

RECIPES = sorted((SKILL_DIR / "recipes").glob("*.py")) if (SKILL_DIR / "recipes").exists() else []


@pytest.mark.parametrize("recipe", RECIPES, ids=lambda p: p.stem)
def test_recipe_produces_stl(recipe: Path):
    """Each recipe in skills/cadcode/recipes/ must compile and export STL."""
    with tempfile.TemporaryDirectory() as tmp:
        payload = _run_cad(str(recipe), "--out-dir", tmp)
        assert payload.get("ok"), f"{recipe.name} failed: {payload}"
        assert payload.get("is_solid"), f"{recipe.name} non-solid"
        stl = Path(tmp) / f"{recipe.stem}.stl"
        assert stl.exists() and stl.stat().st_size > 1000, (
            f"{recipe.name} did not produce a real STL"
        )


# -- Helper-specific geometry checks ------------------------------------------


def test_heat_set_pocket_cuts_rim_relief():
    """add_heat_set_pocket must counterbore the rim relief (relief_d × relief_h
    from HEATSET_TABLE), not just a plain body pocket — the relief is where the
    plastic displaced during reflow goes. Regression for the helper ignoring
    the relief_* columns it reads from the table."""
    import cadquery as cq
    from cadlib.mounting import add_heat_set_pocket
    from cadlib.tables import HEATSET_TABLE

    h = HEATSET_TABLE["M3"]
    depth = h["insert_len"] + 1.5
    with_relief = add_heat_set_pocket(
        cq.Workplane("XY").box(40, 40, 12), positions=[(0, 0)], insert_size="M3"
    )
    plain = (
        cq.Workplane("XY").box(40, 40, 12)
        .faces(">Z").workplane().pushPoints([(0, 0)]).hole(h["pocket_d"], depth=depth)
    )
    # The relief removes extra material at the rim, so the relieved part has
    # strictly less volume than a plain-pocket part of the same dimensions.
    assert with_relief.val().Volume() < plain.val().Volume(), (
        "heat-set pocket did not cut the rim relief"
    )


def test_mating_fits_derive_both_halves_from_one_nominal():
    """The fit primitive picks the correct FDM clearance for a named class and
    derives the female (``slot_for``) and male (``peg_for``) halves from ONE
    nominal, so a tab and its slot can never drift apart. Unknown fit classes
    raise (the spec is wrong), not silently default."""
    from cadlib.fits import FIT_TABLE, mating_clearance, peg_for, slot_for

    # slip is the default assembled fit; classes are ordered tight -> loose.
    assert mating_clearance("slip") == pytest.approx(0.20)
    assert (
        mating_clearance("snug")
        < mating_clearance("slip")
        < mating_clearance("free")
    )
    # A female opening for a 10 mm male grows by 2x clearance; a male peg for a
    # 10 mm female shrinks by 2x clearance — symmetric around the nominal.
    assert slot_for(10.0, "slip") == pytest.approx(10.40)
    assert peg_for(10.0, "slip") == pytest.approx(9.60)
    assert slot_for(10.0, "slip") - 10.0 == pytest.approx(10.0 - peg_for(10.0, "slip"))
    # Every class is a real per-side clearance value.
    assert set(FIT_TABLE) >= {"snug", "slip", "free"}
    # Bad inputs point at the spec, not at OCCT five frames deep.
    with pytest.raises(ValueError):
        mating_clearance("snug-ish")
    with pytest.raises(ValueError):
        peg_for(0.1, "free")  # clearance larger than the hole


def test_print_in_place_gap_is_open_on_every_face_and_larger_in_z():
    """Parts printed together must leave an OPEN gap on every face or they fuse.
    The helper gives looser-than-assembled per-face gaps, a vertical gap STRICTLY
    larger than the horizontal one (the gap ceiling sags and bonds), a bottom
    chamfer for elephant's foot, and an ooze bump for PETG."""
    from cadlib.fits import PIP_FIT_TABLE, print_in_place_gap

    g = print_in_place_gap()  # default: sliding, PLA, 0.2 layer
    assert g["xy"] == pytest.approx(0.30)
    # Z MUST exceed XY — the core print-in-place rule (bridge sag + elephant foot).
    assert g["z"] > g["xy"]
    assert g["z"] == pytest.approx(0.30 + 0.2)
    assert g["bottom_chamfer"] > 0
    # Print-in-place fits are looser than the tightest assembled fit, and ordered.
    assert PIP_FIT_TABLE["tight"] < PIP_FIT_TABLE["sliding"] < PIP_FIT_TABLE["loose"]
    # Ooze-prone filaments get a little more XY gap.
    assert print_in_place_gap(material="PETG")["xy"] > print_in_place_gap()["xy"]
    # The Z > XY invariant holds across every fit class.
    for fit in PIP_FIT_TABLE:
        gg = print_in_place_gap(fit)
        assert gg["z"] > gg["xy"], fit
    # Bad inputs point at the spec.
    with pytest.raises(ValueError):
        print_in_place_gap("snug")  # an assembled-fit name, not a PiP class
    with pytest.raises(ValueError):
        print_in_place_gap(layer_height=0)


def test_solve_fourbar_closes_the_loop():
    """solve_fourbar returns the one joint both links reach: |C-B| == coupler
    and |C-D| == rocker. The two branches are distinct elbows, and link lengths
    that can't span the pivots raise ValueError (the spec is wrong, not OCCT)."""
    import math
    from cadlib.kinematics import circle_intersections, solve_fourbar

    B, D = (8.0, -13.0), (-16.0, -13.0)
    coupler = rocker = 20.0
    C = solve_fourbar(
        crank_pin=B, ground_pivot=D, coupler=coupler, rocker=rocker, branch="right"
    )
    assert math.dist(C, B) == pytest.approx(coupler, abs=1e-6)
    assert math.dist(C, D) == pytest.approx(rocker, abs=1e-6)

    other = solve_fourbar(
        crank_pin=B, ground_pivot=D, coupler=coupler, rocker=rocker, branch="left"
    )
    assert math.dist(other, C) > 1.0, "left/right branches must be distinct elbows"

    a, b = circle_intersections(c0=B, r0=coupler, c1=D, r1=rocker)
    for pt in (a, b):
        assert math.dist(pt, B) == pytest.approx(coupler, abs=1e-6)
        assert math.dist(pt, D) == pytest.approx(rocker, abs=1e-6)

    with pytest.raises(ValueError):  # links too short to span the pivots
        solve_fourbar(
            crank_pin=(0.0, 0.0), ground_pivot=(100.0, 0.0), coupler=10.0, rocker=10.0
        )


def test_place_two_point_rejects_rigid_mismatch():
    """A printed link is rigid: if its local pin spacing != the solved world
    span, place_two_point raises rather than silently leaving the far pin off
    its joint."""
    import cadquery as cq
    from cadlib.kinematics import place_two_point

    bar = cq.Workplane("XY").box(20, 6, 4)
    with pytest.raises(ValueError):
        place_two_point(
            bar,
            p0_local=(0, 0, 0), p1_local=(20, 0, 0),
            p0_world=(0, 0, 0), p1_world=(30, 0, 0),   # 30 != 20
        )


# -- The canonical multi-part exemplar fits, assembles, stays collision-clean --


def test_snap_lid_box_is_multipart_and_collision_and_fit_clean():
    """The canonical two-part exemplar must export as a real assembly (base+lid),
    seat in its assembled position WITHOUT interpenetration (collision-clean),
    and pass its own functional fit check — the whole 'parts work together' bar
    end to end. Regression for the multi-part fit discipline."""
    asset = SKILL_DIR / "assets" / "example_snap_lid_box.py"
    with tempfile.TemporaryDirectory() as tmp:
        payload = _run_cad(str(asset), "--out-dir", tmp)
    assert payload.get("ok"), payload
    names = {p["name"] for p in payload.get("parts", [])}
    assert names == {"base", "lid"}, f"expected a 2-part assembly, got {names}"
    kinds = {w["kind"] for w in payload.get("warnings", [])}
    assert "collision" not in kinds, payload.get("warnings")
    assert "functional" not in kinds, payload.get("warnings")


def test_drifted_lip_trips_the_collision_check():
    """Sizing the lid lip to the cavity OUTER (the classic 'forgot the wall +
    clearance' drift) makes it ram the base walls in the seated position. The
    deterministic collision check must catch it — proving the gate guards real
    mating geometry, which is exactly what ``peg_for`` prevents by construction."""
    code = """
import cadquery as cq
from cadlib.enclosure import hollow_box

def gen_step():
    L, W, H, wall, t, lip_h = 80, 60, 25, 2.0, 3.0, 10.0
    base = hollow_box(length=L, width=W, height=H, wall=wall)
    plate = cq.Workplane("XY").box(L, W, t)
    lip = cq.Workplane("XY").box(L, W, lip_h).translate((0, 0, -(t + lip_h) / 2))
    lid = plate.union(lip)
    asm = cq.Assembly()
    asm.add(base, name="base")
    asm.add(lid, name="lid", loc=cq.Location((0, 0, H / 2 + t / 2)))
    return asm
"""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "drifted_lid.py"
        src.write_text(code)
        payload = _run_cad(str(src), "--out-dir", tmp)
    assert payload.get("ok"), payload
    kinds = {w["kind"] for w in payload.get("warnings", [])}
    assert "collision" in kinds, f"drift bug should collide; got {payload.get('warnings')}"


# -- Sandbox still blocks third-party imports ---------------------------------


def test_sandbox_still_blocks_unknown_libs():
    """Adding cadlib to the allow-list shouldn't have opened up other libs."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "bad.py"
        src.write_text("import cq_warehouse\nresult = None\n")
        payload = _run_cad(str(src), "--out-dir", tmp)
        assert not payload["ok"]
        msg = _err_message(payload).lower()
        assert "cq_warehouse" in msg or "not allowed" in msg
