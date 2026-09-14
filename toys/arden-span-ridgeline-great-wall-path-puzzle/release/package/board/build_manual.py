"""Add the numbered-cradle setup to the unchanged original puzzle guide."""
from io import BytesIO
from pathlib import Path
import hashlib
import json
import zipfile
import reportlab
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
MM = 72/25.4
PAGE = 150*MM
M = 10*MM
W = PAGE-2*M
INK = HexColor('#263b40')
fonts = Path(reportlab.__file__).resolve().parent/'fonts'
pdfmetrics.registerFont(TTFont('Guide', str(fonts/'Vera.ttf')))
pdfmetrics.registerFont(TTFont('GuideBold', str(fonts/'VeraBd.ttf')))


def wrapped(c, text, x, y, width=W, size=9, leading=13):
    c.setFont('Guide', size)
    c.setFillColor(INK)
    for para in text.split('\n'):
        line = ''
        for word in para.split():
            candidate = (line+' '+word).strip()
            if line and pdfmetrics.stringWidth(candidate, 'Guide', size)>width:
                c.drawString(x, y, line)
                y -= leading
                line = word
            else:
                line = candidate
        c.drawString(x, y, line)
        y -= leading+4
    return y


def heading(c, kicker, title):
    c.setFillColor(INK)
    c.setFont('GuideBold', 8)
    c.drawString(M, PAGE-M, kicker)
    c.setFont('GuideBold', 18)
    c.drawString(M, PAGE-M-27, title)


def footer(c, number):
    c.setStrokeColor(HexColor('#72756f'))
    c.setLineWidth(.4)
    c.line(M, 21, PAGE-M, 21)
    c.setFillColor(INK)
    c.setFont('Guide', 7)
    c.drawString(M, 11, 'RIDGELINE  /  LEVELS 0 low   1 middle   2 high')
    c.drawRightString(PAGE-M, 11, str(number))


def build():
    with zipfile.ZipFile(ROOT/'board/previous-edition.zip') as z:
        original = z.read('manual.pdf')
    old = PdfReader(BytesIO(original))
    assert len(old.pages) == 12
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=(PAGE, PAGE))
    heading(c, 'A WALL ACROSS THREE HEIGHTS', 'RIDGELINE')
    wrapped(c, '14 route puzzles. Nine mountain-wall modules. One unbroken walk from G1 to G2.', M, PAGE-86, size=11, leading=16)
    c.drawImage(str(ROOT/'renders/assembled-iso.png'), (PAGE-236)/2, 137, width=236, height=177)
    wrapped(c, 'Begin with the numbered tray', M, 118, size=12, leading=16)
    wrapped(c, 'Remove the nine pieces. On the next page, find the engraved grid, cell numbers and north arrow. Then try the guided two-piece starter.', M, 95, size=9, leading=13)
    wrapped(c, '174 x 182 x 63 mm, including the north tab. Digital prototype; physical printing, fit and play have not been tested.', M, 57, size=7.5, leading=10)
    footer(c, 1)
    c.showPage()

    heading(c, 'SET UP THE BOARD', 'Every space has a number')
    c.drawImage(str(ROOT/'renders/cradle-grid-top.png'), (PAGE-250)/2, 165, width=250, height=187.5)
    y = wrapped(c, '1  Turn the tray so the N arrow points away from you. This is N / TOP in every challenge diagram.', M, 150, size=9, leading=13)
    y = wrapped(c, '2  Read cells 0-8 from left to right, top to bottom. Each square takes one piece. The number is covered when that space is filled.', M, y-1, size=9, leading=13)
    y = wrapped(c, '3  Copy the seven fixed pieces on the next page. Leave cells 0 and 1 empty for A and S.', M, y-1, size=9, leading=13)
    wrapped(c, 'The lines guide placement; they do not lock the pieces. Keep the tray flat and lift each piece clear before turning it.', M, y-1, size=8, leading=11)
    footer(c, 2)
    c.showPage()
    c.save()

    writer = PdfWriter()
    for p in PdfReader(BytesIO(output.getvalue())).pages:
        writer.add_page(p)
    # Retain original starter, piece diagrams, 14 challenges, answers and
    # failure examples. Change only their printed page numbers.
    for index, p in enumerate(old.pages[1:], start=3):
        overlay = BytesIO()
        stamp = canvas.Canvas(overlay, pagesize=(PAGE, PAGE))
        stamp.setFillColorRGB(1, 1, 1)
        stamp.rect(PAGE-M-19, 6, 22, 13, fill=1, stroke=0)
        stamp.setFillColor(INK)
        stamp.setFont('Guide', 7)
        stamp.drawRightString(PAGE-M, 11, str(index))
        stamp.save()
        p.merge_page(PdfReader(BytesIO(overlay.getvalue())).pages[0])
        writer.add_page(p)
    writer.add_metadata({'/Title': 'RIDGELINE | Numbered cradle and 14 route puzzles', '/Author': 'Arden Span'})
    dest = ROOT/'manual.pdf'
    with dest.open('wb') as f:
        writer.write(f)
    check = PdfReader(dest)
    assert len(check.pages) == 13
    assert 'Every space has a number' in check.pages[1].extract_text()
    assert 'Bridge the low terrace' in check.pages[2].extract_text()
    report = {'pages': 13, 'original_guide_sha256': hashlib.sha256(original).hexdigest(),
              'manual_sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
              'original_puzzle_pages_retained': 11, 'new_cover_and_board_setup': True}
    (ROOT/'board/manual-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    build()
