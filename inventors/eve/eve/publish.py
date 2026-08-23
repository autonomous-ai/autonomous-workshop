"""Compatibility wrapper for Eve's historical publication module."""

from .send import (
    full_writeup,
    insert_card,
    render_card,
    send_design,
    send_to_shop,
    shop_description,
    stage_catalog,
)

import_design = send_design
publish_to_store = send_to_shop
panda_description = shop_description

__all__ = [
    "full_writeup",
    "import_design",
    "insert_card",
    "panda_description",
    "publish_to_store",
    "render_card",
    "stage_catalog",
]
