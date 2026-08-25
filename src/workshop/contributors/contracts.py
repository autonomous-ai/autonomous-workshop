"""Public policy shared by inventor contributors and Workshop applications."""

from __future__ import annotations

from typing import Tuple


CUSTOMIZATION_LEVELS: Tuple[str, ...] = (
    "taste-only",
    "custom-make",
    "custom-playtest",
)
ROUTABLE_INVENTOR_STATUSES = frozenset(("active", "experimental"))


__all__ = ["CUSTOMIZATION_LEVELS", "ROUTABLE_INVENTOR_STATUSES"]
