"""ADR 0096 beaver pilot (2026-11-02): the design rules it found missing.

Contract: design-a-toy writes schema 11 and CONTRACT-FORMAT documents it
(`shape`, optional prose sections, the seeded build, validation); an
amended concept gets three new views drawn from it, and counts are held by
retries and per-view counting; every Concept Checklist trait is required
(owner rule, 2026-11-02) and the owner is asked, with a pictured trade-off,
only about a trait the Proof or critic finds cannot be made, their answer
becoming its mark; a Proof from before ADR
0096 has a migration path into Make's layout; fits come from the wiki,
groove ends from the print-details library, and pins and springs are Bought
Parts, not stdparts."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / ".claude/skills/design-a-toy"


def _text(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


SKILL = _text(DESIGN / "SKILL.md")
FORMAT = _text(ROOT / ".claude/skills/build-a-toy/CONTRACT-FORMAT.md")


class PilotRulesTest(unittest.TestCase):
    def test_new_contracts_are_schema_11(self):
        self.assertIn('Write the block as `"schema_version": 11` with `"shape": "approved-proof"`', SKILL)
        self.assertNotIn('Write the block as `"schema_version": 9`', SKILL)
        self.assertIn('`11` (ADR 0096) is schema 10 plus `shape: "approved-proof"`', FORMAT)
        self.assertIn("- `shape` (schema 11, ADR 0096, required there and refused before it)", FORMAT)
        self.assertIn("`design-a-toy` writes every new contract as schema 11.", FORMAT)
        self.assertNotIn("writes every new contract as schema 9", FORMAT)

    def test_an_amended_concept_gets_new_views_and_counts_are_held(self):
        self.assertIn("draw the three views again from the amended concept", SKILL)
        self.assertIn("Never edit the old views one by one", SKILL)
        self.assertIn("generate three or four sheets and keep the first whose every view holds every count", SKILL)

    def test_every_trait_is_required_and_only_a_trait_at_risk_asks_the_owner(self):
        # Owner rule 2026-11-02: no Stage 1 marking, no proposed marks.
        self.assertNotIn("(proposed)", SKILL)
        self.assertNotIn("The owner marks it here", SKILL)
        self.assertIn("Do not ask the owner to mark the checklist and do not propose a changeable mark", SKILL)
        self.assertIn("**Trait at risk.** When the Proof's findings or the critic show that a checklist trait cannot be made", SKILL)
        self.assertIn("Show the trade-off in pictures", SKILL)
        self.assertIn("Write the owner's answer into that trait's \"owner\" cell", SKILL)
        self.assertIn("Never change a mark without the owner", SKILL)
        critic = _text(DESIGN / "critic-prompt.md")
        self.assertNotIn("changeable", critic)
        self.assertNotIn("(proposed)", critic)
        self.assertIn("list it under **Trait at risk** instead of as a difference", critic)
        self.assertIn("no trait is lost or at risk", critic)
        checklist = _text(DESIGN / "checklist-prompt.md")
        self.assertIn('Write "required" in every "owner" cell', checklist)
        proof = _text(DESIGN / "proof-prompt.md")
        self.assertIn('list it under "Trait at risk"', proof)
        self.assertIn("Never drop or change the trait yourself: the owner decides", proof)
        adr = _text(next((ROOT / "docs/adr").glob("0096-*.md")))
        self.assertIn("Amended 2026-11-02 (owner rule): every trait is required by default", adr)

    def test_a_pre_0096_proof_has_a_migration_path(self):
        self.assertIn("**A Proof from before ADR 0096.**", SKILL)
        self.assertIn("run `--shared-helpers --contract` until it freezes", SKILL)

    def test_library_numbers_and_bought_parts(self):
        self.assertIn('a press fit for the 1.5 mm steel pin is a 1.4 bore', FORMAT)
        self.assertIn('never "a flat end"', FORMAT)
        proof = _text(DESIGN / "proof-prompt.md")
        self.assertIn("A pin, spring, magnet, cork disc or other bought item has no `stdpart`", proof)


if __name__ == "__main__":
    unittest.main()
