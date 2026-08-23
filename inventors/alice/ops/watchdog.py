#!/usr/bin/env python3
"""Independent Alice watchdog installed outside the mutable source checkout."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Callable, Mapping, Sequence
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


HEALTH_SCHEMA_VERSION = 2
RATE_SCHEMA_VERSION = 1
RECEIPT_SCHEMA_VERSION = 1
MAX_FILE_BYTES = 1024 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_TARGET = re.compile(r"^gui/[1-9][0-9]*/ai\.autonomous\.alice\.worker$")
_HEALTH_KEYS = frozenset(
    {
        "schema_version",
        "started_at",
        "heartbeat_at",
        "success_at",
        "failure_at",
        "tick_started_at",
        "consecutive_failures",
        "source_tree_sha256",
        "config_sha256",
        "policy_hash",
        "effect_mode",
        "pid",
        "message_hash",
    }
)


class WatchdogError(RuntimeError):
    pass


def _hash(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8", errors="replace")).hexdigest()


def _positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive and finite")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def _absolute(value: str, name: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise WatchdogError(f"{name} must be absolute")
    return path


def _check_components(path: Path, *, allow_missing_leaf: bool = False) -> None:
    current = Path(path.anchor)
    parts = path.parts[1:]
    for index, part in enumerate(parts):
        current /= part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            if allow_missing_leaf and index == len(parts) - 1:
                continue
            raise WatchdogError("required path component is unavailable")
        except OSError as exc:
            raise WatchdogError("required path component could not be inspected") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise WatchdogError("symlink path components are not allowed")


def _read_owner_file(path: Path, *, exact_mode: int, maximum: int = MAX_FILE_BYTES) -> bytes:
    _check_components(path)
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise WatchdogError("required state is unavailable") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != exact_mode
        or metadata.st_uid != os.geteuid()
        or metadata.st_size > maximum
    ):
        raise WatchdogError("required state is not an owner-only regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise WatchdogError("required state could not be opened safely") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino)
            or stat.S_IMODE(opened.st_mode) != exact_mode
            or opened.st_uid != os.geteuid()
        ):
            raise WatchdogError("required state changed while opening")
        content = os.read(descriptor, maximum + 1)
    finally:
        os.close(descriptor)
    if len(content) > maximum:
        raise WatchdogError("required state exceeds its size bound")
    return content


def load_env(path: Path) -> dict[str, str]:
    content = _read_owner_file(path, exact_mode=0o600)
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WatchdogError("environment file is not UTF-8") from exc
    values: dict[str, str] = {}
    for line_number, original in enumerate(text.splitlines(), start=1):
        line = original.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise WatchdogError(f"invalid environment assignment on line {line_number}")
        name, raw = line.split("=", 1)
        name = name.strip()
        raw = raw.strip()
        if (
            not _ENV_NAME.fullmatch(name)
            or name in values
            or name in {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR"}
            or name.startswith("PYTHON")
            or name.startswith("DYLD_")
            or name.startswith("GIT_")
        ):
            raise WatchdogError(f"invalid environment name on line {line_number}")
        if raw.startswith("'"):
            if len(raw) < 2 or not raw.endswith("'"):
                raise WatchdogError(f"invalid environment value on line {line_number}")
            value = raw[1:-1]
        elif raw.startswith('"'):
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise WatchdogError(
                    f"invalid environment value on line {line_number}"
                ) from exc
            if not isinstance(value, str):
                raise WatchdogError(f"invalid environment value on line {line_number}")
        else:
            value = raw
        values[name] = value
    return values


def _parse_time(value: object, field: str, *, optional: bool = False) -> datetime | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.endswith("Z"):
        raise WatchdogError(f"invalid {field}")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise WatchdogError(f"invalid {field}") from exc


def read_health(path: Path) -> dict[str, object]:
    content = _read_owner_file(path, exact_mode=0o600)
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WatchdogError("health state is unreadable") from exc
    if not isinstance(value, dict) or set(value) != _HEALTH_KEYS:
        raise WatchdogError("health state schema is invalid")
    if value.get("schema_version") != HEALTH_SCHEMA_VERSION or isinstance(
        value.get("schema_version"), bool
    ):
        raise WatchdogError("health state version is invalid")
    for field in ("started_at", "heartbeat_at"):
        _parse_time(value.get(field), field)
    for field in ("success_at", "failure_at", "tick_started_at"):
        _parse_time(value.get(field), field, optional=True)
    for field in (
        "source_tree_sha256",
        "config_sha256",
        "policy_hash",
    ):
        if not isinstance(value.get(field), str) or not _SHA256.fullmatch(str(value[field])):
            raise WatchdogError("health identity is invalid")
    failures = value.get("consecutive_failures")
    pid = value.get("pid")
    if isinstance(failures, bool) or not isinstance(failures, int) or failures < 0:
        raise WatchdogError("health failure count is invalid")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise WatchdogError("health PID is invalid")
    if value.get("effect_mode") not in {"dry-run", "draft", "live"}:
        raise WatchdogError("health effect mode is invalid")
    digest = value.get("message_hash")
    if digest is not None and (
        not isinstance(digest, str) or not _SHA256.fullmatch(digest)
    ):
        raise WatchdogError("health message hash is invalid")
    return value


def health_problems(
    health: Mapping[str, object],
    *,
    expected: Mapping[str, str],
    stale_seconds: float,
    max_tick_seconds: float,
    max_consecutive_failures: int,
    now: datetime | None = None,
) -> tuple[str, ...]:
    observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    problems: list[str] = []
    heartbeat = _parse_time(health["heartbeat_at"], "heartbeat_at")
    assert heartbeat is not None
    age = (observed - heartbeat).total_seconds()
    heartbeat_is_fresh = -5 <= age <= stale_seconds
    if age < -5:
        problems.append("heartbeat_from_future")
    elif age > stale_seconds:
        problems.append("stale_heartbeat")
    tick_started = _parse_time(health["tick_started_at"], "tick_started_at", optional=True)
    bounded_active_tick = False
    if tick_started is not None:
        tick_age = (observed - tick_started).total_seconds()
        if tick_age < -5:
            problems.append("tick_started_from_future")
        elif tick_age > max_tick_seconds:
            problems.append("overlong_tick")
        elif heartbeat_is_fresh:
            bounded_active_tick = True
    if (
        int(health["consecutive_failures"]) >= max_consecutive_failures
        and not bounded_active_tick
    ):
        problems.append("repeated_failures")
    for field, expected_value in expected.items():
        if health.get(field) != expected_value:
            problems.append("identity_mismatch")
            break
    return tuple(problems)


def _atomic_json(path: Path, value: Mapping[str, object]) -> None:
    _check_components(path.parent, allow_missing_leaf=True)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    _check_components(path.parent)
    parent_metadata = path.parent.lstat()
    if (
        not stat.S_ISDIR(parent_metadata.st_mode)
        or stat.S_IMODE(parent_metadata.st_mode) != 0o700
        or parent_metadata.st_uid != os.geteuid()
    ):
        raise WatchdogError("watchdog state parent must be owner-only")
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=".alert-rate-")
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        try:
            payload = (
                json.dumps(
                    value,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                + "\n"
            ).encode()
        except (TypeError, ValueError) as exc:
            raise WatchdogError("watchdog state is not finite JSON") from exc
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _check_components(path.parent)
        os.replace(temporary, path)
        os.chmod(path, 0o600, follow_symlinks=False)
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def alert_due(rate_state: Path, *, now_epoch: float, interval_seconds: float) -> bool:
    try:
        value = json.loads(_read_owner_file(rate_state, exact_mode=0o600).decode("utf-8"))
    except WatchdogError:
        return True
    except (UnicodeDecodeError, json.JSONDecodeError):
        return True
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "last_alert_epoch",
        "message_hash",
    }:
        return True
    last = value.get("last_alert_epoch")
    if (
        value.get("schema_version") != RATE_SCHEMA_VERSION
        or isinstance(value.get("schema_version"), bool)
        or isinstance(last, bool)
        or not isinstance(last, (int, float))
        or not math.isfinite(float(last))
    ):
        return True
    return now_epoch - float(last) >= interval_seconds


def in_startup_grace(
    script_path: Path, *, now_epoch: float, grace_seconds: float
) -> bool:
    try:
        metadata = script_path.lstat()
    except OSError:
        return False
    return (
        stat.S_ISREG(metadata.st_mode)
        and 0 <= now_epoch - metadata.st_mtime < grace_seconds
    )


def mark_alert(rate_state: Path, *, now_epoch: float, digest: str) -> None:
    _atomic_json(
        rate_state,
        {
            "schema_version": RATE_SCHEMA_VERSION,
            "last_alert_epoch": now_epoch,
            "message_hash": digest,
        },
    )


def write_receipt(
    path: Path,
    *,
    expected: Mapping[str, str],
    healthy: bool,
    action: str,
    digest: str,
    now: datetime | None = None,
) -> None:
    if action not in {"none", "startup_grace", "restart_requested", "internal_error"}:
        raise WatchdogError("watchdog receipt action is invalid")
    if not _SHA256.fullmatch(digest):
        raise WatchdogError("watchdog receipt digest is invalid")
    checked = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    _atomic_json(
        path,
        {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "checked_at": checked.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
            "healthy": healthy,
            "action": action,
            **expected,
            "message_hash": digest,
        },
    )


def send_webhook(
    values: Mapping[str, str],
    payload: Mapping[str, object],
    *,
    opener: Callable[..., object] = urlopen,
) -> bool:
    url = values.get("ALICE_ALERT_WEBHOOK_URL")
    if not url:
        return False
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise WatchdogError("alert webhook must be a clean HTTPS URL")
    headers = {"Content-Type": "application/json"}
    token = values.get("ALICE_ALERT_BEARER_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        url,
        data=json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        response = opener(request, timeout=5)
        response.read(1025)
        response.close()
        return True
    except Exception as exc:
        raise WatchdogError("alert webhook failed") from exc


def recover_launchd_target(
    target: str,
    *,
    command: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
    sleeper: Callable[[float], None] = time.sleep,
    grace_seconds: float = 12.0,
) -> None:
    """Recover only the exact launchd-owned worker label, never a heartbeat PID."""

    if not _TARGET.fullmatch(target) or target != (
        f"gui/{os.getuid()}/ai.autonomous.alice.worker"
    ):
        raise WatchdogError("worker launchd target is invalid")
    launchctl = "/bin/launchctl"
    common = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "timeout": 15,
        "check": False,
    }
    try:
        present = command([launchctl, "print", target], **common)
    except (OSError, subprocess.SubprocessError) as exc:
        raise WatchdogError("worker launchd label could not be inspected") from exc
    if present.returncode != 0:
        raise WatchdogError("worker launchd label is unavailable")
    try:
        terminated = command([launchctl, "kill", "SIGTERM", target], **common)
    except (OSError, subprocess.SubprocessError) as exc:
        raise WatchdogError("worker launchd TERM request failed") from exc
    if terminated.returncode != 0:
        raise WatchdogError("launchd refused the worker TERM request")
    sleeper(grace_seconds)
    # The worker places every tick behind a sealed guardian whose control pipe
    # reaches EOF if launchd hard-kills the worker.  It is therefore safe to
    # force this exact label without orphaning the tick process group.
    try:
        restarted = command([launchctl, "kickstart", "-k", target], **common)
    except (OSError, subprocess.SubprocessError) as exc:
        raise WatchdogError("worker launchd restart request failed") from exc
    if restarted.returncode != 0:
        raise WatchdogError("launchd refused the worker restart request")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alice-watchdog")
    parser.add_argument("--state", required=True)
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--rate-state", required=True)
    parser.add_argument("--watchdog-state", required=True)
    parser.add_argument("--launchd-target", required=True)
    parser.add_argument("--expected-source-tree-sha256", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    parser.add_argument("--expected-policy-hash", required=True)
    parser.add_argument("--expected-effect-mode", required=True)
    parser.add_argument("--stale-seconds", type=_positive_float, default=300.0)
    parser.add_argument("--max-tick-seconds", type=_positive_float, default=1800.0)
    parser.add_argument("--max-consecutive-failures", type=_positive_int, default=3)
    parser.add_argument("--alert-interval-seconds", type=_positive_float, default=900.0)
    parser.add_argument("--startup-grace-seconds", type=_positive_float, default=120.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    state = _absolute(args.state, "health state")
    env_file = _absolute(args.env_file, "environment file")
    rate_state = _absolute(args.rate_state, "alert rate state")
    watchdog_state = _absolute(args.watchdog_state, "watchdog receipt")
    expected = {
        "source_tree_sha256": args.expected_source_tree_sha256.lower(),
        "config_sha256": args.expected_config_sha256.lower(),
        "policy_hash": args.expected_policy_hash.lower(),
        "effect_mode": args.expected_effect_mode,
    }
    if any(not _SHA256.fullmatch(expected[key]) for key in (
        "source_tree_sha256", "config_sha256", "policy_hash"
    )) or expected["effect_mode"] not in {"dry-run", "draft", "live"}:
        return 2
    try:
        try:
            health = read_health(state)
            problems = health_problems(
                health,
                expected=expected,
                stale_seconds=args.stale_seconds,
                max_tick_seconds=args.max_tick_seconds,
                max_consecutive_failures=args.max_consecutive_failures,
            )
        except WatchdogError:
            health = {}
            problems = ("health_unavailable",)
        if not problems:
            write_receipt(
                watchdog_state,
                expected=expected,
                healthy=True,
                action="none",
                digest=_hash("healthy"),
            )
            return 0

        digest = _hash("|".join(problems))
        now_epoch = time.time()
        # A reinstall may leave an old heartbeat until the newly pinned worker
        # finishes its own source/config verification.  Do not kill that worker
        # during the bounded installer health window.
        if in_startup_grace(
            Path(__file__),
            now_epoch=now_epoch,
            grace_seconds=args.startup_grace_seconds,
        ):
            write_receipt(
                watchdog_state,
                expected=expected,
                healthy=False,
                action="startup_grace",
                digest=digest,
            )
            return 2
        try:
            values = load_env(env_file)
            if alert_due(
                rate_state,
                now_epoch=now_epoch,
                interval_seconds=args.alert_interval_seconds,
            ):
                attempted = bool(values.get("ALICE_ALERT_WEBHOOK_URL"))
                try:
                    send_webhook(
                        values,
                        {
                            "service": "alice",
                            "problems": list(problems),
                            "message_hash": health.get("message_hash"),
                        },
                    )
                finally:
                    if attempted:
                        mark_alert(rate_state, now_epoch=now_epoch, digest=digest)
        except WatchdogError:
            # Alerting is optional; it must never disable label-scoped recovery.
            pass
        recover_launchd_target(args.launchd_target)
        write_receipt(
            watchdog_state,
            expected=expected,
            healthy=False,
            action="restart_requested",
            digest=digest,
        )
        return 2
    except WatchdogError:
        try:
            write_receipt(
                watchdog_state,
                expected=expected,
                healthy=False,
                action="internal_error",
                digest=_hash("watchdog-internal-error"),
            )
        except Exception:
            pass
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
