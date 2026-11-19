from __future__ import annotations
import os as _cadthreads_os, runpy as _cadthreads_runpy  # noqa: E401,E402
# Before numpy, build123d or OCP load: one BLAS/OpenMP/OCCT thread unless the caller set one.
_cadthreads_path = _cadthreads_os.path.join(_cadthreads_os.path.dirname(_cadthreads_os.path.abspath(__file__)), "..", "cadthreads.py")
# A copy made without its helper runs as before, unpinned.
_cadthreads = _cadthreads_runpy.run_path(_cadthreads_path) if _cadthreads_os.path.isfile(_cadthreads_path) else None
if _cadthreads is not None:
    _cadthreads["pin"](occ=True)

import sys
from pathlib import Path

if __package__ in {None, ""}:
    tool_dir = Path(__file__).resolve().parent
    if str(tool_dir) not in sys.path:
        sys.path.insert(0, str(tool_dir))
    from server import main
else:
    from .server import main


if __name__ == "__main__":
    raise SystemExit(main())
