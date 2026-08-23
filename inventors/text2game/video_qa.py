#!/usr/bin/env python3
"""Sample a generated clip into one sheet a judge can actually check.

    ./video_qa.py <clip.mp4> <reference.png> [-n 5]   -> <clip>_qa.png

There was no gate on the video at all. A clip came off the gateway, I looked at
a frame or two, and it shipped. Measured on coach-party beat 1, 2026-08-21,
by pulling four frames out afterwards:

  - the coach is a closed red box at t=1 and an open see-through cage at t=4.
    The i2i prompt says "Do NOT add, remove, duplicate, reshape" in as many
    words.
  - the rules spill EXACTLY 5 visitors per round. By t=10 there are visibly
    more than five loose on the board.
  - the pawns grow through the clip.
  - they come to rest leaning on the church, which nothing could roll to from
    the coach ramp.
  - the nine chartreuse villagers mostly vanish.

howto_anim.py's docstring already said this would happen - "it invented faceted
wall patterns the geometry does not have and lifted loose pieces out of the
hopper that is actually empty, so the clip advertised a machine nobody would
receive" - and it happened again because nothing was watching.

This file does the mechanical half: pull frames spread across the clip, put the
STAGED REFERENCE beside them at the same size, and label everything. The
judging is prompts.video_qa(), because whether five pawns became eight is a
question for something that can look.
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CELL_W = 640


def duration(clip: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(clip)],
                       capture_output=True, text=True, timeout=60)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def frame_at(clip: Path, t: float, dst: Path) -> bool:
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i",
                        str(clip), "-frames:v", "1", "-y", str(dst)],
                       capture_output=True, text=True, timeout=120)
    return dst.is_file() and r.returncode == 0


def sample_times(dur: float, n: int) -> list:
    """Spread over the clip, but never the first or last 0.4s.

    The first frame is the i2i still the model was handed, so it always looks
    perfect and proves nothing; the last can be a fade.
    """
    if dur <= 1.2:
        return [dur / 2]
    lo, hi = 0.4, dur - 0.4
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)] if n > 1 else [dur / 2]


def label(im: Image.Image, text: str, tone: str = "#F2EFE6") -> Image.Image:
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype(FONT_PATH, 26)
    except OSError:
        f = ImageFont.load_default()
    d.rectangle([0, 0, im.size[0], 40], fill="#111417")
    d.text((12, 6), text, font=f, fill=tone)
    return im


def sheet(clip: Path, ref: Path, dst: Path, n: int = 5) -> Path:
    """REFERENCE first, then n frames in time order, one grid, same scale."""
    dur = duration(clip)
    if dur <= 0:
        raise SystemExit(f"{clip.name}: ffprobe found no duration")
    tmp = dst.parent / f".{dst.stem}_frames"
    tmp.mkdir(parents=True, exist_ok=True)
    cells = []
    if ref.is_file():
        im = Image.open(ref).convert("RGB")
        im = im.resize((CELL_W, round(CELL_W * im.size[1] / im.size[0])))
        cells.append(label(im, "REFERENCE - the parts as they really are"))
    for i, t in enumerate(sample_times(dur, n)):
        f = tmp / f"f{i}.png"
        if not frame_at(clip, t, f):
            continue
        im = Image.open(f).convert("RGB")
        im = im.resize((CELL_W, round(CELL_W * im.size[1] / im.size[0])))
        cells.append(label(im, f"t = {t:.1f}s"))
    if len(cells) < 2:
        raise SystemExit(f"{clip.name}: could not sample enough frames")
    cols = 2
    rows = (len(cells) + cols - 1) // cols
    ch = max(c.size[1] for c in cells)
    grid = Image.new("RGB", (CELL_W * cols, ch * rows), "#111417")
    for i, c in enumerate(cells):
        grid.paste(c, ((i % cols) * CELL_W, (i // cols) * ch))
    grid.save(dst)
    for f in tmp.glob("*.png"):
        f.unlink()
    tmp.rmdir()
    return dst


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if len(args) < 2:
        print(__doc__)
        return 2
    n = 5
    if "-n" in sys.argv:
        n = int(sys.argv[sys.argv.index("-n") + 1])
    clip, ref = Path(args[0]).resolve(), Path(args[1]).resolve()
    dst = clip.with_name(f"{clip.stem}_qa.png")
    sheet(clip, ref, dst, n)
    print(json.dumps({"clip": clip.name, "reference": ref.name,
                      "sheet": str(dst), "seconds": round(duration(clip), 2),
                      "frames": n}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
