from __future__ import annotations

import importlib.util
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import catalog_build  # noqa: E402

spec = importlib.util.spec_from_file_location("design_refs", SCRIPTS / "design_refs.py")
assert spec and spec.loader
design_refs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design_refs)


FIXTURE = b'''"""fixture"""
from build123d import *

# Description: A rounded mounting bracket with two holes.
def model_fixture_0001():
    """Model: Fixture Bracket"""
    return Box(1, 2, 3)

MODELS = {
    "model_fixture_0001": {
        "func": model_fixture_0001,
        "volume": 6.0,
        "area": 22.0,
    },
}
'''


class CatalogBuildTests(unittest.TestCase):
    def test_parse_batch_extracts_search_and_validation_fields(self) -> None:
        records = catalog_build.parse_batch("fixture", "03_4to5ops/batch_007.py", FIXTURE)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["id"], "fixture/model_fixture_0001")
        self.assertEqual(record["title"], "Fixture Bracket")
        self.assertIn("rounded mounting bracket", record["description"])
        self.assertEqual((record["operationMin"], record["operationMax"]), (4, 5))
        self.assertEqual(record["volume"], 6.0)
        self.assertEqual(len(record["functionSha256"]), 64)

    def test_extract_function_omits_other_batch_metadata(self) -> None:
        excerpt = catalog_build.extract_function(FIXTURE, "model_fixture_0001")
        self.assertIn("from build123d import *", excerpt)
        self.assertIn("def model_fixture_0001", excerpt)
        self.assertNotIn("MODELS", excerpt)

    def test_tar_adapter_strips_archive_root(self) -> None:
        archive_data = io.BytesIO()
        with tarfile.open(fileobj=archive_data, mode="w:gz") as archive:
            member = tarfile.TarInfo("repository-commit/01_2ops/batch_001.py")
            member.size = len(FIXTURE)
            archive.addfile(member, io.BytesIO(FIXTURE))
        archive_data.seek(0)
        with tarfile.open(fileobj=archive_data, mode="r:gz") as archive:
            records = catalog_build.records_from_tar(archive, "fixture")
        self.assertEqual(records[0]["sourcePath"], "01_2ops/batch_001.py")

    def test_validate_records_rejects_duplicates(self) -> None:
        record = catalog_build.parse_batch("fixture", "01_2ops/batch_001.py", FIXTURE)[0]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            catalog_build.validate_records([record, record])


class ClientTests(unittest.TestCase):
    def test_default_cache_is_rooted_in_invocation_workspace(self) -> None:
        self.assertEqual(
            design_refs.DEFAULT_CACHE_DIR,
            Path.cwd().resolve() / ".design-reference-cache",
        )

    def test_search_score_prefers_title_and_all_terms(self) -> None:
        exact = {"id": "fixture/a", "title": "Mounting Bracket", "description": "rounded body with holes"}
        partial = {"id": "fixture/b", "title": "Plate", "description": "one mounting hole"}
        self.assertGreater(
            design_refs._score(exact, "mounting bracket holes"),
            design_refs._score(partial, "mounting bracket holes"),
        )

    def test_provenance_verification_detects_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = root / "reference.build123d.txt"
            artifact.write_bytes(b"reference")
            provenance = root / "provenance.json"
            provenance.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "files": {
                            artifact.name: {
                                "sha256": design_refs._sha256(b"reference"),
                                "byteSize": len(b"reference"),
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            self.assertTrue(design_refs._verify_provenance(provenance)["ok"])
            artifact.write_bytes(b"changed")
            self.assertFalse(design_refs._verify_provenance(provenance)["ok"])

    def test_empty_provenance_is_not_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            provenance = Path(temp_dir) / "provenance.json"
            provenance.write_text(json.dumps({"schemaVersion": 1, "files": {}}), encoding="utf-8")
            self.assertFalse(design_refs._verify_provenance(provenance)["ok"])


if __name__ == "__main__":
    unittest.main()
