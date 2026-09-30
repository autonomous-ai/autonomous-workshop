"""Project one canonical custom agent into another Manager's agent format.

Every Inventor and Make role agent is sealed once as a Codex custom agent under
``.codex/agents/``, and that file stays the host identity binding. A Manager
whose native agent directory differs receives the same agent there as well,
rendered deterministically from those exact bytes, so both files always say
the same thing. Only the wait instructions differ, because each runtime waits
for a long command differently.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import PurePosixPath
from typing import Mapping, Optional

from workshop.errors import ContractError

CODEX_AGENT_DIRECTORY = ".codex/agents"
CLAUDE_AGENT_DIRECTORY = ".claude/agents"
MAX_PROJECTED_AGENT_BYTES = 256 * 1024

_FIELDS = frozenset({"name", "description", "developer_instructions"})
_OPTIONAL_FIELDS = frozenset({"model_reasoning_effort"})
_CLAUDE_EFFORTS = ("low", "medium", "high", "xhigh")

# Codex waits for a long command by polling its session; Claude Code's Bash
# tool blocks until the command exits or moves it to the background itself.
_CODEX_WORKER_WAIT = (
    "Start it with `yield_time_ms: 300000`; while it runs, continue it with\n"
    "  an empty `write_stdin` poll at `yield_time_ms: 300000`. The poll returns as\n"
    "  soon as the round exits. Never sleep between polls."
)
_CLAUDE_WORKER_WAIT = (
    "Run it with the Bash tool's `timeout` at 600000. If Claude Code moves\n"
    "  it to the background, wait for its completion notification. Never sleep\n"
    "  or poll between checks."
)
_CLAUDE_REPLACEMENTS = (
    (_CODEX_WORKER_WAIT, _CLAUDE_WORKER_WAIT),
    ("a standard native Codex subagent", "a standard native Claude Code subagent"),
)


def projected_agent_path(manager_directory: str, codex_path: str) -> str:
    """Return where one ``.codex/agents/<name>.toml`` agent lands for a Manager."""

    source = PurePosixPath(codex_path)
    if source.parent.as_posix() != CODEX_AGENT_DIRECTORY or source.suffix != ".toml":
        raise ContractError("agent projection source must be a Codex custom agent")
    if manager_directory != CLAUDE_AGENT_DIRECTORY:
        raise ContractError("no agent projection exists for %s" % manager_directory)
    return "%s/%s.md" % (CLAUDE_AGENT_DIRECTORY, source.stem)


def _yaml_scalar(value: str) -> str:
    # A JSON string is a valid YAML double-quoted scalar.
    return json.dumps(value, ensure_ascii=False)


def claude_agent_bytes(codex_agent: bytes) -> bytes:
    """Render one canonical Codex custom agent as a Claude Code subagent file.

    The model is omitted, so the subagent inherits the Manager's frozen model;
    an explicit reasoning effort carries over as ``effort``. Every runtime
    sentence this module rewrites must be present exactly, so a changed source
    fails closed rather than projecting stale wait instructions.
    """

    try:
        parsed = tomllib.loads(codex_agent.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ContractError("agent projection source must be UTF-8 TOML") from exc
    fields = set(parsed)
    if not _FIELDS <= fields or not fields <= _FIELDS | _OPTIONAL_FIELDS:
        raise ContractError("agent projection source fields are not canonical")
    if not all(isinstance(parsed[name], str) and parsed[name] for name in _FIELDS):
        raise ContractError("agent projection source text is invalid")
    instructions = parsed["developer_instructions"]
    for codex_text, claude_text in _CLAUDE_REPLACEMENTS:
        count = instructions.count(codex_text)
        if count > 1:
            raise ContractError("agent projection source repeats a runtime sentence")
        instructions = instructions.replace(codex_text, claude_text)
    for fragment in ("yield_time_ms", "write_stdin", "wait_agent"):
        if fragment in instructions:
            raise ContractError(
                "agent projection source keeps a Codex-only wait instruction"
            )
    effort: Optional[str] = parsed.get("model_reasoning_effort")
    if effort is not None and effort not in _CLAUDE_EFFORTS:
        raise ContractError("agent projection effort is unsupported")
    lines = [
        "---",
        "name: %s" % _yaml_scalar(parsed["name"]),
        "description: %s" % _yaml_scalar(parsed["description"]),
    ]
    if effort is not None:
        lines.append("effort: %s" % effort)
    lines.append("---")
    rendered = ("\n".join(lines) + "\n" + instructions.strip("\n") + "\n").encode(
        "utf-8"
    )
    if len(rendered) > MAX_PROJECTED_AGENT_BYTES:
        raise ContractError("projected agent exceeds its limit")
    return rendered


def project_agents(
    manager_directory: str, codex_agents: Mapping[str, bytes]
) -> dict[str, bytes]:
    """Project every ``.codex/agents`` file into a Manager's agent directory.

    Codex needs no projection. A Manager this module cannot render keeps only
    the Codex files, as before.
    """

    if manager_directory != CLAUDE_AGENT_DIRECTORY:
        return {}
    return {
        projected_agent_path(manager_directory, path): claude_agent_bytes(content)
        for path, content in sorted(codex_agents.items())
    }


__all__ = [
    "CLAUDE_AGENT_DIRECTORY",
    "CODEX_AGENT_DIRECTORY",
    "claude_agent_bytes",
    "project_agents",
    "projected_agent_path",
]
