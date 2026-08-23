import json
import os
import signal
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from alice.cli import _engine
from alice.codex_provider import (
    CODEX_CONFIG_SHA256,
    CODEX_TRANSPORT_SCHEMA,
    CodexAppServerProvider,
    REJECTION,
)
from alice.config import load_config, resolve_runtime_paths
from alice.providers import AgentRequest, ProviderError


_FAKE_CODEX = r'''
import json
import os
import signal
import sys
import time


def send(value):
    sys.stdout.write(json.dumps(value, separators=(",", ":")) + "\n")
    sys.stdout.flush()


mode = os.environ.get("FAKE_CODEX_MODE", "success")
if sys.argv[1:] == ["login", "status"]:
    if os.environ.get("FAKE_SIGNED_IN") == "1":
        print("Logged in using isolated test credentials")
        raise SystemExit(0)
    print("Not logged in: credential-auth-marker", file=sys.stderr)
    raise SystemExit(1)

if sys.argv[1:] != ["app-server", "--stdio"]:
    raise SystemExit(64)

if mode == "timeout":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

thread_options = {}
for line in sys.stdin:
    message = json.loads(line)
    method = message.get("method")
    if method == "initialize":
        if mode == "initialize-error":
            send({"id": message["id"], "error": {
                "code": -32000, "message": "credential-initialize-marker"}})
        else:
            send({"id": message["id"], "result": {"serverInfo": {"name": "fake"}}})
    elif method == "initialized":
        continue
    elif method == "thread/start":
        thread_options = message["params"]
        send({"id": message["id"], "result": {"thread": {"id": "thread-test-123"}}})
    elif method == "turn/start":
        params = message["params"]
        send({"id": message["id"], "result": {"turn": {"id": "turn-test-456"}}})
        if mode == "parent-sigterm":
            os.kill(os.getppid(), signal.SIGTERM)
            time.sleep(60)
            continue
        if mode == "timeout":
            time.sleep(60)
            continue
        if mode == "oversize":
            send({"method": "item/agentMessage/delta", "params": {
                "threadId": "thread-test-123", "delta": "x" * 10000}})
            time.sleep(60)
            continue

        methods = [
            "item/commandExecution/requestApproval",
            "execCommandApproval",
            "applyPatchApproval",
            "item/fileChange/requestApproval",
            "item/permissions/requestApproval",
            "item/tool/requestUserInput",
            "item/tool/call",
            "invented/serverMethod",
        ]
        denials = []
        for number, server_method in enumerate(methods, 900):
            send({"id": number, "method": server_method, "params": {"anything": True}})
            reply = json.loads(sys.stdin.readline())
            denials.append(reply)

        request = json.loads(params["input"][0]["text"])
        schema = params.get("outputSchema") or {}
        config = thread_options.get("config") or {}
        content = {
            "ok": True,
            "request_id_seen": request.get("request_id"),
            "schema_ok": (
                schema.get("additionalProperties") is False
                and set(schema.get("required") or [])
                == {"content_json", "claims_json", "artifacts_json", "confidence"}
                and schema.get("properties", {}).get("content_json", {}).get("type") == "string"
            ),
            "lockdown_ok": (
                thread_options.get("sandbox") == "read-only"
                and thread_options.get("ephemeral") is True
                and config.get("approval_policy") == "untrusted"
                and config.get("agents", {}).get("enabled") is False
                and config.get("features", {}).get("apps") is False
            ),
            "base_instructions_present": bool(thread_options.get("baseInstructions")),
            "cwd": thread_options.get("cwd"),
            "codex_home": os.environ.get("CODEX_HOME"),
            "secret_forwarded": "ALICE_TEST_SECRET" in os.environ,
            "denials": denials,
        }
        if mode == "bad-envelope":
            answer = json.dumps({
                "content_json": content,
                "claims_json": "[]",
                "artifacts_json": "[]",
                "confidence": 0.8,
            })
        else:
            answer = json.dumps({
                "content_json": json.dumps(content, separators=(",", ":")),
                "claims_json": json.dumps([{"evidence_class": "surrogate"}]),
                "artifacts_json": "[]",
                "confidence": 0.8,
            }, separators=(",", ":"))
        send({"method": "item/agentMessage/delta", "params": {
            "threadId": "thread-test-123", "delta": answer[:len(answer) // 2]}})
        send({"method": "item/completed", "params": {
            "threadId": "thread-test-123",
            "item": {"type": "agentMessage", "text": answer}}})
        send({"method": "thread/tokenUsage/updated", "params": {
            "threadId": "thread-test-123", "tokenUsage": {"last": {"inputTokens": 10}}}})
        send({"method": "turn/completed", "params": {
            "threadId": "thread-test-123",
            "turn": {"id": "turn-test-456", "status": "completed", "durationMs": 5}}})
'''


class CodexProviderTests(unittest.TestCase):
    def _fake_binary(self, directory: str) -> Path:
        path = Path(directory) / "fake-codex"
        path.write_text(f"#!{sys.executable}\n{_FAKE_CODEX}", encoding="utf-8")
        path.chmod(0o755)
        return path

    def _provider(
        self,
        directory: str,
        *,
        mode: str = "success",
        timeout: float = 2.0,
        grace: float = 0.2,
        max_output_bytes: int = 200_000,
    ) -> CodexAppServerProvider:
        binary = self._fake_binary(directory)
        environment = {
            "FAKE_CODEX_MODE": mode,
            "FAKE_SIGNED_IN": "1",
            "ALICE_TEST_SECRET": "must-not-leak",
        }
        with patch.dict(os.environ, environment):
            return CodexAppServerProvider(
                binary=str(binary),
                codex_home=Path(directory) / "codex-home",
                model="test-model",
                effort="low",
                timeout_seconds=timeout,
                startup_timeout_seconds=min(1.0, timeout),
                shutdown_grace_seconds=grace,
                max_output_bytes=max_output_bytes,
                allowed_environment=("PATH", "FAKE_CODEX_MODE", "FAKE_SIGNED_IN"),
            )

    def test_real_jsonl_round_trip_is_locked_down_and_denies_every_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = self._provider(directory)
            response = provider.run(
                AgentRequest(
                    "request-123",
                    "inventor_divergent",
                    "Invent one game",
                    {"known": "surrogate only"},
                    {"type": "object"},
                )
            )

            self.assertEqual(response.request_id, "request-123")
            self.assertEqual(response.provider_run_id, "thread-test-123")
            self.assertEqual(response.claims, ({"evidence_class": "surrogate"},))
            self.assertEqual(response.confidence, 0.8)
            self.assertTrue(response.content["schema_ok"])
            self.assertTrue(response.content["lockdown_ok"])
            self.assertTrue(response.content["base_instructions_present"])
            self.assertFalse(response.content["secret_forwarded"])
            self.assertEqual(response.content["codex_home"], str(Path(directory) / "codex-home"))
            self.assertFalse(Path(response.content["cwd"]).exists())

            replies = response.content["denials"]
            denied = {"decision": {"denied": {"rejection": REJECTION}}}
            self.assertEqual([item["result"] for item in replies[:3]], [denied] * 3)
            self.assertEqual(replies[3]["result"], {"decision": "decline"})
            self.assertEqual(replies[4]["result"], {"permissions": {}})
            self.assertEqual(replies[5]["result"], {"answers": {}})
            self.assertEqual(
                replies[6]["result"],
                {
                    "success": False,
                    "contentItems": [{"type": "inputText", "text": REJECTION}],
                },
            )
            self.assertEqual(replies[7]["error"]["code"], -32601)

            config_path = Path(directory) / "codex-home" / "config.toml"
            self.assertTrue(config_path.is_file())
            self.assertEqual(stat.S_IMODE(config_path.stat().st_mode), 0o600)
            diagnostics = provider.diagnostics()
            self.assertTrue(diagnostics["ready"])
            self.assertTrue(diagnostics["auth"]["signed_in"])
            self.assertTrue(diagnostics["auth"]["credential_files_secure"])
            self.assertTrue(diagnostics["codex_home"]["isolated"])
            self.assertTrue(diagnostics["config"]["matches_lockdown"])
            self.assertTrue(diagnostics["app_server"]["initialized"])
            self.assertEqual(diagnostics["config"]["sha256"], CODEX_CONFIG_SHA256)
            self.assertEqual(provider.doctor(), diagnostics)
            self.assertEqual(
                provider.last_run_diagnostics["refused_server_requests"],
                [
                    "item/commandExecution/requestApproval",
                    "execCommandApproval",
                    "applyPatchApproval",
                    "item/fileChange/requestApproval",
                    "item/permissions/requestApproval",
                    "item/tool/requestUserInput",
                    "item/tool/call",
                    "invented/serverMethod",
                ],
            )

    def test_rejects_non_string_transport_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = self._provider(directory, mode="bad-envelope")
            with self.assertRaisesRegex(ProviderError, "content_json must be a JSON string"):
                provider.run(AgentRequest("bad-envelope", "archivist", "compact", {}))

    def test_output_byte_cap_stops_an_oversize_stream(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = self._provider(directory, mode="oversize", max_output_bytes=128)
            with self.assertRaisesRegex(ProviderError, "exceeded max_output_bytes"):
                provider.run(AgentRequest("too-large", "rules_engineer", "rules", {}))
            self.assertEqual(provider.last_run_diagnostics["status"], "failed")

    @unittest.skipUnless(hasattr(os, "killpg"), "POSIX process groups required")
    def test_timeout_terms_then_kills_the_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            # Leave enough time for Python startup so SIGTERM lands after the
            # fake app-server installs its ignore handler.
            provider = self._provider(directory, mode="timeout", timeout=1.5, grace=0.1)
            calls = []
            real_killpg = os.killpg

            def tracking_killpg(pid: int, sig: signal.Signals) -> None:
                calls.append((pid, sig))
                real_killpg(pid, sig)

            started = time.monotonic()
            with patch("alice.codex_provider.os.killpg", side_effect=tracking_killpg):
                with self.assertRaisesRegex(ProviderError, "timed out"):
                    provider.run(AgentRequest("timeout", "critic", "critique", {}))
            self.assertLess(time.monotonic() - started, 4.0)
            self.assertIn(signal.SIGTERM, [sig for _, sig in calls])
            self.assertIn(signal.SIGKILL, [sig for _, sig in calls])

    def test_constructor_rejects_the_operators_default_codex_home(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be dedicated"):
            CodexAppServerProvider(codex_home=Path.home() / ".codex")

    def test_diagnostics_require_a_real_initialize_handshake_and_redact_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = self._provider(directory, mode="initialize-error")

            diagnostics = provider.diagnostics()

            serialized = json.dumps(diagnostics, sort_keys=True)
            self.assertFalse(diagnostics["ready"])
            self.assertFalse(diagnostics["app_server"]["initialized"])
            self.assertIn("initialize_failed", diagnostics["app_server"]["status"])
            self.assertNotIn("credential-initialize-marker", serialized)

    def test_auth_status_does_not_display_raw_login_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = self._provider(directory)
            provider.environment["FAKE_SIGNED_IN"] = "0"

            diagnostics = provider.diagnostics()

            serialized = json.dumps(diagnostics, sort_keys=True)
            self.assertFalse(diagnostics["ready"])
            self.assertEqual(diagnostics["auth"]["status"], "not_signed_in")
            self.assertNotIn("credential-auth-marker", serialized)
            self.assertNotIn("Not logged in", serialized)

    def test_rejects_symlink_nonregular_and_unsafe_equivalent_credentials(self) -> None:
        cases = ("symlink", "directory", "unsafe-mode")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                provider = self._provider(directory)
                provider.codex_home.mkdir(mode=0o700)
                credential = provider.codex_home / (
                    "credentials.json" if case == "unsafe-mode" else "auth.json"
                )
                if case == "symlink":
                    target = Path(directory) / "outside-auth.json"
                    target.write_text("secret", encoding="utf-8")
                    credential.symlink_to(target)
                elif case == "directory":
                    credential.mkdir(mode=0o700)
                else:
                    credential.write_text("secret", encoding="utf-8")
                    credential.chmod(0o640)

                diagnostics = provider.diagnostics()
                self.assertFalse(diagnostics["ready"])
                self.assertFalse(diagnostics["auth"]["credential_files_secure"])
                with self.assertRaisesRegex(ProviderError, "credential boundary"):
                    provider.run(AgentRequest("unsafe-auth", "critic", "test", {}))

    def test_accepts_owner_only_auth_file_without_reading_or_reporting_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = self._provider(directory)
            provider.codex_home.mkdir(mode=0o700)
            auth = provider.codex_home / "auth.json"
            secret = "sk-secure-auth-value"
            auth.write_text(secret, encoding="utf-8")
            auth.chmod(0o600)

            diagnostics = provider.diagnostics()

            self.assertTrue(diagnostics["ready"])
            self.assertEqual(diagnostics["auth"]["credential_files_checked"], 1)
            self.assertNotIn(secret, json.dumps(diagnostics, sort_keys=True))

    @unittest.skipUnless(hasattr(os, "killpg"), "POSIX process groups required")
    def test_parent_sigterm_is_scoped_to_active_app_server_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = self._provider(directory, mode="parent-sigterm")
            calls = []
            real_killpg = os.killpg

            def tracking_killpg(pid: int, sig: signal.Signals) -> None:
                calls.append((pid, sig))
                real_killpg(pid, sig)

            with patch("alice.providers.os.killpg", side_effect=tracking_killpg):
                with self.assertRaises(SystemExit):
                    provider.run(AgentRequest("sigterm", "critic", "test", {}))

            self.assertIn(signal.SIGTERM, [sig for _, sig in calls])
            self.assertEqual(len({pid for pid, _ in calls}), 1)

    def test_cli_wires_resolved_codex_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = resolve_runtime_paths(load_config(), directory)
            config["agents"]["provider"] = "codex"
            with patch("alice.cli.CodexAppServerProvider") as provider_class:
                engine = _engine(object(), config)
            kwargs = provider_class.call_args.kwargs
            self.assertIs(engine.provider, provider_class.return_value)
            self.assertEqual(
                kwargs["codex_home"], str(Path(directory).resolve() / "var/codex-home")
            )
            self.assertEqual(kwargs["model"], "gpt-5.6-sol")
            self.assertEqual(kwargs["max_output_bytes"], 200_000)
            self.assertEqual(CODEX_TRANSPORT_SCHEMA["additionalProperties"], False)


if __name__ == "__main__":
    unittest.main()
