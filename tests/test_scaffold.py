import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.errors import ContractError, StateConflict
from inventor_workshop.manifest import load_manifest
from inventor_workshop.scaffold import scaffold_inventor
from inventor_workshop.taste import load_taste_header
from inventor_workshop.toys import PLAYTHING_LANES, WORKSHOP_JOBS


class ScaffoldTest(unittest.TestCase):
    @staticmethod
    def environment(destination: Path):
        core_src = Path(__file__).resolve().parents[1] / "src"
        environment = dict(os.environ)
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(core_src), str(destination / "src"))
        )
        return environment

    def test_scaffold_has_exactly_five_physical_magic_lanes(self):
        expected = (
            "classics-made-yours",
            "invented-games",
            "moving-machines",
            "holdable-science",
            "little-worlds",
        )
        self.assertEqual(tuple(PLAYTHING_LANES), expected)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, lane in enumerate(expected):
                destination = scaffold_inventor(
                    root,
                    "lane-%d" % index,
                    "Inventor %d" % index,
                    "Wish-shaped physical magic",
                    lane=lane,
                )
                manifest = load_manifest(destination / "inventor.json")
                self.assertIn(lane, manifest.capabilities)
                taste = (destination / "TASTE.md").read_text(encoding="utf-8")
                if lane == "classics-made-yours":
                    self.assertIn("rules are already known", taste)
                    self.assertIn("Wish-shaped physical set", taste)
                if lane == "invented-games":
                    self.assertIn("experimental rules craft", taste)
                    self.assertIn("human table replay", taste)
                    self.assertIn("exact rules and printed prototype", taste)
            for index, lane in enumerate(
                (
                    "games-puzzles",
                    "table-game",
                    "desk-toy",
                    "model-character",
                    "puzzle-keepsake",
                )
            ):
                with self.subTest(old_lane=lane), self.assertRaises(ContractError):
                    scaffold_inventor(
                        root,
                        "old-lane-%d" % index,
                        "Old Inventor",
                        "old category",
                        lane=lane,
                    )

    def test_taste_only_inventor_is_thin_discoverable_and_truthful(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = scaffold_inventor(
                Path(temporary),
                "word-games",
                "Ada",
                "printable word games",
                lane="invented-games",
                level="taste-only",
            )
            manifest = load_manifest(destination / "inventor.json")
            self.assertEqual(manifest.inventor_id, "word-games")
            self.assertEqual(manifest.schema_version, 5)
            self.assertEqual(
                set(manifest.to_dict()),
                {
                    "schema_version",
                    "id",
                    "status",
                    "entrypoint",
                    "capabilities",
                    "checks",
                    "source",
                },
            )
            self.assertEqual(manifest.workshop_features, ())
            self.assertEqual(
                tuple(manifest.capabilities),
                (*WORKSHOP_JOBS, "invented-games", "taste-only"),
            )

            package = destination / "src/word_games"
            self.assertTrue((package / "__main__.py").is_file())
            self.assertFalse((package / "inventor.py").exists())
            self.assertFalse((package / "workflow.py").exists())
            entrypoint = (package / "__main__.py").read_text(encoding="utf-8")
            self.assertIn("Workshop", entrypoint)
            self.assertIn("WorkshopTools", entrypoint)

            taste = (destination / "TASTE.md").read_text(encoding="utf-8")
            self.assertIn("creative constitution", taste)
            self.assertIn("printable word games", taste)
            self.assertIn("Nothing may be merely useful", taste)
            self.assertIn("I couldn't have downloaded it before this Wish", taste)
            self.assertIn("Cool beats cute", taste)
            readme = (destination / "README.md").read_text(encoding="utf-8")
            self.assertIn(
                "Wish -> Make <-> Playtest -> Instructions -> Deliver", readme
            )
            self.assertIn("owns only `TASTE.md`", readme)
            self.assertIn("trusted checkout or product tier", readme)
            self.assertIn("No generic, download-equivalent prints", readme)
            self.assertNotIn("Make/Inspect", readme)
            self.assertIn('requires-python = ">=3.9"', (destination / "pyproject.toml").read_text())

            environment = self.environment(destination)
            observed = []
            for name in ("one", "two"):
                cwd = Path(temporary) / name
                cwd.mkdir()
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        (
                            "from word_games.__main__ import default_runtime_root; "
                            "print(default_runtime_root())"
                        ),
                    ],
                    cwd=str(cwd),
                    env=environment,
                    check=True,
                    stdout=subprocess.PIPE,
                    text=True,
                )
                observed.append(result.stdout.strip())
            self.assertEqual(observed[0], observed[1])
            self.assertEqual(Path(observed[0]), destination / ".workshop")

            profile = subprocess.run(
                [sys.executable, "-m", "word_games", "profile"],
                cwd=str(Path(temporary) / "one"),
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            profile_data = json.loads(profile.stdout)
            self.assertEqual(profile_data["customization_level"], "taste-only")
            self.assertFalse(profile_data["production_ready"])
            self.assertFalse((destination / ".workshop").exists())

            preview = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "word_games",
                    "preview",
                    "first-product",
                    "I wish for a tiny game of words",
                ],
                cwd=str(Path(temporary) / "one"),
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            preview_data = json.loads(preview.stdout)
            self.assertEqual(preview_data["blueprint"]["lane"], "invented-games")
            human_table = next(
                task
                for task in preview_data["blueprint"]["tasks"]
                if task["key"] == "playtest.human-table"
            )
            self.assertEqual(human_table["capability"], "human-replay")
            self.assertTrue(human_table["external"])
            self.assertFalse((destination / ".workshop").exists())

            run = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "word_games",
                    "run",
                    "--playtest-rounds",
                    "3",
                    "first-product",
                    "I wish for a tiny game of words",
                ],
                cwd=str(Path(temporary) / "two"),
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            waiting = json.loads(run.stdout)
            self.assertEqual(waiting["status"], "waiting")
            self.assertEqual(waiting["job"], "make")
            self.assertEqual(waiting["playtest_rounds"], 3)
            self.assertIsNone(waiting["artifact_sha256"])
            self.assertEqual(waiting["needs"][0]["capability"], "model-and-cad-maker")
            self.assertTrue((destination / ".workshop/workshop.sqlite3").is_file())

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_*.py",
                ],
                cwd=str(destination),
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

    def test_three_levels_generate_only_the_declared_creative_seams(self):
        cases = (
            ("taste-only", False, False),
            ("custom-make", True, False),
            ("custom-playtest", True, True),
        )
        with tempfile.TemporaryDirectory() as temporary:
            for index, (level, has_make, has_playtest) in enumerate(cases):
                inventor_id = "level-%d" % index
                with self.subTest(level=level):
                    destination = scaffold_inventor(
                        Path(temporary),
                        inventor_id,
                        "Inventor %d" % index,
                        "small desk surprises",
                        lane="moving-machines",
                        level=level,
                    )
                    hook = destination / "src" / inventor_id.replace("-", "_") / "inventor.py"
                    self.assertEqual(hook.exists(), has_make)
                    if hook.exists():
                        source = hook.read_text(encoding="utf-8")
                        self.assertIn("def make(", source)
                        self.assertEqual("def playtest(" in source, has_playtest)
                        self.assertIn("WaitingFor", source)
                        self.assertIn("context.playtest_rounds", source)
                    for source in sorted(destination.rglob("*.py")):
                        compile(source.read_text(encoding="utf-8"), str(source), "exec")

                    package = inventor_id.replace("-", "_")
                    environment = self.environment(destination)
                    observed = subprocess.run(
                        [sys.executable, "-m", package, "profile"],
                        cwd=str(destination),
                        env=environment,
                        check=True,
                        stdout=subprocess.PIPE,
                        text=True,
                    )
                    self.assertEqual(
                        json.loads(observed.stdout)["customization_level"], level
                    )
                    run = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            package,
                            "run",
                            "waiting-product",
                            "I wish for a playful desk companion",
                        ],
                        cwd=str(destination),
                        env=environment,
                        check=True,
                        stdout=subprocess.PIPE,
                        text=True,
                    )
                    need = json.loads(run.stdout)["needs"][0]["capability"]
                    self.assertEqual(
                        need,
                        "model-and-cad-maker" if level == "taste-only" else "inventor-make",
                    )

    def test_scaffold_rejects_unknown_scope_and_unsafe_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for inventor_id in ("class", "inventor-workshop", "tests"):
                with self.subTest(inventor_id=inventor_id), self.assertRaises(ContractError):
                    scaffold_inventor(
                        root,
                        inventor_id,
                        "Ada",
                        "word games",
                        lane="invented-games",
                    )
            with self.assertRaises(ContractError):
                scaffold_inventor(
                    root,
                    "safe-id",
                    "Ada\nInjected",
                    "word games",
                    lane="invented-games",
                )
            with self.assertRaisesRegex(ContractError, "lane"):
                scaffold_inventor(root, "no-lane", "Ada", "word games")
            with self.assertRaisesRegex(ContractError, "lane"):
                scaffold_inventor(
                    root, "bad-lane", "Ada", "word games", lane="organizer"
                )
            with self.assertRaisesRegex(ContractError, "level"):
                scaffold_inventor(
                    root,
                    "bad-level",
                    "Ada",
                    "word games",
                    lane="invented-games",
                    level="everything",
                )
            with self.assertRaisesRegex(ContractError, "conflicts"):
                scaffold_inventor(
                    root,
                    "conflict",
                    "Ada",
                    "word games",
                    lane="moving-machines",
                    template="board-game",
                )
            destination = scaffold_inventor(
                root, "existing", "Ada", "word games", lane="invented-games"
            )
            self.assertTrue(destination.is_dir())
            with self.assertRaises(StateConflict):
                scaffold_inventor(
                    root, "existing", "Ada", "word games", lane="invented-games"
                )

    def test_legacy_template_maps_to_a_toy_lane_without_entering_help_surface(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = scaffold_inventor(
                Path(temporary),
                "legacy-game",
                "Ada",
                "word games",
                template="board-game",
            )
            manifest = load_manifest(destination / "inventor.json")
            self.assertIn("invented-games", manifest.capabilities)
            self.assertIn("taste-only", manifest.capabilities)

    def test_scaffold_quotes_display_text_and_person_wish_stays_exact(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = scaffold_inventor(
                Path(temporary),
                "quote-toys",
                'Ada "The Inventor"',
                'tiny "word" toys with \\ paths',
                lane="little-worlds",
            )
            for source in sorted(destination.rglob("*.py")):
                compile(source.read_text(encoding="utf-8"), str(source), "exec")
            manifest = load_manifest(destination / "inventor.json")
            header = load_taste_header(destination)
            self.assertEqual(header.name, 'Ada "The Inventor"')
            self.assertIn('tiny "word" toys with \\ paths', header.description)
            self.assertIn('tiny "word" toys', (destination / "TASTE.md").read_text())

            environment = self.environment(destination)
            observed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from quote_toys.__main__ import create_wish; "
                        "print(create_wish('quoted', 'My exact wish').objective)"
                    ),
                ],
                cwd=temporary,
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(observed.stdout.strip(), "My exact wish")

    def test_generated_identity_resolves_from_target_like_package_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = scaffold_inventor(
                root / "source",
                "target-games",
                "Ada",
                "word games",
                lane="invented-games",
            )
            target = root / "target"
            package = target / "target_games"
            shutil.copytree(destination / "src/target_games", package)
            identity = package / "_identity"
            identity.mkdir()
            shutil.copy2(destination / "inventor.json", identity / "inventor.json")
            shutil.copy2(destination / "TASTE.md", identity / "TASTE.md")
            away = root / "away"
            away.mkdir()
            core_src = Path(__file__).resolve().parents[1] / "src"
            environment = dict(os.environ)
            environment["PYTHONPATH"] = os.pathsep.join((str(target), str(core_src)))
            observed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from target_games.__main__ import inventor_root; print(inventor_root())",
                ],
                cwd=away,
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(Path(observed.stdout.strip()), identity.resolve())


if __name__ == "__main__":
    unittest.main()
