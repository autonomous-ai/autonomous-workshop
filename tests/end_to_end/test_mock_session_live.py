import json
import os
from pathlib import Path
import tempfile
import unittest

from tests.end_to_end.mock_session_harness import (
    ENABLE_ENVIRONMENT,
    HOME_ENVIRONMENT,
    preflight_codex,
    run_mock_session_acceptance,
)


@unittest.skipUnless(
    os.environ.get(ENABLE_ENVIRONMENT) == "1",
    "set WORKSHOP_RUN_MOCK_SESSION_E2E=1 to run the authenticated real-Codex acceptance",
)
class RealCodexMockSessionEndToEndTest(unittest.TestCase):
    def test_one_real_session_reaches_private_deliver_with_context_proofs(self):
        preflight_codex()
        configured = os.environ.get(HOME_ENVIRONMENT)
        home = (
            Path(configured).resolve()
            if configured
            else Path(tempfile.mkdtemp(prefix="workshop-mock-session-e2e-")).resolve()
        )
        timeout = int(os.environ.get("WORKSHOP_MOCK_SESSION_TURN_TIMEOUT", "300"))
        report = run_mock_session_acceptance(
            home,
            native_turn_timeout_seconds=timeout,
            native_model=os.environ.get("WORKSHOP_MOCK_SESSION_MODEL", "gpt-5.6-luna"),
            native_reasoning_effort=os.environ.get(
                "WORKSHOP_MOCK_SESSION_REASONING_EFFORT", "low"
            ),
        )
        self.assertEqual(report.stages, ("match", "invent", "concept", "make", "playtest", "release"))
        self.assertEqual(report.session_starts, 1)
        self.assertEqual(report.session_resumes, 5)
        self.assertIn(report.transport_retries, (0, 1))
        self.assertEqual(report.context_records_verified, 6)
        self.assertEqual(report.context_proof, "verified")
        self.assertEqual(report.final_stage, "deliver")
        self.assertEqual(report.final_status, "waiting")
        print(json.dumps(report.to_dict(), sort_keys=True))


if __name__ == "__main__":
    unittest.main()
