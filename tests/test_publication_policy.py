import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from inventor_workshop.cli import main, parser
from inventor_workshop.errors import ContractError
from inventor_workshop.handoff import ManagerAssignmentHandoff, PublicationPolicy
from tests import test_cli as cli_fixtures


class DurablePublicationPolicyTest(unittest.TestCase):
    @staticmethod
    def _assigned_fixture(root: Path, policy=None):
        assignment, _, inventor_root = cli_fixtures.CliTest.durable_wait_fixture(
            root
        )
        database = inventor_root / ".workshop" / "workshop.sqlite3"
        database.unlink()
        if policy is not None:
            assignment.publication_policy = policy
            handoff = ManagerAssignmentHandoff.from_assignment(assignment)
            path = next(
                (inventor_root / ".workshop" / "manager-assignments").glob(
                    "*.json"
                )
            )
            path.write_text(
                json.dumps(handoff.to_dict(), sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return assignment, inventor_root

    @staticmethod
    def _site_wait():
        return {
            "product_id": "wish-one",
            "status": "waiting",
            "job": "instructions",
            "playtest_rounds": 4,
            "needs": [
                {
                    "job": "instructions",
                    "capability": "site-page",
                    "reason": "Factory authentication is required.",
                    "instructions": "Reconnect the trusted Manager.",
                }
            ],
        }

    @staticmethod
    def _draft_page_with_child_claim():
        return {
            "product_id": "wish-one",
            "status": "waiting",
            "job": "instructions",
            "playtest_rounds": 4,
            "needs": [],
            "page_url": "https://www.autonomous.ai/factory/product/wish-one",
            # Adversarial contribution output: the Manager must never consult it.
            "publication_policy": {"visibility": "public"},
        }

    def test_draft_wait_bare_resume_inherits_draft_and_retry_is_bare(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._assigned_fixture(
                root, PublicationPolicy.for_wish(publish=False)
            )
            output = StringIO()
            with mock.patch.dict("os.environ", {}, clear=True), mock.patch(
                "inventor_workshop.cli._run_inventor",
                return_value=self._site_wait(),
            ), mock.patch(
                "inventor_workshop.cli._publish_inventor_draft"
            ) as publish, redirect_stdout(output):
                result = main(
                    ("resume", "wish-one", "--root", str(root), "--json")
                )
            self.assertEqual(result, 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(
                receipt["publication_policy"]["visibility"], "draft"
            )
            instructions = receipt["result"]["needs"][0]["instructions"]
            self.assertIn("inherit its saved draft policy", instructions)
            self.assertIn("workshop resume wish-one", instructions)
            self.assertNotIn("--publish", instructions)
            self.assertNotIn("--draft", instructions)
            publish.assert_not_called()

    def test_wish_draft_is_sealed_before_the_child_launches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inventor_root = root / "inventors" / "mira"
            card, taste = cli_fixtures.CliTest.inventor_identity(
                inventor_root, "mira"
            )

            class FakeManager:
                def __init__(self, **kwargs):
                    self.catalog = kwargs["catalog_provider"]()

                def assign(self, wish, *, playtest_rounds):
                    decision = SimpleNamespace(
                        decision_sha256="d" * 64,
                        selected=SimpleNamespace(card=card, taste=taste),
                        fit=SimpleNamespace(score=95, explanation="Exact fixture fit."),
                        context=SimpleNamespace(
                            routing=SimpleNamespace(catalog=self.catalog)
                        ),
                    )
                    return SimpleNamespace(
                        wish=wish,
                        inventor_id="mira",
                        playtest_rounds=playtest_rounds,
                        assignment_sha256="a" * 64,
                        entrypoint=tuple(card.entrypoint),
                        decision=decision,
                        assert_current=lambda: None,
                    )

            output = StringIO()
            with mock.patch(
                "inventor_workshop.cli.WorkshopManager", FakeManager
            ), mock.patch(
                "inventor_workshop.cli._run_inventor",
                return_value={
                    "status": "waiting",
                    "job": "make",
                    "needs": [],
                },
            ), mock.patch(
                "inventor_workshop.cli._publish_inventor_draft"
            ) as publish, redirect_stdout(output), redirect_stderr(StringIO()):
                result = main(
                    (
                        "wish",
                        "a",
                        "tiny",
                        "rolling",
                        "moon",
                        "--draft",
                        "--root",
                        str(root),
                        "--json",
                    )
                )
            self.assertEqual(result, 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["publication_policy"]["visibility"], "draft")
            path = next(
                (inventor_root / ".workshop" / "manager-assignments").glob(
                    "*.json"
                )
            )
            saved = ManagerAssignmentHandoff.from_dict(
                json.loads(path.read_text(encoding="utf-8")),
                expected_inventor_id="mira",
            )
            self.assertEqual(saved.schema_version, 4)
            self.assertEqual(saved.publication_policy.visibility, "draft")
            publish.assert_not_called()

    def test_explicit_publish_is_durable_and_bare_retry_stays_public(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, inventor_root = self._assigned_fixture(
                root, PublicationPolicy.for_wish(publish=False)
            )
            public = {
                "status": "public",
                "verified": True,
                "page_url": "https://www.autonomous.ai/factory/product/wish-one",
            }
            output = StringIO()
            progress = StringIO()
            with mock.patch(
                "inventor_workshop.cli._run_inventor",
                return_value=self._draft_page_with_child_claim(),
            ), mock.patch(
                "inventor_workshop.cli._publish_inventor_draft",
                return_value=public,
            ) as publish, redirect_stdout(output), redirect_stderr(progress):
                result = main(
                    (
                        "resume",
                        "wish-one",
                        "--root",
                        str(root),
                        "--publish",
                        "--json",
                    )
                )
            self.assertEqual(result, 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["publication_policy"]["visibility"], "public")
            self.assertEqual(
                receipt["publication_policy_change"]["authorization"],
                "explicit-resume-publish",
            )
            self.assertIn("visible to anyone", progress.getvalue())
            publish.assert_called_once()

            path = next(
                (inventor_root / ".workshop" / "manager-assignments").glob(
                    "*.json"
                )
            )
            saved = ManagerAssignmentHandoff.from_dict(
                json.loads(path.read_text(encoding="utf-8")),
                expected_inventor_id="mira",
            )
            self.assertEqual(saved.publication_policy.visibility, "public")
            self.assertEqual(
                saved.publication_policy.authorization,
                "explicit-resume-publish",
            )

            output = StringIO()
            with mock.patch(
                "inventor_workshop.cli._run_inventor",
                return_value=self._draft_page_with_child_claim(),
            ), mock.patch(
                "inventor_workshop.cli._publish_inventor_draft",
                return_value=public,
            ) as publish, mock.patch(
                "inventor_workshop.cli._replace_manager_assignment_publication_policy"
            ) as replace, redirect_stdout(output):
                self.assertEqual(
                    main(
                        (
                            "resume",
                            "wish-one",
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            retried = json.loads(output.getvalue())
            self.assertEqual(retried["publication_policy"]["visibility"], "public")
            self.assertNotIn("publication_policy_change", retried)
            replace.assert_not_called()
            publish.assert_called_once()

    def test_public_policy_cannot_be_downgraded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._assigned_fixture(
                root, PublicationPolicy.for_wish(publish=True)
            )
            error = StringIO()
            with mock.patch(
                "inventor_workshop.cli._run_inventor"
            ) as child, mock.patch(
                "inventor_workshop.cli._publish_inventor_draft"
            ) as publish, redirect_stderr(error):
                result = main(
                    (
                        "resume",
                        "wish-one",
                        "--root",
                        str(root),
                        "--draft",
                        "--json",
                    )
                )
            self.assertEqual(result, 2)
            self.assertIn("cannot downgrade", error.getvalue())
            child.assert_not_called()
            publish.assert_not_called()

    def test_legacy_policy_and_child_claim_fail_safe_to_draft(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._assigned_fixture(root)
            output = StringIO()
            with mock.patch(
                "inventor_workshop.cli._run_inventor",
                return_value=self._draft_page_with_child_claim(),
            ), mock.patch(
                "inventor_workshop.cli._publish_inventor_draft"
            ) as publish, redirect_stdout(output):
                result = main(
                    ("resume", "wish-one", "--root", str(root), "--json")
                )
            self.assertEqual(result, 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["publication_policy"]["visibility"], "draft")
            self.assertEqual(
                receipt["publication_policy"]["authorization"],
                "legacy-fail-safe",
            )
            publish.assert_not_called()

    def test_policy_tamper_stops_before_child_or_factory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, inventor_root = self._assigned_fixture(
                root, PublicationPolicy.for_wish(publish=False)
            )
            path = next(
                (inventor_root / ".workshop" / "manager-assignments").glob(
                    "*.json"
                )
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["publication_policy"]["visibility"] = "public"
            path.write_text(json.dumps(payload), encoding="utf-8")
            error = StringIO()
            with mock.patch(
                "inventor_workshop.cli._run_inventor"
            ) as child, mock.patch(
                "inventor_workshop.cli._publish_inventor_draft"
            ) as publish, redirect_stderr(error):
                result = main(
                    ("resume", "wish-one", "--root", str(root), "--json")
                )
            self.assertEqual(result, 2)
            self.assertIn("publication policy identity", error.getvalue())
            child.assert_not_called()
            publish.assert_not_called()

    def test_resume_help_and_parser_make_inheritance_explicit(self):
        command = parser()
        subcommands = next(
            action
            for action in command._actions
            if hasattr(action, "choices") and action.choices
        )
        help_text = subcommands.choices["resume"].format_help()
        self.assertIn("inherits", help_text)
        self.assertIn("only explicit --publish", help_text)
        self.assertIn("visible to anyone", help_text)
        self.assertIsNone(command.parse_args(("resume", "wish-one")).publish)
        self.assertTrue(
            command.parse_args(("resume", "wish-one", "--publish")).publish
        )
        self.assertFalse(
            command.parse_args(("resume", "wish-one", "--draft")).publish
        )


class PublicationPolicyHandoffTest(unittest.TestCase):
    def test_policy_hash_is_part_of_handoff_and_child_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, _ = DurablePublicationPolicyTest._assigned_fixture(
                root, PublicationPolicy.for_wish(publish=False)
            )
            handoff = ManagerAssignmentHandoff.from_assignment(assignment)
            self.assertEqual(handoff.schema_version, 4)
            self.assertEqual(
                handoff.result_binding()["publication_policy_sha256"],
                handoff.publication_policy.policy_sha256,
            )
            payload = handoff.to_dict()
            payload["publication_policy"]["visibility"] = "public"
            payload["publication_policy"]["authorization"] = (
                "explicit-resume-publish"
            )
            with self.assertRaisesRegex(
                ContractError, "publication policy identity"
            ):
                ManagerAssignmentHandoff.from_dict(
                    payload, expected_inventor_id="mira"
                )


if __name__ == "__main__":
    unittest.main()
