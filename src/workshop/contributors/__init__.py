"""Strict native Inventor bundles, Taste, and static contribution tooling."""

from workshop.contributors.contribution import (
    check_target,
    manifests_for_target,
    validate_contribution,
    validate_inventor_collection,
)
from workshop.contributors.manifest import (
    InventorManifest,
    discover_inventors,
    inventor_collection,
    load_manifest,
)
from workshop.contributors.extensions import (
    INVENTOR_EXTENSION_KIND,
    InventorExtension,
    InventorExtensionBundle,
    fingerprint_extension_skill,
    load_inventor_extension_bundles,
)
from workshop.contributors.scaffold import (
    create_inventor,
    prepare_inventor_collection,
)
from workshop.contributors.taste import (
    Taste,
    TasteHeader,
    load_taste,
    load_taste_header,
)

__all__ = [
    "INVENTOR_EXTENSION_KIND",
    "InventorExtension",
    "InventorExtensionBundle",
    "InventorManifest",
    "Taste",
    "TasteHeader",
    "check_target",
    "create_inventor",
    "discover_inventors",
    "fingerprint_extension_skill",
    "inventor_collection",
    "load_manifest",
    "load_inventor_extension_bundles",
    "load_taste",
    "load_taste_header",
    "manifests_for_target",
    "prepare_inventor_collection",
    "validate_contribution",
    "validate_inventor_collection",
]
