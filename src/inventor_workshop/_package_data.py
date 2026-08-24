"""Resolve filesystem-backed data shipped inside the Workshop package."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def packaged_data_root(group: str, package_file: Path) -> Optional[Path]:
    """Return an installed package-data directory, if this is an installed build."""

    if group not in ("schemas", "skills"):
        raise ValueError("unknown Workshop package-data group: %s" % group)
    candidate = Path(package_file).resolve().parent / "_data" / group
    try:
        resolved = candidate.resolve(strict=True)
    except OSError:
        return None
    return resolved if resolved.is_dir() else None
