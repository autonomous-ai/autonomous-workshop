import json
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ContractError
from workshop.release import ProductRelease
from workshop.runtime import Receipt


SHA256 = "a" * 64


class ProductReleaseContractTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve() / "release"
        self.root.mkdir()
        self.claims = {"mechanical-test": {"passed": True}}
        (self.root / "MANUAL.md").write_text("# Manual\n\nUse the toy safely.\n")
        (self.root / "product.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "kind": "workshop.release-package",
                    "status": "facts-ready",
                    "product_artifact_sha256": SHA256,
                    "claims": self.claims,
                    "factory_enrichment": {
                        "copy_owner": "factory",
                        "media_owner": "factory",
                        "status": "pending",
                    },
                }
            )
            + "\n"
        )
        self.manifest = build_artifact_manifest(
            self.root, created_at="content-addressed"
        )

    def receipt(self, *, page_url=True, project_url=None):
        details = {"release_sha256": self.manifest.artifact_sha256}
        if page_url:
            details["page_url"] = (
                "https://www.autonomous.ai/factory/product/current-route"
            )
        return Receipt(
            payload_sha256="b" * 64,
            artifact_sha256=SHA256,
            adapter="factory",
            status="draft",
            observed_at="2026-08-26T00:00:00Z",
            reference="design-1",
            details=details,
            design_id="design-1",
            slug="current-route",
            owner_id="owner-1",
            root_id="design-1",
            current_history_id="history-1",
            project_url=project_url or "https://cdn.autonomous.ai/projects/history-1/",
        )

    def test_site_receipt_is_the_only_receipt_property(self):
        receipt = self.receipt()
        release = ProductRelease.from_root(
            self.root, SHA256, "MANUAL.md", self.claims, receipt
        )

        self.assertIs(release.site_receipt, receipt)
        self.assertFalse(hasattr(release, "publication_receipt"))
        self.assertEqual(
            release.page_url,
            "https://www.autonomous.ai/factory/product/current-route",
        )

    def test_project_url_cannot_substitute_for_page_url(self):
        receipt = self.receipt(
            page_url=False,
            project_url="https://www.autonomous.ai/factory/product/old-route",
        )

        with self.assertRaisesRegex(ContractError, "customer product page URL"):
            ProductRelease.from_root(
                self.root, SHA256, "MANUAL.md", self.claims, receipt
            )


if __name__ == "__main__":
    unittest.main()
