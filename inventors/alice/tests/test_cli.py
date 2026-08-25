import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from workshop import load_taste

from alice.cli import (
    ADAPTER_DIAGNOSTICS_CONTRACT_VERSION,
    PROVIDER_DIAGNOSTICS_CONTRACT_VERSION,
    _adapters,
    _readiness,
    main,
)
from alice.config import DATA_ROOT, load_config, resolve_runtime_paths
from alice.policy import release_policy_from_config
from alice.store import DurableStore


class DiagnosticProvider:
    def diagnostics(self):
        return {
            "provider": "test-provider",
            "ready": True,
            "authenticated": True,
            "contract_version": PROVIDER_DIAGNOSTICS_CONTRACT_VERSION,
        }


class DiagnosticAdapter:
    def __init__(self, name: str, capabilities=()) -> None:
        self.name = name
        self.capabilities = list(capabilities)

    def diagnostics(self):
        return {
            "adapter": self.name,
            "ready": True,
            "authenticated": True,
            "contract_version": ADAPTER_DIAGNOSTICS_CONTRACT_VERSION,
            "capabilities": self.capabilities,
        }


class DiagnosticStore:
    def quick_check(self):
        return "ok"

    def verify_event_chain(self):
        return SimpleNamespace(valid=True, events_checked=0)


def diagnostic_engine(config, adapters):
    return SimpleNamespace(
        provider=DiagnosticProvider(),
        adapters=adapters,
        store=DiagnosticStore(),
        taste=load_taste(DATA_ROOT),
        release_policy=release_policy_from_config(config),
        factory_capabilities=lambda: (_ for _ in ()).throw(
            AssertionError("readiness must not infer capabilities from engine presence")
        ),
    )


class CLITests(unittest.TestCase):
    @staticmethod
    def calibration_profile() -> dict[str, object]:
        return {
            "profile_id": "printer-profile-1",
            "revision": 1,
            "printer_id": "printer-1",
            "nozzle_diameter_mm": 0.4,
            "layer_height_mm": 0.2,
            "material": "PETG",
            "calibration_evidence_sha256": "a" * 64,
            "assembled_fits": [
                {"name": "sliding", "per_side_clearance_mm": 0.2}
            ],
            "print_in_place_fits": [
                {
                    "name": "hinge",
                    "xy_gap_mm": 0.3,
                    "z_gap_mm": 0.4,
                    "bottom_relief_mm": 0.2,
                }
            ],
        }

    @staticmethod
    def printer_target() -> dict[str, object]:
        return {
            "profile_id": "printer-profile-1",
            "profile_revision": 1,
            "printer_id": "printer-1",
            "nozzle_diameter_mm": 0.4,
            "layer_height_mm": 0.2,
            "material": "PETG",
        }

    def test_enabled_text2game_owns_cad_with_pinned_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "profile.json"
            profile.write_text(json.dumps(self.calibration_profile()), encoding="utf-8")
            config = resolve_runtime_paths(load_config(), root)
            config["runtime"]["effect_mode"] = "draft"
            config["adapters"]["text2game"].update(
                {
                    "enabled": True,
                    "repo": str(root / "text2game"),
                    "commit": "b" * 40,
                    "vibe_workspace": str(root / "vibe"),
                    "command": [sys.executable],
                    "text2cad_repo": str(root / "text2cad"),
                    "text2cad_commit": "c" * 40,
                    "cad_python": sys.executable,
                    "slicer_binary": str(root / "slicer"),
                    "slicer_profile": str(root / "slicer.ini"),
                    "codex_binary": str(root / "codex"),
                    "codex_home": str(root / "codex-home"),
                    "git_binary": str(root / "git"),
                    "calibration_profile": str(profile),
                    "printer_target": self.printer_target(),
                }
            )
            sentinel = object()
            with patch(
                "alice.cli.Text2GamePhysicalAdapter", return_value=sentinel
            ) as constructor:
                adapters = _adapters(config, object())

            self.assertIs(adapters["cad"], sentinel)
            self.assertEqual(constructor.call_args.args[1], "b" * 40)
            self.assertEqual(constructor.call_args.args[4], [sys.executable])
            self.assertEqual(
                constructor.call_args.kwargs["text2cad_commit"], "c" * 40
            )
            self.assertEqual(
                constructor.call_args.kwargs["git_binary"], root / "git"
            )

    def test_text2game_cannot_run_in_dry_run(self) -> None:
        config = load_config()
        config["adapters"]["text2game"]["enabled"] = True

        with self.assertRaisesRegex(SystemExit, "effect_mode='draft' or 'live'"):
            _adapters(config, object())

    def test_page_builder_receives_reviewed_source_and_binary_pins(self) -> None:
        config = load_config()
        config["runtime"]["effect_mode"] = "draft"
        page = config["adapters"]["page_builder"]
        page.update(
            {
                "enabled": True,
                "workspace": "/srv/vibe",
                "workspace_commit": "a" * 40,
                "operator_command": [
                    "/srv/vibe/.venv/bin/python",
                    "/srv/vibe/board-game/tools/publish.py",
                ],
                "interpreter_sha256": "b" * 64,
                "operator_sha256": "c" * 64,
                "operator_dependency_sha256": {
                    "animation_gate.py": "d" * 64,
                    "journal.py": "e" * 64,
                    "telegram.py": "f" * 64,
                },
                "publishdesign_sha256": "1" * 64,
                "publishdesign_preflight_receipt": "/secure/page-builder-preflight.json",
                "publishdesign_preflight_sha256": "3" * 64,
                "git_binary": "/usr/bin/git",
                "diagnostic_design_id": "private-diagnostic-draft",
                "diagnostic_owner_id": "2" * 24,
                "allowed_project_hosts": ["cdn.example.invalid"],
            }
        )
        sentinel = object()
        with patch(
            "alice.cli.ShopDoorHttpClient.from_environment",
            return_value=SimpleNamespace(get_design=lambda _design_id: {}),
        ), patch("alice.cli.ShopDoorAdapter", return_value=sentinel) as constructor:
            adapters = _adapters(config, object())

        self.assertIs(adapters["page_builder"], sentinel)
        self.assertEqual(constructor.call_args.kwargs["workspace_commit"], "a" * 40)
        self.assertEqual(constructor.call_args.kwargs["interpreter_sha256"], "b" * 64)
        self.assertEqual(
            constructor.call_args.kwargs["publishdesign_preflight_sha256"],
            "3" * 64,
        )
        self.assertEqual(
            constructor.call_args.kwargs["operator_dependency_sha256"]["telegram.py"],
            "f" * 64,
        )
        self.assertEqual(constructor.call_args.kwargs["git_binary"], Path("/usr/bin/git"))

    def test_tick_exit_code_distinguishes_idle_success_and_failed_work(self) -> None:
        cases = (
            (None, False, 0),
            (SimpleNamespace(id="ok", kind="work", state="succeeded"), False, 0),
            (SimpleNamespace(id="quarantine", kind="work", state="succeeded"), True, 3),
            (SimpleNamespace(id="retry", kind="work", state="queued"), False, 3),
            (SimpleNamespace(id="bad", kind="work", state="failed"), False, 3),
        )
        for task, quarantined, expected in cases:
            with self.subTest(state=None if task is None else task.state):
                engine = SimpleNamespace(
                    work_once=lambda: task,
                    _task_is_quarantined=lambda _task_id: quarantined,
                )
                with tempfile.TemporaryDirectory() as directory, patch(
                    "alice.cli._engine", return_value=engine
                ), patch(
                    "alice.cli._readiness",
                    return_value={"ready_for_mode": True, "missing_for_mode": []},
                ), redirect_stdout(StringIO()):
                    self.assertEqual(
                        main(["--root", directory, "tick", "--count", "1"]),
                        expected,
                    )

    def test_idle_tick_is_unhealthy_while_historical_quarantine_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(StringIO()):
            self.assertEqual(main(["--root", directory, "init"]), 0)
            with DurableStore(Path(directory) / "var" / "alice.sqlite3") as store:
                store.add_experience(
                    "task.result_quarantined",
                    {"task_id": "old-task"},
                    idempotency_key="old-quarantine",
                )
            engine = SimpleNamespace(
                work_once=lambda: None,
                _task_is_quarantined=lambda _task_id: False,
            )
            with patch("alice.cli._engine", return_value=engine), patch(
                "alice.cli._readiness",
                return_value={"ready_for_mode": True, "missing_for_mode": []},
            ):
                self.assertEqual(
                    main(["--root", directory, "tick", "--count", "1"]), 3
                )

    def test_init_and_status_in_isolated_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--root", directory, "init"]), 0)
            self.assertTrue((Path(directory) / "var" / "alice.sqlite3").exists())
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--root", directory, "status"]), 0)
            data = json.loads(output.getvalue())
            self.assertTrue(data["event_chain"]["valid"])
            self.assertEqual(data["quick_check"], "ok")

            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--root", directory, "doctor"]), 0)
            doctor = json.loads(output.getvalue())
            self.assertTrue(doctor["runtime_ready"])
            self.assertTrue(doctor["runtime_integrity"]["ready"])
            self.assertTrue(
                doctor["runtime_integrity"]["release_policy_eval_passed"]
            )
            self.assertFalse(doctor["full_loop_ready"])
            self.assertFalse(doctor["live_effects_ready"])
            self.assertTrue(doctor["provider"]["simulation_only"])

    def test_fixture_provider_is_rejected_for_draft_even_when_configured(self) -> None:
        config = load_config()
        config["runtime"]["effect_mode"] = "draft"
        engine = SimpleNamespace(
            provider=object(),
            adapters={},
            store=DiagnosticStore(),
            release_policy=release_policy_from_config(config),
        )

        readiness = _readiness(engine, config)

        self.assertFalse(readiness["ready_for_mode"])
        self.assertIn("provider:fixture_not_allowed", readiness["missing_for_mode"])

    def test_dry_run_tick_cannot_bypass_failed_provider_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            override = Path(directory) / "config.json"
            override.write_text(
                json.dumps(
                    {
                        "agents": {
                            "provider": "command",
                            "command": ["/definitely/missing-alice-provider"],
                        }
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "readiness failed"):
                main(
                    [
                        "--config",
                        str(override),
                        "--root",
                        directory,
                        "tick",
                    ]
                )

    def test_order_to_print_requires_authenticated_primitive_contracts(self) -> None:
        config = load_config()
        config["runtime"]["effect_mode"] = "live"
        config["agents"]["provider"] = "command"
        names = (
            "library",
            "history",
            "research",
            "rules_validator",
            "digital_playtest",
            "human_playtest",
            "cad",
            "market_validation",
            "outcomes",
            "page_builder",
            "shop_door",
            "delivery",
            "print_fulfillment",
        )
        publish_capabilities = {
            "durable_publication_intent",
            "explicit_price",
            "ambiguous_no_retry",
            "page_pipeline_readback",
            "expected_history_cas",
            "exact_sku_currency_binding",
            "server_enrichment_readback",
        }
        cad_capabilities = {
            "idempotent_cad_by_operation_key",
            "reconcile_cad_by_operation_key",
        }
        print_capabilities = {
            "authenticated_manufacturing_readback",
            "idempotent_prototype_by_operation_key",
            "reconcile_prototype_by_operation_key",
            "idempotent_production_by_operation_key",
            "reconcile_production_by_operation_key",
        }
        domain_capabilities = {
            "library": {"licensed_source_readback"},
            "history": {"cited_game_corpus_readback"},
            "research": {"independent_prior_art_search"},
            "rules_validator": {"deterministic_rules_validation"},
            "digital_playtest": {"seeded_executable_simulation"},
            "human_playtest": {"authenticated_blind_human_readback"},
            "cad": {"artifact_hash_readback"} | cad_capabilities,
            "market_validation": {"authenticated_market_readback"},
            "outcomes": {"authenticated_external_outcome_readback"},
            "page_builder": {
                "private_rich_page_draft",
                "project_hash_bound_draft",
            },
        }
        adapters = {
            name: DiagnosticAdapter(
                name,
                publish_capabilities
                if name == "shop_door"
                else print_capabilities
                if name == "print_fulfillment"
                else domain_capabilities.get(name, ()),
            )
            for name in names
        }
        engine = diagnostic_engine(config, adapters)

        without_contract = _readiness(engine, config)

        self.assertFalse(without_contract["ready_for_mode"])
        self.assertNotIn(
            "order_to_print_job", without_contract["observed_shop_capabilities"]
        )
        self.assertIn(
            "capability:order_to_print_job", without_contract["missing_for_mode"]
        )

        adapters["delivery"] = DiagnosticAdapter(
            "delivery", ["paid_order_readback"]
        )
        adapters["print_fulfillment"] = DiagnosticAdapter(
            "print_fulfillment",
            print_capabilities
            | {
                "idempotent_print_by_operation_key",
                "reconcile_print_by_operation_key",
                "reconcile_qa_ship_by_operation_key",
            },
        )
        with_contract = _readiness(diagnostic_engine(config, adapters), config)

        self.assertTrue(with_contract["ready_for_mode"])
        self.assertIn(
            "order_to_print_job", with_contract["observed_shop_capabilities"]
        )

    def test_draft_readiness_fails_closed_when_store_integrity_fails(self) -> None:
        config = load_config()
        config["runtime"]["effect_mode"] = "draft"
        engine = diagnostic_engine(config, {})
        engine.store = SimpleNamespace(
            quick_check=lambda: "corrupt",
            verify_event_chain=lambda: SimpleNamespace(
                valid=False, events_checked=1
            ),
        )

        readiness = _readiness(engine, config)

        self.assertFalse(readiness["runtime_integrity"]["ready"])
        self.assertIn(
            "integrity:database_quick_check", readiness["missing_for_mode"]
        )
        self.assertIn("integrity:event_chain", readiness["missing_for_mode"])


if __name__ == "__main__":
    unittest.main()
