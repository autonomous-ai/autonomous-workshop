import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from inventor_workshop import cli
from inventor_workshop.make import Wish
from inventor_workshop.store import InventorStore


class _SavedAssignment:
    def __init__(self, wish):
        self.wish = wish


class _IdleRuntime:
    @staticmethod
    def active_lease(unused_product_id):
        return None


class _BusyRuntime:
    @staticmethod
    def active_lease(unused_product_id):
        return {"holder": "running-worker", "expires_at": "2999-01-01T00:00:00Z"}


class WorldReferenceCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.catalog = Path(self.temp.name) / "catalog"
        self.inventor = self.catalog / "inventors" / "eve"
        self.inventor.mkdir(parents=True)
        self.wish = Wish.create(
            "wish-20260826-010101-abcdef12",
            "A tiny world starring my dog",
            context={"source": "workshop-cli"},
        )
        store = InventorStore(self.inventor / ".workshop" / "workshop.sqlite3")
        store.register_product(
            self.wish.product_id,
            "playtest",
            {
                "wish": self.wish.to_dict(),
                "lane": "little-worlds",
                "inventor_id": "eve",
            },
        )
        self.reference = Path(self.temp.name) / "reference.jpg"
        self.consent = Path(self.temp.name) / "consent.txt"
        self.private_reference = b"\xff\xd8\xffprivate-cli-reference-material\xff\xd9"
        self.private_consent = b"private-cli-customer-consent"
        self.reference.write_bytes(self.private_reference)
        self.consent.write_bytes(self.private_consent)

    def located(self, runtime=None):
        return {
            "card": SimpleNamespace(root=self.inventor, inventor_id="eve"),
            "handoff": _SavedAssignment(self.wish),
            "runtime": runtime or _IdleRuntime(),
            "product": {"id": self.wish.product_id},
        }

    def run_cli(self, argv, *, runtime=None):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(cli, "ManagerAssignmentHandoff", _SavedAssignment),
            mock.patch.object(cli, "_catalog_roots", return_value=(self.catalog,)),
            mock.patch.object(
                cli,
                "_root_for_durable_wish",
                return_value=(self.catalog, self.located(runtime)),
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            code = cli.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def add_args(self):
        return [
            "references",
            "add",
            self.wish.product_id,
            "customer-dog",
            str(self.reference),
            "--consent-file",
            str(self.consent),
            "--media-type",
            "image/jpeg",
            "--subject-kind",
            "customer-owned-subject",
            "--subject",
            "the customer's dog",
            "--rights-basis",
            "customer owns the reference and authorizes this toy",
            "--allow",
            "round ears",
            "--exclude",
            "home address",
            "--reviewer-id",
            "customer-order-42",
            "--allow-same-user-local-vault",
            "--json",
        ]

    def test_add_and_list_emit_only_raw_free_receipts(self):
        code, output, error = self.run_cli(self.add_args())
        self.assertEqual((code, error), (0, ""))
        document = json.loads(output)
        self.assertEqual(document["status"], "staged-local-development")
        self.assertEqual(
            document["integration_status"],
            {
                "invent": "ready-on-explicit-manager-resume",
                "playtest": "external-isolated-service-required",
            },
        )
        self.assertEqual(document["reference"]["reference_id"], "customer-dog")
        combined = (output + error).encode("utf-8")
        self.assertNotIn(self.private_reference, combined)
        self.assertNotIn(self.private_consent, combined)
        code, output, error = self.run_cli(
            ["references", "list", self.wish.product_id, "--json"]
        )
        self.assertEqual((code, error), (0, ""))
        listed = json.loads(output)
        self.assertEqual(len(listed["references"]), 1)
        self.assertNotIn(self.private_reference, output.encode("utf-8"))
        self.assertNotIn(self.private_consent, output.encode("utf-8"))

    def test_add_refuses_to_race_an_active_workshop_run(self):
        code, output, error = self.run_cli(self.add_args(), runtime=_BusyRuntime())
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertIn("still running", error)
        self.assertNotIn(self.private_reference, error.encode("utf-8"))
        self.assertNotIn(self.private_consent, error.encode("utf-8"))

    def test_local_storage_requires_an_explicit_same_user_trust_opt_in(self):
        arguments = self.add_args()
        arguments.remove("--allow-same-user-local-vault")
        code, output, error = self.run_cli(arguments)
        self.assertEqual((code, output), (2, ""))
        self.assertIn("not isolated", error)
        self.assertFalse(
            (
                self.inventor
                / ".workshop"
                / "private-inputs"
                / "world-references-v1"
            ).exists()
        )

    def test_parser_requires_customer_created_consent_and_explicit_scope(self):
        command = cli.parser()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            command.parse_args(
                [
                    "references",
                    "add",
                    self.wish.product_id,
                    "customer-dog",
                    str(self.reference),
                ]
            )
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            command.parse_args(
                self.add_args()[:-1]
                + ["--subject-kind", "celebrity"]
            )


if __name__ == "__main__":
    unittest.main()
