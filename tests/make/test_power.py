"""ADR 0095: before Make is accepted the host checks that a schema 10 toy's
power report is the sealed circuit and that final verification passed
check_power on it, on the exact sealed bytes and without rerunning the gate."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import types
import unittest

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ContractError
from workshop.make.power import check_power_report, has_electrical, verify_made_power
from tests.wish.test_electrical import _electrical

PRODUCT = "artifacts/make/r0001/product"


def power_report():
    """A check_power schema 3 report of the Mac fidget's circuit, two wires
    on its path; evidence and mounts are check_power's to judge."""

    def component(identifier, role, **fields):
        return {"id": identifier, "role": role, **fields}

    return {
        "schema_version": 3,
        "components": [
            component("cells", "source", voltage_v={"min": 2.0, "max": 3.3}),
            component("plate", "connector"), component("spring", "connector"),
            component("bridge", "connector"), component("switch", "switch"),
            component("resistor", "controller"), component("led", "load", load_type="lighting"),
            component("wire-a", "wire"), component("wire-b", "wire"),
        ],
        "paths": [{
            "id": "screen-light", "source": "cells", "load": "led",
            "sequence": ["cells", "plate", "wire-a", "switch", "resistor", "led", "wire-b", "spring",
                         "bridge", "cells"],
            "required_continuous_current_a": 0.0127, "required_peak_current_a": 0.02,
        }],
    }


def pipeline(status="rc=0", note=False):
    rows = ["| 1 | `/v/bin/python /r/skills/cad/scripts/gen mac/mac.step.py --write --json` | rc=0 | 1.00 |",
            "| 2 | `/v/bin/python /r/skills/electromechanical-integration/scripts/check_power mac "
            "--manifest mac/measure/power.json` | %s | 0.10 |" % status]
    if note:
        rows.append("| 3 | `check_power  # NOTE: mating interface door: fit coupon is planned` | note | 0.00 |")
    return "# Verification pipeline record\n\n| # | command | status | s |\n|---|---|---|---|\n%s\n" % "\n".join(rows)


class PowerReportTest(unittest.TestCase):
    def test_the_report_of_the_sealed_circuit_matches(self):
        self.assertEqual(check_power_report(_electrical(), power_report()), [])

    def test_every_difference_from_the_circuit_is_named(self):
        report = power_report()
        report["components"] = [item for item in report["components"] if item["id"] != "resistor"]
        report["components"][4]["role"] = "load"
        report["paths"][0]["sequence"].remove("resistor")
        report["paths"][0]["required_continuous_current_a"] = 0.005
        report["components"][0]["voltage_v"] = {"min": 2.6, "max": 3.3}
        problems = "\n".join(check_power_report(_electrical(), report))
        self.assertIn("the contract's controller resistor is no report component", problems)
        self.assertIn("report component switch is a load, not the contract's switch", problems)
        self.assertIn("wires left out, is ['cells', 'plate', 'switch', 'led'", problems)
        self.assertIn("required_continuous_current_a is 0.005 A, below the contract's 12.7 mA", problems)
        self.assertIn("does not cover the contract's supply 2.4-3.2 V", problems)

    def test_a_missing_path_wire_or_other_report_is_refused(self):
        report = power_report()
        report["components"] = [item for item in report["components"] if item["role"] != "wire"]
        report["paths"][0]["id"] = "other"
        problems = "\n".join(check_power_report(_electrical(), report))
        self.assertIn("buys wire wire, but the report has no wire component", problems)
        self.assertIn("the contract's path screen-light is no report path", problems)
        self.assertEqual(check_power_report(_electrical(), {"schema_version": 1}),
                         ["measure/power.json is not a schema 2 or 3 power report"])

    def test_only_a_schema_10_contract_states_a_circuit(self):
        self.assertTrue(has_electrical({"schema_version": 10, "electrical": _electrical()}))
        self.assertFalse(has_electrical({"schema_version": 9, "electrical": _electrical()}))
        self.assertFalse(has_electrical({"schema_version": 10}))
        self.assertFalse(has_electrical(None))


class MadePowerTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name)
        self.cad = self.run_root / PRODUCT / "cad"
        (self.cad / "measure").mkdir(parents=True)
        self.contract = {"schema_version": 10, "electrical": _electrical()}
        self.write("measure/power.json", json.dumps(power_report()))
        self.write("measure/verification-pipeline.md", pipeline())

    def write(self, relative, text):
        (self.cad / relative).write_text(text)

    def made(self):
        manifest = build_artifact_manifest(self.run_root / PRODUCT, created_at="content-addressed")
        return types.SimpleNamespace(product_root=PRODUCT, cad_project_path="cad", product_manifest=manifest)

    def refused(self, made=None):
        with self.assertRaises(ContractError) as caught:
            verify_made_power(self.run_root, made or self.made(), self.contract)
        return str(caught.exception)

    def test_a_matching_report_that_passed_check_power_is_accepted(self):
        account = verify_made_power(self.run_root, self.made(), self.contract)
        self.assertEqual(account["report"], "cad/measure/power.json")
        self.assertEqual(len(account["report_sha256"]), 64)
        self.assertEqual(account["paths"], [{"id": "screen-light", "load": "led", "current_ma": 12.7}])
        self.assertEqual((account["assembled_by"], account["joins"], account["runtime_h"]), ("maker", "solder", 60))

    def test_an_unpowered_contract_is_not_checked(self):
        (self.cad / "measure" / "power.json").unlink()
        self.assertIsNone(verify_made_power(self.run_root, self.made(), {"schema_version": 9}))

    def test_a_planned_fit_coupon_note_is_no_failed_gate(self):
        self.write("measure/verification-pipeline.md", pipeline(note=True))
        self.assertIsNotNone(verify_made_power(self.run_root, self.made(), self.contract))

    def test_a_missing_report_or_record_is_refused(self):
        (self.cad / "measure" / "power.json").unlink()
        self.assertIn("lacks its power report, measure/power.json", self.refused())
        self.write("measure/power.json", json.dumps(power_report()))
        (self.cad / "measure" / "verification-pipeline.md").unlink()
        self.assertIn("lacks its final pipeline record", self.refused())

    def test_a_failed_skipped_or_absent_gate_is_refused(self):
        for status in ("rc=1", "skipped"):
            self.write("measure/verification-pipeline.md", pipeline(status))
            self.assertIn("did not pass check_power", self.refused())
        self.write("measure/verification-pipeline.md", pipeline().replace("check_power", "check_mount"))
        self.assertIn("did not pass check_power", self.refused())

    def test_bytes_that_differ_from_the_manifest_are_refused(self):
        made = self.made()
        report = power_report()
        report["components"][0]["voltage_v"]["min"] = 1.0
        self.write("measure/power.json", json.dumps(report))
        self.assertIn("differs from the Made manifest", self.refused(made))

    def test_a_report_of_another_circuit_is_refused(self):
        report = copy.deepcopy(power_report())
        report["paths"][0]["load"] = "switch"
        self.write("measure/power.json", json.dumps(report))
        self.assertIn("the power report is not the sealed circuit: report path screen-light runs cells to switch",
                      self.refused())
        self.write("measure/power.json", "{not json")
        self.assertIn("measure/power.json is not JSON", self.refused())


if __name__ == "__main__":
    unittest.main()
