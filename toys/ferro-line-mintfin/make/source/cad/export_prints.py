"""Reproduce requested STL/3MF and production solids from the component CAD.
Run after gen has refreshed every component and mintfin.step.py.
Static expression/pose states are presentation, not motion verification.
"""
from pathlib import Path
import json
from build123d import Compound, Pos, export_step, import_step
from mintfin_scene import inventory, regions_for, rgb, scene
from params import PALETTE
from mesh_delivery import mesh, stl, three_mf

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def main():
    prints=ROOT.parent/'engineering'/'prints'; parts=ROOT/'parts'; states=ROOT/'states'
    for p in (prints,parts,states):p.mkdir(parents=True,exist_ok=True)
    audit={'units':'mm','tessellation_tolerance_mm':.04,'angular_tolerance_rad':.08,
           'motion':'unverified','production_parts':{},'print_meshes':{}}
    expected={o['name'] for o in json.loads((HERE/'__cadgen__/models/mintfin.step.py/assembly.json').read_text())['occurrences']}
    for role,instance,shape,loc in inventory():
        source=import_step(HERE/f'part_{role}.step')
        assert len(source.solids())==1 and abs(source.volume-shape.volume)<.002,(role,'STEP drift')
        for i,(color,piece) in enumerate(regions_for(role,shape),1):
            name=f'{instance}_{color}_{i:02}';leaf=loc*piece;leaf.color=rgb(color)
            assert len(leaf.solids())==1 and leaf.is_valid
            export_step(leaf,parts/(name+'.step'))
            audit['production_parts'][name]={'color':PALETTE[color],'volume_mm3':leaf.volume,'solids':1}
    assert set(audit['production_parts'])==expected,'Occurrence names disagree'

    inv=inventory()
    chain=[r for r in inv if r[0]=='head' or r[0]=='tail' or r[0].startswith('body_')]
    faces=[]
    for i,mood in enumerate(('happy','sleepy','angry')):
        role='face_'+mood
        faces.append((role,role,import_step(HERE/f'part_{role}.step'),Pos(i*30,0,0)))
    coupons=[r for r in inv if r[0].startswith('coupon_')]
    for title,rows in [('chain',chain),('faces',faces),('hinge-coupon',coupons)]:
        objects=[];physical=[]
        for role,instance,shape,loc in rows:
            physical.append(loc*shape)
            for i,(color,piece) in enumerate(regions_for(role,shape),1):
                name=f'{instance}_{color}_{i:02}'
                pp,ff,report=mesh(loc*piece)
                assert report['shells']==1,name
                audit['print_meshes'][name]=report
                objects.append({'name':name,'color':PALETTE[color],'points':pp,'faces':ff})
        # One build item preserves the engineered arrangement through import.
        three_mf(prints/f'Mintfin-{title}.3mf',objects,[{'name':'Mintfin '+title,'members':list(range(len(objects)))}])
        pp,ff,report=mesh(Compound(children=physical))
        assert report['shells']==len(rows),(title,report)
        stl(prints/f'Mintfin-{title}.stl',pp,ff)
        audit['print_meshes']['Mintfin-'+title]=report
    for mood in ('happy','sleepy','angry'):
        pp,ff,report=mesh(import_step(HERE/f'part_face_{mood}.step'))
        stl(prints/f'Mintfin-face-{mood}.stl',pp,ff)
    for mood,angles in [('happy',[0]*8),('sleepy',[22]*8),('angry',[-18,-18,-18,18,18,18,18,18])]:
        export_step(scene(mood,angles,extras=False),states/(mood+'.step'))
    (HERE/'measure/mesh-delivery.json').write_text(json.dumps(audit,indent=2)+'\n')
    print('PASS:',len(expected),'production solids; three arranged 3MF/STL sets; three individual faces; static states.')

if __name__=='__main__':main()
