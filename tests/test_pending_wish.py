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

    def test_wish_is_durable_before_first_model_call_and_status_is_matching(self):
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
            self.assertEqual(receipt["durable_status"], "matching")
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
            self.assertEqual(status["status"], "matching")
            self.assertEqual(status["job"], "match")
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
            self.assertEqual(status["status"], "matching")
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
