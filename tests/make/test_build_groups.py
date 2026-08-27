"""Make build groups: every planned group sealed against the exact part bytes."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tests.invent.test_native_contract import v4_concept, v5_concept
from workshop.errors import ArtifactError, ContractError
from workshop.make.native import MAKE_GROUP_KIND, group_path, part_path, validate_build_groups


def seal_group(root, concept, name):
    group = next(item for item in concept["build_plan"] if item["group"] == name)
    files = {key: hashlib.sha256((root / part_path(key)).read_bytes()).hexdigest() for key in group["parts"]}
    target = root / group_path(name)
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({"schema_version": 1, "kind": MAKE_GROUP_KIND, "group": name,
                                  "parts": group["parts"], "files": files}), encoding="utf-8")
    return target


def write_parts(root, concept):
    (root / "parts").mkdir(parents=True, exist_ok=True)
    for item in concept["components"]:
        (root / part_path(item["key"])).write_bytes(b"solid %s\nendsolid\n" % item["key"].encode())


class BuildGroupsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.concept = v5_concept()
        write_parts(self.root, self.concept)
        for group in self.concept["build_plan"]:
            seal_group(self.root, self.concept, group["group"])

    def test_legacy_concepts_need_no_groups(self):
        self.assertEqual(validate_build_groups(v4_concept(), self.root / "missing"), {"groups": 0, "parts": 0})
        self.assertEqual(validate_build_groups({**v5_concept(), "build_plan": []}, self.root), {"groups": 0, "parts": 0})

    def test_sealed_groups_pass_and_every_drift_fails(self):
        self.assertEqual(validate_build_groups(self.concept, self.root), {"groups": 2, "parts": 3})
        dome = self.root / part_path("dome")
        original = dome.read_bytes()
        dome.write_bytes(original + b"x")
        with self.assertRaisesRegex(ContractError, "body was sealed against different part bytes: dome"):
            validate_build_groups(self.concept, self.root)
        dome.write_bytes(b"")
        with self.assertRaisesRegex(ArtifactError, "part dome must contain"):
            validate_build_groups(self.concept, self.root)
        dome.unlink()
        with self.assertRaisesRegex(ArtifactError, "part dome is missing"):
            validate_build_groups(self.concept, self.root)
        dome.symlink_to(self.root / part_path("base"))
        with self.assertRaisesRegex(ArtifactError, "part dome is missing or not a regular"):
            validate_build_groups(self.concept, self.root)
        dome.unlink()
        dome.write_bytes(original)
        cap = self.root / group_path("cap")
        cap.unlink()
        with self.assertRaisesRegex(ArtifactError, "build group cap is unavailable"):
            validate_build_groups(self.concept, self.root)
        cap.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "strict UTF-8 JSON"):
            validate_build_groups(self.concept, self.root)
        good = json.loads(seal_group(self.root, self.concept, "cap").read_text())
        for broken, pattern in (
            ({**good, "extra": 1}, "fields are invalid"),
            ({**good, "kind": "other"}, "does not match the sealed plan"),
            ({**good, "parts": ["dome"]}, "does not match the sealed plan"),
            ({**good, "files": {"dome": good["files"]["lens_cap"]}}, "hash exactly its parts"),
            ({**good, "files": {"lens_cap": "0" * 64}}, "sealed against different part bytes: lens_cap"),
        ):
            cap.write_text(json.dumps(broken), encoding="utf-8")
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(ContractError, pattern):
                    validate_build_groups(self.concept, self.root)


if __name__ == "__main__":
    unittest.main()
