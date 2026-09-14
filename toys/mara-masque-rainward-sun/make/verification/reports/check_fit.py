"""Algebraic fit audit; generic gates own solid topology and bed contact."""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import rainward_lib as p
from shapely.geometry import Polygon,Point
from shapely.affinity import rotate,translate

def run():
    assert p.SUN_R*2+2*p.RAY_R==190
    assert p.CREST_TOP==28 and p.DECK-p.CHANNEL_DEPTH>=2
    assert (p.CUP_OD-p.CUP_ID)/2>=2 and p.CUP_FLOOR>=2
    assert math.hypot(2*p.DIE_EDGE,p.DIE_EDGE)<p.CUP_ID
    assert p.CUP_H-p.CUP_FLOOR>p.DIE_EDGE
    assert len(p.RADII)==5 and len(set(p.RADII))==5
    assert min(a-b for a,b in zip(p.RADII,p.RADII[1:]))>p.DROP_L
    assert len(p.piece_poses())==30
    polys=[Polygon(p.SINGLE),Polygon(p.FORK)]
    gap=100
    for poly in polys:
        assert poly.is_valid
        assert poly.bounds==(-6,-4,6,4)
        for other in polys:
            for r in p.RADII:
                a=translate(poly,xoff=r)
                b=rotate(translate(other,xoff=r),p.PITCH,origin=(0,0))
                gap=min(gap,a.distance(b))
                assert a.intersection(b).area<1e-9
    before=p.piece_poses('before');after=p.piece_poses('after')
    changed=[k for k in before if before[k]!=after[k]]
    assert len(changed)==2
    victim=next(k for k in changed if k.startswith('fork'))
    attacker=next(k for k in changed if k.startswith('single'))
    assert before[attacker][1]-after[attacker][1]==6
    assert after[attacker][2]==before[victim][2]
    assert math.isclose(math.dist(before[victim][2],after[victim][2]),80,abs_tol=1e-10)
    victim_poly=translate(rotate(polys[1],p.theta(1),origin=(0,0)),*before[victim][2][:2])
    deck=Point(0,0).buffer(p.SUN_R,quad_segs=1024)
    for k in range(p.RAY_COUNT):
        deck=deck.union(Point(*p.xy(p.SUN_R,k*360/p.RAY_COUNT)).buffer(p.RAY_R,quad_segs=64))
    support=deck.intersection(victim_poly)
    assert 0<support.area<victim_poly.area
    assert support.contains(victim_poly.centroid)
    bar=Point(0,0).buffer(p.BAR_R,quad_segs=512)
    dest=translate(rotate(polys[1],p.theta(1),origin=(0,0)),*after[victim][2][:2])
    assert bar.contains(dest)
    for x in (-12,0,12):
        for y in (-5,5):
            for poly in polys:
                assert bar.contains(translate(poly,xoff=x,yoff=y))
    assert p.LANES*15==360 # every lane has five positions times three layers
    result={'status':'PASS','parts':35,'sun_mm':[190,190,28],'lane_count':24,'banks':4,'points_per_bank':6,'capacity_each_point':15,'minimum_adjacent_drop_gap_mm':gap,'signature_displacement_mm':math.dist(before[victim][2],after[victim][2]),'victim_supported_fraction':support.area/victim_poly.area,'victim_centroid_supported':True,'bar_capacity_layout':30,'cup_pair_diagonal_mm':math.hypot(32,16),'scope':'Algebraic and exact planar geometry; no physical test.'}
    dest=Path(__file__).with_name('fit-audit.json');dest.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':run()
