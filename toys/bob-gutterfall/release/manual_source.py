from pathlib import Path

import reportlab
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("MANUAL.pdf")
SIGNATURE = ROOT / "make/r0001/product/cad/gutterfall/snap/signature.png"
ISO = ROOT / "make/r0001/product/cad/gutterfall/snap/iso.png"
fonts = Path(reportlab.__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("Vera", fonts / "Vera.ttf"))
pdfmetrics.registerFont(TTFont("VeraBold", fonts / "VeraBd.ttf"))

W, H = landscape((5 * 72, 7 * 72))
INK = HexColor("#182528")
PAPER = HexColor("#F3E9D2")
STONE = HexColor("#667A73")
MOSS = HexColor("#8BA66B")
EMBER = HexColor("#D96B3B")
MIST = HexColor("#DCE4DA")


def rounded(c, x, y, w, h, fill, radius=9, stroke=None):
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def text(c, s, x, y, size, font="Vera", color=INK):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, s)


def fit_image(c, path, x, y, w, h):
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(img, x + (w-dw)/2, y + (h-dh)/2, dw, dh,
                preserveAspectRatio=True, mask="auto")


def arrow(c, x1, y1, x2, y2, color=EMBER):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(3)
    c.line(x1, y1, x2, y2)
    c.saveState()
    c.translate(x2, y2)
    import math
    c.rotate(math.degrees(math.atan2(y2-y1, x2-x1)))
    p = c.beginPath(); p.moveTo(0, 0); p.lineTo(-9, 5); p.lineTo(-9, -5); p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def page_one(c):
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    rounded(c, 18, 18, W-36, H-36, INK, 14)
    text(c, "GUTTERFALL", 36, H-62, 29, "VeraBold", PAPER)
    text(c, "PRESS. DIVE. CATCH.", 38, H-84, 11, "VeraBold", MOSS)
    rounded(c, 34, 85, W-68, H-190, PAPER, 12)
    fit_image(c, SIGNATURE, 42, 93, W-84, H-206)
    rounded(c, 34, 31, W-68, 40, EMBER, 10)
    text(c, "ONE GARGOYLE. ONE TABLE EDGE. ONE DRAMATIC DROP.", 49, 47, 9.2, "VeraBold", PAPER)


def step_panel(c, x, y, w, h, number, heading, lines):
    rounded(c, x, y, w, h, HexColor("#FFF9EC"), 10, MIST)
    c.setFillColor(EMBER); c.circle(x+22, y+h-24, 14, fill=1, stroke=0)
    text(c, str(number), x+18, y+h-29, 14, "VeraBold", PAPER)
    text(c, heading, x+43, y+h-29, 13, "VeraBold")
    ty = y+h-47
    for line in lines:
        text(c, line, x+18, ty, 7.6)
        ty -= 11


def page_two(c):
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    text(c, "MAKE THE BEAST FALL", 24, H-40, 20, "VeraBold")
    text(c, "Inside: 1 rigid Gutterfall gargoyle", 25, H-58, 8.5, "VeraBold", STONE)

    rounded(c, 24, 177, 112, 106, INK, 10)
    fit_image(c, ISO, 30, 183, 100, 94)
    text(c, "HEAD TO OPEN AIR", 25, 163, 7.5, "VeraBold", EMBER)
    arrow(c, 111, 165, 137, 165)

    step_panel(c, 150, 216, 160, 67, 1, "SEAT", [
        "Use a sturdy, square edge", "18-28 mm thick. Slide the open", "belly-tail throat over it."
    ])
    step_panel(c, 320, 216, 160, 67, 2, "PRESS + RELEASE", [
        "Clear the space below. Press", "the shoulders toward open air,", "then let go as the belly rolls."
    ])
    step_panel(c, 150, 139, 160, 67, 3, "WATCH THE CATCH", [
        "The whole rigid gargoyle turns", "nose-down. Its curled tail should", "meet the underside and stop it."
    ])
    step_panel(c, 320, 139, 160, 67, 4, "RESET", [
        "Grip the body. Lift it back up", "around the same edge until it", "rests flat on top."
    ])

    rounded(c, 24, 25, 456, 92, STONE, 10)
    text(c, "IF IT DOES NOT CATCH", 38, 96, 10.5, "VeraBold", PAPER)
    text(c, "Stop using that edge. Hold the toy; do not let it hit the floor.", 38, 80, 8, "Vera", PAPER)
    text(c, "Try another sturdy 18-28 mm square edge. Never force the throat.", 38, 67, 8, "Vera", PAPER)
    text(c, "Use away from people, pets, glass, heat, stairs, and valuables.", 38, 51, 8, "VeraBold", PAPER)
    text(c, "Check for cracks before use. Wipe dry; store flat. Not a climbing aid.", 38, 38, 8, "Vera", PAPER)


c = Canvas(
    str(OUT),
    pagesize=(W, H),
    pageCompression=1,
    initialFontName="Vera",
    initialFontSize=10,
    initialLeading=12,
)
c.setTitle("Gutterfall Owner Card")
c.setAuthor("Gutterfall")
page_one(c); c.showPage(); page_two(c); c.showPage(); c.save()
print(OUT)
