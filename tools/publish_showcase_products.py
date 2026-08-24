#!/usr/bin/env python3
"""Publish the five checked-in showcase bundles without rebuilding their bytes.

Each toy gets an ignored, persistent outbox at
``.runtime/showcase-publication/<slug>/workshop.sqlite3``.  A retry therefore
resumes the exact recorded Shop effects instead of importing or uploading a
second copy.  Make and Playtest are deliberately absent from this tool.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
TOOLS_ROOT = REPO_ROOT / "tools"
for import_root in (SRC_ROOT, TOOLS_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import build_showcase_products as showcase

from inventor_workshop.artifacts import (
    ArtifactEntry,
    ArtifactManifest,
    build_artifact_manifest,
)
from inventor_workshop.attribution import attribute_product_description
from inventor_workshop.errors import ContractError, PublishError, ReceiptError, StateConflict
from inventor_workshop.instructions import evidence_claims
from inventor_workshop.jobs import InstructionsContext, Made, Playtested
from inventor_workshop.make import Wish
from inventor_workshop.models import PlaytestResult, PublicationReceipt
from inventor_workshop.playtest import Playtest
from inventor_workshop.shop import (
    DEFAULT_SHOP_PAGE_BASE,
    MAX_RESPONSE_BYTES,
    HttpResponse,
    ShopDoor,
    ShopInstructionsWriter,
    Transport,
    _design_with_normalized_currency,
    urllib_transport,
)
from inventor_workshop.store import InventorStore
from inventor_workshop.taste import Taste, load_taste
from inventor_workshop.toys import ToyBlueprint


_RECONSTRUCTED_OBSERVED_AT = "1970-01-01T00:00:00+00:00"


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path, label: str) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ContractError("%s must be a regular JSON file" % label)
    try:
        content = path.read_bytes()
        if not content or len(content) > MAX_RESPONSE_BYTES:
            raise ContractError("%s is empty or exceeds the JSON limit" % label)
        value = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("%s must contain valid UTF-8 JSON" % label) from exc
    if not isinstance(value, Mapping):
        raise ContractError("%s must contain a JSON object" % label)
    return value


def _response_object(response: HttpResponse, label: str) -> Mapping[str, Any]:
    if type(response.body) is not bytes or len(response.body) > MAX_RESPONSE_BYTES:
        raise ReceiptError("%s response exceeds the JSON limit" % label)
    try:
        value = json.loads(response.body.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReceiptError("%s response is not valid UTF-8 JSON" % label) from exc
    if not isinstance(value, Mapping):
        raise ReceiptError("%s response is not a JSON object" % label)
    return value


def _typed_manifest(root: Path, path: Path, label: str) -> ArtifactManifest:
    value = _read_object(path, "%s manifest" % label)
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
    current = build_artifact_manifest(
        root.resolve(strict=True), created_at=manifest.created_at
    )
    if current.to_dict() != manifest.to_dict():
        raise ContractError("%s bytes no longer match their checked-in seal" % label)
    return manifest


def _load_profile(repo_root: Path, inventor_id: str) -> Any:
    path = repo_root / "inventors" / inventor_id / "profile.py"
    if path.is_symlink() or not path.is_file():
        raise ContractError("showcase inventor profile is missing: %s" % path)
    name = "showcase_publish_%s_%s" % (
        inventor_id,
        hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12],
    )
    module_spec = importlib.util.spec_from_file_location(name, path)
    if module_spec is None or module_spec.loader is None:
        raise ContractError("cannot load showcase inventor profile: %s" % path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def _config_sha256(playtest_id: str) -> str:
    return _sha256_bytes(
        _canonical(
            {
                "evaluator": showcase.PLAYTEST_ID,
                "version": showcase.EVALUATOR_VERSION,
                "check": playtest_id,
                "bed_mm": showcase.BED_MM,
                "simulation_games": (
                    showcase.SIMULATION_GAMES
                    if playtest_id == "game-simulation"
                    else None
                ),
                "simulation_seed": (
                    showcase.SIMULATION_SEED
                    if playtest_id == "game-simulation"
                    else None
                ),
            }
        )
    )


@dataclass(frozen=True)
class SealedShowcase:
    spec: Any
    bundle: Path
    run_receipt: Mapping[str, Any]
    wish: Wish
    taste: Taste
    blueprint: ToyBlueprint
    made: Made
    playtested: Playtested
    artifact_manifest: ArtifactManifest
    evidence_manifest: ArtifactManifest
    instructions_manifest: ArtifactManifest
    page: Mapping[str, Any]

    def context(self, lease_token: str) -> InstructionsContext:
        return InstructionsContext(
            self.wish,
            self.taste,
            self.blueprint,
            self.made,
            self.playtested,
            (self.bundle / "instructions").resolve(strict=True),
            lease_token,
        )


def _load_sealed_showcase(
    spec: Any, *, repo_root: Path = REPO_ROOT
) -> SealedShowcase:
    repo_root = Path(repo_root).resolve(strict=True)
    bundle = (
        repo_root / "inventors" / spec.inventor_id / "toys" / spec.slug
    ).resolve(strict=True)

    run_receipt = _read_object(bundle / "workshop-run.json", "Workshop run")
    product = _read_object(bundle / "artifact" / "product.json", "product")
    page = _read_object(bundle / "instructions" / "product.json", "product page")
    artifact_manifest = _typed_manifest(
        bundle / "artifact", bundle / "artifact-manifest.json", "artifact"
    )
    evidence_manifest = _typed_manifest(
        bundle / "evidence", bundle / "evidence-manifest.json", "evidence"
    )
    instructions_manifest = _typed_manifest(
        bundle / "instructions",
        bundle / "instructions-manifest.json",
        "Instructions",
    )

    run = run_receipt.get("run")
    shared = run_receipt.get("shared_adapters")
    if (
        run_receipt.get("schema_version") != 1
        or run_receipt.get("kind") != "showcase-workshop-run"
        or not isinstance(run, Mapping)
        or run.get("product_id") != spec.slug
        or run.get("status") != "waiting"
        or run.get("job") not in ("instructions", "deliver")
        or run.get("round") != 1
        or run.get("playtest_rounds") != spec.playtest_rounds
        or run.get("artifact_sha256") != artifact_manifest.artifact_sha256
        or run.get("delivery") is not None
        or run_receipt.get("artifact_sha256") != artifact_manifest.artifact_sha256
        or run_receipt.get("evidence_sha256") != evidence_manifest.artifact_sha256
        or run_receipt.get("instructions_sha256")
        != instructions_manifest.artifact_sha256
        or not isinstance(shared, Mapping)
        or shared.get("make") != showcase.BUILDER_ID
        or shared.get("playtest") != showcase.PLAYTEST_ID
        or shared.get("builder_path") != "tools/build_showcase_products.py"
        or shared.get("builder_sha256")
        != _sha256_file(Path(showcase.__file__).resolve())
    ):
        raise ContractError("checked-in Workshop receipt no longer binds this sealed bundle")
    if run.get("job") == "instructions":
        if run_receipt.get("site_receipt") is not None or run.get("page_url") is not None:
            raise ContractError("Instructions wait must not claim a live product page")
    elif not isinstance(run_receipt.get("site_receipt"), Mapping) or not run.get("page_url"):
        raise ContractError("Deliver wait must preserve its verified product page")

    profile = _load_profile(repo_root, spec.inventor_id)
    profile_record = getattr(profile, "PROFILE", None)
    if (
        not isinstance(profile_record, Mapping)
        or profile_record.get("inventor_id") != spec.inventor_id
        or profile_record.get("lane") != spec.lane
        or profile_record.get("workshop_level") != spec.extension_level
    ):
        raise ContractError("inventor profile does not match the showcase spec")
    stored_wish = run_receipt.get("wish")
    if not isinstance(stored_wish, Mapping):
        raise ContractError("Workshop run is missing its typed Wish")
    try:
        wish = Wish(**dict(stored_wish))
    except TypeError as exc:
        raise ContractError("Workshop run Wish contains unknown fields") from exc
    expected_wish = profile.create_wish(spec.slug, spec.objective)
    if not isinstance(expected_wish, Wish) or expected_wish.to_dict() != wish.to_dict():
        raise ContractError("checked-in Wish no longer matches the inventor profile")

    taste = load_taste(repo_root / "inventors" / spec.inventor_id)
    blueprint = ToyBlueprint.for_lane(spec.lane)
    inventor = run_receipt.get("inventor")
    if (
        taste.name != spec.inventor_name
        or run_receipt.get("taste_sha256") != taste.sha256
        or run_receipt.get("blueprint_sha256") != blueprint.sha256
        or not isinstance(inventor, Mapping)
        or inventor.get("id") != spec.inventor_id
        or inventor.get("name") != spec.inventor_name
    ):
        raise ContractError("Taste, blueprint, or inventor binding changed")

    if product.get("wish") != wish.to_dict():
        raise ContractError("product bytes contain a different Wish")
    if (
        product.get("product_id") != spec.slug
        or product.get("slug") != spec.slug
        or product.get("title") != spec.title
        or product.get("summary") != spec.summary
        or product.get("description")
        != attribute_product_description(spec.description, spec.inventor_name)
        or product.get("inventor")
        != {"id": spec.inventor_id, "name": spec.inventor_name}
        or product.get("physical_prototype") is not False
        or product.get("reviews_status") != "begins-after-delivery"
    ):
        raise ContractError("sealed product metadata no longer matches the showcase spec")
    made = Made(
        (bundle / "artifact").resolve(strict=True),
        artifact_manifest,
        {
            "title": product.get("title"),
            "summary": product.get("summary"),
            "lane": product.get("lane"),
        },
    )
    if (
        page.get("title") != product.get("title")
        or page.get("lane") != product.get("lane")
        or page.get("summary")
        != attribute_product_description(product.get("summary"), taste.name)
    ):
        raise ContractError("sealed product page does not describe the exact Made result")

    index = _read_object(bundle / "evidence" / "evidence-index.json", "evidence index")
    if (
        index.get("evaluator") != showcase.PLAYTEST_ID
        or index.get("evaluator_version") != showcase.EVALUATOR_VERSION
        or index.get("artifact_sha256") != artifact_manifest.artifact_sha256
        or index.get("status") != "passed-ai-playtest"
        or index.get("unresolved_canonical_capabilities") != []
    ):
        raise ContractError("checked-in AI Playtest index is not an exact pass")
    checks = index.get("validated_checks")
    if not isinstance(checks, list) or not checks:
        raise ContractError("checked-in AI Playtest index has no validated checks")
    evidence_inventory = {
        entry.path: entry.sha256 for entry in evidence_manifest.entries
    }
    results = []
    seen = set()
    for check in checks:
        if not isinstance(check, Mapping) or set(check) != {
            "playtest_id",
            "evidence_ref",
        }:
            raise ContractError("AI Playtest index contains a malformed check")
        playtest_id = check["playtest_id"]
        evidence_ref = check["evidence_ref"]
        if playtest_id in seen or evidence_inventory.get(evidence_ref) is None:
            raise ContractError("AI Playtest index contains a duplicate or unsealed check")
        seen.add(playtest_id)
        evidence_path = bundle / "evidence" / evidence_ref
        evidence = _read_object(evidence_path, "AI Playtest evidence")
        evidence_sha256 = _sha256_file(evidence_path)
        customer_review = evidence.get("customer_review")
        if (
            evidence_sha256 != evidence_inventory[evidence_ref]
            or evidence.get("artifact_sha256") != artifact_manifest.artifact_sha256
            or evidence.get("evidence_class") != "ai-simulation"
            or (
                playtest_id != "game-simulation"
                and customer_review is not False
            )
            or (
                playtest_id == "game-simulation"
                and customer_review not in (None, False)
            )
        ):
            raise ContractError("AI Playtest evidence is not bound to these product bytes")
        if playtest_id == "game-simulation":
            simulator_path = evidence.get("simulator_path")
            simulator_relative = (
                Path(simulator_path) if isinstance(simulator_path, str) else Path(".")
            )
            simulator = (
                bundle / "artifact" / simulator_relative
                if isinstance(simulator_path, str)
                else bundle / "artifact" / "."
            )
            if (
                not isinstance(simulator_path, str)
                or not simulator_path
                or simulator_relative.is_absolute()
                or ".." in simulator_relative.parts
                or simulator_relative.as_posix() != simulator_path
                or evidence.get("executable") is not True
                or evidence.get("completed_games", 0) < 1_000
                or evidence.get("terminated_games")
                != evidence.get("completed_games")
                or evidence.get("nonterminating_games") != 0
                or set(evidence.get("player_styles") or ())
                != {"optimizing", "social", "exploratory", "adversarial"}
                or not simulator.is_file()
                or evidence.get("simulator_sha256") != _sha256_file(simulator)
            ):
                raise ContractError(
                    "game-simulation evidence is not a sealed executable AI Playtest"
                )
        results.append(
            PlaytestResult(
                playtest_id,
                True,
                artifact_manifest.artifact_sha256,
                evidence,
                showcase.PLAYTEST_ID,
                showcase.EVALUATOR_VERSION,
                _config_sha256(playtest_id),
                evidence_ref,
                evidence_sha256,
                _RECONSTRUCTED_OBSERVED_AT,
            )
        )
    required = set(blueprint.required_capabilities("playtest"))
    if seen != required:
        raise ContractError("AI Playtest evidence no longer covers the lane blueprint")
    playtested = Playtested(
        Playtest(
            artifact_manifest,
            tuple(results),
            evidence_manifest=evidence_manifest,
        )
    )
    provisional = InstructionsContext(
        wish,
        taste,
        blueprint,
        made,
        playtested,
        (bundle / "instructions").resolve(strict=True),
    )
    if page.get("claims") != evidence_claims(provisional):
        raise ContractError("sealed page claims do not match typed AI Playtest evidence")

    # Validate recorded file identities without opening CAD kernels or executing
    # the checked-in game simulator. Publication consumes seals; it never reruns
    # Make or Playtest.
    digital_build = _read_object(
        bundle / "artifact" / "cad" / "digital-build.json", "digital build"
    )
    generator = digital_build.get("generator")
    product_build = digital_build.get("product")
    parts = digital_build.get("parts")
    render = digital_build.get("render")
    if (
        not isinstance(generator, Mapping)
        or generator.get("id") != showcase.BUILDER_ID
        or generator.get("sha256") != shared.get("builder_sha256")
        or not isinstance(product_build, Mapping)
        or not isinstance(parts, Mapping)
        or not isinstance(render, Mapping)
    ):
        raise ContractError("digital build identity is malformed")
    for suffix in ("step", "stl"):
        recorded = product_build.get(suffix)
        path = bundle / "artifact" / "cad" / ("product." + suffix)
        if (
            not isinstance(recorded, Mapping)
            or recorded.get("sha256") != _sha256_file(path)
            or recorded.get("bytes") != path.stat().st_size
        ):
            raise ContractError("digital build points at different product %s bytes" % suffix)
    for part_name, part in parts.items():
        if not isinstance(part_name, str) or not isinstance(part, Mapping):
            raise ContractError("digital build contains a malformed part")
        for suffix in ("step", "stl"):
            recorded = part.get(suffix)
            path = bundle / "artifact" / "cad" / "parts" / (part_name + "." + suffix)
            if (
                not isinstance(recorded, Mapping)
                or recorded.get("sha256") != _sha256_file(path)
                or recorded.get("bytes") != path.stat().st_size
            ):
                raise ContractError("digital build points at different part bytes")
    hero = bundle / "artifact" / "images" / "hero.png"
    if (
        render.get("input_sha256") != product_build["stl"].get("sha256")
        or render.get("output_sha256") != _sha256_file(hero)
    ):
        raise ContractError("exact-geometry render identity is malformed")

    return SealedShowcase(
        spec,
        bundle,
        run_receipt,
        wish,
        taste,
        blueprint,
        made,
        playtested,
        artifact_manifest,
        evidence_manifest,
        instructions_manifest,
        page,
    )


def _assert_sealed_inputs_current(sealed: SealedShowcase) -> None:
    for directory, manifest, label in (
        ("artifact", sealed.artifact_manifest, "artifact"),
        ("evidence", sealed.evidence_manifest, "evidence"),
        ("instructions", sealed.instructions_manifest, "Instructions"),
    ):
        current = build_artifact_manifest(
            (sealed.bundle / directory).resolve(strict=True),
            created_at=manifest.created_at,
        )
        if current.to_dict() != manifest.to_dict():
            raise ContractError("sealed %s bytes changed during publication" % label)
    sealed.taste.assert_current()


def _customer_page_url(slug: str) -> str:
    return DEFAULT_SHOP_PAGE_BASE.rstrip("/") + "/" + urllib.parse.quote(slug, safe="")


class _CanonicalSlugDoor(ShopDoor):
    """Stop immediately if an import race creates a collision-suffixed draft."""

    def __init__(self, token: str, expected_slug: str, *, transport: Transport) -> None:
        self.expected_slug = expected_slug
        super().__init__(token, transport=transport)

    def import_design_bytes(
        self, filename: str, content: bytes, metadata: Mapping[str, Any]
    ) -> HttpResponse:
        response = super().import_design_bytes(filename, content, metadata)
        if response.status == 201:
            design = _response_object(response, "Shop import")
            if design.get("slug") != self.expected_slug:
                raise ReceiptError(
                    "Shop import did not preserve the canonical showcase slug; "
                    "the draft outcome is ambiguous and must not be published"
                )
        return response


def _publication_metadata(sealed: SealedShowcase, repo_root: Path) -> Mapping[str, Any]:
    return {
        "schema_version": 1,
        "kind": "checked-in-showcase-publication",
        "bundle": sealed.bundle.relative_to(repo_root.resolve(strict=True)).as_posix(),
        "inventor": {
            "id": sealed.spec.inventor_id,
            "name": sealed.spec.inventor_name,
        },
        "slug": sealed.spec.slug,
        "lane": sealed.spec.lane,
        "wish": sealed.wish.to_dict(),
        "taste_sha256": sealed.taste.sha256,
        "blueprint_sha256": sealed.blueprint.sha256,
        "artifact_sha256": sealed.artifact_manifest.artifact_sha256,
        "evidence_sha256": sealed.evidence_manifest.artifact_sha256,
        "instructions_sha256": sealed.instructions_manifest.artifact_sha256,
    }


def _register_exact_product(
    store: InventorStore, sealed: SealedShowcase, repo_root: Path
) -> None:
    expected_metadata = _publication_metadata(sealed, repo_root)
    try:
        product = store.get_product(sealed.spec.slug)
    except KeyError:
        try:
            product = store.register_product(
                sealed.spec.slug,
                "instructions",
                metadata=expected_metadata,
                artifact_sha256=sealed.artifact_manifest.artifact_sha256,
            )
        except StateConflict:
            product = store.get_product(sealed.spec.slug)
    if (
        product.get("stage") != "instructions"
        or product.get("revision") != 0
        or product.get("artifact_sha256")
        != sealed.artifact_manifest.artifact_sha256
        or product.get("metadata") != expected_metadata
        or not store.verify_event_chain(sealed.spec.slug)
    ):
        raise StateConflict(
            "persistent showcase state is not bound to this exact checked-in bundle"
        )


def _collision_preflight(door: ShopDoor, slug: str) -> None:
    """Require proof that the canonical slug is unused before the first import."""

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
            "canonical Shop slug %r already exists; refusing a collision-suffixed duplicate"
            % slug
        )
    raise PublishError(
        "canonical slug preflight returned HTTP %s; no import was attempted"
        % response.status
    )


def _assert_public_receipt(
    receipt: PublicationReceipt, sealed: SealedShowcase, owner_id: str
) -> str:
    if not isinstance(receipt, PublicationReceipt):
        raise ReceiptError("Shop writer did not return a typed publication Receipt")
    receipt.assert_owner(owner_id)
    receipt.assert_artifact(sealed.artifact_manifest.artifact_sha256)
    if not receipt.is_verified_public:
        raise ReceiptError("Shop receipt does not prove a current public USD listing")
    if receipt.slug != sealed.spec.slug:
        raise ReceiptError("Shop receipt does not preserve the canonical showcase slug")
    page_url = _customer_page_url(sealed.spec.slug)
    if receipt.details.get("page_url") != page_url:
        raise ReceiptError("Shop receipt does not identify the canonical customer page")
    if (
        receipt.details.get("instructions_sha256")
        != sealed.instructions_manifest.artifact_sha256
        or receipt.details.get("playtest_evidence_sha256")
        != sealed.evidence_manifest.artifact_sha256
    ):
        raise ReceiptError("Shop receipt is not bound to exact Instructions and Playtest bytes")
    return page_url


def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".%s." % path.name, dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _mark_waiting_at_deliver(
    sealed: SealedShowcase, receipt: PublicationReceipt, page_url: str
) -> None:
    run_path = sealed.bundle / "workshop-run.json"
    readme_path = sealed.bundle / "README.md"
    old_run = run_path.read_bytes()
    old_readme = readme_path.read_bytes()
    record: MutableMapping[str, Any] = json.loads(old_run.decode("utf-8"))
    run = record.get("run")
    assertions = record.get("assertions")
    if not isinstance(run, MutableMapping) or not isinstance(assertions, MutableMapping):
        raise ContractError("Workshop run cannot record its verified public page")
    run.update(
        {
            "status": "waiting",
            "job": "deliver",
            "instructions_sha256": sealed.instructions_manifest.artifact_sha256,
            "page_url": page_url,
            "delivery": None,
            "needs": [
                {
                    "job": "deliver",
                    "capability": "production-and-shipping",
                    "reason": "The toy and its Instructions are approved, but no real print/QA/packing/carrier implementation is configured.",
                    "instructions": "Configure the shared production bench and USPS, UPS, or FedEx handoff; preserve receipts for the exact artifact hashes.",
                }
            ],
        }
    )
    record["site_receipt"] = receipt.to_dict()
    assertions["site_page_live"] = True
    assertions["physical_prototype"] = False
    assertions["customer_reviews"] = False
    assertions["delivered"] = False
    run_bytes = (
        json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    readme_bytes = showcase._bundle_readme(sealed.spec, run).encode("utf-8")
    try:
        _atomic_write(run_path, run_bytes)
        _atomic_write(readme_path, readme_bytes)
        persisted = _read_object(run_path, "published Workshop run")
        persisted_run = persisted.get("run")
        persisted_receipt = persisted.get("site_receipt")
        if (
            not isinstance(persisted_run, Mapping)
            or persisted_run.get("job") != "deliver"
            or persisted_run.get("status") != "waiting"
            or persisted_run.get("instructions_sha256")
            != sealed.instructions_manifest.artifact_sha256
            or persisted_run.get("page_url") != page_url
            or not isinstance(persisted_receipt, Mapping)
        ):
            raise ContractError("published Workshop run did not preserve Deliver state")
        _assert_public_receipt(
            PublicationReceipt.from_dict(persisted_receipt),
            sealed,
            receipt.owner_id,
        )
        if readme_path.read_bytes() != readme_bytes:
            raise ContractError("published showcase README did not preserve verified page state")
        _assert_sealed_inputs_current(sealed)
    except Exception:
        _atomic_write(run_path, old_run)
        _atomic_write(readme_path, old_readme)
        raise


def _verify_live(
    sealed: SealedShowcase,
    store: InventorStore,
    door: ShopDoor,
    owner_id: str,
) -> Mapping[str, Any]:
    intent = store.latest_publish_intent(sealed.spec.slug)
    if intent is None or intent.get("state") != "live":
        raise StateConflict("showcase has no durable live publication to verify")
    persisted = PublicationReceipt.from_dict(intent.get("receipt"))
    page_url = _assert_public_receipt(persisted, sealed, owner_id)
    response = door.get_design(sealed.spec.slug)
    if response.status != 200:
        raise PublishError("fresh Shop readback returned HTTP %s" % response.status)
    design = _response_object(response, "fresh Shop readback")
    fresh = PublicationReceipt.from_design(
        _design_with_normalized_currency(design),
        intent["packet_sha256"],
        sealed.artifact_manifest.artifact_sha256,
    )
    fresh.assert_owner(owner_id)
    fresh.assert_artifact(sealed.artifact_manifest.artifact_sha256)
    if not fresh.is_verified_public or fresh.slug != sealed.spec.slug:
        raise ReceiptError("fresh Shop readback does not prove the canonical public page")
    for field in (
        "design_id",
        "slug",
        "owner_id",
        "root_id",
        "current_history_id",
        "published_history_id",
        "project_url",
        "listing_active",
        "listing_price_cents",
        "listing_currency",
        "listing_sku",
    ):
        if getattr(fresh, field) != getattr(persisted, field):
            raise ReceiptError("fresh Shop readback changed %s" % field)
    request = intent.get("request")
    live_request = intent.get("live_request")
    if not isinstance(request, Mapping) or not isinstance(live_request, Mapping):
        raise ReceiptError("durable Shop publication request is malformed")
    if design.get("title") != request.get("title") or design.get("description") != request.get("description"):
        raise ReceiptError("fresh Shop readback changed sealed title or attribution")
    observed_attachments = design.get("attachments")
    if not isinstance(observed_attachments, list):
        raise ReceiptError("fresh Shop readback attachments are malformed")
    projected = [
        {"kind": item.get("kind"), "url": item.get("url")}
        for item in observed_attachments
        if isinstance(item, Mapping)
    ]
    if len(projected) != len(observed_attachments) or projected != live_request.get("attachments"):
        raise ReceiptError("fresh Shop readback changed exact Instructions media")
    for effect in store.shop_effects_for_publish_intent(intent["id"]):
        if effect.get("kind") not in ("use-case", "story-blocks"):
            continue
        effect_request = effect.get("request")
        if (
            effect.get("state") != "succeeded"
            or not isinstance(effect_request, Mapping)
            or not ShopInstructionsWriter._content_matches(
                effect["kind"], design, effect_request.get("content")
            )
        ):
            raise ReceiptError("fresh Shop readback changed sealed Instructions copy")
    proof = live_request.get("proof")
    if not isinstance(proof, Mapping):
        raise ReceiptError("durable Shop publication lacks exact local proof")
    media_hashes = {
        role: _sha256_file(sealed.bundle / "instructions" / relative)
        for role, relative in sealed.page["images"].items()
    }
    public_request: MutableMapping[str, Any] = {
        "attachments": live_request.get("attachments")
    }
    if live_request.get("listing") is not None:
        public_request["listing"] = live_request["listing"]
    expected_proof = {
        "instructions_sha256": sealed.instructions_manifest.artifact_sha256,
        "playtest_evidence_sha256": sealed.evidence_manifest.artifact_sha256,
        "page_url": page_url,
        "media_sha256": media_hashes,
        "page_content_sha256": _sha256_bytes(_canonical(sealed.page)),
        "listing_request_sha256": _sha256_bytes(_canonical(public_request)),
    }
    if proof != expected_proof or any(
        persisted.details.get(key) != value for key, value in expected_proof.items()
    ):
        raise ReceiptError("durable Shop receipt proof no longer matches checked-in bytes")
    return {
        "status": "verified-live",
        "slug": sealed.spec.slug,
        "page_url": page_url,
        "artifact_sha256": sealed.artifact_manifest.artifact_sha256,
        "instructions_sha256": sealed.instructions_manifest.artifact_sha256,
        "observed_at": fresh.observed_at,
    }


def publish_one(
    spec: Any,
    *,
    token: str,
    owner_id: str,
    repo_root: Path = REPO_ROOT,
    state_root: Optional[Path] = None,
    transport: Transport = urllib_transport,
    verify_live: bool = False,
) -> Mapping[str, Any]:
    if not isinstance(token, str) or not token.strip() or "\r" in token or "\n" in token:
        raise ContractError("WORKSHOP_SHOP_TOKEN is required")
    if not isinstance(owner_id, str) or not owner_id.strip():
        raise ContractError("WORKSHOP_SHOP_OWNER_ID is required")
    repo_root = Path(repo_root).resolve(strict=True)
    sealed = _load_sealed_showcase(spec, repo_root=repo_root)
    root = Path(state_root) if state_root is not None else (
        repo_root / ".runtime" / "showcase-publication"
    )
    if root.exists() and root.is_symlink():
        raise ContractError("showcase publication state root must not be a symlink")
    state_directory = root / spec.slug
    if state_directory.exists() and state_directory.is_symlink():
        raise ContractError("showcase publication state directory must not be a symlink")
    store = InventorStore(state_directory / "workshop.sqlite3")
    _register_exact_product(store, sealed, repo_root)
    door = _CanonicalSlugDoor(token, spec.slug, transport=transport)
    lease = store.acquire_lease(spec.slug, "showcase-publication")
    try:
        previous_intent = store.latest_publish_intent(spec.slug)
        if previous_intent is None:
            _collision_preflight(door, spec.slug)
        context = sealed.context(lease)
        receipt = ShopInstructionsWriter(store, door, owner_id)(
            context,
            (sealed.bundle / "instructions").resolve(strict=True),
            sealed.instructions_manifest,
        )
        page_url = _assert_public_receipt(receipt, sealed, owner_id)
        # Recheck all three exact seals after the network work. If anything
        # changed in flight, retain the durable receipt but do not edit the repo.
        # This does not execute CAD generation, AI players, or the simulator.
        _assert_sealed_inputs_current(sealed)
        _mark_waiting_at_deliver(sealed, receipt, page_url)
        live_record = _verify_live(sealed, store, door, owner_id) if verify_live else None
    finally:
        store.release_lease(spec.slug, lease)
    result: MutableMapping[str, Any] = {
        "inventor": spec.inventor_name,
        "slug": spec.slug,
        "status": (
            "replayed"
            if previous_intent is not None and previous_intent.get("state") == "live"
            else "published"
        ),
        "page_url": page_url,
        "artifact_sha256": sealed.artifact_manifest.artifact_sha256,
        "evidence_sha256": sealed.evidence_manifest.artifact_sha256,
        "instructions_sha256": sealed.instructions_manifest.artifact_sha256,
        "state": str(state_directory / "workshop.sqlite3"),
    }
    if live_record is not None:
        result["live_verification"] = live_record
    return result


def _credentials(environ: Mapping[str, str]) -> tuple[str, str]:
    token = environ.get("WORKSHOP_SHOP_TOKEN")
    owner_id = environ.get("WORKSHOP_SHOP_OWNER_ID")
    if not token or not token.strip() or not owner_id or not owner_id.strip():
        raise SystemExit(
            "WORKSHOP_SHOP_TOKEN and WORKSHOP_SHOP_OWNER_ID are both required"
        )
    return token, owner_id


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="inventor id or product slug (repeatable; defaults to all five)",
    )
    parser.add_argument(
        "--verify-live",
        action="store_true",
        help="perform one additional authenticated fresh GET after publish/replay",
    )
    args = parser.parse_args(argv)
    token, owner_id = _credentials(os.environ)
    records = []
    for spec in showcase._selected_specs(args.only):
        record = publish_one(
            spec,
            token=token,
            owner_id=owner_id,
            verify_live=args.verify_live,
        )
        records.append(record)
        print("%s %s %s" % (record["status"], spec.inventor_name, record["page_url"]), flush=True)
    print(
        json.dumps(
            {"schema_version": 1, "publications": records},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
