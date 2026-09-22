"""Bed-rooted captive joints and the segmented body. No physical motion claim.
Lessons: cool before flex; rigid bearings replace living hinges; 0.4 mm bed
relief counters elephant foot. No Sphere or blind-ended curved-wall cutters.
"""
from math import cos,sin,radians
from build123d import *
from params import *

def one(shape,label):
    assert len(shape.solids())==1, f'{label}: disconnected solids'
    shape.label=label
    return shape

def radial_solid(profile):
    return revolve(Plane.XZ*Polygon(*profile,align=None),axis=Axis.Z)

def male_pin():
    p=[(0,0),(PIN_CAP_R-RELIEF,0),(PIN_CAP_R,RELIEF*2),
       (PIN_CAP_R,2),(PIN_NECK_R,4),(PIN_NECK_R,5),
       (PIN_CAP_R,7),(PIN_CAP_R,PIN_HEIGHT),(0,PIN_HEIGHT)]
    return one(radial_solid(p),'captive_pin')

def female_profile(clearance=HINGE_CLEARANCE):
    outer=bore_radius(PIN_CAP_R,clearance)
    low=min(4+clearance,4.5)
    high=max(5-clearance,4.5)
    throat=outer-(low-(2+clearance))
    return [(outer+RELIEF,0),(outer,RELIEF),(outer,2+clearance),
            (throat,low),(throat,high),(outer,7-clearance),(outer,PIN_HEIGHT)]

def bore_tool(clearance=HINGE_CLEARANCE):
    pr=female_profile(clearance)
    # Extend through both planar ends; no cutter face terminates inside a wall.
    return radial_solid([(0,-1),(pr[0][0],-1),*pr,(pr[-1][0],30),(0,30)])

def opening_tool():
    a=radians(OPENING_DEG/2)
    return Pos(0,0,-1)*extrude(Polygon((0,0),(-40*cos(a),40*sin(a)),
        (-40*cos(a),-40*sin(a)),align=None),32,dir=(0,0,1))

def female_bearing(clearance=HINGE_CLEARANCE):
    stock=Cylinder(BEARING_R,PIN_HEIGHT,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return one(stock-bore_tool(clearance)-opening_tool(),'captive_c_bearing')

def pod(cx,length,width,height,relief_rise=.4):
    # Flat grounded belly, modest first-layer relief, broad flat crown.
    stations=[(0,.96),(relief_rise,1),(3,1),(height*.73,.89),(height,.68)]
    faces=[Plane(origin=(cx,0,z))*Ellipse(length*s/2,width*s/2) for z,s in stations]
    return loft(faces,ruled=True)

def stem(x0,x1):
    return Pos((x0+x1)/2,0,0)*Box(x1-x0,STEM_WIDTH,STEM_HEIGHT,
        align=(Align.CENTER,Align.CENTER,Align.MIN))

def crest(height):
    pts=[(5.8,height-2),(11.2,height-2),(10.4,height+3),
         (8.8,height+4),(7.2,height+4),(5.8,height+1)]
    return Pos(0,-1.2,0)*extrude(Plane.XZ*Polygon(*pts,align=None),2.4,dir=(0,1,0))

def segment(index):
    w=BODY_WIDTHS[index-1]; h=BODY_HEIGHTS[index-1]
    body=pod(8,10,w,h,relief_rise=.8 if index==2 else .4)
    fin=crest(h)
    extras=[]
    if index in (1,4):
        for side in (-1,1):
            foot=Pos(8,side*12.5,0)*extrude(RectangleRounded(7,9,2),3.6)
            extras.append(foot)
    body=body.fuse(fin,*extras) if extras else body+fin
    # Preserve the incoming throat; free the entire neighboring bearing envelope.
    body=body-bore_tool()-opening_tool()
    keepout=Pos(JOINT_PITCH,0,-1)*Cylinder(BEARING_R+.65,35,
        align=(Align.CENTER,Align.CENTER,Align.MIN))
    body=body-keepout
    shape=body.fuse(female_bearing(),stem(8,JOINT_PITCH),Pos(JOINT_PITCH,0,0)*male_pin())
    return one(shape,f'body_{index}')

def tail():
    # Tapered broad paddle ending exactly 20 mm behind the last hinge.
    outline=Polygon((4,-7),(12,-6),(20,-2),(20,2),(12,6),(4,7),align=None)
    base=extrude(outline,3)
    top=loft([Plane(origin=(0,0,3))*outline,
        Plane(origin=(0,0,8))*Polygon((5,-4),(11,-3),(17,-1),(17,1),(11,3),(5,4),align=None)],ruled=True)
    fin=Pos(0,-1.2,0)*extrude(Plane.XZ*Polygon((5,5),(18,3),(18,5),
        (12,12),(9,12),(5,8),align=None),2.4,dir=(0,1,0))
    body=base.fuse(top,fin)-bore_tool()-opening_tool()
    return one(body+female_bearing(),'tail')

def coupon_pin():
    handle=Pos(-13,0,0)*extrude(RectangleRounded(10,8,1.5),2)
    return one(handle.fuse(stem(-10,0),male_pin()),'coupon_pin')

def coupon_receiver(clearance):
    handle=Pos(12,0,0)*extrude(RectangleRounded(12,10,1.5),2)
    # The aft handle overlaps the C-ring outside its clearance envelope.
    handle=handle-bore_tool(clearance)
    count=round((clearance-.25)/.1)
    for i in range(count):
        handle=handle-Pos(9+i*2.4,4.8,-1)*Box(1.2,2,4,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return one(female_bearing(clearance)+handle,f'coupon_receiver_{clearance}')

def color_regions(shape,role):
    """Split fused print solid into nonoverlapping volumetric AMS regions."""
    colors=[]
    if role.startswith('body_'):
        index=int(role.split('_')[-1]); h=BODY_HEIGHTS[index-1]
        colors.append(('coral',Pos(0,0,h-.1)*Box(40,40,12,align=(Align.CENTER,Align.CENTER,Align.MIN))))
        if index in(1,4):
            for side in(-1,1):
                colors.append(('charcoal',Pos(8,side*17,0)*Box(10,3.2,6,align=(Align.CENTER,Align.CENTER,Align.MIN))))
        colors.append(('cream',Pos(7,0,0)*Box(4,28,1.2,align=(Align.CENTER,Align.CENTER,Align.MIN))))
    elif role=='tail':
        colors.append(('coral',Pos(10,0,8)*Box(30,30,12,align=(Align.CENTER,Align.CENTER,Align.MIN))))
        colors.append(('cream',Pos(10,0,0)*Box(8,20,1.2,align=(Align.CENTER,Align.CENTER,Align.MIN))))
    remainder=shape
    result=[]
    for color,tool in colors:
        region=remainder&tool
        for solid in region.solids():
            if solid.volume>0.01: result.append((color,solid))
        remainder=remainder-tool
    result += [('mint',s) for s in remainder.solids()]
    return result
