"""Golden blocks — frozen, verified CadQuery subparts (composition over invention).

Human-authored (SkillsBench 2026: human-authored skills +16.2pt vs ~0 for
LLM-authored). Every block must pass blocks/testbench.py before use; changes
re-run the testbench. Contracts in BLOCKS.md.

All dimensions in mm. Every function returns a cq.Workplane solid.
"""
import math

import cadquery as cq

MIN_WALL = 1.6  # FDM floor enforced across all blocks


def rounded_box(w, d, h, corner_r=3.0, top_fillet=0.0, bottom_chamfer=0.6):
    """Box with corner rounds BAKED INTO THE 2D PROFILE, then extruded.

    This is the graduated Huggy lesson: a blanket .edges().fillet() makes OCCT
    build spherical vertex-blends that tessellate into phantom sliver bodies.
    Profile arcs + optional top-only fillet / bottom-only chamfer never build a
    vertex blend, so the result stays one watertight solid.
    """
    assert corner_r < min(w, d) / 2, "corner_r must be < half the smaller side"
    s = (cq.Workplane("XY").sketch()
         .rect(w, d).vertices().fillet(corner_r).finalize()
         .extrude(h))
    if top_fillet > 0:
        s = s.edges(">Z").fillet(top_fillet)
    if bottom_chamfer > 0:
        s = s.edges("<Z").chamfer(bottom_chamfer)
    return s


def hollow_box(w, d, h, wall=2.0, corner_r=3.0):
    """Rounded-profile OPEN-TOP container (tray/pot/holder). Always open:
    a sealed internal void is an FDM antipattern (trapped air, 2-surface mesh)
    — testbench-caught 2026-08-11. Need a lid? Model it as a second part."""
    assert wall >= MIN_WALL, f"wall must be >= {MIN_WALL}mm"
    s = rounded_box(w, d, h, corner_r, top_fillet=0.0, bottom_chamfer=0.0)
    return s.faces(">Z").shell(-wall)


def angled_stand(w=70, depth=80, height=75, base_t=4.0, nose_t=8.0, base_ext=0.0):
    """Solid right-wedge stand body (leaning face = hypotenuse) on a flat base.
    nose_t keeps a blunt top edge (printable, no knife edge). base_ext extends
    the base FORWARD past the slope foot — union a lip bar on it to form a
    device channel (the verified phone-stand recipe in BLOCKS.md)."""
    assert base_t >= 2.0 and nose_t >= 2.0
    pts = [(0, 0), (depth + base_ext, 0), (depth + base_ext, base_t)]
    if base_ext > 0:
        pts.append((depth, base_t))  # zero-length edge if appended when ext == 0
    pts += [(nose_t, height), (0, height)]
    return (cq.Workplane("XZ").polyline(pts).close()
            .extrude(w).translate((0, w / 2, 0)))


def phone_slot_cutter(w=85, phone_t=13.5, depth=14, angle_deg=27, clearance=1.5):
    """NEGATIVE volume: subtract from a body to make an angled phone groove.
    angle_deg tilts the slot back from vertical (0 = upright). Position with
    .translate() so the cutter's floor sits where the groove floor belongs."""
    t = phone_t + clearance
    cutter = (cq.Workplane("XY").rect(w, t).extrude(depth + t)
              .rotate((0, 0, 0), (1, 0, 0), -angle_deg))
    return cutter


def snap_hook(w=12.0, t=3.0, arm_l=25.0, hook_depth=6.0, hook_t=3.0):
    """Cantilever J-hook (wall hook / clip finger), flat profile extruded to w.
    Root at origin extending +X, hook lip turning up +Z at the far end."""
    assert t >= 2.0 and hook_t >= 2.0
    pts = [(0, 0), (arm_l, 0), (arm_l, hook_depth + hook_t),
           (arm_l - hook_t, hook_depth + hook_t), (arm_l - hook_t, hook_t),
           (0, t)]
    return (cq.Workplane("XZ").polyline(pts).close()
            .extrude(w).translate((0, w / 2, 0)))


BLOCKS = {
    "rounded_box": rounded_box,
    "hollow_box": hollow_box,
    "angled_stand": angled_stand,
    "phone_slot_cutter": phone_slot_cutter,
    "snap_hook": snap_hook,
}


# ---------------------------------------------------------------------------
# PROPOSED — NOT yet approved. Testbench-verified but not human-curated per
# BLOCKS.md policy (needs Tam's review before moving into BLOCKS above).
# Candidates surfaced 2026-08-16: each was independently hand-rolled in >=2
# separate build directories this week (evidence in the weekly self-improve
# commit), which is the "reimplemented, not merely used" signal BLOCKS.md
# asks for before proposing composition-over-invention library additions.
# ---------------------------------------------------------------------------

def bounds_box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box spanning explicit bounds rather than center+size —
    the shape every build this week hand-rolled under a different name
    (`box`, `lbox`, `wbox`, `xbox`, `box_range`) for fit-check mocks
    (trimesh) and range-defined cutters/pads (CadQuery) alike: draft-stack-dock,
    arc-coil-blaster-prop, finger-mirror-manipulator and terminal-cursor-pen-holder
    each wrote their own copy. Returns a solid; use `.cut()` to subtract it as
    a cutter, same as any other block here."""
    assert x1 > x0 and y1 > y0 and z1 > z0, "bounds must be non-degenerate (x1>x0, y1>y0, z1>z0)"
    return (cq.Workplane("XY")
            .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def dovetail_tenon(throat=6.0, depth=6.0, length=20.0, angle_deg=30.0):
    """Male dovetail tenon: trapezoidal cross-section (narrow at the root,
    wide at the tip so it locks against pull-out), extruded along Y for
    `length` (the joint's slide/insertion axis). `throat` = root width,
    `depth` = radial extent from root to tip, `angle_deg` = taper half-angle
    from the slide axis (30 => 60deg included, matching the two independent
    hand-rolled joints this pattern was found in — aggressive enough to
    retain, shallow enough to print without support along the taper).
    Cross-section lives in XZ, centered on the slide axis (Y) and on X."""
    assert throat >= 2 * MIN_WALL, f"throat must be >= {2 * MIN_WALL}mm"
    assert 5.0 <= angle_deg <= 45.0, "angle_deg outside a printable dovetail range"
    tip = throat + 2 * depth * math.tan(math.radians(angle_deg))
    pts = [(-throat / 2, 0), (throat / 2, 0), (tip / 2, depth), (-tip / 2, depth)]
    return (cq.Workplane("XZ").polyline(pts).close()
            .extrude(length).translate((0, length / 2, 0)))


def dovetail_socket_cutter(throat=6.0, depth=6.0, length=20.0, angle_deg=30.0,
                           clearance=0.15):
    """NEGATIVE volume: subtract from the mating part to cut a socket for
    `dovetail_tenon` with the same params. `clearance` grows the throat and
    depth uniformly (default 0.15mm/side, FDM-safe) for a printable sliding
    fit — same clearance-by-growth approach as `phone_slot_cutter`, not a
    true face-normal offset.

    The mouth (z=0 in this cutter's local frame) must land ON a real face of
    the host part — cutting it into the host's interior seals a void (FDM
    antipattern, same as `hollow_box`'s warning). For the tenon to actually
    slide together with the host afterward, the host must also leave at
    least one end of the slide axis (Y) open past `length` — a host that
    fully encloses the pocket on all sides is dimensionally correct (mates
    with zero clash) but not physically assemblable as two rigid parts."""
    return dovetail_tenon(throat + 2 * clearance, depth + clearance, length, angle_deg)


PROPOSED_BLOCKS = {
    "bounds_box": bounds_box,
    "dovetail_tenon": dovetail_tenon,
    "dovetail_socket_cutter": dovetail_socket_cutter,
}
