"""Assembly datums: fixed carrier; Z pivot at(-10,29); fixed pin head under Z0."""
from build123d import *
from moon_lib import carrier, leaf, pin, cover, inlay_datum, named, PIVOT

def assemble(angle=0):
    base=carrier()
    rotor=leaf()
    RevoluteJoint('leaf_axis',base,Axis((*PIVOT,0),(0,0,1)),angular_range=(0,75))
    RigidJoint('bearing_datum',rotor,Location((*PIVOT,0)))
    base.joints['leaf_axis'].connect_to(rotor.joints['bearing_datum'],angle=angle)
    pivot=Pos(*PIVOT,-1.6)*pin()
    lid=cover()
    tag=named(inlay_datum(),'inlay',(0.92,0.94,0.87))
    return Compound(label='moon_fan',children=[base,rotor,pivot,lid,tag])
