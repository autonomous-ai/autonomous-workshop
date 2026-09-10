"""Host-only publication preserves exact pending releases across policy upgrades."""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import tests.release.test_native_release as release_fixtures
from workshop.errors import StateConflict
from workshop.errors import ContractError
from workshop.release.native import read_native_release
from workshop.wish import Wish
from workshop.workflow import native_run
from workshop.workflow.agent_run import AgentArtifact, AgentOutcome


class MakeOutputPublishHostTest(unittest.TestCase):
    def setUp(self):
        self.fixture = release_fixtures.NativeReleaseTest("test_round_trip_rehashes_full_tree_and_exposes_host_inputs")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.release = self.fixture._release(schema_version=3)
        self.contract_path = self.fixture._write_contract(self.release)
        self.run = SimpleNamespace(run_root=self.fixture.run_root)
        self.checkpoint = SimpleNamespace(
            effort="spark", status="waiting", stage="release",
            product_id="pending-product", checkpoint_sha256="a" * 64,
            input_sha256s={native_run._PRODUCT_RUN_MANUAL_DESIGN_EVIDENCE_INPUT: "d" * 64},
        )
        self.context = {
            "terminal_transition": "complete", "made": self.fixture.made,
            "playtested": None,
        }
        self.current_contract = {
            "native_release_schema_version": 4, "manual_path": None,
            "product_schema_version": 6, "product_status": "make-output-ready",
            "playtest_status": "not-run", "playtest_omission_path": "PLAYTEST-NOT-RUN.json",
        }
        self.subject_inputs = {
            "effort": "spark", "wish_sha256": self.fixture.assignment.wish_sha256,
            "taste_sha256": self.fixture.assignment.selected_taste_sha256,
            "blueprint_sha256": self.fixture.blueprint.sha256,
            "made_sha256": self.fixture.made.made_sha256,
            "product_artifact_sha256": self.fixture.made.product_manifest.artifact_sha256,
            "round": 1, "release_contract": self.current_contract,
            "host_cad_gate_rejection_sha256": None, "playtest_status": "not-run",
        }
        self.outcome = AgentOutcome(
            stage="release", status="ready", proposed_transition="complete",
            artifacts=(AgentArtifact("artifacts/release/release.json", hashlib.sha256(self.contract_path.read_bytes()).hexdigest()),),
        )

    def _wait(self, contract):
        return {
            "schema_version": 2,
            "proposal_checkpoint_sha256": "b" * 64,
            "proposal_subject_sha256": native_run._stage_subject("release", {**self.subject_inputs, "release_contract": contract}),
            "outcome": self.outcome.to_dict(),
        }

    def test_pending_schema_three_recovers_only_its_exact_original_subject(self):
        original = {
            "native_release_schema_version": 3, "manual_path": "MANUAL.pdf",
            "product_schema_version": 5, "product_status": "manual-ready",
            "playtest_status": "not-run", "playtest_omission_path": "PLAYTEST-NOT-RUN.json",
        }
        before = self.contract_path.read_bytes()
        for manual_design in (False, True):
            with self.subTest(manual_design=manual_design):
                expected = dict(original)
                if manual_design:
                    expected.update(manual_design_evidence_path="MANUAL-DESIGN.json", manual_design_evidence_schema_version=1)
                with mock.patch.object(native_run, "_read_release_effect_wait", return_value=self._wait(expected)), mock.patch("workshop.release.native.validate_release_pdf_manual", side_effect=AssertionError("Compatibility selection cannot run PDF checks")):
                    selected = native_run._pending_spark_release_contract(self.run, self.checkpoint, self.subject_inputs, self.context)
                self.assertEqual(selected, expected)
                self.assertEqual(self.contract_path.read_bytes(), before)

    def test_pending_subject_cannot_authorize_changed_upstream_bytes(self):
        waiting = self._wait({"native_release_schema_version": 3})
        with mock.patch.object(native_run, "_read_release_effect_wait", return_value=waiting), self.assertRaisesRegex(StateConflict, "subject changed"):
            native_run._pending_spark_release_contract(self.run, self.checkpoint, self.subject_inputs, self.context)

    def test_active_schema_three_proposal_recovers_after_interrupted_publication(self):
        self.checkpoint.status = "active"
        original = {
            "native_release_schema_version": 3, "manual_path": "MANUAL.pdf",
            "product_schema_version": 5, "product_status": "manual-ready",
            "playtest_status": "not-run", "playtest_omission_path": "PLAYTEST-NOT-RUN.json",
        }
        waiting = self._wait(original)
        proposal = native_run.AgentOutcomeProposal(
            checkpoint_sha256=self.checkpoint.checkpoint_sha256,
            subject_sha256=waiting["proposal_subject_sha256"], outcome=self.outcome,
        )
        path = self.run.run_root / "agent-outcome.json"
        path.write_text(json.dumps(proposal.to_dict()))
        self.assertEqual(native_run._pending_spark_release_contract(self.run, self.checkpoint, self.subject_inputs, self.context), original)
        self.checkpoint.checkpoint_sha256 = "f" * 64
        with self.assertRaisesRegex(StateConflict, "different checkpoint"):
            native_run._pending_spark_release_contract(self.run, self.checkpoint, self.subject_inputs, self.context)

    def test_failed_pending_subject_check_does_not_consume_waiting_checkpoint(self):
        self.run.resume = mock.Mock()
        waiting = self._wait(self.current_contract)
        with mock.patch.object(native_run, "_record_authorization"), mock.patch.object(native_run, "_read_release_effect_wait", return_value=waiting), mock.patch.object(native_run, "_prepare_stage_input", return_value=("c" * 64, {}, {})), self.assertRaisesRegex(StateConflict, "subject changed"):
            native_run._resume_native_run_locked("pending-product", run=self.run, checkpoint=self.checkpoint, paths=SimpleNamespace())
        self.run.resume.assert_not_called()

    def test_pending_replay_rebinds_packet_without_native_turn(self):
        waiting = self._wait(self.current_contract)
        subject = waiting["proposal_subject_sha256"]
        active = SimpleNamespace(**{**vars(self.checkpoint), "status": "active", "checkpoint_sha256": "c" * 64})
        complete = SimpleNamespace(status="complete")
        self.run.resume = mock.Mock(return_value=active)
        packet = {"checkpoint_sha256": self.checkpoint.checkpoint_sha256, "subject_sha256": subject, "stage": "release"}
        with mock.patch.object(native_run, "_record_authorization"), mock.patch.object(native_run, "_read_release_effect_wait", return_value=waiting), mock.patch.object(native_run, "_prepare_stage_input", return_value=(subject, packet, self.context)), mock.patch.object(native_run, "_rebind_existing_progress"), mock.patch.object(native_run, "_remove_release_effect_wait"), mock.patch.object(native_run, "_process_agent_outcome", return_value=complete) as process, mock.patch.object(native_run, "_native_receipt", return_value={"status": "complete"}), mock.patch.object(native_run, "_run_native_session", side_effect=AssertionError("Publication replay cannot launch native work")):
            result = native_run._resume_native_run_locked("pending-product", run=self.run, checkpoint=self.checkpoint, paths=SimpleNamespace())
        self.assertEqual(result["status"], "complete")
        self.run.resume.assert_called_once()
        saved = json.loads((self.run.run_root / "STAGE.json").read_bytes())
        self.assertEqual(saved["checkpoint_sha256"], active.checkpoint_sha256)
        self.assertEqual(saved["subject_sha256"], subject)
        self.assertEqual(process.call_args.kwargs["pending_proposal"].checkpoint_sha256, active.checkpoint_sha256)

    def test_partial_unsealed_legacy_release_is_retained_without_pdf_checks(self):
        self.run.host_state_root = self.fixture.run_root / "private-state"
        self.run.host_state_root.mkdir()
        self.checkpoint.stage_artifacts = {}
        self.checkpoint.status = "active"
        original = b'{"incomplete":'
        self.contract_path.write_bytes(original)
        pdf_path = self.fixture.run_root / "artifacts/release/package/MANUAL.pdf"
        saved_pdf = pdf_path.read_bytes()
        with mock.patch("workshop.release.native.validate_release_pdf_manual", side_effect=AssertionError("No PDF checks")):
            release = native_run._prepare_spark_publication(self.run, self.checkpoint, self.fixture.made)
        self.assertEqual(release.schema_version, 4)
        self.assertEqual(release.package_root, "artifacts/release/publish-package")
        self.assertEqual(pdf_path.read_bytes(), saved_pdf)
        archive = self.run.host_state_root / "retained-release-proposals" / (hashlib.sha256(original).hexdigest() + ".json")
        self.assertEqual(archive.read_bytes(), original)

    def test_unsealed_legacy_package_without_contract_does_not_block_publish(self):
        self.run.host_state_root = self.fixture.run_root / "private-state"
        self.run.host_state_root.mkdir()
        self.checkpoint.stage_artifacts = {}
        self.checkpoint.status = "active"
        self.contract_path.unlink()
        old_product = self.fixture.run_root / "artifacts/release/package/product.json"
        original = old_product.read_bytes()
        release = native_run._prepare_spark_publication(self.run, self.checkpoint, self.fixture.made)
        self.assertEqual(release.schema_version, 4)
        self.assertEqual(old_product.read_bytes(), original)

    def test_partial_contract_with_any_factory_intent_cannot_be_replaced(self):
        self.run.host_state_root = self.fixture.run_root / "private-state"
        self.run.host_state_root.mkdir()
        self.checkpoint.stage_artifacts = {}
        self.checkpoint.status = "active"
        self.contract_path.write_bytes(b'{"incomplete":')
        (self.run.host_state_root / "factory-effects.sqlite3").touch()
        with mock.patch.object(native_run.EffectLedger, "inspect_latest", return_value=object()), self.assertRaisesRegex(StateConflict, "Factory intent forbids"):
            native_run._prepare_spark_publication(self.run, self.checkpoint, self.fixture.made)
        self.assertEqual(self.contract_path.read_bytes(), b'{"incomplete":')
        self.assertFalse((self.run.host_state_root / "retained-release-proposals").exists())

    def test_missing_effected_contract_cannot_create_a_new_publication_carrier(self):
        self.run.host_state_root = self.fixture.run_root / "private-state"
        self.run.host_state_root.mkdir()
        self.checkpoint.stage_artifacts = {}
        self.checkpoint.status = "active"
        self.contract_path.unlink()
        (self.run.host_state_root / "factory-effects.sqlite3").touch()
        with mock.patch.object(native_run.EffectLedger, "inspect_latest", return_value=object()), self.assertRaisesRegex(StateConflict, "Factory intent forbids"):
            native_run._prepare_spark_publication(self.run, self.checkpoint, self.fixture.made)
        self.assertFalse(self.contract_path.exists())
        self.assertFalse((self.run.run_root / "artifacts/release/publish-package").exists())


class PendingSparkPublicationIntegrationTest(unittest.TestCase):
    def test_existing_pdf_publication_wait_resumes_after_make_output_upgrade(self):
        import tests.end_to_end.test_native_full_run as fixtures
        launcher = fixtures._OneSessionProductAgent()
        effects = fixtures._FactoryEffects()
        legacy_contract = {
            "native_release_schema_version": 3, "manual_path": "MANUAL.pdf",
            "product_schema_version": 5, "product_status": "manual-ready",
            "playtest_status": "not-run", "playtest_omission_path": "PLAYTEST-NOT-RUN.json",
        }
        def prepare_legacy(run_root, made):
            stage = json.loads((run_root / "STAGE.json").read_bytes())
            launcher._author_release(run_root, stage)
            return read_native_release(run_root)
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "home"
            wish = Wish.create("pending-spark-upgrade", "Build a pocket draughts set inspired by my orbit-loving dog.")
            with mock.patch.dict(os.environ, {"WORKSHOP_HOME": str(home)}, clear=True), mock.patch.object(native_run, "_source_checkout_root", return_value=None), mock.patch.object(native_run, "CodexNativeSessionLauncher", return_value=launcher), mock.patch.object(native_run, "verify_native_made_cad", side_effect=AssertionError("Spark host CAD must not run")), mock.patch.object(native_run, "FactoryReleaseWriter", side_effect=effects.writer), mock.patch.object(native_run, "FactoryAgentSession", side_effect=effects.session), mock.patch.object(native_run, "FactoryPublicTransition", side_effect=effects.transition):
                with mock.patch.object(native_run, "_materialized_release_contract", return_value=legacy_contract), mock.patch.object(native_run, "prepare_make_output_release", side_effect=prepare_legacy), mock.patch.object(native_run, "_factory_credentials", side_effect=ContractError("credentials unavailable")):
                    waiting = native_run.start_native_run(wish, effort="spark")
                self.assertEqual(waiting["status"], "waiting")
                paths = native_run.native_run_paths(wish.product_id)
                release_path = paths.workspace / "artifacts/release/release.json"
                saved_release = release_path.read_bytes()
                saved_pdf = (paths.workspace / "artifacts/release/package/MANUAL.pdf").read_bytes()
                turns = len(launcher.stage_packets)
                with mock.patch.object(native_run, "_factory_credentials", side_effect=effects.credentials), mock.patch.object(native_run, "prepare_make_output_release", side_effect=AssertionError("Existing PDF Release must not be rewritten")), mock.patch.object(native_run, "validate_bound_manual_design_evidence", side_effect=AssertionError("Legacy replay must not restore manual review")):
                    completed = native_run.resume_native_run(wish.product_id)
                self.assertEqual(completed["status"], "complete")
                self.assertEqual(completed["publication"]["status"], "public")
                self.assertEqual(len(launcher.stage_packets), turns)
                self.assertEqual(release_path.read_bytes(), saved_release)
                self.assertEqual((paths.workspace / "artifacts/release/package/MANUAL.pdf").read_bytes(), saved_pdf)
