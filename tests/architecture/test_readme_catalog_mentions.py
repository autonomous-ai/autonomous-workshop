"""The root README must mention every bundled Inventor and every public toy."""

import json
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
README = REPOSITORY / "README.md"
INVENTORS = REPOSITORY / "inventors"
TOYS = REPOSITORY / "toys"


def _bundle_ids():
    ids = []
    for manifest in sorted(INVENTORS.glob("*/inventor.json")):
        with manifest.open(encoding="utf-8") as handle:
            ids.append(json.load(handle)["id"])
    return ids


def _toy_directories():
    return sorted(
        path.name
        for path in TOYS.iterdir()
        if path.is_dir() and not path.name.startswith("wish-")
    )


class ReadmeCatalogMentionsTest(unittest.TestCase):
    def test_every_bundled_inventor_id_is_mentioned(self):
        text = README.read_text(encoding="utf-8")
        ids = _bundle_ids()
        self.assertGreaterEqual(len(ids), 15)
        for bundle_id in ids:
            self.assertIn(
                "inventors/%s/" % bundle_id,
                text,
                "README.md does not link inventors/%s/" % bundle_id,
            )

    def test_every_public_toy_directory_is_mentioned(self):
        text = README.read_text(encoding="utf-8")
        directories = _toy_directories()
        self.assertGreaterEqual(len(directories), 29)
        for name in directories:
            self.assertIn(
                "toys/%s/" % name,
                text,
                "README.md does not link toys/%s/" % name,
            )


if __name__ == "__main__":
    unittest.main()
