import hashlib
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from inventor_core.artifacts import build_publish_packet
from inventor_core.errors import AmbiguousPublishError, ContractError, PublishError
from inventor_core.panda import (
    HttpResponse,
    PandaClient,
    PandaPublicationCoordinator,
    _NoRedirectHandler,
    _load_packet,
    _validate_packet_bytes,
    inspect_publish_packet,
)
from inventor_core.store import InventorStore


class QueueTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, body, timeout))
        next_response = self.responses.pop(0)
        if isinstance(next_response, Exception):
            raise next_response
        return next_response


class PandaTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.packet = Path(self.temp.name) / "game.zip"
        product = Path(self.temp.name) / "product"
        product.mkdir()
        (product / "project.json").write_text('{"id":"game"}\n', encoding="utf-8")
        (product / "game.stl").write_text("solid game\nendsolid game\n", encoding="utf-8")
        build_publish_packet(product, self.packet)
        self.artifact_sha = _load_packet(self.packet)[2]
        self.store = InventorStore(Path(self.temp.name) / "state.sqlite")
        self.store.register_product("game", "reviewed", artifact_sha256=self.artifact_sha)

    def test_public_packet_inspection_returns_verified_identity(self):
        inspection = inspect_publish_packet(self.packet)
        self.assertEqual(inspection["bytes"], self.packet.stat().st_size)
        self.assertEqual(inspection["entries"], 3)
        self.assertEqual(inspection["artifact_sha256"], self.artifact_sha)
        self.assertEqual(
            inspection["packet_sha256"],
            hashlib.sha256(self.packet.read_bytes()).hexdigest(),
        )

    @staticmethod
    def design(status="draft", price_cents=4000):
        design = {
            "id": "d1",
            "slug": "game",
            "owner_id": "owner",
            "root_id": "d1",
            "current_history_id": "h1",
            "published_history_id": "h1" if status == "public" else None,
            "status": status,
            "project_url": "https://cdn.example/game/",
        }
        if status == "public":
            design["listing"] = {
                "active": True,
                "price_cents": price_cents,
                "currency": "USD",
                "sku": "GAME-001",
            }
        return design

    @staticmethod
    def response(status, body):
        return HttpResponse(status, {}, json.dumps(body).encode("utf-8"))

    @staticmethod
    def handcrafted_packet(path, entries, manifest_overrides=None):
        manifest_entries = [
            {
                "path": name,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "executable": False,
            }
            for name, content in sorted(entries.items())
        ]
        manifest = {
            "schema_version": 1,
            "artifact_sha256": hashlib.sha256(
                json.dumps(
                    manifest_entries,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            ).hexdigest(),
            "total_bytes": sum(len(content) for content in entries.values()),
            "created_at": "content-addressed",
            "entries": manifest_entries,
        }
        manifest.update(manifest_overrides or {})
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, content in list(sorted(entries.items())) + [
                (
                    "_inventor-artifact.json",
                    json.dumps(
                        manifest,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode("utf-8")
                    + b"\n",
                )
            ]:
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 3
                info.external_attr = (0o644 & 0xFFFF) << 16
                archive.writestr(info, content, compress_type=zipfile.ZIP_STORED)

    def coordinator(self, transport):
        return PandaPublicationCoordinator(
            self.store, PandaClient("token", transport=transport), "owner"
        )

    def intent_for_game(self):
        with self.store._connection() as connection:
            intent_id = connection.execute(
                "SELECT id FROM publish_intents WHERE product_id='game'"
            ).fetchone()[0]
        return self.store.get_publish_intent(intent_id)

    def test_draft_then_public_readback(self):
        transport = QueueTransport(
            [
                self.response(201, self.design("draft")),
                self.response(200, self.design("public")),
                self.response(200, self.design("public")),
            ]
        )
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})
        live = coordinator.publish_live(draft.intent_id, 4000)
        self.assertTrue(live.is_verified_public)
        self.assertEqual(
            self.store.get_publish_intent(draft.intent_id)["state"], "live"
        )
        self.assertEqual([call[0] for call in transport.calls], ["POST", "POST", "GET"])

    def test_transport_failure_is_unknown_and_blocks_retry(self):
        transport = QueueTransport([OSError("connection reset")])
        coordinator = self.coordinator(transport)
        with self.assertRaises(AmbiguousPublishError):
            coordinator.import_draft("game", self.packet, {"title": "Game"})
        with self.assertRaises(AmbiguousPublishError):
            coordinator.import_draft("game", self.packet, {"title": "Game"})
        self.assertEqual(len(transport.calls), 1)

    def test_malformed_accepted_import_becomes_reconcilable_unknown(self):
        transport = QueueTransport([HttpResponse(201, {}, b"not json")])
        coordinator = self.coordinator(transport)
        with self.assertRaises(AmbiguousPublishError):
            coordinator.import_draft("game", self.packet, {"title": "Game"})
        with self.assertRaises(AmbiguousPublishError):
            coordinator.import_draft("game", self.packet, {"title": "Game"})
        self.assertEqual(len(transport.calls), 1)

    def test_unexpected_success_or_redirect_never_authorizes_import_retry(self):
        for status in (202, 302):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as directory:
                    store = InventorStore(Path(directory) / "state.sqlite")
                    store.register_product(
                        "game", "reviewed", artifact_sha256=self.artifact_sha
                    )
                    transport = QueueTransport([HttpResponse(status, {}, b"")])
                    coordinator = PandaPublicationCoordinator(
                        store, PandaClient("token", transport=transport), "owner"
                    )
                    with self.assertRaises(AmbiguousPublishError):
                        coordinator.import_draft(
                            "game", self.packet, {"title": "Game"}
                        )
                    with store._connection() as connection:
                        intent_id = connection.execute(
                            "SELECT id FROM publish_intents"
                        ).fetchone()[0]
                    intent = store.get_publish_intent(intent_id)
                    self.assertEqual(intent["state"], "unknown")

    def test_unrelated_slug_cannot_reconcile_unknown_import(self):
        transport = QueueTransport([OSError("lost response")])
        coordinator = self.coordinator(transport)
        with self.assertRaises(AmbiguousPublishError):
            coordinator.import_draft("game", self.packet, {"title": "Game"})
        intent = self.intent_for_game()
        with self.assertRaises(AmbiguousPublishError):
            coordinator.reconcile_import(intent["id"], "unrelated")

    def test_live_malformed_readback_is_unknown_not_stranded(self):
        transport = QueueTransport(
            [
                self.response(201, self.design("draft")),
                self.response(200, self.design("public")),
                HttpResponse(200, {}, b"broken"),
            ]
        )
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})
        with self.assertRaises(AmbiguousPublishError):
            coordinator.publish_live(draft.intent_id, 4000)
        self.assertEqual(
            self.store.get_publish_intent(draft.intent_id)["state"], "live_unknown"
        )

    def test_deterministic_live_rejection_records_attempt_and_allows_correction(self):
        transport = QueueTransport(
            [
                self.response(201, self.design("draft")),
                self.response(422, {"error": "price rejected"}),
                self.response(200, self.design("public", 4500)),
                self.response(200, self.design("public", 4500)),
            ]
        )
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})

        with self.assertRaises(PublishError):
            coordinator.publish_live(draft.intent_id, 4000)
        rejected = self.store.get_publish_intent(draft.intent_id)
        self.assertEqual(rejected["state"], "succeeded")
        self.assertIsNone(rejected["live_request"])
        self.assertEqual(
            rejected["live_attempts"][0]["request"]["listing"]["price_cents"],
            4000,
        )

        live = coordinator.publish_live(draft.intent_id, 4500)
        self.assertTrue(live.is_verified_public)
        self.assertEqual(
            self.store.get_publish_intent(draft.intent_id)["state"], "live"
        )

    def test_publish_redirect_is_ambiguous_and_cannot_retry(self):
        transport = QueueTransport(
            [
                self.response(201, self.design("draft")),
                HttpResponse(302, {"location": "https://other.example"}, b""),
            ]
        )
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})
        with self.assertRaises(AmbiguousPublishError):
            coordinator.publish_live(draft.intent_id, 4000)
        self.assertEqual(
            self.store.get_publish_intent(draft.intent_id)["state"], "live_unknown"
        )
        with self.assertRaises(AmbiguousPublishError):
            coordinator.publish_live(draft.intent_id, 4000)
        self.assertEqual(len(transport.calls), 2)

    def test_upload_hash_identifies_the_bytes_actually_sent(self):
        initial = self.packet.read_bytes()

        def mutate_during_send(method, url, headers, body, timeout):
            self.packet.write_bytes(b"replacement")
            self.assertIn(initial, body)
            return self.response(201, self.design("draft"))

        outcome = self.coordinator(mutate_during_send).import_draft(
            "game", self.packet, {"title": "Game"}
        )
        self.assertEqual(
            outcome.receipt.packet_sha256, hashlib.sha256(initial).hexdigest()
        )

    def test_packet_must_match_the_product_artifact_before_http(self):
        other = Path(self.temp.name) / "other"
        other.mkdir()
        (other / "project.json").write_text('{"id":"other"}\n', encoding="utf-8")
        other_packet = Path(self.temp.name) / "other.zip"
        build_publish_packet(other, other_packet)
        transport = QueueTransport([])
        with self.assertRaises(ContractError):
            self.coordinator(transport).import_draft(
                "game", other_packet, {"title": "Wrong bytes"}
            )
        self.assertEqual(transport.calls, [])

    def test_import_metadata_is_allowlisted_bounded_and_secret_scanned(self):
        transport = QueueTransport([])
        coordinator = self.coordinator(transport)
        with self.assertRaises(ContractError):
            coordinator.import_draft(
                "game", self.packet, {"title": "Game", "token": "not allowed"}
            )
        with self.assertRaises(ContractError):
            coordinator.import_draft(
                "game",
                self.packet,
                {"title": "1234567:" + ("A" * 32)},
            )
        with self.assertRaises(ContractError):
            coordinator.import_draft(
                "game", self.packet, {"title": "Game", "tags": ["same", "same"]}
            )
        self.assertEqual(transport.calls, [])

    def test_final_sender_reapplies_name_and_content_secret_policy(self):
        cases = {
            "excluded-name": {".env": b"apparently harmless\n"},
            "secret-filename": {
                "ghp_" + ("A" * 24): b"apparently harmless\n"
            },
            "secret-content": {
                "notes.txt": b"bot=1234567:" + (b"A" * 32) + b"\n"
            },
        }
        for label, entries in cases.items():
            with self.subTest(case=label):
                packet = Path(self.temp.name) / (label + ".zip")
                self.handcrafted_packet(packet, entries)
                with self.assertRaises(ContractError):
                    _load_packet(packet)

    def test_packet_manifest_rejects_boolean_integer_fields(self):
        for field in ("schema_version", "total_bytes"):
            with self.subTest(field=field):
                packet = Path(self.temp.name) / (field + ".zip")
                self.handcrafted_packet(
                    packet,
                    {"one-byte.txt": b"x"},
                    {field: True},
                )
                with self.assertRaises(ContractError):
                    _load_packet(packet)

    def test_low_level_byte_import_revalidates_packet_before_transport(self):
        transport = QueueTransport([])
        client = PandaClient("token", transport=transport)
        with self.assertRaises(ContractError):
            client.import_design_bytes(
                "game.zip",
                b"ghp_" + (b"A" * 24),
                {"title": "Game"},
            )
        with self.assertRaises(ContractError):
            client.import_design_bytes(
                "ghp_" + ("A" * 24) + ".zip",
                self.packet.read_bytes(),
                {"title": "Game"},
            )
        self.assertEqual(transport.calls, [])

        # The safe low-level API still accepts the exact canonical bytes.
        transport.responses.append(self.response(201, self.design("draft")))
        response = client.import_design_bytes(
            "game.zip", self.packet.read_bytes(), {"title": "Game"}
        )
        self.assertEqual(response.status, 201)
        self.assertEqual(len(transport.calls), 1)

    def test_invalid_outer_packet_name_fails_before_outbox_or_http(self):
        renamed = self.packet.with_name("ghp_" + ("A" * 24) + ".zip")
        renamed.write_bytes(self.packet.read_bytes())
        transport = QueueTransport([])
        with self.assertRaises(ContractError):
            self.coordinator(transport).import_draft(
                "game", renamed, {"title": "Game"}
            )
        self.assertEqual(transport.calls, [])
        with self.store._connection() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM publish_intents"
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_in_memory_validator_rejects_mutable_byte_buffers(self):
        with self.assertRaises(ContractError):
            _validate_packet_bytes(bytearray(self.packet.read_bytes()))

    def test_packet_rejects_trailing_or_other_noncanonical_zip_bytes(self):
        self.packet.write_bytes(self.packet.read_bytes() + b"hidden trailing payload")
        with self.assertRaises(ContractError):
            _load_packet(self.packet)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs unavailable")
    def test_packet_reader_rejects_fifo_without_blocking(self):
        fifo = Path(self.temp.name) / "packet-fifo.zip"
        os.mkfifo(fifo)
        with self.assertRaises(ContractError):
            _load_packet(fifo)

    def test_api_origin_is_https_and_explicitly_pinned(self):
        with self.assertRaises(ContractError):
            PandaClient("token", api_base="http://panda.example/api")
        with self.assertRaises(ContractError):
            PandaClient("token", api_base="https://evil.example/api")
        client = PandaClient(
            "token",
            api_base="https://staging.example/api",
            allowed_origins=("https://staging.example",),
        )
        self.assertEqual(client.api_origin, "https://staging.example")
        self.assertIsNone(_NoRedirectHandler().redirect_request(None, None, 302, "", {}, "https://evil"))

    def test_response_contract_rejects_oversize_and_duplicate_json(self):
        with self.assertRaises(PublishError):
            HttpResponse(200, {}, b"x" * (2 * 1024 * 1024 + 1))
        transport = QueueTransport(
            [HttpResponse(201, {}, b'{"id":"one","id":"two"}')]
        )
        with self.assertRaises(AmbiguousPublishError):
            self.coordinator(transport).import_draft(
                "game", self.packet, {"title": "Game"}
            )
        self.assertEqual(self.intent_for_game()["state"], "unknown")

    @unittest.skipUnless(
        hasattr(os, "O_DIRECTORY")
        and os.open in getattr(os, "supports_dir_fd", set())
        and hasattr(os, "symlink"),
        "descriptor-relative no-follow opens unavailable",
    )
    def test_packet_parent_replacement_with_symlink_fails_closed(self):
        nested = Path(self.temp.name) / "nested"
        nested.mkdir()
        nested_packet = nested / "game.zip"
        nested_packet.write_bytes(self.packet.read_bytes())
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        real_open = os.open
        replaced = [False]

        def replace_parent(path, flags, *args, **kwargs):
            if path == "nested" and kwargs.get("dir_fd") is not None and not replaced[0]:
                replaced[0] = True
                nested.rename(Path(self.temp.name) / "nested-original")
                os.symlink(outside, nested)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch("inventor_core.panda.os.open", side_effect=replace_parent):
            with self.assertRaises(ContractError):
                _load_packet(nested_packet)
        self.assertTrue(replaced[0])

    @unittest.skipUnless(
        hasattr(os, "O_DIRECTORY")
        and os.open in getattr(os, "supports_dir_fd", set()),
        "descriptor-relative opens unavailable",
    )
    def test_packet_parent_replacement_with_real_directory_fails_closed(self):
        nested = Path(self.temp.name) / "nested-real"
        nested.mkdir()
        nested_packet = nested / "game.zip"
        nested_packet.write_bytes(self.packet.read_bytes())
        replacement = Path(self.temp.name) / "replacement-real"
        replacement.mkdir()
        (replacement / "game.zip").write_bytes(self.packet.read_bytes())
        real_open = os.open
        replaced = [False]

        def replace_parent(path, flags, *args, **kwargs):
            if (
                path == "nested-real"
                and kwargs.get("dir_fd") is not None
                and not replaced[0]
            ):
                replaced[0] = True
                nested.rename(Path(self.temp.name) / "nested-real-original")
                replacement.rename(nested)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch("inventor_core.panda.os.open", side_effect=replace_parent):
            with self.assertRaises(ContractError):
                _load_packet(nested_packet)
        self.assertTrue(replaced[0])

    @unittest.skipUnless(
        hasattr(os, "O_DIRECTORY")
        and os.open in getattr(os, "supports_dir_fd", set()),
        "descriptor-relative opens unavailable",
    )
    def test_packet_regular_file_replacement_fails_closed(self):
        nested = Path(self.temp.name) / "nested-file"
        nested.mkdir()
        nested_packet = nested / "game.zip"
        nested_packet.write_bytes(self.packet.read_bytes())
        replacement = nested / "replacement.zip"
        replacement.write_bytes(self.packet.read_bytes())
        real_open = os.open
        replaced = [False]

        def replace_file(path, flags, *args, **kwargs):
            if (
                path == "game.zip"
                and kwargs.get("dir_fd") is not None
                and not replaced[0]
            ):
                replaced[0] = True
                os.replace(replacement, nested_packet)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch("inventor_core.panda.os.open", side_effect=replace_file):
            with self.assertRaises(ContractError):
                _load_packet(nested_packet)
        self.assertTrue(replaced[0])


if __name__ == "__main__":
    unittest.main()
