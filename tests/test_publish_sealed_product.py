import contextlib
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

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.errors import ContractError, StateConflict
from inventor_workshop.shop import HttpResponse
from inventor_workshop.store import InventorStore
from tools import publish_sealed_product as command


REPO_ROOT = Path(__file__).resolve().parents[1]
RESULT_IDS = (
    "agent-playtest",
    "classic-rules-test",
    "mechanical-test",
    "print-test",
)


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _multipart(headers, body):
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
        parts.setdefault(name, []).append(
            {
                "filename": part.get_filename(),
                "content_type": part.get_content_type(),
                "content": part.get_payload(decode=True),
            }
        )
    return parts


def _tree_bytes(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class PrivateDraftTransport:
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
        self.cover_url = "https://cdn.example/sealed/cover.png"
        self.imported_thumbnail = None
        self.imported_pack = None
        self.uploads = []
        self.use_case = None
        self.story_blocks = []
        self.roles = ("hero", "play", "detail", "parts", "box")
        self.urls = {
            role: "https://cdn.example/sealed/%s.png" % role
            for role in self.roles
        }

    def design(self):
        return {
            "id": "design-sealed-1",
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "owner_id": self.owner_id,
            "root_id": "design-sealed-1",
            "current_history_id": "history-sealed-1",
            "published_history_id": None,
            "status": "draft",
            "project_url": "https://cdn.autonomous.ai/projects/history-sealed-1/",
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
            raise AssertionError("publisher omitted authenticated Shop request")
        if url.endswith("/publish"):
            raise AssertionError("sealed product publisher must never publish public")
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
            self.tags = [
                item["content"].decode("utf-8") for item in parts["tags"]
            ]
            self.category = fields["category"]
            if "thumbnails" in parts:
                raise AssertionError("model-only import must not send thumbnails")
            self.exists = True
            return HttpResponse(201, {}, json.dumps(self.design()).encode())
        if method == "POST" and url.endswith("/uploads"):
            part = _multipart(headers, body)["file"][0]
            content = part["content"]
            role = self.roles[len(self.uploads)]
            self.uploads.append((role, content))
            return HttpResponse(
                201,
                {},
                json.dumps(
                    {
                        "url": self.urls[role],
                        "ref": "gs://sealed/%s" % part["filename"],
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
        raise AssertionError("unexpected Shop request %s %s" % (method, url))


class SealedProductFixture:
    def __init__(self, root, *, failed_id=None):
        self.repo = root / "repo"
        self.bundle = (
            self.repo / "inventors" / "alice" / "toys" / "five-job-checkers"
        )
        source = REPO_ROOT / "inventors" / "alice"
        self.bundle.mkdir(parents=True)
        shutil.copytree(
            source / "toys" / "five-job-checkers" / "artifact",
            self.bundle / "artifact",
        )
        shutil.copytree(
            source / "toys" / "five-job-checkers" / "instructions",
            self.bundle / "instructions",
        )
        shutil.copy2(source / "TASTE.md", self.repo / "inventors" / "alice")

        self.round = self.bundle / "playtest" / "round-01"
        self.round.mkdir(parents=True)
        make_manifest = build_artifact_manifest(
            self.bundle / "artifact", created_at="content-addressed"
        )
        self.make_manifest_path = self.round / "make-manifest.json"
        _write_json(self.make_manifest_path, make_manifest.to_dict())

        wrappers = self.round / "wrappers"
        results_root = self.round / "evidence" / "results"
        wrappers.mkdir()
        results_root.mkdir(parents=True)
        wrapper_records = []
        claims = {}
        for result_id in RESULT_IDS:
            passed = result_id != failed_id
            claim = "%s was checked by deterministic AI players." % result_id
            body = {
                "schema_version": 1,
                "playtest_id": result_id,
                "artifact_sha256": make_manifest.artifact_sha256,
                "passed": passed,
                "evidence_class": "ai-simulation",
                "claims": [claim],
            }
            if result_id == "agent-playtest":
                body["agent_roles"] = [
                    "first-time owner",
                    "adversarial tabletop player",
                ]
            result_path = results_root / (result_id + ".json")
            _write_json(result_path, body)
            result_sha = _sha256(result_path)
            evidence_ref = "results/%s.json" % result_id
            wrapper = {
                "inspection_id": result_id,
                "passed": passed,
                "artifact_sha256": make_manifest.artifact_sha256,
                "evidence": {
                    "evidence_class": "ai-simulation",
                    "result_file_sha256": result_sha,
                },
                "evaluator": "sealed-product-test-ai-panel",
                "evaluator_version": "1.0.0",
                "config_sha256": hashlib.sha256(result_id.encode()).hexdigest(),
                "evidence_ref": evidence_ref,
                "evidence_sha256": result_sha,
                "observed_at": "2026-08-24T12:00:00+00:00",
            }
            wrapper_path = wrappers / (result_id + ".json")
            _write_json(wrapper_path, wrapper)
            wrapper_records.append(
                {
                    "playtest_id": result_id,
                    "passed": passed,
                    "evidence_ref": "evidence/" + evidence_ref,
                    "evidence_sha256": result_sha,
                    "wrapper": "wrappers/%s.json" % result_id,
                    "wrapper_sha256": _sha256(wrapper_path),
                }
            )
            claims[result_id] = {
                "passed": passed,
                "evidence_class": "ai-simulation",
                "claims": [claim],
                "evidence_ref": evidence_ref,
                "evidence_sha256": result_sha,
                "evaluator": "sealed-product-test-ai-panel",
                "evaluator_version": "1.0.0",
            }

        evidence_manifest = build_artifact_manifest(
            self.round / "evidence", created_at="content-addressed"
        )
        self.evidence_manifest_path = self.round / "evidence-manifest.json"
        _write_json(self.evidence_manifest_path, evidence_manifest.to_dict())
        feedback = {
            "schema_version": 1,
            "artifact_sha256": make_manifest.artifact_sha256,
            "overall_passed": failed_id is None,
            "feedback": [],
        }
        feedback_path = self.round / "feedback.json"
        _write_json(feedback_path, feedback)
        index = {
            "schema_version": 1,
            "artifact_sha256": make_manifest.artifact_sha256,
            "overall_passed": failed_id is None,
            "unresolved_canonical_capabilities": (
                [] if failed_id is None else [failed_id]
            ),
            "evidence_manifest": {
                "artifact_sha256": evidence_manifest.artifact_sha256,
                "path": "evidence-manifest.json",
            },
            "feedback": {
                "path": "feedback.json",
                "sha256": _sha256(feedback_path),
                "count": 0,
            },
            "result_summary": {
                "passed": [item for item in RESULT_IDS if item != failed_id],
                "failed": [] if failed_id is None else [failed_id],
            },
            "results": wrapper_records,
        }
        self.index_path = self.round / "evidence-index.json"
        _write_json(self.index_path, index)

        page_path = self.bundle / "instructions" / "product.json"
        page = json.loads(page_path.read_text(encoding="utf-8"))
        page["product_artifact_sha256"] = make_manifest.artifact_sha256
        page["playtest_evidence_artifact_sha256"] = (
            evidence_manifest.artifact_sha256
        )
        page["claims"] = claims
        _write_json(page_path, page)
        instructions_manifest = build_artifact_manifest(
            self.bundle / "instructions", created_at="content-addressed"
        )
        self.instructions_manifest_path = self.bundle / "instructions-manifest.json"
        _write_json(self.instructions_manifest_path, instructions_manifest.to_dict())

        taste_path = self.repo / "inventors" / "alice" / "TASTE.md"
        descriptor = {
            "schema_version": 1,
            "kind": "workshop.sealed-private-draft",
            "inventor_id": "alice",
            "taste_sha256": _sha256(taste_path),
            "make": {
                "root": "inventors/alice/toys/five-job-checkers/artifact",
                "manifest": (
                    "inventors/alice/toys/five-job-checkers/playtest/"
                    "round-01/make-manifest.json"
                ),
                "artifact_sha256": make_manifest.artifact_sha256,
            },
            "playtest": {
                "root": "inventors/alice/toys/five-job-checkers/playtest/round-01",
                "evidence_artifact_sha256": evidence_manifest.artifact_sha256,
                "index_sha256": _sha256(self.index_path),
            },
            "instructions": {
                "root": "inventors/alice/toys/five-job-checkers/instructions",
                "manifest": "inventors/alice/toys/five-job-checkers/instructions-manifest.json",
                "artifact_sha256": instructions_manifest.artifact_sha256,
            },
        }
        self.descriptor = self.bundle / "private-draft.json"
        _write_json(self.descriptor, descriptor)
        self.make_sha256 = make_manifest.artifact_sha256


class PublishSealedProductTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.fixture = SealedProductFixture(self.root)
        self.state_root = self.root / "state"

    def test_exact_seals_create_one_private_draft_and_retry_idempotently(self):
        before = _tree_bytes(self.fixture.bundle)
        transport = PrivateDraftTransport("five-job-checkers", "owner-1")

        first = command.publish_sealed_draft(
            self.fixture.descriptor,
            token="test-token",
            owner_id="owner-1",
            repo_root=self.fixture.repo,
            state_root=self.state_root,
            transport=transport,
        )

        self.assertEqual(first["status"], "draft-created")
        self.assertEqual(first["enrichment_status"], "pending")
        self.assertIs(first["page_ready"], False)
        self.assertIsNone(transport.imported_thumbnail)
        self.assertEqual(transport.uploads, [])
        self.assertTrue(transport.description.endswith("By Alice."))
        self.assertEqual(transport.description.count("By Alice."), 1)
        self.assertEqual(transport.design()["status"], "draft")
        self.assertIsNone(transport.design()["published_history_id"])
        self.assertEqual(_tree_bytes(self.fixture.bundle), before)
        self.assertEqual(
            [call[0] for call in transport.calls],
            ["GET", "POST", "GET"],
        )
        self.assertFalse(
            any(url.endswith("/publish") for _, url, _, _, _ in transport.calls)
        )
        with zipfile.ZipFile(io.BytesIO(transport.imported_pack)) as archive:
            names = set(archive.namelist())
            self.assertEqual(
                json.loads(archive.read("project.json")),
                {"id": "five-job-checkers", "name": "Five-Job Checkers"},
            )
            self.assertNotIn("images/hero.png", names)
            self.assertIn("five-job-checkers.stl", names)
            self.assertNotIn("assembled.stl", names)
            self.assertEqual(
                archive.read("five-job-checkers.stl"),
                (
                    self.fixture.bundle / "artifact" / "assembled.stl"
                ).read_bytes(),
            )
            self.assertNotIn("cad/product.stl", names)
            source_sidecar = json.loads(
                (
                    self.fixture.bundle / "artifact" / "assembled.step.json"
                ).read_text(encoding="utf-8")
            )
            occurrence_paths = [
                "five-job-checkers_parts/%s.stl" % item["name"]
                for item in source_sidecar["parts"]
            ]
            self.assertEqual(
                sorted(name for name in names if name.endswith(".stl")),
                sorted(["five-job-checkers.stl"] + occurrence_paths),
            )
            self.assertEqual(len(occurrence_paths), 25)
            self.assertFalse(
                any(
                    name.startswith("cad/parts/") and name.endswith(".stl")
                    for name in names
                )
            )
            self.assertNotIn("assembled.step", names)
            self.assertNotIn("assembled.step.json", names)
            self.assertEqual(
                archive.read("five-job-checkers.step"),
                (
                    self.fixture.bundle / "artifact" / "assembled.step"
                ).read_bytes(),
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
                        self.fixture.bundle
                        / "artifact"
                        / source_item["stlPath"]
                    ).read_bytes(),
                )
            self.assertIn("workshop-product-facts.json", names)
            self.assertEqual(
                json.loads(archive.read("product.json"))["description"].count(
                    "By Alice."
                ),
                1,
            )
            facts = json.loads(archive.read("workshop-product-facts.json"))
            self.assertEqual(facts["product"]["description"].count("By Alice."), 1)
            self.assertEqual(facts["source_artifact_sha256"], self.fixture.make_sha256)
            self.assertEqual(facts["factory_assembly"]["occurrence_count"], 25)

        call_count = len(transport.calls)
        replay = command.publish_sealed_draft(
            self.fixture.descriptor,
            token="test-token",
            owner_id="owner-1",
            repo_root=self.fixture.repo,
            state_root=self.state_root,
            transport=transport,
        )
        self.assertEqual(replay["status"], "replayed")
        self.assertEqual(len(transport.calls), call_count)
        self.assertEqual(_tree_bytes(self.fixture.bundle), before)
        database = self.state_root / "five-job-checkers" / "workshop.sqlite3"
        self.assertNotIn(b"test-token", database.read_bytes())
        self.assertNotIn("test-token", json.dumps(first))
        store = InventorStore(database)
        self.assertEqual(
            store.latest_publish_intent("five-job-checkers")["state"], "succeeded"
        )

    def test_existing_canonical_slug_stops_before_import(self):
        transport = PrivateDraftTransport(
            "five-job-checkers", "owner-1", first_get_status=200
        )
        with self.assertRaisesRegex(StateConflict, "already exists"):
            command.publish_sealed_draft(
                self.fixture.descriptor,
                token="test-token",
                owner_id="owner-1",
                repo_root=self.fixture.repo,
                state_root=self.state_root,
                transport=transport,
            )
        self.assertEqual([call[0] for call in transport.calls], ["GET"])
        store = InventorStore(
            self.state_root / "five-job-checkers" / "workshop.sqlite3"
        )
        self.assertIsNone(store.latest_publish_intent("five-job-checkers"))

    def test_failed_playtest_is_rejected_before_state_or_network(self):
        failed = SealedProductFixture(self.root / "failed", failed_id="print-test")
        transport = PrivateDraftTransport("five-job-checkers", "owner-1")
        with self.assertRaisesRegex(ContractError, "not an all-pass"):
            command.publish_sealed_draft(
                failed.descriptor,
                token="test-token",
                owner_id="owner-1",
                repo_root=failed.repo,
                state_root=self.root / "failed-state",
                transport=transport,
            )
        self.assertEqual(transport.calls, [])
        self.assertFalse((self.root / "failed-state").exists())

    def test_local_instruction_media_is_rejected_before_network(self):
        instructions = self.fixture.bundle / "instructions"
        (instructions / "creator-hero.png").write_bytes(b"creator marketing image")
        manifest = build_artifact_manifest(
            instructions, created_at="content-addressed"
        )
        _write_json(self.fixture.instructions_manifest_path, manifest.to_dict())
        descriptor = json.loads(
            self.fixture.descriptor.read_text(encoding="utf-8")
        )
        descriptor["instructions"]["artifact_sha256"] = manifest.artifact_sha256
        _write_json(self.fixture.descriptor, descriptor)
        transport = PrivateDraftTransport("five-job-checkers", "owner-1")
        with self.assertRaisesRegex(ContractError, "creator page media"):
            command.publish_sealed_draft(
                self.fixture.descriptor,
                token="test-token",
                owner_id="owner-1",
                repo_root=self.fixture.repo,
                state_root=self.root / "duplicate-image-state",
                transport=transport,
            )
        self.assertEqual(transport.calls, [])

    def test_cli_credentials_are_environment_only(self):
        with self.assertRaises(SystemExit):
            command._credentials({})
        with self.assertRaises(SystemExit):
            command._credentials({"WORKSHOP_SHOP_TOKEN": "token"})
        self.assertEqual(
            command._credentials(
                {
                    "WORKSHOP_SHOP_TOKEN": "token",
                    "WORKSHOP_SHOP_OWNER_ID": "owner",
                }
            ),
            ("token", "owner"),
        )
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                command._parser().parse_args(
                    ["sealed-draft.json", "--token", "must-not-be-supported"]
                )


if __name__ == "__main__":
    unittest.main()
