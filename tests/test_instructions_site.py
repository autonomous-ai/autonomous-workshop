import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.errors import AmbiguousPublishError, ContractError
from inventor_workshop.jobs import Made
from inventor_workshop.make import Wish
from inventor_workshop.shop import (
    HttpResponse,
    ShopDoor,
    ShopInstructionsWriter,
    _normalize_use_case,
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
            "category": {"slug": "tabletop"},
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
        self.made = Made.from_root(
            product,
            {
                "title": "Verified Toy",
                "summary": "A small exact toy.",
                "lane": "classics-made-yours",
            },
        )
        self.store = InventorStore(self.root / "state.sqlite3")
        self.store.register_product(
            "verified-toy",
            "instructions",
            artifact_sha256=self.made.artifact_sha256,
        )
        self.instructions = self.root / "instructions"
        images = self.instructions / "images"
        images.mkdir(parents=True)
        self.media = {}
        image_paths = {}
        for role in ("hero", "play", "detail", "parts", "box"):
            content = ("exact image %s\n" % role).encode()
            path = images / (role + ".png")
            path.write_bytes(content)
            self.media[role] = content
            image_paths[role] = "images/%s.png" % role
        (self.instructions / "INSTRUCTIONS.md").write_text(
            "# Verified Toy\n\nUse the toy.\n", encoding="utf-8"
        )
        self.playtest_sha = "e" * 64
        (self.instructions / "product.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "ready",
                    "title": "Verified Toy",
                    "summary": "An exact toy page.\n\nBy Alice.",
                    "lane": "classics-made-yours",
                    "images": image_paths,
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

    def test_shared_instructions_writer_creates_enriched_private_draft_under_workshop_lease(self):
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
        self.assertEqual(set(receipt.details["media_sha256"]), set(self.media))
        self.assertEqual(
            receipt.details["cover_sha256"],
            hashlib.sha256(self.media["hero"]).hexdigest(),
        )
        self.assertEqual(receipt.details["cover_url"], "https://cdn.example/cover.png")
        self.assertEqual(
            [call[0] for call in transport.calls],
            ["POST", "POST", "POST", "POST", "POST", "POST", "GET"],
        )
        self.assertFalse(any(call[1].endswith("/publish") for call in transport.calls))
        import_body = transport.calls[0][3]
        self.assertIn(b'name="thumbnails"; filename="hero.png"', import_body)
        self.assertIn(self.media["hero"], import_body)
        self.assertIn(b'name="category"\r\n\r\ntabletop\r\n', import_body)
        category_part = import_body.split(b'name="category"', 1)[1].split(
            b"\r\n--", 1
        )[0]
        self.assertNotIn(b"classics-made-yours\r\n", category_part)
        with self.store._connection() as connection:
            states = connection.execute(
                "SELECT state FROM shop_effects ORDER BY created_at, effect_key"
            ).fetchall()
        self.assertEqual([row[0] for row in states], ["succeeded"] * 5)
        intent = self.store.latest_publish_intent("verified-toy")
        self.assertEqual(
            intent["request"]["_workshop_cover_sha256"],
            hashlib.sha256(self.media["hero"]).hexdigest(),
        )

    def test_workshop_lanes_map_to_the_shops_public_taxonomy(self):
        self.assertEqual(_shop_category_for_lane("classics-made-yours"), "tabletop")
        self.assertEqual(_shop_category_for_lane("invented-games"), "tabletop")
        for lane in ("moving-machines", "holdable-science", "little-worlds"):
            self.assertEqual(_shop_category_for_lane(lane), "toys")
        with self.assertRaises(ContractError):
            _shop_category_for_lane("unknown-lane")

    def test_curated_page_images_reject_video_urls_before_import(self):
        with self.assertRaises(ContractError):
            _normalize_use_case(
                {
                    "label": "Made for your table",
                    "body": "U" * 180,
                    "image": "https://cdn.example/looks-like-an-image.mp4",
                }
            )

    def test_ambiguous_image_upload_is_not_repeated(self):
        context = InstructionsSiteContext(self.made, "verified-toy")
        successful = SuccessfulShopTransport(context, self.media)

        def fail_first_upload(method, url, headers, body, timeout):
            if url.endswith("/designs/import"):
                return successful(method, url, headers, body, timeout)
            successful.calls.append((method, url, headers, body, timeout))
            raise OSError("connection reset after upload")

        writer = ShopInstructionsWriter(
            self.store,
            ShopDoor("token", transport=fail_first_upload),
            "owner-1",
        )
        with self.assertRaises(AmbiguousPublishError):
            writer(context, self.instructions, self.manifest)
        calls_after_unknown = len(successful.calls)
        with self.assertRaises(AmbiguousPublishError):
            writer(context, self.instructions, self.manifest)
        self.assertEqual(len(successful.calls), calls_after_unknown)

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

    def test_optional_curated_copy_is_written_and_verified_in_final_readback(self):
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
        receipt = ShopInstructionsWriter(
            self.store, ShopDoor("token", transport=transport), "owner-1"
        )(context, self.instructions, manifest)

        self.assertTrue(receipt.is_verified_draft)
        self.assertEqual(transport.use_case["image"], transport.urls["hero"])
        self.assertEqual(
            transport.story_blocks[0]["pair_images"],
            [transport.urls["detail"], transport.urls["parts"]],
        )
        self.assertNotIn("pair_images", transport.story_blocks[1])
        self.assertEqual(
            [call[0] for call in transport.calls],
            ["POST", "POST", "POST", "POST", "POST", "POST", "PATCH", "PUT", "GET"],
        )


if __name__ == "__main__":
    unittest.main()
