"""A geometry worker must die when its supervisor disappears.

The worker execs in its own process group. Its tiny child watchdog holds only a
read end of a pipe owned by the supervisor, so EOF means that owner has gone.
Unlike an in-process thread, the watchdog remains runnable during native calls.
"""
import os
from pathlib import Path
import select
import signal
import subprocess
import sys


def main():
    if sys.argv[1] == "--watch":
        descriptor, allowance = int(sys.argv[2]), float(sys.argv[3])
        parent = os.getppid()
        select.select([descriptor], [], [], allowance)
        # This PID is our actual parent, never a caller-supplied target. It must
        # still own the dedicated group created by GeometryWorker._start.
        if parent > 1 and os.getppid() == parent and os.getpgid(parent) == parent:
            os.killpg(parent, signal.SIGKILL)
        return 0
    descriptor, allowance = int(sys.argv[1]), sys.argv[2]
    subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--watch", str(descriptor), allowance],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        pass_fds=(descriptor,),
    )
    os.close(descriptor)
    os.execvp(sys.argv[3], sys.argv[3:])


if __name__ == "__main__":
    raise SystemExit(main())
