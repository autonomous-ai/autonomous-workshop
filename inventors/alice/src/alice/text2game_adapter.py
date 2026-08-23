"""Pinned, crash-reconcilable text2game CAD adapter for Alice.

The upstream repository is useful as an invention/CAD worker, but it writes to
``HERE/out`` and its phases are not globally idempotent.  Alice therefore never
runs it in the shared checkout.  One immutable copy of the exact tracked Git
tree is created per engine operation, reviewed rules/components are staged
before the first call, and every phase crosses a durable ``sending`` fence.

This module never invokes either text2game publisher, never changes Vibe's
``QUEUE.json``, and never performs a public Factory write.  Its only handoff is
the deterministic :mod:`alice.text2game_export` workspace consumed by the
existing private-draft PageBuilder adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import tempfile
import time
from typing import Any, Callable, Mapping, Sequence

from .adapters import AdapterError, AdapterReceipt, adapter_input_sha256
from .cad_validation import (
    KernelBodyObservation,
    MotionCondition,
    PrinterCalibrationProfile,
    PrinterTarget,
    derive_assembled_fit,
    derive_print_in_place_fit,
    evaluate_motion_condition,
    inspect_stl_topology,
    self_check_calibration_profile,
    validate_profile_binding,
)
from .providers import (
    BoundedProcessOutputLimit,
    BoundedProcessSpawnError,
    BoundedProcessTimeout,
    run_bounded_process,
)
from .store import DurableStore, StateConflictError, VersionedStateRecord
from .text2game_export import (
    TEXT2GAME_REPOSITORY,
    Text2GameExportRequest,
    canonical_sha256,
    export_text2game_to_vibe,
)


DIAGNOSTICS_CONTRACT_VERSION = "alice.adapter-diagnostics.v1"
STATE_SCHEMA_VERSION = 1
CAD_RECEIPT_VERSION = "alice.text2game-cad.v1"
DFM_RECEIPT_VERSION = "alice.text2game-dfm.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FORBIDDEN_ENVIRONMENT_PREFIXES = (
    "ADMIN_",
    "ALICE_FACTORY_",
    "GCS_",
    "MONGO",
    "PANDA_",
    "TELEGRAM_",
)
_FORBIDDEN_ENVIRONMENT_NAMES = frozenset(
    {"GOOGLE_APPLICATION_CREDENTIALS", "PANDA_SECRETS_ENV"}
)
_FORBIDDEN_SOURCE_NAMES = frozenset(
    {".env", "auth.json", "credentials.json", "gcs-sa.json", "secrets.json"}
)
_UNSAFE_PROCESS_ENVIRONMENT = frozenset(
    {
        "BASH_ENV",
        "ENV",
        "LD_PRELOAD",
        "PYTHONBREAKPOINT",
        "PYTHONHOME",
        "PYTHONINSPECT",
        "PYTHONPATH",
        "PYTHONSTARTUP",
    }
)
_TEXT2GAME_RUNTIME_FILES = frozenset(
    {
        "catalog.json",
        "consistency.py",
        "discover.py",
        "fit.py",
        "harness.py",
        "harvest.py",
        "mechanisms.md",
        "phase2.py",
        "phase3.py",
        "plates.py",
        "profiles/petg.ini",
        "prompts.py",
        "render_assembly.py",
        "scaffold.py",
        "slice_parts.py",
        "stage.py",
        "storyboard.py",
        "taste_boardgame.md",
        "text2game",
        "trace_log.py",
        "trends.py",
    }
)
_TEXT2GAME_RUNTIME_PREFIXES = ("priorart/",)
_TEXT2CAD_RUNTIME_FILES = frozenset({"gate.py"})
_TEXT2CAD_RUNTIME_PREFIXES = ("skills/cadcode/",)
_HARDENED_HARNESS_CONTRACT = "alice-text2game-out-dir-only-v1"
_PINNED_CAD_SHIM_CONTRACT = "alice-pinned-cad-python-shim-v1"
_MAX_TRACKED_FILES = 20_000
_MAX_TRACKED_BYTES = 2 << 30
_MAX_OUTPUT_FILES = 20_000
_MAX_OUTPUT_BYTES = 20 << 30
_RULE_FIELDS = (
    "setup",
    "turn",
    "legal_actions",
    "end",
    "scoring",
    "ties",
    "rules_markdown",
)
_PAGE_LINEAGE_FIELDS = (
    "slug",
    "production_slug",
    "candidate_id",
    "candidate_version",
    "candidate_content_sha256",
    "rules_sha256",
    "rules_file_sha256",
    "vibe_idea_sha256",
    "project_sha256",
    "artifact_hashes",
    "text2game_source_artifact_hashes",
    "text2game_source_artifact_hashes_sha256",
    "text2game_export_receipt_sha256",
    "text2game_source_snapshot_sha256",
    "text2game_repo_url",
    "text2game_repo_commit",
)


class Text2GameAdapterError(AdapterError):
    """A deterministic preflight/configuration failure that may be retried."""


class AmbiguousText2GameEffect(AdapterError):
    """A phase may have changed its workspace and must reconcile before retry."""


@dataclass(frozen=True, slots=True)
class _RepoSnapshot:
    files: tuple[tuple[str, str, int], ...]
    manifest_sha256: str
    total_bytes: int


@dataclass(frozen=True, slots=True)
class _FilePin:
    target: Path
    sha256: str | None


@dataclass(frozen=True, slots=True)
class _Operation:
    operation_id: str
    key: str
    directory: Path
    repository: Path
    source: Path
    identity: Mapping[str, Any]
    design: Mapping[str, Any]
    rules: Mapping[str, Any]


class Text2GamePhysicalAdapter:
    """Run verified text2game phases and export one exact private-draft input."""

    name = "cad"
    capabilities = (
        "alice_text2game_locked_rules",
        "artifact_hash_readback",
        "idempotent_cad_by_operation_key",
        "peter_fail_closed_validation",
        "reconcile_cad_by_operation_key",
    )

    def __init__(
        self,
        text2game_repo: str | Path,
        text2game_commit: str,
        work_root: str | Path,
        vibe_workspace: str | Path,
        command: Sequence[str],
        calibration_profile: PrinterCalibrationProfile | Mapping[str, Any],
        printer_target: PrinterTarget | Mapping[str, Any],
        store: DurableStore,
        *,
        text2cad_repo: str | Path,
        text2cad_commit: str,
        cad_python: str | Path,
        slicer_binary: str | Path,
        slicer_profile: str | Path,
        codex_binary: str | Path,
        codex_home: str | Path,
        git_binary: str | Path,
        timeout_seconds: float = 7_200,
        max_output_bytes: int = 262_144,
        max_stderr_bytes: int = 262_144,
        shutdown_grace_seconds: float = 10,
        environment: Mapping[str, str] | None = None,
        kernel_evaluator: Callable[[bytes, Mapping[str, Any]], Any] | None = None,
        motion_evaluator: Callable[[MotionCondition], Any] | None = None,
    ) -> None:
        self.text2game_repo = _absolute_path(text2game_repo, "text2game_repo")
        self.work_root = _absolute_path(work_root, "work_root")
        self.vibe_workspace = _absolute_path(vibe_workspace, "vibe_workspace")
        if not isinstance(text2game_commit, str) or _COMMIT.fullmatch(text2game_commit) is None:
            raise ValueError("text2game_commit must be a lowercase 40-hex commit")
        self.text2game_commit = text2game_commit
        self.text2cad_repo = _absolute_path(text2cad_repo, "text2cad_repo")
        if not isinstance(text2cad_commit, str) or _COMMIT.fullmatch(text2cad_commit) is None:
            raise ValueError("text2cad_commit must be a lowercase 40-hex commit")
        self.text2cad_commit = text2cad_commit
        self.cad_python = _absolute_path(cad_python, "cad_python")
        self.slicer_binary = _absolute_path(slicer_binary, "slicer_binary")
        self.slicer_profile = _absolute_path(slicer_profile, "slicer_profile")
        self.codex_binary = _absolute_path(codex_binary, "codex_binary")
        self.codex_home = _absolute_path(codex_home, "codex_home")
        self.git_binary = _absolute_path(git_binary, "git_binary")
        if (
            not isinstance(command, Sequence)
            or isinstance(command, (str, bytes))
            or len(command) != 1
            or not isinstance(command[0], str)
        ):
            raise ValueError("command must contain exactly one absolute interpreter path")
        interpreter = Path(command[0])
        if not interpreter.is_absolute():
            raise ValueError("text2game interpreter must be absolute")
        self.command = (str(interpreter),)
        self._interpreter_target = interpreter.resolve(strict=False)
        if not self._interpreter_target.is_file():
            raise ValueError("text2game interpreter target must be a regular file")
        self._interpreter_sha256 = _sha256_file(self._interpreter_target)
        self._tool_pins = {
            "cad_python": _initial_file_pin(self.cad_python),
            "slicer_binary": _initial_file_pin(self.slicer_binary),
            "slicer_profile": _initial_file_pin(self.slicer_profile),
            "codex_binary": _initial_file_pin(self.codex_binary),
            "git_binary": _initial_file_pin(self.git_binary),
        }
        self.toolchain_sha256 = canonical_sha256(
            {
                "text2game_commit": self.text2game_commit,
                "text2cad_commit": self.text2cad_commit,
                "text2game_interpreter_sha256": self._interpreter_sha256,
                "pinned_file_sha256": {
                    name: pin.sha256 for name, pin in sorted(self._tool_pins.items())
                },
                "codex_sandbox": "workspace-write",
                "codex_fallback": False,
                "hardened_harness_contract": _HARDENED_HARNESS_CONTRACT,
                "cad_execution_contract": _PINNED_CAD_SHIM_CONTRACT,
            }
        )
        self.profile = (
            calibration_profile
            if isinstance(calibration_profile, PrinterCalibrationProfile)
            else PrinterCalibrationProfile.from_mapping(calibration_profile)
        )
        self.target = (
            printer_target
            if isinstance(printer_target, PrinterTarget)
            else PrinterTarget.from_mapping(printer_target)
        )
        self.store = store
        self.timeout_seconds = _positive_number(timeout_seconds, "timeout_seconds")
        self.max_output_bytes = _positive_integer(max_output_bytes, "max_output_bytes")
        self.max_stderr_bytes = _positive_integer(max_stderr_bytes, "max_stderr_bytes")
        self.shutdown_grace_seconds = _positive_number(
            shutdown_grace_seconds, "shutdown_grace_seconds"
        )
        raw_environment = dict(environment or {})
        for key, value in raw_environment.items():
            if not isinstance(key, str) or not key or not isinstance(value, str):
                raise ValueError("environment must contain string names and values")
            if key in _FORBIDDEN_ENVIRONMENT_NAMES or key.startswith(
                _FORBIDDEN_ENVIRONMENT_PREFIXES
            ):
                raise ValueError(f"publishing/messaging environment is forbidden: {key}")
            if (
                key in _UNSAFE_PROCESS_ENVIRONMENT
                or key.startswith("DYLD_")
                or key.startswith("GIT_")
            ):
                raise ValueError(f"process-injection environment is forbidden: {key}")
        raw_environment["STOP_AT_CHECKPOINT"] = "1"
        raw_environment["COHERENCE_BLOCKS"] = "1"
        # text2game's Claude lane grants Bash against the host.  Alice only
        # permits the Codex lane and forces its own workspace sandbox so model
        # commands work in the per-operation copy rather than the source
        # checkout.  Codex still receives its dedicated CODEX_HOME for auth;
        # this is a process boundary, not a claim that credentials are hidden
        # from the model runtime.  The optional shared vault is disabled in
        # both directions; learning enters Alice through reviewed evidence.
        raw_environment["CODEX_JOBS"] = "all"
        raw_environment["CODEX_SANDBOX"] = "workspace-write"
        raw_environment["CODEX_FALLBACK"] = "0"
        raw_environment["CODEX_BIN"] = str(self.codex_binary)
        raw_environment["CODEX_HOME"] = str(self.codex_home)
        raw_environment["TEXT2CAD_DIR"] = str(self.text2cad_repo)
        raw_environment["TEXT2CAD_PY"] = str(self.cad_python)
        raw_environment["RENDER_PY"] = str(self.cad_python)
        raw_environment["SLICER_BIN"] = str(self.slicer_binary)
        raw_environment["SLICER_PROFILE"] = str(self.slicer_profile)
        raw_environment.pop("MEASURE_CMD", None)
        raw_environment.pop("NO_SLICE", None)
        raw_environment.pop("ORCASLICER_CLI", None)
        raw_environment["CRITIC_VAULT"] = "off"
        raw_environment["VAULT_INGEST"] = "off"
        raw_environment["CONCEPT_VIDEO"] = "off"
        raw_environment["PYTHONDONTWRITEBYTECODE"] = "1"
        self.environment = raw_environment
        self.kernel_evaluator = kernel_evaluator
        self.motion_evaluator = motion_evaluator

    def diagnostics(self) -> dict[str, Any]:
        """Read-only, versioned readiness proof for ``alice doctor``."""

        failures: list[str] = []
        repo_sha256: str | None = None
        try:
            repo_sha256 = self._text2game_snapshot().manifest_sha256
        except Exception as exc:
            failures.append(f"source:{type(exc).__name__}")
        failures.extend(self._toolchain_failures(include_text2game_source=False))
        binding = validate_profile_binding(self.profile, self.target)
        profile_check = self_check_calibration_profile(self.profile)
        if binding.status != "passed":
            failures.append("calibration_binding")
        if profile_check.status != "passed":
            failures.append("calibration_self_check")
        if (
            self.vibe_workspace.is_symlink()
            or not (self.vibe_workspace / "board-game" / "ideas").is_dir()
            or not (self.vibe_workspace / "board-game" / "QUEUE.json").is_file()
            or not (self.vibe_workspace / "board-game" / "tools" / "publish.py").is_file()
        ):
            failures.append("vibe_workspace")
        if not _directory_ready_without_writing(self.work_root):
            failures.append("work_root")
        authenticated = self._authentication_ready()
        if not authenticated:
            failures.append("model_authentication")
        ready = not failures
        return {
            "adapter": self.name,
            "ready": ready,
            "authenticated": authenticated,
            "contract_version": DIAGNOSTICS_CONTRACT_VERSION,
            "capabilities": sorted(self.capabilities) if ready else [],
            "text2game_commit": self.text2game_commit,
            "text2cad_commit": self.text2cad_commit,
            "toolchain_sha256": self.toolchain_sha256,
            "source_manifest_sha256": repo_sha256,
            "calibration_profile_sha256": self.profile.profile_sha256,
            "printer_target_sha256": self.target.target_sha256,
            "failures": sorted(failures),
        }

    def invoke(self, operation: str, payload: dict[str, Any]) -> AdapterReceipt:
        started = time.monotonic()
        input_sha256 = adapter_input_sha256(operation, payload)
        if operation in {"physical.cad", "physical.reconcile_cad"}:
            result = self._cad(operation, payload, input_sha256)
            run_id = str(result["text2game_operation_id"])
        elif operation == "physical.dfm":
            result = self._dfm(payload)
            run_id = str(result["text2game_operation_id"])
        else:
            raise Text2GameAdapterError(f"unsupported text2game operation {operation!r}")
        return AdapterReceipt(
            adapter=self.name,
            run_id=run_id,
            status="passed",
            evidence_class="manufacturing",
            payload=result,
            input_sha256=input_sha256,
            elapsed_seconds=time.monotonic() - started,
        )

    def _authentication_ready(self) -> bool:
        if not _file_pin_ready(
            self.codex_binary, self._tool_pins["codex_binary"], executable=True
        ) or not _secure_codex_home(self.codex_home):
            return False
        try:
            result = run_bounded_process(
                (str(self.codex_binary), "login", "status"),
                input_bytes=b"",
                timeout_seconds=min(30.0, self.timeout_seconds),
                stdout_limit_bytes=65_536,
                stderr_limit_bytes=65_536,
                shutdown_grace_seconds=self.shutdown_grace_seconds,
                env=self.environment,
            )
            if result.returncode != 0:
                return False
            help_result = run_bounded_process(
                (str(self.codex_binary), "exec", "--help"),
                input_bytes=b"",
                timeout_seconds=min(30.0, self.timeout_seconds),
                stdout_limit_bytes=131_072,
                stderr_limit_bytes=65_536,
                shutdown_grace_seconds=self.shutdown_grace_seconds,
                env=self.environment,
            )
        except Exception:
            return False
        return bool(
            help_result.returncode == 0
            and all(
                flag in help_result.stdout
                for flag in (
                    b"--ephemeral",
                    b"--ignore-user-config",
                    b"--ignore-rules",
                    b"--strict-config",
                )
            )
        )

    def _toolchain_failures(self, *, include_text2game_source: bool = True) -> list[str]:
        failures: list[str] = []
        if include_text2game_source:
            try:
                self._text2game_snapshot()
            except Exception as exc:
                failures.append(f"source:{type(exc).__name__}")
        try:
            self._text2cad_snapshot()
        except Exception as exc:
            failures.append(f"text2cad_source:{type(exc).__name__}")

        for relative in (
            "text2game",
            "phase2.py",
            "phase3.py",
            "consistency.py",
            "mechanisms.md",
            "slice_parts.py",
            "profiles/petg.ini",
        ):
            if not _plain_required_file(self.text2game_repo / relative):
                failures.append(f"text2game_file:{relative}")
        for relative in (
            "gate.py",
            "skills/cadcode/SKILL.md",
            "skills/cadcode/scripts/measure/cli.py",
            "skills/cadcode/scripts/cad/cli.py",
        ):
            if not _plain_required_file(self.text2cad_repo / relative):
                failures.append(f"text2cad_file:{relative}")

        pinned_paths = (
            ("cad_python", self.cad_python, True),
            ("slicer_binary", self.slicer_binary, True),
            ("slicer_profile", self.slicer_profile, False),
            ("codex_binary", self.codex_binary, True),
            ("git_binary", self.git_binary, True),
        )
        for name, path, executable in pinned_paths:
            if not _file_pin_ready(
                path, self._tool_pins[name], executable=executable
            ):
                failures.append(f"pinned_file:{name}")

        try:
            self._verify_interpreter()
        except Exception as exc:
            failures.append(f"interpreter:{type(exc).__name__}")
        if not self._probe_python_imports(
            self.command[0], ("PIL", "cadquery", "trimesh", "numpy", "matplotlib")
        ):
            failures.append("text2game_python_imports")
        if not self._probe_python_imports(
            str(self.cad_python),
            ("cadquery", "trimesh", "numpy", "matplotlib"),
        ):
            failures.append("cad_python_imports")
        if not self._probe_tool((str(self.slicer_binary), "--version")):
            failures.append("slicer_probe")
        if not self._probe_tool((str(self.git_binary), "--version")):
            failures.append("git_probe")
        if not self._authentication_ready():
            failures.append("model_authentication")
        return sorted(set(failures))

    def _probe_python_imports(
        self, executable: str, modules: Sequence[str]
    ) -> bool:
        script = (
            "import importlib.util,sys;"
            "sys.exit(0 if all(importlib.util.find_spec(x) for x in sys.argv[1:]) else 9)"
        )
        return self._probe_tool((executable, "-I", "-c", script, *modules))

    def _probe_tool(self, command: Sequence[str]) -> bool:
        safe_environment = {
            name: value
            for name, value in self.environment.items()
            if name
            in {
                "PATH",
                "HOME",
                "LANG",
                "LC_ALL",
                "TMPDIR",
                "CODEX_HOME",
                "CODEX_BIN",
            }
        }
        try:
            result = run_bounded_process(
                tuple(command),
                input_bytes=b"",
                timeout_seconds=min(60.0, self.timeout_seconds),
                stdout_limit_bytes=65_536,
                stderr_limit_bytes=65_536,
                shutdown_grace_seconds=self.shutdown_grace_seconds,
                env=safe_environment,
            )
        except Exception:
            return False
        return result.returncode == 0

    def _verify_interpreter(self) -> None:
        configured = Path(self.command[0])
        if not configured.exists() or not os.access(configured, os.X_OK):
            raise Text2GameAdapterError("text2game interpreter is unavailable")
        target = configured.resolve(strict=True)
        if target != self._interpreter_target:
            raise Text2GameAdapterError("text2game interpreter target changed")
        metadata = target.stat()
        if not stat.S_ISREG(metadata.st_mode):
            raise Text2GameAdapterError("text2game interpreter target is not regular")
        if _sha256_file(target) != self._interpreter_sha256:
            raise Text2GameAdapterError("text2game interpreter bytes changed")

    def _git(
        self,
        *arguments: str,
        stdout_limit: int = 4 << 20,
        repository: Path | None = None,
    ) -> bytes:
        pin = self._tool_pins["git_binary"]
        if not _file_pin_ready(self.git_binary, pin, executable=True):
            raise Text2GameAdapterError("pinned git executable changed")
        git = str(pin.target)
        try:
            git_environment = dict(self.environment)
            git_environment.update(
                {
                    "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_SYSTEM": os.devnull,
                    "GIT_NO_REPLACE_OBJECTS": "1",
                    "GIT_OPTIONAL_LOCKS": "0",
                }
            )
            result = run_bounded_process(
                (
                    git,
                    "--no-replace-objects",
                    "-C",
                    str(repository or self.text2game_repo),
                    *arguments,
                ),
                input_bytes=b"",
                timeout_seconds=min(60.0, self.timeout_seconds),
                stdout_limit_bytes=stdout_limit,
                stderr_limit_bytes=65_536,
                shutdown_grace_seconds=self.shutdown_grace_seconds,
                env=git_environment,
            )
        except (BoundedProcessTimeout, BoundedProcessOutputLimit, OSError) as exc:
            raise Text2GameAdapterError(
                f"text2game source inspection failed ({type(exc).__name__})"
            ) from exc
        if result.returncode != 0:
            raise Text2GameAdapterError(
                "text2game source inspection failed; "
                f"stderr_sha256={result.stderr_sha256}"
            )
        return result.stdout

    def _text2game_snapshot(self) -> _RepoSnapshot:
        return self._repo_snapshot(
            include_files=_TEXT2GAME_RUNTIME_FILES,
            include_prefixes=_TEXT2GAME_RUNTIME_PREFIXES,
        )

    def _text2cad_snapshot(self) -> _RepoSnapshot:
        return self._repo_snapshot(
            self.text2cad_repo,
            self.text2cad_commit,
            label="text2cad",
            include_files=_TEXT2CAD_RUNTIME_FILES,
            include_prefixes=_TEXT2CAD_RUNTIME_PREFIXES,
        )

    def _repo_snapshot(
        self,
        repository: Path | None = None,
        commit: str | None = None,
        *,
        label: str = "text2game",
        include_files: frozenset[str] | None = None,
        include_prefixes: tuple[str, ...] = (),
    ) -> _RepoSnapshot:
        repository = repository or self.text2game_repo
        commit = commit or self.text2game_commit
        if repository.is_symlink() or not repository.is_dir():
            raise Text2GameAdapterError(
                f"{label}_repo must be a non-symlink directory"
            )
        head = self._git("rev-parse", "HEAD", repository=repository).decode(
            "ascii", errors="strict"
        ).strip()
        if head != commit:
            raise Text2GameAdapterError(
                f"{label} checkout is not at the pinned commit"
            )
        status = self._git(
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            repository=repository,
        )
        if status:
            raise Text2GameAdapterError(f"{label} checkout must be clean")
        encoded_tree = self._git(
            "ls-tree",
            "-r",
            "-z",
            "--full-tree",
            commit,
            stdout_limit=32 << 20,
            repository=repository,
        )
        raw_entries = encoded_tree.split(b"\0")
        if raw_entries and raw_entries[-1] == b"":
            raw_entries.pop()
        if not raw_entries or len(raw_entries) > _MAX_TRACKED_FILES:
            raise Text2GameAdapterError("text2game tracked-file count is invalid")
        files: list[tuple[str, str, int]] = []
        total = 0
        object_format: str | None = None
        for raw in raw_entries:
            try:
                metadata_raw, path_raw = raw.split(b"\t", 1)
                mode_raw, kind_raw, oid_raw = metadata_raw.split(b" ", 2)
                mode = mode_raw.decode("ascii")
                kind = kind_raw.decode("ascii")
                oid = oid_raw.decode("ascii")
            except (ValueError, UnicodeDecodeError) as exc:
                raise Text2GameAdapterError("pinned text2game tree is malformed") from exc
            if mode not in {"100644", "100755"} or kind != "blob":
                raise Text2GameAdapterError(
                    "pinned text2game tree may contain only regular files"
                )
            this_format = "sha1" if len(oid) == 40 else "sha256" if len(oid) == 64 else ""
            if not this_format or (object_format is not None and this_format != object_format):
                raise Text2GameAdapterError("pinned text2game object ids are malformed")
            object_format = this_format
            try:
                relative = path_raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise Text2GameAdapterError("tracked paths must be UTF-8") from exc
            if include_files is not None and (
                relative not in include_files
                and not any(relative.startswith(prefix) for prefix in include_prefixes)
            ):
                continue
            path = _contained_relative_file(repository, relative)
            if _credential_like_path(relative):
                raise Text2GameAdapterError(
                    f"credential-like file is tracked in {label}: {relative}"
                )
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode):
                raise Text2GameAdapterError(
                    f"tracked {label} source must be regular: {relative}"
                )
            executable = bool(metadata.st_mode & 0o111)
            if executable != (mode == "100755"):
                raise Text2GameAdapterError(
                    f"tracked {label} mode differs from pinned commit: {relative}"
                )
            size = int(metadata.st_size)
            total += size
            if total > _MAX_TRACKED_BYTES:
                raise Text2GameAdapterError("text2game tracked source exceeds byte limit")
            digest, blob_oid = _file_hashes(path, object_format)
            if blob_oid != oid:
                raise Text2GameAdapterError(
                    f"{label} source differs from pinned commit: {relative}"
                )
            files.append((relative, digest, size))
        files.sort()
        selected_paths = {path for path, _, _ in files}
        if include_files is not None:
            missing = sorted(include_files - selected_paths)
            empty_prefixes = sorted(
                prefix
                for prefix in include_prefixes
                if not any(path.startswith(prefix) for path in selected_paths)
            )
            if missing or empty_prefixes:
                raise Text2GameAdapterError(
                    f"pinned {label} runtime allowlist is incomplete"
                )
        if not files:
            raise Text2GameAdapterError(f"pinned {label} runtime is empty")
        manifest = canonical_sha256(
            [{"path": path, "sha256": digest, "bytes": size} for path, digest, size in files]
        )
        return _RepoSnapshot(tuple(files), manifest, total)

    def _copy_repo(
        self, destination: Path, snapshot: _RepoSnapshot
    ) -> dict[str, str]:
        destination.mkdir(mode=0o700)
        for relative, expected, _ in snapshot.files:
            source = _contained_relative_file(self.text2game_repo, relative)
            target = destination / PurePosixPath(relative)
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            before = source.lstat()
            data = source.read_bytes()
            after = source.lstat()
            if (
                (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
                or hashlib.sha256(data).hexdigest() != expected
            ):
                raise Text2GameAdapterError("text2game source changed while copying")
            target.write_bytes(data)
            target.chmod(0o500 if before.st_mode & 0o111 else 0o400)
        after = self._text2game_snapshot()
        if after != snapshot:
            raise Text2GameAdapterError("text2game source changed during snapshot")
        entrypoint = destination / "text2game"
        if not entrypoint.is_file() or entrypoint.is_symlink():
            raise Text2GameAdapterError("pinned text2game entrypoint is missing")
        _harden_operation_harness(destination / "harness.py")
        return _snapshot_regular_tree(destination)

    def _write_operation_shims(
        self, temporary: Path, final_directory: Path
    ) -> dict[str, str]:
        bin_dir = temporary / "home" / ".local" / "bin"
        bin_dir.mkdir(parents=True, mode=0o700)
        cad_python = shlex.quote(str(self.cad_python))
        final_text2cad = final_directory / "toolchain" / "text2cad"
        measure = shlex.quote(
            str(final_text2cad / "skills" / "cadcode" / "scripts" / "measure")
        )
        uv_shim = (
            "#!/bin/sh\n"
            "set -eu\n"
            "[ \"$#\" -ge 7 ] || exit 64\n"
            "[ \"$1\" = run ] || exit 64\nshift\n"
            "[ \"$1\" = --python ] && [ \"$2\" = 3.12 ] || exit 64\nshift 2\n"
            "[ \"$1\" = --with ] && [ \"$2\" = cadquery ] || exit 64\nshift 2\n"
            "[ \"$1\" = python3 ] || exit 64\nshift\n"
            f"exec {cad_python} \"$@\"\n"
        ).encode("utf-8")
        measure_shim = (
            "#!/bin/sh\n"
            "set -eu\n"
            f"exec {cad_python} {measure} \"$@\"\n"
        ).encode("utf-8")
        python_shim = (
            "#!/bin/sh\n"
            "set -eu\n"
            f"exec {cad_python} \"$@\"\n"
        ).encode("utf-8")
        documents = {
            "uv": uv_shim,
            "alice-measure": measure_shim,
            "python": python_shim,
            "python3": python_shim,
        }
        hashes: dict[str, str] = {}
        for name, document in documents.items():
            target = bin_dir / name
            _write_bytes(target, document)
            target.chmod(0o500)
            hashes[name] = hashlib.sha256(document).hexdigest()
        return hashes

    def _cad(
        self, operation: str, payload: Mapping[str, Any], input_sha256: str
    ) -> dict[str, Any]:
        reconcile_only = operation == "physical.reconcile_cad"
        effect_key = _required_string(
            payload.get("effect_operation_key"), "effect_operation_key"
        )
        operation_id = hashlib.sha256(effect_key.encode("utf-8")).hexdigest()[:32]
        design = _dependency_content(payload, "physical.design")
        rules = _accepted_content(payload, "candidate.rules")
        identity = self._operation_identity(
            operation_id, effect_key, payload, design, rules
        )
        operation_state = self._prepare_operation(
            operation_id, identity, design, rules, reconcile_only=reconcile_only
        )
        result = self._advance_operation(operation_state, reconcile_only=reconcile_only)
        return dict(result)

    def _dfm(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        cad = _dependency_content(payload, "physical.cad")
        design = _dependency_content(payload, "physical.design")
        operation_id = _required_string(
            cad.get("text2game_operation_id"), "physical.cad text2game_operation_id"
        )
        if re.fullmatch(r"[0-9a-f]{32}", operation_id) is None:
            raise Text2GameAdapterError("physical.cad operation id is malformed")
        key = f"alice.text2game:v1:{operation_id}"
        state = self.store.get_state(key)
        if state is None:
            raise Text2GameAdapterError("text2game CAD operation state is missing")
        value = _state_value(state)
        if value.get("status") != "confirmed" or not isinstance(value.get("result"), Mapping):
            raise AmbiguousText2GameEffect("text2game CAD operation is not confirmed")
        result = dict(value["result"])
        for field in _PAGE_LINEAGE_FIELDS:
            if cad.get(field) != result.get(field):
                raise Text2GameAdapterError(f"physical.cad {field} no longer matches")
        expected_design_sha = canonical_sha256(design)
        if result.get("physical_design_sha256") != expected_design_sha:
            raise Text2GameAdapterError("physical.design changed before DFM")
        source_dir = Path(_required_string(value.get("source_dir"), "source_dir"))
        source_hashes = _snapshot_output(source_dir)
        if source_hashes != result.get("text2game_source_artifact_hashes"):
            raise Text2GameAdapterError("text2game output changed after CAD acceptance")
        validation = self._validate_physical_design(design, source_dir)
        if validation["hashes"] != result.get("validation_receipt_hashes"):
            raise Text2GameAdapterError("DFM validation receipts changed")
        export = self._export(value, design, source_hashes)
        lineage = export.page_builder_lineage()
        if any(lineage.get(field) != result.get(field) for field in _PAGE_LINEAGE_FIELDS):
            raise Text2GameAdapterError("DFM export lineage changed")
        slice_report = _load_mapping(source_dir / "slice_report.json", "slice_report.json")
        parts = slice_report.get("parts")
        failed = slice_report.get("failed")
        total_parts = len(parts) if isinstance(parts, list) else 0
        failed_count = len(failed) if isinstance(failed, list) else total_parts
        print_yield = 0.0 if total_parts == 0 else (total_parts - failed_count) / total_parts
        output = dict(result)
        output.update(
            {
                "fit": True,
                "tolerances": validation["receipts"],
                "print_yield": print_yield,
                "landed_cost": {
                    "basis": "slice_report_only",
                    "currency": None,
                    "total_grams": slice_report.get("total_grams"),
                    "total_seconds": slice_report.get("total_seconds"),
                    "priced": False,
                },
                "receipt": {
                    "schema_version": DFM_RECEIPT_VERSION,
                    "status": "passed",
                    "operation_id": operation_id,
                    "source_snapshot_sha256": export.source_snapshot_sha256,
                    "validation_receipt_hashes": validation["hashes"],
                    "limitations": [
                        "slice success is not a physical production-yield measurement",
                        "cost remains unpriced until the real prototype/production adapters run",
                    ],
                },
            }
        )
        return output

    def _operation_identity(
        self,
        operation_id: str,
        effect_key: str,
        payload: Mapping[str, Any],
        design: Mapping[str, Any],
        rules: Mapping[str, Any],
    ) -> dict[str, Any]:
        candidate_id = _required_string(payload.get("candidate_id"), "candidate_id")
        candidate_version = _positive_integer(payload.get("candidate_version"), "candidate_version")
        candidate_hash = _required_sha256(
            payload.get("candidate_content_sha256"), "candidate_content_sha256"
        )
        for field, expected in (
            ("candidate_id", candidate_id),
            ("candidate_version", candidate_version),
            ("candidate_content_sha256", candidate_hash),
        ):
            if design.get(field) != expected:
                raise Text2GameAdapterError(f"physical.design {field} mismatch")
        rule_document = {field: rules.get(field) for field in _RULE_FIELDS}
        rules_sha256 = canonical_sha256(rule_document)
        if rules.get("rules_sha256") != rules_sha256 or design.get("rules_sha256") != rules_sha256:
            raise Text2GameAdapterError("physical.design does not bind accepted rules")
        slug = _required_string(design.get("production_slug"), "production_slug")
        if _SLUG.fullmatch(slug) is None or not slug.endswith("-" + candidate_hash[:12]):
            raise Text2GameAdapterError("production_slug is not candidate-version unique")
        if any(
            isinstance(item, Mapping) and item.get("blocks_dfm") is True
            for item in design.get("open_items", [])
        ):
            raise Text2GameAdapterError("physical.design has a DFM-blocking open item")
        original_input = payload.get("task_input_sha256")
        original_input = _required_sha256(original_input, "task_input_sha256")
        return {
            "schema_version": STATE_SCHEMA_VERSION,
            "operation_id": operation_id,
            "effect_operation_key": effect_key,
            "task_input_sha256": original_input,
            "candidate_id": candidate_id,
            "candidate_version": candidate_version,
            "candidate_content_sha256": candidate_hash,
            "rules_sha256": rules_sha256,
            "physical_design_sha256": canonical_sha256(design),
            "production_slug": slug,
            "text2game_commit": self.text2game_commit,
            "text2cad_commit": self.text2cad_commit,
            "toolchain_sha256": self.toolchain_sha256,
            "calibration_profile_sha256": self.profile.profile_sha256,
            "printer_target_sha256": self.target.target_sha256,
        }

    def _prepare_operation(
        self,
        operation_id: str,
        identity: Mapping[str, Any],
        design: Mapping[str, Any],
        rules: Mapping[str, Any],
        *,
        reconcile_only: bool,
    ) -> _Operation:
        key = f"alice.text2game:v1:{operation_id}"
        directory = self.work_root / operation_id
        repository = directory / "repo"
        source = repository / "out" / str(identity["production_slug"])
        state = self.store.get_state(key)
        if state is None:
            if reconcile_only and not directory.is_dir():
                raise AmbiguousText2GameEffect(
                    "reconciliation found no exact text2game operation workspace"
                )
            if directory.exists():
                existing_identity = _load_mapping(
                    directory / "identity.json", "operation identity"
                )
                if existing_identity != dict(identity):
                    raise AmbiguousText2GameEffect(
                        "existing text2game workspace has a different identity"
                    )
            else:
                if reconcile_only:
                    raise AmbiguousText2GameEffect(
                        "reconciliation cannot create a missing operation workspace"
                    )
                self._create_operation_workspace(directory, identity, design, rules)
            value = {
                "schema_version": STATE_SCHEMA_VERSION,
                "identity": dict(identity),
                "design": dict(design),
                "rules": {field: rules.get(field) for field in _RULE_FIELDS},
                "status": "prepared",
                "operation_dir": str(directory),
                "source_dir": str(source),
            }
            try:
                state = self.store.put_state(key, value, None)
            except StateConflictError:
                state = self.store.get_state(key)
                if state is None:
                    raise
        value = _state_value(state)
        if value.get("identity") != dict(identity):
            raise AmbiguousText2GameEffect("text2game durable identity mismatch")
        if value.get("design") != dict(design) or value.get("rules") != {
            field: rules.get(field) for field in _RULE_FIELDS
        }:
            raise AmbiguousText2GameEffect("text2game durable design/rules mismatch")
        if value.get("operation_dir") != str(directory) or value.get("source_dir") != str(source):
            raise AmbiguousText2GameEffect("text2game durable path binding mismatch")
        if not directory.is_dir() or directory.is_symlink():
            raise AmbiguousText2GameEffect("text2game operation directory is unavailable")
        if _load_mapping(directory / "identity.json", "operation identity") != dict(identity):
            raise AmbiguousText2GameEffect("text2game operation identity file changed")
        return _Operation(
            operation_id=operation_id,
            key=key,
            directory=directory,
            repository=repository,
            source=source,
            identity=dict(identity),
            design=dict(design),
            rules=dict(rules),
        )

    def _create_operation_workspace(
        self,
        directory: Path,
        identity: Mapping[str, Any],
        design: Mapping[str, Any],
        rules: Mapping[str, Any],
    ) -> None:
        _ensure_private_directory_parent(self.work_root)
        snapshot = self._text2game_snapshot()
        text2cad_snapshot = self._text2cad_snapshot()
        temporary = Path(
            tempfile.mkdtemp(prefix=f".{directory.name}.", dir=self.work_root)
        )
        try:
            temporary.chmod(0o700)
            repo = temporary / "repo"
            runtime_hashes = self._copy_repo(repo, snapshot)
            text2cad_copy = temporary / "toolchain" / "text2cad"
            _copy_snapshot_subtree(
                self.text2cad_repo,
                text2cad_copy,
                text2cad_snapshot,
                "",
            )
            text2cad_runtime_hashes = _snapshot_regular_tree(text2cad_copy)
            skill_home = temporary / "home" / ".claude" / "skills" / "cadcode"
            _copy_snapshot_subtree(
                text2cad_copy,
                skill_home,
                text2cad_snapshot,
                "skills/cadcode/",
            )
            _required_regular_file(
                skill_home / "SKILL.md", "pinned operation cadcode skill"
            )
            # Pinned text2game's preflight checks ``~/.codex/auth.json`` only
            # for existence and does not honor CODEX_HOME there.  Supply a
            # deliberately non-secret marker in the operation HOME.  The real
            # Codex CLI still authenticates through the separately configured,
            # owner-only CODEX_HOME; if it ever ignores that variable, this
            # marker cannot authenticate and the phase fails closed.
            _write_json(
                temporary / "home" / ".codex" / "auth.json",
                {
                    "schema_version": "alice.codex-preflight-marker.v1",
                    "credential_source": "CODEX_HOME",
                },
            )
            shim_hashes = self._write_operation_shims(temporary, directory)
            source = repo / "out" / str(identity["production_slug"])
            source.mkdir(parents=True, mode=0o700)
            rules_markdown = rules.get("rules_markdown")
            if not isinstance(rules_markdown, str) or not rules_markdown.strip():
                raise Text2GameAdapterError("accepted rules_markdown is missing")
            _write_bytes(source / "gdd.md", rules_markdown.encode("utf-8"))
            text2game = design.get("text2game")
            if not isinstance(text2game, Mapping):
                raise Text2GameAdapterError("physical.design text2game plan is missing")
            _write_json(source / "components.json", text2game.get("components"))
            _write_json(source / "mechanisms.json", text2game.get("mechanisms"))
            accepted_game = design.get("accepted_game")
            concept = accepted_game.get("concept") if isinstance(accepted_game, Mapping) else None
            if not isinstance(concept, str) or not concept.strip():
                raise Text2GameAdapterError("physical.design accepted_game concept is missing")
            _write_bytes(source / "seed.md", (concept.strip() + "\n").encode("utf-8"))
            self._verify_seed_compatibility(repo, source)
            _write_json(temporary / "identity.json", identity)
            _write_json(
                temporary / "source-manifest.json",
                {
                    "commit": self.text2game_commit,
                    "manifest_sha256": snapshot.manifest_sha256,
                    "text2cad_commit": self.text2cad_commit,
                    "text2cad_manifest_sha256": text2cad_snapshot.manifest_sha256,
                    "toolchain_sha256": self.toolchain_sha256,
                    "operation_runtime_hashes": runtime_hashes,
                    "operation_runtime_manifest_sha256": canonical_sha256(
                        runtime_hashes
                    ),
                    "text2cad_runtime_hashes": text2cad_runtime_hashes,
                    "text2cad_runtime_manifest_sha256": canonical_sha256(
                        text2cad_runtime_hashes
                    ),
                    "operation_shim_hashes": shim_hashes,
                    "files": [
                        {"path": path, "sha256": digest, "bytes": size}
                        for path, digest, size in snapshot.files
                    ],
                },
            )
            try:
                os.rename(temporary, directory)
            except FileExistsError as exc:
                raise AmbiguousText2GameEffect(
                    "text2game operation workspace appeared concurrently"
                ) from exc
            temporary = Path()
        finally:
            if temporary != Path() and temporary.exists():
                shutil.rmtree(temporary)

    def _verify_seed_compatibility(self, repository: Path, source: Path) -> None:
        """Run text2game's pinned deterministic checker before any model call."""

        checker = _required_regular_file(
            repository / "consistency.py", "pinned consistency.py"
        )
        _required_regular_file(repository / "mechanisms.md", "pinned mechanisms.md")
        deterministic_names = {
            "PATH",
            "LANG",
            "LC_ALL",
            "TMPDIR",
            "PARTS",
            "GDD_MAX_WORDS",
            "GDD_MAX_GLOSSARY",
            "GDD_MAX_RULE_NUMBERS",
            "SCULPT_MAX",
            "SETUP_MAX_STEPS",
            "PLATE_MM",
        }
        environment = {
            name: value
            for name, value in self.environment.items()
            if name in deterministic_names
        }
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            result = run_bounded_process(
                (self.command[0], str(checker), str(source)),
                input_bytes=b"",
                timeout_seconds=min(120.0, self.timeout_seconds),
                stdout_limit_bytes=131_072,
                stderr_limit_bytes=65_536,
                shutdown_grace_seconds=self.shutdown_grace_seconds,
                env=environment,
                cwd=repository,
            )
        except (BoundedProcessTimeout, BoundedProcessOutputLimit, OSError) as exc:
            raise Text2GameAdapterError(
                f"pinned text2game compatibility check failed ({type(exc).__name__})"
            ) from exc
        report_path = source / "consistency.json"
        try:
            report = _load_json(report_path, "text2game seed consistency")
        except Text2GameAdapterError:
            report = None
        if result.returncode != 0 or not isinstance(report, list) or any(
            isinstance(item, Mapping) and item.get("severity") == "high"
            for item in report or []
        ):
            raise Text2GameAdapterError(
                "accepted rules/physical design are not text2game-compatible; "
                f"stdout_sha256={hashlib.sha256(result.stdout).hexdigest()}; "
                f"stderr_sha256={result.stderr_sha256}"
            )
        if any(not isinstance(item, Mapping) for item in report):
            raise Text2GameAdapterError("text2game compatibility report is malformed")
        os.replace(report_path, source / "alice-seed-consistency.json")

    def _advance_operation(
        self, operation: _Operation, *, reconcile_only: bool
    ) -> Mapping[str, Any]:
        while True:
            state = self.store.get_state(operation.key)
            if state is None:
                raise AmbiguousText2GameEffect("text2game durable state disappeared")
            value = _state_value(state)
            if value.get("identity") != dict(operation.identity):
                raise AmbiguousText2GameEffect("text2game durable identity changed")
            status = value.get("status")
            if status == "confirmed":
                result = value.get("result")
                if not isinstance(result, Mapping):
                    raise AmbiguousText2GameEffect("confirmed text2game result is malformed")
                return dict(result)
            if status == "prepared":
                # The inner operation writes ``phase1_sending`` before Popen.
                # Reaching ``prepared`` during an outer reconciliation is
                # therefore conclusive proof that no phase process started.
                # It is safe to cross the first sender fence now; every other
                # reconciliation state remains adoption-only for its phase.
                self._send_phase(operation, state, "1")
                continue
            if status == "phase1_sending":
                self._adopt_phase(operation, state, "1")
                continue
            if status == "phase1_confirmed":
                self._send_phase(operation, state, "2")
                continue
            if status == "phase2_sending":
                self._adopt_phase(operation, state, "2")
                continue
            if status == "phase2_confirmed":
                self._send_phase(operation, state, "3")
                continue
            if status == "phase3_sending":
                self._adopt_phase(operation, state, "3")
                continue
            if status == "phase3_confirmed":
                result = self._finalize(operation, value)
                updated = dict(value)
                updated.update({"status": "confirmed", "result": result})
                try:
                    self.store.put_state(operation.key, updated, state.version)
                except StateConflictError:
                    continue
                return result
            raise AmbiguousText2GameEffect(
                f"unknown text2game operation status {status!r}"
            )

    def _send_phase(
        self, operation: _Operation, state: VersionedStateRecord, phase: str
    ) -> None:
        readiness_failures = self._toolchain_failures()
        if readiness_failures:
            raise Text2GameAdapterError(
                "text2game runtime preflight failed: "
                + ", ".join(readiness_failures)
            )
        value = _state_value(state)
        command = [
            self.command[0],
            str(operation.repository / "text2game"),
            "--slug",
            str(operation.identity["production_slug"]),
            "--phase",
            phase,
        ]
        if phase == "1":
            command.extend(("--max-rounds", "1"))
        _validate_phase_command(command, operation.repository)
        self._verify_operation_runtime(operation)
        phase_environment = dict(self.environment)
        operation_home = operation.directory / "home"
        phase_environment["HOME"] = str(operation_home)
        phase_environment["TEXT2CAD_DIR"] = str(
            operation.directory / "toolchain" / "text2cad"
        )
        phase_environment["MEASURE_CMD"] = "alice-measure"
        phase_environment["PATH"] = (
            str(operation_home / ".local" / "bin")
            + os.pathsep
            + phase_environment.get("PATH", os.defpath)
        )
        sending = dict(value)
        sending["status"] = f"phase{phase}_sending"
        sending["phase_started_at"] = time.time()
        try:
            sending_state = self.store.put_state(operation.key, sending, state.version)
        except StateConflictError:
            return
        try:
            result = run_bounded_process(
                command,
                input_bytes=b"",
                timeout_seconds=self.timeout_seconds,
                stdout_limit_bytes=self.max_output_bytes,
                stderr_limit_bytes=self.max_stderr_bytes,
                shutdown_grace_seconds=self.shutdown_grace_seconds,
                env=phase_environment,
                cwd=operation.repository,
            )
        except BoundedProcessSpawnError as exc:
            # ``run_bounded_process`` creates its process before entering any
            # later code that can raise OSError.  This branch therefore means
            # Popen never started and no external effect exists.  Restore the
            # exact prior state with CAS so the normal retry remains usable.
            try:
                self.store.put_state(operation.key, value, sending_state.version)
            except StateConflictError as conflict:
                raise AmbiguousText2GameEffect(
                    f"text2game phase {phase} pre-spawn rollback lost its state race"
                ) from conflict
            raise Text2GameAdapterError(
                f"text2game phase {phase} could not start ({type(exc).__name__})"
            ) from exc
        except (BoundedProcessTimeout, BoundedProcessOutputLimit) as exc:
            raise AmbiguousText2GameEffect(
                f"text2game phase {phase} outcome is ambiguous ({type(exc).__name__})"
            ) from exc
        if result.returncode != 0:
            raise AmbiguousText2GameEffect(
                f"text2game phase {phase} exited {result.returncode}; "
                f"stderr_sha256={result.stderr_sha256}; stderr_bytes={result.stderr_bytes}"
            )
        self._verify_locked_inputs(operation)
        self._phase_complete(operation, phase)
        confirmed = dict(sending)
        confirmed.update(
            {
                "status": f"phase{phase}_confirmed",
                "phase_completed_at": time.time(),
                "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                "stdout_bytes": result.stdout_bytes,
                "stderr_sha256": result.stderr_sha256,
                "stderr_bytes": result.stderr_bytes,
            }
        )
        try:
            self.store.put_state(operation.key, confirmed, sending_state.version)
        except StateConflictError as exc:
            raise AmbiguousText2GameEffect(
                "text2game phase receipt lost its durable state race"
            ) from exc

    def _adopt_phase(
        self, operation: _Operation, state: VersionedStateRecord, phase: str
    ) -> None:
        try:
            self._verify_locked_inputs(operation)
            self._phase_complete(operation, phase)
        except Exception as exc:
            raise AmbiguousText2GameEffect(
                f"text2game phase {phase} cannot be conclusively adopted"
            ) from exc
        value = _state_value(state)
        value.update(
            {
                "status": f"phase{phase}_confirmed",
                "phase_completed_at": time.time(),
                "adopted_after_uncertain_send": True,
            }
        )
        try:
            self.store.put_state(operation.key, value, state.version)
        except StateConflictError:
            return

    def _verify_operation_runtime(self, operation: _Operation) -> None:
        manifest = _load_mapping(
            operation.directory / "source-manifest.json", "source manifest"
        )
        runtime_hashes = _sha256_mapping(
            manifest.get("operation_runtime_hashes"),
            "operation runtime hashes",
        )
        text2cad_hashes = _sha256_mapping(
            manifest.get("text2cad_runtime_hashes"),
            "text2cad runtime hashes",
        )
        shim_hashes = _sha256_mapping(
            manifest.get("operation_shim_hashes"),
            "operation shim hashes",
        )
        if manifest.get("operation_runtime_manifest_sha256") != canonical_sha256(
            runtime_hashes
        ) or manifest.get("text2cad_runtime_manifest_sha256") != canonical_sha256(
            text2cad_hashes
        ):
            raise Text2GameAdapterError("operation runtime manifest is corrupt")
        if _snapshot_regular_tree(
            operation.repository, excluded_top_level=frozenset({"out"})
        ) != runtime_hashes:
            raise Text2GameAdapterError("trusted text2game runtime changed")
        operation_text2cad = operation.directory / "toolchain" / "text2cad"
        if _snapshot_regular_tree(operation_text2cad) != text2cad_hashes:
            raise Text2GameAdapterError("trusted text2cad runtime changed")
        expected_skill = {
            path[len("skills/cadcode/") :]: digest
            for path, digest in text2cad_hashes.items()
            if path.startswith("skills/cadcode/")
        }
        skill = operation.directory / "home" / ".claude" / "skills" / "cadcode"
        if not expected_skill or _snapshot_regular_tree(skill) != expected_skill:
            raise Text2GameAdapterError("operation CAD skill changed")
        marker = _load_mapping(
            operation.directory / "home" / ".codex" / "auth.json",
            "Codex preflight marker",
        )
        if marker != {
            "schema_version": "alice.codex-preflight-marker.v1",
            "credential_source": "CODEX_HOME",
        }:
            raise Text2GameAdapterError("Codex preflight marker changed")
        shim_dir = operation.directory / "home" / ".local" / "bin"
        if _snapshot_regular_tree(shim_dir) != shim_hashes or set(shim_hashes) != {
            "alice-measure",
            "python",
            "python3",
            "uv",
        }:
            raise Text2GameAdapterError("operation CAD tool shim changed")
        for name, path, executable in (
            ("cad_python", self.cad_python, True),
            ("slicer_binary", self.slicer_binary, True),
            ("slicer_profile", self.slicer_profile, False),
            ("codex_binary", self.codex_binary, True),
            ("git_binary", self.git_binary, True),
        ):
            if not _file_pin_ready(
                path, self._tool_pins[name], executable=executable
            ):
                raise Text2GameAdapterError(
                    f"pinned operation dependency changed: {name}"
                )
        self._verify_interpreter()

    def _verify_locked_inputs(self, operation: _Operation) -> None:
        self._verify_operation_runtime(operation)
        rules_markdown = operation.rules.get("rules_markdown")
        expected_rules = (
            rules_markdown.encode("utf-8")
            if isinstance(rules_markdown, str)
            else b""
        )
        if (operation.source / "gdd.md").read_bytes() != expected_rules:
            raise Text2GameAdapterError("text2game changed the accepted rules")
        text2game = operation.design.get("text2game")
        if not isinstance(text2game, Mapping):
            raise Text2GameAdapterError("physical.design text2game plan is missing")
        if _load_json(operation.source / "components.json", "components.json") != text2game.get(
            "components"
        ):
            raise Text2GameAdapterError("text2game changed the accepted components")
        if _load_json(operation.source / "mechanisms.json", "mechanisms.json") != text2game.get(
            "mechanisms"
        ):
            raise Text2GameAdapterError("text2game changed the accepted mechanisms")

    def _phase_complete(self, operation: _Operation, phase: str) -> None:
        if phase == "1":
            receipt = _load_mapping(operation.source / "phase1.json", "phase1.json")
            if receipt.get("exit") != "clean":
                raise Text2GameAdapterError("text2game phase 1 did not exit clean")
            if receipt.get("priorart") not in {"clear", "novel", "none"}:
                raise Text2GameAdapterError("text2game prior-art gate did not clear")
            if receipt.get("consistency_high") != 0 or receipt.get("critic_high") != 0:
                raise Text2GameAdapterError("text2game phase 1 has unresolved high findings")
            if receipt.get("referee_clean") is not True or receipt.get("referee_missing") is True:
                raise Text2GameAdapterError("text2game referee gate did not clear")
            for name in ("consistency.json", "critic.json", "referee.md", "priorart.json"):
                _required_regular_file(operation.source / name, name)
            return
        if phase == "2":
            receipt = _load_mapping(operation.source / "phase2.json", "phase2.json")
            if receipt.get("staged") is not True or receipt.get("coherence_fail") is True:
                raise Text2GameAdapterError("text2game phase 2 did not pass staging/coherence")
            components = operation.design["text2game"]["components"]
            expected = {str(row["id"]) for row in components}
            actual = {
                path.stem
                for path in (operation.source / "fe_parts").glob("*.stl")
                if path.is_file() and not path.is_symlink()
            }
            if actual != expected:
                raise Text2GameAdapterError("phase 2 meshes do not match accepted components")
            _required_regular_file(operation.source / "assembled.stl", "assembled.stl")
            steps = [
                path
                for suffix in ("*.step", "*.stp")
                for path in operation.source.glob(suffix)
                if path.is_file() and not path.is_symlink()
            ]
            if len(steps) != 1:
                raise Text2GameAdapterError("phase 2 needs one root STEP assembly")
            _required_regular_file(
                operation.source / "renders" / "assembled.png",
                "renders/assembled.png",
            )
            return
        if phase == "3":
            receipt = _load_mapping(operation.source / "phase3.json", "phase3.json")
            gate = _load_mapping(operation.source / "gate.json", "gate.json")
            slice_report = _load_mapping(
                operation.source / "slice_report.json", "slice_report.json"
            )
            if gate.get("pass") is not True or gate.get("fails") not in ([], None):
                raise Text2GameAdapterError("text2game print gate did not pass")
            if receipt.get("fit_ok") is not True or receipt.get("unplaceable") not in ([], None):
                raise Text2GameAdapterError("text2game phase 3 fit/plate gate did not pass")
            if slice_report.get("failed") not in ([], None):
                raise Text2GameAdapterError("text2game slicer reported failed parts")
            for name in ("plates.json", "rulebook.md", "print_kit.md"):
                _required_regular_file(operation.source / name, name)
            return
        raise Text2GameAdapterError(f"unsupported phase {phase!r}")

    def _validate_physical_design(
        self, design: Mapping[str, Any], source: Path
    ) -> dict[str, Any]:
        receipts: dict[str, Any] = {}
        hashes: dict[str, str] = {}
        binding = validate_profile_binding(self.profile, self.target)
        profile_check = self_check_calibration_profile(self.profile)
        for key, receipt in (
            ("profile_binding", binding),
            ("profile_self_check", profile_check),
        ):
            receipts[key] = receipt.to_dict()
            hashes[key] = receipt.receipt_sha256
            if receipt.status != "passed":
                raise Text2GameAdapterError(f"{key} did not pass")
        fits = design.get("fit_requirements")
        if not isinstance(fits, list):
            raise Text2GameAdapterError("physical.design fit_requirements are missing")
        for raw in fits:
            if not isinstance(raw, Mapping):
                raise Text2GameAdapterError("fit requirement must be an object")
            fit_id = _required_string(raw.get("id"), "fit requirement id")
            if raw.get("kind") == "assembled":
                receipt = derive_assembled_fit(
                    self.profile,
                    self.target,
                    fit_class=_required_string(raw.get("fit_class"), "fit_class"),
                    owned_side=_required_string(raw.get("owned_side"), "owned_side"),
                    owned_dimension_mm=raw.get("owned_dimension_mm"),
                )
            elif raw.get("kind") == "print_in_place":
                receipt = derive_print_in_place_fit(
                    self.profile,
                    self.target,
                    fit_class=_required_string(raw.get("fit_class"), "fit_class"),
                )
            else:
                raise Text2GameAdapterError(f"unknown fit kind for {fit_id}")
            key = f"fit:{fit_id}"
            receipts[key] = receipt.to_dict()
            hashes[key] = receipt.receipt_sha256
            if receipt.status != "passed":
                raise Text2GameAdapterError(f"fit requirement {fit_id} did not pass")
        topology = design.get("topology_expectations")
        if not isinstance(topology, list) or not topology:
            raise Text2GameAdapterError("physical.design topology expectations are missing")
        for raw in topology:
            if not isinstance(raw, Mapping):
                raise Text2GameAdapterError("topology expectation must be an object")
            part = _required_string(raw.get("part_id"), "topology part_id")
            mesh = source / "fe_parts" / f"{part}.stl"
            data = _required_regular_file(mesh, f"fe_parts/{part}.stl").read_bytes()
            expected_bodies = raw.get("expected_body_count")
            observation = None
            if expected_bodies is not None:
                if self.kernel_evaluator is None:
                    raise Text2GameAdapterError(
                        f"topology {part} requires an unavailable kernel body evaluator"
                    )
                try:
                    observed = self.kernel_evaluator(data, dict(raw))
                    observation = (
                        observed
                        if isinstance(observed, KernelBodyObservation)
                        else KernelBodyObservation.from_mapping(observed)
                    )
                except Exception as exc:
                    raise Text2GameAdapterError(
                        f"topology {part} kernel evaluator failed"
                    ) from exc
            receipt = inspect_stl_topology(
                data,
                expected_shell_count=_positive_integer(
                    raw.get("expected_shell_count"), "expected_shell_count"
                ),
                expected_body_count=(
                    _positive_integer(expected_bodies, "expected_body_count")
                    if expected_bodies is not None
                    else None
                ),
                kernel_body_observation=observation,
                expected_source_sha256=hashlib.sha256(data).hexdigest(),
                expected_source_bytes=len(data),
            )
            key = f"topology:{part}"
            receipts[key] = receipt.to_dict()
            hashes[key] = receipt.receipt_sha256
            if receipt.status != "passed":
                raise Text2GameAdapterError(f"topology expectation {part} did not pass")
        motions = design.get("motion_conditions")
        if not isinstance(motions, list):
            raise Text2GameAdapterError("physical.design motion_conditions are missing")
        for raw in motions:
            condition = MotionCondition.from_mapping(raw)
            if self.motion_evaluator is None:
                raise Text2GameAdapterError(
                    f"motion condition {condition.condition_id} needs an evaluator"
                )
            receipt = evaluate_motion_condition(condition, self.motion_evaluator)
            key = f"motion:{condition.condition_id}"
            receipts[key] = receipt.to_dict()
            hashes[key] = receipt.receipt_sha256
            if receipt.status != "passed":
                raise Text2GameAdapterError(
                    f"motion condition {condition.condition_id} did not pass"
                )
        return {"receipts": receipts, "hashes": hashes}

    def _finalize(self, operation: _Operation, state: Mapping[str, Any]) -> dict[str, Any]:
        self._verify_locked_inputs(operation)
        self._phase_complete(operation, "1")
        self._phase_complete(operation, "2")
        self._phase_complete(operation, "3")
        source_hashes = _snapshot_output(operation.source)
        validation = self._validate_physical_design(operation.design, operation.source)
        export = self._export(state, operation.design, source_hashes, operation=operation)
        lineage = export.page_builder_lineage()
        output = dict(lineage)
        output.update(
            {
                "page_builder_lineage": dict(lineage),
                "physical_design_sha256": operation.identity["physical_design_sha256"],
                "text2game_operation_id": operation.operation_id,
                "text2cad_repo_commit": self.text2cad_commit,
                "toolchain_sha256": self.toolchain_sha256,
                "validation_receipt_hashes": validation["hashes"],
                "receipt": {
                    "schema_version": CAD_RECEIPT_VERSION,
                    "status": "passed",
                    "operation_id": operation.operation_id,
                    "effect_operation_key": operation.identity["effect_operation_key"],
                    "task_input_sha256": operation.identity["task_input_sha256"],
                    "source_repo_manifest_sha256": _load_mapping(
                        operation.directory / "source-manifest.json", "source manifest"
                    )["manifest_sha256"],
                    "text2cad_source_manifest_sha256": _load_mapping(
                        operation.directory / "source-manifest.json", "source manifest"
                    )["text2cad_manifest_sha256"],
                    "text2cad_repo_commit": self.text2cad_commit,
                    "toolchain_sha256": self.toolchain_sha256,
                    "source_snapshot_sha256": export.source_snapshot_sha256,
                    "validation_receipts": validation["receipts"],
                    "limitations": [
                        "CAD/DFM checks do not substitute for the later physical prototype",
                        "the exported workspace remains private until Dee publishes it",
                    ],
                },
            }
        )
        return output

    def _export(
        self,
        state: Mapping[str, Any],
        design: Mapping[str, Any],
        source_hashes: Mapping[str, str],
        *,
        operation: _Operation | None = None,
    ):
        if operation is None:
            identity = state.get("identity")
            if not isinstance(identity, Mapping):
                raise Text2GameAdapterError("text2game state identity is missing")
            operation_id = _required_string(identity.get("operation_id"), "operation_id")
            directory = Path(_required_string(state.get("operation_dir"), "operation_dir"))
            source = Path(_required_string(state.get("source_dir"), "source_dir"))
            rules = _accepted_rules_from_identity_state(state)
            operation = _Operation(
                operation_id=operation_id,
                key=f"alice.text2game:v1:{operation_id}",
                directory=directory,
                repository=directory / "repo",
                source=source,
                identity=dict(identity),
                design=dict(design),
                rules=rules,
            )
        rule_document = {field: operation.rules.get(field) for field in _RULE_FIELDS}
        return export_text2game_to_vibe(
            Text2GameExportRequest(
                source_dir=operation.source,
                vibe_workspace=self.vibe_workspace,
                production_slug=str(operation.identity["production_slug"]),
                candidate_id=str(operation.identity["candidate_id"]),
                candidate_version=int(operation.identity["candidate_version"]),
                candidate_content_sha256=str(
                    operation.identity["candidate_content_sha256"]
                ),
                accepted_game=design["accepted_game"],
                accepted_rules=rule_document,
                accepted_rules_sha256=str(operation.identity["rules_sha256"]),
                cad_artifact_hashes=source_hashes,
                dfm_artifact_hashes=source_hashes,
                source_repo_url=TEXT2GAME_REPOSITORY,
                source_repo_commit=self.text2game_commit,
            )
        )


def _absolute_path(value: str | Path, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    return path


def _positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a positive finite number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError(f"{label} must be a positive finite number")
    return normalized


def _positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise Text2GameAdapterError(f"{label} must be a non-empty trimmed string")
    return value


def _required_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise Text2GameAdapterError(f"{label} must be a lowercase SHA-256")
    return value


def _sha256_mapping(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or not value:
        raise Text2GameAdapterError(f"{label} must be a non-empty object")
    result: dict[str, str] = {}
    for key, digest in value.items():
        if (
            not isinstance(key, str)
            or not key
            or PurePosixPath(key).is_absolute()
            or ".." in PurePosixPath(key).parts
            or not isinstance(digest, str)
            or _SHA256.fullmatch(digest) is None
        ):
            raise Text2GameAdapterError(f"{label} contains an invalid entry")
        result[key] = digest
    return result


def _canonical_document(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise Text2GameAdapterError("document is not finite canonical JSON") from exc


def _write_json(path: Path, value: Any) -> None:
    _write_bytes(path, _canonical_document(value))


def _write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise Text2GameAdapterError(f"could not create operation file {path.name}") from exc
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)


def _harden_operation_harness(path: Path) -> None:
    """Remove repo-wide model write access and ignore ambient Codex policy."""

    file = _required_regular_file(path, "pinned harness.py")
    original = file.read_bytes()
    add_dir = b'            "-C", str(out_dir), "--add-dir", str(HERE),\n'
    checkpoint = b'            "--skip-git-repo-check",\n'
    if original.count(add_dir) != 1 or original.count(checkpoint) != 1:
        raise Text2GameAdapterError(
            "pinned text2game harness no longer matches the reviewed hardening patch"
        )
    hardened = original.replace(
        add_dir,
        b'            "-C", str(out_dir),\n',
        1,
    ).replace(
        checkpoint,
        checkpoint
        + b'            "--ephemeral", "--ignore-user-config", "--ignore-rules",\n'
        + b'            "--strict-config",\n',
        1,
    )
    if b'"--add-dir", str(HERE)' in hardened:
        raise Text2GameAdapterError("text2game harness hardening was incomplete")
    file.chmod(0o600)
    descriptor = os.open(
        file,
        os.O_WRONLY | os.O_TRUNC | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(hardened)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)
    file.chmod(0o400)


def _snapshot_regular_tree(
    root: Path, *, excluded_top_level: frozenset[str] = frozenset()
) -> dict[str, str]:
    if root.is_symlink() or not root.is_dir():
        raise Text2GameAdapterError("operation runtime tree is unavailable")
    result: dict[str, str] = {}
    total = 0
    for path in sorted(root.rglob("*")):
        relative_path = path.relative_to(root)
        if relative_path.parts and relative_path.parts[0] in excluded_top_level:
            continue
        metadata = path.lstat()
        if stat.S_ISDIR(metadata.st_mode):
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise Text2GameAdapterError("operation runtime contains a non-regular entry")
        relative = relative_path.as_posix()
        if _credential_like_path(relative):
            raise Text2GameAdapterError("operation runtime contains a credential-like file")
        total += int(metadata.st_size)
        if len(result) >= _MAX_TRACKED_FILES or total > _MAX_TRACKED_BYTES:
            raise Text2GameAdapterError("operation runtime exceeds resource limits")
        result[relative] = _sha256_file(path)
    if not result:
        raise Text2GameAdapterError("operation runtime tree is empty")
    return result


def _credential_like_path(relative: str) -> bool:
    name = PurePosixPath(relative).name.casefold()
    return bool(
        name in _FORBIDDEN_SOURCE_NAMES
        or name.startswith(".env.")
        or name.endswith((".pem", ".p12", ".pfx"))
    )


def _load_json(path: Path, label: str) -> Any:
    file = _required_regular_file(path, label)
    if file.stat().st_size > 64 << 20:
        raise Text2GameAdapterError(f"{label} exceeds its byte limit")
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Text2GameAdapterError(f"{label} is not valid JSON") from exc


def _load_mapping(path: Path, label: str) -> Mapping[str, Any]:
    value = _load_json(path, label)
    if not isinstance(value, Mapping):
        raise Text2GameAdapterError(f"{label} must be an object")
    return value


def _required_regular_file(path: Path, label: str) -> Path:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise Text2GameAdapterError(f"required file is unavailable: {label}") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0:
        raise Text2GameAdapterError(f"required file must be non-empty and regular: {label}")
    return path


def _contained_relative_file(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if (
        not relative
        or pure.is_absolute()
        or ".." in pure.parts
        or "." in pure.parts
        or pure.as_posix() != relative
    ):
        raise Text2GameAdapterError(f"unsafe tracked path {relative!r}")
    path = root.joinpath(*pure.parts)
    try:
        resolved_root = root.resolve(strict=True)
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise Text2GameAdapterError(f"tracked source is unavailable: {relative}") from exc
    if resolved.parent != resolved_root and resolved_root not in resolved.parents:
        raise Text2GameAdapterError(f"tracked source escapes checkout: {relative}")
    if path.is_symlink():
        raise Text2GameAdapterError(f"tracked symlinks are forbidden: {relative}")
    return path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _file_hashes(path: Path, object_format: str) -> tuple[str, str]:
    """Hash a worktree file both canonically and as its pinned Git blob."""

    if object_format == "sha1":
        blob = hashlib.sha1()  # noqa: S324 - Git's repository object identity
    elif object_format == "sha256":
        blob = hashlib.sha256()
    else:
        raise Text2GameAdapterError("unsupported Git object format")
    size = path.stat().st_size
    blob.update(f"blob {size}\0".encode("ascii"))
    canonical = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            canonical.update(chunk)
            blob.update(chunk)
    return canonical.hexdigest(), blob.hexdigest()


def _copy_snapshot_subtree(
    source_root: Path,
    destination: Path,
    snapshot: _RepoSnapshot,
    prefix: str,
) -> None:
    """Copy one commit-verified subtree into a private operation directory."""

    pure_prefix = PurePosixPath(prefix.rstrip("/")) if prefix else None
    if prefix and (
        not prefix.endswith("/")
        or pure_prefix is None
        or pure_prefix.is_absolute()
        or not pure_prefix.parts
        or any(part in {"", ".", ".."} for part in pure_prefix.parts)
    ):
        raise Text2GameAdapterError("snapshot subtree prefix is unsafe")
    selected = [
        (relative, digest, size)
        for relative, digest, size in snapshot.files
        if not prefix or relative.startswith(prefix)
    ]
    if not selected:
        raise Text2GameAdapterError("pinned snapshot subtree is empty")
    destination.mkdir(parents=True, mode=0o700)
    destination.chmod(0o700)
    for relative, expected, expected_size in selected:
        suffix = relative[len(prefix) :] if prefix else relative
        pure_suffix = PurePosixPath(suffix)
        if (
            not suffix
            or pure_suffix.is_absolute()
            or any(part in {"", ".", ".."} for part in pure_suffix.parts)
        ):
            raise Text2GameAdapterError("pinned subtree contains an unsafe path")
        source = _contained_relative_file(source_root, relative)
        target = destination.joinpath(*pure_suffix.parts)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        target.parent.chmod(0o700)
        before = source.lstat()
        data = source.read_bytes()
        after = source.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            or len(data) != expected_size
            or hashlib.sha256(data).hexdigest() != expected
        ):
            raise Text2GameAdapterError(
                "pinned source changed while copying the operation skill"
            )
        _write_bytes(target, data)
        target.chmod(0o500 if before.st_mode & 0o111 else 0o400)


def _initial_file_pin(path: Path) -> _FilePin:
    try:
        target = path.resolve(strict=True)
        metadata = target.stat()
        if not stat.S_ISREG(metadata.st_mode):
            return _FilePin(target, None)
        return _FilePin(target, _sha256_file(target))
    except OSError:
        return _FilePin(path.resolve(strict=False), None)


def _file_pin_ready(
    configured: Path, pin: _FilePin, *, executable: bool
) -> bool:
    try:
        target = configured.resolve(strict=True)
        metadata = target.stat()
        return bool(
            pin.sha256
            and target == pin.target
            and stat.S_ISREG(metadata.st_mode)
            and (not executable or os.access(target, os.X_OK))
            and _sha256_file(target) == pin.sha256
        )
    except OSError:
        return False


def _plain_required_file(path: Path) -> bool:
    try:
        metadata = path.lstat()
        return stat.S_ISREG(metadata.st_mode) and metadata.st_size > 0
    except OSError:
        return False


def _secure_codex_home(path: Path) -> bool:
    """Require a dedicated owner-only home and non-symlink auth file."""

    try:
        home = path.lstat()
        if (
            not stat.S_ISDIR(home.st_mode)
            or home.st_uid != os.geteuid()
            or stat.S_IMODE(home.st_mode) & 0o077
            or stat.S_IMODE(home.st_mode) & 0o7000
        ):
            return False
        auth_path = path / "auth.json"
        auth = auth_path.lstat()
        mode = stat.S_IMODE(auth.st_mode)
        return bool(
            stat.S_ISREG(auth.st_mode)
            and auth.st_uid == os.geteuid()
            and not (mode & 0o177)
            and not (mode & 0o7000)
            and auth.st_size > 0
        )
    except OSError:
        return False


def _ensure_private_directory_parent(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise Text2GameAdapterError("work_root must be a non-symlink directory")
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o077:
            raise Text2GameAdapterError("work_root must not be group/world accessible")
        return
    parent = path.parent
    if not parent.is_dir() or parent.is_symlink():
        raise Text2GameAdapterError("work_root parent is unavailable")
    path.mkdir(mode=0o700)


def _directory_ready_without_writing(path: Path) -> bool:
    try:
        if path.exists():
            return (
                path.is_dir()
                and not path.is_symlink()
                and stat.S_IMODE(path.stat().st_mode) & 0o077 == 0
                and os.access(path, os.W_OK | os.X_OK)
            )
        parent = path.parent
        return (
            parent.is_dir()
            and not parent.is_symlink()
            and os.access(parent, os.W_OK | os.X_OK)
        )
    except OSError:
        return False


def _state_value(state: VersionedStateRecord) -> dict[str, Any]:
    if not isinstance(state.value, Mapping):
        raise AmbiguousText2GameEffect("text2game state value is malformed")
    value = dict(state.value)
    if value.get("schema_version") != STATE_SCHEMA_VERSION:
        raise AmbiguousText2GameEffect("text2game state version is unsupported")
    return value


def _unwrap_result(result: Any) -> Mapping[str, Any]:
    if not isinstance(result, Mapping):
        raise Text2GameAdapterError("dependency result is not an object")
    if result.get("executor") == "agent":
        response = result.get("response")
        content = response.get("content") if isinstance(response, Mapping) else None
    elif result.get("executor") == "adapter":
        receipt = result.get("receipt")
        content = receipt.get("payload") if isinstance(receipt, Mapping) else None
    else:
        content = result.get("content")
    if not isinstance(content, Mapping):
        raise Text2GameAdapterError("dependency result content is not an object")
    return content


def _dependency_content(payload: Mapping[str, Any], action: str) -> Mapping[str, Any]:
    dependencies = payload.get("dependencies")
    dependency = dependencies.get(action) if isinstance(dependencies, Mapping) else None
    result = dependency.get("result") if isinstance(dependency, Mapping) else None
    return _unwrap_result(result)


def _accepted_content(payload: Mapping[str, Any], action: str) -> Mapping[str, Any]:
    artifacts = payload.get("accepted_artifacts")
    if not isinstance(artifacts, list):
        raise Text2GameAdapterError("accepted_artifacts must be an array")
    matches = [
        item.get("content")
        for item in artifacts
        if isinstance(item, Mapping) and item.get("action") == action
    ]
    if len(matches) != 1 or not isinstance(matches[0], Mapping):
        raise Text2GameAdapterError(f"accepted artifact {action} is not unique")
    return matches[0]


def _accepted_rules_from_identity_state(state: Mapping[str, Any]) -> Mapping[str, Any]:
    rules = state.get("rules")
    if not isinstance(rules, Mapping) or set(rules) != set(_RULE_FIELDS):
        raise Text2GameAdapterError("text2game durable rules are missing")
    return rules


def _snapshot_output(root: Path) -> dict[str, str]:
    if root.is_symlink() or not root.is_dir():
        raise Text2GameAdapterError("text2game output directory is unavailable")
    result: dict[str, str] = {}
    total = 0
    for path in sorted(root.rglob("*")):
        metadata = path.lstat()
        if stat.S_ISDIR(metadata.st_mode):
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise Text2GameAdapterError("text2game output contains a non-regular entry")
        relative = path.relative_to(root).as_posix()
        if _credential_like_path(relative):
            raise Text2GameAdapterError("text2game output contains a credential-like file")
        total += int(metadata.st_size)
        if len(result) >= _MAX_OUTPUT_FILES or total > _MAX_OUTPUT_BYTES:
            raise Text2GameAdapterError("text2game output exceeds resource limits")
        result[relative] = _sha256_file(path)
    if not result:
        raise Text2GameAdapterError("text2game output is empty")
    return result


def _validate_phase_command(command: Sequence[str], repository: Path) -> None:
    if "--force" in command or "all" in command or any(
        "run_full" in value for value in command
    ):
        raise Text2GameAdapterError("unsafe text2game phase command")
    if len(command) not in {6, 8}:
        raise Text2GameAdapterError("text2game phase command shape is invalid")
    if Path(command[1]) != repository / "text2game":
        raise Text2GameAdapterError("text2game must run from the operation copy")
    if command[2:6:2] != ["--slug", "--phase"]:
        raise Text2GameAdapterError("text2game phase arguments are malformed")
    if command[5] not in {"1", "2", "3"}:
        raise Text2GameAdapterError("text2game phase must be separate")
    if command[5] == "1" and command[6:] != ["--max-rounds", "1"]:
        raise Text2GameAdapterError("text2game phase 1 must run one immutable round")


__all__ = [
    "AmbiguousText2GameEffect",
    "CAD_RECEIPT_VERSION",
    "DFM_RECEIPT_VERSION",
    "DIAGNOSTICS_CONTRACT_VERSION",
    "Text2GameAdapterError",
    "Text2GamePhysicalAdapter",
]
