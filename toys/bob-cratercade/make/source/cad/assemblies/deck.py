"""Deck placement and common cutter interface; independent of mechanism modules."""
import math
from build123d import Pos, Rot
import params as p
from parts.deck_tile import build_tile
from parts.seam_strap import build_strap, dimensions as strap_dimensions
from parts.foot import build_foot


def _point(x,y,angle,dx,dy):
    a = math.radians(angle)
    return (x+dx*math.cos(a)-dy*math.sin(a),
            y+dx*math.sin(a)+dy*math.cos(a))


def fastener_rows():
    """(label,x,y,head_z,nut_bottom_z): all vertical qualified M4×16 CSK."""
    rows = []
    for i,(x,y,angle) in enumerate(p.DECK_STRAP_POSES):
        _,bolt_y,_ = strap_dimensions(i in p.DECK_SHORT_STRAP_INDICES)
        for j,(dx,dy) in enumerate(((-p.DECK_STRAP_BOLT_X,-bolt_y),
                                    (-p.DECK_STRAP_BOLT_X,bolt_y),
                                    (p.DECK_STRAP_BOLT_X,-bolt_y),
                                    (p.DECK_STRAP_BOLT_X,bolt_y))):
            bx,by = _point(x,y,angle,dx,dy)
            rows.append((f'deck_strap_{i}_{j}',bx,by,0.0,-p.DECK_T-p.DECK_STRAP_T-p.NUT_T))
    for i,(x,y) in enumerate(p.FOOT_CENTERS):
        for j,dx in enumerate((-p.FOOT_BOLT_X,p.FOOT_BOLT_X)):
            rows.append((f'deck_foot_{i}_{j}',x+dx,y,0.0,-p.DECK_T-p.FOOT_LAND_T-p.NUT_T))
    return rows


def _structural_interfaces():
    sockets = []
    exclusions = list(p.DECK_RETURN_RIB_EXCLUSIONS)
    for i,(x,y,angle) in enumerate(p.DECK_STRAP_POSES):
        length,_,pin_y = strap_dimensions(i in p.DECK_SHORT_STRAP_INDICES)
        for dx in (-p.DECK_STRAP_PIN_X,p.DECK_STRAP_PIN_X):
            for dy in (-pin_y,pin_y):
                sockets.append(_point(x,y,angle,dx,dy))
        sx,sy = (p.DECK_STRAP_W/2,length/2) if angle==0 else (length/2,p.DECK_STRAP_W/2)
        exclusions.append((x-sx,x+sx,y-sy,y+sy))
    for x,y in p.FOOT_CENTERS:
        exclusions.append((x-p.FOOT_LAND_W/2,x+p.FOOT_LAND_W/2,
                           y-p.FOOT_LAND_L/2,y+p.FOOT_LAND_L/2))
    return sockets,exclusions


def tile(column,row,holes=(),cutters=(),rib_keepouts=()):
    """Return one cell in its local nominal 160 mm frame."""
    assert 0<=column<p.DECK_COLUMNS and 0<=row<p.DECK_ROWS
    ox,oy = column*p.DECK_CELL,row*p.DECK_CELL
    gap = p.DECK_SEAM/2
    bounds = (gap if column else 0,p.DECK_CELL-gap if column<p.DECK_COLUMNS-1 else p.DECK_CELL,
              gap if row else 0,p.DECK_CELL-gap if row<p.DECK_ROWS-1 else p.DECK_CELL)
    structural = [(x,y) for _,x,y,_,_ in fastener_rows()]
    all_holes = tuple(dict.fromkeys(tuple(h) for h in (*holes,*structural)))
    sockets,exclusions = _structural_interfaces()
    for keepout in rib_keepouts:
        if isinstance(keepout,(tuple,list)):
            exclusions.append(tuple(keepout))
        else:
            b = keepout.bounding_box()
            exclusions.append((b.min.X,b.max.X,b.min.Y,b.max.Y))
    def local_points(points):
        return [(x-ox,y-oy) for x,y in points
                if ox<=x<=ox+p.DECK_CELL and oy<=y<=oy+p.DECK_CELL]
    local_cuts = []
    for cutter in cutters:
        b = cutter.bounding_box()
        if b.max.X>=ox and b.min.X<=ox+p.DECK_CELL and b.max.Y>=oy and b.min.Y<=oy+p.DECK_CELL:
            local_cuts.append(Pos(-ox,-oy,0)*cutter)
    return build_tile(bounds,local_points(all_holes),local_points(structural),
                      local_points(sockets),local_cuts,
                      [(x0-ox,x1-ox,y0-oy,y1-oy) for x0,x1,y0,y1 in exclusions])


def tile_for_print(column,row,**inputs):
    # The ball-contact face is the print bed; ribs and blind sockets face up.
    return Pos(0,p.DECK_CELL,0)*Rot(180,0,0)*tile(column,row,**inputs)


def _foot(index, holes=()):
    x,y = p.FOOT_CENTERS[index]
    a = p.DECK_NUT_ACCESS_HALF
    reliefs = list(p.FOOT_RELIEFS.get(index,()))
    for hx,hy in holes:
        dx,dy = hx-x,hy-y
        if (abs(dx)<p.FOOT_LAND_W/2+p.FOOT_NUT_ENVELOPE_R and
                abs(dy)<p.FOOT_LAND_L/2+p.FOOT_NUT_ENVELOPE_R):
            reliefs.append((dx-a,dx+a,dy-a,dy+a))
    return build_foot(y,reliefs)


def foot_for_print(index,holes=(),cutters=(),rib_keepouts=()):
    return Pos(0,0,-p.DECK_T)*Rot(180,0,0)*_foot(index,holes)


def components(holes=(),cutters=(),rib_keepouts=()):
    items = []
    for row in range(p.DECK_ROWS):
        for column in range(p.DECK_COLUMNS):
            shape = tile(column,row,holes,cutters,rib_keepouts)
            items.append((f'deck_tile_{column}_{row}',Pos(column*p.DECK_CELL,row*p.DECK_CELL,0)*shape,p.DECK_STRUCTURE_COLOR))
    for i,(x,y,angle) in enumerate(p.DECK_STRAP_POSES):
        shape = Pos(x,y,-p.DECK_T-p.DECK_STRAP_T)*Rot(0,0,angle)*build_strap(i in p.DECK_SHORT_STRAP_INDICES)
        items.append((f'deck_seam_strap_{i}',shape,p.DECK_BRACE_COLOR))
    for i,(x,y) in enumerate(p.FOOT_CENTERS):
        items.append((f'deck_foot_{i}',Pos(x,y,0)*_foot(i,holes),p.DECK_BRACE_COLOR))
    return items
