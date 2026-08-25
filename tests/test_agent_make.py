import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.agent_make import CodexMaker
from inventor_workshop.cad import inspect_stl_path
from inventor_workshop.errors import ArtifactError
from inventor_workshop.jobs import InventContext, Invented, MakeContext, WaitingFor
from inventor_workshop.make import Wish
from inventor_workshop.reward_loop import json_sha256
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint


def make_action(title="Orbit Press", *, overlap=False):
    second_x = 30 if overlap else 78
    return {
        "title": title,
        "summary": "A Wish-shaped desktop press assembled from three bold printable parts.",
        "interaction": "Turn the round handle and slide the marker through a short track.",
        "mechanical_principle": "A hand-turned wheel gives a tactile index for a separate sliding marker.",
        "assembly": [
            "Place the base on a stable table.",
            "Seat the wheel and marker in their labelled positions after printing.",
        ],
        "instructions": "Arrange the three printed pieces as shown, turn the wheel, and move the marker one station per turn.",
        "parts": [
            {
                "part_id": "base",
                "name": "one base",
                "purpose": "Supports the desktop interaction.",
                "shape": "box",
                "size_mm": {"x": 48, "y": 36, "z": 5},
                "print_center_mm": {"x": 28, "y": 28},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 80, "y": 80, "z": 0},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            },
            {
                "part_id": "index-wheel",
                "name": "one index wheel",
                "purpose": "Provides the hand-turned index.",
                "shape": "cylinder",
                "size_mm": {"x": 30, "y": 30, "z": 6},
                "print_center_mm": {"x": second_x, "y": 28},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 80, "y": 80, "z": 8},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            },
            {
                "part_id": "marker",
                "name": "one sliding marker",
                "purpose": "Marks progress through the interaction.",
                "shape": "cylinder",
                "size_mm": {"x": 14, "y": 14, "z": 8},
                "print_center_mm": {"x": 108, "y": 28},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 108, "y": 80, "z": 0},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            },
        ],
        "classic_spec": {
            "enabled": False,
            "known_game": "not applicable",
            "rules_reference": "not applicable",
            "rules_unchanged": False,
        },
        "game_spec": {
            "enabled": False,
            "title": "not applicable",
            "starting_tokens": 7,
            "max_take": 3,
            "last_take_wins": True,
            "theme": "not applicable",
            "token_part_ids": [],
        },
        "motion_spec": {
            "enabled": True,
            "moving_part_id": "index-wheel",
            "axis": "z",
            "sweep_degrees": 360,
            "minimum_aabb_clearance_mm": 1,
        },
        "design_limitations": [
            "This MVP does not yet model the final axle or sliding fit.",
        ],
    }


def verdict(score, feedback="Ready for digital Make."):
    return {
        "dimensions": {
            "concept_fidelity": score,
            "taste_fit": score,
            "interaction": score,
            "mechanical_coherence": score,
            "manufacturing_review": score,
        },
        "feedback": [feedback],
        "hard_tensions": [],
        "assessment": feedback,
    }


def game_action():
    value = make_action("Seven Sparks")
    parts = []
    for index in range(7):
        part_id = "spark-%d" % (index + 1)
        parts.append(
            {
                "part_id": part_id,
                "name": "spark token %d" % (index + 1),
                "purpose": "One physical token in the shared finite supply.",
                "shape": "cylinder",
                "size_mm": {"x": 12, "y": 12, "z": 4},
                "print_center_mm": {"x": 14 + index * 18, "y": 18},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 70 + index * 14, "y": 80, "z": 0},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            }
        )
    value["parts"] = parts
    value["game_spec"] = {
        "enabled": True,
        "title": "Seven Sparks",
        "starting_tokens": 7,
        "max_take": 3,
        "last_take_wins": True,
        "theme": "Players coax the final spark from a shared constellation.",
        "token_part_ids": [part["part_id"] for part in parts],
    }
    value["motion_spec"] = {
        "enabled": False,
        "moving_part_id": "",
        "axis": "z",
        "sweep_degrees": 1,
        "minimum_aabb_clearance_mm": 0,
    }
    return value


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


class AgentMakeTest(unittest.TestCase):
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
            "# Bob's Taste\n\nMake motion the magic. Not for static character models.\n",
            encoding="utf-8",
        )
        self.taste = load_taste(self.inventor)
        self.wish = Wish.create(
            "orbit-press",
            "A hand-operated desk toy where a tiny moon advances around my anniversary date",
            constraints={"lane": "moving-machines"},
            context={"inventor_id": "bob"},
        )
        self.blueprint = ToyBlueprint.for_lane("moving-machines")
        self.invented = Invented(
            wish_sha256=json_sha256(self.wish.to_dict()),
            taste_sha256=self.taste.sha256,
            lane=self.blueprint.lane,
            concept={
                "title": "Anniversary Orbit",
                "summary": "A hand-driven orbital desk toy.",
                "mechanical_handoff": ["Make the advance tactile and visible."],
            },
            score=91,
            target_score=85,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def context(self, workspace="make"):
        return MakeContext(
            self.wish,
            self.taste,
            self.blueprint,
            self.invented,
            1,
            (self.root / workspace).absolute(),
            (),
            2,
        )

    def game_context(self, workspace="game-make"):
        wish = Wish.create(
            "seven-sparks",
            "A tiny strategy game about seven sparks from our first studio",
            constraints={"lane": "invented-games"},
            context={"inventor_id": "leo"},
        )
        blueprint = ToyBlueprint.for_lane("invented-games")
        invented = Invented(
            wish_sha256=json_sha256(wish.to_dict()),
            taste_sha256=self.taste.sha256,
            lane=blueprint.lane,
            concept={"title": "Seven Sparks", "summary": "A finite shared-supply strategy game."},
            score=90,
            target_score=85,
        )
        return MakeContext(
            wish,
            self.taste,
            blueprint,
            invented,
            1,
            (self.root / workspace).absolute(),
            (),
            2,
        )

    def worker(self, actions, verdicts, **kwargs):
        creator = FakeCodex("gpt-5.6-terra", actions)
        evaluator = FakeCodex("gpt-5.6-luna", verdicts)
        evaluator.reasoning_effort = "low"
        return CodexMaker(creator=creator, evaluator=evaluator, **kwargs), creator, evaluator

    def test_make_improves_then_writes_exact_inspected_printable_stls(self):
        worker, creator, evaluator = self.worker(
            [make_action("First Press"), make_action("Orbit Press")],
            [verdict(72, "Tie the wheel more closely to the Wish."), verdict(92)],
        )
        made = worker(self.context())

        self.assertEqual(made.product["title"], "Orbit Press")
        self.assertFalse(made.product["physical_prototype"])
        self.assertEqual(len(creator.prompts), 2)
        self.assertIn("previous reward", creator.prompts[1][0])
        self.assertIn("may not upgrade it", evaluator.prompts[0][0])
        self.assertEqual(
            (made.artifact_root / "assembled.stl").read_bytes(),
            (made.artifact_root / "cad" / "product.stl").read_bytes(),
        )
        self.assertNotEqual(
            (made.artifact_root / "assembled.stl").read_bytes(),
            (made.artifact_root / "validation" / "print-plate.stl").read_bytes(),
        )
        receipt = inspect_stl_path(
            made.artifact_root / "assembled.stl", expected_shell_count=3
        )
        self.assertEqual(receipt.status, "passed")
        print_receipt = inspect_stl_path(
            made.artifact_root / "validation" / "print-plate.stl", expected_shell_count=3
        )
        self.assertEqual(print_receipt.status, "passed")
        for part_id in ("base", "index-wheel", "marker"):
            part_receipt = inspect_stl_path(
                made.artifact_root / "validation" / "parts" / (part_id + ".stl"),
                expected_shell_count=1,
            )
            self.assertEqual(part_receipt.status, "passed")
        geometry = json.loads(
            (made.artifact_root / "validation" / "digital-geometry.json").read_text(encoding="utf-8")
        )
        self.assertTrue(geometry["passed"])
        self.assertEqual(geometry["print_plate"]["status"], "passed")
        self.assertEqual(geometry["assembled_presentation"]["status"], "passed")
        self.assertEqual(geometry["motion"]["status"], "passed")
        self.assertIn("slicer success or support requirements", geometry["not_proven"])
        paths = {entry.path for entry in made.artifact_manifest.entries}
        self.assertIn("cad/design.json", paths)
        self.assertIn("validation/digital-geometry.json", paths)
        self.assertIn("validation/parts/base.stl", paths)
        self.assertIn("validation/print-plate.stl", paths)
        self.assertIn("cad/FORMAT-LIMITATIONS.md", paths)
        self.assertIn("playtest/mechanical.json", paths)
        self.assertIn("playtest/print.json", paths)
        self.assertIn("playtest/motion.json", paths)
        handoff_stls = sorted(
            path for path in paths if path.endswith(".stl") and not path.startswith("validation/")
        )
        self.assertEqual(handoff_stls, ["assembled.stl", "cad/product.stl"])

    def test_deterministic_action_produces_identical_content_address(self):
        first, _, _ = self.worker([make_action()], [verdict(95)])
        second, _, _ = self.worker([make_action()], [verdict(95)])
        made_one = first(self.context("make-one"))
        made_two = second(self.context("make-two"))
        self.assertEqual(made_one.artifact_sha256, made_two.artifact_sha256)

    def test_geometry_failure_cannot_be_overruled_by_model_scores(self):
        worker, _, _ = self.worker(
            [make_action(overlap=True), make_action(overlap=True)],
            [verdict(100), verdict(100)],
            max_steps=2,
        )
        with self.assertRaises(WaitingFor) as caught:
            worker(self.context())
        self.assertEqual(
            caught.exception.needs[0].capability,
            "mechanical-design-target-score",
        )
        self.assertFalse((self.context().workspace / "artifact").exists())

    def test_sealed_made_detects_later_mesh_mutation(self):
        worker, _, _ = self.worker([make_action()], [verdict(95)])
        made = worker(self.context())
        (made.artifact_root / "assembled.stl").write_bytes(b"changed")
        with self.assertRaises(ArtifactError):
            made.assert_current()

    def test_invented_game_seals_full_rules_and_runs_one_thousand_seeded_games(self):
        worker, _, _ = self.worker([game_action()], [verdict(95)])
        made = worker(self.game_context())
        simulator = made.artifact_root / "game" / "simulate.py"
        request_path = self.root / "simulation-request.json"
        output_path = self.root / "simulation-output.json"
        styles = ["optimizing", "social", "exploratory", "adversarial"]
        request = {
            "protocol": "workshop-seeded-games-v1",
            "artifact_sha256": made.artifact_sha256,
            "requested_games": 1000,
            "base_seed": 260825,
            "games": [
                {
                    "index": index,
                    "seed": 260825 + index,
                    "player_styles": [styles[index % 4], styles[(index + 1) % 4]],
                }
                for index in range(1000)
            ],
        }
        request_path.write_text(json.dumps(request), encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(simulator),
                "--request",
                str(request_path),
                "--output",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(result["completed_games"], 1000)
        self.assertEqual(result["issues"], [])
        self.assertTrue(all(game["completed"] for game in result["games"]))
        rules = json.loads(
            (made.artifact_root / "game" / "rules.json").read_text(encoding="utf-8")
        )
        self.assertEqual(rules["termination_bound_turns"], 7)
        self.assertIn("There are no ties", (made.artifact_root / "game" / "RULES.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
