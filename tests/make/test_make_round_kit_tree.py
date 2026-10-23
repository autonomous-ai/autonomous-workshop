"""ADR 0092: make_round, the paper gate and final verification run the
Assembly Tree gates of a schema 7 contract in the scope each owns, and a tree
defect stops every later round (decision 10)."""

from __future__ import annotations

import contextlib
import io
import json
import runpy
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.runtime.package_data import product_run_domain_skill_roots
from workshop.wish.design_contract import parse_design_contract
from tests.make.test_kit_tree import kit_tree as TOOL, sealed_block, sealed_kit
from tests.make.test_make_round import (
    _gate_output, _install_gate_identity, fake_render_review, load_module,
)
from tests.wish.test_assembly_tree import _catalogues
from tests.wish.test_design_contract import _contract_text

ROOTS = product_run_domain_skill_roots()
CHECK_PIECES = ROOTS["print-details"] / "scripts" / "check_print_pieces.py"
VERIFIER = ROOTS["cad"] / "scripts" / "verify_project"


def report_line(verdict="PASS", defects=(), failures=(), digest="d" * 64, scope="assembly", slips=()):
    return json.dumps({"kind": "kit-tree-report", "verdict": verdict, "defects": list(defects),
                       "slips": list(slips),
                       "failures": list(failures), "conditions": [{"id": "S07-furniture"}], "routes": [],
                       "tree_sha256": digest, "scope": scope})


class KitStateTest(unittest.TestCase):
    """Which tree a round checks, and where its Print Pieces are checked."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name)
        self.project = self.run_root / "artifacts" / "make" / "r0001" / "product" / "cad"
        self.project.mkdir(parents=True)
        self.module = load_module()
        parsed = parse_design_contract(_contract_text(sealed_block()), catalogues=_catalogues())
        self.contract, self.catalogue = parsed.to_dict(), parsed.kit_catalogue()

    def write_wish(self, contract=None):
        context = {"design_contract": contract or self.contract, "kit_catalogue": self.catalogue}
        (self.run_root / "WISH.json").write_text(json.dumps({"references": [], "context": context}))

    def test_a_schema_7_run_checks_the_installed_tree_against_the_seal(self):
        self.assertEqual(self.module.kit_state(self.project), (None, None))
        self.write_wish()
        kit, error = self.module.kit_state(self.project)
        self.assertIn("not installed", error)
        TOOL.install(self.project, self.run_root / "WISH.json")
        kit, error = self.module.kit_state(self.project)
        self.assertIsNone(error)
        self.assertEqual(kit["assembly_tree"], self.contract["assembly_tree"])
        # Outside the run (the host's rerun of a copied project) the install stands.
        (self.run_root / "WISH.json").unlink()
        self.assertEqual(self.module.kit_state(self.project), (kit, None))

    def test_an_earlier_schema_never_reads_a_tree(self):
        contract = dict(self.contract, schema_version=6)
        self.write_wish(contract)
        self.assertEqual(self.module.kit_state(self.project), (None, None))
        self.assertEqual(self.module.tree_refusal(self.project), "")

    def test_the_paper_gate_runs_in_the_rounds_of_the_components_that_carry_pieces(self):
        self.write_wish()
        (self.project / "print").mkdir()
        (self.project / "print" / "pieces.json").write_text(json.dumps(
            {"title": self.contract["title"], "print": self.contract["print"]}, indent=2, sort_keys=True))
        roles, error = self.module.paper_hosts(self.project)
        self.assertIn("Assembly Tree is not installed", error)
        TOOL.install(self.project, self.run_root / "WISH.json")
        # M01 lands on the cabinet carcass, M02 on the desk: not on "B01-cabinet-carcass".
        self.assertEqual(self.module.paper_hosts(self.project), ({"cabinet", "desk"}, None))

    def test_a_recorded_tree_defect_refuses_every_later_round_of_that_tree(self):
        self.write_wish()
        TOOL.install(self.project, self.run_root / "WISH.json")
        kit, _ = self.module.kit_state(self.project)
        self.assertEqual(self.module.tree_refusal(self.project), "")
        report = TOOL.summarise({"scope": "component:cabinet", "defects": [
            {"kind": "missing", "part": "B02-cabinet-door", "detail": "no body labelled B02-cabinet-door"}],
            "failures": [], "conditions": [], "routes": []})
        TOOL.record_defects(self.project, report, TOOL.tree_digest(kit))
        refusal = self.module.tree_refusal(self.project)
        self.assertIn("a tree defect stopped this run (ADR 0092 decision 10)", refusal)
        self.assertIn("stage_proposal.py --run-root . need --stage make", refusal)
        self.assertIn("TREE-ISSUES.md", refusal)
        with contextlib.redirect_stderr(io.StringIO()) as stderr, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.module.main([str(self.project), "--component", "part_cabinet.step.py"]), 2)
        self.assertIn("tree defect stopped this run", stderr.getvalue())
        # A ledger of another tree (the owner amended it) refuses nothing.
        TOOL.record_defects(self.project, report, "0" * 64)
        self.assertEqual(self.module.tree_refusal(self.project), "")

    def test_a_tree_verdict_reads_the_report_line(self):
        parse = self.module.parse_tree
        tree = parse("kit tree assembly: PASS\n" + report_line() + "\n", 0)
        self.assertEqual((tree["verdict"], tree["conditions"], tree["routes"]), ("PASS", 1, 0))
        self.assertEqual(parse("Traceback\n", 2)["verdict"], "FAIL")
        self.assertIn("kit_tree exit 2", parse("Traceback\n", 2)["failures"][0])


class CheckPrintPiecesTreeTest(unittest.TestCase):
    """check_print_pieces under a schema 7 tree: which part carries a piece."""

    def test_the_tree_decides_the_part(self):
        tool = runpy.run_path(str(CHECK_PIECES))
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self.assertIsNone(tool["kit_hosts"](project, "cabinet"))
            (project / "tree").mkdir()
            block = sealed_block()
            block["print"]["pieces"].append(
                {"id": "M04-jar-label", "art": "print-01-spines.png", "stock": "paper", "way": "flat",
                 "on": "P02-jar", "where": "On the jar's front.", "size_mm": [5, 5]})
            step = next(item for item in block["assembly_tree"]["steps"] if item["id"] == "S01-cabinet-shelf")
            step["joint"] = "paper"
            step["inputs"].append({"id": "M04-jar-label", "direction": [0, 1, 0]})
            kit = sealed_kit(block)
            (project / "tree" / "kit.json").write_text(json.dumps(kit))
            cabinet = tool["kit_hosts"](project, "cabinet")
            self.assertEqual(cabinet, {"hosted": {"M01-spine-strip"}, "bought": {"M04-jar-label"},
                                       "spanning": set()})
            section = {"pieces": kit["pieces"]}
            self.assertEqual([p["id"] for p in tool["hosted_pieces"](section, "cabinet", cabinet)],
                             ["M01-spine-strip"])
            spine = kit["pieces"][0]
            self.assertTrue(tool["carries"](spine, "cabinet", cabinet))
            self.assertFalse(tool["carries"](spine, "desk", tool["kit_hosts"](project, "desk")))
            # Without a tree a piece's `on` is its Unique Geometry, as before.
            self.assertTrue(tool["carries"]({"id": "x", "on": "panel#2"}, "panel", None))


class RoundTreeGateTest(unittest.TestCase):
    """An assembly round runs kit_tree.py --assembly and keeps its verdict."""

    def round(self, project, stdout, code, exit_code):
        module = load_module()
        calls = []

        def fake_run(command, **kwargs):
            tool = Path(command[1]).name
            calls.append(command)
            if tool == "gen":
                Path(command[2]).with_name(Path(command[2]).name[:-3]).write_bytes(b"step")
            if tool == "render_review":
                fake_render_review(command)
            if tool == "kit_tree.py":
                return subprocess.CompletedProcess(command, code, stdout, "")
            if tool in ("check_thickness", "check_overhang"):
                out, rc = _gate_output(tool, fails=False)
                return subprocess.CompletedProcess(command, rc, out, "")
            return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

        with contextlib.redirect_stdout(io.StringIO()) as printed, \
                mock.patch.object(module, "skills_root", return_value=project), \
                mock.patch.object(module, "run", side_effect=fake_run):
            self.assertEqual(module.main([str(project)]), exit_code)
        rounds = sorted((project / "measure" / "rounds").iterdir())
        return module, calls, json.loads((rounds[-1] / "summary.json").read_text()), printed.getvalue()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        (self.project / "toy.step.py").write_text("def gen_step(): pass\n")
        (self.project / "part_wheel.step.py").write_text("def gen_step(): pass\n")
        _install_gate_identity(self.project)
        (self.project / "tree").mkdir()
        self.kit = sealed_kit()
        (self.project / "tree" / "kit.json").write_text(json.dumps(self.kit))

    def test_a_passing_tree_joins_the_round(self):
        module, calls, summary, _ = self.round(self.project, report_line() + "\n", 0, 1)
        command = next(c for c in calls if Path(c[1]).name == "kit_tree.py")
        self.assertIn("--assembly", command)
        self.assertEqual(summary["tree"]["verdict"], "PASS")
        self.assertTrue(summary["checks_ok"])
        self.assertIn("  tree  PASS 1 insertion sequence(s)", module.render_summary(summary))

    def test_a_failing_tree_fails_the_round(self):
        line = report_line("FAIL", failures=["S07-furniture: S03-hang-door#1 cannot go in alone"])
        _, _, summary, printed = self.round(self.project, line + "\n", 1, 1)
        self.assertFalse(summary["checks_ok"])
        self.assertIn("S03-hang-door#1 cannot go in alone", printed)

    def test_a_labelling_slip_fails_the_round_but_the_run_continues(self):
        # Owner decision Q28: a body that does not match a sound tree is
        # repaired in the next round; nothing is recorded, nothing refuses.
        slip = {"kind": "missing", "part": "B02-cabinet-door", "detail": "no body labelled B02-cabinet-door"}
        line = report_line("FAIL", slips=[slip], digest=TOOL.tree_digest(self.kit), failures=[
            "labelling slip: missing B02-cabinet-door: no body labelled B02-cabinet-door; rebuild or relabel "
            "the body to match the tree"])
        module, _, summary, printed = self.round(self.project, line + "\n", 1, 1)
        self.assertFalse(summary["checks_ok"])
        self.assertEqual(summary["tree"]["verdict"], "FAIL")
        self.assertNotIn("need", summary["tree"])
        self.assertNotIn("TREE DEFECT", printed)
        self.assertIn("labelling slip", printed)
        self.assertFalse((self.project / "measure" / "tree-defects.json").exists())
        self.assertEqual(module.tree_refusal(self.project), "")
        # The next round runs, and with the body built it passes its tree line.
        _, _, summary, _ = self.round(self.project, report_line(digest=TOOL.tree_digest(self.kit)) + "\n", 0, 1)
        self.assertEqual(summary["tree"]["verdict"], "PASS")
        self.assertTrue(summary["checks_ok"])

    def test_a_tree_defect_fails_the_round_and_stops_every_later_one(self):
        digest = TOOL.tree_digest(self.kit)
        line = report_line("DEFECT", defects=[{"kind": "extra", "part": "B03-shelf", "detail": "no leaf"}],
                           digest=digest)
        _, _, summary, printed = self.round(self.project, line + "\n", 3, 1)
        self.assertFalse(summary["checks_ok"])
        self.assertIn("TREE DEFECT: stop now", printed)
        self.assertIn("TREE-ISSUES.md", summary["tree"]["need"])
        ledger = json.loads((self.project / "measure" / "tree-defects.json").read_text())
        self.assertEqual(ledger["tree_sha256"], digest)
        module = load_module()
        with contextlib.redirect_stderr(io.StringIO()) as stderr, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(module.main([str(self.project)]), 2)
        self.assertIn("extra B03-shelf", stderr.getvalue())


class FinalVerificationTreeTest(unittest.TestCase):
    def test_final_verification_runs_the_tree_gates_of_a_schema_7_run(self):
        verifier = runpy.run_path(str(VERIFIER))
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary)
            project = run_root / "cad"
            project.mkdir()
            parsed = parse_design_contract(_contract_text(sealed_block()), catalogues=_catalogues())
            (run_root / "WISH.json").write_text(json.dumps({"references": [], "context": {
                "design_contract": parsed.to_dict(), "kit_catalogue": parsed.kit_catalogue()}}))
            runner = verifier["Runner"](cwd=project, dry_run=False, verbose=False)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verifier["_run_kit_tree"](runner, project, 0.4), 1)
            self.assertIn("Assembly Tree is not installed", runner.records[-1]["command"])
            TOOL.install(project, run_root / "WISH.json")
            runner = verifier["Runner"](cwd=project, dry_run=True, verbose=False)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(verifier["_run_kit_tree"](runner, project, 0.4), 0)
            self.assertIn("kit_tree.py", runner.records[-1]["command"])
            self.assertIn("--final", runner.records[-1]["command"])
            # An earlier contract runs nothing.
            (run_root / "WISH.json").write_text(json.dumps({"references": [], "context": {
                "design_contract": dict(parsed.to_dict(), schema_version=6)}}))
            runner = verifier["Runner"](cwd=project, dry_run=True, verbose=False)
            self.assertEqual(verifier["_run_kit_tree"](runner, project, 0.4), 0)
            self.assertEqual(runner.records, [])


if __name__ == "__main__":
    unittest.main()
