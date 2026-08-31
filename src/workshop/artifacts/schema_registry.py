"""Discover the exact JSON contracts owned by Workshop components."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from workshop.errors import ContractError

SCHEMA_LOCATIONS = (
    ("artifact-manifest.schema.json", Path("artifacts/schemas/artifact-manifest.schema.json")),
    ("inventor.schema.json", Path("contributors/schemas/inventor.schema.json")),
    ("receipt.schema.json", Path("runtime/schemas/receipt.schema.json")),
    ("cad-project.schema.json", Path("make/schemas/cad-project.schema.json")),
    ("validator-policy.schema.json", Path("make/schemas/validator-policy.schema.json")),
    (
        "verification-receipt.schema.json",
        Path("make/schemas/verification-receipt.schema.json"),
    ),
    ("concept-v1.schema.json", Path("concept/schemas/concept-v1.schema.json")),
    ("concept-v2.schema.json", Path("concept/schemas/concept-v2.schema.json")),
)
SCHEMA_NAMES = tuple(name for name, _ in SCHEMA_LOCATIONS)


def resolve_schemas_root(explicit_root: Optional[Path] = None) -> Path:
    if explicit_root is None:
        candidate = Path(__file__).resolve().parents[1]
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
    flat = all((resolved / name).is_file() for name in SCHEMA_NAMES)
    owned = all((resolved / relative).is_file() for _, relative in SCHEMA_LOCATIONS)
    if not flat and not owned:
        missing = [
            name
            for name, relative in SCHEMA_LOCATIONS
            if not (resolved / name).is_file() and not (resolved / relative).is_file()
        ]
        raise ContractError("Workshop schemas root is incomplete: %s" % missing)
    return resolved


def discover_schemas(explicit_root: Optional[Path] = None) -> Tuple[Path, ...]:
    root = resolve_schemas_root(explicit_root)
    if all((root / name).is_file() for name in SCHEMA_NAMES):
        return tuple(root / name for name in SCHEMA_NAMES)
    return tuple(root / relative for _, relative in SCHEMA_LOCATIONS)
