#!/usr/bin/env python
"""Flatten a reference image to a clean silhouette the likeness gate can read.

`check_likeness.py` scores the model against a silhouette pulled out of the
reference by `measure_image.py`'s mask.  That mask is a luminance threshold
around an estimated background, plus a chromatic shadow test and a chromatic
two-sided rescue -- and a **studio render of a multi-colour object on a neutral
ground defeats it from both sides at once**:

  * at the default threshold the mask punches **holes** in the object.  Every
    region whose luma sits inside the threshold band is dropped: a white shaft
    end, a signature, the specular highlight on a bore wall or a barb.  The
    reference then measures 10-26 % holey and the model is scored against a
    perforated target.
  * lower the threshold and the holes close, but the soft **cast shadow** comes
    in.  Shadow rejection is chromatic, so on a grey object over a grey ground
    it has nothing to work with, and the shadow adds material under the subject
    that reads as "the model is too small".

Measured on one such reference set, on geometry that did not change:

    reference   mask @28   mask @14   flattened
    front         0.784      0.849      0.945
    hero          0.787      0.787      0.916
    iso           0.787      0.809      0.890

That is the difference between "this model is 20 % wrong" and "this model is
right", reported by the same gate about the same solid.

THE TELL, before you spend a round chasing a shape defect that is not there:
run `render_views.py --match` against several genuinely different viewpoints.
If it recovers nearly the **same azimuth** for all of them, the mask is wrong,
not the model -- the search is fitting the reference's holes, not its outline.
With the flattened references above the same search recovered -88 deg, -71 deg
and -116 deg: head-on for the front frame and about +/-24 deg for the two 3/4
views, which is what those images are.

THE RULE, which knows nothing about the model:

    ground-like  = low saturation AND mid luminance
    background   = the ground-like pixels CONNECTED TO THE FRAME BORDER
    object       = everything else, holes filled, largest blob kept

A cast shadow is ground-like and reaches the border, so it goes.  A specular
highlight is ground-like but enclosed by the subject, so it stays.  Nothing is
drawn, moved or smoothed: the outline is exactly the set of pixels the image
did not leave at ground colour.

Filling holes has a price: a real through-opening (a handle loop, a window in a
frame) is filled along with the highlights, because enclosure is all the rule
can see.  So every file written here carries `check_likeness.HOLES_KEY` in its
PNG text chunk, and the gate fills the render's holes too when it finds it.
Without that mark the correct opening scored as missing material and deleting
it raised the IoU.  The openings then leave the silhouette gate entirely; give
each one a landmark-ledger row.

A LIGHT GROUND IS A SECOND RULE.  A near-white subject on a near-white sweep
(cream plastic on pale grey) leaves the ground above the luminance band, so
nothing is ground-like and the whole frame comes back as the object; and the
subject's own white sits at the ground's luminance and saturation, so widening
the band eats it.  What still separates them is the *direction* of their tint
-- a warm white against a cool grey differs by a few units of chroma, of
opposite sign, that saturation (max - min) throws away.  `--ground border`
reads the ground's chroma (R-G, B-G) off the frame border and calls a pixel
ground-like when its own chroma lies within `--chroma-tol` of it and it is no
darker than the border's darkest by more than `LUM_DROP` (a contact shadow
stays ground, a black part stays object).  The tolerance sits just above the
JPEG chroma step: a flat ground scatters to sqrt(10) = 3.16 from its median,
so a tolerance of 3.0 left a maze of ground pixels standing as object, which
the closing then glued to the outline.  The chroma is not smoothed -- a mean
grew the object 2 px into the ground and took the shadow beside it along.  `--ground auto`, the default, uses the band
rule while the border itself is ground-like by it, and the border rule when it
is not -- the case where the band rule cannot see the ground at all.  The
record says which rule ran.

A COLOURED SUBJECT IN ITS OWN CONTACT SHADOW IS A THIRD RULE.  A brown, red or
green part photographed on a pale sweep under a key light throws a contact
shadow that is dark: far darker than the border, so the border rule's
`LUM_DROP` keeps it as object, and below the band rule's luminance floor, so
the band rule keeps it too.  Both outlines then carry a crescent of shadow
along every edge facing away from the light -- measured 10-15 % of the area on
one oblique product shot, which reads as "the model is too thin" on every
lower edge.  What the shadow never has is the subject's *tint relative to its
own brightness*: `--ground tint` calls a pixel ground-like when its relative
saturation (max - min) / max is at or under `--tint-sat`, at any luminance.
On that shot the subject sat at 0.46-0.77 (lit face to deepest groove) and
every shadow pixel at 0.31 or under.  A neutral subject (grey, white, black,
chrome) has no tint to keep and is lost: use band or border there.

The default is a measured split, not a constant: read both sides before you
trust it.  A dark, low-chroma subject sits close to it -- a forest-green part
measured 0.35 on its lit face and 0.30-0.41 down its walls, and the default
0.34 kept only a tenth of it -- while its grey contact shadow stayed at 0.15
and the ground at 0.06.  `--tint-sat` midway between the subject's darkest
lit tone and the shadow's most tinted pixel (0.2 there) brought the outline
back to a 2 px median against the tool mask.  The record's
`outline_agreement` says which way it went: a flattened area that is a
fraction of the tool mask's is a subject the rule called ground.

A NEUTRAL SUBJECT ON A TINTED GROUND IS A FOURTH RULE, the tint rule turned
inside out.  A grey part on a cream sweep: the subject is the neutral thing
(relative saturation 0.02-0.06) and the ground and its warm contact shadow
are the tinted ones (0.10-0.30), so the tint rule would keep the shadow and
drop the subject.  `--ground neutral` reads the ground's chroma direction off
the frame border and calls a pixel ground-like when it is tinted that way by
at least `--neutral-frac` of the border's own tint.  That alone loses the
subject's walls on the side away from the light: lit by bounce off the warm
ground, the lower 10-15 px of a grey wall measured as warm as the shadow
beside it, at the same luminance, and no per-pixel colour rule can split the
two.  What separates them is the **contact crease** -- the thin line, darker
than both, where the wall meets the ground.  A black top-hat of the
luminance (`CREASE_SIZE` px) finds it as a thin valley a broad shadow is not,
the crease is grown `CREASE_GROW` px to close its gaps and used as a barrier
the border flood cannot cross, and the outline is eroded back by the same
amount after the fill.  On the reference that needed it, the tool mask saw 2 %
of the subject, the border rule kept the whole shadow, the colour test alone
lost every shaded wall, and the creased flood followed the contact line to
within a few pixels.  Look at an overlay before trusting it: where the crease
is too faint the flood leaks along the shadow side, and widening
`CREASE_SIZE` to 9 px was what closed it there.

A PASTEL SUBJECT AS UNSATURATED AS ITS SHADOW needs the tint's direction too.
A lilac wall on a cream sweep measured 0.11-0.15 and the sweep's warm contact
shadow 0.13-0.15, so no `--tint-sat` separates them.  `--tint-hue DEG` adds a
second condition to the tint rule: a ground pixel's chroma (R-G, B-G) must
also point within DEG of the border's median direction (pixels with under
`NEUTRAL_CHROMA` of chroma have no direction and stay ground).  The shadow
keeps the ground's warm direction at any brightness; the lilac, pink and
blue parts point elsewhere, and a yellow that points the ground's way is far
too saturated to be ground.  `--tint-sat 0.25 --tint-hue 30` held every wall
of a four-colour pastel render and dropped every shadow pixel.

A SUBJECT LIT TO THE GROUND'S OWN COLOUR is a fifth rule.  A white robot on a
pure white page (a maker's CG render): its lit faces are 255, 255, 255 like
the page, the rest of it is neutral grey, and every colour rule calls those
faces ground -- the tool mask saw 10 % of the outline, `border` kept 70 %
and dropped every top face that met the page.  What still separates them is
the outline itself: a renderer draws each face's shading up to its edge, so
the subject's silhouette is a line of luminance gradient even where both
sides are white.  `--ground edge` calls a pixel ground-like when it is within
`EDGE_TOL` of the border's colour on every channel, neutral, and not on a
gradient wall (Sobel magnitude over `EDGE_GRAD`, grown 1 px); the border
flood cannot cross the walls, and after the flood the ground takes back the
ground-coloured wall pixels next to it (`EDGE_GROW` px), so the outline is not
fattened by the wall.  Text printed on the page stays a separate blob and the
largest blob is kept.  Look at the `-sil.png` before scoring: a face drawn
with no shading step at its silhouette leaks, and the leak is visible.

The edge rule has one failure in the other direction.  A soft contact shadow
has no shading step, but it is darker than the page by more than `EDGE_TOL`,
so the flood will not enter it either; where it runs under two feet it joins
them, the gap between the legs is enclosed, and filling holes fills it.  The
front view of a standing figure then scores its legs as one block.  On a white
CG turnaround the shadow sat 5-18 levels under the page and the armour's lit
faces met the page through a shading step; `--edge-tol 12` opened the gap and
dropped the shadow, and took nothing from the subject but its 1 px antialiased
rim.  Raise it only as far as the gap needs, and look at the result.

This is the same remedy the skill already prescribes for line art -- make the
reference measurable, then measure it with the *unchanged* instrument.  It is a
script rather than a per-project probe so that every project flattens the same
way and the numbers stay comparable.

    python ref_silhouette.py ref/*.png                 # writes ref/<stem>-sil.png
    python ref_silhouette.py ref/hero.png -o tmp/
    python ref_silhouette.py ref/hero.png --json
    python ref_silhouette.py --self-check

Then point the gate at the flattened files and keep the originals:

    render_views.py <src> --match ref/hero-sil.png --label hero -o snap/
    check_likeness.py --pair snap/hero.png ref/hero-sil.png --min 0.90

WHAT IT DOES NOT DO.  It cannot separate a subject from a *cluttered* or
textured background -- the whole rule rests on the ground being one flat
colour, which is what a studio render gives you and a photo in the wild does
not.  It cannot recover a subject region that the renderer drew at exactly the
ground colour and left touching the frame edge.  And it says nothing about
whether the outline is the right shape: that is the gate's job, and this only
makes the gate's question answerable.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_likeness import HOLES_FILLED, HOLES_KEY  # noqa: E402

SAT_MAX = 20            # a ground pixel is neutral
LUM_LO, LUM_HI = 66, 212
CHROMA_TOL = 3.5        # border rule: ground chroma distance; JPEG scatters a flat ground to 3.16
LUM_DROP = 60           # border rule: a ground pixel is at most this much darker than the border's darkest
TINT_SAT = 0.34         # tint rule: a ground pixel's (max - min) / max is at most this, at any luminance
TINT_HUE = 0.0          # tint rule: when > 0, a ground pixel's chroma direction is also within this many degrees of the border's
NEUTRAL_CHROMA = 6.0    # tint-hue: a pixel with less chroma than this has no direction and stays ground
NEUTRAL_FRAC = 0.8      # neutral rule: a ground pixel is tinted the border's way by at least this share of its tint
CREASE_SIZE = 9         # neutral rule: black top-hat window that finds the thin contact crease
CREASE_DEPTH = 10       # neutral rule: a crease pixel is this much darker than its closing
CREASE_GROW = 2         # neutral rule: px the crease barrier is grown to close gaps (outline eroded back after)
EDGE_TOL = 5           # edge rule: a ground pixel is within this of the border's colour, per channel
EDGE_GRAD = 6.0        # edge rule: Sobel magnitude / 8 above this is an outline wall the flood stops at
EDGE_GROW = 2          # edge rule: px the ground takes back over ground-coloured wall pixels
BORDER_PX = 8
SUFFIX = "-sil"
VERIFY_FRACTION = 0.66  # rows a contact shadow cannot reach
VERIFY_MEDIAN_PX = 6.0


def _border(shape) -> np.ndarray:
    ring = np.zeros(shape, bool)
    ring[:BORDER_PX] = ring[-BORDER_PX:] = True
    ring[:, :BORDER_PX] = ring[:, -BORDER_PX:] = True
    return ring


def pick_ground(rgb: np.ndarray, sat_max: float = SAT_MAX,
                lum_lo: float = LUM_LO, lum_hi: float = LUM_HI) -> str:
    """`band` while the border is ground-like by the band rule, else `border`."""
    rgb = rgb.astype(int)
    ring = _border(rgb.shape[:2])
    lum, sat = rgb.mean(2)[ring], (rgb.max(2) - rgb.min(2))[ring]
    seen = (sat <= sat_max) & (lum >= lum_lo) & (lum <= lum_hi)
    return "band" if seen.mean() >= 0.5 else "border"


def ground_mask(rgb: np.ndarray, ground: str, sat_max: float = SAT_MAX,
                lum_lo: float = LUM_LO, lum_hi: float = LUM_HI,
                chroma_tol: float = CHROMA_TOL, tint_sat: float = TINT_SAT,
                neutral_frac: float = NEUTRAL_FRAC, tint_hue: float = TINT_HUE,
                edge_tol: float = EDGE_TOL) -> np.ndarray:
    """Pixels that look like the ground, by the chosen rule (not yet connected)."""
    rgb = rgb.astype(float)
    lum = rgb.mean(2)
    if ground == "tint":
        hi = rgb.max(2)
        low = hi - rgb.min(2) <= tint_sat * np.maximum(hi, 1.0)
        if tint_hue <= 0:
            return low
        # a pastel subject can be as unsaturated as the warm shadow it sits in;
        # what it never shares is the direction of the ground's tint
        cr, cb = rgb[..., 0] - rgb[..., 1], rgb[..., 2] - rgb[..., 1]
        ring = _border(lum.shape)
        a0 = np.arctan2(np.median(cb[ring]), np.median(cr[ring]))
        turn = np.abs((np.arctan2(cb, cr) - a0 + np.pi) % (2 * np.pi) - np.pi)
        neutral = np.hypot(cr, cb) < NEUTRAL_CHROMA
        return low & (neutral | (turn <= np.radians(tint_hue)))
    if ground == "neutral":
        tinted, barrier = _neutral_ground(rgb, neutral_frac)
        return tinted & ~barrier
    if ground == "edge":
        return _edge_colour(rgb, edge_tol) & ~_edge_walls(rgb)
    if ground == "band":
        sat = rgb.max(2) - rgb.min(2)
        return (sat <= sat_max) & (lum >= lum_lo) & (lum <= lum_hi)
    ring = _border(lum.shape)
    cr, cb = rgb[..., 0] - rgb[..., 1], rgb[..., 2] - rgb[..., 1]
    c0 = np.median(cr[ring]), np.median(cb[ring])
    near = np.hypot(cr - c0[0], cb - c0[1]) <= chroma_tol
    return near & (lum >= np.percentile(lum[ring], 1) - LUM_DROP)


def _neutral_ground(rgb: np.ndarray, neutral_frac: float) -> np.ndarray:
    """(tinted the border's way, the grown contact crease the flood may not cross)."""
    lum, hi = rgb.mean(2), np.maximum(rgb.max(2), 1.0)
    chroma = np.stack([rgb[..., 0] - rgb[..., 1], rgb[..., 2] - rgb[..., 1]], -1) / hi[..., None]
    ring = _border(lum.shape)
    c0 = np.median(chroma[ring], axis=0)
    norm = float(np.hypot(*c0))
    if norm < 1e-3:
        raise ValueError("neutral rule: the border has no tint to follow; use band or border")
    along = chroma @ (c0 / norm)
    tinted = along >= neutral_frac * norm
    crease = (ndimage.black_tophat(lum, size=CREASE_SIZE) > CREASE_DEPTH) & tinted
    return tinted, ndimage.binary_dilation(crease, iterations=CREASE_GROW)


def _edge_colour(rgb: np.ndarray, tol: float = EDGE_TOL) -> np.ndarray:
    """Edge rule: pixels the border's own colour, within `tol` per channel."""
    ring = _border(rgb.shape[:2])
    c0 = np.median(rgb[ring], axis=0)
    return (np.abs(rgb - c0) <= tol).all(axis=2)


def _edge_walls(rgb: np.ndarray) -> np.ndarray:
    """Edge rule: the luminance-gradient lines the border flood may not cross."""
    lum = rgb.mean(2)
    grad = np.hypot(ndimage.sobel(lum, 1), ndimage.sobel(lum, 0)) / 8.0
    return ndimage.binary_dilation(grad > EDGE_GRAD, iterations=1)


def flatten(rgb: np.ndarray, sat_max: float = SAT_MAX,
            lum_lo: float = LUM_LO, lum_hi: float = LUM_HI,
            ground: str = "band", chroma_tol: float = CHROMA_TOL,
            tint_sat: float = TINT_SAT, neutral_frac: float = NEUTRAL_FRAC,
            tint_hue: float = TINT_HUE, edge_tol: float = EDGE_TOL) -> np.ndarray:
    """Boolean object mask: everything not connected-to-the-border ground."""
    if ground == "auto":
        ground = pick_ground(rgb, sat_max, lum_lo, lum_hi)
    ground_like = ground_mask(rgb, ground, sat_max, lum_lo, lum_hi, chroma_tol, tint_sat,
                              neutral_frac, tint_hue, edge_tol)
    lum = rgb.mean(2)
    lab, _ = ndimage.label(ground_like)
    edge = np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    border = set(int(v) for v in np.unique(edge) if v)
    obj = ~np.isin(lab, list(border)) if border else np.ones(lum.shape, bool)
    if ground == "edge":    # take back the ground-coloured wall pixels beside the ground
        colour = _edge_colour(rgb.astype(float), edge_tol)
        obj &= ~(ndimage.binary_dilation(~obj, iterations=EDGE_GROW) & colour)
    obj = ndimage.binary_opening(obj, np.ones((3, 3)))
    obj = ndimage.binary_closing(obj, np.ones((5, 5)))
    obj = ndimage.binary_fill_holes(obj)
    if ground == "neutral":  # give back the px the crease barrier was grown by, only there
        barrier = _neutral_ground(rgb.astype(float), neutral_frac)[1]
        obj = np.where(barrier, ndimage.binary_erosion(obj, iterations=CREASE_GROW), obj)
    lab2, n2 = ndimage.label(obj)
    if n2 > 1:
        sizes = ndimage.sum(obj, lab2, range(1, n2 + 1))
        obj = lab2 == (int(np.argmax(sizes)) + 1)
    return obj


def _tool_mask(path: Path, threshold: float):
    """The mask `check_likeness` would use, for the outline comparison."""
    import check_likeness as CL
    return CL.silhouette(path, threshold)


def save_flattened(obj: np.ndarray, target: Path) -> None:
    """Write the mask with the holes-filled mark the likeness gate reads."""
    info = PngInfo()
    info.add_text(HOLES_KEY, HOLES_FILLED)
    Image.fromarray(np.where(obj, 0, 255).astype(np.uint8)).save(target, pnginfo=info)


COMPARABLE_COVER = 0.5   # the tool's mask must see this much of the outline to judge it


def verify(obj: np.ndarray, tool: np.ndarray) -> dict:
    """How far the flattened outline sits from the tool's own, above the shadow.

    When the tool's own mask sees under half the flattened outline -- a white
    subject on a white ground, the case the border rule exists for -- its
    outline is not evidence either way: say so, rather than fail on a
    comparison with a mask that is known to be blind. An outline that reaches
    the frame edge is a failed flatten whatever the comparison says.
    """
    # within 3 px: the closing's erosion pulls a full-frame mask 2 px off the edge
    m = 3
    edge = bool(obj[:m].any() or obj[-m:].any() or obj[:, :m].any() or obj[:, -m:].any())
    cover = float((obj & tool).sum() / max(int(obj.sum()), 1))
    if edge:
        return {"rows": 0, "median_px": None, "p95_px": None, "ok": False,
                "comparable": True, "tool_cover": round(cover, 3),
                "reason": "the outline reaches the frame edge: the ground was not found"}
    if cover < COMPARABLE_COVER:
        return {"rows": 0, "median_px": None, "p95_px": None, "ok": True,
                "comparable": False, "tool_cover": round(cover, 3),
                "reason": f"the tool's mask sees {cover:.0%} of the outline: not comparable, "
                          "check the flattened file by eye"}
    ys, _ = np.nonzero(obj)
    top = ys.min() + int(VERIFY_FRACTION * (ys.max() - ys.min()))
    deltas = []
    for y in range(ys.min() + 4, top):
        a, b = np.nonzero(obj[y])[0], np.nonzero(tool[y])[0]
        if a.size and b.size:
            deltas += [abs(int(a.min()) - int(b.min())),
                       abs(int(a.max()) - int(b.max()))]
    if not deltas:
        return {"rows": 0, "median_px": None, "p95_px": None, "ok": False,
                "comparable": True, "tool_cover": round(cover, 3)}
    return {"rows": top - ys.min() - 4,
            "median_px": round(float(np.median(deltas)), 1),
            "p95_px": round(float(np.percentile(deltas, 95)), 1),
            "ok": bool(np.median(deltas) <= VERIFY_MEDIAN_PX),
            "comparable": True, "tool_cover": round(cover, 3)}


def run(paths, out_dir, suffix, sat_max, band, threshold, ground="auto",
        chroma_tol=CHROMA_TOL, tint_sat=TINT_SAT, neutral_frac=NEUTRAL_FRAC,
        tint_hue=TINT_HUE, edge_tol=EDGE_TOL):
    records = []
    for p in paths:
        rgb = np.asarray(Image.open(p).convert("RGB"))
        rule = pick_ground(rgb, sat_max, band[0], band[1]) if ground == "auto" else ground
        obj = flatten(rgb, sat_max, band[0], band[1], rule, chroma_tol, tint_sat, neutral_frac,
                      tint_hue, edge_tol)
        ys, xs = np.nonzero(obj)
        tool = _tool_mask(p, threshold)
        ty, tx = np.nonzero(tool)
        if out_dir and Path(out_dir).suffix.lower() == ".png":
            target = Path(out_dir)
        else:
            target = (Path(out_dir) if out_dir else p.parent) / f"{p.stem}{suffix}.png"
        save_flattened(obj, target)
        records.append({
            "source": str(p), "output": str(target), "ground": rule,
            "flattened": {"bbox": [int(xs.min()), int(ys.min()),
                                   int(xs.max()), int(ys.max())],
                          "area_px": int(obj.sum())},
            "tool_mask": {"threshold": threshold,
                          "bbox": [int(tx.min()), int(ty.min()),
                                   int(tx.max()), int(ty.max())],
                          "area_px": int(tool.sum())},
            "outline_agreement": verify(obj, tool),
        })
    return records


def _fixture():
    """A grey subject on a grey ground: attached cast shadow, enclosed highlight."""
    img = np.full((200, 240, 3), 150, np.uint8)
    img[130:160, 40:210] = 118          # soft cast shadow, reaches the border
    img[50:150, 70:170] = 45            # the subject
    img[85:105, 100:140] = 235          # specular highlight, enclosed
    img[60:80, 80:100] = 150            # mid-tone region AT ground luminance
    return img


def _light_fixture():
    """A warm white subject on a cool light ground of the same luminance."""
    img = np.zeros((200, 240, 3), np.uint8)
    img[:] = (229, 229, 233)            # cool pale-grey sweep
    img[150:175, 30:215] = (196, 196, 199)  # contact shadow, reaches the border? no: below
    img[150:175, 0:30] = (196, 196, 199)    # ... it does now
    img[40:150, 60:180] = (233, 229, 226)   # warm white subject at ground luminance
    img[60:90, 70:110] = (46, 45, 46)       # a black inlay inside it
    img[130:150, 60:180] = (200, 195, 190)  # its shaded lower edge
    return img


def _tinted_fixture():
    """A brown subject on a pale warm sweep, in its own dark neutral contact shadow."""
    img = np.zeros((200, 240, 3), np.uint8)
    img[:] = (240, 237, 232)                 # pale warm sweep, above the band rule's ceiling
    img[150:170, 0:200] = (175, 165, 155)    # soft shadow, reaches the border
    img[40:150, 60:180] = (128, 88, 69)      # the lit brown face
    img[130:150, 60:180] = (89, 56, 37)      # its wall, darker but still brown
    img[139:141, 60:180] = (47, 24, 11)      # a groove round the wall, darkest
    img[60:70, 80:120] = (183, 139, 115)     # a highlight on the face, least saturated part
    img[150:160, 70:190] = (78, 66, 54)      # dark contact shadow hugging the lower edge
    img[40:150, 180:192] = (91, 79, 67)      # ... and the edge facing away from the light
    return img


def _neutral_fixture():
    """A grey subject on a cream sweep: warm-bounced lower wall, dark crease, warm shadow."""
    img = np.zeros((200, 240, 3), np.uint8)
    img[:] = (252, 243, 226)                 # cream sweep
    img[150:185, 0:215] = (193, 178, 151)    # warm contact shadow, reaches the border
    img[40:150, 60:180] = (209, 208, 204)    # the lit grey face
    img[135:150, 60:180] = (175, 163, 141)   # lower wall in bounce light: as warm as the shadow
    img[150:152, 58:182] = (142, 127, 97)    # the contact crease, darker than both,
    img[135:152, 58:60] = img[135:152, 180:182] = (142, 127, 97)  # round the wall's ends
    img[60:80, 80:100] = (240, 160, 165)     # a pink inlay inside it
    return img


def _pastel_fixture():
    """A lilac subject on a cream sweep, in a warm shadow just as unsaturated."""
    img = np.zeros((200, 240, 3), np.uint8)
    img[:] = (248, 239, 222)                 # cream sweep, rel. saturation 0.10
    img[150:170, 0:200] = (222, 208, 189)    # warm contact shadow, 0.15, reaches the border
    img[40:150, 60:180] = (218, 192, 227)    # lilac lit face, 0.15
    img[130:150, 60:180] = (206, 183, 205)   # its shaded wall, 0.11
    return img


def _white_fixture():
    """A white subject on a white page: its lit top face IS the page's colour,
    only the shading step at its outline tells them apart; text on the page."""
    img = np.full((200, 240, 3), 255, np.uint8)
    img[40:150, 60:180] = (236, 236, 238)   # the subject's side face, neutral grey
    img[40:90, 60:180] = (255, 255, 255)    # its lit top face: exactly the page
    img[39, 58:182] = img[150, 58:182] = (205, 205, 207)   # the renderer's shading step
    img[39:151, 58:60] = img[39:151, 180:182] = (205, 205, 207)
    img[89:91, 60:180] = (220, 220, 222)    # the edge between top and side faces
    img[170:178, 10:60] = (40, 40, 40)      # a line of text on the page
    return img


def self_check() -> int:
    ok = True
    white = _white_fixture()
    truth = np.zeros(white.shape[:2], bool)
    truth[39:151, 58:182] = True
    got = flatten(white, ground="edge")
    iou = (got & truth).sum() / (got | truth).sum()
    lost = flatten(white, ground="border")
    hit = iou >= 0.95 and (lost & truth).sum() < 0.8 * truth.sum()
    ok &= hit
    print(f"{'ok  ' if hit else 'FAIL'} edge rule holds a white subject whose lit face is the "
          f"page's colour (IoU {iou:.3f}); the border rule loses it "
          f"({(lost & truth).sum() / truth.sum():.0%} kept)")
    # two white legs standing in one soft contact shadow: the default tolerance
    # calls the shadow subject, so the gap between the legs is enclosed and
    # filled; a wider tolerance lets the flood through the shadow
    legs = np.full((200, 240, 3), 255, np.uint8)
    legs[20:60, 48:192] = (236, 236, 238)        # the hips the two legs hang from
    legs[19, 46:194] = (205, 205, 207)
    legs[19:61, 46:48] = legs[19:61, 192:194] = (205, 205, 207)
    for x0 in (50, 140):
        legs[40:170, x0:x0 + 50] = (236, 236, 238)
        legs[170, x0 - 2:x0 + 52] = (205, 205, 207)
        legs[60:171, x0 - 2:x0] = legs[60:171, x0 + 50:x0 + 52] = (205, 205, 207)
    legs[60, 100:140] = (205, 205, 207)          # the crotch
    for k in range(12):                          # the shadow: soft, 6-12 under the page
        legs[171 + k, 30:220] = 255 - 12 + abs(k - 6)
    gap = np.zeros(legs.shape[:2], bool)
    gap[62:165, 106:134] = True
    sealed = int((flatten(legs, ground="edge") & gap).sum())
    opened = int((flatten(legs, ground="edge", edge_tol=14) & gap).sum())
    good = sealed > 0.9 * gap.sum() and opened == 0
    print(f"{'ok  ' if good else 'FAIL'} a soft contact shadow under two legs seals the gap "
          f"at the default tolerance ({sealed} px filled) and --edge-tol 14 opens it "
          f"({opened} px)")
    ok &= good

    img = _fixture()
    obj = flatten(img)
    subject = np.zeros(img.shape[:2], bool)
    subject[50:150, 70:170] = True

    missed = int((subject & ~obj).sum())
    print(f"{'ok  ' if missed == 0 else 'FAIL'} the subject survives whole "
          f"-- highlight and ground-luma region kept ({missed} px missing)")
    ok &= missed == 0

    shadow = np.zeros(img.shape[:2], bool)
    shadow[130:160, 40:210] = True
    shadow &= ~subject
    leaked = int((shadow & obj).sum())
    print(f"{'ok  ' if leaked == 0 else 'FAIL'} the attached cast shadow is "
          f"rejected ({leaked} px leaked)")
    ok &= leaked == 0

    # and the thing this exists to beat: a plain luma threshold low enough to
    # keep the highlight also keeps the shadow.
    lum = img.astype(int).mean(2)
    naive = np.abs(lum - 150) > 14
    naive_leak = int((shadow & naive).sum())
    print(f"{'ok  ' if naive_leak > 0 else 'FAIL'} a luma threshold that keeps "
          f"the highlight leaks the shadow ({naive_leak} px) -- which is why "
          f"this is not a threshold")
    ok &= naive_leak > 0

    ys, xs = np.nonzero(obj)
    tight = (ys.min(), ys.max(), xs.min(), xs.max()) == (50, 149, 70, 169)
    print(f"{'ok  ' if tight else 'FAIL'} the outline is not moved: bbox "
          f"y{ys.min()}..{ys.max()} x{xs.min()}..{xs.max()} (want y50..149 x70..169)")
    ok &= tight

    # a light ground: the band rule cannot see it and returns the whole frame;
    # auto must notice and switch to the border rule, which keeps the white
    # subject and its black inlay and drops the neutral shadow
    light = _light_fixture()
    lsub = np.zeros(light.shape[:2], bool)
    lsub[40:150, 60:180] = True
    lshadow = np.zeros(light.shape[:2], bool)
    lshadow[150:175, 0:215] = True
    band_obj = flatten(light)
    blind = band_obj.mean() > 0.5
    print(f"{'ok  ' if blind else 'FAIL'} the band rule cannot see a light ground "
          f"(object covers {band_obj.mean():.0%} of the frame)")
    ok &= blind
    rule = pick_ground(light)
    lobj = flatten(light, ground="auto")
    lmiss, lleak = int((lsub & ~lobj).sum()), int((lshadow & lobj).sum())
    lys, lxs = np.nonzero(lobj)
    ltight = (lys.min(), lys.max(), lxs.min(), lxs.max()) == (40, 149, 60, 179)
    good = rule == "border" and lmiss == 0 and lleak == 0 and ltight
    print(f"{'ok  ' if good else 'FAIL'} auto picks the border rule ({rule}) for a warm "
          f"white on a cool light ground: {lmiss} px missing, {lleak} px of shadow "
          f"leaked, bbox y{lys.min()}..{lys.max()} x{lxs.min()}..{lxs.max()}")
    ok &= good
    kept = pick_ground(img) == "band"
    print(f"{'ok  ' if kept else 'FAIL'} auto keeps the band rule on a mid-grey ground")
    ok &= kept

    # a brown subject in its own dark contact shadow: band and border both keep
    # the shadow as object (it is darker than either rule's ground); the tint
    # rule drops it and keeps the subject, its groove and its highlight
    tinted = _tinted_fixture()
    tsub = np.zeros(tinted.shape[:2], bool)
    tsub[40:150, 60:180] = True
    tshadow = np.zeros(tinted.shape[:2], bool)
    tshadow[150:160, 70:190] = tshadow[40:150, 180:192] = True
    leaks = {rule: int((tshadow & flatten(tinted, ground=rule)).sum()) for rule in ("band", "border")}
    tobj = flatten(tinted, ground="tint")
    tmiss, tleak = int((tsub & ~tobj).sum()), int((tshadow & tobj).sum())
    tys, txs = np.nonzero(tobj)
    ttight = (tys.min(), tys.max(), txs.min(), txs.max()) == (40, 149, 60, 179)
    good = min(leaks.values()) > 0 and tmiss == 0 and tleak == 0 and ttight
    print(f"{'ok  ' if good else 'FAIL'} a dark contact shadow leaks into band ({leaks['band']} px) "
          f"and border ({leaks['border']} px); the tint rule drops it: {tmiss} px missing, "
          f"{tleak} px leaked, bbox y{tys.min()}..{tys.max()} x{txs.min()}..{txs.max()}")
    ok &= good

    # a neutral subject on a tinted ground: the tint rule keeps the shadow and
    # drops the subject; the neutral rule keeps the warm-bounced wall because
    # the contact crease stops the border flood before it reaches the wall
    neutral = _neutral_fixture()
    nsub = np.zeros(neutral.shape[:2], bool)
    nsub[40:150, 60:180] = True
    nshadow = np.zeros(neutral.shape[:2], bool)
    nshadow[153:185, 0:215] = True
    tint_obj = flatten(neutral, ground="tint")
    tint_bad = int((nsub & ~tint_obj).sum()) > 0
    nobj = flatten(neutral, ground="neutral")
    nmiss, nleak = int((nsub & ~nobj).sum()), int((nshadow & nobj).sum())
    nys, nxs = np.nonzero(nobj)
    near = abs(nys.max() - 150) <= 2 and abs(nys.min() - 40) <= 1 and abs(nxs.min() - 60) <= 2
    good = tint_bad and nmiss == 0 and nleak == 0 and near
    print(f"{'ok  ' if good else 'FAIL'} a grey subject on a cream ground: the tint rule loses it "
          f"({tint_bad}); the neutral rule keeps the bounce-lit wall ({nmiss} px missing, "
          f"{nleak} px of shadow leaked, bbox y{nys.min()}..{nys.max()} x{nxs.min()}..{nxs.max()})")
    ok &= good

    # a pastel subject as unsaturated as its warm shadow: saturation alone
    # cannot split them at any threshold, the direction of the tint can
    pastel = _pastel_fixture()
    psub = np.zeros(pastel.shape[:2], bool)
    psub[40:150, 60:180] = True
    pshadow = np.zeros(pastel.shape[:2], bool)
    pshadow[150:170, 0:200] = True
    plain_obj = flatten(pastel, ground="tint", tint_sat=0.155)
    hue_obj = flatten(pastel, ground="tint", tint_sat=0.155, tint_hue=25)
    plain_bad = int((psub & ~plain_obj).sum()) + int((pshadow & plain_obj).sum())
    pmiss, pleak = int((psub & ~hue_obj).sum()), int((pshadow & hue_obj).sum())
    good = plain_bad > 0 and pmiss == 0 and pleak == 0
    print(f"{'ok  ' if good else 'FAIL'} a lilac subject in a warm shadow of equal saturation: "
          f"saturation alone misreads {plain_bad} px; with --tint-hue {pmiss} px missing, {pleak} px leaked")
    ok &= good

    # the first light reference was written as a full-frame "object" and only
    # the comparison happened to object; an outline at the frame edge must fail
    # on its own, and a comparison with a blind tool mask must not decide
    edge_v = verify(band_obj, np.zeros_like(band_obj))
    blind_v = verify(lobj, lobj & (light.astype(int).mean(2) < 100))
    good = (not edge_v["ok"]) and blind_v["ok"] and not blind_v["comparable"]
    print(f"{'ok  ' if good else 'FAIL'} an outline at the frame edge fails "
          f"({edge_v['ok']}); a tool mask that sees {blind_v['tool_cover']:.0%} of "
          f"the outline is reported not comparable ({blind_v['comparable']})")
    ok &= good

    # the file must say its holes were filled, or the gate scores a filled
    # reference against an unfilled render and pays for deleting openings
    import tempfile
    import check_likeness as CL
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "fixture-sil.png"
        save_flattened(obj, target)
        marked = CL.holes_filled(target)
        plain = Path(tmp) / "plain.png"
        Image.fromarray(img).save(plain)
        unmarked = not CL.holes_filled(plain)
    print(f"{'ok  ' if marked and unmarked else 'FAIL'} the flattened file carries "
          f"the holes-filled mark and an ordinary image does not")
    ok &= marked and unmarked

    # --json has to serialise what run() really returns: numpy ints in every
    # bbox made it crash on the first real image it met
    import contextlib
    import io
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "fixture.png"
        Image.fromarray(img).save(source)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            try:
                main([str(source), "-o", tmp, "--json"])
                parsed = json.loads(out.getvalue())
                emitted = bool(parsed.get("images"))
            except (TypeError, ValueError) as error:
                emitted, parsed = False, error
    print(f"{'ok  ' if emitted else 'FAIL'} --json emits parseable JSON for a real run"
          + ("" if emitted else f": {parsed}"))
    ok &= emitted

    print("\nall fixtures pass" if ok else "\nself-check FAILED")
    return 0 if ok else 1


def _plain(value):
    """numpy scalars and arrays as the JSON numbers and lists they hold: a
    bbox of numpy ints made `--json` crash on every real image."""
    if hasattr(value, "tolist"):
        return value.tolist()
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="*", type=Path)
    ap.add_argument("-o", "--out", help="directory for the flattened files, or one "
                                        "FILE.png when flattening a single image "
                                        "(default: beside each source)")
    ap.add_argument("--suffix", default=SUFFIX)
    ap.add_argument("--sat-max", type=float, default=SAT_MAX,
                    help="a ground pixel is this neutral or more (default 20)")
    ap.add_argument("--lum-band", default=f"{LUM_LO},{LUM_HI}",
                    help="ground luminance band LO,HI (default 66,212)")
    ap.add_argument("--ground", choices=("auto", "band", "border", "tint", "neutral", "edge"),
                    default="auto",
                    help="ground rule: band (neutral, mid luminance), border (chroma "
                         "of the frame border), tint (low relative saturation at any "
                         "luminance: a coloured subject in its own dark contact "
                         "shadow), neutral (a grey/white subject on a tinted ground: "
                         "tinted the border's way, with the contact crease as a "
                         "barrier), edge (a subject lit to the ground's own colour: "
                         "the border's colour, stopped at the outline's shading "
                         "step), or auto (default: band unless the border fails it)")
    ap.add_argument("--neutral-frac", type=float, default=NEUTRAL_FRAC,
                    help="neutral rule: ground-like when tinted the border's way by at "
                         f"least this share of the border's tint (default {NEUTRAL_FRAC})")
    ap.add_argument("--tint-sat", type=float, default=TINT_SAT,
                    help="tint rule: ground relative saturation (max-min)/max at most "
                         "this (default 0.34)")
    ap.add_argument("--tint-hue", type=float, default=TINT_HUE,
                    help="tint rule: also require a ground pixel's chroma direction "
                         "(R-G, B-G) within this many degrees of the border's; 0 "
                         "(default) turns it off. For a pastel subject as unsaturated "
                         "as its warm shadow")
    ap.add_argument("--edge-tol", type=float, default=EDGE_TOL,
                    help="edge rule: a ground pixel is within this of the border's colour "
                         f"per channel (default {EDGE_TOL}). Raise it (about 12) when a soft "
                         "contact shadow, darker than the page but with no shading step, "
                         "joins two feet and seals the gap between the legs")
    ap.add_argument("--chroma-tol", type=float, default=CHROMA_TOL,
                    help="border rule: ground chroma distance (default 3)")
    ap.add_argument("--threshold", type=float, default=28.0,
                    help="the check_likeness threshold to compare the outline against")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args(argv)

    if a.self_check:
        return self_check()
    if not a.images:
        ap.error("give at least one image, or --self-check")
    band = tuple(float(v) for v in a.lum_band.split(","))
    if a.out and Path(a.out).suffix.lower() == ".png":
        if len(a.images) != 1:
            ap.error("-o FILE.png takes exactly one image; give a directory for several")
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    elif a.out:
        Path(a.out).mkdir(parents=True, exist_ok=True)
    records = run(a.images, a.out, a.suffix, a.sat_max, band, a.threshold,
                  a.ground, a.chroma_tol, a.tint_sat, a.neutral_frac, a.tint_hue, a.edge_tol)

    if a.json:
        print(json.dumps(
            {"ok": all(r["outline_agreement"]["ok"] for r in records),
             "images": records},
            separators=(",", ":"),
            ensure_ascii=False,
            default=_plain,
        ))
    else:
        for r in records:
            v = r["outline_agreement"]
            print(f"{Path(r['source']).name}  (ground rule: {r['ground']})")
            print(f"   flattened  area {r['flattened']['area_px']:>7}  "
                  f"bbox {r['flattened']['bbox']}")
            print(f"   tool @{r['tool_mask']['threshold']:<4g} area "
                  f"{r['tool_mask']['area_px']:>7}  bbox {r['tool_mask']['bbox']}")
            if v.get("reason"):
                print(f"   {'note' if v['ok'] else 'FAIL'}: {v['reason']}")
            else:
                print(f"   outline over the top {VERIFY_FRACTION:.0%} of rows: median "
                      f"|dx| {v['median_px']} px, p95 {v['p95_px']} px "
                      f"({'unmoved' if v['ok'] else 'MOVED -- check the band'})")
            print(f"   wrote {r['output']}")
    return 0 if all(r["outline_agreement"]["ok"] for r in records) else 1


if __name__ == "__main__":
    sys.exit(main())
