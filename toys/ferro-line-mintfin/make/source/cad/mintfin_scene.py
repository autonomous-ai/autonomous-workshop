"""Named placements and AMS regions, built from the reviewed component source.
A static pose is presentation only; motion remains unverified.
"""
from math import radians,cos,sin
from build123d import Color,Pos,Rot,Box,Align,Compound
from cadgen.assembly import AssemblyHelper
import mintfin_lib as body
import head_faces as face
from params import PALETTE,FIRST_JOINT_X,JOINT_PITCH

def rgb(name):
    h=PALETTE[name].lstrip('#')
    return Color(*[int(h[i:i+2],16)/255 for i in(0,2,4)])

def split_masks(shape,masks,default):
    remaining=shape;regions=[]
    for color,tools in masks.items():
        for tool in tools:
            piece=remaining&tool
            for solid in piece.solids():
                assert solid.volume>0.001,'Sliver color island'
                regions.append((color,solid))
            remaining=remaining-tool
    regions += [(default,s) for s in remaining.solids()]
    assert abs(sum(s.volume for _,s in regions)-shape.volume)<.001
    return regions

def regions_for(role,shape):
    if role=='head': return split_masks(shape,face.head_color_masks(),'mint')
    if role.startswith('face_'):return split_masks(shape,face.face_color_masks(role[5:]),'cream')
    if role.startswith('body_') or role=='tail':
        # Feet receive three distinct blunt charcoal claw inlays, not a full cap.
        regions=body.color_regions(shape,role)
        if role in('body_1','body_4'):
            mint=shape
            tools=[]
            for side in(-1,1):
                for x in(5.8,8,10.2):
                    tools.append(Pos(x,side*17,0)*Box(1.3,3.8,5,
                        align=(Align.CENTER,Align.CENTER,Align.MIN)))
            regions=split_masks(shape,{'charcoal':tools,'coral':[Pos(0,0,body.BODY_HEIGHTS[int(role[-1])-1]-.1)*Box(40,40,12,align=(Align.CENTER,Align.CENTER,Align.MIN))],
                'cream':[Pos(7,0,0)*Box(4,28,1.2,align=(Align.CENTER,Align.CENTER,Align.MIN))]},'mint')
        return regions
    return [('mint' if role=='coupon_pin' else 'coral',shape)]

def inventory(mood='happy',joint_angles=None,extras=True):
    """Role, physical instance name, fused solid, placement datum."""
    angles=[0]*8 if joint_angles is None else joint_angles
    assert len(angles)==8 and all(abs(a)<=30 for a in angles)
    rows=[('head','head',face.head(),Pos(0,0,0)),
          ('face_'+mood,'installed_'+mood,face.face(mood),face.FACE_INSTALL)]
    x,y,angle=FIRST_JOINT_X,0,0
    for i in range(1,8):
        angle+=angles[i-1]
        rows.append((f'body_{i}',f'body_{i}',body.segment(i),Pos(x,y,0)*Rot(0,0,angle)))
        x+=JOINT_PITCH*cos(radians(angle));y+=JOINT_PITCH*sin(radians(angle))
    angle+=angles[7]
    rows.append(('tail','tail',body.tail(),Pos(x,y,0)*Rot(0,0,angle)))
    if extras:
        spares=[m for m in('happy','sleepy','angry') if m!=mood]
        for i,m in enumerate(spares):
            rows.append(('face_'+m,'spare_'+m,face.face(m),Pos(30+i*30,52,0)))
        for i,c in enumerate((.35,.45,.55)):
            loc=Pos(38+i*42,83,0)
            rows += [('coupon_pin',f'coupon_{round(c*100)}_pin',body.coupon_pin(),loc),
                 (f'coupon_receiver_{round(c*100)}',f'coupon_{round(c*100)}_receiver',body.coupon_receiver(c),loc)]
    return rows

def scene(mood='happy',joint_angles=None,extras=True):
    asm=AssemblyHelper('Mintfin')
    for role,instance,shape,loc in inventory(mood,joint_angles,extras):
        for i,(color,piece) in enumerate(regions_for(role,shape),1):
            leaf=loc*piece
            leaf.color=rgb(color)
            asm.add(leaf,f'{instance}_{color}_{i:02}')
    return asm.build()
