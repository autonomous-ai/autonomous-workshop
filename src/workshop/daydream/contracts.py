"""Daydream idea, novelty, and sealed-brief contracts."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Sequence
from urllib.parse import urlsplit

from workshop.errors import ContractError, WorkshopError
from workshop._validation import copy_json_mapping, require_sha256
from workshop.daydream.schema import (
    DAYDREAM_IDEA_KIND,
    DAYDREAM_VERDICT_KIND,
    LEGACY_VERDICT_CHECKS,
    PROOF_MODES,
    ROUTE_FLOORS,
    THESIS_V2_VERDICT_CHECKS,
    THESIS_VERDICT_CHECKS,
    idea_problems as schema_idea_problems,
    verdict_problems as schema_verdict_problems,
)


DAYDREAM_SEAL_KIND = "autonomous-workshop.daydream-seal"
DAYDREAM_PROVENANCE_KIND = "autonomous-workshop.daydream-provenance"
MAX_TITLE_CHARS = 60
MAX_ONE_LINER_CHARS = 200
MAX_VERDICT_TEXT_CHARS = 400
VERDICT_DECISIONS = ("build", "dream-again")
# Historical verdict vocabulary remains stable so records written while the
# retired Judge existed can still be parsed. New Daydreams do not create or
# gate on Verdict objects.
VERDICT_CHECKS = LEGACY_VERDICT_CHECKS
MAX_PRIOR_ART_NAME_CHARS = 80
MAX_PRIOR_ART_DIFFERENCE_CHARS = 300
MAX_TASTE_FIT_ITEM_CHARS = 200
MIN_PRIOR_ART_ENTRIES = 2
MAX_PRIOR_ART_ENTRIES = 5
MIN_TASTE_FIT_ITEMS = 1
MAX_TASTE_FIT_ITEMS = 5
MIN_PARTS_ESTIMATE = 1
MAX_PARTS_ESTIMATE = 12
MIN_KEYWORDS = 3
MAX_KEYWORDS = 8
MAX_INVENTOR_NAME_CHARS = 200
MAX_NOVELTY_NEIGHBORS = 3
MAX_NOVELTY_TEXT_CHARS = 200
MAX_NOVELTY_REASON_CHARS = 1_000
NOVELTY_STATUSES = ("new", "too-close")
CREATED_AT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

_DAYDREAM_ID = re.compile(r"^daydream-\d{8}-\d{6}-[0-9a-f]{8}$")
_INVENTOR_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
_MANAGER_ID = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
_KEYWORD = re.compile(r"^[a-z0-9][a-z0-9-]{1,31}$")
_PRIOR_ART_KEYS = frozenset(("name", "how_this_differs"))
_PRIOR_ART_V2_KEYS = frozenset(("name", "url", "observed_at", "how_this_differs"))
_TASTE_FIT_KEYS = frozenset(("honors", "steers_clear_of"))
_RISK_KEYS = frozenset(("kind", "detail"))
_SEAL_OPTIONAL_KEYS = frozenset(("verdict",))
_NEIGHBOR_KEYS = frozenset(("source", "title", "similarity"))
_NOVELTY_KEYS = frozenset(("status", "max_similarity", "nearest", "reason"))
_SEAL_V1_KEYS = frozenset(
    (
        "schema_version",
        "kind",
        "daydream_id",
        "inventor_id",
        "inventor_name",
        "taste_sha256",
        "manager_id",
        "seed",
        "created_at",
        "idea",
        "idea_sha256",
        "novelty",
        "session",
        "brief",
    )
)
_SEAL_V2_KEYS = _SEAL_V1_KEYS | frozenset(("provenance",))
DAYDREAM_PROVENANCE_INPUTS = (
    "daydream_prompt",
    "daydream_constitution",
    "taste",
    "inventor_binding",
    "vault_binding",
    "vault_snapshot",
    "prior_work",
    "portfolio",
    "notebook",
    "finalizer",
    "schema",
    "world_scan",
    "prior_art",
    "manager_spec",
)
_OPTIONAL_PROVENANCE_INPUTS = frozenset(("vault_snapshot",))
_PROVENANCE_KEYS = frozenset(
    ("schema_version", "kind", "route", "input_sha256s")
)


class DaydreamError(WorkshopError):
    """One Daydream turn could not produce a sealed, novel idea."""


def canonical_json(value: Any) -> str:
    """Serialize one JSON value exactly the way every Daydream identity does."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def generate_daydream_id(
    *, moment: Optional[datetime] = None, token: Optional[str] = None
) -> str:
    """Create an opaque daydream identifier without putting idea words in paths."""

    observed = moment if moment is not None else datetime.now(timezone.utc)
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    observed = observed.astimezone(timezone.utc)
    suffix = token if token is not None else secrets.token_hex(4)
    if (
        not isinstance(suffix, str)
        or len(suffix) != 8
        or any(character not in "0123456789abcdef" for character in suffix)
    ):
        raise ContractError(
            "Daydream id token must be eight lowercase hexadecimal characters"
        )
    return "daydream-%s-%s" % (observed.strftime("%Y%m%d-%H%M%S"), suffix)


def require_daydream_id(value: Any, label: str = "daydream_id") -> str:
    if not isinstance(value, str) or _DAYDREAM_ID.fullmatch(value) is None:
        raise ContractError("%s must look like daydream-YYYYMMDD-HHMMSS-hex8" % label)
    return value


def require_inventor_id(value: Any, label: str = "inventor_id") -> str:
    if not isinstance(value, str) or _INVENTOR_ID.fullmatch(value) is None:
        raise ContractError("%s must match %s" % (label, _INVENTOR_ID.pattern))
    return value


def require_created_at(value: Any, label: str = "created_at") -> str:
    try:
        if (
            not isinstance(value, str)
            or datetime.strptime(value, CREATED_AT_FORMAT).strftime(CREATED_AT_FORMAT)
            != value
        ):
            raise ValueError
    except ValueError as exc:
        raise ContractError("%s must be YYYY-MM-DDTHH:MM:SSZ" % label) from exc
    return value


def bounded_line(value: Any, label: str, maximum: int) -> str:
    """Validate one non-empty control-free line of at most ``maximum`` characters."""

    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError(
            "%s must be one control-free line of 1 to %d characters" % (label, maximum)
        )
    return value


def bounded_paragraph(value: Any, label: str, maximum: int) -> str:
    """Validate short prose that may contain line feeds but no other controls."""

    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(
            (ord(character) < 32 and character != "\n") or ord(character) == 127
            for character in value
        )
    ):
        raise ContractError(
            "%s must be 1 to %d characters with no control characters other "
            "than line feeds" % (label, maximum)
        )
    return value


def _exact_keys(raw: Any, expected: frozenset, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise ContractError("%s must be a JSON object" % label)
    missing = sorted(expected - set(raw))
    unknown = sorted(set(raw) - expected)
    details = []
    if missing:
        details.append("missing keys %s" % missing)
    if unknown:
        details.append("unknown keys %s" % unknown)
    if details:
        raise ContractError("%s has %s" % (label, "; ".join(details)))
    return raw


def _line_tuple(
    value: Any, label: str, *, minimum: int, maximum: int, item_maximum: int
) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ContractError("%s must be a list of %d to %d lines" % (label, minimum, maximum))
    items = tuple(value)
    if not minimum <= len(items) <= maximum:
        raise ContractError("%s must contain %d to %d items" % (label, minimum, maximum))
    for index, item in enumerate(items):
        bounded_line(item, "%s[%d]" % (label, index), item_maximum)
    return items


def _finite_unit_float(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError("%s must be a number from 0 to 1" % label)
    number = float(value)
    if number != number or not 0.0 <= number <= 1.0:
        raise ContractError("%s must be a number from 0 to 1" % label)
    return number


@dataclass(frozen=True)
class PriorArt:
    """One existing thing the idea is closest to, and the real difference."""

    name: str
    how_this_differs: str
    url: Optional[str] = None
    observed_at: Optional[str] = None

    def __post_init__(self) -> None:
        bounded_line(self.name, "prior_art name", MAX_PRIOR_ART_NAME_CHARS)
        bounded_line(
            self.how_this_differs,
            "prior_art how_this_differs",
            MAX_PRIOR_ART_DIFFERENCE_CHARS,
        )
        if (self.url is None) != (self.observed_at is None):
            raise ContractError("prior_art url and observed_at must be present together")
        if self.url is not None:
            bounded_line(self.url, "prior_art url", 500)
            parsed = urlsplit(self.url)
            if (
                parsed.scheme not in ("http", "https")
                or not parsed.netloc
                or parsed.username is not None
                or parsed.password is not None
            ):
                raise ContractError(
                    "prior_art url must be an http(s) URL without embedded credentials"
                )
            require_created_at(self.observed_at, "prior_art observed_at")

    @classmethod
    def parse(cls, raw: Mapping[str, Any], *, schema_version: int = 1) -> "PriorArt":
        expected = _PRIOR_ART_KEYS if schema_version == 1 else _PRIOR_ART_V2_KEYS
        _exact_keys(raw, expected, "prior_art entry")
        return cls(
            name=raw["name"],
            how_this_differs=raw["how_this_differs"],
            url=raw.get("url"),
            observed_at=raw.get("observed_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        value = {"name": self.name, "how_this_differs": self.how_this_differs}
        if self.url is not None:
            value.update({"url": self.url, "observed_at": self.observed_at})
        return value


@dataclass(frozen=True)
class TasteFit:
    """The Inventor's own account of how the idea obeys its Taste."""

    honors: tuple[str, ...]
    steers_clear_of: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("honors", "steers_clear_of"):
            object.__setattr__(
                self,
                name,
                _line_tuple(
                    getattr(self, name),
                    "taste_fit %s" % name,
                    minimum=MIN_TASTE_FIT_ITEMS,
                    maximum=MAX_TASTE_FIT_ITEMS,
                    item_maximum=MAX_TASTE_FIT_ITEM_CHARS,
                ),
            )

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "TasteFit":
        _exact_keys(raw, _TASTE_FIT_KEYS, "taste_fit")
        return cls(honors=raw["honors"], steers_clear_of=raw["steers_clear_of"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "honors": list(self.honors),
            "steers_clear_of": list(self.steers_clear_of),
        }


@dataclass(frozen=True)
class WorldSignal:
    """One bounded, source-addressed current-world observation."""

    title: str
    url: str
    published_at: Optional[str]
    insight: str

    def __post_init__(self) -> None:
        bounded_line(self.title, "world signal title", 160)
        bounded_line(self.url, "world signal url", 500)
        parsed = urlsplit(self.url)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ContractError(
                "world signal url must be an http(s) URL without embedded credentials"
            )
        if self.published_at is not None:
            require_created_at(self.published_at, "world signal published_at")
        bounded_line(self.insight, "world signal insight", 300)

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "WorldSignal":
        _exact_keys(
            raw,
            frozenset(("title", "url", "published_at", "insight")),
            "world signal",
        )
        return cls(
            title=raw["title"],
            url=raw["url"],
            published_at=raw["published_at"],
            insight=raw["insight"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "insight": self.insight,
        }


@dataclass(frozen=True)
class WorldScan:
    """The bounded search scope and current signals one thesis considered."""

    observed_at: str
    scope: str
    evergreen: bool
    signals: tuple[WorldSignal, ...]

    def __post_init__(self) -> None:
        require_created_at(self.observed_at, "world scan observed_at")
        bounded_line(self.scope, "world scan scope", 500)
        if type(self.evergreen) is not bool:
            raise ContractError("world scan evergreen must be a boolean")
        if isinstance(self.signals, (str, Mapping)) or not isinstance(self.signals, Sequence):
            raise ContractError("world scan signals must be a list")
        signals = tuple(self.signals)
        if not 2 <= len(signals) <= 6 or any(
            not isinstance(signal, WorldSignal) for signal in signals
        ):
            raise ContractError("world scan signals must contain 2 to 6 WorldSignal entries")
        urls = [signal.url for signal in signals]
        if len(set(urls)) != len(urls):
            raise ContractError("world scan signal URLs must be unique")
        object.__setattr__(self, "signals", signals)

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "WorldScan":
        _exact_keys(
            raw,
            frozenset(("observed_at", "scope", "evergreen", "signals")),
            "world scan",
        )
        return cls(
            observed_at=raw["observed_at"],
            scope=raw["scope"],
            evergreen=raw["evergreen"],
            signals=tuple(WorldSignal.parse(item) for item in raw["signals"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observed_at": self.observed_at,
            "scope": self.scope,
            "evergreen": self.evergreen,
            "signals": [signal.to_dict() for signal in self.signals],
        }


@dataclass(frozen=True)
class Opportunity:
    """The explicit signal-to-tension-to-physical-opportunity translation."""

    world_scan: WorldScan
    human_tension: str
    why_now: str
    physical_opportunity: str
    evidence_boundary: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.world_scan, WorldScan):
            raise ContractError("opportunity world_scan must be a WorldScan")
        for name in ("human_tension", "why_now", "physical_opportunity"):
            bounded_paragraph(getattr(self, name), "opportunity %s" % name, 600)
        if self.evidence_boundary is not None:
            bounded_paragraph(
                self.evidence_boundary, "opportunity evidence_boundary", 600
            )

    @classmethod
    def parse(cls, raw: Mapping[str, Any], *, schema_version: int = 2) -> "Opportunity":
        expected = frozenset(
            ("world_scan", "human_tension", "why_now", "physical_opportunity")
        )
        if schema_version == 3:
            expected |= frozenset(("evidence_boundary",))
        _exact_keys(
            raw,
            expected,
            "opportunity",
        )
        return cls(
            world_scan=WorldScan.parse(raw["world_scan"]),
            human_tension=raw["human_tension"],
            why_now=raw["why_now"],
            physical_opportunity=raw["physical_opportunity"],
            evidence_boundary=raw.get("evidence_boundary"),
        )

    def to_dict(self) -> Dict[str, Any]:
        value = {
            "world_scan": self.world_scan.to_dict(),
            "human_tension": self.human_tension,
            "why_now": self.why_now,
            "physical_opportunity": self.physical_opportunity,
        }
        if self.evidence_boundary is not None:
            value["evidence_boundary"] = self.evidence_boundary
        return value


@dataclass(frozen=True)
class Experience:
    """The experience-level promise Daydream owns while Invent owns the how."""

    physical_form: str
    action: str
    response: str
    payoff: str
    anti_generic_signature: str
    theme_strip_test: str
    invent_freedom: str

    def __post_init__(self) -> None:
        for name in (
            "physical_form",
            "action",
            "response",
            "payoff",
            "anti_generic_signature",
            "theme_strip_test",
            "invent_freedom",
        ):
            bounded_paragraph(getattr(self, name), "experience %s" % name, 600)

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "Experience":
        expected = frozenset(
            (
                "physical_form",
                "action",
                "response",
                "payoff",
                "anti_generic_signature",
                "theme_strip_test",
                "invent_freedom",
            )
        )
        _exact_keys(raw, expected, "experience")
        return cls(**{name: raw[name] for name in expected})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "physical_form": self.physical_form,
            "action": self.action,
            "response": self.response,
            "payoff": self.payoff,
            "anti_generic_signature": self.anti_generic_signature,
            "theme_strip_test": self.theme_strip_test,
            "invent_freedom": self.invent_freedom,
        }


@dataclass(frozen=True)
class ProofPlan:
    """How a later stage can falsify the promised signature."""

    mode: str
    observable: str
    kill_criteria: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.mode not in PROOF_MODES:
            raise ContractError("proof mode must be one of %s" % (PROOF_MODES,))
        bounded_paragraph(self.observable, "proof observable", 600)
        object.__setattr__(
            self,
            "kill_criteria",
            _line_tuple(
                self.kill_criteria,
                "proof kill_criteria",
                minimum=2,
                maximum=5,
                item_maximum=300,
            ),
        )

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "ProofPlan":
        _exact_keys(raw, frozenset(("mode", "observable", "kill_criteria")), "proof")
        return cls(
            mode=raw["mode"],
            observable=raw["observable"],
            kill_criteria=raw["kill_criteria"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "observable": self.observable,
            "kill_criteria": list(self.kill_criteria),
        }


@dataclass(frozen=True)
class LearningTrace:
    """An exact response to one unresolved prior Daydream memory."""

    daydream_id: str
    memory_sha256: str
    disposition: str
    response: str

    def __post_init__(self) -> None:
        require_daydream_id(self.daydream_id, "learning daydream_id")
        require_sha256(self.memory_sha256, "learning memory_sha256")
        if self.disposition not in ("repaired", "abandoned"):
            raise ContractError("learning disposition must be repaired or abandoned")
        bounded_paragraph(self.response, "learning response", 500)

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "LearningTrace":
        _exact_keys(
            raw,
            frozenset(("daydream_id", "memory_sha256", "disposition", "response")),
            "learning entry",
        )
        return cls(
            daydream_id=raw["daydream_id"],
            memory_sha256=raw["memory_sha256"],
            disposition=raw["disposition"],
            response=raw["response"],
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "daydream_id": self.daydream_id,
            "memory_sha256": self.memory_sha256,
            "disposition": self.disposition,
            "response": self.response,
        }


@dataclass(frozen=True, kw_only=True)
class Idea:
    """One idea or creative product thesis exactly as the Inventor wrote it."""

    schema_version: int = 1
    title: str
    one_liner: str
    what_you_do: str
    what_happens: str
    why_it_is_new: str
    prior_art: tuple[PriorArt, ...]
    taste_fit: TasteFit
    parts_estimate: int
    keywords: tuple[str, ...]
    held_form: Optional[str] = None
    before_after: Optional[str] = None
    opportunity: Optional[Opportunity] = None
    experience: Optional[Experience] = None
    proof: Optional[ProofPlan] = None
    route_floor: Optional[str] = None
    learning: tuple[LearningTrace, ...] = ()

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version not in (1, 2, 3):
            raise ContractError("idea schema_version must be 1, 2, or 3")
        if isinstance(self.learning, (str, Mapping)) or not isinstance(
            self.learning, Sequence
        ):
            raise ContractError("idea learning must be a list")
        learning = tuple(self.learning)
        if len(learning) > 5 or any(
            not isinstance(entry, LearningTrace) for entry in learning
        ):
            raise ContractError("idea learning must contain at most 5 LearningTrace entries")
        if len({entry.daydream_id for entry in learning}) != len(learning):
            raise ContractError("idea learning cannot repeat a prior daydream_id")
        object.__setattr__(self, "learning", learning)
        if self.schema_version == 1:
            if any(
                value is not None
                for value in (self.opportunity, self.experience, self.proof, self.route_floor)
            ) or learning:
                raise ContractError("idea schema 1 cannot carry thesis-v2 fields")
        else:
            if not isinstance(self.opportunity, Opportunity):
                raise ContractError("idea opportunity must be an Opportunity")
            if not isinstance(self.experience, Experience):
                raise ContractError("idea experience must be an Experience")
            if not isinstance(self.proof, ProofPlan):
                raise ContractError("idea proof must be a ProofPlan")
            if self.route_floor not in ROUTE_FLOORS:
                raise ContractError("idea route_floor must be one of %s" % (ROUTE_FLOORS,))
            if self.schema_version == 2:
                if learning:
                    raise ContractError("idea schema 2 cannot carry learning traces")
                if self.opportunity.evidence_boundary is not None:
                    raise ContractError("idea schema 2 cannot carry an evidence boundary")
            elif self.opportunity.evidence_boundary is None:
                raise ContractError("idea schema 3 requires an evidence boundary")
        if isinstance(self.prior_art, (str, Mapping)) or not isinstance(
            self.prior_art, Sequence
        ):
            raise ContractError("idea prior_art must be a list of entries")
        prior_art = tuple(self.prior_art)
        if not MIN_PRIOR_ART_ENTRIES <= len(prior_art) <= MAX_PRIOR_ART_ENTRIES or any(
            not isinstance(entry, PriorArt) for entry in prior_art
        ):
            raise ContractError(
                "idea prior_art must contain %d to %d entries"
                % (MIN_PRIOR_ART_ENTRIES, MAX_PRIOR_ART_ENTRIES)
            )
        if self.schema_version == 1 and any(entry.url is not None for entry in prior_art):
            raise ContractError("idea schema 1 prior_art cannot carry source fields")
        if self.schema_version >= 2 and any(entry.url is None for entry in prior_art):
            raise ContractError("thesis prior_art requires source fields")
        object.__setattr__(self, "prior_art", prior_art)
        if not isinstance(self.taste_fit, TasteFit):
            raise ContractError("idea taste_fit must be a TasteFit")
        if (
            type(self.parts_estimate) is not int
            or not MIN_PARTS_ESTIMATE <= self.parts_estimate <= MAX_PARTS_ESTIMATE
        ):
            raise ContractError(
                "idea parts_estimate must be an integer from %d to %d"
                % (MIN_PARTS_ESTIMATE, MAX_PARTS_ESTIMATE)
            )
        if isinstance(self.keywords, str) or not isinstance(self.keywords, Sequence):
            raise ContractError("idea keywords must be a list of slugs")
        keywords = tuple(self.keywords)
        if (
            not MIN_KEYWORDS <= len(keywords) <= MAX_KEYWORDS
            or any(
                not isinstance(keyword, str) or _KEYWORD.fullmatch(keyword) is None
                for keyword in keywords
            )
            or len(set(keywords)) != len(keywords)
        ):
            raise ContractError(
                "idea keywords must be %d to %d unique slugs matching %s"
                % (MIN_KEYWORDS, MAX_KEYWORDS, _KEYWORD.pattern)
            )
        object.__setattr__(self, "keywords", keywords)
        problems = schema_idea_problems(self.to_dict())
        if problems:
            raise ContractError("idea is invalid: %s" % "; ".join(problems))

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "Idea":
        problems = schema_idea_problems(raw)
        if problems:
            raise ContractError("idea is invalid: %s" % "; ".join(problems))
        version = raw["schema_version"]
        if version == 1:
            return cls(
                schema_version=version,
                title=raw["title"],
                one_liner=raw["one_liner"],
                what_you_do=raw["what_you_do"],
                what_happens=raw["what_happens"],
                why_it_is_new=raw["why_it_is_new"],
                prior_art=tuple(
                    PriorArt.parse(entry, schema_version=version) for entry in raw["prior_art"]
                ),
                taste_fit=TasteFit.parse(raw["taste_fit"]),
                parts_estimate=raw["parts_estimate"],
                keywords=raw["keywords"],
                held_form=raw.get("held_form"),
                before_after=raw.get("before_after"),
            )
        opportunity = Opportunity.parse(raw["opportunity"], schema_version=version)
        experience = Experience.parse(raw["experience"])
        proof = ProofPlan.parse(raw["proof"])
        return cls(
            schema_version=version,
            title=raw["title"],
            one_liner=raw["one_liner"],
            # Compatibility views for callers that consumed schema-v1 fields.
            what_you_do=experience.action,
            what_happens="%s %s" % (experience.response, experience.payoff),
            why_it_is_new=raw["why_it_is_new"],
            prior_art=tuple(
                PriorArt.parse(entry, schema_version=version) for entry in raw["prior_art"]
            ),
            taste_fit=TasteFit.parse(raw["taste_fit"]),
            parts_estimate=raw["parts_estimate"],
            keywords=raw["keywords"],
            held_form=experience.physical_form,
            before_after=proof.observable,
            opportunity=opportunity,
            experience=experience,
            proof=proof,
            route_floor=raw["route_floor"],
            learning=tuple(
                LearningTrace.parse(entry) for entry in raw.get("learning", ())
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        if self.schema_version >= 2:
            assert self.opportunity is not None
            assert self.experience is not None
            assert self.proof is not None
            value = {
                "schema_version": self.schema_version,
                "kind": DAYDREAM_IDEA_KIND,
                "title": self.title,
                "one_liner": self.one_liner,
                "opportunity": self.opportunity.to_dict(),
                "experience": self.experience.to_dict(),
                "why_it_is_new": self.why_it_is_new,
                "prior_art": [entry.to_dict() for entry in self.prior_art],
                "taste_fit": self.taste_fit.to_dict(),
                "proof": self.proof.to_dict(),
                "route_floor": self.route_floor,
                "parts_estimate": self.parts_estimate,
                "keywords": list(self.keywords),
            }
            if self.schema_version == 3:
                value["learning"] = [entry.to_dict() for entry in self.learning]
            return value
        value: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "kind": DAYDREAM_IDEA_KIND,
            "title": self.title,
            "one_liner": self.one_liner,
        }
        if self.held_form is not None:
            # Older sealed ideas have no held form; leaving the key out keeps
            # their canonical bytes and sha256 unchanged.
            value["held_form"] = self.held_form
        if self.before_after is not None:
            value["before_after"] = self.before_after
        value.update({
            "what_you_do": self.what_you_do,
            "what_happens": self.what_happens,
            "why_it_is_new": self.why_it_is_new,
            "prior_art": [entry.to_dict() for entry in self.prior_art],
            "taste_fit": self.taste_fit.to_dict(),
            "parts_estimate": self.parts_estimate,
            "keywords": list(self.keywords),
        })
        return value

    def canonical_bytes(self) -> bytes:
        return canonical_json(self.to_dict()).encode("utf-8")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def render_brief(idea: Idea, *, inventor_name: str, inventor_id: str) -> str:
    """Render the deterministic plain-text brief that becomes the Wish objective."""

    if not isinstance(idea, Idea):
        raise ContractError("render_brief requires an Idea")
    bounded_line(inventor_name, "inventor name", MAX_INVENTOR_NAME_CHARS)
    require_inventor_id(inventor_id, "inventor id")
    if idea.schema_version >= 2:
        assert idea.opportunity is not None
        assert idea.experience is not None
        assert idea.proof is not None
        lines = [
            "Daydreamed by %s (%s). Build this creative product thesis."
            % (inventor_name, inventor_id),
            "",
            "Title: %s" % idea.title,
            "In one line: %s" % idea.one_liner,
            "Human tension: %s" % idea.opportunity.human_tension,
            "Why now: %s" % idea.opportunity.why_now,
            "Physical opportunity: %s" % idea.opportunity.physical_opportunity,
            "Physical form: %s" % idea.experience.physical_form,
            "Action: %s" % idea.experience.action,
            "Response: %s" % idea.experience.response,
            "Payoff: %s" % idea.experience.payoff,
            "Anti-generic signature: %s" % idea.experience.anti_generic_signature,
            "Theme-strip test: %s" % idea.experience.theme_strip_test,
            "Invent freedom: %s" % idea.experience.invent_freedom,
            "Why it is new: %s" % idea.why_it_is_new,
            "Proof mode: %s" % idea.proof.mode,
            "Observable proof: %s" % idea.proof.observable,
            "Kill criteria:",
        ]
        lines.extend("- %s" % criterion for criterion in idea.proof.kill_criteria)
        lines.append("Closest existing things, and how this differs:")
        lines.extend(
            "- %s (%s, observed %s): %s"
            % (entry.name, entry.url, entry.observed_at, entry.how_this_differs)
            for entry in idea.prior_art
        )
        lines.extend(
            (
                "Fits the Inventor's Taste by: %s" % "; ".join(idea.taste_fit.honors),
                "Steers clear of: %s" % "; ".join(idea.taste_fit.steers_clear_of),
                "Minimum route: %s" % idea.route_floor,
                "Printed parts (estimate): %d" % idea.parts_estimate,
                "",
                "Preserve the opportunity, Taste promises, action, payoff, and "
                "anti-generic signature. Invent owns the exact mechanism, dimensions, "
                "materials, construction, and evidence-backed physical facts.",
                "Match should bind %s, who dreamed this, unless the Taste rejects the "
                "final concept." % inventor_name,
            )
        )
        return "\n".join(lines)
    lines = [
        "Daydreamed by %s (%s). Build this new toy." % (inventor_name, inventor_id),
        "",
        "Title: %s" % idea.title,
        "In one line: %s" % idea.one_liner,
    ]
    if idea.held_form is not None:
        lines.append("What it looks like: %s" % idea.held_form)
    if idea.before_after is not None:
        lines.append("Before and after, as a render must show them: %s" % idea.before_after)
    lines += [
        "What you do: %s" % idea.what_you_do,
        "What happens: %s" % idea.what_happens,
        "Why it is new: %s" % idea.why_it_is_new,
        "Closest existing things, and how this differs:",
    ]
    lines.extend(
        "- %s: %s" % (entry.name, entry.how_this_differs) for entry in idea.prior_art
    )
    lines.extend(
        (
            "Fits the Inventor's Taste by: %s" % "; ".join(idea.taste_fit.honors),
            "Steers clear of: %s" % "; ".join(idea.taste_fit.steers_clear_of),
            "Printed parts (estimate): %d" % idea.parts_estimate,
            "",
            "Match should bind %s, who dreamed this, unless the Taste rejects the "
            "final concept." % inventor_name,
        )
    )
    return "\n".join(lines)


@dataclass(frozen=True)
class VerdictRisk:
    """One risk the judge saw, named by the Make review criterion it threatens."""

    kind: str
    detail: str

    def __post_init__(self) -> None:
        bounded_line(self.kind, "verdict risk kind", 60)
        bounded_line(self.detail, "verdict risk detail", MAX_VERDICT_TEXT_CHARS)

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "VerdictRisk":
        _exact_keys(raw, _RISK_KEYS, "verdict risk")
        return cls(kind=raw["kind"], detail=raw["detail"])

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "detail": self.detail}


@dataclass(frozen=True, kw_only=True)
class Verdict:
    """An independent judge's call on whether Make can prove this idea."""

    schema_version: int = 1
    decision: str
    checks: Mapping[str, bool]
    confidence: float
    risks: tuple[VerdictRisk, ...]
    advice: str
    daydream_id: Optional[str] = None
    idea_sha256: Optional[str] = None
    taste_sha256: Optional[str] = None
    route: Optional[str] = None

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version not in (1, 2, 3):
            raise ContractError("verdict schema_version must be 1, 2, or 3")
        if not isinstance(self.checks, Mapping):
            raise ContractError("verdict checks must be a mapping")
        expected_checks = (
            VERDICT_CHECKS
            if self.schema_version == 1
            else THESIS_V2_VERDICT_CHECKS
            if self.schema_version == 2
            else THESIS_VERDICT_CHECKS
        )
        if set(self.checks) != set(expected_checks):
            raise ContractError("verdict checks must be exactly %s" % (expected_checks,))
        object.__setattr__(self, "checks", dict(self.checks))
        if isinstance(self.risks, (str, Mapping)) or not isinstance(self.risks, Sequence):
            raise ContractError("verdict risks must be a list")
        risks = tuple(self.risks)
        if any(not isinstance(risk, VerdictRisk) for risk in risks):
            raise ContractError("verdict risks must contain VerdictRisk entries")
        object.__setattr__(self, "risks", risks)
        problems = schema_verdict_problems(self.to_dict())
        if problems:
            raise ContractError("verdict is invalid: %s" % "; ".join(problems))
        object.__setattr__(
            self, "confidence", _finite_unit_float(self.confidence, "verdict confidence")
        )

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "Verdict":
        problems = schema_verdict_problems(raw)
        if problems:
            raise ContractError("verdict is invalid: %s" % "; ".join(problems))
        return cls(
            schema_version=raw["schema_version"],
            decision=raw["decision"],
            checks=raw["checks"],
            confidence=raw["confidence"],
            risks=tuple(VerdictRisk.parse(entry) for entry in raw["risks"]),
            advice=raw["advice"],
            daydream_id=raw.get("daydream_id"),
            idea_sha256=raw.get("idea_sha256"),
            taste_sha256=raw.get("taste_sha256"),
            route=raw.get("route"),
        )

    @property
    def failed_checks(self) -> tuple[str, ...]:
        return tuple(sorted(name for name, value in self.checks.items() if not value))

    def to_dict(self) -> Dict[str, Any]:
        check_names = (
            VERDICT_CHECKS
            if self.schema_version == 1
            else THESIS_V2_VERDICT_CHECKS
            if self.schema_version == 2
            else THESIS_VERDICT_CHECKS
        )
        value: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "kind": DAYDREAM_VERDICT_KIND,
            "decision": self.decision,
            "checks": {name: self.checks[name] for name in check_names},
            "confidence": self.confidence,
            "risks": [risk.to_dict() for risk in self.risks],
            "advice": self.advice,
        }
        if self.schema_version >= 2:
            value.update(
                {
                    "daydream_id": self.daydream_id,
                    "idea_sha256": self.idea_sha256,
                    "taste_sha256": self.taste_sha256,
                    "route": self.route,
                }
            )
        return value


@dataclass(frozen=True)
class NoveltyNeighbor:
    """One prior-work entry and how similar the idea is to it."""

    source: str
    title: str
    similarity: float

    def __post_init__(self) -> None:
        bounded_line(self.source, "novelty neighbor source", MAX_NOVELTY_TEXT_CHARS)
        bounded_line(self.title, "novelty neighbor title", MAX_NOVELTY_TEXT_CHARS)
        object.__setattr__(
            self,
            "similarity",
            _finite_unit_float(self.similarity, "novelty neighbor similarity"),
        )

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "NoveltyNeighbor":
        _exact_keys(raw, _NEIGHBOR_KEYS, "novelty neighbor")
        return cls(source=raw["source"], title=raw["title"], similarity=raw["similarity"])

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "title": self.title, "similarity": self.similarity}


@dataclass(frozen=True)
class NoveltyReport:
    """The deterministic lint verdict recorded beside every sealed idea."""

    status: str
    max_similarity: float
    nearest: tuple[NoveltyNeighbor, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.status not in NOVELTY_STATUSES:
            raise ContractError("novelty status must be one of %s" % (NOVELTY_STATUSES,))
        object.__setattr__(
            self,
            "max_similarity",
            _finite_unit_float(self.max_similarity, "novelty max_similarity"),
        )
        if isinstance(self.nearest, (str, Mapping)) or not isinstance(
            self.nearest, Sequence
        ):
            raise ContractError("novelty nearest must be a list of neighbors")
        nearest = tuple(self.nearest)
        if len(nearest) > MAX_NOVELTY_NEIGHBORS or any(
            not isinstance(entry, NoveltyNeighbor) for entry in nearest
        ):
            raise ContractError(
                "novelty nearest must hold at most %d neighbors" % MAX_NOVELTY_NEIGHBORS
            )
        similarities = [entry.similarity for entry in nearest]
        if similarities != sorted(similarities, reverse=True):
            raise ContractError("novelty nearest must be sorted by descending similarity")
        expected = similarities[0] if similarities else 0.0
        if self.max_similarity != expected:
            raise ContractError("novelty max_similarity must equal the nearest similarity")
        object.__setattr__(self, "nearest", nearest)
        bounded_line(self.reason, "novelty reason", MAX_NOVELTY_REASON_CHARS)

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "NoveltyReport":
        _exact_keys(raw, _NOVELTY_KEYS, "novelty")
        if isinstance(raw["nearest"], (str, Mapping)) or not isinstance(
            raw["nearest"], Sequence
        ):
            raise ContractError("novelty nearest must be a list of neighbors")
        return cls(
            status=raw["status"],
            max_similarity=raw["max_similarity"],
            nearest=tuple(NoveltyNeighbor.parse(entry) for entry in raw["nearest"]),
            reason=raw["reason"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "max_similarity": self.max_similarity,
            "nearest": [entry.to_dict() for entry in self.nearest],
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DaydreamProvenance:
    """Content identities for every context plane used by one new Dream."""

    route: str
    input_sha256s: Mapping[str, Optional[str]]
    schema_version: int = 1
    kind: str = DAYDREAM_PROVENANCE_KIND

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("Daydream provenance schema_version must be 1")
        if self.kind != DAYDREAM_PROVENANCE_KIND:
            raise ContractError("Daydream provenance kind is invalid")
        if self.route not in ROUTE_FLOORS:
            raise ContractError(
                "Daydream provenance route must be one of %s" % (ROUTE_FLOORS,)
            )
        if not isinstance(self.input_sha256s, Mapping) or set(self.input_sha256s) != set(
            DAYDREAM_PROVENANCE_INPUTS
        ):
            raise ContractError(
                "Daydream provenance inputs must be exactly %s"
                % (DAYDREAM_PROVENANCE_INPUTS,)
            )
        copied: Dict[str, Optional[str]] = {}
        for name in DAYDREAM_PROVENANCE_INPUTS:
            value = self.input_sha256s[name]
            if value is None:
                if name not in _OPTIONAL_PROVENANCE_INPUTS:
                    raise ContractError("Daydream provenance input %s cannot be null" % name)
            else:
                require_sha256(value, "Daydream provenance input %s" % name)
            copied[name] = value
        object.__setattr__(self, "input_sha256s", copied)

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "DaydreamProvenance":
        _exact_keys(raw, _PROVENANCE_KEYS, "Daydream provenance")
        return cls(
            schema_version=raw["schema_version"],
            kind=raw["kind"],
            route=raw["route"],
            input_sha256s=raw["input_sha256s"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "route": self.route,
            "input_sha256s": {
                name: self.input_sha256s[name] for name in DAYDREAM_PROVENANCE_INPUTS
            },
        }

    @property
    def sha256(self) -> str:
        return hashlib.sha256(canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


@dataclass(frozen=True, kw_only=True)
class SealedDaydream:
    """One idea, its provenance, its lint verdict, and the brief it becomes."""

    schema_version: int = 1
    kind: str = DAYDREAM_SEAL_KIND
    daydream_id: str
    inventor_id: str
    inventor_name: str
    taste_sha256: str
    manager_id: str
    seed: Mapping[str, Any]
    created_at: str
    idea: Idea
    idea_sha256: str
    novelty: NoveltyReport
    session: Mapping[str, Any]
    brief: str
    verdict: Optional[Verdict] = None
    provenance: Optional[DaydreamProvenance] = None

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version not in (1, 2, 3):
            raise ContractError("sealed daydream schema_version must be 1, 2, or 3")
        if self.verdict is not None and not isinstance(self.verdict, Verdict):
            raise ContractError("sealed daydream verdict must be a Verdict")
        if self.schema_version == 1 and self.provenance is not None:
            raise ContractError("sealed daydream schema 1 cannot carry provenance")
        if self.schema_version >= 2 and not isinstance(self.provenance, DaydreamProvenance):
            raise ContractError("sealed thesis requires provenance")
        if self.kind != DAYDREAM_SEAL_KIND:
            raise ContractError("sealed daydream kind must be %s" % DAYDREAM_SEAL_KIND)
        require_daydream_id(self.daydream_id, "sealed daydream daydream_id")
        require_inventor_id(self.inventor_id, "sealed daydream inventor_id")
        bounded_line(
            self.inventor_name, "sealed daydream inventor_name", MAX_INVENTOR_NAME_CHARS
        )
        require_sha256(self.taste_sha256, "sealed daydream taste_sha256")
        if not isinstance(self.manager_id, str) or _MANAGER_ID.fullmatch(self.manager_id) is None:
            raise ContractError("sealed daydream manager_id is invalid")
        object.__setattr__(
            self,
            "seed",
            copy_json_mapping(self.seed, "sealed daydream seed", nonempty=True),
        )
        require_created_at(self.created_at, "sealed daydream created_at")
        if not isinstance(self.idea, Idea):
            raise ContractError("sealed daydream idea must be an Idea")
        require_sha256(self.idea_sha256, "sealed daydream idea_sha256")
        if self.idea_sha256 != self.idea.sha256:
            raise ContractError("sealed daydream idea_sha256 does not match its idea")
        if self.schema_version >= 2:
            if self.idea.schema_version != self.schema_version:
                raise ContractError(
                    "sealed daydream schema %d requires a schema-v%d thesis"
                    % (self.schema_version, self.schema_version)
                )
            assert self.provenance is not None
            if self.provenance.input_sha256s["taste"] != self.taste_sha256:
                raise ContractError("sealed Daydream provenance does not match Taste")
            assert self.idea.opportunity is not None
            expected_world = hashlib.sha256(
                canonical_json(self.idea.opportunity.world_scan.to_dict()).encode("utf-8")
            ).hexdigest()
            expected_prior_art = hashlib.sha256(
                canonical_json([entry.to_dict() for entry in self.idea.prior_art]).encode(
                    "utf-8"
                )
            ).hexdigest()
            if (
                self.provenance.input_sha256s["world_scan"] != expected_world
                or self.provenance.input_sha256s["prior_art"] != expected_prior_art
            ):
                raise ContractError(
                    "sealed Daydream provenance does not match its source evidence"
                )
            if self.verdict is not None and (
                self.verdict.schema_version != self.schema_version
                or self.verdict.daydream_id != self.daydream_id
                or self.verdict.idea_sha256 != self.idea_sha256
                or self.verdict.taste_sha256 != self.taste_sha256
                or self.verdict.route != self.provenance.route
            ):
                raise ContractError("sealed Daydream provenance does not match its Judge")
        if not isinstance(self.novelty, NoveltyReport):
            raise ContractError("sealed daydream novelty must be a NoveltyReport")
        object.__setattr__(
            self, "session", copy_json_mapping(self.session, "sealed daydream session")
        )
        expected = render_brief(
            self.idea, inventor_name=self.inventor_name, inventor_id=self.inventor_id
        )
        if self.brief != expected:
            raise ContractError("sealed daydream brief does not match its idea")

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "SealedDaydream":
        if not isinstance(raw, Mapping):
            raise ContractError("sealed daydream must be a JSON object")
        version = raw.get("schema_version")
        if type(version) is not int or version not in (1, 2, 3):
            raise ContractError("sealed daydream schema_version must be 1, 2, or 3")
        expected = _SEAL_V1_KEYS if version == 1 else _SEAL_V2_KEYS
        _exact_keys(
            {key: value for key, value in raw.items() if key not in _SEAL_OPTIONAL_KEYS},
            expected,
            "sealed daydream",
        )
        verdict = raw.get("verdict")
        return cls(
            verdict=None if verdict is None else Verdict.parse(verdict),
            provenance=(
                DaydreamProvenance.parse(raw["provenance"]) if version >= 2 else None
            ),
            schema_version=version,
            kind=raw["kind"],
            daydream_id=raw["daydream_id"],
            inventor_id=raw["inventor_id"],
            inventor_name=raw["inventor_name"],
            taste_sha256=raw["taste_sha256"],
            manager_id=raw["manager_id"],
            seed=raw["seed"],
            created_at=raw["created_at"],
            idea=Idea.parse(raw["idea"]),
            idea_sha256=raw["idea_sha256"],
            novelty=NoveltyReport.parse(raw["novelty"]),
            session=raw["session"],
            brief=raw["brief"],
        )

    def to_dict(self) -> Dict[str, Any]:
        value: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "daydream_id": self.daydream_id,
            "inventor_id": self.inventor_id,
            "inventor_name": self.inventor_name,
            "taste_sha256": self.taste_sha256,
            "manager_id": self.manager_id,
            "seed": copy_json_mapping(self.seed, "sealed daydream seed", nonempty=True),
            "created_at": self.created_at,
            "idea": self.idea.to_dict(),
            "idea_sha256": self.idea_sha256,
            "novelty": self.novelty.to_dict(),
            "session": copy_json_mapping(self.session, "sealed daydream session"),
            "brief": self.brief,
        }
        if self.verdict is not None:
            value["verdict"] = self.verdict.to_dict()
        if self.schema_version >= 2:
            assert self.provenance is not None
            value["provenance"] = self.provenance.to_dict()
        return value

    @property
    def sha256(self) -> str:
        return hashlib.sha256(canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


__all__ = [
    "CREATED_AT_FORMAT",
    "DAYDREAM_IDEA_KIND",
    "DAYDREAM_PROVENANCE_INPUTS",
    "DAYDREAM_PROVENANCE_KIND",
    "DAYDREAM_SEAL_KIND",
    "DAYDREAM_VERDICT_KIND",
    "DaydreamError",
    "DaydreamProvenance",
    "Experience",
    "Idea",
    "LearningTrace",
    "NOVELTY_STATUSES",
    "NoveltyNeighbor",
    "NoveltyReport",
    "PriorArt",
    "Opportunity",
    "PROOF_MODES",
    "ProofPlan",
    "ROUTE_FLOORS",
    "SealedDaydream",
    "THESIS_VERDICT_CHECKS",
    "THESIS_V2_VERDICT_CHECKS",
    "TasteFit",
    "VERDICT_CHECKS",
    "VERDICT_DECISIONS",
    "Verdict",
    "VerdictRisk",
    "WorldScan",
    "WorldSignal",
    "bounded_line",
    "bounded_paragraph",
    "canonical_json",
    "generate_daydream_id",
    "render_brief",
    "require_created_at",
    "require_daydream_id",
    "require_inventor_id",
]
