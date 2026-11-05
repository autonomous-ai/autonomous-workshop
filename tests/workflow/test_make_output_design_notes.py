"""B23/B24: the design notes a Spark page carries to Factory come from the
host, from the sealed Design Contract in WISH.json and the owner amendments
the host recorded, never from the Manager's prose."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.errors import StateConflict
from workshop.workflow.native_run import _make_output_design_notes, _make_output_print_overrides

ASSEMBLY = "Bought Parts and assembly"
PRINT = "Print stances and details"
ORDER = "Assembly order:\n1. Press a cork disc into each coaster's well.\n"
RULES = (
    "Workshop prints with a 0.4 mm nozzle in PETG; no part may need support.\n"
    "Print settings (owner's cost choice): 8% infill in every part."
)
SENTENCE = "Workshop prints with a 0.4 mm nozzle in PETG; no part may need support."


def _wish(contract):
    context = {} if contract is None else {"design_contract": contract}
    return json.dumps({"objective": "a toy", "context": context}).encode("utf-8")


def _contract(*sections):
    return {
        "schema_version": 8,
        "requirements": [{"id": "r1", "scope": "assembly", "text": "Stands."}],
        "prose": [{"heading": heading, "text": text} for heading, text in sections],
    }


class MakeOutputDesignNotesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run_root = Path(self.tmp.name)

    def seal(self, contract):
        content = _wish(contract)
        (self.run_root / "WISH.json").write_bytes(content)
        return hashlib.sha256(content).hexdigest()

    def test_the_sealed_sections_are_the_notes(self):
        digest = self.seal(_contract((ASSEMBLY, ORDER), (PRINT, RULES)))
        self.assertEqual(
            _make_output_design_notes(self.run_root, digest, []),
            {"assembly": ORDER.strip(), "print_settings": SENTENCE},
        )

    def test_a_contract_stating_neither_or_no_contract_has_no_notes(self):
        digest = self.seal(_contract(("Base", "A stump.")))
        self.assertIsNone(_make_output_design_notes(self.run_root, digest, []))
        digest = self.seal(None)
        self.assertIsNone(_make_output_design_notes(self.run_root, digest, []))

    def test_one_section_alone_carries_only_itself(self):
        digest = self.seal(_contract((PRINT, RULES)))
        self.assertEqual(
            _make_output_design_notes(self.run_root, digest, []),
            {"print_settings": SENTENCE},
        )

    def test_an_owner_amendment_of_the_material_is_the_text_in_effect(self):
        amended = RULES.replace("PETG", "PLA")
        digest = self.seal(_contract((PRINT, RULES)))
        owners = [{"changes": [
            {"row": "prose:" + PRINT, "scope": "prose", "from": RULES, "to": amended},
        ]}]
        self.assertEqual(
            _make_output_design_notes(self.run_root, digest, owners),
            {"print_settings": SENTENCE.replace("PETG", "PLA")},
        )

    def test_a_wish_that_differs_from_the_run_binding_is_refused(self):
        self.seal(_contract((PRINT, RULES)))
        with self.assertRaisesRegex(StateConflict, "differs from the run binding"):
            _make_output_design_notes(self.run_root, "0" * 64, [])


class MakeOutputPrintOverridesTest(unittest.TestCase):
    """The infill Factory measures, prices and prints the toy at comes from
    the same sealed contract and owner amendments."""

    setUp = MakeOutputDesignNotesTest.setUp
    seal = MakeOutputDesignNotesTest.seal

    def test_the_sealed_infill_is_the_override(self):
        digest = self.seal(_contract((PRINT, RULES)))
        self.assertEqual(
            _make_output_print_overrides(self.run_root, digest, []), {"infill_percent": 8}
        )

    def test_no_infill_or_no_contract_is_no_override(self):
        digest = self.seal(_contract((PRINT, SENTENCE)))
        self.assertIsNone(_make_output_print_overrides(self.run_root, digest, []))
        digest = self.seal(None)
        self.assertIsNone(_make_output_print_overrides(self.run_root, digest, []))

    def test_an_owner_amendment_of_the_infill_is_the_infill_in_effect(self):
        digest = self.seal(_contract((PRINT, RULES)))
        owners = [{"changes": [
            {"row": "prose:" + PRINT, "scope": "prose", "from": RULES, "to": RULES.replace("8%", "10%")},
        ]}]
        self.assertEqual(
            _make_output_print_overrides(self.run_root, digest, owners), {"infill_percent": 10}
        )


if __name__ == "__main__":
    unittest.main()
