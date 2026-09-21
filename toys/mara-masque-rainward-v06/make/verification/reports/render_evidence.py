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


def sheet(panels, out):
    images = [Image.open(p).convert("RGB") for p in panels]
    width = sum(i.width for i in images)
    height = max(i.height for i in images)
    board = Image.new("RGB", (width, height), (255, 255, 255))
    x = 0
    for image in images:
        board.paste(image, (x, 0))
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
    sheet(panels, "snap/signature.png")

    greyscale("snap/setup-top.png", "snap/greyscale-top.png")
    crop("snap/top.png", (0.22, 0.00, 0.80, 0.24), 1500, "snap/rim-detail.png")
    crop("snap/setup-top.png", (0.33, 0.33, 0.67, 0.67), 1200, "snap/hub-detail.png")
    crop("snap/greyscale-top.png", (0.14, 0.24, 0.62, 0.66), 1300,
         "snap/greyscale-counter-detail.png")
    print("renders written under snap/")
