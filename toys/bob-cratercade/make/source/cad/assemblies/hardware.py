"""Catalog fastener placements; positions also define proof-board through holes."""
from build123d import Axis,Pos,Color
import params as p
from parts.purchased_hardware import screw_csk,screw_socket,nut


def deck_fasteners():
    rows=[]
    for side,(x,y) in p.FLIPPER_PIVOTS.items():
        rows.append((f'flipper_{side}_pivot',x,y,p.FLIPPER_SCREW_UNDER_HEAD_Z,'socket'))
    guard_index=0
    for side,(px,py) in p.FLIPPER_PIVOTS.items():
        mounts=p.FLIPPER_GUARD_MOUNTS if side=='left' else p.FLIPPER_RIGHT_GUARD_MOUNTS
        for dx,dy in mounts:
            rows.append((f'flipper_guard_{guard_index}',px+dx*(1 if side=='left' else -1),py+dy,p.FLIPPER_GUARD_SCREW_HEAD_Z,'csk'))
            guard_index+=1
    for index,(x,y) in enumerate(p.LAUNCH_MOUNT_POINTS):
        rows.append((f'launcher_root_{index}',x,y,p.LAUNCH_MOUNT_Z,'csk'))
    rows.append(('launcher_root_2',p.LAUNCH_BAND_X,p.LAUNCH_ANCHOR_Y[0]+p.LAUNCH_ANCHOR_BOLT_OFFSET,
                 p.LAUNCH_POCKET_FLOOR+p.LAUNCH_ANCHOR_T,'csk'))
    for index,(x,y) in enumerate(p.FRAME_BOLT_CENTERS):
        rows.append((f'jackpot_frame_{index}',x+p.JACKPOT_AXIS[0],y+p.JACKPOT_AXIS[1],p.FRAME_BASE_T,'csk'))
    for index,x in enumerate((-p.RAMP_MOUNT_X,p.RAMP_MOUNT_X)):
        rows.append((f'ramp_root_{index}',x+p.JACKPOT_AXIS[0],p.RAMP_Y0+p.RAMP_MOUNT_Y,p.RAMP_MOUNT_T,'csk'))
    return rows


def hardware_parts():
    items=[]
    steel=Color(0.64,0.67,0.70)
    for label,x,y,z,kind in deck_fasteners():
        bolt=screw_socket() if kind=='socket' else screw_csk()
        items.append((label+'_bolt',Pos(x,y,z)*bolt,steel))
        items.append((label+'_nut',Pos(x,y,-p.DECK_T-p.NUT_T)*nut(),steel))
    cap_rows=[]
    for suffix,(x,y) in zip(('rear','front'),p.LAUNCH_GUIDE_BOLTS):
        cap_rows.append((f'launcher_guide_{suffix}',x,y,p.LAUNCH_GUIDE_CAP_TOP,p.LAUNCH_GUIDE_NUT_TOP-p.NUT_T,30))
    for suffix,(x,y) in zip(('front','rear'),p.LAUNCH_GUARD_BOLTS):
        cap_rows.append((f'launcher_guard_{suffix}',x,y,p.LAUNCH_GUARD_BOTTOM+p.LAUNCH_GUARD_T,p.LAUNCH_GUARD_NUT_TOP-p.NUT_T,0))
    for label,x,y,z,nut_z,nut_angle in cap_rows:
        items.append((label+'_bolt',Pos(x,y,z)*screw_csk(),steel))
        items.append((label+'_nut',Pos(x,y,nut_z)*nut().rotate(Axis.Z,nut_angle),steel))
    origin=Pos(*p.JACKPOT_AXIS)
    for side,outer_x,nut_x,direction in (
        ('left',p.CAP_LEFT_X,p.FRAME_TOWER_X_RANGES[0][1],1),
        ('right',p.CAP_RIGHT_X,p.FRAME_TOWER_X_RANGES[1][0],-1),
    ):
        for index,y in enumerate((-p.CAP_BOLT_Y,p.CAP_BOLT_Y)):
            items.append((f'jackpot_{side}_cap_{index}_bolt',origin*Pos(outer_x,y,p.CAP_BOLT_Z)*screw_csk().rotate(Axis.Y,-90*direction),steel))
            items.append((f'jackpot_{side}_cap_{index}_nut',origin*Pos(nut_x,y,p.CAP_BOLT_Z)*nut().rotate(Axis.Y,90*direction),steel))
    return items
