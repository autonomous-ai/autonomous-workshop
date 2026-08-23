import tempfile
import unittest
import hashlib
import json
from pathlib import Path

from alice.policy import ReleasePolicy
from alice.store import DurableStore
from alice.transitions import TransitionEvidence, advance_with_evidence


class TransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = DurableStore(Path(self.tmp.name) / "db.sqlite3")
        self.store.create_candidate({"title": "Game"}, candidate_id="g1")

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def test_same_model_cannot_claim_research_transition(self) -> None:
        evidence = TransitionEvidence("e1", "same_model", True, {"result": "pass"})
        with self.assertRaises(ValueError):
            advance_with_evidence(self.store, "g1", "researched", evidence)

    def test_verified_deterministic_receipt_advances(self) -> None:
        task = self.store.enqueue_task(
            "candidate.prior_art",
            {
                "candidate_id": "g1",
                "candidate_version": 1,
                "role": "novelty_adversary",
            },
            candidate_id="g1",
            idempotency_key="prior-art-transition",
        )
        leased = self.store.lease_task("research-worker")
        content = {"checks": ["prior_art"]}
        completed = self.store.complete_task(
            leased.id,
            "research-worker",
            leased.lease_token,
            {
                "executor": "adapter",
                "receipt": {
                    "status": "passed",
                    "evidence_class": "independent_model",
                    "payload": content,
                },
            },
        )
        manifest = [
            {
                "action": task.kind,
                "task_id": task.id,
                "candidate_version": 1,
                "output_sha256": completed.output_sha256,
                "content_sha256": self.store.sha256_json(content),
                "executor": "adapter",
                "evidence_class": "independent_model",
            }
        ]
        manifest_hash = hashlib.sha256(
            json.dumps(
                manifest,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode()
        ).hexdigest()
        evidence = TransitionEvidence(
            "e2",
            "independent_model",
            True,
            {
                "candidate_id": "g1",
                "candidate_version": 1,
                "target_state": "researched",
                "artifacts": manifest,
                "artifact_manifest_sha256": manifest_hash,
            },
        )
        candidate = advance_with_evidence(self.store, "g1", "researched", evidence)
        self.assertEqual(candidate.state, "researched")

    def test_human_transition_requires_held_out(self) -> None:
        candidate = self.store.get_candidate("g1")
        for target in (
            "researched",
            "rules_valid",
            "digitally_playtested",
            "human_ready",
        ):
            candidate = self.store.transition_candidate(
                "g1",
                target,
                expected_state=candidate.state,
                expected_version=candidate.version,
            )
        with self.assertRaises(ValueError):
            advance_with_evidence(
                self.store,
                "g1",
                "human_validated",
                TransitionEvidence("human-1", "blind_human", True, {"groups": 3}),
            )

    def test_forged_allowed_receipt_cannot_override_denied_release_task(self) -> None:
        current = self.store.get_candidate("g1")
        current = self.store.transition_candidate(
            current.id,
            "production_validated",
            expected_state=current.state,
            expected_version=current.version,
        )
        packet_hash = "a" * 64
        release_manifest_hash = "b" * 64
        policy_hash = ReleasePolicy().policy_hash
        denied = {
            "allowed": False,
            "policy_hash": policy_hash,
            "effect_mode": "live",
            "failures": ["insufficient_blind_groups"],
            "production_packet_hash": packet_hash,
            "reviewed_packet_hash": packet_hash,
            "production_candidate_version": current.version,
            "artifact_manifest": [{"source": "real-evidence"}],
            "artifact_manifest_sha256": release_manifest_hash,
            "release_facts": {},
            "reward": {},
            "production_manifest": {"candidate_id": current.id},
            "candidate_id": current.id,
            "candidate_version": current.version,
            "target_state": "publish_ready",
        }
        task = self.store.enqueue_task(
            "release.evaluate",
            {
                "candidate_id": current.id,
                "candidate_version": current.version,
                "role": "alice_director",
            },
            candidate_id=current.id,
            idempotency_key="denied-release-task",
        )
        leased = self.store.lease_task("release-worker")
        completed = self.store.complete_task(
            leased.id,
            "release-worker",
            leased.lease_token,
            {"executor": "release_policy", "content": denied},
        )
        manifest = [
            {
                "action": task.kind,
                "task_id": task.id,
                "candidate_version": current.version,
                "output_sha256": completed.output_sha256,
                "content_sha256": self.store.sha256_json(denied),
                "executor": "release_policy",
                "evidence_class": "release_policy",
            }
        ]
        transition_manifest_hash = hashlib.sha256(
            json.dumps(
                manifest,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode()
        ).hexdigest()
        forged = {
            **denied,
            "allowed": True,
            "failures": [],
            "release_artifact_manifest_sha256": release_manifest_hash,
            "artifacts": manifest,
            "artifact_manifest_sha256": transition_manifest_hash,
        }

        with self.assertRaisesRegex(ValueError, "does not match durable"):
            advance_with_evidence(
                self.store,
                current.id,
                "publish_ready",
                TransitionEvidence("forged-release", "release_policy", True, forged),
                expected_policy_hash=policy_hash,
            )

        self.assertEqual(
            self.store.get_candidate(current.id).state, "production_validated"
        )


if __name__ == "__main__":
    unittest.main()
