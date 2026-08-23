"""Compatibility wrapper for Eve's pre-Workshop launch vocabulary.

Canonical code imports :mod:`eve.send` and uses ``send_design`` or
``send_to_shop``. These aliases keep existing extensions readable while all
effects still pass through the same Workshop Sender and Clockwork state.
"""

from .send import (
    full_writeup,
    insert_card,
    render_card,
    send_design,
    send_to_shop,
    shop_description,
    stage_catalog,
)

launch_design = send_design
launch_to_portal = send_to_shop
portal_description = shop_description

__all__ = [
    "full_writeup",
    "insert_card",
    "launch_design",
    "launch_to_portal",
    "portal_description",
    "render_card",
    "stage_catalog",
]
