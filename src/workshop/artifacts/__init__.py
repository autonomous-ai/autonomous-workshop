"""Public contracts for manifests and immutable product Artifacts."""

from workshop.artifacts.core import (
    ArtifactEntry,
    ArtifactManifest,
    MAX_ENTRIES,
    MAX_EXPANDED_BYTES,
    MAX_FILE_BYTES,
    MAX_PACK_BYTES,
    assert_artifact_path_hygiene,
    assert_packable_content,
    artifact_manifest_from_mapping,
    build_artifact_manifest,
    build_pack,
)
from workshop.artifacts.pack import (
    Artifact,
    ArtifactPlan,
    bundle_artifact,
    inspect_artifact,
    inspect_artifact_details,
    load_artifact_payload,
    plan_artifact,
    seal_artifact,
    validate_artifact_payload,
)
from workshop.artifacts.schema_registry import discover_schemas, resolve_schemas_root

__all__ = [
    "Artifact",
    "ArtifactEntry",
    "ArtifactManifest",
    "ArtifactPlan",
    "MAX_ENTRIES",
    "MAX_EXPANDED_BYTES",
    "MAX_FILE_BYTES",
    "MAX_PACK_BYTES",
    "assert_artifact_path_hygiene",
    "assert_packable_content",
    "artifact_manifest_from_mapping",
    "build_artifact_manifest",
    "build_pack",
    "bundle_artifact",
    "discover_schemas",
    "inspect_artifact",
    "inspect_artifact_details",
    "load_artifact_payload",
    "plan_artifact",
    "resolve_schemas_root",
    "seal_artifact",
    "validate_artifact_payload",
]
