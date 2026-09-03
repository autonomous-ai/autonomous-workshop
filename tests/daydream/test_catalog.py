import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.daydream.support import horn_tip_paraphrase_dict, sample_idea, sample_idea_dict
from workshop.daydream.catalog import (
    NOVELTY_MAX_SIMILARITY,
    PriorWork,
    content_tokens,
    lint_novelty,
    load_repository_prior_work,
    normalize_title,
    render_prior_work_markdown,
    source_checkout_root,
)
from workshop.daydream.contracts import Idea
from workshop.errors import ContractError


REPOSITORY = Path(__file__).resolve().parents[2]


def _toy(root: Path, slug: str) -> Path:
    toy = root / "toys" / slug
    toy.mkdir(parents=True)
    return toy


class RepositoryPriorWorkTest(unittest.TestCase):
    def test_reads_wish_json_then_readme_and_skips_malformed_toys(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bound = _toy(root, "a-bound")
            (bound / "wish").mkdir()
            (bound / "wish" / "wish.json").write_text(
                json.dumps(
                    {
                        "public_title": "Bound Toy",
                        "public_summary": "Summary from the wish binding.",
                        "objective": "ignored when a summary exists",
                    }
                ),
                encoding="utf-8",
            )
            objective_only = _toy(root, "b-objective")
            (objective_only / "wish").mkdir()
            (objective_only / "wish" / "wish.json").write_text(
                json.dumps({"public_title": "Objective Toy", "objective": "The objective."}),
                encoding="utf-8",
            )
            readme_only = _toy(root, "c-readme")
            (readme_only / "README.md").write_text(
                "# Readme Toy\n\n![Readme Toy](renders/hero.png)\n\n"
                "First paragraph line one\nline two.\n\nSecond paragraph.\n",
                encoding="utf-8",
            )
            broken = _toy(root, "d-broken")
            (broken / "wish").mkdir()
            (broken / "wish" / "wish.json").write_text("{not json", encoding="utf-8")
            (broken / "README.md").write_text("no heading\n", encoding="utf-8")
            (root / "toys" / "e-file").write_text("not a directory", encoding="utf-8")
            _toy(root, "f-empty")
            too_big = _toy(root, "g-big")
            (too_big / "README.md").write_text(
                "# Big\n\n" + "x" * (64 * 1024), encoding="utf-8"
            )
            entries = load_repository_prior_work(root)
            self.assertEqual(
                [(entry.source, entry.title, entry.summary) for entry in entries],
                [
                    ("toys/a-bound", "Bound Toy", "Summary from the wish binding."),
                    ("toys/b-objective", "Objective Toy", "The objective."),
                    ("toys/c-readme", "Readme Toy", "First paragraph line one line two."),
                ],
            )

    @unittest.skipIf(not hasattr(os, "symlink"), "symlink unavailable")
    def test_symlinked_toys_are_skipped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real = _toy(root, "real")
            (real / "README.md").write_text("# Real\n\nA real toy.\n", encoding="utf-8")
            os.symlink(real, root / "toys" / "linked")
            self.assertEqual(
                [entry.source for entry in load_repository_prior_work(root)],
                ["toys/real"],
            )

    def test_missing_catalog_is_empty(self):
        self.assertEqual(load_repository_prior_work(None), ())
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(load_repository_prior_work(Path(temporary)), ())

    def test_source_checkout_root_finds_this_checkout(self):
        self.assertEqual(source_checkout_root(), REPOSITORY)
        entries = load_repository_prior_work(source_checkout_root())
        self.assertIn("Horn Tip", [entry.title for entry in entries])


class TokenTest(unittest.TestCase):
    def test_normalize_title_and_content_tokens(self):
        self.assertEqual(normalize_title("  Horn-Tip!!  Deluxe (v2) "), "horn tip deluxe v2")
        self.assertEqual(
            content_tokens("A tiny one-piece desk rocker; the horn tips, it's printed."),
            frozenset({"rocker", "horn", "tips"}),
        )
        self.assertEqual(content_tokens("the and of"), frozenset())


class NoveltyLintTest(unittest.TestCase):
    def setUp(self):
        self.prior = (
            PriorWork(
                source="toys/pico-press-horn-tip",
                title="Horn Tip",
                summary=(
                    "A tiny one-piece crescent desk rocker. Press a rounded horn with "
                    "a fingertip and it tips, then gravity walks it back to rest on "
                    "its outer curve."
                ),
            ),
            PriorWork(
                source="toys/bob-lunar-relay",
                title="Lunar Relay",
                summary=(
                    "A palm-sized, three-part printable desk mechanism whose exposed "
                    "rocker makes one cratered moon rise when the other is pressed."
                ),
            ),
        )

    def test_identical_title_is_too_close(self):
        raw = sample_idea_dict()
        raw["title"] = "  horn-tip "
        report = lint_novelty(Idea.parse(raw), self.prior)
        self.assertEqual(report.status, "too-close")
        self.assertEqual(report.max_similarity, 1.0)
        self.assertEqual(report.nearest[0].title, "Horn Tip")
        self.assertIn("Horn Tip", report.reason)

    def test_paraphrase_is_too_close(self):
        report = lint_novelty(Idea.parse(horn_tip_paraphrase_dict()), self.prior)
        self.assertEqual(report.status, "too-close")
        self.assertGreaterEqual(report.max_similarity, NOVELTY_MAX_SIMILARITY)
        self.assertEqual(report.nearest[0].source, "toys/pico-press-horn-tip")

    def test_different_idea_is_new_and_lists_nearest(self):
        report = lint_novelty(sample_idea(), self.prior)
        self.assertEqual(report.status, "new")
        self.assertLess(report.max_similarity, NOVELTY_MAX_SIMILARITY)
        self.assertEqual(len(report.nearest), 2)
        self.assertEqual(
            [entry.similarity for entry in report.nearest],
            sorted((entry.similarity for entry in report.nearest), reverse=True),
        )
        self.assertIn(report.nearest[0].title, report.reason)
        self.assertEqual(lint_novelty(sample_idea(), ()).nearest, ())
        self.assertEqual(lint_novelty(sample_idea(), ()).status, "new")

    def test_lint_requires_typed_inputs(self):
        with self.assertRaises(ContractError):
            lint_novelty(sample_idea_dict(), self.prior)
        with self.assertRaises(ContractError):
            lint_novelty(sample_idea(), [{"title": "x"}])

    def test_render_prior_work_markdown(self):
        text = render_prior_work_markdown(self.prior[:1])
        self.assertTrue(text.startswith("# Prior work (already exists — do not repeat)\n"))
        self.assertIn(
            "- **Horn Tip** (toys/pico-press-horn-tip): A tiny one-piece crescent", text
        )
        self.assertIn("(none recorded yet)", render_prior_work_markdown(()))


if __name__ == "__main__":
    unittest.main()
