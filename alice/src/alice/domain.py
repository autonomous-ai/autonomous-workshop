"""Stable domain vocabulary shared by Alice's runtime and policy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class CandidateState(StrEnum):
    PROPOSED = "proposed"
    RESEARCHED = "researched"
    RULES_VALID = "rules_valid"
    DIGITALLY_PLAYTESTED = "digitally_playtested"
    HUMAN_READY = "human_ready"
    HUMAN_VALIDATED = "human_validated"
    PHYSICAL_READY = "physical_ready"
    PRODUCTION_VALIDATED = "production_validated"
    PUBLISH_READY = "publish_ready"
    PAGE_READY = "page_ready"
    PUBLISHED = "published"
    REWORK = "rework"
    BLOCKED = "blocked"
    KILLED = "killed"
    ARCHIVED = "archived"


class EvidenceSource(StrEnum):
    DETERMINISTIC = "deterministic"
    SIMULATION = "simulation"
    SAME_MODEL = "same_model"
    INDEPENDENT_MODEL = "independent_model"
    BLIND_HUMAN = "blind_human"
    MANUFACTURING = "manufacturing"
    MARKET = "market"


class EffectMode(StrEnum):
    DRY_RUN = "dry-run"
    DRAFT = "draft"
    LIVE = "live"


@dataclass(frozen=True, slots=True)
class WorkItem:
    loop: str
    action: str
    role: str
    objective: str
    candidate_id: str | None = None
    payload: dict[str, Any] | None = None
    depends_on: tuple[str, ...] = ()


TERMINAL_STATES = {
    CandidateState.PUBLISHED.value,
    CandidateState.KILLED.value,
    CandidateState.ARCHIVED.value,
}


TRANSITIONS: dict[str, set[str]] = {
    CandidateState.PROPOSED: {CandidateState.RESEARCHED, CandidateState.REWORK, CandidateState.KILLED},
    CandidateState.RESEARCHED: {CandidateState.RULES_VALID, CandidateState.REWORK, CandidateState.KILLED},
    CandidateState.RULES_VALID: {CandidateState.DIGITALLY_PLAYTESTED, CandidateState.REWORK, CandidateState.KILLED},
    CandidateState.DIGITALLY_PLAYTESTED: {CandidateState.HUMAN_READY, CandidateState.REWORK, CandidateState.KILLED},
    CandidateState.HUMAN_READY: {CandidateState.HUMAN_VALIDATED, CandidateState.REWORK, CandidateState.BLOCKED, CandidateState.KILLED},
    CandidateState.HUMAN_VALIDATED: {CandidateState.PHYSICAL_READY, CandidateState.REWORK, CandidateState.KILLED},
    CandidateState.PHYSICAL_READY: {CandidateState.PRODUCTION_VALIDATED, CandidateState.REWORK, CandidateState.BLOCKED, CandidateState.KILLED},
    CandidateState.PRODUCTION_VALIDATED: {CandidateState.PUBLISH_READY, CandidateState.REWORK, CandidateState.KILLED},
    CandidateState.PUBLISH_READY: {CandidateState.PAGE_READY, CandidateState.REWORK, CandidateState.BLOCKED},
    CandidateState.PAGE_READY: {CandidateState.PUBLISHED, CandidateState.REWORK, CandidateState.BLOCKED},
    CandidateState.REWORK: {
        CandidateState.PROPOSED,
        CandidateState.RESEARCHED,
        CandidateState.RULES_VALID,
        CandidateState.DIGITALLY_PLAYTESTED,
        CandidateState.HUMAN_READY,
        CandidateState.PHYSICAL_READY,
        CandidateState.PUBLISH_READY,
        CandidateState.KILLED,
    },
    CandidateState.BLOCKED: {CandidateState.REWORK, CandidateState.KILLED, CandidateState.ARCHIVED},
    CandidateState.KILLED: {CandidateState.ARCHIVED},
    CandidateState.PUBLISHED: {CandidateState.ARCHIVED},
    CandidateState.ARCHIVED: set(),
}
