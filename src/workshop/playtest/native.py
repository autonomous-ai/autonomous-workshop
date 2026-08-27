"""Evidence-bound Playtest handoff for a native-agent product run."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from workshop._validation import (
    copy_json_mapping,
    require_exact_version,
    require_sha256,
    require_utc_timestamp,
)
from workshop.artifacts import (
    ArtifactManifest,
    artifact_manifest_from_mapping,
    build_artifact_manifest,
)
from workshop.errors import ArtifactError, ContractError
from workshop.make.native import NativeMade
from workshop.playtest.contracts import Feedback, Playtested
from workshop.playtest.evidence import PlaytestResult
from workshop.playtest.service import Playtest
from workshop.product import ToyBlueprint


NATIVE_PLAYTESTED_KIND = "autonomous-workshop.playtested"
PLAYTEST_VERDICTS = ("pass", "improve", "block")
_CHECK_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("native Playtest values must be finite JSON") from exc


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _safe_relative(value: Any, label: str) -> PurePosixPath:
    candidate = PurePosixPath(value) if isinstance(value, str) else PurePosixPath(".")
    if (
        not isinstance(value, str)
        or not value
        or value in (".", "..")
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.as_posix() != value
    ):
        raise ContractError("%s must be a safe relative POSIX path" % label)
    return candidate


VAULT_LEAD_CHECK_ID = "agent-playtest"
VAULT_LEAD_VERDICTS = ("confirmed", "dismissed")
MAX_VAULT_LEAD_WHY = 1_000
_LEAD_ID = re.compile(r"^[0-9a-f]{16}$")


def validate_vault_lead_answers(
    leads: Sequence[Mapping[str, Any]],
    checks: Sequence[Mapping[str, Any]],
    feedback: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    """Every issued design-vault lead must be answered exactly once.

    Answers live in the ``agent-playtest`` check's observations as
    ``vault_leads``: ``{"lead", "verdict", "why", "feedback_code"}``.  A
    ``confirmed`` lead must name a feedback item by ``code`` so the risk it
    confirmed becomes a repair; a ``dismissed`` lead must say why and names
    no feedback.  With no issued leads nothing is required and nothing may be
    answered.
    """

    issued = {}
    for lead in leads:
        identifier = lead.get("id") if isinstance(lead, Mapping) else None
        if not isinstance(identifier, str) or _LEAD_ID.fullmatch(identifier) is None:
            raise ContractError("issued vault lead id is invalid")
        issued[identifier] = lead
    answers: list[Any] = []
    for check in checks:
        if check.get("check_id") == VAULT_LEAD_CHECK_ID:
            observations = check.get("observations") or {}
            raw = observations.get("vault_leads", [])
            if not isinstance(raw, (list, tuple)):
                raise ContractError("vault_leads answers must be a list")
            answers = list(raw)
    if not issued:
        if answers:
            raise ContractError("Playtest answers vault leads that were never issued")
        return {"answered": 0, "confirmed": 0, "dismissed": 0}
    codes = {item.get("code") for item in feedback if isinstance(item, Mapping)}
    seen: set[str] = set()
    confirmed = 0
    for answer in answers:
        if not isinstance(answer, Mapping) or set(answer) != {
            "lead",
            "verdict",
            "why",
            "feedback_code",
        }:
            raise ContractError("vault lead answers need exactly lead, verdict, why, feedback_code")
        identifier = answer["lead"]
        if identifier not in issued:
            raise ContractError("vault lead answer names a lead that was not issued: %r" % (identifier,))
        if identifier in seen:
            raise ContractError("vault lead %s is answered more than once" % identifier)
        seen.add(identifier)
        if answer["verdict"] not in VAULT_LEAD_VERDICTS:
            raise ContractError("vault lead %s verdict must be confirmed or dismissed" % identifier)
        why = answer["why"]
        if not isinstance(why, str) or not why.strip() or len(why) > MAX_VAULT_LEAD_WHY:
            raise ContractError("vault lead %s needs a bounded non-empty why" % identifier)
        code = answer["feedback_code"]
        if answer["verdict"] == "confirmed":
            if not isinstance(code, str) or code not in codes:
                raise ContractError(
                    "confirmed vault lead %s must name an existing feedback code" % identifier
                )
            confirmed += 1
        elif code is not None:
            raise ContractError("dismissed vault lead %s must not name feedback" % identifier)
    missing = sorted(set(issued) - seen)
    if missing:
        raise ContractError("Playtest left vault leads unanswered: %s" % ", ".join(missing))
    return {"answered": len(seen), "confirmed": confirmed, "dismissed": len(seen) - confirmed}


@dataclass(frozen=True)
class NativePlaytestCheck:
    """One exact evidence file and its bounded evaluator observation."""

    check_id: str
    passed: bool
    evaluator: str
    evaluator_version: str
    config_sha256: str
    evidence_ref: str
    evidence_sha256: str
    observed_at: str
    observations: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.check_id, str) or _CHECK_ID.fullmatch(self.check_id) is None:
            raise ContractError("native Playtest check_id is invalid")
        if type(self.passed) is not bool:
            raise ContractError("native Playtest passed must be boolean")
        if (
            not isinstance(self.evaluator, str)
            or not self.evaluator.strip()
            or self.evaluator.casefold() in {"self-report", "trust-me"}
        ):
            raise ContractError("native Playtest evaluator must be named")
        require_exact_version(self.evaluator_version, "native Playtest evaluator version")
        require_sha256(self.config_sha256, "native Playtest config sha256")
        _safe_relative(self.evidence_ref, "native Playtest evidence_ref")
        require_sha256(self.evidence_sha256, "native Playtest evidence sha256")
        require_utc_timestamp(self.observed_at, "native Playtest observed_at")
        observations = copy_json_mapping(
            self.observations, "native Playtest observations", nonempty=True
        )
        object.__setattr__(self, "observations", _freeze(observations))

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "evaluator": self.evaluator,
            "evaluator_version": self.evaluator_version,
            "config_sha256": self.config_sha256,
            "evidence_ref": self.evidence_ref,
            "evidence_sha256": self.evidence_sha256,
            "observed_at": self.observed_at,
            "observations": _thaw(self.observations),
        }

    @classmethod
    def from_mapping(cls, value: Any) -> "NativePlaytestCheck":
        expected = {
            "check_id",
            "passed",
            "evaluator",
            "evaluator_version",
            "config_sha256",
            "evidence_ref",
            "evidence_sha256",
            "observed_at",
            "observations",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("native Playtest check fields are invalid")
        return cls(**dict(value))


def _feedback_from_mapping(value: Any) -> Feedback:
    expected = {
        "code",
        "area",
        "severity",
        "finding",
        "change",
        "evidence_refs",
        "invalidates",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ContractError("native Playtest feedback fields are invalid")
    return Feedback(
        code=value["code"],
        area=value["area"],
        severity=value["severity"],
        finding=value["finding"],
        change=value["change"],
        evidence_refs=tuple(value["evidence_refs"]),
        invalidates=tuple(value["invalidates"]),
    )


@dataclass(frozen=True)
class NativePlaytested:
    """All required baseline evidence for one exact Made revision."""

    round: int
    made_sha256: str
    product_artifact_sha256: str
    blueprint_sha256: str
    evidence_root: str
    evidence_manifest: ArtifactManifest
    checks: tuple[NativePlaytestCheck, ...]
    feedback: tuple[Feedback, ...]
    verdict: str
    schema_version: int = 1
    kind: str = NATIVE_PLAYTESTED_KIND
    playtested_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("native Playtested schema_version must be 1")
        if self.kind != NATIVE_PLAYTESTED_KIND:
            raise ContractError("native Playtested kind is invalid")
        if type(self.round) is not int or not 1 <= self.round <= 100:
            raise ContractError("native Playtested round must be from 1 through 100")
        require_sha256(self.made_sha256, "native Playtested Made sha256")
        require_sha256(
            self.product_artifact_sha256,
            "native Playtested product artifact sha256",
        )
        require_sha256(self.blueprint_sha256, "native Playtested blueprint sha256")
        expected_root = "artifacts/playtest/r%04d/evidence" % self.round
        if _safe_relative(self.evidence_root, "native Playtested evidence_root").as_posix() != expected_root:
            raise ContractError(
                "native Playtested evidence_root is not canonical for its round"
            )
        if not isinstance(self.evidence_manifest, ArtifactManifest):
            raise ContractError("native Playtested requires an ArtifactManifest")
        self.evidence_manifest.assert_valid()
        checks = tuple(self.checks)
        if not checks or not all(isinstance(item, NativePlaytestCheck) for item in checks):
            raise ContractError("native Playtested requires typed checks")
        if len({item.check_id for item in checks}) != len(checks):
            raise ContractError("native Playtested check ids must be unique")
        feedback = tuple(self.feedback)
        if not all(isinstance(item, Feedback) for item in feedback):
            raise ContractError("native Playtested feedback must use Feedback records")
        if self.verdict not in PLAYTEST_VERDICTS:
            raise ContractError("native Playtested verdict is invalid")
        failing = any(not item.passed for item in checks)
        actionable = any(item.severity in ("improve", "block") for item in feedback)
        if self.verdict == "pass" and (failing or actionable):
            raise ContractError("passing native Playtest cannot contain failures")
        if self.verdict != "pass" and (not feedback or not (failing or actionable)):
            raise ContractError("failed native Playtest requires actionable evidence")
        inventory = {entry.path: entry.sha256 for entry in self.evidence_manifest.entries}
        for check in checks:
            if inventory.get(check.evidence_ref) != check.evidence_sha256:
                raise ContractError(
                    "native Playtest evidence is absent or hash-mismatched: %s"
                    % check.check_id
                )
        object.__setattr__(self, "checks", checks)
        object.__setattr__(self, "feedback", feedback)
        object.__setattr__(
            self,
            "playtested_sha256",
            hashlib.sha256(_canonical_json(self._identity_dict())).hexdigest(),
        )

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "round": self.round,
            "made_sha256": self.made_sha256,
            "product_artifact_sha256": self.product_artifact_sha256,
            "blueprint_sha256": self.blueprint_sha256,
            "evidence_root": self.evidence_root,
            "evidence_manifest": self.evidence_manifest.to_dict(),
            "checks": [item.to_dict() for item in self.checks],
            "feedback": [item.to_dict() for item in self.feedback],
            "verdict": self.verdict,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["playtested_sha256"] = self.playtested_sha256
        return payload

    @classmethod
    def from_mapping(cls, value: Any) -> "NativePlaytested":
        expected = {
            "schema_version",
            "kind",
            "round",
            "made_sha256",
            "product_artifact_sha256",
            "blueprint_sha256",
            "evidence_root",
            "evidence_manifest",
            "checks",
            "feedback",
            "verdict",
            "playtested_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("native Playtested fields are invalid")
        checks = value["checks"]
        feedback = value["feedback"]
        if isinstance(checks, (str, bytes)) or not isinstance(checks, Sequence):
            raise ContractError("native Playtested checks must be an array")
        if isinstance(feedback, (str, bytes)) or not isinstance(feedback, Sequence):
            raise ContractError("native Playtested feedback must be an array")
        playtested = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            round=value["round"],
            made_sha256=value["made_sha256"],
            product_artifact_sha256=value["product_artifact_sha256"],
            blueprint_sha256=value["blueprint_sha256"],
            evidence_root=value["evidence_root"],
            evidence_manifest=artifact_manifest_from_mapping(value["evidence_manifest"]),
            checks=tuple(NativePlaytestCheck.from_mapping(item) for item in checks),
            feedback=tuple(_feedback_from_mapping(item) for item in feedback),
            verdict=value["verdict"],
        )
        if dict(value) != playtested.to_dict():
            raise ContractError("native Playtested hashes or canonical identity are invalid")
        return playtested

    def assert_context(self, made: NativeMade, blueprint: ToyBlueprint) -> None:
        if not isinstance(made, NativeMade) or not isinstance(blueprint, ToyBlueprint):
            raise ContractError("native Playtested context requires Made and blueprint")
        required = set(blueprint.required_playtest_checks())
        observed = {item.check_id for item in self.checks}
        if (
            self.round != made.round
            or self.made_sha256 != made.made_sha256
            or self.product_artifact_sha256 != made.product_manifest.artifact_sha256
            or self.blueprint_sha256 != made.blueprint_sha256
            or blueprint.sha256 != made.blueprint_sha256
            or observed != required
        ):
            raise ContractError("native Playtested belongs to different or incomplete inputs")

    def assert_vault_leads_answered(
        self, leads: Sequence[Mapping[str, Any]]
    ) -> dict[str, int]:
        """Host mirror of the run-local lead-answer rule for this contract."""

        return validate_vault_lead_answers(
            leads,
            [check.to_dict() for check in self.checks],
            [item.to_dict() for item in self.feedback],
        )

    def validate_evidence_tree(
        self, run_root: Path, made: NativeMade
    ) -> Playtested:
        root = Path(run_root).resolve(strict=True)
        relative = _safe_relative(self.evidence_root, "native Playtested evidence_root")
        evidence_root = root.joinpath(*relative.parts)
        if evidence_root.is_symlink() or not evidence_root.is_dir():
            raise ArtifactError("native Playtest evidence tree is unavailable")
        current = build_artifact_manifest(
            evidence_root, created_at=self.evidence_manifest.created_at
        )
        if current.to_dict() != self.evidence_manifest.to_dict():
            raise ArtifactError("native Playtest evidence differs from its manifest")
        made_contract = made.validate_product_tree(root)
        results = tuple(
            PlaytestResult(
                playtest_id=item.check_id,
                passed=item.passed,
                artifact_sha256=self.product_artifact_sha256,
                evidence=_thaw(item.observations),
                evaluator=item.evaluator,
                evaluator_version=item.evaluator_version,
                config_sha256=item.config_sha256,
                evidence_ref=item.evidence_ref,
                evidence_sha256=item.evidence_sha256,
                observed_at=item.observed_at,
            )
            for item in self.checks
        )
        return Playtested(
            Playtest(
                artifact_manifest=made_contract.artifact_manifest,
                results=results,
                evidence_manifest=self.evidence_manifest,
            ),
            feedback=self.feedback,
        )


__all__ = [
    "NATIVE_PLAYTESTED_KIND",
    "VAULT_LEAD_CHECK_ID",
    "VAULT_LEAD_VERDICTS",
    "validate_vault_lead_answers",
    "PLAYTEST_VERDICTS",
    "NativePlaytestCheck",
    "NativePlaytested",
]
