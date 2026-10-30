"""The owner's two catalogues a schema 7 Design Contract draws from (ADR 0092).

``filaments.json`` lists the filaments the maker stocks; every printed Part
names one. ``bought-parts.json`` lists what the maker buys: Bought Parts the
buyer assembles (battery boxes, LEDs, pins, screws, jars...), and the tools
and consumables that appear only in the Manual's material lists. A colour or
Bought Part outside a catalogue needs the owner's approval, which is the
owner adding it to the catalogue: nothing in a contract can approve it.

Both files are owned data the owner maintains. An entry the owner has not
confirmed carries ``"confirmed": false`` and may leave its pack size and
source empty; a confirmed Bought Part needs both. Loading is deterministic
and refuses a malformed catalogue, naming every failure at once.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from workshop.errors import ContractError

CATALOGUE_DIRECTORY = Path(__file__).resolve().parent / "catalogues"
FILAMENTS_FILE = "filaments.json"
BOUGHT_PARTS_FILE = "bought-parts.json"
CATALOGUE_SCHEMA_VERSION = 1

FILAMENT_KINDS = ("opaque", "translucent", "glow")
# What a catalogued thing is. Tools and consumables appear only in the
# Manual's material lists (ADR 0092 decision 2); the rest are Bought Parts,
# leaves of the Assembly Tree. A lamp's leads are what lead steps join.
# ``cell`` (a loose battery cell), ``contact`` (a battery contact: spring,
# plate or bridge) and ``switch`` are the powered-toy parts of ADR 0095; a
# ``power`` part is a whole battery box. A part with a ``lead diameter`` size
# is a Wired Part: lead steps join it and its lead routes are swept.
PART_CATEGORIES = ("lamp", "power", "cell", "contact", "switch", "fastener", "container",
                   "bead", "wire", "other")
MATERIAL_CATEGORIES = ("tool", "consumable")
CATEGORIES = PART_CATEGORIES + MATERIAL_CATEGORIES
MAX_NAME_CHARS = 120
# The size whose presence makes a Bought Part a Wired Part (ADR 0095).
LEAD_DIAMETER = "lead diameter"
MAX_SOURCE_CHARS = 500

# The one colour every Bought Part body carries in every STEP and render, so
# a buyer and a maker see it is bought, not printed: a clearly artificial
# magenta no stocked spool is (ADR 0092 decision 5, owner decision Q29,
# 2026-10-23). No filament may take it. The run-local gate
# make-round/scripts/kit_tree.py holds the same value; a test keeps them one.
BOUGHT_PART_HEX = "#ff00ff"
# How far, per 0-255 channel, the colour gate counts a body as one colour.
COLOUR_TOLERANCE = 2

_ID = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
_HEX = re.compile(r"^#[0-9a-f]{6}$")


@dataclass(frozen=True)
class Filament:
    id: str
    name: str
    hex: str
    kind: str
    confirmed: bool


@dataclass(frozen=True)
class CataloguedPart:
    id: str
    name: str
    category: str
    sizes: Tuple[Dict[str, Any], ...]
    pack: Optional[int]
    source: Optional[str]
    confirmed: bool

    @property
    def material(self) -> bool:
        """A tool or consumable: in material lists only, never a tree leaf."""

        return self.category in MATERIAL_CATEGORIES

    @property
    def lead_diameter_mm(self) -> Optional[float]:
        """The largest ``lead diameter`` size, or None: a part with one is a
        Wired Part (ADR 0095), whose lead routes Make sweeps at that size."""

        found = [
            max(size.get("max_mm") or size.get("mm") or [0])
            for size in self.sizes
            if isinstance(size, dict) and size.get("what") == LEAD_DIAMETER
        ]
        return float(max(found)) if found else None


@dataclass(frozen=True)
class Catalogues:
    filaments: Mapping[str, Filament]
    parts: Mapping[str, CataloguedPart]


def _number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


def _near(a: str, b: str) -> bool:
    """Within the colour gate's tolerance: the gate could not tell them apart."""

    return all(abs(int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) <= COLOUR_TOLERANCE for i in (1, 3, 5))


def _name(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= MAX_NAME_CHARS


def parse_filaments(document: Any, errors: List[str]) -> Dict[str, Filament]:
    label = FILAMENTS_FILE
    if not isinstance(document, dict) or document.get("schema_version") != CATALOGUE_SCHEMA_VERSION:
        errors.append("%s must be an object with schema_version %d" % (label, CATALOGUE_SCHEMA_VERSION))
        return {}
    items = document.get("filaments")
    if not isinstance(items, list) or not items:
        errors.append("%s.filaments must be a non-empty list" % label)
        return {}
    filaments: Dict[str, Filament] = {}
    seen: set = set()
    for index, item in enumerate(items):
        where = "%s.filaments[%d]" % (label, index)
        if not isinstance(item, dict) or set(item) != {"id", "name", "hex", "kind", "confirmed"}:
            errors.append("%s must be exactly {id, name, hex, kind, confirmed}" % where)
            continue
        valid = True
        if not isinstance(item["id"], str) or _ID.fullmatch(item["id"]) is None:
            errors.append("%s.id must be lowercase kebab case" % where)
            valid = False
        elif item["id"] in seen:
            errors.append("%s.id repeats %r" % (where, item["id"]))
            valid = False
        else:
            seen.add(item["id"])
        if not _name(item["name"]):
            errors.append("%s.name must be at most %d characters" % (where, MAX_NAME_CHARS))
            valid = False
        if not isinstance(item["hex"], str) or _HEX.fullmatch(item["hex"]) is None:
            errors.append("%s.hex must be a lowercase #rrggbb colour code" % where)
            valid = False
        elif _near(item["hex"], BOUGHT_PART_HEX):
            errors.append("%s.hex is %s, the reserved colour of Bought Parts; no filament may take it"
                          % (where, item["hex"]))
            valid = False
        if item["kind"] not in FILAMENT_KINDS:
            errors.append("%s.kind must be %s" % (where, ", ".join(FILAMENT_KINDS)))
            valid = False
        if not isinstance(item["confirmed"], bool):
            errors.append("%s.confirmed must be true or false" % where)
            valid = False
        if valid:
            filaments[item["id"]] = Filament(**item)
    return filaments


def _sizes(value: Any, where: str, errors: List[str]) -> bool:
    if not isinstance(value, list):
        errors.append("%s.sizes must be a list" % where)
        return False
    valid = True
    for index, size in enumerate(value):
        place = "%s.sizes[%d]" % (where, index)
        keys = set(size) if isinstance(size, dict) else set()
        bounds = [key for key in ("mm", "max_mm") if key in keys]
        if (
            not isinstance(size, dict) or len(bounds) != 1 or keys != {"what", bounds[0]}
            or not _name(size["what"])
            or not isinstance(size[bounds[0]], list) or not 1 <= len(size[bounds[0]]) <= 3
            or any(not _number(item) or item <= 0 for item in size[bounds[0]])
        ):
            errors.append(
                "%s must be {what, mm} (a nominal size) or {what, max_mm} (a limit), "
                "with one to three positive numbers" % place
            )
            valid = False
    return valid


def parse_bought_parts(document: Any, errors: List[str]) -> Dict[str, CataloguedPart]:
    label = BOUGHT_PARTS_FILE
    if not isinstance(document, dict) or document.get("schema_version") != CATALOGUE_SCHEMA_VERSION:
        errors.append("%s must be an object with schema_version %d" % (label, CATALOGUE_SCHEMA_VERSION))
        return {}
    items = document.get("parts")
    if not isinstance(items, list) or not items:
        errors.append("%s.parts must be a non-empty list" % label)
        return {}
    parts: Dict[str, CataloguedPart] = {}
    fields = {"id", "name", "category", "sizes", "pack", "source", "confirmed"}
    seen: set = set()
    for index, item in enumerate(items):
        where = "%s.parts[%d]" % (label, index)
        if not isinstance(item, dict) or set(item) != fields:
            errors.append("%s must be exactly {%s}" % (where, ", ".join(sorted(fields))))
            continue
        valid = True
        if not isinstance(item["id"], str) or _ID.fullmatch(item["id"]) is None:
            errors.append("%s.id must be lowercase, kebab case (dots allowed)" % where)
            valid = False
        elif item["id"] in seen:
            errors.append("%s.id repeats %r" % (where, item["id"]))
            valid = False
        else:
            seen.add(item["id"])
        if not _name(item["name"]):
            errors.append("%s.name must be at most %d characters" % (where, MAX_NAME_CHARS))
            valid = False
        if item["category"] not in CATEGORIES:
            errors.append("%s.category must be one of %s" % (where, ", ".join(CATEGORIES)))
            valid = False
        valid = _sizes(item["sizes"], where, errors) and valid
        confirmed = item["confirmed"]
        if not isinstance(confirmed, bool):
            errors.append("%s.confirmed must be true or false" % where)
            valid = False
        pack, source = item["pack"], item["source"]
        if pack is not None and (isinstance(pack, bool) or not isinstance(pack, int) or pack < 1):
            errors.append("%s.pack must be how many come in one pack, or null" % where)
            valid = False
        if source is not None and (
            not isinstance(source, str) or not source.strip() or len(source) > MAX_SOURCE_CHARS
        ):
            errors.append("%s.source must say where it is bought, or be null" % where)
            valid = False
        # The owner's confirmation is what makes a pack size and source
        # facts; an unconfirmed seed may leave both unknown.
        if confirmed is True and (pack is None or source is None):
            errors.append("%s is confirmed, so it needs its pack size and source" % where)
            valid = False
        if valid:
            parts[item["id"]] = CataloguedPart(
                id=item["id"], name=item["name"], category=item["category"],
                sizes=tuple(item["sizes"]), pack=pack, source=source, confirmed=confirmed,
            )
    return parts


def parse_catalogues(filaments: Any, bought_parts: Any) -> Catalogues:
    """Both catalogues from their parsed JSON documents, or ContractError."""

    errors: List[str] = []
    parsed_filaments = parse_filaments(filaments, errors)
    parsed_parts = parse_bought_parts(bought_parts, errors)
    if errors:
        raise ContractError("catalogue: " + "; ".join(errors))
    return Catalogues(filaments=parsed_filaments, parts=parsed_parts)


def load_catalogues(directory: Optional[Union[str, Path]] = None) -> Catalogues:
    """The owner's catalogues from ``directory`` (default: the packaged ones)."""

    root = Path(directory) if directory is not None else CATALOGUE_DIRECTORY
    documents = []
    for name in (FILAMENTS_FILE, BOUGHT_PARTS_FILE):
        try:
            documents.append(json.loads((root / name).read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            raise ContractError("catalogue: cannot read %s: %s" % (name, exc)) from exc
    return parse_catalogues(*documents)


__all__ = [
    "BOUGHT_PART_HEX",
    "BOUGHT_PARTS_FILE",
    "CATEGORIES",
    "CATALOGUE_DIRECTORY",
    "Catalogues",
    "CataloguedPart",
    "FILAMENTS_FILE",
    "FILAMENT_KINDS",
    "Filament",
    "LEAD_DIAMETER",
    "MATERIAL_CATEGORIES",
    "PART_CATEGORIES",
    "load_catalogues",
    "parse_catalogues",
]
