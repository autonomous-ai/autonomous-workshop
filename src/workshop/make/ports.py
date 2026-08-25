"""Ports declared by Make for replaceable creative and verification tools."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Protocol, Sequence

from workshop.make.cad import CadReleaseBundle

if TYPE_CHECKING:
    from workshop.make.service import CadBuildResult
    from workshop.playtest import PlaytestResult
    from workshop.wish import Wish


class ModelDoor(Protocol):
    """Run one bounded model or agent role."""

    def run(
        self,
        role: str,
        request: Mapping[str, Any],
        budget_micros: int,
    ) -> Mapping[str, Any]:
        ...


class CadDoor(Protocol):
    """Turn an accepted concept into product artifact files."""

    def build(
        self,
        wish: "Wish",
        concept: Mapping[str, Any],
        workspace: Path,
    ) -> "CadBuildResult":
        ...


class CadInspectionDoor(Protocol):
    """Verify CAD and manufacturing evidence for exact artifact bytes."""

    def verify(
        self,
        artifact_root: Path,
        artifact_sha256: str,
    ) -> CadReleaseBundle:
        ...


class InspectionDoor(Protocol):
    """Evaluate a Make artifact without choosing the next lifecycle stage."""

    def inspect(
        self,
        artifact_root: Path,
        artifact_sha256: str,
    ) -> Sequence["PlaytestResult"]:
        ...


__all__ = [
    "CadDoor",
    "CadInspectionDoor",
    "InspectionDoor",
    "ModelDoor",
]
