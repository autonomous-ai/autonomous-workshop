"""ADR 0096: a seeded Wish starts one native run with the Approved Proof
sealed under seed/, and every resume keeps it.

Contract: `start_native_run(seed_source=)` materializes the seed's approval
and manifest files read-only under the run's `seed/`, freezes both hashes in
`MAKE-OPTIONS.json` schema 3, and puts `seed` in its receipt. A resume that
changes the motion policy keeps the seed. A seed directory that no longer
matches what the Wish records refuses before any run exists."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.invent.fake_gamevault import install_fake_gamevault
from tests.skills import test_seal_proof as seal_tests
from tests.workflow.test_resume_motion import MotionLauncher
from workshop.errors import ContractError, StateConflict
from workshop.wish import Wish
from workshop.wish.seed import seed_context, validate_seed
import workshop.workflow.native_run as host


class SeededRunTest(unittest.TestCase):
    _record = seal_tests.SealProofTest._record
    _seal = seal_tests.SealProofTest._seal

    def setUp(self):
        seal_tests.SealProofTest.setUp(self)
        self.assertEqual(self._seal(), 0, self.stderr)
        install_fake_gamevault(self)
        home = str(Path(self.enterContext(tempfile.TemporaryDirectory())).resolve())
        self.enterContext(mock.patch.dict(os.environ, {"WORKSHOP_HOME": home}, clear=True))
        self.enterContext(mock.patch.object(host, "_source_checkout_root", return_value=None))
        self.launcher = MotionLauncher()
        self.enterContext(mock.patch.object(host, "CodexNativeSessionLauncher", return_value=self.launcher))
        self.product_id = "seeded-run-fixture"
        digest = seal_tests.sha(self.contract)
        self.recorded = seed_context(validate_seed(self.proof, ("body",), digest), digest)
        self.wish = Wish.create(self.product_id, self.contract.read_text(), context={
            "design_contract": {"schema_version": 11, "shape": "approved-proof",
                                "geometries": [{"id": "body"}]},
            "seed": self.recorded,
        })

    def test_the_seed_is_sealed_frozen_and_kept_by_a_resume(self):
        receipt = host.start_native_run(self.wish, seed_source=self.proof)
        workspace = host.native_run_paths(self.product_id).workspace
        approval = (self.proof / "APPROVAL.json").read_bytes()
        self.assertEqual((workspace / "seed/APPROVAL.json").read_bytes(), approval)
        for name in json.loads(approval)["manifest"]:
            self.assertEqual((workspace / "seed" / name).read_bytes(), (self.proof / name).read_bytes())
        frozen = {key: self.recorded[key] for key in ("approval_sha256", "manifest_sha256")}
        options = json.loads((workspace / "MAKE-OPTIONS.json").read_bytes())
        self.assertEqual((options["schema_version"], options["seed"]), (3, frozen))
        self.assertEqual(receipt["seed"], self.recorded)
        # No Make has been accepted yet, so no deviation is recorded.
        self.assertEqual(receipt["seed_deviations"], [])
        host.resume_native_run(self.product_id, check_motion=True)
        options = json.loads((workspace / "MAKE-OPTIONS.json").read_bytes())
        self.assertEqual((options["check_motion"], options["seed"]), (True, frozen))
        self.assertEqual(len(self.launcher.starts), 1)

    def test_a_changed_seed_refuses_before_any_run(self):
        (self.proof / "params.py").write_text("PEG_D = 9\n")
        with self.assertRaises(ContractError):
            host.start_native_run(self.wish, seed_source=self.proof)
        with self.assertRaises(StateConflict):
            host.native_run_paths(self.product_id)
        self.assertEqual(self.launcher.starts, [])


if __name__ == "__main__":
    unittest.main()
