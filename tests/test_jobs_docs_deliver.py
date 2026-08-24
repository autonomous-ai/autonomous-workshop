import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.deliver import DefaultDeliver
from inventor_workshop.docs import DefaultDocs, REQUIRED_PRODUCT_IMAGES
from inventor_workshop.errors import ArtifactError, ContractError
from inventor_workshop.jobs import (
    DeliverContext,
    Delivered,
    DocsContext,
    Made,
    Need,
    Playtested,
    ProductDocs,
    WaitingFor,
)
from inventor_workshop.make import Wish
from inventor_workshop.models import PlaytestResult
from inventor_workshop.playtest import Playtest
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint


CONFIG_SHA256 = "c" * 64


class WorkshopJobFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        inventor = self.root / "inventor"
        inventor.mkdir()
        (inventor / "TASTE.md").write_text(
            "# Alice\n\nSmall games with one surprising decision.\n",
            encoding="utf-8",
        )
        self.taste = load_taste(inventor)
        self.wish = Wish.create("pocket-duel", "A surprising pocket duel")
        self.blueprint = ToyBlueprint.for_lane("classics-made-yours")

        self.product_root = self.root / "product"
        self.product_root.mkdir()
        (self.product_root / "board.step").write_text(
            "ISO-10303-21; exact product bytes\n", encoding="utf-8"
        )
        (self.product_root / "rules.md").write_text(
            "Choose one hidden cap, then reveal.\n", encoding="utf-8"
        )
        self.made = Made.from_root(
            self.product_root,
            {
                "title": "Pocket Duel",
                "summary": "A tiny bluffing game with a satisfying reveal.",
                "lane": "classics-made-yours",
                "instructions": "Choose, commit, and reveal.",
                "components": ["board", "six caps"],
                "limitations": ["AI simulation is not human delight evidence."],
            },
        )

        self.evidence_root = self.root / "evidence"
        evidence_file = self.evidence_root / "gameplay" / "league.json"
        evidence_file.parent.mkdir(parents=True)
        evidence_file.write_text(
            '{"completed":128,"termination_rate":1.0}\n', encoding="utf-8"
        )
        self.evidence_manifest = build_artifact_manifest(
            self.evidence_root, created_at="content-addressed"
        )
        result = PlaytestResult.create(
            "gameplay-league",
            True,
            self.made.artifact_sha256,
            {
                "evidence_class": "ai-simulation",
                "claims": [
                    "128 seeded simulated games terminated under the tested rules."
                ],
                "completed": 128,
            },
            "workshop-gameplay-league",
            "1.0.0",
            CONFIG_SHA256,
            "gameplay/league.json",
            hashlib.sha256(evidence_file.read_bytes()).hexdigest(),
        )
        self.playtested = Playtested(
            Playtest(
                self.made.artifact_manifest,
                (result,),
                evidence_manifest=self.evidence_manifest,
            )
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def docs_context(self, name: str = "docs") -> DocsContext:
        return DocsContext(
            self.wish,
            self.taste,
            self.blueprint,
            self.made,
            self.playtested,
            self.root / name,
        )

    @staticmethod
    def media_maker(context: DocsContext):
        images = context.workspace / "images"
        images.mkdir(parents=True)
        paths = {}
        for role in REQUIRED_PRODUCT_IMAGES:
            path = images / (role + ".png")
            path.write_bytes(("fake PNG for %s\n" % role).encode("utf-8"))
            paths[role] = path.relative_to(context.workspace).as_posix()
        return paths

    def generated_docs(self, name: str = "docs") -> ProductDocs:
        return DefaultDocs(self.media_maker)(self.docs_context(name))

    def delivery_evidence(self):
        return {
            "print_receipt": {"job_id": "print-1", "passed": True},
            "qa_receipt": {"job_id": "qa-1", "passed": True},
            "packing_receipt": {"box_id": "box-1", "passed": True},
            "carrier_receipt": {"acceptance_scan": "scan-1", "passed": True},
        }

    def delivered(self, docs: ProductDocs, **changes) -> Delivered:
        values = {
            "product_artifact_sha256": self.made.artifact_sha256,
            "docs_sha256": docs.docs_sha256,
            "carrier": "USPS",
            "service": "Priority Mail",
            "tracking_id": "9400100000000000000000",
            "status": "handed-off",
            "observed_at": "2026-08-23T12:00:00+00:00",
            "evidence": self.delivery_evidence(),
        }
        values.update(changes)
        return Delivered(**values)


class JobBindingTest(WorkshopJobFixture):
    def test_made_detects_product_bytes_changed_after_make(self):
        (self.product_root / "rules.md").write_text(
            "silently changed rules\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ArtifactError, "bytes changed"):
            self.made.assert_current()

    def test_made_deep_copies_product_metadata(self):
        product = {
            "title": "Mutable Toy",
            "summary": "The input object must not remain live.",
            "lane": "classics-made-yours",
            "components": [{"name": "cap"}],
        }
        made = Made.from_root(self.product_root, product)
        product["components"][0]["name"] = "changed"
        self.assertEqual(made.product["components"][0]["name"], "cap")

    def test_made_rejects_products_outside_the_five_plaything_lanes(self):
        with self.assertRaisesRegex(ContractError, "plaything lane"):
            Made.from_root(
                self.product_root,
                {
                    "title": "Plain Shelf",
                    "summary": "Merely useful.",
                    "lane": "storage",
                },
            )

    def test_playtest_is_bound_to_exact_product_hash(self):
        with self.assertRaisesRegex(ContractError, "different artifact bytes"):
            self.playtested.assert_artifact("0" * 64)

    def test_docs_reject_failed_playtest(self):
        original = self.playtested.evidence.results[0]
        failed = PlaytestResult.create(
            original.playtest_id,
            False,
            original.artifact_sha256,
            original.evidence,
            original.evaluator,
            original.evaluator_version,
            original.config_sha256,
            original.evidence_ref,
            original.evidence_sha256,
        )
        playtested = Playtested(
            Playtest(
                self.made.artifact_manifest,
                (failed,),
                evidence_manifest=self.evidence_manifest,
            )
        )
        with self.assertRaisesRegex(ContractError, "before Playtest passes"):
            DocsContext(
                self.wish,
                self.taste,
                self.blueprint,
                self.made,
                playtested,
                self.root / "failed-docs",
            )

    def test_docs_reject_playtest_for_different_product(self):
        other_root = self.root / "other-product"
        other_root.mkdir()
        (other_root / "toy.step").write_text("different bytes\n", encoding="utf-8")
        other = Made.from_root(
            other_root,
            {
                "title": "Other",
                "summary": "Other toy",
                "lane": "classics-made-yours",
            },
        )
        with self.assertRaisesRegex(ContractError, "different artifact bytes"):
            DocsContext(
                self.wish,
                self.taste,
                self.blueprint,
                other,
                self.playtested,
                self.root / "detached-docs",
            )


class DocsJobTest(WorkshopJobFixture):
    def test_docs_wait_truthfully_when_no_media_provider_exists(self):
        context = self.docs_context("waiting-docs")
        with self.assertRaises(WaitingFor) as raised:
            DefaultDocs()(context)
        self.assertEqual(len(raised.exception.needs), 1)
        need = raised.exception.needs[0]
        self.assertIsInstance(need, Need)
        self.assertEqual((need.job, need.capability), ("docs", "product-images"))
        self.assertFalse(context.workspace.exists())

    def test_docs_require_every_fixed_image_role(self):
        def incomplete(context):
            media = self.media_maker(context)
            del media["box"]
            return media

        with self.assertRaisesRegex(ContractError, "box"):
            DefaultDocs(incomplete)(self.docs_context("incomplete-docs"))

    def test_docs_reject_one_file_claimed_as_every_fixed_view(self):
        def repeated(context):
            path = context.workspace / "one.png"
            path.write_bytes(b"not five distinct views")
            return {role: "one.png" for role in REQUIRED_PRODUCT_IMAGES}

        with self.assertRaisesRegex(ContractError, "distinct"):
            DefaultDocs(repeated)(self.docs_context("repeated-docs"))

    def test_docs_reject_media_outside_workspace(self):
        outside = self.root / "outside.png"
        outside.write_bytes(b"outside")

        def escaped(context):
            media = self.media_maker(context)
            media["hero"] = "../outside.png"
            return media

        with self.assertRaisesRegex(ContractError, "stay inside"):
            DefaultDocs(escaped)(self.docs_context("escaped-docs"))

    def test_docs_page_is_private_and_preserves_claim_provenance(self):
        docs = self.generated_docs("complete-docs")
        page = json.loads((docs.root / docs.page_path).read_text(encoding="utf-8"))
        self.assertEqual(page["status"], "private")
        self.assertEqual(set(page["images"]), set(REQUIRED_PRODUCT_IMAGES))
        self.assertEqual(page["product_artifact_sha256"], self.made.artifact_sha256)
        claim = page["claims"]["gameplay-league"]
        result = self.playtested.evidence.results[0]
        self.assertEqual(claim["evidence_class"], "ai-simulation")
        self.assertEqual(claim["evidence_ref"], result.evidence_ref)
        self.assertEqual(claim["evidence_sha256"], result.evidence_sha256)
        self.assertIn("simulated", claim["claims"][0])
        self.assertNotIn("human", claim["claims"][0].casefold())
        self.assertEqual(docs.claims, page["claims"])

    def test_docs_detect_changed_bytes_after_generation(self):
        docs = self.generated_docs("tampered-docs")
        (docs.root / "README.md").write_text("changed after approval\n", encoding="utf-8")
        with self.assertRaisesRegex(ArtifactError, "bytes changed"):
            docs.assert_current()

    def test_docs_detect_product_tampering_before_calling_media_provider(self):
        context = self.docs_context("product-tamper-docs")
        (self.product_root / "rules.md").write_text("changed\n", encoding="utf-8")
        calls = []

        def media(observed):
            calls.append(observed)
            return self.media_maker(observed)

        with self.assertRaisesRegex(ArtifactError, "bytes changed"):
            DefaultDocs(media)(context)
        self.assertEqual(calls, [])


class DeliverJobTest(WorkshopJobFixture):
    def test_deliver_waits_truthfully_without_real_fulfiller(self):
        docs = self.generated_docs("waiting-delivery-docs")
        context = DeliverContext(self.wish, self.made, docs)
        with self.assertRaises(WaitingFor) as raised:
            DefaultDeliver()(context)
        need = raised.exception.needs[0]
        self.assertEqual(
            (need.job, need.capability), ("deliver", "production-and-shipping")
        )

    def test_delivery_requires_supported_carrier_and_all_receipts(self):
        docs = self.generated_docs("receipt-docs")
        with self.assertRaisesRegex(ContractError, "USPS, UPS, or FedEx"):
            self.delivered(docs, carrier="DHL")
        evidence = self.delivery_evidence()
        del evidence["qa_receipt"]
        with self.assertRaisesRegex(ContractError, "qa_receipt"):
            self.delivered(docs, evidence=evidence)
        evidence = self.delivery_evidence()
        evidence["packing_receipt"] = {}
        with self.assertRaisesRegex(ContractError, "packing_receipt"):
            self.delivered(docs, evidence=evidence)
        with self.assertRaisesRegex(ContractError, "handed-off or delivered"):
            self.delivered(docs, status="label-created")

    def test_deliver_rejects_receipt_for_other_product_or_docs(self):
        docs = self.generated_docs("hash-docs")
        context = DeliverContext(self.wish, self.made, docs)
        wrong_product = self.delivered(docs, product_artifact_sha256="0" * 64)
        with self.assertRaisesRegex(ContractError, "different product or Docs bytes"):
            DefaultDeliver(lambda ignored: wrong_product)(context)
        wrong_docs = self.delivered(docs, docs_sha256="1" * 64)
        with self.assertRaisesRegex(ContractError, "different product or Docs bytes"):
            DefaultDeliver(lambda ignored: wrong_docs)(context)

    def test_deliver_accepts_receipts_for_exact_approved_bytes(self):
        docs = self.generated_docs("exact-docs")
        context = DeliverContext(self.wish, self.made, docs)
        receipt = self.delivered(docs)
        result = DefaultDeliver(lambda observed: receipt)(context)
        self.assertIs(result, receipt)
        self.assertEqual(result.product_artifact_sha256, self.made.artifact_sha256)
        self.assertEqual(result.docs_sha256, docs.docs_sha256)

    def test_deliver_detects_docs_tampering_before_calling_fulfiller(self):
        docs = self.generated_docs("delivery-tamper-docs")
        context = DeliverContext(self.wish, self.made, docs)
        (docs.root / "product.json").write_text("{}\n", encoding="utf-8")
        calls = []

        def fulfiller(observed):
            calls.append(observed)
            return self.delivered(docs)

        with self.assertRaisesRegex(ArtifactError, "bytes changed"):
            DefaultDeliver(fulfiller)(context)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
