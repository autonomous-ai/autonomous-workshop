#!/usr/bin/env python3
"""table_run.py — drive the REAL Toggle engine with LLM player seats via Claude.

Faithful player table:
  * imports games/toggle/playtest/engine.py (single source of truth),
  * plays a 4-seat game move-for-move on that engine,
  * at every decision, one seat (the current player) is asked via `claude -p`
    to choose BY INDEX from the real engine's indexed legal_moves, given ONLY
    the observable state the rules expose to that seat (a Forger sees the
    Keystone; a truster does not),
  * breaks/catches dominance by running seats as adversarial players
    (eve-table-breaker posture) as well as straight players,
  * reports per-game winner_seat, decisive, ask_to_play_again, ended.

Seat answers are parsed from a single token: "CHOOSE n" (decision) or "YES|NO"
(ask-to-play-again). A seat that returns garbage moves is re-prompted once; if
it still fails the game is recorded but flagged (never trusted as evidence).

CLI:
    python3 table_run.py --games 6 --players 4 --out /tmp/toggle.json
"""
import argparse
import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAUDE = "/Users/d/.local/bin/claude"

HEADLESS = (
    "This is a one-shot, unattended, headless session. Reply with the single "
    "requested token and nothing else."
)

RULES_EXCERPT = """TOGGLE - The Hidden Detent (2-4p, ~20min).
Each round one Forger privately peeks the Keystone (a hidden two-sided truth, A or B),
then decides to play TRUE (set their lever to the real face) or BLUFF (the other face),
and claims a side aloud. Each other player in turn TRUSTS (bets 1 chip they were right,
banks even if right) or CHALLENGES (call the bluff: if Forger bluffed, challenger takes
the whole pot; if Forger was truthful, challenger pays 1). If nobody challenges: a truthful
Forger pays every truster +1 and the pot outcall grows; a bluffing Forger nobody dared call
pockets the whole pot. You win by the most point chips after 6 rounds."""


_ENGINE = None

def _engine():
    global _ENGINE
    if _ENGINE is None:
        spec = importlib.util.spec_from_file_location("toggle_engine", str(HERE / "engine.py"))
        m = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = m
        spec.loader.exec_module(m)
        _ENGINE = m
    return _ENGINE


def _load_engine():
    spec = importlib.util.spec_from_file_location("toggle_engine", str(HERE / "engine.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def _run_claude(prompt: str, timeout: int = 90) -> str:
    try:
        r = subprocess.run([CLAUDE, "-p", prompt], capture_output=True, text=True,
                           timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:  # noqa
        return f"ERR {e}"


def _parse_choose(text: str):
    import re
    m = re.search(r"CHOOSE\s*(\d+)", text, re.I)
    if m:
        return int(m.group(1))
    m2 = re.search(r"\b([0-3])\b", text)
    return int(m2.group(1)) if m2 else None


def _observable(state, me: int, hist: str) -> dict:
    """The state slice a seat is allowed to see, exactly per the rules."""
    is_forger = state.phase == "choose" and state.forger == me
    info = {
        "seat": me,
        "seats": state.n,
        "round": state.round,
        "phase": state.phase,
        "scores": state.scores,          # point chips are public
        "pot": state.pot,                # public
        "forger": state.forger,          # whose Forge it is is public
    }
    if is_forger:
        info["keystone"] = state.keystone        # only the Forger peeked it
    elif state.phase == "trust":
        info["forger_claimed"] = state.forger_claimed
        info["you_are_trusting"] = True
    return {"info": info, "history": hist}


def _decision_prompt(game, seat, me, state, hist):
    obs = _observable(state, me, hist)
    eng = _engine()
    if state.phase == "choose":
        moves = ["[0] play TRUE (set lever to the real face)", "[1] bluff (the other face)"]
        extra = f"You are the FORGER this round. The Keystone shows: {obs['info'].get('keystone')}."
        ms = [("forger", True), ("forger", False)]
    else:
        moves = ["[0] TRUST (bet 1 chip it's true)", "[1] CHALLENGE (call the bluff)"]
        extra = f"The Forger (seat {obs['info']['forger']}) claimed: {obs['info'].get('forger_claimed')}."
        ms = [("trust", me), ("challenge", me)]
    body = (
        f"{RULES_EXCERPT}\n\n"
        f"You are seat {me} of {obs['info']['seats']} in game #{game}. Round {obs['info']['round']}/6.\n"
        f"{extra}\n"
        f"Public chips (scores): {obs['info']['scores']}. Pot: {obs['info']['pot']}. "
        f"Current Forger: seat {obs['info']['forger']}.\n"
        f"History of past rounds (round: forger->true|bluff): {hist}\n"
        f"Legal moves (choose by INDEX): {moves}\n"
        f"{HEADLESS}\n"
        f"Reply with exactly: CHOOSE n"
    )
    return body, ms


def _ask_prompt(game, me, state, hist, moments):
    w = _engine().winner(state)
    body = (
        f"{RULES_EXCERPT}\n\n"
        f"You were seat {me} of {state.n} in game #{game}. The game ended - you just "
        f"played the whole thing live, round by round, feeling the tension of each "
        f"call. Final chips (scores): {state.scores} (winner seat {w}).\n"
        f"What actually happened this game:\n" + ("\n".join("- " + m for m in moments) if moments else "no calls were ever made - it all banked quietly.") +
        f"\n\nYou are a real player, not a tutorial bot, and you just experienced "
        f"those moments. Would you genuinely ask to play this game again right now "
        f"with the same group? \n{HEADLESS}\n"
        f"Reply with exactly: YES or NO"
    )
    return body


def play_one(game: int, seed: int, players: int, straight: bool) -> dict:
    """Play one 4-seat game by stepping the real engine, querying Claude seats."""
    eng = _engine()
    s = eng.new_game(players, seed)
    hist = []
    guard = 0
    ended = False
    winner_seat = None
    moments = []
    while not eng.is_over(s) and guard < 300:
        guard += 1
        me = eng.current_player(s)
        prompt, ms = _decision_prompt(game, me, me, s, "; ".join(hist))
        # seats are adversarial when not `straight` (table-breaker posture)
        if not straight:
            prompt = ("You are Eve's TABLE-BREAKER: hunt for a dominant/degenerate "
                      "strategy, kingmaking, or a first-mover exploit.\n" + prompt)
        text = _run_claude(prompt)
        idx = _parse_choose(text)
        if idx is None or not (0 <= idx < len(ms)):
            # one re-prompt
            text = _run_claude(prompt + "\nThat was not a valid index. Reply CHOOSE n again.")
            idx = _parse_choose(text)
        if idx is None or not (0 <= idx < len(ms)):
            return {"game": game, "ended": False, "winner_seat": None,
                    "decisive": False, "ask_to_play_again": [False]*players,
                    "note": "seat returned invalid move; inconclusive", "legit": False}
        move = ms[idx]
        if s.phase == "choose":
            truthful = move[1]
            hist.append(f"r{s.round}: seat{s.forger}->{'true' if truthful else 'bluff'}")
        s = eng.apply(s, move)
        # capture the public drama of the round as it resolves (a round is over when
        # the engine returns to the "choose" phase for the next round)
        if s.phase == "choose" and any(s.last_round_delta):
            delta = s.last_round_delta
            top = max(delta)
            movers = [i for i, d in enumerate(delta) if d == top]
            if s.forger in movers and top >= s.pot:  # uncalled bluff pocketed the pot
                moments.append(f"r{s.round-1}: seat{s.forger} got away with it - "
                               f"uncalled bluff, took the pot")
            elif top > 4:
                moments.append(f"r{s.round-1}: seat{movers[0]} swung +{top} chips")
    if not eng.is_over(s):
        return {"game": game, "ended": False, "winner_seat": None, "decisive": False,
                "ask_to_play_again": [False]*players, "note": "did not terminate", "legit": True}
    ended = True
    winner_seat = eng.winner(s)
    decisive = winner_seat is not None and s.scores[winner_seat] > 1

    def ask(me):
        p = _ask_prompt(game, me, s, "; ".join(hist), moments)
        t = _run_claude(p).strip().upper()
        return t.startswith("YES") or ("Y" == t[:1])

    asks = [ask(m) for m in range(players)]
    return {"game": game, "ended": ended, "winner_seat": winner_seat,
            "decisive": decisive, "ask_to_play_again": asks,
            "note": "break" if not straight else "", "legit": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=6)
    ap.add_argument("--players", type=int, default=4)
    ap.add_argument("--out", default="/tmp/toggle_llm.json")
    ap.add_argument("--seeds", type=int, default=1000)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--break-first", type=int, default=2, help="first N games use breaker")
    args = ap.parse_args()

    def run(g):
        straight = g > args.break_first
        return play_one(g, args.seeds + g, args.players, straight)

    games = {}
    with ThreadPoolExecutor(max_workers=args.parallel) as ex:
        for i, res in enumerate(ex.map(run, range(1, args.games + 1))):
            games[i + 1] = res
            print(f"game {i+1}: winner={res['winner_seat']} ended={res['ended']} "
                  f"dec={res['decisive']} asks={sum(res['ask_to_play_again'])} "
                  f"legit={res.get('legit')}", flush=True)

    out = {"games": [games[k] for k in sorted(games)]}
    Path(args.out).write_text(json.dumps(out))
    # aggregate
    ended = [g for g in out["games"] if g["ended"] and g["legit"]]
    n = len(ended)
    if n:
        fs = sum(1 for g in ended if g["winner_seat"] == 0) / n
        dec = sum(1 for g in ended if g["decisive"]) / n
        asks_all = [a for g in ended for a in g["ask_to_play_again"] if isinstance(a, bool)]
        ask_frac = sum(asks_all) / len(asks_all) if asks_all else 0.0
        print(f"\nAGGREGATE ({n} ended games): first_seat={fs:.3f} "
              f"decisive={dec:.3f} ask_frac={ask_frac:.3f}")
    return out


if __name__ == "__main__":
    main()
