#!/usr/bin/env python3
"""Render the ASSEMBLED game to renders/assembled.png, in its locked colours.

    ./render_assembly.py out/<slug>

Why this exists. Phase 2 exports each part to fe_parts/<id>.stl in PRINT
orientation - flat, at the origin, which is right for a printer and useless as
a picture: measured on overcommit, all 10 parts sat at x=0 y=0, so the review
image drew ten watertight solids occupying the same space and came out as
shards and floating planes. The coherence lens scored that 2/10 and was honest
about what it saw; what it saw was not the product.

The real assembly was on disk the whole time. `scripts/review assembled.step`
resolves it into assembled_parts/<id>_<n>.stl at true positions - but every
png_path it returns is null, because cadcode's PNG renderer does not work on
this box. So the geometry was fine, the assembly was fine, and only the picture
was missing.

Colours come from part_colors.json, which phase 2 already writes correctly and
nothing was reading. A solid named `bid_box_3` takes the colour of `bid_box`.
"""
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # headless: no display on this box
import matplotlib.pyplot as plt            # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
import numpy as np                         # noqa: E402
import trimesh                             # noqa: E402

VIEWS = (("iso", 22, -55), ("top", 89, -90), ("front", 8, -90), ("side", 8, 0))
# The hero is a STEEPER 3/4 than the contact sheet's iso on purpose: this
# design is a flat bed under a 96mm tower, so a low camera is all tower and
# the play area - boxes, pegs, lever - never appears. The coherence lens said
# the same thing about the silhouette; a video of the hopper is not a how-to.
HERO_VIEW = ("hero", 48, -58)
FACE_CAP = 60_000        # per part; a tray with 200k faces renders no better


def part_colours(out_dir: Path) -> dict:
    f = out_dir / "part_colors.json"
    if not f.is_file():
        return {}
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    # Accept both key styles. Phase 2 writes bare ids; publish.py re-keys the
    # same file to `<id>.stl` so fe_colors can match the uploaded siblings, and
    # after that this renderer was silently drawing everything grey - caught by
    # its own missing-colour warning, which is why that warning exists.
    return {re.sub(r"\.stl$", "", k): v for k, v in d.items()
            if isinstance(v, str) and v.startswith("#")}


def base_name(stem: str) -> str:
    """bid_box_3 and visitor_pawn-3 -> the part. A suffix is not a new part.

    The hyphen form is not hypothetical and it is not rare: coach-party
    2026-08-20 exported `visitor_pawn` plus `visitor_pawn-2` .. `visitor_pawn-20`,
    so ONE pawn of twenty took its ivory and the other nineteen fell through to
    the fallback grey. 40 of 51 solids rendered grey. The coherence lens scored
    it 3/10 - "the supposed ivory crowd renders in the same cool grey value as
    the ground", "the lone visibly ivory pawn looks anomalous" - which is an
    exactly correct reading of a picture this file drew wrong, and it stopped
    the run before phase 3.
    """
    return re.sub(r"[-_]\d+$", "", stem)


def decimate(m, cap: int):
    """trimesh changed this signature: older builds take a face COUNT, newer
    ones a reduction FRACTION and raise on anything outside 0..1. Try both, and
    keep the full mesh rather than fail the render if neither works.

    ModuleNotFoundError joined that list 2026-08-21: current trimesh defers to
    `fast_simplification`, which is not installed in the render venv, so the
    call raised straight through the two handlers this function has always had
    and killed the animation. The docstring promised the full mesh rather than
    a dead render and the code did not honour it - which is the whole failure
    mode this function exists to prevent, one exception type down.
    """
    if m.faces.shape[0] <= cap:
        return m
    for kwargs in ({"face_count": cap},
                   {"percent": max(0.01, min(0.99, cap / m.faces.shape[0]))}):
        try:
            return m.simplify_quadric_decimation(**kwargs)
        except (TypeError, ValueError, ModuleNotFoundError, ImportError):
            continue
    return m


def load(out_dir: Path):
    """Every positioned solid, with the colour its id was assigned."""
    src = out_dir / "assembled_parts"
    if not src.is_dir():
        raise SystemExit(f"ABORT: {src} not found - run "
                         f"`scripts/review assembled.step` in {out_dir} first")
    colours = part_colours(out_dir)
    out = []
    for f in sorted(src.glob("*.stl")):
        try:
            m = trimesh.load(f, force="mesh")
        except Exception as e:                       # a single bad part is not fatal
            print(f"  skip {f.name}: {e}", flush=True)
            continue
        m = decimate(m, FACE_CAP)
        out.append((f.stem, m, colours.get(base_name(f.stem), "#9AA5B1")))
    if not out:
        raise SystemExit(f"ABORT: no STL in {src}")
    return out


def distinct_parts(parts):
    """One mesh per DISTINCT part id, laid out on a grid, centred at origin.

    The four views draw the machine as assembled, which is what a buyer meets -
    and it hides everything inside it. Measured 2026-08-20 on `precedent`: the
    coherence lens returned 4/10 and then 3/10 saying "the palette did not
    survive - court violet, bone white, evidence crimson and cool cyan are
    effectively missing", because the gates bolt inside the bench and the
    weights sit in the hopper. Four of seven colours were not in the picture at
    any angle, so no palette could have passed. Three rounds of recolouring
    chased a score the image could not represent.

    The lens's question is "can a player tell the parts apart at a glance". This
    panel is that question, drawn.
    """
    best = {}
    for stem, m, colour in parts:
        b = base_name(stem)
        if b not in best or len(m.faces) > len(best[b][0].faces):
            best[b] = (m, colour)
    items = sorted(best.items())
    if not items:
        return []
    cols = int(np.ceil(np.sqrt(len(items))))
    # Pitch off the MEDIAN part, not the largest. A bench half is 158mm and a
    # testimony weight is a few mm across; sizing every cell to the bench makes
    # the small parts specks, which is the legibility question this panel
    # exists to answer. Big parts may crowd their cell - that is the right
    # trade, and relative scale stays honest because nothing is rescaled.
    ext = sorted(float(m.extents.max()) for m, _ in best.values())
    pitch = max(ext[len(ext) // 2] * 2.2, 1.0)
    out = []
    for i, (b, (m, colour)) in enumerate(items):
        g = m.copy()
        g.apply_translation(-g.centroid)
        g.apply_translation([(i % cols) * pitch, -(i // cols) * pitch, 0.0])
        out.append((b, g, colour))
    span = cols * pitch / 2
    for _, g, _ in out:                       # recentre the whole grid
        g.apply_translation([-span + pitch / 2, span - pitch / 2, 0.0])
    return out


def render(out_dir: Path, hero: bool = False) -> Path:
    """hero=True renders ONE large iso view instead of the 4-view sheet.

    The contact sheet is for the coherence lens, which is asked to judge the
    product from several angles. It is the wrong input for the video chain: an
    i2i pass over four panels produces a photoreal four-panel poster, and
    animating that is not a how-to.
    """
    parts = load(out_dir)
    named = {base_name(s) for s, _, _ in parts}
    missing = named - set(part_colours(out_dir))
    if missing:
        # Loud, because a part rendering in the fallback grey is exactly the
        # "the palette did not survive" finding, and it is ours not the design's.
        print(f"  WARNING: no colour for {sorted(missing)} - drawn grey", flush=True)

    allv = np.vstack([m.vertices for _, m, _ in parts])
    lo, hi = allv.min(axis=0), allv.max(axis=0)
    mid, span = (lo + hi) / 2, (hi - lo).max() / 2 * 1.05

    views = (HERO_VIEW,) if hero else VIEWS
    # The assembled views, then ONE panel of the distinct parts spread out.
    panels = ([(HERO_VIEW, parts)] if hero else
              [(v, parts) for v in VIEWS]
              + [(("parts", 62, -90), distinct_parts(parts))])
    rows, cols_ = (1, 1) if hero else (2, 3)
    fig = plt.figure(figsize=(16, 9) if hero else (24, 16), facecolor="#12151A")
    for i, ((name, elev, azim), drawn) in enumerate(panels, 1):
        ax = fig.add_subplot(rows, cols_, i, projection="3d", facecolor="#12151A")
        if not drawn:
            ax.set_axis_off()
            continue
        allv_p = np.vstack([m.vertices for _, m, _ in drawn])
        lo_p, hi_p = allv_p.min(axis=0), allv_p.max(axis=0)
        mid_p, span_p = (lo_p + hi_p) / 2, (hi_p - lo_p).max() / 2 * 1.05
        for _, m, colour in drawn:
            tris = m.vertices[m.faces]
            # Flat shading by face normal: without it every part is one
            # silhouette and the assembly reads as a blob.
            n = m.face_normals @ np.array([0.35, 0.45, 0.82])
            # Ambient floor: this palette is deliberately charcoal and
            # blue-grey, so a physically-honest lamp term renders the whole
            # machine near-black and the one signal colour that must be
            # findable - the chartreuse wedge - disappears with it.
            shade = 0.62 + 0.38 * np.clip(n, 0, 1)
            rgb = np.array([int(colour[j:j + 2], 16) / 255 for j in (1, 3, 5)])
            ax.add_collection3d(Poly3DCollection(
                tris, facecolors=shade[:, None] * rgb, linewidths=0, alpha=1.0))
        ax.set_xlim(mid_p[0] - span_p, mid_p[0] + span_p)
        ax.set_ylim(mid_p[1] - span_p, mid_p[1] + span_p)
        ax.set_zlim(mid_p[2] - span_p, mid_p[2] + span_p)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        if not hero:
            ax.set_title(name, color="#E8E6E1", fontsize=20, pad=0)

    dst = out_dir / "renders" / ("hero.png" if hero else "assembled.png")
    dst.parent.mkdir(exist_ok=True)
    fig.subplots_adjust(left=0, right=1, top=0.97, bottom=0, wspace=0, hspace=0)
    fig.savefig(dst, dpi=90, facecolor="#12151A")
    plt.close(fig)
    print(f"  {len(parts)} solids -> {dst}", flush=True)
    return dst


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    render(Path(sys.argv[1]).resolve(), hero="--hero" in sys.argv)
