import unittest

from workshop.errors import ContractError
from workshop.make.role_agents import make_role_agent_files
from workshop.runtime.agent_projection import (
    claude_agent_bytes,
    project_agents,
    projected_agent_path,
)


def _frontmatter(rendered):
    text = rendered.decode("utf-8")
    head, separator, body = text[4:].partition("\n---\n")
    assert text.startswith("---\n") and separator
    fields = {}
    for line in head.splitlines():
        key, _, value = line.partition(": ")
        fields[key] = value
    return fields, body


class ClaudeAgentProjectionTest(unittest.TestCase):
    def test_role_agents_keep_their_text_and_lose_codex_waits(self):
        roles = make_role_agent_files()
        worker, body = _frontmatter(claude_agent_bytes(roles["component-worker"]))
        self.assertEqual(worker["name"], '"component-worker"')
        self.assertNotIn("effort", worker)
        self.assertIn("timeout` at 600000", body)
        for fragment in ("yield_time_ms", "write_stdin"):
            self.assertNotIn(fragment, body)
        self.assertIn("Edit only that Component's `part_<id>.step.py`", body)

        reviewer, body = _frontmatter(claude_agent_bytes(roles["component-reviewer"]))
        self.assertEqual(reviewer["effort"], "low")
        self.assertIn("You are the Component Reviewer", body)

    def test_projection_is_deterministic_and_keyed_by_the_claude_path(self):
        roles = make_role_agent_files()
        sources = {
            ".codex/agents/%s.toml" % name: content for name, content in roles.items()
        }
        first = project_agents(".claude/agents", sources)
        self.assertEqual(first, project_agents(".claude/agents", sources))
        self.assertEqual(
            sorted(first),
            [".claude/agents/component-reviewer.md", ".claude/agents/component-worker.md"],
        )
        self.assertEqual(project_agents(".codex/agents", sources), {})
        self.assertEqual(project_agents(".grok/agents", sources), {})

    def test_an_inventor_names_its_runtime(self):
        source = (
            b'name = "rowan-vale"\n'
            b'description = "Rowan Vale: sculptor"\n'
            b'developer_instructions = "You are Rowan Vale, an Autonomous Workshop '
            b'Inventor and a standard native Codex subagent."\n'
        )
        unused, body = _frontmatter(claude_agent_bytes(source))
        self.assertIn("standard native Claude Code subagent", body)

    def test_an_unrewritten_codex_wait_fails_closed(self):
        source = (
            b'name = "component-worker"\n'
            b'description = "worker"\n'
            b'developer_instructions = "Poll with write_stdin."\n'
        )
        with self.assertRaisesRegex(ContractError, "Codex-only wait"):
            claude_agent_bytes(source)

    def test_invalid_sources_and_paths_are_refused(self):
        for source in (b"not toml = ", b'name = "x"\n', b'\xff'):
            with self.subTest(source=source):
                with self.assertRaises(ContractError):
                    claude_agent_bytes(source)
        with self.assertRaises(ContractError):
            projected_agent_path(".claude/agents", ".agents/skills/x.toml")
        with self.assertRaises(ContractError):
            projected_agent_path(".grok/agents", ".codex/agents/x.toml")


if __name__ == "__main__":
    unittest.main()
