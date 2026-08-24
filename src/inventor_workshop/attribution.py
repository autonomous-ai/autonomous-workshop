"""Canonical inventor credit for customer-facing product descriptions."""

from __future__ import annotations

from typing import Any

from .errors import ContractError


def _inventor_name(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.strip()) > 200
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError(
            "product description inventor name must be one control-free line of at most 200 characters"
        )
    return value.strip()


def attribute_product_description(description: Any, inventor_name: Any) -> str:
    """End product copy with exactly one canonical inventor credit.

    Existing copy is preserved.  Only trailing whitespace and exact terminal
    ``By {Inventor}.`` credits are replaced, making the operation idempotent
    across Instructions, listing, and delivery boundaries.
    """

    if not isinstance(description, str) or not description.strip():
        raise ContractError("product description must be non-empty text")
    inventor = _inventor_name(inventor_name)
    credit = "By %s." % inventor
    body = description.rstrip()
    while body.endswith(credit):
        body = body[: -len(credit)].rstrip()
    if not body:
        raise ContractError("product description must contain copy before its inventor credit")
    return "%s\n\n%s" % (body, credit)


__all__ = ["attribute_product_description"]
