"""``python scripts/check <input.py | project_dir/>`` — validate without keeping artifacts.

Cheap sanity check: runs the user's CAD through the cadpy pipeline in the
sandbox, then deletes the artifacts. Prints ``{ok, is_solid, volume_mm3,
bbox, error?}`` on stdout — the path fields from the full ``scripts/cad``
JSON are stripped because they pointed at a tempdir.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from cad.cli import _resolve_project_and_stem
from common.runner import run_sandboxed_sync


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="scripts/check",
        description="Validate a CadQuery project: solid, manifold, plausible volume.",
    )
    p.add_argument("input", type=Path)
    args = p.parse_args(list(argv) if argv is not None else None)

    if not args.input.exists():
        print(json.dumps({
            "ok": False,
            "error": {
                "code": "VALIDATION_FAILED",
                "message": f"input not found: {args.input}",
            },
        }))
        return 2

    if args.input.is_dir() and not (args.input / "main.py").exists():
        print(json.dumps({
            "ok": False,
            "error": {
                "code": "VALIDATION_FAILED",
                "message": f"project directory {args.input} has no main.py",
            },
        }))
        return 2

    project_dir, stem, scratch = _resolve_project_and_stem(args.input.resolve(), None)

    tmp = Path(tempfile.mkdtemp(prefix="cadcode-check-"))
    try:
        payload = run_sandboxed_sync(
            project_dir=project_dir,
            out_dir=tmp,
            stem=stem or "m",
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if scratch is not None:
            shutil.rmtree(scratch, ignore_errors=True)

    # Strip the path fields — they were tempfiles
    for k in ("stl_path", "step_path", "metadata_path"):
        payload.pop(k, None)
    print(json.dumps(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
