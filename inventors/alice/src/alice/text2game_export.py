"""Deterministic bridge from a verified text2game run to a Vibe game draft.

``nohope88/text2game`` is useful upstream R&D: it invents rules, builds
CadQuery geometry, renders the assembled game, and slices every printable
part.  Its own ``publish.py`` is intentionally *not* used here.  The existing
Vibe Ideas operator already creates the richer Shop Door draft and Alice's
``ShopDoorAdapter`` adds the exact remote readback and single-writer fence.

This module owns the seam between those systems.  It accepts an immutable
Alice rules artifact plus the exact source hashes independently accepted by
``physical.cad`` and ``physical.dfm``.  It then creates the Vibe workspace
that ``board-game/tools/publish.py <slug>`` expects.  It is pure filesystem
work: it never invokes either publisher, never edits ``QUEUE.json``, and never
claims that a game is shipped.

The source hash maps use paths relative to the text2game product directory,
not paths relative to the text2game repository.  Every file that can affect
the exported game must be present in both maps with the same digest.  An
identical rerun is a no-op; any differing pre-existing destination is an
explicit conflict that must be reconciled by a person or a higher-level Alice
operation.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import stat
import tempfile
import urllib.parse
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .page_builder import snapshot_project


TEXT2GAME_REPOSITORY = "https://github.com/nohope88/text2game"
EXPORT_SCHEMA_VERSION = 1
REQUIRED_RULES_ARCHIVE_CONTRACT = "project-rules-byte-exact-v1"
REQUIRED_ALICE_DRAFT_HANDOFF_CONTRACT = "alice-text2game-export-v1"
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SEMANTIC_ID = re.compile(r"^[a-z][a-z0-9_-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_RULE_FIELDS = (
    "setup",
    "turn",
    "legal_actions",
    "end",
    "scoring",
    "ties",
    "rules_markdown",
)
_EVIDENCE_FILES = (
    "gdd.md",
    "components.json",
    "phase1.json",
    "consistency.json",
    "critic.json",
    "referee.md",
    "priorart.json",
    "phase2.json",
    "gate.json",
    "slice_report.json",
    "phase3.json",
    "plates.json",
    "rulebook.md",
    "print_kit.md",
    "art_direction.md",
    "part_colors.json",
    "renders/assembled.png",
)
_PROJECT_RESERVED_ROOTS = frozenset(
    {
        "RULES.md",
        "alice-provenance.json",
        "alice-text2game-provenance.json",
        "bill.json",
        "cad_project.json",
        "gate.json",
        "spec.md",
    }
)
_MAX_SOURCE_FILES = 20_000
_MAX_SOURCE_BYTES = 20 << 30


class Text2GameExportError(ValueError):
    """The source run or requested handoff is not exact enough to export."""


class Text2GameExportConflict(Text2GameExportError):
    """The destination already exists with bytes from a different export."""


@dataclass(frozen=True, slots=True)
class Text2GameExportRequest:
    """All authority required for one offline export.

    ``accepted_rules`` is the complete accepted ``candidate.rules`` document.
    Its seven canonical fields are hashed exactly the same way as Alice's
    engine.  ``accepted_game`` supplies storefront facts that are not inferred
    from Markdown: title, concept, players, play time, and component copy.

    ``cad_artifact_hashes`` and ``dfm_artifact_hashes`` bind source-relative
    text2game files.  DFM must have reviewed the exact CAD map.
    """

    source_dir: Path
    vibe_workspace: Path
    production_slug: str
    candidate_id: str
    candidate_version: int
    candidate_content_sha256: str
    accepted_game: Mapping[str, Any]
    accepted_rules: Mapping[str, Any]
    accepted_rules_sha256: str
    cad_artifact_hashes: Mapping[str, str]
    dfm_artifact_hashes: Mapping[str, str]
    source_repo_url: str = TEXT2GAME_REPOSITORY
    source_repo_commit: str = ""


@dataclass(frozen=True, slots=True)
class Text2GameExportReceipt:
    """Immutable local handoff plus the lineage ShopDoorAdapter consumes."""

    destination: Path
    candidate_id: str
    candidate_version: int
    candidate_content_sha256: str
    production_slug: str
    rules_sha256: str
    rules_file_sha256: str
    idea_sha256: str
    project_sha256: str
    artifact_hashes: Mapping[str, str]
    source_artifact_hashes: Mapping[str, str]
    source_artifact_hashes_sha256: str
    source_snapshot_sha256: str
    source_repo_url: str
    source_repo_commit: str
    export_receipt_sha256: str

    def page_builder_lineage(self) -> dict[str, Any]:
        """Return the exact content shape for CAD/DFM and rich-draft lineage."""

        return {
            "slug": self.production_slug,
            "production_slug": self.production_slug,
            "candidate_id": self.candidate_id,
            "candidate_version": self.candidate_version,
            "candidate_content_sha256": self.candidate_content_sha256,
            "rules_sha256": self.rules_sha256,
            "rules_file_sha256": self.rules_file_sha256,
            "vibe_idea_sha256": self.idea_sha256,
            "project_sha256": self.project_sha256,
            "artifact_hashes": dict(sorted(self.artifact_hashes.items())),
            "text2game_source_artifact_hashes": dict(
                sorted(self.source_artifact_hashes.items())
            ),
            "text2game_source_artifact_hashes_sha256": (
                self.source_artifact_hashes_sha256
            ),
            "text2game_export_receipt_sha256": self.export_receipt_sha256,
            "text2game_source_snapshot_sha256": self.source_snapshot_sha256,
            "text2game_repo_url": self.source_repo_url,
            "text2game_repo_commit": self.source_repo_commit,
        }


@dataclass(frozen=True, slots=True)
class _SourceSnapshot:
    files: tuple[dict[str, Any], ...]
    sha256: str
    total_bytes: int


@dataclass(frozen=True, slots=True)
class _ValidatedSource:
    root: Path
    snapshot: _SourceSnapshot
    components: tuple[dict[str, Any], ...]
    phase1: Mapping[str, Any]
    phase2: Mapping[str, Any]
    phase3: Mapping[str, Any]
    gate: Mapping[str, Any]
    slice_report: Mapping[str, Any]
    assembly_step: str
    part_meshes: tuple[str, ...]
    gcode_files: tuple[str, ...]
    evidence_hashes: Mapping[str, str]
    accepted_source_hashes: Mapping[str, str]


def canonical_sha256(value: Any) -> str:
    """Alice's canonical JSON SHA-256 (kept local to avoid execution coupling)."""

    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise Text2GameExportError("accepted data must be finite canonical JSON") from exc
    return hashlib.sha256(encoded).hexdigest()


def _canonical_clone(value: Any, label: str) -> Any:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return json.loads(encoded)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise Text2GameExportError(f"{label} must be finite JSON data") from exc


def export_text2game_to_vibe(
    request: Text2GameExportRequest,
) -> Text2GameExportReceipt:
    """Create one exact Vibe idea workspace without publishing or queue writes."""

    normalized = _validate_request(request)
    source = _validate_source(normalized)
    idea = _vibe_idea(normalized, source.components)

    workspace = _safe_workspace(normalized.vibe_workspace)
    if (
        source.root == workspace
        or source.root in workspace.parents
        or workspace in source.root.parents
    ):
        raise Text2GameExportError(
            "text2game source and Vibe workspace must be disjoint directories"
        )
    queue_path = workspace / "board-game" / "QUEUE.json"
    queue_before = _sha256_file(queue_path)
    ideas_dir = workspace / "board-game" / "ideas"
    destination = ideas_dir / normalized.production_slug

    temporary = Path(
        tempfile.mkdtemp(
            prefix=f".{normalized.production_slug}.alice-export-",
            dir=ideas_dir,
        )
    )
    try:
        receipt = _build_export(temporary, normalized, source, idea)
        source_after = _snapshot_source(source.root)
        if source_after.sha256 != source.snapshot.sha256:
            raise Text2GameExportError(
                "text2game source changed while the export was being assembled"
            )
        if _sha256_file(queue_path) != queue_before:
            raise Text2GameExportError(
                "Vibe QUEUE.json changed during export; retry from a stable queue state"
            )

        if destination.exists() or destination.is_symlink():
            if destination.is_symlink() or not destination.is_dir():
                raise Text2GameExportConflict(
                    f"Vibe destination is not a regular directory: {destination}"
                )
            if _snapshot_destination(destination) != _snapshot_destination(temporary):
                raise Text2GameExportConflict(
                    f"Vibe destination {destination} contains a different export"
                )
            shutil.rmtree(temporary)
            temporary = Path()
            return _receipt_from_document(destination, receipt)

        try:
            os.rename(temporary, destination)
        except FileExistsError as exc:
            raise Text2GameExportConflict(
                f"Vibe destination appeared concurrently: {destination}"
            ) from exc
        temporary = Path()
        if _sha256_file(queue_path) != queue_before:
            raise Text2GameExportError(
                "Vibe QUEUE.json changed while finalizing export; no queue write was made"
            )
        return _receipt_from_document(destination, receipt)
    finally:
        if temporary != Path() and temporary.exists():
            shutil.rmtree(temporary)


def _validate_request(request: Text2GameExportRequest) -> Text2GameExportRequest:
    if not isinstance(request, Text2GameExportRequest):
        raise Text2GameExportError("request must be Text2GameExportRequest")
    slug = _trimmed(request.production_slug, "production_slug")
    if _SLUG.fullmatch(slug) is None:
        raise Text2GameExportError(
            "production_slug must be lowercase words separated by single hyphens"
        )
    candidate_id = _trimmed(request.candidate_id, "candidate_id")
    if (
        isinstance(request.candidate_version, bool)
        or not isinstance(request.candidate_version, int)
        or request.candidate_version < 1
    ):
        raise Text2GameExportError("candidate_version must be a positive integer")
    candidate_hash = _digest(
        request.candidate_content_sha256, "candidate_content_sha256"
    )
    rules_hash = _digest(request.accepted_rules_sha256, "accepted_rules_sha256")
    repo_url = _repository_url(request.source_repo_url)
    commit = _trimmed(request.source_repo_commit, "source_repo_commit")
    if _COMMIT.fullmatch(commit) is None:
        raise Text2GameExportError(
            "source_repo_commit must be a full lowercase 40-hex Git commit"
        )

    if not isinstance(request.accepted_rules, Mapping):
        raise Text2GameExportError("accepted_rules must be a structured object")
    missing_rules = [key for key in _RULE_FIELDS if key not in request.accepted_rules]
    if missing_rules:
        raise Text2GameExportError(
            "accepted_rules is missing canonical fields: " + ", ".join(missing_rules)
        )
    rule_document = _canonical_clone(
        {key: request.accepted_rules[key] for key in _RULE_FIELDS},
        "accepted_rules",
    )
    if canonical_sha256(rule_document) != rules_hash:
        raise Text2GameExportError(
            "accepted_rules_sha256 does not match the complete Alice rule document"
        )
    markdown = rule_document["rules_markdown"]
    if not isinstance(markdown, str) or not markdown.strip():
        raise Text2GameExportError("accepted_rules.rules_markdown must be non-empty")
    structured = _structured_rules(rule_document)
    for section in ("setup", "turn", "end"):
        for entry in structured[section]:
            if entry["text"] not in markdown:
                raise Text2GameExportError(
                    f"accepted_rules.{section} text is absent from rules_markdown"
                )
    win_entries = (
        structured["win"]
        if isinstance(structured["win"], list)
        else [structured["win"]]
    )
    for entry in win_entries:
        if entry["text"] not in markdown:
            raise Text2GameExportError(
                "accepted_rules.scoring text is absent from rules_markdown"
            )
    for entry in _rule_entries(rule_document["ties"], "accepted_rules.ties"):
        if entry["text"] not in markdown:
            raise Text2GameExportError(
                "accepted_rules.ties text is absent from rules_markdown"
            )

    if not isinstance(request.accepted_game, Mapping):
        raise Text2GameExportError("accepted_game must be a structured object")
    accepted_game = _canonical_clone(dict(request.accepted_game), "accepted_game")
    _validate_game(accepted_game)

    cad = _hash_map(request.cad_artifact_hashes, "cad_artifact_hashes")
    dfm = _hash_map(request.dfm_artifact_hashes, "dfm_artifact_hashes")
    if cad != dfm:
        raise Text2GameExportError(
            "physical.dfm did not accept the exact physical.cad source artifact map"
        )

    return Text2GameExportRequest(
        source_dir=Path(request.source_dir),
        vibe_workspace=Path(request.vibe_workspace),
        production_slug=slug,
        candidate_id=candidate_id,
        candidate_version=request.candidate_version,
        candidate_content_sha256=candidate_hash,
        accepted_game=accepted_game,
        accepted_rules=rule_document,
        accepted_rules_sha256=rules_hash,
        cad_artifact_hashes=cad,
        dfm_artifact_hashes=dfm,
        source_repo_url=repo_url,
        source_repo_commit=commit,
    )


def _validate_source(request: Text2GameExportRequest) -> _ValidatedSource:
    configured = Path(request.source_dir).expanduser()
    if configured.is_symlink():
        raise Text2GameExportError("text2game source directory must not be a symlink")
    root = configured.resolve()
    if not root.is_dir():
        raise Text2GameExportError(f"text2game source directory does not exist: {root}")
    snapshot = _snapshot_source(root)

    evidence = {name: _required_source_file(root, name) for name in _EVIDENCE_FILES}
    _validate_png(evidence["renders/assembled.png"], "renders/assembled.png")
    if evidence["gdd.md"].read_bytes() != request.accepted_rules[
        "rules_markdown"
    ].encode("utf-8"):
        raise Text2GameExportError(
            "text2game gdd.md is not byte-for-byte the accepted Alice rules_markdown"
        )

    components_raw = _json_object_or_array(evidence["components.json"], "components")
    if isinstance(components_raw, Mapping):
        components_raw = components_raw.get("components")
    components = _source_components(components_raw)
    _validate_part_colors(evidence["part_colors.json"], components)

    phase1 = _json_mapping(evidence["phase1.json"], "phase1.json")
    phase2 = _json_mapping(evidence["phase2.json"], "phase2.json")
    phase3 = _json_mapping(evidence["phase3.json"], "phase3.json")
    gate = _json_mapping(evidence["gate.json"], "gate.json")
    slice_report = _json_mapping(evidence["slice_report.json"], "slice_report.json")
    _validate_phase1(root, phase1)
    _validate_phase2(phase2, {str(component["id"]) for component in components})

    part_meshes = tuple(
        _relative(root, path)
        for path in sorted((root / "fe_parts").glob("*.stl"))
        if path.is_file() and not path.is_symlink()
    )
    if not part_meshes:
        raise Text2GameExportError("text2game source has no fe_parts/*.stl meshes")
    expected_part_ids = {component["id"] for component in components}
    actual_part_ids = {PurePosixPath(path).stem for path in part_meshes}
    if actual_part_ids != expected_part_ids:
        raise Text2GameExportError(
            "fe_parts STL identities do not exactly match components.json"
        )

    assembled = _required_source_file(root, "assembled.stl")
    _validate_ascii_or_binary_stl(assembled, "assembled.stl")
    for mesh in part_meshes:
        _validate_ascii_or_binary_stl(_contained_file(root, mesh), mesh)

    steps = sorted(
        path
        for pattern in ("*.step", "*.stp")
        for path in root.glob(pattern)
        if path.is_file() and not path.is_symlink()
    )
    if len(steps) != 1:
        raise Text2GameExportError(
            "text2game source must contain exactly one unambiguous root STEP assembly"
        )
    assembly_step = _relative(root, steps[0])
    if steps[0].stat().st_size <= 0:
        raise Text2GameExportError("assembled STEP file must not be empty")
    with steps[0].open("rb") as handle:
        step_head = handle.read(32)
        handle.seek(max(0, steps[0].stat().st_size - 64))
        step_tail = handle.read(64)
    if b"ISO-10303-21" not in step_head or b"END-ISO-10303-21" not in step_tail:
        raise Text2GameExportError("assembled STEP file lacks an ISO-10303-21 envelope")

    _validate_cad_sources(root, components)
    gcode_files = _validate_gate_and_slice(
        root, components, part_meshes, gate, slice_report, phase3
    )

    accepted = dict(request.cad_artifact_hashes)
    hero = root / "renders" / "hero.png"
    required_accepted = {
        *_EVIDENCE_FILES,
        "assembled.stl",
        assembly_step,
        *part_meshes,
        *gcode_files,
        *(
            _relative(root, path)
            for path in sorted(root.rglob("*.py"))
            if path.is_file() and not path.is_symlink()
        ),
        *({"renders/hero.png"} if hero.exists() else set()),
    }
    missing = sorted(required_accepted - set(accepted))
    if missing:
        raise Text2GameExportError(
            "accepted CAD/DFM hash maps omit required source files: "
            + ", ".join(missing)
        )
    for relative, expected in accepted.items():
        path = _contained_file(root, relative)
        if path.stat().st_size <= 0 and path.suffix != ".py":
            raise Text2GameExportError(f"accepted source artifact is empty: {relative}")
        if _sha256_file(path) != expected:
            raise Text2GameExportError(
                f"accepted source artifact hash mismatch: {relative}"
            )

    evidence_hashes = {
        name: _sha256_file(path) for name, path in sorted(evidence.items())
    }
    return _ValidatedSource(
        root=root,
        snapshot=snapshot,
        components=components,
        phase1=phase1,
        phase2=phase2,
        phase3=phase3,
        gate=gate,
        slice_report=slice_report,
        assembly_step=assembly_step,
        part_meshes=part_meshes,
        gcode_files=gcode_files,
        evidence_hashes=evidence_hashes,
        accepted_source_hashes=accepted,
    )


def _build_export(
    root: Path,
    request: Text2GameExportRequest,
    source: _ValidatedSource,
    idea: Mapping[str, Any],
) -> Mapping[str, Any]:
    project = root / "project"
    project.mkdir()
    idea_bytes = _canonical_document(idea)
    (root / "idea.json").write_bytes(idea_bytes)

    source_to_project: dict[str, str] = {}
    validated_not_exported: list[str] = []
    destination_claims: set[str] = set()
    for relative in sorted(source.accepted_source_hashes):
        destination = _source_destination(
            relative, request.production_slug, source.assembly_step
        )
        if destination is None:
            validated_not_exported.append(relative)
            continue
        if destination in destination_claims:
            raise Text2GameExportError(
                f"two text2game source files map to {destination!r}"
            )
        destination_claims.add(destination)
        src = _contained_file(source.root, relative)
        dst = project / PurePosixPath(destination)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        source_to_project[relative] = destination

    (project / "main.py").write_text(
        _step_bridge_main(request.production_slug), encoding="utf-8"
    )
    (project / "params.py").write_text(
        _step_bridge_params(request, source), encoding="utf-8"
    )
    idea_copy = project / "_text2game" / "vibe-idea.json"
    idea_copy.parent.mkdir(parents=True, exist_ok=True)
    idea_copy.write_bytes(idea_bytes)

    rules_bytes = request.accepted_rules["rules_markdown"].encode("utf-8")
    (project / "RULES.md").write_bytes(rules_bytes)
    bill = [
        {"name": component["id"], "qty": component["qty"]}
        for component in source.components
    ]
    _write_json(project / "bill.json", bill)
    _write_json(project / "cad_project.json", _cad_project(request, source))
    _write_json(project / "gate.json", _vibe_gate(source, bill))
    (project / "spec.md").write_text(
        _spec_markdown(request, source, idea), encoding="utf-8"
    )

    review = project / f"{request.production_slug}_review"
    review.mkdir()
    assembled_render = _contained_file(source.root, "renders/assembled.png")
    hero = source.root / "renders" / "hero.png"
    if hero.exists():
        if hero.is_symlink() or not hero.is_file():
            raise Text2GameExportError("renders/hero.png must be a regular file")
        _validate_png(hero, "renders/hero.png")
        shutil.copyfile(hero, review / "_assembled.png")
        shutil.copyfile(assembled_render, review / "_qa.png")
    else:
        shutil.copyfile(assembled_render, review / "_assembled.png")

    provenance = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "kind": "alice.text2game-to-vibe",
        "candidate_id": request.candidate_id,
        "candidate_version": request.candidate_version,
        "candidate_content_sha256": request.candidate_content_sha256,
        "production_slug": request.production_slug,
        "accepted_game_sha256": canonical_sha256(request.accepted_game),
        "vibe_idea_sha256": hashlib.sha256(idea_bytes).hexdigest(),
        "rules_sha256": request.accepted_rules_sha256,
        "rules_file_sha256": hashlib.sha256(rules_bytes).hexdigest(),
        "source": {
            "repo_url": request.source_repo_url,
            "repo_commit": request.source_repo_commit,
            "snapshot_sha256": source.snapshot.sha256,
            "file_count": len(source.snapshot.files),
            "byte_count": source.snapshot.total_bytes,
            "evidence_hashes": dict(sorted(source.evidence_hashes.items())),
            "accepted_artifact_hashes": dict(
                sorted(source.accepted_source_hashes.items())
            ),
            "source_to_project": dict(sorted(source_to_project.items())),
            "validated_not_exported": validated_not_exported,
        },
        "gates": {
            "phase1_exit": source.phase1["exit"],
            "priorart": source.phase1["priorart"],
            "phase2_coherence": source.phase2["coherence"],
            "gate_pass": source.gate["pass"],
            "fit_ok": source.phase3["fit_ok"],
            "slice_failed": 0,
        },
        "effects": {
            "publisher_invoked": False,
            "queue_mutated": False,
            "queue_state_claimed": None,
            "public_status_claimed": None,
            "publisher_exact_rules_passthrough_required": True,
            "publisher_rules_archive_contract": REQUIRED_RULES_ARCHIVE_CONTRACT,
            "publisher_alice_draft_handoff_contract": (
                REQUIRED_ALICE_DRAFT_HANDOFF_CONTRACT
            ),
        },
    }
    _write_json(project / "alice-text2game-provenance.json", provenance)

    snapshot = snapshot_project(project)
    artifacts = {
        str(item["path"]): str(item["sha256"]) for item in snapshot.files
    }
    receipt = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "kind": "alice.text2game-export-receipt",
        "candidate_id": request.candidate_id,
        "candidate_version": request.candidate_version,
        "candidate_content_sha256": request.candidate_content_sha256,
        "production_slug": request.production_slug,
        "rules_sha256": request.accepted_rules_sha256,
        "rules_file_sha256": hashlib.sha256(rules_bytes).hexdigest(),
        "idea_sha256": hashlib.sha256(idea_bytes).hexdigest(),
        "project_sha256": snapshot.project_sha256,
        "artifact_hashes": dict(sorted(artifacts.items())),
        "source_artifact_hashes": dict(sorted(source.accepted_source_hashes.items())),
        "source_artifact_hashes_sha256": canonical_sha256(
            source.accepted_source_hashes
        ),
        "source_snapshot_sha256": source.snapshot.sha256,
        "source_repo_url": request.source_repo_url,
        "source_repo_commit": request.source_repo_commit,
        "handoff": {
            "vibe_queue_transition_required": False,
            "vibe_queue_transition_performed": False,
            "publisher_invoked": False,
            "publisher_exact_rules_passthrough_required": True,
            "publisher_rules_archive_contract": REQUIRED_RULES_ARCHIVE_CONTRACT,
            "publisher_alice_draft_handoff_contract": (
                REQUIRED_ALICE_DRAFT_HANDOFF_CONTRACT
            ),
        },
    }
    _write_json(root / ".alice-text2game-export.json", receipt)
    return receipt


def _receipt_from_document(
    destination: Path, document: Mapping[str, Any]
) -> Text2GameExportReceipt:
    encoded = _canonical_document(document)
    return Text2GameExportReceipt(
        destination=destination,
        candidate_id=str(document["candidate_id"]),
        candidate_version=int(document["candidate_version"]),
        candidate_content_sha256=str(document["candidate_content_sha256"]),
        production_slug=str(document["production_slug"]),
        rules_sha256=str(document["rules_sha256"]),
        rules_file_sha256=str(document["rules_file_sha256"]),
        idea_sha256=str(document["idea_sha256"]),
        project_sha256=str(document["project_sha256"]),
        artifact_hashes=MappingProxyType(dict(document["artifact_hashes"])),
        source_artifact_hashes=MappingProxyType(
            dict(document["source_artifact_hashes"])
        ),
        source_artifact_hashes_sha256=str(
            document["source_artifact_hashes_sha256"]
        ),
        source_snapshot_sha256=str(document["source_snapshot_sha256"]),
        source_repo_url=str(document["source_repo_url"]),
        source_repo_commit=str(document["source_repo_commit"]),
        export_receipt_sha256=hashlib.sha256(encoded).hexdigest(),
    )


def _vibe_idea(
    request: Text2GameExportRequest,
    source_components: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    game = request.accepted_game
    accepted_components = _accepted_components(game["components"])
    source_identity = [(str(c["id"]), int(c["qty"])) for c in source_components]
    accepted_identity = [(str(c["name"]), int(c["qty"])) for c in accepted_components]
    if accepted_identity != source_identity:
        raise Text2GameExportError(
            "accepted_game component ids/quantities do not exactly match components.json"
        )
    rules = _structured_rules(request.accepted_rules)
    component_ids = {str(component["name"]) for component in accepted_components}
    all_entries = [*rules["setup"], *rules["turn"], *rules["end"]]
    all_entries.extend(
        rules["win"] if isinstance(rules["win"], list) else [rules["win"]]
    )
    all_entries.extend(
        _rule_entries(
            request.accepted_rules["legal_actions"],
            "accepted_rules.legal_actions",
        )
    )
    all_entries.extend(
        _rule_entries(request.accepted_rules["ties"], "accepted_rules.ties")
    )
    unknown_uses = sorted(
        {
            component_id
            for entry in all_entries
            for component_id in entry.get("uses", [])
            if component_id not in component_ids
        }
    )
    if unknown_uses:
        raise Text2GameExportError(
            "accepted rules refer to unknown component ids: " + ", ".join(unknown_uses)
        )
    result = {
        "slug": request.production_slug,
        "title": _trimmed(game["title"], "accepted_game.title"),
        "concept": " ".join(str(game["concept"]).split()),
        "players": {
            "min": int(game["players"]["min"]),
            "max": int(game["players"]["max"]),
        },
        "playtime_min": int(game["playtime_min"]),
        "components": accepted_components,
        "rules": {
            "setup": rules["setup"],
            "turn": rules["turn"],
            "end": rules["end"],
            "win": rules["win"],
        },
    }
    _validate_vibe_page_inputs(result)
    return result


def _structured_rules(value: Mapping[str, Any]) -> dict[str, Any]:
    setup = _rule_entries(value.get("setup"), "accepted_rules.setup")
    turn = _rule_entries(value.get("turn"), "accepted_rules.turn")
    legal = _rule_entries(value.get("legal_actions"), "accepted_rules.legal_actions")
    ending = _rule_entries(value.get("end"), "accepted_rules.end")
    scoring = _rule_entries(value.get("scoring"), "accepted_rules.scoring")
    _rule_entries(value.get("ties"), "accepted_rules.ties")
    turn_texts = {entry["text"] for entry in turn}
    missing_actions = [entry["text"] for entry in legal if entry["text"] not in turn_texts]
    if missing_actions:
        raise Text2GameExportError(
            "accepted_rules.turn must contain every legal_actions rule verbatim"
        )
    win: Any = scoring[0] if len(scoring) == 1 else scoring
    return {"setup": setup, "turn": turn, "end": ending, "win": win}


def _validate_vibe_page_inputs(idea: Mapping[str, Any]) -> None:
    """Mirror the existing publisher's hard copy windows before any effect.

    The Shop Door backend refuses rich-page bodies outside 180..400 characters.
    Vibe's publisher deliberately drops undersized chunks, so a seemingly
    complete idea can otherwise import without ``use_case`` or story blocks
    and fail Alice's authenticated postflight only after the write.
    """

    if not _vibe_split_prose(str(idea["concept"])):
        raise Text2GameExportError(
            "accepted_game.concept cannot produce Vibe's 180..400 character use_case"
        )
    rules = idea["rules"]
    section_texts: list[str] = []
    for key in ("setup", "turn", "end", "win"):
        raw = rules[key]
        entries = raw if isinstance(raw, list) else [raw]
        section_texts.append(
            " ".join(str(entry["text"]) for entry in entries if isinstance(entry, Mapping))
        )
    if not any(_vibe_split_prose(text) for text in section_texts):
        raise Text2GameExportError(
            "accepted rules cannot produce any Vibe story block in the 180..400 character window"
        )


def _vibe_split_prose(text: str, lo: int = 180, hi: int = 400) -> list[str]:
    """The proven ``vibe-ideas`` sentence packer, kept deterministic and local."""

    sentences = [
        sentence.strip()
        for sentence in re.findall(r"[^.]+\.|[^.]+$", text)
        if sentence.strip()
    ]
    pieces: list[str] = []
    for sentence in sentences:
        while len(sentence) > hi:
            cut = sentence.rfind(" ", 0, hi)
            if cut <= 0:
                cut = hi
            pieces.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        pieces.append(sentence)
    total = sum(len(piece) + 1 for piece in pieces)
    wanted = max(1, -(-total // hi))
    target = total / wanted
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if current and (
            len(current) + 1 + len(piece) > hi
            or (len(current) >= target and len(chunks) < wanted - 1)
        ):
            chunks.append(current)
            current = piece
        else:
            current = f"{current} {piece}".strip()
    if current:
        chunks.append(current)
    while (
        len(chunks) > 1
        and len(chunks[-1]) < lo
        and len(chunks[-2]) + 1 + len(chunks[-1]) <= hi
    ):
        chunks[-2:] = [f"{chunks[-2]} {chunks[-1]}"]
    return [chunk for chunk in chunks if lo <= len(chunk) <= hi]


def _rule_entries(value: Any, label: str) -> list[dict[str, Any]]:
    rows = [value] if isinstance(value, Mapping) else value
    if not isinstance(rows, list) or not rows:
        raise Text2GameExportError(f"{label} must be a non-empty rule-entry array")
    result: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise Text2GameExportError(f"{label}[{index}] must be an object")
        text = _trimmed(row.get("text"), f"{label}[{index}].text")
        uses = row.get("uses", [])
        if not isinstance(uses, list) or not all(
            isinstance(item, str) and item and item == item.strip() for item in uses
        ):
            raise Text2GameExportError(
                f"{label}[{index}].uses must be an array of trimmed component ids"
            )
        result.append({"text": text, "uses": list(uses)})
    return result


def _validate_game(game: Mapping[str, Any]) -> None:
    for key in ("title", "concept", "players", "playtime_min", "components"):
        if key not in game:
            raise Text2GameExportError(f"accepted_game is missing {key}")
    title = _trimmed(game["title"], "accepted_game.title")
    if len(title) > 120:
        raise Text2GameExportError("accepted_game.title exceeds 120 characters")
    concept = _trimmed(game["concept"], "accepted_game.concept")
    collapsed = " ".join(concept.split())
    if not 180 <= len(collapsed) <= 5_000:
        raise Text2GameExportError(
            "accepted_game.concept must be 180..5000 characters for Vibe rich-page copy"
        )
    players = game["players"]
    if not isinstance(players, Mapping):
        raise Text2GameExportError("accepted_game.players must be an object")
    minimum = _positive_int(players.get("min"), "accepted_game.players.min")
    maximum = _positive_int(players.get("max"), "accepted_game.players.max")
    if minimum > maximum or maximum > 12:
        raise Text2GameExportError("accepted_game players must be an ordered range <= 12")
    minutes = _positive_int(game["playtime_min"], "accepted_game.playtime_min")
    if minutes > 1_440:
        raise Text2GameExportError("accepted_game.playtime_min exceeds one day")
    _accepted_components(game["components"])


def _accepted_components(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise Text2GameExportError("accepted_game.components must be a non-empty array")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise Text2GameExportError(
                f"accepted_game.components[{index}] must be an object"
            )
        name = _trimmed(row.get("name"), f"accepted_game.components[{index}].name")
        if _SEMANTIC_ID.fullmatch(name) is None or name in seen:
            raise Text2GameExportError(
                "accepted_game component names must be unique semantic ids"
            )
        seen.add(name)
        qty = _positive_int(row.get("qty", 1), f"component {name} qty")
        desc = _trimmed(row.get("desc"), f"component {name} desc")
        result.append({"name": name, "qty": qty, "desc": desc})
    return result


def _source_components(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list) or not value:
        raise Text2GameExportError("components.json must contain a non-empty component array")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise Text2GameExportError(f"components.json[{index}] must be an object")
        component_id = _trimmed(row.get("id"), f"components.json[{index}].id")
        if _SEMANTIC_ID.fullmatch(component_id) is None or component_id in seen:
            raise Text2GameExportError("components.json ids must be unique semantic ids")
        seen.add(component_id)
        qty = _positive_int(row.get("qty"), f"components.json {component_id} qty")
        result.append({"id": component_id, "qty": qty})
    return tuple(result)


def _validate_part_colors(
    path: Path, components: Sequence[Mapping[str, Any]]
) -> None:
    colors = _json_mapping(path, "part_colors.json")
    expected = {str(component["id"]) for component in components}
    if set(colors) != expected:
        raise Text2GameExportError(
            "part_colors.json must assign exactly one color to every component"
        )
    for component_id, color in colors.items():
        if not isinstance(color, str) or re.fullmatch(r"#[0-9A-Fa-f]{6}", color) is None:
            raise Text2GameExportError(
                f"part_colors.json color for {component_id!r} must be #RRGGBB"
            )


def _validate_phase1(root: Path, phase1: Mapping[str, Any]) -> None:
    if phase1.get("exit") != "clean" or phase1.get("priorart") != "clear":
        raise Text2GameExportError("phase1.json must exit clean with clear prior art")
    for key in ("consistency_high", "critic_high"):
        value = phase1.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value != 0:
            raise Text2GameExportError(f"phase1.json {key} must be integer zero")
    if phase1.get("referee_clean") is not True:
        raise Text2GameExportError("phase1.json referee_clean must be true")
    if phase1.get("referee_missing") is not False:
        raise Text2GameExportError("phase1.json referee_missing must be false")
    if "teach_below_floor" in phase1:
        raise Text2GameExportError("phase1.json retains a teach-below-floor finding")
    priorart = _json_mapping(root / "priorart.json", "priorart.json")
    if priorart.get("verdict") != "clear":
        raise Text2GameExportError("priorart.json must have verdict=clear")
    consistency = _json_object_or_array(root / "consistency.json", "consistency.json")
    if not isinstance(consistency, list):
        raise Text2GameExportError("consistency.json must be an issue array")
    if any(not isinstance(issue, Mapping) for issue in consistency):
        raise Text2GameExportError("consistency.json contains a malformed finding")
    if any(
        isinstance(issue, Mapping) and issue.get("severity") == "high"
        for issue in consistency
    ):
        raise Text2GameExportError("consistency.json contains unresolved high findings")
    critic = _json_object_or_array(root / "critic.json", "critic.json")
    if not isinstance(critic, list):
        raise Text2GameExportError("critic.json must be a finding array")
    if any(not isinstance(issue, Mapping) for issue in critic):
        raise Text2GameExportError("critic.json contains a malformed finding")
    if any(
        isinstance(issue, Mapping) and issue.get("severity") == "high"
        for issue in critic
    ):
        raise Text2GameExportError("critic.json contains unresolved high findings")
    referee = (root / "referee.md").read_text(encoding="utf-8")
    if re.search(r"^\s*CLEAN\s*$", referee, re.MULTILINE) is None:
        raise Text2GameExportError("referee.md lacks an explicit standalone CLEAN verdict")


def _validate_phase2(
    phase2: Mapping[str, Any], expected_component_ids: set[str]
) -> None:
    if phase2.get("stopped_at") not in (None, ""):
        raise Text2GameExportError("phase2 stopped before completing every build group")
    groups = phase2.get("groups")
    if not isinstance(groups, list) or not groups:
        raise Text2GameExportError("phase2.json must contain measured build groups")
    built_ids: list[str] = []
    for index, group in enumerate(groups):
        high = group.get("high") if isinstance(group, Mapping) else None
        if (
            not isinstance(group, Mapping)
            or isinstance(high, bool)
            or not isinstance(high, int)
            or high != 0
        ):
            raise Text2GameExportError(f"phase2 group {index} has unresolved high findings")
        issues = group.get("issues", [])
        if (
            not isinstance(issues, list)
            or any(not isinstance(issue, Mapping) for issue in issues)
            or any(issue.get("severity") == "high" for issue in issues)
        ):
            raise Text2GameExportError(f"phase2 group {index} has a high issue")
        group_parts = group.get("parts")
        if not isinstance(group_parts, list) or not all(
            isinstance(part, str) and _SEMANTIC_ID.fullmatch(part) is not None
            for part in group_parts
        ):
            raise Text2GameExportError(f"phase2 group {index} has malformed part ids")
        built_ids.extend(group_parts)
    if set(built_ids) != expected_component_ids or len(built_ids) != len(set(built_ids)):
        raise Text2GameExportError(
            "phase2 build groups do not cover every component exactly once"
        )
    if phase2.get("sculptural") != []:
        raise Text2GameExportError(
            "phase2 contains sculptural parts on text2game's unwired TRELLIS branch"
        )
    coherence = phase2.get("coherence")
    if not _finite_number(coherence) or float(coherence) < 6:
        raise Text2GameExportError("phase2 coherence must be a measured score >= 6")
    if phase2.get("coherence_fail") is not False:
        raise Text2GameExportError("phase2 coherence gate is failed or ambiguous")
    if phase2.get("staged") is not True:
        raise Text2GameExportError("phase2 lacks a completed staged assembly")


def _validate_gate_and_slice(
    root: Path,
    components: Sequence[Mapping[str, Any]],
    part_meshes: Sequence[str],
    gate: Mapping[str, Any],
    slice_report: Mapping[str, Any],
    phase3: Mapping[str, Any],
) -> tuple[str, ...]:
    if gate.get("pass") is not True or gate.get("fails") != []:
        raise Text2GameExportError("gate.json must contain an unambiguous pass")
    parts = gate.get("parts")
    if not isinstance(parts, Mapping) or not parts:
        raise Text2GameExportError("gate.json must contain per-part measurements")
    by_stem = {PurePosixPath(str(key)).stem: value for key, value in parts.items()}
    if len(by_stem) != len(parts):
        raise Text2GameExportError("gate.json contains ambiguous duplicate part stems")
    mesh_ids = {PurePosixPath(path).stem for path in part_meshes}
    if set(by_stem) != mesh_ids:
        raise Text2GameExportError("gate.json part identities do not match fe_parts")
    for part_id, facts in by_stem.items():
        if not isinstance(facts, Mapping):
            raise Text2GameExportError(f"gate facts for {part_id} must be an object")
        bodies = facts.get("bodies")
        if (
            facts.get("watertight") is not True
            or isinstance(bodies, bool)
            or not isinstance(bodies, int)
            or bodies != 1
        ):
            raise Text2GameExportError(f"gate facts for {part_id} are not one watertight body")
        bbox = facts.get("bbox_mm")
        if not isinstance(bbox, list) or len(bbox) != 3 or not all(
            _finite_number(value) and float(value) > 0 for value in bbox
        ):
            raise Text2GameExportError(f"gate facts for {part_id} lack a positive bbox")
        if not _finite_number(facts.get("volume_mm3")) or float(
            facts["volume_mm3"]
        ) <= 0:
            raise Text2GameExportError(f"gate facts for {part_id} lack positive volume")
        _trimmed(facts.get("print_orientation"), f"gate {part_id} orientation")
        overhang = facts.get("overhang_pct")
        bridge = facts.get("bridge_span_mm")
        if not _finite_number(overhang) or not 0 <= float(overhang) <= 100:
            raise Text2GameExportError(f"gate facts for {part_id} have bad overhang")
        if not _finite_number(bridge) or float(bridge) < 0:
            raise Text2GameExportError(f"gate facts for {part_id} have bad bridge span")

    failed = slice_report.get("failed")
    rows = slice_report.get("parts")
    if failed != [] or not isinstance(rows, list) or not rows:
        raise Text2GameExportError("slice_report.json must have rows and zero failed parts")
    expected_qty = {str(c["id"]): int(c["qty"]) for c in components}
    observed: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise Text2GameExportError(f"slice row {index} must be an object")
        part = _trimmed(row.get("part"), f"slice row {index} part")
        if part in observed:
            raise Text2GameExportError(f"slice report repeats part {part}")
        if row.get("qty") != expected_qty.get(part):
            raise Text2GameExportError(f"slice quantity for {part} does not match components")
        for key in ("grams_each", "seconds_each", "grams_total", "seconds_total"):
            if not _finite_number(row.get(key)) or float(row[key]) <= 0:
                raise Text2GameExportError(f"slice row {part} lacks positive {key}")
        observed[part] = row
    if set(observed) != mesh_ids:
        raise Text2GameExportError("slice rows do not exactly cover fe_parts")
    total_grams = sum(float(row["grams_total"]) for row in observed.values())
    total_seconds = sum(float(row["seconds_total"]) for row in observed.values())
    if not _close(slice_report.get("total_grams"), total_grams, 0.11):
        raise Text2GameExportError("slice_report total_grams does not match its part rows")
    if not _close(slice_report.get("total_seconds"), total_seconds, 1.0):
        raise Text2GameExportError("slice_report total_seconds does not match its part rows")
    for key in ("profile", "slicer", "total_print_time"):
        _trimmed(slice_report.get(key), f"slice_report.{key}")

    if phase3.get("gate") != gate:
        raise Text2GameExportError("phase3.json does not bind the current gate.json")
    if phase3.get("slice") != slice_report:
        raise Text2GameExportError("phase3.json does not bind the current slice_report.json")
    if phase3.get("fit_ok") is not True:
        raise Text2GameExportError("phase3 fit check is failed or ambiguous")
    if phase3.get("unplaceable") != []:
        raise Text2GameExportError("phase3 contains unplaceable components")
    plates = phase3.get("plates")
    if isinstance(plates, bool) or not isinstance(plates, int) or plates < 1:
        raise Text2GameExportError("phase3 lacks printable plates")
    open_questions = phase3.get("open_questions")
    if (
        isinstance(open_questions, bool)
        or not isinstance(open_questions, int)
        or open_questions != 0
    ):
        raise Text2GameExportError("phase3 retains unresolved open questions")
    if phase3.get("coherence_fail") not in (None, False):
        raise Text2GameExportError("phase3 carries a failed coherence gate")

    gcode_files: list[str] = []
    for part_id in sorted(mesh_ids):
        relative = f"gcode/{part_id}.gcode"
        path = _required_source_file(root, relative)
        if path.stat().st_size <= 0:
            raise Text2GameExportError(f"gcode is empty: {relative}")
        gcode_files.append(relative)
    extras = sorted((root / "gcode").glob("*.gcode"))
    if {_relative(root, path) for path in extras} != set(gcode_files):
        raise Text2GameExportError("gcode directory does not exactly match sliced parts")
    return tuple(gcode_files)


def _validate_cad_sources(
    root: Path, components: Sequence[Mapping[str, Any]]
) -> None:
    """Require text2game's real per-part sources, not a made-up root layout."""

    for component in components:
        _required_source_file(root, f"parts/{component['id']}.py")


def _cad_project(
    request: Text2GameExportRequest, source: _ValidatedSource
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "engine": "cadquery",
        "entrypoint": {"path": "main.py", "callable": "gen_step"},
        "parameters": "params.py",
        "specification": "spec.md",
        "model": {
            "kind": "assembly" if len(source.components) > 1 else "single-part",
            "primaryPose": "assembled",
            "parts": [
                {
                    "id": component["id"],
                    "source": f"_text2game/source/parts/{component['id']}.py",
                }
                for component in source.components
            ],
            **({"assembly": "main.py"} if len(source.components) > 1 else {}),
        },
        "artifactStem": request.production_slug,
    }


def _vibe_gate(
    source: _ValidatedSource, bill: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    allowed_part_fields = (
        "watertight",
        "bodies",
        "volume_mm3",
        "bbox_mm",
        "print_orientation",
        "overhang_pct",
        "bridge_span_mm",
    )
    parts = {
        PurePosixPath(str(name)).stem: {
            key: facts[key]
            for key in allowed_part_fields
            if isinstance(facts, Mapping) and key in facts
        }
        for name, facts in sorted(source.gate["parts"].items())
    }
    return {
        "pass": True,
        "fails": [],
        "part_count": sum(int(row["qty"]) for row in bill),
        "parts": parts,
        "bill": list(bill),
        "slice": {
            "parts": len(source.slice_report["parts"]),
            "total_grams": source.slice_report["total_grams"],
            "total_seconds": source.slice_report["total_seconds"],
            "total_print_time": source.slice_report["total_print_time"],
            "profile": source.slice_report["profile"],
            "slicer": source.slice_report["slicer"],
            "failed": [],
        },
        "source_sha256": source.evidence_hashes["gate.json"],
    }


def _spec_markdown(
    request: Text2GameExportRequest,
    source: _ValidatedSource,
    idea: Mapping[str, Any],
) -> str:
    lines = [
        f"# {idea['title']}",
        "",
        "This Vibe workspace is a deterministic export of an accepted text2game run.",
        "The complete accepted rules are in `RULES.md`; `gdd.md` was not reparsed.",
        "",
        "## Lineage",
        "",
        f"- Candidate: `{request.candidate_id}` version {request.candidate_version}",
        f"- Rules SHA-256: `{request.accepted_rules_sha256}`",
        f"- text2game commit: `{request.source_repo_commit}`",
        f"- Source snapshot: `{source.snapshot.sha256}`",
        "",
        "## Components",
        "",
    ]
    lines.extend(
        f"- `{component['id']}` ×{component['qty']}"
        for component in source.components
    )
    lines.extend(
        [
            "",
            "## Measured print facts",
            "",
            f"- {source.slice_report['total_grams']} g total",
            f"- {source.slice_report['total_print_time']} total print time",
            f"- {len(source.slice_report['parts'])} distinct sliced parts",
            "- Zero slice failures",
            "",
            "The exporter did not publish this game and did not change Vibe's queue.",
        ]
    )
    return "\n".join(lines) + "\n"


def _source_destination(
    relative: str, slug: str, assembly_step: str
) -> str | None:
    path = PurePosixPath(relative)
    if relative == "assembled.stl":
        return f"{slug}.stl"
    if relative == assembly_step:
        return f"{slug}.step"
    if path.suffix == ".py":
        return f"_text2game/source/{relative}"
    if relative == "part_colors.json":
        return relative
    if path.parts and path.parts[0] in {"renders"}:
        return f"_text2game/{relative}"
    if path.name in _PROJECT_RESERVED_ROOTS or relative in _EVIDENCE_FILES:
        return f"_text2game/{relative}"
    if len(path.parts) == 2 and path.parts[0] == "fe_parts" and path.suffix == ".stl":
        return relative
    # G-code is printer/profile-specific and can exceed the Shop Door readback
    # cap. It is verified as slice evidence but deliberately not shipped in a
    # general STL/STEP product bundle. Unknown accepted diagnostics stay local
    # for the same least-publication reason; their hashes remain in provenance.
    return None


def _step_bridge_main(slug: str) -> str:
    """Canonical Vibe entrypoint over the exact accepted STEP assembly.

    text2game's current contract is ``parts/*.py`` plus a shared STEP and does
    not promise Vibe's root ``main.py`` API.  Importing the accepted B-rep is a
    deterministic compatibility bridge; the original editable sources remain
    byte-for-byte under ``_text2game/source``.
    """

    return (
        '"""Vibe compatibility entrypoint for an accepted text2game STEP."""\n\n'
        "from pathlib import Path\n\n"
        "import cadquery as cq\n\n\n"
        "def gen_step():\n"
        f"    return cq.importers.importStep(str(Path(__file__).with_name({slug!r} + '.step')))\n"
    )


def _step_bridge_params(
    request: Text2GameExportRequest, source: _ValidatedSource
) -> str:
    return (
        '"""Immutable lineage for the text2game STEP compatibility bridge."""\n\n'
        f"ARTIFACT_STEM = {request.production_slug!r}\n"
        f"SOURCE_SNAPSHOT_SHA256 = {source.snapshot.sha256!r}\n"
        f"RULES_SHA256 = {request.accepted_rules_sha256!r}\n"
    )


def _safe_workspace(value: Path) -> Path:
    configured = Path(value).expanduser()
    if configured.is_symlink():
        raise Text2GameExportError("Vibe workspace must not be a symlink")
    workspace = configured.resolve()
    board_game = workspace / "board-game"
    ideas = board_game / "ideas"
    operator = board_game / "tools" / "publish.py"
    queue = board_game / "QUEUE.json"
    for label, path, directory in (
        ("board-game", board_game, True),
        ("ideas", ideas, True),
        ("publish.py", operator, False),
        ("QUEUE.json", queue, False),
    ):
        if path.is_symlink() or (not path.is_dir() if directory else not path.is_file()):
            raise Text2GameExportError(
                f"Vibe workspace lacks regular {label} at {path}"
            )
    _json_mapping(queue, "Vibe QUEUE.json")
    return workspace


def _snapshot_source(root: Path) -> _SourceSnapshot:
    files: list[dict[str, Any]] = []
    total = 0
    for path in sorted(root.rglob("*")):
        relative = _relative(root, path)
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise Text2GameExportError(f"text2game source contains a symlink: {relative}")
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise Text2GameExportError(
                f"text2game source contains a non-regular file: {relative}"
            )
        size = path.stat().st_size
        total += size
        if len(files) >= _MAX_SOURCE_FILES or total > _MAX_SOURCE_BYTES:
            raise Text2GameExportError("text2game source exceeds safe export limits")
        files.append({"path": relative, "sha256": _sha256_file(path), "bytes": size})
    if not files:
        raise Text2GameExportError("text2game source directory is empty")
    return _SourceSnapshot(
        files=tuple(files),
        sha256=canonical_sha256(files),
        total_bytes=total,
    )


def _snapshot_destination(root: Path) -> tuple[tuple[str, str, int], ...]:
    rows: list[tuple[str, str, int]] = []
    for path in sorted(root.rglob("*")):
        relative = _relative(root, path)
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or (not stat.S_ISDIR(mode) and not stat.S_ISREG(mode)):
            raise Text2GameExportConflict(
                f"destination contains an unsafe filesystem entry: {relative}"
            )
        if stat.S_ISREG(mode):
            rows.append((relative, _sha256_file(path), path.stat().st_size))
    return tuple(rows)


def _repository_url(value: Any) -> str:
    raw = _trimmed(value, "source_repo_url")
    parsed = urllib.parse.urlsplit(raw)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.query
        or parsed.fragment
    ):
        raise Text2GameExportError(
            "source_repo_url must be a credential-free github.com HTTPS URL"
        )
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise Text2GameExportError("source_repo_url must name one GitHub repository")
    repo = parts[1][:-4] if parts[1].endswith(".git") else parts[1]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", parts[0]) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+", repo
    ):
        raise Text2GameExportError("source_repo_url has unsafe owner or repo text")
    return f"https://github.com/{parts[0]}/{repo}"


def _hash_map(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or not value:
        raise Text2GameExportError(f"{label} must be a non-empty source hash map")
    result: dict[str, str] = {}
    for raw_path, raw_digest in value.items():
        if not isinstance(raw_path, str):
            raise Text2GameExportError(f"{label} paths must be strings")
        path = _safe_relative(raw_path, f"{label} path")
        _reject_sensitive_source_path(path, label)
        result[path] = _digest(raw_digest, f"{label}[{path!r}]")
    return dict(sorted(result.items()))


def _contained_file(root: Path, relative: str) -> Path:
    safe = _safe_relative(relative, "source path")
    candidate = root / PurePosixPath(safe)
    if candidate.is_symlink():
        raise Text2GameExportError(f"source path is a symlink: {safe}")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise Text2GameExportError(f"source artifact is missing: {safe}") from exc
    if root not in resolved.parents or not resolved.is_file():
        raise Text2GameExportError(f"source path escapes the product directory: {safe}")
    if not stat.S_ISREG(resolved.stat().st_mode):
        raise Text2GameExportError(f"source path is not a regular file: {safe}")
    return resolved


def _required_source_file(root: Path, relative: str) -> Path:
    return _contained_file(root, relative)


def _safe_relative(value: str, label: str) -> str:
    if (
        not value
        or value != value.strip()
        or "\\" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise Text2GameExportError(f"{label} must be a normalized POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise Text2GameExportError(f"{label} is unsafe: {value!r}")
    normalized = path.as_posix()
    if normalized != value or normalized in {"", "."}:
        raise Text2GameExportError(f"{label} is not normalized: {value!r}")
    return normalized


def _reject_sensitive_source_path(value: str, label: str) -> None:
    path = PurePosixPath(value)
    names = {part.casefold() for part in path.parts}
    sensitive_names = {
        ".env",
        "auth.json",
        "credentials.json",
        "gcs-sa.json",
        "id_rsa",
        "id_ed25519",
        "secrets.json",
        "token.json",
    }
    if names & sensitive_names or path.suffix.casefold() in {
        ".key",
        ".p12",
        ".pem",
        ".pfx",
    }:
        raise Text2GameExportError(f"{label} contains a credential-like source path")


def _relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise Text2GameExportError(f"path escapes source root: {path}") from exc


def _json_mapping(path: Path, label: str) -> Mapping[str, Any]:
    value = _json_object_or_array(path, label)
    if not isinstance(value, Mapping):
        raise Text2GameExportError(f"{label} must contain a JSON object")
    return value


def _json_object_or_array(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Text2GameExportError(f"could not read valid {label}") from exc


def _validate_ascii_or_binary_stl(path: Path, label: str) -> None:
    size = path.stat().st_size
    if size < 15:
        raise Text2GameExportError(f"printable STL is too small: {label}")
    with path.open("rb") as handle:
        head = handle.read(84)
        handle.seek(max(0, size - 256))
        tail = handle.read(256)
    ascii_stl = (
        head.lstrip().startswith(b"solid")
        and b"facet normal" in head + _read_prefix(path, 1 << 20)
        and b"endsolid" in tail
    )
    triangles = int.from_bytes(head[80:84], "little") if len(head) == 84 else 0
    binary_stl = triangles > 0 and size == 84 + triangles * 50
    if not ascii_stl and not binary_stl:
        raise Text2GameExportError(f"printable STL has no valid ASCII/binary envelope: {label}")


def _validate_png(path: Path, label: str) -> None:
    with path.open("rb") as handle:
        header = handle.read(32)
        handle.seek(max(0, path.stat().st_size - 32))
        tail = handle.read(32)
    if (
        path.stat().st_size <= 32
        or header[:8] != b"\x89PNG\r\n\x1a\n"
        or header[12:16] != b"IHDR"
        or b"IEND" not in tail
    ):
        raise Text2GameExportError(f"{label} is not a PNG file")


def _read_prefix(path: Path, maximum_bytes: int) -> bytes:
    with path.open("rb") as handle:
        return handle.read(maximum_bytes)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(_canonical_document(value))


def _canonical_document(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise Text2GameExportError("export document is not finite JSON") from exc


def _trimmed(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise Text2GameExportError(f"{label} must be a non-empty trimmed string")
    return value


def _digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise Text2GameExportError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise Text2GameExportError(f"{label} must be a positive integer")
    return value


def _finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _close(value: Any, expected: float, tolerance: float) -> bool:
    return _finite_number(value) and abs(float(value) - expected) <= tolerance


__all__ = [
    "EXPORT_SCHEMA_VERSION",
    "REQUIRED_ALICE_DRAFT_HANDOFF_CONTRACT",
    "REQUIRED_RULES_ARCHIVE_CONTRACT",
    "TEXT2GAME_REPOSITORY",
    "Text2GameExportConflict",
    "Text2GameExportError",
    "Text2GameExportReceipt",
    "Text2GameExportRequest",
    "canonical_sha256",
    "export_text2game_to_vibe",
]
