import hashlib
import io
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import reportlab
from PIL import Image, ImageDraw
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from workshop.artifacts import build_artifact_manifest
from workshop.workflow.native_run import (
    _MAX_NATIVE_TURNS,
    native_run_paths,
    resume_native_run,
    start_native_run,
)
from workshop.errors import ArtifactError, StateConflict
from workshop.invent.gamevault import GameVaultClient, GameVaultConfig
from workshop.invent.vault import RUN_VAULT_PATH, Vault
from tests.invent.fake_gamevault import E2E_NODES, FakeGameVaultTransport, install_fake_gamevault
from workshop.errors import ArtifactError, EffectError, StateConflict
from workshop.invent.native import NativeInvented
from workshop.integrations.factory import FACTORY_CONTENT_MAPPING
from workshop.make.native import NativeMade
from workshop.make.native_gate import (
    NATIVE_CAD_FULL_TIER,
    NATIVE_CAD_NON_PRINT_READY_TIER,
    NATIVE_CAD_NON_PRINT_READY_VERIFIER_MODE,
    NATIVE_CAD_VERIFIER_MODE,
    NATIVE_CAD_VERIFIER_PATH,
    CapturedVerifierStream,
    NativeCadGateError,
    NativeCadGateEvidence,
)
from workshop.match.native import NativeMatchAssignment
from workshop.playtest.native import NativePlaytested
from workshop.release.native import (
    NATIVE_RELEASE_PLAYTEST_OMISSION_PATH,
    NativeRelease,
    direct_release_claims,
    playtest_omission_record,
    playtest_omission_sha256,
)
from workshop.release.verification import (
    PRODUCT_VERIFICATION_PATH,
    read_product_verification,
)
from workshop.runtime import (
    CodexRecoverableInvocationError,
    Receipt,
)
from workshop.runtime.agent_assets import ProductRunAgentAssets
from workshop.wish import Wish
from workshop.workflow import AgentRun
from workshop.workflow.agent_run import AgentArtifact, AgentOutcome
from workshop.workflow.proposals import AgentOutcomeProposal


_OBSERVED_AT = "2026-08-26T00:00:00+00:00"
_PAGE_URL = "https://www.autonomous.ai/factory/product/orbit-dog"
_COVER_URL = "https://cdn.autonomous.ai/products/orbit-dog/cover.webp"
_MANUAL_URL = "https://cdn.autonomous.ai/projects/orbit-dog-1/MANUAL.pdf"
_SESSION_CHECKPOINT = b'{"session_id":"fixture-native-session"}\n'


def _canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json(value))


def stage_round(run_root):
    return _read_json(Path(run_root) / "STAGE.json")["round"]


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(content):
    return hashlib.sha256(content).hexdigest()


def _manual_pdf():
    """Return one deterministic, text-extractable A6 manual fixture."""

    font_name = "WorkshopFixtureVera"
    if font_name not in pdfmetrics.getRegisteredFontNames():
        font_path = Path(reportlab.__file__).resolve().parent / "fonts/Vera.ttf"
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
    output = io.BytesIO()
    canvas = Canvas(
        output,
        pagesize=(297.64, 419.53),
        pageCompression=1,
        invariant=1,
        initialFontName=font_name,
    )
    for page, lines in (
        (
            1,
            (
                "Orbit Dog Draughts",
                "Meet the exact board and every playing piece.",
                "A tiny orbital match is ready to begin.",
            ),
        ),
        (
            2,
            (
                "Set up and play",
                "Use standard English draughts rules.",
                "For ages fourteen and older. Keep small parts away.",
            ),
        ),
    ):
        del page
        canvas.setFont(font_name, 15)
        canvas.drawString(30, 370, lines[0])
        canvas.setFont(font_name, 10)
        canvas.drawString(30, 340, lines[1])
        canvas.drawString(30, 320, lines[2])
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def _manual_design_evidence(manual, made):
    visual = next(
        entry
        for entry in made["product_manifest"]["entries"]
        if entry["path"] == "assembled.stl"
    )
    return {
        "schema_version": 1,
        "kind": "autonomous-workshop.manual-design-evidence",
        "manual_sha256": _sha256(manual),
        "design_mode": "bespoke",
        "creative_brief": {
            "emotional_promise": "Unbox a tiny orbital rivalry that feels ready for a first match.",
            "physical_format": "Two-page A6 field card",
            "format_rationale": "Two compact pages keep the inventory and first turn visible together.",
            "visual_motif": "Orbital paths connect exact piece silhouettes to numbered actions.",
            "palette": ["deep space navy", "warm paper white", "signal orange"],
            "typography": ["Vera display", "Vera instructional body"],
            "teaching_arc": [
                "Meet the exact board and pieces",
                "Set up the first orbital match",
                "Play, reset, and pack away",
            ],
        },
        "product_visuals": [
            {
                "source_path": visual["path"],
                "source_sha256": visual["sha256"],
                "pages": [1, 2],
            }
        ],
        "review": {
            "page_count": 2,
            "color_pages": [1, 2],
            "grayscale_pages": [1, 2],
            "first_time_owner_pass": True,
            "independent_reviewer": "native-subagent",
            "findings": ["The setup action initially competed with the cover title."],
            "resolved_changes": ["Moved setup to page two and strengthened its action hierarchy."],
            "status": "approved",
        },
    }


def _product_run_assets_without_direct_release(
    root: Path,
    *,
    markdown_release: bool = False,
) -> ProductRunAgentAssets:
    """Copy a frozen pre-direct-Release product-run protocol for compatibility tests."""

    repository = Path(__file__).resolve().parents[2]
    legacy_root = root / "legacy-assets"
    constitution = legacy_root / ".agents/product-run/AGENTS.md"
    constitution.parent.mkdir(parents=True)
    shutil.copy2(repository / ".agents/product-run/AGENTS.md", constitution)
    skill_root = legacy_root / ".agents/product-run/.agents/skills/autonomous-workshop"
    shutil.copytree(
        repository / ".agents/product-run/.agents/skills/autonomous-workshop",
        skill_root,
    )
    shutil.copytree(repository / "inventors", legacy_root / "inventors")
    (skill_root / "references/direct-release-v1.md").unlink()
    if markdown_release:
        (skill_root / "scripts/pdf_validator.py").unlink()
        (skill_root / "references/release-terminal-v1.md").unlink()
    return ProductRunAgentAssets(
        constitution=constitution,
        skill_root=skill_root,
        sha256="0" * 64,
        source="repository",
    )


def _failed_cad_gate(
    made,
    arguments,
    *,
    failure_code,
    timed_out,
    stdout_content=b"CAD verifier inspected the sealed revision.\n",
    stderr_content=None,
    verification_tier=NATIVE_CAD_FULL_TIER,
):
    if stderr_content is None:
        stderr_content = (
            failure_code + ": repair the CAD project and retry.\n"
        ).encode("utf-8")
    stdout = CapturedVerifierStream.from_bytes(
        stdout_content, 64 * 1024
    )
    stderr = CapturedVerifierStream.from_bytes(
        stderr_content,
        64 * 1024,
    )
    lower_tier = verification_tier == NATIVE_CAD_NON_PRINT_READY_TIER
    evidence_stage = arguments.get("evidence_stage", "make")
    evidence = NativeCadGateEvidence(
        passed=False,
        failure_code=failure_code,
        made_sha256=made.made_sha256,
        product_artifact_sha256=made.product_manifest.artifact_sha256,
        cad_project_path=made.cad_project_path,
        cad_project_sha256=_sha256(made.made_sha256.encode("ascii")),
        verifier_sha256=arguments["expected_verifier_sha256"],
        command=(
            "<python>",
            NATIVE_CAD_VERIFIER_PATH,
            "<isolated-cad-project>",
            "--fresh",
            "--exports",
            "--strict-fit",
            *(("--skip-thickness",) if lower_tier else ()),
        ),
        returncode=-9 if timed_out else 7,
        duration_ms=1_800_000 if timed_out else 11,
        timed_out=timed_out,
        stdout=stdout,
        stderr=stderr,
        source_tree_unchanged=True,
        verification_tier=verification_tier,
        verifier_mode=(
            NATIVE_CAD_NON_PRINT_READY_VERIFIER_MODE
            if lower_tier
            else NATIVE_CAD_VERIFIER_MODE
        ),
        evidence_stage=evidence_stage,
    )
    evidence_parent = (
        Path(arguments["host_state_root"]) / "evidence" / evidence_stage
    )
    current = Path(arguments["host_state_root"])
    for part in ("evidence", evidence_stage):
        current = current / part
        current.mkdir(mode=0o700, exist_ok=True)
        os.chmod(current, 0o700)
    evidence_path = evidence_parent / (
        "r%04d-cad-gate.json" % made.round
    )
    evidence_path.write_bytes(_canonical_json(evidence.to_dict()) + b"\n")
    os.chmod(evidence_path, 0o600)
    return NativeCadGateError(failure_code, evidence, evidence_path)


def _write_fixture_render(project):
    """Make must ship one chromatic presentation render at snap/iso.png.

    Mirrors the render checked by ``test_stage_proposal_tool``: a real RGB PNG
    with tonal variation, so the finalizer's grayscale-mask guard passes.
    """
    snap = project / "snap"
    snap.mkdir(exist_ok=True)
    render = Image.new("RGB", (900, 900), "#fff4df")
    pen = ImageDraw.Draw(render)
    pen.ellipse((180, 160, 720, 700), fill="#35aeb8")
    pen.polygon(((450, 230), (700, 690), (200, 690)), fill="#ffb445")
    render.save(snap / "iso.png", format="PNG")


class _SessionOutcome:
    def __init__(self, arguments, stage):
        self.arguments = dict(arguments)
        stage_input = {
            "match": 50,
            "invent": 100,
            "make": 200,
            "playtest": 300,
            "release": 400,
        }[stage]
        self.input_tokens = stage_input
        self.cached_input_tokens = stage_input * 3 // 4
        self.cache_write_input_tokens = stage_input // 20
        self.output_tokens = stage_input // 10
        self.reasoning_output_tokens = stage_input // 20

    def to_dict(self):
        return {
            "status": "completed",
            "session": {
                "product_id": self.arguments["product_id"],
                "wish_sha256": self.arguments["wish_sha256"],
                "constitution_sha256": self.arguments["constitution_sha256"],
                "checkpoint_sha256": "c" * 64,
            },
            "used_web_search": False,
        }


def _fixture_components():
    return {
        "board": {
            "name": "Board",
            "duty": "the playing surface that holds every waypoint",
            "form": "flat concentric-ringed 200 mm square panel",
            "dimensions_mm": {"length_mm": 200.0, "width_mm": 200.0, "height_mm": 5.0},
            "placement": "centered on the table",
            "interfaces": "pieces rest in 1 mm deep orbital waypoint recesses",
            "mates_with": ["pieces"],
            "signature": False,
        },
        "pieces": {
            "name": "Pieces",
            "duty": "the two draughts piece families that are moved and captured",
            "form": "stackable dog-silhouette discs",
            "dimensions_mm": {"length_mm": 20.0, "width_mm": 20.0, "height_mm": 8.0},
            "placement": "set out on the board's waypoints",
            "interfaces": "seat into the board's waypoint recesses",
            "mates_with": ["board"],
            "signature": True,
        },
    }


class _OneSessionProductAgent:
    """A deterministic stand-in for one resumed native Codex session."""

    def __init__(
        self, *, playtest_plan=None, confirm_first_lead=False, product_contract_name_collisions=False
    ):
        self.starts = []
        self.resumes = []
        self.stage_packets = []
        self.finalizer_commands = []
        self.playtest_plan = list(playtest_plan) if playtest_plan else []
        self.confirm_first_lead = confirm_first_lead
        self.product_contract_name_collisions = product_contract_name_collisions

    @staticmethod
    def _checkpoint(arguments):
        path = Path(arguments["host_state_root"]) / "codex-session.json"
        path.write_bytes(_SESSION_CHECKPOINT)
        os.chmod(path, 0o600)

    @staticmethod
    def _assert_public_arguments(arguments):
        rendered = repr(arguments)
        if "FACTORY" in rendered or "fixture-host-secret" in rendered:
            raise AssertionError("host effect authority reached the native launcher")

    def _run_finalizer(self, run_root, *arguments):
        script = (
            run_root
            / ".agents"
            / "skills"
            / "autonomous-workshop"
            / "scripts"
            / "stage_proposal.py"
        )
        command = (
            sys.executable,
            str(script),
            "--run-root",
            str(run_root),
            *arguments,
        )
        self.finalizer_commands.append(command)
        completed = subprocess.run(
            command,
            cwd=str(run_root),
            env={
                "PATH": os.defpath,
                "PYTHONDONTWRITEBYTECODE": "1",
                "WORKSHOP_PYTHON": str(Path(sys.executable).absolute()),
            },
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                "stage proposal failed (%s): %s"
                % (completed.returncode, completed.stderr)
            )
        result = json.loads(completed.stdout)
        expected_outcome = (
            "artifacts/make/r%04d/product/groups/%s.json" % (stage_round(run_root), arguments[-1])
            if arguments[0] == "make-group"
            else "agent-outcome.json"
        )
        assert result["outcome_path"] == expected_outcome, "finalizer authored an unexpected outcome"

    def _author_match(self, run_root, stage):
        ranking = self._ranking(stage)
        source = "authored/match.json"
        _write_json(
            run_root / source,
            {"selected_inventor_id": "alice", "ranking": ranking},
        )
        self._run_finalizer(run_root, "match", "--source", source)

    @staticmethod
    def _ranking(stage):
        inventors = stage["inputs"]["inventor_roster"]["inventors"]
        ids = [entry["inventor_id"] for entry in inventors]
        if ids != sorted(ids) or "alice" not in ids:
            raise AssertionError("fixture received a non-canonical inventor roster")
        return [
            {
                "inventor_id": inventor_id,
                "rationale": (
                    "Alice best preserves known draughts rules while making the "
                    "physical set structurally specific to the Wish."
                    if inventor_id == "alice"
                    else "%s is a valid specialist, but another Taste fits less directly."
                    % inventor_id.title()
                ),
            }
            for inventor_id in (["alice"] + [item for item in ids if item != "alice"])
        ]
    def _author_invent(self, run_root, stage):
        assignment = stage["inputs"].get("assignment")
        if assignment is not None and assignment["selected_inventor_id"] != "alice":
            raise AssertionError("Invent did not receive the accepted Match assignment")
        revised = (
            "failing_playtested" in stage["inputs"]
            or "make_revision_request" in stage["inputs"]
        )
        source = "authored/invent.json"
        authored = {
                "concept": {
                    "title": (
                        "Orbit Dog Draughts — Aligned Orbits"
                        if revised
                        else "Orbit Dog Draughts"
                    ),
                    "summary": (
                        "A pocket draughts set whose concentric board, opposing orbit "
                        "packs, and king pieces turn the requested dog into the geometry "
                        "of a familiar public-domain game."
                        + (
                            " Every orbit now maps one-to-one to legal squares."
                            if revised
                            else ""
                        )
                    ),
                    "signature_decision": (
                        "Every playable square is an orbital waypoint and each side uses "
                        "a distinct dog-pack silhouette without changing draughts rules."
                    ),
                    "interaction": (
                        "Two players move dog pieces along the board's orbital "
                        "waypoints, capture by jumping, and stack a piece to crown it."
                    ),
                    "envelope_mm": {
                        "length_mm": 200.0,
                        "width_mm": 200.0,
                        "height_mm": 20.0,
                    },
                    "mechanisms": ["stacking-and-balancing", "square-grid"],
                    "build_plan": [
                        {"group": "board", "parts": ["board"], "exit_criteria": "Recesses are 1 mm deep."},
                        {"group": "pieces", "parts": ["pieces"], "exit_criteria": "Pieces seat and stack."},
                    ],
                    "components": [
                        {"key": key, **fields}
                        for key, fields in _fixture_components().items()
                    ],
                    "assumptions": ["Players know English draughts rules."],
                    "unresolved_risks": [
                        "Physical fit and handling have not been tested by a person."
                    ],
                },
                "research": {
                    "rules_basis": "English draughts movement remains unchanged.",
                    "sources": [
                        {
                            "title": "English draughts rules reference",
                            "url": "https://www.fmjd.org/",
                            "use": "Known-rule baseline only",
                        }
                    ],
                    "safety_boundary": "Ages 14+; small parts are explicitly identified.",
                },
            }
        if assignment is None:
            authored.update(
                {
                    "selected_inventor_id": "alice",
                    "ranking": self._ranking(stage),
                }
            )
        _write_json(run_root / source, authored)
        self._run_finalizer(run_root, "invent", "--source", source)

    def _author_make(self, run_root, stage):
        inputs = stage["inputs"]
        product_root_value = inputs["product_root"]
        product_root = run_root / product_root_value
        (product_root / "cad" / "project").mkdir(parents=True, exist_ok=True)
        _write_fixture_render(product_root / "cad" / "project")
        (product_root / "cad" / "project" / "validation").mkdir(exist_ok=True)
        wish = _read_json(run_root / "WISH.json")
        invented = inputs.get("invented")
        spark_source = None
        if invented is None:
            spark_source = "authored/spark-make.json"
            spark_authored = {
                "selected_inventor_id": "alice",
                "ranking": self._ranking(stage),
                "concept": {
                    "title": "Orbit Dog Draughts",
                    "summary": (
                        "A compact orbital draughts set designed and built in one "
                        "Spark Make turn."
                    ),
                    "signature_decision": (
                        "Every playable square is an orbital waypoint without changing "
                        "the familiar rules."
                    ),
                    "interaction": (
                        "Two players move dog pieces along the board's orbital "
                        "waypoints, capture by jumping, and stack a piece to crown it."
                    ),
                    "envelope_mm": {
                        "length_mm": 200.0,
                        "width_mm": 200.0,
                        "height_mm": 20.0,
                    },
                    "mechanisms": ["stacking-and-balancing", "square-grid"],
                    "build_plan": [
                        {"group": "board", "parts": ["board"], "exit_criteria": "Recesses are 1 mm deep."},
                        {"group": "pieces", "parts": ["pieces"], "exit_criteria": "Pieces seat and stack."},
                    ],
                    "components": [
                        {"key": key, **fields}
                        for key, fields in _fixture_components().items()
                    ],
                    "assumptions": ["Players know English draughts rules."],
                    "unresolved_risks": [
                        "Physical fit and handling have not been tested by a person."
                    ],
                },
                "research": {
                    "rules_basis": "English draughts movement remains unchanged.",
                    "scope": "Compact evidence sufficient for the Spark build.",
                },
            }
            _write_json(run_root / spark_source, spark_authored)
            invented = {"concept": spark_authored["concept"]}
        if not invented["concept"]["title"].startswith("Orbit Dog Draughts"):
            raise AssertionError("Make did not receive the accepted Invent result")
        product = {
            "schema_version": 1,
            "product_id": stage["product_id"],
            "slug": stage["product_id"],
            "title": "Orbit Dog Draughts",
            "summary": (
                "A compact, printable draughts set with orbital waypoints and two "
                "tactile dog-pack piece families."
            ),
            "description": (
                "A Wish-specific public-domain classic with unchanged play. Invented by Alice"
            ),
            "wish": wish,
            "inventor": {"id": "alice", "name": "Alice"},
            "components": sorted(_fixture_components()),
            "instructions": (
                "Set up and play English draughts normally; the orbital graphic changes "
                "the object, never the rules."
            ),
            "limitations": [
                "Digitally verified prototype; no claim of physical manufacture or delivery."
            ],
        }
        _write_json(product_root / "product.json", product)
        if self.product_contract_name_collisions:
            _write_json(product_root / "assignment.json", {"product_asset": True})
            _write_json(product_root / "invented.json", {"product_asset": True})
        (product_root / "wish.json").write_bytes((run_root / "WISH.json").read_bytes())
        (product_root / "assembled.step").write_bytes(
            b"ISO-10303-21;\nHEADER;ENDSEC;\nDATA;ENDSEC;\nEND-ISO-10303-21;\n"
        )
        (product_root / "assembled.stl").write_bytes(
            b"solid orbit_dog\nendsolid orbit_dog\n"
        )
        _write_json(
            product_root / "assembled.step.json",
            {
                "schema_version": 1,
                "step_path": "assembled.step",
                "assembly": product["title"],
            },
        )
        (product_root / "cad" / "project" / "build.py").write_text(
            "def build():\n    return 'orbit-dog-draughts'\n",
            encoding="utf-8",
        )
        (product_root / "cad" / "project" / "assembled.step.py").write_text(
            "from build import build\n",
            encoding="utf-8",
        )
        render_path = product_root / "cad" / "project" / "snap" / "iso.png"
        render_path.parent.mkdir(parents=True, exist_ok=True)
        render = Image.new("RGB", (800, 800), (244, 238, 224))
        drawing = ImageDraw.Draw(render)
        for index in range(32):
            inset = 80 + index * 6
            drawing.ellipse(
                (inset, inset, 800 - inset, 800 - inset),
                outline=(40 + index * 3, 90 + index * 2, 170 - index * 2),
                width=5,
            )
        render.save(render_path, format="PNG", optimize=False)
        signature_path = render_path.with_name("signature.png")
        signature = Image.new("RGB", (1800, 900), (244, 238, 224))
        signature_drawing = ImageDraw.Draw(signature)
        for offset, color in (
            (0, (49, 129, 176)),
            (600, (235, 160, 55)),
            (1200, (49, 129, 176)),
        ):
            signature_drawing.ellipse(
                (offset + 110, 160, offset + 490, 700), fill=color
            )
        signature.save(signature_path, format="PNG", optimize=False)
        preflight = (
            b"# Verification pipeline record\n\n"
            b"- Recorded: content-addressed\n"
            b"- Mode: `print-preflight`\n"
            b"- Result: **PASS** (exit 0)\n\n"
            b"| # | command | result | seconds |\n"
            b"|---:|---|---:|---:|\n"
            b"| 1 | `check_mesh assembled.stl` | rc=0 | 0.01 |\n"
            b"| 2 | `check_thickness assembled.stl --nozzle 0.4` | rc=0 | 0.01 |\n"
        )
        preflight_path = product_root / "cad/project/measure/print-preflight.md"
        preflight_path.parent.mkdir(parents=True, exist_ok=True)
        preflight_path.write_bytes(preflight)
        _write_json(
            signature_path.with_name("SIGNATURE-REVIEW.json"),
            {
                "schema_version": 6,
                "kind": "autonomous-workshop.signature-experience-review",
                "concept_sha256": _sha256(_canonical_json(invented["concept"])),
                "iso_sha256": _sha256(render_path.read_bytes()),
                "signature_sha256": _sha256(signature_path.read_bytes()),
                "reviewer": "independent-native-visual-critic",
                "blind_held_read": "A compact orbital play object with a strong ring.",
                "blind_form_read": "A rounded volumetric ring with a deep center.",
                "blind_subjects_read": "A ring, orbiting token, and central play field.",
                "blind_action_read": "The token moves through three distinct ring states.",
                "blind_relationship_read": "The token crosses and returns around the ring.",
                "anti_generic_signature_read": "Orbital waypoints shape the play field.",
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
                        "requirement": "The play object must be rounded and volumetric.",
                        "blind_evidence": "The exact views show a deep rounded ring.",
                        "matches": True,
                    }
                ],
                "blocking_visual_defects": [],
                "print_preflight_sha256": _sha256(preflight),
                "largest_risk": "The three play states could read as decoration.",
                "resolution": "Separated color and position make the state change explicit.",
            },
        )
        (
            product_root / "cad" / "project" / "validation" / "cad-verification.json"
        ).write_text(
            "# Verification pipeline record\n\n"
            "- Recorded: content-addressed\n"
            "- Mode: `final`\n"
            "- Result: **PASS** (exit 0)\n\n"
            "| # | command | result | seconds |\n"
            "|---:|---|---:|---:|\n"
            "| 1 | `check_thickness exact.stl` | rc=0 | 0.01 |\n",
            encoding="utf-8",
        )
        for required in inputs["required_root_files"]:
            if not (product_root / required).is_file():
                raise AssertionError("Make omitted a host-required root file")
        (product_root / "parts").mkdir(exist_ok=True)
        for group in invented["concept"]["build_plan"]:
            for key in group["parts"]:
                (product_root / "parts" / ("%s.stl" % key)).write_bytes(
                    b"solid %s\nendsolid %s\n" % (key.encode(), key.encode())
                )
            self._run_finalizer(
                run_root,
                "make-group",
                *(("--source", spark_source) if spark_source is not None else ()),
                "--product-root",
                product_root_value,
                "--group",
                group["group"],
            )
        arguments = ["make"]
        if spark_source is not None:
            arguments.extend(("--source", spark_source))
        arguments.extend(
            (
                "--product-root",
                product_root_value,
                "--cad-project-path",
                "cad/project",
                "--cad-verification-path",
                "cad/project/validation/cad-verification.json",
            )
        )
        self._run_finalizer(run_root, *arguments)

    def _author_playtest(self, run_root, stage):
        inputs = stage["inputs"]
        evidence_root_value = inputs["evidence_root"]
        evidence_root = run_root / evidence_root_value
        checks = []
        for check_id in inputs["required_check_ids"]:
            config_ref = "configs/%s.json" % check_id
            evidence_ref = "results/%s.json" % check_id
            _write_json(
                evidence_root / config_ref,
                {
                    "schema_version": 1,
                    "check_id": check_id,
                    "seed": 17,
                    "artifact_sha256": inputs["made"]["product_manifest"][
                        "artifact_sha256"
                    ],
                },
            )
            _write_json(
                evidence_root / evidence_ref,
                {
                    "schema_version": 1,
                    "check_id": check_id,
                    "passed": True,
                    "finding": "The exact sealed revision passed %s." % check_id,
                },
            )
            checks.append(
                {
                    "check_id": check_id,
                    "passed": True,
                    "evaluator": "independent-fixture-judge",
                    "evaluator_version": "1.0.0",
                    "config_ref": config_ref,
                    "evidence_ref": evidence_ref,
                    "observed_at": _OBSERVED_AT,
                    "observations": {
                        "evidence_class": "deterministic-digital-check",
                        "claims": ["The sealed revision passed %s." % check_id],
                        "artifact_bound": True,
                    },
                }
            )
        cad_rejection = inputs.get("host_cad_gate_rejection")
        if (
            isinstance(cad_rejection, dict)
            and cad_rejection.get("failure_code") == "cad-not-print-ready"
        ):
            verdict, feedback = (
                "improve",
                [
                    {
                        "code": "cad-not-print-ready",
                        "area": "make",
                        "severity": "block",
                        "finding": (
                            "The host's exact CAD replay found this revision is "
                            "digital-only and cannot support the required "
                            "ready-to-print Release."
                        ),
                        "change": (
                            "Rebuild the CAD at the full verification tier, "
                            "including wall-thickness checks."
                        ),
                        "evidence_refs": ["results/printability-check.json"],
                        "invalidates": ["playtest", "release"],
                    }
                ],
            )
        elif self.playtest_plan:
            verdict, feedback = self.playtest_plan.pop(0)
        else:
            verdict, feedback = "pass", []
        answers = [
            {
                "lead": lead["id"],
                "verdict": "dismissed",
                "why": "The fixture revision has no %s exposure." % lead["nodes"][1],
                "feedback_code": None,
            }
            for lead in inputs.get("vault_leads", [])
        ]
        if self.confirm_first_lead and answers and feedback:
            answers[0] = {
                "lead": answers[0]["lead"],
                "verdict": "confirmed",
                "why": "Observed in this revision's seeded games.",
                "feedback_code": feedback[0]["code"],
            }
        base = {1: 8, 2: 6}.get(stage["round"], 7)
        reads = [
            {
                "reader": reader,
                "scores": {
                    dimension: min(10, base + offset)
                    for dimension in inputs.get("score_dimensions", [])
                },
                "one_change": "Deepen the waypoint recesses by 0.5 mm.",
            }
            for reader, offset in (("first-time", 0), ("optimizing", 0), ("adversarial", 1))
        ]
        for check in checks:
            if check["check_id"] == "agent-playtest":
                check["observations"]["vault_leads"] = answers
                if "score_dimensions" in inputs:
                    check["observations"]["reads"] = reads
        source = "authored/playtest.json"
        _write_json(
            run_root / source,
            {"checks": checks, "feedback": feedback, "verdict": verdict},
        )
        self._run_finalizer(
            run_root,
            "playtest",
            "--source",
            source,
            "--evidence-root",
            evidence_root_value,
        )

    def _author_release(self, run_root, stage):
        inputs = stage["inputs"]
        made = inputs["made"]
        package_root_value = inputs["package_root"]
        package_root = run_root / package_root_value
        package_root.mkdir(parents=True, exist_ok=True)
        manual = _manual_pdf()
        (package_root / "MANUAL.pdf").write_bytes(manual)
        if (
            inputs["release_contract"].get("manual_design_evidence_path")
            == "MANUAL-DESIGN.json"
        ):
            _write_json(
                package_root / "MANUAL-DESIGN.json",
                _manual_design_evidence(manual, made),
            )
        if inputs["release_contract"]["native_release_schema_version"] == 3:
            _write_json(
                package_root / NATIVE_RELEASE_PLAYTEST_OMISSION_PATH,
                playtest_omission_record(),
            )
            _write_json(
                package_root / "product.json",
                {
                    "schema_version": 5,
                    "kind": "workshop.release-package",
                    "status": "manual-ready",
                    "title": made["product"]["title"],
                    "summary": made["product"]["summary"],
                    "what_arrives": list(made["product"]["components"]),
                    "limitations": list(made["product"]["limitations"]),
                    "product_artifact_sha256": made["product_manifest"][
                        "artifact_sha256"
                    ],
                    "playtest_status": "not-run",
                    "playtest_evidence_artifact_sha256": (
                        playtest_omission_sha256()
                    ),
                    "claims": direct_release_claims(),
                },
            )
            self._run_finalizer(
                run_root,
                "release",
                "--package-root",
                package_root_value,
            )
            return

        playtested = inputs["playtested"]
        if playtested.get("kind") != "autonomous-workshop.playtested":
            raise AssertionError("Release did not receive the full Playtest contract")
        binding = inputs["playtested_artifact"]
        if binding["playtested_sha256"] != playtested["playtested_sha256"]:
            raise AssertionError("Release Playtest contract and artifact binding differ")
        claims = {}
        for check in playtested["checks"]:
            observations = check["observations"]
            claims[check["check_id"]] = {
                "passed": check["passed"],
                "evidence_class": observations["evidence_class"],
                "claims": observations["claims"],
                "evidence_ref": check["evidence_ref"],
                "evidence_sha256": check["evidence_sha256"],
                "evaluator": check["evaluator"],
                "evaluator_version": check["evaluator_version"],
            }
        _write_json(
            package_root / "product.json",
            {
                "schema_version": 4,
                "kind": "workshop.release-package",
                "status": "manual-ready",
                "title": made["product"]["title"],
                "summary": made["product"]["summary"],
                "what_arrives": list(made["product"]["components"]),
                "limitations": list(made["product"]["limitations"]),
                "product_artifact_sha256": made["product_manifest"][
                    "artifact_sha256"
                ],
                "playtest_evidence_artifact_sha256": playtested[
                    "evidence_manifest"
                ]["artifact_sha256"],
                "claims": claims,
            },
        )
        self._run_finalizer(
            run_root,
            "release",
            "--package-root",
            package_root_value,
        )

    def _turn(self, arguments):
        self._assert_public_arguments(arguments)
        run_root = Path(arguments["run_root"])
        stage_path = run_root / "STAGE.json"
        if stat.S_IMODE(stage_path.stat().st_mode) & 0o222:
            raise AssertionError("native session received a writable STAGE.json")
        stage = _read_json(stage_path)
        if stage["product_id"] != arguments["product_id"]:
            raise AssertionError("STAGE product identity differs from the session")
        if stage["stage"] not in arguments["prompt"]:
            raise AssertionError("native prompt does not identify the current stage")
        self.stage_packets.append(stage)
        getattr(self, "_author_%s" % stage["stage"])(run_root, stage)
        return _SessionOutcome(arguments, stage["stage"])

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        if self.starts or self.resumes:
            if len(self.starts) != 1 or self.resumes:
                raise AssertionError("one product run may start only one native session")
        self._checkpoint(arguments)
        return self._turn(arguments)

    def resume(self, **arguments):
        self.resumes.append(dict(arguments))
        if len(self.starts) != 1:
            raise AssertionError("resume must continue the already-started session")
        checkpoint = Path(arguments["host_state_root"]) / "codex-session.json"
        if checkpoint.read_bytes() != _SESSION_CHECKPOINT:
            raise AssertionError("resume did not use the original native session checkpoint")
        return self._turn(arguments)


class _PlaytestProposalLinkRepairAgent(_OneSessionProductAgent):
    """Replace one finalized config with a link, then repair exact host feedback."""

    def __init__(self, *, rejections_before_repair=1):
        super().__init__()
        self.playtest_attempts = 0
        self.rejections_before_repair = rejections_before_repair

    def _author_playtest(self, run_root, stage):
        inputs = stage["inputs"]
        check_id = inputs["required_check_ids"][0]
        config = (
            run_root
            / inputs["evidence_root"]
            / "configs"
            / ("%s.json" % check_id)
        )
        if self.playtest_attempts > 0:
            rejection = inputs.get("host_playtest_proposal_rejection")
            if (
                not isinstance(rejection, dict)
                or rejection.get("failure_code")
                != "playtest-artifact-invalid"
                or rejection.get("rejection_number") != self.playtest_attempts
            ):
                raise AssertionError(
                    "Playtest retry did not receive exact host proposal feedback"
                )
            if config.is_symlink():
                config.unlink()
        if self.playtest_attempts < self.rejections_before_repair:
            super()._author_playtest(run_root, stage)
            linked = run_root / (
                "work/playtest/linked-config-%04d.json" % self.playtest_attempts
            )
            linked.parent.mkdir(parents=True, exist_ok=True)
            linked.write_bytes(config.read_bytes())
            config.unlink()
            config.symlink_to(linked)
        else:
            super()._author_playtest(run_root, stage)
        self.playtest_attempts += 1


class _OneUnfinishedTurnAgent(_OneSessionProductAgent):
    """Return once without a proposal, then finish through the same session."""

    def __init__(self):
        super().__init__()
        self.returned_unfinished = False
        self.received_continuation_prompt = False

    def _turn(self, arguments):
        if self.returned_unfinished:
            if not self.received_continuation_prompt:
                self.received_continuation_prompt = (
                    "previous native turn returned without agent-outcome.json"
                    in arguments["prompt"]
                )
                if not self.received_continuation_prompt:
                    raise AssertionError("unfinished continuation prompt is missing")
            return super()._turn(arguments)
        self._assert_public_arguments(arguments)
        run_root = Path(arguments["run_root"])
        stage = _read_json(run_root / "STAGE.json")
        self.stage_packets.append(stage)
        self.returned_unfinished = True
        return _SessionOutcome(arguments, stage["stage"])


class _LegacyReleaseProductAgent(_OneSessionProductAgent):
    """Finish through the Markdown Release contract frozen in an older run."""

    assert_legacy_packet = True

    def _author_release(self, run_root, stage):
        inputs = stage["inputs"]
        if self.assert_legacy_packet:
            if inputs["release_contract"] != {
                "native_release_schema_version": 1,
                "manual_path": "MANUAL.md",
                "product_schema_version": 3,
                "product_status": "page-ready",
            }:
                raise AssertionError("legacy run received today's Release contract")
            if inputs["required_package_files"] != ["MANUAL.md", "product.json"]:
                raise AssertionError("legacy run was told to author MANUAL.pdf")

        made = inputs["made"]
        playtested = inputs["playtested"]
        claims = {}
        for check in playtested["checks"]:
            observations = check["observations"]
            claims[check["check_id"]] = {
                "passed": check["passed"],
                "evidence_class": observations["evidence_class"],
                "claims": observations["claims"],
                "evidence_ref": check["evidence_ref"],
                "evidence_sha256": check["evidence_sha256"],
                "evaluator": check["evaluator"],
                "evaluator_version": check["evaluator_version"],
            }
        evidence_refs = ["made:product.json"]
        playtest_ref = "playtest:%s" % next(iter(claims))
        package_root_value = inputs["package_root"]
        package_root = run_root / package_root_value
        package_root.mkdir(parents=True, exist_ok=True)
        (package_root / "MANUAL.md").write_text(
            "# Orbit Dog Draughts\n\nSet up and play English draughts safely.\n",
            encoding="utf-8",
        )
        product = {
            "schema_version": 3,
            "kind": "workshop.release-package",
            "status": "page-ready",
            "title": made["product"]["title"],
            "summary": made["product"]["summary"],
            "hero": {
                "headline": "Orbit Dog Draughts",
                "body": "A compact orbital draughts set with tactile dog-pack pieces.",
                "visual_direction": "Show only the exact sealed board and pieces.",
                "evidence_refs": evidence_refs,
            },
            "cinematic": {
                "headline": "Two packs enter orbit",
                "body": "The familiar game becomes a small tabletop space mission.",
                "visual_direction": "Use the exact assembled model from a low angle.",
                "evidence_refs": evidence_refs,
            },
            "use_case": {
                "headline": "Set up and play",
                "body": (
                    "Place every piece on its starting waypoint, then use standard "
                    "English draughts movement and captures. The orbital artwork and "
                    "dog-pack silhouettes change the object while preserving the "
                    "familiar rules for a complete tabletop match."
                ),
                "visual_direction": "Show the exact starting arrangement.",
                "evidence_refs": evidence_refs,
            },
            "story_blocks": [
                {
                    "headline": "Digitally checked",
                    "body": (
                        "This exact sealed revision completed the Workshop's required "
                        "digital checks. The cited records bind each statement to the "
                        "tested files and disclose that no physical print, fit, or human "
                        "play session has been claimed by this package."
                    ),
                    "visual_direction": "Pair the exact model with a restrained check motif.",
                    "evidence_refs": [playtest_ref],
                }
            ],
            "what_arrives": list(made["product"]["components"]),
            "limitations": list(made["product"]["limitations"]),
            "product_artifact_sha256": made["product_manifest"]["artifact_sha256"],
            "playtest_evidence_artifact_sha256": playtested["evidence_manifest"][
                "artifact_sha256"
            ],
            "claims": claims,
        }
        product_bytes = _canonical_json(product)
        (package_root / "product.json").write_bytes(product_bytes)
        release = NativeRelease(
            schema_version=1,
            round=stage["round"],
            made_sha256=made["made_sha256"],
            playtested_sha256=playtested["playtested_sha256"],
            product_artifact_sha256=made["product_manifest"]["artifact_sha256"],
            playtest_evidence_artifact_sha256=playtested["evidence_manifest"][
                "artifact_sha256"
            ],
            package_root=package_root_value,
            package_manifest=build_artifact_manifest(
                package_root, created_at="content-addressed"
            ),
            manual_path="MANUAL.md",
            product_json_path="product.json",
            product_json_sha256=_sha256(product_bytes),
            product=product,
        )
        contract_path_value = inputs["contract_path"]
        contract_bytes = _canonical_json(release.to_dict())
        contract_path = run_root / contract_path_value
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_bytes(contract_bytes)
        outcome = AgentOutcome(
            stage="release",
            status="ready",
            artifacts=(
                AgentArtifact(
                    path=contract_path_value,
                    sha256=_sha256(contract_bytes),
                ),
            ),
            proposed_transition=stage["next_transition"],
        )
        proposal = AgentOutcomeProposal(
            checkpoint_sha256=stage["checkpoint_sha256"],
            subject_sha256=stage["subject_sha256"],
            outcome=outcome,
        )
        (run_root / "agent-outcome.json").write_bytes(
            _canonical_json(proposal.to_dict())
        )


class _ManualFirstDowngradeProductAgent(_LegacyReleaseProductAgent):
    """Try to submit the readable legacy schema from a manual-first run."""

    assert_legacy_packet = False


class _TimeoutOnceProductAgent(_OneSessionProductAgent):
    """Checkpoint one session, time out, then finish it on host continuation."""

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        if len(self.starts) != 1 or self.resumes:
            raise AssertionError("one product run may start only one native session")
        self._assert_public_arguments(arguments)
        self._checkpoint(arguments)
        raise CodexRecoverableInvocationError("fixture native turn timed out")


class _ConceptRevisionProductAgent(_OneSessionProductAgent):
    """Verify re-Invent lineage and author a changed versioned contract."""

    def __init__(self, *, playtest_plan=None):
        super().__init__(playtest_plan=playtest_plan)
        self.invent_outputs = []

    def _author_invent(self, run_root, stage):
        inputs = stage["inputs"]
        if "failing_playtested" in inputs:
            prior_invented = inputs["prior_invented"]
            failing_playtested = inputs["failing_playtested"]
            feedback = inputs["feedback"]
            if inputs["repair_round"] != 2:
                raise AssertionError("re-Invent did not retain the shared repair round")
            prior_binding = inputs["prior_invented_artifact"]
            if "invented_sha256" in prior_binding:
                if prior_binding["invented_sha256"] != prior_invented[
                    "invented_sha256"
                ]:
                    raise AssertionError(
                        "re-Invent prior Invented identity is unbound"
                    )
            elif prior_binding["sha256"] != _sha256(
                (run_root / prior_binding["path"]).read_bytes()
            ):
                raise AssertionError("re-Invent prior Invented artifact is unbound")
            playtested_binding = inputs["failing_playtested_artifact"]
            if "playtested_sha256" in playtested_binding:
                if playtested_binding["playtested_sha256"] != failing_playtested[
                    "playtested_sha256"
                ]:
                    raise AssertionError(
                        "re-Invent failing Playtested identity is unbound"
                    )
            elif playtested_binding["sha256"] != _sha256(
                (run_root / playtested_binding["path"]).read_bytes()
            ):
                raise AssertionError(
                    "re-Invent failing Playtested artifact is unbound"
                )
            if feedback != failing_playtested["feedback"]:
                raise AssertionError("re-Invent feedback differs from Playtested bytes")
            if inputs["feedback_sha256"] != _sha256(_canonical_json(feedback)):
                raise AssertionError("re-Invent feedback hash is not canonical")

        super()._author_invent(run_root, stage)
        contract_path = inputs["contract_path"]
        self.invent_outputs.append(
            (contract_path, (run_root / contract_path).read_bytes())
        )
        if len(self.invent_outputs) == 2:
            first_path, first_bytes = self.invent_outputs[0]
            if (run_root / first_path).read_bytes() != first_bytes:
                raise AssertionError("re-Invent overwrote the sealed prior contract")


class _MakeInventRevisionProductAgent(_ConceptRevisionProductAgent):
    """Return one impossible sealed concept from Make, then finish its revision."""

    def __init__(self):
        super().__init__()
        self.requested_revision = False

    def _author_make(self, run_root, stage):
        inputs = stage["inputs"]
        if not self.requested_revision:
            if inputs.get("invent_revision_allowed") is not True:
                raise AssertionError("Quest Make lacks its frozen revision capability")
            evidence_root_value = inputs["invent_revision_evidence_root"]
            evidence_root = run_root / evidence_root_value
            _write_json(
                evidence_root / "geometry-check.json",
                {
                    "schema_version": 1,
                    "check": "sealed-concept-consistency",
                    "passed": False,
                    "clearance_mm": -0.3,
                },
            )
            source = "authored/make-revision.json"
            _write_json(
                run_root / source,
                {
                    "feedback": [
                        {
                            "code": "forced-overlap",
                            "area": "keel-index-interface",
                            "severity": "block",
                            "finding": (
                                "The exact sealed dimensions force a 0.3 mm overlap."
                            ),
                            "change": (
                                "Revise the index placement or its bound dimensions."
                            ),
                            "evidence_refs": ["geometry-check.json"],
                            "invalidates": [
                                "invent",
                                "make",
                                "playtest",
                                "release",
                            ],
                        }
                    ]
                },
            )
            self._run_finalizer(
                run_root,
                "make-revision",
                "--source",
                source,
                "--evidence-root",
                evidence_root_value,
            )
            self.requested_revision = True
            return
        super()._author_make(run_root, stage)

    def _author_invent(self, run_root, stage):
        inputs = stage["inputs"]
        if "make_revision_request" in inputs:
            request = inputs["make_revision_request"]
            request_binding = inputs["make_revision_request_artifact"]
            if inputs["repair_round"] != 2:
                raise AssertionError("Make-driven re-Invent lost its shared round")
            if request_binding["sha256"] != _sha256(
                (run_root / request_binding["path"]).read_bytes()
            ):
                raise AssertionError("Make revision request artifact is unbound")
            if inputs["feedback"] != request["feedback"]:
                raise AssertionError("re-Invent feedback differs from Make request")
            if inputs["feedback_sha256"] != request["feedback_sha256"]:
                raise AssertionError("Make revision feedback hash is unbound")
        super()._author_invent(run_root, stage)


class _FactoryEffects:
    def __init__(self):
        self.secret = "fixture-host-secret"
        self.credentials_value = SimpleNamespace(
            username="alice", password=self.secret
        )
        self.credential_requests = []
        self.writer_calls = []
        self.session_calls = []
        self.publish_calls = []
        self.ledgers = []

    def credentials(self, inventor_id):
        self.credential_requests.append(inventor_id)
        return self.credentials_value

    def writer(self, ledger, inventor_id, credentials):
        self.writer_calls.append((ledger, inventor_id, credentials))
        self.ledgers.append(ledger)
        fixture = self

        def write(context, root, manifest):
            fixture.writer_calls.append((context, root, manifest))
            manual_path = (
                "MANUAL.pdf"
                if (Path(root) / "MANUAL.pdf").is_file()
                else "MANUAL.md"
            )
            if not (Path(root) / manual_path).is_file():
                raise AssertionError("Factory effect did not receive the verified manual")
            context.assert_current()
            product_root = context.made.artifact_root
            exact_print_package = {
                "assembled.step": (product_root / "assembled.step").read_bytes(),
                "assembled.stl": (product_root / "assembled.stl").read_bytes(),
                manual_path: (Path(root) / manual_path).read_bytes(),
            }
            if not exact_print_package["assembled.step"].startswith(
                b"ISO-10303-21;"
            ) or not exact_print_package["assembled.stl"].startswith(b"solid "):
                raise AssertionError("Factory effect lacked ready-to-print model bytes")
            fixture.handoff_files = exact_print_package
            product_page_sha256 = next(
                entry.sha256
                for entry in manifest.entries
                if entry.path == "product.json"
            )
            manual_sha256 = next(
                entry.sha256
                for entry in manifest.entries
                if entry.path == manual_path
            )
            details = {
                "release_sha256": manifest.artifact_sha256,
                "product_page_sha256": product_page_sha256,
                "manual_path": manual_path,
                "manual_sha256": manual_sha256,
                "page_url": _PAGE_URL,
                "cover_url": _COVER_URL,
            }
            if manual_path == "MANUAL.pdf":
                details.update(
                    {
                        "manual_url": _MANUAL_URL,
                        "manual_readback_sha256": manual_sha256,
                    }
                )
            else:
                details.update(
                    {
                        "factory_content_sha256": _sha256(
                            b"fixture-factory-content"
                        ),
                        "factory_content_mapping": FACTORY_CONTENT_MAPPING,
                    }
                )
            return Receipt(
                payload_sha256=_sha256(b"fixture-model-handoff"),
                artifact_sha256=context.made.artifact_sha256,
                adapter="factory",
                status="draft",
                observed_at=_OBSERVED_AT,
                reference="design-orbit-dog",
                details=details,
                design_id="design-orbit-dog",
                slug="orbit-dog",
                owner_id="owner-alice",
                root_id="design-orbit-dog",
                current_history_id="history-orbit-dog-1",
                published_history_id=None,
                project_url="https://cdn.autonomous.ai/projects/orbit-dog-1/",
            )

        return write

    def session(self, credentials):
        self.session_calls.append(credentials)
        return SimpleNamespace(credentials=credentials)

    def transition(self, ledger, session):
        fixture = self

        class PublicTransition:
            def publish(self, draft):
                fixture.publish_calls.append((ledger, session, draft))
                return Receipt(
                    payload_sha256=draft.payload_sha256,
                    artifact_sha256=draft.artifact_sha256,
                    adapter="factory",
                    status="public",
                    observed_at=_OBSERVED_AT,
                    reference=draft.reference,
                    details=dict(draft.details),
                    design_id=draft.design_id,
                    slug=draft.slug,
                    owner_id=draft.owner_id,
                    root_id=draft.root_id,
                    current_history_id=draft.current_history_id,
                    published_history_id=draft.current_history_id,
                    project_url=draft.project_url,
                    listing_active=True,
                    listing_price_cents=2400,
                    listing_currency="USD",
                    listing_sku="ORBIT-DOG-001",
                )

        return PublicTransition()


class NativeFullRunTest(unittest.TestCase):
    def setUp(self):
        self.gamevault = install_fake_gamevault(self, FakeGameVaultTransport(E2E_NODES))

    def test_permanent_factory_error_is_visible_and_not_an_outage_wait(self):
        launcher = _OneSessionProductAgent()

        def verify_cad(made, **arguments):
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(made.made_sha256.encode("ascii")),
                verifier_sha256=arguments["expected_verifier_sha256"],
                verifier_mode=NATIVE_CAD_VERIFIER_MODE,
                verification_tier=NATIVE_CAD_FULL_TIER,
                thickness_gate_required=True,
                print_ready_eligible=True,
            )

        def writer(unused_ledger, unused_inventor_id, unused_credentials):
            def reject(unused_context, unused_root, unused_manifest):
                raise EffectError("Factory permanently rejected this handoff")

            return reject

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            home = root / "workshop-home"
            wish = Wish.create(
                "orbit-dog-permanent-factory-error",
                "Build a pocket draughts set inspired by my orbit-loving dog.",
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=verify_cad,
            ), mock.patch(
                "workshop.workflow.native_run._factory_credentials",
                return_value=SimpleNamespace(username="alice", password="secret"),
            ), mock.patch(
                "workshop.workflow.native_run.FactoryReleaseWriter",
                side_effect=writer,
            ), self.assertRaisesRegex(
                EffectError, "permanently rejected"
            ):
                start_native_run(wish)

            paths = SimpleNamespace(
                workspace=home / "runs" / wish.product_id / "workspace",
                host_state=home / "state" / wish.product_id,
            )
            checkpoint = AgentRun.open(
                paths.workspace, host_state_root=paths.host_state
            ).snapshot()
            self.assertEqual((checkpoint.stage, checkpoint.status), ("release", "active"))
            self.assertTrue((paths.workspace / "agent-outcome.json").is_file())
            self.assertFalse((paths.host_state / "release-effect-wait.json").exists())

    def test_release_waits_for_required_factory_credentials(self):
        launcher = _OneSessionProductAgent()
        effects = _FactoryEffects()
        timing_events = []

        def verify_cad(made, **arguments):
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(made.made_sha256.encode("ascii")),
                verifier_sha256=arguments["expected_verifier_sha256"],
                verifier_mode=NATIVE_CAD_VERIFIER_MODE,
                verification_tier=NATIVE_CAD_FULL_TIER,
                thickness_gate_required=True,
                print_ready_eligible=True,
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            home = root / "workshop-home"
            wish = Wish.create(
                "orbit-dog-local-release",
                "Build a pocket draughts set inspired by my orbit-loving dog.",
                constraints={"audience": "14+", "manufacture": "not-authorized"},
                context={"source": "native-local-release-test"},
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=Path(temporary).resolve() / "repository",
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=verify_cad,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryReleaseWriter",
                side_effect=effects.writer,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession",
                side_effect=effects.session,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryPublicTransition",
                side_effect=effects.transition,
            ), mock.patch(
                "workshop.workflow.native_run.try_materialize_digital_verification",
                side_effect=OSError("optional verification storage unavailable"),
            ), mock.patch(
                "workshop.workflow.native_run.materialize_public_example_if_source_checkout",
                side_effect=RuntimeError("unexpected public example regression"),
            ):
                receipt = start_native_run(
                    wish,
                    timing_observer=timing_events.append,
                )
                paths = native_run_paths(wish.product_id)
                run = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                )
                checkpoint = run.snapshot()

            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(receipt["stage"], "release")
            self.assertEqual(receipt["native_turns"], 4)
            self.assertEqual(receipt["tokens"]["status"], "measured")
            self.assertEqual(
                receipt["tokens"]["turns"],
                {"total": 4, "measured": 4, "unmeasured": 0},
            )
            self.assertEqual(receipt["tokens"]["input_tokens"], 750)
            self.assertEqual(receipt["tokens"]["output_tokens"], 75)
            self.assertEqual(receipt["tokens"]["economics"]["status"], "measured")
            self.assertEqual(receipt["tokens"]["economics"]["input_tokens"], 750)
            self.assertEqual(receipt["tokens"]["economics"]["cached_input_tokens"], 562)
            self.assertEqual(receipt["tokens"]["economics"]["uncached_input_tokens"], 188)
            self.assertEqual(receipt["tokens"]["economics"]["output_tokens"], 75)
            self.assertEqual(receipt["tokens"]["economics"]["reasoning_output_tokens"], 37)
            self.assertEqual(
                receipt["tokens"]["stages"]["make"]["input_tokens"],
                200,
            )
            self.assertEqual(
                receipt["tokens"]["stages"]["make"]["output_tokens"],
                20,
            )
            self.assertEqual(receipt["publication"]["status"], "not-created")
            self.assertTrue(receipt["publication"]["requested"])
            self.assertIn("Factory credentials", receipt["publication"]["reason"])
            self.assertIn("Factory credentials", receipt["needs"][0])
            self.assertEqual(checkpoint.status, "waiting")
            self.assertEqual(checkpoint.stage, "release")
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 3)
            self.assertEqual(
                [packet["stage"] for packet in launcher.stage_packets],
                ["match", "invent", "make", "release"],
            )
            release_packet = launcher.stage_packets[-1]
            self.assertEqual(
                release_packet["inputs"]["release_contract"],
                {
                    "native_release_schema_version": 3,
                    "manual_path": "MANUAL.pdf",
                    "product_schema_version": 5,
                    "product_status": "manual-ready",
                    "playtest_status": "not-run",
                    "playtest_omission_path": "PLAYTEST-NOT-RUN.json",
                    "manual_design_evidence_path": "MANUAL-DESIGN.json",
                    "manual_design_evidence_schema_version": 1,
                },
            )
            self.assertEqual(
                release_packet["inputs"]["required_package_files"],
                [
                    "MANUAL.pdf",
                    "product.json",
                    "MANUAL-DESIGN.json",
                    "PLAYTEST-NOT-RUN.json",
                ],
            )
            self.assertEqual(release_packet["next_transition"], "complete")
            self.assertEqual(
                list((paths.host_state / "gates").glob("*-release.json")), []
            )
            stage_finalizers = [
                command for command in launcher.finalizer_commands if command[4] != "make-group"
            ]
            self.assertEqual(len(stage_finalizers), 4)
            self.assertEqual(
                sum(1 for command in launcher.finalizer_commands if command[4] == "make-group"), 2
            )
            self.assertEqual(effects.writer_calls, [])
            self.assertEqual(effects.publish_calls, [])
            factory_events = [
                event
                for event in timing_events
                if event.operation == "effect.factory"
            ]
            self.assertEqual(
                [event.state for event in factory_events],
                ["started", "failed"],
            )
            self.assertNotIn(
                "Factory credentials",
                repr([event.to_dict() for event in factory_events]),
            )
            self.assertTrue((paths.host_state / "release-effect-wait.json").exists())
            self.assertFalse((paths.host_state / "release-effect.json").exists())
            self.assertFalse((paths.host_state / "factory-effects.sqlite3").exists())
            self.assertNotIn("release", checkpoint.stage_artifacts)
            self.assertTrue(
                (paths.workspace / "artifacts/release/package/MANUAL.pdf").is_file()
            )

    def test_frozen_legacy_markdown_release_is_readable_but_cannot_complete(self):
        launcher = _LegacyReleaseProductAgent()
        effects = _FactoryEffects()

        def verify_cad(made, **arguments):
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(made.made_sha256.encode("ascii")),
                verifier_sha256=arguments["expected_verifier_sha256"],
                verifier_mode=NATIVE_CAD_VERIFIER_MODE,
                verification_tier=NATIVE_CAD_FULL_TIER,
                thickness_gate_required=True,
                print_ready_eligible=True,
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            repository = Path(__file__).resolve().parents[2]
            assets = _product_run_assets_without_direct_release(
                root,
                markdown_release=True,
            )
            home = root / "workshop-home"
            wish = Wish.create(
                "legacy-markdown-release",
                "Build a pocket draughts set inspired by my orbit-loving dog.",
                constraints={"audience": "14+", "manufacture": "not-authorized"},
                context={"source": "legacy-release-regression"},
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run.product_run_agent_assets",
                return_value=assets,
            ), mock.patch(
                "workshop.workflow.native_run._product_run_inventor_source_root",
                return_value=repository / "inventors",
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=verify_cad,
            ), mock.patch(
                "workshop.workflow.native_run._factory_credentials",
                side_effect=effects.credentials,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryReleaseWriter",
                side_effect=effects.writer,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession",
                side_effect=effects.session,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryPublicTransition",
                side_effect=effects.transition,
            ):
                receipt = start_native_run(wish)
                paths = native_run_paths(wish.product_id)
                checkpoint = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                ).snapshot()

            self.assertEqual(receipt["stage"], "release")
            self.assertEqual(receipt["status"], "failed")
            self.assertEqual(checkpoint.stage, "release")
            self.assertEqual(checkpoint.status, "failed")
            release_packet = launcher.stage_packets[-1]
            self.assertEqual(
                release_packet["inputs"]["required_package_files"],
                ["MANUAL.md", "product.json"],
            )
            self.assertEqual(
                release_packet["inputs"]["release_contract"][
                    "native_release_schema_version"
                ],
                1,
            )
            package = paths.workspace / "artifacts/release/package"
            self.assertTrue((package / "MANUAL.md").is_file())
            self.assertFalse((package / "MANUAL.pdf").exists())
            self.assertEqual(
                list((paths.host_state / "gates").glob("*-release.json")), []
            )
            self.assertEqual(receipt["publication"]["status"], "not-created")
            self.assertEqual(effects.writer_calls, [])
            self.assertEqual(effects.publish_calls, [])

    def test_manual_first_run_cannot_downgrade_to_the_readable_legacy_schema(self):
        launcher = _ManualFirstDowngradeProductAgent()

        def verify_cad(made, **arguments):
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(made.made_sha256.encode("ascii")),
                verifier_sha256=arguments["expected_verifier_sha256"],
                verifier_mode=NATIVE_CAD_VERIFIER_MODE,
                verification_tier=NATIVE_CAD_FULL_TIER,
                thickness_gate_required=True,
                print_ready_eligible=True,
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            home = root / "workshop-home"
            assets = _product_run_assets_without_direct_release(root)
            wish = Wish.create(
                "manual-first-no-downgrade",
                "Build a pocket draughts set inspired by my orbit-loving dog.",
                constraints={"audience": "14+", "manufacture": "not-authorized"},
                context={"source": "release-downgrade-regression"},
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run.product_run_agent_assets",
                return_value=assets,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=verify_cad,
            ), self.assertRaisesRegex(
                StateConflict, "materialized Release protocol"
            ):
                start_native_run(wish)

            release_packet = launcher.stage_packets[-1]
            self.assertEqual(
                release_packet["inputs"]["release_contract"][
                    "native_release_schema_version"
                ],
                2,
            )
            self.assertEqual(
                release_packet["inputs"]["required_package_files"],
                ["MANUAL.pdf", "product.json", "MANUAL-DESIGN.json"],
            )

    def _run_playtest_routing_case(
        self,
        *,
        playtest_plan,
        wish_name,
        context_source,
        launcher=None,
        effort=None,
    ):
        if launcher is None:
            launcher = _OneSessionProductAgent(playtest_plan=playtest_plan)
        else:
            launcher.playtest_plan = list(playtest_plan)
        effects = _FactoryEffects()

        def verify_cad(made, **arguments):
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(made.made_sha256.encode("ascii")),
                verifier_sha256=arguments["expected_verifier_sha256"],
                verifier_mode=NATIVE_CAD_VERIFIER_MODE,
                verification_tier=NATIVE_CAD_FULL_TIER,
                thickness_gate_required=True,
                print_ready_eligible=True,
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            home = root / "workshop-home"
            assets = (
                _product_run_assets_without_direct_release(root)
                if effort is None
                else None
            )
            wish = Wish.create(
                wish_name,
                "Build a pocket draughts set inspired by my orbit-loving dog.",
                constraints={"audience": "14+", "manufacture": "not-authorized"},
                context={"source": context_source},
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=verify_cad,
            ), mock.patch(
                "workshop.workflow.native_run._factory_credentials",
                side_effect=effects.credentials,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryReleaseWriter",
                side_effect=effects.writer,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession",
                side_effect=effects.session,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryPublicTransition",
                side_effect=effects.transition,
            ):
                asset_patch = (
                    mock.patch(
                        "workshop.workflow.native_run.product_run_agent_assets",
                        return_value=assets,
                    )
                    if assets is not None
                    else mock.patch(
                        "workshop.workflow.native_run._source_checkout_root",
                        return_value=None,
                    )
                )
                with asset_patch:
                    receipt = start_native_run(wish, effort=effort)
                paths = native_run_paths(wish.product_id)
                run = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                )
                checkpoint = run.snapshot()

        self.assertEqual(receipt["status"], "complete")
        self.assertEqual(receipt["stage"], "release")
        return launcher, checkpoint

    def test_quest_playtest_repair_returns_to_make_without_match(self):
        launcher, checkpoint = self._run_playtest_routing_case(
            effort="quest",
            playtest_plan=[
                (
                    "improve",
                    [
                        {
                            "code": "piece-clearance",
                            "area": "make",
                            "severity": "block",
                            "finding": "The piece clearance needs a build-only repair.",
                            "change": "Increase the printable clearance and rebuild.",
                            "evidence_refs": ["results/mechanical-check.json"],
                            "invalidates": ["playtest", "release"],
                        }
                    ],
                )
            ],
            wish_name="quest-build-repair",
            context_source="quest-build-repair-test",
        )

        self.assertEqual(checkpoint.effort, "quest")
        self.assertEqual(checkpoint.round_index, 2)
        self.assertEqual(
            [packet["stage"] for packet in launcher.stage_packets],
            ["invent", "make", "playtest", "make", "playtest", "release"],
        )
        self.assertNotIn("match", checkpoint.stage_artifacts)

    def test_quest_playtest_linked_config_is_quarantined_and_repaired(self):
        launcher = _PlaytestProposalLinkRepairAgent()

        launcher, unused_checkpoint = self._run_playtest_routing_case(
            playtest_plan=[],
            wish_name="quest-playtest-linked-config-repair",
            context_source="playtest-linked-config-recovery-regression",
            launcher=launcher,
            effort="quest",
        )

        playtest_packets = [
            packet
            for packet in launcher.stage_packets
            if packet["stage"] == "playtest"
        ]
        self.assertEqual(len(playtest_packets), 2)
        self.assertNotIn(
            "host_playtest_proposal_rejection",
            playtest_packets[0]["inputs"],
        )
        rejection = playtest_packets[1]["inputs"][
            "host_playtest_proposal_rejection"
        ]
        self.assertEqual(rejection["failure_code"], "playtest-artifact-invalid")
        self.assertEqual(rejection["rejection_number"], 1)

    def test_quest_playtest_rejection_history_is_hash_chained(self):
        launcher = _PlaytestProposalLinkRepairAgent(rejections_before_repair=2)

        launcher, unused_checkpoint = self._run_playtest_routing_case(
            playtest_plan=[],
            wish_name="quest-playtest-rejection-chain",
            context_source="playtest-rejection-chain-regression",
            launcher=launcher,
            effort="quest",
        )

        playtest_packets = [
            packet
            for packet in launcher.stage_packets
            if packet["stage"] == "playtest"
        ]
        self.assertEqual(len(playtest_packets), 3)
        first = playtest_packets[1]["inputs"][
            "host_playtest_proposal_rejection"
        ]
        second = playtest_packets[2]["inputs"][
            "host_playtest_proposal_rejection"
        ]
        self.assertEqual(first["rejection_number"], 1)
        self.assertIsNone(first["previous_rejection_sha256"])
        self.assertEqual(second["rejection_number"], 2)
        self.assertEqual(
            second["previous_rejection_sha256"], first["rejection_sha256"]
        )

    def test_unfinished_native_turn_continues_same_goal_automatically(self):
        launcher = _OneUnfinishedTurnAgent()

        launcher, checkpoint = self._run_playtest_routing_case(
            playtest_plan=[],
            wish_name="spark-unfinished-native-turn",
            context_source="unfinished-native-turn-regression",
            launcher=launcher,
            effort="spark",
        )

        self.assertEqual(checkpoint.effort, "spark")
        self.assertEqual(
            [packet["stage"] for packet in launcher.stage_packets],
            ["make", "make", "release"],
        )
        self.assertEqual(len(launcher.starts), 1)
        self.assertGreaterEqual(len(launcher.resumes), 2)
        self.assertTrue(launcher.received_continuation_prompt)

    def test_spark_release_uses_exact_creative_contract_paths(self):
        launcher = _OneSessionProductAgent(product_contract_name_collisions=True)
        launcher, checkpoint = self._run_playtest_routing_case(
            effort="spark",
            launcher=launcher,
            playtest_plan=[],
            wish_name="spark-contract-name-collisions",
            context_source="spark-contract-name-collisions-test",
        )

        self.assertTrue(checkpoint.complete)
        self.assertEqual(
            [packet["stage"] for packet in launcher.stage_packets],
            ["make", "release"],
        )
        make_paths = {artifact.path for artifact in checkpoint.stage_artifacts["make"]}
        self.assertIn("artifacts/make/r0001/assignment.json", make_paths)
        self.assertIn("artifacts/make/r0001/invented.json", make_paths)
        self.assertIn(
            "artifacts/make/r0001/product/assignment.json", make_paths
        )
        self.assertIn("artifacts/make/r0001/product/invented.json", make_paths)

    def test_quest_concept_revision_reinvents_without_match(self):
        launcher = _ConceptRevisionProductAgent()
        launcher, checkpoint = self._run_playtest_routing_case(
            effort="quest",
            playtest_plan=[
                (
                    "block",
                    [
                        {
                            "code": "waypoint-misalignment",
                            "area": "make",
                            "severity": "block",
                            "finding": (
                                "The orbital waypoints do not align with the "
                                "draughts grid, so legal jumps are ambiguous."
                            ),
                            "change": (
                                "Revise the concept so its orbital interaction maps "
                                "unambiguously to every legal playable square."
                            ),
                            "evidence_refs": ["results/mechanical-check.json"],
                            "invalidates": [
                                "invent",
                                "make",
                                "playtest",
                                "release",
                            ],
                        }
                    ],
                )
            ],
            wish_name="quest-orbit-dog-design-revision",
            context_source="quest-playtest-design-revision-test",
            launcher=launcher,
        )

        self.assertEqual(checkpoint.effort, "quest")
        self.assertEqual(checkpoint.round_index, 2)
        self.assertEqual(
            (checkpoint.stage, checkpoint.status), ("release", "complete")
        )
        self.assertEqual(
            [packet["stage"] for packet in launcher.stage_packets],
            [
                "invent",
                "make",
                "playtest",
                "invent",
                "make",
                "playtest",
                "release",
            ],
        )
        self.assertNotIn("match", checkpoint.stage_artifacts)
        first_invent_packet = launcher.stage_packets[0]
        reinvent_packet = launcher.stage_packets[3]
        self.assertEqual(
            first_invent_packet["inputs"]["assignment_contract_path"],
            "artifacts/invent/assignment.json",
        )
        self.assertEqual(
            reinvent_packet["inputs"]["assignment_contract_path"],
            "artifacts/invent/r0002/assignment.json",
        )
        self.assertEqual(
            reinvent_packet["inputs"]["contract_path"],
            "artifacts/invent/r0002/invented.json",
        )
        self.assertEqual(
            reinvent_packet["inputs"]["prior_invented_artifact"]["path"],
            "artifacts/invent/invented.json",
        )
        self.assertEqual(
            reinvent_packet["inputs"]["failing_playtested_artifact"]["path"],
            "artifacts/playtest/r0001/playtested.json",
        )
        self.assertEqual(
            [path for path, unused_bytes in launcher.invent_outputs],
            [
                "artifacts/invent/invented.json",
                "artifacts/invent/r0002/invented.json",
            ],
        )
        self.assertNotEqual(
            launcher.invent_outputs[0][1], launcher.invent_outputs[1][1]
        )

    def test_quest_make_can_return_unbuildable_concept_to_invent(self):
        launcher = _MakeInventRevisionProductAgent()
        launcher, checkpoint = self._run_playtest_routing_case(
            effort="quest",
            playtest_plan=[],
            wish_name="quest-make-invent-revision",
            context_source="quest-make-invent-revision-test",
            launcher=launcher,
        )

        self.assertTrue(checkpoint.complete)
        self.assertEqual(checkpoint.round_index, 2)
        self.assertEqual(
            [packet["stage"] for packet in launcher.stage_packets],
            ["invent", "make", "invent", "make", "playtest", "release"],
        )
        first_make = launcher.stage_packets[1]
        reinvent = launcher.stage_packets[2]
        self.assertTrue(first_make["inputs"]["invent_revision_allowed"])
        self.assertEqual(
            first_make["inputs"]["invent_revision_contract_path"],
            "artifacts/make/r0001/invent-revision-request.json",
        )
        self.assertEqual(
            reinvent["inputs"]["make_revision_request_artifact"]["path"],
            "artifacts/make/r0001/invent-revision-request.json",
        )
        self.assertEqual(
            reinvent["inputs"]["contract_path"],
            "artifacts/invent/r0002/invented.json",
        )
        self.assertEqual(
            [command[4] for command in launcher.finalizer_commands],
            # the revised concept's two build groups are sealed before Make itself
            ["invent", "make-revision", "invent", "make-group", "make-group", "make", "playtest", "release"],
        )
        self.assertEqual(
            [path for path, unused_bytes in launcher.invent_outputs],
            [
                "artifacts/invent/invented.json",
                "artifacts/invent/r0002/invented.json",
            ],
        )
        self.assertNotEqual(
            launcher.invent_outputs[0][1], launcher.invent_outputs[1][1]
        )

    def test_timeout_continues_same_session_through_the_full_run(self):
        with mock.patch("workshop.workflow.native_run.time.sleep") as backoff:
            launcher, checkpoint = self._run_playtest_routing_case(
                playtest_plan=[],
                wish_name="orbit-dog-timeout-continuation",
                context_source="native-timeout-continuation-test",
                launcher=_TimeoutOnceProductAgent(),
            )

        self.assertEqual(checkpoint.stage, "release")
        self.assertEqual(checkpoint.status, "complete")
        self.assertEqual(len(launcher.starts), 1)
        self.assertEqual(len(launcher.resumes), 5)
        recovery_delays = [
            call.args[0]
            for call in backoff.call_args_list
            if call.args and call.args[0] >= 0.75
        ]
        self.assertEqual(len(recovery_delays), 1)
        self.assertGreaterEqual(recovery_delays[0], 0.75)
        self.assertLessEqual(recovery_delays[0], 30)
        self.assertEqual(
            [packet["stage"] for packet in launcher.stage_packets],
            ["match", "invent", "make", "playtest", "release"],
        )

    def test_concept_invalidating_playtest_routes_to_bound_reinvent_checkpoint(self):
        launcher = _ConceptRevisionProductAgent()
        launcher, checkpoint = self._run_playtest_routing_case(
            playtest_plan=[
                (
                    "block",
                    [
                        {
                            "code": "waypoint-misalignment",
                            "area": "make",
                            "severity": "block",
                            "finding": (
                                "The orbital waypoints do not align with the "
                                "draughts grid, so legal jumps are ambiguous."
                            ),
                            "change": (
                                "Revise the concept so its orbital interaction maps "
                                "unambiguously to every legal playable square."
                            ),
                            "evidence_refs": ["results/mechanical-check.json"],
                            "invalidates": [
                                "invent",
                                "make",
                                "playtest",
                                "release",
                            ],
                        }
                    ],
                )
            ],
            wish_name="orbit-dog-design-revision",
            context_source="native-playtest-design-revision-test",
            launcher=launcher,
        )

        self.assertEqual(checkpoint.round_index, 2)
        self.assertEqual((checkpoint.stage, checkpoint.status), ("release", "complete"))
        self.assertEqual(
            [packet["stage"] for packet in launcher.stage_packets],
            [
                "match",
                "invent",
                "make",
                "playtest",
                "invent",
                "make",
                "playtest",
                "release",
            ],
        )
        first_invent_packet = launcher.stage_packets[1]
        reinvent_packet = launcher.stage_packets[4]
        # The repair round is written against the very leads Make refused on.
        self.assertEqual(
            reinvent_packet["inputs"]["vault_leads"],
            launcher.stage_packets[2]["inputs"]["vault_leads"],
        )
        self.assertTrue(reinvent_packet["inputs"]["vault_leads"])
        self.assertIsNone(first_invent_packet["round"])
        self.assertIsNone(reinvent_packet["round"])
        self.assertNotEqual(
            first_invent_packet["checkpoint_sha256"],
            reinvent_packet["checkpoint_sha256"],
        )
        self.assertEqual(
            reinvent_packet["inputs"]["failing_playtested_artifact"]["path"],
            "artifacts/playtest/r0001/playtested.json",
        )
        self.assertEqual(
            reinvent_packet["inputs"]["prior_invented_artifact"]["path"],
            "artifacts/invent/invented.json",
        )
        self.assertEqual(
            reinvent_packet["inputs"]["contract_path"],
            "artifacts/invent/r0002/invented.json",
        )
        self.assertEqual(
            [path for path, unused_bytes in launcher.invent_outputs],
            [
                "artifacts/invent/invented.json",
                "artifacts/invent/r0002/invented.json",
            ],
        )
        self.assertNotEqual(
            launcher.invent_outputs[0][1], launcher.invent_outputs[1][1]
        )
        self.assertEqual(
            checkpoint.stage_artifacts["invent"][0].path,
            "artifacts/invent/r0002/invented.json",
        )

    def test_build_only_playtest_verdict_routes_back_to_make(self):
        launcher, checkpoint = self._run_playtest_routing_case(
            playtest_plan=[
                (
                    "improve",
                    [
                        {
                            "code": "fit-tolerance",
                            "area": "make",
                            "severity": "improve",
                            "finding": (
                                "The piece pegs are slightly loose in the "
                                "waypoint recesses."
                            ),
                            "change": (
                                "Tighten the peg-to-recess clearance in the "
                                "next Make revision."
                            ),
                            "evidence_refs": ["results/printability-check.json"],
                            "invalidates": ["playtest", "release"],
                        }
                    ],
                )
            ],
            wish_name="orbit-dog-make-revision",
            context_source="native-playtest-make-revision-test",
        )

        self.assertEqual(checkpoint.round_index, 2)
        self.assertEqual(
            [packet["stage"] for packet in launcher.stage_packets],
            [
                "match",
                "invent",
                "make",
                "playtest",
                "make",
                "playtest",
                "release",
            ],
        )
        make_artifacts = checkpoint.stage_artifacts["make"]
        self.assertTrue(any("r0002" in artifact.path for artifact in make_artifacts))

    def test_four_round_design_repairs_stay_under_the_turn_ceiling(self):
        # Exhaust every repair round (max_rounds=4) with design-invalidating
        # feedback except the last, which must pass before Playtest can advance.
        design_invalidating_feedback = [
            {
                "code": "waypoint-misalignment",
                "area": "make",
                "severity": "block",
                "finding": (
                    "The orbital waypoints do not align with the draughts "
                    "grid, so legal jumps are ambiguous."
                ),
                "change": (
                    "Revise the design and geometry in Make so every waypoint "
                    "is centered on a playable square."
                ),
                "evidence_refs": ["results/mechanical-check.json"],
                "invalidates": ["playtest", "release"],
            }
        ]
        launcher, checkpoint = self._run_playtest_routing_case(
            playtest_plan=[
                ("block", design_invalidating_feedback),
                ("block", design_invalidating_feedback),
                ("block", design_invalidating_feedback),
            ],
            wish_name="orbit-dog-worst-case-rounds",
            context_source="native-turn-ceiling-worst-case-test",
        )

        self.assertEqual(checkpoint.round_index, 4)
        self.assertEqual(checkpoint.max_rounds, 4)
        total_turns = len(launcher.starts) + len(launcher.resumes)
        self.assertEqual(len(launcher.stage_packets), total_turns)
        # Match + Invent, then four Make/Playtest rounds, then Release.
        self.assertEqual(total_turns, 2 + 4 * 2 + 1)
        self.assertLess(total_turns, _MAX_NATIVE_TURNS)
        self.assertEqual(
            [packet["stage"] for packet in launcher.stage_packets],
            [
                "match",
                "invent",
                "make",
                "playtest",
                "make",
                "playtest",
                "make",
                "playtest",
                "make",
                "playtest",
                "release",
            ],
        )
        make_packets = [
            packet
            for packet in launcher.stage_packets
            if packet["stage"] == "make"
        ]
        self.assertEqual([packet["round"] for packet in make_packets], [1, 2, 3, 4])
        self.assertEqual(
            [len(packet["inputs"]["score_history"]) for packet in make_packets],
            [0, 1, 2, 3],
        )
        self.assertEqual(make_packets[1]["inputs"]["regression"], {})
        # round 2 scored 6 against round 1's 8: the next Make is told so
        self.assertEqual(
            make_packets[2]["inputs"]["regression"],
            {"wish_fit": -2, "play": -2, "legibility": -2, "build_confidence": -2},
        )
        self.assertEqual(
            [entry["verdict"] for entry in make_packets[3]["inputs"]["score_history"]],
            ["block", "block", "block"],
        )

    def test_confirmed_leads_and_dismissals_reach_the_game_vault(self):
        finding = {
            "code": "idle-seat",
            "area": "play",
            "severity": "block",
            "finding": "One seat idles while the other resolves captures.",
            "change": "Resolve captures simultaneously.",
            "evidence_refs": ["results/agent-playtest.json"],
            "invalidates": ["playtest", "release"],
        }
        effects = _FactoryEffects()

        def verify_cad(made, **arguments):
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(made.made_sha256.encode("ascii")),
                verifier_sha256=arguments["expected_verifier_sha256"],
                verifier_mode=NATIVE_CAD_VERIFIER_MODE,
                verification_tier=NATIVE_CAD_FULL_TIER,
                thickness_gate_required=True,
                print_ready_eligible=True,
            )

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            home.mkdir()
            first = _OneSessionProductAgent(playtest_plan=[("block", [finding])], confirm_first_lead=True)
            second = _OneSessionProductAgent()
            active_launcher = {"agent": first}
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root", return_value=None
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                side_effect=lambda *a, **k: active_launcher["agent"],
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad", side_effect=verify_cad
            ), mock.patch(
                "workshop.workflow.native_run._factory_credentials", side_effect=effects.credentials
            ), mock.patch(
                "workshop.workflow.native_run.FactoryReleaseWriter", side_effect=effects.writer
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession", side_effect=effects.session
            ), mock.patch(
                "workshop.workflow.native_run.FactoryPublicTransition", side_effect=effects.transition
            ):
                wish_a = Wish.create(
                    "orbit-dog-a",
                    "Build a pocket draughts set inspired by my orbit-loving dog.",
                    constraints={"audience": "14+"},
                    context={"source": "native-ledger-test"},
                )
                receipt_a = start_native_run(wish_a, effort="quest")
                active_launcher["agent"] = second
                wish_b = Wish.create(
                    "orbit-dog-b",
                    "Build a pocket draughts set for my other dog.",
                    constraints={"audience": "14+"},
                    context={"source": "native-ledger-test"},
                )
                receipt_b = start_native_run(wish_b, effort="quest")

                self.assertEqual((receipt_a["stage"], receipt_b["stage"]), ("release", "release"))
                self.assertEqual((receipt_a["status"], receipt_b["status"]), ("complete", "complete"))
                first_leads = [p for p in first.stage_packets if p["stage"] == "playtest"][0]["inputs"]["vault_leads"]
                confirmed_symptom = first_leads[0]["nodes"][1]
                posted = [item for item in self.gamevault.evidence if item["label"] == "workshop orbit-dog-a r1"]
                self.assertEqual(len(posted), 1)
                self.assertEqual([row["id"] for row in posted[0]["rows"]], ["r0001-idle-seat"])
                self.assertEqual(posted[0]["rows"][0]["symptom"], confirmed_symptom)
                self.assertEqual(posted[0]["rows"][0]["severity"], "high")
                reviewed = [item for item in self.gamevault.review if item["label"] == "workshop orbit-dog-a r1"]
                self.assertEqual(len(reviewed), 1)
                self.assertEqual(
                    sorted(item["symptom"] for item in reviewed[0]["dismissals"]),
                    sorted(lead["nodes"][1] for lead in first_leads[1:]),
                )
                self.assertFalse((home / "state" / "orbit-dog-a" / "vault" / "pending").exists())
                # every phase that needs design knowledge fetched it live
                exports = [call for call in self.gamevault.calls if call[1].endswith("/api/gamevault/export")]
                self.assertGreaterEqual(len(exports), 6)
                second_make = [p for p in second.stage_packets if p["stage"] == "make"][0]
                self.assertTrue(second_make["inputs"]["vault_leads"])
                self.assertEqual(receipt_a["rounds"][0]["vault_leads_confirmed"], 1)

    def test_full_run_completes_and_queues_write_backs_when_the_vault_is_down(self):
        """A dead game vault never blocks a run.

        The real HTTP client is pointed at a closed local port: every phase
        records an ``unavailable`` marker and proceeds without design
        knowledge, and the sealed Playtest write-backs wait in the host's
        pending queue instead of failing the round.
        """
        finding = {
            "code": "idle-seat",
            "area": "play",
            "severity": "block",
            "finding": "One seat idles while the other resolves captures.",
            "change": "Resolve captures simultaneously.",
            "evidence_refs": ["results/agent-playtest.json"],
            "invalidates": ["playtest", "release"],
        }
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            closed_port = probe.getsockname()[1]
        dead_vault = GameVaultClient(
            GameVaultConfig("http://127.0.0.1:%d" % closed_port, "fixture-token")
        )
        effects = _FactoryEffects()
        launcher = _OneSessionProductAgent(playtest_plan=[("block", [finding])])

        def verify_cad(made, **arguments):
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(made.made_sha256.encode("ascii")),
                verifier_sha256=arguments["expected_verifier_sha256"],
                verifier_mode=NATIVE_CAD_VERIFIER_MODE,
                verification_tier=NATIVE_CAD_FULL_TIER,
                thickness_gate_required=True,
                print_ready_eligible=True,
            )

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            home.mkdir()
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root", return_value=None
            ), mock.patch(
                "workshop.workflow.native_run._gamevault_client", return_value=dead_vault
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad", side_effect=verify_cad
            ), mock.patch(
                "workshop.workflow.native_run._factory_credentials", side_effect=effects.credentials
            ), mock.patch(
                "workshop.workflow.native_run.FactoryReleaseWriter", side_effect=effects.writer
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession", side_effect=effects.session
            ), mock.patch(
                "workshop.workflow.native_run.FactoryPublicTransition", side_effect=effects.transition
            ):
                wish = Wish.create(
                    "orbit-dog-offline",
                    "Build a pocket draughts set inspired by my orbit-loving dog.",
                    constraints={"audience": "14+"},
                    context={"source": "native-vault-down-test"},
                )
                receipt = start_native_run(wish, effort="quest")
                paths = native_run_paths(wish.product_id)

                self.assertEqual((receipt["stage"], receipt["status"]), ("release", "complete"))
                self.assertEqual(receipt["publication"]["status"], "public")
                self.assertEqual(len(receipt["rounds"]), 2)
                # no phase ever received design knowledge, and none paused for it
                self.assertFalse((paths.workspace / RUN_VAULT_PATH).exists())
                for packet in launcher.stage_packets:
                    self.assertNotIn("design_vault", packet["inputs"], packet["stage"])
                    self.assertFalse(packet["inputs"].get("vault_leads"), packet["stage"])
                self.assertEqual(
                    [packet["stage"] for packet in launcher.stage_packets],
                    ["invent", "make", "playtest", "make", "playtest", "release"],
                )
                vault_state = paths.host_state / "vault"
                self.assertGreaterEqual(len(list(vault_state.glob("*.unavailable"))), 1)
                self.assertEqual(list(vault_state.glob("*.json")), [])
                # sealed Playtest findings wait for the vault instead of failing the round
                pending = sorted((vault_state / "pending").glob("*.json"))
                self.assertGreaterEqual(len(pending), 1)
                # an unreachable vault is not a refusal: nothing is set aside as rejected
                self.assertEqual(list((vault_state / "pending").glob("*.rejected")), [])
                queued = [json.loads(path.read_text(encoding="utf-8")) for path in pending]
                self.assertEqual(
                    {payload["label"] for payload in queued} & {"workshop orbit-dog-offline r1"},
                    {"workshop orbit-dog-offline r1"},
                )
                for payload in queued:
                    self.assertEqual(set(payload), {"label", "rows", "dismissals", "design"})
                    self.assertEqual(payload["dismissals"], [])
                self.assertEqual(self.gamevault.calls, [])

    def test_a_worse_round_redirects_the_next_make_to_the_best_sealed_round(self):
        one = {
            "code": "waypoint-misalignment",
            "area": "make",
            "severity": "block",
            "finding": "Waypoints miss the grid.",
            "change": "Center every waypoint on a playable square.",
            "evidence_refs": ["results/mechanical-check.json"],
            "invalidates": ["playtest", "release"],
        }
        two = {**one, "code": "piece-wobble", "finding": "Pieces wobble in the recess.",
               "change": "Deepen the recess by 0.5 mm."}
        launcher, checkpoint = self._run_playtest_routing_case(
            playtest_plan=[("block", [one]), ("block", [one, two])],
            wish_name="orbit-dog-worse-round",
            context_source="native-repair-base-test",
        )
        self.assertEqual(checkpoint.round_index, 3)
        make_packets = [p for p in launcher.stage_packets if p["stage"] == "make"]
        self.assertEqual([p["round"] for p in make_packets], [1, 2, 3])
        self.assertIsNone(make_packets[0]["inputs"]["repair_base"])
        self.assertIsNone(make_packets[1]["inputs"]["repair_base"])
        base = make_packets[2]["inputs"]["repair_base"]
        self.assertEqual(base["round"], 1)
        self.assertEqual(base["product_root"], "artifacts/make/r0001/product")
        self.assertEqual(
            [entry["machine_failures"] for entry in make_packets[2]["inputs"]["score_history"]],
            [1, 2],
        )
        playtest_packets = [p for p in launcher.stage_packets if p["stage"] == "playtest"]
        self.assertEqual(base["made_sha256"], playtest_packets[0]["inputs"]["made"]["made_sha256"])
        self.assertNotEqual(base["made_sha256"], playtest_packets[1]["inputs"]["made"]["made_sha256"])
        self.assertEqual(base["made_artifact"]["path"], "artifacts/make/r0001/made.json")

    def test_cad_gate_rejections_resume_with_hash_bound_same_stage_feedback(self):
        launcher = _OneSessionProductAgent()
        effects = _FactoryEffects()
        cad_calls = []

        def verify_cad(made, **arguments):
            cad_calls.append((made, dict(arguments)))
            if len(cad_calls) == 1:
                raise _failed_cad_gate(
                    made,
                    arguments,
                    failure_code="verifier-output-limit",
                    timed_out=False,
                    stdout_content=("🧸\"\\\n" * 20_000).encode("utf-8"),
                    stderr_content=b"\xff" * 70_000,
                )
            if len(cad_calls) == 2:
                raise _failed_cad_gate(
                    made,
                    arguments,
                    failure_code="verifier-nonzero",
                    timed_out=False,
                )
            if len(cad_calls) == 4:
                raise _failed_cad_gate(
                    made,
                    arguments,
                    failure_code="verifier-timeout",
                    timed_out=True,
                )
            if len(cad_calls) == 6:
                raise _failed_cad_gate(
                    made,
                    arguments,
                    failure_code="verifier-timeout",
                    timed_out=True,
                )
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(
                    (made.made_sha256 + str(len(cad_calls))).encode("ascii")
                ),
                verifier_sha256=arguments["expected_verifier_sha256"],
                verifier_mode=NATIVE_CAD_VERIFIER_MODE,
                verification_tier=NATIVE_CAD_FULL_TIER,
                thickness_gate_required=True,
                print_ready_eligible=True,
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            home = root / "workshop-home"
            assets = _product_run_assets_without_direct_release(root)
            wish = Wish.create(
                "orbit-dog-cad-retry",
                "Build a pocket draughts set inspired by my orbit-loving dog.",
                constraints={"audience": "14+", "manufacture": "not-authorized"},
                context={"source": "native-cad-retry-test"},
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run.product_run_agent_assets",
                return_value=assets,
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=verify_cad,
            ), mock.patch(
                "workshop.workflow.native_run._factory_credentials",
                side_effect=effects.credentials,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryReleaseWriter",
                side_effect=effects.writer,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession",
                side_effect=effects.session,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryPublicTransition",
                side_effect=effects.transition,
            ):
                receipt = start_native_run(wish)
                paths = native_run_paths(wish.product_id)
                checkpoint = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                ).snapshot()

            self.assertEqual(receipt["status"], "complete")
            self.assertEqual(receipt["stage"], "release")
            self.assertEqual(receipt["native_turns"], 9)
            self.assertEqual(checkpoint.stage, "release")
            self.assertEqual(checkpoint.status, "complete")
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 8)
            self.assertEqual(
                [packet["stage"] for packet in launcher.stage_packets],
                [
                    "match",
                    "invent",
                    "make",
                    "make",
                    "make",
                    "playtest",
                    "playtest",
                    "release",
                    "release",
                ],
            )
            self.assertEqual(len(cad_calls), 7)
            self.assertFalse((paths.workspace / "agent-outcome.json").exists())

            make_initial, make_retry, make_second_retry = (
                launcher.stage_packets[2:5]
            )
            playtest_initial, playtest_retry = launcher.stage_packets[5:7]
            release_initial, release_retry = launcher.stage_packets[7:9]
            rejection_pairs = (
                (
                    make_initial,
                    make_retry,
                    "verifier-output-limit",
                    False,
                ),
                (
                    make_retry,
                    make_second_retry,
                    "verifier-nonzero",
                    False,
                ),
                (
                    playtest_initial,
                    playtest_retry,
                    "verifier-timeout",
                    True,
                ),
                (
                    release_initial,
                    release_retry,
                    "verifier-timeout",
                    True,
                ),
            )
            for initial, retry, failure_code, timed_out in rejection_pairs:
                self.assertEqual(
                    initial["checkpoint_sha256"], retry["checkpoint_sha256"]
                )
                self.assertNotEqual(
                    initial["subject_sha256"], retry["subject_sha256"]
                )
                rejection = retry["inputs"]["host_cad_gate_rejection"]
                self.assertEqual(rejection["failure_code"], failure_code)
                self.assertEqual(rejection["timed_out"], timed_out)
                self.assertEqual(
                    rejection["checkpoint_sha256"],
                    initial["checkpoint_sha256"],
                )
                self.assertEqual(
                    rejection["subject_sha256"], initial["subject_sha256"]
                )
                self.assertEqual(
                    rejection["rejection_sha256"],
                    _sha256(
                        _canonical_json(
                            {
                                key: value
                                for key, value in rejection.items()
                                if key != "rejection_sha256"
                            }
                        )
                    ),
                )
                self.assertLess(
                    len(_canonical_json(rejection)), 64 * 1024
                )

            self.assertIsNone(
                make_initial["inputs"]["host_cad_gate_rejection"]
            )
            self.assertIsNone(
                playtest_initial["inputs"]["host_cad_gate_rejection"]
            )
            bounded_rejection = make_retry["inputs"][
                "host_cad_gate_rejection"
            ]
            for stream_name in ("stdout", "stderr"):
                self.assertLessEqual(
                    len(
                        _canonical_json(
                            bounded_rejection[stream_name]["captured_text_tail"]
                        )
                    ),
                    8 * 1024,
                )
                self.assertTrue(bounded_rejection[stream_name]["truncated"])
            self.assertIn(
                "\ufffd", bounded_rejection["stderr"]["captured_text_tail"]
            )
            self.assertIn(
                "verifier-nonzero",
                make_second_retry["inputs"]["host_cad_gate_rejection"][
                    "stderr"
                ]["captured_text_tail"],
            )
            self.assertIn(
                "verifier-timeout",
                playtest_retry["inputs"]["host_cad_gate_rejection"]["stderr"][
                    "captured_text_tail"
                ],
            )
            self.assertIn(
                "verifier-timeout",
                release_retry["inputs"]["host_cad_gate_rejection"]["stderr"][
                    "captured_text_tail"
                ],
            )

            rejection_root = paths.host_state / "cad-gate-rejections"
            self.assertEqual(stat.S_IMODE(rejection_root.stat().st_mode), 0o700)
            rejection_paths = sorted(rejection_root.glob("*.json"))
            self.assertEqual(len(rejection_paths), 3)
            for rejection_path in rejection_paths:
                self.assertEqual(stat.S_IMODE(rejection_path.stat().st_mode), 0o600)
                persisted = _read_json(rejection_path)
                self.assertIn(
                    persisted["failure_code"],
                    {"verifier-nonzero", "verifier-timeout"},
                )
            persisted_make = _read_json(
                rejection_root / (make_initial["checkpoint_sha256"] + ".json")
            )
            self.assertEqual(
                persisted_make["rejection_sha256"],
                make_second_retry["inputs"]["host_cad_gate_rejection"][
                    "rejection_sha256"
                ],
            )
            self.assertNotEqual(
                make_retry["inputs"]["host_cad_gate_rejection"][
                    "rejection_sha256"
                ],
                persisted_make["rejection_sha256"],
            )
            self.assertEqual(len(effects.publish_calls), 1)

    def test_non_print_ready_playtest_returns_to_make_before_release(self):
        launcher = _OneSessionProductAgent()
        effects = _FactoryEffects()
        cad_calls = []

        def verified(made, arguments, *, lower=False):
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(
                    (made.made_sha256 + str(len(cad_calls))).encode("ascii")
                ),
                verifier_sha256=arguments["expected_verifier_sha256"],
                verifier_mode=(
                    NATIVE_CAD_NON_PRINT_READY_VERIFIER_MODE
                    if lower
                    else NATIVE_CAD_VERIFIER_MODE
                ),
                verification_tier=(
                    NATIVE_CAD_NON_PRINT_READY_TIER
                    if lower
                    else NATIVE_CAD_FULL_TIER
                ),
                thickness_gate_required=not lower,
                print_ready_eligible=not lower,
            )

        def verify_cad(made, **arguments):
            cad_calls.append((made, dict(arguments)))
            call = len(cad_calls)
            if call == 2:
                self.assertTrue(arguments["require_print_ready"])
                self.assertEqual(effects.publish_calls, [])
                raise _failed_cad_gate(
                    made,
                    arguments,
                    failure_code="cad-not-print-ready",
                    timed_out=False,
                    verification_tier=NATIVE_CAD_NON_PRINT_READY_TIER,
                )
            return verified(made, arguments, lower=call in (1, 3))

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            home = root / "workshop-home"
            assets = _product_run_assets_without_direct_release(root)
            wish = Wish.create(
                "orbit-dog-lower-tier-repair",
                "Build a pocket draughts set inspired by my orbit-loving dog.",
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run.product_run_agent_assets",
                return_value=assets,
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=verify_cad,
            ), mock.patch(
                "workshop.workflow.native_run._factory_credentials",
                side_effect=effects.credentials,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryReleaseWriter",
                side_effect=effects.writer,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession",
                side_effect=effects.session,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryPublicTransition",
                side_effect=effects.transition,
            ):
                receipt = start_native_run(wish)
                repair_binding = launcher.stage_packets[5]["inputs"][
                    "previous_playtest"
                ]
                repair_playtest = _read_json(
                    native_run_paths(wish.product_id).workspace
                    / repair_binding["path"]
                )

        self.assertEqual(
            (receipt["stage"], receipt["status"]), ("release", "complete")
        )
        self.assertEqual(
            [packet["stage"] for packet in launcher.stage_packets],
            [
                "match",
                "invent",
                "make",
                "playtest",
                "playtest",
                "make",
                "playtest",
                "release",
            ],
        )
        rejected_retry = launcher.stage_packets[4]
        self.assertEqual(
            rejected_retry["inputs"]["host_cad_gate_rejection"]["failure_code"],
            "cad-not-print-ready",
        )
        self.assertEqual(repair_playtest["verdict"], "improve")
        self.assertEqual(
            repair_playtest["feedback"][0]["code"],
            "cad-not-print-ready",
        )
        self.assertEqual(len(effects.publish_calls), 1)
        self.assertEqual(cad_calls[-1][1]["evidence_stage"], "release")

    def test_one_native_session_runs_every_stage_and_host_seals_the_release(self):
        launcher = _OneSessionProductAgent()
        effects = _FactoryEffects()
        timing_events = []
        cad_calls = []

        def verify_cad(made, **arguments):
            cad_calls.append((made, dict(arguments)))
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(
                    (made.made_sha256 + str(len(cad_calls))).encode("ascii")
                ),
                verifier_sha256=arguments["expected_verifier_sha256"],
                verifier_mode=NATIVE_CAD_VERIFIER_MODE,
                verification_tier=NATIVE_CAD_FULL_TIER,
                thickness_gate_required=True,
                print_ready_eligible=True,
            )

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            wish = Wish.create(
                "orbit-dog",
                "Build a pocket draughts set inspired by my orbit-loving dog.",
                constraints={"audience": "14+", "manufacture": "not-authorized"},
                context={"source": "native-full-run-test"},
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=verify_cad,
            ), mock.patch(
                "workshop.workflow.native_run._factory_credentials",
                side_effect=effects.credentials,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryReleaseWriter",
                side_effect=effects.writer,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession",
                side_effect=effects.session,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryPublicTransition",
                side_effect=effects.transition,
            ):
                receipt = start_native_run(
                    wish,
                    timing_observer=timing_events.append,
                )
                paths = native_run_paths(wish.product_id)
                effect_path = paths.host_state / "release-effect.json"
                self.assertTrue(effect_path.exists())
                run = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                )
                checkpoint = run.snapshot()

            self.assertEqual(receipt["status"], "complete")
            self.assertEqual(receipt["stage"], "release")
            self.assertEqual(receipt["native_turns"], 4)
            self.assertEqual(receipt["action"], "started")
            self.assertEqual(receipt["publication"]["status"], "public")
            self.assertTrue(receipt["publication"]["verified"])
            self.assertEqual(receipt["publication"]["page_url"], _PAGE_URL)
            self.assertEqual(
                [
                    (event.stage, event.operation, event.state)
                    for event in timing_events
                    if event.operation == "effect.factory"
                ],
                [
                    ("release", "effect.factory", "started"),
                    ("release", "effect.factory", "completed"),
                ],
            )
            self.assertEqual(checkpoint.stage, "release")
            self.assertEqual(checkpoint.status, "complete")

            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 3)
            self.assertEqual(
                [packet["stage"] for packet in launcher.stage_packets],
                ["match", "invent", "make", "release"],
            )
            stage_finalizers = [
                command for command in launcher.finalizer_commands if command[4] != "make-group"
            ]
            self.assertEqual(len(stage_finalizers), 4)
            self.assertEqual(
                sum(1 for command in launcher.finalizer_commands if command[4] == "make-group"), 2
            )
            self.assertEqual(
                len({packet["checkpoint_sha256"] for packet in launcher.stage_packets}),
                4,
            )
            session_calls = launcher.starts + launcher.resumes
            for field in (
                "product_id",
                "wish_sha256",
                "constitution_sha256",
                "run_root",
                "host_state_root",
            ):
                self.assertEqual(
                    {str(arguments[field]) for arguments in session_calls},
                    {str(session_calls[0][field])},
                )
            for arguments in session_calls:
                self.assertNotIn(effects.secret, repr(arguments))
                self.assertNotIn("FACTORY", repr(arguments))

            release_packet = launcher.stage_packets[-1]
            self.assertEqual(
                release_packet["inputs"]["release_contract"],
                {
                    "native_release_schema_version": 3,
                    "manual_path": "MANUAL.pdf",
                    "product_schema_version": 5,
                    "product_status": "manual-ready",
                    "playtest_status": "not-run",
                    "playtest_omission_path": "PLAYTEST-NOT-RUN.json",
                    "manual_design_evidence_path": "MANUAL-DESIGN.json",
                    "manual_design_evidence_schema_version": 1,
                },
            )
            self.assertEqual(
                release_packet["inputs"]["required_package_files"],
                [
                    "MANUAL.pdf",
                    "product.json",
                    "MANUAL-DESIGN.json",
                    "PLAYTEST-NOT-RUN.json",
                ],
            )
            self.assertNotIn("playtested", release_packet["inputs"])

            self.assertEqual(len(cad_calls), 2)
            self.assertEqual(
                {call[0].made_sha256 for call in cad_calls},
                {cad_calls[0][0].made_sha256},
            )
            verifier_path = paths.workspace / ".agents/skills/cad/scripts/verify_project"
            verifier_sha256 = _sha256(verifier_path.read_bytes())
            for made, arguments in cad_calls:
                self.assertEqual(arguments["run_root"], paths.workspace)
                self.assertEqual(arguments["host_state_root"], paths.host_state)
                self.assertTrue(arguments["require_print_ready"])
                self.assertEqual(
                    arguments["expected_verifier_sha256"], verifier_sha256
                )
                self.assertEqual(made.product["title"], "Orbit Dog Draughts")

            self.assertEqual(effects.credential_requests, ["alice"])
            self.assertEqual(len(effects.writer_calls), 2)
            self.assertIs(effects.writer_calls[0][2], effects.credentials_value)
            self.assertEqual(len(effects.ledgers), 1)
            self.assertEqual(
                effects.ledgers[0].path,
                paths.host_state / "factory-effects.sqlite3",
            )
            self.assertEqual(len(effects.session_calls), 1)
            self.assertEqual(len(effects.publish_calls), 1)
            self.assertTrue(effects.publish_calls[0][2].is_verified_draft)

            effect_path = paths.host_state / "release-effect.json"
            self.assertEqual(stat.S_IMODE(effect_path.stat().st_mode), 0o600)
            effect = _read_json(effect_path)
            publication = Receipt.from_dict(effect["receipt"])
            self.assertEqual(effect["schema_version"], 3)
            self.assertEqual(effect["publication_status"], "public")
            self.assertEqual(
                effect["product_page_sha256"],
                publication.details["product_page_sha256"],
            )
            self.assertEqual(
                effect["manual_sha256"], publication.details["manual_sha256"]
            )
            self.assertEqual(effect["manual_path"], "MANUAL.pdf")
            self.assertNotIn("factory_content_sha256", effect)
            self.assertNotIn("factory_content_mapping", effect)
            self.assertTrue(publication.is_verified_public)
            self.assertEqual(publication.details["page_url"], _PAGE_URL)

            expected_paths = {
                "wish": {"artifacts/wish/wish.json"},
                "match": {"artifacts/match/assignment.json"},
                "invent": {"artifacts/invent/invented.json"},
                "make": {
                    "artifacts/make/r0001/made.json",
                    "artifacts/make/r0001/product/product.json",
                    "artifacts/make/r0001/product/assembled.step",
                    "artifacts/make/r0001/product/assembled.step.json",
                    "artifacts/make/r0001/product/assembled.stl",
                    "artifacts/make/r0001/product/cad/project/build.py",
                    "artifacts/make/r0001/product/cad/project/validation/cad-verification.json",
                },
                "release": {
                    "artifacts/release/release.json",
                    "artifacts/release/package/MANUAL.pdf",
                    "artifacts/release/package/PLAYTEST-NOT-RUN.json",
                    "artifacts/release/package/product.json",
                },
            }
            for stage, required in expected_paths.items():
                sealed = {artifact.path for artifact in checkpoint.stage_artifacts[stage]}
                self.assertTrue(required <= sealed, (stage, required - sealed))
                for artifact in checkpoint.stage_artifacts[stage]:
                    self.assertEqual(
                        _sha256((paths.workspace / artifact.path).read_bytes()),
                        artifact.sha256,
                    )

            assignment = NativeMatchAssignment.from_mapping(
                _read_json(paths.workspace / checkpoint.stage_artifacts["match"][0].path)
            )
            invented = NativeInvented.from_mapping(
                _read_json(paths.workspace / checkpoint.stage_artifacts["invent"][0].path)
            )
            made = NativeMade.from_mapping(
                _read_json(paths.workspace / checkpoint.stage_artifacts["make"][0].path)
            )
            release = NativeRelease.from_mapping(
                _read_json(paths.workspace / checkpoint.stage_artifacts["release"][0].path)
            )
            invented.assert_context(assignment)
            made.assert_context(assignment, invented, expected_round=1)
            release.validate_package_tree(paths.workspace, made, None)
            self.assertFalse(
                (paths.workspace / PRODUCT_VERIFICATION_PATH).exists()
            )

            tamper_targets = (
                (
                    paths.workspace / "artifacts/make/r0001/product/assembled.stl",
                    lambda: made.validate_product_tree(paths.workspace),
                ),
                (
                    paths.workspace / "artifacts/release/package/MANUAL.pdf",
                    lambda: release.validate_package_tree(
                        paths.workspace, made, None
                    ),
                ),
                (
                    paths.workspace
                    / "artifacts/release/package/PLAYTEST-NOT-RUN.json",
                    lambda: release.validate_package_tree(paths.workspace, made, None),
                ),
            )
            for target, validator in tamper_targets:
                original = target.read_bytes()
                target.write_bytes(original + b"tampered")
                with self.assertRaises(ArtifactError):
                    validator()
                target.write_bytes(original)
                validator()

            for root in (paths.workspace, paths.host_state):
                for path in root.rglob("*"):
                    if path.is_file():
                        self.assertNotIn(effects.secret.encode("utf-8"), path.read_bytes())

            gates = sorted(path.name for path in (paths.host_state / "gates").iterdir())
            self.assertEqual(
                gates,
                [
                    "0000-wish.json",
                    "0001-match.json",
                    "0002-invent.json",
                    "0003-make.json",
                    "0004-release.json",
                ],
            )
            make_gate = _read_json(paths.host_state / "gates/0003-make.json")
            release_gate = _read_json(paths.host_state / "gates/0004-release.json")
            invent_gate = _read_json(paths.host_state / "gates/0002-invent.json")
            by_stage = {packet["stage"]: packet for packet in launcher.stage_packets}
            design_vault = by_stage["invent"]["inputs"]["design_vault"]
            self.assertEqual(design_vault["path"], "VAULT.json")
            self.assertEqual(design_vault["nodes"], len(E2E_NODES))
            self.assertEqual(
                invent_gate["evidence"]["checks"]["design_vault_sha256"],
                Vault.from_packed_bytes(
                    (paths.workspace / design_vault["path"]).read_bytes()
                ).sha256,
            )
            leads = by_stage["make"]["inputs"]["vault_leads"]
            self.assertTrue(leads)
            self.assertTrue(all(lead["kind"] == "risk" for lead in leads))
            # Round one: the Wish names no vault mechanism, so Invent gets the
            # constraint-only findings (a list, never absent while the vault is up).
            self.assertIsInstance(by_stage["invent"]["inputs"]["vault_leads"], list)
            self.assertEqual(
                invent_gate["evidence"]["checks"]["vault_leads"], len(leads)
            )
            self.assertEqual(by_stage["make"]["inputs"]["score_history"], [])
            self.assertEqual(by_stage["make"]["inputs"]["regression"], {})
            self.assertEqual(by_stage["make"]["inputs"]["ambiguous"], [])
            self.assertTrue(make_gate["evidence"]["checks"]["cad_verification_passed"])
            self.assertEqual(make_gate["evidence"]["checks"]["build_groups"], 2)
            self.assertEqual(make_gate["evidence"]["checks"]["build_parts"], 2)
            self.assertTrue(
                (paths.workspace / "artifacts/make/r0001/product/groups/pieces.json").is_file()
            )
            self.assertTrue(
                release_gate["evidence"]["checks"]["cad_print_ready_eligible"]
            )
            self.assertEqual(
                release_gate["evidence"]["checks"]["publication_status"],
                "public",
            )
            self.assertTrue(
                release_gate["evidence"]["checks"]["factory_readback_verified"]
            )
            self.assertEqual(
                release_gate["evidence"]["checks"]["playtest_status"],
                "not-run",
            )
            self.assertEqual(
                release_gate["evidence"]["checks"]["product_verification_status"],
                "not-recorded",
            )
            self.assertNotIn(
                "product_verification_sha256", release_gate["evidence"]["checks"]
            )

    def test_each_selectable_effort_runs_its_exact_passthrough_route(self):
        routes = {
            "spark": ["make", "release"],
            "forge": ["invent", "make", "release"],
            "quest": ["invent", "make", "playtest", "release"],
        }

        for effort, expected_stages in routes.items():
            with self.subTest(effort=effort), tempfile.TemporaryDirectory() as temporary:
                launcher = _OneSessionProductAgent()
                effects = _FactoryEffects()
                home = Path(temporary).resolve() / "workshop-home"
                wish = Wish.create(
                    "effort-%s" % effort,
                    "Build a pocket draughts set inspired by my orbit-loving dog.",
                )

                def verify_cad(made, **arguments):
                    return SimpleNamespace(
                        passed=True,
                        receipt_sha256=_sha256(made.made_sha256.encode("ascii")),
                        verifier_sha256=arguments["expected_verifier_sha256"],
                        verifier_mode=NATIVE_CAD_VERIFIER_MODE,
                        verification_tier=NATIVE_CAD_FULL_TIER,
                        thickness_gate_required=True,
                        print_ready_eligible=True,
                    )

                with mock.patch.dict(
                    os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
                ), mock.patch(
                    "workshop.workflow.native_run._source_checkout_root",
                    return_value=None,
                ), mock.patch(
                    "workshop.workflow.native_run.CodexNativeSessionLauncher",
                    return_value=launcher,
                ), mock.patch(
                    "workshop.workflow.native_run.verify_native_made_cad",
                    side_effect=verify_cad,
                ), mock.patch(
                    "workshop.workflow.native_run._factory_credentials",
                    side_effect=effects.credentials,
                ), mock.patch(
                    "workshop.workflow.native_run.FactoryReleaseWriter",
                    side_effect=effects.writer,
                ), mock.patch(
                    "workshop.workflow.native_run.FactoryAgentSession",
                    side_effect=effects.session,
                ), mock.patch(
                    "workshop.workflow.native_run.FactoryPublicTransition",
                    side_effect=effects.transition,
                ):
                    receipt = start_native_run(wish, effort=effort)
                    paths = native_run_paths(wish.product_id)
                    checkpoint = AgentRun.open(
                        paths.workspace, host_state_root=paths.host_state
                    ).snapshot()

                self.assertEqual(receipt["status"], "complete")
                self.assertEqual(receipt["effort"], effort)
                self.assertEqual(checkpoint.effort, effort)
                self.assertEqual(
                    [packet["stage"] for packet in launcher.stage_packets],
                    expected_stages,
                )
                self.assertEqual(receipt["native_turns"], len(expected_stages))
                self.assertNotIn("match", checkpoint.stage_artifacts)
                self.assertEqual(
                    "playtest" in checkpoint.stage_artifacts,
                    effort == "quest",
                )
                creative_stage = "make" if effort == "spark" else "invent"
                creative_paths = {
                    Path(item.path).name
                    for item in checkpoint.stage_artifacts[creative_stage]
                }
                self.assertTrue(
                    {"assignment.json", "invented.json"} <= creative_paths
                )
                release = NativeRelease.from_mapping(
                    _read_json(
                        paths.workspace
                        / checkpoint.stage_artifacts["release"][0].path
                    )
                )
                self.assertEqual(release.schema_version, 2 if effort == "quest" else 3)
                if effort == "quest":
                    by_stage = {
                        packet["stage"]: packet for packet in launcher.stage_packets
                    }
                    leads = by_stage["make"]["inputs"]["vault_leads"]
                    self.assertTrue(leads)
                    self.assertEqual(by_stage["playtest"]["inputs"]["vault_leads"], leads)
                    checks = _read_json(
                        next((paths.host_state / "gates").glob("*-playtest.json"))
                    )["evidence"]["checks"]
                    self.assertEqual(checks["vault_leads_answered"], len(leads))
                    self.assertEqual(checks["vault_leads_confirmed"], 0)
                    self.assertEqual(checks["score_reads"], 3)
                    self.assertEqual(
                        checks["score_median"],
                        {"wish_fit": 8, "play": 8, "legibility": 8, "build_confidence": 8},
                    )
                    self.assertEqual(
                        checks["score_spread"],
                        {"wish_fit": 1, "play": 1, "legibility": 1, "build_confidence": 1},
                    )


if __name__ == "__main__":
    unittest.main()
