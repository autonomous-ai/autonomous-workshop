#!/usr/bin/env python3
"""Watch a run and say something when it stalls or dies. Telegram only.

    ./watchdog.py logs/relay-phase1.log --slug keep-the-light-relay [--stall 25]

A text2game phase can legitimately be silent for 20 minutes; text2cad's BUILD
went 5174s before dying. The difference between "thinking" and "the gateway
hung" is whether ANYTHING is still being written - the log, or the agent's own
transcript. This watches both, and it never restarts anything: a blind retry
loop burns the night twice. It reports, a human decides.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402


def newest_write(paths) -> float:
    best = 0.0
    for p in paths:
        try:
            if p.is_dir():
                for f in p.rglob("*"):
                    if f.is_file():
                        best = max(best, f.stat().st_mtime)
            elif p.exists():
                best = max(best, p.stat().st_mtime)
        except OSError:
            continue
    return best


def alive(slug: str) -> bool:
    return subprocess.run(["pgrep", "-f", f"text2game .*--slug {slug}"],
                          capture_output=True).returncode == 0


def main() -> int:
    harness.load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--stall", type=float, default=25.0, help="minutes")
    ap.add_argument("--poll", type=float, default=60.0, help="seconds")
    a = ap.parse_args()

    log = Path(a.log).resolve()
    watched = [log, HERE / "out" / a.slug]
    print(f"watching {log.name} + out/{a.slug} (stall={a.stall}min)", flush=True)
    warned_at = 0.0
    while True:
        if not alive(a.slug):
            tail = "\n".join(log.read_text(encoding="utf-8",
                                           errors="replace").splitlines()[-6:]) \
                if log.exists() else "(no log)"
            pm = harness.postmortem(HERE / "out" / a.slug)
            harness.telegram(f"text2game {a.slug}: driver exited.\n\n{pm}\n\n{tail[-600:]}")
            print("driver gone, alerted", flush=True)
            return 0
        quiet = (time.time() - newest_write(watched)) / 60.0
        if quiet > a.stall and time.time() - warned_at > a.stall * 60:
            warned_at = time.time()
            harness.telegram(
                f"text2game {a.slug}: STALLED - nothing written for "
                f"{quiet:.0f} min. Gateway or phase may be hung.\n{log}")
            print(f"stall alert sent ({quiet:.0f} min quiet)", flush=True)
        time.sleep(a.poll)


if __name__ == "__main__":
    sys.exit(main())
