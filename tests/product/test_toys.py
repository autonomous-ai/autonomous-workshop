import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.wish import Wish
from workshop.contributors.taste import load_taste
from workshop.product import (
    PLAYTHING_LANES,
    ReviewsPolicy,
    WORKSHOP_JOBS,
    ToyBlueprint,
    playful_make_request,
)


class ToyBlueprintTest(unittest.TestCase):
    def test_workshop_has_six_jobs_and_five_plaything_lanes(self):
        self.assertEqual(
            WORKSHOP_JOBS,
            ("wish", "invent", "make", "playtest", "release", "deliver"),
        )
        self.assertEqual(
            PLAYTHING_LANES,
            (
                "classics-made-yours",
                "invented-games",
                "moving-machines",
                "holdable-science",
                "little-worlds",
            ),
        )
        for lane in PLAYTHING_LANES:
            blueprint = ToyBlueprint.for_lane(lane)
            self.assertEqual(set(task.job for task in blueprint.tasks), set(WORKSHOP_JOBS))
            self.assertEqual(len(blueprint.sha256), 64)
            self.assertEqual(blueprint.to_dict()["audience"], "grown-ups-14-plus")

    def test_each_craft_receives_its_distinct_make_and_playtest_work(self):
        classics = ToyBlueprint.for_lane("classics-made-yours")
        games = ToyBlueprint.for_lane("invented-games")
        machines = ToyBlueprint.for_lane("moving-machines")
        science = ToyBlueprint.for_lane("holdable-science")
        worlds = ToyBlueprint.for_lane("little-worlds")

        self.assertIn("invent.classic", {task.key for task in classics.tasks})
        self.assertIn("playtest.classic", {task.key for task in classics.tasks})
        self.assertNotIn("invent.rules", {task.key for task in classics.tasks})

        game_keys = {task.key for task in games.tasks}
        self.assertIn("invent.rules", game_keys)
        self.assertIn("playtest.game", game_keys)
        self.assertNotIn("playtest.human-table", game_keys)
        self.assertNotIn("playtest.people", game_keys)
        self.assertNotIn("playtest.prototype", game_keys)
        self.assertEqual(
            games.to_dict()["post_delivery_reviews"]["feeds"], "future-make"
        )

        self.assertIn("invent.motion", {task.key for task in machines.tasks})
        self.assertIn("playtest.motion", {task.key for task in machines.tasks})
        self.assertIn("invent.science", {task.key for task in science.tasks})
        self.assertIn("playtest.science", {task.key for task in science.tasks})
        self.assertIn("invent.world", {task.key for task in worlds.tasks})
        self.assertIn("playtest.likeness", {task.key for task in worlds.tasks})

    def test_default_make_request_turns_utility_into_play(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor = Path(temporary)
            (inventor / "TASTE.md").write_text(
                "---\n"
                "name: Ada\n"
                "description: Warm creatures with one surprising motion.\n"
                "---\n"
                "# Ada\n\n"
                "Warm creatures with one surprising motion.\n",
                encoding="utf-8",
            )
            taste = load_taste(inventor)
            wish = Wish.create("whale-cable-holder", "I wish my cables stayed tidy")
            request = playful_make_request(
                wish, taste, ToyBlueprint.for_lane("moving-machines")
            )
            self.assertEqual(request["wish"]["objective"], wish.objective)
            self.assertEqual(request["taste"]["sha256"], taste.sha256)
            self.assertIn("Nothing may be merely useful", request["brief"]["utility_rule"])
            self.assertIn("interchangeable", request["brief"]["product_bar"])
            self.assertIn("Cool beats cute", request["brief"]["tone"])
            self.assertIn("STEP", request["brief"]["deliverables"])
            self.assertIn("AI agents", request["brief"]["playtest_rule"])
            self.assertIn("after Deliver", request["brief"]["reviews_rule"])

    def test_product_accepts_a_structural_taste_binding(self):
        class ProductTaste:
            def assert_valid(self):
                return None

            def to_binding(self):
                return {"schema_version": 1, "sha256": "a" * 64}

        request = playful_make_request(
            Wish.create("structural", "I wish for a surprising small machine"),
            ProductTaste(),
            ToyBlueprint.for_lane("moving-machines"),
        )
        self.assertEqual(request["taste"]["sha256"], "a" * 64)

    def test_unknown_product_lane_fails_closed(self):
        with self.assertRaises(ContractError):
            ToyBlueprint.for_lane("organizer")

    def test_reviews_policy_cannot_become_a_creation_job_or_rewrite_delivery(self):
        with self.assertRaisesRegex(ContractError, "preserve the delivered revision"):
            ReviewsPolicy(feeds="make", mutates_delivered_revision=True)


if __name__ == "__main__":
    unittest.main()
