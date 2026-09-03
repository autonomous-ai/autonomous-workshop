"""Add communication cues to the exact-state signature render."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
SOURCE = ROOT / "review" / "signature_raw.png"
OUTPUT = ROOT / "snap" / "signature.png"


def font(size):
    for name in (
        "<HOME>/code/autonomous-workshop/.venv/lib/python3.11/site-packages/"
        "matplotlib/mpl-data/fonts/ttf/DejaVuSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


image = Image.open(SOURCE).convert("RGB")
draw = ImageDraw.Draw(image)
ink = (52, 65, 75)
accent = (181, 105, 38)
paper = (244, 239, 230)

# All cues sit in the render's existing clear margins and do not obscure the
# exact meshes. They resolve whole-body motion without claiming physical test.
draw.rounded_rectangle((250, 28, 1750, 116), radius=22, fill=paper, outline=ink, width=4)
headline = "ONE RIGID PIECE — THE WHOLE GARGOYLE ROLLS"
draw.text((1000, 72), headline, font=font(36), fill=ink, anchor="mm")
draw.text((500, 155), "READY · SEATED OVER EDGE", font=font(30), fill=ink, anchor="mm")
draw.text((1500, 155), "CAUGHT · NOSE-DOWN ~70°", font=font(30), fill=ink, anchor="mm")

# A curved arrow crosses the state divider and points down, matching the
# rotation of every visible gargoyle feature around the table edge.
draw.arc((820, 205, 1180, 565), start=210, end=345, fill=accent, width=14)
draw.polygon(((1158, 465), (1196, 520), (1128, 515)), fill=accent)
draw.text((1000, 580), "WHOLE-BODY ROLL", font=font(26), fill=accent, anchor="mm")
draw.text((1000, 948), "Fixed tabletop witness · wings, body, head, paws and tail rotate together",
          font=font(24), fill=ink, anchor="mm")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
image.save(OUTPUT, format="PNG", optimize=True)
print(f"wrote {OUTPUT}")
