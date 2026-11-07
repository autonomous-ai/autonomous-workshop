"""The sealed Bought Parts a Workshop Release bills as Factory
``extra_materials`` (ADR 0095 amendment, 2026-11-07).

Factory prices a design by the filament it weighs plus its extra materials,
so the bought hardware a buyer gets must cross as extras, or the listing
leaves its cost out. A Workshop run reads them from what its Wish sealed,
never from the model's bodies: the contract's electrical section (every
carried part, by count), its optional Bought Parts block (pins, springs,
glue and anything else the circuit does not name), and the
factory-assembled board, priced by that block. The prices are the sealed
catalogue snapshot's ``unit_prices``; the board's is the contract's.

A part without a price refuses the publication; nothing is estimated here.
A run whose Wish sealed no Bought Parts block and draws no bought models
bills nothing, as before.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Mapping, Optional

from workshop.errors import ContractError
from workshop.make.bought_model import draws_bought_parts
from workshop.wish.electrical import pcba_parts

PCBA_PART = "pcba"
PCBA_NAME = "Factory-assembled circuit board (PCBA)"


def sealed_bought_lines(
    contract: Optional[Mapping[str, Any]], catalogue: Optional[Mapping[str, Any]]
) -> Optional[list[dict[str, Any]]]:
    """Every Bought Part the sealed contract lists, one line per catalogue
    entry, or None when this run bills none. A line's ``unit_price_cents``
    is None when nothing sealed prices it; ``factory_extra_materials``
    refuses such a line."""

    if not isinstance(contract, Mapping):
        return None
    block = contract.get("bought_parts")
    if not isinstance(block, Mapping):
        block = None
    if block is None and not draws_bought_parts(contract, catalogue):
        return None
    catalogue = catalogue if isinstance(catalogue, Mapping) else {}
    entries = catalogue.get("bought_parts") if isinstance(catalogue.get("bought_parts"), Mapping) else {}
    prices = catalogue.get("unit_prices") if isinstance(catalogue.get("unit_prices"), Mapping) else {}
    counts: "OrderedDict[str, int]" = OrderedDict()
    electrical = contract.get("electrical") if isinstance(contract.get("electrical"), Mapping) else None
    for item in (electrical or {}).get("parts") or ():
        if not isinstance(item, Mapping) or item.get("external") is True or "bought" not in item:
            continue
        counts[item["bought"]] = counts.get(item["bought"], 0) + int(item.get("count", 1))
    for item in (block or {}).get("parts") or ():
        counts[item["bought"]] = counts.get(item["bought"], 0) + int(item["count"])
    lines = []
    for part, count in counts.items():
        entry = entries.get(part) if isinstance(entries.get(part), Mapping) else {}
        price = prices.get(part)
        lines.append({
            "part": part,
            "name": entry.get("name") or part,
            "count": count,
            "unit_price_cents": price if type(price) is int and price > 0 else None,
            "price_source": "catalogue",
        })
    if electrical is not None and pcba_parts(electrical):
        board = (block or {}).get("pcba") if isinstance((block or {}).get("pcba"), Mapping) else {}
        price = board.get("unit_price_cents")
        line = {
            "part": PCBA_PART,
            "name": PCBA_NAME,
            "count": 1,
            "unit_price_cents": price if type(price) is int and price > 0 else None,
            "price_source": "contract",
        }
        if board:
            line["estimate"] = board.get("estimate") is True
            line["source"] = board.get("source")
        lines.append(line)
    return lines


def factory_extra_materials(lines: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """``lines`` as the ``bought_hardware`` the Factory adapter prices, or
    refuse naming every part nothing sealed prices."""

    missing = sorted(line["part"] for line in lines if line.get("unit_price_cents") is None)
    if missing:
        raise ContractError(
            "these Bought Parts have no sealed price, and Release will not publish their cost as "
            "zero: %s. Prices are sealed only with the contract's bought-parts block: add it "
            "(its parts, and pcba.unit_price_cents for a factory-assembled board), record "
            "unit_price_cents in the bought-parts catalogue for any part that lacks one, and "
            "re-seal the Wish" % ", ".join(missing)
        )
    return [dict(line) for line in lines]


__all__ = ["PCBA_NAME", "PCBA_PART", "factory_extra_materials", "sealed_bought_lines"]
