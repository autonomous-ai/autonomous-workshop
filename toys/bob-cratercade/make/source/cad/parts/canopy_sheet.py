"""Actual thin PET material envelopes; these are cut stock, never FDM parts."""
import params as p
from build123d import Color
from features.primitives import bounded_box


def roof():
    x0=(p.CANOPY_CELL_W-p.CANOPY_ROOF_SHEET_W)/2
    y0=(p.CANOPY_CELL_L-p.CANOPY_ROOF_SHEET_L)/2
    x1=x0+p.CANOPY_ROOF_SHEET_W; y1=y0+p.CANOPY_ROOF_SHEET_L
    z0=p.CANOPY_FRAME_TOP  # sheet rests on its rim inside the captured gap
    shape=bounded_box(x0,x1,y0,y1,z0,z0+p.CANOPY_PET_T)
    c=p.CANOPY_ROOF_SHEET_CORNER
    for xa,xb in ((x0,x0+c),(x1-c,x1)):
        for ya,yb in ((y0,y0+c),(y1-c,y1)):
            shape-=bounded_box(xa,xb,ya,yb,z0,z0+p.CANOPY_PET_T)
    h=p.CANOPY_ROOF_SHEET_NOTCH_HALF; end=p.CANOPY_ROOF_SHEET_NOTCH_END
    for xa,xb in ((x0,end),(p.CANOPY_CELL_W-end,x1)):
        shape-=bounded_box(xa,xb,p.CANOPY_CELL_L/2-h,p.CANOPY_CELL_L/2+h,z0,z0+p.CANOPY_PET_T)
    for ya,yb in ((y0,end),(p.CANOPY_CELL_L-end,y1)):
        shape-=bounded_box(p.CANOPY_CELL_W/2-h,p.CANOPY_CELL_W/2+h,ya,yb,z0,z0+p.CANOPY_PET_T)
    shape.color=Color(*p.CANOPY_PET_COLOR)
    return shape


def side(length):
    x=p.CANOPY_SIDE_SHEET_X
    shape=bounded_box(x-p.CANOPY_PET_T/2,x+p.CANOPY_PET_T/2,
                      0,length,p.CANOPY_SIDE_SHEET_BOTTOM,p.CANOPY_SIDE_SHEET_TOP+p.CANOPY_ROOF_LIFT)
    shape.color=Color(*p.CANOPY_PET_COLOR)
    return shape


def end(half=0,rear=False):
    """Two 148.4 x 96.4 cut sheets at each front/rear end."""
    clearance=p.CANOPY_SIDE_SHEET_END_CLEARANCE
    x0=p.CANOPY_POST_OUTER_X[1]-p.CANOPY_SLOT_DEPTH+clearance
    x1=p.CANOPY_CELL_W+p.CANOPY_END_JOIN_SLOT_X[1]-clearance
    if half: x0,x1=p.DECK_W-x1,p.DECK_W-x0
    sy=p.CANOPY_END_PANEL_Y[1 if rear else 0]
    shape=bounded_box(x0,x1,sy-p.CANOPY_PET_T/2,sy+p.CANOPY_PET_T/2,
                      p.CANOPY_SIDE_SHEET_BOTTOM,p.CANOPY_SIDE_SHEET_TOP+p.CANOPY_ROOF_LIFT)
    shape.color=Color(*p.CANOPY_PET_COLOR)
    return shape
