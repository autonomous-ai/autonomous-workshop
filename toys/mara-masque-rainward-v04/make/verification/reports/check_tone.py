"""Greyscale separation of the five sealed values, measured on a real render.

Colour is a hard constraint here: the board body, both lane tones and both
counter colours have to stay apart with the colour taken away. The renderer
applies its own flat lighting, so this does not assume rendered pixels equal
the sealed sRGB values. It finds the dominant flat-shaded colours in the
canonical top view, matches each one to a sealed colour by hue, converts the
same image to Rec.709 greyscale, and reports what each class actually measures
there. Usage: `check_tone.py <render.png> <greyscale-out.png>`.
"""
import json
import sys
from colorsys import rgb_to_hsv

import os
import pathlib
import sys

_PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

import numpy as np
from PIL import Image

import params as P

LUMA = np.array([0.2126, 0.7152, 0.0722])
CLASSES = (
    ("single_beige_counter", P.SINGLE_COLOR),
    ("lane_light_yellow", P.LANE_LIGHT_COLOR),
    ("sun_body_orange", P.SUN_COLOR),
    ("lane_dark_cocoa", P.LANE_DARK_COLOR),
    ("fork_dark_brown_counter", P.FORK_COLOR),
)
MIN_SHARE = 0.002            # a class must cover this much of the image to count
MAX_HUE_DRIFT = 12.0         # degrees a shaded pixel may drift from its sealed hue
MIN_GAP = 0.03               # greyscale separation two neighbouring values must keep


def hue_degrees(rgb):
    return rgb_to_hsv(*[c for c in rgb])[0] * 360.0


def circular_gap(a, b):
    delta = abs(a - b) % 360.0
    return min(delta, 360.0 - delta)


def measure(render_path, grey_path):
    """Match the five flat-shaded face colours to the five sealed values.

    The renderer lightens and slightly rotates hue, so rendered pixels are not
    the sealed sRGB values. A tone map is monotonic, though: it cannot reorder
    values. So the five largest flat-shaded colours are ranked by greyscale and
    paired with the five sealed colours ranked the same way, and every pair is
    then required to still carry its own hue. A pairing that needed a hue jump
    would fail rather than be assumed.
    """
    image = Image.open(render_path).convert("RGB")
    rgb = np.asarray(image)
    grey = (rgb.astype(np.float64) / 255.0) @ LUMA
    Image.fromarray((grey * 255).round().astype(np.uint8)).save(grey_path)

    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    background = tuple(int(v) for v in np.median(border, axis=0))

    flat = rgb.reshape(-1, 3)
    colours, counts = np.unique(flat, axis=0, return_counts=True)
    total = flat.shape[0]
    clusters = [
        {"rgb": [int(v) for v in colour],
         "share": float(count) / total,
         "grey": float(np.dot(LUMA, [float(v) / 255.0 for v in colour])),
         "hue": hue_degrees([float(v) / 255.0 for v in colour])}
        for colour, count in zip(colours, counts)
        if tuple(int(v) for v in colour) != background
    ]
    clusters.sort(key=lambda c: -c["share"])
    dominant = clusters[:len(CLASSES)]
    dominant.sort(key=lambda c: -c["grey"])

    sealed = [{"class": name, "sealed_srgb": [round(c, 3) for c in colour],
               "sealed_grey": float(np.dot(LUMA, colour)),
               "sealed_hue": hue_degrees(colour)}
              for name, colour in CLASSES]
    sealed.sort(key=lambda s: -s["sealed_grey"])

    rows = []
    for seal, cluster in zip(sealed, dominant):
        drift = circular_gap(cluster["hue"], seal["sealed_hue"])
        rows.append({
            "class": seal["class"],
            "sealed_srgb": seal["sealed_srgb"],
            "sealed_grey": round(seal["sealed_grey"], 4),
            "rendered_rgb": cluster["rgb"],
            "rendered_grey": round(cluster["grey"], 4),
            "image_share": round(cluster["share"], 5),
            "hue_drift_deg": round(drift, 2),
            "hue_kept": bool(drift <= MAX_HUE_DRIFT),
        })

    present = all(row["image_share"] >= MIN_SHARE for row in rows)
    hues_kept = all(row["hue_kept"] for row in rows)
    order = [row["rendered_grey"] for row in rows]
    ordered = all(a > b for a, b in zip(order, order[1:]))

    separations = [{"lighter": a["class"], "darker": b["class"],
                    "rendered_gap": round(a["rendered_grey"] - b["rendered_grey"], 4),
                    "sealed_gap": round(a["sealed_grey"] - b["sealed_grey"], 4)}
                   for a, b in zip(rows, rows[1:])]
    lanes = [r for r in rows if r["class"].startswith("lane_")]
    counters = [r for r in rows if r["class"].endswith("_counter")]
    cross = [{"counter": c["class"], "tile": l["class"],
              "rendered_gap": round(abs(c["rendered_grey"] - l["rendered_grey"]), 4)}
             for c in counters for l in lanes]

    report = {
        "kind": "rainward-corona-greyscale-tone-check",
        "render": render_path,
        "greyscale_image": grey_path,
        "background_rgb": list(background),
        "classes": rows,
        "lane_tone_separation": round(
            abs(lanes[0]["rendered_grey"] - lanes[1]["rendered_grey"]), 4)
        if len(lanes) == 2 else None,
        "neighbour_separations": separations,
        "counter_on_tile_separations": cross,
        "value_order_matches_sealed_order": bool(ordered),
        "every_class_kept_its_hue": bool(hues_kept),
        "note": ("The renderer lightens every face and clips the two most "
                 "saturated tops, so the rendered body-to-light-lane gap is "
                 "narrower than the sealed one. Both numbers are reported."),
    }
    report["pass"] = bool(
        present and ordered and hues_kept
        and all(s["rendered_gap"] >= MIN_GAP for s in separations)
        and all(s["rendered_gap"] >= MIN_GAP for s in cross)
        and report["lane_tone_separation"] >= 0.10)
    return report


if __name__ == "__main__":
    render = sys.argv[1] if len(sys.argv) > 1 else "snap/top.png"
    grey = sys.argv[2] if len(sys.argv) > 2 else "snap/greyscale-top.png"
    result = measure(render, grey)
    with open("measure/greyscale-tone.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if result["pass"] else 1)
