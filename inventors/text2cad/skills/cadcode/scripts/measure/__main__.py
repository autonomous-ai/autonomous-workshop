from __future__ import annotations

import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    scripts_dir = Path(__file__).resolve().parents[1]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from measure.cli import main
else:
    from .cli import main


def _apply_mem_limit() -> None:
    """Opt-in address-space cap (CADPY_MEM_LIMIT_MB), same contract as scripts/cad.

    Measuring loads the whole STEP scene, so an assembly big enough to OOM the
    export is big enough to OOM the measurement — and this tool exists partly
    because the trimesh alternative did exactly that. Under the rlimit it dies
    as a MemoryError this CLI reports as JSON instead of taking the host down."""
    mb = os.environ.get("CADPY_MEM_LIMIT_MB", "").strip()
    if not mb:
        return
    try:
        import resource

        limit = int(mb) * 1024 * 1024
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        if hard != resource.RLIM_INFINITY:
            limit = min(limit, hard)
        resource.setrlimit(resource.RLIMIT_AS, (limit, hard))
    except (ValueError, OSError, ImportError):
        pass


if __name__ == "__main__":
    _apply_mem_limit()
    raise SystemExit(main())
