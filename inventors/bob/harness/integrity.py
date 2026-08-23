"""Integrity auditor — the tick loop's precondition, `bob audit`'s core.

The one sentence that decides everything: every system that ever
self-improved was an evaluator story; every one that failed edited its
own judge (DGM removed its hallucination markers). So this module's
whole job is proving the judge is still the judge:

  (a) reward freeze — sha256 of harness/reward.py and docs/REWARD.md
      pinned in state/REWARD_BASELINE.json; drift halts all ticks.
  (b) improve allowlist — the ONLY paths the meta loop may write,
      exported for loops/meta.py to enforce IN CODE before any write.
  (c) heartbeat — a silent channel must alarm (text2cad receipt:
      4-night scraper blackout 6/5-6/8; $13 silent burn 8/9-8/10).
  (d) sim-vs-human divergence — when the LLM tables stop predicting
      human verdicts, the judge is drifting and must not keep gating.

This file is itself on the FORBIDDEN list: an improver that can edit
its auditor has no auditor.
"""

import fnmatch
import hashlib
import json
import math
import os
import posixpath
from datetime import datetime, timezone

from harness import ledger  # pinned API (CONTRACTS §2): rows()

# --- (b) improve-loop write authority -----------------------------------
# loops/meta.py MUST check every intended write against these BEFORE
# applying it (path allowlist enforced in code, never in prompts —
# vibe-ideas: "budgets live in code, not prompts"; an agent that can
# read its own leash negotiates with it). Doc-tier only; code changes
# go to a branch + PR, never main.
IMPROVE_MAY_WRITE = [
    ".claude/agents/*.md",     # its own prompts
    "knowledge/lessons.md",    # graduated lessons
    "corpus/**",               # cards, queues, new bandit arms
    "knowledge/PROPOSALS.md",  # everything bigger becomes a proposal
]
# Never writable by the improve loop, whatever the allowlist says.
# reward.py + REWARD_BASELINE: the judge and its seal. TASTE.md: the
# owner's verbatim voice. state/**: the factory's memory. integrity.py:
# this auditor.
FORBIDDEN = [
    "harness/reward.py",
    "knowledge/TASTE.md",
    "state/**",
    "harness/integrity.py",
    "state/REWARD_BASELINE.json",
    # Judge/gate prompts are part of the judge: an improver that can edit
    # the rubric that scores it has re-sealed itself (the DGM
    # hallucination-marker receipt, in prompt form). Generator prompts
    # (ideator, builder, writers) stay writable; judge changes ride the
    # PR path like reward.py changes do.
    ".claude/agents/*-judge.md",
    ".claude/agents/*-lens.md",
    ".claude/agents/bob-fresh-reader.md",
    ".claude/agents/bob-table-player.md",
    ".claude/agents/bob-table-breaker.md",
]

# The only arms allowed to carry lane='edition' (which skips the sim
# gates — reward.hard_gates forces g2/g3 True for editions). Pinned HERE,
# in the auditor, because corpus/DIRECTIONS.json is improver-writable:
# a drifting improve session must not be able to grant gate-skipping to
# an invention arm by editing a doc-tier file. classic-reborn earned the
# lane with 2 real pre-Bob sales (the 2030 SF chess + xiangqi sets).
EDITION_ARMS = frozenset(["classic-reborn"])

HEARTBEAT_STALE_HOURS = 6.0   # launchd ticks every 30 min; 6h = 12 missed
                              # ticks — that is a dead daemon, not a busy one
DIVERGENCE_MIN_N = 5          # Pearson on fewer pairs is noise, not signal
DIVERGENCE_MIN_R = 0.3        # below this the LLM tables aren't predicting
                              # humans; rubric gets edited via PR, never scores

_BASELINE_WARNING = (
    "WARNING: this file seals harness/reward.py and docs/REWARD.md. "
    "Only a HUMAN commit may regenerate it (regenerate_baseline() with "
    "BOB_HUMAN=1, run by a person, after reviewing the reward diff). "
    "No agent, loop, or automation may touch it — an evaluator that can "
    "re-seal itself is not sealed (DGM receipt)."
)


def _home():
    # Env read inside functions only (CONTRACTS §6).
    return os.environ.get("BOB_HOME") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))


def _baseline_path():
    return os.path.join(_home(), "state", "REWARD_BASELINE.json")


def _pinned_files():
    home = _home()
    return {
        "harness/reward.py": os.path.join(home, "harness", "reward.py"),
        "docs/REWARD.md": os.path.join(home, "docs", "REWARD.md"),
    }


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _atomic_write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _current_hashes():
    hashes = {}
    missing = []
    for rel, path in _pinned_files().items():
        if os.path.exists(path):
            hashes[rel] = _sha256(path)
        else:
            missing.append(rel)
    return hashes, missing


def _write_baseline():
    hashes, missing = _current_hashes()
    if missing:
        raise FileNotFoundError(
            "Cannot pin reward baseline: missing %s under BOB_HOME=%s. "
            "Fix BOB_HOME or restore the file(s)." % (missing, _home()))
    _atomic_write_json(_baseline_path(), {
        "warning": _BASELINE_WARNING,
        "created": datetime.now(timezone.utc).isoformat(),
        "hashes": hashes,
    })
    return hashes


def regenerate_baseline():
    """Re-pin the reward hashes. HUMAN-ONLY: requires env BOB_HUMAN=1.

    The guard is deliberately an env var a human exports in their own
    shell, not a flag an agent can pass: the loops never run with
    BOB_HUMAN set, so an agent that calls this inside the harness gets
    a refusal with instructions instead of a new seal.
    """
    if os.environ.get("BOB_HUMAN") != "1":
        raise PermissionError(
            "regenerate_baseline() is human-only. If you are a person who "
            "just reviewed and merged a reward change, run: "
            "BOB_HUMAN=1 python3 -c \"from harness import integrity; "
            "integrity.regenerate_baseline()\". If you are an agent: stop — "
            "propose the reward change as a PR instead.")
    return _write_baseline()


def improve_write_allowed(relpath):
    """True iff the improve loop may write this repo-relative path.

    A path must match some IMPROVE_MAY_WRITE glob AND no FORBIDDEN glob.
    '**' is handled as 'this directory and everything under it'.
    Enforced by loops/meta.py before any write is applied.

    Normalization happens HERE, not in callers: this function is the
    exported write-authority contract, and a caller-side-only guard let
    'corpus/../harness/reward.py' match corpus/** by pure string prefix
    — a traversal straight through the judge and its seal. Never rely
    on every caller pre-normalizing.
    """
    rel = str(relpath).replace(os.sep, "/")
    # Strip a leading "./" without eating dotfile names like .claude/
    # (str.lstrip strips CHARACTERS, not a prefix — that bug would have
    # denied the improve loop its own prompt files).
    while rel.startswith("./"):
        rel = rel[2:]
    # Absolute paths and home-dir shorthand are never repo-relative
    # writes; refuse before normalizing.
    if posixpath.isabs(rel) or rel.startswith("~"):
        return False
    rel = posixpath.normpath(rel)
    # Any '..' surviving normpath escapes the repo root entirely.
    if any(part == ".." for part in rel.split("/")):
        return False

    def matches(pattern):
        if pattern.endswith("/**"):
            root = pattern[:-3]
            return rel == root or rel.startswith(root + "/")
        # fnmatch's * already crosses '/' — acceptable for the doc-tier
        # patterns above, which are either exact files or one dir deep.
        return fnmatch.fnmatch(rel, pattern)

    if any(matches(p) for p in FORBIDDEN):
        return False
    return any(matches(p) for p in IMPROVE_MAY_WRITE)


def _pearson(xs, ys):
    """Pearson r, stdlib only. None when undefined (zero variance)."""
    n = len(xs)
    if n < 2 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0.0 or vy == 0.0:
        return None
    return cov / math.sqrt(vx * vy)


def _check_reward_frozen(violations):
    baseline_path = _baseline_path()
    if not os.path.exists(baseline_path):
        # A missing seal mid-flight is an ATTACK SIGNATURE, not a first
        # run: rm the baseline + edit reward.py and a silent re-pin would
        # bless the tampered judge (the exact METR reward-hack this file
        # exists to stop). state/QUEUE.json is the first-run tell — it
        # exists from the first tick onward, so its presence proves the
        # factory has run before and the seal was deleted.
        if os.path.exists(os.path.join(_home(), "state", "QUEUE.json")):
            violations.append(
                "reward-baseline: %s — baseline missing — a human must "
                "re-pin with BOB_HUMAN=1 regenerate_baseline() after "
                "reviewing harness/reward.py and docs/REWARD.md against "
                "git. All ticks halt until then." % baseline_path)
            return
        # Genuinely first run (no QUEUE.json yet): pin what exists NOW.
        # Creating (not failing) here is deliberate — the seal must exist
        # before it can protect anything, and first-run happens on the
        # human's install, not mid-flight.
        try:
            _write_baseline()
        except (OSError, FileNotFoundError) as e:
            violations.append(
                "reward-baseline: could not create %s (%s). Fix the path "
                "problem, then rerun `bob audit`." % (baseline_path, e))
        return
    try:
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = json.load(f)
        pinned = baseline.get("hashes", {})
    except ValueError:
        violations.append(
            "reward-baseline: %s is not valid JSON. A human must inspect "
            "it and regenerate with BOB_HUMAN=1 regenerate_baseline()."
            % baseline_path)
        return
    current, missing = _current_hashes()
    for rel in missing:
        violations.append(
            "reward-freeze: %s is MISSING under BOB_HOME=%s. Restore it "
            "from git; all ticks halt until it is back." % (rel, _home()))
    for rel, want in sorted(pinned.items()):
        got = current.get(rel)
        if got is not None and got != want:
            violations.append(
                "reward-freeze: %s hash drifted (pinned %s…, found %s…). "
                "The reward function is frozen — revert the change, or a "
                "HUMAN reviews it and re-pins with BOB_HUMAN=1 "
                "regenerate_baseline(). All ticks halt until then."
                % (rel, want[:12], got[:12]))
    for rel in _pinned_files():
        if rel not in pinned:
            violations.append(
                "reward-baseline: %s has no pinned hash for %s. A human "
                "must regenerate the baseline (BOB_HUMAN=1)."
                % (baseline_path, rel))


def _check_allowlist(violations):
    # Self-consistency: the seal on the judge must actually be excluded
    # from the improver's write authority. Belt for meta.py's suspenders.
    for probe in ("harness/reward.py", "harness/integrity.py",
                  "knowledge/TASTE.md", "state/REWARD_BASELINE.json",
                  "state/BANDIT.json", "state/QUEUE.json"):
        if improve_write_allowed(probe):
            violations.append(
                "improve-allowlist: %r is writable by the improve loop — "
                "IMPROVE_MAY_WRITE/FORBIDDEN have been tampered with. "
                "Restore harness/integrity.py from git." % probe)


def _check_edition_lanes(violations):
    # lane='edition' skips the sim gates (reward.hard_gates forces
    # g2_sim_integrity/g3_degeneracy True), and DIRECTIONS.json is
    # improver-writable — so the set of edition arms is pinned here in
    # the auditor (EDITION_ARMS), out of the improver's reach. Any other
    # arm claiming the lane is gate-erosion, not configuration.
    path = os.path.join(_home(), "corpus", "DIRECTIONS.json")
    if not os.path.exists(path):
        return  # no corpus, no lanes to grant
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except ValueError:
        return  # corrupt corpus can't grant lanes; bandit alarms elsewhere
    arms = data.get("arms")
    if not isinstance(arms, dict):
        return
    for arm_id, spec in sorted(arms.items()):
        lane = spec.get("lane") if isinstance(spec, dict) else None
        if lane == "edition" and arm_id not in EDITION_ARMS:
            violations.append(
                "edition-lane: arm %r has lane='edition' in "
                "corpus/DIRECTIONS.json but is not in the pinned set %s — "
                "that lane skips the sim gates. Revert the corpus edit; "
                "adding an edition arm means changing EDITION_ARMS in "
                "harness/integrity.py via PR." % (arm_id, sorted(EDITION_ARMS)))


def _check_heartbeat(violations):
    path = os.path.join(_home(), "state", "DAYBOOK.json")
    if not os.path.exists(path):
        return  # pre-first-tick install: nothing to be stale yet
    try:
        with open(path, "r", encoding="utf-8") as f:
            daybook = json.load(f)
    except ValueError:
        violations.append(
            "heartbeat: state/DAYBOOK.json is not valid JSON — the tick "
            "loop cannot record liveness. Restore or delete it.")
        return
    hb = daybook.get("heartbeat")
    if not hb:
        return  # daybook exists but no tick has stamped it yet
    try:
        ts = datetime.fromisoformat(str(hb).replace("Z", "+00:00"))
    except ValueError:
        violations.append(
            "heartbeat: unparseable timestamp %r in DAYBOOK.json — fix or "
            "delete the 'heartbeat' key." % hb)
        return
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600.0
    if age_h > HEARTBEAT_STALE_HOURS:
        violations.append(
            "heartbeat: last tick %.1fh ago (limit %.0fh) — the daemon is "
            "dead or wedged. Check `bob daemon status` and launchd logs. "
            "(Silent-channel deaths must alarm: text2cad blackout receipt.)"
            % (age_h, HEARTBEAT_STALE_HOURS))


def _check_divergence(violations):
    # Pair, per slug, the fun_table component the LLM tables produced at
    # publish with the human_table score that later came back. If the
    # sim-side judge stops tracking humans, its gate verdicts are noise.
    try:
        all_rows = ledger.rows()
    except Exception as e:  # a broken ledger is its own violation
        violations.append(
            "divergence: could not read reward ledger (%s). Fix the ledger "
            "before trusting any scores." % e)
        return
    publish_ft = {}
    human_scores = {}
    for row in all_rows:
        slug = row.get("slug")
        if not slug:
            continue
        if row.get("kind") == "publish":
            comps = row.get("components") or {}
            if "fun_table" in comps:
                try:
                    publish_ft[slug] = float(comps["fun_table"])
                except (TypeError, ValueError):
                    pass
        elif row.get("kind") == "human_table":
            try:
                human_scores.setdefault(slug, []).append(float(row.get("score", 0.0)))
            except (TypeError, ValueError):
                pass
    xs, ys = [], []
    for slug, ft in publish_ft.items():
        if slug in human_scores:
            xs.append(ft)
            ys.append(sum(human_scores[slug]) / len(human_scores[slug]))
    if len(xs) < DIVERGENCE_MIN_N:
        return  # not enough paired evidence to accuse the judge
    r = _pearson(xs, ys)
    if r is None:
        violations.append(
            "divergence: sim-vs-human correlation undefined over %d pairs "
            "(zero variance — a judge scoring every game the same is not "
            "judging). Audit the fun_table rubric via PR." % len(xs))
    elif r < DIVERGENCE_MIN_R:
        violations.append(
            "divergence: sim fun_table vs human_table Pearson r=%.2f over "
            "%d pairs (floor %.1f) — the LLM tables no longer predict "
            "humans. Edit the rubric via PR (never the scores) and "
            "re-run the anchors." % (r, len(xs), DIVERGENCE_MIN_R))


def audit():
    """Run all integrity checks; return a list of violation strings.

    Empty list = clean. Any entry halts the tick loop (CONTRACTS §3:
    audit() clean is the FIRST tick precondition). Each message says
    what to do next — never a bare traceback (CONTRACTS §6).
    """
    violations = []
    _check_reward_frozen(violations)
    _check_allowlist(violations)
    _check_edition_lanes(violations)
    _check_heartbeat(violations)
    _check_divergence(violations)
    return violations
