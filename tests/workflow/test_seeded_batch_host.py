"""ADR 0098 decisions 3 and 4: the host runs a seeded Make's batch, and the
native session works only on a check failure.

Contract: a run that froze ``seed.batch`` runs the batch once before the
first native Make turn of a checkpoint; a run without one (every run seeded
before ADR 0098) never does. A pass leaves the finalizer's proposal and
records no failure, so no native turn is needed. A check failure records a
packet that ``STAGE.json`` carries and lets the native turn start. A
harness failure stops the run naming each failed step, and a resume runs
the batch again. Seed nonces are host state the role guard accepts. A batch
tool other than the frozen one stops the run. The gate on a native proposal
reruns only the check layers, reusing unchanged passes, rejects a failure
with a fresh packet, and does not rerun the batch for the exact proposal a
pass finalized."""

from __future__ import annotations

import hashlib
import json
import tempfile
import types
import unittest
from pathlib import Path, PurePosixPath

from tests.skills.test_seal_proof import SEED_PRODUCT
from workshop.errors import ContractError, StateConflict
from workshop.make import seeded_batch as sb
from workshop.make.make_round_guard import NONCE_TABLE_NAME
from workshop.make.role_guard import _issued_seed_nonces
from workshop.make.seeded_batch import RunResult
from workshop.runtime.make_round_hook import MAKE_ROUND_GUARD_DIRECTORY
from workshop.workflow import native_run
from workshop.workflow import seeded_batch_host as host

CHECKPOINT = "c" * 64
CONTRACT = {
    "schema_version": 10,
    "geometries": [{"id": "body"}, {"id": "lid"}],
    "interfaces": [{"id": "hinge", "kind": "coupled", "components": ["body", "lid"]},
                   {"id": "seat", "kind": "static", "components": ["body", "lid"]}],
}


def product_tree(run_root):
    """Every file of the round's product tree, by path and sha256: what the
    finalizer seals as the Made manifest."""

    root = run_root / "artifacts/make/r0001/product"
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()}


class FakeRunner:
    """Deterministic steps: a named fragment fails as given; the finalizer
    writes the run's proposal as the real one does."""

    def __init__(self, run_root, results=None, verdict="PASS"):
        self.run_root = run_root
        self.results = results or {}
        self.verdict = verdict
        self.calls = []

    def __call__(self, argv, cwd, timeout):
        self.calls.append(list(argv))
        for fragment, result in self.results.items():
            if any(fragment in item for item in argv):
                return result
        if any(item.endswith("stage_proposal.py") for item in argv):
            (self.run_root / host.AGENT_OUTCOME).write_text('{"proposal": 1}\n')
            self.sealed_tree = product_tree(self.run_root)
        if "--report" in argv:
            # verify_project writes its record, whose Result is the verdict.
            report = Path(argv[argv.index("--report") + 1])
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text("- Result: **%s** (exit 0)\n" % self.verdict)
        return RunResult(0, "ok")


class SeededBatchHostTest(unittest.TestCase):
    def setUp(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.run_root = root / "workspace"
        self.host_state = root / "host-state"
        (self.host_state / MAKE_ROUND_GUARD_DIRECTORY).mkdir(parents=True)
        (self.run_root / "seed").mkdir(parents=True)
        (self.run_root / "WISH.json").write_text(json.dumps({
            "objective": "Name this toy exactly: Hinge Box (v2).\n# Box\n",
            "context": {"design_contract": CONTRACT}, "references": [{"name": "ref-01.png"}]}))
        (self.run_root / "seed/APPROVAL.json").write_text(json.dumps({"schema_version": 2, "nozzle_mm": 0.4}))
        (self.run_root / "seed/SEED-PRODUCT.json").write_text(json.dumps(SEED_PRODUCT))
        self._options(batch=True)

    def _options(self, batch):
        seed = {"approval_sha256": "a" * 64, "manifest_sha256": "b" * 64}
        if batch:
            seed["batch"] = {"tool_sha256": sb.module_sha256()}
        (self.run_root / "MAKE-OPTIONS.json").write_text(json.dumps(
            {"schema_version": 4 if batch else 3, "check_motion": True, "seed": seed}))

    def _run(self, results=None, verdict="PASS"):
        runner = FakeRunner(self.run_root, results, verdict)
        attempt = host.run_for_checkpoint(self.run_root, self.host_state, CHECKPOINT, 1, runner=runner)
        return attempt, runner

    def test_a_run_without_a_frozen_batch_never_runs_one(self):
        self._options(batch=False)
        self.assertFalse(host.batch_due(self.run_root, self.host_state, CHECKPOINT))
        self.assertIsNone(host.current_failure(self.run_root, self.host_state, CHECKPOINT))
        (self.run_root / "MAKE-OPTIONS.json").unlink()
        self.assertFalse(host.batch_due(self.run_root, self.host_state, CHECKPOINT))

    def test_a_pass_needs_no_native_turn(self):
        self.assertTrue(host.batch_due(self.run_root, self.host_state, CHECKPOINT))
        attempt, runner = self._run()
        self.assertEqual((attempt["status"], attempt["executor"]), (sb.PASS, "host-batch"))
        self.assertEqual(attempt["proposal_sha256"],
                         hashlib.sha256((self.run_root / host.AGENT_OUTCOME).read_bytes()).hexdigest())
        self.assertNotIn("packet", attempt)
        self.assertFalse(host.batch_due(self.run_root, self.host_state, CHECKPOINT))
        self.assertIsNone(host.current_failure(self.run_root, self.host_state, CHECKPOINT))
        ran = [" ".join(argv) for argv in runner.calls]
        self.assertTrue(ran[0].endswith("--project %s" % (self.run_root / "artifacts/make/r0001/product/cad")))
        self.assertIn("stage_proposal.py", ran[-1])
        self.assertTrue(any("--interface hinge" in line for line in ran))
        self.assertFalse(any("--interface seat" in line for line in ran), "only Coupled Interfaces are checked")
        expected = sb.concept_sha256(SEED_PRODUCT["concept"])
        self.assertTrue(any("--concept-sha256 %s" % expected in line for line in ran))

    def test_the_finalizer_gets_run_relative_paths(self):
        # stage_proposal.py refuses any path argument that is not a safe
        # relative POSIX path, so an absolute --source stopped a passing
        # batch at its last step (Sunset Slider, 2026-11-08).
        _, runner = self._run()
        finalizer = next(argv for argv in runner.calls if any(item.endswith("stage_proposal.py") for item in argv))
        for flag in ("--product-root", "--cad-project-path", "--cad-verification-path", "--source"):
            value = finalizer[finalizer.index(flag) + 1]
            path = PurePosixPath(value)
            self.assertFalse(path.is_absolute(), flag)
            self.assertNotIn("..", path.parts, flag)
            self.assertEqual(path.as_posix(), value, flag)
        self.assertEqual(finalizer[finalizer.index("--source") + 1], host.SOURCE)

    def test_nothing_writes_the_product_tree_after_the_finalizer_seals_it(self):
        # The finalizer seals the product tree's manifest as the batch's last
        # step; a record written into the tree afterwards made the host
        # refuse every proposal (Sunset Slider, 2026-11-08).
        _, runner = self._run()
        self.assertEqual(product_tree(self.run_root), runner.sealed_tree)
        self.assertTrue((self.run_root / host.RUN_RECORD).is_file())
        self.assertFalse((self.run_root / "artifacts/make/r0001/product/cad" / sb.RECORD).exists())

    def test_the_gate_on_a_native_proposal_leaves_the_product_tree_alone(self):
        # A native turn re-finalized the passed bytes: the gate reuses every
        # unchanged check and writes only its record, outside the tree.
        self._run()
        (self.run_root / host.AGENT_OUTCOME).write_text('{"proposal": "repaired"}\n')
        before = product_tree(self.run_root)
        runner = FakeRunner(self.run_root)
        summary = host.gate_proposal(self.run_root, self.host_state, CHECKPOINT, 1, runner=runner)
        self.assertEqual(runner.calls, [], "every unchanged check is reused")
        self.assertEqual(summary["record"], host.RUN_RECORD)
        self.assertEqual(summary["record_sha256"], host._sha256((self.run_root / host.RUN_RECORD).read_bytes()))
        self.assertEqual(product_tree(self.run_root), before)

    def test_a_record_inside_an_older_product_tree_is_still_reused(self):
        self._run()
        legacy = self.run_root / "artifacts/make/r0001/product/cad" / sb.RECORD
        (self.run_root / host.RUN_RECORD).replace(legacy)
        host_attempts = self.host_state / host.ATTEMPTS
        for path in host_attempts.glob("*.json"):
            path.unlink()
        _, runner = self._run()
        record = json.loads((self.run_root / host.RUN_RECORD).read_text())
        self.assertIn(sb.REUSED, {item["status"] for item in record["steps"]})

    def test_a_check_failure_records_the_packet_stage_carries(self):
        attempt, runner = self._run({"part_lid.step.py": RunResult(1, "lid: wall 0.5 mm under the 0.8 mm limit")})
        self.assertEqual(attempt["status"], sb.CHECK_FAILURE)
        packet = host.current_failure(self.run_root, self.host_state, CHECKPOINT)
        self.assertEqual(packet, attempt["packet"])
        self.assertEqual([item["id"] for item in packet["failing"]], ["component:lid"])
        self.assertIn("wall 0.5 mm", packet["failing"][0]["excerpt"])
        self.assertIn("component:body", [item["id"] for item in packet["passed"]])
        self.assertIn("finalizer", packet["skipped"])
        self.assertFalse(host.batch_due(self.run_root, self.host_state, CHECKPOINT),
                         "the native repair turn starts next")
        self.assertFalse(any("stage_proposal.py" in " ".join(argv) for argv in runner.calls))

    def test_a_harness_failure_stops_the_run_and_a_resume_reruns(self):
        with self.assertRaises(host.SeededBatchHarnessFailure) as caught:
            self._run({"check_motion": RunResult(1, "Traceback (most recent call last):\nImportError: libexpat")})
        message = str(caught.exception)
        self.assertIn("no model is asked to repair a tool", message)
        self.assertIn("check-motion", message)
        self.assertIn("workshop resume", message)
        self.assertTrue(host.batch_due(self.run_root, self.host_state, CHECKPOINT))
        self.assertIsNone(host.current_failure(self.run_root, self.host_state, CHECKPOINT))
        attempt, runner = self._run()
        self.assertEqual(attempt["status"], sb.PASS)
        record = json.loads((self.run_root / host.RUN_RECORD).read_text())
        self.assertIn(sb.REUSED, {item["status"] for item in record["steps"]}, "passed steps are reused")

    def test_an_unverified_final_verification_stops_the_run(self):
        """Issue #241: an exit 0 whose report records UNVERIFIED (the shared
        geometry allowance spent) is a harness failure, never a pass, and
        the final step gives its analyses the layer's whole deadline."""
        with self.assertRaises(host.SeededBatchHarnessFailure) as caught:
            self._run(verdict="UNVERIFIED")
        self.assertIn("final-verification", str(caught.exception))
        self.assertTrue(host.batch_due(self.run_root, self.host_state, CHECKPOINT))
        attempt, runner = self._run()
        self.assertEqual(attempt["status"], sb.PASS)
        final = next(argv for argv in runner.calls if "--report" in argv)
        self.assertEqual(final[final.index("--geometry-seconds") + 1], "3300")
        self.assertNotIn("--design", final)
        self.assertNotIn("--contract", final, "in a run WISH.json gives the contract")

    def test_an_assembly_round_that_ran_out_of_time_stops_the_run(self):
        """Issue #244: the round's check_motion took 773 s against make_round's
        600 s. The round now gets the layer's allowance, and a round that
        still runs out records motion unverified: a harness failure, never a
        pass and never a model turn."""
        project = self.run_root / "artifacts/make/r0001/product/cad"

        class TimedOut(FakeRunner):
            def __call__(self, argv, cwd, timeout):
                if "--require-component-passes" in argv:
                    self.calls.append(list(argv))
                    out = project / "measure/rounds/r0001"
                    out.mkdir(parents=True, exist_ok=True)
                    (out / "summary.json").write_text(json.dumps(
                        {"ok": False, "motion_status": "unverified", "geometry_status": "unverified"}))
                    (project / "measure/make-round-state.json").write_text(json.dumps({"last_out": str(out)}))
                    return RunResult(1, "motion unverified")
                return super().__call__(argv, cwd, timeout)

        runner = TimedOut(self.run_root)
        with self.assertRaises(host.SeededBatchHarnessFailure) as caught:
            host.run_for_checkpoint(self.run_root, self.host_state, CHECKPOINT, 1, runner=runner)
        self.assertIn("assembly-round", str(caught.exception))
        self.assertIn("check_motion did not finish", str(caught.exception))
        self.assertIsNone(host.current_failure(self.run_root, self.host_state, CHECKPOINT), "no model turn")
        assembly = next(argv for argv in runner.calls if "--require-component-passes" in argv)
        self.assertEqual(assembly[assembly.index("--geometry-seconds") + 1], "3300")

    def test_the_operators_refresh_rebinds_the_frozen_batch_tool(self):
        """Issue #244: a harness fix to the batch reaches a run only through
        ``workshop resume --refresh-tools``, which rebinds its tool hash."""
        from unittest import mock
        with mock.patch.object(native_run, "native_run_paths"), \
                mock.patch.object(native_run, "_native_run_mutation_lock"), \
                mock.patch.object(native_run, "_open_budgeted_agent_run"), \
                mock.patch.object(native_run, "_refresh_native_run_tools_locked", return_value={}) as locked:
            native_run.refresh_native_run_tools("wish-x", reason="workshop resume --refresh-tools", dry_run=True)
        self.assertEqual(locked.call_args.kwargs["seed_batch_tool_sha256"], sb.module_sha256())

    def test_seed_nonces_are_host_state_the_role_guard_accepts(self):
        self._run()
        table = self.host_state / MAKE_ROUND_GUARD_DIRECTORY / NONCE_TABLE_NAME
        records = [json.loads(line) for line in table.read_text().splitlines()]
        self.assertEqual(sorted(record["component"] for record in records),
                         ["part_body.step.py", "part_lid.step.py"])
        self.assertTrue(all(record["issuer"] == "host-batch" for record in records))
        self.assertEqual(sorted(_issued_seed_nonces(self.host_state).values()),
                         ["part_body.step.py", "part_lid.step.py"])

    def test_another_batch_tool_stops_the_run(self):
        options = json.loads((self.run_root / "MAKE-OPTIONS.json").read_text())
        options["seed"]["batch"]["tool_sha256"] = "0" * 64
        (self.run_root / "MAKE-OPTIONS.json").write_text(json.dumps(options))
        with self.assertRaisesRegex(host.SeededBatchHarnessFailure, "not the one the run froze"):
            self._run()

    def test_the_gate_does_not_rerun_the_proposal_a_pass_finalized(self):
        self._run()
        runner = FakeRunner(self.run_root)
        summary = host.gate_proposal(self.run_root, self.host_state, CHECKPOINT, 1, runner=runner)
        self.assertEqual(runner.calls, [])
        # The Make record shows the host ran the batch and no native turn
        # proposed this Make (ADR 0098).
        attempt = host.read_attempt(self.host_state, CHECKPOINT)
        self.assertEqual((summary["executor"], summary["proposed_by"], summary["gate"]),
                         ("host-batch", "host-batch", host.FINALIZED_BY_BATCH))
        self.assertEqual(summary["record_sha256"], attempt["record_sha256"])

    def test_the_gate_reruns_the_check_layers_on_a_native_proposal(self):
        self._run({"part_lid.step.py": RunResult(1, "lid fails")})
        (self.run_root / host.AGENT_OUTCOME).write_text('{"proposal": "repaired"}\n')
        runner = FakeRunner(self.run_root)
        summary = host.gate_proposal(self.run_root, self.host_state, CHECKPOINT, 1, runner=runner)
        self.assertEqual((summary["executor"], summary["proposed_by"], summary["gate"]),
                         ("host-batch", "native-turn", host.GATED_BY_BATCH))
        record = self.run_root / host.RUN_RECORD
        self.assertEqual(summary["record_sha256"], host._sha256(record.read_bytes()))
        ran = [" ".join(argv) for argv in runner.calls]
        self.assertTrue(any("part_lid.step.py" in line for line in ran))
        self.assertFalse(any("part_body.step.py" in line for line in ran), "an unchanged pass is reused")
        for absent in ("seeded_package", "stage_proposal.py"):
            self.assertFalse(any(absent in line for line in ran), "the gate never re-copies the seed or "
                                                                   "re-finalizes: %s" % absent)

    def test_the_make_receipt_reads_how_the_batch_ran(self):
        """The accepted Make's gate seals the summary among its checks; the
        receipt reads it back, and a Make without one shows none."""
        gates = self.host_state / "gates"
        gates.mkdir(parents=True, exist_ok=True)
        self.assertEqual(native_run._seeded_batch_history(self.host_state), [])
        summary = {"executor": "host-batch", "gate": host.GATED_BY_BATCH, "record_sha256": "a" * 64}
        (gates / "0001-make.json").write_text(json.dumps({"evidence": {"checks": {"seeded_batch": [summary]}}}))
        self.assertEqual(native_run._seeded_batch_history(self.host_state), [summary])

    def test_a_gate_failure_rejects_with_a_fresh_packet(self):
        self._run({"part_lid.step.py": RunResult(1, "lid fails")})
        (self.run_root / host.AGENT_OUTCOME).write_text('{"proposal": "repaired"}\n')
        runner = FakeRunner(self.run_root, {"--interface": RunResult(1, "hinge: lid clashes at 80 deg")})
        with self.assertRaisesRegex(ContractError, "interface:hinge exit 1"):
            host.gate_proposal(self.run_root, self.host_state, CHECKPOINT, 1, runner=runner)
        packet = host.current_failure(self.run_root, self.host_state, CHECKPOINT)
        self.assertEqual([item["id"] for item in packet["failing"]], ["interface:hinge"])
        self.assertIn("clashes at 80 deg", packet["failing"][0]["excerpt"])
        runner = FakeRunner(self.run_root, {"--interface": RunResult(-9, "")})
        with self.assertRaises(host.SeededBatchHarnessFailure):
            host.gate_proposal(self.run_root, self.host_state, CHECKPOINT, 1, runner=runner)

    def test_a_corrupt_attempt_record_is_a_state_conflict(self):
        path = self.host_state / host.ATTEMPTS / ("%s.json" % CHECKPOINT)
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"checkpoint_sha256": "d" * 64}))
        with self.assertRaises(StateConflict):
            host.batch_due(self.run_root, self.host_state, CHECKPOINT)


class BeforeTurnTest(SeededBatchHostTest):
    """The native loop's decision (``_seeded_batch_before_turn``)."""

    def _checkpoint(self, stage="make", effort="spark"):
        return types.SimpleNamespace(stage=stage, effort=effort, checkpoint_sha256=CHECKPOINT, round_index=1)

    def _run_object(self):
        return types.SimpleNamespace(run_root=self.run_root, host_state_root=self.host_state)

    def test_the_native_turn_starts_only_after_a_check_failure(self):
        runner = FakeRunner(self.run_root, {"part_lid.step.py": RunResult(1, "lid fails")})
        self.assertTrue(native_run._seeded_batch_before_turn(self._run_object(), self._checkpoint(), runner=runner))
        self.assertFalse(native_run._seeded_batch_before_turn(self._run_object(), self._checkpoint(), runner=runner))
        self.assertIsNotNone(host.current_failure(self.run_root, self.host_state, CHECKPOINT))

    def test_a_pass_leaves_the_proposal_for_the_gate(self):
        runner = FakeRunner(self.run_root)
        self.assertTrue(native_run._seeded_batch_before_turn(self._run_object(), self._checkpoint(), runner=runner))
        self.assertTrue((self.run_root / host.AGENT_OUTCOME).is_file())
        self.assertIsNone(host.current_failure(self.run_root, self.host_state, CHECKPOINT))

    def test_other_stages_efforts_and_frozen_runs_are_untouched(self):
        runner = FakeRunner(self.run_root)
        for checkpoint in (self._checkpoint(stage="release"), self._checkpoint(effort="forge")):
            self.assertFalse(native_run._seeded_batch_before_turn(self._run_object(), checkpoint, runner=runner))
        self._options(batch=False)
        self.assertFalse(native_run._seeded_batch_before_turn(self._run_object(), self._checkpoint(), runner=runner))
        self.assertEqual(runner.calls, [])

    def test_a_harness_failure_raises_out_of_the_loop(self):
        runner = FakeRunner(self.run_root, {"check_motion": RunResult(None, "", timed_out=True)})
        with self.assertRaises(host.SeededBatchHarnessFailure):
            native_run._seeded_batch_before_turn(self._run_object(), self._checkpoint(), runner=runner)


if __name__ == "__main__":
    unittest.main()
