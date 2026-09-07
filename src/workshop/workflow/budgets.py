"""Native execution budgets, including frozen legacy command clocks.

New lifetime-capable runs reserve and settle a durable allowance across
resumes. The command-clock description below applies only to older runs.

These clocks bound **one toy**, from its sealed brief to its published page.
They are created once per ``workshop start`` build or ``workshop resume``, so
the daydream loop that calls them is never bounded by them: it dreams and
builds until an operator stops it, and each toy starts with fresh clocks.

A run frozen with :data:`BUDGETS_CAPABILITY_PATH` replaces every turn counter
and recovery window with:

* :data:`STEP_BUDGET_SECONDS` for each step (Invent, Make, Playtest,
  Release), which is room for two maximum-length turns so a slow turn can be
  resumed rather than lost;
* :data:`RUN_BUDGET_SECONDS` for that one toy across all of its steps.

Inside its clocks a step may take as many native turns as it needs and the
host continues the same Goal automatically.  Every turn is bounded by whatever
is left, so a turn never outlives its step.  When a clock runs out the build
stops with one plain sentence and the exact session stays checkpointed;
``workshop resume`` starts fresh clocks.

Runs frozen before this capability keep their historical counters and windows.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Optional

from workshop.errors import ContractError


BUDGETS_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/budgets-v1.md"
)
LIFETIME_BUDGETS_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/lifetime-budgets-v1.md"
)
LIFETIME_STEP_SECONDS = 40 * 60
LIFETIME_RUN_SECONDS = 60 * 60
TURN_BUDGETS_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/turn-budgets-v1.md"
)
STAGE_TURN_LIMIT = 6
PRODUCT_TURN_LIMIT = 12
# A step must afford more than one maximum-length turn, or a single timeout
# ends it and throws away work a resume would have finalized.  Two full turns
# matches the ceiling the retired two-timeout rail allowed.
STEP_BUDGET_SECONDS = 2 * 60 * 60
RUN_BUDGET_SECONDS = 6 * 60 * 60
# The runtime launchers refuse anything longer, so no turn may exceed it.
MAX_TURN_SECONDS = 60 * 60
# Budgeted Spark uses the shorter operator-requested boundary. Keep this
# separate from legacy launcher defaults so unbudgeted session policies do not
# drift on resume.
SPARK_BUDGETED_TURN_SECONDS = 20 * 60
MIN_TURN_SECONDS = 60
# Starting a turn with only minutes left spends them and finalizes nothing.
MIN_USEFUL_TURN_SECONDS = 10 * 60
# A clock, not a counter, ends a budgeted command; this only stops a pathological
# loop of instant turns from spinning forever.
MAX_BUDGETED_TURNS = 200


def _positive_seconds(value: Any, label: str) -> int:
    if type(value) is not int or not 1 <= value <= 24 * 60 * 60:
        raise ContractError("%s must be a whole number of seconds in one day" % label)
    return value


@dataclass
class CommandBudget:
    """The two clocks of one toy's build. The daydream loop is not bounded."""

    step_seconds: int = STEP_BUDGET_SECONDS
    run_seconds: int = RUN_BUDGET_SECONDS
    clock: Callable[[], float] = time.monotonic
    _spent_by_step: Dict[str, float] = field(default_factory=dict)
    _spent_total: float = 0.0

    def __post_init__(self) -> None:
        _positive_seconds(self.step_seconds, "step budget")
        _positive_seconds(self.run_seconds, "run budget")
        if self.step_seconds > self.run_seconds:
            raise ContractError("a step budget cannot exceed the run budget")
        if not callable(self.clock):
            raise ContractError("budget clock must be callable")

    def spent(self, step: str) -> float:
        return self._spent_by_step.get(step, 0.0)

    @property
    def spent_total(self) -> float:
        return self._spent_total

    def remaining(self, step: str) -> float:
        """Seconds left for this step: the tighter of its clock and the run's."""

        return min(
            self.step_seconds - self.spent(step),
            self.run_seconds - self._spent_total,
        )

    def exhausted(self, step: str) -> Optional[str]:
        """Return ``step`` or ``run`` when a clock has no usable time left."""

        if self.run_seconds - self._spent_total < MIN_USEFUL_TURN_SECONDS:
            return "run"
        if self.step_seconds - self.spent(step) < MIN_USEFUL_TURN_SECONDS:
            return "step"
        return None

    def turn_timeout_seconds(self, step: str) -> int:
        """Bound one native turn by whatever both clocks still allow."""

        allowed = min(float(MAX_TURN_SECONDS), self.remaining(step))
        return max(MIN_TURN_SECONDS, int(math.floor(allowed)))

    def spend(self, step: str, seconds: float) -> None:
        if type(seconds) not in (int, float) or seconds < 0 or not math.isfinite(seconds):
            raise ContractError("budget spend must be a non-negative number")
        self._spent_by_step[step] = self.spent(step) + float(seconds)
        self._spent_total += float(seconds)

    def started(self) -> float:
        """Return a mark for :meth:`spend_since`."""

        return float(self.clock())

    def spend_since(self, step: str, mark: float) -> float:
        elapsed = max(0.0, float(self.clock()) - float(mark))
        self.spend(step, elapsed)
        return elapsed

    def exhausted_message(self, step: str, which: str, product_id: str) -> str:
        if which == "run":
            used, limit = self._spent_total, self.run_seconds
            what = "This toy"
        else:
            used, limit = self.spent(step), self.step_seconds
            what = step.title()
        return (
            "%s used its %d-minute budget (%d minutes spent); the exact session "
            "remains checkpointed and resumable with `workshop resume %s`"
            % (what, limit // 60, int(used // 60), product_id)
        )

    def to_dict(self) -> Dict[str, Any]:
        """The receipt view: whole seconds, so the numbers stay comparable."""

        return {
            "schema_version": 1,
            "run": {
                "used_seconds": int(self._spent_total),
                "limit_seconds": self.run_seconds,
            },
            "steps": {
                step: {
                    "used_seconds": int(seconds),
                    "limit_seconds": self.step_seconds,
                }
                for step, seconds in sorted(self._spent_by_step.items())
            },
        }


def uses_command_budget(input_sha256s: Mapping[str, Any]) -> bool:
    """Whether this frozen run replaced its counters with the two clocks."""

    return BUDGETS_CAPABILITY_PATH in input_sha256s


class LifetimeBudget(CommandBudget):
    """Native execution allowance, reserved durably before each launch.

    The host owns IO and the exclusive run lock. An uncatchable death leaves
    the full reservation charged; resume never grants a fresh allowance.
    """

    def __init__(self, *, clock: Callable[[], float] = time.monotonic):
        super().__init__(LIFETIME_STEP_SECONDS, LIFETIME_RUN_SECONDS, clock)

    def restore(self, value: Mapping[str, Any]) -> None:
        if not isinstance(value, Mapping) or set(value) != {"schema_version", "run", "steps"} or type(value["schema_version"]) is not int or value["schema_version"] != 1:
            raise ContractError("invalid lifetime budget record")
        steps = value["steps"]
        if not isinstance(steps, dict) or set(steps) - {"match", "invent", "make", "playtest", "release"}:
            raise ContractError("invalid lifetime budget stages")
        spent = {}
        for stage, record in steps.items():
            if not isinstance(record, dict) or set(record) != {"used_seconds", "limit_seconds"}:
                raise ContractError("invalid lifetime stage budget")
            seconds = record["used_seconds"]
            if type(seconds) is not int or not 0 <= seconds <= self.step_seconds or record["limit_seconds"] != self.step_seconds:
                raise ContractError("invalid lifetime budget spend")
            spent[stage] = seconds
        total = sum(spent.values())
        if total > self.run_seconds or value["run"] != {"used_seconds": total, "limit_seconds": self.run_seconds}:
            raise ContractError("inconsistent lifetime budget total")
        self._spent_by_step = spent
        self._spent_total = total

    def reserve(self, stage: str, seconds: int) -> None:
        if type(seconds) is not int or not 0 < seconds <= self.remaining(stage):
            raise ContractError("native turn exceeds lifetime allowance")
        self.spend(stage, seconds)

    def settle(self, stage: str, reserved: int, elapsed: float) -> None:
        if type(reserved) is not int or not 0 < reserved <= self.spent(stage) or type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
            raise ContractError("invalid lifetime reservation settlement")
        # Round upward: repeated short turns must not escape accounting.
        actual = min(reserved, max(0, math.ceil(elapsed)))
        self._spent_by_step[stage] -= reserved - actual
        self._spent_total -= reserved - actual

    def exhausted_message(self, step: str, which: str, product_id: str) -> str:
        return (
            "This toy exhausted its persistent %s native-execution budget; "
            "artifacts remain checkpointed. Resume does not reset the allowance."
            % which
        )


class LifetimeTurnBudget(LifetimeBudget):
    """Count host launches, not model messages, tools, tokens, or elapsed time.

    Reserve before launch and never refund a crash or short turn. The inherited
    clock is diagnostic only; each launcher retains its frozen watchdog.
    """

    def __init__(self):
        super().__init__()
        self.used_by_stage: Dict[str, int] = {}
        self.previous_time_budget = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 2,
            "unit": "native_turns",
            "run": {"used_turns": sum(self.used_by_stage.values()), "limit_turns": PRODUCT_TURN_LIMIT},
            "steps": {
                stage: {"used_turns": used, "limit_turns": STAGE_TURN_LIMIT}
                for stage, used in sorted(self.used_by_stage.items())
            },
            "previous_time_budget": self.previous_time_budget,
        }

    def restore(self, value: Mapping[str, Any]) -> None:
        if (
            not isinstance(value, dict)
            or set(value) != {"schema_version", "unit", "run", "steps", "previous_time_budget"}
            or type(value["schema_version"]) is not int
            or value["schema_version"] != 2
            or value["unit"] != "native_turns"
            or not isinstance(value["steps"], dict)
            or set(value["steps"]) - {"match", "invent", "make", "playtest", "release"}
        ):
            raise ContractError("invalid persistent turn budget")
        counts = {}
        for stage, entry in value["steps"].items():
            if (
                not isinstance(entry, dict)
                or set(entry) != {"used_turns", "limit_turns"}
                or type(entry["used_turns"]) is not int
                or not 0 <= entry["used_turns"] <= STAGE_TURN_LIMIT
                or type(entry["limit_turns"]) is not int
                or entry["limit_turns"] != STAGE_TURN_LIMIT
            ):
                raise ContractError("invalid persistent stage turn count")
            counts[stage] = entry["used_turns"]
        total = sum(counts.values())
        run = value["run"]
        if (
            total > PRODUCT_TURN_LIMIT
            or not isinstance(run, dict)
            or any(type(v) is not int for v in run.values())
            or run != {"used_turns": total, "limit_turns": PRODUCT_TURN_LIMIT}
        ):
            raise ContractError("inconsistent persistent turn total")
        previous = value["previous_time_budget"]
        if previous is not None:
            LifetimeBudget().restore(previous)
        self.used_by_stage = counts
        self.previous_time_budget = previous

    def exhausted(self, step: str) -> Optional[str]:
        if sum(self.used_by_stage.values()) >= PRODUCT_TURN_LIMIT:
            return "run"
        if self.used_by_stage.get(step, 0) >= STAGE_TURN_LIMIT:
            return "step"
        return None

    def turn_timeout_seconds(self, step: str) -> int:
        return MAX_TURN_SECONDS

    def reserve(self, stage: str, seconds: int) -> None:
        if stage not in {"match", "invent", "make", "playtest", "release"} or self.exhausted(stage):
            raise ContractError("native turn exceeds persistent turn allowance")
        self.used_by_stage[stage] = self.used_by_stage.get(stage, 0) + 1

    def settle(self, stage: str, reserved: int, elapsed: float) -> None:
        # Launches remain charged, including timeout, error and cancellation.
        pass

    def exhausted_message(self, step: str, which: str, product_id: str) -> str:
        return (
            "This toy exhausted its persistent %s native-turn budget; "
            "artifacts remain checkpointed. Resume does not reset the allowance."
            % which
        )


__all__ = [
    "BUDGETS_CAPABILITY_PATH",
    "LIFETIME_BUDGETS_CAPABILITY_PATH",
    "LIFETIME_STEP_SECONDS",
    "LIFETIME_RUN_SECONDS",
    "LifetimeBudget",
    "LifetimeTurnBudget",
    "TURN_BUDGETS_CAPABILITY_PATH",
    "STAGE_TURN_LIMIT",
    "PRODUCT_TURN_LIMIT",
    "MAX_BUDGETED_TURNS",
    "MAX_TURN_SECONDS",
    "MIN_TURN_SECONDS",
    "MIN_USEFUL_TURN_SECONDS",
    "RUN_BUDGET_SECONDS",
    "SPARK_BUDGETED_TURN_SECONDS",
    "STEP_BUDGET_SECONDS",
    "CommandBudget",
    "uses_command_budget",
]
