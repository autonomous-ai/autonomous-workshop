"""Open three-web foot; local top matches deck, bottom is a true world plane."""
import math
from build123d import Plane, Polygon, Pos, Rectangle, extrude, loft
import params as p
from features.primitives import bounded_box, yz_prism, z_cylinder


def table_z(board_y, local_y):
    a = math.radians(p.INCLINE_DEG)
    return (p.FOOT_FELT_T-p.FRONT_DATUM_Z-(board_y+local_y)*math.sin(a))/math.cos(a)


def build_foot(board_y, upper_reliefs=()):
    """One solid, centered XY; upper bearing plane Z−DECK_T."""
    half_y = p.FOOT_L/2
    low = table_z(board_y,half_y)
    high = table_z(board_y,-half_y)
    top = -p.DECK_T
    sections = (
        Plane.XY.offset(low)*Rectangle(p.FOOT_W,p.FOOT_L),
        Plane.XY.offset(high+p.FOOT_BASE_T)*Rectangle(p.FOOT_W,p.FOOT_L),
        Plane.XY.offset(high+p.FOOT_FLARE_H)*Rectangle(p.FOOT_LAND_W,p.FOOT_LAND_L),
        Plane.XY.offset(top)*Rectangle(p.FOOT_LAND_W,p.FOOT_LAND_L),
    )
    foot = loft(sections,ruled=True)
    # Clip the lowest plinth to the exact table plane after the board rotates.
    foot &= yz_prism(-p.FOOT_W,p.FOOT_W,
                     [(-half_y,high),(half_y,low),(half_y,top),(-half_y,top)])
    # Open nut/tool access from both Y ends. Three 3 mm webs divide the final
    # upside-down print's bottom-plate bridges into 11.5 mm clear spans.
    inner = p.FOOT_LAND_W/2-p.FOOT_WEB_T
    intervals = ((-inner,-p.FOOT_WEB_T/2),(p.FOOT_WEB_T/2,inner))
    a = math.radians(p.INCLINE_DEG)
    base_rise = p.FOOT_BASE_T/math.cos(a)
    for x0,x1 in intervals:
        foot -= yz_prism(x0,x1,[(-half_y,high+base_rise),(half_y,low+base_rise),
                                (half_y,top-p.FOOT_LAND_T),
                                (-half_y,top-p.FOOT_LAND_T)])
    for x in (-p.FOOT_BOLT_X,p.FOOT_BOLT_X):
        foot -= z_cylinder(x,0,top-p.FOOT_LAND_T,p.FOOT_LAND_T,p.M4_BORE/2)
    for x0,x1,y0,y1 in upper_reliefs:
        bottom = top-p.FOOT_MECHANISM_CLEAR_DEPTH
        d = p.FOOT_RELIEF_CHAMFER
        rise = d*p.FOOT_RELIEF_SLOPE
        # The service notch opens through its nearest side. Its closing floor
        # slopes 45 degrees, avoiding a buried horizontal print overhang.
        along_y = abs((y0+y1)/p.FOOT_LAND_L)>=abs((x0+x1)/p.FOOT_LAND_W)
        lo,hi = (y0,y1) if along_y else (x0,x1)
        if lo+hi<0:
            points = [(lo,bottom),(hi-d,bottom),(hi,bottom+rise),(hi,top),(lo,top)]
        else:
            points = [(lo+d,bottom),(hi,bottom),(hi,top),(lo,top),(lo,bottom+rise)]
        if along_y:
            foot -= yz_prism(x0,x1,points)
        else:
            face = Plane.XZ*Polygon(*points,align=None)
            foot -= Pos(0,y0,0)*extrude(face,amount=y1-y0,dir=(0,1,0))
    assert len(foot.solids()) == 1, 'Foot must be one solid'
    return foot
