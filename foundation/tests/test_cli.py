import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import inventor_core
from inventor_core.cli import main, parser


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
        self.assertEqual(declared, inventor_core.__version__)

    def test_foundation_is_the_canonical_cli_name_with_v1_alias(self):
        self.assertEqual(parser().prog, "inventor-foundation")
        project = (
            Path(__file__).resolve().parents[1] / "pyproject.toml"
        ).read_text(encoding="utf-8")
        self.assertIn('inventor-foundation = "inventor_core.cli:main"', project)
        self.assertIn('inventor-core = "inventor_core.cli:main"', project)

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
                        "--root",
                        str(root),
                    )
                )
            self.assertEqual(result, 0)
            self.assertTrue((root / "inventors/word-games/inventor.json").is_file())

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
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 0)
            self.assertTrue((collection / "deduction-games/inventor.json").is_file())


if __name__ == "__main__":
    unittest.main()
