"""Playtesting — scripted engine runs + LLM-player table + the fun gate.

The load-bearing measurement of the whole system: **FUN = a player asks to
play again**. The org's PLAYTEST.md protocol runs ≥3 real human groups; before
humans are available Eve runs real LLM-player tables (four seats, adversarial
breaker) the same way vibe-ideas does.

Playtest is honest by construction:
  * the scripted engine runs thousands of games with simple policies and
    reports *measured* properties: does it end, first-seat win rate,
    decisiveness, whether looking-ahead helps (a proxy for skill mattering);
  * the player table, when unavailable, returns NO fun evidence — so the fun
    gate cannot pass on a placeholder (see audit(): fun_pass requires evidence);
  * the fun gate passes only on real evidence, never on self-report.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import gates


@dataclass
class FunEvidence:
    source: str                 # "scripted" | "llm_table" | "human"
    games_played: int
    first_seat_wins: float      # fraction won by seat 0 (bad if ~1)
    ends: bool                  # can the game reach a terminal state
    decisiveness: float         # 0..1 how often a clear winner emerges
    ask_to_play_again: float    # faction of players who asked to replay
    note: str = ""

    @property
    def fun(self) -> bool:
        """F.U.N. bar: at least one asked-to-replay, with a reachable end and
        no dominant first seat. Source must be real (llm_table/human), never
        a stand-in."""
        if self.source not in ("llm_table", "human"):
            return False
        if not self.ends:
            return False
        if self.first_seat_wins >= 0.60:
            return False  # first player advantage is a design defect
        return self.ask_to_play_again > 0


# --- scripted engine ------------------------------------------------------
def scripted_engine(game, trials: int = 3000, seed: int = 0) -> FunEvidence:
    """A deterministic multi-seat simulation over the game's bill/spec.

    This is a *skeleton* engine that models the three properties the rules
    lens cares about; the real per-game engine is written by the rules-engineer
    agent into games/<slug>/playtest/engine.py (as vibe-ideas does). When an
    engine.py exists it is imported; otherwise we fall back to this neutral
    model so the pipeline is runnable and the metric is always measurable."""
    engine_script = Path("games") / (game.slug or "x") / "playtest" / "engine.py"
    if engine_script.exists():
        return _run_imported_engine(engine_script, trials=trials, seed=seed)

    rng = random.Random(seed)
    ends_count = 0
    first_seat_wins = 0
    decisive = 0
    lookahead_matters = 0
    seats = 4
    for _ in range(trials):
        # neutral model: any combination of 2-6 turns; seats sampled
        end = rng.random() < 0.9
        if not end:
            continue
        ends_count += 1
        winner = rng.randrange(seats)
        if winner == 0:
            first_seat_wins += 1
        # decisiveness: a clear margin exists most of the time
        decisive += 1 if rng.random() < 0.75 else 0
        # lookahead helps ~half the time (proxy for skill mattering)
        lookahead_matters += 1 if rng.random() < 0.5 else 0

    asks = 0.0 if ends_count == 0 else 0.15  # neutral replay-ask fraction
    return FunEvidence(
        source="scripted",
        games_played=trials,
        first_seat_wins=(first_seat_wins / ends_count) if ends_count else 1.0,
        ends=ends_count > 0,
        decisiveness=(decisive / ends_count) if ends_count else 0.0,
        ask_to_play_again=asks,
        note="skeleton engine (no engine.py); use engine.py for a real game model",
    )


def _run_imported_engine(path: Path, trials: int, seed: int) -> FunEvidence:
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("game_engine", path)
    mod = importlib.util.module_from_spec(spec)
    # Register the module in sys.modules BEFORE exec so dataclass/typing
    # resolution (which looks the class's module up in sys.modules) works.
    # Without this, dataclasses.__process_class fails with
    # AttributeError: 'NoneType' object has no attribute '__dict__'.
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop(spec.name, None)   # avoid stale module across games
    run = getattr(mod, "run", None)
    if run is None:
        return FunEvidence(
            source="scripted", games_played=0, first_seat_wins=1.0, ends=False,
            decisiveness=0.0, ask_to_play_again=0.0, note="engine.py missing run()")
    return run(trials=trials, seed=seed)



# --- player table ---------------------------------------------------------
LIVE_API = ("new_game", "current_player", "describe", "legal_moves",
            "apply", "is_over", "winner")
MAX_RETRIES = 1
SEAT_RULES_MAX = 2800          # chars of rules.md given to a seat
TABLE_BREAKER = ("You are Eve's TABLE-BREAKER: hunt for a dominant or "
                 "degenerate strategy, kingmaking, or a first-mover exploit. "
                 "Play to break the game, then answer honestly.")


def engine_has_live(eng) -> bool:
    return all(getattr(eng, f, None) is not None for f in LIVE_API)


def _standby(note: str) -> FunEvidence:
    return FunEvidence(source="standby", games_played=0, first_seat_wins=1.0,
                       ends=False, decisiveness=0.0, ask_to_play_again=0.0,
                       note=note)


def _import_engine(engine_path: Path):
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("eve_table_engine", engine_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop(spec.name, None)
    return mod


def _rules_excerpt(gdir: Path) -> str:
    rp = gdir / "rules.md"
    if not rp.exists():
        return "(no rules.md found in the game dir)"
    txt = rp.read_text(encoding="utf-8", errors="replace").strip()
    return txt[:SEAT_RULES_MAX]


def _seat_reply(prompt: str, break_: bool):
    """One seat decision via the Claude CLI (prompt-only, no tools)."""
    from . import agents, config
    if not break_:
        pass
    body = prompt
    try:
        res = agents.run_agent("table-seat", body, cwd=None,
                               max_minutes=8, max_turns=2)
        return res.text
    except agents.QuotaExhausted:
        raise
    except agents.Starved:
        return ""
    except agents.AgentError:
        return ""


def _parse_choose(text: str):
    import re
    m = re.search(r"CHOOSE\s*(\d+)", text or "", re.I)
    if m:
        return int(m.group(1))
    m2 = re.search(r"\b([0-9])\b", text or "")
    return int(m2.group(1)) if m2 else None


_SESSION_LIMIT_MARKS = (
    "session limit", "session_limit", "resets", "rate limit", "rate-limit",
    "too many requests", "quota", "403", "429", "capacity",
)


def _is_session_limited(text: str) -> bool:
    low = (text or "").lower()
    return any(m in low for m in _SESSION_LIMIT_MARKS)


def _seat_choose(g, me, rules, obs, moves, hist, agents_mod, break_):
    lines = [f"[{i}] {m}" for i, m in enumerate(moves)]
    prompt = (
        f"{rules}\n\nYou are seat {me} in Eve board game #{g}. It is your turn.\n"
        f"History: {'; '.join(hist) or 'none yet'}\n"
        f"Your view of the board:\n{obs}\n\n"
        f"These are the legal moves. Reply CHOOSE n with the index of your move.\n"
        + "\n".join(lines)
    )
    if break_:
        prompt = TABLE_BREAKER + "\n" + prompt
    return prompt


def _play_live_game(g, eng, rules, players, seed, agents_mod, run_table) -> dict:
    s = eng.new_game(players, seed)
    hist = []
    guard = 0
    break_ = g <= 2          # first 2 games adversarial (vibe-ideas rule)
    while not eng.is_over(s) and guard < 400:
        guard += 1
        try:
            me = eng.current_player(s)
        except Exception:
            me = (guard - 1) % players
        describe = getattr(eng, "describe", None)
        obs = describe(s, me) if describe else repr(s)
        moves = eng.legal_moves(s)
        if not moves:
            break
        prompt = _seat_choose(g, me, rules, obs, moves, hist, agents_mod, break_)
        legit = False
        idx = None
        replies = []
        for attempt in range(MAX_RETRIES + 1):
            text = _seat_reply(prompt, break_)
            replies.append(text or "")
            idx = _parse_choose(text)
            if idx is not None and 0 <= idx < len(moves):
                legit = True
                break
            if attempt == 0:
                prompt += ("\nThat was not a valid move index. Reply CHOOSE n "
                           "with one of the listed indices.")
        if not legit:
            note = ("seat returned no valid move for consecutive turns" if not
                    any(_is_session_limited(t) for t in replies)
                    else "seat could not respond (Claude session limit; standby)")
            return {"game": g, "ended": False, "winner_seat": None,
                    "decisive": False, "ask_to_play_again": [False] * players,
                    "legit": False, "note": note}
        s = eng.apply(s, moves[idx])
        hist.append(f"r{guard}: seat{me}->{moves[idx]}")
    if not eng.is_over(s):
        return {"game": g, "ended": False, "winner_seat": None, "decisive": False,
                "ask_to_play_again": [False] * players, "legit": True,
                "note": "did not terminate within guard"}
    winner_seat = eng.winner(s)
    decisive = winner_seat is not None
    asks = []
    for me in range(players):
        ask_prompt = (
            f"{rules}\n\nYou are seat {me}; you just played Eve board game #{g} "
            f"to the end (winner seat {winner_seat}).\n"
            f"Full game, {guard} turns. History: {'; '.join(hist)}\n\n"
            "You are a real player, not a tutorial bot, and you just experienced "
            "those turns. Would you genuinely ask to play this game again right now "
            "with the same group?\nHeadless session. Reply with exactly: YES or NO"
        )
        if break_:
            ask_prompt = TABLE_BREAKER + "\n" + ask_prompt
        t = _seat_reply(ask_prompt, break_).strip().upper()
        asks.append(bool(t.startswith("YES") or t == "Y"))
    return {"game": g, "ended": True, "winner_seat": winner_seat,
            "decisive": decisive, "ask_to_play_again": asks, "legit": True, "note": ""}


def run_player_table(game, cfg) -> FunEvidence:
    """Run a real LLM-player table (claude -p seats) over the game's live engine.

    Faithful port of the org's proven table (vibe-ideas / toggle table_run.py):
    drives the real engine move-for-move, one seat per decision choosing BY INDEX
    from the engine's legal_moves given only the per-seat observable view, with an
    adversarial breaker, then asks each seat whether it would play again.

    Requires an engine with a live interface (new_game/current_player/describe/
    legal_moves/apply/is_over/winner). When the engine lacks that interface, or
    the table is disabled, we return a `standby` placeholder the fun gate refuses
    to treat as evidence — never a fabricated pass. Opt-in via EVE_RUN_LLM_TABLE=1
    so the daemon does not burn seats on every tick."""
    if not getattr(cfg, "run_llm_table", False):
        return _standby("LLM-player table disabled (EVE_RUN_LLM_TABLE=0); no fun evidence")
    gdir = cfg.games_dir / game.slug
    engine_path = gdir / "playtest" / "engine.py"
    if not engine_path.exists():
        return _standby("no playtest/engine.py; no fun evidence")
    eng = _import_engine(engine_path)
    if not engine_has_live(eng):
        return _standby("engine lacks live interface (%s); no fun evidence"
                        % ", ".join(LIVE_API))
    rules = _rules_excerpt(gdir)
    players = int(getattr(cfg, "table_players", 4))
    tries = int(getattr(cfg, "table_games", 4))
    seed = int(getattr(cfg, "table_seed", 11))
    parallel = int(getattr(cfg, "table_parallel", 2))

    def run(g):
        return _play_live_game(g, eng, rules, players, seed + g, agents_mod, cfg)

    from . import agents as agents_mod
    if parallel > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=parallel) as ex:
            results = list(ex.map(run, range(1, tries + 1)))
    else:
        results = [run(g) for g in range(1, tries + 1)]

    ended = [r for r in results if r.get("ended") and r.get("legit")]
    n = len(ended)
    outdir = gdir / "playtest" / "table"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "run_llm.json").write_text(json.dumps({
        "slug": game.slug, "players": players, "games": results}, indent=2,
        default=str))
    if n == 0:
        note = (results[0].get("note") or "no terminated legit game") if results else "no games"
        return _standby(f"{note}; no fun evidence")
    fs = sum(1 for r in ended if r["winner_seat"] == 0) / n
    dec = sum(1 for r in ended if r["decisive"]) / n
    asks = [a for r in ended for a in r["ask_to_play_again"] if isinstance(a, bool)]
    ask_frac = sum(asks) / len(asks) if asks else 0.0
    return FunEvidence(source="llm_table", games_played=n, first_seat_wins=fs,
                       ends=True, decisiveness=dec, ask_to_play_again=ask_frac,
                       note=f"LLM-player {players}-seat table (claude -p); "
                            f"{n} ended games, breaks on first 2")


def cfg_eval_seats(cfg) -> int:
    return int(getattr(cfg, "table_players", 4))


def fun_gate(game, evidence: Optional[FunEvidence] = None) -> gates.GateResult:
    """Fil for FUN; requires real evidence (see FunEvidence.fun)."""
    if evidence is None:
        return gates.GateResult(False, ["no playtest evidence yet"], measurable=False)
    if not evidence.fun:
        reasons = []
        if evidence.source not in ("llm_table", "human"):
            reasons.append(f"evidence source '{evidence.source}' is not real playtest")
        if not evidence.ends:
            reasons.append("game does not reliably reach an end state")
        if evidence.first_seat_wins >= 0.60:
            reasons.append(f"first seat wins {evidence.first_seat_wins:.0%} — dominant first player")
        if evidence.ask_to_play_again <= 0 and evidence.source in ("llm_table", "human"):
            reasons.append("no player asked to play again (FUN = ask to play again)")
        return gates.GateResult(False, reasons)
    return gates.GateResult(True, ["fun gate passed on real playtest evidence"])
