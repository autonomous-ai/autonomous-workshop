"""One homogeneous circular-segment rocker; dimensions in mm."""
from build123d import Cylinder, Box, Align, Axis, fillet
RADIUS = 40.0
CHORD_OFFSET = 18.0
WIDTH = 28.0
CORNER_RADIUS = 2.0

def rocker_print():
    disk = Cylinder(RADIUS, WIDTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    clip = Box(2*RADIUS+2, RADIUS-CHORD_OFFSET, WIDTH,
               align=(Align.CENTER, Align.MIN, Align.MIN)).translate((0,-RADIUS,0))
    body = disk & clip
    body = fillet(body.edges().filter_by(Axis.Z), CORNER_RADIUS)
    body = body.translate((0,RADIUS,0))
    body.label = 'Solid circular-segment rocker'
    assert len(body.solids()) == 1
    return body

def rocker_rest():
    return rocker_print().rotate(Axis.X,90).translate((0,WIDTH/2,0))
