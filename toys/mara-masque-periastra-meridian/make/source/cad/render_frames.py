"""Render exact STEP states at named camera angles with the shared renderer.

No CAD is authored or modified here. The shared render_review module tessellates
the exact STEP and preserves imported occurrence colours; an optional crop only
selects a region of the rendered frame, it never edits the rendered pixels.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.machinery
import importlib.util
import json

import numpy as np
from PIL import Image


def load_renderer(path):
    loader = importlib.machinery.SourceFileLoader('periastra_shared_renderer', str(Path(path).resolve()))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    module._runtime_paths()
    return module


def box_points(box):
    lo = np.array(box[:3], dtype=float)
    hi = np.array(box[3:], dtype=float)
    return np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--azimuth', type=float, required=True)
    parser.add_argument('--elevation', type=float, required=True)
    parser.add_argument('--size', type=int, default=1200)
    parser.add_argument('--pad', type=float, default=0.07)
    parser.add_argument('--crop', type=str, default=None,
                        help='cx,cy,frac -- select a square region of the rendered frame, as '
                             'fractions of its width/height, and resample it to --size')
    parser.add_argument('--provenance', type=Path, default=None)
    args = parser.parse_args()

    module = load_renderer(args.renderer)
    _, shape = module.build_shape(args.source.resolve())
    state = module.tessellate_occurrences(shape, 0.05)
    if args.crop:
        cx, cy, frac = (float(v) for v in args.crop.split(','))
        image = module.render(state, args.azimuth, args.elevation, int(args.size/frac), args.pad)
        half = image.width*frac/2
        box = (round(image.width*cx-half), round(image.height*cy-half),
               round(image.width*cx+half), round(image.height*cy+half))
        image = image.crop(box).resize((args.size, args.size), Image.LANCZOS)
    else:
        image = module.render(state, args.azimuth, args.elevation, args.size, args.pad)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.out)
    record = {'source': str(args.source), 'source_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
              'camera': {'azimuth_deg': args.azimuth, 'elevation_deg': args.elevation,
                         'projection': 'orthographic', 'crop_cx_cy_frac': args.crop},
              'output': str(args.out), 'output_sha256': hashlib.sha256(args.out.read_bytes()).hexdigest()}
    if args.provenance:
        args.provenance.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
