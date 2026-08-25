"""Canonical request values accepted by the Factory integration.

These validators describe Factory's occurrence-based rendering API. They live
with the adapter so the generic durable runtime never depends on Factory field
names or request shapes.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any, List, Mapping, Optional, Sequence

from workshop.errors import ContractError


FACTORY_ASSEMBLY_INVENTORY_FIELD = "_workshop_factory_assembly_inventory"
MAX_FACTORY_ASSEMBLY_PARTS = 128
_FACTORY_COLOR = re.compile(r"#[0-9A-Fa-f]{6}\Z")
_OCCURRENCE_KEYS = {"order", "mesh_name", "part", "color"}
_LEGACY_KEYS = {"part", "color"}
_INVENTORY_KEYS = {"order", "mesh_name", "part"}


def _validate_part(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > 255
        or PurePosixPath(value).name != value
        or "\\" in value
        or value in (".", "..")
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError(
            "Factory assembly_parts part must be one non-empty safe basename"
        )
    return value


def _validate_color(value: Any) -> str:
    if not isinstance(value, str) or _FACTORY_COLOR.fullmatch(value) is None:
        raise ContractError(
            "Factory assembly_parts color must use full #RRGGBB hex"
        )
    return value.lower()


def _validate_order(value: Any, *, inventory: bool = False) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        or value >= MAX_FACTORY_ASSEMBLY_PARTS
    ):
        label = "sealed Factory assembly occurrence" if inventory else "Factory assembly_parts"
        raise ContractError(
            "%s order must be an integer in 0..%d"
            % (label, MAX_FACTORY_ASSEMBLY_PARTS - 1)
        )
    return value


def _validate_mesh_name(value: Any, *, inventory: bool = False) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > 255
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        label = "sealed Factory assembly" if inventory else "Factory assembly_parts"
        raise ContractError(
            "%s mesh_name must be one non-empty trimmed control-free string" % label
        )
    return value


def validate_factory_assembly_parts(
    value: Any,
    *,
    allow_legacy_shorthand: bool = False,
) -> Optional[List[Mapping[str, Any]]]:
    """Canonicalize a reviewed occurrence palette for Factory publication."""

    if value is None:
        return None
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ContractError("Factory assembly_parts must be a non-empty sequence")
    if not value or len(value) > MAX_FACTORY_ASSEMBLY_PARTS:
        raise ContractError(
            "Factory assembly_parts must contain 1..%d reviewed entries"
            % MAX_FACTORY_ASSEMBLY_PARTS
        )
    if any(not isinstance(item, Mapping) for item in value):
        raise ContractError("each Factory assembly_parts entry must be an object")
    shapes = {frozenset(item) for item in value}
    if len(shapes) != 1:
        raise ContractError(
            "Factory assembly_parts entries must use one consistent shape"
        )
    shape = next(iter(shapes), frozenset())
    if shape == frozenset(_LEGACY_KEYS):
        if not allow_legacy_shorthand:
            raise ContractError(
                "Factory live assembly_parts require full occurrence entries "
                "with order, mesh_name, part, and color"
            )
        normalized_legacy: List[Mapping[str, Any]] = []
        seen_parts = set()
        for item in value:
            part = _validate_part(item.get("part"))
            if part in seen_parts:
                raise ContractError(
                    "legacy Factory assembly_parts part names must be unique"
                )
            seen_parts.add(part)
            normalized_legacy.append(
                {"part": part, "color": _validate_color(item.get("color"))}
            )
        return sorted(normalized_legacy, key=lambda item: item["part"])
    if shape != frozenset(_OCCURRENCE_KEYS):
        raise ContractError(
            "each Factory assembly_parts entry must contain exactly order, "
            "mesh_name, part, and color"
        )

    normalized: List[Mapping[str, Any]] = []
    seen_orders = set()
    for item in value:
        order = _validate_order(item.get("order"))
        if order in seen_orders:
            raise ContractError(
                "Factory assembly_parts occurrence orders must be unique"
            )
        seen_orders.add(order)
        normalized.append(
            {
                "order": order,
                "mesh_name": _validate_mesh_name(item.get("mesh_name")),
                "part": _validate_part(item.get("part")),
                "color": _validate_color(item.get("color")),
            }
        )
    normalized.sort(key=lambda item: item["order"])
    if [item["order"] for item in normalized] != list(range(len(normalized))):
        raise ContractError(
            "Factory assembly_parts must cover contiguous occurrence orders from zero"
        )
    return normalized


def validate_factory_assembly_inventory(
    value: Any,
) -> Optional[List[Mapping[str, Any]]]:
    """Canonicalize the color-free occurrence inventory sealed at import."""

    if value is None:
        return None
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ContractError(
            "sealed Factory assembly inventory must be a non-empty sequence"
        )
    if not value or len(value) > MAX_FACTORY_ASSEMBLY_PARTS:
        raise ContractError(
            "sealed Factory assembly inventory must contain 1..%d occurrences"
            % MAX_FACTORY_ASSEMBLY_PARTS
        )
    normalized: List[Mapping[str, Any]] = []
    seen_orders = set()
    for item in value:
        if not isinstance(item, Mapping) or set(item) != _INVENTORY_KEYS:
            raise ContractError(
                "each sealed Factory assembly occurrence must contain exactly "
                "order, mesh_name, and part"
            )
        order = _validate_order(item.get("order"), inventory=True)
        if order in seen_orders:
            raise ContractError(
                "sealed Factory assembly occurrence orders must be unique integers "
                "in 0..%d" % (MAX_FACTORY_ASSEMBLY_PARTS - 1)
            )
        seen_orders.add(order)
        normalized.append(
            {
                "order": order,
                "mesh_name": _validate_mesh_name(item.get("mesh_name"), inventory=True),
                "part": _validate_part(item.get("part")),
            }
        )
    normalized.sort(key=lambda item: item["order"])
    if [item["order"] for item in normalized] != list(range(len(normalized))):
        raise ContractError(
            "sealed Factory assembly inventory must cover contiguous orders from zero"
        )
    return normalized


def bind_factory_assembly_parts(
    value: Any,
    inventory: Any,
) -> Optional[List[Mapping[str, Any]]]:
    """Bind a requested palette to the exact sealed import occurrences."""

    normalized = validate_factory_assembly_parts(value)
    if normalized is None:
        return None
    expected = validate_factory_assembly_inventory(inventory)
    if expected is None:
        raise ContractError(
            "Factory assembly_parts require a sealed occurrence inventory in the "
            "imported model handoff"
        )
    identities = [
        {
            "order": item["order"],
            "mesh_name": item["mesh_name"],
            "part": item["part"],
        }
        for item in normalized
    ]
    if identities != expected:
        raise ContractError(
            "Factory assembly_parts must match the exact sealed occurrence count, "
            "order, mesh_name, and part; only colors may vary"
        )
    return normalized


__all__ = [
    "FACTORY_ASSEMBLY_INVENTORY_FIELD",
    "MAX_FACTORY_ASSEMBLY_PARTS",
    "bind_factory_assembly_parts",
    "validate_factory_assembly_inventory",
    "validate_factory_assembly_parts",
]
