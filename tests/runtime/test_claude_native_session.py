import hashlib
import json
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.runtime.managers import (
    MAX_NATIVE_TURN_SECONDS,
    NATIVE_TOKEN_USAGE_FIELDS,
)
from workshop.runtime.claude import (
    CLAUDE_SESSION_CHECKPOINT_NAME,
    CLAUDE_TOKEN_BUDGET_STOP_MESSAGE,
    DEFAULT_CLAUDE_TIMEOUT_SECONDS,
    ClaudeInvocationError,
    ClaudeNativeSessionLauncher,
    ClaudeNativeSessionOutcome,
    _canonical_json,
    claude_subprocess_environment,
    claude_supports_native_workshop,
)


DIGEST = "b" * 64
SESSION = "claude-session-one"
# Shapes copied from what Claude Code 2.1.274 writes: per-request ``usage``
# counts uncached input separately from cache reads and writes, and the
# terminal result's ``modelUsage`` carries per-model running totals with an
# optional ``thinkingTokens`` subset of ``outputTokens``.
PER_BLOCK_USAGE = {
    "input_tokens": 2,
    "cache_creation_input_tokens": 13_227,
    "cache_read_input_tokens": 10_010,
    "output_tokens": 168,
    "output_tokens_details": {"thinking_tokens": 0},
    "service_tier": "standard",
}
OPUS_TOTALS = {
    "inputTokens": 158,
    "outputTokens": 245_325,
    "thinkingTokens": 181_276,
    "cacheReadInputTokens": 16_463_646,
    "cacheCreationInputTokens": 371_296,
    "webSearchRequests": 0,
    "costUSD": 41.5,
    "contextWindow": 200_000,
    "maxOutputTokens": 32_000,
}
HAIKU_TOTALS = {
    "inputTokens": 40,
    "outputTokens": 100,
    "thinkingTokens": 0,
    "cacheReadInputTokens": 1_000,
    "cacheCreationInputTokens": 60,
    "webSearchRequests": 0,
    "costUSD": 0.01,
    "contextWindow": 200_000,
    "maxOutputTokens": 8_192,
}
OPUS_GROSS_INPUT = 158 + 16_463_646 + 371_296
HAIKU_GROSS_INPUT = 40 + 1_000 + 60
_ABSENT = object()


def _init_line(session_id=SESSION):
    return json.dumps(
        {"type": "system", "subtype": "init", "session_id": session_id}
    ) + "\n"


def _assistant_line(message_id, usage, session_id=SESSION):
    return json.dumps(
        {
            "type": "assistant",
            "session_id": session_id,
            "parent_tool_use_id": None,
            "message": {
                "id": message_id,
                "role": "assistant",
                "model": "claude-opus-5",
                "stop_reason": None,
                "usage": usage,
            },
        }
    ) + "\n"


def _result_line(model_usage=_ABSENT, session_id=SESSION, **extra):
    event = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 3,
        "session_id": session_id,
        "total_cost_usd": 41.51,
        "usage": {
            "input_tokens": 198,
            "cache_creation_input_tokens": 371_356,
            "cache_read_input_tokens": 16_464_646,
            "output_tokens": 245_425,
            "output_tokens_details": {"thinking_tokens": 181_276},
        },
    }
    if model_usage is not _ABSENT:
        event["modelUsage"] = model_usage
    event.update(extra)
    return json.dumps(event) + "\n"


class _FakeStdout:
    def __init__(self, lines):
        self._lines = list(lines)

    def __iter__(self):
        return iter(self._lines)


class _FakeProcess:
    def __init__(self, lines, returncode=0):
        self.stdout = _FakeStdout(lines)
        self.stderr = _FakeStdout([])
        self.returncode = returncode

    def wait(self, timeout=None):
        del timeout
        return self.returncode

    def kill(self):
        self.returncode = -9


class ClaudeNativeSessionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name).resolve()
        self.run_root = root / "run"
        self.host_state = root / "state"
        self.run_root.mkdir(mode=0o700)
        self.host_state.mkdir(mode=0o700)

    def test_version_pin(self):
        self.assertTrue(claude_supports_native_workshop("2.1.0"))
        self.assertFalse(claude_supports_native_workshop("1.9.0"))

    def test_environment_drops_factory_credentials(self):
        environment = claude_subprocess_environment(
            {"PATH": "/usr/bin", "HOME": "/tmp/home", "FACTORY_PASSWORD": "secret"}
        )
        self.assertNotIn("FACTORY_PASSWORD", environment)

    def test_environment_forwards_non_interactive_authentication(self):
        """A sandbox with no interactive login still authenticates its turns."""

        environment = claude_subprocess_environment(
            {
                "PATH": "/usr/bin",
                "HOME": "/home/agent",
                "CLAUDE_CODE_OAUTH_TOKEN": "oauth-token",
                "ANTHROPIC_API_KEY": "api-key",
            }
        )
        self.assertEqual(environment["CLAUDE_CODE_OAUTH_TOKEN"], "oauth-token")
        self.assertEqual(environment["ANTHROPIC_API_KEY"], "api-key")

    def test_environment_forwards_no_unrelated_account_authority(self):
        """Runtime authentication widened; external-effect authority did not."""

        environment = claude_subprocess_environment(
            {
                "PATH": "/usr/bin",
                "HOME": "/home/agent",
                "CLAUDE_CODE_OAUTH_TOKEN": "oauth-token",
                "FACTORY_API_TOKEN": "factory",
                "GH_TOKEN": "github",
                "AWS_SECRET_ACCESS_KEY": "aws",
                "STRIPE_SECRET_KEY": "stripe",
            }
        )
        for name in (
            "FACTORY_API_TOKEN",
            "GH_TOKEN",
            "AWS_SECRET_ACCESS_KEY",
            "STRIPE_SECRET_KEY",
        ):
            self.assertNotIn(name, environment)

    def test_environment_extra_may_not_smuggle_factory_credentials(self):
        """The widened allowlist did not widen the caller-supplied extras."""

        with self.assertRaisesRegex(ContractError, "extra environment is invalid"):
            claude_subprocess_environment(
                {"PATH": "/usr/bin", "HOME": "/home/agent"},
                extra={"FACTORY_API_TOKEN": "factory"},
            )

    def test_turn_boundary_accepts_a_longer_turn_and_an_untimed_one(self):
        """Only an explicit request may exceed the historical one-hour default."""

        self.assertEqual(DEFAULT_CLAUDE_TIMEOUT_SECONDS, 3_600)
        default = ClaudeNativeSessionLauncher(
            binary="/bin/claude", cli_version="2.0.0"
        )
        self.assertEqual(default.timeout_seconds, 3_600)
        longer = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            timeout_seconds=MAX_NATIVE_TURN_SECONDS,
        )
        self.assertEqual(longer.timeout_seconds, MAX_NATIVE_TURN_SECONDS)
        untimed = ClaudeNativeSessionLauncher(
            binary="/bin/claude", cli_version="2.0.0", timeout_seconds=None
        )
        self.assertIsNone(untimed.timeout_seconds)
        for invalid in (MAX_NATIVE_TURN_SECONDS + 1, 0, -1, 60.0, "3600"):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(
                ValueError, "1 to %d or None" % MAX_NATIVE_TURN_SECONDS
            ):
                ClaudeNativeSessionLauncher(
                    binary="/bin/claude",
                    cli_version="2.0.0",
                    timeout_seconds=invalid,
                )

    def test_an_untimed_turn_never_arms_a_process_deadline(self):
        """An untimed launcher must wait without a timeout, not with a huge one."""

        waits = []

        class _RecordingProcess(_FakeProcess):
            def wait(self, timeout=None):
                waits.append(timeout)
                return self.returncode

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            timeout_seconds=None,
            popen_factory=lambda command, **kwargs: _RecordingProcess(
                [
                    json.dumps(
                        {
                            "type": "system",
                            "subtype": "init",
                            "session_id": "claude-session-untimed",
                        }
                    )
                    + "\n",
                ]
            ),
            uuid_factory=lambda: "initial-session-id",
        )
        launcher.start(
            product_id="wish-untimed",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="make",
        )
        self.assertEqual(waits, [None])

    def test_start_and_resume_preserve_session_identity(self):
        seen = {}

        def popen(command, **kwargs):
            seen.setdefault("commands", []).append(command)
            self.assertEqual(kwargs["cwd"], str(self.run_root))
            self.assertIn("WORKSHOP_PYTHON", kwargs["env"])
            self.assertNotIn("FACTORY_PASSWORD", kwargs["env"])
            return _FakeProcess(
                [
                    json.dumps(
                        {
                            "type": "system",
                            "subtype": "init",
                            "session_id": "claude-session-one",
                        }
                    )
                    + "\n",
                    json.dumps({"type": "tool_use"}) + "\n",
                ]
            )

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        started = launcher.start(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="invent",
        )
        self.assertEqual(started.session_id, "claude-session-one")
        resumed = launcher.resume(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="make",
        )
        self.assertEqual(resumed.session_id, "claude-session-one")
        self.assertIn("--print", seen["commands"][0])
        self.assertIn("--verbose", seen["commands"][0])
        self.assertIn("bypassPermissions", seen["commands"][0])
        self.assertIn("--resume", seen["commands"][1])
        payload = json.loads(
            (self.host_state / "claude-session.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["session_id"], "claude-session-one")

    def test_selected_opus_model_and_effort_are_bound_and_reused(self):
        commands = []

        def popen(command, **kwargs):
            del kwargs
            commands.append(command)
            return _FakeProcess(
                [
                    json.dumps(
                        {
                            "type": "system",
                            "subtype": "init",
                            "session_id": "claude-session-one",
                        }
                    )
                    + "\n"
                ]
            )

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            model="claude-opus-5",
            reasoning_effort="high",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        launcher.start(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="invent",
        )
        launcher.resume(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="make",
        )
        for command in commands:
            self.assertIn("--model", command)
            self.assertEqual(command[command.index("--model") + 1], "claude-opus-5")
            self.assertIn("--effort", command)
            self.assertEqual(command[command.index("--effort") + 1], "high")
        payload = json.loads(
            (self.host_state / "claude-session.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["model"], "claude-opus-5")
        self.assertEqual(payload["reasoning_effort"], "high")

        changed = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            model="claude-sonnet-5",
            reasoning_effort="high",
            popen_factory=popen,
        )
        with self.assertRaisesRegex(ContractError, "runtime binding"):
            changed.resume(
                product_id="wish-one",
                wish_sha256=DIGEST,
                constitution_sha256=DIGEST,
                run_root=self.run_root,
                host_state_root=self.host_state,
                prompt="make",
            )
        self.assertEqual(len(commands), 2)

    def test_the_compaction_window_reaches_every_turn_and_is_frozen(self):
        commands = []

        def popen(command, **kwargs):
            del kwargs
            commands.append(command)
            return _FakeProcess([_init_line()])

        def launcher(window):
            return ClaudeNativeSessionLauncher(
                binary="/bin/claude",
                cli_version="2.1.285",
                model="claude-opus-5",
                reasoning_effort="medium",
                autocompact_tokens=window,
                popen_factory=popen,
                uuid_factory=lambda: "initial-session-id",
            )

        frozen = launcher(256_000)
        self._turn(frozen, "start")
        self._turn(frozen, "resume")
        for command in commands:
            self.assertEqual(
                command[command.index("--autocompact") + 1], "256000"
            )
        payload = json.loads(
            (self.host_state / "claude-session.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["autocompact_tokens"], 256_000)
        for window in (None, 300_000):
            with self.subTest(window=window):
                with self.assertRaisesRegex(ContractError, "runtime binding"):
                    self._turn(launcher(window), "resume")
        self.assertEqual(len(commands), 2)

    def test_a_session_without_a_window_passes_none_and_refuses_one(self):
        commands = []

        def popen(command, **kwargs):
            del kwargs
            commands.append(command)
            return _FakeProcess([_init_line()])

        plain = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.1.285",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        self._turn(plain, "start")
        self.assertNotIn("--autocompact", commands[0])
        widened = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.1.285",
            autocompact_tokens=256_000,
            popen_factory=popen,
        )
        with self.assertRaisesRegex(ContractError, "runtime binding"):
            self._turn(widened, "resume")

    def test_an_older_cli_refuses_a_metered_turn_up_front(self):
        for options in ({"autocompact_tokens": 256_000}, {}):
            with self.subTest(options=options):
                launcher = ClaudeNativeSessionLauncher(
                    binary="/bin/claude",
                    cli_version="2.1.284",
                    popen_factory=lambda command, **kwargs: self.fail("started"),
                    **options,
                )
                if not options:
                    launcher.token_budget_observer = lambda counters, *, final: None
                with self.assertRaisesRegex(ClaudeInvocationError, "2.1.285 or newer"):
                    self._turn(launcher, "start")
                self.assertFalse((self.host_state / "claude-session.json").exists())

    def test_an_out_of_range_compaction_window_is_refused(self):
        for window in (99_999, 1_000_001, 256_000.0, True):
            with self.subTest(window=window):
                with self.assertRaisesRegex(ContractError, "autocompact window"):
                    ClaudeNativeSessionLauncher(
                        binary="/bin/claude",
                        cli_version="2.1.285",
                        autocompact_tokens=window,
                    )

    def test_every_supported_effort_reaches_claude_command(self):
        observed = 0
        for effort in ("low", "medium", "high", "xhigh"):
            observed += 1
            with self.subTest(effort=effort):
                launcher = ClaudeNativeSessionLauncher(
                    binary="/bin/claude",
                    cli_version="2.0.0",
                    model="claude-opus-5",
                    reasoning_effort=effort,
                )
                command = launcher._command(
                    self.run_root, "invent", session_id=None
                )
                self.assertEqual(
                    command[command.index("--model") + 1], "claude-opus-5"
                )
                self.assertEqual(command[command.index("--effort") + 1], effort)
        self.assertEqual(observed, 4)

    def test_clean_exit_without_finalizer_is_recoverable(self):
        from workshop.runtime.claude import ClaudeRecoverableInvocationError

        def popen(command, **kwargs):
            del command, kwargs
            return _FakeProcess([json.dumps({"type": "assistant"}) + "\n"])

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        marker = self.run_root / "agent-outcome.json"
        with self.assertRaises(ClaudeRecoverableInvocationError):
            launcher.start(
                product_id="wish-one",
                wish_sha256=DIGEST,
                constitution_sha256=DIGEST,
                run_root=self.run_root,
                host_state_root=self.host_state,
                prompt="make",
                finalization_marker=marker,
            )

    def test_rate_limit_is_a_hard_session_failure(self):
        from workshop.runtime.claude import ClaudeInvocationError

        def popen(command, **kwargs):
            del command, kwargs
            return _FakeProcess(
                [
                    json.dumps(
                        {
                            "type": "rate_limit_event",
                            "rate_limit_info": {"status": "rejected"},
                            "session_id": "claude-session-one",
                        }
                    )
                    + "\n",
                    json.dumps({"is_error": True, "session_id": "claude-session-one"})
                    + "\n",
                ],
                returncode=1,
            )

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        with self.assertRaisesRegex(ClaudeInvocationError, "weekly limit"):
            launcher.start(
                product_id="wish-one",
                wish_sha256=DIGEST,
                constitution_sha256=DIGEST,
                run_root=self.run_root,
                host_state_root=self.host_state,
                prompt="make",
            )

    def test_environment_keeps_the_macos_credential_account(self):
        """Without USER the CLI reports itself logged out mid-run."""

        environment = claude_subprocess_environment(
            {
                "PATH": "/usr/bin",
                "HOME": "/tmp/home",
                "USER": "operator",
                "LOGNAME": "operator",
            }
        )
        self.assertEqual(environment["USER"], "operator")
        self.assertEqual(environment["LOGNAME"], "operator")

    def test_error_turn_names_its_signature_without_quoting_the_turn(self):
        from workshop.runtime.claude import ClaudeInvocationError

        secret = "the Wish objective and workspace prose"

        def popen(command, **kwargs):
            del command, kwargs
            return _FakeProcess(
                [
                    json.dumps(
                        {
                            "type": "result",
                            "is_error": True,
                            "result": "Not logged in · Please run /login",
                            "session_id": "claude-session-one",
                        }
                    )
                    + "\n",
                ],
                returncode=1,
            )

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        with self.assertRaises(ClaudeInvocationError) as caught:
            launcher.start(
                product_id="wish-one",
                wish_sha256=DIGEST,
                constitution_sha256=DIGEST,
                run_root=self.run_root,
                host_state_root=self.host_state,
                prompt="make",
            )
        self.assertIn("signature=not-logged-in", str(caught.exception))
        self.assertNotIn(secret, str(caught.exception))
        self.assertNotIn("/login", str(caught.exception))

    def test_unclassified_error_turn_still_reports_a_signature(self):
        from workshop.runtime.claude import ClaudeInvocationError

        def popen(command, **kwargs):
            del command, kwargs
            return _FakeProcess(
                [
                    json.dumps(
                        {
                            "type": "result",
                            "is_error": True,
                            "result": "the printer bed is on fire",
                            "session_id": "claude-session-one",
                        }
                    )
                    + "\n",
                ],
                returncode=1,
            )

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        with self.assertRaisesRegex(ClaudeInvocationError, "signature=unclassified"):
            launcher.start(
                product_id="wish-one",
                wish_sha256=DIGEST,
                constitution_sha256=DIGEST,
                run_root=self.run_root,
                host_state_root=self.host_state,
                prompt="make",
            )

    def test_a_turn_that_dies_midflight_still_binds_the_real_session(self):
        """An hour of work must stay reopenable after a timed out clock."""

        from workshop.runtime.claude import ClaudeRecoverableInvocationError

        class _DyingProcess(_FakeProcess):
            def wait(self, timeout=None):
                del timeout
                raise subprocess.TimeoutExpired("claude", 1)

        turns = []
        lines = [
            json.dumps(
                {
                    "type": "system",
                    "subtype": "init",
                    "session_id": "claude-session-real",
                }
            )
            + "\n",
        ]

        def popen(command, **kwargs):
            del command, kwargs
            turns.append(1)
            if len(turns) == 1:
                return _DyingProcess(lines)
            return _FakeProcess(lines)

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.0.0",
            popen_factory=popen,
            uuid_factory=lambda: "host-invented-id",
        )
        with self.assertRaises(ClaudeRecoverableInvocationError):
            launcher.start(
                product_id="wish-one",
                wish_sha256=DIGEST,
                constitution_sha256=DIGEST,
                run_root=self.run_root,
                host_state_root=self.host_state,
                prompt="make",
            )
        payload = json.loads(
            (self.host_state / "claude-session.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["session_id"], "claude-session-real")
        self.assertNotEqual(payload["session_id"], "host-invented-id")
        resumed = launcher.resume(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="make",
        )
        self.assertEqual(resumed.session_id, "claude-session-real")

    def _rebind(self, launcher, constitution_sha256, **overrides):
        values = {
            "product_id": "wish-one",
            "wish_sha256": DIGEST,
            "run_root": self.run_root,
            "host_state_root": self.host_state,
            "constitution_sha256": constitution_sha256,
        }
        values.update(overrides)
        return launcher.rebind_session_constitution(**values)

    def test_rebind_session_constitution_moves_only_the_instruction_hash(self):
        """A host tool refresh reaches a Claude run by rebinding its record."""

        launcher = self._launcher_with_streams(
            [[_init_line(), _result_line()], [_init_line(), _result_line()]]
        )
        self._turn(launcher, "start")
        checkpoint = self.host_state / CLAUDE_SESSION_CHECKPOINT_NAME
        before = json.loads(checkpoint.read_text(encoding="utf-8"))
        corrected = "c" * 64

        result = self._rebind(launcher, corrected)

        self.assertEqual(
            result,
            {
                "session_id": SESSION,
                "previous_constitution_sha256": DIGEST,
                "constitution_sha256": corrected,
                "changed": True,
            },
        )
        after = json.loads(checkpoint.read_text(encoding="utf-8"))
        unchanged = {"constitution_sha256", "checkpoint_sha256"}
        self.assertEqual(
            {key: value for key, value in after.items() if key not in unchanged},
            {key: value for key, value in before.items() if key not in unchanged},
        )
        self.assertEqual(after["constitution_sha256"], corrected)
        self.assertEqual(
            after["checkpoint_sha256"],
            hashlib.sha256(
                _canonical_json(
                    {key: value for key, value in after.items() if key != "checkpoint_sha256"}
                )
            ).hexdigest(),
        )
        self.assertEqual(stat.S_IMODE(checkpoint.stat().st_mode), 0o600)
        self.assertFalse(self._rebind(launcher, corrected)["changed"])

        with self.assertRaisesRegex(ContractError, "checkpoint binding is invalid"):
            self._turn(launcher, "resume")
        resumed = launcher.resume(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=corrected,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="make",
        )
        self.assertEqual(resumed.session_id, SESSION)

    def test_rebind_session_constitution_refuses_another_binding_or_a_tampered_record(self):
        launcher = self._launcher_with_streams([[_init_line(), _result_line()]])
        self._turn(launcher, "start")
        checkpoint = self.host_state / CLAUDE_SESSION_CHECKPOINT_NAME
        for overrides in (
            {"wish_sha256": "d" * 64},
            {"product_id": "wish-two"},
            {"run_root": self.run_root.parent},
        ):
            with self.subTest(overrides=overrides), self.assertRaisesRegex(
                ContractError, "checkpoint binding is invalid"
            ):
                self._rebind(launcher, "e" * 64, **overrides)
        tampered = json.loads(checkpoint.read_text(encoding="utf-8"))
        tampered["session_id"] = "claude-session-other"
        checkpoint.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "checkpoint binding is invalid"):
            self._rebind(launcher, "e" * 64)

    def _launcher_with_streams(self, streams, returncodes=None):
        remaining = [list(lines) for lines in streams]
        codes = list(returncodes or [0] * len(remaining))

        def popen(command, **kwargs):
            del command, kwargs
            return _FakeProcess(remaining.pop(0), returncode=codes.pop(0))

        return ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.1.274",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )

    def _turn(self, launcher, method):
        return getattr(launcher, method)(
            product_id="wish-one",
            wish_sha256=DIGEST,
            constitution_sha256=DIGEST,
            run_root=self.run_root,
            host_state_root=self.host_state,
            prompt="make",
        )

    def _assert_unmeasured(self, outcome):
        for name in NATIVE_TOKEN_USAGE_FIELDS:
            self.assertIsNone(getattr(outcome, name))
        self.assertFalse(set(outcome.to_dict()) & set(NATIVE_TOKEN_USAGE_FIELDS))

    def test_terminal_model_usage_is_reduced_to_exact_bounded_token_counters(self):
        """The result's per-model totals are the turn's whole account.

        Claude Code repeats a non-final usage on every content-block event
        of one API message and never forwards subagent requests, so those
        events are not summed on top of the terminal totals, and the CLI's
        dollar estimate never reaches the outcome.
        """

        launcher = self._launcher_with_streams(
            [
                [
                    _init_line(),
                    _assistant_line("msg_01A", PER_BLOCK_USAGE),
                    _assistant_line("msg_01A", PER_BLOCK_USAGE),
                    json.dumps({"type": "user", "session_id": SESSION}) + "\n",
                    _assistant_line("msg_01B", PER_BLOCK_USAGE),
                    _result_line(
                        {
                            "claude-opus-5": OPUS_TOTALS,
                            "claude-haiku-4-5-20251001": HAIKU_TOTALS,
                        }
                    ),
                ]
            ]
        )
        started = self._turn(launcher, "start")
        self.assertEqual(started.input_tokens, OPUS_GROSS_INPUT + HAIKU_GROSS_INPUT)
        self.assertEqual(started.cached_input_tokens, 16_463_646 + 1_000)
        self.assertEqual(started.cache_write_input_tokens, 371_296 + 60)
        self.assertEqual(started.output_tokens, 245_325 + 100)
        self.assertEqual(started.reasoning_output_tokens, 181_276)
        payload = started.to_dict()
        self.assertEqual(payload["manager"], "claude")
        self.assertEqual(payload["input_tokens"], 16_836_200)
        self.assertEqual(payload["cached_input_tokens"], 16_464_646)
        self.assertEqual(payload["cache_write_input_tokens"], 371_356)
        self.assertEqual(payload["output_tokens"], 245_425)
        self.assertEqual(payload["reasoning_output_tokens"], 181_276)
        self.assertLessEqual(
            payload["cached_input_tokens"] + payload["cache_write_input_tokens"],
            payload["input_tokens"],
        )
        self.assertLessEqual(
            payload["reasoning_output_tokens"], payload["output_tokens"]
        )
        self.assertFalse(
            [key for key in payload if "cost" in key or "usd" in key or "total" in key]
        )

    def _budgeted_launcher(self, lines, observer, commands=None):
        processes = []

        def popen(command, **kwargs):
            del kwargs
            if commands is not None:
                commands.append(command)
            processes.append(_FakeProcess(lines))
            return processes[-1]

        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude",
            cli_version="2.1.285",
            popen_factory=popen,
            uuid_factory=lambda: "initial-session-id",
        )
        launcher.token_budget_observer = observer
        return launcher, processes

    def test_a_budget_observes_each_request_once_and_the_result_last(self):
        """Repeated blocks of one request count once; forwarded subagent
        requests count; the terminal totals raise, never lower, the count."""

        reports = []
        commands = []
        subagent = _assistant_line("msg_sub", PER_BLOCK_USAGE)
        subagent = json.dumps(
            {**json.loads(subagent), "parent_tool_use_id": "toolu_01"}
        ) + "\n"
        launcher, unused = self._budgeted_launcher(
            [
                _init_line(),
                _assistant_line("msg_01A", PER_BLOCK_USAGE),
                _assistant_line("msg_01A", PER_BLOCK_USAGE),
                subagent,
                _result_line({"claude-opus-5": OPUS_TOTALS}),
            ],
            lambda counters, *, final: reports.append((dict(counters), final)),
            commands,
        )
        self._turn(launcher, "start")
        self.assertIn("--forward-subagent-text", commands[0])
        request_input = 2 + 13_227 + 10_010
        self.assertEqual(
            [(counters["input_tokens"], final) for counters, final in reports],
            [
                (request_input, False),
                (2 * request_input, False),
                (OPUS_GROSS_INPUT, False),
                (OPUS_GROSS_INPUT, True),
            ],
        )
        final = reports[-1][0]
        self.assertEqual(final["output_tokens"], 245_325)
        self.assertEqual(final["reasoning_output_tokens"], 181_276)
        self.assertEqual(final["cached_input_tokens"], 16_463_646)

    def test_an_unbudgeted_turn_forwards_no_subagent_text(self):
        commands = []
        launcher, unused = self._budgeted_launcher(
            [_init_line(), _result_line({"claude-opus-5": OPUS_TOTALS})],
            None,
            commands,
        )
        self._turn(launcher, "start")
        self.assertNotIn("--forward-subagent-text", commands[0])

    def test_a_budget_stop_kills_the_turn_at_the_crossing_request(self):
        seen = []

        def observer(counters, *, final):
            seen.append(final)
            if counters["input_tokens"] > 30_000:
                raise RuntimeError("limit")

        launcher, processes = self._budgeted_launcher(
            [
                _init_line(),
                _assistant_line("msg_01A", PER_BLOCK_USAGE),
                _assistant_line("msg_01B", PER_BLOCK_USAGE),
                _assistant_line("msg_01C", PER_BLOCK_USAGE),
                _result_line({"claude-opus-5": OPUS_TOTALS}),
            ],
            observer,
        )
        with self.assertRaisesRegex(
            ClaudeInvocationError, CLAUDE_TOKEN_BUDGET_STOP_MESSAGE
        ):
            self._turn(launcher, "start")
        self.assertEqual(processes[0].returncode, -9)
        # The crossing report is the last one; no final report repeats it.
        self.assertEqual(seen, [False, False])

    def test_a_limit_reached_by_the_final_totals_stops_a_finished_turn(self):
        def observer(counters, *, final):
            if final:
                raise RuntimeError("limit")

        launcher, unused = self._budgeted_launcher(
            [_init_line(), _result_line({"claude-opus-5": OPUS_TOTALS})],
            observer,
        )
        with self.assertRaisesRegex(
            ClaudeInvocationError, CLAUDE_TOKEN_BUDGET_STOP_MESSAGE
        ):
            self._turn(launcher, "start")

    def test_a_turn_that_ends_early_still_charges_what_streamed(self):
        reports = []
        launcher, unused = self._budgeted_launcher(
            [_init_line(), _assistant_line("msg_01A", PER_BLOCK_USAGE)],
            lambda counters, *, final: reports.append((dict(counters), final)),
        )
        launcher_error = None
        try:
            self._turn(launcher, "start")
        except Exception as exc:  # the missing finalizer is not this test's subject
            launcher_error = exc
        del launcher_error
        self.assertEqual(reports[-1][1], True)
        self.assertEqual(reports[-1][0]["input_tokens"], 2 + 13_227 + 10_010)

    def test_a_stream_without_terminal_totals_is_truthfully_unmeasured(self):
        """No per-model totals means an unmeasured turn, never a guessed one.

        Per-block usage alone is not summed, and the result's ``usage``
        block is not a substitute because Claude Code documents it as either
        a running total or the main loop's turn-end value.
        """

        launcher = self._launcher_with_streams(
            [
                [
                    _init_line(),
                    _assistant_line("msg_01A", PER_BLOCK_USAGE),
                    _assistant_line("msg_01B", PER_BLOCK_USAGE),
                ],
                [_init_line(), _result_line()],
                [_init_line(), _result_line({})],
                [_init_line(), _result_line("not-a-mapping")],
            ]
        )
        self._assert_unmeasured(self._turn(launcher, "start"))
        for _ in range(3):
            self._assert_unmeasured(self._turn(launcher, "resume"))

    def test_partial_terminal_totals_keep_gross_counters_only(self):
        """A missing or inconsistent thinking subset drops the detail, not the base.

        Claude Code documents ``thinkingTokens`` as absent when no turn ran
        on a CLI version that records it, so the gross counters stay
        measured and the economics breakdown becomes unavailable, exactly
        like a base-only Codex turn.
        """

        without_thinking = {
            name: value
            for name, value in OPUS_TOTALS.items()
            if name != "thinkingTokens"
        }
        haiku_without_thinking = {
            name: value
            for name, value in HAIKU_TOTALS.items()
            if name != "thinkingTokens"
        }
        launcher = self._launcher_with_streams(
            [
                [_init_line(), _result_line({"claude-opus-5": without_thinking})],
                [
                    _init_line(),
                    _result_line(
                        {
                            "claude-opus-5": OPUS_TOTALS,
                            "claude-haiku-4-5-20251001": haiku_without_thinking,
                        }
                    ),
                ],
                [
                    _init_line(),
                    _result_line(
                        {
                            "claude-opus-5": {
                                **OPUS_TOTALS,
                                "thinkingTokens": OPUS_TOTALS["outputTokens"] + 1,
                            }
                        }
                    ),
                ],
                [
                    _init_line(),
                    _result_line(
                        {"claude-opus-5": {**OPUS_TOTALS, "outputTokens": -1}}
                    ),
                ],
                [
                    _init_line(),
                    _result_line(
                        {
                            "claude-opus-5": OPUS_TOTALS,
                            "claude-haiku-4-5-20251001": {
                                **HAIKU_TOTALS,
                                "cacheReadInputTokens": "1000",
                            },
                        }
                    ),
                ],
            ]
        )
        base_only = self._turn(launcher, "start")
        mixed = self._turn(launcher, "resume")
        inconsistent = self._turn(launcher, "resume")
        malformed = self._turn(launcher, "resume")
        malformed_detail = self._turn(launcher, "resume")
        for outcome in (base_only, inconsistent):
            self.assertEqual(outcome.input_tokens, OPUS_GROSS_INPUT)
            self.assertEqual(outcome.output_tokens, 245_325)
            self.assertIsNone(outcome.cached_input_tokens)
            self.assertIsNone(outcome.cache_write_input_tokens)
            self.assertIsNone(outcome.reasoning_output_tokens)
            self.assertEqual(
                set(outcome.to_dict()) & set(NATIVE_TOKEN_USAGE_FIELDS),
                {"input_tokens", "output_tokens"},
            )
        self.assertEqual(mixed.input_tokens, OPUS_GROSS_INPUT + HAIKU_GROSS_INPUT)
        self.assertEqual(mixed.output_tokens, 245_425)
        self.assertIsNone(mixed.reasoning_output_tokens)
        self.assertIsNone(mixed.cached_input_tokens)
        self._assert_unmeasured(malformed)
        self._assert_unmeasured(malformed_detail)

    def test_the_latest_result_replaces_an_earlier_running_total(self):
        """Claude Code says to read the latest result, never to sum results."""

        earlier = {
            "claude-opus-5": {
                **OPUS_TOTALS,
                "inputTokens": 10,
                "outputTokens": 20,
                "thinkingTokens": 5,
                "cacheReadInputTokens": 30,
                "cacheCreationInputTokens": 40,
            }
        }
        launcher = self._launcher_with_streams(
            [
                [
                    _init_line(),
                    _result_line(earlier, result_index=0),
                    _result_line({"claude-opus-5": OPUS_TOTALS}, result_index=1),
                ]
            ]
        )
        started = self._turn(launcher, "start")
        self.assertEqual(started.input_tokens, OPUS_GROSS_INPUT)
        self.assertEqual(started.cached_input_tokens, 16_463_646)
        self.assertEqual(started.cache_write_input_tokens, 371_296)
        self.assertEqual(started.output_tokens, 245_325)
        self.assertEqual(started.reasoning_output_tokens, 181_276)

    def test_an_error_result_with_zeroed_totals_is_a_failed_turn_not_zero_usage(self):
        """Claude Code zeroes usage on crash results; that is not a measurement."""

        from workshop.runtime.claude import ClaudeInvocationError

        zeroed = {
            "claude-opus-5": {
                **OPUS_TOTALS,
                "inputTokens": 0,
                "outputTokens": 0,
                "thinkingTokens": 0,
                "cacheReadInputTokens": 0,
                "cacheCreationInputTokens": 0,
            }
        }
        launcher = self._launcher_with_streams(
            [
                [
                    _init_line(),
                    _result_line(
                        zeroed,
                        subtype="error_during_execution",
                        is_error=True,
                        result="the provider stream closed",
                    ),
                ]
            ],
            returncodes=[1],
        )
        with self.assertRaisesRegex(ClaudeInvocationError, "error turn"):
            self._turn(launcher, "start")

    def test_outcome_contract_rejects_incomplete_or_inconsistent_usage(self):
        """The Claude outcome enforces the same usage contract as Codex."""

        def outcome(**usage):
            return ClaudeNativeSessionOutcome(SESSION, DIGEST, "2.1.274", **usage)

        with self.assertRaisesRegex(ContractError, "token usage is incomplete"):
            outcome(input_tokens=1)
        with self.assertRaisesRegex(ContractError, "token detail is incomplete"):
            outcome(input_tokens=1, output_tokens=1, cached_input_tokens=1)
        with self.assertRaisesRegex(ContractError, "token detail lacks usage"):
            outcome(
                cached_input_tokens=0,
                cache_write_input_tokens=0,
                reasoning_output_tokens=0,
            )
        with self.assertRaisesRegex(ContractError, "token usage is invalid"):
            outcome(input_tokens=-1, output_tokens=1)
        with self.assertRaisesRegex(ContractError, "token usage is invalid"):
            outcome(input_tokens=1.0, output_tokens=1)
        with self.assertRaisesRegex(ContractError, "token detail is invalid"):
            outcome(
                input_tokens=1,
                output_tokens=1,
                cached_input_tokens=2,
                cache_write_input_tokens=0,
                reasoning_output_tokens=0,
            )
        with self.assertRaisesRegex(ContractError, "token detail is invalid"):
            outcome(
                input_tokens=1,
                output_tokens=1,
                cached_input_tokens=0,
                cache_write_input_tokens=0,
                reasoning_output_tokens=2,
            )
        self.assertEqual(
            outcome(input_tokens=42, output_tokens=7).to_dict()["input_tokens"], 42
        )
