"""Symmetry-side printed stepped saddle; exact ledge-contact underside."""
from build123d import *
from features.common import prism_xz
from parts.tank_cover import envelope
from params import (BODY_SEAT_PROFILE, BODY_SEAT_Y_WIDTH, BODY_SEAT_CHAMFER,
    BODY_SEAT_TANK_SCALE_ORIGIN, BODY_SEAT_TANK_SCALE)

def build():
    seat=prism_xz(BODY_SEAT_PROFILE,*BODY_SEAT_Y_WIDTH)
    outer=seat.faces().sort_by(Axis.Y)[-1]
    seat=chamfer(outer.edges(),length=BODY_SEAT_CHAMFER)
    # Project the clearance at the symmetry plane through the full seat width.
    # A curved tank subtraction alone allowed the nose to grow unsupported.
    origin=BODY_SEAT_TANK_SCALE_ORIGIN
    clearance=Pos(*origin)*scale(Pos(*[-v for v in origin])*envelope(),by=BODY_SEAT_TANK_SCALE)
    profile=section(clearance,section_by=Plane.XZ)
    cutter=extrude(profile,amount=BODY_SEAT_Y_WIDTH[1],dir=(0,1,0))
    return seat-cutter
