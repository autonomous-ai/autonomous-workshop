"""Durable handoff to the existing Vibe product-page publishing pipeline.

This module deliberately stops at the supported Vibe HTTP contract. Alice's
release path supplies the already manufactured Vibe design/history and explicit
price; the deployed page observer may add merchandising media/copy. An older
text-only create/resume path remains available for non-release workflows. Alice
publishes once, then observes the anonymous design representation until the
existing page verifier says the customer-facing page is complete.

Every mutating request is fenced by a durable publication intent.  A lost or
malformed response is therefore *ambiguous* and is never automatically retried.
Only authenticated reads and the anonymous page-observer read are polled.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping, Protocol

from .adapters import AdapterError, AdapterReceipt, adapter_input_sha256
from .page import (
    PageVerification,
    has_exact_alice_product_description_suffix,
    verify_factory_product_page,
)
from .store import DurableStore, PublicationRecord, StateConflictError


PUBLICATION_TARGET = "vibe_pipeline"
# This is the capability name already used by Alice's future hash-bound
# Factory contract.  For this adapter it means more than accepting extra JSON:
# the endpoint must atomically compare expected_history_id and echo the bound
# history, packet, and policy hashes in its success receipt.
REVISION_BOUND_PUBLISH_CAPABILITY = "packet_hash_bound_publish"
LISTING_BOUND_PUBLISH_CAPABILITY = "sku_currency_bound_publish"
RICH_PAGE_BOUND_PUBLISH_CAPABILITY = "rich_page_bound_publish"
REQUIRED_PUBLIC_WRITE_CAPABILITIES = frozenset(
    {
        REVISION_BOUND_PUBLISH_CAPABILITY,
        LISTING_BOUND_PUBLISH_CAPABILITY,
        RICH_PAGE_BOUND_PUBLISH_CAPABILITY,
    }
)
ALICE_REVISION_BOUND_RELEASE_CAPABILITIES = (
    "durable_publication_intent",
    "explicit_price",
    "ambiguous_no_retry",
    "page_pipeline_readback",
    "expected_history_cas",
    "exact_sku_currency_binding",
    "atomic_rich_page_precondition",
)
PAUSED_JOB_STATUSES = frozenset(
    {
        "awaiting_questions",
        "awaiting_plan_approval",
        "awaiting_concept_input",
        "awaiting_concept_selection",
        "stopped",
    }
)
TERMINAL_FAILURE_JOB_STATUSES = frozenset({"failed", "canceled"})


class VibePipelineError(RuntimeError):
    """Base error for the Vibe handoff."""


class VibeHTTPError(VibePipelineError):
    """A definite HTTP response rejected a request."""

    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail
        super().__init__(f"Vibe HTTP {status}: {detail}")


class VibeReadError(VibePipelineError):
    """A read failed transiently and is safe to repeat."""


class AmbiguousVibeEffect(VibePipelineError):
    """A write may have committed; it must not be sent again."""

    def __init__(
        self,
        message: str,
        *,
        operation_key: str | None = None,
        publication_id: str | None = None,
    ) -> None:
        self.operation_key = operation_key
        self.publication_id = publication_id
        super().__init__(message)


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Do not forward Vibe bearer credentials across HTTP redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


class VibeActionRequired(VibePipelineError):
    """The Vibe creation job is parked for a human/agent answer."""

    def __init__(
        self, receipt: "VibePipelineReceipt", job: Mapping[str, Any]
    ) -> None:
        self.receipt = receipt
        self.job = dict(job)
        super().__init__(f"Vibe job is awaiting input: {job.get('status')!r}")


class VibePollingTimeout(VibePipelineError):
    """A safe read poll exhausted its local wait budget."""

    def __init__(self, message: str, receipt: "VibePipelineReceipt") -> None:
        self.receipt = receipt
        super().__init__(message)


class VibePageIncomplete(VibePollingTimeout):
    """The public record exists, but PageVerifier is not complete yet."""

    def __init__(
        self,
        receipt: "VibePipelineReceipt",
        verification: PageVerification | None,
    ) -> None:
        self.verification = verification
        failures = () if verification is None else verification.failures
        super().__init__(
            "public Factory page did not become complete before the poll limit: "
            + ", ".join(failures),
            receipt,
        )


@dataclass(frozen=True, slots=True)
class VibePipelineRequest:
    """The minimal Alice -> Vibe handoff.

    ``operation_key`` is supplied by the caller, not derived from mutable
    process state.  It is stored with the immutable request and copied into
    every receipt.  The category is a Vibe category slug and price is integer
    USD cents, matching the live publish endpoint.
    """

    operation_key: str
    candidate_id: str
    packet_hash: str
    prompt: str
    category: str
    price_cents: int
    title: str | None = None
    tags: tuple[str, ...] = ()
    llm_source: str | None = None
    model: str | None = None
    effort_level: str | None = None
    ref_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("operation_key", "candidate_id", "prompt", "category"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if any(ord(ch) < 33 or ord(ch) > 126 for ch in self.operation_key):
            raise ValueError("operation_key must contain printable non-space ASCII")
        if (
            not isinstance(self.packet_hash, str)
            or len(self.packet_hash) != 64
            or self.packet_hash.lower() != self.packet_hash
            or any(ch not in "0123456789abcdef" for ch in self.packet_hash)
        ):
            raise ValueError("packet_hash must be a lowercase SHA-256 hex digest")
        if not isinstance(self.price_cents, int) or isinstance(self.price_cents, bool):
            raise ValueError("price_cents must be an integer")
        if not 100 <= self.price_cents <= 1_000_000:
            raise ValueError("price_cents must be between 100 and 1000000")
        if self.title is not None and not self.title.strip():
            raise ValueError("title must be non-empty when provided")
        if not isinstance(self.tags, tuple) or not all(
            isinstance(tag, str) and tag.strip() for tag in self.tags
        ):
            raise ValueError("tags must be a tuple of non-empty strings")
        if self.llm_source not in (None, "platform", "byos"):
            raise ValueError("llm_source must be 'platform' or 'byos'")
        if self.effort_level not in (None, "low", "medium", "high", "xhigh", "max"):
            raise ValueError("unsupported effort_level")

    def generation_payload(self) -> dict[str, Any]:
        # These are the normal POST /api/v1/generate fields.  concept_phase is
        # intentionally true because that is the supported web Vibe workflow;
        # auto_build skips only the separate plan-approval pause.
        payload: dict[str, Any] = {
            "prompt": self.prompt,
            "category": self.category,
            "tags": list(self.tags),
            "auto_build": True,
            "concept_phase": True,
        }
        for key, value in (
            ("title", self.title),
            ("llm_source", self.llm_source),
            ("model", self.model),
            ("effort_level", self.effort_level),
            ("ref_id", self.ref_id),
        ):
            if value is not None:
                payload[key] = value
        return payload

    def durable_request(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "operation_key": self.operation_key,
            "candidate_id": self.candidate_id,
            # The immutable production PublicationPacket hash is supplied by
            # release policy.  It is distinct from the hash of this HTTP intent.
            "packet_hash": self.packet_hash,
            "generation": self.generation_payload(),
            "publication": {
                "price_cents": self.price_cents,
                "currency": "USD",
                "require_rich_page_complete": True,
            },
        }


@dataclass(frozen=True, slots=True)
class ExistingVibeDesignRequest:
    """Publish an already built, reviewed, and physically tested Vibe design."""

    operation_key: str
    candidate_id: str
    candidate_version: int
    candidate_content_sha256: str
    packet_hash: str
    production_packet_hash: str
    reviewed_packet_hash: str
    policy_hash: str
    production_candidate_version: int
    production_manifest: Mapping[str, Any]
    design_id: str
    slug: str
    history_id: str
    project_url: str
    project_sha256: str
    price_cents: int
    release_decision: Mapping[str, Any]
    artifact_hashes: Mapping[str, str]

    def __post_init__(self) -> None:
        for name in (
            "operation_key",
            "candidate_id",
            "design_id",
            "slug",
            "history_id",
            "project_url",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if any(ord(ch) < 33 or ord(ch) > 126 for ch in self.operation_key):
            raise ValueError("operation_key must contain printable non-space ASCII")
        if not isinstance(self.candidate_version, int) or isinstance(
            self.candidate_version, bool
        ) or self.candidate_version < 1:
            raise ValueError("candidate_version must be a positive integer")
        self._require_sha256(
            self.candidate_content_sha256, "candidate_content_sha256"
        )
        self._require_sha256(self.packet_hash, "packet_hash")
        self._require_sha256(
            self.production_packet_hash, "production_packet_hash"
        )
        self._require_sha256(self.reviewed_packet_hash, "reviewed_packet_hash")
        self._require_sha256(self.policy_hash, "policy_hash")
        self._require_sha256(self.project_sha256, "project_sha256")
        if not (
            self.packet_hash
            == self.production_packet_hash
            == self.reviewed_packet_hash
        ):
            raise ValueError(
                "packet_hash, production_packet_hash, and reviewed_packet_hash must match"
            )
        if not isinstance(self.production_candidate_version, int) or isinstance(
            self.production_candidate_version, bool
        ) or self.production_candidate_version < 1:
            raise ValueError("production_candidate_version must be a positive integer")
        if self.production_candidate_version > self.candidate_version - 1:
            raise ValueError(
                "production_candidate_version cannot be newer than the release candidate"
            )
        if not isinstance(self.production_manifest, Mapping):
            raise ValueError("production_manifest must be an object")
        if DurableStore.sha256_json(self.production_manifest) != self.packet_hash:
            raise ValueError("production_manifest does not match packet_hash")
        if not isinstance(self.price_cents, int) or isinstance(self.price_cents, bool):
            raise ValueError("price_cents must be an integer")
        if not 100 <= self.price_cents <= 1_000_000:
            raise ValueError("price_cents must be between 100 and 1000000")
        if not self.project_url.startswith(("https://", "http://")):
            raise ValueError("project_url must be HTTP(S)")
        if not isinstance(self.release_decision, Mapping):
            raise ValueError("release_decision must be an object")
        if self.release_decision.get("allowed") is not True:
            raise ValueError("release_decision must contain allowed=true")
        for key, expected in (
            ("effect_mode", "live"),
            ("candidate_id", self.candidate_id),
            ("release_candidate_version", self.candidate_version - 1),
            ("publish_candidate_version", self.candidate_version),
            ("production_candidate_version", self.production_candidate_version),
            ("production_packet_hash", self.production_packet_hash),
            ("reviewed_packet_hash", self.reviewed_packet_hash),
            ("policy_hash", self.policy_hash),
        ):
            if self.release_decision.get(key) != expected:
                raise ValueError(f"release_decision {key} mismatch")
        if not isinstance(self.artifact_hashes, Mapping) or not all(
            isinstance(key, str)
            and key
            and isinstance(value, str)
            and value
            for key, value in self.artifact_hashes.items()
        ):
            raise ValueError("artifact_hashes must map names to hashes")
        for key, value in self.artifact_hashes.items():
            self._require_sha256(value, f"artifact_hashes[{key!r}]")
        if self.production_manifest.get("candidate_id") != self.candidate_id:
            raise ValueError("production_manifest candidate_id mismatch")
        if (
            self.production_manifest.get("candidate_version")
            != self.production_candidate_version
        ):
            raise ValueError("production_manifest candidate_version mismatch")
        if (
            self.production_manifest.get("candidate_content_sha256")
            != self.candidate_content_sha256
        ):
            raise ValueError("production_manifest candidate content mismatch")
        manufacturing = self.production_manifest.get("manufacturing")
        design = (
            manufacturing.get("vibe_design")
            if isinstance(manufacturing, Mapping)
            else None
        )
        if not isinstance(design, Mapping):
            raise ValueError("production_manifest lacks manufacturing.vibe_design")
        for key, expected in (
            ("design_id", self.design_id),
            ("slug", self.slug),
            ("history_id", self.history_id),
            ("project_url", self.project_url),
            ("project_sha256", self.project_sha256),
        ):
            if design.get(key) != expected:
                raise ValueError(f"production_manifest vibe_design {key} mismatch")
        if dict(design.get("artifact_hashes") or {}) != dict(self.artifact_hashes):
            raise ValueError(
                "production_manifest vibe_design artifact_hashes mismatch"
            )
        price = self.production_manifest.get("price")
        if not isinstance(price, Mapping) or price.get("price_cents") != self.price_cents:
            raise ValueError("production_manifest price mismatch")
        if price.get("currency") != "USD":
            raise ValueError("production_manifest price currency must be USD")
        listing = self.production_manifest.get("listing")
        sku = listing.get("sku") if isinstance(listing, Mapping) else None
        if (
            not isinstance(sku, str)
            or not sku
            or len(sku) > 128
            or any(ord(ch) < 33 or ord(ch) > 126 for ch in sku)
        ):
            raise ValueError("production_manifest listing.sku is invalid")

    @staticmethod
    def _require_sha256(value: Any, name: str) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or value.lower() != value
            or any(ch not in "0123456789abcdef" for ch in value)
        ):
            raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")

    def durable_request(self) -> dict[str, Any]:
        manufacturing = self.production_manifest.get("manufacturing")
        bound_design = (
            manufacturing.get("vibe_design")
            if isinstance(manufacturing, Mapping)
            else None
        )
        if not isinstance(bound_design, Mapping):
            raise ValueError("production_manifest lacks manufacturing.vibe_design")
        return {
            "schema_version": 1,
            "operation_key": self.operation_key,
            "candidate_id": self.candidate_id,
            "candidate_version": self.candidate_version,
            "candidate_content_sha256": self.candidate_content_sha256,
            "packet_hash": self.packet_hash,
            "production_packet_hash": self.production_packet_hash,
            "reviewed_packet_hash": self.reviewed_packet_hash,
            "policy_hash": self.policy_hash,
            "production_candidate_version": self.production_candidate_version,
            "production_manifest": dict(self.production_manifest),
            "release_decision": dict(self.release_decision),
            "existing_design": dict(bound_design),
            "publication": {
                "price_cents": self.price_cents,
                "currency": "USD",
            },
        }


@dataclass(frozen=True, slots=True)
class VibePipelineReceipt:
    operation_key: str
    publication_id: str
    candidate_id: str
    packet_hash: str
    pipeline_run_id: str | None
    design_id: str | None
    slug: str | None
    history_id: str | None
    status: str
    price_cents: int
    sku: str
    currency: str
    page_url: str | None
    verification: PageVerification | None = None

    def evidence_receipt(self) -> dict[str, Any]:
        """Return the receipt shape required by Alice lifecycle transitions."""

        if self.status != "complete" or self.verification is None:
            raise VibePipelineError("only a complete page has transition evidence")
        if not self.pipeline_run_id or not self.page_url:
            raise VibePipelineError("complete receipt lacks run id or page URL")
        return {
            "operation_key": self.operation_key,
            "publication_id": self.publication_id,
            "candidate_id": self.candidate_id,
            "packet_hash": self.packet_hash,
            "pipeline_run_id": self.pipeline_run_id,
            "design_id": self.design_id,
            "history_id": self.history_id,
            "page_url": self.page_url,
            "price_cents": self.price_cents,
            "sku": self.sku,
            "currency": self.currency,
        }


class VibeTransport(Protocol):
    """Narrow boundary around only the supported Vibe endpoints."""

    def create_design(
        self, payload: Mapping[str, Any], *, operation_key: str
    ) -> Mapping[str, Any]: ...

    def get_job(self, job_id: str) -> Mapping[str, Any]: ...

    def capabilities(self) -> frozenset[str]: ...

    def get_design(self, slug_or_id: str) -> Mapping[str, Any]: ...

    def send_job_message(
        self,
        job_id: str,
        payload: Mapping[str, Any],
        *,
        operation_key: str,
    ) -> Mapping[str, Any]: ...

    def publish_design(
        self,
        slug_or_id: str,
        payload: Mapping[str, Any],
        *,
        operation_key: str,
    ) -> Mapping[str, Any]: ...

    def get_public_design(self, slug_or_id: str) -> Mapping[str, Any]: ...


class VibeHttpClient:
    """Dependency-free HTTP transport for the live ``/api/v1`` routes."""

    def __init__(self, base_url: str, token: str, *, timeout_seconds: int = 180) -> None:
        parsed = urllib.parse.urlsplit(base_url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "Vibe base_url must be a credential-free HTTPS origin/path"
            )
        if not token:
            raise ValueError("Vibe bearer token is required")
        base = base_url.rstrip("/")
        self.api_base_url = base if base.endswith("/api/v1") else f"{base}/api/v1"
        self._token = token
        self.timeout_seconds = timeout_seconds
        self._opener = urllib.request.build_opener(_RejectRedirects())

    def __repr__(self) -> str:
        return (
            f"VibeHttpClient(api_base_url={self.api_base_url!r}, "
            f"timeout_seconds={self.timeout_seconds!r}, token=<redacted>)"
        )

    @classmethod
    def from_environment(
        cls,
        base_url: str,
        token_env: str = "ALICE_FACTORY_TOKEN",
        *,
        timeout_seconds: int = 180,
    ) -> "VibeHttpClient":
        token = os.environ.get(token_env)
        if not token:
            raise VibePipelineError(
                f"Vibe token environment variable {token_env!r} is missing"
            )
        return cls(base_url, token, timeout_seconds=timeout_seconds)

    def create_design(
        self, payload: Mapping[str, Any], *, operation_key: str
    ) -> Mapping[str, Any]:
        return self._write("POST", "/generate", payload, operation_key)

    def get_job(self, job_id: str) -> Mapping[str, Any]:
        return self._read(
            f"/jobs/{urllib.parse.quote(job_id, safe='')}", authenticated=True
        )

    def capabilities(self) -> frozenset[str]:
        raw = self._read("/capabilities", authenticated=True)
        values = raw.get("capabilities")
        if not isinstance(values, list) or not all(
            isinstance(value, str) for value in values
        ):
            raise VibeReadError("Vibe capabilities response is invalid")
        return frozenset(values)

    def get_design(self, slug_or_id: str) -> Mapping[str, Any]:
        return self._read(
            f"/designs/{urllib.parse.quote(slug_or_id, safe='')}",
            authenticated=True,
        )

    def send_job_message(
        self,
        job_id: str,
        payload: Mapping[str, Any],
        *,
        operation_key: str,
    ) -> Mapping[str, Any]:
        return self._write(
            "POST",
            f"/jobs/{urllib.parse.quote(job_id, safe='')}/message",
            payload,
            operation_key,
        )

    def publish_design(
        self,
        slug_or_id: str,
        payload: Mapping[str, Any],
        *,
        operation_key: str,
    ) -> Mapping[str, Any]:
        return self._write(
            "POST",
            f"/designs/{urllib.parse.quote(slug_or_id, safe='')}/publish",
            payload,
            operation_key,
        )

    def get_public_design(self, slug_or_id: str) -> Mapping[str, Any]:
        # Deliberately anonymous: authenticated owners see their mutable current
        # history, while the public page is pinned to published_history_id.
        return self._read(
            f"/designs/{urllib.parse.quote(slug_or_id, safe='')}",
            authenticated=False,
        )

    def _write(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any],
        operation_key: str,
    ) -> Mapping[str, Any]:
        body = json.dumps(
            dict(payload), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        try:
            return self._request(
                method,
                path,
                body=body,
                authenticated=True,
                headers={
                    "Content-Type": "application/json",
                    "Idempotency-Key": operation_key,
                    "X-Alice-Operation-Key": operation_key,
                },
            )
        except VibeHTTPError as exc:
            # A server error may be emitted after a commit; a 4xx is a definite
            # rejection.  Neither class is retried here.
            if exc.status >= 500:
                raise AmbiguousVibeEffect(
                    "Vibe write returned a server error; reconcile before retry"
                ) from exc
            raise
        except (VibeReadError, ValueError) as exc:
            raise AmbiguousVibeEffect(
                "Vibe write lost a valid receipt; reconcile before retry"
            ) from exc

    def _read(self, path: str, *, authenticated: bool) -> Mapping[str, Any]:
        return self._request("GET", path, authenticated=authenticated)

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        authenticated: bool,
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        request_headers = {
            "Accept": "application/json",
            "User-Agent": "alice-inventor/0.1",
            **dict(headers or {}),
        }
        if authenticated:
            request_headers["Authorization"] = f"Bearer {self._token}"
        request = urllib.request.Request(
            f"{self.api_base_url}{path}",
            data=body,
            method=method,
            headers=request_headers,
        )
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                response_body = response.read()
        except urllib.error.HTTPError as exc:
            detail_sha256 = hashlib.sha256(exc.read()).hexdigest()
            raise VibeHTTPError(
                exc.code, f"response_body_sha256={detail_sha256}"
            ) from exc
        except (TimeoutError, urllib.error.URLError, OSError) as exc:
            raise VibeReadError("Vibe request timed out or disconnected") from exc
        try:
            raw = json.loads(response_body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise VibeReadError("Vibe returned invalid JSON") from exc
        if not isinstance(raw, Mapping):
            raise VibeReadError("Vibe response must be a JSON object")
        return dict(raw)


PauseHandler = Callable[[Mapping[str, Any]], Mapping[str, Any] | None]
PageVerifier = Callable[..., PageVerification]


class VibePipeline:
    """Run or resume the durable Vibe -> publish -> public-page handoff."""

    def __init__(
        self,
        store: DurableStore,
        transport: VibeTransport,
        *,
        page_verifier: PageVerifier = verify_factory_product_page,
        poll_interval_seconds: float = 5.0,
        max_job_polls: int = 4_320,
        max_page_polls: int = 360,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if poll_interval_seconds < 0:
            raise ValueError("poll_interval_seconds must be non-negative")
        if max_job_polls < 1 or max_page_polls < 1:
            raise ValueError("poll limits must be positive")
        self.store = store
        self.transport = transport
        self.page_verifier = page_verifier
        self.poll_interval_seconds = poll_interval_seconds
        self.max_job_polls = max_job_polls
        self.max_page_polls = max_page_polls
        self.sleep = sleep

    def run(
        self,
        request: VibePipelineRequest,
        *,
        pause_handler: PauseHandler | None = None,
    ) -> VibePipelineReceipt:
        intent = request.durable_request()
        request_sha256 = self.store.sha256_json(intent)
        record = self.store.prepare_publication(
            PUBLICATION_TARGET,
            request.operation_key,
            request_sha256,
            intent,
            candidate_id=request.candidate_id,
        )
        return self._continue(record, intent, pause_handler=pause_handler)

    def publish_existing(
        self, request: ExistingVibeDesignRequest
    ) -> VibePipelineReceipt:
        """Publish the exact Vibe design already bound to production evidence."""

        candidate = self.store.get_candidate(request.candidate_id)
        if candidate.version != request.candidate_version:
            raise VibePipelineError(
                "existing-design request is stale for the current candidate version"
            )
        if candidate.state != "publish_ready":
            raise VibePipelineError(
                f"candidate must be publish_ready, got {candidate.state!r}"
            )
        if self.store.sha256_json(candidate.content) != request.candidate_content_sha256:
            raise VibePipelineError("existing-design request candidate content is stale")
        release = candidate.metadata.get("release_decision")
        if not isinstance(release, Mapping):
            raise VibePipelineError("candidate has no pinned release decision")
        for key, expected in (
            ("allowed", True),
            ("effect_mode", "live"),
            ("candidate_id", request.candidate_id),
            ("candidate_version", request.candidate_version - 1),
            ("release_candidate_version", request.candidate_version - 1),
            ("production_candidate_version", request.production_candidate_version),
            ("production_packet_hash", request.production_packet_hash),
            ("reviewed_packet_hash", request.reviewed_packet_hash),
            ("policy_hash", request.policy_hash),
            ("production_manifest", request.production_manifest),
        ):
            if release.get(key) != expected:
                raise VibePipelineError(
                    f"existing-design request does not match release decision {key}"
                )
        intent = request.durable_request()
        request_sha256 = self.store.sha256_json(intent)
        record = self.store.prepare_publication(
            PUBLICATION_TARGET,
            request.operation_key,
            request_sha256,
            intent,
            candidate_id=request.candidate_id,
            slug=request.slug,
        )
        return self._continue(record, intent, pause_handler=None)

    def reconcile(
        self,
        operation_key: str,
        *,
        pause_handler: PauseHandler | None = None,
    ) -> VibePipelineReceipt:
        """Resume safe reads after a crash, never blindly repeating a write."""

        record = self.store.get_publication_intent(PUBLICATION_TARGET, operation_key)
        if record is None:
            raise VibePipelineError(f"no Vibe operation {operation_key!r} exists")
        if not isinstance(record.request, Mapping):
            raise VibePipelineError("stored Vibe request is invalid")
        return self._continue(record, record.request, pause_handler=pause_handler)

    def _continue(
        self,
        record: PublicationRecord,
        intent: Mapping[str, Any],
        *,
        pause_handler: PauseHandler | None,
    ) -> VibePipelineReceipt:
        if record.state == "confirmed":
            self._finish_candidate_publication_effect(record, "confirmed")
            return self._receipt(record)
        if record.state == "ambiguous":
            self._finish_candidate_publication_effect(record, "ambiguous")
            raise AmbiguousVibeEffect(
                record.last_error or "Vibe operation is ambiguous and cannot be retried",
                operation_key=record.idempotency_key,
                publication_id=record.id,
            )
        if record.state == "failed":
            raise VibePipelineError(record.last_error or "Vibe operation failed")

        generation = intent.get("generation")
        existing_design = intent.get("existing_design")
        publication = intent.get("publication")
        if not isinstance(publication, Mapping) or not (
            isinstance(generation, Mapping) or isinstance(existing_design, Mapping)
        ):
            raise VibePipelineError(
                "stored Vibe request lacks generation or existing-design publication data"
            )
        price_cents = publication.get("price_cents")
        if not isinstance(price_cents, int) or isinstance(price_cents, bool):
            raise VibePipelineError("stored Vibe request lacks an integer price_cents")

        progress = self._progress(record)
        stage = progress.get("stage")
        if record.state == "prepared":
            if isinstance(existing_design, Mapping):
                identity: dict[str, str] = {}
                for key in ("design_id", "slug", "history_id", "project_url"):
                    value = existing_design.get(key)
                    if not isinstance(value, str) or not value:
                        raise VibePipelineError(
                            f"stored existing Vibe design lacks {key}"
                        )
                    identity[key] = value
                record = self._save(
                    record,
                    "in_flight",
                    stage="publish_ready",
                    price_cents=price_cents,
                    pipeline_run_id=identity["history_id"],
                    design_id=identity["design_id"],
                    slug=identity["slug"],
                    history_id=identity["history_id"],
                    project_url=identity["project_url"],
                    remote_design_id=identity["design_id"],
                    remote_slug=identity["slug"],
                    remote_history_id=identity["history_id"],
                    remote_project_url=identity["project_url"],
                )
            else:
                assert isinstance(generation, Mapping)
                self._claim_effect(
                    record,
                    "create_sending",
                    record.idempotency_key,
                    generation,
                )
                record = self._save(
                    record,
                    "in_flight",
                    stage="create_sending",
                    price_cents=price_cents,
                    write_operation_key=record.idempotency_key,
                )
                try:
                    created = self.transport.create_design(
                        generation, operation_key=record.idempotency_key
                    )
                except BaseException as exc:
                    self._effect_error(record, "create_sending", exc)
                    raise AssertionError("unreachable")
                job_id = self._required_effect_text(record, created, "job_id", "create")
                design_id = self._required_effect_text(record, created, "design_id", "create")
                slug = created.get("slug")
                if not isinstance(slug, str) or not slug:
                    slug = design_id
                record = self._save(
                    record,
                    "in_flight",
                    stage="generation_waiting",
                    pipeline_run_id=job_id,
                    design_id=design_id,
                    slug=slug,
                    pause_count=0,
                    remote_design_id=design_id,
                    remote_slug=slug,
                )
        elif stage in {"create_sending", "job_message_sending"}:
            self._mark_ambiguous(
                record,
                f"process stopped during {stage}; the write cannot be repeated safely",
                ambiguous_stage=str(stage),
            )
        elif stage == "publish_sending":
            record = self._reconcile_publish_sending(record, price_cents)

        progress = self._progress(record)
        stage = progress.get("stage")
        if stage in {"generation_waiting", "action_required"}:
            record = self._wait_for_generation(record, pause_handler)
            progress = self._progress(record)
            stage = progress.get("stage")

        if stage == "publish_ready":
            if not isinstance(existing_design, Mapping):
                self._mark_failed(
                    record,
                    "fresh Vibe output is not production-bound; physically validate it "
                    "and call publish_existing",
                )
            record = self._preflight_bound_publish(record, intent)
            progress = self._progress(record)
            design_id = self._required_progress_text(record, "design_id")
            target = str(progress.get("slug") or design_id)
            write_key = f"{record.idempotency_key}:publish"
            self._assert_current_publication_candidate(record, intent)
            effect_payload = {
                "design_id": design_id,
                "history_id": self._required_progress_text(record, "history_id"),
                "packet_hash": self._packet_hash(record),
                "policy_hash": self._policy_hash(record),
                "price_cents": price_cents,
                "sku": self._manifest_sku(record),
                "currency": "USD",
            }
            progress = self._progress(record)
            progress.update(
                {
                    "stage": "publish_sending",
                    "write_operation_key": write_key,
                    "schema_version": 1,
                    "operation_key": record.idempotency_key,
                    "candidate_id": record.candidate_id,
                    "packet_hash": self._packet_hash(record),
                }
            )
            candidate_version = intent.get("candidate_version")
            candidate_content_sha256 = intent.get("candidate_content_sha256")
            if not isinstance(candidate_version, int) or not isinstance(
                candidate_content_sha256, str
            ):
                raise VibePipelineError("publication intent lacks a candidate fence")
            try:
                record = self.store.claim_candidate_publication_send(
                    record.id,
                    candidate_id=str(record.candidate_id or ""),
                    candidate_version=candidate_version,
                    candidate_content_sha256=candidate_content_sha256,
                    response=progress,
                    effect_payload=effect_payload,
                )
            except StateConflictError as exc:
                message = str(exc)
                if "already" in message or "durable owner" in message:
                    raise AmbiguousVibeEffect(
                        "publish_sending already has a durable sender claim; "
                        "reconcile instead of repeating the write",
                        operation_key=record.idempotency_key,
                        publication_id=record.id,
                    ) from exc
                raise VibePipelineError(message) from exc
            try:
                published = self.transport.publish_design(
                    target,
                    {
                        "listing": {
                            "price_cents": price_cents,
                            "sku": self._manifest_sku(record),
                            "currency": "USD",
                        },
                        "expected_history_id": self._required_progress_text(
                            record, "history_id"
                        ),
                        "packet_hash": self._packet_hash(record),
                        "policy_hash": self._policy_hash(record),
                        "project_sha256": self._project_sha256(record),
                        "preconditions": {
                            "rich_page_complete": True,
                            "history_id": self._required_progress_text(
                                record, "history_id"
                            ),
                            "project_sha256": self._project_sha256(record),
                        },
                    },
                    operation_key=write_key,
                )
            except BaseException as exc:
                self._effect_error(record, "publish_sending", exc)
                raise AssertionError("unreachable")
            record = self._accept_publish_receipt(record, published, price_cents)
            stage = "public_waiting"

        if stage == "public_waiting":
            return self._wait_for_public_page(record, price_cents)
        raise VibePipelineError(f"unsupported stored Vibe stage {stage!r}")

    def _preflight_bound_publish(
        self, record: PublicationRecord, intent: Mapping[str, Any]
    ) -> PublicationRecord:
        """Prove the authenticated head is the manufactured revision.

        Reads are safe, but every mismatch is terminal for this immutable
        operation.  Most importantly, no POST is sent when the backend cannot
        atomically compare the expected history during publish.
        """

        try:
            capabilities = self.transport.capabilities()
        except Exception as exc:
            self._mark_failed(record, f"cannot prove publish capabilities: {exc}")
        if not REQUIRED_PUBLIC_WRITE_CAPABILITIES.issubset(capabilities):
            missing = sorted(REQUIRED_PUBLIC_WRITE_CAPABILITIES - capabilities)
            self._mark_failed(
                record,
                "Vibe publish endpoint does not advertise atomic revision/listing "
                f"binding; missing={missing}",
            )
        progress = self._progress(record)
        design_id = self._required_progress_text(record, "design_id")
        try:
            design = self.transport.get_design(design_id)
        except Exception as exc:
            self._mark_failed(record, f"authenticated design preflight failed: {exc}")
        if not isinstance(design, Mapping):
            self._mark_failed(record, "authenticated design preflight returned no object")
        expected: tuple[tuple[str, Any], ...] = (
            ("id", design_id),
            ("slug", self._required_progress_text(record, "slug")),
            ("current_history_id", self._required_progress_text(record, "history_id")),
            ("project_url", self._required_progress_text(record, "project_url")),
        )
        for key, value in expected:
            if design.get(key) != value:
                self._mark_failed(record, f"authenticated design {key} mismatch")
        if not has_exact_alice_product_description_suffix(
            design.get("description")
        ):
            self._mark_failed(
                record,
                "authenticated design description lacks Alice's exact attribution",
            )
        existing = intent.get("existing_design")
        if not isinstance(existing, Mapping):
            self._mark_failed(record, "existing-design manufacturing binding is missing")
        artifact_hashes = existing.get("artifact_hashes")
        if not isinstance(artifact_hashes, Mapping):
            self._mark_failed(record, "existing-design artifact hashes are missing")
        project_sha256 = existing.get("project_sha256")
        if not isinstance(project_sha256, str) or not project_sha256:
            self._mark_failed(record, "existing-design project hash is missing")
        if design.get("project_sha256") != project_sha256:
            self._mark_failed(record, "authenticated design project_sha256 mismatch")
        return self._save(
            record,
            "in_flight",
            stage="publish_ready",
            preflight_history_id=design.get("current_history_id"),
            preflight_project_url=design.get("project_url"),
            revision_binding_capability=REVISION_BOUND_PUBLISH_CAPABILITY,
            listing_binding_capability=LISTING_BOUND_PUBLISH_CAPABILITY,
            rich_page_binding_capability=RICH_PAGE_BOUND_PUBLISH_CAPABILITY,
        )

    def _wait_for_generation(
        self, record: PublicationRecord, pause_handler: PauseHandler | None
    ) -> PublicationRecord:
        progress = self._progress(record)
        job_id = self._required_progress_text(record, "pipeline_run_id")
        last_error: str | None = None
        for attempt in range(self.max_job_polls):
            try:
                job = self.transport.get_job(job_id)
            except (VibeReadError, TimeoutError, urllib.error.URLError, OSError) as exc:
                last_error = str(exc)
                self._sleep_between(attempt, self.max_job_polls)
                continue
            except VibeHTTPError as exc:
                self._mark_failed(record, f"job poll failed: {exc}")
            if not isinstance(job, Mapping):
                last_error = "job poll did not return an object"
                self._sleep_between(attempt, self.max_job_polls)
                continue
            status = str(job.get("status") or "").lower()
            if status in PAUSED_JOB_STATUSES:
                record = self._save(
                    record,
                    "in_flight",
                    stage="action_required",
                    job_status=status,
                )
                if pause_handler is None:
                    raise VibeActionRequired(self._receipt(record), job)
                reply = pause_handler(dict(job))
                if reply is None:
                    raise VibeActionRequired(self._receipt(record), job)
                reply_payload = self._pause_payload(status, reply)
                progress = self._progress(record)
                pause_count = int(progress.get("pause_count") or 0) + 1
                write_key = f"{record.idempotency_key}:pause:{pause_count}"
                self._claim_effect(
                    record,
                    "job_message_sending",
                    write_key,
                    reply_payload,
                )
                record = self._save(
                    record,
                    "in_flight",
                    stage="job_message_sending",
                    pause_count=pause_count,
                    pause_status=status,
                    pause_reply_sha256=self.store.sha256_json(reply_payload),
                    write_operation_key=write_key,
                )
                try:
                    resumed = self.transport.send_job_message(
                        job_id, reply_payload, operation_key=write_key
                    )
                except BaseException as exc:
                    self._effect_error(record, "job_message_sending", exc)
                    raise AssertionError("unreachable")
                if not isinstance(resumed, Mapping):
                    self._mark_ambiguous(
                        record,
                        "job-message write returned no valid receipt; do not retry",
                        ambiguous_stage="job_message_sending",
                    )
                record = self._save(
                    record,
                    "in_flight",
                    stage="generation_waiting",
                    job_status=str(resumed.get("status") or "queued"),
                    write_operation_key=None,
                )
                self._sleep_between(attempt, self.max_job_polls)
                continue
            if status == "done":
                result = job.get("result")
                if not isinstance(result, Mapping):
                    self._mark_failed(record, "Vibe job finished without a built result")
                history_id = result.get("history_id")
                project_url = result.get("project_url")
                if not isinstance(history_id, str) or not history_id:
                    self._mark_failed(record, "Vibe job result lacks history_id")
                if not isinstance(project_url, str) or not project_url:
                    self._mark_failed(record, "Vibe job result lacks project_url")
                return self._save(
                    record,
                    "in_flight",
                    stage="publish_ready",
                    job_status="done",
                    history_id=history_id,
                    project_url=project_url,
                    remote_history_id=history_id,
                    remote_project_url=project_url,
                    write_operation_key=None,
                )
            if status in TERMINAL_FAILURE_JOB_STATUSES:
                self._mark_failed(record, self._job_failure(job, status))
            self._sleep_between(attempt, self.max_job_polls)
        record = self._save(
            record,
            "in_flight",
            stage="generation_waiting",
            poll_error=last_error,
        )
        raise VibePollingTimeout(
            "Vibe generation is still running; reconcile to continue safe polling",
            self._receipt(record),
        )

    def _reconcile_publish_sending(
        self, record: PublicationRecord, price_cents: int
    ) -> PublicationRecord:
        design_id = self._required_progress_text(record, "design_id")
        last_error = "exact public listing not observed"
        for attempt in range(self.max_page_polls):
            try:
                design = self.transport.get_public_design(design_id)
            except VibeHTTPError as exc:
                last_error = f"public read HTTP {exc.status}"
            except (VibeReadError, TimeoutError, urllib.error.URLError, OSError) as exc:
                last_error = f"public read failed:{type(exc).__name__}"
            else:
                if self._published_revision_matches(record, design, price_cents):
                    progress = self._progress(record)
                    return self._save(
                        record,
                        "in_flight",
                        stage="public_waiting",
                        slug=str(
                            design.get("slug")
                            or progress.get("slug")
                            or design_id
                        ),
                        remote_status="published",
                        write_operation_key=None,
                        reconciliation_error=None,
                    )
                last_error = "public listing does not match the immutable release"
            self._sleep_between(attempt, self.max_page_polls)
        pending = self._save(
            record,
            "in_flight",
            stage="publish_sending",
            reconciliation_error=last_error,
        )
        raise VibePollingTimeout(
            "publish outcome remains unknown; repeat only the public readback",
            self._receipt(pending),
        )

    def _accept_publish_receipt(
        self,
        record: PublicationRecord,
        published: Mapping[str, Any],
        price_cents: int,
    ) -> PublicationRecord:
        if not isinstance(published, Mapping):
            self._mark_ambiguous(
                record,
                "publish returned no listing receipt; do not retry",
                ambiguous_stage="publish_sending",
            )
        if published.get("packet_hash") != self._packet_hash(record):
            self._mark_ambiguous(
                record,
                "publish receipt did not echo the production packet hash; do not retry",
                ambiguous_stage="publish_sending",
            )
        if published.get("policy_hash") != self._policy_hash(record):
            self._mark_ambiguous(
                record,
                "publish receipt did not echo the release policy hash; do not retry",
                ambiguous_stage="publish_sending",
            )
        if published.get("rich_page_complete") is not True:
            self._mark_ambiguous(
                record,
                "publish receipt did not echo the atomic rich-page precondition; "
                "do not retry",
                ambiguous_stage="publish_sending",
            )
        if not self._published_revision_matches(record, published, price_cents):
            self._mark_ambiguous(
                record,
                "publish returned no exact revision-bound listing receipt; do not retry",
                ambiguous_stage="publish_sending",
            )
        verification = self.page_verifier(
            published,
            expected_price_cents=price_cents,
            expected_currency="USD",
        )
        if not isinstance(verification, PageVerification) or not verification.complete:
            self._mark_ambiguous(
                record,
                "publish receipt did not contain the complete bound rich page; "
                "do not retry",
                ambiguous_stage="publish_sending",
            )
        progress = self._progress(record)
        design_id = str(published.get("id") or progress.get("design_id") or "")
        slug = str(published.get("slug") or progress.get("slug") or design_id)
        if not design_id or not slug:
            self._mark_ambiguous(
                record,
                "publish receipt lacks design identity; do not retry",
                ambiguous_stage="publish_sending",
            )
        return self._save(
            record,
            "in_flight",
            stage="public_waiting",
            design_id=design_id,
            slug=slug,
            remote_design_id=design_id,
            remote_slug=slug,
            remote_status="published",
            write_operation_key=None,
        )

    def _wait_for_public_page(
        self, record: PublicationRecord, price_cents: int
    ) -> VibePipelineReceipt:
        design_id = self._required_progress_text(record, "design_id")
        last_verification: PageVerification | None = None
        last_error: str | None = None
        for attempt in range(self.max_page_polls):
            try:
                design = self.transport.get_public_design(design_id)
            except VibeHTTPError as exc:
                if exc.status != 404:
                    last_error = str(exc)
                self._sleep_between(attempt, self.max_page_polls)
                continue
            except (VibeReadError, TimeoutError, urllib.error.URLError, OSError) as exc:
                last_error = str(exc)
                self._sleep_between(attempt, self.max_page_polls)
                continue
            if not isinstance(design, Mapping):
                last_error = "public design poll did not return an object"
                self._sleep_between(attempt, self.max_page_polls)
                continue
            if not self._published_revision_matches(record, design, price_cents):
                last_error = "public design is not the bound published history"
                self._sleep_between(attempt, self.max_page_polls)
                continue
            verification = self.page_verifier(
                design,
                expected_price_cents=price_cents,
                expected_currency="USD",
            )
            if not isinstance(verification, PageVerification):
                raise VibePipelineError("page_verifier must return PageVerification")
            last_verification = verification
            if verification.complete:
                progress = self._progress(record)
                response = {
                    **progress,
                    "stage": "complete",
                    "operation_key": record.idempotency_key,
                    "packet_hash": self._packet_hash(record),
                    "price_cents": price_cents,
                    "currency": "USD",
                    "project_sha256": self._project_sha256(record),
                    "page_url": verification.page_url,
                    "verification": asdict(verification),
                    "listing_sku": self._manifest_sku(record),
                    "write_operation_key": None,
                }
                confirmed = self.store.transition_publication(
                    record.id,
                    "confirmed",
                    expected_state="in_flight",
                    remote_design_id=design_id,
                    slug=str(design.get("slug") or progress.get("slug") or design_id),
                    history_id=str(progress.get("history_id") or "") or None,
                    status="published",
                    project_url=str(progress.get("project_url") or "") or None,
                    response=response,
                )
                self._finish_candidate_publication_effect(confirmed, "confirmed")
                return self._receipt(confirmed)
            self._sleep_between(attempt, self.max_page_polls)
        record = self._save(
            record,
            "in_flight",
            stage="public_waiting",
            verification=(None if last_verification is None else asdict(last_verification)),
            poll_error=last_error,
        )
        raise VibePageIncomplete(self._receipt(record), last_verification)

    def _save(
        self,
        record: PublicationRecord,
        state: str,
        *,
        remote_design_id: str | None = None,
        remote_slug: str | None = None,
        remote_history_id: str | None = None,
        remote_status: str | None = None,
        remote_project_url: str | None = None,
        **changes: Any,
    ) -> PublicationRecord:
        response = self._progress(record)
        response.update(changes)
        response.setdefault("schema_version", 1)
        response["operation_key"] = record.idempotency_key
        response["candidate_id"] = record.candidate_id
        response["packet_hash"] = self._packet_hash(record)
        return self.store.transition_publication(
            record.id,
            state,
            expected_state=record.state,
            remote_design_id=remote_design_id,
            slug=remote_slug,
            history_id=remote_history_id,
            status=remote_status,
            project_url=remote_project_url,
            response=response,
        )

    def _claim_effect(
        self,
        record: PublicationRecord,
        stage: str,
        operation_key: str,
        payload: Mapping[str, Any],
    ) -> None:
        """Atomically make one process the sole sender for a remote write."""

        key = f"alice.effect:vibe:{record.id}:{operation_key}"
        try:
            self.store.put_state(
                key,
                {
                    "publication_id": record.id,
                    "stage": stage,
                    "operation_key": operation_key,
                    "payload_sha256": self.store.sha256_json(payload),
                    "status": "sending",
                },
                None,
            )
        except StateConflictError as exc:
            raise AmbiguousVibeEffect(
                f"{stage} already has a durable sender claim; reconcile instead "
                "of repeating the write",
                operation_key=record.idempotency_key,
                publication_id=record.id,
            ) from exc

    def _assert_current_publication_candidate(
        self, record: PublicationRecord, intent: Mapping[str, Any]
    ) -> None:
        candidate_id = intent.get("candidate_id")
        version = intent.get("candidate_version")
        content_hash = intent.get("candidate_content_sha256")
        if not isinstance(candidate_id, str) or not isinstance(version, int):
            raise VibePipelineError("publication intent lacks a candidate fence")
        candidate = self.store.get_candidate(candidate_id)
        if candidate.state != "publish_ready" or candidate.version != version:
            raise VibePipelineError(
                "candidate was retracted or revised before the public write"
            )
        if self.store.sha256_json(candidate.content) != content_hash:
            raise VibePipelineError(
                "candidate content changed before the public write"
            )
        release = candidate.metadata.get("release_decision")
        if not isinstance(release, Mapping):
            raise VibePipelineError("candidate release decision disappeared")
        for key, expected in (
            ("allowed", True),
            ("effect_mode", "live"),
            ("policy_hash", intent.get("policy_hash")),
            ("production_packet_hash", intent.get("packet_hash")),
            ("reviewed_packet_hash", intent.get("packet_hash")),
            ("production_manifest", intent.get("production_manifest")),
        ):
            if release.get(key) != expected:
                raise VibePipelineError(
                    f"candidate release decision changed before publish: {key}"
                )

    def _effect_error(
        self, record: PublicationRecord, stage: str, exc: BaseException
    ) -> None:
        if isinstance(exc, AmbiguousVibeEffect) or isinstance(
            exc, (TimeoutError, urllib.error.URLError, OSError)
        ):
            self._mark_ambiguous(
                record,
                f"{stage} outcome is unknown; do not retry",
                ambiguous_stage=stage,
            )
        if isinstance(exc, VibeHTTPError):
            self._mark_failed(record, f"{stage} was rejected: {exc}")
        if isinstance(exc, VibePipelineError):
            self._mark_failed(record, f"{stage} failed: {exc}")
        self._mark_ambiguous(
            record,
            f"{stage} raised without a durable receipt; do not retry",
            ambiguous_stage=stage,
        )

    def _mark_ambiguous(
        self,
        record: PublicationRecord,
        message: str,
        *,
        ambiguous_stage: str,
    ) -> None:
        response = self._progress(record)
        response.update(
            {
                "stage": "ambiguous",
                "ambiguous_stage": ambiguous_stage,
                "operation_key": record.idempotency_key,
                "candidate_id": record.candidate_id,
                "packet_hash": self._packet_hash(record),
            }
        )
        ambiguous = self.store.transition_publication(
            record.id,
            "ambiguous",
            expected_state=record.state,
            response=response,
            last_error=message,
        )
        self._finish_candidate_publication_effect(ambiguous, "ambiguous")
        raise AmbiguousVibeEffect(
            message,
            operation_key=ambiguous.idempotency_key,
            publication_id=ambiguous.id,
        )

    def _mark_failed(self, record: PublicationRecord, message: str) -> None:
        response = self._progress(record)
        response.update(
            {
                "stage": "failed",
                "operation_key": record.idempotency_key,
                "candidate_id": record.candidate_id,
                "packet_hash": self._packet_hash(record),
            }
        )
        failed = self.store.transition_publication(
            record.id,
            "failed",
            expected_state=record.state,
            response=response,
            last_error=message,
        )
        self._finish_candidate_publication_effect(failed, "failed")
        raise VibePipelineError(message)

    def _finish_candidate_publication_effect(
        self, record: PublicationRecord, status: str
    ) -> None:
        request = record.request if isinstance(record.request, Mapping) else None
        candidate_id = request.get("candidate_id") if request is not None else None
        candidate_version = (
            request.get("candidate_version") if request is not None else None
        )
        if not isinstance(candidate_id, str) or not isinstance(candidate_version, int):
            return
        receipt_sha256 = (
            self.store.sha256_json(record.response) if status == "confirmed" else None
        )
        self.store.finish_candidate_publication_send(
            record.id,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            status=status,
            receipt_sha256=receipt_sha256,
        )

    def _required_effect_text(
        self,
        record: PublicationRecord,
        value: Mapping[str, Any],
        key: str,
        effect: str,
    ) -> str:
        found = value.get(key) if isinstance(value, Mapping) else None
        if not isinstance(found, str) or not found:
            self._mark_ambiguous(
                record,
                f"{effect} returned no {key}; do not retry",
                ambiguous_stage=f"{effect}_sending",
            )
        return found

    @staticmethod
    def _required_progress_text(record: PublicationRecord, key: str) -> str:
        progress = VibePipeline._progress(record)
        value = progress.get(key)
        if not isinstance(value, str) or not value:
            raise VibePipelineError(f"stored Vibe progress lacks {key}")
        return value

    @staticmethod
    def _progress(record: PublicationRecord) -> dict[str, Any]:
        return dict(record.response) if isinstance(record.response, Mapping) else {}

    @staticmethod
    def _pause_payload(status: str, reply: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(reply, Mapping):
            raise ValueError("pause handler must return a mapping or None")
        message = reply.get("message")
        set_id = reply.get("set_id")
        approve = reply.get("approve")
        if status in {"awaiting_questions", "awaiting_concept_input", "stopped"}:
            if not isinstance(message, str) or not message.strip():
                raise ValueError(f"{status} requires a non-empty message")
            return {"message": message.strip()}
        if status == "awaiting_concept_selection":
            has_message = isinstance(message, str) and bool(message.strip())
            has_set = isinstance(set_id, str) and set_id.lower() in {"a", "b", "c"}
            if has_message == has_set:
                raise ValueError(
                    "concept selection requires exactly one of message or set_id a/b/c"
                )
            return (
                {"message": message.strip()}
                if has_message
                else {"set_id": set_id.lower()}
            )
        if status == "awaiting_plan_approval":
            if not isinstance(approve, bool):
                raise ValueError("plan approval requires boolean approve")
            payload: dict[str, Any] = {"approve": approve}
            if isinstance(message, str) and message.strip():
                payload["message"] = message.strip()
            return payload
        raise ValueError(f"unsupported pause status {status!r}")

    @staticmethod
    def _public_price_matches(design: Mapping[str, Any], price_cents: int) -> bool:
        listing = design.get("listing") if isinstance(design, Mapping) else None
        return bool(
            design.get("status") == "public"
            and isinstance(listing, Mapping)
            and listing.get("active") is True
            and listing.get("price_cents") == price_cents
        )

    def _published_revision_matches(
        self,
        record: PublicationRecord,
        design: Mapping[str, Any],
        price_cents: int,
    ) -> bool:
        progress = self._progress(record)
        listing = design.get("listing") if isinstance(design, Mapping) else None
        try:
            expected_sku = self._manifest_sku(record)
        except VibePipelineError:
            return False
        return bool(
            self._public_price_matches(design, price_cents)
            and isinstance(listing, Mapping)
            and listing.get("sku") == expected_sku
            and listing.get("currency") == "USD"
            and design.get("rich_page_complete") is True
            and design.get("id") == progress.get("design_id")
            and design.get("slug") == progress.get("slug")
            and design.get("published_history_id") == progress.get("history_id")
            and design.get("project_url") == progress.get("project_url")
            and design.get("project_sha256") == self._project_sha256(record)
            and design.get("packet_hash") == self._packet_hash(record)
            and design.get("policy_hash") == self._policy_hash(record)
        )

    @staticmethod
    def _manifest_sku(record: PublicationRecord) -> str:
        manifest = (
            record.request.get("production_manifest")
            if isinstance(record.request, Mapping)
            else None
        )
        listing = manifest.get("listing") if isinstance(manifest, Mapping) else None
        sku = listing.get("sku") if isinstance(listing, Mapping) else None
        if not isinstance(sku, str) or not sku:
            raise VibePipelineError("stored production manifest lacks listing.sku")
        return sku

    @staticmethod
    def _job_failure(job: Mapping[str, Any], status: str) -> str:
        error = job.get("error")
        try:
            encoded = json.dumps(
                error,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError):
            encoded = repr(type(error).__name__).encode("utf-8")
        return (
            f"Vibe job {status}; "
            f"error_sha256={hashlib.sha256(encoded).hexdigest()}"
        )

    def _receipt(self, record: PublicationRecord) -> VibePipelineReceipt:
        progress = self._progress(record)
        verification_value = progress.get("verification")
        verification = None
        if isinstance(verification_value, Mapping):
            try:
                verification = PageVerification(
                    complete=bool(verification_value.get("complete")),
                    page_url=str(verification_value.get("page_url") or ""),
                    failures=tuple(verification_value.get("failures") or ()),
                    warnings=tuple(verification_value.get("warnings") or ()),
                    image_count=int(verification_value.get("image_count") or 0),
                    video_count=int(verification_value.get("video_count") or 0),
                    story_count=int(verification_value.get("story_count") or 0),
                )
            except (TypeError, ValueError):
                verification = None
        price = progress.get("price_cents")
        if not isinstance(price, int):
            publication = record.request.get("publication") if isinstance(record.request, Mapping) else None
            price = publication.get("price_cents") if isinstance(publication, Mapping) else 0
        stage = str(progress.get("stage") or record.state)
        return VibePipelineReceipt(
            operation_key=record.idempotency_key,
            publication_id=record.id,
            candidate_id=str(record.candidate_id or progress.get("candidate_id") or ""),
            packet_hash=self._packet_hash(record),
            pipeline_run_id=self._optional_text(progress.get("pipeline_run_id")),
            design_id=self._optional_text(progress.get("design_id") or record.remote_design_id),
            slug=self._optional_text(progress.get("slug") or record.slug),
            history_id=self._optional_text(progress.get("history_id") or record.history_id),
            status=stage,
            price_cents=int(price),
            sku=self._manifest_sku(record),
            currency="USD",
            page_url=self._optional_text(progress.get("page_url")),
            verification=verification,
        )

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _packet_hash(record: PublicationRecord) -> str:
        value = record.request.get("packet_hash") if isinstance(record.request, Mapping) else None
        if (
            not isinstance(value, str)
            or len(value) != 64
            or value.lower() != value
            or any(ch not in "0123456789abcdef" for ch in value)
        ):
            raise VibePipelineError("stored Vibe request lacks a valid packet_hash")
        return value

    @staticmethod
    def _policy_hash(record: PublicationRecord) -> str:
        value = record.request.get("policy_hash") if isinstance(record.request, Mapping) else None
        if (
            not isinstance(value, str)
            or len(value) != 64
            or value.lower() != value
            or any(ch not in "0123456789abcdef" for ch in value)
        ):
            raise VibePipelineError("stored Vibe request lacks a valid policy_hash")
        return value

    @staticmethod
    def _project_sha256(record: PublicationRecord) -> str:
        existing = (
            record.request.get("existing_design")
            if isinstance(record.request, Mapping)
            else None
        )
        value = (
            existing.get("project_sha256")
            if isinstance(existing, Mapping)
            else None
        )
        if (
            not isinstance(value, str)
            or len(value) != 64
            or value.lower() != value
            or any(ch not in "0123456789abcdef" for ch in value)
        ):
            raise VibePipelineError(
                "stored Vibe request lacks a valid project_sha256"
            )
        return value

    def _sleep_between(self, attempt: int, limit: int) -> None:
        if attempt + 1 < limit and self.poll_interval_seconds:
            self.sleep(self.poll_interval_seconds)


class VibePublishingAdapter:
    """Map Alice publish tasks to the existing verified-design Vibe path."""

    def __init__(self, pipeline: VibePipeline) -> None:
        self.pipeline = pipeline
        self.name = "publishing_pipeline"
        self.evidence_class = "publishing_pipeline"

    def release_capabilities(self) -> tuple[str, ...]:
        """Report policy capabilities only when live revision binding is proven."""

        try:
            capabilities = self.pipeline.transport.capabilities()
            if not REQUIRED_PUBLIC_WRITE_CAPABILITIES.issubset(capabilities):
                return ()
        except Exception:
            return ()
        return ALICE_REVISION_BOUND_RELEASE_CAPABILITIES

    def invoke(self, operation: str, payload: dict[str, Any]) -> AdapterReceipt:
        started = time.monotonic()
        input_sha256 = adapter_input_sha256(operation, payload)
        if operation == "publish.invoke_pipeline":
            request = self._existing_request(payload)
            try:
                receipt = self.pipeline.publish_existing(request)
            except VibePollingTimeout as exc:
                # Generation/page observation is read-only at this point and
                # may be leased again safely. Remote writes remain fenced in
                # the publication record and are never repeated.
                raise AdapterError(str(exc)) from exc
        elif operation == "publish.verify_page":
            receipt = self._verify_again(payload)
        else:
            raise AdapterError(f"unsupported Vibe publishing operation {operation!r}")
        evidence = receipt.evidence_receipt()
        return AdapterReceipt(
            adapter=self.name,
            run_id=receipt.publication_id,
            status="passed",
            evidence_class=self.evidence_class,
            payload=evidence,
            input_sha256=input_sha256,
            elapsed_seconds=time.monotonic() - started,
        )

    def _existing_request(self, payload: Mapping[str, Any]) -> ExistingVibeDesignRequest:
        candidate_id = payload.get("candidate_id")
        version = payload.get("candidate_version")
        if not isinstance(candidate_id, str) or not candidate_id:
            raise AdapterError("publish task lacks candidate_id")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise AdapterError("publish task lacks candidate_version")
        candidate = self.pipeline.store.get_candidate(candidate_id)
        if candidate.version != version or candidate.state != "publish_ready":
            raise AdapterError("publish task candidate snapshot is stale or not publish_ready")
        candidate_snapshot = payload.get("candidate")
        candidate_content_sha256 = payload.get("candidate_content_sha256")
        if candidate_snapshot != candidate.content:
            raise AdapterError("publish task candidate content is not current")
        calculated_candidate_hash = self.pipeline.store.sha256_json(candidate.content)
        if candidate_content_sha256 != calculated_candidate_hash:
            raise AdapterError("publish task candidate content hash mismatch")
        candidate_metadata = payload.get("candidate_metadata")
        if not isinstance(candidate_metadata, Mapping) or dict(candidate_metadata) != dict(
            candidate.metadata
        ):
            raise AdapterError("publish task candidate metadata is not current")
        dependencies = payload.get("dependencies")
        packet_dependency = (
            dependencies.get("publish.packet")
            if isinstance(dependencies, Mapping)
            else None
        )
        result = (
            packet_dependency.get("result")
            if isinstance(packet_dependency, Mapping)
            else None
        )
        if not isinstance(result, Mapping) or result.get("executor") != "release_policy":
            raise AdapterError(
                "publish.packet must come from the deterministic release_policy executor"
            )
        content = result.get("content")
        if not isinstance(content, Mapping):
            raise AdapterError("publish task lacks the completed publication packet")
        packet = content.get("publication_packet")
        packet_hash = content.get("packet_hash")
        if not isinstance(packet, Mapping) or not isinstance(packet_hash, str):
            raise AdapterError("publication packet or packet_hash is missing")
        calculated = self.pipeline.store.sha256_json(packet)
        if calculated != packet_hash:
            raise AdapterError("publication packet hash does not match its content")
        production_version = packet.get("candidate_version")
        if (
            not isinstance(production_version, int)
            or isinstance(production_version, bool)
            or production_version < 1
            or production_version > version - 1
        ):
            raise AdapterError("publication packet candidate_version mismatch")
        for key, expected in (
            ("candidate_id", candidate_id),
            ("candidate_content_sha256", candidate_content_sha256),
        ):
            if packet.get(key) != expected:
                raise AdapterError(f"publication packet {key} mismatch")
        release_decision = content.get("release_decision")
        if not isinstance(release_decision, Mapping):
            raise AdapterError("publication wrapper lacks release_decision")
        if release_decision.get("allowed") is not True:
            raise AdapterError("publication release_decision is not allowed")
        production_packet_hash = release_decision.get("production_packet_hash")
        reviewed_packet_hash = release_decision.get("reviewed_packet_hash")
        policy_hash = release_decision.get("policy_hash")
        if content.get("policy_hash") != policy_hash:
            raise AdapterError("publication wrapper policy_hash mismatch")
        if packet_hash not in (production_packet_hash, reviewed_packet_hash) or (
            production_packet_hash != reviewed_packet_hash
        ):
            raise AdapterError(
                "publication packet, production, and reviewed hashes do not match"
            )
        for key, expected in (
            ("effect_mode", "live"),
            ("candidate_id", candidate_id),
            ("release_candidate_version", version - 1),
            ("publish_candidate_version", version),
            ("production_candidate_version", production_version),
            ("production_packet_hash", production_packet_hash),
            ("reviewed_packet_hash", reviewed_packet_hash),
            ("policy_hash", policy_hash),
        ):
            if release_decision.get(key) != expected:
                raise AdapterError(f"release decision {key} mismatch")
        manufacturing = packet.get("manufacturing")
        design = (
            manufacturing.get("vibe_design")
            if isinstance(manufacturing, Mapping)
            else None
        )
        price = packet.get("price")
        if not isinstance(design, Mapping):
            raise AdapterError("publication manufacturing lacks vibe_design identity")
        if not isinstance(price, Mapping):
            raise AdapterError("publication packet lacks price")
        pinned_release = candidate_metadata.get("release_decision")
        if not isinstance(pinned_release, Mapping):
            raise AdapterError("candidate metadata lacks its pinned release_decision")
        for key, expected in (
            ("allowed", True),
            ("effect_mode", "live"),
            ("candidate_id", candidate_id),
            ("candidate_version", version - 1),
            ("release_candidate_version", version - 1),
            ("production_candidate_version", production_version),
            ("production_packet_hash", production_packet_hash),
            ("reviewed_packet_hash", reviewed_packet_hash),
            ("policy_hash", policy_hash),
            ("production_manifest", packet),
        ):
            if pinned_release.get(key) != expected:
                raise AdapterError(f"candidate metadata release_decision {key} mismatch")
        wrapper_manifest_hash = release_decision.get("artifact_manifest_sha256")
        if wrapper_manifest_hash is not None and (
            wrapper_manifest_hash != pinned_release.get("artifact_manifest_sha256")
        ):
            raise AdapterError(
                "release decision artifact_manifest_sha256 mismatch"
            )
        price_cents = price.get("price_cents")
        operation_key = (
            f"alice:vibe:{candidate_id}:v{version}:{packet_hash}"
        )
        try:
            return ExistingVibeDesignRequest(
                operation_key=operation_key,
                candidate_id=candidate_id,
                candidate_version=version,
                candidate_content_sha256=str(candidate_content_sha256 or ""),
                packet_hash=packet_hash,
                production_packet_hash=str(production_packet_hash or ""),
                reviewed_packet_hash=str(reviewed_packet_hash or ""),
                policy_hash=str(policy_hash or ""),
                production_candidate_version=production_version,
                production_manifest=dict(packet),
                design_id=str(design.get("design_id") or ""),
                slug=str(design.get("slug") or ""),
                history_id=str(design.get("history_id") or ""),
                project_url=str(design.get("project_url") or ""),
                project_sha256=str(design.get("project_sha256") or ""),
                price_cents=price_cents,
                release_decision=dict(release_decision),
                artifact_hashes=dict(design.get("artifact_hashes") or {}),
            )
        except (TypeError, ValueError) as exc:
            raise AdapterError(f"invalid verified Vibe publication packet: {exc}") from exc

    def _verify_again(self, payload: Mapping[str, Any]) -> VibePipelineReceipt:
        candidate_id = payload.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            raise AdapterError("page verification task lacks candidate_id")
        candidate = self.pipeline.store.get_candidate(candidate_id)
        version = payload.get("candidate_version")
        if version != candidate.version or candidate.state != "page_ready":
            raise AdapterError(
                "page verification task candidate snapshot is stale or not page_ready"
            )
        if payload.get("candidate") != candidate.content or payload.get(
            "candidate_content_sha256"
        ) != self.pipeline.store.sha256_json(candidate.content):
            raise AdapterError("page verification task candidate content is stale")
        metadata = payload.get("candidate_metadata")
        if not isinstance(metadata, Mapping) or dict(metadata) != dict(candidate.metadata):
            raise AdapterError("page verification task candidate metadata is stale")
        publications = self.pipeline.store.list_publications(
            target=PUBLICATION_TARGET,
            state="confirmed",
            candidate_id=candidate_id,
            limit=100,
        )
        if not publications:
            raise AdapterError("candidate has no confirmed Vibe publication")
        record = publications[-1]
        # publish.invoke_pipeline advances publish_ready -> page_ready after its
        # receipt lands, so the immutable publication must name exactly the
        # immediately preceding candidate version. Product content must remain
        # byte-for-byte identical across that lifecycle-only transition.
        if not isinstance(record.request, Mapping) or (
            record.request.get("candidate_id") != candidate_id
            or record.request.get("candidate_version") != version - 1
            or record.request.get("candidate_content_sha256")
            != payload.get("candidate_content_sha256")
        ):
            raise AdapterError("confirmed Vibe publication is for a stale candidate")
        release = metadata.get("release_decision")
        manifest = record.request.get("production_manifest")
        wrapper = record.request.get("release_decision")
        existing_design = record.request.get("existing_design")
        publication = record.request.get("publication")
        if not all(
            isinstance(value, Mapping)
            for value in (release, manifest, wrapper, existing_design, publication)
        ):
            raise AdapterError(
                "confirmed Vibe publication lacks its deterministic release binding"
            )
        assert isinstance(release, Mapping)
        assert isinstance(manifest, Mapping)
        assert isinstance(wrapper, Mapping)
        assert isinstance(existing_design, Mapping)
        assert isinstance(publication, Mapping)
        packet_hash = record.request.get("packet_hash")
        production_hash = record.request.get("production_packet_hash")
        reviewed_hash = record.request.get("reviewed_packet_hash")
        policy_hash = record.request.get("policy_hash")
        production_version = record.request.get("production_candidate_version")
        publish_version = record.request.get("candidate_version")
        if (
            not isinstance(publish_version, int)
            or isinstance(publish_version, bool)
            or not isinstance(production_version, int)
            or isinstance(production_version, bool)
        ):
            raise AdapterError("confirmed Vibe publication has invalid candidate versions")
        if (
            self.pipeline.store.sha256_json(manifest) != packet_hash
            or packet_hash != production_hash
            or packet_hash != reviewed_hash
        ):
            raise AdapterError("confirmed Vibe publication packet hashes no longer match")
        for key, expected in (
            ("allowed", True),
            ("effect_mode", "live"),
            ("candidate_id", candidate_id),
            ("candidate_version", publish_version - 1),
            ("release_candidate_version", publish_version - 1),
            ("production_candidate_version", production_version),
            ("production_packet_hash", production_hash),
            ("reviewed_packet_hash", reviewed_hash),
            ("policy_hash", policy_hash),
            ("production_manifest", manifest),
        ):
            if release.get(key) != expected:
                raise AdapterError(
                    f"confirmed Vibe publication no longer matches release decision {key}"
                )
        for key, expected in (
            ("allowed", True),
            ("effect_mode", "live"),
            ("candidate_id", candidate_id),
            ("release_candidate_version", publish_version - 1),
            ("publish_candidate_version", publish_version),
            ("production_candidate_version", production_version),
            ("production_packet_hash", production_hash),
            ("reviewed_packet_hash", reviewed_hash),
            ("policy_hash", policy_hash),
        ):
            if wrapper.get(key) != expected:
                raise AdapterError(
                    f"confirmed Vibe publication wrapper {key} no longer matches"
                )
        bound_manufacturing = manifest.get("manufacturing")
        bound_design = (
            bound_manufacturing.get("vibe_design")
            if isinstance(bound_manufacturing, Mapping)
            else None
        )
        if not isinstance(existing_design, Mapping) or existing_design != bound_design:
            raise AdapterError(
                "confirmed Vibe publication design no longer matches manufacturing"
            )
        price = manifest.get("price")
        if not isinstance(price, Mapping) or (
            publication.get("price_cents") != price.get("price_cents")
        ):
            raise AdapterError(
                "confirmed Vibe publication price no longer matches production"
            )
        receipt = self.pipeline.reconcile(record.idempotency_key)
        target = receipt.slug or receipt.design_id
        if not target:
            raise AdapterError("confirmed Vibe receipt lacks design identity")
        try:
            design = self.pipeline.transport.get_public_design(target)
        except (VibeReadError, VibeHTTPError) as exc:
            raise AdapterError(f"could not reread the public Factory page: {exc}") from exc
        if not self.pipeline._published_revision_matches(
            record, design, receipt.price_cents
        ):
            raise AdapterError(
                "public Factory page is not the revision bound by the publication receipt"
            )
        verification = self.pipeline.page_verifier(
            design,
            expected_price_cents=receipt.price_cents,
            expected_currency="USD",
        )
        if not verification.complete:
            raise AdapterError(
                "public Factory page no longer satisfies its contract: "
                + ", ".join(verification.failures)
            )
        return VibePipelineReceipt(
            operation_key=receipt.operation_key,
            publication_id=receipt.publication_id,
            candidate_id=receipt.candidate_id,
            packet_hash=receipt.packet_hash,
            pipeline_run_id=receipt.pipeline_run_id,
            design_id=receipt.design_id,
            slug=receipt.slug,
            history_id=receipt.history_id,
            status="complete",
            price_cents=receipt.price_cents,
            sku=receipt.sku,
            currency=receipt.currency,
            page_url=verification.page_url,
            verification=verification,
        )
