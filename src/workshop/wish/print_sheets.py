"""A schema 6 Design Contract's Print Sheets section (ADR 0091).

The ``print`` section declares what the maker prints on A4 sheets and ships
in the box: the stocks it prints on, the sealed art files, and every Print
Piece cut from them, each applied to one Unique Geometry in one of six ways.
The contract's sizes are the truth; Make's gate later measures the B-rep
against them and lays the pieces out. Parsing here checks only what the
contract itself states, and like the rest of the contract it collects every
failure instead of stopping at the first.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

STOCKS = ("paper", "sticker", "card", "film")
# Which stocks each way of applying a piece may be cut from.
WAY_STOCKS: Mapping[str, Tuple[str, ...]] = {
    "flat": ("paper", "film"),
    "sticker": ("sticker",),
    "wrap": ("paper",),
    "sphere": ("paper",),
    "fold": ("paper",),
    "stand": ("card",),
}
WAYS = tuple(WAY_STOCKS)
OUTLINES = ("rect", "oval")
WRAP_AROUND = ("cover", "band")
CC0_LICENCE = "CC0-1.0"
# The buyer cuts with scissors (ADR 0091 decision 5).
MIN_CUT_EDGE_MM = 5.0
MIN_SPHERE_DIAMETER_MM = 25.0
GORES_RANGE = (8, 24)
FOLD_PAGES_RANGE = (2, 32)
CALIPER_RANGE_MM = (0.03, 1.0)
MAX_PIECE_COUNT = 99
MAX_PIECES = 999
MAX_ART_SHOWS_CHARS = 500
MAX_WHERE_CHARS = 300
MAX_STOCK_NAME_CHARS = 120
MAX_SOURCE_CHARS = 500

PRINT_ART_FILE = re.compile(
    r"^print-(?:0[1-9]|[1-9][0-9]{1,2})-[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\.(?:png|jpg|webp)$"
)
_PIECE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Schema 7 (ADR 0092): a Print Piece is a Part, with a code and a mnemonic,
# M01-<slug> or N01-<slug>.
_TREE_PIECE_ID = re.compile(r"^[MN][0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
_HOST = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)(?:#([0-9]+))?$")
_URL = re.compile(r"^https?://\S+$")

_COMMON_FIELDS = frozenset(("id", "art", "stock", "way", "on", "where", "count"))
_WAY_FIELDS: Mapping[str, frozenset] = {
    "flat": frozenset(("size_mm", "outline")),
    "sticker": frozenset(("size_mm", "outline")),
    "stand": frozenset(("size_mm", "outline", "slot_mm")),
    "wrap": frozenset(("block_mm", "around")),
    "sphere": frozenset(("diameter_mm", "gores")),
    "fold": frozenset(("page_mm", "pages")),
}


@dataclass(frozen=True)
class ContractPrint:
    """The validated ``print`` section, kept as the exact JSON the contract
    sealed so Make's tools read the same values the owner approved."""

    section: Dict[str, Any]

    @property
    def art_files(self) -> Tuple[str, ...]:
        return tuple(item["file"] for item in self.section["art"])

    @property
    def pieces(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(self.section["pieces"])

    def to_dict(self) -> Dict[str, Any]:
        return self.section


def _number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


def _positive_numbers(value: Any, length: int) -> bool:
    return (
        isinstance(value, list) and len(value) == length
        and all(_number(item) and item > 0 for item in value)
    )


def _text(value: Any, limit: int) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def _integer(value: Any, low: int, high: int) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and low <= value <= high


def _parse_stocks(value: Any, errors: List[str]) -> Dict[str, Any]:
    if not isinstance(value, dict) or not value:
        errors.append("print.stocks must name at least one stock: %s" % ", ".join(STOCKS))
        return {}
    stocks: Dict[str, Any] = {}
    for key, item in value.items():
        label = "print.stocks.%s" % key
        if key not in STOCKS:
            errors.append("%s is not a stock; use %s" % (label, ", ".join(STOCKS)))
            continue
        if not isinstance(item, dict) or set(item) != {"name", "caliper_mm"}:
            errors.append("%s must be exactly {name, caliper_mm}" % label)
            continue
        valid = True
        if not _text(item["name"], MAX_STOCK_NAME_CHARS):
            errors.append("%s.name must name the stock in at most %d characters"
                          % (label, MAX_STOCK_NAME_CHARS))
            valid = False
        caliper = item["caliper_mm"]
        if not _number(caliper) or not CALIPER_RANGE_MM[0] <= caliper <= CALIPER_RANGE_MM[1]:
            errors.append("%s.caliper_mm must be a thickness from %g to %g mm"
                          % (label, CALIPER_RANGE_MM[0], CALIPER_RANGE_MM[1]))
            valid = False
        if valid:
            stocks[key] = item
    return stocks


def _parse_art(value: Any, errors: List[str]) -> List[str]:
    if not isinstance(value, list) or not value:
        errors.append("print.art must be a non-empty list")
        return []
    files: List[str] = []
    for index, item in enumerate(value):
        label = "print.art[%d]" % index
        if not isinstance(item, dict):
            errors.append("%s must be an object" % label)
            continue
        unknown = sorted(set(item) - {"file", "shows", "source", "licence"})
        if unknown:
            errors.append("%s has unknown field(s): %s" % (label, ", ".join(unknown)))
        file_name = item.get("file")
        if not isinstance(file_name, str) or PRINT_ART_FILE.fullmatch(file_name) is None:
            errors.append("%s.file must look like print-NN-<slug>.png, .jpg, or .webp" % label)
        elif int(file_name.split("-")[1]) != index + 1:
            errors.append("%s.file must be numbered print-%02d" % (label, index + 1))
        else:
            files.append(file_name)
        if not _text(item.get("shows"), MAX_ART_SHOWS_CHARS):
            errors.append("%s.shows must say in at most %d characters what the art is"
                          % (label, MAX_ART_SHOWS_CHARS))
        # Stock art is CC0 only, with its source recorded (ADR 0091
        # decision 4); art drawn for the toy has neither field.
        if ("source" in item) != ("licence" in item):
            errors.append("%s needs both source and licence, or neither" % label)
        if "source" in item and (
            not isinstance(item["source"], str) or len(item["source"]) > MAX_SOURCE_CHARS
            or _URL.fullmatch(item["source"]) is None
        ):
            errors.append("%s.source must be the http(s) link the art came from" % label)
        if "licence" in item and item["licence"] != CC0_LICENCE:
            errors.append("%s.licence must be %s: stock art is CC0 only" % (label, CC0_LICENCE))
    return files


def _check_host(entry: Any, counts: Mapping[str, int], label: str, errors: List[str]) -> None:
    match = _HOST.fullmatch(entry) if isinstance(entry, str) else None
    if match is None:
        errors.append("%s.on must name a Unique Geometry, or one instance <id>#<n>" % label)
        return
    geometry, number = match.group(1), match.group(2)
    if geometry not in counts:
        errors.append("%s.on names a Unique Geometry that does not exist: %r" % (label, entry))
    elif number is not None and (
        counts[geometry] < 2 or number != str(int(number)) or not 1 <= int(number) <= counts[geometry]
    ):
        errors.append("%s.on names instance %r; %r has %d" % (label, entry, geometry, counts[geometry]))


def _check_way(item: Mapping[str, Any], way: str, label: str, errors: List[str]) -> None:
    """The sizes one way of applying a piece declares, and the scissors
    rules the contract alone can check."""

    if way in ("flat", "sticker", "stand"):
        size = item.get("size_mm")
        if not _positive_numbers(size, 2):
            errors.append("%s.size_mm must be [width, height] in mm" % label)
        elif min(size) < MIN_CUT_EDGE_MM:
            errors.append("%s.size_mm has an edge under %g mm, too small to cut with scissors"
                          % (label, MIN_CUT_EDGE_MM))
        if "outline" in item and item["outline"] not in OUTLINES:
            errors.append("%s.outline must be %s" % (label, " or ".join(OUTLINES)))
        if way == "stand":
            slot = item.get("slot_mm")
            if not _number(slot) or slot <= 0:
                errors.append("%s.slot_mm must be the slot's length in mm" % label)
            elif _positive_numbers(size, 2) and slot > size[0]:
                errors.append("%s.slot_mm is longer than the card is wide" % label)
    elif way == "wrap":
        block = item.get("block_mm")
        if not _positive_numbers(block, 3):
            errors.append("%s.block_mm must be [height, width, depth] in mm" % label)
        elif block[0] < MIN_CUT_EDGE_MM:
            errors.append("%s.block_mm height is under %g mm, too small to cut with scissors"
                          % (label, MIN_CUT_EDGE_MM))
        if item.get("around") not in WRAP_AROUND:
            errors.append("%s.around must be cover (front, spine, back) or band (all four sides)"
                          % label)
    elif way == "sphere":
        diameter = item.get("diameter_mm")
        if not _number(diameter) or diameter < MIN_SPHERE_DIAMETER_MM:
            errors.append("%s.diameter_mm must be at least %g mm" % (label, MIN_SPHERE_DIAMETER_MM))
        if not _integer(item.get("gores"), *GORES_RANGE):
            errors.append("%s.gores must be a whole number from %d to %d" % ((label,) + GORES_RANGE))
    elif way == "fold":
        page = item.get("page_mm")
        if not _positive_numbers(page, 2):
            errors.append("%s.page_mm must be [width, height] in mm" % label)
        elif min(page) < MIN_CUT_EDGE_MM:
            errors.append("%s.page_mm has an edge under %g mm, too small to cut with scissors"
                          % (label, MIN_CUT_EDGE_MM))
        if not _integer(item.get("pages"), *FOLD_PAGES_RANGE):
            errors.append("%s.pages must be a whole number from %d to %d"
                          % ((label,) + FOLD_PAGES_RANGE))


def _parse_pieces(
    value: Any, stocks: Mapping[str, Any], art: List[str], counts: Mapping[str, int],
    errors: List[str], tree: bool = False,
) -> Tuple[set, set]:
    """Check every piece; return the stocks and art files the pieces use.

    With ``tree`` (schema 7), each id is a Part id, ``M01-<slug>``, and the
    Assembly Tree checks what ``on`` names."""

    used_stocks: set = set()
    used_art: set = set()
    if not isinstance(value, list) or not value or len(value) > MAX_PIECES:
        errors.append("print.pieces must be a list of 1 to %d pieces" % MAX_PIECES)
        return used_stocks, used_art
    seen: set = set()
    for index, item in enumerate(value):
        label = "print.pieces[%d]" % index
        if not isinstance(item, dict):
            errors.append("%s must be an object" % label)
            continue
        identifier = item.get("id")
        pattern = _TREE_PIECE_ID if tree else _PIECE_ID
        if not isinstance(identifier, str) or pattern.fullmatch(identifier) is None:
            errors.append(
                "%s.id must look like M01-<kebab-case mnemonic> or N01-<...> (schema_version 7)"
                % label if tree else "%s.id must be lowercase kebab case" % label
            )
        elif identifier in seen:
            errors.append("%s.id repeats an earlier piece id: %r" % (label, identifier))
        else:
            seen.add(identifier)
        way = item.get("way")
        if way not in WAY_STOCKS:
            errors.append("%s.way must be one of %s" % (label, ", ".join(WAYS)))
        else:
            unknown = sorted(set(item) - _COMMON_FIELDS - _WAY_FIELDS[way])
            if unknown:
                errors.append("%s: a %s piece does not take %s" % (label, way, ", ".join(unknown)))
            _check_way(item, way, label, errors)
        stock = item.get("stock")
        if stock not in stocks:
            errors.append("%s.stock must be a stock print.stocks declares" % label)
        else:
            used_stocks.add(stock)
            if way in WAY_STOCKS and stock not in WAY_STOCKS[way]:
                errors.append("%s: a %s piece is cut from %s, not %s"
                              % (label, way, " or ".join(WAY_STOCKS[way]), stock))
        piece_art = item.get("art")
        if piece_art not in art:
            errors.append("%s.art must be a file print.art lists" % label)
        else:
            used_art.add(piece_art)
        if not tree:
            _check_host(item.get("on"), counts, label, errors)
        if not _text(item.get("where"), MAX_WHERE_CHARS):
            errors.append("%s.where must say in at most %d characters which face, block, sphere or "
                          "slot it lands on" % (label, MAX_WHERE_CHARS))
        if "count" in item and not _integer(item["count"], 1, MAX_PIECE_COUNT):
            errors.append("%s.count must be a whole number from 1 to %d" % (label, MAX_PIECE_COUNT))
    return used_stocks, used_art


def parse_print_section(
    value: Any, counts: Mapping[str, int], errors: List[str], tree: bool = False
) -> Optional[ContractPrint]:
    """Schema 6's ``print`` section, or None after appending every failure.

    ``counts`` maps each Unique Geometry id to its count, so a piece may
    land on one instance, ``<id>#<n>``, as an Interface may. With ``tree``
    (schema 7, ADR 0092) a piece's id is ``M01-<slug>`` and its ``on`` names
    a printed Part, Bought Part or Sub-assembly, which the Assembly Tree's
    parser checks instead.
    """

    if not isinstance(value, dict):
        errors.append("print must be an object with stocks, art and pieces (schema_version 6 or 7)")
        return None
    before = len(errors)
    unknown = sorted(set(value) - {"stocks", "art", "pieces"})
    if unknown:
        errors.append("print has unknown field(s): %s" % ", ".join(unknown))
    stocks = _parse_stocks(value.get("stocks"), errors)
    art = _parse_art(value.get("art"), errors)
    used_stocks, used_art = _parse_pieces(value.get("pieces"), stocks, art, counts, errors, tree)
    for key in sorted(set(stocks) - used_stocks):
        errors.append("print.stocks.%s is declared but no piece is cut from it" % key)
    for file_name in art:
        if file_name not in used_art:
            errors.append("print.art %s is used by no piece" % file_name)
    if len(errors) != before:
        return None
    return ContractPrint(section=value)


__all__ = [
    "CC0_LICENCE",
    "ContractPrint",
    "PRINT_ART_FILE",
    "STOCKS",
    "WAYS",
    "WAY_STOCKS",
    "parse_print_section",
]
