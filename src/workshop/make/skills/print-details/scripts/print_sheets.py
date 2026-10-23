#!/usr/bin/env python3
"""Lay a Design Contract's Print Pieces out on A4 Print Sheets (ADR 0091).

The layout is deterministic: the same contract and art give the same pages
and the same bytes. No agent places a piece. For every stock the contract
declares, pieces are packed onto as many A4 pages as they need, numbered
``<stock>-<n>``. Each page prints the art clipped to its piece's cut line,
the cut line solid, every fold line dashed, each piece's id beside it and a
1:1 scale bar.

    print_sheets.py --contract CONTRACT.md --art DIR -o OUT [--check]

``--contract`` reads a Design Contract (the fenced ``design-contract`` block
of a ``.md`` file), a run's ``WISH.json`` or the contract's JSON itself.
``--art`` is the directory holding every ``print.art`` file under its name.
It writes ``print-sheets.pdf``, one ``sheet-<stock>-<n>.png`` preview per
page and ``print-sheets.json``, the layout and every check. ``--check``
writes only the JSON.

It exits 0 when every check passes, 1 when any fails (the files are still
written so the failure can be seen), 2 on unusable input. The checks are
the layout half of the Print Sheet gate: every piece is placed, inside the
printable area, overlapping none; every cut edge meets the scissors limit;
every art file exists, matches its piece's shape and prints at 300 dpi or
more. Measuring the model against the declared sizes is the other half.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

PAGE_MM = (210.0, 297.0)
MARGIN_MM = 10.0
HEADER_MM = 14.0
GAP_MM = 3.0
LABEL_MM = 3.5
MIN_DPI = 300.0
ASPECT_TOLERANCE = 0.03
MIN_CUT_EDGE_MM = 5.0
WRAP_OVERLAP_MM = 5.0
STAND_TAB_MM = 5.0
# The gores of a sphere strip stay joined in a band this far either side of
# the equator; the cuts between them stop at its edge.
SPHERE_BAND_DEGREES = 8.0
OVAL_SEGMENTS = 144
GORE_SEGMENTS = 24
PREVIEW_DPI = 100
STOCK_ORDER = ("paper", "sticker", "card", "film")
CUT_LINE_MM = 0.2
FOLD_DASH_MM = (2.0, 1.5)
SCALE_BAR_MM = 50.0
SCHEMA_VERSION = 1
KIND = "print-sheets"

_FENCE = re.compile(r"```design-contract\s*\n(.*?)```", re.DOTALL)


class UsageError(Exception):
    """The input cannot be laid out at all."""


# -- the contract -------------------------------------------------------------

def load_contract(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        match = _FENCE.search(text)
        if match is None:
            raise UsageError("%s has no design-contract block" % path)
        text = match.group(1)
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise UsageError("%s does not parse as JSON: %s" % (path, exc)) from exc
    if isinstance(document, dict) and isinstance(document.get("context"), dict):
        document = document["context"].get("design_contract")
    if not isinstance(document, dict) or not isinstance(document.get("print"), dict):
        raise UsageError("%s declares no Print Sheets (schema 6 print section)" % path)
    section = document["print"]
    for key in ("stocks", "art", "pieces"):
        if not section.get(key):
            raise UsageError("the print section has no %s" % key)
    return document


# -- one piece's shape ---------------------------------------------------------

def _rect(width: float, height: float) -> list:
    return [(0.0, 0.0), (width, 0.0), (width, height), (0.0, height)]


def _oval(width: float, height: float, base: float = 0.0) -> list:
    a, b = width / 2.0, height / 2.0
    return [
        (a + a * math.cos(2 * math.pi * k / OVAL_SEGMENTS),
         base + b + b * math.sin(2 * math.pi * k / OVAL_SEGMENTS))
        for k in range(OVAL_SEGMENTS)
    ]


def _stand(width: float, height: float, slot: float, oval: bool) -> list:
    """The card above a tab ``slot`` wide and STAND_TAB_MM deep that goes
    into the slot; the tab is centred under the card."""

    tab = STAND_TAB_MM
    left, right = (width - slot) / 2.0, (width + slot) / 2.0
    if not oval:
        return [(left, 0.0), (right, 0.0), (right, tab), (width, tab), (width, tab + height),
                (0.0, tab + height), (0.0, tab), (left, tab)]
    a, b = width / 2.0, height / 2.0
    cy = tab + b
    # Where each side of the tab meets the oval's lower half, as the angle of
    # the oval's parameter; the cut runs anticlockwise over the top between.
    across = slot / 2.0 / a
    start = math.atan2(-math.sqrt(max(0.0, 1.0 - across ** 2)), across)
    end = math.atan2(-math.sqrt(max(0.0, 1.0 - across ** 2)), -across) + 2 * math.pi
    arc = [
        (a + a * math.cos(start + (end - start) * k / OVAL_SEGMENTS),
         cy + b * math.sin(start + (end - start) * k / OVAL_SEGMENTS))
        for k in range(OVAL_SEGMENTS + 1)
    ]
    return [(left, 0.0), (right, 0.0)] + arc


def _sphere(diameter: float, gores: int) -> tuple:
    """One strip of ``gores`` joined gores, poles up and down. Each gore is
    as wide at latitude phi as the sphere's circumference there divided by
    the gore count; the gores stay joined in a band about the equator."""

    width, height = math.pi * diameter, math.pi * diameter / 2.0
    half = width / (2.0 * gores)
    band = math.radians(SPHERE_BAND_DEGREES)
    band_y = height / 2.0 * band / (math.pi / 2.0)

    def side(sign: float) -> list:
        """The top (sign 1) or bottom (sign -1) edge, left to right."""

        points = []
        for gore in range(gores):
            centre = (gore + 0.5) * width / gores
            for k in range(GORE_SEGMENTS + 1):
                phi = band + (math.pi / 2.0 - band) * k / GORE_SEGMENTS
                y = height / 2.0 + sign * (height / 2.0) * phi / (math.pi / 2.0)
                points.append((centre - half * math.cos(phi), y))
            for k in range(GORE_SEGMENTS - 1, -1, -1):
                phi = band + (math.pi / 2.0 - band) * k / GORE_SEGMENTS
                y = height / 2.0 + sign * (height / 2.0) * phi / (math.pi / 2.0)
                points.append((centre + half * math.cos(phi), y))
        return points

    middle = height / 2.0
    # Up the left end, along the top gores, down the right end, then back
    # along the bottom gores, right to left.
    outline = [(0.0, middle - band_y), (0.0, middle + band_y)] + side(1.0)
    outline += [(width, middle + band_y), (width, middle - band_y)] + side(-1.0)[::-1]
    return outline, width, height


def piece_shape(piece: dict, stocks: dict) -> dict:
    """The cut outline, fold lines and size, in mm, of one piece laid flat."""

    way = piece["way"]
    caliper = float(stocks[piece["stock"]]["caliper_mm"])
    folds: list = []
    edges: list = []
    if way in ("flat", "sticker"):
        width, height = (float(v) for v in piece["size_mm"])
        oval = piece.get("outline") == "oval"
        outline = _oval(width, height) if oval else _rect(width, height)
        edges = [width, height]
    elif way == "stand":
        card_w, card_h = (float(v) for v in piece["size_mm"])
        slot = float(piece["slot_mm"])
        outline = _stand(card_w, card_h, slot, piece.get("outline") == "oval")
        width, height = card_w, card_h + STAND_TAB_MM
        folds = []
        edges = [card_w, card_h, slot, STAND_TAB_MM]
    elif way == "wrap":
        block_h, block_w, block_d = (float(v) for v in piece["block_mm"])
        if piece["around"] == "cover":
            panels = [block_w, block_d, block_w]
            width = 2 * block_w + block_d + 2 * caliper
        else:
            panels = [block_w, block_d, block_w, block_d]
            width = 2 * block_w + 2 * block_d + 4 * caliper + WRAP_OVERLAP_MM
        height = block_h
        x = 0.0
        for panel in panels[:-1] if piece["around"] == "cover" else panels:
            x += panel + caliper
            folds.append(((x, 0.0), (x, height)))
        outline = _rect(width, height)
        edges = [height, width]
    elif way == "sphere":
        outline, width, height = _sphere(float(piece["diameter_mm"]), int(piece["gores"]))
        edges = []  # ADR 0091 decision 5: the one piece allowed points.
        folds.append(((0.0, height / 2.0), (width, height / 2.0)))
    elif way == "fold":
        page_w, page_h = (float(v) for v in piece["page_mm"])
        pages = int(piece["pages"])
        width, height = page_w * pages, page_h
        folds = [((page_w * k, 0.0), (page_w * k, height)) for k in range(1, pages)]
        outline = _rect(width, height)
        edges = [page_w, page_h]
    else:
        raise UsageError("piece %s has an unknown way %r" % (piece.get("id"), way))
    return {"outline": outline, "folds": folds, "width": width, "height": height, "edges": edges}


# -- packing -----------------------------------------------------------------

def _printable() -> tuple:
    return (PAGE_MM[0] - 2 * MARGIN_MM, PAGE_MM[1] - 2 * MARGIN_MM - HEADER_MM)


def pack(items: list) -> tuple:
    """Shelf-pack ``items`` (dicts with width/height) onto pages, tallest
    first. A piece wider than the printable width turns a quarter turn when
    that makes it fit. Returns (pages of placements, unplaced items)."""

    usable_w, usable_h = _printable()
    order = sorted(items, key=lambda item: (-max(item["width"], item["height"]), item["key"]))
    pages: list = []
    unplaced: list = []
    page: list = []
    x = y = row = 0.0
    for item in order:
        width, height, rotated = item["width"], item["height"], False
        if width > usable_w and height <= usable_w:
            width, height, rotated = height, width, True
        cell_h = height + LABEL_MM
        if width > usable_w or cell_h > usable_h:
            unplaced.append(item)
            continue
        if x > 0 and x + width > usable_w:
            x, y, row = 0.0, y + row + GAP_MM, 0.0
        if y + cell_h > usable_h:
            pages.append(page)
            page, x, y, row = [], 0.0, 0.0, 0.0
        page.append({**item, "x": MARGIN_MM + x,
                     "y": PAGE_MM[1] - MARGIN_MM - HEADER_MM - y - height,
                     "placed_w": width, "placed_h": height, "rotated": rotated})
        x += width + GAP_MM
        row = max(row, cell_h)
    if page:
        pages.append(page)
    return pages, unplaced


# -- checks ------------------------------------------------------------------

def _art_size(path: Path):
    from PIL import Image

    with Image.open(path) as image:
        return image.size


def check_layout(contract: dict, art_dir: Path, sheets: list, unplaced: list) -> list:
    failures: list = []
    usable_top = PAGE_MM[1] - MARGIN_MM - HEADER_MM
    for item in unplaced:
        failures.append("%s does not fit on an A4 sheet (%.1f x %.1f mm)"
                        % (item["label"], item["width"], item["height"]))
    for sheet in sheets:
        boxes = []
        for place in sheet["pieces"]:
            left, bottom = place["x"], place["y"]
            right, top = left + place["placed_w"], bottom + place["placed_h"]
            if (left < MARGIN_MM - 1e-6 or right > PAGE_MM[0] - MARGIN_MM + 1e-6
                    or bottom - LABEL_MM < MARGIN_MM - 1e-6 or top > usable_top + 1e-6):
                failures.append("%s leaves the printable area of sheet %s"
                                % (place["label"], sheet["sheet"]))
            for other, box in boxes:
                if (left < box[2] + GAP_MM - 1e-6 and box[0] < right + GAP_MM - 1e-6
                        and bottom - LABEL_MM < box[3] + GAP_MM - 1e-6
                        and box[1] - LABEL_MM < top + GAP_MM - 1e-6):
                    failures.append("%s and %s are closer than %g mm on sheet %s"
                                    % (place["label"], other, GAP_MM, sheet["sheet"]))
            boxes.append((place["label"], (left, bottom, right, top)))
    seen_art: dict = {}
    for piece in contract["print"]["pieces"]:
        shape = piece_shape(piece, contract["print"]["stocks"])
        for edge in shape["edges"]:
            if edge < MIN_CUT_EDGE_MM - 1e-9:
                failures.append("%s has a %.1f mm edge, under the %g mm scissors limit"
                                % (piece["id"], edge, MIN_CUT_EDGE_MM))
        path = art_dir / piece["art"]
        if piece["art"] not in seen_art:
            seen_art[piece["art"]] = _art_size(path) if path.is_file() else None
        size = seen_art[piece["art"]]
        if size is None:
            failures.append("%s: art %s is missing" % (piece["id"], piece["art"]))
            continue
        dpi = min(size[0] / (shape["width"] / 25.4), size[1] / (shape["height"] / 25.4))
        if dpi < MIN_DPI - 1e-6:
            failures.append("%s: art %s prints at %.0f dpi, under %g"
                            % (piece["id"], piece["art"], dpi, MIN_DPI))
        aspect = (size[0] / size[1]) / (shape["width"] / shape["height"])
        if abs(aspect - 1.0) > ASPECT_TOLERANCE:
            failures.append("%s: art %s is %dx%d px, the wrong shape for a %.1f x %.1f mm piece"
                            % (piece["id"], piece["art"], size[0], size[1],
                               shape["width"], shape["height"]))
    return failures


# -- drawing -----------------------------------------------------------------

def _mm(value: float) -> float:
    return value * 72.0 / 25.4


def _path(canvas, points, rotated, place):
    path = canvas.beginPath()
    for index, (px, py) in enumerate(points):
        x, y = _to_page(px, py, rotated, place)
        (path.moveTo if index == 0 else path.lineTo)(_mm(x), _mm(y))
    path.close()
    return path


def _to_page(px, py, rotated, place):
    if not rotated:
        return place["x"] + px, place["y"] + py
    # A quarter turn anticlockwise: the piece's height runs along the page.
    return place["x"] + place["placed_w"] - py, place["y"] + px


def draw(contract: dict, art_dir: Path, sheets: list, pdf_path: Path) -> None:
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as pdf_canvas

    stocks = contract["print"]["stocks"]
    canvas = pdf_canvas.Canvas(str(pdf_path), pagesize=(_mm(PAGE_MM[0]), _mm(PAGE_MM[1])),
                               invariant=1)
    canvas.setTitle("%s Print Sheets" % contract.get("title", ""))
    canvas.setCreator("print_sheets.py (ADR 0091)")
    readers: dict = {}
    for sheet in sheets:
        top = PAGE_MM[1] - MARGIN_MM
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(_mm(MARGIN_MM), _mm(top - 4), "%s  -  sheet %s  -  %s" % (
            contract.get("title", ""), sheet["sheet"], stocks[sheet["stock"]]["name"]))
        canvas.setFont("Helvetica", 6.5)
        canvas.drawString(_mm(MARGIN_MM), _mm(top - 8),
                          "Print at 100% (actual size). Cut on solid lines, fold on dashed lines.")
        bar_x = PAGE_MM[0] - MARGIN_MM - SCALE_BAR_MM
        canvas.setLineWidth(_mm(0.3))
        canvas.line(_mm(bar_x), _mm(top - 6), _mm(bar_x + SCALE_BAR_MM), _mm(top - 6))
        for tick in range(0, int(SCALE_BAR_MM) + 1, 10):
            canvas.line(_mm(bar_x + tick), _mm(top - 6), _mm(bar_x + tick), _mm(top - 4.5))
        canvas.drawRightString(_mm(PAGE_MM[0] - MARGIN_MM), _mm(top - 10), "%g mm" % SCALE_BAR_MM)
        for place in sheet["pieces"]:
            piece, shape, rotated = place["piece"], place["shape"], place["rotated"]
            if piece["art"] not in readers:
                path = art_dir / piece["art"]
                readers[piece["art"]] = ImageReader(str(path)) if path.is_file() else None
            canvas.saveState()
            canvas.clipPath(_path(canvas, shape["outline"], rotated, place), stroke=0, fill=0)
            reader = readers[piece["art"]]
            if reader is not None:
                if rotated:
                    canvas.translate(_mm(place["x"] + place["placed_w"]), _mm(place["y"]))
                    canvas.rotate(90)
                else:
                    canvas.translate(_mm(place["x"]), _mm(place["y"]))
                canvas.drawImage(reader, 0, 0, _mm(shape["width"]), _mm(shape["height"]))
            canvas.restoreState()
            canvas.setStrokeColorRGB(0.15, 0.15, 0.15)
            canvas.setLineWidth(_mm(CUT_LINE_MM))
            canvas.drawPath(_path(canvas, shape["outline"], rotated, place), stroke=1, fill=0)
            canvas.setDash(_mm(FOLD_DASH_MM[0]), _mm(FOLD_DASH_MM[1]))
            for (ax, ay), (bx, by) in shape["folds"]:
                x0, y0 = _to_page(ax, ay, rotated, place)
                x1, y1 = _to_page(bx, by, rotated, place)
                canvas.line(_mm(x0), _mm(y0), _mm(x1), _mm(y1))
            canvas.setDash()
            canvas.setFillColorRGB(0, 0, 0)
            canvas.setFont("Helvetica", 6)
            canvas.drawString(_mm(place["x"]), _mm(place["y"] - LABEL_MM + 0.8), place["label"])
        canvas.showPage()
    canvas.save()


def render_previews(pdf_path: Path, sheets: list, out: Path) -> list:
    import pypdfium2

    files = []
    document = pypdfium2.PdfDocument(str(pdf_path))
    try:
        for index, sheet in enumerate(sheets):
            image = document[index].render(scale=PREVIEW_DPI / 72.0).to_pil()
            name = "sheet-%s.png" % sheet["sheet"]
            image.save(out / name, optimize=False)
            files.append(name)
    finally:
        document.close()
    return files


# -- the whole run -------------------------------------------------------------

def layout(contract: dict) -> tuple:
    section = contract["print"]
    stocks = section["stocks"]
    sheets: list = []
    unplaced: list = []
    for stock in STOCK_ORDER:
        items = []
        for piece in section["pieces"]:
            if piece["stock"] != stock:
                continue
            shape = piece_shape(piece, stocks)
            count = int(piece.get("count", 1))
            for copy in range(1, count + 1):
                label = piece["id"] if count == 1 else "%s %d/%d" % (piece["id"], copy, count)
                items.append({"key": (piece["id"], copy), "label": label, "piece": piece,
                              "shape": shape, "width": shape["width"], "height": shape["height"]})
        pages, missed = pack(items)
        unplaced += missed
        for number, page in enumerate(pages, start=1):
            sheets.append({"sheet": "%s-%d" % (stock, number), "stock": stock, "pieces": page})
    return sheets, unplaced


def report(contract: dict, sheets: list, failures: list) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "title": contract.get("title"),
        "page_mm": list(PAGE_MM),
        "sheets": [
            {"sheet": sheet["sheet"], "stock": sheet["stock"],
             "pieces": [{"id": place["piece"]["id"], "label": place["label"],
                         "x_mm": round(place["x"], 3), "y_mm": round(place["y"], 3),
                         "size_mm": [round(place["shape"]["width"], 3),
                                     round(place["shape"]["height"], 3)],
                         "rotated": place["rotated"], "art": place["piece"]["art"]}
                        for place in sheet["pieces"]]}
            for sheet in sheets
        ],
        "failures": failures,
        "passed": not failures,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--art", required=True, type=Path)
    parser.add_argument("-o", "--out", required=True, type=Path)
    parser.add_argument("--check", action="store_true", help="write only print-sheets.json")
    args = parser.parse_args(argv)
    try:
        contract = load_contract(args.contract)
        sheets, unplaced = layout(contract)
    except (OSError, UsageError, KeyError, TypeError, ValueError) as exc:
        print("print_sheets: %s" % exc, file=sys.stderr)
        return 2
    failures = check_layout(contract, args.art, sheets, unplaced)
    args.out.mkdir(parents=True, exist_ok=True)
    document = report(contract, sheets, failures)
    if not args.check and sheets:
        pdf = args.out / "print-sheets.pdf"
        draw(contract, args.art, sheets, pdf)
        document["pdf"] = {"file": pdf.name, "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()}
        document["previews"] = render_previews(pdf, sheets, args.out)
    (args.out / "print-sheets.json").write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    for failure in failures:
        print("FAIL %s" % failure)
    print("%s: %d sheet(s), %d piece(s) placed, %d failure(s)" % (
        "PASS" if not failures else "FAIL", len(sheets),
        sum(len(sheet["pieces"]) for sheet in sheets), len(failures)))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
