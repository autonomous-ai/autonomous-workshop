"""ADR 0105: seal_proof records the cadfits fit table the Proof was built
with, and a re-seal keeps the approved table unless the owner ordered a
refit; the host refuses a seed whose table it cannot name.

Contract:
- A seal records ``fit_table``: ``WORKSHOP_FIT_TABLE``, else the current
  table; an unknown name refuses.
- A re-seal under another table than the previous approval's refuses,
  naming the export that re-seals it as approved, unless ``--refit``.
- ``validate_seed`` refuses an approval whose ``fit_table`` is unknown and
  accepts one without the field (sealed before ADR 0105)."""

from __future__ import annotations

import json
import os
import unittest
from unittest import mock

from tests.skills import test_seal_proof as seal_tests
from workshop.errors import ContractError
from workshop.wish import fit_tables
from workshop.wish.seed import validate_seed

ENV = fit_tables.FIT_TABLE_ENV


class SealFitTableTest(unittest.TestCase):
    _record = seal_tests.SealProofTest._record
    _seal = seal_tests.SealProofTest._seal

    def setUp(self):
        seal_tests.SealProofTest.setUp(self)
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(ENV, None)
        self.approval_path = self.proof / "APPROVAL.json"

    def _approval(self):
        return json.loads(self.approval_path.read_text())

    def test_a_seal_records_the_current_table_by_default(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        self.assertEqual(self._approval()["fit_table"], fit_tables.CURRENT)

    def test_a_seal_records_the_pinned_table(self):
        os.environ[ENV] = fit_tables.LEGACY
        self.assertEqual(self._seal(), 0, self.stderr)
        self.assertEqual(self._approval()["fit_table"], fit_tables.LEGACY)

    def test_an_unknown_table_refuses(self):
        os.environ[ENV] = "fits-1999"
        self.assertEqual(self._seal(), 1)
        self.assertIn("names no fit table", self.stderr)
        self.assertFalse(self.approval_path.exists())

    def test_a_reseal_keeps_the_approved_table_unless_the_owner_ordered_a_refit(self):
        os.environ[ENV] = fit_tables.LEGACY
        self.assertEqual(self._seal(), 0, self.stderr)
        sealed = self.approval_path.read_bytes()
        os.environ.pop(ENV)
        self.assertEqual(self._seal(), 1)
        self.assertIn("approved with fit table fits-legacy", self.stderr)
        self.assertIn("WORKSHOP_FIT_TABLE=fits-legacy", self.stderr)
        self.assertEqual(self.approval_path.read_bytes(), sealed)
        self.assertEqual(self._seal("--refit"), 0, self.stderr)
        self.assertEqual(self._approval()["fit_table"], fit_tables.CURRENT)

    def test_an_approval_from_before_the_field_is_placed_by_its_lock(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        approval = self._approval()
        del approval["fit_table"]
        approval["skills_lock_sha256"] = "d7" * 32
        self.approval_path.write_text(json.dumps(approval))
        self.assertEqual(self._seal(), 1)
        self.assertIn("approved with fit table fits-legacy", self.stderr)
        os.environ[ENV] = fit_tables.LEGACY
        self.assertEqual(self._seal(), 0, self.stderr)


class SeedFitTableTest(unittest.TestCase):
    _record = seal_tests.SealProofTest._record
    _seal = seal_tests.SealProofTest._seal

    def setUp(self):
        seal_tests.SealProofTest.setUp(self)
        os.environ.pop(ENV, None)
        self.assertEqual(self._seal(), 0, self.stderr)
        self.approval_path = self.proof / "APPROVAL.json"

    def _with(self, change):
        approval = json.loads(self.approval_path.read_text())
        change(approval)
        self.approval_path.write_text(json.dumps(approval))
        return validate_seed(self.proof, ("body",), seal_tests.sha(self.contract))

    def test_a_known_or_absent_table_seeds(self):
        self._with(lambda a: a.update(fit_table=fit_tables.LEGACY))
        self._with(lambda a: a.pop("fit_table"))

    def test_an_unknown_table_cannot_seed(self):
        with self.assertRaises(ContractError) as caught:
            self._with(lambda a: a.update(fit_table="fits-1999"))
        self.assertIn("seed: APPROVAL.json fit_table 'fits-1999' names no fit table", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
