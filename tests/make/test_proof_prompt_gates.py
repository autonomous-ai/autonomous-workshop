"""design-a-toy's Contract Proof runs Make's own print gates through
make_round --print-gates-only, never the CAD skill's gates by hand, so a
contract whose Proof passes cannot fail Make's gates for a reason the Proof
never measured (owner, 2026-10-28)."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROOF_PROMPT = REPO / ".claude" / "skills" / "design-a-toy" / "proof-prompt.md"


class ProofPromptTest(unittest.TestCase):
    def test_the_proof_runs_makes_gates_through_make_round(self):
        text = PROOF_PROMPT.read_text(encoding="utf-8")
        self.assertIn("make-round/scripts/make_round <OUT> --print-gates-only", text)
        self.assertIn("--contract <CONTRACT>", text)
        self.assertIn("print_parts()", text)
        # The Proof no longer calls the CAD gates itself.
        for gate in ("scripts/check_mesh", "scripts/check_overhang", "scripts/check_thickness"):
            self.assertNotIn(gate, text)
        self.assertIn("At the limit", text)
        self.assertIn("52", text)



if __name__ == "__main__":
    unittest.main()
