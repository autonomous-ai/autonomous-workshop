"""A real ``ModelDoor`` backed by an actual tool-using agent process.

``doors.ModelDoor.run(role, request, budget_micros)`` already names the
contract: run one bounded model *or agent* role and return its structured
result. Nothing implements it for real anywhere in this repository.
``AgentSessionDoor`` closes that gap — it launches a caller-supplied,
headless coding-agent process (no hardcoded binary or vendor), bound to a
workspace created fresh for that one call, under a wall-clock bound and a
dollar budget, and reads back the one JSON result file the process is told
to write before it exits.

Per-role configuration (:class:`AgentRoleConfig`) owns everything about the
process's permission boundary: which tools it gets, which paths it may
touch, what (if anything) is pre-populated into its workspace, and its
wall-clock bound. The door builds the launched process's actual boundary
from that configuration — never from anything the role's request or the
process's own output claims about itself (see CONTRIBUTING.md — "An
inventor may strengthen a gate but must not create a bypass around a shared
floor").

The mechanism that actually starts and talks to the process
(:data:`ProcessLauncher`) is an injectable seam, mirroring ``_http.py``'s
``Transport``: a default, stdlib-only subprocess implementation ships here,
and a deterministic substitute (``tools/agent_door_fixture.py``) lets tests
and the showcase builder run every documented role with no real process and
no network.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from .errors import AgentSessionError, ContractError


def _string_tuple(value: Any, label: str) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Sequence):
        raise ContractError("%s must be a sequence of strings" % label)
    items = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ContractError("%s entries must be non-empty strings" % label)
        items.append(item)
    return tuple(items)


@dataclass(frozen=True)
class AgentRoleConfig:
    """Everything one role's launched process is allowed to be and do.

    ``tools`` and ``allowed_paths`` describe the process's permission
    boundary; ``workspace_files`` is content written into its fresh
    workspace before it starts. ``max_budget_micros``, if set, caps every
    call to this role regardless of the ``budget_micros`` a caller passes to
    :meth:`AgentSessionDoor.run`. ``required_result_fields`` names the
    top-level keys the role's result file must carry — a shape check, not a
    domain validation; the caller that parses the result into a typed record
    still applies its own strict rules.
    """

    tools: Sequence[str]
    allowed_paths: Sequence[str]
    wall_clock_seconds: int
    workspace_files: Mapping[str, bytes] = field(default_factory=dict)
    max_budget_micros: Optional[int] = None
    required_result_fields: Sequence[str] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "tools", _string_tuple(self.tools, "AgentRoleConfig tools")
        )
        object.__setattr__(
            self,
            "allowed_paths",
            _string_tuple(self.allowed_paths, "AgentRoleConfig allowed_paths"),
        )
        if (
            not isinstance(self.wall_clock_seconds, int)
            or isinstance(self.wall_clock_seconds, bool)
            or self.wall_clock_seconds <= 0
        ):
            raise ContractError(
                "AgentRoleConfig wall_clock_seconds must be a positive integer"
            )
        if not isinstance(self.workspace_files, Mapping):
            raise ContractError("AgentRoleConfig workspace_files must be a mapping")
        files: Dict[str, bytes] = {}
        for relative, content in self.workspace_files.items():
            if not isinstance(relative, str) or not relative.strip():
                raise ContractError(
                    "AgentRoleConfig workspace_files keys must be non-empty "
                    "relative paths"
                )
            if Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise ContractError(
                    "AgentRoleConfig workspace_files paths must stay inside "
                    "the workspace"
                )
            if not isinstance(content, bytes):
                raise ContractError(
                    "AgentRoleConfig workspace_files values must be bytes"
                )
            files[relative] = content
        object.__setattr__(self, "workspace_files", files)
        if self.max_budget_micros is not None and (
            not isinstance(self.max_budget_micros, int)
            or isinstance(self.max_budget_micros, bool)
            or self.max_budget_micros <= 0
        ):
            raise ContractError(
                "AgentRoleConfig max_budget_micros must be a positive integer "
                "or None"
            )
        object.__setattr__(
            self,
            "required_result_fields",
            _string_tuple(
                self.required_result_fields, "AgentRoleConfig required_result_fields"
            )
            if self.required_result_fields
            else (),
        )


@dataclass(frozen=True)
class ResolvedRoleAccess:
    """One call's actual permission boundary, handed to the launcher.

    The role's own static configuration merged with this call's effective
    budget ceiling — the launcher never sees the caller's raw
    ``budget_micros``, only the number it is actually bound by.
    """

    role: str
    tools: Sequence[str]
    allowed_paths: Sequence[str]
    wall_clock_seconds: int
    budget_micros: int


@dataclass(frozen=True)
class LaunchResult:
    """What a launcher reports about one process it ran to completion.

    ``spent_micros`` is the launcher's own best report of actual cost, when
    it can produce one; ``None`` means the launcher could not observe spend
    at all, and the door falls back to wall-clock as the only enforced
    bound.
    """

    exit_status: int
    stdout: str
    stderr: str
    spent_micros: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.exit_status, int) or isinstance(self.exit_status, bool):
            raise ContractError("LaunchResult exit_status must be an integer")
        if not isinstance(self.stdout, str) or not isinstance(self.stderr, str):
            raise ContractError("LaunchResult stdout and stderr must be strings")
        if self.spent_micros is not None and (
            not isinstance(self.spent_micros, int)
            or isinstance(self.spent_micros, bool)
            or self.spent_micros < 0
        ):
            raise ContractError(
                "LaunchResult spent_micros must be a non-negative integer or None"
            )


class LauncherTimedOut(Exception):
    """A launcher's way of reporting it killed an overrunning process.

    Raised by a :data:`ProcessLauncher` implementation, never by
    :class:`AgentSessionDoor` itself — only the launcher holds the running
    process and can actually terminate it.
    """


class LauncherOverBudget(Exception):
    """A launcher's way of reporting it killed an overspending process."""

    def __init__(self, spent_micros: int) -> None:
        super().__init__("launcher terminated an overspending process")
        self.spent_micros = spent_micros


# (role, request, resolved access, fresh workspace, result-file path) -> LaunchResult
ProcessLauncher = Callable[
    [str, Mapping[str, Any], ResolvedRoleAccess, Path, Path], LaunchResult
]


def _subprocess_launcher(launch_command: Sequence[str]) -> ProcessLauncher:
    """The default launcher: a plain stdlib subprocess, no vendor assumed.

    The role, the request (written to a file), and the resolved access
    configuration are handed to the process entirely through its
    environment and a request file — never through anything that could be
    mistaken for a shared floor the process itself controls. The process is
    expected to write its structured result to ``AGENT_DOOR_RESULT_FILE``
    before exiting; stdout and stderr are captured for diagnostics only and
    never parsed for the result.
    """

    def launcher(
        role: str,
        request: Mapping[str, Any],
        access: ResolvedRoleAccess,
        workspace: Path,
        result_file: Path,
    ) -> LaunchResult:
        request_file = workspace / "request.json"
        request_file.write_text(
            json.dumps(dict(request), sort_keys=True, ensure_ascii=False),
            encoding="utf-8",
        )
        env = dict(os.environ)
        env.update(
            {
                "AGENT_DOOR_ROLE": role,
                "AGENT_DOOR_REQUEST_FILE": str(request_file),
                "AGENT_DOOR_RESULT_FILE": str(result_file),
                "AGENT_DOOR_WORKSPACE": str(workspace),
                "AGENT_DOOR_TOOLS": ",".join(access.tools),
                "AGENT_DOOR_ALLOWED_PATHS": ",".join(access.allowed_paths),
                "AGENT_DOOR_BUDGET_MICROS": str(access.budget_micros),
            }
        )
        argv = list(launch_command) + [role]
        process = subprocess.Popen(
            argv,
            cwd=str(workspace),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = process.communicate(timeout=access.wall_clock_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise LauncherTimedOut()
        return LaunchResult(
            exit_status=process.returncode,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
        )

    return launcher


class AgentSessionDoor:
    """Run one named role at a time against a caller-configured agent process.

    Satisfies ``doors.ModelDoor``. ``launch_command`` is the argv prefix for
    the process to start — the door assumes no vendor or binary of its own,
    exactly as every existing HTTP adapter assumes no base URL. Construction
    is refused without one. ``role_configs`` binds each role this door will
    run to its own :class:`AgentRoleConfig`; a role with no entry is refused
    before any process is launched.
    """

    def __init__(
        self,
        launch_command: Sequence[str],
        role_configs: Mapping[str, AgentRoleConfig],
        *,
        launcher: Optional[ProcessLauncher] = None,
        workspace_root: Optional[Path] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if (
            isinstance(launch_command, (str, bytes))
            or not isinstance(launch_command, Sequence)
            or not launch_command
        ):
            raise ContractError(
                "AgentSessionDoor requires a non-empty launch command"
            )
        command = _string_tuple(launch_command, "AgentSessionDoor launch command")
        if not isinstance(role_configs, Mapping) or not role_configs:
            raise ContractError(
                "AgentSessionDoor requires at least one role configuration"
            )
        configs: Dict[str, AgentRoleConfig] = {}
        for role, config in role_configs.items():
            if not isinstance(role, str) or not role.strip():
                raise ContractError(
                    "AgentSessionDoor role names must be non-empty strings"
                )
            if not isinstance(config, AgentRoleConfig):
                raise ContractError(
                    "AgentSessionDoor role %r configuration must be an "
                    "AgentRoleConfig" % role
                )
            configs[role] = config
        self._launch_command = command
        self._role_configs = configs
        self._launcher = (
            launcher if launcher is not None else _subprocess_launcher(command)
        )
        self._workspace_root = (
            Path(workspace_root)
            if workspace_root is not None
            else Path(tempfile.mkdtemp(prefix="agent-session-door-"))
        )
        self._workspace_root.mkdir(parents=True, exist_ok=True)
        self._clock = clock

    def run(
        self, role: str, request: Mapping[str, Any], budget_micros: int
    ) -> Mapping[str, Any]:
        if not isinstance(role, str) or not role.strip():
            raise ContractError("AgentSessionDoor.run requires a non-empty role")
        if not isinstance(request, Mapping):
            raise ContractError("AgentSessionDoor.run requires a request mapping")
        if (
            type(budget_micros) is not int
            or isinstance(budget_micros, bool)
            or budget_micros <= 0
        ):
            raise ContractError(
                "AgentSessionDoor.run budget_micros must be a positive integer"
            )
        config = self._role_configs.get(role)
        if config is None:
            raise ContractError(
                "AgentSessionDoor has no configuration for role %r" % role
            )
        effective_budget = budget_micros
        if config.max_budget_micros is not None:
            effective_budget = min(effective_budget, config.max_budget_micros)

        workspace = self._workspace_root / uuid.uuid4().hex
        workspace.mkdir(mode=0o700)
        for relative, content in config.workspace_files.items():
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        result_file = workspace / "result.json"
        access = ResolvedRoleAccess(
            role,
            config.tools,
            config.allowed_paths,
            config.wall_clock_seconds,
            effective_budget,
        )

        started = self._clock()
        try:
            outcome = self._launcher(
                role, dict(request), access, workspace, result_file
            )
        except LauncherTimedOut as exc:
            raise AgentSessionError(
                role,
                "exceeded its %ds wall-clock bound" % config.wall_clock_seconds,
                elapsed_seconds=self._clock() - started,
            ) from exc
        except LauncherOverBudget as exc:
            raise AgentSessionError(
                role,
                "exceeded its %d-micros budget" % effective_budget,
                elapsed_seconds=self._clock() - started,
                spent_micros=exc.spent_micros,
            ) from exc
        except Exception as exc:
            raise AgentSessionError(
                role,
                "launcher failed: %s" % exc,
                elapsed_seconds=self._clock() - started,
            ) from exc
        elapsed = self._clock() - started

        if not isinstance(outcome, LaunchResult):
            raise AgentSessionError(
                role,
                "launcher returned %r instead of a LaunchResult" % (outcome,),
                elapsed_seconds=elapsed,
            )
        if (
            outcome.spent_micros is not None
            and outcome.spent_micros > effective_budget
        ):
            raise AgentSessionError(
                role,
                "spent %d micros, exceeding its %d-micros budget"
                % (outcome.spent_micros, effective_budget),
                elapsed_seconds=elapsed,
                spent_micros=outcome.spent_micros,
            )
        if outcome.exit_status != 0:
            raise AgentSessionError(
                role,
                "process exited with status %d: %s"
                % (outcome.exit_status, outcome.stderr[:500]),
                elapsed_seconds=elapsed,
                spent_micros=outcome.spent_micros,
            )
        if not result_file.is_file():
            raise AgentSessionError(
                role,
                "produced no structured result at the file the door named",
                elapsed_seconds=elapsed,
                spent_micros=outcome.spent_micros,
            )
        try:
            parsed = json.loads(result_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            raise AgentSessionError(
                role,
                "result file could not be parsed as JSON: %s" % exc,
                elapsed_seconds=elapsed,
                spent_micros=outcome.spent_micros,
            ) from exc
        if not isinstance(parsed, Mapping):
            raise AgentSessionError(
                role,
                "result file is not a JSON object",
                elapsed_seconds=elapsed,
                spent_micros=outcome.spent_micros,
            )
        missing = [
            name for name in config.required_result_fields if name not in parsed
        ]
        if missing:
            raise AgentSessionError(
                role,
                "result is missing %s, which its declared shape requires"
                % ", ".join(missing),
                elapsed_seconds=elapsed,
                spent_micros=outcome.spent_micros,
            )
        return {
            "result": dict(parsed),
            "elapsed_seconds": elapsed,
            "spent_micros": outcome.spent_micros,
        }


__all__ = [
    "AgentRoleConfig",
    "AgentSessionDoor",
    "LaunchResult",
    "LauncherOverBudget",
    "LauncherTimedOut",
    "ProcessLauncher",
    "ResolvedRoleAccess",
]
