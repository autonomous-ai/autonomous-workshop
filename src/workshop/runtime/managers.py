"""Registry and narrow port for native Workshop Manager runtimes.

The Workflow host depends on this module rather than on a vendor launcher.
Each adapter owns its CLI protocol, private session checkpoint, sandbox policy,
and project-native agent layout.  Product contracts and lifecycle checkpoints
remain manager-neutral.
"""

from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping, Protocol, runtime_checkable

from workshop.errors import ContractError


DEFAULT_MANAGER_ID = "codex"
MANAGER_PROJECT_KIND = "autonomous-workshop.manager-project"
MANAGER_PROJECT_PATH = "MANAGER.json"
CLAUDE_PLUGIN_MANIFEST_PATH = ".claude/.claude-plugin/plugin.json"
_MANAGER_ID = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
_INVENTOR_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")


class NativeManagerInvocationError(RuntimeError):
    """A selected native Manager could not complete its bounded turn."""


@runtime_checkable
class NativeSessionOutcome(Protocol):
    """Redacted result shared by every concrete Manager launcher."""

    def to_dict(self) -> Mapping[str, Any]: ...


@runtime_checkable
class NativeSessionLauncher(Protocol):
    """One Wish-wide native session implemented by a concrete runtime."""

    manager_id: str
    session_checkpoint_name: str

    def start(self, **arguments: Any) -> NativeSessionOutcome: ...

    def resume(self, **arguments: Any) -> NativeSessionOutcome: ...

    def goal_disposition(self, **arguments: Any) -> str: ...

    def acknowledge_goal(self, **arguments: Any) -> None: ...


@dataclass(frozen=True)
class ManagerRuntimeSpec:
    """Deterministic project and session conventions for one Manager."""

    manager_id: str
    display_name: str
    agent_directory: str
    agent_suffix: str
    skill_directory: str
    instruction_entrypoint: str
    session_checkpoint_name: str
    native_work_control: str = "goal"
    goal_prompt_style: str = "instruction"
    agent_namespace: str | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.manager_id, str)
            or _MANAGER_ID.fullmatch(self.manager_id) is None
        ):
            raise ContractError("Workshop Manager id is invalid")
        if (
            not isinstance(self.display_name, str)
            or not self.display_name
            or self.display_name != self.display_name.strip()
            or len(self.display_name) > 64
        ):
            raise ContractError("Workshop Manager display name is invalid")
        for value, label in (
            (self.agent_directory, "agent directory"),
            (self.skill_directory, "skill directory"),
            (self.instruction_entrypoint, "instruction entrypoint"),
            (self.session_checkpoint_name, "session checkpoint name"),
        ):
            if (
                not isinstance(value, str)
                or not value
            ):
                raise ContractError("Workshop Manager %s is invalid" % label)
            path = PurePosixPath(value)
            if (
                path.is_absolute()
                or ".." in path.parts
                or path.as_posix() != value
            ):
                raise ContractError("Workshop Manager %s is invalid" % label)
        if self.agent_suffix not in (".toml", ".md"):
            raise ContractError("Workshop Manager agent suffix is invalid")
        if self.native_work_control != "goal":
            raise ContractError("Workshop Manager work-control convention is invalid")
        if self.goal_prompt_style not in ("instruction", "slash-command"):
            raise ContractError("Workshop Manager Goal prompt style is invalid")
        if self.agent_namespace is not None and (
            not isinstance(self.agent_namespace, str)
            or _MANAGER_ID.fullmatch(self.agent_namespace) is None
        ):
            raise ContractError("Workshop Manager agent namespace is invalid")

    def agent_path(self, inventor_id: str) -> str:
        if (
            not isinstance(inventor_id, str)
            or _INVENTOR_ID.fullmatch(inventor_id) is None
        ):
            raise ContractError("Inventor id is invalid for a Manager projection")
        return "%s/%s%s" % (
            self.agent_directory,
            inventor_id,
            self.agent_suffix,
        )

    def skill_path(self, skill_name: str, relative: str = "SKILL.md") -> str:
        if (
            not isinstance(skill_name, str)
            or _INVENTOR_ID.fullmatch(skill_name) is None
        ):
            raise ContractError("skill name is invalid for a Manager projection")
        if not isinstance(relative, str) or not relative:
            raise ContractError("skill-relative path is invalid")
        selected = PurePosixPath(relative)
        if selected.is_absolute() or ".." in selected.parts:
            raise ContractError("skill-relative path is invalid")
        return (PurePosixPath(self.skill_directory) / skill_name / selected).as_posix()

    def project_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": MANAGER_PROJECT_KIND,
            "manager": self.manager_id,
            "display_name": self.display_name,
            "instruction_entrypoint": self.instruction_entrypoint,
            "agent_directory": self.agent_directory,
            "skill_directory": self.skill_directory,
            "native_work_control": self.native_work_control,
            "agent_namespace": self.agent_namespace,
        }

    def project_bytes(self) -> bytes:
        return (
            json.dumps(
                self.project_dict(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )

    def instruction_path(self, path: str) -> bool:
        if not isinstance(path, str):
            return False
        return (
            path in {"AGENTS.md", MANAGER_PROJECT_PATH, self.instruction_entrypoint}
            or path.startswith(self.agent_directory + "/")
            or path.startswith(self.skill_directory + "/")
        )


_MANAGER_SPECS = {
    "codex": ManagerRuntimeSpec(
        manager_id="codex",
        display_name="Codex",
        agent_directory=".codex/agents",
        agent_suffix=".toml",
        skill_directory=".agents/skills",
        instruction_entrypoint="AGENTS.md",
        session_checkpoint_name="codex-session.json",
    ),
    "claude": ManagerRuntimeSpec(
        manager_id="claude",
        display_name="Claude Code",
        agent_directory=".claude/agents",
        agent_suffix=".md",
        skill_directory=".claude/skills",
        instruction_entrypoint="CLAUDE.md",
        session_checkpoint_name="claude-session.json",
        goal_prompt_style="slash-command",
        agent_namespace="autonomous-workshop",
    ),
    "grok": ManagerRuntimeSpec(
        manager_id="grok",
        display_name="Grok Build",
        agent_directory=".grok/agents",
        agent_suffix=".md",
        skill_directory=".grok/skills",
        instruction_entrypoint="AGENTS.md",
        session_checkpoint_name="grok-session.json",
        goal_prompt_style="slash-command",
    ),
}
SUPPORTED_MANAGER_IDS = tuple(_MANAGER_SPECS)
_MANAGER_LAUNCHERS = {
    "codex": ("workshop.runtime.codex", "CodexNativeSessionLauncher"),
    "claude": ("workshop.runtime.claude", "ClaudeNativeSessionLauncher"),
    "grok": ("workshop.runtime.grok", "GrokNativeSessionLauncher"),
}


def manager_spec(manager_id: str = DEFAULT_MANAGER_ID) -> ManagerRuntimeSpec:
    """Return one registered Manager spec or fail before creating run state."""

    if not isinstance(manager_id, str):
        raise ContractError("Workshop Manager must be text")
    try:
        return _MANAGER_SPECS[manager_id]
    except KeyError:
        raise ContractError(
            "unsupported Workshop Manager %r; choose one of: %s"
            % (manager_id, ", ".join(SUPPORTED_MANAGER_IDS))
        ) from None


def parse_manager_project_bytes(content: bytes) -> ManagerRuntimeSpec:
    """Validate one canonical immutable ``MANAGER.json`` projection."""

    if not isinstance(content, bytes) or not 1 <= len(content) <= 8 * 1024:
        raise ContractError("Manager project binding must be bounded bytes")
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Manager project binding must be UTF-8 JSON") from exc
    if not isinstance(value, Mapping):
        raise ContractError("Manager project binding must contain one object")
    manager_id = value.get("manager")
    spec = manager_spec(manager_id)
    if dict(value) != spec.project_dict() or content != spec.project_bytes():
        raise ContractError("Manager project binding is not canonical")
    return spec


def manager_support_files(manager_id: str) -> tuple[tuple[str, bytes], ...]:
    """Return immutable adapter metadata needed by one runtime projection."""

    spec = manager_spec(manager_id)
    if spec.manager_id != "claude":
        return ()
    manifest = {
        "name": spec.agent_namespace,
        "description": "Host-projected Workshop runtime",
        "version": "1.0.0",
        "author": {"name": "Autonomous Workshop"},
    }
    content = (
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    return ((CLAUDE_PLUGIN_MANIFEST_PATH, content),)


def manager_launcher(manager_id: str) -> NativeSessionLauncher:
    """Construct the selected concrete launcher through one lazy registry seam."""

    spec = manager_spec(manager_id)
    try:
        module_name, class_name = _MANAGER_LAUNCHERS[spec.manager_id]
        factory: Any = getattr(importlib.import_module(module_name), class_name)
    except (AttributeError, ImportError, KeyError):
        raise ContractError("Workshop Manager registry is incomplete")
    launcher: Any = factory()
    if (
        not isinstance(launcher, NativeSessionLauncher)
        or launcher.manager_id != spec.manager_id
        or launcher.session_checkpoint_name != spec.session_checkpoint_name
    ):
        raise ContractError("Workshop Manager adapter does not satisfy its registry")
    return launcher


__all__ = [
    "DEFAULT_MANAGER_ID",
    "CLAUDE_PLUGIN_MANIFEST_PATH",
    "MANAGER_PROJECT_KIND",
    "MANAGER_PROJECT_PATH",
    "SUPPORTED_MANAGER_IDS",
    "ManagerRuntimeSpec",
    "NativeManagerInvocationError",
    "NativeSessionLauncher",
    "NativeSessionOutcome",
    "manager_launcher",
    "manager_support_files",
    "manager_spec",
    "parse_manager_project_bytes",
]
