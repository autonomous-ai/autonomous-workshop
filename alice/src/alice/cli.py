"""Operator CLI for Alice's durable worker."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from .adapters import COMMAND_ADAPTER_CONTRACT_VERSION, CommandAdapter
from .codex_provider import CodexAppServerProvider
from .cad_validation import PrinterCalibrationProfile, PrinterTarget
from .config import DEFAULT_EVAL_PATH, default_runtime_root, load_config, resolve_runtime_paths
from .engine import AliceEngine
from .evals import run_release_policy_suite
from .learning import ContextualThompsonBandit
from .page_builder import (
    PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION,
    PageBuilderAdapter,
    PageBuilderReadback,
)
from .policy import release_policy_from_config
from .providers import CommandAgentProvider, FixtureAgentProvider
from .store import DurableStore
from .text2game_adapter import Text2GamePhysicalAdapter
from .transitions import TransitionEvidence, advance_with_evidence
from .vibe_pipeline import (
    ALICE_REVISION_BOUND_RELEASE_CAPABILITIES,
    REQUIRED_PUBLIC_WRITE_CAPABILITIES,
    VibeHttpClient,
    VibePipeline,
    VibePublishingAdapter,
)


PROJECT_ROOT = default_runtime_root()
PROVIDER_DIAGNOSTICS_CONTRACT_VERSION = "alice.provider-diagnostics.v1"
ADAPTER_DIAGNOSTICS_CONTRACT_VERSION = "alice.adapter-diagnostics.v1"
VIBE_PUBLISHING_CONTRACT_VERSION = "alice.vibe-publishing.v1"
CAD_EFFECT_RECOVERY_CAPABILITIES = frozenset(
    {"idempotent_cad_by_operation_key", "reconcile_cad_by_operation_key"}
)
PRINT_PRODUCTION_RECOVERY_CAPABILITIES = frozenset(
    {
        "authenticated_manufacturing_readback",
        "idempotent_prototype_by_operation_key",
        "reconcile_prototype_by_operation_key",
        "idempotent_production_by_operation_key",
        "reconcile_production_by_operation_key",
    }
)
FACTORY_ORDER_READINESS_CAPABILITIES = frozenset({"paid_order_readback"})
PRINT_FULFILLMENT_READINESS_CAPABILITIES = frozenset(
    {
        "authenticated_manufacturing_readback",
        "idempotent_print_by_operation_key",
        "reconcile_print_by_operation_key",
        "reconcile_qa_ship_by_operation_key",
    }
)
DOMAIN_READINESS_CAPABILITIES: dict[str, frozenset[str]] = {
    "library": frozenset({"licensed_source_readback"}),
    "history": frozenset({"cited_game_corpus_readback"}),
    "research": frozenset({"independent_prior_art_search"}),
    "rules_validator": frozenset({"deterministic_rules_validation"}),
    "digital_playtest": frozenset({"seeded_executable_simulation"}),
    "human_playtest": frozenset({"authenticated_blind_human_readback"}),
    "cad": frozenset({"artifact_hash_readback"}),
    "market_validation": frozenset({"authenticated_market_readback"}),
    "outcomes": frozenset({"authenticated_external_outcome_readback"}),
    "page_builder": frozenset(
        {"private_rich_page_draft", "project_hash_bound_draft"}
    ),
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alice", description="Autonomous 3D-printable board-game inventor"
    )
    parser.add_argument("--config", help="JSON override file")
    parser.add_argument("--root", default=str(PROJECT_ROOT), help="runtime path root")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="initialize durable state and seed known evidence")
    tick = sub.add_parser("tick", help="schedule due work and execute a bounded number of tasks")
    tick.add_argument("--count", type=int, default=1)
    run = sub.add_parser("run", help="run the restartable worker continuously")
    run.add_argument("--poll-seconds", type=float)
    sub.add_parser("status", help="show durable runtime status")
    sub.add_parser("doctor", help="check provider and external-effect readiness")
    sub.add_parser("verify-ledger", help="verify the append-only event chain")
    sub.add_parser("policy", help="show the pinned release-policy hash")
    sub.add_parser("library", help="show the book-laboratory queue")
    evaluate = sub.add_parser("eval", help="run outcome-level release-policy evals")
    evaluate.add_argument(
        "suite", nargs="?", default=str(DEFAULT_EVAL_PATH)
    )

    candidate = sub.add_parser("candidate-add", help="add a 3D game candidate from JSON")
    candidate.add_argument("file")
    candidate.add_argument("--id")
    candidate.add_argument("--title")
    candidate.add_argument("--idempotency-key")

    advance = sub.add_parser("advance", help="advance a candidate using a typed evidence receipt")
    advance.add_argument("candidate_id")
    advance.add_argument("target_state")
    advance.add_argument("evidence_file")

    learn = sub.add_parser("learning-init", help="create the auditable learning-policy state")
    learn.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path(args.root).resolve()
    config = resolve_runtime_paths(load_config(args.config), root)
    database = Path(config["runtime"]["database"])

    if args.command == "library":
        data = config["knowledge"]["library"]
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    if args.command == "eval":
        result = run_release_policy_suite(args.suite)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.passed else 2

    database.parent.mkdir(parents=True, exist_ok=True)
    with DurableStore(database) as store:
        if args.command == "init":
            _seed_market_signals(
                store, config["knowledge"]["market_signals"]
            )
            print(
                json.dumps(
                    {
                        "database": str(database),
                        "journal_mode": store.journal_mode,
                        "policy_hash": release_policy_from_config(config).policy_hash,
                        "effect_mode": config["runtime"]["effect_mode"],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "learning-init":
            existing = store.get_state("alice.learning-policy")
            if existing is not None and not args.force:
                raise SystemExit(
                    "learning state already exists in the durable store"
                )
            learning = config["learning"]
            bandit = ContextualThompsonBandit(
                learning["actions"],
                seed=int(learning["seed"]),
                exploration_probability=float(
                    learning["exploration_probability"]
                ),
                control_action=(
                    "simplify_rules"
                    if "simplify_rules" in learning["actions"]
                    else None
                ),
                control_rate=0.10,
            )
            record = store.put_state(
                "alice.learning-policy",
                bandit.to_state(),
                None if existing is None else existing.version,
            )
            print(
                json.dumps(
                    {
                        "state": record.key,
                        "version": record.version,
                        "database": str(database),
                    },
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "status":
            verification = store.verify_event_chain()
            print(
                json.dumps(
                    {
                        "database": str(database),
                        "quick_check": store.quick_check(),
                        "event_chain": {
                            "valid": verification.valid,
                            "events": verification.events_checked,
                            "head_hash": verification.head_hash,
                        },
                        "stats": store.stats(),
                        "candidates": [
                            {
                                "id": item.id,
                                "title": item.title,
                                "state": item.state,
                                "version": item.version,
                            }
                            for item in store.list_candidates(limit=100)
                        ],
                        "effect_mode": config["runtime"]["effect_mode"],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "doctor":
            engine = _engine(store, config)
            result = _readiness(engine, config)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["ready_for_mode"] else 2

        if args.command == "verify-ledger":
            result = store.verify_event_chain()
            print(json.dumps(as_json(result), indent=2, sort_keys=True))
            return 0 if result.valid else 2

        if args.command == "policy":
            policy = release_policy_from_config(config)
            print(json.dumps({"policy_hash": policy.policy_hash}, indent=2))
            return 0

        if args.command == "candidate-add":
            content = _read_object(args.file)
            title = args.title or content.get("title")
            if not isinstance(title, str) or not title.strip():
                raise SystemExit("candidate title is required")
            candidate = store.create_candidate(
                content,
                kind="3d_printable_board_game",
                title=title,
                candidate_id=args.id,
                idempotency_key=args.idempotency_key,
            )
            print(json.dumps({"id": candidate.id, "state": candidate.state, "version": candidate.version}))
            return 0

        if args.command == "advance":
            evidence = TransitionEvidence.from_mapping(_read_object(args.evidence_file))
            candidate = advance_with_evidence(
                store,
                args.candidate_id,
                args.target_state,
                evidence,
                expected_policy_hash=release_policy_from_config(config).policy_hash,
            )
            print(json.dumps({"id": candidate.id, "state": candidate.state, "version": candidate.version}))
            return 0

        engine = _engine(store, config)
        readiness = _readiness(engine, config)
        if not readiness["ready_for_mode"]:
            missing = ", ".join(readiness["missing_for_mode"])
            raise SystemExit(
                f"refusing to start {config['runtime']['effect_mode']} worker; "
                f"readiness failed: {missing or 'unknown preflight failure'}"
            )
        if args.command == "tick":
            if args.count <= 0:
                raise SystemExit("--count must be positive")
            completed: list[dict[str, Any]] = []
            tick_succeeded = True
            for _ in range(args.count):
                task = engine.work_once()
                if task is None:
                    break
                quarantined = engine._task_is_quarantined(task.id)
                completed.append(
                    {
                        "id": task.id,
                        "kind": task.kind,
                        "state": task.state,
                        "quarantined": quarantined,
                    }
                )
                if task.state != "succeeded" or quarantined:
                    tick_succeeded = False
                    break
            # A quarantine discovered while schedule() replayed an older
            # succeeded result is also unhealthy even when this invocation was
            # otherwise idle.  It remains loud until explicitly reconciled.
            if store.list_experiences(kind="task.result_quarantined", limit=1):
                tick_succeeded = False
            print(json.dumps({"tasks": completed, "status": store.task_counts()}, indent=2))
            return 0 if tick_succeeded else 3
        if args.command == "run":
            engine.run_forever(poll_seconds=args.poll_seconds)
            return 0

    return 1


def _engine(store: DurableStore, config: dict[str, Any]) -> AliceEngine:
    agents = config["agents"]
    if agents["provider"] == "fixture":
        provider = FixtureAgentProvider()
    elif agents["provider"] == "command":
        provider = CommandAgentProvider(
            agents["command"],
            timeout_seconds=int(agents["timeout_seconds"]),
            allowed_environment=agents["model_allowed_environment"],
        )
    elif agents["provider"] == "codex":
        codex = agents["codex"]
        provider = CodexAppServerProvider(
            binary=codex["binary"],
            codex_home=codex["home"],
            model=codex["model"],
            effort=codex["effort"],
            timeout_seconds=float(codex["timeout_seconds"]),
            startup_timeout_seconds=float(codex["startup_timeout_seconds"]),
            shutdown_grace_seconds=float(codex["shutdown_grace_seconds"]),
            max_output_bytes=int(codex["max_output_bytes"]),
            allowed_environment=agents["model_allowed_environment"],
        )
    else:
        raise SystemExit(f"unknown agents.provider {agents['provider']!r}")
    adapters = _adapters(config, store)
    return AliceEngine(store, provider, config, adapters=adapters)


def _readiness(
    engine: AliceEngine, config: Mapping[str, Any]
) -> dict[str, Any]:
    provider = _provider_diagnostics(engine.provider, config)
    integrity = _runtime_integrity_diagnostics(engine)
    adapter_names = (
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
    configured = {name: name in engine.adapters for name in adapter_names}
    diagnostics = {
        name: _adapter_diagnostics(name, engine.adapters.get(name))
        for name in adapter_names
    }
    draft_required = (
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
        "print_fulfillment",
    )
    live_required = adapter_names
    # Capabilities are accepted only from authenticated, versioned diagnostics.
    # In particular, two configured commerce adapters do not by themselves
    # prove the end-to-end order-to-print contract.
    observed_capabilities: set[str] = set()
    for status in diagnostics.values():
        if status["ready"]:
            observed_capabilities.update(status["capabilities"])
    observed_capabilities.discard("order_to_print_job")
    order_capabilities = set(diagnostics["factory_order"]["capabilities"])
    fulfillment_capabilities = set(
        diagnostics["print_fulfillment"]["capabilities"]
    )
    if (
        diagnostics["factory_order"]["ready"]
        and diagnostics["print_fulfillment"]["ready"]
        and FACTORY_ORDER_READINESS_CAPABILITIES.issubset(order_capabilities)
        and PRINT_FULFILLMENT_READINESS_CAPABILITIES.issubset(
            fulfillment_capabilities
        )
    ):
        observed_capabilities.add("order_to_print_job")
    required_capabilities = set(
        engine.release_policy.config.required_factory_capabilities
    )
    missing_capabilities = sorted(required_capabilities - observed_capabilities)
    mode = str(config["runtime"]["effect_mode"])
    required_adapters = (
        () if mode == "dry-run" else draft_required if mode == "draft" else live_required
    )
    missing_adapters = sorted(name for name in required_adapters if not configured[name])
    unready_adapters = sorted(
        name
        for name in required_adapters
        if configured[name] and not diagnostics[name]["ready"]
    )
    missing_adapter_capabilities: list[tuple[str, str]] = []
    for name in required_adapters:
        if not diagnostics[name]["ready"]:
            continue
        required_for_adapter = _required_adapter_capabilities(name, mode)
        observed_for_adapter = set(diagnostics[name]["capabilities"])
        missing_adapter_capabilities.extend(
            (name, capability)
            for capability in sorted(required_for_adapter - observed_for_adapter)
        )
    missing: list[str] = []
    provider_ready = (
        provider["runtime_ready"]
        if mode == "dry-run"
        else provider["effect_ready"]
    )
    if not provider_ready:
        if mode != "dry-run" and provider["simulation_only"]:
            missing.append("provider:fixture_not_allowed")
        elif mode != "dry-run":
            missing.append("provider:authenticated_diagnostics")
        else:
            missing.append("provider")
    if mode != "dry-run":
        missing.extend(f"integrity:{item}" for item in integrity["failures"])
    missing.extend(f"adapter:{name}" for name in missing_adapters)
    missing.extend(f"adapter-diagnostics:{name}" for name in unready_adapters)
    missing.extend(
        f"adapter-capability:{name}:{capability}"
        for name, capability in missing_adapter_capabilities
    )
    if mode == "live":
        missing.extend(f"capability:{name}" for name in missing_capabilities)
    all_adapters_ready = all(
        diagnostics[name]["ready"]
        and _required_adapter_capabilities(name, "live").issubset(
            set(diagnostics[name]["capabilities"])
        )
        for name in adapter_names
    )
    draft_adapters_ready = all(
        diagnostics[name]["ready"]
        and _required_adapter_capabilities(name, "draft").issubset(
            set(diagnostics[name]["capabilities"])
        )
        for name in draft_required
    )
    integrity_ready = integrity["ready"]
    return {
        "provider": provider,
        "runtime_integrity": integrity,
        "adapters": configured,
        "adapters_configured": configured,
        "adapter_diagnostics": diagnostics,
        "observed_factory_capabilities": sorted(observed_capabilities),
        "required_factory_capabilities": sorted(required_capabilities),
        "missing_factory_capabilities": missing_capabilities,
        "runtime_ready": provider["runtime_ready"],
        "full_loop_ready": integrity_ready
        and provider["effect_ready"]
        and all_adapters_ready
        and not missing_capabilities,
        "draft_loop_ready": integrity_ready
        and provider["effect_ready"]
        and draft_adapters_ready,
        "live_effects_ready": integrity_ready
        and provider["effect_ready"]
        and all_adapters_ready
        and not missing_capabilities,
        "effect_mode": mode,
        "missing_for_mode": missing,
        "ready_for_mode": not missing,
    }


def _runtime_integrity_diagnostics(engine: AliceEngine) -> dict[str, Any]:
    """Check durable state and the compiled release-policy regression suite."""

    failures: list[str] = []
    quick_check: str | None = None
    event_chain_valid = False
    events_checked = 0
    try:
        quick_check = engine.store.quick_check()
        if quick_check != "ok":
            failures.append("database_quick_check")
    except Exception as exc:
        failures.append(f"database_quick_check:{type(exc).__name__}")
    try:
        verification = engine.store.verify_event_chain()
        event_chain_valid = verification.valid is True
        events_checked = int(verification.events_checked)
        if not event_chain_valid:
            failures.append("event_chain")
    except Exception as exc:
        failures.append(f"event_chain:{type(exc).__name__}")
    eval_suite = str(DEFAULT_EVAL_PATH)
    eval_passed = False
    eval_cases = 0
    try:
        evaluation = run_release_policy_suite(DEFAULT_EVAL_PATH)
        eval_passed = evaluation.passed is True
        eval_cases = len(evaluation.cases)
        if not eval_passed:
            failures.append("release_policy_eval")
    except Exception as exc:
        failures.append(f"release_policy_eval:{type(exc).__name__}")
    return {
        "ready": not failures,
        "quick_check": quick_check,
        "event_chain_valid": event_chain_valid,
        "events_checked": events_checked,
        "release_policy_eval_passed": eval_passed,
        "release_policy_eval_cases": eval_cases,
        "release_policy_eval_suite": eval_suite,
        "failures": failures,
    }


def _required_adapter_capabilities(name: str, mode: str) -> frozenset[str]:
    if mode not in {"draft", "live"}:
        return frozenset()
    required = set(DOMAIN_READINESS_CAPABILITIES.get(name, ()))
    if name == "cad":
        required.update(CAD_EFFECT_RECOVERY_CAPABILITIES)
        return frozenset(required)
    if name == "print_fulfillment":
        required.update(PRINT_PRODUCTION_RECOVERY_CAPABILITIES)
        if mode == "live":
            required.update(PRINT_FULFILLMENT_READINESS_CAPABILITIES)
        return frozenset(required)
    if name == "factory_order" and mode == "live":
        return FACTORY_ORDER_READINESS_CAPABILITIES
    return frozenset(required)


def _provider_diagnostics(
    provider: Any, config: Mapping[str, Any]
) -> dict[str, Any]:
    configured = str(config["agents"]["provider"])
    if configured == "fixture":
        return {
            "provider": "fixture",
            "runtime_ready": True,
            "effect_ready": False,
            "authenticated": False,
            "contract_version": None,
            "contract_valid": False,
            "simulation_only": True,
        }
    method = getattr(provider, "diagnostics", None)
    if not callable(method):
        return {
            "provider": configured,
            "runtime_ready": False,
            "effect_ready": False,
            "authenticated": False,
            "contract_version": None,
            "contract_valid": False,
            "simulation_only": False,
            "reason": "diagnostics_unavailable",
        }
    try:
        raw = method()
    except Exception as exc:
        return {
            "provider": configured,
            "runtime_ready": False,
            "effect_ready": False,
            "authenticated": False,
            "contract_version": None,
            "contract_valid": False,
            "simulation_only": False,
            "reason": f"diagnostics_failed:{type(exc).__name__}",
        }
    if not isinstance(raw, Mapping):
        return {
            "provider": configured,
            "runtime_ready": False,
            "effect_ready": False,
            "authenticated": False,
            "contract_version": None,
            "contract_valid": False,
            "simulation_only": False,
            "reason": "diagnostics_not_an_object",
        }

    if configured == "codex":
        auth = raw.get("auth")
        runtime = raw.get("runtime")
        home = raw.get("codex_home")
        managed = raw.get("config")
        app_server = raw.get("app_server")
        authenticated = (
            isinstance(auth, Mapping)
            and auth.get("signed_in") is True
            and auth.get("credential_files_secure") is True
        )
        contract_valid = (
            raw.get("provider") == "codex-app-server"
            and isinstance(runtime, Mapping)
            and runtime.get("sandbox") == "read-only"
            and runtime.get("server_requests") == "deny-all"
            and isinstance(home, Mapping)
            and home.get("isolated") is True
            and isinstance(managed, Mapping)
            and managed.get("managed_on_run") is True
            and managed.get("matches_lockdown") is True
            and isinstance(managed.get("sha256"), str)
            and len(str(managed["sha256"])) == 64
            and isinstance(app_server, Mapping)
            and app_server.get("initialized") is True
        )
        runtime_ready = raw.get("ready") is True
        return {
            "provider": "codex-app-server",
            "runtime_ready": runtime_ready,
            "effect_ready": bool(runtime_ready and authenticated and contract_valid),
            "authenticated": authenticated,
            "contract_version": PROVIDER_DIAGNOSTICS_CONTRACT_VERSION,
            "contract_valid": contract_valid,
            "simulation_only": False,
        }

    authenticated = raw.get("authenticated") is True
    contract_valid = (
        raw.get("contract_version") == PROVIDER_DIAGNOSTICS_CONTRACT_VERSION
    )
    runtime_ready = raw.get("ready") is True
    return {
        "provider": str(raw.get("provider") or configured),
        "runtime_ready": runtime_ready,
        "effect_ready": bool(runtime_ready and authenticated and contract_valid),
        "authenticated": authenticated,
        "contract_version": raw.get("contract_version"),
        "contract_valid": contract_valid,
        "simulation_only": False,
    }


def _adapter_diagnostics(name: str, adapter: Any | None) -> dict[str, Any]:
    if adapter is None:
        return {
            "adapter": name,
            "configured": False,
            "ready": False,
            "authenticated": False,
            "contract_version": None,
            "contract_valid": False,
            "capabilities": [],
            "reason": "not_configured",
        }

    if isinstance(adapter, VibePublishingAdapter):
        try:
            backend_capabilities = adapter.pipeline.transport.capabilities()
            authenticated = True
        except Exception as exc:
            return {
                "adapter": name,
                "configured": True,
                "ready": False,
                "authenticated": False,
                "contract_version": VIBE_PUBLISHING_CONTRACT_VERSION,
                "contract_valid": False,
                "capabilities": [],
                "reason": f"authenticated_diagnostics_failed:{type(exc).__name__}",
            }
        contract_valid = REQUIRED_PUBLIC_WRITE_CAPABILITIES.issubset(
            backend_capabilities
        )
        return {
            "adapter": name,
            "configured": True,
            "ready": bool(authenticated and contract_valid),
            "authenticated": authenticated,
            "contract_version": VIBE_PUBLISHING_CONTRACT_VERSION,
            "contract_valid": contract_valid,
            "capabilities": (
                sorted(ALICE_REVISION_BOUND_RELEASE_CAPABILITIES)
                if contract_valid
                else []
            ),
            "backend_contracts": sorted(REQUIRED_PUBLIC_WRITE_CAPABILITIES),
        }

    method = getattr(adapter, "diagnostics", None)
    if not callable(method):
        return {
            "adapter": name,
            "configured": True,
            "ready": False,
            "authenticated": False,
            "contract_version": None,
            "contract_valid": False,
            "capabilities": [],
            "reason": "diagnostics_unavailable",
        }
    try:
        raw = method()
    except Exception as exc:
        return {
            "adapter": name,
            "configured": True,
            "ready": False,
            "authenticated": False,
            "contract_version": None,
            "contract_valid": False,
            "capabilities": [],
            "reason": f"diagnostics_failed:{type(exc).__name__}",
        }
    if not isinstance(raw, Mapping):
        raw = {}
    expected_contract = (
        COMMAND_ADAPTER_CONTRACT_VERSION
        if isinstance(adapter, CommandAdapter)
        else PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION
        if isinstance(adapter, PageBuilderAdapter)
        else ADAPTER_DIAGNOSTICS_CONTRACT_VERSION
    )
    capabilities = raw.get("capabilities")
    capabilities_valid = isinstance(capabilities, (list, tuple)) and all(
        isinstance(item, str) and item.strip() for item in capabilities
    )
    normalized_capabilities = (
        sorted(set(capabilities)) if capabilities_valid else []
    )
    contract_valid = raw.get("contract_version") == expected_contract
    authenticated = raw.get("authenticated") is True
    identity_valid = raw.get("adapter") == name
    ready = bool(
        raw.get("ready") is True
        and authenticated
        and contract_valid
        and identity_valid
        and capabilities_valid
    )
    result = {
        "adapter": name,
        "configured": True,
        "ready": ready,
        "authenticated": authenticated,
        "contract_version": raw.get("contract_version"),
        "contract_valid": contract_valid,
        "capabilities": normalized_capabilities,
    }
    if not ready:
        result["reason"] = "diagnostic_contract_not_satisfied"
    return result


def _adapters(
    config: Mapping[str, Any], store: DurableStore
) -> dict[str, Any]:
    values = config["adapters"]
    definitions = {
        "library": ("library_command", "deterministic"),
        "history": ("history_command", "deterministic"),
        "research": ("research_command", "independent_model"),
        "rules_validator": ("rules_validator_command", "deterministic"),
        "digital_playtest": ("digital_playtest_command", "simulation"),
        "human_playtest": ("human_playtest_command", "blind_human"),
        "cad": ("cad_command", "manufacturing"),
        "market_validation": ("market_validation_command", "market"),
        "outcomes": ("outcomes_command", "external"),
        "factory_order": ("factory_order_command", "market"),
        "print_fulfillment": ("print_fulfillment_command", "manufacturing"),
    }
    command_environment = values["command_allowed_environment"]
    result: dict[str, Any] = {}
    for name, (key, evidence_class) in definitions.items():
        command = values.get(key, [])
        if command:
            result[name] = CommandAdapter(
                name,
                command,
                evidence_class=evidence_class,
                timeout_seconds=1_800,
                allowed_environment=command_environment.get(name, ()),
            )
    text2game = values.get("text2game", {})
    if isinstance(text2game, Mapping) and text2game.get("enabled") is True:
        if config["runtime"]["effect_mode"] == "dry-run":
            raise SystemExit(
                "adapters.text2game runs CAD/model phases and requires "
                "runtime.effect_mode='draft' or 'live'"
            )
        if "cad" in result:
            raise SystemExit(
                "adapters.text2game and adapters.cad_command cannot both own CAD"
            )
        calibration_path = Path(str(text2game["calibration_profile"]))
        profile_raw = _read_small_json_object(
            calibration_path, "adapters.text2game.calibration_profile"
        )
        try:
            profile = PrinterCalibrationProfile.from_mapping(profile_raw)
            target = PrinterTarget.from_mapping(text2game["printer_target"])
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"invalid text2game printer calibration: {exc}") from exc
        environment = {
            name: os.environ[name]
            for name in text2game["allowed_environment"]
            if name in os.environ
        }
        result["cad"] = Text2GamePhysicalAdapter(
            Path(str(text2game["repo"])),
            str(text2game["commit"]),
            Path(str(text2game["work_root"])),
            Path(str(text2game["vibe_workspace"])),
            [str(item) for item in text2game["command"]],
            profile,
            target,
            store,
            text2cad_repo=Path(str(text2game["text2cad_repo"])),
            text2cad_commit=str(text2game["text2cad_commit"]),
            cad_python=Path(str(text2game["cad_python"])),
            slicer_binary=Path(str(text2game["slicer_binary"])),
            slicer_profile=Path(str(text2game["slicer_profile"])),
            codex_binary=Path(str(text2game["codex_binary"])),
            codex_home=Path(str(text2game["codex_home"])),
            git_binary=Path(str(text2game["git_binary"])),
            timeout_seconds=float(text2game["timeout_seconds"]),
            max_output_bytes=int(text2game["max_output_bytes"]),
            max_stderr_bytes=int(text2game["max_stderr_bytes"]),
            shutdown_grace_seconds=float(text2game["shutdown_grace_seconds"]),
            environment=environment,
        )
    page_builder = values.get("page_builder", {})
    if isinstance(page_builder, Mapping) and page_builder.get("enabled") is True:
        if config["runtime"]["effect_mode"] == "dry-run":
            raise SystemExit(
                "adapters.page_builder creates a private remote draft and requires "
                "runtime.effect_mode='draft' or 'live'"
            )
        workspace = str(page_builder.get("workspace") or "").strip()
        operator_command = page_builder.get("operator_command")
        if not workspace:
            raise SystemExit("adapters.page_builder.workspace must be an absolute path")
        if not Path(workspace).expanduser().is_absolute():
            raise SystemExit("adapters.page_builder.workspace must be an absolute path")
        if not isinstance(operator_command, list) or not operator_command:
            raise SystemExit(
                "adapters.page_builder.operator_command must invoke the existing "
                "vibe-ideas board-game/tools/publish.py entry point"
            )
        if (
            isinstance(text2game, Mapping)
            and text2game.get("enabled") is True
            and Path(workspace).resolve()
            != Path(str(text2game["vibe_workspace"])).resolve()
        ):
            raise SystemExit(
                "text2game export and page_builder must use the same Vibe workspace"
            )
        readback_transport = VibeHttpClient.from_environment(
            str(page_builder["base_url"]),
            str(page_builder["token_env"]),
            timeout_seconds=int(page_builder["readback_timeout_seconds"]),
        )
        readback = PageBuilderReadback(
            readback_transport,
            timeout_seconds=int(page_builder["readback_timeout_seconds"]),
            allowed_project_hosts=page_builder["allowed_project_hosts"],
        )
        result["page_builder"] = PageBuilderAdapter(
            workspace,
            [str(value) for value in operator_command],
            readback,
            store,
            timeout_seconds=int(page_builder["timeout_seconds"]),
            diagnostic_design_id=str(page_builder["diagnostic_design_id"]),
            diagnostic_owner_id=str(page_builder["diagnostic_owner_id"]),
            workspace_commit=str(page_builder["workspace_commit"]),
            interpreter_sha256=str(page_builder["interpreter_sha256"]),
            operator_sha256=str(page_builder["operator_sha256"]),
            operator_dependency_sha256=dict(
                page_builder["operator_dependency_sha256"]
            ),
            publishdesign_sha256=str(page_builder["publishdesign_sha256"]),
            publishdesign_preflight_receipt=Path(
                str(page_builder["publishdesign_preflight_receipt"])
            ),
            publishdesign_preflight_sha256=str(
                page_builder["publishdesign_preflight_sha256"]
            ),
            git_binary=Path(str(page_builder["git_binary"])),
            allowed_environment=page_builder["allowed_environment"],
        )
    vibe = values.get("vibe", {})
    if isinstance(vibe, Mapping) and vibe.get("enabled") is True:
        if config["runtime"]["effect_mode"] != "live":
            raise SystemExit(
                "adapters.vibe is a public-write adapter and requires "
                "runtime.effect_mode='live'"
            )
        transport = VibeHttpClient.from_environment(
            str(vibe["base_url"]),
            str(vibe["token_env"]),
            timeout_seconds=int(vibe["timeout_seconds"]),
        )
        pipeline = VibePipeline(
            store,
            transport,
            poll_interval_seconds=float(vibe["poll_interval_seconds"]),
            max_job_polls=int(vibe["max_job_polls"]),
            max_page_polls=int(vibe["max_page_polls"]),
        )
        result["publishing_pipeline"] = VibePublishingAdapter(pipeline)
    return result


def _read_small_json_object(path: Path, label: str) -> Mapping[str, Any]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise SystemExit(f"{label} is unavailable") from exc
    if path.is_symlink() or not path.is_file() or metadata.st_size > 1_048_576:
        raise SystemExit(f"{label} must be a small non-symlink regular JSON file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"{label} is not valid JSON") from exc
    if not isinstance(value, Mapping):
        raise SystemExit(f"{label} must contain a JSON object")
    return value


def _seed_market_signals(
    store: DurableStore, data: Mapping[str, Any]
) -> None:
    if not isinstance(data.get("signals"), list):
        raise ValueError("knowledge.market_signals.signals must be an array")
    for signal in data["signals"]:
        store.add_experience(
            "market.seed",
            signal,
            idempotency_key=f"market-seed:{signal['id']}",
        )


def _read_object(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain one JSON object")
    return value


def as_json(value: Any) -> dict[str, Any]:
    return {
        name: getattr(value, name)
        for name in value.__dataclass_fields__
    }


if __name__ == "__main__":
    raise SystemExit(main())
