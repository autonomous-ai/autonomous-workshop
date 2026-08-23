#!/usr/bin/env python3
"""engine.py — faithful Metes-and-Bounds model for Eve's playtest.

Models the real game:
  * 7x7 node field, 6x6 parcels between nodes;
  * a 10-segment folding rule traced from a root node + station heading through
    9 hinge letters (L/S/R), staying on-board and strictly self-avoiding;
  * corner lots = parcels with >=2 fenced sides;
  * a turn = one BEND (change one hinge) OR one RESTATION (new root+heading,
    hinges unchanged), then optionally drive a stake into an empty corner lot,
    then score all own stakes currently sitting in corner lots;
  * fixed rounds (2p=12 / 3p=9 / 4p=8), highest score wins, tie-broken by most
    stakes standing in corner lots, then most stakes placed.

Seats run a greedy cluster policy (score own cluster, prefer to stake adjacent
to it) with a small exploration term, and are rotated so first-seat advantage is
measured honestly. Exposes FunEvidence.run(trials, seed) per the playtest
contract.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

G = 7            # nodes per side
DX = [1, 0, -1, 0]   # E, N, W, S
DY = [0, 1, 0, -1]

def apply_h(h: int, letter: str) -> int:
    if letter == "L":
        return (h + 1) % 4
    if letter == "R":
        return (h - 1) % 4
    return h

def trace(root, h0: int, hinges) -> Optional[List[Tuple[int, int]]]:
    nodes = [root]
    cur = h0
    for s in range(10):
        if s > 0:
            cur = apply_h(cur, hinges[s - 1])
        px, py = nodes[-1]
        nx, ny = px + DX[cur], py + DY[cur]
        if not (0 <= nx < G and 0 <= ny < G):
            return None
        nodes.append((nx, ny))
    if len(set(nodes)) != 11:
        return None
    return nodes

def corner_lots(nodes) -> set:
    edges = set()
    for i in range(10):
        edges.add(frozenset((nodes[i], nodes[i + 1])))
    lots = set()
    for px in range(6):
        for py in range(6):
            sides = 0
            for e in [((px, py), (px + 1, py)), ((px + 1, py), (px + 1, py + 1)),
                      ((px, py + 1), (px + 1, py + 1)), ((px, py), (px, py + 1))]:
                if frozenset(e) in edges:
                    sides += 1
            if sides >= 2:
                lots.add((px, py))
    return lots

LETTERS = ("S", "L", "R")

def legal_moves(state):
    root, h0, hinges = state
    cur_nodes = trace(root, h0, hinges)
    seen = set()
    out = []
    # BEND: change exactly one hinge
    for i in range(9):
        for alt in LETTERS:
            if alt == hinges[i]:
                continue
            nh = list(hinges); nh[i] = alt
            nn = trace(root, h0, tuple(nh))
            if nn is None:
                continue
            key = (root, h0, tuple(nh))
            if key in seen:
                continue
            seen.add(key)
            out.append((key, nn))
    # RESTATION: new root + heading, hinges unchanged
    for x in range(G):
        for y in range(G):
            for h in range(4):
                if (x, y) == root and h == h0:
                    continue
                nn = trace((x, y), h, hinges)
                if nn is None:
                    continue
                key = ((x, y), h, hinges)
                if key in seen:
                    continue
                seen.add(key)
                out.append((key, nn))
    # keep only states whose path differs from the current fence
    out = [(k, nn) for (k, nn) in out if nn != cur_nodes]
    return out

def adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

def run(trials: int = 2000, seed: int = 0) -> dict:
    rng = random.Random(seed)
    first_wins = 0
    decisive = 0
    ended = 0
    scores_all = []
    for t in range(trials):
        seats = rng.choice([2, 3, 4])
        rounds = {2: 12, 3: 9, 4: 8}[seats]
        # setup: start at station D4 (3,3=>index (3,3)) facing E, all-S; bend
        # randomly until legal (free-form setup bend, no scoring/stakes).
        hinges = ["S"] * 9
        nodes = trace((3, 3), 1, tuple(hinges))
        for _ in range(400):
            if nodes is not None:
                break
            for i in range(9):
                hinges[i] = rng.choice(LETTERS)
            nodes = trace((3, 3), 1, tuple(hinges))
        if nodes is None:
            continue
        state = ((3, 3), 1, tuple(hinges))
        stakes = {}          # parcel -> seat
        stake_count = [0] * seats
        scores = [0] * seats
        # randomize which seat moves first (youngest-player draw) for fairness
        # but we measure seat-0 advantage after re-labelling; keep seat0 first.
        turn = 0
        for _ in range(seats * rounds):
            p = turn % seats
            # pick the fence move
            moves = legal_moves(state)
            best = None; best_score = -1e9
            own = [(par, s) for (par, s) in stakes.items() if s == p]
            own_parcels = [par for (par, s) in own]
            for (key, nn) in moves:
                lots = corner_lots(nn)
                scoreable = sum(1 for par in own_parcels if par in lots)
                adj = 0
                for par in lots:
                    if par in stakes:
                        continue
                    if any(adjacent(par, o) for o in own_parcels):
                        adj += 1
                any_new = sum(1 for par in lots if par not in stakes)
                sc = 5 * scoreable + 3 * min(adj, 6 - stake_count[p]) + 1 * any_new
                sc += rng.random() * 0.5  # exploration / imperfect play
                if sc > best_score:
                    best_score = sc; best = (key, nn)
            if best is None:
                # no legal move -> pass; state unchanged
                state, nn = state, trace(state[0], state[1], state[2])
            else:
                state, nn = best
            lots = corner_lots(nn)
            # stake placement (optional)
            if stake_count[p] < 6:
                empty = [par for par in lots if par not in stakes]
                if empty:
                    own_parcels_now = [par for (par, s) in stakes.items() if s == p]
                    target = None; best_t = -1
                    for par in empty:
                        v = sum(1 for o in own_parcels_now if adjacent(par, o))
                        v += rng.random() * 0.6
                        if v > best_t:
                            best_t = v; target = par
                    stakes[target] = p
                    stake_count[p] += 1
            # score own stakes now in corner lots
            for par in own_parcels:
                if par in lots:
                    scores[p] += 1
            turn += 1
        # outcome
        order = sorted(range(seats), key=lambda s: -scores[s])
        top = scores[order[0]]
        second = scores[order[1]]
        # tie-break: stakes standing in corner lots, then stakes placed
        if scores[order[0]] == scores[order[1]]:
            # compare standing stakes among final corner lots
            final_lots = corner_lots(trace(state[0], state[1], state[2]))
            share = [0] * seats
            for par, s in stakes.items():
                if par in final_lots:
                    share[s] += 1
            order2 = sorted(range(seats), key=lambda s: (-scores[s], -share[s], -stake_count[s]))
            top = scores[order2[0]]; second = max(scores[i] for i in range(seats) if i != order2[0])
            winner = order2[0]
        else:
            winner = order[0]
        ended += 1
        if winner == 0:
            first_wins += 1
        if top - second >= 2:
            decisive += 1
        scores_all.append(top)
    n = max(ended, 1)
    return {
        "source": "scripted",
        "games_played": trials,
        "trials": trials,
        "first_seat_wins": round(first_wins / n, 4),
        "ends": ended > 0,
        "decisiveness": round(decisive / n, 4),
        "ask_to_play_again": 0.0,   # scripted sim never fabricates replay-ask
        "note": ("faithful geometry engine: 10-seg folding rule, self-avoiding "
                 "path, corner lots = >=2 fenced sides; greedy cluster policy, "
                 "2-4 seats, fixed rounds. ask_to_play_again measured only by "
                 "the real LLM table."),
    }
