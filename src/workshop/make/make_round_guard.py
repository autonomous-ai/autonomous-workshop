#!/usr/bin/env python3
"""Pre-tool hook deciding which agent may run which make_round call (ADR 0080).

The host copies this file's exact bytes into a run's private host state and
registers it as a ``PreToolUse`` command hook for the native session, root
and subagents alike. The runtime names the calling subagent in the hook input
(``agent_type``); a root call carries none.

- A Component round (``--component`` without ``--record-review``) runs only
  from a ``component-worker``. The hook issues it a one-time nonce, appends it
  to the nonce table beside this file, and rewrites the command to pass it as
  ``--worker-nonce``. make_round records the nonce in the round, and the host
  refuses a Make proposal holding a Component round whose nonce it did not
  issue to a worker for that Component.
- ``--record-review``, ``--record-visual`` and assembly rounds run only from
  the root Workshop Manager.

The hook decides who may run make_round, not who may spawn whom. It runs as a
standalone script with the standard library only; it makes no model call.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shlex
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

NONCE_TABLE_NAME = "worker-nonces.jsonl"
NONCE_FLAG = "--worker-nonce"
COMPONENT_WORKER = "component-worker"
SCRIPT_NAME = "make_round"
_COMMAND_KEYS = ("command", "cmd")
_SEPARATORS = frozenset({"&&", "||", ";", "|", "&", "(", ")", ";;", "|&"})
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_PYTHON = re.compile(r"^python[0-9.]*$")
_PYTHON_VARIABLES = frozenset({"$WORKSHOP_PYTHON", "${WORKSHOP_PYTHON}"})
_SHELLS = frozenset({"bash", "sh", "zsh", "dash"})
_WRAPPERS = frozenset({"exec", "nohup", "time", "command", "builtin"})
# The script token, optionally closed by a quote, followed by the end of the
# token. The nonce goes right after it, before the call's own arguments.
_SCRIPT_TOKEN = re.compile(r"make_round([\"']?)(?=[\s;&|)]|$)")

Issuer = Callable[[Mapping[str, Any], str], str]


def _segments(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    segments: list[list[str]] = [[]]
    for token in lexer:
        if token in _SEPARATORS:
            segments.append([])
        else:
            segments[-1].append(token)
    return [segment for segment in segments if segment]


def _strip_prefix(tokens: list[str]) -> list[str]:
    """Drop assignments and the wrappers that only run the command after them."""

    index = 0
    while index < len(tokens):
        token = tokens[index]
        name = os.path.basename(token)
        if _ASSIGNMENT.match(token) or name in _WRAPPERS:
            index += 1
        elif name == "env":
            index += 1
            while index < len(tokens) and (
                tokens[index].startswith("-") or _ASSIGNMENT.match(tokens[index])
            ):
                index += 1
        elif name in ("timeout", "nice"):
            index += 1
            while index < len(tokens) and tokens[index].startswith("-"):
                index += 2 if tokens[index] in ("-n", "-s", "-k") else 1
            if name == "timeout" and index < len(tokens):
                index += 1  # the duration
        else:
            break
    return tokens[index:]


def make_round_calls(command: str) -> Optional[list[list[str]]]:
    """The argument lists of every make_round call in one shell command.

    ``None`` means the command names make_round but cannot be parsed. Reading
    the script (``sed``, ``grep``, ``cat``) is not a call. A call hidden inside
    another program (``python -c``) is not seen here; the nonce catches it.
    """

    try:
        segments = _segments(command)
    except ValueError:
        return None
    calls: list[list[str]] = []
    for segment in segments:
        tokens = _strip_prefix(segment)
        if not tokens:
            continue
        program = os.path.basename(tokens[0])
        if program in _SHELLS:
            # ``bash -c '...'`` or ``bash -lc '...'``: read the script it runs.
            flag = next(
                (index for index, token in enumerate(tokens[1:], 1)
                 if re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", token)),
                None,
            )
            if flag is not None and flag + 1 < len(tokens):
                nested = make_round_calls(tokens[flag + 1])
                if nested is None:
                    return None
                calls.extend(nested)
            continue
        if program == SCRIPT_NAME:
            calls.append(tokens[1:])
            continue
        if _PYTHON.match(program) or tokens[0] in _PYTHON_VARIABLES:
            index = 1
            while index < len(tokens) and tokens[index].startswith("-") and tokens[index] not in ("-c", "-m"):
                index += 1
            if index < len(tokens) and os.path.basename(tokens[index]) == SCRIPT_NAME:
                calls.append(tokens[index + 1:])
    return calls


def _option(arguments: list[str], name: str) -> Optional[str]:
    for index, argument in enumerate(arguments):
        if argument == name and index + 1 < len(arguments):
            return arguments[index + 1]
        if argument.startswith(name + "="):
            return argument[len(name) + 1:]
    return None


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Workshop make_round guard (ADR 0080): " + reason,
        }
    }


def decide(event: Mapping[str, Any], *, issue: Issuer) -> Optional[dict[str, Any]]:
    """The hook output for one tool call, or ``None`` to let it run unchanged."""

    tool_input = event.get("tool_input")
    if not isinstance(tool_input, Mapping):
        return None
    key = next(
        (name for name in _COMMAND_KEYS if isinstance(tool_input.get(name), str)), None
    )
    if key is None or SCRIPT_NAME not in tool_input[key]:
        return None
    command = tool_input[key]
    calls = make_round_calls(command)
    if calls is None:
        return _deny("this command names make_round but cannot be parsed; run make_round as one plain command")
    if not calls:
        return None
    if len(calls) > 1:
        return _deny("run one make_round call per command")
    arguments = calls[0]
    if any(argument == NONCE_FLAG or argument.startswith(NONCE_FLAG + "=") for argument in arguments):
        return _deny("%s is issued by Workshop; never pass one" % NONCE_FLAG)
    if any(argument in ("--self-check", "-h", "--help") for argument in arguments):
        return None
    agent_type = event.get("agent_type")
    is_root = not agent_type and not event.get("agent_id")
    component = _option(arguments, "--component")
    if component is not None and "--record-review" not in arguments and not any(
        argument.startswith("--record-review=") for argument in arguments
    ):
        if agent_type != COMPONENT_WORKER:
            return _deny(
                "only a component-worker runs a Component's rounds; spawn one "
                "component-worker for %s and give it that Component's inputs" % component
            )
        if len(_SCRIPT_TOKEN.findall(command)) != 1:
            return _deny("name make_round exactly once in the command")
        nonce = issue(event, os.path.basename(component))
        rewritten = _SCRIPT_TOKEN.sub(
            lambda match: match.group(0) + " %s %s" % (NONCE_FLAG, nonce), command, count=1
        )
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {**dict(tool_input), key: rewritten},
            }
        }
    if not is_root:
        return _deny(
            "only the Workshop Manager records a Component Review, runs an "
            "assembly round or records assembly feedback"
        )
    return None


def _table_issuer(table: Path) -> Issuer:
    def issue(event: Mapping[str, Any], component: str) -> str:
        nonce = secrets.token_hex(16)
        record = {
            "nonce": nonce,
            "component": component,
            "agent_type": event.get("agent_type"),
            "agent_id": event.get("agent_id"),
            "session_id": event.get("session_id"),
            "tool_use_id": event.get("tool_use_id"),
        }
        line = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        descriptor = os.open(str(table), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.write(descriptor, line)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return nonce

    return issue


def main() -> int:
    try:
        event = json.loads(sys.stdin.read())
        if not isinstance(event, dict):
            raise ValueError("hook input must be an object")
    except ValueError:
        print(json.dumps(_deny("the hook input is not a JSON object")))
        return 0
    table = Path(__file__).resolve().parent / NONCE_TABLE_NAME
    try:
        output = decide(event, issue=_table_issuer(table))
    except OSError:
        output = _deny("the worker nonce could not be recorded")
    if output is not None:
        print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
