"""The missing executor: turns Eve's meta-loop *plan* into real agent runs.

meta.py is the planner — it decides *what* to run next (one unit of work per
tick) and records the outcome. driver.py is the executor: it reads a tick's
dispatch and actually runs the Claude sub-agent that fulfills it, then hands
the result back through meta.record_stage / the queue. The launchd daemon runs
`eve drive --steps 1` (or `eve tick --run-agent` which now executes), so a
tick that says "dispatch this role" no longer just prints and exits.

The one contract every role agent obeys: write a JSON contract file back into
its game directory (`stage_out.json`, or `idea.json` for a brand-new game).
The driver never parses free-form prose for structured fields; an agent that
fails to emit its contract fails the step, and an LLM step is retried exactly
once (Starved/Quota are never retried — see agents.py).

Unit of work stays one-per-call (matching the 30-min cadence): by default
`drive` advances exactly one step and exits, so the daemon stays crash-safe.
`--steps N` loops for a longer focused session.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from . import agents, meta as meta_mod, playtest
from . import promptlib


class DriverStop(Exception):
    """Raised to stop the drive loop cleanly (quota, quiet, hard failure)."""


def _log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[driver {ts}] {msg}", flush=True)


def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError):
        return None


def _safe_slug(s: str) -> str:
    import re
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or "game"


def _game_dir(cfg, slug: str) -> Path:
    return cfg.games_dir / slug


# --- ideator (brand-new game, from 'spark' or stage 'queued') --------------


def _run_ideator(cfg, m: "meta_mod.Meta", fn_run_agent) -> dict:
    """Invent one new game. The agent writes <dir>/idea.json + rules.md in a
    staging dir; on success we move it to games/<slug> and queue it."""
    from .queue import Queue
    pending = cfg.games_dir / (".pending-" + time.strftime("%Y%m%d%H%M%S"))
    pending.mkdir(parents=True, exist_ok=True)

    try:
        prompt = promptlib.ideator_prompt(cfg, out_dir=str(pending))
        res = fn_run_agent("ideator", prompt, cwd=str(pending))
        idea = _load_json(pending / "idea.json")
        if not idea:
            raise DriverStop(f"ideator finished but wrote no idea.json in {pending}")
        slug = _safe_slug(idea.get("slug"))
        if Queue(cfg, journal=m.journal).get(slug):
            raise DriverStop(f"ideator proposed an existing slug '{slug}' — killed")
        bill = idea.get("bill") or {}
        if not isinstance(bill, dict) or not bill:
            raise DriverStop("ideator wrote an empty bill — not a physical game")
        # move staged files into the resolved game dir
        target = cfg.games_dir / slug
        if target.exists():
            shutil.rmtree(target)
        pending.rename(target)
        queue = Queue(cfg, journal=m.journal)
        queue.add(slug,
                  title=idea.get("title", slug),
                  idea=idea.get("idea", ""),
                  identity=idea.get("identity", ""))
        queue.record(slug, bill=bill, mech=idea.get("mech", ""),
                     blurb=idea.get("blurb", ""), seats=idea.get("seats", "2-4"),
                     t_min=idea.get("t_min", "15"), t_max=idea.get("t_max", "25"))
        m.record_stage(slug, "novelty")   # next tick runs the no-LLM novelty gate
        return {"role": "ideator", "game": slug, "title": idea.get("title"),
                "identity": idea.get("identity", "")[:120]}
    finally:
        if pending.exists():
            shutil.rmtree(pending, ignore_errors=True)


def _run_brief(cfg, m, fn_run_agent, slug: str) -> dict:
    gdir = _game_dir(cfg, slug)
    prompt = promptlib.brief_prompt(cfg, game_dir=str(gdir))
    res = fn_run_agent("brief", prompt, cwd=str(gdir))
    out = _load_json(gdir / "stage_out.json")
    if not out:
        raise DriverStop(f"brief-agent for {slug} wrote no stage_out.json")
    bill = out.get("bill")
    if isinstance(bill, dict) and bill:
        _queue(self=Queue := None)  # placeholder replaced below
    return {"role": "brief", "game": slug}


def _queue(cfg, m):
    from .queue import Queue
    return Queue(cfg, journal=m.journal)


def _run_brief2(cfg, m, fn_run_agent, slug: str) -> dict:
    gdir = _game_dir(cfg, slug)
    prompt = promptlib.brief_prompt(cfg, game_dir=str(gdir))
    fn_run_agent("brief", prompt, cwd=str(gdir))
    out = _load_json(gdir / "stage_out.json")
    if not out:
        raise DriverStop(f"brief-agent for {slug} wrote no stage_out.json")
    q = _queue(cfg, m)
    bill = out.get("bill")
    if isinstance(bill, dict) and bill:
        q.record(slug, bill=bill)
    if out.get("brief"):
        q.record(slug, brief=out["brief"])
    m.record_stage(slug, "draft")
    return {"role": "brief", "game": slug}


def _run_builder(cfg, m, fn_run_agent, slug: str) -> dict:
    gdir = _game_dir(cfg, slug)
    prompt = promptlib.builder_prompt(cfg, game_dir=str(gdir))
    fn_run_agent("builder", prompt, cwd=str(gdir))
    out = _load_json(gdir / "stage_out.json")
    if not out or not out.get("built"):
        raise DriverStop(f"builder for {slug} produced no staged parts (no build/)")
    m.record_stage(slug, "build")   # next tick runs the deterministic print gate
    return {"role": "builder", "game": slug, "n_parts": out.get("n_parts")}


def _run_panel(cfg, m, fn_run_agent, slug: str) -> dict:
    gdir = _game_dir(cfg, slug)
    prompt = promptlib.panel_prompt(cfg, game_dir=str(gdir))
    fn_run_agent("panel", prompt, cwd=str(gdir))
    out = _load_json(gdir / "stage_out.json")
    if not out:
        raise DriverStop(f"panel for {slug} wrote no stage_out.json")
    verdict = (out.get("verdict") or "").lower()
    if verdict == "fail":
        m.journal.append("meta", action="panel_failed", game=slug,
                         notes=out.get("notes", ""))
        _queue(cfg, m).release(slug)
        return {"role": "panel", "game": slug, "verdict": "fail"}
    m.record_stage(slug, "playtest")
    return {"role": "panel", "game": slug, "verdict": "pass"}


def _run_playtest(cfg, m, fn_run_agent, slug: str) -> dict:
    """Playtest agent builds the engine + table; the driver measures FUN with
    the real (no-LLM) fun gate. Only a real llm_table/human evidence passes."""
    gdir = _game_dir(cfg, slug)
    prompt = promptlib.playtest_prompt(cfg, game_dir=str(gdir))
    try:
        fn_run_agent("playtest", prompt, cwd=str(gdir))
    except agents.Starved:
        # coding the engine starved -> stop this step, keep the game in playtest
        _queue(cfg, m).release(slug)
        return {"role": "playtest", "game": slug, "result": "starved"}
    out = _load_json(gdir / "stage_out.json")
    if not out:
        _queue(cfg, m).release(slug)
        return {"role": "playtest", "game": slug, "result": "no_evidence"}
    er = out.get("engine_run") or {}
    evidence = playtest.FunEvidence(
        source=str(er.get("source") or "scripted"),
        games_played=int(er.get("games_played") or er.get("trials") or 0),
        first_seat_wins=float(er.get("first_seat_wins") or 1.0),
        ends=bool(er.get("ends", False)),
        decisiveness=float(er.get("decisiveness") or 0.0),
        ask_to_play_again=float(er.get("ask_to_play_again") or 0.0),
        note=str(er.get("note") or out.get("interpretation") or ""),
    )
    q = _queue(cfg, m)
    q.record(slug, fun_evidence=q.get(slug).fun_evidence + [{
        "source": evidence.source, "games_played": evidence.games_played,
        "first_seat_wins": evidence.first_seat_wins, "ends": evidence.ends,
        "decisiveness": evidence.decisiveness,
        "ask_to_play_again": evidence.ask_to_play_again,
        "note": evidence.note}])
    gate = playtest.fun_gate(q.get(slug), evidence)
    if gate.passed:
        from .reward import RewardLedger
        RewardLedger(cfg, journal=m.journal).record(
            slug, "fun_pass", evidence=str(evidence))
        q.ship(slug)
        return {"role": "playtest", "game": slug, "result": "fun_pass",
                "evidence": evidence.source}
    m.journal.append("meta", action="fun_failed", game=slug,
                     reasons=gate.reasons, evidence=evidence.note)
    q.release(slug)
    return {"role": "playtest", "game": slug, "result": "fun_fail",
            "reasons": gate.reasons}


ROLE_FN = {
    "ideator": _run_ideator,
    "brief": _run_brief2,
    "builder": _run_builder,
    "panel": _run_panel,
    "playtest": _run_playtest,
}


# --- the driver loop --------------------------------------------------------


def _run_agent_once(fn_run_agent, role: str, prompt: str, cwd):
    """Run one agent with exactly one retry on transient AgentError."""
    try:
        return fn_run_agent(role, prompt, cwd=cwd)
    except agents.QuotaExhausted:
        raise
    except agents.Starved:
        raise
    except agents.AgentError:
        # LLM step: transient crash retried once, never twice (agents.py).
        return fn_run_agent(role, prompt, cwd=cwd)


def evolve(cfg, *, max_steps: int = 1, fn_run_agent=None) -> dict:
    """Advance up to `max_steps` units of work; returns a summary.

    Executes deterministic gates via meta.tick and LLM roles via fn_run_agent
    (injectable for mocks/tests; defaults to agents.run_agent)."""
    fn_run_agent = fn_run_agent or agents.run_agent
    m = meta_mod.Meta(cfg)
    m.heartbeat()
    ok, problems = m.audit_ok()
    if not ok:
        return {"action": "halted", "problems": problems}

    done = []
    for step in range(max(1, int(max_steps))):
        out = m.tick(run_agent=True)
        action = out.get("action")

        if action in ("gate", "study", "improve", "ship_check"):
            done.append(out)
            _log(f"{action}: {json.dumps(out, default=str)[:200]}")
            continue                       # one real unit done; keep looping

        if action == "dispatch":
            role = out.get("role")
            if role not in ROLE_FN:
                _log(f"dispatch for unknown role '{role}' — releasing, stopping")
                _queue(cfg, m).release(out.get("game"))
                break
            try:
                result = ROLE_FN[role](cfg, m, fn_run_agent, _safe_slug(out.get("game")))
            except agents.QuotaExhausted:
                m.journal.append("meta", action="quota",
                                 note="DAYBOOK quota_until 60m; loop pauses")
                _queue(cfg, m).release(out.get("game"))
                done.append({"action": "quota"})
                break
            except agents.Starved:
                m.journal.append("meta", action="starved", game=out.get("game"),
                                 role=role,
                                 note="raise the cap or cut the task; never same-cap retry")
                _queue(cfg, m).release(out.get("game"))
                done.append({"action": "starved", "role": role, "game": out.get("game")})
                break
            done.append(result)
            _log(f"dispatch {role}: {json.dumps(result, default=str)[:200]}")
            continue

        # quiet / spark when below floor but idle is not actionable here
        done.append(out)
        _log(f"{action}")
        if action == "spark":
            # below the inflight floor -> invent a new game now
            try:
                res = _run_ideator(cfg, m, fn_run_agent)
            except agents.QuotaExhausted:
                done.append({"action": "quota"})
                break
            except agents.Starved:
                done.append({"action": "starved", "role": "ideator"})
                break
            done.append(res)
            _log(f"spark->ideator: {json.dumps(res, default=str)[:200]}")
            continue
        break                            # quiet or terminal

    return {"action": "step", "results": done}
