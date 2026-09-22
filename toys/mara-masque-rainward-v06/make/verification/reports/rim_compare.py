"""Unwrap the rim of the concept and of the built Sun into one comparison strip.

The concept panel is the exact strip the previous correction round published in
`ref/previous-rim-comparison.png`: one third of the ring, radius 0.86 to 1.22
of the disc, 1600 px wide. Reusing those bytes is what makes "same radius
window and arc as before" exact rather than approximate.

The built panel is unwrapped from a fresh orthographic top render of the exact
STEP, over the same third of a ring and the same radius window, at the same
1600 px arc width. The mm-to-pixel mapping is taken from the render's own
silhouette bounding box against the model's exact bounding box, and is then
checked against the disc edge radius measured in the valleys between flames:
if that check misses by more than 0.5 mm the script refuses to write a strip.

Run it from the CAD project directory.
"""
import json
import math
import os
import pathlib
import sys

sys.path.insert(0, ".")

import numpy as np
from PIL import Image, ImageDraw

import params as P
import profiles as G

REF = pathlib.Path("ref/previous-rim-comparison.png")
STRIP_W = 1600
R_LO, R_HI = 0.86, 1.22
ARC_DEG = 120.0
BUILT_START_DEG = 96.0     # the third of the ring the built strip unwraps
CAPTION_H = 22


def _mask(image):
    """Orange board pixels: warm hue, well saturated, not the background."""
    a = np.asarray(image.convert("RGB")).astype(np.float64) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    return (sat > 0.25) & (mx > 0.35) & (r >= g) & (g >= b)


def _panels(path):
    """Split the published comparison into its caption/strip bands."""
    a = np.asarray(Image.open(path).convert("RGB"))
    plain = np.all(a > 245, axis=2).mean(axis=1) > 0.995
    bands, start = [], None
    for y, white in enumerate(plain):
        if not white and start is None:
            start = y
        elif white and start is not None:
            bands.append((start, y))
            start = None
    if start is not None:
        bands.append((start, len(plain)))
    return a, [band for band in bands if band[1] - band[0] > 40]


def concept_panel():
    a, bands = _panels(REF)
    top, bottom = bands[0]
    return Image.fromarray(a[top:bottom])


def built_panel(render_path, bbox_mm, samples_r=None):
    image = Image.open(render_path).convert("RGB")
    mask = _mask(image)
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    px_per_mm = (x1 - x0 + 1) / (bbox_mm[1] - bbox_mm[0])
    cx = x0 - bbox_mm[0] * px_per_mm
    cy = y1 + bbox_mm[2] * px_per_mm          # image y grows downward
    check = _edge_radius_check(mask, cx, cy, px_per_mm)
    if abs(check - P.SUN_R) > 0.5:
        raise SystemExit("top render calibration is off: disc edge measured "
                         "%.2f mm against %.2f" % (check, P.SUN_R))
    height = samples_r or int(round(STRIP_W * (R_HI - R_LO) * ARC_DEG
                                    / (360.0 * (R_HI + R_LO) / 2.0) * 0))
    height = int(round(P.SUN_R * (R_HI - R_LO) * px_per_mm_strip()))
    strip = Image.new("RGB", (STRIP_W, height), (235, 238, 242))
    src = np.asarray(image)
    out = np.asarray(strip).copy()
    for col in range(STRIP_W):
        angle = math.radians(BUILT_START_DEG + ARC_DEG * col / STRIP_W)
        for row in range(height):
            frac = R_HI - (R_HI - R_LO) * row / max(height - 1, 1)
            r = frac * P.SUN_R * px_per_mm
            sx = int(round(cx + r * math.cos(angle)))
            sy = int(round(cy - r * math.sin(angle)))
            if 0 <= sx < src.shape[1] and 0 <= sy < src.shape[0]:
                out[row, col] = src[sy, sx]
    return Image.fromarray(out), check, px_per_mm


def px_per_mm_strip():
    """Pixels per mm of the output strip, set by its 1600 px arc width."""
    arc_mm = math.radians(ARC_DEG) * P.SUN_R
    return STRIP_W / arc_mm


def _edge_radius_check(mask, cx, cy, px_per_mm):
    """Disc edge radius, measured where the boundary is bare base circle.

    Along a ray the mask is solid out to the disc edge; in a valley it ends
    there. The tenth percentile over many rays is that edge.
    """
    edges = []
    for k in range(720):
        angle = math.radians(k * 0.5)
        last = None
        for step in range(int(0.5 * px_per_mm), int(110 * px_per_mm)):
            sx = int(round(cx + step * math.cos(angle)))
            sy = int(round(cy - step * math.sin(angle)))
            if 0 <= sx < mask.shape[1] and 0 <= sy < mask.shape[0] and mask[sy, sx]:
                last = step
        if last is not None:
            edges.append(last / px_per_mm)
    return float(np.percentile(edges, 10))


def caption(text, width):
    band = Image.new("RGB", (width, CAPTION_H), (255, 255, 255))
    ImageDraw.Draw(band).text((6, 5), text, fill=(0, 0, 0))
    return band


def main(render_path, out_path, bbox_mm):
    top = concept_panel().resize((STRIP_W, concept_panel().height), Image.LANCZOS)
    bottom, edge_mm, px_per_mm = built_panel(render_path, bbox_mm)
    bands = [
        caption("CONCEPT ref-01-idea-3-corona-rim.png - rim unwrapped, one third"
                " of the ring, radius 0.86 to 1.22 of the disc", STRIP_W),
        top,
        caption("BUILT Rainward Emberfan cad/snap/top.png - same unwrap, same"
                " window, same arc length, disc radius 79.70", STRIP_W),
        bottom,
    ]
    sheet = Image.new("RGB", (STRIP_W, sum(b.height for b in bands)), (255, 255, 255))
    y = 0
    for band in bands:
        sheet.paste(band, (0, y))
        y += band.height
    sheet.save(out_path)
    return {"out": out_path, "measured_disc_edge_mm": round(edge_mm, 3),
            "render_px_per_mm": round(px_per_mm, 4),
            "strip_px_per_mm": round(px_per_mm_strip(), 4),
            "arc_deg": ARC_DEG, "radius_window": [R_LO, R_HI],
            "built_start_deg": BUILT_START_DEG}


def built_only(render_path, out_path, bbox_mm, starts):
    """The built rim unwrapped on its own, one panel per starting angle.

    The base circle becomes a straight horizontal line, so a root's base width
    and the bare arc beside it are the same kind of measurement on the same
    line and can be compared directly by eye.
    """
    global BUILT_START_DEG
    panels = []
    for start in starts:
        BUILT_START_DEG = start
        panel, check, _ = built_panel(render_path, bbox_mm)
        panels.append(caption("built rim unwrapped, %d to %d degrees, radius "
                              "0.86 to 1.22 of the disc" % (start, start + ARC_DEG),
                              STRIP_W))
        panels.append(panel)
    sheet = Image.new("RGB", (STRIP_W, sum(b.height for b in panels)), (255, 255, 255))
    y = 0
    for band in panels:
        sheet.paste(band, (0, y))
        y += band.height
    sheet.save(out_path)
    return out_path


if __name__ == "__main__":
    render = sys.argv[1] if len(sys.argv) > 1 else "snap/top.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "snap/rim-comparison.png"
    xs, ys = [], []
    for i in range(P.CORONA_COUNT):
        for x, y in G.tongue_face_outline(i, 64):
            xs.append(x)
            ys.append(y)
    for k in range(721):
        a = math.radians(k * 0.5)
        xs.append(P.SUN_R * math.cos(a))
        ys.append(P.SUN_R * math.sin(a))
    bbox = (min(xs), max(xs), min(ys), max(ys))
    if len(sys.argv) > 3 and sys.argv[3] == "--built-only":
        print(built_only(render, out, bbox, (96.0, 216.0, 336.0)))
    else:
        print(json.dumps(main(render, out, bbox), indent=2, sort_keys=True))
