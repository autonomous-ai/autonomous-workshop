"""Frozen selectable effort routes for new Workshop product runs.

Effort is deterministic lifecycle policy, not an agent persona or a Python
reasoning loop.  Optional stages pass through by selecting the next enabled
stage in the canonical sequence; skipped stages do not receive native turns,
artifacts, gates, or fabricated evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from workshop.errors import ContractError


EFFORT_ROUTE_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/effort-routes-v1.md"
)
SPARK_ECONOMICS_V1_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/spark-economics-v1.md"
)
SPARK_ECONOMICS_V2_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/spark-economics-v2.md"
)
SPARK_ECONOMICS_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/spark-economics-v3.md"
)
DEEP_ECONOMICS_V1_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v1.md"
)
DEEP_ECONOMICS_V2_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v2.md"
)
DEEP_ECONOMICS_V3_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v3.md"
)
DEEP_ECONOMICS_V4_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v4.md"
)
DEEP_ECONOMICS_V5_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v5.md"
)
DEEP_ECONOMICS_V6_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v6.md"
)
DEEP_ECONOMICS_V7_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v7.md"
)
DEEP_ECONOMICS_V8_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v8.md"
)
DEEP_ECONOMICS_V9_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v9.md"
)
DEEP_ECONOMICS_V10_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v10.md"
)
DEEP_ECONOMICS_V11_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v11.md"
)
DEEP_ECONOMICS_V12_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v12.md"
)
DEEP_ECONOMICS_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/deep-economics-v13.md"
)
SPARK_AUTO_COMPACT_TOKEN_LIMIT = 64_000
SPARK_NATIVE_TURN_TIMEOUT_SECONDS = 20 * 60
DEEP_V1_AUTO_COMPACT_TOKEN_LIMIT = 32_000
DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT = 24_000
DEEP_AUTO_COMPACT_TOKEN_LIMIT = 256_000
DEEP_MAKE_AUTO_COMPACT_TOKEN_LIMIT = 16_000
DEEP_NATIVE_TURN_TIMEOUT_SECONDS = 30 * 60
DEEP_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS = 12 * 60
DEEP_V5_INITIAL_INVENT_TIMEOUT_SECONDS = 20 * 60
DEEP_V5_INVENT_RECOVERY_TIMEOUT_SECONDS = 10 * 60
DEEP_V5_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS = 8 * 60
DEEP_V8_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS = 16 * 60
DEEP_V10_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS = 15 * 60
DEEP_V11_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS = 15 * 60
DEEP_V12_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS = 15 * 60
DEEP_V13_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS = 15 * 60
DEEP_V1_NATIVE_TURN_LIMIT = 8
DEEP_NATIVE_TURN_LIMIT = 8
DEFAULT_WORKSHOP_EFFORT = "spark"
_CANONICAL_OPTIONAL_SEQUENCE = ("invent", "make", "playtest", "release")


@dataclass(frozen=True)
class WorkshopEffort:
    """One public effort name and its exact enabled cognitive stages."""

    name: str
    title: str
    description: str
    enabled_stages: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ContractError("Workshop effort name must be non-empty text")
        if not isinstance(self.title, str) or not self.title:
            raise ContractError("Workshop effort title must be non-empty text")
        if not isinstance(self.description, str) or not self.description:
            raise ContractError("Workshop effort description must be non-empty text")
        enabled = tuple(self.enabled_stages)
        if (
            not enabled
            or enabled[-1] != "release"
            or "make" not in enabled
            or any(stage not in _CANONICAL_OPTIONAL_SEQUENCE for stage in enabled)
            or tuple(
                stage for stage in _CANONICAL_OPTIONAL_SEQUENCE if stage in enabled
            )
            != enabled
        ):
            raise ContractError("Workshop effort stages must be canonical and releasable")
        object.__setattr__(self, "enabled_stages", enabled)

    @property
    def lifecycle(self) -> tuple[str, ...]:
        return ("wish", *self.enabled_stages)

    def includes(self, stage: str) -> bool:
        return stage in self.enabled_stages

    def next_stage(self, stage: str) -> str:
        """Pass through disabled stages and return the next enabled boundary."""

        if stage == "release":
            return "complete"
        if stage == "wish":
            start = 0
        else:
            if stage not in _CANONICAL_OPTIONAL_SEQUENCE:
                raise ContractError("Workshop effort cannot route unknown stage")
            start = _CANONICAL_OPTIONAL_SEQUENCE.index(stage) + 1
        for candidate in _CANONICAL_OPTIONAL_SEQUENCE[start:]:
            if candidate in self.enabled_stages:
                return candidate
        raise ContractError("Workshop effort has no downstream stage")

    def previous_stage(self, stage: str) -> str:
        """Return the nearest enabled predecessor across optional stages."""

        if stage not in self.enabled_stages:
            raise ContractError("Workshop effort cannot route disabled stage")
        position = self.enabled_stages.index(stage)
        return "wish" if position == 0 else self.enabled_stages[position - 1]


WORKSHOP_EFFORTS: Mapping[str, WorkshopEffort] = MappingProxyType({
    effort.name: effort
    for effort in (
        WorkshopEffort(
            name="spark",
            title="Spark",
            description="Fastest path: Wish -> Make -> Release.",
            enabled_stages=("make", "release"),
        ),
        WorkshopEffort(
            name="forge",
            title="Forge",
            description="Balanced path: Wish -> Invent -> Make -> Release.",
            enabled_stages=("invent", "make", "release"),
        ),
        WorkshopEffort(
            name="quest",
            title="Quest",
            description=(
                "Deepest path: Wish -> Invent -> Make -> Playtest -> Release."
            ),
            enabled_stages=("invent", "make", "playtest", "release"),
        ),
    )
})


def workshop_effort(value: Any) -> WorkshopEffort:
    if not isinstance(value, str) or value not in WORKSHOP_EFFORTS:
        raise ContractError(
            "Workshop effort must be one of: %s"
            % ", ".join(WORKSHOP_EFFORTS)
        )
    return WORKSHOP_EFFORTS[value]


__all__ = [
    "DEFAULT_WORKSHOP_EFFORT",
    "DEEP_AUTO_COMPACT_TOKEN_LIMIT",
    "DEEP_ECONOMICS_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V1_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V2_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V3_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V4_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V5_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V6_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V7_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V8_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V9_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V10_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V11_CAPABILITY_PATH",
    "DEEP_ECONOMICS_V12_CAPABILITY_PATH",
    "DEEP_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS",
    "DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT",
    "DEEP_MAKE_AUTO_COMPACT_TOKEN_LIMIT",
    "DEEP_NATIVE_TURN_LIMIT",
    "DEEP_NATIVE_TURN_TIMEOUT_SECONDS",
    "DEEP_V1_AUTO_COMPACT_TOKEN_LIMIT",
    "DEEP_V1_NATIVE_TURN_LIMIT",
    "DEEP_V5_INITIAL_INVENT_TIMEOUT_SECONDS",
    "DEEP_V5_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS",
    "DEEP_V5_INVENT_RECOVERY_TIMEOUT_SECONDS",
    "DEEP_V8_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS",
    "DEEP_V10_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS",
    "DEEP_V11_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS",
    "DEEP_V12_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS",
    "DEEP_V13_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS",
    "EFFORT_ROUTE_CAPABILITY_PATH",
    "SPARK_AUTO_COMPACT_TOKEN_LIMIT",
    "SPARK_ECONOMICS_CAPABILITY_PATH",
    "SPARK_ECONOMICS_V1_CAPABILITY_PATH",
    "SPARK_ECONOMICS_V2_CAPABILITY_PATH",
    "SPARK_NATIVE_TURN_TIMEOUT_SECONDS",
    "WORKSHOP_EFFORTS",
    "WorkshopEffort",
    "workshop_effort",
]
