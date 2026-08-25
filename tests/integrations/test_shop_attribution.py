import unittest

from workshop.errors import ContractError
from workshop.integrations.shop import _normalize_shop_listing


class ShopAttributionTest(unittest.TestCase):
    def test_shop_listing_applies_attribution_before_its_size_limit(self):
        listing = _normalize_shop_listing(
            {"title": "Pocket Machine", "description": "One surprising motion."},
            inventor_name="Bob",
        )
        self.assertEqual(
            listing["description"], "One surprising motion.\n\nBy Bob."
        )
        with self.assertRaisesRegex(ContractError, "description"):
            _normalize_shop_listing(
                {"title": "Too Long", "description": "x" * 19_995},
                inventor_name="Bob",
            )


if __name__ == "__main__":
    unittest.main()
