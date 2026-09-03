import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from tests.daydream.support import build_thesis_verdict_dict, sample_thesis_dict
from workshop.daydream.contracts import DaydreamError, Idea, Verdict
from workshop.daydream.notebook import (
    JudgeMemory,
    NotebookEntry,
    StructuralTrace,
    append_notebook_entry,
    prior_work_from_notebook,
    read_notebook,
    render_notebook_markdown,
)
from workshop.errors import ContractError


def _entry(index: int, status: str = "dreamed") -> NotebookEntry:
    return NotebookEntry(
        daydream_id="daydream-20260902-1015%02d-%08x" % (index, index),
        created_at="2026-09-02T10:15:%02dZ" % index,
        title="Idea %d" % index,
        one_liner="One line about idea %d." % index,
        idea_sha256="%064x" % index,
        status=status,
    )


class NotebookTest(unittest.TestCase):
    def test_append_and_read_round_trip_as_a_private_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "NOTEBOOK.jsonl"
            self.assertEqual(read_notebook(path), ())
            append_notebook_entry(path, _entry(1))
            append_notebook_entry(path, _entry(2, "rejected"))
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(read_notebook(path), (_entry(1), _entry(2, "rejected")))
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0]), _entry(1).to_dict())

    def test_append_repairs_a_torn_tail(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "NOTEBOOK.jsonl"
            append_notebook_entry(path, _entry(1))
            with open(path, "ab") as handle:
                handle.write(json.dumps(_entry(2).to_dict()).encode("utf-8")[:-4])
            append_notebook_entry(path, _entry(3))
            self.assertEqual(read_notebook(path), (_entry(1), _entry(3)))

    def test_malformed_lines_are_skipped_and_limit_keeps_the_newest(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "NOTEBOOK.jsonl"
            append_notebook_entry(path, _entry(1))
            with path.open("a", encoding="utf-8") as handle:
                handle.write("{not json\n")
                handle.write(json.dumps({"daydream_id": "x"}) + "\n")
                handle.write("[1, 2]\n")
                handle.write("\n")
            append_notebook_entry(path, _entry(2))
            append_notebook_entry(path, _entry(3))
            self.assertEqual(read_notebook(path), (_entry(1), _entry(2), _entry(3)))
            self.assertEqual(read_notebook(path, limit=2), (_entry(2), _entry(3)))
            with self.assertRaises(ContractError):
                read_notebook(path, limit=0)

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_symlinked_notebook_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "real.jsonl").write_text("", encoding="utf-8")
            os.symlink(root / "real.jsonl", root / "NOTEBOOK.jsonl")
            with self.assertRaises(DaydreamError):
                append_notebook_entry(root / "NOTEBOOK.jsonl", _entry(1))
            with self.assertRaises(DaydreamError):
                read_notebook(root / "NOTEBOOK.jsonl")

    def test_entry_validation(self):
        with self.assertRaises(ContractError):
            NotebookEntry.parse({**_entry(1).to_dict(), "extra": 1})
        with self.assertRaises(ContractError):
            _entry(1, "liked")
        with self.assertRaises(ContractError):
            append_notebook_entry(Path("/nonexistent"), _entry(1).to_dict())

    def test_markdown_and_prior_work_projection(self):
        text = render_notebook_markdown((_entry(1), _entry(2, "rejected")))
        self.assertTrue(
            text.startswith("# Your notebook (ideas you already had — do not repeat)\n")
        )
        self.assertIn(
            "- **Idea 2** (daydream-20260902-101502-00000002, rejected, "
            "2026-09-02T10:15:02Z): One line about idea 2.",
            text,
        )
        self.assertIn("(empty: this is your first daydream)", render_notebook_markdown(()))
        prior = prior_work_from_notebook((_entry(1),))
        self.assertEqual(prior[0].source, "notebook:daydream-20260902-101501-00000001")
        self.assertEqual(prior[0].title, "Idea 1")
        self.assertEqual(prior[0].summary, "One line about idea 1.")

    def test_schema_v2_retains_structure_and_judge_repair_advice(self):
        idea = Idea.parse(sample_thesis_dict())
        verdict = Verdict.parse(build_thesis_verdict_dict("dream-again"))
        entry = NotebookEntry(
            daydream_id="daydream-20260902-101501-00000001",
            created_at="2026-09-02T10:15:01Z",
            title=idea.title,
            one_liner=idea.one_liner,
            idea_sha256=idea.sha256,
            status="judged",
            schema_version=2,
            structure=StructuralTrace.from_idea(idea),
            judge=JudgeMemory.from_verdict(verdict),
        )
        self.assertEqual(NotebookEntry.parse(entry.to_dict()), entry)
        text = render_notebook_markdown((entry,))
        self.assertIn("Anti-generic signature:", text)
        self.assertIn("Judge prediction: dream-again", text)
        self.assertIn("proof_observable", text)
        self.assertIn(verdict.advice, text)
        tampered = entry.to_dict()
        tampered["structure"]["action"] = "A different action."
        with self.assertRaisesRegex(ContractError, "sha256"):
            NotebookEntry.parse(tampered)

    def test_schema_v2_retains_deterministic_rejection_reason(self):
        idea = Idea.parse(sample_thesis_dict())
        entry = NotebookEntry(
            daydream_id="daydream-20260902-101501-00000001",
            created_at="2026-09-02T10:15:01Z",
            title=idea.title,
            one_liner=idea.one_liner,
            idea_sha256=idea.sha256,
            status="rejected",
            schema_version=2,
            structure=StructuralTrace.from_idea(idea),
            rejection_reason="too close to an existing structural promise",
        )
        self.assertEqual(NotebookEntry.parse(entry.to_dict()), entry)
        self.assertIn(
            "Deterministic novelty rejection: too close",
            render_notebook_markdown((entry,)),
        )


if __name__ == "__main__":
    unittest.main()
