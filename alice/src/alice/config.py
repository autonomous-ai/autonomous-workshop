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
        "factory_order",
        "print_fulfillment",
    }
)
_ENVIRONMENT_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
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

    page_builder = adapters.get("page_builder")
    vibe = adapters.get("vibe")
    if not isinstance(page_builder, Mapping) or not isinstance(vibe, Mapping):
        raise ValueError("adapters.page_builder and adapters.vibe must be objects")
    page_environment = set(
        _environment_names(
            page_builder.get("allowed_environment"),
            "adapters.page_builder.allowed_environment",
        )
    )
    adapter_environment.update(page_environment)
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
    if path:
        with Path(path).open(encoding="utf-8") as handle:
            override = json.load(handle)
        if not isinstance(override, dict):
            raise ValueError("configuration root must be an object")
        config = _merge(config, override)

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
