import hashlib
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from inventor_workshop.cli import _save_manager_assignment, main
from inventor_workshop.errors import WorkshopError
from inventor_workshop.handoff import PublicationPolicy
from inventor_workshop.jobs import Need, WaitingFor
from inventor_workshop.manager import TasteFit, create_shortlist, discover_inventor_catalog
from inventor_workshop.make import Wish
from inventor_workshop.match_attempt import MatchAttemptStore
from inventor_workshop.pending_wish import PendingWish, PendingWishStore
from tests import test_cli as cli_fixtures


class _UnavailableSemanticManager:
    judge_identity = "fixture-semantic-manager"
    judge_version = "1.0.0"
    judge_config_sha256 = "f" * 64

    def retrieve(self, context):
        del context
        raise WaitingFor(
            Need(
                "wish",
                "semantic-manager",
                "The semantic Manager is temporarily unavailable.",
                "Resume this exact Wish after reconnecting the Manager.",
            )
        )

    def judge(self, context):  # pragma: no cover - retrieve always waits
        del context
        raise AssertionError("judge must not run")


class _MiraSemanticManager:
    judge_identity = "fixture-semantic-manager"
    judge_version = "1.0.0"
    judge_config_sha256 = "e" * 64
    explanation = "Mira makes this exact small mechanical surprise sing."

    def retrieve(self, context):
        return create_shortlist(
            context,
            ("mira",),
            retriever=self.judge_identity,
            retriever_version=self.judge_version,
            rationale=self.explanation,
        )

    def judge(self, context):
        finalist = context.finalists[0]
        return (
            TasteFit(
                inventor_id="mira",
                taste_sha256=finalist.taste.sha256,
                score=97,
                accepted=True,
                explanation=self.explanation,
            ),
        )


class PendingWishStoreTest(unittest.TestCase):
    @staticmethod
    def _catalog(root: Path, inventor_id: str = "mira"):
        cli_fixtures.CliTest.inventor_identity(
            root / "inventors" / inventor_id, inventor_id
        )
        return discover_inventor_catalog(root)

    @classmethod
    def _record(
        cls,
        root: Path,
        *,
        product_id: str = "wish-20260826-010203-deadbeef",
        objective: str = "A tiny moon that walks when I wind it",
        publish: bool = False,
    ):
        catalog = cls._catalog(root)
        return PendingWish.create(
            Wish.create(
                product_id,
                objective,
                context={"source": "workshop-cli"},
            ),
            PublicationPolicy.for_wish(publish=publish),
            catalog,
            playtest_rounds=4,
        )

    @staticmethod
    def _replace_with_legacy_record(store: PendingWishStore, record: PendingWish):
        """Install the exact pre-full-TASTE wire shape used by old checkouts."""

        payload = json.loads(record.object_bytes().decode("utf-8"))
        payload["catalog"].pop("taste_sha256s")
        source = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        digest = hashlib.sha256(source).hexdigest()
        object_path = store.path / "objects" / (digest + ".json")
        object_path.write_bytes(source)
        object_path.chmod(0o600)
        index_path = store.path / "by-wish" / (
            hashlib.sha256(record.wish.product_id.encode("utf-8")).hexdigest()
            + ".json"
        )
        index_path.write_bytes(store._index_bytes(record.wish.product_id, digest))
        index_path.chmod(0o600)
        return source, digest

    def test_content_addressed_record_round_trips_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = self._record(root)
            store = PendingWishStore(record.catalog_collection)
            index = store.save(record)
            loaded = store.load(record.wish.product_id)

            self.assertEqual(loaded.to_dict(), record.to_dict())
            self.assertEqual(store.list(), (record,))
            self.assertEqual(index.name, hashlib.sha256(
                record.wish.product_id.encode("utf-8")
            ).hexdigest() + ".json")
            object_path = store.path / "objects" / (record.record_sha256 + ".json")
            self.assertEqual(
                hashlib.sha256(object_path.read_bytes()).hexdigest(),
                record.record_sha256,
            )
            self.assertEqual(object_path.read_bytes(), record.object_bytes())

    def test_save_rereads_an_existing_index_at_its_commit_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = self._record(root)
            store = PendingWishStore(record.catalog_collection)
            index = store.save(record)
            from inventor_workshop import pending_wish as pending_module

            real_write = pending_module._write_atomic_exclusive

            def race_pointer(*args, **kwargs):
                if kwargs.get("label") != "Manager pending Wish index":
                    return real_write(*args, **kwargs)
                index.write_bytes(
                    store._index_bytes(record.wish.product_id, "f" * 64)
                )
                index.chmod(0o600)
                return False

            with mock.patch.object(
                pending_module,
                "_write_atomic_exclusive",
                side_effect=race_pointer,
            ), self.assertRaisesRegex(WorkshopError, "different pending record"):
                store.save(record)

    def test_legacy_record_is_readable_but_cannot_be_rematched(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = self._record(root)
            store = PendingWishStore(record.catalog_collection)
            store.save(record)
            source, digest = self._replace_with_legacy_record(store, record)

            legacy = store.load(record.wish.product_id)
            self.assertFalse(legacy.catalog_taste_identity_bound)
            self.assertEqual(legacy.catalog_taste_sha256s, ())
            self.assertEqual(legacy.record_sha256, digest)
            self.assertEqual(legacy.object_bytes(), source)
            self.assertEqual(store.list(), (legacy,))
            with self.assertRaisesRegex(WorkshopError, "legacy.*full-TASTE"):
                legacy.assert_catalog_current(discover_inventor_catalog(root))

    def test_tamper_symlink_duplicate_and_content_collision_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = self._record(root)
            store = PendingWishStore(record.catalog_collection)
            index = store.save(record)
            object_path = store.path / "objects" / (record.record_sha256 + ".json")
            original = object_path.read_bytes()
            object_path.write_bytes(original[:-1] + b" ")
            with self.assertRaisesRegex(WorkshopError, "address|canonical"):
                store.load(record.wish.product_id)

            object_path.write_bytes(original)
            index_copy = index.with_name("safe-index-copy")
            index_copy.write_bytes(index.read_bytes())
            index.unlink()
            index.symlink_to(index_copy)
            with self.assertRaisesRegex(WorkshopError, "regular file"):
                store.load(record.wish.product_id)

            index.unlink()
            index.write_bytes(index_copy.read_bytes())
            index.chmod(0o600)
            index_copy.unlink()
            duplicate = index.with_name("0" * 64 + ".json")
            duplicate.write_bytes(index.read_bytes())
            duplicate.chmod(0o600)
            with self.assertRaisesRegex(WorkshopError, "collision|duplicate"):
                store.load(record.wish.product_id)
            duplicate.unlink()
            collision = self._record(
                root,
                product_id=record.wish.product_id,
                objective="A different Wish forced onto the same id",
            )
            with self.assertRaisesRegex(WorkshopError, "different pending record"):
                store.save(collision)

    def test_catalog_root_swap_fails_even_when_catalog_content_matches(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            first_root = base / "first"
            second_root = base / "second"
            first = self._record(first_root)
            first_store = PendingWishStore(first.catalog_collection)
            first_store.save(first)
            second_catalog = self._catalog(second_root)
            second_runtime = second_catalog.collection / ".workshop"
            second_runtime.mkdir(mode=0o700)
            shutil.copytree(first_store.path, second_runtime / "manager-wishes")

            copied = PendingWishStore(second_catalog.collection).load(
                first.wish.product_id
            )
            with self.assertRaisesRegex(WorkshopError, "different catalog root"):
                copied.assert_catalog_current(second_catalog)

    def test_full_taste_change_after_save_cannot_change_a_resumed_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = self._record(root)
            taste_path = record.catalog_collection / "mira" / "TASTE.md"
            original = taste_path.read_text(encoding="utf-8")
            taste_path.write_text(
                original + "\nA new constitution that would change the match.\n",
                encoding="utf-8",
            )
            changed_catalog = discover_inventor_catalog(root)
            # Compact routing cards intentionally disclose only the header, so
            # their public digest stays stable. The Manager-owned pending ledger
            # separately binds every complete Taste byte digest.
            self.assertEqual(changed_catalog.catalog_sha256, record.catalog_sha256)
            with self.assertRaisesRegex(WorkshopError, "full Taste changed"):
                record.assert_catalog_current(changed_catalog)

    def test_pending_parent_and_lock_symlinks_are_never_followed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = self._record(root)
            store = PendingWishStore(record.catalog_collection)
            store.save(record)
            real = store.path.with_name("manager-wishes-real")
            store.path.rename(real)
            store.path.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(WorkshopError, "regular directory"):
                store.load(record.wish.product_id)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = self._record(root)
            store = PendingWishStore(record.catalog_collection)
            store.save(record)
            lock = store.path / "locks" / (
                hashlib.sha256(record.wish.product_id.encode("utf-8")).hexdigest()
                + ".lock"
            )
            target = store.path / "objects" / (record.record_sha256 + ".json")
            lock.symlink_to(target)
            with self.assertRaisesRegex(WorkshopError, "lock"):
                with store.lock(record.wish.product_id):
                    pass

    def test_assignment_name_never_exposes_partially_staged_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inventor_root = root / "inventors" / "mira"
            card, taste = cli_fixtures.CliTest.inventor_identity(
                inventor_root, "mira"
            )
            wish = Wish.create("wish-atomic-assignment", "A tiny patient moon")
            assignment = SimpleNamespace(
                wish=wish,
                inventor_id="mira",
                playtest_rounds=4,
                assignment_sha256="a" * 64,
                entrypoint=tuple(card.entrypoint),
                decision=SimpleNamespace(
                    decision_sha256="d" * 64,
                    selected=SimpleNamespace(card=card, taste=taste),
                ),
            )
            with mock.patch(
                "inventor_workshop.cli.os.link",
                side_effect=OSError("fixture link failure"),
            ), self.assertRaisesRegex(WorkshopError, "atomically seal"):
                _save_manager_assignment(assignment)
            assignment_root = inventor_root / ".workshop" / "manager-assignments"
            self.assertEqual(tuple(assignment_root.glob("*.json")), ())
            self.assertEqual(tuple(assignment_root.glob("*.tmp")), ())

            path = _save_manager_assignment(assignment)
            self.assertTrue(path.is_file())
            self.assertEqual(len(tuple(assignment_root.glob("*.json"))), 1)


class PendingWishCliTest(unittest.TestCase):
    product_id = "wish-20260826-010203-cafebabe"
    objective = "a wind-up moon that follows me"

    @staticmethod
    def _root(path: Path) -> Path:
        cli_fixtures.CliTest.inventor_identity(
            path / "inventors" / "mira", "mira"
        )
        return path

    def _wish_waiting_at_match(self, root: Path):
        output = StringIO()
        progress = StringIO()
        with mock.patch(
            "inventor_workshop.cli.generate_wish_id", return_value=self.product_id
        ), mock.patch(
            "inventor_workshop.cli.CodexSemanticManager",
            return_value=_UnavailableSemanticManager(),
        ), redirect_stdout(output), redirect_stderr(progress):
            result = main(
                (
                    "wish",
                    *self.objective.split(),
                    "--root",
                    str(root),
                    "--draft",
                    "--json",
                )
            )
        return result, json.loads(output.getvalue()), progress.getvalue()

    def test_wish_is_durable_before_first_model_call_and_wait_is_status_visible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(Path(temporary))
            catalog = discover_inventor_catalog(root)
            observed = {}

            def semantic_factory():
                pending = PendingWishStore(catalog.collection).load(self.product_id)
                observed["wish"] = pending.wish.to_dict()
                observed["policy"] = pending.publication_policy.to_dict()
                observed["catalog"] = pending.catalog_sha256
                return _UnavailableSemanticManager()

            output = StringIO()
            progress = StringIO()
            with mock.patch(
                "inventor_workshop.cli.generate_wish_id", return_value=self.product_id
            ), mock.patch(
                "inventor_workshop.cli.CodexSemanticManager",
                side_effect=semantic_factory,
            ), redirect_stdout(output), redirect_stderr(progress):
                result = main(
                    (
                        "wish",
                        *self.objective.split(),
                        "--root",
                        str(root),
                        "--draft",
                        "--json",
                    )
                )
            receipt = json.loads(output.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(observed["wish"], receipt["wish"])
            self.assertEqual(observed["policy"], receipt["publication_policy"])
            self.assertEqual(observed["catalog"], catalog.catalog_sha256)
            self.assertEqual(receipt["job"], "match")
            self.assertEqual(receipt["durable_status"], "waiting")
            self.assertEqual(receipt["match_attempt"]["status"], "waiting")
            self.assertEqual(
                receipt["match_attempt"]["needs"], receipt["needs"]
            )
            self.assertIn("resume %s" % self.product_id, receipt["next_command"])
            self.assertNotIn("workshop wish", receipt["next_command"])

            pending_root = PendingWishStore(catalog.collection).path
            before = {
                path.relative_to(pending_root): (
                    path.read_bytes(),
                    path.stat().st_mode,
                    path.stat().st_mtime_ns,
                )
                for path in pending_root.rglob("*")
                if path.is_file()
            }
            status_output = StringIO()
            with redirect_stdout(status_output):
                self.assertEqual(
                    main(
                        (
                            "status",
                            self.product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            status = json.loads(status_output.getvalue())
            self.assertEqual(status["status"], "waiting")
            self.assertEqual(status["job"], "match")
            self.assertEqual(status["needs"], receipt["needs"])
            self.assertEqual(
                status["match_attempt"], receipt["match_attempt"]
            )
            self.assertIsNone(status["inventor_id"])
            self.assertEqual(status["wish"]["objective"], self.objective)
            self.assertEqual(status["resume"]["kind"], "match")
            self.assertIn("resume %s" % self.product_id, status["resume"]["command"])
            after = {
                path.relative_to(pending_root): (
                    path.read_bytes(),
                    path.stat().st_mode,
                    path.stat().st_mtime_ns,
                )
                for path in pending_root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)

    def test_status_lists_legacy_pending_wish_without_advertising_unsafe_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(Path(temporary))
            catalog = discover_inventor_catalog(root)
            record = PendingWish.create(
                Wish.create(
                    self.product_id,
                    self.objective,
                    context={"source": "workshop-cli"},
                ),
                PublicationPolicy.for_wish(publish=False),
                catalog,
                playtest_rounds=4,
            )
            store = PendingWishStore(catalog.collection)
            store.save(record)
            PendingWishStoreTest._replace_with_legacy_record(store, record)

            single_output = StringIO()
            with redirect_stdout(single_output):
                self.assertEqual(
                    main(
                        (
                            "status",
                            self.product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            single = json.loads(single_output.getvalue())
            self.assertEqual(single["status"], "matching")
            self.assertFalse(single["catalog"]["full_taste_bound"])
            self.assertEqual(single["resume"]["status"], "unavailable")
            self.assertEqual(single["resume"]["kind"], "legacy-match")
            self.assertIn("start a new Wish", single["resume"]["reason"])

            list_output = StringIO()
            with redirect_stdout(list_output):
                self.assertEqual(
                    main(("status", "--root", str(root), "--json")),
                    0,
                )
            listing = json.loads(list_output.getvalue())
            self.assertEqual(listing["count"], 1)
            self.assertEqual(listing["wishes"][0], single)

            error = StringIO()
            with mock.patch(
                "inventor_workshop.cli.CodexSemanticManager"
            ) as semantic, redirect_stderr(error):
                self.assertEqual(
                    main(
                        (
                            "resume",
                            self.product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    2,
                )
            semantic.assert_not_called()
            self.assertIn("legacy pending Wish", error.getvalue())

    def test_resume_matches_same_id_once_and_preserves_exact_why(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(Path(temporary))
            result, waiting, unused_progress = self._wish_waiting_at_match(root)
            self.assertEqual(result, 0)
            self.assertEqual(waiting["wish"]["product_id"], self.product_id)

            child_result = {
                "product_id": self.product_id,
                "status": "waiting",
                "job": "invent",
                "needs": [],
                "playtest_rounds": 4,
            }
            output = StringIO()
            progress = StringIO()
            with mock.patch(
                "inventor_workshop.cli.CodexSemanticManager",
                return_value=_MiraSemanticManager(),
            ) as semantic, mock.patch(
                "inventor_workshop.cli._run_inventor",
                return_value=child_result,
            ) as child, redirect_stdout(output), redirect_stderr(progress):
                resumed = main(
                    (
                        "resume",
                        self.product_id,
                        "--root",
                        str(root),
                        "--json",
                    )
                )
            receipt = json.loads(output.getvalue())
            self.assertEqual(resumed, 0)
            self.assertEqual(receipt["wish"], waiting["wish"])
            self.assertEqual(receipt["match"]["inventor_id"], "mira")
            self.assertEqual(
                receipt["match"]["explanation"],
                _MiraSemanticManager.explanation,
            )
            self.assertIn(
                "Why: %s" % _MiraSemanticManager.explanation,
                progress.getvalue(),
            )
            semantic.assert_called_once()
            self.assertEqual(child.call_args.args[0].wish.product_id, self.product_id)
            assignments = list(
                (root / "inventors" / "mira" / ".workshop" / "manager-assignments").glob(
                    "*.json"
                )
            )
            self.assertEqual(len(assignments), 1)

            status_output = StringIO()
            with redirect_stdout(status_output):
                self.assertEqual(
                    main(
                        (
                            "status",
                            self.product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            status = json.loads(status_output.getvalue())
            self.assertEqual(status["status"], "assigned")
            self.assertEqual(status["inventor_id"], "mira")
            self.assertEqual(status["resume"]["kind"], "assigned")
            self.assertEqual(len(assignments), 1)

    def test_strict_resume_returns_one_for_a_durable_match_wait(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(Path(temporary))
            result, first, unused_progress = self._wish_waiting_at_match(root)
            self.assertEqual(result, 0)
            output = StringIO()
            progress = StringIO()
            with mock.patch(
                "inventor_workshop.cli.CodexSemanticManager",
                return_value=_UnavailableSemanticManager(),
            ), redirect_stdout(output), redirect_stderr(progress):
                code = main(
                    (
                        "resume",
                        self.product_id,
                        "--root",
                        str(root),
                        "--strict",
                        "--json",
                    )
                )
            receipt = json.loads(output.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(receipt["durable_status"], "waiting")
            self.assertEqual(receipt["match_attempt"]["attempt_number"], 2)
            self.assertNotEqual(
                receipt["match_attempt"]["attempt_id"],
                first["match_attempt"]["attempt_id"],
            )

    def test_saved_handoff_is_authoritative_if_assigned_event_append_crashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(Path(temporary))
            self._wish_waiting_at_match(root)
            error = StringIO()
            with mock.patch(
                "inventor_workshop.cli.CodexSemanticManager",
                return_value=_MiraSemanticManager(),
            ), mock.patch(
                "inventor_workshop.cli.MatchAttemptStore.record_assigned",
                side_effect=WorkshopError("fixture crash after handoff fsync"),
            ), redirect_stderr(error):
                self.assertEqual(
                    main(
                        (
                            "resume",
                            self.product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    2,
                )
            self.assertIn("after handoff fsync", error.getvalue())

            catalog = discover_inventor_catalog(root)
            latest = MatchAttemptStore(catalog.collection).load(self.product_id)
            self.assertEqual(latest.status, "working")
            status_output = StringIO()
            with redirect_stdout(status_output):
                self.assertEqual(
                    main(
                        (
                            "status",
                            self.product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            status = json.loads(status_output.getvalue())
            self.assertEqual(status["status"], "assigned")
            self.assertEqual(status["match_attempt"]["status"], "working")
            self.assertRegex(status["manager_handoff_sha256"], r"^[0-9a-f]{64}$")

            child_result = {
                "product_id": self.product_id,
                "status": "waiting",
                "job": "invent",
                "needs": [],
                "playtest_rounds": 4,
            }
            output = StringIO()
            with mock.patch(
                "inventor_workshop.cli.CodexSemanticManager"
            ) as semantic, mock.patch(
                "inventor_workshop.cli._run_inventor",
                return_value=child_result,
            ), redirect_stdout(output):
                self.assertEqual(
                    main(
                        (
                            "resume",
                            self.product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            semantic.assert_not_called()

    def test_publication_upgrade_preserves_immutable_assigned_match_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(Path(temporary))
            self._wish_waiting_at_match(root)
            child_result = {
                "product_id": self.product_id,
                "status": "waiting",
                "job": "invent",
                "needs": [],
                "playtest_rounds": 4,
            }
            with mock.patch(
                "inventor_workshop.cli.CodexSemanticManager",
                return_value=_MiraSemanticManager(),
            ), mock.patch(
                "inventor_workshop.cli._run_inventor",
                return_value=child_result,
            ), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(
                        (
                            "resume",
                            self.product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            catalog = discover_inventor_catalog(root)
            attempts = MatchAttemptStore(catalog.collection)
            before = attempts.load_chain(self.product_id)
            self.assertEqual(before[-1].status, "assigned")

            output = StringIO()
            with mock.patch(
                "inventor_workshop.cli._run_inventor",
                return_value=child_result,
            ), redirect_stdout(output), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(
                        (
                            "resume",
                            self.product_id,
                            "--root",
                            str(root),
                            "--publish",
                            "--json",
                        )
                    ),
                    0,
                )
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["publication_policy"]["visibility"], "public")
            self.assertEqual(attempts.load_chain(self.product_id), before)

            status_output = StringIO()
            with redirect_stdout(status_output):
                self.assertEqual(
                    main(
                        (
                            "status",
                            self.product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            status = json.loads(status_output.getvalue())
            self.assertEqual(status["status"], "assigned")
            self.assertEqual(status["publication_policy"]["visibility"], "public")
            self.assertEqual(
                status["match_attempt"]["event_sha256"],
                before[-1].event_sha256,
            )
            self.assertEqual(
                status["match_attempt"]["manager_handoff_sha256"],
                before[-1].manager_handoff_sha256,
            )
            self.assertNotEqual(
                status["manager_handoff_sha256"],
                status["match_attempt"]["manager_handoff_sha256"],
            )

    def test_status_retries_old_pending_new_match_pair_without_taking_write_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(Path(temporary))
            self._wish_waiting_at_match(root)
            catalog = discover_inventor_catalog(root)
            pending_store = PendingWishStore(catalog.collection)
            attempts = MatchAttemptStore(catalog.collection)
            original = pending_store.load(self.product_id)
            original_attempt = attempts.load(self.product_id)
            upgraded = original.with_publication_policy(
                original.publication_policy.authorize_public()
            )
            original_load = PendingWishStore.load
            raced = False

            def load_with_one_publication_race(
                selected_store, product_id, *, allow_missing=False
            ):
                nonlocal raced
                observed = original_load(
                    selected_store,
                    product_id,
                    allow_missing=allow_missing,
                )
                if not raced and product_id == self.product_id:
                    raced = True
                    with pending_store.lock(product_id):
                        pending_store.replace(original, upgraded)
                        working = attempts.begin(upgraded)
                        attempts.record_waiting(
                            working, original_attempt.needs
                        )
                return observed

            output = StringIO()
            with mock.patch.object(
                PendingWishStore,
                "load",
                load_with_one_publication_race,
            ), redirect_stdout(output):
                self.assertEqual(
                    main(
                        (
                            "status",
                            self.product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            status = json.loads(output.getvalue())
            self.assertTrue(raced)
            self.assertEqual(
                status["publication_policy"]["visibility"], "public"
            )
            self.assertEqual(
                status["match_attempt"]["pending_wish_sha256"],
                upgraded.record_sha256,
            )
            self.assertEqual(
                status["needs"], status["match_attempt"]["needs"]
            )

    def test_pending_resume_publication_upgrade_is_durable_across_match_waits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(Path(temporary))
            result, waiting, unused_progress = self._wish_waiting_at_match(root)
            self.assertEqual(result, 0)
            self.assertEqual(waiting["publication_policy"]["visibility"], "draft")

            output = StringIO()
            progress = StringIO()
            with mock.patch(
                "inventor_workshop.cli.CodexSemanticManager",
                return_value=_UnavailableSemanticManager(),
            ), redirect_stdout(output), redirect_stderr(progress):
                resumed = main(
                    (
                        "resume",
                        self.product_id,
                        "--root",
                        str(root),
                        "--publish",
                        "--json",
                    )
                )
            receipt = json.loads(output.getvalue())
            self.assertEqual(resumed, 0)
            self.assertEqual(receipt["publication_policy"]["visibility"], "public")
            self.assertEqual(
                receipt["publication_policy_change"]["authorization"],
                "explicit-resume-publish",
            )
            self.assertIn("visible to anyone", progress.getvalue())

            status_output = StringIO()
            with redirect_stdout(status_output):
                self.assertEqual(
                    main(
                        (
                            "status",
                            self.product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            status = json.loads(status_output.getvalue())
            self.assertEqual(status["status"], "waiting")
            self.assertEqual(
                status["needs"][0]["capability"], "semantic-manager"
            )
            self.assertEqual(status["publication_policy"]["visibility"], "public")

            error = StringIO()
            with mock.patch(
                "inventor_workshop.cli.CodexSemanticManager"
            ) as semantic, redirect_stderr(error):
                self.assertEqual(
                    main(
                        (
                            "resume",
                            self.product_id,
                            "--root",
                            str(root),
                            "--draft",
                            "--json",
                        )
                    ),
                    2,
                )
            self.assertIn("cannot downgrade", error.getvalue())
            semantic.assert_not_called()

    def test_save_failure_prints_no_untrackable_wish_id_or_calls_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(Path(temporary))
            output = StringIO()
            error = StringIO()
            with mock.patch(
                "inventor_workshop.cli.generate_wish_id", return_value=self.product_id
            ), mock.patch(
                "inventor_workshop.cli.PendingWishStore.save",
                side_effect=WorkshopError("fixture fsync failure"),
            ), mock.patch(
                "inventor_workshop.cli.CodexSemanticManager"
            ) as semantic, redirect_stdout(output), redirect_stderr(error):
                result = main(
                    (
                        "wish",
                        *self.objective.split(),
                        "--root",
                        str(root),
                        "--json",
                    )
                )
            self.assertEqual(result, 2)
            self.assertNotIn(self.product_id, output.getvalue())
            self.assertNotIn("Wish: %s" % self.product_id, error.getvalue())
            self.assertIn("fsync failure", error.getvalue())
            semantic.assert_not_called()

    def test_explicit_catalog_root_symlink_fails_before_model_or_wish_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = self._root(base / "real")
            alias = base / "alias"
            alias.symlink_to(root, target_is_directory=True)
            output = StringIO()
            error = StringIO()
            with mock.patch(
                "inventor_workshop.cli.generate_wish_id", return_value=self.product_id
            ), mock.patch(
                "inventor_workshop.cli.CodexSemanticManager"
            ) as semantic, redirect_stdout(output), redirect_stderr(error):
                result = main(
                    (
                        "wish",
                        *self.objective.split(),
                        "--root",
                        str(alias),
                        "--json",
                    )
                )
            self.assertEqual(result, 2)
            self.assertIn("must not be a symlink", error.getvalue())
            self.assertNotIn(self.product_id, output.getvalue())
            semantic.assert_not_called()


if __name__ == "__main__":
    unittest.main()
