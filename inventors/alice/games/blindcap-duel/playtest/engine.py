"""engine.py — Blindcap: Duel, an executable model of idea.json.

Semantically re-verified on 2026-08-23 against the exact final source hashes
declared below. The executable mapping covers setup, the five alternating main
rounds, the alternating closing round, legal targets, hidden information,
grove scoring, and the complete neutral tiebreak chain.
"""
from __future__ import annotations

import copy


class Undefined(Exception):
    """The rules do not say."""


SLUG = "blindcap-duel"
PLAYERS = (2, 2)
MAX_TURNS = 40           # every complete game is exactly 24 applied moves
MOVE_KINDS = ("seed", "plant", "probe", "crown")
HIDDEN_INFO = True
ASSUMPTIONS = []
CHOICES = {}

# A content binding, not a timestamp-only freshness stamp. Update these only
# after comparing the executable model with both sources and rerunning the
# playtest harness.
VERIFIED_IDEA_SHA256 = "7f85d295b9127fd1688b68dd782f0b10255465a30a43d4c83f5c839802477fe1"
VERIFIED_RULES_SHA256 = "5e48d003b59450fc12df677d476350b84c2e0be3a30f3405bbd545239c2ad880"


SPECIES = ("deadhead", "bracket", "inkcap", "hollow")
SCARCE_SPECIES = ("inkcap", "hollow")
BASE_SUPPLY = ("deadhead", "deadhead", "bracket", "bracket", "inkcap", "hollow")
# Internal `upper` / `lower` band names mean the one-dot / two-dot channels,
# respectively. True is an open tunnel and therefore the public low result.
SPECIES_GROOVES = {
    "deadhead": (False, False),
    "bracket": (True, False),
    "inkcap": (False, True),
    "hollow": (True, True),
}

MAIN_ROUNDS = 5
PINS_PER_PLAYER = 3
CROWNS_PER_PLAYER = 3
MAIN_CROWN_LIMIT = 2
SEED_SOCKETS = (5, 12)  # fixed central sockets: (row 1, col 2) and (row 1, col 3)


def _layout():
    """Two joined 3x3 tiles, retaining the production socket numbering."""
    coords = []
    coord_to_id = {}
    for tile_col in (0, 1):
        for local_row in range(3):
            for local_col in range(3):
                coord = (local_row, tile_col * 3 + local_col)
                coord_to_id[coord] = len(coords)
                coords.append(coord)
    adjacency = [[] for _ in coords]
    for (row, col), idx in coord_to_id.items():
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbour = (row + dr, col + dc)
            if neighbour in coord_to_id:
                adjacency[idx].append(coord_to_id[neighbour])
    return coords, adjacency


COORDS, ADJACENCY = _layout()


def new_game(n_players, rng):
    if n_players != 2:
        raise Undefined("Blindcap: Duel is defined for exactly two players")
    sockets = [
        {
            "owner": None,
            "species": None,
            "crown": None,
            "probed_upper": False,
            "probed_lower": False,
            "probe_upper_by": None,
            "probe_lower_by": None,
        }
        for _ in COORDS
    ]
    return {
        "n": 2,
        "sockets": sockets,
        "troughs": [list(BASE_SUPPLY), list(BASE_SUPPLY)],
        "crowns_remaining": [CROWNS_PER_PLAYER, CROWNS_PER_PLAYER],
        "main_crowns_placed": [0, 0],
        "pins_remaining": [PINS_PER_PLAYER, PINS_PER_PLAYER],
        "phase": "seed",
        "seed_ptr": 0,
        "round": 0,
        # The physical rules choose the opening starter at random; seed choice
        # is simultaneous and therefore independent of this draw.
        "start_seat": rng.randrange(2),
        "seat_ptr": 0,
        "subphase": "seed",
    }


def player_to_move(state):
    if state["phase"] == "seed":
        return state["seed_ptr"]
    return (state["start_seat"] + state["seat_ptr"]) % state["n"]


def is_over(state):
    return state["phase"] == "over"


def _probe_moves(state, seat):
    if state["pins_remaining"][seat] <= 0:
        return []
    moves = []
    for i, socket in enumerate(state["sockets"]):
        if socket["species"] is None or socket["owner"] == seat:
            continue
        if not socket["probed_upper"]:
            moves.append(("probe", i, "upper"))
        if not socket["probed_lower"]:
            moves.append(("probe", i, "lower"))
    return moves


def _crown_moves(state, seat, *, closing=False):
    if state["crowns_remaining"][seat] <= 0:
        return []
    if not closing and state["main_crowns_placed"][seat] >= MAIN_CROWN_LIMIT:
        return []
    return [
        ("crown", i)
        for i, socket in enumerate(state["sockets"])
        if socket["species"] is not None
        and socket["owner"] != seat
        and socket["crown"] is None
    ]


def legal_moves(state):
    if is_over(state):
        return []
    seat = player_to_move(state)

    if state["phase"] == "seed":
        socket = SEED_SOCKETS[seat]
        return [("seed", species, socket) for species in sorted(set(state["troughs"][seat]))]

    if state["phase"] == "main" and state["subphase"] == "plant":
        empties = [i for i, socket in enumerate(state["sockets"])
                   if socket["species"] is None]
        return [("plant", species, socket)
                for species in sorted(set(state["troughs"][seat]))
                for socket in empties]

    if state["phase"] == "main":
        # No voluntary pass: the 3-probe/2-crown budget exactly fills the five
        # action rounds. The resource caps force the mix without prescribing order.
        moves = _probe_moves(state, seat) + _crown_moves(state, seat)
        if not moves:
            raise Undefined("main action: neither a legal probe nor crown exists")
        return moves

    if state["phase"] == "closing":
        moves = _crown_moves(state, seat, closing=True)
        if not moves:
            raise Undefined("closing round: reserved crown has no legal rival stool")
        return moves

    raise Undefined(f"turn structure: unknown phase {state['phase']!r}")


def _finish_seat_turn(state):
    state["seat_ptr"] += 1
    if state["seat_ptr"] < state["n"]:
        state["subphase"] = "plant" if state["phase"] == "main" else "closing"
        return

    state["seat_ptr"] = 0
    state["round"] += 1
    state["start_seat"] = 1 - state["start_seat"]
    if state["phase"] == "closing":
        state["phase"] = "over"
        state["subphase"] = "over"
    elif state["round"] >= MAIN_ROUNDS:
        state["phase"] = "closing"
        state["subphase"] = "closing"
    else:
        state["subphase"] = "plant"


def apply_move(state, move, rng):
    if move not in legal_moves(state):
        raise Undefined(f"illegal move {move!r} in {state['phase']}/{state['subphase']}")
    seat = player_to_move(state)
    kind = move[0]

    if kind == "seed":
        _, species, socket = move
        state["troughs"][seat].remove(species)
        state["sockets"][socket]["species"] = species
        state["sockets"][socket]["owner"] = seat
        state["seed_ptr"] += 1
        if state["seed_ptr"] == state["n"]:
            state["phase"] = "main"
            state["subphase"] = "plant"
            state["seat_ptr"] = 0
        return state

    if kind == "plant":
        _, species, socket = move
        state["troughs"][seat].remove(species)
        state["sockets"][socket]["species"] = species
        state["sockets"][socket]["owner"] = seat
        state["subphase"] = "action"
        return state

    if kind == "probe":
        _, socket, band = move
        target = state["sockets"][socket]
        target[f"probed_{band}"] = True
        target[f"probe_{band}_by"] = seat
        state["pins_remaining"][seat] -= 1
        _finish_seat_turn(state)
        return state

    if kind == "crown":
        _, socket = move
        state["sockets"][socket]["crown"] = seat
        state["crowns_remaining"][seat] -= 1
        if state["phase"] == "main":
            state["main_crowns_placed"][seat] += 1
        _finish_seat_turn(state)
        return state

    raise Undefined(f"unrecognised move kind {kind!r}")


def _groves(state):
    visited = [False] * len(state["sockets"])
    groves = []
    for start, socket in enumerate(state["sockets"]):
        if visited[start] or socket["species"] is None:
            continue
        species = socket["species"]
        visited[start] = True
        stack = [start]
        component = [start]
        while stack:
            current = stack.pop()
            for neighbour in ADJACENCY[current]:
                if (not visited[neighbour]
                        and state["sockets"][neighbour]["species"] == species):
                    visited[neighbour] = True
                    stack.append(neighbour)
                    component.append(neighbour)
        groves.append({"species": species, "sockets": component})
    return groves


def _grove_owners(state, grove):
    return {state["sockets"][i]["crown"] for i in grove["sockets"]
            if state["sockets"][i]["crown"] is not None}


def scores(state):
    result = [0.0, 0.0]
    for grove in _groves(state):
        owners = _grove_owners(state, grove)
        if not owners:
            continue
        size = len(grove["sockets"])
        multiplier = 2 if grove["species"] in SCARCE_SPECIES else 1
        payout = size * size * multiplier if len(owners) == 1 else size * multiplier
        for owner in owners:
            result[owner] += payout
    return result


def _largest_uncontested(state):
    best = [0, 0]
    for grove in _groves(state):
        owners = _grove_owners(state, grove)
        if len(owners) == 1:
            owner = next(iter(owners))
            best[owner] = max(best[owner], len(grove["sockets"]))
    return best


def _fully_identified_rivals(state):
    counts = [0, 0]
    for socket in state["sockets"]:
        owner = socket["owner"]
        if owner is None:
            continue
        for seat in range(2):
            if (owner != seat and socket["probe_upper_by"] == seat
                    and socket["probe_lower_by"] == seat):
                counts[seat] += 1
    return counts


def _distinct_rivals_probed(state):
    counts = [0, 0]
    for socket in state["sockets"]:
        owner = socket["owner"]
        if owner is None:
            continue
        for seat in range(2):
            if owner != seat and (socket["probe_upper_by"] == seat
                                  or socket["probe_lower_by"] == seat):
                counts[seat] += 1
    return counts


def _probe_bands_supporting_crowns(state):
    """Count a player's pins in the same rival stools as their crowns."""
    counts = [0, 0]
    for socket in state["sockets"]:
        seat = socket["crown"]
        if seat is None:
            continue
        counts[seat] += int(socket["probe_upper_by"] == seat)
        counts[seat] += int(socket["probe_lower_by"] == seat)
    return counts


def _sunk_probes(state):
    """Count each player's pins that found a groove and therefore sank."""
    counts = [0, 0]
    for socket in state["sockets"]:
        species = socket["species"]
        if species is None:
            continue
        upper_sunk, lower_sunk = SPECIES_GROOVES[species]
        if socket["probe_upper_by"] is not None and upper_sunk:
            counts[socket["probe_upper_by"]] += 1
        if socket["probe_lower_by"] is not None and lower_sunk:
            counts[socket["probe_lower_by"]] += 1
    return counts


def winners(state):
    tied = [0, 1]
    for values in (scores(state), _largest_uncontested(state),
                   _fully_identified_rivals(state), _distinct_rivals_probed(state),
                   _probe_bands_supporting_crowns(state), _sunk_probes(state)):
        top = max(values[seat] for seat in tied)
        tied = [seat for seat in tied if values[seat] == top]
        if len(tied) == 1:
            break
    return tied  # a tie surviving all neutral comparisons is a shared win


def _sample_consistent(constraints, trough_count, rng):
    slots = []
    for socket, req_upper, req_lower in constraints:
        allowed = [species for species in SPECIES
                   if (req_upper is None or SPECIES_GROOVES[species][0] == req_upper)
                   and (req_lower is None or SPECIES_GROOVES[species][1] == req_lower)]
        slots.append({"socket": socket, "allowed": allowed})
    for _ in range(trough_count):
        slots.append({"socket": None, "allowed": list(SPECIES)})

    order = sorted(range(len(slots)), key=lambda idx: len(slots[idx]["allowed"]))
    assigned = {}
    initial = {"deadhead": 2, "bracket": 2, "inkcap": 1, "hollow": 1}

    def backtrack(position, remaining):
        if position == len(order):
            return True
        idx = order[position]
        candidates = [species for species in slots[idx]["allowed"]
                      if remaining[species] > 0]
        rng.shuffle(candidates)
        for species in candidates:
            remaining[species] -= 1
            assigned[idx] = species
            if backtrack(position + 1, remaining):
                return True
            remaining[species] += 1
            del assigned[idx]
        return False

    if not backtrack(0, dict(initial)):
        raise AssertionError("determinize found no assignment consistent with probe results")
    planted, trough = {}, []
    for idx, slot in enumerate(slots):
        if slot["socket"] is None:
            trough.append(assigned[idx])
        else:
            planted[slot["socket"]] = assigned[idx]
    return planted, trough


def determinize(state, seat, rng):
    st = copy.deepcopy(state)
    # Harvest exposes every shank. There is no hidden assignment left to
    # resample once both closing crowns have been placed.
    if is_over(st):
        return st
    for opponent in range(st["n"]):
        if opponent == seat:
            continue
        constraints = []
        for idx, socket in enumerate(st["sockets"]):
            if socket["owner"] != opponent:
                continue
            pattern = SPECIES_GROOVES[socket["species"]]
            constraints.append((
                idx,
                pattern[0] if socket["probed_upper"] else None,
                pattern[1] if socket["probed_lower"] else None,
            ))
        planted, trough = _sample_consistent(constraints, len(st["troughs"][opponent]), rng)
        for idx, species in planted.items():
            st["sockets"][idx]["species"] = species
        st["troughs"][opponent] = trough
    return st


def observation(state, seat):
    sockets = []
    for socket in state["sockets"]:
        species = socket["species"]
        fully_probed = socket["probed_upper"] and socket["probed_lower"]
        harvested = is_over(state)
        sockets.append({
            "owner": socket["owner"],
            "crown": socket["crown"],
            "probed_upper": socket["probed_upper"],
            "probed_lower": socket["probed_lower"],
            "probe_upper_by": socket["probe_upper_by"],
            "probe_lower_by": socket["probe_lower_by"],
            "revealed_upper": (SPECIES_GROOVES[species][0]
                               if species is not None and socket["probed_upper"] else None),
            "revealed_lower": (SPECIES_GROOVES[species][1]
                               if species is not None and socket["probed_lower"] else None),
            "species": (species if socket["owner"] == seat or fully_probed or harvested
                        else None),
        })
    return {
        "n": state["n"],
        "seat": seat,
        "sockets": sockets,
        "troughs": [list(trough) if player == seat else len(trough)
                    for player, trough in enumerate(state["troughs"])],
        "crowns_remaining": list(state["crowns_remaining"]),
        "main_crowns_placed": list(state["main_crowns_placed"]),
        "pins_remaining": list(state["pins_remaining"]),
        "phase": state["phase"],
        "round": state["round"],
        "start_seat": state["start_seat"],
        "seat_ptr": state["seat_ptr"],
        "subphase": state["subphase"],
    }
