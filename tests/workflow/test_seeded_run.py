"""ADR 0096: a seeded Wish starts one native run with the Approved Proof
sealed under seed/, and every resume keeps it.

Contract: `start_native_run(seed_source=)` materializes the seed's approval
and manifest files read-only under the run's `seed/`, freezes both hashes in
`MAKE-OPTIONS.json` schema 3, and puts `seed` in its receipt. A resume that
changes the motion policy keeps the seed. A seed directory that no longer
matches what the Wish records refuses before any run exists."""

from __future__ import annotations

import hashlib
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
from workshop.make.make_round_guard import BOUNDARY_LOG_NAME
from workshop.make.role_guard import MAKE_ROUND_GUARD_DIRECTORY
from workshop.wish import Wish
from workshop.make import seeded_batch
from workshop.wish.seed import seed_context, validate_seed
from workshop.workflow import seeded_batch_host
import workshop.workflow.native_run as host
from workshop.workflow.agent_run import frozen_seed_review


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
        frozen["batch"] = {"tool_sha256": seeded_batch.module_sha256()}
        # ADR 0102: a new run reviews a visible deviation against the Proof.
        frozen["review"] = "approved-proof"
        options = json.loads((workspace / "MAKE-OPTIONS.json").read_bytes())
        self.assertEqual((options["schema_version"], options["seed"]), (5, frozen))
        self.assertEqual(frozen_seed_review(workspace), "approved-proof")
        self.assertEqual(receipt["seed"], self.recorded)
        # No Make has been accepted yet, so no deviation is recorded.
        self.assertEqual(receipt["seed_deviations"], [])
        host.resume_native_run(self.product_id, check_motion=True)
        options = json.loads((workspace / "MAKE-OPTIONS.json").read_bytes())
        self.assertEqual((options["check_motion"], options["seed"]), (True, frozen))
        self.assertEqual(len(self.launcher.starts), 1)

    def test_a_run_started_before_adr_0098_resumes_with_its_frozen_rules(self):
        # Owner decision 2: the refusal is for new launches only. A run whose
        # seed predates ADR 0098 (schema 1 approval, MAKE-OPTIONS schema 3, no
        # batch) resumes, never revalidates its seed and never gains a batch.
        approval = json.loads((self.proof / "APPROVAL.json").read_text())
        approval["schema_version"] = 1
        del approval["check_inputs"], approval["batch"]
        legacy = json.dumps(approval).encode()
        files = {"APPROVAL.json": legacy, **{name: (self.proof / name).read_bytes() for name in approval["manifest"]}}
        frozen = {"approval_sha256": hashlib.sha256(legacy).hexdigest(),
                  "manifest_sha256": approval["manifest_sha256"]}
        with mock.patch.object(host, "_seed_start_inputs", return_value=(frozen, files)):
            host.start_native_run(self.wish, seed_source=self.proof)
        workspace = host.native_run_paths(self.product_id).workspace
        options = json.loads((workspace / "MAKE-OPTIONS.json").read_bytes())
        self.assertEqual((options["schema_version"], options["seed"]), (3, frozen))
        with mock.patch("workshop.wish.seed.validate_seed", side_effect=AssertionError("resume revalidated")):
            host.resume_native_run(self.product_id, check_motion=True)
        options = json.loads((workspace / "MAKE-OPTIONS.json").read_bytes())
        self.assertEqual((options["schema_version"], options["seed"]), (3, frozen))
        paths = host.native_run_paths(self.product_id)
        self.assertFalse(seeded_batch_host.batch_due(paths.workspace, paths.host_state, "0" * 64))

    def test_a_run_started_before_adr_0102_keeps_its_review_against_references(self):
        # A run that froze MAKE-OPTIONS schema 4 (seed with batch, no review)
        # resumes with the same options and never gains the Proof review.
        frozen = {key: self.recorded[key] for key in ("approval_sha256", "manifest_sha256")}
        frozen["batch"] = {"tool_sha256": seeded_batch.module_sha256()}
        files = {"APPROVAL.json": (self.proof / "APPROVAL.json").read_bytes(),
                 **{name: (self.proof / name).read_bytes()
                    for name in json.loads((self.proof / "APPROVAL.json").read_bytes())["manifest"]}}
        with mock.patch.object(host, "_seed_start_inputs", return_value=(frozen, files)):
            host.start_native_run(self.wish, seed_source=self.proof)
        workspace = host.native_run_paths(self.product_id).workspace
        host.resume_native_run(self.product_id, check_motion=True)
        options = json.loads((workspace / "MAKE-OPTIONS.json").read_bytes())
        self.assertEqual((options["schema_version"], options["seed"]), (4, frozen))
        self.assertIsNone(frozen_seed_review(workspace))

    def test_the_receipt_reports_run_boundary_refusals(self):
        # ADR 0096 pilot (B7, B8): a refusal the guard logged reaches the receipt.
        receipt = host.start_native_run(self.wish, seed_source=self.proof)
        self.assertNotIn("boundary_refusals", receipt)
        paths = host.native_run_paths(self.product_id)
        log = paths.host_state / MAKE_ROUND_GUARD_DIRECTORY / BOUNDARY_LOG_NAME
        if not log.parent.is_dir():
            self.skipTest("this launcher installs no make_round guard")
        records = [{"tool": "Bash", "reason": "never install %d" % index} for index in range(7)]
        log.write_text("".join(json.dumps(record) + "\n" for record in records))
        receipt = host.resume_native_run(self.product_id, check_motion=True)
        self.assertEqual(receipt["boundary_refusals"], {"count": 7, "recent": records[-5:]})

    def test_a_changed_seed_refuses_before_any_run(self):
        (self.proof / "params.py").write_text("PEG_D = 9\n")
        with self.assertRaises(ContractError):
            host.start_native_run(self.wish, seed_source=self.proof)
        with self.assertRaises(StateConflict):
            host.native_run_paths(self.product_id)
        self.assertEqual(self.launcher.starts, [])


if __name__ == "__main__":
    unittest.main()
