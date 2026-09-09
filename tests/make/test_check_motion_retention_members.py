"""A blocked rigid group is not proof that all its material members are held."""
from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

from build123d import Box, Compound, Location, Shell, Solid
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid

CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_motion"


class RetentionMemberTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    @staticmethod
    def condition(part="group", obstacles=None):
        return {"id": "held-" + part, "check": "linear_motion_collision", "expect": "blocked",
                "inputs": {"moving_part": part, "obstacle_parts": obstacles or ["fixed"],
                           "translation": [0, 0, 10], "steps": 10},
                "thresholds": {"maxOverlapMm3": .001}}

    @staticmethod
    def fixture(both=False, wrapped=False, reverse=False):
        solids = [Box(10, 10, 10), Box(2, 2, 2).translate((30, 0, 0))]
        if reverse:
            solids.reverse()
        group = Compound(solids) if wrapped else Compound(children=solids)
        fixed = (Box(50, 14, 2).translate((15, 0, 7)) if both
                 else Box(14, 14, 2).translate((0, 0, 7)))
        return {"group": group, "fixed": fixed}

    def audit(self, parts, condition=None, supports=None, nested=False):
        condition = self.condition() if condition is None else condition
        proof = {"part": condition["inputs"]["moving_part"], "condition": condition["id"]}
        if supports is not None:
            proof["supports"] = supports
        conditions = ([{"id": "sequence", "check": "assembly_sequence",
                        "inputs": {"steps": [condition]}}] if nested else [condition])
        manifest = {"conditions": conditions,
                    "retention": {"fixed_parts": supports or condition["inputs"]["obstacle_parts"],
                                  "proofs": [proof]}}
        before = deepcopy(manifest)
        results = [self.tool["run_condition"](row, parts, i) for i, row in enumerate(conditions)]
        result = self.tool["check_retention_closure"](manifest, parts, results)
        self.assertEqual(manifest, before)
        return results[0], result

    def test_escaping_member_fails_retention_in_every_group_representation(self):
        for wrapped in (False, True):
            for reverse in (False, True):
                with self.subTest(wrapped=wrapped, reverse=reverse):
                    swept, held = self.audit(self.fixture(wrapped=wrapped, reverse=reverse))
                    self.assertEqual(swept["status"], "pass", swept)
                    self.assertEqual(held["status"], "fail", held)
                    evidence = held["memberEvidence"][0]
                    self.assertEqual(evidence["solidCount"], 2)
                    escaped = [m for m in evidence["members"] if m["status"] == "fail"]
                    self.assertEqual(len(escaped), 1)
                    self.assertAlmostEqual(escaped[0]["volumeMm3"], 8)
                    self.assertTrue(escaped[0]["clear"])
                    self.assertEqual(escaped[0]["steps"], 10)
                    self.assertAlmostEqual(escaped[0]["boundsMm"][0][0], 29)

    def test_each_member_can_be_retained_at_a_different_sample(self):
        swept, held = self.audit(self.fixture(both=True))
        self.assertEqual(swept["status"], "pass", swept)
        self.assertEqual(held["status"], "pass", held)
        members = held["memberEvidence"][0]["members"]
        self.assertEqual(sorted(m["step"] for m in members), [2, 6])

    def test_connected_overlap_and_enclosed_cavity_are_one_material_member(self):
        shapes = [Compound(children=[Box(10, 10, 10), Box(6, 10, 10).translate((4, 0, 0))]),
                  Box(10, 10, 10) - Box(4, 4, 4)]
        self.assertEqual(len(shapes[1].solids()), 1)
        self.assertEqual(len(shapes[1].shells()), 2)
        for shape in shapes:
            with self.subTest(volume=shape.volume):
                parts = self.fixture()
                parts["group"] = shape
                _, held = self.audit(parts)
                self.assertEqual(held["status"], "pass", held)
                self.assertEqual(held["memberEvidence"][0]["solidCount"], 1)

    def test_nested_assembly_and_dotted_alias_keep_placed_members(self):
        for alias in ("group", "root.module.group"):
            parts = self.fixture()
            parts["group"].label, parts["fixed"].label = "group", "fixed"
            module = Compound(children=list(parts.values()), label="module")
            module.location = Location((10, 20, 3), (0, 0, 90))
            root = Compound(children=[module], label="root")
            indexed = self.tool["index_parts"](root)
            condition = self.condition(alias, ["root.module.fixed"])
            swept, held = self.audit(indexed, condition, nested=True)
            self.assertEqual(swept["status"], "pass", swept)
            self.assertEqual(held["status"], "fail", held)
            escaped = next(m for m in held["memberEvidence"][0]["members"] if m["clear"])
            self.assertAlmostEqual(escaped["boundsMm"][0][1], 49)

    def test_rotation_checks_every_member(self):
        for both in (False, True):
            with self.subTest(both=both):
                moving = Compound([Box(2, 2, 2).translate((5, 0, 0)),
                                   Box(2, 2, 2).translate((30, 0, 0))])
                stops = [Box(2, 2, 2).translate((0, 5, 0))]
                if both:
                    stops.append(Box(2, 2, 2).translate((0, 30, 0)))
                condition = {"id": "turn-held", "check": "rotation_motion_collision", "expect": "blocked",
                             "inputs": {"moving_part": "group", "obstacle_parts": ["fixed"],
                                        "axis_point": [0, 0, 0], "axis_direction": [0, 0, 1],
                                        "start_deg": 0, "end_deg": 90, "steps": 18}}
                swept, held = self.audit({"group": moving, "fixed": Compound(stops)}, condition)
                self.assertEqual(swept["status"], "pass", swept)
                self.assertEqual(held["status"], "pass" if both else "fail", held)

    def test_declared_supports_must_actually_block_the_members(self):
        parts = self.fixture()
        parts["loose"] = parts.pop("fixed")
        parts["fixed"] = Box(2, 2, 2).translate((100, 0, 0))
        swept, held = self.audit(parts, self.condition(obstacles=["loose", "fixed"]), supports=["fixed"])
        self.assertEqual(swept["status"], "pass", swept)
        self.assertEqual(held["status"], "fail", held)
        self.assertTrue(all(m["clear"] for m in held["memberEvidence"][0]["members"]))

    def test_seated_contact_option_is_preserved_per_member(self):
        parts = self.fixture()
        parts["fixed"] = Compound([parts["fixed"], Box(2, 2, .25).translate((30, 0, -.75))])
        for seated in (False, True):
            condition = self.condition()
            condition["inputs"]["allow_seated_contact"] = seated
            swept, held = self.audit(parts, condition)
            self.assertEqual(swept["status"], "pass", swept)
            self.assertEqual(held["status"], "fail" if seated else "pass", held)

    def test_per_member_overlap_threshold_cannot_be_met_by_summing_tiny_hits(self):
        parts = {"group": Compound([Box(1, 1, 1), Box(1, 1, 1).translate((3, 0, 0))]),
                 "fixed": Box(5, 1, 1).translate((1.5, 0, .4))}
        condition = self.condition()
        condition["inputs"].update(translation=[0, 0, 0], steps=1)
        condition["thresholds"]["maxOverlapMm3"] = 1.0
        swept, held = self.audit(parts, condition)
        self.assertEqual(swept["status"], "pass", swept)  # aggregate 1.2 mm3
        self.assertEqual(held["status"], "fail", held)  # each 0.6 mm3

    def test_measurement_errors_are_inconclusive_not_retained(self):
        condition = self.condition()
        parts = self.fixture(both=True)
        globals_ = self.tool["retention_member_evidence"].__globals__
        with patch.dict(globals_, {"overlap_volume": lambda *_: (_ for _ in ()).throw(ValueError("injected inconsistent Boolean"))}):
            evidence = self.tool["retention_member_evidence"](condition, parts, ["fixed"])
        self.assertEqual(evidence["status"], "inconclusive", evidence)
        self.assertEqual(len(evidence["members"]), 2)
        self.assertTrue(all(m["status"] == "inconclusive" for m in evidence["members"]))

    def test_empty_or_invalid_geometry_cannot_certify_retention(self):
        shell = Shell(list(Box(2, 2, 2).faces())[:-1])
        invalid = Solid(BRepBuilderAPI_MakeSolid(shell.wrapped).Solid())
        for shape in (Compound([]), invalid):
            parts = self.fixture()
            parts["group"] = shape
            evidence = self.tool["retention_member_evidence"](self.condition(), parts, ["fixed"])
            self.assertEqual(evidence["status"], "inconclusive", evidence)

    def test_coarse_or_unknown_sweep_cannot_certify_retention(self):
        for variant in ("coarse", "proxy"):
            condition = self.condition()
            if variant == "coarse":
                condition["thresholds"]["maxStepMm"] = .1
            else:
                condition["check"] = "clear_path_proxy"
            evidence = self.tool["retention_member_evidence"](condition, self.fixture(both=True), ["fixed"])
            self.assertEqual(evidence["status"], "inconclusive", evidence)

    def test_failed_graph_does_not_trigger_member_measurements(self):
        condition = self.condition()
        manifest = {"conditions": [condition], "retention": {"fixed_parts": ["fixed"],
                    "proofs": [{"part": "group", "condition": condition["id"]}]}}
        globals_ = self.tool["check_retention_closure"].__globals__
        with patch.dict(globals_, {"retention_member_evidence": lambda *_: self.fail("invalid proof was measured")}):
            result = self.tool["check_retention_closure"](manifest, self.fixture(), [{"id": condition["id"], "status": "inconclusive"}])
        self.assertEqual(result["status"], "fail", result)

    def test_graph_propagates_inconclusive_member_evidence(self):
        condition = self.condition()
        parts = self.fixture(both=True)
        manifest = {"conditions": [condition], "retention": {"fixed_parts": ["fixed"],
                    "proofs": [{"part": "group", "condition": condition["id"]}]}}
        results = [self.tool["run_condition"](condition, parts, 0)]
        globals_ = self.tool["check_retention_closure"].__globals__
        with patch.dict(globals_, {"_material": lambda *_: (_ for _ in ()).throw(ValueError("injected normalization failure"))}):
            result = self.tool["check_retention_closure"](manifest, parts, results)
        self.assertEqual(result["status"], "inconclusive", result)

    def test_graph_self_check_uses_measured_support_chain(self):
        self.assertEqual(self.tool["run_self_check"](), 0)

    def test_cli_failure_keeps_per_member_evidence_in_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "assembly.step.py").write_text(
                "from build123d import Box, Compound\n"
                "def gen_step():\n"
                "    group = Compound([Box(10, 10, 10), Box(2, 2, 2).translate((30, 0, 0))], label='group')\n"
                "    fixed = Box(14, 14, 2).translate((0, 0, 7))\n"
                "    fixed.label = 'fixed'\n"
                "    return Compound(children=[group, fixed], label='root')\n"
            )
            manifest = root / "motion.json"
            manifest.write_text(json.dumps({"conditions": [self.condition()],
                "retention": {"fixed_parts": ["fixed"],
                              "proofs": [{"part": "group", "condition": "held-group"}]}}))
            output = StringIO()
            with patch.object(sys, "argv", [str(CHECK), str(root), "--manifest", str(manifest), "--json"]), redirect_stdout(output):
                code = self.tool["main"]()
            result = json.loads(output.getvalue())
            self.assertEqual(code, 1)
            self.assertFalse(result["ok"])
            self.assertEqual(result["results"][0]["status"], "pass")
            retention = result["results"][1]
            self.assertEqual(retention["status"], "fail")
            self.assertEqual(retention["memberEvidence"][0]["solidCount"], 2)

    def test_without_retention_declaration_the_rigid_sweep_keeps_its_meaning(self):
        parts = self.fixture()
        condition = self.condition()
        result = self.tool["run_condition"](condition, parts, 0)
        self.assertEqual(result["status"], "pass", result)
        self.assertIsNone(self.tool["check_retention_closure"]({"conditions": [condition]}, parts, [result]))


if __name__ == "__main__":
    unittest.main()
