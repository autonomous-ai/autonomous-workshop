"""Registry and narrow port for native Workshop Manager runtimes.

The Workflow host depends on this module rather than on a vendor launcher.
Each adapter owns its CLI protocol, private session checkpoint, sandbox policy,
and native agent layout. Product contracts, effort routes, and lifecycle
checkpoints remain manager-neutral.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Callable, Mapping, Optional, Protocol, runtime_checkable

from workshop.errors import ContractError


DEFAULT_MANAGER_ID = "codex"
MANAGER_PROJECT_KIND = "autonomous-workshop.manager-project"
MANAGER_PROJECT_PATH = "MANAGER.json"
SUPPORTED_REASONING_EFFORTS = ("low", "medium", "high", "xhigh")
_MANAGER_ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
_MODEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


class NativeManagerInvocationError(RuntimeError):
    """A selected native Manager could not complete its bounded turn."""


class NativeManagerRecoverableError(NativeManagerInvocationError):
    """A typed timeout or provider disconnect that may resume the same session."""


@runtime_checkable
class NativeSessionOutcome(Protocol):
    """Redacted result shared by every concrete Manager launcher."""

    def to_dict(self) -> Mapping[str, Any]: ...


@runtime_checkable
class NativeSessionLauncher(Protocol):
    """One Wish-wide native session implemented by a concrete runtime."""

    manager_id: str
    session_checkpoint_name: str

    def start(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Any,
        host_state_root: Any,
        prompt: str,
        activity_observer: Optional[Callable[[str], None]] = None,
        finalization_marker: Any = None,
    ) -> NativeSessionOutcome: ...

    def resume(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Any,
        host_state_root: Any,
        prompt: str,
        activity_observer: Optional[Callable[[str], None]] = None,
        finalization_marker: Any = None,
    ) -> NativeSessionOutcome: ...


@dataclass(frozen=True)
class ManagerRuntimeSpec:
    """Deterministic project and session conventions for one Manager."""

    manager_id: str
    display_name: str
    agent_directory: str
    agent_suffix: str
    session_checkpoint_name: str
    default_model: str
    default_reasoning_effort: Optional[str]
    experimental: bool = False

    def __post_init__(self) -> None:
        if (
            not isinstance(self.manager_id, str)
            or _MANAGER_ID_RE.fullmatch(self.manager_id) is None
        ):
            raise ContractError("Workshop Manager id is invalid")
        if (
            not isinstance(self.display_name, str)
            or not self.display_name.strip()
            or len(self.display_name) > 64
        ):
            raise ContractError("Workshop Manager display name is invalid")
        for value, label in (
            (self.agent_directory, "agent directory"),
            (self.session_checkpoint_name, "session checkpoint name"),
        ):
            if not isinstance(value, str) or not value:
                raise ContractError("Workshop Manager %s is invalid" % label)
            path = PurePosixPath(value)
            if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
                raise ContractError("Workshop Manager %s is invalid" % label)
        if self.agent_suffix not in (".toml", ".md"):
            raise ContractError("Workshop Manager agent suffix is invalid")
        _model_id(self.default_model)
        if (
            self.default_reasoning_effort is not None
            and self.default_reasoning_effort not in SUPPORTED_REASONING_EFFORTS
        ):
            raise ContractError("Workshop Manager reasoning effort is invalid")
        if type(self.experimental) is not bool:
            raise ContractError("Workshop Manager experimental flag is invalid")

    def agent_path(self, inventor_id: str) -> str:
        if not isinstance(inventor_id, str) or not inventor_id:
            raise ContractError("Inventor id is invalid for a Manager projection")
        return "%s/%s%s" % (self.agent_directory, inventor_id, self.agent_suffix)


@dataclass(frozen=True)
class ManagerRuntimeSelection:
    """One canonical, immutable native-runtime choice for a new run."""

    spec: ManagerRuntimeSpec
    model: str
    reasoning_effort: Optional[str]


def _model_id(value: Any) -> str:
    if not isinstance(value, str) or _MODEL_ID_RE.fullmatch(value) is None:
        raise ContractError("Workshop Manager model is invalid")
    return value


_MODEL_ALIASES = {
    "codex": {
        "astra": "gpt-6-astra",
        "sol": "gpt-5.6-sol",
        "terra": "gpt-5.6-terra",
        "luna": "gpt-5.6-luna",
    },
    "claude": {
        "opus": "claude-opus-5",
        "opus-5": "claude-opus-5",
    },
}


_SPECS = {
    "codex": ManagerRuntimeSpec(
        manager_id="codex",
        display_name="Codex",
        agent_directory=".codex/agents",
        agent_suffix=".toml",
        session_checkpoint_name="codex-session.json",
        default_model="gpt-5.6-sol",
        default_reasoning_effort="medium",
    ),
    "claude": ManagerRuntimeSpec(
        manager_id="claude",
        display_name="Claude Code",
        agent_directory=".claude/agents",
        agent_suffix=".md",
        session_checkpoint_name="claude-session.json",
        default_model="claude-opus-5",
        default_reasoning_effort="medium",
        experimental=True,
    ),
    "grok": ManagerRuntimeSpec(
        manager_id="grok",
        display_name="Grok Build",
        agent_directory=".grok/agents",
        agent_suffix=".md",
        session_checkpoint_name="grok-session.json",
        default_model="grok-4.6",
        default_reasoning_effort=None,
        experimental=True,
    ),
}

SUPPORTED_MANAGER_IDS = tuple(_SPECS)
_LAUNCHERS = {
    "codex": "workshop.runtime.codex.CodexNativeSessionLauncher",
    "claude": "workshop.runtime.claude.ClaudeNativeSessionLauncher",
    "grok": "workshop.runtime.grok.GrokNativeSessionLauncher",
}


def manager_spec(value: Any) -> ManagerRuntimeSpec:
    if not isinstance(value, str) or value not in _SPECS:
        raise ContractError(
            "Workshop Manager must be one of: %s" % ", ".join(SUPPORTED_MANAGER_IDS)
        )
    return _SPECS[value]


def manager_runtime_selection(
    manager_id: Any,
    *,
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
) -> ManagerRuntimeSelection:
    """Resolve defaults and aliases into one manager-specific runtime choice."""

    spec = manager_spec(manager_id)
    selected_model = spec.default_model if model is None else _model_id(model)
    selected_model = _MODEL_ALIASES.get(spec.manager_id, {}).get(
        selected_model, selected_model
    )
    selected_effort = (
        spec.default_reasoning_effort
        if reasoning_effort is None
        else reasoning_effort
    )
    if selected_effort is not None and selected_effort not in SUPPORTED_REASONING_EFFORTS:
        raise ContractError(
            "Workshop Manager reasoning effort must be one of: %s"
            % ", ".join(SUPPORTED_REASONING_EFFORTS)
        )
    if spec.default_reasoning_effort is None and selected_effort is not None:
        raise ContractError(
            "%s does not expose a Workshop reasoning-effort control"
            % spec.display_name
        )
    if (
        spec.manager_id == "codex"
        and selected_model not in frozenset(_MODEL_ALIASES["codex"].values())
    ):
        raise ContractError(
            "Workshop Codex model must be astra, sol, terra, luna, or its full model id"
        )
    if spec.manager_id == "grok" and selected_model != spec.default_model:
        raise ContractError("Workshop Grok model must be %s" % spec.default_model)
    return ManagerRuntimeSelection(spec, selected_model, selected_effort)


def manager_project_bytes(
    value: ManagerRuntimeSpec | ManagerRuntimeSelection,
) -> bytes:
    """Return the exact host-written MANAGER.json bytes for one run."""

    selection = (
        manager_runtime_selection(value.manager_id)
        if isinstance(value, ManagerRuntimeSpec)
        else value
    )
    if not isinstance(selection, ManagerRuntimeSelection):
        raise ContractError("Workshop Manager selection is invalid")
    canonical = manager_runtime_selection(
        selection.spec.manager_id,
        model=selection.model,
        reasoning_effort=selection.reasoning_effort,
    )
    if canonical != selection:
        raise ContractError("Workshop Manager selection is not canonical")
    spec = selection.spec

    payload = {
        "schema_version": 2,
        "kind": MANAGER_PROJECT_KIND,
        "manager_id": spec.manager_id,
        "display_name": spec.display_name,
        "agent_directory": spec.agent_directory,
        "agent_suffix": spec.agent_suffix,
        "model": selection.model,
        "reasoning_effort": selection.reasoning_effort,
        "experimental": spec.experimental,
    }
    return (
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def parse_manager_project_bytes(
    source: bytes,
) -> tuple[ManagerRuntimeSpec, Optional[str], Optional[str]]:
    """Parse a hash-verified MANAGER.json, including schema-v1 compatibility."""

    try:
        payload = json.loads(source.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Workshop Manager project is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ContractError("Workshop Manager project must contain one object")
    schema_version = payload.get("schema_version")
    common_fields = {
        "schema_version",
        "kind",
        "manager_id",
        "display_name",
        "agent_directory",
        "agent_suffix",
        "experimental",
    }
    expected_fields = (
        common_fields
        if schema_version == 1
        else common_fields | {"model", "reasoning_effort"}
    )
    if schema_version not in (1, 2) or set(payload) != expected_fields:
        raise ContractError("Workshop Manager project fields are invalid")
    if payload.get("kind") != MANAGER_PROJECT_KIND:
        raise ContractError("Workshop Manager project kind is invalid")
    spec = manager_spec(payload.get("manager_id"))
    expected_metadata = {
        "display_name": spec.display_name,
        "agent_directory": spec.agent_directory,
        "agent_suffix": spec.agent_suffix,
        "experimental": spec.experimental,
    }
    if any(payload.get(name) != value for name, value in expected_metadata.items()):
        raise ContractError("Workshop Manager project binding is invalid")
    if schema_version == 1:
        return spec, None, None
    selection = manager_runtime_selection(
        spec.manager_id,
        model=payload.get("model"),
        reasoning_effort=payload.get("reasoning_effort"),
    )
    if (
        selection.model != payload["model"]
        or selection.reasoning_effort != payload["reasoning_effort"]
    ):
        raise ContractError("Workshop Manager project is not canonical")
    return spec, selection.model, selection.reasoning_effort


def manager_launcher(manager_id: str, **kwargs: Any) -> NativeSessionLauncher:
    """Construct the frozen Manager's launcher. Unknown or unloadable ids fail closed."""

    spec = manager_spec(manager_id)
    qualified = _LAUNCHERS[spec.manager_id]
    module_name, class_name = qualified.rsplit(".", 1)
    try:
        module = __import__(module_name, fromlist=[class_name])
        launcher_type = getattr(module, class_name)
    except (ImportError, AttributeError) as exc:
        raise ContractError(
            "Workshop Manager %s is not executable" % spec.display_name
        ) from exc
    launcher = launcher_type(**kwargs)
    if (
        getattr(launcher, "manager_id", None) != spec.manager_id
        or getattr(launcher, "session_checkpoint_name", None)
        != spec.session_checkpoint_name
    ):
        raise ContractError(
            "Workshop Manager %s launcher binding is invalid" % spec.display_name
        )
    return launcher


__all__ = [
    "DEFAULT_MANAGER_ID",
    "MANAGER_PROJECT_KIND",
    "MANAGER_PROJECT_PATH",
    "SUPPORTED_MANAGER_IDS",
    "SUPPORTED_REASONING_EFFORTS",
    "ManagerRuntimeSpec",
    "ManagerRuntimeSelection",
    "NativeManagerInvocationError",
    "NativeManagerRecoverableError",
    "NativeSessionLauncher",
    "NativeSessionOutcome",
    "manager_launcher",
    "parse_manager_project_bytes",
    "manager_project_bytes",
    "manager_runtime_selection",
    "manager_spec",
]
