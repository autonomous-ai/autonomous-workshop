import fnmatch
import tomllib
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
COMPONENTS_FILE = REPOSITORY / ".github" / "components.toml"


def _matches(path: str, pattern: str) -> bool:
    """Match repository paths; component globs intentionally include `/`."""

    return fnmatch.fnmatchcase(path, pattern)


class GovernanceProjectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with COMPONENTS_FILE.open("rb") as stream:
            cls.document = tomllib.load(stream)
        cls.components = cls.document["components"]

    def test_component_ids_and_names_are_unique(self):
        ids = [component["id"] for component in self.components]
        names = [component["name"] for component in self.components]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(names), len(set(names)))

    def test_every_declared_path_exists(self):
        missing = []
        for component in self.components:
            for field in ("source", "tests", "docs"):
                for pattern in component[field]:
                    if not list(REPOSITORY.glob(pattern)):
                        missing.append("%s.%s: %s" % (component["id"], field, pattern))
        self.assertEqual(missing, [])

    def test_every_workshop_and_cli_source_file_has_an_owner(self):
        patterns = [
            pattern
            for component in self.components
            for pattern in component["source"]
        ]
        unowned = []
        for source_root in (REPOSITORY / "src" / "workshop", REPOSITORY / "src" / "cli"):
            for path in source_root.rglob("*"):
                if not path.is_file() or "__pycache__" in path.parts:
                    continue
                relative = path.relative_to(REPOSITORY).as_posix()
                if not any(_matches(relative, pattern) for pattern in patterns):
                    unowned.append(relative)
        self.assertEqual(unowned, [])

    def test_verified_maintainers_project_to_codeowners(self):
        codeowners = (REPOSITORY / ".github" / "CODEOWNERS").read_text(
            encoding="utf-8"
        )
        maintainers = (REPOSITORY / ".github" / "MAINTAINERS.md").read_text(
            encoding="utf-8"
        )
        for component in self.components:
            self.assertTrue(component["primary_github"])
            self.assertTrue(component["docs"])
            for account in component["primary_github"]:
                self.assertIn(account, codeowners)
                self.assertIn(account, maintainers)
            if not component["backup_github"]:
                self.assertEqual(component["backup_status"], "vacant")


if __name__ == "__main__":
    unittest.main()
