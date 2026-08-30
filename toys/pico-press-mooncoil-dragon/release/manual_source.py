#!/usr/bin/env python3
"""Build the two-sided Mooncoil Dragon owner card."""

from pathlib import Path

import reportlab
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name("MANUAL.pdf")
SIGNATURE = ROOT / "artifacts/make/r0001/product/snap/signature.png"
FONTS = Path(reportlab.__file__).resolve().parent / "fonts"

PAGE = landscape((4 * 72, 6 * 72))
W, H = PAGE
INK = HexColor("#172536")
NIGHT = HexColor("#172536")
PAPER = HexColor("#F7F0DF")
GOLD = HexColor("#D7B867")
SKY = HexColor("#486679")
MIST = HexColor("#A9C2D0")
PALE = HexColor("#FFF9E9")


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("Vera", str(FONTS / "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("VeraBold", str(FONTS / "VeraBd.ttf")))


def rounded_panel(c, x, y, w, h, fill, radius=10, stroke=None):
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1 if stroke else 0)


def label(c, text, x, y, size=8, color=INK, font="VeraBold"):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, text)


def centered(c, text, x, y, size=8, color=INK, font="VeraBold"):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawCentredString(x, y, text)


def wrap(c, text, x, y, width, size=7.2, leading=9, color=INK, font="Vera"):
    c.setFont(font, size)
    c.setFillColor(color)
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = word if not current else current + " " + word
        if pdfmetrics.stringWidth(trial, font, size) <= width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def moon(c, x, y, r, fill=GOLD, cut=NIGHT):
    c.setFillColor(fill)
    c.circle(x, y, r, fill=1, stroke=0)
    c.setFillColor(cut)
    c.circle(x + r * 0.38, y + r * 0.13, r * 0.83, fill=1, stroke=0)


def arrow(c, x1, y1, x2, y2, color=GOLD):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(3)
    c.line(x1, y1, x2, y2)
    c.line(x2, y2, x2 - 8, y2 + 5)
    c.line(x2, y2, x2 - 4, y2 - 8)


def draw_cover(c):
    c.setFillColor(NIGHT)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    for x, y, r in [(28, 260, 1.6), (57, 242, 1), (202, 267, 1.4), (401, 250, 1.2), (375, 274, 1.7)]:
        c.setFillColor(PALE)
        c.circle(x, y, r, fill=1, stroke=0)
    moon(c, 379, 245, 31)
    label(c, "MOONCOIL DRAGON", 28, 258, 9, GOLD)
    label(c, "WAKE", 28, 221, 27, PALE)
    label(c, "THE MOON", 28, 190, 27, PALE)
    wrap(c, "One gentle rock turns a curled dragon into a castle-bearing crescent.", 30, 167, 155, 8.2, 11, MIST)

    # Exact Made signature image, clipped to emphasize the sleeping pose.
    p = c.beginPath()
    p.roundRect(202, 55, 202, 158, 15)
    c.saveState()
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(str(SIGNATURE), 202, 55, width=404, height=227, preserveAspectRatio=False, mask="auto")
    c.restoreState()
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.4)
    c.roundRect(202, 55, 202, 158, 15, fill=0, stroke=1)

    rounded_panel(c, 28, 47, 151, 54, PAPER)
    label(c, "IN THE BOX", 40, 84, 7, SKY)
    label(c, "1 x Mooncoil Dragon", 40, 65, 10, INK)
    label(c, "One solid piece. No assembly.", 40, 53, 6.8, INK, "Vera")
    label(c, "OWNER CARD  /  AGES 14+", 260, 28, 7.2, MIST)


def step_panel(c, x, n, title, body, icon):
    rounded_panel(c, x, 142, 122, 104, PALE, stroke=HexColor("#D7CDB8"))
    c.setFillColor(NIGHT)
    c.circle(x + 18, 226, 11, fill=1, stroke=0)
    centered(c, str(n), x + 18, 222.5, 8, PALE)
    label(c, title, x + 35, 221, 10, NIGHT)
    icon(c, x + 61, 187)
    centered(c, body[0], x + 61, 159, 6.7, INK, "Vera")
    if len(body) > 1:
        centered(c, body[1], x + 61, 150, 6.7, INK, "Vera")


def icon_rest(c, x, y):
    c.setStrokeColor(INK)
    c.setLineWidth(2)
    c.arc(x - 26, y - 10, x + 22, y + 31, 10, 245)
    c.line(x - 24, y - 8, x + 24, y - 8)
    c.setFillColor(GOLD)
    c.circle(x - 5, y + 4, 3, fill=1, stroke=0)


def icon_rock(c, x, y):
    c.setStrokeColor(INK)
    c.setLineWidth(2)
    c.arc(x - 22, y - 11, x + 22, y + 27, 0, 250)
    c.line(x - 12, y - 9, x + 24, y + 7)
    arrow(c, x - 27, y + 22, x + 18, y + 26)


def icon_reveal(c, x, y):
    moon(c, x, y + 3, 20, GOLD, PALE)
    c.setFillColor(INK)
    c.rect(x - 13, y - 14, 23, 10, fill=1, stroke=0)
    c.rect(x - 10, y - 6, 6, 10, fill=1, stroke=0)
    c.rect(x + 2, y - 9, 6, 13, fill=1, stroke=0)


def draw_instructions(c):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    label(c, "ONE GENTLE ROCK. TWO RESTING STORIES.", 24, 268, 13, NIGHT)
    label(c, "Use on a clear, level, hard desk. Keep one hand nearby.", 24, 251, 7.2, SKY, "Vera")

    step_panel(c, 24, 1, "REST", ["Set the long dragon edge", "flat on the desk."], icon_rest)
    step_panel(c, 155, 2, "ROCK", ["Tip the upper-right edge", "clockwise, gently."], icon_rock)
    step_panel(c, 286, 3, "REVEAL", ["Let the straight castle", "edge come to rest."], icon_reveal)

    # Exact two-state Made image, split into two complete state references.
    rounded_panel(c, 24, 65, 188, 64, NIGHT)
    p = c.beginPath()
    p.roundRect(30, 78, 84, 45, 6)
    c.saveState()
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(str(SIGNATURE), 30, 78, width=168, height=45, preserveAspectRatio=False, mask="auto")
    c.restoreState()
    p = c.beginPath()
    p.roundRect(122, 78, 84, 45, 6)
    c.saveState()
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(str(SIGNATURE), 38, 78, width=168, height=45, preserveAspectRatio=False, mask="auto")
    c.restoreState()
    centered(c, "DRAGON REST", 72, 69, 5.7, MIST)
    centered(c, "CASTLE REST", 164, 69, 5.7, MIST)
    label(c, "RESET", 227, 117, 8, SKY)
    wrap(c, "Reverse the rock until the long dragon edge is flat again. Never force or flick it.", 227, 101, 181, 7.4, 9.4, INK)

    rounded_panel(c, 24, 18, 188, 37, HexColor("#E8DFC9"))
    label(c, "IF IT WILL NOT SETTLE", 35, 42, 6.8, NIGHT)
    label(c, "Clear crumbs. Use a firm, level surface. Reset gently.", 35, 28, 6.6, INK, "Vera")
    rounded_panel(c, 222, 18, 186, 37, HexColor("#E8DFC9"))
    label(c, "CARE + SAFETY", 233, 42, 6.8, NIGHT)
    label(c, "Ages 14+. Do not throw. Stop if cracked or sharp.", 233, 28, 6.6, INK, "Vera")


def build():
    register_fonts()
    c = canvas.Canvas(
        str(OUT),
        pagesize=PAGE,
        pageCompression=1,
        invariant=1,
        initialFontName="Vera",
        initialFontSize=10,
    )
    c.setTitle("Mooncoil Dragon Owner Card")
    c.setAuthor("Autonomous Workshop")
    c.setSubject("Self-contained owner instructions")
    draw_cover(c)
    c.showPage()
    draw_instructions(c)
    c.showPage()
    c.save()


if __name__ == "__main__":
    build()
