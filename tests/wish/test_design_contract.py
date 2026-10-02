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
        with self.assertRaisesRegex(ContractError, "interfaces need schema_version 2 or later"):
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


class InterfaceInstancesTest(unittest.TestCase):
    """Issue #80: an Interface may name one instance of a Unique Geometry
    whose count is above 1, as ``<id>#<n>``."""

    MESH = {
        "id": "wing-sector-mesh", "kind": "coupled", "components": ["wing#1", "wing#2"],
        "yielding": "wing#2",
        "poses": {"steps": 8, "movers": [
            {"component": "wing#1", "rotation": {"axis_point": [16, 0, 198.8], "axis_direction": [1, 0, 0],
                                                 "start_deg": 0, "end_deg": 35}},
            {"component": "wing#2", "rotation": {"axis_point": [-16, 0, 198.8], "axis_direction": [1, 0, 0],
                                                 "start_deg": 0, "end_deg": -35}, "driven": True},
        ]},
    }

    def _refused(self, interfaces):
        with self.assertRaises(ContractError) as failure:
            parse_design_contract(_contract_text(_interfaces_block(interfaces)))
        return str(failure.exception)

    def _mesh(self, **changes):
        item = {**self.MESH, **changes}
        return [{key: value for key, value in item.items() if value is not None}]

    def test_two_instances_of_one_geometry_may_meet_and_seal_verbatim(self):
        contract = parse_design_contract(_contract_text(_interfaces_block(self._mesh())))
        self.assertEqual(contract.interfaces[0].components, ("wing#1", "wing#2"))
        self.assertEqual(contract.interfaces[0].yielding, "wing#2")
        self.assertEqual(contract.to_dict()["interfaces"], self._mesh())

    def test_one_instance_may_meet_another_geometry_and_keep_one_side_of_an_envelope(self):
        separable = {
            "id": "left-wing-housing", "kind": "separable", "components": ["wing#1", "spine-housing"],
            "envelope": {"inside": "wing#1", "outside": "spine-housing", "shapes": [
                {"pose": "rest", "box": {"min_mm": [0, 0, 0], "max_mm": [1, 1, 1]}}]},
        }
        pinion = {"id": "pinion-left", "kind": "coupled", "components": ["heart-core", "wing#1"],
                  "yielding": "wing#1", "poses_from": "pinion-drives-left-wing"}
        mirror = {"id": "wing-fold", "kind": "separable", "components": ["wing#1", "wing#2"],
                  "envelope": {"inside": "wing#2", "outside": "wing#1", "shapes": [
                      {"pose": "rest", "box": {"min_mm": [0, 0, 0], "max_mm": [1, 1, 1]}}]}}
        contract = parse_design_contract(_contract_text(_interfaces_block([separable, pinion, mirror])))
        self.assertEqual(contract.interfaces[0].envelope["inside"], "wing#1")
        self.assertEqual(contract.interfaces[2].envelope["outside"], "wing#1")

    def test_every_instance_reference_is_unambiguous(self):
        self.assertIn("has instances #1 to #2", self._refused(self._mesh(components=["wing#1", "wing#3"])))
        self.assertIn("has instances #1 to #2", self._refused(self._mesh(components=["wing#0", "wing#2"])))
        self.assertIn("has instances #1 to #2", self._refused(self._mesh(components=["wing#01", "wing#2"])))
        message = self._refused(self._mesh(components=["wing#1", "heart-core#1"], yielding="wing#1", poses=None,
                                           poses_from="drive"))
        self.assertIn("'heart-core' has count 1", message)
        self.assertIn("names both 'wing' and an instance of it",
                      self._refused(self._mesh(components=["wing", "wing#2"])))
        self.assertIn("two or more different Components",
                      self._refused(self._mesh(components=["wing#1", "wing#1"])))
        self.assertIn("does not exist: 'tail#1'", self._refused(self._mesh(components=["wing#1", "tail#1"])))

    def test_an_unknown_instance_may_not_yield_or_move(self):
        self.assertIn(".yielding must name", self._refused(self._mesh(yielding="wing")))
        self.assertIn(".yielding must name", self._refused(self._mesh(yielding="wing#3")))
        poses = {"steps": 4, "movers": [{"component": "wing", "rotation": {"axis_point": [0, 0, 0]}}]}
        self.assertIn("Component the Interface joins", self._refused(self._mesh(poses=poses)))
        envelope = {"inside": "wing", "outside": "wing#2", "shapes": [
            {"pose": "rest", "box": {"min_mm": [0, 0, 0], "max_mm": [1, 1, 1]}}]}
        self.assertIn("two different Components", self._refused([
            {"id": "wing-fold", "kind": "separable", "components": ["wing#1", "wing#2"], "envelope": envelope}]))


def _camera_block(cameras=((-60, 20), (0, 90)), **overrides):
    """A schema 3 contract: every reference carries its Reference Camera."""

    block = _block(schema_version=3, interfaces=[])
    for reference, camera in zip(block["references"], cameras):
        if camera is not None:
            reference["camera"] = list(camera)
    block.update(overrides)
    return block


class ReferenceCameraTest(unittest.TestCase):
    """ADR 0083: a schema 3 reference names the camera, in the Display Pose
    frame, from which its image shows its subject."""

    def _refused(self, block):
        with self.assertRaises(ContractError) as caught:
            parse_design_contract(_contract_text(block))
        return str(caught.exception)

    def test_every_reference_carries_its_camera_and_seals_it(self):
        contract = parse_design_contract(_contract_text(_camera_block()))
        self.assertEqual([item.camera for item in contract.references], [(-60.0, 20.0), (0.0, 90.0)])
        self.assertEqual(contract.to_dict()["references"], [
            {"file": "ref-01-antisol.png", "shows": "assembly", "camera": [-60, 20]},
            {"file": "ref-02-world-disc.png", "shows": "geometry:world-disc", "camera": [0, 90]},
        ])
        self.assertEqual(contract.interfaces, ())

    def test_a_reference_without_a_camera_is_refused_naming_it(self):
        message = self._refused(_camera_block(cameras=((-60, 20), None)))
        self.assertIn("references[1].camera must be [AZ, EL]", message)
        self.assertNotIn("references[0]", message)
        # The assembly reference too.
        self.assertIn("references[0].camera", self._refused(_camera_block(cameras=(None, (0, 0)))))

    def test_an_out_of_range_or_malformed_camera_is_refused(self):
        for camera in ([181, 0], [-181, 0], [0, 91], [0, -90.5], [0], [0, 0, 15], ["0", 0], [True, 0]):
            with self.subTest(camera=camera):
                block = _camera_block()
                block["references"][0]["camera"] = camera
                self.assertIn("references[0].camera must be", self._refused(block))
        block = _camera_block(cameras=((180, 90), (-180, -90)))
        self.assertEqual(parse_design_contract(_contract_text(block)).references[1].camera, (-180.0, -90.0))

    def test_schema_3_keeps_the_interfaces_section(self):
        block = _camera_block()
        del block["interfaces"]
        self.assertIn("interfaces must be a list", self._refused(block))

    def test_schema_1_and_2_parse_as_before_and_refuse_a_camera(self):
        for block in (_block(), _block(schema_version=2, interfaces=[])):
            with self.subTest(schema=block["schema_version"]):
                contract = parse_design_contract(_contract_text(block))
                self.assertEqual([item.camera for item in contract.references], [None, None])
                self.assertEqual(contract.to_dict()["references"], block["references"])
                block["references"][0]["camera"] = [0, 0]
                self.assertIn("references[0].camera needs schema_version 3", self._refused(block))


def _text_block(texts=("The wing's root carries a 4 mm peg; the heart core a 4.2 mm socket.",
                       "The wing stays inside its swing drum; the housing stays out of it.",
                       "The heart core's pinion meshes with the sector on the wing's root.")):
    """A schema 4 contract: schema 3 plus each Interface's text (ADR 0084)."""

    block = _interfaces_block()
    block["schema_version"] = 4
    block["references"][0]["camera"] = [-60, 20]
    block["references"][1]["camera"] = [0, 90]
    for interface, text in zip(block["interfaces"], texts):
        if text is not None:
            interface["text"] = text
    return block


class InterfaceTextTest(unittest.TestCase):
    """ADR 0084: a schema 4 Interface states in words what it imposes on each
    Component it joins."""

    def _refused(self, block):
        with self.assertRaises(ContractError) as caught:
            parse_design_contract(_contract_text(block))
        return str(caught.exception)

    def test_every_interface_carries_its_text_and_seals_it(self):
        block = _text_block()
        contract = parse_design_contract(_contract_text(block))
        self.assertEqual(contract.schema_version, 4)
        self.assertEqual(contract.interfaces[0].text, block["interfaces"][0]["text"])
        self.assertEqual(contract.to_dict()["interfaces"], block["interfaces"])
        # Schema 4 keeps schema 3's Reference Cameras.
        self.assertEqual([item.camera for item in contract.references], [(-60.0, 20.0), (0.0, 90.0)])

    def test_text_has_no_maximum_length(self):
        block = _text_block(texts=("x" * 20_000, "y", "z"))
        self.assertEqual(len(parse_design_contract(_contract_text(block)).interfaces[0].text), 20_000)

    def test_an_interface_without_non_empty_text_is_refused_naming_it(self):
        for text in (None, "", "   ", 3, ["a"]):
            with self.subTest(text=text):
                block = _text_block(texts=(None, "y", "z"))
                if text is not None:
                    block["interfaces"][0]["text"] = text
                message = self._refused(block)
                self.assertIn("interfaces[0].text must state", message)
                self.assertNotIn("interfaces[1]", message)

    def test_schema_4_still_needs_every_reference_camera(self):
        block = _text_block()
        del block["references"][1]["camera"]
        self.assertIn("references[1].camera must be [AZ, EL]", self._refused(block))

    def test_schema_1_to_3_parse_as_before_and_refuse_interface_text(self):
        for block in (_interfaces_block(), _camera_block()):
            with self.subTest(schema=block["schema_version"]):
                contract = parse_design_contract(_contract_text(block))
                self.assertTrue(all(item.text is None for item in contract.interfaces))
                self.assertEqual(contract.to_dict()["interfaces"], block["interfaces"])
        block = _interfaces_block()
        block["interfaces"][0]["text"] = "A peg in a socket."
        message = self._refused(block)
        self.assertIn("interfaces[0].text needs schema_version 4", message)
        self.assertNotIn("does not take", message)
        camera = _camera_block(interfaces=_text_block()["interfaces"])
        self.assertIn("text needs schema_version 4", self._refused(camera))

    def test_an_unknown_schema_is_refused(self):
        self.assertIn("schema_version must be 1, 2, 3 or 4", self._refused(_block(schema_version=5)))
