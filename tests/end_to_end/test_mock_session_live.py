"""Opt-in authenticated Codex route acceptance."""

import json
import os
from pathlib import Path
import tempfile
import unittest

from tests.end_to_end.deterministic_fidelity import CANONICAL_ROUTES
from tests.end_to_end.mock_session_harness import (
    EFFORT_ENVIRONMENT,
    ENABLE_ENVIRONMENT,
    HOME_ENVIRONMENT,
    preflight_codex,
    run_mock_session_acceptance,
)


@unittest.skipUnless(
    os.environ.get(ENABLE_ENVIRONMENT) == "1",
    "set WORKSHOP_RUN_MOCK_SESSION_E2E=1 for authenticated Codex acceptance",
)
class RealCodexMockSessionEndToEndTest(unittest.TestCase):
    def test_selected_effort_reaches_published_release_with_context_proofs(self):
        preflight_codex()
        effort = os.environ.get(EFFORT_ENVIRONMENT)
        self.assertIn(effort, CANONICAL_ROUTES)
        configured = os.environ.get(HOME_ENVIRONMENT)
        if configured:
            home = Path(configured).resolve()
        else:
            temporary = tempfile.TemporaryDirectory(
                prefix="workshop-mock-session-e2e-"
            )
            self.addCleanup(temporary.cleanup)
            home = Path(temporary.name).resolve()
        timeout = int(os.environ.get("WORKSHOP_MOCK_SESSION_TURN_TIMEOUT", "900"))
        report = run_mock_session_acceptance(
            home,
            effort=str(effort),
            turn_timeout_seconds=timeout,
        )
        self.assertEqual(report.stages, CANONICAL_ROUTES[report.effort])
        self.assertEqual(report.session_starts, 1)
        self.assertEqual(report.session_resumes, len(report.stages) - 1)
        self.assertEqual(report.context_records_verified, len(report.stages))
        self.assertEqual(report.final_stage, "release")
        self.assertEqual(report.final_status, "complete")
        self.assertEqual(report.publication_status, "public")
        print(json.dumps(report.to_dict(include_local_paths=False), sort_keys=True))


if __name__ == "__main__":
    unittest.main()
