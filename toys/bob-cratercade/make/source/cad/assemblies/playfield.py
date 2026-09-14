"""Named static playfield placements and exact deck hardware interfaces."""
from math import cos,sin,radians
from build123d import Pos,Rot
import params as p
from parts import perimeter_wall,launch_divider,orbit_wall,return_guide,crater,mission_guide

def _place(label,shape,position=(0,0,0),angle=0,color="#718499"):
    shape=Pos(*position)*Rot(0,0,angle)*shape
    shape.label=label
    return label,shape,color,{"role":"stationary","printable":True,"removable":True}

def components(mission="A"):
    assert mission in p.MISSION_LAYOUTS
    out=[]
    for side in ("left","right"):
        y0=0
        for index,(length,bolts) in enumerate(zip(p.PERIMETER_LENGTHS,p.PERIMETER_SIDE_BOLTS)):
            shape=perimeter_wall.build(length,bolts,mirror=side=="right",post_y=p.CANOPY_WALL_POST_Y[index])
            out.append(_place(f"perimeter_{side}_{index+1}",shape,(0 if side=="left" else p.DECK_W,y0,0)))
            y0+=length
    for index in range(2):
        out.append(_place(f"perimeter_rear_{index+1}",perimeter_wall.build(p.PERIMETER_REAR_LENGTH,p.PERIMETER_REAR_BOLTS),
                          (p.PERIMETER_BASE_W+index*p.PERIMETER_REAR_LENGTH,p.DECK_L,0),-90))
    for index,y0 in enumerate((p.DIVIDER_Y0,p.DIVIDER_SPLIT_Y)):
        out.append(_place(f"launch_divider_{index+1}",launch_divider.build(index),(p.DIVIDER_X,y0,0),color="#287998"))
    for kind in ("inner","outer"):
        out.append(_place(f"orbit_{kind}_wall",orbit_wall.build(kind),(*p.ORBIT_CENTER,0),color="#287998"))
    for side in ("left","right"):
        out.append(_place(f"return_guide_{side}",return_guide.build(side),color="#287998"))
    layout=p.MISSION_LAYOUTS[mission]
    for index,(x,y,a) in enumerate(layout["craters"]):
        out.append(_place(f"mission_crater_{index+1}",crater.build(),(x,y,0),a,"#B8B5AD"))
    for index,(x,y,a) in enumerate(layout["guides"]):
        out.append(_place(f"mission_guide_{index+1}",mission_guide.build(),(x,y,0),a,"#DCA956"))
    return out

def _mount(label,x,y):
    return {"part":label,"x":x,"y":y,"head_z":p.PLAYFIELD_ROOT_T,
            "bore_d":p.M4_BORE,"nut_bottom_z":-p.DECK_T-p.NUT_T,
            "nut_rotation_z":0.0,"screw":"M4x16_countersunk","nut":"ISO4035_M4"}

def deck_mounts(mission="A"):
    assert mission in p.MISSION_LAYOUTS
    rows=[]
    for side in ("left","right"):
        y0=0
        for index,(length,bolts) in enumerate(zip(p.PERIMETER_LENGTHS,p.PERIMETER_SIDE_BOLTS)):
            x=p.PERIMETER_BOLT_X if side=="left" else p.DECK_W-p.PERIMETER_BOLT_X
            rows.extend(_mount(f"perimeter_{side}_{index+1}",x,y0+y) for y in bolts)
            y0+=length
    for index in range(2):
        rows.extend(_mount(f"perimeter_rear_{index+1}",p.PERIMETER_BASE_W+index*p.PERIMETER_REAR_LENGTH+y,p.DECK_L-p.PERIMETER_BOLT_X) for y in p.PERIMETER_REAR_BOLTS)
    for index,ys in enumerate(p.DIVIDER_BOLT_Y):
        rows.extend(_mount(f"launch_divider_{index+1}",p.DIVIDER_BOLT_X,y) for y in ys)
    for kind in ("inner","outer"):
        rows.extend(_mount(f"orbit_{kind}_wall",p.ORBIT_CENTER[0]+x,p.ORBIT_CENTER[1]+y) for x,y in orbit_wall.mount_points(kind))
    for side in ("left","right"):
        rows.extend(_mount(f"return_guide_{side}",x,y) for x,y in return_guide.mount_points(side))
    for kind,poses in p.MISSION_LAYOUTS[mission].items():
        for index,(x,y,angle) in enumerate(poses):
            for u in (-p.MISSION_BOLT_PITCH/2,p.MISSION_BOLT_PITCH/2):
                v=p.GUIDE_BOLT_Y if kind=="guides" else 0
                theta=radians(angle)
                rows.append(_mount(f"mission_{'guide' if kind=='guides' else 'crater'}_{index+1}",x+u*cos(theta)-v*sin(theta),y+u*sin(theta)+v*cos(theta)))
    return rows

def configuration_holes():
    """All unique A/B bolt holes; no broad grid holes under protected roots."""
    return sorted({(round(row["x"],8),round(row["y"],8)) for mission in p.MISSION_LAYOUTS for row in deck_mounts(mission)})
