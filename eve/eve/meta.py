"""meta.py — Eve's meta-loop: the 24/7 supervisor.

Eve is a meta-loop: it runs several smaller loops and feeds their outputs into
one another. This module is the *core* that keeps them running — the scheduler,
the heartbeat, the cadence constraints, and the reward-recording bookkeeping.
Everything here is deterministic, no-LLM. The *work* of each step (inventing,
writing rules, building CAD, running a real player table) is done by subagents
the driver (`eve.py`) dispatches; meta decides *what* to run next and records
what came back.

Cadence is a CONSTRAINT, not a reward (DESIGN.md ss.3.4):
  * ship >= 1 game / week  (a weekly check reports the shortfall, it never
    forces slop through the gates);
  * advance a game >= 1 stage / day (finishing beats starting);
  * one book worked / day (Loop D is deliberately the slowest loop);
  * one self-improvement session / week (it spends the most and rushes worst).

`tick()` performs exactly ONE unit of work per call, in priority order, so a
launchd 30-minute cadence is safe to fire around the clock — each tick either
does one step or reports why it is quiet. A heartbeat is stamped before any
precondition so the watchdog can distinguish "alive but idle" from "dead"
(text2cad receipt, mirrored from Bob).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .journal import open_journal

# Where the heartbeat + cadence bookkeeping lives. Written by every tick even
# when the tick is a no-op, so the watchdog can tell alive-but-idle from dead.
DAYBOOK_NAME = "DAYBOOK.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        when = datetime.fromisoformat(value)
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when


class Meta:
    """Scheduler + heartbeat + cadence + reward-recording core."""

    def __init__(self, cfg, journal=None):
        self.cfg = cfg
        self.journal = journal or open_journal(cfg)
        self._daybook_path = cfg.root / "state" / DAYBOOK_NAME

    # --- heartbeat / cadence state ---------------------------------------
    def _read_daybook(self) -> dict:
        try:
            return json.loads(self._daybook_path.read_text())
        except (OSError, ValueError):
            return {}

    def _write_daybook(self, book: dict) -> None:
        self._daybook_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._daybook_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(book, indent=2, sort_keys=True))
        os.replace(tmp, self._daybook_path)

    def heartbeat(self, **extra) -> dict:
        """Stamp the heartbeat BEFORE any precondition. A tick that skips all
        work still proves launchd fired (text2cad's watchdog contract)."""
        book = self._read_daybook()
        book["heartbeat"] = _iso(_now())
        book.update(extra)
        self._write_daybook(book)
        return book

    def _days_since(self, key: str) -> Optional[float]:
        when = _parse(self._read_daybook().get(key))
        if when is None:
            return None
        return (_now() - when).total_seconds() / 86400.0

    def audit_ok(self):
        """The ledger must be verifiable before any work (never improve from
        an inflatable score). Returns (ok, problems)."""
        from .reward import audit
        problems = audit(self.cfg)
        return (not problems), problems

    def books_due(self) -> bool:
        """Loop D: one book worked per day."""
        days = self._days_since("last_books_study")
        return days is None or days >= 1.0

    def improve_due(self) -> bool:
        """One self-improvement session per week."""
        days = self._days_since("last_improve")
        return days is None or days >= self.cfg.ship_every_days

    def ship_check_due(self) -> bool:
        days = self._days_since("last_ship_check")
        return days is None or days >= self.cfg.ship_every_days

    # --- Loop D -----------------------------------------------------------
    def study_tick(self):
        """Exactly one book unit per call; marks the daily cadence in the
        DAYBOOK. Returns the book under study, or None if the shelf is empty."""
        from . import books
        book = books.study_tick(self.cfg, journal=self.journal)
        if book is not None:
            # Fold any recorded-but-unapplied learning into the policy on the
            # same cadence (the bibliophile's output feeds the rules lens).
            self._flush_learnings()
        book_back = self.heartbeat(last_books_study=_iso(_now()))
        self.journal.append("meta", action="study_tick",
                            book=(book or {}).get("title"))
        return book, book_back

    def _flush_learnings(self):
        from . import books
        try:
            for lesson in books.unapplied_learnings(self.cfg):
                books.apply_learning(self.cfg, lesson["id"])
                self.journal.append("meta", action="books_learning_applied",
                                    id=lesson["id"])
        except Exception as exc:  # Loop D must never take down a tick
            self.journal.append("meta", action="books_flush_skipped",
                                error=str(exc))

    # --- self-improvement (weekly) ---------------------------------------
    def improve(self):
        from .improve import run
        result = run(self.cfg, journal=self.journal)
        self.heartbeat(last_improve=_iso(_now()))
        self.journal.append("meta", action="improve",
                            doc_writes=len(result["doc_writes"]),
                            code_proposals=len(result["code_proposals"]),
                            skipped=len(result["skipped"]))
        return result

    # --- weekly ship-check (cadence constraint, not a reward term) --------
    def ship_check(self):
        from .queue import Queue
        q = Queue(self.cfg, journal=self.journal)
        shipped = [g for g in q.list() if g.stage == "ship"]
        days = self._days_since("last_ship_check")
        self.heartbeat(last_ship_check=_iso(_now()))
        out = {"shipped_count": len(shipped), "rolling_days": days}
        if len(shipped) == 0 and days is None:
            self.journal.append("meta", action="ship_check",
                                outcome="warmup", note="no ships yet, week 1")
        self.journal.append("meta", action="ship_check", **out)
        return out

    # --- the per-game pipeline (Loop C) -----------------------------------
    def next_game_action(self) -> Optional[dict]:
        """Decide the next unit of work for the in-flight game pipeline.

        Returns a dispatch dict the driver executes, or None when there is no
        actionable game. Deterministic: selects the oldest active game (or
        signals a spark when the queue is empty / below the inflight floor).
        """
        from .queue import Queue
        q = Queue(self.cfg, journal=self.journal)
        game = q.next()
        if game is not None:
            return self._plan_stage(game)
        return {"action": "spark", "phase": "invent"} if self._below_floor(q) else None

    def _below_floor(self, q) -> bool:
        max_inflight = int(os.environ.get("EVE_MAX_INFLIGHT", "2"))
        return len(q.active()) < max_inflight

    def _plan_stage(self, game) -> dict:
        """Map a game's stage to the next concrete step: a deterministic gate
        we can run now, or an agent dispatch the driver must fulfill."""
        plan = {"game": game.slug, "stage": game.stage}
        gates = {
            "novelty": "novelty",
            "rules": "rules",
            "build": "print",
        }
        if game.stage in gates:
            plan.update({"action": "gate", "gate": gates[game.stage]})
            return plan
        # LLM-dependent stages are dispatched to a subagent; the driver runs
        # the agent and records the outcome back through meta.record_*.
        role = {
            "queued": "ideator",
            "brief": "brief",
            "draft": "builder",
            "panel": "panel",
            "playtest": "playtest",
        }.get(game.stage, "ideator")
        plan.update({"action": "dispatch", "role": role})
        return plan

    # --- deterministic gates (no-LLM) + reward recording ------------------
    def run_gate(self, game, gate: str, *, game_dir: Optional[Path] = None) -> dict:
        """Run one deterministic gate. On pass, advances the game a stage and
        records the matching reward term. Returns a result dict."""
        from . import gates
        if gate == "novelty":
            from .corpus import load as corpus_load
            result = gates.novelty_gate(game, corpus_load(self.cfg))
            component, next_stage, evidence = "novelty_pass", "rules", "corpus"
        elif gate == "rules":
            result = gates.rules_gate(game)
            component, next_stage, evidence = "rules_pass", "brief", "rules"
        elif gate == "print":
            result = gates.print_gate(game, game_dir=game_dir)
            component, next_stage, evidence = "print_pass", "panel", "print"
        else:
            return {"result": False, "note": f"unknown gate {gate}"}

        from .queue import Queue
        from .reward import RewardLedger
        q = Queue(self.cfg, journal=self.journal)
        q.release(game.slug)
        if result.passed:
            RewardLedger(self.cfg, journal=self.journal).record(
                game.slug, component, evidence=evidence)
            q.record(game.slug, stage=next_stage)
        else:
            self.journal.append("meta", action="gate_failed",
                                game=game.slug, gate=gate,
                                reasons=result.reasons)
        return {"gate": gate, "passed": result.passed, "reasons": result.reasons,
                "next_stage": next_stage if result.passed else game.stage}

    # --- record a stage advanced by an agent dispatch ---------------------
    def record_stage(self, slug: str, stage: str, *, component: Optional[str] = None,
                     evidence: str = "") -> None:
        """Advance a game to `stage` after an agent finished its step, and
        optionally record the reward the step earned."""
        from .queue import Queue
        from .reward import RewardLedger
        Queue(self.cfg, journal=self.journal).release(slug)
        Queue(self.cfg, journal=self.journal).record(slug, stage=stage)
        if component:
            RewardLedger(self.cfg, journal=self.journal).record(
                slug, component, evidence=evidence)
        self.journal.append("meta", action="stage_recorded", game=slug,
                            stage=stage, component=component)

    # --- the one-unit-of-work tick ----------------------------------------
    def tick(self, *, run_agent: bool = False) -> dict:
        """Perform exactly ONE unit of work, in priority order. Returns a
        dict describing what happened (or why the tick is quiet)."""
        self.heartbeat()
        book = self._read_daybook()

        ok, problems = self.audit_ok()
        if not ok:
            self.journal.append("meta", action="halted", reason="audit_failed",
                                problems=problems[:3])
            return {"action": "halted", "problems": problems}

        # 1) Finishing beats starting: advance the in-flight game pipeline.
        decision = self.next_game_action()
        if decision is not None:
            if decision["action"] == "gate":
                from .queue import Queue
                game = Queue(self.cfg, journal=self.journal).get(decision["game"])
                out = self.run_gate(game, decision["gate"])
                out["action"] = "gate"
                return out
            # agent stages: dispatch only when the driver is allowed to run it
            if run_agent:
                return {"action": "dispatch", **decision}
            return {"action": "dispatch_pending", **decision}

        # 2) Loop D: one book per day.
        if self.books_due():
            study, _ = self.study_tick()
            return {"action": "study", "book": (study or {}).get("title")}

        # 3) Weekly self-improvement.
        if self.improve_due():
            result = self.improve()
            return {"action": "improve",
                    "doc_writes": len(result["doc_writes"]),
                    "code_proposals": len(result["code_proposals"])}

        # 4) Weekly ship-check (cadence constraint).
        if self.ship_check_due():
            return {"action": "ship_check", **self.ship_check()}

        self.journal.append("meta", action="quiet", note="everything current")
        return {"action": "quiet"}
