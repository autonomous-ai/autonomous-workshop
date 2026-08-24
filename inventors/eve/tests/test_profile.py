import unittest

from profile import build_workshop, create_wish


class EveProfileTest(unittest.TestCase):
    def test_eve_is_a_taste_only_little_worlds_profile(self):
        workshop = build_workshop()
        self.assertEqual(workshop.lane, "little-worlds")
        self.assertEqual(workshop.customization_level, "taste-only")
        wish = create_wish("rig-world", "I wish my gaming rig were an engine room.")
        preview = workshop.preview(wish)
        self.assertEqual(preview["wish"], wish.to_dict())
        self.assertEqual(preview["taste"]["sha256"], workshop.taste.sha256)


if __name__ == "__main__":
    unittest.main()
