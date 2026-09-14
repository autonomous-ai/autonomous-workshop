"""Canonical deck interface registry; root integrates completed subassemblies."""
from build123d import Pos
import params as p
from assemblies.hardware import deck_fasteners
from assemblies.playfield import configuration_holes
from assemblies.return_system import deck_mounts,deck_cutters,rib_keepouts
from assemblies.containment import deck_mounts as enclosure_mounts
from features.primitives import top_countersink
from parts.landing_ramp import seat_cutter

def inputs():
    """All holes are board XY; all cutting solids use board coordinates."""
    returns=deck_mounts()
    holes=[(x,y) for _,x,y,_,_ in deck_fasteners()]
    holes+=configuration_holes()+[(x,y) for _,x,y,_,_ in returns]
    holes += [(row['x'],row['y']) for row in enclosure_mounts()]
    holes += [(p.LAUNCH_BAND_X,y+p.LAUNCH_ANCHOR_BOLT_OFFSET) for y in p.LAUNCH_ANCHOR_Y]
    cutters=[Pos(p.JACKPOT_AXIS[0],p.RAMP_Y0,0)*seat_cutter()]+deck_cutters()
    cutters += [top_countersink(x,y,0,p.CSK_HEAD_MAX_H,p.M4_BORE,p.CSK_RECESS_D)
                for _,x,y,head,_ in returns if head==0]
    return {'holes':list(dict.fromkeys(holes)), 'cutters':cutters,
            'rib_keepouts':rib_keepouts()}
