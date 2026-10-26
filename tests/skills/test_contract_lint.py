"""design-a-toy's contract_lint.py: the host's schema check, schema 7's
Assembly Tree refusals (ADR 0092), and the facts lint left as it was."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.wish.test_assembly_tree import _component, _tree_block
from tests.wish.test_design_contract import _contract_text

TOOL = (
    Path(__file__).resolve().parents[2]
    / ".claude" / "skills" / "design-a-toy" / "scripts" / "contract_lint.py"
)


def _schema_4_block():
    return {
        "schema_version": 4,
        "title": "Disc",
        "inventor": "ad-astra",
        "envelope_mm": [30, 30, 6],
        "references": [{"file": "ref-01-disc.png", "shows": "geometry:disc", "camera": [-90, 15]}],
        "geometries": [{"id": "disc", "name": "Disc", "count": 1, "extents_mm": [30, 30, 6],
                        "wall_min_mm": 1.2}],
        "requirements": [{"id": "R01", "scope": "geometry:disc", "text": "A plain disc."}],
        "interfaces": [],
    }


class ContractLintTest(unittest.TestCase):
    def _lint(self, block, facts=None):
        with tempfile.TemporaryDirectory() as tmp:
            contract = Path(tmp) / "CONTRACT.md"
            contract.write_text(_contract_text(block), encoding="utf-8")
            command = [sys.executable, str(TOOL), str(contract), "--json"]
            if facts is not None:
                path = Path(tmp) / "facts.json"
                path.write_text(json.dumps(facts), encoding="utf-8")
                command.insert(3, str(path))
            done = subprocess.run(command, capture_output=True, text=True, timeout=120)
        return done.returncode, json.loads(done.stdout) if done.stdout.strip() else done.stderr

    def _errors(self, block):
        code, findings = self._lint(block)
        self.assertEqual(code, 1, findings)
        return " | ".join(item["message"] for item in findings if item["level"] == "error")

    def test_a_schema_7_example_passes_with_its_unconfirmed_entries_named(self):
        code, findings = self._lint(_tree_block())
        self.assertEqual(code, 0, findings)
        self.assertFalse([item for item in findings if item["level"] == "error"])
        warned = [item["message"] for item in findings if item["check"] == "catalogue"]
        self.assertIn("filaments.json:navy is not confirmed by the owner yet", warned)

    def test_an_older_schema_passes_unchanged(self):
        code, findings = self._lint(_schema_4_block())
        self.assertEqual((code, findings), (0, []))

    def test_the_acceptance_refusals(self):
        block = _tree_block()
        _component(block, "desk")["parts"].append("D01-inkwell")
        self.assertIn("D01-inkwell is in two Components", self._errors(block))

        block = _tree_block()
        _component(block, "cabinet")["parts"].remove("D01-inkwell")
        _component(block, "case")["parts"].append("D01-inkwell")
        self.assertIn("Component cabinet is not one contiguous subtree", self._errors(block))

        block = _tree_block()
        block["assembly_tree"]["parts"][2]["id"] = "B01-cabinet-leaf"
        self.assertIn("repeats the id B01", self._errors(block))
        block = _tree_block()
        block["assembly_tree"]["parts"].append({"id": "C02-inkwell", "name": "Inkwell", "filament": "oak", "form": "solid"})
        self.assertIn("repeats the mnemonic 'inkwell'", self._errors(block))

        block = _tree_block()
        block["assembly_tree"]["parts"][0]["filament"] = "sparkle-purple"
        self.assertIn("'sparkle-purple' is not in the filament catalogue", self._errors(block))

        block = _tree_block()
        block["assembly_tree"]["parts"][5]["bought"] = "brass-hinge"
        self.assertIn("'brass-hinge' is not in the Bought Part catalogue", self._errors(block))

        block = _tree_block()
        block["print"]["pieces"][0]["on"] = "B09-shelf"
        self.assertIn("M01-spine-strip.on 'B09-shelf' names nothing that exists", self._errors(block))

    def test_a_panel_of_another_thickness_needs_its_reason_and_is_listed(self):
        # Owner decision Q34, 2026-10-26: one standard panel thickness.
        block = _tree_block()
        block["assembly_tree"]["parts"][2]["thickness_mm"] = 3.0
        self.assertIn("a panel of another thickness states its thickness_reason", self._errors(block))
        block["assembly_tree"]["parts"][2]["thickness_reason"] = "The door's arch moulding."
        code, findings = self._lint(block)
        self.assertEqual(code, 0, findings)
        self.assertIn({"level": "warn", "check": "panel",
                       "message": "B02-cabinet-door is a 3 mm panel, not the toy's 2 mm: "
                                  "The door's arch moulding."}, findings)
        block = _tree_block()
        del block["assembly_tree"]["parts"][4]["form"]
        self.assertIn("a printed Part is {id, name, filament, form}", self._errors(block))

    def test_facts_are_still_linted_beside_the_schema(self):
        facts = {"envelope": {"x": [0, 30], "y": [0, 30], "z": [0, 8]},
                 "components": {"disc": {"geometry": "disc",
                                         "bbox": {"x": [0, 30], "y": [0, 30], "z": [0, 6]}}}}
        code, findings = self._lint(_schema_4_block(), facts)
        self.assertEqual(code, 1)
        self.assertEqual([item["check"] for item in findings], ["envelope"])


if __name__ == "__main__":
    unittest.main()
