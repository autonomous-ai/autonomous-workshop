"""Configuration loading with safe, explicit defaults."""

from __future__ import annotations

import copy
import json
import math
import os
import re
from pathlib import Path
import sysconfig
from typing import Any, Mapping


SOURCE_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DATA_ROOT = SOURCE_ROOT
INSTALLED_DATA_ROOT = (
    Path(sysconfig.get_path("data")) / "share" / "autonomous-alice"
)
DATA_ROOT = (
    SOURCE_DATA_ROOT
    if (SOURCE_DATA_ROOT / "config" / "default.json").is_file()
    else INSTALLED_DATA_ROOT
)
DEFAULT_CONFIG_PATH = DATA_ROOT / "config" / "default.json"
DEFAULT_LIBRARY_PATH = DEFAULT_CONFIG_PATH.parent / "library.json"
DEFAULT_MARKET_SIGNALS_PATH = DEFAULT_CONFIG_PATH.parent / "market-signals.json"
DEFAULT_EVAL_PATH = DATA_ROOT / "evals" / "release-policy.json"

SAFE_SHARED_ENVIRONMENT = frozenset({"PATH", "LANG", "LC_ALL", "TMPDIR"})
COMMAND_ADAPTER_NAMES = frozenset(
    {
        "library",
        "history",
        "research",
        "rules_validator",
        "digital_playtest",
        "human_playtest",
        "cad",
        "market_validation",
        "outcomes",
        "delivery",
        "print_fulfillment",
    }
)
_ENVIRONMENT_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OBJECT_ID = re.compile(r"^[0-9a-f]{24}$")
_PAGE_BUILDER_DEPENDENCIES = frozenset(
    {"animation_gate.py", "journal.py", "telegram.py"}
)
_UNSAFE_PROCESS_ENVIRONMENT = frozenset(
    {
        "BASH_ENV",
        "ENV",
        "LD_PRELOAD",
        "PYTHONHOME",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "PYTHONINSPECT",
        "PYTHONBREAKPOINT",
    }
)
_REMOVED_CONFIG_PATHS = (
    ("runtime", "artifacts"),
    ("runtime", "outbox"),
    ("runtime", "target_publish_cadence_days"),
    ("objective", "product_type"),
    ("objective", "fulfillment"),
    ("objective", "human_publish_approval"),
    ("agents", "allowed_environment"),
    ("adapters", "factory_publish_command"),
    ("quality", "maximum_critical_exploits"),
)


def _merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def _environment_names(value: Any, path: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not _ENVIRONMENT_NAME.fullmatch(item)
        for item in value
    ):
        raise ValueError(f"{path} must be an array of environment-variable names")
    if len(set(value)) != len(value):
        raise ValueError(f"{path} must not contain duplicates")
    return tuple(value)


def _positive_number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{path} must be a positive finite number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError(f"{path} must be a positive finite number")
    return normalized


def _positive_integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{path} must be a positive integer")
    return value


def _unit_interval(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{path} must be between 0 and 1")
    normalized = float(value)
    if not math.isfinite(normalized) or not 0 <= normalized <= 1:
        raise ValueError(f"{path} must be between 0 and 1")
    return normalized


def _validate_config(config: Mapping[str, Any]) -> None:
    for section, key in _REMOVED_CONFIG_PATHS:
        value = config.get(section)
        if isinstance(value, Mapping) and key in value:
            raise ValueError(
                f"{section}.{key} was removed; it is not an active runtime control"
            )

    runtime = config.get("runtime")
    agents = config.get("agents")
    adapters = config.get("adapters")
    if (
        not isinstance(runtime, Mapping)
        or not isinstance(agents, Mapping)
        or not isinstance(adapters, Mapping)
    ):
        raise ValueError("runtime, agents, and adapters configuration must be objects")
    _positive_number(runtime.get("poll_seconds"), "runtime.poll_seconds")
    _positive_number(runtime.get("lease_seconds"), "runtime.lease_seconds")
    _positive_integer(runtime.get("max_attempts"), "runtime.max_attempts")
    _positive_integer(
        runtime.get("max_active_candidates"), "runtime.max_active_candidates"
    )
    objective = config.get("objective")
    if not isinstance(objective, Mapping) or not isinstance(
        objective.get("auto_publish_when_eligible"), bool
    ):
        raise ValueError(
            "objective.auto_publish_when_eligible must be a boolean"
        )
    _positive_number(agents.get("timeout_seconds"), "agents.timeout_seconds")
    codex = agents.get("codex")
    if not isinstance(codex, Mapping):
        raise ValueError("agents.codex must be an object")
    for key in (
        "timeout_seconds",
        "startup_timeout_seconds",
        "shutdown_grace_seconds",
    ):
        _positive_number(codex.get(key), f"agents.codex.{key}")
    _positive_integer(
        codex.get("max_output_bytes"), "agents.codex.max_output_bytes"
    )
    model_environment = set(
        _environment_names(
            agents.get("model_allowed_environment"),
            "agents.model_allowed_environment",
        )
    )
    unsafe_model_environment = sorted(
        model_environment - SAFE_SHARED_ENVIRONMENT
    )
    if unsafe_model_environment:
        raise ValueError(
            "adapter-only or credential environment variables cannot be forwarded "
            "to the model; agents.model_allowed_environment is limited to: "
            + ", ".join(sorted(SAFE_SHARED_ENVIRONMENT))
        )

    command_environment = adapters.get("command_allowed_environment")
    if not isinstance(command_environment, Mapping):
        raise ValueError("adapters.command_allowed_environment must be an object")
    unknown = sorted(set(command_environment) - COMMAND_ADAPTER_NAMES)
    if unknown:
        raise ValueError(
            "adapters.command_allowed_environment has unknown adapters: "
            + ", ".join(unknown)
        )
    adapter_environment: set[str] = set()
    for name, names in command_environment.items():
        adapter_environment.update(
            _environment_names(names, f"adapters.command_allowed_environment.{name}")
        )

    text2game = adapters.get("text2game")
    page_builder = adapters.get("page_builder")
    vibe = adapters.get("vibe")
    if (
        not isinstance(text2game, Mapping)
        or not isinstance(page_builder, Mapping)
        or not isinstance(vibe, Mapping)
    ):
        raise ValueError(
            "adapters.text2game, adapters.page_builder, and adapters.vibe must be objects"
        )
    if "uv_binary" in text2game:
        raise ValueError(
            "adapters.text2game.uv_binary was removed; Alice uses a pinned "
            "operation-local CAD-Python shim"
        )
    if not isinstance(text2game.get("enabled"), bool):
        raise ValueError("adapters.text2game.enabled must be a boolean")
    text2game_environment = set(
        _environment_names(
            text2game.get("allowed_environment"),
            "adapters.text2game.allowed_environment",
        )
    )
    unsafe_text2game_environment = sorted(
        name
        for name in text2game_environment
        if name in _UNSAFE_PROCESS_ENVIRONMENT
        or name.startswith("DYLD_")
        or name.startswith("GIT_")
    )
    if unsafe_text2game_environment:
        raise ValueError(
            "adapters.text2game.allowed_environment contains process-injection names: "
            + ", ".join(unsafe_text2game_environment)
        )
    adapter_environment.update(text2game_environment)
    for key in (
        "repo",
        "work_root",
        "vibe_workspace",
        "text2cad_repo",
        "cad_python",
        "slicer_binary",
        "slicer_profile",
        "codex_binary",
        "codex_home",
        "git_binary",
        "calibration_profile",
    ):
        if not isinstance(text2game.get(key), str):
            raise ValueError(f"adapters.text2game.{key} must be a path string")
    for key in ("commit", "text2cad_commit"):
        pinned_commit = text2game.get(key)
        if not isinstance(pinned_commit, str) or (
            pinned_commit and _GIT_COMMIT.fullmatch(pinned_commit) is None
        ):
            raise ValueError(
                f"adapters.text2game.{key} must be empty or a lowercase 40-hex commit"
            )
    text2game_command = text2game.get("command")
    if not isinstance(text2game_command, list) or any(
        not isinstance(item, str) or not item.strip() or item != item.strip()
        for item in text2game_command
    ):
        raise ValueError(
            "adapters.text2game.command must be an array of non-empty arguments"
        )
    if not isinstance(text2game.get("printer_target"), Mapping):
        raise ValueError("adapters.text2game.printer_target must be an object")
    _positive_number(
        text2game.get("timeout_seconds"), "adapters.text2game.timeout_seconds"
    )
    _positive_integer(
        text2game.get("max_output_bytes"), "adapters.text2game.max_output_bytes"
    )
    _positive_integer(
        text2game.get("max_stderr_bytes"), "adapters.text2game.max_stderr_bytes"
    )
    _positive_number(
        text2game.get("shutdown_grace_seconds"),
        "adapters.text2game.shutdown_grace_seconds",
    )
    if text2game.get("enabled") is True:
        missing_text2game = [
            key
            for key in (
                "repo",
                "commit",
                "vibe_workspace",
                "text2cad_repo",
                "text2cad_commit",
                "cad_python",
                "slicer_binary",
                "slicer_profile",
                "codex_binary",
                "codex_home",
                "git_binary",
                "calibration_profile",
            )
            if not str(text2game.get(key) or "").strip()
        ]
        if missing_text2game:
            raise ValueError(
                "enabled text2game adapter requires: "
                + ", ".join(f"adapters.text2game.{key}" for key in missing_text2game)
            )
        if not text2game_command:
            raise ValueError(
                "enabled text2game adapter requires adapters.text2game.command"
            )
        if not text2game.get("printer_target"):
            raise ValueError(
                "enabled text2game adapter requires adapters.text2game.printer_target"
            )
        if adapters.get("cad_command"):
            raise ValueError(
                "adapters.text2game and adapters.cad_command cannot both be enabled"
            )
    page_environment = set(
        _environment_names(
            page_builder.get("allowed_environment"),
            "adapters.page_builder.allowed_environment",
        )
    )
    adapter_environment.update(page_environment)
    for key in ("workspace", "git_binary", "publishdesign_preflight_receipt"):
        if not isinstance(page_builder.get(key), str):
            raise ValueError(f"adapters.page_builder.{key} must be a path string")
    for key in ("diagnostic_design_id", "diagnostic_owner_id"):
        if not isinstance(page_builder.get(key), str):
            raise ValueError(f"adapters.page_builder.{key} must be a string")
    diagnostic_owner_id = page_builder.get("diagnostic_owner_id")
    if diagnostic_owner_id and _OBJECT_ID.fullmatch(diagnostic_owner_id) is None:
        raise ValueError(
            "adapters.page_builder.diagnostic_owner_id must be empty or a "
            "lowercase 24-hex owner id"
        )
    workspace_commit = page_builder.get("workspace_commit")
    if not isinstance(workspace_commit, str) or (
        workspace_commit and _GIT_COMMIT.fullmatch(workspace_commit) is None
    ):
        raise ValueError(
            "adapters.page_builder.workspace_commit must be empty or a lowercase 40-hex commit"
        )
    for key in (
        "interpreter_sha256",
        "operator_sha256",
        "publishdesign_sha256",
        "publishdesign_preflight_sha256",
    ):
        digest = page_builder.get(key)
        if not isinstance(digest, str) or (
            digest and _SHA256.fullmatch(digest) is None
        ):
            raise ValueError(
                f"adapters.page_builder.{key} must be empty or a lowercase SHA-256"
            )
    dependency_hashes = page_builder.get("operator_dependency_sha256")
    if not isinstance(dependency_hashes, Mapping) or set(dependency_hashes) != set(
        _PAGE_BUILDER_DEPENDENCIES
    ):
        raise ValueError(
            "adapters.page_builder.operator_dependency_sha256 must contain exactly: "
            + ", ".join(sorted(_PAGE_BUILDER_DEPENDENCIES))
        )
    for name, digest in dependency_hashes.items():
        if not isinstance(digest, str) or (
            digest and _SHA256.fullmatch(digest) is None
        ):
            raise ValueError(
                "adapters.page_builder.operator_dependency_sha256."
                f"{name} must be empty or a lowercase SHA-256"
            )
    operator_command = page_builder.get("operator_command")
    if not isinstance(operator_command, list) or any(
        not isinstance(item, str) or not item.strip() or item != item.strip()
        for item in operator_command
    ):
        raise ValueError(
            "adapters.page_builder.operator_command must be an array of non-empty arguments"
        )
    allowed_project_hosts = page_builder.get("allowed_project_hosts")
    if not isinstance(allowed_project_hosts, list) or any(
        not isinstance(host, str)
        or not host.strip()
        or host != host.strip()
        or "/" in host
        or ":" in host
        or "@" in host
        for host in allowed_project_hosts
    ):
        raise ValueError(
            "adapters.page_builder.allowed_project_hosts must be DNS host names"
        )
    if len({host.casefold() for host in allowed_project_hosts}) != len(
        allowed_project_hosts
    ):
        raise ValueError(
            "adapters.page_builder.allowed_project_hosts must not contain duplicates"
        )
    if page_builder.get("enabled") is True and not allowed_project_hosts:
        raise ValueError(
            "enabled page_builder requires adapters.page_builder.allowed_project_hosts"
        )
    if page_builder.get("enabled") is True:
        required_page_builder = (
            "workspace",
            "workspace_commit",
            "interpreter_sha256",
            "operator_sha256",
            "publishdesign_sha256",
            "publishdesign_preflight_receipt",
            "publishdesign_preflight_sha256",
            "git_binary",
            "diagnostic_design_id",
            "diagnostic_owner_id",
        )
        missing_page_builder = [
            key
            for key in required_page_builder
            if not str(page_builder.get(key) or "").strip()
        ]
        missing_page_builder.extend(
            f"operator_dependency_sha256.{name}"
            for name, digest in dependency_hashes.items()
            if not digest
        )
        if missing_page_builder:
            raise ValueError(
                "enabled page_builder requires: "
                + ", ".join(
                    f"adapters.page_builder.{key}" for key in missing_page_builder
                )
            )
        if len(operator_command) != 2:
            raise ValueError(
                "enabled page_builder requires exactly two operator_command arguments"
            )
    for key in ("timeout_seconds", "readback_timeout_seconds"):
        _positive_number(
            page_builder.get(key), f"adapters.page_builder.{key}"
        )
    for key in ("timeout_seconds", "poll_interval_seconds"):
        _positive_number(vibe.get(key), f"adapters.vibe.{key}")
    for key in ("max_job_polls", "max_page_polls"):
        _positive_integer(vibe.get(key), f"adapters.vibe.{key}")

    token_names: set[str] = set()
    for name, values in (("page_builder", page_builder), ("vibe", vibe)):
        token_env = values.get("token_env")
        if not isinstance(token_env, str) or not _ENVIRONMENT_NAME.fullmatch(token_env):
            raise ValueError(f"adapters.{name}.token_env must name an environment variable")
        token_names.add(token_env)
    if str(page_builder["token_env"]) in page_environment:
        raise ValueError(
            "adapters.page_builder.token_env must not be forwarded to publish.py"
        )

    sensitive_adapter_environment = (
        adapter_environment - SAFE_SHARED_ENVIRONMENT
    ) | token_names
    overlap = sorted(model_environment & sensitive_adapter_environment)
    if overlap:
        raise ValueError(
            "adapter-only environment variables cannot be forwarded to the model: "
            + ", ".join(overlap)
        )

    required = adapters.get("required_live_capabilities")
    if not isinstance(required, list) or any(
        not isinstance(item, str) or not item.strip() for item in required
    ):
        raise ValueError("adapters.required_live_capabilities must be an array of names")
    if len(set(required)) != len(required):
        raise ValueError("adapters.required_live_capabilities must not contain duplicates")

    learning = config.get("learning")
    quality = config.get("quality")
    if not isinstance(learning, Mapping) or not isinstance(quality, Mapping):
        raise ValueError("learning and quality configuration must be objects")
    _positive_integer(
        learning.get("minimum_external_trials"),
        "learning.minimum_external_trials",
    )
    _unit_interval(
        learning.get("exploration_probability"),
        "learning.exploration_probability",
    )
    for key in (
        "minimum_dimension",
        "minimum_quality",
        "minimum_confidence",
        "minimum_print_yield",
        "minimum_gross_margin",
    ):
        _unit_interval(quality.get(key), f"quality.{key}")
    _positive_integer(
        quality.get("minimum_blind_groups"), "quality.minimum_blind_groups"
    )
    _positive_integer(
        quality.get("minimum_games_per_group"),
        "quality.minimum_games_per_group",
    )


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load defaults, then merge an optional JSON file and narrow env overrides."""

    with DEFAULT_CONFIG_PATH.open(encoding="utf-8") as handle:
        config: dict[str, Any] = json.load(handle)
    with DEFAULT_LIBRARY_PATH.open(encoding="utf-8") as handle:
        library = json.load(handle)
    with DEFAULT_MARKET_SIGNALS_PATH.open(encoding="utf-8") as handle:
        market_signals = json.load(handle)
    config["knowledge"] = {
        "library": library,
        "market_signals": market_signals,
    }
    override: dict[str, Any] | None = None
    if path:
        with Path(path).open(encoding="utf-8") as handle:
            override = json.load(handle)
        if not isinstance(override, dict):
            raise ValueError("configuration root must be an object")
        config = _merge(config, override)
    _normalize_legacy_adapter_config(config, override)

    env_map: dict[str, tuple[str, str, Any]] = {
        "ALICE_DATABASE": ("runtime", "database", str),
        "ALICE_EFFECT_MODE": ("runtime", "effect_mode", str),
        "ALICE_AGENT_PROVIDER": ("agents", "provider", str),
        "ALICE_POLL_SECONDS": ("runtime", "poll_seconds", int),
    }
    for env_name, (section, key, cast) in env_map.items():
        if env_name in os.environ:
            config[section][key] = cast(os.environ[env_name])

    codex_env: dict[str, tuple[str, Any]] = {
        "ALICE_CODEX_BINARY": ("binary", str),
        "ALICE_CODEX_HOME": ("home", str),
        "ALICE_CODEX_MODEL": ("model", str),
        "ALICE_CODEX_EFFORT": ("effort", str),
    }
    for env_name, (key, cast) in codex_env.items():
        if env_name in os.environ:
            config["agents"]["codex"][key] = cast(os.environ[env_name])

    effect_mode = config["runtime"]["effect_mode"]
    if effect_mode not in {"dry-run", "draft", "live"}:
        raise ValueError("runtime.effect_mode must be dry-run, draft, or live")
    _validate_config(config)
    return config


def _normalize_legacy_adapter_config(
    config: dict[str, Any], override: Mapping[str, Any] | None
) -> None:
    """Read old Delivery configuration without keeping old names active."""

    adapters = config.get("adapters")
    if not isinstance(adapters, dict):
        return
    override_adapters = (
        override.get("adapters") if isinstance(override, Mapping) else None
    )
    if not isinstance(override_adapters, Mapping):
        override_adapters = {}

    legacy_command = override_adapters.get("factory_order_command")
    if "factory_order_command" in override_adapters:
        if (
            "delivery_command" in override_adapters
            and override_adapters.get("delivery_command") != legacy_command
        ):
            raise ValueError(
                "adapters.delivery_command conflicts with legacy "
                "adapters.factory_order_command"
            )
        adapters["delivery_command"] = copy.deepcopy(legacy_command)
    adapters.pop("factory_order_command", None)

    environments = adapters.get("command_allowed_environment")
    if not isinstance(environments, dict) or "factory_order" not in environments:
        return
    legacy_environment = environments["factory_order"]
    if (
        "delivery" in environments
        and environments["delivery"] != legacy_environment
    ):
        raise ValueError(
            "adapters.command_allowed_environment.delivery conflicts with legacy "
            "factory_order"
        )
    environments.setdefault("delivery", legacy_environment)
    del environments["factory_order"]


def resolve_runtime_paths(config: dict[str, Any], root: str | Path) -> dict[str, Any]:
    """Return a copy with runtime filesystem paths rooted at the project."""

    resolved = copy.deepcopy(config)
    root_path = Path(root).resolve()
    path = Path(resolved["runtime"]["database"])
    resolved["runtime"]["database"] = str(
        path if path.is_absolute() else root_path / path
    )
    codex_home = Path(resolved["agents"]["codex"]["home"])
    resolved["agents"]["codex"]["home"] = str(
        codex_home if codex_home.is_absolute() else root_path / codex_home
    )
    text2game = resolved["adapters"]["text2game"]
    for key in (
        "repo",
        "work_root",
        "vibe_workspace",
        "text2cad_repo",
        "cad_python",
        "slicer_binary",
        "slicer_profile",
        "codex_binary",
        "codex_home",
        "git_binary",
        "calibration_profile",
    ):
        raw = str(text2game.get(key) or "")
        if not raw:
            continue
        text2game_path = Path(raw).expanduser()
        text2game[key] = str(
            text2game_path
            if text2game_path.is_absolute()
            else root_path / text2game_path
        )
    page_builder = resolved["adapters"]["page_builder"]
    for key in ("workspace", "git_binary", "publishdesign_preflight_receipt"):
        raw = str(page_builder.get(key) or "")
        if not raw:
            continue
        page_path = Path(raw).expanduser()
        page_builder[key] = str(
            page_path if page_path.is_absolute() else root_path / page_path
        )
    return resolved


def default_runtime_root() -> Path:
    """Use the checkout when running from source, otherwise a writable state root."""

    if DATA_ROOT == SOURCE_DATA_ROOT:
        return SOURCE_ROOT
    xdg_state = os.environ.get("XDG_STATE_HOME")
    base = (
        Path(xdg_state).expanduser()
        if xdg_state
        else Path.home() / ".local" / "state"
    )
    return base / "autonomous-alice"
