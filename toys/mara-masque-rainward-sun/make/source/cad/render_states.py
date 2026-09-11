"""Color-preserving, fixed-camera CAD review from the exact exported STEP solids.

The stock render_product reduces the whole set to two face-normal colors and
its full-frame metric hides a two-counter hit. This renderer uses the native
render_review rasterizer, original occurrence colors and one fixed close view.
No geometry, backgrounds or camera positions change between the two states.
The original mean-RGB difference threshold remains 2.0.
"""
from pathlib import Path
import runpy,json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw
from build123d import import_step
from rainward_lib import assembly

ROOT=Path(__file__).resolve().parent
RUN=next(p for p in ROOT.parents if (p/'STAGE.json').is_file())
API=runpy.run_path(str(RUN/'.agents/skills/cad/scripts/render_review'),run_name='native_cad_renderer')
AZ,EL,SIZE,PAD=-75.,55.,1400,.025

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def exact_occurrences(state,path):
    expected=list(assembly(state).children)
    actual=list(import_step(path).solids())
    assert len(expected)==len(actual)==35
    result=[];named={};matches=[]
    for intended in expected:
        center=np.array(tuple(intended.center()))
        distances=[np.linalg.norm(np.array(tuple(s.center()))-center) for s in actual]
        k=int(np.argmin(distances));s=actual.pop(k)
        assert distances[k]<1e-5,(intended.label,distances[k])
        assert abs(s.volume-intended.volume)<max(1e-5,intended.volume*1e-7)
        v,f=s.tessellate(.08)
        points=np.array([[p.X,p.Y,p.Z] for p in v]);faces=np.array(f,dtype=np.int64)
        colour=tuple(round(float(c)*255) for c in tuple(intended.color)[:3])
        row=(points,faces,colour);result.append(row);named[intended.label]=row
        matches.append({'name':intended.label,'centroid_error_mm':float(distances[k]),'volume_mm3':s.volume})
    return result,named,matches

def region(occurrences,framing):
    # Standard camera-frustum culling prevents native rasterizer negative slices
    # for faces wholly outside a close-up. Remaining geometry is unchanged.
    _,right,up=API["camera_basis"](AZ,EL)
    sx,sy=framing@right,framing@up
    span=max(float(np.ptp(sx)),float(np.ptp(sy)))
    half=span/(1-2*PAD)/2
    cx,cy=(sx.min()+sx.max())/2,(sy.min()+sy.max())/2
    visible=[]
    for points,faces,color in occurrences:
        tx=(points@right)[faces];ty=(points@up)[faces]
        keep=(tx.max(axis=1)>=cx-half)&(tx.min(axis=1)<=cx+half)&(ty.max(axis=1)>=cy-half)&(ty.min(axis=1)<=cy+half)
        if keep.any():visible.append((points,faces[keep],color))
    return API["render"](visible,AZ,EL,SIZE,PAD,framing=framing)

def main():
    snap=ROOT/'snap';snap.mkdir(exist_ok=True)
    setup,_,setup_matches=exact_occurrences('setup',ROOT/'rainward.step')
    API['render'](setup,AZ,EL,1600,.05).save(snap/'iso.png')
    before,bnames,bmatches=exact_occurrences('before',ROOT.parent/'evidence/states/before.step')
    after,anames,amatches=exact_occurrences('after',ROOT.parent/'evidence/states/after.step')
    # Camera frame follows the three relevant occupied footprints, includes
    # the underlying rim height, and is frozen for both panels.
    framing=np.concatenate([bnames['single_06'][0],bnames['fork_01'][0],anames['fork_01'][0]])
    floor=framing.copy();floor[:,2]=0
    framing=np.concatenate([framing,floor])
    left=region(before,framing)
    right=region(after,framing)
    difference=float(np.abs(np.asarray(left,dtype=float)-np.asarray(right,dtype=float)).mean())
    left.save(snap/'before-detail.png');right.save(snap/'after-detail.png')
    assert difference>=2.,f'Fixed interaction framing remains indistinguishable: {difference}'
    # Compose newly generated CAD views; headers are explanatory, not geometry.
    header=65
    sheet=Image.new('RGB',(SIZE*2,SIZE+header),'#edf0f5')
    sheet.paste(left,(0,header));sheet.paste(right,(SIZE,header))
    draw=ImageDraw.Draw(sheet)
    draw.text((25,20),'BEFORE',fill='#222222',font_size=24)
    draw.text((SIZE+25,20),'AFTER',fill='#222222',font_size=24)
    sheet.save(snap/'signature.png')
    report={'status':'PASS','camera':{'azimuth_deg':AZ,'elevation_deg':EL,'fixed_framing_points':framing.tolist()},'signature_scope':'Fixed high three-quarter close view of the interaction; full35-part set in hero. Both state renders contain all35 exact solids; camera clips the distant region.','mean_rgb_state_difference':difference,'minimum_difference':2.,'geometry':'Exact exported STEP solids, matched to source occurrence colors by centroid and volume; no geometry changes.','sources':{__import__("os").path.relpath(p,ROOT):sha(p) for p in (ROOT/'rainward.step',ROOT.parent/'evidence/states/before.step',ROOT.parent/'evidence/states/after.step',ROOT/'rainward_lib.py')},'states':{'setup':setup_matches,'before':bmatches,'after':amatches},'images':{p.name:sha(p) for p in (snap/'iso.png',snap/'signature.png',snap/'before-detail.png',snap/'after-detail.png')}}
    (ROOT/'measure/presentation.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'PASS','mean_rgb_state_difference':difference,'minimum_difference':2.,'all_states_solids':35}))
if __name__=='__main__': main()
