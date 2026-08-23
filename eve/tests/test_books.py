"""Deterministic tests for Loop D (the great-books study).

These cover the no-LLM bookkeeping: seeding, the cadence primitive (one book
per tick), the persistence bug regression, learning dedupe/apply, and
principle dedupe. Everything runs against a temp root so the real loops/ state
is never touched.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from eve import books, config

CANONICAL = [
    "Everybody Wins: Four Decades of the Greatest Board Games Ever Made",
    "Around the World in Eighty Games",
    "Board Games in 100 Moves",
    "GameTek: The Math and Science of Gaming",
    "A Theory of Fun for Game Design",
    "Characteristics of Games",
    "Building Blocks of Tabletop Game Design",
]


@pytest.fixture()
def cfg(tmp_path: Path):
    """A Config rooted at a throwaway dir, seeded from the bundled shelf."""
    seed_dir = tmp_path / "corpus" / "seed"
    seed_dir.mkdir(parents=True)
    payload = json.loads(
        (config.REPO_ROOT / "corpus" / "seed" / "books.json").read_text(
            encoding="utf-8"
        )
    )
    (seed_dir / "books.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    c = config.Config(root=tmp_path, seed_dir=seed_dir,
                      journal_path=tmp_path / "loops" / "journal.md")
    return c


def test_seed_loads_canonical_shelf(cfg):
    n = books.seed_reading_list(cfg)
    titles = [b["title"] for b in books.reading_list(cfg)]
    assert n == len(CANONICAL) == 7
    for t in CANONICAL:
        assert t in titles


def test_next_up_respects_shelf_order(cfg):
    books.seed_reading_list(cfg)
    assert books.next_up(cfg)["title"] == CANONICAL[0]


def test_study_tick_starts_exactly_one_book(cfg):
    books.seed_reading_list(cfg)
    book = books.study_tick(cfg)
    assert book["title"] == CANONICAL[0]
    prog = books.progress(cfg)
    assert prog["books"]["in_progress"] == 1
    assert prog["books"]["unread"] == 6


def test_study_tick_holds_a_book_until_done(cfg):
    books.seed_reading_list(cfg)
    a = books.study_tick(cfg)["title"]
    b = books.study_tick(cfg)["title"]
    assert a == b == CANONICAL[0]  # no second book starts mid-reading


def test_mark_done_persists(cfg):
    # Regression: mark_* used to mutate then re-read from disk, losing the write.
    books.seed_reading_list(cfg)
    books.mark_started(cfg, CANONICAL[0])
    books.mark_done(cfg, CANONICAL[0])
    prog = books.progress(cfg)
    assert prog["books"]["done"] == 1
    assert prog["books"]["in_progress"] == 0
    assert books.next_up(cfg)["title"] == CANONICAL[1]


def test_record_learning_dedupes_and_applies(cfg):
    books.seed_reading_list(cfg)
    lid = books.record_learning(
        cfg, book=CANONICAL[0], learning="Landmark games carry their moment's cultural weight.",
        target_area="ideator")
    again = books.record_learning(
        cfg, book=CANONICAL[0], learning="  LANDMARK GAMES CARRY THEIR MOMENT'S CULTURAL WEIGHT.  ",
        target_area="ideator")
    assert again == lid  # deduped by normalized content
    assert books.graduation_repeats(cfg)[0]["id"] == lid
    assert [l["id"] for l in books.unapplied_learnings(cfg)] == [lid]
    assert books.apply_learning(cfg, lid)
    assert books.unapplied_learnings(cfg) == []
    assert [l["id"] for l in books.learnings_for(cfg, "ideator")] == [lid]


def test_add_principle_dedupes(cfg):
    books.add_principle(cfg, text="The printed game is the product.", source="owners shelf")
    books.add_principle(cfg, text="the printed game is the product.", source="owners shelf")
    assert len(books.principles(cfg)) == 1
