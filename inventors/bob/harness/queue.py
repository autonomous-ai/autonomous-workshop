"""The game queue — the only decision-maker in Bob's pipeline.

Port of the best of vibe-ideas' pipeline_queue.py (docs/research/
vibe-ideas-lessons.md §1.1-1.2). The design creed, straight from that file's
receipts:

- The unit of work is a GAME, not a tick. vibe-ideas lost fifteen turns to a
  loop that replaced a crashed idea with a fresh one every tick and finished
  nothing. A game leaves this queue only by going live or by being killed for
  a stated reason.
- State transitions are decided HERE, in code. "A stage is complete when this
  file says so, not when a model reports success." Agents never see or edit
  this file's constants.
- State says where a game *got to*; a lease says someone is *moving it*.
  Two drivers on a short launchd interval cannot double-spawn onto the same
  game dir; a crashed driver's lease lapses within the hour.

Auto-publish lane note: the CONTRACTS §1 schema enum still lists
``awaiting_owner``/``approved`` from the old human-flip ladder, but Dee's
2026-08-22 ruling ("publish on our website automatically") removed the owner
turnstile for this lane, so those two states do not exist here. reviewed →
published is Bob's own move once publish-eligible + validator green.
"""

import fcntl
import hashlib
import json
import os
import time
import uuid
from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------

# The pipeline in gate order. Gate order IS the economics (the Armillary
# receipt: 6 CAD repair rounds spent on rules that later failed the playtest —
# nothing expensive happens before the game is machine-played and LLM-tabled).
PIPELINE = [
    "sparked", "researched", "ruled", "rules_gated", "simulated", "tabled",
    "briefed", "built", "build_gated", "reviewed", "published", "live",
]

# Side states. "Terminal" means both scheduler-terminal and lifecycle-terminal
# for ordinary operation. parked/blocked are reopened explicitly; killed/live
# never re-enter the invent loop.
TERMINAL = frozenset(["live", "parked", "blocked", "killed"])

# A `published` game is deliberately waiting, not terminal: it is a draft or a
# dry-run receipt awaiting an explicit authenticated flip/reconciliation.
# Scheduling it used to advance unconditionally to `live`, including when
# published.json said pushed=false. It may still be parked by an operator.
WAITING = frozenset(["published"])

ALL_STATES = PIPELINE + ["parked", "blocked", "killed"]

# Closest-to-publish first: "finishing something beats starting something.
# sparked sits last so a backlog never crowds out a build" (vibe-ideas
# PRIORITY, ported with Bob's state names).
PRIORITY = [
    "reviewed", "build_gated", "built", "briefed", "tabled",
    "simulated", "rules_gated", "ruled", "researched", "sparked",
]

# The vibe-ideas scheduler-hole receipt: a state missing from PRIORITY is a
# state the scheduler silently never touches — every idea that reached it
# stalled forever and nothing alarmed. This assert makes that bug impossible
# to ship: every state is either schedulable or DELIBERATELY terminal.
assert set(PRIORITY) | set(WAITING) | set(TERMINAL) == set(ALL_STATES), (
    "PRIORITY + WAITING + TERMINAL must cover every state exactly — a state "
    "outside them is a silent stall"
)
assert not (set(PRIORITY) & set(TERMINAL) or
            set(PRIORITY) & set(WAITING) or
            set(WAITING) & set(TERMINAL)), (
    "a state cannot be schedulable, waiting, and/or terminal at once"
)

# Explicit legal moves. Forward edges follow the pipeline; backward edges are
# the paid rework paths (gate failures send RULES back — the playtest gate
# rewound 3 of vibe-ideas' 6 ideas — and the build gate sends the BUILD back
# for a repair round, never the rules).
_FORWARD = {
    "sparked": {"researched"},
    "researched": {"ruled"},
    "ruled": {"rules_gated"},
    "rules_gated": {"simulated", "ruled"},
    "simulated": {"tabled", "ruled"},
    "tabled": {"briefed", "ruled"},
    "briefed": {"built"},
    "built": {"build_gated"},
    "build_gated": {"reviewed", "built"},
    "reviewed": {"published", "ruled", "built"},
    "published": {"live"},
}

TRANSITIONS = {}
for _s, _targets in _FORWARD.items():
    # Any working state may park (budget/judgement pause), block (cascade
    # stop / infra fault), or be killed for a stated reason.
    TRANSITIONS[_s] = frozenset(_targets | {"parked", "blocked", "killed"})
TRANSITIONS["parked"] = frozenset(set(PRIORITY) | {"killed"})
TRANSITIONS["blocked"] = frozenset(set(PRIORITY) | {"parked", "killed"})
TRANSITIONS["live"] = frozenset()    # done is done
TRANSITIONS["killed"] = frozenset()  # dead is dead; a revival is a new slug

assert set(TRANSITIONS) == set(ALL_STATES), "every state needs a transition row"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# 45 min: longer than any single agent step (agents cap at 15 min per
# CONTRACTS §2 runner), shorter than two 30-min launchd ticks — a crashed
# driver's game is claimable again within the hour (vibe-ideas
# CLAIM_TTL_SECONDS = 45*60, ported unchanged).
LEASE_MINUTES = 45

# 30s: a transaction is a JSON read-modify-write, milliseconds when healthy.
# Waiting longer than 30s means the other holder is wedged, and failing loud
# beats queueing behind a corpse (vibe-ideas LOCK_TIMEOUT_SECONDS).
LOCK_TIMEOUT_SECONDS = 30.0

Step = namedtuple("Step", ["slug", "state", "lease_id"])


# ---------------------------------------------------------------------------
# Paths (env read inside functions, never at import time — testability rule,
# CONTRACTS §6)
# ---------------------------------------------------------------------------

def bob_home():
    """BOB_HOME: env override, else the repo bob/ dir (parent of harness/)."""
    env = os.environ.get("BOB_HOME")
    if env:
        return os.path.abspath(env)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _state_dir():
    d = os.path.join(bob_home(), "state")
    os.makedirs(d, exist_ok=True)
    return d


def _queue_path():
    return os.path.join(_state_dir(), "QUEUE.json")


def _lock_path():
    return os.path.join(_state_dir(), ".lock")


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat()


# ---------------------------------------------------------------------------
# Lock, load, save, transaction
# ---------------------------------------------------------------------------

@contextmanager
def locked():
    """fcntl.flock on state/.lock, exclusive, with a bounded wait.

    flock ties the lock to the open file description, so two transactions in
    the same process (different fds) exclude each other just like two
    processes do — which is exactly the double-driver case leases exist for.
    """
    fh = open(_lock_path(), "a+")
    try:
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (BlockingIOError, OSError):
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "could not lock %s within %.0fs — another bob process "
                        "is wedged; find it (ps aux | grep bob) or remove a "
                        "stale holder before retrying" % (_lock_path(),
                                                          LOCK_TIMEOUT_SECONDS)
                    )
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    finally:
        fh.close()


def load():
    """Read QUEUE.json; a missing file is an empty queue, not an error."""
    path = _queue_path()
    if not os.path.exists(path):
        return {"version": 2, "games": {}}
    with open(path, "r") as fh:
        return json.load(fh)


def save(q):
    """Atomic save: tmp in the same dir + os.replace, so a dashboard reading
    without the lock never sees a half-written file (vibe-ideas rule)."""
    _atomic_write_json(_queue_path(), q)


def _atomic_write_json(path, obj):
    tmp = "%s.tmp.%s" % (path, uuid.uuid4().hex[:8])
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


@contextmanager
def transaction():
    """Lock → load → yield the queue dict → save. The ONLY correct way to do
    a read-modify-write; an exception inside the block saves nothing."""
    with locked():
        q = load()
        yield q
        save(q)


# ---------------------------------------------------------------------------
# Games
# ---------------------------------------------------------------------------

def add_game(slug, title, direction=None):
    """Register a fresh spark. Integrator convenience; not in CONTRACTS §2 but
    every caller needs it and inlining the schema invites drift."""
    with transaction() as q:
        if slug in q["games"]:
            raise ValueError(
                "game '%s' already exists — pick a new slug or advance the "
                "existing one" % slug
            )
        now = _iso(_now())
        q["games"][slug] = {
            "slug": slug,
            "title": title,
            "state": "sparked",
            "direction": direction or {},
            "budgets": {"clarify_used": 0, "rework_used": 0, "repair_used": 0},
            "reward": {"latest": 0.0, "history": []},
            "lease": {"holder": None, "expires": None},
            "created": now,
            "log": [{"at": now, "from": None, "to": "sparked",
                     "note": "sparked"}],
        }
        return q["games"][slug]


def _lease_active(game):
    lease = game.get("lease") or {}
    if not lease.get("holder") or not lease.get("expires"):
        return False
    try:
        expires = datetime.fromisoformat(lease["expires"])
    except ValueError:
        return False  # unparseable lease = broken lease = reclaimable
    return expires > _now()


def claim_next(loop_name):
    """Hand out the one step closest to publishing, and CLAIM it.

    Returns Step(slug, state, lease_id) or None when nothing is claimable.
    The claim is the point: `next` without a lease let two drivers on a short
    loop double-spawn onto the same files (vibe-ideas receipt). An expired
    lease is free — a crashed driver costs at most LEASE_MINUTES.
    """
    with transaction() as q:
        for state in PRIORITY:
            candidates = [
                g for g in q["games"].values()
                if g.get("state") == state and not _lease_active(g)
            ]
            if not candidates:
                continue
            # Oldest first within a state: finishing beats starting, and the
            # longest-waiting game finishes first.
            game = sorted(candidates, key=lambda g: g.get("created") or "")[0]
            lease_id = uuid.uuid4().hex
            game["lease"] = {
                "holder": loop_name,
                "id": lease_id,
                "expires": _iso(_now() + timedelta(minutes=LEASE_MINUTES)),
            }
            return Step(game["slug"], state, lease_id)
        return None


def advance(slug, to_state, note, lease_id=None):
    """Move a game to to_state if the TRANSITIONS map allows it.

    Appends a log row and releases the lease — the step is over either way.
    Illegal moves raise ValueError naming the legal ones, because a stale
    caller (the vibe-ideas stray-Telegram-tap receipt) must be refused, never
    absorbed.

    lease_id (optional) is the fencing token from claim_next(): a driver
    that wedged past LEASE_MINUTES and lost its lease to a fresh claim
    must not be able to move the game under the new holder. Pass the
    Step's lease_id and a mismatch is a logged no-op returning False —
    False, not an exception, because the stale driver did nothing wrong
    except being slow, and its cleanup path should not crash. Success
    returns the (truthy) game dict. Callers that don't pass lease_id keep
    the old trusting behavior unchanged.
    """
    if to_state not in set(ALL_STATES):
        raise ValueError(
            "unknown state '%s' — legal states: %s" % (to_state,
                                                       ", ".join(ALL_STATES))
        )
    with transaction() as q:
        game = q["games"].get(slug)
        if game is None:
            raise KeyError(
                "no game '%s' in the queue — check the slug with load(), or "
                "add_game() it first" % slug
            )
        if lease_id is not None and \
                (game.get("lease") or {}).get("id") != lease_id:
            # Fenced out: record the refusal in the game log (durable
            # evidence of a wedged driver) but touch nothing else — the
            # current holder's lease and state stay exactly as they are.
            game["log"].append({
                "at": _iso(_now()), "from": game["state"],
                "to": game["state"],
                "note": "fenced: stale lease refused advance to %s (%s)"
                        % (to_state, note),
            })
            return False
        frm = game["state"]
        allowed = TRANSITIONS[frm]
        if to_state not in allowed:
            raise ValueError(
                "illegal transition %s -> %s for '%s' — legal from %s: %s. "
                "If this is a stale verdict, drop it; the queue's state is "
                "the truth" % (frm, to_state, slug, frm,
                               ", ".join(sorted(allowed)) or "(none, terminal)")
            )
        game["state"] = to_state
        game["log"].append({
            "at": _iso(_now()), "from": frm, "to": to_state, "note": note,
        })
        game["lease"] = {"holder": None, "expires": None}
        return game


def release(slug, lease_id=None):
    """End a step WITHOUT faking progress: clear the lease, change nothing
    else. For drivers that claimed a step and then could not act on it.

    lease_id (optional): same fencing token as advance() — a stale driver
    releasing a lease it no longer holds would wipe the NEW holder's
    lease mid-work. Mismatch is a logged no-op returning False."""
    with transaction() as q:
        game = q["games"].get(slug)
        if game is None:
            raise KeyError(
                "no game '%s' to release — nothing to do" % slug
            )
        if lease_id is not None and \
                (game.get("lease") or {}).get("id") != lease_id:
            game["log"].append({
                "at": _iso(_now()), "from": game["state"],
                "to": game["state"],
                "note": "fenced: stale lease refused release",
            })
            return False
        game["lease"] = {"holder": None, "expires": None}
        return game


def park(slug, reason):
    """Park with a stated reason. Exhaustion is never silent (CONTRACTS §1)."""
    return advance(slug, "parked", "parked: %s" % reason)


def park_or_kill(slug, reason):
    """The rework-exhaustion rule, enforced by the queue, not the caller.

    vibe-ideas: "an idea still failing after three balancing passes is a
    shape problem, not a tuning one" — rework budget gone means the next
    failure kills, everything else parks for a human or a budget reset.
    Returns the game dict; read game["state"] for which way it went.
    """
    # Import here, not at module top: budgets imports queue for mech_surface
    # and the transaction machinery, so top-level would be circular.
    from harness import budgets

    with locked():
        q = load()
        game = q["games"].get(slug)
        if game is None:
            raise KeyError("no game '%s' to park or kill" % slug)
        exhausted = (
            game.get("budgets", {}).get("rework_used", 0)
            >= budgets.REWORK_BUDGET
        )
    if exhausted:
        return advance(slug, "killed",
                       "killed (rework budget exhausted): %s" % reason)
    return park(slug, reason)


# ---------------------------------------------------------------------------
# Mechanic surface — the anti-laundering hash
# ---------------------------------------------------------------------------

# Keys inside rules/actions that a legitimate clarify is free to touch:
# pure prose, no mechanics. Everything ELSE in the rules block is surface
# — the hole this closes was hashing only rules['win'], which let a
# "clarify" rewrite movement/turn/effect rules for free (up to
# CLARIFY_BUDGET=3 laundered reworks per game).
_PROSE_KEYS = frozenset(["description", "flavor", "notes", "summary"])


def _strip_prose(obj):
    """Recursively drop prose keys so only mechanic-bearing fields hash."""
    if isinstance(obj, dict):
        return {k: _strip_prose(v) for k, v in obj.items()
                if k not in _PROSE_KEYS}
    if isinstance(obj, list):
        return [_strip_prose(v) for v in obj]
    return obj


def mech_surface(game_doc):
    """sha256 over exactly the mechanic-defining fields of a game doc.

    The vibe-ideas jewel: a "clarify" (free-ish lane, wording only) that
    actually changed mechanics must be converted into a paid rework after the
    fact — "the disposition is the gate's to assign and the queue's to
    enforce, not the fixer's to claim." So the hash covers action types plus
    every non-prose field of structured actions, the FULL rules block minus
    prose keys (_PROSE_KEYS), player counts, and component name/qty — and
    deliberately NOT descriptions, wording, concept, or art direction, which
    a legitimate clarify is free to touch.
    """
    structured = game_doc.get("actions") or []
    actions = game_doc.get("action_types")
    if actions is None:
        # Docs that carry structured actions instead of a flat list.
        actions = [
            a.get("type") or a.get("name")
            for a in structured
        ]
    # Non-prose fields of each structured action (effects, costs, ranges)
    # are mechanics too — 'move 1' -> 'move up to 3' must change the hash.
    # Empty when actions carry only type/name, so a doc with a flat
    # action_types list and one with bare typed dicts hash identically.
    action_detail = []
    for a in structured:
        if not isinstance(a, dict):
            continue
        fields = _strip_prose(
            {k: v for k, v in a.items() if k not in ("type", "name")})
        if fields:
            action_detail.append(
                {"action": a.get("type") or a.get("name"), "fields": fields})
    action_detail.sort(
        key=lambda d: json.dumps(d, sort_keys=True, default=str))
    rules = game_doc.get("rules") or {}
    components = []
    for c in (game_doc.get("components") or []):
        components.append({
            "name": c.get("name"),
            "qty": c.get("qty"),
            "per_player": c.get("per_player"),
        })
    surface = {
        "action_types": sorted(str(a) for a in (actions or [])),
        "action_detail": action_detail,
        "rules": _strip_prose(rules),
        "players": game_doc.get("players"),
        "components": sorted(components,
                             key=lambda c: (str(c["name"]), str(c["qty"]))),
    }
    blob = json.dumps(surface, sort_keys=True, separators=(",", ":"),
                      default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
