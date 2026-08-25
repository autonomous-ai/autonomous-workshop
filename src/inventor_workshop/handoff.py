"""Content-bound Manager-to-Inventor process handoff.

The customer CLI launches an inventor as a child process.  This module keeps
that boundary structured: the exact Manager-owned Wish travels over stdin,
while the assignment and routing decision hashes remain attached to the child
result.  No Wish text is interpolated into a shell command.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, TextIO, Tuple

from .errors import ContractError
from .make import Wish
from .models import require_json_mapping, require_sha256
from .world_service import WorldInventInputs, WorldPlaytestEvidence


HANDOFF_KIND = "autonomous-workshop-manager-assignment"
PUBLICATION_POLICY_KIND = "autonomous-workshop-publication-policy"
MAX_HANDOFF_BYTES = 1_000_000
RESULT_BINDING_FIELD = "manager_assignment"


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Manager assignment handoff must be JSON-safe") from exc


def _sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _bounded_identifier(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 256
        or value != value.strip()
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be a bounded identifier" % label)
    return value


def _entrypoint(value: Sequence[str]) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes, Mapping)):
        raise ContractError("Manager assignment entrypoint must be a sequence")
    try:
        copied = tuple(value)
    except TypeError as exc:
        raise ContractError("Manager assignment entrypoint must be a sequence") from exc
    if not copied or len(copied) > 100:
        raise ContractError("Manager assignment entrypoint must contain 1 to 100 values")
    for item in copied:
        if (
            not isinstance(item, str)
            or not item.strip()
            or len(item) > 4_000
            or any(ord(character) < 32 or ord(character) == 127 for character in item)
        ):
            raise ContractError(
                "Manager assignment entrypoint values must be bounded, non-empty text"
            )
    return copied


def _current_inventor_identity(root: Path) -> Tuple[str, str, str, Tuple[str, ...]]:
    """Recompute the bounded inventor identity used by Manager routing."""

    requested = Path(root)
    if not requested.is_absolute() or requested.is_symlink() or not requested.is_dir():
        raise ContractError(
            "Manager assignment inventor root must be an absolute regular directory"
        )
    resolved = requested.resolve(strict=True)
    # Import lazily so this process-boundary module does not depend on Manager
    # construction at module import time. These are the canonical snapshot
    # functions that produced RoutingDecision.selected.
    from .manager import _implementation_sha256, _load_manifest_snapshot
    from .taste import load_taste

    manifest, manifest_sha256 = _load_manifest_snapshot(resolved / "inventor.json")
    if manifest.inventor_id != resolved.name:
        raise ContractError(
            "Manager assignment inventor manifest belongs to a different directory"
        )
    return (
        manifest_sha256,
        load_taste(resolved).sha256,
        _implementation_sha256(resolved),
        _entrypoint(manifest.entrypoint),
    )


def _copy_mapping(value: Mapping[str, Any], label: str) -> Dict[str, Any]:
    require_json_mapping(value, label)
    try:
        copied = json.loads(_canonical_json(value).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:  # pragma: no cover - canonical JSON
        raise ContractError("%s must be a JSON object" % label) from exc
    if not isinstance(copied, dict):
        raise ContractError("%s must be a JSON object" % label)
    return copied


@dataclass(frozen=True)
class PublicationPolicy:
    """One Manager-owned, monotonic authorization for Factory visibility."""

    visibility: str
    authorization: str
    schema_version: int = 1
    kind: str = PUBLICATION_POLICY_KIND
    policy_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("publication policy schema_version must be 1")
        if self.kind != PUBLICATION_POLICY_KIND:
            raise ContractError("publication policy kind is invalid")
        if self.visibility not in ("draft", "public"):
            raise ContractError("publication policy visibility must be draft or public")
        if self.authorization not in (
            "wish",
            "explicit-resume-publish",
            "legacy-fail-safe",
        ):
            raise ContractError("publication policy authorization is invalid")
        if self.authorization == "explicit-resume-publish" and self.visibility != "public":
            raise ContractError("explicit resume publication must authorize public visibility")
        if self.authorization == "legacy-fail-safe" and self.visibility != "draft":
            raise ContractError("legacy publication policy must fail safe to draft")
        object.__setattr__(self, "policy_sha256", _sha256(self._identity_dict()))

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "visibility": self.visibility,
            "authorization": self.authorization,
        }

    def to_dict(self) -> Dict[str, Any]:
        payload = self._identity_dict()
        payload["policy_sha256"] = self.policy_sha256
        return payload

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PublicationPolicy":
        payload = _copy_mapping(value, "publication policy")
        if set(payload) != {
            "schema_version",
            "kind",
            "visibility",
            "authorization",
            "policy_sha256",
        }:
            raise ContractError("publication policy fields are invalid")
        policy = cls(
            visibility=payload["visibility"],
            authorization=payload["authorization"],
            schema_version=payload["schema_version"],
            kind=payload["kind"],
        )
        if payload["policy_sha256"] != policy.policy_sha256:
            raise ContractError("publication policy identity is inconsistent")
        return policy

    @classmethod
    def for_wish(cls, *, publish: bool) -> "PublicationPolicy":
        if type(publish) is not bool:
            raise ContractError("Wish publication choice must be boolean")
        return cls(
            visibility="public" if publish else "draft",
            authorization="wish",
        )

    @classmethod
    def legacy_fail_safe(cls) -> "PublicationPolicy":
        return cls(visibility="draft", authorization="legacy-fail-safe")

    def authorize_public(self) -> "PublicationPolicy":
        if self.visibility == "public":
            return self
        return PublicationPolicy(
            visibility="public",
            authorization="explicit-resume-publish",
        )


@dataclass(frozen=True)
class ManagerAssignmentHandoff:
    """The minimum exact assignment identity an Inventor needs to execute."""

    wish: Wish
    inventor_id: str
    playtest_rounds: int
    decision_sha256: str
    assignment_sha256: str
    manifest_sha256: Optional[str] = None
    taste_sha256: Optional[str] = None
    implementation_sha256: Optional[str] = None
    entrypoint: Sequence[str] = field(default_factory=tuple)
    world_inputs: Optional[WorldInventInputs] = None
    world_evidence: Optional[WorldPlaytestEvidence] = None
    schema_version: int = 1
    kind: str = HANDOFF_KIND
    publication_policy: Optional[PublicationPolicy] = None
    wish_sha256: str = field(init=False)
    handoff_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version not in (1, 2, 3, 4):
            raise ContractError(
                "Manager assignment handoff schema_version must be 1, 2, 3, or 4"
            )
        if self.kind != HANDOFF_KIND:
            raise ContractError("Manager assignment handoff kind is invalid")
        if not isinstance(self.wish, Wish):
            raise ContractError("Manager assignment handoff requires an exact Wish")
        self.wish.assert_valid()
        _bounded_identifier(self.inventor_id, "Manager assignment inventor_id")
        if (
            type(self.playtest_rounds) is not int
            or not 1 <= self.playtest_rounds <= 100
        ):
            raise ContractError(
                "Manager assignment playtest_rounds must be an integer from 1 to 100"
            )
        require_sha256(self.decision_sha256, "Manager routing decision sha256")
        require_sha256(self.assignment_sha256, "Manager assignment sha256")
        if self.schema_version == 1:
            if any(
                value is not None
                for value in (
                    self.manifest_sha256,
                    self.taste_sha256,
                    self.implementation_sha256,
                )
            ) or tuple(self.entrypoint):
                raise ContractError(
                    "legacy Manager assignment handoff cannot claim v2 inventor identity"
                )
            if self.world_inputs is not None or self.world_evidence is not None:
                raise ContractError("legacy Manager handoff cannot carry world inputs")
            if self.publication_policy is not None:
                raise ContractError("legacy Manager handoff cannot carry publication policy")
            entrypoint: Tuple[str, ...] = ()
        else:
            require_sha256(
                self.manifest_sha256, "Manager assignment manifest sha256"
            )
            require_sha256(self.taste_sha256, "Manager assignment Taste sha256")
            require_sha256(
                self.implementation_sha256,
                "Manager assignment implementation sha256",
            )
            entrypoint = _entrypoint(self.entrypoint)
            if self.schema_version == 2 and (
                self.world_inputs is not None or self.world_evidence is not None
            ):
                raise ContractError("v2 Manager handoff cannot carry world inputs")
            if self.schema_version in (2, 3) and self.publication_policy is not None:
                raise ContractError(
                    "legacy Manager handoff cannot carry publication policy"
                )
            if self.schema_version == 3:
                if not isinstance(self.world_inputs, WorldInventInputs):
                    raise ContractError("v3 Manager handoff requires typed world inputs")
                self.world_inputs.assert_wish(self.wish)
                if self.world_evidence is not None and not isinstance(
                    self.world_evidence, WorldPlaytestEvidence
                ):
                    raise ContractError("v3 Manager handoff world evidence is untyped")
            if self.schema_version == 4:
                if not isinstance(self.publication_policy, PublicationPolicy):
                    raise ContractError("v4 Manager handoff requires publication policy")
                if self.world_inputs is not None:
                    if not isinstance(self.world_inputs, WorldInventInputs):
                        raise ContractError("v4 Manager handoff world inputs are untyped")
                    self.world_inputs.assert_wish(self.wish)
                if self.world_evidence is not None:
                    if self.world_inputs is None:
                        raise ContractError(
                            "v4 Manager handoff world evidence requires world inputs"
                        )
                    if not isinstance(self.world_evidence, WorldPlaytestEvidence):
                        raise ContractError("v4 Manager handoff world evidence is untyped")
        object.__setattr__(self, "entrypoint", entrypoint)
        object.__setattr__(self, "wish_sha256", _sha256(self.wish.to_dict()))
        object.__setattr__(self, "handoff_sha256", _sha256(self._identity_dict()))

    def _identity_dict(self) -> Dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "wish": self.wish.to_dict(),
            "wish_sha256": self.wish_sha256,
            "inventor_id": self.inventor_id,
            "playtest_rounds": self.playtest_rounds,
            "decision_sha256": self.decision_sha256,
            "assignment_sha256": self.assignment_sha256,
        }
        if self.schema_version in (2, 3, 4):
            payload.update(
                {
                    "manifest_sha256": self.manifest_sha256,
                    "taste_sha256": self.taste_sha256,
                    "implementation_sha256": self.implementation_sha256,
                    "entrypoint": list(self.entrypoint),
                }
            )
        if self.schema_version == 3:
            assert self.world_inputs is not None
            payload.update(
                {
                    "world_inputs": self.world_inputs.to_dict(),
                    "world_evidence": (
                        self.world_evidence.to_dict()
                        if self.world_evidence is not None
                        else None
                    ),
                }
            )
        if self.schema_version == 4:
            assert self.publication_policy is not None
            payload.update(
                {
                    "publication_policy": self.publication_policy.to_dict(),
                    "world_inputs": (
                        self.world_inputs.to_dict()
                        if self.world_inputs is not None
                        else None
                    ),
                    "world_evidence": (
                        self.world_evidence.to_dict()
                        if self.world_evidence is not None
                        else None
                    ),
                }
            )
        return payload

    def to_dict(self) -> Dict[str, Any]:
        payload = self._identity_dict()
        payload["handoff_sha256"] = self.handoff_sha256
        return payload

    def result_binding(self) -> Dict[str, Any]:
        """Return the public identity the child must attach to its result."""

        payload = {
            "schema_version": self.schema_version,
            "product_id": self.wish.product_id,
            "inventor_id": self.inventor_id,
            "wish_sha256": self.wish_sha256,
            "decision_sha256": self.decision_sha256,
            "assignment_sha256": self.assignment_sha256,
            "handoff_sha256": self.handoff_sha256,
        }
        if self.schema_version in (2, 3, 4):
            payload.update(
                {
                    "manifest_sha256": self.manifest_sha256,
                    "taste_sha256": self.taste_sha256,
                    "implementation_sha256": self.implementation_sha256,
                    "entrypoint": list(self.entrypoint),
                }
            )
        if self.schema_version == 3:
            assert self.world_inputs is not None
            payload.update(
                {
                    "world_inputs_sha256": self.world_inputs.binding_sha256,
                    "world_evidence_sha256": (
                        self.world_evidence.evidence_sha256
                        if self.world_evidence is not None
                        else None
                    ),
                }
            )
        if self.schema_version == 4:
            assert self.publication_policy is not None
            payload.update(
                {
                    "publication_policy_sha256": self.publication_policy.policy_sha256,
                    "world_inputs_sha256": (
                        self.world_inputs.binding_sha256
                        if self.world_inputs is not None
                        else None
                    ),
                    "world_evidence_sha256": (
                        self.world_evidence.evidence_sha256
                        if self.world_evidence is not None
                        else None
                    ),
                }
            )
        return payload

    @property
    def has_exact_inventor_identity(self) -> bool:
        """Whether this handoff can prove which contribution code may execute."""

        return self.schema_version in (2, 3, 4)

    def require_exact_inventor_identity(self) -> None:
        """Reject legacy handoffs at contribution-code execution boundaries."""

        if not self.has_exact_inventor_identity:
            raise ContractError(
                "legacy Manager assignment has no exact inventor implementation identity"
            )

    def assert_inventor_current(self, root_or_card: Any) -> None:
        """Prove manifest, Taste, implementation, and entrypoint still match.

        ``root_or_card`` may be the selected ``InventorCard`` or its absolute
        inventor directory. Call this immediately before contribution code can
        execute and again after the child returns.
        """

        self.require_exact_inventor_identity()
        card_root = (
            root_or_card
            if isinstance(root_or_card, (str, Path))
            else getattr(root_or_card, "root", root_or_card)
        )
        root = Path(card_root)
        if root.name != self.inventor_id:
            raise ContractError(
                "Manager assignment inventor root belongs to a different Inventor"
            )
        manifest, taste, implementation, entrypoint = _current_inventor_identity(root)
        if (
            manifest != self.manifest_sha256
            or taste != self.taste_sha256
            or implementation != self.implementation_sha256
            or entrypoint != tuple(self.entrypoint)
        ):
            raise ContractError(
                "Manager assignment inventor manifest, Taste, implementation, or entrypoint changed"
            )

    @classmethod
    def from_assignment(cls, assignment: Any) -> "ManagerAssignmentHandoff":
        """Snapshot one validated Manager assignment for a child process."""

        assert_current = getattr(assignment, "assert_current", None)
        if callable(assert_current):
            assert_current()
        try:
            wish = assignment.wish
            inventor_id = assignment.inventor_id
            playtest_rounds = assignment.playtest_rounds
            decision = assignment.decision
            decision_sha256 = decision.decision_sha256
            assignment_sha256 = assignment.assignment_sha256
            selected = decision.selected
            card = selected.card
        except AttributeError as exc:
            raise ContractError(
                "Manager assignment handoff requires a complete assignment"
            ) from exc
        manifest, taste, implementation, entrypoint = _current_inventor_identity(
            Path(card.root)
        )
        if getattr(card, "inventor_id", inventor_id) != inventor_id:
            raise ContractError("Manager assignment selected a different Inventor")
        selected_taste = getattr(getattr(selected, "taste", None), "sha256", taste)
        selected_implementation = getattr(
            selected, "implementation_sha256", implementation
        )
        card_manifest = getattr(card, "manifest_sha256", manifest)
        card_entrypoint = tuple(getattr(card, "entrypoint", entrypoint))
        assignment_entrypoint = tuple(getattr(assignment, "entrypoint", entrypoint))
        if (
            card_manifest != manifest
            or selected_taste != taste
            or selected_implementation != implementation
            or card_entrypoint != entrypoint
            or assignment_entrypoint != entrypoint
        ):
            raise ContractError("Manager assignment contains stale inventor identity")
        world_inputs = getattr(assignment, "world_inputs", None)
        world_evidence = getattr(assignment, "world_evidence", None)
        publication_policy = getattr(assignment, "publication_policy", None)
        if world_evidence is not None and world_inputs is None:
            raise ContractError("Manager assignment world evidence has no Invent inputs")
        if publication_policy is not None and not isinstance(
            publication_policy, PublicationPolicy
        ):
            raise ContractError("Manager assignment publication policy is untyped")
        handoff = cls(
            wish=wish,
            inventor_id=inventor_id,
            playtest_rounds=playtest_rounds,
            decision_sha256=decision_sha256,
            assignment_sha256=assignment_sha256,
            manifest_sha256=manifest,
            taste_sha256=taste,
            implementation_sha256=implementation,
            entrypoint=entrypoint,
            world_inputs=world_inputs,
            world_evidence=world_evidence,
            publication_policy=publication_policy,
            schema_version=(
                4
                if publication_policy is not None
                else 3
                if world_inputs is not None
                else 2
            ),
        )
        handoff.assert_inventor_current(card)
        return handoff

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any], *, expected_inventor_id: str
    ) -> "ManagerAssignmentHandoff":
        payload = _copy_mapping(value, "Manager assignment handoff")
        version = payload.get("schema_version")
        expected_keys = {
            "schema_version",
            "kind",
            "wish",
            "wish_sha256",
            "inventor_id",
            "playtest_rounds",
            "decision_sha256",
            "assignment_sha256",
            "handoff_sha256",
        }
        if version in (2, 3, 4):
            expected_keys |= {
                "manifest_sha256",
                "taste_sha256",
                "implementation_sha256",
                "entrypoint",
            }
        if version == 3:
            expected_keys |= {"world_inputs", "world_evidence"}
        if version == 4:
            expected_keys |= {
                "publication_policy",
                "world_inputs",
                "world_evidence",
            }
        if set(payload) != expected_keys:
            raise ContractError("Manager assignment handoff fields are invalid")
        wish_value = payload["wish"]
        if not isinstance(wish_value, Mapping) or set(wish_value) != {
            "schema_version",
            "product_id",
            "objective",
            "constraints",
            "context",
        }:
            raise ContractError("Manager assignment handoff Wish fields are invalid")
        wish = Wish(
            schema_version=wish_value["schema_version"],
            product_id=wish_value["product_id"],
            objective=wish_value["objective"],
            constraints=wish_value["constraints"],
            context=wish_value["context"],
        )
        raw_world_inputs = payload.get("world_inputs")
        world_inputs = (
            WorldInventInputs.from_dict(raw_world_inputs)
            if version in (3, 4) and raw_world_inputs is not None
            else None
        )
        raw_world_evidence = payload.get("world_evidence")
        world_evidence = (
            WorldPlaytestEvidence.from_dict(raw_world_evidence)
            if version in (3, 4) and raw_world_evidence is not None
            else None
        )
        publication_policy = (
            PublicationPolicy.from_dict(payload["publication_policy"])
            if version == 4
            else None
        )
        handoff = cls(
            wish=wish,
            inventor_id=payload["inventor_id"],
            playtest_rounds=payload["playtest_rounds"],
            decision_sha256=payload["decision_sha256"],
            assignment_sha256=payload["assignment_sha256"],
            manifest_sha256=payload.get("manifest_sha256"),
            taste_sha256=payload.get("taste_sha256"),
            implementation_sha256=payload.get("implementation_sha256"),
            entrypoint=payload.get("entrypoint", ()),
            world_inputs=world_inputs,
            world_evidence=world_evidence,
            publication_policy=publication_policy,
            schema_version=payload["schema_version"],
            kind=payload["kind"],
        )
        _bounded_identifier(expected_inventor_id, "expected inventor_id")
        if handoff.inventor_id != expected_inventor_id:
            raise ContractError("Manager assignment selected a different Inventor")
        if payload["wish_sha256"] != handoff.wish_sha256:
            raise ContractError("Manager assignment Wish identity is inconsistent")
        if payload["handoff_sha256"] != handoff.handoff_sha256:
            raise ContractError("Manager assignment handoff identity is inconsistent")
        return handoff


def read_manager_assignment(
    stream: TextIO, *, expected_inventor_id: str
) -> ManagerAssignmentHandoff:
    """Read one bounded assignment document from stdin."""

    source = stream.read(MAX_HANDOFF_BYTES + 1)
    try:
        encoded_size = len(source.encode("utf-8")) if isinstance(source, str) else 0
    except UnicodeError as exc:
        raise ContractError(
            "Manager assignment handoff must be bounded UTF-8 JSON"
        ) from exc
    if not isinstance(source, str) or not source or encoded_size > MAX_HANDOFF_BYTES:
        raise ContractError("Manager assignment handoff must be bounded UTF-8 JSON")
    try:
        value = json.loads(source)
    except (TypeError, ValueError) as exc:
        raise ContractError("Manager assignment handoff must be valid JSON") from exc
    if not isinstance(value, Mapping):
        raise ContractError("Manager assignment handoff must be one JSON object")
    handoff = ManagerAssignmentHandoff.from_dict(
        value, expected_inventor_id=expected_inventor_id
    )
    handoff.require_exact_inventor_identity()
    return handoff


def bind_manager_assignment_result(
    result: Mapping[str, Any], handoff: ManagerAssignmentHandoff
) -> Dict[str, Any]:
    """Attach the exact assignment identity to a Workshop child result."""

    if not isinstance(handoff, ManagerAssignmentHandoff):
        raise ContractError("Workshop result binding requires a Manager assignment")
    payload = _copy_mapping(result, "Workshop child result")
    if payload.get("product_id") != handoff.wish.product_id:
        raise ContractError("Workshop child result belongs to a different product")
    if payload.get("playtest_rounds") != handoff.playtest_rounds:
        raise ContractError("Workshop child result changed the assignment Playtest allowance")
    if RESULT_BINDING_FIELD in payload:
        raise ContractError("Workshop child result already contains a Manager assignment")
    payload[RESULT_BINDING_FIELD] = handoff.result_binding()
    return payload


def validate_manager_assignment_result(
    result: Mapping[str, Any], handoff: ManagerAssignmentHandoff
) -> Dict[str, Any]:
    """Validate that returned output is for the exact dispatched assignment."""

    payload = _copy_mapping(result, "Workshop child result")
    binding = payload.get(RESULT_BINDING_FIELD)
    if binding != handoff.result_binding():
        raise ContractError("Workshop child result is not bound to this Manager assignment")
    if payload.get("product_id") != handoff.wish.product_id:
        raise ContractError("Workshop child result belongs to a different product")
    if payload.get("playtest_rounds") != handoff.playtest_rounds:
        raise ContractError("Workshop child result changed the assignment Playtest allowance")
    return payload


__all__ = [
    "HANDOFF_KIND",
    "MAX_HANDOFF_BYTES",
    "PUBLICATION_POLICY_KIND",
    "RESULT_BINDING_FIELD",
    "ManagerAssignmentHandoff",
    "PublicationPolicy",
    "bind_manager_assignment_result",
    "read_manager_assignment",
    "validate_manager_assignment_result",
]
