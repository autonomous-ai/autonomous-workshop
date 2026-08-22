"""Loop A — the board-game history study (the historian).

Studies the board games of thousands of years (Senet, Go, Mancala, modern
Euros) as a *design corpus*, not trivia, and turns them into three things the
rest of Eve is held to:

  * a mechanics taxonomy with the design space it opens (decision space, cost,
    audience, canonical examples) so the ideator can honestly say
    "this is like X plus Y, which no one has combined";
  * a saturation map: which mechanics and themes are already owned or so common
    in the world that they are not novel (the novelty axes);
  * a running history of the games actually studied.

Loop A's corpus is the ground truth for the *novelty gate* in Loop C: an idea
must be new against the corpus, not just new to Eve. Therefore this module is
the only writer of the corpus DB and the ideator never edits it.

State lives in corpus/db/corpus.json, seeded from corpus/seed/ on first run.
Everything here is deterministic, no-LLM code.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .journal import open_journal

SCHEMA_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def empty_corpus() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated": _now(),
        "mechanics": {},        # slug -> {name, space, cost, audience, examples}
        "themes": [],           # known theme list
        "owned": {"mechanics": [], "themes": []},     # already used by Eve games
        "saturated": {"mechanics": [], "themes": []}, # too common to be novel
        "novelty_axes": [],     # the dimensions along which an idea must be new
        "studied": [],          # history DB: games actually studied
    }


def _ensure(cfg) -> dict:
    cfg.corpus_db.parent.mkdir(parents=True, exist_ok=True)
    if not cfg.corpus_db.exists():
        seed(cfg, empty_corpus())
    return json.loads(cfg.corpus_db.read_text())


def load(cfg) -> dict:
    """Load the corpus DB, seeding it from corpus/seed/ if absent."""
    return _ensure(cfg)


def save(cfg, corpus: dict) -> None:
    corpus["updated"] = _now()
    cfg.corpus_db.parent.mkdir(parents=True, exist_ok=True)
    cfg.corpus_db.write_text(json.dumps(corpus, indent=2))


def seed(cfg, corpus: Optional[dict] = None) -> None:
    """Bootstrap the corpus DB from the bundled seed files.

    The seed is the historian's initial hand-off from the human world: the
    taxonomy and the saturated map are the floor everything else is measured
    against. Seeding only happens when the DB does not already exist.
    """
    corpus = corpus or empty_corpus()
    seed_dir = cfg.seed_dir
    if seed_dir.exists():
        for path in sorted(seed_dir.glob("*.json")):
            data = json.loads(path.read_text())
            if "mechanics" in data:
                corpus["mechanics"].update(data["mechanics"])
            for key in ("themes", "saturated", "novelty_axes"):
                if key in data:
                    corpus[key] = _merge_list(corpus.get(key, []), data[key])
    cfg.corpus_db.parent.mkdir(parents=True, exist_ok=True)
    cfg.corpus_db.write_text(json.dumps(corpus, indent=2))


def _merge_list(a: list, b: list) -> list:
    out = list(a)
    for item in b:
        if item not in out:
            out.append(item)
    return out


def record_study(cfg, *, title: str, mechanic: str, theme: str, source: str = "",
                 note: str = "") -> None:
    """Record a historical game that Loop A studied, so novelty has a memory."""
    corpus = _ensure(cfg)
    entry = {
        "title": title,
        "mechanic": mechanic,
        "theme": theme,
        "source": source,
        "note": note,
        "at": _now(),
    }
    if not any(e.get("title") == title for e in corpus["studied"]):
        corpus["studied"].append(entry)
        save(cfg, corpus)
        open_journal(cfg).append("corpus_study", title=title, mechanic=mechanic)


def own(cfg, *, mechanic: Optional[str] = None, theme: Optional[str] = None,
        journal=None) -> None:
    """Mark a mechanic/theme as already owned by Eve's shipped/proposed games.

    Once something is owned it is off the table for future novelty claims, so
    Eve cannot re-invent the same game under a new title.
    """
    corpus = _ensure(cfg)
    changed = False
    if mechanic:
        if mechanic not in corpus["owned"]["mechanics"]:
            corpus["owned"]["mechanics"].append(mechanic)
            changed = True
    if theme:
        if theme not in corpus["owned"]["themes"]:
            corpus["owned"]["themes"].append(theme)
            changed = True
    if changed:
        save(cfg, corpus)
        (journal or open_journal(cfg)).append(
            "corpus_own", mechanic=mechanic, theme=theme)


def saturation(cfg) -> dict:
    """The novelty axes: what is owned and what is saturated in the world."""
    corpus = _ensure(cfg)
    return {
        "owned": corpus["owned"],
        "saturated": corpus["saturated"],
        "novelty_axes": corpus["novelty_axes"],
        "mechanics": sorted(corpus["mechanics"]),
    }


def add_mechanic(cfg, slug: str, *, name: str, space: str, cost: str,
                 audience: str, examples: list, journal=None) -> None:
    """Loop A populates the taxonomy. The ideator never edits this."""
    corpus = _ensure(cfg)
    corpus["mechanics"][slug] = {
        "name": name, "space": space, "cost": cost,
        "audience": audience, "examples": examples,
    }
    save(cfg, corpus)
    (journal or open_journal(cfg)).append("corpus_mechanic", slug=slug, name=name)
