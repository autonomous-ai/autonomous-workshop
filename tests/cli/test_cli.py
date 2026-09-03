import json
import importlib
import os
import stat
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from cli.main import main, parser
from workshop.runtime.progress import WishRunTimingEvent
from workshop.daydream import DaydreamError

from tests.daydream.support import sample_sealed, sample_verdict


cli_main = importlib.import_module("cli.main")


def native_receipt(*, status="waiting", stage="match", published=False, progress=None):
    receipt = {
        "schema_version": 1,
        "kind": "native-agent-run",
        "product_id": "wish-one",
        "status": status,
        "stage": stage,
        "publication": {
            "status": "public" if published else "not-created",
            "requested": True,
            "required": True,
        },
    }
    if progress is not None:
        receipt["progress"] = progress
    return receipt


def timing_event(*, state="started", elapsed_ms=None, operation="session.start"):
    return WishRunTimingEvent(
        observed_at="2026-08-27T03:14:15.926Z",
        product_id="wish-one",
        stage="match",
        operation=operation,
        state=state,
        elapsed_ms=elapsed_ms,
    )


class NativeCommandTest(unittest.TestCase):
    def test_surface_contains_only_the_lean_supported_commands(self):
        command = parser()
        subparsers = next(
            action
            for action in command._actions
            if action.__class__.__name__ == "_SubParsersAction"
        )
        self.assertEqual(
            set(subparsers.choices),
            {
                "start",
                "stop",
                "daydream",
                "wish",
                "status",
                "resume",
                "doctor",
                "inventors",
                "create",
                "check",
                "seal",
                "pack",
                "plan-pack",
                "skills",
                "schemas",
                "vault",
            },
        )
        for removed in (
            "registry",
            "artifact",
            "clockwork",
            "init-state",
            "audit-state",
            "new",
        ):
            with self.subTest(command=removed), redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                command.parse_args((removed,))

    def test_removed_execution_and_profile_options_are_rejected(self):
        command = parser()
        for arguments in (
            ("wish", "a moon", "--root", "/tmp/legacy"),
            ("resume", "wish-one", "--root", "/tmp/legacy"),
            ("inventors", "--check-entrypoints"),
            ("create", "inventor", "mira", "--level", "taste-only"),
            ("create", "inventor", "mira", "--template", "custom"),
            ("create", "inventor", "mira", "--run-checks"),
            (
                "create",
                "inventor",
                "mira",
                "--description",
                "specific physical playthings",
                "--lane",
                "little-worlds",
            ),
            ("check", ".", "--run"),
            ("wish", "a moon", "--draft"),
            ("wish", "a moon", "--publish"),
            ("resume", "wish-one", "--publish"),
        ):
            with self.subTest(arguments=arguments), redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                command.parse_args(arguments)

    def test_main_has_no_legacy_orchestration_entrypoints(self):
        for name in (
            "CodexSemanticManager",
            "WorkshopManager",
            "Clockwork",
            "_run_inventor",
            "_resume_factory_release",
            "_promote_factory_intent",
            "_publish_inventor_draft",
            "_ReadOnlyWorkshopStore",
        ):
            self.assertFalse(hasattr(cli_main, name), name)

    def test_wish_calls_only_native_start_and_keeps_json_stdout_clean(self):
        observed = {}

        def start(
            wish,
            *,
            effort,
            manager_id,
            max_rounds,
            github_publish_requested,
            activity_observer,
            timing_observer,
        ):
            observed["wish"] = wish
            observed["effort"] = effort
            observed["manager_id"] = manager_id
            observed["github_publish_requested"] = github_publish_requested
            timing_observer(timing_event())
            for activity in (
                "starting",
                "reasoning",
                "running",
                "running",
                "tool",
                "tool",
                "completed",
            ):
                activity_observer(activity)
            timing_observer(
                timing_event(state="completed", elapsed_ms=2_375)
            )
            return native_receipt()

        stdout = StringIO()
        stderr = StringIO()
        with mock.patch("cli.main.generate_wish_id", return_value="wish-one"), mock.patch(
            "cli.main.start_native_run", side_effect=start
        ) as native_start, mock.patch(
            "cli.main.time.monotonic",
            side_effect=(100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0),
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(("wish", "a", "moon", "that", "waddles", "--json"))

        self.assertEqual(result, 0)
        self.assertEqual(json.loads(stdout.getvalue())["stage"], "match")
        self.assertIn("Starting one native Codex session", stderr.getvalue())
        self.assertEqual(observed["manager_id"], "codex")
        self.assertIn("reasoning about the current stage", stderr.getvalue())
        self.assertIn("process is still running", stderr.getvalue())
        self.assertIn("using a tool for the current stage", stderr.getvalue())
        self.assertIn("turn complete; Workshop is verifying it", stderr.getvalue())
        self.assertIn(
            "[2026-08-27T03:14:15.926Z] wish=wish-one stage=match "
            "operation=session.start state=started",
            stderr.getvalue(),
        )
        self.assertIn("state=completed elapsed_ms=2375", stderr.getvalue())
        self.assertNotIn("a moon that waddles", stderr.getvalue())
        self.assertEqual(stderr.getvalue().count("process is still running"), 1)
        self.assertEqual(stderr.getvalue().count("using a tool"), 1)
        self.assertEqual(observed["wish"].objective, "a moon that waddles")
        self.assertEqual(observed["wish"].context, {"source": "workshop-cli"})
        self.assertEqual(observed["effort"], "spark")
        self.assertFalse(observed["github_publish_requested"])
        self.assertIn("Effort: Spark", stderr.getvalue())
        native_start.assert_called_once()

    def test_wish_strict_wait_exits_one_without_a_publication_flag(self):
        stdout = StringIO()
        with mock.patch("cli.main.generate_wish_id", return_value="wish-one"), mock.patch(
            "cli.main.start_native_run", return_value=native_receipt()
        ) as start, redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("wish", "a moon", "--strict", "--json"))
        self.assertEqual(result, 1)
        start.assert_called_once()

    def test_human_wish_timing_uses_stdout_and_flushes(self):
        def start(
            wish,
            *,
            effort,
            manager_id,
            max_rounds,
            github_publish_requested,
            activity_observer,
            timing_observer,
        ):
            self.assertEqual(effort, "spark")
            self.assertEqual(manager_id, "codex")
            self.assertFalse(github_publish_requested)
            del wish, activity_observer
            timing_observer(timing_event(operation="stage.prepare"))
            timing_observer(
                timing_event(
                    operation="stage.prepare",
                    state="completed",
                    elapsed_ms=42,
                )
            )
            return native_receipt()

        stdout = StringIO()
        stderr = StringIO()
        with mock.patch(
            "cli.main.generate_wish_id", return_value="wish-one"
        ), mock.patch(
            "cli.main.start_native_run", side_effect=start
        ), mock.patch.object(
            stdout, "flush", wraps=stdout.flush
        ) as flush, redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(("wish", "private human objective"))

        self.assertEqual(result, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("operation=stage.prepare state=started", stdout.getvalue())
        self.assertIn("state=completed elapsed_ms=42", stdout.getvalue())
        self.assertNotIn("private human objective", stdout.getvalue())
        self.assertGreaterEqual(flush.call_count, 2)

    def test_wish_passes_each_named_effort_to_the_native_host(self):
        for effort in ("spark", "forge", "quest"):
            with self.subTest(effort=effort), mock.patch(
                "cli.main.generate_wish_id", return_value="wish-" + effort
            ), mock.patch(
                "cli.main.start_native_run", return_value=native_receipt()
            ) as start, redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                result = main(
                    ("wish", "a moon", "--effort", effort, "--json")
                )
            self.assertEqual(result, 0)
            self.assertEqual(start.call_args.kwargs["effort"], effort)
            self.assertEqual(start.call_args.kwargs["manager_id"], "codex")

    def test_wish_passes_named_manager_to_the_native_host(self):
        with mock.patch(
            "cli.main.generate_wish_id", return_value="wish-grok"
        ), mock.patch(
            "cli.main.start_native_run", return_value=native_receipt()
        ) as start, redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            result = main(("wish", "a moon", "--manager", "grok", "--json"))
        self.assertEqual(result, 0)
        self.assertEqual(start.call_args.kwargs["manager_id"], "grok")

    def test_wish_passes_round_budget_to_the_native_host(self):
        with mock.patch(
            "cli.main.generate_wish_id", return_value="wish-rounds"
        ), mock.patch(
            "cli.main.start_native_run", return_value=native_receipt()
        ) as start, redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            result = main(("wish", "a moon", "--max-rounds", "8", "--json"))
        self.assertEqual(result, 0)
        self.assertEqual(start.call_args.kwargs["max_rounds"], 8)

    def test_wish_defaults_the_round_budget_to_four(self):
        with mock.patch(
            "cli.main.generate_wish_id", return_value="wish-default-rounds"
        ), mock.patch(
            "cli.main.start_native_run", return_value=native_receipt()
        ) as start, redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            result = main(("wish", "a moon", "--json"))
        self.assertEqual(result, 0)
        self.assertEqual(start.call_args.kwargs["max_rounds"], 4)

    def test_wish_rejects_an_out_of_range_round_budget(self):
        for value in ("0", "101", "four"):
            with self.subTest(value=value), mock.patch(
                "cli.main.start_native_run", return_value=native_receipt()
            ) as start, redirect_stdout(StringIO()), redirect_stderr(
                StringIO()
            ), self.assertRaises(SystemExit) as caught:
                main(("wish", "a moon", "--max-rounds", value, "--json"))
            self.assertEqual(caught.exception.code, 2)
            start.assert_not_called()

    def test_live_native_activity_repeats_only_throttled_running_updates(self):
        output = StringIO()
        progress = cli_main._LiveWishProgress(output)
        with mock.patch(
            "cli.main.time.monotonic",
            side_effect=(100.0, 129.9, 130.0),
        ):
            progress.activity("running")
            progress.activity("running")
            progress.activity("running")

        self.assertEqual(output.getvalue().count("process is still running"), 2)

    def test_live_native_activity_rate_limits_high_churn_classes(self):
        output = StringIO()
        progress = cli_main._LiveWishProgress(output)
        with mock.patch(
            "cli.main.time.monotonic",
            side_effect=(100.0, 100.5, 102.0),
        ):
            progress.activity("reasoning")
            progress.activity("tool")
            progress.activity("tool")

        self.assertEqual(output.getvalue().count("reasoning"), 1)
        self.assertEqual(output.getvalue().count("using a tool"), 1)

    def test_failed_activity_neutrally_reports_proposal_check(self):
        output = StringIO()
        cli_main._LiveWishProgress(output).activity("failed")

        self.assertIn("checking for a valid stage proposal", output.getvalue())
        self.assertNotIn("turn stopped", output.getvalue())

    def test_status_is_read_only_native_inspection(self):
        stdout = StringIO()
        with mock.patch(
            "cli.main.native_run_status", return_value=native_receipt(status="active")
        ) as status, redirect_stdout(stdout):
            result = main(("status", "wish-one", "--json"))
        self.assertEqual(result, 0)
        status.assert_called_once_with("wish-one")
        self.assertEqual(json.loads(stdout.getvalue())["product_id"], "wish-one")

    def test_status_text_shows_only_safe_progress_metadata(self):
        stdout = StringIO()
        progress = {
            "status": "available",
            "stage_attempt": {"stage": "make", "number": 2},
            "activity": "tool",
            "elapsed_seconds": 73,
            "last_activity_at": "2026-08-26T15:00:00.000Z",
        }
        with mock.patch(
            "cli.main.native_run_status",
            return_value=native_receipt(
                status="active", stage="make", progress=progress
            ),
        ), redirect_stdout(stdout):
            result = main(("status", "wish-one"))

        self.assertEqual(result, 0)
        self.assertIn(
            "Progress: Make attempt 2 — tool (73s; last activity "
            "2026-08-26T15:00:00.000Z)",
            stdout.getvalue(),
        )

    def test_status_text_prints_one_line_per_scored_round(self):
        stdout = StringIO()
        receipt = native_receipt(status="active", stage="make")
        receipt["rounds"] = [
            {"round": 1, "verdict": "block", "score_median": {"play": 8, "wish_fit": 7.5},
             "score_spread": {"play": 1, "wish_fit": 4}},
            {"round": 2, "verdict": "pass", "score_median": None, "score_spread": None},
            "not a mapping",
        ]
        with mock.patch("cli.main.native_run_status", return_value=receipt), redirect_stdout(stdout):
            self.assertEqual(main(("status", "wish-one")), 0)
        text = stdout.getvalue()
        self.assertIn("Round 1: block — play 8 wish_fit 7.5 (readers disagree on wish_fit)", text)
        self.assertIn("Round 2: pass — unscored", text)

    def test_status_text_surfaces_actionable_publication_need(self):
        stdout = StringIO()
        receipt = native_receipt(status="waiting", stage="release")
        reason = (
            "Factory credentials are missing; configure them, then resume this run."
        )
        receipt["publication"] = {
            "status": "not-created",
            "requested": True,
            "reason": reason,
        }
        receipt["needs"] = [reason, "Manufacturing remains separately authorized."]
        with mock.patch(
            "cli.main.native_run_status", return_value=receipt
        ), redirect_stdout(stdout):
            result = main(("status", "wish-one"))

        self.assertEqual(result, 0)
        output = stdout.getvalue()
        self.assertIn("Publication note: %s" % reason, output)
        self.assertEqual(output.count(reason), 1)
        self.assertIn("Need: Manufacturing remains separately authorized.", output)

    def test_status_text_surfaces_hash_verified_manual_url(self):
        stdout = StringIO()
        receipt = native_receipt(status="complete", stage="release")
        receipt["publication"] = {
            "status": "public",
            "requested": True,
            "verified": True,
            "page_url": "https://www.autonomous.ai/factory/product/moon-toy",
            "manual_url": (
                "https://cdn.autonomous.ai/projects/history-1/MANUAL.pdf"
            ),
        }

        with mock.patch(
            "cli.main.native_run_status", return_value=receipt
        ), redirect_stdout(stdout):
            result = main(("status", "wish-one"))

        self.assertEqual(result, 0)
        self.assertIn(
            "Manual PDF: https://cdn.autonomous.ai/projects/history-1/"
            "MANUAL.pdf (hash-verified)",
            stdout.getvalue(),
        )

    def test_resume_calls_only_native_resume_and_has_strict_wait_policy(self):
        def resume_run(product_id, *, activity_observer, timing_observer):
            timing_observer(timing_event(operation="session.resume"))
            activity_observer("tool")
            timing_observer(
                timing_event(
                    operation="session.resume",
                    state="completed",
                    elapsed_ms=911,
                )
            )
            return native_receipt(stage="make")

        stdout = StringIO()
        stderr = StringIO()
        with mock.patch(
            "cli.main.resume_native_run", side_effect=resume_run
        ) as resume, redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(("resume", "wish-one", "--strict", "--json"))
        self.assertEqual(result, 1)
        resume.assert_called_once()
        self.assertEqual(resume.call_args.args, ("wish-one",))
        self.assertTrue(callable(resume.call_args.kwargs["activity_observer"]))
        self.assertTrue(callable(resume.call_args.kwargs["timing_observer"]))
        self.assertEqual(json.loads(stdout.getvalue())["stage"], "make")
        self.assertIn("exact native Codex session", stderr.getvalue())
        self.assertIn("using a tool for the current stage", stderr.getvalue())
        self.assertIn("operation=session.resume state=started", stderr.getvalue())
        self.assertIn("state=completed elapsed_ms=911", stderr.getvalue())

    def test_failed_native_run_exits_one_even_without_strict(self):
        with mock.patch("cli.main.generate_wish_id", return_value="wish-one"), mock.patch(
            "cli.main.start_native_run",
            return_value=native_receipt(status="failed", stage="playtest"),
        ), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(main(("wish", "a moon")), 1)

    def test_github_publication_is_explicit_and_forwarded(self):
        with mock.patch(
            "cli.main.generate_wish_id", return_value="wish-one"
        ), mock.patch(
            "cli.main.start_native_run", return_value=native_receipt()
        ) as start, redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(main(("wish", "--github", "a moon")), 0)
        self.assertTrue(start.call_args.kwargs["github_publish_requested"])

    def test_legacy_publication_flags_are_not_part_of_the_core_cli(self):
        command = parser()
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            command.parse_args(("wish", "a moon", "--publish"))
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            command.parse_args(("resume", "wish-one", "--publish"))


class DaydreamCommandTest(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        self.home = Path(self._temporary.name).resolve() / "home"
        environment = mock.patch.dict(os.environ, {"WORKSHOP_HOME": str(self.home)})
        environment.start()
        self.addCleanup(environment.stop)
        self._with_credentials()

    def _loop_folder(self):
        return self.home / "daydreams" / "sample"

    def _with_credentials(self):
        ready = mock.patch("cli.main._publishing_account_ready", return_value=True)
        ready.start()
        self.addCleanup(ready.stop)

    def test_parser_defaults(self):
        args = parser().parse_args(("start", "pico-press"))
        self.assertEqual(args.inventor, "pico-press")
        self.assertEqual(args.effort, "spark")
        self.assertEqual(args.manager, "codex")
        self.assertIsNone(args.idea)
        self.assertFalse(args.json)
        self.assertFalse(args.strict)
        self.assertFalse(args.github)
        self.assertFalse(args.once)
        self.assertIsNone(args.max_ideas)
        self.assertEqual(args.max_failures, 3)
        stop = parser().parse_args(("stop", "pico-press", "--now"))
        self.assertTrue(stop.now)
        args = parser().parse_args(("daydream", "pico-press"))
        self.assertEqual(args.manager, "codex")
        self.assertIsNone(args.idea)
        for arguments in (
            ("daydream", "pico-press", "--run"),
            ("daydream", "pico-press", "--effort", "spark"),
            ("daydream", "pico-press", "--strict"),
            ("start", "pico-press", "--run"),
        ):
            with self.subTest(arguments=arguments), redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                parser().parse_args(arguments)

    def test_daydream_prints_the_card_and_never_starts_a_run(self):
        sealed = sample_sealed()
        observed = {}

        def dream(inventor_id, *, source_root, manager_id, activity_observer, effort):
            observed["inventor_id"] = inventor_id
            observed["source_root"] = source_root
            observed["manager_id"] = manager_id
            observed["effort"] = effort
            activity_observer("starting")
            activity_observer("completed")
            return sealed

        stdout = StringIO()
        stderr = StringIO()
        with mock.patch("cli.main.run_daydream", side_effect=dream) as run, mock.patch(
            "cli.main.start_native_run"
        ) as start, redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(("daydream", "sample"))

        self.assertEqual(result, 0)
        run.assert_called_once()
        start.assert_not_called()
        self.assertEqual(observed["inventor_id"], "sample")
        self.assertEqual(observed["manager_id"], "codex")
        self.assertIsNone(observed["effort"])
        self.assertTrue(Path(observed["source_root"]).is_dir())
        output = stdout.getvalue()
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("Daydreaming one brand-new idea", output)
        self.assertIn("starting the current stage", output)
        self.assertIn("Daydream: %s" % sealed.daydream_id, output)
        self.assertIn("Title: Ladder Drop", output)
        self.assertIn("What it looks like: A palm-sized", output)
        self.assertIn("Closest existing things: Jacob's ladder", output)
        self.assertIn("Taste fit: honors Motion comes from geometry", output)
        self.assertIn("Printed parts: 2", output)
        self.assertIn("Novelty lint: new (no prior work to compare against)", output)
        self.assertIn(
            "workshop start sample --idea %s" % sealed.daydream_id, output
        )

    def test_daydream_json_emits_one_object_and_keeps_stdout_clean(self):
        sealed = sample_sealed()
        stdout = StringIO()
        stderr = StringIO()
        with mock.patch("cli.main.run_daydream", return_value=sealed), redirect_stdout(
            stdout
        ), redirect_stderr(stderr):
            result = main(("daydream", "sample", "--json"))
        self.assertEqual(result, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(set(payload), {"daydream"})
        self.assertEqual(payload["daydream"], sealed.to_dict())
        self.assertIn("Daydreaming", stderr.getvalue())
        self.assertNotIn("Title:", stderr.getvalue())

    def test_start_dreams_then_builds_from_the_sealed_brief(self):
        sealed = sample_sealed()
        observed = {}

        def start(
            wish,
            *,
            effort,
            manager_id,
            github_publish_requested,
            max_rounds,
            activity_observer,
            timing_observer,
        ):
            observed["wish"] = wish
            observed["effort"] = effort
            observed["manager_id"] = manager_id
            observed["github"] = github_publish_requested
            observed["max_rounds"] = max_rounds
            activity_observer("completed")
            timing_observer(timing_event())
            return native_receipt()

        stdout = StringIO()
        stderr = StringIO()
        with mock.patch("cli.main.run_daydream", return_value=sealed) as run, mock.patch(
            "workshop.daydream.native.generate_wish_id", return_value="wish-one"
        ), mock.patch(
            "cli.main.start_native_run", side_effect=start
        ) as native_start, redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(("start", "sample", "--once", "--json"))

        self.assertEqual(result, 0)
        run.assert_called_once()
        native_start.assert_called_once()
        self.assertEqual(run.call_args.kwargs["manager_id"], "codex")
        self.assertEqual(run.call_args.kwargs["effort"], "spark")
        wish = observed["wish"]
        self.assertEqual(wish.product_id, "wish-one")
        self.assertEqual(wish.objective, sealed.brief)
        self.assertEqual(wish.context["source"], "workshop-daydream")
        self.assertEqual(wish.context["daydream_id"], sealed.daydream_id)
        self.assertEqual(wish.context["idea_sha256"], sealed.idea_sha256)
        self.assertEqual(observed["effort"], "spark")
        self.assertEqual(observed["manager_id"], "codex")
        self.assertFalse(observed["github"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(set(payload), {"daydream", "run"})
        self.assertEqual(payload["run"]["stage"], "match")
        self.assertIn("Sealing the idea as this run's brief", stderr.getvalue())
        self.assertIn("Starting one native Codex session for Make", stderr.getvalue())
        self.assertNotIn(sealed.brief, stderr.getvalue())

    def test_start_passes_effort_manager_github_and_strict(self):
        sealed = sample_sealed()
        with mock.patch("cli.main.run_daydream", return_value=sealed) as run, mock.patch(
            "cli.main.start_native_run", return_value=native_receipt()
        ) as start, redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            result = main(
                (
                    "start",
                    "sample",
                    "--once",
                    "--effort",
                    "forge",
                    "--manager",
                    "grok",
                    "--github",
                    "--strict",
                )
            )
        self.assertEqual(result, 1)
        self.assertEqual(run.call_args.kwargs["manager_id"], "grok")
        self.assertEqual(run.call_args.kwargs["effort"], "forge")
        self.assertEqual(start.call_args.kwargs["effort"], "forge")
        self.assertEqual(start.call_args.kwargs["manager_id"], "grok")
        self.assertTrue(start.call_args.kwargs["github_publish_requested"])

    def test_start_with_a_saved_idea_never_redreams(self):
        sealed = sample_sealed()
        stdout = StringIO()
        with mock.patch(
            "cli.main.load_sealed_daydream", return_value=sealed
        ) as load, mock.patch("cli.main.run_daydream") as run, mock.patch(
            "cli.main.start_native_run", return_value=native_receipt()
        ) as start, redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("start", "sample", "--idea", sealed.daydream_id))
        self.assertEqual(result, 0)
        load.assert_called_once_with("sample", sealed.daydream_id)
        run.assert_not_called()
        start.assert_called_once()
        self.assertEqual(start.call_args.kwargs["effort"], "spark")
        self.assertIn("(saved idea)", stdout.getvalue())
        self.assertNotIn("Build it:", stdout.getvalue())
        self.assertIn("Wish: wish-", stdout.getvalue())

    def test_daydream_with_a_saved_idea_only_prints_it(self):
        sealed = sample_sealed()
        stdout = StringIO()
        with mock.patch(
            "cli.main.load_sealed_daydream", return_value=sealed
        ), mock.patch("cli.main.run_daydream") as run, mock.patch(
            "cli.main.start_native_run"
        ) as start, redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("daydream", "sample", "--idea", sealed.daydream_id))
        self.assertEqual(result, 0)
        run.assert_not_called()
        start.assert_not_called()
        self.assertIn("Title: Ladder Drop", stdout.getvalue())
        self.assertIn("Build it: workshop start sample --idea", stdout.getvalue())

    def test_loop_dreams_and_builds_until_workshop_stop(self):
        sealed = sample_sealed()
        calls = []

        def start(wish, **kwargs):
            calls.append(wish.product_id)
            if len(calls) == 2:
                (self._loop_folder() / "STOP").write_text("stop\n")
            return native_receipt(status="completed", stage="release", published=True)

        stdout = StringIO()
        with mock.patch("cli.main.run_daydream", return_value=sealed) as run, mock.patch(
            "cli.main.start_native_run", side_effect=start
        ), redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("start", "sample"))
        self.assertEqual(result, 0)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(len(calls), 2)
        output = stdout.getvalue()
        self.assertIn("Loop: sample dreams and builds until you stop it", output)
        self.assertIn("workshop stop sample", output)
        self.assertIn(
            "Loop stopped (stopped by workshop stop). Ideas: 2. Builds: 2. Published: 2.",
            output,
        )
        record = json.loads((self._loop_folder() / "LOOP.json").read_text())
        self.assertEqual(record["status"], "stopped")
        self.assertEqual(record["published"], 2)
        self.assertEqual(record["last_wish_id"], calls[-1])
        self.assertFalse((self._loop_folder() / "STOP").exists())

    def test_loop_skips_builds_the_judge_bets_against(self):
        rejected = sample_sealed(verdict=sample_verdict("dream-again"))
        approved = sample_sealed(verdict=sample_verdict("build"))
        stdout = StringIO()
        with mock.patch(
            "cli.main.run_daydream", side_effect=[rejected, approved]
        ) as run, mock.patch(
            "cli.main.start_native_run",
            return_value=native_receipt(status="completed", stage="release", published=True),
        ) as start, redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("start", "sample", "--max-ideas", "2"))
        self.assertEqual(result, 0)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(start.call_count, 1)
        output = stdout.getvalue()
        self.assertIn(
            "Judge: dream again (confidence 0.25). Failed: "
            "moving_part_visible_in_both_states. hidden-signature:",
            output,
        )
        self.assertIn("Judge says dream again; not building this one.", output)
        self.assertIn("Judge: build (confidence 0.80). Keep the ladder body", output)
        self.assertIn("Loop stopped (reached --max-ideas 2). Ideas: 2. Builds: 1. Published: 1.", output)

    def test_loop_stops_after_five_judged_out_ideas(self):
        rejected = sample_sealed(verdict=sample_verdict("dream-again"))
        with mock.patch("cli.main.run_daydream", return_value=rejected) as run, mock.patch(
            "cli.main.start_native_run"
        ) as start, redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            result = main(("start", "sample"))
        self.assertEqual(result, 1)
        self.assertEqual(run.call_count, 5)
        start.assert_not_called()
        record = json.loads((self._loop_folder() / "LOOP.json").read_text())
        self.assertEqual(record["stop_reason"], "5 ideas judged out in a row")

    def test_saved_idea_is_built_even_if_the_judge_said_dream_again(self):
        rejected = sample_sealed(verdict=sample_verdict("dream-again"))
        with mock.patch("cli.main.load_sealed_daydream", return_value=rejected), mock.patch(
            "cli.main.start_native_run", return_value=native_receipt()
        ) as start, redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            result = main(("start", "sample", "--idea", rejected.daydream_id))
        self.assertEqual(result, 0)
        start.assert_called_once()

    def test_stop_requested_during_a_daydream_lands_before_the_build(self):
        sealed = sample_sealed()

        def dream(inventor_id, **kwargs):
            (self._loop_folder() / "STOP").write_text("stop\n")
            return sealed

        stdout = StringIO()
        with mock.patch("cli.main.run_daydream", side_effect=dream), mock.patch(
            "cli.main.start_native_run"
        ) as start, redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("start", "sample"))
        self.assertEqual(result, 0)
        start.assert_not_called()
        output = stdout.getvalue()
        self.assertIn("Build it: workshop start sample --idea %s" % sealed.daydream_id, output)
        self.assertIn("Loop stopped (stopped by workshop stop). Ideas: 1. Builds: 0.", output)
        record = json.loads((self._loop_folder() / "LOOP.json").read_text())
        self.assertEqual(record["last_daydream_id"], sealed.daydream_id)
        self.assertFalse((self._loop_folder() / "STOP").exists())

    def test_loop_stops_after_consecutive_failures_with_exit_one(self):
        sealed = sample_sealed()
        with mock.patch("cli.main.run_daydream", return_value=sealed) as run, mock.patch(
            "cli.main.start_native_run", return_value=native_receipt(status="failed")
        ) as start, redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            result = main(("start", "sample"))
        self.assertEqual(result, 1)
        self.assertEqual(run.call_count, 3)
        self.assertEqual(start.call_count, 3)
        record = json.loads((self._loop_folder() / "LOOP.json").read_text())
        self.assertEqual(record["stop_reason"], "3 consecutive failures")

    def test_loop_survives_a_failed_daydream_and_honours_max_ideas(self):
        sealed = sample_sealed()
        stdout = StringIO()
        with mock.patch(
            "cli.main.run_daydream",
            side_effect=[DaydreamError("too close to Horn Tip"), sealed, sealed],
        ) as run, mock.patch(
            "cli.main.start_native_run",
            return_value=native_receipt(status="completed", stage="release", published=True),
        ) as start, redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("start", "sample", "--max-ideas", "2", "--max-failures", "2"))
        self.assertEqual(result, 0)
        self.assertEqual(run.call_count, 3)
        self.assertEqual(start.call_count, 2)
        self.assertIn("Daydream failed: too close to Horn Tip", stdout.getvalue())
        self.assertIn("Loop stopped (reached --max-ideas 2). Ideas: 2.", stdout.getvalue())

    def test_loop_counts_a_build_session_error_and_moves_on(self):
        from workshop.errors import WorkshopError

        sealed = sample_sealed()
        stdout = StringIO()
        with mock.patch("cli.main.run_daydream", return_value=sealed) as run, mock.patch(
            "cli.main.start_native_run",
            side_effect=[
                WorkshopError("native Codex session did not complete"),
                native_receipt(status="completed", stage="release", published=True),
            ],
        ) as start, redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("start", "sample", "--max-ideas", "2"))
        self.assertEqual(result, 0)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(start.call_count, 2)
        output = stdout.getvalue()
        self.assertIn("Build failed: native Codex session did not complete", output)
        self.assertIn("Resume it later: workshop resume wish-", output)
        self.assertIn("Loop stopped (reached --max-ideas 2). Ideas: 2. Builds: 1. Published: 1.", output)
        record = json.loads((self._loop_folder() / "LOOP.json").read_text())
        self.assertEqual(record["consecutive_failures"], 0)
        with mock.patch("cli.main.run_daydream", return_value=sealed), mock.patch(
            "cli.main.start_native_run",
            side_effect=WorkshopError("native Codex session did not complete"),
        ), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(main(("start", "sample", "--once")), 2)
        record = json.loads((self._loop_folder() / "LOOP.json").read_text())
        self.assertEqual(record["status"], "stopped")
        self.assertTrue(record["stop_reason"].startswith("error: native Codex session"))

    def test_loop_json_emits_one_object_per_idea(self):
        sealed = sample_sealed()
        stdout = StringIO()
        with mock.patch("cli.main.run_daydream", return_value=sealed), mock.patch(
            "cli.main.start_native_run",
            return_value=native_receipt(status="completed", stage="release", published=True),
        ), redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("start", "sample", "--max-ideas", "2", "--json"))
        self.assertEqual(result, 0)
        lines = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(lines), 2)
        self.assertEqual({tuple(sorted(line)) for line in lines}, {("daydream", "run")})

    def test_ctrl_c_stops_the_loop_and_keeps_the_run_resumable(self):
        sealed = sample_sealed()
        stdout = StringIO()
        with mock.patch("cli.main.run_daydream", return_value=sealed), mock.patch(
            "cli.main.start_native_run", side_effect=KeyboardInterrupt
        ), redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("start", "sample"))
        self.assertEqual(result, 130)
        self.assertIn("Loop stopped (stopped by Ctrl-C). Ideas: 1. Builds: 0.", stdout.getvalue())
        record = json.loads((self._loop_folder() / "LOOP.json").read_text())
        self.assertEqual(record["status"], "stopped")
        self.assertEqual(record["stop_reason"], "stopped by Ctrl-C")

    def test_second_loop_for_the_same_inventor_is_refused(self):
        from workshop.daydream import acquire_loop

        acquire_loop("sample", pid=os.getpid() + 1, alive=lambda pid: True)
        stderr = StringIO()
        with mock.patch("cli.main.acquire_loop", side_effect=DaydreamError(
            "a daydream loop for sample is already running (pid 7); stop it with `workshop stop sample`"
        )), mock.patch("cli.main.run_daydream") as run, redirect_stdout(
            StringIO()
        ), redirect_stderr(stderr):
            result = main(("start", "sample"))
        self.assertEqual(result, 2)
        run.assert_not_called()
        self.assertIn("already running", stderr.getvalue())

    def test_stop_command_reports_the_running_loop_or_fails(self):
        from workshop.daydream import acquire_loop

        stderr = StringIO()
        with redirect_stdout(StringIO()), redirect_stderr(stderr):
            self.assertEqual(main(("stop", "sample")), 2)
        self.assertIn("no daydream loop is running for sample", stderr.getvalue())
        lease = acquire_loop("sample")
        lease.update(ideas=3, builds=2, published=1)
        stdout = StringIO()
        with redirect_stdout(stdout), redirect_stderr(StringIO()):
            self.assertEqual(main(("stop", "sample")), 0)
        self.assertIn("Stop requested for sample (pid %d)" % os.getpid(), stdout.getvalue())
        self.assertIn("So far: 3 idea(s), 2 build(s), 1 published.", stdout.getvalue())
        self.assertTrue(lease.stop_requested())
        signals = []
        stdout = StringIO()
        with mock.patch("cli.main.request_stop", wraps=lambda inventor, now: (
            signals.append(now) or lease.state
        )), redirect_stdout(stdout), redirect_stderr(StringIO()):
            self.assertEqual(main(("stop", "sample", "--now")), 0)
        self.assertEqual(signals, [True])
        self.assertIn("Interrupting the daydream loop for sample", stdout.getvalue())

    def test_start_asks_for_this_inventors_shop_account_before_any_work(self):
        mock.patch.stopall()
        environment = mock.patch.dict(os.environ, {"WORKSHOP_HOME": str(self.home)})
        environment.start()
        self.addCleanup(environment.stop)
        stdout = StringIO()
        with mock.patch("cli.main.sys.stdin.isatty", return_value=True), mock.patch(
            "builtins.input", return_value=" pico-press "
        ), mock.patch(
            "cli.main.getpass.getpass", return_value="s3cret"
        ), mock.patch(
            "cli.main.run_daydream", return_value=sample_sealed()
        ) as run, mock.patch(
            "cli.main.start_native_run", return_value=native_receipt()
        ), redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("start", "sample", "--once"))
        self.assertEqual(result, 0)
        run.assert_called_once()
        output = stdout.getvalue()
        self.assertIn("sample publishes to the shop as its own account", output)
        self.assertIn("https://www.autonomous.ai/toys", output)
        stored = self.home / "credentials" / "inventors" / "sample.env"
        self.assertEqual(stat.S_IMODE(stored.stat().st_mode), 0o600)
        self.assertIn("FACTORY_USERNAME=pico-press", stored.read_text(encoding="utf-8"))
        # A second start reuses the stored pair and never prompts again.
        with mock.patch(
            "builtins.input", side_effect=AssertionError("prompted twice")
        ), mock.patch(
            "cli.main.run_daydream", return_value=sample_sealed()
        ), mock.patch(
            "cli.main.start_native_run", return_value=native_receipt()
        ), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(main(("start", "sample", "--once")), 0)

    def test_start_without_an_account_outside_a_terminal_fails_closed(self):
        mock.patch.stopall()
        environment = mock.patch.dict(os.environ, {"WORKSHOP_HOME": str(self.home)})
        environment.start()
        self.addCleanup(environment.stop)
        stderr = StringIO()
        with mock.patch("cli.main.sys.stdin.isatty", return_value=False), mock.patch(
            "cli.main.run_daydream"
        ) as run, mock.patch("cli.main.acquire_loop") as lease, redirect_stdout(
            StringIO()
        ), redirect_stderr(stderr):
            result = main(("start", "sample"))
        self.assertEqual(result, 2)
        run.assert_not_called()
        lease.assert_not_called()
        self.assertIn("sample has no shop account on this host", stderr.getvalue())
        self.assertIn("https://www.autonomous.ai/toys", stderr.getvalue())

    def test_daydream_failure_reports_on_stderr_with_exit_two(self):
        stderr = StringIO()
        with mock.patch(
            "cli.main.run_daydream",
            side_effect=DaydreamError("idea is too close to Horn Tip"),
        ), mock.patch("cli.main.start_native_run") as start, redirect_stdout(
            StringIO()
        ), redirect_stderr(stderr):
            result = main(("start", "sample", "--once"))
        self.assertEqual(result, 2)
        start.assert_not_called()
        self.assertIn("workshop: idea is too close to Horn Tip", stderr.getvalue())

    def test_unknown_inventor_source_root_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            stderr = StringIO()
            with mock.patch("cli.main.run_daydream") as run, redirect_stdout(
                StringIO()
            ), redirect_stderr(stderr):
                result = main(("start", "sample", "--once", "--root", temp))
            self.assertEqual(result, 2)
            run.assert_not_called()
            self.assertIn("no native Inventor bundles", stderr.getvalue())


class DoctorTest(unittest.TestCase):
    def test_codex_probe_uses_a_scrubbed_environment_and_no_model(self):
        calls = []

        def run(command, **kwargs):
            calls.append((command, kwargs))
            stdout = "codex-cli 0.145.0" if command[-1] == "--version" else "ok"
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        environment = {
            "WORKSHOP_CODEX_BIN": "/opt/codex",
            "HOME": "/tmp/codex-home",
            "PATH": "/usr/bin",
            "FACTORY_PASSWORD": "factory-secret",
            "AWS_SECRET_ACCESS_KEY": "cloud-secret",
        }
        with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
            "cli.main.subprocess.run", side_effect=run
        ):
            check = cli_main._doctor_codex()
        self.assertEqual(check["status"], "ready")
        self.assertEqual([call[0] for call in calls], [
            ["/opt/codex", "--version"],
            ["/opt/codex", "login", "status"],
        ])
        for unused_command, kwargs in calls:
            self.assertEqual(kwargs["env"]["HOME"], "/tmp/codex-home")
            self.assertNotIn("FACTORY_PASSWORD", kwargs["env"])
            self.assertNotIn("AWS_SECRET_ACCESS_KEY", kwargs["env"])

    def test_old_codex_cannot_pass_the_native_runtime_check(self):
        def run(command, **unused_kwargs):
            return subprocess.CompletedProcess(
                command, 0, stdout="codex-cli 0.144.9", stderr=""
            )

        with mock.patch.dict(
            os.environ,
            {"WORKSHOP_CODEX_BIN": "/opt/codex", "PATH": "/usr/bin"},
            clear=True,
        ), mock.patch("cli.main.subprocess.run", side_effect=run):
            check = cli_main._doctor_codex()
        self.assertEqual(check["status"], "needs-attention")
        self.assertIn("goals, subagents, and isolation", check["detail"])
        self.assertIn("0.145.0", check["next"])

    def test_missing_factory_credentials_block_terminal_release(self):
        ready = lambda name: {"name": name, "status": "ready", "detail": "ok"}
        stdout = StringIO()
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch(
            "cli.main._inventor_source_root", return_value=Path("/inventors")
        ), mock.patch("cli.main._doctor_catalog", return_value=ready("inventor-sources")), mock.patch(
            "cli.main._doctor_codex", return_value=ready("codex")
        ), mock.patch(
            "cli.main._doctor_agent_assets", return_value=ready("agent-assets")
        ), mock.patch(
            "cli.main.factory_credential_environment", return_value={}
        ), redirect_stdout(stdout):
            result = main(("doctor", "--json"))
        receipt = json.loads(stdout.getvalue())
        self.assertEqual(result, 1)
        self.assertEqual(receipt["status"], "needs-attention")
        factory = next(item for item in receipt["checks"] if item["name"] == "factory-credentials")
        self.assertEqual(factory["status"], "needs-attention")
        self.assertIn("Release requires public Factory publication", factory["detail"])

    def test_partial_factory_credentials_fail_without_printing_values(self):
        secret = "do-not-print-this-value"
        ready = lambda name: {"name": name, "status": "ready", "detail": "ok"}
        stdout = StringIO()
        with mock.patch.dict(os.environ, {"FACTORY_PASSWORD": secret}, clear=True), mock.patch(
            "cli.main._inventor_source_root", return_value=Path("/inventors")
        ), mock.patch("cli.main._doctor_catalog", return_value=ready("inventor-sources")), mock.patch(
            "cli.main._doctor_codex", return_value=ready("codex")
        ), mock.patch(
            "cli.main._doctor_agent_assets", return_value=ready("agent-assets")
        ), mock.patch(
            "cli.main.factory_credential_environment",
            return_value={"FACTORY_PASSWORD": secret},
        ), redirect_stdout(stdout):
            result = main(("doctor", "--json"))
        self.assertEqual(result, 1)
        self.assertNotIn(secret, stdout.getvalue())
        self.assertEqual(json.loads(stdout.getvalue())["status"], "needs-attention")

    def test_mismatched_scoped_factory_username_fails_without_printing_value(self):
        secret_username = "not-the-inventor"
        with mock.patch(
            "cli.main.factory_credential_environment",
            return_value={
                "FACTORY_ALICE_USERNAME": secret_username,
                "FACTORY_PASSWORD": "secret",
            },
        ):
            check = cli_main._doctor_factory()
        self.assertEqual(check["status"], "needs-attention")
        self.assertIn("exactly match", check["detail"])
        self.assertNotIn(secret_username, json.dumps(check))

    def test_generic_factory_service_account_is_ready_for_every_inventor(self):
        with mock.patch(
            "cli.main.factory_credential_environment",
            return_value={
                "FACTORY_USERNAME": "alice",
                "FACTORY_PASSWORD": "secret",
            },
        ):
            check = cli_main._doctor_factory()
        self.assertEqual(check["status"], "ready")
        self.assertIn("service-account pair", check["detail"])
        self.assertIn("every Inventor", check["detail"])

    def test_one_legacy_scoped_username_is_ready_with_migration_guidance(self):
        with mock.patch(
            "cli.main.factory_credential_environment",
            return_value={
                "FACTORY_ALICE_USERNAME": "alice",
                "FACTORY_PASSWORD": "secret",
            },
        ):
            check = cli_main._doctor_factory()
        self.assertEqual(check["status"], "ready")
        self.assertIn("service account for every Inventor", check["detail"])
        self.assertIn("FACTORY_USERNAME", check["next"])

    def test_multiple_factory_accounts_fail_without_printing_values(self):
        first = "alice"
        second = "leo-smith"
        with mock.patch(
            "cli.main.factory_credential_environment",
            return_value={
                "FACTORY_ALICE_USERNAME": first,
                "FACTORY_LEO_SMITH_USERNAME": second,
                "FACTORY_PASSWORD": "secret",
            },
        ):
            check = cli_main._doctor_factory()
        self.assertEqual(check["status"], "needs-attention")
        self.assertIn("only one Workshop service account", check["detail"])
        self.assertNotIn(first, json.dumps(check))
        self.assertNotIn(second, json.dumps(check))

    def test_repository_agent_assets_include_executable_cad_verifier(self):
        self.assertEqual(cli_main._doctor_agent_assets()["status"], "ready")


class PersonaCommandTest(unittest.TestCase):
    def test_create_list_and_check_use_only_v8_inventor_bundles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            created_stdout = StringIO()
            with redirect_stdout(created_stdout), redirect_stderr(StringIO()):
                created = main(
                    (
                        "create",
                        "inventor",
                        "mira",
                        "--description",
                        "kinetic desk toys, never board games",
                        "--root",
                        str(root),
                        "--json",
                    )
                )
            self.assertEqual(created, 0)
            receipt = json.loads(created_stdout.getvalue())
            persona = root / "inventors" / "mira"
            manifest = json.loads((persona / "inventor.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], 8)
            self.assertNotIn("capabilities", manifest)
            self.assertNotIn("entrypoint", manifest)
            self.assertNotIn("checks", manifest)
            self.assertEqual(
                {path.name for path in persona.iterdir()},
                {"inventor.json", "TASTE.md", "skills"},
            )
            self.assertEqual(manifest["extensions"][0]["name"], "mira-inventor")
            self.assertEqual(receipt["skills"], manifest["extensions"])
            self.assertEqual(receipt["validation"], "static-passed")
            self.assertNotIn("lane", receipt)

            listed_stdout = StringIO()
            with redirect_stdout(listed_stdout):
                self.assertEqual(main(("inventors", "--root", str(root), "--json")), 0)
            listed = json.loads(listed_stdout.getvalue())
            self.assertEqual([item["id"] for item in listed], ["mira"])
            self.assertNotIn("lane", listed[0])
            self.assertEqual(listed[0]["skills"], ["mira-inventor"])

            checked_stdout = StringIO()
            with mock.patch("cli.main.subprocess.run") as process, redirect_stdout(checked_stdout):
                self.assertEqual(main(("check", str(persona), "--json")), 0)
            process.assert_not_called()
            self.assertEqual(json.loads(checked_stdout.getvalue())["status"], "passed")

    def test_create_from_taste_preserves_exact_bytes_and_derives_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            taste_root = root / "source"
            taste_root.mkdir()
            content = (
                "---\n"
                "name: Moon Weaver\n"
                "description: Tiny astronomical mechanisms with one tactile surprise.\n"
                "---\n"
                "# Moon Weaver's Taste\n\nKeep this exact punctuation.\n"
            ).encode("utf-8")
            taste = taste_root / "TASTE.md"
            taste.write_bytes(content)
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                result = main(
                    (
                        "create",
                        "inventor",
                        "--taste",
                        str(taste),
                        "--root",
                        str(root),
                        "--json",
                    )
                )
            self.assertEqual(result, 0)
            self.assertEqual(
                (root / "inventors" / "moon-weaver" / "TASTE.md").read_bytes(),
                content,
            )

    def test_check_rejects_pre_v8_manifests_without_executing_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            persona = Path(temporary) / "legacy"
            persona.mkdir()
            (persona / "TASTE.md").write_text(
                "---\nname: Legacy\ndescription: Old profile fixture.\n---\n# Taste\n",
                encoding="utf-8",
            )
            (persona / "inventor.json").write_text(
                json.dumps(
                    {
                        "schema_version": 5,
                        "id": "legacy",
                        "status": "active",
                        "entrypoint": ["python3", "profile.py"],
                        "capabilities": ["little-worlds"],
                        "checks": [["python3", "profile.py"]],
                        "source": {"kind": "local"},
                    }
                ),
                encoding="utf-8",
            )
            (persona / "profile.py").write_text(
                "raise RuntimeError('must never execute')\n", encoding="utf-8"
            )
            output = StringIO()
            errors = StringIO()
            with mock.patch("cli.main.subprocess.run") as process, redirect_stdout(output), redirect_stderr(errors):
                result = main(("check", str(persona), "--json"))
            process.assert_not_called()
            self.assertEqual(result, 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("schema_version must be 8", errors.getvalue())

    def test_json_error_does_not_pollute_stdout(self):
        stdout = StringIO()
        stderr = StringIO()
        with tempfile.TemporaryDirectory() as temporary, redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(
                (
                    "create",
                    "inventor",
                    "mira",
                    "--root",
                    temporary,
                    "--json",
                )
            )
        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("--description is required", stderr.getvalue())


class ArtifactCommandTest(unittest.TestCase):
    def test_seal_pack_and_plan_pack_emit_machine_readable_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "artifact"
            artifact.mkdir()
            (artifact / "product.txt").write_text("one exact product\n", encoding="utf-8")
            manifest_path = root / "manifest.json"

            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    main(("seal", str(artifact), "--output", str(manifest_path))), 0
                )
            sealed = json.loads(output.getvalue())
            self.assertEqual(len(sealed["artifact_sha256"]), 64)
            self.assertTrue(manifest_path.is_file())

            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(("plan-pack", str(artifact))), 0)
            self.assertTrue(json.loads(output.getvalue())["fits"])

            output = StringIO()
            pack_path = root / "product.pack"
            with redirect_stdout(output):
                self.assertEqual(main(("pack", str(artifact), str(pack_path))), 0)
            packed = json.loads(output.getvalue())
            self.assertEqual(len(packed["pack_sha256"]), 64)
            self.assertTrue(pack_path.is_file())

class VaultCommandTest(unittest.TestCase):
    def run_cli(self, *argv):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_vault_lint_and_check_read_a_local_checkout(self):
        from tests.invent.test_vault import write_vault

        with tempfile.TemporaryDirectory() as temporary:
            root = write_vault(Path(temporary) / "vault")
            code, out, _ = self.run_cli("vault", "lint", "--root", str(root))
            self.assertEqual(code, 0)
            self.assertIn("error(s)", out)
            code, out, _ = self.run_cli("vault", "lint", "--root", str(root), "--json")
            self.assertEqual(json.loads(out)["errors"], [])
            code, out, _ = self.run_cli(
                "vault", "check", "mechanisms/card-hand", "constraints/fdm-only", "--root", str(root)
            )
            self.assertEqual(code, 0)
            self.assertIn("CONFLICT", out)
            self.assertIn("fix:", out)
            code, out, _ = self.run_cli(
                "vault", "check", "mechanisms/card-hand", "constraints/fdm-only", "--root", str(root), "--json"
            )
            self.assertEqual(json.loads(out)[0]["kind"], "conflict")
            (root / "mechanisms" / "bad.md").write_text(
                "---\ntype: widget\nname: Bad\n---\n## Relations\n- risks:: [[anti-patterns/none]]\n",
                encoding="utf-8",
            )
            code, out, _ = self.run_cli("vault", "lint", "--root", str(root))
            self.assertEqual(code, 2)
            self.assertIn("ERROR mechanisms/bad", out)
            code, _, err = self.run_cli("vault", "lint", "--root", str(Path(temporary) / "nowhere"))
            self.assertEqual(code, 2)
            self.assertIn("no design vault directory", err)

    def test_vault_reads_the_vault_api_and_fails_closed_without_a_token(self):
        from tests.invent.fake_gamevault import FakeGameVaultTransport, install_fake_gamevault
        from workshop.invent.gamevault import default_client as real_default_client

        transport = install_fake_gamevault(
            self, FakeGameVaultTransport(), targets=("cli.main.default_gamevault_client",)
        )
        code, out, _ = self.run_cli("vault", "lint", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["nodes"], len(transport.nodes))
        self.assertTrue(transport.calls[-1][1].endswith("/api/gamevault/export"))
        code, out, _ = self.run_cli("vault", "check", "mechanisms/hand-off", "--json")
        self.assertEqual(json.loads(out)[0]["kind"], "risk")
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(
            os.environ, {"WORKSHOP_HOME": temporary}, clear=True
        ), mock.patch("cli.main.default_gamevault_client", side_effect=real_default_client):
            code, _, err = self.run_cli("vault", "lint")
            self.assertEqual(code, 2)
            self.assertIn("no game vault URL", err)
            self.assertIn("gamevault.env", err)
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(
            os.environ,
            {
                "WORKSHOP_HOME": temporary,
                "WORKSHOP_GAMEVAULT_URL": "http://vault.test",
            },
            clear=True,
        ), mock.patch("cli.main.default_gamevault_client", side_effect=real_default_client):
            code, _, err = self.run_cli("vault", "lint")
            self.assertEqual(code, 2)
            self.assertIn("no game vault token", err)
            self.assertIn("gamevault.env", err)


if __name__ == "__main__":
    unittest.main()
