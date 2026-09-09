import unittest

from tests.runtime.test_agent_assets import ALICE_SKILLS, ALICE_TASTE, manifest_bytes
from workshop.errors import ContractError
from workshop.runtime.agent_assets import inventor_custom_agent_bytes, parse_inventor_custom_agent_bytes


class ClaudeInventorAssetsTest(unittest.TestCase):
    def test_exact_source_roundtrip_and_tamper_rejection(self):
        encoded = inventor_custom_agent_bytes("alice", manifest_bytes(), ALICE_TASTE,
                                              skills=ALICE_SKILLS, manager_id="claude")
        self.assertTrue(encoded.startswith(b'---\nname: "alice"\n'))
        self.assertIn(b'model: inherit\n---\n', encoded)
        binding = parse_inventor_custom_agent_bytes(encoded)
        self.assertEqual(binding.agent_path, ".claude/agents/alice.md")
        self.assertEqual(binding.manifest_bytes, manifest_bytes())
        self.assertEqual(binding.taste_bytes, ALICE_TASTE)
        self.assertEqual(binding.skills, ALICE_SKILLS)
        for changed in (encoded.replace(b"model: inherit", b"model: opus"),
                        encoded + b"Additional authority", encoded.replace(b"Makes exact", b"Makes vague")):
            with self.subTest(changed=changed[:40]), self.assertRaises(ContractError):
                parse_inventor_custom_agent_bytes(changed)
