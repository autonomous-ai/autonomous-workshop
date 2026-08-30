from pathlib import Path
from io import BytesIO

import reportlab
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("MANUAL.pdf")
ISO = ROOT / "make/r0001/product/cad/snap/iso.png"
SIGNATURE = ROOT / "make/r0001/product/cad/snap/signature.png"
FONT_DIR = Path(reportlab.__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("Vera", FONT_DIR / "Vera.ttf"))
pdfmetrics.registerFont(TTFont("VeraBold", FONT_DIR / "VeraBd.ttf"))

W, H = 5 * inch, 7 * inch
INK = HexColor("#15243A")
BLUE = HexColor("#4D87A8")
PALE = HexColor("#EAF3F5")
GOLD = HexColor("#F2B544")
WHITE = HexColor("#FFFDF7")


def txt(c, x, y, s, size=9, font="Vera", color=INK):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, s)


def fit_image(c, path, x, y, w, h, max_dimensions=None):
    if max_dimensions:
        source = Image.open(path).convert("RGB")
        source.thumbnail(max_dimensions, Image.Resampling.LANCZOS)
        encoded = BytesIO()
        source.save(encoded, format="PNG", optimize=True)
        encoded.seek(0)
        im = ImageReader(encoded)
    else:
        im = ImageReader(str(path))
    iw, ih = im.getSize()
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(im, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh,
                preserveAspectRatio=True, mask="auto")


def rounded(c, x, y, w, h, fill, radius=12, stroke=None):
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1 if stroke else 0)


def step(c, n, heading, body, y):
    c.setFillColor(GOLD)
    c.circle(35, y + 5, 12, fill=1, stroke=0)
    txt(c, 31.2, y + 1.5, str(n), 10, "VeraBold", INK)
    txt(c, 55, y + 8, heading.upper(), 9, "VeraBold", INK)
    txt(c, 55, y - 5, body, 7.6, "Vera", INK)


c = Canvas(
    str(OUT), pagesize=(W, H), pageCompression=1,
    initialFontName="Vera", initialFontSize=9, initialLeading=10.8,
)
c.setTitle("Tempest Lull Owner Card")
c.setAuthor("Autonomous Workshop")

# FRONT — promise, exact product, inventory, orientation.
c.setFillColor(INK); c.rect(0, 0, W, H, fill=1, stroke=0)
txt(c, 28, H - 46, "TEMPEST LULL", 22, "VeraBold", WHITE)
txt(c, 29, H - 65, "A small storm that settles with a nudge.", 9, "Vera", PALE)
rounded(c, 22, 126, W - 44, 300, WHITE, 20)
fit_image(c, ISO, 30, 140, W - 60, 272)
rounded(c, 25, 42, W - 50, 66, PALE, 13)
txt(c, 42, 83, "IN THE BOX", 8, "VeraBold", BLUE)
txt(c, 42, 61, "1  Tempest Lull rocker", 12, "VeraBold", INK)
txt(c, 42, 47, "One connected piece. No assembly.", 7.5, "Vera", INK)
txt(c, W - 108, 83, "CURVE DOWN", 7.4, "VeraBold", BLUE)
c.setStrokeColor(BLUE); c.setLineWidth(2)
c.arc(W - 104, 48, W - 48, 94, 200, 140)
c.line(W - 51, 68, W - 58, 75); c.line(W - 51, 68, W - 61, 64)
txt(c, W - 105, 47, "on the surface", 6.8, "VeraBold", INK)
txt(c, 28, 18, "OWNER CARD  |  AGES 14+", 6.8, "VeraBold", PALE)
c.showPage()

# BACK — exact motion sequence, complete use, reset, troubleshooting and care.
c.setFillColor(WHITE); c.rect(0, 0, W, H, fill=1, stroke=0)
txt(c, 25, H - 35, "SETTLE THE STORM", 17, "VeraBold", INK)
txt(c, 26, H - 51, "The fixed bolt moves with the whole rocker.", 8, "Vera", BLUE)
rounded(c, 22, 310, W - 44, 130, PALE, 15)
fit_image(c, SIGNATURE, 28, 323, W - 56, 102, max_dimensions=(1400, 1050))
c.setStrokeColor(BLUE); c.setLineWidth(2.2)
for x in (118, 236):
    c.line(x, 383, x + 25, 383)
    c.line(x + 25, 383, x + 18, 388)
    c.line(x + 25, 383, x + 18, 378)
txt(c, 42, 318, "REST", 6.8, "VeraBold", INK)
txt(c, W/2 - 13, 318, "CREST", 6.8, "VeraBold", INK)
txt(c, W - 75, 318, "RETURN", 6.8, "VeraBold", INK)

step(c, 1, "Place", "Set the crescent keel on a clean, level, hard surface.", 281)
step(c, 2, "Nudge", "Tap either cloud cheek gently with one finger.", 241)
step(c, 3, "Release", "Let go. Watch the framed bolt sweep as the body returns.", 201)

rounded(c, 22, 91, 152, 86, PALE, 11)
txt(c, 35, 158, "RESET & CARE", 8, "VeraBold", BLUE)
txt(c, 35, 142, "Let it come to rest; set it", 7.3)
txt(c, 35, 131, "upright again if it tips.", 7.3)
txt(c, 35, 114, "Wipe dry. Store indoors,", 7.3)
txt(c, 35, 103, "away from heat and sunlight.", 7.3)

rounded(c, 186, 91, W - 208, 86, HexColor("#FFF3D5"), 11)
txt(c, 199, 158, "IF IT WILL NOT ROCK", 8, "VeraBold", INK)
txt(c, 199, 142, "Clear grit; check that the", 7.3)
txt(c, 199, 131, "surface is level and hard.", 7.3)
txt(c, 199, 114, "Return to center and try a", 7.3)
txt(c, 199, 103, "smaller, gentler nudge.", 7.3)

c.setFillColor(INK); c.rect(0, 0, W, 72, fill=1, stroke=0)
txt(c, 24, 52, "USE SAFELY", 7.5, "VeraBold", GOLD)
txt(c, 24, 38, "Ages 14+. Desk toy, not a children's toy. Do not throw or drop.", 6.8, "Vera", WHITE)
txt(c, 24, 27, "Inspect before use; stop using if cracked, sharp, or damaged.", 6.8, "Vera", WHITE)
txt(c, 24, 16, "Use on a clear surface, away from edges. Keep the arch unobstructed.", 6.8, "Vera", WHITE)
c.save()
