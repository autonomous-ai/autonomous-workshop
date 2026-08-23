"""stool_<species>_p<owner> -- 8 Duel names, ALL sharing one canonical body.

Above the shoulder (cap, boss, neck, shoulder) is built by ONE function,
`_canonical_upper`, called identically for every one of the 8 variants --
that is what makes the "identical above the collar" constraint hold by
construction rather than by separately-typed copies of the same
numbers. Only two things ever vary: `owner_bites` (cut into the cap edge,
visible) and keyed A/B probe tunnels (cut into the shank, buried).
"""
import math

import cadquery as cq

import params as p


def _canonical_upper():
    """cap + boss + neck + shoulder, IDENTICAL for every Duel stool
    stool_* parts. Built with z=0 at the shoulder's bottom face (== the
    shank's top face), so callers just stack this on top of their own
    (species-specific) shank.
    """
    shoulder = (
        cq.Workplane("XY")
        .circle(p.STOOL_SHANK_D / 2.0)
        .workplane(offset=p.STOOL_SHOULDER_H)
        .circle(p.STOOL_SHOULDER_D / 2.0)
        .loft(ruled=True)
    )
    shoulder_trim = (
        cq.Workplane("XY")
        .box(p.STOOL_SHOULDER_D * 2, p.STOOL_SHOULDER_D * 2,
             p.STOOL_SHOULDER_H + 1.0, centered=(True, False, False))
        .translate((0, p.STOOL_KEY_FLAT_Y - p.STOOL_SHOULDER_D * 2, -0.5))
    )
    shoulder = shoulder.cut(shoulder_trim)
    neck = (
        cq.Workplane("XY").circle(p.STOOL_NECK_D / 2.0).extrude(p.STOOL_NECK_H)
        .translate((0, 0, p.STOOL_SHOULDER_H))
    )
    cap_z0 = p.STOOL_SHOULDER_H + p.STOOL_NECK_H
    cap = cq.Workplane("XY").circle(p.STOOL_CAP_D / 2.0).extrude(p.STOOL_CAP_T).translate(
        (0, 0, cap_z0)
    )
    # A shallow mushroom frustum supports the full cap perimeter at <43deg
    # in the canonical upright print. This eliminates slicer-reported floating
    # cantilevers without generated supports and preserves the neck shadow.
    support = (
        cq.Workplane("XY")
        .workplane(offset=cap_z0 - p.STOOL_CAP_SUPPORT_H)
        .circle(p.STOOL_NECK_D / 2.0)
        .workplane(offset=p.STOOL_CAP_SUPPORT_H)
        .circle(p.STOOL_CAP_D / 2.0)
        .loft(ruled=True)
    )

    # Growth rings, top face (concentric shallow grooves). Each annular cutter
    # has two opposed 1.6mm bridges. A fully closed groove left the decorative
    # centre island as a second disconnected STL shell even though it touched
    # the cap below; the bridges make the printable body connected by
    # construction while retaining the growth-ring read.
    for r in p.STOOL_RING_RADII:
        ring = (
            cq.Workplane("XY").circle(r + p.STOOL_RING_WIDTH / 2.0)
            .circle(r - p.STOOL_RING_WIDTH / 2.0)
            .extrude(p.STOOL_RING_RELIEF)
            .translate((0, 0, cap_z0 + p.STOOL_CAP_T - p.STOOL_RING_RELIEF))
        )
        bridges = (
            cq.Workplane("XY")
            .box(p.STOOL_CAP_D * 1.2, 1.6, p.STOOL_RING_RELIEF + 0.4,
                 centered=(True, True, False))
            .translate((0, 0, cap_z0 + p.STOOL_CAP_T - p.STOOL_RING_RELIEF - 0.2))
        )
        ring = ring.cut(bridges)
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

    return shoulder.union(neck).union(support).union(cap).union(boss)


def _owner_bites(body, count):
    """N square notches (BITE_W x BITE_D) cut into the cap's outer edge,
    evenly spaced and clearly countable -- the only visible identity mark
    that differs by owner.
    """
    cap_z0 = p.STOOL_SHANK_H + p.STOOL_SHOULDER_H + p.STOOL_NECK_H
    r = p.STOOL_CAP_D / 2.0
    notch = cq.Workplane("XY").box(
        p.BITE_D * 2, p.BITE_W, p.STOOL_CAP_T + 0.4, centered=(False, True, False)
    ).translate((r - p.BITE_D, 0, cap_z0 - 0.2))
    for i in range(count):
        ang = p.BITE_START_DEG + i * p.BITE_SPACING_DEG
        cut = notch.rotate((0, 0, 0), (0, 0, 1), ang)
        body = body.cut(cut)
    return body


def _d_profile_solid(diameter, flat_y, height):
    """Round body with a rear (-Y) registration flat, extruded from z=0."""
    body = cq.Workplane("XY").circle(diameter / 2.0).extrude(height)
    trim = (
        cq.Workplane("XY")
        .box(diameter * 2, diameter * 2, height + 0.4, centered=(True, False, False))
        .translate((0, flat_y - diameter * 2, -0.2))
    )
    return body.cut(trim)


def _tunnel_cutter(bit):
    """Channel collinear with the matching tile entry for a seated stool."""
    index = p.PROBE_BITS.index(bit)
    ex, ey = p.PROBE_MOUTHS_XY[index]
    hx, hy = p.PROBE_INWARD_XY[index]
    angle = math.radians(p.PROBE_ANGLE_DEG)
    local_entry_z = p.TILE_T - p.SEATED_STOOL_Z
    direction = cq.Vector(
        math.sin(angle) * hx,
        math.sin(angle) * hy,
        -math.cos(angle),
    )
    solid = cq.Solid.makeCylinder(
        p.PROBE_HOLE_D / 2.0,
        p.PROBE_CHANNEL_LEN,
        pnt=cq.Vector(ex, ey, local_entry_z),
        dir=direction,
    )
    return cq.Workplane("XY").newObject([solid])


def _shank(species):
    """Keyed 21.4mm shank with zero, A, B, or both parallel tunnels."""
    shank = _d_profile_solid(p.STOOL_SHANK_D, p.STOOL_KEY_FLAT_Y, p.STOOL_SHANK_H)
    bits = p.SPECIES_TUNNELS[species]
    for bit in p.PROBE_BITS:
        if bit in bits:
            shank = shank.cut(_tunnel_cutter(bit))
    return shank.clean()


def build_stool(species, owner_bites):
    """Full 34x34x49mm stool: shank (species-specific, buried/hidden) +
    shoulder/neck/cap/boss (canonical, identical across all 8 names) +
    owner bites (visible, cap edge only).
    """
    shank = _shank(species)
    upper = _canonical_upper().translate((0, 0, p.STOOL_SHANK_H))
    body = shank.union(upper).clean()
    body = _owner_bites(body, owner_bites)
    return body.clean()
