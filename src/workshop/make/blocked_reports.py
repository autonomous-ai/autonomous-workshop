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
"""

from __future__ import annotations

import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from workshop.errors import ContractError
from workshop.make.make_round_guard import (
    BLOCKED_REPORTS_NAME,
    MAX_BLOCKED_LEDGER_BYTES,
    OPEN_BLOCKED,
    blocked_reports,
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


def verify_no_open_blocked_reports(project: Path, *, wish_sha256: str) -> list[dict[str, Any]]:
    """Refuse Make output while a Blocked Report is open; return every report.

    A project without a ledger has none. A report not bound to this run's
    Wish, or a ledger that is not a valid sequence of events, is refused.
    """

    ledger = Path(project) / "measure" / BLOCKED_REPORTS_NAME
    if not ledger.exists() and not ledger.is_symlink():
        return []
    reports = _read_ledger(ledger)
    held = []
    for number, report in sorted(reports.items()):
        if report["wish_sha256"] != wish_sha256:
            raise ContractError(
                "Blocked Report %d is not bound to this run's Wish" % number
            )
        if report["status"] in OPEN_BLOCKED:
            held.append("%d (%s, %s)" % (number, report["component"], report["status"]))
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
    "run_blocked_reports",
    "verify_no_open_blocked_reports",
]
