"""Compatibility import for Workshop 0.3's Inspect vocabulary."""

from .models import InspectionResult
from .playtest import Playtest


# A true alias keeps isinstance checks and old custom workflows lossless.
Inspection = Playtest

__all__ = ["Inspection", "InspectionResult"]
