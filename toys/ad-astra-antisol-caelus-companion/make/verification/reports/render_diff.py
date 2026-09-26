"""Where do this run's canonical renders differ from the source archive's?

The correction adds one small oval to each Neptune piece and must change
nothing else.  The renderer is deterministic, so a render of an unchanged
scene at an unchanged camera comes out pixel-identical, and every pixel that
moved must lie on a Neptune globe.  This compares each regenerated render
against the image of the same name in `revision-source.zip`
(`make/verification/renders/...`) and reports how many pixels changed, the
bounding box of the change, and writes an amplified difference image to
`measure/render-diff/` so the location can be checked by eye.

    "$WORKSHOP_PYTHON" measure/render_diff.py <revision-source.zip> \
        > measure/render-diff.md
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
SNAP = HERE.parent / "snap"
PREFIX = "make/verification/renders/"
NAMES = [
    "iso.png", "signature.png", "rank-ladder-sol.png", "rank-ladder-anti.png",
    "worlds/neptune-sol-hero.png", "worlds/neptune-anti-hero.png",
    "worlds/neptune-sol-spot.png", "worlds/neptune-anti-spot.png",
    "worlds/neptune-sol-opposite.png", "worlds/neptune-anti-opposite.png",
    "worlds/neptune-sol-polar.png", "worlds/neptune-anti-polar.png",
    "worlds/neptune-pair-hero.png", "worlds/neptune-pair-spot.png",
    "worlds/neptune-pair-opposite.png",
    "worlds/neptune-earth-hero.png", "worlds/neptune-earth-hero-anti.png",
    "worlds/uranus-neptune-hero.png", "worlds/uranus-neptune-hero-anti.png",
]
#: A channel difference at or under this is antialiasing noise, not a change.
NOISE = 8


def main() -> int:
    archive = zipfile.ZipFile(sys.argv[1])
    out_dir = HERE / "render-diff"
    out_dir.mkdir(exist_ok=True)
    lines = [
        "# Canonical renders against the source archive's", "",
        "Pixels whose largest channel difference exceeds %d of 255, against the"
        % NOISE,
        "image of the same name in `%s`. Box is (x0, y0, x1, y1)." % Path(sys.argv[1]).name,
        "", "| render | size | changed px | changed % | box of change |",
        "|---|---|---:|---:|---|",
    ]
    for name in NAMES:
        new = np.asarray(Image.open(SNAP / name).convert("RGB")).astype(int)
        old = np.asarray(Image.open(io.BytesIO(archive.read(PREFIX + name)))
                         .convert("RGB")).astype(int)
        if new.shape != old.shape:
            lines.append("| `%s` | %s vs %s | - | - | size differs |"
                         % (name, new.shape[:2], old.shape[:2]))
            continue
        mask = np.abs(new - old).max(axis=2) > NOISE
        count = int(mask.sum())
        if count:
            ys, xs = np.nonzero(mask)
            box = "(%d, %d, %d, %d)" % (xs.min(), ys.min(), xs.max(), ys.max())
            vis = (new * 0.35).astype(np.uint8)
            vis[mask] = (255, 0, 255)
            Image.fromarray(vis).save(out_dir / name.replace("/", "__"))
        else:
            box = "none"
        lines.append("| `%s` | %dx%d | %d | %.4f | %s |"
                     % (name, new.shape[1], new.shape[0], count,
                        100.0 * count / mask.size, box))
    lines += ["", "Magenta marks every changed pixel in `measure/render-diff/<name>`.", ""]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
