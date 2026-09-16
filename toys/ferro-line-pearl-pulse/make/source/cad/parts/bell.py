"""Crown-down, three-colour co-printed bell and three concealed bayonet seats.

Material boundaries are actual solids. They must be registered and co-printed;
these are not paint, detachable wedges, or a set of unsupported display faces.
"""
from functools import lru_cache
from math import cos, sin, pi, radians, sqrt
from build123d import (Spline, Wire, Face, Solid, Polygon, extrude, loft,
                      Pos, Rot, Cylinder, Align, CenterArc, Line)
from params import (PEARL, BLUSH, MIST, BELL_CROWN_Z, BELL_CROWN_R,
                    BELL_MEAN_R, BELL_SCALLOP, BELL_LOBES, BELL_WALL,
                    BELL_POST_ANGLES, BELL_COLOUR_CENTRES,
                    BELL_COLOUR_HALF_ANGLE, BELL_COLOUR_INNER_R,
                    BELL_LOCK_TURN, BELL_SOCKET_BOTTOM_Z,
                    BELL_RIM_EXTRA_INSET, BELL_RECEIVER_INNER_R,
                    BELL_RECEIVER_OUTER_R, BELL_RIM_ROUND_R)


def _radius(z, theta):
    t = z / 18.0
    # C2 smooth radial growth, with sixteen lobes growing only toward the rim.
    return BELL_CROWN_R + (BELL_MEAN_R-BELL_CROWN_R)*t + BELL_SCALLOP*t*t*cos(BELL_LOBES*theta)


def _ring(z, inset=0):
    pts=[]
    for i in range(64):
        a=2*pi*i/64
        r=_radius(z,a)-inset
        pts.append((r*cos(a),r*sin(a),z))
    return Wire([Spline(*pts, periodic=True)])


def _sector(inner, outer, a0, a1, z=0):
    def point(r,a):
        return (r*cos(radians(a)),r*sin(radians(a)))
    edges=[CenterArc((0,0),outer,a0,a1-a0),
           Line(point(outer,a1),point(inner,a1)),
           CenterArc((0,0),inner,a1,a0-a1),
           Line(point(inner,a0),point(outer,a0))]
    return Pos(0,0,z)*Face(Wire(edges))


def _sector_prism(inner,outer,a0,a1,z0,z1):
    return extrude(_sector(inner,outer,a0,a1,z0),amount=z1-z0)


def _socket(a, envelope):
    # Print coordinates: z=0 is crown, positive toward open rim.
    # Broaden only the receiver's outside walls; mating channel stays exact.
    # The earlier 2.7-degree entry margin left a thin extended corner band.
    receiver=_sector_prism(BELL_RECEIVER_INNER_R,BELL_RECEIVER_OUTER_R,
                           a-23,a+11,1.1,
                           BELL_CROWN_Z-BELL_SOCKET_BOTTOM_Z) & envelope
    # 45-degree inward capture roof, with the outer channel wall unchanged.
    levels=((1.8,22.6),(3.8,22.6),(5.0,23.8),(6.2,23.8))
    channel=loft([_sector(r,26.8,a-17.3,a+5.3,z) for z,r in levels],ruled=True)
    entry=_sector_prism(22.6,26.8,a-BELL_LOCK_TURN-5.3,
                         a-BELL_LOCK_TURN+5.3,1.8,6.4)
    return receiver-channel-entry


@lru_cache(maxsize=1)
def _whole_print():
    # Ruled stations reproduce the intended radial quadratic to <0.006mm
    # without the unconstrained low-shoulder drift of mixed smooth lofts.
    # A small constructed rim round removes the long sharp knife-edge band.
    stations=(0,3,6,9,12,15,17.6,17.8,17.9,17.95,18)
    def rim_round(z):
        r=BELL_RIM_ROUND_R
        h=max(0.0,z-(18-r))
        return r-sqrt(max(0.0,r*r-h*h)) if h>0 else 0.0
    outer=Solid.make_loft([_ring(z,rim_round(z)) for z in stations],ruled=True)
    # Explicit cavity: radial inset is the normal wall corrected for slope.
    inset=BELL_WALL*(1+((BELL_MEAN_R-BELL_CROWN_R)/18)**2)**0.5
    # Reinforce the opening internally over its final six mm. The exterior
    # silhouette and mating sockets are unchanged; extra rim inset grows at
    # <=0.3mm/mm, keeping the inward material growth supported by prior layers.
    cavity_sections=[]
    for z in (BELL_WALL,3,6,9,12,15,17.6,17.8,17.9,17.95,18,19):
        t=min(1.0,max(0.0,(z-12)/6))
        cavity_sections.append(_ring(z,inset+BELL_RIM_EXTRA_INSET*t*t-rim_round(z)))
    cavity=Solid.make_loft(cavity_sections,ruled=True)
    shell=outer-cavity
    seats=[_socket(-a,outer) for a in BELL_POST_ANGLES]
    body=shell.fuse(*seats)
    assert len(body.solids())==1, 'bell body must be one co-print solid'
    return body


def _colour_tool(index):
    a=-BELL_COLOUR_CENTRES[index]
    return _sector_prism(BELL_COLOUR_INNER_R,45,a-BELL_COLOUR_HALF_ANGLE,
                         a+BELL_COLOUR_HALF_ANGLE,-1,20)


def bell(region='pearl', print_orientation=True):
    """One material leaf, crown down by default; world pose at nominal z118."""
    whole=_whole_print()
    if region=='pearl':
        result=whole-[_colour_tool(0),_colour_tool(1)]
        colour=PEARL
    elif region in ('blush','mist'):
        index=0 if region=='blush' else 1
        result=whole & _colour_tool(index)
        colour=BLUSH if index==0 else MIST
    else:
        raise ValueError('bell region must be pearl, blush, or mist')
    assert len(result.solids())==1, 'each material region must be one solid'
    result.label='bell_'+region+'_co_print_region'
    result.color=colour
    if not print_orientation:
        result=Pos(0,0,BELL_CROWN_Z)*Rot(180,0,0)*result
        result.label='bell_'+region+'_co_print_region'
        result.color=colour
    return result
