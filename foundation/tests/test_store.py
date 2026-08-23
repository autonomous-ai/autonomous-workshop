import os
import sqlite3
import stat
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from inventor_core.errors import (
    AmbiguousPublishError,
    BudgetExceeded,
    ContractError,
    LeaseBusy,
    ReceiptError,
    StateConflict,
)
from inventor_core.models import PublicationReceipt
from inventor_core.store import InventorStore

SHA = "a" * 64


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = InventorStore(Path(self.temp.name) / "state.sqlite")
        self.store.register_product("game", "idea", {"title": "Game"}, SHA)

    def receipt(self, status="draft"):
        return PublicationReceipt(
            packet_sha256=SHA,
            artifact_sha256=SHA,
            design_id="d1",
            slug="game",
            owner_id="alice-owner",
            root_id="d1",
            current_history_id="h1",
            published_history_id="h1" if status == "public" else None,
            status=status,
            project_url="https://cdn.example/game/",
            observed_at="2026-08-23T00:00:00+00:00",
            listing_active=True if status == "public" else None,
            listing_price_cents=4000 if status == "public" else None,
            listing_currency="USD" if status == "public" else None,
            listing_sku="GAME-001" if status == "public" else None,
        )

    def publish_request(self, **metadata):
        return {
            "status": "draft",
            "_core_artifact_sha256": SHA,
            "_core_owner_id": "alice-owner",
            "_core_api_origin": "https://panda-social-api.autonomous.ai",
            **metadata,
        }

    def test_revision_fence_and_hash_chain(self):
        product = self.store._transition("game", "idea", "rules", 0, SHA, {"why": "ok"})
        self.assertEqual(product["revision"], 1)
        self.assertTrue(self.store.verify_event_chain("game"))
        with self.assertRaises(StateConflict):
            self.store._transition("game", "idea", "built", 0, SHA)
        self.assertEqual(
            [product["id"] for product in self.store.list_products("rules")],
            ["game"],
        )

    def test_lease_uses_unforgeable_fencing_token(self):
        token = self.store.acquire_lease("game", "worker-a")
        with self.assertRaises(LeaseBusy):
            self.store.acquire_lease("game", "worker-b")
        with self.assertRaises(LeaseBusy):
            self.store._transition("game", "idea", "rules", 0, SHA)
        with self.assertRaises(LeaseBusy):
            self.store._transition("game", "idea", "rules", 0, SHA, lease_token="wrong")
        product = self.store._transition(
            "game", "idea", "rules", 0, SHA, lease_token=token
        )
        self.assertEqual(product["stage"], "rules")
        self.assertTrue(self.store.renew_lease("game", token))
        self.assertFalse(self.store.release_lease("game", "wrong"))
        self.assertTrue(self.store.release_lease("game", token))
        with self.assertRaises(StateConflict):
            self.store._transition("game", "rules", "built", 1, SHA, lease_token=token)

    def test_lease_ttl_is_typed_and_bounded(self):
        for ttl in (True, 0, -1, 24 * 60 * 60 + 1):
            with self.subTest(ttl=ttl), self.assertRaises(ContractError):
                self.store.acquire_lease("game", "worker", ttl)

    def test_expired_worker_cannot_mutate_after_replacement_claim(self):
        stale = self.store.acquire_lease("game", "worker-a")
        with closing(sqlite3.connect(str(self.store.path))) as connection:
            connection.execute(
                "UPDATE leases SET expires_at='2000-01-01T00:00:00+00:00' WHERE product_id='game'"
            )
            connection.commit()
        current = self.store.acquire_lease("game", "worker-b")
        self.assertNotEqual(stale, current)
        with self.assertRaises(LeaseBusy):
            self.store._transition(
                "game", "idea", "rules", 0, SHA, lease_token=stale
            )
        product = self.store._transition(
            "game", "idea", "rules", 0, SHA, lease_token=current
        )
        self.assertEqual(product["stage"], "rules")

    def test_event_audit_reconciles_chain_to_product_row(self):
        self.assertTrue(self.store.verify_event_chain("game"))
        with closing(sqlite3.connect(str(self.store.path))) as connection:
            connection.execute(
                "UPDATE products SET stage='live', revision=99 WHERE id='game'"
            )
            connection.commit()
        self.assertFalse(self.store.verify_event_chain("game"))
        with closing(sqlite3.connect(str(self.store.path))) as connection:
            connection.execute("DELETE FROM events WHERE product_id='game'")
            connection.commit()
        self.assertFalse(self.store.verify_event_chain("game"))
        with self.assertRaises(KeyError):
            self.store.verify_event_chain("typo")

    def test_event_audit_reports_malformed_json_as_invalid(self):
        with closing(sqlite3.connect(str(self.store.path))) as connection:
            connection.execute(
                "UPDATE events SET payload_json='not-json' WHERE product_id='game'"
            )
            connection.commit()
        self.assertFalse(self.store.verify_event_chain("game"))

    @unittest.skipIf(os.name == "nt", "POSIX permissions")
    def test_database_and_wal_are_private(self):
        self.store.get_product("game")
        self.assertEqual(stat.S_IMODE(self.store.path.stat().st_mode), 0o600)
        for suffix in ("-wal", "-shm"):
            candidate = Path(str(self.store.path) + suffix)
            if candidate.exists():
                self.assertEqual(stat.S_IMODE(candidate.stat().st_mode), 0o600)

    def test_future_schema_is_rejected_before_core_mutates_it(self):
        database = Path(self.temp.name) / "future.sqlite"
        with closing(sqlite3.connect(str(database))) as connection:
            connection.execute(
                "CREATE TABLE core_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            connection.execute(
                "INSERT INTO core_meta(key, value) VALUES ('schema_version', '999')"
            )
            connection.execute("CREATE TABLE future_only (value TEXT)")
            connection.commit()
        with self.assertRaises(ContractError):
            InventorStore(database)
        with closing(sqlite3.connect(str(database))) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        self.assertEqual(tables, {"core_meta", "future_only"})

    def test_budget_is_enforced_in_same_transaction(self):
        now = datetime.now(timezone.utc)
        starts = (now - timedelta(days=1)).isoformat()
        ends = (now + timedelta(days=1)).isoformat()
        self.store.configure_budget("daily", 1_000, starts, ends)
        remaining = self.store.spend(
            "daily", "game:research:1", 400, "research", "game"
        )
        self.assertEqual(remaining, 600)
        status = self.store.budget_status("daily")
        self.assertTrue(status["active"])
        self.assertEqual(status["used_micros"], 400)
        self.assertEqual(status["remaining_micros"], 600)
        self.assertEqual(
            self.store.spend(
                "daily", "game:research:1", 400, "research", "game"
            ),
            600,
        )
        with self.assertRaises(BudgetExceeded):
            self.store.spend(
                "daily", "game:build:1", 700, "build", "game"
            )
        with self.assertRaises(StateConflict):
            self.store.spend(
                "daily", "game:research:1", 401, "research", "game"
            )

    def test_budget_clock_cannot_be_spoofed_and_active_lease_is_fenced(self):
        now = datetime.now(timezone.utc)
        self.store.configure_budget(
            "expired",
            1_000,
            (now - timedelta(days=2)).isoformat(),
            (now - timedelta(days=1)).isoformat(),
        )
        with self.assertRaises(BudgetExceeded):
            self.store.spend("expired", "past:1", 1, "research", "game")

        self.store.configure_budget(
            "active",
            1_000,
            (now - timedelta(days=1)).isoformat(),
            (now + timedelta(days=1)).isoformat(),
        )
        token = self.store.acquire_lease("game", "worker")
        with self.assertRaises(LeaseBusy):
            self.store.spend("active", "game:1", 1, "research", "game")
        self.assertEqual(
            self.store.spend(
                "active", "game:1", 1, "research", "game", lease_token=token
            ),
            999,
        )

    def test_budget_policy_and_idempotent_result_are_immutable(self):
        starts = "2026-01-01T00:00:00+00:00"
        ends = "2026-01-02T00:00:00+00:00"
        with mock.patch(
            "inventor_core.store.utc_now",
            return_value="2026-01-01T12:00:00+00:00",
        ):
            first = self.store.configure_budget("window", 1_000, starts, ends)
            same = self.store.configure_budget("window", 1_000, starts, ends)
            self.assertEqual(first, same)
            with self.assertRaises(StateConflict):
                self.store.configure_budget("window", 2_000, starts, ends)
            self.assertEqual(
                self.store.spend("window", "window:1", 400, "research", "game"),
                600,
            )
        with mock.patch(
            "inventor_core.store.utc_now",
            return_value="2026-01-03T00:00:00+00:00",
        ):
            self.assertEqual(
                self.store.spend("window", "window:1", 400, "research", "game"),
                600,
            )
            replacement = self.store.configure_budget(
                "window",
                2_000,
                "2026-01-03T00:00:00+00:00",
                "2026-01-04T00:00:00+00:00",
            )
            self.assertEqual(replacement["limit_micros"], 2_000)

    def test_ambiguous_import_cannot_blind_retry(self):
        intent = self.store.prepare_publish("game", SHA, self.publish_request())
        sending = self.store.begin_publish(intent["id"])
        self.store.mark_publish_unknown(
            intent["id"], sending["effect_token"], "socket closed"
        )
        with self.assertRaises(AmbiguousPublishError):
            self.store.begin_publish(intent["id"])
        with self.assertRaises(AmbiguousPublishError):
            self.store.resolve_publish_unknown(
                intent["id"], self.receipt(), "caller-authored receipt"
            )

    def test_publish_intent_rejects_request_drift_and_parallel_packet(self):
        self.assertIsNone(self.store.latest_publish_intent("game"))
        intent = self.store.prepare_publish(
            "game", SHA, self.publish_request(title="Original")
        )
        self.assertEqual(
            self.store.latest_publish_intent("game")["id"], intent["id"]
        )
        with self.assertRaises(StateConflict):
            self.store.prepare_publish(
                "game", SHA, self.publish_request(title="Substituted")
            )
        with self.assertRaises(StateConflict):
            self.store.prepare_publish(
                "game", "b" * 64, self.publish_request(title="Other packet")
            )
        self.store.begin_publish(intent["id"])
        recovered = self.store.recover_stranded_intent(intent["id"], "worker crashed")
        self.assertEqual(recovered["state"], "unknown")

    def test_latest_publish_intent_validates_product_identity(self):
        self.assertIsNone(self.store.latest_publish_intent("not-registered"))
        with self.assertRaises(ContractError):
            self.store.latest_publish_intent("unsafe\nproduct")

    def test_live_effect_is_fenced_and_receipt_gated(self):
        intent = self.store.prepare_publish("game", SHA, self.publish_request())
        sending = self.store.begin_publish(intent["id"])
        self.store.mark_publish_succeeded(
            intent["id"], sending["effect_token"], self.receipt()
        )
        publishing = self.store.begin_live(
            intent["id"],
            {
                "api_origin": "https://panda-social-api.autonomous.ai",
                "owner_id": "alice-owner",
                "listing": {"price_cents": 4000},
            },
        )
        self.assertEqual(publishing["live_request"]["listing"]["price_cents"], 4000)
        live = self.store.mark_publish_live(
            intent["id"], publishing["effect_token"], self.receipt("public")
        )
        self.assertEqual(live["state"], "live")

    def test_low_level_receipt_writes_enforce_owner_artifact_and_history(self):
        intent = self.store.prepare_publish("game", SHA, self.publish_request())
        sending = self.store.begin_publish(intent["id"])
        forged = PublicationReceipt(
            **{
                **self.receipt().to_dict(),
                "artifact_sha256": "b" * 64,
                "owner_id": "other-owner",
            }
        )
        with self.assertRaises(ReceiptError):
            self.store.mark_publish_succeeded(
                intent["id"], sending["effect_token"], forged
            )
        self.store.mark_publish_succeeded(
            intent["id"], sending["effect_token"], self.receipt()
        )
        publishing = self.store.begin_live(
            intent["id"],
            {
                "api_origin": "https://panda-social-api.autonomous.ai",
                "owner_id": "alice-owner",
                "listing": {"price_cents": 4000},
            },
        )
        unrelated = PublicationReceipt(
            **{
                **self.receipt("public").to_dict(),
                "design_id": "different-design",
            }
        )
        with self.assertRaises(ReceiptError):
            self.store.mark_publish_live(
                intent["id"], publishing["effect_token"], unrelated
            )

    def test_stale_effect_completion_cannot_overwrite_a_corrected_live_attempt(self):
        intent = self.store.prepare_publish("game", SHA, self.publish_request())
        sending = self.store.begin_publish(intent["id"])
        self.store.mark_publish_succeeded(
            intent["id"], sending["effect_token"], self.receipt()
        )
        request = {
            "api_origin": "https://panda-social-api.autonomous.ai",
            "owner_id": "alice-owner",
            "listing": {"price_cents": 4000},
        }
        first = self.store.begin_live(intent["id"], request)
        self.store.restore_draft_after_publish_rejection(
            intent["id"], first["effect_token"], "HTTP 422"
        )
        request["listing"]["price_cents"] = 4500
        second = self.store.begin_live(intent["id"], request)
        self.assertNotEqual(first["effect_token"], second["effect_token"])
        with self.assertRaises(StateConflict):
            self.store.mark_live_unknown(
                intent["id"], first["effect_token"], "late stale completion"
            )


if __name__ == "__main__":
    unittest.main()
