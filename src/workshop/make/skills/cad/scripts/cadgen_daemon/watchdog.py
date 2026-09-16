"""Kill our owning daemon if its native request outlives a finite deadline.

This separate interpreter still runs when the geometry kernel holds the GIL.
The completion pipe closes on normal completion or parent death. No PID from a
client is trusted: only this process's actual, still-live parent can be killed.
"""
import os
import select
import signal
import sys


def main():
    descriptor, seconds = int(sys.argv[1]), float(sys.argv[2])
    parent = os.getppid()
    ready, _, _ = select.select([descriptor], [], [], seconds)
    if not ready and os.getppid() == parent and parent > 1:
        os.kill(parent, signal.SIGKILL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
