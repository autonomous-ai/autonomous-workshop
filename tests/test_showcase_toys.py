import json
import re
import unittest
from pathlib import Path

from inventor_workshop.artifacts import build_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHOWCASE_TOYS = {
    "alice": ("Alice", "five-job-checkers"),
    "bob": ("Bob", "comet-geneva"),
    "eve": ("Eve", "rackhaven-night-shift"),
    "ivy": ("Ivy", "montauk-tide-orrery"),
    "leo": ("Leo", "counterorbit"),
}
PRINTED_PIECE_COUNTS = {
    "alice": 25,
    "bob": 5,
    "eve": 5,
    "ivy": 6,
    "leo": 12,
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ShowcaseToyTest(unittest.TestCase):
    def toy_root(self, inventor_id, slug):
        return ROOT / "inventors" / inventor_id / "toys" / slug

    def test_the_five_showcases_use_the_one_toys_collection(self):
        for inventor_id, (_, slug) in SHOWCASE_TOYS.items():
            with self.subTest(inventor_id=inventor_id):
                inventor_root = ROOT / "inventors" / inventor_id
                self.assertTrue(self.toy_root(inventor_id, slug).is_dir())
                self.assertFalse((inventor_root / "games").exists())
                self.assertFalse((inventor_root / "products").exists())

    def test_records_credit_inventor_and_preserve_truthful_instructions_state(self):
        for inventor_id, (inventor_name, slug) in SHOWCASE_TOYS.items():
            with self.subTest(inventor_id=inventor_id):
                toy = self.toy_root(inventor_id, slug)
                product_path = toy / "artifact" / "product.json"
                receipt_path = toy / "workshop-run.json"
                self.assertTrue(product_path.is_file())
                self.assertTrue(receipt_path.is_file())

                product = load_json(product_path)
                description = product["description"]
                self.assertEqual(
                    product["inventor"],
                    {"id": inventor_id, "name": inventor_name},
                )
                self.assertTrue(description.endswith("By %s." % inventor_name))
                self.assertEqual(description, description.rstrip())
                self.assertEqual(product["status"], "digital-prototype")
                self.assertIs(product["physical_prototype"], False)
                self.assertEqual(product["reviews_status"], "begins-after-delivery")

                receipt = load_json(receipt_path)
                self.assertEqual(receipt["inventor"]["id"], inventor_id)
                self.assertEqual(receipt["inventor"]["name"], inventor_name)
                self.assertEqual(receipt["run"]["status"], "waiting")
                self.assertIn(receipt["run"]["job"], ("instructions", "deliver"))
                self.assertEqual(
                    receipt["run"]["artifact_sha256"],
                    receipt["artifact_sha256"],
                )
                self.assertIsNone(receipt["run"]["delivery"])
                waiting_for = {
                    need["capability"] for need in receipt["run"]["needs"]
                }
                self.assertTrue(receipt["assertions"]["ai_playtest_passed"])
                self.assertTrue(receipt["assertions"]["instructions_created"])
                self.assertFalse(receipt["assertions"]["site_page_live"])
                self.assertFalse(receipt["assertions"]["customer_reviews"])
                if receipt["run"]["job"] == "instructions":
                    self.assertIsNone(receipt["run"]["instructions_sha256"])
                    self.assertEqual(waiting_for, {"site-page"})
                    self.assertFalse(receipt["assertions"]["site_draft_verified"])
                    self.assertIsNone(receipt["site_receipt"])
                    self.assertIsNone(receipt["run"]["page_url"])
                else:
                    self.assertEqual(
                        receipt["run"]["instructions_sha256"],
                        receipt["instructions_sha256"],
                    )
                    self.assertEqual(waiting_for, {"production-and-shipping"})
                    self.assertTrue(receipt["assertions"]["site_draft_verified"])
                    self.assertEqual(receipt["site_receipt"]["status"], "draft")
                    self.assertIsNone(
                        receipt["site_receipt"]["published_history_id"]
                    )
                    self.assertEqual(
                        receipt["site_receipt"]["details"]["page_url"],
                        receipt["run"]["page_url"],
                    )

    def test_manifests_bind_every_checked_in_artifact_and_evidence_file(self):
        required_artifacts = {
            "project.json",
            "product.json",
            "assembled.stl",
            "assembled.step",
            "assembled.step.json",
            "cad/design.json",
            "cad/model.py",
            "cad/product.step",
            "cad/product.stl",
            "images/hero.png",
        }
        for inventor_id, (_, slug) in SHOWCASE_TOYS.items():
            with self.subTest(inventor_id=inventor_id):
                toy = self.toy_root(inventor_id, slug)
                receipt = load_json(toy / "workshop-run.json")
                for directory, manifest_name, receipt_key in (
                    ("artifact", "artifact-manifest.json", "artifact_sha256"),
                    ("evidence", "evidence-manifest.json", "evidence_sha256"),
                    ("instructions", "instructions-manifest.json", "instructions_sha256"),
                ):
                    manifest_path = toy / manifest_name
                    self.assertTrue(manifest_path.is_file())
                    stored = load_json(manifest_path)
                    self.assertRegex(stored["artifact_sha256"], SHA256)
                    self.assertEqual(
                        receipt[receipt_key], stored["artifact_sha256"]
                    )
                    current = build_artifact_manifest(
                        toy / directory, created_at=stored["created_at"]
                    ).to_dict()
                    self.assertEqual(current, stored)
                    for entry in stored["entries"]:
                        self.assertRegex(entry["sha256"], SHA256)
                        self.assertTrue((toy / directory / entry["path"]).is_file())

                artifact_paths = {
                    entry["path"]
                    for entry in load_json(toy / "artifact-manifest.json")["entries"]
                }
                self.assertTrue(required_artifacts.issubset(artifact_paths))
                self.assertEqual(
                    (toy / "artifact" / "assembled.stl").read_bytes(),
                    (toy / "artifact" / "cad" / "product.stl").read_bytes(),
                )
                evidence_index = load_json(toy / "evidence" / "evidence-index.json")
                self.assertEqual(evidence_index["status"], "passed-ai-playtest")
                self.assertEqual(evidence_index["unresolved_canonical_capabilities"], [])
                self.assertEqual(
                    evidence_index["artifact_sha256"], receipt["artifact_sha256"]
                )
                instructions_page = load_json(toy / "instructions" / "product.json")
                self.assertEqual(
                    instructions_page["product_artifact_sha256"],
                    receipt["artifact_sha256"],
                )
                self.assertEqual(
                    instructions_page["playtest_evidence_artifact_sha256"],
                    receipt["evidence_sha256"],
                )
                self.assertFalse(
                    {"images", "use_case", "story_blocks"}
                    & set(instructions_page)
                )
                self.assertEqual(
                    instructions_page["factory_enrichment"],
                    {
                        "copy_owner": "factory",
                        "media_owner": "factory",
                        "status": "pending",
                    },
                )

    def test_printed_piece_truth_matches_the_occurrence_sidecar(self):
        for inventor_id, (_, slug) in SHOWCASE_TOYS.items():
            with self.subTest(inventor_id=inventor_id):
                artifact = self.toy_root(inventor_id, slug) / "artifact"
                product = load_json(artifact / "product.json")
                sidecar = load_json(artifact / "assembled.step.json")
                build = load_json(artifact / "cad" / "digital-build.json")
                expected = PRINTED_PIECE_COUNTS[inventor_id]
                names = [item["name"] for item in sidecar["parts"]]

                self.assertEqual(product["design"]["printed_piece_count"], expected)
                self.assertEqual(len(names), expected)
                self.assertEqual(len(names), len(set(names)))
                self.assertEqual(
                    build["factory_assembly"]["occurrence_count"], expected
                )
                self.assertEqual(
                    build["factory_assembly"]["step_solid_count"], expected
                )
                self.assertEqual(build["product"]["step"]["solid_count"], expected)
                self.assertEqual(build["product"]["stl"]["shell_count"], expected)
                self.assertTrue(
                    all(
                        record["step"]["solid_count"] == 1
                        and record["stl"]["shell_count"] == 1
                        for record in build["parts"].values()
                    )
                )
                self.assertEqual(build["factory_assembly"]["part_names"], names)
                if inventor_id == "bob":
                    expected_components = [
                        "one base",
                        "two axles (one is the hand-crank input axle)",
                        "one comet drive wheel",
                        "one six-slot orbit wheel",
                    ]
                    self.assertEqual(product["components"], expected_components)
                    instructions = load_json(
                        self.toy_root(inventor_id, slug)
                        / "instructions"
                        / "product.json"
                    )
                    self.assertEqual(
                        instructions["what_arrives"], expected_components
                    )
                if inventor_id == "ivy":
                    self.assertEqual(len(product["components"]), 6)
                    self.assertIn("one center post", product["components"])
                    self.assertIn("one Earth hub", product["components"])
                    self.assertIn(
                        "all six printed pieces", product["factory_brief"]
                    )


if __name__ == "__main__":
    unittest.main()
