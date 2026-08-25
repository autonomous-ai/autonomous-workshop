"""Bridge between the text2game pipeline and Pip's Workshop seams.

text2game is an operator-run pipeline (game design -> build123d CAD ->
contract gate -> AI referee -> slicing) whose completed runs live under
``<TEXT2GAME_ROOT>/out/<slug>/``. Pip's Make adopts the run whose slug equals
the Wish ``product_id`` and imports its files as the product artifact; Pip's
Playtest binds the same run's recorded verdicts as evidence. The bridge never
invents results: anything the run cannot prove becomes a typed wait.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PIPELINE_ROOT_ENV = "TEXT2GAME_ROOT"
DEFAULT_PIPELINE_ROOT = "/root/text2game"
BRIDGE_VERSION = "1.0.0"
LANE = "invented-games"

_SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")

# Files a run must have before Make can import a product from it.
PRODUCT_FILES = (
    "gdd.md",
    "components.json",
    "rulebook.md",
    "parts_index.json",
    "part_colors.json",
    "assembled.step",
)
# Recorded verdicts Playtest binds as evidence.
EVIDENCE_FILES = (
    "phase1.json",
    "referee.md",
    "evaluate.json",
    "gate.json",
    "fit.json",
    "slice_report.json",
)
OPTIONAL_EVIDENCE_FILES = ("critic.json", "print_kit.md")
# A mass seeded-game simulation, when text2game grows one (>=1000 games).
SIMULATION_FILE = "game_simulation.json"


def pipeline_root() -> Path:
    return Path(os.environ.get(PIPELINE_ROOT_ENV, DEFAULT_PIPELINE_ROOT))


def pipeline_present(root: Path) -> bool:
    return (root / "text2game").is_file()


def run_dir(root: Path, slug: str) -> Optional[Path]:
    if not _SLUG.match(slug):
        return None
    return root / "out" / slug


def missing_product_files(run: Path) -> List[str]:
    missing = [name for name in PRODUCT_FILES if not (run / name).is_file()]
    if not list(run.glob("parts/*.py")):
        missing.append("parts/*.py")
    if not list(run.glob("fe_parts/*.stl")):
        missing.append("fe_parts/*.stl")
    return missing


def missing_evidence_files(run: Path) -> List[str]:
    return [name for name in EVIDENCE_FILES if not (run / name).is_file()]


def load_json(run: Path, name: str) -> Optional[Any]:
    try:
        with (run / name).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def _copy(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)


def import_product(run: Path, artifact_root: Path) -> Dict[str, int]:
    """Copy the curated product tree (rules, source, CAD, meshes, assembly).

    Slicing gcode and pipeline logs stay behind: they are evidence and ops
    material, not the product a customer's kit is built from.
    """

    plan = {
        "gdd.md": "rules/gdd.md",
        "rulebook.md": "rules/rulebook.md",
        "components.json": "rules/components.json",
        "assembled.step": "cad/assembled.step",
        "parts_index.json": "assembly/parts_index.json",
        "part_colors.json": "assembly/part_colors.json",
        "stage.json": "assembly/stage.json",
        "art_direction.md": "assembly/art_direction.md",
        "export_all.py": "source/export_all.py",
        "plates.json": "print/plates.json",
        "print_kit.md": "print/print_kit.md",
    }
    optional = {"stage.json", "art_direction.md", "export_all.py", "plates.json", "print_kit.md"}
    for source_name, dest_name in plan.items():
        source = run / source_name
        if not source.is_file():
            if source_name in optional:
                continue
            raise FileNotFoundError(source_name)
        _copy(source, artifact_root / dest_name)
    part_sources = sorted(run.glob("parts/*.py"))
    for source in part_sources:
        _copy(source, artifact_root / "source" / "parts" / source.name)
    mesh_sources = sorted(run.glob("fe_parts/*.stl"))
    for source in mesh_sources:
        _copy(source, artifact_root / "mesh" / source.name)
    return {"part_sources": len(part_sources), "meshes": len(mesh_sources)}


def title_and_summary(run: Path, fallback_objective: str) -> Tuple[str, str]:
    title = ""
    summary = ""
    try:
        for line in (run / "gdd.md").read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not title and stripped.startswith("# "):
                title = stripped[2:].strip()
            if not summary and stripped.startswith("**Box face:**"):
                summary = stripped[len("**Box face:**"):].strip()
            if title and summary:
                break
    except OSError:
        pass
    if not title:
        title = run.name.replace("-", " ").title()
    if not summary:
        summary = fallback_objective.strip()[:280]
    return title, summary


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def config_sha256(config: Dict[str, Any]) -> str:
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def copy_evidence(run: Path, workspace: Path) -> None:
    for name in EVIDENCE_FILES + OPTIONAL_EVIDENCE_FILES + (SIMULATION_FILE,):
        source = run / name
        if source.is_file():
            _copy(source, workspace / name)


def referee_verdict(phase1: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Did the pipeline's own design loop accept a round of this game?

    Pip's referee bar is deliberately asymptotic: after the allowed passes,
    open findings become table notes rather than another revision. Acceptance
    therefore means the referee actually ran and a round was kept — the open
    findings still ride along in the evidence and as note feedback.
    """

    referee_ran = phase1.get("referee_missing") is False
    kept = phase1.get("kept_round")
    passed = referee_ran and isinstance(kept, int)
    evidence = {
        "evidence_class": "ai-simulation",
        "agent_roles": ["referee-player", "critic", "evaluator"],
        "rounds": phase1.get("round"),
        "exit": phase1.get("exit"),
        "kept_round": kept,
        "referee_clean": bool(phase1.get("referee_clean")),
        "critic_high": phase1.get("critic_high"),
        "scores": phase1.get("evaluate") or {},
    }
    return passed, evidence


def gate_verdict(
    gate: Dict[str, Any], fit: List[Dict[str, Any]]
) -> Tuple[bool, Dict[str, Any], List[Dict[str, Any]]]:
    parts = gate.get("parts") or {}
    watertight = [
        name
        for name, record in parts.items()
        if record.get("watertight") is True and record.get("bodies") == 1
    ]
    fit_high = [item for item in fit if item.get("severity") == "high"]
    fit_warn = [item for item in fit if item.get("severity") == "warn"]
    passed = bool(parts) and len(watertight) == len(parts) and not fit_high
    evidence = {
        "evidence_class": "ai-simulation",
        "method": "cad-kernel-measurement",
        "parts_measured": len(parts),
        "watertight_single_body_parts": len(watertight),
        "fit_high": len(fit_high),
        "fit_warn": len(fit_warn),
    }
    return passed, evidence, fit_high


def slice_verdict(report: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    parts = report.get("parts") or []
    sliced = [
        item
        for item in parts
        if isinstance(item.get("grams_each"), (int, float))
        and isinstance(item.get("seconds_each"), int)
    ]
    passed = bool(parts) and len(sliced) == len(parts)
    evidence = {
        "evidence_class": "ai-simulation",
        "method": "slicer-analysis",
        "slicer_profile": "petg",
        "parts_sliced": len(sliced),
        "parts_total": len(parts),
        "grams_total": round(sum(item.get("grams_total") or 0 for item in sliced), 1),
        "seconds_total": sum(item.get("seconds_total") or 0 for item in sliced),
    }
    return passed, evidence


def simulation_verdict(run: Path) -> Optional[Tuple[bool, Dict[str, Any]]]:
    """Adopt a mass seeded-game simulation only when one truly exists."""

    record = load_json(run, SIMULATION_FILE)
    if not isinstance(record, dict):
        return None
    evidence = dict(record)
    evidence.setdefault("evidence_class", "ai-simulation")
    passed = record.get("passed") is True
    return passed, evidence
