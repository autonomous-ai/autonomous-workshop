"""Raised approach with clear underside around the transverse rocker hub."""
import params as p
from features.primitives import bounded_box,yz_prism,z_cylinder,top_countersink

def build_ramp():
    length=p.RAMP_Y1-p.RAMP_Y0
    supported=p.RAMP_SUPPORT_END-p.RAMP_Y0
    # The 1.2 mm toe seats flush in the deck. A 46.4 degree rising underside
    # clears the hub continuously. The Z40 exit drops 4 mm into the Z36 entry;
    # this removes the unanchored terminal cantilever rejected in round 3.
    surface=[(0,0),(length,p.RAMP_Z1),(length,p.RAMP_Z1-p.RAMP_T),
             (supported,-p.RAMP_SEAT_DEPTH),(0,-p.RAMP_SEAT_DEPTH)]
    ramp=yz_prism(-p.RAMP_W/2,p.RAMP_W/2,surface)
    rail=[(0,0),(length,p.RAMP_Z1),(length,p.RAMP_Z1+p.RAMP_RAIL_H),
          (0,p.RAMP_RAIL_H)]
    for x0,x1 in ((-p.RAMP_W/2,-p.RAMP_INNER_W/2),
                   (p.RAMP_INNER_W/2,p.RAMP_W/2)):
        ramp+=yz_prism(x0,x1,rail)
    for x in (-p.RAMP_MOUNT_X,p.RAMP_MOUNT_X):
        ramp+=z_cylinder(x,p.RAMP_MOUNT_Y,-p.RAMP_SEAT_DEPTH,p.RAMP_MOUNT_T+p.RAMP_SEAT_DEPTH,p.RAMP_MOUNT_R)
        ramp-=z_cylinder(x,p.RAMP_MOUNT_Y,-p.RAMP_SEAT_DEPTH,p.RAMP_MOUNT_T+p.RAMP_SEAT_DEPTH,p.M4_BORE/2)
        ramp-=top_countersink(x,p.RAMP_MOUNT_Y,p.RAMP_MOUNT_T,p.CSK_HEAD_MAX_H,p.M4_BORE,p.CSK_RECESS_D)
    span=p.RAMP_MOUNT_X+p.RAMP_MOUNT_R+p.RAMP_SEAT_CLEARANCE
    for y0,y1,end in p.RAMP_SEAT_LANDS:
        lo,hi=y0-p.RAMP_SEAT_GROOVE_CLEAR,y1+p.RAMP_SEAT_GROOVE_CLEAR
        roof=p.RAMP_SEAT_GROOVE_CLEAR
        if end:
            raised=roof+(hi-lo)*p.RAMP_SEAT_END_ROOF_SLOPE
            ramp-=yz_prism(-span,span,[(lo,-p.RAMP_SEAT_DEPTH),
                (hi,-p.RAMP_SEAT_DEPTH),(hi,raised if end>0 else roof),
                (lo,raised if end<0 else roof)])
        else:
            ramp-=bounded_box(-span,span,lo,hi,-p.RAMP_SEAT_DEPTH,roof)
    return ramp

def seat_cutter():
    """Local deck rebate, with explicit lateral assembly clearance."""
    c=p.RAMP_SEAT_CLEARANCE
    end=p.RAMP_SUPPORT_END-p.RAMP_Y0+p.RAMP_SEAT_DEPTH/p.RAMP_UNDERSIDE_SLOPE+c
    pocket=bounded_box(-p.RAMP_W/2-c,p.RAMP_W/2+c,-c,end,-p.RAMP_SEAT_DEPTH,0)
    for x in (-p.RAMP_MOUNT_X,p.RAMP_MOUNT_X):
        pocket+=z_cylinder(x,p.RAMP_MOUNT_Y,-p.RAMP_SEAT_DEPTH,p.RAMP_SEAT_DEPTH,p.RAMP_MOUNT_R+c)
    span=p.RAMP_MOUNT_X+p.RAMP_MOUNT_R+c
    # The right clearance crosses the center seam by only 0.15 mm. Open
    # this clearance strip through the deck instead of leaving a fragile
    # blind-rebate roof attached to the edge of the neighboring tile.
    lip=bounded_box(p.RAMP_W/2+p.DECK_SEAM/2,p.RAMP_W/2+c,
                    -c,end,-p.DECK_T,0)
    pocket+=lip
    for y0,y1,_ in p.RAMP_SEAT_LANDS:
        pocket-=bounded_box(-span,span,y0,y1,-p.DECK_T,0)
    return pocket
