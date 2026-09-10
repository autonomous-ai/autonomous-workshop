import dataclasses
import hashlib
import io
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
    NATIVE_CAD_GATE_NOZZLE_MM,
    NATIVE_CAD_NON_PRINT_READY_TIER,
    NATIVE_CAD_PRINT_GATES_VERIFIER_MODE,
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
            "status": "digitally-verified-not-print-ready",
        }
        product_bytes = (
            json.dumps(product, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        (product_root / "product.json").write_bytes(product_bytes)
        (product_root / "assembled.step").write_bytes(b"ISO-10303-21;\n")
        (product_root / "assembled.step.json").write_text(
            '{"assembly":"Moon Nook","parts":1}\n'
        )
        (project / "moon.step.py").write_text("def build():\n    return None\n")
        (project / "moon.step").write_bytes(b"ISO-10303-21;\n")
        (project / "measure/verification-pipeline.md").write_text("old timing\n")
        (project / "measure/design-review.md").write_text("stable review\n")
        (project / "measure/fit-report.json").write_text('{"ok":true}\n')
        verification = (
            b'{"final_pipeline":{"print_ready_claim":false},"ok":true,'
            b'"validator":"cad-final"}\n'
        )
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

    def _rebuild_made_manifest(self):
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
            product=previous.product,
            product_json_sha256=previous.product_json_sha256,
            cad_verification_path=previous.cad_verification_path,
            cad_verification_sha256=previous.cad_verification_sha256,
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

    def test_missing_required_root_delivery_file_fails_before_verifier(self):
        invoked = False

        def runner(*_args, **_kwargs):
            nonlocal invoked
            invoked = True
            raise AssertionError("verifier must not run")

        (self.product_root / "assembled.step.json").unlink()
        self._rebuild_made_manifest()

        with self.assertRaisesRegex(
            NativeMadeTreeGateError,
            "lacks required root delivery files: assembled.step.json",
        ):
            self._verify(runner)
        self.assertFalse(invoked)

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
                    "measure/verification-pipeline.md",
                    "moon.step",
                    "moon.step.py",
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
            observed["command"][3:], ("--fresh", "--strict-fit")
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

    def test_the_lower_tier_runs_without_the_print_gates(self):
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
            ("--fresh", "--strict-fit"),
        )
        self.assertEqual(evidence.verifier_mode, NATIVE_CAD_VERIFIER_MODE)
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

    def test_the_full_tier_runs_the_print_gates_at_a_named_nozzle(self):
        self._rewrite_claim_declarations(
            product_status=NATIVE_CAD_FULL_TIER,
            print_ready_claim=True,
        )
        observed = {}

        def runner(command, **arguments):
            observed["command"] = tuple(command)
            return VerifierProcessResult.from_bytes(0)

        evidence = self._verify(runner)

        # A wall that passes at 0.4 mm can fail at 0.6, so the nozzle the claim
        # was made at is in the command and therefore in the receipt.
        self.assertEqual(
            observed["command"][3:],
            ("--fresh", "--strict-fit", "--print-gates", "--nozzle", NATIVE_CAD_GATE_NOZZLE_MM),
        )
        # Skipping the wall gate forfeits the claim upstream, so the tier that
        # carries the claim can never ask for it.
        self.assertNotIn("--skip-thickness", observed["command"])
        self.assertEqual(
            evidence.verifier_mode, NATIVE_CAD_PRINT_GATES_VERIFIER_MODE
        )
        self.assertEqual(evidence.verification_tier, NATIVE_CAD_FULL_TIER)
        self.assertTrue(evidence.thickness_gate_required)
        self.assertTrue(evidence.print_ready_eligible)
        self.assertEqual(
            evidence.to_dict()["verification_tier"], "full-with-thickness"
        )

    def test_print_ready_requirement_accepts_the_full_tier(self):
        self._rewrite_claim_declarations(
            product_status=NATIVE_CAD_FULL_TIER,
            print_ready_claim=True,
        )
        evidence = self._verify(
            lambda *args, **kwargs: VerifierProcessResult.from_bytes(0),
            evidence_stage="release",
            require_print_ready=True,
        )
        self.assertTrue(evidence.passed)
        self.assertIsNone(evidence.failure_code)
        self.assertTrue(evidence.print_ready_eligible)

    def test_a_full_tier_status_without_its_claim_is_refused(self):
        self._rewrite_claim_declarations(
            product_status=NATIVE_CAD_FULL_TIER,
            print_ready_claim=False,
        )
        called = False

        def runner(command, **arguments):
            nonlocal called
            del command, arguments
            called = True
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaisesRegex(ContractError, "must name the same tier"):
            self._verify(runner)
        self.assertFalse(called)

    def test_a_failing_print_gate_run_cannot_carry_its_claim(self):
        self._rewrite_claim_declarations(
            product_status=NATIVE_CAD_FULL_TIER,
            print_ready_claim=True,
        )
        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(
                lambda *args, **kwargs: VerifierProcessResult.from_bytes(
                    1, b"", b"wall below minimum", maximum_bytes=64
                ),
                require_print_ready=True,
            )
        # The claim is declared, but the host's own rerun is what carries it.
        self.assertEqual(caught.exception.failure_code, "verifier-nonzero")
        self.assertEqual(
            caught.exception.evidence.verification_tier, NATIVE_CAD_FULL_TIER
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
            ContractError, "must name the same tier"
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
            ContractError, "must name the same tier"
        ):
            self._verify(runner)
        self.assertFalse(called)

    def test_only_a_literal_false_receipt_claim_is_accepted(self):
        self._rewrite_claim_declarations(
            product_status=NATIVE_CAD_NON_PRINT_READY_TIER,
            print_ready_claim="false",
        )
        with self.assertRaisesRegex(ContractError, "must name the same tier"):
            self._verify(
                lambda *args, **kwargs: VerifierProcessResult.from_bytes(0)
            )

    def test_a_print_ready_claim_without_its_status_is_refused(self):
        self._rewrite_claim_declarations(print_ready_claim=True)
        called = False

        def runner(command, **arguments):
            nonlocal called
            del command, arguments
            called = True
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaisesRegex(ContractError, "must name the same tier"):
            self._verify(runner)
        self.assertFalse(called)

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

    _MINI_STEP = (
        "ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('Open CASCADE Model'),'2;1');\n"
        "FILE_NAME('moon','1970-01-01T00:00:00',('Author'),('Open CASCADE'),"
        "'Open CASCADE STEP processor 7.9','cadgen','Unknown');\n"
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\nENDSEC;\n"
        "DATA;\n"
        "#1 = CARTESIAN_POINT('',(0.,0.,0.));\n"
        "#2 = CARTESIAN_POINT('',(1.,0.,0.));\n"
        "#3 = VERTEX_POINT('',#1);\n"
        "#4 = VERTEX_POINT('',#2);\n"
        "#5 = COLOUR_RGB('',0.12,0.19,0.24);\n"
        "#6 = COLOUR_RGB('',0.45,0.55,0.60);\n"
        "#7 = STYLED_ITEM('color',(#5),#3);\n"
        "#8 = STYLED_ITEM('color',(#6),#4);\n"
        "#9 = MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',(\n"
        "    #7,#8),#1);\n"
        "ENDSEC;\nEND-ISO-10303-21;\n"
    )
    # The same model as Open CASCADE re-emits it on another run: style ids
    # handed out in a different pointer order, colours travelling along.
    _MINI_STEP_REEMITTED = _MINI_STEP.replace(
        "#7 = STYLED_ITEM('color',(#5),#3);\n#8 = STYLED_ITEM('color',(#6),#4);",
        "#7 = STYLED_ITEM('color',(#6),#4);\n#8 = STYLED_ITEM('color',(#5),#3);",
    ).replace("    #7,#8),#1);", "    #8,#7),#1);")

    def _seal_mini_step(self):
        sealed = self._MINI_STEP.encode()
        (self.product_root / "cad/project/moon.step").write_bytes(sealed)
        manifest = build_artifact_manifest(
            self.product_root, created_at="content-addressed"
        )
        self.made = dataclasses.replace(self.made, product_manifest=manifest)
        return sealed

    def test_step_reemitted_with_other_entity_numbering_still_passes(self):
        sealed = self._seal_mini_step()
        self.assertNotEqual(self._MINI_STEP_REEMITTED, self._MINI_STEP)

        def runner(command, **arguments):
            del arguments
            Path(command[2], "moon.step").write_text(self._MINI_STEP_REEMITTED)
            return VerifierProcessResult.from_bytes(0)

        evidence = self._verify(runner)

        self.assertTrue(evidence.passed)
        self.assertTrue(evidence.source_tree_unchanged)
        self.assertEqual(
            (self.product_root / "cad/project/moon.step").read_bytes(), sealed
        )

    def test_step_whose_geometry_or_colour_changed_still_fails_closed(self):
        self._seal_mini_step()
        for label, old, new in (
            ("coordinate", "(1.,0.,0.)", "(1.001,0.,0.)"),
            ("colour", "0.45,0.55,0.60", "0.45,0.55,0.61"),
            ("wiring", "#7 = STYLED_ITEM('color',(#5),#3);", "#7 = STYLED_ITEM('color',(#5),#4);"),
            ("garbage", "DATA;", "DATA"),
        ):
            with self.subTest(label=label):
                changed = self._MINI_STEP.replace(old, new, 1)
                self.assertNotEqual(changed, self._MINI_STEP)

                def runner(command, **arguments):
                    del arguments
                    Path(command[2], "moon.step").write_text(changed)
                    return VerifierProcessResult.from_bytes(0)

                with self.assertRaises(NativeCadGateError) as caught:
                    self._verify(runner)

                self.assertEqual(
                    caught.exception.failure_code, "declared-cad-output-changed"
                )

    def test_step_mode_change_is_not_forgiven_by_graph_comparison(self):
        self._seal_mini_step()

        def runner(command, **arguments):
            del arguments
            Path(command[2], "moon.step").chmod(0o700)
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(runner)

        self.assertEqual(caught.exception.failure_code, "declared-cad-output-changed")

    def test_frozen_verifier_may_refresh_only_known_volatile_reports(self):
        observed = {}

        def runner(command, **arguments):
            observed["command"] = tuple(command)
            copied = Path(command[2])
            (copied / "measure/verification-pipeline.md").write_text(
                "different path and wall-clock timing\n"
            )
            return VerifierProcessResult.from_bytes(0)

        evidence = self._verify(runner)

        self.assertTrue(evidence.passed)
        self.assertEqual(
            observed["command"][3:], ("--fresh", "--strict-fit")
        )
        self.assertEqual(
            (
                self.product_root
                / "cad/project/measure/verification-pipeline.md"
            ).read_text(),
            "old timing\n",
        )

    @staticmethod
    def _print_gate_report(gate, prefix):
        title, option, value, head, rows = {
            "overhang": (
                "Overhang and support", "--angle", "45.0",
                "65.5 cm2 of surface, grid 0.400 mm, 0 unsupported samples",
                "| overhang | PASS | 0 regions need support |\n",
            ),
            "thickness": (
                "Thickness and hollow", "--nozzle", "0.4",
                "12.25 cm3 solid, grid 0.100 mm, 4096 surface samples",
                "| wall >= 0.80 mm | PASS | 0.0% of surface below |\n",
            ),
        }[gate]
        return (
            f"# {title}\n\n"
            f"`{prefix}part_moon.step.py {option} {value} "
            f"--report {prefix}measure/{gate}-moon.md`\n\n"
            f"part_moon.step.py: {head}\n\n"
            "| check | status | detail |\n|---|---|---|\n" + rows
        )

    def _seal_print_gate_report(self, gate):
        path = self.product_root / ("cad/project/measure/%s-moon.md" % gate)
        path.write_text(
            self._print_gate_report(gate, "artifacts/make/r0001/product/cad/project/")
        )
        self._rebuild_made_manifest()
        return path

    def test_print_gate_report_relocation_preserves_every_measurement(self):
        for gate in ("overhang", "thickness"):
            with self.subTest(gate=gate):
                sealed = self._seal_print_gate_report(gate)
                before = sealed.read_bytes()

                def runner(command, **arguments):
                    Path(command[2], "measure/%s-moon.md" % gate).write_text(
                        self._print_gate_report(gate, "project/")
                    )
                    return VerifierProcessResult.from_bytes(0)

                self.assertTrue(self._verify(runner).passed)
                self.assertEqual(sealed.read_bytes(), before)

    def test_print_gate_report_content_changes_fail_closed(self):
        for gate, changes in (
            ("overhang", (
                ("65.5", "65.6"), ("PASS", "FAIL"), ("45.0", "30.0"),
                ("0 regions", "1 regions"), ("part_moon", "part_other"),
                ("# Overhang and support", "# Custom report"),
            )),
            ("thickness", (
                ("12.25", "12.26"), ("PASS", "FAIL"), ("--nozzle 0.4", "--nozzle 0.2"),
                ("0.0% of surface", "3.0% of surface"),
                ("# Thickness and hollow", "# Custom report"),
            )),
        ):
            self._seal_print_gate_report(gate)
            for old, new in changes:
                with self.subTest(gate=gate, old=old):
                    def runner(command, **arguments):
                        Path(command[2], "measure/%s-moon.md" % gate).write_text(
                            self._print_gate_report(gate, "project/").replace(old, new)
                        )
                        return VerifierProcessResult.from_bytes(0)
                    with self.assertRaises(NativeCadGateError) as caught:
                        self._verify(runner)
                    self.assertEqual(
                        caught.exception.failure_code, "declared-cad-output-changed"
                    )

    def test_a_print_gate_report_cannot_be_repointed_at_another_part(self):
        # The entry basename must match the role the report is named for, so a
        # passing report cannot be made to stand for a different part.
        self._seal_print_gate_report("thickness")

        def runner(command, **arguments):
            Path(command[2], "measure/thickness-moon.md").write_text(
                self._print_gate_report("thickness", "project/").replace(
                    "part_moon.step.py --nozzle", "part_hull.step.py --nozzle"
                )
            )
            return VerifierProcessResult.from_bytes(0)

        with self.assertRaises(NativeCadGateError) as caught:
            self._verify(runner)
        self.assertEqual(
            caught.exception.failure_code, "declared-cad-output-changed"
        )

    def test_print_gate_report_mode_and_symlink_changes_fail_closed(self):
        self._seal_print_gate_report("overhang")
        for link in (False, True):
            with self.subTest(link=link):
                def runner(command, **arguments):
                    path = Path(command[2], "measure/overhang-moon.md")
                    if link:
                        path.unlink()
                        path.symlink_to(Path(command[2], "moon.step"))
                    else:
                        path.chmod(0o700)
                    return VerifierProcessResult.from_bytes(0)
                with self.assertRaises(NativeCadGateError):
                    self._verify(runner)

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
            Path(command[2], "measure/verification-pipeline.md").chmod(0o700)
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
        self._assert_default_runner_drains_and_bounds_both_streams()

    def test_untimed_verifier_cancellation_reaps_its_process_group(self):
        process = mock.Mock(pid=12345, stdout=io.BytesIO(b""), stderr=io.BytesIO(b""))
        process.wait.side_effect = [KeyboardInterrupt(), 0]
        with mock.patch("workshop.make.native_gate.subprocess.Popen", return_value=process), mock.patch(
            "workshop.make.native_gate.os.killpg"
        ) as killpg, self.assertRaises(KeyboardInterrupt):
            run_bounded_verifier(["verifier"], cwd=self.run_root, environment={},
                                 timeout_seconds=None, max_output_bytes=32)
        killpg.assert_called_once()
        self.assertEqual(process.wait.call_count, 2)
        self.assertTrue(process.stdout.closed)
        self.assertTrue(process.stderr.closed)

    def _assert_default_runner_drains_and_bounds_both_streams(self):
        result = run_bounded_verifier(
            (
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(b'a'*80); sys.stderr.buffer.write(b'b'*70)",
            ),
            cwd=self.run_root,
            environment={"PYTHONDONTWRITEBYTECODE": "1"},
            timeout_seconds=None,
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
            "schema_version": 7,
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
        self.assertIn("one to four review rounds", completed.stderr)
        self.assertNotIn("check_layout", completed.stdout)

    def test_signature_review_allows_three_repairs_but_not_a_fourth(self):
        import runpy

        self._write_signature_review(review_rounds=4)
        validate = runpy.run_path(str(self.verifier))["_required_signature_review"]
        review_path = self.project / "snap/SIGNATURE-REVIEW.json"
        self.assertEqual(validate(self.project), _sha(review_path.read_bytes()))
        review = json.loads(review_path.read_text())
        review["review_rounds"] = 5
        review_path.write_text(json.dumps(review, sort_keys=True, separators=(",", ":")))
        with self.assertRaisesRegex(ValueError, "one to four"):
            validate(self.project)

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

    def test_the_only_plan_retains_every_surviving_deterministic_gate(self):
        output = self._plan()

        for required in (
            "check_layout",
            "gen",
            "check_fit",
            "check_spec.py",
            "check_landmarks.py",
            "check_mount",
            "check_motion",
            "inspect batch",
        ):
            with self.subTest(required=required):
                self.assertIn(required, output)
        for retired in ("check_thickness", "check_mesh", "check_overhang", "export"):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, output)

