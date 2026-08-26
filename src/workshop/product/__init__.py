"""Stable product-lane bindings and customer-facing attribution."""

from workshop.product.attribution import attribute_product_description
from workshop.product.blueprints import (
    PLAYTHING_LANES,
    ToyBlueprint,
)

__all__ = [
    "PLAYTHING_LANES",
    "ToyBlueprint",
    "attribute_product_description",
]
