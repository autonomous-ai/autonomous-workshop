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
from scipy import ndimage

SAT_MAX = 20            # a ground pixel is neutral
LUM_LO, LUM_HI = 66, 212
SUFFIX = "-sil"
VERIFY_FRACTION = 0.66  # rows a contact shadow cannot reach
VERIFY_MEDIAN_PX = 6.0


def flatten(rgb: np.ndarray, sat_max: float = SAT_MAX,
            lum_lo: float = LUM_LO, lum_hi: float = LUM_HI) -> np.ndarray:
    """Boolean object mask: everything not connected-to-the-border ground."""
    rgb = rgb.astype(int)
    lum = rgb.mean(2)
    sat = rgb.max(2) - rgb.min(2)
    ground_like = (sat <= sat_max) & (lum >= lum_lo) & (lum <= lum_hi)
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
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_likeness as CL
    return CL.silhouette(path, threshold)


def verify(obj: np.ndarray, tool: np.ndarray) -> dict:
    """How far the flattened outline sits from the tool's own, above the shadow."""
    ys, _ = np.nonzero(obj)
    top = ys.min() + int(VERIFY_FRACTION * (ys.max() - ys.min()))
    deltas = []
    for y in range(ys.min() + 4, top):
        a, b = np.nonzero(obj[y])[0], np.nonzero(tool[y])[0]
        if a.size and b.size:
            deltas += [abs(int(a.min()) - int(b.min())),
                       abs(int(a.max()) - int(b.max()))]
    if not deltas:
        return {"rows": 0, "median_px": None, "p95_px": None, "ok": False}
    return {"rows": top - ys.min() - 4,
            "median_px": round(float(np.median(deltas)), 1),
            "p95_px": round(float(np.percentile(deltas, 95)), 1),
            "ok": bool(np.median(deltas) <= VERIFY_MEDIAN_PX)}


def run(paths, out_dir, suffix, sat_max, band, threshold):
    records = []
    for p in paths:
        rgb = np.asarray(Image.open(p).convert("RGB"))
        obj = flatten(rgb, sat_max, band[0], band[1])
        ys, xs = np.nonzero(obj)
        tool = _tool_mask(p, threshold)
        ty, tx = np.nonzero(tool)
        target = (Path(out_dir) if out_dir else p.parent) / f"{p.stem}{suffix}.png"
        Image.fromarray(np.where(obj, 0, 255).astype(np.uint8)).save(target)
        records.append({
            "source": str(p), "output": str(target),
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

    print("\nall fixtures pass" if ok else "\nself-check FAILED")
    return 0 if ok else 1


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
    records = run(a.images, a.out, a.suffix, a.sat_max, band, a.threshold)

    if a.json:
        print(json.dumps({"ok": all(r["outline_agreement"]["ok"] for r in records),
                          "images": records}, indent=2))
    else:
        for r in records:
            v = r["outline_agreement"]
            print(Path(r["source"]).name)
            print(f"   flattened  area {r['flattened']['area_px']:>7}  "
                  f"bbox {r['flattened']['bbox']}")
            print(f"   tool @{r['tool_mask']['threshold']:<4g} area "
                  f"{r['tool_mask']['area_px']:>7}  bbox {r['tool_mask']['bbox']}")
            print(f"   outline over the top {VERIFY_FRACTION:.0%} of rows: median "
                  f"|dx| {v['median_px']} px, p95 {v['p95_px']} px "
                  f"({'unmoved' if v['ok'] else 'MOVED -- check the band'})")
            print(f"   wrote {r['output']}")
    return 0 if all(r["outline_agreement"]["ok"] for r in records) else 1


if __name__ == "__main__":
    sys.exit(main())
