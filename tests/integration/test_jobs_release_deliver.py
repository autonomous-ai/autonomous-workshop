import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts.core import build_artifact_manifest
from workshop.deliver.service import DefaultDeliver
from workshop.deliver.evidence import DeliveryEvidenceReceipt
from workshop.release.service import DefaultRelease
from workshop.errors import ArtifactError, ContractError
from workshop.deliver.contracts import DeliverContext, Delivered
from workshop.release.contracts import ReleaseContext, ProductRelease
from workshop.make.contracts import Made
from workshop.outcomes import Need, WaitingFor
from workshop.playtest.contracts import Playtested
from workshop.wish import Wish
from workshop.playtest.evidence import PlaytestResult
from workshop.runtime import Receipt
from workshop.playtest.service import Playtest
from workshop.contributors.taste import load_taste
from workshop.product.blueprints import ToyBlueprint


CONFIG_SHA256 = "c" * 64


class WorkshopJobFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        inventor = self.root / "inventor"
        inventor.mkdir()
        (inventor / "TASTE.md").write_text(
            "---\n"
            "name: Alice\n"
            "description: Small games with one surprising decision.\n"
            "---\n"
            "# Alice\n\n"
            "Small games with one surprising decision.\n",
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

    def release_context(
        self, name: str = "release"
    ) -> ReleaseContext:
        return ReleaseContext(
            self.wish,
            self.taste,
            self.blueprint,
            self.made,
            self.playtested,
            self.root / name,
        )

    @staticmethod
    def site_writer(context, sealed_root, sealed_manifest):
        del sealed_root
        return Receipt(
            pack_sha256="f" * 64,
            artifact_sha256=context.made.artifact_sha256,
            design_id="design-pocket-duel",
            slug="pocket-duel",
            owner_id="owner-alice",
            root_id="design-pocket-duel",
            current_history_id="history-1",
            published_history_id=None,
            status="draft",
            project_url="https://cdn.autonomous.ai/projects/history-1/",
            observed_at="2026-08-23T12:00:00+00:00",
            details={
                "release_sha256": sealed_manifest.artifact_sha256,
                "page_url": "https://www.autonomous.ai/factory/product/pocket-duel",
            },
        )

    def generated_release(
        self, name: str = "release"
    ) -> ProductRelease:
        return DefaultRelease(site_writer=self.site_writer)(
            self.release_context(name)
        )

    def delivery_evidence(
        self,
        release_sha256=None,
        *,
        product_artifact_sha256=None,
        carrier="USPS",
        service="Priority Mail",
        tracking_id="9400100000000000000000",
        status="handed-off",
        observed_at="2026-08-23T12:00:00+00:00",
    ):
        product_sha256 = product_artifact_sha256 or self.made.artifact_sha256
        release_sha256 = release_sha256 or self._delivery_release_sha256
        common = {
            "provider": "fixture-fulfillment-bench",
            "provider_version": "1.0.0",
            "provider_config_sha256": "d" * 64,
            "product_artifact_sha256": product_sha256,
            "release_sha256": release_sha256,
            "observed_at": observed_at,
        }
        printed = DeliveryEvidenceReceipt(
            stage="print",
            receipt_id="print-receipt-1",
            details={
                "job_id": "print-1",
                "status": "completed",
                "quantity": 1,
                "material": "PLA",
                "output_lot_id": "lot-1",
            },
            **common,
        )
        qa = DeliveryEvidenceReceipt(
            stage="qa",
            receipt_id="qa-receipt-1",
            details={
                "inspection_id": "qa-1",
                "status": "passed",
                "print_receipt_sha256": printed.receipt_sha256,
                "checks": ["exact-product", "fit", "finish", "safety"],
            },
            **common,
        )
        packed = DeliveryEvidenceReceipt(
            stage="packing",
            receipt_id="packing-receipt-1",
            details={
                "package_id": "box-1",
                "status": "sealed",
                "print_receipt_sha256": printed.receipt_sha256,
                "qa_receipt_sha256": qa.receipt_sha256,
                "contents_count": 2,
            },
            **common,
        )
        carrier_receipt = DeliveryEvidenceReceipt(
            stage="carrier",
            receipt_id="carrier-receipt-1",
            details={
                "carrier": carrier,
                "service": service,
                "tracking_id": tracking_id,
                "status": status,
                "package_id": "box-1",
                "packing_receipt_sha256": packed.receipt_sha256,
                "acceptance_scan_id": "scan-1",
            },
            **common,
        )
        return {
            "print_receipt": printed.to_dict(),
            "qa_receipt": qa.to_dict(),
            "packing_receipt": packed.to_dict(),
            "carrier_receipt": carrier_receipt.to_dict(),
        }

    def delivered(
        self, release: ProductRelease, **changes
    ) -> Delivered:
        self._delivery_release_sha256 = release.release_sha256
        values = {
            "product_artifact_sha256": self.made.artifact_sha256,
            "release_sha256": release.release_sha256,
            "carrier": "USPS",
            "service": "Priority Mail",
            "tracking_id": "9400100000000000000000",
            "status": "handed-off",
            "observed_at": "2026-08-23T12:00:00+00:00",
        }
        values.update(changes)
        if "evidence" not in values:
            values["evidence"] = self.delivery_evidence(
                values["release_sha256"],
                product_artifact_sha256=values["product_artifact_sha256"],
                carrier=values["carrier"],
                service=values["service"],
                tracking_id=values["tracking_id"],
                status=values["status"],
                observed_at=values["observed_at"],
            )
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

    def test_release_reject_failed_playtest(self):
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
            ReleaseContext(
                self.wish,
                self.taste,
                self.blueprint,
                self.made,
                playtested,
                self.root / "failed-release",
            )

    def test_release_reject_playtest_for_different_product(self):
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
            ReleaseContext(
                self.wish,
                self.taste,
                self.blueprint,
                other,
                self.playtested,
                self.root / "detached-release",
            )


class ReleaseJobTest(WorkshopJobFixture):
    def test_release_wait_truthfully_when_no_site_writer_exists(self):
        context = self.release_context("waiting-release")
        with self.assertRaises(WaitingFor) as raised:
            DefaultRelease()(context)
        self.assertEqual(len(raised.exception.needs), 1)
        self.assertTrue(all(isinstance(need, Need) for need in raised.exception.needs))
        self.assertEqual(
            {need.capability for need in raised.exception.needs},
            {"site-page"},
        )
        self.assertFalse(context.workspace.exists())

    def test_release_reject_retired_creator_media_provider(self):
        with self.assertRaisesRegex(ContractError, "Factory owns"):
            DefaultRelease(media_maker=lambda context: {})

    def test_release_reject_site_receipt_for_unverified_or_different_bytes(self):
        def unverified(context, sealed_root, sealed_manifest):
            del sealed_root
            receipt = self.site_writer(context, None, sealed_manifest)
            value = receipt.to_dict()
            value["current_history_id"] = None
            return Receipt.from_dict(value)

        with self.assertRaisesRegex(ContractError, "authenticated private draft"):
            DefaultRelease(site_writer=unverified)(
                self.release_context("unverified-site-release")
            )

        def wrong_page(context, sealed_root, sealed_manifest):
            del sealed_root
            receipt = self.site_writer(context, None, sealed_manifest)
            value = receipt.to_dict()
            value["details"] = {
                **value["details"],
                "release_sha256": "0" * 64,
            }
            return Receipt.from_dict(value)

        with self.assertRaisesRegex(ContractError, "different facts"):
            DefaultRelease(site_writer=wrong_page)(
                self.release_context("wrong-site-release")
            )

    def test_verified_public_receipt_remains_compatible_for_custom_writers(self):
        def public_writer(context, sealed_root, sealed_manifest):
            receipt = self.site_writer(context, sealed_root, sealed_manifest)
            value = receipt.to_dict()
            value.update(
                {
                    "status": "public",
                    "published_history_id": value["current_history_id"],
                    "listing_active": True,
                    "listing_price_cents": 3500,
                    "listing_currency": "USD",
                    "listing_sku": "PD-001",
                }
            )
            return Receipt.from_dict(value)

        release = DefaultRelease(site_writer=public_writer)(
            self.release_context("legacy-public-release")
        )
        self.assertTrue(release.is_public)
        self.assertTrue(release.site_receipt.is_verified_public)

    def test_release_output_is_box_ready_and_page_preserves_provenance(self):
        release = self.generated_release("complete-release")
        page = json.loads(
            (release.root / "product.json").read_text(encoding="utf-8")
        )
        self.assertEqual(page["status"], "facts-ready")
        self.assertEqual(page["kind"], "workshop.release-package")
        self.assertEqual(
            page["summary"],
            "A tiny bluffing game with a satisfying reveal.\n\nBy Alice.",
        )
        self.assertEqual(page["instructions_kind"], "rulebook")
        self.assertEqual(page["how_to_play"], "Choose, commit, and reveal.")
        self.assertNotIn("how_to_use", page)
        self.assertFalse({"images", "use_case", "story_blocks"} & set(page))
        self.assertEqual(
            page["factory_enrichment"],
            {"copy_owner": "factory", "media_owner": "factory", "status": "pending"},
        )
        self.assertEqual(page["product_artifact_sha256"], self.made.artifact_sha256)
        claim = page["claims"]["gameplay-league"]
        result = self.playtested.evidence.results[0]
        self.assertEqual(claim["evidence_class"], "ai-simulation")
        self.assertEqual(claim["evidence_ref"], result.evidence_ref)
        self.assertEqual(claim["evidence_sha256"], result.evidence_sha256)
        self.assertIn("simulated", claim["claims"][0])
        self.assertNotIn("human", claim["claims"][0].casefold())
        self.assertEqual(release.claims, page["claims"])
        self.assertEqual(release.manual_path, "MANUAL.md")
        self.assertTrue(release.site_receipt.is_verified_draft)
        self.assertFalse(release.is_public)
        self.assertEqual(
            release.page_url,
            "https://www.autonomous.ai/factory/product/pocket-duel",
        )
        insert = (release.root / release.manual_path).read_text(
            encoding="utf-8"
        )
        self.assertIn("## How to play", insert)
        self.assertIn("## What's in the box", insert)
        self.assertIn("## Care and safety", insert)
        self.assertIn("\n\nBy Alice.\n\n## How to play", insert)
        self.assertEqual(insert.count("By Alice."), 1)
        self.assertFalse(insert.endswith(" \n"))
        self.assertFalse((release.root / "README.md").exists())

    def test_non_game_output_uses_release_and_how_to_use(self):
        moving_made = Made.from_root(
            self.product_root,
            {
                **self.made.product,
                "lane": "moving-machines",
                "instructions": "Turn the crank clockwise and watch the rhythm.",
            },
        )
        context = ReleaseContext(
            self.wish,
            self.taste,
            ToyBlueprint.for_lane("moving-machines"),
            moving_made,
            self.playtested,
            self.root / "moving-machine-release",
        )
        release = DefaultRelease(site_writer=self.site_writer)(context)
        page = json.loads(
            (release.root / "product.json").read_text(encoding="utf-8")
        )
        self.assertEqual(page["instructions_kind"], "instructions")
        self.assertEqual(
            page["how_to_use"],
            "Turn the crank clockwise and watch the rhythm.",
        )
        self.assertNotIn("how_to_play", page)
        insert = (release.root / "MANUAL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## How to use", insert)
        self.assertNotIn("## How to play", insert)

    def test_release_detect_changed_bytes_after_generation(self):
        release = self.generated_release("tampered-release")
        (release.root / "MANUAL.md").write_text(
            "changed after approval\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ArtifactError, "bytes changed"):
            release.assert_current()

    def test_release_detect_product_tampering_before_calling_site_writer(self):
        context = self.release_context("product-tamper-release")
        (self.product_root / "rules.md").write_text("changed\n", encoding="utf-8")
        calls = []

        def writer(observed, sealed_root, sealed_manifest):
            del sealed_root
            calls.append(observed)
            return self.site_writer(observed, None, sealed_manifest)

        with self.assertRaisesRegex(ArtifactError, "bytes changed"):
            DefaultRelease(site_writer=writer)(context)
        self.assertEqual(calls, [])


class DeliverJobTest(WorkshopJobFixture):
    def test_deliver_waits_truthfully_without_real_fulfiller(self):
        release = self.generated_release("waiting-delivery-release")
        context = DeliverContext(self.wish, self.made, release)
        with self.assertRaises(WaitingFor) as raised:
            DefaultDeliver()(context)
        need = raised.exception.needs[0]
        self.assertEqual(
            (need.job, need.capability), ("deliver", "production-and-shipping")
        )

    def test_delivery_requires_supported_carrier_and_all_receipts(self):
        release = self.generated_release("receipt-release")
        with self.assertRaisesRegex(ContractError, "unsupported carrier"):
            self.delivered(release, carrier="DHL")
        self._delivery_release_sha256 = release.release_sha256
        evidence = self.delivery_evidence()
        del evidence["qa_receipt"]
        with self.assertRaisesRegex(ContractError, "four receipts"):
            self.delivered(release, evidence=evidence)
        evidence = self.delivery_evidence()
        evidence["packing_receipt"] = {}
        with self.assertRaisesRegex(ContractError, "envelope"):
            self.delivered(release, evidence=evidence)
        with self.assertRaisesRegex(ContractError, "handoff"):
            self.delivered(release, status="label-created")

    def test_deliver_rejects_receipt_for_other_product_or_release(self):
        release = self.generated_release("hash-release")
        context = DeliverContext(self.wish, self.made, release)
        wrong_product = self.delivered(
            release, product_artifact_sha256="0" * 64
        )
        with self.assertRaisesRegex(
            ContractError, "different product or Release bytes"
        ):
            DefaultDeliver(lambda ignored: wrong_product)(context)
        wrong_release = self.delivered(
            release, release_sha256="1" * 64
        )
        with self.assertRaisesRegex(
            ContractError, "different product or Release bytes"
        ):
            DefaultDeliver(lambda ignored: wrong_release)(context)

    def test_deliver_accepts_receipts_for_exact_approved_bytes(self):
        release = self.generated_release("exact-release")
        context = DeliverContext(self.wish, self.made, release)
        receipt = self.delivered(release)
        result = DefaultDeliver(lambda observed: receipt)(context)
        self.assertIs(result, receipt)
        self.assertEqual(result.product_artifact_sha256, self.made.artifact_sha256)
        self.assertEqual(
            result.release_sha256, release.release_sha256
        )

    def test_delivery_rejects_truthy_legacy_placeholders_and_broken_chain(self):
        release = self.generated_release("strict-receipt-release")
        placeholders = {
            "print_receipt": {"passed": True},
            "qa_receipt": {"passed": True},
            "packing_receipt": {"passed": True},
            "carrier_receipt": {"passed": True},
        }
        with self.assertRaisesRegex(ContractError, "envelope"):
            self.delivered(release, evidence=placeholders)
        self._delivery_release_sha256 = release.release_sha256
        evidence = self.delivery_evidence()
        evidence["carrier_receipt"]["details"]["packing_receipt_sha256"] = "0" * 64
        # Recomputeing only the self-hash still cannot break cross-receipt binding.
        carrier = DeliveryEvidenceReceipt(
            stage="carrier",
            provider=evidence["carrier_receipt"]["provider"],
            provider_version=evidence["carrier_receipt"]["provider_version"],
            provider_config_sha256=evidence["carrier_receipt"]["provider_config_sha256"],
            receipt_id=evidence["carrier_receipt"]["receipt_id"],
            product_artifact_sha256=evidence["carrier_receipt"]["product_artifact_sha256"],
            release_sha256=evidence["carrier_receipt"]["release_sha256"],
            observed_at=evidence["carrier_receipt"]["observed_at"],
            details=evidence["carrier_receipt"]["details"],
        )
        evidence["carrier_receipt"] = carrier.to_dict()
        with self.assertRaisesRegex(ContractError, "exact sealed package"):
            self.delivered(release, evidence=evidence)

    def test_deliver_detects_release_tampering_before_calling_fulfiller(self):
        release = self.generated_release(
            "delivery-tamper-release"
        )
        context = DeliverContext(self.wish, self.made, release)
        (release.root / "product.json").write_text(
            "{}\n", encoding="utf-8"
        )
        calls = []

        def fulfiller(observed):
            calls.append(observed)
            return self.delivered(release)

        with self.assertRaisesRegex(ArtifactError, "bytes changed"):
            DefaultDeliver(fulfiller)(context)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
