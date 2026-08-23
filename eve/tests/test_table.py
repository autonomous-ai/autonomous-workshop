"""Live LLM-player table: drives the real shed-and-shuttle engine seat-by-seat
over the pure live interface and emits typed llm_table FunEvidence — never a
fabricated pass. Also guards the honest standby path (no live interface)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from eve import agents, config, playtest


class _Result(agents.AgentResult):
    pass


def _copy_game(tmp_path: Path, name: str) -> Path:
    src = Path(__file__).resolve().parents[1] / "games" / name
    dst = tmp_path / "games" / name
    shutil.copytree(src, dst)
    return dst


@pytest.fixture
def table_cfg(tmp_path):
    _copy_game(tmp_path, "shed-and-shuttle")
    return config.Config(
        games_dir=tmp_path / "games",
        run_llm_table=True,
        table_games=2,
        table_players=4,
        table_parallel=1,
        table_seed=11,
    )


def _monkey_action(monkeypatch, move_text="CHOOSE 0", ask_text="YES"):
    def _run(name, prompt, **kw):
        if "YES or NO" in prompt:
            text = ask_text
        else:
            text = move_text
        return _Result(text=text, cost_usd=0.0, minutes=0.0, num_turns=1,
                       transcript_path=None, subtype="success")
    monkeypatch.setattr(agents, "run_agent", _run)


def test_run_player_table_emits_real_llm_evidence(monkeypatch, table_cfg):
    _monkey_action(monkeypatch)
    game = types.SimpleNamespace(slug="shed-and-shuttle")
    ev = playtest.run_player_table(game, table_cfg)
    assert ev.source == "llm_table", f"expected real table evidence, got {ev.source}: {ev.note}"
    assert ev.games_played > 0
    assert ev.ends is True
    # the per-run JSON is written for auditability
    js = table_cfg.games_dir / "shed-and-shuttle" / "playtest" / "table" / "run_llm.json"
    assert js.exists()
    data = json.loads(js.read_text())
    assert all(r["ended"] for r in data["games"])


def test_live_table_can_pass_fun_gate(monkeypatch, table_cfg):
    _monkey_action(monkeypatch, move_text="CHOOSE 0", ask_text="YES")  # every seat eager to replay
    game = types.SimpleNamespace(slug="shed-and-shuttle")
    ev = playtest.run_player_table(game, table_cfg)
    gate = playtest.fun_gate(None, ev)
    # With every seat asking to play again and a genuine end, first-seat must not
    # dominate for the gate to pass — assert the gate evaluates honestly, not that
    # one seeded draw auto-passes.
    assert gate.measurable is True
    assert ev.ask_to_play_again == 1.0


def test_fun_gate_rejects_standby_and_scripted():
    bad = playtest._standby("engine lacks live interface; no fun evidence")
    assert bad.source == "standby"
    assert playtest.fun_gate(None, bad).passed is False

    scripted = playtest.FunEvidence(
        source="scripted", games_played=2000, first_seat_wins=0.5,
        ends=True, decisiveness=0.9, ask_to_play_again=0.7, note="sim only")
    assert playtest.fun_gate(None, scripted).passed is False


def test_no_live_engine_returns_standby(tmp_path):
    g = tmp_path / "games" / "novel"
    (g / "playtest").mkdir(parents=True)
    (g / "playtest" / "engine.py").write_text(
        "def run(trials, seed):\n    return {'source': 'scripted'}\n"
        "class FunEvidence: pass\n"
    )
    cfg = config.Config(games_dir=tmp_path / "games", run_llm_table=True,
                        table_games=1, table_players=4, table_parallel=1)
    game = types.SimpleNamespace(slug="novel")
    ev = playtest.run_player_table(game, cfg)
    assert ev.source == "standby"
    assert playtest.fun_gate(None, ev).passed is False


import types


def _monkey_session_limit(monkeypatch):
    """Every seat returns the CLI's real session-limit text (Claude 429)."""
    def _run(name, prompt, **kw):
        return _Result(
            text="You've hit your session limit · resets 6:20pm (Asia/Saigon)",
            cost_usd=0.0, minutes=0.0, num_turns=1,
            transcript_path=None, subtype="success")
    monkeypatch.setattr(agents, "run_agent", _run)


def test_session_limit_is_recorded_honestly_not_as_invalid_move(monkeypatch, table_cfg):
    _monkey_session_limit(monkeypatch)
    game = types.SimpleNamespace(slug="shed-and-shuttle")
    ev = playtest.run_player_table(game, table_cfg)
    assert ev.source == "standby"
    assert "session limit" in ev.note, ev.note
    assert "no valid move" not in ev.note
    assert playtest.fun_gate(None, ev).passed is False
