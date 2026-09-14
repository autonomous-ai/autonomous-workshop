"""Bearing towers and deck-rooted frame; local rocker-axis datum."""
import params as p
from features.primitives import bounded_box,x_cylinder,z_cylinder,top_countersink

def build_frame():
    pieces=[]
    floor=-p.JACKPOT_AXIS[2]
    for x0,x1 in p.FRAME_X_RANGES:
        pieces.append(bounded_box(x0,x1,*p.FRAME_Y_RANGE,floor,floor+p.FRAME_BASE_T))
    # North and south low cross ties stay below the rotating bucket envelope.
    for y in p.FRAME_CROSS_TIE_Y:
        pieces.append(bounded_box(p.FRAME_X_RANGES[0][0],p.FRAME_X_RANGES[-1][-1],
                                  y,y+p.FRAME_BASE_T,floor,floor+p.FRAME_BASE_T))
    for x0,x1 in p.FRAME_TOWER_X_RANGES:
        tower=bounded_box(x0,x1,-p.FRAME_TOWER_W/2,p.FRAME_TOWER_W/2,
                           floor,p.FRAME_TOWER_TOP)
        tower-=x_cylinder(x0-p.BUCKET_WALL,x1-x0+2*p.BUCKET_WALL,p.FRAME_AXLE_BORE/2)
        for y in (-p.CAP_BOLT_Y,p.CAP_BOLT_Y):
            tower-=x_cylinder(x0-p.BUCKET_WALL,x1-x0+2*p.BUCKET_WALL,p.M4_BORE/2,y,p.CAP_BOLT_Z)
        pieces.append(tower)
    pieces.append(bounded_box(p.FLAG_ARM_X-p.FLAG_ARM_W/2,p.FLAG_ARM_X+p.FLAG_ARM_W/2,
                              *p.JACKPOT_REST_STOP_Y,floor,p.ROCKER_PRINT_BASE_Z))
    pieces.append(bounded_box(p.FRAME_X_RANGES[0][0],p.FRAME_X_RANGES[-1][-1],
                              p.JACKPOT_TIP_Y-p.JACKPOT_STOP_HALF_L,
                              p.JACKPOT_TIP_Y+p.JACKPOT_STOP_HALF_L,floor,p.JACKPOT_TIP_Z))
    frame=pieces[0]
    for piece in pieces[1:]: frame+=piece
    for x,y in p.FRAME_BOLT_CENTERS:
        frame-=z_cylinder(x,y,floor-p.FRAME_BASE_T,3*p.FRAME_BASE_T,p.M4_BORE/2)
        frame-=top_countersink(x,y,floor+p.FRAME_BASE_T,p.CSK_HEAD_MAX_H,p.M4_BORE,p.CSK_RECESS_D)
    return frame
