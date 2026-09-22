"""Coarse printable trapezoidal thread for listed removable retainers.
Rigid sweep is geometric only; coupon qualifies friction and printed fit.
"""
from build123d import Edge,Wire,Face,Solid,Helix,Cylinder,Align,Pos

def cylinder(radius,height,z=0):
    return Pos(0,0,z)*Cylinder(radius,height,align=(Align.CENTER,Align.CENTER,Align.MIN))

def thread_ridge(major_radius,depth,pitch,length):
    root=major_radius-depth
    #60% pitch wide at base,20% at crest; flanks steeper than45deg.
    points=[(root-.08,0,-.30*pitch),(major_radius,0,-.10*pitch),
            (major_radius,0,.10*pitch),(root-.08,0,.30*pitch)]
    profile=Face(Wire.make_polygon(points,close=True))
    path=Helix(pitch,length+2*pitch,root,center=(0,0,-pitch))
    ridge=Solid.sweep(profile,path,is_frenet=True)
    return ridge & cylinder(major_radius+.2,length)

def male_thread(major_radius,depth,pitch,length):
    core=cylinder(major_radius-depth,length)
    return core.fuse(thread_ridge(major_radius,depth,pitch,length))

def female_tool(major_radius,depth,pitch,length,clearance):
    # Radial clearance keeps topology disjoint at nominal helical phase.
    core=cylinder(major_radius-depth+clearance,length+2,-1)
    ridge=thread_ridge(major_radius+clearance,depth,pitch,length)
    return core.fuse(ridge)
