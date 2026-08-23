"""Tests for loops/scholar.py and loops/architect.py.

Self-contained per CONTRACTS §5: each test builds its own temp BOB_HOME,
runs under BOB_MOCK_AGENTS=1 (fixtures planted in <home>/tests/fixtures,
which agents._mock_result prefers over the repo copies), no network, no
real claude calls.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from loops import architect, scholar  # noqa: E402

# A reply comfortably over scholar.MIN_CARD_CHARS, with an H1 the INDEX
# line should pick up.
LONG_CARD = "# Fixture Card Title\n\n" + ("Invariant sentence. " * 40)
SHORT_CARD = "sorry, I could not research this topic."

ARCHITECT_REPLY = (
    "- finding one, with a receipt and a link\n"
    "- finding two\n\n"
    "## P-2026-08-22-1: per-phase memory ceiling\n"
    "Evidence: text2cad OOM receipt\n"
    "Change: harness/agents.py preexec RLIMIT_AS\n"
    "Tier: CODE\n"
    "Cost of not doing it: one runaway phase can OOM the box.\n"
)


class Base(unittest.TestCase):
    ENV_KEYS = ("BOB_HOME", "BOB_MOCK_AGENTS", "BOB_CLAUDE_BIN")

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="bob-test-")
        self._saved = {k: os.environ.get(k) for k in self.ENV_KEYS}
        for k in self.ENV_KEYS:
            os.environ.pop(k, None)
        os.environ["BOB_HOME"] = self.home
        os.environ["BOB_MOCK_AGENTS"] = "1"

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.home, ignore_errors=True)

    # -- helpers ----------------------------------------------------------

    def plant_fixture(self, agent, text):
        fdir = os.path.join(self.home, "tests", "fixtures")
        os.makedirs(fdir, exist_ok=True)
        with open(os.path.join(fdir, agent + ".txt"), "w") as f:
            f.write(text)

    def write_json(self, rel, obj):
        path = os.path.join(self.home, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(obj, f)

    def write_text(self, rel, text):
        path = os.path.join(self.home, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def read_text(self, rel):
        path = os.path.join(self.home, rel)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return f.read()

    def read_json(self, rel):
        with open(os.path.join(self.home, rel)) as f:
            return json.load(f)

    def study_queue(self, units):
        self.write_json("corpus/STUDY_QUEUE.json",
                        {"next_id": 99, "units": units})

    def book_queue(self, units):
        self.write_json("corpus/BOOK_QUEUE.json",
                        {"next_id": 99, "units": units})

    def cards(self):
        cdir = os.path.join(self.home, "corpus", "cards")
        if not os.path.isdir(cdir):
            return []
        return sorted(os.listdir(cdir))


class TestScholarLanes(Base):
    def setUp(self):
        super(TestScholarLanes, self).setUp()
        self.plant_fixture("bob-scholar", LONG_CARD)
        self.plant_fixture("bob-librarian", LONG_CARD)
        self.study_queue([
            {"id": 1, "kind": "era", "topic": "Ancient race games",
             "status": "todo"}])
        self.book_queue([
            {"id": 1, "book": "GameTek", "topic": "Probability essays",
             "status": "todo"}])

    def test_lanes_alternate_study_first(self):
        r1 = scholar.tick()
        self.assertEqual(r1["lane"], "study")
        self.assertEqual(r1["outcome"], "done")
        r2 = scholar.tick()
        self.assertEqual(r2["lane"], "book")
        self.assertEqual(r2["outcome"], "done")

        names = self.cards()
        self.assertEqual(len(names), 2)
        self.assertTrue(any(n.startswith("study-1-") for n in names), names)
        self.assertTrue(any(n.startswith("book-1-") for n in names), names)

        # queues marked done with a date, cursor points at the last lane
        squnit = self.read_json("corpus/STUDY_QUEUE.json")["units"][0]
        bqunit = self.read_json("corpus/BOOK_QUEUE.json")["units"][0]
        self.assertEqual(squnit["status"], "done")
        self.assertIn("studied", squnit)
        self.assertEqual(bqunit["status"], "done")
        book = self.read_json("state/DAYBOOK.json")
        self.assertEqual(book[scholar.CURSOR_KEY], "book")

        # one INDEX.md line per card, carrying the card's own H1
        index = self.read_text("corpus/INDEX.md")
        self.assertEqual(index.count("Fixture Card Title"), 2)
        self.assertEqual(len(index.strip().splitlines()), 2)

    def test_fallback_when_preferred_lane_empty(self):
        # cursor says study just ran, but book queue is exhausted:
        # the tick must fall back to study rather than no-op.
        self.book_queue([{"id": 1, "book": "GameTek", "topic": "t",
                          "status": "done"}])
        scholar._update_daybook(scholar.CURSOR_KEY, "study")
        r = scholar.tick()
        self.assertEqual(r["lane"], "study")
        self.assertEqual(r["outcome"], "done")

    def test_both_queues_empty_is_a_noop(self):
        self.study_queue([])
        self.book_queue([])
        r = scholar.tick()
        self.assertEqual(r["outcome"], "empty")
        self.assertEqual(self.cards(), [])


class TestScholarRetryFailed(Base):
    def setUp(self):
        super(TestScholarRetryFailed, self).setUp()
        # Only the study lane has work; every tick lands on it.
        self.plant_fixture("bob-scholar", SHORT_CARD)
        self.study_queue([
            {"id": 7, "kind": "case", "topic": "Doomed topic",
             "status": "todo"}])
        self.book_queue([])

    def test_short_card_marks_retry_then_failed_never_done(self):
        r1 = scholar.tick()
        self.assertEqual(r1["outcome"], "retry")
        unit = self.read_json("corpus/STUDY_QUEUE.json")["units"][0]
        self.assertEqual(unit["status"], "retry")

        r2 = scholar.tick()
        self.assertEqual(r2["outcome"], "failed")
        unit = self.read_json("corpus/STUDY_QUEUE.json")["units"][0]
        self.assertEqual(unit["status"], "failed")
        self.assertIn("failed", unit)

        # never a card, never an INDEX line, never silently done
        self.assertEqual(self.cards(), [])
        self.assertIsNone(self.read_text("corpus/INDEX.md"))

        # a failed unit stops being schedulable: next tick is a no-op
        r3 = scholar.tick()
        self.assertEqual(r3["outcome"], "empty")

    def test_retry_unit_recovers_when_reply_improves(self):
        scholar.tick()  # -> retry
        self.plant_fixture("bob-scholar", LONG_CARD)
        r = scholar.tick()
        self.assertEqual(r["outcome"], "done")
        unit = self.read_json("corpus/STUDY_QUEUE.json")["units"][0]
        self.assertEqual(unit["status"], "done")
        self.assertEqual(len(self.cards()), 1)


class TestArchitectWeekly(Base):
    def setUp(self):
        super(TestArchitectWeekly, self).setUp()
        self.plant_fixture("bob-architect", ARCHITECT_REPLY)
        self.write_text("knowledge/SOURCES.md",
                        "# Sources\n- https://example.test/engineering\n")

    def set_stamp(self, dt):
        self.write_json("state/DAYBOOK.json",
                        {architect.STAMP_KEY: dt.isoformat()})

    def test_sweep_appends_notes_and_proposals_then_throttles(self):
        r = architect.tick()
        self.assertEqual(r["outcome"], "swept")
        self.assertEqual(r["proposals"], 1)

        notes = self.read_text("knowledge/architecture-notes.md")
        self.assertIn("## Sweep ", notes)
        self.assertIn("finding one", notes)
        proposals = self.read_text("knowledge/PROPOSALS.md")
        self.assertIn("## P-2026-08-22-1", proposals)
        self.assertIn("Tier: CODE", proposals)

        # stamp written -> immediate second tick is a no-op
        r2 = architect.tick()
        self.assertEqual(r2["outcome"], "throttled")
        self.assertEqual(self.read_text("knowledge/architecture-notes.md"),
                         notes)

    def test_stale_stamp_runs_again(self):
        self.set_stamp(datetime.now(timezone.utc) - timedelta(days=8))
        r = architect.tick()
        self.assertEqual(r["outcome"], "swept")

    def test_fresh_stamp_throttles(self):
        self.set_stamp(datetime.now(timezone.utc) - timedelta(days=2))
        r = architect.tick()
        self.assertEqual(r["outcome"], "throttled")
        self.assertIsNone(self.read_text("knowledge/architecture-notes.md"))

    def test_missing_sources_does_not_stamp(self):
        os.remove(os.path.join(self.home, "knowledge", "SOURCES.md"))
        r = architect.tick()
        self.assertEqual(r["outcome"], "no_sources")
        # no stamp -> still due once the file is restored
        self.assertTrue(architect._due())


if __name__ == "__main__":
    unittest.main()
