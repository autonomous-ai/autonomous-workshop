"""Discover the exact JSON contracts shipped with Inventor Workshop."""

from __future__ import annotations

import sysconfig
from pathlib import Path
from typing import Optional, Tuple

from ._package_data import packaged_data_root
from .errors import ContractError

SCHEMA_NAMES = (
    "inventor.schema.json",
    "playtest-result.schema.json",
    "inspection-result.schema.json",
    "maker-mark.schema.json",
    "receipt.schema.json",
    "stamp.schema.json",
)


def resolve_schemas_root(explicit_root: Optional[Path] = None) -> Path:
    if explicit_root is None:
        package = Path(__file__).resolve().parent
        source = package.parent
        checkout = source.parent / "schemas"
        packaged = packaged_data_root("schemas", Path(__file__))
        legacy_installed = (
            Path(sysconfig.get_path("data"))
            / "share"
            / "inventor-workshop"
            / "schemas"
        )
        if packaged is not None:
            candidate = packaged
        elif source.name == "src" and checkout.is_dir():
            candidate = checkout
        else:
            candidate = legacy_installed
    else:
        candidate = Path(explicit_root)
        if not candidate.is_absolute():
            raise ContractError("an explicit schemas root must be absolute")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ContractError("cannot resolve Workshop schemas root %s" % candidate) from exc
    if not resolved.is_dir():
        raise ContractError("Workshop schemas root is not a directory: %s" % resolved)
    missing = [name for name in SCHEMA_NAMES if not (resolved / name).is_file()]
    if missing:
        raise ContractError("Workshop schemas root is incomplete: %s" % missing)
    return resolved


def discover_schemas(explicit_root: Optional[Path] = None) -> Tuple[Path, ...]:
    root = resolve_schemas_root(explicit_root)
    return tuple(root / name for name in SCHEMA_NAMES)
