"""Fail-closed bridge from Alice's release packet to Inventor Foundation.

Alice keeps her mature release state machine and production-manifest hash. At
the final publication-preparation boundary, this module asks ``inventor_core``
to independently build its content-addressed manifest and canonical ZIP. The
ZIP is reconstructable from the durable Alice task result, so only its binding
is persisted; the temporary bytes are never treated as a second source of
truth.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

import inventor_core
from inventor_core.artifacts import build_artifact_manifest, build_publish_packet
from inventor_core.errors import ArtifactError


CORE_PACKET_SCHEMA_VERSION = 1
CORE_PACKET_SOURCE_PATH = "publication.json"


class CoreIntegrationError(ValueError):
    """Alice's publication packet could not satisfy the Foundation contract."""


def _canonical_bytes(packet: Mapping[str, Any]) -> bytes:
    if not isinstance(packet, Mapping):
        raise CoreIntegrationError("publication packet must be an object")
    try:
        return json.dumps(
            packet,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CoreIntegrationError(
            "publication packet must contain finite JSON values"
        ) from exc


def build_core_packet_binding(
    packet: Mapping[str, Any], *, alice_packet_sha256: str
) -> dict[str, Any]:
    """Build and identify the exact core packet corresponding to Alice bytes.

    ``publication.json`` deliberately contains the exact canonical bytes Alice
    already hashes. This creates a parity assertion, not a competing packet
    identity: the source entry SHA-256 must equal ``alice_packet_sha256``.
    """

    source = _canonical_bytes(packet)
    source_sha256 = hashlib.sha256(source).hexdigest()
    if source_sha256 != alice_packet_sha256:
        raise CoreIntegrationError(
            "core publication source does not match Alice's packet hash"
        )

    try:
        with tempfile.TemporaryDirectory(prefix="alice-core-packet-") as directory:
            staging = Path(directory)
            source_root = staging / "source"
            source_root.mkdir(mode=0o700)
            (source_root / CORE_PACKET_SOURCE_PATH).write_bytes(source)
            manifest = build_artifact_manifest(
                source_root,
                created_at="content-addressed",
            )
            packet_identity = build_publish_packet(
                source_root,
                staging / "publication.zip",
            )
    except (ArtifactError, OSError) as exc:
        raise CoreIntegrationError(
            "Foundation rejected Alice's publication packet: %s" % exc
        ) from exc

    if (
        len(manifest.entries) != 1
        or manifest.entries[0].path != CORE_PACKET_SOURCE_PATH
        or manifest.entries[0].sha256 != alice_packet_sha256
        or packet_identity["artifact_sha256"] != manifest.artifact_sha256
        or packet_identity["entries"] != 2
    ):
        raise CoreIntegrationError(
            "Foundation packet identity is inconsistent with Alice's packet"
        )

    return {
        "schema_version": CORE_PACKET_SCHEMA_VERSION,
        "core_version": inventor_core.__version__,
        "source_path": CORE_PACKET_SOURCE_PATH,
        "source_sha256": source_sha256,
        "artifact_sha256": manifest.artifact_sha256,
        "artifact_manifest": manifest.to_dict(),
        "packet_sha256": packet_identity["packet_sha256"],
        "packet_bytes": packet_identity["bytes"],
        "packet_entries": packet_identity["entries"],
    }


def validate_core_packet_binding(
    packet: Mapping[str, Any],
    *,
    alice_packet_sha256: str,
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Rebuild Foundation's deterministic packet and compare the complete binding."""

    if not isinstance(binding, Mapping):
        raise CoreIntegrationError("publication wrapper lacks a core packet binding")
    expected = build_core_packet_binding(
        packet,
        alice_packet_sha256=alice_packet_sha256,
    )
    if dict(binding) != expected:
        raise CoreIntegrationError(
            "stored core packet binding does not match the publication packet"
        )
    return expected


__all__ = [
    "CORE_PACKET_SCHEMA_VERSION",
    "CoreIntegrationError",
    "build_core_packet_binding",
    "validate_core_packet_binding",
]
