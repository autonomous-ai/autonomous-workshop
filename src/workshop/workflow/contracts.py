"""Run-level state contract owned by the canonical workflow engine."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence

from workshop._validation import bounded_text, require_sha256
from workshop.deliver.contracts import Delivered
from workshop.errors import ContractError
from workshop.invent.contracts import Invented
from workshop.outcomes import Need
from workshop.product import WORKSHOP_JOBS


_RUN_STATUSES = frozenset(("working", "waiting", "ready", "delivered", "stopped"))


@dataclass(frozen=True)
class WorkshopRun:
    product_id: str
    status: str
    job: str
    round: int
    artifact_sha256: Optional[str] = None
    instructions_sha256: Optional[str] = None
    needs: Sequence[Need] = field(default_factory=tuple)
    delivery: Optional[Delivered] = None
    playtest_rounds: int = 1
    page_url: Optional[str] = None
    invented: Optional[Invented] = None

    def __post_init__(self) -> None:
        bounded_text(self.product_id, "WorkshopRun product_id", 256)
        if self.status not in _RUN_STATUSES:
            raise ContractError("WorkshopRun status is invalid")
        if self.job not in WORKSHOP_JOBS:
            raise ContractError("WorkshopRun job is invalid")
        if type(self.round) is not int or self.round < 0:
            raise ContractError("WorkshopRun round must be a non-negative integer")
        if (
            type(self.playtest_rounds) is not int
            or not 1 <= self.playtest_rounds <= 100
            or self.round > self.playtest_rounds
        ):
            raise ContractError(
                "WorkshopRun playtest_rounds must cover this round and be from 1 to 100"
            )
        if self.artifact_sha256 is not None:
            require_sha256(self.artifact_sha256, "WorkshopRun artifact sha256")
        if self.instructions_sha256 is not None:
            require_sha256(
                self.instructions_sha256, "WorkshopRun instructions sha256"
            )
        if self.page_url is not None:
            try:
                parsed_page_url = urllib.parse.urlsplit(self.page_url)
            except ValueError as exc:
                raise ContractError(
                    "WorkshopRun page_url must be a valid HTTPS URL"
                ) from exc
            if parsed_page_url.scheme != "https" or not parsed_page_url.hostname:
                raise ContractError("WorkshopRun page_url must be a valid HTTPS URL")
        if self.invented is not None and not isinstance(self.invented, Invented):
            raise ContractError("WorkshopRun invented must use an Invented record")
        needs = tuple(self.needs)
        if not all(isinstance(item, Need) for item in needs):
            raise ContractError("WorkshopRun needs must use Need records")
        object.__setattr__(self, "needs", needs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "status": self.status,
            "job": self.job,
            "round": self.round,
            "playtest_rounds": self.playtest_rounds,
            "artifact_sha256": self.artifact_sha256,
            "instructions_sha256": self.instructions_sha256,
            "page_url": self.page_url,
            "invented": self.invented.to_dict() if self.invented is not None else None,
            "needs": [item.to_dict() for item in self.needs],
            "delivery": self.delivery.to_dict() if self.delivery is not None else None,
        }


__all__ = ["WorkshopRun"]
