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
    def test_first_workshop_has_exactly_five_jobs_and_four_plaything_lanes(self):
        self.assertEqual(
            WORKSHOP_JOBS, ("wish", "make", "playtest", "docs", "deliver")
        )
        self.assertEqual(
            PLAYTHING_LANES,
            (
                "table-game",
                "desk-toy",
                "model-character",
                "puzzle-keepsake",
            ),
        )
        for lane in PLAYTHING_LANES:
            blueprint = ToyBlueprint.for_lane(lane)
            self.assertEqual(set(task.job for task in blueprint.tasks), set(WORKSHOP_JOBS))
            self.assertEqual(len(blueprint.sha256), 64)
            self.assertEqual(blueprint.to_dict()["audience"], "grown-ups-14-plus")

    def test_table_games_receive_rules_and_ai_playtest_work(self):
        table = ToyBlueprint.for_lane("table-game")
        desk = ToyBlueprint.for_lane("desk-toy")
        self.assertIn("make.rules", {task.key for task in table.tasks})
        self.assertIn("playtest.game", {task.key for task in table.tasks})
        self.assertNotIn("make.rules", {task.key for task in desk.tasks})
        self.assertNotIn("playtest.game", {task.key for task in desk.tasks})
        self.assertIn("playtest.mechanics", {task.key for task in desk.tasks})
        self.assertIn("playtest.print", {task.key for task in desk.tasks})

    def test_default_make_request_turns_utility_into_play(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor = Path(temporary)
            (inventor / "TASTE.md").write_text(
                "# Ada\n\nWarm creatures with one surprising motion.\n",
                encoding="utf-8",
            )
            taste = load_taste(inventor)
            wish = Wish.create("whale-cable-holder", "I wish my cables stayed tidy")
            request = playful_make_request(
                wish, taste, ToyBlueprint.for_lane("desk-toy")
            )
            self.assertEqual(request["wish"]["objective"], wish.objective)
            self.assertEqual(request["taste"]["sha256"], taste.sha256)
            self.assertIn("Nothing may be merely useful", request["brief"]["utility_rule"])
            self.assertIn("STEP", request["brief"]["deliverables"])

    def test_unknown_product_lane_fails_closed(self):
        with self.assertRaises(ContractError):
            ToyBlueprint.for_lane("organizer")


if __name__ == "__main__":
    unittest.main()
