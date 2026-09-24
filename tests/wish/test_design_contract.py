import json
import unittest

from workshop.errors import ContractError
from workshop.wish.design_contract import (
    MAX_ASSEMBLY_REQUIREMENTS,
    MAX_GEOMETRY_REQUIREMENTS,
    parse_design_contract,
)


def _block(**overrides):
    block = {
        "schema_version": 1,
        "title": "Antisol",
        "inventor": "ad-astra",
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
    block.update(overrides)
    return block


def _contract_text(block=None, prose="# Antisol\n\nA toy about disc worlds.\n"):
    body = block if block is not None else _block()
    return "%s\n```design-contract\n%s\n```\n" % (prose, json.dumps(body, indent=2))


class DesignContractParsingTest(unittest.TestCase):
    def test_a_well_formed_contract_parses(self):
        contract = parse_design_contract(_contract_text())

        self.assertEqual(contract.title, "Antisol")
        self.assertEqual(contract.inventor, "ad-astra")
        self.assertEqual(contract.envelope_mm, (200.0, 200.0, 60.0))
        self.assertEqual(len(contract.references), 2)
        self.assertEqual(len(contract.geometries), 1)
        self.assertEqual(len(contract.requirements), 2)
        self.assertEqual(
            contract.reference_labels(),
            {"ref-01-antisol.png": "assembly", "ref-02-world-disc.png": "geometry:world-disc"},
        )

    def test_prose_without_any_fenced_block_refuses(self):
        with self.assertRaises(ContractError):
            parse_design_contract("# Antisol\n\nJust prose, no block.\n")

    def test_a_block_that_is_not_valid_json_refuses(self):
        with self.assertRaises(ContractError):
            parse_design_contract("# Antisol\n\n```design-contract\n{not json\n```\n")

    def test_a_missing_required_field_refuses(self):
        block = _block()
        del block["inventor"]

        with self.assertRaisesRegex(ContractError, "inventor"):
            parse_design_contract(_contract_text(block))

    def test_a_malformed_field_refuses(self):
        block = _block(envelope_mm=[200, 200])

        with self.assertRaisesRegex(ContractError, "envelope_mm"):
            parse_design_contract(_contract_text(block))

    def test_citing_a_geometry_that_does_not_exist_refuses(self):
        block = _block()
        block["requirements"].append(
            {"id": "R03", "scope": "geometry:does-not-exist", "text": "A missing geometry."}
        )

        with self.assertRaisesRegex(ContractError, "does not exist"):
            parse_design_contract(_contract_text(block))

    def test_a_reference_citing_a_geometry_that_does_not_exist_refuses(self):
        block = _block()
        block["references"].append({"file": "ref-03-gone.png", "shows": "geometry:does-not-exist"})

        with self.assertRaisesRegex(ContractError, "does not exist"):
            parse_design_contract(_contract_text(block))

    def test_more_than_sixteen_assembly_requirements_refuses(self):
        block = _block()
        block["requirements"] = [
            {"id": "R%02d" % index, "scope": "assembly", "text": "Requirement %d." % index}
            for index in range(1, MAX_ASSEMBLY_REQUIREMENTS + 2)
        ]

        with self.assertRaisesRegex(ContractError, "at most %d assembly" % MAX_ASSEMBLY_REQUIREMENTS):
            parse_design_contract(_contract_text(block))

    def test_more_than_four_requirements_for_one_geometry_refuses(self):
        block = _block()
        block["requirements"] = [
            {"id": "R%02d" % index, "scope": "geometry:world-disc", "text": "Requirement %d." % index}
            for index in range(1, MAX_GEOMETRY_REQUIREMENTS + 2)
        ]

        with self.assertRaisesRegex(
            ContractError, "at most %d requirements are allowed for geometry:world-disc" % MAX_GEOMETRY_REQUIREMENTS
        ):
            parse_design_contract(_contract_text(block))

    def test_every_failure_is_named_at_once(self):
        block = _block(title="", inventor="")
        block["requirements"].append(
            {"id": "R03", "scope": "geometry:does-not-exist", "text": "A missing geometry."}
        )

        with self.assertRaises(ContractError) as failure:
            parse_design_contract(_contract_text(block))

        message = str(failure.exception)
        self.assertIn("title", message)
        self.assertIn("inventor", message)
        self.assertIn("does not exist", message)
