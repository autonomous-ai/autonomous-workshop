#!/usr/bin/env python3
"""Transparent real-Codex wrapper for opt-in context acceptance."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import subprocess
import sys
import time
from typing import Any, Mapping


DIRECTIVE_VERSION = 8
DIRECTIVE = r"""
<workshop_mock_session_acceptance version="8">
This is an opt-in context-and-integration acceptance run. Read and follow the
normal materialized product-run constitution, applicable declared skills and
references, the current read-only STAGE.json, and its accepted upstream inputs.
Those production bytes remain the only source of stage-specific schemas,
commands, transitions, routing, and ownership rules.

Do the smallest valid, clearly acceptance-labelled work that genuinely passes
the unchanged production checks. Keep stage authority and final synthesis in
the root session. Use a bounded native child agent only where the production
instructions require an Inventor or independent review; do not delegate the
whole stage or create child agents for optional exploration. Do not browse the
web, contact a live or non-loopback service, request credentials, or perform
broad exploration. "Minimal" may reduce optional depth; it may not use
placeholder bytes, skip a required tool or check, or fabricate evidence.
Keep agent artifacts free of credential-shaped field names or values. Express
physical-production limits as plain descriptive prose instead of access,
authorization, password, token, key, or bearer metadata.

Finish every agent-authored source file first. Immediately before normal
finalization, write one JSON context record to the exact path below. It must
contain exactly these fields:

- schema_version: 1
- kind: "autonomous-workshop.mock-session-context"
- stage, checkpoint_sha256, and subject_sha256 copied from STAGE.json
- stage_packet_sha256: SHA-256 of the exact current STAGE.json bytes
- instructions: a non-empty array of {"path","sha256"} for run-root production
  instruction files actually consulted, including AGENTS.md, the main Workshop
  skill, and at least one applicable reference
- used_inputs: a non-empty array of top-level STAGE.json.inputs keys actually used
- strategy: {"id","explanation"} with a short generic identifier and explanation
- outputs: a non-empty array of {"path","sha256"} for final agent-authored source
  files supplied to the production finalizer. Cite the source path passed to the
  finalizer, even when that finalizer preserves a copy under artifacts/
- deferred_work: a non-empty array naming only optional expensive work omitted

All paths are canonical and relative to the run root. Exclude this context
record, STAGE.json, generated contracts, agent-outcome.json, verifier output,
and host-owned files from outputs. No outputs path may contain an evidence,
configs, results, gates, or receipts directory; those are derived or finalizer
files even when this turn wrote them. Do not modify a listed output after
hashing it. If a source repair changes bytes, refresh the record before retrying.

Context record path: {context_record_path}

After the normal production finalizer succeeds, immediately complete the active
native Goal as the production instructions require, then return control. Do not
inspect files, call another tool, or add work after Goal completion; the
pass-through wrapper independently rechecks every listed final source hash.
</workshop_mock_session_acceptance>
""".strip()

TRACE_KIND = "autonomous-workshop.mock-session-turn"
_PROHIBITED_ITEM_TYPES = frozenset(
    {
        "web_search",
    }
)
_CREDENTIAL_NAMES = (
    "FACTORY_PASSWORD",
    "FACTORY_USERNAME",
    "CONCEPT_IMAGES_API_KEY",
    "OPENAI_API_KEY",
)
_URL = re.compile(r"https?://([^/\s'\"<>]+)", re.IGNORECASE)


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


def _stage_snapshot(run_root: Path) -> tuple[dict[str, object], bytes, str, str]:
    source = run_root / "STAGE.json"
    if source.is_symlink() or not source.is_file():
        raise RuntimeError("STAGE.json is not a regular file")
    content = source.read_bytes()
    packet = json.loads(content.decode("utf-8"))
    if not isinstance(packet, dict):
        raise RuntimeError("STAGE.json is not an object")
    stage = packet.get("stage")
    checkpoint = packet.get("checkpoint_sha256")
    subject = packet.get("subject_sha256")
    if not all(isinstance(item, str) and item for item in (stage, checkpoint, subject)):
        raise RuntimeError("STAGE.json lacks its stage bindings")
    snapshots = run_root / ".mock-session" / "packets"
    snapshots.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Host rejection feedback changes the subject and packet without advancing
    # the lifecycle checkpoint. Preserve each exact repair-turn packet instead
    # of colliding with the first attempt's checkpoint-only snapshot.
    target = snapshots / ("%s-%s.json" % (checkpoint, subject))
    try:
        descriptor = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if target.read_bytes() != content:
            raise RuntimeError(
                "mock-session stage snapshot changed for one checkpoint"
            )
    else:
        try:
            os.write(descriptor, content)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    record = ".mock-session/context/%s.json" % checkpoint
    return packet, content, str(stage), record


def _real_codex() -> str:
    selected = shutil.which("codex")
    if not selected:
        raise RuntimeError("the real Codex CLI is not installed or on PATH")
    if Path(selected).resolve() == Path(__file__).resolve():
        raise RuntimeError("the mock-session pass-through resolved itself as Codex")
    return selected


def _forward_signal(
    child: subprocess.Popen[str], signum: int, unused_frame: object
) -> None:
    del unused_frame
    if child.poll() is None:
        child.send_signal(signum)


def _event(line: str) -> Mapping[str, Any] | None:
    try:
        value = json.loads(line)
    except ValueError:
        return None
    return value if isinstance(value, Mapping) else None


def _item_text(item: Mapping[str, Any]) -> str:
    values: list[str] = []
    for key in ("command", "text", "name", "query", "url"):
        value = item.get(key)
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            values.extend(part for part in value if isinstance(part, str))
    return "\n".join(values)


def _prohibited_activity(event: Mapping[str, Any]) -> tuple[str, ...]:
    item = event.get("item")
    if not isinstance(item, Mapping):
        return ()
    item_type = item.get("type")
    violations: set[str] = set()
    if isinstance(item_type, str) and item_type in _PROHIBITED_ITEM_TYPES:
        violations.add(item_type)
    text = _item_text(item)
    if any(name in text for name in _CREDENTIAL_NAMES):
        violations.add("credential_solicitation")
    for match in _URL.finditer(text):
        authority = match.group(1).rsplit("@", 1)[-1]
        host = authority.split(":", 1)[0].strip("[]").casefold()
        if host not in {"127.0.0.1", "localhost", "::1"}:
            violations.add("non_loopback_network")
    return tuple(sorted(violations))


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
        if isinstance(item, Mapping) and isinstance(item.get("path"), str)
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
        if not isinstance(item, Mapping) or not isinstance(item.get("path"), str):
            return {}
        pure = Path(item["path"])
        if pure.is_absolute() or ".." in pure.parts:
            return {}
        path = run_root / pure
        try:
            content = path.read_bytes()
        except OSError:
            return {}
        result[item["path"]] = hashlib.sha256(content).hexdigest()
    return result


def _context_proof_error(
    run_root: Path,
    relative_record: str,
    packet: Mapping[str, object],
    packet_sha256: str,
    output_hashes: Mapping[str, str],
) -> str | None:
    try:
        value = json.loads((run_root / relative_record).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "context record is missing or malformed"
    if not isinstance(value, Mapping):
        return "context record is not an object"
    expected = {
        "stage": packet.get("stage"),
        "checkpoint_sha256": packet.get("checkpoint_sha256"),
        "subject_sha256": packet.get("subject_sha256"),
        "stage_packet_sha256": packet_sha256,
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            return "context record has a stale %s binding" % key
    for key in ("instructions", "used_inputs", "outputs", "deferred_work"):
        if not isinstance(value.get(key), list) or not value[key]:
            return "context record has no %s evidence" % key
    if not output_hashes:
        return "context record output hashes are missing or invalid"
    declared = {
        item.get("path"): item.get("sha256")
        for item in value.get("outputs", [])
        if isinstance(item, Mapping)
    }
    if declared != dict(output_hashes):
        return "context record differs from final source bytes"
    return None


def _make_proof_boundary(
    run_root: Path,
    packet: Mapping[str, object],
    prompt: str,
) -> bool:
    """Recognize the host's exact intermediate deep-Make marker.

    This is not finalization evidence.  It only lets the pass-through return
    the terminal event for a bounded proof turn, so the production host can
    consume its own marker and resume the same native Goal.  Every ordinary
    turn still requires the complete context record below.
    """

    if packet.get("stage") != "make":
        return False
    checkpoint = packet.get("checkpoint_sha256")
    if not isinstance(checkpoint, str) or not checkpoint:
        return False
    path = run_root / ".make-proof-ready.json"
    try:
        before = path.lstat()
    except OSError:
        return False
    if path.is_symlink() or not path.is_file():
        return False
    try:
        content = path.read_bytes()
        after = path.lstat()
    except OSError:
        return False
    if (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size) != (
        after.st_dev,
        after.st_ino,
        after.st_mtime_ns,
        after.st_size,
    ):
        return False
    expected = {
        "schema_version": 1,
        "kind": "autonomous-workshop.make-proof-ready",
        "checkpoint_sha256": checkpoint,
    }
    # A mutable marker appearance is not a host-accepted boundary. The host
    # requests the one proof handoff by supplying this exact canonical payload
    # in the proof-phase prompt; final Make prompts do not contain it.
    if _canonical_json(expected).decode("utf-8") not in prompt:
        return False
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return False
    return value == expected and content == _canonical_json(expected) + b"\n"


def _runtime_configuration(arguments: list[str]) -> tuple[str | None, str | None, str]:
    model = arguments[arguments.index("--model") + 1] if "--model" in arguments else None
    effort = next(
        (
            value.split("=", 1)[1].strip('"')
            for value in arguments
            if value.startswith("model_reasoning_effort=")
        ),
        None,
    )
    method = "resume" if "resume" in arguments else "start"
    return model, effort, method


def _turn_timeout(run_root: Path) -> int:
    # The host writes this before the run workspace exists.  It is intentionally
    # outside the agent-readable root and contains no secret.
    try:
        path = run_root.parents[2] / "mock-session-config.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        timeout = value["turn_timeout_seconds"]
    except (OSError, KeyError, IndexError, TypeError, ValueError):
        # IndexError: a run root only two levels deep (a bare /tmp/tmpXXXX on
        # Linux) has no third parent; the default applies there too.
        return 300
    if type(timeout) is not int or not 1 <= timeout <= 3600:
        raise RuntimeError("mock-session turn timeout is invalid")
    return timeout


def main() -> int:
    real = _real_codex()
    arguments = sys.argv[1:]
    if arguments == ["--version"]:
        return subprocess.run([real, *arguments], check=False).returncode

    run_root = Path.cwd().resolve()
    packet, packet_bytes, stage, context_record = _stage_snapshot(run_root)
    packet_sha256 = hashlib.sha256(packet_bytes).hexdigest()
    packet_path = ".mock-session/packets/%s-%s.json" % (
        packet["checkpoint_sha256"],
        packet["subject_sha256"],
    )
    prompt = sys.stdin.read()
    directive = DIRECTIVE.replace("{context_record_path}", context_record)
    before = _workspace_inventory(run_root)
    started = time.monotonic()
    trace_path = run_root / ".mock-session" / "turns.jsonl"
    model, reasoning_effort, method = _runtime_configuration(arguments)
    prohibited: set[str] = set()
    terminal_line: str | None = None
    terminal_forwarded = False
    make_proof_boundary = False
    thread_ids: set[str] = set()
    timed_out = False
    child = subprocess.Popen(
        [real, *arguments],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        bufsize=1,
    )
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(
            signum,
            lambda number, frame, process=child: _forward_signal(
                process, number, frame
            ),
        )
    assert child.stdin is not None and child.stdout is not None
    child.stdin.write(prompt + "\n\n" + directive + "\n")
    child.stdin.close()
    deadline = time.monotonic() + _turn_timeout(run_root)
    while True:
        if time.monotonic() >= deadline:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
            print("mock-session Codex turn exceeded its budget", file=sys.stderr)
            timed_out = True
            break
        readable, unused_write, unused_error = select.select(
            [child.stdout], [], [], min(0.1, max(0.0, deadline - time.monotonic()))
        )
        del unused_write, unused_error
        if not readable:
            if child.poll() is not None:
                break
            continue
        line = child.stdout.readline()
        if not line:
            if child.poll() is not None:
                break
            continue
        event = _event(line)
        if event is not None:
            prohibited.update(_prohibited_activity(event))
            if event.get("type") == "thread.started" and isinstance(
                event.get("thread_id"), str
            ):
                thread_ids.add(event["thread_id"])
            if event.get("type") == "turn.completed":
                terminal_line = line
                make_proof_boundary = _make_proof_boundary(
                    run_root, packet, prompt
                )
                if make_proof_boundary:
                    immediate_error = None
                else:
                    immediate_hashes = _context_output_hashes(run_root, context_record)
                    immediate_error = _context_proof_error(
                        run_root,
                        context_record,
                        packet,
                        packet_sha256,
                        immediate_hashes,
                    )
                if immediate_error is None and not prohibited:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    terminal_forwarded = True
                continue
        sys.stdout.write(line)
        sys.stdout.flush()
    returncode = 124 if timed_out else child.wait()
    child.stdout.close()
    after = _workspace_inventory(run_root)
    agent_writes = sorted(
        path for path, identity in after.items() if before.get(path) != identity
    )
    elapsed = round(time.monotonic() - started, 6)
    output_hashes = _context_output_hashes(run_root, context_record)
    make_proof_boundary = _make_proof_boundary(run_root, packet, prompt)
    proof_error = (
        None
        if make_proof_boundary
        else _context_proof_error(
            run_root,
            context_record,
            packet,
            packet_sha256,
            output_hashes,
        )
    )
    if returncode == 0 and terminal_line is not None and proof_error is not None:
        returncode = 126
    if prohibited and returncode == 0:
        returncode = 127
    _append_json_line(
        trace_path,
        {
            "schema_version": 1,
            "kind": TRACE_KIND,
            "stage": stage,
            "checkpoint_sha256": packet["checkpoint_sha256"],
            "subject_sha256": packet["subject_sha256"],
            "stage_packet_sha256": packet_sha256,
            "stage_packet_path": packet_path,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "context_record_path": context_record,
            "model": model,
            "reasoning_effort": reasoning_effort,
            "method": method,
            "thread_ids": sorted(thread_ids),
            "elapsed_seconds": elapsed,
            "terminal_observed": terminal_line is not None,
            "terminal_forwarded": terminal_forwarded,
            "timed_out": timed_out,
            "prohibited_items": sorted(prohibited),
            "agent_writes": agent_writes,
            "proposal_artifacts": _proposal_artifacts(run_root),
            "turn_output_hashes": output_hashes,
            "make_proof_boundary": make_proof_boundary,
            "context_proof_error": proof_error,
            "returncode": returncode,
        },
    )
    if proof_error is not None and returncode == 126:
        print("mock-session context proof failed: %s" % proof_error, file=sys.stderr)
        return returncode
    if prohibited and returncode == 127:
        print(
            "mock-session observed prohibited activity: %s"
            % ", ".join(sorted(prohibited)),
            file=sys.stderr,
        )
    return returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("mock-session Codex pass-through failed: %s" % exc, file=sys.stderr)
        raise SystemExit(125)
