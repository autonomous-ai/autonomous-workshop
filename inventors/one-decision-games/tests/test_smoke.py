import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from inventor_workshop import WORKSHOP_JOBS, Workshop, WorkshopTools, load_taste
from one_decision_games.__main__ import (
    build_workshop,
    create_wish,
    default_runtime_root,
    main,
)


class SmokeTest(unittest.TestCase):
    def test_profile_is_a_thin_workshop_configuration(self):
        workshop = build_workshop(tools=WorkshopTools())
        self.assertIsInstance(workshop, Workshop)
        self.assertEqual(workshop.lane, 'invented-games')
        self.assertEqual(workshop.customization_level, 'custom-playtest')
        self.assertEqual(
            tuple(WORKSHOP_JOBS),
            ("wish", "make", "playtest", "instructions", "deliver"),
        )
        profile = load_taste(Path(__file__).resolve().parents[1])
        self.assertIn("creative constitution", profile.content)

    def test_preview_is_read_only_and_run_waits_truthfully(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "workshop"
            with mock.patch.dict(os.environ, {"ONE_DECISION_GAMES_RUNTIME": str(runtime)}):
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(
                        main(("preview", "first-toy", "I wish for a tiny surprise")),
                        0,
                    )
                preview = json.loads(output.getvalue())
                self.assertEqual(preview["blueprint"]["lane"], 'invented-games')
                self.assertFalse(runtime.exists())

                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(
                        main((
                            "run",
                            "--playtest-rounds",
                            "2",
                            "waiting-toy",
                            "I wish for a tiny surprise",
                        )),
                        0,
                    )
                result = json.loads(output.getvalue())
                self.assertEqual(result["status"], "waiting")
                self.assertEqual(result["job"], "make")
                self.assertEqual(result["playtest_rounds"], 2)
                self.assertIsNone(result["artifact_sha256"])
                self.assertTrue(result["needs"])
                self.assertTrue((default_runtime_root() / "workshop.sqlite3").is_file())

    def test_wish_keeps_the_persons_words_and_lane(self):
        wish = create_wish("joy", "I wish my cable holder could make me laugh")
        self.assertEqual(wish.objective, "I wish my cable holder could make me laugh")
        self.assertEqual(wish.constraints["lane"], 'invented-games')


if __name__ == "__main__":
    unittest.main()
