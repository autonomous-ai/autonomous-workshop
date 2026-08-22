from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from alice.adapters import adapter_input_sha256
from alice.cli import _adapters
from alice.config import load_config
from alice.page_builder import (
    AmbiguousPageBuilderEffect,
    PAGE_BUILDER_OPERATION,
    PageBuilderAdapter,
    PageBuilderError,
    PageBuilderReadback,
    build_publishdesign_preflight_receipt,
    snapshot_project,
)
from alice.store import DurableStore


class FakeDraftReadback:
    def __init__(self, project: Path) -> None:
        self.project = project
        self.calls: list[str] = []
        self.file_calls: list[str] = []
        self.remote_hash_overrides: dict[str, str] = {}
        self.design: dict[str, object] = {
            "id": "design-1",
            "slug": "river-council",
            "title": "River Council",
            "description": "A complete physical strategy game.",
            "status": "draft",
            "owner_id": "a" * 24,
            "current_history_id": "history-1",
            "published_history_id": None,
            "project_url": "https://cdn.example/design-1/history-1/",
            "thumbnail_urls": [
                "https://cdn.example/hero.png",
                "https://cdn.example/qa.png",
            ],
            "use_case": {
                "label": "On the table",
                "body": "A concrete player experience with enough detail for the product page.",
                "image": "https://cdn.example/hero.png",
            },
            "story_blocks": [
                {
                    "lead": "Setup",
                    "body": "Set the pieces, choose a side, and establish the first shared objective before play begins.",
                }
            ],
            "print_specs": {
                "part_count": 12,
                "materials": ["PLA"],
            },
        }

    def get_design(self, slug_or_id: str):
        self.calls.append(slug_or_id)
        return dict(self.design)

    def project_file_sha256(self, project_url: str, relative_path: str) -> str:
        self.file_calls.append(relative_path)
        if relative_path in self.remote_hash_overrides:
            return self.remote_hash_overrides[relative_path]
        return hashlib.sha256((self.project / relative_path).read_bytes()).hexdigest()


class ReadbackTransport:
    def get_design(self, slug_or_id: str):
        return {"id": slug_or_id}


class PageBuilderReadbackSecurityTests(unittest.TestCase):
    def test_project_fetch_requires_explicit_https_cdn_host(self) -> None:
        with self.assertRaisesRegex(ValueError, "host allowlist"):
            PageBuilderReadback(ReadbackTransport())
        readback = PageBuilderReadback(
            ReadbackTransport(), allowed_project_hosts=["cdn.example"]
        )
        for value in (
            "http://cdn.example/project/",
            "https://user:secret@cdn.example/project/",
            "https://127.0.0.1/project/",
            "https://cdn.example/project/?signed=secret",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(PageBuilderError, "approved"):
                    readback.project_file_sha256(value, "board.3mf")


class PageBuilderAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.idea = self.workspace / "board-game" / "ideas" / "river-council"
        self.project = self.idea / "project"
        self.project.mkdir(parents=True)
        self.model = self.project / "river-council.stl"
        self.model.write_bytes(b"solid river-council\nendsolid\n")
        self.rules_markdown = "# River Council Rules\n\nTake turns and score routes.\n"
        self.rules_file = self.project / "RULES.md"
        self.rules_file.write_text(self.rules_markdown, encoding="utf-8")
        (self.project / "main.py").write_text("print('river')\n", encoding="utf-8")
        self.calls = self.workspace / "operator-calls.jsonl"
        self.operator = self.workspace / "board-game" / "tools" / "publish.py"
        self.operator.parent.mkdir(parents=True, exist_ok=True)
        (self.operator.parent / "animation_gate.py").write_text(
            "ENABLED = True\n", encoding="utf-8"
        )
        (self.operator.parent / "journal.py").write_text(
            "import animation_gate\n", encoding="utf-8"
        )
        (self.operator.parent / "telegram.py").write_text(
            """
import os
from pathlib import Path

def load_env():
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                name, value = line.split("=", 1)
                os.environ.setdefault(name, value)

def send(message):
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        marker = Path(__file__).resolve().parents[2] / "telegram-called.txt"
        marker.write_text(message, encoding="utf-8")
""".strip()
            + "\n",
            encoding="utf-8",
        )
        self.operator.write_text(
            """
RULES_ARCHIVE_CONTRACT = "project-rules-byte-exact-v1"
ALICE_DRAFT_HANDOFF_CONTRACT = "alice-text2game-export-v1"

import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import journal
import telegram

workspace = Path.cwd()
slug = sys.argv[1]
telegram.load_env()
telegram.send("unexpected Telegram side effect")
with (workspace / "operator-calls.jsonl").open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({
        "args": sys.argv[1:],
        "operation_key": os.environ.get("ALICE_OPERATION_KEY"),
        "input_sha256": os.environ.get("ALICE_INPUT_SHA256"),
        "project_sha256": os.environ.get("ALICE_PROJECT_SHA256"),
        "dont_write_bytecode": os.environ.get("PYTHONDONTWRITEBYTECODE"),
        "pycache_prefix": os.environ.get("PYTHONPYCACHEPREFIX"),
        "telegram_bot_token": os.environ.get("TELEGRAM_BOT_TOKEN"),
        "telegram_chat_dm": os.environ.get("TELEGRAM_CHAT_DM"),
        "telegram_chat_journal": os.environ.get("TELEGRAM_CHAT_JOURNAL"),
    }, sort_keys=True) + "\\n")
published = {
    "id": "design-1",
    "slug": slug,
    "history_id": "history-1",
    "project_url": "https://cdn.example/design-1/history-1/",
    "status": "draft",
    "applied": ["use_case", "story_blocks(1)", "print_specs"],
}
path = workspace / "board-game" / "ideas" / slug / "published.json"
path.write_text(json.dumps(published), encoding="utf-8")
print(f"publish: {slug} -> import ok")
""".strip()
            + "\n",
            encoding="utf-8",
        )
        self.publishdesign = self.operator.parent / "bin" / "publishdesign"
        self.publishdesign.parent.mkdir()
        self.publishdesign.write_bytes(b"#!/bin/sh\nexit 99\n")
        self.publishdesign.chmod(0o700)
        (self.workspace / ".gitignore").write_text(
            "/board-game/tools/bin/publishdesign\n", encoding="utf-8"
        )
        git = shutil.which("git")
        if git is None:
            self.skipTest("git is required for PageBuilder pin tests")
        self.git_binary = Path(git).resolve()
        self._git("init", "--quiet")
        self._git("config", "user.name", "Alice PageBuilder Test")
        self._git("config", "user.email", "alice-page-builder@example.invalid")
        self._git("add", ".")
        self._git("commit", "--quiet", "-m", "pinned vibe fixture")
        self._refresh_pins()
        self.backend = self.workspace / "panda-social-backend"
        self.backend.mkdir()
        (self.backend / "go.mod").write_text(
            "module example.invalid/panda-social-backend\n", encoding="utf-8"
        )
        (self.backend / ".env").write_text(
            "MONGODB_URI=mongodb://fixture.invalid\n", encoding="utf-8"
        )
        (self.backend / ".env").chmod(0o600)
        self.gcs_credentials = self.backend / "gcs-sa.json"
        self.gcs_credentials.write_text('{"type":"service_account"}\n', encoding="utf-8")
        self.gcs_credentials.chmod(0o600)
        self.local_environment = {
            "PANDA_OWNER_ID": "a" * 24,
            "PANDA_BACKEND_DIR": str(self.backend),
            "GOOGLE_APPLICATION_CREDENTIALS": str(self.gcs_credentials),
        }
        self.publishdesign_preflight_receipt = (
            self.workspace / "publishdesign-preflight.json"
        )
        self._refresh_preflight_receipt()
        self.readback = FakeDraftReadback(self.project)
        self.store = DurableStore(self.workspace / "alice.sqlite3")

    def tearDown(self) -> None:
        self.store.close()
        self.temporary.cleanup()

    def _git(
        self, *arguments: str, input_bytes: bytes | None = None
    ) -> str:
        environment = dict(os.environ)
        environment.update(
            {
                "GIT_AUTHOR_NAME": "Alice PageBuilder Test",
                "GIT_AUTHOR_EMAIL": "alice-page-builder@example.invalid",
                "GIT_COMMITTER_NAME": "Alice PageBuilder Test",
                "GIT_COMMITTER_EMAIL": "alice-page-builder@example.invalid",
            }
        )
        result = subprocess.run(
            (str(self.git_binary), *arguments),
            cwd=self.workspace,
            env=environment,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return result.stdout.decode("utf-8").strip()

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.resolve().read_bytes()).hexdigest()

    def _refresh_pins(self) -> None:
        self.workspace_commit = self._git("rev-parse", "HEAD")
        self.interpreter_sha256 = self._sha256(Path(sys.executable))
        self.operator_sha256 = self._sha256(self.operator)
        self.operator_dependency_sha256 = {
            name: self._sha256(self.operator.parent / name)
            for name in ("animation_gate.py", "journal.py", "telegram.py")
        }
        self.publishdesign_sha256 = self._sha256(self.publishdesign)
        if hasattr(self, "publishdesign_preflight_receipt"):
            self._refresh_preflight_receipt()

    def _refresh_preflight_receipt(
        self, *, dry_run_overrides: dict[str, object] | None = None
    ) -> None:
        dry_run = {
            "dry_run": True,
            "mode": "import",
            "owner": "a" * 24,
            "owner_name": "Alice Fixture",
            "db": "panda-fixture",
            "bucket": "panda-fixture-bucket",
            "zip": "/private/tmp/alice-preflight.zip",
            "zip_bytes": 128,
            "title": "Alice preflight",
            "status": "draft",
            "tags": [],
            "thumbs": "/private/tmp/alice-cover.png",
            "description": "",
            "prompt_chars": 0,
        }
        dry_run.update(dry_run_overrides or {})
        raw = build_publishdesign_preflight_receipt(
            workspace_commit=self.workspace_commit,
            interpreter_sha256=self.interpreter_sha256,
            operator_sha256=self.operator_sha256,
            operator_dependency_sha256=self.operator_dependency_sha256,
            publishdesign_sha256=self.publishdesign_sha256,
            diagnostic_owner_id="a" * 24,
            backend_dir=self.backend.resolve(),
            backend_go_mod_sha256=self._sha256(self.backend / "go.mod"),
            backend_env_sha256=self._sha256(self.backend / ".env"),
            gcs_credentials=self.gcs_credentials.resolve(),
            gcs_credentials_sha256=self._sha256(self.gcs_credentials),
            dry_run=dry_run,
        )
        self.publishdesign_preflight_receipt.write_bytes(raw)
        self.publishdesign_preflight_receipt.chmod(0o600)
        self.publishdesign_preflight_sha256 = hashlib.sha256(raw).hexdigest()

    def _commit_operator(self, message: str) -> None:
        self._git("add", str(self.operator.relative_to(self.workspace)))
        self._git("commit", "--quiet", "-m", message)
        self._refresh_pins()

    def security_kwargs(self) -> dict[str, object]:
        return {
            "workspace_commit": self.workspace_commit,
            "interpreter_sha256": self.interpreter_sha256,
            "operator_sha256": self.operator_sha256,
            "operator_dependency_sha256": dict(
                self.operator_dependency_sha256
            ),
            "publishdesign_sha256": self.publishdesign_sha256,
            "publishdesign_preflight_receipt": (
                self.publishdesign_preflight_receipt
            ),
            "publishdesign_preflight_sha256": (
                self.publishdesign_preflight_sha256
            ),
            "git_binary": self.git_binary,
            "diagnostic_owner_id": "a" * 24,
        }

    def payload(self) -> dict[str, object]:
        snapshot = snapshot_project(self.project)
        artifact_hashes = {
            self.model.name: hashlib.sha256(self.model.read_bytes()).hexdigest(),
            "RULES.md": hashlib.sha256(self.rules_file.read_bytes()).hexdigest(),
        }
        candidate_hash = "c" * 64
        rules_hash = "d" * 64

        def dependency(content: dict[str, object]) -> dict[str, object]:
            return {
                "output_sha256": "f" * 64,
                "result": {
                    "executor": "adapter",
                    "receipt": {
                        "status": "passed",
                        "evidence_class": "manufacturing",
                        "payload": content,
                    },
                },
            }

        cad = {
            "slug": "river-council",
            "candidate_content_sha256": candidate_hash,
            "rules_sha256": rules_hash,
            "rules_file_sha256": artifact_hashes["RULES.md"],
            "artifact_hashes": artifact_hashes,
            "project_sha256": snapshot.project_sha256,
        }
        dfm = {
            "candidate_content_sha256": candidate_hash,
            "rules_sha256": rules_hash,
            "rules_file_sha256": artifact_hashes["RULES.md"],
            "artifact_hashes": artifact_hashes,
            "project_sha256": snapshot.project_sha256,
        }
        return {
            "candidate_id": "candidate-1",
            "candidate_version": 7,
            "candidate": {"title": "River Council"},
            "candidate_content_sha256": candidate_hash,
            "accepted_artifacts": [
                {
                    "action": "candidate.rules",
                    "task_id": "rules-task",
                    "candidate_version": 2,
                    "content": {
                        "rules_markdown": self.rules_markdown,
                        "rules_sha256": rules_hash,
                    },
                }
            ],
            "role": "publisher",
            "dependencies": {
                "physical.cad": dependency(cad),
                "physical.dfm": dependency(dfm),
            },
        }

    def adapter(self, **overrides: object) -> PageBuilderAdapter:
        return self.adapter_with_environment(self.local_environment, **overrides)

    def adapter_with_environment(
        self, environment: dict[str, str], **overrides: object
    ) -> PageBuilderAdapter:
        options = self.security_kwargs()
        options["timeout_seconds"] = 10
        options.update(overrides)
        with patch.dict(os.environ, environment, clear=True):
            return PageBuilderAdapter(
                self.workspace,
                [sys.executable, str(self.operator)],
                self.readback,
                self.store,
                **options,
            )

    def add_text2game_handoff(
        self, payload: dict[str, object]
    ) -> dict[str, object]:
        idea_bytes = b'{"components":[{"name":"token","qty":12}],"title":"River Council"}\n'
        (self.idea / "idea.json").write_bytes(idea_bytes)
        idea_copy = self.project / "_text2game" / "vibe-idea.json"
        idea_copy.parent.mkdir(parents=True, exist_ok=True)
        idea_copy.write_bytes(idea_bytes)
        snapshot = snapshot_project(self.project)
        artifacts = {
            str(item["path"]): str(item["sha256"]) for item in snapshot.files
        }
        source_artifacts = {
            "gdd.md": "1" * 64,
            "fe_parts/token.stl": "2" * 64,
        }
        source_artifacts_sha256 = hashlib.sha256(
            json.dumps(
                source_artifacts,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        dependencies = payload["dependencies"]
        self.assertIsInstance(dependencies, dict)
        cad = dependencies["physical.cad"]["result"]["receipt"]["payload"]
        dfm = dependencies["physical.dfm"]["result"]["receipt"]["payload"]
        receipt = {
            "schema_version": 1,
            "kind": "alice.text2game-export-receipt",
            "candidate_id": payload["candidate_id"],
            "candidate_version": payload["candidate_version"],
            "candidate_content_sha256": payload["candidate_content_sha256"],
            "production_slug": "river-council",
            "rules_sha256": cad["rules_sha256"],
            "rules_file_sha256": cad["rules_file_sha256"],
            "idea_sha256": hashlib.sha256(idea_bytes).hexdigest(),
            "project_sha256": snapshot.project_sha256,
            "artifact_hashes": artifacts,
            "source_artifact_hashes": source_artifacts,
            "source_artifact_hashes_sha256": source_artifacts_sha256,
            "source_snapshot_sha256": "3" * 64,
            "source_repo_url": "https://github.com/nohope88/text2game",
            "source_repo_commit": "4" * 40,
            "handoff": {
                "vibe_queue_transition_required": False,
                "vibe_queue_transition_performed": False,
                "publisher_invoked": False,
                "publisher_exact_rules_passthrough_required": True,
                "publisher_rules_archive_contract": "project-rules-byte-exact-v1",
                "publisher_alice_draft_handoff_contract": "alice-text2game-export-v1",
            },
        }
        receipt_hash = hashlib.sha256(
            (
                json.dumps(
                    receipt,
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                    allow_nan=False,
                )
                + "\n"
            ).encode("utf-8")
        ).hexdigest()
        (self.idea / ".alice-text2game-export.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        lineage = {
            "candidate_id": payload["candidate_id"],
            "candidate_version": payload["candidate_version"],
            "vibe_idea_sha256": receipt["idea_sha256"],
            "project_sha256": snapshot.project_sha256,
            "artifact_hashes": artifacts,
            "text2game_source_artifact_hashes": source_artifacts,
            "text2game_source_artifact_hashes_sha256": source_artifacts_sha256,
            "text2game_export_receipt_sha256": receipt_hash,
            "text2game_source_snapshot_sha256": receipt["source_snapshot_sha256"],
            "text2game_repo_url": receipt["source_repo_url"],
            "text2game_repo_commit": receipt["source_repo_commit"],
        }
        cad.update(lineage)
        dfm.update(lineage)
        return payload

    def test_invokes_only_existing_operator_and_binds_exact_rich_draft(self) -> None:
        ignored_binary = self._git(
            "status",
            "--ignored",
            "--short",
            "--",
            str(self.publishdesign.relative_to(self.workspace)),
        )
        self.assertTrue(ignored_binary.startswith("!!"))
        payload = self.payload()
        receipt = self.adapter().invoke(PAGE_BUILDER_OPERATION, payload)

        self.assertEqual(receipt.status, "passed")
        self.assertEqual(receipt.evidence_class, "publishing_pipeline")
        self.assertEqual(
            receipt.input_sha256,
            adapter_input_sha256(PAGE_BUILDER_OPERATION, payload),
        )
        self.assertEqual(receipt.payload["design_id"], "design-1")
        self.assertEqual(receipt.payload["history_id"], "history-1")
        self.assertEqual(receipt.payload["status"], "draft")
        self.assertEqual(
            receipt.payload["project_sha256"], snapshot_project(self.project).project_sha256
        )
        self.assertEqual(
            receipt.payload["rich_page"]["use_case"]["label"], "On the table"
        )
        call = json.loads(self.calls.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(call["args"], ["river-council"])
        self.assertEqual(call["operation_key"], receipt.payload["operation_key"])
        self.assertEqual(call["input_sha256"], receipt.input_sha256)
        self.assertEqual(call["project_sha256"], receipt.payload["project_sha256"])
        self.assertEqual(call["dont_write_bytecode"], "1")
        self.assertTrue(call["pycache_prefix"])
        self.assertEqual(call["telegram_bot_token"], "")
        self.assertEqual(call["telegram_chat_dm"], "")
        self.assertEqual(call["telegram_chat_journal"], "")
        self.assertFalse((self.operator.parent / "__pycache__").exists())
        self.assertEqual(
            set(self.readback.file_calls),
            {"river-council.stl", "RULES.md", "alice-provenance.json"},
        )
        self.assertTrue((self.idea / ".alice-rich-draft.json").is_file())

    def test_text2game_export_binds_the_exact_vibe_idea_and_source_lineage(self) -> None:
        payload = self.add_text2game_handoff(self.payload())

        receipt = self.adapter().invoke(PAGE_BUILDER_OPERATION, payload)

        binding = receipt.payload["text2game_export"]
        self.assertEqual(
            binding["vibe_idea_sha256"],
            hashlib.sha256((self.idea / "idea.json").read_bytes()).hexdigest(),
        )
        self.assertEqual(binding["source_repo_commit"], "4" * 40)

    def test_text2game_root_idea_drift_is_rejected_before_the_operator(self) -> None:
        payload = self.add_text2game_handoff(self.payload())
        (self.idea / "idea.json").write_text(
            '{"title":"A different storefront game"}\n', encoding="utf-8"
        )

        with self.assertRaisesRegex(PageBuilderError, "exact reviewed.*idea copy"):
            self.adapter().invoke(PAGE_BUILDER_OPERATION, payload)

        self.assertFalse(self.calls.exists())

    def test_text2game_export_receipt_must_keep_canonical_bytes(self) -> None:
        payload = self.add_text2game_handoff(self.payload())
        receipt_path = self.idea / ".alice-text2game-export.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        with self.assertRaisesRegex(PageBuilderError, "receipt is not canonical"):
            self.adapter().invoke(PAGE_BUILDER_OPERATION, payload)

        self.assertFalse(self.calls.exists())

    def test_matching_sidecar_makes_restart_a_verified_noop(self) -> None:
        adapter = self.adapter()
        payload = self.payload()
        first = adapter.invoke(PAGE_BUILDER_OPERATION, payload)
        second = adapter.invoke(PAGE_BUILDER_OPERATION, payload)

        self.assertEqual(first.payload["history_id"], second.payload["history_id"])
        self.assertEqual(len(self.calls.read_text(encoding="utf-8").splitlines()), 1)
        self.assertEqual(self.readback.calls, ["river-council", "river-council"])

    def test_preexisting_unbound_publish_is_ambiguous_and_never_invoked(self) -> None:
        (self.idea / "published.json").write_text(
            json.dumps({"id": "old-design"}), encoding="utf-8"
        )

        with self.assertRaisesRegex(AmbiguousPageBuilderEffect, "predates Alice"):
            self.adapter().invoke(PAGE_BUILDER_OPERATION, self.payload())

        self.assertFalse(self.calls.exists())
        self.assertEqual(self.readback.calls, [])

    def test_changed_artifact_is_rejected_before_the_operator(self) -> None:
        adapter = self.adapter()
        payload = self.payload()
        self.model.write_bytes(b"different model")

        with self.assertRaisesRegex(
            PageBuilderError, "tracked drift|workspace changed|artifact changed"
        ):
            adapter.invoke(PAGE_BUILDER_OPERATION, payload)

        self.assertFalse(self.calls.exists())
        self.assertEqual(self.readback.calls, [])

    def test_rules_only_artifact_maps_and_projects_are_rejected(self) -> None:
        payload = self.payload()
        dependencies = payload["dependencies"]
        self.assertIsInstance(dependencies, dict)
        for action in ("physical.cad", "physical.dfm"):
            content = dependencies[action]["result"]["receipt"]["payload"]
            content["artifact_hashes"] = {
                "RULES.md": hashlib.sha256(self.rules_file.read_bytes()).hexdigest()
            }
        with self.assertRaisesRegex(PageBuilderError, "printable"):
            self.adapter().invoke(PAGE_BUILDER_OPERATION, payload)

        self.model.unlink()
        with self.assertRaisesRegex(PageBuilderError, "printable"):
            snapshot_project(self.project)

    def test_backend_readback_must_be_private_exact_and_rich(self) -> None:
        self.readback.design["status"] = "public"

        with self.assertRaisesRegex(AmbiguousPageBuilderEffect, "exact receipt/readback"):
            self.adapter().invoke(PAGE_BUILDER_OPERATION, self.payload())

        self.assertTrue((self.idea / "published.json").is_file())
        self.assertFalse((self.idea / ".alice-rich-draft.json").exists())

    def test_any_nonzero_exit_after_launch_is_ambiguous(self) -> None:
        self.operator.write_text(
            'RULES_ARCHIVE_CONTRACT = "project-rules-byte-exact-v1"\n'
            'ALICE_DRAFT_HANDOFF_CONTRACT = "alice-text2game-export-v1"\n'
            "import sys\nsys.exit(7)\n",
            encoding="utf-8",
        )
        self._commit_operator("nonzero operator fixture")
        adapter = self.adapter()

        with self.assertRaisesRegex(
            AmbiguousPageBuilderEffect, "exited 7 after launch"
        ):
            adapter.invoke(PAGE_BUILDER_OPERATION, self.payload())

        self.assertEqual(self.readback.calls, [])

    def test_operator_output_is_bounded_after_single_writer_claim(self) -> None:
        self.operator.write_text(
            'RULES_ARCHIVE_CONTRACT = "project-rules-byte-exact-v1"\n'
            'ALICE_DRAFT_HANDOFF_CONTRACT = "alice-text2game-export-v1"\n'
            "print('x' * 4096)\n",
            encoding="utf-8",
        )
        self._commit_operator("large output operator fixture")
        adapter = self.adapter(maximum_stdout_bytes=128)

        with self.assertRaisesRegex(AmbiguousPageBuilderEffect, "stdout exceeded"):
            adapter.invoke(PAGE_BUILDER_OPERATION, self.payload())

    def test_remote_history_must_contain_the_exact_cad_artifact(self) -> None:
        self.readback.remote_hash_overrides["river-council.stl"] = "0" * 64

        with self.assertRaisesRegex(
            AmbiguousPageBuilderEffect, "exact artifact 'river-council.stl'"
        ):
            self.adapter().invoke(PAGE_BUILDER_OPERATION, self.payload())

        self.assertTrue((self.idea / "published.json").is_file())
        self.assertFalse((self.idea / ".alice-rich-draft.json").exists())

    def test_rejects_any_other_operation(self) -> None:
        with self.assertRaisesRegex(PageBuilderError, "only accepts"):
            self.adapter().invoke("publish.invoke_pipeline", self.payload())
        self.assertFalse(self.calls.exists())

    def test_operator_command_rejects_wrappers_flags_and_extra_arguments(self) -> None:
        invalid_commands = (
            ["env", sys.executable, str(self.operator)],
            [sys.executable, "-I", str(self.operator)],
            [sys.executable, str(self.operator), "--force"],
            [sys.executable, str(self.workspace / "other.py")],
        )
        for command in invalid_commands:
            with self.subTest(command=command):
                with self.assertRaisesRegex(ValueError, "exactly|no wrappers or flags"):
                    PageBuilderAdapter(
                        self.workspace,
                        command,
                        self.readback,
                        self.store,
                        **self.security_kwargs(),
                    )

    def test_operator_must_declare_exact_reviewed_rules_archive_contract(self) -> None:
        self.operator.write_text(
            self.operator.read_text(encoding="utf-8").replace(
                'RULES_ARCHIVE_CONTRACT = "project-rules-byte-exact-v1"\n',
                "",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "RULES_ARCHIVE_CONTRACT"):
            self.adapter()

    def test_operator_must_declare_exact_alice_private_draft_handoff(self) -> None:
        self.operator.write_text(
            self.operator.read_text(encoding="utf-8").replace(
                'ALICE_DRAFT_HANDOFF_CONTRACT = "alice-text2game-export-v1"\n',
                "",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "ALICE_DRAFT_HANDOFF_CONTRACT"):
            self.adapter()

    def test_operator_source_change_after_startup_fails_before_import(self) -> None:
        adapter = self.adapter()
        self.operator.write_text(
            self.operator.read_text(encoding="utf-8") + "# changed\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(PageBuilderError, "source changed"):
            adapter.invoke(PAGE_BUILDER_OPERATION, self.payload())

        self.assertFalse(self.calls.exists())

    def test_missing_or_changed_publishdesign_is_rejected_without_tofu(self) -> None:
        self.publishdesign.unlink()
        with self.assertRaisesRegex(ValueError, "publishdesign"):
            self.adapter()

    def test_wrong_publishdesign_bytes_are_rejected_without_tofu(self) -> None:
        self.publishdesign.write_bytes(b"#!/bin/sh\nexit 0\n")
        self.publishdesign.chmod(0o700)
        with self.assertRaisesRegex(ValueError, "publishdesign_sha256"):
            self.adapter()

    def test_clean_new_commit_cannot_redefine_the_reviewed_operator_pin(self) -> None:
        reviewed_operator_sha256 = self.operator_sha256
        self.operator.write_text(
            self.operator.read_text(encoding="utf-8") + "# unreviewed but committed\n",
            encoding="utf-8",
        )
        self._git("add", str(self.operator.relative_to(self.workspace)))
        self._git("commit", "--quiet", "-m", "unreviewed operator drift")
        unreviewed_commit = self._git("rev-parse", "HEAD")

        with self.assertRaisesRegex(ValueError, "operator_sha256"):
            self.adapter(
                workspace_commit=unreviewed_commit,
                operator_sha256=reviewed_operator_sha256,
            )

    def test_git_replace_refs_are_rejected_even_when_head_matches(self) -> None:
        tree = self._git("rev-parse", f"{self.workspace_commit}^{{tree}}")
        replacement = self._git(
            "commit-tree",
            tree,
            "-p",
            self.workspace_commit,
            input_bytes=b"replacement commit\n",
        )
        self._git("replace", self.workspace_commit, replacement)

        with self.assertRaisesRegex(ValueError, "replace refs"):
            self.adapter()

    def test_assume_unchanged_cannot_hide_tracked_drift(self) -> None:
        tracked = self.workspace / ".gitignore"
        self._git("update-index", "--assume-unchanged", ".gitignore")
        tracked.write_text(
            tracked.read_text(encoding="utf-8") + "# hidden drift\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "hidden or nonstandard"):
            self.adapter()

    def test_wrong_absolute_git_binary_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "git inspection"):
            self.adapter(git_binary=Path(sys.executable).resolve())

    def test_tracked_drift_after_preparation_is_caught_before_effect(self) -> None:
        import alice.page_builder as page_builder_module

        adapter = self.adapter()
        original_write = page_builder_module._write_exact_file

        def write_then_drift(path: Path, content: bytes) -> None:
            original_write(path, content)
            ignore = self.workspace / ".gitignore"
            ignore.write_text(
                ignore.read_text(encoding="utf-8") + "# tracked drift\n",
                encoding="utf-8",
            )

        with patch.object(
            page_builder_module, "_write_exact_file", side_effect=write_then_drift
        ):
            with self.assertRaisesRegex(PageBuilderError, "tracked drift"):
                adapter.invoke(PAGE_BUILDER_OPERATION, self.payload())

        self.assertFalse(self.calls.exists())

    def test_dependency_drift_fails_diagnostics_before_remote_read(self) -> None:
        adapter = self.adapter(diagnostic_design_id="river-council")
        dependency = self.operator.parent / "journal.py"
        dependency.write_text(
            dependency.read_text(encoding="utf-8") + "# changed\n",
            encoding="utf-8",
        )

        diagnostics = adapter.diagnostics()

        self.assertFalse(diagnostics["ready"])
        self.assertFalse(diagnostics["authenticated"])
        self.assertEqual(diagnostics["reason"], "workspace_integrity_failed")
        self.assertEqual(self.readback.calls, [])

    def test_untracked_python_in_operator_directory_is_rejected(self) -> None:
        (self.operator.parent / "surprise.py").write_text(
            "raise RuntimeError('unreviewed')\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "unreviewed untracked file"):
            self.adapter()

    def test_workspace_dotenv_is_rejected_before_it_can_reenable_telegram(self) -> None:
        (self.workspace / ".env").write_text(
            "TELEGRAM_BOT_TOKEN=workspace-secret\n"
            "TELEGRAM_CHAT_DM=owner-chat\n"
            "TELEGRAM_CHAT_JOURNAL=journal-chat\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "workspace .env is forbidden"):
            self.adapter()
        self.assertFalse((self.workspace / "telegram-called.txt").exists())

    def test_local_backend_owner_and_secret_paths_are_required(self) -> None:
        cases = {
            "owner": {
                **self.local_environment,
                "PANDA_OWNER_ID": "b" * 24,
            },
            "backend": {
                **self.local_environment,
                "PANDA_BACKEND_DIR": str(self.workspace / "missing-backend"),
            },
            "credentials": {
                **self.local_environment,
                "GOOGLE_APPLICATION_CREDENTIALS": str(
                    self.workspace / "missing-credentials.json"
                ),
            },
        }
        for label, environment in cases.items():
            with self.subTest(label=label):
                with self.assertRaisesRegex(
                    ValueError,
                    "PANDA_OWNER_ID|PANDA_BACKEND_DIR|GOOGLE_APPLICATION_CREDENTIALS",
                ):
                    self.adapter_with_environment(environment)

    def test_local_credentials_are_rechecked_before_effect(self) -> None:
        adapter = self.adapter()
        self.gcs_credentials.unlink()

        with self.assertRaisesRegex(
            PageBuilderError, "GOOGLE_APPLICATION_CREDENTIALS"
        ):
            adapter.invoke(PAGE_BUILDER_OPERATION, self.payload())

        self.assertFalse(self.calls.exists())

    def test_preflight_receipt_must_be_present_owner_only_and_hash_pinned(self) -> None:
        self.publishdesign_preflight_receipt.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "owner-only"):
            self.adapter()

        self.publishdesign_preflight_receipt.chmod(0o600)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.adapter(publishdesign_preflight_sha256="0" * 64)

        self.publishdesign_preflight_receipt.unlink()
        with self.assertRaisesRegex(ValueError, "receipt is unavailable"):
            self.adapter()

    def test_preflight_receipt_must_keep_canonical_bytes(self) -> None:
        receipt = json.loads(
            self.publishdesign_preflight_receipt.read_text(encoding="utf-8")
        )
        raw = json.dumps(receipt, separators=(",", ":")).encode("utf-8")
        self.publishdesign_preflight_receipt.write_bytes(raw)
        self.publishdesign_preflight_receipt.chmod(0o600)
        digest = hashlib.sha256(raw).hexdigest()

        with self.assertRaisesRegex(ValueError, "not canonical"):
            self.adapter(publishdesign_preflight_sha256=digest)

    def test_preflight_receipt_top_level_fields_are_exact(self) -> None:
        receipt = json.loads(
            self.publishdesign_preflight_receipt.read_text(encoding="utf-8")
        )
        receipt["unreviewed"] = True
        raw = (
            json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode("utf-8")
        self.publishdesign_preflight_receipt.write_bytes(raw)
        self.publishdesign_preflight_receipt.chmod(0o600)
        digest = hashlib.sha256(raw).hexdigest()

        with self.assertRaisesRegex(ValueError, "top-level fields are not exact"):
            self.adapter(publishdesign_preflight_sha256=digest)

    def test_content_only_preflight_cannot_prove_first_import_readiness(self) -> None:
        receipt = json.loads(
            self.publishdesign_preflight_receipt.read_text(encoding="utf-8")
        )
        receipt["dry_run"]["mode"] = "page"
        receipt["dry_run"]["zip"] = ""
        receipt["dry_run"]["zip_bytes"] = 0
        raw = (
            json.dumps(
                receipt,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        self.publishdesign_preflight_receipt.write_bytes(raw)
        self.publishdesign_preflight_receipt.chmod(0o600)
        digest = hashlib.sha256(raw).hexdigest()

        with self.assertRaisesRegex(ValueError, "receipt values are invalid"):
            self.adapter(publishdesign_preflight_sha256=digest)

    def test_preflight_local_hashes_are_rechecked_by_diagnostics_and_invoke(self) -> None:
        diagnostics_adapter = self.adapter(diagnostic_design_id="river-council")
        backend_env = self.backend / ".env"
        backend_env.write_text(
            "MONGODB_URI=mongodb://different.invalid\n", encoding="utf-8"
        )
        backend_env.chmod(0o600)

        diagnostics = diagnostics_adapter.diagnostics()
        self.assertFalse(diagnostics["ready"])
        self.assertFalse(diagnostics["authenticated"])
        self.assertEqual(
            diagnostics["reason"], "publishdesign_dry_run_not_proven"
        )
        self.assertEqual(self.readback.calls, [])

        with self.assertRaisesRegex(
            PageBuilderError, "backend_env_sha256 does not match"
        ):
            diagnostics_adapter.invoke(PAGE_BUILDER_OPERATION, self.payload())
        self.assertFalse(self.calls.exists())

    def test_preflight_receipt_is_rechecked_after_last_local_preparation(self) -> None:
        import alice.page_builder as page_builder_module

        adapter = self.adapter()
        original_write = page_builder_module._write_exact_file

        def write_then_invalidate_receipt(path: Path, content: bytes) -> None:
            original_write(path, content)
            self.publishdesign_preflight_receipt.write_bytes(
                self.publishdesign_preflight_receipt.read_bytes() + b"\n"
            )

        with patch.object(
            page_builder_module,
            "_write_exact_file",
            side_effect=write_then_invalidate_receipt,
        ):
            with self.assertRaisesRegex(PageBuilderError, "receipt SHA-256"):
                adapter.invoke(PAGE_BUILDER_OPERATION, self.payload())

        self.assertFalse(self.calls.exists())

    def test_default_operator_environment_excludes_telegram_credentials(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "TELEGRAM_BOT_TOKEN": "must-not-forward",
                "TELEGRAM_CHAT_ID": "must-not-forward",
            },
        ):
            adapter = self.adapter()

        self.assertNotIn("TELEGRAM_BOT_TOKEN", adapter.environment)
        self.assertNotIn("TELEGRAM_CHAT_ID", adapter.environment)

    def test_diagnostics_require_an_authenticated_matching_owner_read(self) -> None:
        adapter = self.adapter(diagnostic_design_id="river-council")

        diagnostics = adapter.diagnostics()

        self.assertTrue(diagnostics["ready"])
        self.assertTrue(diagnostics["authenticated"])
        self.assertEqual(self.readback.calls, ["river-council"])

    def test_diagnostics_reject_public_or_wrong_owner_optional_auth_reads(self) -> None:
        adapter = self.adapter(diagnostic_design_id="river-council")
        original = dict(self.readback.design)
        cases = (
            (
                {"status": "public", "published_history_id": "history-1"},
                "diagnostic_design_not_private_draft",
            ),
            (
                {"owner_id": "b" * 24},
                "diagnostic_design_owner_mismatch",
            ),
            (
                {"current_history_id": ""},
                "diagnostic_design_history_missing",
            ),
            (
                {"published_history_id": "history-1"},
                "diagnostic_design_has_published_history",
            ),
        )
        for changes, reason in cases:
            with self.subTest(reason=reason):
                self.readback.design = {**original, **changes}
                diagnostics = adapter.diagnostics()
                self.assertFalse(diagnostics["ready"])
                self.assertFalse(diagnostics["authenticated"])
                self.assertEqual(diagnostics["reason"], reason)

    def test_durable_sender_claim_prevents_a_second_import(self) -> None:
        payload = self.payload()
        snapshot = snapshot_project(self.project)
        operation_key = (
            "alice:rich-draft:candidate-1:v7:"
            f"{snapshot.project_sha256[:20]}"
        )
        self.store.put_state(
            f"alice.effect:rich-draft:{operation_key}",
            {"status": "sending"},
            None,
        )

        with self.assertRaisesRegex(
            AmbiguousPageBuilderEffect, "already claimed"
        ):
            self.adapter().invoke(PAGE_BUILDER_OPERATION, payload)

        self.assertFalse(self.calls.exists())

    def test_cli_wires_private_draft_adapter_only_outside_dry_run(self) -> None:
        config = load_config()
        config["runtime"]["effect_mode"] = "draft"
        config["adapters"]["page_builder"] = {
            **config["adapters"]["page_builder"],
            "enabled": True,
            "workspace": str(self.workspace),
            "workspace_commit": self.workspace_commit,
            "operator_command": [sys.executable, str(self.operator)],
            "interpreter_sha256": self.interpreter_sha256,
            "operator_sha256": self.operator_sha256,
            "operator_dependency_sha256": dict(
                self.operator_dependency_sha256
            ),
            "publishdesign_sha256": self.publishdesign_sha256,
            "publishdesign_preflight_receipt": str(
                self.publishdesign_preflight_receipt
            ),
            "publishdesign_preflight_sha256": (
                self.publishdesign_preflight_sha256
            ),
            "git_binary": str(self.git_binary),
            "diagnostic_design_id": "river-council",
            "diagnostic_owner_id": "a" * 24,
            "allowed_project_hosts": ["cdn.example"],
        }
        store = DurableStore(self.workspace / "alice.sqlite3")
        try:
            with patch.dict(
                "os.environ",
                {"ALICE_FACTORY_TOKEN": "test-token", **self.local_environment},
            ):
                adapters = _adapters(config, store)
            self.assertIsInstance(adapters["page_builder"], PageBuilderAdapter)

            config["runtime"]["effect_mode"] = "dry-run"
            with self.assertRaisesRegex(SystemExit, "private remote draft"):
                with patch.dict(
                    "os.environ",
                    {"ALICE_FACTORY_TOKEN": "test-token", **self.local_environment},
                ):
                    _adapters(config, store)
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
