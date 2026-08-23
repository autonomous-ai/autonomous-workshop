import hashlib
import json
import unittest
from unittest.mock import patch

from inventor_core.artifacts import build_publish_packet as core_build_publish_packet

from alice.core_integration import (
    CoreIntegrationError,
    build_core_packet_binding,
    validate_core_packet_binding,
)


class CoreIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = {
            "candidate_id": "game-1",
            "candidate_version": 4,
            "title": "Café Council",
            "price": {"currency": "USD", "price_cents": 4900},
        }
        encoded = json.dumps(
            self.packet,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        self.alice_hash = hashlib.sha256(encoded).hexdigest()

    def test_binding_executes_core_and_preserves_alice_hash_parity(self) -> None:
        with patch(
            "alice.core_integration.build_publish_packet",
            wraps=core_build_publish_packet,
        ) as core_builder:
            binding = build_core_packet_binding(
                self.packet,
                alice_packet_sha256=self.alice_hash,
            )

        core_builder.assert_called_once()
        self.assertEqual(binding["source_sha256"], self.alice_hash)
        self.assertEqual(
            binding["artifact_manifest"]["entries"],
            [
                {
                    "path": "publication.json",
                    "bytes": len(
                        json.dumps(
                            self.packet,
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                            allow_nan=False,
                        ).encode("utf-8")
                    ),
                    "sha256": self.alice_hash,
                    "executable": False,
                }
            ],
        )
        self.assertEqual(binding["packet_entries"], 2)

    def test_binding_is_deterministic_and_revalidated(self) -> None:
        first = build_core_packet_binding(
            self.packet,
            alice_packet_sha256=self.alice_hash,
        )
        second = validate_core_packet_binding(
            self.packet,
            alice_packet_sha256=self.alice_hash,
            binding=first,
        )
        self.assertEqual(first, second)

    def test_tampered_binding_fails_closed(self) -> None:
        binding = build_core_packet_binding(
            self.packet,
            alice_packet_sha256=self.alice_hash,
        )
        binding["artifact_sha256"] = "0" * 64
        with self.assertRaisesRegex(CoreIntegrationError, "does not match"):
            validate_core_packet_binding(
                self.packet,
                alice_packet_sha256=self.alice_hash,
                binding=binding,
            )

    def test_alice_hash_mismatch_fails_before_core_packet_creation(self) -> None:
        with patch("alice.core_integration.build_publish_packet") as core_builder:
            with self.assertRaisesRegex(CoreIntegrationError, "Alice's packet hash"):
                build_core_packet_binding(
                    self.packet,
                    alice_packet_sha256="0" * 64,
                )
        core_builder.assert_not_called()


if __name__ == "__main__":
    unittest.main()
