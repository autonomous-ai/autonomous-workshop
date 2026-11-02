"""ADR 0096: `workshop wish|fix --seed-source DIR` validates the Approved
Proof before any run starts.

Contract: both commands accept `--seed-source`. `_load_seed` returns what the
Wish context records (both hashes, the contract's sha256 of its bytes, who
approved it and when) for a directory sealed for that contract, and refuses
a schema 11 contract without a seed, a seed without a contract, a workflow
other than spark, a contract file that is not UTF-8 with LF line endings,
and a seed sealed for another contract."""

from __future__ import annotations

import argparse
import unittest

from cli.main import _load_seed, parser
from tests.skills import test_seal_proof as seal_tests
from workshop.errors import ContractError, WorkshopError


class SeedSourceTest(unittest.TestCase):
    _record = seal_tests.SealProofTest._record
    _seal = seal_tests.SealProofTest._seal

    def setUp(self):
        seal_tests.SealProofTest.setUp(self)
        self.assertEqual(self._seal(), 0, self.stderr)
        self.design = {"schema_version": 11, "shape": "approved-proof", "geometries": [{"id": "body"}]}

    def _args(self, **values):
        values.setdefault("seed_source", self.proof)
        values.setdefault("contract", self.contract)
        values.setdefault("workflow", "spark")
        return argparse.Namespace(**values)

    def test_both_commands_take_the_option(self):
        for command in (["wish", "--contract", "C.md"], ["fix", "toy", "--prompt", "fix it"]):
            args = parser().parse_args([*command, "--seed-source", "proof"])
            self.assertEqual(str(args.seed_source), "proof")

    def test_a_sealed_seed_is_recorded(self):
        recorded = _load_seed(self._args(), self.design)
        self.assertEqual(recorded["contract_sha256"], seal_tests.sha(self.contract))
        self.assertEqual(recorded["approval_sha256"], seal_tests.sha(self.proof / "APPROVAL.json"))
        self.assertEqual((recorded["approved_by"], recorded["date"]), ("owner", "2026-11-02"))
        self.assertEqual(set(recorded), {"approval_sha256", "manifest_sha256", "contract_sha256",
                                         "approved_by", "date"})

    def test_no_seed_for_an_ordinary_contract(self):
        self.assertIsNone(_load_seed(self._args(seed_source=None), {"schema_version": 10}))
        self.assertIsNone(_load_seed(self._args(seed_source=None), None))

    def test_refusals(self):
        with self.assertRaisesRegex(WorkshopError, "pass --seed-source DIR"):
            _load_seed(self._args(seed_source=None), self.design)
        with self.assertRaisesRegex(WorkshopError, "pass --contract FILE too"):
            _load_seed(self._args(), None)
        with self.assertRaisesRegex(WorkshopError, "only the spark workflow"):
            _load_seed(self._args(workflow="forge"), self.design)

    def test_a_crlf_contract_is_refused(self):
        self.contract.write_bytes(self.contract.read_bytes().replace(b"\n", b"\r\n"))
        with self.assertRaisesRegex(WorkshopError, "LF line endings"):
            _load_seed(self._args(), self.design)

    def test_the_receipt_prints_the_seed(self):
        from contextlib import redirect_stdout
        from io import StringIO

        from cli.main import _print_native_receipt
        from tests.cli.test_cli import native_receipt

        seed = {"approval_sha256": "a" * 64, "approved_by": "owner", "date": "2026-11-02"}
        stdout = StringIO()
        with redirect_stdout(stdout):
            _print_native_receipt({**native_receipt(status="complete", stage="release"), "seed": seed,
                                   "seed_deviations": [{"component": "lid", "within_tolerance": False,
                                                        "locked_by": "component-review"}]},
                                  verb="Run")
        self.assertIn("Seed deviation: lid over tolerance against the Approved Proof; locked by its "
                      "Component Review", stdout.getvalue())
        self.assertIn("Seed: the Approved Proof approved by owner on 2026-11-02 (approval aaaaaaaaaaaa)",
                      stdout.getvalue())

    def test_a_seed_for_another_contract_is_refused(self):
        self.contract.write_text(self.contract.read_text() + "\nchanged\n")
        with self.assertRaisesRegex(ContractError, "sealed for another contract"):
            _load_seed(self._args(), self.design)


if __name__ == "__main__":
    unittest.main()
