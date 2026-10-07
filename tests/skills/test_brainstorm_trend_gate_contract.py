import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = (
    Path(__file__).resolve().parents[2]
    / ".claude"
    / "skills"
    / "brainstorm-trend"
    / "scripts"
    / "gate_contract.py"
)


def _load_tool():
    spec = importlib.util.spec_from_file_location("brainstorm_trend_gate_contract_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BLOCK = {
    "schema_version": 4,
    "title": "Glacier Gulper",
    "inventor": "trend-lab",
    "envelope_mm": [160, 90, 110],
    "references": [
        {"file": "ref-01-gulper.png", "shows": "assembly", "camera": [-35, 20]},
        {"file": "ref-02-jaw.png", "shows": "geometry:jaw", "camera": [-35, 20]},
    ],
    "geometries": [
        {"id": "body", "name": "Body", "count": 1, "extents_mm": [150, 80, 90], "wall_min_mm": 2.0},
        {"id": "jaw", "name": "Jaw", "count": 1, "extents_mm": [60, 70, 20], "wall_min_mm": 2.0},
    ],
    "requirements": [
        {"id": "R01", "scope": "assembly", "text": "Pressing the tail drops the jaw open."},
        {"id": "R02", "scope": "geometry:jaw", "text": "The jaw carries six blunt teeth."},
    ],
    "interfaces": [
        {
            "id": "jaw-hinge", "kind": "coupled", "components": ["body", "jaw"],
            "yielding": "jaw", "poses_from": "jaw-opens",
            "text": "The jaw swings 40 degrees on a pin through the body's cheeks.",
        }
    ],
}

_PROSE = (
    "# Glacier Gulper\n\n"
    "A toy whale that swallows ice cubes.\n\n"
    "## Trend Hook\n\n"
    "The six teeth are the six ice shelves in this month's melt news.\n\n"
    "## Signature Motion\n\n"
    "Press the tail and the jaw gulps.\n\n"
    "## Palette\n\n"
    "- body: glacier blue PLA\n"
    "- jaw: white PLA\n"
)

_PALETTE = "\n## Palette\n\n- body: blue\n- jaw: white\n"


def _contract_text(prose=_PROSE, block=None):
    body = _BLOCK if block is None else block
    return "%s\n```design-contract\n%s\n```\n" % (prose, json.dumps(body, indent=2))


class GateContractTests(unittest.TestCase):
    def setUp(self):
        self.tool = _load_tool()

    def test_passes_a_conforming_contract(self):
        passed, reasons = self.tool.gate_contract(_contract_text())
        self.assertTrue(passed)
        self.assertEqual(reasons, [])

    def test_fails_without_a_trend_hook_section(self):
        prose = _PROSE.replace("## Trend Hook", "## Inspiration")
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose))
        self.assertFalse(passed)
        self.assertEqual(reasons, ["no Trend Hook section found in the prose"])

    def test_fails_with_an_empty_trend_hook_section(self):
        prose = "# Gulper\n\n## Trend Hook\n\n## Signature Motion\n\nThe jaw gulps.\n" + _PALETTE
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose))
        self.assertFalse(passed)
        self.assertEqual(reasons, ["no Trend Hook section found in the prose"])

    def test_fails_without_a_signature_motion_section(self):
        prose = "# Gulper\n\n## Trend Hook\n\nSix teeth, six ice shelves.\n" + _PALETTE
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose))
        self.assertFalse(passed)
        self.assertEqual(reasons, ["no Signature Motion section found in the prose"])

    def test_sections_match_in_any_order_and_heading_level(self):
        prose = "# Gulper\n\n### signature motion\n\nThe jaw gulps.\n\n# Trend Hook\n\nSix teeth.\n" + _PALETTE
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose))
        self.assertTrue(passed, reasons)

    def test_a_heading_inside_the_contract_block_does_not_count(self):
        prose = "# Gulper\n\n## Trend Hook\n\nSix teeth.\n" + _PALETTE
        text = _contract_text(prose=prose) + "\n## Signature Motion\n\nAfter the block.\n"
        passed, reasons = self.tool.gate_contract(text)
        self.assertFalse(passed)
        self.assertIn("no Signature Motion section found in the prose", reasons)

    def test_fails_when_no_interface_is_coupled(self):
        block = copy.deepcopy(_BLOCK)
        block["interfaces"] = [
            {
                "id": "jaw-seat", "kind": "static", "components": ["body", "jaw"],
                "text": "The jaw is glued into the body.",
            }
        ]
        passed, reasons = self.tool.gate_contract(_contract_text(block=block))
        self.assertFalse(passed)
        self.assertEqual(
            reasons, ["no coupled Interface: a trend toy needs a Signature Motion"]
        )

    def test_fails_when_the_contract_has_no_interfaces_at_all(self):
        block = copy.deepcopy(_BLOCK)
        block["interfaces"] = []
        passed, reasons = self.tool.gate_contract(_contract_text(block=block))
        self.assertFalse(passed)
        self.assertIn("no coupled Interface: a trend toy needs a Signature Motion", reasons)

    def test_a_schema_1_contract_has_no_interfaces_and_fails(self):
        block = copy.deepcopy(_BLOCK)
        block["schema_version"] = 1
        del block["interfaces"]
        for reference in block["references"]:
            del reference["camera"]
        passed, reasons = self.tool.gate_contract(_contract_text(block=block))
        self.assertFalse(passed)
        self.assertEqual(
            reasons, ["no coupled Interface: a trend toy needs a Signature Motion"]
        )

    def test_fails_over_the_character_limit(self):
        prose = _PROSE + ("x" * self.tool.MAX_CONTRACT_CHARACTERS)
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose))
        self.assertFalse(passed)
        self.assertTrue(any("character limit" in reason for reason in reasons))

    def test_fails_over_sixteen_assembly_requirements(self):
        block = copy.deepcopy(_BLOCK)
        block["requirements"] = [
            {"id": "R%02d" % (index + 1), "scope": "assembly", "text": "Requirement %d." % index}
            for index in range(17)
        ]
        passed, reasons = self.tool.gate_contract(_contract_text(block=block))
        self.assertFalse(passed)
        self.assertTrue(any("assembly-scoped requirements" in reason for reason in reasons))

    def test_fails_over_four_requirements_for_one_geometry(self):
        block = copy.deepcopy(_BLOCK)
        block["requirements"] = [
            {
                "id": "R%02d" % (index + 1),
                "scope": "geometry:jaw",
                "text": "Requirement %d." % index,
            }
            for index in range(5)
        ]
        passed, reasons = self.tool.gate_contract(_contract_text(block=block))
        self.assertFalse(passed)
        self.assertTrue(any("geometry:jaw" in reason for reason in reasons))

    def test_fails_when_the_block_does_not_validate(self):
        block = copy.deepcopy(_BLOCK)
        del block["title"]
        passed, reasons = self.tool.gate_contract(_contract_text(block=block))
        self.assertFalse(passed)
        self.assertIn("title must be a non-empty string", reasons)

    def test_fails_when_no_block_is_present_at_all(self):
        passed, reasons = self.tool.gate_contract(_PROSE)
        self.assertFalse(passed)
        self.assertTrue(any("design-contract" in reason for reason in reasons))

    def test_reports_every_failure_at_once(self):
        prose = "# Gulper\n\nNo hook, no motion.\n"
        block = copy.deepcopy(_BLOCK)
        del block["title"]
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose, block=block))
        self.assertFalse(passed)
        self.assertEqual(
            reasons,
            [
                "title must be a non-empty string",
                "no Trend Hook section found in the prose",
                "no Signature Motion section found in the prose",
                "no Palette section found in the prose",
            ],
        )

    def test_fails_without_a_palette_section(self):
        prose = _PROSE.split("## Palette")[0]
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose))
        self.assertFalse(passed)
        self.assertEqual(reasons, ["no Palette section found in the prose"])

    def test_fails_when_the_palette_leaves_out_a_geometry(self):
        prose = _PROSE.replace("- jaw: white PLA\n", "")
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose))
        self.assertFalse(passed)
        self.assertEqual(reasons, ["the Palette names no colour for geometry jaw"])

    def test_a_geometry_id_inside_a_longer_word_does_not_count(self):
        prose = _PROSE.replace("- jaw: white PLA\n", "- jawline trim: white PLA\n")
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose))
        self.assertFalse(passed)
        self.assertEqual(reasons, ["the Palette names no colour for geometry jaw"])

    def test_the_palette_has_no_limit_on_colours(self):
        block = copy.deepcopy(_BLOCK)
        block["geometries"] += [
            {"id": "fin-%d" % index, "name": "Fin", "count": 1,
             "extents_mm": [20, 20, 5], "wall_min_mm": 2.0}
            for index in range(6)
        ]
        prose = _PROSE + "".join("- fin-%d: colour %d\n" % (index, index) for index in range(6))
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose, block=block))
        self.assertTrue(passed, reasons)

    def test_main_writes_json_pass_and_reasons(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CONTRACT.md"
            path.write_text(_contract_text(), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(TOOL), str(path)],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"pass": True, "reasons": []})

if __name__ == "__main__":
    unittest.main()
