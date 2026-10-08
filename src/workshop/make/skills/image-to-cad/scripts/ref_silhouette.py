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
                chroma_tol: float = CHROMA_TOL, tint_sat: float = TINT_SAT) -> np.ndarray:
    """Pixels that look like the ground, by the chosen rule (not yet connected)."""
    rgb = rgb.astype(float)
    lum = rgb.mean(2)
    if ground == "tint":
        hi = rgb.max(2)
        return hi - rgb.min(2) <= tint_sat * np.maximum(hi, 1.0)
    if ground == "band":
        sat = rgb.max(2) - rgb.min(2)
        return (sat <= sat_max) & (lum >= lum_lo) & (lum <= lum_hi)
    ring = _border(lum.shape)
    cr, cb = rgb[..., 0] - rgb[..., 1], rgb[..., 2] - rgb[..., 1]
    c0 = np.median(cr[ring]), np.median(cb[ring])
    near = np.hypot(cr - c0[0], cb - c0[1]) <= chroma_tol
    return near & (lum >= np.percentile(lum[ring], 1) - LUM_DROP)


def flatten(rgb: np.ndarray, sat_max: float = SAT_MAX,
            lum_lo: float = LUM_LO, lum_hi: float = LUM_HI,
            ground: str = "band", chroma_tol: float = CHROMA_TOL,
            tint_sat: float = TINT_SAT) -> np.ndarray:
    """Boolean object mask: everything not connected-to-the-border ground."""
    if ground == "auto":
        ground = pick_ground(rgb, sat_max, lum_lo, lum_hi)
    ground_like = ground_mask(rgb, ground, sat_max, lum_lo, lum_hi, chroma_tol, tint_sat)
    lum = rgb.mean(2)
    lab, _ = ndimage.label(ground_like)
    edge = np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    border = set(int(v) for v in np.unique(edge) if v)
    obj = ~np.isin(lab, list(border)) if border else np.ones(lum.shape, bool)
    obj = ndimage.binary_opening(obj, np.ones((3, 3)))
    obj = ndimage.binary_closing(obj, np.ones((5, 5)))
    obj = ndimage.binary_fill_holes(obj)
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
        chroma_tol=CHROMA_TOL, tint_sat=TINT_SAT):
    records = []
    for p in paths:
        rgb = np.asarray(Image.open(p).convert("RGB"))
        rule = pick_ground(rgb, sat_max, band[0], band[1]) if ground == "auto" else ground
        obj = flatten(rgb, sat_max, band[0], band[1], rule, chroma_tol, tint_sat)
        ys, xs = np.nonzero(obj)
        tool = _tool_mask(p, threshold)
        ty, tx = np.nonzero(tool)
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


def self_check() -> int:
    ok = True
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
    ap.add_argument("-o", "--out", help="directory for the flattened files "
                                        "(default: beside each source)")
    ap.add_argument("--suffix", default=SUFFIX)
    ap.add_argument("--sat-max", type=float, default=SAT_MAX,
                    help="a ground pixel is this neutral or more (default 20)")
    ap.add_argument("--lum-band", default=f"{LUM_LO},{LUM_HI}",
                    help="ground luminance band LO,HI (default 66,212)")
    ap.add_argument("--ground", choices=("auto", "band", "border", "tint"), default="auto",
                    help="ground rule: band (neutral, mid luminance), border (chroma "
                         "of the frame border), tint (low relative saturation at any "
                         "luminance: a coloured subject in its own dark contact "
                         "shadow), or auto (default: band unless the border fails it)")
    ap.add_argument("--tint-sat", type=float, default=TINT_SAT,
                    help="tint rule: ground relative saturation (max-min)/max at most "
                         "this (default 0.34)")
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
    if a.out:
        Path(a.out).mkdir(parents=True, exist_ok=True)
    records = run(a.images, a.out, a.suffix, a.sat_max, band, a.threshold,
                  a.ground, a.chroma_tol, a.tint_sat)

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
