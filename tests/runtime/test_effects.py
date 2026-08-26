import json
import os
import sqlite3
import stat
import tempfile
import unittest
from pathlib import Path

from workshop.errors import AmbiguousEffectError, ContractError, ReceiptError, StateConflict
from workshop.runtime import EffectLedger, Receipt


SHA = "a" * 64
HANDOFF = "b" * 64
PRODUCT = "c" * 64
RELEASE = "d" * 64
PLAYTEST = "e" * 64
OBSERVED = "2026-08-26T00:00:00+00:00"


class EffectLedgerTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "private" / "factory-effects.sqlite3"
        self.ledger = EffectLedger(self.path)

    def tearDown(self):
        self.temporary.cleanup()

    def prepare(self, **changes):
        values = {
            "kind": "factory-import",
            "product_id": "orbit-dog",
            "request": {
                "method": "POST",
                "path": "/designs/import",
                "owner_id": "owner-alice",
                "metadata": {"title": "Orbit Dog"},
            },
            "pack_sha256": SHA,
            "handoff_artifact_sha256": HANDOFF,
            "product_artifact_sha256": PRODUCT,
            "release_sha256": RELEASE,
            "playtest_evidence_sha256": PLAYTEST,
        }
        values.update(changes)
        return self.ledger.prepare(**values)

    @staticmethod
    def receipt(intent, *, status="draft"):
        public = status == "public"
        return Receipt(
            payload_sha256=intent.pack_sha256,
            artifact_sha256=intent.product_artifact_sha256,
            adapter="factory",
            status=status,
            observed_at=OBSERVED,
            reference="design-one",
            details={
                "product_id": intent.product_id,
                "effect_request_sha256": intent.request_sha256,
                "effect_idempotency_key": intent.idempotency_key,
                "release_sha256": intent.release_sha256,
                "playtest_evidence_sha256": intent.playtest_evidence_sha256,
                "handoff_artifact_sha256": intent.handoff_artifact_sha256,
            },
            design_id="design-one",
            slug="orbit-dog",
            owner_id="owner-alice",
            root_id="design-one",
            current_history_id="history-one",
            published_history_id="history-one" if public else None,
            project_url="https://cdn.autonomous.ai/projects/orbit-dog/",
            listing_active=True if public else None,
            listing_price_cents=2400 if public else None,
            listing_currency="USD" if public else None,
            listing_sku="ORBIT-DOG" if public else None,
        )

    def test_database_and_parent_are_private(self):
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.path.parent.stat().st_mode), 0o700)

    def test_prepare_binds_all_hashes_and_has_stable_idempotency_key(self):
        first = self.prepare()
        replay = self.prepare()
        self.assertEqual(first, replay)
        self.assertEqual(first.state, "planned")
        self.assertEqual(len(first.request_sha256), 64)
        self.assertEqual(first.intent_id, first.idempotency_key.rsplit("-", 1)[-1])
        self.assertEqual(first.handoff_artifact_sha256, HANDOFF)
        self.assertEqual(first.product_artifact_sha256, PRODUCT)
        self.assertEqual(first.release_sha256, RELEASE)

    def test_request_or_byte_drift_cannot_replace_an_active_intent(self):
        self.prepare()
        with self.assertRaises(StateConflict):
            self.prepare(request={"method": "POST", "path": "/other"})
        with self.assertRaises(StateConflict):
            self.prepare(pack_sha256="f" * 64)

    def test_intent_is_recorded_before_send_and_token_fences_completion(self):
        planned = self.prepare()
        self.assertEqual(self.ledger.get(planned.intent_id).state, "planned")
        sending = self.ledger.begin(planned.intent_id)
        self.assertEqual(sending.state, "sending")
        with self.assertRaises(StateConflict):
            self.ledger.mark_succeeded(
                sending.intent_id,
                "stale-token",
                self.receipt(sending),
                {"id": "design-one"},
            )
        completed = self.ledger.mark_succeeded(
            sending.intent_id,
            sending.effect_token,
            self.receipt(sending),
            {"id": "design-one"},
        )
        self.assertEqual(completed.state, "succeeded")
        self.assertEqual(self.ledger.begin(completed.intent_id), completed)

    def test_unknown_and_crash_stranded_effects_never_reopen(self):
        sending = self.ledger.begin(self.prepare().intent_id)
        unknown = self.ledger.strand_as_unknown(
            sending.intent_id, "host exited\nduring send\x7f"
        )
        self.assertEqual(unknown.state, "unknown")
        self.assertEqual(unknown.error, "host exited during send")
        with self.assertRaises(AmbiguousEffectError):
            self.ledger.begin(unknown.intent_id)
        with self.assertRaises(AmbiguousEffectError):
            self.prepare(pack_sha256="f" * 64)

    def test_authenticated_reconciliation_can_resolve_unknown_success(self):
        sending = self.ledger.begin(self.prepare().intent_id)
        unknown = self.ledger.mark_unknown(
            sending.intent_id,
            sending.effect_token,
            "GET unavailable",
            response={"id": "design-one", "slug": "orbit-dog"},
        )
        receipt = self.receipt(unknown)
        completed = self.ledger.resolve_succeeded(
            unknown.intent_id, receipt, {"id": "design-one"}
        )
        self.assertEqual(completed.state, "succeeded")
        self.assertEqual(completed.receipt, receipt)

    def test_proven_rejection_can_retry_exact_request_or_corrected_bytes(self):
        sending = self.ledger.begin(self.prepare().intent_id)
        rejected = self.ledger.mark_rejected(
            sending.intent_id, sending.effect_token, "HTTP 422"
        )
        self.assertEqual(rejected.state, "rejected")
        retry = self.prepare()
        self.assertEqual(retry.state, "planned")
        self.assertEqual(retry.intent_id, rejected.intent_id)
        self.assertIsNone(retry.error)
        self.assertIsNone(retry.response)
        retry_sending = self.ledger.begin(retry.intent_id)
        self.ledger.mark_rejected(
            retry_sending.intent_id, retry_sending.effect_token, "HTTP 422 again"
        )
        corrected = self.prepare(pack_sha256="f" * 64)
        self.assertEqual(corrected.state, "planned")
        self.assertNotEqual(corrected.intent_id, retry.intent_id)

    def test_receipt_must_bind_every_effect_identity(self):
        sending = self.ledger.begin(self.prepare().intent_id)
        value = self.receipt(sending).to_dict()
        value["details"]["release_sha256"] = "f" * 64
        with self.assertRaises(ReceiptError):
            self.ledger.mark_succeeded(
                sending.intent_id,
                sending.effect_token,
                Receipt.from_dict(value),
                {"id": "design-one"},
            )

    def test_non_native_database_is_refused_without_migration(self):
        other = Path(self.temporary.name) / "old.sqlite3"
        connection = sqlite3.connect(other)
        connection.execute("CREATE TABLE products(id TEXT PRIMARY KEY)")
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(ContractError, "native Factory effect schema"):
            EffectLedger(other)


if __name__ == "__main__":
    unittest.main()
