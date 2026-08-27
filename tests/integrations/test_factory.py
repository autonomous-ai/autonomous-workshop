import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from email.parser import BytesParser
from email.policy import default as email_policy
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.errors import (
    AmbiguousEffectError,
    ContractError,
    EffectError,
    StateConflict,
)
from workshop.integrations.factory import (
    DEFAULT_FACTORY_API,
    FACTORY_USER_AGENT,
    FactoryAgentCredentials,
    FactoryAgentSession,
    FactoryClient,
    FactoryCredentialRejected,
    FactoryPublicTransition,
    FactoryReleaseWriter,
    HttpResponse,
    factory_credentials_from_environment,
)
from workshop.make.contracts import Made
from workshop.runtime import EffectLedger, Receipt
from workshop.wish import Wish


OBSERVED = "2026-08-26T00:00:00+00:00"
TETRA_STL = b"""solid workshop
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 0 1 0
      vertex 1 0 0
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 1 0 0
      vertex 0 0 1
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 0 0 1
      vertex 0 1 0
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 1 0 0
      vertex 0 1 0
      vertex 0 0 1
    endloop
  endfacet
endsolid workshop
"""


def canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def login_response(number=1):
    return HttpResponse(
        200,
        {"Content-Type": "application/json"},
        json.dumps(
            {
                "access_token": "test-access-%d" % number,
                "token_type": "Bearer",
                "expires_in": 31_536_000,
                "user": {"id": "owner-alice", "username": "alice"},
            }
        ).encode(),
    )


def multipart_parts(headers, body):
    message = BytesParser(policy=email_policy).parsebytes(
        ("Content-Type: %s\r\nMIME-Version: 1.0\r\n\r\n" % headers["Content-Type"]).encode()
        + body
    )
    values = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        values.setdefault(name, []).append(part.get_payload(decode=True))
    return values


class ScriptedSessionTransport:
    def __init__(self, protected_statuses=(200,)):
        self.protected_statuses = list(protected_statuses)
        self.calls = []
        self.logins = 0

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, dict(headers), body, timeout))
        if url.endswith("/auth/agent/login"):
            self.logins += 1
            return login_response(self.logins)
        return HttpResponse(self.protected_statuses.pop(0), {}, b"{}")


class FactorySessionTest(unittest.TestCase):
    def test_credentials_are_exact_and_redacted(self):
        credentials = factory_credentials_from_environment(
            "alice",
            {"FACTORY_USERNAME": "alice", "FACTORY_PASSWORD": "test-secret"},
        )
        self.assertEqual(credentials.username, "alice")
        self.assertNotIn("alice", repr(credentials))
        self.assertNotIn("test-secret", repr(credentials))
        with self.assertRaisesRegex(ContractError, "configured together"):
            factory_credentials_from_environment("alice", {"FACTORY_USERNAME": "alice"})
        with self.assertRaisesRegex(ContractError, "exactly match"):
            factory_credentials_from_environment(
                "bob",
                {"FACTORY_USERNAME": "alice", "FACTORY_PASSWORD": "test-secret"},
            )

    def test_bearer_is_memory_only_cached_and_same_origin(self):
        transport = ScriptedSessionTransport((200, 200))
        session = FactoryAgentSession(
            FactoryAgentCredentials("alice", "test-secret"), transport=transport
        )
        for _ in range(2):
            session.authenticated_transport(
                "GET", DEFAULT_FACTORY_API + "/designs/example", {}, None, 30
            )
        self.assertEqual(transport.logins, 1)
        self.assertNotIn("Authorization", transport.calls[0][2])
        for call in transport.calls[1:]:
            self.assertEqual(call[2]["Authorization"], "Bearer test-access-1")
            self.assertNotIn(b"test-secret", call[3] or b"")
        with self.assertRaisesRegex(ContractError, "another origin"):
            session.authenticated_transport(
                "GET", "https://example.com/api/v1/designs/example", {}, None, 30
            )

    def test_one_401_refreshes_once_and_login_rejection_is_redacted(self):
        transport = ScriptedSessionTransport((401, 200))
        session = FactoryAgentSession(
            FactoryAgentCredentials("alice", "test-secret"), transport=transport
        )
        self.assertEqual(
            session.authenticated_transport(
                "POST", DEFAULT_FACTORY_API + "/designs/import", {}, b"exact", 30
            ).status,
            200,
        )
        self.assertEqual(transport.logins, 2)

        def rejected(method, url, headers, body, timeout):
            return HttpResponse(401, {}, b'{"error":"provider-secret"}')

        rejected_session = FactoryAgentSession(
            FactoryAgentCredentials("alice", "test-secret"), transport=rejected
        )
        with self.assertRaises(FactoryCredentialRejected) as raised:
            rejected_session.login()
        self.assertNotIn("test-secret", str(raised.exception))
        self.assertNotIn("provider-secret", str(raised.exception))


class ReleaseContext:
    def __init__(self, made, product_id="verified-toy"):
        self.made = made
        self.wish = Wish.create(product_id, "A toy with a verified Factory page")
        self.taste = type("TasteName", (), {"name": "Alice"})()

    def assert_current(self):
        self.made.assert_current()


class FactoryTransport:
    def __init__(
        self, product_id="verified-toy", *, fail_get=False, import_status=201
    ):
        self.product_id = product_id
        self.fail_get = fail_get
        self.import_status = import_status
        self.public = False
        self.calls = []
        self.imports = 0
        self.use_case = None
        self.story_blocks = []
        self.use_case_writes = 0
        self.story_block_writes = 0

    def design(self):
        return {
            "id": "design-1",
            "slug": self.product_id,
            "owner_id": "owner-alice",
            "root_id": "design-1",
            "current_history_id": "history-1",
            "published_history_id": "history-1" if self.public else None,
            "status": "public" if self.public else "draft",
            "project_url": "https://cdn.autonomous.ai/projects/history-1/",
            "origin": "import",
            "title": "Verified Toy",
            "description": "An exact toy page authored before Factory import.",
            "tags": ["toy"],
            "category": {"slug": "toys"},
            "author": {"id": "owner-alice"},
            "thumbnail_urls": ["https://cdn.example/cover.png"],
            "use_case": self.use_case,
            "story_blocks": self.story_blocks,
            "listing": (
                {
                    "active": True,
                    "price_cents": 2400,
                    "currency": "usd",
                    "sku": "TOY-001",
                }
                if self.public
                else None
            ),
        }

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, dict(headers), body, timeout))
        if url.endswith("/auth/agent/login"):
            return login_response()
        if url.endswith("/designs/import"):
            self.imports += 1
            if self.import_status != 201:
                return HttpResponse(
                    self.import_status, {}, b'{"error":"request rejected"}'
                )
            return HttpResponse(201, {}, json.dumps(self.design()).encode())
        if method == "GET" and "/designs/" in url:
            if self.fail_get:
                raise RuntimeError("readback unavailable")
            return HttpResponse(200, {}, json.dumps(self.design()).encode())
        if method == "PATCH" and url.endswith("/use-case"):
            self.use_case_writes += 1
            self.use_case = json.loads(body.decode("utf-8"))
            return HttpResponse(
                200,
                {},
                canonical_json(
                    {
                        "use_case": self.use_case,
                        "story_blocks": self.story_blocks,
                    }
                ),
            )
        if method == "PUT" and url.endswith("/story-blocks"):
            self.story_block_writes += 1
            self.story_blocks = json.loads(body.decode("utf-8"))["story_blocks"]
            return HttpResponse(
                200,
                {},
                canonical_json(
                    {
                        "use_case": self.use_case,
                        "story_blocks": self.story_blocks,
                    }
                ),
            )
        if method == "POST" and url.endswith("/publish"):
            self.public = True
            return HttpResponse(200, {}, b"{}")
        raise AssertionError("unexpected Factory call %s %s" % (method, url))


class FactoryReleaseTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        product = self.root / "product"
        product.mkdir()
        (product / "project.json").write_text(
            '{"id":"verified-toy","name":"Verified Toy"}\n', encoding="utf-8"
        )
        (product / "assembled.step").write_bytes(b"exact STEP bytes")
        (product / "assembled.stl").write_bytes(b"solid verified\nendsolid verified\n")
        (product / "main.py").write_text(
            "def gen_step():\n    raise RuntimeError('must not execute')\n",
            encoding="utf-8",
        )
        (product / "unrelated.py").write_text(
            "raise RuntimeError('must not upload')\n", encoding="utf-8"
        )
        (product / "page.json").write_text(
            '{"title":"creator copy"}\n', encoding="utf-8"
        )
        (product / "review.json").write_text(
            '{"verdict":"creator review"}\n', encoding="utf-8"
        )
        (product / "marketing-copy.md").write_text(
            "# Creator marketing copy\n", encoding="utf-8"
        )
        for name in ("review", "renders", "product-media"):
            folder = product / name
            folder.mkdir()
            (folder / "local.png").write_bytes((name + " bytes").encode())
        made_product = {
            "title": "Verified Toy",
            "summary": "A small exact toy.",
            "description": "A small exact toy. By Alice.",
            "components": ["one puzzle", "one rule card"],
            "instructions": "Turn it.",
            "rules": {"goal": "align the star"},
            "limitations": ["digital Playtest only"],
        }
        (product / "product.json").write_text(
            json.dumps(made_product, sort_keys=True) + "\n", encoding="utf-8"
        )
        self.made = Made.from_root(product, made_product)
        self.context = ReleaseContext(self.made)
        self.release = self.root / "release"
        self.release.mkdir()
        (self.release / "MANUAL.md").write_text("# Verified Toy\n\nTurn it.\n")
        self.playtest_sha256 = "e" * 64
        self.page = {
            "schema_version": 3,
            "kind": "workshop.release-package",
            "status": "page-ready",
            "title": "Verified Toy",
            "summary": "An exact toy page authored before Factory import.",
            "hero": {
                "headline": "Turn the star",
                "body": "A small exact puzzle for one tabletop.",
                "visual_direction": "Show only the exact sealed assembly.",
                "evidence_refs": ["made:product.json"],
            },
            "cinematic": {
                "headline": "One turn changes the pattern",
                "body": "Rotate the puzzle and watch the star align.",
                "visual_direction": "Use the exact model at a low three-quarter angle.",
                "evidence_refs": ["made:product.json"],
            },
            "use_case": {
                "headline": "A quick tabletop challenge",
                "body": (
                    "Set down the exact sealed puzzle, follow the included rule card, "
                    "and rotate one piece at a time until the star aligns. The compact "
                    "tabletop format supports a focused solo challenge without adding "
                    "any unverified physical claim."
                ),
                "visual_direction": "Show one puzzle and one rule card only.",
                "evidence_refs": ["made:product.json"],
            },
            "story_blocks": [
                {
                    "headline": "Digitally checked",
                    "body": (
                        "The sealed digital design passed the required mechanical check "
                        "recorded by Workshop. This page reports that bounded digital "
                        "evidence exactly and does not claim a successful physical print, "
                        "durability result, or human playtest."
                    ),
                    "visual_direction": "Pair the exact model with a restrained check mark.",
                    "evidence_refs": ["playtest:mechanical-check"],
                }
            ],
            "what_arrives": ["one puzzle", "one rule card"],
            "limitations": ["digital Playtest only"],
            "product_artifact_sha256": self.made.artifact_sha256,
            "playtest_evidence_artifact_sha256": self.playtest_sha256,
            "claims": {"mechanical-check": {"passed": True}},
        }
        (self.release / "product.json").write_bytes(canonical_json(self.page))
        self.manifest = build_artifact_manifest(
            self.release, created_at="content-addressed"
        )
        self.ledger = EffectLedger(self.root / "state" / "factory-effects.sqlite3")

    def writer(self, transport):
        return FactoryReleaseWriter(
            self.ledger,
            "alice",
            FactoryAgentCredentials("alice", "test-secret"),
            transport=transport,
        )

    def test_private_import_is_model_only_hash_bound_and_idempotent(self):
        transport = FactoryTransport()
        receipt = self.writer(transport)(self.context, self.release, self.manifest)
        self.assertTrue(receipt.is_verified_draft)
        self.assertEqual(receipt.adapter, "factory")
        self.assertEqual(receipt.details["release_sha256"], self.manifest.artifact_sha256)
        self.assertEqual(receipt.details["playtest_evidence_sha256"], self.playtest_sha256)
        self.assertEqual(receipt.details["page_url"], "https://www.autonomous.ai/factory/product/verified-toy")
        self.assertEqual(receipt.details["primary_model_path"], "assembled.stl")
        self.assertRegex(receipt.details["effect_request_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(receipt.details["factory_content_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            receipt.details["manual_sha256"],
            hashlib.sha256((self.release / "MANUAL.md").read_bytes()).hexdigest(),
        )
        import_call = next(call for call in transport.calls if call[1].endswith("/designs/import"))
        self.assertEqual(import_call[2]["User-Agent"], FACTORY_USER_AGENT)
        self.assertRegex(import_call[2]["Idempotency-Key"], r"^autonomous-workshop-[0-9a-f]{64}$")
        parts = multipart_parts(import_call[2], import_call[3])
        self.assertNotIn("prompt", parts)
        self.assertNotIn("category", parts)
        self.assertEqual(parts["title"], [b"Verified Toy"])
        self.assertEqual(
            parts["description"],
            [b"An exact toy page authored before Factory import."],
        )
        with zipfile.ZipFile(io.BytesIO(parts["file"][0])) as archive:
            names = set(archive.namelist())
            self.assertIn("assembled.stl", names)
            self.assertIn("workshop-release-page.json", names)
            self.assertIn("workshop-product-facts.json", names)
            self.assertIn("MANUAL.md", names)
            self.assertNotIn("main.py", names)
            self.assertNotIn("page.json", names)
            self.assertNotIn("review.json", names)
            self.assertNotIn("marketing-copy.md", names)
            self.assertFalse(any(name.endswith(".png") for name in names))
            facts = json.loads(archive.read("workshop-product-facts.json"))
            self.assertEqual(facts["primary_model"]["path"], "assembled.stl")
            self.assertEqual(
                archive.read("workshop-release-page.json"),
                canonical_json(self.page),
            )
            self.assertEqual(
                archive.read("MANUAL.md"),
                (self.release / "MANUAL.md").read_bytes(),
            )
        self.assertEqual(
            receipt.details["product_page_sha256"],
            hashlib.sha256(canonical_json(self.page)).hexdigest(),
        )
        self.assertEqual(receipt.details["content_owner"], "workshop-manager")
        self.assertEqual(
            transport.use_case,
            {
                "label": self.page["use_case"]["headline"],
                "body": self.page["use_case"]["body"],
                "image": "https://cdn.example/cover.png",
            },
        )
        self.assertEqual(
            transport.story_blocks,
            [
                {
                    "lead": self.page["story_blocks"][0]["headline"],
                    "body": self.page["story_blocks"][0]["body"],
                }
            ],
        )
        replay = self.writer(transport)(self.context, self.release, self.manifest)
        self.assertEqual(replay, receipt)
        self.assertEqual(transport.imports, 1)
        self.assertEqual(transport.use_case_writes, 1)
        self.assertEqual(transport.story_block_writes, 1)

    def test_private_import_accepts_canonical_make_tree_without_project_json(self):
        product = self.made.artifact_root
        (product / "project.json").unlink()
        self.made = Made.from_root(product, self.made.product)
        self.context = ReleaseContext(self.made)
        release_page = json.loads(
            (self.release / "product.json").read_text(encoding="utf-8")
        )
        release_page["product_artifact_sha256"] = self.made.artifact_sha256
        (self.release / "product.json").write_bytes(canonical_json(release_page))
        self.manifest = build_artifact_manifest(
            self.release, created_at="content-addressed"
        )

        receipt = self.writer(FactoryTransport())(
            self.context, self.release, self.manifest
        )

        self.assertTrue(receipt.is_verified_draft)

    def test_generator_primary_is_included_but_creator_outputs_are_not(self):
        product = self.made.artifact_root
        (product / "assembled.stl").unlink()
        self.made = Made.from_root(product, self.made.product)
        self.context = ReleaseContext(self.made)
        release_facts_path = self.release / "product.json"
        release_facts = json.loads(release_facts_path.read_text(encoding="utf-8"))
        release_facts["product_artifact_sha256"] = self.made.artifact_sha256
        release_facts_path.write_bytes(canonical_json(release_facts))
        self.manifest = build_artifact_manifest(
            self.release, created_at="content-addressed"
        )

        transport = FactoryTransport()
        receipt = self.writer(transport)(self.context, self.release, self.manifest)

        self.assertTrue(receipt.is_verified_draft)
        import_call = next(
            call for call in transport.calls if call[1].endswith("/designs/import")
        )
        parts = multipart_parts(import_call[2], import_call[3])
        with zipfile.ZipFile(io.BytesIO(parts["file"][0])) as archive:
            names = set(archive.namelist())
            self.assertIn("main.py", names)
            self.assertIn("assembled.step", names)
            self.assertNotIn("unrelated.py", names)
            self.assertNotIn("page.json", names)
            self.assertNotIn("review.json", names)
            self.assertNotIn("marketing-copy.md", names)
            facts = json.loads(archive.read("workshop-product-facts.json"))
            self.assertEqual(
                facts["primary_model"],
                {
                    "kind": "generator",
                    "path": "main.py",
                    "sha256": hashlib.sha256(archive.read("main.py")).hexdigest(),
                },
            )

    def test_client_rejects_unrecognized_creator_output_in_model_archive(self):
        primary = b"solid exact\nendsolid exact\n"
        buffer = io.BytesIO()
        manual = b"# Exact Manual\n"
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("assembled.stl", primary)
            archive.writestr("MANUAL.md", manual)
            archive.writestr(
                "workshop-release-page.json", canonical_json(self.page)
            )
            archive.writestr(
                "workshop-product-facts.json",
                json.dumps(
                    {
                        "primary_model": {
                            "kind": "mesh",
                            "path": "assembled.stl",
                            "sha256": hashlib.sha256(primary).hexdigest(),
                        },
                        "manual": {
                            "path": "MANUAL.md",
                            "sha256": hashlib.sha256(manual).hexdigest(),
                        },
                    }
                ),
            )
            archive.writestr("page.json", '{"title":"must not cross"}')
            archive.writestr("unrelated.py", "raise RuntimeError('must not cross')")

        def must_not_send(method, url, headers, body, timeout):
            raise AssertionError("invalid model archive reached the transport")

        client = FactoryClient(must_not_send)
        with self.assertRaisesRegex(ContractError, "non-model output: page.json"):
            client.import_model(
                filename="model-handoff.zip",
                content=buffer.getvalue(),
                metadata={},
                idempotency_key="test-key",
            )

    def test_multipart_import_preserves_safe_underscore_occurrence_names(self):
        product = self.made.artifact_root
        (product / "assembled.stl").write_bytes(TETRA_STL)
        (product / "stone_rook_a1.stl").write_bytes(TETRA_STL)
        (product / "assembled.step.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "entryKind": "assembly",
                    "primaryPose": "assembled",
                    "parts": [
                        {"name": "stone_rook_a1", "stlPath": "stone_rook_a1.stl"}
                    ],
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        self.made = Made.from_root(product, self.made.product)
        self.context = ReleaseContext(self.made)
        release_facts_path = self.release / "product.json"
        release_facts = json.loads(release_facts_path.read_text(encoding="utf-8"))
        release_facts["product_artifact_sha256"] = self.made.artifact_sha256
        release_facts_path.write_bytes(canonical_json(release_facts))
        self.manifest = build_artifact_manifest(
            self.release, created_at="content-addressed"
        )

        transport = FactoryTransport()
        receipt = self.writer(transport)(self.context, self.release, self.manifest)

        self.assertTrue(receipt.is_verified_draft)
        import_call = next(
            call for call in transport.calls if call[1].endswith("/designs/import")
        )
        parts = multipart_parts(import_call[2], import_call[3])
        with zipfile.ZipFile(io.BytesIO(parts["file"][0])) as archive:
            names = set(archive.namelist())
            occurrence_path = "verified-toy_parts/stone_rook_a1.stl"
            self.assertIn(occurrence_path, names)
            sidecar = json.loads(archive.read("verified-toy.step.json"))
            self.assertEqual(sidecar["parts"][0]["name"], "stone_rook_a1")
            self.assertEqual(sidecar["parts"][0]["stlPath"], occurrence_path)

    def test_unrepresentable_factory_copy_fails_before_remote_import(self):
        page = json.loads((self.release / "product.json").read_text(encoding="utf-8"))
        page["use_case"]["body"] = "Too short for the Factory page contract."
        (self.release / "product.json").write_bytes(canonical_json(page))
        manifest = build_artifact_manifest(
            self.release, created_at="content-addressed"
        )
        transport = FactoryTransport()

        with self.assertRaisesRegex(
            ContractError, "use_case body.*180-400"
        ):
            self.writer(transport)(self.context, self.release, manifest)

        self.assertEqual(transport.calls, [])
        self.assertIsNone(self.ledger.latest("verified-toy", "factory-import"))

    def test_unknown_content_write_recovers_exact_readback_without_resending(self):
        class LostStoryResponse(FactoryTransport):
            def __init__(self):
                super().__init__()
                self.lost = False

            def __call__(self, method, url, headers, body, timeout):
                response = super().__call__(method, url, headers, body, timeout)
                if method == "PUT" and url.endswith("/story-blocks") and not self.lost:
                    self.lost = True
                    raise RuntimeError("response lost after exact write")
                return response

        transport = LostStoryResponse()
        with self.assertRaises(AmbiguousEffectError):
            self.writer(transport)(self.context, self.release, self.manifest)
        intent = self.ledger.latest("verified-toy", "factory-content")
        self.assertIsNotNone(intent)
        self.assertEqual(intent.state, "unknown")

        receipt = self.writer(transport)(self.context, self.release, self.manifest)

        self.assertTrue(receipt.is_verified_draft)
        self.assertEqual(transport.imports, 1)
        self.assertEqual(transport.use_case_writes, 1)
        self.assertEqual(transport.story_block_writes, 1)
        self.assertEqual(self.ledger.get(intent.intent_id).state, "succeeded")

    def test_partial_content_write_resumes_only_the_missing_story_blocks(self):
        class RejectStoryBlocksOnce(FactoryTransport):
            def __init__(self):
                super().__init__()
                self.rejected_story_blocks = False

            def __call__(self, method, url, headers, body, timeout):
                if (
                    method == "PUT"
                    and url.endswith("/story-blocks")
                    and not self.rejected_story_blocks
                ):
                    self.rejected_story_blocks = True
                    self.calls.append((method, url, dict(headers), body, timeout))
                    self.story_block_writes += 1
                    return HttpResponse(422, {}, b'{"error":"rejected"}')
                return super().__call__(method, url, headers, body, timeout)

        transport = RejectStoryBlocksOnce()
        with self.assertRaises(AmbiguousEffectError):
            self.writer(transport)(self.context, self.release, self.manifest)
        intent = self.ledger.latest("verified-toy", "factory-content")
        self.assertIsNotNone(intent)
        self.assertEqual(intent.state, "unknown")
        self.assertIsNotNone(transport.use_case)
        self.assertEqual(transport.story_blocks, [])

        receipt = self.writer(transport)(self.context, self.release, self.manifest)

        self.assertTrue(receipt.is_verified_draft)
        self.assertEqual(transport.imports, 1)
        self.assertEqual(transport.use_case_writes, 1)
        self.assertEqual(transport.story_block_writes, 2)
        self.assertEqual(self.ledger.get(intent.intent_id).state, "succeeded")

    def test_existing_different_factory_content_is_never_overwritten(self):
        transport = FactoryTransport()
        transport.use_case = {
            "label": "Existing page",
            "body": "Existing independently authored Factory content remains in place. " * 4,
            "image": "https://cdn.example/existing.png",
        }

        with self.assertRaisesRegex(StateConflict, "refusing to overwrite"):
            self.writer(transport)(self.context, self.release, self.manifest)

        self.assertEqual(transport.imports, 1)
        self.assertEqual(transport.use_case_writes, 0)
        self.assertEqual(transport.story_block_writes, 0)

    def test_unknown_import_recovers_by_get_without_resending(self):
        failed = FactoryTransport(fail_get=True)
        with self.assertRaises(AmbiguousEffectError):
            self.writer(failed)(self.context, self.release, self.manifest)
        intent = self.ledger.latest("verified-toy", "factory-import")
        self.assertEqual(intent.state, "unknown")
        self.assertIsNotNone(intent.response)

        recovery = FactoryTransport()
        receipt = self.writer(recovery)(self.context, self.release, self.manifest)
        self.assertTrue(receipt.is_verified_draft)
        self.assertEqual(recovery.imports, 0)
        self.assertEqual(self.ledger.get(intent.intent_id).state, "succeeded")

    def test_proven_no_effect_rejection_can_retry_after_host_correction(self):
        rejected = FactoryTransport(import_status=422)
        with self.assertRaises(EffectError):
            self.writer(rejected)(self.context, self.release, self.manifest)
        intent = self.ledger.latest("verified-toy", "factory-import")
        self.assertEqual(intent.state, "rejected")

        corrected = FactoryTransport()
        receipt = self.writer(corrected)(self.context, self.release, self.manifest)

        self.assertTrue(receipt.is_verified_draft)
        self.assertEqual(corrected.imports, 1)
        self.assertEqual(
            self.ledger.get(intent.intent_id).state,
            "succeeded",
        )

    def test_import_infrastructure_failures_are_safe_to_retry(self):
        for status in (500, 524):
            with self.subTest(status=status):
                ledger = EffectLedger(
                    self.root / ("state-%s" % status) / "factory-effects.sqlite3"
                )
                writer = FactoryReleaseWriter(
                    ledger,
                    "alice",
                    FactoryAgentCredentials("alice", "test-secret"),
                    transport=FactoryTransport(import_status=status),
                )
                with self.assertRaisesRegex(
                    EffectError, "rejected model import"
                ):
                    writer(self.context, self.release, self.manifest)
                intent = ledger.latest("verified-toy", "factory-import")
                self.assertIsNotNone(intent)
                self.assertEqual(intent.state, "rejected")

                corrected = FactoryReleaseWriter(
                    ledger,
                    "alice",
                    FactoryAgentCredentials("alice", "test-secret"),
                    transport=FactoryTransport(),
                )
                receipt = corrected(self.context, self.release, self.manifest)

                self.assertTrue(receipt.is_verified_draft)
                self.assertEqual(
                    ledger.get(intent.intent_id).state,
                    "succeeded",
                )


def draft_factory_content():
    return {
        "use_case": {
            "label": "A quick tabletop challenge",
            "body": "x" * 180,
            "image": "https://cdn.example/cover.png",
        },
        "story_blocks": [
            {
                "lead": "Digitally checked",
                "body": "y" * 180,
            }
        ],
    }


def draft_receipt():
    content = draft_factory_content()
    return Receipt(
        payload_sha256="f" * 64,
        artifact_sha256="a" * 64,
        adapter="factory",
        status="draft",
        observed_at=OBSERVED,
        reference="design-1",
        details={
            "product_id": "verified-toy",
            "release_sha256": "b" * 64,
            "playtest_evidence_sha256": "c" * 64,
            "handoff_artifact_sha256": "d" * 64,
            "product_page_sha256": "e" * 64,
            "manual_sha256": "1" * 64,
            "factory_content_sha256": hashlib.sha256(
                canonical_json(content)
            ).hexdigest(),
            "factory_content": content,
            "factory_content_mapping": "workshop-release-v3-to-factory-content-v1",
            "page_url": "https://www.autonomous.ai/factory/product/verified-toy",
        },
        design_id="design-1",
        slug="verified-toy",
        owner_id="owner-alice",
        root_id="design-1",
        current_history_id="history-1",
        project_url="https://cdn.autonomous.ai/projects/history-1/",
    )


class FactoryPublicTransitionTest(unittest.TestCase):
    def test_explicit_transition_is_fenced_then_proven_by_get(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger = EffectLedger(Path(temporary) / "effects.sqlite3")
            transport = FactoryTransport()
            content = draft_factory_content()
            transport.use_case = content["use_case"]
            transport.story_blocks = content["story_blocks"]
            session = FactoryAgentSession(
                FactoryAgentCredentials("alice", "test-secret"), transport=transport
            )
            receipt = FactoryPublicTransition(ledger, session).publish(draft_receipt())
        self.assertTrue(receipt.is_verified_public)
        publish = [call for call in transport.calls if call[1].endswith("/publish")]
        self.assertEqual(len(publish), 1)
        self.assertIsNone(publish[0][3])
        self.assertIn("Idempotency-Key", publish[0][2])

    def test_unknown_publication_never_blindly_retries(self):
        class UnknownPublish(FactoryTransport):
            def __call__(self, method, url, headers, body, timeout):
                if method == "POST" and url.endswith("/publish"):
                    self.calls.append((method, url, dict(headers), body, timeout))
                    raise RuntimeError("connection lost")
                return super().__call__(method, url, headers, body, timeout)

        with tempfile.TemporaryDirectory() as temporary:
            ledger = EffectLedger(Path(temporary) / "effects.sqlite3")
            transport = UnknownPublish()
            content = draft_factory_content()
            transport.use_case = content["use_case"]
            transport.story_blocks = content["story_blocks"]
            session = FactoryAgentSession(
                FactoryAgentCredentials("alice", "test-secret"), transport=transport
            )
            transition = FactoryPublicTransition(ledger, session)
            with self.assertRaises(AmbiguousEffectError):
                transition.publish(draft_receipt())
            with self.assertRaises(AmbiguousEffectError):
                transition.publish(draft_receipt())
        self.assertEqual(
            len([call for call in transport.calls if call[1].endswith("/publish")]),
            1,
        )

    def test_changed_page_content_is_not_published(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger = EffectLedger(Path(temporary) / "effects.sqlite3")
            transport = FactoryTransport()
            transport.use_case = {
                **draft_factory_content()["use_case"],
                "label": "Changed elsewhere",
            }
            transport.story_blocks = draft_factory_content()["story_blocks"]
            session = FactoryAgentSession(
                FactoryAgentCredentials("alice", "test-secret"), transport=transport
            )

            with self.assertRaisesRegex(StateConflict, "content changed"):
                FactoryPublicTransition(ledger, session).publish(draft_receipt())

        self.assertFalse(
            any(call[1].endswith("/publish") for call in transport.calls)
        )


if __name__ == "__main__":
    unittest.main()
