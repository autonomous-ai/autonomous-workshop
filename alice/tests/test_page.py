import unittest

from alice.page import verify_factory_product_page


def complete_design():
    return {
        "id": "d1",
        "slug": "river-council",
        "title": "River Council",
        "description": "A complete game.",
        "status": "public",
        "category": {"slug": "games", "name": "Games"},
        "project_url": "https://cdn.example/project/",
        "primary_thumbnail_url": "https://cdn.example/hero.png",
        "thumbnail_urls": ["https://cdn.example/hero.png"],
        "listing": {
            "sku": "VB-1",
            "price_cents": 4900,
            "currency": "usd",
            "active": True,
            "ships_within_days": 14,
        },
        "use_case": {
            "label": "At the table",
            "body": "A concrete player experience.",
            "image": "https://cdn.example/use.png",
        },
        "story_blocks": [
            {"lead": "One", "body": "Body", "hero_image": "https://cdn.example/1.png"},
            {"lead": "Two", "body": "Body", "hero_image": "https://cdn.example/2.png"},
            {"lead": "Three", "body": "Body", "hero_image": "https://cdn.example/3.png"},
        ],
        "print_specs": {
            "dimensions_mm": {"x": 200, "y": 200, "z": 60},
            "weight_g": 400,
            "print_time_minutes": 900,
            "part_count": 24,
            "materials": ["PETG"],
        },
        "assembly_parts": [{"part": "board.stl", "color": "#fff"}],
    }


class PageTests(unittest.TestCase):
    def test_complete_pipeline_record_passes(self) -> None:
        result = verify_factory_product_page(complete_design(), expected_price_cents=4900)
        self.assertTrue(result.complete, result.failures)
        self.assertEqual(result.image_count, 5)

    def test_missing_pipeline_enrichment_fails(self) -> None:
        design = complete_design()
        design["story_blocks"] = []
        result = verify_factory_product_page(design)
        self.assertFalse(result.complete)
        self.assertIn("story_blocks_below_three", result.failures)

    def test_price_drift_fails(self) -> None:
        result = verify_factory_product_page(complete_design(), expected_price_cents=9900)
        self.assertIn("listing_price_mismatch", result.failures)

    def test_currency_drift_fails_when_usd_was_reviewed(self) -> None:
        result = verify_factory_product_page(
            complete_design(), expected_currency="USD"
        )
        self.assertIn("listing_currency_mismatch", result.failures)

    def test_missing_category_is_visible_but_does_not_block_a_complete_page(self) -> None:
        design = complete_design()
        design["category"] = None
        result = verify_factory_product_page(design)
        self.assertTrue(result.complete, result.failures)
        self.assertIn("category_missing", result.warnings)


if __name__ == "__main__":
    unittest.main()
