"""The two canonical product frames, written the same way every time.

`iso.png` is the hero: the whole set in the opening position with both trays,
at the fixed frame the product is photographed from -- 35 degrees of azimuth
off the rank axis from the Sol end and 22 degrees of elevation, which is
azimuth -55 in this build's axes (antisol_spec.md, section 11, item 11).  Its low elevation is
what puts the globes rather than the board in front of the eye.

`signature.png` is the state sheet: the three positions of one game, side by
side, at the higher isometric.  It stays there because at 22 degrees the far
ranks foreshorten into each other and the three positions stop being
separable.

The three state panels share one camera AND one framing box.  Framed panel by
panel the same board lands at a different size in each, and the sheet reads as
though the terrain had moved between positions; sharing the box means the only
thing that changes across the three is which worlds are still standing.

Shading, colour and projection are `render_review`'s, unchanged -- this only
chooses the camera, the shared framing and the crop.

    "$WORKSHOP_PYTHON" snap_frames.py <cad-skill-scripts-dir> [out]
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image

#: [assumed] the product's own fixed frame, and the isometric the sheet keeps.
HERO_VIEW = (-55.0, 22.0)
SHEET_VIEW = (-45.0, 35.264)
HERO_SIZE = 2400
PANEL = (1200, 800)
SHEET_ORDER = ("opening", "midgame", "endgame")
BACKGROUND = (237, 240, 244)


def _renderer(scripts: Path):
    path = scripts / "render_review"
    loader = importlib.machinery.SourceFileLoader("render_review", str(path))
    spec = importlib.util.spec_from_loader("render_review", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _crop_to_content(image: Image.Image, margin: int) -> Image.Image:
    pixels = np.asarray(image.convert("RGB")).astype(int)
    mask = np.abs(pixels - np.array(BACKGROUND)).sum(2) > 6
    rows, cols = np.nonzero(mask)
    box = (
        max(0, cols.min() - margin), max(0, rows.min() - margin),
        min(image.width, cols.max() + 1 + margin),
        min(image.height, rows.max() + 1 + margin),
    )
    return image.crop(box)


def write_iso(scripts: Path, source: Path, out: Path) -> Path:
    render_review = _renderer(scripts)
    _src, shape = render_review.build_shape(source)
    occurrences = render_review.tessellate_occurrences(shape, 0.08)
    image = render_review.render(occurrences, *HERO_VIEW, HERO_SIZE, 0.02)
    out.parent.mkdir(parents=True, exist_ok=True)
    _crop_to_content(image, round(0.02 * HERO_SIZE)).save(out)
    return out


def write_signature(scripts: Path, out: Path, states: Path | None = None) -> Path:
    """The three-state sheet, from source or from exported state STEPs.

    `states` names a directory holding one `board-<position>.step` per position
    -- exactly what `snapshots.py` writes -- and makes the sheet reproducible
    without rebuilding the whole set three times.  That matters for more than
    speed: generating the set takes about four and a half minutes per position
    on the machine this was built on, so the sheet is a fifteen-minute job in
    one piece and a one-minute job from files, and a fifteen-minute job is one
    that can be interrupted halfway and leave nothing behind.  The two paths
    describe the same three assemblies: `snapshots.write_state` exports exactly
    the `product_compound(name, with_trays=False)` this builds otherwise.
    """
    render_review = _renderer(scripts)
    panels = []
    for name in SHEET_ORDER:
        if states is not None:
            _src, shape = render_review.build_shape(states / ("board-%s.step" % name))
        else:
            from assemblies.product import product_compound

            shape = product_compound(name, with_trays=False)
        panels.append(render_review.tessellate_occurrences(shape, 0.08))

    return _draw_sheet(render_review, panels, out)


def _draw_sheet(render_review, panels, out: Path) -> Path:
    """Three tessellated positions -> one sheet, one camera, one framing box."""
    # One framing box over all three states, so the camera does not zoom
    # between panels.
    framing = np.concatenate(
        [points for occurrences in panels for points, _faces, _colour in occurrences]
    )
    images = [
        render_review.render(occurrences, *SHEET_VIEW, PANEL[0], 0.03, framing=framing)
        for occurrences in panels
    ]

    # One vertical window over all three, for the same reason.
    top, bottom = PANEL[0], 0
    for image in images:
        pixels = np.asarray(image.convert("RGB")).astype(int)
        rows, _cols = np.nonzero(np.abs(pixels - np.array(BACKGROUND)).sum(2) > 6)
        top, bottom = min(top, int(rows.min())), max(bottom, int(rows.max()) + 1)
    centre = (top + bottom) // 2
    start = max(0, min(PANEL[0] - PANEL[1], centre - PANEL[1] // 2))

    sheet = Image.new("RGB", (PANEL[0] * len(images), PANEL[1]), BACKGROUND)
    for index, image in enumerate(images):
        sheet.paste(image.crop((0, start, PANEL[0], start + PANEL[1])),
                    (index * PANEL[0], 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def tessellate_state(scripts: Path, state: Path, out: Path) -> Path:
    """Tessellate ONE exported state and keep the triangles on disk.

    The third way of making the sheet, and the one that survives being
    interrupted.  Reading a fifty-megabyte assembly STEP and tessellating its
    236 occurrences is minutes of work per position, so doing all three and
    then rendering is a single job long enough that losing it costs everything.
    This does one position and stops.  `compose_signature` then reads the three
    caches and draws the sheet in seconds.

    The cached arrays are exactly what `render_review.tessellate_occurrences`
    returns -- points, faces and one colour per occurrence -- so the sheet this
    path produces is the sheet the other two produce.
    """
    render_review = _renderer(scripts)
    _src, shape = render_review.build_shape(state)
    occurrences = render_review.tessellate_occurrences(shape, 0.08)
    out.parent.mkdir(parents=True, exist_ok=True)
    stored = {}
    for index, (points, faces, colour) in enumerate(occurrences):
        stored["points_%d" % index] = points
        stored["faces_%d" % index] = faces
        stored["colour_%d" % index] = np.asarray(colour, dtype=float)
    stored["count"] = np.asarray([len(occurrences)])
    np.savez_compressed(out, **stored)
    return out


def _load_state(path: Path):
    stored = np.load(path)
    count = int(stored["count"][0])
    return [
        (stored["points_%d" % index], stored["faces_%d" % index],
         tuple(stored["colour_%d" % index].tolist()))
        for index in range(count)
    ]


def compose_signature(scripts: Path, caches, out: Path) -> Path:
    """The sheet, from three cached tessellations, in the sheet's own order."""
    render_review = _renderer(scripts)
    panels = [_load_state(Path(item)) for item in caches]
    return _draw_sheet(render_review, panels, out)


if __name__ == "__main__":
    scripts = Path(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == "tess":
        print(tessellate_state(scripts, Path(sys.argv[3]), Path(sys.argv[4])))
    elif len(sys.argv) > 2 and sys.argv[2] == "compose":
        print(compose_signature(scripts, sys.argv[3:-1], Path(sys.argv[-1])))
    else:
        where = Path(sys.argv[2] if len(sys.argv) > 2 else "snap")
        states = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        print(write_iso(scripts, Path("antisol.step"), where / "iso.png"))
        print(write_signature(scripts, where / "signature.png", states))
