"""Placement at reviewed motorcycle datums. No part geometry authored here."""
from pathlib import Path
from build123d import Color,Plane,mirror,Pos,Rot,Axis,RevoluteJoint
from cadgen.assembly import AssemblyHelper
from cadgen.step_scene import import_step
from params import *
from parts import chassis_half,swingarm_side,fork_leg,fork_bridge,wheel,tank_cover,seat_half,pannier,front_fender,screen,handlebar,bar_riser,footboard,plinth

def build():
    asm=AssemblyHelper("heritage")
    for module,role,color in [(chassis_half,"chassis","charcoal"),(swingarm_side,"swingarm","gray"),(fork_leg,"fork_leg","gray"),(fork_bridge,"fork_bridge","gray"),(seat_half,"seat","brown"),(pannier,"pannier","brown"),(footboard,"footboard","charcoal")]:
        left=module.build()
        asm.add(left,role+"_left",color=Color(*COLORS[color]))
        asm.add(mirror(module.build(),about=Plane.XZ),role+"_right",color=Color(*COLORS[color]))
    for module,role,color in [(tank_cover,"tank_cover","teal"),(front_fender,"front_fender","teal"),(screen,"screen","screen"),(handlebar,"handlebar","gray"),(bar_riser,"bar_riser","gray"),(plinth,"plinth","charcoal")]:
        asm.add(module.build(),role,color=Color(*COLORS[color]))
    ref=Path(__file__).resolve().parents[1]/"ref"
    for name,x in zip(("rear","front"),AXLE_X):
        w=Pos(x,0,AXLE_Z)*wheel.build()
        RevoluteJoint(name+"_wheel_axis",w,Axis((x,0,AXLE_Z),(0,1,0)))
        asm.add(w,name+"_wheel",color=Color(*COLORS["tire"]))
        bolt=import_step(str(ref/"iso4762_socket_head_cap_screw_m3x30.step"))
        asm.add(Pos(x,-SUPPORT_OUTER,AXLE_Z)*Rot(90,0,0)*bolt,name+"_axle",color=Color(*COLORS["gray"]))
        for i in range(2):
            nut=import_step(str(ref/"iso4032_hex_nut_m3.step"))
            asm.add(Pos(x,SUPPORT_OUTER+i*NUT_HEIGHT,AXLE_Z)*Rot(-90,0,0)*nut,name+"_nut_"+str(i+1),color=Color(*COLORS["gray"]))
    return asm.compound()
