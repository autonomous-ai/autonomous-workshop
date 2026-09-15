"""Replaceable rubber bands in nominal installed clearance envelopes.

These deformed solids identify routing and material sections. They do not model
elastic force, fatigue, or volume conservation during stretch.
"""
from math import cos,sin,radians
from build123d import Color,Plane,Pos
import params as p
from parts.rubber_band import band

def band_parts(left_fraction=0,right_fraction=0,pull=0,anchor_index=0):
    rows=[]
    for side,fraction in (('left',left_fraction),('right',right_fraction)):
        angle=radians(p.FLIPPER_TRAVEL*fraction)
        x,y=p.FLIPPER_TAIL_JOINT
        moving=(x*cos(angle)-y*sin(angle),x*sin(angle)+y*cos(angle))
        shape=band(p.FLIPPER_FIXED_ANCHORS[side][0],moving,
                   p.FLIPPER_BAND_RADII[side],p.BAND_T,p.BAND_WIDTH,
                   p.FLIPPER_BAND_CENTER_Z,p.FLIPPER_BAND_TURNS[side],
                   p.FLIPPER_BAND_RADIAL_WOBBLE[side],p.FLIPPER_BAND_AXIAL_WOBBLE[side],
                   p.BAND_SAMPLES_PER_LAP)
        if side=='right': shape=shape.mirror(Plane.YZ)
        rows.append((f'flipper_{side}_rubber_band',Pos(*p.FLIPPER_PIVOTS[side],0)*shape,Color(0.67,0.30,0.16)))
    launch=band((p.LAUNCH_BAND_X,p.LAUNCH_ANCHOR_Y[anchor_index]),
                (p.LAUNCH_BAND_X,p.LAUNCH_MOVING_POST_Y-pull),
                p.LAUNCHER_BAND_RADIUS,p.BAND_T,p.BAND_WIDTH,p.LAUNCH_BAND_Z,
                1,0,0,p.BAND_SAMPLES_PER_LAP)
    rows.append(('launcher_rubber_band',launch,Color(0.67,0.30,0.16)))
    return rows
