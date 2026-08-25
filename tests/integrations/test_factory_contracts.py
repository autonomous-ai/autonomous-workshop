import unittest

from workshop.errors import ContractError
from workshop.integrations.factory_contracts import (
    bind_factory_assembly_parts,
    validate_factory_assembly_inventory,
    validate_factory_assembly_parts,
)


class FactoryContractTest(unittest.TestCase):
    def setUp(self):
        self.inventory = [
            {"order": 0, "mesh_name": "body", "part": "body.stl"},
            {"order": 1, "mesh_name": "axle", "part": "axle.stl"},
        ]
        self.palette = [
            {**self.inventory[0], "color": "#AABBCC"},
            {**self.inventory[1], "color": "#102030"},
        ]

    def test_inventory_and_palette_are_canonical_and_bound(self):
        self.assertEqual(
            validate_factory_assembly_inventory(list(reversed(self.inventory))),
            self.inventory,
        )
        expected = [
            {**self.inventory[0], "color": "#aabbcc"},
            {**self.inventory[1], "color": "#102030"},
        ]
        self.assertEqual(validate_factory_assembly_parts(self.palette), expected)
        self.assertEqual(
            bind_factory_assembly_parts(self.palette, self.inventory), expected
        )

    def test_only_colors_may_change_after_import(self):
        changed = [dict(self.palette[0]), dict(self.palette[1])]
        changed[1]["mesh_name"] = "replacement"
        with self.assertRaisesRegex(ContractError, "only colors may vary"):
            bind_factory_assembly_parts(changed, self.inventory)

    def test_legacy_shorthand_is_read_only_compatibility(self):
        shorthand = [{"part": "body.stl", "color": "#AABBCC"}]
        with self.assertRaisesRegex(ContractError, "full occurrence"):
            validate_factory_assembly_parts(shorthand)
        self.assertEqual(
            validate_factory_assembly_parts(
                shorthand, allow_legacy_shorthand=True
            ),
            [{"part": "body.stl", "color": "#aabbcc"}],
        )


if __name__ == "__main__":
    unittest.main()
