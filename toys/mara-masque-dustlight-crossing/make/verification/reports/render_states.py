"""Exact static rule-example states using the native CAD review renderer.
These are illustrative arrangements, not a claimed played game or motion test.
"""
import argparse, importlib.machinery, importlib.util, copy, json, hashlib, sys
from pathlib import Path
from PIL import Image
from build123d import Compound, Pos, Rot, export_step
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dustlight_lib import STARTS, PITCH, BORDER, SURFACE

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--renderer',type=Path,required=True);args=ap.parse_args()
    loader=importlib.machinery.SourceFileLoader('native_review',str(args.renderer.resolve()))
    spec=importlib.util.spec_from_loader(loader.name,loader);renderer=importlib.util.module_from_spec(spec);loader.exec_module(renderer)
    cad=Path(__file__).resolve().parents[1];out=cad.parent/'visual-states';out.mkdir(parents=True,exist_ok=True)
    _,shape=renderer.build_shape(cad/'dustlight.step.py')
    original=list(shape.children)
    # Same sixteen-piece inventory in a crowded illustrative position.
    maps=[{(0,6):(0,3),(1,1):(1,3),(0,7):(6,3),(0,1):(5,3),(1,8):(3,4)},
          {(0,6):(3,8),(1,1):(2,3),(0,7):(3,3),(0,1):(3,5),(1,8):None}]
    sheets=[];records=[]
    for i,changes in enumerate(maps,1):
        children=[copy.deepcopy(p) for p in original[:4]];occupied=set()
        for team,starts in enumerate(STARTS):
            for rank,(x,y) in enumerate(starts,1):
                xy=changes.get((team,rank),(x,y))
                if xy is None:continue
                assert xy not in occupied;occupied.add(xy)
                child=copy.deepcopy(original[4+team*8+rank-1])
                child.location=Pos(BORDER+PITCH*(xy[0]+.5),BORDER+PITCH*(xy[1]+.5),SURFACE)*Rot(0,0,team*180)
                children.append(child)
        state=Compound(label=f'example_{i}',children=children)
        step=out/f'example_{i}.step';export_step(state,step)
        occurrences=renderer.tessellate_occurrences(state,.1)
        view=renderer.render(occurrences,-65,55,1200,.06)
        sheets.append(view)
        records.append(dict(path=str(step.relative_to(cad.parent)),sha256=hashlib.sha256(step.read_bytes()).hexdigest(),occurrences=len(children),view=[-65,55],changed_positions={f'{t}:{r}':xy for (t,r),xy in changes.items()}))
    # Compose two native geometry renders directly into one CAD state sheet.
    sheet=Image.new('RGB',(2400,1200),(234,239,245))
    for i,view in enumerate(sheets):sheet.paste(view,(1200*i,0))
    sheet.save(cad/'snap'/'signature.png')
    for az,name in [(-65,'white-seat'),(115,'black-seat')]:
        renderer.render(renderer.tessellate_occurrences(shape,.1),az,55,1600,.06).save(cad/'snap'/f'{name}.png')
    key_parts=[]
    for team in range(2):
        for rank in range(1,9):
            child=copy.deepcopy(original[4+team*8+rank-1])
            child.location=Pos(((rank-1)%4)*32,((rank-1)//4)*80+team*40,0)
            key_parts.append(child)
    key=Compound(label='piece_comparison',children=key_parts)
    export_step(key,out/'piece_comparison.step')
    renderer.render(renderer.tessellate_occurrences(key,.1),-65,50,1800,.16).save(cad/'snap'/'piece-comparison.png')
    (out/'states.json').write_text(json.dumps(dict(kind='static-rule-example-geometry',states=records,motion='unverified',meaning=['Left: opposing Dust knot blocks Comet at a4, friendly Dust knot blocks Pulsar at g4.','Right: example den victory and removed Giant; this is an illustrative arrangement, not the next ply of the left state.']),indent=2))

if __name__=='__main__':main()
