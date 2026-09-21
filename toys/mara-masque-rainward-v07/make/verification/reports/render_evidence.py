"""Write the canonical render family and the exact-state STEPs it needs.

Presentation only: every image is tessellated from an exact STEP this project
already built. `render_review` is the renderer here rather than
`render_product`, because this set tessellates to several hundred thousand
triangles and `render_product` evenly subsamples anything over 75,000, which
drops most of the surface and produces a torn image. `render_review` keeps the
occurrence colours and the whole mesh. Run it from the CAD project directory.
"""
import os
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, ".")

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import params as P
import profiles as G

SKILL = pathlib.Path(os.environ.get(
    "CAD_SKILL_ROOT", "../../../../../.agents/skills/cad")).resolve()
PYTHON = os.environ["WORKSHOP_PYTHON"]
SNAP = pathlib.Path("snap")
# exact-state exports live outside the CAD project: the final verifier refuses
# any STEP inside it that has no sibling .step.py entry
STATE_DIR = pathlib.Path("../states")
STATES = (("setup", "colour", "state-setup.step"),
          ("before", "colour", "state-before.step"),
          ("after", "colour", "state-after.step"),
          ("board", "colour", "state-board.step"),
          ("setup", "neutral", "state-neutral.step"),
          ("board", "neutral", "state-neutral-board.step"))


def gen(state, tone, target):
    env = dict(os.environ, RAINWARD_STATE=state, RAINWARD_TONE=tone)
    subprocess.run([PYTHON, str(SKILL / "scripts/gen"), "rainward.step.py",
                    "--write", target, "--force"], check=True, env=env)


def review(source, view, size, out):
    """Render one view, skipping any output this run already produced."""
    if pathlib.Path(out).exists():
        print("keep", out)
        return out
    scratch = SNAP / "_scratch"
    subprocess.run([PYTHON, str(SKILL / "scripts/render_review"), source,
                    "--view", view, "--size", str(size), "-o", str(scratch)],
                   check=True)
    shutil.move(str(scratch / ("%s.png" % view)), out)
    shutil.rmtree(scratch, ignore_errors=True)
    return out


def _font(size, bold=False):
    """A legible face if the host has one, the bitmap default if not."""
    names = (["/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold else
             ["/System/Library/Fonts/Supplemental/Arial.ttf"])
    names += ["/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _plan_bounds():
    """Model-space bounds of the whole part, the same ones the renders frame to."""
    import math
    xs, ys = [], []
    for i in range(P.CORONA_COUNT):
        for x, y in G.tongue_face_outline(i, 64):
            xs.append(x)
            ys.append(y)
    for k in range(721):
        a = math.radians(k * 0.5)
        xs.append(P.SUN_R * math.cos(a))
        ys.append(P.SUN_R * math.sin(a))
    return min(xs), max(xs), min(ys), max(ys)


def _mark_bar(panel, draw, offset):
    """Ring the centre bar on one panel, so the named location is named.

    The critic that read this sheet cold took the counter parked on the bar for
    a piece that had fallen off, and said so again after captions were added:
    "Cover the captions and panel 3 is indistinguishable in kind from my first
    cold read ... nothing marks it as a named location rather than as
    decoration." A caption states the capture; this shows it.
    """
    a = np.asarray(panel.convert("RGB")).astype(np.float64) / 255.0
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    ys, xs = np.nonzero((sat > 0.25) & (mx > 0.35))
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    lo_x, hi_x, lo_y, hi_y = _plan_bounds()
    px = (x1 - x0 + 1) / (hi_x - lo_x)
    cx = x0 - lo_x * px + offset[0]
    cy = y1 + lo_y * px + offset[1]
    r = P.BAR_R * px + 10
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(200, 40, 40), width=4)
    label = "THE CENTRE BAR"
    font = _font(22, bold=True)
    w = draw.textlength(label, font=font)
    draw.text((cx - w / 2, cy + r + 10), label, fill=(200, 40, 40), font=font)


def _wrap(draw, text, font, width):
    """Break one caption to the panel width, so no line is cut off."""
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if line and draw.textlength(trial, font=font) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def sheet(panels, out, captions=None, mark_bar_on=None):
    """Paste the exact-state renders side by side, each named.

    The three panels are three positions of the same game at one fixed
    overhead view and one fixed scale, not three angles on one position. An
    independent critic read the third panel cold and took the counter parked on
    the centre bar for a dropped piece - "a stray dark teardrop ... that is a
    floating/misplaced part" - and held that flag through two rounds. The
    geometry was right: that counter is the hit drop, resting on the bar top at
    Z 6.2. What was missing was any grammar in the image saying so, and a
    signature sheet that needs a caption elsewhere to be read has not carried
    its own evidence.
    """
    images = [Image.open(p).convert("RGB") for p in panels]
    title_font, body_font = _font(30, bold=True), _font(24)
    band = 112 if captions else 0
    width = sum(i.width for i in images)
    height = max(i.height for i in images) + band
    board = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(board)
    x = 0
    for index, image in enumerate(images):
        board.paste(image, (x, band))
        if captions:
            title, note = captions[index]
            draw.text((x + 18, 14), title, fill=(0, 0, 0), font=title_font)
            y = 52
            for line in _wrap(draw, note, body_font, image.width - 36):
                draw.text((x + 18, y), line, fill=(70, 70, 70), font=body_font)
                y += 26
            if index:
                draw.line([(x, 0), (x, height)], fill=(210, 210, 210), width=2)
        if mark_bar_on is not None and index == mark_bar_on:
            _mark_bar(image, draw, (x, band))
        x += image.width
    board.save(out)
    return out


def crop(source, box, width, out):
    image = Image.open(source).convert("RGB")
    w, h = image.size
    left, top, right, bottom = (int(w * box[0]), int(h * box[1]),
                                int(w * box[2]), int(h * box[3]))
    piece = image.crop((left, top, right, bottom))
    scale = width / piece.width
    piece.resize((width, max(int(piece.height * scale), 1)), Image.LANCZOS).save(out)
    return out


def greyscale(source, out):
    Image.open(source).convert("RGB").convert("L").convert("RGB").save(out)
    return out


if __name__ == "__main__":
    SNAP.mkdir(exist_ok=True)
    STATE_DIR.mkdir(exist_ok=True)
    for state, tone, name in STATES:
        target = STATE_DIR / name
        if not target.exists():
            gen(state, tone, str(target))

    review("../states/state-setup.step", "iso", 1100, "snap/iso.png")
    review("../states/state-setup.step", "top", 1600, "snap/setup-top.png")
    review("../states/state-setup.step", "front", 1200, "snap/side-profile.png")
    review("../states/state-board.step", "top", 2000, "snap/top.png")
    review("../states/state-neutral.step", "top", 1500, "snap/neutral-top.png")
    review("../states/state-neutral-board.step", "top", 1600,
           "snap/neutral-board-top.png")

    # the signature sheet is three exact states at one fixed overhead view, so
    # the drop that is hit, displaced and parked on the centre bar can be read
    # off the board rather than inferred from a change of angle
    panels = []
    for state in ("setup", "before", "after"):
        panels.append(review("../states/state-%s.step" % state, "top", 1100,
                             "../states/state-%s-top.png" % state))
    sheet(panels, "snap/signature.png", mark_bar_on=2, captions=(
        ("1.  OPENING POSITION",
         "Fifteen cream drops and fifteen dark drops, each side set on its own "
         "24, 13, 8 and 6 points."),
        ("2.  BEFORE THE HIT",
         "A cream drop is about to land on the dark side's point 1, where a "
         "single dark drop stands alone."),
        ("3.  AFTER THE HIT",
         "The dark drop is not lost. It is held on the centre bar, ringed below, "
         "and must re-enter before its owner moves again."),
    ))

    greyscale("snap/setup-top.png", "snap/greyscale-top.png")
    crop("snap/top.png", (0.22, 0.00, 0.80, 0.24), 1500, "snap/rim-detail.png")
    crop("snap/setup-top.png", (0.33, 0.33, 0.67, 0.67), 1200, "snap/hub-detail.png")
    crop("snap/greyscale-top.png", (0.14, 0.24, 0.62, 0.66), 1300,
         "snap/greyscale-counter-detail.png")
    print("renders written under snap/")
