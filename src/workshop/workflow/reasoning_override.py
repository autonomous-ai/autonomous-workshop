"""Auditable operator reasoning changes without rewriting frozen run inputs."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping
from uuid import UUID

from workshop._validation import require_exact_version, require_sha256, require_utc_timestamp
from workshop.errors import ContractError, StateConflict
from workshop.runtime.codex import CODEX_PERMISSION_PROFILE, CODEX_SESSION_CHECKPOINT_KIND
from workshop.runtime.managers import MANAGER_PROJECT_PATH, manager_runtime_selection
from workshop.workflow.budgets import BUDGETS_CAPABILITY_PATH
from workshop.workflow.token_budget import TOKEN_BUDGET_CAPABILITY_PATH


REASONING_OVERRIDE_NAME = "reasoning-effort.json"
_KIND = "autonomous-workshop.reasoning-effort-override"


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def validate_reasoning_selection(checkpoint, effort: str) -> None:
    """Only explicitly selected, profile-bound Codex token runs can opt in."""
    if (
        checkpoint.manager_id != "codex"
        or checkpoint.manager_model is None
        or checkpoint.manager_reasoning_effort is None
        or any(path not in checkpoint.input_sha256s for path in (
            MANAGER_PROJECT_PATH, BUDGETS_CAPABILITY_PATH, TOKEN_BUDGET_CAPABILITY_PATH,
        ))
    ):
        raise ContractError(
            "reasoning effort override requires a profile-bound Codex token-budget product"
        )
    selected = manager_runtime_selection(
        checkpoint.manager_id, model=checkpoint.manager_model, reasoning_effort=effort,
    )
    if selected.model != checkpoint.manager_model or selected.reasoning_effort != effort:
        raise ContractError("reasoning effort override must preserve the frozen model")


def reasoning_override_binding(paths, checkpoint, session: Mapping[str, Any]) -> dict:
    """Validate current session bytes, then retain only stable session identity.

    Native launch still verifies the complete runtime configuration. Constitution,
    CLI version and session checkpoint hashes can change through existing host
    migrations; they are deliberately not frozen by this additional record.
    """
    validate_reasoning_selection(checkpoint, checkpoint.manager_reasoning_effort)
    fields = {
        "schema_version", "kind", "product_id", "wish_sha256", "constitution_sha256",
        "run_root_sha256", "host_state_root_sha256", "runtime_config_sha256",
        "cli_version", "permission_profile", "native_web_search", "thread_id",
        "checkpoint_sha256",
    }
    try:
        if set(session) != fields or not isinstance(session.get("thread_id"), str):
            raise ValueError
        if str(UUID(session["thread_id"])) != session["thread_id"]:
            raise ValueError
        for key in fields:
            if key.endswith("_sha256"):
                require_sha256(session[key])
        require_exact_version(session["cli_version"])
        if (
            type(session["schema_version"]) is not int or session["schema_version"] != 1
            or session["kind"] != CODEX_SESSION_CHECKPOINT_KIND
            or session["permission_profile"] != CODEX_PERMISSION_PROFILE
            or session["native_web_search"] is not True
            or session["product_id"] != checkpoint.product_id
            or session["wish_sha256"] != checkpoint.wish_sha256
            or session["run_root_sha256"] != hashlib.sha256(str(paths.workspace).encode()).hexdigest()
            or session["host_state_root_sha256"] != hashlib.sha256(str(paths.host_state).encode()).hexdigest()
            or session["checkpoint_sha256"] != _digest({
                key: value for key, value in session.items() if key != "checkpoint_sha256"
            })
        ):
            raise ValueError
    except (ContractError, ValueError, TypeError) as exc:
        raise StateConflict("reasoning effort native session binding is invalid") from exc
    return {
        "product_id": checkpoint.product_id,
        "wish_sha256": checkpoint.wish_sha256,
        "manager_sha256": checkpoint.input_sha256s[MANAGER_PROJECT_PATH],
        "runtime_profile_sha256": checkpoint.input_sha256s[BUDGETS_CAPABILITY_PATH],
        "model": checkpoint.manager_model,
        "initial_effort": checkpoint.manager_reasoning_effort,
        "thread_id": session["thread_id"],
        "run_root_sha256": session["run_root_sha256"],
        "host_state_root_sha256": session["host_state_root_sha256"],
    }


def validate_reasoning_override(value, *, binding, checkpoint) -> dict:
    try:
        if (
            not isinstance(value, dict)
            or set(value) != {"schema_version", "kind", "binding", "changes", "record_sha256"}
            or type(value["schema_version"]) is not int or value["schema_version"] != 1
            or value["kind"] != _KIND or value["binding"] != binding
            or not isinstance(value["changes"], list) or not value["changes"]
            or value["record_sha256"] != _digest({
                key: item for key, item in value.items() if key != "record_sha256"
            })
        ):
            raise ValueError
        previous = binding["initial_effort"]
        for change in value["changes"]:
            if (
                not isinstance(change, dict)
                or set(change) != {"previous_effort", "effort", "requested_at", "checkpoint_sha256", "runtime_config_sha256"}
                or change["previous_effort"] != previous or change["effort"] == previous
            ):
                raise ValueError
            validate_reasoning_selection(checkpoint, change["effort"])
            require_utc_timestamp(change["requested_at"])
            require_sha256(change["checkpoint_sha256"])
            require_sha256(change["runtime_config_sha256"])
            previous = change["effort"]
    except (ContractError, ValueError, TypeError) as exc:
        raise StateConflict("reasoning effort override binding or history is invalid") from exc
    return value


def append_reasoning_override(previous, *, binding, checkpoint, session, effort, requested_at):
    """Return one atomic history snapshot, or None for an unchanged selection."""
    validate_reasoning_selection(checkpoint, effort)
    current = binding["initial_effort"] if previous is None else previous["changes"][-1]["effort"]
    if current == effort:
        return None
    value = {
        "schema_version": 1, "kind": _KIND, "binding": binding,
        "changes": ([] if previous is None else previous["changes"]) + [{
            "previous_effort": current, "effort": effort, "requested_at": requested_at,
            "checkpoint_sha256": checkpoint.checkpoint_sha256,
            "runtime_config_sha256": session["runtime_config_sha256"],
        }],
    }
    value["record_sha256"] = _digest(value)
    return validate_reasoning_override(value, binding=binding, checkpoint=checkpoint)
