"""Thompson-sampling bandit over design directions — state/BANDIT.json.

Each arm is a mechanism-family bet from corpus/DIRECTIONS.json, held as
a Beta(alpha, beta) posterior. Thompson (sample each posterior, play the
argmax) beats UCB here because rewards are sparse and terminal-only:
one published game per arm per weeks, so we want posterior-width-driven
exploration, not visit-count bonuses.

Non-stationarity: taste and the market drift, so evidence decays —
x0.9 per week on the counts ABOVE the uniform Beta(1,1) prior, computed
from each arm's last-update timestamp. An arm that won in June must
re-earn its edge in September; decay toward (1,1) also naturally revives
exploration of neglected arms.

Priors come from receipts, not vibes: classic-reborn seeds Beta(3,2) —
2 real sales before Bob existed (the 2030 San Francisco chess set + the
xiangqi set, 08-2026) = 2 pseudo-wins, 1 pseudo-loss of humility. Every
other arm starts uninformative at Beta(1,1). The wildcard arm is ALWAYS
present — never let exploration hit zero (corpus/DIRECTIONS.json:
"never removed").

Terminal-event updates only (docs/REWARD.md): published -> R/100,
parked/killed after real iteration -> 0.15 (learning happened), and
post-publish market/human signal arrives as retro_bonus() fractional
pseudo-wins. Marketplace numbers never gate publishing and never enter
R — they only tilt this bandit (engagement-Goodhart guard).
"""

import fcntl
import json
import os
import random
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone

WEEKLY_DISCOUNT = 0.9      # x0.9/week on effective evidence
WILDCARD_ARM = "wildcard"  # the exploration reserve; guaranteed present
_PRIOR_RE = re.compile(r"alpha\s*=\s*([0-9.]+)\s*,\s*beta\s*=\s*([0-9.]+)")
_SECONDS_PER_WEEK = 7 * 24 * 3600.0

# 30s: a bandit write is a small JSON read-modify-write, milliseconds when
# healthy; waiting longer means the other holder is wedged, and failing
# loud beats queueing behind a corpse (same reasoning as queue.locked()).
_LOCK_TIMEOUT_SECONDS = 30.0


def _home():
    # Env read inside functions only (CONTRACTS §6).
    return os.environ.get("BOB_HOME") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))


def _state_path():
    return os.path.join(_home(), "state", "BANDIT.json")


def _directions_path():
    return os.path.join(_home(), "corpus", "DIRECTIONS.json")


def _now():
    return datetime.now(timezone.utc)


def _now_iso():
    return _now().isoformat()


def _parse_ts(ts):
    if not ts:
        return None
    try:
        # py3.9 fromisoformat can't read a trailing 'Z'.
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def _lock_path():
    return os.path.join(_home(), "state", ".bandit.lock")


@contextmanager
def _locked():
    """fcntl.flock on state/.bandit.lock, exclusive, bounded wait.

    Same pattern as queue.locked(): without it, a pick() in a manual tick
    and an update() in the launchd tick interleave load-mutate-save and
    one terminal reward observation silently vanishes from the posterior
    (reproduced: alpha 2.0 where 3.0 expected).
    """
    path = _lock_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fh = open(path, "a+")
    try:
        deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (BlockingIOError, OSError):
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "could not lock %s within %.0fs — another bob "
                        "process is wedged; find it (ps aux | grep bob) "
                        "before retrying" % (path, _LOCK_TIMEOUT_SECONDS))
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    finally:
        fh.close()


def _atomic_save(state):
    path = _state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)  # atomic per contract: readers never see half a file


def _prior_for(arm_id, spec):
    """Prior from DIRECTIONS.json prior_note ("alpha=3,beta=2"), else (1,1).

    Parsed from the note rather than hardcoded per-arm so a scholar-added
    arm with its own receipts can carry its own prior without touching
    this file (this file is not frozen, but the fewer edits the better).
    """
    note = ""
    if isinstance(spec, dict):
        note = str(spec.get("prior_note", "") or "")
    m = _PRIOR_RE.search(note)
    if m:
        try:
            a = float(m.group(1))
            b = float(m.group(2))
            if a > 0 and b > 0:
                return a, b
        except ValueError:
            pass
    return 1.0, 1.0


def _load_directions():
    path = _directions_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        arms = data.get("arms", {})
        if isinstance(arms, dict):
            return arms
    except (OSError, ValueError):
        pass
    # Corrupt or missing corpus must not stop the factory: fall back to
    # the exploration reserve alone.
    return {}


def _load_state():
    """Load BANDIT.json, seeding/syncing arms from DIRECTIONS.json.

    New arms (scholar/meta loops may ADD arms) get their prior on first
    sight; existing posteriors are never reset by a corpus edit. The
    wildcard arm is force-present even if the corpus file is gone.

    Returns (state, seeded): seeded is True iff this load added arms the
    file didn't have — pick() uses it to save ONLY then, so a read path
    can't overwrite a concurrent update() with a stale snapshot.
    """
    path = _state_path()
    state = None
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except ValueError:
            state = None  # corrupt state: reseed below rather than crash
    if not isinstance(state, dict) or not isinstance(state.get("arms"), dict):
        state = {"arms": {}, "total_pulls": 0}

    seeded = False
    now_iso = _now_iso()
    directions = _load_directions()
    for arm_id, spec in directions.items():
        if arm_id not in state["arms"]:
            a, b = _prior_for(arm_id, spec)
            state["arms"][arm_id] = {
                "alpha": a, "beta": b,
                "pulls": 0, "reward_sum": 0.0,
                # last = seed time: the decay clock starts when the belief
                # is written, so stale receipts fade like any evidence.
                "last": now_iso,
            }
            seeded = True
    if WILDCARD_ARM not in state["arms"]:
        state["arms"][WILDCARD_ARM] = {
            "alpha": 1.0, "beta": 1.0,
            "pulls": 0, "reward_sum": 0.0, "last": now_iso,
        }
        seeded = True
    return state, seeded


def _effective(arm, now=None):
    """Effective (alpha, beta) after the x0.9/week decay of the counts
    above the Beta(1,1) floor. Non-destructive: pick() samples from
    these; stored counts are only re-materialized on update()."""
    now = now or _now()
    last = _parse_ts(arm.get("last"))
    a = float(arm.get("alpha", 1.0))
    b = float(arm.get("beta", 1.0))
    if last is None:
        return max(a, 1e-9), max(b, 1e-9)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    weeks = max((now - last).total_seconds(), 0.0) / _SECONDS_PER_WEEK
    d = WEEKLY_DISCOUNT ** weeks
    # Decay only the evidence, never below the uninformative prior:
    # Beta(1,1) is the floor an arm forgets back to, not past.
    eff_a = 1.0 + (a - 1.0) * d
    eff_b = 1.0 + (b - 1.0) * d
    return max(eff_a, 1e-9), max(eff_b, 1e-9)


def pick():
    """Thompson sample: betavariate per arm on decayed counts, argmax."""
    with _locked():
        state, seeded = _load_state()
        if seeded:
            # Persist newly-seeded arms so audit sees them — and ONLY
            # then: an unconditional save here clobbered a concurrent
            # update()'s reward with this call's stale snapshot.
            _atomic_save(state)
    now = _now()
    best_arm = None
    best_draw = -1.0
    for arm_id in sorted(state["arms"]):  # sorted: deterministic under seeded RNG
        a, b = _effective(state["arms"][arm_id], now)
        draw = random.betavariate(a, b)
        if draw > best_draw:
            best_draw = draw
            best_arm = arm_id
    return best_arm


def update(arm, reward01):
    """Record a terminal event: alpha += r, beta += (1-r), r clamped to [0,1].

    Stored counts are first decayed to now (the sliding-window trick:
    materialize the discount at write time so the file always holds
    now-current evidence), then the new observation lands at full weight.
    """
    r = min(max(float(reward01), 0.0), 1.0)
    with _locked():
        state, _ = _load_state()
        if arm not in state["arms"]:
            raise ValueError(
                "Unknown bandit arm %r; known arms: %s. Add it to "
                "corpus/DIRECTIONS.json first." % (arm, sorted(state["arms"])))
        now = _now()
        rec = state["arms"][arm]
        eff_a, eff_b = _effective(rec, now)
        rec["alpha"] = eff_a + r
        rec["beta"] = eff_b + (1.0 - r)
        rec["pulls"] = int(rec.get("pulls", 0)) + 1
        rec["reward_sum"] = float(rec.get("reward_sum", 0.0)) + r
        rec["last"] = now.isoformat()
        state["total_pulls"] = int(state.get("total_pulls", 0)) + 1
        _atomic_save(state)
    return rec


def retro_bonus(arm, bonus):
    """Post-publish market/human signal: fractional pseudo-WINS only.

    A sale is +0.05 (capped by caller), an unprompted "asked to play
    again" report is +0.10 (docs/REWARD.md). Alpha-only, no beta, no
    pull: the market saying yes must never be able to look like a loss,
    and it is not a new trial — the trial already happened at publish.
    """
    b = min(max(float(bonus), 0.0), 1.0)
    with _locked():
        state, _ = _load_state()
        if arm not in state["arms"]:
            raise ValueError(
                "Unknown bandit arm %r; known arms: %s." % (arm, sorted(state["arms"])))
        now = _now()
        rec = state["arms"][arm]
        eff_a, eff_b = _effective(rec, now)
        rec["alpha"] = eff_a + b
        rec["beta"] = eff_b
        rec["last"] = now.isoformat()
        _atomic_save(state)
    return rec


def arms():
    """Current arms with stored and effective (decayed) counts."""
    state, _ = _load_state()  # read-only view: never saves, needs no lock
    now = _now()
    out = {}
    for arm_id, rec in state["arms"].items():
        eff_a, eff_b = _effective(rec, now)
        out[arm_id] = {
            "alpha": float(rec.get("alpha", 1.0)),
            "beta": float(rec.get("beta", 1.0)),
            "effective_alpha": eff_a,
            "effective_beta": eff_b,
            "pulls": int(rec.get("pulls", 0)),
            "reward_sum": float(rec.get("reward_sum", 0.0)),
            "last": rec.get("last"),
        }
    return out
