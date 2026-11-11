"""ADR 0102: the instructions a seed deviation's review follows.

Contract: the Component Reviewer's instructions describe an approved-proof
packet (the approved Component beside the changed one, no reference image,
`matches_approved`, `{feature, approved, model}`, no camera mismatch or
Reference Conflict); the Component Worker of such a run views no reference
image and repairs toward the approved source and STEP; the seeded Make
reference and the make-round skill say the same; build-a-toy shows each
visible deviation beside the approved Proof render; and the ADR is indexed."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(*parts: str) -> str:
    return re.sub(r"\s+", " ", ROOT.joinpath(*parts).read_text(encoding="utf-8"))


class SeedReviewRulesTest(unittest.TestCase):
    def test_the_reviewer_compares_with_the_approved_component(self):
        reviewer = _text("src/workshop/make/agents/component-reviewer.toml")
        for required in (
            'When the packet has `basis: "approved-proof"`',
            "no reference image is in the packet, and you open none",
            "does the changed Component still look like the approved one, apart from what the forcing gate needed?",
            '"approved": "<what the approved render shows>"',
            "Answer `matches_plan` and `matches_approved`",
            "There is no camera mismatch and no Reference Conflict for such a packet",
        ):
            with self.subTest(required=required):
                self.assertIn(required, reviewer)

    def test_the_worker_views_no_reference_in_such_a_run(self):
        worker = _text("src/workshop/make/agents/component-worker.toml")
        self.assertIn('`review: "approved-proof"` (ADR 0102), view no reference image at all', worker)
        self.assertIn("repair toward the approved shape", worker)

    def test_the_seeded_make_reference_and_the_skill_say_so(self):
        seeded = _text(".agents/product-run/.agents/skills/autonomous-workshop/references/make-seeded.md")
        self.assertIn("that review is against the Approved Proof, not a Reference Image", seeded)
        self.assertIn("never toward a reference image", seeded)
        skill = _text("src/workshop/make/skills/make-round/SKILL.md")
        self.assertIn("binds no reference image", skill)
        self.assertIn('`{"feature", "approved", "model"}`', skill)

    def test_build_a_toy_shows_a_visible_deviation_beside_the_approved_render(self):
        build = _text(".claude/skills/build-a-toy/SKILL.md")
        self.assertIn("beside the approved Proof render, never beside a reference image (ADR 0102)", build)

    def test_the_adr_is_indexed_and_the_glossary_names_it(self):
        self.assertIn("0102-seed-deviations-are-reviewed-against-the-approved-proof.md",
                      _text("docs/adr/README.md"))
        context = _text("CONTEXT.md")
        self.assertIn("**Seed Deviation**:", context)
        self.assertIn("a new seeded build reads none (ADR 0102)", context)


if __name__ == "__main__":
    unittest.main()
