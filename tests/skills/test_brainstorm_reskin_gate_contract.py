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
    / "brainstorm-reskin"
    / "scripts"
    / "gate_contract.py"
)


def _load_tool():
    spec = importlib.util.spec_from_file_location("brainstorm_reskin_gate_contract_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BLOCK = {
    "schema_version": 1,
    "title": "Antisol",
    "inventor": "reskin-lab",
    "envelope_mm": [200, 200, 60],
    "references": [
        {"file": "ref-01-antisol.png", "shows": "assembly"},
        {"file": "ref-02-world-disc.png", "shows": "geometry:world-disc"},
    ],
    "geometries": [
        {
            "id": "world-disc",
            "name": "Planet disc",
            "count": 16,
            "extents_mm": [30, 30, 6],
            "wall_min_mm": 1.2,
        }
    ],
    "requirements": [
        {
            "id": "R01",
            "scope": "assembly",
            "text": "The sun den is the focal point at 35 degrees azimuth.",
        },
        {
            "id": "R02",
            "scope": "geometry:world-disc",
            "text": "Each disc carries one raised equatorial band.",
        },
    ],
}

_PROSE = (
    "# Antisol\n\n"
    "A toy about disc worlds.\n\n"
    "## Theme Hook\n\n"
    "The eight planets of the solar system become the eight world discs.\n"
)


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

    def test_fails_without_a_theme_hook_section(self):
        prose = "# Antisol\n\nA toy about disc worlds.\n"
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose))
        self.assertFalse(passed)
        self.assertIn("no Theme Hook section found in the prose", reasons)

    def test_fails_with_an_empty_theme_hook_section(self):
        prose = "# Antisol\n\n## Theme Hook\n\n## Next\n\nMore prose.\n"
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose))
        self.assertFalse(passed)
        self.assertIn("no Theme Hook section found in the prose", reasons)

    def test_theme_hook_at_end_of_prose_with_no_following_heading(self):
        prose = "# Antisol\n\n## Theme Hook\n\nThe planets become the discs.\n"
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose))
        self.assertTrue(passed)
        self.assertEqual(reasons, [])

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
                "scope": "geometry:world-disc",
                "text": "Requirement %d." % index,
            }
            for index in range(5)
        ]
        passed, reasons = self.tool.gate_contract(_contract_text(block=block))
        self.assertFalse(passed)
        self.assertTrue(any("geometry:world-disc" in reason for reason in reasons))

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
        prose = "# Antisol\n\nNo hook here.\n"
        block = copy.deepcopy(_BLOCK)
        del block["title"]
        passed, reasons = self.tool.gate_contract(_contract_text(prose=prose, block=block))
        self.assertFalse(passed)
        self.assertIn("title must be a non-empty string", reasons)
        self.assertIn("no Theme Hook section found in the prose", reasons)

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
