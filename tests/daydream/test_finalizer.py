import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.daydream.support import sample_idea_dict
from workshop.daydream import finalize_daydream
from workshop.daydream.native import DAYDREAM_OUTCOME_KIND, FINALIZER_FILE_NAME, finalizer_bytes


class FinalizerTest(unittest.TestCase):
    def _root(self, temporary, idea):
        root = Path(temporary) / "workspace"
        (root / "work").mkdir(parents=True)
        (root / FINALIZER_FILE_NAME).write_bytes(finalizer_bytes())
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

    def test_judge_role_validates_the_verdict(self):
        from tests.daydream.support import build_verdict_dict

        with tempfile.TemporaryDirectory() as temporary:
            root = self._root(temporary, None)
            (root / "work" / "VERDICT.json").write_text(
                json.dumps(build_verdict_dict("dream-again")), encoding="utf-8"
            )
            completed = subprocess.run(
                [sys.executable, str(root / FINALIZER_FILE_NAME), "--role", "judge"],
                cwd=root, capture_output=True, text=True, timeout=60, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            outcome = json.loads((root / "agent-outcome.json").read_text(encoding="utf-8"))
            self.assertEqual(outcome["role"], "judge")
            self.assertEqual(outcome["idea_path"], "work/VERDICT.json")
            self.assertEqual(outcome["title"], "dream-again")
            bad = build_verdict_dict("dream-again")
            bad["risks"] = [{"kind": "vibes", "detail": "meh"}]
            (root / "work" / "VERDICT.json").write_text(json.dumps(bad), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(root / FINALIZER_FILE_NAME), "--role", "judge"],
                cwd=root, capture_output=True, text=True, timeout=60, check=False,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("risks[0].kind must be one of", completed.stderr)

    def test_finalizer_stays_standard_library_only(self):
        source = finalizer_bytes().decode("utf-8")
        self.assertNotIn("import workshop", source)
        self.assertNotIn("from workshop", source)
        self.assertEqual(finalize_daydream.DAYDREAM_OUTCOME_KIND, DAYDREAM_OUTCOME_KIND)


if __name__ == "__main__":
    unittest.main()
