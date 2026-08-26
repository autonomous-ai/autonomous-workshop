"""One whole-run native Grok Build session launcher.

Grok Build is a peer Workshop Manager, not a Python agent framework.  This
adapter translates the shared Workshop contract into Grok's pinned CLI,
session, Goal, project-agent, and sandbox protocols.  Grok retains all product
reasoning and native subagent work; the Workshop host retains durable state,
deterministic gates, budgets, and external effects.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from workshop.errors import ContractError
from workshop.runtime.managers import NativeManagerInvocationError
from workshop.runtime.project_boundary import PRODUCT_RUN_ROOT_MARKER


PINNED_GROK_NATIVE_RUNTIME_VERSION = "1.0.5 (5115b46bc909)"
MINIMUM_GROK_NATIVE_RUNTIME_VERSION = (1, 0, 5)
GROK_MODEL = "grok-build"
GROK_PERMISSION_MODE = "dontAsk"
GROK_SESSION_CHECKPOINT_KIND = "autonomous-workshop-native-grok-session"
GROK_SESSION_CHECKPOINT_NAME = "grok-session.json"
GROK_GOAL_CHECKPOINT_KIND = "autonomous-workshop-native-grok-goal"
GROK_GOAL_CHECKPOINT_NAME = "grok-goal.json"
GROK_PRIVATE_HOME_NAME = "grok-home"
GROK_NEUTRAL_HOME_NAME = "grok-neutral-home"
GROK_PRIVATE_POLICY_NAME = "grok-policy"
GROK_PRIVATE_TEMP_NAME = "grok-tmp"
GROK_ROOT_AGENT_NAME = "workshop-manager.md"
GROK_GOAL_RESUME_PROMPT = "/goal resume"
GROK_GOAL_STATUS_PROMPT = "/goal status"
DEFAULT_GROK_TIMEOUT_SECONDS = 1_200
DEFAULT_GROK_MAX_TURNS = 128
MAX_GROK_EVENT_STREAM_BYTES = 2 * 1024 * 1024
MAX_GROK_STDERR_BYTES = 256 * 1024
MAX_GROK_PROMPT_BYTES = 1 * 1024 * 1024
MAX_GROK_GOAL_CONDITION_CHARS = 4_000
MAX_GROK_SESSION_CHECKPOINT_BYTES = 64 * 1024
MAX_GROK_POLICY_FILE_BYTES = 256 * 1024
MAX_GROK_PROJECTION_FILE_BYTES = 4 * 1024 * 1024
MAX_GROK_PROJECTION_FILES = 256
MAX_GROK_PROJECTION_BYTES = 4 * 1024 * 1024
MAX_GROK_INSPECT_BYTES = 2 * 1024 * 1024
_PROCESS_EXIT_GRACE_SECONDS = 0.5
_GOAL_STAGE = re.compile(r"^(match|invent|make|playtest|release)$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STATUS_COMPLETE = re.compile(r"(?m)^Status: Complete \| Phase: [^\r\n]{1,128}$")


# Grok 1.0.5 can silently retain its default tools when a requested tool name
# does not resolve.  The root profile disables default injection, the CLI
# repeats the allowlist, and every live turn must attest this exact roster.
GROK_ALLOWED_TOOLS = (
    "run_terminal_command",
    "read_file",
    "search_replace",
    "list_dir",
    "grep",
    "todo_write",
    "spawn_subagent",
    "get_command_or_subagent_output",
    "wait_commands_or_subagents",
    "kill_command_or_subagent",
    "update_goal",
)
GROK_DISALLOWED_TOOLS = (
    "search_tool",
    "use_tool",
    "workflow",
    "scheduler_create",
    "scheduler_list",
    "scheduler_update",
    "scheduler_delete",
    "monitor_create",
    "monitor_list",
    "monitor_update",
    "monitor_delete",
    "web_search",
    "web_fetch",
    "generate_image",
    "memory",
)
GROK_SUBPROCESS_ENVIRONMENT_ALLOWLIST = (
    "PATH",
    "XAI_API_KEY",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TERM",
    "TMPDIR",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
)
_GROK_STATIC_ENVIRONMENT = (
    ("GROK_DISABLE_AUTOUPDATER", "1"),
    ("GROK_TELEMETRY_ENABLED", "false"),
    ("GROK_TELEMETRY_TRACE_UPLOAD", "false"),
    ("DISABLE_TELEMETRY", "1"),
    ("GROK_EXTERNAL_OTEL", "false"),
    ("GROK_CRASH_HANDLER", "false"),
    ("GROK_WORKFLOWS", "1"),
)
_IMMUTABLE_RUN_DIRECTORIES = (
    ".grok",
    ".git",
)
_IMMUTABLE_RUN_FILES = (
    PRODUCT_RUN_ROOT_MARKER,
    "AGENTS.md",
    "MANAGER.json",
    "STAGE.json",
    "WISH.json",
)
_STREAM_EVENT_TYPES = frozenset(
    (
        "text",
        "thought",
        "tool_call",
        "tool_call_update",
        "plan",
        "available_commands",
        "usage",
        "auto_compact_started",
        "auto_compact_completed",
        "auto_continue_completed",
        "image_compressed",
        "end",
    )
)
_STATUS_EVENT_TYPES = frozenset(("text", "available_commands", "usage", "end"))


class GrokInvocationError(NativeManagerInvocationError):
    """Grok Build could not complete an attested native turn."""


class _GrokProcessNotSpawned(GrokInvocationError):
    """Grok provably could not receive this invocation's argv prompt."""


def grok_supports_native_workshop(version: str) -> bool:
    """Return whether the exact audited Grok Build is selected."""

    return isinstance(version, str) and version == PINNED_GROK_NATIVE_RUNTIME_VERSION


def grok_subprocess_environment(
    source: Optional[Mapping[str, str]] = None,
    *,
    allowlist: Optional[Sequence[str]] = None,
) -> Mapping[str, str]:
    """Keep only Grok authentication and non-secret runtime inputs."""

    names = (
        GROK_SUBPROCESS_ENVIRONMENT_ALLOWLIST
        if allowlist is None
        else tuple(allowlist)
    )
    if (
        len(names) != len(set(names))
        or any(
            not isinstance(name, str)
            or not name
            or name not in GROK_SUBPROCESS_ENVIRONMENT_ALLOWLIST
            for name in names
        )
    ):
        raise ValueError("Grok subprocess environment allowlist is invalid")
    values = os.environ if source is None else source
    return {
        name: value
        for name in names
        if isinstance((value := values.get(name)), str) and value
    }


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Grok session state must be finite JSON") from exc


def _sha256_json(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ContractError("%s must be a lowercase sha256" % label)
    return value


def _bounded_identifier(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 256
        or value != value.strip()
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be a bounded identifier" % label)
    return value


def _canonical_session_id(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 64:
        raise ContractError("Grok session checkpoint identity is invalid")
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ContractError("Grok session checkpoint identity is invalid") from exc
    canonical = str(parsed)
    if value != canonical:
        raise ContractError("Grok session checkpoint identity is invalid")
    return canonical


def _path_sha256(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()


def _resolve_run_root(value: Path) -> Path:
    requested = Path(value)
    if not requested.is_absolute() or requested.is_symlink():
        raise ContractError("Grok native run root must be an absolute real directory")
    try:
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise ContractError("Grok native run root must already exist") from exc
    if requested != root or not root.is_dir():
        raise ContractError("Grok native run root must not contain symlinks")
    return root


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_host_state_root(value: Path, run_root: Path) -> Path:
    requested = Path(value)
    if not requested.is_absolute() or requested.is_symlink():
        raise ContractError("Grok host state root must be an absolute real directory")
    try:
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise ContractError("Grok host state root must already exist") from exc
    if requested != root or not root.is_dir():
        raise ContractError("Grok host state root must not contain symlinks")
    if _is_within(root, run_root) or _is_within(run_root, root):
        raise ContractError("Grok host state root and run root must not overlap")
    if stat.S_IMODE(root.stat().st_mode) != 0o700:
        raise ContractError("Grok host state root permissions must be 0700")
    return root


def _validated_prompt(value: Any) -> str:
    if not isinstance(value, str) or not value.startswith("/goal ") or "\x00" in value:
        raise ContractError("Grok native session prompt must invoke /goal")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise ContractError("Grok native session prompt must be UTF-8") from exc
    condition = value.removeprefix("/goal ")
    if (
        size > MAX_GROK_PROMPT_BYTES
        or not condition.strip()
        or len(condition) > MAX_GROK_GOAL_CONDITION_CHARS
        or any(ord(character) < 32 and character not in "\n\t" for character in condition)
    ):
        raise ContractError("Grok native Goal condition is invalid")
    return value


def _validated_goal_binding(stage: Any, digest: Any) -> tuple[str, str]:
    if not isinstance(stage, str) or _GOAL_STAGE.fullmatch(stage) is None:
        raise ContractError("Grok native Goal stage is invalid")
    return stage, _require_sha256(digest, "Grok native Goal stage checkpoint sha256")


def _read_limited_regular(path: Path, maximum: int, label: str) -> bytes:
    try:
        identity = path.lstat()
    except OSError as exc:
        raise ContractError("%s is missing" % label) from exc
    if path.is_symlink() or not stat.S_ISREG(identity.st_mode):
        raise ContractError("%s must be a regular file" % label)
    if not 1 <= identity.st_size <= maximum:
        raise ContractError("%s size is invalid" % label)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ContractError("%s cannot be read safely" % label) from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (identity.st_dev, identity.st_ino)
        ):
            raise ContractError("%s changed while opening" % label)
        chunks: list[bytes] = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            len(content) > maximum
            or len(content) != opened.st_size
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ContractError("%s changed while reading" % label)
        return content
    finally:
        os.close(descriptor)


def _write_exact_private_file(
    path: Path, content: bytes, *, create_missing: bool
) -> None:
    if not isinstance(content, bytes) or not 1 <= len(content) <= MAX_GROK_POLICY_FILE_BYTES:
        raise ContractError("Grok private policy file is invalid")
    if path.exists() or path.is_symlink():
        observed = _read_limited_regular(path, MAX_GROK_POLICY_FILE_BYTES, "Grok policy")
        if observed != content or stat.S_IMODE(path.stat().st_mode) != 0o600:
            raise ContractError("Grok private policy differs from its host projection")
        return
    if not create_missing:
        raise ContractError("Grok private policy file is missing")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            written = 0
            while written < len(content):
                written += os.write(descriptor, content[written:])
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise GrokInvocationError("Grok private policy could not be materialized") from exc


def _ensure_private_directory(path: Path) -> None:
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        pass
    except OSError as exc:
        raise GrokInvocationError("Grok private state directory could not be created") from exc
    if path.is_symlink() or not path.is_dir() or stat.S_IMODE(path.stat().st_mode) != 0o700:
        raise ContractError("Grok private state directory must have mode 0700")


def _write_new_checkpoint(path: Path, value: Mapping[str, Any]) -> None:
    source = _canonical_json(value) + b"\n"
    if len(source) > MAX_GROK_SESSION_CHECKPOINT_BYTES:
        raise GrokInvocationError("Grok checkpoint exceeded its safe size limit")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % path.name, suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(source):
            written += os.write(descriptor, source[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.link(str(temporary), str(path), follow_symlinks=False)
        directory_descriptor = os.open(
            str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except FileExistsError as exc:
        raise GrokInvocationError(
            "Grok session checkpoint already exists; resume it explicitly"
        ) from exc
    except OSError as exc:
        raise GrokInvocationError("Grok checkpoint could not be persisted") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _replace_checkpoint(path: Path, value: Mapping[str, Any]) -> None:
    source = _canonical_json(value) + b"\n"
    if len(source) > MAX_GROK_SESSION_CHECKPOINT_BYTES:
        raise GrokInvocationError("Grok checkpoint exceeded its safe size limit")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % path.name, suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    replaced = False
    try:
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(source):
            written += os.write(descriptor, source[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(str(temporary), str(path))
        replaced = True
        directory_descriptor = os.open(
            str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as exc:
        raise GrokInvocationError("Grok checkpoint could not be updated") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if not replaced:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _read_checkpoint(path: Path) -> Mapping[str, Any]:
    content = _read_limited_regular(
        path, MAX_GROK_SESSION_CHECKPOINT_BYTES, "Grok session checkpoint"
    )
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ContractError("Grok session checkpoint permissions must be 0600")
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ContractError("Grok session checkpoint must be UTF-8 JSON") from exc
    if not isinstance(value, Mapping):
        raise ContractError("Grok session checkpoint must contain one object")
    return value


def _remove_exact_checkpoints(items: Sequence[tuple[Path, Mapping[str, Any]]]) -> None:
    for path, expected in items:
        if not path.exists() and not path.is_symlink():
            continue
        if _read_checkpoint(path) != expected:
            raise GrokInvocationError("Grok unlaunched checkpoint changed unexpectedly")
        try:
            path.unlink()
        except OSError as exc:
            raise GrokInvocationError("Grok unlaunched checkpoint could not be removed") from exc


@dataclass(frozen=True)
class _GrokGoalState:
    session_checkpoint_sha256: str
    stage: str
    stage_checkpoint_sha256: str
    prompt_sha256: str
    attempt: int
    status: str
    revision: int
    schema_version: int = 1
    kind: str = GROK_GOAL_CHECKPOINT_KIND

    def __post_init__(self) -> None:
        if (
            self.schema_version != 1
            or self.kind != GROK_GOAL_CHECKPOINT_KIND
            or _GOAL_STAGE.fullmatch(self.stage) is None
            or type(self.attempt) is not int
            or not 1 <= self.attempt <= 2**53 - 1
            or type(self.revision) is not int
            or self.revision < self.attempt
            or self.status not in ("prepared", "active", "returned", "completed")
        ):
            raise ContractError("Grok native Goal state is invalid")
        _require_sha256(self.session_checkpoint_sha256, "Grok Goal session sha256")
        _require_sha256(self.stage_checkpoint_sha256, "Grok Goal stage sha256")
        _require_sha256(self.prompt_sha256, "Grok Goal prompt sha256")

    def identity(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "session_checkpoint_sha256": self.session_checkpoint_sha256,
            "stage": self.stage,
            "stage_checkpoint_sha256": self.stage_checkpoint_sha256,
            "goal_prompt_sha256": self.prompt_sha256,
            "attempt": self.attempt,
            "status": self.status,
            "revision": self.revision,
        }

    def to_dict(self) -> Mapping[str, Any]:
        identity = self.identity()
        return {**identity, "state_sha256": _sha256_json(identity)}

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "_GrokGoalState":
        expected = {
            "schema_version",
            "kind",
            "session_checkpoint_sha256",
            "stage",
            "stage_checkpoint_sha256",
            "goal_prompt_sha256",
            "attempt",
            "status",
            "revision",
            "state_sha256",
        }
        if set(value) != expected:
            raise ContractError("Grok native Goal state fields are invalid")
        try:
            state = cls(
                session_checkpoint_sha256=value["session_checkpoint_sha256"],
                stage=value["stage"],
                stage_checkpoint_sha256=value["stage_checkpoint_sha256"],
                prompt_sha256=value["goal_prompt_sha256"],
                attempt=value["attempt"],
                status=value["status"],
                revision=value["revision"],
                schema_version=value["schema_version"],
                kind=value["kind"],
            )
        except (KeyError, TypeError, ValueError, ContractError) as exc:
            raise ContractError("Grok native Goal state is invalid") from exc
        if value["state_sha256"] != _sha256_json(state.identity()):
            raise ContractError("Grok native Goal state binding is invalid")
        return state


def _goal_with_status(
    state: _GrokGoalState, status: str, *, revision: Optional[int] = None
) -> _GrokGoalState:
    return _GrokGoalState(
        session_checkpoint_sha256=state.session_checkpoint_sha256,
        stage=state.stage,
        stage_checkpoint_sha256=state.stage_checkpoint_sha256,
        prompt_sha256=state.prompt_sha256,
        attempt=state.attempt,
        status=status,
        revision=state.revision if revision is None else revision,
    )


@dataclass(frozen=True)
class _GrokPolicy:
    grok_home: Path
    neutral_home: Path
    temp_root: Path
    root_agent: Path
    config_sha256: str
    sandbox_sha256: str
    root_agent_sha256: str
    projection_sha256: str
    inventor_ids: tuple[str, ...]
    skill_names: tuple[str, ...]

    def digest(self) -> str:
        return _sha256_json(
            {
                "config_sha256": self.config_sha256,
                "sandbox_sha256": self.sandbox_sha256,
                "root_agent_sha256": self.root_agent_sha256,
                "projection_sha256": self.projection_sha256,
                "inventor_ids": list(self.inventor_ids),
                "skill_names": list(self.skill_names),
                "allowed_tools": list(GROK_ALLOWED_TOOLS),
                "disallowed_tools": list(GROK_DISALLOWED_TOOLS),
                "subprocess_environment_allowlist": list(
                    GROK_SUBPROCESS_ENVIRONMENT_ALLOWLIST
                ),
                "subprocess_environment_overrides": [
                    {"name": name, "value": value}
                    for name, value in _GROK_STATIC_ENVIRONMENT
                ],
                "direct_web_tools": False,
                "model": GROK_MODEL,
                "permission_mode": GROK_PERMISSION_MODE,
            }
        )

    def environment(self, source: Mapping[str, str]) -> Mapping[str, str]:
        values = dict(grok_subprocess_environment(source))
        if not values.get("XAI_API_KEY"):
            raise GrokInvocationError(
                "Grok Build requires XAI_API_KEY in Workshop's isolated profile"
            )
        values.update(dict(_GROK_STATIC_ENVIRONMENT))
        values.update(
            {
                "HOME": str(self.neutral_home),
                "GROK_HOME": str(self.grok_home),
                "TMPDIR": str(self.temp_root),
            }
        )
        return values


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _private_config_bytes() -> bytes:
    return (
        "[cli]\n"
        "auto_update = false\n"
        "use_leader = false\n"
        "session_registry = false\n\n"
        "[goal]\n"
        "enabled = true\n\n"
        "[subagents]\n"
        "enabled = true\n"
        "max_depth = 1\n"
        "max_concurrent = 5\n"
        "workflow_max_concurrent = 5\n\n"
        "[workflows]\n"
        "enabled = true\n\n"
        "[memory]\n"
        "enabled = false\n\n"
        "[compat.claude]\n"
        "agents = false\n"
        "rules = false\n"
        "skills = false\n"
        "hooks = false\n"
        "mcps = false\n"
        "sessions = false\n\n"
        "[compat.cursor]\n"
        "rules = false\n"
        "agents = false\n"
        "skills = false\n"
        "hooks = false\n"
        "mcps = false\n"
        "sessions = false\n\n"
        "[compat.codex]\n"
        "agents = false\n"
        "skills = false\n"
        "mcps = false\n"
        "sessions = false\n\n"
        "[managed_mcps]\n"
        "enabled = false\n"
        "gateway_tools_enabled = false\n\n"
        "[diagnostics]\n"
        "crash_handler = false\n\n"
        "[telemetry]\n"
        "otel_enabled = false\n"
        "trace_upload = false\n\n"
        "[shell_environment_policy]\n"
        "inherit = \"none\"\n"
        "ignore_default_excludes = false\n"
        "include_only = [\"PATH\", \"HOME\", \"LANG\", \"LC_ALL\", \"TMPDIR\"]\n"
    ).encode("utf-8")


def _sandbox_bytes(
    run_root: Path,
    policy_root: Path,
    grok_home: Path,
    neutral_home: Path,
) -> bytes:
    readonly = (
        run_root / ".grok",
        run_root / ".git",
        policy_root,
        grok_home,
        neutral_home,
    )
    return (
        "[profiles.workshop]\n"
        "extends = \"strict\"\n"
        "restrict_network = true\n"
        "read_only = [%s]\n"
        "deny = [\"**/.env\", \"**/.env.*\", \"**/*.pem\", "
        "\"**/*.key\", \"**/.netrc\", \"/proc/**\"]\n"
        % ", ".join(_quoted(str(path)) for path in readonly)
    ).encode("utf-8")


def _root_agent_bytes(inventor_ids: Sequence[str]) -> bytes:
    agent_selector = "Agent(%s)" % ",".join(inventor_ids)
    tool_lines = [
        *("  - %s\n" % tool for tool in GROK_ALLOWED_TOOLS if tool != "spawn_subagent"),
        "  - %s\n" % agent_selector,
    ]
    return (
        "---\n"
        "name: workshop-manager\n"
        "description: \"Host-bound Autonomous Workshop root Manager\"\n"
        "promptMode: extend\n"
        "tools:\n"
        + "".join(tool_lines)
        + "disallowedTools:\n"
        + "".join("  - %s\n" % tool for tool in GROK_DISALLOWED_TOOLS)
        + "permissionMode: dontAsk\n"
        "skills:\n"
        "  - autonomous-workshop\n"
        "agentsMd: true\n"
        "mcpInheritance: none\n"
        "discoverSkills: true\n"
        "inheritSkills: false\n"
        "injectDefaultTools: false\n"
        "model: inherit\n"
        "isolation: none\n"
        "---\n"
        "Follow the exact run-local AGENTS.md, MANAGER.json, and STAGE.json. "
        "Use only the projected Inventor subagents and skills. The Workshop host "
        "alone owns lifecycle gates, credentials, and external effects.\n"
    ).encode("utf-8")


def _projection_digest(run_root: Path) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    agent_root = run_root / ".grok" / "agents"
    skill_root = run_root / ".grok" / "skills"
    grok_root = run_root / ".grok"
    if (
        grok_root.is_symlink()
        or agent_root.is_symlink()
        or skill_root.is_symlink()
        or not grok_root.is_dir()
        or not agent_root.is_dir()
        or not skill_root.is_dir()
    ):
        raise ContractError("Grok Manager projection must not contain symlink roots")
    try:
        grok_children = tuple(grok_root.iterdir())
        agent_entries = tuple(agent_root.iterdir())
        skill_entries = tuple(skill_root.iterdir())
    except OSError as exc:
        raise ContractError("Grok Manager projection is incomplete") from exc
    if {path.name for path in grok_children} != {"agents", "skills"}:
        raise ContractError("Grok Manager projection contains unexpected roots")
    if any(
        path.is_symlink() or not path.is_file() or path.suffix != ".md"
        for path in agent_entries
    ) or any(path.is_symlink() or not path.is_dir() for path in skill_entries):
        raise ContractError("Grok Manager projection roster is invalid")
    agents = tuple(sorted(path.stem for path in agent_entries))
    skills = tuple(sorted(path.name for path in skill_entries))
    if (
        not agents
        or not skills
        or len(agents) != len(set(agents))
        or len(skills) != len(set(skills))
    ):
        raise ContractError("Grok Manager projection roster is invalid")
    digest = hashlib.sha256()
    selected: list[Path] = [
        run_root / PRODUCT_RUN_ROOT_MARKER,
        run_root / "AGENTS.md",
        run_root / "MANAGER.json",
        run_root / "WISH.json",
    ]
    try:
        projected_entries = tuple(sorted(grok_root.rglob("*")))
    except OSError as exc:
        raise ContractError("Grok Manager projection could not be inspected") from exc
    if len(projected_entries) > MAX_GROK_PROJECTION_FILES or any(
        path.is_symlink() for path in projected_entries
    ):
        raise ContractError("Grok Manager projection contains an unsafe tree")
    selected.extend(path for path in projected_entries if path.is_file())
    if len(selected) > MAX_GROK_PROJECTION_FILES:
        raise ContractError("Grok Manager projection contains too many files")
    total_bytes = 0
    for path in selected:
        if path.is_symlink() or not path.is_file() or not _is_within(path, run_root):
            raise ContractError("Grok Manager projection contains an unsafe file")
        content = _read_limited_regular(
            path, MAX_GROK_PROJECTION_FILE_BYTES, "Grok projection file"
        )
        total_bytes += len(content)
        if total_bytes > MAX_GROK_PROJECTION_BYTES:
            raise ContractError("Grok Manager projection exceeds its byte limit")
        relative = path.relative_to(run_root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest(), agents, skills


def _prepare_policy(
    run_root: Path, state_root: Path, *, create_missing: bool
) -> _GrokPolicy:
    grok_home = state_root / GROK_PRIVATE_HOME_NAME
    neutral_home = state_root / GROK_NEUTRAL_HOME_NAME
    policy_root = state_root / GROK_PRIVATE_POLICY_NAME
    temp_root = state_root / GROK_PRIVATE_TEMP_NAME
    for path in (grok_home, neutral_home, policy_root, temp_root):
        if create_missing:
            _ensure_private_directory(path)
        elif (
            path.is_symlink()
            or not path.is_dir()
            or stat.S_IMODE(path.stat().st_mode) != 0o700
        ):
            raise ContractError("Grok private state directory is missing or invalid")
    projection_sha256, inventor_ids, skill_names = _projection_digest(run_root)
    config = _private_config_bytes()
    sandbox = _sandbox_bytes(
        run_root,
        policy_root,
        grok_home,
        neutral_home,
    )
    root_agent = _root_agent_bytes(inventor_ids)
    config_path = grok_home / "config.toml"
    sandbox_path = grok_home / "sandbox.toml"
    root_agent_path = policy_root / GROK_ROOT_AGENT_NAME
    _write_exact_private_file(config_path, config, create_missing=create_missing)
    _write_exact_private_file(sandbox_path, sandbox, create_missing=create_missing)
    _write_exact_private_file(root_agent_path, root_agent, create_missing=create_missing)
    return _GrokPolicy(
        grok_home=grok_home,
        neutral_home=neutral_home,
        temp_root=temp_root,
        root_agent=root_agent_path,
        config_sha256=hashlib.sha256(config).hexdigest(),
        sandbox_sha256=hashlib.sha256(sandbox).hexdigest(),
        root_agent_sha256=hashlib.sha256(root_agent).hexdigest(),
        projection_sha256=projection_sha256,
        inventor_ids=inventor_ids,
        skill_names=skill_names,
    )


@dataclass(frozen=True)
class GrokNativeSessionBinding:
    """Redacted identity for one Wish-wide native Grok Build session."""

    product_id: str
    wish_sha256: str
    constitution_sha256: str
    run_root_sha256: str
    host_state_root_sha256: str
    runtime_config_sha256: str
    checkpoint_sha256: str
    schema_version: int = 1
    kind: str = GROK_SESSION_CHECKPOINT_KIND

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.kind != GROK_SESSION_CHECKPOINT_KIND:
            raise ContractError("Grok native session binding version is invalid")
        _bounded_identifier(self.product_id, "Grok native session product_id")
        for value, label in (
            (self.wish_sha256, "Grok native session Wish sha256"),
            (self.constitution_sha256, "Grok native session constitution sha256"),
            (self.run_root_sha256, "Grok native session run-root sha256"),
            (self.host_state_root_sha256, "Grok native session host-state-root sha256"),
            (self.runtime_config_sha256, "Grok native session runtime-config sha256"),
            (self.checkpoint_sha256, "Grok native session checkpoint sha256"),
        ):
            _require_sha256(value, label)

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "product_id": self.product_id,
            "wish_sha256": self.wish_sha256,
            "constitution_sha256": self.constitution_sha256,
            "run_root_sha256": self.run_root_sha256,
            "host_state_root_sha256": self.host_state_root_sha256,
            "runtime_config_sha256": self.runtime_config_sha256,
            "checkpoint_sha256": self.checkpoint_sha256,
        }


@dataclass(frozen=True)
class GrokNativeSessionOutcome:
    """Compact public outcome; session UUID and event text remain private."""

    binding: GrokNativeSessionBinding
    used_web_search: bool = False
    status: str = "completed"

    def __post_init__(self) -> None:
        if not isinstance(self.binding, GrokNativeSessionBinding):
            raise ContractError("Grok native session outcome requires a binding")
        if self.status != "completed" or type(self.used_web_search) is not bool:
            raise ContractError("Grok native session outcome is invalid")

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "status": self.status,
            "session": self.binding.to_dict(),
            "used_web_search": self.used_web_search,
        }


def _runner_text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _git_environment(policy: _GrokPolicy, source: Mapping[str, str]) -> Mapping[str, str]:
    values: dict[str, str] = {
        "HOME": str(policy.neutral_home),
        "TMPDIR": str(policy.temp_root),
    }
    for name in ("PATH", "LANG", "LC_ALL", "LC_CTYPE"):
        value = source.get(name)
        if isinstance(value, str) and value:
            values[name] = value
    return values


def _ensure_project_repository(
    run_root: Path,
    policy: _GrokPolicy,
    *,
    runner: Any,
    source_environment: Mapping[str, str],
    allow_init: bool,
) -> None:
    """Keep Grok discovery inside an ignored private toy directory."""

    git_root = run_root / ".git"
    if git_root.is_symlink() or (git_root.exists() and not git_root.is_dir()):
        raise ContractError("Grok project Git boundary is unsafe")
    environment = _git_environment(policy, source_environment)

    def discover() -> Any:
        try:
            return runner(
                ["git", "-C", str(run_root), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
                env=environment,
            )
        except (OSError, subprocess.SubprocessError, TypeError, ValueError) as exc:
            raise GrokInvocationError("Grok project Git boundary could not be inspected") from exc

    discovered = discover()
    output = _runner_text(getattr(discovered, "stdout", "")).strip()
    if getattr(discovered, "returncode", 1) == 0 and output == str(run_root):
        return
    if not allow_init or git_root.exists() or git_root.is_symlink():
        raise ContractError("Grok project root is not the exact private run root")
    try:
        initialized = runner(
            [
                "git",
                "-C",
                str(run_root),
                "init",
                "--quiet",
                "--initial-branch=workshop",
                "--template=",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError, TypeError, ValueError) as exc:
        raise GrokInvocationError(
            "Grok private project boundary could not be initialized"
        ) from exc
    if getattr(initialized, "returncode", 1) != 0:
        raise GrokInvocationError("Grok private project boundary could not be initialized")
    discovered = discover()
    output = _runner_text(getattr(discovered, "stdout", "")).strip()
    if getattr(discovered, "returncode", 1) != 0 or output != str(run_root):
        raise GrokInvocationError("Grok private project boundary was not established")


def _entry_path(value: Any) -> Optional[Path]:
    if isinstance(value, str) and value:
        return Path(value)
    if not isinstance(value, Mapping):
        return None
    for key in ("path", "file", "filePath", "sourcePath"):
        selected = value.get(key)
        if isinstance(selected, str) and selected:
            return Path(selected)
    source = value.get("source")
    if isinstance(source, Mapping):
        return _entry_path(source)
    return None


def _entry_name(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return Path(value).stem
    if isinstance(value, Mapping):
        for key in ("name", "id", "command"):
            selected = value.get(key)
            if isinstance(selected, str) and selected:
                return selected.removeprefix("/")
    return None


def _has_true_boolean(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, Mapping):
        return any(_has_true_boolean(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_has_true_boolean(item) for item in value)
    return False


def _project_roster(
    value: Any,
    *,
    run_root: Path,
    expected_root: Path,
    label: str,
) -> set[str]:
    if not isinstance(value, list):
        raise GrokInvocationError("Grok inspect did not report its project %s" % label)
    observed: set[str] = set()
    for entry in value:
        path = _entry_path(entry)
        scope = entry.get("scope") if isinstance(entry, Mapping) else None
        project_scoped = isinstance(scope, str) and scope.casefold() == "project"
        if isinstance(entry, Mapping) and isinstance(entry.get("source"), Mapping):
            source_type = entry["source"].get("type")
            project_scoped = project_scoped or (
                isinstance(source_type, str) and source_type.casefold() == "project"
            )
        resolved: Optional[Path] = None
        if path is not None:
            candidate = path if path.is_absolute() else run_root / path
            try:
                resolved = candidate.resolve(strict=False)
            except OSError:
                resolved = None
            if resolved is not None and _is_within(resolved, run_root):
                project_scoped = True
                if not _is_within(resolved, expected_root):
                    raise GrokInvocationError(
                        "Grok inspect reported an unexpected project %s" % label
                    )
        if project_scoped:
            if resolved is None or not _is_within(resolved, expected_root):
                raise GrokInvocationError(
                    "Grok inspect reported an unexpected project %s" % label
                )
            name = _entry_name(entry)
            if name is None:
                raise GrokInvocationError("Grok inspect project %s is invalid" % label)
            if isinstance(entry, Mapping) and entry.get("enabled") is False:
                raise GrokInvocationError("Grok inspect disabled a projected %s" % label)
            observed.add(name)
    return observed


def _inspect_digest(
    payload: Mapping[str, Any], run_root: Path, policy: _GrokPolicy
) -> str:
    if payload.get("grokVersion") not in (
        PINNED_GROK_NATIVE_RUNTIME_VERSION,
        ".".join(str(part) for part in MINIMUM_GROK_NATIVE_RUNTIME_VERSION),
    ):
        raise GrokInvocationError("Grok inspect reported an unexpected runtime build")
    try:
        inspected_cwd = Path(payload.get("cwd", "")).resolve(strict=False)
        inspected_root = Path(payload.get("projectRoot", "")).resolve(strict=False)
    except (OSError, TypeError, ValueError):
        raise GrokInvocationError("Grok inspect reported the wrong project root") from None
    if inspected_cwd != run_root or inspected_root != run_root:
        raise GrokInvocationError("Grok inspect reported the wrong project root")
    if payload.get("channel") != "unknown" or type(payload.get("projectTrusted")) is not bool:
        raise GrokInvocationError("Grok inspect reported an invalid runtime context")
    instructions = payload.get("projectInstructions")
    if not isinstance(instructions, list) or not instructions:
        raise GrokInvocationError("Grok inspect did not load the run-local AGENTS.md")
    instruction_paths: set[Path] = set()
    for entry in instructions:
        selected = _entry_path(entry)
        if selected is None:
            raise GrokInvocationError("Grok inspect returned an invalid instruction path")
        candidate = selected if selected.is_absolute() else run_root / selected
        try:
            instruction_paths.add(candidate.resolve(strict=False))
        except OSError as exc:
            raise GrokInvocationError("Grok inspect instruction path is invalid") from exc
    expected_instruction = run_root / "AGENTS.md"
    if len(instruction_paths) != 1:
        raise GrokInvocationError("Grok inspect loaded instructions outside the private run")
    try:
        same_instruction = os.path.samefile(
            next(iter(instruction_paths)), expected_instruction
        )
    except OSError:
        same_instruction = next(iter(instruction_paths)) == expected_instruction.resolve(
            strict=False
        )
    if not same_instruction:
        raise GrokInvocationError("Grok inspect loaded instructions outside the private run")
    permissions = payload.get("permissions")
    if (
        not isinstance(permissions, Mapping)
        or permissions.get("sources") != []
        or permissions.get("loaded") != 0
        or permissions.get("skipped") != []
        or permissions.get("mcpServerAllowlist") != []
        or permissions.get("marketplaceAllowlist") != []
        or permissions.get("managedSettingsExists") is not False
        or permissions.get("managedSettingsActive") is not False
    ):
        raise GrokInvocationError("Grok inspect reported ambient permission policy")
    login_policy = payload.get("loginPolicy")
    if (
        not isinstance(login_policy, Mapping)
        or login_policy.get("disableApiKeyAuth") not in (None, False)
        or login_policy.get("apiKeyAuthDisabled") is not False
        or login_policy.get("forceLoginTeamUuid") is not None
    ):
        raise GrokInvocationError("Grok inspect reported incompatible login policy")
    for field in ("hooks", "plugins", "marketplaces", "mcpServers", "lspServers"):
        if payload.get(field) not in (None, False, [], {}):
            raise GrokInvocationError("Grok inspect reported forbidden %s" % field)
    if payload.get("configWarnings") not in (None, [], {}) or payload.get(
        "mcpConfigProblems"
    ) not in (None, [], {}):
        raise GrokInvocationError("Grok inspect reported configuration problems")
    if _has_true_boolean(payload.get("externalCompat")):
        raise GrokInvocationError("Grok inspect reported ambient compatibility imports")
    config_sources = payload.get("configSources")
    layers = config_sources.get("layers") if isinstance(config_sources, Mapping) else None
    if not isinstance(layers, list) or len(layers) != 1 or not isinstance(layers[0], Mapping):
        raise GrokInvocationError("Grok inspect reported unexpected configuration sources")
    config_path = _entry_path(layers[0])
    if layers[0].get("role") != "user" or config_path is None:
        raise GrokInvocationError("Grok inspect reported unexpected configuration sources")
    try:
        same_config = os.path.samefile(config_path, policy.grok_home / "config.toml")
    except OSError:
        same_config = config_path.resolve(strict=False) == (
            policy.grok_home / "config.toml"
        ).resolve(strict=False)
    if not same_config:
        raise GrokInvocationError("Grok inspect reported unexpected configuration sources")
    observed_agents = _project_roster(
        payload.get("agents"),
        run_root=run_root,
        expected_root=run_root / ".grok" / "agents",
        label="agents",
    )
    observed_skills = _project_roster(
        payload.get("skills"),
        run_root=run_root,
        expected_root=run_root / ".grok" / "skills",
        label="skills",
    )
    if observed_agents != set(policy.inventor_ids):
        raise GrokInvocationError("Grok inspect Inventor roster differs from its projection")
    if observed_skills != set(policy.skill_names):
        raise GrokInvocationError("Grok inspect skill roster differs from its projection")
    try:
        return hashlib.sha256(_canonical_json(payload)).hexdigest()
    except ContractError as exc:
        raise GrokInvocationError("Grok inspect report is not canonical JSON") from exc


def _normalize_commands(value: Any) -> set[str]:
    if not isinstance(value, list):
        raise GrokInvocationError("Grok command attestation is invalid")
    result: set[str] = set()
    for item in value:
        name = _entry_name(item)
        if name is None:
            raise GrokInvocationError("Grok command attestation is invalid")
        result.add(name.removeprefix("/"))
    return result


def _attest_available_commands(event: Mapping[str, Any]) -> None:
    tools = event.get("tools")
    if (
        not isinstance(tools, list)
        or any(not isinstance(tool, str) for tool in tools)
        or len(tools) != len(set(tools))
        or set(tools) != set(GROK_ALLOWED_TOOLS)
    ):
        raise GrokInvocationError("Grok live tool roster differs from its allowlist")
    if "goal" not in _normalize_commands(event.get("commands")):
        raise GrokInvocationError("Grok did not attest its native /goal command")


def _decode_stream_event(line: str) -> Mapping[str, Any]:
    if not isinstance(line, str) or not line.strip():
        raise GrokInvocationError("Grok native event stream is invalid")
    try:
        event = json.loads(line)
    except (TypeError, ValueError):
        raise GrokInvocationError("Grok native event stream is invalid") from None
    if not isinstance(event, Mapping):
        raise GrokInvocationError("Grok native event stream is invalid")
    return event


def _terminate_process_group(process: Any) -> None:
    killed_group = False
    if os.name == "posix":
        try:
            pid = int(process.pid)
            if pid > 1 and pid != os.getpgrp():
                os.killpg(pid, signal.SIGKILL)
                killed_group = True
        except BaseException:
            pass
    if not killed_group:
        try:
            process.kill()
        except BaseException:
            pass
    try:
        process.wait(timeout=_PROCESS_EXIT_GRACE_SECONDS)
    except BaseException:
        pass


class GrokNativeSessionLauncher:
    """Launch or resume one pinned native Grok Build Manager per Wish."""

    manager_id = "grok"
    session_checkpoint_name = GROK_SESSION_CHECKPOINT_NAME

    def __init__(
        self,
        *,
        binary: Optional[str] = None,
        model: str = GROK_MODEL,
        timeout_seconds: int = DEFAULT_GROK_TIMEOUT_SECONDS,
        max_turns: int = DEFAULT_GROK_MAX_TURNS,
        popen_factory: Any = subprocess.Popen,
        version_runner: Any = subprocess.run,
        inspect_runner: Any = subprocess.run,
        git_runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
        uuid_factory: Any = uuid.uuid4,
        environment_source: Optional[Mapping[str, str]] = None,
    ) -> None:
        if model != GROK_MODEL:
            raise ContractError("Workshop Grok model must be the audited grok-build model")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3_600:
            raise ValueError("Grok timeout_seconds must be from 1 to 3,600")
        if type(max_turns) is not int or not 1 <= max_turns <= 512:
            raise ValueError("Grok max_turns must be from 1 to 512")
        self.binary = binary or os.environ.get("WORKSHOP_GROK_BIN") or shutil.which("grok")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_turns = max_turns
        self._popen_factory = popen_factory
        self._version_runner = version_runner
        self._inspect_runner = inspect_runner
        self._git_runner = git_runner
        self._uuid_factory = uuid_factory
        self._environment_source = dict(
            os.environ if environment_source is None else environment_source
        )
        self.cli_version = cli_version or self._read_cli_version()
        if self.binary and not grok_supports_native_workshop(self.cli_version):
            raise GrokInvocationError(
                "Workshop requires exact Grok Build %s; other builds have not "
                "passed the session and isolation contract"
                % PINNED_GROK_NATIVE_RUNTIME_VERSION
            )

    def _read_cli_version(self) -> str:
        if not self.binary:
            return "0.0.0"
        environment = grok_subprocess_environment(
            self._environment_source,
            allowlist=tuple(
                name
                for name in GROK_SUBPROCESS_ENVIRONMENT_ALLOWLIST
                if name != "XAI_API_KEY"
            ),
        )
        environment = {
            **environment,
            "GROK_DISABLE_AUTOUPDATER": "1",
            "GROK_TELEMETRY_ENABLED": "false",
            "GROK_TELEMETRY_TRACE_UPLOAD": "false",
        }
        try:
            completed = self._version_runner(
                [self.binary, "version", "--json"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                env=environment,
            )
        except (OSError, subprocess.SubprocessError, TypeError, ValueError):
            return "0.0.0"
        output = _runner_text(getattr(completed, "stdout", ""))
        if getattr(completed, "returncode", 1) != 0 or len(output.encode("utf-8")) > 4096:
            return "0.0.0"
        try:
            value = json.loads(output)
        except ValueError:
            return "0.0.0"
        version = value.get("currentVersion") if isinstance(value, Mapping) else None
        return version if isinstance(version, str) else "0.0.0"

    def _inspect(
        self, run_root: Path, policy: _GrokPolicy, environment: Mapping[str, str]
    ) -> str:
        if not self.binary:
            raise _GrokProcessNotSpawned("Grok Build is not installed or on PATH")
        inspect_environment = dict(environment)
        inspect_environment.pop("XAI_API_KEY", None)
        try:
            completed = self._inspect_runner(
                [self.binary, "--cwd", str(run_root), "inspect", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                env=inspect_environment,
            )
        except (OSError, subprocess.SubprocessError, TypeError, ValueError) as exc:
            raise GrokInvocationError("Grok project inspection could not run") from exc
        output = _runner_text(getattr(completed, "stdout", ""))
        if (
            getattr(completed, "returncode", 1) != 0
            or not output
            or len(output.encode("utf-8", errors="replace")) > MAX_GROK_INSPECT_BYTES
        ):
            raise GrokInvocationError("Grok project inspection did not complete")
        try:
            value = json.loads(output)
        except (TypeError, ValueError):
            raise GrokInvocationError("Grok project inspection returned invalid JSON") from None
        if not isinstance(value, Mapping):
            raise GrokInvocationError("Grok project inspection returned invalid JSON")
        return _inspect_digest(value, run_root, policy)

    def _runtime_config_sha256(self, policy: _GrokPolicy, inspect_sha256: str) -> str:
        return _sha256_json(
            {
                "adapter": "grok-build-cli-native-session",
                "binary_path_sha256": hashlib.sha256(
                    (self.binary or "").encode("utf-8")
                ).hexdigest(),
                "cli_version": self.cli_version,
                "model": self.model,
                "permission_mode": GROK_PERMISSION_MODE,
                "output_format": "streaming-json",
                "goal_protocol": "slash-goal-status-v1",
                "policy_sha256": policy.digest(),
                "inspect_sha256": _require_sha256(
                    inspect_sha256, "Grok inspect sha256"
                ),
                "max_turns": self.max_turns,
                "timeout_seconds": self.timeout_seconds,
                "process_group_isolation": os.name == "posix",
            }
        )

    def _common_command(self, run_root: Path, policy: _GrokPolicy) -> list[str]:
        command = [
            self.binary or "grok",
            "--no-plan",
            "--cwd",
            str(run_root),
            "--sandbox",
            "workshop",
            "--model",
            self.model,
            "--agent",
            str(policy.root_agent),
            "--permission-mode",
            GROK_PERMISSION_MODE,
            "--disable-web-search",
            "--tools",
            ",".join(GROK_ALLOWED_TOOLS),
            "--disallowed-tools",
            ",".join(GROK_DISALLOWED_TOOLS),
            "--max-turns",
            str(self.max_turns),
            "--output-format",
            "streaming-json",
        ]
        for rule in ("Read(./**)", "Edit(./**)", "Grep", "Bash(*)"):
            command.extend(("--allow", rule))
        for path in _IMMUTABLE_RUN_DIRECTORIES:
            command.extend(("--deny", "Edit(%s/**)" % path))
        for path in _IMMUTABLE_RUN_FILES:
            command.extend(("--deny", "Edit(%s)" % path))
        return command

    def _command(
        self,
        *,
        run_root: Path,
        policy: _GrokPolicy,
        session_id: str,
        prompt: str,
        resume: bool,
    ) -> list[str]:
        selector = "--resume" if resume else "--session-id"
        return [
            *self._common_command(run_root, policy),
            selector,
            _canonical_session_id(session_id),
            "-p",
            prompt,
        ]

    def _stream(
        self,
        *,
        command: list[str],
        run_root: Path,
        environment: Mapping[str, str],
        expected_session_id: str,
        status_turn: bool,
        on_spawn: Optional[Callable[[], None]] = None,
    ) -> None:
        if not self.binary:
            raise _GrokProcessNotSpawned("Grok Build is not installed or on PATH")
        popen_arguments: dict[str, Any] = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "bufsize": 1,
            "cwd": str(run_root),
            "env": environment,
        }
        if os.name == "posix":
            popen_arguments["start_new_session"] = True
        elif os.name == "nt":  # pragma: no cover - Windows CI only
            popen_arguments["creationflags"] = getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0
            )
        try:
            process = self._popen_factory(command, **popen_arguments)
        except (OSError, subprocess.SubprocessError, TypeError, ValueError):
            raise _GrokProcessNotSpawned(
                "Grok native session could not be launched"
            ) from None
        if on_spawn is not None:
            try:
                on_spawn()
            except BaseException:
                _terminate_process_group(process)
                raise
        if process.stdout is None or process.stderr is None:
            _terminate_process_group(process)
            raise GrokInvocationError("Grok native session streams are unavailable")

        stderr_size = 0
        stderr_tail = ""
        stderr_overflow = threading.Event()

        def drain_stderr() -> None:
            nonlocal stderr_size, stderr_tail
            try:
                for raw in process.stderr:
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", errors="replace")
                    if not isinstance(raw, str):
                        stderr_overflow.set()
                        return
                    stderr_size += len(raw.encode("utf-8", errors="replace"))
                    stderr_tail = (stderr_tail + raw)[-64 * 1024 :]
                    if stderr_size > MAX_GROK_STDERR_BYTES:
                        stderr_overflow.set()
                        _terminate_process_group(process)
                        return
            except (OSError, ValueError, UnicodeError):
                stderr_overflow.set()

        stderr_thread = threading.Thread(
            target=drain_stderr,
            name="workshop-grok-stderr",
            daemon=True,
        )
        stderr_thread.start()
        timed_out = threading.Event()

        def expire() -> None:
            timed_out.set()
            _terminate_process_group(process)

        deadline = time.monotonic() + self.timeout_seconds
        timer = threading.Timer(self.timeout_seconds, expire)
        timer.daemon = True
        timer.start()
        total_size = 0
        saw_available_commands = False
        saw_end = False
        status_text: list[str] = []
        stream_failure: Optional[BaseException] = None
        allowed_types = _STATUS_EVENT_TYPES if status_turn else _STREAM_EVENT_TYPES
        try:
            for raw in process.stdout:
                if isinstance(raw, bytes):
                    try:
                        raw = raw.decode("utf-8")
                    except UnicodeError:
                        raise GrokInvocationError(
                            "Grok native event stream is invalid"
                        ) from None
                if not isinstance(raw, str):
                    raise GrokInvocationError("Grok native event stream is invalid")
                total_size += len(raw.encode("utf-8", errors="replace"))
                if total_size > MAX_GROK_EVENT_STREAM_BYTES:
                    raise GrokInvocationError(
                        "Grok native event stream exceeded its safe size limit"
                    )
                event = _decode_stream_event(raw)
                event_type = event.get("type")
                if saw_end:
                    raise GrokInvocationError(
                        "Grok returned events after its terminal event"
                    )
                if event_type in ("error", "max_turns_reached"):
                    raise GrokInvocationError("Grok native session did not complete")
                if event_type not in allowed_types:
                    raise GrokInvocationError(
                        "Grok returned an event outside its pinned protocol"
                    )
                event_session = event.get("sessionId")
                if event_session is not None:
                    try:
                        observed_session = _canonical_session_id(event_session)
                    except ContractError:
                        raise GrokInvocationError(
                            "Grok returned an invalid native session identity"
                        ) from None
                    if observed_session != expected_session_id:
                        raise GrokInvocationError(
                            "Grok resumed a different native session"
                        )
                if event_type == "available_commands":
                    _attest_available_commands(event)
                    saw_available_commands = True
                elif event_type in ("tool_call", "tool_call_update"):
                    tool_name = event.get("toolName")
                    if event_type == "tool_call" and not isinstance(tool_name, str):
                        raise GrokInvocationError("Grok tool call is invalid")
                    if tool_name is not None and tool_name not in GROK_ALLOWED_TOOLS:
                        raise GrokInvocationError(
                            "Grok invoked a tool outside its allowlist"
                        )
                elif event_type in ("text", "thought"):
                    data = event.get("data")
                    if not isinstance(data, str) or "\x00" in data:
                        raise GrokInvocationError("Grok message event is invalid")
                    if len(data.encode("utf-8")) > MAX_GROK_EVENT_STREAM_BYTES:
                        raise GrokInvocationError("Grok message event is invalid")
                    if status_turn and event_type == "text":
                        status_text.append(data)
                elif event_type == "end":
                    try:
                        terminal_session = _canonical_session_id(event.get("sessionId"))
                    except ContractError:
                        raise GrokInvocationError(
                            "Grok terminal session identity is invalid"
                        ) from None
                    request_id = event.get("requestId")
                    if (
                        terminal_session != expected_session_id
                        or event.get("stopReason") != "end_turn"
                        or not isinstance(request_id, str)
                        or not request_id
                        or len(request_id) > 256
                    ):
                        raise GrokInvocationError(
                            "Grok terminal event did not attest a completed turn"
                        )
                    saw_end = True
        except BaseException as exc:
            stream_failure = exc
            _terminate_process_group(process)
        finally:
            timer.cancel()

        try:
            returncode = process.wait(
                timeout=max(0.001, deadline - time.monotonic())
            )
        except (subprocess.TimeoutExpired, OSError, ValueError):
            _terminate_process_group(process)
            returncode = getattr(process, "returncode", None)
        stderr_thread.join(timeout=_PROCESS_EXIT_GRACE_SECONDS)
        if stream_failure is not None and not isinstance(stream_failure, Exception):
            raise stream_failure
        if timed_out.is_set():
            raise GrokInvocationError("Grok native session timed out")
        if stderr_thread.is_alive() or stderr_overflow.is_set():
            _terminate_process_group(process)
            raise GrokInvocationError(
                "Grok native diagnostic stream exceeded its safe limit"
            )
        if "warning" in stderr_tail.casefold():
            raise GrokInvocationError(
                "Grok native session reported a configuration warning"
            )
        if stream_failure is not None:
            if isinstance(stream_failure, (GrokInvocationError, ContractError)):
                raise stream_failure from None
            raise GrokInvocationError("Grok native event stream is invalid") from None
        if returncode != 0 or not saw_available_commands or not saw_end:
            raise GrokInvocationError("Grok native session did not complete")
        if status_turn and _STATUS_COMPLETE.search("".join(status_text)) is None:
            raise GrokInvocationError(
                "Grok native Goal did not report an exact Complete status"
            )

    def _binding_paths(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
    ) -> tuple[Path, Path, Path, Path]:
        _bounded_identifier(product_id, "Grok native session product_id")
        _require_sha256(wish_sha256, "Grok native session Wish sha256")
        _require_sha256(
            constitution_sha256, "Grok native session constitution sha256"
        )
        root = _resolve_run_root(run_root)
        state_root = _resolve_host_state_root(host_state_root, root)
        return (
            root,
            state_root,
            state_root / GROK_SESSION_CHECKPOINT_NAME,
            state_root / GROK_GOAL_CHECKPOINT_NAME,
        )

    def _checkpoint_identity(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        session_id: str,
        policy: _GrokPolicy,
        inspect_sha256: str,
    ) -> Mapping[str, Any]:
        runtime_config_sha256 = self._runtime_config_sha256(policy, inspect_sha256)
        return {
            "schema_version": 1,
            "kind": GROK_SESSION_CHECKPOINT_KIND,
            "product_id": product_id,
            "wish_sha256": wish_sha256,
            "constitution_sha256": constitution_sha256,
            "run_root_sha256": _path_sha256(run_root),
            "host_state_root_sha256": _path_sha256(host_state_root),
            "policy_sha256": policy.digest(),
            "inspect_sha256": inspect_sha256,
            "runtime_config_sha256": runtime_config_sha256,
            "cli_version": self.cli_version,
            "model": self.model,
            "permission_mode": GROK_PERMISSION_MODE,
            "sandbox_required": True,
            "session_id": _canonical_session_id(session_id),
        }

    def _load_checkpoint(
        self,
        *,
        path: Path,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        policy: _GrokPolicy,
        current_inspect_sha256: Optional[str],
    ) -> tuple[str, str, str]:
        payload = _read_checkpoint(path)
        expected_fields = {
            "schema_version",
            "kind",
            "product_id",
            "wish_sha256",
            "constitution_sha256",
            "run_root_sha256",
            "host_state_root_sha256",
            "policy_sha256",
            "inspect_sha256",
            "runtime_config_sha256",
            "cli_version",
            "model",
            "permission_mode",
            "sandbox_required",
            "session_id",
            "checkpoint_sha256",
        }
        if set(payload) != expected_fields or type(payload.get("sandbox_required")) is not bool:
            raise ContractError("Grok native session checkpoint fields are invalid")
        session_id = _canonical_session_id(payload.get("session_id"))
        inspect_sha256 = _require_sha256(
            payload.get("inspect_sha256"), "Grok session inspect sha256"
        )
        checkpoint_sha256 = _require_sha256(
            payload.get("checkpoint_sha256"), "Grok session checkpoint sha256"
        )
        if current_inspect_sha256 is not None and inspect_sha256 != current_inspect_sha256:
            raise ContractError("Grok project inspection changed since session creation")
        identity = self._checkpoint_identity(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
            session_id=session_id,
            policy=policy,
            inspect_sha256=inspect_sha256,
        )
        observed_identity = {key: payload[key] for key in identity}
        if observed_identity != identity or checkpoint_sha256 != _sha256_json(identity):
            raise ContractError("Grok native session checkpoint binding is invalid")
        return session_id, checkpoint_sha256, identity["runtime_config_sha256"]

    def _load_goal_state(
        self, path: Path, *, session_checkpoint_sha256: str
    ) -> _GrokGoalState:
        try:
            state = _GrokGoalState.from_mapping(_read_checkpoint(path))
        except ContractError as exc:
            raise ContractError(
                "Grok native Goal checkpoint is missing or invalid"
            ) from exc
        if state.session_checkpoint_sha256 != session_checkpoint_sha256:
            raise ContractError("Grok native Goal belongs to another session")
        return state

    def _public_binding(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        runtime_config_sha256: str,
        checkpoint_sha256: str,
    ) -> GrokNativeSessionBinding:
        return GrokNativeSessionBinding(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root_sha256=_path_sha256(run_root),
            host_state_root_sha256=_path_sha256(host_state_root),
            runtime_config_sha256=runtime_config_sha256,
            checkpoint_sha256=checkpoint_sha256,
        )

    def start(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        prompt: str,
        goal_stage: str,
        goal_checkpoint_sha256: str,
    ) -> GrokNativeSessionOutcome:
        root, state_root, session_path, goal_path = self._binding_paths(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
        )
        if session_path.exists() or session_path.is_symlink():
            raise ContractError(
                "Grok native session checkpoint already exists; resume it explicitly"
            )
        if goal_path.exists() or goal_path.is_symlink():
            try:
                orphan = _GrokGoalState.from_mapping(_read_checkpoint(goal_path))
            except ContractError as exc:
                raise ContractError(
                    "Grok uncommitted Goal checkpoint cannot be recovered"
                ) from exc
            if orphan.status != "prepared" or orphan.attempt != 1 or orphan.revision != 1:
                raise ContractError(
                    "Grok Goal exists without its committed native session"
                )
            _remove_exact_checkpoints(((goal_path, orphan.to_dict()),))
        prompt = _validated_prompt(prompt)
        goal_stage, goal_checkpoint_sha256 = _validated_goal_binding(
            goal_stage, goal_checkpoint_sha256
        )
        policy = _prepare_policy(root, state_root, create_missing=True)
        environment = policy.environment(self._environment_source)
        _ensure_project_repository(
            root,
            policy,
            runner=self._git_runner,
            source_environment=self._environment_source,
            allow_init=True,
        )
        inspect_sha256 = self._inspect(root, policy, environment)
        try:
            session_id = _canonical_session_id(str(self._uuid_factory()))
        except (ContractError, TypeError, ValueError):
            raise GrokInvocationError("Grok native session id could not be allocated") from None
        identity = self._checkpoint_identity(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=root,
            host_state_root=state_root,
            session_id=session_id,
            policy=policy,
            inspect_sha256=inspect_sha256,
        )
        checkpoint_sha256 = _sha256_json(identity)
        session_checkpoint = {**identity, "checkpoint_sha256": checkpoint_sha256}
        prepared = _GrokGoalState(
            session_checkpoint_sha256=checkpoint_sha256,
            stage=goal_stage,
            stage_checkpoint_sha256=goal_checkpoint_sha256,
            prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            attempt=1,
            status="prepared",
            revision=1,
        )
        prepared_checkpoint = prepared.to_dict()
        try:
            _write_new_checkpoint(goal_path, prepared_checkpoint)
            _write_new_checkpoint(session_path, session_checkpoint)
        except BaseException:
            _remove_exact_checkpoints(
                (
                    (session_path, session_checkpoint),
                    (goal_path, prepared_checkpoint),
                )
            )
            raise
        activated = False

        def activate() -> None:
            nonlocal activated
            _replace_checkpoint(goal_path, _goal_with_status(prepared, "active").to_dict())
            activated = True

        try:
            self._stream(
                command=self._command(
                    run_root=root,
                    policy=policy,
                    session_id=session_id,
                    prompt=prompt,
                    resume=False,
                ),
                run_root=root,
                environment=environment,
                expected_session_id=session_id,
                status_turn=False,
                on_spawn=activate,
            )
            self._stream(
                command=self._command(
                    run_root=root,
                    policy=policy,
                    session_id=session_id,
                    prompt=GROK_GOAL_STATUS_PROMPT,
                    resume=True,
                ),
                run_root=root,
                environment=environment,
                expected_session_id=session_id,
                status_turn=True,
            )
        except _GrokProcessNotSpawned:
            if not activated:
                _remove_exact_checkpoints(
                    (
                        (session_path, session_checkpoint),
                        (goal_path, prepared_checkpoint),
                    )
                )
            raise
        _replace_checkpoint(goal_path, _goal_with_status(prepared, "returned").to_dict())
        return GrokNativeSessionOutcome(
            self._public_binding(
                product_id=product_id,
                wish_sha256=wish_sha256,
                constitution_sha256=constitution_sha256,
                run_root=root,
                host_state_root=state_root,
                runtime_config_sha256=identity["runtime_config_sha256"],
                checkpoint_sha256=checkpoint_sha256,
            )
        )

    def resume(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        prompt: str,
        goal_stage: str,
        goal_checkpoint_sha256: str,
    ) -> GrokNativeSessionOutcome:
        root, state_root, session_path, goal_path = self._binding_paths(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
        )
        prompt = _validated_prompt(prompt)
        goal_stage, goal_checkpoint_sha256 = _validated_goal_binding(
            goal_stage, goal_checkpoint_sha256
        )
        policy = _prepare_policy(root, state_root, create_missing=False)
        environment = policy.environment(self._environment_source)
        _ensure_project_repository(
            root,
            policy,
            runner=self._git_runner,
            source_environment=self._environment_source,
            allow_init=False,
        )
        inspect_sha256 = self._inspect(root, policy, environment)
        session_id, checkpoint_sha256, runtime_config_sha256 = self._load_checkpoint(
            path=session_path,
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=root,
            host_state_root=state_root,
            policy=policy,
            current_inspect_sha256=inspect_sha256,
        )
        observed = self._load_goal_state(
            goal_path, session_checkpoint_sha256=checkpoint_sha256
        )
        prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        previous: Optional[_GrokGoalState] = None
        prepared: Optional[_GrokGoalState] = None
        if observed.status == "prepared":
            raise ContractError(
                "Grok native Goal prompt delivery is ambiguous; it cannot be resumed"
            )
        if observed.status == "returned":
            raise ContractError(
                "Grok returned Goal is awaiting host acknowledgement"
            )
        if observed.status == "active":
            if (
                observed.stage != goal_stage
                or observed.stage_checkpoint_sha256 != goal_checkpoint_sha256
                or observed.prompt_sha256 != prompt_sha256
            ):
                raise ContractError(
                    "Grok cannot replace an interrupted active Goal"
                )
            invocation_state = observed
            stream_prompt = GROK_GOAL_RESUME_PROMPT
        else:
            if (
                observed.stage == goal_stage
                and observed.stage_checkpoint_sha256 == goal_checkpoint_sha256
                and observed.prompt_sha256 == prompt_sha256
            ):
                raise ContractError("Grok completed Goal cannot be run as a new attempt")
            previous = observed
            prepared = _GrokGoalState(
                session_checkpoint_sha256=checkpoint_sha256,
                stage=goal_stage,
                stage_checkpoint_sha256=goal_checkpoint_sha256,
                prompt_sha256=prompt_sha256,
                attempt=observed.attempt + 1,
                status="prepared",
                revision=observed.revision + 1,
            )
            _replace_checkpoint(goal_path, prepared.to_dict())
            invocation_state = prepared
            stream_prompt = prompt
        spawned = False

        def activate() -> None:
            nonlocal spawned
            if prepared is not None:
                _replace_checkpoint(
                    goal_path, _goal_with_status(invocation_state, "active").to_dict()
                )
            spawned = True

        try:
            self._stream(
                command=self._command(
                    run_root=root,
                    policy=policy,
                    session_id=session_id,
                    prompt=stream_prompt,
                    resume=True,
                ),
                run_root=root,
                environment=environment,
                expected_session_id=session_id,
                status_turn=False,
                on_spawn=activate,
            )
            self._stream(
                command=self._command(
                    run_root=root,
                    policy=policy,
                    session_id=session_id,
                    prompt=GROK_GOAL_STATUS_PROMPT,
                    resume=True,
                ),
                run_root=root,
                environment=environment,
                expected_session_id=session_id,
                status_turn=True,
            )
        except _GrokProcessNotSpawned:
            if prepared is not None and previous is not None and not spawned:
                current = self._load_goal_state(
                    goal_path, session_checkpoint_sha256=checkpoint_sha256
                )
                if current != prepared:
                    raise GrokInvocationError(
                        "Grok unlaunched Goal could not be rolled back safely"
                    ) from None
                _replace_checkpoint(goal_path, previous.to_dict())
            raise
        _replace_checkpoint(
            goal_path, _goal_with_status(invocation_state, "returned").to_dict()
        )
        return GrokNativeSessionOutcome(
            self._public_binding(
                product_id=product_id,
                wish_sha256=wish_sha256,
                constitution_sha256=constitution_sha256,
                run_root=root,
                host_state_root=state_root,
                runtime_config_sha256=runtime_config_sha256,
                checkpoint_sha256=checkpoint_sha256,
            )
        )

    def _static_goal_state(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        prompt: str,
        goal_stage: str,
        goal_checkpoint_sha256: str,
    ) -> tuple[Path, _GrokGoalState]:
        root, state_root, session_path, goal_path = self._binding_paths(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
        )
        prompt = _validated_prompt(prompt)
        goal_stage, goal_checkpoint_sha256 = _validated_goal_binding(
            goal_stage, goal_checkpoint_sha256
        )
        policy = _prepare_policy(root, state_root, create_missing=False)
        _ensure_project_repository(
            root,
            policy,
            runner=self._git_runner,
            source_environment=self._environment_source,
            allow_init=False,
        )
        unused_session_id, checkpoint_sha256, unused_runtime = self._load_checkpoint(
            path=session_path,
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=root,
            host_state_root=state_root,
            policy=policy,
            current_inspect_sha256=None,
        )
        state = self._load_goal_state(
            goal_path, session_checkpoint_sha256=checkpoint_sha256
        )
        if (
            state.stage != goal_stage
            or state.stage_checkpoint_sha256 != goal_checkpoint_sha256
            or state.prompt_sha256 != hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        ):
            raise ContractError(
                "Grok native Goal does not match its current host attempt"
            )
        return goal_path, state

    def goal_disposition(self, **arguments: Any) -> str:
        """Return durable Goal state without launching Grok or spending tokens."""

        unused_path, state = self._static_goal_state(**arguments)
        return state.status

    def acknowledge_goal(self, **arguments: Any) -> None:
        """Complete a returned Goal only after the host validates its proposal."""

        path, state = self._static_goal_state(**arguments)
        if state.status == "completed":
            return
        if state.status != "returned":
            raise ContractError(
                "Grok native Goal acknowledgement requires an attested return"
            )
        completed = _goal_with_status(
            state, "completed", revision=state.revision + 1
        )
        _replace_checkpoint(path, completed.to_dict())


__all__ = [
    "DEFAULT_GROK_MAX_TURNS",
    "DEFAULT_GROK_TIMEOUT_SECONDS",
    "GROK_ALLOWED_TOOLS",
    "GROK_MODEL",
    "GROK_PERMISSION_MODE",
    "GROK_SESSION_CHECKPOINT_KIND",
    "GROK_SESSION_CHECKPOINT_NAME",
    "GROK_SUBPROCESS_ENVIRONMENT_ALLOWLIST",
    "MINIMUM_GROK_NATIVE_RUNTIME_VERSION",
    "PINNED_GROK_NATIVE_RUNTIME_VERSION",
    "GrokInvocationError",
    "GrokNativeSessionBinding",
    "GrokNativeSessionLauncher",
    "GrokNativeSessionOutcome",
    "grok_subprocess_environment",
    "grok_supports_native_workshop",
]
