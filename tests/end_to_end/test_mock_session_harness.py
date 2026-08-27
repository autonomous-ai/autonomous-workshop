import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from workshop.errors import ContractError
from workshop.integrations.factory import (
    DEFAULT_FACTORY_API,
    FactoryAgentCredentials,
    FactoryAgentSession,
)

from tests.end_to_end.mock_codex_passthrough import DIRECTIVE
from tests.end_to_end.mock_session_harness import (
    CONTEXT_KIND,
    MAX_CONTEXT_RECORD_BYTES,
    MockSessionEvidenceError,
    MockSessionPrerequisiteError,
    _assert_no_secrets,
    preflight_codex,
    redact_diagnostics,
    run_bounded_process,
    validate_concept_boundary_instruction,
    validate_context_record,
    validate_stage_packet_inputs,
)
from tests.end_to_end.mock_session_protocols import MockSessionProtocolServer
from workshop.workflow.native_run import NativeRunExternalTransports


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class _Result:
    def __init__(self, returncode=0, stdout=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


class MockSessionPreflightTest(unittest.TestCase):
    def test_missing_unsupported_and_unauthenticated_codex_fail_before_a_run(self):
        with self.assertRaisesRegex(MockSessionPrerequisiteError, "not installed"):
            preflight_codex(
                which=lambda unused: None,
                module_finder=lambda unused: object(),
            )

        calls = []

        def unsupported(arguments, **unused):
            calls.append(arguments)
            return _Result(stdout="codex-cli 0.1.0")

        with self.assertRaisesRegex(MockSessionPrerequisiteError, "missing native"):
            preflight_codex(
                which=lambda unused: "/bin/codex",
                runner=unsupported,
                module_finder=lambda unused: object(),
            )
        self.assertEqual(len(calls), 1)

        def unauthenticated(arguments, **unused):
            if arguments[-1] == "--version":
                return _Result(stdout="codex-cli 0.145.0")
            return _Result(returncode=1)

        with self.assertRaisesRegex(MockSessionPrerequisiteError, "not authenticated"):
            preflight_codex(
                which=lambda unused: "/bin/codex",
                runner=unauthenticated,
                module_finder=lambda unused: object(),
            )

    def test_missing_cad_runtime_fails_before_codex_or_a_run(self):
        queried = []

        with self.assertRaisesRegex(
            MockSessionPrerequisiteError,
            "active Python interpreter lacks the CAD runtime.*build123d",
        ):
            preflight_codex(
                which=lambda name: queried.append(name),
                module_finder=lambda name: None if name == "build123d" else object(),
            )
        self.assertEqual(queried, [])

    def test_supported_authenticated_codex_passes(self):
        def runner(arguments, **unused):
            return _Result(stdout="codex-cli 0.145.0" if arguments[-1] == "--version" else "logged in")

        result = preflight_codex(
            which=lambda unused: "/bin/codex",
            runner=runner,
            module_finder=lambda unused: object(),
        )
        self.assertEqual(result.version, "0.145.0")
        self.assertTrue(result.authenticated)
        self.assertTrue(result.cad_runtime_ready)

    def test_whole_run_budget_terminates_and_redacts_diagnostics(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_bounded_process(
                [sys.executable, "-c", "import time; print('started', flush=True); time.sleep(5)"],
                cwd=Path(temporary),
                environment=os.environ,
                timeout_seconds=1,
            )
        self.assertTrue(result.timed_out)
        self.assertEqual(result.returncode, 124)
        self.assertIn("started", result.stdout)
        self.assertEqual(
            redact_diagnostics("before mock-session-concept-secret after"),
            "before <redacted> after",
        )


class MockSessionContextRecordTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        files = {
            "AGENTS.md": b"constitution",
            ".agents/skills/autonomous-workshop/SKILL.md": b"workflow",
            ".agents/skills/autonomous-workshop/references/wish-match.md": b"match",
            "work/match-source.json": b"{}",
        }
        for relative, content in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.packet = {
            "stage": "match",
            "checkpoint_sha256": "a" * 64,
            "subject_sha256": "b" * 64,
            "inputs": {"wish": {"path": "WISH.json"}, "inventor_roster": []},
        }
        self.packet_path = self.root / ".mock-session/packets/packet.json"
        _write_json(self.packet_path, self.packet)
        self.record_path = self.root / ".mock-session/context/record.json"
        self.record = {
            "schema_version": 1,
            "kind": CONTEXT_KIND,
            "stage": "match",
            "checkpoint_sha256": "a" * 64,
            "subject_sha256": "b" * 64,
            "instructions": [
                {"path": relative, "sha256": hashlib.sha256(content).hexdigest()}
                for relative, content in files.items()
                if relative != "work/match-source.json"
            ],
            "used_inputs": ["wish", "inventor_roster"],
            "strategy": "minimal_match",
            "outputs": [
                {
                    "path": "work/match-source.json",
                    "sha256": hashlib.sha256(files["work/match-source.json"]).hexdigest(),
                }
            ],
            "deferred_work": ["broad candidate exploration"],
        }
        _write_json(self.record_path, self.record)

    def validate(self):
        return validate_context_record(
            self.record_path, run_root=self.root, packet_path=self.packet_path
        )

    def test_valid_record_binds_exact_context_and_outputs(self):
        self.assertEqual(self.validate()["strategy"], "minimal_match")

    def test_malformed_stale_missing_and_oversized_records_fail(self):
        cases = (
            ("stage", "invent", "stale stage"),
            ("checkpoint_sha256", "c" * 64, "stale checkpoint_sha256"),
            ("used_inputs", ["not-an-input"], "unrelated input"),
        )
        for field, value, message in cases:
            with self.subTest(field=field):
                changed = dict(self.record)
                changed[field] = value
                _write_json(self.record_path, changed)
                with self.assertRaisesRegex(MockSessionEvidenceError, message):
                    self.validate()
        _write_json(self.record_path, self.record)
        (self.root / "AGENTS.md").unlink()
        with self.assertRaisesRegex(MockSessionEvidenceError, "not a regular file"):
            self.validate()
        self.record_path.write_bytes(b" " * (MAX_CONTEXT_RECORD_BYTES + 1))
        with self.assertRaisesRegex(MockSessionEvidenceError, "size is invalid"):
            self.validate()

    def test_wrong_hash_and_host_owned_output_fail(self):
        changed = dict(self.record)
        changed["outputs"] = [{"path": "work/match-source.json", "sha256": "0" * 64}]
        _write_json(self.record_path, changed)
        with self.assertRaisesRegex(MockSessionEvidenceError, "sha256 is stale"):
            self.validate()

        sealed = self.root / "artifacts/concept/sealed-concept.json"
        sealed.parent.mkdir(parents=True)
        sealed.write_bytes(b"host")
        changed["outputs"] = [
            {"path": "artifacts/concept/sealed-concept.json", "sha256": hashlib.sha256(b"host").hexdigest()}
        ]
        _write_json(self.record_path, changed)
        with self.assertRaisesRegex(MockSessionEvidenceError, "host-owned boundary"):
            self.validate()

    def test_removed_skill_and_corrupted_reference_fail_without_overlay_fallback(self):
        skill = self.root / ".agents/skills/autonomous-workshop/SKILL.md"
        original_skill = skill.read_bytes()
        skill.unlink()
        with self.assertRaisesRegex(MockSessionEvidenceError, "not a regular file"):
            self.validate()
        skill.write_bytes(original_skill)
        reference = (
            self.root
            / ".agents/skills/autonomous-workshop/references/wish-match.md"
        )
        reference.write_bytes(b"regressed production reference")
        with self.assertRaisesRegex(MockSessionEvidenceError, "sha256 is stale"):
            self.validate()

    def test_stage_packet_hash_bound_inputs_must_exist_and_remain_exact(self):
        upstream = self.root / "artifacts/invent/invented.json"
        upstream.parent.mkdir(parents=True)
        upstream.write_bytes(b"accepted upstream")
        packet = dict(self.packet)
        packet["inputs"] = {
            "invented_artifact": {
                "path": "artifacts/invent/invented.json",
                "sha256": hashlib.sha256(b"accepted upstream").hexdigest(),
            }
        }
        _write_json(self.packet_path, packet)
        self.assertEqual(
            validate_stage_packet_inputs(self.packet_path, run_root=self.root),
            ("artifacts/invent/invented.json",),
        )
        upstream.write_bytes(b"corrupted upstream")
        with self.assertRaisesRegex(MockSessionEvidenceError, "bytes are stale"):
            validate_stage_packet_inputs(self.packet_path, run_root=self.root)
        upstream.unlink()
        with self.assertRaisesRegex(MockSessionEvidenceError, "unavailable"):
            validate_stage_packet_inputs(self.packet_path, run_root=self.root)

    def test_output_inventory_must_match_turn_writes_and_a_real_proposal(self):
        proposal = self.root / "artifacts/match/assignment.json"
        proposal.parent.mkdir(parents=True)
        proposal.write_bytes(b"proposal")
        output_hash = self.record["outputs"][0]["sha256"]
        validate_context_record(
            self.record_path,
            run_root=self.root,
            packet_path=self.packet_path,
            agent_writes=["work/match-source.json"],
            proposal_artifacts=["artifacts/match/assignment.json"],
            context_output_hashes={"work/match-source.json": output_hash},
        )
        with self.assertRaisesRegex(MockSessionEvidenceError, "differs from this turn"):
            validate_context_record(
                self.record_path,
                run_root=self.root,
                packet_path=self.packet_path,
                agent_writes=["work/another.json"],
                proposal_artifacts=["artifacts/match/assignment.json"],
                context_output_hashes={"work/match-source.json": output_hash},
            )
        with self.assertRaisesRegex(MockSessionEvidenceError, "proposal artifacts"):
            validate_context_record(
                self.record_path,
                run_root=self.root,
                packet_path=self.packet_path,
                agent_writes=["work/match-source.json"],
                proposal_artifacts=[],
                context_output_hashes={"work/match-source.json": output_hash},
            )


class MockSessionProtocolTest(unittest.TestCase):
    def test_loopback_server_is_reached_through_production_protocol_shapes(self):
        with MockSessionProtocolServer() as server:
            session = FactoryAgentSession(
                FactoryAgentCredentials("alice", "secret"),
                transport=server.factory_transport,
            )
            response = session.authenticated_transport(
                "GET", DEFAULT_FACTORY_API + "/designs/mock", {}, None, 10
            )
            self.assertEqual(response.status, 200)
            self.assertTrue(any(path.endswith("/auth/agent/login") for _, path in server.state.calls))
            self.assertTrue(any("/designs/" in path for _, path in server.state.calls))


class MockSessionArchitectureTest(unittest.TestCase):
    def test_generic_directive_does_not_duplicate_stage_protocols(self):
        lowered = DIRECTIVE.casefold()
        self.assertIn("does not permit placeholder", lowered)
        self.assertIn("every unchanged production gate", lowered)
        for forbidden in (
            "--source",
            "--concept-root",
            "--product-root",
            "--package-root",
            "proposed_transition",
            "sealed-concept.json",
            "match -> invent",
            "playtest -> release",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_normal_cli_and_product_template_cannot_enable_mock_session_mode(self):
        repository = Path(__file__).resolve().parents[2]
        for root in (repository / "src/cli", repository / ".agents/product-run"):
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix not in (".py", ".md", ".toml", ""):
                    continue
                content = path.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn("WORKSHOP_RUN_MOCK_SESSION_E2E", content, path)
                self.assertNotIn("mock_session_harness", content, path)

    def test_transport_bundle_accepts_only_external_protocol_callables(self):
        opener = lambda *unused, **unused_named: None
        transport = lambda *unused, **unused_named: None
        value = NativeRunExternalTransports(
            concept_image_opener=opener, factory_transport=transport
        )
        self.assertIs(value.concept_image_opener, opener)
        self.assertIs(value.factory_transport, transport)
        with self.assertRaisesRegex(ContractError, "must be callable"):
            NativeRunExternalTransports(factory_transport="not-callable")

    def test_fixture_secret_audit_rejects_any_workspace_leak(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "safe.txt").write_text("safe")
            _assert_no_secrets(root)
            (root / "leak.txt").write_text("mock-session-factory-secret")
            with self.assertRaisesRegex(MockSessionEvidenceError, "secret leaked"):
                _assert_no_secrets(root)

    def test_concept_instruction_preserves_the_pre_render_boundary(self):
        repository = Path(__file__).resolve().parents[2]
        path = (
            repository
            / ".agents/product-run/.agents/skills/autonomous-workshop/references/concept.md"
        )
        source = path.read_text(encoding="utf-8")
        validate_concept_boundary_instruction(source)
        normalized = " ".join(source.split())
        self.assertIn(
            "copy `product_id`, `objective`, and `context` exactly from `WISH.json`",
            normalized,
        )
        self.assertIn("never into `context`", normalized)
        regressed = " ".join(source.split()).replace(
            "Missing rendered images before finalization is the expected state",
            "Rendered images are required before finalization",
        )
        with self.assertRaisesRegex(MockSessionEvidenceError, "lost the pre-render boundary"):
            validate_concept_boundary_instruction(regressed)


class MockCodexPassThroughTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.wrapper = Path(__file__).with_name("mock_codex_passthrough.py")
        _write_json(
            self.root / "STAGE.json",
            {
                "stage": "match",
                "checkpoint_sha256": "a" * 64,
                "subject_sha256": "b" * 64,
                "inputs": {"wish": {}},
            },
        )

    def fake_codex(self, body):
        path = self.bin / "codex"
        path.write_text("#!%s\n%s\n" % (sys.executable, body), encoding="utf-8")
        path.chmod(0o755)
        return path

    def environment(self):
        values = dict(os.environ)
        values["PATH"] = str(self.bin) + os.pathsep + values.get("PATH", "")
        return values

    def test_version_arguments_prompt_events_exit_and_trace_are_forwarded(self):
        self.fake_codex(
            """import json, pathlib, sys
if sys.argv[1:] == ['--version']:
    print('codex-cli 0.145.0')
    raise SystemExit(0)
prompt = sys.stdin.read()
pathlib.Path('capture.json').write_text(json.dumps({'arguments': sys.argv[1:], 'prompt': prompt}))
pathlib.Path('source.json').write_text('{}')
record = {
    'stage': 'match',
    'checkpoint_sha256': 'a' * 64,
    'subject_sha256': 'b' * 64,
    'instructions': [{'path': 'AGENTS.md', 'sha256': '0' * 64}],
    'used_inputs': ['wish'],
    'outputs': [{'path': 'source.json', 'sha256': __import__('hashlib').sha256(b'{}').hexdigest()}],
    'deferred_work': ['optional depth'],
}
context = pathlib.Path('.mock-session/context')
context.mkdir(parents=True, exist_ok=True)
(context / (('a' * 64) + '.json')).write_text(json.dumps(record))
events = [
    {'type': 'thread.started', 'thread_id': '00000000-0000-4000-8000-000000000001'},
    {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'done'}},
    {'type': 'turn.completed'},
]
for event in events:
    print(json.dumps(event), flush=True)
"""
        )
        version = subprocess.run(
            [str(self.wrapper), "--version"],
            cwd=self.root,
            env=self.environment(),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(version.returncode, 0)
        self.assertEqual(version.stdout.strip(), "codex-cli 0.145.0")
        arguments = ["exec", "--model", "gpt-5.6-sol", '--config', 'model_reasoning_effort="high"', "-"]
        result = subprocess.run(
            [str(self.wrapper), *arguments],
            cwd=self.root,
            env=self.environment(),
            input="production prompt",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        capture = json.loads((self.root / "capture.json").read_text())
        self.assertEqual(capture["arguments"], arguments)
        self.assertTrue(capture["prompt"].startswith("production prompt"))
        self.assertIn("workshop_mock_session_acceptance", capture["prompt"])
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(events[-1]["type"], "turn.completed")
        trace = json.loads((self.root / ".mock-session/turns.jsonl").read_text())
        self.assertEqual(trace["model"], "gpt-5.6-sol")
        self.assertEqual(trace["reasoning_effort"], "high")
        self.assertEqual(trace["prohibited_items"], [])
        self.assertTrue((self.root / ".mock-session/packets" / (("a" * 64) + ".json")).is_file())

        (self.root / ".mock-session/context" / (("a" * 64) + ".json")).unlink()
        self.fake_codex(
            "import json, sys; sys.stdin.read(); "
            "print(json.dumps({'type':'turn.completed'}), flush=True)"
        )
        missing_proof = subprocess.run(
            [str(self.wrapper), *arguments],
            cwd=self.root,
            env=self.environment(),
            input="production prompt",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(missing_proof.returncode, 126)
        self.assertNotIn("turn.completed", missing_proof.stdout)
        self.assertIn("context proof failed", missing_proof.stderr)

        self.fake_codex("import sys; sys.stdin.read(); raise SystemExit(7)")
        failed = subprocess.run(
            [str(self.wrapper), *arguments],
            cwd=self.root,
            env=self.environment(),
            input="production prompt",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(failed.returncode, 7)

    def test_term_signal_is_forwarded_to_the_real_codex_child(self):
        self.fake_codex(
            """import pathlib, signal, sys, time
def stop(unused_number, unused_frame):
    pathlib.Path('signal-forwarded').write_text('yes')
    raise SystemExit(143)
signal.signal(signal.SIGTERM, stop)
pathlib.Path('child-started').write_text('yes')
sys.stdin.read()
while True:
    time.sleep(0.05)
"""
        )
        process = subprocess.Popen(
            [str(self.wrapper), "exec", "--model", "gpt-5.6-sol", '--config', 'model_reasoning_effort="high"', "-"],
            cwd=self.root,
            env=self.environment(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert process.stdin is not None
        process.stdin.write("prompt")
        process.stdin.close()
        for _ in range(100):
            if (self.root / "child-started").exists():
                break
            time.sleep(0.01)
        self.assertTrue((self.root / "child-started").exists())
        process.terminate()
        process.wait(timeout=5)
        self.assertTrue((self.root / "signal-forwarded").is_file())
        assert process.stdout is not None and process.stderr is not None
        process.stdout.close()
        process.stderr.close()

    def test_prohibited_web_and_child_agent_events_are_observed(self):
        source = self.root / "source.json"
        source.write_bytes(b"{}")
        _write_json(
            self.root / ".mock-session/context" / (("a" * 64) + ".json"),
            {
                "stage": "match",
                "checkpoint_sha256": "a" * 64,
                "subject_sha256": "b" * 64,
                "instructions": [{"path": "AGENTS.md", "sha256": "0" * 64}],
                "used_inputs": ["wish"],
                "outputs": [
                    {
                        "path": "source.json",
                        "sha256": hashlib.sha256(b"{}").hexdigest(),
                    }
                ],
                "deferred_work": ["optional depth"],
            },
        )
        self.fake_codex(
            """import json, sys
sys.stdin.read()
for item_type in ('web_search', 'collaboration_tool_call'):
    print(json.dumps({'type': 'item.completed', 'item': {'type': item_type}}), flush=True)
print(json.dumps({'type': 'turn.completed'}), flush=True)
"""
        )
        result = subprocess.run(
            [str(self.wrapper), "exec", "--model", "gpt-5.6-sol", '--config', 'model_reasoning_effort="high"', "-"],
            cwd=self.root,
            env=self.environment(),
            input="prompt",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        trace = json.loads((self.root / ".mock-session/turns.jsonl").read_text())
        self.assertEqual(
            trace["prohibited_items"],
            ["collaboration_tool_call", "web_search"],
        )


if __name__ == "__main__":
    unittest.main()
