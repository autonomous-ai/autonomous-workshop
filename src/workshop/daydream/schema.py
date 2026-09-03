"""Portable, deterministic validation for Daydream agent-authored JSON.

This module deliberately uses only the Python standard library.  The host
imports it directly and copies the exact same bytes beside the run-local
finalizer, so the native agent and the sealing host cannot drift onto subtly
different schemas.
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any, Mapping
from urllib.parse import urlsplit


DAYDREAM_IDEA_KIND = "autonomous-workshop.daydream-idea"
DAYDREAM_VERDICT_KIND = "autonomous-workshop.daydream-verdict"

LEGACY_VERDICT_CHECKS = (
    "silhouette_changes",
    "moving_part_visible_in_both_states",
    "travel_is_large",
    "body_reads_as_a_toy",
    "mechanism_is_not_dominant",
    "fits_the_route",
    "worth_owning",
)
THESIS_VERDICT_CHECKS = (
    "taste_fidelity",
    "opportunity_grounded",
    "mechanism_or_play_novelty",
    "anti_generic_signature",
    "proof_observable",
    "fits_the_route",
    "worth_building",
    "invent_handoff_clear",
)
PROOF_MODES = (
    "visual-form",
    "visual-state",
    "configuration-set",
    "tactile",
    "acoustic",
    "light-shadow",
    "rules-play",
)
ROUTE_FLOORS = ("spark", "forge", "quest")
RISK_KINDS = (
    "generic-form",
    "exposed-mechanism",
    "hidden-signature",
    "unclear-state-change",
    "too-many-parts",
    "tight-tolerance",
    "print-preflight",
    "taste-fit",
    "not-desirable",
    "weak-signal",
    "theme-only",
    "prior-art",
    "proof-mismatch",
    "route-fit",
    "invent-ambiguity",
    "other",
)

_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,31}$", re.ASCII)
_DAYDREAM_ID = re.compile(r"^daydream-\d{8}-\d{6}-[0-9a-f]{8}$", re.ASCII)
_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.ASCII)
_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

_IDEA_V1_REQUIRED = frozenset(
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
_IDEA_V1_OPTIONAL = frozenset(("held_form", "before_after"))
_IDEA_V2_KEYS = frozenset(
    (
        "schema_version",
        "kind",
        "title",
        "one_liner",
        "opportunity",
        "experience",
        "why_it_is_new",
        "prior_art",
        "taste_fit",
        "proof",
        "route_floor",
        "parts_estimate",
        "keywords",
    )
)
_OPPORTUNITY_KEYS = frozenset(
    ("world_scan", "human_tension", "why_now", "physical_opportunity")
)
_WORLD_SCAN_KEYS = frozenset(("observed_at", "scope", "evergreen", "signals"))
_WORLD_SIGNAL_KEYS = frozenset(("title", "url", "published_at", "insight"))
_EXPERIENCE_KEYS = frozenset(
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
_PROOF_KEYS = frozenset(("mode", "observable", "kill_criteria"))
_PRIOR_ART_V1_KEYS = frozenset(("name", "how_this_differs"))
_PRIOR_ART_V2_KEYS = frozenset(("name", "url", "observed_at", "how_this_differs"))
_TASTE_FIT_KEYS = frozenset(("honors", "steers_clear_of"))
_VERDICT_V1_KEYS = frozenset(
    ("schema_version", "kind", "decision", "checks", "confidence", "risks", "advice")
)
_VERDICT_V2_KEYS = frozenset(
    (
        "schema_version",
        "kind",
        "daydream_id",
        "idea_sha256",
        "taste_sha256",
        "route",
        "decision",
        "checks",
        "confidence",
        "risks",
        "advice",
    )
)


def _key_problems(raw: Any, expected: frozenset[str], label: str) -> list[str]:
    if not isinstance(raw, Mapping):
        return ["%s must be one JSON object" % label]
    missing = sorted(expected - set(raw))
    unknown = sorted(set(raw) - expected)
    problems: list[str] = []
    if missing:
        problems.append("%s missing keys: %s" % (label, ", ".join(missing)))
    if unknown:
        problems.append("%s unknown keys: %s" % (label, ", ".join(unknown)))
    return problems


def _line_problems(value: Any, label: str, maximum: int) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return ["%s must be a non-empty string" % label]
    problems: list[str] = []
    if len(value) > maximum:
        problems.append("%s is longer than %d characters" % (label, maximum))
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        problems.append("%s contains control characters" % label)
    return problems


def _paragraph_problems(value: Any, label: str, maximum: int) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return ["%s must be a non-empty string" % label]
    problems: list[str] = []
    if len(value) > maximum:
        problems.append("%s is longer than %d characters" % (label, maximum))
    if any(
        (ord(character) < 32 and character != "\n") or ord(character) == 127
        for character in value
    ):
        problems.append("%s contains control characters" % label)
    return problems


def _timestamp_problems(value: Any, label: str, *, nullable: bool = False) -> list[str]:
    if nullable and value is None:
        return []
    try:
        if (
            not isinstance(value, str)
            or datetime.strptime(value, _TIMESTAMP_FORMAT).strftime(_TIMESTAMP_FORMAT)
            != value
        ):
            raise ValueError
    except (TypeError, ValueError):
        return ["%s must be YYYY-MM-DDTHH:MM:SSZ%s" % (label, " or null" if nullable else "")]
    return []


def _url_problems(value: Any, label: str) -> list[str]:
    problems = _line_problems(value, label, 500)
    if problems:
        return problems
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username:
        return ["%s must be an http(s) URL without embedded credentials" % label]
    return []


def _line_list_problems(
    value: Any,
    label: str,
    *,
    minimum: int,
    maximum: int,
    item_maximum: int,
) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        return ["%s must list %d to %d lines" % (label, minimum, maximum)]
    problems: list[str] = []
    for index, item in enumerate(value):
        problems.extend(_line_problems(item, "%s[%d]" % (label, index), item_maximum))
    return problems


def _taste_fit_problems(raw: Any) -> list[str]:
    problems = _key_problems(raw, _TASTE_FIT_KEYS, "taste_fit")
    if problems:
        return problems
    for key in ("honors", "steers_clear_of"):
        problems.extend(
            _line_list_problems(
                raw[key], "taste_fit.%s" % key, minimum=1, maximum=5, item_maximum=200
            )
        )
    return problems


def _prior_art_problems(raw: Any, *, version: int) -> list[str]:
    if not isinstance(raw, list) or not 2 <= len(raw) <= 5:
        return ["prior_art must list 2 to 5 entries"]
    expected = _PRIOR_ART_V1_KEYS if version == 1 else _PRIOR_ART_V2_KEYS
    problems: list[str] = []
    for index, entry in enumerate(raw):
        label = "prior_art[%d]" % index
        entry_problems = _key_problems(entry, expected, label)
        problems.extend(entry_problems)
        if entry_problems:
            continue
        problems.extend(_line_problems(entry["name"], "%s.name" % label, 80))
        problems.extend(
            _line_problems(
                entry["how_this_differs"], "%s.how_this_differs" % label, 300
            )
        )
        if version == 2:
            problems.extend(_url_problems(entry["url"], "%s.url" % label))
            problems.extend(
                _timestamp_problems(entry["observed_at"], "%s.observed_at" % label)
            )
    return problems


def _keywords_problems(value: Any) -> list[str]:
    if not isinstance(value, list) or not 3 <= len(value) <= 8:
        return ["keywords must be 3 to 8 unique lowercase ASCII slugs"]
    if any(not isinstance(keyword, str) or _SLUG.fullmatch(keyword) is None for keyword in value):
        return ["keywords must be 3 to 8 unique lowercase ASCII slugs"]
    if len(set(value)) != len(value):
        return ["keywords must be 3 to 8 unique lowercase ASCII slugs"]
    return []


def _parts_problems(value: Any) -> list[str]:
    if type(value) is not int or not 1 <= value <= 12:
        return ["parts_estimate must be an integer from 1 to 12"]
    return []


def _world_scan_problems(raw: Any) -> list[str]:
    problems = _key_problems(raw, _WORLD_SCAN_KEYS, "opportunity.world_scan")
    if problems:
        return problems
    problems.extend(_timestamp_problems(raw["observed_at"], "opportunity.world_scan.observed_at"))
    problems.extend(_line_problems(raw["scope"], "opportunity.world_scan.scope", 500))
    if type(raw["evergreen"]) is not bool:
        problems.append("opportunity.world_scan.evergreen must be true or false")
    signals = raw["signals"]
    if not isinstance(signals, list) or not 2 <= len(signals) <= 6:
        problems.append("opportunity.world_scan.signals must list 2 to 6 sources")
        return problems
    seen_urls: set[str] = set()
    for index, signal in enumerate(signals):
        label = "opportunity.world_scan.signals[%d]" % index
        signal_problems = _key_problems(signal, _WORLD_SIGNAL_KEYS, label)
        problems.extend(signal_problems)
        if signal_problems:
            continue
        problems.extend(_line_problems(signal["title"], "%s.title" % label, 160))
        problems.extend(_url_problems(signal["url"], "%s.url" % label))
        problems.extend(
            _timestamp_problems(signal["published_at"], "%s.published_at" % label, nullable=True)
        )
        problems.extend(_line_problems(signal["insight"], "%s.insight" % label, 300))
        if isinstance(signal["url"], str):
            if signal["url"] in seen_urls:
                problems.append("%s.url duplicates another world signal" % label)
            seen_urls.add(signal["url"])
    return problems


def _opportunity_problems(raw: Any) -> list[str]:
    problems = _key_problems(raw, _OPPORTUNITY_KEYS, "opportunity")
    if problems:
        return problems
    problems.extend(_world_scan_problems(raw["world_scan"]))
    for key in ("human_tension", "why_now", "physical_opportunity"):
        problems.extend(_paragraph_problems(raw[key], "opportunity.%s" % key, 600))
    return problems


def _experience_problems(raw: Any) -> list[str]:
    problems = _key_problems(raw, _EXPERIENCE_KEYS, "experience")
    if problems:
        return problems
    for key in _EXPERIENCE_KEYS:
        problems.extend(_paragraph_problems(raw[key], "experience.%s" % key, 600))
    return problems


def _proof_problems(raw: Any) -> list[str]:
    problems = _key_problems(raw, _PROOF_KEYS, "proof")
    if problems:
        return problems
    if raw["mode"] not in PROOF_MODES:
        problems.append("proof.mode must be one of %s" % (PROOF_MODES,))
    problems.extend(_paragraph_problems(raw["observable"], "proof.observable", 600))
    problems.extend(
        _line_list_problems(
            raw["kill_criteria"], "proof.kill_criteria", minimum=2, maximum=5, item_maximum=300
        )
    )
    return problems


def idea_problems(raw: Any) -> list[str]:
    """Return every bounded schema problem in one parsed ``IDEA.json`` value."""

    if not isinstance(raw, Mapping):
        return ["IDEA.json must be one JSON object"]
    version = raw.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        return ["schema_version must be 1 or 2"]
    if version == 1:
        present = set(raw)
        problems: list[str] = []
        missing = sorted(_IDEA_V1_REQUIRED - present)
        unknown = sorted(present - _IDEA_V1_REQUIRED - _IDEA_V1_OPTIONAL)
        if missing:
            problems.append("IDEA.json missing keys: %s" % ", ".join(missing))
        if unknown:
            problems.append("IDEA.json unknown keys: %s" % ", ".join(unknown))
        if problems:
            return problems
        line_bounds = {"title": 60, "one_liner": 200, "held_form": 240, "before_after": 300}
        for key, maximum in line_bounds.items():
            if key in raw:
                problems.extend(_line_problems(raw[key], key, maximum))
        for key in ("what_you_do", "what_happens", "why_it_is_new"):
            problems.extend(_paragraph_problems(raw[key], key, 600))
    else:
        problems = _key_problems(raw, _IDEA_V2_KEYS, "IDEA.json")
        if problems:
            return problems
        problems.extend(_line_problems(raw["title"], "title", 60))
        problems.extend(_line_problems(raw["one_liner"], "one_liner", 200))
        problems.extend(_opportunity_problems(raw["opportunity"]))
        problems.extend(_experience_problems(raw["experience"]))
        problems.extend(_paragraph_problems(raw["why_it_is_new"], "why_it_is_new", 600))
        problems.extend(_proof_problems(raw["proof"]))
        if raw["route_floor"] not in ROUTE_FLOORS:
            problems.append("route_floor must be one of %s" % (ROUTE_FLOORS,))
    if raw["kind"] != DAYDREAM_IDEA_KIND:
        problems.append("kind must be %s" % DAYDREAM_IDEA_KIND)
    problems.extend(_prior_art_problems(raw["prior_art"], version=version))
    problems.extend(_taste_fit_problems(raw["taste_fit"]))
    problems.extend(_parts_problems(raw["parts_estimate"]))
    problems.extend(_keywords_problems(raw["keywords"]))
    return problems


def verdict_problems(raw: Any) -> list[str]:
    """Return every bounded schema problem in one parsed ``VERDICT.json`` value."""

    if not isinstance(raw, Mapping):
        return ["VERDICT.json must be one JSON object"]
    version = raw.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        return ["schema_version must be 1 or 2"]
    expected = _VERDICT_V1_KEYS if version == 1 else _VERDICT_V2_KEYS
    problems = _key_problems(raw, expected, "VERDICT.json")
    if problems:
        return problems
    if raw["kind"] != DAYDREAM_VERDICT_KIND:
        problems.append("kind must be %s" % DAYDREAM_VERDICT_KIND)
    if raw["decision"] not in ("build", "dream-again"):
        problems.append("decision must be build or dream-again")
    checks = raw["checks"]
    expected_checks = LEGACY_VERDICT_CHECKS if version == 1 else THESIS_VERDICT_CHECKS
    if not isinstance(checks, Mapping) or set(checks) != set(expected_checks):
        problems.append("checks must hold exactly these keys: %s" % ", ".join(expected_checks))
    elif any(type(value) is not bool for value in checks.values()):
        problems.append("every check must be true or false")
    elif raw["decision"] == "build" and not all(checks.values()):
        failed = ", ".join(sorted(name for name, value in checks.items() if not value))
        problems.append("a build verdict requires every check to be true; failed: %s" % failed)
    confidence = raw["confidence"]
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not math.isfinite(float(confidence))
        or not 0.0 <= float(confidence) <= 1.0
    ):
        problems.append("confidence must be a finite number from 0.0 to 1.0")
    risks = raw["risks"]
    if not isinstance(risks, list) or len(risks) > 6:
        problems.append("risks must be a list of at most 6 entries")
    else:
        if raw["decision"] == "dream-again" and not risks:
            problems.append("a dream-again verdict must name at least one risk")
        for index, risk in enumerate(risks):
            label = "risks[%d]" % index
            risk_problems = _key_problems(risk, frozenset(("kind", "detail")), label)
            problems.extend(risk_problems)
            if risk_problems:
                continue
            if risk["kind"] not in RISK_KINDS:
                problems.append("%s.kind must be one of %s" % (label, RISK_KINDS))
            problems.extend(_line_problems(risk["detail"], "%s.detail" % label, 400))
    problems.extend(_line_problems(raw["advice"], "advice", 400))
    if version == 2:
        if not isinstance(raw["daydream_id"], str) or _DAYDREAM_ID.fullmatch(raw["daydream_id"]) is None:
            problems.append("daydream_id is invalid")
        for key in ("idea_sha256", "taste_sha256"):
            if not isinstance(raw[key], str) or _SHA256.fullmatch(raw[key]) is None:
                problems.append("%s must be a lowercase sha256" % key)
        if raw["route"] not in ROUTE_FLOORS:
            problems.append("route must be one of %s" % (ROUTE_FLOORS,))
    return problems


__all__ = [
    "DAYDREAM_IDEA_KIND",
    "DAYDREAM_VERDICT_KIND",
    "LEGACY_VERDICT_CHECKS",
    "PROOF_MODES",
    "RISK_KINDS",
    "ROUTE_FLOORS",
    "THESIS_VERDICT_CHECKS",
    "idea_problems",
    "verdict_problems",
]
