import numpy as np
from PIL import Image
D=__import__('sys').argv[1]
im=Image.open(D+'/p1-2.png').convert('RGB'); a=np.asarray(im).copy()
BG=np.array([251,242,231],dtype=np.uint8); MM=150/22.0
# 1. squash the toe (contract: toe 17 ahead of the shin, heel 2.5 behind)
out=a.copy()
for y in range(600,1024):
    row=a[y]; bgp=np.tile(BG,(1,1))
    def sq(x0,x1,w): return np.asarray(Image.fromarray(row[x0:x1][None]).resize((w,1),Image.LANCZOS))[0]
    left=np.concatenate([np.tile(BG,(116,1)),row[0:340],sq(340,500,44)])
    right=np.concatenate([sq(682,733,25),row[733:],np.tile(BG,(26,1))])
    out[y]=np.concatenate([left,row[500:682],right])
# lift the leg so the hanging boot fits; canvas 1024 x 1400
H=1400; can=np.tile(BG,(H,1024,1)); can[0:1024]=out
p1=Image.fromarray(can)
c=np.asarray(p1).astype(int); fg=np.abs(c-BG.astype(int)).sum(-1)>36
yy,xx=np.mgrid[0:H,0:1024]
r_,g_,b_=c[...,0],c[...,1],c[...,2]
zone=(yy>=727)|((xx<532)&(yy>=630))
orng=(r_>g_+50)&(b_<120); light=(r_>185)&(g_>185)&(b_>175)
boot=fg&zone&~orng&~light
upper=(fg&~zone)|(fg&zone&orng&(xx>=525)&(xx<=690)&(yy<760))
r,g,b=c[...,0],c[...,1],c[...,2]; pur0=boot&(b>r+12)&(r>g+12)
from PIL import ImageFilter
pd=np.asarray(Image.fromarray((pur0*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)))>0
grey=(np.abs(r-g)<14)&(np.abs(g-b)<14)&(r<140)
pur=boot&pd&~grey
def layer(mask,img=None):
    img=np.asarray(p1) if img is None else img
    rgba=np.dstack([img,(mask*255).astype(np.uint8)]); return Image.fromarray(rgba,'RGBA')
def place(base_rgb,layers):
    out=Image.fromarray(base_rgb).convert('RGBA')
    for L in layers: out.alpha_composite(L)
    return out.convert('RGB')
blank=np.tile(BG,(H,1024,1))
ankle=(532+16.75*MM, 910-12.25*MM)
tx0,tx1=round(532+12.75*MM),round(532+20.75*MM)
src=np.asarray(p1)[600:727,tx0:tx1]
tongue_img=np.asarray(p1).copy(); tm=np.zeros((H,1024),bool)
ty1=round(ankle[1])
reps=int(np.ceil((ty1-727)/127))+1
strip=np.concatenate([src]*reps)[:ty1-727]
tongue_img[727:ty1,tx0:tx1]=strip; tm[727:ty1,tx0:tx1]=True
TG=layer(tm,tongue_img)
U=layer(upper); B=layer(boot)
panel1=place(blank,[B,U])
# 2. boot folds 90 down at the ankle (toe down, sole back)
B2=B.rotate(90,center=ankle,resample=Image.BICUBIC)
panel2=place(blank,[TG,B2,U])
# 3. shin slides 16 up into the thigh: everything below the thigh rises
s=round(16*MM)
thigh=fg&(yy<234); T=layer(thigh)
wheel=upper&((np.abs(r-g)<14)&(np.abs(g-b)<14))&(yy>=234)
lower=layer(upper&~thigh&~wheel); W3=Image.new('RGBA',(1024,H),(0,0,0,0)); W3.alpha_composite(layer(wheel),(0,-s))
TG3=Image.new('RGBA',(1024,H),(0,0,0,0)); TG3.alpha_composite(TG,(0,-s))
L3=Image.new('RGBA',(1024,H),(0,0,0,0)); L3.alpha_composite(lower,(0,-s))
B3=Image.new('RGBA',(1024,H),(0,0,0,0)); B3.alpha_composite(B2,(0,-s))
panel3=place(blank,[TG3,B3,L3,T,W3])
# 4. wing stands up 90 on its hinge (knuckle at the toe), then the leg lies down as in the car
kn=(300+116+20, 757)          # knuckle centre in panel 1 (after the squash shift)
def rot(p,c,deg):              # visual CCW rotation in screen coords
    t=np.radians(deg); dx,dy=p[0]-c[0],p[1]-c[1]
    return (c[0]+dx*np.cos(t)+dy*np.sin(t), c[1]-dx*np.sin(t)+dy*np.cos(t))
kn3=rot(kn,ankle,90); kn3=(kn3[0],kn3[1]-s)
P=layer(pur); notP=layer(boot&~pur)
P3=Image.new('RGBA',(1024,H),(0,0,0,0)); P3.alpha_composite(P.rotate(90,center=ankle,resample=Image.BICUBIC),(0,-s))
N3=Image.new('RGBA',(1024,H),(0,0,0,0)); N3.alpha_composite(notP.rotate(90,center=ankle,resample=Image.BICUBIC),(0,-s))
P4=P3.rotate(90,center=kn3,resample=Image.BICUBIC)
leg4=place(blank,[TG3,N3,P4,L3,T,W3])
big=Image.new('RGB',(2000,2000),tuple(int(v) for v in BG)); big.paste(leg4,(488,300))
panel4=big.rotate(-90,center=(1000,1000),resample=Image.BICUBIC,fillcolor=tuple(int(v) for v in BG))
def crop(p):
    c=np.asarray(p).astype(int); m=np.abs(c-BG.astype(int)).sum(-1)>36; ys,xs=np.nonzero(m)
    return p.crop((xs.min()-20,ys.min()-20,xs.max()+21,ys.max()+21))
panel1,panel2,panel3,panel4=[crop(p) for p in (panel1,panel2,panel3,panel4)]
for i,p in enumerate([panel1,panel2,panel3,panel4],1): p.save(f'{D}/q{i}.png')
print('ok',ankle,kn3)
