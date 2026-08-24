import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.errors import ContractError, ReceiptError
from inventor_workshop.jobs import Made
from inventor_workshop.make import Wish
from inventor_workshop.models import PublicationReceipt
from inventor_workshop.shop import (
    FACTORY_STORY_PROMPT_LIMIT,
    HttpResponse,
    SHOP_USER_AGENT,
    ShopDoor,
    ShopInstructionsWriter,
    _factory_story_prompt,
    _sealed_factory_primary,
    _shop_category_for_lane,
)
from inventor_workshop.store import InventorStore


class InstructionsSiteContext:
    def __init__(self, made, product_id, lease_token=None):
        self.made = made
        self.wish = Wish.create(product_id, "A toy with a verified site page")
        self.taste = type("TasteName", (), {"name": "Alice"})()
        self.lease_token = lease_token

    def assert_current(self):
        self.made.assert_current()


class SuccessfulShopTransport:
    def __init__(self, context, media):
        self.context = context
        self.media = media
        self.calls = []
        self.upload_index = 0
        self.urls = {
            role: "https://cdn.example/%s.png" % role for role in media
        }

    def design(self, status):
        value = {
            "id": "design-1",
            "slug": self.context.wish.product_id,
            "title": "Verified Toy",
            "description": "An exact toy page.\n\nBy Alice.",
            "owner_id": "owner-1",
            "root_id": "design-1",
            "current_history_id": "history-1",
            "published_history_id": "history-1" if status == "public" else None,
            "status": status,
            "project_url": "https://cdn.autonomous.ai/projects/history-1/",
            "origin": "import",
            "tags": ["toy", "classics-made-yours"],
            "category": {"slug": "toys"},
            "author": {"id": "owner-1"},
            "thumbnail_urls": ["https://cdn.example/cover.png"],
        }
        if status == "public":
            value["attachments"] = [
                {"kind": "image", "url": self.urls[role]}
                for role in self.media
            ]
            value["listing"] = {
                "active": True,
                "price_cents": 4200,
                "currency": "usd",
                "sku": "TOY-001",
            }
        return value

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, body, timeout))
        if url.endswith("/designs/import"):
            return HttpResponse(201, {}, json.dumps(self.design("draft")).encode())
        if url.endswith("/uploads"):
            role = tuple(self.media)[self.upload_index]
            self.upload_index += 1
            content = self.media[role]
            return HttpResponse(
                201,
                {},
                json.dumps(
                    {
                        "url": self.urls[role],
                        "ref": "gs://bucket/%s.png" % role,
                        "filename": "%s.png" % role,
                        "content_type": "image/png",
                        "size": len(content),
                        "sha256": hashlib.sha256(content).hexdigest(),
                    }
                ).encode(),
            )
        if method == "POST" and url.endswith("/publish"):
            return HttpResponse(200, {}, json.dumps(self.design("public")).encode())
        if method == "GET" and "/designs/" in url:
            return HttpResponse(200, {}, json.dumps(self.design("draft")).encode())
        raise AssertionError("unexpected Shop request %s %s" % (method, url))


class CuratedShopTransport(SuccessfulShopTransport):
    def __init__(self, context, media):
        super().__init__(context, media)
        self.use_case = None
        self.story_blocks = []

    def design(self, status):
        value = super().design(status)
        value["use_case"] = self.use_case
        value["story_blocks"] = self.story_blocks
        return value

    def __call__(self, method, url, headers, body, timeout):
        if method == "PATCH" and url.endswith("/use-case"):
            self.calls.append((method, url, headers, body, timeout))
            self.use_case = json.loads(body.decode("utf-8"))
            return HttpResponse(
                200,
                {},
                json.dumps(
                    {
                        "use_case": self.use_case,
                        "story_blocks": self.story_blocks,
                    }
                ).encode(),
            )
        if method == "PUT" and url.endswith("/story-blocks"):
            self.calls.append((method, url, headers, body, timeout))
            self.story_blocks = json.loads(body.decode("utf-8"))["story_blocks"]
            return HttpResponse(
                200,
                {},
                json.dumps(
                    {
                        "use_case": self.use_case,
                        "story_blocks": self.story_blocks,
                    }
                ).encode(),
            )
        return super().__call__(method, url, headers, body, timeout)


class InstructionsSiteTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        product = self.root / "product"
        product.mkdir()
        (product / "project.json").write_text(
            '{"id":"verified-toy","name":"Verified Toy"}\n',
            encoding="utf-8",
        )
        (product / "toy.step").write_text("exact product bytes\n", encoding="utf-8")
        (product / "assembled.stl").write_text(
            "solid verified-toy\nendsolid verified-toy\n", encoding="utf-8"
        )
        for directory, marker in (
            ("review", b"local review cover"),
            ("renders", b"local render cover"),
            ("product-media", b"local product media"),
        ):
            media_directory = product / directory
            media_directory.mkdir()
            (media_directory / "hero.png").write_bytes(marker)
        made_product = {
            "title": "Verified Toy",
            "summary": "A small exact toy.",
            "description": "A brass puzzle whose shadow reveals a hidden star. By Alice.",
            "lane": "classics-made-yours",
            "components": ["one brass puzzle", "one folded rule card"],
            "design": {"rings": 3, "shadow_aperture": "five-point star"},
            "specifications": {"assembled_diameter_mm": 84},
            "instructions": "Turn the three rings until their shadows align.",
            "rules": {"goal": "reveal the hidden star", "moves": 3},
            "story": {
                "setting": "a midnight observatory",
                "piece_meaning": "each ring marks one unfinished wish",
            },
            "art_direction": {
                "light": "hard moonlight",
                "palette": ["blackened brass", "deep indigo"],
            },
            "limitations": ["digital Playtest only; physical QA happens in Deliver"],
        }
        (product / "product.json").write_text(
            json.dumps(made_product, sort_keys=True) + "\n", encoding="utf-8"
        )
        self.made = Made.from_root(product, made_product)
        self.store = InventorStore(self.root / "state.sqlite3")
        self.store.register_product(
            "verified-toy",
            "instructions",
            artifact_sha256=self.made.artifact_sha256,
        )
        self.instructions = self.root / "instructions"
        self.instructions.mkdir(parents=True)
        self.media = {}
        (self.instructions / "INSTRUCTIONS.md").write_text(
            "# Verified Toy\n\nUse the toy.\n", encoding="utf-8"
        )
        self.playtest_sha = "e" * 64
        (self.instructions / "product.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "kind": "workshop.instructions-facts",
                    "status": "facts-ready",
                    "title": "Verified Toy",
                    "summary": "An exact toy page.\n\nBy Alice.",
                    "lane": "classics-made-yours",
                    "factory_enrichment": {
                        "copy_owner": "factory",
                        "media_owner": "factory",
                        "status": "pending",
                    },
                    "product_artifact_sha256": self.made.artifact_sha256,
                    "playtest_evidence_artifact_sha256": self.playtest_sha,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        self.manifest = build_artifact_manifest(
            self.instructions, created_at="content-addressed"
        )

    def test_shared_writer_creates_model_only_draft_with_pending_enrichment(self):
        lease = self.store.acquire_lease("verified-toy", "toy-workshop")
        context = InstructionsSiteContext(self.made, "verified-toy", lease)
        transport = SuccessfulShopTransport(context, self.media)
        writer = ShopInstructionsWriter(
            self.store,
            ShopDoor("token", transport=transport),
            "owner-1",
        )
        try:
            receipt = writer(context, self.instructions, self.manifest)
        finally:
            self.store.release_lease("verified-toy", lease)

        self.assertTrue(receipt.is_verified_draft)
        self.assertFalse(receipt.is_verified_public)
        self.assertIsNone(receipt.listing_currency)
        self.assertEqual(
            receipt.details["instructions_sha256"],
            self.manifest.artifact_sha256,
        )
        self.assertEqual(
            receipt.details["page_url"],
            "https://www.autonomous.ai/factory/product/verified-toy",
        )
        self.assertEqual(receipt.details["playtest_evidence_sha256"], self.playtest_sha)
        self.assertEqual(receipt.details["enrichment_status"], "pending")
        self.assertIs(receipt.details["page_ready"], False)
        self.assertRegex(receipt.details["handoff_artifact_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(receipt.details["product_facts_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(receipt.details["primary_model_path"], "assembled.stl")
        self.assertEqual(
            receipt.details["primary_model_sha256"],
            hashlib.sha256(
                (self.made.artifact_root / "assembled.stl").read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(receipt.details["cover_url"], "https://cdn.example/cover.png")
        self.assertEqual(
            [call[0] for call in transport.calls],
            ["POST", "GET"],
        )
        self.assertTrue(
            all(call[2].get("User-Agent") == SHOP_USER_AGENT for call in transport.calls)
        )
        self.assertFalse(any(call[1].endswith("/publish") for call in transport.calls))
        import_body = transport.calls[0][3]
        self.assertNotIn(b'name="thumbnails"', import_body)
        self.assertFalse(any(content in import_body for content in self.media.values()))
        self.assertNotIn(b"local review cover", import_body)
        self.assertNotIn(b"local render cover", import_body)
        self.assertNotIn(b"local product media", import_body)
        self.assertIn(b"exact product bytes", import_body)
        self.assertIn(b'name="prompt"', import_body)
        self.assertIn(b"midnight observatory", import_body)
        self.assertIn(b"blackened brass", import_body)
        self.assertIn(b"reveal the hidden star", import_body)
        self.assertIn(b"five-point star", import_body)
        self.assertIn(b"assembled_diameter_mm", import_body)
        self.assertIn(b"one folded rule card", import_body)
        self.assertIn(b"Inventor attribution (retain exactly): By Alice.", import_body)
        self.assertNotIn(b"story_blocks", import_body)
        self.assertNotIn(b"use_case", import_body)
        self.assertIn(b'name="category"\r\n\r\ntoys\r\n', import_body)
        category_part = import_body.split(b'name="category"', 1)[1].split(
            b"\r\n--", 1
        )[0]
        self.assertNotIn(b"classics-made-yours\r\n", category_part)
        with self.store._connection() as connection:
            effect_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='shop_effects'"
            ).fetchone()
        self.assertIsNone(effect_table)
        intent = self.store.latest_publish_intent("verified-toy")
        self.assertNotIn("_workshop_cover_sha256", intent["request"])
        self.assertEqual(
            intent["request"]["_workshop_handoff_artifact_sha256"],
            receipt.details["handoff_artifact_sha256"],
        )

    def test_factory_story_prompt_is_bounded_without_losing_attribution(self):
        product = dict(self.made.product)
        product["art_direction"] = {"notes": "nocturne " * 8_000}
        made = Made(self.made.artifact_root, self.made.artifact_manifest, product)
        context = InstructionsSiteContext(made, "verified-toy")
        page = json.loads((self.instructions / "product.json").read_text())

        prompt = _factory_story_prompt(context, page)

        self.assertLessEqual(len(prompt), FACTORY_STORY_PROMPT_LIMIT)
        self.assertTrue(prompt.endswith("By Alice."))
        self.assertIn("_workshop_truncated", prompt)

    def test_unsealed_product_story_mutation_fails_before_http(self):
        product = dict(self.made.product)
        product["story"] = {"setting": "a substituted story"}
        made = Made(self.made.artifact_root, self.made.artifact_manifest, product)
        context = InstructionsSiteContext(made, "verified-toy")
        transport = SuccessfulShopTransport(context, self.media)

        with self.assertRaisesRegex(ContractError, "artifact/product.json"):
            ShopInstructionsWriter(
                self.store, ShopDoor("token", transport=transport), "owner-1"
            )(context, self.instructions, self.manifest)
        self.assertEqual(transport.calls, [])

    def test_divergent_root_primary_models_fail_closed(self):
        canonical = self.made.artifact_root / "verified-toy.stl"
        canonical.write_text("solid different\nendsolid different\n", encoding="utf-8")
        made = Made.from_root(self.made.artifact_root, self.made.product)
        context = InstructionsSiteContext(made, "verified-toy")

        with self.assertRaisesRegex(ContractError, "diverge"):
            _sealed_factory_primary(context)

    def test_workshop_lanes_map_to_the_shops_public_taxonomy(self):
        for lane in (
            "classics-made-yours",
            "invented-games",
            "moving-machines",
            "holdable-science",
            "little-worlds",
        ):
            self.assertEqual(_shop_category_for_lane(lane), "toys")
        with self.assertRaises(ContractError):
            _shop_category_for_lane("unknown-lane")

    def test_low_level_shop_door_rejects_every_creator_media_bypass(self):
        calls = []

        def forbidden_transport(method, url, headers, body, timeout):
            calls.append((method, url))
            raise AssertionError("creator media must be rejected before HTTP")

        door = ShopDoor("token", transport=forbidden_transport)
        cases = (
            lambda: door.import_design_bytes(
                "model.zip",
                b"not-even-a-pack",
                {"title": "Model"},
                thumbnail={"filename": "cover.png"},
            ),
            lambda: door.upload_file_bytes("hero.png", b"creator render", "image/png"),
            lambda: door.patch_use_case("verified-toy", {"body": "creator copy"}),
            lambda: door.put_story_blocks("verified-toy", [{"body": "creator copy"}]),
            lambda: door.publish(
                "verified-toy",
                4200,
                attachments=[{"kind": "image", "url": "https://cdn.example/hero.png"}],
            ),
            lambda: door.publish(
                "verified-toy", 4200, title="Creator replacement"
            ),
        )
        for operation in cases:
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(ContractError, "Factory owns"):
                    operation()
        self.assertEqual(calls, [])

    def test_model_handoff_never_calls_image_upload(self):
        context = InstructionsSiteContext(self.made, "verified-toy")
        successful = SuccessfulShopTransport(context, self.media)

        def reject_upload(method, url, headers, body, timeout):
            if url.endswith("/uploads"):
                raise AssertionError("Workshop must not upload Factory page media")
            return successful(method, url, headers, body, timeout)

        writer = ShopInstructionsWriter(
            self.store,
            ShopDoor("token", transport=reject_upload),
            "owner-1",
        )
        receipt = writer(context, self.instructions, self.manifest)
        self.assertTrue(receipt.is_verified_draft)
        self.assertEqual([call[0] for call in successful.calls], ["POST", "GET"])

    def test_pending_model_handoff_cannot_claim_page_ready(self):
        context = InstructionsSiteContext(self.made, "verified-toy")
        transport = SuccessfulShopTransport(context, self.media)
        writer = ShopInstructionsWriter(
            self.store, ShopDoor("token", transport=transport), "owner-1"
        )
        receipt = writer(context, self.instructions, self.manifest)
        changed = receipt.to_dict()
        changed["details"] = dict(changed["details"])
        changed["details"]["enrichment_status"] = "complete"
        changed["details"]["page_ready"] = True
        with self.assertRaisesRegex(ReceiptError, "cannot claim"):
            writer._assert_instructions_draft_receipt(
                PublicationReceipt.from_dict(changed),
                self.made.artifact_sha256,
                self.manifest.artifact_sha256,
            )

    def test_completed_draft_replays_without_http_and_rejects_price_policy(self):
        context = InstructionsSiteContext(self.made, "verified-toy")
        transport = SuccessfulShopTransport(context, self.media)
        door = ShopDoor("token", transport=transport)
        writer = ShopInstructionsWriter(self.store, door, "owner-1")
        first = writer(context, self.instructions, self.manifest)
        calls_after_draft = len(transport.calls)

        replay = writer(context, self.instructions, self.manifest)
        self.assertEqual(replay.to_dict(), first.to_dict())
        self.assertEqual(len(transport.calls), calls_after_draft)

        with self.assertRaisesRegex(ContractError, "separate owner-controlled"):
            ShopInstructionsWriter(
                self.store, door, "owner-1", price_cents=5000
            )
        self.assertEqual(len(transport.calls), calls_after_draft)

    def test_creator_page_copy_is_rejected_before_import(self):
        page_path = self.instructions / "product.json"
        page = json.loads(page_path.read_text(encoding="utf-8"))
        page["use_case"] = {
            "label": "Made for your table",
            "body": "U" * 180,
            "image": "hero",
        }
        page["story_blocks"] = [
            {
                "lead": "How it plays",
                "body": "S" * 180,
                "hero_image": "play",
                "pair_images": ["detail", "parts"],
            },
            {
                "lead": "What arrives",
                "body": "B" * 180,
                "hero_image": "box",
                "pair_images": [],
            },
        ]
        page_path.write_text(
            json.dumps(page, sort_keys=True) + "\n", encoding="utf-8"
        )
        manifest = build_artifact_manifest(
            self.instructions, created_at="content-addressed"
        )
        context = InstructionsSiteContext(self.made, "verified-toy")
        transport = CuratedShopTransport(context, self.media)
        with self.assertRaisesRegex(ContractError, "creator page copy"):
            ShopInstructionsWriter(
                self.store, ShopDoor("token", transport=transport), "owner-1"
            )(context, self.instructions, manifest)
        self.assertEqual(transport.calls, [])

    def test_creator_factory_output_in_made_facts_is_rejected_before_import(self):
        product = dict(self.made.product)
        product["story_blocks"] = [{"body": "creator-authored page block"}]
        made = Made(self.made.artifact_root, self.made.artifact_manifest, product)
        context = InstructionsSiteContext(made, "verified-toy")
        transport = SuccessfulShopTransport(context, self.media)

        with self.assertRaisesRegex(ContractError, "creator-owned Factory output"):
            ShopInstructionsWriter(
                self.store, ShopDoor("token", transport=transport), "owner-1"
            )(context, self.instructions, self.manifest)
        self.assertEqual(transport.calls, [])

    def test_creator_media_in_instructions_is_rejected_before_import(self):
        image = self.instructions / "hero.png"
        image.write_bytes(b"creator page render")
        manifest = build_artifact_manifest(
            self.instructions, created_at="content-addressed"
        )
        context = InstructionsSiteContext(self.made, "verified-toy")
        transport = SuccessfulShopTransport(context, self.media)

        with self.assertRaisesRegex(ContractError, "creator page media"):
            ShopInstructionsWriter(
                self.store, ShopDoor("token", transport=transport), "owner-1"
            )(context, self.instructions, manifest)
        self.assertEqual(transport.calls, [])


if __name__ == "__main__":
    unittest.main()
