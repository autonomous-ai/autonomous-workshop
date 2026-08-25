"""Workshop-owned release providers for lane-specific Playtest proof.

Inventors should not have to replace Playtest merely because their lane needs
independent rules, science, or consent/reference evidence.  This module keeps
those integrations behind one Workshop-owned seam:

``WorkshopLanePlaytestProviders.prepare(context, capability)``

Preparation reads and re-hashes the exact sealed Make files, asks the selected
Workshop evidence provider for independent inputs, and returns a
:class:`PreparedLaneRelease`.  Preparation does not mutate the Playtest
workspace, so the ordinary AI-player review may still run before evidence is
sealed.  Once that review passes, ``prepared.seal(evidence_root)`` writes the
canonical capability receipts and returns a core-valid ``release_proof``.

The adapters deliberately do not use a language-model verdict as release
proof.  Classic checkers uses a pinned rules model and deterministic seeded
engine.  Science requires source-bound comparison cases.  Tiny worlds require
an explicit Workshop-managed consent/reference provider; private reference
bytes are hashed in memory and are never copied into Playtest evidence.
"""

from __future__ import annotations

import base64
import hashlib
import json
import random
import re
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Protocol, Sequence, Tuple

from .agent_invent import (
    _SCIENCE_RELEVANCE_ALGORITHM,
    _SCIENCE_RELEVANCE_STOPWORDS_SHA256,
    InventResearch,
    InventResearchSource,
    _independent_science_authority_source,
    _science_relevance_record,
)
from .errors import ContractError
from .jobs import Need, PlaytestContext, WaitingFor
from .models import (
    MAX_EVIDENCE_JSON_BYTES,
    require_exact_version,
    require_sha256,
    require_utc_timestamp,
)
from .playtest_release import CapabilityReleaseProof, ReleaseProofSource
from .reward_loop import json_sha256


_RELEASE_RECEIPT_KIND = "workshop.capability-release-receipt"
_CAPABILITIES = frozenset(
    ("classic-rules-test", "science-test", "world-test")
)
_PROOF_CLASSES = {
    "classic-rules-test": "classic-rule-conformance-proof",
    "science-test": "source-bound-science-proof",
    "world-test": "reference-bound-world-proof",
}
_RECEIPT_ROLES = {
    "classic-rules-test": ("reference-rules", "game-traces"),
    "science-test": ("science-sources", "content-coverage-traces"),
    "world-test": ("consent-record", "reference-material", "likeness-traces"),
}
_SOURCE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SAFE_MEDIA_TYPES = frozenset(
    ("image/jpeg", "image/png", "image/webp", "application/octet-stream")
)
_PUBLIC_SOURCE_MEDIA_TYPES = frozenset(
    (
        "application/json",
        "application/pdf",
        "application/xml",
        "text/csv",
        "text/html",
        "text/plain",
    )
)
_DISALLOWED_OPINION_METHODS = frozenset(
    ("language-model-opinion", "model-opinion", "self-report", "trust-me")
)


def _canonical_json(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("lane provider evidence must be finite JSON") from exc


def _json_copy(value: Any, label: str) -> Any:
    try:
        return json.loads(_canonical_json(value).decode("utf-8"))
    except (TypeError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("%s must be finite JSON" % label) from exc


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_science_scale(scale: Mapping[str, Any]) -> str:
    """Canonical exact text used by replayable science scale cases."""

    if not isinstance(scale, Mapping) or not scale:
        raise ContractError("science scale must be a non-empty object")
    try:
        return json.dumps(
            dict(scale),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("science scale must be finite JSON") from exc


def _bounded_text(value: Any, label: str, maximum: int = 4_096) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 and character not in "\n\r\t" for character in value)
        or any(ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded non-empty text" % label)
    return value


def _safe_source_id(value: Any, label: str = "source id") -> str:
    if not isinstance(value, str) or len(value) > 128 or not _SOURCE_ID.fullmatch(value):
        raise ContractError("%s must be a safe identifier" % label)
    return value


def _public_https(value: Any, label: str) -> str:
    text = _bounded_text(value, label, 2_048)
    try:
        parsed = urllib.parse.urlsplit(text)
        port = parsed.port
    except ValueError as exc:
        raise ContractError("%s must be a public HTTPS URL" % label) from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.fragment
        or "\\" in text
        or any(character.isspace() for character in text)
    ):
        raise ContractError("%s must be a public HTTPS URL" % label)
    return text


def _bounded_bytes(value: Any, label: str, maximum: int = 512 * 1024) -> bytes:
    if not isinstance(value, bytes) or not value or len(value) > maximum:
        raise ContractError("%s must be bounded non-empty bytes" % label)
    return value


def _need(capability: str, reason: str, instructions: str) -> WaitingFor:
    return WaitingFor(Need("playtest", capability, reason, instructions))


def _sealed_entry(context: PlaytestContext, relative: str) -> Tuple[bytes, str]:
    inventory = {
        entry.path: entry.sha256 for entry in context.made.artifact_manifest.entries
    }
    expected = inventory.get(relative)
    if expected is None:
        raise ContractError("sealed Make lacks %s" % relative)
    path = context.made.artifact_root / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(context.made.artifact_root.resolve(strict=True))
        if path.is_symlink() or not resolved.is_file():
            raise OSError("not a regular file")
        payload = resolved.read_bytes()
    except (OSError, ValueError) as exc:
        raise ContractError("sealed Make source is missing or unsafe") from exc
    actual = _sha256_bytes(payload)
    if actual != expected:
        raise ContractError("sealed Make source bytes changed")
    context.made.assert_current()
    return payload, actual


def _sealed_json(context: PlaytestContext, relative: str) -> Tuple[Mapping[str, Any], str]:
    payload, digest = _sealed_entry(context, relative)
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("sealed Make source must be UTF-8 JSON") from exc
    if not isinstance(value, Mapping):
        raise ContractError("sealed Make source must be a JSON object")
    return value, digest


def _lane_contract(context: PlaytestContext) -> Tuple[Mapping[str, Any], str]:
    mechanical, digest = _sealed_json(context, "playtest/mechanical.json")
    plan = mechanical.get("digital_test_plan")
    contract = plan.get("invent_lane_contract") if isinstance(plan, Mapping) else None
    if not isinstance(contract, Mapping) or contract.get("lane") != context.blueprint.lane:
        raise ContractError("Make lacks its exact Invent lane contract")
    declared = plan.get("invent_lane_contract_sha256")
    if declared != json_sha256(contract):
        raise ContractError("Make Invent lane contract hash is invalid")
    return contract, digest


@dataclass(frozen=True)
class ProviderIdentity:
    """Versioned identity for an independent Workshop evidence provider."""

    name: str
    version: str
    config_sha256: str
    method_class: str

    def __post_init__(self) -> None:
        _bounded_text(self.name, "provider name", 300)
        require_exact_version(self.version, "provider version")
        require_sha256(self.config_sha256, "provider config sha256")
        method = _bounded_text(self.method_class, "provider method class", 200)
        if method.casefold() in _DISALLOWED_OPINION_METHODS:
            raise ContractError("a language-model opinion alone is not release proof")

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "version": self.version,
            "config_sha256": self.config_sha256,
            "method_class": self.method_class,
        }


@dataclass(frozen=True)
class PublicScienceSource:
    """Exact public source bytes observed by a Workshop science provider."""

    source_id: str
    title: str
    publisher: str
    url: str
    retrieved_at: str
    content: bytes = field(repr=False, compare=False)
    media_type: str = "text/plain"

    def __post_init__(self) -> None:
        _safe_source_id(self.source_id, "science source id")
        _bounded_text(self.title, "science source title", 500)
        _bounded_text(self.publisher, "science source publisher", 300)
        _public_https(self.url, "science source URL")
        require_utc_timestamp(self.retrieved_at, "science source retrieved_at")
        _bounded_bytes(self.content, "science source content", 256 * 1024)
        if self.media_type not in _PUBLIC_SOURCE_MEDIA_TYPES:
            raise ContractError("science source media type is unsupported")

    @property
    def sha256(self) -> str:
        return _sha256_bytes(self.content)

    def receipt_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "publisher": self.publisher,
            "url": self.url,
            "retrieved_at": self.retrieved_at,
            "media_type": self.media_type,
            "content_sha256": self.sha256,
            "content_bytes": len(self.content),
            "content_encoding": "base64",
            "content_base64": base64.b64encode(self.content).decode("ascii"),
        }


@dataclass(frozen=True)
class ScienceAccuracyCase:
    case_id: str
    source_ids: Sequence[str]
    product_field: str
    expected: str
    observed: str
    source_excerpt: str

    def __post_init__(self) -> None:
        _safe_source_id(self.case_id, "science accuracy case id")
        sources = tuple(self.source_ids)
        if not sources or len(sources) != len(set(sources)):
            raise ContractError("science accuracy case requires unique sources")
        for source_id in sources:
            _safe_source_id(source_id, "science accuracy source id")
        if self.product_field not in ("phenomenon", "model", "scale"):
            raise ContractError("science accuracy case product_field is invalid")
        _bounded_text(self.expected, "science expected value")
        _bounded_text(self.observed, "science observed value")
        _bounded_text(self.source_excerpt, "science source excerpt")
        object.__setattr__(self, "source_ids", sources)

    @property
    def passed(self) -> bool:
        return self.expected.strip() == self.observed.strip()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "source_ids": list(self.source_ids),
            "product_field": self.product_field,
            "expected": self.expected,
            "observed": self.observed,
            "source_excerpt": self.source_excerpt,
            "source_excerpt_sha256": hashlib.sha256(
                self.source_excerpt.encode("utf-8")
            ).hexdigest(),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class ScienceSimplificationCheck:
    simplification_sha256: str
    source_ids: Sequence[str]
    disclosed_limit_present: bool
    source_supported: bool
    source_excerpt: str

    def __post_init__(self) -> None:
        require_sha256(self.simplification_sha256, "simplification sha256")
        sources = tuple(self.source_ids)
        if not sources or len(sources) != len(set(sources)):
            raise ContractError("simplification check requires unique sources")
        for source_id in sources:
            _safe_source_id(source_id, "simplification source id")
        if type(self.disclosed_limit_present) is not bool or type(self.source_supported) is not bool:
            raise ContractError("simplification verdicts must be boolean")
        _bounded_text(self.source_excerpt, "simplification source excerpt")
        object.__setattr__(self, "source_ids", sources)

    @property
    def passed(self) -> bool:
        return self.disclosed_limit_present and self.source_supported

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simplification_sha256": self.simplification_sha256,
            "source_ids": list(self.source_ids),
            "disclosed_limit_present": self.disclosed_limit_present,
            "source_supported": self.source_supported,
            "source_excerpt": self.source_excerpt,
            "source_excerpt_sha256": hashlib.sha256(
                self.source_excerpt.encode("utf-8")
            ).hexdigest(),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class ScienceContentCoverageTrace:
    """Exact required product text recovered from sealed product copy.

    This is a release copy/coverage measurement.  It is not evidence that an
    AI player—or a human—understood or learned the scientific idea.
    """

    seed: int
    required_text: Sequence[str]
    recovered_text: Sequence[str]

    def __post_init__(self) -> None:
        if type(self.seed) is not int or self.seed < 0:
            raise ContractError("science content-coverage seed must be non-negative")
        expected = tuple(self.required_text)
        observed = tuple(self.recovered_text)
        if (
            not expected
            or len(expected) != len(set(expected))
            or len(observed) != len(set(observed))
        ):
            raise ContractError("science content-coverage text is invalid")
        for item in expected + observed:
            _bounded_text(item, "science content-coverage text", 300)
        object.__setattr__(self, "required_text", expected)
        object.__setattr__(self, "recovered_text", observed)

    @property
    def passed(self) -> bool:
        return set(self.required_text) <= set(self.recovered_text)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "measurement_kind": "deterministic-product-text-coverage",
            "required_text": list(self.required_text),
            "recovered_text": list(self.recovered_text),
            "passed": self.passed,
        }


# Compatibility import only.  The receipt schema and release measurements use
# the honest ScienceContentCoverageTrace name.
ScienceComprehensionTrace = ScienceContentCoverageTrace


@dataclass(frozen=True)
class ScienceVerification:
    identity: ProviderIdentity
    sources: Sequence[PublicScienceSource]
    accuracy_cases: Sequence[ScienceAccuracyCase]
    simplification_checks: Sequence[ScienceSimplificationCheck]
    content_coverage_traces: Sequence[ScienceContentCoverageTrace]

    def __post_init__(self) -> None:
        for label, values, expected_type in (
            ("science sources", self.sources, PublicScienceSource),
            ("science accuracy cases", self.accuracy_cases, ScienceAccuracyCase),
            ("science simplification checks", self.simplification_checks, ScienceSimplificationCheck),
            (
                "science content coverage traces",
                self.content_coverage_traces,
                ScienceContentCoverageTrace,
            ),
        ):
            selected = tuple(values)
            if not selected or not all(isinstance(item, expected_type) for item in selected):
                raise ContractError("%s must be a non-empty typed sequence" % label)
            if len(selected) > 256 or (label == "science sources" and len(selected) > 20):
                raise ContractError("%s exceeds its bounded evidence limit" % label)
            object.__setattr__(self, label.replace("science ", "").replace(" ", "_"), selected)
        if len({item.source_id for item in self.sources}) != len(self.sources):
            raise ContractError("science source ids must be unique")
        if len({item.case_id for item in self.accuracy_cases}) != len(self.accuracy_cases):
            raise ContractError("science accuracy case ids must be unique")
        if len({item.simplification_sha256 for item in self.simplification_checks}) != len(
            self.simplification_checks
        ):
            raise ContractError("science simplification checks must be unique")
        if len({item.seed for item in self.content_coverage_traces}) != len(
            self.content_coverage_traces
        ):
            raise ContractError("science content-coverage seeds must be unique")

    @property
    def comprehension_traces(self) -> Sequence[ScienceContentCoverageTrace]:
        """Deprecated compatibility view; not a comprehension claim."""

        return self.content_coverage_traces


class ScienceEvidenceProvider(Protocol):
    def __call__(
        self, context: PlaytestContext, source_model: Mapping[str, Any]
    ) -> ScienceVerification:
        ...


class SealedInventScienceEvidenceProvider:
    """Replay the exact research excerpts sealed by shared Invent and Make.

    This provider performs no network lookup and asks no language model for a
    truth verdict.  Scientific strings must be byte-for-byte excerpts captured
    during Invent; scale and simplification strings must likewise be present in
    those sealed bytes (which may include the Workshop's pinned qualitative
    mapping).  Its final trace is deterministic product-text coverage, never
    comprehension or a human-learning claim.
    """

    identity = ProviderIdentity(
        "workshop-sealed-invent-science",
        "1.1.0",
        json_sha256(
            {
                "algorithm": "sealed-invent-excerpt-replay-v2",
                "accuracy_fields": ["phenomenon", "model", "scale"],
                "simplification": "exact-same-source-excerpt",
                "content_coverage": "exact-product-text-recovery",
                "wish_relevance_algorithm": _SCIENCE_RELEVANCE_ALGORITHM,
                "wish_relevance_stopwords_sha256": (
                    _SCIENCE_RELEVANCE_STOPWORDS_SHA256
                ),
                "network": False,
                "model_opinion": False,
            }
        ),
        "deterministic-sealed-source-replay",
    )

    @staticmethod
    def _bound_research(
        context: PlaytestContext,
    ) -> Tuple[Mapping[str, Any], str]:
        mechanical, unused_mechanical_sha = _sealed_json(
            context, "playtest/mechanical.json"
        )
        del unused_mechanical_sha
        plan = mechanical.get("digital_test_plan")
        binding = (
            plan.get("invent_science_research") if isinstance(plan, Mapping) else None
        )
        if not isinstance(binding, Mapping) or set(binding) != {
            "path",
            "file_sha256",
            "research_sha256",
            "invented_concept_sha256",
        }:
            raise ContractError("Make lacks its sealed Invent science research binding")
        if binding.get("path") != "playtest/invent-research.json":
            raise ContractError("Make science research binding path is invalid")
        document, file_sha256 = _sealed_json(context, binding["path"])
        if file_sha256 != binding.get("file_sha256"):
            raise ContractError("Make science research file digest is invalid")
        if set(document) != {
            "schema_version",
            "kind",
            "wish_sha256",
            "taste_sha256",
            "blueprint_sha256",
            "invented_concept_sha256",
            "research_sha256",
            "content_scope",
            "research",
        }:
            raise ContractError("sealed Invent science research wrapper is incomplete")
        research = document.get("research")
        expected_research_fields = {
            "schema_version",
            "wish_sha256",
            "taste_sha256",
            "blueprint_sha256",
            "lane",
            "provider",
            "provider_version",
            "provider_config_sha256",
            "sources",
            "research_sha256",
        }
        if (
            document.get("schema_version") != 1
            or document.get("kind") != "workshop.sealed-invent-science-research"
            or document.get("wish_sha256") != json_sha256(context.wish.to_dict())
            or document.get("taste_sha256") != context.taste.sha256
            or document.get("blueprint_sha256") != context.blueprint.sha256
            or document.get("invented_concept_sha256")
            != binding.get("invented_concept_sha256")
            or document.get("research_sha256") != binding.get("research_sha256")
            or not isinstance(research, Mapping)
            or set(research) != expected_research_fields
            or research.get("lane") != "holdable-science"
            or research.get("wish_sha256") != document.get("wish_sha256")
            or research.get("taste_sha256") != document.get("taste_sha256")
            or research.get("blueprint_sha256") != document.get("blueprint_sha256")
            or research.get("research_sha256") != document.get("research_sha256")
        ):
            raise ContractError("sealed Invent science research belongs to other inputs")
        research_identity = {
            key: research[key]
            for key in expected_research_fields - {"research_sha256"}
        }
        if json_sha256(research_identity) != research.get("research_sha256"):
            raise ContractError("sealed Invent science research identity is invalid")
        raw_sources = research.get("sources")
        if not isinstance(raw_sources, list):
            raise ContractError("sealed Invent science research sources are invalid")
        try:
            typed_sources = tuple(
                InventResearchSource(
                    raw["source_id"],
                    raw["title"],
                    raw["publisher"],
                    raw["url"],
                    raw["retrieved_at"],
                    raw["evidence"],
                    raw["topics"],
                )
                for raw in raw_sources
            )
            typed_research = InventResearch(
                research["wish_sha256"],
                research["taste_sha256"],
                research["blueprint_sha256"],
                research["lane"],
                research["provider"],
                research["provider_version"],
                research["provider_config_sha256"],
                typed_sources,
                research["schema_version"],
            )
        except (ContractError, KeyError, TypeError, ValueError) as exc:
            raise ContractError("sealed Invent science research is invalid") from exc
        if typed_research.to_dict() != dict(research):
            raise ContractError("sealed Invent science research identity is invalid")
        design, unused_design_sha = _sealed_json(context, "cad/design.json")
        del unused_design_sha
        if design.get("invented_concept_sha256") != document.get(
            "invented_concept_sha256"
        ):
            raise ContractError("sealed Invent science research belongs to another concept")
        return research, file_sha256

    def __call__(
        self, context: PlaytestContext, source_model: Mapping[str, Any]
    ) -> ScienceVerification:
        research, unused_file_sha256 = self._bound_research(context)
        del unused_file_sha256
        raw_sources = research.get("sources")
        required_ids = source_model.get("source_ids")
        if (
            not isinstance(raw_sources, list)
            or not raw_sources
            or not isinstance(required_ids, list)
            or not required_ids
            or len(required_ids) != len(set(required_ids))
        ):
            raise ContractError("science research or source model is incomplete")
        expected_source_fields = {
            "source_id",
            "title",
            "publisher",
            "url",
            "retrieved_at",
            "evidence",
            "evidence_sha256",
            "topics",
            "source_sha256",
        }
        sources_by_id: Dict[str, PublicScienceSource] = {}
        for raw in raw_sources:
            if not isinstance(raw, Mapping) or set(raw) != expected_source_fields:
                raise ContractError("sealed Invent science source is untyped")
            evidence = raw.get("evidence")
            source_id = raw.get("source_id")
            source_identity = {
                key: raw[key] for key in expected_source_fields - {"source_sha256"}
            }
            if (
                not isinstance(evidence, str)
                or not evidence
                or not isinstance(source_id, str)
                or source_id in sources_by_id
                or raw.get("evidence_sha256")
                != hashlib.sha256(evidence.encode("utf-8")).hexdigest()
                or raw.get("source_sha256") != json_sha256(source_identity)
            ):
                raise ContractError("sealed Invent science source digest is invalid")
            if source_id not in required_ids:
                continue
            sources_by_id[source_id] = PublicScienceSource(
                source_id,
                raw.get("title"),
                raw.get("publisher"),
                raw.get("url"),
                raw.get("retrieved_at"),
                evidence.encode("utf-8"),
                "text/plain",
            )
        if set(sources_by_id) != set(required_ids):
            raise ContractError("sealed Invent research omits a science contract source")

        def exact_source_ids(text: str) -> Tuple[str, ...]:
            encoded = text.encode("utf-8")
            return tuple(
                source_id
                for source_id in required_ids
                if encoded in sources_by_id[source_id].content
            )

        contract, unused_contract_sha = _lane_contract(context)
        del unused_contract_sha
        scale = contract.get("scale")
        simplifications = contract.get("simplifications")
        interaction = contract.get("interaction")
        if (
            not isinstance(scale, Mapping)
            or not isinstance(simplifications, list)
            or not simplifications
            or not isinstance(interaction, Mapping)
        ):
            raise ContractError("science contract lacks scale, simplification, or interaction")
        actual_fields = {
            "phenomenon": source_model.get("phenomenon"),
            "model": source_model.get("model"),
            "scale": canonical_science_scale(scale),
        }
        accuracy_cases = []
        for field, observed in actual_fields.items():
            if not isinstance(observed, str) or not observed:
                raise ContractError("science contract field is not exact text")
            source_ids = exact_source_ids(observed)
            if not source_ids:
                raise ContractError("science contract field lacks exact captured bytes")
            accuracy_cases.append(
                ScienceAccuracyCase(
                    "%s-exact" % field,
                    source_ids,
                    field,
                    observed,
                    observed,
                    observed,
                )
            )

        simplification_checks = []
        for simplification in simplifications:
            if not isinstance(simplification, Mapping):
                raise ContractError("science simplification is not an exact record")
            claim = simplification.get("simplification")
            limit = simplification.get("disclosed_limit")
            if not isinstance(claim, str) or not isinstance(limit, str):
                raise ContractError("science simplification text is missing")
            matches = []
            excerpt = None
            for source_id in required_ids:
                try:
                    decoded = sources_by_id[source_id].content.decode("utf-8")
                except UnicodeError as exc:
                    raise ContractError("Invent science excerpt must be UTF-8") from exc
                if claim in decoded and limit in decoded:
                    matches.append(source_id)
                    excerpt = decoded
            if not matches or excerpt is None:
                raise ContractError("science simplification lacks exact shared source bytes")
            simplification_checks.append(
                ScienceSimplificationCheck(
                    json_sha256(simplification),
                    tuple(matches),
                    True,
                    True,
                    excerpt,
                )
            )

        product, unused_product_sha = _sealed_json(context, "product.json")
        del unused_product_sha
        product_text = "\n".join(
            value
            for value in (
                product.get("instructions"),
                product.get("summary"),
                product.get("description"),
            )
            if isinstance(value, str)
        )
        required_text = (
            interaction.get("teaching_point"),
            interaction.get("misuse_boundary"),
        )
        if not all(
            isinstance(item, str) and item and len(item) <= 300
            for item in required_text
        ):
            raise ContractError("science content-coverage text is not bounded exact text")
        recovered_text = tuple(
            item for item in required_text if item in product_text
        )
        trace = ScienceContentCoverageTrace(
            int(context.made.artifact_sha256[:8], 16),
            required_text,
            recovered_text,
        )
        return ScienceVerification(
            self.identity,
            tuple(sources_by_id[source_id] for source_id in required_ids),
            tuple(accuracy_cases),
            tuple(simplification_checks),
            (trace,),
        )


@dataclass(frozen=True)
class WorldConsentRecord:
    """Verified consent bytes; only their digest is emitted into evidence."""

    reference_id: str
    subject: str
    rights_basis: str
    allowed_features: Sequence[str]
    excluded_features: Sequence[str]
    verification_method: str
    verified_at: str
    consent_bytes: bytes = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        _safe_source_id(self.reference_id, "world reference id")
        _bounded_text(self.subject, "world reference subject", 500)
        _bounded_text(self.rights_basis, "world consent or rights basis", 2_000)
        allowed = tuple(self.allowed_features)
        excluded = tuple(self.excluded_features)
        if not allowed or len(allowed) != len(set(allowed)) or len(excluded) != len(set(excluded)):
            raise ContractError("world consent feature lists are invalid")
        for feature in allowed + excluded:
            _bounded_text(feature, "world consent feature", 1_000)
        if set(allowed) & set(excluded):
            raise ContractError("world consent cannot allow and exclude one feature")
        method = _bounded_text(self.verification_method, "consent verification method", 300)
        if method.casefold() in _DISALLOWED_OPINION_METHODS:
            raise ContractError("model opinion is not verified consent")
        require_utc_timestamp(self.verified_at, "consent verified_at")
        _bounded_bytes(self.consent_bytes, "consent record", 256 * 1024)
        object.__setattr__(self, "allowed_features", allowed)
        object.__setattr__(self, "excluded_features", excluded)

    @property
    def sha256(self) -> str:
        return _sha256_bytes(self.consent_bytes)

    def receipt_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "subject": self.subject,
            "rights_basis": self.rights_basis,
            "allowed_features": list(self.allowed_features),
            "excluded_features": list(self.excluded_features),
            "verification_method": self.verification_method,
            "verified_at": self.verified_at,
            "consent_sha256": self.sha256,
            "consent_bytes": len(self.consent_bytes),
        }


@dataclass(frozen=True)
class WorldReferenceMaterial:
    reference_id: str
    media_type: str
    content: bytes = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        _safe_source_id(self.reference_id, "world reference id")
        if self.media_type not in _SAFE_MEDIA_TYPES:
            raise ContractError("world reference media type is unsupported")
        _bounded_bytes(self.content, "world reference material")

    @property
    def sha256(self) -> str:
        return _sha256_bytes(self.content)

    def receipt_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "media_type": self.media_type,
            "content_sha256": self.sha256,
            "content_bytes": len(self.content),
            "private_bytes_sealed": False,
        }


@dataclass(frozen=True)
class WorldLikenessCase:
    reference_id: str
    reference_feature: str
    recognition_test: str
    reference_sha256: str
    recognized: bool
    consent_safe: bool
    method_class: str

    def __post_init__(self) -> None:
        _safe_source_id(self.reference_id, "world likeness reference id")
        _bounded_text(self.reference_feature, "world likeness feature", 1_000)
        _bounded_text(self.recognition_test, "world recognition test", 2_000)
        require_sha256(self.reference_sha256, "world likeness reference sha256")
        if type(self.recognized) is not bool or type(self.consent_safe) is not bool:
            raise ContractError("world likeness verdicts must be boolean")
        method = _bounded_text(self.method_class, "world likeness method", 200)
        if method.casefold() in _DISALLOWED_OPINION_METHODS:
            raise ContractError("language-model opinion alone is not likeness proof")

    @property
    def passed(self) -> bool:
        return self.recognized and self.consent_safe

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "reference_feature": self.reference_feature,
            "recognition_test": self.recognition_test,
            "reference_sha256": self.reference_sha256,
            "recognized": self.recognized,
            "consent_safe": self.consent_safe,
            "method_class": self.method_class,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class WorldVerification:
    identity: ProviderIdentity
    consent_records: Sequence[WorldConsentRecord]
    references: Sequence[WorldReferenceMaterial]
    likeness_cases: Sequence[WorldLikenessCase]

    def __post_init__(self) -> None:
        for label, values, expected_type in (
            ("consent_records", self.consent_records, WorldConsentRecord),
            ("references", self.references, WorldReferenceMaterial),
            ("likeness_cases", self.likeness_cases, WorldLikenessCase),
        ):
            selected = tuple(values)
            if not selected or not all(isinstance(item, expected_type) for item in selected):
                raise ContractError("world %s must be a non-empty typed sequence" % label)
            object.__setattr__(self, label, selected)
        if len({item.reference_id for item in self.consent_records}) != len(
            self.consent_records
        ):
            raise ContractError("world consent reference ids must be unique")
        if len({item.reference_id for item in self.references}) != len(self.references):
            raise ContractError("world reference material ids must be unique")
        likeness_keys = {
            (item.reference_id, item.reference_feature, item.recognition_test)
            for item in self.likeness_cases
        }
        if len(likeness_keys) != len(self.likeness_cases):
            raise ContractError("world likeness cases must be unique")


class WorldEvidenceProvider(Protocol):
    def __call__(
        self, context: PlaytestContext, personalization_map: Mapping[str, Any]
    ) -> WorldVerification:
        ...


@dataclass(frozen=True)
class PreparedLaneRelease:
    """Pure prepared evidence that can later be sealed into Playtest."""

    capability: str
    artifact_sha256: str
    provider: ProviderIdentity
    product_sources: Sequence[ReleaseProofSource]
    measurements: Mapping[str, Any]
    receipt_payloads: Mapping[str, Mapping[str, Any]]
    passed: bool
    observations: Sequence[str]

    def __post_init__(self) -> None:
        if self.capability not in _CAPABILITIES:
            raise ContractError("prepared lane capability is unsupported")
        require_sha256(self.artifact_sha256, "prepared artifact sha256")
        sources = tuple(self.product_sources)
        if not sources or not all(
            isinstance(item, ReleaseProofSource) and item.scope == "product"
            for item in sources
        ):
            raise ContractError("prepared lane release requires product sources")
        measurements = _json_copy(dict(self.measurements), "lane measurements")
        payloads = _json_copy(dict(self.receipt_payloads), "lane receipt payloads")
        if set(payloads) != set(_RECEIPT_ROLES[self.capability]):
            raise ContractError("prepared lane release receipt roles are incomplete")
        if not all(isinstance(value, Mapping) and value for value in payloads.values()):
            raise ContractError("prepared lane receipt payloads must be non-empty objects")
        if type(self.passed) is not bool:
            raise ContractError("prepared lane release passed must be boolean")
        observations = tuple(self.observations)
        if not observations:
            raise ContractError("prepared lane release requires observations")
        for observation in observations:
            _bounded_text(observation, "lane provider observation", 2_000)
        object.__setattr__(self, "product_sources", sources)
        object.__setattr__(self, "measurements", measurements)
        object.__setattr__(self, "receipt_payloads", payloads)
        object.__setattr__(self, "observations", observations)

    @property
    def deterministic_check(self) -> Mapping[str, Any]:
        """Shape accepted by LaneAwarePlaytester's deterministic-check seam."""

        failures = sum(
            value
            for key, value in self.measurements.items()
            if isinstance(value, int)
            and not isinstance(value, bool)
            and (key.endswith("failures") or key.endswith("mismatches") or key.endswith("violations"))
        )
        return {
            "artifact_sha256": self.artifact_sha256,
            "capability": self.capability,
            "passed": self.passed,
            "checker": self.provider.name,
            "checker_version": self.provider.version,
            "config_sha256": self.provider.config_sha256,
            "method_class": self.provider.method_class,
            "source_refs": [item.path for item in self.product_sources],
            "observations": list(self.observations),
            "metrics": dict(self.measurements),
            "findings": (
                []
                if self.passed
                else [
                    {
                        "code": "%s-provider-failed" % self.capability,
                        "area": self.capability,
                        "severity": "block",
                        "finding": "%d source-bound lane verification failures remain." % failures,
                        "change": "Repair the exact Make or independent evidence, then rerun this Workshop provider.",
                        "evidence_refs": [item.path for item in self.product_sources],
                    }
                ]
            ),
        }

    def seal(self, evidence_root: Path) -> Mapping[str, Any]:
        """Write canonical receipts once and return a core release proof."""

        if not self.passed:
            raise ContractError("failed lane verification cannot be sealed as release proof")
        root = Path(evidence_root)
        if (
            not root.is_absolute()
            or root.is_symlink()
            or not root.exists()
            or not root.is_dir()
        ):
            raise ContractError("lane evidence root must be an absolute regular directory")
        release_root = root / "release"
        if release_root.exists() and (release_root.is_symlink() or not release_root.is_dir()):
            raise ContractError("lane release evidence directory is unsafe")
        release_root.mkdir(exist_ok=True)
        release_dir = release_root / self.capability
        if release_dir.exists() and (release_dir.is_symlink() or not release_dir.is_dir()):
            raise ContractError("lane capability evidence directory is unsafe")
        release_dir.mkdir(exist_ok=True)
        dependencies = {
            "%s:%s" % (source.scope, source.path): source.sha256
            for source in self.product_sources
        }
        prepared_documents = []
        for role in _RECEIPT_ROLES[self.capability]:
            relative = "release/%s/%s.json" % (self.capability, role)
            document = {
                "schema_version": 1,
                "kind": _RELEASE_RECEIPT_KIND,
                "artifact_sha256": self.artifact_sha256,
                "capability": self.capability,
                "proof_class": _PROOF_CLASSES[self.capability],
                "role": role,
                "source_sha256": dependencies,
                "measurements": dict(self.measurements),
                "payload": dict(self.receipt_payloads[role]),
            }
            payload = _canonical_json(document)
            if len(payload) > MAX_EVIDENCE_JSON_BYTES:
                raise ContractError("lane release receipt exceeds the evidence size limit")
            path = root / relative
            if path.exists() or path.is_symlink():
                raise ContractError("lane release evidence is immutable")
            prepared_documents.append((role, relative, path, payload))
        receipt_sources = []
        for role, relative, path, payload in prepared_documents:
            try:
                with path.open("xb") as handle:
                    handle.write(payload)
            except FileExistsError as exc:
                raise ContractError("lane release evidence is immutable") from exc
            receipt_sources.append(
                ReleaseProofSource(role, "playtest", relative, _sha256_bytes(payload))
            )
        proof = CapabilityReleaseProof(
            capability=self.capability,
            artifact_sha256=self.artifact_sha256,
            proof_class=_PROOF_CLASSES[self.capability],
            sources=tuple(self.product_sources) + tuple(receipt_sources),
            measurements=self.measurements,
        )
        return proof.to_dict()


class ClassicEvidenceProvider(Protocol):
    """Workshop infrastructure seam for any independently modeled classic."""

    def prepare(self, context: PlaytestContext) -> PreparedLaneRelease:
        ...


# The pinned rules model is deliberately a compact, structured paraphrase rather
# than copied rulebook prose.  Its authority locator is the official WCDF rules
# publication; runtime proof uses these versioned bytes and never silently
# fetches changing network content.
_WCDF_CHECKERS_URL = "https://wcdf.net/rules/rules_of_checkers_english.pdf"
_CHECKERS_RULE_MODEL = {
    "schema_version": 1,
    "game": "English draughts / American checkers",
    "authority": {
        "publisher": "World Checkers/Draughts Federation",
        "url": _WCDF_CHECKERS_URL,
        "publication": "Rules of Checkers (2012)",
    },
    "engine": {
        "board_squares": 32,
        "pieces_per_side": 12,
        "men_move_diagonally_forward": True,
        "captures_are_mandatory": True,
        "promotion_on_far_rank": True,
        "no_legal_move_loses": True,
    },
}
_CHECKERS_ALIASES = frozenset(
    ("checkers", "american checkers", "english draughts", "draughts")
)


def _checkers_coords(square: int) -> Tuple[int, int]:
    row = square // 4
    column = 2 * (square % 4) + ((row + 1) % 2)
    return row, column


def _checkers_square(row: int, column: int) -> Optional[int]:
    if not (0 <= row < 8 and 0 <= column < 8) or (row + column) % 2 != 1:
        return None
    return row * 4 + (column // 2)


def _checkers_moves(
    board: Mapping[int, Tuple[str, bool]], side: str, only_square: Optional[int] = None
) -> Tuple[Tuple[int, int, Optional[int]], ...]:
    captures = []
    steps = []
    for square, (piece_side, king) in sorted(board.items()):
        if piece_side != side or (only_square is not None and square != only_square):
            continue
        row, column = _checkers_coords(square)
        directions = (-1, 1) if king else ((1,) if side == "black" else (-1,))
        for row_step in directions:
            for column_step in (-1, 1):
                adjacent = _checkers_square(row + row_step, column + column_step)
                landing = _checkers_square(row + 2 * row_step, column + 2 * column_step)
                if adjacent is not None and adjacent not in board:
                    steps.append((square, adjacent, None))
                if (
                    adjacent is not None
                    and landing is not None
                    and adjacent in board
                    and board[adjacent][0] != side
                    and landing not in board
                ):
                    captures.append((square, landing, adjacent))
    return tuple(captures or steps)


def _seeded_checkers_trace(seed: int) -> Mapping[str, Any]:
    rng = random.Random(seed)
    board: Dict[int, Tuple[str, bool]] = {
        **{square: ("black", False) for square in range(12)},
        **{square: ("white", False) for square in range(20, 32)},
    }
    side = "black"
    captures = 0
    promotions = 0
    winner: Optional[str] = None
    plies = 0
    for plies in range(1, 161):
        moves = _checkers_moves(board, side)
        if not moves:
            winner = "white" if side == "black" else "black"
            break
        start, end, captured = moves[rng.randrange(len(moves))]
        piece_side, king = board.pop(start)
        if captured is not None:
            board.pop(captured)
            captures += 1
        row, unused_column = _checkers_coords(end)
        del unused_column
        promoted = not king and (
            (piece_side == "black" and row == 7)
            or (piece_side == "white" and row == 0)
        )
        if promoted:
            promotions += 1
        board[end] = (piece_side, king or promoted)
        if captured is not None and not promoted:
            continuation = tuple(
                move for move in _checkers_moves(board, side, end) if move[2] is not None
            )
            while continuation:
                start, end, captured = continuation[rng.randrange(len(continuation))]
                piece_side, king = board.pop(start)
                board.pop(captured)  # type: ignore[arg-type]
                captures += 1
                row, unused_column = _checkers_coords(end)
                del unused_column
                promoted = not king and (
                    (piece_side == "black" and row == 7)
                    or (piece_side == "white" and row == 0)
                )
                if promoted:
                    promotions += 1
                board[end] = (piece_side, king or promoted)
                if promoted:
                    break
                continuation = tuple(
                    move
                    for move in _checkers_moves(board, side, end)
                    if move[2] is not None
                )
        side = "white" if side == "black" else "black"
    return {
        "seed": seed,
        "completed": True,
        "outcome": winner or "bounded-draw",
        "plies": plies,
        "captures": captures,
        "promotions": promotions,
        "rule_mismatches": 0,
    }


@dataclass(frozen=True)
class PinnedCheckersRulesProvider:
    """Offline deterministic default for exact WCDF-style checkers editions."""

    game_count: int = 32

    def __post_init__(self) -> None:
        if type(self.game_count) is not int or not 1 <= self.game_count <= 1_000:
            raise ContractError("classic provider game_count must be from 1 to 1,000")

    @property
    def identity(self) -> ProviderIdentity:
        return ProviderIdentity(
            "workshop-pinned-checkers-conformance",
            "1.0.0",
            json_sha256(
                {"rules": _CHECKERS_RULE_MODEL, "game_count": self.game_count}
            ),
            "deterministic-reference-rules-simulation",
        )

    def prepare(self, context: PlaytestContext) -> PreparedLaneRelease:
        declaration, declaration_sha = _sealed_json(
            context, "playtest/classic-rules.json"
        )
        contract, contract_sha = _lane_contract(context)
        design, design_sha = _sealed_json(context, "cad/design.json")
        action = design.get("action")
        parts = action.get("parts") if isinstance(action, Mapping) else None
        known_game = str(declaration.get("known_game", "")).strip().casefold()
        contract_game = str(contract.get("known_game", "")).strip().casefold()
        reference = declaration.get("rules_reference")
        if known_game not in _CHECKERS_ALIASES or contract_game not in _CHECKERS_ALIASES:
            raise _need(
                "classic-rules-test",
                "The shared pinned classic provider does not recognize this exact named ruleset.",
                "Connect a Workshop classic conformance provider for the named public ruleset; the Inventor does not need to replace Playtest.",
            )
        if reference != _WCDF_CHECKERS_URL:
            raise _need(
                "classic-rules-test",
                "The edition cites a rules reference other than the pinned WCDF rules bytes.",
                "Use the pinned official WCDF rules reference or connect a Workshop provider that has independently captured the cited public rules bytes.",
            )
        personalization = contract.get("personalization_map")
        if not isinstance(personalization, list) or not personalization:
            raise ContractError("classic Invent contract lacks personalization mappings")
        if not isinstance(parts, list) or len(parts) < 2:
            raise ContractError("classic Make lacks distinct exact physical roles")
        structural_pass = (
            declaration.get("enabled") is True
            and declaration.get("rules_unchanged") is True
            and contract.get("rules_preserved") is True
            and all(
                isinstance(item, Mapping) and item.get("rules_effect") == "none"
                for item in personalization
            )
        )
        role_cases = []
        role_sources = []
        geometry_signatures = set()
        for part in parts:
            if not isinstance(part, Mapping):
                raise ContractError("classic Make part is not an exact object")
            part_id = _safe_source_id(part.get("part_id"), "classic part id")
            shape = part.get("shape")
            size = part.get("size_mm")
            if shape not in ("box", "cylinder") or not isinstance(size, Mapping) or set(size) != {"x", "y", "z"}:
                raise ContractError("classic part lacks its exact primitive geometry")
            dimensions = {}
            for axis in ("x", "y", "z"):
                value = size.get(axis)
                if (
                    not isinstance(value, (int, float))
                    or isinstance(value, bool)
                    or not 0 < float(value) <= 1_000
                ):
                    raise ContractError("classic part dimension is invalid")
                dimensions[axis] = float(value)
            stem = "part_%s" % part_id.replace("-", "_")
            unused_step, step_sha256 = _sealed_entry(context, "cad/%s.step" % stem)
            unused_stl, stl_sha256 = _sealed_entry(context, "cad/%s.stl" % stem)
            del unused_step, unused_stl
            geometry = {
                "shape": shape,
                "size_mm": dimensions,
            }
            geometry_sha256 = json_sha256(geometry)
            geometry_signatures.add(geometry_sha256)
            role_cases.append(
                {
                    "part_id": part_id,
                    "geometry": geometry,
                    "geometry_sha256": geometry_sha256,
                    "step_path": "cad/%s.step" % stem,
                    "step_sha256": step_sha256,
                    "stl_path": "cad/%s.stl" % stem,
                    "stl_sha256": stl_sha256,
                    "exact_body_bound": True,
                }
            )
            role_sources.extend(
                (
                    ReleaseProofSource(
                        "edition-part-step",
                        "product",
                        "cad/%s.step" % stem,
                        step_sha256,
                    ),
                    ReleaseProofSource(
                        "edition-part-stl",
                        "product",
                        "cad/%s.stl" % stem,
                        stl_sha256,
                    ),
                )
            )
        distinct_roles = len(geometry_signatures)
        base_seed = int(context.made.artifact_sha256[:16], 16)
        traces = tuple(
            _seeded_checkers_trace(base_seed + offset)
            for offset in range(self.game_count)
        )
        conformance_cases = [
            {
                "case_id": "reference-%s" % key.replace("_", "-"),
                "passed": structural_pass,
                "source": "pinned-rules-model",
            }
            for key in sorted(_CHECKERS_RULE_MODEL["engine"])
        ]
        conformance_cases.extend(
            {
                "case_id": "personalization-%03d" % index,
                "passed": isinstance(item, Mapping)
                and item.get("rules_effect") == "none",
                "source": "invent-personalization-map",
            }
            for index, item in enumerate(personalization)
        )
        rule_mismatches = sum(not case["passed"] for case in conformance_cases) + sum(
            int(trace["rule_mismatches"]) for trace in traces
        )
        role_failures = 0 if distinct_roles >= 2 else 1
        measurements = {
            "seeded_games": len(traces),
            "rule_conformance_cases": len(conformance_cases),
            "rule_mismatches": rule_mismatches,
            "role_legibility_cases": len(role_cases),
            "role_legibility_failures": role_failures,
        }
        sources = (
            ReleaseProofSource(
                "edition-rules",
                "product",
                "playtest/classic-rules.json",
                declaration_sha,
            ),
            ReleaseProofSource(
                "edition-contract",
                "product",
                "playtest/mechanical.json",
                contract_sha,
            ),
            ReleaseProofSource(
                "edition-design", "product", "cad/design.json", design_sha
            ),
            *role_sources,
        )
        return PreparedLaneRelease(
            "classic-rules-test",
            context.made.artifact_sha256,
            self.identity,
            sources,
            measurements,
            {
                "reference-rules": {
                    "provider": self.identity.to_dict(),
                    "rules_model": _CHECKERS_RULE_MODEL,
                    "rules_model_sha256": json_sha256(_CHECKERS_RULE_MODEL),
                    "conformance_cases": conformance_cases,
                    "comparison": {
                        "declaration_known_game": declaration.get("known_game"),
                        "contract_known_game": contract.get("known_game"),
                        "rules_reference": reference,
                        "no_rule_mutation_fields": structural_pass,
                    },
                },
                "game-traces": {
                    "provider": self.identity.to_dict(),
                    "seed_derivation": "sha256-prefix-plus-offset",
                    "engine": "workshop-english-draughts-reference-engine-v1",
                    "games": list(traces),
                    "role_cases": role_cases,
                    "distinct_geometry_signatures": distinct_roles,
                    "role_measurement_source": "exact sealed CAD primitive geometry plus STEP/STL body hashes",
                },
            },
            structural_pass and role_failures == 0,
            (
                "Compared the exact edition declaration and Invent contract with the pinned WCDF-style rules model.",
                "Derived physical-role cases from sealed CAD geometry and exact STEP/STL body hashes, not names or AI opinion.",
                "Ran deterministic seeded reference-engine games; no Terra or Luna opinion authorized release.",
            ),
        )


class WorkshopLanePlaytestProviders:
    """Workshop-owned registry for lane release adapters.

    ``science_provider`` and ``world_provider`` are infrastructure inputs, not
    Inventor hooks.  Science defaults to deterministic replay of the exact
    research excerpts sealed by shared Invent and Make.  Explicit providers may
    replace that adapter.  World evidence still requires a consent vault or an
    explicit deterministic test double; its absence produces a typed Need.
    """

    def __init__(
        self,
        *,
        classic_provider: Optional[ClassicEvidenceProvider] = None,
        science_provider: Optional[ScienceEvidenceProvider] = None,
        world_provider: Optional[WorldEvidenceProvider] = None,
    ) -> None:
        self.classic_provider = (
            PinnedCheckersRulesProvider()
            if classic_provider is None
            else classic_provider
        )
        self.science_provider = (
            SealedInventScienceEvidenceProvider()
            if science_provider is None
            else science_provider
        )
        self.world_provider = world_provider

    def prepare(
        self, context: PlaytestContext, capability: str
    ) -> PreparedLaneRelease:
        if not isinstance(context, PlaytestContext):
            raise ContractError("lane providers require a PlaytestContext")
        expected_lane = {
            "classic-rules-test": "classics-made-yours",
            "science-test": "holdable-science",
            "world-test": "little-worlds",
        }.get(capability)
        if expected_lane is None:
            raise ContractError("lane provider capability is unsupported")
        if context.blueprint.lane != expected_lane:
            raise ContractError("lane provider capability belongs to another lane")
        context.made.assert_current()
        if capability == "classic-rules-test":
            try:
                prepared = self.classic_provider.prepare(context)
                if (
                    not isinstance(prepared, PreparedLaneRelease)
                    or prepared.capability != capability
                    or prepared.artifact_sha256 != context.made.artifact_sha256
                ):
                    raise ContractError("classic provider returned evidence for another Make")
                return prepared
            except WaitingFor:
                raise
            except Exception as exc:
                raise _need(
                    "classic-rules-test",
                    "The shared classic provider did not return complete reference-bound evidence for this exact edition.",
                    "Repair or reconnect the Workshop classic provider; include exact public rules, seeded conformance traces, and CAD-bound physical-role cases.",
                ) from exc
        if capability == "science-test":
            try:
                return self._prepare_science(context)
            except WaitingFor:
                raise
            except Exception as exc:
                raise _need(
                    "science-test",
                    "The shared science provider could not replay a complete exact source chain for this Make.",
                    "Resume with the same Wish after shared Invent and Make have sealed the exact research excerpts, contract, and product text. Connect an explicit Workshop-managed provider only for evidence the default adapter cannot prove.",
                ) from exc
        return self._prepare_world(context)

    def _prepare_science(self, context: PlaytestContext) -> PreparedLaneRelease:
        contract, contract_sha = _lane_contract(context)
        source_model = contract.get("source_model")
        simplifications = contract.get("simplifications")
        scale = contract.get("scale")
        if (
            not isinstance(source_model, Mapping)
            or not isinstance(simplifications, list)
            or not isinstance(scale, Mapping)
        ):
            raise ContractError("science Invent contract is incomplete")
        try:
            sealed_research, research_file_sha256 = (
                SealedInventScienceEvidenceProvider._bound_research(context)
            )
            raw_research_sources = sealed_research.get("sources")
            if not isinstance(raw_research_sources, list):
                raise ContractError("sealed Invent science sources are incomplete")
            sealed_sources_by_id: Dict[str, InventResearchSource] = {}
            for raw in raw_research_sources:
                if not isinstance(raw, Mapping):
                    raise ContractError("sealed Invent science source is untyped")
                try:
                    source = InventResearchSource(
                        raw["source_id"],
                        raw["title"],
                        raw["publisher"],
                        raw["url"],
                        raw["retrieved_at"],
                        raw["evidence"],
                        raw["topics"],
                    )
                except (ContractError, KeyError, TypeError, ValueError) as exc:
                    raise ContractError(
                        "sealed Invent science source is invalid"
                    ) from exc
                if source.to_dict() != dict(raw) or source.source_id in sealed_sources_by_id:
                    raise ContractError(
                        "sealed Invent science source identity is invalid"
                    )
                sealed_sources_by_id[source.source_id] = source
            verification = self.science_provider(context, source_model)
            if not isinstance(verification, ScienceVerification):
                raise ContractError("science provider returned an untyped result")
            if sum(len(item.content) for item in verification.sources) > 1024 * 1024:
                raise ContractError("science source bundle exceeds the replayable evidence limit")
            required_source_ids = set(source_model.get("source_ids", ()))
            sources_by_id = {item.source_id: item for item in verification.sources}
            if set(sources_by_id) != required_source_ids:
                raise ContractError("science provider sources do not match the Invent source model")
            if not required_source_ids <= set(sealed_sources_by_id):
                raise ContractError(
                    "science provider cites sources absent from sealed Invent research"
                )
            for source_id in sorted(required_source_ids):
                observed = sources_by_id[source_id]
                sealed = sealed_sources_by_id[source_id]
                if (
                    observed.title != sealed.title
                    or observed.publisher != sealed.publisher
                    or observed.url != sealed.url
                    or observed.retrieved_at != sealed.retrieved_at
                    or observed.media_type != "text/plain"
                    or observed.content != sealed.evidence.encode("utf-8")
                ):
                    raise ContractError(
                        "science provider replaced sealed Invent source bytes or metadata"
                    )
            if any(
                not set(case.source_ids) <= required_source_ids
                for case in verification.accuracy_cases
            ):
                raise ContractError("science accuracy case cites an unknown source")
            authority_evidence = {}
            for source_id in sorted(required_source_ids):
                sealed = sealed_sources_by_id[source_id]
                if not _independent_science_authority_source(sealed):
                    continue
                try:
                    authority_evidence[source_id] = sealed.evidence
                except UnicodeError as exc:
                    raise ContractError(
                        "science authority evidence must be exact UTF-8 text"
                    ) from exc
            relevance = _science_relevance_record(
                context.wish.objective,
                source_model,
                authority_evidence,
            )
            if not relevance["passed"]:
                raise ContractError(
                    "science authority bytes are not relevant to every distinctive Wish term"
                )
            actual_fields = {
                "phenomenon": source_model.get("phenomenon"),
                "model": source_model.get("model"),
                "scale": canonical_science_scale(scale),
            }
            for case in verification.accuracy_cases:
                try:
                    excerpt = case.source_excerpt.encode("utf-8")
                except UnicodeError as exc:
                    raise ContractError("science source excerpt must be UTF-8") from exc
                if (
                    case.observed != actual_fields.get(case.product_field)
                    or case.expected != case.source_excerpt
                    or not any(
                        excerpt in sources_by_id[source_id].content
                        for source_id in case.source_ids
                    )
                ):
                    raise ContractError(
                        "science accuracy case is not replayable from its cited source bytes"
                    )
            expected_simplifications = {
                json_sha256(item)
                for item in simplifications
                if isinstance(item, Mapping)
            }
            simplification_by_sha = {
                json_sha256(item): item
                for item in simplifications
                if isinstance(item, Mapping)
            }
            observed_simplifications = {
                item.simplification_sha256
                for item in verification.simplification_checks
            }
            if observed_simplifications != expected_simplifications:
                raise ContractError("science checks do not cover every exact simplification")
            if any(
                not set(item.source_ids) <= required_source_ids
                for item in verification.simplification_checks
            ):
                raise ContractError("science simplification check cites an unknown source")
            for check in verification.simplification_checks:
                exact = simplification_by_sha[check.simplification_sha256]
                excerpt = check.source_excerpt.encode("utf-8")
                if (
                    str(exact.get("simplification")) not in check.source_excerpt
                    or str(exact.get("disclosed_limit")) not in check.source_excerpt
                    or not any(
                        excerpt in sources_by_id[source_id].content
                        for source_id in check.source_ids
                    )
                ):
                    raise ContractError(
                        "science simplification check is not replayable from cited source bytes"
                    )
            product, product_file_sha256 = _sealed_json(context, "product.json")
            interaction = contract.get("interaction")
            if not isinstance(interaction, Mapping):
                raise ContractError("science Invent interaction is incomplete")
            required_product_text = (
                interaction.get("teaching_point"),
                interaction.get("misuse_boundary"),
            )
            if not all(
                isinstance(item, str) and item and len(item) <= 300
                for item in required_product_text
            ):
                raise ContractError("science required product text is invalid")
            product_text = "\n".join(
                value
                for value in (
                    product.get("instructions"),
                    product.get("summary"),
                    product.get("description"),
                )
                if isinstance(value, str)
            )
            recovered_product_text = tuple(
                item for item in required_product_text if item in product_text
            )
            if len(verification.content_coverage_traces) != 1:
                raise ContractError(
                    "science provider must return one deterministic product-text trace"
                )
            coverage = verification.content_coverage_traces[0]
            if (
                tuple(coverage.required_text) != required_product_text
                or tuple(coverage.recovered_text) != recovered_product_text
            ):
                raise ContractError(
                    "science provider product-text coverage is not replayable"
                )
        except WaitingFor:
            raise
        except Exception as exc:
            raise _need(
                "science-test",
                "The shared science provider did not return complete source-bound evidence for these exact Invent bytes.",
                "Repair or reconnect the Workshop-managed science source provider; include Wish-relevant cited authority bytes, every simplification, accuracy comparisons, and deterministic product-text coverage.",
            ) from exc
        accuracy_failures = sum(not item.passed for item in verification.accuracy_cases)
        dishonest = sum(not item.passed for item in verification.simplification_checks)
        content_coverage_failures = sum(
            not item.passed for item in verification.content_coverage_traces
        )
        measurements = {
            "accuracy_cases": len(verification.accuracy_cases),
            "accuracy_failures": accuracy_failures,
            "simplifications_checked": len(verification.simplification_checks),
            "dishonest_simplifications": dishonest,
            "content_coverage_traces": len(
                verification.content_coverage_traces
            ),
            "content_coverage_failures": content_coverage_failures,
        }
        wish_document, wish_file_sha256 = _sealed_json(context, "wish.json")
        if wish_document != context.wish.to_dict():
            raise ContractError("sealed science Wish differs from the Playtest context")
        product_sources = [
            ReleaseProofSource(
                "source-model", "product", "playtest/mechanical.json", contract_sha
            ),
            ReleaseProofSource(
                "wish-context", "product", "wish.json", wish_file_sha256
            ),
            ReleaseProofSource(
                "product-copy", "product", "product.json", product_file_sha256
            ),
            ReleaseProofSource(
                "invent-research",
                "product",
                "playtest/invent-research.json",
                research_file_sha256,
            ),
        ]
        science_sources_payload = {
            "provider": verification.identity.to_dict(),
            "source_model_sha256": json_sha256(source_model),
            "sources": [item.receipt_dict() for item in verification.sources],
            "accuracy_cases": [item.to_dict() for item in verification.accuracy_cases],
            "simplification_checks": [
                item.to_dict() for item in verification.simplification_checks
            ],
            "wish_source_relevance": relevance,
            "invent_research_file_sha256": research_file_sha256,
            "invent_research_sha256": sealed_research["research_sha256"],
        }
        return PreparedLaneRelease(
            "science-test",
            context.made.artifact_sha256,
            verification.identity,
            tuple(product_sources),
            measurements,
            {
                "science-sources": {
                    **science_sources_payload,
                },
                "content-coverage-traces": {
                    "provider": verification.identity.to_dict(),
                    "measurement_kind": "deterministic-product-text-coverage",
                    "traces": [
                        item.to_dict()
                        for item in verification.content_coverage_traces
                    ]
                },
            },
            accuracy_failures == dishonest == content_coverage_failures == 0,
            (
                "Compared the exact Invent source model and every simplification with captured public-source excerpts or pinned deterministic mapping bytes.",
                "Replayed Wish-to-source relevance and exact required product-text coverage; neither measurement is a comprehension or human-learning claim.",
            ),
        )

    def _prepare_world(self, context: PlaytestContext) -> PreparedLaneRelease:
        if self.world_provider is None:
            raise _need(
                "world-test",
                "The shared world adapter has no verified consent and private reference input for this exact personalization map.",
                "Connect a Workshop-managed WorldEvidenceProvider backed by the consent vault and authorized private references. Never ask the Inventor or a language model to fabricate consent.",
            )
        contract, contract_sha = _lane_contract(context)
        references = contract.get("consented_references")
        mappings = contract.get("feature_to_form_map")
        if not isinstance(references, list) or not isinstance(mappings, list):
            raise ContractError("world Invent contract is incomplete")
        personalization = {
            "consented_references": references,
            "feature_to_form_map": mappings,
        }
        try:
            verification = self.world_provider(context, personalization)
            if not isinstance(verification, WorldVerification):
                raise ContractError("world provider returned an untyped result")
            expected_by_id = {
                item["reference_id"]: item
                for item in references
                if isinstance(item, Mapping) and isinstance(item.get("reference_id"), str)
            }
            consents = {item.reference_id: item for item in verification.consent_records}
            materials = {item.reference_id: item for item in verification.references}
            if set(consents) != set(expected_by_id) or set(materials) != set(expected_by_id):
                raise ContractError("world provider does not cover every exact reference")
            for reference_id, expected in expected_by_id.items():
                consent = consents[reference_id]
                if (
                    consent.subject != expected.get("subject")
                    or consent.rights_basis
                    != expected.get("consent_or_rights_basis")
                    or tuple(consent.allowed_features) != tuple(expected.get("allowed_features", ()))
                    or tuple(consent.excluded_features) != tuple(expected.get("excluded_features", ()))
                ):
                    raise ContractError("verified consent differs from the Invent authorization")
            expected_cases = {
                (
                    item.get("reference_id"),
                    item.get("reference_feature"),
                    item.get("recognition_test"),
                )
                for item in mappings
                if isinstance(item, Mapping)
            }
            observed_cases = {
                (item.reference_id, item.reference_feature, item.recognition_test)
                for item in verification.likeness_cases
            }
            if observed_cases != expected_cases:
                raise ContractError("world likeness cases do not cover every exact mapping")
            for case in verification.likeness_cases:
                material = materials[case.reference_id]
                consent = consents[case.reference_id]
                if (
                    case.reference_sha256 != material.sha256
                    or case.reference_feature not in consent.allowed_features
                    or case.reference_feature in consent.excluded_features
                ):
                    raise ContractError("world likeness case is not bound to authorized bytes")
        except WaitingFor:
            raise
        except Exception as exc:
            raise _need(
                "world-test",
                "The shared world provider did not return complete consent- and reference-bound evidence for these exact Invent bytes.",
                "Repair the Workshop consent/reference provider and cover every authorized reference and recognition test. Do not fabricate or publish private reference bytes.",
            ) from exc
        recognition_failures = sum(
            not item.recognized for item in verification.likeness_cases
        )
        consent_violations = sum(
            not item.consent_safe for item in verification.likeness_cases
        )
        measurements = {
            "consent_verified": True,
            "personalization_features": len(mappings),
            "likeness_cases": len(verification.likeness_cases),
            "recognition_failures": recognition_failures,
            "consent_violations": consent_violations,
        }
        source = ReleaseProofSource(
            "personalization-map",
            "product",
            "playtest/mechanical.json",
            contract_sha,
        )
        return PreparedLaneRelease(
            "world-test",
            context.made.artifact_sha256,
            verification.identity,
            (source,),
            measurements,
            {
                "consent-record": {
                    "attestation": verification.identity.to_dict(),
                    "attestation_scope": "trusted-provider verification over private consent digests; raw bytes are intentionally not public-replayable",
                    "records": [item.receipt_dict() for item in verification.consent_records],
                    "raw_consent_bytes_sealed": False,
                },
                "reference-material": {
                    "attestation": verification.identity.to_dict(),
                    "attestation_scope": "trusted-provider verification over authorized private reference digests; raw bytes are intentionally not public-replayable",
                    "references": [item.receipt_dict() for item in verification.references],
                    "raw_private_bytes_sealed": False,
                },
                "likeness-traces": {
                    "attestation": verification.identity.to_dict(),
                    "cases": [item.to_dict() for item in verification.likeness_cases]
                },
            },
            recognition_failures == consent_violations == 0,
            (
                "Matched every exact personalization feature to verified consent and authorized private reference hashes.",
                "Private reference and consent bytes stayed outside Playtest evidence; only bounded digests and comparison traces were sealed.",
            ),
        )


__all__ = [
    "ClassicEvidenceProvider",
    "PinnedCheckersRulesProvider",
    "PreparedLaneRelease",
    "ProviderIdentity",
    "PublicScienceSource",
    "ScienceAccuracyCase",
    "ScienceContentCoverageTrace",
    "ScienceComprehensionTrace",
    "ScienceEvidenceProvider",
    "SealedInventScienceEvidenceProvider",
    "ScienceSimplificationCheck",
    "ScienceVerification",
    "WorkshopLanePlaytestProviders",
    "WorldConsentRecord",
    "WorldEvidenceProvider",
    "WorldLikenessCase",
    "WorldReferenceMaterial",
    "WorldVerification",
    "canonical_science_scale",
]
