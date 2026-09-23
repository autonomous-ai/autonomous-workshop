"""Parameter-only contract audit; geometric gates own solids and collision checks."""
from math import hypot,pi,cos,exp,sqrt,radians
import params as p

def audit():
    assert len(p.TEETH)==len(p.CENTERS)==len(p.PHASES)==len(p.LOADED_PHASE_OFFSETS)==7
    assert p.M>=1.5 and min(p.TEETH)>=12
    assert min(p.TEETH)*p.M+2*p.M*p.ADDENDUM_FACTOR>=20
    assert 26<=max(p.TEETH)<=34 and 4<=p.FACE<=6
    assert .15<=p.BACKLASH_FLANK<=.25
    assert p.SPOKES in (5,6,7) and p.SPOKE_WIDTH>=2.4 and p.RIM>=2*p.M
    assert abs((p.GEAR_BORE-p.POST_DIAMETER)/2-.35)<1e-9
    assert abs(p.GEAR_Z-p.CARRIER_THICKNESS-.3)<1e-9
    assert 12<=p.AXLE_ID<=18
    assert 50<=p.SUN_TEETH*p.M+2*p.M*p.ADDENDUM_FACTOR<=70
    assert 5<=(p.BEZEL_OD-p.BEZEL_ID)/2<=8
    assert 3<=p.GEAR_Z-(p.ORANGE_Z+p.ORANGE_THICKNESS)<=5
    assert abs(p.AXLE_SHOULDER_Z+p.AXLE_SHOULDER_THICKNESS-p.ORANGE_Z)<1e-9
    assert 10<=p.STEM_DIAMETER<=14 and 95<=p.BASE_DIAMETER<=115
    previous=(0,0); teeth=p.SUN_TEETH
    for center,n in zip(p.CENTERS,p.TEETH):
        assert abs(hypot(center[0]-previous[0],center[1]-previous[1])-p.M*(n+teeth)/2)<1e-8
        previous=center;teeth=n
    radius=max(hypot(*c)+p.M*n/2+p.M*p.ADDENDUM_FACTOR for c,n in zip(p.CENTERS,p.TEETH))
    assert 2*(radius+.7)<=190
    assert 150<=2*radius<=190 and 190<=p.HUB_HEIGHT+radius<=230
    assert p.HUB_HEIGHT-radius-p.BASE_HEIGHT-.7>=8
    assert -p.WHEEL_Y-p.STEM_DIAMETER/2>=8
    entries=[((0,0),p.SUN_TEETH,'sun')]
    for sign in (1,-1):
        entries += [((sign*c[0],sign*c[1]),n,f'{sign}:{i}') for i,(c,n) in enumerate(zip(p.CENTERS,p.TEETH))]
    radii=[p.M*n/2+p.M*p.ADDENDUM_FACTOR for c,n,k in entries]
    for i,(c,_,key) in enumerate(entries):
        for j,(d,_,other) in enumerate(entries[:i]):
            samearm=key!='sun' and other!='sun' and key.split(':')[0]==other.split(':')[0]
            neighbor=(samearm and abs(int(key.split(':')[1])-int(other.split(':')[1]))==1) or (other=='sun' and key.endswith(':0'))
            if neighbor:continue
            # Two independent journals may each move0.35mm toward their neighbor.
            allowance=.7  # Main+planet play relative to fixedsun; two planet journals otherwise.
            assert hypot(c[0]-d[0],c[1]-d[1])-radii[i]-radii[j]-allowance>=(0 if other=='sun' else 2)
    return {'ideal_swept_od_mm':2*radius,'height_mm':p.HUB_HEIGHT+radius,'base_gap_after_journal_excursions_mm':p.HUB_HEIGHT-radius-p.BASE_HEIGHT-.7,'physical_operation':'unverified'}

if __name__=='__main__':
    import json
    print(json.dumps(audit(),indent=2))
