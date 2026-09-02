"""Byte-bound evidence and isolation policy for live-Codex acceptance."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping, Sequence


MAX_CONTEXT_RECORD_BYTES = 64 * 1024
MAX_PACKET_BYTES = 1024 * 1024
CONTEXT_KIND = "autonomous-workshop.mock-session-context"
TRACE_KIND = "autonomous-workshop.mock-session-turn"
CONTEXT_FIELDS = frozenset(
    {
        "schema_version",
        "kind",
        "stage",
        "checkpoint_sha256",
        "subject_sha256",
        "stage_packet_sha256",
        "instructions",
        "used_inputs",
        "strategy",
        "outputs",
        "deferred_work",
    }
)
APPROVED_PATCH_TARGETS = frozenset(
    {
        "workshop.workflow.native_run._FACTORY_TRANSPORT",
        "workshop.workflow.native_run._FACTORY_PROJECT_FILE_TRANSPORT",
        "workshop.workflow.native_run._CONCEPT_IMAGE_TRANSPORT",
    }
)
MOCK_SESSION_FILES = (
    "mock_codex_passthrough.py",
    "mock_session_evidence.py",
    "mock_session_factory.py",
    "mock_session_harness.py",
    "test_mock_session_harness.py",
    "test_mock_session_live.py",
)
FIXTURE_SECRETS = (
    "mock-session-factory-password-canary",
    "mock-session-access-token-canary",
)
FORBIDDEN_OUTPUT_PARTS = frozenset(
    {
        "STAGE.json",
        "agent-outcome.json",
        "host-state",
        "checkpoints",
        "evidence",
        "gates",
        "receipts",
        "release-effect.json",
        "factory-effects.sqlite3",
    }
)
_INVENT_CONCEPT_SOURCE = re.compile(
    r"artifacts/concept/r\d{4}/concept/"
    r"(?:brief|research|prompts|descriptor|derived_wish)\.json"
)
FORBIDDEN_INTERNAL_TERMS = frozenset(
    {
        "launcher",
        "stage_evaluator",
        "finalizer_override",
        "contract_reader",
        "checkpoint_store",
        "verify_native_made_cad",
        "native_cad_gate",
        "release_writer",
        "factory_session",
        "public_transition",
        "apply_outcome",
        "gate_receipt",
        "stage_result",
    }
)
FORBIDDEN_TRANSPORT_FILE_MUTATORS = frozenset(
    {
        "chmod",
        "mkdir",
        "open",
        "rename",
        "replace",
        "rmdir",
        "unlink",
        "write_bytes",
        "write_text",
    }
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STRATEGY_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_FORBIDDEN_DIRECTIVE_FRAGMENTS = (
    "spark",
    "forge",
    "quest",
    "stage_proposal.py",
    "--source",
    "--product-root",
    "--evidence-root",
    "assignment_contract_path",
    "invented_contract_path",
    "PLAYTEST-NOT-RUN",
    "proposed_transition",
    "make -> release",
    "invent -> make",
)


class MockSessionEvidenceError(AssertionError):
    """The live acceptance trace does not prove its narrow claim."""


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_bounded_json(path: Path, maximum: int) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise MockSessionEvidenceError(
            "mock-session JSON is not a regular file: %s" % path
        )
    content = path.read_bytes()
    if not 1 <= len(content) <= maximum:
        raise MockSessionEvidenceError(
            "mock-session JSON size is invalid: %s" % path
        )
    try:
        value = json.loads(
            content.decode("utf-8"), object_pairs_hook=strict_object
        )
    except (UnicodeError, ValueError) as exc:
        raise MockSessionEvidenceError(
            "mock-session JSON is malformed: %s" % path
        ) from exc
    if not isinstance(value, Mapping):
        raise MockSessionEvidenceError(
            "mock-session JSON must contain one object: %s" % path
        )
    return dict(value)


def safe_run_path(run_root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise MockSessionEvidenceError("%s must be a run-relative path" % label)
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or pure.as_posix() != value
        or any(part in ("", ".", "..") for part in pure.parts)
    ):
        raise MockSessionEvidenceError(
            "%s must be a canonical run-relative path" % label
        )
    target = run_root.joinpath(*pure.parts)
    try:
        target.relative_to(run_root)
    except ValueError as exc:  # pragma: no cover - defensive after PurePosixPath
        raise MockSessionEvidenceError("%s escapes the run root" % label) from exc
    return target


def _bound_files(
    values: Any,
    *,
    run_root: Path,
    label: str,
    forbid_host_outputs: bool,
    stage: str | None = None,
    observed_hashes: Mapping[str, str] | None = None,
    allow_turn_written_sources: bool = False,
) -> tuple[str, ...]:
    if not isinstance(values, list) or not values:
        raise MockSessionEvidenceError("%s must be a non-empty array" % label)
    paths: list[str] = []
    for index, item in enumerate(values):
        if not isinstance(item, Mapping) or set(item) != {"path", "sha256"}:
            raise MockSessionEvidenceError(
                "%s[%d] fields are invalid" % (label, index)
            )
        relative = item["path"]
        target = safe_run_path(run_root, relative, "%s[%d].path" % (label, index))
        if target.is_symlink() or not target.is_file():
            raise MockSessionEvidenceError(
                "%s[%d] is not a regular run-root file" % (label, index)
            )
        final_digest = sha256_bytes(target.read_bytes())
        observed_digest = (
            observed_hashes.get(relative)
            if observed_hashes is not None
            else final_digest
        )
        if observed_digest is None:
            raise MockSessionEvidenceError(
                "%s[%d] %s has no turn-time hash" % (label, index, relative)
            )
        if item["sha256"] != observed_digest or item["sha256"] != final_digest:
            raise MockSessionEvidenceError(
                "%s[%d] %s differs from final source bytes"
                % (label, index, relative)
            )
        if forbid_host_outputs and (
            relative.startswith(".mock-session/")
            or any(part in FORBIDDEN_OUTPUT_PARTS for part in PurePosixPath(relative).parts)
        ):
            raise MockSessionEvidenceError(
                "%s[%d] cites generated or host-owned output %s"
                % (label, index, relative)
            )
        stage_owned = bool(
            stage == "invent"
            and re.match(
                r"^artifacts/(?:invent/(?:r[0-9]{4}/)?|concept/r[0-9]{4}/).+",
                relative,
            )
        ) or bool(
            stage in {"make", "playtest"}
            and re.match(
                r"^artifacts/%s/r[0-9]{4}/.+" % re.escape(stage),
                relative,
            )
        ) or bool(
            stage == "release" and relative.startswith("artifacts/release/package/")
        )
        if (
            forbid_host_outputs
            and not relative.startswith("authored/")
            and not stage_owned
            and not allow_turn_written_sources
        ):
            raise MockSessionEvidenceError(
                "%s[%d] must cite a current-stage authored source file"
                % (label, index)
            )
        paths.append(relative)
    if len(paths) != len(set(paths)):
        raise MockSessionEvidenceError("%s paths must be unique" % label)
    return tuple(paths)


def validate_stage_packet_inputs(
    packet_path: Path, *, run_root: Path
) -> tuple[str, ...]:
    """Rehash direct run-root path/digest bindings in ``STAGE.inputs``."""

    packet = read_bounded_json(packet_path, MAX_PACKET_BYTES)
    inputs = packet.get("inputs")
    if not isinstance(inputs, Mapping):
        raise MockSessionEvidenceError("mock-session stage packet inputs are invalid")
    observed: list[str] = []

    def verify(value: Mapping[str, Any], label: str) -> None:
        path_value = value.get("path")
        digest_value = value.get("sha256")
        if (
            not isinstance(path_value, str)
            or not isinstance(digest_value, str)
            or _SHA256.fullmatch(digest_value) is None
        ):
            raise MockSessionEvidenceError(
                "%s path/digest binding is malformed" % label
            )
        target = safe_run_path(run_root, path_value, "%s path" % label)
        if target.is_symlink() or not target.is_file():
            raise MockSessionEvidenceError("%s input is unavailable" % label)
        if sha256_bytes(target.read_bytes()) != digest_value:
            raise MockSessionEvidenceError("%s input bytes are stale" % label)
        observed.append(path_value)

    for key, value in inputs.items():
        if isinstance(value, Mapping) and "path" in value and "sha256" in value:
            verify(value, "inputs.%s" % key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, Mapping) and "path" in item and "sha256" in item:
                    verify(item, "inputs.%s[%d]" % (key, index))
    return tuple(dict.fromkeys(observed))


def validate_context_record(
    record_path: Path,
    *,
    run_root: Path,
    packet_path: Path,
    agent_writes: Sequence[str] | None = None,
    proposal_artifacts: Sequence[str] | None = None,
    turn_output_hashes: Mapping[str, str] | None = None,
) -> Mapping[str, Any]:
    record = read_bounded_json(record_path, MAX_CONTEXT_RECORD_BYTES)
    packet = read_bounded_json(packet_path, MAX_PACKET_BYTES)
    if set(record) != CONTEXT_FIELDS:
        raise MockSessionEvidenceError(
            "mock-session context record fields are invalid"
        )
    if record["schema_version"] != 1 or record["kind"] != CONTEXT_KIND:
        raise MockSessionEvidenceError(
            "mock-session context record identity is invalid"
        )
    packet_digest = sha256_bytes(packet_path.read_bytes())
    expected = {
        "stage": packet.get("stage"),
        "checkpoint_sha256": packet.get("checkpoint_sha256"),
        "subject_sha256": packet.get("subject_sha256"),
        "stage_packet_sha256": packet_digest,
    }
    for field, value in expected.items():
        if record[field] != value:
            raise MockSessionEvidenceError(
                "mock-session context record has stale %s" % field
            )
    for field in ("checkpoint_sha256", "subject_sha256", "stage_packet_sha256"):
        if not isinstance(record[field], str) or _SHA256.fullmatch(record[field]) is None:
            raise MockSessionEvidenceError(
                "mock-session context binding is malformed"
            )
    instructions = _bound_files(
        record["instructions"],
        run_root=run_root,
        label="instructions",
        forbid_host_outputs=False,
    )
    required = {
        "AGENTS.md",
        ".agents/skills/autonomous-workshop/SKILL.md",
    }
    if not required <= set(instructions) or not any(
        path.startswith(".agents/skills/autonomous-workshop/references/")
        for path in instructions
    ):
        raise MockSessionEvidenceError(
            "mock-session context omitted production instructions"
        )
    inputs = packet.get("inputs")
    used_inputs = record["used_inputs"]
    if (
        not isinstance(inputs, Mapping)
        or not isinstance(used_inputs, list)
        or not used_inputs
        or any(not isinstance(key, str) or key not in inputs for key in used_inputs)
        or len(used_inputs) != len(set(used_inputs))
    ):
        raise MockSessionEvidenceError("mock-session used_inputs are invalid")
    strategy = record["strategy"]
    if (
        not isinstance(strategy, Mapping)
        or set(strategy) != {"id", "explanation"}
        or not isinstance(strategy["id"], str)
        or _STRATEGY_ID.fullmatch(strategy["id"]) is None
        or not isinstance(strategy["explanation"], str)
        or not 1 <= len(strategy["explanation"].strip()) <= 500
    ):
        raise MockSessionEvidenceError("mock-session strategy is invalid")
    outputs = _bound_files(
        record["outputs"],
        run_root=run_root,
        label="outputs",
        forbid_host_outputs=True,
        stage=record["stage"],
        observed_hashes=turn_output_hashes,
        allow_turn_written_sources=agent_writes is not None,
    )
    if agent_writes is not None and not set(outputs) <= set(agent_writes):
        raise MockSessionEvidenceError(
            "mock-session output inventory differs from this turn's writes"
        )
    if proposal_artifacts is not None:
        if not proposal_artifacts:
            raise MockSessionEvidenceError(
                "mock-session finalizer proposal inventory is empty"
            )
        for index, relative in enumerate(proposal_artifacts):
            target = safe_run_path(
                run_root, relative, "proposal_artifacts[%d]" % index
            )
            if target.is_symlink() or not target.is_file():
                raise MockSessionEvidenceError(
                    "mock-session finalizer proposal artifact is unavailable: %s"
                    % relative
                )
        overlapping = set(outputs) & set(proposal_artifacts)
        if record["stage"] == "invent":
            # Marked Invent's five Concept inputs are direct Manager-authored
            # source even though the compound finalizer also lists them in the
            # accepted proposal.  Derived pre-render and lifecycle artifacts
            # remain forbidden context outputs.
            overlapping = {
                relative
                for relative in overlapping
                if _INVENT_CONCEPT_SOURCE.fullmatch(relative) is None
            }
        if overlapping:
            raise MockSessionEvidenceError(
                "mock-session outputs cite generated finalizer proposal artifacts"
            )
    deferred = record["deferred_work"]
    if (
        not isinstance(deferred, list)
        or not deferred
        or any(
            not isinstance(value, str)
            or not value.strip()
            or len(value) > 500
            for value in deferred
        )
    ):
        raise MockSessionEvidenceError("mock-session deferred_work is invalid")
    validate_stage_packet_inputs(packet_path, run_root=run_root)
    return record


def assert_no_fixture_secrets(*roots: Path, extra_text: Sequence[str] = ()) -> None:
    encoded = tuple(secret.encode("utf-8") for secret in FIXTURE_SECRETS)
    for root in roots:
        for path in root.rglob("*"):
            if (
                path.is_symlink()
                or not path.is_file()
                or path.stat().st_size > 16 * 1024 * 1024
            ):
                continue
            content = path.read_bytes()
            if any(secret in content for secret in encoded):
                raise MockSessionEvidenceError(
                    "fixture secret leaked into agent-readable state: %s" % path
                )
    for value in extra_text:
        if any(secret in value for secret in FIXTURE_SECRETS):
            raise MockSessionEvidenceError(
                "fixture secret leaked into mock-session diagnostics"
            )


def redact_diagnostics(value: str) -> str:
    result = value
    for secret in FIXTURE_SECRETS:
        result = result.replace(secret, "<redacted>")
    return result


def validate_generic_directive(source: str) -> None:
    normalized = " ".join(source.casefold().split())
    missing = [
        phrase
        for phrase in (
            "normal materialized product-run constitution",
            "current read-only stage.json",
            "context record path",
            "stage_packet_sha256",
            "do not browse the web",
        )
        if phrase not in normalized
    ]
    forbidden = []
    for fragment in _FORBIDDEN_DIRECTIVE_FRAGMENTS:
        lowered = fragment.casefold()
        present = (
            re.search(r"\b%s\b" % re.escape(lowered), normalized) is not None
            if lowered in {"spark", "forge", "quest"}
            else lowered in normalized
        )
        if present:
            forbidden.append(fragment)
    if missing or forbidden:
        raise MockSessionEvidenceError(
            "mock-session directive is not generic; missing=%r forbidden=%r"
            % (missing, forbidden)
        )


def _literal_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def mock_session_policy_violations(
    source: str, *, filename: str
) -> tuple[str, ...]:
    tree = ast.parse(source, filename=filename)
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.endswith(
            ("Transport", "FactoryServer")
        ):
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr in FORBIDDEN_TRANSPORT_FILE_MUTATORS
                ):
                    violations.append(
                        "%s:%d transport mutates files with %s"
                        % (filename, child.lineno, child.func.attr)
                    )
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ]
            for argument in arguments:
                if (
                    argument.arg == "monkeypatch"
                    or argument.arg in FORBIDDEN_INTERNAL_TERMS
                ):
                    violations.append(
                        "%s:%d injects internal %s"
                        % (filename, node.lineno, argument.arg)
                    )
        if isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            if name in {"setattr", "fixture", "fixture_factory"}:
                violations.append("%s:%d calls %s" % (filename, node.lineno, name))
            if name == "patch":
                target = _literal_text(node.args[0]) if node.args else None
                if target not in APPROVED_PATCH_TARGETS:
                    violations.append(
                        "%s:%d patches internal %s"
                        % (filename, node.lineno, target)
                    )
            for keyword in node.keywords:
                if keyword.arg in FORBIDDEN_INTERNAL_TERMS:
                    violations.append(
                        "%s:%d injects internal %s"
                        % (filename, node.lineno, keyword.arg)
                    )
    return tuple(sorted(set(violations)))


def mock_session_paths() -> tuple[Path, ...]:
    root = Path(__file__).resolve().parent
    return tuple(root / name for name in MOCK_SESSION_FILES if (root / name).exists())


def assert_helpers_are_test_only(repository: Path) -> None:
    forbidden_roots = (
        repository / "src",
        repository / ".agents" / "product-run",
    )
    needles = (
        "mock_session_harness",
        "mock-session-context",
        "WORKSHOP_RUN_MOCK_SESSION_E2E",
    )
    for root in forbidden_roots:
        for path in root.rglob("*"):
            if path.suffix not in {".py", ".md", ".json", ".toml"} or not path.is_file():
                continue
            try:
                source = path.read_text(encoding="utf-8")
            except UnicodeError:
                continue
            if any(needle in source for needle in needles):
                raise MockSessionEvidenceError(
                    "mock-session helper leaked into production path: %s" % path
                )


__all__ = [
    "APPROVED_PATCH_TARGETS",
    "CONTEXT_FIELDS",
    "CONTEXT_KIND",
    "FIXTURE_SECRETS",
    "MAX_CONTEXT_RECORD_BYTES",
    "MAX_PACKET_BYTES",
    "MOCK_SESSION_FILES",
    "MockSessionEvidenceError",
    "TRACE_KIND",
    "assert_helpers_are_test_only",
    "assert_no_fixture_secrets",
    "canonical_json",
    "mock_session_paths",
    "mock_session_policy_violations",
    "read_bounded_json",
    "redact_diagnostics",
    "safe_run_path",
    "sha256_bytes",
    "strict_object",
    "validate_context_record",
    "validate_generic_directive",
    "validate_stage_packet_inputs",
]
