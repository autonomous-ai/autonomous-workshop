#!/usr/bin/env python3
"""Stamp a labelled pixel grid on a reference image, or on a crop of one.

`measure_image.py` summarises a silhouette. For an **organic** subject that is
often not enough: a freeform outline needs a table of (x, z) stations along
it, not a fill ratio. The fastest
reliable way to get that table is to read coordinates off the image directly --
but only if the image carries coordinates you can read.

    python grid_overlay.py ref/side.png -o tmp/side-grid.png
    python grid_overlay.py ref/side.png -o tmp/head.png --crop 300,120,700,520 --zoom 3
    python grid_overlay.py ref/side.png -o tmp/side-grid.png --step 50

Labels are always in ORIGINAL image pixels, including inside a crop, so a
number read off a zoomed detail can be pasted straight back into
`measure_image.py --rows` or into the spec.

Why this is in the toolbox rather than left to a throwaway script: the whole
point of `measure_image.py` is that a project measures with one instrument. A
grid overlay reads the same pixels in the same coordinate frame, so a station
table taken off the grid and a `--rows` scan can be cross-checked against each
other. A hand-rolled crop with no axes cannot.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

GRID = (255, 0, 255)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--step", type=int, default=100, help="grid pitch in original px")
    ap.add_argument("--crop", help="x0,y0,x1,y1 in original px")
    ap.add_argument("--zoom", type=float, default=1.0)
    args = ap.parse_args()

    image = Image.open(args.image).convert("RGB")
    x0, y0 = 0, 0
    if args.crop:
        x0, y0, x1, y1 = (int(v) for v in args.crop.split(","))
        x0, x1 = sorted((max(0, x0), min(image.width, x1)))
        y0, y1 = sorted((max(0, y0), min(image.height, y1)))
        image = image.crop((x0, y0, x1, y1))
    if args.zoom != 1.0:
        image = image.resize((int(image.width * args.zoom),
                              int(image.height * args.zoom)), Image.LANCZOS)

    draw = ImageDraw.Draw(image)
    step = max(1, int(args.step * args.zoom))
    for px in range(0, image.width, step):
        draw.line([(px, 0), (px, image.height)], fill=GRID)
        draw.text((px + 3, 3), str(int(x0 + px / args.zoom)), fill=GRID)
    for py in range(0, image.height, step):
        draw.line([(0, py), (image.width, py)], fill=GRID)
        draw.text((3, py + 3), str(int(y0 + py / args.zoom)), fill=GRID)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(f"wrote {args.output}  ({image.width}x{image.height}, "
          f"grid {args.step} original px, labels in original coordinates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
