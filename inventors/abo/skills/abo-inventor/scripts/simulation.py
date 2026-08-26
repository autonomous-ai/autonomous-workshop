"""ABO's seeded simulation: a thousand completed games, or a truthful wait.

This drives the imported harness against the engine bytes *inside the revision
under test*, so every number it reports belongs to those exact bytes and to no
other build. What it measures is the game, never a model's opinion of it:
whether games terminate, whether a seat holds an advantage across a balanced
seat-swapped sample, how many turns offered no real choice, how wide the
decision space is, which declared move kinds were never legal or never chosen,
and whether a stronger policy beats a weaker one by a margin — because a
position where lookahead cannot beat greedy is not deep.

The floor is a thousand *completed* games. A game abandoned at the turn cap, at
the deadline, or by an engine error is reported separately and excluded, and
when the deadline arrives short the round returns a `Need` saying how far it
got. It never passes over a smaller sample and it never quietly extends its own
deadline.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
import math
import traceback
from types import ModuleType
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple



# ---------------------------------------------------------------------------
# The deterministic policy/statistics core.
#
# Inlined verbatim (module-level renames aside) from the upstream-snapshot
# harness/playtest.py at reinSPQR/vibe-ideas@a557cacb3d98e5936194e4ba11721809370195f8,
# whose harness/ tree design decision D7 deletes as orchestration. These
# functions are not orchestration -- they are the pure, seeded game-theoretic
# primitives (scripted policies, batch play, Wilson intervals, sensitivity
# analysis) that this module's own run_simulation needs to be a real
# simulation harness rather than a wrapper around a deleted one. See
# references/UPSTREAM.md.
# ---------------------------------------------------------------------------

# A flipped assumption that moves any headline number by more than this is
# load-bearing, and the rules have to say which reading is meant.
SENSITIVITY_DELTA = 0.10


REQUIRED_CALLS = ("new_game", "player_to_move", "legal_moves", "apply_move",
                  "is_over", "scores", "winners")
REQUIRED_META = ("PLAYERS", "MAX_TURNS", "HIDDEN_INFO")


# ---------------------------------------------------------------------------
# Loading and validating an engine
# ---------------------------------------------------------------------------

class EngineBroken(Exception):
    """The engine is not a usable model of the rules. Not a verdict on the game."""


def load_engine(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"pt_engine_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise EngineBroken(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - any import error is the same problem
        raise EngineBroken(f"{path} failed to import: {exc}") from exc
    return module


def validate_engine(eng: ModuleType) -> list[str]:
    findings = []
    for name in REQUIRED_CALLS:
        if not callable(getattr(eng, name, None)):
            findings.append(f"contract: engine has no callable `{name}`")
    for name in REQUIRED_META:
        if getattr(eng, name, None) is None:
            findings.append(f"contract: engine has no `{name}`")
    players = getattr(eng, "PLAYERS", None)
    if players is not None:
        try:
            lo, hi = int(players[0]), int(players[1])
            if lo < 1 or hi < lo:
                findings.append(f"contract: PLAYERS {players} is not a seat range")
        except (TypeError, ValueError, IndexError):
            findings.append(f"contract: PLAYERS {players!r} is not (min, max)")
    for entry in getattr(eng, "ASSUMPTIONS", []) or []:
        missing = [k for k in ("id", "rule", "question", "chosen", "alternative")
                   if not entry.get(k)]
        if missing:
            findings.append(f"contract: ASSUMPTIONS entry {entry.get('id', '?')} "
                            f"is missing {missing}")
    return findings


def is_undefined(exc: BaseException) -> bool:
    """An engine signals a rules gap with any exception class named Undefined.

    Matched by name rather than by identity so the engine stays a standalone
    file with no import back into this harness: an agent writing one should
    need nothing but `idea.json` and the contract in this docstring.
    """
    return any(cls.__name__ == "Undefined" for cls in type(exc).__mro__)


def move_kind(move) -> str:
    kind = getattr(move, "kind", None)
    if isinstance(kind, str) and kind:
        return kind
    if isinstance(move, (tuple, list)) and move and isinstance(move[0], str):
        return move[0]
    text = str(move)
    return text.split(":")[0].split("(")[0].strip()[:40] or "?"


# ---------------------------------------------------------------------------
# Policies. Each takes (engine, state, seat, rng) and returns one legal move.
# They know nothing about any particular game, which is the point: a heuristic
# tuned per game would measure the heuristic, not the game.
# ---------------------------------------------------------------------------

def _margin(scores: list, seat: int) -> float:
    """Own score minus the best rival's. What every player actually wants."""
    others = [s for i, s in enumerate(scores) if i != seat]
    return float(scores[seat]) - (max(others) if others else 0.0)


def _payoff(eng: ModuleType, state, seat: int) -> float:
    """1 for a win, split for a shared win, 0 for a loss."""
    if not eng.is_over(state):
        return 0.5  # cut short by a cap; treat as a draw rather than a loss
    winners = list(eng.winners(state))
    if not winners:
        return 0.5
    return (1.0 / len(winners)) if seat in winners else 0.0


def pol_random(eng, state, seat, rng, moves):
    return rng.choice(moves)


def pol_first(eng, state, seat, rng, moves):
    """Always the first move offered. A baseline, and an ordering-bias probe."""
    return moves[0]


def unplayable(exc: BaseException) -> bool:
    """A gap a policy walked into while imagining a line, not while playing.

    A policy speculates: greedy applies every candidate to a copy, and the
    lookahead plays whole games out. If one of those imagined lines reaches a
    position the rules do not cover, that is a candidate the policy cannot
    evaluate, and the honest response is to leave it alone. It is emphatically
    NOT the real game reaching a rules gap, and letting it escape means the
    real game dies of something that never happened to it.

    Millbind is what taught this: its crank jam is reachable, so every
    lookahead rollout eventually hit it, and the entire skill ladder recorded
    0 completed games out of 60 while the run reported them as rules gaps in
    play. Any engine with a reachable `Undefined` loses its ladder the same
    way, silently, and the ladder is the strongest measure in this file.
    """
    return is_undefined(exc)


def pol_greedy(eng, state, seat, rng, moves):
    """One ply: the move leaving the best score margin right now.

    Resamples what `seat` cannot see before scoring each candidate, the same
    way `pol_mc` already does. Without this, a hidden-information engine that
    resolves a simultaneous reveal synchronously inside one seat's own move
    (rather than exposing an extra forced "reveal" turn just to dodge this
    policy) hands greedy the true, not-yet-revealed state of every other
    seat's already-fixed choice — an oracle, not a one-ply evaluation. This
    was discovered in an engine whose `reveal_resolve` move existed purely to
    route around this gap; fixing it here is what lets an engine fold that
    kind of bookkeeping turn back into the move that actually causes it.
    """
    determinize = getattr(eng, "determinize", None)
    best, best_val = [], None
    for move in moves:
        try:
            trial = copy.deepcopy(state)
            if determinize is not None:
                trial = determinize(trial, seat, rng)
            after = eng.apply_move(trial, move, rng)
            val = _margin(eng.scores(after), seat)
        except Exception as exc:  # noqa: BLE001
            if not unplayable(exc):
                raise
            continue
        if best_val is None or val > best_val:
            best, best_val = [move], val
        elif val == best_val:
            best.append(move)
    # Every candidate led somewhere the rules do not cover. The policy has no
    # basis to prefer any of them and says so by not pretending to.
    return rng.choice(best) if best else rng.choice(moves)


def make_mc(budget: int, cap: int):
    """Flat Monte Carlo: play each candidate move out at random, many times.

    Deliberately the dumbest strong player there is. It needs no evaluation
    function, so it cannot be tuned to flatter a particular game, and it
    measures exactly the thing in question: does looking ahead help at all?
    """
    def pol_mc(eng, state, seat, rng, moves):
        per_move = max(1, budget // max(1, len(moves)))
        best, best_val = [], None
        for move in moves:
            total = 0.0
            scored = 0
            for _ in range(per_move):
                try:
                    trial = copy.deepcopy(state)
                    determinize = getattr(eng, "determinize", None)
                    if determinize is not None:
                        trial = determinize(trial, seat, rng)
                    trial = eng.apply_move(trial, move, rng)
                    trial, _turns, _stuck = _rollout(eng, trial, rng, cap)
                except Exception as exc:  # noqa: BLE001
                    if not unplayable(exc):
                        raise
                    continue
                total += _payoff(eng, trial, seat)
                scored += 1
            if not scored:
                continue
            val = total / scored
            if best_val is None or val > best_val:
                best, best_val = [move], val
            elif val == best_val:
                best.append(move)
        return rng.choice(best) if best else rng.choice(moves)
    return pol_mc


def _rollout(eng, state, rng, cap: int):
    """Random play to the end. Returns (state, turns played, stuck)."""
    turns = 0
    while turns < cap and not eng.is_over(state):
        moves = eng.legal_moves(state)
        if not moves:
            return state, turns, True
        state = eng.apply_move(state, rng.choice(moves), rng)
        turns += 1
    return state, turns, False


# ---------------------------------------------------------------------------
# One game
# ---------------------------------------------------------------------------

def play_one(eng: ModuleType, seat_policies: list, n_players: int,
             rng: random.Random, cap: int, admin_kinds: frozenset = frozenset()
             ) -> dict:
    """Play a single game. Never raises for a game-level fault; reports it."""
    record = {
        "turns": 0, "natural": False, "stuck": False, "undefined": None,
        "winners": [], "scores": [], "branching": [], "kinds_chosen": [],
        "kinds_legal": set(), "leader_at_half": None,
        "admin_turns": 0, "admin_violations": [],
    }
    try:
        state = eng.new_game(n_players, rng)
        seen: list[list] = []
        while record["turns"] < cap:
            if eng.is_over(state):
                record["natural"] = True
                break
            moves = eng.legal_moves(state)
            kinds_here = [move_kind(m) for m in moves]
            record["kinds_legal"].update(kinds_here)
            # See the ADMIN_KINDS docstring above. A kind proves itself
            # administrative only by always being the sole legal move; the
            # moment it shares a turn with anything else, that turn counts
            # normally and the sharing itself is reported as a broken
            # declaration, not silently absorbed.
            if len(moves) == 1 and kinds_here[0] in admin_kinds:
                record["admin_turns"] += 1
            else:
                record["branching"].append(len(moves))
                bad = admin_kinds.intersection(kinds_here)
                if bad:
                    record["admin_violations"].append(
                        f"contract: ADMIN_KINDS {sorted(bad)} declared as "
                        f"always the sole legal move, but appeared among "
                        f"{len(moves)} legal moves together — it is a real "
                        f"branch sometimes, not administrative")
            if not moves:
                record["stuck"] = True
                break
            seat = int(eng.player_to_move(state))
            move = seat_policies[seat](eng, state, seat, rng, moves)
            record["kinds_chosen"].append(move_kind(move))
            state = eng.apply_move(state, move, rng)
            seen.append(list(eng.scores(state)))
            record["turns"] += 1
    except Exception as exc:  # noqa: BLE001
        if is_undefined(exc):
            record["undefined"] = str(exc)
            return record
        raise EngineBroken(
            f"engine raised {type(exc).__name__}: {exc}\n"
            + "".join(traceback.format_exc(limit=6))) from exc

    record["scores"] = list(eng.scores(state))
    record["winners"] = list(eng.winners(state)) if record["natural"] else []
    if seen:
        half = seen[len(seen) // 2]
        top = max(half)
        leaders = [i for i, s in enumerate(half) if s == top]
        record["leader_at_half"] = leaders[0] if len(leaders) == 1 else None
    return record


# ---------------------------------------------------------------------------
# Batches
# ---------------------------------------------------------------------------

def wilson(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Confidence interval on a win rate. A win rate with no interval on it is
    an anecdote with a decimal point."""
    if total == 0:
        return (0.0, 1.0)
    p = hits / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    spread = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def run_batch(eng, policy_of_seat, n_players: int, games: int, cap: int,
              seed: int, deadline: float, challenger_seat=None) -> dict:
    """`policy_of_seat(seat, game_index)` picks each seat's policy per game, so
    a challenger can be rotated through every seat and never gain or lose from
    where it sat. `challenger_seat(game_index)` says which seat that was, and
    is the only way the challenger's own win rate can be read back out of a
    table where it moved around."""
    rng_master = random.Random(seed)
    challenger_wins = 0.0
    challenger_decided = 0
    wins = [0.0] * n_players
    played = natural = stuck = 0
    turns, branching, margins = [], [], []
    ties = 0
    kinds_chosen: dict[str, int] = {}
    kinds_legal: set = set()
    undefined: list[str] = []
    leader_half_correct = leader_half_seen = 0
    admin_kinds = frozenset(str(k) for k in (getattr(eng, "ADMIN_KINDS", ()) or ()))
    admin_turns = 0
    admin_violations: list[str] = []

    for i in range(games):
        if time.monotonic() > deadline:
            break
        rng = random.Random(rng_master.randrange(1 << 30))
        seats = [policy_of_seat(s, i) for s in range(n_players)]
        rec = play_one(eng, seats, n_players, rng, cap, admin_kinds)
        played += 1
        if rec["undefined"]:
            undefined.append(rec["undefined"])
            continue
        turns.append(rec["turns"])
        branching.extend(rec["branching"])
        admin_turns += rec["admin_turns"]
        admin_violations.extend(rec["admin_violations"])
        kinds_legal |= rec["kinds_legal"]
        for kind in rec["kinds_chosen"]:
            kinds_chosen[kind] = kinds_chosen.get(kind, 0) + 1
        if rec["stuck"]:
            stuck += 1
            continue
        if not rec["natural"]:
            continue
        natural += 1
        if len(rec["winners"]) > 1:
            ties += 1
        for seat in rec["winners"]:
            wins[seat] += 1.0 / len(rec["winners"])
        if challenger_seat is not None:
            mine = challenger_seat(i)
            challenger_decided += 1
            if mine in rec["winners"]:
                challenger_wins += 1.0 / len(rec["winners"])
        if rec["scores"]:
            ordered = sorted(rec["scores"], reverse=True)
            margins.append(ordered[0] - (ordered[1] if len(ordered) > 1 else 0))
        if rec["leader_at_half"] is not None:
            leader_half_seen += 1
            if rec["leader_at_half"] in rec["winners"]:
                leader_half_correct += 1

    return {
        "games_requested": games, "games_played": played,
        "natural_endings": natural, "stuck": stuck,
        "undefined": undefined[:5], "undefined_count": len(undefined),
        "wins": wins,
        "turns_mean": statistics.fmean(turns) if turns else 0.0,
        "turns_median": statistics.median(turns) if turns else 0.0,
        "turns_p90": (sorted(turns)[int(0.9 * (len(turns) - 1))] if turns else 0.0),
        "branching_mean": statistics.fmean(branching) if branching else 0.0,
        "branching_median": statistics.median(branching) if branching else 0.0,
        # The median says whether a turn is interesting; the widest position
        # says whether a seat at this table can answer at all, and they are
        # not close on a game whose first action is its broadest. Millbind
        # runs a median of 53 and a maximum of 118, so a table run reading
        # only the median sails past its own warning and dies on turn seven.
        "branching_p90": (sorted(branching)[int(0.9 * (len(branching) - 1))]
                          if branching else 0.0),
        "branching_max": max(branching) if branching else 0.0,
        "forced_fraction": (sum(1 for b in branching if b <= 1) / len(branching)
                            if branching else 0.0),
        "margin_mean": statistics.fmean(margins) if margins else 0.0,
        "admin_turns": admin_turns,
        "admin_violations": admin_violations,
        "kinds_legal": sorted(kinds_legal),
        "kinds_chosen": kinds_chosen,
        "runaway": (leader_half_correct / leader_half_seen
                    if leader_half_seen else None),
        "ties": ties,
        "tie_rate": (ties / natural) if natural else 0.0,
        "challenger_wins": challenger_wins,
        "challenger_decided": challenger_decided,
    }


def seat_edge(batch: dict, n_players: int) -> dict:
    """How far the luckiest seat sits above its fair share, with the interval."""
    decided = sum(batch["wins"])
    fair = 1.0 / n_players
    rates = [(w / decided if decided else 0.0) for w in batch["wins"]]
    best = max(range(n_players), key=lambda s: rates[s]) if decided else 0
    lo, hi = wilson(int(round(batch["wins"][best])), int(round(decided)))
    return {"fair_share": fair, "win_rates": rates, "best_seat": best,
            "best_rate": rates[best] if decided else 0.0,
            "best_ci": [lo, hi], "decided": decided,
            # The edge is measured on the low end of the interval: a seat is
            # only guilty if even the pessimistic reading puts it ahead.
            "edge": (lo - fair) if decided else 0.0}


def challenge(eng, name: str, challenger, field_name: str, field,
              n_players: int, games: int, cap: int, seed: int,
              deadline: float) -> dict:
    """One policy against a table of another, rotated through every seat.

    Rotation is not politeness. Without it a challenger measured only in seat 0
    reports the seat's advantage as its own skill, and the two things this
    whole file exists to tell apart would be added together.
    """
    def policy_of_seat(seat: int, game: int):
        return challenger if seat == (game % n_players) else field

    batch = run_batch(eng, policy_of_seat, n_players, games, cap, seed,
                      deadline, challenger_seat=lambda game: game % n_players)
    won, decided = batch["challenger_wins"], batch["challenger_decided"]
    rate = (won / decided) if decided else 0.0
    lo, hi = wilson(int(round(won)), decided)
    fair = 1.0 / n_players
    return {"policy": name, "field": field_name, "games": decided,
            "win_rate": rate, "ci": [lo, hi], "fair_share": fair,
            "edge": (lo - fair) if decided else 0.0,
            "kinds_chosen": batch["kinds_chosen"]}


def run_sensitivity(eng, n_players: int, games: int, cap: int, seed: int,
                    deadline: float, policy) -> list:
    """Play each declared assumption both ways and see whether it mattered.

    This is the only cheap way to rank an ambiguity. A rules gap that changes
    nothing measurable can be left for the editor; one that moves the seat bias
    is the game, and the rules have to say which reading is meant.
    """
    assumptions = list(getattr(eng, "ASSUMPTIONS", []) or [])
    if not assumptions:
        return []
    choices = getattr(eng, "CHOICES", None)
    if not isinstance(choices, dict):
        return [{"id": a.get("id", "?"), "rule": a.get("rule", "?"),
                 "verdict": "unwired",
                 "note": "engine declares ASSUMPTIONS but has no CHOICES dict, "
                         "so neither reading can be played"} for a in assumptions]

    def headline(batch: dict) -> dict:
        return {"seat_edge": seat_edge(batch, n_players)["edge"],
                "forced_fraction": batch["forced_fraction"],
                "runaway": batch["runaway"] if batch["runaway"] is not None else 0.0,
                "turns_mean": batch["turns_mean"]}

    def win_shares(batch: dict) -> list:
        decided = sum(batch["wins"])
        if decided <= 0:
            return [0.0] * n_players
        return [w / decided for w in batch["wins"]]

    def pair(pol, count: int, aid: str | None):
        """The same games under both readings, same seed, same everything."""
        if aid is None:
            return run_batch(eng, lambda s, g: pol, n_players, count, cap,
                             seed, deadline), None
        was = choices.get(aid, "chosen")
        base = run_batch(eng, lambda s, g: pol, n_players, count, cap,
                         seed, deadline)
        choices[aid] = "alternative" if was != "alternative" else "chosen"
        try:
            flip = run_batch(eng, lambda s, g: pol, n_players, count, cap,
                             seed, deadline)
        finally:
            choices[aid] = was
        return base, flip

    def compare(base_batch, flipped_batch):
        base, flipped = headline(base_batch), headline(flipped_batch)
        deltas = {
            k: abs(flipped[k] - base[k]) if k != "turns_mean"
            else (abs(flipped[k] - base[k]) / max(base[k], 1.0))
            for k in base
        }
        # Every measure above reads the game in aggregate, and `seat_edge`
        # reads only the BEST seat, so a reading that swaps which seat wins
        # moves none of them: [.5,.5,0,0] and [0,0,.5,.5] both put the best
        # seat 25 points over a fair share. Total variation distance across
        # the whole win-share vector sees exactly that, and calls an inverted
        # winner set what it is, a delta of 1.0.
        a, b = win_shares(base_batch), win_shares(flipped_batch)
        deltas["win_share"] = 0.5 * sum(abs(x - y) for x, y in zip(a, b))
        same = (flipped_batch["wins"] == base_batch["wins"]
                and flipped_batch["turns_mean"] == base_batch["turns_mean"])
        return deltas, (max(deltas.values()) if deltas else 0.0), same

    out = []
    for entry in assumptions:
        aid = entry.get("id", "?")
        base_batch, flipped_batch = pair(policy, games, aid)
        deltas, worst, same = compare(base_batch, flipped_batch)
        verdict = "blocking" if worst > SENSITIVITY_DELTA else "cosmetic"
        under = "the baseline policy"

        if same:
            # Identical runs mean one of two very different things: the flip
            # is wired to nothing, or the position it changes never came up.
            # A tight policy visits a narrow slice of the game, so ask a loose
            # one, which wanders much further, before calling it dead wiring.
            base_batch, flipped_batch = pair(pol_random, games * 2, aid)
            deltas, worst, still_same = compare(base_batch, flipped_batch)
            if still_same:
                verdict, under = "unwired", "neither policy"
            else:
                verdict = "loose_play_only"
                under = "random play only"

        out.append({
            "id": aid, "rule": entry.get("rule", "?"),
            "question": entry.get("question", ""),
            "chosen": entry.get("chosen", ""),
            "alternative": entry.get("alternative", ""),
            "measured_under": under,
            "deltas": {k: round(v, 4) for k, v in deltas.items()},
            "worst_delta": round(worst, 4),
            "verdict": verdict,
        })
    return out


class _Harness:
    """A local namespace for the deterministic policy/statistics core above.

    `simulation.py` threads a `harness` object through several functions by
    convention (`run_simulation`, `make_adversarial`, `_opponent_best_margin`).
    Before this module was made self-contained, that object was the vendored
    `harness/playtest.py`, loaded through `config.load_harness("playtest")`.
    That vendored tree is gone -- deleted per design decision D7, which keeps
    only this file and `game.py` -- so the functions it supplied are defined
    directly above, in this same module, and exposed here under the same
    names so nothing downstream has to change.
    """

    unplayable = staticmethod(unplayable)
    _margin = staticmethod(_margin)
    make_mc = staticmethod(make_mc)
    pol_random = staticmethod(pol_random)
    pol_first = staticmethod(pol_first)
    pol_greedy = staticmethod(pol_greedy)
    run_batch = staticmethod(run_batch)
    seat_edge = staticmethod(seat_edge)
    challenge = staticmethod(challenge)
    run_sensitivity = staticmethod(run_sensitivity)
    validate_engine = staticmethod(validate_engine)
    play_one = staticmethod(play_one)


_HARNESS = _Harness()


EVALUATOR = "abo-game-simulation"
EVALUATOR_VERSION = "1.0.0"

# The lane names these four. A style is declared only where a policy behind it
# actually played games in the reported sample.
STYLES: Tuple[str, ...] = ("optimizing", "social", "exploratory", "adversarial")
SCRIPTED_STYLES: Tuple[str, ...] = ("optimizing", "exploratory", "adversarial")

MINIMUM_COMPLETED_GAMES = 1_000
DEFAULT_MC_BUDGET = 240
DEFAULT_DEADLINE_SECONDS = 1_800.0
DISTINCTNESS_POSITIONS = 60


class SimulationRefused(RuntimeError):
    """The sample cannot support the result that was asked for."""


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------


# How many of the opponent's replies the adversarial policy looks at. Reading
# every reply to every candidate is quadratic in the branching factor, and on a
# wide game that is the whole run's cost for a number that stops moving after a
# handful of samples. The subset is drawn from the policy's own seeded stream,
# so the measurement stays reproducible.
ADVERSARIAL_REPLY_SAMPLE = 8


def _opponent_best_margin(harness, engine, state, seat: int, rng) -> float:
    """The best margin the seat *not* to move could reach in one ply."""

    opponent = int(engine.player_to_move(state))
    replies = engine.legal_moves(state)
    if len(replies) > ADVERSARIAL_REPLY_SAMPLE:
        replies = rng.sample(replies, ADVERSARIAL_REPLY_SAMPLE)
    best = None
    for reply in replies:
        try:
            after = engine.apply_move(copy.deepcopy(state), reply, rng)
        except Exception as exc:  # noqa: BLE001
            if not harness.unplayable(exc):
                raise
            continue
        value = harness._margin(engine.scores(after), opponent)
        if best is None or value > best:
            best = value
    del seat
    return 0.0 if best is None else best


def make_adversarial(harness) -> Callable:
    """Play to deny the opponent, not to advance yourself.

    Design decision D3. This is the one style with no upstream equivalent, and
    it is a genuinely different objective from `optimizing`: it picks the move
    that leaves the opponent's best reply worst, which on a real position often
    costs its own score. Whether it actually diverges from `optimizing` is not
    asserted here — it is measured over the sample, so a badly written
    adversarial policy that collapses onto optimizing is caught by the same
    distinctness check that catches any other collapsed pair.
    """

    def pol_adversarial(engine, state, seat, rng, moves):
        best, best_value = [], None
        determinize = getattr(engine, "determinize", None)
        for move in moves:
            try:
                trial = copy.deepcopy(state)
                if determinize is not None:
                    trial = determinize(trial, seat, rng)
                after = engine.apply_move(trial, move, rng)
            except Exception as exc:  # noqa: BLE001
                if not harness.unplayable(exc):
                    raise
                continue
            if engine.is_over(after):
                value = harness._margin(engine.scores(after), seat)
            else:
                # Lower is better: we are minimizing what the opponent can do.
                value = -_opponent_best_margin(harness, engine, after, seat, rng)
            if best_value is None or value > best_value:
                best, best_value = [move], value
            elif value == best_value:
                best.append(move)
        return rng.choice(best) if best else rng.choice(moves)

    return pol_adversarial


def scripted_policies(harness, *, mc_budget: int, turn_cap: int) -> Dict[str, Callable]:
    """The three styles a script can play, mapped onto real policies.

    `social` is absent by design: no scripted policy is a social player, and a
    style with nothing executing behind it is not declared. It comes from the
    model seats.
    """

    return {
        "optimizing": harness.make_mc(mc_budget, turn_cap),
        "exploratory": harness.pol_random,
        "adversarial": make_adversarial(harness),
    }


# ---------------------------------------------------------------------------
# The sample
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StyleSample:
    """One style's batch, with completions and abandonments kept apart."""

    style: str
    requested: int
    played: int
    completed: int
    abandoned_turn_cap: int
    abandoned_no_legal_move: int
    engine_errors: int
    seed: int
    batch: Mapping[str, Any] = field(default_factory=dict, repr=False)

    @property
    def abandoned_deadline(self) -> int:
        return self.requested - self.played

    def to_dict(self) -> Dict[str, Any]:
        return {
            "style": self.style,
            "seed": self.seed,
            "games_requested": self.requested,
            "games_played": self.played,
            "completed_games": self.completed,
            "abandoned": {
                "turn_cap": self.abandoned_turn_cap,
                "no_legal_move": self.abandoned_no_legal_move,
                "deadline": self.abandoned_deadline,
                "engine_error": self.engine_errors,
            },
            "turns_mean": round(float(self.batch.get("turns_mean", 0.0)), 3),
            "branching_median": round(float(self.batch.get("branching_median", 0.0)), 3),
            "branching_max": float(self.batch.get("branching_max", 0.0)),
            "forced_fraction": round(float(self.batch.get("forced_fraction", 0.0)), 4),
            "kinds_legal": list(self.batch.get("kinds_legal", ())),
            "kinds_chosen": dict(self.batch.get("kinds_chosen", {})),
            "wins": list(self.batch.get("wins", ())),
            "tie_rate": round(float(self.batch.get("tie_rate", 0.0)), 4),
            "contract_findings": list(self.batch.get("admin_violations", ())),
        }


def _sample_style(
    harness,
    engine,
    policy,
    *,
    style: str,
    seats: int,
    games: int,
    turn_cap: int,
    seed: int,
    deadline: float,
) -> StyleSample:
    batch = harness.run_batch(
        engine, lambda seat, index: policy, seats, games, turn_cap, seed, deadline
    )
    played = int(batch["games_played"])
    completed = int(batch["natural_endings"])
    stuck = int(batch["stuck"])
    errors = int(batch["undefined_count"])
    # Everything played that neither ended naturally, ran out of legal moves,
    # nor hit a rules gap, stopped at the turn cap.
    turn_cap_abandonments = max(0, played - completed - stuck - errors)
    return StyleSample(
        style=style,
        requested=games,
        played=played,
        completed=completed,
        abandoned_turn_cap=turn_cap_abandonments,
        abandoned_no_legal_move=stuck,
        engine_errors=errors,
        seed=seed,
        batch=batch,
    )


# ---------------------------------------------------------------------------
# Style distinctness
# ---------------------------------------------------------------------------


def _positions(harness, engine, seats: int, turn_cap: int, seed: int, count: int):
    """A fixed set of real positions, reached by random play from one seed."""

    rng = random.Random(seed)
    found = []
    while len(found) < count:
        state = engine.new_game(seats, rng)
        depth = 0
        while depth < turn_cap and not engine.is_over(state):
            moves = engine.legal_moves(state)
            if not moves:
                break
            if len(moves) > 1:
                found.append(copy.deepcopy(state))
                if len(found) >= count:
                    break
            state = engine.apply_move(state, rng.choice(moves), rng)
            depth += 1
    del harness
    return found


def measure_distinctness(
    harness,
    engine,
    policies: Mapping[str, Callable],
    *,
    seats: int,
    turn_cap: int,
    seed: int,
    positions: int = DISTINCTNESS_POSITIONS,
) -> Dict[str, Any]:
    """Where the styles actually chose differently, recorded rather than claimed.

    Two styles that never diverge over the sample are one style with two names,
    and saying so is the point: the lane asks for four *distinct* styles, and a
    declaration is not a distinction.
    """

    sampled = _positions(harness, engine, seats, turn_cap, seed, positions)
    names = sorted(policies)
    chosen: Dict[str, list] = {name: [] for name in names}
    for index, state in enumerate(sampled):
        moves = engine.legal_moves(state)
        seat = int(engine.player_to_move(state))
        for name in names:
            # One rng per (style, position) so a divergence is the policy's
            # doing rather than a different draw from a shared stream.
            rng = random.Random(seed * 1_000_003 + index)
            chosen[name].append(repr(policies[name](engine, state, seat, rng, moves)))

    pairs = []
    collapsed = []
    for first_index, first in enumerate(names):
        for second in names[first_index + 1 :]:
            divergences = [
                index
                for index in range(len(sampled))
                if chosen[first][index] != chosen[second][index]
            ]
            pairs.append(
                {
                    "styles": [first, second],
                    "positions_compared": len(sampled),
                    "positions_diverged": len(divergences),
                    "first_divergence": divergences[0] if divergences else None,
                }
            )
            if not divergences:
                collapsed.append([first, second])
    return {
        "positions_compared": len(sampled),
        "pairs": pairs,
        "collapsed_pairs": collapsed,
        "distinct": not collapsed,
    }


# ---------------------------------------------------------------------------
# The measured properties
# ---------------------------------------------------------------------------


def measure_seat_advantage(harness, engine, policy, *, seats, games, turn_cap, seed, deadline):
    """One policy against itself, rotated through every seat.

    Rotation is the whole measurement: a seat edge read from a table where a
    policy never moved seats is the policy's skill and the seat's advantage
    added together.
    """

    batch = harness.run_batch(
        engine,
        lambda seat, index: policy,
        seats,
        games,
        turn_cap,
        seed,
        deadline,
        challenger_seat=lambda index: index % seats,
    )
    edge = harness.seat_edge(batch, seats)
    return {
        "completed_games": int(batch["natural_endings"]),
        "win_rates": [round(value, 4) for value in edge["win_rates"]],
        "fair_share": round(edge["fair_share"], 4),
        "best_seat": edge["best_seat"],
        "best_seat_rate": round(edge["best_rate"], 4),
        "confidence_interval": [round(value, 4) for value in edge["best_ci"]],
        # Guilty only if even the pessimistic reading puts a seat ahead.
        "edge": round(edge["edge"], 4),
    }


def measure_skill_ladder(
    harness, engine, policies, *, seats, games, turn_cap, seed, deadline, mc_budget
):
    """Does looking ahead beat not looking ahead?

    `greedy` and `first` are rungs rather than styles: they are how the depth
    is measured, and neither is a distinct *style* of play as the lane means it.
    """

    rungs = []
    for name, challenger, field_name, opponent in (
        ("optimizing-vs-greedy", policies["optimizing"], "greedy", harness.pol_greedy),
        ("greedy-vs-random", harness.pol_greedy, "random", harness.pol_random),
        ("optimizing-vs-random", policies["optimizing"], "random", harness.pol_random),
    ):
        outcome = harness.challenge(
            engine, name, challenger, field_name, opponent, seats, games, turn_cap, seed, deadline
        )
        rungs.append(
            {
                "rung": name,
                "games": outcome["games"],
                "win_rate": round(outcome["win_rate"], 4),
                "confidence_interval": [round(value, 4) for value in outcome["ci"]],
                "fair_share": round(outcome["fair_share"], 4),
                "edge": round(outcome["edge"], 4),
            }
        )
    del mc_budget
    return rungs


def measure_move_kinds(engine, samples: Sequence[StyleSample]) -> Dict[str, Any]:
    """Which declared move kinds were never legal, and which never chosen."""

    declared = sorted(str(kind) for kind in (getattr(engine, "MOVE_KINDS", ()) or ()))
    legal: set = set()
    chosen: Dict[str, int] = {}
    for sample in samples:
        legal |= set(sample.batch.get("kinds_legal", ()))
        for kind, count in dict(sample.batch.get("kinds_chosen", {})).items():
            chosen[kind] = chosen.get(kind, 0) + int(count)
    return {
        "declared": declared,
        "ever_legal": sorted(legal),
        "chosen_counts": chosen,
        "never_legal": [kind for kind in declared if kind not in legal],
        "never_chosen": [
            kind for kind in declared if kind in legal and not chosen.get(kind)
        ],
        "undeclared_but_seen": sorted(legal - set(declared)),
    }


def measure_assumption_readings(
    harness, engine, policy, *, seats, games, turn_cap, seed, deadline
) -> list:
    """Play every declared reading both ways and say whether it mattered."""

    return list(
        harness.run_sensitivity(engine, seats, games, turn_cap, seed, deadline, policy)
    )


def contract_findings(engine, samples: Sequence[StyleSample], kinds: Mapping[str, Any]) -> list:
    """Where the engine's own declarations did not survive being played.

    Ported from the imported harness: a move kind claimed to carry no decision
    that is ever seen alongside another legal move is a real branch sometimes,
    and the harness already counts that turn normally rather than excluding it.
    """

    findings = []
    for sample in samples:
        for violation in sample.batch.get("admin_violations", ()) or ():
            findings.append({"style": sample.style, "finding": violation})
    for kind in kinds["never_legal"]:
        findings.append(
            {
                "style": None,
                "finding": "contract: declared move kind %r was never legal in any "
                "game; a move the rules define and the engine never offers is a "
                "rule nobody plays" % kind,
            }
        )
    for kind in kinds["never_chosen"]:
        findings.append(
            {
                "style": None,
                "finding": "contract: declared move kind %r was legal but never "
                "chosen by any style; a choice nobody takes is not a choice" % kind,
            }
        )
    for kind in kinds["undeclared_but_seen"]:
        findings.append(
            {
                "style": None,
                "finding": "contract: move kind %r was offered in play but the "
                "engine does not declare it" % kind,
            }
        )
    del engine
    return findings


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SimulationOutcome:
    """Everything measured, and whether it can support a passing result."""

    evidence: Dict[str, Any]
    completed_games: int
    styles_played: Tuple[str, ...]
    findings: Tuple[str, ...]

    @property
    def meets_floor(self) -> bool:
        return self.completed_games >= MINIMUM_COMPLETED_GAMES

    @property
    def passed(self) -> bool:
        return self.meets_floor and not self.findings


def run_simulation(
    engine,
    *,
    artifact_sha256: str,
    seats: int,
    social_sample: Optional[Mapping[str, Any]] = None,
    games_per_style: int = 340,
    turn_cap: Optional[int] = None,
    mc_budget: int = DEFAULT_MC_BUDGET,
    seed: int = 20260826,
    deadline_seconds: float = DEFAULT_DEADLINE_SECONDS,
    ladder_games: int = 60,
    balance_games: int = 120,
    sensitivity_games: int = 40,
    distinctness_positions: int = DISTINCTNESS_POSITIONS,
    now: Callable[[], float] = time.monotonic,
) -> SimulationOutcome:
    """Play the game, measure it, and bind every number to these engine bytes."""

    harness = _HARNESS
    broken = harness.validate_engine(engine)
    if broken:
        raise SimulationRefused(
            "the engine under test is not a usable model of the rules:\n  - %s"
            % "\n  - ".join(broken)
        )
    cap = int(turn_cap or getattr(engine, "MAX_TURNS", 200))
    deadline = now() + float(deadline_seconds)
    policies = scripted_policies(harness, mc_budget=mc_budget, turn_cap=cap)

    samples = []
    for index, style in enumerate(SCRIPTED_STYLES):
        samples.append(
            _sample_style(
                harness,
                engine,
                policies[style],
                style=style,
                seats=seats,
                games=games_per_style,
                turn_cap=cap,
                seed=seed + index,
                deadline=deadline,
            )
        )

    completed = sum(sample.completed for sample in samples)
    styles_played = [sample.style for sample in samples if sample.completed]

    # The model seats supply `social`. They are a separate result with separate
    # evidence, and their games count toward this sample as one more style.
    social = None
    if social_sample is not None:
        social = dict(social_sample)
        social_completed = int(social.get("completed_games", 0))
        completed += social_completed
        if social_completed:
            styles_played.append("social")

    distinctness = measure_distinctness(
        harness,
        engine,
        policies,
        seats=seats,
        turn_cap=cap,
        seed=seed,
        positions=distinctness_positions,
    )
    kinds = measure_move_kinds(engine, samples)
    findings = [item["finding"] for item in contract_findings(engine, samples, kinds)]
    for pair in distinctness["collapsed_pairs"]:
        findings.append(
            "styles: %s and %s never chose differently over %d positions; they "
            "are one style with two names, not two"
            % (pair[0], pair[1], distinctness["positions_compared"])
        )
    missing_styles = [style for style in STYLES if style not in styles_played]
    for style in missing_styles:
        findings.append(
            "styles: %r is declared by the lane but no policy behind it played a "
            "completed game in this sample" % style
        )

    balance = measure_seat_advantage(
        harness,
        engine,
        policies["optimizing"],
        seats=seats,
        games=balance_games,
        turn_cap=cap,
        seed=seed + 101,
        deadline=deadline,
    )
    ladder = measure_skill_ladder(
        harness,
        engine,
        policies,
        seats=seats,
        games=ladder_games,
        turn_cap=cap,
        seed=seed + 202,
        deadline=deadline,
        mc_budget=mc_budget,
    )
    readings = measure_assumption_readings(
        harness,
        engine,
        policies["optimizing"],
        seats=seats,
        games=sensitivity_games,
        turn_cap=cap,
        seed=seed + 303,
        deadline=deadline,
    )
    for entry in readings:
        verdict = entry.get("verdict")
        if verdict == "unwired":
            # Either the flip is wired to nothing or the position it changes
            # never arose. The two are indistinguishable from outside, and
            # neither one lets the reading be reported as exercised.
            findings.append(
                "assumptions: %s could not be shown to be played both ways — "
                "flipping the reading changed nothing measurable under either a "
                "tight or a loose policy, so it is either wired to nothing or "
                "about a position no game reached" % entry.get("id")
            )
        elif verdict == "blocking":
            # The reading moved the game. The rules have to say which one is
            # meant; this is not something Make gets to keep deciding.
            findings.append(
                "assumptions: %s changed the outcome (worst delta %.4f under %s); "
                "rule %s has to say which reading is meant"
                % (
                    entry.get("id"),
                    entry.get("worst_delta", 0.0),
                    entry.get("measured_under"),
                    entry.get("rule"),
                )
            )

    abandoned = {
        "turn_cap": sum(sample.abandoned_turn_cap for sample in samples),
        "no_legal_move": sum(sample.abandoned_no_legal_move for sample in samples),
        "deadline": sum(sample.abandoned_deadline for sample in samples),
        "engine_error": sum(sample.engine_errors for sample in samples),
    }
    if abandoned["engine_error"]:
        findings.append(
            "termination: %d game(s) ended on a rules gap the engine could not "
            "resolve" % abandoned["engine_error"]
        )
    if abandoned["turn_cap"]:
        findings.append(
            "termination: %d game(s) did not reach a terminal state within %d "
            "turns" % (abandoned["turn_cap"], cap)
        )

    evidence: Dict[str, Any] = {
        "evidence_class": "ai-simulation",
        "executable": True,
        "artifact_sha256": artifact_sha256,
        "engine_sha256": _engine_digest(engine),
        "completed_games": completed,
        "minimum_completed_games": MINIMUM_COMPLETED_GAMES,
        "player_styles": sorted(set(styles_played)),
        "seats": seats,
        "turn_cap": cap,
        "seeds": [sample.seed for sample in samples],
        "abandoned": abandoned,
        "samples": [sample.to_dict() for sample in samples],
        "social_sample": social,
        "style_distinctness": distinctness,
        "seat_advantage": balance,
        "skill_ladder": ladder,
        "move_kinds": kinds,
        "assumption_readings": readings,
        "findings": findings,
        # Everything above is a measurement of seeded games. None of it is a
        # claim that a person understood, enjoyed, or would replay this game.
        "claim": (
            "%d seeded games ran to a terminal state against these exact engine "
            "bytes, and the properties recorded here were measured in them."
            % completed
        ),
        "evaluator": EVALUATOR,
        "evaluator_version": EVALUATOR_VERSION,
    }
    return SimulationOutcome(
        evidence=evidence,
        completed_games=completed,
        styles_played=tuple(sorted(set(styles_played))),
        findings=tuple(findings),
    )


def _engine_digest(engine) -> str:
    path = getattr(engine, "__file__", None)
    if not path or not Path(path).is_file():
        return "unmeasured"
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def config_digest(**settings: Any) -> str:
    """A digest of exactly the settings the sample was produced under."""

    return hashlib.sha256(
        json.dumps(settings, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


__all__ = [
    "ADVERSARIAL_REPLY_SAMPLE",
    "DEFAULT_DEADLINE_SECONDS",
    "DEFAULT_MC_BUDGET",
    "DISTINCTNESS_POSITIONS",
    "EVALUATOR",
    "EVALUATOR_VERSION",
    "MINIMUM_COMPLETED_GAMES",
    "SCRIPTED_STYLES",
    "STYLES",
    "SimulationOutcome",
    "SimulationRefused",
    "StyleSample",
    "config_digest",
    "contract_findings",
    "make_adversarial",
    "measure_assumption_readings",
    "measure_distinctness",
    "measure_move_kinds",
    "measure_seat_advantage",
    "measure_skill_ladder",
    "run_simulation",
    "scripted_policies",
]
