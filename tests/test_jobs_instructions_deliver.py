import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.deliver import DefaultDeliver
from inventor_workshop.instructions import (
    DefaultInstructions,
    REQUIRED_PRODUCT_IMAGES,
)
from inventor_workshop.errors import ArtifactError, ContractError
from inventor_workshop.jobs import (
    DeliverContext,
    Delivered,
    InstructionsContext,
    Made,
    Need,
    Playtested,
    ProductInstructions,
    WaitingFor,
)
from inventor_workshop.make import Wish
from inventor_workshop.models import PlaytestResult, Receipt
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

    def instructions_context(
        self, name: str = "instructions"
    ) -> InstructionsContext:
        return InstructionsContext(
            self.wish,
            self.taste,
            self.blueprint,
            self.made,
            self.playtested,
            self.root / name,
        )

    @staticmethod
    def media_maker(context: InstructionsContext):
        images = context.workspace / "images"
        images.mkdir(parents=True)
        paths = {}
        for role in REQUIRED_PRODUCT_IMAGES:
            path = images / (role + ".png")
            path.write_bytes(("fake PNG for %s\n" % role).encode("utf-8"))
            paths[role] = path.relative_to(context.workspace).as_posix()
        return paths

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
            published_history_id="history-1",
            status="public",
            project_url="https://www.autonomous.ai/factory/product/pocket-duel",
            observed_at="2026-08-23T12:00:00+00:00",
            listing_active=True,
            listing_price_cents=3500,
            listing_currency="USD",
            listing_sku="PD-001",
            details={"instructions_sha256": sealed_manifest.artifact_sha256},
        )

    def generated_instructions(
        self, name: str = "instructions"
    ) -> ProductInstructions:
        return DefaultInstructions(self.media_maker, self.site_writer)(
            self.instructions_context(name)
        )

    def delivery_evidence(self):
        return {
            "print_receipt": {"job_id": "print-1", "passed": True},
            "qa_receipt": {"job_id": "qa-1", "passed": True},
            "packing_receipt": {"box_id": "box-1", "passed": True},
            "carrier_receipt": {"acceptance_scan": "scan-1", "passed": True},
        }

    def delivered(
        self, instructions: ProductInstructions, **changes
    ) -> Delivered:
        values = {
            "product_artifact_sha256": self.made.artifact_sha256,
            "instructions_sha256": instructions.instructions_sha256,
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

    def test_instructions_reject_failed_playtest(self):
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
            InstructionsContext(
                self.wish,
                self.taste,
                self.blueprint,
                self.made,
                playtested,
                self.root / "failed-instructions",
            )

    def test_instructions_reject_playtest_for_different_product(self):
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
            InstructionsContext(
                self.wish,
                self.taste,
                self.blueprint,
                other,
                self.playtested,
                self.root / "detached-instructions",
            )


class InstructionsJobTest(WorkshopJobFixture):
    def test_instructions_wait_truthfully_when_no_media_provider_exists(self):
        context = self.instructions_context("waiting-instructions")
        with self.assertRaises(WaitingFor) as raised:
            DefaultInstructions()(context)
        self.assertEqual(len(raised.exception.needs), 2)
        self.assertTrue(all(isinstance(need, Need) for need in raised.exception.needs))
        self.assertEqual(
            {need.capability for need in raised.exception.needs},
            {"product-images", "site-page"},
        )
        self.assertFalse(context.workspace.exists())

    def test_instructions_wait_when_images_exist_but_site_access_is_missing(self):
        context = self.instructions_context("site-waiting-instructions")
        with self.assertRaises(WaitingFor) as raised:
            DefaultInstructions(self.media_maker)(context)
        self.assertEqual(
            [(need.job, need.capability) for need in raised.exception.needs],
            [("instructions", "site-page")],
        )
        self.assertFalse(context.workspace.exists())

    def test_instructions_reject_site_receipt_for_unverified_or_different_bytes(self):
        def unverified(context, sealed_root, sealed_manifest):
            del sealed_root
            receipt = self.site_writer(context, None, sealed_manifest)
            value = receipt.to_dict()
            value["status"] = "draft"
            value["published_history_id"] = None
            value["listing_active"] = None
            value["listing_price_cents"] = None
            value["listing_currency"] = None
            value["listing_sku"] = None
            return Receipt.from_dict(value)

        with self.assertRaisesRegex(ContractError, "authenticated public"):
            DefaultInstructions(self.media_maker, unverified)(
                self.instructions_context("unverified-site-instructions")
            )

        def wrong_page(context, sealed_root, sealed_manifest):
            del sealed_root
            receipt = self.site_writer(context, None, sealed_manifest)
            value = receipt.to_dict()
            value["details"] = {"instructions_sha256": "0" * 64}
            return Receipt.from_dict(value)

        with self.assertRaisesRegex(ContractError, "different page"):
            DefaultInstructions(self.media_maker, wrong_page)(
                self.instructions_context("wrong-site-instructions")
            )

    def test_instructions_require_every_fixed_image_role(self):
        def incomplete(context):
            media = self.media_maker(context)
            del media["box"]
            return media

        with self.assertRaisesRegex(ContractError, "box"):
            DefaultInstructions(incomplete, self.site_writer)(
                self.instructions_context("incomplete-instructions")
            )

    def test_instructions_reject_one_file_claimed_as_every_fixed_view(self):
        def repeated(context):
            path = context.workspace / "one.png"
            path.write_bytes(b"not five distinct views")
            return {role: "one.png" for role in REQUIRED_PRODUCT_IMAGES}

        with self.assertRaisesRegex(ContractError, "distinct"):
            DefaultInstructions(repeated, self.site_writer)(
                self.instructions_context("repeated-instructions")
            )

    def test_instructions_reject_media_outside_workspace(self):
        outside = self.root / "outside.png"
        outside.write_bytes(b"outside")

        def escaped(context):
            media = self.media_maker(context)
            media["hero"] = "../outside.png"
            return media

        with self.assertRaisesRegex(ContractError, "stay inside"):
            DefaultInstructions(escaped, self.site_writer)(
                self.instructions_context("escaped-instructions")
            )

    def test_instructions_output_is_box_ready_and_page_preserves_provenance(self):
        instructions = self.generated_instructions("complete-instructions")
        page = json.loads(
            (instructions.root / "product.json").read_text(encoding="utf-8")
        )
        self.assertEqual(page["status"], "ready")
        self.assertEqual(
            page["summary"],
            "A tiny bluffing game with a satisfying reveal.\n\nBy Alice.",
        )
        self.assertEqual(page["instructions_kind"], "rulebook")
        self.assertEqual(page["how_to_play"], "Choose, commit, and reveal.")
        self.assertNotIn("how_to_use", page)
        self.assertEqual(set(page["images"]), set(REQUIRED_PRODUCT_IMAGES))
        self.assertEqual(page["product_artifact_sha256"], self.made.artifact_sha256)
        claim = page["claims"]["gameplay-league"]
        result = self.playtested.evidence.results[0]
        self.assertEqual(claim["evidence_class"], "ai-simulation")
        self.assertEqual(claim["evidence_ref"], result.evidence_ref)
        self.assertEqual(claim["evidence_sha256"], result.evidence_sha256)
        self.assertIn("simulated", claim["claims"][0])
        self.assertNotIn("human", claim["claims"][0].casefold())
        self.assertEqual(instructions.claims, page["claims"])
        self.assertEqual(instructions.instructions_path, "INSTRUCTIONS.md")
        self.assertTrue(instructions.site_receipt.is_verified_public)
        self.assertEqual(
            instructions.page_url,
            "https://www.autonomous.ai/factory/product/pocket-duel",
        )
        insert = (instructions.root / instructions.instructions_path).read_text(
            encoding="utf-8"
        )
        self.assertIn("## How to play", insert)
        self.assertIn("## What's in the box", insert)
        self.assertIn("## Care and safety", insert)
        self.assertIn("\n\nBy Alice.\n\n## How to play", insert)
        self.assertEqual(insert.count("By Alice."), 1)
        self.assertFalse(insert.endswith(" \n"))
        self.assertFalse((instructions.root / "README.md").exists())

    def test_non_game_output_uses_instructions_and_how_to_use(self):
        moving_made = Made.from_root(
            self.product_root,
            {
                **self.made.product,
                "lane": "moving-machines",
                "instructions": "Turn the crank clockwise and watch the rhythm.",
            },
        )
        context = InstructionsContext(
            self.wish,
            self.taste,
            ToyBlueprint.for_lane("moving-machines"),
            moving_made,
            self.playtested,
            self.root / "moving-machine-instructions",
        )
        instructions = DefaultInstructions(self.media_maker, self.site_writer)(context)
        page = json.loads(
            (instructions.root / "product.json").read_text(encoding="utf-8")
        )
        self.assertEqual(page["instructions_kind"], "instructions")
        self.assertEqual(
            page["how_to_use"],
            "Turn the crank clockwise and watch the rhythm.",
        )
        self.assertNotIn("how_to_play", page)
        insert = (instructions.root / "INSTRUCTIONS.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## How to use", insert)
        self.assertNotIn("## How to play", insert)

    def test_instructions_detect_changed_bytes_after_generation(self):
        instructions = self.generated_instructions("tampered-instructions")
        (instructions.root / "INSTRUCTIONS.md").write_text(
            "changed after approval\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ArtifactError, "bytes changed"):
            instructions.assert_current()

    def test_instructions_detect_product_tampering_before_calling_media_provider(self):
        context = self.instructions_context("product-tamper-instructions")
        (self.product_root / "rules.md").write_text("changed\n", encoding="utf-8")
        calls = []

        def media(observed):
            calls.append(observed)
            return self.media_maker(observed)

        with self.assertRaisesRegex(ArtifactError, "bytes changed"):
            DefaultInstructions(media, self.site_writer)(context)
        self.assertEqual(calls, [])


class DeliverJobTest(WorkshopJobFixture):
    def test_deliver_waits_truthfully_without_real_fulfiller(self):
        instructions = self.generated_instructions("waiting-delivery-instructions")
        context = DeliverContext(self.wish, self.made, instructions)
        with self.assertRaises(WaitingFor) as raised:
            DefaultDeliver()(context)
        need = raised.exception.needs[0]
        self.assertEqual(
            (need.job, need.capability), ("deliver", "production-and-shipping")
        )

    def test_delivery_requires_supported_carrier_and_all_receipts(self):
        instructions = self.generated_instructions("receipt-instructions")
        with self.assertRaisesRegex(ContractError, "USPS, UPS, or FedEx"):
            self.delivered(instructions, carrier="DHL")
        evidence = self.delivery_evidence()
        del evidence["qa_receipt"]
        with self.assertRaisesRegex(ContractError, "qa_receipt"):
            self.delivered(instructions, evidence=evidence)
        evidence = self.delivery_evidence()
        evidence["packing_receipt"] = {}
        with self.assertRaisesRegex(ContractError, "packing_receipt"):
            self.delivered(instructions, evidence=evidence)
        with self.assertRaisesRegex(ContractError, "handed-off or delivered"):
            self.delivered(instructions, status="label-created")

    def test_deliver_rejects_receipt_for_other_product_or_instructions(self):
        instructions = self.generated_instructions("hash-instructions")
        context = DeliverContext(self.wish, self.made, instructions)
        wrong_product = self.delivered(
            instructions, product_artifact_sha256="0" * 64
        )
        with self.assertRaisesRegex(
            ContractError, "different product or Instructions bytes"
        ):
            DefaultDeliver(lambda ignored: wrong_product)(context)
        wrong_instructions = self.delivered(
            instructions, instructions_sha256="1" * 64
        )
        with self.assertRaisesRegex(
            ContractError, "different product or Instructions bytes"
        ):
            DefaultDeliver(lambda ignored: wrong_instructions)(context)

    def test_deliver_accepts_receipts_for_exact_approved_bytes(self):
        instructions = self.generated_instructions("exact-instructions")
        context = DeliverContext(self.wish, self.made, instructions)
        receipt = self.delivered(instructions)
        result = DefaultDeliver(lambda observed: receipt)(context)
        self.assertIs(result, receipt)
        self.assertEqual(result.product_artifact_sha256, self.made.artifact_sha256)
        self.assertEqual(
            result.instructions_sha256, instructions.instructions_sha256
        )

    def test_deliver_detects_instructions_tampering_before_calling_fulfiller(self):
        instructions = self.generated_instructions(
            "delivery-tamper-instructions"
        )
        context = DeliverContext(self.wish, self.made, instructions)
        (instructions.root / "product.json").write_text(
            "{}\n", encoding="utf-8"
        )
        calls = []

        def fulfiller(observed):
            calls.append(observed)
            return self.delivered(instructions)

        with self.assertRaisesRegex(ArtifactError, "bytes changed"):
            DefaultDeliver(fulfiller)(context)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
