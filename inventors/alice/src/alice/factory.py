"""Read-only compatibility imports for Alice's pre-Workshop Shop names.

New code imports :mod:`alice.shop_door`. ``FactoryClient.create_draft`` is a
fail-closed compatibility method; only shared Workshop may import a model.
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
