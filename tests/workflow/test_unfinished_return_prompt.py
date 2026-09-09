"""An empty native return must tell the agent what the next one costs.

The host cannot read why a turn returned without `agent-outcome.json`; it only
sees that none was written.  What it can say is how many empty returns this
subject has spent and that the next one ends the invocation, so a genuinely
blocked Goal seals a truthful need instead of repeating a failed repair until a
cap stops it.
"""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workshop.workflow.budgets import LifetimeBudget
from workshop.workflow.native_run import (
    _MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS,
    _launcher_call,
    _unfinished_return_stop_armed,
)
from workshop.workflow.token_budget import ProductTokenBudget


class CapturingLauncher:
    def __init__(self):
        self.calls = []

    def resume(self, **arguments):
        self.calls.append(arguments)
        return "session"

    start = resume


class UnfinishedReturnPromptTest(unittest.TestCase):
    def prompt(self, *, unfinished_returns, armed, stage="make"):
        checkpoint = SimpleNamespace(
            manager_id="codex",
            stage=stage,
            effort="spark",
            product_id="wish-20260909-000000-aaaaaaaa",
            wish_sha256="a" * 64,
            input_sha256s={},
        )
        paths = SimpleNamespace(
            workspace=Path("/tmp/workspace"),
            host_state=Path("/tmp/host-state"),
        )
        launcher = CapturingLauncher()
        with mock.patch(
            "workshop.workflow.native_run._load_lifetime_budget",
            return_value=None,
        ), mock.patch(
            "workshop.workflow.native_run."
            "materialized_agent_instructions_sha256",
            return_value="b" * 64,
        ):
            _launcher_call(
                launcher,
                "resume",
                checkpoint=checkpoint,
                paths=paths,
                unfinished_returns=unfinished_returns,
                unfinished_stop_armed=armed,
            )
        return launcher.calls[0]["prompt"]

    def test_a_first_turn_carries_no_empty_return_text(self):
        prompt = self.prompt(unfinished_returns=0, armed=True)
        self.assertNotIn("returned without agent-outcome.json", prompt)
        self.assertNotIn("empty return", prompt)

    def test_an_early_empty_return_reports_its_position(self):
        prompt = self.prompt(unfinished_returns=1, armed=True)
        self.assertIn("returned without agent-outcome.json", prompt)
        self.assertIn(
            "This is empty return 1 of the %d this invocation allows"
            % _MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS,
            prompt,
        )
        # Not the last one yet, so no exit route is offered.
        self.assertNotIn("ends this invocation", prompt)

    def test_the_last_allowed_return_offers_the_truthful_need_route(self):
        prompt = self.prompt(
            unfinished_returns=_MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS - 1,
            armed=True,
        )
        self.assertIn("ends this invocation", prompt)
        self.assertIn(
            "--run-root . need --stage make --status waiting|failed", prompt
        )
        self.assertIn("do not repeat the attempt that already failed", prompt)

    def test_the_named_stage_follows_the_checkpoint(self):
        prompt = self.prompt(
            unfinished_returns=_MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS - 1,
            armed=True,
            stage="release",
        )
        self.assertIn("--stage release --status", prompt)
        self.assertNotIn("--stage make --status", prompt)

    def test_an_unarmed_run_is_not_promised_a_stop_it_will_not_get(self):
        prompt = self.prompt(
            unfinished_returns=_MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS - 1,
            armed=False,
        )
        self.assertIn("returned without agent-outcome.json", prompt)
        self.assertNotIn("empty return", prompt)
        self.assertNotIn("ends this invocation", prompt)

    def test_the_prompt_reads_the_same_condition_the_loop_enforces(self):
        self.assertTrue(_unfinished_return_stop_armed(None))
        self.assertTrue(
            _unfinished_return_stop_armed(ProductTokenBudget(1_000_000))
        )
        # Legacy clock and turn-budget runs keep unbounded continuation.
        self.assertFalse(_unfinished_return_stop_armed(LifetimeBudget()))


if __name__ == "__main__":
    unittest.main()
