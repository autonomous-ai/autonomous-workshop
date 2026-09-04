import tempfile
import unittest
from pathlib import Path

from tests.daydream.support import sample_thesis_dict
from workshop.daydream.contracts import Idea
from workshop.daydream.notebook import NotebookEntry, StructuralTrace, append_notebook_entry
from workshop.daydream.portfolio import (
    PortfolioEntry,
    load_portfolio,
    prior_work_from_portfolio,
    render_portfolio_markdown,
)
from workshop.errors import ContractError


def _memory(daydream_id: str) -> NotebookEntry:
    idea = Idea.parse(sample_thesis_dict())
    return NotebookEntry(
        daydream_id=daydream_id,
        created_at="2026-09-02T10:15:00Z",
        title=idea.title,
        one_liner=idea.one_liner,
        idea_sha256=idea.sha256,
        status="dreamed",
        schema_version=2,
        structure=StructuralTrace.from_idea(idea),
    )


class PortfolioTest(unittest.TestCase):
    def test_projects_other_inventor_notebooks_with_structure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "daydreams"
            for inventor, suffix in (("alpha", "00000001"), ("beta", "00000002")):
                folder = root / inventor
                folder.mkdir(parents=True)
                append_notebook_entry(
                    folder / "NOTEBOOK.jsonl",
                    _memory("daydream-20260902-101500-%s" % suffix),
                )
            entries = load_portfolio(root, exclude_inventor="alpha")
            self.assertEqual([entry.inventor_id for entry in entries], ["beta"])
            self.assertIsInstance(entries[0], PortfolioEntry)
            text = render_portfolio_markdown(entries)
            self.assertIn("Workshop portfolio (all Inventors", text)
            self.assertIn("Anti-generic signature", text)
            prior = prior_work_from_portfolio(entries)
            self.assertEqual(
                prior[0].source,
                "portfolio:beta:daydream-20260902-101500-00000002",
            )
            self.assertIn(entries[0].memory.structure.action, prior[0].summary)

    def test_missing_empty_and_invalid_roots_are_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "missing"
            self.assertEqual(load_portfolio(root), ())
            self.assertIn("(none recorded yet)", render_portfolio_markdown(()))
            root.write_text("not a directory", encoding="utf-8")
            with self.assertRaises(ContractError):
                load_portfolio(root)
            with self.assertRaises(ContractError):
                prior_work_from_portfolio((_memory("daydream-20260902-101500-00000001"),))


if __name__ == "__main__":
    unittest.main()
