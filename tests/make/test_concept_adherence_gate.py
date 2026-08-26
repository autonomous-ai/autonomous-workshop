"""Failure-path tests for the Make-boundary concept-adherence checks."""

import hashlib
import json
import unittest
from dataclasses import asdict

from workshop.artifacts import ArtifactEntry, ArtifactManifest
from workshop.concept.native import ConceptTree
from workshop.errors import ContractError
from workshop.make.native_gate import (
    assert_concept_component_correspondence,
    assert_no_concept_pixels_in_product,
)


def _manifest(entries):
    entries = tuple(
        sorted(
            (*entries, ArtifactEntry(path="_baseline", bytes=1, sha256="b" * 64, executable=False)),
            key=lambda entry: entry.path,
        )
    )
    identity = json.dumps(
        [asdict(entry) for entry in entries],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return ArtifactManifest(
        schema_version=1,
        artifact_sha256=hashlib.sha256(identity).hexdigest(),
        entries=entries,
        total_bytes=sum(entry.bytes for entry in entries),
        created_at="content-addressed",
    )


def _tree(*, manifest_entries=()):
    return ConceptTree(
        root=object(),
        manifest=_manifest(manifest_entries),
        brief={"components": [{"key": "dome"}, {"key": "base"}]},
        research={},
        drawing_instructions={},
        descriptor={},
        derived_wish=object(),
    )


class ConceptComponentCorrespondenceTest(unittest.TestCase):
    def test_matching_components_are_accepted(self):
        tree = _tree()
        assert_concept_component_correspondence(
            tree, {"components": ["dome", "base"]}
        )

    def test_missing_a_brief_component_is_refused(self):
        tree = _tree()
        with self.assertRaisesRegex(ContractError, "missing components"):
            assert_concept_component_correspondence(tree, {"components": ["dome"]})

    def test_declaring_an_extra_component_is_refused(self):
        tree = _tree()
        with self.assertRaisesRegex(ContractError, "did not.*name"):
            assert_concept_component_correspondence(
                tree, {"components": ["dome", "base", "lid"]}
            )

    def test_repeated_component_key_is_refused(self):
        tree = _tree()
        with self.assertRaisesRegex(ContractError, "not repeat a key"):
            assert_concept_component_correspondence(
                tree, {"components": ["dome", "dome"]}
            )

    def test_non_list_components_field_is_refused(self):
        tree = _tree()
        with self.assertRaisesRegex(ContractError, "list of concept"):
            assert_concept_component_correspondence(tree, {"components": "dome"})


class ConceptPixelsInProductTest(unittest.TestCase):
    def test_no_shared_bytes_is_accepted(self):
        concept_tree = _tree(
            manifest_entries=[
                ArtifactEntry(path="images/front.png", bytes=4, sha256="c" * 64, executable=False),
            ]
        )
        product_manifest = _manifest(
            [ArtifactEntry(path="product.json", bytes=4, sha256="d" * 64, executable=False)]
        )
        assert_no_concept_pixels_in_product(concept_tree, product_manifest)

    def test_a_product_file_matching_a_concept_image_is_refused(self):
        concept_tree = _tree(
            manifest_entries=[
                ArtifactEntry(path="images/front.png", bytes=4, sha256="c" * 64, executable=False),
            ]
        )
        product_manifest = _manifest(
            [
                ArtifactEntry(
                    path="renders/hero.png", bytes=4, sha256="c" * 64, executable=False
                )
            ]
        )
        with self.assertRaisesRegex(ContractError, "carries concept image bytes"):
            assert_no_concept_pixels_in_product(concept_tree, product_manifest)

    def test_a_matching_non_image_concept_file_is_not_checked(self):
        concept_tree = _tree(
            manifest_entries=[
                ArtifactEntry(path="brief.json", bytes=4, sha256="c" * 64, executable=False),
            ]
        )
        product_manifest = _manifest(
            [ArtifactEntry(path="product.json", bytes=4, sha256="c" * 64, executable=False)]
        )
        assert_no_concept_pixels_in_product(concept_tree, product_manifest)


if __name__ == "__main__":
    unittest.main()
