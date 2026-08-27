import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zlib
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.invent.native import NativeInvented
from tests.invent.test_native_contract import CONCEPT_VIOLATIONS, v4_concept
from tests.invent.test_vault import write_vault
from tests.playtest.test_native_playtested import LEAD_ANSWER_CASES
from workshop.invent.vault import Vault
from workshop.make.native import NativeMade
from workshop.match.native import (
    InventorRoster,
    InventorRosterEntry,
    MatchRankingEntry,
    NativeMatchAssignment,
)
from workshop.playtest.native import NativePlaytested
from workshop.product import ToyBlueprint
from workshop.release.native import NativeRelease
from workshop.workflow.proposals import AgentOutcomeProposal


REPOSITORY = Path(__file__).resolve().parents[2]
VAULT_TOOL = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "workshop"
    / "invent"
    / "skills"
    / "design-vault"
    / "vault_tools.py"
)
TOOL = (
    REPOSITORY
    / ".agents"
    / "product-run"
    / ".agents"
    / "skills"
    / "autonomous-workshop"
    / "scripts"
    / "stage_proposal.py"
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


def manual_pdf(
    *,
    page_count=1,
    declared_page_count=None,
    repeated_page_references=None,
    box=(0, 0, 297, 420),
    text=(
        "Moon Nook field manual. Arrange the rover, inspect every part, "
        "and begin a safe tabletop expedition."
    ),
    catalog_entries=b"",
    page_entries=b"",
    resource_entries=b"",
    content_suffix=b"",
    extra_objects=None,
):
    def pdf_string(value):
        return (
            value.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .encode("ascii")
        )

    objects = {}
    page_ids = [4 + index * 2 for index in range(page_count)]
    kids = page_ids
    if repeated_page_references is not None:
        kids = [page_ids[0]] * repeated_page_references
    declared = page_count if declared_page_count is None else declared_page_count
    objects[1] = (
        b"<< /Type /Catalog /Pages 2 0 R " + catalog_entries + b" >>"
    )
    objects[2] = (
        b"<< /Type /Pages /Count "
        + str(declared).encode("ascii")
        + b" /Kids ["
        + " ".join("%d 0 R" % page_id for page_id in kids).encode("ascii")
        + b"] >>"
    )
    objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    box_bytes = b" ".join(str(value).encode("ascii") for value in box)
    for index, page_id in enumerate(page_ids, start=1):
        content_id = page_id + 1
        page_text = "%s Page %d." % (text, index) if text else ""
        stream = (
            b"BT /F1 12 Tf 24 360 Td ("
            + pdf_string(page_text)
            + b") Tj ET\n"
            + content_suffix
        )
        objects[page_id] = (
            b"<< /Type /Page /Parent 2 0 R /MediaBox ["
            + box_bytes
            + b"] /Resources << /Font << /F1 3 0 R >> "
            + resource_entries
            + b" >> /Contents "
            + str(content_id).encode("ascii")
            + b" 0 R "
            + page_entries
            + b" >>"
        )
        objects[content_id] = (
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"endstream"
        )
    objects.update(extra_objects or {})

    result = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = {0: 0}
    for object_number in range(1, max(objects, default=0) + 1):
        offsets[object_number] = len(result)
        result.extend(("%d 0 obj\n" % object_number).encode("ascii"))
        result.extend(objects[object_number])
        result.extend(b"\nendobj\n")
    xref = len(result)
    result.extend(("xref\n0 %d\n" % len(offsets)).encode("ascii"))
    result.extend(b"0000000000 65535 f \n")
    for object_number in range(1, len(offsets)):
        result.extend(
            ("%010d 00000 n \n" % offsets[object_number]).encode("ascii")
        )
    result.extend(
        (
            "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(offsets), xref)
        ).encode("ascii")
    )
    return bytes(result)


class StageProposalToolTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_root = Path(self.temporary.name).resolve()
        self.blueprint = ToyBlueprint()
        alice = InventorRosterEntry(
            "alice",
            ".codex/agents/alice.toml",
            "a" * 64,
            "1" * 64,
            "b" * 64,
        )
        eve = InventorRosterEntry(
            "eve",
            ".codex/agents/eve.toml",
            "c" * 64,
            "2" * 64,
            "d" * 64,
        )
        self.roster = InventorRoster((alice, eve))
        self.assignment = NativeMatchAssignment(
            wish_sha256="e" * 64,
            inventor_roster_sha256=self.roster.roster_sha256,
            selected_inventor_id="eve",
            selected_agent_path=eve.agent_path,
            selected_agent_sha256=eve.agent_sha256,
            selected_source_manifest_sha256=eve.source_manifest_sha256,
            selected_taste_sha256=eve.taste_sha256,
            blueprint_sha256=self.blueprint.sha256,
            ranking=(
                MatchRankingEntry(
                    "eve", "The Wish asks for a specific coherent tiny world."
                ),
                MatchRankingEntry(
                    "alice", "The classic-edition specialist is less direct for this Wish."
                ),
            ),
        )
        self.invented = NativeInvented(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            schema_version=4,
            concept=v4_concept(),
            research={
                "sources": [
                    {
                        "url": "https://example.test/moon",
                        "claim": "The visible phases follow relative geometry.",
                    }
                ]
            },
        )
        self.legacy_invented = NativeInvented(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            schema_version=3,
            concept={
                "title": "Moon Nook",
                "summary": "A tiny lunar observatory shaped by the Wish.",
            },
            research=self.invented.to_dict()["research"],
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

    def run_tool(
        self,
        *arguments,
        expected=0,
        include_workshop_python=True,
        workshop_python_override=None,
    ):
        environment = os.environ.copy()
        if include_workshop_python:
            environment["WORKSHOP_PYTHON"] = (
                str(Path(sys.executable).absolute())
                if workshop_python_override is None
                else workshop_python_override
            )
        else:
            environment.pop("WORKSHOP_PYTHON", None)
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
            env=environment,
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

    def test_requires_the_exact_host_supplied_python(self):
        self.write_stage("match", self.match_inputs())
        self.write_json(
            "drafts/match-python.json",
            {
                "selected_inventor_id": "eve",
                "ranking": [item.to_dict() for item in self.assignment.ranking],
            },
        )

        result = self.run_tool(
            "match",
            "--source",
            "drafts/match-python.json",
            expected=2,
            include_workshop_python=False,
        )

        self.assertIn("exact host-supplied WORKSHOP_PYTHON", result.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

        nonexact = "%s/./%s" % (
            Path(sys.executable).absolute().parent,
            Path(sys.executable).name,
        )
        result = self.run_tool(
            "match",
            "--source",
            "drafts/match-python.json",
            expected=2,
            workshop_python_override=nonexact,
        )
        self.assertIn("exact host-supplied WORKSHOP_PYTHON", result.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

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
            "inventor_roster": self.roster.to_dict(),
            "blueprint_sha256": self.blueprint.sha256,
        }

    def create_product(self):
        product_root = self.run_root / "artifacts/make/r0001/product"
        (product_root / "cad/project").mkdir(parents=True)
        (product_root / "exports/stl").mkdir(parents=True)
        (product_root / "validation").mkdir()
        product = {
            "title": "Moon Nook",
            "summary": "A tiny lunar observatory.",
            "components": ["observatory"],
        }
        product_bytes = canonical_json(product) + b"\n"
        verification = b'{"ok":true,"validator":"cad-final"}\n'
        (product_root / "product.json").write_bytes(product_bytes)
        (product_root / "cad/project/moon.step.py").write_text("pass\n")
        (product_root / "assembled.step").write_bytes(b"ISO-10303-21;\n")
        (product_root / "assembled.step.json").write_bytes(
            canonical_json({"assembly": "Moon Nook", "parts": 1}) + b"\n"
        )
        assembled_stl = (
            b"solid moon\nendsolid moon\n"
        )
        (product_root / "assembled.stl").write_bytes(assembled_stl)
        (product_root / "exports/stl/assembled.stl").write_bytes(assembled_stl)
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
                "concept": self.invented.to_dict()["concept"],
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
        observed_invented = NativeInvented.from_mapping(invented_document)
        self.assertEqual(observed_invented, self.invented)
        self.assert_outcome(
            "invent",
            "artifacts/invent/invented.json",
            invented_bytes,
            "make",
        )

    def materialize_vault(self, *, tool=True, vault=True, corrupt=False):
        skill = self.run_root / ".agents" / "skills" / "design-vault"
        skill.mkdir(parents=True, exist_ok=True)
        packed = Vault.from_directory(write_vault(self.run_root / "vault-source")).packed_bytes()
        if vault:
            (skill / "vault.json").write_bytes(b"{not json" if corrupt else packed)
        if tool:
            (skill / "vault_tools.py").write_bytes(VAULT_TOOL.read_bytes())
        return skill

    def invent_source(self, mechanisms, **extra):
        concept = v4_concept()
        concept["mechanisms"] = mechanisms
        concept.update(extra)
        return {"concept": concept, "research": self.invented.to_dict()["research"]}

    def test_invent_applies_the_run_local_design_vault(self):
        self.materialize_vault()
        self.write_stage("invent", {"assignment": self.assignment.to_dict()})
        self.write_json("drafts/invent.json", self.invent_source(["hand-off", "single-token"]))
        self.run_tool("invent", "--source", "drafts/invent.json")
        document, _ = self.assert_canonical_file("artifacts/invent/invented.json")
        self.assertEqual(document["schema_version"], 4)
        self.assertEqual(document["concept"]["mechanisms"], ["hand-off", "single-token"])
        for mechanisms, extra, pattern in (
            (["rotating-dome"], {}, "mechanism-unknown"),
            (["card-hand"], {}, "vault-conflict"),
            (["hand-off"], {}, "vault-requirement"),
            (
                ["hand-off", "single-token"],
                {"novel_mechanisms": [{"id": "hand-off", "definition": "x" * 30}]},
                "mechanism-not-novel",
            ),
        ):
            (self.run_root / "artifacts/invent/invented.json").unlink(missing_ok=True)
            self.write_json("drafts/invent.json", self.invent_source(mechanisms, **extra))
            with self.subTest(pattern=pattern):
                completed = self.run_tool("invent", "--source", "drafts/invent.json", expected=2)
                self.assertIn("refused by the design vault", completed.stderr)
                self.assertIn(pattern, completed.stderr)
        (self.run_root / "artifacts/invent/invented.json").unlink(missing_ok=True)
        self.write_json(
            "drafts/invent.json",
            self.invent_source(
                ["single-token", "rotating-dome"],
                novel_mechanisms=[{"id": "rotating-dome", "definition": "A dome that turns by hand."}],
            ),
        )
        self.run_tool("invent", "--source", "drafts/invent.json")

    def test_invent_vault_snapshot_must_be_whole_or_absent(self):
        spec = importlib.util.spec_from_file_location("stage_proposal_vault_test", TOOL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        self.assertIsNone(tool._design_vault(self.run_root))
        tool._assert_concept_vault_compatible(self.run_root, v4_concept())
        skill = self.materialize_vault(tool=True, vault=False)
        with self.assertRaisesRegex(tool.ProposalError, "missing from the run"):
            tool._design_vault(self.run_root)
        (skill / "vault_tools.py").unlink()
        self.materialize_vault(tool=False, vault=True)
        with self.assertRaisesRegex(tool.ProposalError, "missing from the run"):
            tool._design_vault(self.run_root)
        self.materialize_vault(corrupt=True)
        with self.assertRaisesRegex(tool.ProposalError, "snapshot is invalid"):
            tool._design_vault(self.run_root)
        self.materialize_vault()
        module, vault = tool._design_vault(self.run_root)
        self.assertEqual(vault.resolve("pass the baton"), "mechanisms/hand-off")
        with self.assertRaisesRegex(tool.ProposalError, "vault-conflict"):
            tool._assert_concept_vault_compatible(self.run_root, {**v4_concept(), "mechanisms": ["card-hand"]})
        self.write_stage("invent", {"assignment": self.assignment.to_dict()})
        self.write_json("drafts/invent.json", self.invent_source(["hand-off", "single-token"]))
        import argparse

        with mock.patch.dict(os.environ, {"WORKSHOP_PYTHON": str(Path(sys.executable).absolute())}):
            result = tool.run(
                argparse.Namespace(run_root=str(self.run_root), command="invent", source="drafts/invent.json")
            )
        self.assertEqual(result["outcome_path"], "agent-outcome.json")
        document, _ = self.assert_canonical_file("artifacts/invent/invented.json")
        self.assertEqual(document["schema_version"], 4)

    def test_invent_rejects_contract_violations_with_a_named_rule(self):
        self.write_stage("invent", {"assignment": self.assignment.to_dict()})
        for name, mutate, pattern in CONCEPT_VIOLATIONS[:3] + CONCEPT_VIOLATIONS[-3:]:
            concept = v4_concept()
            mutate(concept)
            self.write_json(
                "drafts/invent.json",
                {"concept": concept, "research": self.invented.to_dict()["research"]},
            )
            with self.subTest(violation=name):
                completed = self.run_tool(
                    "invent", "--source", "drafts/invent.json", expected=2
                )
                self.assertRegex(completed.stderr, pattern)
                self.assertFalse((self.run_root / "artifacts/invent/invented.json").exists())

    def test_invent_contract_rules_match_the_host_mirror(self):
        spec = importlib.util.spec_from_file_location("stage_proposal_under_test", TOOL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        tool._validate_concept_contract(v4_concept())
        for name, mutate, pattern in CONCEPT_VIOLATIONS:
            concept = v4_concept()
            mutate(concept)
            with self.subTest(violation=name):
                with self.assertRaisesRegex(tool.ProposalError, pattern):
                    tool._validate_concept_contract(concept)
        legacy = self.legacy_invented.to_dict()
        assignment = self.assignment.to_dict()
        self.assertEqual(tool._validate_invented(legacy, assignment), legacy)
        current = self.invented.to_dict()
        self.assertEqual(tool._validate_invented(current, assignment), current)
        with self.assertRaisesRegex(tool.ProposalError, "schema_version must be 3 or 4"):
            tool._validate_invented({**legacy, "schema_version": 2}, assignment)
        hand_written = {**current, "concept": {**current["concept"], "mechanisms": ["Bad Slug"]}}
        with self.assertRaisesRegex(tool.ProposalError, "unique slugs"):
            tool._validate_invented(hand_written, assignment)
        sealed = tool._invent_contract(
            self.run_root,
            {"inputs": {"assignment": assignment}},
            {"concept": current["concept"], "research": current["research"]},
        )
        self.assertEqual(sealed["schema_version"], 4)
        self.assertEqual(sealed, current)

    def test_make_accepts_a_sealed_legacy_schema_3_invent(self):
        self.create_product()
        self.write_stage(
            "make",
            {
                "assignment": self.assignment.to_dict(),
                "invented": self.legacy_invented.to_dict(),
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
        made_document, _ = self.assert_canonical_file("artifacts/make/r0001/made.json")
        NativeMade.from_mapping(made_document).assert_context(
            self.assignment, self.legacy_invented, expected_round=1
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

    def test_make_rejects_editor_backup_and_patch_debris(self):
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
        for name in ("model.step.orig", "change.rej", "notes.md~", ".part.py.swp"):
            with self.subTest(name=name):
                debris = product_root / name
                debris.write_text("stale editing output\n", encoding="utf-8")
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
                self.assertIn("editor, backup, or patch debris", result.stderr)
                debris.unlink()

        (product_root / "original.step").write_bytes(b"ISO-10303-21;\n")
        self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "validation/cad-build.json",
        )

    def test_make_rejects_empty_directories_before_writing_a_proposal(self):
        product_root, _, _, _ = self.create_product()
        (product_root / "cad/spec").mkdir()
        (product_root / "cad/exports").mkdir()
        self.write_stage(
            "make",
            {
                "assignment": self.assignment.to_dict(),
                "invented": self.invented.to_dict(),
                "feedback": [],
            },
            round_index=1,
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

        self.assertIn("empty, undeclared, or missing directories", result.stderr)
        self.assertFalse(
            (self.run_root / "artifacts/make/r0001/made.json").exists()
        )
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

    def test_vault_lead_answer_rules_match_the_host_mirror(self):
        spec = importlib.util.spec_from_file_location("stage_proposal_leads_test", TOOL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        for name, leads, checks, feedback, expected in LEAD_ANSWER_CASES:
            with self.subTest(case=name):
                if isinstance(expected, dict):
                    self.assertEqual(tool._validate_vault_lead_answers(leads, checks, feedback), expected)
                else:
                    with self.assertRaisesRegex(tool.ProposalError, expected):
                        tool._validate_vault_lead_answers(leads, checks, feedback)

    def test_playtest_must_answer_issued_vault_leads(self):
        made = self.create_made()
        evidence_root = self.run_root / "artifacts/playtest/r0001/evidence"
        evidence_root.mkdir(parents=True)
        (evidence_root / "config.json").write_bytes(b'{"seed":1}\n')
        lead = {"id": "c" * 16, "kind": "risk", "nodes": ["mechanisms/x", "anti-patterns/y"], "explanation": "", "evidence": [], "suggested_fixes": []}
        checks = []
        for check_id in self.blueprint.required_playtest_checks():
            evidence_ref = "%s.json" % check_id
            (evidence_root / evidence_ref).write_bytes(canonical_json({"check": check_id}) + b"\n")
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
                "required_check_ids": list(self.blueprint.required_playtest_checks()),
                "vault_leads": [lead],
            },
            round_index=1,
        )
        self.write_json(
            "drafts/playtest.json", {"checks": checks, "feedback": [], "verdict": "pass"}
        )
        completed = self.run_tool(
            "playtest", "--source", "drafts/playtest.json",
            "--evidence-root", "artifacts/playtest/r0001/evidence", expected=2,
        )
        self.assertIn("unanswered: " + "c" * 16, completed.stderr)
        for check in checks:
            if check["check_id"] == "agent-playtest":
                check["observations"]["vault_leads"] = [
                    {"lead": "c" * 16, "verdict": "dismissed", "why": "No exposure.", "feedback_code": None}
                ]
        self.write_json(
            "drafts/playtest.json", {"checks": checks, "feedback": [], "verdict": "pass"}
        )
        self.run_tool(
            "playtest", "--source", "drafts/playtest.json",
            "--evidence-root", "artifacts/playtest/r0001/evidence",
        )
        document, _ = self.assert_canonical_file("artifacts/playtest/r0001/playtested.json")
        playtested = NativePlaytested.from_mapping(document)
        self.assertEqual(
            playtested.assert_vault_leads_answered([lead]),
            {"answered": 1, "confirmed": 0, "dismissed": 1},
        )
        (self.run_root / "artifacts/playtest/r0001/playtested.json").unlink()
        (self.run_root / "agent-outcome.json").unlink()
        spec = importlib.util.spec_from_file_location("stage_proposal_playtest_run", TOOL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        import argparse

        with mock.patch.dict(os.environ, {"WORKSHOP_PYTHON": str(Path(sys.executable).absolute())}):
            result = tool.run(
                argparse.Namespace(
                    run_root=str(self.run_root),
                    command="playtest",
                    source="drafts/playtest.json",
                    evidence_root="artifacts/playtest/r0001/evidence",
                )
            )
        self.assertEqual(result["outcome_path"], "agent-outcome.json")
        again, _ = self.assert_canonical_file("artifacts/playtest/r0001/playtested.json")
        self.assertEqual(again, document)

    def test_playtest_derives_file_hashes_and_loop_transition(self):
        made = self.create_made()
        replay_work = self.run_root / "work/playtest/r0001/replay.py"
        replay_work.parent.mkdir(parents=True)
        replay_work.write_text("print('replay')\n", encoding="utf-8")
        evidence_root = self.run_root / "artifacts/playtest/r0001/evidence"
        evidence_root.mkdir(parents=True)
        config = b'{"seed":42,"version":1}\n'
        (evidence_root / "config.json").write_bytes(config)
        checks = []
        for check_id in self.blueprint.required_playtest_checks():
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
                    self.blueprint.required_playtest_checks()
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
        self.assertTrue(replay_work.exists())
        self.assertNotIn(
            "replay.py",
            {entry.path for entry in playtested.evidence_manifest.entries},
        )
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

        feedback["invalidates"] = ["make", "playtest", "release"]
        self.write_json(
            "drafts/playtest-invalid-invalidation.json",
            {"checks": checks, "feedback": [feedback], "verdict": "improve"},
        )
        rejected = self.run_tool(
            "playtest",
            "--source",
            "drafts/playtest-invalid-invalidation.json",
            "--evidence-root",
            "artifacts/playtest/r0001/evidence",
            expected=2,
        )
        self.assertIn(
            "the verdict already routes the repair to Make",
            rejected.stderr,
        )

    def test_playtest_rejects_working_tree_debris_inside_evidence(self):
        made = self.create_made()
        evidence_root = self.run_root / "artifacts/playtest/r0001/evidence"
        evidence_root.mkdir(parents=True)
        (evidence_root / "config.json").write_bytes(b'{"version":1}\n')
        debris = evidence_root / "__pycache__/replay.pyc"
        debris.parent.mkdir()
        debris.write_bytes(b"temporary bytecode")
        checks = []
        for check_id in self.blueprint.required_playtest_checks():
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
                    self.blueprint.required_playtest_checks()
                ),
            },
            round_index=1,
        )
        self.write_json(
            "drafts/playtest.json",
            {"checks": checks, "feedback": [], "verdict": "pass"},
        )

        rejected = self.run_tool(
            "playtest",
            "--source",
            "drafts/playtest.json",
            "--evidence-root",
            "artifacts/playtest/r0001/evidence",
            expected=2,
        )

        self.assertIn("path excluded by manifest policy", rejected.stderr)
        self.assertFalse(
            (self.run_root / "artifacts/playtest/r0001/playtested.json").exists()
        )
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

    def test_release_seals_exact_codex_authored_page_and_matches_native_release(self):
        made = self.create_made()
        evidence_root = self.run_root / "artifacts/playtest/r0001/evidence"
        evidence_root.mkdir(parents=True)
        (evidence_root / "config.json").write_bytes(b'{"version":1}\n')
        checks = []
        expected_claims = {}
        for check_id in self.blueprint.required_playtest_checks():
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
                    self.blueprint.required_playtest_checks()
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
        (package_root / "MANUAL.pdf").write_bytes(manual_pdf())
        product = {
            "schema_version": 4,
            "kind": "workshop.release-package",
            "status": "manual-ready",
            "title": made.product["title"],
            "summary": "The exact tested Moon Nook revision.",
            "what_arrives": ["One tested Moon Nook product revision", "One manual"],
            "limitations": [],
            "product_artifact_sha256": made.product_manifest.artifact_sha256,
            "playtest_evidence_artifact_sha256": (
                playtested.evidence_manifest.artifact_sha256
            ),
            "claims": expected_claims,
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
        self.assertEqual(release.schema_version, 2)
        self.assertEqual(release.manual_path, "MANUAL.pdf")
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

        invalid_product_cases = (
            (
                {"hero": {"headline": "Website copy is not a Release gate."}},
                "fields are invalid",
            ),
            (
                {"schema_version": 3, "status": "page-ready"},
                "not a manual-ready package",
            ),
            (
                {"what_arrives": []},
                "must not be empty",
            ),
        )
        for changes, message in invalid_product_cases:
            invalid_product = {**product, **changes}
            (package_root / "product.json").write_bytes(
                canonical_json(invalid_product)
            )
            result = self.run_tool(
                "release",
                "--package-root",
                "artifacts/release/package",
                expected=2,
            )
            self.assertIn(message, result.stderr)

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

        (package_root / "invented-image.png").unlink()
        pdf_path = package_root / "MANUAL.pdf"
        pdf_path.unlink()
        (package_root / "MANUAL.md").write_text("# Legacy manual\n", encoding="utf-8")
        result = self.run_tool(
            "release",
            "--package-root",
            "artifacts/release/package",
            expected=2,
        )
        self.assertIn("lacks MANUAL.pdf", result.stderr)
        (package_root / "MANUAL.md").unlink()

        expanded_stream = b"x" * (8 * 1024 * 1024 + 1)
        compressed_stream = zlib.compress(expanded_stream, level=9)
        run_length_stream = (
            b"\x81x" * ((8 * 1024 * 1024) // 128 + 1) + b"\x80"
        )
        ascii85_stream = b"<~" + b"z" * (2 * 1024 * 1024 + 1) + b"~>"
        oversized_jpeg = (
            b"\xff\xd8\xff\xc0\x00\x0b\x08\x23\x28\x23\x28\x01"
            b"\x01\x11\x00\xff\xd9"
        )
        inline_pixels = zlib.compress(
            b"\x00" * ((9_000 * 9_000 + 7) // 8), level=9
        )
        inline_form = (
            b"q BI /W 9000 /H 9000 /CS /G /BPC 1 /F /FlateDecode ID "
            + inline_pixels
            + b" EI Q\n"
        )
        invalid_manual_cases = (
            (manual_pdf(page_count=0), "1 through 64 pages"),
            (manual_pdf(page_count=65), "1 through 64 pages"),
            (
                manual_pdf(
                    page_count=1,
                    declared_page_count=1,
                    repeated_page_references=10_000,
                ),
                "unreadable page tree",
            ),
            (manual_pdf(box=(0, 0, 0, 420)), "printable page"),
            (manual_pdf(text=""), "meaningful extractable text"),
            (
                manual_pdf(
                    catalog_entries=(
                        b"/Names << /Dests << /Names [(x) << /S /JavaScript "
                        b"/JS (app.alert\\(1\\)) >>] >> >>"
                    )
                ),
                "active or external",
            ),
            (
                manual_pdf(
                    catalog_entries=(
                        b"/Names << /Dests << /Names [(sound) 6 0 R] >> >>"
                    ),
                    extra_objects={
                        6: b"<< /S /Sound /Sound 7 0 R >>",
                        7: (
                            b"<< /R 8000 /C 1 /B 8 /Length 1 >>\n"
                            b"stream\n\x00\nendstream"
                        ),
                    },
                ),
                "forbidden PDF action: /Sound",
            ),
            (
                manual_pdf(
                    page_entries=b"/Annots [6 0 R]",
                    extra_objects={
                        6: (
                            b"<< /Type /Annot /Subtype /Link /Rect [0 0 20 20] "
                            b"/Dest [4 0 R /Fit] >>"
                        )
                    },
                ),
                "forbidden PDF object: /Annot",
            ),
            (
                manual_pdf(
                    extra_objects={
                        6: (
                            b"<< /Type /XObject /Subtype /Image /Width 8193 "
                            b"/Height 1 /ColorSpace /DeviceGray /BitsPerComponent 8 "
                            b"/Length 1 >>\nstream\n\x00\nendstream"
                        )
                    },
                ),
                "image Width",
            ),
            (
                manual_pdf(
                    extra_objects={
                        6: (
                            b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 "
                            b"/ColorSpace /DeviceGray /BitsPerComponent 8 "
                            b"/Filter /DCTDecode /Length "
                            + str(len(oversized_jpeg)).encode("ascii")
                            + b" >>\nstream\n"
                            + oversized_jpeg
                            + b"\nendstream"
                        )
                    }
                ),
                "JPEG dimensions differ",
            ),
            (
                manual_pdf(
                    resource_entries=b"/XObject << /Fm1 6 0 R >>",
                    content_suffix=b"q /Fm1 Do Q\n",
                    extra_objects={
                        6: (
                            b"<< /Type /XObject /Subtype /Form /BBox [0 0 10 10] "
                            b"/Resources << >> /Length "
                            + str(len(inline_form)).encode("ascii")
                            + b" >>\nstream\n"
                            + inline_form
                            + b"endstream"
                        )
                    },
                ),
                "unsupported inline image",
            ),
            (
                manual_pdf(
                    extra_objects={
                        6: (
                            b"<< /Filter /FlateDecode /Length "
                            + str(len(compressed_stream)).encode("ascii")
                            + b" >>\nstream\n"
                            + compressed_stream
                            + b"\nendstream"
                        )
                    },
                ),
                "decoded PDF stream",
            ),
            (
                manual_pdf(
                    extra_objects={
                        6: (
                            b"<< /Filter /RunLengthDecode /Length "
                            + str(len(run_length_stream)).encode("ascii")
                            + b" >>\nstream\n"
                            + run_length_stream
                            + b"\nendstream"
                        )
                    }
                ),
                "oversized PDF stream",
            ),
            (
                manual_pdf(
                    extra_objects={
                        6: (
                            b"<< /Filter /ASCII85Decode /Length "
                            + str(len(ascii85_stream)).encode("ascii")
                            + b" >>\nstream\n"
                            + ascii85_stream
                            + b"\nendstream"
                        )
                    }
                ),
                "decoded bound is too large",
            ),
        )
        for invalid_manual, message in invalid_manual_cases:
            pdf_path.write_bytes(invalid_manual)
            result = self.run_tool(
                "release",
                "--package-root",
                "artifacts/release/package",
                expected=2,
            )
            self.assertIn(message, result.stderr)

        valid_manual = manual_pdf()
        pdf_path.write_bytes(
            valid_manual
            + b" " * (16 * 1024 * 1024 - len(valid_manual) + 1)
        )
        result = self.run_tool(
            "release",
            "--package-root",
            "artifacts/release/package",
            expected=2,
        )
        self.assertIn("exceeds its byte limit", result.stderr)

        pdf_path.write_bytes(valid_manual)
        (package_root / "product.json.orig").write_bytes(canonical_json(product))
        result = self.run_tool(
            "release",
            "--package-root",
            "artifacts/release/package",
            expected=2,
        )
        self.assertIn("editor, backup, or patch debris", result.stderr)

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
