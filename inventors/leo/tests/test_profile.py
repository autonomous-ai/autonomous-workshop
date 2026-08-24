import unittest

from profile import build_workshop, create_wish


class LeoProfileTest(unittest.TestCase):
    def test_leo_owns_invented_game_make_and_playtest(self):
        workshop = build_workshop()
        self.assertEqual(workshop.lane, "invented-games")
        self.assertEqual(workshop.customization_level, "custom-playtest")
        wish = create_wish("first-game", "I wish for a tense duel for our table.")
        preview = workshop.preview(wish)
        self.assertEqual(preview["wish"], wish.to_dict())
        self.assertEqual(preview["taste"]["sha256"], workshop.taste.sha256)


if __name__ == "__main__":
    unittest.main()
