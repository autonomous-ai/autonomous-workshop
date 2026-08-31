import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

from PIL import Image, ImageDraw

from workshop.artifacts import build_artifact_manifest
from workshop.concept import PreRenderConcept, seal_pre_render_concept
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import NativeInvented
from workshop.make.contracts import Made
from workshop.make.native import NativeMade
from workshop.make.revision import NativeMakeInventRevision
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
from workshop.workflow.stage_gates import evaluate_routed_invent_stage
from workshop.wish import Wish
from workshop.runtime.concept_effects import (
    ConceptEffectEvidence,
    ConceptEffectRoleEvidence,
)


REPOSITORY = Path(__file__).resolve().parents[2]
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
    "release": "complete",
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
            concept={
                "title": "Moon Nook",
                "summary": "A tiny lunar observatory shaped by the Wish.",
                "signature_decision": (
                    "The viewing aperture and the moon-phase dial share one "
                    "compact tactile enclosure."
                ),
                "intended_interaction": (
                    "A person turns the dial and looks through the aperture."
                ),
                "envelope_mm": {
                    "length_mm": 60.0,
                    "width_mm": 40.0,
                    "height_mm": 25.0,
                },
                "components": [
                    {
                        "key": "observatory",
                        "name": "Observatory body",
                        "purpose": "Holds the aperture and phase dial",
                        "form": "Rounded printable enclosure",
                        "placement": "Centered on a table",
                        "interfaces": "The dial rotates within the body",
                        "dimensions_mm": {
                            "length_mm": 60.0,
                            "width_mm": 40.0,
                            "height_mm": 25.0,
                        },
                    }
                ],
                "assumptions": ["The object is used indoors."],
                "unresolved_risks": ["Physical fit has not yet been tested."],
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

    def assert_outcome(
        self,
        stage,
        contract_path,
        contract_bytes,
        transition,
        additional_artifacts=(),
    ):
        document, _ = self.assert_canonical_file("agent-outcome.json")
        proposal = AgentOutcomeProposal.from_mapping(document)
        self.assertEqual(proposal.outcome.stage, stage)
        self.assertEqual(proposal.outcome.proposed_transition, transition)
        self.assertEqual(len(proposal.outcome.artifacts), 1 + len(additional_artifacts))
        artifact = proposal.outcome.artifacts[0]
        self.assertEqual(artifact.path, contract_path)
        self.assertEqual(artifact.sha256, sha256(contract_bytes))
        self.assertEqual(
            tuple((item.path, item.sha256) for item in proposal.outcome.artifacts[1:]),
            tuple(additional_artifacts),
        )
        self.assertEqual(proposal.checkpoint_sha256, "1" * 64)
        self.assertEqual(proposal.subject_sha256, "2" * 64)

    def test_need_finalizer_writes_bound_nonready_outcome_without_artifacts(self):
        for status in ("waiting", "failed"):
            with self.subTest(status=status):
                self.write_stage(
                    "make",
                    {"wish_sha256": "e" * 64},
                    round_index=1,
                )
                result = self.run_tool(
                    "need",
                    "--stage",
                    "make",
                    "--status",
                    status,
                    "--reason",
                    "The required CAD runtime is unavailable.",
                )

                self.assertEqual(
                    json.loads(result.stdout),
                    {
                        "needs": 1,
                        "outcome_path": "agent-outcome.json",
                        "status": status,
                    },
                )
                document, _ = self.assert_canonical_file("agent-outcome.json")
                proposal = AgentOutcomeProposal.from_mapping(document)
                self.assertEqual(proposal.checkpoint_sha256, "1" * 64)
                self.assertEqual(proposal.subject_sha256, "2" * 64)
                self.assertEqual(proposal.outcome.stage, "make")
                self.assertEqual(proposal.outcome.status, status)
                self.assertEqual(proposal.outcome.artifacts, ())
                self.assertEqual(
                    proposal.outcome.needs,
                    ("The required CAD runtime is unavailable.",),
                )
                self.assertIsNone(proposal.outcome.proposed_transition)
                (self.run_root / "agent-outcome.json").unlink()

    def test_need_finalizer_rejects_stage_mismatch_and_control_text(self):
        self.write_stage(
            "make",
            {"wish_sha256": "e" * 64},
            round_index=1,
        )

        mismatch = self.run_tool(
            "need",
            "--stage",
            "invent",
            "--status",
            "waiting",
            "--reason",
            "A concrete operator action is required.",
            expected=2,
        )
        self.assertIn("describes another stage", mismatch.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

        invalid = self.run_tool(
            "need",
            "--stage",
            "make",
            "--status",
            "waiting",
            "--reason",
            "A concrete operator action is required.\nRetry later.",
            expected=2,
        )
        self.assertIn("bounded single-line text", invalid.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

    def match_inputs(self):
        return {
            "wish_sha256": self.assignment.wish_sha256,
            "inventor_roster": self.roster.to_dict(),
            "blueprint_sha256": self.blueprint.sha256,
        }

    def create_marked_invent_source(self):
        wish = Wish.create(
            "run-local-toy",
            "A tactile moon observatory with a compact phase dial.",
            context={"audience": "adult"},
        )
        wish_bytes = canonical_json(wish.to_dict())
        (self.run_root / "WISH.json").write_bytes(wish_bytes)
        wish_sha256 = sha256(wish_bytes)
        assignment = NativeMatchAssignment(
            wish_sha256=wish_sha256,
            inventor_roster_sha256=self.roster.roster_sha256,
            selected_inventor_id=self.assignment.selected_inventor_id,
            selected_agent_path=self.assignment.selected_agent_path,
            selected_agent_sha256=self.assignment.selected_agent_sha256,
            selected_source_manifest_sha256=self.assignment.selected_source_manifest_sha256,
            selected_taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.blueprint.sha256,
            ranking=self.assignment.ranking,
        )
        invented = NativeInvented(
            wish_sha256=wish_sha256,
            assignment_sha256=assignment.assignment_sha256,
            taste_sha256=assignment.selected_taste_sha256,
            blueprint_sha256=assignment.blueprint_sha256,
            concept=self.invented.to_dict()["concept"],
            research=self.invented.to_dict()["research"],
        )
        source = {
            "selected_inventor_id": assignment.selected_inventor_id,
            "ranking": [item.to_dict() for item in assignment.ranking],
            "concept": invented.to_dict()["concept"],
            "research": invented.to_dict()["research"],
        }
        root = "artifacts/concept/r0001/concept"
        excerpt = "A bounded physical reference."
        excerpt_sha256 = sha256(canonical_json(excerpt))
        brief = {
            "object": "moon observatory",
            "category": "tactile tabletop object",
            "envelope_mm": {"length_mm": 60, "width_mm": 40, "height_mm": 25},
            "wall_thickness_mm": 2.4,
            "print_stance": {
                "orientation": "body down",
                "supports_required": False,
                "support_notes": "self-supporting shell",
            },
            "features": [{"id": "phase-dial", "text": "A tactile rotating phase dial."}],
            "fit_target": {
                "target": "phase dial axle",
                "dimensions_mm": {"length_mm": 5, "width_mm": 5, "height_mm": 20},
                "clearance_mm": 0.3,
            },
            "components": [self.invented.to_dict()["concept"]["components"][0]],
        }
        fields = (
            "object", "category", "envelope_mm", "wall_thickness_mm", "print_stance",
            "fit_target", "features.phase-dial", "components.observatory",
        )
        brief["facts"] = [
            {"field": field, "source_id": "source-1", "assumption_reason": None}
            for field in fields
        ]
        research = {
            "sources": [{
                "id": "source-1",
                "origin": "https://example.test/moon",
                "excerpt": excerpt,
                "excerpt_sha256": excerpt_sha256,
                "retrieved_at": "2026-08-30T00:00:00+00:00",
            }],
            "findings": [{
                "finding": "The source bounds the tactile phase mechanism.",
                "source_ids": ["source-1"],
            }],
        }
        prompts = {
            "presentation": "Neutral studio treatment at consistent scale.",
            "front": {"instruction": "Front view of the observatory.", "references": []},
            "top": {"instruction": "Top view of the same body.", "references": ["front"]},
            "bottom": {"instruction": "Bottom interface view.", "references": ["front"]},
            "exploded": {
                "instruction": "Show the Observatory body and phase dial separated.",
                "references": ["front", "top", "bottom"],
            },
            "components": {
                "observatory": {
                    "instruction": "Observatory body alone with matching finish.",
                    "references": ["front"],
                }
            },
        }
        descriptor = {
            "front": {"path": "images/front.png"},
            "top": {"path": "images/top.png"},
            "bottom": {"path": "images/bottom.png"},
            "exploded": {"path": "images/exploded.png"},
            "components": {"observatory": {"path": "images/components/observatory.png"}},
        }
        derived = {
            "schema_version": 1,
            "kind": "autonomous-workshop.concept-derived-wish",
            "wish_sha256": wish_sha256,
            "product_id": wish.product_id,
            "objective": wish.objective,
            "context": dict(wish.context),
            "constraints": {"envelope_mm": brief["envelope_mm"]},
        }
        derived["derived_wish_sha256"] = sha256(canonical_json(derived))
        for name, value in (
            ("brief.json", brief),
            ("derived_wish.json", derived),
            ("descriptor.json", descriptor),
            ("prompts.json", prompts),
            ("research.json", research),
        ):
            self.write_json("%s/%s" % (root, name), value, canonical=True)
        inputs = {
            "effort": "forge",
            "wish": {"path": "WISH.json", "sha256": wish_sha256},
            "wish_sha256": wish_sha256,
            "inventor_roster": self.roster.to_dict(),
            "blueprint": self.blueprint.to_dict(),
            "blueprint_sha256": self.blueprint.sha256,
            "assignment_contract_path": "artifacts/invent/assignment.json",
            "contract_path": "artifacts/invent/invented.json",
            "invent_concept_capability": {
                "path": ".agents/skills/autonomous-workshop/references/invent-concept-v1.md",
                "sha256": "f" * 64,
            },
            "concept_root": root,
            "concept_pre_render_path": "artifacts/concept/r0001/pre-render.json",
            "concept_sealed_path": "artifacts/concept/r0001/sealed.json",
            "concept_effect_path": "artifacts/concept/r0001/effect.json",
            "concept_round": 1,
            "standing_concept_sha256": None,
            "revision_input_sha256": None,
        }
        return inputs, source

    def create_product(self):
        product_root = self.run_root / "artifacts/make/r0001/product"
        (product_root / "cad/project").mkdir(parents=True)
        (product_root / "cad/project/snap").mkdir()
        (product_root / "exports/stl").mkdir(parents=True)
        (product_root / "cad/project/validation").mkdir()
        product = {
            "title": "Moon Nook",
            "summary": "A tiny lunar observatory.",
            "components": ["observatory"],
        }
        product_bytes = canonical_json(product) + b"\n"
        verification = (
            b"# Verification pipeline record\n\n"
            b"- Recorded: content-addressed\n"
            b"- Mode: `final`\n"
            b"- Result: **PASS** (exit 0)\n\n"
            b"| # | command | result | seconds |\n"
            b"|---:|---|---:|---:|\n"
            b"| 1 | `check_thickness exact.stl` | rc=0 | 0.01 |\n"
        )
        preflight = (
            b"# Verification pipeline record\n\n"
            b"- Recorded: content-addressed\n"
            b"- Mode: `print-preflight`\n"
            b"- Result: **PASS** (exit 0)\n\n"
            b"| # | command | result | seconds |\n"
            b"|---:|---|---:|---:|\n"
            b"| 1 | `check_mesh exact.stl` | rc=0 | 0.01 |\n"
            b"| 2 | `check_thickness exact.stl --nozzle 0.4` | rc=0 | 0.01 |\n"
        )
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
        (product_root / "cad/project/validation/cad-build.json").write_bytes(verification)
        (product_root / "cad/project/measure").mkdir()
        (product_root / "cad/project/measure/print-preflight.md").write_bytes(
            preflight
        )
        render = Image.new("RGB", (900, 900), "#fff4df")
        pen = ImageDraw.Draw(render)
        pen.ellipse((180, 160, 720, 700), fill="#35aeb8")
        pen.polygon(((450, 230), (700, 690), (200, 690)), fill="#ffb445")
        render.save(product_root / "cad/project/snap/iso.png", format="PNG")
        signature = Image.new("RGB", (1800, 900), "#fff4df")
        signature_pen = ImageDraw.Draw(signature)
        for offset, color in ((0, "#35aeb8"), (600, "#ffb445"), (1200, "#35aeb8")):
            signature_pen.ellipse(
                (offset + 110, 160, offset + 490, 700), fill=color
            )
        signature.save(
            product_root / "cad/project/snap/signature.png", format="PNG"
        )
        review = {
            "schema_version": 6,
            "kind": "autonomous-workshop.signature-experience-review",
            "concept_sha256": self.invented.concept_sha256,
            "iso_sha256": sha256(
                (product_root / "cad/project/snap/iso.png").read_bytes()
            ),
            "signature_sha256": sha256(
                (product_root / "cad/project/snap/signature.png").read_bytes()
            ),
            "reviewer": "independent-native-visual-critic",
            "blind_held_read": "A compact moon observatory with a clear opening.",
            "blind_form_read": "A rounded observatory body with a deep opening.",
            "blind_subjects_read": "A moon observatory, opening, and rotating mask.",
            "blind_action_read": "The mask rotates through three exact states.",
            "blind_relationship_read": "The opening aligns with the observatory window.",
            "anti_generic_signature_read": "A deep lunar opening frames the mask.",
            "wish_revealed_after_blind_read": True,
            "held_object_unmistakable": True,
            "form_matches_wish": True,
            "subjects_match_wish": True,
            "action_matches_wish": True,
            "relationship_matches_wish": True,
            "anti_generic_signature_visible": True,
            "signature_experience_unmistakable": True,
            "finished_product_desirable": True,
            "review_rounds": 1,
            "critical_form_requirements": [
                {
                    "requirement": "The observatory must be rounded and volumetric.",
                    "blind_evidence": "The exact views show rounded depth.",
                    "matches": True,
                }
            ],
            "blocking_visual_defects": [],
            "print_preflight_sha256": sha256(preflight),
            "largest_risk": "The three states need a stronger direction cue.",
            "resolution": "The final sheet uses separated contrasting states.",
        }
        (product_root / "cad/project/snap/SIGNATURE-REVIEW.json").write_bytes(
            canonical_json(review)
        )
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
            cad_verification_path="cad/project/validation/cad-build.json",
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
        source_bytes = (self.run_root / "artifacts/invent/source.json").read_bytes()
        self.assert_outcome(
            "invent",
            "artifacts/invent/invented.json",
            invented_bytes,
            "make",
            (("artifacts/invent/source.json", sha256(source_bytes)),),
        )

    def test_routed_invent_seals_assignment_and_invented_contracts_together(self):
        assignment_path = "artifacts/invent/assignment.json"
        invented_path = "artifacts/invent/invented.json"
        invented_source = self.invented.to_dict()
        self.write_stage(
            "invent",
            {
                **self.match_inputs(),
                "assignment_contract_path": assignment_path,
                "contract_path": invented_path,
            },
        )
        self.write_json(
            "drafts/routed-invent.json",
            {
                "selected_inventor_id": "eve",
                "ranking": [item.to_dict() for item in self.assignment.ranking],
                "concept": invented_source["concept"],
                "research": invented_source["research"],
            },
        )

        self.run_tool("invent", "--source", "drafts/routed-invent.json")

        assignment_document, assignment_bytes = self.assert_canonical_file(
            assignment_path
        )
        invented_document, invented_bytes = self.assert_canonical_file(invented_path)
        source_bytes = (self.run_root / "artifacts/invent/source.json").read_bytes()
        self.assertEqual(
            NativeMatchAssignment.from_mapping(assignment_document), self.assignment
        )
        self.assertEqual(NativeInvented.from_mapping(invented_document), self.invented)
        proposal_document, _ = self.assert_canonical_file("agent-outcome.json")
        proposal = AgentOutcomeProposal.from_mapping(proposal_document)
        self.assertEqual(
            tuple((item.path, item.sha256) for item in proposal.outcome.artifacts),
            (
                (invented_path, sha256(invented_bytes)),
                (assignment_path, sha256(assignment_bytes)),
                ("artifacts/invent/source.json", sha256(source_bytes)),
            ),
        )
        self.assertEqual(proposal.outcome.proposed_transition, "make")

    def test_marked_routed_invent_seals_complete_pre_render_concept(self):
        inputs, source = self.create_marked_invent_source()
        self.write_stage("invent", inputs)
        self.write_json("drafts/marked-invent.json", source, canonical=True)

        self.run_tool(
            "invent",
            "--source",
            "drafts/marked-invent.json",
            "--concept-root",
            inputs["concept_root"],
        )

        pre_render_document, pre_render_bytes = self.assert_canonical_file(
            inputs["concept_pre_render_path"]
        )
        pre_render = PreRenderConcept.from_mapping(
            pre_render_document, root=self.run_root / inputs["concept_root"]
        )
        self.assertEqual(pre_render.provenance.round, 1)
        proposal_document, _ = self.assert_canonical_file("agent-outcome.json")
        proposal = AgentOutcomeProposal.from_mapping(proposal_document)
        paths = tuple(item.path for item in proposal.outcome.artifacts)
        self.assertEqual(
            paths,
            (
                "artifacts/invent/invented.json",
                "artifacts/invent/assignment.json",
                inputs["concept_pre_render_path"],
                "artifacts/invent/source.json",
                *("%s/%s" % (inputs["concept_root"], name) for name in (
                    "brief.json", "derived_wish.json", "descriptor.json",
                    "prompts.json", "research.json",
                )),
            ),
        )
        self.assertEqual(
            dict((item.path, item.sha256) for item in proposal.outcome.artifacts)[
                inputs["concept_pre_render_path"]
            ],
            sha256(pre_render_bytes),
        )
        decision = evaluate_routed_invent_stage(
            proposal,
            run_root=self.run_root,
            expected_checkpoint_sha256="1" * 64,
            expected_subject_sha256="2" * 64,
            wish_sha256=inputs["wish_sha256"],
            roster=self.roster,
            assignment_artifact_path="artifacts/invent/assignment.json",
            invented_artifact_path="artifacts/invent/invented.json",
            concept_context={
                "concept_root": inputs["concept_root"],
                "concept_pre_render_path": inputs["concept_pre_render_path"],
                "concept_round": 1,
                "standing_concept_sha256": None,
                "revision_input_sha256": None,
                "wish": inputs["wish"],
            },
        )
        self.assertEqual(
            decision.evidence.checks["pre_render_concept_sha256"],
            pre_render.concept_sha256,
        )
        brief_path = self.run_root / inputs["concept_root"] / "brief.json"
        brief_path.write_bytes(brief_path.read_bytes() + b" ")
        with self.assertRaises((ArtifactError, ContractError)):
            evaluate_routed_invent_stage(
                proposal,
                run_root=self.run_root,
                expected_checkpoint_sha256="1" * 64,
                expected_subject_sha256="2" * 64,
                wish_sha256=inputs["wish_sha256"],
                roster=self.roster,
                assignment_artifact_path="artifacts/invent/assignment.json",
                invented_artifact_path="artifacts/invent/invented.json",
                concept_context={
                    "concept_root": inputs["concept_root"],
                    "concept_pre_render_path": inputs["concept_pre_render_path"],
                    "concept_round": 1,
                    "standing_concept_sha256": None,
                    "revision_input_sha256": None,
                    "wish": inputs["wish"],
                },
            )

    def test_marked_routed_invent_rejects_incomplete_or_extra_source_tree(self):
        for mutation in ("missing-role", "extra-file"):
            with self.subTest(mutation=mutation):
                inputs, source = self.create_marked_invent_source()
                if mutation == "missing-role":
                    prompts_path = self.run_root / inputs["concept_root"] / "prompts.json"
                    prompts = json.loads(prompts_path.read_text())
                    prompts.pop("presentation")
                    prompts_path.write_bytes(canonical_json(prompts))
                else:
                    self.write_json(
                        "%s/extra.json" % inputs["concept_root"], {"extra": True}
                    )
                self.write_stage("invent", inputs)
                self.write_json("drafts/marked-invent.json", source, canonical=True)

                result = self.run_tool(
                    "invent",
                    "--source",
                    "drafts/marked-invent.json",
                    "--concept-root",
                    inputs["concept_root"],
                    expected=2,
                )
                self.assertIn("Invent Concept source is invalid", result.stderr)
                self.assertFalse((self.run_root / "agent-outcome.json").exists())
                if (self.run_root / "STAGE.json").exists():
                    (self.run_root / "STAGE.json").chmod(0o600)
                for path in (
                    self.run_root / "artifacts/invent/invented.json",
                    self.run_root / "artifacts/invent/assignment.json",
                    self.run_root / inputs["concept_pre_render_path"],
                    self.run_root / "artifacts/invent/source.json",
                ):
                    self.assertFalse(path.exists())

    def test_marked_invent_rejects_stale_round_and_substituted_wish_before_output(self):
        inputs, source = self.create_marked_invent_source()
        inputs["concept_round"] = 2
        self.write_stage("invent", inputs)
        self.write_json("drafts/marked-invent.json", source, canonical=True)
        result = self.run_tool(
            "invent", "--source", "drafts/marked-invent.json",
            "--concept-root", inputs["concept_root"], expected=2,
        )
        self.assertIn("not canonical for this round", result.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

        (self.run_root / "STAGE.json").chmod(0o600)
        inputs, source = self.create_marked_invent_source()
        self.write_stage("invent", inputs)
        self.write_json("drafts/marked-invent.json", source, canonical=True)
        (self.run_root / "WISH.json").write_bytes(
            canonical_json({"substituted": True})
        )
        result = self.run_tool(
            "invent", "--source", "drafts/marked-invent.json",
            "--concept-root", inputs["concept_root"], expected=2,
        )
        self.assertIn("Wish sha256 differs", result.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

    def test_marked_invent_rejects_linked_or_duplicate_key_source(self):
        inputs, source = self.create_marked_invent_source()
        brief = self.run_root / inputs["concept_root"] / "brief.json"
        outside = self.run_root / "outside.json"
        outside.write_bytes(brief.read_bytes())
        brief.unlink()
        brief.symlink_to(outside)
        self.write_stage("invent", inputs)
        self.write_json("drafts/marked-invent.json", source, canonical=True)
        result = self.run_tool(
            "invent", "--source", "drafts/marked-invent.json",
            "--concept-root", inputs["concept_root"], expected=2,
        )
        self.assertIn("regular files", result.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

        (self.run_root / "STAGE.json").chmod(0o600)
        brief.unlink()
        inputs, source = self.create_marked_invent_source()
        research = self.run_root / inputs["concept_root"] / "research.json"
        research.write_bytes(b'{"sources":[],"sources":[],"findings":[]}')
        self.write_stage("invent", inputs)
        self.write_json("drafts/marked-invent.json", source, canonical=True)
        result = self.run_tool(
            "invent", "--source", "drafts/marked-invent.json",
            "--concept-root", inputs["concept_root"], expected=2,
        )
        self.assertIn("strict finite UTF-8 JSON", result.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

    def test_spark_make_seals_all_compound_creative_contracts(self):
        product_root, _, _, _ = self.create_product()
        assignment_path = "artifacts/make/r0001/assignment.json"
        invented_path = "artifacts/make/r0001/invented.json"
        made_path = "artifacts/make/r0001/made.json"
        invented_source = self.invented.to_dict()
        self.write_stage(
            "make",
            {
                **self.match_inputs(),
                "creative_source_required": True,
                "assignment_contract_path": assignment_path,
                "invented_contract_path": invented_path,
            },
            round_index=1,
        )
        self.write_json(
            "drafts/spark-make.json",
            {
                "selected_inventor_id": "eve",
                "ranking": [item.to_dict() for item in self.assignment.ranking],
                "concept": invented_source["concept"],
                "research": invented_source["research"],
            },
        )

        self.run_tool(
            "make",
            "--source",
            "drafts/spark-make.json",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
        )

        made_document, made_bytes = self.assert_canonical_file(made_path)
        assignment_document, assignment_bytes = self.assert_canonical_file(
            assignment_path
        )
        invented_document, invented_bytes = self.assert_canonical_file(invented_path)
        assignment = NativeMatchAssignment.from_mapping(assignment_document)
        invented = NativeInvented.from_mapping(invented_document)
        made = NativeMade.from_mapping(made_document)
        self.assertEqual(assignment, self.assignment)
        self.assertEqual(invented, self.invented)
        made.assert_context(assignment, invented, expected_round=1)
        made.validate_product_tree(self.run_root)
        self.assertEqual(
            made.product_manifest.to_dict(),
            build_artifact_manifest(
                product_root, created_at="content-addressed"
            ).to_dict(),
        )
        proposal_document, _ = self.assert_canonical_file("agent-outcome.json")
        proposal = AgentOutcomeProposal.from_mapping(proposal_document)
        self.assertEqual(
            tuple((item.path, item.sha256) for item in proposal.outcome.artifacts),
            (
                (made_path, sha256(made_bytes)),
                (assignment_path, sha256(assignment_bytes)),
                (invented_path, sha256(invented_bytes)),
            ),
        )
        self.assertEqual(proposal.outcome.proposed_transition, "playtest")

    def test_marked_make_binds_sealed_concept_and_rejects_concept_pixels(self):
        inputs, source = self.create_marked_invent_source()
        self.write_stage("invent", inputs)
        self.write_json("drafts/marked-invent.json", source, canonical=True)
        self.run_tool(
            "invent", "--source", "drafts/marked-invent.json",
            "--concept-root", inputs["concept_root"],
        )
        assignment, _ = self.assert_canonical_file("artifacts/invent/assignment.json")
        invented, _ = self.assert_canonical_file("artifacts/invent/invented.json")
        pre_render_document, _ = self.assert_canonical_file(inputs["concept_pre_render_path"])
        pre_render = PreRenderConcept.from_mapping(
            pre_render_document, root=self.run_root / inputs["concept_root"]
        )
        descriptor_paths = (
            "images/front.png", "images/top.png", "images/bottom.png",
            "images/exploded.png", "images/components/observatory.png",
        )
        for index, path in enumerate(descriptor_paths):
            image = self.run_root / inputs["concept_root"] / path
            image.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes(b"\x89PNG\r\n\x1a\nconcept-%d" % index)
        sealed = seal_pre_render_concept(pre_render)
        sealed_path = inputs["concept_sealed_path"]
        self.write_json(sealed_path, sealed.to_dict(), canonical=True)
        effect = ConceptEffectEvidence(
            pre_render_concept_sha256=pre_render.concept_sha256,
            sealed_concept_sha256=sealed.concept_sha256,
            profile_id="openrouter-images-v1",
            profile_sha256="9" * 64,
            roles=tuple(
                ConceptEffectRoleEvidence(
                    role=(
                        ("front", "top", "bottom", "exploded")[index]
                        if index < 4 else "components.observatory"
                    ),
                    path=entry.path,
                    intent_sha256=("%x" % (index + 1)) * 64,
                    image_sha256=entry.sha256,
                    media_type="image/png",
                )
                for index, entry in enumerate(sealed.image_manifest.entries)
            ),
        )
        effect_path = inputs["concept_effect_path"]
        self.write_json(effect_path, effect.to_dict(), canonical=True)
        product_root, _, _, _ = self.create_product()
        make_inputs = {
            "assignment": assignment,
            "invented": invented,
            "invent_concept_capability": inputs["invent_concept_capability"],
            "sealed_concept": sealed.to_dict(),
            "sealed_concept_artifact": {
                "path": sealed_path,
                "sha256": sha256((self.run_root / sealed_path).read_bytes()),
            },
            "concept_effect": effect.to_dict(),
            "concept_effect_artifact": {
                "path": effect_path,
                "sha256": sha256((self.run_root / effect_path).read_bytes()),
            },
        }
        self.write_stage("make", make_inputs, round_index=1)
        self.run_tool(
            "make",
            "--product-root", "artifacts/make/r0001/product",
            "--cad-project-path", "cad/project",
            "--cad-verification-path", "validation/cad-build.json",
        )
        made_document, _ = self.assert_canonical_file("artifacts/make/r0001/made.json")
        made = NativeMade.from_mapping(made_document)
        self.assertEqual(made.schema_version, 2)
        self.assertEqual(made.concept_sha256, sealed.concept_sha256)
        self.assertEqual(made.concept_effect_sha256, effect.concept_effect_sha256)

        # Reusing exact Concept pixels in the product is prohibited even under another name.
        copied = product_root / "cad/project/snap/copied-concept.png"
        copied.write_bytes(
            (self.run_root / inputs["concept_root"] / descriptor_paths[0]).read_bytes()
        )
        (self.run_root / "agent-outcome.json").unlink()
        result = self.run_tool(
            "make",
            "--product-root", "artifacts/make/r0001/product",
            "--cad-project-path", "cad/project",
            "--cad-verification-path", "validation/cad-build.json",
            expected=2,
        )
        self.assertIn("must not copy sealed Concept image pixels", result.stderr)

    def test_spark_make_requires_creative_source_before_sealing(self):
        self.create_product()
        self.write_stage(
            "make",
            {
                **self.match_inputs(),
                "creative_source_required": True,
                "assignment_contract_path": (
                    "artifacts/make/r0001/assignment.json"
                ),
                "invented_contract_path": "artifacts/make/r0001/invented.json",
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
            "cad/project/validation/cad-build.json",
            expected=2,
        )

        self.assertIn("Spark Make requires --source creative JSON", result.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())
        self.assertFalse(
            (self.run_root / "artifacts/make/r0001/made.json").exists()
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
            "cad/project/validation/cad-build.json",
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

    def test_make_requires_explicit_chromatic_product_render(self):
        product_root, _, _, _ = self.create_product()
        render = product_root / "cad/project/snap/iso.png"
        render.unlink()
        self.write_stage(
            "make",
            {
                "assignment": self.assignment.to_dict(),
                "invented": self.invented.to_dict(),
                "feedback": [],
            },
            round_index=1,
        )

        missing = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("requires a product render", missing.stderr)

        grayscale = Image.new("L", (900, 900), 255)
        ImageDraw.Draw(grayscale).ellipse((180, 160, 720, 700), fill=0)
        grayscale.save(render, format="PNG")
        rejected = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("diagnostic grayscale image", rejected.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

        valid = Image.new("RGB", (900, 900), "#fff4df")
        ImageDraw.Draw(valid).ellipse((180, 160, 720, 700), fill="#35aeb8")
        valid.save(render, format="PNG")
        signature = product_root / "cad/project/snap/signature.png"
        signature.unlink()
        missing_signature = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("requires a signature render", missing_signature.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

        invalid_signature = Image.new("L", (1800, 900), 255)
        ImageDraw.Draw(invalid_signature).rectangle((120, 120, 1680, 780), fill=0)
        invalid_signature.save(signature, format="PNG")
        rejected_signature = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("signature render", rejected_signature.stderr)
        self.assertIn("diagnostic grayscale image", rejected_signature.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

    def test_make_requires_one_unambiguous_combined_cad_entry(self):
        product_root, _, _, _ = self.create_product()
        (product_root / "cad/project/presentation.step.py").write_text(
            "pass\n", encoding="utf-8"
        )
        self.write_stage(
            "make",
            {
                "assignment": self.assignment.to_dict(),
                "invented": self.invented.to_dict(),
                "feedback": [],
            },
            round_index=1,
        )

        rejected = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )

        self.assertIn("exactly one non-part *.step.py", rejected.stderr)
        self.assertIn("moon.step.py, presentation.step.py", rejected.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

    def test_make_requires_review_bound_to_final_signature_images(self):
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
        review_path = product_root / "cad/project/snap/SIGNATURE-REVIEW.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))

        review_path.unlink()
        missing = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("requires a signature review", missing.stderr)

        review_path.write_text(json.dumps(review, indent=2), encoding="utf-8")
        noncanonical = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("must use canonical JSON encoding", noncanonical.stderr)

        review["concept_sha256"] = "f" * 64
        review_path.write_bytes(canonical_json(review))
        stale_concept = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("signature review identity is invalid", stale_concept.stderr)
        review["concept_sha256"] = self.invented.concept_sha256

        review["blind_held_read"] = ""
        review_path.write_bytes(canonical_json(review))
        no_blind_read = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn(
            "Make blind held read must be bounded non-empty text",
            no_blind_read.stderr,
        )
        review["blind_held_read"] = (
            "A compact moon observatory with a clear opening."
        )

        review["held_object_unmistakable"] = False
        review_path.write_bytes(canonical_json(review))
        unreadable = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("final held object is unmistakable", unreadable.stderr)

        review["held_object_unmistakable"] = True
        review["form_matches_wish"] = False
        review_path.write_bytes(canonical_json(review))
        wrong_form = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("visible form matches the Wish and concept", wrong_form.stderr)

        review["form_matches_wish"] = True
        review["anti_generic_signature_visible"] = False
        review_path.write_bytes(canonical_json(review))
        generic = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("anti-generic signature is visible", generic.stderr)

        review["anti_generic_signature_visible"] = True
        review["finished_product_desirable"] = False
        review_path.write_bytes(canonical_json(review))
        undesirable = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("product looks finished and desirable", undesirable.stderr)

        review["finished_product_desirable"] = True
        review["relationship_matches_wish"] = False
        review_path.write_bytes(canonical_json(review))
        wrong_relationship = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn(
            "blind spatial relationship matches the Wish",
            wrong_relationship.stderr,
        )

        review["relationship_matches_wish"] = True
        review["review_rounds"] = 3
        review_path.write_bytes(canonical_json(review))
        unbounded_review = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("one or two review rounds", unbounded_review.stderr)

        review["review_rounds"] = 1
        review["critical_form_requirements"][0]["matches"] = False
        review_path.write_bytes(canonical_json(review))
        missing_form = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("critical form requirement 1 does not visibly match", missing_form.stderr)

        review["critical_form_requirements"][0]["matches"] = True
        review["blocking_visual_defects"] = [
            "The exact view is a constant-depth relief instead of a rounded body."
        ]
        review_path.write_bytes(canonical_json(review))
        blocked_form = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("still has blocking visual defects", blocked_form.stderr)

        review["blocking_visual_defects"] = []
        review["signature_sha256"] = "f" * 64
        review_path.write_bytes(canonical_json(review))
        stale = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("not bound to the final signature.png", stale.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

    def test_make_requires_current_full_tier_verification_report(self):
        product_root, _, _, _ = self.create_product()
        report = product_root / "cad/project/validation/cad-build.json"
        self.write_stage(
            "make",
            {
                "assignment": self.assignment.to_dict(),
                "invented": self.invented.to_dict(),
                "feedback": [],
            },
            round_index=1,
        )
        report.write_text(
            "# Verification pipeline record\n\n"
            "- Mode: `final`\n"
            "- Result: **PASS** (exit 0)\n\n"
            "| # | command | result | seconds |\n"
            "|---:|---|---:|---:|\n"
            "| 1 | `check_mesh exact.stl` | rc=0 | 0.01 |\n",
            encoding="utf-8",
        )
        omitted = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("passing final full-tier report", omitted.stderr)

        report.write_text(
            "# Verification pipeline record\n\n"
            "- Mode: `final`\n"
            "- Result: **FAIL** (exit 1)\n\n"
            "| # | command | result | seconds |\n"
            "|---:|---|---:|---:|\n"
            "| 1 | `check_thickness exact.stl` | rc=1 | 0.01 |\n\n"
            "---\n\n## Previous pipeline record\n\n"
            "# Verification pipeline record\n\n"
            "- Mode: `final`\n"
            "- Result: **PASS** (exit 0)\n\n"
            "| 1 | `check_thickness old.stl` | rc=0 | 0.01 |\n",
            encoding="utf-8",
        )
        failed_current = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("passing final full-tier report", failed_current.stderr)

    def test_make_requires_hash_bound_standard_print_preflight(self):
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
        preflight = product_root / "cad/project/measure/print-preflight.md"
        preflight.write_text(
            "# Verification pipeline record\n\n"
            "- Mode: `print-preflight`\n"
            "- Result: **PASS** (exit 0)\n\n"
            "| # | command | result | seconds |\n"
            "|---:|---|---:|---:|\n"
            "| 1 | `check_mesh exact.stl` | rc=0 | 0.01 |\n"
            "| 2 | `check_thickness exact.stl --nozzle 0.1` | rc=0 | 0.01 |\n",
            encoding="utf-8",
        )
        review_path = product_root / "cad/project/snap/SIGNATURE-REVIEW.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))
        review["print_preflight_sha256"] = sha256(preflight.read_bytes())
        review_path.write_bytes(canonical_json(review))

        completed = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )

        self.assertIn("standard 0.4 mm thickness", completed.stderr)

    def test_make_verification_must_belong_to_declared_cad_project(self):
        product_root, _, _, verification = self.create_product()
        outside = product_root / "validation/cad-build.json"
        outside.parent.mkdir()
        outside.write_bytes(verification)
        self.write_stage(
            "make",
            {
                "assignment": self.assignment.to_dict(),
                "invented": self.invented.to_dict(),
                "feedback": [],
            },
            round_index=1,
        )
        rejected = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "validation/cad-build.json",
            expected=2,
        )
        self.assertIn(
            "CAD verification must live inside the declared CAD project",
            rejected.stderr,
        )

    def test_make_rejects_duplicate_final_snap_family(self):
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
        duplicate = product_root / "snap"
        duplicate.mkdir()
        (duplicate / "iso.png").write_bytes(
            (product_root / "cad/project/snap/iso.png").read_bytes()
        )
        rejected = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )
        self.assertIn("duplicate final snap family", rejected.stderr)
        self.assertIn("snap/iso.png", rejected.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

    def test_make_rejects_invalid_required_product_metadata_before_outputs(self):
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
        invalid_products = (
            (
                "aliases do not replace required fields",
                {
                    "name": "Moon Nook",
                    "description": "A tiny lunar observatory.",
                },
                "Make product title",
            ),
            (
                "missing title",
                {"summary": "A tiny lunar observatory."},
                "Make product title",
            ),
            (
                "blank title",
                {"title": " \t\n", "summary": "A tiny lunar observatory."},
                "Make product title",
            ),
            (
                "oversized title",
                {"title": "x" * 2_001, "summary": "A tiny lunar observatory."},
                "Make product title",
            ),
            (
                "missing summary",
                {"title": "Moon Nook"},
                "Make product summary",
            ),
            (
                "blank summary",
                {"title": "Moon Nook", "summary": " \t\n"},
                "Make product summary",
            ),
            (
                "oversized summary",
                {"title": "Moon Nook", "summary": "x" * 2_001},
                "Make product summary",
            ),
            (
                "control character",
                {"title": "Moon Nook", "summary": "Tiny\u0000 observatory"},
                "Make product summary",
            ),
        )

        for label, product, error_label in invalid_products:
            with self.subTest(label=label):
                (product_root / "product.json").write_bytes(canonical_json(product))
                result = self.run_tool(
                    "make",
                    "--product-root",
                    "artifacts/make/r0001/product",
                    "--cad-project-path",
                    "cad/project",
                    "--cad-verification-path",
                    "cad/project/validation/cad-build.json",
                    expected=2,
                )
                self.assertIn(error_label, result.stderr)
                with self.assertRaisesRegex(
                    ContractError, error_label.replace("Make ", "Made ")
                ):
                    Made(
                        product_root,
                        build_artifact_manifest(
                            product_root, created_at="content-addressed"
                        ),
                        product,
                    )
                self.assertFalse(
                    (self.run_root / "artifacts/make/r0001/made.json").exists()
                )
                self.assertFalse((self.run_root / "agent-outcome.json").exists())

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
                    "cad/project/validation/cad-build.json",
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
            "cad/project/validation/cad-build.json",
        )

    def test_make_prunes_empty_directories_before_writing_a_proposal(self):
        product_root, _, _, _ = self.create_product()
        (product_root / "cad/spec").mkdir()
        (product_root / "cad/exports/nested").mkdir(parents=True)
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
            "cad/project/validation/cad-build.json",
        )

        self.assertFalse((product_root / "cad/spec").exists())
        self.assertFalse((product_root / "cad/exports").exists())
        self.assertTrue(
            (self.run_root / "artifacts/make/r0001/made.json").is_file()
        )
        self.assertTrue((self.run_root / "agent-outcome.json").is_file())

    def test_make_prunes_derived_cad_cache_before_writing_a_proposal(self):
        product_root, _, _, _ = self.create_product()
        cache = product_root / "cad/project/__cadgen__/models/part.step.py"
        cache.mkdir(parents=True)
        (cache / "topology.glb").write_bytes(b"derived cache\n")
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
            "cad/project/validation/cad-build.json",
        )

        self.assertFalse((product_root / "cad/project/__cadgen__").exists())
        made, _ = self.assert_canonical_file(
            "artifacts/make/r0001/made.json"
        )
        self.assertFalse(
            any(
                "__cadgen__" in entry["path"].split("/")
                for entry in made["product_manifest"]["entries"]
            )
        )

    def test_make_tolerates_a_sandbox_protected_empty_cad_cache(self):
        product_root, _, _, _ = self.create_product()
        project = product_root / "cad/project"
        cache = project / "__cadgen__"
        cache.mkdir()
        self.write_stage(
            "make",
            {
                "assignment": self.assignment.to_dict(),
                "invented": self.invented.to_dict(),
                "feedback": [],
            },
            round_index=1,
        )
        project.chmod(0o500)
        try:
            self.run_tool(
                "make",
                "--product-root",
                "artifacts/make/r0001/product",
                "--cad-project-path",
                "cad/project",
                "--cad-verification-path",
                "cad/project/validation/cad-build.json",
            )
        finally:
            project.chmod(0o700)

        self.assertTrue(cache.is_dir())
        made, _ = self.assert_canonical_file(
            "artifacts/make/r0001/made.json"
        )
        self.assertFalse(
            any(
                "__cadgen__" in entry["path"].split("/")
                for entry in made["product_manifest"]["entries"]
            )
        )

    def test_make_rejects_linked_derived_cad_cache(self):
        product_root, _, _, _ = self.create_product()
        outside = self.run_root / "outside-cache"
        outside.mkdir()
        (outside / "keep.txt").write_text("keep\n", encoding="utf-8")
        (product_root / "cad/project/__cadgen__").symlink_to(
            outside, target_is_directory=True
        )
        self.write_stage(
            "make",
            {
                "assignment": self.assignment.to_dict(),
                "invented": self.invented.to_dict(),
                "feedback": [],
            },
            round_index=1,
        )

        rejected = self.run_tool(
            "make",
            "--product-root",
            "artifacts/make/r0001/product",
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "cad/project/validation/cad-build.json",
            expected=2,
        )

        self.assertIn("symlink or special directory", rejected.stderr)
        self.assertEqual((outside / "keep.txt").read_text(), "keep\n")
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

    def test_make_revision_seals_exact_contradiction_evidence_for_invent(self):
        evidence_root = self.run_root / "artifacts/make/r0001/revision-evidence"
        evidence_root.mkdir(parents=True)
        evidence = b'{"clearance_mm":-0.3,"passed":false}\n'
        (evidence_root / "geometry-check.json").write_bytes(evidence)
        contract_path = "artifacts/make/r0001/invent-revision-request.json"
        self.write_stage(
            "make",
            {
                "assignment": self.assignment.to_dict(),
                "invented": self.invented.to_dict(),
                "invent_revision_allowed": True,
                "invent_revision_contract_path": contract_path,
                "invent_revision_evidence_root": (
                    "artifacts/make/r0001/revision-evidence"
                ),
            },
            round_index=1,
        )
        source = {
            "feedback": [
                {
                    "code": "forced-overlap",
                    "area": "keel-index-interface",
                    "severity": "block",
                    "finding": "The sealed dimensions force a 0.3 mm overlap.",
                    "change": "Move the index capsule or revise its dimensions.",
                    "evidence_refs": ["missing.json"],
                    "invalidates": ["invent", "make", "playtest", "release"],
                }
            ]
        }
        self.write_json("drafts/make-revision.json", source)

        rejected = self.run_tool(
            "make-revision",
            "--source",
            "drafts/make-revision.json",
            "--evidence-root",
            "artifacts/make/r0001/revision-evidence",
            expected=2,
        )
        self.assertIn("references absent evidence", rejected.stderr)
        self.assertFalse((self.run_root / contract_path).exists())
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

        source["feedback"][0]["evidence_refs"] = ["geometry-check.json"]
        source_path = self.write_json("drafts/make-revision.json", source)
        source_bytes = source_path.read_bytes()
        self.run_tool(
            "make-revision",
            "--source",
            "drafts/make-revision.json",
            "--evidence-root",
            "artifacts/make/r0001/revision-evidence",
        )

        document, contract_bytes = self.assert_canonical_file(contract_path)
        request = NativeMakeInventRevision.from_mapping(document)
        request.assert_context(
            self.assignment, self.invented, expected_round=1
        )
        request.validate_evidence_tree(self.run_root)
        archived_source_path = (
            "artifacts/make/r0001/invent-revision-source.json"
        )
        self.assertEqual(
            (self.run_root / archived_source_path).read_bytes(), source_bytes
        )
        self.assert_outcome(
            "make",
            contract_path,
            contract_bytes,
            "invent",
            ((archived_source_path, sha256(source_bytes)),),
        )

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
            "invalidates": ["playtest", "release"],
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

        feedback["severity"] = "block"
        feedback["area"] = "invent"
        feedback["change"] = "Revise the concept before rebuilding the product."
        feedback["invalidates"] = ["invent", "make", "playtest", "release"]
        self.write_json(
            "drafts/playtest-reinvent.json",
            {"checks": checks, "feedback": [feedback], "verdict": "block"},
        )
        self.run_tool(
            "playtest",
            "--source",
            "drafts/playtest-reinvent.json",
            "--evidence-root",
            "artifacts/playtest/r0001/evidence",
        )
        reinvent_document, reinvent_bytes = self.assert_canonical_file(
            "artifacts/playtest/r0001/playtested.json"
        )
        self.assertEqual(reinvent_document["verdict"], "block")
        self.assertEqual(
            NativePlaytested.from_mapping(reinvent_document).proposed_transition,
            "invent",
        )
        self.assert_outcome(
            "playtest",
            "artifacts/playtest/r0001/playtested.json",
            reinvent_bytes,
            "invent",
        )

        feedback["invalidates"] = ["invent", "playtest", "release"]
        self.write_json(
            "drafts/playtest-invalid-invalidation.json",
            {"checks": checks, "feedback": [feedback], "verdict": "block"},
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
            "every downstream stage",
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

    def test_quest_playtest_accepts_two_matching_artifact_binding_keys(self):
        made = self.create_made()
        evidence_root = self.run_root / "artifacts/playtest/r0001/evidence"
        (evidence_root / "configs").mkdir(parents=True)
        checks = []
        check_ids = self.blueprint.required_playtest_checks()
        product_sha256 = made.product_manifest.artifact_sha256
        for index, check_id in enumerate(check_ids):
            config_ref = "configs/%s.json" % check_id
            evidence_ref = "%s.json" % check_id
            self.write_json(
                "artifacts/playtest/r0001/evidence/%s" % config_ref,
                {
                    "schema_version": 1,
                    "check_id": check_id,
                    "artifact_sha256": product_sha256,
                    "product_artifact_sha256": (
                        "0" * 64 if index == 0 else product_sha256
                    ),
                    "seed": 42,
                },
            )
            (evidence_root / evidence_ref).write_bytes(
                canonical_json({"check": check_id, "ok": True}) + b"\n"
            )
            checks.append(
                {
                    "check_id": check_id,
                    "passed": True,
                    "evaluator": "workshop-host",
                    "evaluator_version": "1.0.0",
                    "config_ref": config_ref,
                    "evidence_ref": evidence_ref,
                    "observed_at": "2026-08-26T00:00:00Z",
                    "observations": {"ok": True},
                }
            )
        self.write_stage(
            "playtest",
            {
                "effort": "quest",
                "made": made.to_dict(),
                "required_check_ids": list(check_ids),
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
        self.assertIn("not bound to the current Made revision", rejected.stderr)
        self.assertFalse((self.run_root / "agent-outcome.json").exists())

        self.write_json(
            "artifacts/playtest/r0001/evidence/configs/%s.json" % check_ids[0],
            {
                "schema_version": 1,
                "check_id": check_ids[0],
                "artifact_sha256": product_sha256,
                "product_artifact_sha256": product_sha256,
                "seed": 42,
            },
        )
        self.run_tool(
            "playtest",
            "--source",
            "drafts/playtest.json",
            "--evidence-root",
            "artifacts/playtest/r0001/evidence",
        )

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
            "complete",
        )

        self.write_stage(
            "release",
            {
                "made": made.to_dict(),
                "playtested": playtested.to_dict(),
                "release_contract": {
                    "native_release_schema_version": 2,
                    "manual_path": "MANUAL.pdf",
                    "product_schema_version": 4,
                    "product_status": "manual-ready",
                    "manual_design_evidence_path": "MANUAL-DESIGN.json",
                    "manual_design_evidence_schema_version": 1,
                },
            },
            round_index=1,
        )
        missing_design_evidence = self.run_tool(
            "release",
            "--package-root",
            "artifacts/release/package",
            expected=2,
        )
        self.assertIn(
            "manifest lacks MANUAL-DESIGN.json",
            missing_design_evidence.stderr,
        )

        self.write_stage(
            "release",
            {"made": made.to_dict(), "playtested": playtested.to_dict()},
            round_index=1,
        )

        invalid_product_cases = (
            (
                {"hero": {"headline": "Website copy is not a Release gate."}},
                "fields are invalid",
            ),
            (
                {"schema_version": 3, "status": "page-ready"},
                "fields are invalid",
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
            "cad/project/validation/cad-build.json",
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
        self.assertIn(
            "match,invent,make,playtest,make-revision,release",
            completed.stdout,
        )


if __name__ == "__main__":
    unittest.main()
