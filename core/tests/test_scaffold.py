import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from inventor_core.manifest import load_manifest
from inventor_core.errors import ContractError
from inventor_core.scaffold import scaffold_inventor


class ScaffoldTest(unittest.TestCase):
    def test_new_inventor_is_immediately_discoverable(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = scaffold_inventor(
                Path(temporary), "word-games", "Ada", "printable word games"
            )
            manifest = load_manifest(destination / "inventor.json")
            self.assertEqual(manifest.inventor_id, "word-games")
            self.assertTrue((destination / "src/word_games/workflow.py").exists())
            self.assertIn("../core", (destination / "README.md").read_text())
            self.assertIn(
                'requires-python = ">=3.11"',
                (destination / "pyproject.toml").read_text(encoding="utf-8"),
            )

            core_src = Path(__file__).resolve().parents[1] / "src"
            env = dict(os.environ)
            env["PYTHONPATH"] = os.pathsep.join(
                (str(core_src), str(destination / "src"))
            )
            observed = []
            for name in ("one", "two"):
                cwd = Path(temporary) / name
                cwd.mkdir()
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        "from word_games.__main__ import database_path; print(database_path())",
                    ],
                    cwd=str(cwd),
                    env=env,
                    check=True,
                    stdout=subprocess.PIPE,
                    text=True,
                )
                observed.append(result.stdout.strip())
            self.assertEqual(observed[0], observed[1])
            self.assertEqual(
                Path(observed[0]), destination / ".runtime" / "state.sqlite"
            )
            created = subprocess.run(
                [sys.executable, "-m", "word_games", "create", "first-product"],
                cwd=str(Path(temporary) / "one"),
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertIn("created first-product at idea@0", created.stdout)
            status = subprocess.run(
                [sys.executable, "-m", "word_games", "status"],
                cwd=str(Path(temporary) / "two"),
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertIn("first-product idea@0 unbound", status.stdout)
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
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

    def test_scaffold_rejects_invalid_package_names_and_control_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for inventor_id in ("class", "inventor-core", "tests"):
                with self.subTest(inventor_id=inventor_id), self.assertRaises(
                    ContractError
                ):
                    scaffold_inventor(root, inventor_id, "Ada", "word games")
            with self.assertRaises(ContractError):
                scaffold_inventor(root, "safe-id", "Ada\nInjected", "word games")

    def test_scaffold_quotes_display_name_in_generated_python(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = scaffold_inventor(
                Path(temporary),
                "quote-games",
                'Ada "The Inventor"',
                "printable word games",
            )
            source = destination / "src/quote_games/__init__.py"
            compile(source.read_text(encoding="utf-8"), str(source), "exec")


if __name__ == "__main__":
    unittest.main()
