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
    PARTIAL_CONCEPT_ENVIRONMENT,
    SIMPLIFIED_CONCEPT_ENVIRONMENT,
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
            simplified_concept=(
                os.environ.get(SIMPLIFIED_CONCEPT_ENVIRONMENT) == "1"
            ),
        )
        self.assertEqual(report.stages, CANONICAL_ROUTES[report.effort])
        self.assertEqual(report.session_starts, 1)
        self.assertGreaterEqual(report.session_resumes, len(report.stages) - 1)
        self.assertEqual(report.context_records_verified, len(report.stages))
        self.assertEqual(report.final_stage, "release")
        self.assertEqual(report.final_status, "complete")
        self.assertEqual(report.publication_status, "public")
        if os.environ.get(SIMPLIFIED_CONCEPT_ENVIRONMENT) == "1":
            evidence = report.simplified_concept_acceptance
            self.assertIsNotNone(evidence)
            self.assertEqual(
                evidence["capability_version"],
                "invent-concept-v2/concept-v3/deep-economics-v14",
            )
            self.assertEqual(
                evidence["session_continuity"], "one-verified-native-session"
            )
            self.assertGreaterEqual(evidence["native_turn_count"], len(report.stages))
            self.assertEqual(
                set(evidence["authored_input_sha256s"]),
                {"source", "visual_plan"},
            )
            self.assertGreaterEqual(evidence["visual_role_count"], 2)
            self.assertLessEqual(evidence["visual_role_count"], 20)
            self.assertEqual(
                evidence["make_transition"],
                "verified-sealed-v3-invent-to-make",
            )
        print(json.dumps(report.to_dict(include_local_paths=False), sort_keys=True))

    def test_forge_partial_concept_effect_wait_reconciles_without_repeating_invent(self):
        preflight_codex()
        configured = os.environ.get(HOME_ENVIRONMENT)
        if configured and os.environ.get(PARTIAL_CONCEPT_ENVIRONMENT) != "1":
            self.skipTest("the partial-role acceptance requires an isolated home")
        if configured:
            report = run_mock_session_acceptance(
                Path(configured).resolve(),
                effort="forge",
                turn_timeout_seconds=int(
                    os.environ.get("WORKSHOP_MOCK_SESSION_TURN_TIMEOUT", "900")
                ),
                partial_concept_roles=True,
            )
        else:
            with tempfile.TemporaryDirectory(
                prefix="workshop-mock-session-partial-"
            ) as value:
                report = run_mock_session_acceptance(
                    Path(value).resolve(),
                    effort="forge",
                    turn_timeout_seconds=int(
                        os.environ.get("WORKSHOP_MOCK_SESSION_TURN_TIMEOUT", "900")
                    ),
                    partial_concept_roles=True,
                )
        self.assertEqual(report.stages, CANONICAL_ROUTES["forge"])
        self.assertEqual(report.session_starts, 1)
        self.assertGreaterEqual(report.session_resumes, len(report.stages) - 1)
        self.assertEqual(report.context_records_verified, len(report.stages))
        self.assertEqual((report.final_stage, report.final_status), ("release", "complete"))
        self.assertEqual(
            report.concept_wait_resume["final_receipts"],
            "verified-exact-ledger-and-image-bytes",
        )
        self.assertFalse(report.concept_wait_resume["completed_roles_resent"])
        self.assertFalse(report.concept_wait_resume["invent_cognition_repeated"])


if __name__ == "__main__":
    unittest.main()
