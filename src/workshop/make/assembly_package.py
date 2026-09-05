"""Typed reader for the cadgen assembly-package descriptor Make seals.

Make's required root file ``assembled.step.json`` is written by the CAD
skill's ``artifact`` tool as an *assembly-package*: the occurrence tree of the
sealed STEP with one 4x4 row-major transform and one optional surface colour
per occurrence.  The trusted host reads it here for two purposes only:

* the Factory handoff derives one production mesh per occurrence from it so a
  multi-part toy reaches the shop as addressable, colourable meshes; and
* the Make gate requires every occurrence of a multi-part package to have its
  sealed production STL under ``parts/<name>.stl``, the same path the
  build-group contract already uses.

Colour channels are the raw values the designer passed to build123d's
``Color``.  The cadgen GLB exporter and the shop viewer display those values
as sRGB, so this module reports them as the ``#rrggbb`` a viewer shows.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Collection, Mapping, Optional, Sequence, Tuple

from workshop.errors import ContractError


ASSEMBLY_PACKAGE_KIND = "assembly-package"
ASSEMBLY_PACKAGE_SCHEMA_VERSION = 2
ASSEMBLY_PACKAGE_PATH = "assembled.step.json"
PRODUCTION_PARTS_DIRECTORY = "parts"
MAX_ASSEMBLY_PACKAGE_BYTES = 16 * 1024 * 1024
MAX_ASSEMBLY_OCCURRENCES = 512
OCCURRENCE_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
IDENTITY_TRANSFORM: Tuple[float, ...] = (
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0,
)


def _strict_object(pairs: Sequence[Tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("non-finite JSON constant %s" % value)


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError("%s must be a finite number" % label)
    number = float(value)
    if not math.isfinite(number):
        raise ContractError("%s must be a finite number" % label)
    return number


def srgb_channels_hex(channels: Sequence[float]) -> str:
    """Return ``#rrggbb`` for raw 0..1 channels displayed as sRGB."""

    if len(channels) < 3:
        raise ValueError("a colour requires at least three channels")
    encoded = []
    for value in channels[:3]:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value != value
            or not 0.0 <= float(value) <= 1.0
        ):
            raise ValueError("colour channel is outside 0..1")
        # Round half up like the viewer, not to even like Python.
        encoded.append(max(0, min(255, int(float(value) * 255.0 + 0.5))))
    return "#%02x%02x%02x" % tuple(encoded)


@dataclass(frozen=True)
class AssemblyOccurrence:
    """One leaf occurrence of the sealed assembly."""

    name: str
    transform: Tuple[float, ...]
    color: Optional[Tuple[float, float, float, float]]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or OCCURRENCE_NAME.fullmatch(self.name) is None:
            raise ContractError("assembly-package occurrence name is unsafe")
        if len(self.transform) != 16 or not all(
            isinstance(item, float) and math.isfinite(item) for item in self.transform
        ):
            raise ContractError("assembly-package occurrence transform is invalid")
        if self.color is not None and (
            len(self.color) != 4
            or not all(
                isinstance(item, float) and 0.0 <= item <= 1.0 for item in self.color
            )
        ):
            raise ContractError("assembly-package occurrence colour is invalid")

    @property
    def production_stl_path(self) -> str:
        return "%s/%s.stl" % (PRODUCTION_PARTS_DIRECTORY, self.name)

    @property
    def translation(self) -> Tuple[float, float, float]:
        return (self.transform[3], self.transform[7], self.transform[11])

    @property
    def color_hex(self) -> Optional[str]:
        return None if self.color is None else srgb_channels_hex(self.color)


@dataclass(frozen=True)
class AssemblyPackage:
    """The validated occurrence view of one sealed assembly-package."""

    root_name: str
    units: str
    occurrences: Tuple[AssemblyOccurrence, ...]

    def __post_init__(self) -> None:
        if not 1 <= len(self.occurrences) <= MAX_ASSEMBLY_OCCURRENCES:
            raise ContractError("assembly-package occurrence count is out of range")
        names = [item.name for item in self.occurrences]
        if len(set(names)) != len(names):
            raise ContractError("assembly-package occurrence names must be unique")

    @property
    def occurrence_count(self) -> int:
        return len(self.occurrences)

    @property
    def is_multipart(self) -> bool:
        return len(self.occurrences) >= 2

    @property
    def production_stl_paths(self) -> Tuple[str, ...]:
        return tuple(item.production_stl_path for item in self.occurrences)

    def part_colors(self) -> dict[str, str]:
        return {
            item.name: item.color_hex
            for item in self.occurrences
            if item.color_hex is not None
        }


def is_assembly_package(value: Any) -> bool:
    """Report whether a parsed JSON document claims the assembly-package shape."""

    return (
        isinstance(value, Mapping)
        and value.get("kind") == ASSEMBLY_PACKAGE_KIND
        and value.get("schemaVersion") == ASSEMBLY_PACKAGE_SCHEMA_VERSION
    )


def _occurrence(value: Any, index: int) -> AssemblyOccurrence:
    label = "assembly-package occurrence %d" % index
    if not isinstance(value, Mapping):
        raise ContractError("%s is malformed" % label)
    name = value.get("name")
    if not isinstance(name, str) or OCCURRENCE_NAME.fullmatch(name) is None:
        raise ContractError("%s name is unsafe" % label)
    raw_transform = value.get("transform", list(IDENTITY_TRANSFORM))
    if (
        isinstance(raw_transform, (str, bytes))
        or not isinstance(raw_transform, Sequence)
        or len(raw_transform) != 16
    ):
        raise ContractError("%s transform must have 16 entries" % label)
    transform = tuple(
        _finite(item, "%s transform entry" % label) for item in raw_transform
    )
    raw_color = value.get("color")
    color: Optional[Tuple[float, float, float, float]] = None
    if raw_color is not None:
        if (
            isinstance(raw_color, (str, bytes))
            or not isinstance(raw_color, Sequence)
            or len(raw_color) not in (3, 4)
        ):
            raise ContractError("%s colour must have three or four channels" % label)
        channels = [_finite(item, "%s colour channel" % label) for item in raw_color]
        if any(not 0.0 <= item <= 1.0 for item in channels):
            raise ContractError("%s colour channel is outside 0..1" % label)
        if len(channels) == 3:
            channels.append(1.0)
        color = (channels[0], channels[1], channels[2], channels[3])
    return AssemblyOccurrence(name=name, transform=transform, color=color)


def read_assembly_package(content: bytes) -> AssemblyPackage:
    """Parse and validate exact assembly-package bytes."""

    if not isinstance(content, bytes) or not 1 <= len(content) <= MAX_ASSEMBLY_PACKAGE_BYTES:
        raise ContractError("assembly-package must be bounded non-empty bytes")
    try:
        document = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ContractError("assembly-package must be strict UTF-8 JSON") from exc
    if not is_assembly_package(document):
        raise ContractError("document is not a schemaVersion 2 assembly-package")
    package_schema = document.get("packageSchemaVersion")
    if isinstance(package_schema, bool) or not isinstance(package_schema, int) or package_schema < 1:
        raise ContractError("assembly-package packageSchemaVersion is invalid")
    if document.get("entryKind") not in ("assembly", "part"):
        raise ContractError("assembly-package entryKind is unsupported")
    raw_occurrences = document.get("occurrences")
    if (
        isinstance(raw_occurrences, (str, bytes))
        or not isinstance(raw_occurrences, Sequence)
        or not 1 <= len(raw_occurrences) <= MAX_ASSEMBLY_OCCURRENCES
    ):
        raise ContractError("assembly-package occurrences are out of range")
    occurrences = tuple(
        _occurrence(item, index) for index, item in enumerate(raw_occurrences)
    )
    stats = document.get("stats")
    if isinstance(stats, Mapping) and "occurrenceCount" in stats:
        declared = stats["occurrenceCount"]
        if isinstance(declared, bool) or declared != len(occurrences):
            raise ContractError("assembly-package occurrenceCount differs from its occurrences")
    root_name = document.get("rootName", "")
    units = document.get("units", "mm")
    if not isinstance(root_name, str) or not isinstance(units, str):
        raise ContractError("assembly-package rootName and units must be strings")
    return AssemblyPackage(root_name=root_name, units=units, occurrences=occurrences)


def read_assembly_package_file(path: Path) -> AssemblyPackage:
    """Read one regular assembly-package file without following symlinks."""

    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ContractError("assembly-package %s is missing or not a regular file" % path.name)
    if path.stat().st_size > MAX_ASSEMBLY_PACKAGE_BYTES:
        raise ContractError("assembly-package %s exceeds its size bound" % path.name)
    return read_assembly_package(path.read_bytes())


def missing_production_parts(
    package: AssemblyPackage, sealed_paths: Collection[str]
) -> Tuple[str, ...]:
    """Return the production STL paths a multi-part package lacks."""

    if not package.is_multipart:
        return ()
    sealed = set(sealed_paths)
    return tuple(
        path for path in package.production_stl_paths if path not in sealed
    )


def validate_production_parts(
    package: AssemblyPackage, sealed_paths: Collection[str]
) -> Tuple[str, ...]:
    """Require one sealed production STL per occurrence of a multi-part package."""

    missing = missing_production_parts(package, sealed_paths)
    if missing:
        raise ContractError(
            "Made assembly-package lists %d occurrences but lacks production STLs: %s"
            % (package.occurrence_count, ", ".join(missing))
        )
    return package.production_stl_paths if package.is_multipart else ()


__all__ = [
    "ASSEMBLY_PACKAGE_KIND",
    "ASSEMBLY_PACKAGE_PATH",
    "ASSEMBLY_PACKAGE_SCHEMA_VERSION",
    "AssemblyOccurrence",
    "AssemblyPackage",
    "IDENTITY_TRANSFORM",
    "MAX_ASSEMBLY_PACKAGE_BYTES",
    "PRODUCTION_PARTS_DIRECTORY",
    "is_assembly_package",
    "missing_production_parts",
    "read_assembly_package",
    "read_assembly_package_file",
    "srgb_channels_hex",
    "validate_production_parts",
]
