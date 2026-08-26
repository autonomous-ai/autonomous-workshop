"""Thin CLI bridge to one native coding-agent session per Wish.

This module deliberately contains no Match, Invent, Make, or Playtest
reasoning.  It creates the private filesystem protocol, binds a native Codex
session to those exact bytes, and exposes a redacted status view.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from workshop.errors import ContractError, StateConflict, WorkshopError
from workshop.runtime import (
    CodexInvocationError,
    CodexNativeSessionLauncher,
    CodexNativeSessionOutcome,
)
from workshop.runtime.agent_assets import product_run_agent_assets
from workshop.runtime.package_data import (
    default_workshop_home,
    packaged_inventors_root,
    product_run_domain_skill_roots,
)
from workshop.wish import Wish
from workshop.workflow import AgentRun, AgentRunCheckpoint


_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_INSTRUCTION_HASH_DOMAIN = b"autonomous-workshop/product-run-instructions/v1\0"
_SESSION_CHECKPOINT_NAME = "codex-session.json"


@dataclass(frozen=True)
class NativeRunPaths:
    """Private sibling roots for agent-visible work and host-only state."""

    container: Path
    workspace: Path
    host_state: Path


def canonical_wish_bytes(wish: Wish) -> bytes:
    """Return the one JSON encoding accepted by :class:`AgentRun`."""

    if not isinstance(wish, Wish):
        raise ContractError("native run requires a validated Wish")
    try:
        return json.dumps(
            wish.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Wish cannot be encoded for a native run") from exc


def materialized_agent_instructions_sha256(
    checkpoint: AgentRunCheckpoint,
) -> str:
    """Bind the exact AGENTS.md and skill bytes already inside a run.

    Resume derives this value from the immutable run manifest, not from the
    current source checkout or installed package.  Updating instructions for a
    future Wish therefore cannot silently change an existing session binding.
    """

    if not isinstance(checkpoint, AgentRunCheckpoint):
        raise ContractError("instruction manifest requires an AgentRun checkpoint")
    selected = {
        path: digest
        for path, digest in checkpoint.input_sha256s.items()
        if path == "AGENTS.md"
        or path.startswith(".agents/skills/")
    }
    required = {
        "AGENTS.md",
        ".agents/skills/autonomous-workshop/SKILL.md",
    }
    if not required <= set(selected):
        raise StateConflict("native run instruction manifest is incomplete")
    digest = hashlib.sha256(_INSTRUCTION_HASH_DOMAIN)
    for relative, content_sha256 in sorted(selected.items()):
        try:
            content_digest = bytes.fromhex(content_sha256)
        except (TypeError, ValueError) as exc:
            raise StateConflict("native run instruction manifest is invalid") from exc
        if len(content_digest) != 32:
            raise StateConflict("native run instruction manifest is invalid")
        encoded_path = relative.encode("utf-8")
        digest.update(len(encoded_path).to_bytes(4, "big"))
        digest.update(encoded_path)
        digest.update(content_digest)
    return digest.hexdigest()


def native_stage_prompt(stage: str) -> str:
    """Give the native session a compact pointer, never Wish or host secrets."""

    if stage not in (
        "wish",
        "match",
        "invent",
        "make",
        "playtest",
        "release",
        "deliver",
    ):
        raise ContractError("native run stage is invalid")
    return (
        "Follow the local AGENTS.md and autonomous-workshop skill. "
        "Perform the current %s stage only. Write the compact result to "
        "agent-outcome.json, then return control to the Workshop host gate."
        % stage
    )


def _validated_product_id(product_id: str) -> str:
    if not isinstance(product_id, str) or _RUN_ID.fullmatch(product_id) is None:
        raise ContractError("native run product id is invalid")
    return product_id


def _existing_real_directory(path: Path, *, label: str) -> Path:
    try:
        identity = path.lstat()
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if path.is_symlink() or not stat.S_ISDIR(identity.st_mode):
        raise StateConflict("%s must be a real directory" % label)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if resolved != path:
        raise StateConflict("%s must not contain symlinks" % label)
    return resolved


def _ensure_private_directory(path: Path, *, label: str) -> Path:
    created = False
    try:
        path.mkdir(mode=0o700)
        created = True
    except FileExistsError:
        pass
    except OSError as exc:
        raise StateConflict("%s could not be created" % label) from exc
    resolved = _existing_real_directory(path, label=label)
    if created:
        os.chmod(resolved, 0o700)
    if stat.S_IMODE(resolved.stat().st_mode) != 0o700:
        raise StateConflict("%s permissions must be 0700" % label)
    return resolved


def _workshop_home() -> Path:
    selected = Path(default_workshop_home()).expanduser()
    if not selected.is_absolute():
        raise ContractError("Workshop home must be absolute")
    try:
        selected.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as exc:
        raise StateConflict("Workshop home could not be created") from exc
    return _existing_real_directory(selected, label="Workshop home")


def _product_run_catalog_root(assets: Any) -> Path:
    if assets.source == "repository":
        repository = assets.constitution.parents[2]
        catalog = repository / "inventors"
    else:
        catalog = packaged_inventors_root()
        if catalog is None:
            raise StateConflict("installed Workshop has no inventor personas")
    return _existing_real_directory(Path(catalog), label="inventor persona catalog")


def native_run_paths(
    product_id: str,
    *,
    create_container: bool = False,
) -> NativeRunPaths:
    """Resolve the deterministic private location for one product id."""

    product_id = _validated_product_id(product_id)
    home = _workshop_home()
    runs = home / "runs"
    if create_container:
        runs = _ensure_private_directory(runs, label="native runs directory")
        container = _ensure_private_directory(
            runs / product_id, label="native product run directory"
        )
    else:
        runs = _existing_real_directory(runs, label="native runs directory")
        container = _existing_real_directory(
            runs / product_id, label="native product run directory"
        )
        if stat.S_IMODE(container.stat().st_mode) != 0o700:
            raise StateConflict("native product run directory permissions must be 0700")
    return NativeRunPaths(
        container=container,
        workspace=container / "workspace",
        host_state=container / "host-state",
    )


def native_run_exists(product_id: str) -> bool:
    """Return whether this id has any native-run state, including partial state."""

    product_id = _validated_product_id(product_id)
    home = Path(default_workshop_home()).expanduser()
    if not home.is_absolute():
        raise ContractError("Workshop home must be absolute")
    candidate = home / "runs" / product_id
    return candidate.exists() or candidate.is_symlink()


def _open_native_run(product_id: str) -> tuple[AgentRun, AgentRunCheckpoint]:
    paths = native_run_paths(product_id)
    run = AgentRun.open(paths.workspace, host_state_root=paths.host_state)
    return run, run.snapshot()


def _launcher_call(
    launcher: CodexNativeSessionLauncher,
    method: str,
    *,
    checkpoint: AgentRunCheckpoint,
    paths: NativeRunPaths,
) -> CodexNativeSessionOutcome:
    arguments = {
        "product_id": checkpoint.product_id,
        "wish_sha256": checkpoint.wish_sha256,
        "constitution_sha256": materialized_agent_instructions_sha256(checkpoint),
        "run_root": paths.workspace,
        "host_state_root": paths.host_state,
        "prompt": native_stage_prompt(checkpoint.stage),
    }
    try:
        return getattr(launcher, method)(**arguments)
    except CodexInvocationError as exc:
        raise WorkshopError("native Codex session did not complete: %s" % exc) from None


def _session_status(paths: NativeRunPaths) -> str:
    checkpoint = paths.host_state / _SESSION_CHECKPOINT_NAME
    if not checkpoint.exists() and not checkpoint.is_symlink():
        return "not-started"
    try:
        identity = checkpoint.lstat()
    except OSError as exc:
        raise StateConflict("native Codex session checkpoint is unavailable") from exc
    if (
        checkpoint.is_symlink()
        or not stat.S_ISREG(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o600
    ):
        raise StateConflict("native Codex session checkpoint is not a private file")
    return "checkpointed"


def _native_receipt(
    checkpoint: AgentRunCheckpoint,
    *,
    session: Optional[CodexNativeSessionOutcome] = None,
    action: str,
    publish_requested: bool = False,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "kind": "native-agent-run",
        "product_id": checkpoint.product_id,
        "status": checkpoint.status,
        "stage": checkpoint.stage,
        "revision": checkpoint.revision,
        "round": checkpoint.round_index,
        "max_rounds": checkpoint.max_rounds,
        "wish_sha256": checkpoint.wish_sha256,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "agent_instructions_sha256": materialized_agent_instructions_sha256(
            checkpoint
        ),
        "invalidated_stages": list(checkpoint.invalidated_stages),
        "action": action,
        "publication": {
            "status": "draft",
            "requested": bool(publish_requested),
            "reason": (
                "No publication or other authenticated effect is performed by "
                "the native product-run session."
            ),
        },
    }
    if session is not None:
        receipt["session"] = session.to_dict()
    return receipt


def start_native_run(
    wish: Wish,
    *,
    publish_requested: bool = False,
) -> Mapping[str, Any]:
    """Persist one Wish and immediately start its whole-run native session."""

    paths = native_run_paths(wish.product_id, create_container=True)
    assets = product_run_agent_assets()
    run = AgentRun.create(
        paths.workspace,
        paths.host_state,
        product_id=wish.product_id,
        wish_bytes=canonical_wish_bytes(wish),
        product_run_constitution_source=assets.constitution,
        skill_root=assets.skill_root,
        domain_skill_roots=product_run_domain_skill_roots(),
        inventor_catalog_root=_product_run_catalog_root(assets),
        max_rounds=4,
    )
    checkpoint = run.snapshot()
    launcher = CodexNativeSessionLauncher()
    session = _launcher_call(
        launcher, "start", checkpoint=checkpoint, paths=paths
    )
    return {
        **_native_receipt(
            checkpoint,
            session=session,
            action="started",
            publish_requested=publish_requested,
        ),
        "wish": wish.to_dict(),
    }


def resume_native_run(
    product_id: str,
    *,
    publish_requested: bool = False,
) -> Mapping[str, Any]:
    """Resume the exact native session, or safely finish an interrupted start."""

    run, checkpoint = _open_native_run(product_id)
    del run
    paths = native_run_paths(product_id)
    launcher = CodexNativeSessionLauncher()
    method = "resume" if _session_status(paths) == "checkpointed" else "start"
    session = _launcher_call(
        launcher, method, checkpoint=checkpoint, paths=paths
    )
    return _native_receipt(
        checkpoint,
        session=session,
        action="resumed" if method == "resume" else "started-after-interruption",
        publish_requested=publish_requested,
    )


def native_run_status(product_id: str) -> Mapping[str, Any]:
    """Return a redacted, validated native checkpoint without running a model."""

    run, checkpoint = _open_native_run(product_id)
    del run
    paths = native_run_paths(product_id)
    return {
        **_native_receipt(checkpoint, action="inspected"),
        "session_status": _session_status(paths),
    }


__all__ = [
    "NativeRunPaths",
    "canonical_wish_bytes",
    "materialized_agent_instructions_sha256",
    "native_run_exists",
    "native_run_paths",
    "native_run_status",
    "native_stage_prompt",
    "resume_native_run",
    "start_native_run",
]
