"""Daydream idea, novelty, and sealed-brief contracts."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Sequence

from workshop.errors import ContractError, WorkshopError
from workshop._validation import copy_json_mapping, require_sha256


DAYDREAM_IDEA_KIND = "autonomous-workshop.daydream-idea"
DAYDREAM_SEAL_KIND = "autonomous-workshop.daydream-seal"
MAX_TITLE_CHARS = 60
MAX_ONE_LINER_CHARS = 200
MAX_HELD_FORM_CHARS = 240
MAX_PARAGRAPH_CHARS = 600
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
_TASTE_FIT_KEYS = frozenset(("honors", "steers_clear_of"))
_IDEA_KEYS = frozenset(
    (
        "schema_version",
        "kind",
        "title",
        "one_liner",
        "what_you_do",
        "what_happens",
        "why_it_is_new",
        "prior_art",
        "taste_fit",
        "parts_estimate",
        "keywords",
    )
)
_IDEA_OPTIONAL_KEYS = frozenset(("held_form",))
_NEIGHBOR_KEYS = frozenset(("source", "title", "similarity"))
_NOVELTY_KEYS = frozenset(("status", "max_similarity", "nearest", "reason"))
_SEAL_KEYS = frozenset(
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

    def __post_init__(self) -> None:
        bounded_line(self.name, "prior_art name", MAX_PRIOR_ART_NAME_CHARS)
        bounded_line(
            self.how_this_differs,
            "prior_art how_this_differs",
            MAX_PRIOR_ART_DIFFERENCE_CHARS,
        )

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "PriorArt":
        _exact_keys(raw, _PRIOR_ART_KEYS, "prior_art entry")
        return cls(name=raw["name"], how_this_differs=raw["how_this_differs"])

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "how_this_differs": self.how_this_differs}


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


@dataclass(frozen=True, kw_only=True)
class Idea:
    """One brand-new toy idea exactly as the Inventor wrote it."""

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

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("idea schema_version must be 1")
        bounded_line(self.title, "idea title", MAX_TITLE_CHARS)
        bounded_line(self.one_liner, "idea one_liner", MAX_ONE_LINER_CHARS)
        if self.held_form is not None:
            bounded_line(self.held_form, "idea held_form", MAX_HELD_FORM_CHARS)
        for name in ("what_you_do", "what_happens", "why_it_is_new"):
            bounded_paragraph(getattr(self, name), "idea %s" % name, MAX_PARAGRAPH_CHARS)
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

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "Idea":
        if not isinstance(raw, Mapping):
            raise ContractError("idea must be a JSON object")
        _exact_keys(
            {key: value for key, value in raw.items() if key not in _IDEA_OPTIONAL_KEYS},
            _IDEA_KEYS,
            "idea",
        )
        if raw["kind"] != DAYDREAM_IDEA_KIND:
            raise ContractError("idea kind must be %s" % DAYDREAM_IDEA_KIND)
        if isinstance(raw["prior_art"], (str, Mapping)) or not isinstance(
            raw["prior_art"], Sequence
        ):
            raise ContractError("idea prior_art must be a list of entries")
        prior_art = tuple(PriorArt.parse(entry) for entry in raw["prior_art"])
        return cls(
            schema_version=raw["schema_version"],
            title=raw["title"],
            one_liner=raw["one_liner"],
            what_you_do=raw["what_you_do"],
            what_happens=raw["what_happens"],
            why_it_is_new=raw["why_it_is_new"],
            prior_art=prior_art,
            taste_fit=TasteFit.parse(raw["taste_fit"]),
            parts_estimate=raw["parts_estimate"],
            keywords=raw["keywords"],
            held_form=raw.get("held_form"),
        )

    def to_dict(self) -> Dict[str, Any]:
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
    lines = [
        "Daydreamed by %s (%s). Build this new toy." % (inventor_name, inventor_id),
        "",
        "Title: %s" % idea.title,
        "In one line: %s" % idea.one_liner,
    ]
    if idea.held_form is not None:
        lines.append("What it looks like: %s" % idea.held_form)
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

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("sealed daydream schema_version must be 1")
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
        _exact_keys(raw, _SEAL_KEYS, "sealed daydream")
        return cls(
            schema_version=raw["schema_version"],
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
        return {
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

    @property
    def sha256(self) -> str:
        return hashlib.sha256(canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


__all__ = [
    "CREATED_AT_FORMAT",
    "DAYDREAM_IDEA_KIND",
    "DAYDREAM_SEAL_KIND",
    "DaydreamError",
    "Idea",
    "NOVELTY_STATUSES",
    "NoveltyNeighbor",
    "NoveltyReport",
    "PriorArt",
    "SealedDaydream",
    "TasteFit",
    "bounded_line",
    "bounded_paragraph",
    "canonical_json",
    "generate_daydream_id",
    "render_brief",
    "require_created_at",
    "require_daydream_id",
    "require_inventor_id",
]
