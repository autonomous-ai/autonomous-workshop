"""Content-addressed reward loops for self-improving Workshop stages."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Sequence, Tuple

from .errors import ContractError
from .models import require_exact_version, require_json_mapping, require_sha256


def _copy_mapping(value: Mapping[str, Any], label: str) -> Dict[str, Any]:
    require_json_mapping(value, label)
    try:
        copied = json.loads(
            json.dumps(
                dict(value),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise ContractError("%s must be finite JSON" % label) from exc
    if not copied:
        raise ContractError("%s must not be empty" % label)
    return copied


def json_sha256(value: Mapping[str, Any]) -> str:
    copied = _copy_mapping(value, "reward-loop value")
    encoded = json.dumps(
        copied,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class RewardSignal:
    """One independent environment verdict for an exact action."""

    value: int
    goal: int
    dimensions: Mapping[str, int]
    feedback: Sequence[str]
    evaluator: str
    evaluator_version: str
    config_sha256: str
    hard_tensions: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if type(self.value) is not int or not 0 <= self.value <= 100:
            raise ContractError("reward value must be an integer from 0 to 100")
        if type(self.goal) is not int or not 1 <= self.goal <= 100:
            raise ContractError("reward goal must be an integer from 1 to 100")
        dimensions = _copy_mapping(self.dimensions, "reward dimensions")
        if not all(
            isinstance(key, str)
            and key.strip()
            and type(score) is int
            and 0 <= score <= 100
            for key, score in dimensions.items()
        ):
            raise ContractError("reward dimensions must map names to scores from 0 to 100")
        feedback = tuple(self.feedback)
        tensions = tuple(self.hard_tensions)
        for values, label in ((feedback, "feedback"), (tensions, "hard tension")):
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise ContractError("reward %s must contain non-empty text" % label)
        if not isinstance(self.evaluator, str) or not self.evaluator.strip():
            raise ContractError("reward evaluator must be non-empty text")
        require_exact_version(self.evaluator_version, "reward evaluator_version")
        require_sha256(self.config_sha256, "reward config_sha256")
        object.__setattr__(self, "dimensions", dimensions)
        object.__setattr__(self, "feedback", feedback)
        object.__setattr__(self, "hard_tensions", tensions)

    @property
    def passed(self) -> bool:
        return self.value >= self.goal and not self.hard_tensions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "goal": self.goal,
            "passed": self.passed,
            "dimensions": dict(self.dimensions),
            "feedback": list(self.feedback),
            "hard_tensions": list(self.hard_tensions),
            "evaluator": self.evaluator,
            "evaluator_version": self.evaluator_version,
            "config_sha256": self.config_sha256,
        }


@dataclass(frozen=True)
class RewardStep:
    step: int
    observation_sha256: str
    action_sha256: str
    next_state_sha256: str
    reward: RewardSignal

    def __post_init__(self) -> None:
        if type(self.step) is not int or self.step < 1:
            raise ContractError("reward-loop step must be positive")
        require_sha256(self.observation_sha256, "reward observation sha256")
        require_sha256(self.action_sha256, "reward action sha256")
        require_sha256(self.next_state_sha256, "reward next-state sha256")
        if not isinstance(self.reward, RewardSignal):
            raise ContractError("reward-loop step requires a RewardSignal")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "observation_sha256": self.observation_sha256,
            "action_sha256": self.action_sha256,
            "next_state_sha256": self.next_state_sha256,
            "reward": self.reward.to_dict(),
        }


@dataclass(frozen=True)
class RewardLoopResult:
    final_state: Mapping[str, Any]
    final_action: Mapping[str, Any]
    steps: Sequence[RewardStep]

    def __post_init__(self) -> None:
        state = _copy_mapping(self.final_state, "reward-loop final state")
        action = _copy_mapping(self.final_action, "reward-loop final action")
        steps = tuple(self.steps)
        if not steps or not all(isinstance(item, RewardStep) for item in steps):
            raise ContractError("reward loop must contain typed steps")
        object.__setattr__(self, "final_state", state)
        object.__setattr__(self, "final_action", action)
        object.__setattr__(self, "steps", steps)

    @property
    def reward(self) -> RewardSignal:
        return self.steps[-1].reward

    @property
    def reached_goal(self) -> bool:
        return self.reward.passed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reached_goal": self.reached_goal,
            "final_state_sha256": json_sha256(self.final_state),
            "final_action_sha256": json_sha256(self.final_action),
            "steps": [item.to_dict() for item in self.steps],
        }


Observer = Callable[[Mapping[str, Any], int], Mapping[str, Any]]
Agent = Callable[[Mapping[str, Any], int], Mapping[str, Any]]
Environment = Callable[
    [Mapping[str, Any], Mapping[str, Any], int],
    Tuple[Mapping[str, Any], RewardSignal],
]


def run_reward_loop(
    initial_state: Mapping[str, Any],
    *,
    observe: Observer,
    act: Agent,
    environment: Environment,
    goal: int,
    max_steps: int,
) -> RewardLoopResult:
    """Run state/observation/action/reward transitions until the goal or budget."""

    if type(goal) is not int or not 1 <= goal <= 100:
        raise ContractError("reward-loop goal must be an integer from 1 to 100")
    if type(max_steps) is not int or not 1 <= max_steps <= 20:
        raise ContractError("reward-loop max_steps must be an integer from 1 to 20")
    for function, label in (
        (observe, "observer"),
        (act, "agent"),
        (environment, "environment"),
    ):
        if not callable(function):
            raise ContractError("reward-loop %s must be callable" % label)
    state: Mapping[str, Any] = _copy_mapping(initial_state, "reward-loop initial state")
    steps = []
    action: Mapping[str, Any] = {}
    for step_number in range(1, max_steps + 1):
        observation = _copy_mapping(
            observe(state, step_number), "reward-loop observation"
        )
        action = _copy_mapping(act(observation, step_number), "reward-loop action")
        next_state, reward = environment(state, action, step_number)
        next_state = _copy_mapping(next_state, "reward-loop next state")
        if not isinstance(reward, RewardSignal):
            raise ContractError("reward-loop environment must return a RewardSignal")
        if reward.goal != goal:
            raise ContractError("reward-loop environment changed the goal")
        steps.append(
            RewardStep(
                step_number,
                json_sha256(observation),
                json_sha256(action),
                json_sha256(next_state),
                reward,
            )
        )
        state = next_state
        if reward.passed:
            break
    return RewardLoopResult(state, action, tuple(steps))


__all__ = [
    "Agent",
    "Environment",
    "Observer",
    "RewardLoopResult",
    "RewardSignal",
    "RewardStep",
    "json_sha256",
    "run_reward_loop",
]
