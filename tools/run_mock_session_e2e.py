#!/usr/bin/env python3
"""Run the opt-in real-Codex mock-session E2E under a whole-run budget."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))
sys.path.insert(0, str(REPOSITORY))

from tests.end_to_end.mock_session_harness import (  # noqa: E402
    ENABLE_ENVIRONMENT,
    HOME_ENVIRONMENT,
    MockSessionPrerequisiteError,
    preflight_codex,
    redact_diagnostics,
    run_bounded_process,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one authenticated real Codex session through the minimal "
            "Workshop context-and-integration acceptance scenario."
        )
    )
    parser.add_argument("--timeout", type=int, default=1800, help="whole-run seconds")
    parser.add_argument("--turn-timeout", type=int, default=300, help="per-Codex-turn seconds")
    parser.add_argument("--model", default="gpt-5.6-luna", choices=("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"))
    parser.add_argument("--reasoning-effort", default="low", choices=("low", "medium", "high", "xhigh"))
    parser.add_argument("--keep", action="store_true", help="keep the isolated home after success")
    parser.add_argument("--preflight-only", action="store_true", help="check Codex and authentication only")
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    if not 1 <= arguments.turn_timeout <= 3600:
        raise SystemExit("--turn-timeout must be from 1 to 3600 seconds")
    if not 1 <= arguments.timeout <= 21600:
        raise SystemExit("--timeout must be from 1 to 21600 seconds")
    try:
        preflight = preflight_codex()
    except MockSessionPrerequisiteError as exc:
        print("mock-session preflight failed: %s" % exc, file=sys.stderr)
        return 2
    print(
        "Mock-session preflight passed: Codex %s (%s); CAD Python %s"
        % (preflight.binary, preflight.version, preflight.python)
    )
    if arguments.preflight_only:
        return 0

    home = Path(tempfile.mkdtemp(prefix="workshop-mock-session-e2e-")).resolve()
    os.chmod(home, 0o700)
    environment = dict(os.environ)
    environment.update(
        {
            ENABLE_ENVIRONMENT: "1",
            HOME_ENVIRONMENT: str(home),
            "WORKSHOP_MOCK_SESSION_TURN_TIMEOUT": str(arguments.turn_timeout),
            "WORKSHOP_MOCK_SESSION_MODEL": arguments.model,
            "WORKSHOP_MOCK_SESSION_REASONING_EFFORT": arguments.reasoning_effort,
            "PYTHONPATH": os.pathsep.join(
                (str(REPOSITORY / "src"), str(REPOSITORY))
            ),
        }
    )
    command = [
        sys.executable,
        "-m",
        "unittest",
        "tests.end_to_end.test_mock_session_live.RealCodexMockSessionEndToEndTest",
    ]
    result = run_bounded_process(
        command,
        cwd=str(REPOSITORY),
        environment=environment,
        timeout_seconds=arguments.timeout,
    )
    print(redact_diagnostics(result.stdout), end="")
    print(redact_diagnostics(result.stderr), end="", file=sys.stderr)
    manifest_path = home / "mock-session-diagnostics.json"
    manifest = None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    diagnostic_workspace = manifest.get("workspace") if isinstance(manifest, dict) else None
    if result.timed_out:
        print(
            "mock-session E2E exceeded %d seconds; diagnostics retained at %s%s"
            % (
                arguments.timeout,
                home,
                " (workspace %s)" % diagnostic_workspace if diagnostic_workspace else "",
            ),
            file=sys.stderr,
        )
        return 124
    if result.returncode != 0:
        print(
            "mock-session E2E failed; diagnostics retained at %s%s"
            % (
                home,
                " (workspace %s)" % diagnostic_workspace if diagnostic_workspace else "",
            ),
            file=sys.stderr,
        )
        return result.returncode
    if arguments.keep:
        print("mock-session diagnostics retained at %s" % home)
    else:
        if isinstance(diagnostic_workspace, str):
            workspace = Path(diagnostic_workspace)
            toys_root = REPOSITORY / "toys"
            if workspace.parent == toys_root and workspace.name.startswith(
                "mock-session-pocket-token-"
            ):
                shutil.rmtree(workspace)
        shutil.rmtree(home)
        print("mock-session isolated home removed after success")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
