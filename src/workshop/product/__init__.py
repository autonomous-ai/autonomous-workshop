"""Open-ended product checks and customer-facing attribution."""

from workshop.product.attribution import attribute_product_description
from workshop.product.blueprints import (
    BASELINE_PLAYTEST_CHECKS,
    ToyBlueprint,
)

__all__ = [
    "BASELINE_PLAYTEST_CHECKS",
    "ToyBlueprint",
    "attribute_product_description",
]
