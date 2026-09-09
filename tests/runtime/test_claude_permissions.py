"""Claude Code must be able to run the stage, and must not rewrite host bytes.

The launcher previously passed only ``--permission-mode acceptEdits``. That
combination auto-approved edits (so host-owned files were writable) while
leaving Bash to a prompt that ``--print`` can never answer, so any stage whose
finalizer runs a script could not complete at all.
"""

from __future__ import annotations

from pathlib import Path
import unittest

from workshop.errors import ContractError
from workshop.runtime.claude import (
    CLAUDE_HOST_OWNED_PATHS,
    DEFAULT_CLAUDE_AUTO_COMPACT_TOKENS,
    MAX_CLAUDE_AUTO_COMPACT_TOKENS,
    MIN_CLAUDE_AUTO_COMPACT_TOKENS,
    CLAUDE_SUBPROCESS_ENVIRONMENT_ALLOWLIST,
    CLAUDE_HOST_OWNED_TREES,
    CLAUDE_MUTATING_TOOLS,
    CLAUDE_PERMISSION_MODE,
    ClaudeNativeSessionLauncher,
    _host_owned_deny_rules,
)


RUN_ROOT = Path("/tmp/workshop-run")


class PermissionModeTest(unittest.TestCase):
    def test_mode_allows_unattended_tool_use(self) -> None:
        # acceptEdits and dontAsk both auto-deny anything that would prompt,
        # which includes every Bash call the CAD pipeline depends on.
        self.assertEqual(CLAUDE_PERMISSION_MODE, "auto")
        self.assertNotIn(CLAUDE_PERMISSION_MODE, ("acceptEdits", "dontAsk"))

    def test_command_carries_the_mode_and_the_deny_rules(self) -> None:
        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/echo", cli_version="2.1.259"
        )
        command = launcher._command(RUN_ROOT, prompt="go", session_id=None)
        self.assertEqual(
            command[command.index("--permission-mode") + 1], CLAUDE_PERMISSION_MODE
        )
        self.assertIn("--disallowedTools", command)


class DenyRuleShapeTest(unittest.TestCase):
    """Claude Code silently ignores a deny pattern it cannot resolve."""

    def setUp(self) -> None:
        self.rules = _host_owned_deny_rules(RUN_ROOT)

    def test_every_rule_is_an_absolute_path(self) -> None:
        # A bare name ("STAGE.json") and a "**/" glob are both accepted by the
        # CLI and both match nothing, which would leave a rule that reads as
        # protection while protecting nothing.
        for rule in self.rules:
            target = rule[rule.index("(") + 1 : -1]
            self.assertTrue(
                target.startswith("//"),
                "%s must target an absolute path" % rule,
            )
            self.assertNotIn("**/", target.rstrip("*"))

    def test_every_host_owned_file_is_denied_for_every_mutating_tool(self) -> None:
        for name in CLAUDE_HOST_OWNED_PATHS:
            for tool in CLAUDE_MUTATING_TOOLS:
                self.assertIn(
                    "%s(/%s)" % (tool, RUN_ROOT / name),
                    self.rules,
                    "%s may still rewrite %s" % (tool, name),
                )

    def test_every_host_owned_tree_is_denied_recursively(self) -> None:
        for tree in CLAUDE_HOST_OWNED_TREES:
            for tool in CLAUDE_MUTATING_TOOLS:
                self.assertIn(
                    "%s(/%s/**)" % (tool, RUN_ROOT / tree),
                    self.rules,
                )

    def test_rules_follow_the_run_root(self) -> None:
        other = _host_owned_deny_rules(Path("/tmp/another-run"))
        self.assertTrue(all(rule not in self.rules for rule in other))

    def test_agent_writable_trees_are_not_denied(self) -> None:
        # Make and Release must still author artifacts; denying these would
        # trade one blocked stage for another.
        joined = " ".join(self.rules)
        for writable in ("/artifacts", "/work"):
            self.assertNotIn("%s/" % (RUN_ROOT / writable.lstrip("/")), joined)

    def test_reads_are_never_denied(self) -> None:
        # The Manager must read STAGE.json every turn; only mutation is denied.
        self.assertNotIn("Read", " ".join(self.rules))


class AutoCompactTest(unittest.TestCase):
    """Bound each turn's transcript instead of the model's whole window."""

    def _command(self, **kwargs):
        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/echo", cli_version="2.1.259", **kwargs
        )
        return list(launcher._command(RUN_ROOT, prompt="go", session_id=None))

    def test_limit_is_declared_by_default(self) -> None:
        command = self._command()
        self.assertEqual(
            command[command.index("--autocompact") + 1],
            str(DEFAULT_CLAUDE_AUTO_COMPACT_TOKENS),
        )

    def test_resume_carries_the_same_limit(self) -> None:
        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/echo", cli_version="2.1.259"
        )
        resumed = launcher._command(RUN_ROOT, prompt="go", session_id="s-1")
        self.assertIn("--autocompact", resumed)
        self.assertIn("--resume", resumed)

    def test_limit_stays_inside_the_range_the_cli_accepts(self) -> None:
        for value in (MIN_CLAUDE_AUTO_COMPACT_TOKENS - 1,
                      MAX_CLAUDE_AUTO_COMPACT_TOKENS + 1, 0, "big", 1.5):
            with self.assertRaises(ContractError):
                self._command(auto_compact_token_limit=value)

    def test_it_can_be_switched_off(self) -> None:
        self.assertNotIn("--autocompact", self._command(auto_compact_token_limit=None))


class SubscriptionAuthTest(unittest.TestCase):
    """A locally signed-in Claude Code must stay signed in inside a run."""

    def test_account_name_reaches_the_subprocess(self) -> None:
        # Without USER the CLI reports "Not logged in - Please run /login"
        # even with a valid local session, so a run that does not supply a
        # gateway key could never authenticate at all.
        self.assertIn("USER", CLAUDE_SUBPROCESS_ENVIRONMENT_ALLOWLIST)

    def test_allowlist_still_excludes_factory_authority(self) -> None:
        for name in CLAUDE_SUBPROCESS_ENVIRONMENT_ALLOWLIST:
            self.assertFalse(name.startswith("FACTORY_"), name)


if __name__ == "__main__":
    unittest.main()
