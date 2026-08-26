"""Validated Wish intake contract and opaque identifier generation."""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

from workshop.errors import ContractError
from workshop._validation import require_json_mapping


MAX_PRODUCT_ID_CHARS = 256
MAX_OBJECTIVE_CHARS = 50_000


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


@dataclass(frozen=True)
class Wish:
    schema_version: int
    product_id: str
    objective: str
    constraints: Mapping[str, Any] = field(default_factory=dict)
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "constraints", _copy_mapping(self.constraints, "wish constraints")
        )
        object.__setattr__(self, "context", _copy_mapping(self.context, "wish context"))
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

    @classmethod
    def create(
        cls,
        product_id: str,
        objective: str,
        constraints: Optional[Mapping[str, Any]] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> "Wish":
        return cls(
            1,
            product_id,
            objective,
            constraints if constraints is not None else {},
            context if context is not None else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return {
            "schema_version": self.schema_version,
            "product_id": self.product_id,
            "objective": self.objective,
            "constraints": _copy_mapping(self.constraints, "wish constraints"),
            "context": _copy_mapping(self.context, "wish context"),
        }
