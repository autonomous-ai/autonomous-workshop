import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from workshop import invent, make, match, playtest, release
from workshop.release.agent import RewardedRelease
from workshop.invent.agent import CodexInventor
from workshop.make.agent import CodexMaker
from workshop.playtest.agent import LaneAwarePlaytester
from workshop.runtime.codex import (
    ALLOWED_WORKSHOP_MODELS,
    DEFAULT_CODEX_TIMEOUT_SECONDS,
    MAX_CODEX_EVENT_BYTES,
    MAX_CODEX_OUTPUT_BYTES,
    CodexInvocationError,
    CodexStructuredRunner,
)
from workshop.errors import ContractError
from workshop.match.semantic import CodexSemanticManager


class EnvironmentRecordingRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((tuple(command), dict(kwargs.get("env", {}))))
        if "--version" in command:
            return subprocess.CompletedProcess(command, 0, "codex-cli 2.3.4\n", "")
        output = Path(command[command.index("--output-last-message") + 1])
        output.write_text(json.dumps({"ok": True}), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")


class ScriptedInvocationRunner:
    def __init__(self, scripts):
        self.scripts = list(scripts)
        self.calls = []
        self.output_paths = []

    def __call__(self, command, **kwargs):
        command = tuple(command)
        self.calls.append((command, dict(kwargs)))
        output = Path(command[command.index("--output-last-message") + 1])
        self.output_paths.append(output)
        script = self.scripts.pop(0)
        if "payload" in script:
            output.write_text(json.dumps(script["payload"]), encoding="utf-8")
        if "raw_output" in script:
            output.write_bytes(script["raw_output"])
        return subprocess.CompletedProcess(
            command,
            script.get("returncode", 0),
            script.get("stdout", ""),
            script.get("stderr", ""),
        )


class CodexModelPolicyTest(unittest.TestCase):
    def test_stage_output_schemas_leave_uniqueness_to_trusted_validation(self):
        modules = (
            release.agent,
            invent.agent,
            make.agent,
            match.semantic,
            playtest.agent,
        )

        def unsupported_paths(value, path="schema"):
            if isinstance(value, dict):
                properties = value.get("properties")
                if isinstance(properties, dict):
                    required = value.get("required")
                    if not isinstance(required, list) or set(required) != set(
                        properties
                    ):
                        yield path + ".required"
                for key, child in value.items():
                    current = "%s.%s" % (path, key)
                    if key == "uniqueItems":
                        yield current
                    yield from unsupported_paths(child, current)
            elif isinstance(value, (list, tuple)):
                for index, child in enumerate(value):
                    yield from unsupported_paths(child, "%s[%d]" % (path, index))

        offenders = []
        for module in modules:
            for name, value in vars(module).items():
                if name.endswith("_SCHEMA") and isinstance(value, dict):
                    offenders.extend(
                        "%s.%s:%s" % (module.__name__, name, path)
                        for path in unsupported_paths(value)
                    )
        self.assertEqual(
            offenders,
            [],
            "Codex structured outputs reject uniqueItems and optional object "
            "properties; trusted stage validation must enforce uniqueness after "
            "decoding and each lane must supply one exact strict schema",
        )

    def test_only_terra_and_luna_are_accepted_by_the_shared_runner(self):
        self.assertEqual(
            ALLOWED_WORKSHOP_MODELS,
            frozenset(("gpt-5.6-terra", "gpt-5.6-luna")),
        )
        for model in sorted(ALLOWED_WORKSHOP_MODELS):
            with self.subTest(model=model), mock.patch(
                "workshop.runtime.codex.shutil.which", return_value=None
            ):
                selected = CodexStructuredRunner(
                    model=model,
                    reasoning_effort="low",
                )
            self.assertEqual(selected.model, model)

    def test_long_form_stage_calls_have_a_bounded_twenty_minute_default(self):
        with mock.patch("workshop.runtime.codex.shutil.which", return_value=None):
            selected = CodexStructuredRunner(
                model="gpt-5.6-terra",
                reasoning_effort="high",
            )
        self.assertEqual(DEFAULT_CODEX_TIMEOUT_SECONDS, 1_200)
        self.assertEqual(selected.timeout_seconds, DEFAULT_CODEX_TIMEOUT_SECONDS)
        for timeout in (True, 0, -1, 3_601, 1.5, "1200"):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                CodexStructuredRunner(
                    model="gpt-5.6-terra",
                    reasoning_effort="high",
                    binary="/not/run/codex",
                    timeout_seconds=timeout,
                )

    def test_long_form_creator_defaults_use_bounded_low_reasoning(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch(
            "workshop.runtime.codex.shutil.which", return_value=None
        ):
            inventor = CodexInventor(research_provider=None)
            maker = CodexMaker(cad_builder=object())
        self.assertEqual(inventor.creator.reasoning_effort, "low")
        self.assertEqual(maker.creator.reasoning_effort, "low")
        self.assertEqual(inventor.evaluator.reasoning_effort, "low")
        self.assertEqual(maker.evaluator.reasoning_effort, "low")

    def test_explicit_sol_or_arbitrary_model_is_rejected_before_subprocess(self):
        runner = mock.Mock(side_effect=AssertionError("must not launch Codex"))
        for model in ("gpt-5.6-sol", "gpt-5.5", "terra", "", None):
            with self.subTest(model=model), self.assertRaises(ContractError):
                CodexStructuredRunner(
                    model=model,
                    reasoning_effort="low",
                    binary="/not/run/codex",
                    runner=runner,
                )
        runner.assert_not_called()

    def test_every_stage_model_environment_rejects_sol(self):
        cases = (
            ("WORKSHOP_MANAGER_MODEL", CodexSemanticManager),
            ("WORKSHOP_INVENT_MODEL", CodexInventor),
            ("WORKSHOP_REWARD_MODEL", CodexInventor),
            ("WORKSHOP_MAKE_MODEL", CodexMaker),
            ("WORKSHOP_MAKE_REWARD_MODEL", CodexMaker),
            ("WORKSHOP_PLAYTEST_MODEL", LaneAwarePlaytester),
            ("WORKSHOP_RELEASE_MODEL", RewardedRelease),
            ("WORKSHOP_RELEASE_REWARD_MODEL", RewardedRelease),
        )
        for variable, constructor in cases:
            with self.subTest(variable=variable), mock.patch.dict(
                os.environ,
                {variable: "gpt-5.6-sol"},
                clear=True,
            ), mock.patch(
                "workshop.runtime.codex.shutil.which", return_value=None
            ), self.assertRaises(ContractError):
                constructor()

    def test_codex_and_manager_probes_and_calls_receive_only_codex_auth(self):
        parent_environment = {
            "PATH": "/fixture/bin:/usr/bin",
            "HOME": "/fixture/home",
            "CODEX_HOME": "/fixture/codex-home",
            "OPENAI_API_KEY": "fixture-codex-auth",
            "CODEX_API_KEY": "fixture-codex-api-auth",
            "FACTORY_USERNAME": "alice",
            "FACTORY_PASSWORD": "must-not-reach-codex",
            "WORKSHOP_SHOP_TOKEN": "must-not-reach-codex",
            "AWS_SECRET_ACCESS_KEY": "must-not-reach-codex",
            "GITHUB_TOKEN": "must-not-reach-codex",
        }
        structured_runner = EnvironmentRecordingRunner()
        manager_runner = EnvironmentRecordingRunner()
        with mock.patch.dict(os.environ, parent_environment, clear=True):
            structured = CodexStructuredRunner(
                model="gpt-5.6-terra",
                reasoning_effort="low",
                binary="/fixture/codex",
                runner=structured_runner,
            )
            self.assertEqual(
                structured.invoke(
                    prompt="fixture",
                    schema={"type": "object", "additionalProperties": True},
                ),
                {"ok": True},
            )
            manager = CodexSemanticManager(
                binary="/fixture/codex",
                runner=manager_runner,
            )
            self.assertEqual(
                manager._invoke(
                    prompt="fixture",
                    schema={"type": "object", "additionalProperties": True},
                    capability="semantic-inventor-retriever",
                ),
                {"ok": True},
            )

        for calls in (structured_runner.calls, manager_runner.calls):
            self.assertEqual(len(calls), 2)
            self.assertIn("--version", calls[0][0])
            for unused_command, environment in calls:
                self.assertEqual(environment["HOME"], "/fixture/home")
                self.assertEqual(environment["CODEX_HOME"], "/fixture/codex-home")
                self.assertEqual(environment["OPENAI_API_KEY"], "fixture-codex-auth")
                self.assertEqual(environment["CODEX_API_KEY"], "fixture-codex-api-auth")
                for forbidden in (
                    "FACTORY_USERNAME",
                    "FACTORY_PASSWORD",
                    "WORKSHOP_SHOP_TOKEN",
                    "AWS_SECRET_ACCESS_KEY",
                    "GITHUB_TOKEN",
                ):
                    self.assertNotIn(forbidden, environment)


class CodexStructuredInvocationTest(unittest.TestCase):
    def runner(self, scripts, *, timeout_seconds=30):
        scripted = ScriptedInvocationRunner(scripts)
        return (
            CodexStructuredRunner(
                model="gpt-5.6-terra",
                reasoning_effort="low",
                binary="/fixture/codex",
                timeout_seconds=timeout_seconds,
                runner=scripted,
                cli_version="2.3.4",
            ),
            scripted,
        )

    def test_native_web_search_is_explicit_and_requires_a_jsonl_search_event(self):
        event = json.dumps(
            {
                "type": "item.completed",
                "item": {"id": "search-1", "type": "web_search"},
            }
        )
        selected, scripted = self.runner(
            [{"payload": {"sources": ["verified"]}, "stdout": event + "\n"}]
        )

        result = selected.invoke(
            prompt="research without leaking this into argv",
            schema={"type": "object", "additionalProperties": True},
            native_web_search=True,
        )

        self.assertEqual(result, {"sources": ["verified"]})
        self.assertTrue(selected.last_used_web_search)
        command, call = scripted.calls[0]
        self.assertEqual(command[:3], ("/fixture/codex", "--search", "exec"))
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--json", command)
        self.assertNotIn("research without leaking this into argv", command)
        self.assertEqual(call["input"], "research without leaking this into argv")

        missing, missing_runner = self.runner(
            [
                {
                    "payload": {"sources": ["unverified"]},
                    "stdout": json.dumps({"type": "turn.completed"}) + "\n",
                }
            ]
        )
        with self.assertRaisesRegex(CodexInvocationError, "without a web search event"):
            missing.invoke(
                prompt="research",
                schema={"type": "object", "additionalProperties": True},
                native_web_search=True,
            )
        self.assertFalse(missing.last_used_web_search)
        self.assertEqual(len(missing_runner.calls), 1)

    def test_regular_structured_call_keeps_search_off_and_fake_runner_compatibility(self):
        selected, scripted = self.runner([{"payload": {"ok": True}}])
        self.assertEqual(
            selected.invoke(
                prompt="fixture",
                schema={"type": "object", "additionalProperties": True},
            ),
            {"ok": True},
        )
        self.assertFalse(selected.last_used_web_search)
        command = scripted.calls[0][0]
        self.assertEqual(command[:2], ("/fixture/codex", "exec"))
        self.assertNotIn("--search", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--json", command)

    def test_only_explicit_transient_disconnect_gets_one_fresh_bounded_retry(self):
        secret = "FACTORY_PASSWORD=never-show-this"
        selected, scripted = self.runner(
            [
                {
                    "returncode": 1,
                    "raw_output": b'{"partial":"must-not-be-used"}',
                    "stderr": secret + "\nERROR: stream disconnected before completion",
                },
                {"payload": {"ok": "second-attempt"}},
            ],
            timeout_seconds=10,
        )
        with mock.patch(
            "workshop.runtime.codex.time.monotonic", side_effect=[100.0, 100.0, 103.0]
        ):
            result = selected.invoke(
                prompt="private prompt sentinel",
                schema={"type": "object", "additionalProperties": True},
            )

        self.assertEqual(result, {"ok": "second-attempt"})
        self.assertEqual(len(scripted.calls), 2)
        self.assertNotEqual(scripted.output_paths[0], scripted.output_paths[1])
        self.assertEqual(
            [call[1]["timeout"] for call in scripted.calls],
            [10.0, 7.0],
        )
        self.assertEqual(
            [call[1]["input"] for call in scripted.calls],
            ["private prompt sentinel", "private prompt sentinel"],
        )
        for command, unused_call in scripted.calls:
            self.assertNotIn("resume", command)

    def test_non_transient_failure_never_retries_or_exposes_diagnostics(self):
        diagnostics = (
            "authentication failed private prompt sentinel "
            "FACTORY_PASSWORD=never-show-this"
        )
        selected, scripted = self.runner(
            [
                {
                    "returncode": 1,
                    "stderr": diagnostics,
                    "payload": {"must": "not be accepted after nonzero exit"},
                }
            ]
        )
        with self.assertRaises(CodexInvocationError) as caught:
            selected.invoke(
                prompt="private prompt sentinel",
                schema={"type": "object", "additionalProperties": True},
            )
        rendered = str(caught.exception)
        self.assertEqual(len(scripted.calls), 1)
        self.assertNotIn("private prompt sentinel", rendered)
        self.assertNotIn("FACTORY_PASSWORD", rendered)
        self.assertNotIn("authentication failed", rendered)

    def test_a_second_transient_failure_stops_without_leaking_raw_output(self):
        diagnostics = (
            "stream disconnected before completion; "
            "private prompt sentinel; FACTORY_PASSWORD=never-show-this"
        )
        selected, scripted = self.runner(
            [
                {"returncode": 1, "stderr": diagnostics},
                {"returncode": 1, "stderr": diagnostics},
            ]
        )
        with self.assertRaisesRegex(
            CodexInvocationError, "provider transport failed after one retry"
        ) as caught:
            selected.invoke(
                prompt="private prompt sentinel",
                schema={"type": "object", "additionalProperties": True},
            )
        self.assertEqual(len(scripted.calls), 2)
        self.assertNotIn("private prompt sentinel", str(caught.exception))
        self.assertNotIn("FACTORY_PASSWORD", str(caught.exception))

    def test_timeout_is_not_retried_and_has_no_sensitive_exception_cause(self):
        calls = []

        def timeout_runner(command, **kwargs):
            calls.append((command, kwargs))
            raise subprocess.TimeoutExpired(
                command,
                kwargs["timeout"],
                output="private prompt sentinel",
                stderr="FACTORY_PASSWORD=never-show-this",
            )

        selected = CodexStructuredRunner(
            model="gpt-5.6-terra",
            reasoning_effort="low",
            binary="/fixture/codex",
            timeout_seconds=10,
            runner=timeout_runner,
            cli_version="2.3.4",
        )
        with self.assertRaisesRegex(CodexInvocationError, "timed out") as caught:
            selected.invoke(
                prompt="private prompt sentinel",
                schema={"type": "object", "additionalProperties": True},
            )
        self.assertEqual(len(calls), 1)
        self.assertIsNone(caught.exception.__cause__)
        self.assertIsNone(caught.exception.__context__.output)
        self.assertIsNone(caught.exception.__context__.stderr)
        self.assertNotIn("private prompt sentinel", str(caught.exception))
        self.assertNotIn("FACTORY_PASSWORD", str(caught.exception))

    def test_structured_result_and_event_stream_are_size_bounded(self):
        oversized_output, output_runner = self.runner(
            [{"raw_output": b"x" * (MAX_CODEX_OUTPUT_BYTES + 1)}]
        )
        with self.assertRaisesRegex(CodexInvocationError, "safe size limit"):
            oversized_output.invoke(
                prompt="fixture",
                schema={"type": "object", "additionalProperties": True},
            )
        self.assertEqual(len(output_runner.calls), 1)

        oversized_events, event_runner = self.runner(
            [
                {
                    "payload": {"ok": True},
                    "stdout": "x" * (MAX_CODEX_EVENT_BYTES + 1),
                }
            ]
        )
        with self.assertRaisesRegex(CodexInvocationError, "event stream"):
            oversized_events.invoke(
                prompt="fixture",
                schema={"type": "object", "additionalProperties": True},
            )
        self.assertEqual(len(event_runner.calls), 1)

    def test_invalid_or_missing_structured_results_fail_closed(self):
        cases = (
            ({}, "no structured result"),
            ({"raw_output": b"not-json"}, "no valid structured result"),
            ({"payload": ["not", "an", "object"]}, "must be an object"),
        )
        for script, message in cases:
            with self.subTest(message=message):
                selected, scripted = self.runner([script])
                with self.assertRaisesRegex(CodexInvocationError, message):
                    selected.invoke(
                        prompt="fixture",
                        schema={"type": "object", "additionalProperties": True},
                    )
                self.assertEqual(len(scripted.calls), 1)

    def test_native_web_search_flag_requires_a_real_boolean(self):
        for value in (None, 0, 1, "true"):
            with self.subTest(value=value):
                selected, scripted = self.runner([])
                with self.assertRaises(ValueError):
                    selected.invoke(
                        prompt="fixture",
                        schema={"type": "object", "additionalProperties": True},
                        native_web_search=value,
                    )
                self.assertEqual(scripted.calls, [])


if __name__ == "__main__":
    unittest.main()
