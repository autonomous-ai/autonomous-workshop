#!/usr/bin/env python3
"""Build the Knockseed two-sided owner card as MANUAL.pdf."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
MADE = ROOT / "artifacts/make/r0001/product"
ISO = MADE / "cad/snap/iso.png"
ART = ROOT / "artifacts/release/work"
OUT = PACKAGE / "MANUAL.pdf"

PAGE_W = 7.5 * inch
PAGE_H = 5.0 * inch
MARGIN = 0.38 * inch

PAPER = HexColor("#F3E4C4")
INK = HexColor("#2C1A0E")
SEED = HexColor("#C48A4A")
DARK = HexColor("#6E3B16")
PANEL = HexColor("#E8CFA8")
RULE = HexColor("#A56A32")


def _crop_seed(src: Path, dest: Path, pad: int = 28) -> Path:
    image = Image.open(src).convert("RGB")
    pixels = image.load()
    w, h = image.size
    bg = pixels[2, 2]
    def is_bg(xy):
        r, g, b = pixels[xy[0], xy[1]]
        return abs(r - bg[0]) < 18 and abs(g - bg[1]) < 18 and abs(b - bg[2]) < 18
    left, top, right, bottom = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            if not is_bg((x, y)):
                left = min(left, x)
                right = max(right, x)
                top = min(top, y)
                bottom = max(bottom, y)
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(w - 1, right + pad)
    bottom = min(h - 1, bottom + pad)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.crop((left, top, right + 1, bottom + 1)).save(dest)
    return dest


def _fonts() -> tuple[str, str, str]:
    import reportlab

    font_dir = Path(reportlab.__file__).resolve().parent / "fonts"
    pdfmetrics.registerFont(TTFont("Vera", str(font_dir / "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("VeraBd", str(font_dir / "VeraBd.ttf")))
    pdfmetrics.registerFont(TTFont("VeraIt", str(font_dir / "VeraIt.ttf")))
    return "Vera", "VeraBd", "VeraIt"


def _rounded_rect(c: canvas.Canvas, x, y, w, h, r, fill=None, stroke=None, width=1):
    c.saveState()
    if fill:
        c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(width)
    p = c.beginPath()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.arcTo(x + w - 2 * r, y, x + w, y + 2 * r, -90, 90)
    p.lineTo(x + w, y + h - r)
    p.arcTo(x + w - 2 * r, y + h - 2 * r, x + w, y + h, 0, 90)
    p.lineTo(x + r, y + h)
    p.arcTo(x, y + h - 2 * r, x + 2 * r, y + h, 90, 90)
    p.lineTo(x, y + r)
    p.arcTo(x, y, x + 2 * r, y + 2 * r, 180, 90)
    p.close()
    c.drawPath(p, fill=1 if fill else 0, stroke=1 if stroke else 0)
    c.restoreState()


def _seed_silhouette(c: canvas.Canvas, cx, cy, scale=1.0, fill=None, stroke=None):
    """Simple ovate seed outline used as a motif, not a substitute for the photo."""
    c.saveState()
    c.translate(cx, cy)
    c.scale(scale, scale)
    p = c.beginPath()
    p.moveTo(-42, 0)
    p.curveTo(-42, 22, -18, 34, 8, 28)
    p.curveTo(28, 22, 40, 10, 46, 0)
    p.curveTo(40, -10, 28, -22, 8, -28)
    p.curveTo(-18, -34, -42, -22, -42, 0)
    p.close()
    if fill:
        c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(1.4)
    c.drawPath(p, fill=1 if fill else 0, stroke=1 if stroke else 0)
    c.restoreState()


def cover(c: canvas.Canvas, regular: str, bold: str, italic: str) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # edge band
    c.setFillColor(DARK)
    c.rect(0, 0, 10, PAGE_H, fill=1, stroke=0)
    c.rect(PAGE_W - 10, 0, 10, PAGE_H, fill=1, stroke=0)

    _seed_silhouette(c, 1.15 * inch, PAGE_H - 0.7 * inch, 0.55, fill=PANEL, stroke=RULE)

    c.setFillColor(DARK)
    c.setFont(bold, 11)
    c.drawString(MARGIN + 6, PAGE_H - 0.42 * inch, "ONE-PIECE TABLE TOY")
    c.setFillColor(INK)
    c.setFont(bold, 36)
    c.drawString(MARGIN + 6, PAGE_H - 0.92 * inch, "KNOCKSEED")
    c.setFillColor(DARK)
    c.setFont(italic, 13)
    c.drawString(MARGIN + 6, PAGE_H - 1.22 * inch, "Flick. Spin. Knock home.")

    # Hero image panel
    img_x = MARGIN + 6
    img_y = 0.72 * inch
    img_w = 4.55 * inch
    img_h = 2.85 * inch
    _rounded_rect(c, img_x - 6, img_y - 6, img_w + 12, img_h + 12, 10, fill=PANEL, stroke=RULE, width=1.2)
    hero = _crop_seed(ISO, ART / "iso-crop.png", pad=40)
    c.drawImage(
        str(hero),
        img_x,
        img_y,
        width=img_w,
        height=img_h,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )

    # Inventory card
    card_x = 5.35 * inch
    card_y = 0.72 * inch
    card_w = 1.75 * inch
    card_h = 2.85 * inch
    _rounded_rect(c, card_x, card_y, card_w, card_h, 10, fill=HexColor("#FFF6E4"), stroke=DARK, width=1.4)
    c.setFillColor(DARK)
    c.setFont(bold, 9)
    c.drawCentredString(card_x + card_w / 2, card_y + card_h - 0.32 * inch, "IN THE BOX")
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    c.line(card_x + 14, card_y + card_h - 0.42 * inch, card_x + card_w - 14, card_y + card_h - 0.42 * inch)

    c.setFillColor(INK)
    c.setFont(bold, 28)
    c.drawCentredString(card_x + card_w / 2, card_y + 1.55 * inch, "1")
    c.setFont(regular, 10)
    c.drawCentredString(card_x + card_w / 2, card_y + 1.28 * inch, "Knockseed")
    c.setFont(italic, 8)
    lines = [
        "One printed seed.",
        "No extra parts.",
        "No glue.",
        "Ready on a table.",
    ]
    y = card_y + 0.95 * inch
    c.setFont(regular, 8)
    c.setFillColor(INK)
    for line in lines:
        c.drawCentredString(card_x + card_w / 2, y, line)
        y -= 0.16 * inch

    c.setFillColor(DARK)
    c.setFont(regular, 8)
    c.drawString(MARGIN + 6, 0.38 * inch, "Turn the card over to play.")
    c.setFont(italic, 8)
    c.drawRightString(PAGE_W - MARGIN, 0.38 * inch, "Keep this card with the seed.")


def play_side(c: canvas.Canvas, regular: str, bold: str, italic: str) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(DARK)
    c.rect(0, 0, 10, PAGE_H, fill=1, stroke=0)
    c.rect(PAGE_W - 10, 0, 10, PAGE_H, fill=1, stroke=0)

    c.setFillColor(INK)
    c.setFont(bold, 16)
    c.drawString(MARGIN + 4, PAGE_H - 0.42 * inch, "How to play")
    c.setFillColor(DARK)
    c.setFont(italic, 9)
    c.drawString(MARGIN + 4, PAGE_H - 0.62 * inch, "Same seed. Same face. Every time.")

    rest = _crop_seed(ART / "rest.png", ART / "rest-crop.png")
    spin = _crop_seed(ART / "knock.png", ART / "spin-crop.png")
    home = _crop_seed(ART / "rest.png", ART / "home-crop.png")
    panels = [
        (rest, "1  FACE DOWN", False, False),
        (spin, "2  FLICK AND SPIN", True, False),
        (home, "3  KNOCK HOME", False, True),
    ]
    strip_x = MARGIN + 2
    strip_y = 2.48 * inch
    strip_w = PAGE_W - 2 * MARGIN - 4
    strip_h = 1.62 * inch
    gap = 0.10 * inch
    panel_w = (strip_w - 2 * gap) / 3
    for i, (img, label, arrows, knock) in enumerate(panels):
        x = strip_x + i * (panel_w + gap)
        _rounded_rect(c, x, strip_y, panel_w, strip_h, 8, fill=HexColor("#FFF6E4"), stroke=RULE, width=1.0)
        img_h = 1.12 * inch
        img_y = strip_y + 0.32 * inch
        c.drawImage(str(img), x + 8, img_y, width=panel_w - 16, height=img_h, preserveAspectRatio=True, anchor="c", mask="auto")
        # table plane
        c.setStrokeColor(DARK)
        c.setLineWidth(1.3)
        table_y = img_y + 0.10 * inch
        c.line(x + 16, table_y, x + panel_w - 16, table_y)
        if arrows:
            c.setStrokeColor(DARK)
            c.setLineWidth(1.5)
            cx = x + panel_w / 2
            cy = img_y + img_h - 0.08 * inch
            c.arc(cx - 28, cy - 10, cx + 28, cy + 18, 20, 140)
            c.line(cx + 24, cy + 14, cx + 30, cy + 8)
            c.line(cx + 24, cy + 14, cx + 18, cy + 8)
        if knock:
            c.setStrokeColor(DARK)
            c.setLineWidth(1.2)
            for dx, dy in ((-10, 8), (0, 11), (10, 8)):
                c.line(x + panel_w / 2 + dx, table_y + 2, x + panel_w / 2 + dx * 1.4, table_y + dy)
        c.setFillColor(DARK)
        c.setFont(bold, 7)
        c.drawCentredString(x + panel_w / 2, strip_y + 8, label)

    # Three steps
    steps = [
        ("1", "Set", "Place the seed on a hard table so the flat oval face sits down."),
        ("2", "Flick", "Snap a fingertip against the rounded equator. Let it turn on its belly."),
        ("3", "Knock", "When the spin dies, the same face meets the table. Pick it up and go again."),
    ]
    box_w = 2.15 * inch
    box_h = 1.15 * inch
    gap = 0.12 * inch
    start_x = MARGIN + 2
    box_y = 1.22 * inch
    for i, (num, verb, body) in enumerate(steps):
        x = start_x + i * (box_w + gap)
        _rounded_rect(c, x, box_y, box_w, box_h, 8, fill=PANEL, stroke=DARK, width=0.9)
        c.setFillColor(DARK)
        c.circle(x + 12, box_y + box_h - 14, 8, fill=1, stroke=0)
        c.setFillColor(HexColor("#FFF6E4"))
        c.setFont(bold, 9)
        c.drawCentredString(x + 12, box_y + box_h - 17, num)
        c.setFillColor(INK)
        c.setFont(bold, 11)
        c.drawString(x + 24, box_y + box_h - 18, verb)
        c.setFont(regular, 8)
        text_obj = c.beginText(x + 10, box_y + box_h - 36)
        text_obj.setLeading(10)
        for line in _wrap(body, 32):
            text_obj.textLine(line)
        c.drawText(text_obj)

    # Footer care / safety
    c.setFillColor(INK)
    c.setFont(bold, 8)
    c.drawString(MARGIN + 4, 0.92 * inch, "Reset")
    c.setFont(regular, 8)
    c.drawString(MARGIN + 42, 0.92 * inch, "Lift the seed. Set the flat face on the table. Flick again. No extra parts.")

    c.setFont(bold, 8)
    c.drawString(MARGIN + 4, 0.70 * inch, "Care")
    c.setFont(regular, 8)
    c.drawString(MARGIN + 42, 0.70 * inch, "Wipe with a dry cloth. Keep it a table toy, not a chew, not a projectile.")

    c.setFont(bold, 8)
    c.drawString(MARGIN + 4, 0.48 * inch, "Safety")
    c.setFont(regular, 8)
    c.drawString(
        MARGIN + 42,
        0.48 * inch,
        "Small object. Keep away from children who mouth toys. Play on a clear table.",
    )

    c.setFillColor(DARK)
    c.setFont(italic, 7.5)
    c.drawString(
        MARGIN + 4,
        0.26 * inch,
        "This card teaches the intended play. It does not prove how a print will sound or last.",
    )


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def main() -> None:
    regular, bold, italic = _fonts()
    if not ISO.is_file() or not (ART / "rest.png").is_file() or not (ART / "knock.png").is_file():
        raise SystemExit("missing sealed product renders")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(
        str(OUT),
        pagesize=(PAGE_W, PAGE_H),
        initialFontName=regular,
        initialFontSize=10,
    )
    c.setTitle("Knockseed owner card")
    c.setAuthor("Autonomous Workshop")
    cover(c, regular, bold, italic)
    c.showPage()
    play_side(c, regular, bold, italic)
    c.showPage()
    c.save()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
