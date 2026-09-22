"""Independent parameter/connector ledger. No geometry rebuild or motion sweep."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import params as p
from head_faces import FACE_POCKET_WIDTH,FACE_POCKET_LENGTH
from mintfin_lib import female_profile
assert len(p.BODY_WIDTHS)==len(p.BODY_HEIGHTS)==7
assert p.FIRST_JOINT_X+7*p.JOINT_PITCH+20==180
assert p.STEM_WIDTH>=3.2 and p.STEM_HEIGHT>=2
for c in(.35,.45,.55):
    profile=female_profile(c)
    assert all(profile[i][1]<=profile[i+1][1] for i in range(len(profile)-1))
    assert abs(profile[-1][0]-p.PIN_CAP_R-c)<1e-9
    assert p.BEARING_R-max(r for r,z in profile)>=2.0
    assert 2*min(r for r,z in profile)<2*p.PIN_CAP_R
    assert 2*profile[-1][0]*math.sin(math.radians(p.OPENING_DEG/2))<2*p.PIN_CAP_R
q=p.HEAD_FACE_PARAMS
assert math.isclose((FACE_POCKET_WIDTH-q['face_width'])/2,.15,abs_tol=1e-9)
assert math.isclose((FACE_POCKET_LENGTH-q['face_length'])/2,.25,abs_tol=1e-9)
assert math.isclose(q['catch_projection']-q['side_clearance'],.20,abs_tol=1e-9)
assert q['arm_root_x']-q['arm_tip_x']==12
assert q['arm_width']>=1.2 and q['arm_slot']>=.8
assert q['horn_x']-q['horn_base_radius']>=22.2
print('PASS: chain length180;8 coaxial joint datums;positive coupon gaps and retaining overlap;face socket derives from20x28 plate;two12x1.2mm XY arms;horn/face envelope clear.')
print('Motion and physical release unverified; this ledger is not an insertion or retention sweep.')
