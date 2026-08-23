"""Adapter boundaries: core defines evidence shapes, inventors choose tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, Sequence

from .cad import CadReleaseBundle
from .models import GateResult, PublicationOutcome
from .models import PublicationReceipt


class AgentPort(Protocol):
    def run(self, role: str, request: Mapping[str, Any], budget_micros: int) -> Mapping[str, Any]:
        ...


class CadPort(Protocol):
    def build(self, brief: Mapping[str, Any], workspace: Path) -> Mapping[str, Any]:
        ...


class CadVerifierPort(Protocol):
    def verify(self, artifact_root: Path, artifact_sha256: str) -> CadReleaseBundle:
        ...


class EvaluatorPort(Protocol):
    def evaluate(self, artifact_root: Path, artifact_sha256: str) -> Sequence[GateResult]:
        ...


class PublisherPort(Protocol):
    def import_draft(
        self,
        product_id: str,
        packet: Path,
        metadata: Mapping[str, Any],
        lease_token: Optional[str] = None,
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


class FulfillmentPort(Protocol):
    def quote(self, artifact_root: Path, material: str) -> Mapping[str, Any]:
        ...
