"""B18: the public README's Bought Parts and assembly text comes from the
host, from the sealed Design Contract in WISH.json and the owner amendments
the host recorded, never from the Manager's prose."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.errors import StateConflict
from workshop.workflow.native_run import _public_assembly_text

SECTION = "Bought Parts and assembly"
SEALED = "Assembly order:\n1. Press a cork disc into each coaster's well."
AMENDED = "Assembly order:\n1. Press a cork disc into each coaster's well, rough side down."


def _wish(contract):
    context = {} if contract is None else {"design_contract": contract}
    return json.dumps({"objective": "a toy", "context": context}).encode("utf-8")


def _contract(*sections):
    return {
        "schema_version": 8,
        "requirements": [{"id": "r1", "scope": "assembly", "text": "Stands."}],
        "prose": [{"heading": heading, "text": text} for heading, text in sections],
    }


class PublicAssemblyTextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run_root = Path(self.tmp.name)

    def seal(self, contract):
        content = _wish(contract)
        (self.run_root / "WISH.json").write_bytes(content)
        return hashlib.sha256(content).hexdigest()

    def test_the_sealed_section_is_the_text(self):
        digest = self.seal(_contract(("Base", "A stump."), (SECTION, SEALED)))
        self.assertEqual(_public_assembly_text(self.run_root, digest, []), SEALED)

    def test_a_contract_without_the_section_or_no_contract_has_none(self):
        digest = self.seal(_contract(("Base", "A stump.")))
        self.assertIsNone(_public_assembly_text(self.run_root, digest, []))
        digest = self.seal(None)
        self.assertIsNone(_public_assembly_text(self.run_root, digest, []))

    def test_an_owner_amendment_of_the_section_is_the_text_in_effect(self):
        digest = self.seal(_contract((SECTION, SEALED)))
        owners = [{"changes": [
            {"row": "prose:" + SECTION, "scope": "prose", "from": SEALED, "to": AMENDED},
        ]}]
        self.assertEqual(_public_assembly_text(self.run_root, digest, owners), AMENDED)

    def test_a_wish_that_differs_from_the_run_binding_is_refused(self):
        self.seal(_contract((SECTION, SEALED)))
        with self.assertRaisesRegex(StateConflict, "differs from the run binding"):
            _public_assembly_text(self.run_root, "0" * 64, [])


if __name__ == "__main__":
    unittest.main()
