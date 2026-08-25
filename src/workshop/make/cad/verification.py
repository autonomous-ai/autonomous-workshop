"""Public verification seam for the repository-pinned Make CAD project.

Playtest must be able to authenticate and recheck exact Make bytes without
depending on Make's agent implementation class.  This module keeps that
boundary deliberately small: callers can validate a design action, derive the
canonical generated sources, or request an opaque verifier through a protocol.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, Sequence


LOCKED_CAD_GENERATOR_ID = "workshop-locked-step-cad"
LOCKED_CAD_GENERATOR_VERSION = "2.1.0"


class CadVerificationBuild(Protocol):
    """Result shape returned by a pinned CAD verifier."""

    root: Path
    observation: Mapping[str, Any]


class CadProjectVerifier(Protocol):
    """Operations Playtest may invoke against an isolated CAD project copy."""

    def verify(
        self,
        action: Mapping[str, Any],
        *,
        lane: Optional[str],
        root: Path,
        groups: Sequence[str],
    ) -> CadVerificationBuild:
        ...

    def check_motion(self, *args: Any, **kwargs: Any) -> Any:
        ...


def validate_cad_design_action(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate the canonical primitive CAD action emitted by Make.

    The implementation remains private to the Make agent for compatibility;
    this function is the stable component boundary used by Playtest.
    """

    from workshop.make.agent import _validate_action

    return _validate_action(value)


def canonical_cad_project_sources(
    action: Mapping[str, Any],
) -> Mapping[str, str]:
    """Return the exact executable source inventory for a Make CAD action."""

    from workshop.make.agent import LockedCadSkillBuilder

    return dict(LockedCadSkillBuilder._project_sources(action))


def locked_cad_project_verifier() -> CadProjectVerifier:
    """Construct the opaque repository-pinned CAD verifier."""

    from workshop.make.agent import LockedCadSkillBuilder

    return LockedCadSkillBuilder()


__all__ = [
    "CadProjectVerifier",
    "CadVerificationBuild",
    "LOCKED_CAD_GENERATOR_ID",
    "LOCKED_CAD_GENERATOR_VERSION",
    "canonical_cad_project_sources",
    "locked_cad_project_verifier",
    "validate_cad_design_action",
]
