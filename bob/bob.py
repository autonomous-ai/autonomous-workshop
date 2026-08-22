#!/usr/bin/env python3
"""bob — the tick driver and CLI for Bob, the autonomous board-game inventor.

One tick advances ONE step of ONE loop, then exits. launchd fires a tick every
30 minutes; the machine sleeping just makes the next tick a catch-up (state
lives entirely on disk, so a 10-hour gap costs time and nothing else).

Tick preconditions, in order, all in code (CONTRACTS §3):
  1. integrity.audit() clean   — a drifted reward hash halts everything.
  2. daily spend under cap     — dollars are a ceiling, never a surprise.
  3. quota window clear        — a retry against an exhausted subscription
                                 cap burns wall-clock and produces nothing
                                 (text2cad receipt, 08-13: silent dead cycle).
Work priority: finish a game (invent) > learn (scholar/librarian) >
architecture sweep (weekly) > weekly self-improvement. Finishing beats
starting; studying never starves an in-flight game.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from harness import agents, integrity, ledger, queue  # noqa: E402

DAILY_BUDGET_DEFAULT = 25.0
IMPROVE_EVERY_DAYS = 7


def _now():
    return datetime.now(timezone.utc)


def _daybook_path():
    return os.path.join(queue.bob_home(), "state", "DAYBOOK.json")


def _read_daybook():
    try:
        with open(_daybook_path()) as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def _write_daybook(book):
    path = _daybook_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as handle:
        json.dump(book, handle, indent=2, sort_keys=True)
    os.replace(tmp, path)


def _stamp_heartbeat():
    """First act of every tick, BEFORE any precondition — a tick that skips
    still proves launchd fired (text2cad's watchdog contract)."""
    book = _read_daybook()
    book["heartbeat"] = _now().isoformat()
    _write_daybook(book)


def _quota_blocked(book):
    until = book.get("quota_until")
    if not until:
        return None
    try:
        when = datetime.fromisoformat(until)
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return until if when > _now() else None


def _set_quota_wait(minutes=60):
    book = _read_daybook()
    book["quota_until"] = (_now() + timedelta(minutes=minutes)).isoformat()
    _write_daybook(book)


def _improve_due(book):
    last = book.get("improve_last_run")
    if not last:
        return True
    try:
        when = datetime.fromisoformat(last)
    except ValueError:
        return True
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return (_now() - when) >= timedelta(days=IMPROVE_EVERY_DAYS)


def cmd_tick(_args):
    _stamp_heartbeat()

    violations = integrity.audit()
    hard = [v for v in violations if "warning" not in v.lower()]
    if hard:
        print("tick: HALTED — integrity audit red:")
        for v in hard:
            print("  - %s" % v)
        return 0  # logged no-op: launchd keeps firing, a human reads status

    cap = float(os.environ.get("BOB_DAILY_BUDGET_USD", DAILY_BUDGET_DEFAULT))
    spent = ledger.spend_today()
    if spent >= cap:
        print("tick: no-op — $%.2f of $%.2f daily budget spent" % (spent, cap))
        return 0

    book = _read_daybook()
    blocked = _quota_blocked(book)
    if blocked:
        print("tick: no-op — quota window blocked until %s" % blocked)
        return 0

    from harness.agents import QuotaExhausted

    # 1) Finishing beats starting: an in-flight game first.
    step = queue.claim_next("invent")
    if step is not None:
        from loops import invent
        print("tick: invent %s (%s)" % (step.slug, step.state))
        try:
            invent.tick(step)
        except QuotaExhausted:
            queue.release(step.slug)
            _set_quota_wait()
            print("tick: quota exhausted — deferred 60 min")
        return 0

    # 2) Nothing claimable? Maybe the queue is EMPTY — spark a new game.
    q = queue.load()
    active = [g for g in q["games"].values()
              if g["state"] not in queue.TERMINAL]
    max_inflight = int(os.environ.get("BOB_MAX_INFLIGHT", "3"))
    if len(active) < max_inflight:
        from loops import invent
        slug = invent.spark_new()
        if slug:
            print("tick: sparked new game %s" % slug)
            return 0

    # 3) Learn: one scholar/librarian unit.
    try:
        from loops import scholar
        result = scholar.tick()
        if result:
            print("tick: scholar %s" % json.dumps(result)[:200])
            return 0
    except QuotaExhausted:
        _set_quota_wait()
        print("tick: quota exhausted in scholar — deferred 60 min")
        return 0

    # 4) Weekly architecture sweep.
    try:
        from loops import architect
        result = architect.tick()
        if result:
            print("tick: architect swept")
            return 0
    except QuotaExhausted:
        _set_quota_wait()
        return 0

    # 5) Weekly self-improvement (last: it spends the most and rushes worst).
    if _improve_due(book):
        from loops import meta
        try:
            meta.improve()
        except QuotaExhausted:
            _set_quota_wait()
            return 0
        book = _read_daybook()
        book["improve_last_run"] = _now().isoformat()
        _write_daybook(book)
        print("tick: weekly improve session ran")
        return 0

    print("tick: quiet — everything current")
    return 0


def cmd_status(_args):
    q = queue.load()
    games = q.get("games", {})
    by_state = {}
    for slug, g in sorted(games.items()):
        by_state.setdefault(g["state"], []).append(slug)
    print("queue (%d games):" % len(games))
    for state in queue.PRIORITY + ["published", "live", "parked", "blocked", "killed"]:
        if state in by_state:
            print("  %-12s %s" % (state, ", ".join(by_state[state])))
    cap = float(os.environ.get("BOB_DAILY_BUDGET_USD", DAILY_BUDGET_DEFAULT))
    print("spend today: $%.2f of $%.2f" % (ledger.spend_today(), cap))
    book = _read_daybook()
    print("heartbeat: %s" % book.get("heartbeat", "never"))
    blocked = _quota_blocked(book)
    if blocked:
        print("quota: BLOCKED until %s" % blocked)
    violations = integrity.audit()
    if violations:
        print("audit:")
        for v in violations:
            print("  - %s" % v)
    else:
        print("audit: clean")
    return 0


def cmd_audit(_args):
    violations = integrity.audit()
    for v in violations:
        print(v)
    return 1 if any("warning" not in v.lower() for v in violations) else 0


def cmd_improve(_args):
    from loops import meta
    result = meta.improve()
    print(json.dumps(result, indent=2, default=str))
    book = _read_daybook()
    book["improve_last_run"] = _now().isoformat()
    _write_daybook(book)
    return 0


def cmd_publish(args):
    """Manual flip for a game the pipeline parked at the publish edge —
    the human override path. The autonomous flip lives in loops/invent.py."""
    from harness import publish
    errors = publish.validate(args.slug)
    if errors:
        print("validator red:")
        for e in errors:
            print("  - %s" % e)
        return 1
    publish.import_draft(args.slug)
    publish.curate(args.slug)
    if args.price_cents:
        publish.flip_public(args.slug, args.price_cents)
        print("published %s at %d cents" % (args.slug, args.price_cents))
    else:
        print("draft imported + curated; pass --price-cents to flip public")
    return 0


def cmd_unpublish(args):
    from harness import publish
    publish.unpublish(args.slug)
    print("unpublished %s" % args.slug)
    return 0


def cmd_seed(_args):
    """First run: make sure the state files exist and the bandit knows its
    arms. Idempotent — safe to run any time."""
    from harness import bandit
    os.makedirs(os.path.join(queue.bob_home(), "state"), exist_ok=True)
    queue.save(queue.load())          # materializes QUEUE.json
    arms = bandit.arms()              # materializes BANDIT.json from DIRECTIONS
    _stamp_heartbeat()
    violations = integrity.audit()    # materializes REWARD_BASELINE.json
    print("seeded: %d bandit arms, queue + daybook + baseline in place"
          % len(arms))
    for v in violations:
        print("  audit note: %s" % v)
    return 0


def cmd_daemon(args):
    ops = os.path.join(HERE, "ops")
    if args.action == "install":
        return subprocess.call(["bash", os.path.join(ops, "install.sh")])
    if args.action == "uninstall":
        return subprocess.call(["bash", os.path.join(ops, "uninstall.sh")])
    label = "ai.autonomous.bob"
    return subprocess.call(
        "launchctl list | grep %s || echo 'not installed'" % label, shell=True)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="bob", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tick").set_defaults(fn=cmd_tick)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("audit").set_defaults(fn=cmd_audit)
    sub.add_parser("improve").set_defaults(fn=cmd_improve)
    p = sub.add_parser("publish")
    p.add_argument("slug")
    p.add_argument("--price-cents", type=int, default=0)
    p.set_defaults(fn=cmd_publish)
    p = sub.add_parser("unpublish")
    p.add_argument("slug")
    p.set_defaults(fn=cmd_unpublish)
    sub.add_parser("seed").set_defaults(fn=cmd_seed)
    p = sub.add_parser("daemon")
    p.add_argument("action", choices=["install", "uninstall", "status"])
    p.set_defaults(fn=cmd_daemon)
    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
