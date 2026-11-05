"""Pure, deterministic per-part colour reads from sealed STEP bytes.

Make writes assembly STEP through ``cadgen``, which stores a part's colour as
XCAF surface style.  Release needs those exact colours to describe the shop
listing's rendered thumbnail, so this module reads them back from the sealed
bytes with only the standard library, exactly like :mod:`workshop.make.cad.mesh`.

Colour space is the one contract worth stating out loud.  ``COLOUR_RGB``
holds sRGB display values: ``cadgen.color.srgb`` hands ``build123d.Color`` the
hex's channels, OpenCascade writes them unchanged, and every STEP viewer and
the shop show them as that hex.  STEPs written before 2026-11-05 hold the
same hex converted to **linear** RGB (``cadgen`` then pre-converted), which
opens far too dark; :func:`is_legacy_linear` recognises such a colour exactly,
every channel the linear value of a byte, and :func:`displayed_hex` reads it as
the hex it was authored from, so older sealed STEPs still read correctly.

Every read is fail-closed.  A colour that cannot be tied to exactly one named
part, a style chain this reader does not fully understand, or a channel outside
``0..1`` is dropped rather than guessed at: an omitted part keeps whatever the
shop already renders, while a wrong colour would be published.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterator, List, Mapping, Optional, Sequence, Tuple


__all__ = [
    "StepPartColor",
    "displayed_hex",
    "is_legacy_linear",
    "linear_to_srgb_hex",
    "read_step_part_colors",
    "srgb_channels_hex",
]


_MAX_STEP_BYTES = 64 * 1024 * 1024
_INSTANCE = re.compile(r"^#(\d+)\s*=\s*(.*)$", re.DOTALL)
_SIMPLE_ENTITY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)$", re.DOTALL)
_REFERENCE = re.compile(r"^#(\d+)$")
# A representation groups the geometry a style can be attached to. Every STEP
# flavour Make emits names it ``*_REPRESENTATION``; the shared shape is
# ``NAME(label, (items...), context)``.
_REPRESENTATION_SUFFIX = "REPRESENTATION"
_TYPE_HEAD = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
# A STEP is overwhelmingly geometry. Only these entity types carry a colour or
# the identity a colour hangs off, so every other record is counted for
# duplicate ids and then skipped without splitting its arguments.
_RELEVANT = frozenset(
    (
        "COLOUR_RGB",
        "FILL_AREA_STYLE",
        "FILL_AREA_STYLE_COLOUR",
        "OVER_RIDING_STYLED_ITEM",
        "PRESENTATION_STYLE_ASSIGNMENT",
        "PRODUCT",
        "PRODUCT_DEFINITION",
        "PRODUCT_DEFINITION_FORMATION",
        "PRODUCT_DEFINITION_SHAPE",
        "SHAPE_DEFINITION_REPRESENTATION",
        "STYLED_ITEM",
        "SURFACE_SIDE_STYLE",
        "SURFACE_STYLE_FILL_AREA",
        "SURFACE_STYLE_USAGE",
    )
)


@dataclass(frozen=True)
class StepPartColor:
    """One part name bound to one exact surface colour.

    ``channels`` are the raw 0..1 values sealed in the STEP.  build123d writes
    the values a designer passed to ``Color`` unchanged, and every viewer and
    the shop display them as sRGB.  ``hex`` is that displayed ``#rrggbb``, or
    for a legacy linear colour the hex it was authored from
    (:func:`displayed_hex`).
    """

    name: str
    hex: str
    channels: Tuple[float, float, float]


def srgb_channels_hex(rgb: Sequence[float]) -> str:
    """Return the ``#rrggbb`` a viewer shows for raw sRGB ``rgb`` channels."""

    if len(rgb) != 3:
        raise ValueError("a colour requires exactly three channels")
    channels = []
    for value in rgb:
        if not isinstance(value, float) or value != value or not 0.0 <= value <= 1.0:
            raise ValueError("colour channel is outside 0..1")
        # Round half up like the viewer, not to even like Python.
        channels.append(max(0, min(255, int(value * 255.0 + 0.5))))
    return "#%02x%02x%02x" % tuple(channels)


def _srgb_to_linear(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


_LINEAR_BYTES = tuple(_srgb_to_linear(k / 255.0) for k in range(256))
# OpenCascade keeps a colour in float32 and build123d rounds it to 7 digits,
# so a legacy channel strays up to 5e-8 from its byte's linear value; no
# k/255 lies within 1.04e-6 of one.
_LEGACY_TOLERANCE = 2e-7


def _is_linear_byte(value: float) -> bool:
    low, high = 0, 255
    while low < high:
        middle = (low + high) // 2
        if _LINEAR_BYTES[middle] < value:
            low = middle + 1
        else:
            high = middle
    return any(
        abs(_LINEAR_BYTES[k] - value) <= _LEGACY_TOLERANCE
        for k in (low - 1, low)
        if 0 <= k <= 255
    )


def is_legacy_linear(rgb: Sequence[float]) -> bool:
    """True for a colour sealed in the pre-2026-11-05 linear convention.

    Every channel is exactly the linear value of a byte and at least one is
    neither 0 nor 1, where the two conventions agree.  ``cadgen.color``
    applies the same test on the authoring side.
    """

    if len(rgb) != 3:
        return False
    channels = [float(value) for value in rgb]
    if all(value in (0.0, 1.0) for value in channels):
        return False
    return all(_is_linear_byte(value) for value in channels)


def displayed_hex(rgb: Sequence[float]) -> str:
    """Return the ``#rrggbb`` sealed channels stand for.

    Channels are sRGB and shown as they are; a legacy linear colour is shown
    as the hex it was authored from.
    """

    if is_legacy_linear(rgb):
        return linear_to_srgb_hex(rgb)
    return srgb_channels_hex(rgb)


def linear_to_srgb_hex(rgb: Sequence[float]) -> str:
    """Return the ``#rrggbb`` for linear ``rgb`` channels (sRGB transfer applied).

    Kept for callers that hold genuinely linear channels; sealed STEP colours
    are read with :func:`displayed_hex` instead.
    """

    if len(rgb) != 3:
        raise ValueError("a linear colour requires exactly three channels")
    channels = []
    for value in rgb:
        if not isinstance(value, float) or value != value or not 0.0 <= value <= 1.0:
            raise ValueError("linear colour channel is outside 0..1")
        encoded = (
            value * 12.92
            if value <= 0.0031308
            else 1.055 * (value ** (1.0 / 2.4)) - 0.055
        )
        channels.append(max(0, min(255, round(encoded * 255.0))))
    return "#%02x%02x%02x" % tuple(channels)


def _strip_comments(text: str) -> str:
    """Drop ``/* ... */`` comments without touching quoted part names."""

    pieces = []
    start = 0
    index = 0
    quoted = False
    length = len(text)
    while index < length:
        character = text[index]
        if quoted:
            if character == "'":
                if index + 1 < length and text[index + 1] == "'":
                    index += 2
                    continue
                quoted = False
        elif character == "'":
            quoted = True
        elif character == "/" and index + 1 < length and text[index + 1] == "*":
            closing = text.find("*/", index + 2)
            pieces.append(text[start:index])
            pieces.append(" ")
            if closing < 0:
                return "".join(pieces)
            index = closing + 2
            start = index
            continue
        index += 1
    pieces.append(text[start:])
    return "".join(pieces)


def _decoded(content: bytes) -> str:
    if not isinstance(content, bytes):
        raise TypeError("STEP content must be bytes")
    if not content or len(content) > _MAX_STEP_BYTES:
        return ""
    # STEP part 21 is 7-bit ASCII with escapes; decode leniently so an exotic
    # header cannot hide the colours in the data section.
    return _strip_comments(content.decode("ascii", "replace"))


def _data_section(text: str) -> str:
    start = text.find("DATA;")
    if start < 0:
        return ""
    end = text.find("ENDSEC;", start)
    return text[start + len("DATA;") : end if end >= 0 else len(text)]


def _records(section: str) -> Iterator[str]:
    """Yield each ``#N = ...`` instance, honouring quoted semicolons."""

    start = 0
    quoted = False
    index = 0
    length = len(section)
    while index < length:
        character = section[index]
        if quoted:
            if character == "'":
                if index + 1 < length and section[index + 1] == "'":
                    index += 2
                    continue
                quoted = False
        elif character == "'":
            quoted = True
        elif character == ";":
            record = section[start:index].strip()
            if record:
                yield record
            start = index + 1
        index += 1


def _split_arguments(arguments: str) -> List[str]:
    values: List[str] = []
    depth = 0
    quoted = False
    start = 0
    index = 0
    length = len(arguments)
    while index < length:
        character = arguments[index]
        if quoted:
            if character == "'":
                if index + 1 < length and arguments[index + 1] == "'":
                    index += 2
                    continue
                quoted = False
        elif character == "'":
            quoted = True
        elif character in "([":
            depth += 1
        elif character in ")]":
            depth -= 1
        elif character == "," and depth == 0:
            values.append(arguments[start:index].strip())
            start = index + 1
        index += 1
    tail = arguments[start:].strip()
    if tail or values:
        values.append(tail)
    return values


def _sub_entities(body: str) -> Iterator[Tuple[str, str]]:
    """Yield ``(type, arguments)`` for a simple or complex entity body."""

    body = body.strip()
    simple = _SIMPLE_ENTITY.match(body)
    if simple is not None:
        yield simple.group(1).upper(), simple.group(2)
        return
    if not body.startswith("(") or not body.endswith(")"):
        return
    inner = body[1:-1]
    index = 0
    length = len(inner)
    while index < length:
        match = re.compile(r"[A-Za-z_][A-Za-z0-9_]*").match(inner, index)
        if match is None:
            index += 1
            continue
        name = match.group(0)
        cursor = match.end()
        while cursor < length and inner[cursor].isspace():
            cursor += 1
        if cursor >= length or inner[cursor] != "(":
            index = match.end()
            continue
        depth = 0
        quoted = False
        scan = cursor
        while scan < length:
            character = inner[scan]
            if quoted:
                if character == "'":
                    if scan + 1 < length and inner[scan + 1] == "'":
                        scan += 2
                        continue
                    quoted = False
            elif character == "'":
                quoted = True
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0:
                    break
            scan += 1
        if scan >= length:
            return
        yield name.upper(), inner[cursor + 1 : scan]
        index = scan + 1


def _parse(content: bytes) -> Dict[int, List[Tuple[str, List[str]]]]:
    entities: Dict[int, List[Tuple[str, List[str]]]] = {}
    seen: set = set()
    for record in _records(_data_section(_decoded(content))):
        instance = _INSTANCE.match(record)
        if instance is None:
            continue
        identifier = int(instance.group(1))
        if identifier in seen:
            # A duplicate instance id makes every reference ambiguous.
            return {}
        seen.add(identifier)
        body = instance.group(2).lstrip()
        head = _TYPE_HEAD.match(body)
        if head is not None:
            name = head.group(1).upper()
            if name not in _RELEVANT and not name.endswith(_REPRESENTATION_SUFFIX):
                continue
        entities[identifier] = [
            (name, _split_arguments(arguments))
            for name, arguments in _sub_entities(body)
        ]
    return entities


def _typed(
    entities: Mapping[int, List[Tuple[str, List[str]]]], identifier: Optional[int], name: str
) -> Optional[List[str]]:
    if identifier is None:
        return None
    for entity_name, arguments in entities.get(identifier, ()):
        if entity_name == name:
            return arguments
    return None


def _reference(value: str) -> Optional[int]:
    match = _REFERENCE.match(value.strip())
    return int(match.group(1)) if match is not None else None


def _references(value: str) -> List[int]:
    value = value.strip()
    if not value.startswith("(") or not value.endswith(")"):
        return []
    resolved = []
    for item in _split_arguments(value[1:-1]):
        identifier = _reference(item)
        if identifier is None:
            return []
        resolved.append(identifier)
    return resolved


def _string(value: str) -> Optional[str]:
    value = value.strip()
    if len(value) < 2 or not value.startswith("'") or not value.endswith("'"):
        return None
    return value[1:-1].replace("''", "'")


def _real(value: str) -> Optional[float]:
    try:
        return float(value.strip())
    except ValueError:
        return None


def _linear_rgb(
    entities: Mapping[int, List[Tuple[str, List[str]]]], identifier: int
) -> Optional[Tuple[float, float, float]]:
    arguments = _typed(entities, identifier, "COLOUR_RGB")
    if arguments is None or len(arguments) != 4:
        return None
    channels = tuple(_real(value) for value in arguments[1:])
    if any(
        channel is None or channel != channel or not 0.0 <= channel <= 1.0
        for channel in channels
    ):
        return None
    return channels  # type: ignore[return-value]


def _style_colour(
    entities: Mapping[int, List[Tuple[str, List[str]]]], style: int
) -> Optional[Tuple[float, float, float]]:
    """Walk one presentation style down to its single surface colour."""

    assignment = _typed(entities, style, "PRESENTATION_STYLE_ASSIGNMENT")
    if assignment is None or len(assignment) != 1:
        return None
    found: List[Tuple[float, float, float]] = []
    for usage in _references(assignment[0]):
        selections = _typed(entities, usage, "SURFACE_STYLE_USAGE")
        if selections is None or len(selections) != 2:
            continue
        side = _reference(selections[1])
        side_style = _typed(entities, side, "SURFACE_SIDE_STYLE")
        if side_style is None or len(side_style) != 2:
            continue
        for element in _references(side_style[1]):
            fill = _typed(entities, element, "SURFACE_STYLE_FILL_AREA")
            if fill is None or len(fill) != 1:
                continue
            area = _typed(entities, _reference(fill[0]), "FILL_AREA_STYLE")
            if area is None or len(area) != 2:
                continue
            for style_colour in _references(area[1]):
                colour = _typed(entities, style_colour, "FILL_AREA_STYLE_COLOUR")
                if colour is None or len(colour) != 2:
                    continue
                linear = _linear_rgb(entities, _reference(colour[1]) or -1)
                if linear is not None and linear not in found:
                    found.append(linear)
    return found[0] if len(found) == 1 else None


def _representation_of_item(
    entities: Mapping[int, List[Tuple[str, List[str]]]]
) -> Dict[int, int]:
    owner: Dict[int, int] = {}
    ambiguous = set()
    for identifier, definitions in entities.items():
        for name, arguments in definitions:
            if not name.endswith(_REPRESENTATION_SUFFIX) or len(arguments) != 3:
                continue
            for item in _references(arguments[1]):
                if owner.get(item, identifier) != identifier:
                    ambiguous.add(item)
                owner[item] = identifier
    for item in ambiguous:
        owner.pop(item, None)
    return owner


def _product_name_of_representation(
    entities: Mapping[int, List[Tuple[str, List[str]]]]
) -> Dict[int, str]:
    names: Dict[int, str] = {}
    ambiguous = set()
    for definitions in entities.values():
        for name, arguments in definitions:
            if name != "SHAPE_DEFINITION_REPRESENTATION" or len(arguments) != 2:
                continue
            representation = _reference(arguments[1])
            shape = _typed(entities, _reference(arguments[0]), "PRODUCT_DEFINITION_SHAPE")
            if representation is None or shape is None or len(shape) != 3:
                continue
            definition = _typed(
                entities, _reference(shape[2]), "PRODUCT_DEFINITION"
            )
            if definition is None or len(definition) != 4:
                continue
            formation = _typed(
                entities, _reference(definition[2]), "PRODUCT_DEFINITION_FORMATION"
            )
            if formation is None or len(formation) != 3:
                continue
            product = _typed(entities, _reference(formation[2]), "PRODUCT")
            if product is None or len(product) != 4:
                continue
            label = _string(product[1]) or _string(product[0])
            if not label:
                continue
            if names.get(representation, label) != label:
                ambiguous.add(representation)
            names[representation] = label
    for representation in ambiguous:
        names.pop(representation, None)
    return names


def read_step_part_colors(content: bytes) -> Dict[str, StepPartColor]:
    """Return every part name in ``content`` bound to exactly one colour.

    The mapping is keyed by the STEP ``PRODUCT`` name, which ``cadgen`` writes
    from the occurrence label Make already uses to name that part's mesh.  A
    part with no colour, an unreadable style chain, or two conflicting colours
    is absent from the result.
    """

    if not isinstance(content, bytes):
        raise TypeError("STEP content must be bytes")
    if b"COLOUR_RGB" not in content:
        # An unstyled STEP is the common case; it is not worth parsing.
        return {}
    entities = _parse(content)
    if not entities:
        return {}
    owner = _representation_of_item(entities)
    products = _product_name_of_representation(entities)
    if not products:
        return {}

    resolved: Dict[str, StepPartColor] = {}
    conflicting = set()
    for identifier, definitions in entities.items():
        for name, arguments in definitions:
            if name not in ("STYLED_ITEM", "OVER_RIDING_STYLED_ITEM"):
                continue
            if len(arguments) < 3:
                continue
            item = _reference(arguments[2])
            if item is None:
                continue
            representation = item if item in products else owner.get(item)
            product = products.get(representation) if representation is not None else None
            if product is None:
                continue
            colour: Optional[Tuple[float, float, float]] = None
            for style in _references(arguments[1]):
                candidate = _style_colour(entities, style)
                if candidate is None:
                    continue
                if colour is not None and colour != candidate:
                    colour = None
                    break
                colour = candidate
            if colour is None:
                continue
            try:
                value = StepPartColor(product, displayed_hex(colour), colour)
            except ValueError:
                continue
            if resolved.get(product, value) != value:
                conflicting.add(product)
            resolved[product] = value
    for product in conflicting:
        resolved.pop(product, None)
    return resolved
