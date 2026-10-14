"""Compose the v3 colour-steps sheet. Robot panels share one scale and one
anchor (the top of the shoulder row, yellow excluded), shrunk together so the
tallest panel fits its tile. Run from prototypes/v3-steps."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
BG=(245,240,230); P=400; CAP=44; M=14
font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",20)
def load(f):
    im=Image.open(f).convert("RGBA"); flat=Image.new("RGBA",im.size,BG+(255,)); flat.alpha_composite(im)
    rgb=flat.convert("RGB"); a=np.asarray(rgb).astype(int); fg=abs(a-a[3,3]).sum(-1)>40
    return rgb,a,fg
def fit(f):
    rgb,a,fg=load(f); ys=np.nonzero(fg.any(1))[0]; xs=np.nonzero(fg.any(0))[0]
    c=rgb.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1)); s=min((P-40)/c.size[0],(P-40)/c.size[1])
    c=c.resize((int(c.size[0]*s),int(c.size[1]*s)),Image.LANCZOS)
    t=Image.new("RGB",(P,P),tuple(int(v) for v in a[3,3])); t.paste(c,((P-c.size[0])//2,(P-c.size[1])//2)); return t
robots=["r6","r5","r4b","r3","r2c","r1","r0","back2"]
info={}
for f in robots:
    rgb,a,fg=load(f+".png"); r,g,b=a[...,0],a[...,1],a[...,2]
    grey=(abs(r-g)<15)&(abs(g-b)<15)&(r>150)&(r<235)
    anchor=np.nonzero(grey.sum(1)>20)[0].min()
    w=np.array([np.ptp(np.nonzero(row)[0]) if row.any() else 0 for row in fg[anchor:]]); W=w.max()
    xs=np.nonzero(fg[anchor:].any(0))[0]; cx=(xs.min()+xs.max())/2
    ys=np.nonzero(fg.any(1))[0]
    info[f]=(rgb,a,1.0/W,anchor,cx,ys.min(),ys.max())
base=138
above=max((an-y0)*s*base for _,_,s,an,_,y0,_ in info.values())
below=max((y1-an)*s*base for _,_,s,an,_,_,y1 in info.values())
k=min(1.0,(P-2*M)/(above+below)); ay=M+above*k
print("shrink",round(k,3),"anchor",round(ay))
def tile(f):
    rgb,a,s,an,cx,_,_=info[f]; s=s*base*k
    im=rgb.resize((round(rgb.size[0]*s),round(rgb.size[1]*s)),Image.LANCZOS)
    t=Image.new("RGB",(P,P),tuple(int(v) for v in a[3,3])); t.paste(im,(round(P/2-cx*s),round(ay-an*s))); return t
items=[("0. Xe",fit("car.png")),("1. Dựng xe đứng trên đuôi",tile("r6")),("2. Gập cánh sau lên mũi giày",tile("r5")),("3. Kéo cẳng chân ra",tile("r4b")),
("4. Gập bàn chân ra trước",tile("r3")),("5. Nắm tay bật ra",tile("r2c")),("6. Mũi lật ra sau lưng",tile("r1")),("7. Đầu bật lên",tile("r0")),
("Sau lưng robot",tile("back2")),("Đuôi xe nhìn từ sau",fit("carrear.png")),("Chân nhìn ngang: robot → xe",fit("leg2.png")),("Robot thật (ảnh ref-01)",fit("../../ref-01-racer-mecha.png"))]
sheet=Image.new("RGB",(4*P,3*(P+CAP)),BG); d=ImageDraw.Draw(sheet)
for i,(cap,t) in enumerate(items):
    x0,y0=(i%4)*P,(i//4)*(P+CAP); sheet.paste(t,(x0,y0+CAP)); d.text((x0+10,y0+11),cap,fill=(40,36,32),font=font)
sheet.save("../v3-colour-steps.png")
