"""The exact extents of a STEP file, for build-a-toy DETECT (ADR 0096 pilot, B12).

``inspect refs --facts`` reports an assembly's bounding box loosely: on curved
faces it can include B-spline control points, so the beaver coaster keeper
measured 308.8 x 350.5 x 183.0 mm against its true 186.3 x 312.5 x 183.0 mm,
a false ``envelope`` finding at DETECT's 0.05 mm rule. This tool takes the
optimal (exact-geometry) bounding box of every solid in the file, with no
rebuild, and reports their union.

    python -m workshop.make.envelope STEP [--json OUT]

It prints one JSON object, ``{"step", "solids", "bbox": [xmin, ymin, zmin,
xmax, ymax, zmax], "size": [x, y, z], "method"}``, and exits 0; it exits 2
with a reason on stderr for a missing or unreadable file or one with no
solid. Nothing it cannot measure is reported as a size.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

METHOD = "union of each solid's optimal bounding box"


class EnvelopeError(Exception):
    """A STEP file whose envelope cannot be measured."""


def _boxes(solids: Iterable[Any]) -> list[list[float]]:
    boxes = []
    for solid in solids:
        box = solid.bounding_box(optimal=True)
        boxes.append([box.min.X, box.min.Y, box.min.Z, box.max.X, box.max.Y, box.max.Z])
    return boxes


def union(boxes: Sequence[Sequence[float]]) -> list[float]:
    """The bounding box of several ``[xmin, ymin, zmin, xmax, ymax, zmax]``."""

    if not boxes:
        raise EnvelopeError("no solid to measure")
    return [min(box[i] for box in boxes) for i in range(3)] + [max(box[i] for box in boxes) for i in range(3, 6)]


def measure(path: Path) -> dict[str, Any]:
    """The exact envelope of one STEP file, or EnvelopeError."""

    path = Path(path)
    if not path.is_file():
        raise EnvelopeError("%s: no such STEP file" % path)
    import build123d as bd  # deferred: --help must not load OCP

    try:
        shape = bd.import_step(str(path))
    except Exception as exc:  # noqa: BLE001 - OCP raises many types
        raise EnvelopeError("%s: not a readable STEP file (%s)" % (path, type(exc).__name__)) from exc
    solids = list(shape.solids())
    if not solids:
        raise EnvelopeError("%s: holds no solid" % path)
    bbox = union(_boxes(solids))
    return {
        "step": str(path),
        "solids": len(solids),
        "bbox": [round(value, 6) + 0.0 for value in bbox],
        "size": [round(bbox[i + 3] - bbox[i], 6) + 0.0 for i in range(3)],
        "method": METHOD,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m workshop.make.envelope", description=__doc__.splitlines()[0])
    parser.add_argument("step", type=Path)
    parser.add_argument("--json", type=Path, dest="out", help="also write the report here")
    args = parser.parse_args(argv)
    try:
        report = measure(args.step)
    except EnvelopeError as exc:
        print("envelope: %s" % exc, file=sys.stderr)
        return 2
    text = json.dumps(report, sort_keys=True)
    if args.out is not None:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
