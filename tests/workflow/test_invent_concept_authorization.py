import json
import tempfile
import unittest
from pathlib import Path

from workshop.integrations.concept_images import ConceptImageProfile
from workshop.workflow.native_run import NativeRunPaths, _record_authorization


class InventConceptAuthorizationTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.paths = NativeRunPaths(root / "workspace", root / "state")
        self.paths.host_state.mkdir(parents=True)

    def test_v3_preserves_publication_and_discloses_exact_concept_profile(self):
        profile = ConceptImageProfile()
        authority = {
            "profile_id": profile.profile_id,
            "profile_sha256": profile.profile_sha256,
            "transmitted_data_classes": [
                "drawing-instruction-text", "exact-prior-role-images"
            ],
        }
        value = _record_authorization(
            self.paths,
            product_id="moon-lamp",
            publish_requested=True,
            github_publish_requested=True,
            concept_render_authority=authority,
            create=True,
        )
        self.assertEqual(value["schema_version"], 3)
        self.assertEqual(value["concept_render_authority"], authority)
        observed = _record_authorization(
            self.paths,
            product_id="moon-lamp",
            publish_requested=False,
            create=False,
        )
        self.assertTrue(observed["publish_requested"])
        self.assertTrue(observed["github_publish_requested"])
        self.assertEqual(observed["concept_render_authority"], authority)

    def test_legacy_authorization_remains_readable_without_render_authority(self):
        path = self.paths.host_state / "authorization.json"
        path.write_text(json.dumps({
            "schema_version": 2,
            "kind": "autonomous-workshop.run-authorization",
            "product_id": "legacy",
            "publish_requested": True,
            "github_publish_requested": False,
        }, sort_keys=True, separators=(",", ":")) + "\n")
        path.chmod(0o600)
        value = _record_authorization(
            self.paths,
            product_id="legacy",
            publish_requested=False,
            create=False,
        )
        self.assertEqual(value["schema_version"], 3)
        self.assertIsNone(value["concept_render_authority"])


if __name__ == "__main__":
    unittest.main()
