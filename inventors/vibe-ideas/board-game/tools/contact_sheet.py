#!/usr/bin/env python3
"""contact_sheet.py — one image per turn: vision vs. what actually got built.

Each idea becomes a labelled strip — vision render | first-shot build |
repaired build — stacked into a single PNG. This is the five-second human
check on a turn. Scores can drift, rubrics change, and an agent can describe
a build as "largely faithful"; the contact sheet cannot.

Usage:
    python3 board-game/tools/contact_sheet.py --turn 14
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

CELL = 420
PAD = 12
LABEL_H = 26
BG = (250, 250, 249)
FG = (30, 30, 30)
MISSING = (232, 232, 230)


def _cell(path: Path | None, label: str) -> Image.Image:
    tile = Image.new("RGB", (CELL, CELL + LABEL_H), BG)
    draw = ImageDraw.Draw(tile)
    if path and path.exists():
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((CELL, CELL))
            tile.paste(img, ((CELL - img.width) // 2, (CELL - img.height) // 2))
        except OSError:
            path = None
    if not path or not path.exists():
        draw.rectangle([0, 0, CELL, CELL], fill=MISSING)
        draw.text((CELL // 2 - 30, CELL // 2), "— none —", fill=FG)
    draw.text((4, CELL + 6), label[:60], fill=FG)
    return tile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turn", type=int, required=True)
    parser.add_argument("--history-root", default="board-game/history")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    turn_dir = Path(args.history_root) / f"turn-{args.turn}"
    builds = turn_dir / "builds"
    images = turn_dir / "images"
    if not builds.exists():
        print(f"no builds directory at {builds}")
        return 2

    strips: list[Image.Image] = []
    for bdir in sorted(builds.glob("idea-*")):
        slug = bdir.name  # idea-NN-title-slug
        vision = next(iter(sorted(images.glob(f"{slug}.*"))), None) if images.exists() else None
        cells = [
            _cell(vision, f"{slug} — vision"),
            _cell(bdir / "first-shot" / "assembled.png", "first shot"),
            _cell(bdir / "first-shot" / "qa.png", "first shot — QA views"),
            _cell(bdir / "repaired" / "assembled.png", "after repair"),
        ]
        width = len(cells) * CELL + (len(cells) + 1) * PAD
        strip = Image.new("RGB", (width, CELL + LABEL_H + 2 * PAD), BG)
        for i, cell in enumerate(cells):
            strip.paste(cell, (PAD + i * (CELL + PAD), PAD))
        strips.append(strip)

    if not strips:
        print("no idea build directories found")
        return 2

    sheet = Image.new("RGB", (max(s.width for s in strips), sum(s.height for s in strips)), BG)
    y = 0
    for strip in strips:
        sheet.paste(strip, (0, y))
        y += strip.height

    out = Path(args.out) if args.out else turn_dir / f"contact-sheet-turn-{args.turn}.png"
    sheet.save(out)
    print(f"CONTACT_SHEET: {out} ({len(strips)} ideas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
