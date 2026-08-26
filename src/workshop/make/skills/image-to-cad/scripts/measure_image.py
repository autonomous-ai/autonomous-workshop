#!/usr/bin/env python3
"""Measure a reference image's object proportions — deterministically.

Why this exists: a model reading a photo produces adjectives ("looks roughly
square", "tapers a bit"). A build spec needs numbers. This script supplies the
numbers, so the spec can state ratios instead of vibes.

The measurement is deliberately dumb and deterministic. No model call, no
segmentation network, no renderer. It estimates the background from the frame's
border ring, thresholds the object silhouette, denoises with an
erode-then-dilate opening, and reports the silhouette's bounding box, fill
ratio, width/height profiles, constant-width bands, and mirror-symmetry scores.

Because it measures only the SILHOUETTE it cannot distinguish a hole from a
notch, and a cluttered background will wreck it. Always reconcile the output
against what you actually see in the image; when they disagree, trust your eyes
and say the tool disagreed.

Usage:

    python measure_image.py hero.jpg
    python measure_image.py top.png front.png side.png --views top,front,side
    python measure_image.py six/*.png --views top,bottom,front,back,left,right
    python measure_image.py side.png --palette 5
    python measure_image.py dark_product.jpg --invert
    python measure_image.py noisy.jpg --threshold 40 --json-only

The outline is only half the job. An assembly's real numbers are interior, so
three flags interrogate the mask instead of summarising it:

    # where does this row break into separate blocks?
    python measure_image.py front.png --rows 640,720,800
    python measure_image.py front.png --rows 230:480:10 --run-gap 3

    # what is inside just this box? (the gear window, an inset tray)
    python measure_image.py front.png --region 169,650,798,965

    # where is the part I can name off the reference?
    python measure_image.py front.png --isolate '#6E4A30' --isolate '#C69E4A'

Reach for those rather than writing a throwaway probe script: a probe has to
re-derive the silhouette with its own ad-hoc threshold, and then two images in
one project have been measured with two different instruments.

Cast shadows are rejected by chromaticity (see object_mask) — without that a
studio render's contact shadow reads as object and inflates every ratio.

Give two or more canonically named views (top/bottom, front/back, left/right/
side) and the tool also solves L : W : H across all of them and reports how far
each view disagrees. That number is what tells you whether the images share one
camera scale.

Output is JSON on stdout; a short human summary goes to stderr unless
--json-only is passed.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    import numpy as np
    from PIL import Image, ImageFilter
except ImportError:  # pragma: no cover - environment guard
    sys.stderr.write(
        "numpy and Pillow are required to measure reference images.\n"
        "Install them with:  pip install numpy Pillow\n"
    )
    raise SystemExit(2)


BUCKETS = 24
BORDER_FRACTION = 0.04
DEFAULT_THRESHOLD = 28
OPENING_SIZE = 5
BAND_TOLERANCE = 0.06

# Shadow rejection. A cast shadow keeps the ground's CHROMATICITY and only
# lowers its value, so a pixel counts as object when it differs in hue, or is
# far too dark / too bright for any shadow to explain.
CHROMA_TOLERANCE = 0.045     # normalised-rgb distance from the background hue
SHADOW_DARK_FLOOR = 0.55     # below this fraction of background luma: object
SHADOW_BRIGHT_CEIL = 1.10    # above this fraction: object (specular, lenses)
TWO_SIDED_MIN_SHARE = 0.004  # an off-hue attached region this big is a part
TWO_SIDED_CHROMA_FACTOR = 2.0  # bright regions must be twice as off-hue to count
TWO_SIDED_TOUCH_PX = 7         # how close a bright region must sit to the silhouette

# Which two of (L, W, H) each canonical view name measures, as
# (bbox width -> dim, bbox height -> dim).
VIEW_AXES = {
    "top": ("L", "W"),
    "bottom": ("L", "W"),
    "plan": ("L", "W"),
    "side": ("L", "H"),
    "left": ("L", "H"),
    "right": ("L", "H"),
    "profile": ("L", "H"),
    "front": ("W", "H"),
    "back": ("W", "H"),
    "rear": ("W", "H"),
}


# --------------------------------------------------------------------------
# silhouette extraction
# --------------------------------------------------------------------------

def _background_level(gray: np.ndarray) -> float:
    """Modal luminance of the border ring.

    Sampling the border rather than the whole frame keeps a large centred
    object from dragging the estimate toward its own colour.
    """
    h, w = gray.shape
    band_h = max(1, int(round(h * BORDER_FRACTION)))
    band_w = max(1, int(round(w * BORDER_FRACTION)))

    pixels = np.concatenate(
        [
            gray[:band_h, :].ravel(),
            gray[-band_h:, :].ravel(),
            gray[:, :band_w].ravel(),
            gray[:, -band_w:].ravel(),
        ]
    )
    # Mode over a 16-level histogram: robust to gradients and JPEG noise in a
    # way a mean or median is not.
    hist, edges = np.histogram(pixels, bins=16, range=(0.0, 255.0))
    peak = int(np.argmax(hist))
    return float((edges[peak] + edges[peak + 1]) / 2.0)


def _background_rgb(rgb: np.ndarray) -> np.ndarray:
    """Median colour of the border ring, per channel."""
    h, w, _ = rgb.shape
    band_h = max(1, int(round(h * BORDER_FRACTION)))
    band_w = max(1, int(round(w * BORDER_FRACTION)))
    pixels = np.concatenate(
        [
            rgb[:band_h, :].reshape(-1, 3),
            rgb[-band_h:, :].reshape(-1, 3),
            rgb[:, :band_w].reshape(-1, 3),
            rgb[:, -band_w:].reshape(-1, 3),
        ]
    )
    return np.median(pixels, axis=0)


def _chromaticity(rgb: np.ndarray) -> np.ndarray:
    """Normalised rgb: colour with intensity divided out.

    This is the whole trick behind shadow rejection — dimming a surface scales
    all three channels together, so it moves the pixel's luminance but leaves
    its chromaticity where it was.
    """
    total = rgb.sum(axis=-1) + 1e-6
    return np.stack([rgb[..., 0] / total, rgb[..., 1] / total], axis=-1)


def _not_shadow(rgb: np.ndarray, gray: np.ndarray, bg_rgb: np.ndarray,
                bg_lum: float) -> np.ndarray:
    """True where a pixel is too chromatic, too dark, or too bright to be a
    shadow cast by the object onto the background."""
    chroma = _chromaticity(rgb)
    bg_chroma = _chromaticity(bg_rgb.reshape(1, 1, 3))[0, 0]
    chroma_dist = np.linalg.norm(chroma - bg_chroma, axis=-1)
    lum_ratio = gray / max(bg_lum, 1.0)
    return (
        (chroma_dist > CHROMA_TOLERANCE)
        | (lum_ratio < SHADOW_DARK_FLOOR)
        | (lum_ratio > SHADOW_BRIGHT_CEIL)
    )


def _open_mask(mask: np.ndarray, size: int = OPENING_SIZE) -> np.ndarray:
    """Erode then dilate: deletes anything thinner than `size`, keeps the rest.

    Runs PIL rank filters over a padded copy so the frame edges count as
    background instead of being replicated.
    """
    if size < 3:
        return mask
    pad = size
    padded = np.pad(mask.astype(np.uint8) * 255, pad, mode="constant", constant_values=0)
    img = Image.fromarray(padded, mode="L")
    img = img.filter(ImageFilter.MinFilter(size))   # erode
    img = img.filter(ImageFilter.MaxFilter(size))   # dilate
    out = np.asarray(img)[pad:-pad, pad:-pad]
    return out > 127


def _touching(candidate: np.ndarray, anchor: np.ndarray, reach: int) -> np.ndarray:
    """Components of `candidate` that come within `reach` px of `anchor`.

    Used to decide whether a brighter-than-background region is part of the
    object or part of the scene: object parts touch the object.
    """
    if not candidate.any() or not anchor.any():
        return np.zeros_like(candidate)
    size = max(3, reach | 1)
    grown = np.asarray(
        Image.fromarray((anchor.astype(np.uint8) * 255)).filter(
            ImageFilter.MaxFilter(size))) > 127
    labels, count = _flood_components(candidate)
    if count == 0:
        return np.zeros_like(candidate)
    keep = np.zeros(count + 1, dtype=bool)
    hit = labels[grown & candidate]
    keep[np.unique(hit[hit > 0])] = True
    return keep[labels]


def object_mask(
    rgb: np.ndarray, gray: np.ndarray, threshold: float, invert: bool,
    reject_shadow: bool = True, two_sided: bool = True,
) -> tuple[np.ndarray, float, dict[str, Any]]:
    """Boolean silhouette: True where the object is.

    With `reject_shadow` (the default) a pixel must also fail the shadow test.
    A studio render on a plain ground puts a soft contact shadow around the
    object that is darker than the background and therefore passes a pure
    luminance threshold and inflate every ratio derived from the measured
    bounds.

    With `two_sided` (the default) a region that is *brighter* than the
    background is also admitted, provided it is chromatically distinct from it.
    A single-sided threshold is right for a monochrome part on a contrasting
    ground and silently wrong for a **multi-colour** subject whose distinct
    region has similar luminance to the background. The third return value
    carries `bright_region_share` and a `note`
    whenever this admitted a region, so the decision is visible rather than
    silent.
    """
    bg = _background_level(gray)
    delta = gray - bg
    mask = (delta < -threshold) if not invert else (delta > threshold)
    # A light object on a light ground, or vice versa: fall back to absolute
    # difference so we still get a silhouette instead of an empty frame.
    if mask.mean() < 0.005:
        mask = np.abs(delta) > threshold
    notes: dict[str, Any] = {"two_sided": bool(two_sided)}
    if reject_shadow:
        keep = _not_shadow(rgb, gray, _background_rgb(rgb), bg)
        shadow_free = mask & keep
        # Only trust the rejection if it left a real object behind; a
        # monochrome subject on a monochrome ground legitimately has no hue
        # difference to exploit.
        if shadow_free.mean() > 0.002:
            mask = shadow_free
    if two_sided and mask.any():
        chroma = _chromaticity(rgb)
        bg_chroma = _chromaticity(_background_rgb(rgb).reshape(1, 1, 3))[0, 0]
        chromatic = (np.linalg.norm(chroma - bg_chroma, axis=-1)
                     > CHROMA_TOLERANCE * TWO_SIDED_CHROMA_FACTOR)
        # Not a luminance test. This catches subject regions whose luma sits
        # inside the threshold band around the background but whose colour is
        # distinct enough to identify them.
        candidate = _open_mask(chromatic & ~mask)
        # Touch test.  A brighter, chromatic region is part of the object only
        # if it is attached to the object; a lit tabletop or a warm backdrop
        # gradient is brighter and slightly off-hue too, and admitting it blows
        # the bounding box out to the whole frame.  Keeping only components
        # that touch the already-found silhouette is what separates the two.
        extra = _touching(candidate, mask, TWO_SIDED_TOUCH_PX)
        share = float(extra.mean())
        if share > TWO_SIDED_MIN_SHARE:
            mask = mask | extra
            notes["offhue_region_share"] = round(share, 4)
            notes["note"] = (
                f"{share * 100:.1f} % of the frame is chromatically distinct "
                "from the background and attached to the silhouette, but sits "
                "within the luminance threshold band, so a luminance-only mask "
                "would have dropped it. Admitted as object."
            )
    return _open_mask(mask), bg, notes


# --------------------------------------------------------------------------
# profile analysis
# --------------------------------------------------------------------------

def _extent_profile(mask: np.ndarray, axis: int) -> np.ndarray:
    """Silhouette extent (not pixel count) along `axis`, in pixels.

    Extent is the right measure for form: an object with a big hole through it
    still has the outline width its silhouette shows.
    """
    other = 1 - axis
    idx = np.arange(mask.shape[other])
    out = np.zeros(mask.shape[axis], dtype=float)
    for i in range(mask.shape[axis]):
        line = mask[i, :] if axis == 0 else mask[:, i]
        if not line.any():
            continue
        hit = idx[line]
        out[i] = float(hit.max() - hit.min() + 1)
    return out


def _decimate(profile: np.ndarray, buckets: int = BUCKETS) -> list[float]:
    """Average a profile down to `buckets` samples, normalised to its max."""
    if profile.size == 0:
        return []
    peak = float(profile.max())
    if peak <= 0:
        return [0.0] * buckets
    chunks = np.array_split(profile, buckets)
    return [round(float(c.mean()) / peak, 3) if c.size else 0.0 for c in chunks]


def _bands(samples: list[float], tol: float = BAND_TOLERANCE) -> list[dict[str, float]]:
    """Contiguous runs where the profile is roughly constant.

    These are where loft stations and part splits usually belong: a band
    boundary is the image telling you the section changed character.
    """
    if not samples:
        return []
    out: list[dict[str, float]] = []
    start = 0
    n = len(samples)
    for i in range(1, n + 1):
        if i < n:
            run = samples[start : i + 1]
            if max(run) - min(run) <= tol:
                continue
        run = samples[start:i]
        out.append(
            {
                "from": round(start / n, 3),
                "to": round(i / n, 3),
                "width": round(sum(run) / len(run), 3),
            }
        )
        start = i
    return out


def _profile_shape(samples: list[float]) -> str:
    """One-word character of a profile, for construction-family triage.

    Names are stated relative to the profile's own index, never to a compass
    direction: `row_profile` runs top -> bottom, `col_profile` runs left ->
    right, so "wide_start" means wide at the TOP for rows and wide at the LEFT
    for columns. Direction words would flip meaning between the two axes.
    """
    if len(samples) < 6:
        return "unknown"
    a = np.array(samples, dtype=float)
    third = len(a) // 3
    head, mid, tail = a[:third].mean(), a[third:-third].mean(), a[-third:].mean()
    spread = float(a.max() - a.min())
    if spread <= 0.08:
        return "flat"                       # prismatic -> extrude
    if head - tail > 0.15 and mid > tail:
        return "wide_start"                 # -> tapered extrude, or loft
    if tail - head > 0.15 and mid > head:
        return "wide_end"                   # -> tapered extrude, or loft
    if mid < head - 0.12 and mid < tail - 0.12:
        return "waisted"                    # -> revolve or loft
    if mid > head + 0.12 and mid > tail + 0.12:
        return "bulged"                     # -> revolve or loft
    return "irregular"                      # -> loft over measured stations


def _mirror_score(mask: np.ndarray, axis: int) -> float:
    """IoU of the silhouette against its own mirror, in [0, 1]."""
    flipped = np.flip(mask, axis=axis)
    union = np.logical_or(mask, flipped).sum()
    if union == 0:
        return 0.0
    return round(float(np.logical_and(mask, flipped).sum()) / float(union), 3)


# --------------------------------------------------------------------------
# colour regions
# --------------------------------------------------------------------------

def _kmeans(pixels: np.ndarray, k: int, iters: int = 12) -> np.ndarray:
    """Lloyd's algorithm, seeded on quantiles of luminance.

    Deterministic on purpose: the same image must give the same palette every
    run, or two readings of one photo disagree for no reason.
    """
    lum = pixels.mean(axis=1)
    order = np.argsort(lum)
    seeds = [pixels[order[int((i + 0.5) * len(order) / k)]] for i in range(k)]
    centres = np.array(seeds, dtype=float)
    for _ in range(iters):
        d = np.linalg.norm(pixels[:, None, :] - centres[None, :, :], axis=2)
        who = np.argmin(d, axis=1)
        moved = False
        for i in range(k):
            sel = pixels[who == i]
            if sel.size:
                new = sel.mean(axis=0)
                if not np.allclose(new, centres[i]):
                    centres[i] = new
                    moved = True
        if not moved:
            break
    return centres


def palette_regions(rgb: np.ndarray, mask: np.ndarray, k: int,
                    x0: int, y0: int, bw: int, bh: int) -> list[dict[str, Any]]:
    """Split the silhouette into k colour clusters and locate each one.

    Silhouette measurement alone cannot see a painted stripe, a cockpit
    opening, a tyre against a fender, or a headlight — they are all interior to
    the outline. Colour is what separates them, and their positions are exactly
    what the view sections of the spec need.
    """
    pts = rgb[mask]
    if pts.shape[0] < k * 8:
        return []
    sample = pts[:: max(1, pts.shape[0] // 20000)]
    centres = _kmeans(sample.astype(float), k)
    d = np.linalg.norm(pts[:, None, :].astype(float) - centres[None, :, :], axis=2)
    who = np.argmin(d, axis=1)

    ys, xs = np.nonzero(mask)
    out: list[dict[str, Any]] = []
    for i in range(k):
        sel = who == i
        n = int(sel.sum())
        if n == 0:
            continue
        cx, cy = xs[sel], ys[sel]
        # Column occupancy: for each of BUCKETS columns, the vertical span this
        # colour covers, as fractions of the bounding box.
        span: list[list[float] | None] = []
        edges = np.linspace(x0, x0 + bw, BUCKETS + 1)
        for b in range(BUCKETS):
            inb = (cx >= edges[b]) & (cx < edges[b + 1])
            if not inb.any():
                span.append(None)
                continue
            span.append([
                round(float(cy[inb].min() - y0) / bh, 3),
                round(float(cy[inb].max() - y0) / bh, 3),
            ])
        r, g, b_ = (int(round(v)) for v in centres[i])
        out.append({
            "hex": f"#{r:02X}{g:02X}{b_:02X}",
            "share": round(n / float(pts.shape[0]), 4),
            "bbox_frac": {
                "x": round(float(cx.min() - x0) / bw, 3),
                "y": round(float(cy.min() - y0) / bh, 3),
                "w": round(float(cx.max() - cx.min() + 1) / bw, 3),
                "h": round(float(cy.max() - cy.min() + 1) / bh, 3),
            },
            "column_span": span,
        })
    return sorted(out, key=lambda r: -r["share"])


# --------------------------------------------------------------------------
# cross-view consistency
# --------------------------------------------------------------------------

def cross_check(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Solve L : W : H from every canonically named view at once.

    Each view constrains the RATIO of two of the three dimensions, so two
    views spanning all three close the loop and a third over-determines it.
    The residual is the number that tells you whether the images share one
    camera scale — without it, a foreshortened view is averaged in silently
    and every ratio in the spec is quietly wrong.
    """
    rows, obs = [], []
    used = []
    index = {"L": 0, "W": 1, "H": 2}
    for r in records:
        if "error" in r:
            continue
        axes = VIEW_AXES.get(r["view"].split("-")[-1].split("_")[-1].lower())
        if axes is None:
            continue
        eq = [0.0, 0.0, 0.0]
        eq[index[axes[0]]] = 1.0
        eq[index[axes[1]]] -= 1.0
        rows.append(eq)
        obs.append(math.log(r["bbox_px"]["w"] / r["bbox_px"]["h"]))
        used.append((r["view"], axes))
    if len(rows) < 2:
        return None
    a = np.array(rows)
    # Fix log L = 0 to remove the free scale, then least-squares the rest.
    a_free, obs_v = a[:, 1:], np.array(obs) - a[:, 0] * 0.0
    sol, *_ = np.linalg.lstsq(a_free, obs_v, rcond=None)
    logs = np.array([0.0, sol[0], sol[1]])
    resid = a @ logs - np.array(obs)
    worst = float(np.max(np.abs(np.expm1(resid))))
    return {
        "solved_ratio_L_W_H": [1.0, round(float(np.exp(logs[1])), 4),
                               round(float(np.exp(logs[2])), 4)],
        "views_used": [v for v, _ in used],
        "per_view_disagreement_pct": {
            v: round(float(abs(np.expm1(resid[i]))) * 100.0, 2)
            for i, (v, _) in enumerate(used)
        },
        "worst_disagreement_pct": round(worst * 100.0, 2),
        "verdict": (
            "consistent — treat the views as one orthographic set"
            if worst < 0.05 else
            "INCONSISTENT — at least one view is foreshortened or differently "
            "scaled; do not average, find the bad view first"
        ),
    }


# --------------------------------------------------------------------------
# interrogation: asking the mask about one row, one box, one colour
# --------------------------------------------------------------------------
#
# Everything above answers "what does the whole outline look like". The three
# helpers below answer the questions a build spec actually runs into, all of
# which are INTERIOR and none of which an outline can show:
#
#   where does this row break into separate blocks?  -> _runs / scan_lines
#   what is going on inside just this box?           -> --region
#   where is the brass part / the dark window?       -> isolate_colours
#
# Without these the only way to get the number is a throwaway script that
# re-derives the silhouette with its own ad-hoc threshold, which is how one
# pipeline ends up measuring four objects with four different instruments.


def _parse_ints(raw: str, count: int, flag: str) -> list[int]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) != count:
        raise ValueError(f"{flag} needs {count} comma-separated integers, got {len(parts)}")
    try:
        return [int(p) for p in parts]
    except ValueError as exc:
        raise ValueError(f"{flag} takes integers: {exc}") from exc


def parse_scan(raw: str, limit: int, flag: str) -> list[int]:
    """`120,240,360` or a `start:stop:step` slice, clamped into the image."""
    if ":" in raw:
        bits = raw.split(":")
        if len(bits) not in (2, 3):
            raise ValueError(f"{flag} slice looks like start:stop or start:stop:step")
        start, stop = int(bits[0]), int(bits[1])
        step = int(bits[2]) if len(bits) == 3 else 1
        if step <= 0:
            raise ValueError(f"{flag} step must be positive")
        wanted = list(range(start, stop, step))
    else:
        wanted = [int(p) for p in raw.split(",") if p.strip()]
    kept = [v for v in wanted if 0 <= v < limit]
    # Never drop a requested line silently: asking for row 2000 of a 1024 px
    # image is a mistake about the image, and an empty scan looks like an
    # answer ("no runs there") rather than a question that was never asked.
    if len(kept) != len(wanted):
        dropped = sorted(set(wanted) - set(kept))
        sys.stderr.write(
            f"{flag}: ignored {len(dropped)} position(s) outside 0..{limit - 1}: "
            f"{dropped[:8]}{' ...' if len(dropped) > 8 else ''}\n"
        )
    return kept


def _runs(line: np.ndarray, gap: int) -> list[list[int]]:
    """Contiguous True spans along a 1-D mask, merging holes up to `gap` wide.

    The gap tolerance is the point: a 2 px antialiasing seam is not a real
    split, but the 40 px opening between two blocks is exactly what tells you
    the object is two parts rather than one.
    """
    idx = np.nonzero(line)[0]
    if idx.size == 0:
        return []
    out: list[list[int]] = []
    start = prev = int(idx[0])
    for value in idx[1:]:
        value = int(value)
        if value > prev + 1 + gap:
            out.append([start, prev])
            start = value
        prev = value
    out.append([start, prev])
    return out


def scan_lines(mask: np.ndarray, positions: list[int], axis: str,
               gap: int) -> list[dict[str, Any]]:
    """Per-row (or per-column) run report — replaces the hand-written probes.

    `axis="row"` walks y and reports x spans; `axis="col"` walks x and reports
    y spans. Both report in ORIGINAL image pixel coordinates, so a number here
    can be pasted straight back into a crop or a follow-up scan.
    """
    out = []
    for position in positions:
        line = mask[position, :] if axis == "row" else mask[:, position]
        spans = _runs(line, gap)
        out.append({
            "at": position,
            "runs": spans,
            "run_count": len(spans),
            "covered_px": int(line.sum()),
            "extent": [spans[0][0], spans[-1][1]] if spans else None,
        })
    return out


def _flood_components(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """4-connected labelling. Pure numpy + a stack; scipy just makes it fast."""
    try:  # pragma: no cover - availability differs per environment
        from scipy import ndimage
    except ImportError:
        pass
    else:
        labels, count = ndimage.label(mask)
        return labels, int(count)

    labels = np.zeros(mask.shape, np.int32)
    height, width = mask.shape
    current = 0
    for sy in range(height):
        for sx in np.nonzero(mask[sy] & (labels[sy] == 0))[0]:
            current += 1
            stack = [(sy, int(sx))]
            labels[sy, sx] = current
            while stack:
                y, x = stack.pop()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width \
                            and mask[ny, nx] and labels[ny, nx] == 0:
                        labels[ny, nx] = current
                        stack.append((ny, nx))
    return labels, current


def _blob_box(hit: np.ndarray, x0: int, y0: int, bw: int, bh: int) -> dict[str, Any]:
    ys, xs = np.nonzero(hit)
    hx0, hx1 = int(xs.min()), int(xs.max())
    hy0, hy1 = int(ys.min()), int(ys.max())
    return {
        "px": int(hit.sum()),
        "bbox_px": {"x": hx0, "y": hy0, "w": hx1 - hx0 + 1, "h": hy1 - hy0 + 1},
        "bbox_frac": {
            "x": round((hx0 - x0) / bw, 3),
            "y": round((hy0 - y0) / bh, 3),
            "w": round((hx1 - hx0 + 1) / bw, 3),
            "h": round((hy1 - hy0 + 1) / bh, 3),
        },
    }


def isolate_colours(rgb: np.ndarray, mask: np.ndarray, targets: list[str],
                    tolerance: float) -> list[dict[str, Any]]:
    """Locate named colours inside the silhouette.

    `--palette K` finds whichever K clusters happen to dominate; this answers
    the opposite question — "where is THIS colour", the one you can name off
    the reference because it is the walnut base or the brass crank.

    Matching is per-channel (Chebyshev) distance, not Euclidean: a tolerance
    read as "within N of this R, this G and this B" is what a person means by
    a colour family, and Euclidean lets one wildly-off channel hide behind two
    close ones — on a set of wood tones that merges every family into one.

    The hit mask is then intersected with the object mask, so a background of
    a similar colour cannot answer for a part, and opened, because a bbox is a
    min/max and a handful of stray speckles would otherwise stretch it across
    the whole frame while the part sits in one corner.
    """
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return []
    y0, x0 = int(ys.min()), int(xs.min())
    bh = int(ys.max()) - y0 + 1
    bw = int(xs.max()) - x0 + 1
    total = float(mask.sum())

    out = []
    for target in targets:
        want = target.strip().lstrip("#")
        if len(want) != 6:
            out.append({"hex": f"#{want}", "error": "expected #RRGGBB"})
            continue
        try:
            ref = np.array([int(want[i : i + 2], 16) for i in (0, 2, 4)], dtype=float)
        except ValueError:
            out.append({"hex": f"#{want}", "error": "not valid hex"})
            continue

        raw = (np.abs(rgb - ref).max(axis=-1) <= tolerance) & mask
        hit = _open_mask(raw) if raw.any() else raw
        n = int(hit.sum())
        if n == 0:
            note = (
                f"matched {int(raw.sum())} px, but none survived the speckle "
                "opening — the colour is scattered noise here, not a part"
                if raw.any() else
                f"no pixel within {tolerance:.0f} per channel of this colour — "
                "raise --isolate-tolerance or re-sample the hex"
            )
            out.append({"hex": f"#{want.upper()}", "px": 0, "note": note})
            continue
        labels, count = _flood_components(hit)
        entry: dict[str, Any] = {
            "hex": f"#{want.upper()}",
            "px": n,
            "share_of_silhouette": round(n / total, 4),
            "mean_rgb": [int(round(v)) for v in rgb[hit].mean(axis=0)],
            "blobs": count,
            # Every matched pixel. On a part that appears twice (a brass crank
            # on the left, a brass moon on the right) this box spans the gap
            # between them and describes no single part — read `parts` instead.
            "all": _blob_box(hit, x0, y0, bw, bh),
        }
        if count:
            sizes = np.bincount(labels.ravel())
            sizes[0] = 0
            keep = [i for i in np.argsort(sizes)[::-1] if sizes[i] > 0][:4]
            entry["parts"] = [_blob_box(labels == int(i), x0, y0, bw, bh) for i in keep]
        out.append(entry)
    return out


# --------------------------------------------------------------------------
# per-image measurement
# --------------------------------------------------------------------------

def measure(path: Path, label: str, threshold: float, invert: bool,
            reject_shadow: bool = True, palette: int = 0,
            region: list[int] | None = None,
            rows_at: str = "", cols_at: str = "", run_gap: int = 2,
            isolate: list[str] | None = None,
            isolate_tolerance: float = 46.0) -> dict[str, Any]:
    try:
        image = Image.open(path)
    except Exception as exc:  # noqa: BLE001 - report, don't crash the batch
        return {"view": label, "file": str(path), "error": f"cannot open: {exc}"}

    image = image.convert("RGB")
    rgb = np.asarray(image, dtype=float)
    gray = np.asarray(image.convert("L"), dtype=float)
    # The mask is always derived from the WHOLE frame, even under --region.
    # Background estimation reads the frame's border ring, and a region cropped
    # to sit inside the object has no background in its own border to read.
    mask, bg, mask_notes = object_mask(rgb, gray, threshold, invert, reject_shadow)

    region_box: dict[str, int] | None = None
    if region is not None:
        rx0, ry0, rx1, ry1 = region
        rx0, rx1 = sorted((max(0, rx0), min(image.width, rx1)))
        ry0, ry1 = sorted((max(0, ry0), min(image.height, ry1)))
        if rx1 - rx0 < 1 or ry1 - ry0 < 1:
            return {
                "view": label,
                "file": str(path),
                "error": f"--region is empty after clamping to the {image.width}x"
                         f"{image.height} frame",
            }
        window = np.zeros_like(mask)
        window[ry0:ry1, rx0:rx1] = True
        mask = mask & window
        region_box = {"x": rx0, "y": ry0, "w": rx1 - rx0, "h": ry1 - ry0}

    if not mask.any():
        where = " inside --region" if region_box else ""
        return {
            "view": label,
            "file": str(path),
            "error": f"no object found{where} — try --invert, or --threshold below "
                     f"{int(threshold)}; background luminance was {bg:.0f}",
            "image_px": {"w": image.width, "h": image.height},
            **({"region_px": region_box} if region_box else {}),
        }

    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    y0, y1 = int(rows.min()), int(rows.max())
    x0, x1 = int(cols.min()), int(cols.max())
    bw, bh = x1 - x0 + 1, y1 - y0 + 1

    crop = mask[y0 : y1 + 1, x0 : x1 + 1]
    row_profile = _decimate(_extent_profile(crop, axis=0))   # width at each height
    col_profile = _decimate(_extent_profile(crop, axis=1))   # height at each column

    area = int(crop.sum())
    widest = int(np.argmax(_extent_profile(crop, axis=0)))

    record: dict[str, Any] = {
        "view": label,
        "file": str(path),
        "image_px": {"w": image.width, "h": image.height},
        "background_luminance": round(bg, 1),
        "shadow_rejected": bool(reject_shadow),
        "mask": mask_notes,
        "bbox_px": {"x": x0, "y": y0, "w": bw, "h": bh},
        "aspect_w_over_h": round(bw / bh, 3),
        "fill_ratio": round(area / float(bw * bh), 3),
        "profile_index_note": "row_profile runs top->bottom; col_profile runs left->right",
        "row_profile": row_profile,
        "row_shape": _profile_shape(row_profile),
        "row_bands": _bands(row_profile),
        "col_profile": col_profile,
        "col_shape": _profile_shape(col_profile),
        "col_bands": _bands(col_profile),
        "widest_at_height_frac": round(widest / max(1, bh - 1), 3),
        "symmetry": {
            "left_right": _mirror_score(crop, axis=1),
            "top_bottom": _mirror_score(crop, axis=0),
        },
    }
    if region_box is not None:
        # Say so loudly: every number in this record describes the window only,
        # so it must never be quoted as an overall proportion.
        record["region_px"] = region_box
        record["scope"] = "REGION ONLY — these numbers describe the --region window, not the whole object"
    if palette:
        record["palette"] = palette_regions(rgb, mask, palette, x0, y0, bw, bh)
    if isolate:
        record["isolate"] = isolate_colours(rgb, mask, isolate, isolate_tolerance)
    if rows_at:
        record["row_scan"] = scan_lines(
            mask, parse_scan(rows_at, image.height, "--rows"), "row", run_gap
        )
    if cols_at:
        record["col_scan"] = scan_lines(
            mask, parse_scan(cols_at, image.width, "--cols"), "col", run_gap
        )
    return record


def summarise(record: dict[str, Any]) -> str:
    if "error" in record:
        return f"  {record['view']}: ERROR — {record['error']}"
    bb = record["bbox_px"]
    sym = record["symmetry"]
    return (
        f"  {record['view']}: {bb['w']}x{bb['h']} px  "
        f"aspect {record['aspect_w_over_h']}  fill {record['fill_ratio']}  "
        f"rows {record['row_shape']} ({len(record['row_bands'])} bands)  "
        f"cols {record['col_shape']}  "
        f"sym L/R {sym['left_right']} T/B {sym['top_bottom']}"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Measure reference-image proportions for a CAD build spec."
    )
    ap.add_argument("images", nargs="+", type=Path, help="one or more image files")
    ap.add_argument(
        "--views",
        default="",
        help="comma-separated labels matching the images (e.g. top,front,side)",
    )
    ap.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"luminance delta from background counted as object (default {DEFAULT_THRESHOLD})",
    )
    ap.add_argument(
        "--invert",
        action="store_true",
        help="object is LIGHTER than the background (default assumes darker)",
    )
    ap.add_argument(
        "--no-reject-shadow",
        action="store_true",
        help="keep pixels a cast shadow could explain (pre-0.2 behaviour; a "
             "soft contact shadow then inflates the measured bounding box)",
    )
    ap.add_argument(
        "--palette",
        type=int,
        default=0,
        metavar="K",
        help="also split the silhouette into K colour clusters and report each "
             "one's bbox and column span — how you locate a stripe, a cockpit "
             "opening, a tyre or a lens, none of which the outline can show",
    )
    ap.add_argument(
        "--region",
        default="",
        metavar="X0,Y0,X1,Y1",
        help="measure only inside this pixel box — how you interrogate an "
             "assembly's interior (a gear window, an inset tray) instead of "
             "re-measuring the outline. The silhouette is still derived from "
             "the whole frame, so background estimation stays valid",
    )
    ap.add_argument(
        "--rows",
        default="",
        metavar="Y|START:STOP:STEP",
        help="report the object's horizontal runs at these rows, e.g. "
             "'640,720,800' or '230:480:10'. Two runs on a row means a real "
             "gap there — the number that separates one part from two",
    )
    ap.add_argument(
        "--cols",
        default="",
        metavar="X|START:STOP:STEP",
        help="the same scan down columns, reporting vertical runs",
    )
    ap.add_argument(
        "--run-gap",
        type=int,
        default=2,
        metavar="PX",
        help="holes up to this wide do not split a run (default 2, so an "
             "antialiasing seam is not read as a gap)",
    )
    ap.add_argument(
        "--isolate",
        action="append",
        default=[],
        metavar="#RRGGBB",
        help="locate a NAMED colour inside the silhouette and report its bbox; "
             "repeat for several. Use this for the parts you can name off the "
             "reference (the walnut base, the brass crank) — unlike --palette, "
             "which returns whichever clusters happen to dominate",
    )
    ap.add_argument(
        "--isolate-tolerance",
        type=float,
        default=46.0,
        metavar="D",
        help="per-channel RGB distance counted as a match for --isolate (default 46)",
    )
    ap.add_argument("--json-only", action="store_true", help="suppress the stderr summary")
    args = ap.parse_args(argv)

    try:
        region = _parse_ints(args.region, 4, "--region") if args.region else None
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2

    labels = [s.strip() for s in args.views.split(",") if s.strip()]
    if labels and len(labels) != len(args.images):
        sys.stderr.write(
            f"--views has {len(labels)} labels but {len(args.images)} images were given\n"
        )
        return 2
    if not labels:
        labels = [p.stem for p in args.images]

    try:
        records = [
            measure(p, label, args.threshold, args.invert,
                    not args.no_reject_shadow, args.palette,
                    region=region, rows_at=args.rows, cols_at=args.cols,
                    run_gap=args.run_gap, isolate=args.isolate,
                    isolate_tolerance=args.isolate_tolerance)
            for p, label in zip(args.images, labels)
        ]
    except ValueError as exc:  # a malformed --rows/--cols spec
        sys.stderr.write(f"{exc}\n")
        return 2
    ok = all("error" not in r for r in records)
    payload: dict[str, Any] = {"ok": ok, "views": records}
    # A region measures a window, not the object, so its bbox says nothing
    # about L:W:H. Solving the ratio from it would produce a confident,
    # wrong answer — the one failure mode this script exists to prevent.
    check = None if region is not None else cross_check(records)
    if check is not None:
        payload["cross_check"] = check
    elif region is not None:
        payload["cross_check_skipped"] = "--region measures a window, not the object"
    print(json.dumps(payload, indent=2))

    if not args.json_only:
        sys.stderr.write("measure_image:\n")
        for r in records:
            sys.stderr.write(summarise(r) + "\n")
            for c in r.get("palette", []):
                bb = c["bbox_frac"]
                sys.stderr.write(
                    f"      {c['hex']}  {c['share'] * 100:5.1f}%  "
                    f"box x{bb['x']:.2f} y{bb['y']:.2f} w{bb['w']:.2f} h{bb['h']:.2f}\n"
                )
            for c in r.get("isolate", []):
                if not c.get("px"):
                    sys.stderr.write(
                        f"      {c['hex']}  {c.get('error') or c.get('note')}\n"
                    )
                    continue
                sys.stderr.write(
                    f"      {c['hex']}  {c['share_of_silhouette'] * 100:5.1f}%  "
                    f"{c['blobs']} blob(s)\n"
                )
                for i, part in enumerate(c.get("parts", [])):
                    bb = part["bbox_px"]
                    sys.stderr.write(
                        f"          part{i}  {part['px']:>7} px  "
                        f"x{bb['x']} y{bb['y']} w{bb['w']} h{bb['h']}\n"
                    )
            for scan_key, unit in (("row_scan", "x"), ("col_scan", "y")):
                for s in r.get(scan_key, []):
                    spans = " ".join(f"{a}-{b}" for a, b in s["runs"]) or "(empty)"
                    sys.stderr.write(
                        f"      {scan_key[:3]} {s['at']:>5}: {s['run_count']} run(s) "
                        f"{unit} {spans}\n"
                    )
        if check is not None:
            r = check["solved_ratio_L_W_H"]
            sys.stderr.write(
                f"  cross-check L:W:H = 1 : {r[1]} : {r[2]}  "
                f"worst disagreement {check['worst_disagreement_pct']}%  "
                f"-> {check['verdict'].split(' — ')[0]}\n"
            )
        sys.stderr.write(
            "  note: silhouette only — a hole and a notch look identical here.\n"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
