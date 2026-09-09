"""A failed Claude turn must still leave the real session id resumable."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from workshop.runtime.claude import (
    ClaudeInvocationError,
    ClaudeNativeSessionLauncher,
    _error_turn_detail,
)


REAL_SESSION = "8af587ef-86ac-4085-97ca-79162ea721be"


class _FakeProcess:
    """Emit one init event, then a failing result event, like the CLI does."""

    def __init__(self, lines: list[str]) -> None:
        self.stdout = iter(lines)
        self.stderr = iter(())
        self.returncode = 0

    def wait(self, timeout=None):  # noqa: ANN001 - test double
        return 0

    def kill(self) -> None:
        return None


def _popen_factory(lines: list[str]):
    def factory(*args, **kwargs):  # noqa: ANN002, ANN003 - test double
        return _FakeProcess(lines)

    return factory


class FailedTurnStillBindsTheSessionTest(unittest.TestCase):
    def _launch(self, lines: list[str], directory: str):
        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/echo",
            cli_version="2.1.259",
            popen_factory=_popen_factory(lines),
        )
        root = Path(directory)
        run_root = root / "workspace"
        state = root / "state"
        run_root.mkdir()
        state.mkdir()
        return launcher, run_root, state

    def _checkpoint(self, state: Path) -> dict:
        return json.loads((state / "claude-session.json").read_text(encoding="utf-8"))

    def test_error_turn_records_the_id_the_cli_actually_created(self) -> None:
        lines = [
            json.dumps({"type": "system", "subtype": "init", "session_id": REAL_SESSION}),
            json.dumps(
                {
                    "type": "result",
                    "subtype": "error_during_execution",
                    "is_error": True,
                    "session_id": REAL_SESSION,
                    "errors": ["No conversation found with session ID: stale"],
                }
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            launcher, run_root, state = self._launch(lines, directory)
            with self.assertRaises(ClaudeInvocationError):
                launcher.start(
                    product_id="wish-one",
                    wish_sha256="0" * 64,
                    constitution_sha256="1" * 64,
                    run_root=run_root,
                    host_state_root=state,
                    prompt="do the stage",
                )
            # The turn failed, but the conversation exists: a resume must be
            # able to reach it rather than a placeholder id the CLI never made.
            self.assertEqual(self._checkpoint(state)["session_id"], REAL_SESSION)

    def test_successful_turn_also_binds_the_observed_id(self) -> None:
        lines = [
            json.dumps({"type": "system", "subtype": "init", "session_id": REAL_SESSION}),
            json.dumps({"type": "result", "subtype": "success", "is_error": False}),
        ]
        with tempfile.TemporaryDirectory() as directory:
            launcher, run_root, state = self._launch(lines, directory)
            outcome = launcher.start(
                product_id="wish-one",
                wish_sha256="0" * 64,
                constitution_sha256="1" * 64,
                run_root=run_root,
                host_state_root=state,
                prompt="do the stage",
            )
        self.assertEqual(outcome.session_id, REAL_SESSION)

    def test_checkpoint_digest_matches_the_rebound_identity(self) -> None:
        lines = [
            json.dumps({"type": "system", "subtype": "init", "session_id": REAL_SESSION}),
            json.dumps({"type": "result", "subtype": "success", "is_error": False}),
        ]
        with tempfile.TemporaryDirectory() as directory:
            launcher, run_root, state = self._launch(lines, directory)
            outcome = launcher.start(
                product_id="wish-one",
                wish_sha256="0" * 64,
                constitution_sha256="1" * 64,
                run_root=run_root,
                host_state_root=state,
                prompt="do the stage",
            )
            stored = self._checkpoint(state)
        self.assertEqual(stored["checkpoint_sha256"], outcome.checkpoint_sha256)


class ErrorTurnDetailTest(unittest.TestCase):
    def test_the_cli_diagnosis_survives_into_the_message(self) -> None:
        detail = _error_turn_detail(
            {
                "is_error": True,
                "subtype": "error_during_execution",
                "errors": ["No conversation found with session ID: abc"],
            }
        )
        self.assertIn("No conversation found", detail)
        self.assertIn("error_during_execution", detail)

    def test_a_bare_error_still_reports_something(self) -> None:
        self.assertEqual(
            _error_turn_detail({"is_error": True}),
            "Claude Code reported an error turn",
        )

    def test_detail_is_bounded(self) -> None:
        detail = _error_turn_detail({"is_error": True, "errors": ["x" * 5_000]})
        self.assertLessEqual(len(detail), 500)


if __name__ == "__main__":
    unittest.main()
