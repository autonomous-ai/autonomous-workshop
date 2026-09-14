"""Deterministic BRep balance/contact/clearance audit; no physical-test claim.

Builds the current source once and samples the specified constrained quasistatic
seat. The marble is free: floor and rear-wall contact plus nonnegative reaction
forces establish its seat. No fixed joint attaches it to the rocker.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from build123d import Axis,CenterOf,Pos,Sphere
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import params as p
from parts.jackpot_rocker import build_rocker
from parts.jackpot_trim import build_trim
from parts.jackpot_frame import build_frame
from parts.landing_ramp import build_ramp
from parts.wooden_axle import build_axle
from parts.purchased_hardware import screw_csk,nut
from parts.jackpot_axle_cap import build as build_cap
from assemblies.hardware import hardware_parts


def volume(shape):
    if shape is None: return 0.0
    if hasattr(shape,'volume'): return float(shape.volume)
    return sum(float(s.volume) for s in shape)


def placed_moving_parts():
    return {
        'rocker':(build_rocker(),p.PLA_DENSITY_G_MM3),
        'trim':(Pos(p.FLAG_ARM_X,p.TRIM_Y,p.TRIM_Z)*build_trim(),p.PLA_DENSITY_G_MM3),
        'trim_bolt':(Pos(p.FLAG_ARM_X,p.TRIM_Y,p.ROCKER_PRINT_BASE_Z-p.TRIM_H)
                     *screw_csk().rotate(Axis.X,180),p.STEEL_DENSITY_G_MM3),
        'trim_nut':(Pos(p.FLAG_ARM_X,p.TRIM_Y,p.ROCKER_PRINT_BASE_Z+p.FLAG_ARM_T)
                    *nut(),p.STEEL_DENSITY_G_MM3),
    }


def audit(check_collisions=True):
    moving=placed_moving_parts()
    records={}
    for name,(shape,density) in moving.items():
        # The nut's equivalent NURBS surfaces need adaptive integration;
        # use it consistently for every moving mass and its centroid.
        props=GProp_GProps()
        error=BRepGProp.VolumeProperties_s(shape.wrapped,props,1e-12,False,False)
        center=props.CentreOfMass()
        records[name]={'volume_mm3':props.Mass(),'mass_g':props.Mass()*density,
                       'com_axis_mm':[center.X(),center.Y(),center.Z()],
                       'default_nonadaptive_volume_mm3':shape.volume,
                       'adaptive_reported_relative_error':error}
    mass=sum(x['mass_g'] for x in records.values())
    moments=np.sum([np.array(x['com_axis_mm'])*x['mass_g'] for x in records.values()],axis=0)
    radius=p.MARBLE_MAX_D/2
    floor_slope=(p.BUCKET_FLOOR_Z[1]-p.BUCKET_FLOOR_Z[0])/(p.BUCKET_Y[1]-p.BUCKET_WALL-p.BUCKET_Y[0])
    ball_y=p.BUCKET_Y[1]-p.BUCKET_WALL-radius
    ball_z=p.BUCKET_FLOOR_Z[0]+floor_slope*(ball_y-p.BUCKET_Y[0])+radius*math.sqrt(1+floor_slope**2)
    ball=Pos(0,ball_y,ball_z)*Sphere(radius)
    normal_floor=np.array([-floor_slope,1.0])/math.sqrt(1+floor_slope**2)
    normal_back=np.array([-1.0,0.0])
    fixed={'frame':build_frame(),'axle':build_axle(),
           'ramp':Pos(0,p.RAMP_Y0-p.JACKPOT_AXIS[1],-p.JACKPOT_AXIS[2])*build_ramp()}
    fixed['left_cap']=Pos(p.CAP_LEFT_X,0,0)*build_cap()
    fixed['right_cap']=Pos(p.CAP_RIGHT_X,0,0)*build_cap().rotate(Axis.Z,180)
    to_axis=Pos(*(-v for v in p.JACKPOT_AXIS))
    for name,shape,_ in hardware_parts():
        if name.startswith(('jackpot_','ramp_')): fixed[name]=to_axis*shape
    samples=[]
    max_overlap=0.0
    contacts={'marble_rocker_overlap_mm3':volume(ball.intersect(moving['rocker'][0])),
              'marble_rocker_distance_mm':ball.distance_to(moving['rocker'][0])}
    for angle in np.linspace(0,p.JACKPOT_TRAVEL_DEG,57):
        alpha=math.radians(p.INCLINE_DEG+float(angle))
        c,s=math.cos(alpha),math.sin(alpha)
        empty=-9.80665*(moments[1]*c-moments[2]*s)/1000
        ball_torque=-p.MARBLE_MIN_G*9.80665*(ball_y*c-ball_z*s)/1000
        rotation=np.array([[c,-s],[s,c]])
        reactions=np.linalg.solve(np.column_stack((rotation@normal_floor,rotation@normal_back)),np.array([0,1.0]))
        row={'rocker_angle_deg':float(angle),'empty_restore_mNm':empty,
             'loaded_tip_mNm':-(empty+ball_torque),
             'floor_reaction_per_weight':float(reactions[0]),
             'back_reaction_per_weight':float(reactions[1])}
        if check_collisions:
            collisions={}
            min_deck=1e9
            collision_movers={name:shape for name,(shape,_) in moving.items()}
            collision_movers['free_marble']=ball
            for name,shape in collision_movers.items():
                posed=shape.rotate(Axis.X,float(angle))
                min_deck=min(min_deck,posed.bounding_box().min.Z+p.JACKPOT_AXIS[2])
                for obstacle,solid in fixed.items():
                    overlap=volume(posed.intersect(solid))
                    max_overlap=max(max_overlap,overlap)
                    if overlap>0.001: collisions[f'{name}/{obstacle}']=overlap
            row['deck_clearance_mm']=min_deck
            row['collisions_mm3']=collisions
        samples.append(row)
    bounds={
        'empty_restore_mNm':[min(x['empty_restore_mNm'] for x in samples),max(x['empty_restore_mNm'] for x in samples)],
        'loaded_tip_min_mNm':min(x['loaded_tip_mNm'] for x in samples),
        'max_fixed_overlap_mm3':max_overlap,
        'minimum_reaction_per_weight':min(min(x['floor_reaction_per_weight'],x['back_reaction_per_weight']) for x in samples),
    }
    if check_collisions: bounds['minimum_deck_clearance_mm']=min(x['deck_clearance_mm'] for x in samples)
    checks={
        'empty_restoring_full_range':bounds['empty_restore_mNm'][0]>=0.05 and bounds['empty_restore_mNm'][1]<=0.40,
        'light_marble_tips_full_range':bounds['loaded_tip_min_mNm']>=0.55,
        'free_marble_seat_supported':bounds['minimum_reaction_per_weight']>=0 and contacts['marble_rocker_distance_mm']<1e-6 and contacts['marble_rocker_overlap_mm3']<0.001,
        'fixed_solids_clear':max_overlap<=0.001 if check_collisions else None,
        'deck_clear':bounds.get('minimum_deck_clearance_mm',1)>0,
    }
    stops={}
    for name,angle in (('empty_rest',0.5),('loaded_limit',p.JACKPOT_TRAVEL_DEG-0.5)):
        stops[name]=volume(moving['rocker'][0].rotate(Axis.X,angle).intersect(fixed['frame']))
    checks['both_hard_stops_block_overtravel']=all(v>0.001 for v in stops.values())
    axle_stops={}
    for name,dx in (('left',-0.5),('right',0.5)):
        axle_stops[name]=volume((Pos(dx,0,0)*fixed['axle']).intersect(fixed[name+'_cap']))
    checks['axle_ends_blocked_by_installed_caps']=all(v>0.001 for v in axle_stops.values())
    checks={k:bool(v) if v is not None else None for k,v in checks.items()}
    return {'kind':'cratercade.quasistatic-jackpot-audit','schema_version':1,
            'physical_test':False,'source_brep_measurement':True,'mass_model':'solid PLA and steel, assumed densities; friction excluded',
            'mass_integration':'BRepGProp adaptive volume and centroid, epsilon 1e-12; reported error is not a total-error bound',
            'trim_y_mm':p.TRIM_Y,'parts':records,'total_moving_mass_g':mass,
            'moving_com_axis_mm':list(moments/mass),'marble_seat_axis_mm':[0,ball_y,ball_z],
            'marble_mass_g':p.MARBLE_MIN_G,'contacts':contacts,'bounds':bounds,'checks':checks,'samples':samples,
            'overtravel_overlap_mm3':stops,'axle_end_escape_overlap_mm3':axle_stops,
            'fixed_obstacles':list(fixed),'retention_limit':'Cap fasteners and real thread engagement need the separate retention/specification audit; this is an installed-geometry check.',
            'pass':all(v is True for v in checks.values())}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--no-collisions',action='store_true')
    parser.add_argument('--output',type=Path,default=Path(__file__).with_suffix('.json'))
    args=parser.parse_args()
    result=audit(not args.no_collisions)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('pass','bounds','checks','contacts','total_moving_mass_g','moving_com_axis_mm')}))
    raise SystemExit(0 if result['pass'] else 1)
