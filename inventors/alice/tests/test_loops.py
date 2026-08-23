import unittest

from alice.config import load_config
from alice.domain import CandidateState
from alice.loops import LOOPS, work_for_state


class LoopTests(unittest.TestCase):
    def test_meta_loop_contains_adversarial_review(self) -> None:
        actions = {item.action for item in LOOPS["meta"].work}
        self.assertIn("harness.adversary", actions)

    def test_library_turns_reading_into_an_experiment(self) -> None:
        actions = {item.action for item in LOOPS["library"].work}
        self.assertIn("library.adversary", actions)
        self.assertIn("library.experiment", actions)

    def test_user_book_shelf_is_loaded_into_runtime_knowledge(self) -> None:
        config = load_config()
        titles = {
            item["title"] for item in config["knowledge"]["library"]["seed_queue"]
        }
        self.assertIn("GameTek: The Math and Science of Gaming", titles)
        self.assertIn("Characteristics of Games", titles)
        self.assertIn(
            "Building Blocks of Tabletop Game Design: An Encyclopedia of Mechanisms",
            titles,
        )

    def test_rules_valid_spawns_independent_player_personas(self) -> None:
        roles = {item.role for item in work_for_state(CandidateState.RULES_VALID, "g1")}
        self.assertGreaterEqual(len(roles), 4)
        self.assertIn("exploit_hunter", roles)

    def test_candidate_id_is_bound_at_dispatch(self) -> None:
        self.assertTrue(
            all(
                item.candidate_id == "g2"
                for item in work_for_state(CandidateState.HUMAN_VALIDATED, "g2")
            )
        )


if __name__ == "__main__":
    unittest.main()
