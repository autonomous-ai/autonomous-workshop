"""Bespoke owner foldout for Ouray No. 100.

Run from the Workshop workspace with the active Workshop Python interpreter.
The PDF embeds the exact sealed host hero and Make signature renders directly;
the source images are opened read-only and cropped only in memory.
"""

from pathlib import Path

import reportlab
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A5, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
HERO = WORKSPACE / "artifacts/make/r0001/renders/hero.png"
SIGNATURE = WORKSPACE / "artifacts/make/r0001/product/cad-project/snap/signature.png"
OUT = HERE / "MANUAL.pdf"

FONT_DIR = Path(reportlab.__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("Vera", FONT_DIR / "Vera.ttf"))
pdfmetrics.registerFont(TTFont("VeraBold", FONT_DIR / "VeraBd.ttf"))

W, H = landscape(A5)
CREAM = HexColor("#F2EBDD")
PAPER = HexColor("#FAF6EC")
INK = HexColor("#172018")
GREEN = HexColor("#183A2A")
GREEN_2 = HexColor("#315B43")
BRASS = HexColor("#D7B45A")
OXBLOOD = HexColor("#8F3B2F")
MIST = HexColor("#DDE3D8")
WHITE = HexColor("#FFFFFF")


def fit_lines(text, font, size, width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if pdfmetrics.stringWidth(candidate, font, size) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_block(c, text, x, y, width, size=9, leading=12, color=INK, font="Vera"):
    c.setFont(font, size)
    c.setFillColor(color)
    for line in fit_lines(text, font, size, width):
        c.drawString(x, y, line)
        y -= leading
    return y


def page_base(c, number, section):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.rect(0, H - 18, W, 18, fill=1, stroke=0)
    c.setFillColor(BRASS)
    c.circle(22, H - 9, 3.2, fill=1, stroke=0)
    c.setFont("VeraBold", 7)
    c.setFillColor(WHITE)
    c.drawString(32, H - 12, section.upper())
    c.setStrokeColor(GREEN_2)
    c.setLineWidth(0.8)
    c.line(30, 21, W - 30, 21)
    c.setFont("Vera", 6.5)
    c.setFillColor(GREEN_2)
    c.drawString(30, 10, "OURAY NO. 100  /  OWNER FOLDOUT  /  1:87")
    c.drawRightString(W - 30, 10, f"{number} / 6")


def heading(c, kicker, title, subtitle=None):
    c.setFont("VeraBold", 7.5)
    c.setFillColor(OXBLOOD)
    c.drawString(30, H - 43, kicker.upper())
    c.setFont("VeraBold", 22)
    c.setFillColor(GREEN)
    c.drawString(30, H - 69, title)
    if subtitle:
        text_block(c, subtitle, 30, H - 87, W - 60, 8.5, 11, GREEN_2)


def panel(c, x, y, w, h, number, title, body, accent=BRASS):
    c.setFillColor(CREAM)
    c.setStrokeColor(MIST)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
    c.setFillColor(accent)
    c.circle(x + 20, y + h - 22, 11, fill=1, stroke=0)
    c.setFillColor(GREEN if accent == BRASS else WHITE)
    c.setFont("VeraBold", 10)
    c.drawCentredString(x + 20, y + h - 25.5, str(number))
    c.setFont("VeraBold", 11)
    c.setFillColor(GREEN)
    c.drawString(x + 38, y + h - 26, title)
    text_block(c, body, x + 14, y + h - 48, w - 28, 8, 10.5, INK)


def wheel_row(c, x, y, count, radius=7):
    c.setStrokeColor(GREEN)
    c.setFillColor(MIST)
    for i in range(count):
        cx = x + i * (radius * 2 + 5)
        c.circle(cx, y, radius, fill=1, stroke=1)
        c.circle(cx, y, radius * 0.30, fill=0, stroke=1)
        c.line(cx - radius + 2, y, cx + radius - 2, y)
        c.line(cx, y - radius + 2, cx, y + radius - 2)


def cropped_reader(path, box):
    source = Image.open(path)
    return ImageReader(source.crop(box))


def draw_cover(c):
    c.setFillColor(GREEN)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(BRASS)
    c.rect(0, H - 12, W, 12, fill=1, stroke=0)
    c.setFont("VeraBold", 8)
    c.setFillColor(BRASS)
    c.drawString(32, H - 37, "FERRO LINE  /  OWNER FOLDOUT")
    c.setFont("VeraBold", 32)
    c.setFillColor(WHITE)
    c.drawString(32, H - 74, "Ouray No. 100")
    c.setFont("Vera", 12)
    c.setFillColor(CREAM)
    c.drawString(33, H - 94, "Build the mountain engine. Guide it by hand.")
    c.setFillColor(PAPER)
    c.roundRect(30, 56, W - 60, 238, 12, fill=1, stroke=0)
    hero = cropped_reader(HERO, (180, 430, 1800, 1540))
    c.drawImage(hero, 43, 70, width=W - 86, height=205, preserveAspectRatio=True, anchor="c", mask="auto")
    c.setFillColor(BRASS)
    c.roundRect(33, 29, 170, 24, 12, fill=1, stroke=0)
    c.setFont("VeraBold", 8.5)
    c.setFillColor(GREEN)
    c.drawCentredString(118, 37, "1:87  /  30 NAMED PARTS")
    c.setFont("Vera", 7)
    c.setFillColor(CREAM)
    c.drawRightString(W - 32, 36, "Keep this guide with the model")
    c.showPage()


def draw_inventory(c):
    page_base(c, 2, "Know the parts")
    heading(c, "Inventory", "Thirty parts. Two assemblies.", "Lay the parts on a soft cloth. Match names before fitting; similarly shaped wheelsets belong to different places.")
    x1, x2, top = 30, 305, H - 112
    for x, label, count in ((x1, "LOCOMOTIVE", 16), (x2, "TENDER + COUPLING", 14)):
        c.setFillColor(GREEN)
        c.roundRect(x, top - 26, 255, 26, 7, fill=1, stroke=0)
        c.setFont("VeraBold", 10)
        c.setFillColor(WHITE)
        c.drawString(x + 12, top - 17, label)
        c.setFillColor(BRASS)
        c.drawRightString(x + 242, top - 17, f"{count} PARTS")
    left = [
        ("1", "frame"), ("1", "axle keeper"), ("4", "driver wheelsets"),
        ("1", "pilot truck"), ("1", "pilot wheelset"), ("1", "pilot axle keeper"),
        ("1", "pilot pivot pin"), ("1", "boiler + smokebox"), ("1", "dome cluster"),
        ("1", "diamond stack"), ("1", "cab"), ("1", "headlamp"), ("1", "pilot beam"),
    ]
    right = [
        ("1", "tender frame"), ("1", "tender tank"), ("2", "truck bodies"),
        ("2", "truck keepers"), ("2", "pivot pins"), ("4", "tender wheelsets"),
        ("1", "front coupling bar"), ("1", "rear coupling bar"),
    ]
    for x, rows in ((x1, left), (x2, right)):
        y = top - 45
        for qty, name in rows:
            c.setFillColor(BRASS)
            c.roundRect(x, y - 7, 25, 16, 5, fill=1, stroke=0)
            c.setFillColor(GREEN)
            c.setFont("VeraBold", 8)
            c.drawCentredString(x + 12.5, y - 2, qty)
            c.setFont("Vera", 8.5)
            c.setFillColor(INK)
            c.drawString(x + 34, y - 2, name)
            y -= 19
    wheel_row(c, x2 + 35, 76, 4, 8)
    c.setFont("VeraBold", 8)
    c.setFillColor(GREEN)
    c.drawString(x2, 48, "QUICK CHECK")
    text_block(c, "Four large driver sets, one small pilot set, and four tender sets.", x2 + 82, 48, 170, 7.5, 9.5)
    c.showPage()


def draw_locomotive(c):
    page_base(c, 3, "Build the locomotive")
    heading(c, "Assembly A", "Make the engine roll", "Dry-fit first. Work over a tray so small pins cannot escape. Never force a journal, keeper, or fitting.")
    panel(c, 30, 203, 258, 110, 1, "Seat four drivers", "Turn the frame upside down. Place the four large driver wheelsets into the four open journals. Keep every axle square across the frame.")
    panel(c, 307, 203, 258, 110, 2, "Close the journals", "Lay the long axle keeper along the underside. Check that every wheelset turns before securing any fixed seam.", OXBLOOD)
    panel(c, 30, 72, 258, 110, 3, "Build the pilot truck", "Seat the small pilot wheelset in its truck and close it with the pilot axle keeper. Align the truck beneath the front pivot and insert the pilot pin.", OXBLOOD)
    panel(c, 307, 72, 258, 110, 4, "Add the landmark parts", "Fit boiler + smokebox, cab, dome cluster, diamond stack, headlamp, and pilot beam at their named seams. Keep adhesive away from axles and the pilot pivot.")
    wheel_row(c, 47, 54, 4, 6)
    c.setFont("VeraBold", 7)
    c.setFillColor(GREEN_2)
    c.drawString(117, 51, "FOUR LARGE DRIVERS DEFINE THE 2-8-0 STANCE")
    c.showPage()


def draw_tender(c):
    page_base(c, 4, "Build the tender")
    heading(c, "Assembly B", "Give the tender two trucks", "The front is the end that faces the locomotive. Keep both truck pivots and every axle free of adhesive.")
    panel(c, 30, 203, 258, 110, 1, "Make two rolling trucks", "For each truck, seat two tender wheelsets in the journals. Close the underside with its matching keeper. Test all four axles by hand.")
    panel(c, 307, 203, 258, 110, 2, "Hang the trucks", "Place the front and rear trucks beneath the tender frame. Align each center hole and insert its pivot pin. Confirm both trucks can yaw gently.", OXBLOOD)
    panel(c, 30, 72, 258, 110, 3, "Fit the lettered tank", "Set the SILVERTON R.R. CO. tank on the frame with the lettering outward. Dry-fit the full body before securing fixed seams.", OXBLOOD)
    panel(c, 307, 72, 258, 110, 4, "Seat the two bars", "Place the front bar at the locomotive end and the rear bar at the opposite end. Keep each center span exposed for a hook. Stop if either bar will not seat gently.")
    c.setFillColor(BRASS)
    c.rect(42, 47, 90, 5, fill=1, stroke=0)
    c.rect(W - 132, 47, 90, 5, fill=1, stroke=0)
    c.setFont("VeraBold", 7)
    c.setFillColor(GREEN_2)
    c.drawCentredString(W / 2, 47, "FRONT BAR  <  TENDER  >  REAR BAR")
    c.showPage()


def draw_coupling(c):
    page_base(c, 5, "First use")
    heading(c, "Guide by hand", "Connect. Roll. Release.", "Use a clean, flat desk. Hold the locomotive and tender by their bodies - never by the stack, lamp, lettering, or coupling bar.")
    c.setFillColor(CREAM)
    c.roundRect(30, 178, W - 60, 128, 8, fill=1, stroke=0)
    # Keep the complete three-state source visible and align each third with its
    # matching instruction card below.  The earlier centered image anchor
    # treated x/y as an anchor point and clipped most of the release state.
    strip = cropped_reader(SIGNATURE, (0, 190, 2700, 710))
    c.drawImage(strip, 40, 191, width=W - 80, height=102, preserveAspectRatio=False, mask="auto")
    labels = [
        (30, "1  CONNECT", "Align the tender's front bar beneath the locomotive's rear hook. Lower the hook over the bar."),
        (217, "2  ROLL + YAW", "Push the bodies gently. The wheelsets should turn and the tender should follow with a small angle."),
        (404, "3  RELEASE", "Stop. Lift the locomotive rear only enough to clear the bar, then move the two bodies apart."),
    ]
    for x, title, body in labels:
        c.setFillColor(GREEN)
        c.roundRect(x, 65, 161, 93, 7, fill=1, stroke=0)
        c.setFont("VeraBold", 9)
        c.setFillColor(BRASS)
        c.drawString(x + 12, 139, title)
        text_block(c, body, x + 12, 121, 137, 7.5, 10, WHITE)
    c.setFont("VeraBold", 7.2)
    c.setFillColor(OXBLOOD)
    c.drawString(30, 42, "STOP IF A WHEEL BINDS OR A BAR RESISTS. CHECK ALIGNMENT; DO NOT BEND OR FORCE.")
    c.showPage()


def draw_care(c):
    page_base(c, 6, "Keep it ready")
    heading(c, "Reference", "Fix small problems gently", "Printed fit varies. These checks protect the fine stack, lamp, lettering, wheels, pivots, and coupling bars.")
    sections = [
        (30, "WHEELS BIND", "Confirm the correct wheelset is in each journal. Loosen the keeper, remove dust, reseat the axle square, and test again."),
        (216, "TRUCK WILL NOT YAW", "Check that the pivot pin is upright and no adhesive reaches the joint. Lift and reseat; never twist the truck."),
        (402, "HOOK MISSES BAR", "Place both bodies on the same flat surface. Align the front bar under the hook, then lower. Do not bend the bar."),
    ]
    for x, title, body in sections:
        c.setFillColor(CREAM)
        c.roundRect(x, 218, 163, 94, 7, fill=1, stroke=0)
        c.setFont("VeraBold", 8.5)
        c.setFillColor(OXBLOOD)
        c.drawString(x + 12, 290, title)
        text_block(c, body, x + 12, 271, 139, 7.3, 9.6)
    c.setFillColor(GREEN)
    c.roundRect(30, 65, 257, 132, 8, fill=1, stroke=0)
    c.setFont("VeraBold", 10)
    c.setFillColor(BRASS)
    c.drawString(44, 176, "CARE + PACK AWAY")
    text_block(c, "Uncouple and cradle the locomotive and tender separately. Keep weight off the stack and lamp. Dust with a soft brush; avoid heat, sun, water, and solvents. Store every loose pin and bar with the model. Follow the adhesive maker's ventilation, contact, age, and supervision guidance.", 44, 154, 229, 7.2, 9.3, WHITE)
    c.setFont("VeraBold", 7.2)
    c.setFillColor(BRASS)
    c.drawString(44, 79, "SMALL PARTS - KEEP AWAY FROM")
    c.drawString(44, 69, "CHILDREN AND PETS.")
    c.setFillColor(CREAM)
    c.roundRect(307, 65, 258, 132, 8, fill=1, stroke=0)
    c.setFont("VeraBold", 10)
    c.setFillColor(GREEN)
    c.drawString(321, 176, "HISTORICAL LINEAGE")
    text_block(c, "The Fort Lewis College catalog identifies the 1888 subject as Silverton Railroad No. 100 Ouray and records its 2-8-0 wheel arrangement. Sister Class 60/C-16 records informed the wheel proportions.", 321, 154, 230, 7.6, 10.4)
    c.setFont("VeraBold", 7.5)
    c.setFillColor(OXBLOOD)
    c.drawString(321, 107, "DIGITAL-ONLY CHECK")
    text_block(c, "Fit and rolling were assessed digitally only; neither has been proven on a physical print. Strength and finish also remain untested.", 321, 93, 230, 7.1, 9.4)
    c.showPage()


def build():
    c = canvas.Canvas(
        str(OUT),
        pagesize=(W, H),
        pageCompression=1,
        invariant=1,
        initialFontName="Vera",
    )
    c.setTitle("Ouray No. 100 Owner Foldout")
    c.setAuthor("Ferro Line")
    c.setSubject("Assembly, first use, care, and safety for the 1:87 model")
    draw_cover(c)
    draw_inventory(c)
    draw_locomotive(c)
    draw_tender(c)
    draw_coupling(c)
    draw_care(c)
    c.save()


if __name__ == "__main__":
    build()
