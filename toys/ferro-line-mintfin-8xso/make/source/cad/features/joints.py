"""Spherical snap interfaces, defined in world coordinates about a +Y axis.
The 0.25 diametral cavity is a geometric clearance. Compliance and friction
require the full-size coupon; this module cannot prove material recovery.
"""
from math import sqrt
from build123d import *
from params.body import SLIT, WALL

def y_cylinder(radius, y0, y1, z=0):
    return Pos(0,y0,z)*Rot(-90,0,0)*Cylinder(radius,y1-y0,align=(Align.CENTER,Align.CENTER,Align.MIN))

def socket(j, base_y):
    x,y,z=j['ball_center']; r=j['cavity_diameter']/2
    lip=j['lip_axial_position_from_center']
    outside=r+WALL
    shell=y_cylinder(outside,base_y,y+lip,z)
    sphere=Pos(x,y,z)*Rot(0,0,90)*Sphere(r)
    mouth=y_cylinder(j['mouth_diameter']/2,y,y+lip+2,z)
    shell=shell-sphere-mouth
    # Slits stop above a 1.6mm root; explicit elastic fingers, not a rigid fit.
    slit_y=max(base_y+1.6,y+lip-j['slit_length'])
    length=y+lip-slit_y+1
    cuts=[Pos(0,slit_y+length/2,z)*Box(SLIT,length,2*outside+2),
          Pos(0,slit_y+length/2,z)*Box(2*outside+2,length,SLIT)]
    return shell-cuts

def ball(j, shell_center_y):
    x,y,z=j['ball_center']; r=j['ball_diameter']/2
    stem=y_cylinder(j['neck_diameter']/2,y,shell_center_y+2.0,z)
    return (Pos(x,y,z)*Rot(0,0,90)*Sphere(r)).fuse(stem)

def socket_cavity(j):
    x,y,z=j['ball_center'];r=j['cavity_diameter']/2
    return (Pos(x,y,z)*Rot(0,0,90)*Sphere(r)).fuse(y_cylinder(j['mouth_diameter']/2,y,y+j['lip_axial_position_from_center']+1,z))

def preload_pads(j):
    """Four local elastic lands, nominal 0.075mm radial interference.
    Their overlap is intentional compliance, not a collision-free rigid fit.
    """
    from math import sqrt
    _,y,z=j['ball_center']; r=j['cavity_diameter']/2
    outer=Pos(0,y,z)*Rot(0,0,90)*Sphere(r+.15)
    inner=Pos(0,y,z)*Rot(0,0,90)*Sphere(r-.20)
    band=outer-inner
    pads=[]
    for sx,sz in ((1,1),(-1,1),(-1,-1),(1,-1)):
        c=r/sqrt(2)
        crop=Pos(sx*c,y, z+sz*c)*Box(1.6,1.6,1.6)
        pads.append(band&crop)
    return pads
