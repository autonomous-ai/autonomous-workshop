"""Host side of the make_round guard (ADR 0080).

A new run's host state holds the guard hook, ``make_round_guard.py``, and the
nonce table it appends to, outside the run workspace. The native launchers
register that exact script as a ``PreToolUse`` hook whenever it is installed;
a frozen run has none and launches unchanged. At Make acceptance the host
refuses any Component round whose recorded worker nonce it did not issue to a
``component-worker`` for that Component.

On Claude Code, which runs without a sandbox, this is tamper-resistant, not
tamper-proof: an agent can reach host state with its own tools. Nothing here
spawns, schedules or judges an agent.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import stat
import sys
import zipfile
from importlib import resources
from pathlib import Path
from typing import Optional

from workshop.errors import ContractError, StateConflict
from workshop.make.make_round_guard import COMPONENT_WORKER, NONCE_TABLE_NAME

MAKE_ROUND_GUARD_DIRECTORY = "make-round-guard"
MAKE_ROUND_GUARD_SCRIPT = "make_round_guard.py"
HOOK_TIMEOUT_SECONDS = 10
MAX_NONCE_TABLE_BYTES = 8 * 1024 * 1024
# Kept in step with ``REVISION_INPUT`` in ``workshop.workflow.revision``; the
# make package does not import the workflow package.
REVISION_SOURCE = "revision-source.zip"
_COMPONENT_ROUNDS = ("measure", "component-rounds")


def make_round_guard_bytes() -> bytes:
    """The packaged guard hook's exact bytes."""

    return resources.files("workshop.make").joinpath(MAKE_ROUND_GUARD_SCRIPT).read_bytes()


def install_make_round_guard(host_state_root: Path) -> str:
    """Materialize the guard into fresh host state; return its sha256."""

    content = make_round_guard_bytes()
    directory = Path(host_state_root) / MAKE_ROUND_GUARD_DIRECTORY
    directory.mkdir(mode=0o700)
    os.chmod(directory, 0o700)
    script = directory / MAKE_ROUND_GUARD_SCRIPT
    descriptor = os.open(str(script), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    try:
        os.write(descriptor, content)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.chmod(script, 0o400)
    return hashlib.sha256(content).hexdigest()


def installed_make_round_guard(host_state_root: Path) -> Optional[Path]:
    """The installed guard script, or None for a run created without one."""

    script = Path(host_state_root) / MAKE_ROUND_GUARD_DIRECTORY / MAKE_ROUND_GUARD_SCRIPT
    if script.is_symlink() or not script.is_file():
        return None
    return script


def verify_make_round_guard(host_state_root: Path, expected_sha256: str) -> Path:
    """Refuse a guard that is missing or differs from the bytes the run sealed."""

    script = installed_make_round_guard(host_state_root)
    if script is None:
        raise StateConflict("the run's make_round guard is missing")
    if hashlib.sha256(script.read_bytes()).hexdigest() != expected_sha256:
        raise StateConflict("the run's make_round guard differs from its sealed bytes")
    return script


def _hook_command(script: Path) -> str:
    return shlex.join([str(Path(sys.executable).absolute()), str(script)])


def claude_hook_settings(script: Path) -> str:
    """The ``--settings`` JSON registering the guard for a Claude Code session."""

    return json.dumps(
        {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": _hook_command(script),
                                "timeout": HOOK_TIMEOUT_SECONDS,
                            }
                        ],
                    }
                ]
            }
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def codex_hook_arguments(script: Path) -> tuple[str, ...]:
    """The ``codex exec`` arguments registering the guard for every tool call.

    Workshop launches Codex with ``--ignore-user-config``, so a project hooks
    file is never read; the hook is passed at launch instead. The host wrote
    the script itself, which is what the hook-trust bypass requires.
    """

    return (
        "--config",
        "hooks.PreToolUse=[{hooks=[{type=\"command\",command=%s,timeout=%d}]}]"
        % (json.dumps(_hook_command(script)), HOOK_TIMEOUT_SECONDS),
        "--dangerously-bypass-hook-trust",
    )


def _issued_worker_nonces(host_state_root: Path) -> dict[str, str]:
    """Nonce -> the Component source it was issued to a worker for."""

    table = Path(host_state_root) / MAKE_ROUND_GUARD_DIRECTORY / NONCE_TABLE_NAME
    if not table.exists() and not table.is_symlink():
        return {}
    try:
        identity = table.lstat()
        if not stat.S_ISREG(identity.st_mode) or identity.st_size > MAX_NONCE_TABLE_BYTES:
            raise ValueError("not a bounded regular file")
        issued: dict[str, str] = {}
        for line in table.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if not isinstance(record, dict) or not isinstance(record.get("nonce"), str):
                raise ValueError("invalid record")
            if record.get("agent_type") == COMPONENT_WORKER and isinstance(
                record.get("component"), str
            ):
                issued[record["nonce"]] = record["component"]
    except (OSError, UnicodeError, ValueError) as exc:
        raise StateConflict("the make_round guard nonce table is invalid") from exc
    return issued


def _carried_summaries(run_root: Path) -> set[str]:
    """sha256 of every Component round summary the revision source sealed."""

    archive_path = Path(run_root) / REVISION_SOURCE
    if archive_path.is_symlink() or not archive_path.is_file():
        return set()
    digests = set()
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                parts = info.filename.split("/")
                if (
                    parts[-1] == "summary.json"
                    and "component-rounds" in parts
                    and not info.is_dir()
                ):
                    digests.add(hashlib.sha256(archive.read(info)).hexdigest())
    except (OSError, zipfile.BadZipFile) as exc:
        raise StateConflict("the sealed revision source is unreadable") from exc
    return digests


def verify_component_round_nonces(
    project: Path, host_state_root: Path, *, run_root: Path
) -> None:
    """Refuse a Component round no ``component-worker`` ran (ADR 0080).

    Every round summary under ``measure/component-rounds`` must carry a nonce
    the guard issued to a worker for that Component, each used by one round
    only. A summary whose exact bytes the revision source sealed was carried
    forward by a correction and keeps the evidence it already had.
    """

    rounds = Path(project).joinpath(*_COMPONENT_ROUNDS)
    if not rounds.is_dir():
        return
    summaries = sorted(rounds.glob("*/r[0-9][0-9][0-9][0-9]/summary.json"))
    if not summaries:
        return
    issued = _issued_worker_nonces(host_state_root)
    carried: Optional[set[str]] = None
    used: dict[str, str] = {}
    for path in summaries:
        role = path.parent.parent.name
        label = "%s %s" % (role, path.parent.name)
        content = path.read_bytes()
        try:
            summary = json.loads(content)
        except ValueError as exc:
            raise ContractError("Component round %s summary is not JSON" % label) from exc
        nonce = summary.get("worker_nonce") if isinstance(summary, dict) else None
        if isinstance(nonce, str) and issued.get(nonce) == "part_%s.step.py" % role:
            if nonce in used:
                raise ContractError(
                    "Component round %s reuses the worker nonce of %s" % (label, used[nonce])
                )
            used[nonce] = label
            continue
        if carried is None:
            carried = _carried_summaries(run_root)
        if hashlib.sha256(content).hexdigest() in carried:
            continue
        raise ContractError(
            "Component round %s was not run by a component-worker: its worker "
            "nonce is missing or was not issued for part_%s.step.py. Have a "
            "component-worker rerun that Component's round." % (label, role)
        )


__all__ = [
    "MAKE_ROUND_GUARD_DIRECTORY",
    "MAKE_ROUND_GUARD_SCRIPT",
    "claude_hook_settings",
    "codex_hook_arguments",
    "install_make_round_guard",
    "installed_make_round_guard",
    "make_round_guard_bytes",
    "verify_component_round_nonces",
    "verify_make_round_guard",
]
