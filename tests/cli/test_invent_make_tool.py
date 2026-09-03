import unittest

from tools.run_invent_make import DEFAULT_WISH, arguments


class InventMakeToolArgumentsTest(unittest.TestCase):
    def test_defaults_bind_fixed_wish_and_medium_sol_profile(self):
        parsed = arguments(())

        self.assertEqual(parsed.wish, DEFAULT_WISH)
        self.assertIn("Ho Chi Minh City", parsed.wish)
        self.assertEqual(parsed.model, "gpt-5.6-sol")
        self.assertEqual(parsed.reasoning_effort, "medium")
        self.assertEqual(parsed.stop_after, "make")
        self.assertEqual(parsed.max_rounds, 4)
        self.assertIsNone(parsed.resume)

    def test_model_effort_and_wish_are_customizable(self):
        parsed = arguments(
            (
                "A fixed comparison Wish",
                "--model",
                "gpt-5.6-luna",
                "--effort",
                "high",
                "--max-rounds",
                "7",
                "--stop-after",
                "concept",
            )
        )

        self.assertEqual(parsed.wish, "A fixed comparison Wish")
        self.assertEqual(parsed.model, "gpt-5.6-luna")
        self.assertEqual(parsed.reasoning_effort, "high")
        self.assertEqual(parsed.max_rounds, 7)
        self.assertEqual(parsed.stop_after, "concept")


if __name__ == "__main__":
    unittest.main()
