"""ADR 0094: design-a-toy checks through the Contract Proof, and detection reads Make's gates."""

import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
DESIGN = REPOSITORY / ".claude" / "skills" / "design-a-toy"
BUILD = REPOSITORY / ".claude" / "skills" / "build-a-toy"


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class DesignFlowTest(unittest.TestCase):
    def setUp(self):
        self.skill = flat(DESIGN / "SKILL.md")

    def stage(self, start: str, end: str) -> str:
        return self.skill[self.skill.index(start):self.skill.index(end)]

    def test_one_proof_subagent_is_kept_and_one_fresh_read_closes_it(self):
        proof = self.stage("## Stage 3a", "### Trial")
        for required in (
            "Keep this one subagent for the whole design: every amendment goes to it",
            "**Fresh read.**",
            "spawn one **fresh** Proof subagent with the same prompt",
            "never after a change of words alone",
            "in every `build-a-toy` root amendment",
        ):
            with self.subTest(required=required):
                self.assertIn(required, proof)

    def test_lint_claims_and_audit_stage_is_gone(self):
        self.assertNotIn("## Stage 3e", self.skill)
        self.assertNotIn("Stage 3e", flat(BUILD / "SKILL.md"))
        self.assertFalse((DESIGN / "audit-prompt.md").exists())
        self.assertFalse((DESIGN / "claims-prompt.md").exists())
        prompt = flat(DESIGN / "proof-prompt.md")
        self.assertIn("one fact stated in two places with two values", prompt)
        self.assertIn('Under a heading "Placement"', prompt)

    def test_images_are_reconciled_from_the_proof_compare(self):
        stage = self.stage("## Stage 3b", "### Guide Images")
        self.assertIn("reconcile every image with the drafted contract from its Stage 3a compare", stage)
        self.assertIn("Do not measure the image by hand for what the Proof draws", stage)
        for check in ("**Reference Camera.**", "**Joint features.**", "**Part colours**", "**Visible faces.**"):
            with self.subTest(check=check):
                self.assertIn(check, stage)

    def test_45_degrees_is_the_only_overhang_limit(self):
        stage = self.stage("## Stage 3c", "## Stage 3d")
        self.assertIn("45 is the only limit", stage)
        self.assertNotIn("rises at 52 degrees", stage)
        self.assertIn("Its print gates are Make's own, run by Make's own code", stage)

    def test_no_likeness_gate_is_promised(self):
        for path in (DESIGN / "SKILL.md", BUILD / "SKILL.md", BUILD / "DETECT.md"):
            text = flat(path)
            with self.subTest(path=path.name):
                self.assertNotIn("likeness gate", text)
                self.assertNotIn("IoU >= 0.90", text)
                self.assertNotIn("--min 0.90", text)


class DetectionTest(unittest.TestCase):
    def test_detection_reads_make_print_gates_not_wall_min(self):
        detect = flat(BUILD / "DETECT.md")
        self.assertIn("| `print:<geometry>` | print |", detect)
        self.assertNotIn("`wall:<geometry>`", detect)
        self.assertNotIn("`likeness:<ref-stem>`", detect)
        self.assertIn("Read `<toy-dir>/make/verification/CAD-GATE.json`", detect)
        self.assertIn("never into `findings`", detect)


if __name__ == "__main__":
    unittest.main()
