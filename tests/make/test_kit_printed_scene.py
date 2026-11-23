"""ADR 0104 (2026-11-23): a kit's printed-only scene.

Contract: final verification's ``kit_print.py layout`` also writes
``measure/kit/scene.step``, the assembly STEP less exactly the leaves
``measure/not-printed.json`` lists (a Part the scene holds once may be
listed with its ``#1``), and records it under ``printed_scene``; the host's
``check_printed_scene`` accepts exactly the scene less those leaves, each
printed body by volume and area. A listed body the scene does not hold
exactly once fails the tool."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.make.kit_print import check_printed_scene
from workshop.release.printed_primary import scene_bodies
from workshop.runtime.package_data import product_run_domain_skill_roots
from tests.make.test_bought_model import printed_box, tool as bought_tool, write_scene

SCRIPTS = product_run_domain_skill_roots()["make-round"] / "scripts"


def load_kit_print():
    spec = importlib.util.spec_from_file_location("kit_print_under_test", SCRIPTS / "kit_print.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kit_print = load_kit_print()


def pin(label, at):
    from build123d import Box, Color, Pos

    body = Pos(*at) * Box(2.0, 2.0, 12.0)
    body.label = label
    body.color = Color(1.0, 0.0, 1.0)
    return body


class RemovedNamesTest(unittest.TestCase):
    def test_each_listed_body_is_one_leaf_and_a_single_copy_may_drop_its_number(self):
        names = ["T01-tray", "P01-pin-long#1", "P01-pin-long#2", "P03-pin-short-b"]
        self.assertEqual(
            kit_print.removed_names(["P01-pin-long#1", "P01-pin-long#2", "P03-pin-short-b#1"], names),
            {"P01-pin-long#1": "P01-pin-long#1", "P01-pin-long#2": "P01-pin-long#2",
             "P03-pin-short-b": "P03-pin-short-b#1"})

    def test_a_listed_body_absent_or_held_twice_is_refused(self):
        for requested, names in ((["P09-gone#1"], ["T01-tray"]),
                                 (["P01-pin#1"], ["P01-pin", "P01-pin"]),
                                 (["P01-pin#1", "P01-pin"], ["P01-pin"])):
            with self.subTest(requested=requested), self.assertRaisesRegex(ValueError, "not one"):
                kit_print.removed_names(requested, names)


class PrintedSceneTest(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.project)
        (self.project / "toy.step.py").write_text("def gen_step(): pass\n")
        (self.project / "part_tray.step.py").write_text("def gen_step(): pass\n")
        self.parts = [printed_box("T01-tray"), printed_box("T02-quay", at=(0.0, 0.0, 40.0))]
        self.scene = write_scene(self.project / "toy.step", [
            *self.parts, pin("P01-pin-long#1", (60, 0, 0)), pin("P01-pin-long#2", (70, 0, 0)),
            pin("P03-pin-short-b", (80, 0, 0))])
        self.listed = ["P01-pin-long#1", "P01-pin-long#2", "P03-pin-short-b#1"]
        self.write_listed(self.listed)

    def write_listed(self, bodies):
        (self.project / "measure").mkdir(exist_ok=True)
        (self.project / "measure/not-printed.json").write_text(json.dumps(
            {"kind": "kit-not-printed", "bodies": [{"body": body} for body in bodies]}))

    def test_the_scene_less_its_listed_bodies_is_written_and_recorded(self):
        record = kit_print.printed_scene(self.project)
        printed = (self.project / "measure/kit/scene.step").read_bytes()
        self.assertEqual(record, {
            "step": "measure/kit/scene.step", "sha256": hashlib.sha256(printed).hexdigest(),
            "scene": "toy.step", "scene_sha256": hashlib.sha256(self.scene).hexdigest(),
            "removed": sorted(self.listed)})
        self.assertNotIn(b"magenta", printed.lower())
        kept = sorted(body.name for body in scene_bodies(printed))
        self.assertFalse(any(name.startswith("P0") for name in kept), kept)
        # The host accepts it against the scene it was cut from.
        self.assertEqual(check_printed_scene(printed, self.scene, self.listed), len(kept))

    def test_a_listed_body_the_scene_lacks_fails_the_tool(self):
        self.write_listed([*self.listed, "P04-pin-short-c#1"])
        with self.assertRaisesRegex(ValueError, "P04-pin-short-c#1 is 0 leaf bodies"):
            kit_print.printed_scene(self.project)

    def test_the_host_refuses_the_scene_itself_or_another_cut(self):
        kit_print.printed_scene(self.project)
        printed = (self.project / "measure/kit/scene.step").read_bytes()
        with self.assertRaisesRegex(ContractError, "extra"):
            check_printed_scene(self.scene, self.scene, self.listed)
        with self.assertRaisesRegex(ContractError, "missing"):
            check_printed_scene(printed, self.scene, self.listed[:1])
        alone = write_scene(self.project / "alone.step", self.parts[:1])
        with self.assertRaisesRegex(ContractError, "missing"):
            check_printed_scene(alone, self.scene, self.listed)

    def test_the_predicate_removes_named_leaves_and_still_refuses_an_empty_cut(self):
        removed = bought_tool.write_printed_only(
            self.project / "toy.step", self.project / "out.step",
            removed_name=lambda name: name == "P03-pin-short-b")
        self.assertEqual(removed, ["P03-pin-short-b"])
        with self.assertRaises(bought_tool.Refused):
            bought_tool.write_printed_only(self.project / "toy.step", self.project / "none.step",
                                           removed_name=lambda name: False)


class VerifyProjectExemptionTest(unittest.TestCase):
    """Final verification does not count the sealed scene as a stray STEP."""

    def test_the_recorded_scene_with_its_bytes_is_no_misplaced_step(self):
        import runpy

        cad = product_run_domain_skill_roots()["cad"] / "scripts" / "verify_project"
        component_steps = runpy.run_path(str(cad))["_component_steps"]
        project = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, project)
        kit = project / "measure/kit"
        kit.mkdir(parents=True)
        (kit / "print.step").write_bytes(b"layout")
        (kit / "scene.step").write_bytes(b"scene")
        report = {"kind": "kit-print-layout", "step": "measure/kit/print.step",
                  "sha256": hashlib.sha256(b"layout").hexdigest(),
                  "printed_scene": {"step": "measure/kit/scene.step",
                                    "sha256": hashlib.sha256(b"scene").hexdigest()}}
        (kit / "print.json").write_text(json.dumps(report))
        self.assertEqual(component_steps(project)[1], [])
        # Other bytes than the record names are a stray STEP again.
        (kit / "scene.step").write_bytes(b"other")
        self.assertEqual(component_steps(project)[1], [kit / "scene.step"])


if __name__ == "__main__":
    unittest.main()
