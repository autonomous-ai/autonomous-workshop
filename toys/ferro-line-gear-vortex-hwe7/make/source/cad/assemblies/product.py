"""Named physical occurrences; all geometry belongs to the part builders."""
from math import degrees
from build123d import Pos,Rot,Color
from cadgen.assembly import AssemblyHelper
import params as p
from validation import audit
from parts.gears import planet,sun
from parts.carrier import carrier
from parts.core import axle,bezel,orange_disc,main_cap
from parts.retainers import gear_cap
from parts.stand import make_pedestal,make_pedestal_lid,make_stem,make_support_collar,make_rim_trim,make_foot_trim

def assembled():
    audit()
    asm=AssemblyHelper('gear_vortex')
    rotor=AssemblyHelper('rotor_black')
    planet_caps=AssemblyHelper('planet_caps_black')
    bezel_caps=AssemblyHelper('bezel_caps_black')
    axle_unit=AssemblyHelper('axle_front_lock_black')
    wheel=Pos(0,p.WHEEL_Y,p.HUB_HEIGHT)*Rot(90,0,0)
    def add(shape,name,color,parent=None):
        return (asm if parent is None else parent).add(shape,name,color=Color(*color))
    add(Pos(0,0,p.BASE_HEIGHT)*Rot(180,0,0)*make_pedestal(),'pedestal_black',p.BLACK)
    add(Rot(0,0,p.BAYONET_LOCK_ANGLE)*make_pedestal_lid(),'pedestal_lid_black',p.BLACK)
    add(Pos(0,0,p.STEM_BOTTOM-p.STEM_TENON_LENGTH)*make_stem(),'stem_black',p.BLACK)
    add(Pos(0,p.COLLAR_WIDTH/2,p.HUB_HEIGHT)*Rot(90,0,0)*make_support_collar(),'support_collar_black',p.BLACK)
    # Gravity seat: lower groove flank meets the flat bottom of the inlay.
    rim_z=p.BASE_HEIGHT-p.RIM_GROOVE_NECK_DEPTH-(p.RIM_GROOVE_NECK_WIDTH-p.RIM_TRIM_BOTTOM_WIDTH)/2*p.RIM_GROOVE_SLOPE
    add(Pos(0,0,rim_z)*make_rim_trim(),'rim_trim_yellow',p.BRASS)
    add(Pos(0,0,p.BASE_HEIGHT)*make_foot_trim(),'foot_trim_yellow',p.BRASS)
    add(wheel*Pos(0,0,p.AXLE_REAR)*axle(),'axle_black',p.BLACK,axle_unit)
    add(wheel*Pos(0,0,p.COLLAR_REAR_CAP_Z)*main_cap(),'rear_main_cap_black',p.BLACK)
    add(wheel*Pos(0,0,p.COLLAR_FRONT_CAP_Z)*Rot(0,0,180)*main_cap(),'support_main_cap_black',p.BLACK,axle_unit)
    add(wheel*Pos(0,0,p.ORANGE_Z)*orange_disc(),'orange_disc_orange',p.ORANGE)
    add(wheel*carrier(),'carrier_black',p.BLACK,rotor)
    add(wheel*Pos(0,0,p.GEAR_Z)*sun(),'sun_yellow',p.BRASS)
    add(wheel*Pos(0,0,p.MAIN_CAP_Z)*main_cap(),'front_main_cap_black',p.BLACK)
    for arm in range(2):
        halfturn=Rot(0,0,180*arm)
        for i,((x,y),n) in enumerate(zip(p.CENTERS,p.TEETH)):
            phase=degrees(p.PHASES[i]+p.LOADED_PHASE_OFFSETS[i])
            add(wheel*halfturn*Pos(x,y,p.GEAR_Z)*Rot(0,0,phase)*planet(i),f'gear_{arm+1}_{i+1}_yellow',p.BRASS)
            add(wheel*halfturn*Pos(x,y,p.CAP_Z)*gear_cap(),f'cap_{arm+1}_{i+1}_black',p.BLACK,planet_caps)
        add(wheel*halfturn*Pos(0,p.BEZEL_POST_RADIUS,p.BEZEL_CAP_Z)*gear_cap(),f'bezel_cap_{arm+1}_black',p.BLACK,bezel_caps)
    add(wheel*Pos(0,0,p.BEZEL_Z)*bezel(),'bezel_black',p.BLACK,rotor)
    rotor.add(planet_caps.compound(),'planet_caps_black')
    rotor.add(bezel_caps.compound(),'bezel_caps_black')
    asm.add(rotor.compound(),'rotor_black')
    asm.add(axle_unit.compound(),'axle_front_lock_black')
    return asm.compound()
