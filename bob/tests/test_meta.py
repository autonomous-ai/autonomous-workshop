"""Tests for loops/meta.py — the leash on the improve session.

The three behaviors that keep the self-improver safe are exactly what is
tested: (1) one forbidden path voids the whole session with ZERO writes
applied; (2) a failed test suite reverts every applied write; (3) doc-tier
applies, code-tier diverts to PROPOSALS.md, never to disk.

Self-contained per CONTRACTS §5: temp BOB_HOME, BOB_MOCK_AGENTS=1 with the
improver reply planted as a fixture in <home>/tests/fixtures (preferred by
agents._mock_result over the repo copy).
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from loops import meta  # noqa: E402

ORIGINAL_LESSONS = "# lessons\n\n- [seed · pipeline · 2026-08-01 · $0 · OPEN] original entry\n"
NEW_LESSONS = "# lessons\n\n- [new · improve · 2026-08-22 · $0 · OPEN] improved entry\n"


def reply(writes):
    return json.dumps(writes)


class Base(unittest.TestCase):
    ENV_KEYS = ("BOB_HOME", "BOB_MOCK_AGENTS", "BOB_CLAUDE_BIN")

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="bob-test-")
        self._saved = {k: os.environ.get(k) for k in self.ENV_KEYS}
        for k in self.ENV_KEYS:
            os.environ.pop(k, None)
        os.environ["BOB_HOME"] = self.home
        os.environ["BOB_MOCK_AGENTS"] = "1"
        self.write_text("knowledge/lessons.md", ORIGINAL_LESSONS)
        self._real_suite = meta._run_suite
        # Deterministic green suite unless a test says otherwise —
        # meta._run_suite is module-level precisely so tests can
        # monkeypatch it (running the real suite inside the suite recurses).
        meta._run_suite = lambda: (True, "monkeypatched green")

    def tearDown(self):
        meta._run_suite = self._real_suite
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.home, ignore_errors=True)

    # -- helpers ----------------------------------------------------------

    def plant_reply(self, text):
        fdir = os.path.join(self.home, "tests", "fixtures")
        os.makedirs(fdir, exist_ok=True)
        with open(os.path.join(fdir, "bob-improver.txt"), "w") as f:
            f.write(text)

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

    def no_bak_files(self):
        for root, _dirs, files in os.walk(self.home):
            for name in files:
                self.assertFalse(name.endswith(meta.BAK_SUFFIX),
                                 os.path.join(root, name))


class TestForbiddenRejectsWholeSession(Base):
    def test_one_forbidden_path_voids_everything(self):
        self.plant_reply(reply([
            {"path": "harness/reward.py", "content": "def score(c): return 100\n"},
            {"path": "knowledge/lessons.md", "content": NEW_LESSONS},
        ]))
        r = meta.improve()
        self.assertEqual(r["outcome"], "rejected_forbidden")
        self.assertEqual(r["applied"], 0)
        self.assertIn("harness/reward.py", r["forbidden"])
        # the innocent doc-tier write riding alongside was NOT applied
        self.assertEqual(self.read_text("knowledge/lessons.md"),
                         ORIGINAL_LESSONS)
        self.assertIsNone(self.read_text("harness/reward.py"))
        # logged loudly in the session log
        log = self.read_text("knowledge/improve-log.md")
        self.assertIn("REJECTED", log)
        self.assertIn("harness/reward.py", log)
        self.no_bak_files()

    def test_state_glob_and_taste_are_forbidden(self):
        self.plant_reply(reply([
            {"path": "state/BANDIT.json", "content": "{}"},
            {"path": "knowledge/TASTE.md", "content": "my taste now"},
        ]))
        r = meta.improve()
        self.assertEqual(r["outcome"], "rejected_forbidden")
        self.assertIsNone(self.read_text("state/BANDIT.json"))

    def test_path_escape_is_forbidden(self):
        self.plant_reply(reply([
            {"path": "../outside.md", "content": "escape"},
            {"path": "/tmp/absolute.md", "content": "escape"},
        ]))
        r = meta.improve()
        self.assertEqual(r["outcome"], "rejected_forbidden")
        self.assertFalse(os.path.exists(
            os.path.join(os.path.dirname(self.home), "outside.md")))


class TestSuiteFailureReverts(Base):
    def test_failed_suite_reverts_every_write(self):
        self.plant_reply(reply([
            {"path": "knowledge/lessons.md", "content": NEW_LESSONS},
            {"path": ".claude/agents/bob-ideator.md", "content": "v2 prompt\n"},
        ]))
        meta._run_suite = lambda: (False, "FAILED (failures=1)")
        r = meta.improve()
        self.assertEqual(r["outcome"], "reverted_suite_failure")
        self.assertEqual(r["applied"], 0)
        # pre-existing file restored byte-for-byte; created file removed
        self.assertEqual(self.read_text("knowledge/lessons.md"),
                         ORIGINAL_LESSONS)
        self.assertIsNone(self.read_text(".claude/agents/bob-ideator.md"))
        log = self.read_text("knowledge/improve-log.md")
        self.assertIn("reverted", log.lower())
        self.no_bak_files()


class TestApplyAndDivert(Base):
    def test_doc_tier_applies_code_tier_diverts(self):
        self.plant_reply(reply([
            {"path": "knowledge/lessons.md", "content": NEW_LESSONS},
            {"path": "loops/invent.py", "content": "# sneaky code change\n"},
        ]))
        r = meta.improve()
        self.assertEqual(r["outcome"], "ok")
        self.assertEqual(r["applied"], 1)
        self.assertEqual(r["proposals"], 1)
        # doc write landed
        self.assertEqual(self.read_text("knowledge/lessons.md"), NEW_LESSONS)
        # code write NEVER hit disk; it became a PROPOSALS.md entry
        self.assertIsNone(self.read_text("loops/invent.py"))
        proposals = self.read_text("knowledge/PROPOSALS.md")
        self.assertIn("loops/invent.py", proposals)
        self.assertIn("sneaky code change", proposals)
        self.assertIn("Tier: CODE", proposals)
        # session report written, baks cleaned up
        log = self.read_text("knowledge/improve-log.md")
        self.assertIn("knowledge/lessons.md", log)
        self.no_bak_files()

    def test_unparseable_reply_applies_nothing(self):
        self.plant_reply("I think we should improve the prompts a lot.")
        r = meta.improve()
        self.assertEqual(r["outcome"], "unparseable")
        self.assertEqual(self.read_text("knowledge/lessons.md"),
                         ORIGINAL_LESSONS)
        self.assertIn("no parseable",
                      self.read_text("knowledge/improve-log.md"))

    def test_fenced_json_reply_is_accepted(self):
        self.plant_reply("Here are my writes:\n```json\n" + reply(
            [{"path": "knowledge/lessons.md", "content": NEW_LESSONS}]
        ) + "\n```\n")
        r = meta.improve()
        self.assertEqual(r["outcome"], "ok")
        self.assertEqual(self.read_text("knowledge/lessons.md"), NEW_LESSONS)

    def test_empty_list_is_a_legal_session(self):
        self.plant_reply("[]")
        r = meta.improve()
        self.assertEqual(r["outcome"], "ok")
        self.assertEqual(r["applied"], 0)


class TestRealSuiteRunner(Base):
    def test_vacuous_pass_without_tests_dir_via_repo_fixture(self):
        # No fixture planted in home -> agents falls back to the repo's
        # tests/fixtures/bob-improver.txt (doc write + code-tier write),
        # and home has no tests/ dir -> the REAL _run_suite passes
        # vacuously. End to end without monkeypatching.
        meta._run_suite = self._real_suite
        r = meta.improve()
        self.assertEqual(r["outcome"], "ok")
        self.assertEqual(r["applied"], 1)
        self.assertEqual(r["proposals"], 1)
        self.assertIn("Fixture lesson",
                      self.read_text("knowledge/lessons.md"))
        self.assertIsNone(self.read_text("loops/invent.py"))


if __name__ == "__main__":
    unittest.main()
