import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

from alice.cli import (
    ADAPTER_DIAGNOSTICS_CONTRACT_VERSION,
    PROVIDER_DIAGNOSTICS_CONTRACT_VERSION,
    _readiness,
    main,
)
from alice.config import load_config
from alice.policy import release_policy_from_config


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
        release_policy=release_policy_from_config(config),
        factory_capabilities=lambda: (_ for _ in ()).throw(
            AssertionError("readiness must not infer capabilities from engine presence")
        ),
    )


class CLITests(unittest.TestCase):
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
            "publishing_pipeline",
            "factory_order",
            "print_fulfillment",
        )
        publish_capabilities = {
            "durable_publication_intent",
            "explicit_price",
            "ambiguous_no_retry",
            "page_pipeline_readback",
            "expected_history_cas",
            "exact_sku_currency_binding",
            "atomic_rich_page_precondition",
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
                if name == "publishing_pipeline"
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
            "order_to_print_job", without_contract["observed_factory_capabilities"]
        )
        self.assertIn(
            "capability:order_to_print_job", without_contract["missing_for_mode"]
        )

        adapters["factory_order"] = DiagnosticAdapter(
            "factory_order", ["paid_order_readback"]
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
            "order_to_print_job", with_contract["observed_factory_capabilities"]
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
