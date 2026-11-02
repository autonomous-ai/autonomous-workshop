"""Issue #186: the bought bodies ``bought_model.py`` writes are no components.

``bought_model.py --build`` (ADR 0095 amendment of 2026-11-01) writes each
Bought Part body as ``cad/bought/<name>.step`` and lists it with its sha256 in
``measure/bought-bodies.json``. Every STEP walker treats exactly those listed
bytes as bought bodies: the final verifier's component preflight does not ask
them for a mount, ``check_mount`` does not count them as the model holding
their own envelopes, and make-round counts the generated ``bought/__init__.py``
as no Shared Helper. An unlisted STEP is refused as before.
"""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.runtime.package_data import product_run_domain_skill_roots
from tests.make.test_bought_model import (
    PLACEMENTS,
    envelope_path,
    sealed,
    small_circuit,
    tool,
)

SKILLS = product_run_domain_skill_roots()
VERIFIER = SKILLS["cad"] / "scripts" / "verify_project"
CHECK_MOUNT = SKILLS["cad"] / "scripts" / "check_mount"
MAKE_ROUND = SKILLS["make-round"] / "scripts" / "make_round"
STEP_TEXT = "ISO-10303-21;\nEND-ISO-10303-21;\n"


def write(project: Path, relative: str, text: str) -> Path:
    path = project / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def bodies_document(project: Path, steps: dict[str, str], routes: dict[str, str] | None = None) -> None:
    """A ``bought-bodies`` list naming each ``{name: step}`` with its current bytes."""

    def item(name, step):
        return {"name": name, "step": step,
                "step_sha256": hashlib.sha256((project / step).read_bytes()).hexdigest()}

    write(project, "measure/bought-bodies.json", json.dumps({
        "kind": "bought-bodies", "schema_version": 1, "group": "bought",
        "module_sha256": "0" * 64,
        "bodies": [item(name, step) for name, step in steps.items()],
        "routes": [item(name, step) for name, step in (routes or {}).items()],
    }))


class ComponentStepsTest(unittest.TestCase):
    """verify_project's final component preflight."""

    @classmethod
    def setUpClass(cls):
        cls.verifier = runpy.run_path(str(VERIFIER))

    def setUp(self):
        self.project = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.project)
        write(self.project, "widget.step.py", "def gen_step():\n    return None\n")
        write(self.project, "widget.step", STEP_TEXT)
        write(self.project, "bought/bought_usb_c.step", STEP_TEXT + "usb\n")
        write(self.project, "bought/bought_wire_1.step", STEP_TEXT + "wire\n")

    def steps(self):
        canonical, misplaced = self.verifier["_component_steps"](self.project)
        relative = lambda paths: sorted(p.relative_to(self.project).as_posix() for p in paths)
        return relative(canonical), relative(misplaced)

    def test_the_listed_bodies_and_routes_are_no_components(self):
        bodies_document(self.project, {"bought_usb_c": "bought/bought_usb_c.step"},
                        {"bought_wire_1": "bought/bought_wire_1.step"})
        self.assertEqual(self.steps(), ([], []))

    def test_without_the_list_every_bought_body_is_a_stray(self):
        self.assertEqual(self.steps()[1], ["bought/bought_usb_c.step", "bought/bought_wire_1.step"])

    def test_an_unlisted_step_under_bought_stays_a_stray(self):
        bodies_document(self.project, {"bought_usb_c": "bought/bought_usb_c.step"})
        self.assertEqual(self.steps()[1], ["bought/bought_wire_1.step"])

    def test_a_listed_body_whose_bytes_changed_stays_a_stray(self):
        bodies_document(self.project, {"bought_usb_c": "bought/bought_usb_c.step"},
                        {"bought_wire_1": "bought/bought_wire_1.step"})
        write(self.project, "bought/bought_usb_c.step", STEP_TEXT + "edited\n")
        self.assertEqual(self.steps()[1], ["bought/bought_usb_c.step"])

    def test_a_listed_path_outside_the_bought_group_is_not_excluded(self):
        write(self.project, "catalog/bought_servo.step", STEP_TEXT)
        write(self.project, "ref/servo.step", STEP_TEXT)
        bodies_document(self.project, {"bought_usb_c": "bought/bought_usb_c.step",
                                       "bought_wire_1": "bought/bought_wire_1.step",
                                       "bought_servo": "catalog/bought_servo.step",
                                       "bought_ref": "ref/servo.step",
                                       "bought_up": "bought/../catalog/bought_servo.step"})
        self.assertEqual(self.steps(), (["ref/servo.step"], ["catalog/bought_servo.step"]))

    def test_a_list_of_another_kind_excludes_nothing(self):
        bodies_document(self.project, {"bought_usb_c": "bought/bought_usb_c.step",
                                       "bought_wire_1": "bought/bought_wire_1.step"})
        document = json.loads((self.project / "measure/bought-bodies.json").read_text())
        document["kind"] = "bought-placements"
        write(self.project, "measure/bought-bodies.json", json.dumps(document))
        self.assertEqual(len(self.steps()[1]), 2)
        write(self.project, "measure/bought-bodies.json", "{not json")
        self.assertEqual(len(self.steps()[1]), 2)

    def test_final_mode_refuses_an_unlisted_stray_before_any_gate(self):
        bodies_document(self.project, {"bought_usb_c": "bought/bought_usb_c.step"})
        signature_review(self.project)
        done = subprocess.run([sys.executable, str(VERIFIER), ".", "--strict-fit"], cwd=self.project,
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertIn("resolve bought/foreign or stale STEP files", done.stderr)
        self.assertIn("bought/bought_wire_1.step", done.stderr)
        self.assertNotIn("bought/bought_usb_c.step", done.stderr)
        self.assertNotIn("check_layout", done.stdout)


class SharedHelpersTest(unittest.TestCase):
    """make-round counts the generated group module as no Shared Helper."""

    @classmethod
    def setUpClass(cls):
        cls.make_round = runpy.run_path(str(MAKE_ROUND))

    def test_the_recorded_group_module_is_no_shared_helper(self):
        project = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, project)
        write(project, "params.py", "WALL = 2.0\n")
        write(project, "bought/__init__.py", "def bought_group():\n    return None\n")
        write(project, "bought/bought_usb_c.step", STEP_TEXT)
        helpers = self.make_round["shared_helpers"]
        self.assertEqual(sorted(helpers(project)), ["bought/__init__.py", "params.py"],
                         "without a body list the module is an ordinary project module")
        bodies_document(project, {"bought_usb_c": "bought/bought_usb_c.step"})
        self.assertEqual(sorted(helpers(project)), ["params.py"])
        write(project, "bought/extra.py", "X = 1\n")
        self.assertEqual(sorted(helpers(project)), ["bought/extra.py", "params.py"],
                         "only the recorded group module is excluded")


ASSEMBLY = '''"""The fixture toy: one printed tray and its Bought Parts."""

import importlib.util
from pathlib import Path

from build123d import Pos

from bought import bought_group
from cadfilament import filament
from cadgen.assembly import AssemblyHelper

_DIR = Path(__file__).resolve().parent


def _tray():
    spec = importlib.util.spec_from_file_location("_entry_part_tray", _DIR / "part_tray.step.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return Pos(0, 0, -3.0) * module.gen_step()   # print stance -> under the parts


def gen_step():
    asm = AssemblyHelper("fixture_toy")
    asm.add(_tray(), "tray_black", color=filament("black", 1.0, material="catalogue"))
    asm.children.append(bought_group())
    return asm.build()
'''

# A plain plate under every envelope: each component rests on its top face.
TRAY = '''"""The tray every Bought Part rests on, in its print stance."""

from build123d import Align, Box, Pos


def gen_step():
    return Pos(-17.0, -12.0, 0.0) * Box(48.0, 27.0, 3.0, align=(Align.MIN, Align.MIN, Align.MIN))
'''

WIRES = ("screen-light-out", "screen-light-back")
# Every envelope rests on the tray, clear of the board BOARD
# (x -12..12, y 0..1.6) and of each other.
E2E_ENVELOPES = {
    "usb-c": ((-5.0, -10.0, 0.0), (5.0, -2.0, 4.0)),
    "s-half": ((13.0, 2.0, 0.0), (27.0, 9.0, 8.0)),
    "r-screen": ((-3.0, 2.0, 0.0), (3.0, 3.0, 3.0)),
    "screen-led": ((-4.0, 4.0, 0.0), (4.0, 14.0, 8.0)),
    "screen-light-out": ((-16.0, -6.0, 0.0), (-14.0, 12.0, 2.0)),
    "screen-light-back": ((28.0, -6.0, 0.0), (30.0, 12.0, 2.0)),
}


def small_power_report():
    """A check_power schema 3 report of ``small_circuit``: the buyer's
    charger behind a carried USB-C inlet, one wire pair on the one path."""

    evidence = {"kind": "manufacturer_datasheet", "url": "https://manufacturer.example/data.pdf"}
    components = []
    for item in small_circuit()["parts"]:
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
                                  "source": envelope_path(item["id"])})
        if item["role"] == "load":
            component.update(load_type="lighting", continuous_current_a=0.03, peak_current_a=0.03,
                             lighting={"function": "night light", "color": "amber",
                                       "behavior": "steady", "installation": {"mode": "soldered"}})
        components.append(component)
    for wire in WIRES:
        components.append({"id": wire, "role": "wire", "evidence": evidence, "carried": True,
                           "mount_id": "%s-mount" % wire, "continuous_current_a": 1.0,
                           "peak_current_a": 1.0,
                           "cad": {"mode": "validation_envelope", "rendered": False,
                                   "source": envelope_path(wire)}})
    return {
        "schema_version": 3, "project": "fixture-toy", "boundary": "external",
        "github_search": [{"query": "usb led night light enclosure", "decision": "miss",
                           "reason": "no compatible open design"}],
        "component_search": [{"query": "power-only USB-C receptacle", "service": "manufacturer",
                              "url": "https://manufacturer.example/usb-c", "decision": "miss",
                              "reason": "fixture"}],
        "components": components,
        "paths": [{
            "id": "screen-light", "source": "usb-supply", "load": "screen-led",
            "sequence": ["usb-supply", WIRES[0], "usb-c", "s-half", "r-screen", "screen-led",
                         WIRES[1], "usb-supply"],
            "required_continuous_current_a": 0.02, "required_peak_current_a": 0.02,
            "protection": {"status": "not_required", "justification": "USB source is current limited",
                           "evidence_url": "https://usb.example/spec"},
            "control": {"status": "present", "component": "r-screen"},
            "route": {"modeled": True, "clearance_envelope_mm": 1.0, "strain_relief": True,
                      "service_access": "underside"},
        }],
    }


def signature_review(project: Path) -> None:
    """The blind signature review final verification requires, as the
    verifier's own self-check fixture writes it."""

    verifier = runpy.run_path(str(VERIFIER))
    scratch = Path(tempfile.mkdtemp()).resolve()
    try:
        fixture = verifier["_sc_project"](scratch)
        for relative in ("snap/iso.png", "snap/signature.png", verifier["SIGNATURE_REVIEW_RELATIVE"]):
            target = project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(fixture / relative, target)
    finally:
        shutil.rmtree(scratch)


class FinalVerificationTest(unittest.TestCase):
    """End to end: the real final verifier on a powered project whose
    assembly carries ``bought_group()``, as ``make_round --full`` runs it."""

    def setUp(self):
        from build123d import Box, Pos, export_step

        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.root)
        contract, catalogue = sealed(small_circuit())
        (self.root / "WISH.json").write_text(json.dumps({"context": {"design_contract": contract,
                                                                     "kit_catalogue": catalogue}}))
        project = self.project = self.root / "cad"
        mounts = []
        for part, (lo, hi) in E2E_ENVELOPES.items():
            path = project / envelope_path(part)
            path.parent.mkdir(parents=True, exist_ok=True)
            export_step(Pos(*[(hi[i] + lo[i]) / 2 for i in range(3)])
                        * Box(*[hi[i] - lo[i] for i in range(3)]), str(path))
            mounts.append({"id": "%s-mount" % part, "component": envelope_path(part),
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                           "min_clearance": 0.0, "bolts": False,
                           "note": "rests on the tray's top face; contact is the seat"})
        write(project, "measure/mounts.json", json.dumps({"mounts": mounts}))
        write(project, "measure/power.json", json.dumps(small_power_report()))
        write(project, "measure/bought-placements.json", json.dumps(PLACEMENTS))
        write(project, "part_tray.step.py", TRAY)
        write(project, "fixture_toy.step.py", ASSEMBLY)
        tool.build(project)
        signature_review(project)

    def verify(self):
        return subprocess.run(
            [sys.executable, str(VERIFIER), ".", "--strict-fit", "--print-gates", "--nozzle", "0.4",
             "--powered", "--report", "measure/verification-pipeline.md"],
            cwd=self.project, capture_output=True, text=True, timeout=900,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})

    def test_final_verification_passes_with_the_bought_bodies_and_refuses_a_stray(self):
        steps = sorted(p.name for p in (self.project / "bought").glob("*.step"))
        self.assertIn("bought_usb_c.step", steps)
        done = self.verify()
        self.assertEqual(done.returncode, 0, (done.stdout + done.stderr)[-4000:])
        for gate in ("check_mount: rc=0", "check_power: rc=0", "bought_model.py: rc=0",
                     "check_overhang: rc=0"):
            self.assertIn(gate, done.stdout + done.stderr)

        # A STEP the list does not name, even in the bought group, is refused.
        shutil.copy(self.project / "bought/bought_usb_c.step", self.project / "bought/bought_spare.step")
        done = self.verify()
        self.assertEqual(done.returncode, 2, (done.stdout + done.stderr)[-4000:])
        self.assertIn("bought/bought_spare.step", done.stderr)
        self.assertNotIn("bought/bought_usb_c.step", done.stderr)


class CheckMountTest(unittest.TestCase):
    """check_mount measures a mount against the model without the drawn bodies."""

    @classmethod
    def setUpClass(cls):
        cls.check_mount = runpy.run_path(str(CHECK_MOUNT))

    def test_the_listed_bodies_are_left_out_of_the_model_only(self):
        from build123d import Box, Compound, Pos

        project = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, project)
        tray = Box(10, 10, 2)
        tray.label = "tray_black"
        body = Pos(0, 0, 3) * Box(2, 2, 2)
        body.label = "bought_usb_c"
        stray = Pos(0, 0, 6) * Box(2, 2, 2)
        stray.label = "bought_other"
        model = Compound(label="toy", children=[tray, Compound(label="bought", children=[body, stray])])
        parts = self.check_mount["index_parts"](model)
        obstacles = self.check_mount["obstacle_solids"]

        self.assertEqual(len(obstacles(model, parts, None)), 3, "without a body list nothing is left out")
        write(project, "bought/bought_usb_c.step", STEP_TEXT)
        bodies_document(project, {"bought_usb_c": "bought/bought_usb_c.step"})
        parts["__bought__"] = self.check_mount["bought_bodies"](project)
        self.assertEqual(parts["__bought__"], frozenset({"bought_usb_c"}))
        kept = obstacles(model, parts, None)
        self.assertEqual(sorted(round(s.volume, 6) for s in kept), [8.0, 200.0],
                         "the listed body is left out; an unlisted one still counts")
        self.assertEqual(len(obstacles(model, parts, ["bought_usb_c"])), 1,
                         "a mount that names a body in its parts still measures it")


if __name__ == "__main__":
    unittest.main()
