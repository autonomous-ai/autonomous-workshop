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
_MANAGER_ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,31}$")


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
        if type(self.experimental) is not bool:
            raise ContractError("Workshop Manager experimental flag is invalid")

    def agent_path(self, inventor_id: str) -> str:
        if not isinstance(inventor_id, str) or not inventor_id:
            raise ContractError("Inventor id is invalid for a Manager projection")
        return "%s/%s%s" % (self.agent_directory, inventor_id, self.agent_suffix)


_SPECS = {
    "codex": ManagerRuntimeSpec(
        manager_id="codex",
        display_name="Codex",
        agent_directory=".codex/agents",
        agent_suffix=".toml",
        session_checkpoint_name="codex-session.json",
    ),
    "claude": ManagerRuntimeSpec(
        manager_id="claude",
        display_name="Claude Code",
        agent_directory=".claude/agents",
        agent_suffix=".md",
        session_checkpoint_name="claude-session.json",
        experimental=True,
    ),
    "grok": ManagerRuntimeSpec(
        manager_id="grok",
        display_name="Grok Build",
        agent_directory=".grok/agents",
        agent_suffix=".md",
        session_checkpoint_name="grok-session.json",
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


def manager_project_bytes(spec: ManagerRuntimeSpec) -> bytes:
    """Return the exact host-written MANAGER.json bytes for one run."""

    payload = {
        "schema_version": 1,
        "kind": MANAGER_PROJECT_KIND,
        "manager_id": spec.manager_id,
        "display_name": spec.display_name,
        "agent_directory": spec.agent_directory,
        "agent_suffix": spec.agent_suffix,
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
    "ManagerRuntimeSpec",
    "NativeManagerInvocationError",
    "NativeManagerRecoverableError",
    "NativeSessionLauncher",
    "NativeSessionOutcome",
    "manager_launcher",
    "manager_project_bytes",
    "manager_spec",
]
