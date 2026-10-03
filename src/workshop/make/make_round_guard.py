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
- ``--record-review``, ``--record-unlock`` (ADR 0081), ``--record-visual``,
  assembly rounds, and the checks that span Components -- the Shared Helper
  check ``--shared-helpers`` and the Coupled Interface check ``--interface``
  (ADR 0082) -- run only from the root Workshop Manager.

On Claude Code the same script also keeps the evidence that binds a Component
Review to its reviewer (ADR 0081, issue #77). It is registered for ``Read``
and ``SubagentStart`` as well: every subagent the runtime starts is appended
to the subagent log, and every ``Read`` by a ``component-reviewer`` or a
``contract-reviewer`` (ADR 0085) is appended to the reviewer read log with
the agent id, the resolved path and the sha256 of the bytes it read. A
``Read`` is never denied. The host checks each recorded review against both
logs.

Contract Amendments (ADR 0085): ``--propose-amendment`` and
``--record-amendment-review`` are the root's; ``--contract-amendments`` only
lists them, for anyone.

Blocked Reports (issue #88): ``--report-blocked`` runs only from a
``component-worker`` and receives no nonce, since it builds nothing;
``--clear-blocked`` is the root's. Both work without this hook; the hook only
keeps each to its role. On Claude Code the script is also registered for the
root's ``Stop`` event and refuses the turn end while the current Make
attempt holds an open Blocked Report, unless the turn ends on a recorded
need. ``blocked_reports`` reads the ledger; the host imports it from here.

The hook decides who may run make_round, not who may spawn whom. It runs as a
standalone script with the standard library only; it makes no model call.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shlex
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

NONCE_TABLE_NAME = "worker-nonces.jsonl"
READ_LOG_NAME = "reviewer-reads.jsonl"
SUBAGENT_LOG_NAME = "subagents.jsonl"
COMPONENT_REVIEWER = "component-reviewer"
# ADR 0085: the fresh reader who confirms a Contract Amendment.
CONTRACT_REVIEWER = "contract-reviewer"
_LOGGED_READERS = frozenset({COMPONENT_REVIEWER, CONTRACT_REVIEWER})
# A file larger than any packet image is logged without a hash.
MAX_HASHED_READ_BYTES = 64 * 1024 * 1024
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
# The script name at the end of its token. The nonce goes right after it,
# before the call's own arguments; the rewrite is re-parsed before it is used.
_SCRIPT_TOKEN = re.compile(r"make_round(?=[\s;&|)\"']|$)")
# A record about a Component that builds nothing, or a check that spans
# Components (ADR 0082); only the root makes one.
_ROOT_RECORDS = ("--record-review", "--record-unlock", "--shared-helpers", "--interface")
# Blocked Reports (issue #88): the worker's report, and the status anyone reads.
REPORT_BLOCKED = "--report-blocked"
BLOCKED_STATUS = "--blocked-reports"
AMENDMENT_STATUS = "--contract-amendments"
BLOCKED_REPORTS_NAME = "blocked-reports.jsonl"
MAX_BLOCKED_LEDGER_BYTES = 1024 * 1024
OPEN_BLOCKED = frozenset({"open", "waiting"})

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


def _flag(arguments: list[str], name: str) -> bool:
    return any(argument == name or argument.startswith(name + "=") for argument in arguments)


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
    if any(argument in ("--self-check", "-h", "--help", BLOCKED_STATUS, AMENDMENT_STATUS)
           for argument in arguments):
        return None
    agent_type = event.get("agent_type")
    is_root = not agent_type and not event.get("agent_id")
    component = _option(arguments, "--component")
    if _flag(arguments, REPORT_BLOCKED):
        # A Blocked Report builds nothing, so it takes no nonce (issue #88).
        if agent_type != COMPONENT_WORKER:
            return _deny(
                "only a component-worker reports its Component blocked; answer a "
                "Blocked Report with --clear-blocked"
            )
        return None
    if component is not None and not any(
        argument == flag or argument.startswith(flag + "=")
        for argument in arguments
        for flag in _ROOT_RECORDS
    ):
        if agent_type != COMPONENT_WORKER:
            return _deny(
                "only a component-worker runs a Component's rounds; spawn one "
                "component-worker for %s and give it that Component's inputs" % component
            )
        if len(_SCRIPT_TOKEN.findall(command)) != 1:
            return _deny("name make_round exactly once in the command")
        rewritten = _SCRIPT_TOKEN.sub(
            lambda match: match.group(0) + " %s %s" % (NONCE_FLAG, "0" * 32), command, count=1
        )
        # A quoted script path would swallow the nonce into the path; refuse
        # it rather than issue a nonce the round never records.
        if make_round_calls(rewritten) != [[NONCE_FLAG, "0" * 32, *arguments]]:
            return _deny("run make_round with an unquoted script path, as one plain command")
        nonce = issue(event, os.path.basename(component))
        rewritten = rewritten.replace("%s %s" % (NONCE_FLAG, "0" * 32), "%s %s" % (NONCE_FLAG, nonce), 1)
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {**dict(tool_input), key: rewritten},
            }
        }
    if not is_root:
        return _deny(
            "only the Workshop Manager records a Component Review or an "
            "assembly unlock, runs an assembly round, the Shared Helper check or "
            "an Interface check, records assembly feedback, clears a Blocked Report, "
            "or proposes or records a Contract Amendment"
        )
    return None


def reviewer_read(event: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """The read-log record for a ``Read`` by a Component Reviewer or a
    Contract Reviewer (ADR 0085), or ``None``.

    The path is resolved and the file hashed when the hook runs, just before
    the runtime reads it, so the record names the exact bytes the reviewer saw.
    """

    if event.get("tool_name") != "Read" or event.get("agent_type") not in _LOGGED_READERS:
        return None
    agent_id = event.get("agent_id")
    tool_input = event.get("tool_input")
    if not isinstance(agent_id, str) or not agent_id or not isinstance(tool_input, Mapping):
        return None
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not path:
        return None
    cwd = event.get("cwd")
    if not os.path.isabs(path) and isinstance(cwd, str):
        path = os.path.join(cwd, path)
    resolved = os.path.realpath(path)
    digest = None
    try:
        if os.path.isfile(resolved) and os.path.getsize(resolved) <= MAX_HASHED_READ_BYTES:
            with open(resolved, "rb") as handle:
                digest = hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        digest = None
    return {
        "agent_id": agent_id,
        "agent_type": event.get("agent_type"),
        "path": resolved,
        "sha256": digest,
        "session_id": event.get("session_id"),
        "tool_use_id": event.get("tool_use_id"),
    }


def subagent_record(event: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """The subagent-log record for a ``SubagentStart`` event, or ``None``."""

    if event.get("hook_event_name") != "SubagentStart":
        return None
    agent_id = event.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id:
        return None
    return {
        "agent_id": agent_id,
        "agent_type": event.get("agent_type"),
        "session_id": event.get("session_id"),
    }


def _text(value: Any, maximum: int) -> bool:
    return isinstance(value, str) and 1 <= len(value.strip()) <= maximum


def blocked_reports(content: str) -> dict[int, dict[str, Any]]:
    """Every Blocked Report in one ledger, by number (issue #88).

    The ledger is ``measure/blocked-reports.jsonl`` in the CAD project, one
    event per line: a worker's ``report``, then the Manager's ``decision``
    (``waits_on`` a Component, or not), ``need`` or ``amendment`` (an
    applied Contract Amendment, ADR 0085). A report's ``status`` is ``open``
    until answered, ``waiting`` after a decision that waits on a Component,
    ``decided`` after any other decision, ``need`` after a need and
    ``amended`` after an amendment; ``open`` and ``waiting`` both hold the gates. Raises ``ValueError``
    for a ledger that is not a sequence of such events. Kept in step with
    ``blocked_reports`` in make_round and stage_proposal.py, which are
    standalone and cannot import it.
    """

    reports: dict[int, dict[str, Any]] = {}
    for line in content.splitlines():
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError("a Blocked Report event is not an object")
        kind, number = event.get("event"), event.get("report")
        if type(number) is not int or not _text(event.get("at"), 64):
            raise ValueError("a Blocked Report event has no number or time")
        wish = event.get("wish_sha256")
        if wish is not None and not (isinstance(wish, str) and re.fullmatch(r"[0-9a-f]{64}", wish)):
            raise ValueError("a Blocked Report event has an invalid Wish binding")
        if kind == "report":
            rows, round_value = event.get("rows"), event.get("round")
            if (
                number != len(reports) + 1
                or not _text(event.get("component"), 200)
                or not (round_value is None or (type(round_value) is int and round_value >= 1))
                or not isinstance(rows, list) or not 1 <= len(rows) <= 8
                or not all(_text(row, 4000) for row in rows)
                or not _text(event.get("reason"), 4000)
            ):
                raise ValueError("Blocked Report %s is invalid" % number)
            reports[number] = {
                "report": number, "component": event["component"], "round": round_value,
                "rows": list(rows), "reason": event["reason"], "opened_at": event["at"],
                "wish_sha256": wish, "status": "open", "answers": [],
            }
            continue
        report = reports.get(number)
        if report is None or report["status"] not in OPEN_BLOCKED:
            raise ValueError("Blocked Report %s is not open to answer" % number)
        if wish != report["wish_sha256"]:
            raise ValueError("Blocked Report %s is answered from another run" % number)
        if kind == "decision":
            waits_on, waits_round = event.get("waits_on"), event.get("waits_on_round")
            if not _text(event.get("ruling"), 4000) or not (
                (waits_on is None and waits_round is None)
                or (_text(waits_on, 200) and waits_on != report["component"]
                    and type(waits_round) is int and waits_round >= 0)
            ):
                raise ValueError("the decision on Blocked Report %s is invalid" % number)
            answer = {"kind": "decision", "ruling": event["ruling"], "waits_on": waits_on,
                      "waits_on_round": waits_round, "at": event["at"]}
            report["status"] = "waiting" if waits_on is not None else "decided"
        elif kind == "need":
            if not _text(event.get("need"), 1024):
                raise ValueError("the need on Blocked Report %s is invalid" % number)
            answer = {"kind": "need", "need": event["need"], "at": event["at"]}
            report["status"] = "need"
        elif kind == "amendment":
            # ADR 0085: an applied Contract Amendment removed the contradiction.
            amendment, amended = event.get("amendment"), event.get("amended_sha256")
            if type(amendment) is not int or amendment < 1 or not (
                isinstance(amended, str) and re.fullmatch(r"[0-9a-f]{64}", amended)
            ):
                raise ValueError("the amendment answering Blocked Report %s is invalid" % number)
            answer = {"kind": "amendment", "amendment": amendment, "amended_sha256": amended,
                      "at": event["at"]}
            report["status"] = "amended"
        else:
            raise ValueError("unknown Blocked Report event %r" % kind)
        report["answers"].append(answer)
    return reports


def _current_ledgers(run_root: Path) -> list[Path]:
    """The Blocked Report ledgers of the run's current Make attempt."""

    try:
        stage = json.loads((run_root / "STAGE.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(stage, dict) or stage.get("stage") != "make" or type(stage.get("round")) is not int:
        return []
    product = run_root / "artifacts" / "make" / ("r%04d" % stage["round"]) / "product"
    if not product.is_dir():
        return []
    return sorted(
        path for path in product.rglob(BLOCKED_REPORTS_NAME)
        if path.parent.name == "measure" and path.is_file() and not path.is_symlink()
    )


def _ends_on_need(run_root: Path) -> bool:
    try:
        proposal = json.loads((run_root / "agent-outcome.json").read_text(encoding="utf-8"))
        outcome = proposal["outcome"]
        return outcome["status"] in ("waiting", "failed") and bool(outcome["needs"])
    except (OSError, ValueError, KeyError, TypeError):
        return False


def turn_end(event: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """The ``Stop`` hook output refusing the root's turn end, or ``None``.

    The root may not end its turn while the current Make attempt holds an
    open Blocked Report, unless the turn ends on a recorded need (issue #88).
    A subagent's stop, or an unreadable ledger, is never refused here: the
    host's Make gates still refuse it.
    """

    if event.get("hook_event_name") != "Stop" or event.get("agent_type") or event.get("agent_id"):
        return None
    cwd = event.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        return None
    run_root = Path(cwd)
    held = []
    for ledger in _current_ledgers(run_root):
        try:
            if ledger.stat().st_size > MAX_BLOCKED_LEDGER_BYTES:
                continue
            reports = blocked_reports(ledger.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            continue
        held.extend(
            "%d (%s, %s)" % (number, report["component"], report["status"])
            for number, report in sorted(reports.items())
            if report["status"] in OPEN_BLOCKED
        )
    if not held or _ends_on_need(run_root):
        return None
    return {
        "decision": "block",
        "reason": (
            "Workshop (issue #88): Blocked Report %s is still open. Do not end your "
            "turn. Answer each with make_round --clear-blocked: a decision the "
            "worker can follow, a decision waiting on a Component (then wait for "
            "that Component and wake the worker again), or a need quoting its "
            "rows, then seal that need with stage_proposal.py need. Run make_round "
            "<cad-project> --blocked-reports to see them."
        ) % ", ".join(held),
    }


def _append(table: Path, record: Mapping[str, Any]) -> None:
    line = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    descriptor = os.open(str(table), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(descriptor, line)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


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
        _append(table, record)
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
    directory = Path(__file__).resolve().parent
    stop = turn_end(event)
    if stop is not None:
        print(json.dumps(stop))
        return 0
    # Evidence only: a spawn or a read is never refused, and a record that
    # cannot be written is missing at the host's check instead.
    evidence = subagent_record(event)
    log = SUBAGENT_LOG_NAME
    if evidence is None:
        evidence, log = reviewer_read(event), READ_LOG_NAME
    if evidence is not None:
        try:
            _append(directory / log, evidence)
        except OSError:
            pass
        return 0
    table = directory / NONCE_TABLE_NAME
    try:
        output = decide(event, issue=_table_issuer(table))
    except OSError:
        output = _deny("the worker nonce could not be recorded")
    if output is not None:
        print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
