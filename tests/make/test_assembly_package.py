from __future__ import annotations

import json
import unittest

from workshop.errors import ContractError
from workshop.make.assembly_package import (
    ASSEMBLY_PACKAGE_KIND,
    IDENTITY_TRANSFORM,
    AssemblyPackage,
    is_assembly_package,
    missing_production_parts,
    read_assembly_package,
    srgb_channels_hex,
    validate_production_parts,
)


def quarterhoot_package(**overrides):
    """A package shaped like the one cadgen sealed for the Quarterhoot toy."""

    owl_transform = [
        0.8666791601115641, -0.4988659473529074, 0.0, 0.0,
        0.4988659473529074, 0.8666791601115641, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]
    document = {
        "schemaVersion": 2,
        "profile": "index",
        "entryKind": "assembly",
        "kind": ASSEMBLY_PACKAGE_KIND,
        "packageSchemaVersion": 3,
        "rootName": "quarterhoot",
        "units": "mm",
        "components": {"60a16fdb637ed3c4": {"glb": "components/60a16fdb637ed3c4.glb"}},
        "occurrences": [
            {
                "id": "o1.1.1",
                "name": "reversible_nest",
                "component": "60a16fdb637ed3c4",
                "transform": list(IDENTITY_TRANSFORM),
                "color": [0.3, 0.52, 0.62, 1.0],
            },
            {
                "id": "o1.2.1",
                "name": "owl_follower",
                "component": "387aeca90a53010f",
                "transform": owl_transform,
                "color": [0.82, 0.51, 0.18, 1.0],
            },
        ],
        "stats": {"occurrenceCount": 2, "shapeCount": 2},
    }
    document.update(overrides)
    return document


def encode(document) -> bytes:
    return (json.dumps(document, sort_keys=True) + "\n").encode("utf-8")


class ReadAssemblyPackageTest(unittest.TestCase):
    def test_quarterhoot_shaped_package_reads_both_occurrences(self):
        package = read_assembly_package(encode(quarterhoot_package()))

        self.assertIsInstance(package, AssemblyPackage)
        self.assertEqual(package.root_name, "quarterhoot")
        self.assertEqual(package.units, "mm")
        self.assertTrue(package.is_multipart)
        self.assertEqual(package.occurrence_count, 2)
        self.assertEqual(
            [item.name for item in package.occurrences],
            ["reversible_nest", "owl_follower"],
        )
        self.assertEqual(
            package.production_stl_paths,
            ("parts/reversible_nest.stl", "parts/owl_follower.stl"),
        )
        owl = package.occurrences[1]
        self.assertEqual(owl.translation, (0.0, 0.0, 0.0))
        self.assertAlmostEqual(owl.transform[0], 0.8666791601115641)
        self.assertEqual(owl.color, (0.82, 0.51, 0.18, 1.0))

    def test_colours_are_reported_as_the_srgb_a_viewer_shows(self):
        package = read_assembly_package(encode(quarterhoot_package()))

        self.assertEqual(
            package.part_colors(),
            {"reversible_nest": "#4d859e", "owl_follower": "#d1822e"},
        )
        self.assertEqual(srgb_channels_hex((1.0, 1.0, 1.0)), "#ffffff")
        with self.assertRaises(ValueError):
            srgb_channels_hex((1.2, 0.0, 0.0))

    def test_a_single_occurrence_package_is_not_multipart(self):
        document = quarterhoot_package()
        document["occurrences"] = document["occurrences"][:1]
        document["stats"] = {"occurrenceCount": 1}

        package = read_assembly_package(encode(document))

        self.assertFalse(package.is_multipart)
        self.assertEqual(missing_production_parts(package, ()), ())
        self.assertEqual(validate_production_parts(package, ()), ())

    def test_three_channel_colour_and_absent_transform_take_defaults(self):
        document = quarterhoot_package()
        document["occurrences"][0].pop("transform")
        document["occurrences"][0]["color"] = [0.5, 0.25, 0.0]
        document["occurrences"][1]["color"] = None

        package = read_assembly_package(encode(document))

        self.assertEqual(package.occurrences[0].transform, IDENTITY_TRANSFORM)
        self.assertEqual(package.occurrences[0].color, (0.5, 0.25, 0.0, 1.0))
        self.assertIsNone(package.occurrences[1].color)
        self.assertEqual(package.part_colors(), {"reversible_nest": "#804000"})

    def test_other_documents_are_not_assembly_packages(self):
        self.assertFalse(is_assembly_package({"schemaVersion": 1, "entryKind": "assembly"}))
        self.assertFalse(is_assembly_package({"kind": ASSEMBLY_PACKAGE_KIND, "schemaVersion": 1}))
        self.assertFalse(is_assembly_package("assembly-package"))
        with self.assertRaisesRegex(ContractError, "not a schemaVersion 2 assembly-package"):
            read_assembly_package(b'{"schemaVersion":1,"entryKind":"assembly","parts":[]}')

    def test_malformed_packages_are_rejected(self):
        cases = [
            ("duplicate", {"occurrences": quarterhoot_package()["occurrences"][:1] * 2}),
            ("unsafe name", None),
            ("count", {"stats": {"occurrenceCount": 3}}),
            ("transform", None),
            ("colour range", None),
            ("entry kind", {"entryKind": "sketch"}),
            ("package schema", {"packageSchemaVersion": 0}),
            ("empty", {"occurrences": []}),
        ]
        for label, overrides in cases:
            document = quarterhoot_package()
            if label == "unsafe name":
                document["occurrences"][0]["name"] = "../Owl"
            elif label == "transform":
                document["occurrences"][0]["transform"] = [1.0] * 15
            elif label == "colour range":
                document["occurrences"][0]["color"] = [1.5, 0.0, 0.0, 1.0]
            else:
                document.update(overrides)
            with self.subTest(label):
                with self.assertRaises(ContractError):
                    read_assembly_package(encode(document))

    def test_non_finite_and_duplicate_keys_are_rejected(self):
        with self.assertRaises(ContractError):
            read_assembly_package(
                encode(quarterhoot_package()).replace(b"0.82", b"NaN")
            )
        duplicated = b'{"kind":"assembly-package","schemaVersion":2,"schemaVersion":2}'
        with self.assertRaises(ContractError):
            read_assembly_package(duplicated)
        with self.assertRaises(ContractError):
            read_assembly_package(b"")

    def test_missing_production_parts_are_named(self):
        package = read_assembly_package(encode(quarterhoot_package()))

        self.assertEqual(
            missing_production_parts(package, {"parts/owl_follower.stl"}),
            ("parts/reversible_nest.stl",),
        )
        with self.assertRaisesRegex(ContractError, "parts/reversible_nest.stl"):
            validate_production_parts(package, {"parts/owl_follower.stl"})
        self.assertEqual(
            validate_production_parts(
                package, {"parts/owl_follower.stl", "parts/reversible_nest.stl"}
            ),
            ("parts/reversible_nest.stl", "parts/owl_follower.stl"),
        )


if __name__ == "__main__":
    unittest.main()
