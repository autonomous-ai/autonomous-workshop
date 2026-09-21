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

from PIL import Image

SKILL = pathlib.Path(os.environ.get("CAD_SKILL_ROOT", "../../../../../.agents/skills/cad"))
PYTHON = os.environ["WORKSHOP_PYTHON"]
SNAP = pathlib.Path("snap")
# exact-state exports live outside the CAD project: the final verifier refuses
# any STEP inside it that has no sibling .step.py entry
STATE_DIR = pathlib.Path("../states")
STATES = (("setup", "colour", "state-setup.step"),
          ("before", "colour", "state-before.step"),
          ("after", "colour", "state-after.step"),
          ("setup", "neutral", "state-neutral.step"),
          ("board", "neutral", "state-neutral-board.step"))


def gen(state, tone, target):
    env = dict(os.environ, RAINWARD_STATE=state, RAINWARD_TONE=tone)
    subprocess.run([PYTHON, str(SKILL / "scripts/gen"), "rainward.step.py",
                    "--write", target, "--force"], check=True, env=env)


def review(source, view, size, out):
    """Render one view, skipping any output this run already produced.

    A 55-solid assembly view costs minutes, so every image is written once and
    the script is safe to re-run until the whole family exists.
    """
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


def state_sheet(panels, out):
    images = [Image.open(p).convert("RGB") for p in panels]
    width = sum(i.width for i in images)
    height = max(i.height for i in images)
    sheet = Image.new("RGB", (width, height), (255, 255, 255))
    x = 0
    for image in images:
        sheet.paste(image, (x, 0))
        x += image.width
    sheet.save(out)
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


if __name__ == "__main__":
    SNAP.mkdir(exist_ok=True)
    STATE_DIR.mkdir(exist_ok=True)
    for state, tone, name in STATES:
        target = STATE_DIR / name
        if not target.exists():
            gen(state, tone, str(target))

    review("../states/state-setup.step", "iso", 1000, "snap/iso.png")
    review("../states/state-setup.step", "top", 1300, "snap/top.png")
    review("../states/state-setup.step", "front", 800, "snap/side-profile.png")
    review("../states/state-neutral.step", "top", 1300, "snap/neutral-top.png")
    review("../states/state-neutral-board.step", "top", 1400,
           "snap/neutral-board-top.png")

    # the signature sheet is three exact states at one fixed view; the setup
    # panel is the canonical iso itself rather than a second render of it
    panels = ["snap/iso.png"]
    for state in ("before", "after"):
        panels.append(review("../states/state-%s.step" % state, "iso", 1000,
                             "../states/state-%s-iso.png" % state))
    state_sheet(panels, "snap/signature.png")

    # targeted close-ups: the crown at the top of the disc, and the hero arch,
    # which spans 261.5 to 293.5 degrees and so sits at the bottom of a top view
    crop("snap/top.png", (0.24, 0.00, 0.80, 0.26), 1500, "snap/rim-detail.png")
    crop("snap/top.png", (0.30, 0.70, 0.84, 1.00), 1500, "snap/hero-detail.png")
    crop("snap/top.png", (0.08, 0.30, 0.46, 0.72), 1200,
         "snap/greyscale-counter-detail.png")
    print("renders written under snap/")
