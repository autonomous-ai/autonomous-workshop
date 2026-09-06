"""Validated Wish intake contract and opaque identifier generation."""

from __future__ import annotations

import json
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence

from workshop.errors import ContractError
from workshop._validation import require_json_mapping


MAX_PRODUCT_ID_CHARS = 256
MAX_OBJECTIVE_CHARS = 50_000

# Reference images ride the Wish as immutable run inputs under this directory.
WISH_REFERENCES_DIRECTORY = "wish-references"
MAX_WISH_REFERENCES = 8
MAX_WISH_REFERENCE_BYTES = 12 * 1024 * 1024
MAX_WISH_REFERENCE_TOTAL_BYTES = 48 * 1024 * 1024
MIN_WISH_REFERENCE_SIDE_PX = 16
MAX_WISH_REFERENCE_SIDE_PX = 16_384
MAX_WISH_REFERENCE_PIXELS = 50_000_000
WISH_REFERENCE_MEDIA_TYPES: Mapping[str, str] = MappingProxyType(
    {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
)
_REFERENCE_NAME = re.compile(
    r"^ref-(?P<index>0[1-9]|[1-9][0-9])-"
    r"(?P<slug>[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?)"
    r"\.(?P<extension>png|jpg|webp)$"
)
_REFERENCE_FIELDS = frozenset(
    ("name", "sha256", "media_type", "size", "width", "height")
)


def generate_wish_id(
    *, moment: Optional[datetime] = None, token: Optional[str] = None
) -> str:
    """Create an opaque local identifier without putting Wish words in paths."""

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
        raise ContractError("Wish id token must be eight lowercase hexadecimal characters")
    return "wish-%s-%s" % (observed.strftime("%Y%m%d-%H%M%S"), suffix)


def _bounded_text(
    value: str, label: str, maximum: int, allow_format_controls: bool = False
) -> str:
    permitted_controls = "\n\r\t" if allow_format_controls else ""
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(
            ord(character) < 32 and character not in permitted_controls
            for character in value
        )
        or any(ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded, non-empty, and control-free" % label)
    return value


def _copy_mapping(value: Mapping[str, Any], label: str) -> Dict[str, Any]:
    require_json_mapping(value, label)
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    copied = json.loads(payload)
    if not isinstance(copied, dict):
        raise ContractError("%s must be an object" % label)
    return copied


def _bounded_int(value: Any, label: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ContractError("%s must be an integer between %d and %d" % (label, low, high))
    return value


@dataclass(frozen=True)
class WishReference:
    """One reference image attached to a Wish, identified by exact bytes.

    The bytes themselves never enter the Wish document; they are materialized
    by the host as the immutable run input ``wish-references/<name>`` and are
    bound here by size and SHA-256 so every checkpoint can re-verify them.
    """

    name: str
    sha256: str
    media_type: str
    size: int
    width: int
    height: int

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        if not isinstance(self.name, str) or _REFERENCE_NAME.fullmatch(self.name) is None:
            raise ContractError(
                "wish reference name must look like ref-NN-<slug>.png, .jpg, or .webp"
            )
        if (
            not isinstance(self.sha256, str)
            or len(self.sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.sha256)
        ):
            raise ContractError("wish reference sha256 must be 64 lowercase hex characters")
        if self.media_type not in WISH_REFERENCE_MEDIA_TYPES:
            raise ContractError(
                "wish reference media_type must be one of: %s"
                % ", ".join(WISH_REFERENCE_MEDIA_TYPES)
            )
        if not self.name.endswith("." + WISH_REFERENCE_MEDIA_TYPES[self.media_type]):
            raise ContractError("wish reference name extension must match its media type")
        _bounded_int(self.size, "wish reference size", 1, MAX_WISH_REFERENCE_BYTES)
        _bounded_int(
            self.width,
            "wish reference width",
            MIN_WISH_REFERENCE_SIDE_PX,
            MAX_WISH_REFERENCE_SIDE_PX,
        )
        _bounded_int(
            self.height,
            "wish reference height",
            MIN_WISH_REFERENCE_SIDE_PX,
            MAX_WISH_REFERENCE_SIDE_PX,
        )
        if self.width * self.height > MAX_WISH_REFERENCE_PIXELS:
            raise ContractError(
                "wish reference must be at most %d pixels" % MAX_WISH_REFERENCE_PIXELS
            )

    @property
    def index(self) -> int:
        match = _REFERENCE_NAME.fullmatch(self.name)
        assert match is not None
        return int(match.group("index"))

    @property
    def path(self) -> str:
        """The run-relative path the host materializes the bytes at."""

        return "%s/%s" % (WISH_REFERENCES_DIRECTORY, self.name)

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return {
            "name": self.name,
            "sha256": self.sha256,
            "media_type": self.media_type,
            "size": self.size,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_value(cls, value: Any, label: str) -> "WishReference":
        if isinstance(value, WishReference):
            value.assert_valid()
            return value
        require_json_mapping(value, label)
        if set(value) != _REFERENCE_FIELDS:
            raise ContractError(
                "%s must carry exactly: %s" % (label, ", ".join(sorted(_REFERENCE_FIELDS)))
            )
        return cls(**{key: value[key] for key in sorted(_REFERENCE_FIELDS)})


def _references(value: Any) -> tuple[WishReference, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Sequence):
        raise ContractError("wish references must be a list")
    if len(value) > MAX_WISH_REFERENCES:
        raise ContractError("wish references must be at most %d" % MAX_WISH_REFERENCES)
    items = tuple(WishReference.from_value(item, "wish reference") for item in value)
    for position, item in enumerate(items, start=1):
        if item.index != position:
            raise ContractError("wish references must be numbered ref-01, ref-02, ... in order")
    digests = [item.sha256 for item in items]
    if len(set(digests)) != len(digests):
        raise ContractError("wish references must not repeat the same bytes")
    if sum(item.size for item in items) > MAX_WISH_REFERENCE_TOTAL_BYTES:
        raise ContractError(
            "wish references must total at most %d bytes" % MAX_WISH_REFERENCE_TOTAL_BYTES
        )
    return items


@dataclass(frozen=True)
class Wish:
    schema_version: int
    product_id: str
    objective: str
    constraints: Mapping[str, Any] = field(default_factory=dict)
    context: Mapping[str, Any] = field(default_factory=dict)
    references: tuple[WishReference, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "constraints", _copy_mapping(self.constraints, "wish constraints")
        )
        object.__setattr__(self, "context", _copy_mapping(self.context, "wish context"))
        object.__setattr__(self, "references", _references(self.references))
        self.assert_valid()

    def assert_valid(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("wish schema_version must be 1")
        _bounded_text(self.product_id, "wish product_id", MAX_PRODUCT_ID_CHARS)
        if any(character in "/\\" for character in self.product_id):
            raise ContractError("wish product_id must not contain path separators")
        _bounded_text(
            self.objective,
            "wish objective",
            MAX_OBJECTIVE_CHARS,
            allow_format_controls=True,
        )
        _copy_mapping(self.constraints, "wish constraints")
        _copy_mapping(self.context, "wish context")
        _references(self.references)

    @classmethod
    def create(
        cls,
        product_id: str,
        objective: str,
        constraints: Optional[Mapping[str, Any]] = None,
        context: Optional[Mapping[str, Any]] = None,
        references: Optional[Sequence[Any]] = None,
    ) -> "Wish":
        return cls(
            1,
            product_id,
            objective,
            constraints if constraints is not None else {},
            context if context is not None else {},
            references if references is not None else (),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return the canonical document; ``references`` appears only when present.

        Omitting an empty list keeps the canonical bytes, and therefore the
        Wish SHA-256, of every image-less Wish identical to the pre-reference
        contract.
        """

        self.assert_valid()
        document = {
            "schema_version": self.schema_version,
            "product_id": self.product_id,
            "objective": self.objective,
            "constraints": _copy_mapping(self.constraints, "wish constraints"),
            "context": _copy_mapping(self.context, "wish context"),
        }
        if self.references:
            document["references"] = [item.to_dict() for item in self.references]
        return document
