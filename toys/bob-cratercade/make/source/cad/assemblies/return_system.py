"""Positions of covered return hoods, removable floors, funnel and pickup cup."""
from build123d import Axis,Color,Pos
import params as p
from parts.return_channel import hood,floor_lid,mount_points,print_shape as channel_print
from assemblies.hardware import deck_fasteners
from assemblies.playfield import configuration_holes
from parts.hopper import funnel,clamp
from parts.collection_cup import build as cup
from parts.purchased_hardware import screw_csk,nut
from features.primitives import bounded_box,z_cylinder

def ceiling_holes():
    """Sloped tool reliefs for deck-side nuts, clear of the ball centerline."""
    return list(dict.fromkeys([(x,y) for _,x,y,_,_ in deck_fasteners()]
                              +configuration_holes()+list(p.HOPPER_MOUNTS)
                              +[point for points in p.APRON_MOUNTS.values() for point in points]))

def print_channel(index,floor=False):
    return channel_print(index,floor,ceiling_holes())

def components():
    rows=[]
    for index,points in enumerate(p.RETURN_PATHS):
        at=Pos(*points[0],p.RETURN_FLOOR_Z)
        rows.append((f'return_hood_{index}',at*hood(index,ceiling_holes()),Color(0.16,0.23,0.31)))
        rows.append((f'return_floor_{index}',at*floor_lid(index),Color(0.27,0.37,0.43)))
    at=Pos(*p.HOPPER_CENTER,0)
    rows.append(('reset_hopper',at*funnel(),Color(0.48,0.64,0.69)))
    for side in ('left','right'):
        rows.append((f'hopper_clamp_{side}',at*clamp(side),Color(0.16,0.23,0.31)))
    rows.append(('collection_cup',cup(),Color(0.16,0.23,0.31)))
    return rows

def deck_mounts():
    """label,x,y,head_z,nut_bottom_z for downward M4x16 fasteners."""
    rows=[]
    ceiling=p.RETURN_FLOOR_Z+p.RETURN_CLEAR_H
    for index,points in enumerate(p.RETURN_PATHS):
        for i,(x,y) in enumerate(mount_points(index)):
            rows.append((f'return_root_{index}_{i}',x+points[0][0],y+points[0][1],0,ceiling-p.NUT_T))
    for i,(x,y) in enumerate(p.HOPPER_MOUNTS):
        rows.append((f'hopper_root_{i}',x,y,p.HOPPER_MOUNT_Z,-p.DECK_T-p.NUT_T))
    for i,(x,y) in enumerate(p.CUP_MOUNTS):
        rows.append((f'cup_root_{i}',x,y,0,-2*p.DECK_T-p.NUT_T))
    return rows

def hardware_parts():
    rows=[]
    steel=Color(0.64,0.67,0.70)
    for label,x,y,z,nut_z in deck_mounts():
        rows.extend(((label+'_bolt',Pos(x,y,z)*screw_csk(),steel),
                     (label+'_nut',Pos(x,y,nut_z)*nut(),steel)))
    for index,points in enumerate(p.RETURN_PATHS):
        for i,(x,y) in enumerate(mount_points(index,True)):
            x,y=x+points[0][0],y+points[0][1]
            label=f'return_floor_{index}_{i}'
            rows.append((label+'_bolt',Pos(x,y,p.RETURN_FLOOR_Z-p.RETURN_LID_T)*screw_csk().rotate(Axis.X,180),steel))
            rows.append((label+'_nut',Pos(x,y,p.RETURN_FLOOR_Z+p.RETURN_FLOOR_TAB_H)*nut(),steel))
    return rows

def deck_cutters():
    return [z_cylinder(*p.HOPPER_CENTER,-p.DECK_T,p.DECK_T,p.HOPPER_PORT_D/2),
            bounded_box(*p.CUP_DRAIN_X,*p.CUP_DRAIN_Y,-p.DECK_T,0)]

def rib_keepouts():
    # Exact part bounding boxes with a modest tool/assembly margin. Rooted
    # deck screw lands remain in the6mm playing face above this rib volume.
    cuts=[]
    c=p.RAMP_SEAT_CLEARANCE
    for _,shape,_ in components():
        b=shape.bounding_box()
        if b.min.Z < -p.DECK_T:
            cuts.append(bounded_box(b.min.X-c,b.max.X+c,b.min.Y-c,b.max.Y+c,
                                    b.min.Z-c,-p.DECK_T))
    return cuts
