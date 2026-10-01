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


class CheckReferenceNamesTest(unittest.TestCase):
    def setUp(self):
        self.contract = parse_design_contract(_contract_text(_block()))

    def test_the_contract_images_in_order_pass(self):
        self.contract.check_reference_names(["ref-01-antisol.png", "ref-02-world-disc.png"])

    def test_no_images_refuses(self):
        with self.assertRaisesRegex(ContractError, "lists 2 reference image\\(s\\) but 0"):
            self.contract.check_reference_names([])

    def test_a_name_the_contract_does_not_list_refuses_and_names_both(self):
        with self.assertRaises(ContractError) as failure:
            self.contract.check_reference_names(
                ["ref-01-ref-01-antisol.png", "ref-02-world-disc.png"]
            )
        message = str(failure.exception)
        self.assertTrue(message.startswith("design contract: "))
        self.assertIn("ref-01-ref-01-antisol.png", message)
        self.assertIn("not ref-01-antisol.png", message)

    def test_every_mismatch_is_named_at_once(self):
        with self.assertRaises(ContractError) as failure:
            self.contract.check_reference_names(["ref-01-world-disc.png", "ref-02-antisol.png"])
        message = str(failure.exception)
        self.assertIn("reference image 1", message)
        self.assertIn("reference image 2", message)

    def test_a_different_count_refuses(self):
        with self.assertRaisesRegex(ContractError, "lists 2 reference image\\(s\\) but 1"):
            self.contract.check_reference_names(["ref-01-antisol.png"])


def _interfaces_block(interfaces=None):
    """A schema 2 contract: a wing that swings past a housing and is driven
    by a pinion on a heart core (Broken God, ADR 0082)."""

    block = _block(schema_version=2)
    block["geometries"] = [
        {"id": "wing", "name": "Wing", "count": 2, "extents_mm": [80, 30, 6], "wall_min_mm": 1.2},
        {"id": "spine-housing", "name": "Spine housing", "count": 1, "extents_mm": [60, 40, 40], "wall_min_mm": 1.2},
        {"id": "heart-core", "name": "Heart core", "count": 1, "extents_mm": [20, 20, 20], "wall_min_mm": 1.2},
    ]
    block["references"] = [
        {"file": "ref-01-antisol.png", "shows": "assembly"},
        {"file": "ref-02-wing.png", "shows": "geometry:wing"},
    ]
    block["requirements"] = [{"id": "R01", "scope": "assembly", "text": "The wings spread."}]
    block["interfaces"] = interfaces if interfaces is not None else [
        {"id": "wing-peg", "kind": "static", "components": ["wing", "heart-core"]},
        {
            "id": "wing-housing", "kind": "separable", "components": ["wing", "spine-housing"],
            "envelope": {
                "inside": "wing", "outside": "spine-housing",
                "shapes": [
                    {"pose": "folded", "box": {"min_mm": [0, 0, 0], "max_mm": [80, 30, 8]}},
                    {"pose": "spread", "cylinder": {"base_mm": [0, 0, 0], "axis": [0, 0, 1],
                                                    "radius_mm": 82, "height_mm": 8}},
                ],
            },
        },
        {
            "id": "pinion-sector", "kind": "coupled", "components": ["heart-core", "wing"],
            "yielding": "wing",
            "poses": {"steps": 12, "movers": [
                {"component": "heart-core", "rotation": {"axis_point": [0, 0, 0], "axis_direction": [0, 0, 1],
                                                         "start_deg": 0, "end_deg": 360}, "driven": False},
                {"component": "wing", "rotation": {"axis_point": [20, 0, 0], "axis_direction": [0, 0, 1],
                                                   "start_deg": 0, "end_deg": -90}, "driven": True},
            ]},
        },
    ]
    return block


class InterfacesTest(unittest.TestCase):
    """ADR 0082: a schema 2 contract records every Interface between Components."""

    def _refused(self, interfaces):
        with self.assertRaises(ContractError) as failure:
            parse_design_contract(_contract_text(_interfaces_block(interfaces)))
        return str(failure.exception)

    def _one(self, **changes):
        item = {
            "id": "pinion-sector", "kind": "coupled", "components": ["heart-core", "wing"],
            "yielding": "wing", "poses_from": "pinion-drives-sector",
        }
        item.update(changes)
        return [{key: value for key, value in item.items() if value is not None}]

    def test_a_complete_interfaces_section_parses_and_seals(self):
        contract = parse_design_contract(_contract_text(_interfaces_block()))
        self.assertEqual([item.kind for item in contract.interfaces], ["static", "separable", "coupled"])
        sealed = contract.to_dict()
        self.assertEqual(sealed["schema_version"], 2)
        self.assertEqual(sealed["interfaces"], _interfaces_block()["interfaces"])

    def test_a_kinematic_source_may_stand_for_the_pose_table(self):
        contract = parse_design_contract(_contract_text(_interfaces_block(self._one())))
        self.assertEqual(contract.interfaces[0].poses_from, "pinion-drives-sector")

    def test_a_contract_whose_components_never_meet_has_an_empty_section(self):
        self.assertEqual(parse_design_contract(_contract_text(_interfaces_block([]))).interfaces, ())

    def test_an_older_contract_without_interfaces_stays_valid(self):
        contract = parse_design_contract(_contract_text())
        self.assertIsNone(contract.interfaces)
        self.assertNotIn("interfaces", contract.to_dict())

    def test_schema_2_requires_the_section_and_schema_1_refuses_it(self):
        block = _interfaces_block()
        del block["interfaces"]
        with self.assertRaisesRegex(ContractError, "interfaces must be a list"):
            parse_design_contract(_contract_text(block))
        with self.assertRaisesRegex(ContractError, "interfaces need schema_version 2"):
            parse_design_contract(_contract_text(_block(interfaces=[])))

    def test_each_missing_field_is_refused(self):
        self.assertIn(".kind must be", self._refused(self._one(kind=None)))
        self.assertIn(".components must name two or more", self._refused(self._one(components=None)))
        self.assertIn(".components must name two or more", self._refused(self._one(components=["wing"])))
        self.assertIn("does not exist: 'tail'", self._refused(self._one(components=["wing", "tail"], yielding="tail")))
        self.assertIn(".yielding must name", self._refused(self._one(yielding=None)))
        self.assertIn(".yielding must name", self._refused(self._one(yielding="spine-housing")))
        self.assertIn("exactly one of poses", self._refused(self._one(poses_from=None)))
        self.assertIn(".id must be", self._refused(self._one(id=None)))

    def test_a_separable_interface_needs_its_envelope(self):
        separable = {"id": "wing-housing", "kind": "separable", "components": ["wing", "spine-housing"]}
        self.assertIn("needs a Keep-out Envelope", self._refused([separable]))
        envelope = {"inside": "wing", "outside": "wing",
                    "shapes": [{"pose": "rest", "box": {"min_mm": [0, 0, 0], "max_mm": [1, 1, 0]}}]}
        message = self._refused([{**separable, "envelope": envelope}])
        self.assertIn("two different Components", message)
        self.assertIn("min below max", message)
        envelope = {"inside": "wing", "outside": "spine-housing", "shapes": [
            {"pose": "rest", "box": {"min_mm": [0, 0, 0], "max_mm": [1, 1, 1]}},
            {"pose": "rest", "cylinder": {"base_mm": [0, 0, 0], "axis": [0, 0, 0], "radius_mm": 1, "height_mm": 1}},
        ]}
        message = self._refused([{**separable, "envelope": envelope}])
        self.assertIn("non-zero axis", message)
        self.assertIn("name a pose more than once", message)
        self.assertIn("needs a Keep-out Envelope", self._refused([{**separable, "envelope": {
            "inside": "wing", "outside": "spine-housing"}}]))

    def test_fields_of_another_kind_are_refused(self):
        static = {"id": "wing-peg", "kind": "static", "components": ["wing", "heart-core"], "yielding": "wing"}
        self.assertIn("a static Interface does not take yielding", self._refused([static]))

    def test_a_pose_table_names_only_the_interfaces_components(self):
        poses = {"steps": 4, "movers": [{"component": "spine-housing", "rotation": {}}]}
        message = self._refused(self._one(poses_from=None, poses=poses))
        self.assertIn("Component the Interface joins", message)
        self.assertIn("needs a rotation, a translation", message)
