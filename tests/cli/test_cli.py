import json
import importlib
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from cli.main import main, parser


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
            "requested": published,
        },
    }
    if progress is not None:
        receipt["progress"] = progress
    return receipt


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

        def start(wish, *, publish_requested, activity_observer):
            observed["wish"] = wish
            observed["publish_requested"] = publish_requested
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
        self.assertIn("not published by default", stderr.getvalue())
        self.assertIn("reasoning about the current stage", stderr.getvalue())
        self.assertIn("process is still running", stderr.getvalue())
        self.assertIn("using a tool for the current stage", stderr.getvalue())
        self.assertIn("turn complete; Workshop is verifying it", stderr.getvalue())
        self.assertEqual(stderr.getvalue().count("process is still running"), 1)
        self.assertEqual(stderr.getvalue().count("using a tool"), 1)
        self.assertEqual(observed["wish"].objective, "a moon that waddles")
        self.assertEqual(observed["wish"].context, {"source": "workshop-cli"})
        self.assertFalse(observed["publish_requested"])
        native_start.assert_called_once()

    def test_wish_publish_is_explicit_and_strict_wait_exits_one(self):
        stdout = StringIO()
        with mock.patch("cli.main.generate_wish_id", return_value="wish-one"), mock.patch(
            "cli.main.start_native_run", return_value=native_receipt()
        ) as start, redirect_stdout(stdout), redirect_stderr(StringIO()):
            result = main(("wish", "a moon", "--publish", "--strict", "--json"))
        self.assertEqual(result, 1)
        start.assert_called_once()
        self.assertTrue(start.call_args.kwargs["publish_requested"])

    def test_live_native_activity_repeats_only_throttled_running_updates(self):
        output = StringIO()
        activity = cli_main._LiveNativeActivity(output)
        with mock.patch(
            "cli.main.time.monotonic",
            side_effect=(100.0, 129.9, 130.0),
        ):
            activity("running")
            activity("running")
            activity("running")

        self.assertEqual(output.getvalue().count("process is still running"), 2)

    def test_live_native_activity_rate_limits_high_churn_classes(self):
        output = StringIO()
        activity = cli_main._LiveNativeActivity(output)
        with mock.patch(
            "cli.main.time.monotonic",
            side_effect=(100.0, 100.5, 102.0),
        ):
            activity("reasoning")
            activity("tool")
            activity("tool")

        self.assertEqual(output.getvalue().count("reasoning"), 1)
        self.assertEqual(output.getvalue().count("using a tool"), 1)

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
        receipt = native_receipt(status="waiting", stage="deliver")
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
        receipt = native_receipt(status="complete", stage="deliver")
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
        def resume_run(product_id, *, publish_requested, activity_observer):
            activity_observer("tool")
            return native_receipt(stage="make")

        stdout = StringIO()
        stderr = StringIO()
        with mock.patch(
            "cli.main.resume_native_run", side_effect=resume_run
        ) as resume, redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(
                ("resume", "wish-one", "--publish", "--strict", "--json")
            )
        self.assertEqual(result, 1)
        resume.assert_called_once()
        self.assertEqual(resume.call_args.args, ("wish-one",))
        self.assertTrue(resume.call_args.kwargs["publish_requested"])
        self.assertTrue(callable(resume.call_args.kwargs["activity_observer"]))
        self.assertEqual(json.loads(stdout.getvalue())["stage"], "make")
        self.assertIn("exact native Codex session", stderr.getvalue())
        self.assertIn("using a tool for the current stage", stderr.getvalue())

    def test_failed_native_run_exits_one_even_without_strict(self):
        with mock.patch("cli.main.generate_wish_id", return_value="wish-one"), mock.patch(
            "cli.main.start_native_run",
            return_value=native_receipt(status="failed", stage="playtest"),
        ), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(main(("wish", "a moon")), 1)

    def test_draft_is_the_parser_default(self):
        command = parser()
        self.assertFalse(command.parse_args(("wish", "a moon")).publish)
        self.assertFalse(command.parse_args(("resume", "wish-one")).publish)
        self.assertTrue(command.parse_args(("wish", "a moon", "--publish")).publish)


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

    def test_missing_factory_credentials_are_optional_for_local_release(self):
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
        self.assertEqual(result, 0)
        self.assertEqual(receipt["status"], "ready")
        factory = next(item for item in receipt["checks"] if item["name"] == "factory-credentials")
        self.assertEqual(factory["status"], "ready")
        self.assertIn("local Release remains available", factory["detail"])
        self.assertIn("requested publication", factory["detail"])

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

    def test_generic_factory_pair_remains_ready(self):
        with mock.patch(
            "cli.main.factory_credential_environment",
            return_value={
                "FACTORY_USERNAME": "inventor-from-run",
                "FACTORY_PASSWORD": "secret",
            },
        ):
            check = cli_main._doctor_factory()
        self.assertEqual(check["status"], "ready")

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

    def test_vault_seed_lint_and_check_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "vault"
            code, out, _ = self.run_cli("vault", "seed", "--root", str(root))
            self.assertEqual(code, 0)
            self.assertIn("node(s) written", out)
            self.assertTrue((root / "mechanisms").is_dir())
            code, out, _ = self.run_cli("vault", "seed", "--root", str(root), "--json")
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["written"], 0)

            code, out, _ = self.run_cli("vault", "lint", "--root", str(root))
            self.assertIn(code, (0, 1))
            self.assertIn("error(s)", out)
            code, out, _ = self.run_cli("vault", "lint", "--root", str(root), "--json")
            self.assertEqual(json.loads(out)["errors"], [])

            fdm = "constraints/fdm-printed-components-only"
            code, out, _ = self.run_cli(
                "vault", "check", "mechanisms/hand-management", fdm, "--root", str(root)
            )
            self.assertEqual(code, 0)
            self.assertIn("CONFLICT", out)
            self.assertIn("fix:", out)
            code, out, _ = self.run_cli(
                "vault", "check", "mechanisms/hand-management", fdm, "--root", str(root), "--json"
            )
            self.assertEqual(json.loads(out)[0]["kind"], "conflict")

    def test_vault_lint_reports_errors_with_exit_two_and_bundled_flag(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "vault"
            (root / "mechanisms").mkdir(parents=True)
            (root / "mechanisms" / "bad.md").write_text(
                "---\ntype: widget\nname: Bad\n---\n## Relations\n- risks:: [[anti-patterns/none]]\n",
                encoding="utf-8",
            )
            code, out, _ = self.run_cli("vault", "lint", "--root", str(root))
            self.assertEqual(code, 2)
            self.assertIn("ERROR mechanisms/bad", out)
            code, out, _ = self.run_cli("vault", "lint", "--bundled", "--json")
            self.assertIn(code, (0, 1))
            self.assertGreater(json.loads(out)["nodes"], 100)

    def test_vault_defaults_to_the_workshop_home_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict(os.environ, {"WORKSHOP_HOME": temporary}):
                code, _, err = self.run_cli("vault", "lint")
                self.assertEqual(code, 2)
                self.assertIn("workshop vault seed", err)
                code, out, _ = self.run_cli("vault", "seed", "--json")
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(out)["root"], str(Path(temporary) / "vault"))
                code, _, _ = self.run_cli("vault", "lint")
                self.assertIn(code, (0, 1))


if __name__ == "__main__":
    unittest.main()
