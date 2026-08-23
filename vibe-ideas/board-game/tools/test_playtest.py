#!/usr/bin/env python3
"""test_playtest.py — fixtures with known answers for the playtest harness.

    python3 board-game/tools/test_playtest.py

Every fixture below is a tiny game whose verdict is not in doubt, written to
exercise exactly one of the ways a set of rules can fail. A gate that cannot
fail is indistinguishable from one that works, and this one is about to be
pointed at real ideas whose answers nobody knows, so it has to be pointed at
games whose answers everybody knows first.

The clean fixture is the important one. Six checks all firing on a broken game
proves nothing if they also fire on a sound one.
"""
from __future__ import annotations

import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import playtest as pt  # noqa: E402

# ---------------------------------------------------------------------------
# Fixture engines
# ---------------------------------------------------------------------------

PREAMBLE = '''
class Undefined(Exception):
    """The rules do not say."""
'''

# A snake draft. Fair by construction (over a full snake every seat's picks
# sum to the same rank total), terminating, with a real and obvious skill.
CLEAN = PREAMBLE + '''
SLUG = "clean"
PLAYERS = (2, 4)
MAX_TURNS = 60
MOVE_KINDS = ("take",)
HIDDEN_INFO = False
ASSUMPTIONS = []
CHOICES = {}

def new_game(n_players, rng):
    pool = [rng.randint(1, 20) for _ in range(4 * n_players)]
    order = []
    while len(order) < len(pool):
        order.extend(range(n_players))
        order.extend(reversed(range(n_players)))
    return {"pool": pool, "order": order[:len(pool)], "t": 0,
            "taken": [0] * n_players, "held": [[] for _ in range(n_players)]}

def player_to_move(s):
    return s["order"][s["t"]]

def legal_moves(s):
    return [("take", i) for i, v in enumerate(s["pool"]) if v is not None]

def apply_move(s, move, rng):
    seat = player_to_move(s)
    s["taken"][seat] += s["pool"][move[1]]
    s["held"][seat].append(s["pool"][move[1]])
    s["pool"][move[1]] = None
    s["t"] += 1
    return s

def is_over(s):
    return s["t"] >= len(s["order"])

def scores(s):
    return [float(v) for v in s["taken"]]

def winners(s):
    tally = scores(s)
    top = max(tally)
    best = [i for i, v in enumerate(tally) if v == top]
    if len(best) < 2:
        return best
    peak = max(max(s["held"][i], default=0) for i in best)
    return [i for i in best if max(s["held"][i], default=0) == peak]
'''

# Both players walk the same distance at the same speed and one of them starts.
SEAT = PREAMBLE + '''
SLUG = "seat"
PLAYERS = (2, 2)
MAX_TURNS = 40
MOVE_KINDS = ("advance", "stall")
HIDDEN_INFO = False
ASSUMPTIONS = []
CHOICES = {}

def new_game(n_players, rng):
    return {"pos": [0] * n_players, "t": 0}

def player_to_move(s):
    return s["t"] % len(s["pos"])

def legal_moves(s):
    return [("advance",), ("stall",)]

def apply_move(s, move, rng):
    if move[0] == "advance":
        s["pos"][player_to_move(s)] += 1
    s["t"] += 1
    return s

def is_over(s):
    return max(s["pos"]) >= 5

def scores(s):
    return [float(p) for p in s["pos"]]

def winners(s):
    return [i for i, p in enumerate(s["pos"]) if p >= 5]
'''

# Twenty turns of doing the only thing available, then a coin decides.
FORCED = PREAMBLE + '''
SLUG = "forced"
PLAYERS = (2, 2)
MAX_TURNS = 40
MOVE_KINDS = ("step",)
HIDDEN_INFO = False
ASSUMPTIONS = []
CHOICES = {}

def new_game(n_players, rng):
    return {"t": 0, "n": n_players, "won": None}

def player_to_move(s):
    return s["t"] % s["n"]

def legal_moves(s):
    return [("step",)]

def apply_move(s, move, rng):
    s["t"] += 1
    if s["t"] >= 20 and s["won"] is None:
        s["won"] = rng.randrange(s["n"])
    return s

def is_over(s):
    return s["t"] >= 20

def scores(s):
    return [0.0] * s["n"]

def winners(s):
    return [s["won"]] if s["won"] is not None else []
'''

# A game with no ending condition at all.
ENDLESS = PREAMBLE + '''
SLUG = "endless"
PLAYERS = (2, 2)
MAX_TURNS = 30
MOVE_KINDS = ("circle",)
HIDDEN_INFO = False
ASSUMPTIONS = []
CHOICES = {}

def new_game(n_players, rng):
    return {"t": 0, "n": n_players}

def player_to_move(s):
    return s["t"] % s["n"]

def legal_moves(s):
    return [("circle", 0), ("circle", 1), ("circle", 2)]

def apply_move(s, move, rng):
    s["t"] += 1
    return s

def is_over(s):
    return False

def scores(s):
    return [0.0] * s["n"]

def winners(s):
    return []
'''

# The classic omission: a position where you cannot act, and no rule saying so.
DEADLOCK = PREAMBLE + '''
SLUG = "deadlock"
PLAYERS = (2, 2)
MAX_TURNS = 40
MOVE_KINDS = ("place",)
HIDDEN_INFO = False
ASSUMPTIONS = []
CHOICES = {}

def new_game(n_players, rng):
    return {"t": 0, "n": n_players}

def player_to_move(s):
    return s["t"] % s["n"]

def legal_moves(s):
    return [] if s["t"] >= 5 else [("place", i) for i in range(4)]

def apply_move(s, move, rng):
    s["t"] += 1
    return s

def is_over(s):
    return s["t"] >= 30

def scores(s):
    return [0.0] * s["n"]

def winners(s):
    return []
'''

# The engineer hit a gap in the rules and refused to invent a branch.
UNDEFINED = PREAMBLE + '''
SLUG = "undefined"
PLAYERS = (2, 2)
MAX_TURNS = 40
MOVE_KINDS = ("place",)
HIDDEN_INFO = False
ASSUMPTIONS = []
CHOICES = {}

def new_game(n_players, rng):
    return {"t": 0, "n": n_players}

def player_to_move(s):
    return s["t"] % s["n"]

def legal_moves(s):
    return [("place", i) for i in range(4)]

def apply_move(s, move, rng):
    s["t"] += 1
    if s["t"] == 3:
        raise Undefined("rules:turn[2]: the rules never say what happens when "
                        "the row is already full")
    return s

def is_over(s):
    return s["t"] >= 30

def scores(s):
    return [0.0] * s["n"]

def winners(s):
    return []
'''

# An assumption is declared, and then the engine plays the same game whichever
# way it is set. The ambiguity looks tested and is not.
UNWIRED = CLEAN.replace(
    'ASSUMPTIONS = []\nCHOICES = {}',
    'ASSUMPTIONS = [{"id": "tiebreak", "rule": "rules:win",\n'
    '                "question": "who wins a tie?",\n'
    '                "chosen": "shared", "alternative": "first seat"}]\n'
    'CHOICES = {"tiebreak": "chosen"}')

# An assumption that decides the whole game.
BLOCKING = CLEAN.replace(
    'ASSUMPTIONS = []\nCHOICES = {}',
    'ASSUMPTIONS = [{"id": "opening_bonus", "rule": "rules:setup[2]",\n'
    '                "question": "does the start player keep the bonus tile?",\n'
    '                "chosen": "no", "alternative": "yes"}]\n'
    'CHOICES = {"opening_bonus": "chosen"}').replace(
    '    return [float(v) for v in s["taken"]]',
    '    out = [float(v) for v in s["taken"]]\n'
    '    if CHOICES.get("opening_bonus") == "alternative":\n'
    '        out[0] += 40.0\n'
    '    return out')


# Hidden information the engine never hides from the lookahead policy, which
# then reports an oracle's win rate as though it were a reachable skill.
ORACLE = CLEAN.replace("HIDDEN_INFO = False", "HIDDEN_INFO = True")

# The same draft with the token values face down until taken, hidden honestly:
# determinize reshuffles what is still in the pool, observation never shows it.
CONCEALED = CLEAN.replace("HIDDEN_INFO = False", "HIDDEN_INFO = True") + '''
def determinize(s, seat, rng):
    live = [i for i, v in enumerate(s["pool"]) if v is not None]
    vals = [s["pool"][i] for i in live]
    rng.shuffle(vals)
    for i, v in zip(live, vals):
        s["pool"][i] = v
    return s

def observation(s, seat):
    return {"face_down": [i for i, v in enumerate(s["pool"]) if v is not None],
            "taken": list(s["taken"]), "held": [list(h) for h in s["held"]],
            "t": s["t"], "order": list(s["order"])}
'''

# The same game, hidden dishonestly: the observation hands back the whole
# state, face-down values and all, while still claiming to hide them.
LEAKY = CONCEALED.replace(
    'def observation(s, seat):\n'
    '    return {"face_down": [i for i, v in enumerate(s["pool"]) if v is not None],\n'
    '            "taken": list(s["taken"]), "held": [list(h) for h in s["held"]],\n'
    '            "t": s["t"], "order": list(s["order"])}',
    'def observation(s, seat):\n    return s')

# Every token identical, so every seat ends level and the tiebreaker (there
# isn't one) never breaks anything.
TIE = CLEAN.replace("rng.randint(1, 20)", "3")

# The engine happens to enumerate the best move first, so a policy with no
# understanding at all beats random and every edge over random is inflated.
ORDERING = CLEAN.replace(
    'return [("take", i) for i, v in enumerate(s["pool"]) if v is not None]',
    'live = [i for i, v in enumerate(s["pool"]) if v is not None]\n'
    '    live.sort(key=lambda i: -s["pool"][i])\n'
    '    return [("take", i) for i in live]')

# scores() points the wrong way, so the one-ply policy every baseline is read
# from plays worse than dice.
PROXY = CLEAN.replace("    top = max(tally)", "    top = min(tally)")


# name, engine source, playtime_min, expected finding prefixes, run config
FIXTURES = [
    ("clean_game", CLEAN, 5, [], {"games": 150, "ladder_games": 50,
                                  "mc_budget": 16}),
    ("hidden_information_not_modelled", ORACLE, 5, ["depth_unmeasured:"], {}),
    ("hidden_information_hidden_honestly", CONCEALED, 5, [],
     {"games": 150, "ladder_games": 50, "mc_budget": 16}),
    ("observation_hands_back_the_secrets", LEAKY, 5, ["leak:"], {}),
    ("every_game_ends_level", TIE, 5, ["tie:"], {}),
    ("engine_lists_the_best_move_first", ORDERING, 5, ["ordering:"],
     {"games": 100, "ladder_games": 40}),
    ("score_proxy_points_the_wrong_way", PROXY, 5, ["proxy:"],
     {"games": 100, "ladder_games": 40}),
    ("first_seat_always_wins", SEAT, 4, ["seat:"], {}),
    ("every_turn_has_one_option", FORCED, 7, ["decisions:", "depth:"], {}),
    ("game_never_ends", ENDLESS, 10, ["termination:"], {}),
    ("stuck_with_no_rule_for_it", DEADLOCK, 10, ["deadlock:"], {}),
    ("rules_ran_out_mid_game", UNDEFINED, 10, ["undefined:", "unmeasurable:"], {}),
    ("assumption_declared_but_not_wired", UNWIRED, 5, ["contract:"], {}),
    ("assumption_decides_the_game", BLOCKING, 5, ["ambiguous:"], {}),
]

# The ladder count clears MIN_LADDER_GAMES on purpose: below it the depth
# check is suppressed, and half these fixtures are about the depth check.
DEFAULT_RUN = {"games": 40, "ladder_games": 24, "mc_budget": 8}


def run_fixture(source: str, playtime_min: int, config: dict) -> list:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "engine.py"
        path.write_text(source, encoding="utf-8")
        eng = pt.load_engine(path)
        contract = pt.validate_engine(eng)
        if contract:
            return contract
        run = {**DEFAULT_RUN, **config}
        stats = pt.analyse(eng, {"slug": "fixture", "playtime_min": playtime_min},
                           seed=5, deadline_s=240.0, **run)
        return pt.check(stats)


def check_contract_violations() -> list:
    """A file that is not an engine must be refused, not scored."""
    findings = []
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "engine.py"

        path.write_text("def new_game(n, rng):\n    return {}\n", encoding="utf-8")
        missing = pt.validate_engine(pt.load_engine(path))
        for needed in ("legal_moves", "winners", "PLAYERS", "MAX_TURNS"):
            if not any(needed in f for f in missing):
                findings.append(f"contract/{needed}: a stub engine missing "
                                f"`{needed}` was accepted")

        path.write_text("def new_game(:\n", encoding="utf-8")
        try:
            pt.load_engine(path)
            findings.append("contract/syntax: a file that does not parse was "
                            "loaded as an engine")
        except pt.EngineBroken:
            pass

        path.write_text(CLEAN + "\ndef apply_move(s, m, rng):\n"
                                "    raise ValueError('boom')\n", encoding="utf-8")
        try:
            eng = pt.load_engine(path)
            pt.analyse(eng, {"slug": "x", "playtime_min": 5}, games=4,
                       ladder_games=2, mc_budget=4, seed=1, deadline_s=30.0)
            findings.append("contract/crash: an engine that raises a plain "
                            "exception was scored as if it were a game")
        except pt.EngineBroken:
            pass
    return findings


GAP_ENGINE_LINES = [
    'engine.py fixture: every speculative line runs out of rules.',
    '',
    'class Undefined(Exception):',
    '    pass',
    '',
    'SLUG = "gapfixture"',
    'PLAYERS = (2,)',
    'MAX_TURNS = 20',
    'MOVE_KINDS = ("step",)',
    'HIDDEN_INFO = False',
    'ASSUMPTIONS = []',
    'CHOICES = {}',
    '',
    'def new_game(n_players, rng):',
    '    return {"seat": 0, "turns": 0, "held": [0, 0]}',
    '',
    'def player_to_move(state):',
    '    return state["seat"]',
    '',
    'def legal_moves(state):',
    '    return [("step", 1), ("step", 2), ("step", 3)]',
    '',
    'def apply_move(state, move, rng):',
    '    if state["turns"] >= 1:',
    '        raise Undefined("rules:turn[0]: the rules stop after one move")',
    '    state["held"][state["seat"]] += move[1]',
    '    state["seat"] = 1 - state["seat"]',
    '    state["turns"] += 1',
    '    return state',
    '',
    'def is_over(state):',
    '    return state["turns"] >= 1',
    '',
    'def scores(state):',
    '    return [float(x) for x in state["held"]]',
    '',
    'def winners(state):',
    '    best = max(scores(state))',
    '    return [i for i, s in enumerate(scores(state)) if s == best]',
]


def check_policies_survive_a_gap() -> list:
    """A policy must not kill the real game with a gap it only imagined.

    Greedy applies every candidate to a copy and the lookahead plays whole
    games out, so both walk into positions the real game never reaches. When
    one of those is a position the rules do not cover, the honest answer is
    that this candidate cannot be evaluated, not that this game has ended.

    Millbind is why this exists. Its crank jam is reachable, so every rollout
    eventually hit it, and the whole skill ladder recorded 0 completed games
    of 60 while the run attributed them to rules gaps in play. The ladder is
    the strongest measure in `playtest.py` and it had been quietly zeroed for
    every engine with a reachable `Undefined`.
    """
    source = "\n".join(GAP_ENGINE_LINES).replace(
        "engine.py fixture: every speculative line runs out of rules.", "", 1)
    bad = []
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "engine.py"
        path.write_text(source, encoding="utf-8")
        eng = pt.load_engine(path)
        # One real move played, so every further apply_move raises: exactly
        # the shape of a game whose speculative lines all run out of rules.
        state = eng.new_game(2, random.Random(1))
        state = eng.apply_move(state, ("step", 1), random.Random(1))
        moves = eng.legal_moves(state)
        for name, policy in (("greedy", pt.pol_greedy),
                             ("lookahead", pt.make_mc(8, 20))):
            try:
                move = policy(eng, state, 0, random.Random(2), moves)
            except Exception as exc:  # noqa: BLE001
                bad.append(f"{name} let a speculative rules gap escape and "
                           f"kill the game: {type(exc).__name__}: {exc}")
                continue
            if move not in moves:
                bad.append(f"{name} returned {move!r}, which is not legal")
    return bad


def check_table_mode() -> list:
    """The seat a person sits in. Three ways it must not go wrong.

    A table that shows a player the face-down pieces, or that carries on after
    the engine underneath it changed, produces a transcript that reads exactly
    like a real one. Both are silent, so both are checked.
    """
    import json
    import subprocess

    findings = []
    tool = Path(__file__).resolve().parent / "playtest.py"
    python = sys.executable

    def run(*argv):
        return subprocess.run([python, str(tool), "table", *argv],
                              capture_output=True, text=True, timeout=120)

    with tempfile.TemporaryDirectory() as td:
        idea = Path(td) / "fixture"
        (idea / "playtest").mkdir(parents=True)
        (idea / "idea.json").write_text(json.dumps(
            {"slug": "fixture", "playtime_min": 5,
             "players": {"min": 2, "max": 4}}), encoding="utf-8")
        engine = idea / "playtest" / "engine.py"

        # 1. Hidden information with no observation() must be refused outright.
        engine.write_text(ORACLE, encoding="utf-8")
        refused = run("new", str(idea), "--seats", "2")
        if refused.returncode != 2 or "observation" not in refused.stdout:
            findings.append(
                "table/hidden_info_guard: a game with face-down pieces and no "
                f"observation() was dealt anyway (exit {refused.returncode})")

        # 2. A whole game, played through to a real ending.
        engine.write_text(CLEAN, encoding="utf-8")
        opened = run("new", str(idea), "--seats", "2", "--seed", "4",
                     "--label", "t")
        if "LEGAL MOVES" not in opened.stdout:
            findings.append(f"table/new: no position dealt: {opened.stdout[:200]}")
        session = idea / "playtest" / "table" / "t.json"
        for _ in range(40):
            played = run("play", str(session), "--choice", "0",
                         "--why", "first one")
            if played.returncode != 0:
                findings.append(f"table/play: refused a legal choice: "
                                f"{played.stdout[:200]}")
                break
            if "TABLE OVER" in played.stdout:
                break
        else:
            findings.append("table/play: 40 decisions and the game never ended")

        recorded = json.loads(session.read_text(encoding="utf-8"))
        if not all(m["why"] for m in recorded["moves"] if m["by"] == "player"):
            findings.append("table/why: a player's reason was not recorded, so "
                            "the transcript cannot say what was weighed")

        # 3. The engine changing under a live session must stop it, not be
        #    absorbed into a game that then reads as if it were played.
        engine.write_text(ORDERING, encoding="utf-8")
        moved = run("show", str(session))
        if "changed under this session" not in (moved.stdout + moved.stderr):
            findings.append(
                "table/replay: the engine was rewritten mid-session and the "
                "table carried on as though the same game were still on it")
    return findings


def main() -> int:
    failures = []
    for name, source, playtime, needles, config in FIXTURES:
        findings = run_fixture(source, playtime, config)
        blob = " ".join(findings).lower()
        expect_pass = not needles
        if bool(findings) == expect_pass:
            failures.append(f"playtest/{name}: expected "
                            f"{'PASS' if expect_pass else 'FAIL'}, got {findings}")
        elif missing := [n for n in needles if n.lower() not in blob]:
            failures.append(f"playtest/{name}: verdict right but reason missing "
                            f"{missing} in {findings}")
        else:
            print(f"  ok  playtest/{name}")

    contract = check_contract_violations()
    failures += contract
    if not contract:
        print("  ok  playtest/refuses_a_non_engine")

    table = check_table_mode()
    failures += table
    if not table:
        print("  ok  playtest/table_seats_a_player_honestly")

    gaps = check_policies_survive_a_gap()
    failures += gaps
    if not gaps:
        print("  ok  playtest/a_policy_gap_does_not_kill_the_real_game")

    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"\nALL PASS ({len(FIXTURES) + 3} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
