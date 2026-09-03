import hashlib
import unittest

from workshop.daydream.contracts import DAYDREAM_IDEA_KIND
from workshop.daydream.prompt import (
    DAYDREAM_CONSTITUTION,
    DAYDREAM_CONSTITUTION_SHA256,
    build_daydream_prompt,
)
from workshop.daydream.seeds import DaydreamSeed
from workshop.errors import ContractError


class PromptTest(unittest.TestCase):
    def test_prompt_names_inventor_seed_files_and_constitution(self):
        seed = DaydreamSeed(moment="a bus stop in the cold", twist="it counts something")
        prompt = build_daydream_prompt(
            inventor_name="Pico Press",
            inventor_id="pico-press",
            seed=seed,
            notebook_count=3,
            prior_work_count=22,
        )
        for expected in (
            "Pico Press",
            "pico-press",
            "a bus stop in the cold",
            "it counts something",
            "TASTE.md",
            "PRIOR-WORK.md",
            "NOTEBOOK.md",
            "22 toys",
            "3 ideas",
            "work/IDEA.json",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, prompt)
        self.assertTrue(prompt.endswith(DAYDREAM_CONSTITUTION))
        self.assertLess(len(prompt.encode("utf-8")), 1024 * 1024)

    def test_constitution_is_specific_and_its_identity_is_stable(self):
        self.assertEqual(
            DAYDREAM_CONSTITUTION_SHA256,
            hashlib.sha256(DAYDREAM_CONSTITUTION.encode("utf-8")).hexdigest(),
        )
        for expected in (
            DAYDREAM_IDEA_KIND,
            "work/IDEA.json",
            "TASTE.md",
            "PRIOR-WORK.md",
            "NOTEBOOK.md",
            "web search",
            "prior_art",
            "taste_fit",
            "parts_estimate",
            "keywords",
            "12",
            "0.4 mm nozzle",
            "0.8 mm minimum wall",
            "No electronics",
            "^[a-z0-9][a-z0-9-]{1,31}$",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, DAYDREAM_CONSTITUTION)

    def test_prompt_validates_its_inputs(self):
        seed = DaydreamSeed(moment="x", twist="y")
        with self.assertRaises(ContractError):
            build_daydream_prompt(
                inventor_name="Pico Press",
                inventor_id="pico-press",
                seed=seed,
                notebook_count=-1,
                prior_work_count=0,
            )
        with self.assertRaises(ContractError):
            build_daydream_prompt(
                inventor_name="Pico Press",
                inventor_id="pico-press",
                seed={"moment": "x", "twist": "y"},
                notebook_count=0,
                prior_work_count=0,
            )
        with self.assertRaises(ContractError):
            build_daydream_prompt(
                inventor_name="Pico Press",
                inventor_id="Pico Press",
                seed=seed,
                notebook_count=0,
                prior_work_count=0,
            )


if __name__ == "__main__":
    unittest.main()
