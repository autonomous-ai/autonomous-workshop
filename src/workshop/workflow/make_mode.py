"""Frozen Make selection and its narrow product-declaration boundary.

These checks bind a host-selected mode. Manufacturing and CAD validation stay
inside Make; this module neither opens a BOM nor executes engineering tools.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional

from workshop._validation import require_sha256
from workshop.errors import ContractError


MAKE_PROJECT_PATH = "MAKE.json"
MAKE_MODES = ("print", "mixed")
DEFAULT_MAKE_MODE = "print"
MIXED_MATERIAL_SKILL = "mixed-materials"


def validate_make_mode(mode: Optional[str], *, workflow: Optional[str]) -> Optional[str]:
    """None preserves the unselected protocol of existing/programmatic runs."""
    if mode is None:
        return None
    if not isinstance(mode, str) or mode not in MAKE_MODES:
        raise ContractError("Make mode must be one of: print, mixed")
    if mode == "mixed" and workflow != "spark":
        raise ContractError("mixed Make mode is currently supported only for Spark")
    return mode


def make_mode_document(mode: str) -> dict[str, Any]:
    if not isinstance(mode, str) or mode not in MAKE_MODES:
        raise ContractError("Make mode must be one of: print, mixed")
    return {"schema_version": 1, "mode": mode}


def make_project_bytes(mode: str) -> bytes:
    return (json.dumps(make_mode_document(mode), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def parse_make_project_bytes(content: bytes, *, workflow: Optional[str]) -> str:
    def strict_pairs(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate Make input key")
            value[key] = item
        return value

    if not isinstance(content, bytes) or len(content) > 1024:
        raise ContractError("Make input must be bounded canonical JSON")
    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=strict_pairs)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ContractError("Make input must be strict UTF-8 JSON") from exc
    if (not isinstance(value, dict) or set(value) != {"schema_version", "mode"}
            or type(value["schema_version"]) is not int or value["schema_version"] != 1):
        raise ContractError("Make input must declare schema_version 1 and mode")
    mode = validate_make_mode(value["mode"], workflow=workflow)
    if mode is None or content != make_project_bytes(mode):
        raise ContractError("Make input must be canonical and select a mode")
    return mode


def validate_make_product(mode: Optional[str], product: Mapping[str, Any]) -> None:
    """Enforce declared mode only, without revalidating Make's manufacturing."""
    if mode is None:
        return
    make_mode_document(mode)
    if mode == "print":
        if "manufacturing" in product:
            raise ContractError("print Make mode forbids a manufacturing manifest")
        return
    marker = product.get("manufacturing")
    if (not isinstance(marker, Mapping)
            or set(marker) != {"schema_version", "manifest_path", "manifest_sha256"}
            or type(marker["schema_version"]) is not int or marker["schema_version"] != 1
            or marker["manifest_path"] != "internal/manufacturing.json"):
        raise ContractError("mixed Make mode requires a version 1 manufacturing manifest binding")
    require_sha256(marker["manifest_sha256"], "mixed Make manufacturing manifest sha256")
