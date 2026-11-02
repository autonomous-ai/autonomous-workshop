"""ADR 0096 Phase 1: the Contract Proof is the build the owner approves.

Contract: the Proof prompt reads the images, the concept and the Concept
Checklist from round 1, follows Make's authoring rules by pointing at their
homes (which exist) instead of copying them, lists guesses only for contract
fields and splits gate failures; one Proof Critic with a fixed CRITIC.json
schema judges the shape; a fresh checklist subagent sees only the concept;
SKILL.md wires the checklist into Stage 1 and opens Stage 4 with the concept
beside the Proof."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / ".claude/skills/design-a-toy"


def flat(path: Path) -> str:
    return " ".join(path.read_text().split())


class ProofPromptTest(unittest.TestCase):
    def setUp(self):
        self.prompt = flat(DESIGN / "proof-prompt.md")

    def test_it_builds_from_the_images_from_round_one(self):
        self.assertIn("You build the toy the owner will approve and Workshop will ship", self.prompt)
        self.assertIn("`CONCEPT-CHECKLIST.md`", self.prompt)
        self.assertIn("the images own the shape", self.prompt)
        for removed in ("the contract has to stand on its words", "Read only the Design Contract",
                        "you do not design", "Free choices"):
            with self.subTest(removed=removed):
                self.assertNotIn(removed, self.prompt)

    def test_make_rule_homes_are_named_and_exist(self):
        homes = [h.split(" ")[0] for h in re.findall(r"`((?:\.agents|src)/[^`]+)`", self.prompt)]
        for required in (".agents/product-run/.agents/skills/autonomous-workshop/references/make.md",
                         "src/workshop/make/agents/component-worker.toml",
                         "src/workshop/make/skills/wiki/scripts/wiki",
                         "src/workshop/make/skills/cad/scripts/stdpart",
                         "src/workshop/make/skills/image-to-cad/SKILL.md"):
            with self.subTest(home=required):
                self.assertIn(required, homes)
        for home in homes:
            path = home.rstrip(".,")
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).exists(), path)

    def test_every_install_and_freeze_uses_an_out_of_run_contract_input(self):
        for command in ("print_details.py --install <OUT>",
                        "--install-print <OUT> --contract <CONTRACT>",
                        "kit_tree.py --install <OUT> --contract <CONTRACT>",
                        "make_round <OUT> --shared-helpers --contract <CONTRACT>",
                        "make_round <OUT> --print-gates-only"):
            with self.subTest(command=command):
                self.assertIn(command, self.prompt)
        self.assertNotRegex(self.prompt, r"--install(-print)? <OUT> --wish")

    def test_guesses_are_contract_fields_and_gate_failures_split(self):
        self.assertIn("only for a number that falls in a contract field", self.prompt)
        self.assertIn("A shape number stays in the Proof", self.prompt)
        self.assertIn('"Image vs contract"', self.prompt)
        self.assertIn('"Shape repairs"', self.prompt)
        self.assertIn("A failure forced by a contract value stays a finding", self.prompt)
        self.assertIn('"Refused detail"', self.prompt)
        self.assertIn("Never its Step 5 or Step 8", self.prompt)
        self.assertIn("refused details, wiki citations and shape repairs", self.prompt)

    def test_the_kept_findings_rules_remain(self):
        self.assertIn("one fact stated in two places with two values", self.prompt)
        self.assertIn('Under a heading "Placement"', self.prompt)
        self.assertIn("rewrite `GUESSES.md` and `FINDINGS.md` from scratch", self.prompt)


class CriticAndChecklistTest(unittest.TestCase):
    def test_the_critic_has_the_reviewer_verdicts_and_a_schema(self):
        critic = flat(DESIGN / "critic-prompt.md")
        for required in ("never read or write the Proof's code", "**Reference Conflict**",
                         "**camera mismatch**", "**Close look.**", "stops after 5",
                         "one verdict per requirement id", "`<OUT>/CRITIC.json`",
                         '"schema_version": 1', '"close_looks"', '"checklist"', '"requirements"',
                         "A lost required trait is a difference"):
            with self.subTest(required=required):
                self.assertIn(required, critic)

    def test_the_checklist_reader_sees_only_the_concept(self):
        checklist = flat(DESIGN / "checklist-prompt.md")
        self.assertIn("Look only at the chosen Concept Image", checklist)
        self.assertIn("Read no contract", checklist)
        self.assertIn("8 to 12 traits", checklist)
        self.assertIn("required or changeable", checklist)


class SkillWiringTest(unittest.TestCase):
    def setUp(self):
        self.skill = flat(DESIGN / "SKILL.md")

    def test_stage_one_writes_and_marks_the_checklist(self):
        stage = self.skill[self.skill.index("### The chosen Concept Image"):self.skill.index("## Stage 2 ")]
        self.assertIn("[checklist-prompt.md](checklist-prompt.md)", stage)
        self.assertIn("is marked required or changeable", stage)

    def test_stage_four_opens_with_the_concept_beside_the_proof(self):
        stage = self.skill[self.skill.index("## Stage 4"):self.skill.index("## Stage 5")]
        self.assertIn("Open the page with the chosen Concept Image beside the Contract Proof", stage)
        self.assertIn('"this is what ships"', stage)
        self.assertNotIn("with a fresh read", stage)

    def test_the_proof_is_no_longer_kept_apart_from_the_build(self):
        self.assertNotIn("A Proof is never a Reference Image", self.skill)
        self.assertNotIn("modelled from the contract alone", self.skill)
        self.assertIn("[critic-prompt.md](critic-prompt.md)", self.skill)


if __name__ == "__main__":
    unittest.main()
