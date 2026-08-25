import hashlib
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from email.parser import BytesParser
from email.policy import default as email_policy
from pathlib import Path
from unittest import mock

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.errors import ContractError, StateConflict
from inventor_workshop.jobs import Invented, MakeContext
from inventor_workshop.shop import HttpResponse, ShopDoor, ShopInstructionsWriter
from inventor_workshop.store import InventorStore
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint
from tools import publish_showcase_products as publisher

try:
    import build_showcase_products as showcase_builder
except SystemExit as exc:
    showcase_builder = None
    _SHOWCASE_BUILDER_IMPORT_ERROR = str(exc)
else:
    _SHOWCASE_BUILDER_IMPORT_ERROR = ""


def _multipart(headers, body):
    content_type = headers["Content-Type"]
    message = BytesParser(policy=email_policy).parsebytes(
        ("Content-Type: %s\r\nMIME-Version: 1.0\r\n\r\n" % content_type).encode()
        + body
    )
    parts = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        parts.setdefault(name, []).append(
            {
                "filename": part.get_filename(),
                "content_type": part.get_content_type(),
                "content": part.get_payload(decode=True),
            }
        )
    return parts


def _sealed_bytes(bundle):
    result = {}
    for directory in ("artifact", "evidence", "instructions"):
        root = bundle / directory
        for path in sorted(root.rglob("*")):
            if path.is_file():
                result[path.relative_to(bundle).as_posix()] = path.read_bytes()
    return result


class ShowcaseShopTransport:
    def __init__(self, slug, owner_id, *, first_get_status=404):
        self.slug = slug
        self.owner_id = owner_id
        self.first_get_status = first_get_status
        self.calls = []
        self.exists = False
        self.title = None
        self.description = None
        self.tags = []
        self.category = None
        self.cover_url = "https://cdn.example/showcase/cover.png"
        self.imported_thumbnail = None
        self.prompt = None
        self.use_case = None
        self.story_blocks = []
        self.upload_index = 0
        self.roles = ("hero", "play", "detail", "parts", "box")
        self.urls = {
            role: "https://cdn.example/showcase/%s.png" % role
            for role in self.roles
        }
        self.imported_pack = None

    def design(self):
        return {
            "id": "design-showcase-1",
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "owner_id": self.owner_id,
            "root_id": "design-showcase-1",
            "current_history_id": "history-showcase-1",
            "published_history_id": None,
            "status": "draft",
            "project_url": "https://cdn.autonomous.ai/projects/history-showcase-1/",
            "origin": "import",
            "tags": list(self.tags),
            "category": {"slug": self.category},
            "author": {"id": self.owner_id},
            "thumbnail_urls": [self.cover_url],
            "use_case": self.use_case,
            "story_blocks": self.story_blocks,
        }

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, body, timeout))
        if headers.get("Authorization") != "Bearer test-token":
            raise AssertionError("publisher omitted authenticated Shop readback")
        if method == "GET" and url.endswith("/designs/%s" % self.slug):
            if not self.exists:
                if self.first_get_status == 404:
                    return HttpResponse(404, {}, b"{}")
                return HttpResponse(
                    self.first_get_status,
                    {},
                    json.dumps({"slug": self.slug}).encode(),
                )
            return HttpResponse(200, {}, json.dumps(self.design()).encode())
        if method == "POST" and url.endswith("/designs/import"):
            parts = _multipart(headers, body)
            self.imported_pack = parts["file"][0]["content"]
            fields = {
                name: values[0]["content"].decode("utf-8")
                for name, values in parts.items()
                if name not in ("file", "thumbnails", "tags")
            }
            self.title = fields["title"]
            self.description = fields["description"]
            self.prompt = fields["prompt"]
            self.tags = [item["content"].decode("utf-8") for item in parts["tags"]]
            self.category = fields["category"]
            if "thumbnails" in parts:
                raise AssertionError("model-only import must not send thumbnails")
            self.exists = True
            return HttpResponse(201, {}, json.dumps(self.design()).encode())
        if method == "POST" and url.endswith("/uploads"):
            part = _multipart(headers, body)["file"][0]
            content = part["content"]
            role = self.roles[self.upload_index]
            self.upload_index += 1
            return HttpResponse(
                201,
                {},
                json.dumps(
                    {
                        "url": self.urls[role],
                        "ref": "gs://showcase/%s" % part["filename"],
                        "filename": part["filename"],
                        "content_type": part["content_type"],
                        "size": len(content),
                        "sha256": hashlib.sha256(content).hexdigest(),
                    }
                ).encode(),
            )
        if method == "PATCH" and url.endswith("/use-case"):
            self.use_case = json.loads(body.decode("utf-8"))
            return HttpResponse(200, {}, json.dumps(self.design()).encode())
        if method == "PUT" and url.endswith("/story-blocks"):
            self.story_blocks = json.loads(body.decode("utf-8"))["story_blocks"]
            return HttpResponse(200, {}, json.dumps(self.design()).encode())
        if method == "POST" and url.endswith("/publish"):
            raise AssertionError("Instructions must leave the Shop design private")
        raise AssertionError("unexpected Shop request %s %s" % (method, url))


class PublishShowcaseProductsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "repo"
        self.bundle = (
            self.repo
            / "inventors"
            / "alice"
            / "toys"
            / "five-job-checkers"
        )
        source_inventor = publisher.REPO_ROOT / "inventors" / "alice"
        self.bundle.parent.mkdir(parents=True)
        shutil.copytree(
            source_inventor / "toys" / "five-job-checkers", self.bundle
        )
        shutil.copy2(source_inventor / "TASTE.md", self.repo / "inventors" / "alice")
        shutil.copy2(source_inventor / "profile.py", self.repo / "inventors" / "alice")
        self.state_root = self.root / "state"
        self.spec = publisher.showcase.SPECS[0]

    def test_exact_checked_in_bundle_drafts_once_and_durably_replays(self):
        before = _sealed_bytes(self.bundle)
        transport = ShowcaseShopTransport(self.spec.slug, "owner-1")

        first = publisher.publish_one(
            self.spec,
            token="test-token",
            owner_id="owner-1",
            repo_root=self.repo,
            state_root=self.state_root,
            transport=transport,
        )

        self.assertEqual(first["status"], "draft-created")
        self.assertEqual(first["enrichment_status"], "pending")
        self.assertIs(first["page_ready"], False)
        self.assertIsNone(transport.imported_thumbnail)
        self.assertTrue(transport.description.endswith("By Alice."))
        self.assertEqual(_sealed_bytes(self.bundle), before)
        with zipfile.ZipFile(io.BytesIO(transport.imported_pack)) as archive:
            self.assertIn("project.json", archive.namelist())
            self.assertIn("product.json", archive.namelist())
            self.assertIn("five-job-checkers.stl", archive.namelist())
            self.assertNotIn("assembled.stl", archive.namelist())
            self.assertIn("workshop-product-facts.json", archive.namelist())
            self.assertNotIn("images/hero.png", archive.namelist())
            self.assertEqual(
                json.loads(archive.read("project.json")),
                {"id": "five-job-checkers", "name": "Five-Job Checkers"},
            )
            self.assertEqual(
                archive.read("five-job-checkers.stl"),
                (self.bundle / "artifact" / "assembled.stl").read_bytes(),
            )
            self.assertNotIn("cad/product.stl", archive.namelist())
            source_sidecar = json.loads(
                (self.bundle / "artifact" / "assembled.step.json").read_text(
                    encoding="utf-8"
                )
            )
            occurrence_paths = [
                "five-job-checkers_parts/%s.stl" % item["name"]
                for item in source_sidecar["parts"]
            ]
            self.assertEqual(
                sorted(
                    name for name in archive.namelist() if name.endswith(".stl")
                ),
                sorted(["five-job-checkers.stl"] + occurrence_paths),
            )
            self.assertEqual(len(occurrence_paths), 25)
            self.assertFalse(
                any(name.startswith("cad/parts/") and name.endswith(".stl") for name in archive.namelist())
            )
            self.assertNotIn("assembled.step", archive.namelist())
            self.assertNotIn("assembled.step.json", archive.namelist())
            self.assertEqual(
                archive.read("five-job-checkers.step"),
                (self.bundle / "artifact" / "assembled.step").read_bytes(),
            )
            transported_sidecar = json.loads(
                archive.read("five-job-checkers.step.json")
            )
            self.assertEqual(
                [item["name"] for item in transported_sidecar["parts"]],
                [item["name"] for item in source_sidecar["parts"]],
            )
            self.assertEqual(
                [item["stlPath"] for item in transported_sidecar["parts"]],
                occurrence_paths,
            )
            for source_item, occurrence_path in zip(
                source_sidecar["parts"], occurrence_paths
            ):
                self.assertEqual(
                    archive.read(occurrence_path),
                    (
                        self.bundle / "artifact" / source_item["stlPath"]
                    ).read_bytes(),
                )
            self.assertEqual(
                json.loads(archive.read("product.json"))["inventor"]["name"],
                "Alice",
            )
            product = json.loads(archive.read("product.json"))
            facts_payload = archive.read("workshop-product-facts.json")
            facts = json.loads(facts_payload)
            self.assertEqual(facts["product"], product)
            self.assertEqual(facts["wish"], product["wish"])
            self.assertEqual(
                facts["primary_model"]["path"], "five-job-checkers.stl"
            )
            self.assertEqual(
                facts["primary_model"]["sha256"],
                hashlib.sha256(archive.read("five-job-checkers.stl")).hexdigest(),
            )
            self.assertEqual(facts["factory_assembly"]["occurrence_count"], 25)
            self.assertEqual(
                facts["factory_assembly"]["parts_directory"],
                "five-job-checkers_parts",
            )
            self.assertEqual(facts["product"]["components"], [
                "one checkers board",
                "twelve five-ring pieces",
                "twelve five-spoke pieces",
            ])
            self.assertIn("midnight grid", facts["product"]["description"])
            self.assertTrue(facts["product"]["limitations"])
            self.assertEqual(facts["product"]["story"], self.spec.story)
            self.assertEqual(
                facts["product"]["factory_brief"], self.spec.factory_brief
            )
            self.assertEqual(
                facts["product"]["art_direction"], self.spec.art_direction
            )
            self.assertEqual(facts["product"]["design"], self.spec.design)
        self.assertIn("Creative and film brief:\n", transport.prompt)
        self.assertIn(self.spec.factory_brief, transport.prompt)
        self.assertIn(self.spec.art_direction["palette"], transport.prompt)
        self.assertIn(self.spec.art_direction["must_show_media"][0], transport.prompt)
        self.assertIn("Design facts:\n", transport.prompt)
        self.assertIn('"assembled_extents_mm":[132.0,132.0,10.0]', transport.prompt)
        self.assertTrue(transport.prompt.endswith("By Alice."))
        methods_after_first = [call[0] for call in transport.calls]
        self.assertEqual(
            methods_after_first,
            ["GET", "POST", "GET"],
        )
        self.assertFalse(
            any(url.endswith("/publish") for _, url, _, _, _ in transport.calls)
        )
        count_after_first = len(transport.calls)

        replay = publisher.publish_one(
            self.spec,
            token="test-token",
            owner_id="owner-1",
            repo_root=self.repo,
            state_root=self.state_root,
            transport=transport,
        )
        self.assertEqual(replay["status"], "replayed")
        self.assertEqual(len(transport.calls), count_after_first)
        self.assertEqual(_sealed_bytes(self.bundle), before)

        # Factory may enrich mutable page copy and media after the model-only
        # import. Fresh verification observes that output; it must not require
        # it to equal Workshop's factual seed or original server cover.
        transport.title = "Factory-polished Five-Job Checkers"
        transport.description = "A Factory-generated midnight table story."
        transport.cover_url = "https://cdn.example/showcase/generated-cover.webp"
        transport.use_case = {"body": "Factory-generated use case"}
        transport.story_blocks = [{"body": "Factory-generated story"}]
        verified = publisher.publish_one(
            self.spec,
            token="test-token",
            owner_id="owner-1",
            repo_root=self.repo,
            state_root=self.state_root,
            transport=transport,
            verify_draft=True,
        )
        self.assertEqual(len(transport.calls), count_after_first + 1)
        self.assertEqual(
            verified["draft_verification"]["status"], "verified-draft"
        )
        enrichment = verified["draft_verification"]["factory_enrichment"]
        self.assertEqual(
            enrichment["title"], "Factory-polished Five-Job Checkers"
        )
        self.assertEqual(
            enrichment["cover_urls"],
            ["https://cdn.example/showcase/generated-cover.webp"],
        )
        self.assertTrue(enrichment["has_use_case"])
        self.assertEqual(enrichment["story_block_count"], 1)
        run = json.loads((self.bundle / "workshop-run.json").read_text())
        customer_page = (
            "https://www.autonomous.ai/factory/product/five-job-checkers"
        )
        self.assertEqual(run["run"]["job"], "deliver")
        self.assertEqual(run["run"]["page_url"], customer_page)
        self.assertTrue(run["assertions"]["site_draft_verified"])
        self.assertFalse(run["assertions"]["site_page_live"])
        self.assertEqual(run["site_receipt"]["status"], "draft")
        self.assertEqual(
            run["site_receipt"]["details"]["product_facts_sha256"],
            hashlib.sha256(facts_payload).hexdigest(),
        )
        self.assertEqual(
            run["site_receipt"]["details"]["primary_model_path"],
            "five-job-checkers.stl",
        )
        self.assertIsNone(run["site_receipt"]["published_history_id"])
        self.assertEqual(
            run["site_receipt"]["details"]["page_url"], customer_page
        )
        self.assertEqual(
            run["site_receipt"]["details"]["enrichment_status"], "pending"
        )
        self.assertIs(run["site_receipt"]["details"]["page_ready"], False)
        self.assertTrue(
            run["site_receipt"]["project_url"].startswith(
                "https://cdn.autonomous.ai/"
            )
        )
        self.assertNotEqual(
            run["run"]["page_url"], run["site_receipt"]["project_url"]
        )
        database = (
            self.state_root
            / "five-job-checkers"
            / "workshop.sqlite3"
        )
        self.assertTrue(database.is_file())
        store = InventorStore(database)
        publication_metadata = store.get_product(self.spec.slug)["metadata"]
        self.assertEqual(
            publication_metadata["blueprint_sha256"],
            "3b74057c2d747be170b6e0febbe4223a1fda0ddd1f2d4c1d6f7b3630f8e9a108",
        )
        self.assertEqual(
            publication_metadata["current_capability_blueprint_sha256"],
            ToyBlueprint.for_lane(self.spec.lane).sha256,
        )
        self.assertNotEqual(
            publication_metadata["blueprint_sha256"],
            publication_metadata["current_capability_blueprint_sha256"],
        )
        self.assertEqual(len(store.events(self.spec.slug)), 1)
        self.assertEqual(
            store.latest_publish_intent(self.spec.slug)["state"], "succeeded"
        )
        self.assertEqual(
            len(store.shop_effects_for_publish_intent(
                store.latest_publish_intent(self.spec.slug)["id"]
            )),
            0,
        )

    def _assert_mapping_survives_configured_shop_writer(
        self, made, wish, taste, workspace_name
    ):
        self.assertEqual(
            made.product,
            json.loads((made.artifact_root / "product.json").read_text()),
        )
        self.assertEqual(made.product["story"], self.spec.story)
        self.assertEqual(made.product["factory_brief"], self.spec.factory_brief)
        self.assertEqual(made.product["art_direction"], self.spec.art_direction)
        self.assertEqual(made.product["design"], self.spec.design)
        instructions = self.root / (workspace_name + "-instructions")
        instructions.mkdir()
        (instructions / "INSTRUCTIONS.md").write_text(
            "# Five-Job Checkers\n\nUse the known rules.\n", encoding="utf-8"
        )
        (instructions / "product.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "kind": "workshop.instructions-facts",
                    "status": "facts-ready",
                    "title": self.spec.title,
                    "summary": self.spec.summary + "\n\nBy Alice.",
                    "lane": self.spec.lane,
                    "factory_enrichment": {
                        "copy_owner": "factory",
                        "media_owner": "factory",
                        "status": "pending",
                    },
                    "product_artifact_sha256": made.artifact_sha256,
                    "playtest_evidence_artifact_sha256": "e" * 64,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        instructions_manifest = build_artifact_manifest(
            instructions, created_at="content-addressed"
        )
        store = InventorStore(self.root / (workspace_name + "-writer.sqlite3"))
        store.register_product(
            self.spec.slug, "instructions", artifact_sha256=made.artifact_sha256
        )
        lease = store.acquire_lease(self.spec.slug, "configured-writer-test")

        class Context:
            lease_token = lease

            def __init__(self):
                self.made = made
                self.wish = wish
                self.taste = taste

            def assert_current(self):
                self.made.assert_current()

        context = Context()
        transport = ShowcaseShopTransport(self.spec.slug, "owner-1")
        try:
            receipt = ShopInstructionsWriter(
                store, ShopDoor("test-token", transport=transport), "owner-1"
            )(
                context,
                instructions.resolve(strict=True),
                instructions_manifest,
            )
        finally:
            store.release_lease(self.spec.slug, lease)
        self.assertTrue(receipt.is_verified_draft)
        self.assertEqual(
            receipt.details["primary_model_path"], "five-job-checkers.stl"
        )

    def test_checked_in_showcase_mapping_survives_configured_shop_writer(self):
        sealed = publisher._load_sealed_showcase(self.spec)
        self._assert_mapping_survives_configured_shop_writer(
            sealed.made,
            sealed.wish,
            sealed.taste,
            "checked-in",
        )

    @unittest.skipIf(
        showcase_builder is None,
        _SHOWCASE_BUILDER_IMPORT_ERROR or "real showcase CAD runtime unavailable",
    )
    def test_normal_showcase_make_mapping_survives_configured_shop_writer(self):
        wish = showcase_builder._load_profile("alice").create_wish(
            self.spec.slug, self.spec.objective
        )
        taste = load_taste(publisher.REPO_ROOT / "inventors" / "alice")
        wish_sha256 = hashlib.sha256(
            json.dumps(
                wish.to_dict(), sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        made = showcase_builder.showcase_make(
            MakeContext(
                wish,
                taste,
                ToyBlueprint.for_lane(self.spec.lane),
                Invented(
                    wish_sha256,
                    taste.sha256,
                    self.spec.lane,
                    {
                        "title": self.spec.title,
                        "summary": "The reviewed showcase industrial-design concept.",
                    },
                    100,
                    90,
                ),
                1,
                (self.root / "normal-make").resolve(),
                playtest_rounds=self.spec.playtest_rounds,
            )
        )
        self._assert_mapping_survives_configured_shop_writer(
            made, wish, taste, "normal"
        )

    def test_sealed_publisher_has_no_geometry_generation_surface(self):
        self.assertFalse(hasattr(publisher.showcase, "showcase_make"))
        self.assertFalse(hasattr(publisher.showcase, "showcase_playtest"))
        self.assertFalse(hasattr(publisher.showcase, "_verify_bundle"))
        if showcase_builder is None:
            self.assertIn(
                "no fixture geometry will be substituted",
                _SHOWCASE_BUILDER_IMPORT_ERROR,
            )

    def test_unknown_legacy_blueprint_hash_is_rejected(self):
        receipt_path = self.bundle / "workshop-run.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["blueprint_sha256"] = "f" * 64
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ContractError,
            "checked-in Workshop receipt no longer binds this sealed bundle",
        ):
            publisher._load_sealed_showcase(self.spec, repo_root=self.repo)

    def test_current_inventor_profile_is_never_executed_for_legacy_import(self):
        marker = self.root / "profile-executed"
        profile_path = self.repo / "inventors" / "alice" / "profile.py"
        profile_path.write_text(
            "from pathlib import Path\n"
            "Path(%r).write_text('executed', encoding='utf-8')\n"
            "raise RuntimeError('publisher executed the current profile')\n"
            % str(marker),
            encoding="utf-8",
        )

        sealed = publisher._load_sealed_showcase(self.spec, repo_root=self.repo)

        self.assertEqual(sealed.spec.slug, self.spec.slug)
        self.assertFalse(marker.exists())

    def test_all_five_checked_in_bundles_reconstruct_without_running_jobs(self):
        sealed = [
            publisher._load_sealed_showcase(spec)
            for spec in publisher.showcase.SPECS
        ]

        self.assertEqual(
            [item.spec.inventor_id for item in sealed],
            ["alice", "bob", "eve", "ivy", "leo"],
        )
        for item in sealed:
            suffix = "By %s." % item.spec.inventor_name
            self.assertTrue(
                item.page["summary"].endswith(suffix),
                "%s draft summary lost inventor attribution" % item.spec.slug,
            )
            product = json.loads(
                (item.bundle / "artifact" / "product.json").read_text()
            )
            self.assertTrue(product["description"].endswith(suffix))
            self.assertEqual(product["story"], item.spec.story)
            self.assertEqual(product["factory_brief"], item.spec.factory_brief)
            self.assertEqual(product["art_direction"], item.spec.art_direction)
            self.assertEqual(product["design"], item.spec.design)
            self.assertEqual(
                json.loads((item.bundle / "artifact" / "project.json").read_text()),
                {"id": item.spec.slug, "name": item.spec.title},
            )

    def test_all_five_handoffs_match_factory_occurrence_family_contract(self):
        repo = self.root / "all-five-repo"
        expected_counts = {
            "five-job-checkers": 25,
            "comet-geneva": 5,
            "rackhaven-night-shift": 5,
            "montauk-tide-orrery": 6,
            "counterorbit": 12,
        }
        for spec in publisher.showcase.SPECS:
            source = (
                publisher.REPO_ROOT
                / "inventors"
                / spec.inventor_id
            )
            inventor = repo / "inventors" / spec.inventor_id
            bundle = inventor / "toys" / spec.slug
            bundle.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source / "toys" / spec.slug, bundle)
            shutil.copy2(source / "TASTE.md", inventor / "TASTE.md")
            shutil.copy2(source / "profile.py", inventor / "profile.py")

        for spec in publisher.showcase.SPECS:
            with self.subTest(slug=spec.slug):
                transport = ShowcaseShopTransport(spec.slug, "owner-1")
                publisher.publish_one(
                    spec,
                    token="test-token",
                    owner_id="owner-1",
                    repo_root=repo,
                    state_root=self.root / "all-five-state",
                    transport=transport,
                )
                bundle = (
                    repo
                    / "inventors"
                    / spec.inventor_id
                    / "toys"
                    / spec.slug
                )
                source_sidecar = json.loads(
                    (bundle / "artifact" / "assembled.step.json").read_text(
                        encoding="utf-8"
                    )
                )
                expected_paths = [
                    "%s_parts/%s.stl" % (spec.slug, item["name"])
                    for item in source_sidecar["parts"]
                ]
                self.assertEqual(len(expected_paths), expected_counts[spec.slug])
                with zipfile.ZipFile(io.BytesIO(transport.imported_pack)) as archive:
                    names = archive.namelist()
                    self.assertEqual(
                        sorted(name for name in names if name.endswith(".stl")),
                        sorted([spec.slug + ".stl"] + expected_paths),
                    )
                    self.assertIn(spec.slug + ".step", names)
                    self.assertIn(spec.slug + ".step.json", names)
                    self.assertNotIn("assembled.stl", names)
                    self.assertNotIn("assembled.step", names)
                    self.assertNotIn("assembled.step.json", names)
                    self.assertFalse(
                        any(
                            name.startswith("cad/") and name.endswith(".stl")
                            for name in names
                        )
                    )
                    transported_sidecar = json.loads(
                        archive.read(spec.slug + ".step.json")
                    )
                    self.assertEqual(
                        [item["name"] for item in transported_sidecar["parts"]],
                        [item["name"] for item in source_sidecar["parts"]],
                    )
                    self.assertEqual(
                        [item["stlPath"] for item in transported_sidecar["parts"]],
                        expected_paths,
                    )
                    for source_item, path in zip(
                        source_sidecar["parts"], expected_paths
                    ):
                        source_mesh = (
                            bundle / "artifact" / source_item["stlPath"]
                        ).read_bytes()
                        self.assertEqual(archive.read(path), source_mesh)
                    facts = json.loads(
                        archive.read("workshop-product-facts.json")
                    )
                    assembly = facts["factory_assembly"]
                    self.assertEqual(
                        assembly["occurrence_count"], expected_counts[spec.slug]
                    )
                    self.assertEqual(
                        assembly["parts_directory"], spec.slug + "_parts"
                    )
                    self.assertEqual(
                        [item["name"] for item in assembly["production_stls"]],
                        [item["name"] for item in source_sidecar["parts"]],
                    )
                    self.assertEqual(
                        [item["order"] for item in assembly["production_stls"]],
                        list(range(expected_counts[spec.slug])),
                    )
                    self.assertEqual(
                        [item["mesh_name"] for item in assembly["production_stls"]],
                        [item["name"] for item in source_sidecar["parts"]],
                    )
                    self.assertEqual(
                        [item["part"] for item in assembly["production_stls"]],
                        [Path(path).name for path in expected_paths],
                    )

    def test_changed_checked_in_bytes_fail_before_state_or_network(self):
        instructions = self.bundle / "instructions" / "INSTRUCTIONS.md"
        instructions.write_text(
            instructions.read_text(encoding="utf-8") + "changed\n",
            encoding="utf-8",
        )
        transport = ShowcaseShopTransport(self.spec.slug, "owner-1")
        with self.assertRaises(ContractError):
            publisher.publish_one(
                self.spec,
                token="test-token",
                owner_id="owner-1",
                repo_root=self.repo,
                state_root=self.state_root,
                transport=transport,
            )
        self.assertEqual(transport.calls, [])
        self.assertFalse(self.state_root.exists())

    def test_first_import_stops_when_canonical_slug_already_exists(self):
        transport = ShowcaseShopTransport(
            self.spec.slug, "owner-1", first_get_status=200
        )
        with self.assertRaisesRegex(StateConflict, "already exists"):
            publisher.publish_one(
                self.spec,
                token="test-token",
                owner_id="owner-1",
                repo_root=self.repo,
                state_root=self.state_root,
                transport=transport,
            )
        self.assertEqual([call[0] for call in transport.calls], ["GET"])
        store = InventorStore(
            self.state_root / self.spec.slug / "workshop.sqlite3"
        )
        self.assertIsNone(store.latest_publish_intent(self.spec.slug))

    def test_cli_credentials_require_both_values(self):
        with self.assertRaises(SystemExit):
            publisher._credentials({})
        with self.assertRaises(SystemExit):
            publisher._credentials({"WORKSHOP_SHOP_TOKEN": "token"})
        self.assertEqual(
            publisher._credentials(
                {
                    "WORKSHOP_SHOP_TOKEN": "token",
                    "WORKSHOP_SHOP_OWNER_ID": "owner",
                }
            ),
            ("token", "owner"),
        )


if __name__ == "__main__":
    unittest.main()
