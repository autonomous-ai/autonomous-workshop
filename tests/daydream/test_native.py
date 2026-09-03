import hashlib
import json
import os
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tests.invent.fake_gamevault import FAKE_TOKEN, FakeGameVaultTransport
from tests.daydream.support import (
    build_thesis_verdict_dict,
    horn_tip_catalog,
    horn_tip_thesis_dict as horn_tip_paraphrase_dict,
    inventor_bundle,
    sample_thesis_dict as sample_idea_dict,
)
from workshop.daydream.contracts import DaydreamError, Idea, SealedDaydream
from workshop.daydream.notebook import NotebookEntry, StructuralTrace, append_notebook_entry
from workshop.daydream.outcomes import remember_run_outcome
from workshop.daydream.native import (
    DAYDREAM_TURN_TIMEOUT_SECONDS,
    INVENTOR_BINDING_FILE_NAME,
    PROVENANCE_FILE_NAME,
    VAULT_BINDING_FILE_NAME,
    daydream_paths,
    list_daydreams,
    load_sealed_daydream,
    resolve_inventor,
    run_daydream,
    wish_from_daydream,
)
from workshop.runtime.agent_assets import parse_inventor_custom_agent_bytes
from workshop.daydream.prompt import (
    DAYDREAM_CONSTITUTION,
    DAYDREAM_CONSTITUTION_SHA256,
    JUDGE_CONSTITUTION,
    JUDGE_CONSTITUTION_SHA256,
)
from workshop.daydream.seeds import DaydreamSeed
from workshop.errors import ContractError
from workshop.invent.gamevault import GameVaultError, GameVaultUnavailable
from workshop.runtime.codex import CodexInvocationError, CodexRecoverableInvocationError
from workshop.runtime.managers import (
    NativeManagerInvocationError,
    NativeManagerRecoverableError,
)
from workshop.runtime.project_boundary import (
    PRODUCT_RUN_ROOT_MARKER,
    PRODUCT_RUN_ROOT_MARKER_BYTES,
)


MOMENT = datetime(2026, 9, 2, 10, 15, 0, tzinfo=timezone.utc)
FIRST_ID = "daydream-20260902-101500-00000001"
SECOND_ID = "daydream-20260902-101600-00000002"
SEED = DaydreamSeed(moment="a bus stop in the cold", twist="it counts something")


class _FakeOutcome:
    def __init__(self, arguments, *, used_web_search=True):
        self.arguments = arguments
        self.used_web_search = used_web_search

    def to_dict(self):
        return {
            "status": "completed",
            "used_web_search": self.used_web_search,
            "product_id": self.arguments["product_id"],
            "input_tokens": 12,
        }


class _FakeLauncher:
    manager_id = "codex"
    session_checkpoint_name = "codex-session.json"

    def __init__(
        self,
        test,
        *,
        timeout_seconds,
        idea=None,
        error=None,
        expect_notebook=(),
        expect_portfolio=(),
        error_after_idea=False,
        finalize=True,
        outcome_sha256=None,
        verdict="build",
        judge_error=None,
        used_web_search=True,
    ):
        self.test = test
        self.error_after_idea = error_after_idea
        self.finalize = finalize
        self.outcome_sha256 = outcome_sha256
        self.verdict = verdict
        self.judge_error = judge_error
        self.used_web_search = used_web_search
        self.timeout_seconds = timeout_seconds
        self.idea = idea
        self.error = error
        self.expect_notebook = expect_notebook
        self.expect_portfolio = expect_portfolio
        self.starts = []

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        run_root = Path(arguments["run_root"])
        host_state = Path(arguments["host_state_root"])
        if run_root.name == "judge-workspace":
            return self._judge(arguments, run_root, host_state)
        for name in (
            "TASTE.md",
            "PRIOR-WORK.md",
            "PORTFOLIO.md",
            "NOTEBOOK.md",
            "VAULT.md",
            "AGENTS.md",
            "finalize_daydream.py",
            "daydream_schema.py",
            PRODUCT_RUN_ROOT_MARKER,
        ):
            self.test.assertTrue((run_root / name).is_file(), name)
        self.test.assertEqual(
            (run_root / "AGENTS.md").read_text(encoding="utf-8"), DAYDREAM_CONSTITUTION
        )
        self.test.assertEqual(
            arguments["finalization_marker"], run_root / "agent-outcome.json"
        )
        self.test.assertEqual(
            (run_root / PRODUCT_RUN_ROOT_MARKER).read_bytes(), PRODUCT_RUN_ROOT_MARKER_BYTES
        )
        self.test.assertTrue((run_root / "work").is_dir())
        self.test.assertEqual(list((run_root / "work").iterdir()), [])
        skill = run_root / ".agents" / "skills" / "sample-inventor" / "SKILL.md"
        vault_skill = run_root / ".agents" / "skills" / "design-vault" / "SKILL.md"
        vault_tool = run_root / ".agents" / "skills" / "design-vault" / "vault_tools.py"
        agent = run_root / ".codex" / "agents" / "sample.toml"
        self.test.assertEqual(
            skill.read_bytes(),
            (self.test.source_root / "sample" / "skills" / "sample-inventor" / "SKILL.md").read_bytes(),
        )
        self.test.assertEqual(parse_inventor_custom_agent_bytes(agent.read_bytes()).inventor_id, "sample")
        self.test.assertEqual(stat.S_IMODE(skill.stat().st_mode), 0o400)
        self.test.assertTrue(vault_skill.is_file())
        self.test.assertTrue(vault_tool.is_file())
        self.test.assertEqual(stat.S_IMODE(vault_skill.stat().st_mode), 0o400)
        self.test.assertEqual(stat.S_IMODE(vault_tool.stat().st_mode), 0o400)
        self.test.assertEqual(stat.S_IMODE(agent.stat().st_mode), 0o400)
        self.test.assertEqual(stat.S_IMODE((run_root / ".agents").stat().st_mode), 0o500)
        self.test.assertEqual(stat.S_IMODE((run_root / ".codex").stat().st_mode), 0o500)
        self.test.assertEqual(stat.S_IMODE(host_state.stat().st_mode), 0o700)
        self.test.assertEqual(stat.S_IMODE(run_root.stat().st_mode), 0o700)
        self.test.assertFalse(host_state.is_relative_to(run_root))
        notebook = (run_root / "NOTEBOOK.md").read_text(encoding="utf-8")
        for expected in self.expect_notebook:
            self.test.assertIn(expected, notebook)
        portfolio = (run_root / "PORTFOLIO.md").read_text(encoding="utf-8")
        for expected in self.expect_portfolio:
            self.test.assertIn(expected, portfolio)
        if arguments["activity_observer"] is not None:
            arguments["activity_observer"]("reasoning")
        if self.error is not None and not self.error_after_idea:
            raise self.error
        if self.idea is not None:
            idea_path = run_root / "work" / "IDEA.json"
            idea_path.write_text(
                self.idea if isinstance(self.idea, str) else json.dumps(self.idea),
                encoding="utf-8",
            )
            if self.finalize:
                digest = self.outcome_sha256 or hashlib.sha256(idea_path.read_bytes()).hexdigest()
                (run_root / "agent-outcome.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "kind": "autonomous-workshop.daydream-outcome",
                            "status": "ready",
                            "idea_path": "work/IDEA.json",
                            "idea_bytes": idea_path.stat().st_size,
                            "idea_sha256": digest,
                            "title": "fixture",
                            "written_at": "2026-09-02T10:16:00Z",
                        }
                    ),
                    encoding="utf-8",
                )
        if self.error is not None:
            raise self.error
        return _FakeOutcome(arguments, used_web_search=self.used_web_search)


    def _judge(self, arguments, run_root, host_state):
        for name in (
            "IDEA.json",
            "TASTE.md",
            "ROUTE.md",
            "AGENTS.md",
            "finalize_daydream.py",
            "daydream_schema.py",
        ):
            self.test.assertTrue((run_root / name).is_file(), name)
        self.test.assertEqual((run_root / "AGENTS.md").read_text(encoding="utf-8"), JUDGE_CONSTITUTION)
        self.test.assertEqual(arguments["constitution_sha256"], JUDGE_CONSTITUTION_SHA256)
        self.test.assertTrue(arguments["product_id"].endswith("-judge"))
        self.test.assertEqual(stat.S_IMODE(host_state.stat().st_mode), 0o700)
        self.test.assertEqual(arguments["finalization_marker"], run_root / "agent-outcome.json")
        self.test.assertIn("Route budget: SPARK", (run_root / "ROUTE.md").read_text(encoding="utf-8"))
        idea = json.loads((run_root / "IDEA.json").read_text(encoding="utf-8"))
        self.test.assertEqual(idea["kind"], "autonomous-workshop.daydream-idea")
        if self.judge_error is not None:
            raise self.judge_error
        if self.verdict is not None:
            verdict_path = run_root / "work" / "VERDICT.json"
            daydream_id = arguments["product_id"].removesuffix("-judge")
            taste_sha256 = hashlib.sha256((run_root / "TASTE.md").read_bytes()).hexdigest()
            verdict = build_thesis_verdict_dict(
                self.verdict,
                daydream_id=daydream_id,
                idea_sha256=Idea.parse(idea).sha256,
                taste_sha256=taste_sha256,
                route="spark",
            )
            verdict_path.write_text(
                json.dumps(verdict) if isinstance(self.verdict, str) else self.verdict,
                encoding="utf-8",
            )
            (run_root / "agent-outcome.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "autonomous-workshop.daydream-outcome",
                        "status": "ready",
                        "role": "judge",
                        "idea_path": "work/VERDICT.json",
                        "idea_bytes": verdict_path.stat().st_size,
                        "idea_sha256": hashlib.sha256(verdict_path.read_bytes()).hexdigest(),
                        "title": "build",
                        "written_at": "2026-09-02T10:17:00Z",
                    }
                ),
                encoding="utf-8",
            )
        return _FakeOutcome(arguments)


class DaydreamNativeTest(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        root = Path(self._temporary.name).resolve()
        self.home = root / "home"
        self.source_root = root / "sources"
        inventor_bundle(self.source_root)
        self.catalog = root / "catalog"
        self.catalog.mkdir()
        self.environment = mock.patch.dict(os.environ, {"WORKSHOP_HOME": str(self.home)})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.factories = []

    def _factory(self, **options):
        launchers = []

        def factory(manager_id, **kwargs):
            kwargs = dict(kwargs)
            kwargs.pop("reasoning_effort", None)
            launcher = _FakeLauncher(self, **kwargs, **options)
            launchers.append((manager_id, kwargs, launcher))
            return launcher

        self.factories.append(launchers)
        return factory, launchers

    def _run(
        self,
        *,
        daydream_id=FIRST_ID,
        repository_root=None,
        activity_observer=None,
        judge=True,
        vault_loader=None,
        **options,
    ):
        factory, launchers = self._factory(**options)
        sealed = run_daydream(
            "sample",
            source_root=self.source_root,
            repository_root=self.catalog if repository_root is None else repository_root,
            launcher_factory=factory,
            activity_observer=activity_observer,
            seed=SEED,
            moment=MOMENT,
            daydream_id=daydream_id,
            judge=judge,
            vault_loader=vault_loader or self._unavailable_vault,
        )
        return sealed, launchers

    @staticmethod
    def _unavailable_vault():
        raise GameVaultUnavailable("fixture has no Vault")

    def test_happy_path_seals_the_idea_and_remembers_it(self):
        activities = []
        sealed, launchers = self._run(idea=sample_idea_dict(), activity_observer=activities.append)
        self.assertIsInstance(sealed, SealedDaydream)
        self.assertEqual(activities, ["reasoning"])
        manager_id, kwargs, launcher = launchers[0]
        self.assertEqual(manager_id, "codex")
        self.assertEqual(kwargs, {"timeout_seconds": DAYDREAM_TURN_TIMEOUT_SECONDS})
        start = launcher.starts[0]
        self.assertEqual(start["product_id"], FIRST_ID)
        self.assertEqual(start["constitution_sha256"], DAYDREAM_CONSTITUTION_SHA256)
        self.assertRegex(start["wish_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("Sample", start["prompt"])
        self.assertIn("a bus stop in the cold", start["prompt"])
        self.assertEqual(sealed.daydream_id, FIRST_ID)
        self.assertEqual(sealed.inventor_id, "sample")
        self.assertEqual(sealed.inventor_name, "Sample")
        self.assertEqual(sealed.manager_id, "codex")
        self.assertEqual(sealed.seed, SEED.to_dict())
        self.assertEqual(sealed.created_at, "2026-09-02T10:15:00Z")
        self.assertEqual(sealed.idea, Idea.parse(sample_idea_dict()))
        self.assertEqual(sealed.schema_version, 2)
        self.assertEqual(sealed.provenance.route, "spark")
        self.assertEqual(sealed.session, _FakeOutcome(start).to_dict())
        self.assertEqual(sealed.novelty.status, "new")
        paths = daydream_paths("sample", FIRST_ID)
        self.assertTrue(paths.container.is_relative_to(self.home / "daydreams" / "sample"))
        sealed_path = paths.host_state / "IDEA.json"
        self.assertEqual(stat.S_IMODE(sealed_path.stat().st_mode), 0o600)
        self.assertEqual(
            SealedDaydream.parse(json.loads(sealed_path.read_text(encoding="utf-8"))), sealed
        )
        self.assertEqual(
            (paths.workspace / "TASTE.md").read_bytes(),
            (self.source_root / "sample" / "TASTE.md").read_bytes(),
        )
        binding = json.loads(
            (paths.host_state / INVENTOR_BINDING_FILE_NAME).read_text(encoding="utf-8")
        )
        self.assertEqual(binding["inventor_id"], "sample")
        self.assertEqual(binding["taste_sha256"], sealed.taste_sha256)
        self.assertEqual(
            [skill["name"] for skill in binding["skills"]], ["sample-inventor"]
        )
        provenance = json.loads(
            (paths.host_state / PROVENANCE_FILE_NAME).read_text(encoding="utf-8")
        )
        self.assertEqual(provenance, sealed.provenance.to_dict())
        for field, path in (
            ("taste", paths.workspace / "TASTE.md"),
            ("prior_work", paths.workspace / "PRIOR-WORK.md"),
            ("portfolio", paths.workspace / "PORTFOLIO.md"),
            ("notebook", paths.workspace / "NOTEBOOK.md"),
        ):
            self.assertEqual(
                sealed.provenance.input_sha256s[field],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        self.assertEqual(
            sealed.provenance.input_sha256s["inventor_binding"],
            hashlib.sha256(
                (paths.host_state / INVENTOR_BINDING_FILE_NAME).read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(
            sealed.provenance.input_sha256s["vault_binding"],
            hashlib.sha256(
                (paths.host_state / VAULT_BINDING_FILE_NAME).read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(
            sealed.provenance.input_sha256s["daydream_prompt"],
            hashlib.sha256(start["prompt"].encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            stat.S_IMODE((paths.host_state / PROVENANCE_FILE_NAME).stat().st_mode),
            0o600,
        )
        entries = list_daydreams("sample")
        self.assertEqual(
            [(entry.daydream_id, entry.status) for entry in entries],
            [(FIRST_ID, "dreamed")],
        )
        self.assertEqual(entries[0].idea_sha256, sealed.idea_sha256)
        self.assertEqual(load_sealed_daydream("sample", FIRST_ID), sealed)
        vault_binding = json.loads(
            (paths.host_state / VAULT_BINDING_FILE_NAME).read_text(encoding="utf-8")
        )
        self.assertEqual(vault_binding, {"status": "unavailable"})
        self.assertFalse((paths.workspace / "VAULT.json").exists())
        self.assertIn(
            "Status: unavailable",
            (paths.workspace / "VAULT.md").read_text(encoding="utf-8"),
        )

    def test_available_vault_is_hash_bound_and_materialized_without_credentials(self):
        vault = FakeGameVaultTransport().vault()
        sealed, _launchers = self._run(
            idea=sample_idea_dict(), vault_loader=lambda: vault
        )
        paths = daydream_paths("sample", FIRST_ID)
        packed = vault.packed_bytes()
        digest = hashlib.sha256(packed).hexdigest()
        self.assertEqual((paths.workspace / "VAULT.json").read_bytes(), packed)
        self.assertEqual((paths.host_state / "VAULT.json").read_bytes(), packed)
        self.assertEqual(stat.S_IMODE((paths.workspace / "VAULT.json").stat().st_mode), 0o400)
        binding = json.loads(
            (paths.host_state / VAULT_BINDING_FILE_NAME).read_text(encoding="utf-8")
        )
        self.assertEqual(
            binding,
            {
                "status": "available",
                "path": "VAULT.json",
                "skill": ".agents/skills/design-vault/SKILL.md",
                "sha256": digest,
                "nodes": len(vault.nodes),
            },
        )
        self.assertIn(digest, (paths.workspace / "VAULT.md").read_text(encoding="utf-8"))
        workspace_bytes = b"".join(
            path.read_bytes()
            for path in paths.workspace.rglob("*")
            if path.is_file()
        )
        self.assertNotIn(FAKE_TOKEN.encode("utf-8"), workspace_bytes)
        self.assertEqual(sealed.idea.title, "Ladder Drop")

    def test_invalid_vault_evidence_fails_before_starting_a_native_session(self):
        def invalid_vault():
            raise GameVaultError("malformed fixture export")

        with self.assertRaisesRegex(DaydreamError, "invalid evidence"):
            self._run(idea=sample_idea_dict(), vault_loader=invalid_vault)
        self.assertEqual(self.factories[-1], [])

    def test_second_daydream_sees_the_first_and_may_not_repeat_it(self):
        self._run(idea=sample_idea_dict())
        raw = sample_idea_dict()
        raw["title"] = "Rung Counter"
        raw["one_liner"] = (
            "Tap a printed column and count the taps by how far a captive pin has climbed."
        )
        raw["experience"]["action"] = (
            "Tap the top of the column once per event you want to count."
        )
        raw["experience"]["response"] = (
            "Each tap ratchets a captive pin one notch higher."
        )
        raw["experience"]["payoff"] = (
            "A twist lets the climbed pin fall back to zero."
        )
        raw["keywords"] = ["ratchet", "counter", "pin"]
        sealed, launchers = self._run(
            daydream_id=SECOND_ID, idea=raw, expect_notebook=("Ladder Drop", FIRST_ID)
        )
        self.assertEqual(sealed.idea.title, "Rung Counter")
        self.assertEqual(sealed.novelty.nearest[0].source, "notebook:%s" % FIRST_ID)
        self.assertEqual(
            [entry.daydream_id for entry in list_daydreams("sample")], [FIRST_ID, SECOND_ID]
        )
        with self.assertRaisesRegex(DaydreamError, "rejected"):
            self._run(daydream_id="daydream-20260902-101700-00000003", idea=sample_idea_dict())

    def test_downstream_outcome_facts_reach_the_next_daydream_workspace(self):
        previous, _launchers = self._run(idea=sample_idea_dict())
        wish = wish_from_daydream(previous, wish_id="wish-outcome-memory")
        remember_run_outcome(
            wish,
            receipt={
                "effort": "forge",
                "manager": "codex",
                "status": "failed",
                "stage": "make",
                "publication": {"status": "not-created"},
            },
            moment=MOMENT,
            home=self.home,
        )
        raw = sample_idea_dict()
        raw["title"] = "Rung Counter"
        raw["one_liner"] = "Tap a pocket rail and watch a captive marker count upward."
        raw["experience"]["action"] = "Tap the top of the rail once per count."
        raw["experience"]["response"] = "A captive marker ratchets upward by one notch."
        raw["experience"]["payoff"] = "A twist drops the marker back to zero."
        raw["experience"]["anti_generic_signature"] = (
            "The same captive marker both ratchets upward and visibly free-falls on reset."
        )
        raw["keywords"] = ["rail", "marker", "ratchet", "counter"]
        self._run(
            daydream_id=SECOND_ID,
            idea=raw,
            expect_notebook=(
                "Downstream outcomes (host-observed facts, not Judge predictions)",
                "route=forge status=failed stage=make",
                "wish-outcome-memory",
            ),
        )

    def test_cross_inventor_portfolio_blocks_a_renamed_repeat(self):
        idea = Idea.parse(sample_idea_dict())
        other = self.home / "daydreams" / "other"
        other.mkdir(parents=True, mode=0o700)
        (self.home / "daydreams").chmod(0o700)
        other.chmod(0o700)
        append_notebook_entry(
            other / "NOTEBOOK.jsonl",
            NotebookEntry(
                daydream_id="daydream-20260902-091500-00000009",
                created_at="2026-09-02T09:15:00Z",
                title=idea.title,
                one_liner=idea.one_liner,
                idea_sha256=idea.sha256,
                status="dreamed",
                schema_version=2,
                structure=StructuralTrace.from_idea(idea),
            ),
        )
        raw = sample_idea_dict()
        raw["title"] = "Gravity Rungs"
        with self.assertRaisesRegex(DaydreamError, "portfolio:other"):
            self._run(
                idea=raw,
                expect_portfolio=("Ladder Drop", "other", "Anti-generic signature"),
            )

    def test_unfinalized_goal_is_rejected(self):
        with self.assertRaisesRegex(DaydreamError, "did not finalize its Daydream Goal"):
            self._run(idea=sample_idea_dict(), finalize=False)
        with self.assertRaisesRegex(DaydreamError, "do not match agent-outcome.json"):
            self._run(daydream_id=SECOND_ID, idea=sample_idea_dict(), outcome_sha256="0" * 64)
        self.assertEqual(list_daydreams("sample"), ())

    def test_missing_idea_file_fails(self):
        with self.assertRaisesRegex(DaydreamError, "did not finalize its Daydream Goal"):
            self._run()
        self.assertEqual(list_daydreams("sample"), ())

    def test_daydream_without_a_verified_live_search_event_fails_closed(self):
        with self.assertRaisesRegex(DaydreamError, "no verified live web-search"):
            self._run(idea=sample_idea_dict(), used_web_search=False)
        paths = daydream_paths("sample", FIRST_ID)
        self.assertFalse((paths.host_state / "IDEA.json").exists())
        self.assertEqual(list_daydreams("sample"), ())

    def test_invalid_json_and_invalid_schema_fail(self):
        with self.assertRaisesRegex(DaydreamError, "not valid UTF-8 JSON"):
            self._run(idea="{not json")
        raw = sample_idea_dict()
        del raw["keywords"]
        with self.assertRaisesRegex(DaydreamError, "keywords"):
            self._run(daydream_id=SECOND_ID, idea=raw)
        with self.assertRaisesRegex(DaydreamError, "JSON object"):
            self._run(daydream_id="daydream-20260902-101700-00000003", idea="[1]")

    def test_thesis_time_and_taste_citations_must_match_exact_inputs(self):
        raw = sample_idea_dict()
        raw["opportunity"]["world_scan"]["observed_at"] = "2026-09-02T10:14:59Z"
        with self.assertRaisesRegex(DaydreamError, "exact turn time"):
            self._run(idea=raw)
        raw = sample_idea_dict()
        raw["taste_fit"]["honors"] = ["A plausible paraphrase is not an exact citation"]
        with self.assertRaisesRegex(DaydreamError, "not exact excerpts"):
            self._run(daydream_id=SECOND_ID, idea=raw)

    def test_too_close_idea_is_rejected_and_remembered(self):
        catalog = horn_tip_catalog(Path(self._temporary.name).resolve() / "checkout")
        with self.assertRaisesRegex(DaydreamError, "Horn Tip"):
            self._run(idea=horn_tip_paraphrase_dict(), repository_root=catalog)
        paths = daydream_paths("sample", FIRST_ID)
        self.assertFalse((paths.host_state / "IDEA.json").exists())
        rejected = json.loads((paths.host_state / "REJECTED.json").read_text(encoding="utf-8"))
        self.assertEqual(rejected["novelty"]["status"], "too-close")
        self.assertEqual(rejected["idea"]["title"], "Crescent Rocker")
        entries = list_daydreams("sample")
        self.assertEqual(
            [(entry.title, entry.status) for entry in entries],
            [("Crescent Rocker", "rejected")],
        )
        with self.assertRaisesRegex(DaydreamError, "rejected"):
            load_sealed_daydream("sample", FIRST_ID)

    def test_launcher_failures_become_daydream_errors(self):
        with self.assertRaisesRegex(DaydreamError, "fixture disconnect"):
            self._run(error=NativeManagerInvocationError("fixture disconnect"))
        with self.assertRaisesRegex(DaydreamError, "fixture contract"):
            self._run(daydream_id=SECOND_ID, error=ContractError("fixture contract"))

        def broken_factory(manager_id, **kwargs):
            raise ContractError("Workshop Manager Codex is not executable")

        with self.assertRaisesRegex(DaydreamError, "not executable"):
            run_daydream(
                "sample",
                source_root=self.source_root,
                repository_root=self.catalog,
                launcher_factory=broken_factory,
                seed=SEED,
                moment=MOMENT,
                daydream_id="daydream-20260902-101700-00000003",
            )

    def test_codex_failures_become_daydream_errors(self):
        with self.assertRaisesRegex(DaydreamError, "not installed"):
            self._run(error=CodexInvocationError("Codex CLI is not installed or on PATH"))
        with self.assertRaisesRegex(DaydreamError, "timed out"):
            self._run(
                daydream_id=SECOND_ID,
                error=CodexRecoverableInvocationError("Codex native session timed out"),
            )

    def test_recoverable_failure_without_search_proof_fails_closed(self):
        for index, error in enumerate(
            (
                CodexRecoverableInvocationError("terminal event missing"),
                NativeManagerRecoverableError("provider disconnect"),
            )
        ):
            daydream_id = "daydream-20260902-1018%02d-%08x" % (index, index + 7)
            with self.assertRaisesRegex(DaydreamError, "no verified live web-search"):
                self._run(
                    daydream_id=daydream_id,
                    idea=sample_idea_dict(),
                    error=error,
                    error_after_idea=True,
                )
            self.assertEqual(list_daydreams("sample"), ())

    def test_overlapping_daydream_by_the_same_inventor_cannot_seal_a_repeat(self):
        test = self
        inner_factory, _ = self._factory(idea=sample_idea_dict())

        class _Nesting(_FakeLauncher):
            def start(self, **arguments):
                run_daydream(
                    "sample",
                    source_root=test.source_root,
                    repository_root=test.catalog,
                    launcher_factory=inner_factory,
                    seed=SEED,
                    moment=MOMENT,
                    daydream_id=SECOND_ID,
                )
                return super().start(**arguments)

        def factory(manager_id, **kwargs):
            return _Nesting(test, **kwargs, idea=sample_idea_dict())

        with self.assertRaisesRegex(DaydreamError, "Ladder Drop"):
            run_daydream(
                "sample",
                source_root=self.source_root,
                repository_root=self.catalog,
                launcher_factory=factory,
                seed=SEED,
                moment=MOMENT,
                daydream_id=FIRST_ID,
            )
        self.assertEqual(
            [(entry.daydream_id, entry.status) for entry in list_daydreams("sample")],
            [(SECOND_ID, "dreamed"), (FIRST_ID, "rejected")],
        )

    def test_work_directory_replaced_by_a_symlink_is_rejected(self):
        test = self
        elsewhere = Path(self._temporary.name).resolve() / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "IDEA.json").write_text(json.dumps(sample_idea_dict()), encoding="utf-8")

        class _Swapping(_FakeLauncher):
            def start(self, **arguments):
                outcome = super().start(**arguments)
                work = Path(arguments["run_root"]) / "work"
                work.rmdir()
                work.symlink_to(elsewhere)
                return outcome

        def factory(manager_id, **kwargs):
            return _Swapping(test, **kwargs)

        with self.assertRaisesRegex(DaydreamError, "work directory"):
            run_daydream(
                "sample",
                source_root=self.source_root,
                repository_root=self.catalog,
                launcher_factory=factory,
                seed=SEED,
                moment=MOMENT,
                daydream_id=FIRST_ID,
            )
        self.assertEqual(list_daydreams("sample"), ())

    def test_judge_verdict_is_sealed_and_a_dream_again_is_remembered_as_judged(self):
        sealed, launchers = self._run(idea=sample_idea_dict())
        self.assertEqual(sealed.verdict.decision, "build")
        self.assertEqual(len(launchers), 2)
        judge_manager, judge_kwargs, _ = launchers[1]
        self.assertEqual(judge_manager, "codex")
        self.assertEqual(judge_kwargs["timeout_seconds"], 600)
        paths = daydream_paths("sample", FIRST_ID)
        verdict_record = json.loads((paths.host_state / "VERDICT.json").read_text(encoding="utf-8"))
        self.assertEqual(verdict_record["verdict"]["decision"], "build")
        self.assertEqual(load_sealed_daydream("sample", FIRST_ID), sealed)
        self.assertEqual([entry.status for entry in list_daydreams("sample")], ["dreamed"])

        raw = sample_idea_dict()
        raw["title"] = "Turn Pact"
        raw["one_liner"] = "Two players rotate paired dials and try to reveal the same hidden window."
        raw["experience"]["action"] = "Each player rotates one dial without seeing the other dial."
        raw["experience"]["response"] = "The paired shutters reveal one of several shared windows."
        raw["experience"]["payoff"] = "Matching windows create a simultaneous tactile click."
        raw["experience"]["anti_generic_signature"] = (
            "Two blind rotations resolve as one visible window and one shared click."
        )
        raw["keywords"] = ["paired-dials", "shutters", "matching", "shared-click"]
        sealed, _ = self._run(
            daydream_id=SECOND_ID, idea=raw, verdict="dream-again"
        )
        self.assertEqual(sealed.verdict.decision, "dream-again")
        self.assertEqual(sealed.verdict.risks[0].kind, "proof-mismatch")
        self.assertEqual(
            [entry.status for entry in list_daydreams("sample")], ["dreamed", "judged"]
        )
        # A judged-out idea is still sealed, so it can be built on purpose.
        self.assertEqual(load_sealed_daydream("sample", SECOND_ID).verdict.decision, "dream-again")

    def test_judge_repair_advice_reaches_the_next_daydream_workspace(self):
        rejected, _launchers = self._run(
            idea=sample_idea_dict(), verdict="dream-again"
        )
        self.assertEqual(rejected.verdict.decision, "dream-again")
        raw = sample_idea_dict()
        raw["title"] = "Rung Chorus"
        raw["one_liner"] = "Tilt a pocket rail and hear captive beads answer in a staggered rhythm."
        raw["experience"]["action"] = "Tilt the rail through one slow quarter turn."
        raw["experience"]["response"] = "Three captive beads release at visibly different thresholds."
        raw["experience"]["payoff"] = "Their separated catches compose a repeatable three-beat answer."
        raw["experience"]["anti_generic_signature"] = (
            "One tilt produces three visibly separated releases and three distinct catches."
        )
        raw["keywords"] = ["rail", "beads", "tilt", "rhythm"]
        self._run(
            daydream_id=SECOND_ID,
            idea=raw,
            expect_notebook=(
                "Judge prediction: dream-again",
                "proof_observable",
                "make the unequal catch sequence independently observable",
            ),
        )

    def test_judge_can_be_skipped_and_its_failures_fail_closed(self):
        sealed, launchers = self._run(idea=sample_idea_dict(), judge=False)
        self.assertIsNone(sealed.verdict)
        self.assertEqual(len(launchers), 1)
        daydream_paths("sample", FIRST_ID).notebook.unlink()
        with self.assertRaisesRegex(DaydreamError, "did not finalize its Judge Goal"):
            self._run(daydream_id=SECOND_ID, idea=sample_idea_dict(), verdict=None)
        with self.assertRaisesRegex(DaydreamError, "Judge session failed"):
            self._run(
                daydream_id="daydream-20260902-101700-00000003",
                idea=sample_idea_dict(),
                judge_error=NativeManagerInvocationError("judge disconnect"),
            )
        self.assertEqual(list_daydreams("sample"), ())

    def test_unknown_inventor_and_manager_fail_before_any_state_exists(self):
        with self.assertRaisesRegex(DaydreamError, "unknown Inventor: nobody \\(known: sample\\)"):
            resolve_inventor("nobody", source_root=self.source_root)
        factory, launchers = self._factory(idea=sample_idea_dict())
        with self.assertRaises(DaydreamError):
            run_daydream("nobody", source_root=self.source_root, launcher_factory=factory)
        with self.assertRaises(ContractError):
            run_daydream(
                "sample", source_root=self.source_root, manager_id="gpt", launcher_factory=factory
            )
        self.assertEqual(launchers, [])
        self.assertFalse((self.home / "daydreams").exists())

    def test_load_sealed_daydream_verifies_bytes(self):
        sealed, _launchers = self._run(idea=sample_idea_dict())
        path = daydream_paths("sample", FIRST_ID).host_state / "IDEA.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw["idea"]["title"] = "Tampered"
        path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(DaydreamError, "invalid"):
            load_sealed_daydream("sample", FIRST_ID)
        daydream_paths("sample", SECOND_ID, create=True)
        with self.assertRaisesRegex(DaydreamError, "no sealed idea"):
            load_sealed_daydream("sample", SECOND_ID)
        self.assertNotEqual(sealed.idea.title, "Tampered")

    def test_wish_from_daydream_carries_the_brief_and_provenance(self):
        sealed, _launchers = self._run(idea=sample_idea_dict())
        wish = wish_from_daydream(sealed)
        self.assertRegex(wish.product_id, r"^wish-\d{8}-\d{6}-[0-9a-f]{8}$")
        self.assertEqual(wish.objective, sealed.brief)
        self.assertEqual(
            wish.context,
            {
                "source": "workshop-daydream",
                "inventor_id": "sample",
                "daydream_id": FIRST_ID,
                "daydream_sha256": sealed.sha256,
                "idea_sha256": sealed.idea_sha256,
                "provenance_sha256": sealed.provenance.sha256,
                "route": "spark",
                "title": "Ladder Drop",
            },
        )
        self.assertEqual(wish.constraints, {})
        pinned = wish_from_daydream(sealed, wish_id="wish-20260902-101500-0badcafe")
        self.assertEqual(pinned.product_id, "wish-20260902-101500-0badcafe")
        with self.assertRaises(ContractError):
            wish_from_daydream(sealed.to_dict())

    def test_paths_are_private_and_created_once(self):
        paths = daydream_paths("sample", FIRST_ID, create=True)
        for path in (paths.container, paths.workspace, paths.work, paths.host_state):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700)
        self.assertEqual(paths.work, paths.workspace / "work")
        self.assertEqual(paths.notebook, self.home / "daydreams" / "sample" / "NOTEBOOK.jsonl")
        self.assertEqual(daydream_paths("sample", FIRST_ID), paths)
        with self.assertRaisesRegex(DaydreamError, "already exists"):
            daydream_paths("sample", FIRST_ID, create=True)
        with self.assertRaises(DaydreamError):
            daydream_paths("sample", SECOND_ID)
        with self.assertRaises(ContractError):
            daydream_paths("Sample", FIRST_ID)
        with self.assertRaises(ContractError):
            daydream_paths("sample", "wish-20260902-101500-00000001")
        self.assertEqual(list_daydreams("other"), ())

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_symlinked_container_is_rejected(self):
        folder = self.home / "daydreams" / "sample"
        folder.mkdir(parents=True, mode=0o700)
        (self.home / "daydreams").chmod(0o700)
        elsewhere = Path(self._temporary.name).resolve() / "elsewhere"
        elsewhere.mkdir(mode=0o700)
        os.symlink(elsewhere, folder / FIRST_ID)
        with self.assertRaisesRegex(DaydreamError, "already exists"):
            daydream_paths("sample", FIRST_ID, create=True)
        with self.assertRaises(DaydreamError):
            daydream_paths("sample", FIRST_ID)
        factory, _launchers = self._factory(idea=sample_idea_dict())
        with self.assertRaises(DaydreamError):
            run_daydream(
                "sample",
                source_root=self.source_root,
                repository_root=self.catalog,
                launcher_factory=factory,
                daydream_id=FIRST_ID,
            )


if __name__ == "__main__":
    unittest.main()
