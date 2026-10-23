"""ADR 0092 decision 8: the Assembly Tree gates, against a deterministic fake
geometry of axis-aligned boxes. Every failure the issue names has its fake:
a missing body, an extra body and a duplicated leaf; a blocked insertion and
a non-parallel joint; a simultaneous move; a closed lead route; and a
lead-joining step below the lamps' common Sub-assembly."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from workshop.runtime.package_data import product_run_domain_skill_roots
from workshop.wish.design_contract import parse_design_contract
from tests.wish.test_assembly_tree import _catalogues, _step, _tree_block
from tests.wish.test_design_contract import _contract_text

TOOL = product_run_domain_skill_roots()["make-round"] / "scripts" / "kit_tree.py"
HEX = "#112233"


def load_tool():
    spec = importlib.util.spec_from_file_location("kit_tree_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kit_tree = load_tool()


def sealed_block():
    """The schema 7 example, its lead routed under the case floor."""

    block = _tree_block()
    _step(block, "S05-case-lamp")["leads"][0]["route_mm"] = [[90, 90, -2], [90, 95, -2], [110, 95, -2]]
    return block


def sealed_kit(block=None):
    contract = parse_design_contract(_contract_text(block or sealed_block()), catalogues=_catalogues())
    catalogue = contract.kit_catalogue()
    catalogue["bought_parts"]["led-3v-cool-white"]["sizes"] = [{"what": "lead diameter", "max_mm": [0.5]}]
    return kit_tree.install_document(contract.to_dict(), catalogue)


def box(lo, hi):
    return (tuple(float(v) for v in lo), tuple(float(v) for v in hi))


# Every body of the example, placed in the assembly frame: a case floor with
# an LED and a battery box under it, a cabinet standing on it with its jar
# and inkwell pressed on from the front, its door slid in from the left and
# its pin dropped from above, and two desks.
LAYOUT = {
    ("case", 1): [
        ("A01-case-shell", box((0, 0, 0), (100, 100, 5))),
        ("P03-ball-led", box((88, 88, -4), (92, 92, 0))),
        ("P04-battery-box", box((10, 10, -10), (30, 20, 0))),
    ],
    ("cabinet", 1): [
        ("B01-cabinet-carcass", box((40, 40, 5), (70, 60, 35))),
        ("P02-jar", box((45, 35, 20), (50, 40, 27))),
        ("D01-inkwell", box((55, 35, 20), (58, 40, 24))),
        ("B02-cabinet-door", box((35, 42, 6), (40, 58, 34))),
        ("P01-hinge-pin", box((36, 43, 34), (37, 44, 40))),
    ],
    ("desk", 1): [("C01-desk-body", box((10, 60, 5), (30, 75, 15)))],
    ("desk", 2): [("C01-desk-body", box((70, 70, 5), (90, 85, 15)))],
}


def overlap(a, b):
    volume = 1.0
    for axis in range(3):
        side = min(a[1][axis], b[1][axis]) - max(a[0][axis], b[0][axis])
        if side <= 0:
            return 0.0
        volume *= side
    return volume


class BoxGeometry:
    """The geometry interface kit_tree's gates use, on boxes."""

    def __init__(self, layout=None, nonparallel=None, colours=None, instances=None):
        self.layout = copy.deepcopy(LAYOUT if layout is None else layout)
        self.joints = nonparallel or {}
        self.colours = colours or {}
        self.counts = instances or {}
        self.sweeps = []

    def instances(self, role):
        return self.counts.get(role, [1])

    def component(self, role, instance):
        found = []
        for item in self.layout.get((role, instance), ()):
            label, shape = item[0], item[1]
            solids = item[2] if len(item) > 2 else 1
            found.append(kit_tree.Body(label, shape, solids=solids,
                                       colours=(self.colours.get(label, HEX),)))
        return found

    def bounds(self, shapes):
        return (tuple(min(s[0][a] for s in shapes) for a in range(3)),
                tuple(max(s[1][a] for s in shapes) for a in range(3)))

    def sweep(self, condition, moving, obstacles):
        self.sweeps.append(condition)
        inputs = condition["inputs"]
        steps, move = inputs["steps"], inputs["translation"]
        step_mm = sum(c * c for c in move) ** 0.5 / steps
        if step_mm > condition["thresholds"].get("maxStepMm", float("inf")) + 1e-9:
            return {"status": "inconclusive", "detail": "sampled too coarsely"}
        for i in range(1 if inputs["allow_seated_contact"] else 0, steps + 1):
            shift = [c * i / steps for c in move]
            for body in moving:
                lo, hi = body.shape
                placed = (tuple(v + d for v, d in zip(lo, shift)), tuple(v + d for v, d in zip(hi, shift)))
                for other in obstacles:
                    volume = overlap(placed, other.shape)
                    if volume > condition["thresholds"]["maxOverlapMm3"]:
                        return {"status": "fail", "obstacle": other.key, "overlapMm3": volume,
                                "detail": "blocked by %s at step %d/%d" % (other.key, i, steps)}
        return {"status": "pass", "detail": "clear across %d steps" % steps}

    def nonparallel(self, moving, obstacles, direction):
        found = []
        for shape in moving:
            for (lo, hi), message in self.joints.items():
                if shape == (lo, hi):
                    found.append(message)
        return found

    def route(self, points, size, obstacles):
        half = size / 2.0
        blocked = {}
        for start, end in zip(points, points[1:]):
            for i in range(0, 101):
                point = [s + (e - s) * i / 100 for s, e in zip(start, end)]
                probe = (tuple(p - half for p in point), tuple(p + half for p in point))
                for other in obstacles:
                    volume = overlap(probe, other.shape)
                    if volume > kit_tree.OVERLAP_MM3:
                        blocked[other.key] = max(blocked.get(other.key, 0.0), volume)
        return {"clear": not blocked,
                "blocked_by": [{"obstacle": key, "overlapMm3": value} for key, value in sorted(blocked.items())]}


def replace(layout, role, label, shape=None, *, instance=1, drop=False, add=None):
    items = layout[(role, instance)]
    for index, item in enumerate(items):
        if item[0] == label:
            if drop:
                del items[index]
            elif shape is not None:
                items[index] = (label, shape)
            break
    if add is not None:
        items.append(add)
    return layout


class KitTreeGateTest(unittest.TestCase):
    def setUp(self):
        self.kit = sealed_kit()
        self.plan = kit_tree.Plan(self.kit)

    def component(self, role, geometry=None, kit=None):
        plan = kit_tree.Plan(kit or self.kit)
        report = kit_tree.check_component(plan, geometry or BoxGeometry(), role, 0.4)
        report["defects"] = kit_tree.structure_defects(plan) + report["defects"]
        return kit_tree.summarise(report)

    def assembly(self, geometry=None, final=False, kit=None):
        plan = kit_tree.Plan(kit or self.kit)
        return kit_tree.summarise(kit_tree.check_assembly(plan, geometry or BoxGeometry(), 0.4,
                                                          reconcile_all=final))

    # -- where each check runs ---------------------------------------------

    def test_a_step_inside_one_component_runs_in_its_round_and_a_join_at_assembly(self):
        ids = lambda steps: [item["id"] for item in steps]
        self.assertEqual(ids(self.plan.steps_in("cabinet")),
                         ["S01-cabinet-shelf", "S02-cabinet-spines", "S03-hang-door"])
        self.assertEqual(ids(self.plan.steps_in("case")), ["S05-case-lamp", "S06-case-battery"])
        self.assertEqual(ids(self.plan.steps_in("desk")), ["S04-dress-desk"])
        self.assertEqual(ids(self.plan.steps_in(None)), ["S07-furniture", "S08-wiring"])

    def test_the_paper_gate_follows_the_same_split(self):
        block = sealed_block()
        block["print"]["pieces"].append(
            {"id": "M03-room-label", "art": "print-02-book.png", "stock": "paper", "way": "flat",
             "on": "S07-furniture", "where": "The front rail.", "size_mm": [10, 7]})
        block["print"]["pieces"].append(
            {"id": "M04-jar-label", "art": "print-01-spines.png", "stock": "paper", "way": "flat",
             "on": "P02-jar", "where": "On the jar's front.", "size_mm": [5, 5]})
        tree = block["assembly_tree"]
        _step(block, "S08-wiring")["id"] = "S09-wiring"
        tree["steps"].insert(-1, {"id": "S08-front-label", "output": "Labelled room", "count": 1,
                                  "joint": "paper", "text": "Lay the label on the front rail.",
                                  "inputs": [{"id": "S07-furniture"},
                                             {"id": "M03-room-label", "direction": [0, 1, 0]}]})
        _step(block, "S09-wiring")["inputs"][0]["id"] = "S08-front-label"
        _step(block, "S01-cabinet-shelf")["inputs"].insert(2, {"id": "M04-jar-label", "direction": [0, 1, 0]})
        _step(block, "S01-cabinet-shelf")["joint"] = "paper"
        kit = sealed_kit(block)
        plan = kit_tree.paper_plan(kit)
        self.assertEqual(plan["hosted"], {"cabinet": ["M01-spine-strip"], "desk": ["M02-desk-book"]})
        self.assertEqual(plan["bought"], {"cabinet": ["M04-jar-label"]})
        self.assertEqual(plan["spanning"], {"M03-room-label": ["cabinet", "case", "desk"]})
        self.assertEqual(kit_tree.paper_roles(kit), {"cabinet", "case", "desk"})
        # A piece across Components is carried by exactly one of them.
        self.assertEqual(kit_tree.paper_coverage(kit, {"case": {"M03-room-label"}}), [])
        self.assertIn("no part of cabinet, case, desk carries",
                      kit_tree.paper_coverage(kit, {"case": set()})[0])
        self.assertIn("case and desk each carry",
                      kit_tree.paper_coverage(kit, {"case": {"M03-room-label"},
                                                    "desk": {"M03-room-label"}})[0])

    # -- a good kit ----------------------------------------------------------

    def test_a_kit_that_matches_its_tree_passes_every_scope(self):
        for role in ("case", "cabinet", "desk"):
            report = self.component(role)
            self.assertEqual(report["verdict"], "PASS", (role, report))
        report = self.assembly(final=True)
        self.assertEqual(report["verdict"], "PASS", report)
        # The cabinet's three steps compile to check_motion conditions in
        # Manual order, each input alone.
        cabinet = self.component("cabinet")
        sequences = [item["id"] for item in cabinet["conditions"]]
        self.assertEqual(sequences, ["S01-cabinet-shelf", "S03-hang-door"])
        first = cabinet["conditions"][0]
        self.assertEqual(first["check"], "assembly_sequence")
        moved = [step["inputs"]["moving_part"] for step in first["inputs"]["steps"]]
        self.assertEqual(moved, ["P02-jar#1", "D01-inkwell#1"])
        jar, ink = first["inputs"]["steps"]
        self.assertEqual(jar["check"], "linear_motion_collision")
        # Only what is already assembled is in the way: the jar meets the
        # carcass alone, the inkwell the carcass and the jar.
        self.assertEqual(jar["inputs"]["obstacle_parts"], ["B01-cabinet-carcass#1"])
        self.assertEqual(ink["inputs"]["obstacle_parts"], ["B01-cabinet-carcass#1", "P02-jar#1"])
        self.assertTrue(jar["inputs"]["allow_seated_contact"])
        self.assertEqual(jar["thresholds"]["maxOverlapMm3"], 0.001)
        # It starts wholly outside the rest of the Sub-assembly: back along
        # -y past the carcass's near face, plus the margin.
        self.assertEqual(jar["inputs"]["translation"], [0.0, -6.0, 0.0])

    def test_sampling_is_no_coarser_than_the_thinnest_wall(self):
        cabinet = self.component("cabinet")
        for sequence in cabinet["conditions"]:
            for step in sequence["inputs"]["steps"]:
                travel = sum(c * c for c in step["inputs"]["translation"]) ** 0.5
                # Two print lines at 0.4 mm, below the cabinet's 1.2 mm wall_min_mm.
                self.assertEqual(step["thresholds"]["maxStepMm"], 0.8)
                self.assertLessEqual(travel / step["inputs"]["steps"], 0.8 + 1e-9)
        block = sealed_block()
        block["geometries"][1]["wall_min_mm"] = 0.6
        cabinet = self.component("cabinet", kit=sealed_kit(block))
        self.assertEqual(cabinet["conditions"][0]["inputs"]["steps"][0]["thresholds"]["maxStepMm"], 0.6)

    def test_each_copy_of_an_input_goes_in_alone(self):
        report = self.assembly()
        furniture = next(item for item in report["conditions"] if item["id"] == "S07-furniture")
        steps = furniture["inputs"]["steps"]
        self.assertEqual([step["inputs"]["moving_part"] for step in steps],
                         ["S03-hang-door#1", "S04-dress-desk#1", "S04-dress-desk#2"])
        # The second desk meets the first, already set on its sockets.
        self.assertIn("C01-desk-body#1", steps[2]["inputs"]["obstacle_parts"])
        self.assertNotIn("C01-desk-body#2", steps[1]["inputs"]["obstacle_parts"])

    # -- tree defects (ADR 0092 decision 10) -------------------------------

    def test_a_missing_body_is_a_tree_defect(self):
        layout = replace(copy.deepcopy(LAYOUT), "cabinet", "B02-cabinet-door", drop=True)
        report = self.component("cabinet", BoxGeometry(layout))
        self.assertEqual(report["verdict"], "DEFECT")
        self.assertEqual([(d["kind"], d["part"]) for d in report["defects"]], [("missing", "B02-cabinet-door")])
        # No sweep runs on a Component that does not match its tree.
        self.assertEqual(report["conditions"], [])
        self.assertIn("TREE DEFECT: stop", kit_tree.render(report))

    def test_an_extra_body_is_a_tree_defect(self):
        layout = replace(copy.deepcopy(LAYOUT), "cabinet", None,
                         add=("B03-cabinet-shelf", box((41, 41, 6), (69, 59, 7))))
        layout[("cabinet", 1)].append((None, box((0, 0, 50), (1, 1, 51))))
        report = self.component("cabinet", BoxGeometry(layout))
        kinds = [(d["kind"], d["part"]) for d in report["defects"]]
        self.assertIn(("extra", "B03-cabinet-shelf"), kinds)
        self.assertIn(("extra", "(unlabelled)"), kinds)
        # A Part of another Component built here is extra too.
        layout = replace(copy.deepcopy(LAYOUT), "cabinet", None,
                         add=("C01-desk-body", box((0, 0, 60), (1, 1, 61))))
        report = self.component("cabinet", BoxGeometry(layout))
        self.assertIn("is a Part of desk", report["defects"][0]["detail"])

    def test_a_duplicated_leaf_is_a_tree_defect(self):
        layout = replace(copy.deepcopy(LAYOUT), "cabinet", None,
                         add=("D01-inkwell", box((60, 35, 20), (63, 40, 24))))
        report = self.component("cabinet", BoxGeometry(layout))
        self.assertEqual([(d["kind"], d["part"]) for d in report["defects"]], [("duplicated", "D01-inkwell")])
        # One printed Part built as two solids is duplicated as well; a
        # bought STEP of several solids is still one Bought Part.
        layout = copy.deepcopy(LAYOUT)
        layout[("cabinet", 1)][3] = ("B02-cabinet-door", LAYOUT[("cabinet", 1)][3][1], 2)
        layout[("cabinet", 1)][1] = ("P02-jar", LAYOUT[("cabinet", 1)][1][1], 3)
        report = self.component("cabinet", BoxGeometry(layout))
        self.assertEqual([(d["kind"], d["part"]) for d in report["defects"]], [("duplicated", "B02-cabinet-door")])
        # A leaf that is an input of two steps, in a tampered install.
        kit = copy.deepcopy(self.kit)
        steps = kit["assembly_tree"]["steps"]
        steps[5]["inputs"].append({"id": "P02-jar", "direction": [0, 0, 1]})
        report = self.component("case", kit=kit)
        self.assertIn(("duplicated", "P02-jar"), [(d["kind"], d["part"]) for d in report["defects"]])

    def test_a_print_piece_or_bought_part_the_tree_cannot_account_for_is_a_defect(self):
        kit = copy.deepcopy(self.kit)
        kit["pieces"].append({"id": "M09-stray", "on": "A01-case-shell"})
        del kit["catalogue"]["bought_parts"]["clear-jar-6x7"]
        defects = [(d["kind"], d["part"]) for d in kit_tree.structure_defects(kit_tree.Plan(kit))]
        self.assertIn(("extra", "M09-stray"), defects)
        self.assertIn(("missing", "P02-jar"), defects)

    def test_a_lead_joining_step_below_the_lamps_common_sub_assembly_is_a_defect(self):
        kit = copy.deepcopy(self.kit)
        desk = next(item for item in kit["assembly_tree"]["steps"] if item["id"] == "S04-dress-desk")
        desk["joint"], desk["lamps"] = "leads", ["P03-ball-led"]
        defects = kit_tree.structure_defects(kit_tree.Plan(kit))
        self.assertEqual([(d["kind"], d["part"]) for d in defects], [("misplaced", "S04-dress-desk")])
        self.assertIn("below the smallest Sub-assembly holding every lamp", defects[0]["detail"])
        self.assertEqual(self.component("desk", kit=kit)["verdict"], "DEFECT")

    # -- repairable failures -------------------------------------------------

    def test_a_blocked_insertion_fails(self):
        # The jar's seat runs 3 mm into the carcass: past the seat it cannot
        # come out the way it went in.
        layout = replace(copy.deepcopy(LAYOUT), "cabinet", "P02-jar", box((45, 37, 20), (50, 43, 27)))
        report = self.component("cabinet", BoxGeometry(layout))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["defects"], [])
        self.assertIn("S01-cabinet-shelf: P02-jar#1 cannot go in alone along [0, 1, 0]: blocked by "
                      "B01-cabinet-carcass#1", report["failures"][0])

    def test_a_non_parallel_joint_fails(self):
        jar = LAYOUT[("cabinet", 1)][1][1]
        geometry = BoxGeometry(nonparallel={jar: "a flat joint face at 30 deg to it near (47.5, 40.0, 23.5)"})
        report = self.component("cabinet", geometry)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["failures"], [
            "S01-cabinet-shelf: P02-jar#1 engages a joint that is not parallel to its direction [0, 1, 0]: "
            "a flat joint face at 30 deg to it near (47.5, 40.0, 23.5)"])

    def test_a_simultaneous_move_is_refused(self):
        # The door rises over the pin's way out: the pin can only go in with
        # the door, never after it.
        layout = replace(copy.deepcopy(LAYOUT), "cabinet", "B02-cabinet-door", box((35, 42, 41), (40, 58, 45)))
        report = self.component("cabinet", BoxGeometry(layout))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(len(report["failures"]), 1)
        self.assertIn("P01-hinge-pin#1 is blocked only by B02-cabinet-door#1", report["failures"][0])
        self.assertIn("a simultaneous move", report["failures"][0])

    def test_a_closed_lead_route_fails(self):
        block = sealed_block()
        _step(block, "S05-case-lamp")["leads"][0]["route_mm"] = [[90, 90, -2], [90, 90, 3]]
        report = self.component("case", kit=sealed_kit(block))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["routes"][0]["sphere_mm"], 0.9)
        self.assertIn("S05-case-lamp.leads[0]: the lead of P03-ball-led is closed: a 0.90 mm sphere swept "
                      "along its route meets A01-case-shell#1", report["failures"][0])
        # The open route under the floor passes.
        self.assertTrue(self.component("case")["routes"][0]["clear"])

    def test_a_lamp_without_a_lead_diameter_cannot_be_swept(self):
        kit = copy.deepcopy(self.kit)
        kit["catalogue"]["bought_parts"]["led-3v-cool-white"]["sizes"] = []
        report = self.component("case", kit=kit)
        self.assertIn("gives led-3v-cool-white no lead diameter", report["failures"][0])

    def test_a_part_in_the_wrong_colour_fails(self):
        report = self.component("cabinet", BoxGeometry(colours={"B02-cabinet-door": "#ff0000"}))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["failures"], [
            "B02-cabinet-door is #ff0000, not its filament dark-oak (#112233): colour it #112233"])

    def test_assembly_and_final_verification_check_across_components(self):
        # A desk set where the cabinet's way down crosses it.
        layout = replace(copy.deepcopy(LAYOUT), "desk", "C01-desk-body", box((38, 38, 5), (72, 62, 15)),
                         instance=1)
        for role in ("cabinet", "desk"):
            self.assertEqual(self.component(role, BoxGeometry(layout))["verdict"], "PASS")
        report = self.assembly(BoxGeometry(layout))
        self.assertEqual(report["verdict"], "FAIL")
        # Set on its sockets the desk overlaps the cabinet set before it:
        # an interference at the seat, not a move made together.
        self.assertIn("S07-furniture: S04-dress-desk#1 cannot go in alone", report["failures"][0])
        # Final verification reconciles every Component and every instance.
        layout = replace(copy.deepcopy(LAYOUT), "desk", "C01-desk-body", drop=True, instance=2)
        report = self.assembly(BoxGeometry(layout), final=True)
        self.assertEqual([(d["kind"], d["part"], d.get("instance")) for d in report["defects"]],
                         [("missing", "C01-desk-body", 2)])


class KitTreeInstallTest(unittest.TestCase):
    def wish(self, root: Path, kit_catalogue=True) -> Path:
        contract = parse_design_contract(_contract_text(sealed_block()), catalogues=_catalogues())
        context = {"design_contract": contract.to_dict()}
        if kit_catalogue:
            context["kit_catalogue"] = contract.kit_catalogue()
        path = root / "WISH.json"
        path.write_text(json.dumps({"context": context}), encoding="utf-8")
        return path

    def test_install_writes_the_sealed_tree_and_refuses_an_edited_one(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cad = root / "cad"
            cad.mkdir()
            wish = self.wish(root)
            kit_tree.install(cad, wish)
            expected = kit_tree.wish_document(json.loads(wish.read_text()))
            self.assertEqual(kit_tree.install_state(cad, expected), (expected, None))
            kit_tree.install(cad, wish)  # the same bytes again
            path = cad / "tree" / "kit.json"
            edited = json.loads(path.read_text())
            edited["assembly_tree"]["parts"][0]["filament"] = "oak"
            path.write_text(json.dumps(edited))
            self.assertIn("not the sealed contract's", kit_tree.install_state(cad, expected)[1])
            with self.assertRaises(ValueError):
                kit_tree.install(cad, wish)
            path.unlink()
            self.assertIn("not installed", kit_tree.install_state(cad, expected)[1])

    def test_install_needs_a_schema_7_contract_and_its_catalogue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "cad").mkdir()
            with self.assertRaisesRegex(ValueError, "kit_catalogue"):
                kit_tree.install(root / "cad", self.wish(root, kit_catalogue=False))
            with self.assertRaisesRegex(ValueError, "not schema 7"):
                kit_tree.install_document({"schema_version": 6}, {})

    def test_a_tree_defect_is_recorded_for_this_tree_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            cad = Path(temporary)
            report = kit_tree.summarise({"scope": "component:cabinet", "defects": [
                {"kind": "missing", "part": "B02-cabinet-door", "detail": "no body"}],
                "failures": [], "conditions": [], "routes": []})
            record = kit_tree.record_defects(cad, report, "a" * 64)
            self.assertIn("TREE-ISSUES.md", record["need"])
            self.assertIn("missing B02-cabinet-door", record["need"])
            self.assertEqual(kit_tree.open_defects(cad, "a" * 64)["scope"], "component:cabinet")
            # The owner amended the tree: the old defect stops nothing.
            self.assertIsNone(kit_tree.open_defects(cad, "b" * 64))

    def test_the_command_line_exits_3_on_a_defect_and_writes_the_final_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            cad = Path(temporary)
            (cad / "tree").mkdir()
            (cad / "tree" / "kit.json").write_text(json.dumps(sealed_kit()))
            original = kit_tree.run

            def fake_run(project, mode, role, nozzle, geometry=None):
                layout = LAYOUT if mode != "component" else replace(
                    copy.deepcopy(LAYOUT), "cabinet", "B02-cabinet-door", drop=True)
                return original(project, mode, role, nozzle, BoxGeometry(layout))

            kit_tree.run = fake_run
            try:
                with unittest.mock.patch("sys.stdout"):
                    self.assertEqual(kit_tree.main([str(cad), "--component", "cabinet"]), 3)
                    self.assertEqual(kit_tree.main([str(cad), "--final"]), 0)
            finally:
                kit_tree.run = original
            report = json.loads((cad / "measure" / "tree-report.json").read_text())
            self.assertEqual(report["kind"], "kit-tree-report")
            self.assertEqual(report["verdict"], "PASS")
            self.assertEqual(report["leaves"]["pieces"], ["M01-spine-strip", "M02-desk-book"])

    def test_self_check(self):
        with unittest.mock.patch("sys.stdout"):
            self.assertEqual(kit_tree.self_check(), 0)


import unittest.mock  # noqa: E402

if __name__ == "__main__":
    unittest.main()
