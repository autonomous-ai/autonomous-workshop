"""Access Make's frozen, standalone mixed-material contract implementation.

The run-local finalizer owns manufacturing validation. Host publication uses
only the explicit public projection and exact file identities; it does not
rebuild CAD or repeat Make's engineering checks.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import runpy
from typing import Any, Mapping

from workshop.errors import ContractError


@lru_cache(maxsize=1)
def _implementation() -> Mapping[str, Any]:
    script = (
        Path(__file__).parent / "skills" / "mixed-materials" / "scripts"
        / "manufacturing_manifest.py"
    )
    if script.is_symlink() or not script.is_file():
        raise ContractError("Make's mixed-material contract implementation is unavailable")
    return runpy.run_path(str(script))


def _call(name: str, product_root: Path, product: Mapping[str, Any]) -> Any:
    if "manufacturing" not in product:
        return None
    try:
        return _implementation()[name](Path(product_root), product)
    except (ValueError, OSError, TypeError) as exc:
        raise ContractError("invalid Make manufacturing contract: %s" % exc) from exc


def read_manifest(product_root: Path, product: Mapping[str, Any]) -> dict[str, Any] | None:
    """Read the exact bound internal manifest without running engineering checks."""
    return _call("read_manifest", product_root, product)


def public_asset_paths(
    product_root: Path, product: Mapping[str, Any]
) -> tuple[str, ...] | None:
    """Return verified presentation paths, or None for a historical product."""
    return _call("public_asset_paths", product_root, product)


__all__ = ["read_manifest", "public_asset_paths"]
