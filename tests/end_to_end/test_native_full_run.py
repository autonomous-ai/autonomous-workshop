import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workshop.artifacts import build_artifact_manifest
from workshop.workflow.native_run import (
    _MAX_NATIVE_TURNS,
    native_run_paths,
    resume_native_run,
    start_native_run,
)
from workshop.errors import ArtifactError, StateConflict
from workshop.invent.vault import Vault, seed_vault
from workshop.invent.native import NativeInvented
from workshop.make.native import NativeMade
from workshop.make.native_gate import (
    NATIVE_CAD_FULL_TIER,
    NATIVE_CAD_VERIFIER_MODE,
    NATIVE_CAD_VERIFIER_PATH,
    CapturedVerifierStream,
    NativeCadGateError,
    NativeCadGateEvidence,
)
from workshop.match.native import NativeMatchAssignment
from workshop.playtest.native import NativePlaytested
from workshop.release.native import NativeRelease
from workshop.release.verification import (
    PRODUCT_VERIFICATION_PATH,
    read_product_verification,
)
from workshop.runtime import CodexRecoverableInvocationError, Receipt
from workshop.runtime.agent_assets import ProductRunAgentAssets
from workshop.wish import Wish
from workshop.workflow import AgentRun
from workshop.workflow.agent_run import AgentArtifact, AgentOutcome
from workshop.workflow.proposals import AgentOutcomeProposal


_OBSERVED_AT = "2026-08-26T00:00:00+00:00"
_PAGE_URL = "https://www.autonomous.ai/factory/product/orbit-dog"
_COVER_URL = "https://cdn.autonomous.ai/products/orbit-dog/cover.webp"
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

    content = (
        b"BT\n/F1 15 Tf\n36 370 Td\n(Orbit Dog Draughts) Tj\n"
        b"0 -28 Td\n/F1 10 Tf\n(Set out the board and every playing piece.) Tj\n"
        b"0 -18 Td\n(Use standard English draughts rules.) Tj\n"
        b"0 -18 Td\n(For ages fourteen and older. Keep small parts away.) Tj\nET\n"
    )
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 297.64 419.53] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    )
    document = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, 1):
        offsets.append(len(document))
        document.extend(b"%d 0 obj\n" % number)
        document.extend(body)
        document.extend(b"\nendobj\n")
    xref = len(document)
    document.extend(b"xref\n0 %d\n" % (len(objects) + 1))
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(b"%010d 00000 n \n" % offset)
    document.extend(
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objects) + 1, xref)
    )
    return bytes(document)


def _failed_cad_gate(
    made,
    arguments,
    *,
    failure_code,
    timed_out,
    stdout_content=b"CAD verifier inspected the sealed revision.\n",
    stderr_content=None,
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
        ),
        returncode=-9 if timed_out else 7,
        duration_ms=1_800_000 if timed_out else 11,
        timed_out=timed_out,
        stdout=stdout,
        stderr=stderr,
        source_tree_unchanged=True,
    )
    evidence_parent = Path(arguments["host_state_root"]) / "evidence" / "make"
    current = Path(arguments["host_state_root"])
    for part in ("evidence", "make"):
        current = current / part
        current.mkdir(mode=0o700, exist_ok=True)
        os.chmod(current, 0o700)
    evidence_path = evidence_parent / (
        "r%04d-cad-gate.json" % made.round
    )
    evidence_path.write_bytes(_canonical_json(evidence.to_dict()) + b"\n")
    os.chmod(evidence_path, 0o600)
    return NativeCadGateError(failure_code, evidence, evidence_path)


class _SessionOutcome:
    def __init__(self, arguments):
        self.arguments = dict(arguments)

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

    def __init__(self, *, playtest_plan=None, confirm_first_lead=False):
        self.starts = []
        self.resumes = []
        self.stage_packets = []
        self.finalizer_commands = []
        self.playtest_plan = list(playtest_plan) if playtest_plan else []
        self.confirm_first_lead = confirm_first_lead

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
        inventors = stage["inputs"]["inventor_roster"]["inventors"]
        ids = [entry["inventor_id"] for entry in inventors]
        if ids != sorted(ids) or "alice" not in ids:
            raise AssertionError("fixture received a non-canonical inventor roster")
        ranking = [
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
        source = "authored/match.json"
        _write_json(
            run_root / source,
            {"selected_inventor_id": "alice", "ranking": ranking},
        )
        self._run_finalizer(run_root, "match", "--source", source)

    def _author_invent(self, run_root, stage):
        assignment = stage["inputs"]["assignment"]
        if assignment["selected_inventor_id"] != "alice":
            raise AssertionError("Invent did not receive the accepted Match assignment")
        source = "authored/invent.json"
        _write_json(
            run_root / source,
            {
                "concept": {
                    "title": "Orbit Dog Draughts",
                    "summary": (
                        "A pocket draughts set whose concentric board, opposing orbit "
                        "packs, and king pieces turn the requested dog into the geometry "
                        "of a familiar public-domain game."
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
            },
        )
        self._run_finalizer(run_root, "invent", "--source", source)

    def _author_make(self, run_root, stage):
        inputs = stage["inputs"]
        product_root_value = inputs["product_root"]
        product_root = run_root / product_root_value
        (product_root / "cad" / "project").mkdir(parents=True, exist_ok=True)
        (product_root / "validation").mkdir(exist_ok=True)
        wish = _read_json(run_root / "WISH.json")
        invented = inputs["invented"]
        if invented["concept"]["title"] != "Orbit Dog Draughts":
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
        _write_json(
            product_root / "validation" / "cad-verification.json",
            {
                "schema_version": 1,
                "validator": "materialized-cad-final",
                "validator_version": "1.0.0",
                "passed": True,
                "checks": ["fresh-export", "strict-fit", "printable-mesh"],
            },
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
                run_root, "make-group", "--product-root", product_root_value, "--group", group["group"]
            )
        self._run_finalizer(
            run_root,
            "make",
            "--product-root",
            product_root_value,
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "validation/cad-verification.json",
        )

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
        if self.playtest_plan:
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
        package_root_value = inputs["package_root"]
        package_root = run_root / package_root_value
        package_root.mkdir(parents=True, exist_ok=True)
        (package_root / "MANUAL.pdf").write_bytes(_manual_pdf())
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
        return _SessionOutcome(arguments)

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
            proposed_transition="deliver",
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
            if not (Path(root) / "MANUAL.pdf").is_file():
                raise AssertionError("Factory effect did not receive the verified manual")
            product_page_sha256 = next(
                entry.sha256
                for entry in manifest.entries
                if entry.path == "product.json"
            )
            manual_sha256 = next(
                entry.sha256
                for entry in manifest.entries
                if entry.path == "MANUAL.pdf"
            )
            return Receipt(
                payload_sha256=_sha256(b"fixture-model-handoff"),
                artifact_sha256=context.made.artifact_sha256,
                adapter="factory",
                status="draft",
                observed_at=_OBSERVED_AT,
                reference="design-orbit-dog",
                details={
                    "release_sha256": manifest.artifact_sha256,
                    "product_page_sha256": product_page_sha256,
                    "manual_path": "MANUAL.pdf",
                    "manual_sha256": manual_sha256,
                    "page_url": _PAGE_URL,
                    "cover_url": _COVER_URL,
                },
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
    def test_release_without_factory_credentials_reaches_deliver(self):
        launcher = _OneSessionProductAgent()
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
                receipt = start_native_run(wish, publish_requested=True)
                paths = native_run_paths(wish.product_id)
                run = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                )
                checkpoint = run.snapshot()

            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(receipt["stage"], "deliver")
            self.assertEqual(receipt["native_turns"], 5)
            self.assertEqual(receipt["publication"]["status"], "not-created")
            self.assertTrue(receipt["publication"]["requested"])
            self.assertIn("Factory credentials", receipt["publication"]["reason"])
            self.assertIn("Factory credentials", receipt["needs"][0])
            self.assertEqual(checkpoint.status, "waiting")
            self.assertEqual(checkpoint.stage, "deliver")
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 4)
            self.assertEqual(
                [packet["stage"] for packet in launcher.stage_packets],
                ["match", "invent", "make", "playtest", "release"],
            )
            release_packet = launcher.stage_packets[-1]
            self.assertEqual(
                release_packet["inputs"]["release_contract"],
                {
                    "native_release_schema_version": 2,
                    "manual_path": "MANUAL.pdf",
                    "product_schema_version": 4,
                    "product_status": "manual-ready",
                },
            )
            self.assertEqual(
                release_packet["inputs"]["required_package_files"],
                ["MANUAL.pdf", "product.json"],
            )
            release_gate_path = sorted(
                (paths.host_state / "gates").glob("*-release.json")
            )[-1]
            release_gate = _read_json(release_gate_path)
            checks = release_gate["evidence"]["checks"]
            self.assertTrue(checks["local_release_sealed"])
            self.assertTrue(checks["package_tree_rehashed"])
            self.assertEqual(checks["manual_path"], "MANUAL.pdf")
            self.assertNotIn("publication_status", checks)
            self.assertNotIn("factory_readback_verified", checks)
            self.assertEqual(
                checks["product_verification_status"],
                "not-recorded",
            )
            stage_finalizers = [
                command for command in launcher.finalizer_commands if command[4] != "make-group"
            ]
            self.assertEqual(len(stage_finalizers), 5)
            self.assertEqual(
                sum(1 for command in launcher.finalizer_commands if command[4] == "make-group"), 2
            )
            self.assertEqual(effects.writer_calls, [])
            self.assertEqual(effects.publish_calls, [])
            self.assertFalse((paths.host_state / "release-effect-wait.json").exists())
            self.assertFalse((paths.host_state / "release-effect.json").exists())
            self.assertFalse((paths.host_state / "factory-effects.sqlite3").exists())
            self.assertIn("release", checkpoint.stage_artifacts)
            self.assertTrue(
                (paths.workspace / "artifacts/release/package/MANUAL.pdf").is_file()
            )

    def test_frozen_legacy_run_receives_and_finishes_its_markdown_release(self):
        launcher = _LegacyReleaseProductAgent()

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
            legacy_root = root / "legacy-assets"
            constitution = legacy_root / ".agents/product-run/AGENTS.md"
            constitution.parent.mkdir(parents=True)
            shutil.copy2(
                repository / ".agents/product-run/AGENTS.md",
                constitution,
            )
            skill_root = (
                legacy_root
                / ".agents/product-run/.agents/skills/autonomous-workshop"
            )
            shutil.copytree(
                repository
                / ".agents/product-run/.agents/skills/autonomous-workshop",
                skill_root,
            )
            (skill_root / "scripts/pdf_validator.py").unlink()
            assets = ProductRunAgentAssets(
                constitution=constitution,
                skill_root=skill_root,
                sha256="0" * 64,
                source="package",
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
            ):
                receipt = start_native_run(wish)
                paths = native_run_paths(wish.product_id)
                checkpoint = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                ).snapshot()

            self.assertEqual(receipt["stage"], "deliver")
            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(checkpoint.stage, "deliver")
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
            release_gate = _read_json(
                sorted((paths.host_state / "gates").glob("*-release.json"))[-1]
            )
            self.assertEqual(release_gate["evidence"]["checks"]["manual_path"], "MANUAL.md")
            self.assertEqual(
                release_gate["evidence"]["checks"][
                    "native_release_schema_version"
                ],
                1,
            )

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
            home = Path(temporary).resolve() / "workshop-home"
            wish = Wish.create(
                "manual-first-no-downgrade",
                "Build a pocket draughts set inspired by my orbit-loving dog.",
                constraints={"audience": "14+", "manufacture": "not-authorized"},
                context={"source": "release-downgrade-regression"},
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
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
                ["MANUAL.pdf", "product.json"],
            )

    def _run_playtest_routing_case(
        self,
        *,
        playtest_plan,
        wish_name,
        context_source,
        launcher=None,
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
            home = Path(temporary).resolve() / "workshop-home"
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
                receipt = start_native_run(wish, publish_requested=False)
                paths = native_run_paths(wish.product_id)
                run = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                )
                checkpoint = run.snapshot()

        self.assertEqual(receipt["status"], "waiting")
        self.assertEqual(receipt["stage"], "deliver")
        return launcher, checkpoint

    def test_timeout_continues_same_session_through_the_full_run(self):
        with mock.patch("workshop.workflow.native_run.time.sleep") as backoff:
            launcher, checkpoint = self._run_playtest_routing_case(
                playtest_plan=[],
                wish_name="orbit-dog-timeout-continuation",
                context_source="native-timeout-continuation-test",
                launcher=_TimeoutOnceProductAgent(),
            )

        self.assertEqual(checkpoint.stage, "deliver")
        self.assertEqual(checkpoint.status, "waiting")
        self.assertEqual(len(launcher.starts), 1)
        self.assertEqual(len(launcher.resumes), 5)
        backoff.assert_called_once()
        self.assertEqual(
            [packet["stage"] for packet in launcher.stage_packets],
            ["match", "invent", "make", "playtest", "release"],
        )

    def test_design_invalidating_playtest_verdict_routes_back_to_make(self):
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
                                "Revise the design and geometry in Make so every "
                                "waypoint is centered on a playable square."
                            ),
                            "evidence_refs": ["results/mechanical-check.json"],
                            "invalidates": ["playtest", "release", "deliver"],
                        }
                    ],
                )
            ],
            wish_name="orbit-dog-design-revision",
            context_source="native-playtest-design-revision-test",
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
        first_make_packet = launcher.stage_packets[2]
        second_make_packet = launcher.stage_packets[4]
        self.assertEqual(first_make_packet["round"], 1)
        self.assertEqual(second_make_packet["round"], 2)
        self.assertNotEqual(
            first_make_packet["checkpoint_sha256"],
            second_make_packet["checkpoint_sha256"],
        )
        self.assertEqual(
            second_make_packet["inputs"]["previous_playtest"]["path"],
            "artifacts/playtest/r0001/playtested.json",
        )
        make_artifacts = checkpoint.stage_artifacts["make"]
        self.assertTrue(any("r0002" in artifact.path for artifact in make_artifacts))

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
                            "invalidates": ["playtest", "release", "deliver"],
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
                "invalidates": ["playtest", "release", "deliver"],
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

    def test_confirmed_leads_reach_the_next_wish_and_the_host_vault(self):
        finding = {
            "code": "idle-seat",
            "area": "play",
            "severity": "block",
            "finding": "One seat idles while the other resolves captures.",
            "change": "Resolve captures simultaneously.",
            "evidence_refs": ["results/agent-playtest.json"],
            "invalidates": ["playtest", "release", "deliver"],
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
            seed_vault(home / "vault")
            first = _OneSessionProductAgent(playtest_plan=[("block", [finding])], confirm_first_lead=True)
            second = _OneSessionProductAgent()
            launchers = iter((first, second))
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root", return_value=None
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                side_effect=lambda *a, **k: next(launchers),
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
                receipt_a = start_native_run(wish_a, publish_requested=False)
                wish_b = Wish.create(
                    "orbit-dog-b",
                    "Build a pocket draughts set for my other dog.",
                    constraints={"audience": "14+"},
                    context={"source": "native-ledger-test"},
                )
                receipt_b = start_native_run(wish_b, publish_requested=False)

                self.assertEqual((receipt_a["stage"], receipt_b["stage"]), ("deliver", "deliver"))
                first_leads = [p for p in first.stage_packets if p["stage"] == "playtest"][0]["inputs"]["vault_leads"]
                confirmed_symptom = first_leads[0]["nodes"][1]
                ledger = (home / "evidence" / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
                rows = [json.loads(line) for line in ledger]
                self.assertEqual([row["ref"] for row in rows], ["orbit-dog-a#r1:idle-seat"])
                self.assertEqual(rows[0]["symptom"], confirmed_symptom)
                self.assertEqual(rows[0]["weight"], 3)
                self.assertIn("mechanisms/stacking-and-balancing", rows[0]["mechanisms"])
                node = home / "vault" / (confirmed_symptom + ".md")
                self.assertIn("- [orbit-dog-a#r1:idle-seat] block:", node.read_text(encoding="utf-8"))
                review = home / "vault" / "_review" / "orbit-dog-a-r1.md"
                self.assertTrue(review.is_file())
                self.assertEqual(
                    [p["inputs"]["prior_evidence"] for p in first.stage_packets if p["stage"] in ("make", "playtest")],
                    [[], [], [], []],
                )
                for stage in ("make", "playtest"):
                    packet = [p for p in second.stage_packets if p["stage"] == stage][0]
                    self.assertEqual([row["ref"] for row in packet["inputs"]["prior_evidence"]], ["orbit-dog-a#r1:idle-seat"])
                self.assertEqual(receipt_a["rounds"][0]["vault_leads_confirmed"], 1)

    def test_a_worse_round_redirects_the_next_make_to_the_best_sealed_round(self):
        one = {
            "code": "waypoint-misalignment",
            "area": "make",
            "severity": "block",
            "finding": "Waypoints miss the grid.",
            "change": "Center every waypoint on a playable square.",
            "evidence_refs": ["results/mechanical-check.json"],
            "invalidates": ["playtest", "release", "deliver"],
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
                "orbit-dog-cad-retry",
                "Build a pocket draughts set inspired by my orbit-loving dog.",
                constraints={"audience": "14+", "manufacture": "not-authorized"},
                context={"source": "native-cad-retry-test"},
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
                receipt = start_native_run(wish, publish_requested=False)
                paths = native_run_paths(wish.product_id)
                checkpoint = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                ).snapshot()

            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(receipt["stage"], "deliver")
            self.assertEqual(receipt["native_turns"], 8)
            self.assertEqual(checkpoint.stage, "deliver")
            self.assertEqual(checkpoint.status, "waiting")
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 7)
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
                ],
            )
            self.assertEqual(len(cad_calls), 5)
            self.assertFalse((paths.workspace / "agent-outcome.json").exists())

            make_initial, make_retry, make_second_retry = (
                launcher.stage_packets[2:5]
            )
            playtest_initial, playtest_retry = launcher.stage_packets[5:7]
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

            rejection_root = paths.host_state / "cad-gate-rejections"
            self.assertEqual(stat.S_IMODE(rejection_root.stat().st_mode), 0o700)
            rejection_paths = sorted(rejection_root.glob("*.json"))
            self.assertEqual(len(rejection_paths), 2)
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

    def test_one_native_session_runs_every_stage_and_host_seals_the_release(self):
        launcher = _OneSessionProductAgent()
        effects = _FactoryEffects()
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
                local_receipt = start_native_run(wish, publish_requested=False)
                paths = native_run_paths(wish.product_id)
                native_calls_before_promotion = len(launcher.starts) + len(
                    launcher.resumes
                )
                effect_path = paths.host_state / "release-effect.json"
                self.assertFalse(effect_path.exists())
                receipt = resume_native_run(
                    wish.product_id, publish_requested=True
                )
                run = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                )
                checkpoint = run.snapshot()

            self.assertEqual(local_receipt["status"], "waiting")
            self.assertEqual(local_receipt["stage"], "deliver")
            self.assertEqual(local_receipt["native_turns"], 5)
            self.assertEqual(local_receipt["publication"]["status"], "not-created")
            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(receipt["stage"], "deliver")
            self.assertEqual(receipt["native_turns"], 5)
            self.assertEqual(receipt["action"], "published-existing-release")
            self.assertEqual(receipt["publication"]["status"], "public")
            self.assertTrue(receipt["publication"]["verified"])
            self.assertEqual(receipt["publication"]["page_url"], _PAGE_URL)
            self.assertEqual(checkpoint.stage, "deliver")
            self.assertEqual(checkpoint.status, "waiting")
            self.assertEqual(
                len(launcher.starts) + len(launcher.resumes),
                native_calls_before_promotion,
            )

            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 4)
            self.assertEqual(
                [packet["stage"] for packet in launcher.stage_packets],
                ["match", "invent", "make", "playtest", "release"],
            )
            stage_finalizers = [
                command for command in launcher.finalizer_commands if command[4] != "make-group"
            ]
            self.assertEqual(len(stage_finalizers), 5)
            self.assertEqual(
                sum(1 for command in launcher.finalizer_commands if command[4] == "make-group"), 2
            )
            self.assertEqual(
                len({packet["checkpoint_sha256"] for packet in launcher.stage_packets}),
                5,
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
                release_packet["inputs"]["playtested"]["kind"],
                "autonomous-workshop.playtested",
            )
            self.assertEqual(
                release_packet["inputs"]["playtested_artifact"][
                    "playtested_sha256"
                ],
                release_packet["inputs"]["playtested"]["playtested_sha256"],
            )

            self.assertEqual(len(cad_calls), 2)
            self.assertEqual(cad_calls[0][0].made_sha256, cad_calls[1][0].made_sha256)
            verifier_path = paths.workspace / ".agents/skills/cad/scripts/verify_project"
            verifier_sha256 = _sha256(verifier_path.read_bytes())
            for made, arguments in cad_calls:
                self.assertEqual(arguments["run_root"], paths.workspace)
                self.assertEqual(arguments["host_state_root"], paths.host_state)
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
                    "artifacts/make/r0001/product/validation/cad-verification.json",
                },
                "playtest": {
                    "artifacts/playtest/r0001/playtested.json",
                    "artifacts/playtest/r0001/evidence/results/agent-playtest.json",
                    "artifacts/playtest/r0001/evidence/results/mechanical-check.json",
                    "artifacts/playtest/r0001/evidence/results/printability-check.json",
                },
                "release": {
                    "artifacts/release/release.json",
                    "artifacts/release/package/MANUAL.pdf",
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
            playtested = NativePlaytested.from_mapping(
                _read_json(paths.workspace / checkpoint.stage_artifacts["playtest"][0].path)
            )
            release = NativeRelease.from_mapping(
                _read_json(paths.workspace / checkpoint.stage_artifacts["release"][0].path)
            )
            invented.assert_context(assignment)
            made.assert_context(assignment, invented, expected_round=1)
            release.validate_package_tree(paths.workspace, made, playtested)
            verification = read_product_verification(
                paths.workspace / PRODUCT_VERIFICATION_PATH
            )
            verification.assert_context(release, made, playtested)

            tamper_targets = (
                (
                    paths.workspace / "artifacts/make/r0001/product/assembled.stl",
                    lambda: made.validate_product_tree(paths.workspace),
                ),
                (
                    paths.workspace
                    / "artifacts/playtest/r0001/evidence/results/agent-playtest.json",
                    lambda: playtested.validate_evidence_tree(paths.workspace, made),
                ),
                (
                    paths.workspace / "artifacts/release/package/MANUAL.pdf",
                    lambda: release.validate_package_tree(
                        paths.workspace, made, playtested
                    ),
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
                    "0004-playtest.json",
                    "0005-release.json",
                ],
            )
            make_gate = _read_json(paths.host_state / "gates/0003-make.json")
            playtest_gate = _read_json(paths.host_state / "gates/0004-playtest.json")
            release_gate = _read_json(paths.host_state / "gates/0005-release.json")
            invent_gate = _read_json(paths.host_state / "gates/0002-invent.json")
            by_stage = {packet["stage"]: packet for packet in launcher.stage_packets}
            design_vault = by_stage["invent"]["inputs"]["design_vault"]
            self.assertEqual(design_vault["path"], ".agents/skills/design-vault/vault.json")
            self.assertGreater(design_vault["nodes"], 100)
            self.assertEqual(
                invent_gate["evidence"]["checks"]["design_vault_sha256"],
                Vault.from_packed_bytes(
                    (paths.workspace / design_vault["path"]).read_bytes()
                ).sha256,
            )
            leads = by_stage["make"]["inputs"]["vault_leads"]
            self.assertTrue(leads)
            self.assertTrue(all(lead["kind"] == "risk" for lead in leads))
            self.assertEqual(
                invent_gate["evidence"]["checks"]["vault_leads"], len(leads)
            )
            self.assertEqual(by_stage["playtest"]["inputs"]["vault_leads"], leads)
            self.assertEqual(
                playtest_gate["evidence"]["checks"]["vault_leads_answered"], len(leads)
            )
            self.assertEqual(playtest_gate["evidence"]["checks"]["vault_leads_confirmed"], 0)
            self.assertEqual(playtest_gate["evidence"]["checks"]["score_reads"], 3)
            self.assertEqual(
                playtest_gate["evidence"]["checks"]["score_median"],
                {"wish_fit": 8, "play": 8, "legibility": 8, "build_confidence": 8},
            )
            self.assertEqual(
                playtest_gate["evidence"]["checks"]["score_spread"],
                {"wish_fit": 1, "play": 1, "legibility": 1, "build_confidence": 1},
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
                playtest_gate["evidence"]["checks"]["cad_verification_passed"]
            )
            self.assertTrue(
                release_gate["evidence"]["checks"]["local_release_sealed"]
            )
            self.assertEqual(
                release_gate["evidence"]["checks"]["product_verification_status"],
                "recorded",
            )
            self.assertEqual(
                release_gate["evidence"]["checks"]["product_verification_sha256"],
                verification.sha256,
            )


if __name__ == "__main__":
    unittest.main()
