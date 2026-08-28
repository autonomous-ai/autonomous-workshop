import os
import stat
import tempfile
import unittest
from tests.invent.fake_gamevault import E2E_NODES, FakeGameVaultTransport, install_fake_gamevault
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ArtifactError, StateConflict, WorkshopError
from workshop.make.native import NativeMade
from workshop.make.native_gate import (
    NATIVE_CAD_FULL_TIER,
    NATIVE_CAD_VERIFIER_MODE,
)
from workshop.wish import Wish
from workshop.workflow import AgentRun
from workshop.workflow.agent_run import AgentArtifact, AgentOutcome
from workshop.workflow.native_run import (
    _stage_subject,
    native_run_paths,
    resume_native_run,
    start_native_run,
)
from workshop.workflow.proposals import AgentOutcomeProposal

from tests.end_to_end.test_native_full_run import (
    _FactoryEffects,
    _OneSessionProductAgent,
    _canonical_json,
    _product_run_assets_without_direct_release,
    _read_json,
    _sha256,
    _write_json,
)


class _FrozenAliasMakeAgent(_OneSessionProductAgent):
    """Reproduce the valid old finalizer output that omitted title/summary."""

    def __init__(self):
        super().__init__()
        self.rejected_outcome_bytes = None

    def _author_make(self, run_root, stage):
        rejection = stage["inputs"].get("host_make_proposal_rejection")
        if rejection is not None:
            if rejection["failure_code"] != "make-product-metadata-invalid":
                raise AssertionError("Make retry received the wrong host rejection")
            if "title" not in rejection["feedback"] or "summary" not in rejection[
                "feedback"
            ]:
                raise AssertionError("Make retry feedback is not actionable")
            super()._author_make(run_root, stage)
            return

        super()._author_make(run_root, stage)
        product_root = run_root / stage["inputs"]["product_root"]
        product_path = product_root / "product.json"
        product = _read_json(product_path)
        product["name"] = product.pop("title")
        product["description"] = product.pop("summary")
        _write_json(product_path, product)

        made_path = run_root / stage["inputs"]["contract_path"]
        old_made = _read_json(made_path)
        manifest = build_artifact_manifest(
            product_root,
            created_at=old_made["product_manifest"]["created_at"],
        )
        made = NativeMade(
            round=old_made["round"],
            wish_sha256=old_made["wish_sha256"],
            assignment_sha256=old_made["assignment_sha256"],
            taste_sha256=old_made["taste_sha256"],
            blueprint_sha256=old_made["blueprint_sha256"],
            invented_sha256=old_made["invented_sha256"],
            product_root=old_made["product_root"],
            cad_project_path=old_made["cad_project_path"],
            product_manifest=manifest,
            product=product,
            product_json_sha256=_sha256(product_path.read_bytes()),
            cad_verification_path=old_made["cad_verification_path"],
            cad_verification_sha256=_sha256(
                (product_root / old_made["cad_verification_path"]).read_bytes()
            ),
        )
        made_bytes = _canonical_json(made.to_dict())
        made_path.write_bytes(made_bytes)
        outcome = AgentOutcome(
            stage="make",
            status="ready",
            artifacts=(
                AgentArtifact(stage["inputs"]["contract_path"], _sha256(made_bytes)),
            ),
            proposed_transition="playtest",
        )
        proposal = AgentOutcomeProposal(
            checkpoint_sha256=stage["checkpoint_sha256"],
            subject_sha256=stage["subject_sha256"],
            outcome=outcome,
        )
        self.rejected_outcome_bytes = _canonical_json(proposal.to_dict())
        (run_root / "agent-outcome.json").write_bytes(self.rejected_outcome_bytes)

    def _author_playtest(self, run_root, stage):
        outcome = AgentOutcome(
            stage="playtest",
            status="waiting",
            needs=("Fixture stops after the repaired Make gate.",),
        )
        proposal = AgentOutcomeProposal(
            checkpoint_sha256=stage["checkpoint_sha256"],
            subject_sha256=stage["subject_sha256"],
            outcome=outcome,
        )
        (run_root / "agent-outcome.json").write_bytes(
            _canonical_json(proposal.to_dict())
        )


class _ChangedArtifactAgent(_OneSessionProductAgent):
    def __init__(self, rejected_attempt_limit=2):
        super().__init__()
        self.rejected_attempts = 0
        self.rejected_attempt_limit = rejected_attempt_limit

    def _author_make(self, run_root, stage):
        rejection = stage["inputs"].get("host_make_proposal_rejection")
        if rejection is not None:
            if rejection["failure_code"] != "make-artifact-invalid":
                raise AssertionError("Make artifact retry received the wrong rejection")
        super()._author_make(run_root, stage)
        if self.rejected_attempts >= self.rejected_attempt_limit:
            return
        product_path = (
            run_root / stage["inputs"]["product_root"] / "product.json"
        )
        product_path.write_bytes(product_path.read_bytes() + b"\n")
        self.rejected_attempts += 1

    def _author_playtest(self, run_root, stage):
        outcome = AgentOutcome(
            stage="playtest",
            status="waiting",
            needs=("Fixture stops after the repaired Make artifact gate.",),
        )
        proposal = AgentOutcomeProposal(
            checkpoint_sha256=stage["checkpoint_sha256"],
            subject_sha256=stage["subject_sha256"],
            outcome=outcome,
        )
        (run_root / "agent-outcome.json").write_bytes(
            _canonical_json(proposal.to_dict())
        )


def _verified_cad(made, **arguments):
    return SimpleNamespace(
        passed=True,
        receipt_sha256=_sha256(made.made_sha256.encode("ascii")),
        verifier_sha256=arguments["expected_verifier_sha256"],
        verifier_mode=NATIVE_CAD_VERIFIER_MODE,
        verification_tier=NATIVE_CAD_FULL_TIER,
        thickness_gate_required=True,
        print_ready_eligible=True,
    )


class NativeMakeProposalRecoveryTest(unittest.TestCase):
    def setUp(self):
        install_fake_gamevault(self, FakeGameVaultTransport(E2E_NODES))

    def _base_patches(self, home, launcher, effects):
        assets = _product_run_assets_without_direct_release(Path(home).parent)
        return (
            mock.patch.dict(os.environ, {"WORKSHOP_HOME": str(home)}, clear=True),
            mock.patch(
                "workshop.workflow.native_run.product_run_agent_assets",
                return_value=assets,
            ),
            mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ),
            mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ),
            mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=_verified_cad,
            ),
            mock.patch(
                "workshop.workflow.native_run._factory_credentials",
                side_effect=effects.credentials,
            ),
            mock.patch(
                "workshop.workflow.native_run.FactoryReleaseWriter",
                side_effect=effects.writer,
            ),
            mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession",
                side_effect=effects.session,
            ),
            mock.patch(
                "workshop.workflow.native_run.FactoryPublicTransition",
                side_effect=effects.transition,
            ),
        )

    def test_frozen_make_metadata_rejection_survives_crash_and_resumes_same_session(self):
        launcher = _FrozenAliasMakeAgent()
        effects = _FactoryEffects()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            wish = Wish.create(
                "frozen-make-metadata-repair",
                "Build a chess set inspired by iconic buildings around the world.",
            )
            patches = self._base_patches(home, launcher, effects)
            with (
                patches[0],
                patches[1],
                patches[2],
                patches[3],
                patches[4],
                patches[5],
                patches[6],
                patches[7],
                patches[8],
            ):
                with mock.patch(
                    "workshop.workflow.native_run._remove_rejected_agent_outcome",
                    side_effect=StateConflict("fixture crash before marker removal"),
                ), self.assertRaisesRegex(StateConflict, "fixture crash"):
                    start_native_run(wish)

                paths = native_run_paths(wish.product_id)
                checkpoint = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                ).snapshot()
                self.assertEqual((checkpoint.stage, checkpoint.status), ("make", "active"))
                self.assertTrue((paths.workspace / "agent-outcome.json").is_file())

                initial_make = launcher.stage_packets[2]
                self.assertNotIn(
                    "host_make_proposal_rejection", initial_make["inputs"]
                )
                expected_legacy_subject = _stage_subject(
                    "make",
                    {
                        "wish_sha256": initial_make["inputs"]["wish"]["sha256"],
                        "assignment_sha256": initial_make["inputs"]["assignment"][
                            "assignment_sha256"
                        ],
                        "taste_sha256": initial_make["inputs"]["assignment"][
                            "selected_taste_sha256"
                        ],
                        "blueprint_sha256": initial_make["inputs"]["blueprint_sha256"],
                        "invented_sha256": initial_make["inputs"]["invented"][
                            "invented_sha256"
                        ],
                        "round": 1,
                        "feedback_sha256": None,
                        "host_cad_gate_rejection_sha256": None,
                    },
                )
                self.assertEqual(initial_make["subject_sha256"], expected_legacy_subject)

                rejection_dir = (
                    paths.host_state
                    / "make-proposal-rejections"
                    / initial_make["checkpoint_sha256"]
                )
                head_path = rejection_dir / "current.json"
                head_bytes = head_path.read_bytes()
                head_path.write_bytes(head_bytes + b" ")
                with self.assertRaisesRegex(StateConflict, "head is invalid"):
                    resume_native_run(wish.product_id)
                head_path.write_bytes(head_bytes)

                head = _read_json(head_path)
                record_path = rejection_dir / (
                    "rejection-%s.json" % head["rejection_sha256"]
                )
                record_bytes = record_path.read_bytes()
                record_path.write_bytes(record_bytes + b" ")
                with self.assertRaisesRegex(StateConflict, "not canonical"):
                    resume_native_run(wish.product_id)
                record_path.write_bytes(record_bytes)

                tampered_record = _read_json(record_path)
                tampered_record["feedback"] = "Untrusted replacement feedback."
                tampered_identity = {
                    key: value
                    for key, value in tampered_record.items()
                    if key != "rejection_sha256"
                }
                tampered_record["rejection_sha256"] = _sha256(
                    _canonical_json(tampered_identity)
                )
                tampered_record_path = rejection_dir / (
                    "rejection-%s.json" % tampered_record["rejection_sha256"]
                )
                tampered_record_path.write_bytes(
                    _canonical_json(tampered_record) + b"\n"
                )
                os.chmod(tampered_record_path, 0o600)
                tampered_head_identity = {
                    "schema_version": head["schema_version"],
                    "kind": head["kind"],
                    "checkpoint_sha256": head["checkpoint_sha256"],
                    "rejection_sha256": tampered_record["rejection_sha256"],
                }
                tampered_head = {
                    **tampered_head_identity,
                    "head_sha256": _sha256(_canonical_json(tampered_head_identity)),
                }
                head_path.write_bytes(_canonical_json(tampered_head) + b"\n")
                with self.assertRaisesRegex(
                    StateConflict, "Make proposal rejection is invalid"
                ):
                    resume_native_run(wish.product_id)
                head_path.write_bytes(head_bytes)
                tampered_record_path.unlink()

                receipt = resume_native_run(wish.product_id)

            self.assertEqual(
                (receipt["stage"], receipt["status"]), ("playtest", "waiting")
            )
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(
                [packet["stage"] for packet in launcher.stage_packets],
                ["match", "invent", "make", "make", "playtest"],
            )
            retry_make = launcher.stage_packets[3]
            self.assertEqual(
                retry_make["checkpoint_sha256"], initial_make["checkpoint_sha256"]
            )
            self.assertNotEqual(
                retry_make["subject_sha256"], initial_make["subject_sha256"]
            )
            rejection = retry_make["inputs"]["host_make_proposal_rejection"]
            self.assertEqual(
                rejection["failure_code"], "make-product-metadata-invalid"
            )
            self.assertIn("title", rejection["feedback"])
            self.assertIn("summary", rejection["feedback"])
            self.assertEqual(rejection["rejection_number"], 1)
            self.assertIsNone(rejection["previous_rejection_sha256"])
            self.assertEqual(
                rejection["rejection_sha256"],
                _sha256(
                    _canonical_json(
                        {
                            key: value
                            for key, value in rejection.items()
                            if key != "rejection_sha256"
                        }
                    )
                ),
            )

            self.assertEqual(stat.S_IMODE(rejection_dir.stat().st_mode), 0o700)
            record_path = rejection_dir / (
                "rejection-%s.json" % rejection["rejection_sha256"]
            )
            quarantine_path = rejection_dir / (
                "outcome-%s.json" % rejection["rejected_proposal_file_sha256"]
            )
            for private_path in (record_path, quarantine_path, rejection_dir / "current.json"):
                self.assertEqual(stat.S_IMODE(private_path.stat().st_mode), 0o600)
            self.assertEqual(quarantine_path.read_bytes(), launcher.rejected_outcome_bytes)
            self.assertEqual(_read_json(record_path), rejection)
            self.assertEqual(len(list(rejection_dir.glob("rejection-*.json"))), 1)
            self.assertEqual(len(list(rejection_dir.glob("outcome-*.json"))), 1)
            self.assertFalse((paths.workspace / "agent-outcome.json").exists())
            repaired_product = _read_json(
                paths.workspace / "artifacts/make/r0001/product/product.json"
            )
            self.assertEqual(repaired_product["title"], "Orbit Dog Draughts")
            self.assertTrue(repaired_product["summary"])

    def test_make_artifact_binding_rejection_is_repaired(self):
        launcher = _ChangedArtifactAgent()
        effects = _FactoryEffects()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            wish = Wish.create(
                "make-state-conflict-is-fatal",
                "Build a toy whose sealed Make binding must remain exact.",
            )
            patches = self._base_patches(home, launcher, effects)
            with (
                patches[0],
                patches[1],
                patches[2],
                patches[3],
                patches[4],
                patches[5],
                patches[6],
                patches[7],
                patches[8],
            ):
                receipt = start_native_run(wish)
                paths = native_run_paths(wish.product_id)

            self.assertEqual(
                (receipt["stage"], receipt["status"]), ("playtest", "waiting")
            )
            self.assertEqual(
                [packet["stage"] for packet in launcher.stage_packets],
                ["match", "invent", "make", "make", "make", "playtest"],
            )
            first_rejection = launcher.stage_packets[3]["inputs"][
                "host_make_proposal_rejection"
            ]
            rejection = launcher.stage_packets[4]["inputs"][
                "host_make_proposal_rejection"
            ]
            self.assertEqual(first_rejection["rejection_number"], 1)
            self.assertEqual(rejection["rejection_number"], 2)
            self.assertEqual(
                rejection["previous_rejection_sha256"],
                first_rejection["rejection_sha256"],
            )
            self.assertEqual(rejection["failure_code"], "make-artifact-invalid")
            rejection_dir = (
                paths.host_state
                / "make-proposal-rejections"
                / launcher.stage_packets[2]["checkpoint_sha256"]
            )
            self.assertEqual(len(list(rejection_dir.glob("rejection-*.json"))), 2)
            self.assertEqual(len(list(rejection_dir.glob("outcome-*.json"))), 2)
            self.assertFalse((paths.workspace / "agent-outcome.json").exists())

    def test_make_rejection_budget_is_persistent_and_creates_no_orphan(self):
        launcher = _ChangedArtifactAgent(rejected_attempt_limit=3)
        effects = _FactoryEffects()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            wish = Wish.create(
                "make-rejection-budget-is-bounded",
                "Build a toy whose invalid Make proposals must stay bounded.",
            )
            patches = self._base_patches(home, launcher, effects)
            with (
                patches[0],
                patches[1],
                patches[2],
                patches[3],
                patches[4],
                patches[5],
                patches[6],
                patches[7],
                patches[8],
                mock.patch(
                    "workshop.workflow.native_run._MAX_MAKE_PROPOSAL_REJECTIONS",
                    2,
                ),
            ):
                with self.assertRaisesRegex(
                    WorkshopError, "bounded host rejection budget"
                ):
                    start_native_run(wish)
                paths = native_run_paths(wish.product_id)

            self.assertEqual(
                [packet["stage"] for packet in launcher.stage_packets],
                ["match", "invent", "make", "make", "make"],
            )
            rejection_dir = (
                paths.host_state
                / "make-proposal-rejections"
                / launcher.stage_packets[2]["checkpoint_sha256"]
            )
            self.assertEqual(len(list(rejection_dir.glob("rejection-*.json"))), 2)
            self.assertEqual(len(list(rejection_dir.glob("outcome-*.json"))), 2)
            self.assertTrue((paths.workspace / "agent-outcome.json").is_file())

    def test_make_state_conflict_remains_fatal(self):
        launcher = _OneSessionProductAgent()
        effects = _FactoryEffects()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            wish = Wish.create(
                "make-state-conflict-is-fatal",
                "Build a toy whose trusted Make state must remain exact.",
            )
            patches = self._base_patches(home, launcher, effects)
            with (
                patches[0],
                patches[1],
                patches[2],
                patches[3],
                patches[4],
                patches[5],
                patches[6],
                patches[7],
                patches[8],
                mock.patch(
                    "workshop.workflow.native_run._evaluate_make_stage",
                    side_effect=StateConflict("trusted Make state changed"),
                ),
            ):
                with self.assertRaisesRegex(StateConflict, "trusted Make state changed"):
                    start_native_run(wish)
                paths = native_run_paths(wish.product_id)

            self.assertTrue((paths.workspace / "agent-outcome.json").is_file())
            self.assertFalse((paths.host_state / "make-proposal-rejections").exists())

    def test_trusted_cad_integrity_error_is_not_an_agent_repair(self):
        launcher = _OneSessionProductAgent()
        effects = _FactoryEffects()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            wish = Wish.create(
                "make-host-integrity-is-fatal",
                "Build a toy whose trusted CAD verifier must remain exact.",
            )
            patches = self._base_patches(home, launcher, effects)
            with (
                patches[0],
                patches[1],
                patches[2],
                patches[3],
                mock.patch(
                    "workshop.workflow.native_run.verify_native_made_cad",
                    side_effect=ArtifactError(
                        "native CAD verifier differs from its trusted input hash"
                    ),
                ),
                patches[5],
                patches[6],
                patches[7],
                patches[8],
            ):
                with self.assertRaisesRegex(ArtifactError, "trusted input hash"):
                    start_native_run(wish)
                paths = native_run_paths(wish.product_id)

            self.assertTrue((paths.workspace / "agent-outcome.json").is_file())
            self.assertFalse(
                (paths.host_state / "make-proposal-rejections").exists()
            )


if __name__ == "__main__":
    unittest.main()
