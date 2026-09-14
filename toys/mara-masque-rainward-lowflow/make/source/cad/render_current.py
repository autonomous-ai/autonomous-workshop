"""Exact-STEP canonical presentation for Rainward Lowflow.

Install this file as product/cad/render_current.py. Generate auxiliary scenes
ONLY with the skill's gen CLI. Each helper in product/evidence/states can be:

    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'cad'))
    from render_current import support_scene
    def gen_step():
        return support_scene('lane')

Use filenames lane.step.py, capacity.step.py and center.step.py and matching
support_scene arguments. This module does not export STEP or modify geometry.
"""
from pathlib import Path
import runpy,json,hashlib,os
from itertools import product
import numpy as np
from PIL import Image,ImageDraw
from build123d import import_step,Location,Pos,Rot,Compound
import rainward_lib as lib

ROOT=Path(__file__).resolve().parent
RUN=next(p for p in ROOT.parents if (p/'STAGE.json').is_file())
API=runpy.run_path(str(RUN/'.agents/skills/cad/scripts/render_review'),run_name='native_cad_renderer')
AZ,EL,SIZE,PAD=-75.,55.,1400,.035
NEUTRAL=(183,180,173)
PIP=(17,14,13)
SOURCES={}
IMAGES=[]
CAMERAS={}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def register(path):
    path=Path(path);SOURCES[os.path.relpath(path,ROOT)]=sha(path)

def support_scene(state):
    """Exact existing shapes at documented placements; called by gen helpers."""
    sun=lib.sun().moved(Location());sun.label='sun'
    parts=[sun]
    def counter(kind,label,lane,radius,layer=0):
        p=Pos(*lib.xy(radius,lib.theta(lane)),lib.LANE_TOP+layer*lib.DROP_H)*Rot(Z=lib.theta(lane))*lib.drop(kind)
        p.label=label;parts.append(p)
    if state=='lane':
        # Legal two friendly counters in each adjacent lane; all fixed original stations.
        counter('single','single_01',6,59)
        counter('single','single_02',7,59)
        counter('single','single_03',6,72)
        counter('single','single_04',7,72)
    elif state=='capacity':
        for j in range(15):counter('single',f'single_{j+1:02d}',6,lib.RADII[j%5],j//5)
    elif state=='center':
        counter('single','single_01',6,33)
        counter('single','single_02',7,33)
        for i,(x,y) in enumerate(((-12,-5),(0,-5),(12,-5)),1):
            p=Pos(x,y,lib.BAR_TOP)*lib.drop('fork');p.label=f'fork_{i:02d}';parts.append(p)
    else:raise ValueError(state)
    return Compound(label=f'lowflow_{state}_evidence',children=parts)

def tessellate(shape,color,tolerance=.015):
    vv,ff=shape.tessellate(tolerance)
    return np.array([[p.X,p.Y,p.Z] for p in vv]),np.array(ff,dtype=np.int64),color

def color_of(shape):
    return tuple(round(float(c)*255) for c in tuple(shape.color)[:3])

def exact_occurrences(expected,path):
    """Associate imported exact solids with source labels/colors by centroid/volume."""
    register(path)
    expected=list(expected.children);actual=list(import_step(path).solids())
    assert len(expected)==len(actual),(path,len(expected),len(actual))
    rows=[];named={};matches=[]
    for intended in expected:
        center=np.array(tuple(intended.center()))
        distances=[np.linalg.norm(np.array(tuple(s.center()))-center) for s in actual]
        k=int(np.argmin(distances));solid=actual.pop(k)
        assert distances[k]<1e-5,(intended.label,distances[k])
        assert abs(solid.volume-intended.volume)<max(1e-5,intended.volume*1e-7)
        color=color_of(intended);row=tessellate(solid,color)
        named[intended.label]=row
        if intended.label.startswith('die'):
            for face in solid.faces():rows.append(tessellate(face,PIP if face.area<10 else color,.025))
        else:rows.append(row)
        matches.append({'name':intended.label,'centroid_error_mm':float(distances[k]),'volume_mm3':solid.volume})
    return rows,named,matches

def region(occurrences,az,el,size=1400,pad=.045,framing=None):
    if framing is None:return API['render'](occurrences,az,el,size,pad)
    # Cull wholly off-frame triangles without altering the visible STEP surfaces.
    _,right,up=API['camera_basis'](az,el)
    sx,sy=framing@right,framing@up
    span=max(float(np.ptp(sx)),float(np.ptp(sy)))
    half=span/(1-2*pad)/2;cx,cy=(sx.min()+sx.max())/2,(sy.min()+sy.max())/2
    visible=[]
    for points,faces,color in occurrences:
        tx=(points@right)[faces];ty=(points@up)[faces]
        keep=(tx.max(axis=1)>=cx-half)&(tx.min(axis=1)<=cx+half)&(ty.max(axis=1)>=cy-half)&(ty.min(axis=1)<=cy+half)
        if keep.any():visible.append((points,faces[keep],color))
    return API['render'](visible,az,el,size,pad,framing=framing)

def box_frame(xmin,xmax,ymin,ymax,zmin,zmax):
    return np.array(list(product((xmin,xmax),(ymin,ymax),(zmin,zmax))),dtype=float)

def save_view(snap,name,rows,az,el,size=1600,pad=.05,frame=None):
    im=region(rows,az,el,size,pad,frame);im.save(snap/name);IMAGES.append(name)
    CAMERAS[name]={'azimuth_deg':az,'elevation_deg':el,'orthographic':True,'size_px':size,'padding':pad,'framing_points':None if frame is None else frame.tolist()}
    return im

def neutral(rows):return [(v,f,NEUTRAL) for v,f,c in rows]

def detail_parts(snap):
    path=ROOT/'part_die_1.step';register(path)
    die=import_step(path).solids()[0];rows=[]
    color=tuple(round(c*255) for c in lib.DIE_COLOR)
    for face in die.faces():rows.append(tessellate(face,PIP if face.area<10 else color,.025))
    panels=[region(rows,35,35,1100,.12),region(rows,-145,-35,1100,.12)]
    sheet=Image.new('RGB',(2200,1150),'#edf0f5')
    for i,p in enumerate(panels):sheet.paste(p,(i*1100,50))
    ImageDraw.Draw(sheet).text((30,15),'SAME DIE / OPPOSITE VIEWS',fill='#222222',font_size=24)
    sheet.save(snap/'dice-detail.png');IMAGES.append('dice-detail.png')
    rows=[]
    for name,x,c in [('single',-8,lib.SINGLE_COLOR),('fork',8,lib.FORK_COLOR)]:
        path=ROOT/f'part_{name}_01.step';register(path)
        shape=import_step(path).solids()[0].moved(Location((x,0,0)))
        rows.append(tessellate(shape,tuple(round(v*255) for v in c),.008))
    top=region(rows,90,90,1400,.1);iso=region(rows,-75,55,1400,.1)
    sheet=Image.new('RGB',(2800,1450),'#edf0f5');sheet.paste(top,(0,50));sheet.paste(iso,(1400,50))
    ImageDraw.Draw(sheet).text((30,15),'TOP / THREE-QUARTER / SAME COUNTERS',fill='#222222',font_size=24)
    sheet.save(snap/'counter-detail.png');IMAGES.append('counter-detail.png')

def main():
    snap=ROOT/'snap';snap.mkdir(exist_ok=True)
    states=ROOT.parent/'evidence/states';matches={}
    register(ROOT/'rainward_lib.py');register(Path(__file__))
    setup,names,matches['setup']=exact_occurrences(lib.assembly('setup'),ROOT/'rainward.step')
    save_view(snap,'iso.png',setup,-75,48,1800,.05)
    # Frame the board while preserving setup: cups/dice outside framing are simply out of camera.
    top_frame=box_frame(-96,96,-96,96,0,28)
    save_view(snap,'top.png',setup,90,90,2200,.025,top_frame)
    board=[names['sun']]
    save_view(snap,'board-top.png',neutral(board),90,90,2400,.035)
    save_view(snap,'board-near-top.png',neutral(board),-75,78,2200,.035)
    save_view(snap,'board-oblique.png',neutral(board),-55,28,2000,.04)
    save_view(snap,'board-side.png',neutral(board),-82.5,7,2000,.035)
    detail_parts(snap)
    before,bnames,matches['before']=exact_occurrences(lib.assembly('before'),states/'before.step')
    after,anames,matches['after']=exact_occurrences(lib.assembly('after'),states/'after.step')
    moved=[n for n in bnames if n in anames and np.linalg.norm(bnames[n][0].mean(axis=0)-anames[n][0].mean(axis=0))>1]
    assert len(moved)==2,('Expected exactly two moved hit pieces',moved)
    framing=np.concatenate([bnames[n][0] for n in moved]+[anames[n][0] for n in moved])
    floor=framing.copy();floor[:,2]=0;framing=np.concatenate([framing,floor])
    left=save_view(snap,'before-detail.png',before,AZ,EL,SIZE,PAD,framing)
    right=save_view(snap,'after-detail.png',after,AZ,EL,SIZE,PAD,framing)
    difference=float(np.abs(np.asarray(left,dtype=float)-np.asarray(right,dtype=float)).mean())
    assert difference>=2.,f'Fixed interaction framing indistinguishable: {difference}'
    sheet=Image.new('RGB',(SIZE*2,SIZE+65),'#edf0f5');sheet.paste(left,(0,65));sheet.paste(right,(SIZE,65))
    draw=ImageDraw.Draw(sheet);draw.text((25,20),'BEFORE',fill='#222222',font_size=24);draw.text((SIZE+25,20),'AFTER',fill='#222222',font_size=24)
    sheet.save(snap/'signature.png');IMAGES.append('signature.png')
    lane,ln,matches['lane']=exact_occurrences(support_scene('lane'),states/'lane.step')
    # Full existing board; camera crops a34×31mm patch around lanes6/7 and their separator.
    frame=box_frame(51,80,-4,25,15.7,21.0)
    save_view(snap,'lane-detail.png',lane,75,32,2000,.04,frame)
    save_view(snap,'lane-detail-top.png',lane,90,90,2000,.04,frame)
    # Neutral board retains distinguishable checker material, no board color zoning.
    lneutral=[(v,f,NEUTRAL if i==0 else c) for i,(v,f,c) in enumerate(lane)]
    save_view(snap,'lane-detail-neutral.png',lneutral,75,24,2000,.04,frame)
    capacity,cn,matches['capacity']=exact_occurrences(support_scene('capacity'),states/'capacity.step')
    cframe=box_frame(24,94,-7,16,15.7,29.2)
    save_view(snap,'capacity.png',capacity,75,32,2200,.04,cframe)
    center,nn,matches['center']=exact_occurrences(support_scene('center'),states/'center.step')
    zframe=box_frame(-28,42,-28,28,15.5,21.2)
    save_view(snap,'center-detail.png',center,-60,20,2000,.045,zframe)
    (ROOT/'measure').mkdir(exist_ok=True)
    report={'status':'PASS','geometry':'Only exact exported STEP surfaces; source association by centroid and volume. Native face-normal shading. No drawn lane lines, darkened groove materials, fake shadows, or altered relief. Neutral board views recolor the whole board uniformly. Image labels are outside CAD frames.','signature_scope':'Exactly two moving counters in fixed-camera before/after legal hit; all35 solids remain in both imported states.','mean_rgb_state_difference':difference,'minimum_difference':2.,'source_step_matching':matches,'sources':SOURCES,'cameras':CAMERAS,'images':{n:sha(snap/n) for n in IMAGES},'limits':'Presentation is visual evidence; capacity/support require independent geometry checks. No physical tests or dice fairness claim.'}
    (ROOT/'measure/presentation.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'PASS','mean_rgb_state_difference':difference,'images':IMAGES}))
if __name__=='__main__':main()
