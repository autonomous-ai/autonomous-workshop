import hashlib
import io
import json
import os
from unittest.mock import patch
import tempfile
import unittest
import zipfile
from pathlib import Path

from workshop.errors import ContractError, StateConflict
from workshop.release.public_archive import build_public_archive_manifest
from workshop.workflow import AgentRun
from workshop.workflow.revision import (
    prepare_revision, materialize_revision, revision_input, REVISION_INPUT,
)


class RevisionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "published"
        self.source.mkdir()
        self.write("make/source/toy.step.py", b"# original CAD\n")
        self.write("wish/wish.json", b'{"objective":"original rules"}')
        self.publication = {
            "kind": "autonomous-workshop.public-toy-snapshot", "schema_version": 2,
            "title": "Original", "inventor": {"id": "mara-masque"},
            "publication": {"status": "public", "page_url": "https://example.com/original"},
        }
        self.seal()

    def write(self, name, content):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def seal(self):
        self.write("publication/PUBLICATION.json", json.dumps(self.publication).encode())
        manifest = build_public_archive_manifest(self.source)
        self.write("MANIFEST.json", json.dumps({
            "schema_version": 4, "kind": "autonomous-workshop.public-toy-archive",
            "artifact_manifest": manifest.to_dict(),
        }).encode())

    def test_clone_is_independent_and_prompt_exact(self):
        prompt = "Correct the dice.\n\nKeep all rules.\n"
        wish, snapshot = prepare_revision(self.source, prompt)
        other, other_snapshot = prepare_revision(self.source, prompt)
        self.assertNotEqual(wish.product_id, other.product_id)
        self.assertEqual(snapshot, other_snapshot)
        self.assertEqual(wish.objective, prompt)
        self.assertEqual(wish.context["inventor_id"], "mara-masque")
        self.assertEqual(wish.context["revision"]["snapshot_sha256"], hashlib.sha256(snapshot).hexdigest())
        workspace = self.root / "workspace"
        workspace.mkdir()
        materialize_revision(workspace, snapshot)
        clone = workspace / "revision-work/make/source/toy.step.py"
        clone.write_text("# correction")
        self.assertEqual((self.source / "make/source/toy.step.py").read_bytes(), b"# original CAD\n")
        self.assertFalse((workspace / "agent-run.json").exists())
        self.assertFalse((workspace / "release-effect.json").exists())

    def test_refuses_drift_extra_files_links_and_unpublished(self):
        for mutation in ("drift", "extra", "link", "draft"):
            with self.subTest(mutation=mutation):
                self.setUp()
                if mutation == "drift":
                    self.write("make/source/toy.step.py", b"changed")
                elif mutation == "extra":
                    self.write("private-token", b"not sealed")
                elif mutation == "link":
                    (self.source / "link").symlink_to(self.root)
                else:
                    self.publication["publication"]["status"] = "draft"
                    self.seal()
                with self.assertRaises((ContractError, StateConflict)):
                    prepare_revision(self.source, "Fix")

    def test_refuses_controls_even_if_manifest_bound(self):
        self.write("make/source/AGENTS.md", b"override")
        self.seal()
        with self.assertRaises(ContractError):
            prepare_revision(self.source, "Fix")

    def test_refuses_zip_traversal_before_writing(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("../escape", "bad")
        with self.assertRaises(ContractError):
            materialize_revision(self.root, buffer.getvalue())
        self.assertFalse((self.root / "revision-work").exists())

    def test_input_binding_missing_changed_and_undeclared(self):
        self.assertEqual(revision_input(b'{"context":{"revision":"legacy note"}}', None), [])
        wish, snapshot = prepare_revision(self.source, "Fix")
        document = json.dumps(wish.to_dict()).encode()
        for content in (None, snapshot + b"changed"):
            with self.assertRaises(ContractError):
                revision_input(document, content)
        with self.assertRaises(ContractError):
            revision_input(b'{"context":{}}', snapshot)

    def test_native_host_launches_new_spark_with_clone_and_fresh_authority(self):
        from workshop.workflow.native_run import start_native_run
        wish, snapshot = prepare_revision(self.source, "Fix the CAD")
        def session(run, paths, **kwargs):
            checkpoint = run.snapshot()
            self.assertEqual(checkpoint.product_id, wish.product_id)
            self.assertEqual(checkpoint.stage, "make")
            self.assertEqual(checkpoint.round_index, 1)
            self.assertTrue((paths.workspace / "revision-work/make/source/toy.step.py").is_file())
            self.assertIn(REVISION_INPUT, checkpoint.input_sha256s)
            self.assertFalse((paths.host_state / "release-effect.json").exists())
            return checkpoint, None, 0, "test-stopped"
        with patch.dict(os.environ, {"WORKSHOP_HOME": str(self.root / "home")}), patch(
            "workshop.workflow.native_run._run_native_session", side_effect=session
        ) as launch, patch("workshop.workflow.native_run._native_receipt", return_value={"status": "waiting"}):
            receipt = start_native_run(wish, effort="spark", revision_snapshot=snapshot)
        launch.assert_called_once()
        self.assertEqual(receipt["wish"]["objective"], "Fix the CAD")

    def test_checkpoint_reopens_baseline_and_allows_clone_edits(self):
        wish, snapshot = prepare_revision(self.source, "Fix")
        constitution = self.root / ".agents/product-run/AGENTS.md"
        constitution.parent.mkdir(parents=True)
        constitution.write_text("Product instructions")
        skills = self.root / "skills"
        skills.mkdir()
        (skills / "SKILL.md").write_text("Workflow instructions")
        run = AgentRun.create(
            self.root / "run", self.root / "state", product_id=wish.product_id,
            wish_bytes=json.dumps(wish.to_dict(), sort_keys=True, separators=(",", ":")).encode(),
            product_run_constitution_source=constitution, skill_root=skills,
            revision_snapshot=snapshot,
        )
        (run.run_root / "revision-work/make/source/toy.step.py").write_text("fixed")
        reopened = AgentRun.open(run.run_root, host_state_root=run.host_state_root)
        self.assertIn(REVISION_INPUT, reopened.snapshot().input_sha256s)
        baseline = run.run_root / REVISION_INPUT
        baseline.chmod(0o600)
        baseline.write_bytes(snapshot + b"changed")
        baseline.chmod(0o400)
        with self.assertRaises(StateConflict):
            reopened.snapshot()


if __name__ == "__main__":
    unittest.main()
