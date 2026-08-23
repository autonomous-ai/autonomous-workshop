"""Tests for the cadlib helper library + recipes.

These run each helper with representative params through the real sandbox
(``scripts/cad``) — same path the agent uses — so they catch sandbox
allow-list regressions and helper bugs in one shot.
"""

from __future__ import annotations

import json
import math
import runpy
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
    "enclosure.lid_with_skirt": """
from cadlib.enclosure import lid_with_skirt
result = lid_with_skirt(length=60, width=40, thickness=3, lip_clearance=0.3, wall=2, lip_height=2)
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
    "cutouts.add_rounded_side_wall_cutout": """
from cadlib.cutouts import add_rounded_side_wall_cutout, verify_side_wall_through_cut
from cadlib.enclosure import hollow_box
body = hollow_box(length=60, width=40, height=20, wall=2, corner_radius=3)
result = add_rounded_side_wall_cutout(
    body, side="+X", center=(30, 0, 0), width=12, height=6,
    wall_thickness=2, corner_radius=1,
)
proof = verify_side_wall_through_cut(
    result, side="+X", center=(30, 0, 0), width=12, height=6,
    wall_thickness=2,
)
assert proof["aperture_air_samples"] == 15
assert proof["adjacent_wall_samples"] == 12
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
    "validation.verify_bbox": """
import cadquery as cq
from cadlib.validation import verify_bbox
result = cq.Workplane("XY").box(20, 10, 6).translate((10, 5, 3))
proof = verify_bbox(
    shape=result,
    expected_size=(20, 10, 6),
    expected_min=(0, 0, 0),
    expected_max=(20, 10, 6),
    label="probe",
)
assert proof["size"] == [20.0, 10.0, 6.0]
""",
    "validation.verify_uniform_wall_thickness": """
import cadquery as cq
from cadlib.validation import verify_uniform_wall_thickness
wall = cq.Workplane("XY").circle(10).circle(8).extrude(12)
faces = wall.faces("%CYLINDER").vals()
outer = max(faces, key=lambda face: face.BoundingBox().xlen)
inner = min(faces, key=lambda face: face.BoundingBox().xlen)
proof = verify_uniform_wall_thickness(
    outer_face=outer, inner_face=inner, expected_thickness=2, label="tube wall",
)
assert abs(proof["thickness_mm"] - 2.0) < 1e-6
result = wall
""",
    "validation.verify_through_hole_pattern": """
import cadquery as cq
from cadlib.validation import verify_through_hole_pattern
centers = [(-6, 0), (6, 0)]
result = (
    cq.Workplane("XY").box(30, 20, 4)
    .faces(">Z").workplane().pushPoints(centers).hole(4)
)
proof = verify_through_hole_pattern(
    part=result, axis="z", centers=centers, diameter=4, span=(-2, 2),
)
assert proof["count"] == 2
assert proof["air_samples"] == 54
""",
    "validation.verify_rectangular_through_cut": """
import cadquery as cq
from cadlib.validation import verify_rectangular_through_cut
body = cq.Workplane("XY").box(30, 20, 10)
cutter = cq.Workplane("XY").box(32, 6, 4)
result = body.cut(cutter)
proof = verify_rectangular_through_cut(
    part=result, axis="x", center=(0, 0), size=(6, 4), span=(-15, 15),
)
assert proof["axis"] == "x"
assert proof["blocked_volume_mm3"] == 0
""",
    "validation.verify_clearance_box": """
import cadquery as cq
from cadlib.validation import verify_clearance_box
outer = cq.Workplane("XY").box(30, 20, 12, centered=(True, True, False))
cavity = cq.Workplane("XY").box(24, 14, 10).translate((0, 0, 7))
result = outer.cut(cavity)
proof = verify_clearance_box(
    part=result,
    expected_min=(-12, -7, 2),
    expected_max=(12, 7, 12),
    open_faces=("+Z",),
)
assert proof["open_faces"] == ["+Z"]
assert proof["blocked_volume_mm3"] == 0
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


@pytest.mark.parametrize(
    "recipe_name",
    ["electronics_enclosure.py", "magnetic_lid_box.py"],
)
def test_multi_part_recipes_export_named_part_stls(recipe_name: str):
    """A removable lid is an Assembly, never one fused teaching mesh."""
    recipe = SKILL_DIR / "recipes" / recipe_name
    with tempfile.TemporaryDirectory() as tmp:
        payload = _run_cad(str(recipe), "--out-dir", tmp)
        assert payload.get("ok"), payload
        assert {part["name"] for part in payload.get("parts", [])} == {"base", "lid"}
        for part in payload["parts"]:
            assert Path(part["stl_path"]).exists()


def test_open_storage_bin_recipe_proves_full_empty_cavity():
    module = runpy.run_path(str(SKILL_DIR / "recipes" / "open_storage_bin.py"))
    p = module["p"]
    cavity = module["cavity_proof"]
    extent = module["extent_proof"]

    assert cavity["size"] == pytest.approx(
        (p.width - 2 * p.wall, p.depth - 2 * p.wall, p.height - p.floor)
    )
    assert cavity["open_faces"] == ["+Z"]
    assert set(cavity["wall_faces"]) == {"-X", "+X", "-Y", "+Y", "-Z"}
    assert cavity["blocked_volume_mm3"] == pytest.approx(0.0, abs=1e-9)
    assert extent["size"] == pytest.approx((p.width, p.depth, p.height))
    json.dumps({"extent": extent, "cavity": cavity})


def test_electronics_recipe_preserves_literal_geometry():
    """The worked CREATE example proves dimensions on its generated solids."""
    import cadquery as cq

    module = runpy.run_path(str(SKILL_DIR / "recipes" / "electronics_enclosure.py"))
    base = module["base"]
    lid = module["lid"]
    p = module["p"]
    bbox = base.val().BoundingBox()

    assert (bbox.xlen, bbox.ylen, bbox.zlen) == pytest.approx(
        (p.length, p.width, p.height)
    )
    assert bbox.zmin == pytest.approx(-p.height / 2)
    assert bbox.zmax == pytest.approx(p.height / 2)

    xs = [point[0] for point in module["screw_pts"]]
    ys = [point[1] for point in module["screw_pts"]]
    assert len(module["screw_pts"]) == 4
    assert max(xs) - min(xs) == pytest.approx(p.pcb_pattern_length)
    assert max(ys) - min(ys) == pytest.approx(p.pcb_pattern_width)
    assert max(xs) + min(xs) == pytest.approx(0.0)
    assert max(ys) + min(ys) == pytest.approx(0.0)

    floor_z = -p.height / 2 + p.wall
    for x, y in module["screw_pts"]:
        for z in (floor_z + 0.1, floor_z + p.boss_height / 2, floor_z + p.boss_height - 0.1):
            assert not base.val().isInside(cq.Vector(x, y, z), 1e-6)
            assert base.val().isInside(
                cq.Vector(x + p.pcb_hole_diameter / 2 + 0.05, y, z), 1e-6
            )

    assembly = module["gen_step"]()
    assert set(assembly.objects) >= {"base", "lid"}
    lid_z = assembly.objects["lid"].loc.toTuple()[0][2]
    placed_lid = lid.translate((0, 0, lid_z))
    assert lid_z - p.lid_thickness / 2 == pytest.approx(bbox.zmax)
    assert sum(s.Volume() for s in base.intersect(placed_lid).solids().vals()) < 1e-6
    assert placed_lid.val().BoundingBox().zmin < bbox.zmax

    plate_underside = -p.lid_thickness / 2
    assert plate_underside - lid.val().BoundingBox().zmin == pytest.approx(
        p.lid_lip_depth
    )
    center_probe = (
        cq.Workplane("XY")
        .box(20, 20, p.lid_lip_depth / 2)
        .translate((0, 0, plate_underside - p.lid_lip_depth / 2))
    )
    assert sum(s.Volume() for s in lid.intersect(center_probe).solids().vals()) < 1e-6

    skirt_bbox = lid.faces("<Z").val().BoundingBox()
    assert (p.length - 2 * p.wall - skirt_bbox.xlen) / 2 == pytest.approx(
        p.lip_clearance
    )
    assert (p.width - 2 * p.wall - skirt_bbox.ylen) / 2 == pytest.approx(
        p.lip_clearance
    )
    assert module["usb_cutout_proof"] == {
        "side": "+X",
        "aperture_air_samples": 15,
        "adjacent_wall_samples": 12,
        "wall_thickness": p.wall,
    }
    extent = module["base_extent_proof"]
    assert extent["size"] == pytest.approx((p.length, p.width, p.height))
    assert extent["min"] == pytest.approx(
        (-p.length / 2, -p.width / 2, -p.height / 2)
    )
    assert extent["max"] == pytest.approx(
        (p.length / 2, p.width / 2, p.height / 2)
    )
    json.dumps(extent)  # proof is safe to carry into logs or project metadata


def test_lid_with_skirt_is_rounded_annular_and_exact_fit():
    import cadquery as cq
    from cadlib.enclosure import lid_with_skirt

    length, width, wall = 80.0, 60.0, 2.0
    clearance, depth, skirt_wall, radius = 0.3, 3.0, 1.2, 4.0
    lid = lid_with_skirt(
        length=length,
        width=width,
        thickness=3.0,
        corner_radius=radius,
        lip_clearance=clearance,
        wall=wall,
        lip_height=depth,
        lip_wall=skirt_wall,
    )

    assert lid.val().isValid()
    assert len(lid.solids().vals()) == 1
    assert -1.5 - lid.val().BoundingBox().zmin == pytest.approx(depth)
    skirt_bottom = lid.faces("<Z").val()
    skirt_bbox = skirt_bottom.BoundingBox()
    assert (length - 2 * wall - skirt_bbox.xlen) / 2 == pytest.approx(clearance)
    assert (width - 2 * wall - skirt_bbox.ylen) / 2 == pytest.approx(clearance)

    center_probe = cq.Workplane("XY").box(20, 20, depth / 2).translate((0, 0, -3.0))
    assert sum(s.Volume() for s in lid.intersect(center_probe).solids().vals()) < 1e-6
    arc_radii = [
        edge.radius()
        for edge in skirt_bottom.Edges()
        if edge.geomType() == "CIRCLE"
    ]
    assert any(r == pytest.approx(radius - wall - clearance) for r in arc_radii)


def test_lid_plate_keeps_legacy_solid_tongue_by_default():
    """Existing CREATE projects must rebuild without silent lid geometry drift."""
    import cadquery as cq
    from cadlib.enclosure import lid_plate

    lid = lid_plate(length=60, width=40, thickness=3, wall=2, lip_height=3)
    probe = cq.Workplane("XY").box(4, 4, 1).translate((0, 0, -2.5))
    assert sum(s.Volume() for s in lid.intersect(probe).solids().vals()) > 15.0


@pytest.mark.parametrize("lip_wall", [0.0, -0.1, 40.0])
def test_lid_with_skirt_rejects_invalid_wall(lip_wall: float):
    from cadlib.enclosure import lid_with_skirt

    with pytest.raises(ValueError, match="lip_wall"):
        lid_with_skirt(length=60, width=40, wall=2, lip_height=3, lip_wall=lip_wall)


def test_magnetic_lid_recipe_uses_supported_accessible_pockets():
    """D10 pockets cut wall-connected bosses and stay open at mating faces."""
    import cadquery as cq

    module = runpy.run_path(str(SKILL_DIR / "recipes" / "magnetic_lid_box.py"))
    before = module["base_before_pockets"]
    base = module["base"]
    lid = module["lid"]
    p = module["p"]

    assert before.val().Volume() - base.val().Volume() > 900.0
    assert len(base.solids().vals()) == 1
    assembly = module["gen_step"]()
    assert set(assembly.objects) >= {"base", "lid"}
    lid_z = assembly.objects["lid"].loc.toTuple()[0][2]
    assert lid_z == pytest.approx((p.height + p.lid_thickness) / 2 + p.lid_gap)

    base_bbox = base.val().BoundingBox()
    lid_bbox = lid.val().BoundingBox()
    assert lid_bbox.zmin + lid_z == pytest.approx(base_bbox.zmax + p.lid_gap)
    x, y = module["magnet_pts"][0]
    assert not base.val().isInside(cq.Vector(x, y, base_bbox.zmax), 1e-6)
    assert not lid.val().isInside(cq.Vector(x, y, lid_bbox.zmin), 1e-6)
    assert lid.val().isInside(cq.Vector(x, y, lid_bbox.zmax), 1e-6)


# -- Helper-specific geometry checks ------------------------------------------


def test_verify_bbox_proves_size_and_world_extents_on_final_shape():
    import cadquery as cq
    from cadlib.validation import verify_bbox

    shape = cq.Workplane("XY").box(20, 10, 6).translate((10, 5, 3)).val()
    proof = verify_bbox(
        shape=shape,
        expected_size=(20, 10, 6),
        expected_min=(0, 0, 0),
        expected_max=(20, 10, 6),
        label="translated body",
    )

    assert proof["size"] == pytest.approx([20.0, 10.0, 6.0])
    assert proof["min"] == pytest.approx([0.0, 0.0, 0.0])
    assert proof["max"] == pytest.approx([20.0, 10.0, 6.0])
    assert proof["tolerance"] == pytest.approx(0.01)
    json.dumps(proof)


def test_verify_uniform_wall_thickness_proves_parallel_conical_faces():
    import cadquery as cq
    from cadlib.validation import verify_uniform_wall_thickness

    height = 82.0
    thickness = 2.4
    slope = (50.0 - 40.0) / height
    radial_offset = thickness * math.sqrt(1.0 + slope * slope)
    outer = cq.Solid.makeCone(40.0, 50.0, height)
    inner = cq.Solid.makeCone(40.0 - radial_offset, 50.0 - radial_offset, height)
    outer_face = cq.Workplane(obj=outer).faces("%CONE").val()
    inner_face = cq.Workplane(obj=inner).faces("%CONE").val()

    proof = verify_uniform_wall_thickness(
        outer_face=outer_face,
        inner_face=inner_face,
        expected_thickness=thickness,
        tolerance=1e-4,
        label="taper wall",
    )

    assert proof["surface_type"] == "CONE"
    assert proof["thickness_mm"] == pytest.approx(thickness, abs=1e-6)
    json.dumps(proof)


def test_verify_uniform_wall_thickness_rejects_slope_transition_mismatch():
    import cadquery as cq
    from cadlib.validation import verify_uniform_wall_thickness

    outer_cylinder = cq.Workplane("XY").circle(50).extrude(5).faces("%CYLINDER").val()
    inner_cone = cq.Workplane(
        obj=cq.Solid.makeCone(47.58, 47.6, 5)
    ).faces("%CONE").val()

    with pytest.raises(ValueError, match="not a uniform analytic offset"):
        verify_uniform_wall_thickness(
            outer_face=outer_cylinder,
            inner_face=inner_cone,
            expected_thickness=2.4,
            tolerance=1e-4,
            label="top transition",
        )


def test_verify_bbox_allows_only_explicit_axes():
    import cadquery as cq
    from cadlib.validation import verify_bbox

    proof = verify_bbox(
        shape=cq.Workplane("XY").box(91, 47, 12).translate((100, -80, 6)),
        expected_size=(None, None, 12),
        expected_min=(None, None, 0),
        label="height-only stand",
    )

    assert proof["size"][2] == pytest.approx(12.0)
    assert proof["min"][2] == pytest.approx(0.0)


def test_verify_bbox_accounts_for_every_workplane_solid_not_only_val():
    import cadquery as cq
    from cadlib.validation import verify_bbox

    separated = (
        cq.Workplane("XY")
        .box(2, 4, 6)
        .add(cq.Workplane("XY").box(2, 2, 2).translate((10, 0, 0)))
    )
    assert len(separated.solids().vals()) == 2

    proof = verify_bbox(
        shape=separated,
        expected_size=(12, 4, 6),
        expected_min=(-1, -2, -3),
        expected_max=(11, 2, 3),
        label="two-body fixture",
    )
    assert proof["max"][0] == pytest.approx(11.0)


def test_verify_bbox_applies_assembly_child_locations():
    import cadquery as cq
    from cadlib.validation import verify_bbox

    assembly = cq.Assembly()
    assembly.add(
        cq.Workplane("XY").box(2, 4, 6),
        name="placed",
        loc=cq.Location((10, 5, 3)),
    )

    proof = verify_bbox(
        shape=assembly,
        expected_size=(2, 4, 6),
        expected_min=(9, 3, 0),
        expected_max=(11, 7, 6),
        label="explicit assembled envelope",
    )
    assert proof["min"] == pytest.approx((9, 3, 0))


def test_verify_bbox_rejects_post_boolean_protrusion():
    import cadquery as cq
    from cadlib.validation import verify_bbox

    body = cq.Workplane("XY").box(10, 8, 4)
    verify_bbox(shape=body, expected_size=(10, 8, 4), label="body")
    final = body.union(cq.Workplane("XY").box(4, 2, 2).translate((6, 0, 0)))

    with pytest.raises(ValueError, match=r"body bbox size\.x.*got 13.*post-boolean"):
        verify_bbox(shape=final, expected_size=(10, 8, 4), label="body")


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({}, "at least one bbox expectation"),
        ({"expected_size": (1, 2)}, "explicit .* triple"),
        ({"expected_size": (True, None, None)}, "finite number"),
        ({"expected_size": (0, None, None)}, "must be > 0"),
        ({"expected_min": (0, None, None), "expected_max": (0, None, None)}, "must be >"),
        (
            {
                "expected_size": (10, None, None),
                "expected_min": (0, None, None),
                "expected_max": (9, None, None),
            },
            "inconsistent x expectations",
        ),
        ({"expected_size": (10, None, None), "tolerance": 0}, "tolerance must be > 0"),
        ({"expected_size": (10, None, None), "label": ""}, "non-empty string"),
    ],
)
def test_verify_bbox_rejects_invalid_contract(kwargs, message):
    import cadquery as cq
    from cadlib.validation import verify_bbox

    with pytest.raises(ValueError, match=message):
        verify_bbox(shape=cq.Workplane("XY").box(10, 8, 4), **kwargs)


@pytest.mark.parametrize(
    "shape",
    [object()],
)
def test_verify_bbox_rejects_unsupported_shape(shape):
    from cadlib.validation import verify_bbox

    with pytest.raises(ValueError, match="cq.Workplane, cq.Shape, or cq.Assembly"):
        verify_bbox(shape=shape, expected_size=(1, 1, 1))


def test_verify_bbox_rejects_geometry_without_final_solids():
    import cadquery as cq
    from cadlib.validation import verify_bbox

    for shape in (cq.Workplane("XY"), cq.Workplane("XY").rect(2, 2).val()):
        with pytest.raises(ValueError, match="at least one final solid"):
            verify_bbox(shape=shape, expected_size=(1, 1, 1))


def _axis_rectangular_cut_part(
    axis,
    center,
    size,
    *,
    start=-11.0,
    end=11.0,
):
    import cadquery as cq

    axis_index, u_index, v_index = {
        "x": (0, 1, 2),
        "y": (1, 0, 2),
        "z": (2, 0, 1),
    }[axis]
    cutter_size = [0.0, 0.0, 0.0]
    cutter_center = [0.0, 0.0, 0.0]
    cutter_size[axis_index] = end - start
    cutter_size[u_index], cutter_size[v_index] = size
    cutter_center[axis_index] = (start + end) / 2
    cutter_center[u_index], cutter_center[v_index] = center
    cutter = cq.Workplane("XY").box(*cutter_size).translate(tuple(cutter_center))
    return cq.Workplane("XY").box(20, 20, 20).cut(cutter)


@pytest.mark.parametrize("axis", ["x", "y", "z"])
def test_verify_rectangular_through_cut_supports_all_cartesian_axes(axis):
    from cadlib.validation import verify_rectangular_through_cut

    proof = verify_rectangular_through_cut(
        part=_axis_rectangular_cut_part(axis, (2, 3), (4, 6)),
        axis=axis,
        center=(2, 3),
        size=(4, 6),
        span=(-10, 10),
        label=f"{axis}-axis port",
    )

    assert proof["axis"] == axis
    assert proof["center"] == [2.0, 3.0]
    assert proof["size"] == [4.0, 6.0]
    assert proof["span"] == [-10.0, 10.0]
    assert proof["blocked_volume_mm3"] == pytest.approx(0.0, abs=1e-9)
    assert set(proof["wall_missing_volume_mm3"]) == {
        face for face in ("-X", "+X", "-Y", "+Y", "-Z", "+Z")
        if face.lower().strip("+-") != axis
    }
    json.dumps(proof)


@pytest.mark.parametrize(
    ("actual_center", "actual_size", "actual_span", "message"),
    [
        ((3, 3), (4, 6), (-11, 11), "obstructed"),
        ((2, 3), (3, 6), (-11, 11), "obstructed"),
        ((2, 3), (5, 6), (-11, 11), "surrounding material"),
        ((2, 3), (4, 6), (-11, 8), "obstructed"),
    ],
)
def test_verify_rectangular_through_cut_rejects_wrong_final_void(
    actual_center, actual_size, actual_span, message
):
    from cadlib.validation import verify_rectangular_through_cut

    part = _axis_rectangular_cut_part(
        "x", actual_center, actual_size, start=actual_span[0], end=actual_span[1]
    )
    with pytest.raises(ValueError, match=message):
        verify_rectangular_through_cut(
            part=part,
            axis="x",
            center=(2, 3),
            size=(4, 6),
            span=(-10, 10),
            label="owned port",
        )


def _open_rectangular_box():
    import cadquery as cq

    outer = cq.Workplane("XY").box(30, 20, 12, centered=(True, True, False))
    cavity = cq.Workplane("XY").box(24, 14, 11).translate((0, 0, 7.5))
    return outer.cut(cavity)


def test_verify_clearance_box_proves_whole_open_cavity_volume_and_walls():
    from cadlib.validation import verify_clearance_box

    proof = verify_clearance_box(
        part=_open_rectangular_box(),
        expected_min=(-12, -7, 2),
        expected_max=(12, 7, 12),
        open_faces=("+Z",),
        label="open storage cavity",
    )

    assert proof["size"] == pytest.approx([24, 14, 10])
    assert proof["open_faces"] == ["+Z"]
    assert set(proof["wall_faces"]) == {"-X", "+X", "-Y", "+Y", "-Z"}
    assert proof["blocked_volume_mm3"] == pytest.approx(0.0, abs=1e-9)
    assert all(
        missing == pytest.approx(0.0, abs=1e-9)
        for missing in proof["wall_missing_volume_mm3"].values()
    )
    json.dumps(proof)


def test_verify_clearance_box_rejects_unsampled_internal_divider():
    import cadquery as cq
    from cadlib.validation import verify_clearance_box

    divider = cq.Workplane("XY").box(24.4, 0.4, 10).translate((0, 0, 7))
    final = _open_rectangular_box().union(divider)
    with pytest.raises(ValueError, match="obstructed"):
        verify_clearance_box(
            part=final,
            expected_min=(-12, -7, 2),
            expected_max=(12, 7, 12),
            open_faces=("+Z",),
            label="divider-free cavity",
        )


def test_verify_clearance_box_rejects_residual_roof_skin():
    import cadquery as cq
    from cadlib.validation import verify_clearance_box

    outer = cq.Workplane("XY").box(30, 20, 12, centered=(True, True, False))
    shallow = cq.Workplane("XY").box(24, 14, 9).translate((0, 0, 6.5))
    final = outer.cut(shallow)
    with pytest.raises(ValueError, match="obstructed"):
        verify_clearance_box(
            part=final,
            expected_min=(-12, -7, 2),
            expected_max=(12, 7, 12),
            open_faces=("+Z",),
            label="roof-free cavity",
        )


def test_verify_clearance_box_rejects_missing_required_wall_material():
    import cadquery as cq
    from cadlib.validation import verify_clearance_box

    side_port = cq.Workplane("XY").box(4, 4, 4).translate((14, 0, 6))
    final = _open_rectangular_box().cut(side_port)
    with pytest.raises(ValueError, match=r"surrounding material at \+X"):
        verify_clearance_box(
            part=final,
            expected_min=(-12, -7, 2),
            expected_max=(12, 7, 12),
            open_faces=("+Z",),
            label="five-wall cavity",
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"expected_min": (0, 0), "expected_max": (1, 1, 1)}, "explicit"),
        ({"expected_min": (0, 0, 0), "expected_max": (0, 1, 1)}, "4.tolerance"),
        ({"open_faces": ("+Q",)}, "must be one of"),
        ({"open_faces": ("+Z", "+Z")}, "duplicate"),
        ({"open_faces": ("+Z",), "wall_faces": ("+Z",)}, "overlap"),
        ({"open_faces": ("+Z",), "expected_max": (12, 7, 11)}, "coincide"),
        ({"wall_probe": 0.01}, "greater than 2.tolerance"),
        ({"volume_tolerance": 0}, "volume_tolerance must be > 0"),
        ({"label": ""}, "non-empty string"),
    ],
)
def test_verify_clearance_box_rejects_invalid_contract(kwargs, message):
    from cadlib.validation import verify_clearance_box

    valid = {
        "part": _open_rectangular_box(),
        "expected_min": (-12, -7, 2),
        "expected_max": (12, 7, 12),
        "open_faces": ("+Z",),
    }
    valid.update(kwargs)
    with pytest.raises(ValueError, match=message):
        verify_clearance_box(**valid)


def _axis_hole_part(axis, centers, diameter, *, start=-10.0, end=10.0):
    import cadquery as cq

    axis_index, u_index, v_index = {
        "x": (0, 1, 2),
        "y": (1, 0, 2),
        "z": (2, 0, 1),
    }[axis]
    direction = [0.0, 0.0, 0.0]
    direction[axis_index] = 1.0
    part = cq.Workplane("XY").box(20, 20, 20)
    for u, v in centers:
        origin = [0.0, 0.0, 0.0]
        origin[axis_index] = start - 1.0
        origin[u_index], origin[v_index] = u, v
        cutter = cq.Solid.makeCylinder(
            diameter / 2,
            end - start + 2.0,
            origin,
            direction,
        )
        part = part.cut(cq.Workplane(obj=cutter))
    return part


@pytest.mark.parametrize(
    ("axis", "center"),
    [("x", (2.0, 3.0)), ("y", (2.0, 3.0)), ("z", (2.0, 3.0))],
)
def test_verify_through_hole_pattern_supports_all_cartesian_axes(axis, center):
    from cadlib.validation import verify_through_hole_pattern

    proof = verify_through_hole_pattern(
        part=_axis_hole_part(axis, [center], 4.0),
        axis=axis,
        centers=[center],
        diameter=4.0,
        span=(-10.0, 10.0),
        label=f"{axis}-axis bore",
    )

    assert proof["axis"] == axis
    assert proof["centers"] == [[2.0, 3.0]]
    assert proof["count"] == 1
    assert proof["diameter"] == pytest.approx(4.0)
    assert proof["air_samples"] == 27
    assert proof["wall_samples"] == 8
    json.dumps(proof)


def test_verify_through_hole_pattern_proves_exact_count_and_positions():
    from cadlib.validation import verify_through_hole_pattern

    centers = [(-5.0, -4.0), (-5.0, 4.0), (5.0, -4.0), (5.0, 4.0)]
    proof = verify_through_hole_pattern(
        part=_axis_hole_part("z", centers, 3.4),
        axis="z",
        centers=centers,
        diameter=3.4,
        span=(-10, 10),
        label="M3 pattern",
    )

    assert proof["count"] == 4
    assert proof["centers"] == [list(center) for center in centers]


@pytest.mark.parametrize(
    ("actual_centers", "actual_diameter", "actual_end", "message"),
    [
        ([(3.0, 3.0)], 4.0, 10.0, "missing"),
        ([(2.0, 3.0)], 5.0, 10.0, "expected_diameter=4"),
        ([(2.0, 3.0)], 4.0, 5.0, "missing"),
        ([], 4.0, 10.0, "missing"),
    ],
)
def test_verify_through_hole_pattern_rejects_wrong_missing_or_blind_hole(
    actual_centers, actual_diameter, actual_end, message
):
    from cadlib.validation import verify_through_hole_pattern

    part = _axis_hole_part(
        "z", actual_centers, actual_diameter, start=-10, end=actual_end
    )
    with pytest.raises(ValueError, match=message):
        verify_through_hole_pattern(
            part=part,
            axis="z",
            centers=[(2.0, 3.0)],
            diameter=4.0,
            span=(-10, 10),
            label="target bore",
        )


def test_verify_through_hole_pattern_rejects_refilled_hole():
    import cadquery as cq
    from cadlib.validation import verify_through_hole_pattern

    through = _axis_hole_part("z", [(2.0, 3.0)], 4.0)
    refill = cq.Solid.makeCylinder(2.0, 22.0, (2, 3, -11), (0, 0, 1))
    final = through.union(cq.Workplane(obj=refill))

    with pytest.raises(ValueError, match="missing"):
        verify_through_hole_pattern(
            part=final,
            axis="z",
            centers=[(2.0, 3.0)],
            diameter=4.0,
            span=(-10, 10),
            label="refilled bore",
        )


def test_verify_through_hole_pattern_rejects_open_sided_bore():
    from cadlib.validation import verify_through_hole_pattern

    open_slot = _axis_hole_part("z", [(9.0, 0.0)], 4.0)
    with pytest.raises(ValueError, match="open-sided.*surrounding material"):
        verify_through_hole_pattern(
            part=open_slot,
            axis="z",
            centers=[(9.0, 0.0)],
            diameter=4.0,
            span=(-10, 10),
            label="edge bore",
        )


def test_verify_through_hole_pattern_does_not_count_external_cylinder():
    import cadquery as cq
    from cadlib.validation import verify_through_hole_pattern

    through = _axis_hole_part("z", [(-5.0, 0.0)], 4.0)
    same_radius_boss = cq.Solid.makeCylinder(2.0, 4.0, (5, 0, 10), (0, 0, 1))
    final = through.union(cq.Workplane(obj=same_radius_boss))

    proof = verify_through_hole_pattern(
        part=final,
        axis="z",
        centers=[(-5.0, 0.0)],
        diameter=4.0,
        span=(-10, 10),
        label="one bore plus one boss",
    )
    assert proof["count"] == 1


def test_verify_through_hole_pattern_rejects_stale_extra_hole_unless_out_of_scope():
    from cadlib.validation import verify_through_hole_pattern

    part = _axis_hole_part("z", [(-6.0, 0.0), (6.0, 0.0)], 4.0)
    with pytest.raises(ValueError, match=r"unexpected=\[\(6\.0, 0\.0\)\]"):
        verify_through_hole_pattern(
            part=part,
            axis="z",
            centers=[(-6.0, 0.0)],
            diameter=4.0,
            span=(-10, 10),
            label="left pattern",
        )

    proof = verify_through_hole_pattern(
        part=part,
        axis="z",
        centers=[(-6.0, 0.0)],
        diameter=4.0,
        span=(-10, 10),
        scope=(-9.0, -3.0, -3.0, 3.0),
        label="left pattern",
    )
    assert proof["scope"] == [-9.0, -3.0, -3.0, 3.0]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"axis": "q"}, "axis must be"),
        ({"centers": []}, "at least one"),
        ({"centers": [(0,)]}, "explicit .* pair"),
        ({"centers": [(0, 0), (0, 0)]}, "duplicate"),
        ({"diameter": 0}, "diameter must be > 0"),
        ({"span": (0,)}, "explicit world-space"),
        ({"span": (1, 0)}, "end must be greater"),
        ({"tolerance": 0}, "tolerance must be > 0"),
        ({"sample_margin": 0.01}, "greater than 2.tolerance"),
        ({"sample_margin": 1.0}, "one quarter"),
        ({"label": ""}, "non-empty string"),
        ({"scope": (0, 0, 0, 1)}, "max values"),
        ({"scope": (4, 4, 8, 8)}, "center must lie inside scope"),
    ],
)
def test_verify_through_hole_pattern_rejects_invalid_contract(kwargs, message):
    from cadlib.validation import verify_through_hole_pattern

    valid = {
        "part": _axis_hole_part("z", [(2.0, 3.0)], 4.0),
        "axis": "z",
        "centers": [(2.0, 3.0)],
        "diameter": 4.0,
        "span": (-10.0, 10.0),
    }
    valid.update(kwargs)
    with pytest.raises(ValueError, match=message):
        verify_through_hole_pattern(**valid)


def test_verify_through_hole_pattern_requires_one_final_solid():
    import cadquery as cq
    from cadlib.validation import verify_through_hole_pattern

    two_solids = (
        cq.Workplane("XY")
        .box(10, 10, 4)
        .add(cq.Workplane("XY").box(10, 10, 4).translate((20, 0, 0)))
    )
    with pytest.raises(ValueError, match="exactly one final solid"):
        verify_through_hole_pattern(
            part=two_solids,
            axis="z",
            centers=[(0, 0)],
            diameter=4,
            span=(-2, 2),
        )


@pytest.mark.parametrize(
    ("side", "center"),
    [
        ("+X", (30.0, 0.0, 0.0)),
        ("-X", (-30.0, 0.0, 0.0)),
        ("+Y", (0.0, 20.0, 0.0)),
        ("-Y", (0.0, -20.0, 0.0)),
    ],
)
def test_rounded_side_wall_cutout_is_through_and_keeps_adjacent_wall(side, center):
    from cadlib.cutouts import (
        add_rounded_side_wall_cutout,
        verify_side_wall_through_cut,
    )
    from cadlib.enclosure import hollow_box

    body = hollow_box(length=60, width=40, height=20, wall=2, corner_radius=3)
    result = add_rounded_side_wall_cutout(
        body,
        side=side,
        center=center,
        width=12,
        height=6,
        wall_thickness=2,
        corner_radius=1,
    )
    assert result.val().isValid()
    assert len(result.solids().vals()) == 1
    assert verify_side_wall_through_cut(
        result,
        side=side,
        center=center,
        width=12,
        height=6,
        wall_thickness=2,
    ) == {
        "side": side,
        "aperture_air_samples": 15,
        "adjacent_wall_samples": 12,
        "wall_thickness": 2.0,
    }


def test_side_wall_proof_rejects_one_sided_residual_skin():
    import cadquery as cq
    from cadlib.cutouts import verify_side_wall_through_cut
    from cadlib.enclosure import hollow_box

    body = hollow_box(length=60, width=40, height=20, wall=2, corner_radius=3)
    old_cutter = (
        cq.Workplane("YZ")
        .rect(12, 6)
        .extrude(4)
        .edges("|X")
        .fillet(1)
        .translate((28.5, 0, 0))
    )
    residual_skin = body.cut(old_cutter)
    with pytest.raises(ValueError, match="not through.*material remains"):
        verify_side_wall_through_cut(
            residual_skin,
            side="+X",
            center=(30, 0, 0),
            width=12,
            height=6,
            wall_thickness=2,
        )


def test_side_wall_proof_rejects_a_later_refill():
    import cadquery as cq
    from cadlib.cutouts import (
        add_rounded_side_wall_cutout,
        verify_side_wall_through_cut,
    )
    from cadlib.enclosure import hollow_box

    body = hollow_box(length=60, width=40, height=20, wall=2, corner_radius=3)
    opened = add_rounded_side_wall_cutout(
        body,
        side="+X",
        center=(30, 0, 0),
        width=12,
        height=6,
        wall_thickness=2,
        corner_radius=1,
    )
    # This touches the remaining +Y wall, so it is one fused solid rather than
    # a disconnected object rejected before the aperture samples run.
    filled = opened.union(cq.Workplane("XY").box(2, 9, 2).translate((29, 2.5, 0)))
    with pytest.raises(ValueError, match="not through.*material remains"):
        verify_side_wall_through_cut(
            filled,
            side="+X",
            center=(30, 0, 0),
            width=12,
            height=6,
            wall_thickness=2,
        )


def test_side_wall_proof_rejects_an_ambiguous_multi_solid_part():
    import cadquery as cq
    from cadlib.cutouts import (
        add_rounded_side_wall_cutout,
        verify_side_wall_through_cut,
    )
    from cadlib.enclosure import hollow_box

    body = hollow_box(length=60, width=40, height=20, wall=2, corner_radius=3)
    opened = add_rounded_side_wall_cutout(
        body,
        side="+X",
        center=(30, 0, 0),
        width=12,
        height=6,
        wall_thickness=2,
    )
    ambiguous = opened.add(cq.Workplane("XY").box(2, 2, 2).translate((100, 0, 0)))
    assert len(ambiguous.solids().vals()) == 2
    with pytest.raises(ValueError, match="exactly one solid"):
        verify_side_wall_through_cut(
            ambiguous,
            side="+X",
            center=(30, 0, 0),
            width=12,
            height=6,
            wall_thickness=2,
        )


@pytest.mark.parametrize(
    ("actual_width", "actual_height", "error"),
    [
        (10.0, 6.0, "does not cover"),
        (12.0, 4.0, "does not cover"),
        (14.0, 6.0, "lacks surrounding"),
        (12.0, 8.0, "lacks surrounding"),
    ],
)
def test_side_wall_proof_rejects_wrong_size(actual_width, actual_height, error):
    from cadlib.cutouts import (
        add_rounded_side_wall_cutout,
        verify_side_wall_through_cut,
    )
    from cadlib.enclosure import hollow_box

    body = hollow_box(length=60, width=40, height=20, wall=2, corner_radius=3)
    wrong = add_rounded_side_wall_cutout(
        body,
        side="+X",
        center=(30, 0, 0),
        width=actual_width,
        height=actual_height,
        wall_thickness=2,
        corner_radius=1,
    )
    with pytest.raises(ValueError, match=error):
        verify_side_wall_through_cut(
            wrong,
            side="+X",
            center=(30, 0, 0),
            width=12,
            height=6,
            wall_thickness=2,
        )


@pytest.mark.parametrize("actual_center", [(30, 0.75, 0), (30, 0, 0.75)])
def test_side_wall_proof_rejects_shifted_aperture(actual_center):
    from cadlib.cutouts import (
        add_rounded_side_wall_cutout,
        verify_side_wall_through_cut,
    )
    from cadlib.enclosure import hollow_box

    body = hollow_box(length=60, width=40, height=20, wall=2, corner_radius=3)
    shifted = add_rounded_side_wall_cutout(
        body,
        side="+X",
        center=actual_center,
        width=12,
        height=6,
        wall_thickness=2,
        corner_radius=1,
    )
    with pytest.raises(ValueError, match="does not cover"):
        verify_side_wall_through_cut(
            shifted,
            side="+X",
            center=(30, 0, 0),
            width=12,
            height=6,
            wall_thickness=2,
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"side": "X"}, "side must be"),
        ({"center": (29, 0, 0)}, "exterior face"),
        ({"width": 0}, "must be > 0"),
        ({"corner_radius": 3}, "corner_radius"),
        ({"overshoot": 0}, "overshoot"),
        ({"center": (30, 14, 0)}, "width plus adjacent-wall probes"),
    ],
)
def test_rounded_side_wall_cutout_rejects_invalid_arguments(kwargs, message):
    from cadlib.cutouts import add_rounded_side_wall_cutout
    from cadlib.enclosure import hollow_box

    body = hollow_box(length=60, width=40, height=20, wall=2, corner_radius=3)
    valid = {
        "side": "+X",
        "center": (30, 0, 0),
        "width": 12,
        "height": 6,
        "wall_thickness": 2,
        "corner_radius": 1,
    }
    valid.update(kwargs)
    with pytest.raises(ValueError, match=message):
        add_rounded_side_wall_cutout(body, **valid)


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
