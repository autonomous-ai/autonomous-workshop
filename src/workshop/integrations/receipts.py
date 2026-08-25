"""Compatibility imports for runtime-owned external-effect contracts.

New code imports these contracts from :mod:`workshop.runtime`. This module
remains as a source-compatible bridge for Workshop 0.5 and older callers.
"""

from workshop.runtime.contracts import (
    PublicationOutcome,
    PublicationReceipt,
    Receipt,
    SendResult,
    Stamp,
)

__all__ = [
    "PublicationOutcome",
    "PublicationReceipt",
    "Receipt",
    "SendResult",
    "Stamp",
]
