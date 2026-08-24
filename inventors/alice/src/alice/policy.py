"""Deterministic state and release policy.

Agents supply artifacts and observations. This module owns the decision and is
intentionally free of model calls or mutable prompt instructions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from .domain import CandidateState, TRANSITIONS
from .reward import Evidence, RewardAssessment, RewardConfig, evaluate_reward


REQUIRED_FACTORY_CAPABILITIES = frozenset(
    {
        "durable_publication_intent",
        "explicit_price",
        "ambiguous_no_retry",
        "page_pipeline_readback",
        "expected_history_cas",
        "exact_sku_currency_binding",
        "server_enrichment_readback",
        "order_to_print_job",
    }
)
# Compatibility for callers that imported the older, misleading name.  These
# capabilities are a compiled safety floor, not defaults that config can erase.
DEFAULT_FACTORY_CAPABILITIES = REQUIRED_FACTORY_CAPABILITIES


@dataclass(frozen=True, slots=True)
class ReleaseFacts:
    evidence_integrity: bool = False
    rules_complete: bool = False
    terminates: bool = False
    critical_exploits: int = 0
    critical_safety_findings: int = 0
    critical_ip_findings: int = 0
    blind_groups: int = 0
    minimum_games_per_group: int = 0
    designer_hints_required: int = 0
    real_print_receipt: bool = False
    print_yield: float = 0.0
    gross_margin: float = 0.0
    production_packet_hash: str | None = None
    reviewed_packet_hash: str | None = None
    factory_capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "critical_exploits",
            "critical_safety_findings",
            "critical_ip_findings",
            "blind_groups",
            "minimum_games_per_group",
            "designer_hints_required",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name in ("print_yield", "gross_margin"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        for name in ("production_packet_hash", "reviewed_packet_hash"):
            value = getattr(self, name)
            if value is None:
                continue
            if (
                not isinstance(value, str)
                or len(value) != 64
                or value.lower() != value
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")
        if not isinstance(self.factory_capabilities, tuple) or any(
            not isinstance(item, str) or not item.strip()
            for item in self.factory_capabilities
        ):
            raise ValueError("factory_capabilities must be a tuple of non-empty strings")
        if len(set(self.factory_capabilities)) != len(self.factory_capabilities):
            raise ValueError("factory_capabilities must be unique")


@dataclass(frozen=True, slots=True)
class ReleasePolicyConfig:
    min_blind_groups: int = 3
    min_games_per_group: int = 2
    min_print_yield: float = 0.95
    min_gross_margin: float = 0.50
    auto_publish_when_eligible: bool = True
    required_factory_capabilities: tuple[str, ...] = tuple(
        sorted(REQUIRED_FACTORY_CAPABILITIES)
    )
    reward: RewardConfig = RewardConfig()


@dataclass(frozen=True, slots=True)
class ReleaseDecision:
    allowed: bool
    policy_hash: str
    effect_mode: str
    failures: tuple[str, ...]
    reward: RewardAssessment


class ReleasePolicy:
    def __init__(self, config: ReleasePolicyConfig | None = None) -> None:
        self.config = config or ReleasePolicyConfig()
        serializable = asdict(self.config)
        self.policy_hash = hashlib.sha256(
            json.dumps(serializable, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def assess(
        self,
        facts: ReleaseFacts,
        evidence: Evidence | Iterable[Evidence],
        *,
        effect_mode: str,
    ) -> ReleaseDecision:
        if effect_mode not in {"dry-run", "draft", "live"}:
            raise ValueError("effect_mode must be dry-run, draft, or live")
        failures: list[str] = []
        checks = (
            (facts.evidence_integrity, "evidence_integrity_failed"),
            (facts.rules_complete, "rules_incomplete"),
            (facts.terminates, "termination_not_proven"),
            (facts.critical_exploits == 0, "critical_exploit_open"),
            (facts.critical_safety_findings == 0, "critical_safety_finding_open"),
            (facts.critical_ip_findings == 0, "critical_ip_finding_open"),
            (facts.blind_groups >= self.config.min_blind_groups, "insufficient_blind_groups"),
            (
                facts.minimum_games_per_group >= self.config.min_games_per_group,
                "insufficient_games_per_group",
            ),
            (facts.designer_hints_required == 0, "designer_hints_required"),
            (facts.real_print_receipt, "real_print_receipt_missing"),
            (facts.print_yield >= self.config.min_print_yield, "print_yield_below_floor"),
            (facts.gross_margin >= self.config.min_gross_margin, "gross_margin_below_floor"),
            (
                bool(facts.production_packet_hash)
                and facts.production_packet_hash == facts.reviewed_packet_hash,
                "reviewed_packet_hash_mismatch",
            ),
        )
        failures.extend(code for passed, code in checks if not passed)
        reward = evaluate_reward(evidence, self.config.reward)
        failures.extend(f"quality:{code}" for code in reward.failure_codes)

        if effect_mode == "live":
            if not self.config.auto_publish_when_eligible:
                failures.append("automatic_publication_disabled")
            missing = set(self.config.required_factory_capabilities) - set(
                facts.factory_capabilities
            )
            failures.extend(f"factory_capability_missing:{name}" for name in sorted(missing))

        return ReleaseDecision(
            allowed=not failures,
            policy_hash=self.policy_hash,
            effect_mode=effect_mode,
            failures=tuple(failures),
            reward=reward,
        )


def validate_transition(current: str, target: str) -> None:
    try:
        allowed = TRANSITIONS[current]
    except KeyError as exc:
        raise ValueError(f"unknown candidate state {current!r}") from exc
    if target not in allowed:
        raise ValueError(f"illegal candidate transition {current!r} -> {target!r}")


def next_progress_state(current: str) -> str | None:
    """Return the single happy-path state, keeping repair/terminal paths explicit."""

    sequence = (
        CandidateState.PROPOSED,
        CandidateState.RESEARCHED,
        CandidateState.RULES_VALID,
        CandidateState.DIGITALLY_PLAYTESTED,
        CandidateState.HUMAN_READY,
        CandidateState.HUMAN_VALIDATED,
        CandidateState.PHYSICAL_READY,
        CandidateState.PRODUCTION_VALIDATED,
        CandidateState.PUBLISH_READY,
        CandidateState.PAGE_READY,
        CandidateState.PUBLISHED,
    )
    try:
        index = sequence.index(CandidateState(current))
    except (ValueError, KeyError):
        return None
    return sequence[index + 1].value if index + 1 < len(sequence) else None


def release_policy_from_config(config: Mapping[str, Any]) -> ReleasePolicy:
    """Build a pinned policy; operator config may tighten but never weaken it."""

    quality = config["quality"]
    objective = config["objective"]
    adapters = config["adapters"]
    learning = config["learning"]
    compiled_policy = ReleasePolicyConfig()
    compiled_reward = RewardConfig()
    minimum_groups = max(
        int(quality["minimum_blind_groups"]), compiled_policy.min_blind_groups
    )
    games_per_group = max(
        int(quality["minimum_games_per_group"]),
        compiled_policy.min_games_per_group,
    )
    configured_dimension_floor = float(quality["minimum_dimension"])
    reward = RewardConfig(
        dimension_floors={
            dimension: max(
                configured_dimension_floor,
                float(compiled_reward.dimension_floors[dimension]),
            )
            for dimension in compiled_reward.dimension_floors
        },
        quality_threshold=max(
            float(quality["minimum_quality"]), compiled_reward.quality_threshold
        ),
        min_confidence=max(
            float(quality["minimum_confidence"]), compiled_reward.min_confidence
        ),
        min_held_out_samples=max(
            minimum_groups * games_per_group,
            compiled_reward.min_held_out_samples,
        ),
        min_external_samples=max(
            int(learning["minimum_external_trials"]),
            compiled_reward.min_external_samples,
        ),
        min_total_eligible_samples=max(
            minimum_groups * games_per_group,
            compiled_reward.min_total_eligible_samples,
        ),
    )
    return ReleasePolicy(
        ReleasePolicyConfig(
            min_blind_groups=minimum_groups,
            min_games_per_group=games_per_group,
            min_print_yield=max(
                float(quality["minimum_print_yield"]),
                compiled_policy.min_print_yield,
            ),
            min_gross_margin=max(
                float(quality["minimum_gross_margin"]),
                compiled_policy.min_gross_margin,
            ),
            auto_publish_when_eligible=bool(
                objective["auto_publish_when_eligible"]
            ),
            required_factory_capabilities=tuple(
                sorted(
                    REQUIRED_FACTORY_CAPABILITIES
                    | set(adapters["required_live_capabilities"])
                )
            ),
            reward=reward,
        )
    )
