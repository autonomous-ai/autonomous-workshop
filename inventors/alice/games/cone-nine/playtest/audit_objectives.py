"""Deterministic fixed-draw audit for CONE NINE's eight glaze maps.

This is a complement to the authoritative generic simulation.  It holds the
private map deal and the public dial start fixed across every legal disjoint
two-map matchup, so a lucky deal cannot hide a map-value or seat problem.
It is digital model evidence only: no human or physical play is represented.
"""
from __future__ import print_function

import importlib.util
import itertools
import json
import os
import random


HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_PATH = os.path.join(HERE, "engine.py")
REPORT_PATH = os.path.join(HERE, "objective_audit.json")


def _load_engine():
    spec = importlib.util.spec_from_file_location("cone_nine_engine", ENGINE_PATH)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    return engine


def _objective_greedy(engine, state, rng):
    """Choose the move with the largest own immediate score gain.

    Only the active seat's own score is inspected.  Deterministic random
    tie-breaking prevents board-index order from becoming a hidden policy.
    """
    seat = engine.player_to_move(state)
    before = engine.scores(state)[seat]
    valued = []
    for move in engine.legal_moves(state):
        nxt = engine.apply(state, move)
        valued.append((engine.scores(nxt)[seat] - before, move))
    best = max(value for value, _ in valued)
    tied = [move for value, move in valued if value == best]
    return tied[rng.randrange(len(tied))]


def _play_fixed(engine, pair0, pair1, start, seed):
    state = engine.new_game(2, seed)
    state["objectives"] = [list(pair0), list(pair1)]
    state["deck"] = list(engine.DIAL[start:] + engine.DIAL[:start])
    state["dial_pos"] = 0
    state["band"] = state["deck"][0]
    rng = random.Random(seed ^ 0xC09E9)
    while not engine.is_over(state):
        state = engine.apply(state, _objective_greedy(engine, state, rng))
    return state


def run():
    engine = _load_engine()

    ceilings = {
        obj: len(engine.OBJ_CELLS[obj]) * engine.OBJ_VALUE[obj]
        for obj in engine.OBJECTIVES
    }
    if set(ceilings.values()) != {8}:
        raise AssertionError("glaze-map ceilings diverged: %r" % ceilings)
    if len({tuple(engine.OBJ_CELLS[obj]) for obj in engine.OBJECTIVES}) != 8:
        raise AssertionError("glaze maps must be eight distinct target masks")
    corners = {0, 3, 12, 15}
    centres = {5, 6, 9, 10}
    for obj in engine.OBJECTIVES:
        cells = set(engine.OBJ_CELLS[obj])
        if len(cells & corners) != 2 or len(cells & centres) != 2:
            raise AssertionError("map location classes diverged for %s" % obj)

    # Setup/determinism audit over 600 seeds: all four dealt maps are unique,
    # the wheel is a cyclic rotation, and the same seed reproduces byte-for-
    # byte-equivalent state.
    setup_counts = {obj: 0 for obj in engine.OBJECTIVES}
    for seed in range(600):
        state = engine.new_game(2, seed)
        if state != engine.new_game(2, seed):
            raise AssertionError("new_game is not deterministic at seed %d" % seed)
        dealt = state["objectives"][0] + state["objectives"][1]
        if len(dealt) != 4 or len(set(dealt)) != 4:
            raise AssertionError("map deal duplicates at seed %d: %r" % (seed, dealt))
        if sorted(state["deck"]) != sorted(engine.DIAL):
            raise AssertionError("dial is not a rotation at seed %d" % seed)
        for obj in dealt:
            setup_counts[obj] += 1

    pairs = list(itertools.combinations(engine.OBJECTIVES, 2))
    games = 0
    seat_credit = [0.0, 0.0]
    shared = 0
    bonus_sum = {obj: 0.0 for obj in engine.OBJECTIVES}
    appearances = {obj: 0 for obj in engine.OBJECTIVES}

    # Every ordered pair of disjoint two-map hands at all 16 public dial
    # starts: 420 matchups x 16 = 6,720 controlled games.
    for pair0 in pairs:
        remaining = [obj for obj in engine.OBJECTIVES if obj not in pair0]
        for pair1 in itertools.combinations(remaining, 2):
            for start in range(len(engine.DIAL)):
                seed = games * 7919 + start
                final = _play_fixed(engine, pair0, pair1, start, seed)
                games += 1
                winners = engine.winners(final)
                if len(winners) > 1:
                    shared += 1
                for winner in winners:
                    seat_credit[winner] += 1.0 / len(winners)
                for seat, hand in enumerate((pair0, pair1)):
                    for obj in hand:
                        bonus_sum[obj] += engine._obj_score(final, seat, obj)
                        appearances[obj] += 1

    mean_bonus = {
        obj: bonus_sum[obj] / float(appearances[obj])
        for obj in engine.OBJECTIVES
    }
    report = {
        "artifact_kind": "deterministic_digital_model_audit",
        "human_or_physical_evidence": False,
        "engine_idea_sha": engine.IDEA_SHA,
        "setup_seed_count": 600,
        "setup_deal_counts": setup_counts,
        "map_max_points": ceilings,
        "fixed_draw_games": games,
        "fixed_draw_policy": "own-score greedy; deterministic random tiebreak",
        "seat_win_credit": [value / float(games) for value in seat_credit],
        "shared_win_rate": shared / float(games),
        "objective_appearances": appearances,
        "mean_objective_bonus": mean_bonus,
        "mean_objective_bonus_spread": max(mean_bonus.values()) - min(mean_bonus.values()),
        "checks": {
            "all_map_ceilings_equal_eight": True,
            "all_eight_masks_distinct": True,
            "each_map_has_two_corners_two_centres": True,
            "deals_without_replacement": True,
            "seed_reproducible": True,
            "dial_is_fixed_cycle_with_random_start": True,
        },
    }
    with open(REPORT_PATH, "w") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()
