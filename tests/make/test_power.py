"""ADR 0095: before Make is accepted the host checks that a schema 10 toy's
power report is the sealed circuit and that final verification passed
check_power on it, on the exact sealed bytes and without rerunning the gate."""
from __future__ import annotations

import copy
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ContractError
from workshop.make.power import check_power_report, has_electrical, verify_made_power
from tests.wish.test_electrical import _electrical, _mac_usb

CHECK_POWER = (Path(__file__).resolve().parents[2] / "src/workshop/make/skills/electromechanical-integration"
               / "scripts/check_power")

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
        self.assertEqual((account["boundary"], account["parts"]), ("onboard", 8))

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


def _check_power():
    """The vendored check_power script as a module."""

    loader = importlib.machinery.SourceFileLoader("vendored_check_power", str(CHECK_POWER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def usb_power_report():
    """A complete check_power schema 3 report of the USB Mac fidget: the
    buyer's charger a non-carried source behind a carried USB-C inlet
    (check_power's ``external`` boundary), every other part carried and
    mounted, one wire pair per path, and two paths to each warm LED."""

    evidence = {"kind": "manufacturer_datasheet", "url": "https://manufacturer.example/data.pdf"}
    electrical = _mac_usb()
    components, mounts = [], set()
    for item in electrical["parts"]:
        if item["role"] == "wire":
            continue
        component = {"id": item["id"], "role": item["role"], "evidence": evidence,
                     "voltage_v": {"min": 0.0, "max": 30.0}, "continuous_current_a": 1.0,
                     "peak_current_a": 1.0}
        if item.get("external"):
            component.update(carried=False, voltage_v={"min": 4.4, "max": 5.25})
        else:
            component.update(carried=True, mount_id="%s-mount" % item["id"],
                             cad={"mode": "validation_envelope", "rendered": False,
                                  "source": "ref/validation/%s.step" % item["id"]})
            mounts.add("%s-mount" % item["id"])
        if item["role"] == "load":
            component.update(load_type="lighting", continuous_current_a=0.03, peak_current_a=0.03,
                             lighting={"function": "night light", "color": "warm white",
                                       "behavior": "steady", "installation": {"mode": "soldered"}})
        components.append(component)
    paths = []
    for path in electrical["paths"]:
        out, back = "%s-out" % path["id"], "%s-back" % path["id"]
        for wire in (out, back):
            components.append({"id": wire, "role": "wire", "evidence": evidence, "carried": True,
                               "mount_id": wire, "continuous_current_a": 1.0, "peak_current_a": 1.0,
                               "cad": {"mode": "validation_envelope", "rendered": False,
                                       "source": "ref/validation/%s.step" % wire}})
            mounts.add(wire)
        sequence = list(path["sequence"])
        sequence[1:1] = [out]
        sequence[-1:-1] = [back]
        controller = next(key for key in sequence if key.startswith("r-"))
        paths.append({
            "id": path["id"], "source": "usb-supply", "load": path["load"], "sequence": sequence,
            "required_continuous_current_a": path["current_ma"] / 1000.0,
            "required_peak_current_a": path["current_ma"] / 1000.0,
            "protection": {"status": "not_required", "justification": "USB source is current limited",
                           "evidence_url": "https://usb.example/spec"},
            "control": {"status": "present", "component": controller},
            "route": {"modeled": True, "clearance_envelope_mm": 1.0, "strain_relief": True,
                      "service_access": "rear panel"},
        })
    report = {
        "schema_version": 3, "project": "mac-fidget", "boundary": "external",
        "github_search": [{"query": "usb led night light enclosure", "decision": "miss",
                           "reason": "no compatible open design"}],
        "component_search": [{"query": "power-only USB-C receptacle", "service": "manufacturer",
                              "url": "https://manufacturer.example/usb-c", "decision": "miss",
                              "reason": "seed awaits the owner"}],
        "components": components, "paths": paths,
    }
    return report, mounts


class ExternalSourceReportTest(unittest.TestCase):
    """ADR 0095 amendment (E1, E3): a USB toy's report has the external
    boundary, and check_power accepts two paths to one load."""

    def test_check_power_accepts_the_usb_report_with_two_paths_per_warm_led(self):
        report, mounts = usb_power_report()
        loads = [path["load"] for path in report["paths"]]
        self.assertEqual(loads.count("warm-1"), 2)
        self.assertEqual(_check_power().validate_manifest(report, mounts), [])

    def test_check_power_refuses_the_external_boundary_without_a_carried_inlet(self):
        report, mounts = usb_power_report()
        next(item for item in report["components"] if item["id"] == "usb-c")["carried"] = False
        errors = _check_power().validate_manifest(report, mounts)
        self.assertIn("external boundary requires a carried inlet component", errors)

    def test_the_usb_report_is_the_sealed_circuit(self):
        self.assertEqual(check_power_report(_mac_usb(), usb_power_report()[0]), [])

    def test_an_external_source_needs_the_external_boundary_and_is_not_carried(self):
        report = usb_power_report()[0]
        report["boundary"] = "onboard"
        report["components"][0]["carried"] = True
        problems = "\n".join(check_power_report(_mac_usb(), report))
        self.assertIn("the contract's source usb-supply is external, but the report's boundary is onboard", problems)
        self.assertIn("report source usb-supply is the buyer's external supply, so carried is false, not True",
                      problems)
        report = power_report()
        report["boundary"] = "external"
        self.assertIn("the contract carries its source, but the report's boundary is external",
                      check_power_report(_electrical(), report))

    def test_a_dropped_dim_branch_is_refused(self):
        report = usb_power_report()[0]
        report["paths"] = [path for path in report["paths"] if path["id"] != "warm-2-dim"]
        self.assertIn("the contract's path warm-2-dim is no report path", check_power_report(_mac_usb(), report))

    def test_the_receipt_counts_no_charger_and_no_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary)
            cad = run_root / PRODUCT / "cad"
            (cad / "measure").mkdir(parents=True)
            (cad / "measure" / "power.json").write_text(json.dumps(usb_power_report()[0]))
            (cad / "measure" / "verification-pipeline.md").write_text(pipeline())
            manifest = build_artifact_manifest(run_root / PRODUCT, created_at="content-addressed")
            made = types.SimpleNamespace(product_root=PRODUCT, cad_project_path="cad", product_manifest=manifest)
            account = verify_made_power(run_root, made, {"schema_version": 10, "electrical": _mac_usb()})
        self.assertEqual((account["boundary"], account["runtime_h"]), ("external", None))
        self.assertEqual(account["parts"], len(_mac_usb()["parts"]) - 1)
        self.assertEqual(len(account["paths"]), 7)


if __name__ == "__main__":
    unittest.main()
