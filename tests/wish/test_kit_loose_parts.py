"""ADR 0104: loose printed Parts state why they print off any sheet, and
may share one letter across filaments (the Amsterdam kit's T01-T15)."""

import unittest

from workshop.errors import ContractError
from workshop.wish.design_contract import parse_design_contract
from tests.wish.test_assembly_tree import _catalogues, _tree_block
from tests.wish.test_design_contract import _contract_text


def _with_loose(block, *loose):
    """Rename the given printed Parts to T letters and make them loose."""

    renames = {}
    for number, old in enumerate(loose, 1):
        renames[old] = "T%02d-%s" % (number, old.split("-", 1)[1])
    tree = block["assembly_tree"]
    for part in tree["parts"]:
        if part["id"] in renames:
            part["id"] = renames[part["id"]]
            part["loose_reason"] = "A round prop that cannot print flat on a sheet."
    for step in tree["steps"]:
        for item in step["inputs"]:
            item["id"] = renames.get(item["id"], item["id"])
    for component in tree["components"]:
        component["parts"] = [renames.get(part, part) for part in component["parts"]]
    for piece in block["print"]["pieces"]:
        piece["on"] = renames.get(piece["on"], piece["on"])
    return block


class LoosePartTest(unittest.TestCase):
    def _parse(self, block):
        return parse_design_contract(_contract_text(block), catalogues=_catalogues())

    def _refused(self, block):
        with self.assertRaises(ContractError) as caught:
            self._parse(block)
        return str(caught.exception)

    def test_loose_parts_share_one_letter_across_filaments(self):
        # D01 is dark-blue and B02 dark-oak: both become T, loose.
        block = _with_loose(_tree_block(), "D01-inkwell", "B02-cabinet-door")
        contract = self._parse(block)
        parts = {item["id"]: item for item in contract.to_dict()["assembly_tree"]["parts"]}
        self.assertEqual(parts["T01-inkwell"]["filament"], "dark-blue")
        self.assertEqual(parts["T02-cabinet-door"]["filament"], "dark-oak")
        self.assertIn("loose_reason", parts["T01-inkwell"])

    def test_without_a_reason_one_letter_is_still_one_filament(self):
        block = _with_loose(_tree_block(), "D01-inkwell", "B02-cabinet-door")
        for part in block["assembly_tree"]["parts"]:
            part.pop("loose_reason", None)
        self.assertIn("one filament is one letter", self._refused(block))

    def test_a_letter_is_wholly_loose_or_wholly_one_filament(self):
        block = _with_loose(_tree_block(), "D01-inkwell")
        tree = block["assembly_tree"]
        door = next(part for part in tree["parts"] if part["id"] == "B02-cabinet-door")
        door["id"] = "T02-cabinet-door"
        for step in tree["steps"]:
            for item in step["inputs"]:
                if item["id"] == "B02-cabinet-door":
                    item["id"] = "T02-cabinet-door"
        for component in tree["components"]:
            component["parts"] = ["T02-cabinet-door" if p == "B02-cabinet-door" else p
                                  for p in component["parts"]]
        self.assertIn("letter T is not loose (T02-cabinet-door), so T01-inkwell cannot be loose",
                      self._refused(block))

    def test_a_loose_reason_is_short_text(self):
        block = _with_loose(_tree_block(), "D01-inkwell")
        part = next(item for item in block["assembly_tree"]["parts"] if item["id"] == "T01-inkwell")
        for bad in ("", "  ", "x" * 301, 3):
            part["loose_reason"] = bad
            self.assertIn("loose_reason must say", self._refused(block))


if __name__ == "__main__":
    unittest.main()
