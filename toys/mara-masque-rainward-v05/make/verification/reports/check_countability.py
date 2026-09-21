"""Count the lanes and the four banks in the neutral single-material top view.

The set has to survive being printed in one filament colour, so lane count,
lane boundaries and the four groups of six must read from geometry alone. Each
boundary shows in a top view as a pair of dark edges -- the two tile sides
facing into the recess -- and the distance between that pair is the width of
the exposed body between the tiles. This samples the neutral render around
several rings, groups the dark edges into boundaries, counts them, measures
each width and checks that exactly four are the wide bank boundaries and that
they sit at 24/1, 6/7, 12/13 and 18/19.
Usage: `check_countability.py <neutral-top.png>`.
"""
import json
import sys
from math import atan2, cos, degrees, pi, sin

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
SAMPLE_RADII_MM = (45.0, 60.0, 75.0)
SAMPLES = 14400
PAIR_WINDOW_DEG = 4.0        # two edges this close are one boundary
MIN_EDGE_ARC_MM = 0.10       # ignore marks smaller than this
MIN_BOUNDARY_MM = 0.70       # a real boundary is at least this wide; a counter
                             # edge crossing the ring is a fraction of it


def _ring(grey, centre, pixels_per_mm, radius_mm):
    values = np.empty(SAMPLES)
    for i in range(SAMPLES):
        angle = 2.0 * pi * i / SAMPLES
        x = centre[0] + radius_mm * pixels_per_mm * cos(angle)
        y = centre[1] - radius_mm * pixels_per_mm * sin(angle)
        values[i] = grey[int(round(y)), int(round(x))]
    return values


def _dark_runs(values, threshold):
    dark = values < threshold
    if dark.all() or not dark.any():
        return []
    start = int(np.argmax(~dark))
    runs, current = [], []
    for k in range(len(dark)):
        i = (start + k) % len(dark)
        if dark[i]:
            current.append(i)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    return runs


def _angle_of(run):
    return degrees(atan2(sum(sin(2 * pi * i / SAMPLES) for i in run),
                         sum(cos(2 * pi * i / SAMPLES) for i in run))) % 360.0


def _ring_boundaries(values, radius_mm):
    high = float(np.percentile(values, 80))
    low = float(np.percentile(values, 2))
    threshold = high - 0.35 * (high - low)
    per_sample = 2.0 * pi * radius_mm / SAMPLES
    edges = []
    for run in _dark_runs(values, threshold):
        arc = len(run) * per_sample
        if arc >= MIN_EDGE_ARC_MM:
            edges.append({"angle": _angle_of(run), "arc": arc,
                          "lo": min(run), "hi": max(run)})
    edges.sort(key=lambda e: e["angle"])

    groups, current = [], []
    for edge in edges:
        if current and (edge["angle"] - current[-1]["angle"]) > PAIR_WINDOW_DEG:
            groups.append(current)
            current = []
        current.append(edge)
    if current:
        groups.append(current)
    if len(groups) > 1 and (groups[0][0]["angle"] + 360.0
                            - groups[-1][-1]["angle"]) <= PAIR_WINDOW_DEG:
        groups[0] = groups.pop() + groups[0]

    boundaries = []
    for group in groups:
        first, last = group[0]["angle"], group[-1]["angle"]
        if last < first:
            last += 360.0
        span = (last - first) * pi / 180.0 * radius_mm + (
            group[0]["arc"] + group[-1]["arc"]) / 2.0
        if span >= MIN_BOUNDARY_MM:
            boundaries.append({
                "angle_deg": round(((first + last) / 2.0) % 360.0, 2),
                "width_mm": round(span, 3),
                "edges": len(group),
            })
    return boundaries


def audit(path):
    image = Image.open(path).convert("RGB")
    grey = (np.asarray(image).astype(np.float64) / 255.0) @ LUMA
    border = float(np.median(np.concatenate([grey[0], grey[-1]])))
    mask = np.abs(grey - border) > 0.02
    columns = np.where(mask.any(axis=0))[0]
    rows = np.where(mask.any(axis=1))[0]
    span = max(columns[-1] - columns[0], rows[-1] - rows[0])
    pixels_per_mm = span / (2.0 * P.CORONA_MAX_R)
    centre = ((columns[0] + columns[-1]) / 2.0, (rows[0] + rows[-1]) / 2.0)

    expected = sorted(((P.START_ANGLE + P.PITCH * (p - 1) - P.PITCH / 2.0) % 360.0)
                      for p in (1, 7, 13, 19))
    results = []
    for radius in SAMPLE_RADII_MM:
        boundaries = _ring_boundaries(_ring(grey, centre, pixels_per_mm, radius),
                                      radius)
        widths = [b["width_mm"] for b in boundaries]
        widest = sorted(boundaries, key=lambda b: -b["width_mm"])[:4]
        found = sorted(b["angle_deg"] for b in widest)
        ordinary = sorted(widths)[:-4] or widths
        results.append({
            "radius_mm": radius,
            "boundaries_found": len(boundaries),
            "bank_widths_mm": [round(b["width_mm"], 3) for b in
                               sorted(widest, key=lambda b: b["angle_deg"])],
            "bank_angles_deg": [round(a, 1) for a in found],
            "ordinary_width_median_mm": round(float(np.median(ordinary)), 3),
            "ordinary_width_max_mm": round(max(ordinary), 3),
            "banks_at_expected_angles": bool(
                len(found) == 4 and all(min(abs(f - e), 360.0 - abs(f - e)) < 3.0
                                        for f, e in zip(found, expected))),
            "banks_clearly_wider": bool(
                min(b["width_mm"] for b in widest) > max(ordinary) * 1.25),
            "all_angles_deg": [b["angle_deg"] for b in boundaries],
            "spacing_uniform": bool(len(boundaries) == P.LANES and all(
                abs(((boundaries[(i + 1) % len(boundaries)]["angle_deg"]
                      - boundaries[i]["angle_deg"]) % 360.0) - P.PITCH) < 2.0
                for i in range(len(boundaries)))),
        })

    # a reader counts boundaries across the whole board, not on one circle: a
    # tilted view loses one edge of a boundary whose side faces happen to run
    # along the view direction, so the rings are combined before counting
    combined = []
    for result in results:
        for angle in result["all_angles_deg"]:
            if not any(min(abs(angle - c), 360.0 - abs(angle - c)) < 4.0
                       for c in combined):
                combined.append(angle)
    combined.sort()
    spacing_ok = len(combined) == P.LANES and all(
        abs(((combined[(i + 1) % len(combined)] - combined[i]) % 360.0) - P.PITCH) < 2.0
        for i in range(len(combined)))

    report = {
        "kind": "rainward-corona-neutral-countability",
        "boundaries_over_all_rings": len(combined),
        "boundary_angles_deg": [round(a, 1) for a in combined],
        "boundary_spacing_uniform": bool(spacing_ok),
        "render": path,
        "lanes_expected": P.LANES,
        "expected_bank_angles_deg": [round(a, 1) for a in expected],
        "geometric_body_between_tiles_mm": {"ordinary": P.CHANNEL_W,
                                            "bank": P.BANK_W},
        "geometric_gap_between_tile_tops_mm": {
            "ordinary": round(P.CHANNEL_W + 2 * P.CLEAR, 3),
            "bank": round(P.BANK_W + 2 * P.CLEAR, 3)},
        "rings": results,
    }
    report["pass"] = bool(
        spacing_ok
        and all(r["banks_at_expected_angles"] for r in results)
        and all(r["banks_clearly_wider"] for r in results))
    return report


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "snap/neutral-top.png"
    result = audit(target)
    with open("measure/neutral-countability.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if result["pass"] else 1)
