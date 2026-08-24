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
import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from harness import agents, integrity, ledger, queue  # noqa: E402


def _load_dotenv():
    """launchd runs bob.py with a bare environment — the plist carries only
    PATH. Model routing, budget caps, and Telegram creds live in bob/.env,
    so the driver loads it itself (setdefault: a real environment variable
    always wins over the file)."""
    path = os.path.join(HERE, ".env")
    try:
        with open(path) as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, value)
    except OSError:
        pass

DAILY_BUDGET_DEFAULT = 25.0
IMPROVE_EVERY_DAYS = 7

# Wall-clock budget per tick, minutes. 45 = queue.LEASE_MINUTES: the lease
# is the promise "this driver is done or dead within 45", and the time
# budget is what makes the promise true (timebudget was dead code before —
# pre-launch verify finding 2026-08-22).
TICK_BUDGET_MINUTES = 45


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


def _update_daybook(mutate):
    """The ONE write path for bob.py's daybook fields, under the same
    state/.daybook.lock flock harness.agents uses to append cost rows —
    an unlocked read-modify-write here could erase a just-appended agent
    cost row, and the daybook is the only complete spend meter (pre-launch
    verify finding: the $25/day cap could be exceeded unseen). The tmp
    name carries the pid so two writers can never race on one tmp file.

    ``mutate(book)`` edits the freshly-read dict in place; the merged book
    is written atomically and returned."""
    path = _daybook_path()
    state_dir = os.path.dirname(path)
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, ".daybook.lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            book = _read_daybook()
            mutate(book)
            tmp = "%s.tmp.%d" % (path, os.getpid())
            with open(tmp, "w") as handle:
                json.dump(book, handle, indent=2, sort_keys=True)
            os.replace(tmp, path)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
    return book


def _stamp_heartbeat():
    """First act of every tick, BEFORE any precondition — a tick that skips
    still proves launchd fired (text2cad's watchdog contract)."""
    _update_daybook(lambda book: book.__setitem__(
        "heartbeat", _now().isoformat()))


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
    until = (_now() + timedelta(minutes=minutes)).isoformat()
    _update_daybook(lambda book: book.__setitem__("quota_until", until))


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

    # Preconditions clear: open the tick's wall-clock budget. 45 minutes
    # matches queue.LEASE_MINUTES — a tick that consults the run
    # (harness.agents caps each call by what's left) can never outlive its
    # own lease, which is what armed the unfenced-advance race. Handlers
    # are NOT wrapped here: run_agent reads the open run itself.
    from harness import timebudget
    timebudget.open_run(TICK_BUDGET_MINUTES)

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

    # 3) Learn: one scholar/librarian unit. outcome == "empty" means both
    # study queues are exhausted — that MUST fall through, or the truthy
    # empty dict makes steps 4-5 unreachable and the self-improvement loop
    # silently never runs in 24/7 operation (pre-launch verify finding).
    try:
        from loops import scholar
        result = scholar.tick()
        if result and result.get("outcome") not in ("empty",):
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
        _update_daybook(lambda b: b.__setitem__(
            "improve_last_run", _now().isoformat()))
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
    _update_daybook(lambda b: b.__setitem__(
        "improve_last_run", _now().isoformat()))
    return 0


def cmd_send(args):
    """Pack an inspected game and send it through Workshop's Shop Door."""
    from harness import send
    errors = send.validate(args.slug)
    if errors:
        print("validator red:")
        for e in errors:
            print("  - %s" % e)
        return 1
    send.send_draft(args.slug)
    send.curate(args.slug)
    if args.price_cents:
        send.flip_public(args.slug, args.price_cents)
        print("sent %s to the shop at %d cents" % (args.slug, args.price_cents))
    else:
        print("sent as a private draft; pass --price-cents to make it public")
    return 0


cmd_publish = cmd_send  # v0.2 CLI compatibility


def cmd_unpublish(args):
    from harness import send
    send.unpublish(args.slug)
    print("unpublished %s" % args.slug)
    return 0


def cmd_reconcile_public(args):
    """Read Shop Door state; never repeats the public-send effect."""
    from harness import send
    record = send.reconcile_public(args.slug)
    design = record.get("design") or {}
    print("verified public: %s (%s)" %
          (design.get("slug", args.slug), design.get("current_history_id")))
    return 0


def cmd_export(args):
    """Build the legacy text2game payload for explicit operator inspection.

    This compatibility command never changes Bob's queue or send projection;
    only ``send`` through Workshop may establish send authority.
    """
    from harness import export_box
    manifest = export_box.export_text2game(args.slug)
    print(json.dumps(manifest, indent=2))
    return 0 if manifest["complete"] else 1


def cmd_mark_published(args):
    """Refuse the obsolete box-receipt shortcut without mutating state.

    Kept as a compatibility command so an old runbook fails explicitly rather
    than silently treating a design id or human assertion as a Workshop
    receipt.
    """
    sys.stderr.write(
        "REFUSING to mark %s published from a manual/box observation: only "
        "`bob send %s` may create the Workshop product, durable Sender "
        "intent, and validated Shop Door Stamp required for Bob's published "
        "state. Historical box effects must remain external observations.\n"
        % (args.slug, args.slug)
    )
    return 2


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
    p = sub.add_parser("send")
    p.add_argument("slug")
    p.add_argument("--price-cents", type=int, default=0)
    p.set_defaults(fn=cmd_send)
    p = sub.add_parser("publish", help="compatibility alias for send")
    p.add_argument("slug")
    p.add_argument("--price-cents", type=int, default=0)
    p.set_defaults(fn=cmd_send)
    p = sub.add_parser("unpublish")
    p.add_argument("slug")
    p.set_defaults(fn=cmd_unpublish)
    p = sub.add_parser("reconcile-public")
    p.add_argument("slug")
    p.set_defaults(fn=cmd_reconcile_public)
    sub.add_parser("seed").set_defaults(fn=cmd_seed)
    p = sub.add_parser("export")
    p.add_argument("slug")
    p.set_defaults(fn=cmd_export)
    p = sub.add_parser("mark-published")
    p.add_argument("slug")
    p.add_argument("design_id")
    p.set_defaults(fn=cmd_mark_published)
    p = sub.add_parser("daemon")
    p.add_argument("action", choices=["install", "uninstall", "status"])
    p.set_defaults(fn=cmd_daemon)
    args = parser.parse_args(argv)
    _load_dotenv()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
