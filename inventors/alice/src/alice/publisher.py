"""Idempotent publication boundary for Factory and the Alice catalog."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class PublicationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PublicationPacket:
    candidate_id: str
    slug: str
    version: int
    title: str
    one_line: str
    rules: dict[str, Any]
    components: tuple[dict[str, Any], ...]
    evidence_summary: dict[str, Any]
    manufacturing: dict[str, Any]
    price: dict[str, Any]
    assets: tuple[dict[str, Any], ...] = ()

    def validate(self) -> None:
        if not self.candidate_id or not SLUG_PATTERN.fullmatch(self.slug):
            raise PublicationError("candidate_id and a URL-safe slug are required")
        if self.version < 1 or not self.title.strip() or not self.one_line.strip():
            raise PublicationError("version, title, and one_line are required")
        for field_name in ("setup", "turn", "end", "scoring", "ties"):
            if not self.rules.get(field_name):
                raise PublicationError(f"rules.{field_name} is required")
        if not self.components:
            raise PublicationError("at least one physical component is required")

    def canonical_json(self) -> str:
        self.validate()
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    @property
    def packet_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class PublicationReceipt:
    status: str
    mode: str
    packet_hash: str
    idempotency_key: str
    external_id: str | None = None
    url: str | None = None
    detail: dict[str, Any] | None = None


class Publisher:
    """Legacy dry-run packet writer; Factory effects live only in Vibe."""

    def __init__(
        self,
        outbox: str | Path,
        *,
        mode: str = "dry-run",
        command: Sequence[str] = (),
        timeout_seconds: int = 600,
        allowed_environment: Sequence[str] = ("PATH", "HOME"),
    ) -> None:
        if mode != "dry-run":
            raise ValueError(
                "legacy Publisher is dry-run only; draft/live effects must use "
                "the bound VibePublishingAdapter"
            )
        if command:
            raise ValueError("legacy Publisher does not accept an effect command")
        del timeout_seconds, allowed_environment
        self.outbox = Path(outbox)
        self.mode = mode

    def publish(self, packet: PublicationPacket) -> PublicationReceipt:
        encoded = packet.canonical_json()
        packet_hash = packet.packet_hash
        idempotency_key = f"alice:{packet.candidate_id}:v{packet.version}:{packet_hash}"
        packet_dir = self.outbox / packet.slug / f"v{packet.version}-{packet_hash[:12]}"
        packet_path = packet_dir / "publication.json"
        file_content = encoded + "\n"
        packet_dir.mkdir(parents=True, exist_ok=True)
        if packet_path.exists():
            current_hash = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            if current_hash != hashlib.sha256(file_content.encode("utf-8")).hexdigest():
                raise PublicationError("immutable outbox packet changed at an existing path")
        else:
            _atomic_write(packet_path, file_content)

        receipt = PublicationReceipt(
            status="prepared",
            mode=self.mode,
            packet_hash=packet_hash,
            idempotency_key=idempotency_key,
            detail={"packet_path": str(packet_path)},
        )
        _write_receipt(packet_dir / "receipt.json", receipt)
        return receipt


def _atomic_write(path: Path, content: str) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temp_name = handle.name
    os.replace(temp_name, path)


def _write_receipt(path: Path, receipt: PublicationReceipt) -> None:
    encoded = json.dumps(asdict(receipt), sort_keys=True, indent=2) + "\n"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("packet_hash") == receipt.packet_hash and existing.get("status") in {
            "published",
            "exists",
        }:
            return
    _atomic_write(path, encoded)
