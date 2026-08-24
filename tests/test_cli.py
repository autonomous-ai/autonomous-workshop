import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import inventor_workshop
from inventor_workshop.cli import main, parser


class CliTest(unittest.TestCase):
    def test_source_version_matches_project_metadata(self):
        project = Path(__file__).resolve().parents[1] / "pyproject.toml"
        in_project = False
        declared = None
        for raw_line in project.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line == "[project]":
                in_project = True
                continue
            if in_project and line.startswith("["):
                break
            if in_project and line.startswith("version = "):
                declared = line.removeprefix("version = ").strip('"')
                break
        self.assertEqual(declared, inventor_workshop.__version__)

    def test_workshop_is_the_canonical_cli_name(self):
        self.assertEqual(parser().prog, "workshop")
        project = (
            Path(__file__).resolve().parents[1] / "pyproject.toml"
        ).read_text(encoding="utf-8")
        self.assertIn('inventor-workshop = "inventor_workshop.cli:main"', project)
        self.assertIn('workshop = "inventor_workshop.cli:main"', project)
        self.assertNotIn("inventor-core =", project)

    def test_audit_does_not_create_or_validate_a_missing_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "missing.sqlite"
            with redirect_stderr(StringIO()):
                result = main(("audit-state", str(database), "typo"))
            self.assertEqual(result, 2)
            self.assertFalse(database.exists())

    def test_new_places_an_inventor_in_the_repository_collection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "inventors").mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "word-games",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable word games",
                        "--lane",
                        "invented-games",
                        "--level",
                        "taste-only",
                        "--root",
                        str(root),
                    )
                )
            self.assertEqual(result, 0)
            self.assertTrue((root / "inventors/word-games/inventor.json").is_file())
            self.assertFalse(
                (root / "inventors/word-games/src/word_games/inventor.py").exists()
            )

    def test_new_accepts_the_inventor_collection_as_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "deduction-games",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable deduction games",
                        "--lane",
                        "invented-games",
                        "--level",
                        "custom-make",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 0)
            self.assertTrue((collection / "deduction-games/inventor.json").is_file())
            hook = collection / "deduction-games/src/deduction_games/inventor.py"
            self.assertIn("def concept(", hook.read_text(encoding="utf-8"))
            self.assertIn("def make(", hook.read_text(encoding="utf-8"))
            self.assertNotIn("def playtest(", hook.read_text(encoding="utf-8"))

    def test_inventors_lists_taste_identity_not_legacy_manifest_prose(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "science-toys",
                        "--name",
                        "Ada",
                        "--niche",
                        "personal orbit models",
                        "--lane",
                        "holdable-science",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 0)

            output = StringIO()
            with redirect_stdout(output):
                result = main(("inventors", "--root", str(collection), "--json"))
            self.assertEqual(result, 0)
            records = json.loads(output.getvalue())
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["id"], "science-toys")
            self.assertEqual(records[0]["name"], "Ada")
            self.assertEqual(records[0]["status"], "experimental")
            self.assertIn("personal orbit models", records[0]["description"])
            manifest = json.loads(
                (collection / "science-toys/inventor.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("name", manifest)
            self.assertNotIn("niche", manifest)
            self.assertNotIn("summary", manifest)
            self.assertNotIn("autonomy", manifest)

    def test_new_help_is_lane_and_level_not_legacy_template(self):
        command = parser()
        subcommands = next(
            action for action in command._actions if hasattr(action, "choices") and action.choices
        )
        help_text = subcommands.choices["new"].format_help()
        self.assertIn("--lane", help_text)
        self.assertIn("classics-made-yours", help_text)
        self.assertIn("invented-games", help_text)
        self.assertIn("moving-machines", help_text)
        self.assertIn("holdable-science", help_text)
        self.assertIn("little-worlds", help_text)
        for old_lane in (
            "games-puzzles",
            "table-game",
            "desk-toy",
            "model-character",
            "puzzle-keepsake",
        ):
            self.assertNotIn(old_lane, help_text)
        self.assertIn("--level", help_text)
        self.assertIn("taste-only", help_text)
        self.assertIn("custom-make", help_text)
        self.assertIn("custom-playtest", help_text)
        self.assertNotIn("--template", help_text)
        self.assertNotIn("physical-product", help_text)

    def test_hidden_legacy_template_maps_to_invented_games(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "legacy-games",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable games",
                        "--template",
                        "board-game",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 0)
            manifest = (collection / "legacy-games/inventor.json").read_text(
                encoding="utf-8"
            )
            self.assertIn('"invented-games"', manifest)

    def test_new_requires_a_toy_lane(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            error = StringIO()
            with redirect_stderr(error):
                result = main(
                    (
                        "new",
                        "missing-lane",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable games",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 2)
            self.assertIn("inventor lane must be one of", error.getvalue())

    def test_skills_command_exposes_canonical_workshop_tools(self):
        skills_root = Path(__file__).resolve().parents[1] / "skills"
        output = StringIO()
        with redirect_stdout(output):
            result = main(("skills", "list", "--root", str(skills_root)))
        self.assertEqual(result, 0)
        self.assertIn("product-to-cad", output.getvalue())
        output = StringIO()
        with redirect_stdout(output):
            result = main(("skills", "path", "--root", str(skills_root)))
        self.assertEqual(result, 0)
        self.assertEqual(Path(output.getvalue().strip()), skills_root.resolve())


if __name__ == "__main__":
    unittest.main()
