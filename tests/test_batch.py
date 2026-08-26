import hashlib
import json
import os
import stat
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from inventor_workshop.batch import (
    MAX_BATCH_INPUT_BYTES,
    BatchPlan,
    BatchPlanStore,
    BatchRequest,
    generate_batch_id,
    load_or_create_batch_manager_identity,
    parse_batch_file,
    parse_batch_input,
)
from inventor_workshop.errors import ContractError, WorkshopError
from inventor_workshop.handoff import PublicationPolicy
from inventor_workshop.manager import discover_inventor_catalog
from inventor_workshop.make import Wish
from inventor_workshop.pending_wish import PendingWish, PendingWishStore
from inventor_workshop.taste import load_taste
from tests import test_cli as cli_fixtures


class BatchFixture(unittest.TestCase):
    @staticmethod
    def catalog(root: Path):
        cli_fixtures.CliTest.inventor_identity(
            root / "inventors" / "mira", "mira"
        )
        cli_fixtures.CliTest.inventor_identity(
            root / "inventors" / "taro", "taro"
        )
        return discover_inventor_catalog(root)

    @staticmethod
    def entries(*, suffix: str = ""):
        return (
            (
                Wish.create(
                    "wish-batch-one" + suffix,
                    "A patient clockwork moon",
                    context={"source": "workshop-batch", "batch_key": "one"},
                ),
                PublicationPolicy.for_wish(publish=False),
            ),
            (
                Wish.create(
                    "wish-batch-two" + suffix,
                    "A lighthouse game for two rivals",
                    context={"source": "workshop-batch", "batch_key": "two"},
                ),
                PublicationPolicy.for_wish(publish=True),
            ),
            (
                Wish.create(
                    "wish-batch-three" + suffix,
                    "A tiny walking observatory",
                    context={"source": "workshop-batch", "batch_key": "three"},
                ),
                PublicationPolicy.for_wish(publish=False),
            ),
        )

    @classmethod
    def plan(cls, root: Path, *, batch_id: str = "batch-fixture"):
        catalog = cls.catalog(root)
        return BatchPlan.create(
            batch_id,
            catalog,
            cls.entries(),
            playtest_rounds=4,
        )


class BatchInputTest(unittest.TestCase):
    def test_lines_are_ordered_bounded_and_require_explicit_visibility(self):
        requests = parse_batch_input(
            b"first Wish\r\nsecond Wish\r\n",
            input_format="lines",
            default_visibility="draft",
        )

        self.assertEqual(
            requests,
            (
                BatchRequest("line-0001", "first Wish", "draft"),
                BatchRequest("line-0002", "second Wish", "draft"),
            ),
        )
        with self.assertRaisesRegex(ContractError, "explicit visibility"):
            parse_batch_input(b"one\n", input_format="lines")
        with self.assertRaisesRegex(ContractError, "repeated normalized"):
            parse_batch_input(
                "Moon  Toy\nmoon toy\n".encode("utf-8"),
                input_format="lines",
                default_visibility="draft",
            )

    def test_jsonl_is_strict_unique_and_can_bind_mass_visibility(self):
        source = b"\n".join(
            (
                b'{"key":"alpha","wish":"first Wish","visibility":"public"}',
                b'{"key":"beta","wish":"second Wish","visibility":"public"}',
            )
        )
        requests = parse_batch_input(
            source,
            input_format="jsonl",
            default_visibility="public",
        )

        self.assertEqual(tuple(item.key for item in requests), ("alpha", "beta"))
        self.assertTrue(all(item.visibility == "public" for item in requests))

        invalid = (
            (
                b'{"key":"a","key":"b","wish":"x","visibility":"draft"}',
                "strict JSON",
            ),
            (b'{"key":"a","wish":"x"}', "exactly"),
            (
                b'{"key":"a","wish":"x","visibility":"private"}',
                "draft or public",
            ),
            (
                b'{"key":"a","wish":"x","visibility":NaN}',
                "strict JSON",
            ),
            (
                b'{"key":"same","wish":"x","visibility":"draft"}\n'
                b'{"key":"same","wish":"y","visibility":"draft"}',
                "unique",
            ),
        )
        for value, message in invalid:
            with self.subTest(value=value), self.assertRaisesRegex(
                ContractError, message
            ):
                parse_batch_input(value, input_format="jsonl")

        with self.assertRaisesRegex(ContractError, "conflicts"):
            parse_batch_input(
                source,
                input_format="jsonl",
                default_visibility="draft",
            )

    def test_blank_invalid_utf8_record_count_and_byte_bounds_fail_closed(self):
        invalid = (
            (b"", "1 to"),
            (b"one\n\ntwo", "blank"),
            (b"one\rtwo", "LF or CRLF"),
            (b"\xff", "UTF-8"),
            (b"\xef\xbb\xbfwish", "byte-order mark"),
            (b"\n", "blank"),
            (b"wish\n" * 1_001, "more than 1000"),
            (b"x" * (MAX_BATCH_INPUT_BYTES + 1), "1 to"),
        )
        for source, message in invalid:
            with self.subTest(message=message), self.assertRaisesRegex(
                ContractError, message
            ):
                parse_batch_input(
                    source,
                    input_format="lines",
                    default_visibility="draft",
                )

    def test_file_reader_does_not_follow_final_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "wishes.txt"
            source.write_text("one\ntwo\n", encoding="utf-8")
            self.assertEqual(
                len(
                    parse_batch_file(
                        source,
                        input_format="lines",
                        default_visibility="draft",
                    )
                ),
                2,
            )
            link = root / "linked.txt"
            link.symlink_to(source)
            with self.assertRaisesRegex(WorkshopError, "safely open"):
                parse_batch_file(
                    link,
                    input_format="lines",
                    default_visibility="draft",
                )

            if hasattr(os, "mkfifo"):
                fifo = root / "wishes.fifo"
                os.mkfifo(fifo)
                started = time.monotonic()
                with self.assertRaisesRegex(WorkshopError, "regular file"):
                    parse_batch_file(
                        fifo,
                        input_format="lines",
                        default_visibility="draft",
                    )
                self.assertLess(time.monotonic() - started, 1)


class BatchPlanTest(BatchFixture):
    def test_requests_allocate_stable_opaque_ids_and_exact_resubmission(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = self.catalog(root)
            requests = (
                BatchRequest("first", "A patient moon", "draft"),
                BatchRequest("second", "A lighthouse duel", "public"),
            )
            identity = load_or_create_batch_manager_identity(root.resolve())
            first = BatchPlan.from_requests(
                catalog,
                requests,
                playtest_rounds=4,
                manager_identity=identity,
            )
            second = BatchPlan.from_requests(
                catalog,
                requests,
                playtest_rounds=4,
                manager_identity=identity,
            )
            self.assertEqual(first.object_bytes(), second.object_bytes())
            self.assertEqual(first.plan_sha256, second.plan_sha256)
            self.assertTrue(first.batch_id.startswith("batch-"))
            self.assertNotIn("moon", first.batch_id)
            self.assertEqual(
                tuple(item.wish.product_id for item in first.items),
                tuple(item.wish.product_id for item in second.items),
            )
            self.assertEqual(
                tuple(item.publication_policy.visibility for item in first.items),
                ("draft", "public"),
            )
            self.assertEqual(
                first.items[0].wish.context["batch_key"], "first"
            )
            self.assertEqual(first.manager_scope_id, identity.scope_id)
            self.assertEqual(
                first.items[0].wish.context["batch_manager_scope_id"],
                identity.scope_id,
            )

    def test_opaque_ids_are_scoped_to_one_durable_manager_identity(self):
        with tempfile.TemporaryDirectory() as first_temporary, tempfile.TemporaryDirectory() as second_temporary:
            first_root = Path(first_temporary).resolve()
            second_root = Path(second_temporary).resolve()
            requests = (BatchRequest("same", "A patient moon", "public"),)
            first_identity = load_or_create_batch_manager_identity(first_root)
            self.assertEqual(
                load_or_create_batch_manager_identity(first_root).scope_id,
                first_identity.scope_id,
            )
            second_identity = load_or_create_batch_manager_identity(second_root)
            first = BatchPlan.from_requests(
                self.catalog(first_root),
                requests,
                playtest_rounds=4,
                manager_identity=first_identity,
            )
            second = BatchPlan.from_requests(
                self.catalog(second_root),
                requests,
                playtest_rounds=4,
                manager_identity=second_identity,
            )

            self.assertNotEqual(first.batch_id, second.batch_id)
            self.assertNotEqual(
                first.items[0].wish.product_id,
                second.items[0].wish.product_id,
            )
            identity_path = first_root / ".workshop" / "manager-batch-identity.json"
            self.assertEqual(stat.S_IMODE(identity_path.stat().st_mode), 0o600)

    def test_plan_binds_order_catalog_tastes_policy_and_pending_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = self.catalog(root)
            plan = BatchPlan.create(
                "batch-canonical",
                catalog,
                self.entries(),
                playtest_rounds=7,
            )
            pending = plan.pending_wishes()

            self.assertEqual(
                tuple(item.wish.product_id for item in plan.items),
                ("wish-batch-one", "wish-batch-two", "wish-batch-three"),
            )
            self.assertEqual(
                tuple(item.publication_policy.visibility for item in plan.items),
                ("draft", "public", "draft"),
            )
            self.assertEqual(
                tuple(item.pending_wish_sha256 for item in plan.items),
                tuple(item.record_sha256 for item in pending),
            )
            self.assertEqual(plan.playtest_rounds, 7)
            self.assertEqual(plan.catalog_sha256, catalog.catalog_sha256)
            self.assertEqual(
                plan.catalog_taste_sha256s,
                tuple(
                    sorted(
                        (card.inventor_id, load_taste(card.root).sha256)
                        for card in catalog.cards
                    )
                ),
            )
            self.assertEqual(
                hashlib.sha256(plan.object_bytes()).hexdigest(), plan.plan_sha256
            )
            loaded = BatchPlan.from_object_bytes(
                plan.object_bytes(), expected_sha256=plan.plan_sha256
            )
            self.assertEqual(loaded.to_dict(), plan.to_dict())
            self.assertEqual(loaded.object_bytes(), plan.object_bytes())

    def test_noncanonical_tamper_duplicate_ids_and_mixed_snapshots_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.plan(root)
            pretty = json.dumps(plan._identity_dict(), indent=2).encode("utf-8")
            with self.assertRaisesRegex(ContractError, "exact canonical"):
                BatchPlan.from_object_bytes(
                    pretty,
                    expected_sha256=hashlib.sha256(pretty).hexdigest(),
                )

            catalog = discover_inventor_catalog(root)
            duplicate = self.entries()[:1] * 2
            with self.assertRaisesRegex(ContractError, "unique"):
                BatchPlan.create(
                    "batch-duplicate",
                    catalog,
                    duplicate,
                    playtest_rounds=4,
                )

            first = plan.pending_wishes()[0]
            other = PendingWish(
                wish=Wish.create("wish-other", "another exact Wish"),
                publication_policy=first.publication_policy,
                playtest_rounds=5,
                catalog_collection=first.catalog_collection,
                catalog_sha256=first.catalog_sha256,
                catalog_total=first.catalog_total,
                catalog_taste_sha256s=first.catalog_taste_sha256s,
            )
            with self.assertRaisesRegex(ContractError, "one exact catalog"):
                BatchPlan.from_pending_wishes("batch-mixed", (first, other))

    def test_generated_id_is_opaque_and_validated(self):
        moment = datetime(2026, 8, 26, 1, 2, 3, tzinfo=timezone.utc)
        self.assertEqual(
            generate_batch_id(moment=moment, token="deadbeef"),
            "batch-20260826-010203-deadbeef",
        )
        with self.assertRaisesRegex(ContractError, "eight lowercase"):
            generate_batch_id(token="BAD")


class BatchPlanStoreTest(BatchFixture):
    def test_store_is_content_addressed_private_and_exact_save_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.plan(root)
            store = BatchPlanStore(plan.catalog_collection)

            first_path = store.save(plan)
            second_path = store.save(plan)
            loaded = store.load(plan.batch_id)

            self.assertEqual(first_path, second_path)
            self.assertEqual(loaded.to_dict(), plan.to_dict())
            self.assertEqual(store.list(), (plan,))
            object_path = store.path / "objects" / (plan.plan_sha256 + ".json")
            self.assertEqual(object_path.read_bytes(), plan.object_bytes())
            self.assertEqual(stat.S_IMODE(object_path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(first_path.stat().st_mode), 0o600)
            for directory in (
                store.path,
                store.path / "objects",
                store.path / "by-batch",
                store.path / "locks",
            ):
                self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)

            changed = BatchPlan.create(
                plan.batch_id,
                discover_inventor_catalog(root),
                (
                    (
                        Wish.create("wish-replacement", "different batch"),
                        PublicationPolicy.for_wish(publish=False),
                    ),
                ),
                playtest_rounds=4,
            )
            with self.assertRaisesRegex(WorkshopError, "different immutable"):
                store.save(changed)

    def test_save_rereads_an_existing_index_at_its_commit_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.plan(root)
            store = BatchPlanStore(plan.catalog_collection)
            index = store.save(plan)
            from inventor_workshop import batch as batch_module

            real_write = batch_module._write_atomic_exclusive

            def race_pointer(*args, **kwargs):
                if kwargs.get("label") != "Manager batch index":
                    return real_write(*args, **kwargs)
                index.write_bytes(store._index_bytes(plan.batch_id, "f" * 64))
                index.chmod(0o600)
                return False

            with mock.patch.object(
                batch_module,
                "_write_atomic_exclusive",
                side_effect=race_pointer,
            ), self.assertRaisesRegex(WorkshopError, "different immutable"):
                store.save(plan)

    def test_stage_saves_plan_before_pending_and_repairs_crash_gaps(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.plan(root)
            store = BatchPlanStore(plan.catalog_collection)
            pending = PendingWishStore(plan.catalog_collection)
            real_save = pending._batch_save
            calls = 0

            def fail_on_second(record):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise RuntimeError("simulated process death")
                return real_save(record)

            with mock.patch.object(
                pending, "_batch_save", side_effect=fail_on_second
            ):
                with self.assertRaisesRegex(RuntimeError, "process death"):
                    store.stage(plan, pending)

            # Recovery anchor was durable before the first PendingWish write.
            self.assertEqual(store.load(plan.batch_id).plan_sha256, plan.plan_sha256)
            expected = plan.pending_wishes()
            self.assertEqual(
                pending.load(expected[0].wish.product_id).record_sha256,
                expected[0].record_sha256,
            )
            self.assertIsNone(
                pending.load(expected[1].wish.product_id, allow_missing=True)
            )

            repaired = store.repair_pending(plan, pending)
            self.assertEqual(
                tuple(item.record_sha256 for item in repaired),
                tuple(item.record_sha256 for item in expected),
            )
            # Replaying the full staging operation is also an exact no-op.
            replayed = store.stage(plan, pending)
            self.assertEqual(
                tuple(item.record_sha256 for item in replayed),
                tuple(item.record_sha256 for item in expected),
            )

    def test_atomic_plan_write_recovers_after_a_crash_before_final_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.plan(root)
            store = BatchPlanStore(plan.catalog_collection)
            from inventor_workshop import batch as batch_module

            real_write = batch_module._write_private_exclusive
            failed = False

            def crash_after_fsync(*args, **kwargs):
                nonlocal failed
                result = real_write(*args, **kwargs)
                if not failed:
                    failed = True
                    raise RuntimeError("simulated crash before final link")
                return result

            with mock.patch.object(
                batch_module,
                "_write_private_exclusive",
                side_effect=crash_after_fsync,
            ):
                with self.assertRaisesRegex(RuntimeError, "before final link"):
                    store.save(plan)

            saved = store.stage(plan)
            self.assertEqual(len(saved), len(plan.items))
            self.assertEqual(store.load(plan.batch_id).plan_sha256, plan.plan_sha256)

    def test_atomic_pending_write_recovers_after_a_crash_before_final_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.plan(root)
            store = BatchPlanStore(plan.catalog_collection)
            pending = PendingWishStore(plan.catalog_collection)
            store.save(plan)
            from inventor_workshop import pending_wish as pending_module

            real_write = pending_module._write_private_exclusive
            failed = False

            def crash_after_fsync(*args, **kwargs):
                nonlocal failed
                result = real_write(*args, **kwargs)
                if not failed:
                    failed = True
                    raise RuntimeError("simulated pending crash before final link")
                return result

            with mock.patch.object(
                pending_module,
                "_write_private_exclusive",
                side_effect=crash_after_fsync,
            ):
                with self.assertRaisesRegex(RuntimeError, "pending crash"):
                    store.repair_pending(plan, pending)

            repaired = store.repair_pending(plan, pending)
            self.assertEqual(len(repaired), len(plan.items))

    def test_monotonic_public_upgrade_remains_batch_compatible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = self.catalog(root)
            identity = load_or_create_batch_manager_identity(root.resolve())
            plan = BatchPlan.from_requests(
                catalog,
                (BatchRequest("one", "A patient mechanical moon", "draft"),),
                playtest_rounds=4,
                manager_identity=identity,
            )
            store = BatchPlanStore(plan.catalog_collection)
            pending_store = PendingWishStore(plan.catalog_collection)
            store.stage(plan, pending_store)
            expected = pending_store.load(plan.items[0].wish.product_id)
            upgraded = expected.with_publication_policy(
                expected.publication_policy.authorize_public()
            )
            pending_store.replace(expected, upgraded)

            repaired = store.repair_pending(plan, pending_store)

            self.assertEqual(repaired, (upgraded,))

    def test_one_thousand_item_stage_repair_is_linear_and_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            catalog = self.catalog(root)
            identity = load_or_create_batch_manager_identity(root)
            requests = tuple(
                BatchRequest(
                    "item-%04d" % position,
                    "Unique clockwork creature number %d" % position,
                    "draft",
                )
                for position in range(1, 1_001)
            )
            plan = BatchPlan.from_requests(
                catalog,
                requests,
                playtest_rounds=4,
                manager_identity=identity,
            )
            store = BatchPlanStore(plan.catalog_collection)

            started = time.monotonic()
            store.stage(plan)
            stage_seconds = time.monotonic() - started
            started = time.monotonic()
            repaired = store.repair_pending(plan)
            repair_seconds = time.monotonic() - started
            from inventor_workshop.cli import _batch_status_payload

            real_validate = PendingWishStore._validated_indexes
            with mock.patch.object(
                PendingWishStore,
                "_validated_indexes",
                wraps=real_validate,
            ) as validate:
                started = time.monotonic()
                status = _batch_status_payload(plan, root)
                status_seconds = time.monotonic() - started

            self.assertEqual(len(repaired), 1_000)
            self.assertEqual(status["count"], 1_000)
            self.assertEqual(validate.call_count, 2)
            self.assertLess(stage_seconds, 30)
            self.assertLess(repair_seconds, 20)
            self.assertLess(status_seconds, 30)

    def test_repair_never_overwrites_a_conflicting_pending_wish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.plan(root)
            batch_store = BatchPlanStore(plan.catalog_collection)
            pending_store = PendingWishStore(plan.catalog_collection)
            batch_store.save(plan)
            expected = plan.pending_wishes()[0]
            conflict = PendingWish(
                wish=Wish.create(
                    expected.wish.product_id,
                    "different content forced onto the same Wish id",
                ),
                publication_policy=expected.publication_policy,
                playtest_rounds=expected.playtest_rounds,
                catalog_collection=expected.catalog_collection,
                catalog_sha256=expected.catalog_sha256,
                catalog_total=expected.catalog_total,
                catalog_taste_sha256s=expected.catalog_taste_sha256s,
            )
            pending_store.save(conflict)

            with self.assertRaisesRegex(WorkshopError, "different pending"):
                batch_store.repair_pending(plan, pending_store)
            self.assertEqual(
                pending_store.load(expected.wish.product_id).record_sha256,
                conflict.record_sha256,
            )

    def test_repair_requires_the_exact_saved_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.plan(root)
            store = BatchPlanStore(plan.catalog_collection)
            with self.assertRaisesRegex(WorkshopError, "index is missing"):
                store.repair_pending(plan)

    def test_store_and_lock_symlinks_are_never_followed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.plan(root)
            store = BatchPlanStore(plan.catalog_collection)
            store.save(plan)
            real = store.path.with_name("manager-batches-real")
            store.path.rename(real)
            store.path.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(WorkshopError, "regular directory"):
                store.load(plan.batch_id)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.plan(root)
            store = BatchPlanStore(plan.catalog_collection)
            store.save(plan)
            lock = store.path / "locks" / (
                hashlib.sha256(plan.batch_id.encode("utf-8")).hexdigest() + ".lock"
            )
            target = store.path / "objects" / (plan.plan_sha256 + ".json")
            lock.symlink_to(target)
            with self.assertRaisesRegex(WorkshopError, "lock"):
                with store.lock(plan.batch_id):
                    pass

    def test_directory_and_object_tampering_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.plan(root)
            store = BatchPlanStore(plan.catalog_collection)
            store.save(plan)
            object_path = store.path / "objects" / (plan.plan_sha256 + ".json")
            object_path.chmod(0o644)
            with self.assertRaisesRegex(WorkshopError, "permissions are not private"):
                store.load(plan.batch_id)

            object_path.chmod(0o600)
            source = object_path.read_bytes()
            object_path.write_bytes(source[:-1] + b" ")
            object_path.chmod(0o600)
            with self.assertRaisesRegex(WorkshopError, "address|canonical"):
                store.load(plan.batch_id)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
