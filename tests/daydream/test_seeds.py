import unittest

from workshop.daydream.seeds import SITUATIONS, TWISTS, DaydreamSeed, draw_seed
from workshop.errors import ContractError


class SeedTest(unittest.TestCase):
    def test_pools_are_broad_and_unique(self):
        self.assertGreaterEqual(len(SITUATIONS), 12)
        self.assertGreaterEqual(len(TWISTS), 14)
        self.assertEqual(len(set(SITUATIONS)), len(SITUATIONS))
        self.assertEqual(len(set(TWISTS)), len(TWISTS))

    def test_draw_seed_uses_the_injected_chooser(self):
        seen = []

        def choose(options):
            seen.append(tuple(options))
            return options[-1]

        seed = draw_seed(choose)
        self.assertEqual(seed, DaydreamSeed(moment=SITUATIONS[-1], twist=TWISTS[-1]))
        self.assertEqual(seen, [SITUATIONS, TWISTS])
        default = draw_seed()
        self.assertIn(default.moment, SITUATIONS)
        self.assertIn(default.twist, TWISTS)

    def test_round_trip_and_validation(self):
        seed = DaydreamSeed(moment="a bus stop in the cold", twist="it counts something")
        self.assertEqual(DaydreamSeed.parse(seed.to_dict()), seed)
        with self.assertRaises(ContractError):
            DaydreamSeed.parse({"moment": "x"})
        with self.assertRaises(ContractError):
            DaydreamSeed.parse({"moment": "x", "twist": "y", "extra": 1})
        with self.assertRaises(ContractError):
            DaydreamSeed(moment="", twist="y")
        with self.assertRaises(ContractError):
            DaydreamSeed(moment="x", twist="y\nz")


if __name__ == "__main__":
    unittest.main()
