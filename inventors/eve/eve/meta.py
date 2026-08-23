"""meta.py — Eve's meta-loop: the 24/7 supervisor.

Eve is a meta-loop: it runs several smaller loops and feeds their outputs into
one another. This module is the workshop steward that keeps them running — the scheduler,
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

`tick()` performs exactly ONE unit of work per call, in priority order. The
launchd job invokes `eve drive --steps 1` every 30 minutes; that drive calls
one tick, which either does one step or reports why it is quiet. A heartbeat is
stamped before any precondition so the watchdog can distinguish "alive but
idle" from "dead" (text2cad receipt, mirrored from Bob).
"""
from __future__ import annotations

import json
import os
import re
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


_RESET_HINT_RE = re.compile(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", re.IGNORECASE)


def _parse_reset_hint(hint: str) -> Optional[datetime]:
    """Turn a wall-clock reset hint like '6:20pm' into the next UTC datetime
    it describes, using the machine's local timezone. Returns None if unparsable."""
    m = _RESET_HINT_RE.match((hint or "").strip())
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2) or 0)
    ampm = (m.group(3) or "").lower()
    if ampm == "pm" and hh != 12:
        hh += 12
    elif ampm == "am" and hh == 12:
        hh = 0
    now = datetime.now().astimezone()
    try:
        target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    except ValueError:
        return None
    if target <= now:
        target += timedelta(days=1)
    return target.astimezone(timezone.utc)


class Meta:
    """Scheduler + heartbeat + cadence + reward-recording workshop steward."""

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
        work still proves the scheduled drive fired (text2cad's contract)."""
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

    # --- quota pause -----------------------------------------------------
    def pause_for_quota(self, exc) -> None:
        """Persist DAYBOOK quota_until from a QuotaExhausted's reset hint so
        the tick loop no-ops (instead of re-invoking a costly brief) until the
        subscription window reopens. Falls back to now + 60 min when the CLI
        did not disclose the reset time."""
        until = _now() + timedelta(minutes=60)
        hint = getattr(exc, "reset_hint", None)
        if hint:
            parsed = _parse_reset_hint(hint)
            if parsed is not None:
                until = parsed
        book = self._read_daybook()
        book["quota_until"] = _iso(until)
        self._write_daybook(book)
        self.journal.append("meta", action="quota_paused",
                            until=_iso(until), hint=hint)

    def quota_until(self) -> Optional[datetime]:
        return _parse(self._read_daybook().get("quota_until"))

    def quota_paused(self) -> dict:
        """Return the pause window when the daybook says we are still blocked;
        empty dict when it is safe to run LLM work again."""
        until = self.quota_until()
        if until is not None and _now() < until:
            return {"until": until, "until_iso": _iso(until)}
        return {}

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

    def _study_dispatch(self) -> dict:
        """Loop D cadence day: return the one-unit reader work.

        Advances the shelf exactly one book per day (books.study_tick marks a
        single book in_progress) and stamps the daily books cadence so the
        meta never loops on the same book. When a book is under study the work
        is a READER agent dispatch (the driver fulfills it and the reader
        records learnings then marks the book done); when the shelf is empty it
        is a bookkeeping-only 'study' so a tick still does one unit.
        """
        from . import books
        book = books.study_tick(self.cfg, journal=self.journal)
        self.heartbeat(last_books_study=_iso(_now()))
        if book is None:
            return {"action": "study", "book": None, "note": "shelf empty"}
        return {"action": "dispatch", "role": "reader",
                "book": book.get("title"), "author": book.get("author", "")}

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
        signals new invention when the queue is empty / below the inflight floor).
        """
        from .queue import Queue
        q = Queue(self.cfg, journal=self.journal)
        game = q.next()
        if game is not None:
            return self._plan_stage(game)
        return {"action": "invent", "phase": "invent"} if self._below_floor(q) else None

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
        elif getattr(result, "measurable", True) is False:
            # not enough to judge (e.g. no meshes in build/ yet): keep the
            # game active but don't spend the kill cost; a later repaired
            # build may become measurable. Never a reward term.
            self.journal.append("meta", action="gate_immeasurable",
                                game=game.slug, gate=gate,
                                reasons=result.reasons)
        else:
            # A deterministic gate cannot pass by re-running it — no LLM
            # changes state between attempts. A failed hard gate is terminal:
            # spend the design's kill cost with a stated reason and free the
            # queue. Without this a stuck game is re-judged forever and
            # starves every other loop (the Loop-A/B/C/D meta).
            self._kill_gate_failure(game, gate, result, q)
        return {"gate": gate, "passed": result.passed, "reasons": result.reasons,
                "next_stage": next_stage if result.passed else game.stage}

    def _kill_gate_failure(self, game, gate, result, q) -> None:
        """Terminate a game that failed a hard deterministic gate.

        Records the design's terminal `dead_game` penalty and marks the game
        `killed` with a stated reason so the queue keeps moving. `rework` /
        `repair_fail` rewards stay reserved for the LLM rework/repair loops
        that have yet to be wired (see DESIGN.md); a no-LLM gate re-run can
        never change the verdict.
        """
        from .reward import RewardLedger
        reason = "; ".join(result.reasons) or f"{gate}-gate failed"
        RewardLedger(self.cfg, journal=self.journal).record(
            game.slug, "dead_game", evidence=f"{gate}-gate: {reason}")
        q.kill(game.slug, reason=f"{gate}-gate: {reason}")
        self.journal.append("meta", action="game_killed", game=game.slug,
                            gate=gate, reasons=result.reasons)

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

        # Quota pause: never invoke a costly LLM step into a closed window.
        paused = self.quota_paused()
        if paused:
            self.journal.append("meta", action="quota_paused",
                                until=paused["until_iso"])
            return {"action": "quota", "until": paused["until_iso"]}

        # 1) Finishing beats starting: advance the in-flight game pipeline.
        decision = self.next_game_action()
        if decision is not None and decision.get("action") != "invent":
            if decision["action"] == "gate":
                from .queue import Queue
                game = Queue(self.cfg, journal=self.journal).get(decision["game"])
                # print gate needs the real build dir, else it can never see meshes
                gdir = self.cfg.games_dir / game.slug if game else None
                out = self.run_gate(game, decision["gate"], game_dir=gdir)
                out["action"] = "gate"
                return out
            # agent stages: dispatch only when the driver is allowed to run it
            if run_agent:
                return {"action": "dispatch", **decision}
            return {"action": "dispatch_pending", **decision}

        # Pipeline idle (or below the inflight floor): honor the cadence loops
        # BEFORE inventing a fresh game, so Loop D (books) and the weekly
        # improve are never starved by an always-hot queue. Eve invents a new
        # game only when the rest of the meta is current (quality>quantity).
        # 2) Loop D: one book per day (dispatch the reader agent).
        if self.books_due():
            d = self._study_dispatch()
            if d.get("action") == "dispatch":
                if run_agent:
                    return d
                return {"action": "dispatch_pending", **d}
            return d

        # 3) Weekly self-improvement.
        if self.improve_due():
            result = self.improve()
            return {"action": "improve",
                    "doc_writes": len(result["doc_writes"]),
                    "code_proposals": len(result["code_proposals"])}

        # 4) Weekly ship-check (cadence constraint).
        if self.ship_check_due():
            return {"action": "ship_check", **self.ship_check()}

        # 5) All of the meta is current and the queue is below the inflight
        #    floor -> invent a new game to keep the loop alive.
        if decision is not None and decision.get("action") == "invent":
            return decision

        self.journal.append("meta", action="quiet", note="everything current")
        return {"action": "quiet"}
