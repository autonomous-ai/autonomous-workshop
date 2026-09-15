"""Identical underside splice, local base Z0 with upright locating pins."""
import params as p
from features.primitives import bounded_box, z_cylinder


def dimensions(short=False):
    return ((p.DECK_SHORT_STRAP_L,p.DECK_SHORT_STRAP_BOLT_Y,p.DECK_SHORT_STRAP_PIN_Y)
            if short else (p.DECK_STRAP_L,p.DECK_STRAP_BOLT_Y,p.DECK_STRAP_PIN_Y))


def build_strap(short=False):
    length,bolt_y,pin_y = dimensions(short)
    strap = bounded_box(-p.DECK_STRAP_WEB_W/2,p.DECK_STRAP_WEB_W/2,
                        -length/2,length/2,0,p.DECK_STRAP_T)
    # Broad four-bolt lands preserve the 32 mm envelope. Narrow waists leave
    # access to neighboring mechanism nuts; end necks clear adjacent roots.
    for sign_x in (-1,1):
        x0,x1 = ((-p.DECK_STRAP_WEB_W/2,-p.DECK_STRAP_END_W/2)
                 if sign_x<0 else (p.DECK_STRAP_END_W/2,p.DECK_STRAP_WEB_W/2))
        for sign_y in (-1,1):
            y0,y1 = ((-length/2,-length/2+p.DECK_STRAP_END_L)
                     if sign_y<0 else (length/2-p.DECK_STRAP_END_L,length/2))
            strap -= bounded_box(x0,x1,y0,y1,0,p.DECK_STRAP_T)
    for x in (-p.DECK_STRAP_BOLT_X,p.DECK_STRAP_BOLT_X):
        for y in (-bolt_y,bolt_y):
            strap += z_cylinder(x,y,0,p.DECK_STRAP_T,p.DECK_STRAP_BOLT_LAND_R)
    for x in (-p.DECK_STRAP_PIN_X,p.DECK_STRAP_PIN_X):
        for y in (-pin_y,pin_y):
            strap += z_cylinder(x,y,p.DECK_STRAP_T,p.DECK_STRAP_PIN_H,
                                p.DECK_STRAP_PIN_D/2)
    for x in (-p.DECK_STRAP_BOLT_X,p.DECK_STRAP_BOLT_X):
        for y in (-bolt_y,bolt_y):
            strap -= z_cylinder(x,y,0,p.DECK_STRAP_T,p.M4_BORE/2)
    assert len(strap.solids()) == 1, 'A splice must remain one rooted solid'
    return strap
