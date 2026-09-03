"""Two clocks per toy: the whole timeout model for a budgeted native run.

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
# A step must afford more than one maximum-length turn, or a single timeout
# ends it and throws away work a resume would have finalized.  Two full turns
# matches the ceiling the retired two-timeout rail allowed.
STEP_BUDGET_SECONDS = 2 * 60 * 60
RUN_BUDGET_SECONDS = 6 * 60 * 60
# The runtime launchers refuse anything longer, so no turn may exceed it.
MAX_TURN_SECONDS = 60 * 60
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
        if not isinstance(seconds, (int, float)) or seconds < 0 or seconds != seconds:
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


__all__ = [
    "BUDGETS_CAPABILITY_PATH",
    "MAX_BUDGETED_TURNS",
    "MAX_TURN_SECONDS",
    "MIN_TURN_SECONDS",
    "MIN_USEFUL_TURN_SECONDS",
    "RUN_BUDGET_SECONDS",
    "STEP_BUDGET_SECONDS",
    "CommandBudget",
    "uses_command_budget",
]
