import tempfile
import tomllib
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.runtime.agent_assets import (
    inventor_custom_agent_bytes,
    product_run_agent_assets,
)


REPOSITORY = Path(__file__).resolve().parents[2]


class ProductRunAgentAssetsTest(unittest.TestCase):
    def test_source_checkout_uses_product_run_instructions_not_root_agents(self):
        assets = product_run_agent_assets(REPOSITORY)

        self.assertEqual(assets.source, "repository")
        self.assertEqual(
            assets.constitution,
            (REPOSITORY / ".agents" / "product-run" / "AGENTS.md").resolve(),
        )
        self.assertEqual(
            assets.skill_root,
            (
                REPOSITORY
                / ".agents"
                / "product-run"
                / ".agents"
                / "skills"
                / "autonomous-workshop"
            ).resolve(),
        )
        self.assertNotEqual(assets.constitution, (REPOSITORY / "AGENTS.md").resolve())
        self.assertRegex(assets.sha256, r"^[0-9a-f]{64}$")

    def test_installed_lookup_reads_exact_packaged_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package_runtime = root / "site-packages" / "workshop" / "runtime"
            packaged = package_runtime / "_agent_assets" / ".agents"
            constitution = packaged / "product-run" / "AGENTS.md"
            skill = (
                packaged
                / "product-run"
                / ".agents"
                / "skills"
                / "autonomous-workshop"
            )
            constitution.parent.mkdir(parents=True)
            skill.mkdir(parents=True)
            constitution.write_bytes(b"product-run-only\n")
            (skill / "SKILL.md").write_bytes(b"skill\n")
            fake_module = package_runtime / "agent_assets.py"

            assets = product_run_agent_assets(package_file=fake_module)

            self.assertEqual(assets.source, "package")
            self.assertEqual(assets.constitution.read_bytes(), b"product-run-only\n")
            self.assertEqual((assets.skill_root / "SKILL.md").read_bytes(), b"skill\n")

    def test_explicit_source_never_falls_back_to_root_builder_agents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "AGENTS.md").write_bytes(b"builder instructions\n")

            with self.assertRaisesRegex(ContractError, "product-run constitution"):
                product_run_agent_assets(root)

    def test_symlinked_or_changed_skill_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            constitution = root / ".agents" / "product-run" / "AGENTS.md"
            skill = (
                root
                / ".agents"
                / "product-run"
                / ".agents"
                / "skills"
                / "autonomous-workshop"
            )
            constitution.parent.mkdir(parents=True)
            skill.mkdir(parents=True)
            constitution.write_bytes(b"run\n")
            target = root / "outside.md"
            target.write_bytes(b"outside\n")
            (skill / "SKILL.md").symlink_to(target)

            with self.assertRaisesRegex(ContractError, "symlink|regular file"):
                product_run_agent_assets(root)

    def test_canonical_custom_inventor_agent_is_minimal_and_bounded(self):
        taste = (
            b"---\n"
            b"name: Alice\n"
            b"description: Makes exact personal classics.\n"
            b"---\n\n# Alice\n"
        )
        encoded = inventor_custom_agent_bytes(
            "alice",
            taste,
            skill_names=("alice-inventor", "alice-miniatures"),
        )
        parsed = tomllib.loads(encoded.decode("utf-8"))

        self.assertEqual(
            set(parsed), {"name", "description", "developer_instructions"}
        )
        self.assertEqual(parsed["name"], "alice")
        self.assertEqual(
            parsed["description"], "Alice: Makes exact personal classics."
        )
        instructions = parsed["developer_instructions"]
        for exact_path in (
            "catalog/inventors/alice/inventor.json",
            "catalog/inventors/alice/TASTE.md",
            ".agents/skills/alice-inventor/SKILL.md",
            ".agents/skills/alice-miniatures/SKILL.md",
        ):
            self.assertIn(exact_path, instructions)
        self.assertIn("root Workshop Manager", instructions)
        self.assertIn("do not orchestrate", instructions)
        self.assertIn("Do not advance lifecycle gates", instructions)
        self.assertIn("Do not perform external effects", instructions)

    def test_custom_inventor_agent_requires_exact_primary_skill(self):
        taste = b"---\nname: Alice\ndescription: Exact classics.\n---\n"
        with self.assertRaisesRegex(ContractError, "include <id>-inventor"):
            inventor_custom_agent_bytes(
                "alice", taste, skill_names=("alice-miniatures",)
            )

    def test_custom_agent_toml_round_trips_backslashes_from_taste(self):
        taste = (
            b"---\n"
            b'name: "Alice \\\\q"\n'
            b'description: "Makes paths like C:\\\\toys literal."\n'
            b"---\n"
        )
        encoded = inventor_custom_agent_bytes(
            "alice", taste, skill_names=("alice-inventor",)
        )

        parsed = tomllib.loads(encoded.decode("utf-8"))

        self.assertIn(r"Alice \q", parsed["description"])
        self.assertIn(r"Alice \q", parsed["developer_instructions"])
        self.assertNotIn("\t", parsed["description"])


if __name__ == "__main__":
    unittest.main()
