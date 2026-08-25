"""Read-only compatibility for drafts made by the retired Vibe page writer.

The historical operator owned by ``reinSPQR/vibe-ideas`` is
``board-game/tools/publish.py <slug>``. It packaged an already-built game,
imported it, and authored the private draft's use-case, story blocks, print
specs, rules file, and cover images. Inventors must no longer invoke that
provider-specific writer: Workshop sends the inspected model and product facts,
then Factory generates page copy and media on the server.

This module retains the strict snapshot and authenticated readback machinery so
Alice can inspect and reconcile a draft that already has an exact sidecar. For a
new draft it fails before writing provenance, claiming an effect, launching a
subprocess, or calling a remote mutation. It only:

* binds the invocation to one candidate version and one exact local project;
* refuses every new invocation of that operator;
* verifies a strict existing receipt with authenticated draft readback; and
* returns the design/history identity that later print tests and public publish
  must keep using.

``published.json`` makes normal re-entry a no-op in the upstream operator.  An
Alice sidecar adds the input/project binding the upstream receipt does not yet
carry.  A pre-existing upstream receipt without that sidecar is treated as an
ambiguous earlier effect, never silently adopted as the current candidate.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Protocol, Sequence

from .adapters import AdapterError, AdapterReceipt, adapter_input_sha256
from .page import has_exact_alice_product_description_suffix
from .providers import (
    BoundedProcessOutputLimit,
    BoundedProcessTimeout,
    run_bounded_process,
)
from .store import DurableStore


# Alice speaks Workshop's Shop Door vocabulary. The imported Vibe operator
# still consumes its historical environment names, so translation happens only
# at that subprocess boundary. Both generations of historical names are read
# for deployed configurations, but Alice never emits them in her own state.
_SHOP_ENV_ALIASES = {
    "WORKSHOP_SHOP_OWNER_ID": ("VIBE_PORTAL_OWNER_ID", "PANDA_OWNER_ID"),
    "WORKSHOP_SHOP_BACKEND_DIR": ("VIBE_PORTAL_BACKEND_DIR", "PANDA_BACKEND_DIR"),
    "WORKSHOP_SHOP_APP_URL": ("VIBE_PORTAL_APP_URL", "PANDA_APP_URL"),
}
PAGE_BUILDER_OPERATION = "physical.create_rich_draft"
PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION = "alice.page-builder.v1"
REQUIRED_RULES_ARCHIVE_CONTRACT = "project-rules-byte-exact-v1"
REQUIRED_ALICE_DRAFT_HANDOFF_CONTRACT = "alice-text2game-export-v1"
PUBLISHDESIGN_PREFLIGHT_SCHEMA_VERSION = "alice.publishdesign-preflight.v1"
SIDECAR_SCHEMA_VERSION = 1
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SKIP_DIRS = frozenset({"__pycache__", ".git", ".claude", ".idea", ".vscode"})
_SKIP_NAMES = frozenset({".DS_Store"})
_SKIP_SUFFIXES = frozenset({".pyc", ".pyo"})
_PROVENANCE_NAME = "alice-provenance.json"
_TEXT2GAME_EXPORT_RECEIPT = ".alice-text2game-export.json"
_TEXT2GAME_IDEA_COPY = "_text2game/vibe-idea.json"
_TEXT2GAME_REPOSITORY = "https://github.com/nohope88/text2game"
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_OWNER_ID = re.compile(r"^[0-9a-f]{24}$")
_OPERATOR_DEPENDENCIES = (
    "animation_gate.py",
    "journal.py",
    "telegram.py",
)
_PUBLISHDESIGN_PREFLIGHT_FIELDS = frozenset(
    {
        "schema_version",
        "workspace_commit",
        "interpreter_sha256",
        "operator_sha256",
        "operator_dependency_sha256",
        "publishdesign_sha256",
        "diagnostic_owner_id",
        "backend_dir",
        "backend_go_mod_sha256",
        "backend_env_sha256",
        "gcs_credentials",
        "gcs_credentials_sha256",
        "dry_run",
    }
)
_MAX_PUBLISHDESIGN_PREFLIGHT_BYTES = 1 << 20
PRINTABLE_CAD_SUFFIXES = frozenset({".3mf", ".obj", ".stl"})


class PageBuilderError(AdapterError):
    """The existing draft operator or its receipt failed a deterministic check."""


class PublishDesignPreflightError(PageBuilderError):
    """The accountable manual publishdesign dry-run receipt is not proven."""


class AmbiguousPageBuilderEffect(RuntimeError):
    """A draft write may have happened, so automatic retry is unsafe."""


def _configured_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase 64-hex SHA-256")
    return value


def _regular_file_sha256(
    path: Path,
    label: str,
    *,
    executable: bool = False,
    reject_symlink: bool = True,
) -> str:
    """Hash one stable regular file without following an unreviewed link."""

    try:
        configured_metadata = path.lstat()
        if reject_symlink and stat.S_ISLNK(configured_metadata.st_mode):
            raise ValueError(f"{label} must not be a symlink")
        target = path.resolve(strict=True)
        before = target.stat()
        if not stat.S_ISREG(before.st_mode) or before.st_size <= 0:
            raise ValueError(f"{label} must be a non-empty regular file")
        if executable and not os.access(target, os.X_OK):
            raise ValueError(f"{label} must be executable")
        digest = hashlib.sha256()
        with target.open("rb") as handle:
            while True:
                chunk = handle.read(1 << 20)
                if not chunk:
                    break
                digest.update(chunk)
        after = target.stat()
    except ValueError:
        raise
    except OSError as exc:
        raise ValueError(f"{label} is unavailable: {type(exc).__name__}") from exc
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_mode,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_mode,
    ):
        raise ValueError(f"{label} changed while it was being hashed")
    return digest.hexdigest()


def build_publishdesign_preflight_receipt(
    *,
    workspace_commit: str,
    interpreter_sha256: str,
    operator_sha256: str,
    operator_dependency_sha256: Mapping[str, str],
    publishdesign_sha256: str,
    diagnostic_owner_id: str,
    backend_dir: str | Path,
    backend_go_mod_sha256: str,
    backend_env_sha256: str,
    gcs_credentials: str | Path,
    gcs_credentials_sha256: str,
    dry_run: Mapping[str, Any],
) -> bytes:
    """Build canonical manual evidence from captured publishdesign dry-run JSON.

    This helper is pure: callers supply reviewed paths and already-computed
    hashes. It never opens a local file or invokes the credential-bearing
    helper.
    """

    if not isinstance(workspace_commit, str) or _COMMIT.fullmatch(
        workspace_commit
    ) is None:
        raise ValueError("workspace_commit must be a lowercase 40-hex commit")
    hashes = {
        "interpreter_sha256": interpreter_sha256,
        "operator_sha256": operator_sha256,
        "publishdesign_sha256": publishdesign_sha256,
        "backend_go_mod_sha256": backend_go_mod_sha256,
        "backend_env_sha256": backend_env_sha256,
        "gcs_credentials_sha256": gcs_credentials_sha256,
    }
    normalized_hashes = {
        name: _configured_sha256(value, name) for name, value in hashes.items()
    }
    if not isinstance(operator_dependency_sha256, Mapping) or set(
        operator_dependency_sha256
    ) != set(_OPERATOR_DEPENDENCIES):
        raise ValueError(
            "operator_dependency_sha256 must contain exactly: "
            + ", ".join(_OPERATOR_DEPENDENCIES)
        )
    dependency_hashes = {
        name: _configured_sha256(
            operator_dependency_sha256[name],
            f"operator_dependency_sha256[{name!r}]",
        )
        for name in _OPERATOR_DEPENDENCIES
    }
    if (
        not isinstance(diagnostic_owner_id, str)
        or _OWNER_ID.fullmatch(diagnostic_owner_id) is None
    ):
        raise ValueError("diagnostic_owner_id must be a lowercase 24-hex owner id")

    def exact_absolute_path(value: str | Path, label: str) -> str:
        path = Path(value)
        rendered = str(path)
        if (
            not rendered
            or not path.is_absolute()
            or os.path.normpath(rendered) != rendered
        ):
            raise ValueError(f"{label} must be a normalized absolute path")
        return rendered

    backend = exact_absolute_path(backend_dir, "backend_dir")
    credentials = exact_absolute_path(gcs_credentials, "gcs_credentials")
    if not isinstance(dry_run, Mapping):
        raise ValueError("dry_run must be a captured JSON object")
    normalized_dry_run = dict(dry_run)
    dry_run_zip = normalized_dry_run.get("zip")
    zip_bytes = normalized_dry_run.get("zip_bytes")
    thumbs = normalized_dry_run.get("thumbs")
    thumb_paths = thumbs.split(",") if isinstance(thumbs, str) else []
    if (
        normalized_dry_run.get("dry_run") is not True
        or normalized_dry_run.get("mode") != "import"
        or normalized_dry_run.get("owner") != diagnostic_owner_id
        or not isinstance(normalized_dry_run.get("owner_name"), str)
        or not normalized_dry_run["owner_name"].strip()
        or normalized_dry_run.get("status") != "draft"
        or not isinstance(normalized_dry_run.get("db"), str)
        or not normalized_dry_run["db"].strip()
        or not isinstance(normalized_dry_run.get("bucket"), str)
        or not normalized_dry_run["bucket"].strip()
        or not isinstance(dry_run_zip, str)
        or not Path(dry_run_zip).is_absolute()
        or os.path.normpath(dry_run_zip) != dry_run_zip
        or isinstance(zip_bytes, bool)
        or not isinstance(zip_bytes, int)
        or zip_bytes <= 0
        or not thumb_paths
        or any(
            not path
            or not Path(path).is_absolute()
            or os.path.normpath(path) != path
            for path in thumb_paths
        )
    ):
        raise ValueError(
            "dry_run must prove an exact first-import owner, archive, draft status, "
            "database, and bucket"
        )
    document = {
        "schema_version": PUBLISHDESIGN_PREFLIGHT_SCHEMA_VERSION,
        "workspace_commit": workspace_commit,
        "interpreter_sha256": normalized_hashes["interpreter_sha256"],
        "operator_sha256": normalized_hashes["operator_sha256"],
        "operator_dependency_sha256": dict(sorted(dependency_hashes.items())),
        "publishdesign_sha256": normalized_hashes["publishdesign_sha256"],
        "diagnostic_owner_id": diagnostic_owner_id,
        "backend_dir": backend,
        "backend_go_mod_sha256": normalized_hashes["backend_go_mod_sha256"],
        "backend_env_sha256": normalized_hashes["backend_env_sha256"],
        "gcs_credentials": credentials,
        "gcs_credentials_sha256": normalized_hashes[
            "gcs_credentials_sha256"
        ],
        "dry_run": normalized_dry_run,
    }
    return _canonical_document(document)


def _validated_operator_source_sha256(path: Path) -> str:
    """Verify the audited Vibe operator's static exact-rules declaration."""

    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("rich-page operator must be a regular non-symlink file")
        source = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise ValueError(f"cannot read rich-page operator: {type(exc).__name__}") from exc
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_mode,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_mode,
    ):
        raise ValueError("rich-page operator changed while it was being hashed")
    if not source or len(source) > (1 << 20):
        raise ValueError("rich-page operator source must be 1..1048576 bytes")
    try:
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, ValueError) as exc:
        raise ValueError("rich-page operator source is not valid Python") from exc

    required = {
        "RULES_ARCHIVE_CONTRACT": REQUIRED_RULES_ARCHIVE_CONTRACT,
        "ALICE_DRAFT_HANDOFF_CONTRACT": REQUIRED_ALICE_DRAFT_HANDOFF_CONTRACT,
    }
    declarations: dict[str, list[object]] = {name: [] for name in required}
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            if (
                len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id in required
            ):
                declarations[statement.targets[0].id].append(statement.value)
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id in required
        ):
            declarations[statement.target.id].append(statement.value)
    for name, expected in required.items():
        values = declarations[name]
        if len(values) != 1:
            raise ValueError(
                f"rich-page operator must declare {name} exactly once"
            )
        declaration = values[0]
        if not isinstance(declaration, ast.Constant) or declaration.value != expected:
            raise ValueError(
                f"rich-page operator does not guarantee {expected}"
            )
    return hashlib.sha256(source).hexdigest()


class DraftReadback(Protocol):
    """Authenticated owner read of ``GET /api/v1/designs/{slug}``."""

    def get_design(self, slug_or_id: str) -> Mapping[str, Any]: ...

    def project_file_sha256(self, project_url: str, relative_path: str) -> str: ...


class PageBuilderReadback:
    """Authenticated design read plus streamed hashes from its immutable CDN folder."""

    def __init__(
        self,
        design_transport: Any,
        *,
        timeout_seconds: int = 180,
        maximum_file_bytes: int = 100 << 20,
        allowed_project_hosts: Sequence[str] = (),
    ) -> None:
        if not hasattr(design_transport, "get_design"):
            raise ValueError("page-builder design transport needs get_design")
        if timeout_seconds <= 0 or maximum_file_bytes <= 0:
            raise ValueError("page-builder readback limits must be positive")
        self.design_transport = design_transport
        self.timeout_seconds = int(timeout_seconds)
        self.maximum_file_bytes = int(maximum_file_bytes)
        hosts = tuple(
            sorted(
                {
                    str(host).strip().casefold()
                    for host in allowed_project_hosts
                    if str(host).strip()
                }
            )
        )
        if not hosts or any(
            "/" in host
            or ":" in host
            or "@" in host
            or host.startswith(".")
            or host.endswith(".")
            for host in hosts
        ):
            raise ValueError(
                "page-builder readback requires explicit DNS host allowlist entries"
            )
        self.allowed_project_hosts = frozenset(hosts)
        self._opener = urllib.request.build_opener(_RejectRedirects())

    def get_design(self, slug_or_id: str) -> Mapping[str, Any]:
        return self.design_transport.get_design(slug_or_id)

    def project_file_sha256(self, project_url: str, relative_path: str) -> str:
        try:
            parsed_project = urllib.parse.urlsplit(project_url)
            project_port = parsed_project.port
        except ValueError as exc:
            raise PageBuilderError("project_url is malformed") from exc
        if (
            parsed_project.scheme != "https"
            or not parsed_project.hostname
            or parsed_project.hostname.casefold() not in self.allowed_project_hosts
            or parsed_project.username is not None
            or parsed_project.password is not None
            or project_port not in (None, 443)
            or parsed_project.query
            or parsed_project.fragment
        ):
            raise PageBuilderError(
                "project_url is not an approved credential-free HTTPS CDN origin"
            )
        relative = PurePosixPath(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise PageBuilderError(f"unsafe remote project path {relative_path!r}")
        url = (
            project_url.rstrip("/")
            + "/"
            + urllib.parse.quote(relative.as_posix(), safe="/")
        )
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Alice-PageBuilder/1"},
            method="GET",
        )
        digest = hashlib.sha256()
        total = 0
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                while True:
                    chunk = response.read(1 << 20)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > self.maximum_file_bytes:
                        raise PageBuilderError(
                            f"remote project file exceeds {self.maximum_file_bytes} bytes"
                        )
                    digest.update(chunk)
        except (OSError, urllib.error.URLError) as exc:
            raise PageBuilderError(f"could not hash remote project file {url}") from exc
        return digest.hexdigest()


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Keep anonymous project reads on the approved CDN host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


@dataclass(frozen=True, slots=True)
class ProjectSnapshot:
    root: Path
    files: tuple[dict[str, Any], ...]
    project_sha256: str


def _verify_text2game_export_handoff(
    *,
    idea_dir: Path,
    project: Path,
    snapshot: ProjectSnapshot,
    artifact_hashes: Mapping[str, str],
    cad: Mapping[str, Any],
    dfm: Mapping[str, Any],
    candidate_id: str,
    candidate_version: int,
    candidate_content_sha256: str,
    production_slug: str,
    rules_sha256: str,
    rules_file_sha256: str,
) -> dict[str, Any]:
    """Bind Vibe's root idea file to an immutable text2game export receipt."""

    receipt_path = idea_dir / _TEXT2GAME_EXPORT_RECEIPT
    lineage_keys = {
        "vibe_idea_sha256",
        "text2game_source_artifact_hashes",
        "text2game_source_artifact_hashes_sha256",
        "text2game_export_receipt_sha256",
        "text2game_source_snapshot_sha256",
        "text2game_repo_url",
        "text2game_repo_commit",
    }
    declares_text2game = any(
        any(key in content for key in lineage_keys) for content in (cad, dfm)
    )
    if not receipt_path.exists() and not receipt_path.is_symlink():
        if declares_text2game:
            raise PageBuilderError(
                "CAD/DFM declare text2game lineage but its export receipt is missing"
            )
        return {}
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise PageBuilderError("text2game export receipt must be a regular file")
    receipt_bytes = receipt_path.read_bytes()
    receipt = _load_object(receipt_path, "text2game export receipt")
    canonical_receipt = _canonical_document(receipt)
    if receipt_bytes != canonical_receipt:
        raise PageBuilderError("text2game export receipt is not canonical")
    expected_keys = {
        "schema_version",
        "kind",
        "candidate_id",
        "candidate_version",
        "candidate_content_sha256",
        "production_slug",
        "rules_sha256",
        "rules_file_sha256",
        "idea_sha256",
        "project_sha256",
        "artifact_hashes",
        "source_artifact_hashes",
        "source_artifact_hashes_sha256",
        "source_snapshot_sha256",
        "source_repo_url",
        "source_repo_commit",
        "handoff",
    }
    if set(receipt) != expected_keys:
        raise PageBuilderError("text2game export receipt fields are not exact")
    if (
        receipt.get("schema_version") != 1
        or receipt.get("kind") != "alice.text2game-export-receipt"
        or receipt.get("candidate_id") != candidate_id
        or isinstance(receipt.get("candidate_version"), bool)
        or not isinstance(receipt.get("candidate_version"), int)
        or receipt.get("candidate_version") != candidate_version
        or receipt.get("candidate_content_sha256") != candidate_content_sha256
        or receipt.get("production_slug") != production_slug
        or receipt.get("rules_sha256") != rules_sha256
        or receipt.get("rules_file_sha256") != rules_file_sha256
        or receipt.get("project_sha256") != snapshot.project_sha256
        or receipt.get("source_repo_url") != _TEXT2GAME_REPOSITORY
        or _COMMIT.fullmatch(str(receipt.get("source_repo_commit", ""))) is None
    ):
        raise PageBuilderError("text2game export receipt identity does not match")
    expected_handoff = {
        "vibe_queue_transition_required": False,
        "vibe_queue_transition_performed": False,
        "publisher_invoked": False,
        "publisher_exact_rules_passthrough_required": True,
        "publisher_rules_archive_contract": REQUIRED_RULES_ARCHIVE_CONTRACT,
        "publisher_alice_draft_handoff_contract": (
            REQUIRED_ALICE_DRAFT_HANDOFF_CONTRACT
        ),
    }
    if receipt.get("handoff") != expected_handoff:
        raise PageBuilderError("text2game export handoff contract is not exact")

    snapshot_hashes = {
        str(item["path"]): str(item["sha256"]) for item in snapshot.files
    }
    if receipt.get("artifact_hashes") != snapshot_hashes:
        raise PageBuilderError("text2game receipt does not bind the current project")
    if dict(artifact_hashes) != snapshot_hashes:
        raise PageBuilderError(
            "CAD/DFM artifact hashes must contain the complete text2game export"
        )

    source_hashes_raw = receipt.get("source_artifact_hashes")
    if not isinstance(source_hashes_raw, Mapping) or not source_hashes_raw:
        raise PageBuilderError("text2game source artifact hashes are missing")
    source_hashes: dict[str, str] = {}
    for relative, digest in source_hashes_raw.items():
        if not isinstance(relative, str) or not relative:
            raise PageBuilderError("text2game source artifact path is invalid")
        path = PurePosixPath(relative)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "." in path.parts
            or str(path) != relative
        ):
            raise PageBuilderError("text2game source artifact path is unsafe")
        source_hashes[relative] = _require_sha256(
            digest, f"text2game source artifact {relative!r}"
        )
    source_hashes_sha256 = hashlib.sha256(
        json.dumps(
            source_hashes,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    if receipt.get("source_artifact_hashes_sha256") != source_hashes_sha256:
        raise PageBuilderError("text2game source artifact manifest hash is wrong")

    idea_path = idea_dir / "idea.json"
    idea_copy = project / _TEXT2GAME_IDEA_COPY
    for label, path in (("root idea.json", idea_path), ("project idea copy", idea_copy)):
        if path.is_symlink() or not path.is_file():
            raise PageBuilderError(f"text2game {label} must be a regular file")
    idea_bytes = idea_path.read_bytes()
    if not idea_bytes or idea_copy.read_bytes() != idea_bytes:
        raise PageBuilderError(
            "Vibe root idea.json is not the exact reviewed in-project idea copy"
        )
    _load_object(idea_path, "Vibe root idea.json")
    idea_sha256 = hashlib.sha256(idea_bytes).hexdigest()
    if receipt.get("idea_sha256") != idea_sha256:
        raise PageBuilderError("Vibe idea.json does not match its export hash")

    export_receipt_sha256 = hashlib.sha256(
        canonical_receipt
    ).hexdigest()
    source_snapshot_sha256 = _require_sha256(
        receipt.get("source_snapshot_sha256"),
        "text2game source_snapshot_sha256",
    )
    lineage = {
        "candidate_id": candidate_id,
        "candidate_version": candidate_version,
        "vibe_idea_sha256": idea_sha256,
        "text2game_source_artifact_hashes": source_hashes,
        "text2game_source_artifact_hashes_sha256": source_hashes_sha256,
        "text2game_export_receipt_sha256": export_receipt_sha256,
        "text2game_source_snapshot_sha256": source_snapshot_sha256,
        "text2game_repo_url": _TEXT2GAME_REPOSITORY,
        "text2game_repo_commit": receipt["source_repo_commit"],
    }
    for source, content in (("physical.cad", cad), ("physical.dfm", dfm)):
        for key, expected in lineage.items():
            if content.get(key) != expected:
                raise PageBuilderError(f"{source} {key} mismatch")
    return {
        "receipt_sha256": export_receipt_sha256,
        "vibe_idea_sha256": idea_sha256,
        "source_artifact_hashes_sha256": source_hashes_sha256,
        "source_snapshot_sha256": source_snapshot_sha256,
        "source_repo_url": _TEXT2GAME_REPOSITORY,
        "source_repo_commit": receipt["source_repo_commit"],
    }


class ShopDoorAdapter:
    """Inspect legacy rich drafts; refuse the retired inventor-side writer.

    ``operator_command`` must be exactly one absolute interpreter plus the
    existing entry point, for example
    ``[/venv/bin/python, "/srv/vibe-ideas/board-game/tools/publish.py"]``. The
    The command and source pins remain part of reconciliation evidence, but the
    adapter never launches the command. New drafts must go through Workshop's
    model-only publishing boundary.
    """

    capabilities = (
        "authenticated_server_content_readback",
        "legacy_rich_draft_reconciliation",
    )

    def __init__(
        self,
        workspace: str | Path,
        operator_command: Sequence[str],
        readback: DraftReadback,
        store: DurableStore,
        *,
        workspace_commit: str,
        interpreter_sha256: str,
        operator_sha256: str,
        operator_dependency_sha256: Mapping[str, str],
        publishdesign_sha256: str,
        publishdesign_preflight_receipt: str | Path,
        publishdesign_preflight_sha256: str,
        git_binary: str | Path,
        diagnostic_owner_id: str,
        timeout_seconds: int = 3_600,
        maximum_stdout_bytes: int = 1 << 20,
        maximum_stderr_bytes: int = 1 << 16,
        shutdown_grace_seconds: float = 1.0,
        diagnostic_design_id: str = "",
        allowed_environment: Sequence[str] = (
            "PATH",
            "HOME",
            "LANG",
            "LC_ALL",
            "TMPDIR",
            "WORKSHOP_SHOP_OWNER_ID",
            "WORKSHOP_SHOP_BACKEND_DIR",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "WORKSHOP_SHOP_APP_URL",
        ),
    ) -> None:
        configured_workspace = Path(workspace).expanduser()
        self.workspace = configured_workspace.resolve()
        if not self.workspace.is_dir():
            raise ValueError(f"page-builder workspace does not exist: {self.workspace}")
        if not isinstance(workspace_commit, str) or _COMMIT.fullmatch(
            workspace_commit
        ) is None:
            raise ValueError("workspace_commit must be a lowercase 40-hex commit")
        self.workspace_commit = workspace_commit
        self.interpreter_sha256 = _configured_sha256(
            interpreter_sha256, "interpreter_sha256"
        )
        self.operator_sha256 = _configured_sha256(
            operator_sha256, "operator_sha256"
        )
        self.publishdesign_sha256 = _configured_sha256(
            publishdesign_sha256, "publishdesign_sha256"
        )
        self.publishdesign_preflight_sha256 = _configured_sha256(
            publishdesign_preflight_sha256,
            "publishdesign_preflight_sha256",
        )
        configured_preflight_receipt = Path(
            publishdesign_preflight_receipt
        ).expanduser()
        if not configured_preflight_receipt.is_absolute():
            raise ValueError("publishdesign_preflight_receipt must be an absolute path")
        self.publishdesign_preflight_receipt = configured_preflight_receipt
        if not isinstance(operator_dependency_sha256, Mapping) or set(
            operator_dependency_sha256
        ) != set(_OPERATOR_DEPENDENCIES):
            raise ValueError(
                "operator_dependency_sha256 must contain exactly: "
                + ", ".join(_OPERATOR_DEPENDENCIES)
            )
        self.operator_dependency_sha256 = {
            name: _configured_sha256(
                operator_dependency_sha256[name],
                f"operator_dependency_sha256[{name!r}]",
            )
            for name in _OPERATOR_DEPENDENCIES
        }
        if (
            not isinstance(diagnostic_owner_id, str)
            or _OWNER_ID.fullmatch(diagnostic_owner_id) is None
        ):
            raise ValueError(
                "diagnostic_owner_id must be a lowercase 24-hex owner id"
            )
        self.diagnostic_owner_id = diagnostic_owner_id
        if len(operator_command) != 2 or any(
            not isinstance(value, str) or not value for value in operator_command
        ):
            raise ValueError(
                "page-builder operator command must be exactly "
                "[absolute_interpreter, absolute_publish.py]"
            )
        operator_path = self.workspace / "board-game" / "tools" / "publish.py"
        if operator_path.is_symlink():
            raise ValueError("existing rich-page operator must not be a symlink")
        expected_operator = operator_path.resolve()
        if not expected_operator.is_file() or self.workspace not in expected_operator.parents:
            raise ValueError(
                f"existing rich-page operator is missing: {expected_operator}"
            )
        operator_source_sha256 = _validated_operator_source_sha256(expected_operator)
        if operator_source_sha256 != self.operator_sha256:
            raise ValueError("page-builder publish.py does not match operator_sha256")
        interpreter = Path(operator_command[0]).expanduser()
        configured_operator = Path(operator_command[1]).expanduser()
        configured_expected_operator = (
            configured_workspace / "board-game" / "tools" / "publish.py"
        )
        if not interpreter.is_absolute() or not configured_operator.is_absolute():
            raise ValueError(
                "page-builder operator command must use absolute interpreter "
                "and publish.py paths"
            )
        actual_interpreter_sha256 = _regular_file_sha256(
            interpreter,
            "page-builder interpreter",
            executable=True,
            reject_symlink=False,
        )
        resolved_interpreter = interpreter.resolve(strict=True)
        if actual_interpreter_sha256 != self.interpreter_sha256:
            raise ValueError(
                "page-builder interpreter does not match interpreter_sha256"
            )
        if (
            configured_operator.is_symlink()
            or str(configured_operator) != str(configured_expected_operator)
            or configured_operator.resolve() != expected_operator
        ):
            raise ValueError(
                "page-builder command must be exactly the workspace's existing "
                "board-game/tools/publish.py entry point with no wrappers or flags"
            )
        self.operator_command = (
            str(interpreter),
            str(configured_operator),
        )
        self._resolved_interpreter = resolved_interpreter
        self._expected_operator = expected_operator
        self._operator_dependency_paths = {
            name: expected_operator.parent / name for name in _OPERATOR_DEPENDENCIES
        }
        for name, dependency in self._operator_dependency_paths.items():
            actual = _regular_file_sha256(
                dependency,
                f"page-builder operator dependency {name}",
            )
            if actual != self.operator_dependency_sha256[name]:
                raise ValueError(
                    f"page-builder operator dependency {name} does not match its SHA-256"
                )
        self._publishdesign = expected_operator.parent / "bin" / "publishdesign"
        actual_publishdesign_sha256 = _regular_file_sha256(
            self._publishdesign,
            "page-builder publishdesign",
            executable=True,
        )
        if actual_publishdesign_sha256 != self.publishdesign_sha256:
            raise ValueError(
                "page-builder publishdesign does not match publishdesign_sha256"
            )
        configured_git = Path(git_binary).expanduser()
        if not configured_git.is_absolute():
            raise ValueError("git_binary must be an absolute path")
        self._git_sha256 = _regular_file_sha256(
            configured_git,
            "page-builder git_binary",
            executable=True,
            reject_symlink=False,
        )
        self.git_binary = configured_git
        self._resolved_git_binary = configured_git.resolve(strict=True)
        if isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
            raise ValueError("page-builder timeout_seconds must be positive")
        self.timeout_seconds = int(timeout_seconds)
        for name, value in (
            ("maximum_stdout_bytes", maximum_stdout_bytes),
            ("maximum_stderr_bytes", maximum_stderr_bytes),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"page-builder {name} must be positive")
        if (
            isinstance(shutdown_grace_seconds, bool)
            or not isinstance(shutdown_grace_seconds, (int, float))
            or float(shutdown_grace_seconds) <= 0
        ):
            raise ValueError("page-builder shutdown_grace_seconds must be positive")
        self.maximum_stdout_bytes = maximum_stdout_bytes
        self.maximum_stderr_bytes = maximum_stderr_bytes
        self.shutdown_grace_seconds = float(shutdown_grace_seconds)
        self.readback = readback
        self.store = store
        if not isinstance(diagnostic_design_id, str):
            raise ValueError("diagnostic_design_id must be a string")
        self.diagnostic_design_id = diagnostic_design_id.strip()
        self.environment = {
            name: os.environ[name]
            for name in allowed_environment
            if name in os.environ
        }
        allowed_environment_names = frozenset(allowed_environment)
        for workshop_name, aliases in _SHOP_ENV_ALIASES.items():
            semantic_names = (workshop_name, *aliases)
            if allowed_environment_names.isdisjoint(semantic_names):
                continue
            configured = {
                name: os.environ[name]
                for name in semantic_names
                if name in os.environ
            }
            if len(set(configured.values())) > 1:
                raise ValueError(
                    f"{workshop_name} conflicts with a legacy Shop Door alias"
                )
            for name in semantic_names:
                self.environment.pop(name, None)
            if configured:
                self.environment[workshop_name] = next(iter(configured.values()))
        try:
            self._assert_interpreter_isolation_support()
            self._assert_workspace_integrity()
        except PageBuilderError as exc:
            raise ValueError(str(exc)) from exc

    def _assert_interpreter_isolation_support(self) -> None:
        """Prove the reviewed interpreter accepts Alice's fixed isolation flags."""

        try:
            with tempfile.TemporaryDirectory(
                prefix="alice-page-builder-probe-"
            ) as pycache:
                script = (
                    "import sys;"
                    "raise SystemExit(0 if "
                    "sys.flags.isolated == 1 and "
                    "sys.flags.dont_write_bytecode == 1 and "
                    "sys.flags.no_site == 1 and "
                    "sys.pycache_prefix == sys.argv[1] else 9)"
                )
                result = run_bounded_process(
                    (
                        str(self._resolved_interpreter),
                        "-I",
                        "-B",
                        "-S",
                        "-X",
                        f"pycache_prefix={pycache}",
                        "-c",
                        script,
                        pycache,
                    ),
                    input_bytes=b"",
                    timeout_seconds=min(30, self.timeout_seconds),
                    stdout_limit_bytes=4_096,
                    stderr_limit_bytes=16_384,
                    shutdown_grace_seconds=self.shutdown_grace_seconds,
                    env={"LANG": "C", "LC_ALL": "C"},
                )
        except (BoundedProcessTimeout, BoundedProcessOutputLimit, OSError) as exc:
            raise PageBuilderError(
                "page-builder interpreter isolation probe failed"
            ) from exc
        if result.returncode != 0 or result.stdout:
            raise PageBuilderError(
                "page-builder interpreter does not support the required isolation flags"
            )

    def _assert_git_binary_integrity(self) -> None:
        try:
            target = self.git_binary.resolve(strict=True)
            actual = _regular_file_sha256(
                self.git_binary,
                "page-builder git_binary",
                executable=True,
                reject_symlink=False,
            )
        except ValueError as exc:
            raise PageBuilderError(str(exc)) from exc
        if target != self._resolved_git_binary or actual != self._git_sha256:
            raise PageBuilderError("page-builder pinned git executable changed")

    def _git(self, *arguments: str, stdout_limit: int = 4 << 20) -> bytes:
        self._assert_git_binary_integrity()
        environment = {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
        if "TMPDIR" in os.environ:
            environment["TMPDIR"] = os.environ["TMPDIR"]
        try:
            result = run_bounded_process(
                (
                    str(self._resolved_git_binary),
                    "--no-replace-objects",
                    "-c",
                    "core.fsmonitor=false",
                    "-c",
                    "core.untrackedCache=false",
                    "-C",
                    str(self.workspace),
                    *arguments,
                ),
                input_bytes=b"",
                timeout_seconds=min(60, self.timeout_seconds),
                stdout_limit_bytes=stdout_limit,
                stderr_limit_bytes=65_536,
                shutdown_grace_seconds=self.shutdown_grace_seconds,
                env=environment,
            )
        except (BoundedProcessTimeout, BoundedProcessOutputLimit, OSError) as exc:
            raise PageBuilderError(
                f"page-builder Vibe git inspection failed ({type(exc).__name__})"
            ) from exc
        if result.returncode != 0:
            raise PageBuilderError(
                "page-builder Vibe git inspection failed; "
                f"stderr_sha256={result.stderr_sha256}"
            )
        return result.stdout

    def _assert_execution_integrity(self) -> None:
        try:
            interpreter = Path(self.operator_command[0])
            if interpreter.resolve(strict=True) != self._resolved_interpreter:
                raise ValueError("page-builder interpreter target changed")
            if _regular_file_sha256(
                interpreter,
                "page-builder interpreter",
                executable=True,
                reject_symlink=False,
            ) != self.interpreter_sha256:
                raise ValueError("page-builder interpreter bytes changed")

            configured_operator = Path(self.operator_command[1])
            if (
                configured_operator.is_symlink()
                or configured_operator.resolve(strict=True) != self._expected_operator
            ):
                raise ValueError("page-builder publish.py target changed")
            source_sha256 = _validated_operator_source_sha256(configured_operator)
            if source_sha256 != self.operator_sha256:
                raise ValueError("page-builder publish.py source changed")

            for name, dependency in self._operator_dependency_paths.items():
                if _regular_file_sha256(
                    dependency,
                    f"page-builder operator dependency {name}",
                ) != self.operator_dependency_sha256[name]:
                    raise ValueError(
                        f"page-builder operator dependency {name} changed"
                    )
            if _regular_file_sha256(
                self._publishdesign,
                "page-builder publishdesign",
                executable=True,
            ) != self.publishdesign_sha256:
                raise ValueError("page-builder publishdesign bytes changed")
        except (OSError, ValueError) as exc:
            raise PageBuilderError(str(exc)) from exc

    def _assert_local_dependencies(self) -> None:
        """Require the explicit local backend inputs publish.py will consume."""

        workspace_env = self.workspace / ".env"
        if workspace_env.exists() or workspace_env.is_symlink():
            raise PageBuilderError(
                "page-builder workspace .env is forbidden; configure explicit inputs"
            )
        owner_id = self.environment.get("WORKSHOP_SHOP_OWNER_ID")
        if owner_id != self.diagnostic_owner_id:
            raise PageBuilderError(
                "WORKSHOP_SHOP_OWNER_ID must exactly match diagnostic_owner_id"
            )
        backend_value = self.environment.get("WORKSHOP_SHOP_BACKEND_DIR", "")
        backend = Path(backend_value).expanduser()
        if not backend_value or not backend.is_absolute():
            raise PageBuilderError(
                "WORKSHOP_SHOP_BACKEND_DIR must be an explicit absolute path"
            )
        try:
            backend_metadata = backend.lstat()
        except OSError as exc:
            raise PageBuilderError("WORKSHOP_SHOP_BACKEND_DIR is unavailable") from exc
        if not stat.S_ISDIR(backend_metadata.st_mode) or backend.is_symlink():
            raise PageBuilderError(
                "WORKSHOP_SHOP_BACKEND_DIR must be a real non-symlink directory"
            )
        for name in ("go.mod", ".env"):
            dependency = backend / name
            try:
                metadata = dependency.lstat()
            except OSError as exc:
                raise PageBuilderError(
                    f"WORKSHOP_SHOP_BACKEND_DIR is missing required {name}"
                ) from exc
            if (
                not stat.S_ISREG(metadata.st_mode)
                or stat.S_ISLNK(metadata.st_mode)
                or metadata.st_size <= 0
                or not os.access(dependency, os.R_OK)
                or (
                    name == ".env"
                    and (
                        metadata.st_uid != os.geteuid()
                        or stat.S_IMODE(metadata.st_mode) & 0o077
                    )
                )
            ):
                raise PageBuilderError(
                    f"WORKSHOP_SHOP_BACKEND_DIR {name} must be a readable"
                    + (" owner-only" if name == ".env" else "")
                    + " regular file"
                )

        credential_value = self.environment.get(
            "GOOGLE_APPLICATION_CREDENTIALS", ""
        )
        credential = Path(credential_value).expanduser()
        if not credential_value or not credential.is_absolute():
            raise PageBuilderError(
                "GOOGLE_APPLICATION_CREDENTIALS must be an explicit absolute path"
            )
        try:
            credential_metadata = credential.lstat()
        except OSError as exc:
            raise PageBuilderError(
                "GOOGLE_APPLICATION_CREDENTIALS is unavailable"
            ) from exc
        if (
            not stat.S_ISREG(credential_metadata.st_mode)
            or stat.S_ISLNK(credential_metadata.st_mode)
            or credential_metadata.st_size <= 0
            or credential_metadata.st_uid != os.geteuid()
            or stat.S_IMODE(credential_metadata.st_mode) & 0o077
            or not os.access(credential, os.R_OK)
        ):
            raise PageBuilderError(
                "GOOGLE_APPLICATION_CREDENTIALS must be a readable owner-only "
                "non-symlink regular file"
            )

    def _assert_publishdesign_preflight_receipt(self) -> None:
        """Rebind accountable manual dry-run evidence to every local byte pin."""

        path = self.publishdesign_preflight_receipt
        try:
            before = path.lstat()
            if (
                not stat.S_ISREG(before.st_mode)
                or stat.S_ISLNK(before.st_mode)
                or before.st_size <= 0
                or before.st_size > _MAX_PUBLISHDESIGN_PREFLIGHT_BYTES
                or before.st_uid != os.geteuid()
                or stat.S_IMODE(before.st_mode) & 0o077
                or not os.access(path, os.R_OK)
            ):
                raise PublishDesignPreflightError(
                    "publishdesign preflight receipt must be an owner-only "
                    "non-symlink regular file of 1..1048576 bytes"
                )
            raw = path.read_bytes()
            after = path.lstat()
        except PublishDesignPreflightError:
            raise
        except OSError as exc:
            raise PublishDesignPreflightError(
                "publishdesign preflight receipt is unavailable"
            ) from exc
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_mode,
            before.st_uid,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_mode,
            after.st_uid,
        ):
            raise PublishDesignPreflightError(
                "publishdesign preflight receipt changed while being read"
            )
        if hashlib.sha256(raw).hexdigest() != self.publishdesign_preflight_sha256:
            raise PublishDesignPreflightError(
                "publishdesign preflight receipt SHA-256 does not match configuration"
            )

        def reject_constant(value: str) -> None:
            raise ValueError(f"non-finite JSON constant {value!r}")

        try:
            receipt = json.loads(
                raw.decode("utf-8", errors="strict"),
                parse_constant=reject_constant,
            )
        except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
            raise PublishDesignPreflightError(
                "publishdesign preflight receipt is not strict JSON"
            ) from exc
        if not isinstance(receipt, Mapping) or set(receipt) != set(
            _PUBLISHDESIGN_PREFLIGHT_FIELDS
        ):
            raise PublishDesignPreflightError(
                "publishdesign preflight receipt top-level fields are not exact"
            )
        try:
            canonical = build_publishdesign_preflight_receipt(
                workspace_commit=receipt["workspace_commit"],
                interpreter_sha256=receipt["interpreter_sha256"],
                operator_sha256=receipt["operator_sha256"],
                operator_dependency_sha256=receipt[
                    "operator_dependency_sha256"
                ],
                publishdesign_sha256=receipt["publishdesign_sha256"],
                diagnostic_owner_id=receipt["diagnostic_owner_id"],
                backend_dir=receipt["backend_dir"],
                backend_go_mod_sha256=receipt["backend_go_mod_sha256"],
                backend_env_sha256=receipt["backend_env_sha256"],
                gcs_credentials=receipt["gcs_credentials"],
                gcs_credentials_sha256=receipt["gcs_credentials_sha256"],
                dry_run=receipt["dry_run"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PublishDesignPreflightError(
                "publishdesign preflight receipt values are invalid"
            ) from exc
        if raw != canonical:
            raise PublishDesignPreflightError(
                "publishdesign preflight receipt is not canonical"
            )

        try:
            backend = Path(self.environment["WORKSHOP_SHOP_BACKEND_DIR"]).resolve(
                strict=True
            )
            credentials = Path(
                self.environment["GOOGLE_APPLICATION_CREDENTIALS"]
            ).resolve(strict=True)
        except (KeyError, OSError) as exc:
            raise PublishDesignPreflightError(
                "publishdesign preflight local paths are unavailable"
            ) from exc
        try:
            current_bindings: dict[str, Any] = {
                "schema_version": PUBLISHDESIGN_PREFLIGHT_SCHEMA_VERSION,
                "workspace_commit": self.workspace_commit,
                "interpreter_sha256": _regular_file_sha256(
                    Path(self.operator_command[0]),
                    "page-builder interpreter",
                    executable=True,
                    reject_symlink=False,
                ),
                "operator_sha256": _validated_operator_source_sha256(
                    self._expected_operator
                ),
                "operator_dependency_sha256": {
                    name: _regular_file_sha256(
                        dependency,
                        f"page-builder operator dependency {name}",
                    )
                    for name, dependency in self._operator_dependency_paths.items()
                },
                "publishdesign_sha256": _regular_file_sha256(
                    self._publishdesign,
                    "page-builder publishdesign",
                    executable=True,
                ),
                "diagnostic_owner_id": self.diagnostic_owner_id,
                "backend_dir": str(backend),
                "backend_go_mod_sha256": _regular_file_sha256(
                    backend / "go.mod", "Shop Door backend go.mod"
                ),
                "backend_env_sha256": _regular_file_sha256(
                    backend / ".env", "Shop Door backend .env"
                ),
                "gcs_credentials": str(credentials),
                "gcs_credentials_sha256": _regular_file_sha256(
                    credentials, "GCS credentials"
                ),
            }
        except ValueError as exc:
            raise PublishDesignPreflightError(str(exc)) from exc
        for key, expected in current_bindings.items():
            if receipt.get(key) != expected:
                raise PublishDesignPreflightError(
                    f"publishdesign preflight receipt {key} does not match local state"
                )

    def _assert_workspace_integrity(self) -> None:
        self._assert_execution_integrity()
        self._assert_local_dependencies()
        try:
            top_level = self._git("rev-parse", "--show-toplevel").decode(
                "utf-8", errors="strict"
            ).strip()
        except UnicodeError as exc:
            raise PageBuilderError("page-builder Vibe git root is not UTF-8") from exc
        if not top_level or Path(top_level).resolve() != self.workspace:
            raise PageBuilderError("page-builder workspace is not the pinned Git root")
        if self._git("for-each-ref", "--format=%(refname)", "refs/replace/").strip():
            raise PageBuilderError("page-builder workspace has active Git replace refs")
        try:
            head = self._git("rev-parse", "--verify", "HEAD^{commit}").decode(
                "ascii", errors="strict"
            ).strip()
        except UnicodeError as exc:
            raise PageBuilderError("page-builder workspace HEAD is malformed") from exc
        if head != self.workspace_commit:
            raise PageBuilderError("page-builder workspace HEAD is not workspace_commit")
        tracked_flags = self._git("ls-files", "-v", "-z")
        if any(
            entry and not entry.startswith(b"H ")
            for entry in tracked_flags.split(b"\0")
        ):
            raise PageBuilderError(
                "page-builder workspace has hidden or nonstandard tracked-file state"
            )
        try:
            tracked_tools = {
                path.decode("utf-8", errors="strict")
                for path in self._git(
                    "ls-files", "-z", "--", "board-game/tools"
                ).split(b"\0")
                if path
            }
        except UnicodeError as exc:
            raise PageBuilderError("page-builder tracked tool path is not UTF-8") from exc
        allowed_untracked = self._publishdesign.relative_to(self.workspace).as_posix()
        for path in self._expected_operator.parent.rglob("*"):
            if path.is_dir() and not path.is_symlink():
                continue
            relative = path.relative_to(self.workspace).as_posix()
            if relative not in tracked_tools and relative != allowed_untracked:
                raise PageBuilderError(
                    f"page-builder tools contain an unreviewed untracked file: {relative}"
                )
        status = self._git(
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=no",
            "--ignore-submodules=none",
        )
        if status:
            raise PageBuilderError("page-builder workspace has tracked drift")
        self._assert_publishdesign_preflight_receipt()

    def _execution_binding(self) -> dict[str, Any]:
        return {
            "workspace_commit": self.workspace_commit,
            "interpreter_sha256": self.interpreter_sha256,
            "operator_sha256": self.operator_sha256,
            "operator_dependency_sha256": dict(
                sorted(self.operator_dependency_sha256.items())
            ),
            "publishdesign_sha256": self.publishdesign_sha256,
            "publishdesign_preflight_sha256": (
                self.publishdesign_preflight_sha256
            ),
        }

    def diagnostics(self) -> dict[str, Any]:
        """Authenticate one owner read without creating or changing a draft."""

        if not self.diagnostic_design_id:
            return {
                "adapter": "page_builder",
                "ready": False,
                "authenticated": False,
                "contract_version": PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION,
                "capabilities": [],
                "reason": "diagnostic_design_id_missing",
            }
        try:
            self._assert_workspace_integrity()
        except PublishDesignPreflightError:
            return {
                "adapter": "page_builder",
                "ready": False,
                "authenticated": False,
                "contract_version": PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION,
                "capabilities": [],
                "reason": "publishdesign_dry_run_not_proven",
            }
        except PageBuilderError:
            return {
                "adapter": "page_builder",
                "ready": False,
                "authenticated": False,
                "contract_version": PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION,
                "capabilities": [],
                "reason": "workspace_integrity_failed",
            }
        try:
            design = self.readback.get_design(self.diagnostic_design_id)
        except Exception as exc:
            return {
                "adapter": "page_builder",
                "ready": False,
                "authenticated": False,
                "contract_version": PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION,
                "capabilities": [],
                "reason": f"authenticated_read_failed:{type(exc).__name__}",
            }
        checks = (
            (
                isinstance(design, Mapping)
                and (
                    design.get("id") == self.diagnostic_design_id
                    or design.get("slug") == self.diagnostic_design_id
                ),
                "diagnostic_design_identity_mismatch",
            ),
            (
                isinstance(design, Mapping) and design.get("status") == "draft",
                "diagnostic_design_not_private_draft",
            ),
            (
                isinstance(design, Mapping)
                and has_exact_alice_product_description_suffix(
                    design.get("description")
                ),
                "diagnostic_design_description_attribution_invalid",
            ),
            (
                isinstance(design, Mapping)
                and design.get("owner_id") == self.diagnostic_owner_id,
                "diagnostic_design_owner_mismatch",
            ),
            (
                isinstance(design, Mapping)
                and isinstance(design.get("current_history_id"), str)
                and bool(str(design.get("current_history_id")).strip()),
                "diagnostic_design_history_missing",
            ),
            (
                isinstance(design, Mapping)
                and design.get("published_history_id") in (None, ""),
                "diagnostic_design_has_published_history",
            ),
        )
        failed_reason = next((reason for passed, reason in checks if not passed), "")
        if failed_reason:
            return {
                "adapter": "page_builder",
                "ready": False,
                "authenticated": False,
                "contract_version": PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION,
                "capabilities": [],
                "reason": failed_reason,
            }
        return {
            "adapter": "page_builder",
            "ready": True,
            "authenticated": True,
            "contract_version": PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION,
            "capabilities": sorted(self.capabilities),
            "diagnostic_design_id": self.diagnostic_design_id,
            "diagnostic_owner_id": self.diagnostic_owner_id,
            "workspace_commit": self.workspace_commit,
        }

    def invoke(self, operation: str, payload: dict[str, Any]) -> AdapterReceipt:
        if operation != PAGE_BUILDER_OPERATION:
            raise PageBuilderError(
                f"page-builder only accepts {PAGE_BUILDER_OPERATION!r}, got {operation!r}"
            )
        self._assert_workspace_integrity()
        input_sha256 = adapter_input_sha256(operation, payload)
        candidate_id, candidate_version = _candidate_binding(payload)
        candidate_content_sha256 = _require_sha256(
            payload.get("candidate_content_sha256"), "candidate_content_sha256"
        )
        rules = _accepted_artifact_content(payload, "candidate.rules")
        rules_sha256 = _require_sha256(
            rules.get("rules_sha256"), "candidate.rules rules_sha256"
        )
        rules_markdown = rules.get("rules_markdown")
        if not isinstance(rules_markdown, str) or not rules_markdown.strip():
            raise PageBuilderError("accepted candidate.rules lacks rules_markdown")
        cad = _dependency_content(payload, "physical.cad")
        dfm = _dependency_content(payload, "physical.dfm")
        slug = _production_slug(payload, cad)
        expected_artifacts = _artifact_hashes(cad, "physical.cad")
        dfm_artifacts = _artifact_hashes(dfm, "physical.dfm")
        if dfm_artifacts != expected_artifacts:
            raise PageBuilderError(
                "physical.dfm did not review the exact physical.cad artifact hashes"
            )

        idea_dir = self.workspace / "board-game" / "ideas" / slug
        project = idea_dir / "project"
        if not project.is_dir():
            raise PageBuilderError(
                f"production project for {slug!r} is missing at {project}"
            )
        rules_path = project / "RULES.md"
        expected_rules_bytes = rules_markdown.encode("utf-8")
        if not rules_path.is_file() or rules_path.read_bytes() != expected_rules_bytes:
            raise PageBuilderError(
                "production RULES.md is not the exact accepted rules_markdown"
            )
        rules_file_sha256 = hashlib.sha256(expected_rules_bytes).hexdigest()
        snapshot = snapshot_project(project)
        _verify_artifact_files(project, expected_artifacts)
        if expected_artifacts.get("RULES.md") != rules_file_sha256:
            raise PageBuilderError(
                "physical.cad artifact_hashes do not bind the accepted RULES.md"
            )
        for source, value in (("physical.cad", cad), ("physical.dfm", dfm)):
            expected_lineage = {
                "candidate_content_sha256": candidate_content_sha256,
                "rules_sha256": rules_sha256,
                "rules_file_sha256": rules_file_sha256,
            }
            for key, expected in expected_lineage.items():
                if value.get(key) != expected:
                    raise PageBuilderError(f"{source} {key} mismatch")
        expected_project_sha = _require_sha256(
            cad.get("project_sha256"), "physical.cad project_sha256"
        )
        if expected_project_sha != snapshot.project_sha256:
            raise PageBuilderError(
                "production workspace changed after physical.cad was accepted"
            )
        dfm_project_sha = _require_sha256(
            dfm.get("project_sha256"), "physical.dfm project_sha256"
        )
        if dfm_project_sha != snapshot.project_sha256:
            raise PageBuilderError(
                "physical.dfm did not review the current production workspace"
            )
        text2game_binding = _verify_text2game_export_handoff(
            idea_dir=idea_dir,
            project=project,
            snapshot=snapshot,
            artifact_hashes=expected_artifacts,
            cad=cad,
            dfm=dfm,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            candidate_content_sha256=candidate_content_sha256,
            production_slug=slug,
            rules_sha256=rules_sha256,
            rules_file_sha256=rules_file_sha256,
        )

        operation_key = (
            f"alice:rich-draft:{candidate_id}:v{candidate_version}:"
            f"{snapshot.project_sha256[:20]}"
        )
        published_path = idea_dir / "published.json"
        sidecar_path = idea_dir / ".alice-rich-draft.json"
        provenance_path = project / _PROVENANCE_NAME
        execution_binding = self._execution_binding()
        provenance = {
            "schema_version": SIDECAR_SCHEMA_VERSION,
            "operation_key": operation_key,
            "input_sha256": input_sha256,
            "candidate_id": candidate_id,
            "candidate_version": candidate_version,
            "candidate_content_sha256": candidate_content_sha256,
            "rules_sha256": rules_sha256,
            "rules_file_sha256": rules_file_sha256,
            "production_slug": slug,
            "project_sha256": snapshot.project_sha256,
            "artifact_hashes": dict(sorted(expected_artifacts.items())),
            "vibe_execution": execution_binding,
        }
        if text2game_binding:
            provenance["text2game_export"] = text2game_binding
        provenance_bytes = _canonical_document(provenance)
        started = time.monotonic()

        if sidecar_path.is_file():
            if not provenance_path.is_file() or provenance_path.read_bytes() != provenance_bytes:
                raise AmbiguousPageBuilderEffect(
                    "existing rich draft has no matching in-project provenance binding"
                )
            try:
                receipt = _load_object(sidecar_path, "Alice rich-draft sidecar")
                _verify_sidecar_binding(
                    receipt,
                    operation_key=operation_key,
                    input_sha256=input_sha256,
                    project_sha256=snapshot.project_sha256,
                    candidate_id=candidate_id,
                    candidate_version=candidate_version,
                    candidate_content_sha256=candidate_content_sha256,
                    rules_sha256=rules_sha256,
                    rules_file_sha256=rules_file_sha256,
                    text2game_binding=text2game_binding,
                    execution_binding=execution_binding,
                )
                normalized = self._verify_remote(
                    receipt,
                    requested_slug=slug,
                    operation_key=operation_key,
                    input_sha256=input_sha256,
                    project=snapshot,
                    artifact_hashes=expected_artifacts,
                    provenance_sha256=hashlib.sha256(provenance_bytes).hexdigest(),
                    candidate_id=candidate_id,
                    candidate_version=candidate_version,
                    candidate_content_sha256=candidate_content_sha256,
                    rules_sha256=rules_sha256,
                    rules_file_sha256=rules_file_sha256,
                    text2game_binding=text2game_binding,
                )
            except AmbiguousPageBuilderEffect:
                raise
            except Exception as exc:
                raise AmbiguousPageBuilderEffect(
                    "existing rich draft no longer matches its exact Alice binding"
                ) from exc
            return _adapter_receipt(normalized, input_sha256, started)

        if published_path.exists():
            raise AmbiguousPageBuilderEffect(
                f"{published_path} predates Alice's exact input binding; reconcile "
                "that draft and create .alice-rich-draft.json before retrying"
            )

        # This is the last safe point in the compatibility reader. Everything
        # above is local validation or authenticated read-only reconciliation;
        # no writer implementation remains behind this refusal.
        raise PageBuilderError(
            "Alice's inventor-side rich-page writer is retired: send the "
            "inspected model through Workshop and let Factory generate "
            "use-case, story blocks, images, and video on the server"
        )

    def _verify_remote(
        self,
        receipt: Mapping[str, Any],
        *,
        requested_slug: str,
        operation_key: str,
        input_sha256: str,
        project: ProjectSnapshot,
        artifact_hashes: Mapping[str, str],
        provenance_sha256: str,
        candidate_id: str,
        candidate_version: int,
        candidate_content_sha256: str,
        rules_sha256: str,
        rules_file_sha256: str,
        text2game_binding: Mapping[str, Any],
    ) -> dict[str, Any]:
        design_id = _nonempty(receipt.get("design_id") or receipt.get("id"), "design_id")
        remote_slug = _nonempty(receipt.get("slug"), "slug")
        history_id = _nonempty(receipt.get("history_id"), "history_id")
        project_url = _http_url(receipt.get("project_url"), "project_url")

        try:
            remote = self.readback.get_design(remote_slug)
        except Exception as exc:
            raise AmbiguousPageBuilderEffect(
                "draft operator completed but authenticated backend readback failed; "
                "do not retry the write"
            ) from exc
        if not isinstance(remote, Mapping):
            raise PageBuilderError("backend draft readback must be an object")

        remote_design_id = remote.get("design_id") or remote.get("id")
        if remote_design_id != design_id:
            raise PageBuilderError("backend draft design_id does not match operator receipt")
        if remote.get("slug") != remote_slug:
            raise PageBuilderError("backend draft slug does not match operator receipt")
        if remote.get("status") != "draft":
            raise PageBuilderError("rich-page handoff must remain a private draft")
        if not has_exact_alice_product_description_suffix(
            remote.get("description")
        ):
            raise PageBuilderError(
                "backend draft description lacks Alice's exact attribution"
            )
        if remote.get("owner_id") != self.diagnostic_owner_id:
            raise PageBuilderError("backend draft owner does not match configured owner")
        if remote.get("current_history_id") != history_id:
            raise PageBuilderError("backend draft head is not the imported history")
        if remote.get("published_history_id") not in (None, ""):
            raise PageBuilderError("draft unexpectedly has a published history")
        if remote.get("project_url") != project_url:
            raise PageBuilderError("backend draft project_url does not match operator receipt")

        remote_hashes = dict(artifact_hashes)
        remote_hashes[_PROVENANCE_NAME] = provenance_sha256
        for relative, expected in remote_hashes.items():
            try:
                actual = self.readback.project_file_sha256(project_url, relative)
            except Exception as exc:
                raise AmbiguousPageBuilderEffect(
                    f"draft exists but remote artifact {relative!r} could not be verified"
                ) from exc
            if actual != expected:
                raise AmbiguousPageBuilderEffect(
                    f"draft history does not contain the exact artifact {relative!r}"
                )

        use_case = remote.get("use_case")
        story_blocks = remote.get("story_blocks")
        print_specs = remote.get("print_specs")
        if not isinstance(use_case, Mapping) or not {
            "label",
            "body",
            "image",
        }.issubset(use_case):
            raise PageBuilderError("backend draft is missing the rich use_case section")
        if not isinstance(story_blocks, list) or not story_blocks:
            raise PageBuilderError("backend draft is missing rich story_blocks")
        if any(
            not isinstance(block, Mapping)
            or not isinstance(block.get("lead"), str)
            or not isinstance(block.get("body"), str)
            for block in story_blocks
        ):
            raise PageBuilderError("backend draft story_blocks are malformed")
        if not isinstance(print_specs, Mapping) or not print_specs:
            raise PageBuilderError("backend draft is missing print_specs")
        thumbnails = remote.get("thumbnail_urls")
        if not isinstance(thumbnails, list) or not thumbnails or not all(
            isinstance(url, str) and url.startswith(("https://", "http://"))
            for url in thumbnails
        ):
            raise PageBuilderError("backend draft is missing cover visuals")

        # The local slug names the production workspace; the remote slug can be
        # collision-suffixed by the Vibe backend. Preserve both instead of pretending the
        # remote canonical URL stayed identical.
        normalized = {
            "schema_version": SIDECAR_SCHEMA_VERSION,
            "operation_key": operation_key,
            "input_sha256": input_sha256,
            "candidate_id": candidate_id,
            "candidate_version": candidate_version,
            "candidate_content_sha256": candidate_content_sha256,
            "rules_sha256": rules_sha256,
            "rules_file_sha256": rules_file_sha256,
            "production_slug": requested_slug,
            "design_id": design_id,
            "slug": remote_slug,
            "history_id": history_id,
            "project_url": project_url,
            "status": "draft",
            "project_sha256": project.project_sha256,
            "artifact_manifest_sha256": project.project_sha256,
            "artifact_hashes": dict(sorted(artifact_hashes.items())),
            "vibe_execution": self._execution_binding(),
            "provenance_sha256": provenance_sha256,
            "project_files": [dict(item) for item in project.files],
            "rich_page": {
                "use_case": dict(use_case),
                "story_blocks": [dict(block) for block in story_blocks],
                "print_specs": dict(print_specs),
                "thumbnail_urls": list(thumbnails),
            },
            "receipt_source": "authenticated_backend_readback",
            "pipeline_run_id": history_id,
        }
        if text2game_binding:
            normalized["text2game_export"] = dict(text2game_binding)
        return normalized


def snapshot_project(project: str | Path) -> ProjectSnapshot:
    """Hash a stable per-file manifest for the exact production project."""

    root = Path(project).resolve()
    if not root.is_dir():
        raise PageBuilderError(f"project directory does not exist: {root}")
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise PageBuilderError(
                f"production project must not contain symlinks: {relative.as_posix()}"
            )
        if path.is_dir() or any(part in _SKIP_DIRS for part in relative.parts):
            continue
        if not path.is_file():
            raise PageBuilderError(
                "production project must contain only regular files: "
                f"{relative.as_posix()}"
            )
        if path.name in _SKIP_NAMES or path.suffix in _SKIP_SUFFIXES:
            continue
        if relative.as_posix() == _PROVENANCE_NAME:
            continue
        raw = path.read_bytes()
        files.append(
            {
                "path": relative.as_posix(),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
        )
    if not files:
        raise PageBuilderError("production project has no publishable files")
    printable_files = tuple(
        item
        for item in files
        if is_printable_cad_artifact_path(str(item["path"]))
    )
    if not printable_files:
        raise PageBuilderError(
            "production project needs at least one printable .stl, .3mf, or .obj artifact"
        )
    if any(int(item["bytes"]) <= 0 for item in printable_files):
        raise PageBuilderError("printable CAD artifacts must not be empty")
    digest = hashlib.sha256(
        json.dumps(
            files,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    return ProjectSnapshot(root=root, files=tuple(files), project_sha256=digest)


def _candidate_binding(payload: Mapping[str, Any]) -> tuple[str, int]:
    candidate_id = _nonempty(payload.get("candidate_id"), "candidate_id")
    version = payload.get("candidate_version")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise PageBuilderError("candidate_version must be a positive integer")
    return candidate_id, version


def _dependency_content(payload: Mapping[str, Any], action: str) -> Mapping[str, Any]:
    dependencies = payload.get("dependencies")
    if not isinstance(dependencies, Mapping):
        raise PageBuilderError("page-builder task has no dependency receipts")
    dependency = dependencies.get(action)
    if not isinstance(dependency, Mapping):
        raise PageBuilderError(f"page-builder task is missing {action} dependency")
    result = dependency.get("result")
    if not isinstance(result, Mapping):
        raise PageBuilderError(f"{action} dependency result is not an object")
    if result.get("executor") == "adapter":
        receipt = result.get("receipt")
        if not isinstance(receipt, Mapping) or receipt.get("status") != "passed":
            raise PageBuilderError(f"{action} dependency has no passed adapter receipt")
        content = receipt.get("payload")
    else:
        content = result.get("content")
    if not isinstance(content, Mapping):
        raise PageBuilderError(f"{action} dependency content is not an object")
    return content


def _accepted_artifact_content(
    payload: Mapping[str, Any], action: str
) -> Mapping[str, Any]:
    raw = payload.get("accepted_artifacts")
    if not isinstance(raw, list):
        raise PageBuilderError("page-builder task has no accepted artifact context")
    matches = [
        item
        for item in raw
        if isinstance(item, Mapping)
        and item.get("action") == action
        and isinstance(item.get("content"), Mapping)
    ]
    if not matches:
        raise PageBuilderError(f"page-builder task lacks accepted {action} artifact")
    latest = sorted(
        matches,
        key=lambda item: (
            int(item.get("candidate_version") or 0),
            str(item.get("task_id") or ""),
        ),
    )[-1]
    content = latest.get("content")
    assert isinstance(content, Mapping)
    return content


def _production_slug(payload: Mapping[str, Any], cad: Mapping[str, Any]) -> str:
    candidate = payload.get("candidate")
    candidates = [
        cad.get("production_slug"),
        cad.get("slug"),
        candidate.get("production_slug") if isinstance(candidate, Mapping) else None,
        candidate.get("slug") if isinstance(candidate, Mapping) else None,
    ]
    slug = next((value for value in candidates if isinstance(value, str) and value), None)
    if slug is None or _SLUG.fullmatch(slug) is None:
        raise PageBuilderError(
            "physical.cad must bind a lowercase hyphenated production slug"
        )
    return slug


def _artifact_hashes(content: Mapping[str, Any], source: str) -> dict[str, str]:
    raw = content.get("artifact_hashes")
    if not isinstance(raw, Mapping) or not raw:
        raise PageBuilderError(f"{source} must provide artifact_hashes")
    result: dict[str, str] = {}
    for path, digest in raw.items():
        if not isinstance(path, str) or not path:
            raise PageBuilderError(f"{source} artifact paths must be non-empty strings")
        normalized = PurePosixPath(path)
        if normalized.is_absolute() or ".." in normalized.parts or str(normalized) != path:
            raise PageBuilderError(f"unsafe {source} artifact path {path!r}")
        _require_sha256(digest, f"{source} artifact {path!r}")
        result[path] = digest
    validate_printable_artifact_hashes(result, source=source)
    return result


def is_printable_cad_artifact_path(path: str) -> bool:
    """Return whether a normalized project path is a directly printable mesh."""

    return (
        isinstance(path, str)
        and bool(path)
        and PurePosixPath(path).suffix.casefold() in PRINTABLE_CAD_SUFFIXES
    )


def validate_printable_artifact_hashes(
    artifact_hashes: Mapping[str, Any], *, source: str = "artifact_hashes"
) -> tuple[str, ...]:
    """Require a hash-bound printable mesh, not a rules-only project map."""

    if not isinstance(artifact_hashes, Mapping) or not artifact_hashes:
        raise PageBuilderError(f"{source} must be a non-empty artifact hash map")
    printable: list[str] = []
    for path, digest in artifact_hashes.items():
        if not isinstance(path, str) or not path:
            raise PageBuilderError(f"{source} artifact paths must be non-empty strings")
        normalized = PurePosixPath(path)
        if normalized.is_absolute() or ".." in normalized.parts or str(normalized) != path:
            raise PageBuilderError(f"unsafe {source} artifact path {path!r}")
        _require_sha256(digest, f"{source} artifact {path!r}")
        if is_printable_cad_artifact_path(path):
            printable.append(path)
    if not printable:
        raise PageBuilderError(
            f"{source} needs at least one printable .stl, .3mf, or .obj artifact"
        )
    return tuple(sorted(printable))


def _verify_artifact_files(project: Path, artifact_hashes: Mapping[str, str]) -> None:
    root = project.resolve()
    for relative, expected in artifact_hashes.items():
        path = (root / relative).resolve()
        if root not in path.parents or not path.is_file():
            raise PageBuilderError(f"accepted artifact is missing: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise PageBuilderError(f"accepted artifact changed: {relative}")


def _verify_sidecar_binding(
    receipt: Mapping[str, Any],
    *,
    operation_key: str,
    input_sha256: str,
    project_sha256: str,
    candidate_id: str,
    candidate_version: int,
    candidate_content_sha256: str,
    rules_sha256: str,
    rules_file_sha256: str,
    text2game_binding: Mapping[str, Any],
    execution_binding: Mapping[str, Any],
) -> None:
    expected = {
        "schema_version": SIDECAR_SCHEMA_VERSION,
        "operation_key": operation_key,
        "input_sha256": input_sha256,
        "project_sha256": project_sha256,
        "candidate_id": candidate_id,
        "candidate_version": candidate_version,
        "candidate_content_sha256": candidate_content_sha256,
        "rules_sha256": rules_sha256,
        "rules_file_sha256": rules_file_sha256,
        "vibe_execution": dict(execution_binding),
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise PageBuilderError(f"existing rich-draft sidecar {key} mismatch")
    if text2game_binding:
        if receipt.get("text2game_export") != dict(text2game_binding):
            raise PageBuilderError(
                "existing rich-draft sidecar text2game export mismatch"
            )
    elif "text2game_export" in receipt:
        raise PageBuilderError(
            "existing rich-draft sidecar has unexpected text2game lineage"
        )


def _load_object(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PageBuilderError(f"{label} is unreadable: {path}") from exc
    if not isinstance(value, Mapping):
        raise PageBuilderError(f"{label} must contain a JSON object")
    return value


def _canonical_document(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            dict(value),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _write_exact_file(path: Path, raw: bytes) -> None:
    if path.is_file() and path.read_bytes() == raw:
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_bytes(raw)
        temporary.replace(path)
    except OSError as exc:
        raise PageBuilderError(f"could not write exact project provenance: {path}") from exc


def _adapter_receipt(
    payload: Mapping[str, Any], input_sha256: str, started: float
) -> AdapterReceipt:
    return AdapterReceipt(
        adapter="existing_rich_page_builder",
        run_id=str(payload["history_id"]),
        status="passed",
        evidence_class="shop_door",
        payload=dict(payload),
        input_sha256=input_sha256,
        elapsed_seconds=time.monotonic() - started,
    )


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise PageBuilderError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PageBuilderError(f"draft receipt needs {label}")
    return value


def _http_url(value: Any, label: str) -> str:
    result = _nonempty(value, label)
    if not result.startswith(("https://", "http://")):
        raise PageBuilderError(f"draft receipt {label} must be HTTP(S)")
    return result


# Compatibility import for extensions built before Workshop 0.3.
PageBuilderAdapter = ShopDoorAdapter


__all__ = [
    "AmbiguousPageBuilderEffect",
    "DraftReadback",
    "PAGE_BUILDER_OPERATION",
    "PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION",
    "PUBLISHDESIGN_PREFLIGHT_SCHEMA_VERSION",
    "PRINTABLE_CAD_SUFFIXES",
    "PageBuilderAdapter",
    "PageBuilderError",
    "PageBuilderReadback",
    "ProjectSnapshot",
    "PublishDesignPreflightError",
    "ShopDoorAdapter",
    "build_publishdesign_preflight_receipt",
    "is_printable_cad_artifact_path",
    "snapshot_project",
    "validate_printable_artifact_hashes",
]
