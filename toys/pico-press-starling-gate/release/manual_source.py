"""Build the self-contained two-page Starling Gate owner card."""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("MANUAL.pdf")
HERO = ROOT / "make/r0001/product/cad/snap/iso.png"
FONT_DIR = Path("<HOME>/code/autonomous-workshop/.venv/lib/python3.11/site-packages/reportlab/fonts")

INK = HexColor("#20263D")
GOLD = HexColor("#936100")
LIGHT_GOLD = HexColor("#F0C65B")
PAPER = HexColor("#F3F1EA")
SKY = HexColor("#9CB9C8")
WHITE = HexColor("#FFFFFF")
HALF_LETTER = (396, 612)


def fonts():
    pdfmetrics.registerFont(TTFont("Vera", str(FONT_DIR / "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("VeraBold", str(FONT_DIR / "VeraBd.ttf")))


def star(c, x, y, r=5):
    from math import cos, pi, sin
    pts = []
    for i in range(10):
        a = pi / 2 + i * pi / 5
        rr = r if i % 2 == 0 else r * .44
        pts.append((x + rr * cos(a), y + rr * sin(a)))
    p = c.beginPath(); p.moveTo(*pts[0])
    for pt in pts[1:]: p.lineTo(*pt)
    p.close(); c.drawPath(p, fill=1, stroke=0)


def heading(c, kicker, title, y):
    c.setFillColor(GOLD); c.setFont("VeraBold", 8); c.drawString(28, y, kicker.upper())
    c.setFillColor(INK); c.setFont("VeraBold", 22); c.drawString(28, y - 28, title)


def panel(c, x, y, w, h, number, title, body):
    c.setFillColor(WHITE); c.roundRect(x, y, w, h, 12, fill=1, stroke=0)
    c.setFillColor(INK); c.circle(x + 22, y + h - 23, 12, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont("VeraBold", 10); c.drawCentredString(x + 22, y + h - 27, str(number))
    c.setFillColor(INK); c.setFont("VeraBold", 12); c.drawString(x + 42, y + h - 19, title)
    c.setFont("Vera", 8.5); c.setFillColor(HexColor("#46506A"))
    lines = body.split("\n")
    for i, line in enumerate(lines): c.drawString(x + 16, y + h - 43 - 12*i, line)


def footer(c, page):
    c.setStrokeColor(SKY); c.setLineWidth(.6); c.line(28, 24, 368, 24)
    c.setFillColor(INK); c.setFont("Vera", 7); c.drawString(28, 12, "STARLING GATE  •  OWNER CARD")
    c.drawRightString(368, 12, f"{page} / 2")


def build():
    fonts(); c = Canvas(
        str(OUT), pagesize=HALF_LETTER, pageCompression=1,
        initialFontName="Vera", initialFontSize=8.5, initialLeading=10,
    )
    w, h = HALF_LETTER

    # Page 1 — promise, exact visual, inventory, first success.
    c.setFillColor(PAPER); c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(GOLD); star(c, 344, 570, 9); star(c, 366, 550, 4)
    heading(c, "One touch. Two silhouettes.", "Wake the Starling", 572)
    c.setFillColor(HexColor("#46506A")); c.setFont("Vera", 9)
    c.drawString(28, 526, "A perched bird at rest. A shooting star when it rocks.")
    c.drawImage(str(HERO), 73, 260, width=250, height=250, preserveAspectRatio=True, mask='auto')
    # High-contrast action callout over the exact product-derived view.
    c.setStrokeColor(INK); c.setFillColor(INK); c.setLineWidth(2)
    c.line(328, 476, 300, 436); c.line(300, 436, 305, 449); c.line(300, 436, 313, 439)
    c.setFont("VeraBold", 7.5); c.drawRightString(365, 482, "TAP SIDEWAYS")
    c.setFillColor(INK); c.setFont("VeraBold", 9); c.drawString(28, 258, "IN THE BOX")
    c.setFont("Vera", 9); c.drawString(104, 258, "1 × Starling Gate — one solid piece; nothing to assemble")
    panel(c, 28, 137, 108, 98, 1, "SET", "Stand the curved edge\non a level, firm desk.")
    panel(c, 144, 137, 108, 98, 2, "TAP", "Touch one upper\nshoulder lightly.")
    panel(c, 260, 137, 108, 98, 3, "WATCH", "Let it rock freely.\nDo not hold the arch.")
    c.setFillColor(INK); c.roundRect(28, 53, 340, 62, 12, fill=1, stroke=0)
    c.setFillColor(LIGHT_GOLD); c.setFont("VeraBold", 11); c.drawString(44, 91, "READY POSE")
    c.setFillColor(WHITE); c.setFont("Vera", 8.5)
    c.drawString(44, 74, "The gate is upright and the bird appears perched. If it stops tilted,")
    c.drawString(44, 62, "reset it gently by hand—do not force or bend the arch.")
    footer(c, 1); c.showPage()

    # Page 2 — reference, recovery, care and safety.
    c.setFillColor(PAPER); c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(GOLD); star(c, 350, 566, 8)
    heading(c, "Keep the magic effortless", "Rock. Reset. Repeat.", 572)
    c.setFillColor(INK); c.roundRect(28, 405, 340, 110, 14, fill=1, stroke=0)
    c.setFillColor(LIGHT_GOLD); c.setFont("VeraBold", 11); c.drawString(44, 489, "THE WHOLE MOVE")
    c.setFillColor(WHITE); c.setFont("Vera", 9)
    c.drawString(44, 468, "1  Start upright on the curved edge.")
    c.drawString(44, 450, "2  Give one shoulder a light sideways tap.")
    c.drawString(44, 432, "3  Let gravity bring the gate back to its ready pose.")
    c.setFont("Vera", 7.5); c.setFillColor(HexColor("#B7C8D1"))
    c.drawString(44, 416, "Rocking rhythm varies with the tap, desk surface, material, and internal fill.")
    panel(c, 28, 269, 164, 112, "?", "ROCKS TOO LONG", "Use a lighter tap. Move to a\nfirm, level surface. Keep the\ncurved edge clean and dry.")
    panel(c, 204, 269, 164, 112, "?", "BARELY MOVES", "Tap sideways near the upper\nshoulder. Make sure no object\ntouches the gate as it rocks.")
    c.setFillColor(WHITE); c.roundRect(28, 143, 340, 102, 14, fill=1, stroke=0)
    c.setFillColor(INK); c.setFont("VeraBold", 11); c.drawString(44, 221, "CARE & PACK-AWAY")
    c.setFont("Vera", 8.5); c.setFillColor(HexColor("#46506A"))
    c.drawString(44, 201, "• Wipe with a soft, slightly damp cloth; dry before use.")
    c.drawString(44, 185, "• Store flat or upright where it cannot roll or fall.")
    c.drawString(44, 169, "• Stop using it if the body cracks, chips, or develops a sharp edge.")
    c.setFillColor(GOLD); c.roundRect(28, 53, 340, 66, 12, fill=1, stroke=0)
    c.setFillColor(INK); c.setFont("VeraBold", 10); c.drawString(44, 95, "SAFE PLAY")
    c.setFont("Vera", 8); c.drawString(44, 78, "Use on a clear tabletop, away from edges. Keep fingers clear of the")
    c.drawString(44, 65, "rocking contact. This is a desk object, not a throwing or chew toy.")
    footer(c, 2); c.save()


if __name__ == "__main__": build()
