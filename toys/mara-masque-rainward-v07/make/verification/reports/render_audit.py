"""Measure the canonical renders, not the parameters that produced them.

Three questions this answers from pixels alone:

* outside the disc's own edge circle, how many separate pieces of body are
  there? A rim that was poured and set is one piece; a rim of separate licks is
  one piece per lick.
* do the twenty-four lanes alternate light and dark all the way round?
* in greyscale, do the five sealed tones stay in order and stay apart?

Run it from the CAD project directory.
"""
import json
import math
import os
import pathlib
import sys

_PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

import numpy as np
from PIL import Image
from scipy import ndimage

import params as P
import profiles as G

MIN_TONE_GAP = 0.09
LUMA = (0.2126, 0.7152, 0.0722)


def _load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.float64) / 255.0


def _body_mask(a):
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (sat > 0.25) & (mx > 0.35) & (r >= g) & (g >= b)


def _frame(a):
    """Pixels per mm and the image position of the board centre."""
    mask = _body_mask(a)
    ys, xs = np.nonzero(mask)
    plan_x, plan_y = [], []
    for i in range(P.CORONA_COUNT):
        for x, y in G.tongue_face_outline(i, 64):
            plan_x.append(x)
            plan_y.append(y)
    for k in range(721):
        t = math.radians(k * 0.5)
        plan_x.append(P.SUN_R * math.cos(t))
        plan_y.append(P.SUN_R * math.sin(t))
    px_per_mm = (xs.max() - xs.min() + 1) / (max(plan_x) - min(plan_x))
    cx = xs.min() - min(plan_x) * px_per_mm
    cy = ys.max() + min(plan_y) * px_per_mm
    return mask, px_per_mm, cx, cy


def _pixel(a, px_per_mm, cx, cy, radius, angle_deg):
    x, y = G.xy(radius, angle_deg)
    return a[int(round(cy - y * px_per_mm)), int(round(cx + x * px_per_mm))]


def flame_pieces(path):
    """Connected pieces of body outside the disc's edge circle."""
    a = _load(path)
    mask, px_per_mm, cx, cy = _frame(a)
    h, w = mask.shape
    yy, xx = np.mgrid[0:h, 0:w]
    radius = np.hypot((xx - cx) / px_per_mm, (yy - cy) / px_per_mm)
    outside = mask & (radius > P.SUN_R + 0.45)
    labels, count = ndimage.label(outside)
    sizes = ndimage.sum(outside, labels, range(1, count + 1))
    real = int((sizes >= 4.0 * px_per_mm * px_per_mm).sum())
    return real, count, round(px_per_mm, 4)


def lane_tones(path):
    """Rendered tone of every lane, sampled on its own axis."""
    a = _load(path)
    _, px_per_mm, cx, cy = _frame(a)
    out = []
    for point in range(1, P.LANES + 1):
        samples = [_pixel(a, px_per_mm, cx, cy, r, G.theta(point))
                   for r in (58.0, 48.0, 38.0)]
        value = float(np.mean([sum(w * c for w, c in zip(LUMA, s)) for s in samples]))
        out.append(round(value, 4))
    return out


def greyscale_tones(path, colour_path):
    """The five sealed tones read back out of the greyscale board render.

    The greyscale image carries no saturation, so its frame is taken from the
    colour render it was converted from; the two are the same pixels.
    """
    a = _load(path)
    _, px_per_mm, cx, cy = _frame(_load(colour_path))
    spots = {
        "sun_body_orange": (25.0, G.theta(1) - P.PITCH / 2.0 + 180.0),
        "lane_light_yellow": (48.0, G.theta(1)),
        "lane_dark_cocoa": (48.0, G.theta(2)),
        "single_beige_counter": (P.RADII[0], G.theta(24)),
        "fork_dark_brown_counter": (P.RADII[0], G.theta(1)),
    }
    out = {}
    for name, (radius, angle) in spots.items():
        out[name] = round(float(_pixel(a, px_per_mm, cx, cy, radius, angle)[0]), 4)
    return out


def audit():
    pieces, raw, px_per_mm = flame_pieces("snap/top.png")
    tones = lane_tones("snap/setup-top.png")
    grey = greyscale_tones("snap/greyscale-top.png", "snap/setup-top.png")
    light = [i for i, v in enumerate(tones) if v > (max(tones) + min(tones)) / 2]
    alternates = all((i % 2 == 0) == (i in light) for i in range(P.LANES))
    order = ["single_beige_counter", "lane_light_yellow", "sun_body_orange",
             "lane_dark_cocoa", "fork_dark_brown_counter"]
    gaps = [round(grey[order[i]] - grey[order[i + 1]], 4) for i in range(4)]
    report = {
        "kind": "rainward-sunflare-render-audit",
        "render_px_per_mm": px_per_mm,
        "flame_pieces_outside_the_disc_edge": pieces,
        "flame_pieces_raw_regions": raw,
        "flames_in_the_plan": P.CORONA_COUNT,
        "lane_count": len(tones),
        "lane_luma": tones,
        "lane_tones_alternate": bool(alternates),
        "greyscale_luma": grey,
        "greyscale_gaps_light_to_dark": gaps,
        "greyscale_order_holds": bool(all(g > 0 for g in gaps)),
        "greyscale_min_gap": min(gaps),
    }
    report["pass"] = bool(
        report["flame_pieces_outside_the_disc_edge"] == P.CORONA_COUNT
        and report["lane_count"] == 24
        and report["lane_tones_alternate"]
        and report["greyscale_order_holds"]
        and report["greyscale_min_gap"] >= MIN_TONE_GAP)
    return report


if __name__ == "__main__":
    result = audit()
    pathlib.Path("measure/render-audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if result["pass"] else 1)
