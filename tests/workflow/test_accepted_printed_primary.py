"""ADR 0095 amendment (2026-11-07): Release reads the printed-only primary
from the Make gate receipt the host sealed, and nothing else."""

import json
import tempfile
import types
import unittest
from pathlib import Path

from workshop.errors import StateConflict
from workshop.workflow.native_run import _accepted_printed_primary

RECORD = {"path": "cad/measure/electrical/printed.step", "sha256": "a" * 64,
          "scene_path": "assembled.step", "scene_sha256": "b" * 64,
          "removed": ["bought_led"], "printed_bodies": 1, "removed_bodies": 1}


class AcceptedPrintedPrimaryTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.root)
        self.run_ = types.SimpleNamespace(host_state_root=self.root)

    def receipt(self, name, checks):
        gates = self.root / "gates"
        gates.mkdir(exist_ok=True)
        (gates / name).write_text(json.dumps({"evidence": {"checks": checks}}))

    def test_the_latest_make_receipt_names_the_primary(self):
        self.receipt("001-make.json", {"bought_model": [{"bodies": "x"}]})
        self.receipt("002-make.json", {"bought_model": [{"bodies": "x", "printed_primary": RECORD}]})
        self.assertEqual(_accepted_printed_primary(self.run_), RECORD)

    def test_a_run_that_sealed_none_ships_its_scene(self):
        self.assertIsNone(_accepted_printed_primary(self.run_))
        self.receipt("001-make.json", {"bought_model": [{"printed_primary": RECORD}]})
        self.receipt("002-make.json", {"bought_model": [{"bodies": "x"}]})
        self.assertIsNone(_accepted_printed_primary(self.run_), "only the latest acceptance counts")
        self.receipt("003-make.json", {})
        self.assertIsNone(_accepted_printed_primary(self.run_))

    def test_an_unreadable_receipt_stops_the_release(self):
        self.receipt("001-make.json", {"bought_model": {"printed_primary": RECORD}})
        with self.assertRaises(StateConflict):
            _accepted_printed_primary(self.run_)


if __name__ == "__main__":
    unittest.main()
