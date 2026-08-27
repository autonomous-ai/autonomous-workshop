#!/usr/bin/env python3
"""Silhouette-likeness gate: how close does the model look to the reference?

Every other check in this toolchain asks whether the model is *sound* --
`validate` (closed solids), `interfere` (no clash), `check_fit` (prints),
`check_motion` (assembles). None of them asks the only question an
image-derived model exists to answer: **does it look like the photograph?**
That gap is why a model can pass seven gates and still be 60 % of the way
there, and why "looks about right" was the acceptance test.

This makes it a number. For each (render, reference) pair it extracts both
silhouettes with the same instrument `measure_image.py` uses, normalises them
to a common height, aligns them, and reports:

    iou            intersection over union of the two silhouettes, 0..1
    aspect_delta   render width / reference width after height normalisation
    bands          twelve horizontal slices, each with the render's width as a
                   fraction of the reference's -- this is what makes a failure
                   actionable, because it says WHERE the shape is wrong

    python check_likeness.py --pair render.png reference.png
    python check_likeness.py \
        --pair snap/side.png  ref/03-side.png \
        --pair snap/front.png ref/02-front.png \
        --min 0.90 --report measure/likeness.md

Exit 0 when every pair meets `--min` (default 0.90), 1 when any falls short,
2 on bad usage.

    python check_likeness.py --self-check

`--report` also keeps an append-only history beside itself, one row per view
per run, so the report answers the question a single score cannot: **did the
last edit make the model more like the photograph, or less?** Without it a
failing score reads identically on every round and the edit loop goes blind --
round after round of rendering that leaves one number on disk is what that
looks like. Lowering the floor below 0.90 now needs `--accept-mismatch "<reason>"`,
and the reason is recorded in every history row it covers, because a floor
quietly set to 0.00 turns this gate into a formatter.

That history is also a pass mark. A run that scores below the best round this
view has ever recorded fails as `regressed-from-best`, however far above the
floor it lands. Overriding that costs `--accept-regression "<reason>"`, which
needs the `--report` whose history holds the best it would override -- without
one there is no regression to find and nowhere to record the reason.

A failing loop also has to end somewhere. After `STALL_STREAK` consecutive
rounds that did not move the number -- `stalled` or `regressing`, with any
`improving` round resetting the count -- the verdict becomes `stalled out`.
It still exits non-zero, because re-rendering an unchanged shape does not make
it resemble anything; what changes is the instruction. The edits have stopped
reaching what this gate measures, and the only decision left is whether the
measured mismatch is acceptable, which belongs to the user rather than to
another round. The gate prints the form of the command that records it, with
the project's own paths left for the caller to fill in.

For the same reason the floor cannot be lowered until **the view being scored**
has two earlier rounds of its own against that same reference. Rounds spent on
one viewpoint say nothing about a viewpoint being scored for the first time,
and a mismatch accepted on run 1 was never measured against an attempt to fix
it, which is indistinguishable from never having run this gate at all.

Two things it deliberately does NOT do.

It does not align by anything but the bounding box, so a model that is the
right shape in the wrong *place* still scores well -- placement is what
`inspect align` and the assembly checks are for.

It also refuses a reference whose extracted subject touches the image boundary.
Height normalisation cannot distinguish a cropped object from a short one, so
the resulting IoU would measure the crop as if it were geometry. Use a complete
view for whole-object likeness, or `--allow-clipped-reference` only for an
intentional partial-feature comparison.

And it does not know about colour. On a multi-material reference, colour is a
large part of the likeness a human sees, and this gate is blind to it: a
correct silhouette in one flat colour scores the same as the real thing. Read
the score as a floor on the disagreement, never as a ceiling on the quality.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_image import _flood_components, object_mask  # noqa: E402

NORM_HEIGHT = 480
BANDS = 12
DEFAULT_MIN = 0.90
HISTORY_SUFFIX = "-history.jsonl"
HISTORY_SHOWN = 20
STALL_DELTA = 0.005
MIN_ROUNDS_BEFORE_MISMATCH = 2
STALL_STREAK = 3


def clipped_edges(mask: np.ndarray) -> list[str]:
    """Image edges touched by the extracted subject silhouette."""
    contacts = []
    for name, values in (
        ("top", mask[0, :]),
        ("right", mask[:, -1]),
        ("bottom", mask[-1, :]),
        ("left", mask[:, 0]),
    ):
        if values.any():
            contacts.append(name)
    return contacts


def require_complete_reference(mask: np.ndarray, path: Path) -> None:
    """Reject whole-object scoring when the source silhouette is clipped."""
    contacts = clipped_edges(mask)
    if contacts:
        raise ValueError(
            f"reference silhouette touches the image boundary "
            f"({', '.join(contacts)}): {path}; use a complete view, or pass "
            "--allow-clipped-reference only for an intentional partial-feature comparison"
        )


def silhouette(path: Path, threshold: float, largest: bool = True) -> np.ndarray:
    """The subject's silhouette, as the largest connected blob in the frame.

    Keeping only the largest component is not cosmetic. A snapshot rendered
    with `viewLabels` carries a small "ISO" chip in the corner; it is object to
    any threshold, and it stretches the bounding box to the frame's edge. The
    first run of this gate scored the front view at IoU 0.10 with an aspect
    ratio of 1.99 for exactly that reason, and the model was not at fault.
    Render likeness views with `viewLabels: false`, and let this catch the rest.
    """
    image = Image.open(path).convert("RGB")
    rgb = np.asarray(image, dtype=float)
    gray = np.asarray(image.convert("L"), dtype=float)
    mask, _bg, _notes = object_mask(rgb, gray, threshold, invert=False)
    if not mask.any():
        raise ValueError(f"no object found in {path}")
    if largest:
        labels, count = _flood_components(mask)
        if count > 1:
            sizes = np.bincount(labels.ravel())
            sizes[0] = 0
            mask = labels == int(sizes.argmax())
    return mask


def normalise(mask: np.ndarray) -> np.ndarray:
    """Crop to the silhouette's box and scale so its HEIGHT is NORM_HEIGHT.

    Height only, never width: normalising both would divide the aspect ratio
    out of the comparison, and the aspect ratio is the single proportion most
    worth catching.
    """
    ys, xs = np.nonzero(mask)
    box = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = box.shape
    scale = NORM_HEIGHT / h
    out_w = max(1, int(round(w * scale)))
    img = Image.fromarray((box.astype(np.uint8) * 255)).resize(
        (out_w, NORM_HEIGHT), Image.NEAREST)
    return np.asarray(img) > 127


def compare(render: np.ndarray, reference: np.ndarray) -> dict:
    """IoU and per-band widths, with the two silhouettes centred on each other."""
    width = max(render.shape[1], reference.shape[1])
    canvas = []
    for m in (render, reference):
        pad = width - m.shape[1]
        left = pad // 2
        canvas.append(np.pad(m, ((0, 0), (left, pad - left)), constant_values=False))
    a, b = canvas
    inter = int((a & b).sum())
    union = int((a | b).sum())
    iou = inter / union if union else 0.0

    bands = []
    step = NORM_HEIGHT / BANDS
    for i in range(BANDS):
        lo, hi = int(i * step), int((i + 1) * step)
        wa = int(a[lo:hi].any(axis=0).sum())
        wb = int(b[lo:hi].any(axis=0).sum())
        bands.append({
            "band": i,
            "from_top": round(i / BANDS, 3),
            "render_px": wa,
            "reference_px": wb,
            "ratio": round(wa / wb, 3) if wb else None,
        })
    return {
        "iou": round(iou, 4),
        "aspect_delta": round(render.shape[1] / reference.shape[1], 4),
        "bands": bands,
    }


def worst_bands(bands: list[dict], n: int = 3) -> list[dict]:
    scored = [b for b in bands if b["ratio"] is not None]
    scored.sort(key=lambda b: abs(b["ratio"] - 1.0), reverse=True)
    return scored[:n]


def history_path(report: Path) -> Path:
    """The append-only sidecar that gives a report its previous rounds.

    It is a separate file because the report itself is rewritten in full on
    every run: parsing the previous round back out of rendered markdown would
    make the history only as durable as the table format.
    """
    return report.with_name(report.stem + HISTORY_SUFFIX)


def read_history(path: Path) -> list[dict]:
    """Previous rows, skipping any a hand edit has broken.

    One unreadable line must not cost the rest of the history; a lost trend is
    exactly what this file exists to prevent.
    """
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def append_history(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def canonical_reference(reference: str) -> str | None:
    """The reference as an absolute path, or None if it cannot be resolved."""
    try:
        return str(Path(reference).resolve())
    except OSError:
        return None


def same_reference(row: dict, reference: str) -> bool:
    """Whether a stored row scored the same file this run is scoring.

    Spelling, not identity, is what makes this more than `==`: the same image
    reaches the history as `ref/hero.png` from inside the project and
    `output/lamp/ref/hero.png` from the repository root, and treating those as
    two views would silently restart the trend, the best and the stall count --
    while the integrated runner, which resolves paths to answer the same
    question, still counts them as one. A producer and a consumer that scope a
    history differently disagree about which rounds a view has had.

    Resolving the stored spelling at read time cannot fix that on its own,
    because a relative path resolves against *this* run's working directory
    rather than the one that wrote it. So the row carries its own resolved
    path, and that is what identifies it first. Once a row has one it decides:
    a canonical miss is a different view, and does not fall through to the
    spelling. Moving or renaming the project therefore starts a fresh identity
    rather than silently carrying a stall count across the move, and the
    integrated runner reads the field the same way -- a producer and a consumer
    that disagree about which rounds a view has had is the failure this field
    exists to prevent.

    Two older shapes are handled as well as they can be: a row with no
    reference at all predates the field and matches on the label, and a row
    with a relative spelling and no resolved path is genuinely ambiguous -- it
    is matched on the spelling, or on a best-effort resolution that is only
    right when the working directory has not changed.
    """
    stored = row.get("reference_resolved")
    if isinstance(stored, str) and stored:
        return stored == canonical_reference(reference)
    raw = row.get("reference")
    if raw is None:      # rows predating the field: label-only compatibility
        return True
    if not isinstance(raw, str) or not raw:
        return False
    if raw == reference:
        return True
    resolved = canonical_reference(raw)
    return resolved is not None and resolved == canonical_reference(reference)


def rows_for(history: list[dict], label: str,
             reference: str | None) -> list[dict]:
    """Previous rows for one view, scoped to the reference it was scored on.

    A label is a name; the reference is the thing being copied. Swap the
    reference and keep the label — a flattened silhouette in place of the
    photograph, a different viewpoint reusing `hero` — and every earlier score
    belongs to a different comparison, so the trend, the best and the round
    count all have to start again.
    """
    ref = None if reference is None else str(reference)
    return [row for row in history
            if row.get("label") == label
            and (ref is None or same_reference(row, ref))]


def best_round(history: list[dict], label: str,
               reference: str | None) -> dict | None:
    """The highest IoU this view has recorded, and the run that got it.

    The floor is not the only number a run has to beat. Comparing against the
    floor alone cannot say that an edit round made the model worse, because
    every round between the floor and 1.0 reads `ok`; the best round on disk
    is the number that says which shape to keep.
    """
    scored = [row for row in rows_for(history, label, reference)
              if isinstance(row.get("iou"), (int, float))]
    if not scored:
        return None
    top = max(scored, key=lambda row: row["iou"])
    return {"iou": float(top["iou"]), "run": top.get("run")}


def trend(delta: float | None) -> str:
    """Name the direction, so a failing score still says whether to keep going.

    Every round below the floor exits 1 and prints the same verdict, which is
    what makes an agent lower the floor to get a different word back. The
    direction is the number that actually decides whether to revert.
    """
    if delta is None:
        return "first"
    if delta > STALL_DELTA:
        return "improving"
    if delta < -STALL_DELTA:
        return "regressing"
    return "stalled"


def reference_key(row: dict) -> object:
    """What a row is grouped by for display: its canonical path when it has one.

    The table groups rows itself rather than re-matching them through
    `same_reference`, because a raw relative spelling would be resolved against
    whichever directory happens to be current when the report is written --
    which is exactly the ambiguity `reference_resolved` was added to remove.
    """
    resolved = row.get("reference_resolved")
    if isinstance(resolved, str) and resolved:
        return resolved
    return row.get("reference")


def history_table(rows: list[dict], path: Path) -> str:
    shown = rows[-HISTORY_SHOWN:]
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        groups.setdefault((row.get("label") or "", reference_key(row)), []).append(row)
    best = {}
    for key, group in groups.items():
        scored = [r for r in group if isinstance(r.get("iou"), (int, float))]
        if scored:
            top = max(scored, key=lambda r: r["iou"])
            best[key] = {"iou": float(top["iou"]), "run": top.get("run")}
    marked: set[tuple] = set()
    out = ["## History\n",
           "One row per view per run. Read the delta before editing again: a "
           "round that moved the number down is a round to revert, and a run "
           "of `stalled` means the edits are not reaching the shape this gate "
           "measures. A floor marked `!` was lowered under "
           "`--accept-mismatch`; an IoU marked `*` is the best that view has "
           "reached, and the number this run had to beat.\n",
           "| run | time | view | IoU | delta | trend | aspect | floor |",
           "|---|---|---|---|---|---|---|---|"]
    for row in shown:
        iou = row.get("iou")
        aspect = row.get("aspect")
        delta = row.get("delta")
        label = row.get("label") or ""
        floor = f"{row.get('min', DEFAULT_MIN):.2f}"
        if row.get("accepted_mismatch"):
            floor += " !"
        cell = "error" if iou is None else format(iou, ".3f")
        key = (label, reference_key(row))
        top = best.get(key)
        if top and iou is not None and key not in marked and iou >= top["iou"]:
            cell += " *"
            marked.add(key)
        out.append(
            f"| {row.get('run') or '?'} | {row.get('time') or ''} "
            f"| {label} "
            f"| {cell} "
            f"| {'—' if delta is None else format(delta, '+.3f')} "
            f"| {row.get('trend') or '—'} "
            f"| {'—' if aspect is None else format(aspect, '.3f')} "
            f"| {floor} |")
    if len(rows) > HISTORY_SHOWN:
        out.append(f"\nShowing the last {HISTORY_SHOWN} of {len(rows)} rows; "
                   f"the rest are in `{path.name}`.")
    if best:
        # name the reference only where one label has been scored against more
        # than one, which is the case where "best" would otherwise be ambiguous
        refs: dict[str, set] = {}
        for lab, ref in best:
            refs.setdefault(lab, set()).add(ref)
        tops = ", ".join(
            f"{lab}{f' vs {Path(ref).name}' if ref and len(refs[lab]) > 1 else ''} "
            f"{b['iou']:.3f} (run {b['run'] or '?'})"
            for (lab, ref), b in sorted(best.items(),
                                        key=lambda kv: (kv[0][0], str(kv[0][1]))))
        out.append(f"\nBest so far: {tops}. A run below its own best fails as "
                   "`regressed-from-best`, floor or no floor.")
    return "\n".join(out)


# --------------------------------------------------------------------------
# self-check
# --------------------------------------------------------------------------
#
# This gate is what a delivery claim rests on, and it borrows its silhouette
# from `measure_image.object_mask`. A change there moves every IoU this file
# has ever printed, silently and in the right-looking direction. The fixtures
# below are the only thing that notices.


def _box(path: Path, w: int, h: int, top: int | None = None,
         chip: bool = False, waist: int = 0) -> Path:
    """A synthetic silhouette: dark rectangle, light ground.

    `waist` narrows the bottom half by that many pixels per side, which is how
    the band fixture asks the gate WHERE the shape is wrong rather than only
    whether it is.
    """
    canvas = np.full((400, 400, 3), 250, dtype=np.uint8)
    x0 = 200 - w // 2
    y0 = 200 - h // 2 if top is None else top
    canvas[y0:y0 + h, x0:x0 + w] = 30
    if waist:
        mid = y0 + h // 2
        canvas[mid:y0 + h, x0:x0 + waist] = 250
        canvas[mid:y0 + h, x0 + w - waist:x0 + w] = 250
    if chip:                       # the burnt-in "ISO" view label, in a corner
        canvas[8:28, 360:392] = 30
    Image.fromarray(canvas).save(path)
    return path


def self_check() -> int:
    import tempfile

    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        ref = _box(d / "ref.png", 160, 240)
        same = _box(d / "same.png", 160, 240)
        narrow = _box(d / "narrow.png", 100, 240)
        waisted = _box(d / "waist.png", 160, 240, waist=30)
        chipped = _box(d / "chip.png", 160, 240, chip=True)
        clipped = _box(d / "clip.png", 160, 300, top=0)

        def score(render, reference):
            return compare(normalise(silhouette(render, 28.0)),
                           normalise(silhouette(reference, 28.0)))

        r = score(same, ref)
        hit = r["iou"] == 1.0
        print(f"{'ok  ' if hit else 'FAIL'} an identical silhouette scores "
              f"exactly 1  - IoU {r['iou']:.4f}")
        ok &= hit

        r = score(narrow, ref)
        hit = 0.60 < r["iou"] < 0.66
        print(f"{'ok  ' if hit else 'FAIL'} a render 37 % too narrow scores "
              f"well below the floor  - IoU {r['iou']:.4f}")
        ok &= hit

        # the claim the docstring makes: the bands say WHERE, not just THAT.
        r = score(waisted, ref)
        top = [b["ratio"] for b in r["bands"][:5]]
        bottom = [b["ratio"] for b in r["bands"][7:]]
        hit = min(top) > 0.98 and max(bottom) < 0.70
        print(f"{'ok  ' if hit else 'FAIL'} the bands localise a defect to the "
              f"half it is in  - top {min(top):.2f}, bottom {max(bottom):.2f}")
        ok &= hit

        # a corner chip is object to any threshold and would stretch the box
        # to the frame edge; keeping the largest blob is what absorbs it.
        r = score(chipped, ref)
        hit = r["iou"] == 1.0
        print(f"{'ok  ' if hit else 'FAIL'} a burnt-in view label does not "
              f"become part of the silhouette  - IoU {r['iou']:.4f}")
        ok &= hit
        loose = compare(normalise(silhouette(chipped, 28.0, largest=False)),
                        normalise(silhouette(ref, 28.0)))
        hit = loose["iou"] < r["iou"]
        print(f"{'ok  ' if hit else 'FAIL'} and --all-blobs shows what that "
              f"rule is worth  - IoU {loose['iou']:.4f} without it")
        ok &= hit

        try:
            require_complete_reference(silhouette(clipped, 28.0), clipped)
            hit = False
        except ValueError:
            hit = True
        print(f"{'ok  ' if hit else 'FAIL'} a reference that touches the frame "
              f"is refused rather than scored")
        ok &= hit

        # lowering the floor is the cheapest way to change this gate's output,
        # so it has to cost a recorded reason.
        import contextlib
        import io
        code = None
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                main(["--pair", str(narrow), str(ref), "--min", "0.50"])
            except SystemExit as exc:
                code = exc.code
        hit = code == 2
        print(f"{'ok  ' if hit else 'FAIL'} the floor cannot be lowered "
              f"without a reason  - exit {code}")
        ok &= hit

        report = d / "likeness.md"
        with contextlib.redirect_stdout(io.StringIO()):
            main(["--pair", str(narrow), str(ref), "--label", "v",
                  "--report", str(report)])
            main(["--pair", str(waisted), str(ref), "--label", "v",
                  "--report", str(report)])
        rows = read_history(history_path(report))
        hit = (len(rows) == 2 and rows[1]["delta"] is not None
               and rows[1]["delta"] > 0 and rows[1]["trend"] == "improving")
        print(f"{'ok  ' if hit else 'FAIL'} the second run knows the edit "
              f"helped  - delta {rows[-1]['delta'] if rows else None}, "
              f"trend {rows[-1]['trend'] if rows else None}")
        ok &= hit

        # the history is a pass mark, not a diary. `near` clears the 0.90
        # floor on its own, which is exactly the case the floor cannot catch:
        # the only thing that says it is the wrong shape to ship is the
        # better round already on disk.
        near = _box(d / "near.png", 150, 240)
        best_report = d / "best.md"
        with contextlib.redirect_stdout(io.StringIO()):
            first = main(["--pair", str(same), str(ref), "--label", "v",
                          "--report", str(best_report)])
            worse = main(["--pair", str(near), str(ref), "--label", "v",
                          "--report", str(best_report)])
            waived = main(["--pair", str(near), str(ref), "--label", "v",
                           "--report", str(best_report),
                           "--accept-regression", "fixture"])
        hit = (first, worse, waived) == (0, 1, 0)
        print(f"{'ok  ' if hit else 'FAIL'} a round below its own best fails "
              f"while clearing the floor  - exits {first}, {worse}, {waived}")
        ok &= hit

        # and lowering the floor is refused until rounds exist to lower it
        # against: on run 1 there is no attempt for the mismatch to be
        # measured against.
        fresh = d / "fresh.md"
        code = None
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                main(["--pair", str(narrow), str(ref), "--label", "v",
                      "--min", "0.50", "--accept-mismatch", "fixture",
                      "--report", str(fresh)])
            except SystemExit as exc:
                code = exc.code
        hit = code == 2
        print(f"{'ok  ' if hit else 'FAIL'} the floor cannot be lowered before "
              f"{MIN_ROUNDS_BEFORE_MISMATCH} rounds exist  - exit {code}")
        ok &= hit

        with contextlib.redirect_stdout(io.StringIO()):
            main(["--pair", str(narrow), str(ref), "--label", "v",
                  "--report", str(fresh)])
            main(["--pair", str(narrow), str(ref), "--label", "v",
                  "--report", str(fresh)])
            after = main(["--pair", str(narrow), str(ref), "--label", "v",
                          "--min", "0.50", "--accept-mismatch", "fixture",
                          "--report", str(fresh)])
        hit = after == 0
        print(f"{'ok  ' if hit else 'FAIL'} and is allowed once they do  - "
              f"exit {after}")
        ok &= hit

        # those rounds are counted per view. Two rounds spent on one label say
        # nothing about a label being scored for the first time, and a history
        # counted in bulk would let the second ride in on the first's rounds.
        mixed = d / "mixed.md"
        with contextlib.redirect_stdout(io.StringIO()):
            main(["--pair", str(narrow), str(ref), "--label", "a",
                  "--report", str(mixed)])
            main(["--pair", str(narrow), str(ref), "--label", "a",
                  "--report", str(mixed)])
        code = None
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                main(["--pair", str(narrow), str(ref), "--label", "b",
                      "--min", "0.50", "--accept-mismatch", "fixture",
                      "--report", str(mixed)])
            except SystemExit as exc:
                code = exc.code
        hit = code == 2
        print(f"{'ok  ' if hit else 'FAIL'} one view's rounds do not lower "
              f"another view's floor  - exit {code}")
        ok &= hit

        # and the best is scoped to the reference. Swapping the image a label
        # is scored against starts that view's history again: otherwise the
        # first score under a new reference reads as a regression from a
        # comparison it never made.
        ref2 = _box(d / "ref2.png", 160, 240)
        swapped = d / "swapped.md"
        with contextlib.redirect_stdout(io.StringIO()):
            main(["--pair", str(same), str(ref), "--label", "v",
                  "--report", str(swapped)])
            after_swap = main(["--pair", str(near), str(ref2), "--label", "v",
                               "--report", str(swapped)])
        rows = read_history(history_path(swapped))
        hit = (after_swap == 0 and rows[-1]["trend"] == "first"
               and rows[-1]["from_best"] is None)
        print(f"{'ok  ' if hit else 'FAIL'} a new reference is not a "
              f"regression from the old one  - exit {after_swap}, "
              f"trend {rows[-1]['trend']}")
        ok &= hit

        # a waiver for a comparison that cannot happen is refused rather than
        # accepted silently: without a history there is no best to override.
        code = None
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                main(["--pair", str(same), str(ref), "--accept-regression", "fixture"])
            except SystemExit as exc:
                code = exc.code
        hit = code == 2
        print(f"{'ok  ' if hit else 'FAIL'} a regression waiver with no history "
              f"to waive is refused  - exit {code}")
        ok &= hit

        # a failing loop stops after three rounds that did not move the
        # number, and an improving round in between resets the count -- the
        # gate must not tell a loop that is still working to give up.
        stall = d / "stall.md"
        codes, texts = [], []
        for render in (narrow, waisted, narrow, narrow, narrow):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                codes.append(main(["--pair", str(render), str(ref), "--label", "v",
                                   "--report", str(stall)]))
            texts.append(out.getvalue())
        # runs 1..3 are first/improving/regressing, so no streak of three yet;
        # runs 4 and 5 are the second and third stalled rounds after run 3.
        hit = (all(code == 1 for code in codes)
               and not any("STALLED OUT" in t for t in texts[:4])
               and "STALLED OUT" in texts[4]
               # it must hand over the delivery decision, never teach the loop
               # to lower its own floor
               and "likeness-accept-mismatch" in texts[4]
               and "--min" not in texts[4])
        print(f"{'ok  ' if hit else 'FAIL'} three rounds that move nothing stop "
              f"the loop and hand over the decision  - "
              f"{[('stalled' if 'STALLED OUT' in t else '-') for t in texts]}")
        ok &= hit

        # the history row states its own verdict, because the integrated
        # runner decides from it whether a failure is the one the user
        # accepted. If these ever have to be recomputed by the reader, the
        # two layers can disagree about the same run.
        # each of the three verdicts on its own: passing, a regression that
        # clears the floor, and a floor failure that is nobody's regression
        # (the run repeats its own best, so only the floor is missed).
        reasons = d / "reasons.md"
        floor_only = d / "floor-only.md"
        with contextlib.redirect_stdout(io.StringIO()):
            main(["--pair", str(same), str(ref), "--label", "v",
                  "--report", str(reasons)])          # passes
            main(["--pair", str(near), str(ref), "--label", "v",
                  "--report", str(reasons)])          # over the floor, regressed
            for _ in range(2):
                main(["--pair", str(narrow), str(ref), "--label", "v",
                      "--report", str(floor_only)])   # under the floor, no drop
        got = ([(row["ok"], row["failed_because"])
                for row in read_history(history_path(reasons))]
               + [(row["ok"], row["failed_because"])
                  for row in read_history(history_path(floor_only))])
        hit = got == [(True, None), (False, "regression"),
                      (False, "floor"), (False, "floor")]
        print(f"{'ok  ' if hit else 'FAIL'} every history row says why it "
              f"failed, so no reader recomputes it  - {got}")
        ok &= hit

        # the same file scored from two working directories is one view. This
        # is the case the stored resolved path exists for: run 1 names the
        # reference relatively from inside the directory, run 2 absolutely from
        # outside it, and resolving run 1's spelling at read time would resolve
        # it against the wrong cwd. If these ever split, the trend, the best
        # and the stall count all restart while the integrated runner -- which
        # resolves paths for the same question -- still sees one view.
        import os

        spelled = d / "spelled.md"
        origin = Path.cwd()
        try:
            os.chdir(d)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--pair", "same.png", "ref.png", "--label", "v",
                      "--report", str(spelled)])
        finally:
            os.chdir(origin)
        with contextlib.redirect_stdout(io.StringIO()):
            main(["--pair", str(near), str(ref), "--label", "v",
                  "--report", str(spelled)])
        rows = read_history(history_path(spelled))
        row = rows[-1]
        # and the report has to group them together too: the table keys on the
        # canonical path, not on the spelling, or the two rounds render as two
        # views and the best marker lands on both.
        table = spelled.read_text()
        marked = [line for line in table.splitlines() if " * |" in line]
        hit = (rows[0]["reference"] == "ref.png"
               and row["trend"] == "regressing"
               and row["failed_because"] == "regression"
               # the marker sits on run 1 and on nothing else, and the summary
               # names one group rather than the same label twice
               and len(marked) == 1 and "1.000 * |" in marked[0]
               and table.count("1.000 *") == 1
               and "Best so far: v 1.000 (run 1)" in table
               and "Best so far: v vs" not in table)
        print(f"{'ok  ' if hit else 'FAIL'} one reference scored from two "
              f"working directories stays one view  - stored "
              f"{rows[0]['reference']!r}, trend {row['trend']}, "
              f"{len(marked)} best marker(s) on run "
              f"{marked[0].split('|')[1].strip() if marked else '?'}")
        ok &= hit

        # a view can be below the floor and below its own best at the same
        # time, and which one the row reports decides whether a mismatch
        # acceptance downstream also swallows an unwaived regression.
        both = d / "both.md"
        waived_report = d / "waived.md"
        with contextlib.redirect_stdout(io.StringIO()):
            for report in (both, waived_report):
                main(["--pair", str(waisted), str(ref), "--label", "v",
                      "--report", str(report)])
            main(["--pair", str(narrow), str(ref), "--label", "v",
                  "--report", str(both)])
            main(["--pair", str(narrow), str(ref), "--label", "v",
                  "--report", str(waived_report),
                  "--accept-regression", "fixture"])
        pair = (read_history(history_path(both))[-1]["failed_because"],
                read_history(history_path(waived_report))[-1]["failed_because"])
        hit = pair == ("regression", "floor")
        print(f"{'ok  ' if hit else 'FAIL'} below the floor AND below best "
              f"reports the regression until it is waived  - {pair}")
        ok &= hit

        # and the verdict names the mark that was missed. `near` clears the
        # floor, so calling this run "below target" would blame the wrong one.
        verdict_report = d / "verdict.md"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main(["--pair", str(same), str(ref), "--label", "v",
                  "--report", str(verdict_report)])
            main(["--pair", str(near), str(ref), "--label", "v",
                  "--report", str(verdict_report)])
        text = out.getvalue()
        hit = "REGRESSED FROM BEST" in text and "BELOW TARGET" not in text
        print(f"{'ok  ' if hit else 'FAIL'} a run over the floor is reported as "
              f"regressed, not as below target")
        ok &= hit

    print("\nall fixtures pass" if ok else "\nself-check FAILED")
    return 0 if ok else 1


def stall_lines(stalled_out: list[dict], results: list[dict],
                history: list[dict]) -> list[str]:
    """What a loop that has stopped moving should be told to do instead.

    Rendering the same shape again is not a stopping condition. The lines name
    what the rounds actually bought, and hand over the one command that records
    a decision only the user can make.
    """
    lines = []
    for r in stalled_out:
        earlier = rows_for(history, r["label"], r.get("reference"))
        deltas = [row.get("delta") for row in earlier] + [r["delta"]]
        span = [d for d in deltas[-r["stall_streak"]:] if isinstance(d, (int, float))]
        best = "—" if r.get("best") is None else f"{r['best']:.3f}"
        lines.append(
            f"{r['label']}: {len(earlier) + 1} rounds, best {best} at run "
            f"{r.get('best_run') or '?'}, last {r['stall_streak']} rounds moved "
            f"it {sum(span):+.3f} in total")
    worst = min(r["iou"] for r in results if "iou" in r)
    lines.append(
        "the edits are no longer reaching what this gate measures; another "
        f"round is not a stopping condition. Below the {DEFAULT_MIN:.2f} "
        "delivery floor only an explicit user acceptance ships this, and it is "
        "recorded at final verification -- not by lowering this floor:")
    lines.append(
        "    verify_project <project> --image-derived ... "
        f'--likeness-accept-mismatch "<why {worst:.3f} is acceptable here>"')
    return lines


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--self-check" in argv:
        return self_check()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pair", nargs=2, action="append", metavar=("RENDER", "REFERENCE"),
                    required=True, help="one render and the reference it copies")
    ap.add_argument("--label", action="append", default=None,
                    help="name for each pair, in order")
    ap.add_argument("--min", type=float, default=DEFAULT_MIN,
                    help=f"minimum IoU per view (default {DEFAULT_MIN})")
    ap.add_argument("--threshold", type=float, default=28.0)
    ap.add_argument("--all-blobs", action="store_true",
                    help="compare the whole mask instead of its largest blob")
    ap.add_argument("--allow-clipped-reference", action="store_true",
                    help="allow a reference silhouette that touches the image boundary; "
                         "only valid for an intentional partial-feature comparison")
    ap.add_argument("--accept-mismatch", metavar="REASON",
                    help="record why a measured mismatch is accepted; required "
                         f"to set --min below the {DEFAULT_MIN:.2f} delivery floor")
    ap.add_argument("--accept-regression", metavar="REASON",
                    help="record why a score below this view's best recorded "
                         "round is accepted; without it that run fails")
    ap.add_argument("--report", type=Path, help="write a markdown report here")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-check", action="store_true",
                    help="run the built-in fixtures and exit")
    args = ap.parse_args(argv)

    if args.min < DEFAULT_MIN and not args.accept_mismatch:
        ap.error(
            f"--min {args.min:.2f} is below the {DEFAULT_MIN:.2f} delivery floor. "
            "Pass --accept-mismatch \"<why the measured mismatch is accepted>\" so "
            "the reason is recorded in the report and every history row it covers. "
            "A floor set to 0.00 does not make the model closer to the reference; "
            "it only stops this gate from saying so.")

    # History is read before scoring, because two of the rules below are about
    # what earlier rounds already recorded rather than about this render.
    hist_file = history_path(args.report) if args.report else None
    history = read_history(hist_file) if hist_file else []

    if args.accept_regression and hist_file is None:
        ap.error(
            "--accept-regression without --report waives nothing. The best round "
            "it would override lives in the report's history, so with no history "
            "there is no regression to find and nowhere to record the reason -- "
            "the flag would read like an accepted decision and be a no-op.")

    given = args.label or []
    pairs = [(given[i] if i < len(given) else Path(render).stem, render, reference)
             for i, (render, reference) in enumerate(args.pair)]

    if args.min < DEFAULT_MIN:
        if hist_file is None:
            ap.error(
                "--accept-mismatch has nowhere to be recorded without --report. "
                "The reason belongs in the report and in every history row it "
                "covers; a floor lowered in a terminal that scrolls away is a "
                "floor nobody can audit afterwards.")
        # per view, and per reference: rounds spent on one viewpoint say
        # nothing about a viewpoint being scored for the first time, and a
        # history counted in bulk would let a second label ride in on them.
        for label, _render, reference in pairs:
            rounds = len({row.get("run")
                          for row in rows_for(history, label, reference)
                          if row.get("run")})
            if rounds < MIN_ROUNDS_BEFORE_MISMATCH:
                ap.error(
                    f"--accept-mismatch with {rounds} recorded round(s) for "
                    f"{label} against {Path(reference).name}: this view needs "
                    f"{MIN_ROUNDS_BEFORE_MISMATCH} before its floor can be "
                    "lowered. A mismatch accepted before any round tried to "
                    f"fix it was never measured -- score at the "
                    f"{DEFAULT_MIN:.2f} floor, edit the shape, and lower it "
                    "only once the trend says the edits have stopped reaching "
                    "what this gate sees.")

    results = []
    for label, render_path, ref_path in pairs:
        try:
            keep_largest = not args.all_blobs
            render_mask = silhouette(Path(render_path), args.threshold, keep_largest)
            reference_mask = silhouette(Path(ref_path), args.threshold, keep_largest)
            if not args.allow_clipped_reference:
                require_complete_reference(reference_mask, Path(ref_path))
            r = normalise(render_mask)
            f = normalise(reference_mask)
        except (OSError, ValueError) as exc:
            results.append({"label": label, "error": str(exc), "ok": False})
            continue
        rec = compare(r, f)
        rec.update({"label": label, "render": render_path, "reference": ref_path,
                    "ok": rec["iou"] >= args.min})
        results.append(rec)

    scored = [r for r in results if "iou" in r]
    mean_iou = sum(r["iou"] for r in scored) / len(scored) if scored else 0.0
    ok = bool(scored) and all(r["ok"] for r in results)

    # A run without --report scores but does not claim a trend it has no
    # previous round to measure against, and cannot regress from a best it
    # cannot read.
    run = max((row.get("run", 0) for row in history), default=0) + 1
    regressed = []
    for r in results:
        earlier = rows_for(history, r["label"], r.get("reference")) if hist_file else []
        previous = [row["iou"] for row in earlier
                    if isinstance(row.get("iou"), (int, float))]
        r["run"] = run if hist_file else None
        r["delta"] = (round(r["iou"] - previous[-1], 4)
                      if hist_file and previous and "iou" in r else None)
        r["trend"] = trend(r["delta"]) if hist_file and "iou" in r else None
        top = (best_round(history, r["label"], r.get("reference"))
               if hist_file and "iou" in r else None)
        r["best"] = top["iou"] if top else None
        r["best_run"] = top["run"] if top else None
        r["from_best"] = round(r["iou"] - top["iou"], 4) if top else None
        if top is not None and r["from_best"] < -STALL_DELTA:
            regressed.append(r)
            if not args.accept_regression:
                r["ok"] = False
    if regressed and not args.accept_regression:
        ok = False

    # A loop needs a stopping condition, and "render it again" is not one.
    # Three consecutive rounds that did not move the number mean the edits are
    # no longer reaching what this gate sees.
    stalled_out = []
    for r in results:
        if not hist_file or "iou" not in r:
            continue
        trends = [row.get("trend")
                  for row in rows_for(history, r["label"], r.get("reference"))]
        trends.append(r["trend"])
        streak = 0
        for name in reversed(trends):
            if name not in {"stalled", "regressing"}:
                break
            streak += 1
        r["stall_streak"] = streak
        if streak >= STALL_STREAK:
            stalled_out.append(r)
    stalled = bool(stalled_out) and not ok

    # Each view records WHY it failed, so anything reading this history -- the
    # integrated runner deciding whether a failure is the one the user
    # accepted, most of all -- reads a decision instead of recomputing it.
    # Two implementations of one rule is how the two layers start disagreeing.
    # Precedence matters, and it is not the obvious order. A view can be
    # below the floor AND below its own best at once; calling that "floor"
    # would let a mismatch acceptance -- which only ever covers the floor --
    # carry an unwaived regression through with it. Waiving the regression
    # with --accept-regression empties `blocked`, and only then does the same
    # row become the plain floor failure it also is.
    blocked = set() if args.accept_regression else {id(r) for r in regressed}
    for r in results:
        if "iou" not in r:
            r["failed_because"] = "error"
        elif id(r) in blocked:
            r["failed_because"] = "regression"
        elif r["iou"] < args.min:
            r["failed_because"] = "floor"
        else:
            r["failed_because"] = None

    # A run can clear the floor and still fail, so the verdict names the mark
    # it missed rather than blaming the floor for a regression.
    missed_floor = ([r for r in results if "iou" in r and r["iou"] < args.min]
                    or [r for r in results if "iou" not in r])
    verdict = ("ok" if ok
               else "stalled out" if stalled
               else "below target" if missed_floor
               else "regressed from best")

    payload = {"ok": ok, "min": args.min, "mean_iou": round(mean_iou, 4),
               "verdict": verdict,
               "run": run if hist_file else None,
               "accepted_mismatch": args.accept_mismatch,
               "accepted_regression": args.accept_regression,
               "regressed": [r["label"] for r in regressed],
               "stalled_out": [r["label"] for r in stalled_out],
               "failed_because": {r["label"]: r["failed_because"]
                                  for r in results if r["failed_because"]},
               "views": results}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"{'view':<14}{'IoU':>8}{'delta':>9}{'trend':>11}{'aspect':>9}"
              "  worst bands (render/reference width)")
        for r in results:
            if "iou" not in r:
                print(f"{r['label']:<14}{'ERROR':>8}  {r['error']}")
                continue
            wb = ", ".join(f"{b['from_top']:.2f}:{b['ratio']}" for b in worst_bands(r["bands"]))
            flag = " " if r["ok"] else "!"
            delta = "—" if r["delta"] is None else f"{r['delta']:+.3f}"
            print(f"{r['label']:<14}{r['iou']:>8.3f}{delta:>9}"
                  f"{r['trend'] or '—':>11}{r['aspect_delta']:>9.3f} {flag} {wb}")
        print()
        print(f"mean IoU {mean_iou:.3f} against a {args.min:.2f} floor -- "
              f"{verdict.upper() if verdict != 'ok' else 'ok'}")
        if args.accept_mismatch:
            print(f"floor lowered from {DEFAULT_MIN:.2f}: {args.accept_mismatch}")
        for r in regressed:
            # do not tell a run to pass the flag it already passed
            tail = (f"accepted: {args.accept_regression}" if args.accept_regression
                    else 'revert that round, or pass --accept-regression "<reason>"')
            print(f"REGRESSED  {r['label']} {r['iou']:.3f} is "
                  f"{-r['from_best']:.3f} below run {r['best_run'] or '?'}'s "
                  f"{r['best']:.3f} -- {tail}")
        if stalled:
            told = stall_lines(stalled_out, results, history)
            for i, line in enumerate(told):
                # the first rows are per view; the rest is the shared advice
                print(f"STALLED OUT  {line}" if i < len(stalled_out) else line)
        print("bands run top (0.00) to bottom (0.92); ratio > 1 means the model "
              "is too wide there, < 1 too narrow.")
        if hist_file is None:
            print("no --report, so no history: this run cannot say whether the "
                  "last edit helped.")

    if args.report:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [f"# Likeness report\n",
                 f"run **{run}**, {stamp} -- mean IoU **{mean_iou:.3f}** against a "
                 f"{args.min:.2f} floor -- {verdict}\n"]
        if args.accept_mismatch:
            lines.append(f"> Floor lowered from {DEFAULT_MIN:.2f}: "
                         f"{args.accept_mismatch}\n")
        for r in regressed:
            verdict = (f"accepted: {args.accept_regression}"
                       if args.accept_regression
                       else "blocks delivery; revert the round that moved it down")
            lines.append(f"> Regressed from best: {r['label']} {r['iou']:.3f} vs "
                         f"run {r['best_run'] or '?'}'s {r['best']:.3f} -- "
                         f"{verdict}\n")
        if stalled:
            body = "\n> ".join(stall_lines(stalled_out, results, history))
            lines.append(f"> **Stalled out.** {body}\n")
        lines += ["| view | IoU | delta | trend | aspect (render/ref) | worst bands |",
                  "|---|---|---|---|---|---|"]
        for r in results:
            if "iou" not in r:
                lines.append(f"| {r['label']} | error | — | — | — | {r['error']} |")
                continue
            wb = ", ".join(f"{b['from_top']:.2f} → {b['ratio']}" for b in worst_bands(r["bands"]))
            delta = "—" if r["delta"] is None else f"{r['delta']:+.3f}"
            lines.append(f"| {r['label']} | {r['iou']:.3f} | {delta} | {r['trend']} "
                         f"| {r['aspect_delta']:.3f} | {wb} |")
        lines.append("\nBands run from the top of the silhouette (0.00) to the "
                     "bottom (0.92). A ratio above 1 means the model is too wide "
                     "at that height, below 1 too narrow.\n")

        fresh = [{"run": run, "time": stamp, "label": r["label"],
                  "iou": r.get("iou"), "delta": r["delta"], "trend": r["trend"],
                  "aspect": r.get("aspect_delta"), "min": args.min,
                  "best": r.get("best"), "from_best": r.get("from_best"),
                  "ok": r["ok"], "failed_because": r["failed_because"],
                  "stall_streak": r.get("stall_streak"),
                  "accepted_mismatch": args.accept_mismatch,
                  "accepted_regression": args.accept_regression,
                  "render": r.get("render"), "reference": r.get("reference"),
                  "reference_resolved": (canonical_reference(r["reference"])
                                         if r.get("reference") else None)}
                 for r in results]
        append_history(hist_file, fresh)
        lines.append(history_table(history + fresh, hist_file))
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(lines))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
