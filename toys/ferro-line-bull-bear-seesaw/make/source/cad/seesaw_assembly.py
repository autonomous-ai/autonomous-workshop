"""Placement-only assembly. Static poses are presentation, not motion evidence."""
import math
from build123d import Pos, Rot, Color
from cadgen.assembly import AssemblyHelper
from seesaw_lib import BUILDERS, COLOURS, ROLE_COLOUR, PIVOT_Z, DRIVE_H, ANGLE

def build_assembly(theta=0.0):
    assert -ANGLE<=theta<=ANGLE
    asm=AssemblyHelper("bull_bear_seesaw")
    beam_frame=Pos(0,0,PIVOT_Z)*Rot(0,-theta,0)
    q=DRIVE_H*math.sin(math.radians(theta))
    def add(role,name=None,placement=None):
        shape=BUILDERS[role]()
        if placement is not None:
            shape=placement*shape
        colour=ROLE_COLOUR[role]
        return asm.add(shape,(name or role)+"_"+colour,color=Color(*COLOURS[colour]))
    add('base')
    add('stand')
    add('mount_pin',placement=Pos(0,10.4,13))
    add('retainer','base_key',Pos(0,21,13))
    add('main_pin',placement=Pos(0,0,PIVOT_Z))
    add('retainer','axle_key',Pos(0,21,PIVOT_Z))
    for role in ['beam','bull_body','bear_body','mouth_back','tear_back','bear_face','bull_muzzle']:
        add(role,placement=beam_frame)
    add('shuttle',placement=beam_frame*Pos(q,0,0))
    add('bear_mask',placement=beam_frame*Pos(q,0,0))
    for c,animal in [(-60,'bull'),(60,'bear')]:
        add('retainer',animal+'_mount_key',beam_frame*Pos(c,10.6,0.5))
        for dx,side in ([(-27,'left'),(27,'right')] if animal=='bull' else [(-25,'left'),(25,'right')]):
            add('retainer',animal+'_'+side+'_cover_key',beam_frame*Pos(c+dx,4,55 if animal=='bull' else 61.2))
    return asm.build()
