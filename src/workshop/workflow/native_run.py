"""Trusted host for one native coding-agent session per Wish.

This module deliberately contains no Match, Invent, Make, or Playtest
reasoning.  It creates the private filesystem protocol, binds a native Codex
session to those exact bytes, and exposes a redacted status view.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Optional, Sequence

try:
    import fcntl
except ImportError:  # pragma: no cover - Codex CLI hosts are currently POSIX
    fcntl = None  # type: ignore[assignment]

from workshop.errors import (
    AmbiguousEffectError,
    ArtifactError,
    ContractError,
    StateConflict,
    TransitionError,
    WorkshopError,
)
from workshop.contributors import (
    parse_taste_bytes,
)
from workshop.integrations.factory import (
    FACTORY_CONTENT_MAPPING,
    FactoryReleaseWriter,
    FactoryAgentSession,
    FactoryAuthenticationError,
    FactoryCredentialRejected,
    FactoryPublicTransition,
    factory_credentials_from_environment,
    urllib_project_file_transport,
    urllib_transport,
)
from workshop.integrations.git import (
    GitPushError,
    push_toy_directory,
)
from workshop.invent.native import NativeInvented
from workshop.make.native import NativeMade
from workshop.make.revision import (
    MAKE_INVENT_REVISION_CAPABILITY_PATH,
    NativeMakeInventRevision,
)
from workshop.make.native_gate import (
    NATIVE_CAD_FULL_TIER,
    NATIVE_CAD_GATE_KIND,
    NATIVE_CAD_VERIFIER_MODE,
    NATIVE_CAD_VERIFIER_PATH,
    NativeCadGateError,
    NativeMadeTreeGateError,
    verify_native_made_cad,
)
from workshop.match.native import (
    NativeMatchAssignment,
    InventorRoster,
    InventorRosterEntry,
)
from workshop.playtest.native import NativePlaytested
from workshop.product import ToyBlueprint
from workshop.release.contracts import ProductRelease, ReleaseContext
from workshop.release.manual_design import (
    MANUAL_DESIGN_EVIDENCE_PATH,
    validate_bound_manual_design_evidence,
)
from workshop.release.native import (
    DIRECT_RELEASE_PLAYTEST_STATUS,
    DIRECT_RELEASE_PRODUCT_SCHEMA_VERSION,
    NATIVE_RELEASE_LEGACY_MANUAL_PATH,
    NATIVE_RELEASE_MANUAL_PATH,
    NATIVE_RELEASE_PLAYTEST_OMISSION_PATH,
    NativeRelease,
    NativeReleasePackage,
)
from workshop.release.verification import try_materialize_digital_verification
from workshop.release.public_example import (
    materialize_public_example_if_source_checkout,
)
from workshop.runtime import (
    CodexInvocationError,
    CodexRecoverableInvocationError,
    CodexNativeSessionLauncher,
    CodexNativeSessionOutcome,
    DEFAULT_MANAGER_ID,
    EffectLedger,
    NativeManagerInvocationError,
    NativeManagerRecoverableError,
    Receipt,
    factory_credential_environment,
    factory_service_credential_environment,
    manager_launcher,
    manager_spec,
)
from workshop.runtime.managers import NativeSessionLauncher
from workshop.runtime.agent_assets import (
    parse_inventor_custom_agent_bytes,
    product_run_agent_assets,
)
from workshop.runtime.package_data import (
    default_workshop_home,
    packaged_inventors_root,
    product_run_domain_skill_roots,
)
from workshop.runtime.progress import (
    NATIVE_PROGRESS_FILENAME,
    SAFE_NATIVE_ACTIVITY_CLASSES,
    NativeRunProgress,
    WishRunTimingObserver,
    begin_native_progress,
    native_progress_turn_floor,
    trusted_native_progress,
    wish_run_timing_span,
    write_native_progress,
)
from workshop.wish import Wish
from workshop.workflow.agent_run import (
    AgentArtifact,
    AgentOutcome,
    AgentRun,
    AgentRunCheckpoint,
    DeterministicGateReceipt,
)
from workshop.workflow.effort import (
    DEEP_AUTO_COMPACT_TOKEN_LIMIT,
    DEEP_ECONOMICS_CAPABILITY_PATH,
    DEEP_ECONOMICS_V1_CAPABILITY_PATH,
    DEEP_ECONOMICS_V2_CAPABILITY_PATH,
    DEEP_ECONOMICS_V3_CAPABILITY_PATH,
    DEEP_ECONOMICS_V4_CAPABILITY_PATH,
    DEEP_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS,
    DEEP_MAKE_AUTO_COMPACT_TOKEN_LIMIT,
    DEEP_NATIVE_TURN_LIMIT,
    DEEP_NATIVE_TURN_TIMEOUT_SECONDS,
    DEEP_V1_AUTO_COMPACT_TOKEN_LIMIT,
    DEEP_V1_NATIVE_TURN_LIMIT,
    DEEP_V5_INITIAL_INVENT_TIMEOUT_SECONDS,
    DEEP_V5_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS,
    DEEP_V5_INVENT_RECOVERY_TIMEOUT_SECONDS,
    EFFORT_ROUTE_CAPABILITY_PATH,
    SPARK_AUTO_COMPACT_TOKEN_LIMIT,
    SPARK_ECONOMICS_CAPABILITY_PATH,
    SPARK_ECONOMICS_V1_CAPABILITY_PATH,
    SPARK_ECONOMICS_V2_CAPABILITY_PATH,
    SPARK_NATIVE_TURN_TIMEOUT_SECONDS,
    workshop_effort,
)
from workshop.workflow.proposals import (
    AgentOutcomeProposal,
    read_agent_outcome_proposal,
    read_bounded_json_artifact,
)
from workshop.workflow.stage_gates import (
    StageGateDecision,
    StageGateEvidence,
    evaluate_invent_stage,
    evaluate_match_stage,
    evaluate_routed_invent_stage,
    invent_gate_subject_sha256,
    match_gate_subject_sha256,
)


_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_INSTRUCTION_HASH_DOMAIN = b"autonomous-workshop/product-run-instructions/v1\0"
_STAGE_INPUT_NAME = "STAGE.json"
_AGENT_OUTCOME_NAME = "agent-outcome.json"
_AUTHORIZATION_NAME = "authorization.json"
_RELEASE_EFFECT_WAIT_NAME = "release-effect-wait.json"
_PUBLIC_EXAMPLE_STATUS_NAME = "public-example.json"
_NATIVE_TOKEN_USAGE_NAME = "native-token-usage.json"
_NATIVE_TOKEN_USAGE_KIND = "autonomous-workshop.native-token-usage"
_NATIVE_TOKEN_SUMMARY_KIND = "autonomous-workshop.native-token-summary"
_NATIVE_TOKEN_STAGES = ("match", "invent", "make", "playtest", "release")
_CAD_GATE_REJECTIONS_DIRECTORY = "cad-gate-rejections"
_CAD_GATE_REJECTION_KIND = "autonomous-workshop.cad-gate-rejection"
_MAKE_PROPOSAL_REJECTIONS_DIRECTORY = "make-proposal-rejections"
_MAKE_PROPOSAL_REJECTION_KIND = "autonomous-workshop.make-proposal-rejection"
_MAKE_PROPOSAL_REJECTION_HEAD_KIND = (
    "autonomous-workshop.make-proposal-rejection-head"
)
_PLAYTEST_PROPOSAL_REJECTIONS_DIRECTORY = "playtest-proposal-rejections"
_PLAYTEST_PROPOSAL_REJECTION_KIND = (
    "autonomous-workshop.playtest-proposal-rejection"
)
_PLAYTEST_PROPOSAL_REJECTION_HEAD_KIND = (
    "autonomous-workshop.playtest-proposal-rejection-head"
)
_STAGE_INPUT_KIND = "autonomous-workshop.stage-input"
_MAKE_PROOF_READY_NAME = ".make-proof-ready.json"
_AUTHORIZATION_KIND = "autonomous-workshop.run-authorization"
_SUBJECT_KIND = "autonomous-workshop.stage-gate-subject"
_MAX_STAGE_INPUT_BYTES = 512 * 1024
_MAX_CAD_GATE_REJECTION_BYTES = 64 * 1024
_MAX_CAD_GATE_DIAGNOSTIC_JSON_BYTES = 8 * 1024
_MAX_MAKE_PROPOSAL_REJECTION_BYTES = 256 * 1024
_MAX_MAKE_PROPOSAL_REJECTION_FEEDBACK_CHARS = 2_000
_MAX_MAKE_PROPOSAL_REJECTIONS = 32
_MAX_PLAYTEST_PROPOSAL_REJECTION_BYTES = 256 * 1024
_MAX_PLAYTEST_PROPOSAL_REJECTIONS = 32
_MAX_LEGACY_CAD_GATE_EVIDENCE_BYTES = 3 * 1024 * 1024
_MAX_NATIVE_TURNS = 32
_MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS = 3
_MAX_CONSECUTIVE_RECOVERABLE_NATIVE_TURNS = 2
_RECOVERABLE_BACKOFF_BASE_SECONDS = 1.0
_RECOVERABLE_BACKOFF_MAX_SECONDS = 30.0
_RECOVERABLE_BACKOFF_JITTER_MIN = 0.75
_RECOVERABLE_BACKOFF_JITTER_SPAN = 0.5
_FACTORY_CREDENTIALS_NEED = (
    "Factory credentials for Workshop's service account are missing or malformed; "
    "configure FACTORY_USERNAME and FACTORY_PASSWORD, then resume this run."
)
_FACTORY_PUBLICATION_NEED = (
    "Factory publication could not be verified; restore server connectivity, "
    "then resume this run. Workshop will perform authenticated reconciliation "
    "of the existing effect before any retry."
)
_LEGACY_RELEASE_UPGRADE_NEED = (
    "This historical run has an obsolete Release contract. It remains readable, "
    "but it cannot complete today's Workshop until it has a validated MANUAL.pdf "
    "and full-tier, thickness-checked, print-ready CAD evidence."
)
_PRODUCT_RUN_FINALIZER_INPUT = (
    ".agents/skills/autonomous-workshop/scripts/stage_proposal.py"
)
_PRODUCT_RUN_PDF_VALIDATOR_INPUT = (
    ".agents/skills/autonomous-workshop/scripts/pdf_validator.py"
)
_PRODUCT_RUN_MANUAL_DESIGN_EVIDENCE_INPUT = (
    ".agents/skills/autonomous-workshop/references/manual-design-evidence-v1.md"
)
_PRODUCT_RUN_TERMINAL_RELEASE_INPUT = (
    ".agents/skills/autonomous-workshop/references/release-terminal-v1.md"
)
_PRODUCT_RUN_DIRECT_RELEASE_INPUT = (
    ".agents/skills/autonomous-workshop/references/direct-release-v1.md"
)
_PRODUCT_RUN_EFFORT_ROUTES_INPUT = EFFORT_ROUTE_CAPABILITY_PATH
_MAKE_PROPOSAL_REJECTION_FEEDBACK = {
    "make-product-metadata-invalid": (
        "The host rejected product.json metadata. Add both title and summary "
        "as non-empty text values of at most 2000 characters, then rerun "
        "the Make finalizer so made.json, its manifest, and agent-outcome.json "
        "are regenerated from the repaired bytes."
    ),
    "make-artifact-invalid": (
        "The host could not safely identify the exact Make artifact tree. "
        "Repair the product files and rerun the Make finalizer so every "
        "artifact binding and hash is regenerated from the current bytes."
    ),
    "make-contract-invalid": (
        "The host rejected the agent-authored Make contract. Repair the Make "
        "product and rerun the Make finalizer so made.json and agent-outcome.json "
        "are regenerated from one internally consistent artifact tree."
    ),
}
_PLAYTEST_PROPOSAL_REJECTION_FEEDBACK = {
    "playtest-artifact-invalid": (
        "The host could not safely reopen the exact Playtest evidence sealed by "
        "the finalizer. Replace missing, linked, special, or subsequently changed "
        "evidence with stable regular files, then rerun the Playtest finalizer. "
        "After it succeeds, return control immediately without changing evidence."
    ),
    "playtest-contract-invalid": (
        "The host rejected the agent-authored Playtest contract or its binding to "
        "the current Made revision. Repair the configs, evidence, or authored "
        "source, rerun the Playtest finalizer, and return control immediately."
    ),
}

# These are the only deterministic-test seams in the required publication
# path.  Tests may replace outbound HTTP while retaining the production
# Factory session, handoff writer, effect ledger, reconciliation, publication,
# public readback, and receipt validation code.
_FACTORY_TRANSPORT = urllib_transport
_FACTORY_PROJECT_FILE_TRANSPORT = urllib_project_file_transport


def _factory_transport_overrides() -> dict[str, Any]:
    """Return only explicitly replaced outbound Factory transports."""

    overrides: dict[str, Any] = {}
    if _FACTORY_TRANSPORT is not urllib_transport:
        overrides["transport"] = _FACTORY_TRANSPORT
    if _FACTORY_PROJECT_FILE_TRANSPORT is not urllib_project_file_transport:
        overrides["project_file_transport"] = _FACTORY_PROJECT_FILE_TRANSPORT
    return overrides


class _FactoryCredentialsUnavailable(Exception):
    """Signal that required publication cannot begin without host credentials."""

    def __init__(self, inventor_id: str) -> None:
        self.inventor_id = inventor_id
        super().__init__(_FACTORY_CREDENTIALS_NEED)


class _RequiredPublicationUnavailable(Exception):
    """Required publication is unverified and must remain resumable at Release."""


class _LegacyReleaseUpgradeRequired(Exception):
    """A frozen historical proposal cannot satisfy today's terminal Release."""


@dataclass(frozen=True)
class _VerifiedRelease:
    """Exact local Release bytes plus the context needed by its public effect."""

    release: NativeRelease
    package: NativeReleasePackage
    product_release: ProductRelease
    made: NativeMade
    inventor_id: str
    assignment: NativeMatchAssignment
    blueprint: ToyBlueprint
    inventor_binding: Any


class _RecoverableNativeTurn(WorkshopError):
    """Internal typed signal for a checkpoint-bound turn continuation."""


class _MakeProposalRejected(Exception):
    """A valid Make envelope whose agent-authored candidate failed its contract."""

    def __init__(self, failure_code: str, feedback: str) -> None:
        self.failure_code = failure_code
        self.feedback = feedback
        super().__init__(failure_code)


class _PlaytestProposalRejected(Exception):
    """A valid Playtest envelope whose untrusted candidate failed its contract."""

    def __init__(self, failure_code: str, feedback: str) -> None:
        self.failure_code = failure_code
        self.feedback = feedback
        super().__init__(failure_code)


@dataclass(frozen=True)
class NativeRunPaths:
    """Private sibling roots for agent-visible work and host-only state."""

    workspace: Path
    host_state: Path


class _NativeProgressTracker:
    """Best-effort writer for bounded host-selected progress classes."""

    def __init__(
        self,
        path: Path,
        progress: Optional[NativeRunProgress],
    ) -> None:
        self.path = path
        self.progress = progress
        self._last_write = time.monotonic()

    @classmethod
    def begin(
        cls,
        paths: NativeRunPaths,
        checkpoint: AgentRunCheckpoint,
    ) -> "_NativeProgressTracker":
        path = paths.host_state / NATIVE_PROGRESS_FILENAME
        previous = trusted_native_progress(
            path,
            product_id=checkpoint.product_id,
            wish_sha256=checkpoint.wish_sha256,
            checkpoint_sha256=checkpoint.checkpoint_sha256,
            checkpoint_stage=checkpoint.stage,
        )
        try:
            progress = begin_native_progress(
                previous,
                product_id=checkpoint.product_id,
                wish_sha256=checkpoint.wish_sha256,
                checkpoint_sha256=checkpoint.checkpoint_sha256,
                checkpoint_stage=checkpoint.stage,
                native_turn_floor=native_progress_turn_floor(path),
            )
            if not write_native_progress(
                path,
                progress,
                establish_generation=True,
            ):
                progress = None
        except (OSError, WorkshopError):
            progress = None
        return cls(path, progress)

    @classmethod
    def existing(
        cls,
        paths: NativeRunPaths,
        checkpoint: AgentRunCheckpoint,
    ) -> "_NativeProgressTracker":
        path = paths.host_state / NATIVE_PROGRESS_FILENAME
        return cls(
            path,
            trusted_native_progress(
                path,
                product_id=checkpoint.product_id,
                wish_sha256=checkpoint.wish_sha256,
                checkpoint_sha256=checkpoint.checkpoint_sha256,
                checkpoint_stage=checkpoint.stage,
            ),
        )

    def observe(self, activity: str) -> None:
        progress = self.progress
        if progress is None:
            return
        now = time.monotonic()
        if (
            activity not in ("finalizing", "completed", "failed")
            and now - self._last_write < 1.0
        ):
            return
        try:
            progress = progress.observe(activity)
            if not write_native_progress(self.path, progress):
                self.progress = None
                return
        except (OSError, WorkshopError):
            self.progress = None
            return
        self.progress = progress
        self._last_write = now

    def rebind(
        self,
        checkpoint: AgentRunCheckpoint,
        *,
        activity: Optional[str] = None,
    ) -> None:
        progress = self.progress
        if progress is None:
            return
        if (
            progress.product_id != checkpoint.product_id
            or progress.wish_sha256 != checkpoint.wish_sha256
        ):
            self.progress = None
            return
        try:
            progress = progress.rebind(
                checkpoint_sha256=checkpoint.checkpoint_sha256,
                checkpoint_stage=checkpoint.stage,
                activity=activity,
            )
            if not write_native_progress(self.path, progress):
                self.progress = None
                return
        except (OSError, WorkshopError):
            self.progress = None
            return
        self.progress = progress
        self._last_write = time.monotonic()


@contextmanager
def _native_run_mutation_lock(paths: NativeRunPaths):
    """Fail closed when another host process is mutating this Wish.

    The kernel releases the advisory lock if its owner exits or crashes, so a
    stale lock file never grants or blocks authority by itself.
    """

    if fcntl is None:
        raise StateConflict("native run mutation locking is unavailable")
    lock_path = paths.host_state / "mutation.lock"
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(lock_path), flags, 0o600)
    except OSError as exc:
        raise StateConflict("native run mutation lock is unavailable") from exc
    try:
        identity = os.fstat(descriptor)
        if not stat.S_ISREG(identity.st_mode):
            raise StateConflict("native run mutation lock must be a regular file")
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise StateConflict(
                "another Workshop process is already mutating this Wish"
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def canonical_wish_bytes(wish: Wish) -> bytes:
    """Return the one JSON encoding accepted by :class:`AgentRun`."""

    if not isinstance(wish, Wish):
        raise ContractError("native run requires a validated Wish")
    try:
        return json.dumps(
            wish.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Wish cannot be encoded for a native run") from exc


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("native host values must be finite JSON") from exc


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _strict_json_bytes(content: bytes, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            content.decode("utf-8"), object_pairs_hook=_strict_object
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ContractError("%s must contain strict UTF-8 JSON" % label) from exc
    if not isinstance(value, dict):
        raise ContractError("%s must contain one JSON object" % label)
    return value


def _atomic_private_write(path: Path, content: bytes, *, mode: int = 0o600) -> None:
    if mode not in (0o400, 0o600):
        raise ContractError("private file mode is invalid")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % path.name,
        suffix=".tmp",
        dir=str(path.parent),
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        written = 0
        while written < len(content):
            written += os.write(descriptor, content[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, path)
        os.chmod(path, mode)
        directory = os.open(
            str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
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


def _write_private_json(path: Path, value: Mapping[str, Any], *, mode: int = 0o600) -> str:
    content = _canonical_json_bytes(dict(value)) + b"\n"
    _atomic_private_write(path, content, mode=mode)
    return _sha256(content)


def _cad_gate_rejection_path(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    *,
    create_parent: bool = False,
) -> Path:
    if checkpoint.stage not in ("make", "playtest", "release"):
        raise TransitionError("CAD gate rejection requires Make, Playtest, or Release")
    parent = run.host_state_root / _CAD_GATE_REJECTIONS_DIRECTORY
    try:
        identity = parent.lstat()
    except FileNotFoundError:
        if not create_parent:
            return parent / (checkpoint.checkpoint_sha256 + ".json")
        try:
            parent.mkdir(mode=0o700)
            identity = parent.lstat()
        except OSError as exc:
            raise StateConflict("CAD gate rejection directory is unavailable") from exc
    except OSError as exc:
        raise StateConflict("CAD gate rejection directory is unavailable") from exc
    if (
        parent.is_symlink()
        or not stat.S_ISDIR(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o700
    ):
        raise StateConflict("CAD gate rejection directory must be private")
    return parent / (checkpoint.checkpoint_sha256 + ".json")


def _bounded_json_text_tail(text: str, maximum_bytes: int) -> tuple[str, bool]:
    """Keep the longest suffix whose standalone JSON encoding is bounded."""

    if len(_canonical_json_bytes(text)) <= maximum_bytes:
        return text, False
    lower = 0
    upper = len(text)
    while lower < upper:
        candidate_length = (lower + upper + 1) // 2
        candidate = text[-candidate_length:]
        if len(_canonical_json_bytes(candidate)) <= maximum_bytes:
            lower = candidate_length
        else:
            upper = candidate_length - 1
    return (text[-lower:] if lower else ""), True


def _cad_gate_stream_summary(stream: Any) -> dict[str, Any]:
    value = stream.to_dict()
    text = value.get("captured_text")
    if not isinstance(text, str):
        raise StateConflict("CAD gate diagnostic stream is invalid")
    tail, clipped = _bounded_json_text_tail(
        text, _MAX_CAD_GATE_DIAGNOSTIC_JSON_BYTES
    )
    return {
        "captured_text_tail": tail,
        "captured_bytes": value.get("captured_bytes"),
        "total_bytes": value.get("total_bytes"),
        "sha256": value.get("sha256"),
        "truncated": bool(value.get("truncated")) or clipped,
    }


def _validate_cad_gate_stream_summary(value: Any, label: str) -> dict[str, Any]:
    expected = {
        "captured_text_tail",
        "captured_bytes",
        "total_bytes",
        "sha256",
        "truncated",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise StateConflict("%s is invalid" % label)
    text = value["captured_text_tail"]
    captured = value["captured_bytes"]
    total = value["total_bytes"]
    if (
        not isinstance(text, str)
        or len(_canonical_json_bytes(text))
        > _MAX_CAD_GATE_DIAGNOSTIC_JSON_BYTES
        or type(captured) is not int
        or type(total) is not int
        or captured < 0
        or total < captured
        or not isinstance(value["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is None
        or type(value["truncated"]) is not bool
    ):
        raise StateConflict("%s is invalid" % label)
    return dict(value)


def _assert_persisted_cad_gate_evidence(
    run: AgentRun, rejection: NativeCadGateError
) -> None:
    path = Path(rejection.evidence_path)
    try:
        path.relative_to(run.host_state_root)
        before = path.lstat()
    except (OSError, ValueError) as exc:
        raise StateConflict("CAD gate rejection evidence is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(before.st_mode)
        or stat.S_IMODE(before.st_mode) != 0o600
        or not 1 <= before.st_size <= 3 * 1024 * 1024
    ):
        raise StateConflict("CAD gate rejection evidence is not a private file")
    try:
        content = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise StateConflict("CAD gate rejection evidence is unavailable") from exc
    expected = _canonical_json_bytes(rejection.evidence.to_dict()) + b"\n"
    if (
        content != expected
        or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
    ):
        raise StateConflict("CAD gate rejection evidence changed or is invalid")


def _persist_cad_gate_rejection(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    proposal: AgentOutcomeProposal,
    rejection: NativeCadGateError,
) -> Mapping[str, Any]:
    if checkpoint.stage not in ("make", "playtest", "release"):
        raise TransitionError("CAD gate rejection belongs to another stage")
    evidence = rejection.evidence
    if evidence.passed or evidence.failure_code != rejection.failure_code:
        raise StateConflict("CAD gate rejection evidence disagrees with its failure")
    _assert_persisted_cad_gate_evidence(run, rejection)
    identity: dict[str, Any] = {
        "schema_version": 1,
        "kind": _CAD_GATE_REJECTION_KIND,
        "product_id": checkpoint.product_id,
        "stage": checkpoint.stage,
        "round": checkpoint.round_index,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "subject_sha256": proposal.subject_sha256,
        "rejected_outcome_sha256": proposal.outcome.sha256,
        "failure_code": rejection.failure_code,
        "cad_gate_receipt_sha256": evidence.receipt_sha256,
        "made_sha256": evidence.made_sha256,
        "product_artifact_sha256": evidence.product_artifact_sha256,
        "cad_project_path": evidence.cad_project_path,
        "cad_project_sha256": evidence.cad_project_sha256,
        "verifier_path": evidence.verifier_path,
        "verifier_sha256": evidence.verifier_sha256,
        "verifier_mode": evidence.verifier_mode,
        "command": list(evidence.command),
        "returncode": evidence.returncode,
        "duration_ms": evidence.duration_ms,
        "timed_out": evidence.timed_out,
        "source_tree_unchanged": evidence.source_tree_unchanged,
        "stdout": _cad_gate_stream_summary(evidence.stdout),
        "stderr": _cad_gate_stream_summary(evidence.stderr),
    }
    record = {
        **identity,
        "rejection_sha256": _sha256(_canonical_json_bytes(identity)),
    }
    encoded = _canonical_json_bytes(record) + b"\n"
    if len(encoded) > _MAX_CAD_GATE_REJECTION_BYTES:
        raise StateConflict("CAD gate rejection exceeded its safe size limit")
    path = _cad_gate_rejection_path(run, checkpoint, create_parent=True)
    _atomic_private_write(path, encoded)
    return record


def _read_cad_gate_rejection(
    run: AgentRun, checkpoint: AgentRunCheckpoint
) -> Optional[Mapping[str, Any]]:
    if checkpoint.stage not in ("make", "playtest", "release"):
        return None
    path = _cad_gate_rejection_path(run, checkpoint)
    if not path.exists() and not path.is_symlink():
        return None
    try:
        before = path.lstat()
        content = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise StateConflict("CAD gate rejection is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(before.st_mode)
        or stat.S_IMODE(before.st_mode) != 0o600
        or not 1 <= len(content) <= _MAX_CAD_GATE_REJECTION_BYTES
        or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
    ):
        raise StateConflict("CAD gate rejection is not a stable private file")
    try:
        record = _strict_json_bytes(content, label="CAD gate rejection")
    except ContractError as exc:
        raise StateConflict("CAD gate rejection is invalid") from exc
    expected = {
        "schema_version",
        "kind",
        "product_id",
        "stage",
        "round",
        "checkpoint_sha256",
        "subject_sha256",
        "rejected_outcome_sha256",
        "failure_code",
        "cad_gate_receipt_sha256",
        "made_sha256",
        "product_artifact_sha256",
        "cad_project_path",
        "cad_project_sha256",
        "verifier_path",
        "verifier_sha256",
        "verifier_mode",
        "command",
        "returncode",
        "duration_ms",
        "timed_out",
        "source_tree_unchanged",
        "stdout",
        "stderr",
        "rejection_sha256",
    }
    digest_fields = (
        "checkpoint_sha256",
        "subject_sha256",
        "rejected_outcome_sha256",
        "cad_gate_receipt_sha256",
        "made_sha256",
        "product_artifact_sha256",
        "cad_project_sha256",
        "verifier_sha256",
        "rejection_sha256",
    )
    command = record.get("command")
    if (
        set(record) != expected
        or record.get("schema_version") != 1
        or record.get("kind") != _CAD_GATE_REJECTION_KIND
        or record.get("product_id") != checkpoint.product_id
        or record.get("stage") != checkpoint.stage
        or record.get("round") != checkpoint.round_index
        or record.get("checkpoint_sha256") != checkpoint.checkpoint_sha256
        or not isinstance(record.get("failure_code"), str)
        or not 1 <= len(record["failure_code"]) <= 64
        or not isinstance(record.get("cad_project_path"), str)
        or not isinstance(record.get("verifier_path"), str)
        or not isinstance(record.get("verifier_mode"), str)
        or not isinstance(command, list)
        or not command
        or len(command) > 32
        or any(not isinstance(item, str) or not item or len(item) > 1_024 for item in command)
        or type(record.get("returncode")) is not int
        or type(record.get("duration_ms")) is not int
        or record["duration_ms"] < 0
        or type(record.get("timed_out")) is not bool
        or type(record.get("source_tree_unchanged")) is not bool
        or any(
            not isinstance(record.get(name), str)
            or re.fullmatch(r"[0-9a-f]{64}", record[name]) is None
            for name in digest_fields
        )
    ):
        raise StateConflict("CAD gate rejection is invalid")
    _validate_cad_gate_stream_summary(record["stdout"], "CAD gate stdout summary")
    _validate_cad_gate_stream_summary(record["stderr"], "CAD gate stderr summary")
    identity = {key: record[key] for key in expected - {"rejection_sha256"}}
    if record["rejection_sha256"] != _sha256(_canonical_json_bytes(identity)):
        raise StateConflict("CAD gate rejection hash is invalid")
    return record


def _make_proposal_rejection_directory(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    *,
    create: bool = False,
) -> Path:
    if checkpoint.stage != "make":
        raise TransitionError("Make proposal rejection belongs to another stage")
    current = run.host_state_root
    parts = (
        _MAKE_PROPOSAL_REJECTIONS_DIRECTORY,
        checkpoint.checkpoint_sha256,
    )
    for index, part in enumerate(parts):
        candidate = current / part
        try:
            identity = candidate.lstat()
        except FileNotFoundError:
            if not create:
                return current.joinpath(*parts[index:])
            try:
                candidate.mkdir(mode=0o700)
                identity = candidate.lstat()
            except OSError as exc:
                raise StateConflict(
                    "Make proposal rejection directory is unavailable"
                ) from exc
        except OSError as exc:
            raise StateConflict(
                "Make proposal rejection directory is unavailable"
            ) from exc
        if (
            stat.S_ISLNK(identity.st_mode)
            or not stat.S_ISDIR(identity.st_mode)
            or stat.S_IMODE(identity.st_mode) != 0o700
        ):
            raise StateConflict("Make proposal rejection directory must be private")
        current = candidate
    return current


def _read_stable_private_bytes(
    path: Path, *, label: str, maximum_bytes: int
) -> bytes:
    try:
        before = path.lstat()
        content = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if (
        stat.S_ISLNK(before.st_mode)
        or not stat.S_ISREG(before.st_mode)
        or stat.S_IMODE(before.st_mode) != 0o600
        or not 1 <= len(content) <= maximum_bytes
        or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
    ):
        raise StateConflict("%s is not a stable private file" % label)
    return content


def _make_proposal_rejection_record_path(
    directory: Path, rejection_sha256: str
) -> Path:
    if re.fullmatch(r"[0-9a-f]{64}", rejection_sha256) is None:
        raise StateConflict("Make proposal rejection identity is invalid")
    return directory / ("rejection-%s.json" % rejection_sha256)


def _make_proposal_quarantine_path(
    directory: Path, proposal_file_sha256: str
) -> Path:
    if re.fullmatch(r"[0-9a-f]{64}", proposal_file_sha256) is None:
        raise StateConflict("quarantined Make proposal identity is invalid")
    return directory / ("outcome-%s.json" % proposal_file_sha256)


def _validate_make_proposal_rejection_record(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    record: Mapping[str, Any],
    *,
    directory: Path,
    seen: frozenset[str] = frozenset(),
) -> Mapping[str, Any]:
    expected = {
        "schema_version",
        "kind",
        "product_id",
        "stage",
        "round",
        "rejection_number",
        "checkpoint_sha256",
        "subject_sha256",
        "previous_rejection_sha256",
        "rejected_proposal_sha256",
        "rejected_proposal_file_sha256",
        "rejected_outcome_sha256",
        "rejected_artifacts",
        "failure_code",
        "feedback",
        "rejection_sha256",
    }
    digest_fields = (
        "checkpoint_sha256",
        "subject_sha256",
        "rejected_proposal_sha256",
        "rejected_proposal_file_sha256",
        "rejected_outcome_sha256",
        "rejection_sha256",
    )
    previous = record.get("previous_rejection_sha256")
    feedback = record.get("feedback")
    artifacts = record.get("rejected_artifacts")
    rejection_number = record.get("rejection_number")
    rejection_sha256 = record.get("rejection_sha256")
    failure_code = record.get("failure_code")
    if (
        set(record) != expected
        or record.get("schema_version") != 1
        or record.get("kind") != _MAKE_PROPOSAL_REJECTION_KIND
        or record.get("product_id") != checkpoint.product_id
        or record.get("stage") != "make"
        or record.get("round") != checkpoint.round_index
        or type(rejection_number) is not int
        or not 1 <= rejection_number <= _MAX_MAKE_PROPOSAL_REJECTIONS
        or record.get("checkpoint_sha256") != checkpoint.checkpoint_sha256
        or (
            previous is not None
            and (
                not isinstance(previous, str)
                or re.fullmatch(r"[0-9a-f]{64}", previous) is None
            )
        )
        or any(
            not isinstance(record.get(name), str)
            or re.fullmatch(r"[0-9a-f]{64}", record[name]) is None
            for name in digest_fields
        )
        or failure_code not in _MAKE_PROPOSAL_REJECTION_FEEDBACK
        or not isinstance(feedback, str)
        or not feedback.strip()
        or len(feedback) > _MAX_MAKE_PROPOSAL_REJECTION_FEEDBACK_CHARS
        or any(ord(character) < 32 or ord(character) == 127 for character in feedback)
        or feedback != _MAKE_PROPOSAL_REJECTION_FEEDBACK.get(failure_code)
        or not isinstance(artifacts, list)
    ):
        raise StateConflict("Make proposal rejection is invalid")
    try:
        artifact_values = tuple(
            AgentArtifact.from_mapping(value) for value in artifacts
        )
    except ContractError as exc:
        raise StateConflict("Make proposal rejection artifacts are invalid") from exc
    if [artifact.to_dict() for artifact in artifact_values] != artifacts:
        raise StateConflict("Make proposal rejection artifacts are not canonical")
    identity = {key: record[key] for key in expected - {"rejection_sha256"}}
    if rejection_sha256 != _sha256(_canonical_json_bytes(identity)):
        raise StateConflict("Make proposal rejection hash is invalid")
    if rejection_sha256 in seen:
        raise StateConflict("Make proposal rejection chain contains a cycle")

    quarantine_path = _make_proposal_quarantine_path(
        directory, record["rejected_proposal_file_sha256"]
    )
    quarantine = _read_stable_private_bytes(
        quarantine_path,
        label="quarantined Make proposal",
        maximum_bytes=_MAX_MAKE_PROPOSAL_REJECTION_BYTES,
    )
    if _sha256(quarantine) != record["rejected_proposal_file_sha256"]:
        raise StateConflict("quarantined Make proposal hash is invalid")
    try:
        document = _strict_json_bytes(quarantine, label="quarantined Make proposal")
        proposal = AgentOutcomeProposal.from_mapping(document)
    except ContractError as exc:
        raise StateConflict("quarantined Make proposal is invalid") from exc
    if (
        proposal.checkpoint_sha256 != checkpoint.checkpoint_sha256
        or proposal.subject_sha256 != record["subject_sha256"]
        or proposal.outcome.stage != "make"
        or proposal.outcome.status != "ready"
        or proposal.outcome.proposed_transition != "playtest"
        or proposal.sha256 != record["rejected_proposal_sha256"]
        or proposal.outcome.sha256 != record["rejected_outcome_sha256"]
        or [artifact.to_dict() for artifact in proposal.outcome.artifacts]
        != artifacts
    ):
        raise StateConflict("quarantined Make proposal disagrees with its rejection")

    if previous is None:
        if rejection_number != 1:
            raise StateConflict("Make proposal rejection predecessor is invalid")
    else:
        if rejection_number <= 1:
            raise StateConflict("Make proposal rejection predecessor is invalid")
        previous_content = _read_stable_private_bytes(
            _make_proposal_rejection_record_path(directory, previous),
            label="prior Make proposal rejection",
            maximum_bytes=_MAX_MAKE_PROPOSAL_REJECTION_BYTES,
        )
        try:
            previous_record = _strict_json_bytes(
                previous_content, label="prior Make proposal rejection"
            )
        except ContractError as exc:
            raise StateConflict("prior Make proposal rejection is invalid") from exc
        if previous_content != _canonical_json_bytes(previous_record) + b"\n":
            raise StateConflict("prior Make proposal rejection is not canonical")
        validated_previous = _validate_make_proposal_rejection_record(
            run,
            checkpoint,
            previous_record,
            directory=directory,
            seen=seen | {rejection_sha256},
        )
        if (
            validated_previous["rejection_sha256"] != previous
            or validated_previous["rejection_number"] != rejection_number - 1
        ):
            raise StateConflict("Make proposal rejection predecessor is invalid")
    return dict(record)


def _read_make_proposal_rejection(
    run: AgentRun, checkpoint: AgentRunCheckpoint
) -> Optional[Mapping[str, Any]]:
    if checkpoint.stage != "make":
        return None
    directory = _make_proposal_rejection_directory(run, checkpoint)
    head_path = directory / "current.json"
    if not head_path.exists() and not head_path.is_symlink():
        return None
    content = _read_stable_private_bytes(
        head_path,
        label="Make proposal rejection head",
        maximum_bytes=4 * 1024,
    )
    try:
        head = _strict_json_bytes(content, label="Make proposal rejection head")
    except ContractError as exc:
        raise StateConflict("Make proposal rejection head is invalid") from exc
    expected = {
        "schema_version",
        "kind",
        "checkpoint_sha256",
        "rejection_sha256",
        "head_sha256",
    }
    identity = {key: head.get(key) for key in expected - {"head_sha256"}}
    if (
        content != _canonical_json_bytes(head) + b"\n"
        or set(head) != expected
        or head.get("schema_version") != 1
        or head.get("kind") != _MAKE_PROPOSAL_REJECTION_HEAD_KIND
        or head.get("checkpoint_sha256") != checkpoint.checkpoint_sha256
        or not isinstance(head.get("rejection_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", head["rejection_sha256"]) is None
        or head.get("head_sha256") != _sha256(_canonical_json_bytes(identity))
    ):
        raise StateConflict("Make proposal rejection head is invalid")
    record_content = _read_stable_private_bytes(
        _make_proposal_rejection_record_path(
            directory, head["rejection_sha256"]
        ),
        label="Make proposal rejection",
        maximum_bytes=_MAX_MAKE_PROPOSAL_REJECTION_BYTES,
    )
    try:
        record = _strict_json_bytes(
            record_content, label="Make proposal rejection"
        )
    except ContractError as exc:
        raise StateConflict("Make proposal rejection is invalid") from exc
    if record_content != _canonical_json_bytes(record) + b"\n":
        raise StateConflict("Make proposal rejection is not canonical")
    validated = _validate_make_proposal_rejection_record(
        run, checkpoint, record, directory=directory
    )
    if validated["rejection_sha256"] != head["rejection_sha256"]:
        raise StateConflict("Make proposal rejection head points to another record")
    return validated


def _make_rejection_for_error(error: ContractError) -> _MakeProposalRejected:
    if isinstance(error, StateConflict) or not isinstance(error, ContractError):
        raise StateConflict("Make proposal rejection classification is invalid")
    message = str(error)
    if message.startswith("Made product title ") or message.startswith(
        "Made product summary "
    ):
        failure_code = "make-product-metadata-invalid"
        return _MakeProposalRejected(
            failure_code=failure_code,
            feedback=_MAKE_PROPOSAL_REJECTION_FEEDBACK[failure_code],
        )
    if isinstance(error, ArtifactError):
        failure_code = "make-artifact-invalid"
        return _MakeProposalRejected(
            failure_code=failure_code,
            feedback=_MAKE_PROPOSAL_REJECTION_FEEDBACK[failure_code],
        )
    failure_code = "make-contract-invalid"
    return _MakeProposalRejected(
        failure_code=failure_code,
        feedback=_MAKE_PROPOSAL_REJECTION_FEEDBACK[failure_code],
    )


def _current_agent_outcome_bytes(
    run: AgentRun, proposal: AgentOutcomeProposal
) -> bytes:
    document, content = read_bounded_json_artifact(
        run.run_root,
        _AGENT_OUTCOME_NAME,
        maximum_bytes=_MAX_MAKE_PROPOSAL_REJECTION_BYTES,
        label=_AGENT_OUTCOME_NAME,
    )
    current = AgentOutcomeProposal.from_mapping(document)
    if current.to_dict() != proposal.to_dict():
        raise StateConflict("agent outcome changed while its rejection was recorded")
    return content


def _persist_make_proposal_rejection(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    proposal: AgentOutcomeProposal,
    rejection: _MakeProposalRejected,
) -> Mapping[str, Any]:
    if checkpoint.stage != "make":
        raise TransitionError("Make proposal rejection belongs to another stage")
    if (
        _MAKE_PROPOSAL_REJECTION_FEEDBACK.get(rejection.failure_code)
        != rejection.feedback
    ):
        raise StateConflict("Make proposal rejection feedback is invalid")
    proposal_bytes = _current_agent_outcome_bytes(run, proposal)
    proposal_file_sha256 = _sha256(proposal_bytes)
    previous = _read_make_proposal_rejection(run, checkpoint)
    if (
        previous is not None
        and previous["rejected_proposal_file_sha256"] == proposal_file_sha256
        and previous["rejected_proposal_sha256"] == proposal.sha256
        and previous["subject_sha256"] == proposal.subject_sha256
    ):
        return previous
    if (
        previous is not None
        and previous["rejection_number"] >= _MAX_MAKE_PROPOSAL_REJECTIONS
    ):
        raise WorkshopError(
            "Make proposal exhausted its bounded host rejection budget"
        )
    directory = _make_proposal_rejection_directory(run, checkpoint, create=True)
    quarantine_path = _make_proposal_quarantine_path(
        directory, proposal_file_sha256
    )
    if quarantine_path.exists() or quarantine_path.is_symlink():
        quarantined = _read_stable_private_bytes(
            quarantine_path,
            label="quarantined Make proposal",
            maximum_bytes=_MAX_MAKE_PROPOSAL_REJECTION_BYTES,
        )
        if quarantined != proposal_bytes:
            raise StateConflict("quarantined Make proposal bytes changed")
    else:
        _atomic_private_write(quarantine_path, proposal_bytes)
    identity: dict[str, Any] = {
        "schema_version": 1,
        "kind": _MAKE_PROPOSAL_REJECTION_KIND,
        "product_id": checkpoint.product_id,
        "stage": "make",
        "round": checkpoint.round_index,
        "rejection_number": (
            previous["rejection_number"] + 1 if previous is not None else 1
        ),
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "subject_sha256": proposal.subject_sha256,
        "previous_rejection_sha256": (
            previous["rejection_sha256"] if previous is not None else None
        ),
        "rejected_proposal_sha256": proposal.sha256,
        "rejected_proposal_file_sha256": proposal_file_sha256,
        "rejected_outcome_sha256": proposal.outcome.sha256,
        "rejected_artifacts": [
            artifact.to_dict() for artifact in proposal.outcome.artifacts
        ],
        "failure_code": rejection.failure_code,
        "feedback": rejection.feedback,
    }
    record = {
        **identity,
        "rejection_sha256": _sha256(_canonical_json_bytes(identity)),
    }
    encoded = _canonical_json_bytes(record) + b"\n"
    if len(encoded) > _MAX_MAKE_PROPOSAL_REJECTION_BYTES:
        raise StateConflict("Make proposal rejection exceeded its safe size limit")
    record_path = _make_proposal_rejection_record_path(
        directory, record["rejection_sha256"]
    )
    if record_path.exists() or record_path.is_symlink():
        existing = _read_stable_private_bytes(
            record_path,
            label="Make proposal rejection",
            maximum_bytes=_MAX_MAKE_PROPOSAL_REJECTION_BYTES,
        )
        if existing != encoded:
            raise StateConflict("Make proposal rejection identity was reused")
    else:
        _atomic_private_write(record_path, encoded)

    head_identity = {
        "schema_version": 1,
        "kind": _MAKE_PROPOSAL_REJECTION_HEAD_KIND,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "rejection_sha256": record["rejection_sha256"],
    }
    head = {
        **head_identity,
        "head_sha256": _sha256(_canonical_json_bytes(head_identity)),
    }
    _atomic_private_write(
        directory / "current.json", _canonical_json_bytes(head) + b"\n"
    )
    return record


def _playtest_proposal_rejection_directory(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    *,
    create: bool = False,
) -> Path:
    if checkpoint.stage != "playtest":
        raise TransitionError("Playtest proposal rejection belongs to another stage")
    current = run.host_state_root
    for index, part in enumerate(
        (
            _PLAYTEST_PROPOSAL_REJECTIONS_DIRECTORY,
            checkpoint.checkpoint_sha256,
        )
    ):
        candidate = current / part
        try:
            identity = candidate.lstat()
        except FileNotFoundError:
            if not create:
                remaining = (
                    _PLAYTEST_PROPOSAL_REJECTIONS_DIRECTORY,
                    checkpoint.checkpoint_sha256,
                )[index:]
                return current.joinpath(*remaining)
            try:
                candidate.mkdir(mode=0o700)
                identity = candidate.lstat()
            except OSError as exc:
                raise StateConflict(
                    "Playtest proposal rejection directory is unavailable"
                ) from exc
        except OSError as exc:
            raise StateConflict(
                "Playtest proposal rejection directory is unavailable"
            ) from exc
        if (
            stat.S_ISLNK(identity.st_mode)
            or not stat.S_ISDIR(identity.st_mode)
            or stat.S_IMODE(identity.st_mode) != 0o700
        ):
            raise StateConflict(
                "Playtest proposal rejection directory must be private"
            )
        current = candidate
    return current


def _playtest_proposal_rejection_record_path(
    directory: Path, rejection_sha256: str
) -> Path:
    if re.fullmatch(r"[0-9a-f]{64}", rejection_sha256) is None:
        raise StateConflict("Playtest proposal rejection identity is invalid")
    return directory / ("rejection-%s.json" % rejection_sha256)


def _playtest_proposal_quarantine_path(
    directory: Path, proposal_file_sha256: str
) -> Path:
    if re.fullmatch(r"[0-9a-f]{64}", proposal_file_sha256) is None:
        raise StateConflict("quarantined Playtest proposal identity is invalid")
    return directory / ("outcome-%s.json" % proposal_file_sha256)


def _validate_playtest_proposal_rejection_record(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    record: Mapping[str, Any],
    *,
    directory: Path,
    seen: frozenset[str] = frozenset(),
) -> Mapping[str, Any]:
    expected = {
        "schema_version",
        "kind",
        "product_id",
        "stage",
        "round",
        "rejection_number",
        "checkpoint_sha256",
        "subject_sha256",
        "previous_rejection_sha256",
        "rejected_proposal_sha256",
        "rejected_proposal_file_sha256",
        "rejected_outcome_sha256",
        "rejected_artifacts",
        "failure_code",
        "feedback",
        "rejection_sha256",
    }
    digest_fields = (
        "checkpoint_sha256",
        "subject_sha256",
        "rejected_proposal_sha256",
        "rejected_proposal_file_sha256",
        "rejected_outcome_sha256",
        "rejection_sha256",
    )
    previous = record.get("previous_rejection_sha256")
    artifacts = record.get("rejected_artifacts")
    rejection_number = record.get("rejection_number")
    rejection_sha256 = record.get("rejection_sha256")
    failure_code = record.get("failure_code")
    if (
        set(record) != expected
        or record.get("schema_version") != 1
        or record.get("kind") != _PLAYTEST_PROPOSAL_REJECTION_KIND
        or record.get("product_id") != checkpoint.product_id
        or record.get("stage") != "playtest"
        or record.get("round") != checkpoint.round_index
        or type(rejection_number) is not int
        or not 1 <= rejection_number <= _MAX_PLAYTEST_PROPOSAL_REJECTIONS
        or record.get("checkpoint_sha256") != checkpoint.checkpoint_sha256
        or (
            previous is not None
            and (
                not isinstance(previous, str)
                or re.fullmatch(r"[0-9a-f]{64}", previous) is None
            )
        )
        or any(
            not isinstance(record.get(name), str)
            or re.fullmatch(r"[0-9a-f]{64}", record[name]) is None
            for name in digest_fields
        )
        or failure_code not in _PLAYTEST_PROPOSAL_REJECTION_FEEDBACK
        or record.get("feedback")
        != _PLAYTEST_PROPOSAL_REJECTION_FEEDBACK.get(failure_code)
        or not isinstance(artifacts, list)
    ):
        raise StateConflict("Playtest proposal rejection is invalid")
    try:
        artifact_values = tuple(
            AgentArtifact.from_mapping(value) for value in artifacts
        )
    except ContractError as exc:
        raise StateConflict(
            "Playtest proposal rejection artifacts are invalid"
        ) from exc
    if [artifact.to_dict() for artifact in artifact_values] != artifacts:
        raise StateConflict("Playtest proposal rejection artifacts are not canonical")
    identity = {key: record[key] for key in expected - {"rejection_sha256"}}
    if rejection_sha256 != _sha256(_canonical_json_bytes(identity)):
        raise StateConflict("Playtest proposal rejection hash is invalid")
    if rejection_sha256 in seen:
        raise StateConflict("Playtest proposal rejection chain contains a cycle")

    quarantine = _read_stable_private_bytes(
        _playtest_proposal_quarantine_path(
            directory, record["rejected_proposal_file_sha256"]
        ),
        label="quarantined Playtest proposal",
        maximum_bytes=_MAX_PLAYTEST_PROPOSAL_REJECTION_BYTES,
    )
    if _sha256(quarantine) != record["rejected_proposal_file_sha256"]:
        raise StateConflict("quarantined Playtest proposal hash is invalid")
    try:
        proposal_document = _strict_json_bytes(
            quarantine, label="quarantined Playtest proposal"
        )
        proposal = AgentOutcomeProposal.from_mapping(proposal_document)
    except ContractError as exc:
        raise StateConflict("quarantined Playtest proposal is invalid") from exc
    if (
        proposal.checkpoint_sha256 != checkpoint.checkpoint_sha256
        or proposal.subject_sha256 != record["subject_sha256"]
        or proposal.outcome.stage != "playtest"
        or proposal.outcome.status != "ready"
        or proposal.sha256 != record["rejected_proposal_sha256"]
        or proposal.outcome.sha256 != record["rejected_outcome_sha256"]
        or [artifact.to_dict() for artifact in proposal.outcome.artifacts]
        != artifacts
    ):
        raise StateConflict(
            "quarantined Playtest proposal disagrees with its rejection"
        )

    if previous is None:
        if rejection_number != 1:
            raise StateConflict("Playtest proposal rejection predecessor is invalid")
    else:
        if rejection_number <= 1:
            raise StateConflict("Playtest proposal rejection predecessor is invalid")
        previous_content = _read_stable_private_bytes(
            _playtest_proposal_rejection_record_path(directory, previous),
            label="prior Playtest proposal rejection",
            maximum_bytes=_MAX_PLAYTEST_PROPOSAL_REJECTION_BYTES,
        )
        try:
            previous_record = _strict_json_bytes(
                previous_content, label="prior Playtest proposal rejection"
            )
        except ContractError as exc:
            raise StateConflict(
                "prior Playtest proposal rejection is invalid"
            ) from exc
        if previous_content != _canonical_json_bytes(previous_record) + b"\n":
            raise StateConflict(
                "prior Playtest proposal rejection is not canonical"
            )
        validated_previous = _validate_playtest_proposal_rejection_record(
            run,
            checkpoint,
            previous_record,
            directory=directory,
            seen=seen | {rejection_sha256},
        )
        if (
            validated_previous["rejection_sha256"] != previous
            or validated_previous["rejection_number"] != rejection_number - 1
        ):
            raise StateConflict("Playtest proposal rejection predecessor is invalid")
    return dict(record)


def _read_playtest_proposal_rejection(
    run: AgentRun, checkpoint: AgentRunCheckpoint
) -> Optional[Mapping[str, Any]]:
    if checkpoint.stage != "playtest":
        return None
    directory = _playtest_proposal_rejection_directory(run, checkpoint)
    head_path = directory / "current.json"
    if not head_path.exists() and not head_path.is_symlink():
        return None
    head_content = _read_stable_private_bytes(
        head_path,
        label="Playtest proposal rejection head",
        maximum_bytes=4 * 1024,
    )
    try:
        head = _strict_json_bytes(
            head_content, label="Playtest proposal rejection head"
        )
    except ContractError as exc:
        raise StateConflict("Playtest proposal rejection head is invalid") from exc
    head_fields = {
        "schema_version",
        "kind",
        "checkpoint_sha256",
        "rejection_sha256",
        "head_sha256",
    }
    head_identity = {key: head.get(key) for key in head_fields - {"head_sha256"}}
    if (
        head_content != _canonical_json_bytes(head) + b"\n"
        or set(head) != head_fields
        or head.get("schema_version") != 1
        or head.get("kind") != _PLAYTEST_PROPOSAL_REJECTION_HEAD_KIND
        or head.get("checkpoint_sha256") != checkpoint.checkpoint_sha256
        or not isinstance(head.get("rejection_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", head["rejection_sha256"]) is None
        or head.get("head_sha256") != _sha256(_canonical_json_bytes(head_identity))
    ):
        raise StateConflict("Playtest proposal rejection head is invalid")
    record_content = _read_stable_private_bytes(
        _playtest_proposal_rejection_record_path(
            directory, head["rejection_sha256"]
        ),
        label="Playtest proposal rejection",
        maximum_bytes=_MAX_PLAYTEST_PROPOSAL_REJECTION_BYTES,
    )
    try:
        record = _strict_json_bytes(
            record_content, label="Playtest proposal rejection"
        )
    except ContractError as exc:
        raise StateConflict("Playtest proposal rejection is invalid") from exc
    if record_content != _canonical_json_bytes(record) + b"\n":
        raise StateConflict("Playtest proposal rejection is not canonical")
    validated = _validate_playtest_proposal_rejection_record(
        run, checkpoint, record, directory=directory
    )
    if validated["rejection_sha256"] != head["rejection_sha256"]:
        raise StateConflict(
            "Playtest proposal rejection head points to another record"
        )
    return validated


def _playtest_rejection_for_error(error: ContractError) -> _PlaytestProposalRejected:
    if isinstance(error, StateConflict) or not isinstance(error, ContractError):
        raise StateConflict("Playtest proposal rejection classification is invalid")
    failure_code = (
        "playtest-artifact-invalid"
        if isinstance(error, ArtifactError)
        else "playtest-contract-invalid"
    )
    return _PlaytestProposalRejected(
        failure_code=failure_code,
        feedback=_PLAYTEST_PROPOSAL_REJECTION_FEEDBACK[failure_code],
    )


def _persist_playtest_proposal_rejection(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    proposal: AgentOutcomeProposal,
    rejection: _PlaytestProposalRejected,
) -> Mapping[str, Any]:
    if checkpoint.stage != "playtest":
        raise TransitionError("Playtest proposal rejection belongs to another stage")
    if (
        _PLAYTEST_PROPOSAL_REJECTION_FEEDBACK.get(rejection.failure_code)
        != rejection.feedback
    ):
        raise StateConflict("Playtest proposal rejection feedback is invalid")
    proposal_bytes = _current_agent_outcome_bytes(run, proposal)
    proposal_file_sha256 = _sha256(proposal_bytes)
    previous = _read_playtest_proposal_rejection(run, checkpoint)
    if (
        previous is not None
        and previous["rejected_proposal_file_sha256"] == proposal_file_sha256
        and previous["rejected_proposal_sha256"] == proposal.sha256
        and previous["subject_sha256"] == proposal.subject_sha256
    ):
        return previous
    if (
        previous is not None
        and previous["rejection_number"] >= _MAX_PLAYTEST_PROPOSAL_REJECTIONS
    ):
        raise WorkshopError(
            "Playtest proposal exhausted its bounded host rejection budget"
        )
    directory = _playtest_proposal_rejection_directory(
        run, checkpoint, create=True
    )
    quarantine_path = _playtest_proposal_quarantine_path(
        directory, proposal_file_sha256
    )
    if quarantine_path.exists() or quarantine_path.is_symlink():
        if _read_stable_private_bytes(
            quarantine_path,
            label="quarantined Playtest proposal",
            maximum_bytes=_MAX_PLAYTEST_PROPOSAL_REJECTION_BYTES,
        ) != proposal_bytes:
            raise StateConflict("quarantined Playtest proposal bytes changed")
    else:
        _atomic_private_write(quarantine_path, proposal_bytes)
    identity: dict[str, Any] = {
        "schema_version": 1,
        "kind": _PLAYTEST_PROPOSAL_REJECTION_KIND,
        "product_id": checkpoint.product_id,
        "stage": "playtest",
        "round": checkpoint.round_index,
        "rejection_number": (
            previous["rejection_number"] + 1 if previous is not None else 1
        ),
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "subject_sha256": proposal.subject_sha256,
        "previous_rejection_sha256": (
            previous["rejection_sha256"] if previous is not None else None
        ),
        "rejected_proposal_sha256": proposal.sha256,
        "rejected_proposal_file_sha256": proposal_file_sha256,
        "rejected_outcome_sha256": proposal.outcome.sha256,
        "rejected_artifacts": [
            artifact.to_dict() for artifact in proposal.outcome.artifacts
        ],
        "failure_code": rejection.failure_code,
        "feedback": rejection.feedback,
    }
    record = {
        **identity,
        "rejection_sha256": _sha256(_canonical_json_bytes(identity)),
    }
    encoded = _canonical_json_bytes(record) + b"\n"
    if len(encoded) > _MAX_PLAYTEST_PROPOSAL_REJECTION_BYTES:
        raise StateConflict("Playtest proposal rejection exceeded its safe size limit")
    record_path = _playtest_proposal_rejection_record_path(
        directory, record["rejection_sha256"]
    )
    if record_path.exists() or record_path.is_symlink():
        if _read_stable_private_bytes(
            record_path,
            label="Playtest proposal rejection",
            maximum_bytes=_MAX_PLAYTEST_PROPOSAL_REJECTION_BYTES,
        ) != encoded:
            raise StateConflict("Playtest proposal rejection identity was reused")
    else:
        _atomic_private_write(record_path, encoded)
    head_identity = {
        "schema_version": 1,
        "kind": _PLAYTEST_PROPOSAL_REJECTION_HEAD_KIND,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "rejection_sha256": record["rejection_sha256"],
    }
    head = {
        **head_identity,
        "head_sha256": _sha256(_canonical_json_bytes(head_identity)),
    }
    _atomic_private_write(
        directory / "current.json", _canonical_json_bytes(head) + b"\n"
    )
    return record


def _remove_rejected_agent_outcome(
    run: AgentRun, rejection: Mapping[str, Any]
) -> None:
    path = run.run_root / _AGENT_OUTCOME_NAME
    if not path.exists() and not path.is_symlink():
        return
    try:
        document, content = read_bounded_json_artifact(
            run.run_root,
            _AGENT_OUTCOME_NAME,
            maximum_bytes=_MAX_MAKE_PROPOSAL_REJECTION_BYTES,
            label=_AGENT_OUTCOME_NAME,
        )
        proposal = AgentOutcomeProposal.from_mapping(document)
    except ContractError as exc:
        raise StateConflict("rejected agent outcome changed before removal") from exc
    if (
        _sha256(content) != rejection["rejected_proposal_file_sha256"]
        or proposal.sha256 != rejection["rejected_proposal_sha256"]
        or proposal.outcome.sha256 != rejection["rejected_outcome_sha256"]
    ):
        raise StateConflict("rejected agent outcome changed before removal")
    _remove_agent_outcome(run.run_root)


def _reconcile_rejected_agent_outcome(
    run: AgentRun, checkpoint: AgentRunCheckpoint
) -> None:
    rejection = _read_make_proposal_rejection(run, checkpoint)
    if rejection is None or not _agent_outcome_exists(run.run_root):
        return
    try:
        unused_document, content = read_bounded_json_artifact(
            run.run_root,
            _AGENT_OUTCOME_NAME,
            maximum_bytes=_MAX_MAKE_PROPOSAL_REJECTION_BYTES,
            label=_AGENT_OUTCOME_NAME,
        )
    except ContractError:
        return
    del unused_document
    if _sha256(content) == rejection["rejected_proposal_file_sha256"]:
        _remove_rejected_agent_outcome(run, rejection)


def _remove_agent_outcome(run_root: Path) -> None:
    path = run_root / _AGENT_OUTCOME_NAME
    if not path.exists() and not path.is_symlink():
        return
    try:
        identity = path.lstat()
    except OSError as exc:
        raise StateConflict("stale agent outcome is unavailable") from exc
    if path.is_symlink() or not stat.S_ISREG(identity.st_mode):
        raise StateConflict("stale agent outcome must be a regular file")
    try:
        path.unlink()
    except OSError as exc:
        raise StateConflict("stale agent outcome could not be removed") from exc


def _load_wish(run_root: Path) -> Wish:
    path = run_root / "WISH.json"
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise StateConflict("materialized Wish is unavailable") from exc
    document = _strict_json_bytes(content, label="materialized Wish")
    try:
        wish = Wish(**document)
    except (TypeError, ValueError, WorkshopError) as exc:
        raise StateConflict("materialized Wish is invalid") from exc
    if canonical_wish_bytes(wish) != content:
        raise StateConflict("materialized Wish is not canonical")
    return wish


def materialized_agent_instructions_sha256(
    checkpoint: AgentRunCheckpoint,
) -> str:
    """Bind the exact AGENTS.md and skill bytes already inside a run.

    Resume derives this value from the immutable run manifest, not from the
    current source checkout or installed package.  Updating instructions for a
    future Wish therefore cannot silently change an existing session binding.
    """

    if not isinstance(checkpoint, AgentRunCheckpoint):
        raise ContractError("instruction manifest requires an AgentRun checkpoint")
    selected = {
        path: digest
        for path, digest in checkpoint.input_sha256s.items()
        if path == "AGENTS.md"
        or path.startswith(".agents/skills/")
        or path.startswith(".codex/agents/")
    }
    required = {
        "AGENTS.md",
        ".agents/skills/autonomous-workshop/SKILL.md",
    }
    if not required <= set(selected):
        raise StateConflict("native run instruction manifest is incomplete")
    digest = hashlib.sha256(_INSTRUCTION_HASH_DOMAIN)
    for relative, content_sha256 in sorted(selected.items()):
        try:
            content_digest = bytes.fromhex(content_sha256)
        except (TypeError, ValueError) as exc:
            raise StateConflict("native run instruction manifest is invalid") from exc
        if len(content_digest) != 32:
            raise StateConflict("native run instruction manifest is invalid")
        encoded_path = relative.encode("utf-8")
        digest.update(len(encoded_path).to_bytes(4, "big"))
        digest.update(encoded_path)
        digest.update(content_digest)
    return digest.hexdigest()


def _materialized_release_contract(
    checkpoint: AgentRunCheckpoint,
) -> Mapping[str, Any]:
    """Select Release semantics from this run's immutable tool capability.

    Manual-first Release added a required, sibling ``pdf_validator.py`` to the
    materialized finalizer tree.  Historical runs do not contain that exact
    input and can only produce the legacy Markdown contract.  Resume must not
    project today's source-checkout contract onto either frozen toolchain.
    """

    if not isinstance(checkpoint, AgentRunCheckpoint):
        raise ContractError("Release contract requires an AgentRun checkpoint")
    inputs = checkpoint.input_sha256s
    if _PRODUCT_RUN_FINALIZER_INPUT not in inputs:
        raise StateConflict("native run lacks its materialized stage finalizer")
    direct_release = _checkpoint_uses_direct_release(checkpoint)
    manual_design_evidence = _PRODUCT_RUN_MANUAL_DESIGN_EVIDENCE_INPUT in inputs
    if direct_release:
        contract = {
            "native_release_schema_version": 3,
            "manual_path": NATIVE_RELEASE_MANUAL_PATH,
            "product_schema_version": DIRECT_RELEASE_PRODUCT_SCHEMA_VERSION,
            "product_status": "manual-ready",
            "playtest_status": DIRECT_RELEASE_PLAYTEST_STATUS,
            "playtest_omission_path": NATIVE_RELEASE_PLAYTEST_OMISSION_PATH,
        }
        if manual_design_evidence:
            contract["manual_design_evidence_path"] = MANUAL_DESIGN_EVIDENCE_PATH
            contract["manual_design_evidence_schema_version"] = 1
        return contract
    manual_first = _PRODUCT_RUN_PDF_VALIDATOR_INPUT in inputs
    if manual_first:
        contract = {
            "native_release_schema_version": 2,
            "manual_path": NATIVE_RELEASE_MANUAL_PATH,
            "product_schema_version": 4,
            "product_status": "manual-ready",
        }
        if manual_design_evidence:
            contract["manual_design_evidence_path"] = MANUAL_DESIGN_EVIDENCE_PATH
            contract["manual_design_evidence_schema_version"] = 1
        return contract
    return {
        "native_release_schema_version": 1,
        "manual_path": NATIVE_RELEASE_LEGACY_MANUAL_PATH,
        "product_schema_version": 3,
        "product_status": "page-ready",
    }


def _checkpoint_effort(checkpoint: AgentRunCheckpoint):
    """Return the exact frozen effort, or ``None`` for historical runs."""

    if checkpoint.effort is None:
        return None
    capable = _PRODUCT_RUN_EFFORT_ROUTES_INPUT in checkpoint.input_sha256s
    if not capable:
        raise StateConflict("native run frozen effort lacks its immutable capability")
    try:
        return workshop_effort(checkpoint.effort)
    except ContractError as exc:
        raise StateConflict("native run frozen effort is invalid") from exc


def _checkpoint_uses_direct_release(checkpoint: AgentRunCheckpoint) -> bool:
    effort = _checkpoint_effort(checkpoint)
    if effort is not None:
        return not effort.includes("playtest")
    return _PRODUCT_RUN_DIRECT_RELEASE_INPUT in checkpoint.input_sha256s


def _checkpoint_allows_make_invent_revision(
    checkpoint: AgentRunCheckpoint,
) -> bool:
    effort = _checkpoint_effort(checkpoint)
    return bool(
        effort is not None
        and effort.includes("invent")
        and MAKE_INVENT_REVISION_CAPABILITY_PATH in checkpoint.input_sha256s
    )


def _checkpoint_next_stage(checkpoint: AgentRunCheckpoint, stage: str) -> str:
    effort = _checkpoint_effort(checkpoint)
    if effort is not None:
        return effort.next_stage(stage)
    if stage == "make" and _checkpoint_uses_direct_release(checkpoint):
        return "release"
    return {
        "wish": "match",
        "match": "invent",
        "invent": "make",
        "make": "playtest",
        "playtest": "release",
        "release": "complete",
    }[stage]


def _materialized_release_terminal_transition(
    checkpoint: AgentRunCheckpoint,
) -> str:
    """Preserve the forward value understood by the frozen finalizer."""

    if not isinstance(checkpoint, AgentRunCheckpoint):
        raise ContractError("Release transition requires an AgentRun checkpoint")
    if _PRODUCT_RUN_FINALIZER_INPUT not in checkpoint.input_sha256s:
        raise StateConflict("native run lacks its materialized stage finalizer")
    return (
        "complete"
        if _PRODUCT_RUN_TERMINAL_RELEASE_INPUT in checkpoint.input_sha256s
        else "deliver"
    )


def native_stage_prompt(stage: str) -> str:
    """Give the native session a compact pointer, never Wish or host secrets."""

    if stage not in (
        "wish",
        "match",
        "invent",
        "make",
        "playtest",
        "release",
    ):
        raise ContractError("native run stage is invalid")
    return (
        "Follow the local AGENTS.md and autonomous-workshop skill. "
        "Read the host-written STAGE.json. Treat every host-written rejection "
        "in that packet as authoritative proof that the prior proposal failed "
        "its host gate and that the current subject is a new stage attempt. If "
        "the prior Goal is already complete, create a new Goal bound to this "
        "current subject. Address the exact rejection before finalizing; never "
        "rerun the finalizer or resubmit unchanged rejected bytes. Create one "
        "native Goal for the "
        "current %s stage with successful finalization as its stopping condition; "
        "keep inspecting, acting, evaluating, and improving until that condition "
        "is met. Use the run-local deterministic proposal tool, complete the goal "
        "after it writes agent-outcome.json successfully, then return control to "
        "the Workshop host gate."
        % stage
    )


def _current_make_proposal_rejection(
    cad_gate_rejection: Optional[Mapping[str, Any]],
    make_proposal_rejection: Optional[Mapping[str, Any]],
) -> Optional[Mapping[str, Any]]:
    """Hide proposal feedback once a newer CAD gate proves it was repaired.

    The historical proposal-rejection chain remains durably validated and
    auditable. A CAD rejection can exist only after the replacement Made
    proposal passed its authored contract checks, so presenting the older
    proposal feedback as still actionable would direct the next native turn
    away from the current deterministic failure.
    """

    if cad_gate_rejection is not None:
        return None
    return make_proposal_rejection


def _recoverable_native_turn_backoff_seconds(
    checkpoint: AgentRunCheckpoint,
    attempted_turns: int,
) -> float:
    """Return bounded deterministic jitter for one exact run attempt."""

    if (
        not isinstance(checkpoint, AgentRunCheckpoint)
        or type(attempted_turns) is not int
        or not 1 <= attempted_turns < _MAX_NATIVE_TURNS
    ):
        raise ContractError("native continuation backoff input is invalid")
    exponent = min(attempted_turns - 1, 16)
    jitter_ceiling = (
        _RECOVERABLE_BACKOFF_JITTER_MIN
        + _RECOVERABLE_BACKOFF_JITTER_SPAN
    )
    unjittered_cap = _RECOVERABLE_BACKOFF_MAX_SECONDS / jitter_ceiling
    unjittered = min(
        unjittered_cap,
        _RECOVERABLE_BACKOFF_BASE_SECONDS * (2**exponent),
    )
    seed = (
        "%s\0%s\0%d"
        % (
            checkpoint.product_id,
            checkpoint.checkpoint_sha256,
            attempted_turns,
        )
    ).encode("utf-8")
    fraction = int.from_bytes(hashlib.sha256(seed).digest()[:2], "big") / 65_535
    jitter = (
        _RECOVERABLE_BACKOFF_JITTER_MIN
        + _RECOVERABLE_BACKOFF_JITTER_SPAN * fraction
    )
    return unjittered * jitter


def _validated_product_id(product_id: str) -> str:
    if not isinstance(product_id, str) or _RUN_ID.fullmatch(product_id) is None:
        raise ContractError("native run product id is invalid")
    return product_id


def _existing_real_directory(path: Path, *, label: str) -> Path:
    try:
        identity = path.lstat()
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if path.is_symlink() or not stat.S_ISDIR(identity.st_mode):
        raise StateConflict("%s must be a real directory" % label)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if resolved != path:
        raise StateConflict("%s must not contain symlinks" % label)
    return resolved


def _ensure_private_directory(path: Path, *, label: str) -> Path:
    created = False
    try:
        path.mkdir(mode=0o700)
        created = True
    except FileExistsError:
        pass
    except OSError as exc:
        raise StateConflict("%s could not be created" % label) from exc
    resolved = _existing_real_directory(path, label=label)
    if created:
        os.chmod(resolved, 0o700)
    if stat.S_IMODE(resolved.stat().st_mode) != 0o700:
        raise StateConflict("%s permissions must be 0700" % label)
    return resolved


def _workshop_home() -> Path:
    selected = Path(default_workshop_home()).expanduser()
    if not selected.is_absolute():
        raise ContractError("Workshop home must be absolute")
    try:
        selected.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as exc:
        raise StateConflict("Workshop home could not be created") from exc
    return _existing_real_directory(selected, label="Workshop home")


def _source_checkout_root() -> Optional[Path]:
    """Return the repository root when this module is running from ``src/``."""

    module = Path(__file__).resolve()
    if len(module.parents) < 4:
        return None
    candidate = module.parents[3]
    if (
        (candidate / "src" / "workshop" / "workflow" / "native_run.py").resolve()
        != module
        or not (candidate / ".agents" / "product-run" / "AGENTS.md").is_file()
        or not (
            candidate
            / ".agents"
            / "product-run"
            / ".agents"
            / "skills"
            / "autonomous-workshop"
            / "SKILL.md"
        ).is_file()
    ):
        return None
    return _existing_real_directory(candidate, label="Workshop repository")


def _public_example_repository_for_run(run_root: Path) -> Optional[Path]:
    """Return the checkout only for a run created in the new private layout.

    Legacy runs are exact-path compatible but are never retroactively projected
    into a different public-example convention during status or resume.
    """

    expected_runs = _workshop_home() / "runs"
    if (
        run_root.name != "workspace"
        or run_root.parent.parent != expected_runs
    ):
        return None
    return _source_checkout_root()


def _public_example_status_path(run: AgentRun) -> Path:
    return run.host_state_root / _PUBLIC_EXAMPLE_STATUS_NAME


def _record_public_example_projection(
    run: AgentRun,
    *,
    release: NativeRelease,
    made: NativeMade,
    inventor_id: str,
    receipt: Receipt,
) -> Mapping[str, Any]:
    """Project the public toy and optionally commit and push that directory."""

    checkpoint = run.snapshot()
    github_requested = _github_publication_requested(run)

    try:
        repository = _public_example_repository_for_run(run.run_root)
    except Exception:
        repository = None
        repository_error = True
    else:
        repository_error = False
    if repository is None:
        public = {
            "status": "error" if repository_error else "unavailable",
            "reason": (
                "Public Git projection is available only for new private runs "
                "started from a Workshop source checkout."
            ),
        }
    else:
        try:
            target = materialize_public_example_if_source_checkout(
                repository,
                run.run_root,
                release=release,
                made=made,
                inventor_id=inventor_id,
                receipt=receipt,
                manager_id=checkpoint.manager_id,
                effort=checkpoint.effort,
                github_requested=github_requested,
                token_summary=_native_token_summary(
                    NativeRunPaths(run.run_root, run.host_state_root),
                    checkpoint,
                ),
                wish_id=checkpoint.product_id,
            )
            target_relative = (
                target.relative_to(repository).as_posix()
                if target is not None
                else None
            )
        except Exception:
            public = {
                "status": "error",
                "reason": (
                    "Public Git projection failed closed; Factory publication "
                    "is still verified and the projection can be retried later."
                ),
            }
        else:
            if target is None:  # pragma: no cover - repository is non-null above
                public = {"status": "unavailable"}
            elif github_requested:
                try:
                    pushed_path = push_toy_directory(
                        repository,
                        target,
                        title=str(release.product["title"]),
                    )
                except (GitPushError, StateConflict, OSError):
                    public = {
                        "status": "error",
                        "path": target_relative,
                        "reason": (
                            "The toy snapshot was generated, but git add, commit, "
                            "or push failed."
                        ),
                    }
                else:
                    public = {
                        "status": "pushed",
                        "path": pushed_path,
                    }
            else:
                public = {
                    "status": "materialized",
                    "path": target_relative,
                }
    document = {
        "schema_version": 1,
        "kind": "autonomous-workshop.public-example-projection",
        "product_id": checkpoint.product_id,
        "native_release_sha256": release.release_sha256,
        "package_artifact_sha256": release.package_manifest.artifact_sha256,
        "publication_slug": receipt.slug,
        "projection": public,
    }
    try:
        _write_private_json(_public_example_status_path(run), document)
    except Exception:
        # This convenience status is not lifecycle or Factory evidence.
        pass
    return public


def _try_record_public_example_projection(
    run: AgentRun,
    *,
    release: NativeRelease,
    made: NativeMade,
    inventor_id: str,
    receipt: Receipt,
) -> Mapping[str, Any]:
    """Keep even an unexpected projection regression outside the lifecycle."""

    try:
        return _record_public_example_projection(
            run,
            release=release,
            made=made,
            inventor_id=inventor_id,
            receipt=receipt,
        )
    except Exception:
        return {
            "status": "error",
            "reason": (
                "Public Git projection failed outside the lifecycle; Factory "
                "publication remains authoritative and projection is retryable."
            ),
        }


def _read_public_example_projection(
    run: AgentRun, release: NativeRelease
) -> Mapping[str, Any]:
    path = _public_example_status_path(run)
    if not path.exists() and not path.is_symlink():
        return {"status": "not-attempted"}
    try:
        identity = path.lstat()
        content = path.read_bytes()
    except OSError:
        return {"status": "unavailable"}
    if (
        path.is_symlink()
        or not stat.S_ISREG(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o600
    ):
        return {"status": "unavailable"}
    try:
        value = _strict_json_bytes(content, label="public example projection")
    except WorkshopError:
        return {"status": "unavailable"}
    expected = {
        "schema_version",
        "kind",
        "product_id",
        "native_release_sha256",
        "package_artifact_sha256",
        "publication_slug",
        "projection",
    }
    projection = value.get("projection")
    if (
        set(value) != expected
        or value.get("schema_version") != 1
        or value.get("kind")
        != "autonomous-workshop.public-example-projection"
        or value.get("product_id") != run.snapshot().product_id
        or value.get("native_release_sha256") != release.release_sha256
        or value.get("package_artifact_sha256")
        != release.package_manifest.artifact_sha256
        or not isinstance(projection, Mapping)
        or projection.get("status")
        not in ("materialized", "pushed", "error", "unavailable")
    ):
        return {"status": "unavailable"}
    return dict(projection)


def _product_run_inventor_source_root(assets: Any) -> Path:
    if assets.source == "repository":
        repository = assets.constitution.parents[2]
        inventors = repository / "inventors"
    else:
        inventors = packaged_inventors_root()
        if inventors is None:
            raise StateConflict("installed Workshop has no Inventors")
    return _existing_real_directory(Path(inventors), label="Inventor source root")


def _inventor_roster(checkpoint: AgentRunCheckpoint) -> InventorRoster:
    """Derive Match's public roster from host-verified custom agents only."""

    inventors: list[InventorRosterEntry] = []
    for item in checkpoint.inventor_roster:
        try:
            entry = InventorRosterEntry(
                inventor_id=item["inventor_id"],
                agent_path=item["agent_path"],
                agent_sha256=item["agent_sha256"],
                source_manifest_sha256=item["source_manifest_sha256"],
                taste_sha256=item["taste_sha256"],
            )
        except (KeyError, TypeError, ContractError) as exc:
            raise StateConflict("host Inventor roster is invalid") from exc
        if checkpoint.input_sha256s.get(entry.agent_path) != entry.agent_sha256:
            raise StateConflict("Inventor roster differs from immutable run inputs")
        inventors.append(entry)
    try:
        return InventorRoster(tuple(inventors))
    except ContractError as exc:
        raise StateConflict("host Inventor roster is invalid") from exc


def _selected_inventor_binding(
    run_root: Path,
    checkpoint: AgentRunCheckpoint,
    assignment: NativeMatchAssignment,
) -> Any:
    """Recover exact Taste and skill identity from the selected custom agent."""

    path = run_root / assignment.selected_agent_path
    try:
        before = path.lstat()
        content = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise StateConflict("selected Inventor custom agent is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(before.st_mode)
        or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
        or _sha256(content) != assignment.selected_agent_sha256
        or checkpoint.input_sha256s.get(assignment.selected_agent_path)
        != assignment.selected_agent_sha256
    ):
        raise StateConflict("selected Inventor custom agent changed")
    try:
        binding = parse_inventor_custom_agent_bytes(content)
    except ContractError as exc:
        raise StateConflict("selected Inventor custom agent is invalid") from exc
    if (
        binding.inventor_id != assignment.selected_inventor_id
        or binding.agent_path != assignment.selected_agent_path
        or binding.agent_sha256 != assignment.selected_agent_sha256
        or binding.source_manifest_sha256
        != assignment.selected_source_manifest_sha256
        or binding.taste_sha256 != assignment.selected_taste_sha256
    ):
        raise StateConflict("selected Inventor differs from the Match assignment")
    return binding


def _read_contract(
    run_root: Path, artifact: AgentArtifact, contract_type: Any, *, label: str
) -> Any:
    document, content = read_bounded_json_artifact(
        run_root, artifact.path, label=label
    )
    if _sha256(content) != artifact.sha256:
        raise StateConflict("%s differs from its sealed artifact binding" % label)
    return contract_type.from_mapping(document)


def _stage_primary(
    checkpoint: AgentRunCheckpoint, stage: str
) -> AgentArtifact:
    artifacts = checkpoint.stage_artifacts.get(stage)
    if not artifacts:
        raise TransitionError("native run lacks the %s contract" % stage)
    return artifacts[0]


def _stage_subject(stage: str, inputs: Mapping[str, Any]) -> str:
    return _sha256(
        _canonical_json_bytes(
            {
                "schema_version": 1,
                "kind": _SUBJECT_KIND,
                "stage": stage,
                "inputs": dict(inputs),
            }
        )
    )


def _stage_artifact_named(
    checkpoint: AgentRunCheckpoint, stage: str, name: str
) -> AgentArtifact:
    artifacts = checkpoint.stage_artifacts.get(stage, ())
    matches = tuple(item for item in artifacts if PurePosixPath(item.path).name == name)
    if len(matches) != 1:
        raise TransitionError(
            "native run requires exactly one %s artifact from %s" % (name, stage)
        )
    return matches[0]


def _stage_artifact_at(
    checkpoint: AgentRunCheckpoint, stage: str, path: str
) -> AgentArtifact:
    artifacts = checkpoint.stage_artifacts.get(stage, ())
    matches = tuple(item for item in artifacts if item.path == path)
    if len(matches) != 1:
        raise TransitionError(
            "native run requires exactly one %s artifact from %s" % (path, stage)
        )
    return matches[0]


def _routed_invent_contract_paths(
    checkpoint: AgentRunCheckpoint,
) -> tuple[str, str]:
    repairing = bool(
        checkpoint.stage_artifacts.get("invent")
        and "invent" in checkpoint.invalidated_stages
    )
    prefix = (
        "artifacts/invent/r%04d" % checkpoint.round_index
        if repairing
        else "artifacts/invent"
    )
    return "%s/assignment.json" % prefix, "%s/invented.json" % prefix


def _routed_make_creative_paths(round_index: int) -> tuple[str, str]:
    prefix = "artifacts/make/r%04d" % round_index
    return "%s/assignment.json" % prefix, "%s/invented.json" % prefix


def _routed_creative_context(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    roster: InventorRoster,
) -> tuple[
    NativeMatchAssignment,
    NativeInvented,
    AgentArtifact,
    AgentArtifact,
    Any,
]:
    effort = _checkpoint_effort(checkpoint)
    if effort is None:
        raise StateConflict("routed creative context requires a frozen effort")
    creative_stage = "make" if effort.name == "spark" else "invent"
    if effort.name == "spark":
        assignment_path, invented_path = _routed_make_creative_paths(
            checkpoint.round_index
        )
        assignment_artifact = _stage_artifact_at(
            checkpoint, creative_stage, assignment_path
        )
        invented_artifact = _stage_artifact_at(
            checkpoint, creative_stage, invented_path
        )
    else:
        assignment_artifact = _stage_artifact_named(
            checkpoint, creative_stage, "assignment.json"
        )
        invented_artifact = _stage_artifact_named(
            checkpoint, creative_stage, "invented.json"
        )
    assignment = _read_contract(
        run.run_root,
        assignment_artifact,
        NativeMatchAssignment,
        label="routed native Match assignment",
    )
    assignment.assert_context(
        wish_sha256=checkpoint.wish_sha256,
        roster=roster,
    )
    invented = _read_contract(
        run.run_root,
        invented_artifact,
        NativeInvented,
        label="routed native Invented contract",
    )
    invented.assert_context(assignment)
    inventor_binding = _selected_inventor_binding(
        run.run_root, checkpoint, assignment
    )
    return (
        assignment,
        invented,
        assignment_artifact,
        invented_artifact,
        inventor_binding,
    )


def native_run_paths(
    product_id: str,
    *,
    create: bool = False,
) -> NativeRunPaths:
    """Resolve one private Codex workspace and its sibling host state.

    New runs always live below ``$WORKSHOP_HOME/runs``.  Read paths retain
    compatibility with exact path-bound runs created by older Workshop
    versions in a source checkout's ``toys`` directory or in
    ``$WORKSHOP_HOME/toys``.  More than one extant layout is ambiguous and
    fails closed; an active run is never moved between roots.
    """

    product_id = _validated_product_id(product_id)
    home = _workshop_home()
    repository = _source_checkout_root()
    runs = home / "runs"
    run_container = runs / product_id
    new_workspace = run_container / "workspace"
    legacy_workspaces = []
    if repository is not None:
        legacy_workspaces.append(repository / "toys" / product_id)
    legacy_workspaces.append(home / "toys" / product_id)
    # WORKSHOP_HOME may itself be the source checkout.  One exact path is one
    # candidate, not an ambiguity between two names for the same directory.
    workspace_candidates = tuple(
        dict.fromkeys((new_workspace, *legacy_workspaces))
    )
    states = home / "state"
    if create:
        existing = [
            path
            for path in workspace_candidates
            if path.exists() or path.is_symlink()
        ]
        if run_container.exists() or run_container.is_symlink():
            if new_workspace not in existing:
                existing.insert(0, new_workspace)
        if existing:
            raise StateConflict("native run workspace already exists")
        if (states / product_id).exists() or (states / product_id).is_symlink():
            raise StateConflict("native run host state already exists")
        runs = _ensure_private_directory(runs, label="private runs directory")
        states = _ensure_private_directory(states, label="toy state directory")
        try:
            run_container.mkdir(mode=0o700)
        except OSError as exc:
            raise StateConflict(
                "native run container could not be created exclusively"
            ) from exc
        run_container = _existing_real_directory(
            run_container, label="native run container"
        )
        if stat.S_IMODE(run_container.stat().st_mode) != 0o700:
            raise StateConflict("native run container permissions must be 0700")
        workspace = run_container / "workspace"
        host_state = states / product_id
    else:
        present = []
        if run_container.exists() or run_container.is_symlink():
            present.append(new_workspace)
        for candidate in legacy_workspaces:
            if (
                candidate.exists() or candidate.is_symlink()
            ) and candidate not in present:
                present.append(candidate)
        if not present:
            raise StateConflict("native run workspace is unavailable")
        if len(present) != 1:
            raise StateConflict(
                "native run workspace is ambiguous across multiple layouts"
            )
        workspace = present[0]
        if workspace == new_workspace:
            runs = _existing_real_directory(runs, label="private runs directory")
            run_container = _existing_real_directory(
                run_container, label="native run container"
            )
            for path, label in (
                (runs, "private runs directory"),
                (run_container, "native run container"),
            ):
                if stat.S_IMODE(path.stat().st_mode) != 0o700:
                    raise StateConflict("%s permissions must be 0700" % label)
        else:
            legacy_parent = _existing_real_directory(
                workspace.parent, label="legacy toy projects directory"
            )
            del legacy_parent
        states = _existing_real_directory(states, label="toy state directory")
        workspace = _existing_real_directory(
            workspace, label="native run workspace"
        )
        host_state = _existing_real_directory(
            states / product_id, label="toy host-state directory"
        )
        for path, label in (
            (workspace, "native run workspace"),
            (host_state, "toy host-state directory"),
        ):
            if stat.S_IMODE(path.stat().st_mode) != 0o700:
                raise StateConflict("%s permissions must be 0700" % label)
    return NativeRunPaths(
        workspace=workspace,
        host_state=host_state,
    )


def native_run_exists(product_id: str) -> bool:
    """Return whether this id has any native-run state, including partial state."""

    product_id = _validated_product_id(product_id)
    home = Path(default_workshop_home()).expanduser()
    if not home.is_absolute():
        raise ContractError("Workshop home must be absolute")
    repository = _source_checkout_root()
    candidates = [
        home / "runs" / product_id,
        home / "toys" / product_id,
    ]
    if repository is not None:
        candidates.append(repository / "toys" / product_id)
    host_state = home / "state" / product_id
    candidates.append(host_state)
    return any(
        path.exists() or path.is_symlink()
        for path in dict.fromkeys(candidates)
    )


def _open_native_run(product_id: str) -> tuple[AgentRun, AgentRunCheckpoint]:
    paths = native_run_paths(product_id)
    run = AgentRun.open(paths.workspace, host_state_root=paths.host_state)
    return run, run.snapshot()


def _artifact_binding(artifact: AgentArtifact) -> dict[str, str]:
    return {"path": artifact.path, "sha256": artifact.sha256}


def _prepare_effort_stage_input(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    *,
    roster: InventorRoster,
    cad_gate_rejection: Optional[Mapping[str, Any]],
    make_proposal_rejection: Optional[Mapping[str, Any]],
    playtest_proposal_rejection: Optional[Mapping[str, Any]],
) -> tuple[str, Mapping[str, Any], Mapping[str, Any]]:
    """Prepare a selectable-effort stage without fabricating skipped stages."""

    effort = _checkpoint_effort(checkpoint)
    if effort is None or checkpoint.stage not in effort.enabled_stages:
        raise TransitionError("native run stage is disabled by its frozen effort")
    stage = checkpoint.stage
    blueprint = ToyBlueprint()
    normal_transition = effort.next_stage(stage)
    context: dict[str, Any] = {
        "roster": roster,
        "blueprint": blueprint,
        "effort": effort,
    }
    base: dict[str, Any] = {
        "effort": effort.name,
        "wish": {"path": "WISH.json", "sha256": checkpoint.wish_sha256},
        "wish_sha256": checkpoint.wish_sha256,
        "inventor_roster": roster.to_dict(),
        "blueprint": blueprint.to_dict(),
        "blueprint_sha256": blueprint.sha256,
    }

    if stage == "invent":
        assignment_path, invented_path = _routed_invent_contract_paths(checkpoint)
        subject_inputs: dict[str, Any] = {
            "effort": effort.name,
            "wish_sha256": checkpoint.wish_sha256,
            "inventor_roster_sha256": roster.roster_sha256,
            "blueprint_sha256": blueprint.sha256,
            "repair_round": None,
        }
        inputs: dict[str, Any] = {
            **base,
            "assignment_contract_path": assignment_path,
            "contract_path": invented_path,
        }
        prior_paths = checkpoint.stage_artifacts.get("invent")
        if prior_paths:
            if "invent" not in checkpoint.invalidated_stages:
                raise StateConflict("an effort Invent retry requires invalidation")
            (
                prior_assignment,
                prior_invented,
                prior_assignment_artifact,
                prior_invented_artifact,
                unused_binding,
            ) = _routed_creative_context(run, checkpoint, roster)
            del unused_binding
            make_revision_paths = tuple(
                artifact
                for artifact in checkpoint.stage_artifacts.get("make", ())
                if PurePosixPath(artifact.path).name
                == "invent-revision-request.json"
            )
            if make_revision_paths:
                if (
                    len(make_revision_paths) != 1
                    or not _checkpoint_allows_make_invent_revision(checkpoint)
                ):
                    raise StateConflict(
                        "routed re-Invent has an invalid Make revision capability"
                    )
                make_revision_artifact = make_revision_paths[0]
                make_revision = _read_contract(
                    run.run_root,
                    make_revision_artifact,
                    NativeMakeInventRevision,
                    label="routed Make Invent-revision request",
                )
                make_revision.assert_context(
                    prior_assignment,
                    prior_invented,
                    expected_round=checkpoint.round_index - 1,
                )
                make_revision.validate_evidence_tree(run.run_root)
                feedback = [item.to_dict() for item in make_revision.feedback]
                subject_inputs.update(
                    {
                        "repair_round": checkpoint.round_index,
                        "prior_assignment_sha256": (
                            prior_assignment.assignment_sha256
                        ),
                        "prior_invented_sha256": prior_invented.invented_sha256,
                        "prior_invented_artifact_sha256": (
                            prior_invented_artifact.sha256
                        ),
                        "make_revision_request_sha256": (
                            make_revision.revision_request_sha256
                        ),
                        "make_revision_artifact_sha256": (
                            make_revision_artifact.sha256
                        ),
                        "feedback_sha256": make_revision.feedback_sha256,
                    }
                )
                inputs.update(
                    {
                        "repair_round": checkpoint.round_index,
                        "prior_assignment": prior_assignment.to_dict(),
                        "prior_assignment_artifact": _artifact_binding(
                            prior_assignment_artifact
                        ),
                        "prior_invented": prior_invented.to_dict(),
                        "prior_invented_artifact": _artifact_binding(
                            prior_invented_artifact
                        ),
                        "make_revision_request": make_revision.to_dict(),
                        "make_revision_request_artifact": _artifact_binding(
                            make_revision_artifact
                        ),
                        "feedback": feedback,
                        "feedback_sha256": make_revision.feedback_sha256,
                    }
                )
            else:
                prior_made = _read_contract(
                    run.run_root,
                    _stage_primary(checkpoint, "make"),
                    NativeMade,
                    label="prior routed native Made contract",
                )
                prior_made.assert_context(
                    prior_assignment,
                    prior_invented,
                    expected_round=prior_made.round,
                )
                failing_playtested_artifact = _stage_primary(checkpoint, "playtest")
                failing_playtested = _read_contract(
                    run.run_root,
                    failing_playtested_artifact,
                    NativePlaytested,
                    label="failing routed native Playtested contract",
                )
                failing_playtested.assert_context(prior_made, blueprint)
                if failing_playtested.proposed_transition != "invent":
                    raise StateConflict(
                        "routed re-Invent requires concept-revision feedback"
                    )
                feedback = [item.to_dict() for item in failing_playtested.feedback]
                subject_inputs.update(
                    {
                        "repair_round": checkpoint.round_index,
                        "prior_assignment_sha256": (
                            prior_assignment.assignment_sha256
                        ),
                        "prior_invented_sha256": prior_invented.invented_sha256,
                        "prior_invented_artifact_sha256": (
                            prior_invented_artifact.sha256
                        ),
                        "failing_playtested_sha256": (
                            failing_playtested.playtested_sha256
                        ),
                        "feedback_sha256": failing_playtested.feedback_sha256,
                    }
                )
                inputs.update(
                    {
                        "repair_round": checkpoint.round_index,
                        "prior_assignment": prior_assignment.to_dict(),
                        "prior_assignment_artifact": _artifact_binding(
                            prior_assignment_artifact
                        ),
                        "prior_invented": prior_invented.to_dict(),
                        "prior_invented_artifact": _artifact_binding(
                            prior_invented_artifact
                        ),
                        "failing_playtested": failing_playtested.to_dict(),
                        "failing_playtested_artifact": _artifact_binding(
                            failing_playtested_artifact
                        ),
                        "feedback": feedback,
                        "feedback_sha256": failing_playtested.feedback_sha256,
                    }
                )
        subject = _stage_subject("invent", subject_inputs)
        context.update(
            {
                "routed_invent": True,
                "assignment_contract_path": assignment_path,
                "invent_contract_path": invented_path,
            }
        )

    elif stage == "make":
        context["make_transition"] = normal_transition
        if effort.name == "spark":
            assignment_path, invented_path = _routed_make_creative_paths(
                checkpoint.round_index
            )
            common = dict(base)
            common.update(
                {
                    "creative_source_required": True,
                    "assignment_contract_path": assignment_path,
                    "invented_contract_path": invented_path,
                }
            )
            assignment = invented = None
            context.update(
                {
                    "routed_make_creative": True,
                    "assignment_contract_path": assignment_path,
                    "invented_contract_path": invented_path,
                }
            )
        else:
            (
                assignment,
                invented,
                assignment_artifact,
                invented_artifact,
                inventor_binding,
            ) = _routed_creative_context(run, checkpoint, roster)
            context.update(
                {
                    "assignment": assignment,
                    "invented": invented,
                    "inventor_binding": inventor_binding,
                }
            )
            common = {
                **base,
                "assignment": assignment.to_dict(),
                "assignment_artifact": {
                    **_artifact_binding(assignment_artifact),
                    "assignment_sha256": assignment.assignment_sha256,
                },
                "invented": invented.to_dict(),
                "invented_artifact": {
                    **_artifact_binding(invented_artifact),
                    "invented_sha256": invented.invented_sha256,
                },
                "selected_inventor_agent": {
                    "path": assignment.selected_agent_path,
                    "sha256": assignment.selected_agent_sha256,
                    "source_manifest_sha256": (
                        assignment.selected_source_manifest_sha256
                    ),
                    "taste_sha256": assignment.selected_taste_sha256,
                },
            }
        feedback_artifact: Optional[AgentArtifact] = None
        prior = checkpoint.stage_artifacts.get("playtest")
        if prior and "playtest" in checkpoint.invalidated_stages:
            feedback_artifact = prior[0]
        subject_inputs = {
            "effort": effort.name,
            "wish_sha256": checkpoint.wish_sha256,
            "inventor_roster_sha256": roster.roster_sha256,
            "assignment_sha256": (
                assignment.assignment_sha256 if assignment is not None else None
            ),
            "invented_sha256": (
                invented.invented_sha256 if invented is not None else None
            ),
            "blueprint_sha256": blueprint.sha256,
            "round": checkpoint.round_index,
            "feedback_sha256": (
                feedback_artifact.sha256 if feedback_artifact else None
            ),
            "host_cad_gate_rejection_sha256": (
                cad_gate_rejection["rejection_sha256"]
                if cad_gate_rejection is not None
                else None
            ),
        }
        make_invent_revision_allowed = _checkpoint_allows_make_invent_revision(
            checkpoint
        )
        if make_invent_revision_allowed:
            subject_inputs["make_invent_revision_capability_sha256"] = (
                checkpoint.input_sha256s[MAKE_INVENT_REVISION_CAPABILITY_PATH]
            )
        if make_proposal_rejection is not None:
            subject_inputs["host_make_proposal_rejection_sha256"] = (
                make_proposal_rejection["rejection_sha256"]
            )
        subject = _stage_subject("make", subject_inputs)
        inputs = {
            **common,
            "round": checkpoint.round_index,
            "previous_playtest": (
                _artifact_binding(feedback_artifact)
                if feedback_artifact is not None
                else None
            ),
            "host_cad_gate_rejection": cad_gate_rejection,
            "product_root": "artifacts/make/r%04d/product"
            % checkpoint.round_index,
            "contract_path": "artifacts/make/r%04d/made.json"
            % checkpoint.round_index,
            "required_root_files": [
                "product.json",
                "assembled.step",
                "assembled.step.json",
                "assembled.stl",
            ],
        }
        if make_invent_revision_allowed:
            inputs.update(
                {
                    "invent_revision_allowed": True,
                    "invent_revision_contract_path": (
                        "artifacts/make/r%04d/invent-revision-request.json"
                        % checkpoint.round_index
                    ),
                    "invent_revision_evidence_root": (
                        "artifacts/make/r%04d/revision-evidence"
                        % checkpoint.round_index
                    ),
                }
            )
            context["make_invent_revision_allowed"] = True
        if make_proposal_rejection is not None:
            inputs["host_make_proposal_rejection"] = make_proposal_rejection

    else:
        (
            assignment,
            invented,
            assignment_artifact,
            invented_artifact,
            inventor_binding,
        ) = _routed_creative_context(run, checkpoint, roster)
        made_artifact = _stage_primary(checkpoint, "make")
        made = _read_contract(
            run.run_root,
            made_artifact,
            NativeMade,
            label="routed native Made contract",
        )
        made.assert_context(
            assignment, invented, expected_round=checkpoint.round_index
        )
        context.update(
            {
                "assignment": assignment,
                "invented": invented,
                "made": made,
                "inventor_binding": inventor_binding,
            }
        )
        common = {
            **base,
            "assignment": assignment.to_dict(),
            "assignment_artifact": {
                **_artifact_binding(assignment_artifact),
                "assignment_sha256": assignment.assignment_sha256,
            },
            "invented": invented.to_dict(),
            "invented_artifact": {
                **_artifact_binding(invented_artifact),
                "invented_sha256": invented.invented_sha256,
            },
            "made": made.to_dict(),
            "made_artifact": {
                **_artifact_binding(made_artifact),
                "made_sha256": made.made_sha256,
                "product_artifact_sha256": made.product_manifest.artifact_sha256,
                "product_root": made.product_root,
            },
            "selected_inventor_agent": {
                "path": assignment.selected_agent_path,
                "sha256": assignment.selected_agent_sha256,
                "source_manifest_sha256": assignment.selected_source_manifest_sha256,
                "taste_sha256": assignment.selected_taste_sha256,
            },
        }
        if stage == "playtest":
            subject_inputs = {
                "effort": effort.name,
                "made_sha256": made.made_sha256,
                "product_artifact_sha256": made.product_manifest.artifact_sha256,
                "blueprint_sha256": blueprint.sha256,
                "round": checkpoint.round_index,
                "host_cad_gate_rejection_sha256": (
                    cad_gate_rejection["rejection_sha256"]
                    if cad_gate_rejection is not None
                    else None
                ),
            }
            if playtest_proposal_rejection is not None:
                subject_inputs["host_playtest_proposal_rejection_sha256"] = (
                    playtest_proposal_rejection["rejection_sha256"]
                )
            subject = _stage_subject("playtest", subject_inputs)
            inputs = {
                **common,
                "round": checkpoint.round_index,
                "host_cad_gate_rejection": cad_gate_rejection,
                "required_check_ids": list(blueprint.required_playtest_checks()),
                "evidence_root": "artifacts/playtest/r%04d/evidence"
                % checkpoint.round_index,
                "contract_path": "artifacts/playtest/r%04d/playtested.json"
                % checkpoint.round_index,
            }
            if playtest_proposal_rejection is not None:
                inputs["host_playtest_proposal_rejection"] = (
                    playtest_proposal_rejection
                )
        elif stage == "release":
            release_contract = _materialized_release_contract(checkpoint)
            terminal_transition = _materialized_release_terminal_transition(checkpoint)
            normal_transition = terminal_transition
            context.update(
                {
                    "release_contract": release_contract,
                    "terminal_transition": terminal_transition,
                }
            )
            subject_inputs = {
                "effort": effort.name,
                "wish_sha256": checkpoint.wish_sha256,
                "taste_sha256": assignment.selected_taste_sha256,
                "blueprint_sha256": blueprint.sha256,
                "made_sha256": made.made_sha256,
                "product_artifact_sha256": made.product_manifest.artifact_sha256,
                "round": checkpoint.round_index,
                "release_contract": release_contract,
                "host_cad_gate_rejection_sha256": (
                    cad_gate_rejection["rejection_sha256"]
                    if cad_gate_rejection is not None
                    else None
                ),
            }
            inputs = {
                **common,
                "round": checkpoint.round_index,
                "host_cad_gate_rejection": cad_gate_rejection,
                "package_root": "artifacts/release/package",
                "contract_path": "artifacts/release/release.json",
                "release_contract": release_contract,
                "required_package_files": [
                    release_contract["manual_path"],
                    "product.json",
                ],
            }
            if release_contract.get("manual_design_evidence_path") is not None:
                inputs["required_package_files"].append(
                    release_contract["manual_design_evidence_path"]
                )
            if effort.includes("playtest"):
                playtested_artifact = _stage_primary(checkpoint, "playtest")
                playtested = _read_contract(
                    run.run_root,
                    playtested_artifact,
                    NativePlaytested,
                    label="routed native Playtested contract",
                )
                playtested.assert_context(made, blueprint)
                if playtested.verdict != "pass":
                    raise TransitionError("Release requires a passing Playtest")
                context["playtested"] = playtested
                subject_inputs.update(
                    {
                        "playtested_sha256": playtested.playtested_sha256,
                        "evidence_artifact_sha256": (
                            playtested.evidence_manifest.artifact_sha256
                        ),
                    }
                )
                inputs.update(
                    {
                        "playtested": playtested.to_dict(),
                        "playtested_artifact": {
                            **_artifact_binding(playtested_artifact),
                            "playtested_sha256": playtested.playtested_sha256,
                            "evidence_artifact_sha256": (
                                playtested.evidence_manifest.artifact_sha256
                            ),
                        },
                    }
                )
            else:
                context["playtested"] = None
                subject_inputs["playtest_status"] = DIRECT_RELEASE_PLAYTEST_STATUS
                inputs["required_package_files"].append(
                    NATIVE_RELEASE_PLAYTEST_OMISSION_PATH
                )
            subject = _stage_subject("release", subject_inputs)
        else:  # pragma: no cover - effort membership is checked above
            raise TransitionError("effort route cannot prepare this stage")

    packet = {
        "schema_version": 1,
        "kind": _STAGE_INPUT_KIND,
        "product_id": checkpoint.product_id,
        "stage": stage,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "subject_sha256": subject,
        "next_transition": normal_transition,
        "round": (
            checkpoint.round_index
            if stage in ("make", "playtest", "release")
            else None
        ),
        "max_rounds": checkpoint.max_rounds,
        "inputs": inputs,
    }
    encoded = _canonical_json_bytes(packet) + b"\n"
    if len(encoded) > _MAX_STAGE_INPUT_BYTES:
        raise ArtifactError("native effort stage input exceeded its byte limit")
    _atomic_private_write(run.run_root / _STAGE_INPUT_NAME, encoded, mode=0o400)
    return subject, packet, context


def _prepare_stage_input(
    run: AgentRun, checkpoint: AgentRunCheckpoint
) -> tuple[str, Mapping[str, Any], Mapping[str, Any]]:
    """Build the exact public input vector for the current native stage.

    The returned context mapping contains typed host values and is never
    serialized for the native session.  The packet is deliberately free of
    credentials and outside-effect receipts.
    """

    stage = checkpoint.stage
    if stage == "wish":
        raise TransitionError("%s does not use a native stage packet" % stage)
    roster = _inventor_roster(checkpoint)
    context: dict[str, Any] = {"roster": roster}
    direct_release = _checkpoint_uses_direct_release(checkpoint)
    cad_gate_rejection = _read_cad_gate_rejection(run, checkpoint)
    make_proposal_rejection = _read_make_proposal_rejection(run, checkpoint)
    make_proposal_rejection = _current_make_proposal_rejection(
        cad_gate_rejection,
        make_proposal_rejection,
    )
    playtest_proposal_rejection = _read_playtest_proposal_rejection(
        run, checkpoint
    )
    if _checkpoint_effort(checkpoint) is not None:
        return _prepare_effort_stage_input(
            run,
            checkpoint,
            roster=roster,
            cad_gate_rejection=cad_gate_rejection,
            make_proposal_rejection=make_proposal_rejection,
            playtest_proposal_rejection=playtest_proposal_rejection,
        )
    normal_transition = {
        "match": "invent",
        "invent": "make",
        "make": "release" if direct_release else "playtest",
        "playtest": "release",
        "release": "complete",
    }[stage]
    round_value: Optional[int] = (
        checkpoint.round_index
        if stage in ("make", "playtest", "release")
        else None
    )

    if stage == "match":
        blueprint = ToyBlueprint()
        subject = match_gate_subject_sha256(
            wish_sha256=checkpoint.wish_sha256,
            inventor_roster_sha256=roster.roster_sha256,
        )
        inputs: Mapping[str, Any] = {
            "wish_sha256": checkpoint.wish_sha256,
            "wish": {"path": "WISH.json", "sha256": checkpoint.wish_sha256},
            "inventor_roster": roster.to_dict(),
            "blueprint": blueprint.to_dict(),
            "blueprint_sha256": blueprint.sha256,
            "contract_path": "artifacts/match/assignment.json",
        }
    else:
        assignment_artifact = _stage_primary(checkpoint, "match")
        assignment = _read_contract(
            run.run_root,
            assignment_artifact,
            NativeMatchAssignment,
            label="native Match assignment",
        )
        assignment.assert_context(
            wish_sha256=checkpoint.wish_sha256, roster=roster
        )
        blueprint = ToyBlueprint()
        inventor_binding = _selected_inventor_binding(
            run.run_root, checkpoint, assignment
        )
        context.update(
            {
                "assignment": assignment,
                "blueprint": blueprint,
                "inventor_binding": inventor_binding,
            }
        )
        common: dict[str, Any] = {
            "wish": {"path": "WISH.json", "sha256": checkpoint.wish_sha256},
            "assignment": assignment.to_dict(),
            "assignment_artifact": {
                **_artifact_binding(assignment_artifact),
                "assignment_sha256": assignment.assignment_sha256,
            },
            "selected_inventor_agent": {
                "path": assignment.selected_agent_path,
                "sha256": assignment.selected_agent_sha256,
                "source_manifest_sha256": (
                    assignment.selected_source_manifest_sha256
                ),
                "taste_sha256": assignment.selected_taste_sha256,
            },
            "blueprint": blueprint.to_dict(),
            "blueprint_sha256": blueprint.sha256,
        }
        if stage == "invent":
            prior_invented_paths = checkpoint.stage_artifacts.get("invent")
            if prior_invented_paths:
                if "invent" not in checkpoint.invalidated_stages:
                    raise StateConflict(
                        "an Invent retry requires explicit Playtest invalidation"
                    )
                prior_invented_artifact = prior_invented_paths[0]
                prior_invented = _read_contract(
                    run.run_root,
                    prior_invented_artifact,
                    NativeInvented,
                    label="prior native Invented contract",
                )
                prior_invented.assert_context(assignment)
                prior_made_artifact = _stage_primary(checkpoint, "make")
                prior_made = _read_contract(
                    run.run_root,
                    prior_made_artifact,
                    NativeMade,
                    label="prior native Made contract",
                )
                prior_made.assert_context(
                    assignment,
                    prior_invented,
                    expected_round=prior_made.round,
                )
                failing_playtested_artifact = _stage_primary(checkpoint, "playtest")
                failing_playtested = _read_contract(
                    run.run_root,
                    failing_playtested_artifact,
                    NativePlaytested,
                    label="failing native Playtested contract",
                )
                failing_playtested.assert_context(prior_made, blueprint)
                if failing_playtested.proposed_transition != "invent":
                    raise StateConflict(
                        "re-Invent requires explicit concept-revision feedback"
                    )
                feedback = [
                    item.to_dict() for item in failing_playtested.feedback
                ]
                subject_inputs = {
                    "wish_sha256": checkpoint.wish_sha256,
                    "assignment_sha256": assignment.assignment_sha256,
                    "taste_sha256": assignment.selected_taste_sha256,
                    "blueprint_sha256": blueprint.sha256,
                    "prior_invented_artifact_sha256": (
                        prior_invented_artifact.sha256
                    ),
                    "prior_invented_sha256": prior_invented.invented_sha256,
                    "failing_playtested_artifact_sha256": (
                        failing_playtested_artifact.sha256
                    ),
                    "failing_playtested_sha256": (
                        failing_playtested.playtested_sha256
                    ),
                    "feedback_sha256": failing_playtested.feedback_sha256,
                    "repair_round": checkpoint.round_index,
                }
                subject = _stage_subject("invent", subject_inputs)
                inputs = {
                    **common,
                    "repair_round": checkpoint.round_index,
                    "prior_invented": prior_invented.to_dict(),
                    "prior_invented_artifact": {
                        **_artifact_binding(prior_invented_artifact),
                        "invented_sha256": prior_invented.invented_sha256,
                    },
                    "failing_playtested": failing_playtested.to_dict(),
                    "failing_playtested_artifact": {
                        **_artifact_binding(failing_playtested_artifact),
                        "playtested_sha256": (
                            failing_playtested.playtested_sha256
                        ),
                    },
                    "feedback": feedback,
                    "feedback_sha256": failing_playtested.feedback_sha256,
                    "contract_path": (
                        "artifacts/invent/r%04d/invented.json"
                        % checkpoint.round_index
                    ),
                }
                context.update(
                    {
                        "prior_invented": prior_invented,
                        "prior_made": prior_made,
                        "failing_playtested": failing_playtested,
                        "invent_contract_path": inputs["contract_path"],
                    }
                )
            else:
                if "invent" in checkpoint.invalidated_stages:
                    raise StateConflict(
                        "re-Invent lacks its exact prior Invented contract"
                    )
                subject = invent_gate_subject_sha256(assignment)
                inputs = {
                    **common,
                    "contract_path": "artifacts/invent/invented.json",
                }
                context["invent_contract_path"] = inputs["contract_path"]
        else:
            invented_artifact = _stage_primary(checkpoint, "invent")
            invented = _read_contract(
                run.run_root,
                invented_artifact,
                NativeInvented,
                label="native Invented contract",
            )
            invented.assert_context(assignment)
            context["invented"] = invented
            common["invented"] = invented.to_dict()
            common["invented_artifact"] = {
                **_artifact_binding(invented_artifact),
                "invented_sha256": invented.invented_sha256,
            }
            if stage in ("make", "playtest", "release"):
                if stage == "make":
                    context["make_transition"] = normal_transition
                    feedback_artifact: Optional[AgentArtifact] = None
                    prior = checkpoint.stage_artifacts.get("playtest")
                    if prior and "playtest" in checkpoint.invalidated_stages:
                        feedback_artifact = prior[0]
                    subject_inputs = {
                        "wish_sha256": checkpoint.wish_sha256,
                        "assignment_sha256": assignment.assignment_sha256,
                        "taste_sha256": assignment.selected_taste_sha256,
                        "blueprint_sha256": blueprint.sha256,
                        "invented_sha256": invented.invented_sha256,
                        "round": checkpoint.round_index,
                        "feedback_sha256": (
                            feedback_artifact.sha256 if feedback_artifact else None
                        ),
                        "host_cad_gate_rejection_sha256": (
                            cad_gate_rejection["rejection_sha256"]
                            if cad_gate_rejection is not None
                            else None
                        ),
                    }
                    if make_proposal_rejection is not None:
                        # Omitting this field before the first rejection keeps
                        # pre-upgrade/frozen Make subjects byte-compatible.
                        subject_inputs["host_make_proposal_rejection_sha256"] = (
                            make_proposal_rejection["rejection_sha256"]
                        )
                    subject = _stage_subject("make", subject_inputs)
                    inputs = {
                        **common,
                        "round": checkpoint.round_index,
                        "previous_playtest": (
                            _artifact_binding(feedback_artifact)
                            if feedback_artifact is not None
                            else None
                        ),
                        "host_cad_gate_rejection": cad_gate_rejection,
                        "product_root": "artifacts/make/r%04d/product"
                        % checkpoint.round_index,
                        "contract_path": "artifacts/make/r%04d/made.json"
                        % checkpoint.round_index,
                        "required_root_files": [
                            "product.json",
                            "assembled.step",
                            "assembled.step.json",
                            "assembled.stl",
                        ],
                    }
                    if make_proposal_rejection is not None:
                        inputs["host_make_proposal_rejection"] = (
                            make_proposal_rejection
                        )
                else:
                    made_artifact = _stage_primary(checkpoint, "make")
                    made = _read_contract(
                        run.run_root,
                        made_artifact,
                        NativeMade,
                        label="native Made contract",
                    )
                    made.assert_context(
                        assignment, invented, expected_round=checkpoint.round_index
                    )
                    context["made"] = made
                    common["made"] = made.to_dict()
                    common["made_artifact"] = {
                        **_artifact_binding(made_artifact),
                        "made_sha256": made.made_sha256,
                        "product_artifact_sha256": made.product_manifest.artifact_sha256,
                        "product_root": made.product_root,
                    }
                    if stage == "playtest":
                        subject_inputs = {
                            "made_sha256": made.made_sha256,
                            "product_artifact_sha256": made.product_manifest.artifact_sha256,
                            "blueprint_sha256": blueprint.sha256,
                            "round": checkpoint.round_index,
                            "host_cad_gate_rejection_sha256": (
                                cad_gate_rejection["rejection_sha256"]
                                if cad_gate_rejection is not None
                                else None
                            ),
                        }
                        if playtest_proposal_rejection is not None:
                            subject_inputs[
                                "host_playtest_proposal_rejection_sha256"
                            ] = playtest_proposal_rejection["rejection_sha256"]
                        subject = _stage_subject("playtest", subject_inputs)
                        inputs = {
                            **common,
                            "round": checkpoint.round_index,
                            "host_cad_gate_rejection": cad_gate_rejection,
                            "required_check_ids": list(
                                blueprint.required_playtest_checks()
                            ),
                            "evidence_root": "artifacts/playtest/r%04d/evidence"
                            % checkpoint.round_index,
                            "contract_path": "artifacts/playtest/r%04d/playtested.json"
                            % checkpoint.round_index,
                        }
                        if playtest_proposal_rejection is not None:
                            inputs["host_playtest_proposal_rejection"] = (
                                playtest_proposal_rejection
                            )
                    else:
                        release_contract = _materialized_release_contract(checkpoint)
                        context["release_contract"] = release_contract
                        terminal_transition = _materialized_release_terminal_transition(
                            checkpoint
                        )
                        context["terminal_transition"] = terminal_transition
                        normal_transition = terminal_transition
                        subject_inputs: dict[str, Any] = {
                            "wish_sha256": checkpoint.wish_sha256,
                            "taste_sha256": assignment.selected_taste_sha256,
                            "blueprint_sha256": blueprint.sha256,
                            "made_sha256": made.made_sha256,
                            "product_artifact_sha256": made.product_manifest.artifact_sha256,
                            "round": checkpoint.round_index,
                            "release_contract": release_contract,
                            "host_cad_gate_rejection_sha256": (
                                cad_gate_rejection["rejection_sha256"]
                                if cad_gate_rejection is not None
                                else None
                            ),
                        }
                        inputs = {
                            **common,
                            "round": checkpoint.round_index,
                            "host_cad_gate_rejection": cad_gate_rejection,
                            "package_root": "artifacts/release/package",
                            "contract_path": "artifacts/release/release.json",
                            "release_contract": release_contract,
                            "required_package_files": [
                                release_contract["manual_path"],
                                "product.json",
                            ],
                        }
                        if (
                            release_contract.get("manual_design_evidence_path")
                            is not None
                        ):
                            inputs["required_package_files"].append(
                                release_contract["manual_design_evidence_path"]
                            )
                        if direct_release:
                            context["playtested"] = None
                            subject_inputs["playtest_status"] = (
                                DIRECT_RELEASE_PLAYTEST_STATUS
                            )
                            inputs["required_package_files"].append(
                                NATIVE_RELEASE_PLAYTEST_OMISSION_PATH
                            )
                        else:
                            playtested_artifact = _stage_primary(
                                checkpoint, "playtest"
                            )
                            playtested = _read_contract(
                                run.run_root,
                                playtested_artifact,
                                NativePlaytested,
                                label="native Playtested contract",
                            )
                            playtested.assert_context(made, blueprint)
                            if playtested.verdict != "pass":
                                raise TransitionError(
                                    "Release requires a passing Playtest"
                                )
                            context["playtested"] = playtested
                            subject_inputs.update(
                                {
                                    "playtested_sha256": playtested.playtested_sha256,
                                    "evidence_artifact_sha256": (
                                        playtested.evidence_manifest.artifact_sha256
                                    ),
                                }
                            )
                            inputs.update(
                                {
                                    "playtested": playtested.to_dict(),
                                    "playtested_artifact": {
                                        **_artifact_binding(playtested_artifact),
                                        "playtested_sha256": playtested.playtested_sha256,
                                        "evidence_artifact_sha256": (
                                            playtested.evidence_manifest.artifact_sha256
                                        ),
                                    },
                                }
                            )
                        subject = _stage_subject("release", subject_inputs)

    packet = {
        "schema_version": 1,
        "kind": _STAGE_INPUT_KIND,
        "product_id": checkpoint.product_id,
        "stage": stage,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "subject_sha256": subject,
        "next_transition": normal_transition,
        "round": round_value,
        "max_rounds": checkpoint.max_rounds,
        "inputs": inputs,
    }
    encoded = _canonical_json_bytes(packet) + b"\n"
    if len(encoded) > _MAX_STAGE_INPUT_BYTES:
        raise ArtifactError("native stage input exceeded its byte limit")
    _atomic_private_write(
        run.run_root / _STAGE_INPUT_NAME, encoded, mode=0o400
    )
    return subject, packet, context


def _uses_dynamic_deep_profile(checkpoint: AgentRunCheckpoint) -> bool:
    return (
        checkpoint.manager_id == DEFAULT_MANAGER_ID
        and checkpoint.effort in ("forge", "quest")
        and (
            DEEP_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
            or DEEP_ECONOMICS_V4_CAPABILITY_PATH in checkpoint.input_sha256s
            or DEEP_ECONOMICS_V3_CAPABILITY_PATH in checkpoint.input_sha256s
        )
    )


def _native_launcher(
    checkpoint: AgentRunCheckpoint,
    *,
    initial_make_proof_boundary: bool = False,
    recoverable_continuation: bool = False,
) -> NativeSessionLauncher:
    """Construct the frozen Manager launcher.

    Codex stays constructed here so existing host tests can patch the concrete
    class without going through the registry. Other Managers load by id. New
    Marked Spark runs use Codex's low economics profile. Marked Forge and Quest
    v5, v4, and v3 runs shape reasoning and turn boundaries while
    binding their whole frozen profile to one persistent session. Deep-v2
    retains its effective all-high session binding; deep-v1 retains its
    historical all-high profile.
    Older runs lack those markers and retain their historical profile on resume.
    """

    if checkpoint.manager_id == DEFAULT_MANAGER_ID:
        if (
            checkpoint.effort in ("forge", "quest")
            and DEEP_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
        ):
            if checkpoint.stage == "invent":
                reasoning_effort = (
                    "medium" if recoverable_continuation else "high"
                )
                timeout_seconds = (
                    DEEP_V5_INVENT_RECOVERY_TIMEOUT_SECONDS
                    if recoverable_continuation
                    else DEEP_V5_INITIAL_INVENT_TIMEOUT_SECONDS
                )
            elif checkpoint.stage == "make":
                reasoning_effort = (
                    "medium" if initial_make_proof_boundary else "high"
                )
                timeout_seconds = (
                    DEEP_V5_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS
                    if initial_make_proof_boundary
                    else DEEP_NATIVE_TURN_TIMEOUT_SECONDS
                )
            else:
                reasoning_effort = "medium"
                timeout_seconds = DEEP_NATIVE_TURN_TIMEOUT_SECONDS
            return CodexNativeSessionLauncher(
                reasoning_effort=reasoning_effort,
                auto_compact_token_limit=DEEP_AUTO_COMPACT_TOKEN_LIMIT,
                runtime_profile_sha256=checkpoint.input_sha256s[
                    DEEP_ECONOMICS_CAPABILITY_PATH
                ],
                timeout_seconds=timeout_seconds,
            )
        if (
            checkpoint.effort in ("forge", "quest")
            and DEEP_ECONOMICS_V4_CAPABILITY_PATH in checkpoint.input_sha256s
        ):
            return CodexNativeSessionLauncher(
                reasoning_effort=(
                    "high" if checkpoint.stage in ("invent", "make") else "medium"
                ),
                auto_compact_token_limit=(
                    DEEP_MAKE_AUTO_COMPACT_TOKEN_LIMIT
                    if checkpoint.stage == "make"
                    else DEEP_AUTO_COMPACT_TOKEN_LIMIT
                ),
                runtime_profile_sha256=checkpoint.input_sha256s[
                    DEEP_ECONOMICS_V4_CAPABILITY_PATH
                ],
                timeout_seconds=(
                    DEEP_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS
                    if checkpoint.stage == "make" and initial_make_proof_boundary
                    else DEEP_NATIVE_TURN_TIMEOUT_SECONDS
                ),
            )
        if (
            checkpoint.effort in ("forge", "quest")
            and DEEP_ECONOMICS_V3_CAPABILITY_PATH in checkpoint.input_sha256s
        ):
            return CodexNativeSessionLauncher(
                reasoning_effort=(
                    "high" if checkpoint.stage == "invent" else "medium"
                ),
                auto_compact_token_limit=DEEP_AUTO_COMPACT_TOKEN_LIMIT,
                runtime_profile_sha256=checkpoint.input_sha256s[
                    DEEP_ECONOMICS_V3_CAPABILITY_PATH
                ],
                timeout_seconds=(
                    DEEP_INITIAL_MAKE_PROOF_TIMEOUT_SECONDS
                    if checkpoint.stage == "make" and initial_make_proof_boundary
                    else DEEP_NATIVE_TURN_TIMEOUT_SECONDS
                ),
            )
        if (
            checkpoint.effort in ("forge", "quest")
            and DEEP_ECONOMICS_V2_CAPABILITY_PATH in checkpoint.input_sha256s
        ):
            return CodexNativeSessionLauncher(
                # V2 bound the first stage's exact turn configuration to the
                # persistent thread before stage-shaped resume was supported.
                # Keep its effective all-high policy so a stopped historical
                # run can resume without same-version runtime-policy drift.
                reasoning_effort="high",
                auto_compact_token_limit=DEEP_AUTO_COMPACT_TOKEN_LIMIT,
                timeout_seconds=DEEP_NATIVE_TURN_TIMEOUT_SECONDS,
            )
        if (
            checkpoint.effort in ("forge", "quest")
            and DEEP_ECONOMICS_V1_CAPABILITY_PATH in checkpoint.input_sha256s
        ):
            return CodexNativeSessionLauncher(
                reasoning_effort="high",
                auto_compact_token_limit=DEEP_V1_AUTO_COMPACT_TOKEN_LIMIT,
                timeout_seconds=DEEP_NATIVE_TURN_TIMEOUT_SECONDS,
            )
        if (
            checkpoint.effort == "spark"
            and SPARK_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
        ):
            return CodexNativeSessionLauncher(
                reasoning_effort="low",
                auto_compact_token_limit=SPARK_AUTO_COMPACT_TOKEN_LIMIT,
                timeout_seconds=SPARK_NATIVE_TURN_TIMEOUT_SECONDS,
            )
        if (
            checkpoint.effort == "spark"
            and SPARK_ECONOMICS_V2_CAPABILITY_PATH in checkpoint.input_sha256s
        ):
            return CodexNativeSessionLauncher(
                reasoning_effort="low",
                auto_compact_token_limit=SPARK_AUTO_COMPACT_TOKEN_LIMIT,
            )
        reasoning_effort = (
            "low"
            if checkpoint.effort == "spark"
            and SPARK_ECONOMICS_V1_CAPABILITY_PATH in checkpoint.input_sha256s
            else "high"
        )
        return CodexNativeSessionLauncher(reasoning_effort=reasoning_effort)
    return manager_launcher(checkpoint.manager_id)


def _native_turn_limit(checkpoint: AgentRunCheckpoint) -> int:
    """Return the per-invocation turn cap frozen into this Manager run."""

    if (
        checkpoint.manager_id == DEFAULT_MANAGER_ID
        and checkpoint.effort in ("forge", "quest")
        and (
            DEEP_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
            or DEEP_ECONOMICS_V4_CAPABILITY_PATH in checkpoint.input_sha256s
            or DEEP_ECONOMICS_V3_CAPABILITY_PATH in checkpoint.input_sha256s
            or DEEP_ECONOMICS_V2_CAPABILITY_PATH in checkpoint.input_sha256s
        )
    ):
        return DEEP_NATIVE_TURN_LIMIT
    if (
        checkpoint.manager_id == DEFAULT_MANAGER_ID
        and checkpoint.effort in ("forge", "quest")
        and DEEP_ECONOMICS_V1_CAPABILITY_PATH in checkpoint.input_sha256s
    ):
        return DEEP_V1_NATIVE_TURN_LIMIT
    return _MAX_NATIVE_TURNS


def _deep_make_critical_path_prompt(
    checkpoint: AgentRunCheckpoint,
    *,
    proof_boundary: bool = True,
) -> str:
    """Return the versioned first-proof instruction for an initial Make turn."""

    if not (
        checkpoint.stage == "make"
        and checkpoint.effort in ("forge", "quest")
        and (
            DEEP_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
            or DEEP_ECONOMICS_V4_CAPABILITY_PATH in checkpoint.input_sha256s
            or DEEP_ECONOMICS_V3_CAPABILITY_PATH in checkpoint.input_sha256s
            or DEEP_ECONOMICS_V2_CAPABILITY_PATH in checkpoint.input_sha256s
        )
    ):
        return ""
    if (
        DEEP_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
        and not proof_boundary
    ):
        return (
            " The checkpoint-bound v5 proof marker is already valid. Do not "
            "rewrite it, repeat early exploration, or restart the proof. "
            "Reuse the exact proof source and parameters, persist the "
            "smallest complete product baseline, finish print preflight and "
            "the final hash-bound blind review, make at most one focused "
            "repair, run the integrated verifier once, and invoke the Make "
            "finalizer. Only agent-outcome.json completes this Goal."
        )
    prompt = (
        "\n\nThis run uses the frozen deep-economics critical path. "
        "Your first Make deliverable must be the smallest exact causal "
        "or kinematic proof plus neutral held/signature blockout renders, "
        "saved under the declared CAD project at review/early-proof/. "
        "Create, run, inspect, and record that proof before authoring the "
        "complete part tree or detailing final geometry. Do not batch-write "
        "the whole product first. If the proof fails, simplify or repair "
        "the relationship immediately. Reuse the passing proof source in "
        "the final product and preserve the proof files in the product tree."
    )
    if (
        DEEP_ECONOMICS_CAPABILITY_PATH not in checkpoint.input_sha256s
        and DEEP_ECONOMICS_V4_CAPABILITY_PATH not in checkpoint.input_sha256s
    ):
        return prompt
    prompt += (
        " Before treating the held/signature blockout as passing, ask one "
        "independent native visual critic to inspect only those exact images "
        "without the Wish or concept. Record its unprompted object, form, "
        "control, and relationship read. Then reveal the Wish and concept, "
        "compare every positive and negative held-form requirement, and fail "
        "the proof on any generic, plaque-like, box-like, or exposed-mechanism "
        "reading. Repair and rerender the proof before expanding final parts."
    )
    if DEEP_ECONOMICS_CAPABILITY_PATH not in checkpoint.input_sha256s:
        return prompt
    return prompt + (
        " This v5 proof turn is action-only. After reading the mandatory root "
        "instructions and current-stage reference once, do not enumerate or "
        "reread skill trees, open optional CAD references, invoke --help, or "
        "delegate before a working proof source exists. The materialized CAD "
        "commands are exactly .agents/skills/cad/scripts/gen <source.step.py> "
        "--write, .agents/skills/cad/scripts/export <source.step> --stl, and "
        ".agents/skills/cad/scripts/render_product <source.stl> -o "
        "<cad-project>/review/early-proof/held.png --motion-sheet "
        "<cad-project>/review/early-proof/signature.png "
        "--motion-angles=-12,0,12. Replace bracketed paths from STAGE.json, "
        "write source first, then run only those commands. Once exact proof "
        "source, results, held/signature images, "
        "and the blind review are durable under review/early-proof/, write "
        "%s as canonical JSON containing exactly {\"checkpoint_sha256\":\"%s\","
        "\"kind\":\"autonomous-workshop.make-proof-ready\","
        "\"schema_version\":1} followed by one newline. The host uses that "
        "marker only to "
        "end this proof turn and resume the same Make Goal at high reasoning; "
        "it does not advance or waive the Make gate."
        % (_MAKE_PROOF_READY_NAME, checkpoint.checkpoint_sha256)
    )


def _deep_make_recovery_prompt(
    checkpoint: AgentRunCheckpoint,
    *,
    proof_boundary: bool = True,
) -> str:
    """Return the versioned proof-review instruction for Make recovery."""

    if not (
        checkpoint.stage == "make"
        and checkpoint.effort in ("forge", "quest")
        and (
            DEEP_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
            or DEEP_ECONOMICS_V4_CAPABILITY_PATH in checkpoint.input_sha256s
        )
    ):
        return ""
    if (
        DEEP_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
        and not proof_boundary
    ):
        return (
            " The v5 proof marker remains valid, so this is final-product "
            "recovery. Do not rewrite the marker, reread optional references, "
            "or restart the proof. Reuse the durable proof and complete only "
            "the remaining baseline, preflight, final renders and review, "
            "single integrated verification, and Make finalizer work."
        )
    prompt = (
        " Before expanding the final part tree, complete the frozen "
        "early-proof blind review: one independent native critic sees "
        "only the exact held/signature blockout images first, records "
        "its unprompted read, then receives the Wish and concept and "
        "checks every positive and negative held-form constraint. A "
        "generic, box-like, plaque-like, or exposed-mechanism reading "
        "fails the proof and must be repaired now. After a passing "
        "proof, persist the smallest complete product source "
        "immediately and keep all later work on that one baseline."
    )
    if DEEP_ECONOMICS_CAPABILITY_PATH not in checkpoint.input_sha256s:
        return prompt
    return prompt + (
        " This proof boundary still has no valid v5 ready marker. Do not "
        "survey tools, invoke --help, reread instructions, or delegate. "
        "Write and run the smallest proof source now. After the proof and "
        "blind review files exist, write %s with the exact checkpoint-bound "
        "canonical JSON specified in the initial Make instruction."
        % _MAKE_PROOF_READY_NAME
    )


def _deep_invent_recovery_prompt(checkpoint: AgentRunCheckpoint) -> str:
    """Return the frozen v5 decisive Invent recovery instruction."""

    if not (
        checkpoint.stage == "invent"
        and checkpoint.effort in ("forge", "quest")
        and DEEP_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
    ):
        return ""
    return (
        " Do not restart roster comparison, research, exploration, or "
        "subagent work. If the routed Invent source already exists, validate "
        "that one source and invoke the Invent finalizer immediately. If it "
        "does not exist, select the strongest current concept, write one "
        "compact complete source, and finalize it. Optional refinement is "
        "strictly lower priority than sealing the current viable concept."
    )


def _make_proof_ready_path(paths: NativeRunPaths) -> Path:
    return paths.workspace / _MAKE_PROOF_READY_NAME


def _make_proof_ready(
    paths: NativeRunPaths,
    checkpoint: AgentRunCheckpoint,
) -> bool:
    """Validate the untrusted v5 turn marker without treating it as evidence."""

    if not (
        checkpoint.stage == "make"
        and checkpoint.effort in ("forge", "quest")
        and DEEP_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
    ):
        return False
    path = _make_proof_ready_path(paths)
    try:
        before = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise StateConflict("Make proof turn marker cannot be inspected") from exc
    if path.is_symlink() or not stat.S_ISREG(before.st_mode):
        raise StateConflict("Make proof turn marker must be a regular file")
    try:
        content = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise StateConflict("Make proof turn marker cannot be read") from exc
    stable = (
        1 <= len(content) <= 1_024
        and (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        == (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
    )
    expected = {
        "schema_version": 1,
        "kind": "autonomous-workshop.make-proof-ready",
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
    }
    valid = False
    if stable:
        try:
            marker = _strict_json_bytes(content, label="Make proof turn marker")
        except ContractError:
            marker = None
        valid = (
            marker == expected
            and content == _canonical_json_bytes(expected) + b"\n"
        )
    if valid:
        return True
    try:
        path.unlink()
    except OSError as exc:
        raise StateConflict("invalid Make proof turn marker cannot be removed") from exc
    return False


def _launcher_call(
    launcher: NativeSessionLauncher,
    method: str,
    *,
    checkpoint: AgentRunCheckpoint,
    paths: NativeRunPaths,
    unfinished_continuation: bool = False,
    recoverable_continuation: bool = False,
    make_proof_boundary: bool = False,
    activity_observer: Optional[Callable[[str], None]] = None,
) -> Any:
    runtime = manager_spec(checkpoint.manager_id)
    prompt = native_stage_prompt(checkpoint.stage)
    v5_make_phase = (
        checkpoint.stage == "make"
        and DEEP_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
    )
    if (
        not unfinished_continuation
        and not recoverable_continuation
    ) or v5_make_phase:
        prompt += _deep_make_critical_path_prompt(
            checkpoint,
            proof_boundary=make_proof_boundary,
        )
    if unfinished_continuation:
        prompt += (
            "\n\nYour previous native turn returned without "
            "agent-outcome.json. The active Goal is not complete. Continue "
            "the same Goal from the exact current files and STAGE.json, run "
            "the required stage finalizer, and return only after it writes "
            "agent-outcome.json."
        )
    if recoverable_continuation:
        prompt += (
            "\n\nThe immediately previous native turn ended at the host's "
            "timeout or provider-transport recovery boundary. Continue the "
            "same active Goal from the exact existing files and STAGE.json; "
            "do not restart broad exploration. Inspect and reuse completed "
            "work before launching anything new. Keep the root Manager on "
            "the critical path and do not make finalization depend on a "
            "child agent. Run only the remaining essential deterministic "
            "checks, repair concrete failures, invoke the current stage "
            "finalizer as soon as its contract is satisfied, and return "
            "after it writes agent-outcome.json."
        )
        prompt += _deep_make_recovery_prompt(
            checkpoint,
            proof_boundary=make_proof_boundary,
        )
        prompt += _deep_invent_recovery_prompt(checkpoint)
    arguments = {
        "product_id": checkpoint.product_id,
        "wish_sha256": checkpoint.wish_sha256,
        "constitution_sha256": materialized_agent_instructions_sha256(checkpoint),
        "run_root": paths.workspace,
        "host_state_root": paths.host_state,
        "prompt": prompt,
        "activity_observer": activity_observer,
        "finalization_marker": (
            _make_proof_ready_path(paths)
            if make_proof_boundary
            else paths.workspace / _AGENT_OUTCOME_NAME
        ),
    }
    try:
        return getattr(launcher, method)(**arguments)
    except (CodexRecoverableInvocationError, NativeManagerRecoverableError) as exc:
        raise _RecoverableNativeTurn(
            "native %s session did not complete: %s" % (runtime.display_name, exc)
        ) from None
    except (CodexInvocationError, NativeManagerInvocationError) as exc:
        raise WorkshopError(
            "native %s session did not complete: %s" % (runtime.display_name, exc)
        ) from None


def _validated_activity_observer(
    observer: Optional[Callable[[str], None]],
) -> Optional[Callable[[str], None]]:
    if observer is not None and not callable(observer):
        raise ContractError("native run activity observer must be callable")
    return observer


def _validated_timing_observer(
    observer: Optional[WishRunTimingObserver],
) -> Optional[WishRunTimingObserver]:
    if observer is not None and not callable(observer):
        raise ContractError("Wish run timing observer must be callable")
    return observer


def _combined_activity_observer(
    tracker: _NativeProgressTracker,
    observer: Optional[Callable[[str], None]],
) -> Callable[[str], None]:
    """Persist and optionally surface only host-selected activity classes.

    The native launcher normally isolates this callback on its bounded progress
    queue. Keep the fan-out independently failure-safe as well so a future
    adapter or deterministic fake cannot turn presentation telemetry into
    lifecycle authority.
    """

    def observe(activity: str) -> None:
        if activity not in SAFE_NATIVE_ACTIVITY_CLASSES:
            return
        tracker.observe(activity)
        if observer is None:
            return
        try:
            observer(activity)
        except Exception:
            return

    return observe


def _host_evidence_sha256(value: Mapping[str, Any]) -> str:
    return _sha256(_canonical_json_bytes(dict(value)))


def _advance_validated_wish(run: AgentRun) -> AgentRunCheckpoint:
    checkpoint = run.snapshot()
    if checkpoint.stage != "wish" or checkpoint.status != "active":
        raise TransitionError("native Wish checkpoint is not ready for validation")
    source = run.run_root / "WISH.json"
    content = source.read_bytes()
    if _sha256(content) != checkpoint.wish_sha256:
        raise StateConflict("materialized Wish differs from the run binding")
    relative = "artifacts/wish/wish.json"
    target = run.run_root / relative
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        descriptor = os.open(
            str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
    except OSError as exc:
        raise StateConflict("validated Wish artifact already exists") from exc
    try:
        written = 0
        while written < len(content):
            written += os.write(descriptor, content[written:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    artifact = AgentArtifact(relative, checkpoint.wish_sha256)
    outcome = AgentOutcome(
        stage="wish",
        status="ready",
        artifacts=(artifact,),
        proposed_transition=_checkpoint_next_stage(checkpoint, "wish"),
    )
    evidence = {
        "schema_version": 1,
        "kind": "autonomous-workshop.wish-gate-evidence",
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "wish_sha256": checkpoint.wish_sha256,
        "canonical": True,
        "product_id_bound": True,
    }
    gate = DeterministicGateReceipt(
        stage="wish",
        gate_id="wish.contract-v1",
        passed=True,
        subject_sha256=checkpoint.wish_sha256,
        outcome_sha256=outcome.sha256,
        evidence_sha256=_host_evidence_sha256(evidence),
    )
    gates = run.host_state_root / "gates"
    gates.mkdir(mode=0o700, exist_ok=True)
    _write_private_json(gates / "0000-wish.json", evidence)
    return run.apply_outcome(outcome, gate=gate)


def _authorization_path(paths: NativeRunPaths) -> Path:
    return paths.host_state / _AUTHORIZATION_NAME


def _record_authorization(
    paths: NativeRunPaths,
    *,
    product_id: str,
    publish_requested: bool,
    create: bool,
    github_publish_requested: bool = False,
) -> Mapping[str, Any]:
    path = _authorization_path(paths)
    current = False
    current_github = False
    if path.exists() or path.is_symlink():
        try:
            identity = path.lstat()
            content = path.read_bytes()
        except OSError as exc:
            raise StateConflict("run authorization is unavailable") from exc
        if (
            path.is_symlink()
            or not stat.S_ISREG(identity.st_mode)
            or stat.S_IMODE(identity.st_mode) != 0o600
        ):
            raise StateConflict("run authorization must be a private regular file")
        value = _strict_json_bytes(content, label="run authorization")
        legacy_expected = {
            "schema_version",
            "kind",
            "product_id",
            "publish_requested",
        }
        current_expected = legacy_expected | {"github_publish_requested"}
        if (
            set(value) not in (legacy_expected, current_expected)
            or value["schema_version"] not in (1, 2)
            or (value["schema_version"] == 1 and set(value) != legacy_expected)
            or (value["schema_version"] == 2 and set(value) != current_expected)
            or value["kind"] != _AUTHORIZATION_KIND
            or value["product_id"] != product_id
            or type(value["publish_requested"]) is not bool
            or (
                value["schema_version"] == 2
                and type(value["github_publish_requested"]) is not bool
            )
        ):
            raise StateConflict("run authorization is invalid")
        current = value["publish_requested"]
        current_github = (
            value["github_publish_requested"]
            if value["schema_version"] == 2
            else False
        )
    elif not create:
        raise StateConflict("run authorization is missing")
    value = {
        "schema_version": 2,
        "kind": _AUTHORIZATION_KIND,
        "product_id": product_id,
        "publish_requested": bool(current or publish_requested),
        "github_publish_requested": bool(
            current_github or github_publish_requested
        ),
    }
    if (
        create
        or value["publish_requested"] != current
        or value["github_publish_requested"] != current_github
    ):
        _write_private_json(path, value)
    return value


def _github_publication_requested(run: AgentRun) -> bool:
    authorization = _record_authorization(
        NativeRunPaths(run.run_root, run.host_state_root),
        product_id=run.snapshot().product_id,
        publish_requested=False,
        github_publish_requested=False,
        create=False,
    )
    return authorization["github_publish_requested"] is True


def _ready_contract_artifact(
    proposal: AgentOutcomeProposal,
    *,
    stage: str,
    transitions: Sequence[str],
    path: str,
) -> AgentArtifact:
    outcome = proposal.outcome
    if (
        outcome.stage != stage
        or outcome.status != "ready"
        or outcome.proposed_transition not in tuple(transitions)
        or outcome.needs
        or len(outcome.artifacts) != 1
        or outcome.artifacts[0].path != path
    ):
        raise ContractError("%s outcome is not the canonical stage proposal" % stage)
    return outcome.artifacts[0]


def _manifest_agent_artifacts(
    prefix: str, manifest: Any
) -> tuple[AgentArtifact, ...]:
    return tuple(
        AgentArtifact("%s/%s" % (prefix, entry.path), entry.sha256)
        for entry in manifest.entries
    )


def _evaluate_make_invent_revision_stage(
    proposal: AgentOutcomeProposal,
    *,
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    subject_sha256: str,
    context: Mapping[str, Any],
) -> tuple[StageGateDecision, tuple[AgentArtifact, ...]]:
    """Verify exact contradiction evidence without judging its authored prose."""

    if context.get("make_invent_revision_allowed") is not True:
        raise StateConflict(
            "Make Invent revision is absent from this run's frozen protocol"
        )
    if checkpoint.round_index >= checkpoint.max_rounds:
        raise TransitionError("Invent-Make-Playtest round budget is exhausted")
    contract_path = (
        "artifacts/make/r%04d/invent-revision-request.json"
        % checkpoint.round_index
    )
    source_path = (
        "artifacts/make/r%04d/invent-revision-source.json"
        % checkpoint.round_index
    )
    outcome = proposal.outcome
    if (
        outcome.stage != "make"
        or outcome.status != "ready"
        or outcome.proposed_transition != "invent"
        or outcome.needs
        or tuple(item.path for item in outcome.artifacts)
        != (contract_path, source_path)
    ):
        raise ContractError(
            "Make Invent revision must contain its exact request and authored source"
        )
    artifact = outcome.artifacts[0]
    request = _read_contract(
        run.run_root,
        artifact,
        NativeMakeInventRevision,
        label="Make Invent-revision request",
    )
    request.assert_context(
        context["assignment"],
        context["invented"],
        expected_round=checkpoint.round_index,
    )
    canonical = request.validate_evidence_tree(run.run_root)
    additional = _manifest_agent_artifacts(
        request.evidence_root, request.evidence_manifest
    )
    evidence = StageGateEvidence(
        stage="make",
        gate_id="make.invent-revision-v1",
        validator_version="1.0.0",
        passed=False,
        checkpoint_sha256=checkpoint.checkpoint_sha256,
        subject_sha256=subject_sha256,
        outcome_sha256=proposal.outcome.sha256,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
        checks={
            "revision_request_sha256": request.revision_request_sha256,
            "feedback_sha256": request.feedback_sha256,
            "feedback_count": len(request.feedback),
            "evidence_artifact_sha256": canonical.artifact_sha256,
            "evidence_tree_rehashed": True,
            "upstream_bindings_valid": True,
            "round_budget_available": True,
        },
    )
    return StageGateDecision(evidence=evidence, transition="invent"), additional


def _evaluate_make_stage(
    proposal: AgentOutcomeProposal,
    *,
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    subject_sha256: str,
    context: Mapping[str, Any],
) -> tuple[StageGateDecision, tuple[AgentArtifact, ...]]:
    if proposal.outcome.proposed_transition == "invent":
        return _evaluate_make_invent_revision_stage(
            proposal,
            run=run,
            checkpoint=checkpoint,
            subject_sha256=subject_sha256,
            context=context,
        )
    contract_path = "artifacts/make/r%04d/made.json" % checkpoint.round_index
    transition = context.get("make_transition")
    if transition not in ("playtest", "release"):
        raise StateConflict("Make transition is not bound to the run protocol")
    try:
        if context.get("routed_make_creative") is True:
            outcome = proposal.outcome
            assignment_path = context["assignment_contract_path"]
            invented_path = context["invented_contract_path"]
            if (
                outcome.stage != "make"
                or outcome.status != "ready"
                or outcome.proposed_transition != transition
                or outcome.needs
                or tuple(item.path for item in outcome.artifacts)
                != (contract_path, assignment_path, invented_path)
            ):
                raise ContractError(
                    "Spark Make outcome must contain exact Made, assignment, and Invented contracts"
                )
            artifact, assignment_artifact, invented_artifact = outcome.artifacts
            assignment = _read_contract(
                run.run_root,
                assignment_artifact,
                NativeMatchAssignment,
                label="Spark native Match assignment",
            )
            assignment.assert_context(
                wish_sha256=checkpoint.wish_sha256,
                roster=context["roster"],
            )
            invented = _read_contract(
                run.run_root,
                invented_artifact,
                NativeInvented,
                label="Spark native Invented contract",
            )
            invented.assert_context(assignment)
        else:
            artifact = _ready_contract_artifact(
                proposal,
                stage="make",
                transitions=(transition,),
                path=contract_path,
            )
            assignment = context["assignment"]
            invented = context["invented"]
        made = _read_contract(
            run.run_root, artifact, NativeMade, label="native Made contract"
        )
        made.assert_context(
            assignment, invented, expected_round=checkpoint.round_index
        )
        canonical = made.validate_product_tree(run.run_root)
        additional = _manifest_agent_artifacts(
            made.product_root, made.product_manifest
        )
    except (ArtifactError, ContractError) as error:
        # This boundary covers only bytes and bindings authored by the Make
        # proposal. StateConflict is a separate hierarchy and the trusted CAD
        # verifier is deliberately invoked below, outside this recovery path.
        raise _make_rejection_for_error(error) from error
    verifier_sha256 = checkpoint.input_sha256s.get(NATIVE_CAD_VERIFIER_PATH)
    if not isinstance(verifier_sha256, str):
        raise StateConflict("native run lacks its trusted CAD verifier binding")
    try:
        cad_evidence = verify_native_made_cad(
            made,
            run_root=run.run_root,
            host_state_root=run.host_state_root,
            expected_verifier_sha256=verifier_sha256,
            require_print_ready=transition == "release",
        )
    except NativeMadeTreeGateError as error:
        # A tool can materialize cache directories after the run-local
        # finalizer inventories the tree but before the host reopens it. Keep
        # the exactness gate fail-closed, quarantine the stale proposal, and
        # return bounded repair feedback to this same Make checkpoint.
        raise _make_rejection_for_error(error) from error
    evidence = StageGateEvidence(
        stage="make",
        gate_id="make.sealed-revision-v1",
        validator_version="1.0.0",
        passed=True,
        checkpoint_sha256=checkpoint.checkpoint_sha256,
        subject_sha256=subject_sha256,
        outcome_sha256=proposal.outcome.sha256,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
        checks={
            "made_sha256": made.made_sha256,
            "product_artifact_sha256": canonical.artifact_sha256,
            "product_tree_rehashed": True,
            "upstream_bindings_valid": True,
            "cad_receipt_sha256": cad_evidence.receipt_sha256,
            "cad_verifier_sha256": cad_evidence.verifier_sha256,
            "cad_verifier_mode": cad_evidence.verifier_mode,
            "cad_verification_tier": cad_evidence.verification_tier,
            "cad_thickness_gate_required": cad_evidence.thickness_gate_required,
            "cad_print_ready_eligible": cad_evidence.print_ready_eligible,
            "cad_verification_passed": cad_evidence.passed,
        },
    )
    return StageGateDecision(evidence=evidence, transition=transition), additional


def _read_stable_private_json(
    path: Path, *, label: str, maximum_bytes: int
) -> Mapping[str, Any]:
    try:
        before = path.lstat()
        content = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(before.st_mode)
        or stat.S_IMODE(before.st_mode) != 0o600
        or not 1 <= len(content) <= maximum_bytes
        or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
    ):
        raise StateConflict("%s is not a stable private file" % label)
    try:
        return _strict_json_bytes(content, label=label)
    except ContractError as exc:
        raise StateConflict("%s is invalid" % label) from exc


def _native_token_aggregate(
    paths: NativeRunPaths, checkpoint: AgentRunCheckpoint
) -> dict[str, dict[str, Any]]:
    path = paths.host_state / _NATIVE_TOKEN_USAGE_NAME
    if not path.exists() and not path.is_symlink():
        return {}
    value = _read_stable_private_json(
        path,
        label="native token usage",
        maximum_bytes=128 * 1024,
    )
    if (
        set(value)
        != {"schema_version", "kind", "product_id", "wish_sha256", "stages"}
        or value.get("schema_version") not in (1, 2, 3)
        or value.get("kind") != _NATIVE_TOKEN_USAGE_KIND
        or value.get("product_id") != checkpoint.product_id
        or value.get("wish_sha256") != checkpoint.wish_sha256
        or not isinstance(value.get("stages"), Mapping)
        or not set(value["stages"]).issubset(_NATIVE_TOKEN_STAGES)
    ):
        raise StateConflict("native token usage binding is invalid")
    stages: dict[str, Any] = {}
    for stage_name, stage in value["stages"].items():
        if not isinstance(stage, Mapping):
            raise StateConflict("native token stage aggregate is invalid")
        if value["schema_version"] == 1:
            if (
                set(stage) != {"turns", "measured_turns", "tokens"}
                or type(stage.get("turns")) is not int
                or type(stage.get("measured_turns")) is not int
                or not 0 <= stage["measured_turns"] <= stage["turns"] <= 100_000
                or type(stage.get("tokens")) is not int
                or not 0 <= stage["tokens"] <= 10**18
            ):
                raise StateConflict("native token stage aggregate is invalid")
            # Schema v1 collapsed input and output. Preserve its turn coverage,
            # but never guess how the historical total should be split.
            measured_turns = 0
            input_tokens = 0
            output_tokens = 0
            breakdown_turns = 0
            breakdown_input_tokens = 0
            cached_input_tokens = 0
            cache_write_input_tokens = 0
            breakdown_output_tokens = 0
            reasoning_output_tokens = 0
        elif value["schema_version"] == 2:
            if (
                set(stage)
                != {"turns", "measured_turns", "input_tokens", "output_tokens"}
                or type(stage.get("turns")) is not int
                or type(stage.get("measured_turns")) is not int
                or not 0 <= stage["measured_turns"] <= stage["turns"] <= 100_000
                or any(
                    type(stage.get(name)) is not int
                    or not 0 <= stage[name] <= 10**18
                    for name in ("input_tokens", "output_tokens")
                )
            ):
                raise StateConflict("native token stage aggregate is invalid")
            measured_turns = stage["measured_turns"]
            input_tokens = stage["input_tokens"]
            output_tokens = stage["output_tokens"]
            breakdown_turns = 0
            breakdown_input_tokens = 0
            cached_input_tokens = 0
            cache_write_input_tokens = 0
            breakdown_output_tokens = 0
            reasoning_output_tokens = 0
        else:
            if (
                set(stage)
                != {
                    "turns",
                    "measured_turns",
                    "breakdown_turns",
                    "input_tokens",
                    "breakdown_input_tokens",
                    "cached_input_tokens",
                    "cache_write_input_tokens",
                    "output_tokens",
                    "breakdown_output_tokens",
                    "reasoning_output_tokens",
                }
                or any(
                    type(stage.get(name)) is not int
                    for name in (
                        "turns",
                        "measured_turns",
                        "breakdown_turns",
                        "input_tokens",
                        "breakdown_input_tokens",
                        "cached_input_tokens",
                        "cache_write_input_tokens",
                        "output_tokens",
                        "breakdown_output_tokens",
                        "reasoning_output_tokens",
                    )
                )
                or not 0
                <= stage["breakdown_turns"]
                <= stage["measured_turns"]
                <= stage["turns"]
                <= 100_000
                or any(
                    not 0 <= stage[name] <= 10**18
                    for name in (
                        "input_tokens",
                        "breakdown_input_tokens",
                        "cached_input_tokens",
                        "cache_write_input_tokens",
                        "output_tokens",
                        "breakdown_output_tokens",
                        "reasoning_output_tokens",
                    )
                )
                or stage["breakdown_input_tokens"] > stage["input_tokens"]
                or stage["cached_input_tokens"]
                > stage["breakdown_input_tokens"]
                or stage["cache_write_input_tokens"]
                > stage["breakdown_input_tokens"]
                or stage["breakdown_output_tokens"] > stage["output_tokens"]
                or stage["reasoning_output_tokens"]
                > stage["breakdown_output_tokens"]
            ):
                raise StateConflict("native token stage aggregate is invalid")
            measured_turns = stage["measured_turns"]
            breakdown_turns = stage["breakdown_turns"]
            input_tokens = stage["input_tokens"]
            breakdown_input_tokens = stage["breakdown_input_tokens"]
            cached_input_tokens = stage["cached_input_tokens"]
            cache_write_input_tokens = stage["cache_write_input_tokens"]
            output_tokens = stage["output_tokens"]
            breakdown_output_tokens = stage["breakdown_output_tokens"]
            reasoning_output_tokens = stage["reasoning_output_tokens"]
        stages[stage_name] = {
            "turns": stage["turns"],
            "measured_turns": measured_turns,
            "breakdown_turns": breakdown_turns,
            "input_tokens": input_tokens,
            "breakdown_input_tokens": breakdown_input_tokens,
            "cached_input_tokens": cached_input_tokens,
            "cache_write_input_tokens": cache_write_input_tokens,
            "output_tokens": output_tokens,
            "breakdown_output_tokens": breakdown_output_tokens,
            "reasoning_output_tokens": reasoning_output_tokens,
        }
    return stages


def _record_native_token_usage(
    paths: NativeRunPaths,
    checkpoint: AgentRunCheckpoint,
    usage: Any,
) -> None:
    """Add one turn to the small best-effort stage aggregate."""

    if checkpoint.stage not in _NATIVE_TOKEN_STAGES:
        return
    measured = None
    breakdown = None
    if (
        isinstance(usage, tuple)
        and len(usage) == 2
        and all(type(count) is int and 0 <= count <= 10**18 for count in usage)
    ):
        measured = usage
    elif isinstance(usage, Mapping):
        base = (usage.get("input_tokens"), usage.get("output_tokens"))
        if all(
            type(count) is int and 0 <= count <= 10**18 for count in base
        ):
            measured = base
            detail = (
                usage.get("cached_input_tokens"),
                usage.get("cache_write_input_tokens"),
                usage.get("reasoning_output_tokens"),
            )
            if (
                all(
                    type(count) is int and 0 <= count <= 10**18
                    for count in detail
                )
                and detail[0] <= base[0]
                and detail[1] <= base[0]
                and detail[2] <= base[1]
            ):
                breakdown = (base[0], detail[0], detail[1], base[1], detail[2])
    stages = _native_token_aggregate(paths, checkpoint)
    previous = stages.get(checkpoint.stage)
    stages[checkpoint.stage] = {
        "turns": 1 if previous is None else previous["turns"] + 1,
        "measured_turns": (
            (0 if previous is None else previous["measured_turns"])
            + (1 if measured is not None else 0)
        ),
        "breakdown_turns": (
            (0 if previous is None else previous["breakdown_turns"])
            + (1 if breakdown is not None else 0)
        ),
        "input_tokens": (0 if previous is None else previous["input_tokens"])
        + (0 if measured is None else measured[0]),
        "breakdown_input_tokens": (
            0 if previous is None else previous["breakdown_input_tokens"]
        )
        + (0 if breakdown is None else breakdown[0]),
        "cached_input_tokens": (
            0 if previous is None else previous["cached_input_tokens"]
        )
        + (0 if breakdown is None else breakdown[1]),
        "cache_write_input_tokens": (
            0 if previous is None else previous["cache_write_input_tokens"]
        )
        + (0 if breakdown is None else breakdown[2]),
        "output_tokens": (0 if previous is None else previous["output_tokens"])
        + (0 if measured is None else measured[1]),
        "breakdown_output_tokens": (
            0 if previous is None else previous["breakdown_output_tokens"]
        )
        + (0 if breakdown is None else breakdown[3]),
        "reasoning_output_tokens": (
            0 if previous is None else previous["reasoning_output_tokens"]
        )
        + (0 if breakdown is None else breakdown[4]),
    }
    _write_private_json(
        paths.host_state / _NATIVE_TOKEN_USAGE_NAME,
        {
            "schema_version": 3,
            "kind": _NATIVE_TOKEN_USAGE_KIND,
            "product_id": checkpoint.product_id,
            "wish_sha256": checkpoint.wish_sha256,
            "stages": stages,
        },
    )


def _unavailable_native_token_summary() -> dict[str, Any]:
    return {
        "schema_version": 3,
        "kind": _NATIVE_TOKEN_SUMMARY_KIND,
        "status": "unavailable",
        "reason": "Native token usage was not reported for this run.",
    }


def _native_token_summary(
    paths: NativeRunPaths, checkpoint: AgentRunCheckpoint
) -> dict[str, Any]:
    try:
        observed_stages = _native_token_aggregate(paths, checkpoint)
    except (OSError, WorkshopError):
        return _unavailable_native_token_summary()
    if not observed_stages:
        return _unavailable_native_token_summary()

    input_tokens = 0
    output_tokens = 0
    breakdown_input_tokens = 0
    cached_input_tokens = 0
    cache_write_input_tokens = 0
    breakdown_output_tokens = 0
    reasoning_output_tokens = 0
    recorded_turns = 0
    measured_turns = 0
    breakdown_turns = 0
    stages: dict[str, Any] = {}
    for stage_name in _NATIVE_TOKEN_STAGES:
        observed = observed_stages.get(stage_name)
        turns = 0 if observed is None else observed["turns"]
        measured = 0 if observed is None else observed["measured_turns"]
        stage_breakdown_turns = (
            0 if observed is None else observed["breakdown_turns"]
        )
        stage_input_tokens = 0 if observed is None else observed["input_tokens"]
        stage_output_tokens = 0 if observed is None else observed["output_tokens"]
        stage_breakdown_input = (
            0 if observed is None else observed["breakdown_input_tokens"]
        )
        stage_cached_input = (
            0 if observed is None else observed["cached_input_tokens"]
        )
        stage_cache_write_input = (
            0 if observed is None else observed["cache_write_input_tokens"]
        )
        stage_breakdown_output = (
            0 if observed is None else observed["breakdown_output_tokens"]
        )
        stage_reasoning_output = (
            0 if observed is None else observed["reasoning_output_tokens"]
        )
        recorded_turns += turns
        measured_turns += measured
        breakdown_turns += stage_breakdown_turns
        input_tokens += stage_input_tokens
        output_tokens += stage_output_tokens
        breakdown_input_tokens += stage_breakdown_input
        cached_input_tokens += stage_cached_input
        cache_write_input_tokens += stage_cache_write_input
        breakdown_output_tokens += stage_breakdown_output
        reasoning_output_tokens += stage_reasoning_output
        status = "pending"
        if checkpoint.effort is not None and stage_name == "match":
            status = "folded"
        elif checkpoint.effort == "spark" and stage_name == "invent":
            status = "skipped"
        elif checkpoint.effort in ("spark", "forge") and stage_name == "playtest":
            status = "not-run"
        elif turns:
            status = "measured" if measured == turns else "partial"
        stages[stage_name] = {
            "status": status,
            "turns": turns,
            "measured_turns": measured,
            "unmeasured_turns": turns - measured,
            "input_tokens": stage_input_tokens,
            "output_tokens": stage_output_tokens,
            "economics": {
                "status": (
                    status
                    if turns == 0
                    else (
                        "unavailable"
                        if stage_breakdown_turns == 0
                        else (
                            "measured"
                            if stage_breakdown_turns == turns
                            else "partial"
                        )
                    )
                ),
                "turns": {
                    "total": turns,
                    "measured": stage_breakdown_turns,
                    "unmeasured": turns - stage_breakdown_turns,
                },
                "input_tokens": stage_breakdown_input,
                "cached_input_tokens": stage_cached_input,
                "uncached_input_tokens": (
                    stage_breakdown_input - stage_cached_input
                ),
                "cache_write_input_tokens": stage_cache_write_input,
                "output_tokens": stage_breakdown_output,
                "reasoning_output_tokens": stage_reasoning_output,
                "non_reasoning_output_tokens": (
                    stage_breakdown_output - stage_reasoning_output
                ),
            },
        }
    try:
        durable_turns = native_progress_turn_floor(
            paths.host_state / NATIVE_PROGRESS_FILENAME
        )
    except (OSError, WorkshopError):
        durable_turns = recorded_turns
    missing_turns = max(0, durable_turns - recorded_turns)
    unmeasured_turns = recorded_turns - measured_turns + missing_turns
    economics_total_turns = recorded_turns + missing_turns
    economics_unmeasured_turns = economics_total_turns - breakdown_turns
    return {
        "schema_version": 3,
        "kind": _NATIVE_TOKEN_SUMMARY_KIND,
        "status": (
            "unavailable"
            if measured_turns == 0
            else ("partial" if unmeasured_turns else "measured")
        ),
        "turns": {
            "total": recorded_turns + missing_turns,
            "measured": measured_turns,
            "unmeasured": unmeasured_turns,
        },
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "economics": {
            "status": (
                "unavailable"
                if breakdown_turns == 0
                else (
                    "partial" if economics_unmeasured_turns else "measured"
                )
            ),
            "turns": {
                "total": economics_total_turns,
                "measured": breakdown_turns,
                "unmeasured": economics_unmeasured_turns,
            },
            "input_tokens": breakdown_input_tokens,
            "cached_input_tokens": cached_input_tokens,
            "uncached_input_tokens": breakdown_input_tokens
            - cached_input_tokens,
            "cache_write_input_tokens": cache_write_input_tokens,
            "output_tokens": breakdown_output_tokens,
            "reasoning_output_tokens": reasoning_output_tokens,
            "non_reasoning_output_tokens": breakdown_output_tokens
            - reasoning_output_tokens,
        },
        "stages": stages,
    }


def _validate_legacy_full_tier_make_gate(
    *,
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    made_artifact: AgentArtifact,
    made: NativeMade,
    expected_verifier_sha256: str,
) -> None:
    """Validate the exact historical full-tier gate accepted before Playtest.

    Schema-v1 CAD evidence predates named tiers, but it has only one legal
    command: the full fresh/export/strict-fit verifier with thickness enabled.
    This compatibility path is restricted to an immediate, history-bound Make
    predecessor and never applies while evaluating a new Make proposal.
    """

    if checkpoint.stage != "playtest" or checkpoint.revision <= 0:
        raise StateConflict("legacy CAD compatibility requires accepted Make state")
    bound = checkpoint.stage_artifacts.get("make")
    if not bound or bound[0] != made_artifact:
        raise StateConflict("legacy CAD compatibility Made binding is stale")

    gate_path = run.host_state_root / "gates" / (
        "%04d-make.json" % (checkpoint.revision - 1)
    )
    gate_document = _read_stable_private_json(
        gate_path,
        label="accepted Make gate",
        maximum_bytes=_MAX_STAGE_INPUT_BYTES,
    )
    try:
        decision = StageGateDecision.from_mapping(gate_document)
    except ContractError as exc:
        raise StateConflict("accepted Make gate is invalid") from exc
    evidence = decision.evidence
    legacy_checks = {
        "made_sha256",
        "product_artifact_sha256",
        "product_tree_rehashed",
        "upstream_bindings_valid",
        "cad_receipt_sha256",
        "cad_verifier_sha256",
        "cad_verification_passed",
    }
    checks = evidence.checks
    if (
        decision.transition != "playtest"
        or not evidence.passed
        or evidence.stage != "make"
        or evidence.gate_id != "make.sealed-revision-v1"
        or evidence.validator_version != "1.0.0"
        or evidence.artifact_path != made_artifact.path
        or evidence.artifact_sha256 != made_artifact.sha256
        or set(checks) != legacy_checks
        or checks["made_sha256"] != made.made_sha256
        or checks["product_artifact_sha256"]
        != made.product_manifest.artifact_sha256
        or checks["product_tree_rehashed"] is not True
        or checks["upstream_bindings_valid"] is not True
        or checks["cad_verification_passed"] is not True
        or checks["cad_verifier_sha256"] != expected_verifier_sha256
    ):
        raise StateConflict("accepted Make gate does not match the sealed Made artifact")
    run.assert_predecessor_gate_accepted(
        decision.receipt,
        gate_checkpoint_sha256=evidence.checkpoint_sha256,
    )

    cad_path = (
        run.host_state_root
        / "evidence"
        / "make"
        / ("r%04d-cad-gate.json" % made.round)
    )
    cad_document = _read_stable_private_json(
        cad_path,
        label="accepted legacy CAD gate evidence",
        maximum_bytes=_MAX_LEGACY_CAD_GATE_EVIDENCE_BYTES,
    )
    expected_fields = {
        "schema_version",
        "kind",
        "passed",
        "failure_code",
        "made_sha256",
        "product_artifact_sha256",
        "cad_project_path",
        "cad_project_sha256",
        "verifier_path",
        "verifier_sha256",
        "verifier_mode",
        "command",
        "returncode",
        "duration_ms",
        "timed_out",
        "stdout",
        "stderr",
        "source_tree_unchanged",
        "receipt_sha256",
    }
    receipt_sha256 = cad_document.get("receipt_sha256")
    identity = {
        key: value for key, value in cad_document.items() if key != "receipt_sha256"
    }
    full_command = [
        "<python>",
        NATIVE_CAD_VERIFIER_PATH,
        "<isolated-cad-project>",
        "--fresh",
        "--exports",
        "--strict-fit",
    ]
    if (
        set(cad_document) != expected_fields
        or cad_document["schema_version"] != 1
        or cad_document["kind"] != NATIVE_CAD_GATE_KIND
        or cad_document["passed"] is not True
        or cad_document["failure_code"] is not None
        or cad_document["made_sha256"] != made.made_sha256
        or cad_document["product_artifact_sha256"]
        != made.product_manifest.artifact_sha256
        or cad_document["cad_project_path"] != made.cad_project_path
        or cad_document["verifier_path"] != NATIVE_CAD_VERIFIER_PATH
        or cad_document["verifier_sha256"] != expected_verifier_sha256
        or cad_document["verifier_mode"] != NATIVE_CAD_VERIFIER_MODE
        or cad_document["command"] != full_command
        or cad_document["returncode"] != 0
        or cad_document["timed_out"] is not False
        or cad_document["source_tree_unchanged"] is not True
        or not isinstance(cad_document["stdout"], Mapping)
        or not isinstance(cad_document["stderr"], Mapping)
        or receipt_sha256 != checks["cad_receipt_sha256"]
        or receipt_sha256 != _sha256(_canonical_json_bytes(identity))
    ):
        raise StateConflict("accepted legacy CAD gate evidence is invalid")


def _evaluate_playtest_stage(
    proposal: AgentOutcomeProposal,
    *,
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    subject_sha256: str,
    context: Mapping[str, Any],
) -> tuple[StageGateDecision, tuple[AgentArtifact, ...]]:
    contract_path = (
        "artifacts/playtest/r%04d/playtested.json" % checkpoint.round_index
    )
    artifact = _ready_contract_artifact(
        proposal,
        stage="playtest",
        transitions=("release", "make", "invent"),
        path=contract_path,
    )
    playtested = _read_contract(
        run.run_root,
        artifact,
        NativePlaytested,
        label="native Playtested contract",
    )
    made = context["made"]
    blueprint = context["blueprint"]
    playtested.assert_context(made, blueprint)
    canonical = playtested.validate_evidence_tree(run.run_root, made)
    if checkpoint.effort is not None:
        inventory = {
            entry.path: entry.sha256
            for entry in playtested.evidence_manifest.entries
        }
        for check in playtested.checks:
            relative = "%s/configs/%s.json" % (
                playtested.evidence_root,
                check.check_id,
            )
            config, content = read_bounded_json_artifact(
                run.run_root,
                relative,
                label="routed Playtest %s config" % check.check_id,
            )
            expected_digest = inventory.get("configs/%s.json" % check.check_id)
            binding_keys = tuple(
                key
                for key in ("artifact_sha256", "product_artifact_sha256")
                if key in config
            )
            artifact_bindings = {
                config[key] for key in binding_keys if isinstance(config[key], str)
            }
            if (
                expected_digest != check.config_sha256
                or _sha256(content) != expected_digest
                or config.get("schema_version") != 1
                or config.get("check_id") != check.check_id
                or (
                    "seed" in config
                    and type(config["seed"]) is not int
                )
                or len(artifact_bindings) != len(binding_keys)
                or artifact_bindings
                != {made.product_manifest.artifact_sha256}
            ):
                raise ContractError(
                    "routed Playtest config is not bound to the current Made revision: %s"
                    % check.check_id
                )
    verifier_sha256 = checkpoint.input_sha256s.get(NATIVE_CAD_VERIFIER_PATH)
    if not isinstance(verifier_sha256, str):
        raise StateConflict("native run lacks its trusted CAD verifier binding")
    cad_evidence = verify_native_made_cad(
        made,
        run_root=run.run_root,
        host_state_root=run.host_state_root,
        expected_verifier_sha256=verifier_sha256,
        legacy_full_tier_validator=lambda: _validate_legacy_full_tier_make_gate(
            run=run,
            checkpoint=checkpoint,
            made_artifact=_stage_primary(checkpoint, "make"),
            made=made,
            expected_verifier_sha256=verifier_sha256,
        ),
        evidence_stage="playtest",
        require_print_ready=playtested.verdict == "pass",
    )
    passed = playtested.verdict == "pass"
    transition = playtested.proposed_transition
    if proposal.outcome.proposed_transition != transition:
        raise ContractError("Playtest transition differs from its evidence verdict")
    additional = _manifest_agent_artifacts(
        playtested.evidence_root, playtested.evidence_manifest
    )
    evidence = StageGateEvidence(
        stage="playtest",
        gate_id="playtest.release-v1",
        validator_version="1.0.0",
        passed=passed,
        checkpoint_sha256=checkpoint.checkpoint_sha256,
        subject_sha256=subject_sha256,
        outcome_sha256=proposal.outcome.sha256,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
        checks={
            "playtested_sha256": playtested.playtested_sha256,
            "product_artifact_sha256": made.product_manifest.artifact_sha256,
            "evidence_artifact_sha256": canonical.evidence.evidence_artifact_sha256,
            "required_playtest_checks_covered": True,
            "routed_config_made_bindings": checkpoint.effort is not None,
            "cad_receipt_sha256": cad_evidence.receipt_sha256,
            "cad_verifier_mode": cad_evidence.verifier_mode,
            "cad_verification_tier": cad_evidence.verification_tier,
            "cad_thickness_gate_required": cad_evidence.thickness_gate_required,
            "cad_print_ready_eligible": cad_evidence.print_ready_eligible,
            "cad_legacy_full_tier_compatibility": (
                getattr(cad_evidence, "legacy_full_tier_compatibility", False)
            ),
            "cad_verification_passed": cad_evidence.passed,
            "verdict": playtested.verdict,
        },
    )
    return StageGateDecision(evidence=evidence, transition=transition), additional


def _factory_credentials() -> Any:
    credential_environment = factory_service_credential_environment(
        factory_credential_environment()
    )
    return factory_credentials_from_environment(credential_environment)


def _release_effect_path(run: AgentRun) -> Path:
    return run.host_state_root / "release-effect.json"


def _release_effect_wait_path(run: AgentRun) -> Path:
    return run.host_state_root / _RELEASE_EFFECT_WAIT_NAME


def _read_release_effect_wait(
    run: AgentRun, checkpoint: AgentRunCheckpoint
) -> Optional[Mapping[str, Any]]:
    """Read one required-publication wait bound to the current checkpoint."""

    path = _release_effect_wait_path(run)
    if not path.exists() and not path.is_symlink():
        return None
    try:
        identity = path.lstat()
        content = path.read_bytes()
    except OSError as exc:
        raise StateConflict("Release effect wait is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o600
    ):
        raise StateConflict("Release effect wait must be a private file")
    try:
        value = _strict_json_bytes(content, label="Release effect wait")
    except ContractError as exc:
        raise StateConflict("Release effect wait is invalid") from exc
    legacy_expected = {
        "schema_version",
        "kind",
        "product_id",
        "stage",
        "waiting_checkpoint_sha256",
        "proposal_checkpoint_sha256",
        "proposal_subject_sha256",
        "proposal_outcome_sha256",
        "inventor_id",
        "need",
    }
    current_expected = legacy_expected | {"outcome"}
    hash_fields = (
        "waiting_checkpoint_sha256",
        "proposal_checkpoint_sha256",
        "proposal_subject_sha256",
        "proposal_outcome_sha256",
    )
    if (
        set(value) not in (legacy_expected, current_expected)
        or value["schema_version"] not in (1, 2)
        or (value["schema_version"] == 1 and set(value) != legacy_expected)
        or (value["schema_version"] == 2 and set(value) != current_expected)
        or value["kind"] != "autonomous-workshop.release-effect-wait"
        or value["product_id"] != checkpoint.product_id
        or value["stage"] != "release"
        or checkpoint.stage != "release"
        or checkpoint.status != "waiting"
        or value["waiting_checkpoint_sha256"] != checkpoint.checkpoint_sha256
        or not isinstance(value["inventor_id"], str)
        or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value["inventor_id"])
        is None
        or value["need"] not in (
            _FACTORY_CREDENTIALS_NEED,
            _FACTORY_PUBLICATION_NEED,
        )
        or any(
            not isinstance(value[name], str)
            or re.fullmatch(r"[0-9a-f]{64}", value[name]) is None
            for name in hash_fields
        )
    ):
        raise StateConflict("Release effect wait belongs to different state")
    if value["schema_version"] == 2:
        try:
            pending = AgentOutcome.from_mapping(value["outcome"])
        except ContractError as exc:
            raise StateConflict("Release effect wait outcome is invalid") from exc
        if (
            pending.stage != "release"
            or pending.status != "ready"
            or pending.sha256 != value["proposal_outcome_sha256"]
        ):
            raise StateConflict("Release effect wait outcome is not exact")
    return value


def _write_release_effect_wait(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    *,
    proposal: AgentOutcomeProposal,
    inventor_id: str,
    need: str,
) -> None:
    """Bind a resumable Release wait to the exact unaccepted proposal."""

    if (
        checkpoint.stage != "release"
        or checkpoint.status != "waiting"
        or need not in (_FACTORY_CREDENTIALS_NEED, _FACTORY_PUBLICATION_NEED)
    ):
        raise TransitionError("Release effect wait requires a waiting Release")
    _write_private_json(
        _release_effect_wait_path(run),
        {
            "schema_version": 2,
            "kind": "autonomous-workshop.release-effect-wait",
            "product_id": checkpoint.product_id,
            "stage": "release",
            "waiting_checkpoint_sha256": checkpoint.checkpoint_sha256,
            "proposal_checkpoint_sha256": proposal.checkpoint_sha256,
            "proposal_subject_sha256": proposal.subject_sha256,
            "proposal_outcome_sha256": proposal.outcome.sha256,
            "outcome": proposal.outcome.to_dict(),
            "inventor_id": inventor_id,
            "need": need,
        },
    )


def _remove_release_effect_wait(run: AgentRun) -> None:
    path = _release_effect_wait_path(run)
    if not path.exists() and not path.is_symlink():
        return
    try:
        identity = path.lstat()
    except OSError as exc:
        raise StateConflict("Release effect wait is unavailable") from exc
    if path.is_symlink() or not stat.S_ISREG(identity.st_mode):
        raise StateConflict("Release effect wait must be a regular file")
    try:
        path.unlink()
    except OSError as exc:
        raise StateConflict("Release effect wait could not be removed") from exc


def _read_release_effect(run: AgentRun, release: NativeRelease) -> Optional[Receipt]:
    path = _release_effect_path(run)
    if not path.exists() and not path.is_symlink():
        return None
    try:
        identity = path.lstat()
        content = path.read_bytes()
    except OSError as exc:
        raise StateConflict("Release effect checkpoint is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o600
    ):
        raise StateConflict("Release effect checkpoint must be a private file")
    value = _strict_json_bytes(content, label="Release effect checkpoint")
    common = {
        "schema_version",
        "kind",
        "product_id",
        "native_release_sha256",
        "product_artifact_sha256",
        "package_artifact_sha256",
        "product_page_sha256",
        "manual_sha256",
        "publication_status",
        "receipt",
    }
    expected = (
        common | {"factory_content_sha256", "factory_content_mapping"}
        if release.schema_version == 1
        else common | {"manual_path"}
    )
    package_entries = {
        entry.path: entry for entry in release.package_manifest.entries
    }
    manual_entry = package_entries.get(release.manual_path)
    if (
        set(value) != expected
        or value["schema_version"] != (2 if release.schema_version == 1 else 3)
        or value["kind"] != "autonomous-workshop.release-effect"
        or value["product_id"] != run.snapshot().product_id
        or value["native_release_sha256"] != release.release_sha256
        or value["product_artifact_sha256"] != release.product_artifact_sha256
        or value["package_artifact_sha256"]
        != release.package_manifest.artifact_sha256
        or value["product_page_sha256"] != release.product_json_sha256
        or manual_entry is None
        or value["manual_sha256"] != manual_entry.sha256
        or value["publication_status"] not in ("draft", "public")
    ):
        raise StateConflict("Release effect checkpoint belongs to different bytes")
    if release.schema_version == 1:
        if (
            not isinstance(value["factory_content_sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", value["factory_content_sha256"])
            is None
            or value["factory_content_mapping"] != FACTORY_CONTENT_MAPPING
        ):
            raise StateConflict("Release effect checkpoint belongs to different bytes")
    elif value["manual_path"] != release.manual_path:
        raise StateConflict("Release effect checkpoint belongs to a different manual path")
    try:
        receipt = Receipt.from_dict(value["receipt"])
    except (TypeError, ValueError, ContractError) as exc:
        raise StateConflict("Release effect receipt is invalid") from exc
    receipt.assert_artifact(release.product_artifact_sha256)
    if receipt.details.get("release_sha256") != release.package_manifest.artifact_sha256:
        raise StateConflict("Release effect receipt belongs to a different package")
    expected_content: dict[str, Any] = {
        "product_page_sha256": value["product_page_sha256"],
        "manual_sha256": value["manual_sha256"],
    }
    if release.schema_version == 1:
        expected_content.update(
            {
                "factory_content_sha256": value["factory_content_sha256"],
                "factory_content_mapping": value["factory_content_mapping"],
            }
        )
    else:
        expected_content["manual_path"] = value["manual_path"]
    if any(
        receipt.details.get(name) != expected_value
        for name, expected_value in expected_content.items()
    ):
        raise StateConflict(
            "Release effect receipt lacks the exact page and manual bindings"
        )
    if value["publication_status"] == "public" and not receipt.is_verified_public:
        raise StateConflict("Release effect public status is not verified")
    if value["publication_status"] == "draft" and not receipt.is_verified_draft:
        raise StateConflict("Release effect draft status is not verified")
    return receipt


def _write_release_effect(
    run: AgentRun, release: NativeRelease, receipt: Receipt
) -> None:
    status = "public" if receipt.is_verified_public else "draft"
    entries = {entry.path: entry for entry in release.package_manifest.entries}
    manual_entry = entries.get(release.manual_path)
    details = receipt.details
    if (
        manual_entry is None
        or details.get("product_page_sha256") != release.product_json_sha256
        or details.get("manual_sha256") != manual_entry.sha256
    ):
        raise StateConflict(
            "Factory Receipt lacks the exact Release facts and manual bindings"
        )
    effect = {
        "schema_version": 2 if release.schema_version == 1 else 3,
        "kind": "autonomous-workshop.release-effect",
        "product_id": run.snapshot().product_id,
        "native_release_sha256": release.release_sha256,
        "product_artifact_sha256": release.product_artifact_sha256,
        "package_artifact_sha256": release.package_manifest.artifact_sha256,
        "product_page_sha256": release.product_json_sha256,
        "manual_sha256": manual_entry.sha256,
        "publication_status": status,
        "receipt": receipt.to_dict(),
    }
    if release.schema_version == 1:
        factory_content_sha256 = details.get("factory_content_sha256")
        if (
            not isinstance(factory_content_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", factory_content_sha256) is None
            or details.get("factory_content_mapping") != FACTORY_CONTENT_MAPPING
        ):
            raise StateConflict(
                "Factory Receipt lacks the exact legacy rich-content bindings"
            )
        effect.update(
            {
                "factory_content_sha256": factory_content_sha256,
                "factory_content_mapping": FACTORY_CONTENT_MAPPING,
            }
        )
    else:
        if details.get("manual_path") != release.manual_path:
            raise StateConflict("Factory Receipt belongs to a different manual path")
        effect["manual_path"] = release.manual_path
    _write_private_json(_release_effect_path(run), effect)


def _assert_required_public_readback(
    release: NativeRelease, receipt: Receipt
) -> None:
    """Require the public receipt needed to complete this Release protocol."""

    if not receipt.is_verified_public:
        raise StateConflict("Release lacks authenticated public Factory readback")
    if release.schema_version not in (2, 3):
        return
    manual_entry = next(
        (
            entry
            for entry in release.package_manifest.entries
            if entry.path == release.manual_path
        ),
        None,
    )
    manual_url = receipt.details.get("manual_url")
    if (
        manual_entry is None
        or not isinstance(manual_url, str)
        or not manual_url.startswith("https://")
        or receipt.details.get("manual_path") != release.manual_path
        or receipt.details.get("manual_sha256") != manual_entry.sha256
        or receipt.details.get("manual_readback_sha256") != manual_entry.sha256
    ):
        raise StateConflict(
            "Release lacks exact public MANUAL.pdf hash readback"
        )


def _verified_release(
    run: AgentRun,
    release: NativeRelease,
    *,
    made: NativeMade,
    playtested: Optional[NativePlaytested],
    assignment: NativeMatchAssignment,
    blueprint: ToyBlueprint,
    inventor_binding: Any,
) -> _VerifiedRelease:
    """Seal the exact local package without consulting an external service."""

    package = release.validate_package_tree(run.run_root, made, playtested)
    release_contract = _materialized_release_contract(run.snapshot())
    if release_contract.get("manual_design_evidence_path") is not None:
        validate_bound_manual_design_evidence(
            package.root,
            package_manifest=release.package_manifest,
            manual_path=release.manual_path,
            made=made,
        )
    product_release = ProductRelease.from_root(
        package.root,
        release.product_artifact_sha256,
        package.manual_path,
        release.to_dict()["product"]["claims"],
    )
    return _VerifiedRelease(
        release=release,
        package=package,
        product_release=product_release,
        made=made,
        inventor_id=assignment.selected_inventor_id,
        assignment=assignment,
        blueprint=blueprint,
        inventor_binding=inventor_binding,
    )


def _publication_release_context(
    run: AgentRun, verified: _VerifiedRelease
) -> ReleaseContext:
    """Build Factory-only context after the native credential-free turn."""

    taste = parse_taste_bytes(
        verified.inventor_binding.taste_bytes,
        path=(
            run.run_root
            / ".codex"
            / "embedded"
            / verified.assignment.selected_inventor_id
            / "TASTE.md"
        ),
    )
    return ReleaseContext(
        wish=_load_wish(run.run_root),
        taste=taste,
        blueprint=verified.blueprint,
        made=verified.package.made,
        playtested=verified.package.playtested,
        workspace=run.run_root,
    )


def _existing_release_for_promotion(
    run: AgentRun, checkpoint: AgentRunCheckpoint
) -> _VerifiedRelease:
    """Revalidate exact authored Release bytes for publication or migration."""

    if checkpoint.stage not in ("release", "deliver") or checkpoint.status not in (
        "active",
        "waiting",
        "complete",
    ):
        raise TransitionError("public publication requires a verified Release")
    effort = _checkpoint_effort(checkpoint)
    direct_release = _checkpoint_uses_direct_release(checkpoint)
    required_stages = (
        effort.enabled_stages
        if effort is not None
        else (
            ("match", "invent", "make", "release")
            if direct_release
            else ("match", "invent", "make", "playtest", "release")
        )
    )
    if any(stage in checkpoint.invalidated_stages for stage in required_stages):
        raise StateConflict("public promotion cannot use invalidated stage evidence")
    roster = _inventor_roster(checkpoint)
    if effort is not None:
        (
            assignment,
            invented,
            unused_assignment_artifact,
            unused_invented_artifact,
            inventor_binding,
        ) = _routed_creative_context(run, checkpoint, roster)
        del unused_assignment_artifact, unused_invented_artifact
    else:
        assignment = _read_contract(
            run.run_root,
            _stage_primary(checkpoint, "match"),
            NativeMatchAssignment,
            label="native Match assignment",
        )
        assignment.assert_context(
            wish_sha256=checkpoint.wish_sha256, roster=roster
        )
        inventor_binding = _selected_inventor_binding(
            run.run_root, checkpoint, assignment
        )
        invented = _read_contract(
            run.run_root,
            _stage_primary(checkpoint, "invent"),
            NativeInvented,
            label="native Invented contract",
        )
        invented.assert_context(assignment)
    made = _read_contract(
        run.run_root,
        _stage_primary(checkpoint, "make"),
        NativeMade,
        label="native Made contract",
    )
    made.assert_context(assignment, invented, expected_round=checkpoint.round_index)
    blueprint = ToyBlueprint()
    playtested: Optional[NativePlaytested]
    if direct_release:
        playtested = None
    else:
        playtested = _read_contract(
            run.run_root,
            _stage_primary(checkpoint, "playtest"),
            NativePlaytested,
            label="native Playtested contract",
        )
        playtested.assert_context(made, blueprint)
        if playtested.verdict != "pass":
            raise StateConflict("public promotion requires a passing Playtest")
    release = _read_contract(
        run.run_root,
        _stage_primary(checkpoint, "release"),
        NativeRelease,
        label="native Release contract",
    )
    release.assert_context(made, playtested)
    return _verified_release(
        run,
        release,
        made=made,
        playtested=playtested,
        assignment=assignment,
        blueprint=blueprint,
        inventor_binding=inventor_binding,
    )


def _attempt_release_publication(
    run: AgentRun,
    verified: _VerifiedRelease,
) -> tuple[Receipt, bool]:
    """Create and publish exact Factory state through its durable effect ledger.

    Local bytes are validated before this helper, but the Release gate remains
    open until authenticated public readback succeeds. The Factory adapters
    retain ambiguous outcomes in their ledger and reconcile them before any
    later send.
    """

    try:
        receipt = _read_release_effect(run, verified.release)
        if receipt is not None and receipt.is_verified_public:
            _assert_required_public_readback(verified.release, receipt)
            _try_record_public_example_projection(
                run,
                release=verified.release,
                made=verified.made,
                inventor_id=verified.inventor_id,
                receipt=receipt,
            )
            return receipt, False
        try:
            credentials = _factory_credentials()
        except ContractError:
            raise _FactoryCredentialsUnavailable(verified.inventor_id) from None
        ledger = EffectLedger(run.host_state_root / "factory-effects.sqlite3")
        if receipt is None:
            transport_overrides = _factory_transport_overrides()
            writer = FactoryReleaseWriter(
                ledger,
                verified.inventor_id,
                credentials,
                **transport_overrides,
            )
            receipt = writer(
                _publication_release_context(run, verified),
                verified.package.root,
                verified.package.manifest,
            )
            _write_release_effect(run, verified.release, receipt)
        if receipt.is_verified_draft:
            receipt = FactoryPublicTransition(
                ledger,
                FactoryAgentSession(credentials, **_factory_transport_overrides()),
            ).publish(receipt)
            _write_release_effect(run, verified.release, receipt)
        if not receipt.is_verified_public:
            raise StateConflict(
                "Factory publication lacks verified public readback"
            )
        _assert_required_public_readback(verified.release, receipt)
        _try_record_public_example_projection(
            run,
            release=verified.release,
            made=verified.made,
            inventor_id=verified.inventor_id,
            receipt=receipt,
        )
        return receipt, True
    except _FactoryCredentialsUnavailable:
        raise
    except FactoryCredentialRejected:
        raise _FactoryCredentialsUnavailable(verified.inventor_id) from None
    except (AmbiguousEffectError, FactoryAuthenticationError) as exc:
        raise _RequiredPublicationUnavailable() from exc


def _accept_local_release(
    run: AgentRun,
    release: NativeRelease,
    *,
    context: Mapping[str, Any],
) -> _VerifiedRelease:
    """Validate the credential-free bytes before required publication."""

    return _verified_release(
        run,
        release,
        made=context["made"],
        playtested=context["playtested"],
        assignment=context["assignment"],
        blueprint=context["blueprint"],
        inventor_binding=context["inventor_binding"],
    )


def _verify_release_print_ready_cad(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    made: NativeMade,
) -> Any:
    """Re-run the current full CAD gate before any public Release claim."""

    verifier_sha256 = checkpoint.input_sha256s.get(NATIVE_CAD_VERIFIER_PATH)
    if not isinstance(verifier_sha256, str):
        raise StateConflict("native run lacks its trusted CAD verifier binding")
    evidence = verify_native_made_cad(
        made,
        run_root=run.run_root,
        host_state_root=run.host_state_root,
        expected_verifier_sha256=verifier_sha256,
        evidence_stage="release",
        require_print_ready=True,
    )
    if (
        not evidence.passed
        or evidence.verification_tier != NATIVE_CAD_FULL_TIER
        or not evidence.thickness_gate_required
        or not evidence.print_ready_eligible
    ):
        raise StateConflict(
            "Release requires full-tier CAD evidence eligible for a "
            "ready-to-print handoff"
        )
    return evidence


def _evaluate_release_stage(
    proposal: AgentOutcomeProposal,
    *,
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    subject_sha256: str,
    context: Mapping[str, Any],
    timing_observer: Optional[WishRunTimingObserver] = None,
) -> tuple[StageGateDecision, tuple[AgentArtifact, ...]]:
    terminal_transition = context.get("terminal_transition")
    if terminal_transition not in ("complete", "deliver"):
        raise StateConflict("native run lacks its frozen Release transition")
    artifact = _ready_contract_artifact(
        proposal,
        stage="release",
        transitions=(terminal_transition,),
        path="artifacts/release/release.json",
    )
    release = _read_contract(
        run.run_root, artifact, NativeRelease, label="native Release contract"
    )
    expected_release = context.get("release_contract")
    if (
        not isinstance(expected_release, Mapping)
        or release.schema_version
        != expected_release.get("native_release_schema_version")
        or release.manual_path != expected_release.get("manual_path")
    ):
        raise StateConflict(
            "native Release contract differs from the run's materialized "
            "Release protocol"
        )
    release.assert_context(context["made"], context["playtested"])
    verified = _accept_local_release(run, release, context=context)
    if (
        release.schema_version not in (2, 3)
        or release.manual_path != NATIVE_RELEASE_MANUAL_PATH
    ):
        raise _LegacyReleaseUpgradeRequired(_LEGACY_RELEASE_UPGRADE_NEED)
    cad_evidence = _verify_release_print_ready_cad(
        run, checkpoint, context["made"]
    )
    with wish_run_timing_span(
        timing_observer,
        product_id=checkpoint.product_id,
        stage=checkpoint.stage,
        operation="effect.factory",
    ):
        publication, unused_changed = _attempt_release_publication(run, verified)
    del unused_changed
    if not publication.is_verified_public:
        raise StateConflict("Release requires authenticated public readback")
    try:
        verification = (
            None
            if context["playtested"] is None
            else try_materialize_digital_verification(
                run.run_root,
                release,
                context["made"],
                context["playtested"],
            )
        )
    except Exception:
        # Public verification is optional enrichment. It must never become a
        # second Release or Factory gate, including if the helper itself
        # regresses rather than returning its documented ``None``.
        verification = None
    additional = _manifest_agent_artifacts(
        release.package_root, release.package_manifest
    )
    verification_checks: dict[str, Any] = {
        "product_verification_status": (
            "recorded" if verification is not None else "not-recorded"
        )
    }
    if verification is not None:
        verification_checks.update(
            {
                "product_verification_level": verification.level,
                "product_verification_sha256": verification.sha256,
            }
        )
    evidence = StageGateEvidence(
        stage="release",
        gate_id="release.public-print-package-v3",
        validator_version="3.0.0",
        passed=True,
        checkpoint_sha256=checkpoint.checkpoint_sha256,
        subject_sha256=subject_sha256,
        outcome_sha256=proposal.outcome.sha256,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
        checks={
            "native_release_sha256": release.release_sha256,
            "product_release_sha256": (
                verified.product_release.manifest.artifact_sha256
            ),
            "product_artifact_sha256": release.product_artifact_sha256,
            "manual_path": release.manual_path,
            "native_release_schema_version": release.schema_version,
            "playtest_status": (
                DIRECT_RELEASE_PLAYTEST_STATUS
                if context["playtested"] is None
                else "passed"
            ),
            "package_tree_rehashed": True,
            "cad_receipt_sha256": cad_evidence.receipt_sha256,
            "cad_verifier_sha256": cad_evidence.verifier_sha256,
            "cad_verifier_mode": cad_evidence.verifier_mode,
            "cad_verification_tier": cad_evidence.verification_tier,
            "cad_thickness_gate_required": cad_evidence.thickness_gate_required,
            "cad_print_ready_eligible": cad_evidence.print_ready_eligible,
            "publication_status": "public",
            "factory_readback_verified": True,
            "page_url": publication.details.get("page_url"),
            "manual_url": publication.details.get("manual_url"),
            "manual_readback_sha256": publication.details.get(
                "manual_readback_sha256"
            ),
            **verification_checks,
        },
    )
    return (
        StageGateDecision(evidence=evidence, transition=terminal_transition),
        additional,
    )


def _persist_gate_decision(
    run: AgentRun, checkpoint: AgentRunCheckpoint, decision: StageGateDecision
) -> None:
    gates = run.host_state_root / "gates"
    gates.mkdir(mode=0o700, exist_ok=True)
    filename = "%04d-%s.json" % (checkpoint.revision, checkpoint.stage)
    _write_private_json(gates / filename, decision.to_dict())


def _agent_outcome_exists(run_root: Path) -> bool:
    path = run_root / _AGENT_OUTCOME_NAME
    if not path.exists() and not path.is_symlink():
        return False
    try:
        identity = path.lstat()
    except OSError as exc:
        raise StateConflict("agent outcome is unavailable") from exc
    if path.is_symlink() or not stat.S_ISREG(identity.st_mode):
        raise StateConflict("agent outcome must be a regular file")
    return True


def _process_agent_outcome(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    *,
    subject_sha256: str,
    context: Mapping[str, Any],
    pending_proposal: Optional[AgentOutcomeProposal] = None,
    timing_observer: Optional[WishRunTimingObserver] = None,
) -> AgentRunCheckpoint:
    with wish_run_timing_span(
        timing_observer,
        product_id=checkpoint.product_id,
        stage=checkpoint.stage,
        operation="outcome.process",
    ):
        return _process_agent_outcome_inner(
            run,
            checkpoint,
            subject_sha256=subject_sha256,
            context=context,
            pending_proposal=pending_proposal,
            timing_observer=timing_observer,
        )


def _process_agent_outcome_inner(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    *,
    subject_sha256: str,
    context: Mapping[str, Any],
    pending_proposal: Optional[AgentOutcomeProposal],
    timing_observer: Optional[WishRunTimingObserver],
) -> AgentRunCheckpoint:
    if pending_proposal is None:
        proposal = read_agent_outcome_proposal(
            run.run_root,
            expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
            expected_subject_sha256=subject_sha256,
        )
    else:
        proposal = pending_proposal
        if (
            proposal.checkpoint_sha256 != checkpoint.checkpoint_sha256
            or proposal.subject_sha256 != subject_sha256
        ):
            raise StateConflict("pending Release proposal belongs to different state")
    run.validate_outcome(proposal.outcome)
    if proposal.outcome.status != "ready":
        updated = run.apply_outcome(proposal.outcome)
        _remove_agent_outcome(run.run_root)
        return updated

    additional: tuple[AgentArtifact, ...] = ()
    if checkpoint.stage == "match":
        with wish_run_timing_span(
            timing_observer,
            product_id=checkpoint.product_id,
            stage=checkpoint.stage,
            operation="gate.evaluate",
        ):
            decision = evaluate_match_stage(
                proposal,
                run_root=run.run_root,
                expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
                wish_sha256=checkpoint.wish_sha256,
                roster=context["roster"],
            )
    elif checkpoint.stage == "invent":
        with wish_run_timing_span(
            timing_observer,
            product_id=checkpoint.product_id,
            stage=checkpoint.stage,
            operation="gate.evaluate",
        ):
            if context.get("routed_invent") is True:
                decision = evaluate_routed_invent_stage(
                    proposal,
                    run_root=run.run_root,
                    expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
                    expected_subject_sha256=subject_sha256,
                    wish_sha256=checkpoint.wish_sha256,
                    roster=context["roster"],
                    assignment_artifact_path=context[
                        "assignment_contract_path"
                    ],
                    invented_artifact_path=context["invent_contract_path"],
                )
            else:
                decision = evaluate_invent_stage(
                    proposal,
                    run_root=run.run_root,
                    expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
                    expected_subject_sha256=subject_sha256,
                    expected_artifact_path=context["invent_contract_path"],
                    assignment=context["assignment"],
                )
    elif checkpoint.stage == "make":
        try:
            with wish_run_timing_span(
                timing_observer,
                product_id=checkpoint.product_id,
                stage=checkpoint.stage,
                operation="gate.evaluate",
            ):
                decision, additional = _evaluate_make_stage(
                    proposal,
                    run=run,
                    checkpoint=checkpoint,
                    subject_sha256=subject_sha256,
                    context=context,
                )
        except NativeCadGateError as rejection:
            _persist_cad_gate_rejection(run, checkpoint, proposal, rejection)
            _remove_agent_outcome(run.run_root)
            return checkpoint
        except _MakeProposalRejected as rejection:
            persisted = _persist_make_proposal_rejection(
                run, checkpoint, proposal, rejection
            )
            _remove_rejected_agent_outcome(run, persisted)
            return checkpoint
    elif checkpoint.stage == "playtest":
        try:
            with wish_run_timing_span(
                timing_observer,
                product_id=checkpoint.product_id,
                stage=checkpoint.stage,
                operation="gate.evaluate",
            ):
                decision, additional = _evaluate_playtest_stage(
                    proposal,
                    run=run,
                    checkpoint=checkpoint,
                    subject_sha256=subject_sha256,
                    context=context,
                )
        except NativeCadGateError as rejection:
            _persist_cad_gate_rejection(run, checkpoint, proposal, rejection)
            _remove_agent_outcome(run.run_root)
            return checkpoint
        except (ArtifactError, ContractError) as error:
            if isinstance(error, StateConflict):
                raise
            rejection = _playtest_rejection_for_error(error)
            persisted = _persist_playtest_proposal_rejection(
                run, checkpoint, proposal, rejection
            )
            _remove_rejected_agent_outcome(run, persisted)
            return checkpoint
    elif checkpoint.stage == "release":
        try:
            with wish_run_timing_span(
                timing_observer,
                product_id=checkpoint.product_id,
                stage=checkpoint.stage,
                operation="gate.evaluate",
            ):
                decision, additional = _evaluate_release_stage(
                    proposal,
                    run=run,
                    checkpoint=checkpoint,
                    subject_sha256=subject_sha256,
                    context=context,
                    timing_observer=timing_observer,
                )
        except _LegacyReleaseUpgradeRequired:
            failed = AgentOutcome(
                stage="release",
                status="failed",
                artifacts=proposal.outcome.artifacts,
                needs=(_LEGACY_RELEASE_UPGRADE_NEED,),
            )
            updated = run.apply_outcome(failed)
            _remove_agent_outcome(run.run_root)
            return updated
        except NativeCadGateError as rejection:
            # Playtest normally prevents a non-print-ready revision from ever
            # entering Release. A fresh Release replay can still uncover a
            # transient timeout. Persist every exact rejection and discard the
            # finalized proposal. Only a timeout may retry unchanged Release
            # bytes; deterministic failures cannot be repaired in Release and
            # therefore fail closed instead of consuming the native turn
            # budget in a replay loop.
            _persist_cad_gate_rejection(run, checkpoint, proposal, rejection)
            _remove_agent_outcome(run.run_root)
            if rejection.failure_code != "verifier-timeout":
                return run.apply_outcome(
                    AgentOutcome(
                        stage="release",
                        status="failed",
                        artifacts=proposal.outcome.artifacts,
                        needs=(
                            "Release's final CAD guard rejected the sealed Make "
                            "revision (%s); start a repaired Make revision in a "
                            "new run rather than weakening or editing Release."
                            % rejection.failure_code,
                        ),
                    )
                )
            return checkpoint
        except _FactoryCredentialsUnavailable as unavailable:
            need = _FACTORY_CREDENTIALS_NEED
            waiting = AgentOutcome(
                stage="release",
                status="waiting",
                artifacts=proposal.outcome.artifacts,
                needs=(need,),
            )
            updated = run.apply_outcome(waiting)
            _remove_agent_outcome(run.run_root)
            _write_release_effect_wait(
                run,
                updated,
                proposal=proposal,
                inventor_id=unavailable.inventor_id,
                need=need,
            )
            return updated
        except _RequiredPublicationUnavailable:
            need = _FACTORY_PUBLICATION_NEED
            waiting = AgentOutcome(
                stage="release",
                status="waiting",
                artifacts=proposal.outcome.artifacts,
                needs=(need,),
            )
            updated = run.apply_outcome(waiting)
            _remove_agent_outcome(run.run_root)
            _write_release_effect_wait(
                run,
                updated,
                proposal=proposal,
                inventor_id=context["assignment"].selected_inventor_id,
                need=need,
            )
            return updated
    else:  # pragma: no cover - guarded by packet preparation
        raise TransitionError("native stage cannot consume an agent proposal")

    _persist_gate_decision(run, checkpoint, decision)
    updated = run.apply_outcome(
        proposal.outcome,
        gate=decision.receipt,
        gate_subject_sha256=subject_sha256,
        additional_artifacts=additional,
    )
    _remove_agent_outcome(run.run_root)
    if checkpoint.stage == "release" and updated.stage == "deliver":
        # A frozen historical finalizer proposed ``deliver``. Publication has
        # already passed the new Release gate, so migrate without creating or
        # claiming a physical effect.
        updated = run.complete_legacy_release()
    return updated


def _rebind_existing_progress(
    paths: NativeRunPaths,
    previous: AgentRunCheckpoint,
    updated: AgentRunCheckpoint,
    *,
    activity: Optional[str] = None,
) -> None:
    tracker = _NativeProgressTracker.existing(paths, previous)
    tracker.rebind(updated, activity=activity)


def _run_native_session(
    run: AgentRun,
    paths: NativeRunPaths,
    *,
    launcher: Optional[NativeSessionLauncher],
    activity_observer: Optional[Callable[[str], None]] = None,
    timing_observer: Optional[WishRunTimingObserver] = None,
) -> tuple[AgentRunCheckpoint, Optional[CodexNativeSessionOutcome], int, str]:
    """Advance through native stages until complete, wait, or failure."""

    last_session: Optional[CodexNativeSessionOutcome] = None
    turns = 0
    first_method = (
        "resume"
        if _session_status(paths, run.snapshot().manager_id) == "checkpointed"
        else "start"
    )
    action = "resumed" if first_method == "resume" else "started"
    unfinished_continuation = False
    consecutive_unfinished_turns = 0
    consecutive_recoverable_turns = 0
    recoverable_continuation = False
    native_turn_limit = _native_turn_limit(run.snapshot())
    initial_make_boundaries: set[str] = set()
    while turns < native_turn_limit:
        checkpoint = run.snapshot()
        if checkpoint.status in ("waiting", "failed", "complete"):
            return checkpoint, last_session, turns, action
        if checkpoint.stage == "deliver":
            raise TransitionError(
                "legacy Deliver checkpoint must be reconciled before native work"
            )
        if checkpoint.stage == "make":
            # A crash may land after the private rejection head is durable but
            # before its exact unaccepted workspace marker is removed. Reap
            # only that byte-identical marker before deriving the new subject.
            _reconcile_rejected_agent_outcome(run, checkpoint)
        with wish_run_timing_span(
            timing_observer,
            product_id=checkpoint.product_id,
            stage=checkpoint.stage,
            operation="stage.prepare",
        ):
            subject, unused_packet, context = _prepare_stage_input(
                run, checkpoint
            )
        del unused_packet

        if _agent_outcome_exists(run.run_root):
            recovered_progress = _NativeProgressTracker.existing(paths, checkpoint)
            recovered_progress.observe("finalizing")
            try:
                updated = _process_agent_outcome(
                    run,
                    checkpoint,
                    subject_sha256=subject,
                    context=context,
                    timing_observer=timing_observer,
                )
            except WorkshopError:
                recovered_progress.observe("failed")
                raise
            else:
                unfinished_continuation = False
                consecutive_unfinished_turns = 0
                consecutive_recoverable_turns = 0
                recoverable_continuation = False
                _rebind_existing_progress(
                    paths, checkpoint, updated, activity="completed"
                )
                if updated.status in ("waiting", "failed", "complete"):
                    return updated, last_session, turns, action
                continue

        _remove_agent_outcome(run.run_root)
        method = (
            "resume"
            if _session_status(paths, checkpoint.manager_id) == "checkpointed"
            else "start"
        )
        progress = _NativeProgressTracker.begin(paths, checkpoint)
        turn_activity_observer = _combined_activity_observer(
            progress,
            activity_observer,
        )
        launcher_failure: Optional[WorkshopError] = None
        turn_launcher = launcher
        make_proof_boundary = False
        if turn_launcher is None:
            if (
                checkpoint.stage == "make"
                and DEEP_ECONOMICS_CAPABILITY_PATH in checkpoint.input_sha256s
            ):
                initial_make_proof_boundary = not _make_proof_ready(
                    paths, checkpoint
                )
                make_proof_boundary = initial_make_proof_boundary
            else:
                initial_make_proof_boundary = (
                    checkpoint.stage == "make"
                    and checkpoint.checkpoint_sha256 not in initial_make_boundaries
                )
            turn_launcher = _native_launcher(
                checkpoint,
                initial_make_proof_boundary=initial_make_proof_boundary,
                recoverable_continuation=recoverable_continuation,
            )
            if initial_make_proof_boundary and not make_proof_boundary:
                initial_make_boundaries.add(checkpoint.checkpoint_sha256)
        try:
            with wish_run_timing_span(
                timing_observer,
                product_id=checkpoint.product_id,
                stage=checkpoint.stage,
                operation="session.%s" % method,
            ):
                last_session = _launcher_call(
                    turn_launcher,
                    method,
                    checkpoint=checkpoint,
                    paths=paths,
                    unfinished_continuation=unfinished_continuation,
                    recoverable_continuation=recoverable_continuation,
                    make_proof_boundary=make_proof_boundary,
                    activity_observer=turn_activity_observer,
                )
        except WorkshopError as exc:
            # The finalizer is an exact filesystem protocol, independent of the
            # Codex event-stream terminal signal.  A provider timeout or a
            # lingering/failed launcher may happen after the current proposal
            # was atomically written.  Count that launched turn and allow only
            # the normal checkpoint-bound reader and host gate below to decide
            # whether its exact bytes can advance.  No message or launcher
            # status is treated as gate evidence.
            launcher_failure = exc
            progress.observe("failed")
        except (KeyboardInterrupt, SystemExit):
            # The launcher has already terminated and reaped its dedicated
            # process session. Preserve truthful host telemetry before the
            # operator interruption propagates; a later explicit resume owns
            # any continuation.
            progress.observe("failed")
            raise
        else:
            progress.observe("finalizing")
        try:
            _record_native_token_usage(
                paths,
                checkpoint,
                (
                    {
                        "input_tokens": getattr(
                            last_session, "input_tokens", None
                        ),
                        "cached_input_tokens": getattr(
                            last_session, "cached_input_tokens", None
                        ),
                        "cache_write_input_tokens": getattr(
                            last_session, "cache_write_input_tokens", None
                        ),
                        "output_tokens": getattr(
                            last_session, "output_tokens", None
                        ),
                        "reasoning_output_tokens": getattr(
                            last_session, "reasoning_output_tokens", None
                        ),
                    }
                    if launcher_failure is None
                    else None
                ),
            )
        except (OSError, WorkshopError):
            # Token telemetry is best-effort and never a lifecycle gate.
            pass
        turns += 1
        if not _agent_outcome_exists(run.run_root):
            # A normal native turn may end before the active Goal reaches its
            # finalizer. Continue the exact checkpointed session under the same
            # immutable stage subject and shared turn budget. This is not gate
            # evidence and creates no attempt; it merely avoids requiring an
            # operator to issue `workshop resume` between ordinary agent turns.
            if (
                launcher_failure is None
                and _session_status(paths, checkpoint.manager_id) == "checkpointed"
            ):
                consecutive_recoverable_turns = 0
                recoverable_continuation = False
                consecutive_unfinished_turns += 1
                if (
                    consecutive_unfinished_turns
                    >= _MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS
                ):
                    progress.observe("failed")
                    raise WorkshopError(
                        "native %s session returned without agent-outcome.json "
                        "for %d consecutive turns; the exact session remains "
                        "checkpointed and resumable with `workshop resume %s`"
                        % (
                            manager_spec(checkpoint.manager_id).display_name,
                            _MAX_CONSECUTIVE_UNFINISHED_NATIVE_TURNS,
                            checkpoint.product_id,
                        )
                    )
                unfinished_continuation = True
                continue
            consecutive_unfinished_turns = 0
            progress.observe("failed")
            if isinstance(launcher_failure, _RecoverableNativeTurn):
                # A timeout or recognized provider disconnect is safe to
                # continue only when the host has already persisted the exact
                # native session identity.  The unchanged STAGE.json subject,
                # one mutation lock, and the normal turn budget remain in
                # force.  An interruption before thread binding fails closed
                # rather than creating a second root session automatically.
                if _session_status(paths, checkpoint.manager_id) == "checkpointed":
                    consecutive_recoverable_turns += 1
                    if (
                        consecutive_recoverable_turns
                        >= _MAX_CONSECUTIVE_RECOVERABLE_NATIVE_TURNS
                    ):
                        raise WorkshopError(
                            "native %s session did not complete for %d "
                            "consecutive recoverable turns; the exact session "
                            "remains checkpointed and resumable with "
                            "`workshop resume %s`"
                            % (
                                manager_spec(
                                    checkpoint.manager_id
                                ).display_name,
                                _MAX_CONSECUTIVE_RECOVERABLE_NATIVE_TURNS,
                                checkpoint.product_id,
                            )
                        )
                    if turns < native_turn_limit:
                        time.sleep(
                            _recoverable_native_turn_backoff_seconds(
                                checkpoint,
                                turns,
                            )
                        )
                    recoverable_continuation = True
                    continue
            if launcher_failure is not None:
                raise launcher_failure
            raise WorkshopError(
                "native %s session returned without agent-outcome.json"
                % manager_spec(checkpoint.manager_id).display_name
            )
        try:
            updated = _process_agent_outcome(
                run,
                checkpoint,
                subject_sha256=subject,
                context=context,
                timing_observer=timing_observer,
            )
        except WorkshopError:
            progress.observe("failed")
            raise
        unfinished_continuation = False
        consecutive_unfinished_turns = 0
        consecutive_recoverable_turns = 0
        recoverable_continuation = False
        progress.rebind(updated, activity="completed")
        if updated.status in ("waiting", "failed", "complete"):
            return updated, last_session, turns, action
    raise WorkshopError("native product run exhausted its bounded native-turn budget")


def _session_status(
    paths: NativeRunPaths,
    manager_id: str = DEFAULT_MANAGER_ID,
) -> str:
    runtime = manager_spec(manager_id)
    checkpoint = paths.host_state / runtime.session_checkpoint_name
    if not checkpoint.exists() and not checkpoint.is_symlink():
        return "not-started"
    try:
        identity = checkpoint.lstat()
    except OSError as exc:
        raise StateConflict(
            "native %s session checkpoint is unavailable" % runtime.display_name
        ) from exc
    if (
        checkpoint.is_symlink()
        or not stat.S_ISREG(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o600
    ):
        raise StateConflict(
            "native %s session checkpoint is not a private file" % runtime.display_name
        )
    return "checkpointed"


def _native_progress_receipt(
    paths: Optional[NativeRunPaths],
    checkpoint: AgentRunCheckpoint,
    *,
    fallback_turns: int,
) -> tuple[Mapping[str, Any], int]:
    """Return only exact-bound metadata; invalid telemetry is simply hidden."""

    if paths is None:
        return {"status": "unavailable"}, fallback_turns
    progress = trusted_native_progress(
        paths.host_state / NATIVE_PROGRESS_FILENAME,
        product_id=checkpoint.product_id,
        wish_sha256=checkpoint.wish_sha256,
        checkpoint_sha256=checkpoint.checkpoint_sha256,
        checkpoint_stage=checkpoint.stage,
    )
    if progress is None:
        return {"status": "unavailable"}, fallback_turns
    try:
        return progress.public_view(), progress.native_turns
    except WorkshopError:
        return {"status": "unavailable"}, fallback_turns


def _draft_publication_intent_state(
    paths: NativeRunPaths, receipt: Receipt
) -> Optional[str]:
    """Return an exact draft's durable publish state without mutating its ledger."""

    ledger_path = paths.host_state / "factory-effects.sqlite3"
    if not ledger_path.exists() and not ledger_path.is_symlink():
        return None
    product_id = receipt.details.get("product_id")
    if not isinstance(product_id, str) or not product_id:
        raise StateConflict("Factory draft receipt lacks its Workshop product id")
    intent = EffectLedger.inspect_latest(
        ledger_path,
        product_id,
        "factory-publish",
    )
    if intent is None:
        return None
    details = receipt.details
    if (
        intent.pack_sha256 != receipt.payload_sha256
        or intent.product_artifact_sha256 != receipt.artifact_sha256
        or intent.release_sha256 != details.get("release_sha256")
        or intent.playtest_evidence_sha256
        != details.get("playtest_evidence_sha256")
        or intent.handoff_artifact_sha256
        != details.get("handoff_artifact_sha256")
        or intent.request.get("product_page_sha256")
        != details.get("product_page_sha256")
        or intent.request.get("manual_sha256") != details.get("manual_sha256")
    ):
        raise StateConflict(
            "Factory publication intent belongs to different Release bytes"
        )
    return intent.state


def _native_receipt(
    checkpoint: AgentRunCheckpoint,
    *,
    paths: Optional[NativeRunPaths] = None,
    session: Optional[CodexNativeSessionOutcome] = None,
    action: str,
    turns: int = 0,
) -> dict[str, Any]:
    progress, durable_turns = _native_progress_receipt(
        paths, checkpoint, fallback_turns=turns
    )
    publication: dict[str, Any] = {
        "status": "not-created",
        "requested": True,
        "required": True,
        "reason": (
            "Release is incomplete until Factory publication has authenticated "
            "public readback. Credentials remain outside the native session."
        ),
    }
    needs: list[str] = list(checkpoint.needs)
    if paths is not None:
        if checkpoint.stage == "release" and checkpoint.status == "waiting":
            wait_run = AgentRun.open(
                paths.workspace, host_state_root=paths.host_state
            )
            effect_wait = _read_release_effect_wait(wait_run, checkpoint)
            if effect_wait is not None:
                if effect_wait["need"] not in needs:
                    needs.append(effect_wait["need"])
                publication["reason"] = effect_wait["need"]
        effect = paths.host_state / "release-effect.json"
        if (
            (effect.exists() or effect.is_symlink())
            and checkpoint.stage == "release"
            and checkpoint.status == "waiting"
        ):
            # The locally valid proposal has not passed its Release gate yet,
            # so its release artifact is intentionally not an accepted stage
            # binding. The durable Factory ledger will reconcile on resume.
            publication.update(
                {
                    "status": "unknown",
                    "verified": False,
                }
            )
        elif effect.exists() or effect.is_symlink():
            effect_run = AgentRun.open(
                paths.workspace, host_state_root=paths.host_state
            )
            observed_checkpoint = effect_run.snapshot()
            if observed_checkpoint.checkpoint_sha256 != checkpoint.checkpoint_sha256:
                raise StateConflict("Release status raced a checkpoint update")
            verified = _existing_release_for_promotion(
                effect_run, observed_checkpoint
            )
            try:
                receipt = _read_release_effect(effect_run, verified.release)
            except WorkshopError:
                publication = {
                    "status": "unavailable",
                    "requested": True,
                    "required": True,
                    "verified": False,
                    "reason": (
                        "Required Factory publication state could not be verified; "
                        "Release remains incomplete."
                    ),
                }
            else:
                if receipt is None:  # pragma: no cover - effect path exists above
                    raise StateConflict("Release effect checkpoint is unavailable")
                publication = {
                    "status": (
                        "public" if receipt.is_verified_public else "draft"
                    ),
                    "requested": True,
                    "required": True,
                    "page_url": receipt.details.get("page_url"),
                    "manual_url": receipt.details.get("manual_url"),
                    "cover_url": receipt.details.get("cover_url"),
                    "verified": True,
                }
                if receipt.is_verified_public:
                    publication["public_example"] = dict(
                        _read_public_example_projection(
                            effect_run, verified.release
                        )
                    )
                elif receipt.is_verified_draft:
                    try:
                        publish_state = _draft_publication_intent_state(
                            paths, receipt
                        )
                    except WorkshopError:
                        publication = {
                            "status": "unavailable",
                            "requested": True,
                            "required": True,
                            "verified": False,
                            "reason": (
                                "Required Factory publication state could not "
                                "be verified; Release remains incomplete."
                            ),
                        }
                    else:
                        if publish_state in ("sending", "unknown"):
                            publication = {
                                "status": "unknown",
                                "requested": True,
                                "required": True,
                                "verified": False,
                                "reason": (
                                    "Factory publication requires authenticated "
                                    "reconciliation and will not be blindly "
                                    "retried."
                                ),
                            }
        else:
            ledger = paths.host_state / "factory-effects.sqlite3"
            if ledger.exists() or ledger.is_symlink():
                # A durable effect intent without a verified receipt may have
                # reached Factory. Report uncertainty and let the adapter's
                # authenticated reconciliation decide; never call absence
                # "not-created" or imply that a retry is safe.
                publication = {
                    "status": "unknown",
                    "requested": True,
                    "required": True,
                    "verified": False,
                    "reason": (
                        "Factory effect state requires authenticated "
                        "reconciliation and will not be blindly retried."
                    ),
                }
            elif (
                checkpoint.stage == "deliver"
                and checkpoint.status in ("active", "waiting", "complete")
            ):
                # Credential discovery is a local, read-only host operation.
                # Revalidate the exact accepted Release to recover its selected
                # Inventor, then report a useful retry condition without
                # creating an effect intent or weakening local Release.
                effect_run = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                )
                verified = _existing_release_for_promotion(effect_run, checkpoint)
                try:
                    _factory_credentials()
                except ContractError:
                    publication["reason"] = _FACTORY_CREDENTIALS_NEED
                    if _FACTORY_CREDENTIALS_NEED not in needs:
                        needs.append(_FACTORY_CREDENTIALS_NEED)
                else:
                    publication["reason"] = (
                        "No verified public Factory receipt exists; resume this "
                        "run to reconcile or retry required publication."
                    )
    visible_stage = "release" if checkpoint.stage == "deliver" else checkpoint.stage
    visible_status = checkpoint.status
    if checkpoint.stage == "deliver":
        # Historical Deliver checkpoints stay readable, but neither a public
        # page nor an old fulfillment status proves today's PDF + print-ready
        # terminal Release contract. An eligible run is migrated explicitly
        # during resume; until then it is never reported as complete.
        visible_status = "waiting"
        if _LEGACY_RELEASE_UPGRADE_NEED not in needs:
            needs.append(_LEGACY_RELEASE_UPGRADE_NEED)
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "kind": "native-agent-run",
        "product_id": checkpoint.product_id,
        "status": visible_status,
        "stage": visible_stage,
        "revision": checkpoint.revision,
        "round": checkpoint.round_index,
        "max_rounds": checkpoint.max_rounds,
        "wish_sha256": checkpoint.wish_sha256,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "agent_instructions_sha256": materialized_agent_instructions_sha256(
            checkpoint
        ),
        "invalidated_stages": list(checkpoint.invalidated_stages),
        "action": action,
        "native_turns": durable_turns,
        "progress": progress,
        "publication": publication,
        "tokens": (
            _native_token_summary(paths, checkpoint)
            if paths is not None
            else {
                "schema_version": 2,
                "kind": "autonomous-workshop.native-token-summary",
                "status": "unavailable",
                "reason": "Host token state was not provided.",
            }
        ),
    }
    if checkpoint.effort is not None:
        receipt["effort"] = checkpoint.effort
    receipt["manager"] = checkpoint.manager_id
    if needs:
        receipt["needs"] = list(needs)
    if session is not None:
        receipt["session"] = session.to_dict()
    return receipt


def _prune_empty_make_product_directories(
    run_root: Path, checkpoint: AgentRunCheckpoint
) -> None:
    """Remove only byte-free Make residue while no native session is running.

    Older materialized finalizers require every empty directory to be removed
    but may run in a sandbox that permits file unlink and denies directory
    unlink.  The trusted host owns the run lock here, follows no links, and
    never removes files or the product root itself.
    """

    if checkpoint.stage != "make" or checkpoint.round_index < 1:
        return
    root = Path(run_root)
    product_root = (
        root
        / "artifacts"
        / "make"
        / ("r%04d" % checkpoint.round_index)
        / "product"
    )
    try:
        root_identity = root.lstat()
        product_identity = product_root.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise StateConflict("Make product tree is unavailable for host cleanup") from exc
    if (
        not root.is_absolute()
        or root.is_symlink()
        or not stat.S_ISDIR(root_identity.st_mode)
        or product_root.is_symlink()
        or not stat.S_ISDIR(product_identity.st_mode)
    ):
        raise StateConflict("Make product tree is unsafe for host cleanup")
    try:
        if product_root.resolve(strict=True) != product_root:
            raise StateConflict("Make product tree is unsafe for host cleanup")
    except OSError as exc:
        raise StateConflict("Make product tree is unavailable for host cleanup") from exc

    for directory, _, _ in os.walk(
        str(product_root), topdown=False, followlinks=False
    ):
        candidate = Path(directory)
        if candidate == product_root:
            continue
        try:
            identity = candidate.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise StateConflict(
                "Make product tree changed during host cleanup"
            ) from exc
        if candidate.is_symlink() or not stat.S_ISDIR(identity.st_mode):
            continue
        try:
            candidate.rmdir()
        except OSError:
            # Non-empty, protected, or concurrently changed directories stay
            # untouched for the finalizer and exact-file gate to inspect.
            continue


def start_native_run(
    wish: Wish,
    *,
    effort: Optional[str] = None,
    manager_id: Optional[str] = None,
    publish_requested: Optional[bool] = None,
    github_publish_requested: bool = False,
    activity_observer: Optional[Callable[[str], None]] = None,
    timing_observer: Optional[WishRunTimingObserver] = None,
) -> Mapping[str, Any]:
    """Persist one Wish and immediately start its whole-run native session.

    ``effort`` freezes one selectable route for a new run. ``None`` retains the
    schema-v3 lifecycle only for source-compatible programmatic callers; the
    public CLI always passes its named default.

    ``manager_id`` freezes the native Manager runtime. ``None`` selects Codex.

    ``publish_requested`` is a source-compatibility shim for callers of the
    former optional-publication API. Release publication is now mandatory, so
    either legacy boolean has the same terminal behavior and the CLI no longer
    exposes the choice.

    ``github_publish_requested`` grants prospective authority to commit and
    push the sanitized public snapshot after verified Factory readback. It is
    false by default and frozen for the run.

    Both observers receive only bounded, content-free progress. They are
    optional presentation telemetry and cannot change the run result.
    """

    selected_effort = workshop_effort(effort) if effort is not None else None
    selected_manager = manager_spec(
        DEFAULT_MANAGER_ID if manager_id is None else manager_id
    )
    if publish_requested is not None and type(publish_requested) is not bool:
        raise ContractError("legacy publication option must be boolean")
    if type(github_publish_requested) is not bool:
        raise ContractError("GitHub publication option must be boolean")

    activity_observer = _validated_activity_observer(activity_observer)
    timing_observer = _validated_timing_observer(timing_observer)
    with wish_run_timing_span(
        timing_observer,
        product_id=wish.product_id,
        stage="wish",
        operation="run.initialize",
    ):
        assets = product_run_agent_assets()
        wish_bytes = canonical_wish_bytes(wish)
        domain_skill_roots = product_run_domain_skill_roots()
        inventor_source_root = _product_run_inventor_source_root(assets)
        paths = native_run_paths(wish.product_id, create=True)
        try:
            run = AgentRun.create(
                paths.workspace,
                paths.host_state,
                product_id=wish.product_id,
                wish_bytes=wish_bytes,
                product_run_constitution_source=assets.constitution,
                skill_root=assets.skill_root,
                domain_skill_roots=domain_skill_roots,
                inventor_source_root=inventor_source_root,
                max_rounds=4,
                effort=(selected_effort.name if selected_effort is not None else None),
                manager_id=selected_manager.manager_id,
            )
        except Exception:
            # If setup fails early, release only this exact empty reservation.
            # A partial workspace or host state is deliberately preserved.
            try:
                paths.workspace.parent.rmdir()
            except OSError:
                pass
            raise
    with _native_run_mutation_lock(paths):
        _record_authorization(
            paths,
            product_id=wish.product_id,
            publish_requested=True,
            github_publish_requested=github_publish_requested,
            create=True,
        )
        checkpoint = _advance_validated_wish(run)
        launcher = (
            None if _uses_dynamic_deep_profile(checkpoint)
            else _native_launcher(checkpoint)
        )
        checkpoint, session, turns, action = _run_native_session(
            run,
            paths,
            launcher=launcher,
            activity_observer=activity_observer,
            timing_observer=timing_observer,
        )
        return {
            **_native_receipt(
                checkpoint,
                paths=paths,
                session=session,
                action=action,
                turns=turns,
            ),
            "wish": wish.to_dict(),
        }


def _resume_native_run_locked(
    product_id: str,
    *,
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    paths: NativeRunPaths,
    activity_observer: Optional[Callable[[str], None]] = None,
    timing_observer: Optional[WishRunTimingObserver] = None,
) -> Mapping[str, Any]:
    """Mutate one native run while its process lock is held."""

    _record_authorization(
        paths,
        product_id=product_id,
        publish_requested=True,
        create=False,
    )
    promotion_action: Optional[str] = None
    if (
        checkpoint.stage == "deliver"
        and checkpoint.status in ("active", "waiting", "complete")
    ):
        verified = _existing_release_for_promotion(run, checkpoint)
        if (
            verified.release.schema_version not in (2, 3)
            or verified.release.manual_path != NATIVE_RELEASE_MANUAL_PATH
        ):
            return _native_receipt(
                checkpoint,
                paths=paths,
                action="legacy-release-needs-upgrade",
            )
        try:
            _verify_release_print_ready_cad(run, checkpoint, verified.made)
        except NativeCadGateError:
            return _native_receipt(
                checkpoint,
                paths=paths,
                action="legacy-release-cad-rejected",
            )
        try:
            with wish_run_timing_span(
                timing_observer,
                product_id=checkpoint.product_id,
                stage=checkpoint.stage,
                operation="effect.factory",
            ):
                unused_receipt, promoted = _attempt_release_publication(
                    run, verified
                )
                del unused_receipt
        except _FactoryCredentialsUnavailable:
            promotion_action = "publication-not-created"
        except _RequiredPublicationUnavailable:
            promotion_action = "publication-unverified"
        else:
            promotion_action = (
                "published-existing-release"
                if promoted
                else "publication-already-public"
            )
            checkpoint = run.complete_legacy_release()
        if checkpoint.stage == "release" or promotion_action is not None:
            return _native_receipt(
                checkpoint,
                paths=paths,
                action=promotion_action,
            )
    if checkpoint.status == "waiting":
        waiting_checkpoint = checkpoint
        effect_wait = _read_release_effect_wait(run, checkpoint)
        if effect_wait is not None and effect_wait["schema_version"] == 2:
            pending_outcome = AgentOutcome.from_mapping(effect_wait["outcome"])
            checkpoint = run.resume()
            _rebind_existing_progress(paths, waiting_checkpoint, checkpoint)
            with wish_run_timing_span(
                timing_observer,
                product_id=checkpoint.product_id,
                stage=checkpoint.stage,
                operation="stage.prepare",
            ):
                subject, unused_packet, context = _prepare_stage_input(
                    run, checkpoint
                )
            del unused_packet
            if subject != effect_wait["proposal_subject_sha256"]:
                raise StateConflict(
                    "pending Release proposal subject changed while waiting"
                )
            proposal = AgentOutcomeProposal(
                checkpoint_sha256=checkpoint.checkpoint_sha256,
                subject_sha256=subject,
                outcome=pending_outcome,
            )
            _remove_release_effect_wait(run)
            updated = _process_agent_outcome(
                run,
                checkpoint,
                subject_sha256=subject,
                context=context,
                pending_proposal=proposal,
                timing_observer=timing_observer,
            )
            _rebind_existing_progress(
                paths, checkpoint, updated, activity="completed"
            )
            if updated.status == "waiting":
                renewed_wait = _read_release_effect_wait(run, updated)
                action = (
                    "publication-not-created"
                    if renewed_wait is not None
                    and renewed_wait["need"] == _FACTORY_CREDENTIALS_NEED
                    else "publication-unverified"
                )
            elif updated.status == "complete":
                action = "published-release"
            else:
                action = "release-cad-rejected"
            return _native_receipt(
                updated,
                paths=paths,
                action=action,
            )
        if effect_wait is not None:
            # A schema-v1 wait did not retain the exact ready outcome. Resume
            # it through one native turn for backward compatibility; all new
            # waits replay host-side without depending on agent availability.
            _remove_release_effect_wait(run)
        checkpoint = run.resume()
        _rebind_existing_progress(paths, waiting_checkpoint, checkpoint)
    elif checkpoint.status == "complete":
        action = "inspected-terminal"
        if checkpoint.stage == "release":
            verified = _existing_release_for_promotion(run, checkpoint)
            receipt = _read_release_effect(run, verified.release)
            if receipt is None or not receipt.is_verified_public:
                raise StateConflict(
                    "completed Release lacks its verified Factory receipt"
                )
            _assert_required_public_readback(verified.release, receipt)
            projection = _try_record_public_example_projection(
                run,
                release=verified.release,
                made=verified.made,
                inventor_id=verified.inventor_id,
                receipt=receipt,
            )
            if projection.get("status") == "materialized":
                action = "reconciled-public-example"
        return _native_receipt(
            checkpoint,
            paths=paths,
            action=action,
        )
    elif checkpoint.status == "failed":
        return _native_receipt(
            checkpoint,
            paths=paths,
            action="inspected-terminal",
        )
    _prune_empty_make_product_directories(paths.workspace, checkpoint)
    launcher = (
        None if _uses_dynamic_deep_profile(checkpoint)
        else _native_launcher(checkpoint)
    )
    checkpoint, session, turns, action = _run_native_session(
        run,
        paths,
        launcher=launcher,
        activity_observer=activity_observer,
        timing_observer=timing_observer,
    )
    if action == "started":
        action = "started-after-interruption"
    if promotion_action is not None and turns == 0:
        action = promotion_action
    return _native_receipt(
        checkpoint,
        paths=paths,
        session=session,
        action=action,
        turns=turns,
    )


def resume_native_run(
    product_id: str,
    *,
    publish_requested: Optional[bool] = None,
    activity_observer: Optional[Callable[[str], None]] = None,
    timing_observer: Optional[WishRunTimingObserver] = None,
) -> Mapping[str, Any]:
    """Resume one exact native session under an exclusive host mutation lock.

    The ignored keyword preserves source compatibility with the former
    optional-publication API; every resumed Release now requires publication.

    Both observers receive only bounded, content-free progress. They are
    optional presentation telemetry and cannot change the run result.
    """

    if publish_requested is not None and type(publish_requested) is not bool:
        raise ContractError("legacy publication option must be boolean")

    activity_observer = _validated_activity_observer(activity_observer)
    timing_observer = _validated_timing_observer(timing_observer)
    paths = native_run_paths(product_id)
    with _native_run_mutation_lock(paths):
        run = AgentRun.open(paths.workspace, host_state_root=paths.host_state)
        checkpoint = run.snapshot()
        return _resume_native_run_locked(
            product_id,
            run=run,
            checkpoint=checkpoint,
            paths=paths,
            activity_observer=activity_observer,
            timing_observer=timing_observer,
        )


def native_run_status(product_id: str) -> Mapping[str, Any]:
    """Return a redacted, validated native checkpoint without running a model."""

    run, checkpoint = _open_native_run(product_id)
    del run
    paths = native_run_paths(product_id)
    _record_authorization(
        paths,
        product_id=product_id,
        publish_requested=False,
        create=False,
    )
    return {
        **_native_receipt(
            checkpoint,
            paths=paths,
            action="inspected",
        ),
        "session_status": _session_status(paths, checkpoint.manager_id),
    }


__all__ = [
    "NativeRunPaths",
    "canonical_wish_bytes",
    "materialized_agent_instructions_sha256",
    "native_run_exists",
    "native_run_paths",
    "native_run_status",
    "native_stage_prompt",
    "resume_native_run",
    "start_native_run",
]
