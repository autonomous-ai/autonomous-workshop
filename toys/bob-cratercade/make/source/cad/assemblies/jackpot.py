"""Exact positioning of one common rocker; no independent flag animation."""
from build123d import Axis,Pos,Color
import params as p
from parts.jackpot_rocker import build_rocker
from parts.jackpot_frame import build_frame
from parts.jackpot_trim import build_trim
from parts.landing_ramp import build_ramp
from parts.wooden_axle import build_axle
from parts.purchased_hardware import screw_csk,nut
from parts.jackpot_axle_cap import build as build_cap

def jackpot_parts(angle=0):
    rocker=build_rocker().rotate(Axis.X,angle)
    trim=(Pos(p.FLAG_ARM_X,p.TRIM_Y,p.TRIM_Z)*build_trim()).rotate(Axis.X,angle)
    trim_bolt=(Pos(p.FLAG_ARM_X,p.TRIM_Y,p.ROCKER_PRINT_BASE_Z-p.TRIM_H)
               *screw_csk().rotate(Axis.X,180)).rotate(Axis.X,angle)
    trim_nut=(Pos(p.FLAG_ARM_X,p.TRIM_Y,p.ROCKER_PRINT_BASE_Z+p.FLAG_ARM_T)
              *nut()).rotate(Axis.X,angle)
    at=Pos(*p.JACKPOT_AXIS)
    items=[
        ('sample_bucket_flag',at*rocker,Color(1.0,0.62,0.05)),
        ('jackpot_trim',at*trim,Color(0.20,0.28,0.36)),
        ('jackpot_trim_bolt',at*trim_bolt,Color(0.64,0.67,0.70)),
        ('jackpot_trim_nut',at*trim_nut,Color(0.64,0.67,0.70)),
        ('jackpot_wooden_axle',at*build_axle(),Color(0.64,0.44,0.23)),
        ('jackpot_frame',at*build_frame(),Color(0.16,0.23,0.31)),
        ('landing_ramp',Pos(p.JACKPOT_AXIS[0],p.RAMP_Y0,0)*build_ramp(),Color(0.48,0.64,0.69)),
    ]
    items += [
        ('jackpot_left_cap',at*Pos(p.CAP_LEFT_X,0,0)*build_cap(),Color(0.16,0.23,0.31)),
        ('jackpot_right_cap',at*Pos(p.CAP_RIGHT_X,0,0)*build_cap().rotate(Axis.Z,180),Color(0.16,0.23,0.31)),
    ]
    return items
