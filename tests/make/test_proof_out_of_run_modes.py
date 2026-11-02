"""ADR 0096 decision 1b: the Contract Proof writes its project as Make does,
outside any Workshop run.

Contract: `make_round --shared-helpers --contract CONTRACT.md` reads the
Interfaces from that file and freezes the Shared Helpers as a run's check
does, and refuses `--contract` inside a run; `print_details.py
--install-print --contract` writes the same `print/pieces.json` a sealed
Wish gives, art read from beside the contract; `kit_tree.py --install
--contract` writes the same `tree/kit.json` a run would, its catalogue
snapshot taken by the Workshop contract parser. Each refuses a second
install with other bytes and a call with both or neither input."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import sys
from pathlib import Path
from unittest import mock

from tests.make.test_kit_tree import kit_tree, sealed_block
from tests.make import test_make_round as make_round_tests
from tests.wish.test_design_contract import _contract_text
from workshop.wish.design_contract import parse_design_contract

ROOT = Path(__file__).resolve().parents[2]
PRINT_DETAILS = ROOT / "src/workshop/make/skills/print-details/scripts/print_details.py"


def _print_details():
    spec = importlib.util.spec_from_file_location("workshop_test_print_details_0096", PRINT_DETAILS)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # its dataclasses resolve their module
    spec.loader.exec_module(module)
    return module


class SharedHelpersOutsideRunTest(unittest.TestCase):
    _fake = make_round_tests.InterfaceTest._fake
    _run_root = make_round_tests.SealedReferenceTest._run_root

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.module = make_round_tests.load_module()
        self.faults, self.calls = {}, []

    def _proof(self, project: Path) -> Path:
        (project / "features").mkdir(parents=True)
        (project / "params.py").write_text(make_round_tests.params(40))
        (project / "features/__init__.py").write_text("")
        (project / "wiki/pages/printing").mkdir(parents=True)
        (project / "wiki/pages/printing/joints-and-fits.md").write_text("# Joints and fits\n")
        (project / "features/joints.py").write_text("PEG_D = 4.0  # wiki: joints-and-fits\nassert PEG_D >= 3\n")
        (project / "part_body.step.py").write_text("from features.joints import PEG_D\ndef gen_step(): return 'b'\n")
        contract = self.root / "CONTRACT.md"
        contract.write_text(_contract_text({"schema_version": 2, "title": "Proof",
                                            "interfaces": make_round_tests.InterfaceTest.INTERFACES}))
        return contract

    def _main(self, project, argv):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err, \
                mock.patch.object(self.module, "skills_root", return_value=project), \
                mock.patch.object(self.module, "run", side_effect=self._fake):
            code = self.module.main([str(project), *argv])
        self.stdout, self.stderr = out.getvalue(), err.getvalue()
        return code

    def test_the_contract_file_gives_the_interfaces_and_a_pass_freezes(self):
        project = self.root / "proof"
        contract = self._proof(project)
        # Interfaces from the file: a contract with Interfaces needs a sample.
        self.assertEqual(self._main(project, ["--shared-helpers", "--contract", str(contract)]), 2)
        self.assertIn("no sample", self.stderr)
        # Without the file the directory has no contract, so no sample is asked for.
        self.assertEqual(self._main(project, ["--shared-helpers"]), 0, self.stderr)
        (project / "measure/shared-helpers-freeze.json").unlink()
        (project / "samples").mkdir()
        (project / "samples/peg.step.py").write_text("from features.joints import PEG_D\ndef gen_step(): return 'p'\n")
        self.assertEqual(self._main(project, ["--shared-helpers", "--contract", str(contract)]), 0, self.stderr)
        freeze = json.loads((project / "measure/shared-helpers-freeze.json").read_text())
        self.assertEqual(list(freeze["samples"]), ["peg"])
        self.assertIn("features/joints.py", freeze["helpers"])

    def test_the_rules_still_hold_outside_a_run(self):
        project = self.root / "proof"
        contract = self._proof(project)
        (project / "samples").mkdir()
        (project / "samples/peg.step.py").write_text("from features.joints import PEG_D\ndef gen_step(): return 'p'\n")
        (project / "features/joints.py").write_text("PEG_D = 4.0\nassert PEG_D >= 3\n")
        self.assertEqual(self._main(project, ["--shared-helpers", "--contract", str(contract)]), 1)
        self.assertIn("PEG_D cites no wiki page", self.stderr)
        self.assertFalse((project / "measure/shared-helpers-freeze.json").exists())

    def test_an_unreadable_contract_file_refuses(self):
        project = self.root / "proof"
        self._proof(project)
        bad = self.root / "BAD.md"
        bad.write_text("no block here")
        self.assertEqual(self._main(project, ["--shared-helpers", "--contract", str(bad)]), 2)
        self.assertIn("holds no design-contract JSON block", self.stderr)

    def test_contract_inside_a_run_refuses(self):
        project = self._run_root(str(self.root), {"ref-01-whole.png": b"w"}, context={"design_contract": {
            "schema_version": 2, "title": "Run", "references": [{"file": "ref-01-whole.png", "shows": "assembly"}]}})
        contract = self.root / "CONTRACT.md"
        contract.write_text(_contract_text({"schema_version": 2, "title": "Run"}))
        self.assertEqual(self._main(project, ["--shared-helpers", "--contract", str(contract)]), 2)
        self.assertIn("outside a Workshop run", self.stderr)

    def test_contract_with_a_round_mode_is_a_usage_error(self):
        project = self.root / "proof"
        contract = self._proof(project)
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            self.module.main([str(project), "--component", "part_body.step.py", "--contract", str(contract)])


class PrintInstallOutsideRunTest(unittest.TestCase):
    SECTION = {"stocks": [], "pieces": [{"id": "cover", "kind": "flat"}],
               "art": [{"file": "print-01-cover.png", "pieces": ["cover"]}]}

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "proof"
        self.project.mkdir()
        self.module = _print_details()
        self.contract = self.root / "CONTRACT.md"
        self.contract.write_text(_contract_text({"schema_version": 6, "title": "Book", "print": self.SECTION}))
        (self.root / "print-01-cover.png").write_bytes(b"art")

    def _main(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return self.module.main(list(argv))

    def test_writes_the_same_pieces_bytes_a_sealed_wish_gives(self):
        self.assertEqual(self._main("--install-print", str(self.project), "--contract", str(self.contract)), 0)
        written = (self.project / "print/pieces.json").read_bytes()
        self.assertEqual(written, (json.dumps({"title": "Book", "print": self.SECTION},
                                              indent=2, sort_keys=True) + "\n").encode())
        self.assertEqual((self.project / "print/art/print-01-cover.png").read_bytes(), b"art")
        # The same Wish install gives the same bytes.
        run = self.root / "run"
        (run / "wish-references").mkdir(parents=True)
        (run / "wish-references/print-01-cover.png").write_bytes(b"art")
        import hashlib
        (run / "WISH.json").write_text(json.dumps({
            "context": {"design_contract": {"title": "Book", "print": self.SECTION}},
            "references": [{"name": "print-01-cover.png", "sha256": hashlib.sha256(b"art").hexdigest()}]}))
        other = self.root / "other"
        other.mkdir()
        self.module.install_print(other, run / "WISH.json")
        self.assertEqual((other / "print/pieces.json").read_bytes(), written)

    def test_missing_art_and_other_bytes_refuse(self):
        (self.root / "print-01-cover.png").unlink()
        with self.assertRaises(SystemExit):
            self.module.install_print_contract(self.project, self.contract)
        (self.root / "print-01-cover.png").write_bytes(b"art")
        self.module.install_print_contract(self.project, self.contract)
        (self.root / "print-01-cover.png").write_bytes(b"changed")
        with self.assertRaises(SystemExit):
            self.module.install_print_contract(self.project, self.contract)

    def test_a_contract_without_print_sheets_refuses(self):
        self.contract.write_text(_contract_text({"schema_version": 6, "title": "Book"}))
        with self.assertRaises(SystemExit):
            self.module.install_print_contract(self.project, self.contract)

    def test_both_or_neither_input_is_a_usage_error(self):
        for extra in ([], ["--wish", "W.json", "--contract", str(self.contract)]):
            with self.assertRaises(SystemExit):
                self._main("--install-print", str(self.project), *extra)


class KitInstallOutsideRunTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "proof"
        self.project.mkdir()
        self.contract = self.root / "CONTRACT.md"
        self.text = _contract_text(sealed_block())
        self.contract.write_text(self.text)

    def test_writes_the_document_a_run_would_with_the_parsers_catalogue(self):
        result = kit_tree.install_contract(self.project, self.contract)
        written = json.loads((self.project / "tree/kit.json").read_text())
        parsed = parse_design_contract(self.text)
        expected = kit_tree.install_document(sealed_block(), parsed.kit_catalogue())
        self.assertEqual(written, expected)
        self.assertTrue(written["catalogue"]["filaments"])
        self.assertEqual(result["sha256"], kit_tree.tree_digest(expected))
        # A second install of the same contract is a no-op; other bytes refuse.
        kit_tree.install_contract(self.project, self.contract)
        block = sealed_block()
        block["geometries"][0]["name"] = "Changed case"
        self.contract.write_text(_contract_text(block))
        with self.assertRaises(ValueError):
            kit_tree.install_contract(self.project, self.contract)

    def test_a_contract_without_a_tree_or_one_the_parser_refuses_is_an_error(self):
        self.contract.write_text(_contract_text({"schema_version": 2, "title": "No tree"}))
        with self.assertRaises(ValueError):
            kit_tree.install_contract(self.project, self.contract)
        block = sealed_block()
        block["assembly_tree"]["components"] = "broken"
        self.contract.write_text(_contract_text(block))
        with self.assertRaises(ValueError):
            kit_tree.install_contract(self.project, self.contract)

    def test_cli_needs_exactly_one_input(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(kit_tree.main(["--install", str(self.project), "--contract", str(self.contract)]), 0)
            with self.assertRaises(SystemExit):
                kit_tree.main(["--install", str(self.project)])
            with self.assertRaises(SystemExit):
                kit_tree.main(["--install", str(self.project), "--wish", "W", "--contract", str(self.contract)])


if __name__ == "__main__":
    unittest.main()
