"""Canonical digest of an ISO 10303-21 (STEP) file, independent of entity numbering.

Open CASCADE emits presentation-style entities in pointer-hash order, so two
exports of one identical model differ in which ``#id`` each STYLED_ITEM
carries and references.  Byte comparison therefore rejects a faithful fresh
re-export.  This module hashes the entity graph instead: every entity gets a
structural key from its type, its literal arguments, and the keys of the
entities it references (a few Weisfeiler-Lehman refinement rounds), and the
digest covers the HEADER text plus the sorted multiset of final keys.  Two
files are canonically equal exactly when their entity graphs are isomorphic
with identical literals; any changed coordinate, name, colour, or wiring to a
structurally different entity changes the digest.
"""

from __future__ import annotations

import hashlib
import re

_REF_RE = re.compile(r"#(\d+)")
_ROUNDS = 4
MAX_CANONICAL_STEP_BYTES = 256 * 1024 * 1024


class StepCanonicalError(ValueError):
    """The bytes are not a well-formed Part 21 exchange structure."""


def _split_sections(text: str) -> tuple[str, str]:
    upper = text.upper()
    data_at = upper.find("\nDATA;")
    end_at = upper.rfind("ENDSEC;")
    if not upper.startswith("ISO-10303-21;") or data_at < 0 or end_at <= data_at:
        raise StepCanonicalError("not a Part 21 exchange structure")
    header = text[:data_at]
    data = text[data_at + len("\nDATA;") : end_at]
    return header, data


def _statements(data: str) -> list[str]:
    """Split the DATA section into statements on ``;`` outside strings.

    Whitespace outside strings is dropped so line wrapping never matters.
    Part 21 strings are single-quoted and escape a quote by doubling it.
    """

    statements: list[str] = []
    current: list[str] = []
    in_string = False
    index = 0
    length = len(data)
    while index < length:
        char = data[index]
        if in_string:
            current.append(char)
            if char == "'":
                if index + 1 < length and data[index + 1] == "'":
                    current.append("'")
                    index += 1
                else:
                    in_string = False
        elif char == "'":
            in_string = True
            current.append(char)
        elif char == ";":
            statement = "".join(current)
            if statement:
                statements.append(statement)
            current = []
        elif not char.isspace():
            current.append(char)
        index += 1
    if in_string:
        raise StepCanonicalError("unterminated string in DATA section")
    if "".join(current).strip():
        raise StepCanonicalError("trailing DATA content without terminator")
    return statements


def _parse_entities(data: str) -> dict[int, str]:
    entities: dict[int, str] = {}
    for statement in _statements(data):
        if not statement.startswith("#"):
            raise StepCanonicalError("DATA statement is not an entity instance")
        equals = statement.find("=")
        if equals < 1:
            raise StepCanonicalError("entity instance lacks an assignment")
        try:
            identifier = int(statement[1:equals])
        except ValueError as exc:
            raise StepCanonicalError("entity identifier is not an integer") from exc
        if identifier in entities:
            raise StepCanonicalError("duplicate entity identifier #%d" % identifier)
        entities[identifier] = statement[equals + 1 :]
    if not entities:
        raise StepCanonicalError("DATA section holds no entity")
    return entities


def _template_and_refs(body: str) -> tuple[str, tuple[int, ...]]:
    """Replace every ``#n`` outside strings with a slot; return referenced ids."""

    parts: list[str] = []
    refs: list[int] = []
    in_string = False
    index = 0
    length = len(body)
    while index < length:
        char = body[index]
        if in_string:
            parts.append(char)
            if char == "'":
                in_string = False
        elif char == "'":
            in_string = True
            parts.append(char)
        elif char == "#":
            match = _REF_RE.match(body, index)
            if match is None:
                raise StepCanonicalError("malformed entity reference")
            refs.append(int(match.group(1)))
            parts.append("\x00")
            index = match.end()
            continue
        else:
            parts.append(char)
        index += 1
    return "".join(parts), tuple(refs)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_step_digest(content: bytes) -> str:
    """Return the numbering-independent digest of one STEP file."""

    if not isinstance(content, (bytes, bytearray)):
        raise StepCanonicalError("STEP content must be bytes")
    if len(content) > MAX_CANONICAL_STEP_BYTES:
        raise StepCanonicalError("STEP content exceeds the canonical digest bound")
    text = bytes(content).decode("utf-8", errors="strict")
    header, data = _split_sections(text)
    entities = _parse_entities(data)
    templates: dict[int, str] = {}
    references: dict[int, tuple[int, ...]] = {}
    for identifier, body in entities.items():
        template, refs = _template_and_refs(body)
        for ref in refs:
            if ref not in entities:
                raise StepCanonicalError("dangling entity reference #%d" % ref)
        templates[identifier] = template
        references[identifier] = refs
    keys = {identifier: _digest(templates[identifier]) for identifier in entities}
    for _ in range(_ROUNDS):
        keys = {
            identifier: _digest(
                templates[identifier]
                + "|"
                + "|".join(keys[ref] for ref in references[identifier])
            )
            for identifier in entities
        }
    header_text = "".join(header.split())
    summary = hashlib.sha256()
    summary.update(_digest(header_text).encode("ascii"))
    summary.update(b"|")
    for key in sorted(keys.values()):
        summary.update(key.encode("ascii"))
        summary.update(b"\n")
    return summary.hexdigest()


def canonical_step_equal(left: bytes, right: bytes) -> bool:
    """Whether two STEP files describe the same entity graph."""

    return canonical_step_digest(left) == canonical_step_digest(right)
