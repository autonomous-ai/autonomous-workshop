import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.manifest import load_manifest
from inventor_workshop.errors import ContractError
from inventor_workshop.scaffold import scaffold_inventor


class ScaffoldTest(unittest.TestCase):
    def test_new_inventor_is_immediately_discoverable(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = scaffold_inventor(
                Path(temporary), "word-games", "Ada", "printable word games"
            )
            manifest = load_manifest(destination / "inventor.json")
            self.assertEqual(manifest.inventor_id, "word-games")
            self.assertTrue((destination / "src/word_games/workflow.py").exists())
            taste = (destination / "TASTE.md").read_text(encoding="utf-8")
            self.assertIn("creative constitution", taste)
            self.assertIn("printable word games", taste)
            self.assertIn("../../workshop", (destination / "README.md").read_text())
            self.assertIn(
                'requires-python = ">=3.11"',
                (destination / "pyproject.toml").read_text(encoding="utf-8"),
            )
            self.assertTrue((destination / "setup.py").is_file())
            self.assertNotIn(
                "data-files",
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
                Path(observed[0]), destination / ".workshop" / "clockwork.sqlite3"
            )
            runtime = destination / ".workshop"
            doctor = subprocess.run(
                [sys.executable, "-m", "word_games", "doctor"],
                cwd=str(Path(temporary) / "one"),
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertIn("no state changed", doctor.stdout)
            self.assertFalse(runtime.exists())
            made = subprocess.run(
                [sys.executable, "-m", "word_games", "make", "first-product"],
                cwd=str(Path(temporary) / "one"),
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertIn("made and inspected first-product -> ", made.stdout)
            status = subprocess.run(
                [sys.executable, "-m", "word_games", "status"],
                cwd=str(Path(temporary) / "two"),
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertIn("first-product inspect@1 ", status.stdout)
            self.assertNotIn("unbound", status.stdout)
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
            for inventor_id in ("class", "inventor-workshop", "tests"):
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
                'printable "word" games with \\ paths',
            )
            for source in sorted(destination.rglob("*.py")):
                compile(source.read_text(encoding="utf-8"), str(source), "exec")
            core_src = Path(__file__).resolve().parents[1] / "src"
            env = dict(os.environ)
            env["PYTHONPATH"] = os.pathsep.join(
                (str(core_src), str(destination / "src"))
            )
            observed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from quote_games.workflow import wish; "
                        "print(wish('quoted').objective)"
                    ),
                ],
                cwd=temporary,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(
                observed.stdout.strip(),
                (
                    'Invent printable "word" games with \\ paths guided by '
                    'Ada "The Inventor"\'s TASTE.md.'
                ),
            )

    def test_generated_identity_resolves_from_target_like_package_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = scaffold_inventor(
                root / "source", "target-games", "Ada", "word games"
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
            env = dict(os.environ)
            env["PYTHONPATH"] = os.pathsep.join((str(target), str(core_src)))
            observed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from target_games.__main__ import inventor_root; print(inventor_root())",
                ],
                cwd=away,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(Path(observed.stdout.strip()), identity.resolve())


if __name__ == "__main__":
    unittest.main()
