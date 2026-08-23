"""stool_<species>_p<owner> -- 16 names, ALL sharing one canonical body.

Above the shoulder (cap, boss, neck, shoulder) is built by ONE function,
`_canonical_upper`, called identically for every one of the 16 variants --
that is what makes the "identical above the collar" constraint hold by
construction rather than by sixteen separately-typed copies of the same
numbers. Only two things ever vary: `owner_bites` (cut into the cap edge,
visible) and `grooves` (cut into the shank, buried).
"""
import math

import cadquery as cq

import params as p


def _canonical_upper():
    """cap + boss + neck + shoulder, IDENTICAL for every one of the 16
    stool_* parts. Built with z=0 at the shoulder's bottom face (== the
    shank's top face), so callers just stack this on top of their own
    (species-specific) shank.
    """
    shoulder = cq.Workplane("XY").circle(p.STOOL_SHOULDER_D / 2.0).extrude(
        p.STOOL_SHOULDER_H
    )
    neck = (
        cq.Workplane("XY").circle(p.STOOL_NECK_D / 2.0).extrude(p.STOOL_NECK_H)
        .translate((0, 0, p.STOOL_SHOULDER_H))
    )
    cap_z0 = p.STOOL_SHOULDER_H + p.STOOL_NECK_H
    cap = cq.Workplane("XY").circle(p.STOOL_CAP_D / 2.0).extrude(p.STOOL_CAP_T).translate(
        (0, 0, cap_z0)
    )

    # growth rings, top face (concentric shallow grooves)
    for r in p.STOOL_RING_RADII:
        ring = (
            cq.Workplane("XY").circle(r + p.STOOL_RING_WIDTH / 2.0)
            .circle(r - p.STOOL_RING_WIDTH / 2.0)
            .extrude(p.STOOL_RING_RELIEF)
            .translate((0, 0, cap_z0 + p.STOOL_CAP_T - p.STOOL_RING_RELIEF))
        )
        cap = cap.cut(ring)

    # gill ribs, underside of the brim -- polar array of thin raised ribs
    gill = cq.Workplane("XY").box(
        p.STOOL_GILL_OUTER_R - p.STOOL_GILL_INNER_R,
        p.STOOL_GILL_WIDTH,
        p.STOOL_GILL_RELIEF,
        centered=(False, True, False),
    ).translate((p.STOOL_GILL_INNER_R, 0, cap_z0 - p.STOOL_GILL_RELIEF))
    for i in range(p.STOOL_GILL_COUNT):
        ang = 360.0 * i / p.STOOL_GILL_COUNT
        rib = gill.rotate((0, 0, 0), (0, 0, 1), ang)
        cap = cap.union(rib)

    boss = (
        cq.Workplane("XY").circle(p.STOOL_BOSS_D / 2.0).extrude(p.STOOL_BOSS_H)
        .translate((0, 0, cap_z0 + p.STOOL_CAP_T))
    )

    return shoulder.union(neck).union(cap).union(boss)


def _owner_bites(body, count):
    """N square notches (BITE_W x BITE_D) cut into the cap's outer edge,
    evenly spaced and clearly countable -- the only visible identity mark
    that differs by owner.
    """
    cap_z0 = p.STOOL_SHOULDER_H + p.STOOL_NECK_H
    r = p.STOOL_CAP_D / 2.0
    notch = cq.Workplane("XY").box(
        p.BITE_D * 2, p.BITE_W, p.STOOL_CAP_T + 0.4, centered=(False, True, False)
    ).translate((r - p.BITE_D, 0, cap_z0 - 0.2))
    for i in range(count):
        ang = p.BITE_START_DEG + i * p.BITE_SPACING_DEG
        cut = notch.rotate((0, 0, 0), (0, 0, 1), ang)
        body = body.cut(cut)
    return body


def _groove_cutter(center_z, width, depth, chamfer):
    """One chamfered annular groove cut into the 12mm shank: a straight
    undercut band flanked by a small conical lead-in on each side so a
    pin's tip is guided in rather than catching, per idea.json.
    """
    r_full = p.STOOL_SHANK_D / 2.0
    r_deep = r_full - depth
    z0 = center_z - width / 2.0
    z1 = center_z + width / 2.0
    profile = cq.Workplane("XZ").polyline([
        (r_full + 0.2, z0 - chamfer),
        (r_deep, z0),
        (r_deep, z1),
        (r_full + 0.2, z1 + chamfer),
    ])
    solid = profile.close().revolve(360, (0, 0), (0, 1))
    return solid


def _shank(species):
    """12mm-dia x 22mm shank, z=0 (tip) to z=STOOL_SHANK_H (shoulder line).
    Species-specific grooves cut where SPECIES_GROOVES says they are.
    """
    shank = cq.Workplane("XY").circle(p.STOOL_SHANK_D / 2.0).extrude(p.STOOL_SHANK_H)
    bands = p.SPECIES_GROOVES[species]
    top = p.STOOL_SHANK_H
    if "upper" in bands:
        z = top - p.GROOVE_UPPER_CENTER_BELOW
        shank = shank.cut(_groove_cutter(z, p.GROOVE_WIDTH, p.GROOVE_DEPTH, p.GROOVE_CHAMFER))
    if "lower" in bands:
        z = top - p.GROOVE_LOWER_CENTER_BELOW
        shank = shank.cut(_groove_cutter(z, p.GROOVE_WIDTH, p.GROOVE_DEPTH, p.GROOVE_CHAMFER))
    return shank


def build_stool(species, owner_bites):
    """Full 34x34x49mm stool: shank (species-specific, buried/hidden) +
    shoulder/neck/cap/boss (canonical, identical across all 16 names) +
    owner bites (visible, cap edge only).
    """
    shank = _shank(species)
    upper = _canonical_upper().translate((0, 0, p.STOOL_SHANK_H))
    body = shank.union(upper)
    body = _owner_bites(body, owner_bites)
    return body
