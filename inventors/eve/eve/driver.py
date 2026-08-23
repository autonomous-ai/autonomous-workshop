"""The missing executor: turns Eve's meta-loop *plan* into real agent runs.

meta.py is the planner — it decides *what* to run next (one unit of work per
tick) and records the outcome. driver.py is the executor: it reads a tick's
dispatch and actually runs the Claude sub-agent that fulfills it, then hands
the result back through meta.record_stage / the queue. The launchd job runs
`eve drive --steps 1`, so a tick that says "dispatch this role" no longer just
prints and exits.

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


def _auto_send_draft(cfg, game, journal) -> dict:
    """On a fresh ``ship``, Pack and send a Shop Door draft.

    Best-effort and idempotent, so a transient Door/network failure never
    fails the ship itself. Gated by EVE_AUTO_SEND (default on) so a 24/7 daemon
    keeps every finished game
    appearing on the site without a human in the loop.
    """
    from .config import env_with_fallbacks

    auto_send = env_with_fallbacks(
        "EVE_AUTO_SEND", "EVE_AUTO_LAUNCH", "EVE_AUTO_PUBLISH", default="1"
    )
    if auto_send != "1":
        return {"action": "send_skipped", "reason": "EVE_AUTO_SEND=0"}
    try:
        from . import send
        result = send.send_to_shop(cfg, game, status="draft", journal=journal)
        # ``send_to_shop`` reports Workshop ambiguity/refusal as data so the
        # ship remains durable. A non-throwing failure is still not a send.
        info = result.get("info") or {}
        prior_send = result.get("already_sent") or result.get("already_launched") or {}
        stamp = result.get("stamp") or result.get("receipt") or prior_send.get("stamp") or prior_send.get("receipt") or {}
        ident = (
            info.get("id")
            or info.get("slug")
            or stamp.get("design_id")
            or prior_send.get("id")
        )
        send_id = result.get("send_id") or result.get("intent_id") or prior_send.get("send_id") or prior_send.get("intent_id")
        state = (
            result.get("state")
            or result.get("send_state")
            or result.get("intent_state")
            or prior_send.get("send_state")
            or prior_send.get("intent_state")
        )
        blocked = bool(result.get("blocked"))
        skipped = bool(result.get("skipped"))
        succeeded = result.get("ok") is True
        error = str(result.get("error") or "")[-300:]

        if blocked:
            journal.append(
                "meta",
                action="auto_send_blocked",
                game=game.slug,
                sent=False,
                blocked=True,
                send_id=send_id,
                state=state,
                error=error,
            )
            return {
                "action": "send_blocked",
                "game": game.slug,
                "ok": False,
                "blocked": True,
                "send_id": send_id,
                "state": state,
                "error": error,
            }

        if not succeeded and not skipped:
            journal.append(
                "meta",
                action="auto_send_refused",
                game=game.slug,
                sent=False,
                blocked=False,
                send_id=send_id,
                state=state,
                error=error,
            )
            return {
                "action": "send_refused",
                "game": game.slug,
                "ok": False,
                "blocked": False,
                "send_id": send_id,
                "state": state,
                "error": error,
            }

        if skipped:
            journal.append(
                "meta",
                action="auto_send_skipped",
                game=game.slug,
                sent=False,
                blocked=False,
                send_id=send_id,
                state=state,
                id=ident,
                reason=result.get("reason"),
            )
        else:
            journal.append(
                "meta",
                action="auto_sent",
                game=game.slug,
                sent=True,
                blocked=False,
                send_id=send_id,
                state=state,
                id=ident,
            )
        return {"action": "send_draft", "game": game.slug,
                "ok": succeeded or skipped, "id": ident,
                "skipped": skipped, "blocked": False,
                "send_id": send_id, "state": state}
    except Exception as exc:   # never let a send hiccup take down a ship
        journal.append("meta", action="auto_send_failed", game=game.slug,
                       error=str(exc)[-300:])
        return {"action": "send_failed", "game": game.slug,
                "error": str(exc)[-300:]}


_auto_launch_draft = _auto_send_draft


# --- ideator (brand-new game from an invent action or stage 'queued') ------


def _run_ideator(cfg, m: "meta_mod.Meta", fn_run_agent) -> dict:
    """Invent one new game. The agent writes <dir>/idea.json + rules.md in a
    staging dir; on success we move it to games/<slug> and queue it."""
    from .queue import Queue
    # Never start a second ideator while one is already inventing: an Opus run
    # can outlive a single 30-min drive invocation, and two drives sparking at
    # once would double-pay the ideator and contend on the same staging dir. If a
    # .pending-* dir exists, the work is already in flight — skip.
    if list(cfg.games_dir.glob(".pending-*")):
        _log("ideator: an ideator is already in flight (.pending-*) — skipping")
        return {"role": "ideator", "game": None, "skipped": True,
                "reason": "pending-ideator-in-flight"}
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


def _queue(cfg, m):
    from .queue import Queue
    return Queue(cfg, journal=m.journal)


def _run_brief2(cfg, m, fn_run_agent, slug: str) -> dict:
    gdir = _game_dir(cfg, slug)
    prompt = promptlib.brief_prompt(cfg, game_dir=str(gdir))
    fn_run_agent("brief", prompt, cwd=str(gdir),
                 max_minutes=cfg.brief_max_minutes)
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
    fn_run_agent("builder", prompt, cwd=str(gdir),
                 max_minutes=cfg.builder_max_minutes)
    out = _load_json(gdir / "stage_out.json")
    if not out or not out.get("built"):
        raise DriverStop(f"builder for {slug} produced no staged parts (no build/)")
    # Workshop owns the immutable artifact identity. Eve still owns stage
    # progression and the print gate; this snapshot is evidence, not a second
    # lifecycle write.
    from inventor_workshop.errors import WorkshopError
    from .workshop_bridge import snapshot_built_game
    try:
        artifact = snapshot_built_game(gdir, title=_queue(cfg, m).get(slug).title)
    except (WorkshopError, OSError) as exc:
        # A tree that Workshop cannot safely identify must never advance to a print
        # gate (for example, a builder-created symlink or credential file).
        raise DriverStop(
            f"builder for {slug} produced an artifact Workshop cannot Pack: {exc}"
        ) from exc
    m.journal.append(
        "artifact_snapshot",
        game=slug,
        artifact_sha256=artifact["artifact_sha256"],
        entries=len(artifact["entries"]),
        total_bytes=artifact["total_bytes"],
        producer="inventor_workshop",
    )
    m.record_stage(slug, "build")   # next tick runs the deterministic print gate
    return {
        "role": "builder",
        "game": slug,
        "n_parts": out.get("n_parts"),
        "artifact_sha256": artifact["artifact_sha256"],
    }


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
    the real (no-LLM) fun gate. Only a real llm_table/human evidence passes.
    After the playtest agent writes the engine, we also run a real LLM-player
    table (claude seats over the live interface) when opt-in; a genuine table
    pass is what sets ship. Scripted evidence is recorded but never ships."""
    gdir = _game_dir(cfg, slug)
    prompt = promptlib.playtest_prompt(cfg, game_dir=str(gdir))
    try:
        fn_run_agent("playtest", prompt, cwd=str(gdir))
    except agents.Starved:
        # coding the engine starved -> stop this step, keep the game in playtest
        _queue(cfg, m).release(slug)
        return {"role": "playtest", "game": slug, "result": "starved"}
    q = _queue(cfg, m)
    out = _load_json(gdir / "stage_out.json")
    evidence = None
    if out:
        er = out.get("engine_run") or {}
        scripted = playtest.FunEvidence(
            source=str(er.get("source") or "scripted"),
            games_played=int(er.get("games_played") or er.get("trials") or 0),
            first_seat_wins=float(er.get("first_seat_wins") or 1.0),
            ends=bool(er.get("ends", False)),
            decisiveness=float(er.get("decisiveness") or 0.0),
            ask_to_play_again=float(er.get("ask_to_play_again") or 0.0),
            note=str(er.get("note") or out.get("interpretation") or ""),
        )
        q.record(slug, fun_evidence=q.get(slug).fun_evidence + [{
            "source": scripted.source, "games_played": scripted.games_played,
            "first_seat_wins": scripted.first_seat_wins, "ends": scripted.ends,
            "decisiveness": scripted.decisiveness,
            "ask_to_play_again": scripted.ask_to_play_again,
            "note": scripted.note}])
        evidence = scripted
    # Real LLM-player table over the LIVE engine. Honest: returns standby when the
    # engine lacks a live interface or the table is disabled; standby never ships.
    game = q.get(slug)
    table = playtest.run_player_table(game, cfg)
    if table.source in ("llm_table", "human"):
        q.record(slug, fun_evidence=q.get(slug).fun_evidence + [{
            "source": table.source, "games_played": table.games_played,
            "first_seat_wins": table.first_seat_wins, "ends": table.ends,
            "decisiveness": table.decisiveness,
            "ask_to_play_again": table.ask_to_play_again,
            "note": table.note}])
        evidence = table
    if evidence is None:
        q.release(slug)
        return {"role": "playtest", "game": slug, "result": "no_evidence"}
    gate = playtest.fun_gate(q.get(slug), evidence)
    if gate.passed:
        from .reward import RewardLedger
        RewardLedger(cfg, journal=m.journal).record(
            slug, "fun_pass", evidence=str(evidence))
        shipped = q.ship(slug)
        _auto_send_draft(cfg, shipped, m.journal)
        return {"role": "playtest", "game": slug, "result": "fun_pass",
                "evidence": evidence.source}
    m.journal.append("meta", action="fun_failed", game=slug,
                     reasons=gate.reasons, evidence=evidence.note)
    q.release(slug)
    return {"role": "playtest", "game": slug, "result": "fun_fail",
            "reasons": gate.reasons}


def _run_reader(cfg, m: "meta_mod.Meta", fn_run_agent, slug: str) -> dict:
    """Loop D: the bibliophile. Reads the book currently under study and
    distills it into design learnings + principles recorded in books/state.

    The reader runs in loops/books/ and writes stage_out.json there. Each
    learning is recorded via books.record_learning (tagged to a target_area so
    the rules/brief/playtest lenses can consume it); the reader then marks the
    book done so the shelf advances one book per day. A book is only marked
    done after its learnings were recorded (Loop D's contract)."""
    from . import books, promptlib
    book = books.study_tick(cfg, journal=m.journal)
    if book is None:
        return {"role": "reader", "book": None, "skipped": True,
                "reason": "no book under study"}
    title = book.get("title", "")
    workdir = cfg.root / "loops" / "books"
    workdir.mkdir(parents=True, exist_ok=True)
    prompt = promptlib.reader_prompt(cfg, book=book)
    try:
        fn_run_agent("reader", prompt, cwd=str(workdir))
    except agents.QuotaExhausted:
        raise
    except agents.Starved:
        raise
    except agents.AgentError:
        # LLM step: transient crash retried once, never twice (agents.py).
        fn_run_agent("reader", prompt, cwd=str(workdir))
    out = _load_json(workdir / "stage_out.json")
    learnings = (out or {}).get("learnings") or []
    if not learnings:
        m.journal.append("meta", action="reader_empty", book=title,
                         note="reader wrote no learnings; book stays in_progress")
        return {"role": "reader", "book": title, "learnings": 0,
                "skipped": True, "reason": "reader wrote no learnings"}
    for l in learnings:
        if not isinstance(l, dict) or not l.get("learning"):
            continue
        books.record_learning(
            cfg, book=title, learning=l["learning"],
            target_area=l.get("target_area", "design"),
            mechanic=l.get("mechanic"), theme=l.get("theme"),
            journal=m.journal)
    for pr in (out or {}).get("principles") or []:
        if isinstance(pr, dict) and pr.get("text"):
            books.add_principle(cfg, text=pr["text"], source=title,
                                journal=m.journal)
    books.mark_done(cfg, title, journal=m.journal)
    # Fold the fresh learnings into the policy on the same cadence so the
    # bibliophile's output feeds the rules lens immediately.
    m._flush_learnings()
    return {"role": "reader", "book": title,
            "learnings": len(learnings),
            "principles": len((out or {}).get("principles") or [])}


ROLE_FN = {
    "ideator": _run_ideator,
    "brief": _run_brief2,
    "builder": _run_builder,
    "panel": _run_panel,
    "playtest": _run_playtest,
    "reader": _run_reader,
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


def _taste_bound_runner(cfg, fn_run_agent):
    """Require and preserve Eve's exact root Taste around every model call."""
    from inventor_workshop import load_taste

    def run(role, prompt, **kwargs):
        taste = load_taste(Path(cfg.root))
        marker = "TASTE_SHA256=%s" % taste.sha256
        if marker not in prompt or taste.content not in prompt:
            raise DriverStop(
                "refusing to run %s without Eve's exact root Taste binding" % role
            )
        try:
            return fn_run_agent(role, prompt, **kwargs)
        finally:
            taste.assert_current()

    return run


def evolve(cfg, *, max_steps: int = 1, fn_run_agent=None) -> dict:
    """Advance up to `max_steps` units of work; returns a summary.

    Executes deterministic gates via meta.tick and LLM roles via fn_run_agent
    (injectable for mocks/tests; defaults to agents.run_agent)."""
    fn_run_agent = _taste_bound_runner(cfg, fn_run_agent or agents.run_agent)
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
            except agents.QuotaExhausted as exc:
                m.pause_for_quota(exc)
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

        # quiet / invent when below floor but idle is not actionable here
        done.append(out)
        _log(f"{action}")
        if action in ("invent", "spark"):  # ``spark`` reads old queued output.
            # below the inflight floor -> invent a new game now
            try:
                res = _run_ideator(cfg, m, fn_run_agent)
            except agents.QuotaExhausted as exc:
                m.pause_for_quota(exc)
                done.append({"action": "quota"})
                break
            except agents.Starved:
                done.append({"action": "starved", "role": "ideator"})
                break
            done.append(res)
            _log(f"invent->ideator: {json.dumps(res, default=str)[:200]}")
            continue
        break                            # quiet or terminal

    return {"action": "step", "results": done}
