import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.errors import ContractError, ManifestError
from inventor_workshop import skills as skills_module
from inventor_workshop.skills import (
    discover_skills,
    fingerprint_skill_tree,
    resolve_skills_root,
)
from inventor_workshop.taste import load_taste, load_taste_profile


class TasteTest(unittest.TestCase):
    def test_loader_binds_exact_root_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "ada"
            root.mkdir()
            source = b"# Ada's taste\r\n\r\nBright, tactile mechanisms.\r\n"
            (root / "TASTE.md").write_bytes(source)

            taste = load_taste(root)

            self.assertEqual(taste.path, (root / "TASTE.md").resolve())
            self.assertEqual(taste.content.encode("utf-8"), source)
            self.assertEqual(taste.sha256, hashlib.sha256(source).hexdigest())
            self.assertEqual(taste.to_binding()["bytes"], len(source))
            self.assertEqual(taste.to_binding()["path"], "TASTE.md")

    def test_loader_requires_immediate_regular_taste_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "ada"
            root.mkdir()
            with self.assertRaises(ManifestError):
                load_taste(root)
            (root / "TASTE.md").write_text(" \n", encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_taste(root)

    def test_former_loader_is_the_same_compatibility_function(self):
        self.assertIs(load_taste_profile, load_taste)


class SkillFingerprintTest(unittest.TestCase):
    def test_explicit_root_discovers_and_fingerprints_deterministically(self):
        with tempfile.TemporaryDirectory() as temporary:
            skills = Path(temporary).resolve() / "skills"
            skill = skills / "mechanisms"
            scripts = skill / "scripts"
            scripts.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Mechanisms\n", encoding="utf-8")
            tool = scripts / "measure.py"
            tool.write_text("print('one')\n", encoding="utf-8")

            first = discover_skills(skills)
            second = discover_skills(skills)

            self.assertEqual([item.name for item in first], ["mechanisms"])
            self.assertEqual(first[0].sha256, second[0].sha256)
            self.assertEqual(
                [item.path for item in first[0].files],
                ["SKILL.md", "scripts/measure.py"],
            )
            tool.write_text("print('two')\n", encoding="utf-8")
            changed = fingerprint_skill_tree(skill)
            self.assertNotEqual(first[0].sha256, changed.sha256)

    def test_checkout_discovery_finds_canonical_workshop_skills(self):
        observed = {skill.name for skill in discover_skills()}
        self.assertEqual(observed, {"cad", "product-to-cad", "step-parts"})

    def test_reviewed_skill_lock_matches_exact_tree_fingerprints(self):
        workshop_root = Path(__file__).resolve().parents[1]
        lock = json.loads(
            (workshop_root / "skills" / "LOCK.json").read_text(encoding="utf-8")
        )
        expected = {
            name: record["sha256"] for name, record in lock["skills"].items()
        }
        observed = {
            skill.name: skill.sha256 for skill in discover_skills()
        }
        self.assertEqual(observed, expected)

    def test_explicit_root_must_be_absolute(self):
        with self.assertRaises(ContractError):
            discover_skills(Path("skills"))

    def test_installed_layout_resolves_packaged_skill_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            data_root = Path(temporary)
            skills_root = data_root / "share" / "inventor-workshop" / "skills"
            skill = skills_root / "cad"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# CAD\n", encoding="utf-8")
            with mock.patch.object(
                skills_module,
                "__file__",
                "/opt/site-packages/inventor_workshop/skills.py",
            ), mock.patch.object(
                skills_module.sysconfig,
                "get_path",
                return_value=str(data_root),
            ):
                self.assertEqual(resolve_skills_root(), skills_root.resolve())

    def test_target_layout_prefers_package_owned_skill_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            package = target / "inventor_workshop"
            skills_root = package / "_data" / "skills"
            skill = skills_root / "cad"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# CAD\n", encoding="utf-8")
            legacy = target / "legacy-does-not-exist"
            with mock.patch.object(
                skills_module,
                "__file__",
                str(package / "skills.py"),
            ), mock.patch.object(
                skills_module.sysconfig,
                "get_path",
                return_value=str(legacy),
            ):
                self.assertEqual(resolve_skills_root(), skills_root.resolve())


if __name__ == "__main__":
    unittest.main()
