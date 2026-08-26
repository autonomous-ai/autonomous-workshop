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
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

import config

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

    harness = config.load_harness("playtest")
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
