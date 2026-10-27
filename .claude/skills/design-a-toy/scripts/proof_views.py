#!/usr/bin/env python3
"""Render a Contract Proof and lay it beside the AI images (design-a-toy Stage 3a).

    uv run python .claude/skills/design-a-toy/scripts/proof_views.py <command> ...

The Contract Proof (ADR 0093) is a CAD project modelled from CONTRACT.md's
numbers alone, laid out as Make lays out a project: one combined
`<name>.step.py` entry of the whole toy in its Display Pose, and one
`part_<geometry-id>.step.py` per Component whose `gen_step()` returns it in
its print stance and whose `assembly_pose(shape, pose)` places it in the
Display Pose (ADR 0083). This tool renders that model with the CAD skill's
own `render_review` rasteriser and composes images from it. It never draws or
edits a Reference Image, and nothing it writes is compared with a build.

Commands:

  render ENTRY --camera=AZ,EL -o OUT.png [--stance] [--px-per-mm N | --size N]
      One orthographic render. A part entry is shown in its Display Pose
      (assembly_pose(shape, None), instance 1) unless --stance. With
      --px-per-mm every render is at one true scale, so renders of two
      options sit side by side at their real sizes. Prints the scale.

  compare AI.png ENTRY --camera=AZ,EL -o OUT.png [--title TEXT]
      Three panels: the AI image | the Proof at the camera | a 50% overlay.
      The AI image is registered to the render by its object box: one uniform
      scale from the heights, top and left edges aligned. A uniform scale
      error is therefore invisible by design; proportions and positions show.
      The AI background is the median of its corners, so ask for images with
      no cast shadow. Prints, in mm, how far the AI object's right edge sits
      from the Proof's.

  refs CONTRACT.md --proof DIR --images DIR -o OUTDIR
      `compare` for every `references[]` entry at its `camera`: an assembly
      reference against the combined entry, `geometry:<id>` against
      `part_<id>.step.py`. A reference without a camera is listed and skipped.

  split SHEET.png -o OUTDIR [--max 800]
      Cut an AI three-view sheet into its views at the empty columns between
      them (view-1.png, view-2.png, ...), each cropped to its object with a
      margin and scaled down to at most --max pixels a side.

  guide ENTRY --view=AZ,EL[=AI.png] ... -o OUT.png [--title TEXT]
      A Component's Guide Image sheet: one column per view, the AI view on top
      when given, the Proof below it at that camera, every Proof render at one
      scale with a 10 mm bar. At most 2048 pixels a side.

  carry ORIGINAL.png EDITED.png ENTRY --camera=AZ,EL -o OUT.png [--line TEXT]
      The trial of a Proof-edited Component reference (ADR 0093): the
      original AI image | the AI edit of the Proof render | the Proof at the
      camera, each fitted to one tile, with the detail checklist's result as
      one plain line under them.

Write a camera with "=" (--camera=-90,0), or a negative azimuth reads as a
flag.

Exit 1 on a missing file, an entry that does not build, or a contract with
no design-contract block.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.machinery
import importlib.util
import inspect
import io
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[4]
RENDER_REVIEW = REPO / "src/workshop/make/skills/cad/scripts/render_review"
PAD = 0.07
HEADER = 56
GAP = 16
GUIDE_MAX = 2048


def _render_review():
    loader = importlib.machinery.SourceFileLoader("render_review", str(RENDER_REVIEW))
    spec = importlib.util.spec_from_loader("render_review", loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules["render_review"] = module
    loader.exec_module(module)
    module._runtime_paths()
    return module


rr = _render_review()


def _render_with_depth():
    """render_review's own `render`, re-executed with two changes, as the cabinet
    pilot did: a light that follows the camera, so a face seen head-on is never
    dark, and the depth buffer returned, so every depth step can be outlined.
    None when render_review has changed and the patch no longer applies."""
    source = inspect.getsource(rr.render).replace("def render(", "def _proof_render(")
    light = "light = np.array([0.35, -0.45, 0.82], dtype=float)"
    returned = "    return Image.fromarray(pixels)"
    if light not in source or returned not in source:
        return None
    source = source.replace(light, "light = 0.8 * toward_viewer + 0.45 * up - 0.3 * right")
    source = source.replace(returned, "    return Image.fromarray(pixels), depths")
    exec(source, rr.__dict__)
    return rr._proof_render


_RENDER_DEPTH = _render_with_depth()


def _font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _takes_instance(function):
    try:
        return "instance" in inspect.signature(function).parameters
    except (TypeError, ValueError):
        return False


def build(entry: Path, stance: bool = False):
    """The entry's shape: a part entry placed by its assembly_pose unless stance."""
    entry = Path(entry).resolve()
    with contextlib.redirect_stdout(io.StringIO()):
        module = rr._load_entry(entry)
        make = module.gen_step
        shape = make(instance=1) if _takes_instance(make) else make()
        place = getattr(module, "assembly_pose", None)
        if not stance and place is not None:
            shape = place(shape, None, instance=1) if _takes_instance(place) else place(shape, None)
    if shape is None:
        raise ValueError(f"{entry.name} gen_step() returned None")
    return entry, shape


def occurrences(entry: Path, stance: bool = False, tolerance: float = 0.02):
    entry, shape = build(entry, stance)
    return rr.tessellate_occurrences(shape, tolerance, 0.08, cache_entry=entry)


def span_of(occ, camera):
    _toward, right, up = rr.camera_basis(*camera)
    points = np.concatenate([p for p, _f, _c in occ])
    sx, sy = points @ right, points @ up
    return float(max(sx.max() - sx.min(), sy.max() - sy.min()))


def render(occ, camera, size=None, px_per_mm=None):
    """(RGB image, px per mm). Fixed px_per_mm sizes the image to the object."""
    span = span_of(occ, camera)
    if px_per_mm:
        size = max(128, math.ceil(span * px_per_mm / (1 - 2 * PAD)))
    size = size or 800
    if _RENDER_DEPTH is None:
        image = rr.render(occ, camera[0], camera[1], size, PAD).convert("RGB")
    else:
        image, depths = _RENDER_DEPTH(occ, camera[0], camera[1], size, PAD)
        pixels = np.asarray(image.convert("RGB")).copy()
        finite = np.isfinite(depths)
        d = np.where(finite, depths, -1e3)
        edge = np.zeros_like(finite)                 # every depth step over 0.25 mm
        edge[:, 1:] |= np.abs(d[:, 1:] - d[:, :-1]) > 0.25
        edge[1:, :] |= np.abs(d[1:, :] - d[:-1, :]) > 0.25
        pixels[edge] = (pixels[edge] * 0.35).astype(np.uint8)
        image = Image.fromarray(pixels)
    return image, (1 - 2 * PAD) * size / span


def _box(rgb: Image.Image, background, threshold):
    a = np.asarray(rgb.convert("RGB")).astype(int)
    mask = np.abs(a - np.array(background)).max(axis=2) > threshold
    ys, xs = np.nonzero(mask)
    if not len(xs):
        raise ValueError("no object found against the background")
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def corner_background(rgb: Image.Image):
    a = np.asarray(rgb.convert("RGB"))
    k = max(4, min(a.shape[:2]) // 50)
    corners = np.concatenate([a[:k, :k].reshape(-1, 3), a[-k:, -k:].reshape(-1, 3),
                              a[:k, -k:].reshape(-1, 3), a[-k:, :k].reshape(-1, 3)])
    return tuple(int(v) for v in np.median(corners, axis=0))


def register(ai: Image.Image, proof: Image.Image):
    """The AI image scaled and moved onto the proof's object box (heights equal,
    top and left edges aligned), and the two boxes in proof pixels."""
    ai = ai.convert("RGB")
    background = corner_background(ai)
    ax0, ay0, ax1, ay1 = _box(ai, background, 40)
    px0, py0, px1, py1 = _box(proof, rr.BACKGROUND, 12)
    k = (py1 - py0 + 1) / (ay1 - ay0 + 1)
    big = ai.resize((max(1, round(ai.width * k)), max(1, round(ai.height * k))), Image.LANCZOS)
    out = Image.new("RGB", proof.size, background)
    out.paste(big, (round(px0 - ax0 * k), round(py0 - ay0 * k)))
    ai_box = (px0, py0, round(px0 + (ax1 - ax0 + 1) * k) - 1, py1)
    return out, ai_box, (px0, py0, px1, py1)


def scale_bar(image: Image.Image, px_per_mm: float, mm: int = 10):
    draw = ImageDraw.Draw(image)
    x0, y0 = 16, image.height - 24
    length = mm * px_per_mm
    draw.rectangle((x0, y0, x0 + length, y0 + 5), fill=(0, 0, 0))
    for i in range(mm + 1):
        x = x0 + i * px_per_mm
        draw.line((x, y0 - (8 if i % 5 == 0 else 4), x, y0), fill=(0, 0, 0), width=1)
    draw.text((x0, y0 - 26), f"{mm} mm", fill=(0, 0, 0), font=_font(16))


def labelled_row(tiles, titles):
    width = sum(t.width for t in tiles) + GAP * (len(tiles) - 1)
    height = max(t.height for t in tiles) + HEADER
    sheet = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    x = 0
    for tile, title in zip(tiles, titles):
        sheet.paste(tile, (x, HEADER))
        draw.text((x + 8, 14), title, fill=(0, 0, 0), font=_font(24))
        x += tile.width + GAP
    return sheet


def compare(ai_path: Path, entry: Path, camera, out: Path, title=None, size=800, occ=None):
    occ = occ if occ is not None else occurrences(entry)
    proof, px_per_mm = render(occ, camera, size=size)
    ai, ai_box, proof_box = register(Image.open(ai_path), proof)
    overlay = Image.blend(ai, proof, 0.5)
    for tile in (proof, overlay):
        scale_bar(tile, px_per_mm)
    cam = f"[{camera[0]:g}, {camera[1]:g}]"
    sheet = labelled_row([ai, proof, overlay],
                         [title or f"AI: {Path(ai_path).name}", f"Proof {cam}", "50% overlay"])
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    result = {"out": str(out), "camera": list(camera), "px_per_mm": round(px_per_mm, 3),
              "proof_width_mm": round((proof_box[2] - proof_box[0] + 1) / px_per_mm, 2),
              "ai_width_mm": round((ai_box[2] - ai_box[0] + 1) / px_per_mm, 2),
              "height_mm": round((proof_box[3] - proof_box[1] + 1) / px_per_mm, 2)}
    result["right_edge_off_mm"] = round(result["ai_width_mm"] - result["proof_width_mm"], 2)
    return result


def fit_tile(image: Image.Image, tile: int, background=None):
    """The image scaled to fit a tile x tile square, centred on its own
    corner colour (or `background`)."""
    image = image.convert("RGB")
    fitted = image.copy()
    fitted.thumbnail((tile, tile), Image.LANCZOS)
    cell = Image.new("RGB", (tile, tile), background or corner_background(image))
    cell.paste(fitted, ((tile - fitted.width) // 2, (tile - fitted.height) // 2))
    return cell


def with_caption(sheet: Image.Image, text: str, height: int = 48):
    """The sheet with one line of text in a white band under it."""
    out = Image.new("RGB", (sheet.width, sheet.height + height), (255, 255, 255))
    out.paste(sheet, (0, 0))
    ImageDraw.Draw(out).text((8, sheet.height + 12), text, fill=(0, 0, 0), font=_font(22))
    return out


def carry_sheet(original: Image.Image, edited: Image.Image, proof: Image.Image,
                line: str = "", tile: int = 640):
    """original | Proof-edited | Proof, one tile each, with the checklist line."""
    sheet = labelled_row([fit_tile(original, tile), fit_tile(edited, tile), fit_tile(proof, tile)],
                         ["Original AI image", "Edited from the Proof", "Proof"])
    return with_caption(sheet, line) if line else sheet


def carry(original: Path, edited: Path, entry: Path, camera, out: Path, line=""):
    proof, _ = render(occurrences(entry), camera, size=800)
    sheet = carry_sheet(Image.open(original), Image.open(edited), proof, line)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return {"out": str(out), "size": list(sheet.size)}


def contract_block(text: str):
    match = re.search(r"```design-contract\s*\n(.*?)\n```", text, re.S)
    if not match:
        raise ValueError("no design-contract block")
    return json.loads(match.group(1))


def combined_entry(proof: Path) -> Path:
    entries = [p for p in sorted(proof.glob("*.step.py"))
               if not p.name.startswith(("part_", "print_"))]
    if len(entries) != 1:
        raise ValueError(f"{proof} needs exactly one combined *.step.py entry, found {len(entries)}")
    return entries[0]


def refs(contract: Path, proof: Path, images: Path, out: Path):
    block = contract_block(contract.read_text(encoding="utf-8"))
    results, cache = [], {}
    for ref in block.get("references") or []:
        camera = ref.get("camera")
        if not camera:
            results.append({"file": ref["file"], "skipped": "no camera"})
            continue
        shows = ref.get("shows", "")
        entry = combined_entry(proof) if shows == "assembly" else proof / f"part_{shows.split(':', 1)[1]}.step.py"
        if not entry.exists():
            raise FileNotFoundError(f"{ref['file']} shows {shows}: no {entry.name} in {proof}")
        if entry not in cache:
            cache[entry] = occurrences(entry)
        stem = Path(ref["file"]).stem
        result = compare(images / ref["file"], entry, tuple(camera), out / f"{stem}-compare.png",
                         title=f"AI: {ref['file']}", occ=cache[entry])
        results.append({"file": ref["file"], **result})
    return results


def split(sheet_path: Path, out: Path, max_side=800, threshold=40):
    sheet = Image.open(sheet_path).convert("RGB")
    background = corner_background(sheet)
    a = np.asarray(sheet).astype(int)
    mask = np.abs(a - np.array(background)).max(axis=2) > threshold
    filled = mask.sum(axis=0) > max(2, int(0.005 * mask.shape[0]))
    min_gap = max(4, int(0.01 * mask.shape[1]))
    runs, start, gap = [], None, 0
    for x, on in enumerate(filled):
        if on:
            if start is None:
                start = x
            gap, end = 0, x
        elif start is not None:
            gap += 1
            if gap >= min_gap:
                runs.append((start, end))
                start, gap = None, 0
    if start is not None:
        runs.append((start, end))
    runs = [r for r in runs if r[1] - r[0] >= min_gap]
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for n, (x0, x1) in enumerate(runs, 1):
        ys = np.nonzero(mask[:, x0:x1 + 1].any(axis=1))[0]
        y0, y1 = int(ys.min()), int(ys.max())
        margin = int(0.08 * max(x1 - x0, y1 - y0))
        side = max(x1 - x0, y1 - y0) + 2 * margin
        crop = Image.new("RGB", (side, side), background)
        piece = sheet.crop((x0, y0, x1 + 1, y1 + 1))
        crop.paste(piece, ((side - piece.width) // 2, (side - piece.height) // 2))
        if side > max_side:
            crop = crop.resize((max_side, max_side), Image.LANCZOS)
        path = out / f"view-{n}.png"
        crop.save(path)
        paths.append(str(path))
    return paths


def parse_camera(text: str):
    az, el = (float(v) for v in text.split(","))
    if not (-180 <= az <= 180 and -90 <= el <= 90):
        raise argparse.ArgumentTypeError(f"camera out of range: {text}")
    return az, el


def guide(entry: Path, views, out: Path, title=None):
    occ = occurrences(entry)
    tile = min(700, (GUIDE_MAX - GAP * (len(views) - 1)) // len(views))
    span = max(span_of(occ, camera) for camera, _ai in views)
    px_per_mm = tile * (1 - 2 * PAD) / span
    columns = []
    for camera, ai in views:
        proof, _ = render(occ, camera, px_per_mm=px_per_mm)
        canvas = Image.new("RGB", (tile, tile), rr.BACKGROUND)
        canvas.paste(proof, ((tile - proof.width) // 2, (tile - proof.height) // 2))
        scale_bar(canvas, px_per_mm)
        cells = []
        if ai is not None:
            image = Image.open(ai).convert("RGB")
            image.thumbnail((tile, tile), Image.LANCZOS)
            cell = Image.new("RGB", (tile, tile), corner_background(image))
            cell.paste(image, ((tile - image.width) // 2, (tile - image.height) // 2))
            cells.append(cell)
        cells.append(canvas)
        columns.append((camera, cells, ai))
    rows = max(len(c[1]) for c in columns)       # the Proof is always the last row
    top = HEADER if title else 0
    sheet = Image.new("RGB", (tile * len(views) + GAP * (len(views) - 1), top + rows * (tile + HEADER)),
                      (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    if title:
        draw.text((8, 12), title, fill=(0, 0, 0), font=_font(28))
    for i, (camera, cells, ai) in enumerate(columns):
        x = i * (tile + GAP)
        cam = f"[{camera[0]:g}, {camera[1]:g}]"
        labels = ([f"AI {cam}"] if ai is not None else []) + [f"Proof {cam}"]
        first_row = rows - len(cells)
        for j, (cell, label) in enumerate(zip(cells, labels)):
            y = top + (first_row + j) * (tile + HEADER)
            draw.text((x + 8, y + 14), label, fill=(0, 0, 0), font=_font(22))
            sheet.paste(cell, (x, y + HEADER))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return {"out": str(out), "size": list(sheet.size), "px_per_mm": round(px_per_mm, 3)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("render")
    p.add_argument("entry", type=Path)
    p.add_argument("--camera", type=parse_camera, required=True)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--stance", action="store_true")
    p.add_argument("--px-per-mm", type=float)
    p.add_argument("--size", type=int, default=800)
    p = sub.add_parser("compare")
    p.add_argument("ai", type=Path)
    p.add_argument("entry", type=Path)
    p.add_argument("--camera", type=parse_camera, required=True)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--title")
    p = sub.add_parser("refs")
    p.add_argument("contract", type=Path)
    p.add_argument("--proof", type=Path, required=True)
    p.add_argument("--images", type=Path, required=True)
    p.add_argument("-o", "--out", type=Path, required=True)
    p = sub.add_parser("split")
    p.add_argument("sheet", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--max", type=int, default=800)
    p = sub.add_parser("guide")
    p.add_argument("entry", type=Path)
    p.add_argument("--view", action="append", required=True,
                   help="AZ,EL or AZ,EL=AI.png; give the Reference Camera and the two guide cameras")
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--title")
    p = sub.add_parser("carry")
    p.add_argument("original", type=Path)
    p.add_argument("edited", type=Path)
    p.add_argument("entry", type=Path)
    p.add_argument("--camera", type=parse_camera, required=True)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--line", default="", help="the checklist result, one plain line")
    a = parser.parse_args(argv)
    try:
        if a.command == "render":
            occ = occurrences(a.entry, a.stance)
            image, px_per_mm = render(occ, a.camera, size=a.size, px_per_mm=a.px_per_mm)
            a.out.parent.mkdir(parents=True, exist_ok=True)
            image.save(a.out)
            print(json.dumps({"out": str(a.out), "px_per_mm": round(px_per_mm, 3)}))
        elif a.command == "compare":
            print(json.dumps(compare(a.ai, a.entry, a.camera, a.out, a.title)))
        elif a.command == "refs":
            for result in refs(a.contract, a.proof, a.images, a.out):
                print(json.dumps(result))
        elif a.command == "split":
            for path in split(a.sheet, a.out, a.max):
                print(path)
        elif a.command == "guide":
            views = []
            for text in a.view:
                camera, _, ai = text.partition("=")
                views.append((parse_camera(camera), Path(ai) if ai else None))
            print(json.dumps(guide(a.entry, views, a.out, a.title)))
        elif a.command == "carry":
            print(json.dumps(carry(a.original, a.edited, a.entry, a.camera, a.out, a.line)))
    except (OSError, ValueError, AttributeError, ImportError) as exc:
        print(f"proof_views: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
