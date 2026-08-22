"""Narrow handoff to the existing Vibe Ideas rich-page draft operator.

The operator owned by ``reinSPQR/vibe-ideas`` is
``board-game/tools/publish.py <slug>``.  It packages an already-built game,
imports it through Panda Social's production backend, and authors the private
draft's use-case, story blocks, print specs, rules file, and cover images.  This
module deliberately does none of those jobs.  It only:

* binds the invocation to one candidate version and one exact local project;
* invokes that operator without any force, public, or regeneration flags;
* requires a strict receipt and an authenticated draft readback; and
* returns the design/history identity that later print tests and public publish
  must keep using.

``published.json`` makes normal re-entry a no-op in the upstream operator.  An
Alice sidecar adds the input/project binding the upstream receipt does not yet
carry.  A pre-existing upstream receipt without that sidecar is treated as an
ambiguous earlier effect, never silently adopted as the current candidate.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Protocol, Sequence

from .adapters import AdapterError, AdapterReceipt, adapter_input_sha256
from .providers import (
    BoundedProcessOutputLimit,
    BoundedProcessTimeout,
    run_bounded_process,
)
from .store import DurableStore, StateConflictError


PAGE_BUILDER_OPERATION = "physical.create_rich_draft"
PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION = "alice.page-builder.v1"
SIDECAR_SCHEMA_VERSION = 1
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SKIP_DIRS = frozenset({"__pycache__", ".git", ".claude", ".idea", ".vscode"})
_SKIP_NAMES = frozenset({".DS_Store"})
_SKIP_SUFFIXES = frozenset({".pyc", ".pyo"})
_PROVENANCE_NAME = "alice-provenance.json"
PRINTABLE_CAD_SUFFIXES = frozenset({".3mf", ".obj", ".stl"})


class PageBuilderError(AdapterError):
    """The existing draft operator or its receipt failed a deterministic check."""


class AmbiguousPageBuilderEffect(RuntimeError):
    """A draft write may have happened, so automatic retry is unsafe."""


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


class PageBuilderAdapter:
    """Run the existing private-draft page builder against one exact workspace.

    ``operator_command`` must be exactly one absolute interpreter plus the
    existing entry point, for example
    ``[/venv/bin/python, "/srv/vibe-ideas/board-game/tools/publish.py"]``. The
    adapter appends the validated slug. It never accepts wrappers or appends ``--force``,
    ``--page``, ``--new-version``, or any public-status option.
    """

    capabilities = (
        "private_rich_page_draft",
        "exact_history_handoff",
        "project_hash_bound_draft",
    )

    def __init__(
        self,
        workspace: str | Path,
        operator_command: Sequence[str],
        readback: DraftReadback,
        store: DurableStore,
        *,
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
            "PANDA_OWNER_ID",
            "PANDA_BACKEND_DIR",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "PANDA_APP_URL",
        ),
    ) -> None:
        configured_workspace = Path(workspace).expanduser()
        self.workspace = configured_workspace.resolve()
        if not self.workspace.is_dir():
            raise ValueError(f"page-builder workspace does not exist: {self.workspace}")
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
        resolved_interpreter = interpreter.resolve()
        if not resolved_interpreter.is_file() or not os.access(
            resolved_interpreter, os.X_OK
        ):
            raise ValueError(
                f"page-builder interpreter is missing or not executable: {interpreter}"
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
        self.diagnostic_design_id = str(diagnostic_design_id).strip()
        self.environment = {
            name: os.environ[name]
            for name in allowed_environment
            if name in os.environ
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
        identity = (
            design.get("id") == self.diagnostic_design_id
            or design.get("slug") == self.diagnostic_design_id
        ) if isinstance(design, Mapping) else False
        if not identity:
            return {
                "adapter": "page_builder",
                "ready": False,
                "authenticated": True,
                "contract_version": PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION,
                "capabilities": [],
                "reason": "diagnostic_design_identity_mismatch",
            }
        return {
            "adapter": "page_builder",
            "ready": True,
            "authenticated": True,
            "contract_version": PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION,
            "capabilities": sorted(self.capabilities),
            "diagnostic_design_id": self.diagnostic_design_id,
        }

    def invoke(self, operation: str, payload: dict[str, Any]) -> AdapterReceipt:
        if operation != PAGE_BUILDER_OPERATION:
            raise PageBuilderError(
                f"page-builder only accepts {PAGE_BUILDER_OPERATION!r}, got {operation!r}"
            )
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

        operation_key = (
            f"alice:rich-draft:{candidate_id}:v{candidate_version}:"
            f"{snapshot.project_sha256[:20]}"
        )
        published_path = idea_dir / "published.json"
        sidecar_path = idea_dir / ".alice-rich-draft.json"
        provenance_path = project / _PROVENANCE_NAME
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
        }
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

        if Path(self.operator_command[0]).resolve() != self._resolved_interpreter:
            raise PageBuilderError("page-builder interpreter target changed after startup")
        configured_operator = Path(self.operator_command[1])
        if (
            configured_operator.is_symlink()
            or configured_operator.resolve() != self._expected_operator
        ):
            raise PageBuilderError("page-builder publish.py target changed after startup")
        _write_exact_file(provenance_path, provenance_bytes)

        effect_claim_key = f"alice.effect:rich-draft:{operation_key}"
        try:
            self.store.put_state(
                effect_claim_key,
                {
                    "operation": PAGE_BUILDER_OPERATION,
                    "operation_key": operation_key,
                    "input_sha256": input_sha256,
                    "candidate_id": candidate_id,
                    "candidate_version": candidate_version,
                    "project_sha256": snapshot.project_sha256,
                    "status": "sending",
                },
                None,
            )
        except StateConflictError as exc:
            raise AmbiguousPageBuilderEffect(
                "the rich-draft write was already claimed; reconcile its remote "
                "outcome instead of launching the operator again"
            ) from exc

        env = dict(self.environment)
        env["ALICE_OPERATION_KEY"] = operation_key
        env["ALICE_INPUT_SHA256"] = input_sha256
        env["ALICE_PROJECT_SHA256"] = snapshot.project_sha256
        command = [*self.operator_command, slug]
        try:
            run = run_bounded_process(
                command,
                input_bytes=b"",
                cwd=self.workspace,
                env=env,
                timeout_seconds=self.timeout_seconds,
                stdout_limit_bytes=self.maximum_stdout_bytes,
                stderr_limit_bytes=self.maximum_stderr_bytes,
                shutdown_grace_seconds=self.shutdown_grace_seconds,
            )
        except BoundedProcessTimeout as exc:
            raise AmbiguousPageBuilderEffect(
                f"rich-page draft operator timed out after {self.timeout_seconds}s; "
                "the remote write may have completed and must be reconciled"
            ) from exc
        except BoundedProcessOutputLimit as exc:
            raise AmbiguousPageBuilderEffect(
                f"rich-page draft operator {exc.stream} exceeded its byte limit; "
                "the remote write may have completed and must be reconciled"
            ) from exc
        except OSError as exc:
            # The durable claim is intentionally irreversible.  We cannot
            # prove another process did not start the same command, so even a
            # local spawn error is reconciled rather than retried.
            raise AmbiguousPageBuilderEffect(
                f"rich-page draft operator could not be observed after its "
                f"single-writer claim ({type(exc).__name__})"
            ) from exc

        if run.returncode != 0:
            raise AmbiguousPageBuilderEffect(
                f"rich-page draft operator exited {run.returncode} after launch; "
                "the backend import may have committed and must be reconciled; "
                f"stderr_sha256={run.stderr_sha256}; stderr_bytes={run.stderr_bytes}"
            )

        try:
            stdout = run.stdout.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AmbiguousPageBuilderEffect(
                "draft operator completed but stdout was not UTF-8; reconcile the remote write"
            ) from exc

        try:
            local_receipt: Mapping[str, Any]
            if published_path.is_file():
                local_receipt = _load_object(published_path, "upstream published.json")
            else:
                local_receipt = _strict_stdout_receipt(stdout)

            normalized = self._verify_remote(
                local_receipt,
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
            )
        except AmbiguousPageBuilderEffect:
            raise
        except Exception as exc:
            raise AmbiguousPageBuilderEffect(
                "draft operator finished but its exact receipt/readback could not be verified; "
                "do not invoke it again"
            ) from exc
        normalized["operator_stdout_sha256"] = hashlib.sha256(
            run.stdout
        ).hexdigest()
        _write_sidecar(sidecar_path, normalized)
        return _adapter_receipt(normalized, input_sha256, started)

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
        # collision-suffixed by Panda.  Preserve both instead of pretending the
        # remote canonical URL stayed identical.
        return {
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


def _strict_stdout_receipt(stdout: str) -> Mapping[str, Any]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise PageBuilderError("draft operator produced no receipt")
    try:
        value = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise PageBuilderError(
            "draft operator created no published.json and returned no strict JSON receipt"
        ) from exc
    if not isinstance(value, Mapping):
        raise PageBuilderError("draft operator receipt must be a JSON object")
    return value


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
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise PageBuilderError(f"existing rich-draft sidecar {key} mismatch")


def _load_object(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PageBuilderError(f"{label} is unreadable: {path}") from exc
    if not isinstance(value, Mapping):
        raise PageBuilderError(f"{label} must contain a JSON object")
    return value


def _write_sidecar(path: Path, receipt: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    encoded = json.dumps(
        dict(receipt),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    try:
        temporary.write_text(encoded, encoding="utf-8")
        temporary.replace(path)
    except OSError as exc:
        raise AmbiguousPageBuilderEffect(
            "draft exists but Alice could not persist its exact binding sidecar"
        ) from exc


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
        evidence_class="publishing_pipeline",
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


__all__ = [
    "AmbiguousPageBuilderEffect",
    "DraftReadback",
    "PAGE_BUILDER_OPERATION",
    "PAGE_BUILDER_DIAGNOSTICS_CONTRACT_VERSION",
    "PRINTABLE_CAD_SUFFIXES",
    "PageBuilderAdapter",
    "PageBuilderError",
    "PageBuilderReadback",
    "ProjectSnapshot",
    "is_printable_cad_artifact_path",
    "snapshot_project",
    "validate_printable_artifact_hashes",
]
