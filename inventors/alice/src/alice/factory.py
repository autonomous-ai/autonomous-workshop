"""Compatibility imports for Alice's pre-Workshop Shop Door names.

New code imports :mod:`alice.shop_door`.
"""

from .shop_door import (
    AmbiguousShopDoorEffect as AmbiguousFactoryEffect,
    ShopDoorClient as FactoryClient,
    ShopDoorError as FactoryError,
    ShopDraftStamp as FactoryDraftReceipt,
    ShopSendStamp as FactoryPublishReceipt,
)

__all__ = [
    "AmbiguousFactoryEffect",
    "FactoryClient",
    "FactoryDraftReceipt",
    "FactoryError",
    "FactoryPublishReceipt",
]
