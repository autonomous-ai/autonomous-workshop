"""Render exact STEP states with the shared z-buffer renderer and common framing.

No CAD is authored or modified here. Shared render_review tessellates the input
STEP states and preserves imported occurrence colours. Output panels are placed
side-by-side without editing the rendered product pixels.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer', type=Path, required=True)
    parser.add_argument('--closed', type=Path, default=Path(__file__).parent/'periastra.step')
    parser.add_argument('--opened', type=Path, default=Path(__file__).parent.parent/'evidence-states/opened.step')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--azimuth', type=float, default=-45)
    parser.add_argument('--elevation', type=float, default=20)
    parser.add_argument('--size', type=int, default=1200)
    args = parser.parse_args()
    loader = importlib.machinery.SourceFileLoader('periastra_shared_renderer', str(args.renderer.resolve()))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    module._runtime_paths()
    states = []
    for path in (args.closed,args.opened):
        _,shape=module.build_shape(path.resolve())
        states.append(module.tessellate_occurrences(shape,0.08))
    framing=np.concatenate([points for state in states for points,_,_ in state])
    args.output_dir.mkdir(parents=True,exist_ok=True)
    hero=module.render(states[0],args.azimuth,args.elevation,args.size,0.07)
    hero.save(args.output_dir/'iso.png')
    frames=[module.render(state,args.azimuth,args.elevation,args.size,0.07,framing=framing) for state in states]
    sheet=Image.new('RGB',(2*args.size,args.size),module.BACKGROUND)
    for i,frame in enumerate(frames):
        sheet.paste(frame,(i*args.size,0))
    sheet.save(args.output_dir/'signature.png')
    proof={
        'renderer':'shared render_review; exact STEP import; per-pixel z-buffer',
        'camera':{'azimuth_deg':args.azimuth,'elevation_deg':args.elevation,'projection':'orthographic'},
        'signature_common_framing':True,
        'framing_min_mm':framing.min(axis=0).tolist(),'framing_max_mm':framing.max(axis=0).tolist(),
        'inputs':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (args.closed,args.opened)},
        'outputs':{name:hashlib.sha256((args.output_dir/name).read_bytes()).hexdigest() for name in ['iso.png','signature.png']},
        'limitations':'Appearance evidence only; review visibility before design acceptance. No physical test implied.'}
    (args.output_dir/'render-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'output_dir':str(args.output_dir),'azimuth':args.azimuth,'elevation':args.elevation,'size':args.size}))


if __name__=='__main__':
    main()
