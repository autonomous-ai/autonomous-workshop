import json
import os
import signal
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from alice.providers import (
    AgentRequest,
    CommandAgentProvider,
    FixtureAgentProvider,
    ProviderError,
)


class ProviderTests(unittest.TestCase):
    def test_fixture_is_explicitly_non_external(self) -> None:
        request = AgentRequest("r1", "inventor_divergent", "invent", {})
        response = FixtureAgentProvider().run(request)
        self.assertTrue(response.content["fixture"])
        self.assertLess(response.confidence, 0.5)

    def test_command_provider_validates_json_contract(self) -> None:
        program = (
            "import json,sys; r=json.load(sys.stdin); "
            "json.dump({'request_id':r['request_id'],'content':{'ok':True},"
            "'confidence':0.8},sys.stdout)"
        )
        provider = CommandAgentProvider([sys.executable, "-c", program])
        response = provider.run(AgentRequest("r2", "rules_engineer", "rules", {}))
        self.assertEqual(response.request_id, "r2")
        self.assertTrue(response.content["ok"])

    def test_command_provider_rejects_unstructured_output(self) -> None:
        provider = CommandAgentProvider([sys.executable, "-c", "print('hello')"])
        with self.assertRaises(ProviderError):
            provider.run(AgentRequest("r3", "archivist", "compact", {}))

    def test_command_provider_hashes_stderr_instead_of_exposing_it(self) -> None:
        secret = "credential-marker-must-not-enter-the-ledger"
        provider = CommandAgentProvider(
            [
                sys.executable,
                "-c",
                f"import sys; print({secret!r}, file=sys.stderr); raise SystemExit(9)",
            ]
        )

        with self.assertRaises(ProviderError) as caught:
            provider.run(AgentRequest("r4", "archivist", "compact", {}))

        self.assertNotIn(secret, str(caught.exception))
        self.assertIn("stderr_sha256=", str(caught.exception))

    def test_command_provider_bounds_stdout_and_stderr(self) -> None:
        stdout_provider = CommandAgentProvider(
            [sys.executable, "-c", "import sys; sys.stdout.write('x' * 1000000)"],
            max_stderr_bytes=128,
            shutdown_grace_seconds=0.1,
        )
        with self.assertRaisesRegex(ProviderError, "stdout exceeded"):
            stdout_provider.run(
                AgentRequest("stdout-cap", "critic", "test", {}, max_output_bytes=128)
            )

        secret = "stderr-secret-must-stay-out"
        stderr_provider = CommandAgentProvider(
            [
                sys.executable,
                "-c",
                f"import sys; sys.stderr.write({secret!r} * 1000)",
            ],
            max_stderr_bytes=128,
            shutdown_grace_seconds=0.1,
        )
        with self.assertRaises(ProviderError) as caught:
            stderr_provider.run(
                AgentRequest("stderr-cap", "critic", "test", {})
            )
        self.assertIn("stderr exceeded", str(caught.exception))
        self.assertNotIn(secret, str(caught.exception))

    @unittest.skipUnless(hasattr(os, "killpg"), "POSIX process groups required")
    def test_timeout_terms_then_kills_group_containing_grandchild(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "grandchild.pid"
            grandchild = (
                "import signal,time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)"
            )
            parent = (
                "import pathlib,signal,subprocess,sys,time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                f"p=subprocess.Popen([sys.executable,'-c',{grandchild!r}]); "
                f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid)); "
                "time.sleep(60)"
            )
            provider = CommandAgentProvider(
                [sys.executable, "-c", parent],
                timeout_seconds=0.5,
                shutdown_grace_seconds=0.1,
            )
            calls = []
            real_killpg = os.killpg

            def tracking_killpg(pgid: int, sig: signal.Signals) -> None:
                calls.append((pgid, sig))
                real_killpg(pgid, sig)

            started = time.monotonic()
            with patch("alice.providers.os.killpg", side_effect=tracking_killpg):
                with self.assertRaisesRegex(ProviderError, "timed out"):
                    provider.run(AgentRequest("timeout", "critic", "test", {}))
            self.assertLess(time.monotonic() - started, 2.0)
            self.assertTrue(pid_file.is_file(), "grandchild was not created")
            signals = [sig for _, sig in calls]
            self.assertIn(signal.SIGTERM, signals)
            self.assertIn(signal.SIGKILL, signals)
            signaled_groups = {pgid for pgid, sig in calls if sig in {signal.SIGTERM, signal.SIGKILL}}
            self.assertEqual(len(signaled_groups), 1)

    def test_boolean_output_limit_and_confidence_are_rejected(self) -> None:
        provider = CommandAgentProvider(
            [
                sys.executable,
                "-c",
                "import json,sys; json.dump({'content':{},'confidence':True},sys.stdout)",
            ]
        )
        with self.assertRaisesRegex(ProviderError, "max_output_bytes"):
            provider.run(AgentRequest("bool-limit", "critic", "test", {}, max_output_bytes=True))
        with self.assertRaisesRegex(ProviderError, "confidence"):
            provider.run(AgentRequest("bool-confidence", "critic", "test", {}))


if __name__ == "__main__":
    unittest.main()
