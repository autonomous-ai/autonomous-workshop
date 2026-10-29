"""ADR 0095: make_round's final run names the verifier's power class.

verify_project refuses an image-derived final run that is neither
``--powered`` nor ``--unpowered``; a schema 10 contract that states a
circuit is always powered, so the verifier refuses it without its report."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.make.test_make_round import load_module
from tests.wish.test_electrical import _electrical

make_round = load_module()


class PowerOptionsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        (self.project / "measure").mkdir()

    def options(self, contract, image_derived=True):
        with mock.patch.object(make_round, "sealed_contract", return_value=contract):
            return make_round.power_options(self.project, image_derived)

    def test_a_stated_circuit_always_runs_the_powered_gate(self):
        powered = {"schema_version": 10, "electrical": _electrical()}
        self.assertEqual(self.options(powered), ["--powered"])
        self.assertEqual(self.options(powered, image_derived=False), ["--powered"])

    def test_an_image_derived_run_without_a_circuit_names_its_class(self):
        self.assertEqual(self.options({"schema_version": 9}), ["--unpowered"])
        # A schema 7-9 lamp kit whose Make wrote a power report.
        (self.project / "measure" / "power.json").write_text("{}")
        self.assertEqual(self.options({"schema_version": 9}), ["--powered"])

    def test_a_circuit_before_schema_10_is_not_read(self):
        self.assertEqual(self.options({"schema_version": 9, "electrical": _electrical()}), ["--unpowered"])

    def test_a_run_outside_contract_mode_passes_nothing(self):
        self.assertEqual(self.options(None, image_derived=False), [])


if __name__ == "__main__":
    unittest.main()
