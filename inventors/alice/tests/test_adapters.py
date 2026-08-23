from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alice.adapters import (  # noqa: E402
    AdapterError,
    AdapterReceipt,
    COMMAND_ADAPTER_CONTRACT_VERSION,
    CommandAdapter,
    adapter_input_sha256,
    canonical_adapter_input,
)


class CommandAdapterTests(unittest.TestCase):
    @staticmethod
    def adapter(
        *,
        status: str | None = "passed",
        hash_mode: str = "correct",
        payload: object = None,
    ) -> CommandAdapter:
        script = """
import hashlib
import json
import sys

encoded = sys.stdin.read()
digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
response = {"run_id": "adapter-run", "payload": PAYLOAD}
if STATUS is not None:
    response["status"] = STATUS
if HASH_MODE == "correct":
    response["input_sha256"] = digest
elif HASH_MODE == "mismatch":
    response["input_sha256"] = "0" * 64
elif HASH_MODE == "legacy":
    response["input_hash"] = digest
print(json.dumps(response, sort_keys=True))
"""
        script = script.replace("PAYLOAD", repr({} if payload is None else payload))
        script = script.replace("STATUS", repr(status))
        script = script.replace("HASH_MODE", repr(hash_mode))
        return CommandAdapter(
            "test-adapter",
            [sys.executable, "-c", script],
            evidence_class="deterministic_test",
        )

    def test_canonical_envelope_and_hash_are_public_and_deterministic(self) -> None:
        left = {"z": "café", "a": {"two": 2, "one": 1}}
        right = {"a": {"one": 1, "two": 2}, "z": "café"}
        encoded = canonical_adapter_input("rules.lint", left)

        self.assertEqual(encoded, canonical_adapter_input("rules.lint", right))
        self.assertEqual(
            adapter_input_sha256("rules.lint", left),
            hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            json.loads(encoded), {"operation": "rules.lint", "payload": left}
        )
        with self.assertRaises(ValueError):
            canonical_adapter_input("", {})
        with self.assertRaises(ValueError):
            canonical_adapter_input("bad", {"number": float("nan")})

    def test_only_exact_passed_receipt_with_matching_input_is_accepted(self) -> None:
        payload = {"candidate_id": "candidate-1", "version": 4}
        receipt = self.adapter(payload={"verdict": "ok"}).invoke(
            "rules.lint", payload
        )

        self.assertEqual(receipt.status, "passed")
        self.assertEqual(receipt.input_sha256, adapter_input_sha256("rules.lint", payload))
        self.assertEqual(receipt.input_hash, receipt.input_sha256)
        self.assertEqual(receipt.payload, {"verdict": "ok"})
        self.assertIn("input_sha256", asdict(receipt))
        self.assertNotIn("input_hash", asdict(receipt))

    def test_nonpassing_or_missing_status_is_rejected(self) -> None:
        for status in ("queued", "partial", "failed", "Passed", None):
            with self.subTest(status=status):
                with self.assertRaises(AdapterError):
                    self.adapter(status=status).invoke("physical.cad", {"shape": "pawn"})

    def test_missing_mismatched_or_legacy_input_digest_is_rejected(self) -> None:
        for hash_mode in ("missing", "mismatch", "legacy"):
            with self.subTest(hash_mode=hash_mode):
                with self.assertRaises(AdapterError):
                    self.adapter(hash_mode=hash_mode).invoke(
                        "physical.cad", {"shape": "pawn"}
                    )

    def test_response_payload_must_be_an_object(self) -> None:
        with self.assertRaises(AdapterError):
            self.adapter(payload=["not", "an", "object"]).invoke("rules.lint", {})

    def test_receipt_legacy_constructor_alias_does_not_change_wire_name(self) -> None:
        receipt = AdapterReceipt(
            adapter="in-process",
            run_id="one",
            status="passed",
            evidence_class="test",
            payload={},
            input_hash="a" * 64,
        )
        self.assertEqual(receipt.input_sha256, "a" * 64)
        with self.assertRaises(ValueError):
            AdapterReceipt(
                adapter="in-process",
                run_id="two",
                status="passed",
                evidence_class="test",
                payload={},
                input_sha256="a" * 64,
                input_hash="b" * 64,
            )

    def test_diagnostics_require_authenticated_versioned_adapter_identity(self) -> None:
        adapter = self.adapter(
            payload={
                "adapter": "test-adapter",
                "contract_version": COMMAND_ADAPTER_CONTRACT_VERSION,
                "ready": True,
                "authenticated": True,
                "capabilities": ["verified_test_capability"],
            }
        )

        diagnostics = adapter.diagnostics()

        self.assertTrue(diagnostics["ready"])
        self.assertTrue(diagnostics["authenticated"])
        self.assertEqual(
            diagnostics["contract_version"], COMMAND_ADAPTER_CONTRACT_VERSION
        )
        self.assertEqual(diagnostics["capabilities"], ["verified_test_capability"])

    def test_nonzero_exit_hashes_stderr_without_exposing_it(self) -> None:
        secret = "adapter-secret-that-must-not-enter-the-ledger"
        adapter = CommandAdapter(
            "failed-adapter",
            [
                sys.executable,
                "-c",
                f"import sys; sys.stderr.write({secret!r}); sys.exit(17)",
            ],
            evidence_class="deterministic_test",
        )

        with self.assertRaises(AdapterError) as raised:
            adapter.invoke("rules.lint", {})

        message = str(raised.exception)
        self.assertNotIn(secret, message)
        self.assertIn("exited 17", message)
        self.assertIn(
            "stderr_sha256=" + hashlib.sha256(secret.encode("utf-8")).hexdigest(),
            message,
        )

    def test_adapter_bounds_both_output_pipes(self) -> None:
        for stream in ("stdout", "stderr"):
            with self.subTest(stream=stream):
                script = (
                    "import sys; "
                    f"sys.{stream}.write('adapter-secret-' * 100000); "
                    f"sys.{stream}.flush()"
                )
                adapter = CommandAdapter(
                    "bounded-adapter",
                    [sys.executable, "-c", script],
                    evidence_class="test",
                    max_output_bytes=128,
                    max_stderr_bytes=128,
                    shutdown_grace_seconds=0.1,
                )
                with self.assertRaises(AdapterError) as caught:
                    adapter.invoke("rules.lint", {})
                self.assertIn(f"{stream} exceeded", str(caught.exception))
                self.assertNotIn("adapter-secret", str(caught.exception))

    @unittest.skipUnless(hasattr(os, "killpg"), "POSIX process groups required")
    def test_adapter_timeout_uses_term_then_kill_for_owned_group(self) -> None:
        script = (
            "import signal,time; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)"
        )
        adapter = CommandAdapter(
            "timeout-adapter",
            [sys.executable, "-c", script],
            evidence_class="test",
            timeout_seconds=0.4,
            shutdown_grace_seconds=0.1,
        )
        calls = []
        real_killpg = os.killpg

        def tracking_killpg(pgid: int, sig: signal.Signals) -> None:
            calls.append((pgid, sig))
            real_killpg(pgid, sig)

        started = time.monotonic()
        with patch("alice.providers.os.killpg", side_effect=tracking_killpg):
            with self.assertRaisesRegex(AdapterError, "timed out"):
                adapter.invoke("rules.lint", {})
        self.assertLess(time.monotonic() - started, 2.0)
        self.assertIn(signal.SIGTERM, [sig for _, sig in calls])
        self.assertIn(signal.SIGKILL, [sig for _, sig in calls])


if __name__ == "__main__":
    unittest.main()
