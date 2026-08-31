#!/usr/bin/env python3
"""Deterministic Codex-CLI boundary executable for offline E2E acceptance.

This is intentionally a process, not a launcher mock.  The production
``CodexNativeSessionLauncher`` invokes it with the real command, permission
policy, scrubbed environment, stdin prompt, JSONL event protocol, and durable
session checkpoint behavior.  It authors only stage inputs and delegates all
contract construction to the materialized production finalizer.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import stat
from pathlib import Path

import reportlab
from PIL import Image, ImageDraw
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


THREAD_ID = "00000000-0000-4000-8000-000000000001"
OBSERVED_AT = "2026-08-27T00:00:00+00:00"
TRACE_KIND = "autonomous-workshop.deterministic-e2e-turn"
_LAST_FINALIZER = None


def canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


def emit(value) -> None:
    sys.stdout.write(json.dumps(value, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def manual_pdf() -> bytes:
    font_name = "DeterministicWorkshopVera"
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
    for lines in (
        (
            "Orbit Dog Draughts",
            "Meet the exact board and every playing piece.",
            "A tiny orbital match is ready to begin.",
        ),
        (
            "Set up and play",
            "Use standard English draughts rules.",
            "For ages fourteen and older. Keep small parts away.",
        ),
    ):
        canvas.setFont(font_name, 15)
        canvas.drawString(30, 370, lines[0])
        canvas.setFont(font_name, 10)
        canvas.drawString(30, 340, lines[1])
        canvas.drawString(30, 320, lines[2])
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def manual_design_evidence(manual: bytes, made) -> dict:
    visual = next(
        entry
        for entry in made["product_manifest"]["entries"]
        if entry["path"] == "assembled.stl"
    )
    return {
        "schema_version": 1,
        "kind": "autonomous-workshop.manual-design-evidence",
        "manual_sha256": hashlib.sha256(manual).hexdigest(),
        "design_mode": "bespoke",
        "creative_brief": {
            "emotional_promise": (
                "Unbox a tiny orbital rivalry that feels ready for a first match."
            ),
            "physical_format": "Two-page A6 field card",
            "format_rationale": (
                "Two compact pages keep the inventory and first turn visible together."
            ),
            "visual_motif": (
                "Orbital paths connect exact piece silhouettes to numbered actions."
            ),
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
            "resolved_changes": [
                "Moved setup to page two and strengthened its action hierarchy."
            ],
            "status": "approved",
        },
    }


def tetrahedron_stl() -> bytes:
    return b"""solid orbit_dog
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 0 20 0
      vertex 20 0 0
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 20 0 0
      vertex 0 0 20
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 0 0 20
      vertex 0 20 0
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 20 0 0
      vertex 0 20 0
      vertex 0 0 20
    endloop
  endfacet
endsolid orbit_dog
"""


def finalizer(root: Path, *arguments: str) -> None:
    global _LAST_FINALIZER
    python = os.environ.get("WORKSHOP_PYTHON")
    if not python:
        raise RuntimeError("WORKSHOP_PYTHON was not bound by the launcher")
    script = (
        root
        / ".agents/skills/autonomous-workshop/scripts/stage_proposal.py"
    )
    completed = subprocess.run(
        [python, str(script), "--run-root", str(root), *arguments],
        cwd=root,
        env={
            "PATH": os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "WORKSHOP_PYTHON": python,
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    if completed.returncode:
        raise RuntimeError(
            "stage finalizer failed: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    _LAST_FINALIZER = {
        "arguments": list(arguments),
        "returncode": completed.returncode,
        "script": str(script.relative_to(root)),
    }


def mutable_inventory(root: Path) -> dict[str, str]:
    """Hash only agent/finalizer-owned mutable paths in the run workspace."""

    candidates = [root / "authored", root / "artifacts", root / "agent-outcome.json"]
    inventory = {}
    for candidate in candidates:
        paths = candidate.rglob("*") if candidate.is_dir() else (candidate,)
        for path in paths:
            if (
                path == root / "authored/runtime-trace.jsonl"
                or not path.is_file()
                or path.is_symlink()
            ):
                continue
            relative = path.relative_to(root).as_posix()
            inventory[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return inventory


def inventory_sha256(inventory: dict[str, str]) -> str:
    return hashlib.sha256(canonical_json(sorted(inventory.items()))).hexdigest()


def author_match(root: Path, stage) -> None:
    roster = stage["inputs"]["inventor_roster"]["inventors"]
    ids = [entry["inventor_id"] for entry in roster]
    if ids != sorted(ids) or "alice" not in ids:
        raise RuntimeError("Match received a non-canonical Inventor roster")
    ranking = ["alice"] + [item for item in ids if item != "alice"]
    source = "authored/match.json"
    write_json(
        root / source,
        {
            "selected_inventor_id": "alice",
            "ranking": [
                {
                    "inventor_id": inventor_id,
                    "rationale": (
                        "Alice best preserves familiar draughts play while giving "
                        "the exact Wish a structurally specific physical form."
                        if inventor_id == "alice"
                        else "%s is eligible, but its Taste fits this exact Wish less directly."
                        % inventor_id.title()
                    ),
                }
                for inventor_id in ranking
            ],
        },
    )
    finalizer(root, "match", "--source", source)


def ranking(stage):
    roster = stage["inputs"]["inventor_roster"]["inventors"]
    ids = [entry["inventor_id"] for entry in roster]
    if ids != sorted(ids) or "alice" not in ids:
        raise RuntimeError("creative stage received a non-canonical Inventor roster")
    ordered = ["alice"] + [item for item in ids if item != "alice"]
    return [
        {
            "inventor_id": inventor_id,
            "rationale": (
                "Alice best preserves familiar draughts play while giving "
                "the exact Wish a structurally specific physical form."
                if inventor_id == "alice"
                else "%s is eligible, but its Taste fits this exact Wish less directly."
                % inventor_id.title()
            ),
        }
        for inventor_id in ordered
    ]


def invented_source(*, include_selection: bool) -> dict:
    value = {
        "concept": {
            "title": "Orbit Dog Draughts",
            "summary": (
                "A pocket draughts set whose orbital board and tactile dog-pack "
                "pieces preserve the familiar public-domain game."
            ),
            "signature_decision": (
                "Every playable square is an orbital waypoint while movement "
                "and capture rules remain unchanged."
            ),
            "intended_interaction": (
                "Two players move tactile pieces across the marked waypoints."
            ),
            "envelope_mm": {
                "length_mm": 60.0,
                "width_mm": 40.0,
                "height_mm": 4.0,
            },
            "components": [
                {
                    "key": "board",
                    "name": "Board",
                    "purpose": "playing surface",
                    "form": "single printable rounded block",
                    "dimensions_mm": {
                        "length_mm": 60.0,
                        "width_mm": 40.0,
                        "height_mm": 4.0,
                    },
                    "placement": "centered on the table",
                    "interfaces": "pieces rest on marked waypoints",
                }
            ],
            "assumptions": ["Players already know English draughts rules."],
            "unresolved_risks": [
                "Physical print feel and fit have not been tested by a person."
            ],
        },
        "research": {
            "rules_basis": "English draughts movement remains unchanged.",
            "sources": [
                {
                    "title": "World Draughts Federation",
                    "url": "https://www.fmjd.org/",
                    "use": "known-rule baseline",
                }
            ],
            "safety_boundary": "Ages 14+; small pieces require care.",
        },
    }
    if include_selection:
        value["selected_inventor_id"] = "alice"
    return value


def author_concept_source(root: Path, stage, authored: dict) -> None:
    """Author the exact five-file pre-render tree for marked Invent only."""

    inputs = stage["inputs"]
    concept_root = root / inputs["concept_root"]
    wish_bytes = (root / "WISH.json").read_bytes()
    wish = json.loads(wish_bytes)
    wish_sha256 = hashlib.sha256(wish_bytes).hexdigest()
    excerpt = "English draughts uses diagonal movement on a bounded board."
    excerpt_sha256 = hashlib.sha256(canonical_json(excerpt)).hexdigest()
    components = authored["concept"]["components"]
    brief = {
        "object": "orbit dog draughts set",
        "category": "tactile tabletop game",
        "envelope_mm": authored["concept"]["envelope_mm"],
        "wall_thickness_mm": 2.4,
        "print_stance": {
            "orientation": "board down",
            "supports_required": False,
            "support_notes": "The board and pieces use self-supporting profiles.",
        },
        "features": [
            {
                "id": "orbital-waypoints",
                "text": "Orbital waypoints preserve the familiar playable squares.",
            }
        ],
        "fit_target": {
            "target": "piece on waypoint",
            "dimensions_mm": {
                "length_mm": 8.0,
                "width_mm": 8.0,
                "height_mm": 3.0,
            },
            "clearance_mm": 0.3,
        },
        "components": components,
    }
    fields = (
        "object",
        "category",
        "envelope_mm",
        "wall_thickness_mm",
        "print_stance",
        "fit_target",
        "features.orbital-waypoints",
    ) + tuple("components.%s" % item["key"] for item in components)
    brief["facts"] = [
        {"field": field, "source_id": "source-1", "assumption_reason": None}
        for field in fields
    ]
    research = {
        "sources": [
            {
                "id": "source-1",
                "origin": "https://www.fmjd.org/",
                "excerpt": excerpt,
                "excerpt_sha256": excerpt_sha256,
                "retrieved_at": OBSERVED_AT,
            }
        ],
        "findings": [
            {
                "finding": "The familiar rules bound the board and piece relationship.",
                "source_ids": ["source-1"],
            }
        ],
    }
    prompts = {
        "presentation": "Neutral studio treatment at one stable scale.",
        "front": {
            "instruction": "Front view of the orbital board and tactile pieces.",
            "references": [],
        },
        "top": {
            "instruction": "Top view of the same orbital board.",
            "references": ["front"],
        },
        "bottom": {
            "instruction": "Bottom interface view of the same board.",
            "references": ["front"],
        },
        "exploded": {
            "instruction": "Exploded view separating the board and playing pieces.",
            "references": ["front", "top", "bottom"],
        },
        "components": {
            item["key"]: {
                "instruction": "%s alone with the same orbital finish." % item["name"],
                "references": ["front"],
            }
            for item in components
        },
    }
    descriptor = {
        "front": {"path": "images/front.png"},
        "top": {"path": "images/top.png"},
        "bottom": {"path": "images/bottom.png"},
        "exploded": {"path": "images/exploded.png"},
        "components": {
            item["key"]: {"path": "images/components/%s.png" % item["key"]}
            for item in components
        },
    }
    derived = {
        "schema_version": 1,
        "kind": "autonomous-workshop.concept-derived-wish",
        "wish_sha256": wish_sha256,
        "product_id": wish["product_id"],
        "objective": wish["objective"],
        "context": wish["context"],
        "constraints": {"envelope_mm": brief["envelope_mm"]},
    }
    derived["derived_wish_sha256"] = hashlib.sha256(
        canonical_json(derived)
    ).hexdigest()
    for name, value in (
        ("brief.json", brief),
        ("derived_wish.json", derived),
        ("descriptor.json", descriptor),
        ("prompts.json", prompts),
        ("research.json", research),
    ):
        write_json(concept_root / name, value)


def author_invent(root: Path, stage) -> None:
    assignment = stage["inputs"].get("assignment")
    if assignment is not None and assignment["selected_inventor_id"] != "alice":
        raise RuntimeError("Invent lost the accepted Match assignment")
    if (stage.get("round") or 0) > 1:
        inputs = stage["inputs"]
        for name in (
            "prior_assignment",
            "prior_invented",
            "failing_playtested",
            "feedback",
            "feedback_sha256",
        ):
            if name not in inputs:
                raise RuntimeError("re-Invent lost %s" % name)
    source = "authored/invent.json"
    authored = invented_source(include_selection=assignment is None)
    if assignment is None:
        authored["ranking"] = ranking(stage)
    scenario = stage["product_id"]
    if "invent-unavailable" in scenario:
        authored["selected_inventor_id"] = "not-on-the-roster"
    if "invent-ranking" in scenario:
        authored["ranking"] = authored["ranking"][:-1]
    if "invent-research" in scenario:
        authored.pop("research", None)
    if "invent-concept" in scenario:
        authored["concept"].pop("title", None)
    if "invent-physical" in scenario:
        authored["concept"].pop("intended_interaction", None)
    write_json(root / source, authored)
    arguments = ["invent", "--source", source]
    if "invent_concept_capability" in stage["inputs"]:
        author_concept_source(root, stage, authored)
        arguments.extend(("--concept-root", stage["inputs"]["concept_root"]))
    finalizer(root, *arguments)


def author_make(root: Path, stage) -> None:
    inputs = stage["inputs"]
    if "concept-tree-tamper" in stage["product_id"] and "sealed_concept" in inputs:
        concept_root = root / (
            "artifacts/concept/r%04d/concept"
            % inputs["sealed_concept"]["source"]["provenance"]["round"]
        )
        first_image = inputs["sealed_concept"]["image_manifest"]["entries"][0]["path"]
        target = concept_root / first_image
        target.write_bytes(target.read_bytes() + b"changed")
    creative_source = None
    if inputs.get("creative_source_required") is True:
        creative_source = "authored/spark-make.json"
        authored = invented_source(include_selection=True)
        authored["ranking"] = ranking(stage)
        write_json(root / creative_source, authored)
    product_root_value = inputs["product_root"]
    product_root = root / product_root_value
    if inputs.get("host_cad_gate_rejection") is not None:
        if product_root.exists():
            shutil.rmtree(product_root)
        rejected_contract = product_root.parent / "made.json"
        if rejected_contract.exists():
            rejected_contract.unlink()
    project = product_root / "cad/project"
    validation = product_root / "validation"
    project.mkdir(parents=True, exist_ok=True)
    validation.mkdir(parents=True, exist_ok=True)
    product = {
        "schema_version": 1,
        "product_id": stage["product_id"],
        "slug": stage["product_id"],
        "title": "Orbit Dog Draughts",
        "summary": "A compact printable orbital draughts set.",
        "description": "A Wish-specific familiar game invented by Alice.",
        "wish": json.loads((root / "WISH.json").read_text(encoding="utf-8")),
        "inventor": {"id": "alice", "name": "Alice"},
        "components": ["board"],
        "instructions": "Set up and play English draughts normally.",
        "limitations": [
            "Digitally verified; no claim of physical manufacture or delivery."
        ],
    }
    if "concept-component-mismatch" in stage["product_id"]:
        product["components"] = ["wrong-component"]
    write_json(product_root / "product.json", product)
    (product_root / "wish.json").write_bytes((root / "WISH.json").read_bytes())
    (product_root / "assembled.step").write_bytes(
        b"ISO-10303-21;\nHEADER;ENDSEC;\nDATA;ENDSEC;\nEND-ISO-10303-21;\n"
    )
    (product_root / "assembled.stl").write_bytes(tetrahedron_stl())
    render_path = project / "snap/iso.png"
    render_path.parent.mkdir(parents=True, exist_ok=True)
    render = Image.new("RGB", (900, 900), "#fff4df")
    pen = ImageDraw.Draw(render)
    pen.ellipse((150, 130, 750, 730), fill="#35aeb8")
    pen.polygon(((450, 190), (730, 720), (180, 720)), fill="#ff9f43")
    render.save(render_path, format="PNG")
    signature = Image.new("RGB", (1800, 900), "#fff4df")
    signature_pen = ImageDraw.Draw(signature)
    for offset, color in ((0, "#35aeb8"), (600, "#ffb445"), (1200, "#35aeb8")):
        signature_pen.ellipse((offset + 110, 160, offset + 490, 700), fill=color)
    signature.save(project / "snap/signature.png", format="PNG")
    if "concept-copied-pixels" in stage["product_id"] and "sealed_concept" in inputs:
        concept = inputs["sealed_concept"]
        concept_root = root / (
            "artifacts/concept/r%04d/concept" % concept["source"]["provenance"]["round"]
        )
        copied = concept["image_manifest"]["entries"][0]["path"]
        (product_root / "copied-concept.png").write_bytes(
            (concept_root / copied).read_bytes()
        )
    write_json(
        project / "snap/SIGNATURE-REVIEW.json",
        {
            "schema_version": 2,
            "kind": "autonomous-workshop.signature-experience-review",
            "iso_sha256": hashlib.sha256(render_path.read_bytes()).hexdigest(),
            "signature_sha256": hashlib.sha256(
                (project / "snap/signature.png").read_bytes()
            ).hexdigest(),
            "reviewer": "deterministic-independent-native-critic",
            "blind_held_read": "A compact orbital game board with tactile pieces.",
            "blind_signature_read": "Three exact states show a clear orbital play sequence.",
            "wish_revealed_after_blind_read": True,
            "held_object_unmistakable": True,
            "signature_experience_unmistakable": True,
            "finished_product_desirable": True,
            "largest_risk": "The three states could visually merge.",
            "resolution": "Contrasting separated panels preserve each exact state.",
        },
    )
    write_json(
        product_root / "assembled.step.json",
        {
            "schema_version": 1,
            "step_path": "assembled.step",
            "assembly": "Orbit Dog Draughts",
        },
    )
    reject_cad = (
        "cad-repair" in stage["product_id"]
        and inputs.get("host_cad_gate_rejection") is None
    )
    generator = (
        "from build123d import Box, Pos\n\n"
        "PRINTABLE = True\n\n"
        "def gen_step():\n"
        + (
            "    raise RuntimeError('deterministic authored CAD rejection')\n"
            if reject_cad
            else "    return Pos(0, 0, 2) * Box(60, 40, 4)\n"
        )
    )
    (project / "orbit_board.step.py").write_text(
        generator,
        encoding="utf-8",
    )
    write_json(
        validation / "cad-verification.json",
        {
            "schema_version": 1,
            "validator": "materialized-cad-final",
            "validator_version": "1.0.0",
            "passed": True,
            "checks": ["fresh-export", "strict-fit", "printable-mesh"],
            "final_pipeline": {"print_ready_claim": True},
        },
    )
    arguments = ["make"]
    if creative_source is not None:
        arguments.extend(("--source", creative_source))
    arguments.extend((
        "--product-root",
        product_root_value,
        "--cad-project-path",
        "cad/project",
        "--cad-verification-path",
        "validation/cad-verification.json",
    ))
    finalizer(root, *arguments)


def author_playtest(root: Path, stage) -> None:
    inputs = stage["inputs"]
    evidence_root_value = inputs["evidence_root"]
    evidence_root = root / evidence_root_value
    checks = []
    for check_id in inputs["required_check_ids"]:
        config_ref = "configs/%s.json" % check_id
        evidence_ref = "results/%s.json" % check_id
        product_artifact_sha256 = (
            "0" * 64
            if "playtest-stale-made" in stage["product_id"]
            else inputs["made"]["product_manifest"]["artifact_sha256"]
        )
        config = {
            "schema_version": 1,
            "check_id": check_id,
            "seed": 2718,
            "artifact_sha256": product_artifact_sha256,
        }
        if "playtest-conflicting-binding" in stage["product_id"]:
            config["product_artifact_sha256"] = "f" * 64
        if "playtest-rich-config" in stage["product_id"]:
            config = {
                "schema_version": 1,
                "check_id": check_id,
                "product_artifact_sha256": product_artifact_sha256,
                "subject_sha256": stage["subject_sha256"],
                "method": [
                    "Inspect the exact sealed Made bytes.",
                    "Preserve the deterministic configuration and result.",
                ],
                "inputs": {
                    "product.json": inputs["made"]["product_json_sha256"]
                },
            }
        write_json(evidence_root / config_ref, config)
        write_json(
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
                "evaluator": "deterministic-boundary-executable",
                "evaluator_version": "1.0.0",
                "config_ref": config_ref,
                "evidence_ref": evidence_ref,
                "observed_at": OBSERVED_AT,
                "observations": {
                    "evidence_class": "deterministic-digital-check",
                    "claims": ["The sealed revision passed %s." % check_id],
                    "artifact_bound": True,
                },
            }
        )
    repair = (
        "quest-repair" in stage["product_id"] and stage["round"] == 1
    ) or "playtest-over-budget" in stage["product_id"]
    invent_revision = (
        "quest-invent-revision" in stage["product_id"] and stage["round"] == 1
    )
    feedback = []
    verdict = "pass"
    if repair:
        verdict = "improve"
        feedback = [
            {
                "code": "waypoint-clearance",
                "area": "make",
                "severity": "block",
                "finding": "The first sealed revision needs clearer waypoint spacing.",
                "change": "Increase the waypoint clearance in the next Made revision.",
                "evidence_refs": [checks[0]["evidence_ref"]],
                "invalidates": ["playtest", "release"],
            }
        ]
    if invent_revision:
        verdict = "improve"
        feedback = [
            {
                "code": "concept-envelope",
                "area": "invent",
                "severity": "block",
                "finding": "The concept envelope needs a fundamental revision.",
                "change": "Revise the concept before rebuilding the Made artifact.",
                "evidence_refs": [checks[0]["evidence_ref"]],
                "invalidates": ["invent", "make", "playtest", "release"],
            }
        ]
    if "playtest-mismatched-verdict" in stage["product_id"]:
        verdict = "improve"
        feedback = []
    source = "authored/playtest.json"
    write_json(
        root / source,
        {"checks": checks, "feedback": feedback, "verdict": verdict},
    )
    if "playtest-missing-evidence" in stage["product_id"]:
        (evidence_root / checks[-1]["evidence_ref"]).unlink()
    finalizer(
        root,
        "playtest",
        "--source",
        source,
        "--evidence-root",
        evidence_root_value,
    )


def author_release(root: Path, stage) -> None:
    inputs = stage["inputs"]
    made = inputs["made"]
    package_root_value = inputs["package_root"]
    package = root / package_root_value
    package.mkdir(parents=True, exist_ok=True)
    if "release-corrupt-pdf" in stage["product_id"]:
        manual = b"not-a-pdf"
    elif "release-active-pdf" in stage["product_id"]:
        manual = manual_pdf().replace(
            b"/Type /Catalog", b"/Type /Catalog /OpenAction 2 0 R"
        )
    else:
        manual = manual_pdf()
    (package / "MANUAL.pdf").write_bytes(manual)
    if (
        inputs["release_contract"].get("manual_design_evidence_path")
        == "MANUAL-DESIGN.json"
    ):
        write_json(
            package / "MANUAL-DESIGN.json",
            manual_design_evidence(manual, made),
        )
    if inputs["release_contract"]["native_release_schema_version"] == 3:
        omission = {
            "schema_version": 1,
            "kind": "autonomous-workshop.playtest-omission",
            "status": "not-run",
            "reason": "Playtest is deferred for this Release.",
        }
        omission_sha256 = hashlib.sha256(canonical_json(omission)).hexdigest()
        write_json(package / "PLAYTEST-NOT-RUN.json", omission)
        direct_product = (
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
                "playtest_evidence_artifact_sha256": omission_sha256,
                "claims": {
                    "playtest": {
                        "status": "not-run",
                        "claims": [],
                        "evidence_ref": "PLAYTEST-NOT-RUN.json",
                        "evidence_sha256": omission_sha256,
                    }
                },
            }
        )
        if "release-false-claim" in stage["product_id"]:
            direct_product["claims"]["playtest"]["claims"] = [
                "The product was physically tested."
            ]
        write_json(
            package / "product.json",
            direct_product,
        )
        finalizer(root, "release", "--package-root", package_root_value)
        return

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
    write_json(
        package / "product.json",
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
    finalizer(root, "release", "--package-root", package_root_value)


AUTHORS = {
    "match": author_match,
    "invent": author_invent,
    "make": author_make,
    "playtest": author_playtest,
    "release": author_release,
}


def run() -> int:
    global _LAST_FINALIZER
    if "--version" in sys.argv[1:]:
        print("codex-cli 0.150.0")
        return 0
    arguments = sys.argv[1:]
    try:
        root = Path(arguments[arguments.index("-C") + 1]).resolve(strict=True)
    except (ValueError, IndexError, OSError) as exc:
        raise RuntimeError("deterministic runtime did not receive -C") from exc
    prompt = sys.stdin.read()
    forbidden = sorted(
        name
        for name in os.environ
        if name.startswith("FACTORY_")
        or name in {
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "WORKSHOP_CONCEPT_IMAGE_CREDENTIALS_FILE",
        }
    )
    if forbidden:
        raise RuntimeError("credentials reached native runtime: %s" % forbidden)
    stage = json.loads((root / "STAGE.json").read_text(encoding="utf-8"))
    stage_path = root / "STAGE.json"
    before = mutable_inventory(root)
    _LAST_FINALIZER = None
    emit({"type": "thread.started", "thread_id": THREAD_ID})
    emit(
        {
            "type": "item.completed",
            "item": {"id": "tool-1", "type": "command_execution"},
        }
    )
    AUTHORS[stage["stage"]](root, stage)
    product_id = stage["product_id"]
    if "stale-proposal" in product_id and stage["stage"] in {"invent", "make"}:
        outcome_path = root / "agent-outcome.json"
        outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
        outcome["checkpoint_sha256"] = "0" * 64
        outcome_path.write_bytes(canonical_json(outcome))
    if "artifact-tamper" in product_id and stage["stage"] == "make":
        product_path = root / stage["inputs"]["product_root"] / "product.json"
        product_path.write_bytes(product_path.read_bytes() + b"\n")
    if "invent-source-tamper" in product_id and stage["stage"] == "invent":
        source_path = (
            root / stage["inputs"]["contract_path"]
        ).parent / "source.json"
        source_path.write_bytes(source_path.read_bytes() + b"\n")
    if "playtest-evidence-tamper" in product_id and stage["stage"] == "playtest":
        evidence_root = root / stage["inputs"]["evidence_root"]
        target = sorted((evidence_root / "results").glob("*.json"))[0]
        target.write_bytes(target.read_bytes() + b"\n")
    if "release-package-tamper" in product_id and stage["stage"] == "release":
        product_path = root / stage["inputs"]["package_root"] / "product.json"
        product_path.write_bytes(product_path.read_bytes() + b"\n")
    after = mutable_inventory(root)
    writes = sorted(
        path for path, digest in after.items() if before.get(path) != digest
    )
    trace_path = root / "authored/runtime-trace.jsonl"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace = {
        "schema_version": 1,
        "kind": TRACE_KIND,
        "stage": stage["stage"],
        "checkpoint_sha256": stage["checkpoint_sha256"],
        "subject_sha256": stage["subject_sha256"],
        "stage_packet_sha256": hashlib.sha256(stage_path.read_bytes()).hexdigest(),
        "stage_read_only": not bool(stat.S_IMODE(stage_path.stat().st_mode) & 0o222),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "mode": "resume" if "resume" in arguments else "start",
        "resume": "resume" in arguments,
        "session_id": THREAD_ID,
        "argv": arguments,
        "source_paths": ["STAGE.json", "WISH.json"],
        "agent_writes": writes,
        "source_writes": [path for path in writes if path.startswith("authored/")],
        "finalizer_writes": [
            path
            for path in writes
            if path == "agent-outcome.json" or path.startswith("artifacts/")
        ],
        "workspace_before_sha256": inventory_sha256(before),
        "workspace_after_sha256": inventory_sha256(after),
        "finalizer": _LAST_FINALIZER,
        "forbidden_environment": forbidden,
        "forbidden_paths_visible": [
            path
            for path in ("host-state", ".env", "credentials/factory.env")
            if (root / path).exists()
        ],
    }
    with trace_path.open("ab") as stream:
        stream.write(canonical_json(trace) + b"\n")
    emit(
        {
            "type": "item.completed",
            "item": {
                "id": "message-1",
                "type": "agent_message",
                "text": "stage finalized",
            },
        }
    )
    emit({"type": "turn.completed", "usage": {}})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as error:
        try:
            argv = sys.argv[1:]
            debug_root = Path(argv[argv.index("-C") + 1]).resolve()
            write_json(
                debug_root / "authored/runtime-error.json",
                {"type": type(error).__name__, "message": str(error)},
            )
        except Exception:
            pass
        print("deterministic-codex: %s" % error, file=sys.stderr)
        raise
