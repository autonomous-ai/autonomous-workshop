#!/usr/bin/env python3
"""Run one bounded authenticated Codex acceptance route."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))
sys.path.insert(0, str(REPOSITORY))

from tests.end_to_end.mock_session_harness import (  # noqa: E402
    DEFAULT_ROUTE_TIMEOUT_SECONDS,
    DEFAULT_TURN_TIMEOUT_SECONDS,
    EFFORT_ENVIRONMENT,
    ENABLE_ENVIRONMENT,
    HOME_ENVIRONMENT,
    PARTIAL_CONCEPT_ENVIRONMENT,
    SIMPLIFIED_CONCEPT_ENVIRONMENT,
    MockSessionPrerequisiteError,
    preflight_codex,
    redact_diagnostics,
    run_bounded_process,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one authenticated Codex session through a minimal, "
            "effort-aware Workshop context-and-integration acceptance route."
        )
    )
    parser.add_argument("--effort", choices=("spark", "forge", "quest"))
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_ROUTE_TIMEOUT_SECONDS,
        help="whole-route seconds",
    )
    parser.add_argument(
        "--turn-timeout",
        type=int,
        default=DEFAULT_TURN_TIMEOUT_SECONDS,
        help="per-Codex-turn seconds",
    )
    parser.add_argument(
        "--keep", action="store_true", help="keep isolated state after success"
    )
    parser.add_argument(
        "--partial-concept-roles",
        action="store_true",
        help="run the Forge partial Concept effect wait/resume acceptance",
    )
    parser.add_argument(
        "--simplified-concept",
        action="store_true",
        help="opt into the pre-activation Invent Concept v2 acceptance path",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="check Codex, authentication, CAD, and loopback fixture only",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="write a sanitized report outside the temporary state",
    )
    return parser.parse_args()


def _copy_sanitized_report(source: Path, destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise RuntimeError("--report destination already exists")
    value = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("mock-session report is malformed")
    value.pop("workspace", None)
    value.pop("host_state", None)
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _remove_isolated_home(home: Path) -> None:
    home = home.resolve()
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if (
        home.parent != temporary_root
        or not home.name.startswith("workshop-mock-session-")
        or home.is_symlink()
        or not home.is_dir()
    ):
        raise RuntimeError("refusing to remove a non-isolated mock-session home")
    for current, directories, unused_files in os.walk(
        home, topdown=True, followlinks=False
    ):
        del unused_files
        os.chmod(current, stat.S_IRWXU)
        for name in directories:
            path = Path(current) / name
            if not path.is_symlink():
                os.chmod(path, stat.S_IRWXU)
    shutil.rmtree(home)


def main() -> int:
    arguments = _arguments()
    if not 1 <= arguments.turn_timeout <= 3600:
        raise SystemExit("--turn-timeout must be from 1 to 3600 seconds")
    if not 1 <= arguments.timeout <= 21600:
        raise SystemExit("--timeout must be from 1 to 21600 seconds")
    if not arguments.preflight_only and arguments.effort is None:
        raise SystemExit("--effort is required unless --preflight-only is used")
    if arguments.partial_concept_roles and arguments.effort != "forge":
        raise SystemExit("--partial-concept-roles requires --effort forge")
    if arguments.simplified_concept and arguments.effort not in ("forge", "quest"):
        raise SystemExit("--simplified-concept requires --effort forge or quest")
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

    effort = str(arguments.effort)
    home = Path(tempfile.mkdtemp(prefix="workshop-mock-session-%s-" % effort)).resolve()
    os.chmod(home, 0o700)
    environment = dict(os.environ)
    environment.update(
        {
            ENABLE_ENVIRONMENT: "1",
            HOME_ENVIRONMENT: str(home),
            EFFORT_ENVIRONMENT: effort,
            "WORKSHOP_MOCK_SESSION_TURN_TIMEOUT": str(arguments.turn_timeout),
            PARTIAL_CONCEPT_ENVIRONMENT: (
                "1" if arguments.partial_concept_roles else "0"
            ),
            SIMPLIFIED_CONCEPT_ENVIRONMENT: (
                "1" if arguments.simplified_concept else "0"
            ),
            "PYTHONPATH": os.pathsep.join(
                (str(REPOSITORY / "src"), str(REPOSITORY))
            ),
        }
    )
    test_target = (
        "tests.end_to_end.test_mock_session_live."
        "RealCodexMockSessionEndToEndTest."
        "test_forge_partial_concept_effect_wait_reconciles_without_repeating_invent"
        if arguments.partial_concept_roles
        else "tests.end_to_end.test_mock_session_live.RealCodexMockSessionEndToEndTest"
    )
    command = [
        sys.executable,
        "-m",
        "unittest",
        test_target,
    ]
    result = run_bounded_process(
        command,
        cwd=REPOSITORY,
        environment=environment,
        timeout_seconds=arguments.timeout,
    )
    print(redact_diagnostics(result.stdout), end="")
    print(redact_diagnostics(result.stderr), end="", file=sys.stderr)
    report_path = home / ("mock-session-report-%s.json" % effort)
    if result.timed_out:
        print(
            "mock-session %s exceeded %d seconds; redacted diagnostics retained at %s"
            % (effort, arguments.timeout, home),
            file=sys.stderr,
        )
        return 124
    if result.returncode != 0:
        print(
            "mock-session %s failed; redacted diagnostics retained at %s"
            % (effort, home),
            file=sys.stderr,
        )
        return result.returncode
    if not report_path.is_file():
        print(
            "mock-session succeeded without its bounded report; state retained at %s"
            % home,
            file=sys.stderr,
        )
        return 1
    if arguments.report is not None:
        try:
            _copy_sanitized_report(report_path, arguments.report)
        except (OSError, RuntimeError, ValueError) as exc:
            print("could not write sanitized report: %s" % exc, file=sys.stderr)
            return 1
        print("Sanitized report written to %s" % arguments.report.resolve())
    if arguments.keep:
        print("Mock-session state retained at %s" % home)
    else:
        _remove_isolated_home(home)
        print("Mock-session isolated state removed after success")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
