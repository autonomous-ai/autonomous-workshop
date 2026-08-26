import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.invent.native import InventedV2
from workshop.make.native import NativeMade
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    PersonaCatalog,
    PersonaCatalogEntry,
)
from workshop.playtest.native import NativePlaytested
from workshop.product import ToyBlueprint
from workshop.release.native import NativeRelease
from workshop.workflow.proposals import AgentOutcomeProposal


REPOSITORY = Path(__file__).resolve().parents[2]
TOOL = (
    REPOSITORY
    / ".agents"
    / "skills"
    / "autonomous-workshop"
    / "scripts"
    / "stage_proposal.py"
)
LANES = (
    "classics-made-yours",
    "invented-games",
    "moving-machines",
    "holdable-science",
    "little-worlds",
)
FORWARD = {
    "match": "invent",
    "invent": "make",
    "make": "playtest",
    "playtest": "release",
    "release": "deliver",
}


def canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256(content):
    return hashlib.sha256(content).hexdigest()


class StageProposalToolTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_root = Path(self.temporary.name).resolve()
        self.blueprint = ToyBlueprint.for_lane("little-worlds")
        alice = PersonaCatalogEntry(
            "alice", "classics-made-yours", "a" * 64, "b" * 64
        )
        eve = PersonaCatalogEntry(
            "eve", "little-worlds", "c" * 64, "d" * 64
        )
        self.catalog = PersonaCatalog((alice, eve))
        self.assignment = NativeMatchAssignment(
            wish_sha256="e" * 64,
            persona_catalog_sha256=self.catalog.catalog_sha256,
            selected_inventor_id="eve",
            selected_lane="little-worlds",
            selected_manifest_sha256=eve.manifest_sha256,
            selected_taste_sha256=eve.taste_sha256,
            blueprint_sha256=self.blueprint.sha256,
            ranking=(
                MatchRankingEntry(
                    "eve", "The Wish asks for a specific coherent tiny world."
                ),
                MatchRankingEntry(
                    "alice", "The classic-edition lane is less direct for this Wish."
                ),
            ),
        )
        self.invented = InventedV2(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            lane=self.assignment.selected_lane,
            concept={
                "title": "Moon Nook",
                "summary": "A tiny lunar observatory shaped by the Wish.",
            },
            research={
                "sources": [
                    {
                        "url": "https://example.test/moon",
                        "claim": "The visible phases follow relative geometry.",
                    }
                ]
            },
        )

    def write_json(self, relative, value, *, canonical=False):
        path = self.run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        content = canonical_json(value) if canonical else json.dumps(value).encode()
        path.write_bytes(content)
        return path

    def write_stage(self, stage, inputs, *, round_index=None, writable=False):
        path = self.run_root / "STAGE.json"
        if path.exists() or path.is_symlink():
            path.unlink()
        document = {
            "schema_version": 1,
            "kind": "autonomous-workshop.stage-input",
            "product_id": "run-local-toy",
            "stage": stage,
            "checkpoint_sha256": "1" * 64,
            "subject_sha256": "2" * 64,
            "next_transition": FORWARD[stage],
            "round": round_index,
            "max_rounds": 4,
            "inputs": inputs,
        }
        path.write_bytes(canonical_json(document))
        path.chmod(0o600 if writable else 0o400)
        return document

    def run_tool(self, *arguments, expected=0):
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(TOOL),
                "--run-root",
                str(self.run_root),
                *arguments,
            ],
            cwd=self.run_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            expected,
            "stdout:\n%s\nstderr:\n%s" % (completed.stdout, completed.stderr),
        )
        return completed

    def assert_canonical_file(self, relative):
        content = (self.run_root / relative).read_bytes()
        document = json.loads(content.decode("utf-8"))
        self.assertEqual(content, canonical_json(document))
        return document, content

    def assert_outcome(self, stage, contract_path, contract_bytes, transition):
        document, _ = self.assert_canonical_file("agent-outcome.json")
        proposal = AgentOutcomeProposal.from_mapping(document)
        self.assertEqual(proposal.outcome.stage, stage)
        self.assertEqual(proposal.outcome.proposed_transition, transition)
        self.assertEqual(len(proposal.outcome.artifacts), 1)
        artifact = proposal.outcome.artifacts[0]
        self.assertEqual(artifact.path, contract_path)
        self.assertEqual(artifact.sha256, sha256(contract_bytes))
        self.assertEqual(proposal.checkpoint_sha256, "1" * 64)
        self.assertEqual(proposal.subject_sha256, "2" * 64)

    def match_inputs(self):
        return {
            "wish_sha256": self.assignment.wish_sha256,
            "persona_catalog": self.catalog.to_dict(),
            "blueprint_sha256_by_lane": {
                lane: ToyBlueprint.for_lane(lane).sha256 for lane in LANES
            },
        }

    def create_product(self):
        product_root = self.run_root / "artifacts/make/r0001/product"
        (product_root / "cad/project").mkdir(parents=True)
        (product_root / "validation").mkdir()
        product = {
            "title": "Moon Nook",
            "summary": "A tiny lunar observatory.",
            "lane": "little-worlds",
        }
        product_bytes = canonical_json(product) + b"\n"
        verification = b'{"ok":true,"validator":"cad-final"}\n'
        (product_root / "product.json").write_bytes(product_bytes)
        (product_root / "cad/project/moon.step.py").write_text("pass\n")
        (product_root / "cad/project/moon.step").write_bytes(b"ISO-10303-21;\n")
        (product_root / "cad/project/moon.stl").write_bytes(
            b"solid moon\nendsolid moon\n"
        )
        (product_root / "validation/cad-build.json").write_bytes(verification)
        return product_root, product, product_bytes, verification

    def create_made(self):
        product_root, product, product_bytes, verification = self.create_product()
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
            product_json_sha256=sha256(product_bytes),
            cad_verification_path="validation/cad-build.json",
            cad_verification_sha256=sha256(verification),
        )

    def test_match_and_invent_match_native_contract_identities(self):
        self.write_stage("match", self.match_inputs())
        self.write_json(
            "drafts/match.json",
            {
                "selected_inventor_id": "eve",
                "ranking": [item.to_dict() for item in self.assignment.ranking],
            },
        )
        self.run_tool("match", "--source", "drafts/match.json")
        assignment_document, assignment_bytes = self.assert_canonical_file(
            "artifacts/match/assignment.json"
        )
        observed_assignment = NativeMatchAssignment.from_mapping(assignment_document)
        self.assertEqual(observed_assignment, self.assignment)
        self.assert_outcome(
            "match",
            "artifacts/match/assignment.json",
            assignment_bytes,
            "invent",
        )

        self.write_stage(
            "invent", {"assignment": observed_assignment.to_dict()}
        )
        self.write_json(
            "drafts/invent.json",
            {
                "concept": dict(self.invented.concept),
                "research": {
                    "sources": [
                        {
                            "url": "https://example.test/moon",
                            "claim": "The visible phases follow relative geometry.",
                        }
                    ]
                },
            },
        )
        self.run_tool("invent", "--source", "drafts/invent.json")
        invented_document, invented_bytes = self.assert_canonical_file(
            "artifacts/invent/invented.json"
        )
        observed_invented = InventedV2.from_mapping(invented_document)
        self.assertEqual(observed_invented, self.invented)
        self.assert_outcome(
            "invent",
            "artifacts/invent/invented.json",
            invented_bytes,
            "make",
        )

    def test_make_hashes_exact_product_tree_and_matches_native_made(self):
        product_root, _, _, _ = self.create_product()
        self.write_stage(
            "make",
            {
                "assignment": self.assignment.to_dict(),
                "invented": self.invented.to_dict(),
                "feedback": [],
            },
            round_index=1,
        )
        self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "validation/cad-build.json",
        )
        made_document, made_bytes = self.assert_canonical_file(
            "artifacts/make/r0001/made.json"
        )
        made = NativeMade.from_mapping(made_document)
        made.assert_context(self.assignment, self.invented, expected_round=1)
        made.validate_product_tree(self.run_root)
        self.assertEqual(
            made.product_manifest.to_dict(),
            build_artifact_manifest(
                product_root, created_at="content-addressed"
            ).to_dict(),
        )
        self.assert_outcome(
            "make",
            "artifacts/make/r0001/made.json",
            made_bytes,
            "playtest",
        )

    def test_playtest_derives_file_hashes_and_loop_transition(self):
        made = self.create_made()
        evidence_root = self.run_root / "artifacts/playtest/r0001/evidence"
        evidence_root.mkdir(parents=True)
        config = b'{"seed":42,"version":1}\n'
        (evidence_root / "config.json").write_bytes(config)
        checks = []
        for check_id in self.blueprint.required_capabilities("playtest"):
            evidence_ref = "%s.json" % check_id
            (evidence_root / evidence_ref).write_bytes(
                canonical_json({"check": check_id, "ok": True}) + b"\n"
            )
            checks.append(
                {
                    "check_id": check_id,
                    "passed": True,
                    "evaluator": "workshop-host",
                    "evaluator_version": "1.0.0",
                    "config_ref": "config.json",
                    "evidence_ref": evidence_ref,
                    "observed_at": "2026-08-26T00:00:00Z",
                    "observations": {"ok": True},
                }
            )
        self.write_stage(
            "playtest",
            {
                "made": made.to_dict(),
                "required_check_ids": list(
                    self.blueprint.required_capabilities("playtest")
                ),
            },
            round_index=1,
        )
        self.write_json(
            "drafts/playtest.json",
            {"checks": list(reversed(checks)), "feedback": [], "verdict": "pass"},
        )
        self.run_tool(
            "playtest",
            "--source",
            "drafts/playtest.json",
            "--evidence-root",
            "artifacts/playtest/r0001/evidence",
        )
        playtested_document, playtested_bytes = self.assert_canonical_file(
            "artifacts/playtest/r0001/playtested.json"
        )
        playtested = NativePlaytested.from_mapping(playtested_document)
        playtested.assert_context(made, self.blueprint)
        playtested.validate_evidence_tree(self.run_root, made)
        self.assertEqual(
            {item.config_sha256 for item in playtested.checks}, {sha256(config)}
        )
        self.assert_outcome(
            "playtest",
            "artifacts/playtest/r0001/playtested.json",
            playtested_bytes,
            "release",
        )

        failed = checks[0]
        failed["passed"] = False
        failed["observations"] = {"ok": False}
        feedback = {
            "code": "repair-%s" % failed["check_id"],
            "area": "playtest",
            "severity": "improve",
            "finding": "The deterministic check failed.",
            "change": "Revise the exact product and rerun the check.",
            "evidence_refs": [failed["evidence_ref"]],
            "invalidates": ["playtest", "release", "deliver"],
        }
        self.write_json(
            "drafts/playtest-failed.json",
            {"checks": checks, "feedback": [feedback], "verdict": "improve"},
        )
        self.run_tool(
            "playtest",
            "--source",
            "drafts/playtest-failed.json",
            "--evidence-root",
            "artifacts/playtest/r0001/evidence",
        )
        failed_document, failed_bytes = self.assert_canonical_file(
            "artifacts/playtest/r0001/playtested.json"
        )
        self.assertEqual(failed_document["verdict"], "improve")
        NativePlaytested.from_mapping(failed_document)
        self.assert_outcome(
            "playtest",
            "artifacts/playtest/r0001/playtested.json",
            failed_bytes,
            "make",
        )

    def test_release_seals_exact_factual_package_and_matches_native_release(self):
        made = self.create_made()
        evidence_root = self.run_root / "artifacts/playtest/r0001/evidence"
        evidence_root.mkdir(parents=True)
        (evidence_root / "config.json").write_bytes(b'{"version":1}\n')
        checks = []
        expected_claims = {}
        for check_id in self.blueprint.required_capabilities("playtest"):
            evidence_ref = "%s.json" % check_id
            evidence = canonical_json({"check": check_id, "ok": True}) + b"\n"
            (evidence_root / evidence_ref).write_bytes(evidence)
            claims = ["The deterministic %s check passed." % check_id]
            checks.append(
                {
                    "check_id": check_id,
                    "passed": True,
                    "evaluator": "workshop-host",
                    "evaluator_version": "1.0.0",
                    "config_ref": "config.json",
                    "evidence_ref": evidence_ref,
                    "observed_at": "2026-08-26T00:00:00Z",
                    "observations": {
                        "evidence_class": "deterministic-check",
                        "claims": claims,
                    },
                }
            )
            expected_claims[check_id] = {
                "passed": True,
                "evidence_class": "deterministic-check",
                "claims": claims,
                "evidence_ref": evidence_ref,
                "evidence_sha256": sha256(evidence),
                "evaluator": "workshop-host",
                "evaluator_version": "1.0.0",
            }
        self.write_stage(
            "playtest",
            {
                "made": made.to_dict(),
                "required_check_ids": list(
                    self.blueprint.required_capabilities("playtest")
                ),
            },
            round_index=1,
        )
        self.write_json(
            "drafts/release-playtest.json",
            {"checks": checks, "feedback": [], "verdict": "pass"},
        )
        self.run_tool(
            "playtest",
            "--source",
            "drafts/release-playtest.json",
            "--evidence-root",
            "artifacts/playtest/r0001/evidence",
        )
        playtested_document, _ = self.assert_canonical_file(
            "artifacts/playtest/r0001/playtested.json"
        )
        playtested = NativePlaytested.from_mapping(playtested_document)

        package_root = self.run_root / "artifacts/release/package"
        package_root.mkdir(parents=True)
        (package_root / "MANUAL.md").write_text(
            "# Moon Nook\n\nUse only as described in the factual product record.\n",
            encoding="utf-8",
        )
        product = {
            "schema_version": 2,
            "kind": "workshop.release-package",
            "status": "facts-ready",
            "title": made.product["title"],
            "summary": "A factual package for the exact tested Moon Nook revision.",
            "lane": made.product["lane"],
            "product_artifact_sha256": made.product_manifest.artifact_sha256,
            "playtest_evidence_artifact_sha256": (
                playtested.evidence_manifest.artifact_sha256
            ),
            "claims": expected_claims,
            "factory_enrichment": {
                "copy_owner": "factory",
                "media_owner": "factory",
                "status": "pending",
            },
        }
        (package_root / "product.json").write_bytes(canonical_json(product))
        (package_root / "trace.json").write_bytes(
            canonical_json({"made_sha256": made.made_sha256})
        )
        self.write_stage(
            "release",
            {"made": made.to_dict(), "playtested": playtested.to_dict()},
            round_index=1,
        )
        self.run_tool(
            "release", "--package-root", "artifacts/release/package"
        )
        release_document, release_bytes = self.assert_canonical_file(
            "artifacts/release/release.json"
        )
        release = NativeRelease.from_mapping(release_document)
        release.assert_context(made, playtested)
        release.validate_package_tree(self.run_root, made, playtested)
        self.assertEqual(release.to_dict()["product"]["claims"], expected_claims)
        self.assertEqual(release.product_json_sha256, sha256(canonical_json(product)))
        self.assert_outcome(
            "release",
            "artifacts/release/release.json",
            release_bytes,
            "deliver",
        )

        (package_root / "product.json").write_bytes(
            json.dumps(product, indent=2).encode("utf-8")
        )
        result = self.run_tool(
            "release",
            "--package-root",
            "artifacts/release/package",
            expected=2,
        )
        self.assertIn("canonical JSON", result.stderr)

        (package_root / "product.json").write_bytes(canonical_json(product))
        (package_root / "invented-image.png").write_bytes(b"not-real-media")
        result = self.run_tool(
            "release",
            "--package-root",
            "artifacts/release/package",
            expected=2,
        )
        self.assertIn("cannot contain media", result.stderr)

    def test_fail_closed_on_mutable_stage_duplicate_json_and_authored_hashes(self):
        self.write_stage("match", self.match_inputs(), writable=True)
        self.write_json(
            "drafts/match.json",
            {
                "selected_inventor_id": "eve",
                "ranking": [item.to_dict() for item in self.assignment.ranking],
            },
        )
        result = self.run_tool(
            "match", "--source", "drafts/match.json", expected=2
        )
        self.assertIn("read-only", result.stderr)

        self.write_stage("match", self.match_inputs())
        duplicate = (
            b'{"selected_inventor_id":"eve",'
            b'"selected_inventor_id":"alice","ranking":[]}'
        )
        (self.run_root / "drafts/match.json").write_bytes(duplicate)
        result = self.run_tool(
            "match", "--source", "drafts/match.json", expected=2
        )
        self.assertIn("strict UTF-8 JSON", result.stderr)

        forged = {
            "selected_inventor_id": "eve",
            "ranking": [item.to_dict() for item in self.assignment.ranking],
            "assignment_sha256": "f" * 64,
        }
        self.write_json("drafts/match.json", forged)
        result = self.run_tool(
            "match", "--source", "drafts/match.json", expected=2
        )
        self.assertIn("fields are invalid", result.stderr)

    def test_fail_closed_on_path_escape_and_tree_symlink(self):
        self.write_stage("match", self.match_inputs())
        outside = self.run_root.parent / (self.run_root.name + "-outside.json")
        outside.write_text("{}")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        result = self.run_tool(
            "match", "--source", "../%s" % outside.name, expected=2
        )
        self.assertIn("safe relative", result.stderr)

        self.create_product()
        self.write_stage(
            "make",
            {
                "assignment": self.assignment.to_dict(),
                "invented": self.invented.to_dict(),
            },
            round_index=1,
        )
        target = self.run_root / "outside-cad.txt"
        target.write_text("not product data")
        os.symlink(
            target,
            self.run_root / "artifacts/make/r0001/product/cad/project/escape.step",
        )
        result = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "validation/cad-build.json",
            expected=2,
        )
        self.assertIn("not a symlink", result.stderr)

    def test_tool_has_no_workshop_or_third_party_import(self):
        source = TOOL.read_text(encoding="utf-8")
        self.assertNotIn("import workshop", source)
        self.assertNotIn("from workshop", source)
        completed = subprocess.run(
            [sys.executable, "-I", "-B", str(TOOL), "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("match,invent,make,playtest,release", completed.stdout)


if __name__ == "__main__":
    unittest.main()
