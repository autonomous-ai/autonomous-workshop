"""Exact CAD states of a legal five-player round; transfers represent hands, not actuation."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build123d import Compound, Pos, Rot, export_stl
from crosscurrent_lib import *
root=Path(__file__).resolve().parents[1]
base=build_base(); inner=build_inner(); outer=build_outer()
boats={i:build_boat(i) for i in range(1,6)}
# Selected boats and directions: 1b +1, 2b +1, 3a +1, 4a -1, 5a +1.
# Starting-ring totals: inner +1, outer +2. After scoring, cross and drift +1.
selected={(1,'b'),(2,'b'),(3,'a'),(4,'a'),(5,'a')}
initial_levels={}; occupied={}
for identity,letter,ring,h in DEMO_BOATS:
    initial_levels[(identity,letter)]=occupied.get((ring,h),0)
    occupied[(ring,h)]=occupied.get((ring,h),0)+1
final_locations={}; final_levels={}; occupied={}
for identity,letter,ring,h in DEMO_BOATS:
    scoring_h=(h+(1 if ring==0 else 2))%6
    destination=(1-ring,(scoring_h+1)%6) if (identity,letter) in selected else (ring,scoring_h)
    final_locations[(identity,letter)]=destination
    final_levels[(identity,letter)]=occupied.get(destination,0)
    occupied[destination]=occupied.get(destination,0)+1
for index in range(16):
    fraction=min(index/5,1)
    a=60*fraction; b=120*fraction
    shapes=[base,Pos(0,0,RING_Z)*Rot(0,0,-a)*inner,Pos(0,0,RING_Z)*Rot(0,0,-b)*outer]
    for identity,letter,ring,h in DEMO_BOATS:
        key=(identity,letter); angle=a if ring==0 else b
        x,y=polar(INNER_BERTH_R if ring==0 else OUTER_BERTH_R,h,angle)
        z=BOAT_Z+initial_levels[key]*STACK_PITCH
        if key in selected and index>5:
            dest_ring,dest_h=final_locations[key]
            dx,dy=polar(INNER_BERTH_R if dest_ring==0 else OUTER_BERTH_R,dest_h)
            dz=BOAT_Z+final_levels[key]*STACK_PITCH
            lift=60+initial_levels[key]*STACK_PITCH
            if index<=8:
                z=z+(lift-z)*(index-5)/3
            elif index<=12:
                f=(index-8)/4; x=x+(dx-x)*f; y=y+(dy-y)*f; z=lift
            else:
                x,y=dx,dy; z=lift+(dz-lift)*(index-12)/3
        shapes.append(Pos(x,y,z)*Rot(0,0,-angle)*boats[identity])
    export_stl(Compound(children=shapes),root/'measure'/'states'/f'{index:02d}.stl')
    print(f'state {index:02d}',flush=True)
