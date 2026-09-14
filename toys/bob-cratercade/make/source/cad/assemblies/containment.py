"""Captured PET canopy and its canonical, independently removable cell joints.

All shapes use deck coordinates. Sheet stock is explicitly non-printed.
Deck/perimeter integration consumes deck_mounts and wall_cutters; no cycle with
playfield or the root hardware registry is introduced here.
"""
from build123d import Color,Plane,Pos,Rot
import params as p
from parts import canopy_frame,canopy_cap,canopy_post,canopy_post_cap,canopy_rear_adapter
from parts import canopy_roof_splice,canopy_end_join,canopy_sheet
from parts.purchased_hardware import screw_csk,screw_socket,nut
from assemblies import access_doors


def _side(shape,right=False):
    return Pos(p.DECK_W,0,0)*shape.mirror(Plane.YZ) if right else shape


def _item(label,shape,color=None,printed=True,role='stationary'):
    shape.label=label
    return label,shape,color or p.CANOPY_PRINT_COLOR,{
        'role':role,'printable':printed,'removable':True,
        'material':'printed PETG' if printed else 'clear PET cut sheet'}


def _lift_upper_rows(rows):
    """Move complete upper modules together, including every posed door item.

    Rooted posts, mullions and wall PET extend in their builders. Root and rear
    adapter joints keep their original placement. Labels are the assembly's
    existing canonical occurrence identities; no hardware is omitted.
    """
    out=[]
    for label,shape,color,metadata in rows:
        upper=(label.startswith(('canopy_roof_', 'canopy_post_cap_')) or
               (label.startswith('canopy_post_') and '_cross_' in label))
        if upper:
            shape=Pos(0,0,p.CANOPY_ROOF_LIFT)*shape
            shape.label=label
        out.append((label,shape,color,metadata))
    return out


def _door_states(service, door_states):
    if service and door_states is None:
        return {name: {"angle": 120, "latch_angles": [90, 90]} for name in ("load", "reset")}
    return door_states


def components(service=False,include_apron=True,door_states=None):
    """Closed or explicitly posed captive doors; no ordinary-access omissions."""
    door_states=_door_states(service,door_states)
    out=[]
    for right in (False,True):
        side='right' if right else 'left'
        for index,y in enumerate(p.CANOPY_POST_Y):
            end='front' if index==0 else 'rear' if index==3 else 'none'
            post=canopy_post.build(index==3,end)
            out.append(_item(f'canopy_post_{side}_{index}',Pos(0,y,0)*_side(post,right)))
            if index==3:
                out.append(_item(f'canopy_post_{side}_{index}_adapter',Pos(0,y,0)*_side(canopy_rear_adapter.build(),right)))
            out.append(_item(f'canopy_post_cap_{side}_{index}',Pos(0,y,0)*_side(canopy_post_cap.build(),right)))
        for index,(ya,yb) in enumerate(zip(p.CANOPY_POST_Y[:-1],p.CANOPY_POST_Y[1:])):
            start=ya+p.CANOPY_POST_INNER_Y[1]+p.CANOPY_SIDE_SHEET_END_CLEARANCE
            end=yb+p.CANOPY_POST_INNER_Y[0]-p.CANOPY_SIDE_SHEET_END_CLEARANCE
            out.append(_item(f'canopy_side_pet_{side}_{index}',Pos(0,start,0)*_side(canopy_sheet.side(end-start),right),Color(*p.CANOPY_PET_COLOR),False))
    for rear in (False,True):
        label='rear' if rear else 'front'; y=p.CANOPY_POST_Y[-1 if rear else 0]
        out.append(_item(f'canopy_end_join_{label}',Pos(p.CANOPY_CELL_W,y,0)*canopy_end_join.build(rear)))
        for half in (0,1):
            out.append(_item(f'canopy_end_pet_{label}_{half}',Pos(0,y,0)*canopy_sheet.end(half,rear),Color(*p.CANOPY_PET_COLOR),False))
    for index,y in enumerate(p.CANOPY_ROW_Y[1:]):
        out.append(_item(f'canopy_roof_splice_{index}',Pos(p.CANOPY_CELL_W,y,0)*canopy_roof_splice.build()))
    for row,y in enumerate(p.CANOPY_ROW_Y):
        for column in (0,1):
            if (column,row) in access_doors.CELLS:
                out.extend(access_doors.components(column,row,door_states))
                continue
            pose=Pos(column*p.CANOPY_CELL_W,y,0)
            for name,shape,color,printed in (
                ('frame',canopy_frame.build(),p.CANOPY_PRINT_COLOR,True),
                ('cap',canopy_cap.build(),p.CANOPY_CAP_COLOR,True),
                ('pet',canopy_sheet.roof(),Color(*p.CANOPY_PET_COLOR),False)):
                out.append(_item(f'canopy_roof_{column}_{row}_{name}',pose*shape,color,printed))
    if include_apron:
        from parts import apron_shell
        for side in ("left","right"):
            out.append(_item(f"apron_{side}",apron_shell.build(side),p.CANOPY_CAP_COLOR))
    return _lift_upper_rows(out)


def deck_mounts(include_apron=True):
    rows=[]
    for right in (False,True):
        for index,y in enumerate(p.CANOPY_POST_Y):
            y+=canopy_post.root_offset(index==3)
            rows.append({'part':f'canopy_post_{"right" if right else "left"}_{index}'+('_adapter' if index==3 else ''),
                         'x':p.DECK_W-p.CANOPY_POST_ROOT_X if right else p.CANOPY_POST_ROOT_X,
                         'y':y,'head_z':p.CANOPY_ROOT_RING_Z+p.CANOPY_ROOT_RING_T,
                         'nut_bottom_z':-p.DECK_T-p.NUT_T,'nut_rotation_z':0.0,
                         'bore_d':p.M4_BORE,'screw':'M4x25_socket','nut':'ISO4035_M4'})
    for side in (("left","right") if include_apron else ()):
        for index,(x,y) in enumerate(p.APRON_MOUNTS[side]):
            rows.append({"part":f"apron_{side}_{index}","x":x,"y":y,"head_z":p.APRON_ROOT_LAND_Z,
                         "nut_bottom_z":-p.DECK_T-p.NUT_T,"nut_rotation_z":0.0,"bore_d":p.M4_BORE,
                         "screw":"M4x16_countersunk","nut":"ISO4035_M4"})
    return rows


def wall_cutters():
    return [_side(canopy_post.root_cutter(row['y']),row['x']>p.DECK_W/2) for row in deck_mounts() if row['part'].startswith('canopy_post')]


def deck_cutters():
    """Through bores are given by deck_mounts; root needs no extra deck cavity."""
    return []


def hardware_components(service=False,include_roots=True,include_apron=True,door_states=None):
    """Exact catalog solids, suitable for integration once (avoid duplicate roots)."""
    door_states=_door_states(service,door_states)
    out=[]; steel=Color(.64,.67,.70)
    def add(label,shape):
        shape.label=label
        out.append((label,shape,steel,{'role':'fastener','printable':False,'removable':True}))
    if include_roots:
        for row in deck_mounts(include_apron):
            add(row['part']+'_root_bolt',Pos(row['x'],row['y'],row['head_z'])*(screw_socket() if row['screw']=='M4x25_socket' else screw_csk()))
            add(row['part']+'_root_nut',Pos(row['x'],row['y'],row['nut_bottom_z'])*nut())
    for right in (False,True):
        for index,y in enumerate(p.CANOPY_POST_Y):
            label=f'canopy_post_{"right" if right else "left"}_{index}_cross'
            add(label+'_bolt',Pos(0,y,0)*_side(Pos(p.CANOPY_POST_OUTER_X[0],0,p.CANOPY_POST_CROSS_BOLT_Z)*Rot(0,-90,0)*screw_csk(),right))
            add(label+'_nut',Pos(0,y,0)*_side(Pos(p.CANOPY_POST_NUT_X,0,p.CANOPY_POST_CROSS_BOLT_Z)*Rot(0,90,0)*nut(),right))
    for right in (False,True):
        label=f'canopy_rear_joint_{"right" if right else "left"}'
        y=p.CANOPY_POST_Y[-1]; z=p.CANOPY_REAR_JOINT_Z
        add(label+'_bolt',Pos(0,y,0)*_side(Pos(p.CANOPY_POST_OUTER_X[0],0,z)*Rot(0,-90,0)*screw_csk(),right))
        add(label+'_nut',Pos(0,y,0)*_side(Pos(p.CANOPY_POST_NUT_X,0,z)*Rot(0,90,0)*nut(),right))
    for row,y in enumerate(p.CANOPY_ROW_Y):
        for column in (0,1):
            if (column,row) in access_doors.CELLS:
                out.extend(access_doors.hardware_components(column,row,door_states))
                continue
            ox=column*p.CANOPY_CELL_W
            for name,points,head,nut_z in (
                ('mount',canopy_frame.bolt_points(),p.CANOPY_FRAME_TOP,p.CANOPY_POST_TOP_Z-p.NUT_T),
                ('clamp',canopy_frame.clamp_points(),p.CANOPY_CAP_BOTTOM+p.CANOPY_CAP_T,p.CANOPY_FRAME_BOTTOM-p.NUT_T)):
                for i,(x,v) in enumerate(points):
                    label=f'canopy_roof_{column}_{row}_{name}_{i}'
                    add(label+'_bolt',Pos(ox+x,y+v,head)*screw_csk())
                    add(label+'_nut',Pos(ox+x,y+v,nut_z)*nut())
    return _lift_upper_rows(out)


def cut_list():
    height=p.CANOPY_SIDE_SHEET_TOP+p.CANOPY_ROOF_LIFT-p.CANOPY_SIDE_SHEET_BOTTOM
    side_length=p.CANOPY_CELL_L+p.CANOPY_POST_INNER_Y[0]-p.CANOPY_POST_INNER_Y[1]-2*p.CANOPY_SIDE_SHEET_END_CLEARANCE
    end_width=p.CANOPY_CELL_W+p.CANOPY_END_JOIN_SLOT_X[1]-(p.CANOPY_POST_OUTER_X[1]-p.CANOPY_SLOT_DEPTH)-2*p.CANOPY_SIDE_SHEET_END_CLEARANCE
    return {'material':'clear PET','thickness_range_mm':[.2,p.CANOPY_PET_MAX_T],
            'model_thickness_mm':p.CANOPY_PET_T,'roof':{'quantity':4,'blank_mm':[p.CANOPY_ROOF_SHEET_W,p.CANOPY_ROOF_SHEET_L],
             'corner_notches_mm':[p.CANOPY_ROOF_SHEET_CORNER,p.CANOPY_ROOF_SHEET_CORNER],
             'mid_edge_notches_mm':[2*p.CANOPY_ROOF_SHEET_NOTCH_HALF,p.CANOPY_ROOF_SHEET_NOTCH_END-(p.CANOPY_CELL_W-p.CANOPY_ROOF_SHEET_W)/2]},
            'access_roof':{'quantity':2,'base':'roof blank and original corner/mid-edge notches',
                'additional_open_edge_notches_local_mm':[[130,160.1,c-9.5,c+9.5] for c in (30,114)],
                'orientation':'Notches toward board centre; mirror the loading panel'},
            'side':{'quantity':6,'blank_mm':[side_length,height]},'end':{'quantity':4,'blank_mm':[end_width,height]}}
