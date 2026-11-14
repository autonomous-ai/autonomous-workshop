"""The sealed Bought Parts a Workshop Release bills as Factory
``extra_materials`` (ADR 0095 amendment, 2026-11-07).

Factory prices a design by the filament it weighs plus its extra materials,
so the bought hardware a buyer gets must cross as extras, or the listing
leaves its cost out. A Workshop run reads them from what its Wish sealed,
never from the model's bodies: the contract's electrical section (every
carried part, by count), its optional Bought Parts block (pins, springs,
glue and anything else the circuit does not name), and the
factory-assembled board, priced by that block. The prices are the sealed
catalogue snapshot's ``unit_prices``; the board's is the contract's. A
priced board includes the parts mounted on it (``electrical.pcba.parts``),
so those are not billed again; only the board is.

A kit (ADR 0104) bills from the same block, which its parser holds equal to
or above the Assembly Tree's Bought Parts. A kit whose tree holds Bought
Parts but whose Wish sealed no block bills them unpriced, by the tree's
count, so its publication is refused rather than leaving their cost out.

A part without a price refuses the publication; nothing is estimated here.
A run whose Wish sealed no Bought Parts block and draws no bought models
bills nothing, as before.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Mapping, Optional

from workshop.errors import ContractError
from workshop.make.bought_model import draws_bought_parts
from workshop.wish.assembly_tree import bought_totals
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
    tree = contract.get("assembly_tree") if isinstance(contract.get("assembly_tree"), Mapping) else None
    tree_only = bought_totals(tree) if block is None and tree is not None else {}
    if block is None and not tree_only and not draws_bought_parts(contract, catalogue):
        return None
    catalogue = catalogue if isinstance(catalogue, Mapping) else {}
    entries = catalogue.get("bought_parts") if isinstance(catalogue.get("bought_parts"), Mapping) else {}
    prices = catalogue.get("unit_prices") if isinstance(catalogue.get("unit_prices"), Mapping) else {}
    counts: "OrderedDict[str, int]" = OrderedDict()
    electrical = contract.get("electrical") if isinstance(contract.get("electrical"), Mapping) else None
    board = (block or {}).get("pcba") if isinstance((block or {}).get("pcba"), Mapping) else {}
    board_price = board.get("unit_price_cents")
    board_priced = type(board_price) is int and board_price > 0
    # A priced board arrives assembled, its parts included (owner,
    # 2026-11-08): the parts the electrical section places on it, by their
    # part ids in pcba.parts, are not billed again. An unpriced board bills
    # them as before and refuses for its own missing price.
    on_board = set(pcba_parts(electrical)) if electrical is not None and board_priced else set()
    for item in (electrical or {}).get("parts") or ():
        if not isinstance(item, Mapping) or item.get("external") is True or "bought" not in item:
            continue
        if item.get("id") in on_board:
            continue
        counts[item["bought"]] = counts.get(item["bought"], 0) + int(item.get("count", 1))
    for item in (block or {}).get("parts") or ():
        counts[item["bought"]] = counts.get(item["bought"], 0) + int(item["count"])
    circuit = set(counts)
    for part, count in tree_only.items():
        # No block sealed a price for these: they bill unpriced and refuse.
        if part not in circuit:
            counts[part] = counts.get(part, 0) + count
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
        line = {
            "part": PCBA_PART,
            "name": PCBA_NAME,
            "count": 1,
            "unit_price_cents": board_price if board_priced else None,
            "price_source": "contract",
        }
        if board:
            line["estimate"] = board.get("estimate") is True
            line["source"] = board.get("source")
        if on_board:
            line["includes"] = sorted(on_board)
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
