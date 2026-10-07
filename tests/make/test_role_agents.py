import tomllib
import unittest

from workshop.errors import ContractError
from workshop.make.role_agents import (
    COMPONENT_REVIEWER,
    COMPONENT_WORKER,
    CONTRACT_REVIEWER,
    MAKE_ROLE_AGENT_NAMES,
    make_role_agent_files,
    parse_make_role_agent_bytes,
)


def _toml(name, *, effort=None, extra=""):
    lines = [
        'name = "%s"' % name,
        'description = "A fixed Make role."',
        'developer_instructions = "Do the bounded work."',
    ]
    if effort is not None:
        lines.append('model_reasoning_effort = "%s"' % effort)
    return ("\n".join(lines) + "\n" + extra).encode("utf-8")


class MakeRoleAgentFilesTest(unittest.TestCase):
    def test_exactly_the_worker_and_reviewer_roles_are_defined(self):
        files = make_role_agent_files()
        self.assertEqual(set(files), set(MAKE_ROLE_AGENT_NAMES))
        self.assertEqual(
            set(MAKE_ROLE_AGENT_NAMES),
            {COMPONENT_WORKER, COMPONENT_REVIEWER, CONTRACT_REVIEWER},
        )
        for name, content in files.items():
            self.assertEqual(parse_make_role_agent_bytes(name, content)["name"], name)

    def test_worker_inherits_root_effort_and_reviewer_reasons_low(self):
        files = make_role_agent_files()
        worker = tomllib.loads(files[COMPONENT_WORKER].decode("utf-8"))
        reviewer = tomllib.loads(files[COMPONENT_REVIEWER].decode("utf-8"))
        self.assertNotIn("model_reasoning_effort", worker)
        self.assertEqual(reviewer["model_reasoning_effort"], "low")
        self.assertNotIn("model", worker)
        self.assertNotIn("model", reviewer)

    def test_contract_reviewer_inherits_root_effort_and_checks_three_things(self):
        reviewer = tomllib.loads(
            make_role_agent_files()[CONTRACT_REVIEWER].decode("utf-8")
        )
        self.assertNotIn("model_reasoning_effort", reviewer)
        self.assertNotIn("model", reviewer)
        text = reviewer["developer_instructions"]
        for phrase in (
            "ADR 0085",
            "packet path and its sha256",
            "View every image under `references`",
            "`contradiction`",
            "`smallest`",
            "`visible_in`",
            "references_checked",
            "Do not spawn",
            "Do not advance",
        ):
            self.assertIn(phrase, text)

    def test_worker_authors_its_component_and_never_views_rendered_rounds(self):
        worker = tomllib.loads(
            make_role_agent_files()[COMPONENT_WORKER].decode("utf-8")
        )["developer_instructions"]
        for phrase in (
            "part_<id>.step.py",
            "Write the first",
            "own sealed `geometry:<id>` reference",
            "--component",
            "--worker-nonce",
            "shared file",
            "Do not view the rendered round images",
            "cannot both hold",
            "yield_time_ms: 300000",
            "10 lines",
            "Do not spawn",
            "Do not advance",
            "external effect",
        ):
            self.assertIn(phrase, worker)

    def test_worker_runs_make_round_as_its_own_command(self):
        """Issue #113: a round run beside a file edit hid from the guard."""
        worker = " ".join(tomllib.loads(
            make_role_agent_files()[COMPONENT_WORKER].decode("utf-8")
        )["developer_instructions"].split())
        for phrase in ("as its own Bash command", "never in the same command as a file edit",
                       "a heredoc"):
            self.assertIn(phrase, worker)

    def test_reviewer_is_the_only_image_reader_and_answers_in_the_review_shape(self):
        reviewer = tomllib.loads(
            make_role_agent_files()[COMPONENT_REVIEWER].decode("utf-8")
        )["developer_instructions"]
        for phrase in (
            "compare-NN.png",
            '"agrees"',
            '"differences"',
            "Do not edit",
            "Do not spawn",
            "external effect",
        ):
            self.assertIn(phrase, reviewer)


class ParseMakeRoleAgentBytesTest(unittest.TestCase):
    def test_accepts_a_canonical_role_with_or_without_effort(self):
        self.assertEqual(
            parse_make_role_agent_bytes(COMPONENT_WORKER, _toml(COMPONENT_WORKER))[
                "name"
            ],
            COMPONENT_WORKER,
        )
        parsed = parse_make_role_agent_bytes(
            COMPONENT_REVIEWER, _toml(COMPONENT_REVIEWER, effort="low")
        )
        self.assertEqual(parsed["model_reasoning_effort"], "low")

    def test_refuses_an_unknown_role(self):
        with self.assertRaisesRegex(ContractError, "not a Make role agent"):
            parse_make_role_agent_bytes("alice", _toml("alice"))

    def test_refuses_a_name_that_differs_from_its_file(self):
        with self.assertRaisesRegex(ContractError, "name differs"):
            parse_make_role_agent_bytes(COMPONENT_WORKER, _toml(COMPONENT_REVIEWER))

    def test_refuses_undeclared_fields(self):
        with self.assertRaisesRegex(ContractError, "fields"):
            parse_make_role_agent_bytes(
                COMPONENT_WORKER, _toml(COMPONENT_WORKER, extra='model = "x"\n')
            )

    def test_refuses_an_unsupported_effort(self):
        with self.assertRaisesRegex(ContractError, "reasoning effort"):
            parse_make_role_agent_bytes(
                COMPONENT_REVIEWER, _toml(COMPONENT_REVIEWER, effort="ultra")
            )

    def test_refuses_invalid_or_unbounded_bytes(self):
        for content in (b"", b"\xff", b"name = ", b"x" * (64 * 1024 + 1)):
            with self.assertRaises(ContractError):
                parse_make_role_agent_bytes(COMPONENT_WORKER, content)

    def test_refuses_empty_text(self):
        content = (
            'name = "%s"\ndescription = ""\ndeveloper_instructions = "x"\n'
            % COMPONENT_WORKER
        ).encode("utf-8")
        with self.assertRaisesRegex(ContractError, "text"):
            parse_make_role_agent_bytes(COMPONENT_WORKER, content)


if __name__ == "__main__":
    unittest.main()
