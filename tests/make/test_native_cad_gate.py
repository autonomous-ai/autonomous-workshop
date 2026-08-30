import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ArtifactError, ContractError
from workshop.make.native import NativeMade
from workshop.make.native_gate import (
    DEFAULT_NATIVE_CAD_OUTPUT_BYTES,
    NATIVE_CAD_FULL_TIER,
    NATIVE_CAD_NON_PRINT_READY_TIER,
    NATIVE_CAD_NON_PRINT_READY_VERIFIER_MODE,
    NATIVE_CAD_VERIFIER_MODE,
    NATIVE_CAD_VERIFIER_PATH,
    NativeCadGateError,
    NativeMadeTreeGateError,
    VerifierProcessResult,
    run_bounded_verifier,
    verify_native_made_cad,
)


_MISSING = object()


def _sha(value):
    return hashlib.sha256(value).hexdigest()


class NativeCadGateTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name).resolve()
        self.run_root = base / "run"
        self.host_state_root = base / "host-state"
        self.run_root.mkdir(mode=0o700)
        self.host_state_root.mkdir(mode=0o700)
        os.chmod(self.host_state_root, 0o700)
        self.verifier = self.run_root / NATIVE_CAD_VERIFIER_PATH
        self.verifier.parent.mkdir(parents=True)
        self.verifier_bytes = b"#!/usr/bin/env python3\nraise SystemExit(0)\n"
        self.verifier.write_bytes(self.verifier_bytes)
        self.verifier.chmod(0o500)
        self.made, self.product_root = self._make_native_made()

    def _make_native_made(self):
        product_root = self.run_root / "artifacts/make/r0001/product"
        project = product_root / "cad/project"
        validation = product_root / "validation"
        project.mkdir(parents=True)
        (project / "measure").mkdir()
        validation.mkdir()
        product = {
            "title": "Moon Nook",
            "summary": "A tiny lunar observatory.",
            "components": ["observatory"],
            "instructions": "Explore the craters.",
            "limitations": ["Digital checks only"],
        }
        product_bytes = (
            json.dumps(product, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        (product_root / "product.json").write_bytes(product_bytes)
        (project / "moon.step.py").write_text("def build():\n    return None\n")
        (project / "moon.step").write_bytes(b"ISO-10303-21;\n")
        (project / "moon.stl").write_bytes(b"solid moon\nendsolid moon\n")
        (project / "measure/thickness-moon.md").write_text("old thickness\n")
        (project / "measure/verification-pipeline.md").write_text("old timing\n")
        (project / "measure/design-review.md").write_text("stable review\n")
        (project / "measure/fit-report.json").write_text('{"ok":true}\n')
        verification = b'{"ok":true,"validator":"cad-final"}\n'
        (validation / "cad-build.json").write_bytes(verification)
        manifest = build_artifact_manifest(product_root, created_at="content-addressed")
        return (
            NativeMade(
                round=1,
                wish_sha256="a" * 64,
                assignment_sha256="b" * 64,
                taste_sha256="c" * 64,
                blueprint_sha256="d" * 64,
                invented_sha256="e" * 64,
                product_root="artifacts/make/r0001/product",
                cad_project_path="cad/project",
                product_manifest=manifest,
                product=product,
                product_json_sha256=_sha(product_bytes),
                cad_verification_path="validation/cad-build.json",
                cad_verification_sha256=_sha(verification),
            ),
            product_root,
        )

    @property
    def verifier_sha256(self):
        return _sha(self.verifier_bytes)

    def _rewrite_claim_declarations(
        self,
        *,
        product_status=_MISSING,
        print_ready_claim=_MISSING,
        raw_verification=None,
    ):
        product = json.loads((self.product_root / "product.json").read_text())
        product.pop("status", None)
        if product_status is not _MISSING:
            product["status"] = product_status
        product_bytes = (
            json.dumps(product, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        if raw_verification is None:
            verification = {"ok": True, "validator": "cad-final"}
            if print_ready_claim is not _MISSING:
                verification["final_pipeline"] = {
                    "print_ready_claim": print_ready_claim
                }
            verification_bytes = (
                json.dumps(verification, sort_keys=True, separators=(",", ":"))
                + "\n"
            ).encode("utf-8")
        else:
            verification_bytes = raw_verification
        (self.product_root / "product.json").write_bytes(product_bytes)
        (self.product_root / "validation/cad-build.json").write_bytes(
            verification_bytes
        )
        previous = self.made
        self.made = NativeMade(
            round=previous.round,
            wish_sha256=previous.wish_sha256,
            assignment_sha256=previous.assignment_sha256,
            taste_sha256=previous.taste_sha256,
            blueprint_sha256=previous.blueprint_sha256,
            invented_sha256=previous.invented_sha256,
            product_root=previous.product_root,
            cad_project_path=previous.cad_project_path,
            product_manifest=build_artifact_manifest(
                self.product_root, created_at="content-addressed"
            ),
            product=product,
            product_json_sha256=_sha(product_bytes),
            cad_verification_path=previous.cad_verification_path,
            cad_verification_sha256=_sha(verification_bytes),
        )

    def _verify(self, runner, **overrides):
        arguments = {
            "run_root": self.run_root,
            "host_state_root": self.host_state_root,
            "expected_verifier_sha256": self.verifier_sha256,
            "runner": runner,
            "timeout_seconds": 15,
            "max_output_bytes": 64,
        }
        arguments.update(overrides)
        return verify_native_made_cad(self.made, **arguments)

    def test_success_runs_final_verifier_only_on_declared_isolated_copy(self):
        before = build_artifact_manifest(
            self.product_root, created_at="content-addressed"
        ).to_dict()
        observed = {}

        def runner(command, **arguments):
            observed["command"] = tuple(command)
            observed.update(arguments)
            copied = Path(command[2])
            self.assertNotEqual(copied, self.product_root / "cad/project")
            self.assertEqual(copied.parent, arguments["cwd"])
            self.assertEqual(
                sorted(
                    path.relative_to(copied).as_posix()
                    for path in copied.rglob("*")
                    if path.is_file()
                ),
                [
                    "measure/design-review.md",
                    "measure/fit-report.json",
                    "measure/thickness-moon.md",
                    "measure/verification-pipeline.md",
                    "moon.step",
                    "moon.step.py",
                    "moon.stl",
                ],
            )
            (copied / "__cadgen__").mkdir()
            (copied / "__cadgen__/cache").write_bytes(b"temporary")
            return VerifierProcessResult.from_bytes(
                0,
                b"verification passed\n",
                b"one advisory\n",
                duration_ms=37,
                maximum_bytes=arguments["max_output_bytes"],
            )

        evidence = self._verify(runner)

        self.assertTrue(evidence.passed)
        self.assertEqual(evidence.duration_ms, 37)
        self.assertEqual(evidence.stdout.to_dict()["captured_text"], "verification passed\n")
        self.assertEqual(observed["command"][0], sys.executable)
        self.assertEqual(Path(observed["command"][1]), self.verifier)
        self.assertEqual(
            observed["command"][3:], ("--fresh", "--exports", "--strict-fit")
        )
        self.assertEqual(observed["environment"]["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertNotIn("FACTORY_PASSWORD", observed["environment"])
        self.assertEqual(
            build_artifact_manifest(
                self.product_root, created_at="content-addressed"
            ).to_dict(),
            before,
        )
        self.assertFalse((self.product_root / "cad/project/__cadgen__").exists())
        evidence_path = self.host_state_root / "evidence/make/r0001-cad-gate.json"
        payload = json.loads(evidence_path.read_text())
        self.assertEqual(payload, evidence.to_dict())
        self.assertEqual(stat.S_IMODE(evidence_path.stat().st_mode), 0o600)

    def test_empty_cache_directory_is_ignored_as_non_content_residue(self):
        (self.product_root / "cad/project/__cadgen__/empty-cache").mkdir(
            parents=True
        )

        evidence = self._verify(
            lambda *unused_args, **unused_kwargs: VerifierProcessResult.from_bytes(0)
        )

        self.assertTrue(evidence.passed)
        self.assertTrue(
            (self.product_root / "cad/project/__cadgen__/empty-cache").is_dir()
        )

    def test_default_output_bound_accommodates_a_verbose_multi_part_success(self):
        output = b"verified part\n" * 6_000

        def runner(command, **arguments):
            del command
            self.assertEqual(
                arguments["max_output_bytes"], DEFAULT_NATIVE_CAD_OUTPUT_BYTES
            )
            return VerifierProcessResult.from_bytes(
                0,
                output,
                maximum_bytes=arguments["max_output_bytes"],
            )

        evidence = self._verify(
            runner, max_output_bytes=DEFAULT_NATIVE_CAD_OUTPUT_BYTES
        )

        self.assertTrue(evidence.passed)
        self.assertFalse(evidence.stdout.truncated)
        self.assertEqual(evidence.stdout.total_bytes, len(output))

    def test_playtest_replay_preserves_the_accepted_make_evidence(self):
        runner = lambda *args, **kwargs: VerifierProcessResult.from_bytes(0)
        make_evidence = self._verify(runner)
        make_path = self.host_state_root / "evidence/make/r0001-cad-gate.json"
        accepted_bytes = make_path.read_bytes()

        playtest_evidence = self._verify(runner, evidence_stage="playtest")

        self.assertEqual(make_path.read_bytes(), accepted_bytes)
        self.assertEqual(make_evidence.evidence_stage, "make")
        self.assertEqual(playtest_evidence.evidence_stage, "playtest")
        playtest_path = (
            self.host_state_root / "evidence/playtest/r0001-cad-gate.json"
        )
        self.assertEqual(
            json.loads(playtest_path.read_text()), playtest_evidence.to_dict()
        )

    def test_explicit_non_print_ready_pair_skips_only_thickness(self):
        self._rewrite_claim_declarations(
            product_status=NATIVE_CAD_NON_PRINT_READY_TIER,
            print_ready_claim=False,
        )
        observed = {}

        def runner(command, **arguments):
            observed["command"] = tuple(command)
            return VerifierProcessResult.from_bytes(0)

        evidence = self._verify(runner)

        self.assertEqual(
            observed["command"][3:],
            ("--fresh", "--exports", "--strict-fit", "--skip-thickness"),
        )
        self.assertEqual(
            evidence.verifier_mode, NATIVE_CAD_NON_PRINT_READY_VERIFIER_MODE
        )
        self.assertEqual(
            evidence.verification_tier, NATIVE_CAD_NON_PRINT_READY_TIER
        )
        self.assertFalse(evidence.thickness_gate_required)
        self.assertFalse(evidence.print_ready_eligible)
        self.assertEqual(evidence.schema_version, 3)
        self.assertEqual(
            evidence.to_dict()["verification_tier"],
            "digitally-verified-not-print-ready",
        )

    def test_print_ready_requirement_rejects_a_passing_lower_tier(self):
        self._rewrite_claim_declarations(
            product_status=NATIVE_CAD_NON_PRINT_READY_TIER,
            print_ready_claim=False,
        )

        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(
                lambda *args, **kwargs: VerifierProcessResult.from_bytes(0),
                evidence_stage="playtest",
                require_print_ready=True,
            )

        rejection = caught.exception
        self.assertEqual(rejection.failure_code, "cad-not-print-ready")
        self.assertEqual(
            rejection.evidence.verification_tier,
            NATIVE_CAD_NON_PRINT_READY_TIER,
        )
        self.assertFalse(rejection.evidence.thickness_gate_required)
        self.assertFalse(rejection.evidence.print_ready_eligible)
        self.assertEqual(rejection.evidence.evidence_stage, "playtest")
        self.assertEqual(
            json.loads(rejection.evidence_path.read_text()),
            rejection.evidence.to_dict(),
        )

    def test_status_alone_cannot_weaken_the_cad_gate(self):
        self._rewrite_claim_declarations(
            product_status=NATIVE_CAD_NON_PRINT_READY_TIER
        )
        called = False

        def runner(command, **arguments):
            nonlocal called
            del command, arguments
            called = True
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaisesRegex(
            ContractError, "status and CAD print_ready_claim must agree"
        ):
            self._verify(runner)
        self.assertFalse(called)

    def test_receipt_claim_alone_cannot_hide_a_print_ready_status(self):
        self._rewrite_claim_declarations(
            product_status="print-ready",
            print_ready_claim=False,
        )
        called = False

        def runner(command, **arguments):
            nonlocal called
            del command, arguments
            called = True
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaisesRegex(
            ContractError, "status and CAD print_ready_claim must agree"
        ):
            self._verify(runner)
        self.assertFalse(called)

    def test_accepted_legacy_full_gate_replays_thickness_without_readiness(self):
        self._rewrite_claim_declarations(
            product_status="digitally-verified-pending-physical-playtest",
            print_ready_claim=False,
        )
        accepted = mock.Mock()
        observed = {}

        def runner(command, **arguments):
            del arguments
            observed["command"] = tuple(command)
            return VerifierProcessResult.from_bytes(0)

        evidence = self._verify(
            runner,
            legacy_full_tier_validator=accepted,
            evidence_stage="playtest",
        )

        accepted.assert_called_once_with()
        self.assertEqual(
            observed["command"][3:],
            ("--fresh", "--exports", "--strict-fit"),
        )
        self.assertEqual(evidence.verification_tier, NATIVE_CAD_FULL_TIER)
        self.assertTrue(evidence.thickness_gate_required)
        self.assertTrue(evidence.legacy_full_tier_compatibility)
        self.assertFalse(evidence.print_ready_eligible)
        self.assertEqual(evidence.evidence_stage, "playtest")

    def test_legacy_validator_cannot_waive_an_arbitrary_claim_mismatch(self):
        self._rewrite_claim_declarations(
            product_status="print-ready",
            print_ready_claim=False,
        )
        accepted = mock.Mock()

        with self.assertRaisesRegex(
            ContractError, "status and CAD print_ready_claim must agree"
        ):
            self._verify(
                lambda *args, **kwargs: VerifierProcessResult.from_bytes(0),
                legacy_full_tier_validator=accepted,
                evidence_stage="playtest",
            )

        accepted.assert_not_called()

    def test_only_literal_false_in_strict_receipt_json_can_skip_thickness(self):
        self._rewrite_claim_declarations(
            product_status=NATIVE_CAD_NON_PRINT_READY_TIER,
            print_ready_claim="false",
        )
        with self.assertRaisesRegex(ContractError, "must agree"):
            self._verify(
                lambda *args, **kwargs: VerifierProcessResult.from_bytes(0)
            )

    def test_explicit_true_claim_keeps_the_full_thickness_gate(self):
        self._rewrite_claim_declarations(print_ready_claim=True)
        observed = {}

        def runner(command, **arguments):
            del arguments
            observed["command"] = tuple(command)
            return VerifierProcessResult.from_bytes(0)

        evidence = self._verify(runner)

        self.assertEqual(
            observed["command"][3:], ("--fresh", "--exports", "--strict-fit")
        )
        self.assertEqual(evidence.verifier_mode, NATIVE_CAD_VERIFIER_MODE)
        self.assertEqual(evidence.verification_tier, NATIVE_CAD_FULL_TIER)
        self.assertTrue(evidence.thickness_gate_required)
        self.assertTrue(evidence.print_ready_eligible)

    def test_nonzero_and_bounded_output_write_failed_host_evidence(self):
        def runner(command, **arguments):
            del command
            return VerifierProcessResult.from_bytes(
                7,
                b"x" * 100,
                b"bad geometry",
                duration_ms=8,
                maximum_bytes=arguments["max_output_bytes"],
            )

        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(runner)

        self.assertEqual(caught.exception.failure_code, "verifier-output-limit")
        self.assertFalse(caught.exception.evidence.passed)
        self.assertTrue(caught.exception.evidence.stdout.truncated)
        self.assertEqual(len(caught.exception.evidence.stdout.content), 64)
        self.assertTrue(caught.exception.evidence_path.is_file())

    def test_nonzero_without_truncation_fails_closed(self):
        def runner(command, **arguments):
            del command, arguments
            return VerifierProcessResult.from_bytes(9, stderr=b"failed")

        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(runner)
        self.assertEqual(caught.exception.failure_code, "verifier-nonzero")
        self.assertEqual(caught.exception.evidence.returncode, 9)

    def test_changed_sealed_source_is_detected_after_verifier(self):
        def runner(command, **arguments):
            del command, arguments
            (self.product_root / "cad/project/moon.stl").write_bytes(b"tampered")
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(runner)

        self.assertEqual(caught.exception.failure_code, "sealed-product-changed")
        self.assertFalse(caught.exception.evidence.source_tree_unchanged)

    def test_changed_declared_file_in_isolated_copy_fails_closed(self):
        def runner(command, **arguments):
            del arguments
            Path(command[2], "moon.step").write_bytes(b"different")
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(runner)

        self.assertEqual(caught.exception.failure_code, "declared-cad-output-changed")
        self.assertEqual(
            (self.product_root / "cad/project/moon.step").read_bytes(),
            b"ISO-10303-21;\n",
        )

    def test_frozen_verifier_may_refresh_only_known_volatile_reports(self):
        observed = {}

        def runner(command, **arguments):
            observed["command"] = tuple(command)
            copied = Path(command[2])
            (copied / "measure/thickness-moon.md").write_text(
                "project/moon.stl was checked\n"
            )
            (copied / "measure/verification-pipeline.md").write_text(
                "different path and wall-clock timing\n"
            )
            return VerifierProcessResult.from_bytes(0)

        evidence = self._verify(runner)

        self.assertTrue(evidence.passed)
        self.assertEqual(
            observed["command"][3:], ("--fresh", "--exports", "--strict-fit")
        )
        self.assertEqual(
            (self.product_root / "cad/project/measure/thickness-moon.md").read_text(),
            "old thickness\n",
        )
        self.assertEqual(
            (
                self.product_root
                / "cad/project/measure/verification-pipeline.md"
            ).read_text(),
            "old timing\n",
        )

    def test_arbitrary_report_change_still_fails_closed(self):
        def runner(command, **arguments):
            del arguments
            Path(command[2], "measure/design-review.md").write_text("rewritten\n")
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(runner)

        self.assertEqual(caught.exception.failure_code, "declared-cad-output-changed")

    def test_volatile_report_exemption_does_not_allow_mode_changes(self):
        def runner(command, **arguments):
            del arguments
            Path(command[2], "measure/thickness-moon.md").chmod(0o700)
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(runner)

        self.assertEqual(caught.exception.failure_code, "declared-cad-output-changed")

    def test_json_evidence_change_still_fails_closed(self):
        def runner(command, **arguments):
            del arguments
            Path(command[2], "measure/fit-report.json").write_text('{"ok":false}\n')
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(runner)

        self.assertEqual(caught.exception.failure_code, "declared-cad-output-changed")

    def test_declared_source_change_in_isolated_copy_still_fails_closed(self):
        def runner(command, **arguments):
            del arguments
            Path(command[2], "moon.step.py").write_text("raise RuntimeError\n")
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(runner)

        self.assertEqual(caught.exception.failure_code, "declared-cad-output-changed")

    def test_symlinks_missing_or_untrusted_verifier_fail_before_invocation(self):
        called = False

        def runner(command, **arguments):
            nonlocal called
            del command, arguments
            called = True
            return VerifierProcessResult.from_bytes(0)

        linked = self.product_root / "cad/project/linked"
        linked.symlink_to(self.product_root / "product.json")
        with self.assertRaisesRegex(ArtifactError, "symlink"):
            self._verify(runner)
        self.assertFalse(called)
        linked.unlink()

        self.verifier.unlink()
        with self.assertRaisesRegex(ArtifactError, "unavailable"):
            self._verify(runner)
        self.assertFalse(called)

    def test_verifier_must_match_trusted_materialized_input_hash(self):
        def runner(command, **arguments):
            self.fail("untrusted verifier was invoked")

        with self.assertRaisesRegex(ArtifactError, "trusted input hash"):
            self._verify(runner, expected_verifier_sha256="f" * 64)

    def test_injected_runner_cannot_bypass_output_bound(self):
        def runner(command, **arguments):
            del command, arguments
            return VerifierProcessResult.from_bytes(
                0, b"x" * 65, maximum_bytes=65
            )

        with self.assertRaisesRegex(ArtifactError, "exceeded its output bound"):
            self._verify(runner)

    def test_host_state_must_be_private_and_separate(self):
        os.chmod(self.host_state_root, 0o755)
        with self.assertRaisesRegex(ArtifactError, "permissions must be 0700"):
            self._verify(lambda *args, **kwargs: VerifierProcessResult.from_bytes(0))

        with self.assertRaisesRegex(ArtifactError, "must not overlap"):
            verify_native_made_cad(
                self.made,
                run_root=self.run_root,
                host_state_root=self.run_root,
                expected_verifier_sha256=self.verifier_sha256,
                runner=lambda *args, **kwargs: VerifierProcessResult.from_bytes(0),
            )

    def test_default_runner_drains_and_bounds_both_streams_without_shell(self):
        result = run_bounded_verifier(
            (
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(b'a'*80); sys.stderr.buffer.write(b'b'*70)",
            ),
            cwd=self.run_root,
            environment={"PYTHONDONTWRITEBYTECODE": "1"},
            timeout_seconds=10,
            max_output_bytes=32,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.content, b"a" * 32)
        self.assertEqual(result.stdout.total_bytes, 80)
        self.assertEqual(result.stdout.sha256, _sha(b"a" * 80))
        self.assertTrue(result.stdout.truncated)
        self.assertEqual(result.stderr.content, b"b" * 32)
        self.assertEqual(result.stderr.total_bytes, 70)


class VerifyProjectTierPlanTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.project = self.root / "cad-project"
        measure = self.project / "measure"
        measure.mkdir(parents=True)
        (self.project / "assembly.step.py").write_text("def gen_step(): pass\n")
        (self.project / "part_token.step.py").write_text("def gen_step(): pass\n")
        (measure / "check_fit.py").write_text("raise SystemExit(0)\n")
        (measure / "check_spec.py").write_text("raise SystemExit(0)\n")
        (measure / "check_landmarks.py").write_text("raise SystemExit(0)\n")
        (measure / "mounts.json").write_text("{}\n")
        (measure / "motion.json").write_text("{}\n")
        self.verifier = (
            Path(__file__).resolve().parents[2]
            / "src/workshop/make/skills/cad/scripts/verify_project"
        )

    def _write_signature_review(self, *, review_rounds):
        snap = self.project / "snap"
        snap.mkdir()
        iso = b"exact iso fixture"
        signature = b"exact signature fixture"
        (snap / "iso.png").write_bytes(iso)
        (snap / "signature.png").write_bytes(signature)
        review = {
            "schema_version": 5,
            "kind": "autonomous-workshop.signature-experience-review",
            "concept_sha256": "0" * 64,
            "iso_sha256": _sha(iso),
            "signature_sha256": _sha(signature),
            "reviewer": "fixture critic",
            "blind_held_read": "A compact exact product.",
            "blind_form_read": "A rounded volumetric exact product.",
            "blind_subjects_read": "Two exact subjects.",
            "blind_action_read": "One subject moves.",
            "blind_relationship_read": "The subject moves through the other.",
            "anti_generic_signature_read": "A distinct rounded bridge.",
            "wish_revealed_after_blind_read": True,
            "held_object_unmistakable": True,
            "form_matches_wish": True,
            "subjects_match_wish": True,
            "action_matches_wish": True,
            "relationship_matches_wish": True,
            "anti_generic_signature_visible": True,
            "signature_experience_unmistakable": True,
            "finished_product_desirable": True,
            "review_rounds": review_rounds,
            "critical_form_requirements": [
                {
                    "requirement": "The product must be rounded and volumetric.",
                    "blind_evidence": "The exact views show rounded depth.",
                    "matches": True,
                }
            ],
            "blocking_visual_defects": [],
            "largest_risk": "The relationship could be subtle.",
            "resolution": "The exact relationship is visible.",
        }
        (snap / "SIGNATURE-REVIEW.json").write_text(
            json.dumps(review, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )

    def _plan(self, *extra):
        completed = subprocess.run(
            (
                sys.executable,
                str(self.verifier),
                str(self.project),
                "--fresh",
                "--exports",
                "--strict-fit",
                "--dry-run",
                *extra,
            ),
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed.stdout

    def test_final_plan_refuses_before_geometry_without_signature_review(self):
        completed = subprocess.run(
            (
                sys.executable,
                str(self.verifier),
                str(self.project),
                "--fresh",
                "--exports",
                "--strict-fit",
                "--no-report",
            ),
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("snap/SIGNATURE-REVIEW.json", completed.stderr)
        self.assertNotIn("check_layout", completed.stdout)

    def test_boolean_review_round_cannot_unlock_final_geometry(self):
        self._write_signature_review(review_rounds=True)
        completed = subprocess.run(
            (
                sys.executable,
                str(self.verifier),
                str(self.project),
                "--fresh",
                "--exports",
                "--strict-fit",
                "--no-report",
            ),
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("one or two review rounds", completed.stderr)
        self.assertNotIn("check_layout", completed.stdout)

    def test_blocking_form_defect_cannot_unlock_final_geometry(self):
        self._write_signature_review(review_rounds=1)
        review_path = self.project / "snap/SIGNATURE-REVIEW.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))
        review["blocking_visual_defects"] = [
            "The body is a constant-depth relief instead of the required volume."
        ]
        review_path.write_text(
            json.dumps(review, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        completed = subprocess.run(
            (
                sys.executable,
                str(self.verifier),
                str(self.project),
                "--fresh",
                "--exports",
                "--strict-fit",
                "--no-report",
            ),
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("still has blocking visual defects", completed.stderr)
        self.assertNotIn("check_layout", completed.stdout)

    def test_non_print_ready_plan_retains_every_other_deterministic_gate(self):
        output = self._plan("--skip-thickness")

        for required in (
            "check_layout",
            "gen",
            "check_fit",
            "check_spec.py",
            "check_landmarks.py",
            "check_mount",
            "check_motion",
            "inspect batch",
            "export",
            "check_mesh",
        ):
            with self.subTest(required=required):
                self.assertIn(required, output)
        self.assertNotIn("check_thickness", output)

    def test_full_plan_still_requires_thickness(self):
        self.assertIn("check_thickness", self._plan())


if __name__ == "__main__":
    unittest.main()
