"""Tests for harness/novelty.py — BGG lookup shape, the 24h cache (hit,
expiry), the never-raise error contract, and the packaged evidence file.
Zero network: _http is always monkeypatched."""

import hashlib
import json
import os
import shutil
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone

from harness import novelty

SLUG = "tower-duel"

SEARCH_XML = """<?xml version="1.0" encoding="utf-8"?>
<items total="5">
  <item type="boardgame" id="101"><name type="primary" value="Tower One"/>
    <yearpublished value="1999"/></item>
  <item type="boardgame" id="102"><name type="primary" value="Tower Two"/>
    <yearpublished value="2005"/></item>
  <item type="boardgame" id="103"><name type="primary" value="Tower Three"/>
  </item>
  <item type="boardgame" id="104"><name type="primary" value="Tower Four"/>
    <yearpublished value="2011"/></item>
  <item type="boardgame" id="105"><name type="primary" value="Tower Five"/>
    <yearpublished value="2020"/></item>
</items>
"""

THING_XML = """<?xml version="1.0" encoding="utf-8"?>
<items>
  <item type="boardgame" id="101">
    <description>Players stack &amp;quot;towers&amp;quot;   until one
    falls. A dexterity classic.</description></item>
  <item type="boardgame" id="102">
    <description>Second game.</description></item>
</items>
"""


class NoveltyHome(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="bob-test-nov-")
        self._old = os.environ.get("BOB_HOME")
        os.environ["BOB_HOME"] = self.home
        self._orig_http = novelty._http
        self.calls = []

    def tearDown(self):
        novelty._http = self._orig_http
        if self._old is None:
            os.environ.pop("BOB_HOME", None)
        else:
            os.environ["BOB_HOME"] = self._old
        shutil.rmtree(self.home, ignore_errors=True)

    def mock_bgg(self):
        def fake(url):
            self.calls.append(url)
            if "/search?" in url:
                return SEARCH_XML.encode("utf-8")
            if "/thing?" in url:
                return THING_XML.encode("utf-8")
            raise AssertionError("unexpected URL %s" % url)
        novelty._http = fake

    def mock_down(self):
        def fake(url):
            self.calls.append(url)
            raise urllib.error.URLError("boardgamegeek is down")
        novelty._http = fake


class TestBggCandidates(NoveltyHome):
    def test_top5_shape(self):
        self.mock_bgg()
        cands = novelty.bgg_candidates("Tower Duel", ["stacking"])
        self.assertEqual(len(cands), 5)
        first = cands[0]
        self.assertEqual(first["name"], "Tower One")
        self.assertEqual(first["year"], 1999)
        self.assertEqual(first["bgg_id"], "101")
        self.assertEqual(first["url"],
                         "https://boardgamegeek.com/boardgame/101")
        # entities unescaped, whitespace collapsed, snippet capped
        self.assertIn('"towers"', first["description_snippet"])
        self.assertNotIn("  ", first["description_snippet"])
        # missing yearpublished is a legal None, not a crash
        self.assertIsNone(cands[2]["year"])
        # no game got a phantom description
        self.assertEqual(cands[3]["description_snippet"], "")

    def test_cache_hit_skips_network(self):
        self.mock_bgg()
        novelty.bgg_candidates("Tower Duel", ["stacking"])
        n_calls = len(self.calls)
        self.assertGreater(n_calls, 0)
        again = novelty.bgg_candidates("Tower Duel", ["stacking"])
        self.assertEqual(len(self.calls), n_calls)  # served from cache
        self.assertEqual(len(again), 5)

    def test_cache_expiry_refetches(self):
        self.mock_bgg()
        novelty.bgg_candidates("Tower Duel", ["stacking"])
        n_calls = len(self.calls)
        # age the cache past 24h
        cache_dir = os.path.join(self.home, "state", "bgg_cache")
        (cache_file,) = os.listdir(cache_dir)
        path = os.path.join(cache_dir, cache_file)
        with open(path) as fh:
            cached = json.load(fh)
        stale = datetime.now(timezone.utc) - timedelta(hours=25)
        cached["fetched_at"] = stale.isoformat()
        with open(path, "w") as fh:
            json.dump(cached, fh)
        novelty.bgg_candidates("Tower Duel", ["stacking"])
        self.assertGreater(len(self.calls), n_calls)

    def test_naive_fetched_at_never_raises(self):
        """Review 2026-08-22: a tz-naive fetched_at (corrupted or
        externally-written cache row) made _cache_fresh subtract naive from
        aware OUTSIDE its try — a TypeError escaping the 'never raises'
        contract. Naive stamps are normalized to UTC; any failure reads as
        stale, never as a crash."""
        self.mock_bgg()
        novelty.bgg_candidates("Tower Duel", ["stacking"])
        cache_dir = os.path.join(self.home, "state", "bgg_cache")
        (cache_file,) = os.listdir(cache_dir)
        path = os.path.join(cache_dir, cache_file)
        with open(path) as fh:
            cached = json.load(fh)

        # Fresh-but-naive stamp: still a cache hit (no network), no raise.
        naive_now = datetime.now(timezone.utc).replace(tzinfo=None)
        cached["fetched_at"] = naive_now.isoformat()
        with open(path, "w") as fh:
            json.dump(cached, fh)
        self.mock_down()  # any network call would fail loudly
        n_calls = len(self.calls)
        cands = novelty.bgg_candidates("Tower Duel", ["stacking"])
        self.assertEqual(len(cands), 5)
        self.assertEqual(len(self.calls), n_calls)  # served from cache

        # Stale-and-naive stamp: falls through to the warning path, never
        # raises even with the network down.
        naive_old = naive_now - timedelta(hours=25)
        cached["fetched_at"] = naive_old.isoformat()
        with open(path, "w") as fh:
            json.dump(cached, fh)
        rows = novelty.bgg_candidates("Tower Duel", ["stacking"])
        self.assertTrue(any("warning" in r for r in rows))

    def test_error_returns_warning_never_raises(self):
        self.mock_down()
        result = novelty.bgg_candidates("Tower Duel", ["stacking"])
        self.assertEqual(len(result), 1)
        self.assertIn("warning", result[0])
        self.assertIn("corpus only", result[0]["warning"])
        self.assertNotIn("bgg_id", result[0])

    def test_error_serves_stale_cache_with_warning(self):
        self.mock_bgg()
        novelty.bgg_candidates("Tower Duel", ["stacking"])
        # age the cache, then take the network down
        cache_dir = os.path.join(self.home, "state", "bgg_cache")
        (cache_file,) = os.listdir(cache_dir)
        path = os.path.join(cache_dir, cache_file)
        with open(path) as fh:
            cached = json.load(fh)
        cached["fetched_at"] = (datetime.now(timezone.utc)
                                - timedelta(hours=30)).isoformat()
        with open(path, "w") as fh:
            json.dump(cached, fh)
        self.mock_down()
        result = novelty.bgg_candidates("Tower Duel", ["stacking"])
        candidates = [r for r in result if "bgg_id" in r]
        warnings = [r for r in result if "warning" in r]
        self.assertEqual(len(candidates), 5)
        self.assertEqual(len(warnings), 1)
        self.assertIn("stale cache", warnings[0]["warning"])

    def test_distinct_queries_get_distinct_cache_rows(self):
        self.mock_bgg()
        novelty.bgg_candidates("Tower Duel", ["stacking"])
        novelty.bgg_candidates("Marble Vault", ["drafting"])
        cache_dir = os.path.join(self.home, "state", "bgg_cache")
        self.assertEqual(len(os.listdir(cache_dir)), 2)


class TestBuildNoveltyEvidence(NoveltyHome):
    def make_game_doc(self):
        gdir = os.path.join(self.home, "games", SLUG)
        os.makedirs(gdir, exist_ok=True)
        doc = {"title": "Tower Duel",
               "action_types": ["stacking", "sabotage"]}
        raw = json.dumps(doc).encode("utf-8")
        with open(os.path.join(gdir, "game.json"), "wb") as fh:
            fh.write(raw)
        return hashlib.sha256(raw).hexdigest()

    def make_corpus_index(self):
        cdir = os.path.join(self.home, "corpus")
        os.makedirs(cdir, exist_ok=True)
        with open(os.path.join(cdir, "INDEX.md"), "w") as fh:
            fh.write("# Index\n"
                     "- hist-004: senet, race mechanics\n"
                     "- hist-011: dexterity stacking games of Japan\n"
                     "- book-002: Koster on fun\n")

    def test_evidence_file_written_with_hits_and_sha(self):
        self.mock_bgg()
        expected_sha = self.make_game_doc()
        self.make_corpus_index()
        evidence = novelty.build_novelty_evidence(SLUG)

        out = os.path.join(self.home, "games", SLUG, "review",
                           "novelty_evidence.json")
        self.assertTrue(os.path.exists(out))
        with open(out) as fh:
            on_disk = json.load(fh)
        self.assertEqual(on_disk["game_doc_sha256"], expected_sha)
        self.assertEqual(len(on_disk["bgg_candidates"]), 5)
        # 'stacking' from action_types must have grepped line 3 of INDEX.md
        hit_lines = [h["line"] for h in on_disk["corpus_hits"]]
        self.assertTrue(any("stacking" in l for l in hit_lines))
        self.assertEqual(evidence["slug"], SLUG)
        self.assertEqual(on_disk["warnings"], [])

    def test_evidence_survives_bgg_outage_and_missing_corpus(self):
        self.mock_down()
        self.make_game_doc()  # no corpus/INDEX.md on purpose
        evidence = novelty.build_novelty_evidence(SLUG)
        self.assertEqual(evidence["bgg_candidates"], [])
        self.assertTrue(any("corpus only" in w for w in
                            evidence["warnings"]))
        self.assertTrue(any("INDEX.md missing" in w for w in
                            evidence["warnings"]))

    def test_missing_game_doc_still_produces_evidence(self):
        self.mock_bgg()
        os.makedirs(os.path.join(self.home, "games", SLUG), exist_ok=True)
        evidence = novelty.build_novelty_evidence(SLUG)
        self.assertIsNone(evidence["game_doc_sha256"])
        self.assertEqual(evidence["title"], "tower duel")


if __name__ == "__main__":
    unittest.main()
