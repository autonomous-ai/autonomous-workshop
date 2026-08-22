"""Empirical fun instruments — code, not agents, plays the game.

This module is the L1 "simulated" gate's measurement kit: given an engine
module that obeys the contract documented in ``loops/playtest.py``, it plays
thousands of scripted playouts and computes the metrics that the reward
cascade treats as hard floors and soft aesthetics:

- The GAVEL five (Todd et al., NeurIPS 2024, arXiv:2407.09388): balance,
  decisiveness, completion, agency, coverage — combined by HARMONIC mean so
  one bad dimension tanks the score (that asymmetry is the point: a game
  that never ends is not "average", it is broken).
- The Browne aesthetic tier (LUDI, QUT PhD 2008 — the lineage that produced
  Yavalath, the only computer-invented game commercially published): lead
  changes, drama (winner-was-behind), late uncertainty, killer-move
  scarcity, duration distribution.
- The policy ladder (Relative Algorithm Performance Profiles, Nielsen et
  al. 2015): random < greedy < lookahead1 must form a monotone staircase
  with real gaps, else the game is noise (no skill) or shallow (solved by
  myopia). Deep Claim — vibe-ideas' dead game — died of exactly the seat
  bias this file measures.

Everything here is deterministic under ``seed`` and pure stdlib. No LLM is
in the loop: "an LLM running this loop can play a turn for a player who is
slow... here they are not prohibited, they are absent" (vibe-ideas §1.5).
The LLM table lives one gate later and answers a different question.
"""

import math
import os
import random
import time

# --- Gate thresholds --------------------------------------------------------
# UNCALIBRATED — n=2 ground truth. These numbers come from vibe-ideas'
# playtest.py, where they were tuned to separate exactly two data points
# (Millbind, which played fine, from Deep Claim, which the owner killed as
# first-player-solved). "A threshold that cannot separate [Millbind from
# Deep Claim] is not a threshold, it is decoration." Recalibrate from the
# reward ledger as real games accumulate; tighten freely, loosen only by PR
# (thresholds are code-tier — an agent that can lower its own bar does not
# have a bar).

#: Each ladder rung must beat the rung below by at least this much over the
#: chance baseline (1/n_players). Below it the game has no skill gradient.
MIN_SKILL_EDGE = 0.15

#: Max allowed seat winrate spread (max - min) in mirror self-play at the
#: strongest rung. 0.10 encodes the 45-55% band from the research doc
#: (chess White ~54-56%; beyond that real games reach for komi/pie rule).
#: "The one that Deep Claim died of" — vibe-ideas receipt.
MAX_SEAT_EDGE = 0.10

#: No seat may win >= this share of mirror self-play games — first-mover
#: runaway (CONTRACTS G3: "no policy wins >=85% from seat 1").
MAX_RUNAWAY = 0.85

#: Max share of turns with <= 1 legal move. Forced-move chains are dead
#: time (Sid Meier: "a game is a series of interesting decisions").
MAX_FORCED_FRACTION = 0.25

#: Median legal-move count floor. Below 3 options a "choice" is a coin the
#: player did not even get to flip.
MIN_MEDIAN_BRANCHING = 3.0

#: GAVEL floors for the two remaining measurable dimensions. Research doc
#: §2.2: draws < 5-10% for 2p abstracts; completion ~100% within move cap.
MIN_DECISIVENESS = 0.90
MIN_COMPLETION = 0.98

# --- Mechanics constants ----------------------------------------------------

#: Move cap = 4x the median random-playout length (task spec / G2: "500
#: seeded games terminate under 4x target_length"). The probe batch below
#: estimates the median first because we cannot know it a priori.
MOVE_CAP_MULT = 4

#: Probe batch size + absolute cap for the median-length estimate. 200 is
#: enough for a median (it is robust); 4000 moves is "this game does not
#: end" for anything in Bob's 15-50 minute design band.
PROBE_GAMES = 200
PROBE_MOVE_CAP = 4000

#: Never let the derived cap collapse below this — a 2-move median (broken
#: probe) must not truncate every real game into "incomplete".
MIN_MOVE_CAP = 12

#: Probe completion below this short-circuits the whole battery: with few
#: or zero probe terminations the derived cap balloons toward
#: 4x PROBE_MOVE_CAP = 16,000 moves and the 1,000-game main batch plus the
#: lookahead ladder would grind for hours on a game the gate will fail on
#: completion anyway (review 2026-08-22: a never-terminating engine wedged
#: the tick behind 16M applies). Half is generous — the real gate needs
#: MIN_COMPLETION = 0.98 — so nothing that could pass is ever skipped.
PROBE_MIN_COMPLETION = 0.5

#: Games shorter than this fraction of the median are "false starts" —
#: endings that feel accidental (Browne's duration criterion).
FALSE_START_FRACTION = 0.25

#: Terminal-state bonus in policy evaluation. A move that wins IS the
#: maximal score delta in spirit; without this a greedy policy walks past
#: checkmate to grab a point. Large enough to dominate any score scale.
WIN_BONUS = 1e6

#: Ladder matchups use fewer games than the headline batch (they exist to
#: rank policies, not to estimate tail behavior); mirrors get more because
#: the seat-bias gate needs tighter error bars than a ranking does.
MIN_LADDER_GAMES = 60


# --- Policies ----------------------------------------------------------------

def _policy_random(engine, state, me, legal, rng):
    """The floor of the ladder: if this ties the top rung, the game is dice."""
    return legal[rng.randrange(len(legal))]


def _terminal_adjust(engine, state, me, value):
    """Add the win/loss bonus when a state is terminal (shared wins count less)."""
    if engine.is_over(state):
        winners = engine.winners(state)
        if winners:
            if me in winners:
                value += WIN_BONUS / len(winners)
            else:
                value -= WIN_BONUS
    return value


def _eval(engine, state, me):
    """Positional value for `me`: my score minus the best opponent score.

    Margin (not raw score) so 'ahead' means ahead of the field, which is what
    winning is in a multiplayer race. Terminal states add WIN_BONUS.
    """
    sc = engine.scores(state)
    others = [v for i, v in enumerate(sc) if i != me]
    value = sc[me] - (max(others) if others else 0.0)
    return _terminal_adjust(engine, state, me, value)


def _argmax_random_tiebreak(pairs, rng):
    """pairs = [(value, move)]; random tiebreak so mirror matches don't collapse
    into one replayed game (a deterministic policy in a deterministic engine
    would make every mirror playout identical — no distribution, no metrics)."""
    best = max(v for v, _ in pairs)
    ties = [m for v, m in pairs if v == best]
    return ties[rng.randrange(len(ties))]


def _policy_greedy(engine, state, me, legal, rng):
    """1-ply argmax over own score delta (task spec), win-aware, random tiebreak."""
    before = engine.scores(state)[me]
    pairs = []
    for move in legal:
        nxt = engine.apply(state, move)
        value = engine.scores(nxt)[me] - before
        value = _terminal_adjust(engine, nxt, me, value)
        pairs.append((value, move))
    return _argmax_random_tiebreak(pairs, rng)


def _policy_lookahead1(engine, state, me, legal, rng):
    """2-ply minimax on scores: my move, then the next player's best reply
    (they maximize their own eval); among their tied-best replies assume the
    one worst for me (paranoid minimax — the honest 2-ply assumption).
    """
    pairs = []
    for move in legal:
        s1 = engine.apply(state, move)
        if engine.is_over(s1):
            pairs.append((_eval(engine, s1, me), move))
            continue
        opp = engine.player_to_move(s1)
        reply_legal = engine.legal_moves(s1)
        if not reply_legal:
            pairs.append((_eval(engine, s1, me), move))
            continue
        best_opp = None
        best_states = []
        for reply in reply_legal:
            s2 = engine.apply(s1, reply)
            ov = _eval(engine, s2, opp)
            if best_opp is None or ov > best_opp:
                best_opp = ov
                best_states = [s2]
            elif ov == best_opp:
                best_states.append(s2)
        value = min(_eval(engine, s2, me) for s2 in best_states)
        pairs.append((value, move))
    return _argmax_random_tiebreak(pairs, rng)


POLICIES = {
    "random": _policy_random,
    "greedy": _policy_greedy,
    "lookahead1": _policy_lookahead1,
}


# --- Playout machinery --------------------------------------------------------

def _play_one(engine, n_players, seat_policies, move_cap, game_seed, trace):
    """Play one game; seat_policies[i] is the policy NAME for seat i.

    Returns a dict with length, terminated, winners, branching counts, and
    (when trace=True) the per-move scores trace the Browne tier needs.
    """
    # One rng per game, derived from the game seed, so a batch is
    # order-independent and reproducible game-by-game.
    rng = random.Random((game_seed * 0x9E3779B9) & 0xFFFFFFFF)
    state = engine.new_game(n_players, game_seed)
    branchings = []
    scores_trace = []
    movers = []
    moves = 0
    deadlock = False
    while not engine.is_over(state) and moves < move_cap:
        mover = engine.player_to_move(state)
        legal = engine.legal_moves(state)
        if not legal:
            # Deadlock: not-over but no moves. A broken engine/game, counted
            # against completion rather than crashing the instrument (G2
            # measures "no crash"; the gate wants a number, not a traceback).
            deadlock = True
            break
        branchings.append(len(legal))
        move = POLICIES[seat_policies[mover]](engine, state, mover, legal, rng)
        state = engine.apply(state, move)
        moves += 1
        if trace:
            movers.append(mover)
            scores_trace.append(list(engine.scores(state)))
    terminated = bool(engine.is_over(state))
    winners = list(engine.winners(state)) if terminated else []
    return {
        "length": moves,
        "terminated": terminated,
        "deadlock": deadlock,
        "winners": winners,
        "branchings": branchings,
        "scores_trace": scores_trace if trace else None,
    }


def _game_seed(seed, salt, index):
    """Stable per-game seed: master seed x salt x index, no shared rng stream."""
    return (seed * 1000003 + salt * 7919 + index) & 0x7FFFFFFF


class SimWallExceeded(Exception):
    """The battery blew its wall-clock budget — a finding, not a wait.

    g0002 'Re-Pin' burned 46 CPU-minutes in one simulate() call
    (2026-08-23): a lookahead mirror over a branchy engine is O(b^2) per
    move and nothing bounded the total. A game whose OWN playtest harness
    needs an hour is too branchy to certify — fail it and say why."""


def _check_wall(deadline):
    if deadline is not None and time.monotonic() > deadline:
        raise SimWallExceeded(
            "sim wall budget exceeded (BOB_SIM_WALL_MINUTES, default 20) — "
            "the engine is too slow/branchy for its own battery")


def _batch(engine, n_players, seat_policies, count, move_cap, seed, salt,
           trace, deadline=None):
    games = []
    for i in range(count):
        if i % 10 == 0:
            _check_wall(deadline)
        games.append(_play_one(engine, n_players, seat_policies, move_cap,
                               _game_seed(seed, salt, i), trace))
    return games


def _median(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _seat_winrates(games, n_players):
    """Fractional credit for shared wins (1/len(winners)) so rates stay
    comparable across draw-heavy and draw-free games; truncated games earn
    nobody credit (completion is the metric that punishes those)."""
    credit = [0.0] * n_players
    for g in games:
        if g["winners"]:
            share = 1.0 / len(g["winners"])
            for w in g["winners"]:
                if 0 <= w < n_players:
                    credit[w] += share
    total = float(len(games)) or 1.0
    return [c / total for c in credit]


def _harmonic_mean(values):
    """None-safe harmonic mean: Nones (unmeasurable dimensions, e.g. coverage
    on a boardless engine) are skipped, not zeroed — skipping is honest,
    zeroing would fail every card game for not having a board. Any measured
    zero still tanks the whole mean (the GAVEL property we want)."""
    present = [v for v in values if v is not None]
    if not present:
        return None
    if any(v <= 0.0 for v in present):
        return 0.0
    return len(present) / sum(1.0 / v for v in present)


# --- Browne trace metrics -------------------------------------------------------

def _leader(scores):
    """Index of the unique max scorer, else None (a tied lead is no lead)."""
    top = max(scores)
    leads = [i for i, v in enumerate(scores) if v == top]
    return leads[0] if len(leads) == 1 else None


def _browne_tier(games):
    """Lead changes / drama / late uncertainty / killer scarcity / duration —
    Browne's human-predictive criteria (the 57->17 experiment), computed from
    the scores() trace of the main random batch. Random self-play is the
    cheapest honest sampler of the game's state space; the numbers are
    reported (soft aesthetics), not gated — only the GAVEL floors gate."""
    lead_change_counts = []
    late_positions = []
    drama_hits = 0
    drama_eligible = 0
    total_changes = 0
    total_moves = 0
    lengths = [g["length"] for g in games if g["terminated"]]

    for g in games:
        trace = g["scores_trace"]
        if not trace:
            continue
        leaders = [_leader(s) for s in trace]
        changes = 0
        last_change_at = None
        prev = None
        for t, led in enumerate(leaders):
            if led is None:
                continue
            if prev is not None and led != prev:
                changes += 1
                last_change_at = t
            prev = led
        lead_change_counts.append(changes)
        total_changes += changes
        total_moves += len(trace)
        if changes and len(trace) > 1:
            late_positions.append(last_change_at / float(len(trace) - 1))
        else:
            late_positions.append(0.0)
        # Drama: the eventual (sole) winner was strictly behind someone at
        # some earlier point — Browne: winner "suffers a negative lead".
        if g["terminated"] and len(g["winners"]) == 1:
            drama_eligible += 1
            w = g["winners"][0]
            for s in trace[:-1]:
                if s[w] < max(s):
                    drama_hits += 1
                    break

    med = _median(lengths)
    mean_len = (sum(lengths) / float(len(lengths))) if lengths else 0.0
    if lengths and mean_len > 0:
        var = sum((x - mean_len) ** 2 for x in lengths) / float(len(lengths))
        cv = math.sqrt(var) / mean_len
    else:
        cv = 0.0
    false_floor = FALSE_START_FRACTION * med
    false_starts = [x for x in lengths if x < false_floor]

    killer_rate = (total_changes / float(total_moves)) if total_moves else 0.0
    return {
        "lead_changes_mean": (sum(lead_change_counts) / float(len(lead_change_counts))) if lead_change_counts else 0.0,
        "drama": (drama_hits / float(drama_eligible)) if drama_eligible else 0.0,
        "late_uncertainty": (sum(late_positions) / float(len(late_positions))) if late_positions else 0.0,
        # Scarcity, not absence: healthy games HAVE killer moves but few of
        # them — a lead that flips every turn is chaos, not drama (Browne).
        # Proxy: 1 - (lead flips per move).
        "killer_scarcity": max(0.0, 1.0 - killer_rate),
        "duration": {
            "median": med,
            "cv": cv,
            "false_start_share": (len(false_starts) / float(len(lengths))) if lengths else 0.0,
        },
    }


# --- The instrument ---------------------------------------------------------------

def _short_circuit_report(n_players, n_games, seed, move_cap, probe_median,
                          probe_completion, ladder):
    """The failing SimReport for a game whose probe (mostly) never ends.

    Shape-compatible with a full report — every field a consumer reads
    exists (verdicts full set, gavel.harmonic_mean, ladder.edges, move_cap)
    — but every verdict is False and every unmeasured metric is None/empty:
    fail-closed, an absent measurement is never a pass.
    """
    gavel = {
        "balance": None,
        "decisiveness": None,
        "completion": probe_completion,  # the one thing the probe measured
        "agency": None,
        "coverage": None,
        "harmonic_mean": None,
    }
    verdicts = {
        "balance_ok": False,
        "decisiveness_ok": False,
        "completion_ok": False,
        "seat_bias_ok": False,
        "skill_ladder_ok": False,
        "runaway_ok": False,
        "forced_ok": False,
        "branching_ok": False,
        "all_pass": False,
    }
    return {
        "n_players": n_players,
        "n_games": n_games,
        "seed": seed,
        "move_cap": move_cap,
        "probe_median_length": probe_median,
        "probe_completion": probe_completion,
        "gavel": gavel,
        "browne": {},
        "seat_winrates_random": [],
        "branching": {"median": None, "forced_fraction": None},
        "ladder": {
            "policies": list(ladder),
            "matrix": {},
            "edges": {},
            "baseline": 1.0 / n_players,
            "mirror_seat_winrates": {},
            "strongest_rung": ladder[-1],
            "strongest_seat_spread": None,
            "runaway_max_seat_winrate": None,
        },
        "thresholds": thresholds(),
        "verdicts": verdicts,
        "notes": {
            "short_circuit": (
                "probe completion %.2f < PROBE_MIN_COMPLETION %.2f — the "
                "main battery and ladder were skipped (they would run for "
                "hours at a %d-move cap and fail on completion anyway); "
                "every verdict is a fail-closed False"
                % (probe_completion, PROBE_MIN_COMPLETION, move_cap)),
        },
    }


def simulate(engine, n_players, n_games=1000, seed=0,
             policies=("random", "greedy", "lookahead1")):
    """Run the full measurement battery. Returns a SimReport dict.

    ``policies`` is ordered weakest -> strongest; that order IS the ladder
    the monotone-staircase check runs over. Deterministic under ``seed``.
    """
    for name in policies:
        if name not in POLICIES:
            raise ValueError(
                "unknown policy %r — pick from %s (add new rungs to "
                "simmetrics.POLICIES, they must be pure functions)"
                % (name, sorted(POLICIES)))
    if n_players < 1:
        raise ValueError("n_players must be >= 1")
    ladder = list(policies)
    baseline = 1.0 / n_players
    deadline = time.monotonic() + 60.0 * float(
        os.environ.get("BOB_SIM_WALL_MINUTES", "20"))

    # 1. Probe: estimate median random-playout length to set the move cap
    #    (cap = 4x median, G2). The probe runs under an absolute lid so a
    #    never-ending game costs bounded time, not the whole tick.
    probe = _batch(engine, n_players, ["random"] * n_players,
                   min(PROBE_GAMES, n_games), PROBE_MOVE_CAP, seed, 1, False,
                   deadline=deadline)
    probe_lengths = [g["length"] for g in probe if g["terminated"]]
    probe_median = _median(probe_lengths) if probe_lengths else PROBE_MOVE_CAP
    move_cap = max(MIN_MOVE_CAP, int(math.ceil(MOVE_CAP_MULT * probe_median)))

    # Short-circuit: a probe that (mostly) never terminates already IS the
    # verdict — completion fails at the gate no matter what the battery
    # says, and running it would cost hours at a 16k-move cap. Emit the
    # failing report now; every unmeasured verdict stays False (fail-closed:
    # an absent measurement is never a pass).
    probe_completion = (len(probe_lengths) / float(len(probe))) if probe else 0.0
    if probe_completion < PROBE_MIN_COMPLETION:
        return _short_circuit_report(
            n_players, n_games, seed, move_cap, probe_median,
            probe_completion, ladder)

    # 2. Main batch: random mirror self-play with score traces. This is the
    #    GAVEL + Browne sampler (LUDI measured its criteria on self-play).
    main = _batch(engine, n_players, ["random"] * n_players,
                  n_games, move_cap, seed, 2, True, deadline=deadline)

    terminated = [g for g in main if g["terminated"]]
    completion = len(terminated) / float(len(main)) if main else 0.0
    decisive = [g for g in terminated if len(g["winners"]) == 1]
    decisiveness = (len(decisive) / float(len(terminated))) if terminated else 0.0

    all_branchings = []
    for g in main:
        all_branchings.extend(g["branchings"])
    turns = len(all_branchings)
    agency = (sum(1 for b in all_branchings if b > 1) / float(turns)) if turns else 0.0
    forced_fraction = 1.0 - agency
    median_branching = _median(all_branchings)

    seat_rates_random = _seat_winrates(main, n_players)
    random_spread = (max(seat_rates_random) - min(seat_rates_random)) if seat_rates_random else 0.0

    gavel = {
        "balance": max(0.0, 1.0 - random_spread),
        "decisiveness": decisiveness,
        "completion": completion,
        "agency": agency,
        # Coverage needs a board/site enumeration the engine contract does
        # not expose (new_game..observation only). None = "not measured",
        # skipped by the None-safe harmonic mean; add when engines grow a
        # sites() call. Documented, not silently 1.0 — an absent metric is
        # not a passing one.
        "coverage": None,
    }
    gavel["harmonic_mean"] = _harmonic_mean(
        [gavel["balance"], gavel["decisiveness"], gavel["completion"],
         gavel["agency"], gavel["coverage"]])

    browne = _browne_tier(main)

    # 3. Policy ladder: every ordered pair (challenger a in a field of b),
    #    challenger seat rotating so seat advantage cancels out of the SKILL
    #    number (seat advantage gets its own gate below).
    n_ladder = max(MIN_LADDER_GAMES, n_games // 5)
    n_ladder += (-n_ladder) % n_players  # multiple of n_players: even rotation
    matrix = {}
    salt = 3
    for a in ladder:
        matrix[a] = {}
        for b in ladder:
            if a == b:
                continue
            credit = 0.0
            for i in range(n_ladder):
                seat = i % n_players
                seats = [b] * n_players
                seats[seat] = a
                g = _play_one(engine, n_players, seats, move_cap,
                              _game_seed(seed, salt, i), False)
                if g["winners"] and seat in g["winners"]:
                    credit += 1.0 / len(g["winners"])
            matrix[a][b] = credit / float(n_ladder)
            salt += 1

    edges = {}
    staircase_ok = True
    for k in range(1, len(ladder)):
        strong, weak = ladder[k], ladder[k - 1]
        edge = matrix[strong][weak] - baseline
        edges["%s>%s" % (strong, weak)] = edge
        if edge < MIN_SKILL_EDGE:
            staircase_ok = False
    if len(ladder) >= 3:
        # The whole chain must hold end to end, not just link by link.
        top_edge = matrix[ladder[-1]][ladder[0]] - baseline
        edges["%s>%s" % (ladder[-1], ladder[0])] = top_edge
        if top_edge < MIN_SKILL_EDGE:
            staircase_ok = False

    # 4. Mirrors at every rung: seat winrates under identical policies is the
    #    clean read on seat advantage (any skill signal cancels). Strongest
    #    rung carries the seat-bias gate; every rung feeds the runaway gate.
    n_mirror = max(MIN_LADDER_GAMES, n_games // 2)
    mirror_rates = {"random": seat_rates_random}  # reuse the main batch
    for k, name in enumerate(ladder):
        if name == "random":
            continue
        games = _batch(engine, n_players, [name] * n_players,
                       n_mirror, move_cap, seed, 100 + k, False, deadline=deadline)
        mirror_rates[name] = _seat_winrates(games, n_players)

    strongest = ladder[-1]
    strongest_rates = mirror_rates.get(strongest, seat_rates_random)
    strongest_spread = (max(strongest_rates) - min(strongest_rates)) if strongest_rates else 0.0
    runaway_max = max((max(rates) if rates else 0.0)
                      for rates in mirror_rates.values())

    verdicts = {
        # GAVEL floors (hard gates)
        "balance_ok": random_spread <= MAX_SEAT_EDGE,
        "decisiveness_ok": decisiveness >= MIN_DECISIVENESS,
        "completion_ok": completion >= MIN_COMPLETION,
        # Ladder / vibe-ideas gates
        "seat_bias_ok": strongest_spread <= MAX_SEAT_EDGE,
        "skill_ladder_ok": staircase_ok,
        "runaway_ok": runaway_max < MAX_RUNAWAY,
        "forced_ok": forced_fraction <= MAX_FORCED_FRACTION,
        "branching_ok": median_branching >= MIN_MEDIAN_BRANCHING,
    }
    verdicts["all_pass"] = all(verdicts.values())

    return {
        "n_players": n_players,
        "n_games": n_games,
        "seed": seed,
        "move_cap": move_cap,
        "probe_median_length": probe_median,
        "gavel": gavel,
        "browne": browne,
        "seat_winrates_random": seat_rates_random,
        "branching": {
            "median": median_branching,
            "forced_fraction": forced_fraction,
        },
        "ladder": {
            "policies": ladder,
            "matrix": matrix,
            "edges": edges,
            "baseline": baseline,
            "mirror_seat_winrates": mirror_rates,
            "strongest_rung": strongest,
            "strongest_seat_spread": strongest_spread,
            "runaway_max_seat_winrate": runaway_max,
        },
        "thresholds": thresholds(),
        "verdicts": verdicts,
        "notes": {
            "coverage": "skipped: engine contract exposes no board sites; "
                        "None is excluded from the harmonic mean, never "
                        "treated as a pass",
        },
    }


def thresholds():
    """The gate constants, for embedding in reports (judges read artifacts).

    Generators never see this module (METR: reward hacking 43x likelier when
    the model sees the scorer) — reports go to JUDGES and the ledger only.
    """
    return {
        "MIN_SKILL_EDGE": MIN_SKILL_EDGE,
        "MAX_SEAT_EDGE": MAX_SEAT_EDGE,
        "MAX_RUNAWAY": MAX_RUNAWAY,
        "MAX_FORCED_FRACTION": MAX_FORCED_FRACTION,
        "MIN_MEDIAN_BRANCHING": MIN_MEDIAN_BRANCHING,
        "MIN_DECISIVENESS": MIN_DECISIVENESS,
        "MIN_COMPLETION": MIN_COMPLETION,
        "MOVE_CAP_MULT": MOVE_CAP_MULT,
    }
