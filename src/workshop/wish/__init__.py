"""Wish intake contracts and identifiers."""

from workshop.wish.contracts import (
    WISH_REFERENCES_DIRECTORY,
    Wish,
    WishReference,
    generate_wish_id,
)
from workshop.wish.design_contract import DesignContract, parse_design_contract
from workshop.wish.references import (
    LoadedWishReference,
    is_reference_url,
    load_wish_references,
    wish_reference_files,
    wish_reference_sources,
)

__all__ = [
    "WISH_REFERENCES_DIRECTORY",
    "DesignContract",
    "LoadedWishReference",
    "Wish",
    "WishReference",
    "generate_wish_id",
    "is_reference_url",
    "load_wish_references",
    "parse_design_contract",
    "wish_reference_files",
    "wish_reference_sources",
]
