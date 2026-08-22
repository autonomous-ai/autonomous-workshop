"""Tests for harness/agents.py — the claude-CLI runner.

Self-contained per CONTRACTS §5: each test builds its own temp BOB_HOME
(tests/util.py:make_home is integrator-owned and may not exist yet), no
network, no real claude calls. The starved/crashed/quota classification is
driven through a stub CLI (tests/fixtures/fake_claude.py) via
BOB_CLAUDE_BIN; everything else runs under BOB_MOCK_AGENTS=1.
"""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from harness import agents  # noqa: E402

FAKE_CLI = os.path.join(REPO, "tests", "fixtures", "fake_claude.py")


class Base(unittest.TestCase):
    """Fresh temp BOB_HOME + clean env per test."""

    ENV_KEYS = (
        "BOB_HOME",
        "BOB_MOCK_AGENTS",
        "BOB_CLAUDE_BIN",
        "FAKE_MODE",
        "FAKE_ARGV_OUT",
        "BOB_IDEATE_MODEL",
        "BOB_RULES_LENS_MODEL",
    )

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="bob-test-")
        self._saved = {k: os.environ.get(k) for k in self.ENV_KEYS}
        for k in self.ENV_KEYS:
            os.environ.pop(k, None)
        os.environ["BOB_HOME"] = self.home

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.home, ignore_errors=True)

    def use_fake_cli(self, mode):
        os.environ["BOB_CLAUDE_BIN"] = "{} {}".format(
            shell_quote(sys.executable), shell_quote(FAKE_CLI)
        )
        os.environ["FAKE_MODE"] = mode

    def daybook(self):
        path = os.path.join(self.home, "state", "DAYBOOK.json")
        with open(path) as f:
            return json.load(f)

    def today_steps(self):
        book = self.daybook()
        day = [k for k in book if k != "heartbeat"][0]
        return book[day]["steps"]


def shell_quote(s):
    import shlex

    return shlex.quote(s)


class TestMockEndToEnd(Base):
    def test_mock_reads_fixture_and_logs(self):
        os.environ["BOB_MOCK_AGENTS"] = "1"
        res = agents.run_agent("ideate", "spark me five games")
        self.assertIn("Gravity Well", res.text)
        self.assertEqual(res.cost_usd, 0.01)
        self.assertEqual(res.subtype, "success")
        self.assertEqual(res.num_turns, 1)
        # transcript written under BOB_HOME, named <ts>-<name>.json
        self.assertTrue(os.path.exists(res.transcript_path))
        self.assertTrue(res.transcript_path.endswith("-ideate.json"))
        self.assertIn(
            os.path.join(self.home, "state", "transcripts"), res.transcript_path
        )
        # daybook telemetry row present with all pinned keys
        steps = self.today_steps()
        self.assertEqual(len(steps), 1)
        for key in ("name", "model", "wall_s", "num_turns", "cost_usd", "subtype"):
            self.assertIn(key, steps[0])
        self.assertEqual(steps[0]["name"], "ideate")
        self.assertEqual(steps[0]["cost_usd"], 0.01)

    def test_mock_missing_fixture_is_actionable_agent_error(self):
        os.environ["BOB_MOCK_AGENTS"] = "1"
        with self.assertRaises(agents.AgentError) as cm:
            agents.run_agent("no-such-agent", "hello")
        self.assertIn("tests/fixtures/no-such-agent.txt", str(cm.exception))

    def test_mock_home_fixture_overrides_repo_fixture(self):
        os.environ["BOB_MOCK_AGENTS"] = "1"
        fdir = os.path.join(self.home, "tests", "fixtures")
        os.makedirs(fdir)
        with open(os.path.join(fdir, "ideate.txt"), "w") as f:
            f.write("home-planted reply")
        res = agents.run_agent("ideate", "x")
        self.assertEqual(res.text, "home-planted reply")


class TestModelResolution(Base):
    def test_explicit_beats_env_beats_default(self):
        os.environ["BOB_IDEATE_MODEL"] = "claude-opus-5"
        self.assertEqual(
            agents.resolve_model("ideate", "claude-haiku-5"), "claude-haiku-5"
        )
        self.assertEqual(agents.resolve_model("ideate"), "claude-opus-5")
        del os.environ["BOB_IDEATE_MODEL"]
        self.assertEqual(agents.resolve_model("ideate"), agents.DEFAULT_MODEL)
        self.assertEqual(agents.DEFAULT_MODEL, "claude-sonnet-5")

    def test_dashes_map_to_underscores_in_phase_env(self):
        os.environ["BOB_RULES_LENS_MODEL"] = "claude-opus-5"
        self.assertEqual(agents.resolve_model("rules-lens"), "claude-opus-5")

    def test_resolved_model_lands_in_cli_argv_and_daybook(self):
        argv_out = os.path.join(self.home, "argv.json")
        os.environ["FAKE_ARGV_OUT"] = argv_out
        os.environ["BOB_IDEATE_MODEL"] = "claude-opus-5"
        self.use_fake_cli("success")
        agents.run_agent("ideate", "go")
        with open(argv_out) as f:
            argv = json.load(f)
        self.assertEqual(argv[argv.index("--model") + 1], "claude-opus-5")
        self.assertEqual(self.today_steps()[0]["model"], "claude-opus-5")


class TestCliFlags(Base):
    def test_flags_without_cwd_have_no_tools(self):
        argv_out = os.path.join(self.home, "argv.json")
        os.environ["FAKE_ARGV_OUT"] = argv_out
        self.use_fake_cli("success")
        agents.run_agent("judge", "score this", max_turns=13)
        with open(argv_out) as f:
            argv = json.load(f)
        self.assertEqual(argv[:2], ["-p", "score this"])
        self.assertEqual(argv[argv.index("--max-turns") + 1], "13")
        self.assertEqual(argv[argv.index("--output-format") + 1], "json")
        self.assertNotIn("--allowedTools", argv)

    def test_cwd_adds_allowed_tools(self):
        argv_out = os.path.join(self.home, "argv.json")
        os.environ["FAKE_ARGV_OUT"] = argv_out
        self.use_fake_cli("success")
        agents.run_agent("build", "make the part", cwd=self.home)
        with open(argv_out) as f:
            argv = json.load(f)
        self.assertIn("--allowedTools", argv)
        self.assertEqual(
            argv[argv.index("--allowedTools") + 1], "Bash,Read,Write,Edit,Glob,Grep"
        )


class TestClassification(Base):
    """Starved vs crashed vs quota — opposite fixes, distinct exceptions."""

    def test_success_parses_cli_json(self):
        self.use_fake_cli("success")
        res = agents.run_agent("ideate", "go")
        self.assertEqual(res.text, "the canned CLI answer")
        self.assertEqual(res.cost_usd, 0.1234)
        self.assertEqual(res.num_turns, 7)
        self.assertEqual(res.subtype, "success")
        # transcript is the full CLI stdout, verbatim JSON
        with open(res.transcript_path) as f:
            payload = json.load(f)
        self.assertEqual(payload["total_cost_usd"], 0.1234)

    def test_error_max_turns_raises_starved(self):
        self.use_fake_cli("starved")
        with self.assertRaises(agents.Starved) as cm:
            agents.run_agent("build", "go", max_turns=40)
        # the message must steer the caller: raise cap or cut task
        self.assertIn("NEVER retry at the same cap", str(cm.exception))
        step = self.today_steps()[0]
        self.assertEqual(step["subtype"], "error_max_turns")
        self.assertEqual(step["cost_usd"], 0.42)  # starved money still counted

    def test_other_error_raises_retryable_agent_error(self):
        self.use_fake_cli("crashed")
        with self.assertRaises(agents.AgentError) as cm:
            agents.run_agent("lens", "go")
        self.assertNotIsInstance(cm.exception, agents.Starved)
        self.assertIn("retry once", str(cm.exception).lower())

    def test_quota_text_raises_quota_exhausted(self):
        self.use_fake_cli("quota")
        with self.assertRaises(agents.QuotaExhausted):
            agents.run_agent("ideate", "go")
        self.assertEqual(self.today_steps()[0]["subtype"], "quota")

    def test_quota_on_stderr_with_garbage_stdout(self):
        self.use_fake_cli("quota_stderr")
        with self.assertRaises(agents.QuotaExhausted):
            agents.run_agent("ideate", "go")

    def test_quota_is_not_an_agent_error(self):
        # a generic retry-once handler must never swallow a quota death
        self.assertFalse(issubclass(agents.QuotaExhausted, agents.AgentError))

    def test_garbage_output_is_crashed_not_quota(self):
        self.use_fake_cli("garbage")
        with self.assertRaises(agents.AgentError) as cm:
            agents.run_agent("ideate", "go")
        self.assertNotIsInstance(cm.exception, agents.Starved)
        self.assertEqual(self.today_steps()[0]["subtype"], "crashed_no_json")

    def test_starved_is_agent_error_subclass_for_park_paths(self):
        # callers that park on any agent failure may catch AgentError alone
        self.assertTrue(issubclass(agents.Starved, agents.AgentError))


class TestOverrunKill(Base):
    def test_overrun_is_killed_and_logged(self):
        self.use_fake_cli("hang")
        t0 = time.monotonic()
        with self.assertRaises(agents.AgentError) as cm:
            # 0.03 min = 1.8s ceiling; stub sleeps 600s
            agents.run_agent("build", "go", max_minutes=0.03)
        elapsed = time.monotonic() - t0
        self.assertLess(elapsed, 30.0)  # killed, not waited out
        self.assertIn("killed", str(cm.exception).lower())
        self.assertEqual(self.today_steps()[0]["subtype"], "killed_overrun")


class TestDaybook(Base):
    def test_repeat_names_get_suffixes_never_overwrite(self):
        os.environ["BOB_MOCK_AGENTS"] = "1"
        for _ in range(3):
            agents.run_agent("ideate", "x")
        names = [s["name"] for s in self.today_steps()]
        self.assertEqual(names, ["ideate", "ideate#2", "ideate#3"])

    def test_concurrent_appends_lose_nothing(self):
        """text2cad's 12%-low receipt: parallel panel calls must not clobber
        each other's telemetry rows. 12 threads, 12 rows, exact cost sum."""
        os.environ["BOB_MOCK_AGENTS"] = "1"
        with ThreadPoolExecutor(max_workers=6) as pool:
            futs = [pool.submit(agents.run_agent, "judge", "x") for _ in range(12)]
            for f in futs:
                f.result()
        steps = self.today_steps()
        self.assertEqual(len(steps), 12)
        self.assertEqual(len(set(s["name"] for s in steps)), 12)  # all unique
        book = self.daybook()
        day = [k for k in book if k != "heartbeat"][0]
        self.assertAlmostEqual(book[day]["cost_usd"], 0.12, places=6)

    def test_corrupt_daybook_preserved_not_erased(self):
        state = os.path.join(self.home, "state")
        os.makedirs(state)
        book = os.path.join(state, "DAYBOOK.json")
        with open(book, "w") as f:
            f.write("{ this is not json")
        os.environ["BOB_MOCK_AGENTS"] = "1"
        agents.run_agent("ideate", "x")
        self.assertTrue(os.path.exists(book + ".corrupt"))
        self.assertEqual(len(self.today_steps()), 1)


if __name__ == "__main__":
    unittest.main()
