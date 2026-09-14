from build123d import *
from params import *
from features.common import box_bounds, prism_xz, cylinder_y, annular_sector, plate_link

def build():
    battery=box_bounds(BATTERY_BOUNDS)
    rear=annular_sector(*FRAME_REAR_CENTER,ARCH_INNER,ARCH_OUTER,*FRAME_REAR_ANGLES,0,CHASSIS_REAR_WIDTH)
    motor=cylinder_y(*FRAME_MOTOR)
    spine=plate_link(*FRAME_SPINE)
    neck=prism_xz(FRAME_NECK_PROFILE,0,SUPPORT_INNER)
    pieces=[rear,motor,spine,neck,box_bounds(FRAME_STEER_HOUSING),
      box_bounds(FRAME_REAR_SEAT_LEDGE),box_bounds(FRAME_RIDER_LEDGE),
      box_bounds(FRAME_BOARD_LEDGE)]
    for x in FRAME_TANK_PIN_X:
        pieces.append(box_bounds((x-FRAME_LEDGE_HALF,x+FRAME_LEDGE_HALF,0,FRAME_LEDGE_Y,FRAME_PACK_TOP,FRAME_TANK_BOTTOM)))
        pin=Pos(x,0,FRAME_TANK_BOTTOM)*Cylinder(TANK_PIN_D/2,FRAME_PIN_H,align=(Align.CENTER,Align.CENTER,Align.MIN))
        pieces.append(pin.intersect(box_bounds((x-FRAME_LEDGE_HALF,x+FRAME_LEDGE_HALF,0,FRAME_LEDGE_Y,FRAME_PACK_TOP,FRAME_PIN_CLIP_TOP)))[0])
    # V cooling shoulders are supported relief on the electric pack's face.
    shoulders=FRAME_SHOULDERS
    for points in shoulders:
        pieces.append(prism_xz(points,FRAME_SHOULDER_Y,FRAME_SHOULDER_T))
    for x,z in FRAME_RIB_CENTERS:
        pieces.append(box_bounds((x-FRAME_RIB_HALF_LENGTH,x+FRAME_RIB_HALF_LENGTH,FRAME_RIB_Y0,FRAME_RIB_Y1,z-FRAME_RIB_HALF_H,z+FRAME_RIB_HALF_H)))
    s=battery.fuse(*pieces)
    # Shared mating profiles remove frame intrusion without altering body form.
    saddle_seat=prism_xz(BODY_SEAT_PROFILE,0,BODY_SEAT_Y_WIDTH[1])
    a,b,r=FRAME_SWING_LINK
    swing_relief=plate_link(a,b,r+FRAME_SWING_CLEARANCE,SUPPORT_INNER-FRAME_SWING_CLEARANCE,FRAME_MOTOR[1])
    s=s.cut(box_bounds(ROOT_SLOT),box_bounds(STEER_SLOT),saddle_seat,swing_relief)
    return s
