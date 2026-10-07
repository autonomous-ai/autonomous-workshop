#!/usr/bin/env python3
"""Wait for a long job in one tool call, and return the moment it ends.

On Claude Code a foreground ``Bash`` call blocks until its command exits, so
a fixed ``time.sleep(300)`` keeps waiting after the job it waits for has
already ended (issue #112). This helper checks locally, with no model
request, every ``--interval`` seconds and returns as soon as any watched
condition holds, or at the ``--timeout`` ceiling, which stays inside the
600000 ms ``Bash`` tool timeout:

- ``--pid N``: the process has exited;
- ``--exit-file F``: the job wrote its exit status (an integer) to ``F``;
- ``--file F``: ``F`` exists, and with ``--until-pattern`` its text matches.

With no watch it simply waits to the ceiling: the Claude Code wait for a
background agent's notification, which arrives when this call returns.
On return it prints why it ended, the exit status, and the last lines of
every ``--file`` and ``--log``. It always exits 0 unless its arguments are
invalid; the first line says whether the wait ``ended`` or reached the
``ceiling``. It reads only what it is told to watch and never schedules,
retries, or decides anything.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

MAX_TIMEOUT_SECONDS = 590.0
_TAIL_BYTES = 64 * 1024


def _pid_exited(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    try:
        fields = Path("/proc/%d/stat" % pid).read_text().rsplit(")", 1)[1].split()
    except (OSError, IndexError):
        return False
    return bool(fields) and fields[0] in {"Z", "X"}


def _read_tail(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - _TAIL_BYTES))
            return handle.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def _exit_status(path: Path):
    text = _read_tail(path).strip()
    return int(text) if re.fullmatch(r"-?\d+", text) else None


def _ended(arguments, pattern):
    reasons = []
    for pid in arguments.pid:
        if _pid_exited(pid):
            reasons.append("pid %d exited" % pid)
    for path in arguments.exit_file:
        status = _exit_status(path)
        if status is not None:
            reasons.append("%s: exit status %d" % (path, status))
    for path in arguments.file:
        if path.is_file() and (pattern is None or pattern.search(_read_tail(path))):
            reasons.append(
                "%s %s" % (path, "exists" if pattern is None else "matches the pattern")
            )
    return reasons


def _report(arguments, reasons, elapsed: float) -> None:
    if reasons:
        print("wait_for: ended after %.0f s: %s" % (elapsed, "; ".join(reasons)))
    else:
        print("wait_for: ceiling reached after %.0f s; nothing watched has ended" % elapsed)
    for pid in arguments.pid:
        print("pid %d %s" % (pid, "exited" if _pid_exited(pid) else "still running"))
    for path in arguments.exit_file:
        status = _exit_status(path)
        print("%s: %s" % (path, "no exit status yet" if status is None else "exit status %d" % status))
    for path in [*arguments.file, *arguments.log]:
        lines = _read_tail(path).splitlines()[-arguments.tail_lines:]
        print("--- last %d line(s) of %s ---" % (len(lines), path))
        for line in lines:
            print(line)
    sys.stdout.flush()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wait for a job in one tool call and return as soon as it ends."
    )
    parser.add_argument("--pid", type=int, action="append", default=[], help="a process to wait for")
    parser.add_argument("--exit-file", type=Path, action="append", default=[],
                        help="a file the job writes its integer exit status to when it ends")
    parser.add_argument("--file", type=Path, action="append", default=[],
                        help="a file whose existence (or --until-pattern match) ends the wait")
    parser.add_argument("--until-pattern", default=None,
                        help="a regular expression every --file is searched for")
    parser.add_argument("--log", type=Path, action="append", default=[],
                        help="a log whose last lines are printed on return; not watched")
    parser.add_argument("--interval", type=float, default=30.0,
                        help="seconds between local checks (default 30)")
    parser.add_argument("--timeout", type=float, default=570.0,
                        help="ceiling in seconds, at most %g (default 570)" % MAX_TIMEOUT_SECONDS)
    parser.add_argument("--tail-lines", type=int, default=20,
                        help="log lines printed per file on return (default 20)")
    return parser


def main(argv=None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    if not 0 < arguments.timeout <= MAX_TIMEOUT_SECONDS:
        parser.error("--timeout must be above 0 and at most %g seconds, inside the "
                     "600000 ms Bash tool timeout" % MAX_TIMEOUT_SECONDS)
    if not 0 < arguments.interval <= arguments.timeout:
        parser.error("--interval must be above 0 and at most --timeout")
    if arguments.until_pattern is not None and not arguments.file:
        parser.error("--until-pattern needs a --file to search")
    if arguments.tail_lines < 0:
        parser.error("--tail-lines must not be negative")
    try:
        pattern = None if arguments.until_pattern is None else re.compile(arguments.until_pattern)
    except re.error as exc:
        parser.error("--until-pattern is not a valid regular expression: %s" % exc)
    started = time.monotonic()
    deadline = started + arguments.timeout
    while True:
        reasons = _ended(arguments, pattern)
        now = time.monotonic()
        if reasons or now >= deadline:
            _report(arguments, reasons, now - started)
            return 0
        time.sleep(min(arguments.interval, deadline - now))


if __name__ == "__main__":
    raise SystemExit(main())
