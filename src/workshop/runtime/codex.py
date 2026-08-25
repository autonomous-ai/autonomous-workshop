"""Bounded structured-output calls through an installed authenticated Codex CLI."""

from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import stat
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Mapping, Optional

from workshop.errors import ContractError
from workshop.runtime.execution import codex_subprocess_environment


ALLOWED_WORKSHOP_MODELS = frozenset(("gpt-5.6-terra", "gpt-5.6-luna"))
DEFAULT_CODEX_TIMEOUT_SECONDS = 1_200
MAX_CODEX_EVENT_BYTES = 1 * 1024 * 1024
MAX_CODEX_OUTPUT_BYTES = 1 * 1024 * 1024
MAX_CODEX_SESSION_CHECKPOINT_BYTES = 32 * 1024
CODEX_SESSION_CHECKPOINT_KIND = "autonomous-workshop-codex-session"
CODEX_RESEARCH_ROLE = "invent-research"
_MAX_TRANSIENT_DIAGNOSTIC_CHARS = 64 * 1024
_TRANSIENT_DIAGNOSTIC_MARKERS = (
    "stream disconnected before completion",
    "connection reset by peer",
    "connection closed before completion",
    "provider connection was closed",
    "provider stream disconnected",
    "service temporarily unavailable",
    "temporarily unavailable",
    "upstream request timeout",
)


class CodexInvocationError(RuntimeError):
    pass


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Codex session state must be finite JSON") from exc


def _sha256_json(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ContractError("%s must be a lowercase sha256" % label)
    return value


def _bounded_identifier(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 256
        or value != value.strip()
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be a bounded identifier" % label)
    return value


def _canonical_thread_id(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 64:
        raise ContractError("Codex session checkpoint thread identity is invalid")
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ContractError("Codex session checkpoint thread identity is invalid") from exc
    canonical = str(parsed)
    if value != canonical:
        raise ContractError("Codex session checkpoint thread identity is invalid")
    return canonical


def _path_sha256(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_session_root(value: Path) -> Path:
    requested = Path(value)
    if not requested.is_absolute():
        raise ContractError("Codex session root must be absolute")
    if requested.is_symlink():
        raise ContractError("Codex session root must not be a symlink")
    try:
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise ContractError("Codex session root must already exist") from exc
    if not root.is_dir():
        raise ContractError("Codex session root must be a directory")
    return root


def _resolve_runtime_root(value: Path, session_root: Path, *, create: bool) -> Path:
    requested = Path(value)
    if not requested.is_absolute():
        raise ContractError("Codex session runtime_root must be absolute")
    if requested.is_symlink():
        raise ContractError("Codex session runtime_root must not be a symlink")
    if not requested.exists():
        if not create:
            raise ContractError("Codex session checkpoint is missing")
        try:
            parent = requested.parent.resolve(strict=True)
        except OSError as exc:
            raise ContractError(
                "Codex session runtime_root parent must already exist"
            ) from exc
        if not _within(parent, session_root):
            raise ContractError("Codex session runtime_root must be inside its root")
        requested.mkdir(mode=0o700)
    try:
        runtime_root = requested.resolve(strict=True)
    except OSError as exc:
        raise ContractError("Codex session runtime_root is unavailable") from exc
    if not runtime_root.is_dir() or not _within(runtime_root, session_root):
        raise ContractError("Codex session runtime_root must be inside its root")
    return runtime_root


def _checkpoint_path(runtime_root: Path, product_id: str, *, create: bool) -> Path:
    directory = runtime_root / "agent-sessions"
    if directory.is_symlink():
        raise ContractError("Codex session checkpoint directory must not be a symlink")
    if not directory.exists():
        if not create:
            raise ContractError("Codex session checkpoint is missing")
        directory.mkdir(mode=0o700)
    if not directory.is_dir():
        raise ContractError("Codex session checkpoint directory must be a directory")
    if stat.S_IMODE(directory.stat().st_mode) & 0o077:
        try:
            os.chmod(directory, 0o700)
        except OSError as exc:
            raise ContractError("Codex session checkpoint directory is not private") from exc
    name = hashlib.sha256(product_id.encode("utf-8")).hexdigest() + ".json"
    return directory / name


def _write_private_checkpoint(path: Path, value: Mapping[str, Any]) -> None:
    source = _canonical_json(value) + b"\n"
    if len(source) > MAX_CODEX_SESSION_CHECKPOINT_BYTES:
        raise CodexInvocationError("Codex session checkpoint exceeded its safe size limit")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % path.name,
        suffix=".tmp",
        dir=str(path.parent),
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(source):
            written += os.write(descriptor, source[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        # A hard link gives us an atomic create-without-overwrite operation.
        # An unexpected existing target is never replaced or trusted here.
        os.link(str(temporary), str(path), follow_symlinks=False)
        directory_descriptor = os.open(
            str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except FileExistsError as exc:
        raise CodexInvocationError(
            "Codex session checkpoint already exists; resume it explicitly"
        ) from exc
    except CodexInvocationError:
        raise
    except OSError as exc:
        raise CodexInvocationError("Codex session checkpoint could not be persisted") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _read_private_checkpoint(path: Path) -> Mapping[str, Any]:
    try:
        expected = path.lstat()
    except FileNotFoundError as exc:
        raise ContractError("Codex session checkpoint is missing") from exc
    if path.is_symlink() or not stat.S_ISREG(expected.st_mode):
        raise ContractError("Codex session checkpoint must be a regular private file")
    if stat.S_IMODE(expected.st_mode) != 0o600:
        raise ContractError("Codex session checkpoint permissions must be 0600")
    if not 1 <= expected.st_size <= MAX_CODEX_SESSION_CHECKPOINT_BYTES:
        raise ContractError("Codex session checkpoint size is invalid")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ContractError("Codex session checkpoint cannot be read safely") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
        ):
            raise ContractError("Codex session checkpoint changed while opening")
        source = os.read(descriptor, MAX_CODEX_SESSION_CHECKPOINT_BYTES + 1)
        if len(source) > MAX_CODEX_SESSION_CHECKPOINT_BYTES or os.read(descriptor, 1):
            raise ContractError("Codex session checkpoint size is invalid")
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ContractError("Codex session checkpoint changed while reading")
    finally:
        os.close(descriptor)
    try:
        payload = json.loads(source.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Codex session checkpoint is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ContractError("Codex session checkpoint must contain one object")
    return payload


def _runtime_config_sha256(cli_version: str) -> str:
    return _sha256_json(
        {
            "adapter": "codex-cli",
            "allowed_models": sorted(ALLOWED_WORKSHOP_MODELS),
            "cli_version": cli_version,
            "event_protocol": "jsonl-thread-started-v1",
            "ignore_rules": True,
            "ignore_user_config": True,
            "sandbox": "read-only",
        }
    )


class CodexStructuredRunner:
    def __init__(
        self,
        *,
        model: str,
        reasoning_effort: str,
        binary: Optional[str] = None,
        timeout_seconds: int = DEFAULT_CODEX_TIMEOUT_SECONDS,
        runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
    ) -> None:
        if model not in ALLOWED_WORKSHOP_MODELS:
            raise ContractError(
                "Workshop Codex model must be gpt-5.6-terra or gpt-5.6-luna"
            )
        if reasoning_effort not in ("low", "medium", "high", "xhigh"):
            raise ValueError("unsupported Codex reasoning effort")
        if (
            type(timeout_seconds) is not int
            or not 1 <= timeout_seconds <= 3_600
        ):
            raise ValueError("Codex timeout_seconds must be from 1 to 3,600")
        self.binary = binary or os.environ.get("WORKSHOP_CODEX_BIN") or shutil.which("codex")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds
        self._runner = runner
        self.cli_version = cli_version or self._read_cli_version()
        self.last_used_web_search = False

    def _read_cli_version(self) -> str:
        if not self.binary:
            return "0.0.0"
        try:
            completed = self._runner(
                [self.binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                env=codex_subprocess_environment(),
            )
        except (OSError, subprocess.SubprocessError):
            return "0.0.0"
        output = completed.stdout if isinstance(completed.stdout, str) else ""
        match = re.search(r"\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9.-]+)?", output)
        return match.group(0) if match else "0.0.0"

    def invoke(
        self,
        *,
        prompt: str,
        schema: Mapping[str, Any],
        workspace: Optional[Path] = None,
        native_web_search: bool = False,
    ) -> Mapping[str, Any]:
        if not self.binary:
            raise CodexInvocationError("Codex CLI is not installed or on PATH")
        if type(native_web_search) is not bool:
            raise ValueError("native_web_search must be a boolean")

        self.last_used_web_search = False
        deadline = time.monotonic() + self.timeout_seconds
        for attempt in range(2):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CodexInvocationError("Codex structured call timed out")
            try:
                completed, output_bytes = self._run_attempt(
                    prompt=prompt,
                    schema=schema,
                    workspace=workspace,
                    native_web_search=native_web_search,
                    timeout_seconds=remaining,
                )
            except subprocess.TimeoutExpired as exc:
                exc.output = None
                exc.stderr = None
                raise CodexInvocationError("Codex structured call timed out") from None
            except (OSError, subprocess.SubprocessError, TypeError, ValueError) as exc:
                for attribute in ("output", "stdout", "stderr"):
                    if hasattr(exc, attribute):
                        setattr(exc, attribute, None)
                raise CodexInvocationError(
                    "Codex could not execute the structured call"
                ) from None

            stdout = completed.stdout if isinstance(completed.stdout, str) else ""
            stderr = completed.stderr if isinstance(completed.stderr, str) else ""
            if completed.returncode != 0:
                if attempt == 0 and _is_explicit_transient_failure(stdout, stderr):
                    continue
                if _is_explicit_transient_failure(stdout, stderr):
                    raise CodexInvocationError(
                        "Codex provider transport failed after one retry"
                    )
                raise CodexInvocationError("Codex did not complete the structured call")

            used_web_search = _jsonl_used_web_search(stdout)
            if native_web_search and not used_web_search:
                raise CodexInvocationError(
                    "Codex native web research completed without a web search event"
                )
            payload = _decode_bounded_payload(output_bytes)
            self.last_used_web_search = used_web_search
            return payload

        raise CodexInvocationError("Codex did not complete the structured call")

    def _run_attempt(
        self,
        *,
        prompt: str,
        schema: Mapping[str, Any],
        workspace: Optional[Path],
        native_web_search: bool,
        timeout_seconds: float,
    ):
        with tempfile.TemporaryDirectory(prefix="workshop-codex-") as temporary:
            control_root = Path(temporary)
            schema_path = control_root / "output.schema.json"
            output_path = control_root / "output.json"
            schema_path.write_text(json.dumps(schema, sort_keys=True), encoding="utf-8")
            cwd = Path(workspace).resolve() if workspace is not None else control_root
            cwd.mkdir(parents=True, exist_ok=True)
            command = [self.binary]
            if native_web_search:
                command.append("--search")
            command.extend(
                [
                    "exec",
                    "--ephemeral",
                    "--ignore-rules",
                    "--ignore-user-config",
                    "--skip-git-repo-check",
                    "--sandbox",
                    "read-only",
                    "--color",
                    "never",
                    "--json",
                    "--config",
                    'model_reasoning_effort="%s"' % self.reasoning_effort,
                    "--output-schema",
                    str(schema_path),
                    "--output-last-message",
                    str(output_path),
                    "-C",
                    str(cwd),
                    "--model",
                    self.model,
                    "-",
                ]
            )
            completed = self._runner(
                command,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                env=codex_subprocess_environment(),
            )
            output_bytes = None
            if output_path.is_file():
                size = output_path.stat().st_size
                if size > MAX_CODEX_OUTPUT_BYTES:
                    raise CodexInvocationError(
                        "Codex structured result exceeded the safe size limit"
                    )
                output_bytes = output_path.read_bytes()
                if len(output_bytes) > MAX_CODEX_OUTPUT_BYTES:
                    raise CodexInvocationError(
                        "Codex structured result exceeded the safe size limit"
                    )
            return completed, output_bytes


class CodexPersistentSession:
    """One private, resumable Codex thread shared by production-stage roles.

    The Workshop host remains authoritative for sequencing and gates.  This
    object owns only the native Codex conversation identity and structured
    turn transport.  ``start`` is deliberately distinct from ``resume`` so a
    missing or tampered durable checkpoint can never silently create a new
    conversation for an existing Wish.
    """

    def __init__(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        handoff_sha256: str,
        session_root: Path,
        runtime_root: Path,
        binary: Optional[str],
        timeout_seconds: int,
        runner: Any,
        cli_version: Optional[str],
        resume: bool,
    ) -> None:
        _bounded_identifier(product_id, "Codex session product_id")
        _require_sha256(wish_sha256, "Codex session Wish sha256")
        _require_sha256(handoff_sha256, "Codex session handoff sha256")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3_600:
            raise ValueError("Codex timeout_seconds must be from 1 to 3,600")
        root = _resolve_session_root(session_root)
        selected_runtime = _resolve_runtime_root(
            runtime_root, root, create=not resume
        )
        checkpoint_path = _checkpoint_path(
            selected_runtime, product_id, create=not resume
        )
        if not resume and (checkpoint_path.exists() or checkpoint_path.is_symlink()):
            raise ContractError(
                "Codex session checkpoint already exists; resume it explicitly"
            )

        self.product_id = product_id
        self.wish_sha256 = wish_sha256
        self.handoff_sha256 = handoff_sha256
        self.session_root = root
        self.runtime_root = selected_runtime
        self.checkpoint_path = checkpoint_path
        self.binary = (
            binary or os.environ.get("WORKSHOP_CODEX_BIN") or shutil.which("codex")
        )
        self.timeout_seconds = timeout_seconds
        self._runner = runner
        self.cli_version = cli_version or self._read_cli_version()
        self.runtime_config_sha256 = _runtime_config_sha256(self.cli_version)
        self._thread_id: Optional[str] = None
        self._checkpoint_sha256: Optional[str] = None
        self._lock = threading.Lock()

        if resume:
            self._load_checkpoint()

    @classmethod
    def start(
        cls,
        *,
        product_id: str,
        wish_sha256: str,
        handoff_sha256: str,
        session_root: Path,
        runtime_root: Path,
        binary: Optional[str] = None,
        timeout_seconds: int = DEFAULT_CODEX_TIMEOUT_SECONDS,
        runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
    ) -> "CodexPersistentSession":
        return cls(
            product_id=product_id,
            wish_sha256=wish_sha256,
            handoff_sha256=handoff_sha256,
            session_root=session_root,
            runtime_root=runtime_root,
            binary=binary,
            timeout_seconds=timeout_seconds,
            runner=runner,
            cli_version=cli_version,
            resume=False,
        )

    @classmethod
    def resume(
        cls,
        *,
        product_id: str,
        wish_sha256: str,
        handoff_sha256: str,
        session_root: Path,
        runtime_root: Path,
        binary: Optional[str] = None,
        timeout_seconds: int = DEFAULT_CODEX_TIMEOUT_SECONDS,
        runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
    ) -> "CodexPersistentSession":
        return cls(
            product_id=product_id,
            wish_sha256=wish_sha256,
            handoff_sha256=handoff_sha256,
            session_root=session_root,
            runtime_root=runtime_root,
            binary=binary,
            timeout_seconds=timeout_seconds,
            runner=runner,
            cli_version=cli_version,
            resume=True,
        )

    def _read_cli_version(self) -> str:
        if not self.binary:
            return "0.0.0"
        try:
            completed = self._runner(
                [self.binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                env=codex_subprocess_environment(),
            )
        except (OSError, subprocess.SubprocessError):
            return "0.0.0"
        output = completed.stdout if isinstance(completed.stdout, str) else ""
        match = re.search(r"\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9.-]+)?", output)
        return match.group(0) if match else "0.0.0"

    def _checkpoint_identity(self, thread_id: str) -> Mapping[str, Any]:
        return {
            "schema_version": 1,
            "kind": CODEX_SESSION_CHECKPOINT_KIND,
            "product_id": self.product_id,
            "wish_sha256": self.wish_sha256,
            "handoff_sha256": self.handoff_sha256,
            "thread_id": thread_id,
            "session_root_sha256": _path_sha256(self.session_root),
            "runtime_root_sha256": _path_sha256(self.runtime_root),
            "runtime_config_sha256": self.runtime_config_sha256,
            "cli_version": self.cli_version,
            "sandbox": "read-only",
        }

    def _persist_thread_id(self, thread_id: str) -> None:
        canonical = _canonical_thread_id(thread_id)
        identity = self._checkpoint_identity(canonical)
        checkpoint_sha256 = _sha256_json(identity)
        _write_private_checkpoint(
            self.checkpoint_path,
            {**identity, "checkpoint_sha256": checkpoint_sha256},
        )
        self._thread_id = canonical
        self._checkpoint_sha256 = checkpoint_sha256

    def _load_checkpoint(self) -> None:
        payload = _read_private_checkpoint(self.checkpoint_path)
        expected_fields = {
            "schema_version",
            "kind",
            "product_id",
            "wish_sha256",
            "handoff_sha256",
            "thread_id",
            "session_root_sha256",
            "runtime_root_sha256",
            "runtime_config_sha256",
            "cli_version",
            "sandbox",
            "checkpoint_sha256",
        }
        if set(payload) != expected_fields:
            raise ContractError("Codex session checkpoint fields are invalid")
        try:
            thread_id = _canonical_thread_id(payload["thread_id"])
            _require_sha256(
                payload["checkpoint_sha256"], "Codex session checkpoint sha256"
            )
        except ContractError as exc:
            raise ContractError("Codex session checkpoint binding is invalid") from exc
        identity = {key: payload[key] for key in expected_fields - {"checkpoint_sha256"}}
        expected = self._checkpoint_identity(thread_id)
        if identity != expected or payload["checkpoint_sha256"] != _sha256_json(identity):
            raise ContractError("Codex session checkpoint binding is invalid")
        self._thread_id = thread_id
        self._checkpoint_sha256 = payload["checkpoint_sha256"]

    @property
    def checkpoint_sha256(self) -> Optional[str]:
        """Return the safe checkpoint identity, never the resumable thread id."""

        return self._checkpoint_sha256

    def public_binding(self) -> Mapping[str, Any]:
        """Return a redacted status binding suitable for host receipts."""

        return {
            "schema_version": 1,
            "kind": CODEX_SESSION_CHECKPOINT_KIND,
            "product_id": self.product_id,
            "checkpoint_sha256": self._checkpoint_sha256,
            "runtime_config_sha256": self.runtime_config_sha256,
        }

    def view(
        self,
        *,
        role: str,
        model: str,
        reasoning_effort: str,
        native_web_search: bool = False,
    ) -> "CodexSessionView":
        _bounded_identifier(role, "Codex session role")
        if model not in ALLOWED_WORKSHOP_MODELS:
            raise ContractError(
                "Workshop Codex model must be gpt-5.6-terra or gpt-5.6-luna"
            )
        if reasoning_effort not in ("low", "medium", "high", "xhigh"):
            raise ValueError("unsupported Codex reasoning effort")
        if type(native_web_search) is not bool:
            raise ValueError("native_web_search must be a boolean")
        if native_web_search != (role == CODEX_RESEARCH_ROLE):
            raise ContractError(
                "Codex native web search is reserved for the Invent research role"
            )
        return CodexSessionView(
            self,
            role=role,
            model=model,
            reasoning_effort=reasoning_effort,
            native_web_search=native_web_search,
        )

    def _workspace(self, value: Optional[Path]) -> Path:
        if value is None:
            return self.session_root
        requested = Path(value)
        if not requested.is_absolute():
            raise ContractError("Codex session workspace must be absolute")
        if requested.is_symlink():
            raise ContractError("Codex session workspace must not be a symlink")
        try:
            requested.mkdir(parents=True, exist_ok=True)
            workspace = requested.resolve(strict=True)
        except OSError as exc:
            raise ContractError("Codex session workspace is unavailable") from exc
        if not workspace.is_dir() or not _within(workspace, self.session_root):
            raise ContractError("Codex session workspace must be inside its root")
        return workspace

    def _invoke(
        self,
        *,
        view: "CodexSessionView",
        prompt: str,
        schema: Mapping[str, Any],
        workspace: Optional[Path],
    ) -> Mapping[str, Any]:
        if not self.binary:
            raise CodexInvocationError("Codex CLI is not installed or on PATH")
        self._workspace(workspace)
        deadline = time.monotonic() + self.timeout_seconds
        with self._lock:
            for attempt in range(2):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CodexInvocationError("Codex structured call timed out")
                try:
                    completed, output_bytes = self._run_attempt(
                        view=view,
                        prompt=prompt,
                        schema=schema,
                        timeout_seconds=remaining,
                    )
                except subprocess.TimeoutExpired as exc:
                    exc.output = None
                    exc.stderr = None
                    raise CodexInvocationError(
                        "Codex structured call timed out"
                    ) from None
                except (OSError, subprocess.SubprocessError, TypeError, ValueError) as exc:
                    for attribute in ("output", "stdout", "stderr"):
                        if hasattr(exc, attribute):
                            setattr(exc, attribute, None)
                    raise CodexInvocationError(
                        "Codex could not execute the structured call"
                    ) from None

                stdout = completed.stdout if isinstance(completed.stdout, str) else ""
                stderr = completed.stderr if isinstance(completed.stderr, str) else ""
                observed_thread_id, used_web_search = _jsonl_session_metadata(stdout)
                if self._thread_id is None:
                    if observed_thread_id is not None:
                        self._persist_thread_id(observed_thread_id)
                    elif completed.returncode == 0:
                        raise CodexInvocationError(
                            "Codex persistent call returned no valid session identity"
                        )
                elif (
                    observed_thread_id is not None
                    and observed_thread_id != self._thread_id
                ):
                    raise CodexInvocationError(
                        "Codex resumed a different persistent session"
                    )

                if completed.returncode != 0:
                    if attempt == 0 and _is_explicit_transient_failure(stdout, stderr):
                        continue
                    if _is_explicit_transient_failure(stdout, stderr):
                        raise CodexInvocationError(
                            "Codex provider transport failed after one retry"
                        )
                    raise CodexInvocationError(
                        "Codex did not complete the structured call"
                    )

                if self._thread_id is None:  # defensive; success is handled above
                    raise CodexInvocationError(
                        "Codex persistent call returned no valid session identity"
                    )
                if view.requires_native_web_search and not used_web_search:
                    raise CodexInvocationError(
                        "Codex native web research completed without a web search event"
                    )
                payload = _decode_bounded_payload(output_bytes)
                view.last_used_web_search = used_web_search
                return payload

        raise CodexInvocationError("Codex did not complete the structured call")

    def _run_attempt(
        self,
        *,
        view: "CodexSessionView",
        prompt: str,
        schema: Mapping[str, Any],
        timeout_seconds: float,
    ):
        with tempfile.TemporaryDirectory(prefix="workshop-codex-session-") as temporary:
            control_root = Path(temporary)
            schema_path = control_root / "output.schema.json"
            output_path = control_root / "output.json"
            schema_path.write_text(json.dumps(schema, sort_keys=True), encoding="utf-8")
            command = [self.binary]
            if view.requires_native_web_search:
                command.append("--search")
            if self._thread_id is None:
                command.extend(
                    [
                        "exec",
                        "--ignore-rules",
                        "--ignore-user-config",
                        "--skip-git-repo-check",
                        "--sandbox",
                        "read-only",
                        "--color",
                        "never",
                        "--json",
                        "--config",
                        'model_reasoning_effort="%s"' % view.reasoning_effort,
                        "--output-schema",
                        str(schema_path),
                        "--output-last-message",
                        str(output_path),
                        "-C",
                        str(self.session_root),
                        "--model",
                        view.model,
                        "-",
                    ]
                )
            else:
                command.extend(
                    [
                        "exec",
                        "resume",
                        "--ignore-rules",
                        "--ignore-user-config",
                        "--skip-git-repo-check",
                        "--json",
                        "--config",
                        'model_reasoning_effort="%s"' % view.reasoning_effort,
                        "--output-schema",
                        str(schema_path),
                        "--output-last-message",
                        str(output_path),
                        "--model",
                        view.model,
                        self._thread_id,
                        "-",
                    ]
                )
            completed = self._runner(
                command,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                cwd=str(self.session_root),
                env=codex_subprocess_environment(),
            )
            output_bytes = None
            if output_path.is_file():
                size = output_path.stat().st_size
                if size > MAX_CODEX_OUTPUT_BYTES:
                    raise CodexInvocationError(
                        "Codex structured result exceeded the safe size limit"
                    )
                output_bytes = output_path.read_bytes()
                if len(output_bytes) > MAX_CODEX_OUTPUT_BYTES:
                    raise CodexInvocationError(
                        "Codex structured result exceeded the safe size limit"
                    )
            return completed, output_bytes


class CodexSessionView:
    """One stage role over a shared :class:`CodexPersistentSession`."""

    def __init__(
        self,
        session: CodexPersistentSession,
        *,
        role: str,
        model: str,
        reasoning_effort: str,
        native_web_search: bool,
    ) -> None:
        self._session = session
        self.role = role
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.requires_native_web_search = native_web_search
        self.binary = session.binary
        self.timeout_seconds = session.timeout_seconds
        self.cli_version = session.cli_version
        self.last_used_web_search = False

    def invoke(
        self,
        *,
        prompt: str,
        schema: Mapping[str, Any],
        workspace: Optional[Path] = None,
        native_web_search: bool = False,
    ) -> Mapping[str, Any]:
        if type(native_web_search) is not bool:
            raise ValueError("native_web_search must be a boolean")
        if native_web_search != self.requires_native_web_search:
            if self.requires_native_web_search:
                raise ContractError(
                    "Invent research must request Codex native web search"
                )
            raise ContractError(
                "Codex native web search is reserved for the Invent research role"
            )
        self.last_used_web_search = False
        return self._session._invoke(
            view=self,
            prompt=prompt,
            schema=schema,
            workspace=workspace,
        )


def _diagnostic_tail(value: str) -> str:
    return value[-_MAX_TRANSIENT_DIAGNOSTIC_CHARS:].casefold()


def _is_explicit_transient_failure(stdout: str, stderr: str) -> bool:
    diagnostic = _diagnostic_tail(stdout) + "\n" + _diagnostic_tail(stderr)
    return any(marker in diagnostic for marker in _TRANSIENT_DIAGNOSTIC_MARKERS)


def _jsonl_used_web_search(stdout: str) -> bool:
    if len(stdout.encode("utf-8", errors="replace")) > MAX_CODEX_EVENT_BYTES:
        raise CodexInvocationError("Codex event stream exceeded the safe size limit")
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except (TypeError, ValueError):
            continue
        if (
            isinstance(event, Mapping)
            and event.get("type") in ("item.started", "item.updated", "item.completed")
            and isinstance(event.get("item"), Mapping)
            and event["item"].get("type") == "web_search"
        ):
            return True
    return False


def _jsonl_session_metadata(stdout: str) -> tuple[Optional[str], bool]:
    if len(stdout.encode("utf-8", errors="replace")) > MAX_CODEX_EVENT_BYTES:
        raise CodexInvocationError("Codex event stream exceeded the safe size limit")
    thread_ids = []
    used_web_search = False
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except (TypeError, ValueError):
            continue
        if not isinstance(event, Mapping):
            continue
        if event.get("type") == "thread.started":
            try:
                thread_ids.append(_canonical_thread_id(event.get("thread_id")))
            except ContractError as exc:
                raise CodexInvocationError(
                    "Codex returned an invalid persistent session identity"
                ) from exc
        if (
            event.get("type") in ("item.started", "item.updated", "item.completed")
            and isinstance(event.get("item"), Mapping)
            and event["item"].get("type") == "web_search"
        ):
            used_web_search = True
    if len(thread_ids) > 1 or len(set(thread_ids)) > 1:
        raise CodexInvocationError(
            "Codex returned an ambiguous persistent session identity"
        )
    return (thread_ids[0] if thread_ids else None), used_web_search


def _decode_bounded_payload(encoded: Optional[bytes]) -> Mapping[str, Any]:
    if encoded is None:
        raise CodexInvocationError("Codex returned no structured result")
    try:
        if len(encoded) > MAX_CODEX_OUTPUT_BYTES:
            raise CodexInvocationError(
                "Codex structured result exceeded the safe size limit"
            )
        payload = json.loads(encoded.decode("utf-8"))
    except CodexInvocationError:
        raise
    except (OSError, UnicodeError, ValueError):
        raise CodexInvocationError("Codex returned no valid structured result") from None
    if not isinstance(payload, dict):
        raise CodexInvocationError("Codex structured result must be an object")
    return payload


__all__ = [
    "ALLOWED_WORKSHOP_MODELS",
    "CODEX_RESEARCH_ROLE",
    "CODEX_SESSION_CHECKPOINT_KIND",
    "DEFAULT_CODEX_TIMEOUT_SECONDS",
    "MAX_CODEX_EVENT_BYTES",
    "MAX_CODEX_OUTPUT_BYTES",
    "MAX_CODEX_SESSION_CHECKPOINT_BYTES",
    "CodexInvocationError",
    "CodexPersistentSession",
    "CodexSessionView",
    "CodexStructuredRunner",
]
