"""Inputs and outputs owned by the Invent stage."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping

from workshop._validation import bounded_text, copy_json_mapping, require_sha256
from workshop.contributors import Taste
from workshop.errors import ContractError
from workshop.product import PLAYTHING_LANES, ToyBlueprint
from workshop.wish import Wish


@dataclass(frozen=True)
class InventContext:
    """Exact inputs for concept exploration and industrial design."""

    wish: Wish
    taste: Taste
    blueprint: ToyBlueprint
    workspace: Path

    def __post_init__(self) -> None:
        if not isinstance(self.wish, Wish) or not isinstance(self.taste, Taste):
            raise ContractError("InventContext requires a Wish and Taste")
        if not isinstance(self.blueprint, ToyBlueprint):
            raise ContractError("InventContext requires a ToyBlueprint")
        root = Path(self.workspace)
        if not root.is_absolute():
            raise ContractError("InventContext workspace must be absolute")
        object.__setattr__(self, "workspace", root)
        self.wish.assert_valid()
        self.taste.assert_current()


@dataclass(frozen=True)
class Invented:
    """One chosen industrial-design concept that reached its reward target."""

    wish_sha256: str
    taste_sha256: str
    lane: str
    concept: Mapping[str, Any]
    score: int
    target_score: int
    concept_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        require_sha256(self.wish_sha256, "Invented Wish sha256")
        require_sha256(self.taste_sha256, "Invented Taste sha256")
        if self.lane not in PLAYTHING_LANES:
            raise ContractError("Invented lane must be a Workshop plaything lane")
        concept = copy_json_mapping(self.concept, "Invented concept", nonempty=True)
        for key in ("title", "summary"):
            bounded_text(concept.get(key), "Invented concept %s" % key, 2_000)
        if type(self.score) is not int or not 0 <= self.score <= 100:
            raise ContractError("Invented score must be an integer from 0 to 100")
        if type(self.target_score) is not int or not 1 <= self.target_score <= 100:
            raise ContractError(
                "Invented target_score must be an integer from 1 to 100"
            )
        object.__setattr__(self, "concept", concept)
        encoded = json.dumps(
            concept,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        object.__setattr__(self, "concept_sha256", hashlib.sha256(encoded).hexdigest())

    @property
    def passed(self) -> bool:
        return self.score >= self.target_score

    def assert_context(self, context: InventContext) -> None:
        if not isinstance(context, InventContext):
            raise ContractError("Invented requires an InventContext")
        wish_sha256 = hashlib.sha256(
            json.dumps(
                context.wish.to_dict(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        if (
            self.wish_sha256 != wish_sha256
            or self.taste_sha256 != context.taste.sha256
            or self.lane != context.blueprint.lane
        ):
            raise ContractError("Invented concept belongs to different Workshop inputs")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wish_sha256": self.wish_sha256,
            "taste_sha256": self.taste_sha256,
            "lane": self.lane,
            "concept": dict(self.concept),
            "concept_sha256": self.concept_sha256,
            "score": self.score,
            "target_score": self.target_score,
            "passed": self.passed,
        }


__all__ = ["InventContext", "Invented"]
