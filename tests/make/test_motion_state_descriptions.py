"""Read-only caption data must remain bound to exact declared artifact bytes."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import hashlib
import io
import json
import runpy
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


class StateDescriptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.check = runpy.run_path(str(TOOLS / "check_motion"))
        cls.states = runpy.run_path(str(TOOLS / "motion_states.py"))
        cls.presentation = runpy.run_path(str(TOOLS / "motion_presentation.py"))

    @contextmanager
    def metadata_only(self, state_tool=None):
        fake_cad = types.SimpleNamespace(Axis=lambda *args: args, Vector=lambda *args: args)
        with mock.patch.dict(sys.modules, {"build123d": fake_cad}), mock.patch.dict(
            self.states["sample_annotations"].__globals__, {"helpers": lambda: (self.check, None)}
        ), mock.patch.dict(self.presentation["describe_states"].__globals__, {
            "state_tool": lambda: self.states if state_tool is None else state_tool
        }):
            yield

    def fixture(self, root):
        (root / "measure").mkdir()
        (root / "snap").mkdir()
        (root / "model.step.py").write_text("raise AssertionError('caption command must not execute CAD source')\n")
        manifest = {"conditions": [{"id": "cycle", "check": "coupled_motion_collision", "inputs": {
            "steps": 72, "movers": [{"part": "rotor", "rotation": {
                "axis_point": [0, 0, 0], "axis_direction": [0, 1, 0], "end_deg": 360}}]}}]}
        (root / "measure/motion.json").write_text(json.dumps(manifest))
        rows = []
        for ordinal, sample in enumerate((0, 10, 19, 30, 38, 50, 58, 72)):
            # Opaque fixture hashes are intentional: states never reach disk,
            # and this command describes bound declarations rather than
            # certifying CAD poses.
            rows.append({"condition_id": "cycle", "sample_index": sample,
                         "sha256": hashlib.sha256(b"opaque state %d" % ordinal).hexdigest()})
        evidence = {"schema_version": 2, "kind": "declared-cad-motion-animation",
                    "sources": self.presentation["sources"](root), "assembly_entry": "model.step.py",
                    "states": rows, "render": {"azimuth": -45, "elevation": 35, "size": 256},
                    "animation_sha256": "a" * 64,
                    "motion_sha256": self.presentation["digest"](root, "measure/motion.json")}
        (root / "snap/MOTION-EVIDENCE.json").write_bytes(self.presentation["canonical"](evidence))
        return evidence

    def files(self, root):
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def test_descriptions_keep_identities_and_exact_samples_without_geometry_claims(self):
        with tempfile.TemporaryDirectory() as temporary, self.metadata_only():
            root = Path(temporary)
            evidence = self.fixture(root)
            before = self.files(root)
            described = self.presentation["describe_states"](root)
            self.assertEqual(described["kind"], "declared-motion-sample-annotations")
            self.assertFalse(described["geometry_reconciled_by_this_command"])
            self.assertEqual(described["evidence_sha256"], hashlib.sha256(before["snap/MOTION-EVIDENCE.json"]).hexdigest())
            self.assertEqual(
                [(r["condition_id"], r["sample_index"], r["sha256"]) for r in described["states"]],
                [(r["condition_id"], r["sample_index"], r["sha256"]) for r in evidence["states"]],
            )
            self.assertEqual([r["movers"][0]["rotation_deg"] for r in described["states"]], [0, 50, 95, 150, 190, 250, 290, 360])
            self.assertEqual(self.files(root), before)

    def test_stale_source_and_manifest_bytes_are_rejected(self):
        for path in ("model.step.py", "measure/motion.json"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temporary, self.metadata_only():
                root = Path(temporary)
                self.fixture(root)
                with (root / path).open("ab") as handle:
                    handle.write(b"changed")
                with self.assertRaisesRegex(ValueError, "stale"):
                    self.presentation["describe_states"](root)

    def test_changes_during_description_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            def annotations(manifest, identities):
                rows = self.states["sample_annotations"](manifest, identities)
                with (root / "model.step.py").open("a") as handle:
                    handle.write("# concurrent change\n")
                return rows
            with self.metadata_only({"sample_annotations": annotations}), self.assertRaisesRegex(ValueError, "stale"):
                self.presentation["describe_states"](root)

    def test_final_validation_still_requires_review_before_reconstruction(self):
        for mode in ("missing", "stale", "unapproved"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                evidence = self.fixture(root)
                (root / "snap/motion.gif").write_bytes(b"opaque animation fixture")
                evidence["animation_sha256"] = self.presentation["digest"](root, "snap/motion.gif")
                raw = self.presentation["canonical"](evidence)
                (root / "snap/MOTION-EVIDENCE.json").write_bytes(raw)
                signature = {"concept_sha256": "b" * 64, "reviewer": "test critic", "review_rounds": 1}
                review = {"schema_version": 1, **signature, "evidence_sha256": hashlib.sha256(raw).hexdigest(),
                          "blind_motion_read": "Synthetic fixture only", "motion_matches_wish": True,
                          "simulation_not_physical_test": True}
                if mode == "stale":
                    review["evidence_sha256"] = "c" * 64
                if mode == "unapproved":
                    review["motion_matches_wish"] = False
                if mode != "missing":
                    (root / "snap/MOTION-REVIEW.json").write_bytes(self.presentation["canonical"](review))
                reconstruction = mock.Mock(side_effect=AssertionError("CAD must not start before review"))
                # Animation format is isolated; the real review and state/source
                # binding guards must still refuse before CAD reconstruction.
                with mock.patch.dict(self.presentation["validate"].__globals__, {
                    "_check_animation": lambda raw: None, "state_tool": reconstruction
                }), self.assertRaises(FileNotFoundError if mode == "missing" else ValueError):
                    self.presentation["validate"](root, signature)
                reconstruction.assert_not_called()

    def test_cli_returns_json_without_writing_or_claiming_generated_evidence(self):
        with tempfile.TemporaryDirectory() as temporary, self.metadata_only():
            root = Path(temporary)
            self.fixture(root)
            before = self.files(root)
            output = io.StringIO()
            with mock.patch.object(sys, "argv", ["motion_presentation.py", str(root), "--describe-states"]), redirect_stdout(output):
                self.presentation["main"]()
            result = json.loads(output.getvalue())
            self.assertEqual(len(result["states"]), 8)
            self.assertEqual(self.files(root), before)

    def test_cli_rejects_generation_options_in_description_mode(self):
        with mock.patch.object(sys, "argv", ["motion_presentation.py", "unused", "--describe-states", "--frames", "16"]), redirect_stderr(io.StringIO()) as error:
            with self.assertRaises(SystemExit) as raised:
                self.presentation["main"]()
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("generation options do not apply", error.getvalue())


if __name__ == "__main__":
    unittest.main()
