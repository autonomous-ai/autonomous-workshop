"""Two separately rooted circular rails, each one physical print.

Local datum is the exact arc center. The lowered Y456 crown preserves the full
24 mm route within the actual rear perimeter; centerline radius exceeds24.
"""
from math import sin,cos,radians
from build123d import CenterArc,Line,Wire,Face,Polygon,Pos,extrude
import params as p
from features.primitives import bounded_box,z_cylinder,top_countersink

def polar(radius,angle):
    return radius*cos(radians(angle)),radius*sin(radians(angle))

def sector(inner,outer,start,end):
    a,b=polar(outer,start),polar(outer,end)
    c,d=polar(inner,end),polar(inner,start)
    wire=Wire([CenterArc((0,0),outer,start,end-start),Line(b,c),
               CenterArc((0,0),inner,end,start-end),Line(d,a)])
    return extrude(Face(wire),amount=p.PLAYFIELD_WALL_H)

def mount_points(kind):
    radius=p.ORBIT_INNER_BOLT_R if kind=="inner" else p.ORBIT_OUTER_BOLT_R
    angles=p.ORBIT_INNER_BOLT_DEG if kind=="inner" else p.ORBIT_OUTER_BOLT_DEG
    return tuple(polar(radius,angle) for angle in angles)

def build(kind="inner"):
    assert kind in ("inner","outer")
    radius=p.ORBIT_RADIUS
    if kind=="inner":
        inner=radius-p.ORBIT_HALF_CLEAR-p.PLAYFIELD_WALL_T
        outer=radius-p.ORBIT_HALF_CLEAR
        body=sector(inner,outer,0,p.ORBIT_END_DEG)
        start_y=p.DIVIDER_Y1-p.ORBIT_CENTER[1]
        body+=bounded_box(inner,outer,start_y,0,0,p.PLAYFIELD_WALL_H)
        # Tangent continuation keeps the final centerline exactly at230,432.
        end_center=polar(radius,p.ORBIT_END_DEG)
        delta=(p.ORBIT_EXIT_X-p.ORBIT_CENTER[0]-end_center[0],p.ORBIT_EXIT_Y-p.ORBIT_CENTER[1]-end_center[1])
        a,b=polar(inner,p.ORBIT_END_DEG),polar(outer,p.ORBIT_END_DEG)
        profile=Polygon(a,b,(b[0]+delta[0],b[1]+delta[1]),(a[0]+delta[0],a[1]+delta[1]),align=None)
        body+=extrude(profile,amount=p.PLAYFIELD_WALL_H,dir=(0,0,1))
    else:
        inner=radius+p.ORBIT_HALF_CLEAR
        outer=inner+p.PLAYFIELD_WALL_T
        body=sector(inner,outer,p.ORBIT_OUTER_START_DEG,p.ORBIT_END_DEG)
        a,b=polar(inner,p.ORBIT_OUTER_START_DEG),polar(outer,p.ORBIT_OUTER_START_DEG)
        butt_x=p.DECK_W-p.PERIMETER_BASE_W-p.ORBIT_CENTER[0]
        profile=Polygon(a,b,(butt_x,b[1]),(butt_x,a[1]),align=None)
        body+=extrude(profile,amount=p.PLAYFIELD_WALL_H,dir=(0,0,1))
    for x,y in mount_points(kind):
        body+=z_cylinder(x,y,0,p.PLAYFIELD_WALL_H if kind=="outer" else p.PLAYFIELD_ROOT_T,p.PLAYFIELD_ROOT_R)
        body-=z_cylinder(x,y,-p.PLAYFIELD_CUT_MARGIN,p.PLAYFIELD_WALL_H+2*p.PLAYFIELD_CUT_MARGIN,p.M4_BORE/2)
        if kind=="outer":
            body-=z_cylinder(x,y,p.PLAYFIELD_ROOT_T,p.PLAYFIELD_WALL_H,p.PLAYFIELD_ACCESS_D/2)
        body-=top_countersink(x,y,p.PLAYFIELD_ROOT_T,p.PLAYFIELD_CSK_DEPTH,p.M4_BORE,p.CSK_RECESS_D)
    assert len(body.solids())==1
    return body

def print_shape(kind="inner"):
    body=build(kind)
    box=body.bounding_box()
    return Pos(-box.min.X,-box.min.Y,0)*body
