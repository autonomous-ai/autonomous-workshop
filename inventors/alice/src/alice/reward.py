"""Auditable reward and publication gates for Alice game candidates.

The important design choice in this module is that quality is *not* the first
thing in the reward.  Independent evidence, evidence volume, metric coverage,
metric floors, aggregate quality, and confidence are hard gates in that order.
An attractive score can therefore never compensate for missing evidence.

Only verified held-out and external observations contribute to scores or
confidence.  Surrogate observations are useful for iteration, but are kept out
of the publication calculation.  In particular, data produced by the same
model being evaluated is never publication-eligible, even when it is labelled
as held-out or external by mistake.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Iterable, Mapping, Sequence


QUALITY_DIMENSIONS: tuple[str, ...] = (
    "fun_replay",
    "clarity",
    "depth",
    "balance",
    "novelty",
    "physical_delight_print_yield",
    "economics_market",
)


DEFAULT_WEIGHTS: Mapping[str, float] = {
    "fun_replay": 0.30,
    "clarity": 0.15,
    "depth": 0.15,
    "balance": 0.10,
    "novelty": 0.10,
    "physical_delight_print_yield": 0.10,
    "economics_market": 0.10,
}


DEFAULT_DIMENSION_FLOORS: Mapping[str, float] = {
    dimension: 0.65 for dimension in QUALITY_DIMENSIONS
}


class EvidenceSource(str, Enum):
    """Provenance classes understood by the publication gate."""

    HELD_OUT = "held_out"
    EXTERNAL = "external"
    BLIND_HUMAN = "blind_human"
    MANUFACTURING = "manufacturing"
    MARKET = "market"
    DETERMINISTIC = "deterministic"
    SIMULATION = "simulation"
    INDEPENDENT_MODEL = "independent_model"
    SAME_MODEL = "same_model"
    SURROGATE = "surrogate"
    SAME_MODEL_SURROGATE = "same_model_surrogate"


_SOURCE_ALIASES = {
    "heldout": EvidenceSource.HELD_OUT,
    "holdout": EvidenceSource.HELD_OUT,
    "held_out": EvidenceSource.HELD_OUT,
    "held-out": EvidenceSource.HELD_OUT,
    "external": EvidenceSource.EXTERNAL,
    "independent": EvidenceSource.EXTERNAL,
    "blind_human": EvidenceSource.BLIND_HUMAN,
    "blind-human": EvidenceSource.BLIND_HUMAN,
    "human_blind": EvidenceSource.BLIND_HUMAN,
    "human-blind": EvidenceSource.BLIND_HUMAN,
    "manufacturing": EvidenceSource.MANUFACTURING,
    "physical": EvidenceSource.MANUFACTURING,
    "market": EvidenceSource.MARKET,
    "production": EvidenceSource.MARKET,
    "deterministic": EvidenceSource.DETERMINISTIC,
    "simulation": EvidenceSource.SIMULATION,
    "simulated": EvidenceSource.SIMULATION,
    "independent_model": EvidenceSource.INDEPENDENT_MODEL,
    "independent-model": EvidenceSource.INDEPENDENT_MODEL,
    "surrogate": EvidenceSource.SURROGATE,
    "same_model": EvidenceSource.SAME_MODEL,
    "same-model": EvidenceSource.SAME_MODEL,
    "same_model_surrogate": EvidenceSource.SAME_MODEL_SURROGATE,
    "same-model-surrogate": EvidenceSource.SAME_MODEL_SURROGATE,
}


_PUBLICATION_SOURCES = {
    EvidenceSource.HELD_OUT,
    EvidenceSource.EXTERNAL,
    EvidenceSource.BLIND_HUMAN,
    EvidenceSource.MANUFACTURING,
    EvidenceSource.MARKET,
}

_SURROGATE_SOURCES = {
    EvidenceSource.DETERMINISTIC,
    EvidenceSource.SIMULATION,
    EvidenceSource.INDEPENDENT_MODEL,
    EvidenceSource.SAME_MODEL,
    EvidenceSource.SURROGATE,
    EvidenceSource.SAME_MODEL_SURROGATE,
}


# A source may only score the domains it can directly observe.  Manufacturing
# cannot award itself fun or novelty, and market telemetry cannot award itself
# rules clarity.  Blind/held-out players can observe the whole customer
# experience, while the specialist sources provide a second hard check for the
# domains they directly measure.
SOURCE_DOMAIN_DIMENSIONS: Mapping[EvidenceSource, frozenset[str]] = {
    EvidenceSource.HELD_OUT: frozenset(QUALITY_DIMENSIONS),
    EvidenceSource.EXTERNAL: frozenset(QUALITY_DIMENSIONS),
    EvidenceSource.BLIND_HUMAN: frozenset(QUALITY_DIMENSIONS),
    EvidenceSource.MANUFACTURING: frozenset({"physical_delight_print_yield"}),
    EvidenceSource.MARKET: frozenset({"economics_market"}),
}


def _coerce_source(value: EvidenceSource | str) -> EvidenceSource:
    if isinstance(value, EvidenceSource):
        return value
    if not isinstance(value, str):
        raise TypeError("evidence source must be a string or EvidenceSource")
    try:
        return _SOURCE_ALIASES[value.strip().lower()]
    except KeyError as exc:
        allowed = ", ".join(source.value for source in EvidenceSource)
        raise ValueError(f"unknown evidence source {value!r}; expected one of {allowed}") from exc


def _unit_float(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a real number")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{label} must be finite and between 0 and 1")
    return number


def _positive_float(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a real number")
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{label} must be finite and greater than zero")
    return number


@dataclass(frozen=True, slots=True)
class QualityScores:
    """A complete, normalized quality observation.

    Scores use the closed interval ``[0, 1]``.  Keeping this type explicit
    makes it difficult to silently omit an inconvenient quality dimension.
    """

    fun_replay: float
    clarity: float
    depth: float
    balance: float
    novelty: float
    physical_delight_print_yield: float
    economics_market: float

    def __post_init__(self) -> None:
        for dimension in QUALITY_DIMENSIONS:
            object.__setattr__(
                self,
                dimension,
                _unit_float(getattr(self, dimension), f"score {dimension!r}"),
            )

    def as_dict(self) -> dict[str, float]:
        return {dimension: getattr(self, dimension) for dimension in QUALITY_DIMENSIONS}

    @classmethod
    def from_mapping(cls, scores: Mapping[str, float]) -> "QualityScores":
        normalized = _coerce_scores(scores, require_complete=True)
        return cls(**normalized)


def _coerce_scores(
    scores: QualityScores | Mapping[str, float], *, require_complete: bool
) -> dict[str, float]:
    if isinstance(scores, QualityScores):
        return scores.as_dict()
    if not isinstance(scores, Mapping):
        raise TypeError("scores must be a QualityScores instance or mapping")

    unknown = set(scores) - set(QUALITY_DIMENSIONS)
    if unknown:
        raise ValueError(f"unknown quality dimensions: {', '.join(sorted(unknown))}")
    if require_complete:
        missing = set(QUALITY_DIMENSIONS) - set(scores)
        if missing:
            raise ValueError(f"missing quality dimensions: {', '.join(sorted(missing))}")
    if not scores:
        raise ValueError("scores may not be empty")
    return {
        dimension: _unit_float(value, f"score {dimension!r}")
        for dimension, value in scores.items()
    }


@dataclass(frozen=True, slots=True)
class Evidence:
    """One batch of evidence for a game candidate.

    ``sample_size`` weights a batch during aggregation.  ``confidence`` is the
    confidence of the measurement process, not the observed quality.  Model
    identity fields let the gate detect same-model evaluation without trusting
    a caller-supplied boolean.
    """

    source: EvidenceSource | str
    scores: QualityScores | Mapping[str, float]
    verified: bool = False
    sample_size: int = 1
    confidence: float = 1.0
    surrogate: bool = False
    same_model: bool = False
    same_model_surrogate: bool = False
    evidence_id: str | None = None
    evaluator_id: str | None = None
    candidate_model_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _coerce_source(self.source))
        object.__setattr__(self, "scores", _coerce_scores(self.scores, require_complete=False))
        if not isinstance(self.verified, bool):
            raise TypeError("verified must be a bool")
        if isinstance(self.sample_size, bool) or not isinstance(self.sample_size, int):
            raise TypeError("sample_size must be an integer")
        if self.sample_size <= 0:
            raise ValueError("sample_size must be greater than zero")
        object.__setattr__(self, "confidence", _unit_float(self.confidence, "confidence"))
        for name in ("surrogate", "same_model", "same_model_surrogate"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a bool")
        for name in ("evidence_id", "evaluator_id", "candidate_model_id"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be a non-empty string when supplied")

    @property
    def is_same_model(self) -> bool:
        identities_match = (
            self.evaluator_id is not None
            and self.candidate_model_id is not None
            and self.evaluator_id == self.candidate_model_id
        )
        return bool(
            self.same_model
            or self.same_model_surrogate
            or self.source in {EvidenceSource.SAME_MODEL, EvidenceSource.SAME_MODEL_SURROGATE}
            or identities_match
        )

    @property
    def is_surrogate(self) -> bool:
        return bool(
            self.surrogate
            or self.same_model_surrogate
            or self.source in _SURROGATE_SOURCES
        )

    @property
    def publication_eligible(self) -> bool:
        return bool(
            self.verified
            and self.source in _PUBLICATION_SOURCES
            and not self.is_surrogate
            and not self.is_same_model
        )

    @property
    def is_held_out_evidence(self) -> bool:
        """Whether this source can satisfy the held-out sample requirement."""

        return self.source in {EvidenceSource.HELD_OUT, EvidenceSource.BLIND_HUMAN}

    @property
    def is_external_evidence(self) -> bool:
        """Whether this source can satisfy the external sample requirement."""

        return self.source in {
            EvidenceSource.EXTERNAL,
            EvidenceSource.BLIND_HUMAN,
            EvidenceSource.MANUFACTURING,
            EvidenceSource.MARKET,
        }

    @property
    def exclusion_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.verified:
            reasons.append("unverified")
        if self.source not in _PUBLICATION_SOURCES:
            reasons.append("non_independent_source")
        if self.is_surrogate:
            reasons.append("surrogate")
        if self.is_same_model:
            reasons.append("same_model")
        return tuple(dict.fromkeys(reasons))


@dataclass(frozen=True, slots=True)
class RewardConfig:
    """Policy thresholds for a reward assessment.

    The defaults deliberately require both held-out *and* external evidence.
    Projects with larger play-test batches should raise the sample minima while
    retaining both provenance requirements.
    """

    weights: Mapping[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    dimension_floors: Mapping[str, float] = field(
        default_factory=lambda: dict(DEFAULT_DIMENSION_FLOORS)
    )
    quality_threshold: float = 0.72
    min_confidence: float = 0.70
    min_held_out_samples: int = 6
    min_external_samples: int = 3
    min_total_eligible_samples: int = 6
    # Score weighting is deliberately bounded independently of evidence-volume
    # accounting.  A million machine rows can increase confidence in a machine
    # metric, but cannot give that source a million votes over six blind humans.
    max_score_weight_per_batch: int = 64

    def __post_init__(self) -> None:
        if not isinstance(self.weights, Mapping):
            raise TypeError("weights must be a mapping")
        if set(self.weights) != set(QUALITY_DIMENSIONS):
            missing = set(QUALITY_DIMENSIONS) - set(self.weights)
            extra = set(self.weights) - set(QUALITY_DIMENSIONS)
            details = []
            if missing:
                details.append(f"missing {', '.join(sorted(missing))}")
            if extra:
                details.append(f"unknown {', '.join(sorted(extra))}")
            raise ValueError("weights must cover exactly the quality dimensions (" + "; ".join(details) + ")")
        normalized_weights = {
            dimension: _positive_float(weight, f"weight {dimension!r}")
            for dimension, weight in self.weights.items()
        }
        object.__setattr__(self, "weights", normalized_weights)

        if not isinstance(self.dimension_floors, Mapping):
            raise TypeError("dimension_floors must be a mapping")
        if set(self.dimension_floors) != set(QUALITY_DIMENSIONS):
            raise ValueError("dimension_floors must cover exactly the quality dimensions")
        object.__setattr__(
            self,
            "dimension_floors",
            {
                dimension: _unit_float(floor, f"floor {dimension!r}")
                for dimension, floor in self.dimension_floors.items()
            },
        )
        object.__setattr__(
            self, "quality_threshold", _unit_float(self.quality_threshold, "quality_threshold")
        )
        object.__setattr__(
            self, "min_confidence", _unit_float(self.min_confidence, "min_confidence")
        )
        for name in (
            "min_held_out_samples",
            "min_external_samples",
            "min_total_eligible_samples",
            "max_score_weight_per_batch",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.max_score_weight_per_batch < 1:
            raise ValueError("max_score_weight_per_batch must be positive")


@dataclass(frozen=True, slots=True)
class GateFailure:
    gate: str
    code: str
    reason: str


@dataclass(frozen=True, slots=True)
class GateResult:
    gate: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class RewardAssessment:
    """Result of a lexicographically gated reward calculation."""

    publication_allowed: bool
    quality_score: float
    confidence: float
    dimension_scores: Mapping[str, float]
    source_domain_scores: Mapping[str, Mapping[str, float]]
    eligible_samples: int
    held_out_samples: int
    external_samples: int
    excluded_evidence: int
    gate_results: tuple[GateResult, ...]
    failures: tuple[GateFailure, ...]
    warnings: tuple[str, ...]

    @property
    def publish(self) -> bool:
        return self.publication_allowed

    @property
    def can_publish(self) -> bool:
        return self.publication_allowed

    @property
    def failed_gate(self) -> str | None:
        for result in self.gate_results:
            if not result.passed:
                return result.gate
        return None

    @property
    def failure_reasons(self) -> tuple[str, ...]:
        return tuple(failure.reason for failure in self.failures)

    @property
    def failure_codes(self) -> tuple[str, ...]:
        return tuple(failure.code for failure in self.failures)

    @property
    def lexicographic_reward(self) -> tuple[float, ...]:
        return tuple(float(result.passed) for result in self.gate_results) + (
            self.quality_score,
            self.confidence,
        )

    @property
    def reward_vector(self) -> tuple[float, ...]:
        return self.lexicographic_reward

    @property
    def reward(self) -> float:
        """Scalar downstream reward; zero until every hard gate passes."""

        return self.quality_score * self.confidence if self.publication_allowed else 0.0


def weighted_geometric_quality(
    scores: QualityScores | Mapping[str, float],
    weights: Mapping[str, float] | None = None,
) -> float:
    """Return the weighted geometric mean of all seven quality dimensions."""

    normalized_scores = _coerce_scores(scores, require_complete=True)
    chosen_weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
    if set(chosen_weights) != set(QUALITY_DIMENSIONS):
        raise ValueError("weights must cover exactly the quality dimensions")
    normalized_weights = {
        dimension: _positive_float(value, f"weight {dimension!r}")
        for dimension, value in chosen_weights.items()
    }
    if any(normalized_scores[dimension] == 0.0 for dimension in QUALITY_DIMENSIONS):
        return 0.0
    weight_total = math.fsum(normalized_weights.values())
    log_mean = math.fsum(
        (normalized_weights[dimension] / weight_total) * math.log(normalized_scores[dimension])
        for dimension in QUALITY_DIMENSIONS
    )
    return math.exp(log_mean)


# A short alias is convenient for callers doing offline analysis.
score_quality = weighted_geometric_quality


def _failure(gate: str, code: str, reason: str) -> GateFailure:
    return GateFailure(gate=gate, code=code, reason=reason)


def _aggregate_source_domains(
    eligible: Sequence[Evidence], *, max_batch_weight: int
) -> dict[str, dict[str, float]]:
    """Aggregate only source-authoritative dimensions with bounded weights."""

    result: dict[str, dict[str, float]] = {}
    for source in _PUBLICATION_SOURCES:
        observations = tuple(item for item in eligible if item.source is source)
        if not observations:
            continue
        source_scores: dict[str, float] = {}
        for dimension in SOURCE_DOMAIN_DIMENSIONS[source]:
            contributing = tuple(
                item for item in observations if dimension in item.scores
            )
            weights = tuple(
                min(item.sample_size, max_batch_weight) for item in contributing
            )
            total_weight = sum(weights)
            if total_weight:
                source_scores[dimension] = math.fsum(
                    item.scores[dimension] * weight
                    for item, weight in zip(contributing, weights, strict=True)
                ) / total_weight
        if source_scores:
            result[source.value] = source_scores
    return result


def evaluate_reward(
    evidence: Evidence | Iterable[Evidence], config: RewardConfig | None = None
) -> RewardAssessment:
    """Evaluate a candidate against ordered, non-compensating hard gates.

    Ineligible observations are excluded *before* dimension aggregation.  This
    is what prevents a large pile of same-model surrogate scores from nudging a
    candidate over either a quality floor or the aggregate threshold.
    """

    policy = config or RewardConfig()
    if isinstance(evidence, Evidence):
        observations = (evidence,)
    else:
        try:
            observations = tuple(evidence)
        except TypeError as exc:
            raise TypeError("evidence must be an Evidence instance or iterable") from exc
    if any(not isinstance(item, Evidence) for item in observations):
        raise TypeError("every evidence item must be an Evidence instance")

    eligible = tuple(item for item in observations if item.publication_eligible)
    excluded = tuple(item for item in observations if not item.publication_eligible)
    held_out_samples = sum(
        item.sample_size for item in eligible if item.is_held_out_evidence
    )
    external_samples = sum(
        item.sample_size for item in eligible if item.is_external_evidence
    )
    eligible_samples = sum(item.sample_size for item in eligible)

    source_domain_scores = _aggregate_source_domains(
        eligible, max_batch_weight=policy.max_score_weight_per_batch
    )
    dimension_scores: dict[str, float] = {}
    for dimension in QUALITY_DIMENSIONS:
        # Each authoritative source gets one vote for a domain.  Its internal
        # batches are sample-weighted only up to the compiled cap above.
        contributing = tuple(
            scores[dimension]
            for scores in source_domain_scores.values()
            if dimension in scores
        )
        if contributing:
            dimension_scores[dimension] = math.fsum(contributing) / len(contributing)

    complete = len(dimension_scores) == len(QUALITY_DIMENSIONS)
    quality_score = (
        weighted_geometric_quality(dimension_scores, policy.weights) if complete else 0.0
    )

    required_total = max(
        policy.min_total_eligible_samples,
        policy.min_held_out_samples,
        policy.min_external_samples,
        1,
    )
    sample_factor = min(1.0, eligible_samples / required_total)

    source_ratios: list[float] = []
    if policy.min_held_out_samples:
        source_ratios.append(min(1.0, held_out_samples / policy.min_held_out_samples))
    if policy.min_external_samples:
        source_ratios.append(min(1.0, external_samples / policy.min_external_samples))
    source_factor = min(source_ratios, default=1.0)
    coverage_factor = len(dimension_scores) / len(QUALITY_DIMENSIONS)
    per_source_confidence: list[float] = []
    for source in _PUBLICATION_SOURCES:
        source_items = tuple(item for item in eligible if item.source is source)
        weights = tuple(
            min(item.sample_size, policy.max_score_weight_per_batch)
            for item in source_items
        )
        weight_total = sum(weights)
        if weight_total:
            per_source_confidence.append(
                math.fsum(
                    item.confidence * weight
                    for item, weight in zip(source_items, weights, strict=True)
                )
                / weight_total
            )
    evidence_confidence = (
        math.fsum(per_source_confidence) / len(per_source_confidence)
        if per_source_confidence
        else 0.0
    )
    confidence = evidence_confidence * sample_factor * source_factor * coverage_factor

    failures: list[GateFailure] = []
    gate_results: list[GateResult] = []

    evidence_gate = bool(eligible)
    if not observations:
        failures.append(_failure("independent_evidence", "no_evidence", "No evidence was supplied."))
    elif not eligible:
        failures.append(
            _failure(
                "independent_evidence",
                "no_eligible_independent_evidence",
                "No verified independent held-out or external evidence is eligible.",
            )
        )
    gate_results.append(
        GateResult(
            "independent_evidence",
            evidence_gate,
            f"{eligible_samples} eligible samples; {len(excluded)} evidence batches excluded",
        )
    )

    volume_gate = True
    if held_out_samples < policy.min_held_out_samples:
        volume_gate = False
        failures.append(
            _failure(
                "evidence_requirements",
                "insufficient_held_out_evidence",
                f"Held-out evidence has {held_out_samples} samples; "
                f"{policy.min_held_out_samples} required.",
            )
        )
    if external_samples < policy.min_external_samples:
        volume_gate = False
        failures.append(
            _failure(
                "evidence_requirements",
                "insufficient_external_evidence",
                f"External evidence has {external_samples} samples; "
                f"{policy.min_external_samples} required.",
            )
        )
    if eligible_samples < policy.min_total_eligible_samples:
        volume_gate = False
        failures.append(
            _failure(
                "evidence_requirements",
                "insufficient_total_evidence",
                f"Eligible evidence has {eligible_samples} samples; "
                f"{policy.min_total_eligible_samples} required.",
            )
        )
    gate_results.append(
        GateResult(
            "evidence_requirements",
            volume_gate,
            f"held-out={held_out_samples}, external={external_samples}, total={eligible_samples}",
        )
    )

    coverage_gate = complete
    if not complete:
        missing = tuple(dimension for dimension in QUALITY_DIMENSIONS if dimension not in dimension_scores)
        failures.append(
            _failure(
                "metric_coverage",
                "missing_quality_dimensions",
                "Independent evidence is missing: " + ", ".join(missing) + ".",
            )
        )
    gate_results.append(
        GateResult(
            "metric_coverage",
            coverage_gate,
            f"{len(dimension_scores)}/{len(QUALITY_DIMENSIONS)} dimensions covered",
        )
    )

    floor_gate = complete
    for dimension in QUALITY_DIMENSIONS:
        score = dimension_scores.get(dimension)
        floor = policy.dimension_floors[dimension]
        if score is None:
            floor_gate = False
        elif score < floor:
            floor_gate = False
            failures.append(
                _failure(
                    "dimension_floors",
                    f"{dimension}_below_floor",
                    f"{dimension} is {score:.3f}; the hard floor is {floor:.3f}.",
                )
            )
    gate_results.append(
        GateResult("dimension_floors", floor_gate, "every dimension must meet its hard floor")
    )

    source_domain_gate = bool(source_domain_scores)
    for source_name, expected_dimensions in (
        (item.value, SOURCE_DOMAIN_DIMENSIONS[item])
        for item in _PUBLICATION_SOURCES
        if any(observation.source is item for observation in eligible)
    ):
        observed = source_domain_scores.get(source_name, {})
        for dimension in expected_dimensions:
            score = observed.get(dimension)
            floor = policy.dimension_floors[dimension]
            if score is None:
                source_domain_gate = False
                failures.append(
                    _failure(
                        "source_domain_floors",
                        f"{source_name}_{dimension}_missing",
                        f"{source_name} evidence does not measure its required "
                        f"{dimension} domain.",
                    )
                )
            elif score < floor:
                source_domain_gate = False
                failures.append(
                    _failure(
                        "source_domain_floors",
                        f"{source_name}_{dimension}_below_floor",
                        f"{source_name} {dimension} is {score:.3f}; the hard "
                        f"source-domain floor is {floor:.3f}.",
                    )
                )
    gate_results.append(
        GateResult(
            "source_domain_floors",
            source_domain_gate,
            "every eligible source must meet the floors for domains it can observe",
        )
    )

    quality_gate = complete and quality_score >= policy.quality_threshold
    if complete and not quality_gate:
        failures.append(
            _failure(
                "aggregate_quality",
                "quality_below_threshold",
                f"Weighted geometric quality is {quality_score:.3f}; "
                f"{policy.quality_threshold:.3f} required.",
            )
        )
    gate_results.append(
        GateResult(
            "aggregate_quality",
            quality_gate,
            f"weighted geometric quality={quality_score:.6f}",
        )
    )

    confidence_gate = confidence >= policy.min_confidence
    if not confidence_gate:
        failures.append(
            _failure(
                "confidence",
                "confidence_below_threshold",
                f"Confidence is {confidence:.3f}; {policy.min_confidence:.3f} required.",
            )
        )
    gate_results.append(GateResult("confidence", confidence_gate, f"confidence={confidence:.6f}"))

    warnings: list[str] = []
    if excluded:
        counts: dict[str, int] = {}
        for item in excluded:
            for reason in item.exclusion_reasons:
                counts[reason] = counts.get(reason, 0) + 1
        summary = ", ".join(f"{reason}={count}" for reason, count in sorted(counts.items()))
        warnings.append(f"Excluded {len(excluded)} evidence batches ({summary}).")

    publication_allowed = all(result.passed for result in gate_results)
    return RewardAssessment(
        publication_allowed=publication_allowed,
        quality_score=quality_score,
        confidence=confidence,
        dimension_scores=dict(dimension_scores),
        source_domain_scores={
            source: dict(scores) for source, scores in source_domain_scores.items()
        },
        eligible_samples=eligible_samples,
        held_out_samples=held_out_samples,
        external_samples=external_samples,
        excluded_evidence=len(excluded),
        gate_results=tuple(gate_results),
        failures=tuple(failures),
        warnings=tuple(warnings),
    )


def can_publish(evidence: Evidence | Iterable[Evidence], config: RewardConfig | None = None) -> bool:
    """Convenience wrapper returning only the publication decision."""

    return evaluate_reward(evidence, config).publication_allowed


class RewardEvaluator:
    """Small state-free facade for callers that keep one policy configuration."""

    def __init__(self, config: RewardConfig | None = None) -> None:
        self.config = config or RewardConfig()

    def evaluate(self, evidence: Evidence | Iterable[Evidence]) -> RewardAssessment:
        return evaluate_reward(evidence, self.config)

    def can_publish(self, evidence: Evidence | Iterable[Evidence]) -> bool:
        return self.evaluate(evidence).publication_allowed


# Names used by higher-level orchestration read naturally without a facade.
assess_reward = evaluate_reward
evaluate_publication = evaluate_reward
PublicationDecision = RewardAssessment
QualityVector = QualityScores
RewardGate = RewardEvaluator


__all__ = [
    "DEFAULT_DIMENSION_FLOORS",
    "DEFAULT_WEIGHTS",
    "QUALITY_DIMENSIONS",
    "SOURCE_DOMAIN_DIMENSIONS",
    "Evidence",
    "EvidenceSource",
    "GateFailure",
    "GateResult",
    "PublicationDecision",
    "QualityVector",
    "QualityScores",
    "RewardAssessment",
    "RewardConfig",
    "RewardEvaluator",
    "RewardGate",
    "assess_reward",
    "can_publish",
    "evaluate_publication",
    "evaluate_reward",
    "score_quality",
    "weighted_geometric_quality",
]
