"""One slotted crosshead with lowered tongue and printable joining ramp."""
import params as p
from features.primitives import box_at,finish
from features.prisms import yz_prism

def crosshead():
    raw=box_at(-p.CROSSHEAD_X/2,p.CROSSHEAD_X/2,p.CROSSHEAD_FRONT_Y,p.CROSSHEAD_REAR_Y,0,p.CROSSHEAD_H)
    raw=raw+box_at(*p.CROSSHEAD_TONGUE_BOUNDS)+box_at(*p.CROSSHEAD_RISER_BOUNDS)+yz_prism(p.CROSSHEAD_RAMP_YZ,*p.CROSSHEAD_RAMP_X)
    cuts=[box_at(s*p.SLOT_X0 if s>0 else -p.SLOT_X1,s*p.SLOT_X1 if s>0 else -p.SLOT_X0,*p.CROSSHEAD_SLOT_Y,p.SLOT_Z-p.SLOT_HEIGHT/2,p.SLOT_Z+p.SLOT_HEIGHT/2) for s in (-1,1)]
    return finish(raw-cuts,'slotted_shoulder_crosshead',p.BRASS)
