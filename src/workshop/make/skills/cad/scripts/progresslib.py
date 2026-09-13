"""Progress lines on stderr for the long CAD sweeps.

A motion sweep or a motion presentation is minutes to tens of minutes of
Boolean geometry and tessellation. Silent, it is indistinguishable from a
hang: an operator watching the process can see CPU burning and still not know
whether to wait or to kill it, and neither can the agent that started it.
These lines say which phase is running, how far through it is, and how long
the rest should take at the pace measured so far.

Only stderr is written -- stdout carries the JSON and report contracts -- and
nothing here reads or changes a result, a hash or an exit status. Lines are
whole lines, not carriage-return redraws, so a captured log stays readable.

Set ``WORKSHOP_PROGRESS=0`` to silence them, and
``WORKSHOP_PROGRESS_INTERVAL`` to change the seconds between updates within a
loop (default 10; 0 reports every item).
"""
from __future__ import annotations

import contextlib
import os
import sys
import time
from contextvars import ContextVar

DEFAULT_INTERVAL_SECONDS = 10.0

# The condition or project currently being worked, so a loop deep in a check
# can name itself without every helper having to carry the label down.
_SCOPE: ContextVar[str] = ContextVar("workshop_progress_scope", default="")


def enabled() -> bool:
    return os.environ.get("WORKSHOP_PROGRESS", "").strip().lower() not in ("0", "off", "no", "false")


def _interval() -> float:
    try:
        value = float(os.environ.get("WORKSHOP_PROGRESS_INTERVAL", ""))
    except ValueError:
        return DEFAULT_INTERVAL_SECONDS
    return value if value >= 0 else DEFAULT_INTERVAL_SECONDS


def duration(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes, seconds = divmod(int(seconds + 0.5), 60)
    if minutes < 60:
        return f"{minutes}m{seconds:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}m"


def write(message: str) -> None:
    if not enabled():
        return
    scope = _SCOPE.get()
    print(f"[{scope}] {message}" if scope else message, file=sys.stderr, flush=True)


@contextlib.contextmanager
def scope(label: str):
    """Name the work that progress lines inside this block belong to."""
    token = _SCOPE.set(str(label))
    try:
        yield
    finally:
        _SCOPE.reset(token)


@contextlib.contextmanager
def phase(label: str):
    """Announce a single unmeasurable step, and how long it actually took."""
    start = time.monotonic()
    write(f"{label} ...")
    try:
        yield
    except BaseException:
        write(f"{label} failed after {duration(time.monotonic() - start)}")
        raise
    write(f"{label} done in {duration(time.monotonic() - start)}")


class Deadline:
    """A wall-clock bound shared by the loops of one run.

    The clock only: what a stop means -- an inconclusive gate, a refused
    presentation -- belongs to the tool that set it. ``None`` or ``0`` seconds
    is no bound at all, so a caller can hand a configured value straight
    through without deciding whether to bound the run.
    """

    def __init__(self, seconds: float | None):
        self.seconds = float(seconds) if seconds else None
        self.started = time.monotonic()
        self.expires = None if self.seconds is None else self.started + self.seconds

    def expired(self) -> bool:
        return self.expires is not None and time.monotonic() > self.expires

    def elapsed(self) -> float:
        return time.monotonic() - self.started


class Progress:
    """Counted progress through a loop of roughly comparable items.

    ``advance()`` is throttled so a fast loop cannot flood the log; the first
    and last items always report, so a loop that finishes still says so.
    """

    def __init__(self, label: str, total: int | None = None, *, interval: float | None = None):
        self.label = label
        self.total = int(total) if total is not None else None
        self.interval = _interval() if interval is None else float(interval)
        self.count = 0
        self.started = time.monotonic()
        self._last = None
        write(f"{label}: {self.total} to go" if self.total is not None else f"{label}: started")

    def _emit(self, note: str = "") -> None:
        elapsed = time.monotonic() - self.started
        if self.total:
            remaining = elapsed / self.count * (self.total - self.count) if self.count else 0.0
            body = (f"{self.label}: {self.count}/{self.total} "
                    f"({100 * self.count // self.total}%), {duration(elapsed)} elapsed, "
                    f"~{duration(remaining)} left")
        else:
            body = f"{self.label}: {self.count} done, {duration(elapsed)} elapsed"
        write(f"{body}{note}")
        self._last = time.monotonic()

    def item(self, name: str) -> None:
        """Announce the start of a named item; never throttled."""
        self.count += 1
        position = f"{self.count}/{self.total}" if self.total else str(self.count)
        write(f"{self.label} {position}: {name} "
              f"({duration(time.monotonic() - self.started)} elapsed)")
        self._last = time.monotonic()

    def advance(self, note: str = "") -> None:
        self.count += 1
        now = time.monotonic()
        due = self._last is None or now - self._last >= self.interval
        if due or (self.total is not None and self.count >= self.total):
            self._emit(f" {note}" if note else "")

    def finish(self, note: str = "") -> None:
        elapsed = duration(time.monotonic() - self.started)
        write(f"{self.label}: {self.count} done in {elapsed}{' ' + note if note else ''}")
