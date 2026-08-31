import hashlib
import json
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from cli.main import main, parser
from workshop.errors import ContractError, StateConflict, WorkshopError
from workshop.match.native import (
    InventorRoster,
    MatchRankingEntry,
    NativeMatchAssignment,
)
from workshop.product import ToyBlueprint
from workshop.workflow.native_run import (
    _MAX_CONSECUTIVE_RECOVERABLE_NATIVE_TURNS,
    _MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS,
    _RECOVERABLE_BACKOFF_MAX_SECONDS,
    _current_make_proposal_rejection,
    _deep_make_critical_path_prompt,
    _deep_make_recovery_prompt,
    _deep_invent_recovery_prompt,
    _make_proof_ready,
    _make_proof_ready_path,
    _materialized_release_contract,
    NativeRunPaths,
    _NativeProgressTracker,
    _native_token_summary,
    _native_launcher,
    _native_turn_limit,
    _record_native_token_usage,
    _native_run_mutation_lock,
    _prune_empty_make_product_directories,
    _recoverable_native_turn_backoff_seconds,
    canonical_wish_bytes,
    native_run_exists,
    native_run_paths,
    native_run_status,
    resume_native_run,
    start_native_run,
)
from workshop.runtime import (
    CodexFinalizedWithoutTerminalError,
    CodexInvocationError,
    CodexRecoverableInvocationError,
)
from workshop.runtime.progress import NativeRunProgress
from workshop.wish import Wish
from workshop.workflow.agent_run import (
    AgentArtifact,
    AgentOutcome,
    AgentRun,
    AgentRunCheckpoint,
)
from workshop.workflow.proposals import AgentOutcomeProposal
from workshop.workflow.effort import (
    DEEP_AUTO_COMPACT_TOKEN_LIMIT,
    DEEP_ECONOMICS_CAPABILITY_PATH,
    DEEP_ECONOMICS_V1_CAPABILITY_PATH,
    DEEP_ECONOMICS_V2_CAPABILITY_PATH,
    DEEP_ECONOMICS_V3_CAPABILITY_PATH,
    DEEP_ECONOMICS_V4_CAPABILITY_PATH,
    DEEP_ECONOMICS_V5_CAPABILITY_PATH,
    DEEP_ECONOMICS_V6_CAPABILITY_PATH,
    DEEP_ECONOMICS_V7_CAPABILITY_PATH,
    DEEP_ECONOMICS_V8_CAPABILITY_PATH,
    DEEP_ECONOMICS_V9_CAPABILITY_PATH,
    DEEP_ECONOMICS_V10_CAPABILITY_PATH,
    DEEP_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS,
    DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT,
    DEEP_MAKE_AUTO_COMPACT_TOKEN_LIMIT,
    DEEP_NATIVE_TURN_LIMIT,
    DEEP_NATIVE_TURN_TIMEOUT_SECONDS,
    DEEP_V1_AUTO_COMPACT_TOKEN_LIMIT,
    DEEP_V1_NATIVE_TURN_LIMIT,
    DEEP_V5_INITIAL_INVENT_TIMEOUT_SECONDS,
    DEEP_V5_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS,
    DEEP_V5_INVENT_RECOVERY_TIMEOUT_SECONDS,
    DEEP_V8_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS,
    DEEP_V10_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS,
    DEEP_V11_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS,
    SPARK_AUTO_COMPACT_TOKEN_LIMIT,
    SPARK_ECONOMICS_CAPABILITY_PATH,
    SPARK_ECONOMICS_V1_CAPABILITY_PATH,
    SPARK_ECONOMICS_V2_CAPABILITY_PATH,
    SPARK_NATIVE_TURN_TIMEOUT_SECONDS,
)


class NativeTokenTelemetryCompatibilityTest(unittest.TestCase):
    def test_legacy_combined_counter_is_not_guessed_when_split_usage_arrives(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace = root / "workspace"
            host_state = root / "host"
            workspace.mkdir()
            host_state.mkdir()
            checkpoint = AgentRunCheckpoint(
                product_id="legacy-token-run",
                stage="make",
                status="active",
                revision=0,
                round_index=1,
                max_rounds=4,
                wish_sha256="a" * 64,
                run_root_sha256="b" * 64,
                host_state_root_sha256="c" * 64,
                checkpoint_sha256="d" * 64,
                input_sha256s={},
                inventor_roster=(),
                stage_artifacts={},
                invalidated_stages=(),
                effort="spark",
            )
            path = host_state / "native-token-usage.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "autonomous-workshop.native-token-usage",
                        "product_id": checkpoint.product_id,
                        "wish_sha256": checkpoint.wish_sha256,
                        "stages": {
                            "make": {
                                "turns": 2,
                                "measured_turns": 2,
                                "tokens": 999,
                            }
                        },
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            os.chmod(path, 0o600)
            paths = NativeRunPaths(workspace=workspace, host_state=host_state)

            legacy = _native_token_summary(paths, checkpoint)
            self.assertEqual(legacy["status"], "unavailable")
            self.assertEqual(legacy["turns"], {"total": 2, "measured": 0, "unmeasured": 2})
            self.assertEqual(legacy["input_tokens"], 0)
            self.assertEqual(legacy["output_tokens"], 0)

            _record_native_token_usage(paths, checkpoint, (100, 25))
            migrated = _native_token_summary(paths, checkpoint)
            self.assertEqual(migrated["schema_version"], 3)
            self.assertEqual(migrated["status"], "partial")
            self.assertEqual(migrated["turns"], {"total": 3, "measured": 1, "unmeasured": 2})
            self.assertEqual(migrated["input_tokens"], 100)
            self.assertEqual(migrated["output_tokens"], 25)
            self.assertEqual(migrated["economics"]["status"], "unavailable")
            self.assertEqual(
                migrated["economics"]["turns"],
                {"total": 3, "measured": 0, "unmeasured": 3},
            )
            self.assertNotIn("total_tokens", migrated)

            _record_native_token_usage(
                paths,
                checkpoint,
                {
                    "input_tokens": 80,
                    "cached_input_tokens": 60,
                    "cache_write_input_tokens": 5,
                    "output_tokens": 20,
                    "reasoning_output_tokens": 12,
                },
            )
            detailed = _native_token_summary(paths, checkpoint)
            self.assertEqual(detailed["input_tokens"], 180)
            self.assertEqual(detailed["output_tokens"], 45)
            self.assertEqual(detailed["economics"]["status"], "partial")
            self.assertEqual(detailed["economics"]["input_tokens"], 80)
            self.assertEqual(detailed["economics"]["cached_input_tokens"], 60)
            self.assertEqual(detailed["economics"]["uncached_input_tokens"], 20)
            self.assertEqual(detailed["economics"]["cache_write_input_tokens"], 5)
            self.assertEqual(detailed["economics"]["output_tokens"], 20)
            self.assertEqual(detailed["economics"]["reasoning_output_tokens"], 12)
            self.assertEqual(detailed["economics"]["non_reasoning_output_tokens"], 8)


class _FakeOutcome:
    def __init__(self, arguments):
        self.arguments = dict(arguments)

    def to_dict(self):
        return {
            "status": "completed",
            "session": {
                "product_id": self.arguments["product_id"],
                "wish_sha256": self.arguments["wish_sha256"],
                "constitution_sha256": self.arguments["constitution_sha256"],
                "checkpoint_sha256": "c" * 64,
            },
            "used_web_search": False,
        }


class _FakeLauncher:
    def __init__(self, *, fail_first_start=False):
        self.starts = []
        self.resumes = []
        self.fail_first_start = fail_first_start

    @staticmethod
    def _checkpoint(arguments):
        checkpoint = Path(arguments["host_state_root"]) / "codex-session.json"
        checkpoint.write_text("{}\n", encoding="utf-8")
        os.chmod(checkpoint, 0o600)

    @staticmethod
    def _write_waiting(arguments):
        stage = json.loads(
            (Path(arguments["run_root"]) / "STAGE.json").read_text(
                encoding="utf-8"
            )
        )
        proposal = {
            "schema_version": 1,
            "kind": "autonomous-workshop.agent-outcome-proposal",
            "checkpoint_sha256": stage["checkpoint_sha256"],
            "subject_sha256": stage["subject_sha256"],
            "outcome": {
                "schema_version": 1,
                "stage": stage["stage"],
                "status": "waiting",
                "artifacts": [],
                "needs": ["fixture stops after one native turn"],
                "proposed_transition": None,
            },
        }
        (Path(arguments["run_root"]) / "agent-outcome.json").write_text(
            json.dumps(proposal, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        if self.fail_first_start:
            self.fail_first_start = False
            raise CodexInvocationError("fixture interruption before thread.started")
        self._checkpoint(arguments)
        self._write_waiting(arguments)
        return _FakeOutcome(arguments)

    def resume(self, **arguments):
        self.resumes.append(dict(arguments))
        self._write_waiting(arguments)
        return _FakeOutcome(arguments)


class _ReportingFakeLauncher(_FakeLauncher):
    @staticmethod
    def _report(arguments, activities):
        observer = arguments["activity_observer"]
        for activity in activities:
            observer(activity)

    def start(self, **arguments):
        self._report(arguments, ("starting", "reasoning", "event-owned content"))
        return super().start(**arguments)

    def resume(self, **arguments):
        self._report(arguments, ("tool", "running", "event-owned content"))
        return super().resume(**arguments)


class _FinalizedMatchThenFailLauncher(_FakeLauncher):
    """Simulate a launcher failure after the exact Match finalizer boundary."""

    def __init__(self, *, stale_proposal=False, invalid_proposal=False):
        super().__init__()
        if stale_proposal and invalid_proposal:
            raise ValueError("fixture proposal mode is ambiguous")
        self.stale_proposal = stale_proposal
        self.invalid_proposal = invalid_proposal

    @staticmethod
    def _canonical_json(value):
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

    def _write_ready_match(self, arguments):
        run_root = Path(arguments["run_root"])
        stage = json.loads((run_root / "STAGE.json").read_text(encoding="utf-8"))
        roster = InventorRoster.from_mapping(stage["inputs"]["inventor_roster"])
        selected = roster.inventors[0]
        assignment = NativeMatchAssignment(
            wish_sha256=arguments["wish_sha256"],
            inventor_roster_sha256=roster.roster_sha256,
            selected_inventor_id=selected.inventor_id,
            selected_agent_path=selected.agent_path,
            selected_agent_sha256=selected.agent_sha256,
            selected_source_manifest_sha256=selected.source_manifest_sha256,
            selected_taste_sha256=selected.taste_sha256,
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=tuple(
                MatchRankingEntry(
                    inventor_id=entry.inventor_id,
                    rationale="Stable fixture ranking for the exact materialized roster.",
                )
                for entry in roster.inventors
            ),
        )
        relative = "artifacts/match/assignment.json"
        content = self._canonical_json(assignment.to_dict())
        target = run_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        artifact = AgentArtifact(
            path=relative,
            sha256=hashlib.sha256(content).hexdigest(),
        )
        outcome = AgentOutcome(
            stage="match",
            status="ready",
            artifacts=(artifact,),
            proposed_transition="invent",
        )
        proposal = AgentOutcomeProposal(
            checkpoint_sha256=(
                "0" * 64
                if self.stale_proposal
                else stage["checkpoint_sha256"]
            ),
            subject_sha256=stage["subject_sha256"],
            outcome=outcome,
        )
        outcome_path = run_root / "agent-outcome.json"
        if self.invalid_proposal:
            outcome_path.write_bytes(b"{")
        else:
            outcome_path.write_bytes(
                self._canonical_json(proposal.to_dict()) + b"\n"
            )

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        self._checkpoint(arguments)
        self._write_ready_match(arguments)
        raise CodexFinalizedWithoutTerminalError(
            "fixture finalized without a terminal event"
        )


class _FinalizedMatchThenInterruptLauncher(_FinalizedMatchThenFailLauncher):
    """Simulate host interruption after finalization and process cleanup."""

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        self._checkpoint(arguments)
        self._write_ready_match(arguments)
        raise KeyboardInterrupt()


class _RecoverableMatchContinuationLauncher(_FinalizedMatchThenFailLauncher):
    """Interrupt Match once, then finalize it through the same checkpoint."""

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        self._checkpoint(arguments)
        raise CodexRecoverableInvocationError("fixture native turn timed out")

    def resume(self, **arguments):
        self.resumes.append(dict(arguments))
        stage = json.loads(
            (Path(arguments["run_root"]) / "STAGE.json").read_text(
                encoding="utf-8"
            )
        )
        if stage["stage"] == "match":
            self._write_ready_match(arguments)
        else:
            self._write_waiting(arguments)
        return _FakeOutcome(arguments)


class _AlwaysInterruptedLauncher(_FakeLauncher):
    def __init__(self, *, recoverable=True):
        super().__init__()
        self.recoverable = recoverable

    def _raise(self):
        error = (
            CodexRecoverableInvocationError
            if self.recoverable
            else CodexInvocationError
        )
        raise error("fixture native turn interruption")

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        self._checkpoint(arguments)
        self._raise()

    def resume(self, **arguments):
        self.resumes.append(dict(arguments))
        self._raise()


class _AlwaysUnfinishedLauncher(_FakeLauncher):
    """Return normally without proposing while preserving one session."""

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        self._checkpoint(arguments)
        return _FakeOutcome(arguments)

    def resume(self, **arguments):
        self.resumes.append(dict(arguments))
        return _FakeOutcome(arguments)


class _UnboundRecoverableLauncher(_FakeLauncher):
    def start(self, **arguments):
        self.starts.append(dict(arguments))
        raise CodexRecoverableInvocationError(
            "fixture interruption before exact thread binding"
        )


class NativeHostTest(unittest.TestCase):
    @staticmethod
    def _launcher_checkpoint(*, effort, economics_capability, stage="make"):
        capability_paths = {
            "deep-v1": DEEP_ECONOMICS_V1_CAPABILITY_PATH,
            "deep-v2": DEEP_ECONOMICS_V2_CAPABILITY_PATH,
            "deep-v3": DEEP_ECONOMICS_V3_CAPABILITY_PATH,
            "deep-v4": DEEP_ECONOMICS_V4_CAPABILITY_PATH,
            "deep-v5": DEEP_ECONOMICS_V5_CAPABILITY_PATH,
            "deep-v6": DEEP_ECONOMICS_V6_CAPABILITY_PATH,
            "deep-v7": DEEP_ECONOMICS_V7_CAPABILITY_PATH,
            "deep-v8": DEEP_ECONOMICS_V8_CAPABILITY_PATH,
            "deep-v9": DEEP_ECONOMICS_V9_CAPABILITY_PATH,
            "deep-v10": DEEP_ECONOMICS_V10_CAPABILITY_PATH,
            "deep-v11": DEEP_ECONOMICS_CAPABILITY_PATH,
            "v1": SPARK_ECONOMICS_V1_CAPABILITY_PATH,
            "v2": SPARK_ECONOMICS_V2_CAPABILITY_PATH,
            "v3": SPARK_ECONOMICS_CAPABILITY_PATH,
        }
        if economics_capability == "deep-v11":
            # A real v11 run materializes the preserved v5-v10 references too. The
            # host must select the newest frozen profile, not branch merely on
            # an older file's presence.
            inputs = {
                DEEP_ECONOMICS_V5_CAPABILITY_PATH: "e" * 64,
                DEEP_ECONOMICS_V6_CAPABILITY_PATH: "d" * 64,
                DEEP_ECONOMICS_V7_CAPABILITY_PATH: "c" * 64,
                DEEP_ECONOMICS_V8_CAPABILITY_PATH: "b" * 64,
                DEEP_ECONOMICS_V9_CAPABILITY_PATH: "9" * 64,
                DEEP_ECONOMICS_V10_CAPABILITY_PATH: "0" * 64,
                DEEP_ECONOMICS_CAPABILITY_PATH: "a" * 64,
            }
        elif economics_capability == "deep-v10":
            inputs = {
                DEEP_ECONOMICS_V5_CAPABILITY_PATH: "e" * 64,
                DEEP_ECONOMICS_V6_CAPABILITY_PATH: "d" * 64,
                DEEP_ECONOMICS_V7_CAPABILITY_PATH: "c" * 64,
                DEEP_ECONOMICS_V8_CAPABILITY_PATH: "b" * 64,
                DEEP_ECONOMICS_V9_CAPABILITY_PATH: "9" * 64,
                DEEP_ECONOMICS_V10_CAPABILITY_PATH: "a" * 64,
            }
        elif economics_capability == "deep-v9":
            inputs = {
                DEEP_ECONOMICS_V5_CAPABILITY_PATH: "e" * 64,
                DEEP_ECONOMICS_V6_CAPABILITY_PATH: "d" * 64,
                DEEP_ECONOMICS_V7_CAPABILITY_PATH: "c" * 64,
                DEEP_ECONOMICS_V8_CAPABILITY_PATH: "b" * 64,
                DEEP_ECONOMICS_V9_CAPABILITY_PATH: "a" * 64,
            }
        elif economics_capability == "deep-v8":
            inputs = {
                DEEP_ECONOMICS_V5_CAPABILITY_PATH: "d" * 64,
                DEEP_ECONOMICS_V6_CAPABILITY_PATH: "c" * 64,
                DEEP_ECONOMICS_V7_CAPABILITY_PATH: "b" * 64,
                DEEP_ECONOMICS_V8_CAPABILITY_PATH: "a" * 64,
            }
        else:
            inputs = (
                {capability_paths[economics_capability]: "a" * 64}
                if economics_capability is not None
                else {}
            )
        return AgentRunCheckpoint(
            product_id="launcher-economics-fixture",
            stage=stage,
            status="active",
            revision=1,
            round_index=1,
            max_rounds=4,
            wish_sha256="b" * 64,
            run_root_sha256="c" * 64,
            host_state_root_sha256="d" * 64,
            checkpoint_sha256="e" * 64,
            input_sha256s=inputs,
            inventor_roster=(),
            stage_artifacts={},
            invalidated_stages=(),
            effort=effort,
            manager_id="codex",
        )

    def test_grid_keepalive_service_cannot_create_repeating_wishes(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            with mock.patch.dict(
                os.environ,
                {
                    "WORKSHOP_HOME": str(home),
                    "XPC_SERVICE_NAME": "grid.serve.accidental-wish-daemon",
                },
                clear=True,
            ), self.assertRaisesRegex(
                StateConflict,
                "finite jobs.*bounded one-shot runner",
            ):
                start_native_run(
                    Wish.create(
                        "wish-must-not-materialize",
                        "a moon toy that must start only once",
                    ),
                    effort="spark",
                )

            self.assertFalse(home.exists())

    def test_v3_spark_adds_low_reasoning_compaction_and_turn_boundary(self):
        checkpoint = self._launcher_checkpoint(
            effort="spark", economics_capability="v3"
        )
        with mock.patch(
            "workshop.workflow.native_run.CodexNativeSessionLauncher"
        ) as launcher_type:
            launcher = _native_launcher(checkpoint)

        self.assertIs(launcher, launcher_type.return_value)
        launcher_type.assert_called_once_with(
            reasoning_effort="low",
            auto_compact_token_limit=SPARK_AUTO_COMPACT_TOKEN_LIMIT,
            timeout_seconds=SPARK_NATIVE_TURN_TIMEOUT_SECONDS,
        )

    def test_v2_spark_retains_compaction_without_shorter_turn_boundary(self):
        checkpoint = self._launcher_checkpoint(
            effort="spark", economics_capability="v2"
        )
        with mock.patch(
            "workshop.workflow.native_run.CodexNativeSessionLauncher"
        ) as launcher_type:
            _native_launcher(checkpoint)

        launcher_type.assert_called_once_with(
            reasoning_effort="low",
            auto_compact_token_limit=SPARK_AUTO_COMPACT_TOKEN_LIMIT,
        )

    def test_v1_spark_retains_low_reasoning_without_compaction(self):
        checkpoint = self._launcher_checkpoint(
            effort="spark", economics_capability="v1"
        )
        with mock.patch(
            "workshop.workflow.native_run.CodexNativeSessionLauncher"
        ) as launcher_type:
            _native_launcher(checkpoint)

        launcher_type.assert_called_once_with(reasoning_effort="low")

    def test_deep_v9_shapes_each_stage_under_one_frozen_runtime_profile(self):
        for effort in ("forge", "quest"):
            for stage, reasoning in (
                ("invent", "high"),
                ("make", "medium"),
                ("playtest", "medium"),
                ("release", "medium"),
            ):
                with self.subTest(effort=effort, stage=stage), mock.patch(
                    "workshop.workflow.native_run.CodexNativeSessionLauncher"
                ) as launcher_type:
                    checkpoint = self._launcher_checkpoint(
                        effort=effort,
                        economics_capability="deep-v9",
                        stage=stage,
                    )
                    _native_launcher(
                        checkpoint,
                        initial_make_proof_boundary=(stage == "make"),
                    )

                    launcher_type.assert_called_once_with(
                        reasoning_effort=reasoning,
                        auto_compact_token_limit=DEEP_AUTO_COMPACT_TOKEN_LIMIT,
                        runtime_profile_sha256="a" * 64,
                        timeout_seconds=(
                            DEEP_V8_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS
                            if stage == "make"
                            else (
                                DEEP_V5_INITIAL_INVENT_TIMEOUT_SECONDS
                                if stage == "invent"
                                else DEEP_NATIVE_TURN_TIMEOUT_SECONDS
                            )
                        ),
                    )
                    self.assertEqual(
                        _native_turn_limit(checkpoint), DEEP_NATIVE_TURN_LIMIT
                    )

    def test_deep_v10_final_make_uses_source_handoff_then_normal_recovery(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v10", stage="make"
        )
        for recoverable, timeout in (
            (False, DEEP_V10_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS),
            (True, DEEP_NATIVE_TURN_TIMEOUT_SECONDS),
        ):
            with self.subTest(recoverable=recoverable), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher"
            ) as launcher_type:
                _native_launcher(
                    checkpoint,
                    initial_make_proof_boundary=False,
                    recoverable_continuation=recoverable,
                )
                launcher_type.assert_called_once_with(
                    reasoning_effort="high",
                    auto_compact_token_limit=DEEP_AUTO_COMPACT_TOKEN_LIMIT,
                    runtime_profile_sha256="a" * 64,
                    timeout_seconds=timeout,
                )

    def test_deep_v11_final_make_keeps_v10_source_handoff(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v11", stage="make"
        )
        with mock.patch(
            "workshop.workflow.native_run.CodexNativeSessionLauncher"
        ) as launcher_type:
            _native_launcher(checkpoint, initial_make_proof_boundary=False)

        launcher_type.assert_called_once_with(
            reasoning_effort="high",
            auto_compact_token_limit=DEEP_AUTO_COMPACT_TOKEN_LIMIT,
            runtime_profile_sha256="a" * 64,
            timeout_seconds=DEEP_V11_INITIAL_FINAL_MAKE_TIMEOUT_SECONDS,
        )

    def test_deep_v5_retains_its_frozen_phased_profile_and_prompt(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v5", stage="make"
        )
        with mock.patch(
            "workshop.workflow.native_run.CodexNativeSessionLauncher"
        ) as launcher_type:
            _native_launcher(
                checkpoint,
                initial_make_proof_boundary=True,
            )

        launcher_type.assert_called_once_with(
            reasoning_effort="medium",
            auto_compact_token_limit=DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT,
            runtime_profile_sha256="a" * 64,
            timeout_seconds=DEEP_V5_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS,
        )
        prompt = _deep_make_critical_path_prompt(checkpoint)
        self.assertIn("This v5 proof turn", prompt)
        self.assertIn(
            ".agents/skills/cad/scripts/gen <source.step.py> --write",
            prompt,
        )
        self.assertNotIn("$WORKSHOP_PYTHON", prompt)
        self.assertNotIn("module-scope def gen_step()", prompt)

    def test_deep_v6_make_prompt_requires_executable_action_first_proof(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v6"
        )
        prompt = _deep_make_critical_path_prompt(checkpoint)

        self.assertIn("first Make deliverable", prompt)
        self.assertIn("review/early-proof/", prompt)
        self.assertIn("before authoring the complete part tree", prompt)
        self.assertIn("independent native visual critic", prompt)
        self.assertIn("exposed-mechanism", prompt)
        self.assertIn("action-only", prompt)
        self.assertIn(".make-proof-ready.json", prompt)
        self.assertIn("do not enumerate", prompt)
        self.assertIn(checkpoint.checkpoint_sha256, prompt)
        self.assertNotIn("This v5 proof turn", prompt)
        self.assertIn('"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/gen', prompt)
        self.assertIn("exactly one module-scope def gen_step()", prompt)
        self.assertIn(
            '{"checkpoint_sha256":"%s","kind":"autonomous-workshop.make-proof-ready","schema_version":1}'
            % checkpoint.checkpoint_sha256,
            prompt,
        )
        final_prompt = _deep_make_critical_path_prompt(
            checkpoint,
            proof_boundary=False,
        )
        self.assertIn("proof marker is already valid", final_prompt)
        self.assertIn("Only agent-outcome.json completes", final_prompt)
        self.assertNotIn("action-only", final_prompt)
        legacy_prompt = _deep_make_critical_path_prompt(
            self._launcher_checkpoint(
                effort="quest",
                economics_capability="deep-v3",
            )
        )
        self.assertIn("first Make deliverable", legacy_prompt)
        self.assertNotIn("independent native visual critic", legacy_prompt)
        self.assertEqual(
            _deep_make_critical_path_prompt(
                self._launcher_checkpoint(
                    effort="quest",
                    economics_capability="deep-v6",
                    stage="invent",
                )
            ),
            "",
        )

    def test_deep_v7_make_prompt_batches_cached_proof_and_prestarts_critic(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v7"
        )
        prompt = _deep_make_critical_path_prompt(checkpoint)

        self.assertIn("This v7 proof turn", prompt)
        self.assertIn("separate bounded reads", prompt)
        self.assertIn("broad CAD skill is deliberately not applicable", prompt)
        self.assertIn("spawn one blind critic", prompt)
        self.assertIn("wait for the exact held/signature paths", prompt)
        self.assertIn("together in one foreground tool call", prompt)
        self.assertIn("host already binds XDG_CACHE_HOME", prompt)
        self.assertIn('"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/gen', prompt)
        self.assertIn("do not spend a second child turn", prompt)
        self.assertIn(checkpoint.checkpoint_sha256, prompt)
        self.assertNotIn("This v6 proof turn", prompt)

        recovery = _deep_make_recovery_prompt(checkpoint)
        self.assertIn("v7 recovery stays on the proof fast path", recovery)
        self.assertIn("run the supplied generate", recovery)
        self.assertIn("together in one foreground tool call", recovery)

    def test_deep_v8_make_prompt_reserves_one_runway_for_product_bytes(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v8"
        )
        prompt = _deep_make_critical_path_prompt(checkpoint)

        self.assertIn("This v8 proof turn has one 16-minute medium runway", prompt)
        self.assertIn("do not call get_goal", prompt)
        self.assertIn("one bounded batch", prompt)
        self.assertIn("inspect an empty product tree", prompt)
        self.assertIn("spawn an early critic", prompt)
        self.assertIn("very next file edit", prompt)
        self.assertIn("together in one foreground tool call", prompt)
        self.assertIn("early direction check", prompt)
        self.assertIn("final independent critic", prompt)
        self.assertNotIn("ask one independent native visual critic", prompt)
        self.assertNotIn("This v7 proof turn", prompt)

        recovery = _deep_make_recovery_prompt(checkpoint)
        self.assertIn("v8 recovery stays on one proof runway", recovery)
        self.assertIn("Do not call get_goal", recovery)
        self.assertIn("next action an authored proof source", recovery)

    def test_deep_v8_retains_24k_compaction(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v8", stage="make"
        )
        with mock.patch(
            "workshop.workflow.native_run.CodexNativeSessionLauncher"
        ) as launcher_type:
            _native_launcher(checkpoint, initial_make_proof_boundary=True)

        launcher_type.assert_called_once_with(
            reasoning_effort="medium",
            auto_compact_token_limit=DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT,
            runtime_profile_sha256="a" * 64,
            timeout_seconds=DEEP_V8_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS,
        )

    def test_deep_v9_prompt_preserves_v8_critical_path(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v9", stage="make"
        )

        self.assertIn(
            "This v9 proof turn has one 16-minute medium runway",
            _deep_make_critical_path_prompt(checkpoint),
        )
        self.assertIn(
            "v9 recovery stays on one proof runway",
            _deep_make_recovery_prompt(checkpoint),
        )

    def test_deep_v10_requires_real_states_and_source_first_final_handoff(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v10"
        )
        proof = _deep_make_critical_path_prompt(checkpoint)
        self.assertIn("This v10 proof turn", proof)
        self.assertIn("state-0.step.py", proof)
        self.assertIn("--state-sheet", proof)
        self.assertIn("viewpoint-only motion sheet is not state evidence", proof)

        final = _deep_make_critical_path_prompt(checkpoint, proof_boundary=False)
        self.assertIn("15-minute source handoff boundary", final)
        self.assertIn("next action must write", final)
        self.assertIn("do not call update_plan or get_goal", final)

        proof_recovery = _deep_make_recovery_prompt(checkpoint)
        self.assertIn("v10 proof recovery", proof_recovery)
        self.assertIn("three state STL inputs", proof_recovery)
        final_recovery = _deep_make_recovery_prompt(
            checkpoint, proof_boundary=False
        )
        self.assertIn("v10 proof marker remains valid", final_recovery)
        self.assertIn("write it in the next action", final_recovery)

    def test_deep_v11_keeps_real_states_and_makes_invent_recovery_action_first(self):
        make_checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v11", stage="make"
        )
        self.assertIn(
            "This v11 proof turn",
            _deep_make_critical_path_prompt(make_checkpoint),
        )
        self.assertIn(
            "v11 proof recovery",
            _deep_make_recovery_prompt(make_checkpoint),
        )

        invent_checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v11", stage="invent"
        )
        recovery = _deep_invent_recovery_prompt(invent_checkpoint)
        self.assertIn("source handoff, not a creative continuation", recovery)
        self.assertIn("first action must check only", recovery)
        self.assertIn("next action must invoke the exact Invent finalizer", recovery)
        self.assertIn("ten-minute boundary is repair reserve", recovery)

    def test_deep_v7_make_after_proof_restores_high_normal_turn_boundary(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v7", stage="make"
        )
        with mock.patch(
            "workshop.workflow.native_run.CodexNativeSessionLauncher"
        ) as launcher_type:
            _native_launcher(
                checkpoint,
                initial_make_proof_boundary=False,
            )

        launcher_type.assert_called_once_with(
            reasoning_effort="high",
            auto_compact_token_limit=DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT,
            runtime_profile_sha256="a" * 64,
            timeout_seconds=DEEP_NATIVE_TURN_TIMEOUT_SECONDS,
        )
        recovery_prompt = _deep_make_recovery_prompt(
            checkpoint,
            proof_boundary=True,
        )
        self.assertIn("independent native critic", recovery_prompt)
        self.assertIn("persist the smallest complete product source", recovery_prompt)
        self.assertIn("v7 recovery stays on the proof fast path", recovery_prompt)
        self.assertIn("one foreground tool call", recovery_prompt)
        final_recovery = _deep_make_recovery_prompt(
            checkpoint,
            proof_boundary=False,
        )
        self.assertIn("final-product recovery", final_recovery)
        self.assertIn("proof marker remains valid", final_recovery)
        self.assertNotIn("write .make-proof-ready.json", final_recovery)
        self.assertEqual(
            _deep_make_recovery_prompt(
                self._launcher_checkpoint(
                    effort="quest",
                    economics_capability="deep-v3",
                    stage="make",
                )
            ),
            "",
        )

    def test_deep_v7_invent_recovery_is_medium_bounded_and_decisive(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v7", stage="invent"
        )
        with mock.patch(
            "workshop.workflow.native_run.CodexNativeSessionLauncher"
        ) as launcher_type:
            _native_launcher(checkpoint, recoverable_continuation=True)

        launcher_type.assert_called_once_with(
            reasoning_effort="medium",
            auto_compact_token_limit=DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT,
            runtime_profile_sha256="a" * 64,
            timeout_seconds=DEEP_V5_INVENT_RECOVERY_TIMEOUT_SECONDS,
        )
        prompt = _deep_invent_recovery_prompt(checkpoint)
        self.assertIn("Do not restart roster comparison", prompt)
        self.assertIn("finalizer immediately", prompt)
        self.assertEqual(
            _deep_invent_recovery_prompt(
                self._launcher_checkpoint(
                    effort="quest",
                    economics_capability="deep-v4",
                    stage="invent",
                )
            ),
            "",
        )

    def test_deep_v4_retains_frozen_reasoning_compaction_and_boundaries(self):
        for stage, reasoning in (
            ("invent", "high"),
            ("make", "high"),
            ("playtest", "medium"),
            ("release", "medium"),
        ):
            with self.subTest(stage=stage), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher"
            ) as launcher_type:
                checkpoint = self._launcher_checkpoint(
                    effort="quest", economics_capability="deep-v4", stage=stage
                )
                _native_launcher(
                    checkpoint,
                    initial_make_proof_boundary=(stage == "make"),
                )

                launcher_type.assert_called_once_with(
                    reasoning_effort=reasoning,
                    auto_compact_token_limit=(
                        DEEP_MAKE_AUTO_COMPACT_TOKEN_LIMIT
                        if stage == "make"
                        else DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT
                    ),
                    runtime_profile_sha256="a" * 64,
                    timeout_seconds=(
                        DEEP_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS
                        if stage == "make"
                        else DEEP_NATIVE_TURN_TIMEOUT_SECONDS
                    ),
                )

    def test_deep_v7_make_proof_marker_is_exact_checkpoint_bound_hint(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v7", stage="make"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            paths = NativeRunPaths(
                workspace=root / "workspace",
                host_state=root / "host-state",
            )
            paths.workspace.mkdir()
            paths.host_state.mkdir()
            marker = _make_proof_ready_path(paths)

            self.assertFalse(_make_proof_ready(paths, checkpoint))
            marker.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "autonomous-workshop.make-proof-ready",
                        "checkpoint_sha256": checkpoint.checkpoint_sha256,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertTrue(_make_proof_ready(paths, checkpoint))

            marker.write_text("{}\n", encoding="utf-8")
            self.assertFalse(_make_proof_ready(paths, checkpoint))
            self.assertFalse(marker.exists())

    def test_deep_v10_marker_requires_three_distinct_durable_state_proofs(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v10", stage="make"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            paths = NativeRunPaths(
                workspace=root / "workspace",
                host_state=root / "host-state",
            )
            paths.workspace.mkdir()
            paths.host_state.mkdir()
            marker = _make_proof_ready_path(paths)
            marker.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "autonomous-workshop.make-proof-ready",
                        "checkpoint_sha256": checkpoint.checkpoint_sha256,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertFalse(_make_proof_ready(paths, checkpoint))
            self.assertFalse(marker.exists())

            proof = (
                paths.workspace
                / "artifacts/make/r0001/product/review/early-proof"
            )
            proof.mkdir(parents=True)
            for name in (
                "proof.py",
                "state-0.step.py",
                "state-1.step.py",
                "state-2.step.py",
                "state-0.step",
                "state-1.step",
                "state-2.step",
                "held.png",
                "signature.png",
                "finding.json",
            ):
                (proof / name).write_bytes((name + "\n").encode())
            for index in range(3):
                (proof / ("state-%d.stl" % index)).write_bytes(
                    ("distinct-state-%d\n" % index).encode()
                )
            marker.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "autonomous-workshop.make-proof-ready",
                        "checkpoint_sha256": checkpoint.checkpoint_sha256,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertTrue(_make_proof_ready(paths, checkpoint))

    def test_deep_v7_make_proof_marker_fails_closed_on_symlink(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v7", stage="make"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            paths = NativeRunPaths(
                workspace=root / "workspace",
                host_state=root / "host-state",
            )
            paths.workspace.mkdir()
            paths.host_state.mkdir()
            outside = root / "outside.json"
            outside.write_text("{}\n", encoding="utf-8")
            _make_proof_ready_path(paths).symlink_to(outside)

            with self.assertRaisesRegex(StateConflict, "regular file"):
                _make_proof_ready(paths, checkpoint)

    def test_deep_v3_retains_medium_make_and_24k_compaction(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v3", stage="make"
        )
        with mock.patch(
            "workshop.workflow.native_run.CodexNativeSessionLauncher"
        ) as launcher_type:
            _native_launcher(
                checkpoint,
                initial_make_proof_boundary=True,
            )

        launcher_type.assert_called_once_with(
            reasoning_effort="medium",
            auto_compact_token_limit=DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT,
            runtime_profile_sha256="a" * 64,
            timeout_seconds=DEEP_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS,
        )

    def test_deep_v2_retains_effective_all_high_session_binding(self):
        checkpoint = self._launcher_checkpoint(
            effort="quest", economics_capability="deep-v2", stage="make"
        )
        with mock.patch(
            "workshop.workflow.native_run.CodexNativeSessionLauncher"
        ) as launcher_type:
            _native_launcher(
                checkpoint,
                initial_make_proof_boundary=True,
            )

        launcher_type.assert_called_once_with(
            reasoning_effort="high",
            auto_compact_token_limit=DEEP_LEGACY_AUTO_COMPACT_TOKEN_LIMIT,
            timeout_seconds=DEEP_NATIVE_TURN_TIMEOUT_SECONDS,
        )

    def test_deep_v1_retains_all_high_profile_and_original_turn_cap(self):
        for effort in ("forge", "quest"):
            with self.subTest(effort=effort), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher"
            ) as launcher_type:
                checkpoint = self._launcher_checkpoint(
                    effort=effort, economics_capability="deep-v1"
                )
                _native_launcher(checkpoint)

                launcher_type.assert_called_once_with(
                    reasoning_effort="high",
                    auto_compact_token_limit=DEEP_V1_AUTO_COMPACT_TOKEN_LIMIT,
                    timeout_seconds=DEEP_NATIVE_TURN_TIMEOUT_SECONDS,
                )
                self.assertEqual(
                    _native_turn_limit(checkpoint), DEEP_V1_NATIVE_TURN_LIMIT
                )

    def test_older_forge_and_unmarked_spark_retain_historical_high_profile(self):
        for effort, marker in (("forge", None), ("spark", None)):
            with self.subTest(effort=effort, marker=marker), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher"
            ) as launcher_type:
                checkpoint = self._launcher_checkpoint(
                    effort=effort, economics_capability=marker
                )
                _native_launcher(checkpoint)

                launcher_type.assert_called_once_with(reasoning_effort="high")
                self.assertEqual(_native_turn_limit(checkpoint), 32)

    def test_newer_cad_rejection_supersedes_resolved_make_proposal_feedback(self):
        proposal_rejection = {"failure_code": "make-product-metadata-invalid"}
        cad_rejection = {"failure_code": "declared-cad-output-changed"}

        self.assertIs(
            _current_make_proposal_rejection(None, proposal_rejection),
            proposal_rejection,
        )
        self.assertIsNone(
            _current_make_proposal_rejection(cad_rejection, proposal_rejection)
        )

    @staticmethod
    def _release_protocol_checkpoint(
        *, manual_first, direct_release=False, manual_design=False
    ):
        inputs = {
            ".agents/skills/autonomous-workshop/scripts/stage_proposal.py": "a" * 64,
        }
        if manual_first:
            inputs[
                ".agents/skills/autonomous-workshop/scripts/pdf_validator.py"
            ] = "b" * 64
        if direct_release:
            inputs[
                ".agents/skills/autonomous-workshop/references/direct-release-v1.md"
            ] = "c" * 64
        if manual_design:
            inputs[
                ".agents/skills/autonomous-workshop/references/manual-design-evidence-v1.md"
            ] = "d" * 64
        return AgentRunCheckpoint(
            product_id="release-protocol-fixture",
            stage="release",
            status="active",
            revision=4,
            round_index=1,
            max_rounds=4,
            wish_sha256="c" * 64,
            run_root_sha256="d" * 64,
            host_state_root_sha256="e" * 64,
            checkpoint_sha256="f" * 64,
            input_sha256s=inputs,
            inventor_roster=(),
            stage_artifacts={},
            invalidated_stages=(),
        )

    def test_release_contract_follows_the_frozen_run_finalizer_capability(self):
        legacy = _materialized_release_contract(
            self._release_protocol_checkpoint(manual_first=False)
        )
        current = _materialized_release_contract(
            self._release_protocol_checkpoint(manual_first=True)
        )
        direct = _materialized_release_contract(
            self._release_protocol_checkpoint(
                manual_first=True,
                direct_release=True,
            )
        )
        reviewed = _materialized_release_contract(
            self._release_protocol_checkpoint(
                manual_first=True,
                manual_design=True,
            )
        )
        reviewed_direct = _materialized_release_contract(
            self._release_protocol_checkpoint(
                manual_first=True,
                direct_release=True,
                manual_design=True,
            )
        )

        self.assertEqual(
            legacy,
            {
                "native_release_schema_version": 1,
                "manual_path": "MANUAL.md",
                "product_schema_version": 3,
                "product_status": "page-ready",
            },
        )
        self.assertEqual(
            current,
            {
                "native_release_schema_version": 2,
                "manual_path": "MANUAL.pdf",
                "product_schema_version": 4,
                "product_status": "manual-ready",
            },
        )
        self.assertEqual(
            direct,
            {
                "native_release_schema_version": 3,
                "manual_path": "MANUAL.pdf",
                "product_schema_version": 5,
                "product_status": "manual-ready",
                "playtest_status": "not-run",
                "playtest_omission_path": "PLAYTEST-NOT-RUN.json",
            },
        )
        self.assertEqual(
            reviewed,
            {
                "native_release_schema_version": 2,
                "manual_path": "MANUAL.pdf",
                "product_schema_version": 4,
                "product_status": "manual-ready",
                "manual_design_evidence_path": "MANUAL-DESIGN.json",
                "manual_design_evidence_schema_version": 1,
            },
        )
        self.assertEqual(
            reviewed_direct,
            {
                "native_release_schema_version": 3,
                "manual_path": "MANUAL.pdf",
                "product_schema_version": 5,
                "product_status": "manual-ready",
                "playtest_status": "not-run",
                "playtest_omission_path": "PLAYTEST-NOT-RUN.json",
                "manual_design_evidence_path": "MANUAL-DESIGN.json",
                "manual_design_evidence_schema_version": 1,
            },
        )

    def test_release_contract_fails_closed_without_a_materialized_finalizer(self):
        checkpoint = self._release_protocol_checkpoint(manual_first=False)
        checkpoint = AgentRunCheckpoint(
            **{
                **checkpoint.__dict__,
                "input_sha256s": {},
            }
        )
        with self.assertRaisesRegex(
            StateConflict, "materialized stage finalizer"
        ):
            _materialized_release_contract(checkpoint)

    def test_host_prunes_only_empty_make_directories_before_native_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary).resolve() / "run"
            product = run_root / "artifacts/make/r0001/product"
            empty_leaf = product / "cad/__cadgen__/empty-cache"
            empty_leaf.mkdir(parents=True)
            nonempty = product / "cad/project"
            nonempty.mkdir()
            source = nonempty / "toy.step.py"
            source.write_text("pass\n", encoding="utf-8")
            linked = product / "cad/linked-cache"
            linked.symlink_to(nonempty, target_is_directory=True)
            checkpoint = AgentRunCheckpoint(
                product_id="host-empty-cleanup",
                stage="make",
                status="active",
                revision=3,
                round_index=1,
                max_rounds=4,
                wish_sha256="a" * 64,
                run_root_sha256="b" * 64,
                host_state_root_sha256="c" * 64,
                checkpoint_sha256="d" * 64,
                input_sha256s={},
                inventor_roster=(),
                stage_artifacts={},
                invalidated_stages=(),
            )

            _prune_empty_make_product_directories(run_root, checkpoint)

            self.assertTrue(product.is_dir())
            self.assertFalse(empty_leaf.exists())
            self.assertFalse((product / "cad/__cadgen__").exists())
            self.assertTrue(nonempty.is_dir())
            self.assertEqual(source.read_text(encoding="utf-8"), "pass\n")
            self.assertTrue(linked.is_symlink())

    def test_second_mutating_host_fails_while_run_lock_is_held(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            host_state = root / "host-state"
            host_state.mkdir(mode=0o700)
            paths = NativeRunPaths(root / "toy", host_state)

            with _native_run_mutation_lock(paths):
                with self.assertRaisesRegex(
                    StateConflict, "already mutating this Wish"
                ):
                    with _native_run_mutation_lock(paths):
                        self.fail("a second mutating host acquired the run lock")

            self.assertEqual(
                stat.S_IMODE((host_state / "mutation.lock").stat().st_mode),
                0o600,
            )

    def test_source_checkout_still_places_new_run_in_private_workshop_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            repository = root / "repository"
            repository.mkdir(mode=0o700)
            home = root / "workshop-home"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=repository,
            ):
                paths = native_run_paths("stable-toy-id", create=True)

            self.assertEqual(
                paths.workspace,
                home / "runs/stable-toy-id/workspace",
            )
            self.assertEqual(paths.host_state, home / "state/stable-toy-id")
            self.assertFalse(paths.workspace.exists())
            self.assertFalse(paths.host_state.exists())
            self.assertFalse((repository / "toys").exists())
            self.assertEqual(
                stat.S_IMODE((home / "runs/stable-toy-id").stat().st_mode),
                0o700,
            )
            self.assertTrue((home / "state").is_dir())

    def test_failed_run_materialization_releases_only_its_empty_reservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "retryable-materialization-wish"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.AgentRun.create",
                side_effect=ContractError("fixture input validation failed"),
            ), self.assertRaisesRegex(ContractError, "fixture input validation"):
                start_native_run(
                    Wish.create(product_id, "a retryable clockwork bird")
                )

            self.assertFalse((home / "runs" / product_id).exists())
            self.assertFalse((home / "state" / product_id).exists())

    def test_create_rejects_a_legacy_source_checkout_collision(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            repository = root / "repository"
            legacy = repository / "toys/colliding-wish"
            legacy.mkdir(mode=0o700, parents=True)
            home = root / "workshop-home"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=repository,
            ), self.assertRaisesRegex(
                StateConflict, "workspace already exists"
            ):
                native_run_paths("colliding-wish", create=True)

            self.assertFalse((home / "runs/colliding-wish").exists())

    def test_old_workshop_home_toy_layout_resolves_without_moving(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            workspace = home / "toys/old-home-wish"
            host_state = home / "state/old-home-wish"
            workspace.mkdir(mode=0o700, parents=True)
            host_state.mkdir(mode=0o700, parents=True)
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ):
                paths = native_run_paths("old-home-wish")

            self.assertEqual(paths.workspace, workspace)
            self.assertEqual(paths.host_state, host_state)
            self.assertFalse((home / "runs/old-home-wish").exists())

    def test_open_rejects_symlinked_new_run_container(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            home = root / "workshop-home"
            runs = home / "runs"
            runs.mkdir(mode=0o700, parents=True)
            outside = root / "outside"
            (outside / "workspace").mkdir(mode=0o700, parents=True)
            (runs / "linked-wish").symlink_to(outside, target_is_directory=True)
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), self.assertRaisesRegex(
                StateConflict, "native run container must be a real directory"
            ):
                native_run_paths("linked-wish")

            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ):
                self.assertTrue(native_run_exists("linked-wish"))

    def test_open_rejects_ambiguous_new_and_legacy_workspaces(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            repository = root / "repository"
            (repository / "toys/ambiguous-wish").mkdir(
                mode=0o700, parents=True
            )
            home = root / "workshop-home"
            (home / "runs/ambiguous-wish/workspace").mkdir(
                mode=0o700, parents=True
            )
            os.chmod(home / "runs", 0o700)
            os.chmod(home / "runs/ambiguous-wish", 0o700)
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=repository,
            ), self.assertRaisesRegex(
                StateConflict, "ambiguous across multiple layouts"
            ):
                native_run_paths("ambiguous-wish")

    def test_live_source_checkout_legacy_run_stays_status_and_resume_compatible(self):
        launcher = _FakeLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            repository = root / "repository"
            (repository / "toys").mkdir(mode=0o700, parents=True)
            home = root / "workshop-home"
            (home / "state").mkdir(mode=0o700, parents=True)
            product_id = "wish-legacy-live"
            legacy_paths = NativeRunPaths(
                workspace=repository / "toys" / product_id,
                host_state=home / "state" / product_id,
            )
            environment = {"WORKSHOP_HOME": str(home)}
            with mock.patch.dict(
                os.environ, environment, clear=True
            ), mock.patch(
                "workshop.workflow.native_run.native_run_paths",
                return_value=legacy_paths,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ):
                start_native_run(
                    Wish.create(product_id, "a legacy path-bound clockwork toy")
                )

            resumed_launcher = _FakeLauncher()
            with mock.patch.dict(
                os.environ, environment, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=repository,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=resumed_launcher,
            ):
                self.assertTrue(native_run_exists(product_id))
                status = native_run_status(product_id)
                resumed = resume_native_run(product_id)

            self.assertEqual(status["product_id"], product_id)
            self.assertEqual(status["session_status"], "checkpointed")
            self.assertEqual(resumed["action"], "resumed")
            self.assertEqual(len(resumed_launcher.resumes), 1)
            self.assertEqual(
                resumed_launcher.resumes[0]["run_root"],
                legacy_paths.workspace,
            )
            self.assertFalse((home / "runs" / product_id).exists())

    def test_wish_starts_native_session_before_any_effect_path(self):
        launcher = _FakeLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            stdout = StringIO()
            stderr = StringIO()
            with mock.patch.dict(
                os.environ,
                {
                    "WORKSHOP_HOME": str(home),
                    "FACTORY_PASSWORD": "must-never-be-used",
                },
                clear=True,
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), redirect_stdout(stdout), redirect_stderr(stderr):
                result = main(
                    (
                        "wish",
                        "a",
                        "wind-up",
                        "version",
                        "of",
                        "my",
                        "dog",
                        "--json",
                    )
                )

            self.assertEqual(result, 0)
            receipt = json.loads(stdout.getvalue())
            product_id = receipt["product_id"]
            workspace = home / "runs" / product_id / "workspace"
            host_state = home / "state" / product_id
            self.assertEqual(len(launcher.starts), 1)
            arguments = launcher.starts[0]
            self.assertEqual(arguments["run_root"], workspace)
            self.assertEqual(arguments["host_state_root"], host_state)
            self.assertEqual(stat.S_IMODE(workspace.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(host_state.stat().st_mode), 0o700)
            self.assertEqual(
                (workspace / "WISH.json").read_bytes(),
                canonical_wish_bytes(
                    Wish.create(
                        product_id,
                        "a wind-up version of my dog",
                        context={"source": "workshop-cli"},
                    )
                ),
            )
            self.assertTrue((workspace / "AGENTS.md").is_file())
            self.assertTrue(
                (
                    workspace
                    / ".agents"
                    / "skills"
                    / "autonomous-workshop"
                    / "SKILL.md"
                ).is_file()
            )
            for skill_name in (
                "cad",
                "design-reference",
                "electromechanical-integration",
                "image-to-cad",
                "manual-design",
                "step-parts",
            ):
                self.assertTrue(
                    (
                        workspace
                        / ".agents"
                        / "skills"
                        / skill_name
                        / "SKILL.md"
                    ).is_file()
                )
            self.assertTrue(
                (
                    workspace
                    / ".agents"
                    / "skills"
                    / "manual-design"
                    / "references"
                    / "product-manual-visual-system.md"
                ).is_file()
            )
            for inventor_id in (
                "abo",
                "alice",
                "bob",
                "eve",
                "ivy",
                "leo",
                "mira-fold",
                "pico-press",
                "tess-loop",
            ):
                self.assertTrue(
                    (workspace / ".codex" / "agents" / (inventor_id + ".toml")).is_file()
                )
                self.assertTrue(
                    (
                        workspace
                        / ".agents"
                        / "skills"
                        / (inventor_id + "-inventor")
                        / "SKILL.md"
                    ).is_file()
                )
            self.assertFalse((workspace / "catalog").exists())
            prompt = arguments["prompt"]
            self.assertIn("local AGENTS.md", prompt)
            self.assertIn("autonomous-workshop skill", prompt)
            self.assertIn("current make stage", prompt)
            self.assertIn("Create one native Goal", prompt)
            self.assertIn("successful finalization as its stopping condition", prompt)
            self.assertIn("inspecting, acting, evaluating, and improving", prompt)
            self.assertIn("prior proposal failed its host gate", prompt)
            self.assertIn("current subject is a new stage attempt", prompt)
            self.assertIn("never rerun the finalizer", prompt)
            self.assertIn("resubmit unchanged rejected bytes", prompt)
            self.assertIn("complete the goal", prompt)
            self.assertIn("STAGE.json", prompt)
            self.assertIn("agent-outcome.json", prompt)
            self.assertNotIn("wind-up", prompt)
            self.assertNotIn(str(home), prompt)
            self.assertNotIn("FACTORY", prompt)
            self.assertEqual(receipt["publication"]["status"], "not-created")
            self.assertTrue(receipt["publication"]["requested"])
            self.assertEqual(receipt["effort"], "spark")
            self.assertIn("Effort: Spark", stderr.getvalue())
            self.assertIn(
                "Starting one native Codex session for Make",
                stderr.getvalue(),
            )

    def test_resume_uses_exact_materialized_binding(self):
        launcher = _FakeLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            environment = {"WORKSHOP_HOME": str(home)}
            output = StringIO()
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), redirect_stdout(output), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(("wish", "a moon that waddles", "--json")),
                    0,
                )
            started_receipt = json.loads(output.getvalue())
            product_id = started_receipt["product_id"]
            started = launcher.starts[0]

            output = StringIO()
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.product_run_agent_assets",
                side_effect=AssertionError("resume must use materialized bytes"),
            ) as current_assets, redirect_stdout(output), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(("resume", product_id, "--json")),
                    0,
                )
            resumed_receipt = json.loads(output.getvalue())
            self.assertEqual(len(launcher.resumes), 1)
            resumed = launcher.resumes[0]
            for field in (
                "product_id",
                "wish_sha256",
                "constitution_sha256",
                "run_root",
                "host_state_root",
            ):
                self.assertEqual(resumed[field], started[field])
            self.assertNotIn("moon that waddles", resumed["prompt"])
            self.assertNotIn(str(home), resumed["prompt"])
            self.assertEqual(resumed_receipt["action"], "resumed")
            current_assets.assert_not_called()

            output = StringIO()
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), redirect_stdout(output):
                self.assertEqual(main(("status", product_id, "--json")), 0)
            status = json.loads(output.getvalue())
            self.assertEqual(status["kind"], "native-agent-run")
            self.assertEqual(status["session_status"], "checkpointed")
            self.assertEqual(
                status["agent_instructions_sha256"],
                started["constitution_sha256"],
            )

    def test_resume_safely_restarts_only_when_no_session_checkpoint_exists(self):
        interrupted = _FakeLauncher(fail_first_start=True)
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            environment = {"WORKSHOP_HOME": str(home)}
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=interrupted,
            ), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(main(("wish", "a tiny orbit", "--json")), 2)

            product_ids = [path.name for path in (home / "runs").iterdir()]
            self.assertEqual(len(product_ids), 1)
            product_id = product_ids[0]
            self.assertFalse(
                (home / "state" / product_id / "codex-session.json").exists()
            )

            recovered = _FakeLauncher()
            output = StringIO()
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=recovered,
            ), redirect_stdout(output), redirect_stderr(StringIO()):
                self.assertEqual(main(("resume", product_id, "--json")), 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["action"], "started-after-interruption")
            self.assertEqual(len(recovered.starts), 1)
            self.assertEqual(recovered.resumes, [])

    def test_launcher_failure_after_exact_proposal_uses_normal_gate_and_continues(self):
        launcher = _FinalizedMatchThenFailLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "post-finalizer-launch-failure"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                receipt = start_native_run(
                    Wish.create(product_id, "a small resilient clockwork toy")
                )

            self.assertEqual(receipt["stage"], "invent")
            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(receipt["native_turns"], 2)
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 1)
            self.assertIn("current invent stage", launcher.resumes[0]["prompt"])
            workspace = home / "runs" / product_id / "workspace"
            host_state = home / "state" / product_id
            self.assertEqual(
                launcher.starts[0]["finalization_marker"],
                workspace / "agent-outcome.json",
            )
            self.assertFalse((workspace / "agent-outcome.json").exists())
            self.assertTrue(
                any(
                    path.name.endswith("-match.json")
                    for path in (host_state / "gates").iterdir()
                )
            )

    def test_resume_consumes_interrupted_finalized_stage_before_new_turn(self):
        interrupted = _FinalizedMatchThenInterruptLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "interrupted-after-exact-finalization"
            environment = {"WORKSHOP_HOME": str(home)}
            with mock.patch.dict(
                os.environ, environment, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=interrupted,
            ), self.assertRaises(KeyboardInterrupt):
                start_native_run(
                    Wish.create(
                        product_id,
                        "a toy finalized immediately before host interruption",
                    )
                )

            workspace = home / "runs" / product_id / "workspace"
            self.assertTrue((workspace / "agent-outcome.json").is_file())
            with mock.patch.dict(os.environ, environment, clear=True):
                interrupted_status = native_run_status(product_id)
            self.assertEqual(
                interrupted_status["progress"]["activity"], "failed"
            )

            resumed = _FakeLauncher()
            timing_events = []
            with mock.patch.dict(
                os.environ, environment, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=resumed,
            ):
                receipt = resume_native_run(
                    product_id,
                    timing_observer=timing_events.append,
                )

            self.assertEqual(receipt["stage"], "invent")
            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(resumed.starts, [])
            self.assertEqual(len(resumed.resumes), 1)
            self.assertIn("current invent stage", resumed.resumes[0]["prompt"])
            self.assertFalse((workspace / "agent-outcome.json").exists())
            gates = home / "state" / product_id / "gates"
            self.assertEqual(
                len(
                    [
                        path
                        for path in gates.iterdir()
                        if path.name.endswith("-match.json")
                    ]
                ),
                1,
            )
            match_starts = [
                event.operation
                for event in timing_events
                if event.stage == "match" and event.state == "started"
            ]
            invent_starts = [
                event.operation
                for event in timing_events
                if event.stage == "invent" and event.state == "started"
            ]
            self.assertEqual(
                match_starts,
                ["stage.prepare", "outcome.process", "gate.evaluate"],
            )
            self.assertNotIn("session.start", match_starts)
            self.assertNotIn("session.resume", match_starts)
            self.assertEqual(
                invent_starts,
                ["stage.prepare", "session.resume", "outcome.process"],
            )

    def test_recoverable_timeout_continues_same_session_inside_one_command(self):
        launcher = _RecoverableMatchContinuationLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "same-command-timeout-continuation"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.time.sleep"
            ) as backoff:
                receipt = start_native_run(
                    Wish.create(
                        product_id,
                        "a resilient toy completed across a transient timeout",
                    )
                )

            self.assertEqual(receipt["stage"], "invent")
            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(receipt["native_turns"], 3)
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 2)
            self.assertIn(
                "previous native turn ended at the host's timeout",
                launcher.resumes[0]["prompt"],
            )
            self.assertIn(
                "do not make finalization depend on a child agent",
                launcher.resumes[0]["prompt"],
            )
            self.assertNotIn(
                "previous native turn ended at the host's timeout",
                launcher.resumes[1]["prompt"],
            )
            backoff.assert_called_once()
            self.assertTrue(
                0
                < backoff.call_args.args[0]
                <= _RECOVERABLE_BACKOFF_MAX_SECONDS
            )
            self.assertEqual(
                {call["product_id"] for call in launcher.starts + launcher.resumes},
                {product_id},
            )
            host_state = home / "state" / product_id
            progress = json.loads(
                (host_state / "native-progress.json").read_text(encoding="utf-8")
            )
            self.assertEqual(progress["native_turns"], 3)
            self.assertEqual(progress["attempt_stage"], "invent")
            self.assertEqual(progress["stage_attempt"], 1)
            self.assertTrue(
                any(
                    path.name.endswith("-match.json")
                    for path in (host_state / "gates").iterdir()
                )
            )

    def test_normal_unfinished_turns_stop_early_and_remain_resumable(self):
        launcher = _AlwaysUnfinishedLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "bounded-normal-unfinished-continuation"
            environment = {"WORKSHOP_HOME": str(home)}
            with mock.patch.dict(
                os.environ, environment, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), self.assertRaisesRegex(
                WorkshopError,
                "returned without agent-outcome.json for 3 consecutive turns",
            ):
                start_native_run(
                    Wish.create(
                        product_id,
                        "a toy whose Goal repeatedly returns before finalization",
                    )
                )

            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(
                len(launcher.starts) + len(launcher.resumes),
                _MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS,
            )
            self.assertIn(
                "previous native turn returned without agent-outcome.json",
                launcher.resumes[0]["prompt"],
            )
            self.assertNotIn(
                "previous native turn ended at the host's timeout",
                launcher.resumes[0]["prompt"],
            )
            with mock.patch.dict(os.environ, environment, clear=True):
                status = native_run_status(product_id)
            self.assertEqual(status["status"], "active")
            self.assertEqual(status["session_status"], "checkpointed")
            self.assertEqual(
                status["native_turns"],
                _MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS,
            )
            self.assertEqual(status["progress"]["activity"], "failed")

            with mock.patch.dict(
                os.environ, environment, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), self.assertRaisesRegex(
                WorkshopError,
                "resumable with `workshop resume %s`" % product_id,
            ):
                resume_native_run(product_id)

            with mock.patch.dict(os.environ, environment, clear=True):
                resumed_status = native_run_status(product_id)
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 5)
            self.assertEqual(resumed_status["status"], "active")
            self.assertEqual(resumed_status["session_status"], "checkpointed")
            self.assertEqual(
                resumed_status["native_turns"],
                2 * _MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS,
            )

    def test_recoverable_interruptions_stop_early_and_remain_resumable(self):
        launcher = _AlwaysInterruptedLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "bounded-timeout-continuation"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.time.sleep"
            ) as backoff, self.assertRaisesRegex(
                WorkshopError,
                "did not complete for 2 consecutive recoverable turns",
            ):
                start_native_run(
                    Wish.create(
                        product_id,
                        "a bounded toy whose provider stays interrupted",
                    )
                )

            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(
                len(launcher.starts) + len(launcher.resumes),
                _MAX_CONSECUTIVE_RECOVERABLE_NATIVE_TURNS,
            )
            self.assertEqual(
                backoff.call_count,
                _MAX_CONSECUTIVE_RECOVERABLE_NATIVE_TURNS - 1,
            )
            delays = [call.args[0] for call in backoff.call_args_list]
            self.assertTrue(
                all(0 < delay <= _RECOVERABLE_BACKOFF_MAX_SECONDS for delay in delays)
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ):
                status = native_run_status(product_id)
                checkpoint = AgentRun.open(
                    home / "runs" / product_id / "workspace",
                    host_state_root=home / "state" / product_id,
                ).snapshot()
            self.assertEqual(
                delays,
                [
                    _recoverable_native_turn_backoff_seconds(checkpoint, turn)
                    for turn in range(
                        1, _MAX_CONSECUTIVE_RECOVERABLE_NATIVE_TURNS
                    )
                ],
            )
            self.assertEqual(status["stage"], "match")
            self.assertEqual(status["status"], "active")
            self.assertEqual(
                status["native_turns"],
                _MAX_CONSECUTIVE_RECOVERABLE_NATIVE_TURNS,
            )
            self.assertEqual(
                status["progress"]["stage_attempt"],
                {
                    "stage": "match",
                    "number": _MAX_CONSECUTIVE_RECOVERABLE_NATIVE_TURNS,
                },
            )
            self.assertEqual(status["progress"]["activity"], "failed")

            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.time.sleep"
            ) as resumed_backoff, self.assertRaisesRegex(
                WorkshopError,
                "resumable with `workshop resume %s`" % product_id,
            ):
                resume_native_run(product_id)

            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(
                len(launcher.starts) + len(launcher.resumes),
                2 * _MAX_CONSECUTIVE_RECOVERABLE_NATIVE_TURNS,
            )
            self.assertEqual(
                resumed_backoff.call_count,
                _MAX_CONSECUTIVE_RECOVERABLE_NATIVE_TURNS - 1,
            )

    def test_nonrecoverable_checkpointed_failure_is_not_continued(self):
        launcher = _AlwaysInterruptedLauncher(recoverable=False)
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "hard-native-turn-failure"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), self.assertRaisesRegex(
                WorkshopError, "native Codex session did not complete"
            ):
                start_native_run(
                    Wish.create(
                        product_id,
                        "a toy whose unknown native failure must stop",
                    )
                )

            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(launcher.resumes, [])

    def test_recoverable_failure_before_session_binding_fails_closed(self):
        launcher = _UnboundRecoverableLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "unbound-native-turn-timeout"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), self.assertRaisesRegex(
                WorkshopError, "native Codex session did not complete"
            ):
                start_native_run(
                    Wish.create(
                        product_id,
                        "a toy whose unbound session must not be duplicated",
                    )
                )

            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(launcher.resumes, [])
            self.assertFalse(
                (home / "state" / product_id / "codex-session.json").exists()
            )

    def test_launcher_failure_with_stale_proposal_fails_closed(self):
        launcher = _FinalizedMatchThenFailLauncher(stale_proposal=True)
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "stale-post-finalizer-proposal"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), self.assertRaisesRegex(StateConflict, "another checkpoint"):
                start_native_run(
                    Wish.create(product_id, "a stale proposal must never advance")
                )

            host_state = home / "state" / product_id
            self.assertFalse(
                any(
                    path.name.endswith("-match.json")
                    for path in (host_state / "gates").iterdir()
                )
            )
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(launcher.resumes, [])

    def test_launcher_failure_with_invalid_proposal_fails_closed(self):
        launcher = _FinalizedMatchThenFailLauncher(invalid_proposal=True)
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "invalid-post-finalizer-proposal"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), self.assertRaisesRegex(ContractError, "strict UTF-8 JSON"):
                start_native_run(
                    Wish.create(product_id, "an invalid proposal must never advance")
                )

            host_state = home / "state" / product_id
            self.assertFalse(
                any(
                    path.name.endswith("-match.json")
                    for path in (host_state / "gates").iterdir()
                )
            )
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(launcher.resumes, [])

    def test_status_reports_durable_safe_progress_and_attempted_turn_count(self):
        launcher = _FakeLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "durable-progress-wish"
            environment = {"WORKSHOP_HOME": str(home)}
            patches = (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch(
                    "workshop.workflow.native_run._source_checkout_root",
                    return_value=None,
                ),
                mock.patch(
                    "workshop.workflow.native_run.CodexNativeSessionLauncher",
                    return_value=launcher,
                ),
            )
            with patches[0], patches[1], patches[2]:
                started = start_native_run(
                    Wish.create(product_id, "a toy that makes its work visible")
                )
                inspected = native_run_status(product_id)
                resumed = resume_native_run(product_id)
                inspected_again = native_run_status(product_id)

            self.assertEqual(started["native_turns"], 1)
            self.assertEqual(
                started["needs"], ["fixture stops after one native turn"]
            )
            self.assertEqual(inspected["native_turns"], 1)
            self.assertEqual(
                inspected["needs"], ["fixture stops after one native turn"]
            )
            self.assertEqual(inspected["progress"]["status"], "available")
            self.assertEqual(
                inspected["progress"]["stage_attempt"],
                {"stage": "match", "number": 1},
            )
            self.assertEqual(inspected["progress"]["activity"], "completed")
            self.assertIsInstance(inspected["progress"]["elapsed_seconds"], int)
            self.assertRegex(
                inspected["progress"]["last_activity_at"],
                r"Z$",
            )
            self.assertEqual(resumed["native_turns"], 2)
            self.assertEqual(
                resumed["needs"], ["fixture stops after one native turn"]
            )
            self.assertEqual(inspected_again["native_turns"], 2)
            self.assertEqual(
                inspected_again["needs"],
                ["fixture stops after one native turn"],
            )
            self.assertEqual(
                inspected_again["progress"]["stage_attempt"],
                {"stage": "match", "number": 2},
            )
            progress_path = home / "state" / product_id / "native-progress.json"
            self.assertEqual(stat.S_IMODE(progress_path.stat().st_mode), 0o600)
            private = progress_path.read_text(encoding="utf-8")
            for forbidden in (
                "fixture stops after one native turn",
                "agent-outcome.json",
                "thread_id",
                "prompt",
                "arguments",
                "message",
            ):
                self.assertNotIn(forbidden, private)

    def test_start_and_resume_surface_only_safe_non_authoritative_activity(self):
        launcher = _ReportingFakeLauncher()
        observed = []

        def observe(activity):
            observed.append(activity)
            if activity == "reasoning":
                raise RuntimeError("presentation sink failed")

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "foreground-progress-wish"
            environment = {"WORKSHOP_HOME": str(home)}
            with mock.patch.dict(
                os.environ, environment, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ):
                started = start_native_run(
                    Wish.create(product_id, "a toy that shows bounded progress"),
                    activity_observer=observe,
                )
                resumed = resume_native_run(
                    product_id,
                    activity_observer=observe,
                )

        self.assertEqual(started["status"], "waiting")
        self.assertEqual(resumed["status"], "waiting")
        self.assertEqual(
            observed,
            ["starting", "reasoning", "tool", "running"],
        )

    def test_start_and_resume_emit_paired_timing_without_changing_turns(self):
        launcher = _FakeLauncher()
        events = []
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "timed-progress-wish"
            environment = {"WORKSHOP_HOME": str(home)}
            with mock.patch.dict(
                os.environ, environment, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ):
                started = start_native_run(
                    Wish.create(product_id, "private objective value"),
                    timing_observer=events.append,
                )
                resumed = resume_native_run(
                    product_id,
                    timing_observer=events.append,
                )

        self.assertEqual((started["native_turns"], resumed["native_turns"]), (1, 2))
        starts = [event for event in events if event.state == "started"]
        terminals = [event for event in events if event.state != "started"]
        self.assertEqual(len(starts), len(terminals))
        self.assertEqual(
            [event.operation for event in starts],
            [
                "run.initialize",
                "stage.prepare",
                "session.start",
                "outcome.process",
                "stage.prepare",
                "session.resume",
                "outcome.process",
            ],
        )
        self.assertEqual(
            [
                (event.product_id, event.stage, event.operation)
                for event in starts
            ],
            [
                (event.product_id, event.stage, event.operation)
                for event in terminals
            ],
        )
        rendered = repr([event.to_dict() for event in events])
        self.assertNotIn("private objective value", rendered)
        self.assertNotIn("fixture stops after one native turn", rendered)

    def test_invalid_activity_observer_is_rejected_before_run_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), self.assertRaisesRegex(ContractError, "observer must be callable"):
                start_native_run(
                    Wish.create("invalid-progress-sink", "a bounded clockwork toy"),
                    activity_observer="not-callable",
                )

            self.assertFalse(home.exists())

    def test_invalid_timing_observer_is_rejected_before_run_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), self.assertRaisesRegex(ContractError, "observer must be callable"):
                start_native_run(
                    Wish.create(
                        "invalid-timing-sink",
                        "a bounded clockwork toy",
                    ),
                    timing_observer="not-callable",
                )

            self.assertFalse(home.exists())

    def test_progress_throttles_active_event_churn_but_forces_terminal_classes(self):
        progress = NativeRunProgress(
            product_id="progress-throttle-wish",
            wish_sha256="a" * 64,
            checkpoint_sha256="b" * 64,
            checkpoint_stage="make",
            attempt_stage="make",
            stage_attempt=1,
            native_turns=1,
            activity="starting",
            attempt_started_at_ms=1,
            last_activity_at_ms=1,
        )
        with mock.patch(
            "workshop.workflow.native_run.time.monotonic",
            side_effect=(100.0, 100.1, 100.2, 100.3, 100.4),
        ), mock.patch(
            "workshop.workflow.native_run.write_native_progress"
        ) as write_progress:
            tracker = _NativeProgressTracker(Path("/unused"), progress)
            tracker.observe("reasoning")
            tracker.observe("tool")
            tracker.observe("finalizing")
            tracker.observe("completed")

        self.assertEqual(write_progress.call_count, 2)
        self.assertEqual(tracker.progress.activity, "completed")

    def test_untrusted_progress_is_hidden_without_blocking_valid_status(self):
        for case in ("tampered", "symlink"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                home = Path(temporary).resolve() / "workshop-home"
                product_id = "untrusted-progress-" + case
                environment = {"WORKSHOP_HOME": str(home)}
                launcher = _FakeLauncher()
                with mock.patch.dict(
                    os.environ, environment, clear=True
                ), mock.patch(
                    "workshop.workflow.native_run._source_checkout_root",
                    return_value=None,
                ), mock.patch(
                    "workshop.workflow.native_run.CodexNativeSessionLauncher",
                    return_value=launcher,
                ):
                    start_native_run(
                        Wish.create(product_id, "a valid run with optional telemetry")
                    )
                    path = home / "state" / product_id / "native-progress.json"
                    if case == "tampered":
                        value = json.loads(path.read_text(encoding="utf-8"))
                        value["activity"] = "completed"
                        value["native_turns"] = 999
                        path.write_text(json.dumps(value), encoding="utf-8")
                        os.chmod(path, 0o600)
                    else:
                        target = path.with_name("untrusted-target.json")
                        path.rename(target)
                        path.symlink_to(target)

                    receipt = native_run_status(product_id)
                    recovered = resume_native_run(product_id)

                self.assertEqual(receipt["status"], "waiting")
                self.assertEqual(receipt["stage"], "match")
                self.assertEqual(receipt["native_turns"], 0)
                self.assertEqual(receipt["progress"], {"status": "unavailable"})
                self.assertEqual(recovered["status"], "waiting")
                self.assertEqual(recovered["native_turns"], 2)
                self.assertEqual(recovered["progress"]["status"], "available")

    def test_factory_is_mandatory_and_github_is_opt_in_on_wish(self):
        command = parser()
        self.assertFalse(hasattr(command.parse_args(("wish", "a moon")), "publish"))
        self.assertFalse(command.parse_args(("wish", "a moon")).github)
        self.assertTrue(command.parse_args(("wish", "--github", "a moon")).github)
        self.assertFalse(
            hasattr(command.parse_args(("resume", "wish-one")), "publish")
        )
        self.assertFalse(
            hasattr(command.parse_args(("resume", "wish-one")), "github")
        )
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            command.parse_args(("wish", "a moon", "--publish"))


if __name__ == "__main__":
    unittest.main()
