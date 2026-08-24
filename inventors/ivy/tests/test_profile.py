import unittest

from profile import build_workshop, create_wish


class IvyProfileTest(unittest.TestCase):
    def test_ivy_is_a_taste_only_holdable_science_profile(self):
        workshop = build_workshop()
        self.assertEqual(workshop.lane, "holdable-science")
        self.assertEqual(workshop.customization_level, "taste-only")
        wish = create_wish("tide-clock", "I wish I could hold our beach's tide cycle.")
        preview = workshop.preview(wish)
        self.assertEqual(preview["wish"], wish.to_dict())
        self.assertEqual(preview["taste"]["sha256"], workshop.taste.sha256)


if __name__ == "__main__":
    unittest.main()
