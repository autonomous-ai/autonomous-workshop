import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.runtime.agent_assets import product_run_agent_assets


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
                REPOSITORY / ".agents" / "skills" / "autonomous-workshop"
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
            skill = packaged / "skills" / "autonomous-workshop"
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
            skill = root / ".agents" / "skills" / "autonomous-workshop"
            constitution.parent.mkdir(parents=True)
            skill.mkdir(parents=True)
            constitution.write_bytes(b"run\n")
            target = root / "outside.md"
            target.write_bytes(b"outside\n")
            (skill / "SKILL.md").symlink_to(target)

            with self.assertRaisesRegex(ContractError, "symlink|regular file"):
                product_run_agent_assets(root)


if __name__ == "__main__":
    unittest.main()
