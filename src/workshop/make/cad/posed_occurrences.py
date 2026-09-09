"""Posed occurrence geometry from a sealed assembly STEP.

The Factory viewer numbers part groups from the assembled mesh alone, so the
host needs each occurrence's geometry *in its assembled pose* to say which
group belongs to which sealed part.  The production STLs under ``parts/`` are
exported in print orientation and cannot place themselves; the sealed
``assembled.step`` can.  This module runs the CAD kernel in a bounded,
credential-free subprocess (the same interpreter the CAD verifier uses),
tessellates every top-level occurrence coarsely, and returns names, extents,
and a bounded point sample per occurrence.  When the kernel is unavailable
the caller degrades exactly as before this module existed.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

from workshop.errors import ContractError
from workshop.make.cad.fe_parts import PosedOccurrence
from workshop.runtime.execution import minimal_tool_environment


MAX_STEP_BYTES = 256 * 1024 * 1024
MAX_OCCURRENCES = 512
MAX_POINTS_PER_OCCURRENCE = 4_096
MAX_OUTPUT_BYTES = 64 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 600.0
LINEAR_DEFLECTION = 0.1
ANGULAR_DEFLECTION = 0.5

PosedProvider = Callable[[bytes], Sequence[PosedOccurrence]]


class PosedOccurrenceError(Exception):
    """A bounded reason why posed geometry could not be produced."""


_TOOL = r'''
import json, sys
from build123d import import_step
step_path, out_path, linear, angular, max_points = sys.argv[1:6]
shape = import_step(step_path)
children = list(getattr(shape, "children", []) or [])
if not children:
    children = [shape]
records = []
for child in children:
    label = str(getattr(child, "label", "") or "")
    try:
        vertices, _ = child.tessellate(float(linear), float(angular))
    except Exception:
        continue
    points = [(float(v.X), float(v.Y), float(v.Z)) for v in vertices]
    if not points:
        continue
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    limit = int(max_points)
    if len(points) > limit:
        step = len(points) / float(limit)
        points = [points[int(k * step)] for k in range(limit)]
    records.append({"name": label, "bbox_min": lo, "bbox_max": hi, "points": points})
with open(out_path, "w", encoding="utf-8") as handle:
    json.dump(records, handle)
'''


def _parse(records: object) -> Tuple[PosedOccurrence, ...]:
    if not isinstance(records, list) or not records:
        raise PosedOccurrenceError("posed occurrence tool returned no occurrences")
    if len(records) > MAX_OCCURRENCES:
        raise PosedOccurrenceError("posed occurrence tool returned too many occurrences")
    result = []
    for item in records:
        if not isinstance(item, dict):
            raise PosedOccurrenceError("posed occurrence record is malformed")
        points = item.get("points")
        if not isinstance(points, list) or not points or len(points) > MAX_POINTS_PER_OCCURRENCE:
            raise PosedOccurrenceError("posed occurrence points are out of range")
        try:
            result.append(
                PosedOccurrence(
                    name=str(item.get("name", "")),
                    bbox_min=tuple(float(v) for v in item["bbox_min"]),
                    bbox_max=tuple(float(v) for v in item["bbox_max"]),
                    points=tuple(tuple(float(v) for v in point) for point in points),
                )
            )
        except (ContractError, KeyError, TypeError, ValueError) as exc:
            raise PosedOccurrenceError("posed occurrence record is invalid: %s" % exc) from exc
    return tuple(result)


def posed_occurrences(
    step: bytes,
    *,
    python: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Tuple[PosedOccurrence, ...]:
    """Tessellate every top-level occurrence of sealed STEP bytes in pose."""

    if not isinstance(step, bytes) or not step or len(step) > MAX_STEP_BYTES:
        raise PosedOccurrenceError("STEP bytes are empty or exceed the size bound")
    executable = python or sys.executable
    with tempfile.TemporaryDirectory(prefix="workshop-posed-") as temporary:
        root = Path(temporary)
        step_path = root / "assembled.step"
        out_path = root / "occurrences.json"
        step_path.write_bytes(step)
        try:
            completed = subprocess.run(
                [
                    executable,
                    "-c",
                    _TOOL,
                    str(step_path),
                    str(out_path),
                    str(LINEAR_DEFLECTION),
                    str(ANGULAR_DEFLECTION),
                    str(MAX_POINTS_PER_OCCURRENCE),
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env={**minimal_tool_environment(), "PYTHONDONTWRITEBYTECODE": "1"},
                cwd=str(root),
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PosedOccurrenceError("posed occurrence tool could not run: %s" % type(exc).__name__) from exc
        if completed.returncode != 0:
            tail = (completed.stderr or completed.stdout or "").strip().splitlines()
            raise PosedOccurrenceError(
                "posed occurrence tool exited %d: %s" % (completed.returncode, tail[-1] if tail else "")
            )
        try:
            if out_path.stat().st_size > MAX_OUTPUT_BYTES:
                raise PosedOccurrenceError("posed occurrence tool output exceeds its bound")
            records = json.loads(out_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            raise PosedOccurrenceError("posed occurrence tool output is unreadable") from exc
    return _parse(records)


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "PosedOccurrenceError",
    "PosedProvider",
    "posed_occurrences",
]
