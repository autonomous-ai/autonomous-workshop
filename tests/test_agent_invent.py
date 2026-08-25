import tempfile
import unittest
from pathlib import Path

from inventor_workshop.agent_invent import CodexInventor
from inventor_workshop.jobs import InventContext
from inventor_workshop.make import Wish
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint
from inventor_workshop.workshop import Workshop, WorkshopTools


def action(title):
    return {
        "research": {
            "patterns": ["Wind-up walkers convert stored energy into a gait."],
            "opportunities": ["Let the dog's recognizable posture drive the gait."],
            "assumptions": ["The customer will later provide visual references."],
        },
        "directions": [
            {
                "name": "Proud trot",
                "idea": "A dog-shaped walker with a proud stepping rhythm.",
                "play": "Wind it and race it across a desk.",
                "form": "Long legs and an arched body.",
                "risks": ["Gait may be too generic."],
            },
            {
                "name": "Tail metronome",
                "idea": "The tail visibly meters each step.",
                "play": "Predict the next footfall from the tail.",
                "form": "A compact body with an oversized kinetic tail.",
                "risks": ["Tail may steal attention from the dog."],
            },
            {
                "name": "Desk trail",
                "idea": "A walker that traces a characteristic curved path.",
                "play": "Arrange desk obstacles and watch it weave.",
                "form": "Offset feet and a low recognizable silhouette.",
                "risks": ["Path tuning belongs to Make."],
            },
        ],
        "selected": {
            "title": title,
            "summary": "A Wish-specific wind-up dog whose gait carries its personality.",
            "magic": "The dog's familiar attitude appears in every step.",
            "play_pattern": "Wind, release, watch, and rearrange a desk course.",
            "industrial_design": "A low arched body, readable head, expressive tail, and four rhythmic legs.",
            "mechanical_handoff": [
                "Engineer a printable four-leg gait.",
                "Keep the dog's silhouette recognizable around the mechanism.",
            ],
        },
    }


def verdict(score, feedback):
    return {
        "dimensions": {
            "wish_fit": score,
            "taste_fit": score,
            "originality": score,
            "play": score,
            "industrial_design": score,
            "make_feasibility": score,
        },
        "feedback": [feedback],
        "hard_tensions": [],
        "assessment": feedback,
    }


class FakeCodex:
    cli_version = "9.8.7"
    reasoning_effort = "high"

    def __init__(self, model, outputs):
        self.model = model
        self.outputs = list(outputs)
        self.prompts = []

    def invoke(self, *, prompt, schema, workspace):
        self.prompts.append((prompt, schema, workspace))
        return self.outputs.pop(0)


class AgentInventTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.inventor = self.root / "inventor"
        self.inventor.mkdir()
        (self.inventor / "TASTE.md").write_text(
            "---\n"
            "name: Bob\n"
            "description: Kinetic machines where motion creates the spectacle.\n"
            "---\n"
            "# Bob's Taste\n\n"
            "Make motion the magic. Not for static character models.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def context(self):
        return InventContext(
            Wish.create("walking-dog", "A wind-up version of my dog that walks"),
            load_taste(self.inventor),
            ToyBlueprint.for_lane("moving-machines"),
            (self.root / "invent-workspace").absolute(),
        )

    def test_inventor_improves_until_the_independent_reward_reaches_goal(self):
        creator = FakeCodex("gpt-5.6-sol", [action("First dog"), action("Trotter")])
        evaluator = FakeCodex(
            "gpt-5.6-terra",
            [verdict(74, "Make the gait more specific to this dog."), verdict(91, "Ready for Make.")],
        )
        evaluator.reasoning_effort = "low"
        invented = CodexInventor(
            creator=creator,
            evaluator=evaluator,
            goal=85,
            max_steps=3,
        )(self.context())
        self.assertTrue(invented.passed)
        self.assertEqual(invented.score, 91)
        self.assertEqual(invented.concept["title"], "Trotter")
        self.assertEqual(len(invented.concept["reward_loop"]["steps"]), 2)
        self.assertIn("previous reward", creator.prompts[1][0])
        self.assertIn("Make and Playtest own those later", evaluator.prompts[0][0])

    def test_workshop_advances_to_make_only_after_invent_passes(self):
        creator = FakeCodex("gpt-5.6-sol", [action("Trotter")])
        evaluator = FakeCodex("gpt-5.6-terra", [verdict(92, "Ready for Make.")])
        evaluator.reasoning_effort = "low"
        worker = CodexInventor(creator=creator, evaluator=evaluator)
        result = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(invent=worker),
            runtime_root=self.root / "runtime",
        ).run(self.context().wish, playtest_rounds=2)
        self.assertEqual((result.status, result.job), ("waiting", "make"))
        self.assertEqual(result.needs[0].capability, "model-and-cad-maker")
        self.assertIsNotNone(result.invented)
        self.assertEqual(result.invented.concept["title"], "Trotter")
        self.assertEqual(result.to_dict()["invented"]["score"], 92)


if __name__ == "__main__":
    unittest.main()
