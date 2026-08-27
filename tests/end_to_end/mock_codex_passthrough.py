#!/usr/bin/env python3
"""Test-only pass-through that adds one generic mock-session directive.

The Workshop launcher still owns every Codex argument and consumes the real
JSONL event stream.  This executable only snapshots the current stage packet,
adds a stage-agnostic instruction to stdin, observes prohibited activity, and
delegates to the installed ``codex`` executable.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


DIRECTIVE_VERSION = 3
DIRECTIVE = """

<workshop_mock_session_acceptance version="3">
This is an opt-in context-and-integration acceptance run. Follow the normal
materialized product-run instructions and the current read-only STAGE.json;
they remain the only source of stage-specific schemas, commands, ownership
rules, and lifecycle behavior. Do the minimum valid, clearly mock-labelled
work for this stage. Do not browse the web, contact remote services, perform
broad exploration, or create unnecessary child agents.

"Mock" reduces scope and quality depth only. It does not permit placeholder
artifact bytes, skipped required tools or checks, deferred required validation,
or a merely structural finalizer success. Every unchanged production gate must
genuinely accept the output. Deferred work may name only optional or expensive
work beyond the minimum required for those gates.

Finish every source file first. Once those exact bytes will no longer change,
write one JSON context record at the exact path shown below immediately before
normal stage finalization. It must contain exactly: schema_version=1,
kind="autonomous-workshop.mock-session-context", stage, checkpoint_sha256,
subject_sha256, instructions (a non-empty array of {path,sha256} for production
instruction files actually consulted), used_inputs (a non-empty array of
top-level keys actually used from STAGE.json.inputs), strategy (a short
identifier), outputs (a non-empty array of {path,sha256} for agent-authored
source files supplied to the normal finalizer), and deferred_work (a non-empty
array of expensive activities intentionally omitted). Paths are relative to
the run root. Exclude this context record, STAGE.json, generated contracts,
agent-outcome.json, and host-owned files from outputs.

Do not modify a listed output after hashing it. If finalization reports a source
problem, repair the source and refresh its recorded hash before retrying. After
finalization succeeds, recheck every listed output against the record and fix
the record before returning if any byte changed.

Context record path: {context_record_path}

Use the normal production instructions to finalize exactly this stage, then
return control immediately.
</workshop_mock_session_acceptance>
""".strip()

_TRACE_KIND = "autonomous-workshop.mock-session-turn"
_PROHIBITED_ITEM_TYPES = frozenset(
    ("web_search", "subagent", "agent_call", "collab_agent", "collaboration_tool_call")
)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _append_json_line(path: Path, value: object) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(descriptor, _canonical_json(value) + b"\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _stage_snapshot(run_root: Path) -> tuple[dict[str, object], str, str]:
    source = run_root / "STAGE.json"
    content = source.read_bytes()
    packet = json.loads(content.decode("utf-8"))
    if not isinstance(packet, dict):
        raise RuntimeError("STAGE.json is not an object")
    stage = packet.get("stage")
    checkpoint = packet.get("checkpoint_sha256")
    if not isinstance(stage, str) or not isinstance(checkpoint, str):
        raise RuntimeError("STAGE.json lacks its stage binding")
    snapshots = run_root / ".mock-session" / "packets"
    snapshots.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = snapshots / (checkpoint + ".json")
    try:
        descriptor = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if target.read_bytes() != content:
            raise RuntimeError("mock-session stage snapshot changed for one checkpoint")
    else:
        try:
            os.write(descriptor, content)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    record = ".mock-session/context/%s.json" % checkpoint
    return packet, stage, record


def _real_codex() -> str:
    selected = shutil.which("codex")
    if not selected:
        raise RuntimeError("the real Codex CLI is not installed or on PATH")
    if Path(selected).resolve() == Path(__file__).resolve():
        raise RuntimeError("the mock-session pass-through resolved itself as Codex")
    return selected


def _forward_signal(child: subprocess.Popen[str], signum: int, unused_frame: object) -> None:
    del unused_frame
    if child.poll() is None:
        child.send_signal(signum)


def _observed_item_type(line: str) -> str | None:
    try:
        event = json.loads(line)
    except ValueError:
        return None
    if not isinstance(event, dict):
        return None
    item = event.get("item")
    if not isinstance(item, dict):
        return None
    value = item.get("type")
    return value if isinstance(value, str) else None


def _event_type(line: str) -> str | None:
    try:
        event = json.loads(line)
    except ValueError:
        return None
    if not isinstance(event, dict):
        return None
    value = event.get("type")
    return value if isinstance(value, str) else None


def _workspace_inventory(run_root: Path) -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    for path in run_root.rglob("*"):
        try:
            relative = path.relative_to(run_root).as_posix()
            identity = path.lstat()
        except OSError:
            continue
        if relative == ".mock-session" or relative.startswith(".mock-session/"):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        result[relative] = (identity.st_size, identity.st_mtime_ns)
    return result


def _proposal_artifacts(run_root: Path) -> list[str]:
    path = run_root / "agent-outcome.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        artifacts = value["outcome"]["artifacts"]
    except (OSError, KeyError, TypeError, ValueError):
        return []
    if not isinstance(artifacts, list):
        return []
    return sorted(
        item["path"]
        for item in artifacts
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    )


def _context_output_hashes(run_root: Path, relative_record: str) -> dict[str, str]:
    try:
        value = json.loads((run_root / relative_record).read_text(encoding="utf-8"))
        outputs = value["outputs"]
    except (OSError, KeyError, TypeError, ValueError):
        return {}
    result: dict[str, str] = {}
    if not isinstance(outputs, list):
        return result
    for item in outputs:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            return {}
        relative = item["path"]
        pure = Path(relative)
        if pure.is_absolute() or ".." in pure.parts:
            return {}
        path = run_root / pure
        try:
            content = path.read_bytes()
        except OSError:
            return {}
        result[relative] = hashlib.sha256(content).hexdigest()
    return result


def _context_proof_error(
    run_root: Path,
    relative_record: str,
    packet: dict[str, object],
    output_hashes: dict[str, str],
) -> str | None:
    try:
        value = json.loads((run_root / relative_record).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "context record is missing or malformed"
    if not isinstance(value, dict):
        return "context record is not an object"
    for key in ("stage", "checkpoint_sha256", "subject_sha256"):
        if value.get(key) != packet.get(key):
            return "context record has a stale %s binding" % key
    for key in ("instructions", "used_inputs", "outputs", "deferred_work"):
        if not isinstance(value.get(key), list) or not value[key]:
            return "context record has no %s evidence" % key
    if not output_hashes:
        return "context record output hashes are missing or invalid"
    return None


def main() -> int:
    real = _real_codex()
    arguments = sys.argv[1:]
    if arguments == ["--version"]:
        return subprocess.run([real, *arguments], check=False).returncode

    run_root = Path.cwd().resolve()
    packet, stage, context_record = _stage_snapshot(run_root)
    prompt = sys.stdin.read()
    directive = DIRECTIVE.replace("{context_record_path}", context_record)
    before = _workspace_inventory(run_root)
    started = time.monotonic()
    trace_path = run_root / ".mock-session" / "turns.jsonl"
    model = arguments[arguments.index("--model") + 1] if "--model" in arguments else None
    effort = next(
        (
            value.split("=", 1)[1].strip('"')
            for value in arguments
            if value.startswith("model_reasoning_effort=")
        ),
        None,
    )
    prohibited: list[str] = []
    terminal_line: str | None = None
    child = subprocess.Popen(
        [real, *arguments],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        bufsize=1,
    )
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda number, frame, process=child: _forward_signal(process, number, frame))
    assert child.stdin is not None and child.stdout is not None
    child.stdin.write(prompt + "\n\n" + directive + "\n")
    child.stdin.close()
    for line in child.stdout:
        item_type = _observed_item_type(line)
        if item_type in _PROHIBITED_ITEM_TYPES:
            prohibited.append(item_type)
        if _event_type(line) == "turn.completed":
            terminal_line = line
            continue
        sys.stdout.write(line)
        sys.stdout.flush()
    returncode = child.wait()
    after = _workspace_inventory(run_root)
    agent_writes = sorted(
        path for path, identity in after.items() if before.get(path) != identity
    )
    elapsed = round(time.monotonic() - started, 6)
    context_hashes = _context_output_hashes(run_root, context_record)
    proof_error = _context_proof_error(
        run_root,
        context_record,
        packet,
        context_hashes,
    )
    if returncode == 0 and terminal_line is not None and proof_error is not None:
        returncode = 126
    _append_json_line(
        trace_path,
        {
            "schema_version": 1,
            "kind": _TRACE_KIND,
            "stage": stage,
            "checkpoint_sha256": packet["checkpoint_sha256"],
            "subject_sha256": packet["subject_sha256"],
            "packet_sha256": hashlib.sha256(
                (run_root / "STAGE.json").read_bytes()
            ).hexdigest(),
            "context_record_path": context_record,
            "model": model,
            "reasoning_effort": effort,
            "elapsed_seconds": elapsed,
            "prohibited_items": sorted(set(prohibited)),
            "agent_writes": agent_writes,
            "proposal_artifacts": _proposal_artifacts(run_root),
            "context_output_hashes": context_hashes,
            "context_proof_error": proof_error,
            "returncode": returncode,
        },
    )
    if proof_error is not None and returncode == 126:
        print("mock-session context proof failed: %s" % proof_error, file=sys.stderr)
        return returncode
    if terminal_line is not None:
        sys.stdout.write(terminal_line)
        sys.stdout.flush()
    return returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("mock-session Codex pass-through failed: %s" % exc, file=sys.stderr)
        raise SystemExit(125)
