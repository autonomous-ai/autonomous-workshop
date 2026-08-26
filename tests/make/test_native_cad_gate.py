import hashlib
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ArtifactError
from workshop.make.native import NativeMade
from workshop.make.native_gate import (
    NATIVE_CAD_VERIFIER_PATH,
    NativeCadGateError,
    VerifierProcessResult,
    run_bounded_verifier,
    verify_native_made_cad,
)


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
                concept_sha256="f" * 64,
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
                ["moon.step", "moon.step.py", "moon.stl"],
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


if __name__ == "__main__":
    unittest.main()
