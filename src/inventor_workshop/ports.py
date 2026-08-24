"""Adapter boundaries: Workshop defines evidence shapes, inventors choose tools."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional, Protocol, Sequence

from .cad import CadReleaseBundle
from .models import GateResult, PublicationOutcome
from .models import PublicationReceipt

if TYPE_CHECKING:
    from .creation import CadBuildResult, CreationBrief


class AgentPort(Protocol):
    def run(self, role: str, request: Mapping[str, Any], budget_micros: int) -> Mapping[str, Any]:
        ...


class CadPort(Protocol):
    def build(
        self,
        brief: "CreationBrief",
        concept: Mapping[str, Any],
        workspace: Path,
    ) -> "CadBuildResult":
        ...


class CadVerifierPort(Protocol):
    def verify(self, artifact_root: Path, artifact_sha256: str) -> CadReleaseBundle:
        ...


class EvaluatorPort(Protocol):
    def evaluate(self, artifact_root: Path, artifact_sha256: str) -> Sequence[GateResult]:
        ...


class LaunchPort(Protocol):
    def import_draft(
        self,
        product_id: str,
        packet: Path,
        metadata: Mapping[str, Any],
        lease_token: Optional[str] = None,
        *,
        inventor_name: Optional[str] = None,
    ) -> PublicationOutcome:
        ...

    def reconcile_import(self, intent_id: str, remote_slug: str) -> PublicationReceipt:
        ...

    def publish_live(
        self,
        intent_id: str,
        price_cents: int,
        lease_token: Optional[str] = None,
    ) -> PublicationReceipt:
        ...

    def reconcile_live(self, intent_id: str) -> PublicationReceipt:
        ...


class DeliveryPort(Protocol):
    def quote(self, artifact_root: Path, material: str) -> Mapping[str, Any]:
        ...
