from __future__ import annotations

import hashlib
import json
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
            "current_history_id": "history-1",
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
        self.operator.write_text(
            """
import json
import os
from pathlib import Path
import sys

workspace = Path.cwd()
slug = sys.argv[1]
with (workspace / "operator-calls.jsonl").open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({
        "args": sys.argv[1:],
        "operation_key": os.environ.get("ALICE_OPERATION_KEY"),
        "input_sha256": os.environ.get("ALICE_INPUT_SHA256"),
        "project_sha256": os.environ.get("ALICE_PROJECT_SHA256"),
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
        self.readback = FakeDraftReadback(self.project)
        self.store = DurableStore(self.workspace / "alice.sqlite3")

    def tearDown(self) -> None:
        self.store.close()
        self.temporary.cleanup()

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

    def adapter(self) -> PageBuilderAdapter:
        return PageBuilderAdapter(
            self.workspace,
            [sys.executable, str(self.operator)],
            self.readback,
            self.store,
            timeout_seconds=10,
        )

    def test_invokes_only_existing_operator_and_binds_exact_rich_draft(self) -> None:
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
        self.assertEqual(
            set(self.readback.file_calls),
            {"river-council.stl", "RULES.md", "alice-provenance.json"},
        )
        self.assertTrue((self.idea / ".alice-rich-draft.json").is_file())

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
        payload = self.payload()
        self.model.write_bytes(b"different model")

        with self.assertRaisesRegex(PageBuilderError, "workspace changed|artifact changed"):
            self.adapter().invoke(PAGE_BUILDER_OPERATION, payload)

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
        self.operator.write_text("import sys\nsys.exit(7)\n", encoding="utf-8")
        adapter = PageBuilderAdapter(
            self.workspace,
            [sys.executable, str(self.operator)],
            self.readback,
            self.store,
            timeout_seconds=10,
        )

        with self.assertRaisesRegex(
            AmbiguousPageBuilderEffect, "exited 7 after launch"
        ):
            adapter.invoke(PAGE_BUILDER_OPERATION, self.payload())

        self.assertEqual(self.readback.calls, [])

    def test_operator_output_is_bounded_after_single_writer_claim(self) -> None:
        self.operator.write_text("print('x' * 4096)\n", encoding="utf-8")
        adapter = PageBuilderAdapter(
            self.workspace,
            [sys.executable, str(self.operator)],
            self.readback,
            self.store,
            timeout_seconds=10,
            maximum_stdout_bytes=128,
        )

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
                    )

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
        adapter = PageBuilderAdapter(
            self.workspace,
            [sys.executable, str(self.operator)],
            self.readback,
            self.store,
            diagnostic_design_id="river-council",
        )

        diagnostics = adapter.diagnostics()

        self.assertTrue(diagnostics["ready"])
        self.assertTrue(diagnostics["authenticated"])
        self.assertEqual(self.readback.calls, ["river-council"])

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
            "operator_command": [sys.executable, str(self.operator)],
            "allowed_project_hosts": ["cdn.example"],
        }
        store = DurableStore(self.workspace / "alice.sqlite3")
        try:
            with patch.dict("os.environ", {"ALICE_FACTORY_TOKEN": "test-token"}):
                adapters = _adapters(config, store)
            self.assertIsInstance(adapters["page_builder"], PageBuilderAdapter)

            config["runtime"]["effect_mode"] = "dry-run"
            with self.assertRaisesRegex(SystemExit, "private remote draft"):
                with patch.dict("os.environ", {"ALICE_FACTORY_TOKEN": "test-token"}):
                    _adapters(config, store)
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
