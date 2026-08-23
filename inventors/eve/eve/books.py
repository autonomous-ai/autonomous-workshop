"""Loop D — the great-books study (the bibliophile loop).

Studies the best books about tabletop and board gaming, in every register the
hobby has been written about: its history and culture, its design theory, and
its science. The reading list is seeded from the owner's canonical shelf
(corpus/seed/books.json): James Wallis, Marcus du Sautoy, Ian Livingstone,
Geoff Engelstein, Raph Koster, Elias/Garfield/Gutschera, and Daniel Solis.

This loop is Loop A's richer sibling. Loop A studies *games* and produces the
mechanics taxonomy and the novelty axes; Loop D studies *writing about games*
and produces:
  * distilled design principles (long-lived, reused by the rules lens);
  * concrete learnings tagged to a target area (rules, brief, playtest, fun)
    that feed the per-game pipeline (Loop C) and can graduate into the harness,
    exactly the way Loop B lessons do.

Cadence is steady and slow, matching the quality-over-quantity rule: the
meta-loop calls `study_tick()` at most once a day, works a single book at a
time, and a book is only marked done after its learnings have been recorded.
Everything here is deterministic, no-LLM bookkeeping; the *reading* is done by
the book-reading agent, and this module records what it returns.

State lives in loops/books/state.json, seeded from corpus/seed/books.json.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .journal import open_journal

SCHEMA_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _state(cfg) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated": _now(),
        "reading_list": [],   # {title, author, category, why, status, order}
        "learnings": [],      # {id, book, learning, target_area, mechanic, theme, repeat, at}
        "principles": [],     # distilled long-lived principles
    }


def _ensure(cfg) -> dict:
    path = cfg.root / "loops" / "books" / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(_state(cfg), indent=2))
    return json.loads(path.read_text())


def _path(cfg) -> Path:
    return cfg.root / "loops" / "books" / "state.json"


def load(cfg) -> dict:
    state = _ensure(cfg)
    if not state["reading_list"]:
        seed_reading_list(cfg)
        state = _ensure(cfg)
    return state


def save(cfg, state: dict) -> None:
    state["updated"] = _now()
    _path(cfg).parent.mkdir(parents=True, exist_ok=True)
    _path(cfg).write_text(json.dumps(state, indent=2))


def seed_reading_list(cfg, journal=None) -> int:
    """Load the canonical reading list from the seed file (once)."""
    state = _ensure(cfg)
    if state["reading_list"]:
        return len(state["reading_list"])
    seed_file = cfg.seed_dir / "books.json"
    if not seed_file.exists():
        return 0
    data = json.loads(seed_file.read_text())
    for book in data["reading_list"]:
        book.setdefault("status", "unread")
        state["reading_list"].append(book)
    save(cfg, state)
    (journal or open_journal(cfg)).append(
        "books_seed", n_books=len(state["reading_list"]))
    return len(state["reading_list"])


def reading_list(cfg) -> list[dict]:
    return load(cfg)["reading_list"]


def next_up(cfg) -> Optional[dict]:
    """The next book to study: first unread by its shelf order."""
    for b in sorted(load(cfg)["reading_list"], key=lambda x: x.get("order", 0)):
        if b.get("status") == "unread":
            return b
    return None


def _find(cfg, title: str):
    for b in load(cfg)["reading_list"]:
        if b.get("title") == title:
            return b
    return None


def mark_started(cfg, title: str, journal=None) -> bool:
    state = load(cfg)
    for b in state["reading_list"]:
        if b.get("title") == title:
            b["status"] = "in_progress"
            save(cfg, state)
            (journal or open_journal(cfg)).append("books_started", book=title)
            return True
    return False


def mark_done(cfg, title: str, journal=None) -> bool:
    state = load(cfg)
    for b in state["reading_list"]:
        if b.get("title") == title:
            b["status"] = "done"
            save(cfg, state)
            (journal or open_journal(cfg)).append("books_done", book=title)
            return True
    return False


def study_tick(cfg, journal=None) -> Optional[dict]:
    """Advance the great-books loop by exactly one unit of work.

    The cadence primitive the meta-loop calls **at most once a day** (slow and
    steady, matching quality-over-quantity). Exactly one and no more:

      * if a book is already `in_progress`, it is returned unchanged so the
        book-reading agent finishes *that* book before the next one starts
        (a book is only ever `done` after its learnings were recorded);
      * otherwise the next `unread` book by shelf order is started
        (`unread -> in_progress`) and returned.

    Returns the book currently under study, or None when the whole reading
    list is exhausted (the meta-loop then replenishes the list from the
    growing canonical canon). Deterministic, no-LLM bookkeeping; the actual
    *reading* is done by the book-reading agent, which records learnings and
    then calls `mark_done`.
    """
    state = load(cfg)
    for b in state["reading_list"]:
        if b.get("status") == "in_progress":
            return b
    book = next_up(cfg)
    if book is None:
        return None
    mark_started(cfg, book["title"], journal=journal)
    return _find(cfg, book["title"])


def _slugify(text: str, n: int = 32) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:n] or "learning"


def record_learning(cfg, *, book: str, learning: str,
                    target_area: str = "design",
                    mechanic: Optional[str] = None,
                    theme: Optional[str] = None,
                    journal=None) -> str:
    """Log one insight from a book. Dedupes by normalized content; a repeat is
    flagged so the meta-loop can graduate it into the harness.
    Returns the learning id."""
    state = load(cfg)
    key = re.sub(r"\s+", " ", learning.strip().lower())
    for ex in state["learnings"]:
        if re.sub(r"\s+", " ", ex.get("learning", "").strip().lower()) == key:
            ex["repeat"] = True
            save(cfg, state)
            return ex["id"]
    lid = f"{_slugify(book)}-{len(state['learnings']) + 1}"
    state["learnings"].append({
        "id": lid, "book": book, "learning": learning,
        "target_area": target_area, "mechanic": mechanic, "theme": theme,
        "repeat": False, "applied": False, "at": _now(),
    })
    save(cfg, state)
    (journal or open_journal(cfg)).append(
        "books_learning", id=lid, book=book, target_area=target_area)
    return lid


def add_principle(cfg, *, text: str, source: str = "", journal=None) -> None:
    """Distill a long-lived design principle from a book. Principles are the
    library's permanent residue: they outlive any single learning."""
    state = load(cfg)
    key = re.sub(r"\s+", " ", text.strip().lower())
    if any(re.sub(r"\s+", " ", p.get("text", "").lower()) == key
           for p in state["principles"]):
        return
    state["principles"].append({
        "text": text, "source": source, "at": _now(),
    })
    save(cfg, state)
    (journal or open_journal(cfg)).append("books_principle", source=source)


def principles(cfg) -> list[dict]:
    return load(cfg)["principles"]


def graduation_repeats(cfg) -> list[dict]:
    """Learnings that repeated and therefore MUST graduate into the harness."""
    return [l for l in load(cfg)["learnings"] if l.get("repeat")]


def unapplied_learnings(cfg) -> list[dict]:
    """Book learnings not yet folded into Eve's policy. These feed the same
    self-improvement path as Loop B's arch lessons (see improve.run)."""
    return [l for l in load(cfg)["learnings"] if not l.get("applied")]


def apply_learning(cfg, learning_id: str, journal=None) -> bool:
    """Mark a book learning as applied to Eve's policy.

    This is the Loop D -> harness feed, mirroring arch.apply: once a book
    insight has been folded into the rules lens / playtest prompt, it is
    marked applied so the next improve() run does not re-apply it.
    """
    state = load(cfg)
    for l in state["learnings"]:
        if l["id"] == learning_id:
            l["applied"] = True
            save(cfg, state)
            (journal or open_journal(cfg)).append("books_apply", id=learning_id)
            return True
    return False


def learnings_for(cfg, target_area: str) -> list[dict]:
    """Learnings aimed at one part of the pipeline (rules, brief, playtest,
    fun, ideator) — the concrete feed from Loop D into Loop C's lenses."""
    area = target_area.lower()
    return [l for l in load(cfg)["learnings"] if l.get("target_area", "").lower() == area]


def progress(cfg) -> dict:
    state = load(cfg)
    counts = {"unread": 0, "in_progress": 0, "done": 0}
    for b in state["reading_list"]:
        counts[b.get("status", "unread")] = counts.get(b.get("status", "unread"), 0) + 1
    return {
        "books": counts,
        "total": len(state["reading_list"]),
        "learnings": len(state["learnings"]),
        "principles": len(state["principles"]),
        "next_up": next_up(cfg),
    }
