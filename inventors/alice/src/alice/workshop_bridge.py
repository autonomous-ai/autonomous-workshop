"""Fail-closed Pack bridge from Alice to Workshop.

Alice keeps her mature inspection policy and production-manifest hash. At the
Pack boundary this module asks ``workshop`` to seal the exact manifest,
build the canonical archive, and inspect those archive bytes again. Only the
binding is persisted; temporary Pack bytes never become a second authority.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

import workshop
from workshop.artifacts.pack import inspect_pack, pack_artifact, seal_artifact
from workshop.errors import WorkshopError


WORKSHOP_PACK_SCHEMA_VERSION = 3
WORKSHOP_PACK_SOURCE_PATH = "product.json"
_LEGACY_SOURCE_PATH = "publication.json"
# Compatibility constants are readable by old extensions but intentionally not
# exported from the canonical module surface.
WORKSHOP_PACKET_SCHEMA_VERSION = WORKSHOP_PACK_SCHEMA_VERSION
WORKSHOP_PACKET_SOURCE_PATH = WORKSHOP_PACK_SOURCE_PATH


class WorkshopBridgeError(ValueError):
    """Alice's inspected product could not satisfy Workshop's Pack contract."""


def _canonical_bytes(product: Mapping[str, Any]) -> bytes:
    if not isinstance(product, Mapping):
        raise WorkshopBridgeError("inspected product must be an object")
    try:
        return json.dumps(
            product,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise WorkshopBridgeError(
            "inspected product must contain finite JSON values"
        ) from exc


def _pack_binding(
    product: Mapping[str, Any],
    *,
    alice_product_sha256: str,
    source_path: str,
) -> dict[str, Any]:
    source = _canonical_bytes(product)
    source_sha256 = hashlib.sha256(source).hexdigest()
    if source_sha256 != alice_product_sha256:
        raise WorkshopBridgeError(
            "Workshop Pack source does not match Alice's inspected product hash"
        )

    try:
        with tempfile.TemporaryDirectory(prefix="alice-workshop-pack-") as directory:
            staging = Path(directory)
            source_root = staging / "source"
            source_root.mkdir(mode=0o700)
            (source_root / source_path).write_bytes(source)
            manifest = seal_artifact(
                source_root,
                created_at="content-addressed",
            )
            packed = pack_artifact(source_root, staging / "product.zip")
            inspected = inspect_pack(packed.path)
    except (OSError, WorkshopError) as exc:
        raise WorkshopBridgeError(
            "Workshop rejected Alice's inspected product: %s" % exc
        ) from exc

    if (
        len(manifest.entries) != 1
        or manifest.entries[0].path != source_path
        or manifest.entries[0].sha256 != alice_product_sha256
        or packed != inspected
        or packed.artifact_sha256 != manifest.artifact_sha256
        or packed.entries != 2
    ):
        raise WorkshopBridgeError(
            "Workshop Pack identity is inconsistent with Alice's inspected product"
        )

    return {
        "source_path": source_path,
        "source_sha256": source_sha256,
        "artifact_sha256": manifest.artifact_sha256,
        "artifact_manifest": manifest.to_dict(),
        "pack_sha256": packed.pack_sha256,
        "pack_bytes": packed.bytes,
        "pack_entries": packed.entries,
    }


def build_workshop_pack_binding(
    product: Mapping[str, Any], *, alice_product_sha256: str
) -> dict[str, Any]:
    """Pack Alice's exact inspected product and return its durable identity."""

    return {
        "schema_version": WORKSHOP_PACK_SCHEMA_VERSION,
        "workshop_version": workshop.__version__,
        **_pack_binding(
            product,
            alice_product_sha256=alice_product_sha256,
            source_path=WORKSHOP_PACK_SOURCE_PATH,
        ),
    }


def _validate_legacy_binding(
    product: Mapping[str, Any],
    *,
    alice_product_sha256: str,
    binding: Mapping[str, Any],
) -> None:
    schema_version = binding.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version not in (1, 2)
    ):
        raise WorkshopBridgeError("unsupported legacy Workshop binding schema")
    version_keys = {
        1: ("core_version",),
        2: ("foundation_version", "workshop_version"),
    }[schema_version]
    present_versions = [key for key in version_keys if key in binding]
    if len(present_versions) != 1:
        raise WorkshopBridgeError("legacy Workshop binding has ambiguous version names")
    version = binding[present_versions[0]]
    if not isinstance(version, str) or not version.strip():
        raise WorkshopBridgeError("legacy Workshop binding version is invalid")

    legacy = _pack_binding(
        product,
        alice_product_sha256=alice_product_sha256,
        source_path=_LEGACY_SOURCE_PATH,
    )
    expected = {
        "schema_version": schema_version,
        present_versions[0]: version,
        "source_path": legacy["source_path"],
        "source_sha256": legacy["source_sha256"],
        "artifact_sha256": legacy["artifact_sha256"],
        "artifact_manifest": legacy["artifact_manifest"],
        "packet_sha256": legacy["pack_sha256"],
        "packet_bytes": legacy["pack_bytes"],
        "packet_entries": legacy["pack_entries"],
    }
    if dict(binding) != expected:
        raise WorkshopBridgeError(
            "stored legacy Workshop binding does not match the inspected product"
        )


def validate_workshop_pack_binding(
    product: Mapping[str, Any],
    *,
    alice_product_sha256: str,
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Rebuild, inspect, and compare a current or deployed Pack binding."""

    if not isinstance(binding, Mapping):
        raise WorkshopBridgeError("send bundle lacks a Workshop Pack binding")
    if binding.get("schema_version") in (1, 2):
        _validate_legacy_binding(
            product,
            alice_product_sha256=alice_product_sha256,
            binding=binding,
        )
        return build_workshop_pack_binding(
            product,
            alice_product_sha256=alice_product_sha256,
        )

    expected = build_workshop_pack_binding(
        product,
        alice_product_sha256=alice_product_sha256,
    )
    if dict(binding) != expected:
        raise WorkshopBridgeError(
            "stored Workshop Pack binding does not match the inspected product"
        )
    return expected


# Read-only import compatibility for Alice states and extensions created before
# Workshop 0.3. Both wrappers emit/return the canonical v3 Pack shape.
def build_workshop_packet_binding(
    packet: Mapping[str, Any], *, alice_packet_sha256: str
) -> dict[str, Any]:
    return build_workshop_pack_binding(
        packet,
        alice_product_sha256=alice_packet_sha256,
    )


def validate_workshop_packet_binding(
    packet: Mapping[str, Any],
    *,
    alice_packet_sha256: str,
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    return validate_workshop_pack_binding(
        packet,
        alice_product_sha256=alice_packet_sha256,
        binding=binding,
    )


__all__ = [
    "WORKSHOP_PACK_SCHEMA_VERSION",
    "WorkshopBridgeError",
    "build_workshop_pack_binding",
    "validate_workshop_pack_binding",
]
