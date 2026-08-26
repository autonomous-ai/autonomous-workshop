import hashlib
import json
import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ArtifactError, ContractError, StateConflict, TransitionError
from workshop.workflow import (
    AgentArtifact,
    AgentOutcome,
    AgentRun,
    DeterministicGateReceipt,
)


EVIDENCE_SHA256 = "e" * 64


def canonical_wish(product_id, objective):
    return json.dumps(
        {
            "schema_version": 1,
            "product_id": product_id,
            "objective": objective,
            "constraints": {},
            "context": {"source": "agent-run-test"},
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class AgentRunTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.product_run_constitution = (
            self.root / "source" / ".agents" / "product-run" / "AGENTS.md"
        )
        self.skill = self.root / "skill"
        self.product_run_constitution.parent.mkdir(parents=True)
        self.skill.mkdir()
        self.product_run_constitution.write_bytes(b"# Product run constitution\n")
        (self.skill / "SKILL.md").write_bytes(b"# Workshop skill\n")
        references = self.skill / "references"
        references.mkdir()
        (references / "make-playtest.md").write_bytes(b"exact gate guidance\n")
        self.run_root = self.root / "run"
        self.host_state_root = self.root / "host-state"
        self.product_id = "wish-run-1"
        self.wish_bytes = canonical_wish(
            self.product_id, "Make a clockwork moon."
        )

    def create(self, *, max_rounds=4, **kwargs):
        return AgentRun.create(
            self.run_root,
            host_state_root=self.host_state_root,
            product_id=self.product_id,
            wish_bytes=self.wish_bytes,
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
            max_rounds=max_rounds,
            **kwargs,
        )

    def artifact(self, run, stage, name=None, content=None):
        name = name or (stage + ".json")
        content = content or ('{"stage":"%s"}\n' % stage).encode("utf-8")
        relative = "artifacts/%s/%s" % (stage, name)
        path = run.run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return AgentArtifact(relative, hashlib.sha256(content).hexdigest())

    def outcome(self, run, stage, transition, *, name=None, content=None):
        return AgentOutcome(
            stage=stage,
            status="ready",
            artifacts=(self.artifact(run, stage, name=name, content=content),),
            proposed_transition=transition,
        )

    def gate(self, run, outcome, *, passed=True, subject=None):
        return DeterministicGateReceipt(
            stage=outcome.stage,
            gate_id=outcome.stage + "-deterministic-gate",
            passed=passed,
            subject_sha256=subject or run.expected_gate_subject_sha256(),
            outcome_sha256=outcome.sha256,
            evidence_sha256=EVIDENCE_SHA256,
        )

    def advance(self, run, stage, transition, *, name=None, content=None, passed=True):
        outcome = self.outcome(
            run, stage, transition, name=name, content=content
        )
        return run.apply_outcome(outcome, gate=self.gate(run, outcome, passed=passed))

    def reach_playtest(self, run):
        for stage, transition in (
            ("wish", "match"),
            ("match", "invent"),
            ("invent", "make"),
            ("make", "playtest"),
        ):
            self.advance(run, stage, transition)

    def test_create_materializes_exact_private_immutable_inputs(self):
        run = self.create()
        checkpoint = run.snapshot()

        self.assertEqual(checkpoint.stage, "wish")
        self.assertEqual(checkpoint.status, "active")
        self.assertEqual(checkpoint.product_id, self.product_id)
        self.assertEqual(
            checkpoint.wish_sha256,
            hashlib.sha256(self.wish_bytes).hexdigest(),
        )
        expected = {
            "WISH.json": self.wish_bytes,
            "AGENTS.md": b"# Product run constitution\n",
            ".agents/skills/autonomous-workshop/SKILL.md": b"# Workshop skill\n",
            ".agents/skills/autonomous-workshop/references/make-playtest.md": (
                b"exact gate guidance\n"
            ),
        }
        self.assertEqual(stat.S_IMODE(run.run_root.stat().st_mode), 0o700)
        self.assertEqual(
            stat.S_IMODE(run.host_state_root.stat().st_mode),
            0o700,
        )
        self.assertEqual(
            stat.S_IMODE((run.host_state_root / "agent-run.json").stat().st_mode),
            0o600,
        )
        self.assertFalse((run.run_root / ".workshop").exists())
        for relative, content in expected.items():
            path = run.run_root / relative
            self.assertEqual(path.read_bytes(), content)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o400)
            self.assertEqual(
                checkpoint.input_sha256s[relative], hashlib.sha256(content).hexdigest()
            )

        reopened = AgentRun.open(
            run.run_root,
            host_state_root=run.host_state_root,
            expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
        )
        self.assertEqual(reopened.snapshot(), checkpoint)

    def test_create_materializes_catalog_and_executable_domain_skills(self):
        cad = self.root / "cad-skill"
        (cad / "scripts").mkdir(parents=True)
        (cad / "SKILL.md").write_bytes(b"# CAD skill\n")
        checker = cad / "scripts" / "check_mesh"
        checker.write_bytes(b"#!/bin/sh\nexit 0\n")
        checker.chmod(0o755)

        catalog = self.root / "inventors"
        alice = catalog / "alice"
        alice.mkdir(parents=True)
        (alice / "inventor.json").write_text(
            '{"id":"alice","schema_version":6}\n', encoding="utf-8"
        )
        (alice / "TASTE.md").write_text(
            "---\nname: Alice\ndescription: Exact classics.\n---\n",
            encoding="utf-8",
        )

        run = self.create(
            domain_skill_roots={"cad": cad},
            inventor_catalog_root=catalog,
        )
        checkpoint = run.snapshot()
        expected_modes = {
            ".agents/skills/cad/SKILL.md": 0o400,
            ".agents/skills/cad/scripts/check_mesh": 0o500,
            "catalog/inventors/alice/inventor.json": 0o400,
            "catalog/inventors/alice/TASTE.md": 0o400,
        }
        for relative, mode in expected_modes.items():
            path = run.run_root / relative
            self.assertIn(relative, checkpoint.input_sha256s)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), mode)
        self.assertEqual(
            stat.S_IMODE((run.run_root / "catalog" / "inventors").stat().st_mode),
            0o500,
        )

        run_checker = run.run_root / ".agents/skills/cad/scripts/check_mesh"
        run_checker.chmod(0o400)
        with self.assertRaisesRegex(StateConflict, "immutable input mode"):
            run.snapshot()

    def test_creation_requires_explicit_product_run_constitution_source(self):
        repository_agents = self.root / "AGENTS.md"
        repository_agents.write_bytes(b"# Builder-only repository guidance\n")

        with self.assertRaisesRegex(ContractError, "product-run constitution"):
            AgentRun.create(
                self.run_root,
                host_state_root=self.host_state_root,
                product_id="wish-run-wrong-constitution",
                wish_bytes=canonical_wish(
                    "wish-run-wrong-constitution", "Exact Wish"
                ),
                product_run_constitution_source=repository_agents,
                skill_root=self.skill,
            )
        self.assertFalse(self.run_root.exists())

    def test_creation_requires_canonical_wish_bound_to_product_id(self):
        pretty = json.dumps(
            json.loads(canonical_wish("canonical-wish", "Exact Wish")),
            indent=2,
        ).encode("utf-8")
        with self.assertRaisesRegex(ContractError, "canonical encoding"):
            AgentRun.create(
                self.run_root,
                host_state_root=self.host_state_root,
                product_id="canonical-wish",
                wish_bytes=pretty,
                product_run_constitution_source=self.product_run_constitution,
                skill_root=self.skill,
            )
        with self.assertRaisesRegex(ContractError, "product_id does not match"):
            AgentRun.create(
                self.run_root,
                host_state_root=self.host_state_root,
                product_id="expected-product",
                wish_bytes=canonical_wish("other-product", "Exact Wish"),
                product_run_constitution_source=self.product_run_constitution,
                skill_root=self.skill,
            )
        with self.assertRaisesRegex(ArtifactError, "credential"):
            AgentRun.create(
                self.run_root,
                host_state_root=self.host_state_root,
                product_id="private-wish",
                wish_bytes=canonical_wish(
                    "private-wish", "Use api_key=definitely-not-agent-data"
                ),
                product_run_constitution_source=self.product_run_constitution,
                skill_root=self.skill,
            )
        self.assertFalse(self.run_root.exists())
        self.assertFalse(self.host_state_root.exists())

    def test_creation_rejects_existing_root_and_symlinked_skill_input(self):
        self.run_root.mkdir()
        with self.assertRaises(StateConflict):
            self.create()

        other_run = self.root / "other-run"
        target = self.root / "outside.md"
        target.write_text("outside", encoding="utf-8")
        (self.skill / "linked.md").symlink_to(target)
        with self.assertRaisesRegex(ArtifactError, "regular file|symlink"):
            AgentRun.create(
                other_run,
                host_state_root=self.root / "other-host-state",
                product_id="wish-run-2",
                wish_bytes=canonical_wish("wish-run-2", "Exact Wish"),
                product_run_constitution_source=self.product_run_constitution,
                skill_root=self.skill,
            )
        self.assertFalse(other_run.exists())

    def test_host_state_is_external_and_bound_against_copy_or_wrong_roots(self):
        with self.assertRaisesRegex(ContractError, "must not overlap"):
            AgentRun.create(
                self.run_root,
                host_state_root=self.root,
                product_id="overlapping-roots",
                wish_bytes=canonical_wish("overlapping-roots", "Exact Wish"),
                product_run_constitution_source=self.product_run_constitution,
                skill_root=self.skill,
            )
        self.assertFalse(self.run_root.exists())

        run = self.create()
        copied_run = self.root / "copied-run"
        copied_host = self.root / "copied-host-state"
        shutil.copytree(run.run_root, copied_run)
        shutil.copytree(run.host_state_root, copied_host)

        with self.assertRaisesRegex(StateConflict, "another root"):
            AgentRun.open(copied_run, host_state_root=run.host_state_root)
        with self.assertRaisesRegex(StateConflict, "another host-state root"):
            AgentRun.open(run.run_root, host_state_root=copied_host)

        host_alias = self.root / "host-state-alias"
        host_alias.symlink_to(run.host_state_root, target_is_directory=True)
        with self.assertRaisesRegex(ContractError, "real directories"):
            AgentRun.open(run.run_root, host_state_root=host_alias)

    def test_only_exact_host_gate_receipt_advances_the_lifecycle(self):
        run = self.create()
        outcome = self.outcome(run, "wish", "match")
        with self.assertRaisesRegex(TransitionError, "host deterministic gate"):
            run.apply_outcome(outcome)
        self.assertEqual(run.snapshot().stage, "wish")

        wrong_subject = self.gate(run, outcome, subject="a" * 64)
        with self.assertRaisesRegex(TransitionError, "not bound"):
            run.apply_outcome(outcome, gate=wrong_subject)
        self.assertEqual(run.snapshot().stage, "wish")

        checkpoint = run.apply_outcome(outcome, gate=self.gate(run, outcome))
        self.assertEqual(checkpoint.stage, "match")
        self.assertIn("wish", checkpoint.stage_artifacts)

        forged = outcome.to_dict()
        forged["self_score"] = 100
        with self.assertRaisesRegex(ContractError, "fields"):
            AgentOutcome.from_mapping(forged)

    def test_host_gate_can_bind_full_subject_and_seal_a_verified_tree(self):
        run = self.create()
        outcome = self.outcome(run, "wish", "match")
        tree_file = self.artifact(
            run,
            "wish",
            name="product/notes.txt",
            content=b"exact gated bytes\n",
        )
        full_subject = "f" * 64
        gate = self.gate(run, outcome, subject=full_subject)

        checkpoint = run.apply_outcome(
            outcome,
            gate=gate,
            gate_subject_sha256=full_subject,
            additional_artifacts=(tree_file,),
        )

        self.assertEqual(
            [item.path for item in checkpoint.stage_artifacts["wish"]],
            [outcome.artifacts[0].path, tree_file.path],
        )
        (run.run_root / tree_file.path).write_bytes(b"changed\n")
        with self.assertRaisesRegex(StateConflict, "sealed agent artifact changed"):
            run.snapshot()

    def test_additional_gate_artifacts_are_bounded_and_stage_scoped(self):
        run = self.create()
        outcome = self.outcome(run, "wish", "match")
        wrong_stage = self.artifact(run, "match", name="wrong.txt")
        gate = self.gate(run, outcome)
        with self.assertRaisesRegex(ArtifactError, "must live under artifacts/wish"):
            run.apply_outcome(
                outcome,
                gate=gate,
                additional_artifacts=(wrong_stage,),
            )

        duplicate = outcome.artifacts[0]
        with self.assertRaisesRegex(ArtifactError, "paths must be unique"):
            run.apply_outcome(
                outcome,
                gate=gate,
                additional_artifacts=(duplicate,),
            )

    def test_complete_lifecycle_uses_one_bounded_host_checkpoint(self):
        run = self.create()
        for stage, transition in (
            ("wish", "match"),
            ("match", "invent"),
            ("invent", "make"),
            ("make", "playtest"),
            ("playtest", "release"),
            ("release", "deliver"),
            ("deliver", "complete"),
        ):
            checkpoint = self.advance(run, stage, transition)

        self.assertTrue(checkpoint.complete)
        self.assertEqual(checkpoint.stage, "deliver")
        self.assertEqual(checkpoint.round_index, 1)
        self.assertEqual(set(checkpoint.stage_artifacts), set(
            ("wish", "match", "invent", "make", "playtest", "release", "deliver")
        ))
        with self.assertRaises(TransitionError):
            run.apply_outcome(
                AgentOutcome(
                    stage="deliver",
                    status="failed",
                    needs=("already complete",),
                )
            )

    def test_wait_is_resumable_but_failure_is_terminal_and_neither_advances(self):
        waiting_run = self.create()
        waiting = AgentOutcome(
            stage="wish",
            status="waiting",
            needs=("customer-choice-required",),
        )
        checkpoint = waiting_run.apply_outcome(waiting)
        self.assertEqual((checkpoint.stage, checkpoint.status), ("wish", "waiting"))
        self.assertEqual(waiting_run.resume().status, "active")
        self.advance(waiting_run, "wish", "match")

        failed_run = AgentRun.create(
            self.root / "failed-run",
            host_state_root=self.root / "failed-host-state",
            product_id="wish-run-failed",
            wish_bytes=canonical_wish("wish-run-failed", "Another Wish"),
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
        )
        failed = AgentOutcome(
            stage="wish", status="failed", needs=("contract-invalid",)
        )
        checkpoint = failed_run.apply_outcome(failed)
        self.assertEqual((checkpoint.stage, checkpoint.status), ("wish", "failed"))
        with self.assertRaises(TransitionError):
            failed_run.resume()
        with self.assertRaises(TransitionError):
            failed_run.apply_outcome(self.outcome(failed_run, "wish", "match"))

    def test_failed_playtest_returns_to_new_make_and_consumes_round(self):
        run = self.create(max_rounds=2)
        self.reach_playtest(run)
        first_make = run.snapshot().stage_artifacts["make"][0]

        failed_playtest = self.outcome(run, "playtest", "make")
        checkpoint = run.apply_outcome(
            failed_playtest, gate=self.gate(run, failed_playtest, passed=False)
        )
        self.assertEqual((checkpoint.stage, checkpoint.round_index), ("make", 2))
        self.assertEqual(
            checkpoint.invalidated_stages,
            ("playtest", "release", "deliver"),
        )
        self.assertEqual(
            checkpoint.stage_artifacts["playtest"][0], failed_playtest.artifacts[0]
        )

        support = self.artifact(
            run,
            "make",
            name="round-02-support.json",
            content=b'{"revision":2}\n',
        )
        second_make = AgentOutcome(
            stage="make",
            status="ready",
            artifacts=(first_make, support),
            proposed_transition="playtest",
        )
        checkpoint = run.apply_outcome(second_make, gate=self.gate(run, second_make))
        self.assertEqual(checkpoint.stage_artifacts["make"][0], first_make)
        self.assertEqual(len(checkpoint.stage_artifacts["make"]), 2)
        self.assertEqual(
            checkpoint.invalidated_stages,
            ("playtest", "release", "deliver"),
        )
        second_failure = self.outcome(
            run,
            "playtest",
            "make",
            name="round-02.json",
            content=b'{"result":"improve"}\n',
        )
        with self.assertRaisesRegex(TransitionError, "budget"):
            run.apply_outcome(
                second_failure, gate=self.gate(run, second_failure, passed=False)
            )
        self.assertEqual(run.snapshot().stage, "playtest")

    def test_passing_playtest_cannot_return_to_make_and_failure_cannot_advance(self):
        run = self.create()
        self.reach_playtest(run)
        revise = self.outcome(run, "playtest", "make")
        with self.assertRaisesRegex(TransitionError, "passing Playtest"):
            run.apply_outcome(revise, gate=self.gate(run, revise, passed=True))

        advance = self.outcome(
            run,
            "playtest",
            "release",
            name="passing.json",
            content=b'{"passed":true}\n',
        )
        with self.assertRaisesRegex(TransitionError, "failed deterministic gate"):
            run.apply_outcome(advance, gate=self.gate(run, advance, passed=False))
        self.assertEqual(run.snapshot().stage, "playtest")

    def test_artifact_paths_hashes_links_credentials_and_effect_receipts_fail_closed(self):
        run = self.create()
        content = b'{"ok":true}\n'
        valid = self.artifact(run, "wish", content=content)
        with self.assertRaises(ContractError):
            AgentArtifact("artifacts/wish/../escape.json", valid.sha256)
        with self.assertRaisesRegex(ArtifactError, "hash"):
            run.validate_outcome(
                AgentOutcome(
                    stage="wish",
                    status="ready",
                    artifacts=(AgentArtifact(valid.path, "a" * 64),),
                    proposed_transition="match",
                )
            )

        linked = run.run_root / "artifacts" / "wish" / "linked.json"
        linked.symlink_to(run.run_root / "AGENTS.md")
        with self.assertRaises(ArtifactError):
            run.validate_outcome(
                AgentOutcome(
                    stage="wish",
                    status="ready",
                    artifacts=(
                        AgentArtifact(
                            "artifacts/wish/linked.json",
                            hashlib.sha256(b"# Product run constitution\n").hexdigest(),
                        ),
                    ),
                    proposed_transition="match",
                )
            )

        credential = b'api_key="definitely-not-agent-data"\n'
        with self.assertRaisesRegex(ArtifactError, "credential"):
            run.validate_outcome(
                self.outcome(
                    run,
                    "wish",
                    "match",
                    name="credential.txt",
                    content=credential,
                )
            )
        with self.assertRaisesRegex(ArtifactError, "effect receipts"):
            run.validate_outcome(
                self.outcome(
                    run,
                    "wish",
                    "match",
                    name="factory-receipt.json",
                )
            )

    def test_input_checkpoint_and_sealed_artifact_tampering_is_detected(self):
        run = self.create()
        self.advance(run, "wish", "match")
        artifact = run.snapshot().stage_artifacts["wish"][0]
        artifact_path = run.run_root / artifact.path
        artifact_path.write_bytes(b"changed\n")
        with self.assertRaisesRegex(StateConflict, "sealed agent artifact"):
            run.snapshot()

        input_run = AgentRun.create(
            self.root / "input-run",
            host_state_root=self.root / "input-host-state",
            product_id="input-run",
            wish_bytes=canonical_wish("input-run", "Immutable Wish"),
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
        )
        wish = input_run.run_root / "WISH.json"
        os.chmod(wish, 0o600)
        wish.write_bytes(b"Changed Wish")
        with self.assertRaisesRegex(StateConflict, "immutable input"):
            input_run.snapshot()

        checkpoint_run = AgentRun.create(
            self.root / "checkpoint-run",
            host_state_root=self.root / "checkpoint-host-state",
            product_id="checkpoint-run",
            wish_bytes=canonical_wish("checkpoint-run", "Checkpoint Wish"),
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
        )
        checkpoint_path = checkpoint_run.host_state_root / "agent-run.json"
        value = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        value["stage"] = "deliver"
        checkpoint_path.write_text(json.dumps(value), encoding="utf-8")
        os.chmod(checkpoint_path, 0o600)
        with self.assertRaisesRegex(StateConflict, "digest"):
            checkpoint_run.snapshot()

    def test_stale_host_and_oversized_or_private_outcome_are_rejected(self):
        run = self.create()
        stale = AgentRun.open(
            run.run_root,
            host_state_root=run.host_state_root,
            expected_checkpoint_sha256=run.snapshot().checkpoint_sha256,
        )
        self.advance(run, "wish", "match")
        with self.assertRaisesRegex(StateConflict, "changed since"):
            stale.snapshot()

        with self.assertRaises(ContractError):
            AgentOutcome(
                stage="match",
                status="waiting",
                needs=("x" * 1_025,),
            )
        with self.assertRaisesRegex(ArtifactError, "credential"):
            AgentOutcome(
                stage="match",
                status="waiting",
                needs=("password=not-allowed-in-agent-output",),
            )


if __name__ == "__main__":
    unittest.main()
