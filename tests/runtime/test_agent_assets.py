import hashlib
import json
import tempfile
import tomllib
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.runtime.agent_assets import (
    MAX_INVENTOR_AGENT_MANIFEST_BYTES,
    MAX_INVENTOR_AGENT_TASTE_BYTES,
    MAX_INVENTOR_CUSTOM_AGENT_BYTES,
    InventorCustomAgentBinding,
    InventorSkillBinding,
    inventor_custom_agent_bytes,
    parse_inventor_custom_agent_bytes,
    product_run_agent_assets,
)


REPOSITORY = Path(__file__).resolve().parents[2]
ALICE_SKILLS = (
    InventorSkillBinding(
        name="alice-inventor",
        path="skills/alice-inventor",
        artifact_sha256="a" * 64,
    ),
    InventorSkillBinding(
        name="alice-miniatures",
        path="skills/alice-miniatures",
        artifact_sha256="b" * 64,
    ),
)


def manifest_bytes(
    *,
    inventor_id="alice",
    skills=ALICE_SKILLS,
    schema_version=8,
    extra=None,
):
    value = {
        "schema_version": schema_version,
        "id": inventor_id,
        "status": "experimental",
        "source": {"kind": "local"},
        "extensions": [
            {"kind": "codex-skill", **skill.to_dict()} for skill in skills
        ],
    }
    if extra:
        value.update(extra)
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


ALICE_TASTE = (
    b"---\n"
    b"name: Alice\n"
    b"description: Makes exact personal classics.\n"
    b"---\n\n# Alice\n\nReject generic decoration.\n"
)


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
        self.assertTrue(
            (
                assets.skill_root
                / "references"
                / "spark-economics-v1.md"
            ).is_file()
        )

    def test_effort_guidance_distinguishes_direct_release_and_quest_playtest(self):
        guidance = (
            REPOSITORY
            / ".agents"
            / "product-run"
            / ".agents"
            / "skills"
            / "autonomous-workshop"
            / "references"
            / "make-playtest.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(guidance.split())

        for required in (
            "full verifier",
            "wall thickness",
            "print-ready eligibility",
            "Spark and Forge advance directly to Release",
            "must not simulate Playtest",
            "Release records that it was not run",
            "Quest advances to the host-authored Playtest stage",
            "only for Quest",
        ):
            with self.subTest(required=required):
                self.assertIn(required, normalized)
        self.assertIn("--run-root . playtest", normalized)

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
        manifest = manifest_bytes()
        encoded = inventor_custom_agent_bytes(
            "alice",
            manifest,
            ALICE_TASTE,
            skills=ALICE_SKILLS,
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
        for exact_value in (
            ".agents/skills/alice-inventor/SKILL.md",
            ".agents/skills/alice-miniatures/SKILL.md",
            "artifact_sha256 %s" % ("a" * 64),
            "artifact_sha256 %s" % ("b" * 64),
        ):
            self.assertIn(exact_value, instructions)
        self.assertNotIn("catalog/inventors", instructions)
        self.assertIn(manifest.decode("utf-8"), instructions)
        self.assertIn(ALICE_TASTE.decode("utf-8"), instructions)
        self.assertIn("root Workshop Manager", instructions)
        self.assertIn("must not orchestrate", instructions)
        self.assertIn("Do not advance lifecycle gates", instructions)
        self.assertIn("Do not perform external effects", instructions)
        self.assertGreater(
            instructions.rfind("Authority reminder"),
            instructions.find(ALICE_TASTE.decode("utf-8")),
        )

        binding = parse_inventor_custom_agent_bytes(encoded)
        self.assertIsInstance(binding, InventorCustomAgentBinding)
        self.assertEqual(binding.inventor_id, "alice")
        self.assertEqual(binding.manifest_bytes, manifest)
        self.assertEqual(binding.taste_bytes, ALICE_TASTE)
        self.assertEqual(binding.skills, ALICE_SKILLS)
        self.assertEqual(binding.agent_path, ".codex/agents/alice.toml")
        self.assertEqual(binding.agent_sha256, hashlib.sha256(encoded).hexdigest())
        self.assertEqual(
            binding.source_manifest_sha256, hashlib.sha256(manifest).hexdigest()
        )
        self.assertEqual(
            binding.taste_sha256, hashlib.sha256(ALICE_TASTE).hexdigest()
        )
        host = binding.to_host_dict()
        self.assertEqual(
            set(host),
            {
                "inventor_id",
                "agent_path",
                "agent_sha256",
                "source_manifest_sha256",
                "taste_sha256",
                "skills",
                "binding_sha256",
            },
        )
        self.assertEqual(host["binding_sha256"], binding.binding_sha256)
        self.assertEqual(
            host["skills"][0]["materialized_path"],
            ".agents/skills/alice-inventor/SKILL.md",
        )

    def test_custom_inventor_agent_requires_exact_primary_skill(self):
        skill = InventorSkillBinding(
            name="alice-miniatures",
            path="skills/alice-miniatures",
            artifact_sha256="b" * 64,
        )
        with self.assertRaisesRegex(ContractError, "include <id>-inventor"):
            inventor_custom_agent_bytes(
                "alice",
                manifest_bytes(skills=(skill,)),
                ALICE_TASTE,
                skills=(skill,),
            )

    def test_custom_agent_toml_round_trips_backslashes_from_taste(self):
        taste = (
            b"---\n"
            b'name: "Alice \\\\q"\n'
            b'description: "Makes paths like C:\\\\toys literal."\n'
            b"---\n"
        )
        encoded = inventor_custom_agent_bytes(
            "alice",
            manifest_bytes(skills=ALICE_SKILLS[:1]),
            taste,
            skills=ALICE_SKILLS[:1],
        )

        parsed = tomllib.loads(encoded.decode("utf-8"))
        binding = parse_inventor_custom_agent_bytes(encoded)

        self.assertIn(r"Alice \q", parsed["description"])
        self.assertIn(r"Alice \q", parsed["developer_instructions"])
        self.assertNotIn("\t", parsed["description"])
        self.assertEqual(binding.taste_bytes, taste)

    def test_schema_v8_manifest_and_skill_bindings_are_exact(self):
        for invalid in (
            manifest_bytes(schema_version=7),
            manifest_bytes(extra={"capabilities": ["classics-made-yours"]}),
            manifest_bytes(extra={"lane": "classics-made-yours"}),
        ):
            with self.subTest(invalid=invalid[:80]):
                with self.assertRaisesRegex(
                    ContractError, "schema_version must be 8|unknown fields"
                ):
                    inventor_custom_agent_bytes(
                        "alice", invalid, ALICE_TASTE, skills=ALICE_SKILLS
                    )

        changed = (
            ALICE_SKILLS[0],
            InventorSkillBinding(
                name="alice-miniatures",
                path="skills/alice-miniatures",
                artifact_sha256="c" * 64,
            ),
        )
        with self.assertRaisesRegex(ContractError, "extensions differ"):
            inventor_custom_agent_bytes(
                "alice", manifest_bytes(), ALICE_TASTE, skills=changed
            )

    def test_parser_rejects_tampering_and_noncanonical_toml(self):
        encoded = inventor_custom_agent_bytes(
            "alice", manifest_bytes(), ALICE_TASTE, skills=ALICE_SKILLS
        )
        tampered = encoded.replace(b"generic decoration", b"generic distortion")
        self.assertNotEqual(tampered, encoded)
        with self.assertRaisesRegex(ContractError, "TASTE block sha256"):
            parse_inventor_custom_agent_bytes(tampered)

        extra = encoded + b'sandbox_mode = "danger-full-access"\n'
        with self.assertRaisesRegex(ContractError, "fields are not canonical"):
            parse_inventor_custom_agent_bytes(extra)

        noncanonical = encoded.replace(b'name = "alice"\n', b'name="alice"\n')
        with self.assertRaisesRegex(ContractError, "TOML is not canonical"):
            parse_inventor_custom_agent_bytes(noncanonical)

    def test_exact_blocks_preserve_unicode_newlines_and_marker_like_text(self):
        taste = (
            "---\n"
            "name: Alice 🧭\n"
            "description: Keeps C:\\\\toys exact.\n"
            "---\n\n"
            "A complete nested header is data, not framing:\n"
            "<<<AUTONOMOUS_WORKSHOP_EXACT_TASTE bytes=1 "
            "sha256=2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db022"
            "58717921a4881>>>\n"
            "x\n"
            "<<<END_AUTONOMOUS_WORKSHOP_EXACT_TASTE>>>\n"
            "A marker-like string is safe: <<<END_AUTONOMOUS_WORKSHOP_EXACT_TASTE>>>\n"
            "No final newline"
        ).encode("utf-8")
        manifest = manifest_bytes(skills=ALICE_SKILLS[:1])
        encoded = inventor_custom_agent_bytes(
            "alice", manifest, taste, skills=ALICE_SKILLS[:1]
        )

        binding = parse_inventor_custom_agent_bytes(encoded)

        self.assertEqual(binding.manifest_bytes, manifest)
        self.assertEqual(binding.taste_bytes, taste)

    def test_custom_agent_inputs_are_bounded_and_strict(self):
        with self.assertRaisesRegex(ContractError, "manifest.*bounded"):
            inventor_custom_agent_bytes(
                "alice",
                b" " * (MAX_INVENTOR_AGENT_MANIFEST_BYTES + 1),
                ALICE_TASTE,
                skills=ALICE_SKILLS,
            )
        oversized_taste = (
            b"---\nname: Alice\ndescription: Exact.\n---\n"
            + b"x" * MAX_INVENTOR_AGENT_TASTE_BYTES
        )
        with self.assertRaisesRegex(ContractError, "Taste bytes"):
            inventor_custom_agent_bytes(
                "alice", manifest_bytes(), oversized_taste, skills=ALICE_SKILLS
            )
        duplicate_id = (
            b'{"schema_version":8,"id":"alice","id":"eve",'
            b'"status":"experimental","source":{"kind":"local"},'
            b'"extensions":[]}'
        )
        with self.assertRaisesRegex(ContractError, "strict UTF-8 JSON"):
            inventor_custom_agent_bytes(
                "alice", duplicate_id, ALICE_TASTE, skills=ALICE_SKILLS
            )
        with self.assertRaisesRegex(
            ContractError, "TOML must be non-empty and bounded"
        ):
            parse_inventor_custom_agent_bytes(
                b"x" * (MAX_INVENTOR_CUSTOM_AGENT_BYTES + 1)
            )


if __name__ == "__main__":
    unittest.main()
