import unittest

from inventor_workshop import WorkshopTools
from profile import build_workshop, create_wish


class LeoProfileTest(unittest.TestCase):
    def test_leo_uses_shared_make_and_playtest_by_default(self):
        def shared_make(context):
            raise AssertionError("preview must not execute Make")

        def shared_playtest(context):
            raise AssertionError("preview must not execute Playtest")

        workshop = build_workshop(
            tools=WorkshopTools(make=shared_make, playtest=shared_playtest)
        )
        self.assertEqual(workshop.lane, "invented-games")
        self.assertEqual(workshop.customization_level, "taste-only")
        wish = create_wish("first-game", "I wish for a tense duel for our table.")
        preview = workshop.preview(wish)
        self.assertEqual(preview["wish"], wish.to_dict())
        self.assertEqual(preview["taste"]["sha256"], workshop.taste.sha256)


if __name__ == "__main__":
    unittest.main()
