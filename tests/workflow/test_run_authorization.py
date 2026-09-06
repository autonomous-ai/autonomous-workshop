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

    def _write(self, value):
        self.path.write_bytes(json.dumps(value, sort_keys=True).encode("utf-8"))
        os.chmod(self.path, 0o600)

    def test_new_runs_freeze_publication_and_github_flags_in_schema_two(self):
        value = _record_authorization(
            self.paths,
            product_id="wish-1",
            publish_requested=True,
            create=True,
            github_publish_requested=True,
        )

        self.assertEqual(value["schema_version"], 2)
        self.assertTrue(value["publish_requested"])
        self.assertTrue(value["github_publish_requested"])
        self.assertNotIn("history_disclosure_requested", value)
        self.assertEqual(json.loads(self.path.read_bytes()), value)
        reread = _record_authorization(
            self.paths, product_id="wish-1", publish_requested=False, create=False
        )
        self.assertEqual(reread, value)

    def test_schema_one_files_read_without_github_authority(self):
        self._write(
            {
                "schema_version": 1,
                "kind": "autonomous-workshop.run-authorization",
                "product_id": "wish-1",
                "publish_requested": True,
            }
        )

        value = _record_authorization(
            self.paths, product_id="wish-1", publish_requested=False, create=False
        )

        self.assertEqual(value["schema_version"], 2)
        self.assertTrue(value["publish_requested"])
        self.assertFalse(value["github_publish_requested"])

    def test_withdrawn_schema_three_files_still_read_and_drop_the_flag(self):
        # Schema 3 briefly carried a history-disclosure flag on a branch that
        # was withdrawn before merging; runs recorded then must still resume.
        self._write(
            {
                "schema_version": 3,
                "kind": "autonomous-workshop.run-authorization",
                "product_id": "wish-1",
                "publish_requested": True,
                "github_publish_requested": True,
                "history_disclosure_requested": True,
            }
        )

        value = _record_authorization(
            self.paths, product_id="wish-1", publish_requested=False, create=False
        )

        self.assertEqual(value["schema_version"], 2)
        self.assertTrue(value["github_publish_requested"])
        self.assertNotIn("history_disclosure_requested", value)

    def test_malformed_files_are_rejected(self):
        self._write(
            {
                "schema_version": 2,
                "kind": "autonomous-workshop.run-authorization",
                "product_id": "wish-1",
                "publish_requested": True,
                "github_publish_requested": "yes",
            }
        )

        with self.assertRaises(StateConflict):
            _record_authorization(
                self.paths, product_id="wish-1", publish_requested=False, create=False
            )


if __name__ == "__main__":
    unittest.main()
