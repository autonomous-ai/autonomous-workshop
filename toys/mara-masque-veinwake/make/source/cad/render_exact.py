"""Exact STEP renderer with leaf colours and shared before/after framing.

The standard render_product CLI was exercised, but its state_sheet recentres
each state and replaces leaf materials. This presentation helper fixes only
camera/framing/material presentation. All geometry comes from delivered STEP.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from build123d import import_step

HERE=Path(__file__).parent
SIZE=1200
BACKGROUND=(246,242,233)

def unit(v):
    v=np.asarray(v,dtype=float)
    return v/np.linalg.norm(v)

def leaves(shape):
    children=list(getattr(shape,'children',()) or ())
    if children:
        for child in children:yield from leaves(child)
    else:yield shape

def load(path):
    triangles=[];colors=[]
    for leaf in leaves(import_step(path)):
        points,faces=leaf.tessellate(0.06)
        p=np.asarray([(v.X,v.Y,v.Z) for v in points],dtype=float)
        f=np.asarray(faces,dtype=int)
        if not len(f):continue
        color=tuple(leaf.color)[:3] if leaf.color else (0.55,0.50,0.45)
        triangles.append(p[f]);colors.extend([color]*len(f))
    return np.concatenate(triangles),np.asarray(colors)

def render(data,forward,framing):
    tri,materials=data
    forward=unit(forward);right=unit(np.cross([0,0,1],forward));up=unit(np.cross(forward,right))
    r=np.stack((right,-up,forward),axis=1)
    projected=tri@r
    frame=framing@r
    low=frame[:,:2].min(axis=0);high=frame[:,:2].max(axis=0)
    scale=SIZE*2*0.86/max(high-low)
    offset=np.array([SIZE,SIZE*0.94])-(low+high)*scale/2
    xy=projected[:,:,:2]*scale+offset
    a=tri[:,1]-tri[:,0];b=tri[:,2]-tri[:,0]
    normals=np.cross(a,b);norm=np.linalg.norm(normals,axis=1)
    valid=norm>1e-10;normals[valid]/=norm[valid,None]
    visible=valid & ((normals@forward)>1e-8)
    light=unit([-0.7,-0.9,1.8])
    brightness=0.50+0.48*np.maximum(0,normals@light)
    rgb=np.clip(materials*255*brightness[:,None]+8,0,255).astype(np.uint8)
    canvas=Image.new('RGB',(SIZE*2,SIZE*2),BACKGROUND)
    shadow=Image.new('RGBA',canvas.size,(0,0,0,0));pen=ImageDraw.Draw(shadow)
    ground=np.array([[0,0,0]])@r
    ground_y=float(ground[0,1]*scale+offset[1])
    pen.ellipse((SIZE-SIZE*.63,ground_y-SIZE*.20,SIZE+SIZE*.63,ground_y+SIZE*.26),fill=(43,34,27,30))
    shadow=shadow.filter(ImageFilter.GaussianBlur(SIZE*.035))
    canvas=Image.alpha_composite(canvas.convert('RGBA'),shadow).convert('RGB')
    # Per-pixel depth resolves intersecting projected triangles around the
    # recessed seats. Mean-depth painter sorting produced false rim slivers.
    pixels=np.asarray(canvas).copy()
    depth=np.full((SIZE*2,SIZE*2),-np.inf)
    for i in np.flatnonzero(visible):
        p=xy[i]
        lo=np.maximum(np.floor(p.min(axis=0)).astype(int),0)
        hi=np.minimum(np.ceil(p.max(axis=0)).astype(int),SIZE*2-1)
        if np.any(lo>hi):continue
        x0,y0=p[0];x1,y1=p[1];x2,y2=p[2]
        den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(den)<1e-10:continue
        yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        xx=xx+0.5;yy=yy+0.5
        w0=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den
        w1=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den
        w2=1-w0-w1
        z=w0*projected[i,0,2]+w1*projected[i,1,2]+w2*projected[i,2,2]
        region=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        mask=(w0>=-1e-8)&(w1>=-1e-8)&(w2>=-1e-8)&(z>region)
        region[mask]=z[mask]
        pixels[lo[1]:hi[1]+1,lo[0]:hi[0]+1][mask]=rgb[i]
    canvas=Image.fromarray(pixels)
    return canvas.resize((SIZE,SIZE),Image.Resampling.LANCZOS)

def main():
    out=HERE/'snap';out.mkdir(exist_ok=True)
    hero=load(HERE/'veinwake.step')
    render(hero,[1.35,-1.65,1.15],hero[0].reshape(-1,3)).save(out/'iso.png')
    paths=[HERE.parents[1]/'presentation/states'/f'{name}.step' for name in ('before','after')]
    states=[load(p) for p in paths]
    framing=np.concatenate([state[0].reshape(-1,3) for state in states])
    forward=[0,-1,0.9]
    frames=[render(state,forward,framing) for state in states]
    sheet=Image.new('RGB',(SIZE*2,SIZE),BACKGROUND)
    for i,frame in enumerate(frames):sheet.paste(frame,(i*SIZE,0))
    sheet.save(out/'signature.png')
    differences=np.abs(np.asarray(frames[0],dtype=float)-np.asarray(frames[1],dtype=float))
    assert differences.mean()>2
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    record={'schema_version':1,'scope':'Exact STEP presentation, no physical performance claim',
            'camera_forward':forward,'projection':'orthographic','common_frame_bounds':[framing.min(axis=0).tolist(),framing.max(axis=0).tolist()],
            'state_sha256s':{str(p.relative_to(HERE.parents[1])):digest(p) for p in paths},
            'hero_step_sha256':digest(HERE/'veinwake.step'),'renderer_sha256':digest(Path(__file__)),
            'iso_sha256':digest(out/'iso.png'),'signature_sha256':digest(out/'signature.png'),
            'mean_rgb_difference':float(differences.mean()),'leaf_srgb_materials':True,
            'reason':'Standard tool sheet recentred each state; use shared framing and fixed elevated front camera.'}
    (out/'RENDER-EVIDENCE.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))

if __name__=='__main__':main()
