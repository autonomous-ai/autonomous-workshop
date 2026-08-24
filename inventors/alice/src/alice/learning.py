"""A small, auditable contextual Thompson learner for Alice.

The learner keeps an independent Beta posterior for every ``(context, action)``
pair.  It supports Thompson sampling, explicit epsilon exploration, and a
randomized or forced control action.  All randomness comes from a private
``random.Random`` instance and its full state is included in JSON snapshots, so
a restored learner continues the exact same decision sequence.

Learning is deliberately stricter than action selection: only verified,
independent held-out or external outcomes update a posterior.  Surrogate and
same-model outcomes are rejected and recorded in the audit trail.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import math
from pathlib import Path
import random
from typing import Any, Mapping, Sequence


STATE_VERSION = 1


class OutcomeSource(str, Enum):
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
    "heldout": OutcomeSource.HELD_OUT,
    "holdout": OutcomeSource.HELD_OUT,
    "held_out": OutcomeSource.HELD_OUT,
    "held-out": OutcomeSource.HELD_OUT,
    "external": OutcomeSource.EXTERNAL,
    "independent": OutcomeSource.EXTERNAL,
    "blind_human": OutcomeSource.BLIND_HUMAN,
    "blind-human": OutcomeSource.BLIND_HUMAN,
    "human_blind": OutcomeSource.BLIND_HUMAN,
    "human-blind": OutcomeSource.BLIND_HUMAN,
    "manufacturing": OutcomeSource.MANUFACTURING,
    "physical": OutcomeSource.MANUFACTURING,
    "market": OutcomeSource.MARKET,
    "production": OutcomeSource.MARKET,
    "deterministic": OutcomeSource.DETERMINISTIC,
    "simulation": OutcomeSource.SIMULATION,
    "simulated": OutcomeSource.SIMULATION,
    "independent_model": OutcomeSource.INDEPENDENT_MODEL,
    "independent-model": OutcomeSource.INDEPENDENT_MODEL,
    "surrogate": OutcomeSource.SURROGATE,
    "same_model": OutcomeSource.SAME_MODEL,
    "same-model": OutcomeSource.SAME_MODEL,
    "same_model_surrogate": OutcomeSource.SAME_MODEL_SURROGATE,
    "same-model-surrogate": OutcomeSource.SAME_MODEL_SURROGATE,
}


_VERIFIED_OUTCOME_SOURCES = {
    OutcomeSource.HELD_OUT,
    OutcomeSource.EXTERNAL,
    OutcomeSource.BLIND_HUMAN,
    OutcomeSource.MANUFACTURING,
    OutcomeSource.MARKET,
}

_SURROGATE_SOURCES = {
    OutcomeSource.DETERMINISTIC,
    OutcomeSource.SIMULATION,
    OutcomeSource.INDEPENDENT_MODEL,
    OutcomeSource.SAME_MODEL,
    OutcomeSource.SURROGATE,
    OutcomeSource.SAME_MODEL_SURROGATE,
}


def _coerce_source(value: OutcomeSource | str) -> OutcomeSource:
    if isinstance(value, OutcomeSource):
        return value
    if not isinstance(value, str):
        raise TypeError("outcome source must be a string or OutcomeSource")
    try:
        return _SOURCE_ALIASES[value.strip().lower()]
    except KeyError as exc:
        allowed = ", ".join(source.value for source in OutcomeSource)
        raise ValueError(f"unknown outcome source {value!r}; expected one of {allowed}") from exc


def _finite_float(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _unit_float(value: object, label: str) -> float:
    result = _finite_float(value, label)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{label} must be between 0 and 1")
    return result


def _positive_float(value: object, label: str) -> float:
    result = _finite_float(value, label)
    if result <= 0.0:
        raise ValueError(f"{label} must be greater than zero")
    return result


def _json_value(value: Any, path: str = "context") -> Any:
    """Validate and normalize a context into a deterministic JSON value."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return value
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} keys must be strings")
            normalized[key] = _json_value(item, f"{path}.{key}")
        return normalized
    if isinstance(value, (list, tuple)):
        return [_json_value(item, f"{path}[{index}]") for index, item in enumerate(value)]
    raise TypeError(
        f"{path} contains unsupported {type(value).__name__}; "
        "use JSON-compatible values"
    )


def canonical_context(context: Any = None) -> str:
    """Return a stable, collision-resistant key for a JSON-compatible context."""

    return json.dumps(
        _json_value(context), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


@dataclass(frozen=True, slots=True)
class OutcomeEvidence:
    """Provenance attached to an observed action outcome."""

    source: OutcomeSource | str
    verified: bool
    surrogate: bool = False
    same_model: bool = False
    same_model_surrogate: bool = False
    evaluator_id: str | None = None
    candidate_model_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _coerce_source(self.source))
        for name in ("verified", "surrogate", "same_model", "same_model_surrogate"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a bool")
        for name in ("evaluator_id", "candidate_model_id"):
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
            or self.source in {OutcomeSource.SAME_MODEL, OutcomeSource.SAME_MODEL_SURROGATE}
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
    def eligible(self) -> bool:
        return bool(
            self.verified
            and self.source in _VERIFIED_OUTCOME_SOURCES
            and not self.is_surrogate
            and not self.is_same_model
        )

    @property
    def rejection_reason(self) -> str | None:
        if not self.verified:
            return "unverified_outcome"
        if self.is_same_model:
            return "same_model_outcome"
        if self.is_surrogate:
            return "surrogate_outcome"
        if self.source not in _VERIFIED_OUTCOME_SOURCES:
            return "ineligible_source"
        return None


@dataclass(frozen=True, slots=True)
class BetaPosterior:
    """Read-only posterior summary returned to callers."""

    alpha: float
    beta: float
    observations: int = 0
    accepted_weight: float = 0.0
    success_weight: float = 0.0
    failure_weight: float = 0.0

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        total = self.alpha + self.beta
        return self.alpha * self.beta / (total * total * (total + 1.0))

    def to_state(self) -> dict[str, float | int]:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "observations": self.observations,
            "accepted_weight": self.accepted_weight,
            "success_weight": self.success_weight,
            "failure_weight": self.failure_weight,
        }

    @classmethod
    def from_state(cls, state: Mapping[str, Any]) -> "BetaPosterior":
        if not isinstance(state, Mapping):
            raise TypeError("posterior state must be a mapping")
        alpha = _positive_float(state.get("alpha"), "posterior alpha")
        beta = _positive_float(state.get("beta"), "posterior beta")
        observations = state.get("observations", 0)
        if isinstance(observations, bool) or not isinstance(observations, int) or observations < 0:
            raise ValueError("posterior observations must be a non-negative integer")
        accepted_weight = _finite_float(state.get("accepted_weight", 0.0), "accepted_weight")
        success_weight = _finite_float(state.get("success_weight", 0.0), "success_weight")
        failure_weight = _finite_float(state.get("failure_weight", 0.0), "failure_weight")
        if min(accepted_weight, success_weight, failure_weight) < 0.0:
            raise ValueError("posterior weights must be non-negative")
        if not math.isclose(
            success_weight + failure_weight, accepted_weight, rel_tol=1e-9, abs_tol=1e-12
        ):
            raise ValueError("posterior success and failure weights must sum to accepted_weight")
        return cls(
            alpha=alpha,
            beta=beta,
            observations=observations,
            accepted_weight=accepted_weight,
            success_weight=success_weight,
            failure_weight=failure_weight,
        )


@dataclass(frozen=True, slots=True)
class Selection:
    action: str
    mode: str
    context_key: str
    posterior_means: Mapping[str, float]
    sampled_values: Mapping[str, float]
    selection_number: int

    @property
    def explored(self) -> bool:
        return self.mode in {"thompson", "epsilon", "randomized_control"}

    @property
    def is_control(self) -> bool:
        return self.mode in {"forced_control", "randomized_control"}

    def to_state(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "mode": self.mode,
            "context_key": self.context_key,
            "posterior_means": dict(self.posterior_means),
            "sampled_values": dict(self.sampled_values),
            "selection_number": self.selection_number,
        }

    @classmethod
    def from_state(cls, state: Mapping[str, Any]) -> "Selection":
        return cls(
            action=str(state["action"]),
            mode=str(state["mode"]),
            context_key=str(state["context_key"]),
            posterior_means={str(k): float(v) for k, v in state["posterior_means"].items()},
            sampled_values={str(k): float(v) for k, v in state["sampled_values"].items()},
            selection_number=int(state["selection_number"]),
        )


@dataclass(frozen=True, slots=True)
class UpdateResult:
    accepted: bool
    reason: str
    action: str
    context_key: str
    outcome: float
    evidence_source: str
    event_id: str | None = None

    def __bool__(self) -> bool:
        return self.accepted

    def to_state(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "action": self.action,
            "context_key": self.context_key,
            "outcome": self.outcome,
            "evidence_source": self.evidence_source,
            "event_id": self.event_id,
        }

    @classmethod
    def from_state(cls, state: Mapping[str, Any]) -> "UpdateResult":
        return cls(
            accepted=bool(state["accepted"]),
            reason=str(state["reason"]),
            action=str(state["action"]),
            context_key=str(state["context_key"]),
            outcome=float(state["outcome"]),
            evidence_source=str(state["evidence_source"]),
            event_id=None if state.get("event_id") is None else str(state["event_id"]),
        )


def _state_lists(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_state_lists(item) for item in value]
    if isinstance(value, list):
        return [_state_lists(item) for item in value]
    return value


def _state_tuples(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_state_tuples(item) for item in value)
    return value


class ContextualThompsonBandit:
    """Context-specific Beta bandit with strict evidence-gated updates."""

    def __init__(
        self,
        actions: Sequence[str],
        *,
        seed: int = 0,
        alpha_prior: float = 1.0,
        beta_prior: float = 1.0,
        exploration_rate: float = 0.0,
        epsilon: float | None = None,
        exploration_probability: float | None = None,
        control_action: str | None = None,
        control_rate: float = 0.0,
        audit_limit: int = 1_000,
    ) -> None:
        if isinstance(actions, (str, bytes)) or not isinstance(actions, Sequence):
            raise TypeError("actions must be a sequence of strings")
        normalized_actions = tuple(actions)
        if not normalized_actions:
            raise ValueError("at least one action is required")
        if any(not isinstance(action, str) or not action.strip() for action in normalized_actions):
            raise ValueError("actions must be non-empty strings")
        if len(set(normalized_actions)) != len(normalized_actions):
            raise ValueError("actions must be unique")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise TypeError("seed must be an integer")
        self.actions = normalized_actions
        self.seed = seed
        self.alpha_prior = _positive_float(alpha_prior, "alpha_prior")
        self.beta_prior = _positive_float(beta_prior, "beta_prior")
        exploration_aliases = [
            value for value in (epsilon, exploration_probability) if value is not None
        ]
        for alias in exploration_aliases:
            if exploration_rate != 0.0 and not math.isclose(exploration_rate, alias):
                raise ValueError("exploration probability aliases have conflicting values")
            exploration_rate = alias
        if len(exploration_aliases) == 2 and not math.isclose(
            exploration_aliases[0], exploration_aliases[1]
        ):
            raise ValueError("exploration probability aliases have conflicting values")
        self.exploration_rate = _unit_float(exploration_rate, "exploration_rate")
        if control_action is not None and control_action not in self.actions:
            raise ValueError("control_action must be one of actions")
        self.control_action = control_action
        self.control_rate = _unit_float(control_rate, "control_rate")
        if self.control_rate > 0.0 and self.control_action is None:
            raise ValueError("control_action is required when control_rate is positive")
        if isinstance(audit_limit, bool) or not isinstance(audit_limit, int):
            raise TypeError("audit_limit must be an integer")
        if audit_limit < 0:
            raise ValueError("audit_limit must be non-negative")
        self.audit_limit = audit_limit

        self._rng = random.Random(seed)
        self._posteriors: dict[str, dict[str, BetaPosterior]] = {}
        self._contexts: dict[str, Any] = {}
        self._selection_counts: dict[str, dict[str, int]] = {}
        self._seen_event_ids: set[str] = set()
        self._audit: list[dict[str, Any]] = []
        self.selection_count = 0
        self.accepted_updates = 0
        self.rejected_updates = 0
        self.accepted_weight = 0.0
        self.last_selection: Selection | None = None
        self.last_update: UpdateResult | None = None

    @property
    def epsilon(self) -> float:
        return self.exploration_rate

    @property
    def exploration_probability(self) -> float:
        return self.exploration_rate

    def _remember_context(self, context: Any) -> tuple[str, Any]:
        normalized = _json_value(context)
        key = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        self._contexts.setdefault(key, normalized)
        return key, normalized

    def _prior(self) -> BetaPosterior:
        return BetaPosterior(alpha=self.alpha_prior, beta=self.beta_prior)

    def posterior(self, action: str, context: Any = None) -> BetaPosterior:
        if action not in self.actions:
            raise ValueError(f"unknown action {action!r}")
        key = canonical_context(context)
        return self._posteriors.get(key, {}).get(action, self._prior())

    def posterior_mean(self, action: str, context: Any = None) -> float:
        return self.posterior(action, context).mean

    def posteriors(self, context: Any = None) -> dict[str, BetaPosterior]:
        return {action: self.posterior(action, context) for action in self.actions}

    def selection_counts(self, context: Any = None) -> dict[str, int]:
        key = canonical_context(context)
        counts = self._selection_counts.get(key, {})
        return {action: counts.get(action, 0) for action in self.actions}

    def recommend(
        self,
        context: Any = None,
        *,
        explore: bool = True,
        force_control: bool = False,
    ) -> Selection:
        """Select an action and return the full, auditable decision record."""

        if not isinstance(explore, bool) or not isinstance(force_control, bool):
            raise TypeError("explore and force_control must be bools")
        key, _ = self._remember_context(context)
        posterior_map = self.posteriors(context)
        means = {action: posterior_map[action].mean for action in self.actions}
        sampled: dict[str, float] = {}

        if force_control:
            if self.control_action is None:
                raise ValueError("cannot force control without a control_action")
            action = self.control_action
            mode = "forced_control"
        elif explore and self.control_action is not None and self.control_rate > 0.0 and self._rng.random() < self.control_rate:
            action = self.control_action
            mode = "randomized_control"
        elif explore and self.exploration_rate > 0.0 and self._rng.random() < self.exploration_rate:
            action = self.actions[self._rng.randrange(len(self.actions))]
            mode = "epsilon"
        elif explore:
            sampled = {
                candidate: self._rng.betavariate(
                    posterior_map[candidate].alpha, posterior_map[candidate].beta
                )
                for candidate in self.actions
            }
            action = max(self.actions, key=lambda candidate: sampled[candidate])
            mode = "thompson"
        else:
            action = max(self.actions, key=lambda candidate: means[candidate])
            mode = "exploit"

        self.selection_count += 1
        context_counts = self._selection_counts.setdefault(key, {})
        context_counts[action] = context_counts.get(action, 0) + 1
        selection = Selection(
            action=action,
            mode=mode,
            context_key=key,
            posterior_means=means,
            sampled_values=sampled,
            selection_number=self.selection_count,
        )
        self.last_selection = selection
        return selection

    def choose_action(
        self,
        context: Any = None,
        *,
        explore: bool = True,
        force_control: bool = False,
    ) -> str:
        return self.recommend(context, explore=explore, force_control=force_control).action

    def select_action(
        self,
        context: Any = None,
        *,
        explore: bool = True,
        force_control: bool = False,
    ) -> str:
        return self.choose_action(context, explore=explore, force_control=force_control)

    def _append_audit(self, item: dict[str, Any]) -> None:
        if self.audit_limit == 0:
            return
        self._audit.append(item)
        if len(self._audit) > self.audit_limit:
            del self._audit[: len(self._audit) - self.audit_limit]

    @property
    def audit_log(self) -> tuple[dict[str, Any], ...]:
        # JSON round-tripping produces a cheap deep copy using only stdlib.
        return tuple(json.loads(json.dumps(item)) for item in self._audit)

    def observe(
        self,
        action: str,
        outcome: bool | float,
        context: Any = None,
        *,
        evidence: OutcomeEvidence | None = None,
        evidence_source: OutcomeSource | str | None = None,
        source: OutcomeSource | str | None = None,
        verified: bool = False,
        surrogate: bool = False,
        same_model: bool = False,
        same_model_surrogate: bool = False,
        evaluator_id: str | None = None,
        candidate_model_id: str | None = None,
        weight: float = 1.0,
        event_id: str | None = None,
    ) -> UpdateResult:
        """Observe an outcome, updating only when provenance passes the gate."""

        if action not in self.actions:
            raise ValueError(f"unknown action {action!r}")
        if isinstance(outcome, bool):
            normalized_outcome = float(outcome)
        else:
            normalized_outcome = _unit_float(outcome, "outcome")
        normalized_weight = _positive_float(weight, "weight")
        key, _ = self._remember_context(context)
        if event_id is not None and (not isinstance(event_id, str) or not event_id.strip()):
            raise ValueError("event_id must be a non-empty string when supplied")

        if source is not None:
            if evidence_source is not None and _coerce_source(source) is not _coerce_source(evidence_source):
                raise ValueError("source and evidence_source conflict")
            evidence_source = source
        if evidence is not None:
            if not isinstance(evidence, OutcomeEvidence):
                raise TypeError("evidence must be an OutcomeEvidence instance")
            metadata_was_also_supplied = (
                evidence_source is not None
                or verified
                or surrogate
                or same_model
                or same_model_surrogate
                or evaluator_id is not None
                or candidate_model_id is not None
            )
            if metadata_was_also_supplied:
                raise ValueError("supply evidence or provenance keyword fields, not both")
            provenance = evidence
        elif evidence_source is None:
            provenance = None
        else:
            provenance = OutcomeEvidence(
                source=evidence_source,
                verified=verified,
                surrogate=surrogate,
                same_model=same_model,
                same_model_surrogate=same_model_surrogate,
                evaluator_id=evaluator_id,
                candidate_model_id=candidate_model_id,
            )

        if event_id is not None and event_id in self._seen_event_ids:
            accepted = False
            reason = "duplicate_event"
            source_name = provenance.source.value if provenance is not None else "missing"
        elif provenance is None:
            accepted = False
            reason = "missing_evidence_source"
            source_name = "missing"
        elif not provenance.eligible:
            accepted = False
            reason = provenance.rejection_reason or "ineligible_evidence"
            source_name = provenance.source.value
        else:
            accepted = True
            reason = "accepted_verified_independent_outcome"
            source_name = provenance.source.value

        before = self.posterior(action, context)
        after = before
        if accepted:
            success_weight = normalized_weight * normalized_outcome
            failure_weight = normalized_weight * (1.0 - normalized_outcome)
            after = BetaPosterior(
                alpha=before.alpha + success_weight,
                beta=before.beta + failure_weight,
                observations=before.observations + 1,
                accepted_weight=before.accepted_weight + normalized_weight,
                success_weight=before.success_weight + success_weight,
                failure_weight=before.failure_weight + failure_weight,
            )
            self._posteriors.setdefault(key, {})[action] = after
            self.accepted_updates += 1
            self.accepted_weight += normalized_weight
            if event_id is not None:
                self._seen_event_ids.add(event_id)
        else:
            self.rejected_updates += 1

        result = UpdateResult(
            accepted=accepted,
            reason=reason,
            action=action,
            context_key=key,
            outcome=normalized_outcome,
            evidence_source=source_name,
            event_id=event_id,
        )
        self.last_update = result
        self._append_audit(
            {
                **result.to_state(),
                "weight": normalized_weight,
                "posterior_before": before.to_state(),
                "posterior_after": after.to_state(),
            }
        )
        return result

    def update(
        self,
        action: str,
        outcome: bool | float,
        context: Any = None,
        **kwargs: Any,
    ) -> bool:
        """Boolean convenience wrapper around :meth:`observe`."""

        return self.observe(action, outcome, context, **kwargs).accepted

    def to_state(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot, including exact RNG state."""

        return {
            "state_version": STATE_VERSION,
            "actions": list(self.actions),
            "seed": self.seed,
            "alpha_prior": self.alpha_prior,
            "beta_prior": self.beta_prior,
            "exploration_rate": self.exploration_rate,
            "control_action": self.control_action,
            "control_rate": self.control_rate,
            "audit_limit": self.audit_limit,
            "rng_state": _state_lists(self._rng.getstate()),
            "contexts": dict(self._contexts),
            "posteriors": {
                key: {action: posterior.to_state() for action, posterior in action_map.items()}
                for key, action_map in self._posteriors.items()
            },
            "selection_counts": {
                key: dict(action_map) for key, action_map in self._selection_counts.items()
            },
            "seen_event_ids": sorted(self._seen_event_ids),
            "selection_count": self.selection_count,
            "accepted_updates": self.accepted_updates,
            "rejected_updates": self.rejected_updates,
            "accepted_weight": self.accepted_weight,
            "last_selection": None if self.last_selection is None else self.last_selection.to_state(),
            "last_update": None if self.last_update is None else self.last_update.to_state(),
            "audit": list(self._audit),
        }

    state_dict = to_state

    def to_json(self, *, indent: int | None = None) -> str:
        return json.dumps(
            self.to_state(),
            sort_keys=True,
            separators=None if indent is not None else (",", ":"),
            indent=indent,
            ensure_ascii=False,
            allow_nan=False,
        )

    def save(self, path: str | Path, *, indent: int | None = 2) -> None:
        Path(path).write_text(self.to_json(indent=indent) + "\n", encoding="utf-8")

    @classmethod
    def from_state(cls, state: Mapping[str, Any]) -> "ContextualThompsonBandit":
        if not isinstance(state, Mapping):
            raise TypeError("learner state must be a mapping")
        if state.get("state_version") != STATE_VERSION:
            raise ValueError(
                f"unsupported learner state version {state.get('state_version')!r}; "
                f"expected {STATE_VERSION}"
            )
        learner = cls(
            state["actions"],
            seed=state["seed"],
            alpha_prior=state["alpha_prior"],
            beta_prior=state["beta_prior"],
            exploration_rate=state["exploration_rate"],
            control_action=state.get("control_action"),
            control_rate=state["control_rate"],
            audit_limit=state.get("audit_limit", 1_000),
        )

        contexts = state.get("contexts", {})
        if not isinstance(contexts, Mapping):
            raise TypeError("contexts state must be a mapping")
        learner._contexts = {}
        for key, context in contexts.items():
            if not isinstance(key, str):
                raise TypeError("context state keys must be strings")
            normalized = _json_value(context)
            if canonical_context(normalized) != key:
                raise ValueError("context key does not match its canonical context value")
            learner._contexts[key] = normalized

        posterior_state = state.get("posteriors", {})
        if not isinstance(posterior_state, Mapping):
            raise TypeError("posteriors state must be a mapping")
        learner._posteriors = {}
        for key, action_map in posterior_state.items():
            if key not in learner._contexts:
                raise ValueError("posterior references an unknown context key")
            if not isinstance(action_map, Mapping):
                raise TypeError("posterior action map must be a mapping")
            unknown_actions = set(action_map) - set(learner.actions)
            if unknown_actions:
                raise ValueError(f"posterior contains unknown actions: {sorted(unknown_actions)!r}")
            learner._posteriors[key] = {
                action: BetaPosterior.from_state(posterior)
                for action, posterior in action_map.items()
            }

        selection_counts = state.get("selection_counts", {})
        if not isinstance(selection_counts, Mapping):
            raise TypeError("selection_counts state must be a mapping")
        learner._selection_counts = {}
        for key, action_map in selection_counts.items():
            if key not in learner._contexts:
                raise ValueError("selection counts reference an unknown context key")
            if not isinstance(action_map, Mapping):
                raise TypeError("selection count action map must be a mapping")
            normalized_counts: dict[str, int] = {}
            for action, count in action_map.items():
                if action not in learner.actions:
                    raise ValueError(f"selection counts contain unknown action {action!r}")
                if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                    raise ValueError("selection counts must be non-negative integers")
                normalized_counts[action] = count
            learner._selection_counts[key] = normalized_counts

        seen = state.get("seen_event_ids", [])
        if not isinstance(seen, list) or any(not isinstance(item, str) or not item for item in seen):
            raise ValueError("seen_event_ids must be a list of non-empty strings")
        if len(set(seen)) != len(seen):
            raise ValueError("seen_event_ids contains duplicates")
        learner._seen_event_ids = set(seen)

        def non_negative_int(name: str) -> int:
            value = state.get(name, 0)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
            return value

        learner.selection_count = non_negative_int("selection_count")
        learner.accepted_updates = non_negative_int("accepted_updates")
        learner.rejected_updates = non_negative_int("rejected_updates")
        learner.accepted_weight = _finite_float(state.get("accepted_weight", 0.0), "accepted_weight")
        if learner.accepted_weight < 0.0:
            raise ValueError("accepted_weight must be non-negative")

        last_selection = state.get("last_selection")
        learner.last_selection = (
            None if last_selection is None else Selection.from_state(last_selection)
        )
        last_update = state.get("last_update")
        learner.last_update = None if last_update is None else UpdateResult.from_state(last_update)
        audit = state.get("audit", [])
        if not isinstance(audit, list) or any(not isinstance(item, Mapping) for item in audit):
            raise TypeError("audit state must be a list of mappings")
        learner._audit = [dict(item) for item in audit[-learner.audit_limit :]] if learner.audit_limit else []

        try:
            learner._rng.setstate(_state_tuples(state["rng_state"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid RNG state") from exc
        return learner

    from_state_dict = from_state

    @classmethod
    def from_json(cls, payload: str | bytes | bytearray) -> "ContextualThompsonBandit":
        try:
            state = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid learner JSON") from exc
        return cls.from_state(state)

    @classmethod
    def load(cls, path: str | Path) -> "ContextualThompsonBandit":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


# Concise aliases for orchestration code that does not care about the algorithm name.
BanditLearner = ContextualThompsonBandit
OnlineLearner = ContextualThompsonBandit
ContextualBetaBandit = ContextualThompsonBandit
ThompsonBandit = ContextualThompsonBandit


__all__ = [
    "STATE_VERSION",
    "BanditLearner",
    "BetaPosterior",
    "ContextualBetaBandit",
    "ContextualThompsonBandit",
    "OnlineLearner",
    "OutcomeEvidence",
    "OutcomeSource",
    "Selection",
    "ThompsonBandit",
    "UpdateResult",
    "canonical_context",
]
