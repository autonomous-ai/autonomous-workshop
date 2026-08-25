import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from email.parser import BytesParser
from email.policy import default as email_policy
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
    _assert_shop_importable_pack,
    _build_model_handoff_pack,
    _factory_page_readiness,
    _factory_story_prompt,
    _factory_transport_primary,
    _sealed_factory_primary,
    _shop_category_for_lane,
)
from inventor_workshop.store import InventorStore


def _multipart_parts(headers, body):
    message = BytesParser(policy=email_policy).parsebytes(
        (
            "Content-Type: %s\r\nMIME-Version: 1.0\r\n\r\n"
            % headers["Content-Type"]
        ).encode()
        + body
    )
    parts = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        parts.setdefault(name, []).append(part.get_payload(decode=True))
    return parts


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

    def test_exact_root_mesh_wins_and_generator_is_omitted_from_import_zip(self):
        generator = self.made.artifact_root / "main.py"
        generator.write_text(
            "def gen_step():\n    raise RuntimeError('Factory must not execute me')\n",
            encoding="utf-8",
        )
        made = Made.from_root(self.made.artifact_root, self.made.product)
        context = InstructionsSiteContext(made, "verified-toy")
        self.assertEqual(
            _sealed_factory_primary(context),
            {
                "kind": "mesh",
                "path": "assembled.stl",
                "sha256": hashlib.sha256(
                    (made.artifact_root / "assembled.stl").read_bytes()
                ).hexdigest(),
            },
        )

        page_path = self.instructions / "product.json"
        page = json.loads(page_path.read_text(encoding="utf-8"))
        page["product_artifact_sha256"] = made.artifact_sha256
        page_path.write_text(
            json.dumps(page, sort_keys=True) + "\n", encoding="utf-8"
        )
        instructions_manifest = build_artifact_manifest(
            self.instructions, created_at="content-addressed"
        )
        store = InventorStore(self.root / "mesh-preference.sqlite3")
        store.register_product(
            "verified-toy", "instructions", artifact_sha256=made.artifact_sha256
        )
        lease = store.acquire_lease("verified-toy", "mesh-preference-test")
        context = InstructionsSiteContext(made, "verified-toy", lease)
        transport = SuccessfulShopTransport(context, self.media)
        try:
            receipt = ShopInstructionsWriter(
                store, ShopDoor("token", transport=transport), "owner-1"
            )(context, self.instructions, instructions_manifest)
        finally:
            store.release_lease("verified-toy", lease)

        self.assertEqual(receipt.details["primary_model_path"], "assembled.stl")
        import_call = transport.calls[0]
        self.assertEqual(import_call[0], "POST")
        multipart = _multipart_parts(import_call[2], import_call[3])
        self.assertEqual(len(multipart["file"]), 1)
        with zipfile.ZipFile(io.BytesIO(multipart["file"][0])) as archive:
            names = set(archive.namelist())
            self.assertIn("assembled.stl", names)
            self.assertNotIn("main.py", names)
            self.assertNotIn(generator.read_bytes(), multipart["file"][0])
            facts = json.loads(archive.read("workshop-product-facts.json"))
            self.assertEqual(facts["primary_model"]["kind"], "mesh")
            self.assertEqual(facts["primary_model"]["path"], "assembled.stl")

    def test_single_print_mesh_keeps_assembled_name_when_only_review_stl_exists(self):
        review_mesh = self.made.artifact_root / "review" / "reference.stl"
        review_mesh.write_text(
            "solid review-only\nendsolid review-only\n", encoding="utf-8"
        )
        made = Made.from_root(self.made.artifact_root, self.made.product)
        context = InstructionsSiteContext(made, "verified-toy")
        sealed_primary = _sealed_factory_primary(context)

        self.assertEqual(
            _factory_transport_primary(context, sealed_primary), sealed_primary
        )

    def test_multipart_assembled_mesh_is_slug_named_only_in_factory_transport(self):
        parts = self.made.artifact_root / "verified-toy_parts"
        parts.mkdir()
        printable = parts / "body.stl"
        printable.write_text(
            "solid printable-body\nendsolid printable-body\n", encoding="utf-8"
        )
        generator = self.made.artifact_root / "main.py"
        generator.write_text(
            "def gen_step():\n    raise RuntimeError('sealed mesh must win')\n",
            encoding="utf-8",
        )
        nested_source = self.made.artifact_root / "source"
        nested_source.mkdir()
        nested_generator = nested_source / "model.py"
        nested_generator.write_text(
            "def gen_step():\n    return 'auditable source only'\n",
            encoding="utf-8",
        )
        made = Made.from_root(self.made.artifact_root, self.made.product)
        context = InstructionsSiteContext(made, "verified-toy")
        sealed_primary = _sealed_factory_primary(context)
        transported_primary = _factory_transport_primary(context, sealed_primary)
        self.assertEqual(sealed_primary["path"], "assembled.stl")
        self.assertEqual(transported_primary["path"], "verified-toy.stl")
        self.assertEqual(transported_primary["sha256"], sealed_primary["sha256"])

        page_path = self.instructions / "product.json"
        page = json.loads(page_path.read_text(encoding="utf-8"))
        page["product_artifact_sha256"] = made.artifact_sha256
        page_path.write_text(
            json.dumps(page, sort_keys=True) + "\n", encoding="utf-8"
        )
        instructions_manifest = build_artifact_manifest(
            self.instructions, created_at="content-addressed"
        )
        store = InventorStore(self.root / "multipart-mesh.sqlite3")
        store.register_product(
            "verified-toy", "instructions", artifact_sha256=made.artifact_sha256
        )
        lease = store.acquire_lease("verified-toy", "multipart-mesh-test")
        context = InstructionsSiteContext(made, "verified-toy", lease)
        transport = SuccessfulShopTransport(context, self.media)
        try:
            receipt = ShopInstructionsWriter(
                store, ShopDoor("token", transport=transport), "owner-1"
            )(context, self.instructions, instructions_manifest)
        finally:
            store.release_lease("verified-toy", lease)

        self.assertEqual(receipt.details["primary_model_path"], "verified-toy.stl")
        self.assertEqual(
            receipt.details["primary_model_sha256"], sealed_primary["sha256"]
        )
        multipart = _multipart_parts(transport.calls[0][2], transport.calls[0][3])
        with zipfile.ZipFile(io.BytesIO(multipart["file"][0])) as archive:
            names = archive.namelist()
            self.assertNotIn("assembled.stl", names)
            self.assertEqual(names.count("verified-toy.stl"), 1)
            self.assertIn("verified-toy_parts/body.stl", names)
            self.assertNotIn("main.py", names)
            self.assertIn("source/model.py", names)
            self.assertEqual(archive.read("source/model.py"), nested_generator.read_bytes())
            self.assertEqual(
                archive.read("verified-toy.stl"),
                (made.artifact_root / "assembled.stl").read_bytes(),
            )
            self.assertEqual(
                archive.read("verified-toy_parts/body.stl"), printable.read_bytes()
            )
            facts = json.loads(archive.read("workshop-product-facts.json"))
            self.assertEqual(facts["primary_model"], transported_primary)
        self.assertTrue((made.artifact_root / "assembled.stl").is_file())
        self.assertFalse((made.artifact_root / "verified-toy.stl").exists())

    def test_generator_only_artifact_remains_importable_and_keeps_generator(self):
        product_root = self.root / "generator-only"
        product_root.mkdir()
        product = {
            "title": "Generator Toy",
            "summary": "A sealed code-native toy.",
            "description": "A sealed code-native toy. By Alice.",
            "lane": "moving-machines",
        }
        (product_root / "project.json").write_text(
            '{"id":"generator-toy","name":"Generator Toy"}\n',
            encoding="utf-8",
        )
        (product_root / "product.json").write_text(
            json.dumps(product, sort_keys=True) + "\n", encoding="utf-8"
        )
        generator = product_root / "generator.py"
        generator.write_text(
            "def gen_step():\n    return 'sealed generator output'\n",
            encoding="utf-8",
        )
        made = Made.from_root(product_root, product)
        context = InstructionsSiteContext(made, "generator-toy")
        primary = _sealed_factory_primary(context)
        self.assertEqual(primary["kind"], "generator")
        self.assertEqual(primary["path"], "generator.py")

        packet = self.root / "generator-only.zip"
        facts = {
            "schema_version": 2,
            "kind": "workshop.product-facts",
            "primary_model": dict(primary),
        }
        _build_model_handoff_pack(
            made.artifact_root,
            made.artifact_manifest,
            packet,
            facts,
            primary,
        )
        content = packet.read_bytes()
        _assert_shop_importable_pack(content)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            self.assertIn("generator.py", archive.namelist())
            self.assertEqual(archive.read("generator.py"), generator.read_bytes())
            self.assertNotIn("assembled.stl", archive.namelist())
            self.assertNotIn("generator-toy.stl", archive.namelist())

    def test_slug_named_root_mesh_also_wins_over_generator(self):
        product_root = self.root / "slug-mesh"
        product_root.mkdir()
        product = {
            "title": "Slug Mesh Toy",
            "summary": "An exact slug-named mesh.",
            "description": "An exact slug-named mesh. By Alice.",
            "lane": "moving-machines",
        }
        (product_root / "project.json").write_text(
            '{"id":"slug-mesh-toy","name":"Slug Mesh Toy"}\n',
            encoding="utf-8",
        )
        (product_root / "product.json").write_text(
            json.dumps(product, sort_keys=True) + "\n", encoding="utf-8"
        )
        mesh = product_root / "slug-mesh-toy.stl"
        mesh.write_text(
            "solid slug-mesh-toy\nendsolid slug-mesh-toy\n", encoding="utf-8"
        )
        generator = product_root / "main.py"
        generator.write_text(
            "def gen_step():\n    raise RuntimeError('sealed mesh must win')\n",
            encoding="utf-8",
        )
        made = Made.from_root(product_root, product)
        context = InstructionsSiteContext(made, "slug-mesh-toy")
        primary = _sealed_factory_primary(context)
        self.assertEqual(primary["kind"], "mesh")
        self.assertEqual(primary["path"], "slug-mesh-toy.stl")

        packet = self.root / "slug-mesh.zip"
        facts = {
            "schema_version": 2,
            "kind": "workshop.product-facts",
            "primary_model": dict(primary),
        }
        _build_model_handoff_pack(
            made.artifact_root,
            made.artifact_manifest,
            packet,
            facts,
            primary,
        )
        with zipfile.ZipFile(packet) as archive:
            self.assertIn("slug-mesh-toy.stl", archive.namelist())
            self.assertNotIn("main.py", archive.namelist())

    def test_existing_exact_slug_mesh_avoids_duplicate_multipart_primary(self):
        product_root = self.root / "existing-slug-mesh"
        product_root.mkdir()
        product = {
            "title": "Existing Slug Mesh Toy",
            "summary": "One exact assembly and one print part.",
            "description": "One exact assembly and one print part. By Alice.",
            "lane": "moving-machines",
        }
        (product_root / "project.json").write_text(
            '{"id":"existing-slug-toy","name":"Existing Slug Toy"}\n',
            encoding="utf-8",
        )
        (product_root / "product.json").write_text(
            json.dumps(product, sort_keys=True) + "\n", encoding="utf-8"
        )
        mesh_bytes = b"solid exact-assembly\nendsolid exact-assembly\n"
        (product_root / "assembled.stl").write_bytes(mesh_bytes)
        (product_root / "existing-slug-toy.stl").write_bytes(mesh_bytes)
        parts = product_root / "existing-slug-toy_parts"
        parts.mkdir()
        (parts / "part.stl").write_bytes(
            b"solid print-part\nendsolid print-part\n"
        )
        made = Made.from_root(product_root, product)
        context = InstructionsSiteContext(made, "existing-slug-toy")
        sealed_primary = _sealed_factory_primary(context)
        primary = _factory_transport_primary(context, sealed_primary)
        self.assertEqual(sealed_primary["path"], "assembled.stl")
        self.assertEqual(primary["path"], "existing-slug-toy.stl")

        packet = self.root / "existing-slug-mesh.zip"
        facts = {
            "schema_version": 2,
            "kind": "workshop.product-facts",
            "primary_model": dict(primary),
        }
        _build_model_handoff_pack(
            made.artifact_root,
            made.artifact_manifest,
            packet,
            facts,
            primary,
            sealed_primary_model=sealed_primary,
        )
        with zipfile.ZipFile(packet) as archive:
            names = archive.namelist()
            self.assertNotIn("assembled.stl", names)
            self.assertEqual(names.count("existing-slug-toy.stl"), 1)
            self.assertEqual(archive.read("existing-slug-toy.stl"), mesh_bytes)
            self.assertIn("existing-slug-toy_parts/part.stl", names)

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

    def test_factory_story_prompt_prefers_reviewed_cinematic_brief(self):
        product = dict(self.made.product)
        product["factory_brief"] = (
            "The shadow knows first. Film the three exact brass rings turning "
            "under hard moonlight, then reveal the five-point star."
        )
        made = Made(self.made.artifact_root, self.made.artifact_manifest, product)
        context = InstructionsSiteContext(made, "verified-toy")
        page = json.loads((self.instructions / "product.json").read_text())

        prompt = _factory_story_prompt(context, page)

        self.assertIn("Creative and film brief", prompt)
        self.assertIn("The shadow knows first", prompt)
        self.assertIn("cinematic intro video", prompt)
        self.assertIn("never leave a declared media slot blank", prompt)
        self.assertIn("distinguish total pieces from unique part types", prompt)
        self.assertIn("Never turn a CAD target, clearance, tolerance", prompt)
        self.assertIn("claim of proven smooth fit", prompt)
        self.assertNotIn('"setting":"a midnight observatory"', prompt)

    def test_factory_page_readiness_requires_video_use_case_and_each_block_image(self):
        design = {
            "title": "Verified Toy",
            "description": "An exact toy page. By Alice.",
            "thumbnail_urls": ["https://cdn.example/hero.png"],
            "use_case": None,
            "story_blocks": [
                {"lead": "One", "hero_image": "https://cdn.example/one.png"},
                {"lead": "Two"},
            ],
        }

        readiness = _factory_page_readiness(design)

        self.assertIs(readiness["ready"], False)
        self.assertEqual(
            readiness["issues"],
            [
                "use-case-missing",
                "story-block-1-media-missing",
                "intro-video-missing",
            ],
        )

    def test_factory_page_readiness_accepts_complete_progressive_media(self):
        design = {
            "title": "Verified Toy",
            "description": "An exact toy page. By Alice.",
            "thumbnail_urls": [
                "https://cdn.example/intro-video.mp4",
                "https://cdn.example/hero.png",
            ],
            "use_case": {
                "image": "https://cdn.example/use-case.png",
            },
            "story_blocks": [
                {"hero_image": "https://cdn.example/block-0.png"},
                {"pair_images": ["https://cdn.example/block-1-a.png"]},
            ],
        }

        readiness = _factory_page_readiness(design)

        self.assertIs(readiness["ready"], True)
        self.assertEqual(readiness["issues"], [])
        self.assertEqual(
            readiness["video_urls"], ["https://cdn.example/intro-video.mp4"]
        )
        self.assertEqual(readiness["story_block_count"], 2)

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
