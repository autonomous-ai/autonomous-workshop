"""Fixed Make role agents materialized beside the Inventor roster (ADR 0077).

A new product run receives two declarative Codex custom agents: the
Component Worker, which repairs one Component's source until build and print
pass, and the Component Reviewer, which alone views that Component's images.
The files only declare the roles. Codex owns spawning, routing and waiting;
the Workshop Manager decides when to use them. Nothing here schedules agents.
"""

from __future__ import annotations

import tomllib
from importlib import resources
from typing import Any, Mapping

from workshop.errors import ContractError

COMPONENT_WORKER = "component-worker"
COMPONENT_REVIEWER = "component-reviewer"
MAKE_ROLE_AGENT_NAMES = (COMPONENT_REVIEWER, COMPONENT_WORKER)
MAX_MAKE_ROLE_AGENT_BYTES = 64 * 1024

_REQUIRED_FIELDS = frozenset({"name", "description", "developer_instructions"})
_OPTIONAL_FIELDS = frozenset({"model_reasoning_effort"})
_ROLE_REASONING_EFFORTS = ("low", "medium", "high", "xhigh")


def make_role_agent_path(name: str) -> str:
    """Return the run-relative path of one fixed role agent."""

    if name not in MAKE_ROLE_AGENT_NAMES:
        raise ContractError("%r is not a Make role agent" % (name,))
    return ".codex/agents/%s.toml" % name


def parse_make_role_agent_bytes(name: str, content: bytes) -> Mapping[str, Any]:
    """Validate one role agent's exact bytes against its fixed file name."""

    if name not in MAKE_ROLE_AGENT_NAMES:
        raise ContractError("%r is not a Make role agent" % (name,))
    if (
        not isinstance(content, bytes)
        or not 1 <= len(content) <= MAX_MAKE_ROLE_AGENT_BYTES
    ):
        raise ContractError("Make role agent TOML must be non-empty and bounded")
    try:
        parsed = tomllib.loads(content.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ContractError("Make role agent must contain valid UTF-8 TOML") from exc
    fields = set(parsed)
    if not _REQUIRED_FIELDS <= fields or not fields <= _REQUIRED_FIELDS | _OPTIONAL_FIELDS:
        raise ContractError("Make role agent fields are not canonical")
    if parsed["name"] != name:
        raise ContractError("Make role agent name differs from its file")
    for field in ("description", "developer_instructions"):
        if not isinstance(parsed[field], str) or not parsed[field].strip():
            raise ContractError("Make role agent text is invalid")
    effort = parsed.get("model_reasoning_effort")
    if effort is not None and effort not in _ROLE_REASONING_EFFORTS:
        raise ContractError("Make role agent reasoning effort is unsupported")
    return parsed


def make_role_agent_files() -> dict[str, bytes]:
    """Return every packaged role agent's exact bytes, keyed by agent name."""

    directory = resources.files("workshop.make").joinpath("agents")
    files: dict[str, bytes] = {}
    for name in MAKE_ROLE_AGENT_NAMES:
        content = directory.joinpath(name + ".toml").read_bytes()
        parse_make_role_agent_bytes(name, content)
        files[name] = content
    return files
