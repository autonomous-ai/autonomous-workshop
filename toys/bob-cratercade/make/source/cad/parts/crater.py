"""Raised lunar rim and central mound with two open service channels."""
from build123d import Align,Cone,Pos
import params as p
from features.primitives import bounded_box,z_cylinder,top_countersink

def build():
    body=z_cylinder(0,0,0,p.PLAYFIELD_ROOT_T,p.CRATER_R)
    rim=Pos(0,0,p.PLAYFIELD_ROOT_T)*Cone(p.CRATER_R,p.CRATER_RIM_TOP_R,
        p.CRATER_RIM_H-p.PLAYFIELD_ROOT_T,align=(Align.CENTER,Align.CENTER,Align.MIN))
    rim-=z_cylinder(0,0,p.PLAYFIELD_ROOT_T,p.CRATER_H,p.CRATER_RIM_INNER_R)
    mound=Pos(0,0,p.PLAYFIELD_ROOT_T)*Cone(p.CRATER_MOUND_FOOT_R,p.CRATER_MOUND_TOP_R,
        p.CRATER_H-p.PLAYFIELD_ROOT_T,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body+=rim+mound
    for sign in (-1,1):
        x=sign*p.MISSION_BOLT_PITCH/2
        limits=(x-p.CRATER_ACCESS_W/2,p.CRATER_R+p.PLAYFIELD_CUT_MARGIN) if sign>0 else (-p.CRATER_R-p.PLAYFIELD_CUT_MARGIN,x+p.CRATER_ACCESS_W/2)
        body-=bounded_box(*limits,-p.CRATER_ACCESS_W/2,p.CRATER_ACCESS_W/2,p.PLAYFIELD_ROOT_T,p.CRATER_H+p.PLAYFIELD_CUT_MARGIN)
        body-=z_cylinder(x,0,-p.PLAYFIELD_CUT_MARGIN,p.CRATER_H+2*p.PLAYFIELD_CUT_MARGIN,p.M4_BORE/2)
        body-=top_countersink(x,0,p.PLAYFIELD_ROOT_T,p.PLAYFIELD_CSK_DEPTH,p.M4_BORE,p.CSK_RECESS_D)
    assert len(body.solids())==1
    return body
