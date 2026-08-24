"""Credential-free Workshop pieces used by generated inventor starters.

These deterministic adapters prove that Taste -> Make -> Playtest is wired
correctly. They deliberately do not claim to generate production CAD or
replace real AI-agent, model, slicer, or independent-review capabilities.
Physical production and hands-on QA belong to Deliver.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .cad import (
    CadPart,
    CadProjectManifest,
    CadReleaseBundle,
    PhysicalClaim,
    ValidatorRequirement,
    VerificationCheck,
    VerificationReceipt,
)
from .make import CadBuildResult, Workbench
from .models import InspectionResult


_CONFIG_SHA256 = hashlib.sha256(b"workshop-offline-workshop-v1").hexdigest()
_PROFILE_SHA256 = hashlib.sha256(b"offline-fdm-profile-v1").hexdigest()
_SKILL_SHA256 = hashlib.sha256(b"offline-starter-skill-v1").hexdigest()
_CHECKS = {
    "deterministic": {
        "manifest": {"inventory_valid": True},
        "brep": {"valid_solids": 1, "invalid_solids": 0},
        "mesh-topology": {"watertight_parts": 1, "non_manifold_edges": 0},
        "dimensions": {"measured_parts": 1, "out_of_tolerance": 0},
        "interference": {"poses_tested": 1, "forbidden_intersections": 0},
        "bed-packing": {"beds_used": 1, "out_of_bounds_parts": 0},
        "slicer": {
            "profiles_checked": 1,
            "slicer_errors": 0,
            "support_material_grams": 0.0,
        },
    },
    "independent-review": {
        "form-review": {"views_reviewed": 3, "blockers": 0},
        "safety": {"hazards_found": 0, "review_scope": "offline starter only"},
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OfflineMuse:
    """A deterministic stand-in that proves the inventor's Taste is bound."""

    def run(
        self,
        role: str,
        request: Mapping[str, Any],
        budget_micros: int,
    ) -> Mapping[str, Any]:
        brief = request["wish"]
        taste = request["taste"]
        return {
            "title": "%s workshop concept" % brief["product_id"].replace("-", " ").title(),
            "objective": brief["objective"],
            "role": role,
            "taste_sha256": taste["sha256"],
            "offline": True,
        }


class OfflineMaker:
    """Writes a tiny deterministic artifact; it is not production CAD."""

    def build(self, brief, concept, workspace: Path) -> CadBuildResult:
        artifact = workspace / "artifact"
        parts = artifact / "parts"
        evidence = artifact / "evidence"
        parts.mkdir(parents=True)
        evidence.mkdir()
        (parts / "sample-piece.step.py").write_text(
            "# Offline workshop placeholder; replace with a real CAD adapter.\n",
            encoding="utf-8",
        )
        (parts / "sample-piece.step").write_bytes(
            b"ISO-10303-21;\n/* OFFLINE WORKSHOP PLACEHOLDER */\nEND-ISO-10303-21;\n"
        )
        (parts / "sample-piece.stl").write_bytes(
            b"solid offline-sample\nendsolid offline-sample\n"
        )
        (artifact / "concept.json").write_text(
            json.dumps(dict(concept), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        for checks in _CHECKS.values():
            for check_id, measurements in checks.items():
                (evidence / (check_id + ".json")).write_text(
                    json.dumps(measurements, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
        (evidence / "workshop.json").write_text(
            json.dumps(
                {"offline": True, "taste_bound": True}, sort_keys=True
            )
            + "\n",
            encoding="utf-8",
        )
        return CadBuildResult(
            1,
            brief.product_id,
            artifact.resolve(),
            {"adapter": "workshop-offline-workshop", "production_ready": False},
        )


class OfflineInspector:
    """Compatibility adapter that emits synthetic digital Playtest contracts.

    It never represents a print, hands-on QA, or customer observation; those
    facts belong to Deliver and Reviews.
    """

    def verify(self, artifact_root: Path, artifact_sha256: str) -> CadReleaseBundle:
        evidence_files = {
            "evidence/%s.json" % check_id: _sha256(
                artifact_root / "evidence" / (check_id + ".json")
            )
            for checks in _CHECKS.values()
            for check_id in checks
        }
        manifest = CadProjectManifest(
            schema_version=1,
            project_id=artifact_root.parent.name,
            artifact_sha256=artifact_sha256,
            engine={"name": "workshop-offline-workshop", "version": "1.0.0"},
            skill_versions={"workshop": _SKILL_SHA256},
            parts=(
                CadPart(
                    "sample-piece",
                    "Offline sample piece",
                    1,
                    "parts/sample-piece.step.py",
                    "parts/sample-piece.step",
                    "parts/sample-piece.stl",
                    "PLA",
                    (0, 0, 0),
                ),
            ),
            assemblies=(),
            fits=(),
            motions=(),
            print_profile={"process": "FDM", "profile_sha256": _PROFILE_SHA256},
            evidence_files=evidence_files,
            physical_claims=(
                PhysicalClaim(
                    "production-readiness",
                    "A real adapter, slicer, review, and print test are still required",
                    False,
                    "held",
                ),
            ),
        )
        requirements = []
        receipts = []
        for substrate, checks in _CHECKS.items():
            validator = "offline-%s" % substrate
            requirements.append(
                ValidatorRequirement(
                    validator,
                    "1.0.0",
                    _CONFIG_SHA256,
                    substrate,
                    tuple(checks),
                )
            )
            receipts.append(
                VerificationReceipt.create(
                    artifact_sha256,
                    validator,
                    "1.0.0",
                    _CONFIG_SHA256,
                    substrate,
                    tuple(
                        VerificationCheck(
                            check_id,
                            "passed",
                            measurements,
                            "evidence/%s.json" % check_id,
                            evidence_files["evidence/%s.json" % check_id],
                        )
                        for check_id, measurements in checks.items()
                    ),
                )
            )
        return CadReleaseBundle(manifest, tuple(receipts), tuple(requirements))

    def inspect(self, artifact_root: Path, artifact_sha256: str):
        evidence = artifact_root / "evidence/workshop.json"
        return (
            InspectionResult.create(
                "workshop-starter",
                True,
                artifact_sha256,
                {"offline": True, "production_ready": False},
                "workshop-offline-workshop",
                "1.0.0",
                _CONFIG_SHA256,
                "evidence/workshop.json",
                _sha256(evidence),
            ),
        )

    def evaluate(self, artifact_root: Path, artifact_sha256: str):
        """Compatibility spelling used by Workshop 0.2 Workbench adapters."""

        return self.inspect(artifact_root, artifact_sha256)


def offline_workbench() -> Workbench:
    """Return the credential-free Workbench used by generated ``make`` commands."""

    inspector = OfflineInspector()
    return Workbench(OfflineMuse(), OfflineMaker(), inspector, inspector)


__all__ = [
    "OfflineMaker",
    "OfflineMuse",
    "OfflineInspector",
    "OfflineProvingGround",
    "offline_forge",
    "offline_workbench",
]

OfflineProvingGround = OfflineInspector
offline_forge = offline_workbench
