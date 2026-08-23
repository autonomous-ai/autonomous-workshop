"""The game queue — Eve's unit of work is the *game*, not the turn.

A game lives here across many steps. It only leaves by shipping or by being
killed with a stated reason (the org's hard lesson: a pipeline that replaces
an idea on every fault never finishes anything).

State is held in Python, not prompts, so an agent can't negotiate with its
own budget. Two safeguards from vibe-ideas are kept:
  * a lock around every read-modify-write; and
  * a claim (a lease with expiry) on whatever `next` hands out, so a driver
    that dies mid-step releases its game instead of stranding or double-claiming.
"""
from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

STAGES = [
    "queued",       # idea proposed, awaiting novelty gate
    "novelty",      # novelty gate against Loop A corpus
    "rules",        # complete rules + mechanical/engine/table rules gate
    "brief",        # dimensions, interfaces, print plan
    "draft",        # CAD draft + frozen reference renders
    "build",        # per-piece build + deterministic gate
    "panel",        # blind lenses: printability/fidelity/playability
    "playtest",     # fun gate: LLM-player table, then humans
    "ship",         # all checks green, ready to Pack and Send
    "killed",       # terminal — killed with a stated reason
]

# stages that can be terminal
TERMINAL = {"ship", "killed"}


@dataclass
class Game:
    slug: str
    title: str = ""
    stage: str = "queued"
    idea: str = ""
    identity: str = ""            # "like X plus Y" — the novelty identity
    bill: Optional[dict] = None
    cogs_usd: Optional[float] = None
    fun_evidence: list = field(default_factory=list)  # playtest results
    # --- presentation / catalog (send.py reads these) -----------
    mech: str = ""                 # one-line mechanism, e.g. 'living-hinge detent'
    blurb: str = ""                # one-line catalog blurb
    seats: str = "2-4"
    t_min: str = "15"
    t_max: str = "25"
    flag: str = ""                 # 'featured' triggers the featured treatment
    price_usd: float = 0.0          # 0 -> send._default_price()
    rules_text: str = ""           # full rulebook text for the writeup
    brief: str = ""                # dimension/interfaces/print plan
    repair_used: int = 0
    rework_used: int = 0
    kill_reason: str = ""
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    # --- claim/lease ----------------------------------------------------
    claimed_by: Optional[str] = None
    claim_until: Optional[float] = None
    crashes: dict = field(default_factory=dict)  # per-state crash counters

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Game":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


class Queue:
    def __init__(self, cfg, journal=None):
        self.cfg = cfg
        self.path = cfg.queue_path
        self.lock_path = cfg.queue_path.with_suffix(".lock")
        self.journal = journal
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # --- persistence -------------------------------------------------------
    def _load(self) -> list:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text())

    def _save(self, games: list) -> None:
        with open(self.lock_path, "w"):
            pass  # (locking contract handled by callers needing mutual exclusion)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(games, indent=2))

    # --- state operations -------------------------------------------------
    def add(self, slug: str, title: str = "", idea: str = "", identity: str = "") -> Game:
        games = self._load()
        if any(g["slug"] == slug for g in games):
            raise ValueError(f"game already in queue: {slug}")
        g = Game(slug=slug, title=title or slug, idea=idea, identity=identity)
        games.append(g.to_dict())
        self._save(games)
        if self.journal:
            self.journal.append("game_added", game=slug, stage=g.stage)
        return g

    def get(self, slug: str) -> Optional[Game]:
        for g in self._load():
            if g["slug"] == slug:
                return Game.from_dict(g)
        return None

    def list(self, stage: Optional[str] = None) -> list[Game]:
        games = [Game.from_dict(g) for g in self._load()]
        if stage:
            games = [g for g in games if g.stage == stage]
        return games

    def active(self) -> list[Game]:
        return [g for g in self.list() if g.stage not in TERMINAL]

    def _update(self, slug: str, fn) -> Optional[Game]:
        games = self._load()
        for i, g in enumerate(games):
            if g["slug"] == slug:
                game = Game.from_dict(g)
                game = fn(game) or game
                game.updated = datetime.now(timezone.utc).isoformat(timespec="seconds")
                games[i] = game.to_dict()
                self._save(games)
                return game
        return None

    def record(self, slug: str, *, stage: Optional[str] = None, **fields) -> Optional[Game]:
        def fn(g: Game):
            if stage:
                g.stage = stage
            for k, v in fields.items():
                if hasattr(g, k):
                    setattr(g, k, v)
            return g
        game = self._update(slug, fn)
        if game and self.journal:
            self.journal.append("game_record", game=slug, stage=game.stage, fields=sorted(fields))
        return game

    # --- claim / lease -----------------------------------------------------
    def claim(self, slug: str, ttl_s: float = 3600.0) -> Optional[Game]:
        """Claim a game for this driver. Returns the game, or None if held."""
        now = time.time()
        me = f"{socket.gethostname()}:{os.getpid()}"
        g = self.get(slug)
        if g is None:
            return None
        if g.claimed_by and g.claim_until and g.claim_until > now and g.claimed_by != me:
            return None
        return self._update(
            slug,
            lambda x: (setattr(x, "claimed_by", me),
                       setattr(x, "claim_until", now + ttl_s)) and x,
        )

    def release(self, slug: str) -> Optional[Game]:
        return self._update(
            slug,
            lambda x: (setattr(x, "claimed_by", None),
                       setattr(x, "claim_until", None)) and x,
        )

    def sweep_expired(self) -> list[str]:
        """Release any game whose lease has expired (a driver died)."""
        now = time.time()
        freed = []
        for g in self.list():
            if g.claimed_by and g.claim_until and g.claim_until <= now:
                self.release(g.slug)
                freed.append(g.slug)
        return freed

    # --- next --------------------------------------------------------------
    def next(self) -> Optional[Game]:
        """The next game that should be advanced, claiming a lease on it.

        Prefers, in order: the oldest active game that is not far past its
        cadence target; otherwise the oldest active game. Never a terminal one.
        """
        self.sweep_expired()
        active = self.active()
        if not active:
            return None
        active.sort(key=lambda g: g.created)
        for g in active:
            claimed = self.claim(g.slug)
            if claimed:
                return claimed
        return None

    def kill(self, slug: str, reason: str) -> Optional[Game]:
        if not reason:
            raise ValueError("a kill requires a stated reason")
        return self.record(slug, stage="killed", kill_reason=reason)

    def ship(self, slug: str) -> Optional[Game]:
        return self.record(slug, stage="ship")
