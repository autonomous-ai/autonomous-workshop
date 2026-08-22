"""eve — the tick driver and CLI for Eve, the autonomous board-game inventor.

One tick advances ONE unit of work (one gate, one book study, one improvement
session, or one stage of one game), then exits. launchd fires a tick every 30
minutes; the machine sleeping just makes the next tick a catch-up (state lives
entirely on disk, so a long gap costs time and nothing else — the heartbeat
still records when the loop was last alive).

Tick preconditions, in order, all in code (DESIGN.md ss.4):
  1. reward-ledger audit clean   — never improve/advance from an unverifiable score;
  2. heartbeat stamped first     — alive-but-idle is distinguishable from dead.

Work priority (quality over quantity): finish a game > study a book > weekly
self-improvement > weekly ship-check. Finishing beats starting; no daily floor
on *shipping*, only on *progress*.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent  # repo root: .../inventors/eve
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from eve import config, meta  # noqa: E402


def _cfg():
    return config.Config.load()


def _meta(journal=None):
    return meta.Meta(_cfg(), journal=journal)


def cmd_tick(args):
    m = _meta()
    m.heartbeat()
    ok, problems = m.audit_ok()
    if not ok:
        print("tick: HALTED — ledger audit red:")
        for p in problems:
            print("  - %s" % p)
        return 0  # launchd keeps firing; a human reads status
    # A launched tick does bookkeeping + deterministic gates. Agent dispatch
    # is opt-in (run_agent) so the harness is offline-safe and deterministic.
    out = m.tick(run_agent=args.run_agent)
    print("tick: %s" % json.dumps(out, default=str)[:400])
    return 0


def cmd_status(_args):
    from eve import queue as queue_mod
    q = queue_mod.Queue(_cfg())
    by_stage = {}
    for g in q.list():
        by_stage.setdefault(g.stage, []).append(g.slug)
    print("queue (%d games):" % len(q.list()))
    for stage in queue_mod.STAGES:
        if stage in by_stage:
            print("  %-10s %s" % (stage, ", ".join(by_stage[stage])))
    m = _meta()
    book = m._read_daybook()
    print("heartbeat: %s" % book.get("heartbeat", "never"))
    print("last_books_study: %s" % book.get("last_books_study", "never"))
    print("last_improve: %s" % book.get("last_improve", "never"))
    ok, problems = m.audit_ok()
    print("audit: %s" % ("clean" if ok else ", ".join(problems)))
    return 0


def cmd_audit(_args):
    from eve.reward import audit
    problems = audit(_cfg())
    for p in problems:
        print(p)
    return 1 if problems else 0


def cmd_improve(_args):
    m = _meta()
    result = m.improve()
    print(json.dumps(result, indent=2, default=str))
    return 0


def cmd_publish(args):
    """Manual publish of a shipped game (the autonomous flip lives in the
    pipeline). Taps the org's existing product-page pipeline; offline-safe."""
    from eve.queue import Queue
    from eve import publish
    q = Queue(_cfg())
    game = q.get(args.slug)
    if game is None:
        print("no such game: %s" % args.slug)
        return 1
    if game.stage != "ship":
        print("refusing: %s is %s, not 'ship'" % (args.slug, game.stage))
        return 1
    cfg = _cfg()
    result = publish.publish_to_store(cfg, game, status="draft")
    print(json.dumps(result, indent=2, default=str))
    return 0


def cmd_seed(_args):
    cfg = _cfg()
    from eve import corpus, books
    corpus.seed(cfg)
    corpus.seed_owned(cfg)
    books.seed_reading_list(cfg)
    m = _meta()
    m.heartbeat()
    print("seeded: corpus + owned set + reading list + daybook")
    return 0


def cmd_daemon(args):
    ops = HERE / "ops"
    if args.action == "install":
        return subprocess.call(["bash", str(ops / "install.sh")])
    if args.action == "uninstall":
        return subprocess.call(["bash", str(ops / "uninstall.sh")])
    label = "ai.autonomous.eve"
    return subprocess.call(
        "launchctl list | grep %s || echo 'not installed'" % label, shell=True)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="eve", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("tick")
    p.add_argument("--run-agent", action="store_true",
                   help="allow agent dispatch for LLM stages (offline-safe default)")
    p.set_defaults(fn=cmd_tick)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("audit").set_defaults(fn=cmd_audit)
    sub.add_parser("improve").set_defaults(fn=cmd_improve)
    p = sub.add_parser("publish")
    p.add_argument("slug")
    p.set_defaults(fn=cmd_publish)
    sub.add_parser("seed").set_defaults(fn=cmd_seed)
    p = sub.add_parser("daemon")
    p.add_argument("action", choices=["install", "uninstall", "status"])
    p.set_defaults(fn=cmd_daemon)
    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
