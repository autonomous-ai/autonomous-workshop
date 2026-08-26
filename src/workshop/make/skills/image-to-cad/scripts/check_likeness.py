#!/usr/bin/env python3
"""Silhouette-likeness gate: how close does the model look to the reference?

Every other check in this toolchain asks whether the model is *sound* --
`validate` (closed solids), `interfere` (no clash), `check_fit` (prints),
`check_motion` (assembles). None of them asks the only question an
image-derived model exists to answer: **does it look like the photograph?**
That gap is why a model can pass seven gates and still be 60 % of the way
there, and why "looks about right" was the acceptance test.

This makes it a number. For each (render, reference) pair it extracts both
silhouettes with the same instrument `measure_image.py` uses, normalises them
to a common height, aligns them, and reports:

    iou            intersection over union of the two silhouettes, 0..1
    aspect_delta   render width / reference width after height normalisation
    bands          twelve horizontal slices, each with the render's width as a
                   fraction of the reference's -- this is what makes a failure
                   actionable, because it says WHERE the shape is wrong

    python check_likeness.py --pair render.png reference.png
    python check_likeness.py \
        --pair snap/side.png  ref/03-side.png \
        --pair snap/front.png ref/02-front.png \
        --min 0.90 --report measure/likeness.md

Exit 0 when every pair meets `--min` (default 0.90), 1 when any falls short,
2 on bad usage.

Two things it deliberately does NOT do.

It does not align by anything but the bounding box, so a model that is the
right shape in the wrong *place* still scores well -- placement is what
`inspect align` and the assembly checks are for.

It also refuses a reference whose extracted subject touches the image boundary.
Height normalisation cannot distinguish a cropped object from a short one, so
the resulting IoU would measure the crop as if it were geometry. Use a complete
view for whole-object likeness, or `--allow-clipped-reference` only for an
intentional partial-feature comparison.

And it does not know about colour. On a multi-material reference, colour is a
large part of the likeness a human sees, and this gate is blind to it: a
correct silhouette in one flat colour scores the same as the real thing. Read
the score as a floor on the disagreement, never as a ceiling on the quality.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_image import _flood_components, object_mask  # noqa: E402

NORM_HEIGHT = 480
BANDS = 12
DEFAULT_MIN = 0.90


def clipped_edges(mask: np.ndarray) -> list[str]:
    """Image edges touched by the extracted subject silhouette."""
    contacts = []
    for name, values in (
        ("top", mask[0, :]),
        ("right", mask[:, -1]),
        ("bottom", mask[-1, :]),
        ("left", mask[:, 0]),
    ):
        if values.any():
            contacts.append(name)
    return contacts


def require_complete_reference(mask: np.ndarray, path: Path) -> None:
    """Reject whole-object scoring when the source silhouette is clipped."""
    contacts = clipped_edges(mask)
    if contacts:
        raise ValueError(
            f"reference silhouette touches the image boundary "
            f"({', '.join(contacts)}): {path}; use a complete view, or pass "
            "--allow-clipped-reference only for an intentional partial-feature comparison"
        )


def silhouette(path: Path, threshold: float, largest: bool = True) -> np.ndarray:
    """The subject's silhouette, as the largest connected blob in the frame.

    Keeping only the largest component is not cosmetic. A snapshot rendered
    with `viewLabels` carries a small "ISO" chip in the corner; it is object to
    any threshold, and it stretches the bounding box to the frame's edge. The
    first run of this gate scored the front view at IoU 0.10 with an aspect
    ratio of 1.99 for exactly that reason, and the model was not at fault.
    Render likeness views with `viewLabels: false`, and let this catch the rest.
    """
    image = Image.open(path).convert("RGB")
    rgb = np.asarray(image, dtype=float)
    gray = np.asarray(image.convert("L"), dtype=float)
    mask, _bg, _notes = object_mask(rgb, gray, threshold, invert=False)
    if not mask.any():
        raise ValueError(f"no object found in {path}")
    if largest:
        labels, count = _flood_components(mask)
        if count > 1:
            sizes = np.bincount(labels.ravel())
            sizes[0] = 0
            mask = labels == int(sizes.argmax())
    return mask


def normalise(mask: np.ndarray) -> np.ndarray:
    """Crop to the silhouette's box and scale so its HEIGHT is NORM_HEIGHT.

    Height only, never width: normalising both would divide the aspect ratio
    out of the comparison, and the aspect ratio is the single proportion most
    worth catching.
    """
    ys, xs = np.nonzero(mask)
    box = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = box.shape
    scale = NORM_HEIGHT / h
    out_w = max(1, int(round(w * scale)))
    img = Image.fromarray((box.astype(np.uint8) * 255)).resize(
        (out_w, NORM_HEIGHT), Image.NEAREST)
    return np.asarray(img) > 127


def compare(render: np.ndarray, reference: np.ndarray) -> dict:
    """IoU and per-band widths, with the two silhouettes centred on each other."""
    width = max(render.shape[1], reference.shape[1])
    canvas = []
    for m in (render, reference):
        pad = width - m.shape[1]
        left = pad // 2
        canvas.append(np.pad(m, ((0, 0), (left, pad - left)), constant_values=False))
    a, b = canvas
    inter = int((a & b).sum())
    union = int((a | b).sum())
    iou = inter / union if union else 0.0

    bands = []
    step = NORM_HEIGHT / BANDS
    for i in range(BANDS):
        lo, hi = int(i * step), int((i + 1) * step)
        wa = int(a[lo:hi].any(axis=0).sum())
        wb = int(b[lo:hi].any(axis=0).sum())
        bands.append({
            "band": i,
            "from_top": round(i / BANDS, 3),
            "render_px": wa,
            "reference_px": wb,
            "ratio": round(wa / wb, 3) if wb else None,
        })
    return {
        "iou": round(iou, 4),
        "aspect_delta": round(render.shape[1] / reference.shape[1], 4),
        "bands": bands,
    }


def worst_bands(bands: list[dict], n: int = 3) -> list[dict]:
    scored = [b for b in bands if b["ratio"] is not None]
    scored.sort(key=lambda b: abs(b["ratio"] - 1.0), reverse=True)
    return scored[:n]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pair", nargs=2, action="append", metavar=("RENDER", "REFERENCE"),
                    required=True, help="one render and the reference it copies")
    ap.add_argument("--label", action="append", default=None,
                    help="name for each pair, in order")
    ap.add_argument("--min", type=float, default=DEFAULT_MIN,
                    help=f"minimum IoU per view (default {DEFAULT_MIN})")
    ap.add_argument("--threshold", type=float, default=28.0)
    ap.add_argument("--all-blobs", action="store_true",
                    help="compare the whole mask instead of its largest blob")
    ap.add_argument("--allow-clipped-reference", action="store_true",
                    help="allow a reference silhouette that touches the image boundary; "
                         "only valid for an intentional partial-feature comparison")
    ap.add_argument("--report", type=Path, help="write a markdown report here")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    labels = args.label or []
    results = []
    for i, (render_path, ref_path) in enumerate(args.pair):
        label = labels[i] if i < len(labels) else Path(render_path).stem
        try:
            keep_largest = not args.all_blobs
            render_mask = silhouette(Path(render_path), args.threshold, keep_largest)
            reference_mask = silhouette(Path(ref_path), args.threshold, keep_largest)
            if not args.allow_clipped_reference:
                require_complete_reference(reference_mask, Path(ref_path))
            r = normalise(render_mask)
            f = normalise(reference_mask)
        except (OSError, ValueError) as exc:
            results.append({"label": label, "error": str(exc), "ok": False})
            continue
        rec = compare(r, f)
        rec.update({"label": label, "render": render_path, "reference": ref_path,
                    "ok": rec["iou"] >= args.min})
        results.append(rec)

    scored = [r for r in results if "iou" in r]
    mean_iou = sum(r["iou"] for r in scored) / len(scored) if scored else 0.0
    ok = bool(scored) and all(r["ok"] for r in results)

    payload = {"ok": ok, "min": args.min, "mean_iou": round(mean_iou, 4),
               "views": results}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"{'view':<14}{'IoU':>8}{'aspect':>9}  worst bands (render/reference width)")
        for r in results:
            if "iou" not in r:
                print(f"{r['label']:<14}{'ERROR':>8}  {r['error']}")
                continue
            wb = ", ".join(f"{b['from_top']:.2f}:{b['ratio']}" for b in worst_bands(r["bands"]))
            flag = " " if r["ok"] else "!"
            print(f"{r['label']:<14}{r['iou']:>8.3f}{r['aspect_delta']:>9.3f} {flag} {wb}")
        print()
        print(f"mean IoU {mean_iou:.3f} against a {args.min:.2f} floor -- "
              f"{'ok' if ok else 'BELOW TARGET'}")
        print("bands run top (0.00) to bottom (0.92); ratio > 1 means the model "
              "is too wide there, < 1 too narrow.")

    if args.report:
        lines = [f"# Likeness report\n",
                 f"mean IoU **{mean_iou:.3f}** against a {args.min:.2f} floor "
                 f"-- {'ok' if ok else 'below target'}\n",
                 "| view | IoU | aspect (render/ref) | worst bands |",
                 "|---|---|---|---|"]
        for r in results:
            if "iou" not in r:
                lines.append(f"| {r['label']} | error | — | {r['error']} |")
                continue
            wb = ", ".join(f"{b['from_top']:.2f} → {b['ratio']}" for b in worst_bands(r["bands"]))
            lines.append(f"| {r['label']} | {r['iou']:.3f} | {r['aspect_delta']:.3f} | {wb} |")
        lines.append("\nBands run from the top of the silhouette (0.00) to the "
                     "bottom (0.92). A ratio above 1 means the model is too wide "
                     "at that height, below 1 too narrow.\n")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(lines))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
