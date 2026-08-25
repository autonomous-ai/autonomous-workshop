import hashlib
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from workshop.artifacts.core import build_publish_packet
from workshop.errors import (
    AmbiguousPublishError,
    ContractError,
    PublishError,
    StateConflict,
)
from workshop.integrations.launch import (
    HttpResponse,
    Launchpad,
    Portal,
    _NoRedirectHandler,
    _load_packet,
    _validate_packet_bytes,
    inspect_publish_packet,
)
from workshop.runtime.store import InventorStore


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


class LaunchTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.packet = Path(self.temp.name) / "game.zip"
        product = Path(self.temp.name) / "product"
        (product / "game_parts").mkdir(parents=True)
        (product / "project.json").write_text('{"id":"game"}\n', encoding="utf-8")
        (product / "game.stl").write_text("solid game\nendsolid game\n", encoding="utf-8")
        step_content = b"ISO-10303-21;\nEND-ISO-10303-21;\n"
        (product / "game.step").write_bytes(step_content)
        occurrence_sources = (
            ("base-occurrence", b"solid base\nendsolid base\n"),
            ("orbit-occurrence-one", b"solid orbit\nendsolid orbit\n"),
            ("orbit-occurrence-two", b"solid orbit\nendsolid orbit\n"),
        )
        production_stls = []
        sidecar_parts = []
        self.factory_inventory = []
        for order, (name, content) in enumerate(occurrence_sources):
            path = "game_parts/%s.stl" % name
            (product / path).write_bytes(content)
            part = "%s.stl" % name
            production_stls.append(
                {
                    "order": order,
                    "name": name,
                    "mesh_name": name,
                    "part": part,
                    "path": path,
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "source_path": "cad/parts/%s" % part,
                }
            )
            sidecar_parts.append({"name": name, "stlPath": path})
            self.factory_inventory.append(
                {"order": order, "mesh_name": name, "part": part}
            )
        sidecar_content = (
            json.dumps(
                {
                    "schemaVersion": 1,
                    "entryKind": "assembly",
                    "primaryPose": "assembled",
                    "parts": sidecar_parts,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        (product / "game.step.json").write_bytes(sidecar_content)
        facts = {
            "factory_assembly": {
                "schema_version": 1,
                "kind": "factory.occurrence-family",
                "occurrence_count": len(production_stls),
                "parts_directory": "game_parts",
                "production_stls": production_stls,
                "step": {
                    "path": "game.step",
                    "sha256": hashlib.sha256(step_content).hexdigest(),
                },
                "sidecar": {
                    "path": "game.step.json",
                    "sha256": hashlib.sha256(sidecar_content).hexdigest(),
                },
            }
        }
        (product / "workshop-product-facts.json").write_text(
            json.dumps(facts, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        build_publish_packet(product, self.packet)
        self.artifact_sha = _load_packet(self.packet)[2]
        self.store = InventorStore(Path(self.temp.name) / "state.sqlite")
        self.store.register_product("game", "reviewed", artifact_sha256=self.artifact_sha)

    def test_public_packet_inspection_returns_verified_identity(self):
        inspection = inspect_publish_packet(self.packet)
        self.assertEqual(inspection["bytes"], self.packet.stat().st_size)
        self.assertEqual(inspection["entries"], 9)
        self.assertEqual(inspection["artifact_sha256"], self.artifact_sha)
        self.assertEqual(
            inspection["packet_sha256"],
            hashlib.sha256(self.packet.read_bytes()).hexdigest(),
        )

    def test_import_rejects_undiscoverable_sealed_artifact_before_network(self):
        product = Path(self.temp.name) / "undiscoverable"
        product.mkdir()
        (product / "toy.step").write_text("exact sealed geometry\n", encoding="utf-8")
        packet = Path(self.temp.name) / "undiscoverable.zip"
        build_publish_packet(product, packet)
        artifact_sha = _load_packet(packet)[2]
        self.store.register_product(
            "undiscoverable", "reviewed", artifact_sha256=artifact_sha
        )
        transport = QueueTransport([])
        coordinator = Launchpad(
            self.store, Portal("token", transport=transport), "owner"
        )

        with self.assertRaisesRegex(
            ContractError, "top-level.*gen_step.*root project.json.*assembled.stl"
        ):
            coordinator.import_draft(
                "undiscoverable", packet, {"title": "Undiscoverable"}
            )

        self.assertEqual(transport.calls, [])
        self.assertIsNone(self.store.latest_publish_intent("undiscoverable"))

    def test_project_marker_requires_a_root_primary_model_before_network(self):
        product = Path(self.temp.name) / "nested-primary"
        (product / "cad").mkdir(parents=True)
        (product / "project.json").write_text(
            '{"id":"nested-primary"}\n', encoding="utf-8"
        )
        (product / "cad" / "product.stl").write_text(
            "solid nested\nendsolid nested\n", encoding="utf-8"
        )
        packet = Path(self.temp.name) / "nested-primary.zip"
        build_publish_packet(product, packet)
        artifact_sha = _load_packet(packet)[2]
        self.store.register_product(
            "nested-primary", "reviewed", artifact_sha256=artifact_sha
        )
        transport = QueueTransport([])

        with self.assertRaisesRegex(ContractError, "root assembled.stl.*<slug>.stl"):
            Launchpad(
                self.store, Portal("token", transport=transport), "owner"
            ).import_draft("nested-primary", packet, {"title": "Nested Primary"})

        self.assertEqual(transport.calls, [])
        self.assertIsNone(self.store.latest_publish_intent("nested-primary"))

    def test_import_rejects_nested_generator_that_would_drop_artifact_files(self):
        product = Path(self.temp.name) / "narrowed"
        (product / "nested").mkdir(parents=True)
        (product / "project.json").write_text('{"id":"narrowed"}\n', encoding="utf-8")
        (product / "keep.step").write_text("must stay in exact artifact\n", encoding="utf-8")
        (product / "nested" / "generate.py").write_text(
            "def gen_step():\n    return None\n", encoding="utf-8"
        )
        packet = Path(self.temp.name) / "narrowed.zip"
        build_publish_packet(product, packet)
        artifact_sha = _load_packet(packet)[2]
        self.store.register_product(
            "narrowed", "reviewed", artifact_sha256=artifact_sha
        )
        transport = QueueTransport([])
        coordinator = Launchpad(
            self.store, Portal("token", transport=transport), "owner"
        )

        with self.assertRaisesRegex(ContractError, "narrow.*nested generator"):
            coordinator.import_draft("narrowed", packet, {"title": "Narrowed"})

        self.assertEqual(transport.calls, [])
        self.assertIsNone(self.store.latest_publish_intent("narrowed"))

    def test_every_shared_import_rejects_factory_discoverable_local_page_media(self):
        product = Path(self.temp.name) / "creator-media"
        (product / "review").mkdir(parents=True)
        (product / "project.json").write_text(
            '{"id":"creator-media"}\n', encoding="utf-8"
        )
        (product / "toy.step").write_text("exact model\n", encoding="utf-8")
        (product / "creator-media.stl").write_text(
            "solid exact\nendsolid exact\n", encoding="utf-8"
        )
        (product / "review" / "hero.png").write_bytes(b"creator cover")
        packet = Path(self.temp.name) / "creator-media.zip"
        build_publish_packet(product, packet)
        artifact_sha = _load_packet(packet)[2]
        self.store.register_product(
            "creator-media", "reviewed", artifact_sha256=artifact_sha
        )
        transport = QueueTransport([])

        with self.assertRaisesRegex(ContractError, "creator page-output|local page media"):
            Portal("token", transport=transport).import_design(
                packet, {"title": "Creator Media"}
            )
        with self.assertRaisesRegex(ContractError, "creator page-output|local page media"):
            self.coordinator(transport).import_draft(
                "creator-media", packet, {"title": "Creator Media"}
            )

        self.assertEqual(transport.calls, [])
        self.assertIsNone(self.store.latest_publish_intent("creator-media"))

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
        return Launchpad(
            self.store, Portal("token", transport=transport), "owner"
        )

    def intent_for_game(self):
        with self.store._connection() as connection:
            intent_id = connection.execute(
                "SELECT id FROM publish_intents WHERE product_id='game'"
            ).fetchone()[0]
        return self.store.get_publish_intent(intent_id)

    def reviewed_factory_palette(self, color="#112233"):
        return [{**item, "color": color} for item in self.factory_inventory]

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

    def test_public_readback_accepts_factory_generated_copy_and_media(self):
        enriched = self.design("public")
        enriched.update(
            {
                "title": "Factory-polished title",
                "description": "Factory-generated product story.",
                "attachments": [
                    {
                        "kind": "video",
                        "url": "https://cdn.example/generated/product-story.mp4",
                    },
                    {
                        "kind": "image",
                        "url": "https://cdn.example/generated/product-story.webp",
                    },
                ],
            }
        )
        transport = QueueTransport(
            [
                self.response(201, self.design("draft")),
                self.response(200, enriched),
                self.response(200, enriched),
            ]
        )
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})

        live = coordinator.publish_live(draft.intent_id, 4000)

        self.assertTrue(live.is_verified_public)
        publish_body = json.loads(transport.calls[1][3].decode("utf-8"))
        self.assertNotIn("attachments", publish_body)

    def test_reviewed_occurrence_colors_are_canonical_durable_and_replay_bound(self):
        reviewed = [
            {
                "order": 2,
                "mesh_name": "orbit-occurrence-two",
                "part": "orbit-occurrence-two.stl",
                "color": "#FEDCBA",
            },
            {
                "order": 0,
                "mesh_name": "base-occurrence",
                "part": "base-occurrence.stl",
                "color": "#12151D",
            },
            {
                "order": 1,
                "mesh_name": "orbit-occurrence-one",
                "part": "orbit-occurrence-one.stl",
                "color": "#ABCDEF",
            },
        ]
        public = self.design("public")
        public["assembly_parts"] = [
            {
                "order": 0,
                "mesh_name": "base-occurrence",
                "part": "base-occurrence.stl",
                "color": "#12151d",
            },
            {
                "order": 1,
                "mesh_name": "orbit-occurrence-one",
                "part": "orbit-occurrence-one.stl",
                "color": "#abcdef",
            },
            {
                "order": 2,
                "mesh_name": "orbit-occurrence-two",
                "part": "orbit-occurrence-two.stl",
                "color": "#fedcba",
            },
        ]
        seeded_draft = self.design("draft")
        seeded_draft["assembly_parts"] = public["assembly_parts"]
        transport = QueueTransport(
            [
                self.response(201, self.design("draft")),
                self.response(
                    200, {"assembly_parts": public["assembly_parts"]}
                ),
                self.response(200, seeded_draft),
                self.response(200, public),
                self.response(200, public),
            ]
        )
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})

        live = coordinator.publish_live(
            draft.intent_id, 4000, assembly_parts=reviewed
        )

        self.assertTrue(live.is_verified_public)
        expected = [
            {
                "order": 0,
                "mesh_name": "base-occurrence",
                "part": "base-occurrence.stl",
                "color": "#12151d",
            },
            {
                "order": 1,
                "mesh_name": "orbit-occurrence-one",
                "part": "orbit-occurrence-one.stl",
                "color": "#abcdef",
            },
            {
                "order": 2,
                "mesh_name": "orbit-occurrence-two",
                "part": "orbit-occurrence-two.stl",
                "color": "#fedcba",
            },
        ]
        seed_body = json.loads(transport.calls[1][3].decode("utf-8"))
        self.assertEqual(seed_body["assembly_parts"], expected)
        publish_body = json.loads(transport.calls[3][3].decode("utf-8"))
        self.assertNotIn("assembly_parts", publish_body)
        intent = self.store.get_publish_intent(draft.intent_id)
        self.assertEqual(intent["live_request"]["assembly_parts"], expected)
        self.assertEqual(
            intent["request"]["_workshop_factory_assembly_inventory"],
            self.factory_inventory,
        )

        replay = coordinator.publish_live(
            draft.intent_id, 4000, assembly_parts=list(reversed(reviewed))
        )
        self.assertEqual(replay.to_dict(), live.to_dict())
        self.assertEqual(len(transport.calls), 5)
        with self.assertRaisesRegex(StateConflict, "request changed"):
            coordinator.publish_live(
                draft.intent_id,
                4000,
                assembly_parts=[
                    expected[0],
                    {**expected[1], "color": "#000000"},
                    expected[2],
                ],
            )
        self.assertEqual(len(transport.calls), 5)

    def test_assembly_colors_reject_shorthand_partial_and_malformed_occurrences(self):
        transport = QueueTransport([])
        door = Portal("token", transport=transport)
        cases = (
            [],
            [{"part": "body.stl", "color": "#112233"}],
            [{"order": 0, "color": "#112233"}],
            [
                {
                    "order": 0,
                    "mesh_name": "body",
                    "part": "body.stl",
                    "color": "#123",
                }
            ],
            [
                {
                    "order": 0,
                    "mesh_name": "body",
                    "part": "../body.stl",
                    "color": "#112233",
                }
            ],
            [
                {
                    "order": 0,
                    "mesh_name": "body one",
                    "part": "body.stl",
                    "color": "#112233",
                },
                {
                    "order": 0,
                    "mesh_name": "body two",
                    "part": "body.stl",
                    "color": "#445566",
                },
            ],
            [
                {
                    "order": 1,
                    "mesh_name": "body",
                    "part": "body.stl",
                    "color": "#112233",
                }
            ],
            [
                {
                    "order": True,
                    "mesh_name": "body",
                    "part": "body.stl",
                    "color": "#112233",
                }
            ],
            [
                {
                    "order": 0,
                    "mesh_name": " ",
                    "part": "body.stl",
                    "color": "#112233",
                }
            ],
        )
        for assembly_parts in cases:
            with self.subTest(assembly_parts=assembly_parts):
                with self.assertRaises(ContractError):
                    door.publish(
                        "game", 4000, assembly_parts=assembly_parts
                    )
        with self.assertRaisesRegex(ContractError, "durable Workshop publish intent"):
            door.publish(
                "game",
                4000,
                assembly_parts=self.reviewed_factory_palette(),
            )
        with self.assertRaisesRegex(ContractError, "sealed occurrence inventory"):
            door.seed_assembly_parts(
                "game",
                self.reviewed_factory_palette(),
            )
        self.assertEqual(transport.calls, [])

    def test_live_sender_rejects_legacy_shorthand_before_public_effect(self):
        transport = QueueTransport([self.response(201, self.design("draft"))])
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})

        with self.assertRaisesRegex(ContractError, "complete ordered occurrence"):
            coordinator.publish_live(
                draft.intent_id,
                4000,
                assembly_parts=[{"part": "body.stl", "color": "#112233"}],
            )

        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(
            self.store.get_publish_intent(draft.intent_id)["state"], "succeeded"
        )

    def test_live_palette_must_match_sealed_inventory_before_any_live_http(self):
        transport = QueueTransport([self.response(201, self.design("draft"))])
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})
        reviewed = self.reviewed_factory_palette()
        cases = {
            "short-but-contiguous": reviewed[:2],
            "wrong-mesh": [
                reviewed[0],
                {**reviewed[1], "mesh_name": "substitute-mesh"},
                reviewed[2],
            ],
            "wrong-part": [
                reviewed[0],
                {**reviewed[1], "part": "substitute-part.stl"},
                reviewed[2],
            ],
            "wrong-occurrence-order": [
                {**reviewed[0], "mesh_name": reviewed[1]["mesh_name"], "part": reviewed[1]["part"]},
                {**reviewed[1], "mesh_name": reviewed[0]["mesh_name"], "part": reviewed[0]["part"]},
                reviewed[2],
            ],
        }

        for label, assembly_parts in cases.items():
            with self.subTest(label=label), self.assertRaisesRegex(
                ContractError, "exact sealed occurrence"
            ):
                coordinator.publish_live(
                    draft.intent_id,
                    4000,
                    assembly_parts=assembly_parts,
                )

        self.assertEqual([call[0] for call in transport.calls], ["POST"])
        intent = self.store.get_publish_intent(draft.intent_id)
        self.assertEqual(intent["state"], "succeeded")
        self.assertIsNone(intent["live_request"])

    def test_live_palette_rejects_model_without_sealed_inventory_before_http(self):
        product = Path(self.temp.name) / "single"
        product.mkdir()
        (product / "project.json").write_text(
            '{"id":"single"}\n', encoding="utf-8"
        )
        (product / "single.stl").write_text(
            "solid single\nendsolid single\n", encoding="utf-8"
        )
        packet = Path(self.temp.name) / "single.zip"
        build_publish_packet(product, packet)
        artifact_sha = _load_packet(packet)[2]
        self.store.register_product(
            "single", "reviewed", artifact_sha256=artifact_sha
        )
        draft_design = {**self.design("draft"), "slug": "single"}
        transport = QueueTransport([self.response(201, draft_design)])
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft(
            "single", packet, {"title": "Single"}
        )

        with self.assertRaisesRegex(ContractError, "sealed occurrence inventory"):
            coordinator.publish_live(
                draft.intent_id,
                4000,
                assembly_parts=[
                    {
                        "order": 0,
                        "mesh_name": "single",
                        "part": "single.stl",
                        "color": "#112233",
                    }
                ],
            )

        self.assertEqual([call[0] for call in transport.calls], ["POST"])

    def test_public_readback_must_preserve_reviewed_assembly_colors(self):
        reviewed = self.reviewed_factory_palette()
        seeded_draft = self.design("draft")
        seeded_draft["assembly_parts"] = reviewed
        public = self.design("public")
        public["assembly_parts"] = [
            {**reviewed[0], "mesh_name": "wrong-occurrence"},
            *reviewed[1:],
        ]
        transport = QueueTransport(
            [
                self.response(201, self.design("draft")),
                self.response(200, {"assembly_parts": reviewed}),
                self.response(200, seeded_draft),
                self.response(200, public),
                self.response(200, public),
            ]
        )
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})

        with self.assertRaises(AmbiguousPublishError):
            coordinator.publish_live(
                draft.intent_id,
                4000,
                assembly_parts=reviewed,
            )

        self.assertEqual(
            self.store.get_publish_intent(draft.intent_id)["state"],
            "live_unknown",
        )

    def test_unknown_draft_seed_resumes_from_the_same_durable_occurrences(self):
        reviewed = self.reviewed_factory_palette()
        seeded_draft = self.design("draft")
        seeded_draft["assembly_parts"] = reviewed
        public = self.design("public")
        public["assembly_parts"] = reviewed
        transport = QueueTransport(
            [
                self.response(201, self.design("draft")),
                OSError("connection reset during seed"),
                self.response(200, self.design("draft")),
                self.response(200, {"assembly_parts": reviewed}),
                self.response(200, seeded_draft),
                self.response(200, public),
                self.response(200, public),
            ]
        )
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})

        with self.assertRaises(AmbiguousPublishError):
            coordinator.publish_live(
                draft.intent_id,
                4000,
                assembly_parts=reviewed,
            )
        self.assertEqual(
            self.store.get_publish_intent(draft.intent_id)["state"],
            "live_unknown",
        )

        live = coordinator.reconcile_live(draft.intent_id)

        self.assertTrue(live.is_verified_public)
        self.assertEqual(
            [call[0] for call in transport.calls],
            ["POST", "PATCH", "GET", "PATCH", "GET", "POST", "GET"],
        )
        self.assertEqual(
            self.store.get_publish_intent(draft.intent_id)["live_request"][
                "assembly_parts"
            ],
            reviewed,
        )

    def test_server_error_during_draft_seed_is_unknown_and_never_publishes(self):
        reviewed = self.reviewed_factory_palette()
        transport = QueueTransport(
            [
                self.response(201, self.design("draft")),
                self.response(503, {"error": "seed queue unavailable"}),
            ]
        )
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})

        with self.assertRaisesRegex(AmbiguousPublishError, "seed outcome is unknown"):
            coordinator.publish_live(
                draft.intent_id,
                4000,
                assembly_parts=reviewed,
            )

        self.assertEqual(
            self.store.get_publish_intent(draft.intent_id)["state"],
            "live_unknown",
        )
        self.assertEqual(
            [call[0] for call in transport.calls],
            ["POST", "PATCH"],
        )
        with self.assertRaises(AmbiguousPublishError):
            coordinator.publish_live(
                draft.intent_id,
                4000,
                assembly_parts=reviewed,
            )
        self.assertEqual(len(transport.calls), 2)

    def test_shared_sender_rejects_thumbnail_and_attachment_bypasses_before_http(self):
        transport = QueueTransport([])
        coordinator = self.coordinator(transport)

        with self.assertRaisesRegex(ContractError, "Factory owns"):
            coordinator.import_draft(
                "game",
                self.packet,
                {"title": "Game"},
                thumbnail={"filename": "cover.png"},
            )
        with self.assertRaisesRegex(ContractError, "Factory owns"):
            coordinator.publish_live(
                "missing-intent",
                4000,
                attachments=[
                    {"kind": "image", "url": "https://cdn.example/creator.png"}
                ],
            )
        with self.assertRaisesRegex(ContractError, "Factory owns"):
            coordinator.publish_live(
                "missing-intent", 4000, title="Creator replacement"
            )

        self.assertEqual(transport.calls, [])
        self.assertIsNone(self.store.latest_publish_intent("game"))

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
                    coordinator = Launchpad(
                        store, Portal("token", transport=transport), "owner"
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

    def test_public_live_reconciliation_uses_its_single_authenticated_get(self):
        transport = QueueTransport(
            [
                self.response(201, self.design("draft")),
                self.response(200, self.design("public")),
                self.response(503, {"error": "readback unavailable"}),
                self.response(200, self.design("public")),
            ]
        )
        coordinator = self.coordinator(transport)
        draft = coordinator.import_draft("game", self.packet, {"title": "Game"})

        with self.assertRaises(AmbiguousPublishError):
            coordinator.publish_live(draft.intent_id, 4000)
        live = coordinator.reconcile_live(draft.intent_id)

        self.assertTrue(live.is_verified_public)
        self.assertEqual(
            [call[0] for call in transport.calls],
            ["POST", "POST", "GET", "GET"],
        )
        self.assertEqual(
            self.store.get_publish_intent(draft.intent_id)["state"], "live"
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

    def test_shop_description_uses_explicit_inventor_attribution(self):
        transport = QueueTransport([self.response(201, self.design("draft"))])
        coordinator = self.coordinator(transport)
        outcome = coordinator.import_draft(
            "game",
            self.packet,
            {
                "title": "Game",
                "description": "A pocket game made for this table.\n\nBy Alice.\n\nBy Alice.  ",
            },
            inventor_name="Alice",
        )

        expected = "A pocket game made for this table.\n\nBy Alice."
        intent = self.store.get_publish_intent(outcome.intent_id)
        self.assertEqual(intent["request"]["description"], expected)
        body = transport.calls[0][3]
        self.assertIsInstance(body, bytes)
        self.assertIn(expected.encode("utf-8"), body)
        self.assertEqual(body.count(b"By Alice."), 1)
        self.assertNotIn(b"By owner.", body)

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
        client = Portal("token", transport=transport)
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
            Portal("token", api_base="http://portal.example/api")
        with self.assertRaises(ContractError):
            Portal("token", api_base="https://evil.example/api")
        client = Portal(
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

        with mock.patch("workshop.artifacts.pack.os.open", side_effect=replace_parent):
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

        with mock.patch("workshop.artifacts.pack.os.open", side_effect=replace_parent):
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

        with mock.patch("workshop.artifacts.pack.os.open", side_effect=replace_file):
            with self.assertRaises(ContractError):
                _load_packet(nested_packet)
        self.assertTrue(replaced[0])


if __name__ == "__main__":
    unittest.main()
