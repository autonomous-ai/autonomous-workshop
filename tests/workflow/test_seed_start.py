"""ADR 0096: the host revalidates the seed before a seeded run starts.

Contract: `_seed_start_inputs` returns the frozen seed and its files for a
seed directory that validates against the sealed contract and is the one the
Wish records. It refuses a seed the Wish does not record (or a recorded seed
with no directory), a schema 11 contract without a seed, a seed without a
contract, a workflow other than spark, a Wish objective that is not the
contract the seed was approved for, and a directory other than the recorded
one."""

from __future__ import annotations

import json
import unittest

from tests.skills import test_seal_proof as seal_tests
from workshop.errors import ContractError
from workshop.wish.contracts import Wish
from workshop.wish.seed import seed_context, validate_seed
from workshop.workflow.effort import workshop_effort
import hashlib
import tempfile
from pathlib import Path

from workshop.errors import StateConflict
from workshop.make import seeded_batch
from workshop.workflow.native_run import (_sealed_seed, _sealed_seed_assembly_renders, _sealed_seed_components,
                                          _sealed_seed_contract_images,
                                          _seed_start_inputs)


class SeedStartTest(unittest.TestCase):
    _record = seal_tests.SealProofTest._record
    _seal = seal_tests.SealProofTest._seal

    def setUp(self):
        seal_tests.SealProofTest.setUp(self)
        self.assertEqual(self._seal(), 0, self.stderr)
        self.text = self.contract.read_text()
        self.digest = seal_tests.sha(self.contract)
        self.design = {"schema_version": 11, "shape": "approved-proof", "geometries": [{"id": "body"}]}
        self.recorded = seed_context(validate_seed(self.proof, ("body",), self.digest), self.digest)

    def _wish(self, objective=None, **context):
        context.setdefault("design_contract", self.design)
        context.setdefault("seed", self.recorded)
        context = {key: value for key, value in context.items() if value is not None}
        return Wish.create("wish-seed-1", objective or self.text, context=context)

    def _start(self, wish, source="proof", effort="spark", snapshot=None):
        return _seed_start_inputs(wish, self.proof if source == "proof" else source,
                                  workshop_effort(effort) if effort else None, snapshot)

    def _refused(self, fragment, *args, **kwargs):
        with self.assertRaises(ContractError) as caught:
            self._start(*args, **kwargs)
        self.assertIn(fragment, str(caught.exception))

    def test_a_recorded_seed_starts_with_its_files(self):
        seed, files = self._start(self._wish())
        approval = (self.proof / "APPROVAL.json").read_bytes()
        # ADR 0098: a new launch freezes the seeded batch tool with the seed,
        # and ADR 0102 its review of a visible deviation against the Proof.
        self.assertEqual(seed, {**{key: self.recorded[key] for key in ("approval_sha256", "manifest_sha256")},
                                "batch": {"tool_sha256": seeded_batch.module_sha256()},
                                "review": "approved-proof"})
        self.assertEqual(files["APPROVAL.json"], approval)
        self.assertEqual(set(files) - {"APPROVAL.json"}, set(json.loads(approval)["manifest"]))
        # No effort given means the default, spark.
        self.assertEqual(self._start(self._wish(), effort=None)[0], seed)

    def test_an_unseeded_run_has_no_seed_inputs(self):
        design = {"schema_version": 10, "geometries": [{"id": "body"}]}
        self.assertEqual(self._start(self._wish(design_contract=design, seed=None), source=None), (None, None))

    def test_a_seed_and_its_record_come_together(self):
        self._refused("records a seed but no --seed-source", self._wish(), source=None)
        self._refused("seals only with --seed-source", self._wish(seed=None), source=None)
        self._refused("does not record the seed", self._wish(seed=None))
        self._refused("does not record the seed", self._wish(seed=dict(self.recorded, extra="x")))

    def test_a_new_launch_refuses_a_seed_sealed_before_adr_0098(self):
        approval = json.loads((self.proof / "APPROVAL.json").read_text())
        approval["schema_version"] = 1
        del approval["check_inputs"], approval["batch"]
        (self.proof / "APPROVAL.json").write_text(json.dumps(approval))
        self._refused("sealed before ADR 0098", self._wish())
        self._refused("Re-seal it through design-a-toy", self._wish())

    def test_a_new_launch_reads_the_sealed_contract_for_its_inputs(self):
        moving = dict(self.design, interfaces=[{"id": "lid", "kind": "coupled"}])
        self._refused("does not record the check inputs its contract needs: measure/motion.json",
                      self._wish(design_contract=moving))

    def test_spark_only(self):
        self._refused("only the spark workflow", self._wish(), effort="forge")

    def test_the_objective_must_be_the_approved_contract(self):
        named = "Name this toy exactly: Beaver v01.\n" + self.text
        self.assertIsNotNone(self._start(self._wish(objective=named))[0])
        self._refused("another contract than the sealed objective", self._wish(objective=self.text + "\nmore"))
        # A correction's objective is its prompt; the seed binds the contract hash it records.
        self.assertIsNotNone(self._start(self._wish(objective="fix the lid"), snapshot=b"snapshot")[0])

    def test_the_directory_must_be_the_recorded_one(self):
        self._refused("not the one the Wish records",
                      self._wish(seed=dict(self.recorded, approved_by="someone else")))
        self._refused("not the one the Wish records",
                      self._wish(seed=dict(self.recorded, manifest_sha256="0" * 64)))
        (self.proof / "params.py").write_text("PEG_D = 9\n")
        self._refused("changed file(s)", self._wish())


    def test_the_receipt_reads_the_seed_the_wish_sealed(self):
        from workshop.workflow.native_run import canonical_wish_bytes

        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            content = canonical_wish_bytes(self._wish())
            (root / "WISH.json").write_bytes(content)
            self.assertEqual(_sealed_seed(root, hashlib.sha256(content).hexdigest()), self.recorded)
            with self.assertRaises(StateConflict):
                _sealed_seed(root, "0" * 64)
            plain = canonical_wish_bytes(self._wish(seed=None))
            (root / "WISH.json").write_bytes(plain)
            self.assertIsNone(_sealed_seed(root, hashlib.sha256(plain).hexdigest()))
            self.assertIsNone(_sealed_seed(root / "missing", "0" * 64))


    def test_the_host_reads_the_frozen_approvals_components(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.assertIsNone(_sealed_seed_components(root))
            (root / "MAKE-OPTIONS.json").write_text('{"check_motion":false,"schema_version":1}')
            self.assertIsNone(_sealed_seed_components(root))
            approval = (self.proof / "APPROVAL.json").read_bytes()
            frozen = {"approval_sha256": hashlib.sha256(approval).hexdigest(), "manifest_sha256": "a" * 64}
            (root / "MAKE-OPTIONS.json").write_text(json.dumps({"schema_version": 3, "check_motion": False,
                                                                 "seed": frozen}))
            with self.assertRaisesRegex(StateConflict, "missing"):
                _sealed_seed_components(root)
            (root / "seed").mkdir()
            (root / "seed/APPROVAL.json").write_bytes(approval)
            self.assertEqual(set(_sealed_seed_components(root)), {"body"})
            # ADR 0103: a schema 4 seal's contract images reach the host's
            # check; it has no assembly renders, and an older seal has neither.
            self.assertEqual(_sealed_seed_contract_images(root), json.loads(approval)["contract_images"])
            self.assertIsNone(_sealed_seed_assembly_renders(root))
            older = json.loads(approval)
            older.pop("contract_images")
            older_bytes = json.dumps(older).encode()
            (root / "MAKE-OPTIONS.json").write_text(json.dumps({"schema_version": 3, "check_motion": False, "seed": {
                **frozen, "approval_sha256": hashlib.sha256(older_bytes).hexdigest()}}))
            (root / "seed/APPROVAL.json").write_bytes(older_bytes)
            self.assertIsNone(_sealed_seed_assembly_renders(root))
            self.assertIsNone(_sealed_seed_contract_images(root))
            (root / "MAKE-OPTIONS.json").write_text(json.dumps({"schema_version": 3, "check_motion": False,
                                                                 "seed": frozen}))
            (root / "seed/APPROVAL.json").write_bytes(approval + b" ")
            with self.assertRaisesRegex(StateConflict, "not the frozen one"):
                _sealed_seed_components(root)


if __name__ == "__main__":
    unittest.main()
