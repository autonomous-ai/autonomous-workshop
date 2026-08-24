import tempfile
import unittest
from pathlib import Path

from inventor_workshop.errors import ContractError
from inventor_workshop.make import Wish
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import (
    PLAYTHING_LANES,
    WORKSHOP_JOBS,
    ToyBlueprint,
    playful_make_request,
)


class ToyBlueprintTest(unittest.TestCase):
    def test_first_workshop_has_exactly_five_jobs_and_five_plaything_lanes(self):
        self.assertEqual(
            WORKSHOP_JOBS,
            ("wish", "make", "playtest", "instructions", "deliver"),
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

        self.assertIn("make.classic", {task.key for task in classics.tasks})
        self.assertIn("playtest.classic", {task.key for task in classics.tasks})
        self.assertNotIn("make.rules", {task.key for task in classics.tasks})

        game_keys = {task.key for task in games.tasks}
        self.assertIn("make.rules", game_keys)
        self.assertIn("playtest.game", game_keys)
        self.assertIn("playtest.human-table", game_keys)
        self.assertNotIn("playtest.people", game_keys)
        self.assertTrue(
            next(task for task in games.tasks if task.key == "playtest.human-table").external
        )

        self.assertIn("make.motion", {task.key for task in machines.tasks})
        self.assertIn("playtest.motion", {task.key for task in machines.tasks})
        self.assertIn("make.science", {task.key for task in science.tasks})
        self.assertIn("playtest.science", {task.key for task in science.tasks})
        self.assertIn("make.world", {task.key for task in worlds.tasks})
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
            self.assertIn("interchangeable", request["brief"]["download_bar"])
            self.assertIn("Cool beats cute", request["brief"]["tone"])
            self.assertIn("STEP", request["brief"]["deliverables"])

    def test_unknown_product_lane_fails_closed(self):
        with self.assertRaises(ContractError):
            ToyBlueprint.for_lane("organizer")


if __name__ == "__main__":
    unittest.main()
