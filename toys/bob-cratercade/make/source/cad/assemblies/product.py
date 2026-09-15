"""Complete source assembly in the common inclined deck coordinate frame."""
import math
from build123d import Align,Axis,Box,Color,Pos,Rot,Sphere
from cadgen.assembly import AssemblyHelper
import params as p
from validation import validate_parameters
from assemblies.deck import components as deck_components,fastener_rows
from assemblies.deck_interfaces import inputs as deck_inputs
from assemblies.playfield import components as playfield_components,deck_mounts
from assemblies.return_system import components as return_components,hardware_parts as return_hardware
from parts.purchased_hardware import screw_csk,nut
from assemblies.jackpot import jackpot_parts
from assemblies.flippers import components as flipper_components
from assemblies.launcher import components as launcher_components
from assemblies.hardware import deck_fasteners,hardware_parts
from assemblies.bands import band_parts
from assemblies.containment import components as canopy_components,hardware_components as canopy_hardware

def build_product(jackpot_angle=0,left_fraction=0,right_fraction=0,pull=0,loaded=True,mission='A',service=False,door_states=None):
    validate_parameters()
    assembly=AssemblyHelper('cratercade')
    stance=Pos(0,0,p.FRONT_DATUM_Z)*Rot(p.INCLINE_DEG,0,0)
    for label,shape,color in deck_components(**deck_inputs())+return_components():
        assembly.add(stance*shape,label,color=Color(color) if isinstance(color,str) else color)
    for label,shape,color,_ in playfield_components(mission):
        assembly.add(stance*shape,label,color=Color(color))
    rocker=AssemblyHelper('jackpot_rocker_assembly')
    for label,shape,color in jackpot_parts(jackpot_angle):
        target=rocker if label in ('sample_bucket_flag','jackpot_trim','jackpot_trim_bolt','jackpot_trim_nut') else assembly
        target.add(stance*shape,label,color=color)
    assembly.add_module('jackpot_rocker_assembly',rocker.compound().children)
    for label,shape,color,metadata in flipper_components(left_fraction,right_fraction)+launcher_components(pull):
        assembly.add(stance*shape,label,color=Color(color))
    for label,shape,color,metadata in canopy_components(service=service,door_states=door_states)+canopy_hardware(service=service,door_states=door_states):
        assembly.add(stance*shape,label,color=Color(color) if isinstance(color,str) else color)
    for label,shape,color in hardware_parts()+return_hardware():
        assembly.add(stance*shape,label,color=color)
    steel=Color(0.64,0.67,0.70)
    rows=fastener_rows()+[(f"{r['part']}_mount_{i}",r['x'],r['y'],r['head_z'],r['nut_bottom_z'])
                          for i,r in enumerate(deck_mounts(mission))]
    for label,x,y,head,nut_bottom in rows:
        assembly.add(stance*Pos(x,y,head)*screw_csk(),label+'_bolt',color=steel)
        assembly.add(stance*Pos(x,y,nut_bottom)*nut(),label+'_nut',color=steel)
    for label,shape,color in band_parts(left_fraction,right_fraction,pull):
        assembly.add(stance*shape,label,color=color)
    # Cut-stock felt lies on the real horizontal table plane. Its footprint
    # matches the inclined foot's clipped base, not its unrotated XY box.
    angle=math.radians(p.INCLINE_DEG)
    for i,(x,y) in enumerate(p.FOOT_CENTERS):
        world_y=(y-math.sin(angle)*(p.FOOT_FELT_T-p.FRONT_DATUM_Z))/math.cos(angle)
        pad=Pos(x,world_y,0)*Box(p.FOOT_W,p.FOOT_L/math.cos(angle),p.FOOT_FELT_T,
                              align=(Align.CENTER,Align.CENTER,Align.MIN))
        assembly.add(pad,f'foot_felt_{i}',color=Color(.16,.18,.20))
    radius=p.MARBLE_MAX_D/2
    if loaded:
        slope=(p.BUCKET_FLOOR_Z[1]-p.BUCKET_FLOOR_Z[0])/(p.BUCKET_Y[1]-p.BUCKET_WALL-p.BUCKET_Y[0])
        y=p.BUCKET_Y[1]-p.BUCKET_WALL-radius
        z=p.BUCKET_FLOOR_Z[0]+slope*(y-p.BUCKET_Y[0])+radius*(1+slope*slope)**0.5
        ball=Pos(*p.JACKPOT_AXIS)*(Pos(0,y,z)*Sphere(radius)).rotate(Axis.X,jackpot_angle)
    else:
        ball=Pos(p.LAUNCH_X,p.LAUNCH_FACE_Y+radius,radius)*Sphere(radius)
    assembly.add(stance*ball,'marble',color=Color(0.18,0.44,0.63))
    return assembly.compound(label='cratercade')
