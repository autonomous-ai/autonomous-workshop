"""Compatibility import for Workshop 0.3's Inspect vocabulary."""

from workshop.playtest.evidence import InspectionResult
from workshop.playtest.service import Playtest


# A true alias keeps isinstance checks and old custom workflows lossless.
Inspection = Playtest

__all__ = ["Inspection", "InspectionResult"]
