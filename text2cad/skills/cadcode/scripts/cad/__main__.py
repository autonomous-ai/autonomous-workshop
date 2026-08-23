from __future__ import annotations

import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    scripts_dir = Path(__file__).resolve().parents[1]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from cad.cli import main
else:
    from .cli import main


def _apply_mem_limit() -> None:
    """Opt-in address-space cap (CADPY_MEM_LIMIT_MB, set by pipeline harnesses).

    A runaway OCCT boolean chain otherwise grows until the kernel OOM-killer
    fires — which takes out the whole pipeline (and nearly the host) instead of
    just this export. Under the rlimit the same runaway dies as a MemoryError /
    std::bad_alloc inside this process, which the calling agent can see and
    repair. No-op unless the env var is set (other cadcode users unaffected)."""
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
        pass  # bad value or unsupported platform — better unlimited than dead


if __name__ == "__main__":
    _apply_mem_limit()
    raise SystemExit(main())
