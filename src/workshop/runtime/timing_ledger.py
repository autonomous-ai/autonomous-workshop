"""The Workshop timing ledger: one JSONL row per long-running step (ADR 0106).

Every long-running Workshop step (a seal layer, a make_round mode, a
verify_project command, a kit tool, a ``workshop wish``/``fix`` stage
operation, a publish) appends rows to one shared ledger under the Workshop
home, never inside the repository::

    $WORKSHOP_HOME/timing/ledger.jsonl        (WORKSHOP_TIMING_LEDGER overrides)

A step writes a ``start`` row when it begins and an ``end`` row, the step's
one complete record, when it ends. A ``start`` row with no ``end`` row is a
step that was killed before it could write one (SIGKILL, a closed terminal).

The ledger only records. No gate, verdict, threshold, reuse key or lifecycle
decision reads it, and a step never fails because the ledger cannot be
written: every write is best effort. ``tools/process_review.py`` reads it and
writes the slow-step report; proposing and making fixes is agent work.

This module is stdlib-only, so run-local tools (make_round, the kit tools)
import it when a Workshop install is on the path and silently skip it when
none is.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Optional, Sequence

SCHEMA_VERSION = 1
KIND = "workshop-timing"
LEDGER_ENV = "WORKSHOP_TIMING_LEDGER"
PARENT_ENV = "WORKSHOP_TIMING_PARENT"
DISABLE_VALUES = ("", "0", "off", "none")

# Outcomes of a finished step.
PASS = "pass"
FAIL = "fail"
UNVERIFIED = "unverified"
KILLED = "killed"
OUTCOMES = (PASS, FAIL, UNVERIFIED, KILLED)

# Why a step that did not pass did not pass.
PRODUCT_DEFECT = "product-defect"
TOOL_ERROR = "tool-error"
STALE_INPUT = "stale-input"
# A seeded run's input is not what the Approved Proof sealed: a root round
# that cannot be the approved Component, or a seal the Wish would refuse.
SEED_MISMATCH = "seed-mismatch"
FAILURE_CLASSES = (PRODUCT_DEFECT, TOOL_ERROR, STALE_INPUT, SEED_MISMATCH, KILLED)

# Exit codes a shell gives a process a signal ended: SIGINT, SIGKILL, SIGTERM.
_SIGNAL_EXITS = (130, 137, 143)
_TRACEBACK = "Traceback (most recent call last)"
# Text a tool prints when its input, not the product, is out of date. Order
# matters only for readability; any match classes the failure stale.
STALE_PATTERNS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"\bstale\b",
    r"changed since it (?:froze|was (?:sealed|frozen|recorded))",
    r"\brerun make_round\b",
    r"no print-gate summary",
    r"\bout of date\b",
    r"names a CAD entry that does not exist",
    r"foreign or stale",
))
# Text make_round and seal_proof print when a seeded run and its Approved
# Proof disagree on identity: a stale sealed carry key, image bytes the Wish
# refuses. It beats stale: the fix is a re-seal, not a refreshed input.
SEED_MISMATCH_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r"is not the Approved Proof's Component \(its B-rep or carry key differs\)",
    r"workshop wish --seed-source would refuse",
))
TOOL_ERROR_PATTERNS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    re.escape(_TRACEBACK),
    r"could not start",
    r"uncaught exception",
    r"\btimed out\b",
    r"time allowance exhausted",
    r"\busage: ",
    r": error: ",
))
REASON_CHARS = 400
ARGV_ITEMS = 24
ARGV_ITEM_CHARS = 200
# A child timing line a tool prints: ``[verify_project] kit_tree.py: rc=1 in 536.23s``.
CHILD_LINE = re.compile(
    r"^\[(?P<tool>[A-Za-z0-9_.-]+)\] (?:done )?\"?(?P<name>[^\"\n]{1,120}?)\"?: rc=(?P<rc>-?\d+) in (?P<wall>\d+(?:\.\d+)?)s\s*$",
    re.MULTILINE)
# Directories a source fingerprint never reads: outputs, not inputs.
_FINGERPRINT_SKIP = frozenset(("measure", "renders", "__pycache__", ".git", "out", "__cadgen__", "rounds"))
_FINGERPRINT_SUFFIXES = (".py", ".md", ".json", ".yaml", ".yml", ".toml")
_FINGERPRINT_MAX_FILES = 4000


def utc_iso(epoch: float) -> str:
    return (datetime.fromtimestamp(epoch, tz=timezone.utc)
            .isoformat(timespec="milliseconds").replace("+00:00", "Z"))


def parse_iso(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def default_ledger_path(environment: Optional[Mapping[str, str]] = None) -> Optional[Path]:
    """The ledger file, or None when the ledger is turned off."""

    values = os.environ if environment is None else environment
    configured = values.get(LEDGER_ENV)
    if configured is not None:
        if configured.strip().lower() in DISABLE_VALUES:
            return None
        return Path(configured).expanduser()
    try:
        from workshop.runtime.package_data import default_workshop_home
        home = Path(default_workshop_home(values))
    except Exception:  # noqa: BLE001 - a missing install or a bad WORKSHOP_HOME
        home_env = values.get("HOME")
        if not home_env:
            return None
        home = Path(home_env) / ".local" / "share" / "autonomous-workshop"
    return home / "timing" / "ledger.jsonl"


def append_row(row: Mapping[str, Any], path: Optional[Path] = None) -> bool:
    """Append one row; never raises. Returns whether the row was written."""

    try:
        target = path if path is not None else default_ledger_path()
        if target is None:
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(dict(row), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
        # One O_APPEND write per row: concurrent writers never interleave
        # inside a line on a local filesystem.
        descriptor = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(descriptor, line.encode("utf-8"))
        finally:
            os.close(descriptor)
        return True
    except Exception:  # noqa: BLE001 - the ledger never fails a step
        return False


def read_rows(path: Optional[Path] = None) -> list:
    """Every well-formed row in the ledger, in file order."""

    target = path if path is not None else default_ledger_path()
    if target is None or not target.is_file():
        return []
    rows = []
    with target.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict) and value.get("kind") == KIND:
                rows.append(value)
    return rows


def classify(exit_code: Optional[int], *, output: str = "", timed_out: bool = False, killed: bool = False,
             unverified: bool = False, reason: Optional[str] = None) -> tuple:
    """``(outcome, failure_class)`` for one finished step.

    Deterministic, by exit status and the step's own words. Killed beats
    unverified, which beats a seed mismatch, which beats a stale input,
    which beats a tool error; a plain
    exit 1 with none of those marks is a product defect: the gate said the
    product fails. An agent that later finds otherwise records an annotation
    (``tools/process_review.py annotate``); the row itself never changes.
    """

    text = "%s\n%s" % (reason or "", output or "")
    if killed or timed_out or (exit_code is not None and (exit_code < 0 or exit_code in _SIGNAL_EXITS)):
        return KILLED, KILLED
    if unverified:
        return UNVERIFIED, TOOL_ERROR
    if exit_code == 0:
        return PASS, None
    if any(pattern.search(text) for pattern in SEED_MISMATCH_PATTERNS):
        return FAIL, SEED_MISMATCH
    if any(pattern.search(text) for pattern in STALE_PATTERNS):
        return FAIL, STALE_INPUT
    if exit_code is None or exit_code >= 2 or any(pattern.search(text) for pattern in TOOL_ERROR_PATTERNS):
        return FAIL, TOOL_ERROR
    return FAIL, PRODUCT_DEFECT


def toy_of(project: Optional[str]) -> Optional[str]:
    """The toy a project path belongs to: ``mini-city-organizer/amsterdam-kit``
    for ``toys-spec/mini-city-organizer/amsterdam-kit/proof``, the Wish id for
    a run, else the directory's name."""

    if not project:
        return None
    parts = Path(project).parts
    for anchor in ("toys-spec", "toys"):
        if anchor in parts:
            rest = parts[parts.index(anchor) + 1:]
            kept = []
            for part in rest:
                if part in ("proof", "cad", "work", "contract", "measure", "manual", "dev") or part.startswith("dev-"):
                    break
                if part.endswith((".log", ".json", ".py", ".md", ".pdf", ".step")):
                    break
                kept.append(part)
            if kept:
                return "/".join(kept)
    for part in parts:
        if re.fullmatch(r"wish-\d{8}-\d{6}-[0-9a-f]{8}", part):
            return part
    return Path(project).name or None


def inputs_fingerprint(project: Optional[Path], argv: Sequence[str] = (), extra: Iterable[Path] = ()) -> Optional[str]:
    """A hash of the step's argv and the source files its project holds
    (code, specs, contracts; never ``measure/`` or renders). Equal
    fingerprints mean a rerun saw the same inputs. Best effort: None when
    the project cannot be read or is too large to hash quickly."""

    try:
        digest = hashlib.sha256()
        digest.update(json.dumps([str(item) for item in argv]).encode("utf-8"))
        files = []
        if project is not None and Path(project).is_dir():
            root = Path(project)
            for directory, names, filenames in os.walk(root):
                names[:] = sorted(name for name in names if name not in _FINGERPRINT_SKIP
                                  and not name.startswith("."))
                for filename in filenames:
                    if filename.endswith(_FINGERPRINT_SUFFIXES):
                        files.append(Path(directory) / filename)
                if len(files) > _FINGERPRINT_MAX_FILES:
                    return None
            files.sort()
            for path in files:
                digest.update(str(path.relative_to(root)).encode("utf-8") + b"\0")
                digest.update(hashlib.sha256(path.read_bytes()).digest())
        for path in sorted(Path(item) for item in extra):
            if path.is_file():
                digest.update(str(path).encode("utf-8") + b"\0" + hashlib.sha256(path.read_bytes()).digest())
        return digest.hexdigest()
    except Exception:  # noqa: BLE001
        return None


def child_timings(output: str) -> list:
    """The ``[tool] name: rc=N in Ts`` lines a step printed, in order."""

    return [{"tool": match.group("tool"), "name": match.group("name").strip(), "exit_code": int(match.group("rc")),
             "wall_s": float(match.group("wall"))}
            for match in CHILD_LINE.finditer(output or "")]


def _short_argv(argv: Sequence[str]) -> list:
    return [str(item)[:ARGV_ITEM_CHARS] for item in list(argv)[:ARGV_ITEMS]]


def _short(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = " ".join(str(text).split())
    return text[-REASON_CHARS:]


def base_row(event: str, *, row_id: str, step: str, tool: str, project: Optional[str], parent: Optional[str],
             source: str = "live") -> dict:
    return {
        "schema_version": SCHEMA_VERSION, "kind": KIND, "event": event, "id": row_id, "parent": parent,
        "step": step, "tool": tool, "project": project, "toy": toy_of(project), "source": source,
        "host": socket.gethostname(), "pid": os.getpid(),
    }


def end_row(*, row_id: str, step: str, tool: str, project: Optional[str], parent: Optional[str], started: float,
            ended: float, exit_code: Optional[int], outcome: str, failure_class: Optional[str],
            reason: Optional[str] = None, cache_hit: bool = False, inputs_key: Optional[str] = None,
            argv: Sequence[str] = (), source: str = "live", evidence: Optional[str] = None,
            extra: Optional[Mapping[str, Any]] = None) -> dict:
    """The one complete record of a finished step."""

    if outcome not in OUTCOMES:
        raise ValueError("unknown outcome %r" % outcome)
    if failure_class is not None and failure_class not in FAILURE_CLASSES:
        raise ValueError("unknown failure class %r" % failure_class)
    row = base_row("end", row_id=row_id, step=step, tool=tool, project=project, parent=parent, source=source)
    row.update({
        "started_at": utc_iso(started), "ended_at": utc_iso(ended), "wall_s": round(max(0.0, ended - started), 3),
        "exit_code": exit_code, "outcome": outcome, "failure_class": failure_class, "reason": _short(reason),
        "cache_hit": bool(cache_hit), "inputs_key": inputs_key, "argv": _short_argv(argv), "evidence": evidence,
    })
    if extra:
        row.update(dict(extra))
    return row


class Span:
    """What a running step tells its ledger row before it ends."""

    def __init__(self, row_id: str) -> None:
        self.id = row_id
        self.exit_code: Optional[int] = None
        self.reason: Optional[str] = None
        self.output: str = ""
        self.unverified = False
        self.cache_hit = False
        self.evidence: Optional[str] = None
        self.inputs_key: Optional[str] = None


@contextmanager
def timed(step: str, *, tool: str, project: Optional[Path] = None, argv: Sequence[str] = (),
          fingerprint: bool = False, ledger: Optional[Path] = None) -> Iterator[Span]:
    """Record one step: a ``start`` row now, an ``end`` row when it ends.

    The caller sets ``span.exit_code`` (and, when it knows them,
    ``span.reason``, ``span.output``, ``span.unverified``, ``span.cache_hit``).
    An exception counts as exit 1 with its message, a KeyboardInterrupt or
    SystemExit by a signal code as killed. Children started inside the block
    inherit ``WORKSHOP_TIMING_PARENT``, so their rows name this one.
    Nothing here changes what the step does or returns.
    """

    target = ledger if ledger is not None else default_ledger_path()
    if target is None:
        yield Span("")
        return
    row_id = uuid.uuid4().hex
    parent = os.environ.get(PARENT_ENV) or None
    project_text = str(Path(project).resolve()) if project is not None else None
    span = Span(row_id)
    if fingerprint:
        span.inputs_key = inputs_fingerprint(Path(project) if project is not None else None, argv)
    started = time.time()
    start = base_row("start", row_id=row_id, step=step, tool=tool, project=project_text, parent=parent)
    start.update({"started_at": utc_iso(started), "argv": _short_argv(argv)})
    append_row(start, target)
    saved = os.environ.get(PARENT_ENV)
    os.environ[PARENT_ENV] = row_id
    killed = False
    try:
        yield span
    except KeyboardInterrupt:
        killed = True
        raise
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        if span.exit_code is None:
            span.exit_code = code
        raise
    except BaseException as exc:
        if span.exit_code is None:
            span.exit_code = 1
        span.reason = span.reason or "%s: %s" % (type(exc).__name__, exc)
        if not span.output:
            span.output = _TRACEBACK
        raise
    finally:
        if saved is None:
            os.environ.pop(PARENT_ENV, None)
        else:
            os.environ[PARENT_ENV] = saved
        ended = time.time()
        outcome, failure_class = classify(span.exit_code, output=span.output, killed=killed,
                                          unverified=span.unverified, reason=span.reason)
        append_row(end_row(row_id=row_id, step=step, tool=tool, project=project_text, parent=parent,
                           started=started, ended=ended, exit_code=span.exit_code, outcome=outcome,
                           failure_class=failure_class, reason=span.reason if outcome != PASS else None,
                           cache_hit=span.cache_hit, inputs_key=span.inputs_key, argv=argv, evidence=span.evidence),
                   target)


def is_aggregate(name: str) -> bool:
    """A timing line that sums the lines before it (``image-derived final
    workflow``), not a step of its own."""

    return str(name).endswith("workflow")


def place_back_to_back(children: Sequence[Mapping[str, Any]], ended: float) -> list:
    """``(start, end, child)`` for timed children printed in order, the last
    ending at ``ended`` and each earlier one ending where the next began. An
    aggregate line spans the lines before it and moves no cursor."""

    cursor = ended
    placed = []
    for child in reversed(list(children)):
        start = cursor - float(child["wall_s"])
        placed.append((start, cursor, child))
        if not is_aggregate(child["name"]):
            cursor = start
    placed.reverse()
    return placed


def record_children(parent_id: str, *, project: Optional[str], ended: float, output: str,
                    ledger: Optional[Path] = None) -> int:
    """Rows for the ``[tool] name: rc=N in Ts`` lines a step printed (the
    commands verify_project runs, inspect's builds), placed back to back
    ending when the parent ended. Their own clocks are exact; their start
    times are the parent's order, an estimate the row marks."""

    children = child_timings(output)
    if not children or not parent_id:
        return 0
    target = ledger if ledger is not None else default_ledger_path()
    if target is None:
        return 0
    written = 0
    for start, end, child in place_back_to_back(children, ended):
        outcome, failure_class = classify(child["exit_code"])
        row = end_row(row_id=uuid.uuid4().hex, step="%s/%s" % (child["tool"], child["name"]), tool=child["tool"],
                      project=project, parent=parent_id, started=start, ended=end, exit_code=child["exit_code"],
                      outcome=outcome, failure_class=failure_class, extra={"times_estimated": True})
        written += append_row(row, target)
    return written


def run_main(tool: str, main, argv: Optional[Sequence[str]] = None, *, modes: Sequence[str] = (),
             default_mode: str = "run", fingerprint: bool = True) -> int:
    """Run a script's ``main(argv)`` under :func:`timed` as step
    ``<tool>/<mode>``, returning its exit code unchanged. The project is the
    first argument that names a directory."""

    args = list(sys.argv[1:] if argv is None else argv)
    project = next((Path(item) for item in args if not item.startswith("-") and Path(item).is_dir()), None)
    step = "%s/%s" % (tool, mode_of(args, modes, default_mode) if modes else default_mode)
    if modes == () and args and not args[0].startswith("-") and not Path(args[0]).exists():
        step = "%s/%s" % (tool, args[0])  # a subcommand: ``kit_sheets.py check``
    with timed(step, tool=tool, project=project, argv=args, fingerprint=fingerprint) as span:
        code = main(argv)
        span.exit_code = code if isinstance(code, int) else (0 if code is None else 1)
        return code


def script_main(tool: str, main, *, modes: Sequence[str] = (), default_mode: str = "run") -> int:
    """A run-local script's ``__main__``: timed when this module imports."""

    return run_main(tool, main, modes=modes, default_mode=default_mode)


def mode_of(argv: Sequence[str], modes: Sequence[str], default: str) -> str:
    """The first ``--flag`` of ``modes`` present in ``argv``, as its name."""

    present = {item.split("=", 1)[0] for item in argv}
    for flag in modes:
        if flag in present:
            return flag.lstrip("-")
    return default


_WORKSHOP_STATES = {"completed": (PASS, None), "failed": (FAIL, TOOL_ERROR), "pending": (UNVERIFIED, None)}


def record_workshop_event(*, product_id: str, stage: str, operation: str, state: str, observed_at: str,
                          elapsed_ms: Optional[int], ledger: Optional[Path] = None) -> bool:
    """One row for a terminal ``workshop wish``/``fix`` timing event (a stage
    operation: a native session turn, a gate, the Factory effect). A failed
    operation raised in the host, so it is the harness's; a pending one
    ended with its outcome unsettled, which is no failure."""

    if state not in _WORKSHOP_STATES or elapsed_ms is None:
        return False
    try:
        ended = parse_iso(observed_at)
    except ValueError:
        return False
    outcome, failure_class = _WORKSHOP_STATES[state]
    row = end_row(row_id=uuid.uuid4().hex, step="workshop/%s/%s" % (stage, operation), tool="workshop",
                  project=product_id, parent=None, started=ended - elapsed_ms / 1000.0, ended=ended,
                  exit_code=None, outcome=outcome, failure_class=failure_class,
                  reason=None if state == "completed" else state, extra={"stage": stage})
    return append_row(row, ledger)
