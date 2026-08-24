"""Publish one already-sealed Workshop product as a verified private draft.

This module is deliberately downstream of Make and AI Playtest.  A small,
checked-in descriptor points at immutable Make, Playtest, and Instructions
trees; the loader reconstructs the typed Workshop objects and fails before any
network request unless every required Playtest result passes and no actionable
feedback remains.

The remote boundary is equally narrow: derive a model-only Pack from the exact
Made bytes, import it with ``status=draft``, and authenticate the same private
draft by readback. Factory owns later page images, copy, and optional video; the
receipt records that enrichment as pending. There is no public-publish operation
in this module.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence, Tuple

from .artifacts import ArtifactEntry, ArtifactManifest, build_artifact_manifest
from .attribution import attribute_product_description
from .errors import ContractError, PublishError, ReceiptError, StateConflict
from .instructions import evidence_claims
from .jobs import Feedback, InstructionsContext, Made, ProductInstructions, Playtested
from .make import Wish
from .models import PlaytestResult, PublicationReceipt, require_sha256
from .playtest import Playtest
from .shop import (
    DEFAULT_SHOP_PAGE_BASE,
    MAX_RESPONSE_BYTES,
    HttpResponse,
    ShopDoor,
    ShopInstructionsWriter,
    Transport,
    urllib_transport,
)
from .store import InventorStore
from .taste import Taste, load_taste
from .toys import ToyBlueprint


DESCRIPTOR_KIND = "workshop.sealed-private-draft"
DEFAULT_STATE_DIRECTORY = ".runtime/sealed-product-publication"
_CANONICAL_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json_object(path: Path, label: str) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ContractError("%s must be a regular JSON file" % label)
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ContractError("cannot read %s" % label) from exc
    if not content or len(content) > MAX_RESPONSE_BYTES:
        raise ContractError("%s is empty or exceeds the JSON limit" % label)

    def reject_duplicate_keys(pairs):  # type: ignore[no-untyped-def]
        value: Dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key %r" % key)
            value[key] = item
        return value

    try:
        value = json.loads(
            content.decode("utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except (UnicodeError, ValueError) as exc:
        raise ContractError("%s must contain canonical UTF-8 JSON" % label) from exc
    if not isinstance(value, Mapping):
        raise ContractError("%s must contain a JSON object" % label)
    return value


def _response_object(response: HttpResponse, label: str) -> Mapping[str, Any]:
    if type(response.body) is not bytes or len(response.body) > MAX_RESPONSE_BYTES:
        raise ReceiptError("%s response exceeds the JSON limit" % label)
    try:
        value = json.loads(response.body.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ReceiptError("%s response is not valid UTF-8 JSON" % label) from exc
    if not isinstance(value, Mapping):
        raise ReceiptError("%s response is not a JSON object" % label)
    return value


def _safe_repo_path(
    repo_root: Path,
    value: Any,
    label: str,
    *,
    directory: bool,
) -> Path:
    candidate = PurePosixPath(value) if isinstance(value, str) else PurePosixPath(".")
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.as_posix() != value
    ):
        raise ContractError("%s must be a safe repository-relative POSIX path" % label)
    requested = repo_root.joinpath(*candidate.parts)
    if requested.is_symlink():
        raise ContractError("%s must not be a symlink" % label)
    try:
        resolved = requested.resolve(strict=True)
        resolved.relative_to(repo_root)
    except (OSError, ValueError) as exc:
        raise ContractError("%s is missing or outside the repository" % label) from exc
    if directory and not resolved.is_dir():
        raise ContractError("%s must be a directory" % label)
    if not directory and not resolved.is_file():
        raise ContractError("%s must be a regular file" % label)
    return resolved


def _typed_manifest(
    root: Path,
    path: Path,
    label: str,
    expected_artifact_sha256: str,
) -> ArtifactManifest:
    value = _read_json_object(path, "%s manifest" % label)
    if set(value) != {
        "schema_version",
        "artifact_sha256",
        "total_bytes",
        "created_at",
        "entries",
    } or not isinstance(value.get("entries"), list):
        raise ContractError("%s manifest is malformed" % label)
    entries = []
    for raw in value["entries"]:
        if not isinstance(raw, Mapping) or set(raw) != {
            "path",
            "bytes",
            "sha256",
            "executable",
        }:
            raise ContractError("%s manifest entry is malformed" % label)
        entries.append(
            ArtifactEntry(
                raw["path"], raw["bytes"], raw["sha256"], raw["executable"]
            )
        )
    manifest = ArtifactManifest(
        value["schema_version"],
        value["artifact_sha256"],
        tuple(entries),
        value["total_bytes"],
        value["created_at"],
    )
    require_sha256(expected_artifact_sha256, "%s expected artifact sha256" % label)
    if manifest.artifact_sha256 != expected_artifact_sha256:
        raise ContractError("%s manifest has a different artifact identity" % label)
    current = build_artifact_manifest(root, created_at=manifest.created_at)
    if current.to_dict() != manifest.to_dict():
        raise ContractError("%s bytes no longer match their checked-in seal" % label)
    return manifest


def _descriptor_path(repo_root: Path, path: Path) -> Path:
    requested = Path(path)
    if not requested.is_absolute():
        requested = repo_root / requested
    if requested.is_symlink():
        raise ContractError("draft descriptor must not be a symlink")
    try:
        resolved = requested.resolve(strict=True)
        resolved.relative_to(repo_root)
    except (OSError, ValueError) as exc:
        raise ContractError(
            "draft descriptor must be a checked-in file inside the repository"
        ) from exc
    if not resolved.is_file():
        raise ContractError("draft descriptor must be a regular file")
    return resolved


def _strict_keys(value: Mapping[str, Any], expected: Sequence[str], label: str) -> None:
    if set(value) != set(expected):
        raise ContractError("%s fields are malformed" % label)


@dataclass(frozen=True)
class SealedDraft:
    """Typed, current publication input reconstructed from one descriptor."""

    repo_root: Path
    descriptor_path: Path
    descriptor_sha256: str
    inventor_id: str
    taste: Taste
    wish: Wish
    blueprint: ToyBlueprint
    made: Made
    playtested: Playtested
    make_manifest_path: Path
    evidence_root: Path
    evidence_manifest: ArtifactManifest
    evidence_manifest_path: Path
    playtest_index_path: Path
    instructions_root: Path
    instructions_manifest: ArtifactManifest
    instructions_manifest_path: Path
    page: Mapping[str, Any]
    external_hashes: Sequence[Tuple[Path, str]]

    @property
    def product_id(self) -> str:
        return self.wish.product_id

    @property
    def slug(self) -> str:
        return self.wish.product_id

    def context(self, lease_token: str) -> InstructionsContext:
        return InstructionsContext(
            self.wish,
            self.taste,
            self.blueprint,
            self.made,
            self.playtested,
            self.instructions_root,
            lease_token,
        )

    def assert_current(self) -> None:
        if _sha256_file(self.descriptor_path) != self.descriptor_sha256:
            raise ContractError("draft descriptor changed after it was loaded")
        self.taste.assert_current()
        current_make = build_artifact_manifest(
            self.made.artifact_root,
            created_at=self.made.artifact_manifest.created_at,
        )
        if current_make.to_dict() != self.made.artifact_manifest.to_dict():
            raise ContractError("sealed Make changed during draft publication")
        current_evidence = build_artifact_manifest(
            self.evidence_root,
            created_at=self.evidence_manifest.created_at,
        )
        if current_evidence.to_dict() != self.evidence_manifest.to_dict():
            raise ContractError("sealed Playtest evidence changed during publication")
        current_instructions = build_artifact_manifest(
            self.instructions_root,
            created_at=self.instructions_manifest.created_at,
        )
        if current_instructions.to_dict() != self.instructions_manifest.to_dict():
            raise ContractError("sealed Instructions changed during publication")
        for path, expected in self.external_hashes:
            if _sha256_file(path) != expected:
                raise ContractError(
                    "Playtest authority changed during draft publication: %s"
                    % path.name
                )


def _load_artifact_contract(
    make_root: Path,
    make_manifest: ArtifactManifest,
    inventor_id: str,
    taste: Taste,
) -> Tuple[Wish, Made, ToyBlueprint]:
    inventory = {entry.path for entry in make_manifest.entries}
    required = {"project.json", "product.json", "wish.json"}
    if not required <= inventory:
        raise ContractError(
            "sealed Make requires root project.json, product.json, and wish.json"
        )
    wish_value = _read_json_object(make_root / "wish.json", "sealed Wish")
    _strict_keys(
        wish_value,
        ("schema_version", "product_id", "objective", "constraints", "context"),
        "sealed Wish",
    )
    try:
        wish = Wish(**dict(wish_value))
    except TypeError as exc:
        raise ContractError("sealed Wish contains unknown fields") from exc
    if not _CANONICAL_SLUG.fullmatch(wish.product_id):
        raise ContractError(
            "sealed Wish product_id must be a lowercase canonical Shop slug"
        )
    product = _read_json_object(make_root / "product.json", "sealed product")
    made = Made(make_root, make_manifest, product)
    project = _read_json_object(make_root / "project.json", "Factory project marker")
    if project != {"id": wish.product_id, "name": made.product["title"]}:
        raise ContractError("Factory project marker does not identify the sealed product")
    if (
        made.product.get("product_id") != wish.product_id
        or made.product.get("slug") != wish.product_id
        or made.product.get("wish") != wish.to_dict()
        or made.product.get("inventor")
        != {"id": inventor_id, "name": taste.name}
    ):
        raise ContractError("sealed product loses Wish or inventor identity")
    description = made.product.get("description")
    if attribute_product_description(description, taste.name) != description:
        raise ContractError(
            "sealed product description must end with exactly one inventor credit"
        )
    blueprint = ToyBlueprint.for_lane(made.product["lane"])
    return wish, made, blueprint


def _index_relative(round_root: Path, value: Any, label: str) -> Path:
    candidate = PurePosixPath(value) if isinstance(value, str) else PurePosixPath(".")
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.as_posix() != value
    ):
        raise ContractError("%s must be a safe Playtest-relative path" % label)
    requested = round_root.joinpath(*candidate.parts)
    if requested.is_symlink():
        raise ContractError("%s must not be a symlink" % label)
    try:
        resolved = requested.resolve(strict=True)
        resolved.relative_to(round_root)
    except (OSError, ValueError) as exc:
        raise ContractError("%s is missing or outside Playtest" % label) from exc
    if not resolved.is_file():
        raise ContractError("%s must be a regular file" % label)
    return resolved


def _load_playtested(
    round_root: Path,
    make_manifest: ArtifactManifest,
    evidence_manifest: ArtifactManifest,
    blueprint: ToyBlueprint,
    index_sha256: str,
) -> Tuple[Playtested, Path, Sequence[Tuple[Path, str]]]:
    require_sha256(index_sha256, "Playtest index sha256")
    index_path = round_root / "evidence-index.json"
    index = _read_json_object(index_path, "Playtest evidence index")
    if _sha256_file(index_path) != index_sha256:
        raise ContractError("Playtest index does not match its descriptor hash")
    if (
        index.get("artifact_sha256") != make_manifest.artifact_sha256
        or index.get("overall_passed") is not True
        or index.get("unresolved_canonical_capabilities") != []
    ):
        raise ContractError("Playtest index is not an all-pass result for this Make")
    evidence_record = index.get("evidence_manifest")
    if (
        not isinstance(evidence_record, Mapping)
        or evidence_record.get("artifact_sha256")
        != evidence_manifest.artifact_sha256
        or evidence_record.get("path") != "evidence-manifest.json"
    ):
        raise ContractError("Playtest index points at different evidence bytes")
    evidence_inventory = {
        entry.path: entry.sha256 for entry in evidence_manifest.entries
    }
    raw_results = index.get("results")
    if isinstance(raw_results, (str, bytes)) or not isinstance(raw_results, Sequence):
        raise ContractError("Playtest index results must be an array")
    results = []
    seen = set()
    external: list[Tuple[Path, str]] = [(index_path, index_sha256)]
    for position, item in enumerate(raw_results):
        if not isinstance(item, Mapping):
            raise ContractError("Playtest index result %d is malformed" % position)
        required = {
            "playtest_id",
            "passed",
            "evidence_ref",
            "evidence_sha256",
            "wrapper",
            "wrapper_sha256",
        }
        if not required <= set(item):
            raise ContractError("Playtest index result %d is incomplete" % position)
        playtest_id = item.get("playtest_id")
        if not isinstance(playtest_id, str) or not playtest_id or playtest_id in seen:
            raise ContractError("Playtest index result ids must be unique")
        seen.add(playtest_id)
        wrapper_path = _index_relative(
            round_root, item.get("wrapper"), "Playtest wrapper"
        )
        wrapper_sha = require_sha256(
            item.get("wrapper_sha256"), "Playtest wrapper sha256"
        )
        if _sha256_file(wrapper_path) != wrapper_sha:
            raise ContractError("Playtest wrapper hash mismatch for %s" % playtest_id)
        external.append((wrapper_path, wrapper_sha))
        wrapper_value = _read_json_object(wrapper_path, "Playtest wrapper")
        try:
            wrapper = PlaytestResult(**dict(wrapper_value))
        except TypeError as exc:
            raise ContractError("Playtest wrapper contains unknown fields") from exc
        if (
            wrapper.inspection_id != playtest_id
            or wrapper.passed is not item.get("passed")
            or wrapper.artifact_sha256 != make_manifest.artifact_sha256
            or wrapper.evidence_sha256 != item.get("evidence_sha256")
        ):
            raise ContractError("Playtest wrapper identity mismatch for %s" % playtest_id)
        indexed_ref = item.get("evidence_ref")
        expected_index_ref = "evidence/" + wrapper.evidence_ref
        if indexed_ref != expected_index_ref:
            raise ContractError("Playtest evidence path mismatch for %s" % playtest_id)
        if evidence_inventory.get(wrapper.evidence_ref) != wrapper.evidence_sha256:
            raise ContractError("Playtest result is absent from sealed evidence")
        evidence_path = round_root / "evidence" / wrapper.evidence_ref
        evidence_body = _read_json_object(evidence_path, "Playtest result body")
        if (
            evidence_body.get("artifact_sha256") != make_manifest.artifact_sha256
            or evidence_body.get("passed") is not wrapper.passed
            or evidence_body.get("evidence_class") != "ai-simulation"
        ):
            raise ContractError("Playtest result body is malformed for %s" % playtest_id)
        if playtest_id == "agent-playtest":
            roles = evidence_body.get("agent_roles")
            if (
                isinstance(roles, (str, bytes))
                or not isinstance(roles, Sequence)
                or len(roles) < 2
                or not all(isinstance(role, str) and role.strip() for role in roles)
                or len(set(roles)) != len(roles)
            ):
                raise ContractError(
                    "agent-playtest requires at least two distinct named AI-player roles"
                )
        results.append(
            PlaytestResult(
                wrapper.inspection_id,
                wrapper.passed,
                wrapper.artifact_sha256,
                evidence_body,
                wrapper.evaluator,
                wrapper.evaluator_version,
                wrapper.config_sha256,
                wrapper.evidence_ref,
                wrapper.evidence_sha256,
                wrapper.observed_at,
            )
        )
    required_ids = set(blueprint.required_capabilities("playtest"))
    if seen != required_ids or not all(result.passed for result in results):
        raise ContractError(
            "Playtest must pass exactly the lane's required capabilities"
        )
    summary = index.get("result_summary")
    if isinstance(summary, Mapping) and (
        summary.get("failed") != []
        or set(summary.get("passed") or ()) != required_ids
    ):
        raise ContractError("Playtest result summary contradicts its wrappers")
    feedback_record = index.get("feedback")
    if not isinstance(feedback_record, Mapping):
        raise ContractError("Playtest index is missing feedback identity")
    feedback_path = _index_relative(
        round_root, feedback_record.get("path"), "Playtest feedback"
    )
    feedback_sha = require_sha256(
        feedback_record.get("sha256"), "Playtest feedback sha256"
    )
    if _sha256_file(feedback_path) != feedback_sha:
        raise ContractError("Playtest feedback hash mismatch")
    external.append((feedback_path, feedback_sha))
    feedback_value = _read_json_object(feedback_path, "Playtest feedback")
    if (
        feedback_value.get("artifact_sha256") != make_manifest.artifact_sha256
        or feedback_value.get("overall_passed") is not True
        or not isinstance(feedback_value.get("feedback"), list)
        or feedback_record.get("count") != len(feedback_value["feedback"])
    ):
        raise ContractError("Playtest feedback is not an all-pass record")
    feedback = []
    for item in feedback_value["feedback"]:
        if not isinstance(item, Mapping):
            raise ContractError("Playtest feedback item is malformed")
        try:
            feedback.append(Feedback(**dict(item)))
        except TypeError as exc:
            raise ContractError("Playtest feedback contains unknown fields") from exc
    playtested = Playtested(
        Playtest(
            make_manifest,
            tuple(results),
            evidence_manifest=evidence_manifest,
        ),
        tuple(feedback),
    )
    if not playtested.passed:
        raise ContractError("Instructions require all-pass Playtest with no blockers")
    return playtested, index_path, tuple(external)


def _validate_instructions(
    context: InstructionsContext,
    root: Path,
    manifest: ArtifactManifest,
) -> Mapping[str, Any]:
    page = ShopInstructionsWriter._read_page(root)
    claims = evidence_claims(context)
    expected = {
        "status": "ready",
        "title": str(context.made.product["title"]),
        "summary": attribute_product_description(
            context.made.product["summary"], context.taste.name
        ),
        "lane": context.blueprint.lane,
        "wish": context.wish.objective,
        "product_artifact_sha256": context.made.artifact_sha256,
        "playtest_evidence_artifact_sha256": (
            context.playtested.evidence.evidence_artifact_sha256
        ),
        "claims": claims,
    }
    if any(page.get(key) != value for key, value in expected.items()):
        raise ContractError(
            "sealed Instructions belong to a different Wish, Make, Playtest, or inventor"
        )
    if not (root / "INSTRUCTIONS.md").is_file():
        raise ContractError("sealed Instructions require INSTRUCTIONS.md")
    return page


def load_sealed_draft(
    descriptor: Path,
    *,
    repo_root: Path,
) -> SealedDraft:
    """Load and fully validate a descriptor without touching the network."""

    root = Path(repo_root).resolve(strict=True)
    descriptor_path = _descriptor_path(root, Path(descriptor))
    descriptor_sha = _sha256_file(descriptor_path)
    value = _read_json_object(descriptor_path, "sealed draft descriptor")
    _strict_keys(
        value,
        (
            "schema_version",
            "kind",
            "inventor_id",
            "taste_sha256",
            "make",
            "playtest",
            "instructions",
        ),
        "sealed draft descriptor",
    )
    if value.get("schema_version") != 1 or value.get("kind") != DESCRIPTOR_KIND:
        raise ContractError("sealed draft descriptor kind or version is unsupported")
    inventor_id = value.get("inventor_id")
    if (
        not isinstance(inventor_id, str)
        or not inventor_id
        or any(character in inventor_id for character in "/\\")
    ):
        raise ContractError("sealed draft descriptor inventor_id is malformed")
    inventor_root = _safe_repo_path(
        root, "inventors/%s" % inventor_id, "inventor root", directory=True
    )
    taste = load_taste(inventor_root)
    taste_sha = require_sha256(value.get("taste_sha256"), "descriptor Taste sha256")
    if taste.sha256 != taste_sha:
        raise ContractError("descriptor points at a different inventor Taste")

    make_value = value.get("make")
    playtest_value = value.get("playtest")
    instructions_value = value.get("instructions")
    if not all(
        isinstance(item, Mapping)
        for item in (make_value, playtest_value, instructions_value)
    ):
        raise ContractError("descriptor roots must be objects")
    assert isinstance(make_value, Mapping)
    assert isinstance(playtest_value, Mapping)
    assert isinstance(instructions_value, Mapping)
    _strict_keys(make_value, ("root", "manifest", "artifact_sha256"), "Make descriptor")
    _strict_keys(
        playtest_value,
        ("root", "evidence_artifact_sha256", "index_sha256"),
        "Playtest descriptor",
    )
    _strict_keys(
        instructions_value,
        ("root", "manifest", "artifact_sha256"),
        "Instructions descriptor",
    )
    make_root = _safe_repo_path(
        root, make_value.get("root"), "Make root", directory=True
    )
    make_manifest_path = _safe_repo_path(
        root, make_value.get("manifest"), "Make manifest", directory=False
    )
    make_manifest = _typed_manifest(
        make_root,
        make_manifest_path,
        "Make",
        make_value.get("artifact_sha256"),
    )
    wish, made, blueprint = _load_artifact_contract(
        make_root, make_manifest, inventor_id, taste
    )

    round_root = _safe_repo_path(
        root, playtest_value.get("root"), "Playtest root", directory=True
    )
    evidence_root = round_root / "evidence"
    evidence_manifest_path = round_root / "evidence-manifest.json"
    evidence_manifest = _typed_manifest(
        evidence_root,
        evidence_manifest_path,
        "Playtest evidence",
        playtest_value.get("evidence_artifact_sha256"),
    )
    playtested, index_path, external = _load_playtested(
        round_root,
        make_manifest,
        evidence_manifest,
        blueprint,
        playtest_value.get("index_sha256"),
    )

    instructions_root = _safe_repo_path(
        root, instructions_value.get("root"), "Instructions root", directory=True
    )
    instructions_manifest_path = _safe_repo_path(
        root,
        instructions_value.get("manifest"),
        "Instructions manifest",
        directory=False,
    )
    instructions_manifest = _typed_manifest(
        instructions_root,
        instructions_manifest_path,
        "Instructions",
        instructions_value.get("artifact_sha256"),
    )
    provisional = InstructionsContext(
        wish,
        taste,
        blueprint,
        made,
        playtested,
        instructions_root,
    )
    page = _validate_instructions(provisional, instructions_root, instructions_manifest)
    loaded = SealedDraft(
        root,
        descriptor_path,
        descriptor_sha,
        inventor_id,
        taste,
        wish,
        blueprint,
        made,
        playtested,
        make_manifest_path,
        evidence_root,
        evidence_manifest,
        evidence_manifest_path,
        index_path,
        instructions_root,
        instructions_manifest,
        instructions_manifest_path,
        page,
        external,
    )
    loaded.assert_current()
    return loaded


class CanonicalSlugDoor(ShopDoor):
    """Reject a server-created collision suffix before any page enrichment."""

    def __init__(self, token: str, expected_slug: str, *, transport: Transport) -> None:
        self.expected_slug = expected_slug
        super().__init__(token, transport=transport)

    def import_design_bytes(
        self,
        filename: str,
        content: bytes,
        metadata: Mapping[str, Any],
        *,
        thumbnail: Optional[Mapping[str, Any]] = None,
    ) -> HttpResponse:
        response = super().import_design_bytes(
            filename, content, metadata, thumbnail=thumbnail
        )
        if response.status == 201:
            design = _response_object(response, "Shop import")
            if design.get("slug") != self.expected_slug:
                raise ReceiptError(
                    "Shop import did not preserve the canonical product slug"
                )
        return response


def _collision_preflight(door: ShopDoor, slug: str) -> None:
    try:
        response = door.get_design(slug)
    except Exception as exc:
        raise PublishError(
            "canonical slug preflight failed; no import was attempted"
        ) from exc
    if response.status == 404:
        return
    if response.status == 200:
        raise StateConflict(
            "canonical Shop slug %r already exists; refusing a duplicate" % slug
        )
    raise PublishError(
        "canonical slug preflight returned HTTP %s; no import was attempted"
        % response.status
    )


def _publication_metadata(sealed: SealedDraft) -> Mapping[str, Any]:
    return {
        "schema_version": 1,
        "kind": DESCRIPTOR_KIND,
        "descriptor": sealed.descriptor_path.relative_to(sealed.repo_root).as_posix(),
        "descriptor_sha256": sealed.descriptor_sha256,
        "inventor_id": sealed.inventor_id,
        "taste_sha256": sealed.taste.sha256,
        "wish": sealed.wish.to_dict(),
        "artifact_sha256": sealed.made.artifact_sha256,
        "evidence_sha256": sealed.evidence_manifest.artifact_sha256,
        "instructions_sha256": sealed.instructions_manifest.artifact_sha256,
    }


def _register_exact_product(store: InventorStore, sealed: SealedDraft) -> None:
    expected = _publication_metadata(sealed)
    try:
        product = store.get_product(sealed.product_id)
    except KeyError:
        try:
            product = store.register_product(
                sealed.product_id,
                "instructions",
                metadata=expected,
                artifact_sha256=sealed.made.artifact_sha256,
            )
        except StateConflict:
            product = store.get_product(sealed.product_id)
    if (
        product.get("stage") != "instructions"
        or product.get("revision") != 0
        or product.get("artifact_sha256") != sealed.made.artifact_sha256
        or product.get("metadata") != expected
        or not store.verify_event_chain(sealed.product_id)
    ):
        raise StateConflict(
            "persistent draft state is not bound to this exact descriptor"
        )


def _customer_page_url(slug: str) -> str:
    return DEFAULT_SHOP_PAGE_BASE.rstrip("/") + "/" + urllib.parse.quote(
        slug, safe=""
    )


def _verify_fresh_draft(
    sealed: SealedDraft,
    store: InventorStore,
    door: ShopDoor,
    owner_id: str,
    persisted: PublicationReceipt,
) -> Mapping[str, Any]:
    response = door.get_design(sealed.slug)
    if response.status != 200:
        raise PublishError("fresh Shop draft readback returned HTTP %s" % response.status)
    design = _response_object(response, "fresh Shop draft readback")
    fresh = PublicationReceipt.from_design(
        design, persisted.packet_sha256, sealed.made.artifact_sha256
    )
    fresh.assert_owner(owner_id)
    fresh.assert_artifact(sealed.made.artifact_sha256)
    if (
        not fresh.is_verified_draft
        or fresh.slug != sealed.slug
        or fresh.published_history_id is not None
    ):
        raise ReceiptError("fresh readback does not prove the canonical private draft")
    for field in (
        "design_id",
        "slug",
        "owner_id",
        "root_id",
        "current_history_id",
        "project_url",
    ):
        if getattr(fresh, field) != getattr(persisted, field):
            raise ReceiptError("fresh Shop readback changed %s" % field)
    intent = store.latest_publish_intent(sealed.product_id)
    if intent is None or intent.get("state") != "succeeded":
        raise StateConflict("private draft has no succeeded durable intent")
    request = intent.get("request")
    category = design.get("category")
    if (
        not isinstance(request, Mapping)
        or design.get("title") != request.get("title")
        or design.get("description") != request.get("description")
        or design.get("origin") != "import"
        or design.get("tags") != request.get("tags")
        or not isinstance(category, Mapping)
        or category.get("slug") != request.get("category")
        or design.get("thumbnail_urls") != persisted.details.get("server_cover_urls")
    ):
        raise ReceiptError("fresh Shop readback changed sealed listing content")
    if store.shop_effects_for_publish_intent(intent["id"]):
        raise ReceiptError(
            "Factory-owned enrichment cannot contain Workshop page effects"
        )
    return {
        "status": "verified-draft",
        "enrichment_status": "pending",
        "page_ready": False,
        "slug": sealed.slug,
        "page_url": _customer_page_url(sealed.slug),
        "artifact_sha256": sealed.made.artifact_sha256,
        "instructions_sha256": sealed.instructions_manifest.artifact_sha256,
        "observed_at": fresh.observed_at,
    }


def _access_token(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or value.casefold().startswith("bearer ")
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise ContractError("Shop access token is missing or malformed")
    return value


def _owner_id(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > 512
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise ContractError("Shop owner identity is missing or malformed")
    return value


def publish_sealed_draft(
    descriptor: Path,
    *,
    token: str,
    owner_id: str,
    repo_root: Path,
    state_root: Optional[Path] = None,
    transport: Transport = urllib_transport,
    verify_draft: bool = False,
) -> Mapping[str, Any]:
    """Create or replay one exact private draft without exposing credentials."""

    access_token = _access_token(token)
    expected_owner = _owner_id(owner_id)
    sealed = load_sealed_draft(descriptor, repo_root=repo_root)
    root = (
        Path(state_root)
        if state_root is not None
        else sealed.repo_root / DEFAULT_STATE_DIRECTORY
    )
    if root.exists() and root.is_symlink():
        raise ContractError("draft state root must not be a symlink")
    state_directory = root / sealed.product_id
    if state_directory.exists() and state_directory.is_symlink():
        raise ContractError("product draft state must not be a symlink")
    store = InventorStore(state_directory / "workshop.sqlite3")
    _register_exact_product(store, sealed)
    door = CanonicalSlugDoor(
        access_token, sealed.slug, transport=transport
    )
    lease = store.acquire_lease(sealed.product_id, "sealed-draft-publication")
    try:
        previous_intent = store.latest_publish_intent(sealed.product_id)
        sealed.assert_current()
        if previous_intent is None:
            _collision_preflight(door, sealed.slug)
        context = sealed.context(lease)
        receipt = ShopInstructionsWriter(store, door, expected_owner)(
            context,
            sealed.instructions_root,
            sealed.instructions_manifest,
        )
        product_instructions = ProductInstructions.from_root(
            sealed.instructions_root,
            sealed.made.artifact_sha256,
            "INSTRUCTIONS.md",
            evidence_claims(context),
            receipt,
        )
        sealed.assert_current()
        verification = (
            _verify_fresh_draft(
                sealed, store, door, expected_owner, receipt
            )
            if verify_draft
            else None
        )
    finally:
        store.release_lease(sealed.product_id, lease)
    result: MutableMapping[str, Any] = {
        "schema_version": 1,
        "status": (
            "replayed"
            if previous_intent is not None
            and previous_intent.get("state") == "succeeded"
            else "draft-created"
        ),
        "slug": sealed.slug,
        "page_url": product_instructions.page_url,
        "enrichment_status": receipt.details.get("enrichment_status"),
        "page_ready": receipt.details.get("page_ready"),
        "artifact_sha256": sealed.made.artifact_sha256,
        "evidence_sha256": sealed.evidence_manifest.artifact_sha256,
        "instructions_sha256": sealed.instructions_manifest.artifact_sha256,
        "state": str(state_directory / "workshop.sqlite3"),
    }
    if verification is not None:
        result["draft_verification"] = verification
    return result


__all__ = [
    "CanonicalSlugDoor",
    "DEFAULT_STATE_DIRECTORY",
    "DESCRIPTOR_KIND",
    "SealedDraft",
    "load_sealed_draft",
    "publish_sealed_draft",
]
