"""Strict inputs and outputs for the five Toy Workshop jobs."""

from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .artifacts import ArtifactManifest, build_artifact_manifest
from .errors import ArtifactError, ContractError
from .make import Wish
from .models import Receipt, require_json_mapping, require_sha256, require_utc_timestamp
from .playtest import Playtest
from .taste import Taste
from .toys import PLAYTHING_LANES, ToyBlueprint, WORKSHOP_JOBS


_SEVERITIES = frozenset(("note", "improve", "block"))
_RUN_STATUSES = frozenset(("working", "waiting", "ready", "delivered", "stopped"))
_CARRIERS = frozenset(("USPS", "UPS", "FedEx"))
_DELIVERY_STATUSES = frozenset(("handed-off", "delivered"))
_INSTRUCTIONS_MEDIA_ROLES = frozenset(("hero", "play", "detail", "parts", "box"))
_INSTRUCTIONS_IMAGE_SUFFIXES = frozenset((".png", ".jpg", ".jpeg", ".webp"))


def _text(value: Any, label: str, maximum: int = 10_000) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 and character not in "\n\r\t" for character in value)
        or any(ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded, non-empty text" % label)
    return value


def _mapping(value: Mapping[str, Any], label: str, *, nonempty: bool = False) -> Dict[str, Any]:
    require_json_mapping(value, label)
    # Frozen records must not retain live references to caller-owned nested
    # dictionaries or lists.  The JSON round trip also normalizes tuples to
    # their persisted representation.
    try:
        copied = json.loads(
            json.dumps(
                dict(value),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise ContractError("%s must be a JSON object" % label) from exc
    if nonempty and not copied:
        raise ContractError("%s must not be empty" % label)
    return copied


def _fresh_manifest(root: Path, manifest: ArtifactManifest) -> ArtifactManifest:
    current = build_artifact_manifest(root, created_at=manifest.created_at)
    if current.to_dict() != manifest.to_dict():
        raise ArtifactError("artifact bytes changed after the job completed")
    return current


@dataclass(frozen=True)
class Need:
    """A truthful request for a capability or real-world evidence."""

    job: str
    capability: str
    reason: str
    instructions: str

    def __post_init__(self) -> None:
        if self.job not in WORKSHOP_JOBS:
            raise ContractError("need job must name one of the five Workshop jobs")
        _text(self.capability, "need capability", 200)
        _text(self.reason, "need reason")
        _text(self.instructions, "need instructions")

    def to_dict(self) -> Dict[str, str]:
        return {
            "job": self.job,
            "capability": self.capability,
            "reason": self.reason,
            "instructions": self.instructions,
        }


class WaitingFor(RuntimeError):
    """Raised by a job when more work would otherwise fabricate evidence."""

    def __init__(self, *needs: Need) -> None:
        if not needs or not all(isinstance(item, Need) for item in needs):
            raise ContractError("WaitingFor requires at least one typed Need")
        self.needs = tuple(needs)
        super().__init__("; ".join(item.capability for item in self.needs))


@dataclass(frozen=True)
class Feedback:
    """One actionable finding that sends the product back through Make."""

    code: str
    area: str
    severity: str
    finding: str
    change: str
    evidence_refs: Sequence[str] = field(default_factory=tuple)
    invalidates: Sequence[str] = ("playtest", "instructions", "deliver")

    def __post_init__(self) -> None:
        _text(self.code, "feedback code", 200)
        _text(self.area, "feedback area", 200)
        if self.severity not in _SEVERITIES:
            raise ContractError("feedback severity must be note, improve, or block")
        _text(self.finding, "feedback finding")
        _text(self.change, "feedback change")
        refs = tuple(self.evidence_refs)
        invalidates = tuple(self.invalidates)
        if any(not isinstance(item, str) or not item for item in refs):
            raise ContractError("feedback evidence_refs must be non-empty strings")
        if any(item not in WORKSHOP_JOBS for item in invalidates):
            raise ContractError("feedback invalidates an unknown Workshop job")
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(self, "invalidates", invalidates)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "area": self.area,
            "severity": self.severity,
            "finding": self.finding,
            "change": self.change,
            "evidence_refs": list(self.evidence_refs),
            "invalidates": list(self.invalidates),
        }


@dataclass(frozen=True)
class MakeContext:
    wish: Wish
    taste: Taste
    blueprint: ToyBlueprint
    round: int
    workspace: Path
    feedback: Sequence[Feedback] = field(default_factory=tuple)
    playtest_rounds: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.wish, Wish) or not isinstance(self.taste, Taste):
            raise ContractError("MakeContext requires a Wish and Taste")
        if not isinstance(self.blueprint, ToyBlueprint):
            raise ContractError("MakeContext requires a ToyBlueprint")
        if type(self.round) is not int or self.round < 1:
            raise ContractError("MakeContext round must be a positive integer")
        if (
            type(self.playtest_rounds) is not int
            or not 1 <= self.playtest_rounds <= 100
            or self.round > self.playtest_rounds
        ):
            raise ContractError(
                "MakeContext playtest_rounds must cover this round and be from 1 to 100"
            )
        root = Path(self.workspace)
        if not root.is_absolute():
            raise ContractError("MakeContext workspace must be absolute")
        feedback = tuple(self.feedback)
        if not all(isinstance(item, Feedback) for item in feedback):
            raise ContractError("MakeContext feedback must use Feedback records")
        object.__setattr__(self, "workspace", root)
        object.__setattr__(self, "feedback", feedback)


@dataclass(frozen=True)
class Made:
    """One immutable toy or game revision returned by Make."""

    artifact_root: Path
    artifact_manifest: ArtifactManifest
    product: Mapping[str, Any]

    def __post_init__(self) -> None:
        root = Path(self.artifact_root)
        if not root.is_absolute() or root.is_symlink() or not root.is_dir():
            raise ContractError("Made artifact_root must be an absolute regular directory")
        if not isinstance(self.artifact_manifest, ArtifactManifest):
            raise ContractError("Made requires an ArtifactManifest")
        product = _mapping(self.product, "Made product", nonempty=True)
        for key in ("title", "summary", "lane"):
            _text(product.get(key), "Made product %s" % key, 2_000)
        if product["lane"] not in PLAYTHING_LANES:
            raise ContractError("Made product lane must be a Workshop plaything lane")
        _fresh_manifest(root, self.artifact_manifest)
        object.__setattr__(self, "artifact_root", root.resolve(strict=True))
        object.__setattr__(self, "product", product)

    @classmethod
    def from_root(cls, artifact_root: Path, product: Mapping[str, Any]) -> "Made":
        root = Path(artifact_root).resolve(strict=True)
        return cls(
            root,
            build_artifact_manifest(root, created_at="content-addressed"),
            product,
        )

    @property
    def artifact_sha256(self) -> str:
        return self.artifact_manifest.artifact_sha256

    def assert_current(self) -> None:
        _fresh_manifest(self.artifact_root, self.artifact_manifest)


@dataclass(frozen=True)
class PlaytestContext:
    wish: Wish
    taste: Taste
    blueprint: ToyBlueprint
    round: int
    made: Made
    workspace: Path
    playtest_rounds: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.wish, Wish) or not isinstance(self.taste, Taste):
            raise ContractError("PlaytestContext requires a Wish and Taste")
        if not isinstance(self.blueprint, ToyBlueprint):
            raise ContractError("PlaytestContext requires a ToyBlueprint")
        if not isinstance(self.made, Made):
            raise ContractError("PlaytestContext requires a Made revision")
        if self.made.product["lane"] != self.blueprint.lane:
            raise ContractError("PlaytestContext product belongs to a different lane")
        if type(self.round) is not int or self.round < 1:
            raise ContractError("PlaytestContext round must be a positive integer")
        if (
            type(self.playtest_rounds) is not int
            or not 1 <= self.playtest_rounds <= 100
            or self.round > self.playtest_rounds
        ):
            raise ContractError(
                "PlaytestContext playtest_rounds must cover this round and be from 1 to 100"
            )
        root = Path(self.workspace)
        if not root.is_absolute():
            raise ContractError("PlaytestContext workspace must be absolute")
        object.__setattr__(self, "workspace", root)
        self.made.assert_current()


@dataclass(frozen=True)
class Playtested:
    """Completed evidence plus structured feedback for one exact revision."""

    evidence: Playtest
    feedback: Sequence[Feedback] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, Playtest):
            raise ContractError("Playtested requires an artifact-bound Playtest")
        feedback = tuple(self.feedback)
        if not all(isinstance(item, Feedback) for item in feedback):
            raise ContractError("Playtested feedback must use Feedback records")
        object.__setattr__(self, "feedback", feedback)
        self.evidence.assert_valid()

    @property
    def passed(self) -> bool:
        return self.evidence.passed and not any(
            item.severity in ("improve", "block") for item in self.feedback
        )

    def assert_artifact(self, artifact_sha256: str) -> None:
        require_sha256(artifact_sha256, "Playtested artifact sha256")
        if self.evidence.artifact_sha256 != artifact_sha256:
            raise ContractError("Playtested evidence belongs to different artifact bytes")


@dataclass(frozen=True)
class InstructionsContext:
    wish: Wish
    taste: Taste
    blueprint: ToyBlueprint
    made: Made
    playtested: Playtested
    workspace: Path
    lease_token: Optional[str] = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.wish, Wish) or not isinstance(self.taste, Taste):
            raise ContractError("InstructionsContext requires a Wish and Taste")
        if not isinstance(self.blueprint, ToyBlueprint):
            raise ContractError("InstructionsContext requires a ToyBlueprint")
        if not isinstance(self.made, Made) or not isinstance(self.playtested, Playtested):
            raise ContractError(
                "InstructionsContext requires Made and Playtested results"
            )
        if self.made.product["lane"] != self.blueprint.lane:
            raise ContractError(
                "InstructionsContext product belongs to a different lane"
            )
        if not self.playtested.passed:
            raise ContractError("Instructions cannot begin before Playtest passes")
        root = Path(self.workspace)
        if not root.is_absolute():
            raise ContractError("InstructionsContext workspace must be absolute")
        if self.lease_token is not None and (
            not isinstance(self.lease_token, str)
            or not self.lease_token
            or len(self.lease_token) > 512
            or any(ord(character) < 33 or ord(character) == 127 for character in self.lease_token)
        ):
            raise ContractError("InstructionsContext lease token is malformed")
        object.__setattr__(self, "workspace", root)
        self.assert_current()

    def assert_current(self) -> None:
        """Recheck that Instructions still describes the exact Playtested Make."""

        self.made.assert_current()
        self.playtested.assert_artifact(self.made.artifact_sha256)


@dataclass(frozen=True)
class ProductInstructions:
    """One sealed box insert and site page, proven live for the exact Make.

    Instructions is not complete merely because local copy and images exist.  The
    site receipt binds the complete Instructions tree (page, paper, and media) to
    an authenticated public readback for the exact product artifact.
    """

    root: Path
    manifest: ArtifactManifest
    product_artifact_sha256: str
    instructions_path: str
    claims: Mapping[str, Any]
    site_receipt: Receipt

    def __post_init__(self) -> None:
        root = Path(self.root)
        if not root.is_absolute() or root.is_symlink() or not root.is_dir():
            raise ContractError(
                "ProductInstructions root must be an absolute regular directory"
            )
        if not isinstance(self.manifest, ArtifactManifest):
            raise ContractError("ProductInstructions requires an ArtifactManifest")
        require_sha256(
            self.product_artifact_sha256,
            "ProductInstructions product artifact sha256",
        )
        _text(
            self.instructions_path,
            "ProductInstructions instructions_path",
            1_000,
        )
        instructions = Path(self.instructions_path)
        if (
            instructions.is_absolute()
            or ".." in instructions.parts
            or instructions.as_posix() != "INSTRUCTIONS.md"
            or not (root / instructions).is_file()
        ):
            raise ContractError(
                "ProductInstructions instructions_path must be INSTRUCTIONS.md"
            )
        page_path = root / "product.json"
        if not page_path.is_file():
            raise ContractError("ProductInstructions requires an in-root product.json")
        claims = _mapping(self.claims, "ProductInstructions claims", nonempty=True)
        _fresh_manifest(root, self.manifest)
        try:
            page_value = json.loads(page_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError(
                "ProductInstructions product.json must be valid UTF-8 JSON"
            ) from exc
        page = _mapping(
            page_value,
            "ProductInstructions product.json",
            nonempty=True,
        )
        if page.get("status") != "ready":
            raise ContractError(
                "ProductInstructions product.json must be sealed and ready for the site"
            )
        if page.get("product_artifact_sha256") != self.product_artifact_sha256:
            raise ContractError(
                "ProductInstructions product.json describes different product bytes"
            )
        page_claims = _mapping(
            page.get("claims"),
            "ProductInstructions product.json claims",
            nonempty=True,
        )
        if page_claims != claims:
            raise ContractError(
                "ProductInstructions claims differ from the sealed product page"
            )
        images_value = page.get("images")
        if (
            not isinstance(images_value, Mapping)
            or set(images_value) != _INSTRUCTIONS_MEDIA_ROLES
        ):
            raise ContractError(
                "ProductInstructions product.json requires hero, play, detail, "
                "parts, and box images"
            )
        image_paths = []
        resolved_root = root.resolve(strict=True)
        for role in sorted(_INSTRUCTIONS_MEDIA_ROLES):
            relative_value = images_value[role]
            relative = (
                Path(relative_value)
                if isinstance(relative_value, str)
                else Path(".")
            )
            if (
                not isinstance(relative_value, str)
                or not relative_value
                or relative.is_absolute()
                or ".." in relative.parts
                or "\\" in relative_value
                or relative.suffix.casefold() not in _INSTRUCTIONS_IMAGE_SUFFIXES
            ):
                raise ContractError(
                    "ProductInstructions %s image must be a safe relative image path"
                    % role
                )
            try:
                image_path = (root / relative).resolve(strict=True)
                image_path.relative_to(resolved_root)
            except (OSError, ValueError) as exc:
                raise ContractError(
                    "ProductInstructions %s image is missing or outside its root"
                    % role
                ) from exc
            if not image_path.is_file():
                raise ContractError(
                    "ProductInstructions %s image must be a regular file" % role
                )
            image_paths.append(relative.as_posix())
        if len(set(image_paths)) != len(_INSTRUCTIONS_MEDIA_ROLES):
            raise ContractError(
                "ProductInstructions requires a distinct file for every image role"
            )
        self._assert_site_receipt()
        object.__setattr__(self, "root", root.resolve(strict=True))
        object.__setattr__(self, "claims", claims)

    def _assert_site_receipt(self) -> None:
        """Require a public readback bound to both Make and Instructions bytes."""

        if not isinstance(self.site_receipt, Receipt):
            raise ContractError("ProductInstructions requires a site Receipt")
        self.site_receipt.assert_artifact(self.product_artifact_sha256)
        if not self.site_receipt.is_verified_public:
            raise ContractError(
                "ProductInstructions requires an authenticated public site Receipt"
            )
        page_url = self.site_receipt.project_url
        try:
            parsed_page_url = urllib.parse.urlsplit(page_url or "")
        except ValueError as exc:
            raise ContractError(
                "ProductInstructions site Receipt requires a valid public page URL"
            ) from exc
        if (
            parsed_page_url.scheme != "https"
            or not parsed_page_url.hostname
            or parsed_page_url.username is not None
            or parsed_page_url.password is not None
        ):
            raise ContractError(
                "ProductInstructions site Receipt requires an HTTPS public page URL"
            )
        if (
            self.site_receipt.details.get("instructions_sha256")
            != self.manifest.artifact_sha256
        ):
            raise ContractError(
                "ProductInstructions site Receipt describes different page, paper, or media bytes"
            )

    @classmethod
    def from_root(
        cls,
        root: Path,
        product_artifact_sha256: str,
        instructions_path: str,
        claims: Mapping[str, Any],
        site_receipt: Receipt,
    ) -> "ProductInstructions":
        resolved = Path(root).resolve(strict=True)
        return cls(
            resolved,
            build_artifact_manifest(resolved, created_at="content-addressed"),
            product_artifact_sha256,
            instructions_path,
            claims,
            site_receipt,
        )

    @property
    def instructions_sha256(self) -> str:
        return self.manifest.artifact_sha256

    @property
    def page_url(self) -> str:
        """The authenticated public product-page URL created by Instructions."""

        # __post_init__ requires this value, so the cast-free assertion is safe
        # while preserving Receipt's compatibility-friendly Optional field.
        assert self.site_receipt.project_url is not None
        return self.site_receipt.project_url

    @property
    def publication_receipt(self) -> Receipt:
        """Compatibility spelling for callers that previously said publication."""

        return self.site_receipt

    def assert_current(self) -> None:
        """Refuse to use output bytes changed after Instructions completed."""

        _fresh_manifest(self.root, self.manifest)
        self._assert_site_receipt()


@dataclass(frozen=True)
class DeliverContext:
    wish: Wish
    made: Made
    instructions: ProductInstructions

    def __post_init__(self) -> None:
        if not isinstance(self.wish, Wish):
            raise ContractError("DeliverContext requires a Wish")
        if not isinstance(self.made, Made) or not isinstance(
            self.instructions, ProductInstructions
        ):
            raise ContractError(
                "DeliverContext requires Made and ProductInstructions results"
            )
        if self.instructions.product_artifact_sha256 != self.made.artifact_sha256:
            raise ContractError("Deliver Instructions describe different artifact bytes")
        self.assert_current()

    def assert_current(self) -> None:
        """Recheck both exact inputs at every external Deliver boundary."""

        self.made.assert_current()
        self.instructions.assert_current()


@dataclass(frozen=True)
class Delivered:
    """Carrier evidence for the exact approved product and Instructions."""

    product_artifact_sha256: str
    instructions_sha256: str
    carrier: str
    service: str
    tracking_id: str
    status: str
    observed_at: str
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        require_sha256(self.product_artifact_sha256, "Delivered product artifact sha256")
        require_sha256(
            self.instructions_sha256, "Delivered instructions sha256"
        )
        if self.carrier not in _CARRIERS:
            raise ContractError("Delivered carrier must be USPS, UPS, or FedEx")
        _text(self.service, "Delivered service", 200)
        _text(self.tracking_id, "Delivered tracking_id", 300)
        if self.status not in _DELIVERY_STATUSES:
            raise ContractError("Delivered status must be handed-off or delivered")
        require_utc_timestamp(self.observed_at, "Delivered observed_at")
        evidence = _mapping(self.evidence, "Delivered evidence", nonempty=True)
        required = {
            "print_receipt",
            "qa_receipt",
            "packing_receipt",
            "carrier_receipt",
        }
        missing = required - set(evidence)
        if missing:
            raise ContractError(
                "Delivered evidence is missing %s" % ", ".join(sorted(missing))
            )
        for name in sorted(required):
            evidence[name] = _mapping(
                evidence[name], "Delivered %s" % name, nonempty=True
            )
        object.__setattr__(self, "evidence", evidence)

    def assert_context(self, context: DeliverContext) -> None:
        if not isinstance(context, DeliverContext):
            raise ContractError("Delivered requires a DeliverContext")
        context.assert_current()
        if (
            self.product_artifact_sha256 != context.made.artifact_sha256
            or self.instructions_sha256
            != context.instructions.instructions_sha256
        ):
            raise ContractError(
                "Delivered receipt identifies different product or Instructions bytes"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "product_artifact_sha256": self.product_artifact_sha256,
            "instructions_sha256": self.instructions_sha256,
            "carrier": self.carrier,
            "service": self.service,
            "tracking_id": self.tracking_id,
            "status": self.status,
            "observed_at": self.observed_at,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class CustomerReview:
    """Human feedback received after the exact toy has been delivered.

    Reviews are deliberately separate from Playtest. Playtest is an AI-agent
    simulation inside the Make loop; a Review is a real customer's observation
    of a shipped product. It can guide a later revision, but it never rewrites
    the evidence or bytes of the product that customer received.
    """

    review_id: str
    product_artifact_sha256: str
    instructions_sha256: str
    delivery_tracking_id: str
    rating: int
    feedback: str
    observed_at: str

    def __post_init__(self) -> None:
        _text(self.review_id, "CustomerReview review_id", 256)
        require_sha256(
            self.product_artifact_sha256,
            "CustomerReview product artifact sha256",
        )
        require_sha256(
            self.instructions_sha256,
            "CustomerReview instructions sha256",
        )
        _text(
            self.delivery_tracking_id,
            "CustomerReview delivery_tracking_id",
            300,
        )
        if type(self.rating) is not int or not 1 <= self.rating <= 5:
            raise ContractError("CustomerReview rating must be an integer from 1 to 5")
        _text(self.feedback, "CustomerReview feedback", 20_000)
        require_utc_timestamp(self.observed_at, "CustomerReview observed_at")

    def assert_delivery(self, delivered: Delivered) -> None:
        if not isinstance(delivered, Delivered):
            raise ContractError("CustomerReview requires a Delivered result")
        if (
            self.product_artifact_sha256 != delivered.product_artifact_sha256
            or self.instructions_sha256 != delivered.instructions_sha256
            or self.delivery_tracking_id != delivered.tracking_id
        ):
            raise ContractError(
                "CustomerReview belongs to a different product, Instructions, or delivery"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "review_id": self.review_id,
            "product_artifact_sha256": self.product_artifact_sha256,
            "instructions_sha256": self.instructions_sha256,
            "delivery_tracking_id": self.delivery_tracking_id,
            "rating": self.rating,
            "feedback": self.feedback,
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True)
class WorkshopRun:
    product_id: str
    status: str
    job: str
    round: int
    artifact_sha256: Optional[str] = None
    instructions_sha256: Optional[str] = None
    needs: Sequence[Need] = field(default_factory=tuple)
    delivery: Optional[Delivered] = None
    playtest_rounds: int = 1
    page_url: Optional[str] = None

    def __post_init__(self) -> None:
        _text(self.product_id, "WorkshopRun product_id", 256)
        if self.status not in _RUN_STATUSES:
            raise ContractError("WorkshopRun status is invalid")
        if self.job not in WORKSHOP_JOBS:
            raise ContractError("WorkshopRun job is invalid")
        if type(self.round) is not int or self.round < 0:
            raise ContractError("WorkshopRun round must be a non-negative integer")
        if (
            type(self.playtest_rounds) is not int
            or not 1 <= self.playtest_rounds <= 100
            or self.round > self.playtest_rounds
        ):
            raise ContractError(
                "WorkshopRun playtest_rounds must cover this round and be from 1 to 100"
            )
        if self.artifact_sha256 is not None:
            require_sha256(self.artifact_sha256, "WorkshopRun artifact sha256")
        if self.instructions_sha256 is not None:
            require_sha256(
                self.instructions_sha256, "WorkshopRun instructions sha256"
            )
        if self.page_url is not None:
            try:
                parsed_page_url = urllib.parse.urlsplit(self.page_url)
            except ValueError as exc:
                raise ContractError("WorkshopRun page_url must be a valid HTTPS URL") from exc
            if parsed_page_url.scheme != "https" or not parsed_page_url.hostname:
                raise ContractError("WorkshopRun page_url must be a valid HTTPS URL")
        needs = tuple(self.needs)
        if not all(isinstance(item, Need) for item in needs):
            raise ContractError("WorkshopRun needs must use Need records")
        object.__setattr__(self, "needs", needs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "status": self.status,
            "job": self.job,
            "round": self.round,
            "playtest_rounds": self.playtest_rounds,
            "artifact_sha256": self.artifact_sha256,
            "instructions_sha256": self.instructions_sha256,
            "page_url": self.page_url,
            "needs": [item.to_dict() for item in self.needs],
            "delivery": self.delivery.to_dict() if self.delivery is not None else None,
        }


__all__ = [
    "CustomerReview",
    "DeliverContext",
    "Delivered",
    "InstructionsContext",
    "Feedback",
    "Made",
    "MakeContext",
    "Need",
    "PlaytestContext",
    "Playtested",
    "ProductInstructions",
    "WaitingFor",
    "WorkshopRun",
]
