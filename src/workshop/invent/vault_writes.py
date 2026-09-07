"""Shapes shared by every stage that writes back to the game vault.

Playtest (:mod:`workshop.playtest.vault_evidence`) and Make
(:mod:`workshop.make.vault_lessons`) both bank evidence rows and the product's
own ``games/<product_id>`` page. The provenance weighting and the page shape
live here, beside the vault model, so neither stage component imports the
other.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

PROVENANCE_WEIGHTS = (
    ("physical", 4),
    ("deterministic", 3),
    ("codex", 2),
    ("agent", 2),
)
DEFAULT_WEIGHT = 1
SEVERITY_TO_VAULT = {"block": "high", "improve": "medium"}
MAX_DESIGN_LESSONS = 3


def provenance_weight(evidence_class: Optional[str]) -> int:
    """How much a row is worth: measurements outrank model assessments."""

    lowered = (evidence_class or "").casefold()
    for prefix, weight in PROVENANCE_WEIGHTS:
        if lowered.startswith(prefix):
            return weight
    return DEFAULT_WEIGHT


def gamevault_design(
    product_id: str,
    round_index: int,
    *,
    concept: Mapping[str, Any],
    mechanisms: Sequence[str],
    verdict: str,
    scores: Optional[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """The product's own ``games/<product_id>`` page, in the vault API's shape.

    Every wish leaves a game node behind: ``uses`` the mechanisms the vault
    resolved from the sealed concept, ``exhibits`` the anti-patterns the stage
    confirmed, and carries the round's verdict, scores when the stage measured
    any, and up to three confirmed findings as lessons.  ``rows`` are the
    vault-shaped rows the same stage produced for the same round.
    """

    title = concept.get("title")
    summary = concept.get("summary")
    return {
        "slug": product_id,
        "name": " ".join(str(title).split())[:120] if isinstance(title, str) and title.strip() else product_id,
        "summary": " ".join(str(summary).split())[:900] if isinstance(summary, str) else "",
        "mechanisms": sorted({str(item) for item in mechanisms}),
        "exhibits": sorted({str(row["symptom"]) for row in rows}),
        "round": round_index,
        "verdict": str(verdict),
        "scores": {
            str(key): value
            for key, value in (scores or {}).items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        },
        "lessons": [str(row["claim"])[:220] for row in rows[:MAX_DESIGN_LESSONS]],
    }


__all__ = [
    "DEFAULT_WEIGHT",
    "MAX_DESIGN_LESSONS",
    "PROVENANCE_WEIGHTS",
    "SEVERITY_TO_VAULT",
    "gamevault_design",
    "provenance_weight",
]
