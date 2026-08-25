import unittest

from workshop.errors import ContractError
from workshop.product import attribute_product_description


class ProductDescriptionAttributionTest(unittest.TestCase):
    def test_attribution_preserves_copy_and_has_one_canonical_terminal_credit(self):
        copy = "  A pocket machine with one surprising motion.\nSecond paragraph.  \n"
        attributed = attribute_product_description(copy, "Alice")
        self.assertEqual(
            attributed,
            "  A pocket machine with one surprising motion.\n"
            "Second paragraph.\n\n"
            "By Alice.",
        )
        self.assertFalse(attributed.endswith("\n"))
        self.assertEqual(attributed.count("By Alice."), 1)

    def test_attribution_is_idempotent_and_collapses_repeated_terminal_credit(self):
        canonical = "A tiny world made for this Wish.\n\nBy Eve."
        self.assertEqual(attribute_product_description(canonical, "Eve"), canonical)
        repeated = canonical + "\n\nBy Eve.  \n"
        self.assertEqual(attribute_product_description(repeated, "Eve"), canonical)
        self.assertEqual(
            attribute_product_description(repeated, "Eve").count("By Eve."), 1
        )

    def test_attribution_does_not_rewrite_another_inventors_copy(self):
        original = "An earlier edition.\n\nBy Bob."
        self.assertEqual(
            attribute_product_description(original, "Ivy"),
            original + "\n\nBy Ivy.",
        )

    def test_attribution_rejects_missing_copy_or_unsafe_inventor_name(self):
        with self.assertRaises(ContractError):
            attribute_product_description("", "Alice")
        with self.assertRaises(ContractError):
            attribute_product_description("By Alice.", "Alice")
        with self.assertRaises(ContractError):
            attribute_product_description("A real description.", "Alice\nBob")


if __name__ == "__main__":
    unittest.main()
