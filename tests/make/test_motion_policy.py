"""Opt-in motion keeps expensive work absent by default and strict when enabled."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


class MotionPolicyTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def materialize(self, value):
        (self.root / ".workshop-product-run-root").write_text("fixture product run")
        scripts = self.root / ".agents/skills/cad/scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SCRIPTS / "motion_policy.py", scripts / "motion_policy.py")
        if value is not None:
            (self.root / "MAKE-OPTIONS.json").write_text(json.dumps(value))
        return runpy.run_path(str(scripts / "motion_policy.py"))["enabled"]

    def test_standalone_defaults_off_and_accepts_explicit_boolean(self):
        enabled = runpy.run_path(str(SCRIPTS / "motion_policy.py"))["enabled"]
        self.assertFalse(enabled())
        self.assertFalse(enabled(False))
        self.assertTrue(enabled(True))

    def test_materialized_option_is_independent_of_working_directory(self):
        for choice in (False, True):
            enabled = self.materialize({"schema_version": 1, "check_motion": choice})
            with contextlib.chdir(self.root.parent):
                self.assertIs(enabled(), choice)
                self.assertIs(enabled(choice), choice)
                with self.assertRaisesRegex(ValueError, "conflicts with frozen"):
                    enabled(not choice)

    def test_refreshed_legacy_run_without_options_keeps_motion_enabled(self):
        self.assertTrue(self.materialize(None)())

    def test_project_scoped_skill_outside_workshop_defaults_off(self):
        enabled = self.materialize(None)
        (self.root / ".workshop-product-run-root").unlink()
        self.assertFalse(enabled())
        self.assertTrue(enabled(True))

    def test_malformed_or_linked_policy_never_silently_disables_checks(self):
        for payload in ({}, {"schema_version": 1, "check_motion": "false"},
                        {"schema_version": True, "check_motion": False}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.materialize(payload)()
        enabled = self.materialize({"schema_version": 1, "check_motion": False})
        path = self.root / "MAKE-OPTIONS.json"
        path.rename(self.root / "other.json")
        path.symlink_to(self.root / "other.json")
        with self.assertRaises(ValueError):
            enabled()


class VerifyMotionOptionTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.tool = runpy.run_path(str(SCRIPTS / "verify_project"))
        self.project = self.tool["_sc_project"](self.root)
        (self.project / "README.md").write_text("## Assembly\nInsert the pin into the body.\n")

    def invoke(self, *options, dry=True):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.chdir(self.root), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                result = self.tool["main"]([str(self.project), *(["--dry-run"] if dry else []), *options])
            except SystemExit as exc:
                result = exc.code
        return result, out.getvalue(), err.getvalue()

    def test_default_skips_despite_assembly_claim_and_existing_bad_manifest(self):
        for has_manifest in (False, True):
            if has_manifest:
                (self.project / "measure/motion.json").write_text("invalid JSON")
            with self.subTest(has_manifest=has_manifest):
                code, out, err = self.invoke()
                self.assertEqual(code, 0, err)
                self.assertIn("motion is unverified", out)
                self.assertNotIn("scripts/check_motion", out)

    def test_enabled_requires_manifest_before_expensive_work(self):
        code, out, err = self.invoke("--check-motion", "true")
        self.assertEqual(code, 2)
        self.assertIn("no motion manifest exists", err)
        self.assertNotIn("check_layout", out)

    def test_enabled_plan_executes_motion_gate(self):
        (self.project / "measure/motion.json").write_text('{"conditions":[]}')
        code, out, err = self.invoke("--check-motion", "true")
        self.assertEqual(code, 0, err)
        self.assertIn("scripts/check_motion", out)

    def test_default_never_loads_animation_validator(self):
        (self.project / "measure/motion.json").write_text("invalid JSON")
        calls = []
        original = runpy.run_path

        def load(path, *args, **kwargs):
            calls.append(Path(path).name)
            return original(path, *args, **kwargs)

        # Stop before geometry; a real invocation must pass review then reach
        # the runner without loading/reconstructing motion evidence.
        namespace = self.tool["main"].__globals__
        with patch.dict(namespace, {"_required_signature_review": lambda _: "a" * 64,
                                    "_run_or_stop": lambda *a, **kw: False}), \
                patch.object(runpy, "run_path", load):
            self.invoke(dry=False)
        self.assertNotIn("motion_presentation.py", calls)

    def test_enabled_requires_animation_evidence_for_coupled_motion(self):
        (self.project / "measure/motion.json").write_text(
            '{"conditions":[{"check":"coupled_motion_collision"}]}')
        code, out, err = self.invoke("--check-motion", "true", dry=False)
        self.assertEqual(code, 2)
        self.assertIn("MOTION-EVIDENCE.json", err)
        self.assertNotIn("check_layout", out)

    def test_enabled_motion_failure_stops_the_final_pipeline(self):
        manifest = self.project / "measure/motion.json"
        manifest.write_text('{"conditions":[]}')
        calls = []

        def run_gate(runner, command, **kwargs):
            calls.append(Path(command[1]).name)
            return Path(command[1]).name != "check_motion"

        namespace = self.tool["_final"].__globals__
        with patch.dict(namespace, {"_run_or_stop": run_gate,
                                    "_run_preflight_audits": lambda *a, **kw: 0}):
            runner = self.tool["Runner"](cwd=self.root, dry_run=False, verbose=False)
            result = self.tool["_final"](
                runner, self.project, self.project / "widget.step.py", [], [],
                motion_manifest=manifest, check_motion=True,
                strict_fit=False, strict_mount=False, print_gates=False,
                bed=(220, 220, 220), nozzle=0.4, skip_thickness=False,
                overhang_angle=45, image_derived=False, likeness_refs=[],
                likeness_min=0.9, likeness_accept_mismatch=None,
                likeness_mismatch_labels=set(), likeness_accept_regression=None,
                search_fov="20,40,60",
            )
        self.assertEqual(result, 1)
        self.assertEqual(calls, ["gen", "check_motion"])
