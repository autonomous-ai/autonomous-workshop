from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from workshop.errors import StateConflict
from workshop.workflow.native_run import NativeRunPaths, _record_authorization


class RunAuthorizationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name).resolve()
        self.paths = NativeRunPaths(base / "workspace", base / "state")
        self.paths.workspace.mkdir()
        self.paths.host_state.mkdir(mode=0o700)
        os.chmod(self.paths.host_state, 0o700)
        self.path = self.paths.host_state / "authorization.json"

    def test_new_runs_freeze_history_disclosure_in_schema_three(self):
        value = _record_authorization(
            self.paths,
            product_id="wish-1",
            publish_requested=True,
            create=True,
            history_disclosure_requested=True,
        )

        self.assertEqual(value["schema_version"], 3)
        self.assertTrue(value["history_disclosure_requested"])
        self.assertFalse(value["github_publish_requested"])
        stored = json.loads(self.path.read_bytes())
        self.assertEqual(stored, value)
        reread = _record_authorization(
            self.paths, product_id="wish-1", publish_requested=False, create=False
        )
        self.assertTrue(reread["history_disclosure_requested"])
        self.assertTrue(reread["publish_requested"])

    def test_default_runs_do_not_disclose(self):
        value = _record_authorization(
            self.paths, product_id="wish-1", publish_requested=True, create=True
        )

        self.assertFalse(value["history_disclosure_requested"])

    def test_schema_two_files_read_as_undisclosed(self):
        self.path.write_bytes(
            json.dumps(
                {
                    "schema_version": 2,
                    "kind": "autonomous-workshop.run-authorization",
                    "product_id": "wish-1",
                    "publish_requested": True,
                    "github_publish_requested": True,
                },
                sort_keys=True,
            ).encode("utf-8")
        )
        os.chmod(self.path, 0o600)

        value = _record_authorization(
            self.paths, product_id="wish-1", publish_requested=False, create=False
        )

        self.assertEqual(value["schema_version"], 3)
        self.assertTrue(value["github_publish_requested"])
        self.assertFalse(value["history_disclosure_requested"])

    def test_malformed_schema_three_is_rejected(self):
        self.path.write_bytes(
            json.dumps(
                {
                    "schema_version": 3,
                    "kind": "autonomous-workshop.run-authorization",
                    "product_id": "wish-1",
                    "publish_requested": True,
                    "github_publish_requested": False,
                    "history_disclosure_requested": "yes",
                },
                sort_keys=True,
            ).encode("utf-8")
        )
        os.chmod(self.path, 0o600)

        with self.assertRaises(StateConflict):
            _record_authorization(
                self.paths, product_id="wish-1", publish_requested=False, create=False
            )


if __name__ == "__main__":
    unittest.main()
