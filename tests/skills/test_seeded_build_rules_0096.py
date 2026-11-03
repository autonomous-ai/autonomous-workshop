"""ADR 0096 phase 4: the instructions a seeded build follows.

Contract: build-a-toy passes `--seed-source <contract-dir>/proof` to both
`wish` and `fix`, re-seals a kept Proof after a root amendment (within
tolerance without the owner, over tolerance on their approval), and shows the
owner every seed deviation before publishing. DETECT raises `shape:<geometry>`
from proof_diff for schema 11 and drops its `extents:` and form rows. The
product-run Make reference sends only a seeded run to `make-seeded.md`,
which has the root run approved rounds and spawn workers only for a
deviation, and the host refreshes it with make.md."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = (ROOT / ".claude/skills/build-a-toy/SKILL.md").read_text()
DETECT = (ROOT / ".claude/skills/build-a-toy/DETECT.md").read_text()
REFERENCES = ROOT / ".agents/product-run/.agents/skills/autonomous-workshop/references"


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class SeededBuildRulesTest(unittest.TestCase):
    def test_wish_and_fix_take_the_seed(self):
        text = _squash(BUILD)
        self.assertIn("add `--seed-source <contract-dir>/proof`", text)
        self.assertIn("A seeded toy's correction takes `--seed-source <contract-dir>/proof` too", text)

    def test_a_root_amendment_re_seals_the_kept_proof(self):
        text = _squash(BUILD)
        self.assertIn("rebuild and re-seal the kept Proof", text)
        self.assertIn("Within tolerance, re-seal with `seal_proof.py seal` without waiting for the owner", text)
        self.assertIn("re-seal only on their approval", text)

    def test_seed_deviations_are_shown_before_publishing(self):
        self.assertIn("show the owner every `seed_deviations` entry", _squash(BUILD))

    def test_detect_reads_the_approved_proof_for_schema_11(self):
        text = _squash(DETECT)
        self.assertIn("| `shape:<geometry>` | geometry | schema 11", text)
        self.assertIn("Raise no `extents:` and no form-requirement findings for it", text)
        self.assertIn("workshop.make.proof_diff <contract-dir>/proof/approved/part_<role>.step", text)

    def test_only_a_seeded_run_reads_the_seeded_reference(self):
        make = _squash((REFERENCES / "make.md").read_text())
        self.assertIn("A seeded run (`MAKE-OPTIONS.json` has `seed`): [make-seeded.md](make-seeded.md)", make)
        seeded = _squash((REFERENCES / "make-seeded.md").read_text())
        self.assertIn("Run one component round per Component yourself", seeded)
        self.assertIn("spawn one Component Worker for that Component only", seeded)
        self.assertIn("Never rule on shape", seeded)

    def test_the_host_refreshes_it_with_make(self):
        from workshop.workflow.agent_run import MAKE_COMPANION_REFERENCES

        self.assertIn("references/make-seeded.md", MAKE_COMPANION_REFERENCES)


if __name__ == "__main__":
    unittest.main()


class PilotFollowupRulesTest(unittest.TestCase):
    """B12 and B16 (ADR 0096 pilot, build round 0)."""

    def test_detect_measures_the_true_envelope(self):
        text = _squash(DETECT)
        self.assertIn('uv run python -m workshop.make.envelope "$R/step/<file>.step"', text)
        self.assertIn("Do not use `inspect refs --facts` for extents", text)
        self.assertNotIn("entryFacts", text)

    def test_detect_reads_a_carried_reviews_requirement_rows(self):
        text = _squash(DETECT)
        self.assertIn('`carried_from: "seed-approval"`', text)
        self.assertIn("`requirements[{id, verdict, note}]`", text)
        self.assertIn('`verdict: "agree"` is `passed: "requirement:<id>"`', text)
        self.assertIn('`verdict: "differences"` is passed only when `open_lines_approved` is true', text)

    def test_make_names_the_toy_from_the_name_line(self):
        make = _squash((REFERENCES / "make.md").read_text())
        self.assertIn("Name this toy exactly: <name>.", make)
