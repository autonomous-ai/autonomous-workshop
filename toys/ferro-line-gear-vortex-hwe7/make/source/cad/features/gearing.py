"""20 degree stub involutes; tooth thinning occurs at pitch circle, never in centers."""
from math import sin, cos, tan, atan, sqrt, pi, radians, asin
from build123d import Edge, Wire, Face, Solid, Cylinder, Align, Vector
from params import M,PRESSURE_ANGLE,ADDENDUM_FACTOR,BACKLASH_FLANK,FACE,RIM,SPOKES,SPOKE_WIDTH

def polar(r,a):
    return (r*cos(a),r*sin(a),0)

def involute_wire(z):
    rp=M*z/2
    rb=rp*cos(radians(PRESSURE_ANGLE))
    rf=rp-1.25*M
    ra=rp+ADDENDUM_FACTOR*M
    ip=tan(radians(PRESSURE_ANGLE))-radians(PRESSURE_ANGLE)
    half=pi/(2*z)-BACKLASH_FLANK/rp
    edges=[]
    for k in range(z):
        center=2*pi*k/z
        def side(r,sgn):
            t=sqrt(max(0,(r/rb)**2-1))
            return polar(r,center+sgn*(half+ip-(t-atan(t))))
        # Counter-clockwise outline: root, left flank, tooth tip, right flank, root gap.
        p0=polar(rf,center-half-ip)
        p1=side(rb,-1)
        edges.append(Edge.make_line(p0,p1))
        pts=[side(rb+(ra-rb)*i/32,-1) for i in range(33)]
        edges.append(Edge.make_spline(pts,tol=1e-7))
        edges.append(Edge.make_three_point_arc(pts[-1],polar(ra,center),side(ra,1)))
        pts=[side(ra-(ra-rb)*i/32,1) for i in range(33)]
        edges.append(Edge.make_spline(pts,tol=1e-7))
        p2=polar(rf,center+half+ip)
        edges.append(Edge.make_line(pts[-1],p2))
        p3=polar(rf,center+2*pi/z-half-ip)
        edges.append(Edge.make_three_point_arc(p2,polar(rf,center+pi/z),p3))
    return Wire(edges)

def spoke_windows(z,hub_radius,hand):
    inner=M*z/2-1.25*M-RIM
    r0=hub_radius+.25
    r1=inner-.25
    assert r1-r0>=.8, 'pierced spoke window must survive nozzle'
    twist=.32
    rate=twist/(inner-hub_radius)
    holes=[]
    for j in range(SPOKES):
        left=[];right=[]
        for i in range(21):
            r=r0+(r1-r0)*i/20
            theta=2*pi*j/SPOKES+hand*rate*(r-hub_radius)
            # Normal width correction for swept spoke slope; minimum web2.6mm.
            margin=asin(SPOKE_WIDTH*sqrt(1+(r*rate)**2)/(2*r))
            left.append(polar(r,theta+margin))
            right.append(polar(r,theta+2*pi/SPOKES-margin))
        pts=left+right[::-1]
        holes.append(Wire.make_polygon(pts,close=True))
    return holes

def gear_solid(z,bore,hub_radius,hand):
    holes=spoke_windows(z,hub_radius,hand)
    holes.append(Wire.make_circle(bore/2))
    return Solid.extrude(Face(involute_wire(z),holes),(0,0,FACE))
