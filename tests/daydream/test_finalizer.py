import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.daydream.support import (
    sample_idea_dict,
    sample_thesis_dict,
    sample_thesis_v3_dict,
)
from workshop.daydream import finalize_daydream
from workshop.daydream.contracts import Idea
from workshop.daydream.native import (
    DAYDREAM_OUTCOME_KIND,
    FINALIZER_FILE_NAME,
    SCHEMA_FILE_NAME,
    finalizer_bytes,
    schema_bytes,
)


class FinalizerTest(unittest.TestCase):
    def _root(self, temporary, idea):
        root = Path(temporary) / "workspace"
        (root / "work").mkdir(parents=True)
        (root / FINALIZER_FILE_NAME).write_bytes(finalizer_bytes())
        (root / SCHEMA_FILE_NAME).write_bytes(schema_bytes())
        if idea is not None:
            (root / "work" / "IDEA.json").write_text(
                idea if isinstance(idea, str) else json.dumps(idea), encoding="utf-8"
            )
        return root

    def _run(self, root):
        return subprocess.run(
            [sys.executable, str(root / FINALIZER_FILE_NAME)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def test_valid_idea_writes_a_bound_outcome(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary, sample_idea_dict())
            completed = self._run(root)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Mark the Goal complete and stop", completed.stdout)
            outcome = json.loads((root / "agent-outcome.json").read_text(encoding="utf-8"))
            self.assertEqual(outcome["kind"], DAYDREAM_OUTCOME_KIND)
            self.assertEqual(outcome["status"], "ready")
            self.assertEqual(outcome["idea_path"], "work/IDEA.json")
            self.assertEqual(
                outcome["idea_sha256"],
                hashlib.sha256((root / "work" / "IDEA.json").read_bytes()).hexdigest(),
            )
            self.assertEqual(outcome["title"], "Ladder Drop")
            self.assertFalse((root / "agent-outcome.json.tmp").exists())
            # Running it again after an edit rebinds the marker to the new bytes.
            raw = sample_idea_dict()
            raw["title"] = "Ladder Drop II"
            (root / "work" / "IDEA.json").write_text(json.dumps(raw), encoding="utf-8")
            self.assertEqual(self._run(root).returncode, 0)
            outcome = json.loads((root / "agent-outcome.json").read_text(encoding="utf-8"))
            self.assertEqual(outcome["title"], "Ladder Drop II")

    def test_schema_v2_thesis_finalizes_standalone(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary, sample_thesis_dict())
            completed = self._run(root)
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_schema_v3_thesis_finalizes_standalone(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary, sample_thesis_v3_dict())
            completed = self._run(root)
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_host_and_run_local_schema_have_parity_on_adversarial_corpus(self):
        idea_cases = [
            sample_idea_dict(),
            sample_thesis_dict(),
            sample_thesis_v3_dict(),
            [],
            {"schema_version": True},
        ]
        malformed = sample_thesis_dict()
        malformed["keywords"] = ["valid", {"unhashable": True}, "third"]
        idea_cases.append(malformed)
        malformed = sample_thesis_dict()
        malformed["title"] = "bad\x7fcontrol"
        idea_cases.append(malformed)
        malformed = sample_thesis_dict()
        malformed["opportunity"]["world_scan"]["signals"][0]["published_at"] = (
            "2026-09-03T10:15:00Z"
        )
        idea_cases.append(malformed)
        for index, raw in enumerate(idea_cases):
            finalizer_accepts = not finalize_daydream.idea_problems(raw)
            try:
                Idea.parse(raw)
            except Exception as exc:
                host_accepts = False
                self.assertEqual(exc.__class__.__name__, "ContractError")
            else:
                host_accepts = True
            with self.subTest(contract="idea", index=index):
                self.assertEqual(host_accepts, finalizer_accepts)

    def test_problems_are_listed_and_no_marker_is_written(self):
        raw = sample_idea_dict()
        raw["title"] = "x" * 61
        raw["prior_art"] = raw["prior_art"][:1]
        del raw["keywords"]
        raw["extra"] = 1
        cases = (
            (None, "is missing"),
            ("{not json", "not valid UTF-8 JSON"),
            ("[]", "one JSON object"),
            (raw, "missing keys: keywords"),
        )
        for idea, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                root = self._root(temporary, idea)
                completed = self._run(root)
                self.assertEqual(completed.returncode, 1)
                self.assertIn(expected, completed.stderr)
                self.assertFalse((root / "agent-outcome.json").exists())
        problems = finalize_daydream.idea_problems({**sample_idea_dict(), "title": "x" * 61, "parts_estimate": 0})
        self.assertIn("title is longer than 60 characters", problems)
        self.assertIn("parts_estimate must be an integer from 1 to 12", problems)

    def test_retired_judge_role_is_not_available(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary, None)
            completed = subprocess.run(
                [sys.executable, str(root / FINALIZER_FILE_NAME), "--role", "judge"],
                cwd=root, capture_output=True, text=True, timeout=60, check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("unrecognized arguments", completed.stderr)
            self.assertFalse((root / "agent-outcome.json").exists())

    def test_finalizer_stays_standard_library_only(self):
        source = finalizer_bytes().decode("utf-8")
        self.assertNotIn("import workshop", source)
        self.assertNotIn("from workshop", source)
        self.assertEqual(finalize_daydream.DAYDREAM_OUTCOME_KIND, DAYDREAM_OUTCOME_KIND)


if __name__ == "__main__":
    unittest.main()
