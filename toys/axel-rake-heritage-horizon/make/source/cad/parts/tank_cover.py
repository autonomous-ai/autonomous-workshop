"""Original low teardrop storage cover above the inert electric pack."""
from build123d import *
from params import (TANK_SOCKET_D, BODY_TANK_SECTIONS,
    BODY_TANK_SOCKET_X, BODY_TANK_SOCKET_Z_DEPTH)

def envelope():
    # Lower sections have equal footprints: the bed outline supports the full
    # vertical skirt; the upper nested sections form the teardrop dome.
    return loft([Plane(origin=(x,0,z))*Ellipse(rx,ry)
        for z,x,rx,ry in BODY_TANK_SECTIONS],ruled=True)

def build():
    body=envelope()
    z,depth=BODY_TANK_SOCKET_Z_DEPTH
    for x in BODY_TANK_SOCKET_X:
        body=body-Pos(x,0,z)*Cylinder(TANK_SOCKET_D/2,depth,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return body
