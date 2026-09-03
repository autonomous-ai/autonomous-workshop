import hashlib
import json
import os
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tests.daydream.support import (
    horn_tip_catalog,
    horn_tip_paraphrase_dict,
    inventor_bundle,
    sample_idea_dict,
)
from workshop.daydream.contracts import DaydreamError, Idea, SealedDaydream
from workshop.daydream.native import (
    DAYDREAM_TURN_TIMEOUT_SECONDS,
    daydream_paths,
    list_daydreams,
    load_sealed_daydream,
    resolve_inventor,
    run_daydream,
    wish_from_daydream,
)
from workshop.daydream.prompt import DAYDREAM_CONSTITUTION, DAYDREAM_CONSTITUTION_SHA256
from workshop.daydream.seeds import DaydreamSeed
from workshop.errors import ContractError
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
    def __init__(self, arguments):
        self.arguments = arguments

    def to_dict(self):
        return {
            "status": "completed",
            "used_web_search": True,
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
        error_after_idea=False,
        finalize=True,
        outcome_sha256=None,
    ):
        self.test = test
        self.error_after_idea = error_after_idea
        self.finalize = finalize
        self.outcome_sha256 = outcome_sha256
        self.timeout_seconds = timeout_seconds
        self.idea = idea
        self.error = error
        self.expect_notebook = expect_notebook
        self.starts = []

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        run_root = Path(arguments["run_root"])
        host_state = Path(arguments["host_state_root"])
        for name in (
            "TASTE.md",
            "PRIOR-WORK.md",
            "NOTEBOOK.md",
            "AGENTS.md",
            "finalize_daydream.py",
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
        self.test.assertEqual(stat.S_IMODE(host_state.stat().st_mode), 0o700)
        self.test.assertEqual(stat.S_IMODE(run_root.stat().st_mode), 0o700)
        self.test.assertFalse(host_state.is_relative_to(run_root))
        notebook = (run_root / "NOTEBOOK.md").read_text(encoding="utf-8")
        for expected in self.expect_notebook:
            self.test.assertIn(expected, notebook)
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
        )
        return sealed, launchers

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
        entries = list_daydreams("sample")
        self.assertEqual(
            [(entry.daydream_id, entry.status) for entry in entries],
            [(FIRST_ID, "dreamed")],
        )
        self.assertEqual(entries[0].idea_sha256, sealed.idea_sha256)
        self.assertEqual(load_sealed_daydream("sample", FIRST_ID), sealed)

    def test_second_daydream_sees_the_first_and_may_not_repeat_it(self):
        self._run(idea=sample_idea_dict())
        raw = sample_idea_dict()
        raw["title"] = "Rung Counter"
        raw["one_liner"] = (
            "Tap a printed column and count the taps by how far a captive pin has climbed."
        )
        raw["what_you_do"] = "Tap the top of the column once per event you want to count."
        raw["what_happens"] = (
            "Each tap ratchets a captive pin one notch higher; a twist lets it fall "
            "back to zero."
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

    def test_invalid_json_and_invalid_schema_fail(self):
        with self.assertRaisesRegex(DaydreamError, "not valid UTF-8 JSON"):
            self._run(idea="{not json")
        raw = sample_idea_dict()
        del raw["keywords"]
        with self.assertRaisesRegex(DaydreamError, "keywords"):
            self._run(daydream_id=SECOND_ID, idea=raw)
        with self.assertRaisesRegex(DaydreamError, "JSON object"):
            self._run(daydream_id="daydream-20260902-101700-00000003", idea="[1]")

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

    def test_recoverable_failure_after_a_written_idea_is_kept_as_incomplete(self):
        for index, error in enumerate(
            (
                CodexRecoverableInvocationError("terminal event missing"),
                NativeManagerRecoverableError("provider disconnect"),
            )
        ):
            daydream_id = "daydream-20260902-1018%02d-%08x" % (index, index + 7)
            sealed, launchers = self._run(
                daydream_id=daydream_id,
                idea=sample_idea_dict(),
                error=error,
                error_after_idea=True,
            )
            self.assertEqual(sealed.session, {"status": "incomplete", "error": str(error)})
            self.assertEqual(sealed.idea.title, "Ladder Drop")
            self.assertEqual(load_sealed_daydream("sample", daydream_id), sealed)
            paths = daydream_paths("sample", daydream_id)
            (paths.host_state / "IDEA.json").unlink()
            # The second loop iteration must not see the first as prior work.
            paths.notebook.unlink()

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
                "idea_sha256": sealed.idea_sha256,
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
