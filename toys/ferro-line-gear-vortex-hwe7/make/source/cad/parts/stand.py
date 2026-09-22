"""Pedestal and stand. All exports are separate bed-zero print solids.
Construction dimensions and fit allowances are centralized in params.py.
The base is printed roof-down; its bayonet-lid cavity therefore has no roof bridge.
"""
from math import tan, radians
from build123d import Align, Axis, Box, Color, Cone, Cylinder, Plane, Polygon, Pos, Rot, extrude, revolve
import params as p

A = (Align.CENTER, Align.CENTER, Align.MIN)


def _cylinder(radius, height, z=0):
    return Pos(0, 0, z) * Cylinder(radius, height, align=A)


def _ring(outer, inner, height, z=0):
    return _cylinder(outer, height, z) - _cylinder(inner, height + 2*p.CUT_OVERSHOOT, z-p.CUT_OVERSHOOT)


def _d_profile(radius, flat, height, z=0):
    return _cylinder(radius, height, z) & Pos(-radius, 0, z) * Box(radius+flat, 2*radius, height, align=(Align.MIN, Align.CENTER, Align.MIN))


def _radial_sector(radius, angle, height, z):
    half = radians(angle/2)
    profile = Polygon((0, 0), (radius, -radius*tan(half)), (radius, radius*tan(half)), align=None)
    return Pos(0, 0, z) * extrude(profile, amount=height)


def _section_ring(points):
    return revolve(Plane.XZ * Polygon(*points, align=None), axis=Axis.Z)


def _bayonet_dimensions():
    cavity = p.BASE_DIAMETER/2-p.BASE_WALL
    lid_radius = cavity-p.BAYONET_CLEARANCE
    root = lid_radius-p.BAYONET_ROOT_OVERLAP
    tip = cavity+p.BAYONET_RADIAL_DEPTH-p.BAYONET_CLEARANCE
    half_tip = p.BAYONET_TAB_TIP_HEIGHT/2
    half_root = half_tip+p.BAYONET_TAB_RISE
    slope = p.BAYONET_TAB_RISE/(tip-root)
    assert slope > 1, "Bayonet flanks require more than45 degrees from bed"
    return cavity, lid_radius, root, tip, half_tip, half_root, slope


def _bayonet_tab_ring():
    _, _, root, tip, ht, hr, _ = _bayonet_dimensions()
    z = p.BAYONET_CENTER_Z
    return _section_ring([(root,z-hr),(tip,z-ht),(tip,z+ht),(root,z+hr)])


def _bayonet_groove():
    _, _, root, tip, ht, _, slope = _bayonet_dimensions()
    outer = tip+p.BAYONET_CLEARANCE
    lower_tip = p.BAYONET_CENTER_Z-ht-p.BAYONET_CLEARANCE
    upper_tip = p.BAYONET_CENTER_Z+ht+p.BAYONET_CLEARANCE
    lower_root = lower_tip-slope*(outer-root)
    upper_root = upper_tip+slope*(outer-root)
    return _section_ring([(root,lower_root),(outer,lower_tip),(outer,upper_tip),(root,upper_root)]), upper_root


def _socket_transition():
    # Begins below the circular stem flare so its D-flat also expands at45deg.
    inner = p.STEM_TENON_DIAMETER/2+p.STEM_SOCKET_CLEARANCE
    outer = p.STEM_DIAMETER/2+p.STEM_SOCKET_CLEARANCE
    flat = p.STEM_KEY_FLAT+p.STEM_SOCKET_CLEARANCE
    start = p.STEM_BOTTOM-(inner-flat)
    rise = outer-flat
    end = start+rise
    cone = Pos(0,0,start)*Cone(inner,outer,rise,align=A)
    # Clip cone with a sloping D-flat. Its45deg slope avoids a hidden ledge.
    face = Plane.XZ*Polygon((-2*outer,start),(flat,start),(outer,end),(-2*outer,end),align=None)
    clip = extrude(face,amount=2*outer,both=True)
    return cone & clip, end


def _rim_groove():
    center = p.RIM_TRIM_DIAMETER/2-p.RIM_TRIM_WIDTH/2
    top_half = p.RIM_TRIM_WIDTH/2+p.RIM_GROOVE_TOP_CLEARANCE
    neck_half = p.RIM_GROOVE_NECK_WIDTH/2
    top = p.BASE_HEIGHT
    neck = top-p.RIM_GROOVE_NECK_DEPTH
    apex = neck-neck_half*p.RIM_GROOVE_SLOPE
    assert apex >= p.BASE_HEIGHT-p.BASE_ROOF+1.0
    # A pointed cavity roof closes on steep faces; there is no flat bridge.
    return _section_ring([(center-top_half,top+p.CUT_OVERSHOOT),
                          (center+top_half,top+p.CUT_OVERSHOOT),
                          (center+top_half,top),
                          (center+neck_half,neck),
                          (center,apex),
                          (center-neck_half,neck),
                          (center-top_half,top)])


def make_pedestal():
    """Print roof-down. Assembly mapping Pos(0,0,BASE_HEIGHT)*Rot(180,0,0)."""
    outer = p.BASE_DIAMETER/2
    cavity = outer-p.BASE_WALL
    base = _cylinder(outer, p.BASE_HEIGHT)
    base -= _cylinder(cavity, p.BASE_HEIGHT-p.BASE_ROOF+p.CUT_OVERSHOOT, -p.CUT_OVERSHOOT)
    # Central socket boss transfers stem load into roof; stays clear of ballast.
    boss_radius = p.STEM_DIAMETER/2+p.BASE_WALL
    boss_bottom = p.STEM_BOTTOM-p.STEM_TENON_LENGTH
    base += _cylinder(boss_radius, p.BASE_HEIGHT-boss_bottom, boss_bottom)
    base -= _d_profile(p.STEM_TENON_DIAMETER/2+p.STEM_SOCKET_CLEARANCE, p.STEM_KEY_FLAT+p.STEM_SOCKET_CLEARANCE, p.BASE_HEIGHT-boss_bottom+p.CUT_OVERSHOOT, boss_bottom)
    transition, transition_top = _socket_transition()
    base -= transition
    base -= _cylinder(p.STEM_DIAMETER/2+p.STEM_SOCKET_CLEARANCE,
                      p.BASE_HEIGHT-transition_top+p.CUT_OVERSHOOT, transition_top)
    groove, slot_top = _bayonet_groove()
    base -= groove
    # Restrict entry slots to the outer annular wall: never cut the socket boss.
    slot_outer = cavity+p.BAYONET_RADIAL_DEPTH+p.BAYONET_CLEARANCE
    slot_band = _ring(slot_outer,cavity-2*p.BAYONET_CLEARANCE,
                      slot_top+2*p.CUT_OVERSHOOT,-p.CUT_OVERSHOOT)
    slots = [slot_band & (Rot(0,0,i*360/p.BAYONET_COUNT)*
             _radial_sector(slot_outer,p.BAYONET_SLOT_ANGLE,
                            slot_top+2*p.CUT_OVERSHOOT,-p.CUT_OVERSHOOT))
             for i in range(p.BAYONET_COUNT)]
    base -= slots
    base -= _rim_groove()
    result = Pos(0, 0, p.BASE_HEIGHT)*Rot(180, 0, 0)*base
    result.label = 'pedestal_roof_down'
    result.color = Color(*p.BLACK)
    return result


def make_pedestal_lid():
    """Flat bed datumZ0; rotate30deg aroundZ into captured assembly position."""
    cavity = p.BASE_DIAMETER/2-p.BASE_WALL
    radius = cavity-p.BASE_LID_CLEARANCE
    lid = _cylinder(radius, p.BASE_LID_THICKNESS)
    _,_,_,_,_,half_root,_ = _bayonet_dimensions()
    collar_height = p.BAYONET_CENTER_Z+half_root-p.BASE_LID_THICKNESS
    lid += _ring(radius,radius-p.BASE_WALL,collar_height,p.BASE_LID_THICKNESS)
    tab_ring = _bayonet_tab_ring()
    tabs = [tab_ring & (Rot(0,0,i*360/p.BAYONET_COUNT)*
            _radial_sector(cavity+p.BASE_WALL,p.BAYONET_TAB_ANGLE,
                           p.BASE_HEIGHT,0)) for i in range(p.BAYONET_COUNT)]
    lid += tabs
    # A two-finger shallow recess remains within the3mm bottom plate.
    recess_depth = p.BASE_LID_THICKNESS/3
    lid -= Pos(0, 0, -p.CUT_OVERSHOOT)*Box(p.STEM_DIAMETER*2, p.STEM_DIAMETER/2, recess_depth+p.CUT_OVERSHOOT, align=A)
    lid.label = 'ballast_lid_three_tab_bayonet'
    lid.color = Color(*p.BLACK)
    return lid


def make_rim_trim():
    center = p.RIM_TRIM_DIAMETER/2-p.RIM_TRIM_WIDTH/2
    bottom = p.RIM_TRIM_BOTTOM_WIDTH/2
    top = p.RIM_TRIM_WIDTH/2
    result = _section_ring([(center-bottom,0),(center+bottom,0),
                           (center+top,p.RIM_TRIM_HEIGHT),
                           (center-top,p.RIM_TRIM_HEIGHT)])
    result.label = 'brass_rim_inlay'
    result.color = Color(*p.BRASS)
    return result


def make_foot_trim():
    result = _ring(p.FOOT_TRIM_OD/2, p.FOOT_TRIM_ID/2, p.FOOT_TRIM_HEIGHT)
    result.label = 'brass_stem_foot_ring'
    result.color = Color(*p.BRASS)
    return result


def make_stem():
    """Upright print. Assemble with root at globalZ(STEM_BOTTOM-tenon_length)."""
    local_shoulder = p.STEM_SHOULDER_Z-(p.STEM_BOTTOM-p.STEM_TENON_LENGTH)
    stem = _d_profile(p.STEM_TENON_DIAMETER/2, p.STEM_KEY_FLAT, p.STEM_TENON_LENGTH)
    transition = (p.STEM_DIAMETER-p.STEM_TENON_DIAMETER)/2
    stem += Pos(0, 0, p.STEM_TENON_LENGTH)*Cone(p.STEM_TENON_DIAMETER/2, p.STEM_DIAMETER/2, transition, align=A)
    stem += _cylinder(p.STEM_DIAMETER/2, local_shoulder-p.STEM_TENON_LENGTH-transition, p.STEM_TENON_LENGTH+transition)
    stem += Pos(0, 0, local_shoulder)*Box(p.COLLAR_TONGUE_WIDTH, p.COLLAR_TONGUE_DEPTH, p.COLLAR_TONGUE_HEIGHT, align=A)
    stem.label = 'upright_keyed_stem'
    stem.color = Color(*p.BLACK)
    return stem


def make_support_collar():
    """Axial printZ0..12. Assembly Pos(0,6,120)*Rot(90,0,0)."""
    radius = p.COLLAR_OD/2
    collar = _cylinder(radius, p.COLLAR_WIDTH)
    # Flat saddle shoulder supports the stem; its mouth opens radially downward.
    collar += Pos(0, -radius, 0)*Box(p.STEM_DIAMETER, p.COLLAR_TONGUE_HEIGHT, p.COLLAR_WIDTH, align=(Align.CENTER, Align.MIN, Align.MIN))
    bore = _d_profile(p.COLLAR_BORE/2, p.COLLAR_KEY_FLAT, p.COLLAR_WIDTH+2*p.CUT_OVERSHOOT, -p.CUT_OVERSHOOT)
    collar -= bore
    collar -= Pos(0, -radius-p.CUT_OVERSHOOT, p.COLLAR_WIDTH/2)*Box(p.COLLAR_TONGUE_WIDTH+2*p.COLLAR_SOCKET_CLEARANCE, radius-p.COLLAR_BORE/2+2*p.CUT_OVERSHOOT, p.COLLAR_TONGUE_DEPTH+2*p.COLLAR_SOCKET_CLEARANCE, align=(Align.CENTER, Align.MIN, Align.CENTER))
    collar.label = 'annular_hub_collar_open_sightline'
    collar.color = Color(*p.BLACK)
    return collar
