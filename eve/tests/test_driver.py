"""End-to-end driver test: an injected agent writes each role's real contract
file, so `evolve()` drives a brand-new game from spark all the way to `ship`
without ever calling the Claude CLI (no tokens, fully isolated in tmp_path).

This mirrors the handoff's goal: prove the *executor* (driver.py) can walk the
full pipeline — ideator -> novelty -> rules -> brief -> builder -> print ->
panel -> playtest -> ship — using the same JSON contract files real Agent runs
write. It runs in milliseconds and never touches the live games/ or loops/.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from eve import config, corpus, driver, queue

# A fresh, corpus-valid, non-colliding idea. Backpack-rail + vexing-pin is
# deliberately unlike any owned mechanic/theme token (gates.py/gates novelty).
IDEA = {
    "slug": "vigil-station",
    "title": "Vigil Station",
    "mech": "a printed carriage-rail that re-ranges a lantern's beam",
    "blurb": "Shift a carriage on a real rail to aim a shared lantern's light.",
    "idea": (
        "A printed carriage-rail game where each player lands a lantern carriage "
        "on a graduated rail to re-range the light on a target dial; the rail's "
        "indexing toggles a vexing-pin lock that only the aimer can feel."
    ),
    "identity": "like Ricochet Robots' route-planning + a printed carriage-rail indexing lock",
    "bill": {"rail": ["rail_01", "rail_02"], "carriage": ["carriage_01"],
             "dial": ["dial_01"], "token": ["tk_01", "tk_02", "tk_03", "tk_04"]},
    "seats": "2-4",
    "t_min": "15",
    "t_max": "25",
}


class _Result:
    """Stand-in for agents.AgentResult; the driver only checks exceptions."""
    text = ""  # placeholder


def _mock_agent(role, prompt, *, cwd=None, max_minutes=None):
    """Writes the role's real contract file into its cwd, like a real agent."""
    cwd = Path(cwd or ".")
    if role == "ideator":
        n = int(getattr(_mock_agent, "_n", 0)) + 1
        _mock_agent._n = n
        idea = dict(IDEA)   # copy: never mutate the shared IDEA dict
        if n == 1:
            idea["slug"] = IDEA["slug"]
        else:
            # later sparks still invent a real, non-colliding game so a long
            # evolve() keeps the meta-loop turning instead of re-proposing
            # the already-shipped first slug (DriverStop "already exists").
            idea["slug"] = f"vigil-station-{n}"
            idea["identity"] = (
                f"like Hive + a printed {n}-way carriage-rail indexing lock")
        (cwd / "idea.json").write_text(json.dumps(idea))
        (cwd / "rules.md").write_text("# VIGIL STATION\n\nrules text\n")
    elif role == "brief":
        (cwd / "stage_out.json").write_text(json.dumps(
            {"brief": "all parts < 160 mm on a 256 mm bed; rail is the signature piece",
             "bill": IDEA["bill"]}))
    elif role == "builder":
        (cwd / "stage_out.json").write_text(json.dumps(
            {"built": ["rail_01", "rail_02", "carriage_01", "dial_01",
                       "tk_01", "tk_02", "tk_03", "tk_04"],
             "n_parts": 8}))
        b = cwd / "build"
        b.mkdir(exist_ok=True)
        for name in ["rail_01", "carriage_01", "dial_01", "tk_01"]:
            (b / f"{name}.stl").write_bytes(b"solid mock\n  facet normal 0 0 0\nendsolid mock\n")
    elif role == "panel":
        (cwd / "stage_out.json").write_text(json.dumps(
            {"verdict": "pass", "lenses": ["printability", "fidelity", "playability"],
             "notes": "carriage rail indexes cleanly; all parts print flat."}))
    elif role == "playtest":
        (cwd / "stage_out.json").write_text(json.dumps({
            "engine_run": {"source": "llm_table", "games_played": 60,
                           "first_seat_wins": 0.25, "ends": True,
                           "decisiveness": 0.83, "ask_to_play_again": 0.5,
                           "note": "real LLM 4-seat table; balanced and asked to replay"},
            "interpretation": "rail indexing adds a real decision; balanced"}))
        pt = cwd / "playtest"
        pt.mkdir(exist_ok=True)
        (pt / "engine.py").write_text("def run(trials, seed):\n    return None\n")
    return _Result()


@pytest.fixture()
def cfg(tmp_path: Path):
    """A fully isolated Config rooted at tmp_path."""
    seed_dir = tmp_path / "corpus" / "seed"
    seed_dir.mkdir(parents=True)
    shutil.copy(config.REPO_ROOT / "corpus" / "seed" / "corpus.json",
                seed_dir / "corpus.json")
    db = tmp_path / "corpus" / "db" / "corpus.json"
    c = config.Config(
        root=tmp_path,
        games_dir=tmp_path / "games",
        loops_dir=tmp_path / "loops",
        seed_dir=seed_dir,
        corpus_db=db,
        ledger_path=tmp_path / "loops" / "ledger.json",
        queue_path=tmp_path / "loops" / "queue.json",
        journal_path=tmp_path / "loops" / "journal.md",
        taste_path=tmp_path / "taste" / "taste.md",
        arch_state=tmp_path / "loops" / "arch" / "state.json",
        corpus_state=tmp_path / "loops" / "corpus" / "state.json",
    )
    corpus.seed(c)
    corpus.seed_owned(c)   # populate owned axes so the novelty gate can run
    return c


def test_evolve_drives_new_game_to_ship(cfg):
    _mock_agent._n = 0
    res = driver.evolve(cfg, max_steps=24, fn_run_agent=_mock_agent)
    # Regardless of how many sparks fired, at least one game reached ship.
    assert res["action"] == "step"
    q = queue.Queue(cfg)
    shipped = [g for g in q.list() if g.stage == "ship"]
    assert any(g.slug == IDEA["slug"] for g in shipped), \
        "vigil-station should reach ship"
    # The shipped game carries real playtest evidence (fun_pass leave a trace).
    shipped_game = next(g for g in shipped if g.slug == IDEA["slug"])
    assert shipped_game.fun_evidence, "shipped game must have fun_evidence"


def test_driver_audit_clean_after_ship(cfg):
    _mock_agent._n = 0
    driver.evolve(cfg, max_steps=30, fn_run_agent=_mock_agent)
    from eve.reward import audit
    problems = audit(cfg)
    assert problems == [], f"ledger should be verifiable, got: {problems}"


# --- gate-failure must KILL, not re-judge forever --------------------------
# A deterministic gate re-runs to the identical verdict (no LLM changes the
# game between attempts), so a hard novelty failure must terminate the game
# with a stated reason and free the queue. Before the fix, a colliding idea
# was re-judged on every tick, starving every other loop (the real
# `sieve-season-gauge` / 'tension' incident). This test locks that in.


def _colliding_mock_agent(role, prompt, *, cwd=None, max_minutes=None):
    """Always proposes a game whose identity claims an ALREADY-OWNED mechanic
    ('tension' is owned by CATENARY), so the novelty gate must kill it."""
    cwd = Path(cwd or ".")
    if role == "ideator":
        n = int(getattr(_colliding_mock_agent, "_n", 0)) + 1
        _colliding_mock_agent._n = n
        idea = dict(IDEA)
        idea["slug"] = f"tension-clone-{n}"
        idea["title"] = "Tension Clone"
        idea["mech"] = "a printed tension chain latch"
        idea["identity"] = "like Coup's bluff + a printed tension chain latch"
        idea["idea"] = (
            "A tension-latch game whose core relies on the printed tension "
            "chain mechanism that the catalog already owns."
        )
        (cwd / "idea.json").write_text(json.dumps(idea))
        (cwd / "rules.md").write_text("# TENSION CLONE\n\nrules text\n")
    return _Result()


def test_novelty_collision_is_killed_not_restuck(cfg):
    _colliding_mock_agent._n = 0
    res = driver.evolve(cfg, max_steps=8, fn_run_agent=_colliding_mock_agent)
    q = queue.Queue(cfg)
    killed = [g for g in q.list() if g.stage == "killed"]
    assert killed, "a colliding idea must be killed, not left active"
    assert all("tension" in g.kill_reason for g in killed),         "kill reason must state the collision honestly"
    # The killing frees the queue: nothing with a tension collision is left
    # in the active set waiting to be re-judged every tick.
    active = [g for g in q.active()]
    assert all("tension" not in (g.kill_reason or "") for g in active)


def test_gate_kill_records_dead_game_reward(cfg):
    from eve import meta, journal
    _colliding_mock_agent._n = 0
    q = queue.Queue(cfg)
    q.add("catenary-clone", title="Catenary Clone",
          identity="like Coup's bluff + a printed tension chain rite",
          idea="a tension-ratchet game that collides with owned tension/chain")
    q.record("catenary-clone", bill={"chain": ["c1", "c2"]})
    m = meta.Meta(cfg, journal=journal.open_journal(cfg))
    out = m.run_gate(q.get("catenary-clone"), "novelty")
    assert out["passed"] is False
    # meta.run_gate must have cross-checkably killed it (queue stage 'killed'
    # <-> a dead_game ledger row, per reward.audit()).
    g = q.get("catenary-clone")
    assert g.stage == "killed"
    assert "tension" in g.kill_reason
    from eve.reward import audit
    assert audit(cfg) == [], f"killed game must be ledger-consistent, got: {audit(cfg)}"


# --- Loop D: the reader agent dispatch ------------------------------------
# The meta-loop cadence (one book/day) must dispatch a `reader` agent that
# reads the in-progress book, records its learnings, and marks it done —
# and only then may the shelf advance. This proves the driver executes the
# HTML books loop end-to-end without ever touching a live Claude run.


def _mock_reader(role, prompt, *, cwd=None, max_minutes=None):
    """Writes the reader's real contract (loops/books/stage_out.json)."""
    cwd = Path(cwd or ".")
    (cwd / "stage_out.json").write_text(json.dumps({
        "learnings": [
            {"learning": "Landmark games carry their moment's cultural weight.",
             "target_area": "ideator"},
            {"learning": "A game worth replaying lets the loser name the rematch.",
             "target_area": "fun", "mechanic": "achievement"},
        ],
        "principles": [
            {"text": "The printed game is the product."},
        ],
    }))
    return _Result()


def _seed_books(cfg):
    from eve import books
    src = config.REPO_ROOT / "corpus" / "seed" / "books.json"
    cfg.seed_dir.mkdir(parents=True, exist_ok=True)
    (cfg.seed_dir / "books.json").write_text(src.read_text())
    books.seed_reading_list(cfg)


def test_reader_dispatch_records_learnings_and_marks_done(cfg):
    from eve import books, meta
    _seed_books(cfg)
    first = books.reading_list(cfg)[0]["title"]
    # Directly drive the reader role the same way evolve() would.
    m = meta.Meta(cfg)
    res = driver._run_reader(cfg, m, _mock_reader, "")
    assert res["role"] == "reader"
    assert res["book"] == first
    assert res["learnings"] == 2
    assert res["principles"] == 1
    # The book advanced in_progress -> done, and learnings are applied.
    prog = books.progress(cfg)
    assert prog["books"]["done"] == 1
    assert books.learnings_for(cfg, "ideator"), "learning must be tagged to a target area"


def test_evolve_dispatches_reader_when_pipeline_idle(cfg):
    from eve import books, driver as drv, meta
    _seed_books(cfg)
    first = books.reading_list(cfg)[0]["title"]
    # Evolve with a null ideator (never sparks) so the only work available is
    # the books cadence; the reader mock records + closes the book.
    def _null_ideator(role, prompt, *, cwd=None):
        return _Result()
    res = drv.evolve(cfg, max_steps=1, fn_run_agent=_mock_reader)
    # evolve() stamps last_books_study via _study_dispatch, so the cadence
    # is now satisfied for the day (one book worked, no re-loop).
    assert meta.Meta(cfg).books_due() is False
    prog = books.progress(cfg)
    assert prog["books"]["done"] == 1 and books.reading_list(cfg)[0]["title"] == first
