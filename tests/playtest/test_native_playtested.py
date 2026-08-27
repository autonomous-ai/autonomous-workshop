import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import NativeInvented
from workshop.playtest import Feedback
from workshop.make.native import NativeMade
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    InventorRoster,
    InventorRosterEntry,
)
from workshop.playtest.native import NativePlaytestCheck, NativePlaytested
from workshop.product import ToyBlueprint


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class NativePlaytestedTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_root = Path(self.temporary.name).resolve()
        self.blueprint = ToyBlueprint()
        roster = InventorRoster(
            (
                InventorRosterEntry(
                    "eve",
                    ".codex/agents/eve.toml",
                    "b" * 64,
                    "c" * 64,
                    "d" * 64,
                ),
            )
        )
        self.assignment = NativeMatchAssignment(
            wish_sha256="a" * 64,
            inventor_roster_sha256=roster.roster_sha256,
            selected_inventor_id="eve",
            selected_agent_path=".codex/agents/eve.toml",
            selected_agent_sha256="b" * 64,
            selected_source_manifest_sha256="c" * 64,
            selected_taste_sha256="d" * 64,
            blueprint_sha256=self.blueprint.sha256,
            ranking=(
                MatchRankingEntry(
                    "eve", "The Wish is a specific place made into a tiny world."
                ),
            ),
        )
        self.invented = NativeInvented(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept={"title": "Moon Nook", "summary": "A tiny lunar observatory."},
            research={
                "sources": [
                    {"url": "https://example.test/moon", "claim": "scale"}
                ]
            },
        )
        self.made = self._make_product()

    def _make_product(self) -> NativeMade:
        product_root = self.run_root / "artifacts/make/r0001/product"
        (product_root / "cad/project").mkdir(parents=True)
        (product_root / "validation").mkdir()
        product = {
            "title": "Moon Nook",
            "summary": "A tiny lunar observatory.",
        }
        product_bytes = (
            json.dumps(product, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        receipt = b'{"ok":true,"validator":"cad-final"}\n'
        (product_root / "product.json").write_bytes(product_bytes)
        (product_root / "cad/project/moon.step.py").write_text("pass\n")
        (product_root / "cad/project/moon.step").write_bytes(b"ISO-10303-21;\n")
        (product_root / "cad/project/moon.stl").write_bytes(
            b"solid moon\nendsolid moon\n"
        )
        (product_root / "validation/cad-build.json").write_bytes(receipt)
        return NativeMade(
            round=1,
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            invented_sha256=self.invented.invented_sha256,
            product_root="artifacts/make/r0001/product",
            cad_project_path="cad/project",
            product_manifest=build_artifact_manifest(
                product_root, created_at="content-addressed"
            ),
            product=product,
            product_json_sha256=_sha(product_bytes),
            cad_verification_path="validation/cad-build.json",
            cad_verification_sha256=_sha(receipt),
        )

    def _playtested(self, *, verdict="pass", failed=None) -> NativePlaytested:
        evidence_root = self.run_root / "artifacts/playtest/r0001/evidence"
        evidence_root.mkdir(parents=True, exist_ok=True)
        checks = []
        for check_id in self.blueprint.required_playtest_checks():
            content = (json.dumps({"check": check_id, "ok": check_id != failed}) + "\n").encode()
            path = "%s.json" % check_id
            (evidence_root / path).write_bytes(content)
            checks.append(
                NativePlaytestCheck(
                    check_id=check_id,
                    passed=check_id != failed,
                    evaluator="workshop-host",
                    evaluator_version="1.0.0",
                    config_sha256="d" * 64,
                    evidence_ref=path,
                    evidence_sha256=_sha(content),
                    observed_at="2026-08-26T00:00:00Z",
                    observations={"ok": check_id != failed},
                )
            )
        feedback = ()
        if failed is not None:
            feedback = (
                Feedback(
                    code="fix-%s" % failed,
                    area="playtest",
                    severity="improve",
                    finding="The check failed.",
                    change="Revise the product and rerun the check.",
                    evidence_refs=("%s.json" % failed,),
                ),
            )
        return NativePlaytested(
            round=1,
            made_sha256=self.made.made_sha256,
            product_artifact_sha256=self.made.product_manifest.artifact_sha256,
            blueprint_sha256=self.blueprint.sha256,
            evidence_root="artifacts/playtest/r0001/evidence",
            evidence_manifest=build_artifact_manifest(
                evidence_root, created_at="content-addressed"
            ),
            checks=tuple(checks),
            feedback=feedback,
            verdict=verdict,
        )

    def test_round_trip_covers_blueprint_and_rehashes_evidence(self):
        playtested = self._playtested()

        rebuilt = NativePlaytested.from_mapping(playtested.to_dict())
        rebuilt.assert_context(self.made, self.blueprint)
        canonical = rebuilt.validate_evidence_tree(self.run_root, self.made)

        self.assertTrue(canonical.passed)
        self.assertEqual(
            {item.playtest_id for item in canonical.evidence.results},
            set(self.blueprint.required_playtest_checks()),
        )

    def test_tamper_missing_check_and_false_pass_fail_closed(self):
        playtested = self._playtested()
        evidence = self.run_root / "artifacts/playtest/r0001/evidence/agent-playtest.json"
        evidence.write_text('{"changed":true}\n')
        with self.assertRaisesRegex(ArtifactError, "differs from its manifest"):
            playtested.validate_evidence_tree(self.run_root, self.made)

        with self.assertRaisesRegex(ContractError, "incomplete inputs"):
            NativePlaytested(
                round=1,
                made_sha256=self.made.made_sha256,
                product_artifact_sha256=self.made.product_manifest.artifact_sha256,
                blueprint_sha256=self.blueprint.sha256,
                evidence_root=playtested.evidence_root,
                evidence_manifest=playtested.evidence_manifest,
                checks=playtested.checks[:-1],
                feedback=(),
                verdict="pass",
            ).assert_context(self.made, self.blueprint)

        with self.assertRaisesRegex(ContractError, "cannot contain failures"):
            self._playtested(verdict="pass", failed="agent-playtest")

    def test_host_reads_make_targeted_feedback_but_rejects_upstream_stages(self):
        accepted = Feedback(
            code="repair-snap",
            area="make",
            severity="improve",
            finding="The snap geometry failed Playtest.",
            change="Revise the snap in the next Make attempt.",
            evidence_refs=("mechanical-check.json",),
            invalidates=("make", "playtest", "release"),
        )

        self.assertEqual(
            accepted.invalidates,
            ("make", "playtest", "release"),
        )
        with self.assertRaisesRegex(ContractError, "outside the Make repair loop"):
            Feedback(
                code="restart-invent",
                area="invent",
                severity="block",
                finding="The concept should be replaced.",
                change="Return to Invent.",
                invalidates=("invent",),
            )


if __name__ == "__main__":
    unittest.main()
