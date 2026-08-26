import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.errors import ContractError, WorkshopError
from inventor_workshop.handoff import PublicationPolicy
from inventor_workshop.jobs import Need
from inventor_workshop.manager import discover_inventor_catalog
from inventor_workshop.make import Wish
from inventor_workshop.match_attempt import MatchAttemptEvent, MatchAttemptStore
from inventor_workshop.pending_wish import PendingWish, PendingWishStore
from tests import test_cli as cli_fixtures


class MatchAttemptStoreTest(unittest.TestCase):
    PRODUCT_ID = "wish-20260826-010203-cafefeed"

    @staticmethod
    def catalog(root: Path):
        cli_fixtures.CliTest.inventor_identity(
            root / "inventors" / "mira", "mira"
        )
        return discover_inventor_catalog(root)

    @classmethod
    def pending(cls, root: Path, *, publish: bool = False):
        catalog = cls.catalog(root)
        record = PendingWish.create(
            Wish.create(
                cls.PRODUCT_ID,
                "A patient clockwork moon that nods on my desk",
                context={"source": "workshop-cli"},
            ),
            PublicationPolicy.for_wish(publish=publish),
            catalog,
            playtest_rounds=4,
        )
        PendingWishStore(catalog.collection).save(record)
        return record

    @staticmethod
    def need():
        return Need(
            "wish",
            "semantic-inventor-retriever",
            "The semantic Manager returned no valid structured decision.",
            "Reconnect the exact Manager model and resume this Wish.",
        )

    def test_working_and_waiting_events_are_content_addressed_and_exact(self):
        with tempfile.TemporaryDirectory() as temporary:
            pending = self.pending(Path(temporary))
            store = MatchAttemptStore(pending.catalog_collection)
            working = store.begin(pending)
            waiting = store.record_waiting(working, (self.need(),))

            self.assertEqual(store.load(pending.wish.product_id), waiting)
            self.assertEqual(store.load_chain(pending.wish.product_id), (working, waiting))
            self.assertEqual(waiting.status, "waiting")
            self.assertEqual(waiting.needs, (self.need(),))
            self.assertEqual(waiting.previous_event_sha256, working.event_sha256)
            for event in (working, waiting):
                path = store.path / "objects" / (event.event_sha256 + ".json")
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    event.event_sha256,
                )
                self.assertEqual(path.read_bytes(), event.object_bytes())
                self.assertEqual(
                    MatchAttemptEvent.from_object_bytes(
                        path.read_bytes(), expected_sha256=event.event_sha256
                    ),
                    event,
                )

    def test_crashed_working_event_can_be_superseded_only_by_a_new_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            pending = self.pending(Path(temporary))
            store = MatchAttemptStore(pending.catalog_collection)
            crashed = store.begin(pending)
            retried = store.begin(pending)

            self.assertEqual(retried.status, "working")
            self.assertEqual(retried.attempt_number, 2)
            self.assertEqual(retried.event_sequence, 2)
            self.assertNotEqual(retried.attempt_id, crashed.attempt_id)
            self.assertEqual(retried.previous_event_sha256, crashed.event_sha256)
            with self.assertRaisesRegex(WorkshopError, "changed before append"):
                store.append(
                    crashed.waiting((self.need(),)),
                    expected_previous_sha256=crashed.event_sha256,
                )

    def test_publication_upgrade_starts_a_new_attempt_bound_to_new_pending_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            pending = self.pending(Path(temporary), publish=False)
            pending_store = PendingWishStore(pending.catalog_collection)
            attempts = MatchAttemptStore(pending.catalog_collection)
            first = attempts.begin(pending)
            waiting = attempts.record_waiting(first, (self.need(),))

            upgraded = pending.with_publication_policy(
                pending.publication_policy.authorize_public()
            )
            pending_store.replace(pending, upgraded)
            with self.assertRaisesRegex(
                WorkshopError, "PendingWish changed before"
            ):
                attempts.begin(pending)
            retried = attempts.begin(upgraded)

            self.assertNotEqual(pending.record_sha256, upgraded.record_sha256)
            self.assertEqual(retried.pending_wish_sha256, upgraded.record_sha256)
            self.assertEqual(retried.previous_event_sha256, waiting.event_sha256)
            self.assertEqual(attempts.load_chain(self.PRODUCT_ID)[-1], retried)

    def test_assignment_is_terminal_and_binds_the_sealed_handoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            pending = self.pending(Path(temporary))
            store = MatchAttemptStore(pending.catalog_collection)
            working = store.begin(pending)
            assigned = store.record_assigned(working, "a" * 64)

            self.assertEqual(assigned.status, "assigned")
            self.assertEqual(assigned.manager_handoff_sha256, "a" * 64)
            self.assertEqual(assigned.public_status()["manager_handoff_sha256"], "a" * 64)
            with self.assertRaisesRegex(ContractError, "assigned Match"):
                MatchAttemptEvent.start(pending, assigned)

    def test_missing_read_is_non_initializing(self):
        with tempfile.TemporaryDirectory() as temporary:
            pending = self.pending(Path(temporary))
            store = MatchAttemptStore(pending.catalog_collection)
            self.assertIsNone(store.load(self.PRODUCT_ID, allow_missing=True))
            self.assertFalse(store.path.exists())

    def test_tampered_object_index_and_cross_wish_transition_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            pending = self.pending(Path(temporary))
            store = MatchAttemptStore(pending.catalog_collection)
            working = store.begin(pending)
            object_path = store.path / "objects" / (working.event_sha256 + ".json")
            original = object_path.read_bytes()
            object_path.write_bytes(original[:-1] + b" ")
            object_path.chmod(0o600)
            with self.assertRaisesRegex(WorkshopError, "address|canonical"):
                store.load(self.PRODUCT_ID)

            object_path.write_bytes(original)
            object_path.chmod(0o600)
            index = store.path / "by-wish" / (
                hashlib.sha256(self.PRODUCT_ID.encode("utf-8")).hexdigest()
                + ".json"
            )
            payload = json.loads(index.read_text(encoding="utf-8"))
            payload["product_id"] = "another-wish"
            index.write_text(json.dumps(payload), encoding="utf-8")
            index.chmod(0o600)
            with self.assertRaisesRegex(WorkshopError, "identity|canonical"):
                store.load(self.PRODUCT_ID)

            index.write_bytes(
                store._index_bytes(self.PRODUCT_ID, working.event_sha256)
            )
            index.chmod(0o600)
            other = PendingWish(
                wish=Wish.create(
                    "wish-other",
                    pending.wish.objective,
                    context={"source": "workshop-cli"},
                ),
                publication_policy=pending.publication_policy,
                playtest_rounds=pending.playtest_rounds,
                catalog_collection=pending.catalog_collection,
                catalog_sha256=pending.catalog_sha256,
                catalog_total=pending.catalog_total,
                catalog_taste_sha256s=pending.catalog_taste_sha256s,
            )
            PendingWishStore(pending.catalog_collection).save(other)
            cross_wish = MatchAttemptEvent.start(other)
            with self.assertRaisesRegex(
                (ContractError, WorkshopError), "predecessor|another Wish|chain"
            ):
                store.append(
                    cross_wish,
                    expected_previous_sha256=working.event_sha256,
                )


if __name__ == "__main__":
    unittest.main()
