"""A Design Contract's Bought Parts list (ADR 0095 amendment, 2026-11-07).

A toy's electrical section names every circuit part, but the steel pins,
springs, glue and other bought hardware a toy ships are named only in its
prose, and the factory-assembled board (``pcba``) is no catalogue part, so
nothing sealed says what it costs. Release bills the buyer for all of them as
Factory ``extra_materials``, so they must be sealed with the contract.

They are written in one optional fenced block beside the design-contract
block::

    ```bought-parts
    {"parts": [{"bought": "steel-pin-1.5x29.5", "count": 10},
               {"bought": "glue", "count": 1}],
     "pcba": {"unit_price_cents": 400, "estimate": true,
              "source": "owner, 2026-11-07"}}
    ```

``parts`` lists the catalogue entries the toy ships that its electrical
section does not already name, each with how many one toy takes. ``pcba``
prices the electrical section's factory-assembled board, which no catalogue
records; ``estimate`` says the price is not a quote, and ``source`` says
who gave it.

A kit (ADR 0104) may carry the block too. Its Assembly Tree already says
which Bought Parts the buyer assembles, so the block must agree with it:
every catalogue entry a tree leaf names, unless the electrical section
already counts it, appears with at least as many pieces as the tree holds
(more are spares), and any other entry is a tool or consumable the tree's
``materials`` lists, such as the nippers or glue the box includes, or
packaging: the printed Manual and the box packing. The Manual's
self-prepared materials (scissors, batteries) are simply left out.

The block says nothing about shape, so it belongs to no prose section and
the hash an Approved Proof binds leaves it out (``strip_bought_block``): an
owner may price a sealed design without re-sealing its Proof.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from workshop.wish.assembly_tree import bought_totals
from workshop.wish.catalogues import MAX_UNIT_PRICE_CENTS, Catalogues


BOUGHT_FENCE_OPEN = re.compile(r"^ {0,3}```bought-parts\s*$")
_BLOCK = re.compile(r"^```bought-parts[ \t]*\n(.*?)^```[ \t]*$", re.DOTALL | re.MULTILINE)
# The block and the blank lines before it, as an owner adds it to a sealed
# contract: removing exactly this gives back the text the Proof was sealed for.
_STRIP = re.compile(r"^\n*```bought-parts[ \t]*\n.*?^```[ \t]*(?:\n|\Z)", re.DOTALL | re.MULTILINE)
MAX_COUNT = 999
MAX_SOURCE_CHARS = 200
BOUGHT_LIST_SCHEMA_VERSION = 10


@dataclass(frozen=True)
class ContractBought:
    """The validated block, as the sealed contract carries it."""

    section: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return self.section


def strip_bought_block(text: str) -> str:
    """``text`` without its Bought Parts block and the blank lines before it."""

    return _STRIP.sub("", text, count=1)


def parse_bought_block(
    text: str,
    *,
    version: int,
    has_tree: bool,
    tree: Optional[Mapping[str, Any]] = None,
    electrical: Optional[Mapping[str, Any]],
    catalogues: Optional[Catalogues],
    errors: List[str],
) -> Optional[ContractBought]:
    """The contract's Bought Parts block, or None when it has none. Every
    failure is appended to ``errors``."""

    found = _BLOCK.findall(text)
    if not found:
        return None
    label = "bought-parts"
    before = len(errors)
    if len(found) > 1:
        errors.append("a contract has at most one bought-parts block; found %d" % len(found))
        return None
    if version < BOUGHT_LIST_SCHEMA_VERSION:
        errors.append("a bought-parts block needs schema_version 10 or later")
        return None
    if has_tree and not isinstance(tree, Mapping):
        # The tree did not parse: its own failures are already listed.
        return None
    try:
        value = json.loads(found[0])
    except json.JSONDecodeError as exc:
        errors.append("the bought-parts block does not parse as JSON: %s" % exc)
        return None
    if not isinstance(value, dict) or not value or not set(value) <= {"parts", "pcba"}:
        errors.append("%s must be an object with parts, pcba or both" % label)
        return None
    circuit = {
        item.get("bought")
        for item in ((electrical or {}).get("parts") or ())
        if isinstance(item, dict) and isinstance(item.get("bought"), str)
    }
    parts = value.get("parts", [])
    if not isinstance(parts, list) or ("parts" in value and not parts):
        errors.append("%s.parts must be a non-empty list of {bought, count}" % label)
        parts = []
    seen: set = set()
    for index, item in enumerate(parts):
        where = "%s.parts[%d]" % (label, index)
        if not isinstance(item, dict) or set(item) != {"bought", "count"}:
            errors.append("%s must be exactly {bought, count}" % where)
            continue
        bought, count = item["bought"], item["count"]
        if not isinstance(bought, str) or catalogues is None or bought not in catalogues.parts:
            errors.append("%s names %r, which is no Bought Part of the catalogue" % (where, bought))
        elif bought in seen:
            errors.append("%s names %s twice: give one count" % (where, bought))
        elif bought in circuit:
            errors.append("%s names %s, which the electrical section already counts" % (where, bought))
        seen.add(bought)
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_COUNT:
            errors.append("%s.count must be 1 to %d pieces per toy" % (where, MAX_COUNT))
    if isinstance(tree, Mapping) and parts:
        _check_against_tree(tree, parts, circuit, catalogues, errors)
    if "pcba" in value:
        board = value["pcba"]
        if not isinstance((electrical or {}).get("pcba"), dict):
            errors.append("%s.pcba prices a factory-assembled board the electrical section does not name"
                          % label)
        elif not isinstance(board, dict) or set(board) != {"unit_price_cents", "estimate", "source"}:
            errors.append("%s.pcba must be exactly {unit_price_cents, estimate, source}" % label)
        else:
            price = board["unit_price_cents"]
            if isinstance(price, bool) or not isinstance(price, int) or not 0 < price <= MAX_UNIT_PRICE_CENTS:
                errors.append("%s.pcba.unit_price_cents must be what one board costs, 1 to %d US cents"
                              % (label, MAX_UNIT_PRICE_CENTS))
            if not isinstance(board["estimate"], bool):
                errors.append("%s.pcba.estimate must be true or false" % label)
            source = board["source"]
            if not isinstance(source, str) or not source.strip() or len(source) > MAX_SOURCE_CHARS:
                errors.append("%s.pcba.source must say who gave the price, at most %d characters"
                              % (label, MAX_SOURCE_CHARS))
    if len(errors) != before:
        return None
    return ContractBought(section=value)


def _check_against_tree(
    tree: Mapping[str, Any], parts: List[Any], circuit: set, catalogues: Optional[Catalogues],
    errors: List[str],
) -> None:
    """A kit's block agrees with its Assembly Tree (ADR 0104)."""

    listed = {
        item["bought"]: item["count"]
        for item in parts
        if isinstance(item, dict) and isinstance(item.get("bought"), str)
        and isinstance(item.get("count"), int) and not isinstance(item.get("count"), bool)
    }
    totals = bought_totals(tree)
    for bought, need in sorted(totals.items()):
        if bought in circuit:
            continue
        have = listed.get(bought)
        if have is None:
            errors.append(
                "bought-parts: the Assembly Tree's Bought Parts hold %d x %s, which the block "
                "does not list: a kit ships them, so list them with their count" % (need, bought)
            )
        elif have < need:
            errors.append(
                "bought-parts lists %d x %s, but the Assembly Tree holds %d: list at least the "
                "tree's count (more are spares)" % (have, bought, need)
            )
    materials = {name for name in tree.get("materials") or () if isinstance(name, str)}
    for bought in sorted(set(listed) - set(totals) - circuit):
        entry = catalogues.parts.get(bought) if catalogues is not None else None
        if entry is None:
            continue
        if bought not in materials and not entry.packaging:
            errors.append(
                "bought-parts lists %s, which the Assembly Tree neither holds as a Bought Part nor "
                "names in its materials: a kit ships only what its Manual lists" % bought
            )


def bought_list_ids(section: Mapping[str, Any]) -> List[str]:
    """The catalogue ids a validated block names."""

    return [item["bought"] for item in section.get("parts") or ()]


__all__ = [
    "BOUGHT_FENCE_OPEN",
    "ContractBought",
    "bought_list_ids",
    "parse_bought_block",
    "strip_bought_block",
]
