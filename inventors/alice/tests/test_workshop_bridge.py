import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from inventor_workshop.pack import (
    pack_artifact as workshop_pack_artifact,
    seal_artifact,
)

from alice.workshop_bridge import (
    WorkshopBridgeError,
    build_workshop_pack_binding,
    validate_workshop_pack_binding,
)


class WorkshopBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.product = {
            "candidate_id": "game-1",
            "candidate_version": 4,
            "title": "Café Council",
            "price": {"currency": "USD", "price_cents": 4900},
        }
        self.encoded = json.dumps(
            self.product,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        self.alice_hash = hashlib.sha256(self.encoded).hexdigest()

    def legacy_binding(self, schema: int, version_key: str) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            root.mkdir()
            (root / "publication.json").write_bytes(self.encoded)
            manifest = seal_artifact(root, created_at="content-addressed")
            packed = workshop_pack_artifact(root, Path(directory) / "publication.zip")
        return {
            "schema_version": schema,
            version_key: "0.2.0" if schema == 2 else "0.1.0",
            "source_path": "publication.json",
            "source_sha256": self.alice_hash,
            "artifact_sha256": manifest.artifact_sha256,
            "artifact_manifest": manifest.to_dict(),
            "packet_sha256": packed.pack_sha256,
            "packet_bytes": packed.bytes,
            "packet_entries": packed.entries,
        }

    def test_binding_executes_pack_and_preserves_alice_hash_parity(self) -> None:
        with patch(
            "alice.workshop_bridge.pack_artifact",
            wraps=workshop_pack_artifact,
        ) as packer:
            binding = build_workshop_pack_binding(
                self.product,
                alice_product_sha256=self.alice_hash,
            )

        packer.assert_called_once()
        self.assertEqual(binding["schema_version"], 3)
        self.assertEqual(binding["source_sha256"], self.alice_hash)
        self.assertEqual(
            binding["artifact_manifest"]["entries"],
            [
                {
                    "path": "product.json",
                    "bytes": len(self.encoded),
                    "sha256": self.alice_hash,
                    "executable": False,
                }
            ],
        )
        self.assertEqual(binding["pack_entries"], 2)

    def test_binding_is_deterministic_and_reinspected(self) -> None:
        first = build_workshop_pack_binding(
            self.product,
            alice_product_sha256=self.alice_hash,
        )
        second = validate_workshop_pack_binding(
            self.product,
            alice_product_sha256=self.alice_hash,
            binding=first,
        )
        self.assertEqual(first, second)

    def test_core_foundation_and_early_workshop_bindings_are_read_only(self) -> None:
        current = build_workshop_pack_binding(
            self.product,
            alice_product_sha256=self.alice_hash,
        )
        cases = (
            self.legacy_binding(1, "core_version"),
            self.legacy_binding(2, "foundation_version"),
            self.legacy_binding(2, "workshop_version"),
        )
        for legacy in cases:
            with self.subTest(binding=legacy):
                normalized = validate_workshop_pack_binding(
                    self.product,
                    alice_product_sha256=self.alice_hash,
                    binding=legacy,
                )
                self.assertEqual(normalized, current)

    def test_tampered_binding_fails_closed(self) -> None:
        binding = build_workshop_pack_binding(
            self.product,
            alice_product_sha256=self.alice_hash,
        )
        binding["artifact_sha256"] = "0" * 64
        with self.assertRaisesRegex(WorkshopBridgeError, "does not match"):
            validate_workshop_pack_binding(
                self.product,
                alice_product_sha256=self.alice_hash,
                binding=binding,
            )

    def test_boolean_schema_cannot_impersonate_a_legacy_binding(self) -> None:
        binding = self.legacy_binding(1, "core_version")
        binding["schema_version"] = True
        with self.assertRaisesRegex(WorkshopBridgeError, "unsupported legacy"):
            validate_workshop_pack_binding(
                self.product,
                alice_product_sha256=self.alice_hash,
                binding=binding,
            )

    def test_alice_hash_mismatch_fails_before_workshop_pack(self) -> None:
        with patch("alice.workshop_bridge.pack_artifact") as packer:
            with self.assertRaisesRegex(WorkshopBridgeError, "inspected product hash"):
                build_workshop_pack_binding(
                    self.product,
                    alice_product_sha256="0" * 64,
                )
        packer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
