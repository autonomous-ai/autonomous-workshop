"""Reward function + ledger for Eve's self-improvement.

Each game is an *episode*; each stage-advance is a *step*; publishing a
gated game is the *terminal* with reward. The meta-loop's objective is to
maximize expected discounted return per unit time while holding the quality
bar fixed (cadence is a constraint, not a reward).

The ledger is written ONLY by this module, from the queue's own recorded
state and this module's deterministic rules. A model never reports its own
score. `audit()` cross-checks the ledger against the queue, so a score cannot
be inflated.

Reward design follows the org's failure modes:
  * shipping slop is the main long-term risk -> terminal `ship` only fires
    after every gate, and `fun_pass` (the highest non-terminal term) requires
    external playtest evidence, not self-report;
  * endless polishing is the second risk -> a game that can't pass a stage
    spends a bounded repair/rework budget, then is killed (negative terminal);
  * reward that is written by the thing being rewarded -> ledger is audited.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import queue as queue_mod


@dataclass
class RewardEntry:
    slug: str
    component: str          # novelty_pass | rules_pass | fun_pass | print_pass | cogs_ok | ship | repair_fail | rework | dead_game
    value: float            # immediate (undiscounted) reward for this event
    step: int               # 0-based step ordinal within the episode
    evidence: str = ""      # human-readable pointer to what triggered it
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def to_dict(self):
        return asdict(self)


class RewardLedger:
    """Absolute requires that component weights are read once from cfg.

    `cfg` supplies gamma and weights; `event_values()` maps a component to the
    immediate reward given cfg + game, so the configuration lives in exactly
    one place (config.py) and the rules are deterministic from it.
    """

    def __init__(self, cfg, journal=None):
        self.cfg = cfg
        self.path = cfg.ledger_path
        self.journal = journal
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[RewardEntry] = self._load()

    def _load(self) -> list:
        if not self.path.exists():
            return []
        return [RewardEntry(**e) for e in json.loads(self.path.read_text())]

    def _save(self) -> None:
        self.path.write_text(json.dumps([e.to_dict() for e in self._entries], indent=2))

    def _raw(self, component: str) -> float:
        """Immediate reward for a single component event, from config weights."""
        c = self.cfg
        return {
            "novelty_pass": c.w_novelty,
            "rules_pass": c.w_rules,
            "fun_pass": c.w_fun,
            "print_pass": c.w_print,
            "ship": c.w_ship,
            "repair_fail": c.p_repair_fail,
            "rework": c.p_rework,
            "dead_game": c.p_dead,
        }.get(component, 0.0)

    def record(self, slug: str, component: str, *, step: Optional[int] = None,
               evidence: str = "", value: Optional[float] = None) -> RewardEntry:
        if value is None:
            if component == "cogs_ok":
                value = self._cogs_value(slug)
            else:
                value = self._raw(component)
        next_step = step if step is not None else self._next_step(slug)
        entry = RewardEntry(slug=slug, component=component, value=value,
                            step=next_step, evidence=evidence)
        self._entries.append(entry)
        self._save()
        if self.journal:
            self.journal.append("reward", game=slug, component=component,
                                value=round(value, 4), step=next_step, evidence=evidence)
        return entry

    def _next_step(self, slug: str) -> int:
        return sum(1 for e in self._entries if e.slug == slug)

    def _cogs_value(self, slug: str) -> float:
        """cogs_ok = w_cogs * clip(budget / measured, 0.0, 1.0).

        Cheap, well-under-budget games earn more; over-budget games earn 0
        for this term (the terminal ship still requires it to have shipped).
        """
        game = self._find_game(slug)
        if game is None or game.cogs_usd is None or game.cogs_usd <= 0:
            return 0.0
        ratio = self.cfg.cogs_budget_usd / game.cogs_usd
        return self.cfg.w_cogs * max(0.0, min(1.0, ratio))

    def _find_game(self, slug: str):
        q = queue_mod.Queue(self.cfg)
        return q.get(slug)

    # --- per-episode return -----------------------------------------------
    def game_return(self, slug: str) -> float:
        """Discounted sum of this game's step rewards (episode return)."""
        steps = {}
        for e in self._entries:
            if e.slug == slug:
                steps.setdefault(e.step, 0.0)
                steps[e.step] += e.value
        if not steps:
            return 0.0
        total = 0.0
        for step in sorted(steps):
            total += steps[step] * (self.cfg.gamma ** step)
        return total

    def all_returns(self) -> dict[str, float]:
        return {slug: self.game_return(slug) for slug in self._slugs()}

    def _slugs(self) -> list[str]:
        seen = []
        for e in self._entries:
            if e.slug not in seen:
                seen.append(e.slug)
        return seen

    def cumulative_return(self) -> float:
        return sum(self.game_return(s) for s in self._slugs())

    # --- aggregates for self-improvement ----------------------------------
    def loss_by_component(self) -> list[dict]:
        """Where discounted reward is being lost, per component.

        Positive terms that never fired (e.g. `fun_pass` never awarded) count
        as lost *opportunity*; negative penalties count as *spent*. Both tell
        improve.py where the dominant loss lives.
        """
        slugs = self._slugs()
        loss = {}
        for e in self._entries:
            loss.setdefault(e.component, {"fired": 0, "discounted": 0.0})
            loss[e.component]["fired"] += 1
            loss[e.component]["discounted"] += e.value * (self.cfg.gamma ** e.step)
        return [{"component": k, **v} for k, v in sorted(loss.items(), key=lambda kv: kv[1]["discounted"])]

    def summary(self) -> dict:
        shipped = [s for s in self._slugs() if (self._find_game(s) or queue_mod.Game(slug=s)).stage == "ship"]
        killed = [s for s in self._slugs() if (self._find_game(s) or queue_mod.Game(slug=s)).stage == "killed"]
        gs = self._slugs()
        return {
            "games": gs,
            "shipped": shipped,
            "killed": killed,
            "cumulative_return": round(self.cumulative_return(), 4),
            "per_game": {s: round(self.game_return(s), 4) for s in gs},
            "loss_by_component": self.loss_by_component(),
        }


def audit(cfg, ledger: Optional[RewardLedger] = None) -> list[str]:
    """Verify the ledger against the queue and the reward rules.

    Returns a list of problems (empty == clean). Guards against an inflated
    score: every positive reward present in the ledger must have a matching,
    verifiable queue state.
    """
    ledger = ledger or RewardLedger(cfg)
    q = queue_mod.Queue(cfg)
    problems = []

    # terminal ship must correspond to a game in the queue at stage 'ship'
    for e in ledger._entries:
        if e.component == "ship":
            g = q.get(e.slug)
            if not g or g.stage != "ship":
                problems.append(f"ship reward for {e.slug} but game not at stage 'ship'")
        if e.component == "dead_game":
            g = q.get(e.slug)
            if not g or g.stage != "killed":
                problems.append(f"dead_game reward for {e.slug} but game not killed")
        if e.component == "fun_pass":
            g = q.get(e.slug)
            if not g or not g.fun_evidence:
                problems.append(f"fun_pass for {e.slug} but no playtest evidence recorded")
    return problems
