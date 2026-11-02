"""Host side of Blocked Reports (issue #88).

A Component Worker that cannot proceed records a Blocked Report with the
run-local ``make_round --report-blocked``; the Workshop Manager answers it
with ``make_round --clear-blocked``. Both append to the CAD project's
``measure/blocked-reports.jsonl``, each event bound to the run by the sha256
of its ``WISH.json``. The tool works the same on every runtime; no hook is
required.

While a report is open (unanswered, or answered by a decision that waits on
another Component) the host refuses Make acceptance, as ``make_round``
refuses an assembly round and the stage finalizer refuses the Make proposal.
The run report lists every report with how it was cleared and how long it
stayed open. Nothing here judges a report or answers one.

make_round only appends to a ledger. The host logs each read of a ledger
that is this run's record, as the make_round guard does before every
make_round call and on the root's turn end, and refuses Make acceptance
when a ledger no longer begins with every logged read: it was deleted or
rewritten (issue #181).
"""

from __future__ import annotations

import hashlib
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from workshop.errors import ContractError, StateConflict
from workshop.make.make_round_guard import (
    BLOCKED_REPORTS_NAME,
    MAX_BLOCKED_LEDGER_BYTES,
    MAX_LEDGER_READ_LOG_BYTES,
    OPEN_BLOCKED,
    blocked_reports,
    ledger_reads,
    record_ledger_reads,
)

_MAKE_ATTEMPTS = ("artifacts", "make")


def _read_ledger(ledger: Path) -> dict[int, dict[str, Any]]:
    try:
        identity = ledger.lstat()
        if not stat.S_ISREG(identity.st_mode) or identity.st_size > MAX_BLOCKED_LEDGER_BYTES:
            raise ValueError("not a bounded regular file")
        return blocked_reports(ledger.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ContractError("the Blocked Report ledger is invalid: %s" % exc) from exc


def _parse_time(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def report_summary(report: Mapping[str, Any], *, now: Optional[datetime] = None) -> dict[str, Any]:
    """One report as the run report lists it: how it was cleared and how
    long it stayed open (until now, while it is still open)."""

    answers = list(report["answers"])
    open_ = report["status"] in OPEN_BLOCKED
    cleared_at = None if open_ else answers[-1]["at"]
    opened = _parse_time(report["opened_at"])
    until = (
        (now or datetime.now(timezone.utc)) if cleared_at is None else _parse_time(cleared_at)
    )
    seconds = (
        max(0, int((until - opened).total_seconds()))
        if opened is not None and until is not None else None
    )
    return {
        "report": report["report"],
        "component": report["component"],
        "round": report["round"],
        "rows": list(report["rows"]),
        "reason": report["reason"],
        "opened_at": report["opened_at"],
        "status": report["status"],
        "cleared_by": None if open_ else answers[-1]["kind"],
        "cleared_at": cleared_at,
        "open_seconds": seconds,
        "answers": answers,
    }


def _logged_reads(read_log: Path) -> list[dict[str, Any]]:
    if not read_log.exists() and not read_log.is_symlink():
        return []
    try:
        identity = read_log.lstat()
        if not stat.S_ISREG(identity.st_mode) or identity.st_size > MAX_LEDGER_READ_LOG_BYTES:
            raise ValueError("not a bounded regular file")
        return ledger_reads(read_log.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise StateConflict("the Blocked Report ledger read log is invalid") from exc


def verify_ledger_reads(product: Path, read_log: Path) -> None:
    """Refuse a ledger under ``product`` that no longer begins with the exact
    bytes of every read the host or the make_round guard logged of it."""

    root = Path(product).resolve()
    for read in _logged_reads(read_log):
        ledger = Path(read["ledger"])
        if root not in ledger.parents:
            continue
        try:
            identity = ledger.lstat()
            kept = (
                stat.S_ISREG(identity.st_mode)
                and identity.st_size >= read["bytes"]
                and hashlib.sha256(ledger.read_bytes()[:read["bytes"]]).hexdigest()
                == read["sha256"]
            )
        except OSError:
            kept = False
        if not kept:
            raise ContractError(
                "the Blocked Report ledger %s was deleted or rewritten after Workshop "
                "read it; make_round only appends to it and nothing else may edit it. "
                "Put back its exact bytes: every report and answer stays this run's "
                "record" % ledger.relative_to(root).as_posix()
            )


def verify_no_open_blocked_reports(
    project: Path,
    *,
    wish_sha256: str,
    product: Optional[Path] = None,
    read_log: Optional[Path] = None,
) -> list[dict[str, Any]]:
    """Refuse Make output while a Blocked Report is open; return every report.

    A project without a ledger has none. A report not bound to this run's
    Wish, or a ledger that is not a valid sequence of events, is refused.
    With a ``read_log`` (a guarded run), every ledger under ``product`` must
    still begin with each read logged of it, and this read is logged before
    an open report is refused, so the refusal cannot be undone by deleting
    the report (issue #181).
    """

    if read_log is not None:
        verify_ledger_reads(product if product is not None else project, read_log)
    ledger = Path(project) / "measure" / BLOCKED_REPORTS_NAME
    if not ledger.exists() and not ledger.is_symlink():
        return []
    reports = _read_ledger(ledger)
    held = []
    for number, report in sorted(reports.items()):
        if report["wish_sha256"] != wish_sha256:
            raise ContractError(
                "Blocked Report %d is not bound to this run's Wish; a fix run never "
                "carries its source's ledger, which stays in revision-source.zip "
                "as the source's record" % number
            )
        if report["status"] in OPEN_BLOCKED:
            held.append("%d (%s, %s)" % (number, report["component"], report["status"]))
    if read_log is not None:
        try:
            record_ledger_reads(read_log, [ledger], wish_sha256)
        except (OSError, UnicodeError, ValueError) as exc:
            raise StateConflict("the Blocked Report ledger read could not be logged") from exc
    if held:
        raise ContractError(
            "Blocked Report %s is open; the Workshop Manager answers each with "
            "make_round --clear-blocked (a decision, or a need quoting its rows) "
            "before Make is proposed" % ", ".join(held)
        )
    return [report_summary(report) for _, report in sorted(reports.items())]


def run_blocked_reports(run_root: Path, *, now: Optional[datetime] = None) -> list[dict[str, Any]]:
    """Every Blocked Report of every Make attempt in a run workspace, oldest
    attempt first, for the run report. An unreadable ledger is listed as
    invalid rather than hidden."""

    attempts = Path(run_root).joinpath(*_MAKE_ATTEMPTS)
    if not attempts.is_dir():
        return []
    listed: list[dict[str, Any]] = []
    for attempt in sorted(attempts.glob("r[0-9][0-9][0-9][0-9]")):
        product = attempt / "product"
        if product.is_symlink() or not product.is_dir():
            continue
        for ledger in sorted(product.rglob(BLOCKED_REPORTS_NAME)):
            if ledger.parent.name != "measure":
                continue
            where = {"attempt": attempt.name, "ledger": ledger.relative_to(run_root).as_posix()}
            try:
                reports = _read_ledger(ledger)
            except ContractError:
                listed.append({**where, "status": "invalid"})
                continue
            listed.extend(
                {**where, **report_summary(report, now=now)}
                for _, report in sorted(reports.items())
            )
    return listed


__all__ = [
    "report_summary",
    "verify_ledger_reads",
    "run_blocked_reports",
    "verify_no_open_blocked_reports",
]
