"""Bounded one-stage RPC for declared custom Make and Playtest hooks.

The Workshop Manager remains the orchestrator.  It starts a fresh, short-lived
child for exactly one declared hook, gives it one content-addressed context and
one reserved output directory, and accepts only a typed result descriptor.  The
child receives no Factory credentials, no Codex credentials, and no shared
Invent/Instructions/Deliver provider objects.

Custom code is never launched without a Manager-owned OS isolation adapter.
The built-in adapter uses a verified macOS ``sandbox-exec`` profile that denies
network access and grants writes only to the one stage workspace and response
file.  Hosts where that boundary cannot be proved return a typed Need instead
of silently falling back to same-user execution.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

from .artifacts import (
    ArtifactManifest,
    _read_open_file,
    assert_packable_content,
    build_artifact_manifest,
)
from .errors import ArtifactError, ContractError
from .execution_env import minimal_tool_environment
from .jobs import (
    Feedback,
    Made,
    MakeContext,
    Need,
    PlaytestContext,
    Playtested,
    WaitingFor,
)
from .make import Wish
from .manifest import load_manifest
from .playtest import Playtest
from .taste import load_taste
from .toys import PLAYTHING_LANES, ToyBlueprint
from .workshop import (
    CUSTOMIZATION_LEVELS,
    _cad_release_from_dict,
    _cad_release_to_dict,
    _feedback_from_dict,
    _invented_from_dict,
    _manifest_from_dict,
    _playtest_result_from_dict,
)
from .world_service import WorldInventInputs, WorldPlaytestEvidence


RPC_SCHEMA_VERSION = 1
RPC_KIND_REQUEST = "workshop.contribution-hook-request"
RPC_KIND_RESPONSE = "workshop.contribution-hook-response"
RPC_STAGES = ("make", "playtest")
MAX_RPC_BYTES = 8 * 1024 * 1024
MAX_HOOK_BYTES = 1024 * 1024
DEFAULT_HOOK_TIMEOUT_SECONDS = 60 * 60
DEFAULT_ISOLATION_PROBE_TIMEOUT_SECONDS = 15
ISOLATION_CAPABILITY = "contribution-os-isolation"
_SHA256 = __import__("re").compile(r"^[0-9a-f]{64}$")


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("contribution RPC accepts only finite JSON") from exc


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _content_addressed_document(value: Mapping[str, Any], digest_key: str) -> dict:
    if not isinstance(value, Mapping) or digest_key in value:
        raise ContractError("contribution RPC document identity is malformed")
    document = dict(value)
    document[digest_key] = _sha256_json(document)
    return document


def _verify_content_addressed_document(
    value: Any, digest_key: str, label: str
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("%s must be one object" % label)
    digest = value.get(digest_key)
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise ContractError("%s has no valid content identity" % label)
    identity = {key: item for key, item in value.items() if key != digest_key}
    if _sha256_json(identity) != digest:
        raise ContractError("%s content identity changed" % label)
    return dict(value)


def _read_private_file(path: Path, label: str, maximum: int) -> bytes:
    requested = Path(path)
    try:
        expected = requested.lstat()
    except OSError as exc:
        raise ContractError("%s is missing" % label) from exc
    if (
        requested.is_symlink()
        or not stat.S_ISREG(expected.st_mode)
        or expected.st_uid != os.getuid()
        or not 1 <= expected.st_size <= maximum
    ):
        raise ContractError(
            "%s must be a bounded same-user regular file" % label
        )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(
        os, "O_NONBLOCK", 0
    )
    try:
        descriptor = os.open(str(requested), flags)
    except OSError as exc:
        raise ContractError("cannot safely open %s" % label) from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_uid != os.getuid()
            or (opened.st_dev, opened.st_ino)
            != (expected.st_dev, expected.st_ino)
            or opened.st_size > maximum
        ):
            raise ContractError("%s changed while opening" % label)
        chunks = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        source = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            not source
            or len(source) > maximum
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ContractError("%s changed while reading" % label)
        return source
    finally:
        os.close(descriptor)


def _read_json_file(path: Path, label: str) -> Mapping[str, Any]:
    source = _read_private_file(path, label, MAX_RPC_BYTES)
    try:
        value = json.loads(source.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("%s must be valid UTF-8 JSON" % label) from exc
    if not isinstance(value, Mapping):
        raise ContractError("%s must be one object" % label)
    return value


def _write_json_once(path: Path, value: Mapping[str, Any], label: str) -> None:
    source = _canonical_json(value) + b"\n"
    if len(source) > MAX_RPC_BYTES:
        raise ContractError("%s is too large" % label)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags, 0o600)
    except OSError as exc:
        raise ContractError("cannot create %s exactly once" % label) from exc
    try:
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(source):
            written += os.write(descriptor, source[written:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _safe_output_directory(base: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ContractError("%s path is malformed" % label)
    rel = Path(relative)
    if (
        rel.is_absolute()
        or ".." in rel.parts
        or rel.as_posix() != relative
        or (relative != "." and any(part in ("", ".") for part in rel.parts))
    ):
        raise ContractError("%s must stay inside its dedicated output" % label)
    requested_base = Path(base)
    if requested_base.is_symlink():
        raise ContractError("contribution output root must not be a symlink")
    try:
        resolved_base = requested_base.resolve(strict=True)
    except OSError as exc:
        raise ContractError("contribution output root is missing") from exc
    if not resolved_base.is_dir():
        raise ContractError("contribution output root must be a directory")
    candidate = requested_base if relative == "." else requested_base / rel
    current = requested_base
    for part in (() if relative == "." else rel.parts):
        current = current / part
        if current.is_symlink():
            raise ContractError("%s must not contain symlinks" % label)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_base)
    except (OSError, ValueError) as exc:
        raise ContractError("%s must stay inside its dedicated output" % label) from exc
    if not resolved.is_dir():
        raise ContractError("%s must be a directory" % label)
    return resolved


def _sealed_output_manifest(root: Path, label: str) -> ArtifactManifest:
    if Path(root).is_symlink():
        raise ContractError("%s root must not be a symlink" % label)
    first = build_artifact_manifest(root, created_at="content-addressed")
    first_paths = {entry.path for entry in first.entries}
    observed_paths = set()
    for directory, dirnames, filenames in os.walk(str(root), followlinks=False):
        base = Path(directory)
        for name in sorted(dirnames):
            path = base / name
            relative = path.relative_to(root).as_posix()
            try:
                metadata = path.lstat()
            except OSError as exc:
                raise ArtifactError(
                    "%s changed while enumerating %s" % (label, relative)
                ) from exc
            if path.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
                raise ArtifactError(
                    "%s contains a non-directory entry: %s" % (label, relative)
                )
        for name in sorted(filenames):
            path = base / name
            relative = path.relative_to(root).as_posix()
            try:
                metadata = path.lstat()
            except OSError as exc:
                raise ArtifactError(
                    "%s changed while enumerating %s" % (label, relative)
                ) from exc
            if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
                raise ArtifactError(
                    "%s contains a non-regular entry: %s" % (label, relative)
                )
            observed_paths.add(relative)
    if observed_paths != first_paths:
        raise ArtifactError(
            "%s contains files excluded from its content identity" % label
        )
    for entry in first.entries:
        source, opened = _read_open_file(root, Path(entry.path))
        if opened.st_size != entry.bytes or hashlib.sha256(source).hexdigest() != entry.sha256:
            raise ArtifactError("%s changed during Manager validation" % label)
        assert_packable_content(entry.path, source)
    second = build_artifact_manifest(root, created_at="content-addressed")
    if second.to_dict() != first.to_dict():
        raise ArtifactError("%s changed during Manager validation" % label)
    return first


def _wish_from_dict(value: Any) -> Wish:
    if not isinstance(value, Mapping) or set(value) != {
        "schema_version",
        "product_id",
        "objective",
        "constraints",
        "context",
    }:
        raise ContractError("contribution RPC Wish is malformed")
    return Wish(**dict(value))


def _feedback_sequence(value: Any) -> tuple[Feedback, ...]:
    if not isinstance(value, list):
        raise ContractError("contribution RPC feedback must be a list")
    return tuple(_feedback_from_dict(item) for item in value)


def _request_identity(
    stage: str,
    context: Any,
    inventor_root: Path,
) -> Mapping[str, Any]:
    if stage not in RPC_STAGES:
        raise ContractError("unknown contribution RPC stage")
    if stage == "make" and not isinstance(context, MakeContext):
        raise ContractError("custom Make RPC requires a MakeContext")
    if stage == "playtest" and not isinstance(context, PlaytestContext):
        raise ContractError("custom Playtest RPC requires a PlaytestContext")
    inventor_id = (
        context.inventor_id
        if stage == "make"
        else load_manifest(Path(inventor_root) / "inventor.json").inventor_id
    )
    if not isinstance(inventor_id, str):
        raise ContractError("contribution RPC requires exact inventor identity")
    common = {
        "schema_version": RPC_SCHEMA_VERSION,
        "kind": RPC_KIND_REQUEST,
        "stage": stage,
        "inventor_id": inventor_id,
        "lane": context.blueprint.lane,
        "taste_sha256": context.taste.sha256,
        "blueprint_sha256": context.blueprint.sha256,
        "workspace": str(context.workspace),
        "wish": context.wish.to_dict(),
        "round": context.round,
        "playtest_rounds": context.playtest_rounds,
    }
    if stage == "make":
        return {
            **common,
            "invented": context.invented.to_dict(),
            "feedback": [item.to_dict() for item in context.feedback],
        }
    return {
        **common,
        "made": {
            "artifact_root": str(context.made.artifact_root),
            "artifact_manifest": context.made.artifact_manifest.to_dict(),
            "product": dict(context.made.product),
        },
        "world_inputs": (
            context.world_inputs.to_dict()
            if context.world_inputs is not None
            else None
        ),
        "world_evidence": (
            context.world_evidence.to_dict()
            if context.world_evidence is not None
            else None
        ),
    }


def _validate_request(
    value: Any,
    inventor_root: Path,
    *,
    expected_stage: Optional[str] = None,
) -> Mapping[str, Any]:
    request = _verify_content_addressed_document(
        value, "request_sha256", "contribution hook request"
    )
    base = {
        "schema_version",
        "kind",
        "stage",
        "inventor_id",
        "lane",
        "taste_sha256",
        "blueprint_sha256",
        "workspace",
        "wish",
        "round",
        "playtest_rounds",
        "request_sha256",
    }
    stage = request.get("stage")
    expected_keys = base | (
        {"invented", "feedback"}
        if stage == "make"
        else {"made", "world_inputs", "world_evidence"}
        if stage == "playtest"
        else set()
    )
    if (
        set(request) != expected_keys
        or request.get("schema_version") != RPC_SCHEMA_VERSION
        or request.get("kind") != RPC_KIND_REQUEST
        or stage not in RPC_STAGES
        or (expected_stage is not None and stage != expected_stage)
    ):
        raise ContractError("contribution hook request shape is invalid")
    manifest = load_manifest(Path(inventor_root) / "inventor.json")
    lanes = tuple(item for item in manifest.capabilities if item in PLAYTHING_LANES)
    levels = tuple(
        item for item in manifest.capabilities if item in CUSTOMIZATION_LEVELS
    )
    if (
        len(lanes) != 1
        or len(levels) != 1
        or request.get("inventor_id") != manifest.inventor_id
        or request.get("lane") != lanes[0]
        or levels[0] not in ("custom-make", "custom-playtest")
        or (stage == "playtest" and levels[0] != "custom-playtest")
    ):
        raise ContractError("contribution hook request exceeds its declaration")
    wish = _wish_from_dict(request["wish"])
    taste = load_taste(inventor_root)
    blueprint = ToyBlueprint.for_lane(lanes[0])
    if (
        request.get("taste_sha256") != taste.sha256
        or request.get("blueprint_sha256") != blueprint.sha256
        or not isinstance(request.get("workspace"), str)
        or not Path(request["workspace"]).is_absolute()
        or type(request.get("round")) is not int
        or type(request.get("playtest_rounds")) is not int
    ):
        raise ContractError("contribution hook request bindings are invalid")
    wish.assert_valid()
    return request


def _context_from_request(
    request: Mapping[str, Any], inventor_root: Path
) -> MakeContext | PlaytestContext:
    stage = request["stage"]
    wish = _wish_from_dict(request["wish"])
    taste = load_taste(inventor_root)
    blueprint = ToyBlueprint.for_lane(request["lane"])
    workspace = Path(request["workspace"])
    if stage == "make":
        invented = _invented_from_dict(request["invented"])
        return MakeContext(
            wish,
            taste,
            blueprint,
            invented,
            request["round"],
            workspace,
            _feedback_sequence(request["feedback"]),
            request["playtest_rounds"],
            request["inventor_id"],
        )
    made_value = request["made"]
    if not isinstance(made_value, Mapping) or set(made_value) != {
        "artifact_root",
        "artifact_manifest",
        "product",
    }:
        raise ContractError("contribution Playtest Made input is malformed")
    made = Made(
        Path(made_value["artifact_root"]),
        _manifest_from_dict(made_value["artifact_manifest"], "RPC Made"),
        made_value["product"],
    )
    world_inputs = (
        WorldInventInputs.from_dict(request["world_inputs"])
        if request["world_inputs"] is not None
        else None
    )
    world_evidence = (
        WorldPlaytestEvidence.from_dict(request["world_evidence"])
        if request["world_evidence"] is not None
        else None
    )
    return PlaytestContext(
        wish,
        taste,
        blueprint,
        request["round"],
        made,
        workspace,
        request["playtest_rounds"],
        world_inputs,
        world_evidence,
    )


def _response_base(request: Mapping[str, Any], status: str) -> Mapping[str, Any]:
    return {
        "schema_version": RPC_SCHEMA_VERSION,
        "kind": RPC_KIND_RESPONSE,
        "stage": request["stage"],
        "request_sha256": request["request_sha256"],
        "status": status,
    }


def _waiting_response(
    request: Mapping[str, Any], waiting: WaitingFor
) -> Mapping[str, Any]:
    if any(need.job != request["stage"] for need in waiting.needs):
        raise ContractError("custom hook may wait only on its current stage")
    return _content_addressed_document(
        {
            **_response_base(request, "waiting"),
            "needs": [need.to_dict() for need in waiting.needs],
        },
        "response_sha256",
    )


def _relative_result_root(root: Path, workspace: Path, label: str) -> str:
    try:
        relative = root.resolve(strict=True).relative_to(
            workspace.resolve(strict=True)
        )
    except (OSError, ValueError) as exc:
        raise ContractError("%s must stay inside its dedicated output" % label) from exc
    value = relative.as_posix()
    return "." if value == "." else value


def _made_response(
    request: Mapping[str, Any], context: MakeContext, made: Made
) -> Mapping[str, Any]:
    if not isinstance(made, Made):
        raise ContractError("custom Make hook must return Made")
    made.assert_current()
    relative = _relative_result_root(
        made.artifact_root, context.workspace, "custom Made artifact"
    )
    return _content_addressed_document(
        {
            **_response_base(request, "result"),
            "artifact_root": relative,
            "artifact_sha256": made.artifact_sha256,
            "product": dict(made.product),
        },
        "response_sha256",
    )


def _playtested_response(
    request: Mapping[str, Any], context: PlaytestContext, playtested: Playtested
) -> Mapping[str, Any]:
    if not isinstance(playtested, Playtested):
        raise ContractError("custom Playtest hook must return Playtested")
    playtested.assert_artifact(context.made.artifact_sha256)
    playtested.evidence.assert_valid()
    evidence_manifest = playtested.evidence.evidence_manifest
    assert isinstance(evidence_manifest, ArtifactManifest)
    if evidence_manifest.to_dict() == context.made.artifact_manifest.to_dict():
        evidence = {
            "source": "product",
            "root": None,
            "artifact_sha256": context.made.artifact_sha256,
        }
    else:
        current = build_artifact_manifest(
            context.workspace, created_at=evidence_manifest.created_at
        )
        if current.to_dict() != evidence_manifest.to_dict():
            raise ContractError(
                "custom Playtest evidence must be sealed from its dedicated output"
            )
        evidence = {
            "source": "output",
            "root": ".",
            "artifact_sha256": evidence_manifest.artifact_sha256,
        }
    return _content_addressed_document(
        {
            **_response_base(request, "result"),
            "artifact_sha256": context.made.artifact_sha256,
            "evidence": evidence,
            "results": [item.to_dict() for item in playtested.evidence.results],
            "cad_release": _cad_release_to_dict(playtested.evidence.cad_release),
            "feedback": [item.to_dict() for item in playtested.feedback],
        },
        "response_sha256",
    )


def _validate_response(
    value: Any,
    request: Mapping[str, Any],
    context: MakeContext | PlaytestContext,
) -> Made | Playtested:
    response = _verify_content_addressed_document(
        value, "response_sha256", "contribution hook response"
    )
    common = {
        "schema_version",
        "kind",
        "stage",
        "request_sha256",
        "status",
        "response_sha256",
    }
    status = response.get("status")
    expected = common | (
        {"needs"}
        if status == "waiting"
        else {"artifact_root", "artifact_sha256", "product"}
        if request["stage"] == "make" and status == "result"
        else {"artifact_sha256", "evidence", "results", "cad_release", "feedback"}
        if request["stage"] == "playtest" and status == "result"
        else set()
    )
    if (
        set(response) != expected
        or response.get("schema_version") != RPC_SCHEMA_VERSION
        or response.get("kind") != RPC_KIND_RESPONSE
        or response.get("stage") != request["stage"]
        or response.get("request_sha256") != request["request_sha256"]
        or status not in ("waiting", "result")
    ):
        raise ContractError("contribution hook response shape is invalid")
    if status == "waiting":
        raw_needs = response["needs"]
        if not isinstance(raw_needs, list) or not raw_needs:
            raise ContractError("contribution hook waiting response needs typed needs")
        needs = []
        for value in raw_needs:
            if not isinstance(value, Mapping) or set(value) != {
                "job",
                "capability",
                "reason",
                "instructions",
            }:
                raise ContractError("contribution hook Need is malformed")
            need = Need(**dict(value))
            if need.job != request["stage"]:
                raise ContractError("contribution hook Need belongs to another stage")
            needs.append(need)
        raise WaitingFor(*needs)
    if request["stage"] == "make":
        assert isinstance(context, MakeContext)
        artifact_root = _safe_output_directory(
            context.workspace, response["artifact_root"], "custom Made artifact"
        )
        manifest = _sealed_output_manifest(artifact_root, "custom Made artifact")
        if response["artifact_sha256"] != manifest.artifact_sha256:
            raise ContractError("custom Made descriptor claims different artifact bytes")
        return Made(artifact_root, manifest, response["product"])

    assert isinstance(context, PlaytestContext)
    if response["artifact_sha256"] != context.made.artifact_sha256:
        raise ContractError("custom Playtest descriptor belongs to another Make")
    evidence_value = response["evidence"]
    if not isinstance(evidence_value, Mapping) or set(evidence_value) != {
        "source",
        "root",
        "artifact_sha256",
    }:
        raise ContractError("custom Playtest evidence descriptor is malformed")
    if evidence_value["source"] == "product":
        if (
            evidence_value["root"] is not None
            or evidence_value["artifact_sha256"] != context.made.artifact_sha256
        ):
            raise ContractError("custom Playtest product evidence identity differs")
        evidence_manifest = context.made.artifact_manifest
    elif evidence_value["source"] == "output":
        evidence_root = _safe_output_directory(
            context.workspace,
            evidence_value["root"],
            "custom Playtest evidence",
        )
        evidence_manifest = _sealed_output_manifest(
            evidence_root, "custom Playtest evidence"
        )
        if evidence_value["artifact_sha256"] != evidence_manifest.artifact_sha256:
            raise ContractError(
                "custom Playtest descriptor claims different evidence bytes"
            )
    else:
        raise ContractError("custom Playtest evidence source is invalid")
    raw_results = response["results"]
    raw_feedback = response["feedback"]
    if not isinstance(raw_results, list) or not isinstance(raw_feedback, list):
        raise ContractError("custom Playtest result lists are malformed")
    evidence = Playtest(
        context.made.artifact_manifest,
        tuple(_playtest_result_from_dict(item) for item in raw_results),
        _cad_release_from_dict(response["cad_release"]),
        evidence_manifest,
    )
    return Playtested(
        evidence, tuple(_feedback_from_dict(item) for item in raw_feedback)
    )


def contribution_hook_environment(inventor_root: Path) -> Mapping[str, str]:
    """Return the complete environment exposed to a custom hook child."""

    root = Path(inventor_root).resolve(strict=True)
    environment = dict(minimal_tool_environment())
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONSAFEPATH"] = "1"
    paths = []
    for relative in ("src", "contribution_src"):
        contribution_src = root / relative
        if contribution_src.is_dir() and not contribution_src.is_symlink():
            paths.append(str(contribution_src.resolve(strict=True)))
    paths.append(str(Path(__file__).resolve().parents[1]))
    environment["PYTHONPATH"] = os.pathsep.join(paths)
    return environment


@dataclass(frozen=True)
class ContributionIsolationContext:
    """Trusted paths needed to isolate one exact stage invocation."""

    stage: str
    inventor_root: Path
    hook_path: Path
    attempt: Path
    workspace: Path
    control: Path
    request_path: Path
    response_path: Path
    product_root: Optional[Path]
    environment: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.stage not in RPC_STAGES:
            raise ContractError("contribution isolation stage is invalid")
        for name in (
            "inventor_root",
            "hook_path",
            "attempt",
            "workspace",
            "control",
            "request_path",
            "response_path",
        ):
            path = Path(getattr(self, name))
            if not path.is_absolute():
                raise ContractError("contribution isolation paths must be absolute")
            object.__setattr__(self, name, path)
        if self.product_root is not None:
            product = Path(self.product_root)
            if not product.is_absolute():
                raise ContractError("contribution isolation product root must be absolute")
            object.__setattr__(self, "product_root", product)
        if not isinstance(self.environment, Mapping) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in self.environment.items()
        ):
            raise ContractError("contribution isolation environment is malformed")


IsolationAdapter = Callable[
    [Sequence[str], ContributionIsolationContext], Sequence[str]
]


def _isolation_need(stage: str, reason: str) -> WaitingFor:
    return WaitingFor(
        Need(
            stage,
            ISOLATION_CAPABILITY,
            reason,
            (
                "Run this custom contribution in a Manager-owned isolated worker. "
                "On macOS, restore the trusted root-owned /usr/bin/sandbox-exec "
                "boundary; never bypass isolation with same-user execution."
            ),
        )
    )


def _sbpl_string(value: Path | str) -> str:
    """Encode a path as one non-interpolated Seatbelt string literal."""

    text = str(value)
    if not text or any(ord(character) < 32 for character in text):
        raise ContractError("contribution isolation path is malformed")
    return json.dumps(text, ensure_ascii=False)


def _macos_isolation_profile(context: ContributionIsolationContext) -> str:
    """Build one deny-default profile with exact read and write authority."""

    launcher_root = Path(sys.executable).parent.parent
    runtime_roots = {
        Path(sys.base_prefix).resolve(strict=True),
        Path(sys.prefix).resolve(strict=True),
        Path(sys.executable).resolve(strict=True).parent.parent,
        launcher_root,
        Path(__file__).resolve().parents[1],
    }
    if launcher_root.parent.name == "opt" and str(launcher_root.parent).startswith(
        ("/usr/local/", "/opt/homebrew/")
    ):
        # Homebrew's interpreter links extension/runtime dylibs through sibling
        # opt prefixes (openssl, zstd, sqlite, and similar). This root is
        # read-only; no repository or Manager state lives beneath it.
        runtime_roots.add(launcher_root.parent)
    contribution_roots = []
    for relative in ("src", "contribution_src"):
        candidate = context.inventor_root / relative
        if candidate.is_dir() and not candidate.is_symlink():
            contribution_roots.append(candidate.resolve(strict=True))
    read_subpaths = set(runtime_roots)
    read_subpaths.update(contribution_roots)
    read_subpaths.add(context.workspace)
    if context.product_root is not None:
        read_subpaths.add(context.product_root.resolve(strict=True))
    read_literals = {
        context.attempt,
        context.control,
        context.request_path,
        context.response_path,
        context.workspace,
        context.hook_path,
        context.inventor_root / "inventor.json",
        context.inventor_root / "TASTE.md",
        Path(sys.executable),
        Path(sys.executable).resolve(strict=True),
    }
    # Seatbelt still checks metadata while traversing a launcher symlink (for
    # example Homebrew's /usr/local/opt/python@X). Grant only those ancestors,
    # never their contents.
    read_literals.update(
        parent
        for root in runtime_roots
        for parent in (root, *root.parents)
        if str(parent) not in ("/", "")
    )
    read_filters = "\n       ".join(
        ["(subpath %s)" % _sbpl_string(path) for path in sorted(read_subpaths)]
        + ["(literal %s)" % _sbpl_string(path) for path in sorted(read_literals)]
    )
    write_filters = "\n       ".join(
        (
            "(subpath %s)" % _sbpl_string(context.workspace),
            "(literal %s)" % _sbpl_string(context.response_path),
        )
    )
    # ``system.sb`` supplies only the platform runtime primitives needed to
    # start Python.  Explicit network denial overrides its local logging rule;
    # default denial leaves Manager state unwritable and other user files
    # unreadable.  Child processes inherit the same profile.
    return "\n".join(
        (
            "(version 1)",
            "(deny default)",
            '(import "system.sb")',
            "(deny network*)",
            "(allow process-exec)",
            "(allow process-info* (target self))",
            "(allow file-read* file-test-existence",
            "       %s)" % read_filters,
            "(allow file-map-executable",
            "       %s)" % read_filters,
            "(allow file-write*",
            "       %s)" % write_filters,
        )
    )


class MacOSSandboxIsolation:
    """Verified ``sandbox-exec`` adapter; never degrades to an unsafe command."""

    def __init__(
        self,
        executable: Path = Path("/usr/bin/sandbox-exec"),
        *,
        probe_runner: Optional[Callable[..., subprocess.CompletedProcess]] = None,
        probe_timeout: float = DEFAULT_ISOLATION_PROBE_TIMEOUT_SECONDS,
    ) -> None:
        if not isinstance(probe_timeout, (int, float)) or isinstance(
            probe_timeout, bool
        ) or probe_timeout <= 0:
            raise ContractError("contribution isolation probe timeout must be positive")
        self.executable = Path(executable)
        self.probe_runner = subprocess.run if probe_runner is None else probe_runner
        if not callable(self.probe_runner):
            raise ContractError("contribution isolation probe runner must be callable")
        self.probe_timeout = float(probe_timeout)

    def _trusted_executable(self, stage: str) -> Path:
        if sys.platform != "darwin":
            raise _isolation_need(
                stage,
                "Custom contributions are disabled because this host has no verified OS isolation adapter.",
            )
        requested = self.executable
        try:
            metadata = requested.lstat()
        except OSError:
            raise _isolation_need(
                stage,
                "Custom contributions are disabled because macOS sandbox-exec is unavailable.",
            )
        if (
            requested.is_symlink()
            or not requested.is_absolute()
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != 0
            or stat.S_IMODE(metadata.st_mode) & 0o022
            or not os.access(requested, os.X_OK)
        ):
            raise _isolation_need(
                stage,
                "Custom contributions are disabled because sandbox-exec is not a trusted root-owned executable.",
            )
        return requested

    def __call__(
        self,
        command: Sequence[str],
        context: ContributionIsolationContext,
    ) -> Sequence[str]:
        sandbox = self._trusted_executable(context.stage)
        profile = _macos_isolation_profile(context)
        forbidden = context.attempt / ".workshop-isolation-probe-forbidden"
        if forbidden.exists() or forbidden.is_symlink():
            raise ContractError("contribution isolation probe path is not fresh")
        probe_source = (
            "import errno,os,sys\n"
            "path=sys.argv[1]\n"
            "try:\n"
            "    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)\n"
            "except OSError as exc:\n"
            "    raise SystemExit(0 if exc.errno in (errno.EACCES,errno.EPERM) else 8)\n"
            "else:\n"
            "    os.close(fd)\n"
            "    os.unlink(path)\n"
            "    raise SystemExit(9)\n"
        )
        probe_command = (
            str(sandbox),
            "-p",
            profile,
            str(Path(sys.executable).resolve(strict=True)),
            "-c",
            probe_source,
            str(forbidden),
        )
        try:
            completed = self.probe_runner(
                list(probe_command),
                cwd=str(context.attempt),
                env=dict(context.environment),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=self.probe_timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            raise _isolation_need(
                context.stage,
                "Custom contributions are disabled because the OS isolation probe could not run.",
            )
        if (
            not isinstance(completed, subprocess.CompletedProcess)
            or completed.returncode != 0
            or forbidden.exists()
            or forbidden.is_symlink()
        ):
            raise _isolation_need(
                context.stage,
                "Custom contributions are disabled because the OS isolation probe did not prove write denial.",
            )
        return (str(sandbox), "-p", profile, *tuple(command))


def _default_isolation_adapter(
    command: Sequence[str], context: ContributionIsolationContext
) -> Sequence[str]:
    return MacOSSandboxIsolation()(command, context)


def _default_runner(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout: float,
) -> subprocess.CompletedProcess:
    process = subprocess.Popen(
        list(command),
        cwd=str(cwd),
        env=dict(env),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    try:
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (AttributeError, ProcessLookupError, PermissionError):
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (AttributeError, ProcessLookupError, PermissionError):
                process.kill()
            process.wait()
        raise ContractError("custom contribution hook timed out") from exc
    else:
        # A hook may fork and let its direct process exit. Kill anything that
        # remains in the fresh process group before validating output bytes.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (AttributeError, ProcessLookupError, PermissionError):
            pass
    return subprocess.CompletedProcess(list(command), returncode)


class ContributionHookClient:
    """Manager-side callable adapters for one declared contribution."""

    def __init__(
        self,
        inventor_root: Path,
        declared_level: str,
        *,
        runner: Callable[..., subprocess.CompletedProcess] = _default_runner,
        isolation: Optional[IsolationAdapter] = None,
        timeout: float = DEFAULT_HOOK_TIMEOUT_SECONDS,
    ) -> None:
        root = Path(inventor_root)
        if root.is_symlink():
            raise ContractError("custom contribution root must not be a symlink")
        try:
            root = root.resolve(strict=True)
        except OSError as exc:
            raise ContractError("custom contribution root is missing") from exc
        manifest = load_manifest(root / "inventor.json")
        levels = tuple(
            item for item in manifest.capabilities if item in CUSTOMIZATION_LEVELS
        )
        lanes = tuple(item for item in manifest.capabilities if item in PLAYTHING_LANES)
        if (
            declared_level not in ("custom-make", "custom-playtest")
            or levels != (declared_level,)
            or len(lanes) != 1
            or set(manifest.capabilities) != {lanes[0], declared_level}
        ):
            raise ContractError("custom contribution client exceeds its manifest")
        if not callable(runner):
            raise ContractError("custom contribution runner must be callable")
        if isolation is not None and not callable(isolation):
            raise ContractError("custom contribution isolation adapter must be callable")
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
            raise ContractError("custom contribution timeout must be positive")
        self.root = root
        self.inventor_id = manifest.inventor_id
        self.lane = lanes[0]
        self.declared_level = declared_level
        self.runner = runner
        self.isolation = (
            _default_isolation_adapter if isolation is None else isolation
        )
        self.timeout = float(timeout)

    def _hook_bytes(self) -> tuple[Path, bytes]:
        path = self.root / "hook.py"
        return path, _read_private_file(path, "custom contribution hook", MAX_HOOK_BYTES)

    def _invoke(
        self, stage: str, context: MakeContext | PlaytestContext
    ) -> Made | Playtested:
        if stage == "playtest" and self.declared_level != "custom-playtest":
            raise ContractError("custom Playtest is not declared")
        if context.blueprint.lane != self.lane:
            raise ContractError("custom hook context belongs to another lane")
        if stage == "make" and context.inventor_id != self.inventor_id:
            raise ContractError("custom Make context belongs to another Inventor")
        hook_path, hook_before = self._hook_bytes()
        workspace = Path(context.workspace)
        if (
            not workspace.is_absolute()
            or workspace.name != "workspace"
            or workspace.exists()
            or workspace.is_symlink()
        ):
            raise ContractError("custom hook workspace must be a fresh absolute path")
        attempt = workspace.parent
        try:
            attempt_metadata = attempt.lstat()
        except OSError as exc:
            raise ContractError("custom hook attempt directory is invalid") from exc
        if (
            attempt.is_symlink()
            or not stat.S_ISDIR(attempt_metadata.st_mode)
            or attempt_metadata.st_uid != os.getuid()
            or stat.S_IMODE(attempt_metadata.st_mode) & 0o077
            or any(attempt.iterdir())
        ):
            raise ContractError("custom hook attempt directory is invalid")
        control = attempt / "contribution-rpc"
        request_path = control / "request.json"
        response_path = control / "response.json"
        command = (
            str(Path(sys.executable).resolve(strict=True)),
            str(hook_path),
            stage,
            str(request_path),
            str(response_path),
        )
        environment = contribution_hook_environment(self.root)
        isolation_context = ContributionIsolationContext(
            stage=stage,
            inventor_root=self.root,
            hook_path=hook_path,
            attempt=attempt,
            workspace=workspace,
            control=control,
            request_path=request_path,
            response_path=response_path,
            product_root=(
                context.made.artifact_root
                if isinstance(context, PlaytestContext)
                else None
            ),
            environment=environment,
        )
        isolated = self.isolation(command, isolation_context)
        if (
            isinstance(isolated, (str, bytes))
            or not isinstance(isolated, Sequence)
            or not isolated
            or not all(isinstance(item, str) and item for item in isolated)
        ):
            raise ContractError("custom contribution isolation returned no safe command")
        # Isolation probes run before any RPC state is created.  A typed Need is
        # therefore retryable with the same fresh stage attempt.
        if any(attempt.iterdir()):
            raise ContractError("custom contribution isolation changed the attempt")
        try:
            control.mkdir(mode=0o700)
        except OSError as exc:
            raise ContractError("custom hook control directory must be fresh") from exc
        os.chmod(control, 0o700)
        request = _content_addressed_document(
            _request_identity(stage, context, self.root), "request_sha256"
        )
        _write_json_once(request_path, request, "custom hook request")
        request_metadata = request_path.lstat()
        completed = self.runner(
            tuple(isolated),
            cwd=attempt,
            env=environment,
            timeout=self.timeout,
        )
        if not isinstance(completed, subprocess.CompletedProcess):
            raise ContractError("custom contribution runner returned no process result")
        if completed.returncode != 0:
            raise ContractError("custom contribution hook failed")
        _, hook_after = self._hook_bytes()
        if hook_after != hook_before:
            raise ContractError("custom contribution hook changed while executing")
        try:
            after_request_metadata = request_path.lstat()
        except OSError as exc:
            raise ContractError("custom contribution hook removed its exact request") from exc
        if (
            (after_request_metadata.st_dev, after_request_metadata.st_ino)
            != (request_metadata.st_dev, request_metadata.st_ino)
            or after_request_metadata.st_size != request_metadata.st_size
        ):
            raise ContractError("custom contribution hook replaced its exact request")
        observed_request = _read_json_file(request_path, "custom hook request")
        if observed_request != request:
            raise ContractError("custom contribution hook mutated its exact request")
        try:
            control_entries = {item.name for item in control.iterdir()}
            attempt_entries = {item.name for item in attempt.iterdir()}
        except OSError as exc:
            raise ContractError("custom contribution attempt changed during validation") from exc
        if control_entries != {"request.json", "response.json"} or not attempt_entries.issubset(
            {"contribution-rpc", "workspace"}
        ):
            raise ContractError("custom contribution wrote outside its reserved output")
        response = _read_json_file(response_path, "custom hook response")
        return _validate_response(response, request, context)

    def make(self, context: MakeContext) -> Made:
        result = self._invoke("make", context)
        if not isinstance(result, Made):
            raise ContractError("custom Make RPC returned another stage's result")
        return result

    def playtest(self, context: PlaytestContext) -> Playtested:
        result = self._invoke("playtest", context)
        if not isinstance(result, Playtested):
            raise ContractError("custom Playtest RPC returned another stage's result")
        return result


def contribution_hook_main(
    inventor_root: Path,
    *,
    make: Optional[Callable[[MakeContext], Made]] = None,
    playtest: Optional[Callable[[PlaytestContext], Playtested]] = None,
    argv: Optional[Sequence[str]] = None,
) -> int:
    """Stage-only executable used by a generated ``hook.py``."""

    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 3 or arguments[0] not in RPC_STAGES:
        return 2
    stage, request_name, response_name = arguments
    request_path = Path(request_name)
    response_path = Path(response_name)
    if (
        not request_path.is_absolute()
        or not response_path.is_absolute()
        or request_path.parent != response_path.parent
        or request_path.name != "request.json"
        or response_path.name != "response.json"
    ):
        return 2
    try:
        request = _validate_request(
            _read_json_file(request_path, "custom hook request"),
            Path(inventor_root),
            expected_stage=stage,
        )
        context = _context_from_request(request, Path(inventor_root))
        operation = make if stage == "make" else playtest
        if not callable(operation):
            raise ContractError("declared custom hook is not installed")
        try:
            result = operation(context)
        except WaitingFor as waiting:
            response = _waiting_response(request, waiting)
        else:
            response = (
                _made_response(request, context, result)
                if stage == "make"
                else _playtested_response(request, context, result)
            )
        _write_json_once(response_path, response, "custom hook response")
        return 0
    except (ArtifactError, ContractError, OSError, TypeError, ValueError):
        return 1


__all__ = [
    "ContributionHookClient",
    "ContributionIsolationContext",
    "DEFAULT_HOOK_TIMEOUT_SECONDS",
    "ISOLATION_CAPABILITY",
    "IsolationAdapter",
    "MacOSSandboxIsolation",
    "MAX_RPC_BYTES",
    "RPC_KIND_REQUEST",
    "RPC_KIND_RESPONSE",
    "RPC_SCHEMA_VERSION",
    "contribution_hook_environment",
    "contribution_hook_main",
]
