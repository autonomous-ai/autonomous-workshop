#!/usr/bin/env python3
"""Deterministic STEP-first board-game CAD gate; writes <project>/gate.json."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Sequence

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"
CAD = ROOT / "skills" / "cad" / "scripts"
BUDGET = CAD / "with_budget"
BED_X_MM = 256.0
BED_Y_MM = 256.0
BED_Z_MM = 256.0
BED_MARGIN_MM = 5.0
BED = (BED_X_MM - 2 * BED_MARGIN_MM, BED_Y_MM - 2 * BED_MARGIN_MM,
       BED_Z_MM - BED_MARGIN_MM)
OVERHANG_FAIL_PCT = 50.0
BRIDGE_SPAN_MAX_MM = 25.0
MIN_BODY_VOLUME_MM3 = 20.0
MOVING_KINDS = {"slides", "turns", "rotates", "hinges", "moves"}


def python() -> str:
    return str(PYTHON if PYTHON.is_file() else Path(sys.executable))


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def closure_hash(project: Path, inputs: Sequence[Path | None]) -> tuple[str, list[dict]]:
    files = [
        path for path in project.rglob("*")
        if path.is_file() and path.suffix.lower() in {".py", ".json", ".md"}
        and not any(part in {"__cadgen__", "__pycache__", "preview", "reference"} for part in path.parts)
        and path.name not in {"gate.json", "ergonomics_check.json", ".cadgen-budget.json"}
    ]
    files.extend(path for path in inputs if path is not None and path.is_file())
    files.extend(path for path in (
        ROOT / "skills/cad/SKILL.md", ROOT / "skills/cad/requirements.txt", ROOT / "CAD.md"
    ) if path.is_file())
    digest = hashlib.sha256()
    records = []
    for path in sorted(set(item.resolve() for item in files), key=str):
        try:
            label = path.relative_to(ROOT).as_posix()
        except ValueError:
            label = str(path)
        hashed = file_hash(path)
        digest.update(label.encode())
        digest.update(hashed.encode())
        records.append({"path": label, "sha256": hashed})
    return digest.hexdigest(), records


def artifact(path: Path, source_hash: str) -> dict:
    return {
        "path": str(path.resolve()), "sha256": file_hash(path),
        "size": path.stat().st_size, "input_sha256": source_hash,
    }


def tail(text: str, size: int = 3000) -> str:
    return text[-size:]


class Runner:
    def __init__(self, project: Path) -> None:
        self.project = project
        self.commands: list[dict] = []
        self.environment = dict(os.environ)
        existing_pythonpath = self.environment.get("PYTHONPATH", "")
        self.environment["PYTHONPATH"] = str(project) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")

    def start(self) -> bool:
        result = subprocess.run(
            [python(), str(BUDGET), "--start", "--total", "30m", "--label", f"gate:{self.project.name}"],
            cwd=self.project, env=self.environment, capture_output=True, text=True, check=False,
        )
        self._record("budget:start", ["with_budget", "--start", "--total", "30m"], result, 0.0)
        return result.returncode == 0

    def run(self, name: str, argv: Sequence[str | Path], step: str = "10m") -> subprocess.CompletedProcess[str]:
        command = [str(item) for item in argv]
        started = time.perf_counter()
        result = subprocess.run(
            [python(), str(BUDGET), "--step", step, "--", *command], cwd=self.project,
            env=self.environment, capture_output=True, text=True, check=False,
        )
        self._record(name, command, result, time.perf_counter() - started)
        return result

    def _record(self, name: str, argv: list[str], result: subprocess.CompletedProcess[str], seconds: float) -> None:
        self.commands.append({
            "name": name, "argv": argv, "returncode": result.returncode,
            "ok": result.returncode == 0, "seconds": round(seconds, 3),
            "stdout": tail(result.stdout), "stderr": tail(result.stderr),
        })

    def report(self) -> dict:
        result = subprocess.run(
            [python(), str(BUDGET), "--report", "--json"], cwd=self.project,
            env=self.environment, capture_output=True, text=True, check=False,
        )
        report = {"ok": result.returncode == 0, "stdout": tail(result.stdout), "stderr": tail(result.stderr)}
        try:
            value = json.loads(result.stdout)
        except ValueError:
            value = None
        if isinstance(value, dict):
            report["ledger"] = value
        return report


def read_json(path: Path | None):
    if path is None or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def resolve_input(explicit: Path | None, project: Path, *names: str) -> Path | None:
    if explicit is not None:
        return explicit.resolve()
    for name in names:
        for base in (project, project.parent):
            candidate = base / name
            if candidate.is_file():
                return candidate.resolve()
    return None


def load_bill(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("components", raw) if isinstance(raw, dict) else raw
    result = []
    for row in rows if isinstance(rows, list) else []:
        name = str(row.get("name", "")).strip()
        qty = int(row.get("qty", row.get("quantity", 1)))
        if name and qty > 0:
            result.append({"name": name, "qty": qty})
    return result


def check_bill(bill: list[dict], names: list[str]) -> tuple[list[str], int]:
    findings = []
    unclaimed = set(names)
    for row in sorted(bill, key=lambda item: -len(item["name"])):
        name = row["name"]
        matched = {part for part in unclaimed if part == name or part.startswith(name + "_")}
        unclaimed -= matched
        if len(matched) != row["qty"]:
            findings.append(f"bill:{name}: rules need {row['qty']}, assembly names {len(matched)}")
    findings.extend(f"bill:{name}: part exists but no rule asks for it" for name in sorted(unclaimed))
    return findings, sum(row["qty"] for row in bill)


def assembly_names(project: Path, assembly: Path) -> list[str]:
    raw = read_json(project / "__cadgen__/models" / assembly.name / "assembly.json")
    rows = raw.get("occurrences", []) if isinstance(raw, dict) else []
    return [str(row.get("name", "")).strip() for row in rows if isinstance(row, dict) and row.get("name")]


def bridge_span(mesh) -> float:
    import networkx as nx
    import numpy as np
    down = np.where((mesh.face_normals[:, 2] < -0.95) & (mesh.triangles_center[:, 2] > mesh.bounds[0][2] + 3))[0]
    selected = set(down.tolist())
    graph = nx.Graph((a, b) for a, b in mesh.face_adjacency if a in selected and b in selected)
    graph.add_nodes_from(down.tolist())
    worst = 0.0
    for component in nx.connected_components(graph):
        faces = list(component)
        if mesh.area_faces[faces].sum() < 200:
            continue
        edges = np.sort(mesh.faces[faces][:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
        unique, counts = np.unique(edges, axis=0, return_counts=True)
        boundary = np.unique(unique[counts == 1])
        if not len(boundary):
            continue
        points = mesh.vertices[boundary][:, :2]
        centers = mesh.triangles_center[faces][:, :2]
        distances = np.sqrt(((centers[:, None, :] - points[None, :, :]) ** 2).sum(-1)).min(1)
        worst = max(worst, float(2 * distances.max()))
    return round(worst, 1)


ORIENTATIONS = (("as-modelled", 0, 0), ("flip-X", 180, 0), ("X-90", 90, 0),
                ("X+90", -90, 0), ("Y-90", 0, 90), ("Y+90", 0, -90))


def part_stats(path: Path) -> dict:
    import numpy as np
    import trimesh
    mesh = trimesh.load(str(path), force="mesh")
    bodies = max(1, len([body for body in mesh.split(only_watertight=False) if abs(body.volume) >= MIN_BODY_VOLUME_MM3]))
    choices = []
    for label, rx, ry in ORIENTATIONS:
        candidate = mesh.copy()
        if rx:
            candidate.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rx), [1, 0, 0]))
        if ry:
            candidate.apply_transform(trimesh.transformations.rotation_matrix(np.radians(ry), [0, 1, 0]))
        areas = candidate.area_faces
        overhang = float(areas[candidate.face_normals[:, 2] < -0.7071].sum() / areas.sum() * 100) if areas.sum() else 0.0
        bridge = bridge_span(candidate)
        choices.append(((bridge > BRIDGE_SPAN_MAX_MM or overhang > OVERHANG_FAIL_PCT, bridge, overhang), label, round(overhang, 2), bridge))
    _, orientation, overhang, bridge = min(choices, key=lambda row: row[0])
    return {
        "watertight": bool(mesh.is_watertight), "bodies": bodies,
        "volume_mm3": round(float(abs(mesh.volume)), 2),
        "bbox_mm": [round(float(value), 1) for value in np.ptp(mesh.bounds, axis=0).tolist()],
        "print_orientation": orientation, "overhang_pct": overhang, "bridge_span_mm": bridge,
    }


def slice_stl(path: Path) -> dict:
    cli = os.environ.get("ORCASLICER_CLI", "").strip()
    profile = os.environ.get("ORCA_PROFILE", "").strip()
    if not cli or not profile:
        return {"sliced": None}
    profiles = [item.strip() for item in profile.split(";") if item.strip()]
    if len(profiles) != 3:
        return {"sliced": False, "error": "ORCA_PROFILE needs machine;process;filament"}
    with tempfile.TemporaryDirectory() as folder:
        result = subprocess.run(
            [cli, "--load-settings", f"{profiles[0]};{profiles[1]}", "--load-filaments", profiles[2],
             "--slice", "0", "--outputdir", folder, str(path)],
            capture_output=True, text=True, timeout=300, check=False,
        )
        gcodes = sorted(Path(folder).glob("*.gcode"))
        if result.returncode != 0 or not gcodes:
            return {"sliced": False, "error": tail(result.stderr or result.stdout, 300)}
        header = gcodes[0].read_text(encoding="utf-8", errors="ignore")[:16000]
        output = {"sliced": True, "print_min": None, "filament_g": None}
        match = re.search(r"(?:estimated printing time.*?=|total estimated time:)\s*(?:(\d+)h)?\s*(?:(\d+)m)?", header, re.I)
        if match:
            output["print_min"] = int(match.group(1) or 0) * 60 + int(match.group(2) or 0)
        match = re.search(r"(?:filament used \[g\]\s*=|total filament weight \[g\]\s*:)\s*([\d.]+)", header, re.I)
        if match:
            output["filament_g"] = float(match.group(1))
        return output


def missing_motion(brief, motion: Path | None) -> list[str]:
    if not isinstance(brief, dict):
        return []
    moving = {str(row.get("piece", "")).strip() for row in brief.get("interfaces", [])
              if isinstance(row, dict) and str(row.get("kind", "")).lower() in MOVING_KINDS}
    raw = read_json(motion)
    text = json.dumps(raw) if isinstance(raw, dict) else ""
    return sorted(name for name in moving if name and name not in text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--bill", type=Path)
    parser.add_argument("--brief", type=Path)
    parser.add_argument("--motion-manifest", type=Path)
    parser.add_argument("--no-slice", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    if not project.is_dir():
        print('GATE FAIL {"fails":["project must be a directory"]}')
        return 1

    out = args.out.resolve() if args.out else project / "gate.json"
    brief_path = resolve_input(args.brief, project, "brief.json")
    bill_path = resolve_input(args.bill, project, "bill.json")
    motion_path = resolve_input(args.motion_manifest, project, "measure/motion.json", "motion.json")
    brief = read_json(brief_path)
    source_hash, closure = closure_hash(project, (brief_path, bill_path, motion_path))
    report = {"project": str(project), "source_sha256": source_hash, "source_closure": closure,
              "bed_usable_mm": list(BED), "artifacts": {}}
    fails: list[str] = []
    unmeasured: list[str] = []

    previous = read_json(out)
    cache = project / "__cadgen__"
    changed = isinstance(previous, dict) and previous.get("source_sha256") != source_hash
    if changed and cache.exists():
        shutil.rmtree(cache)
    report["cache"] = {"invalidated": bool(changed), "reason": "source closure changed" if changed else None}

    entries = sorted(project.glob("*.step.py"))
    assemblies = [path for path in entries if not path.name.startswith("part_")]
    parts = [path for path in entries if path.name.startswith("part_")]
    if len(assemblies) != 1 or not parts:
        fails.append(f"layout: expected one assembly and printable part entries, found {len(assemblies)} and {len(parts)}")
    assembly = assemblies[0] if len(assemblies) == 1 else None

    runner = Runner(project)
    if not runner.start():
        fails.append("budget: could not start the shared ledger")

    def run(name: str, command: Sequence[str | Path], step: str = "10m"):
        result = runner.run(name, command, step)
        if result.returncode:
            detail = tail(result.stderr or result.stdout, 500).replace("\n", " ").strip()
            fails.append(f"{name}: {detail or f'exit {result.returncode}'}")
        return result

    run("layout", [python(), CAD / "check_layout", "."])
    if brief_path is None:
        fails.append("ergonomics: brief.json is missing")
    else:
        run("ergonomics", [python(), HERE / "ergonomics_check.py", brief_path,
                           "--out", project / "ergonomics_check.json"])

    if assembly is not None and parts:
        run("generation", [python(), CAD / "gen", assembly.name, *[part.name for part in parts], "--write", "--json"])
        run("topology", [python(), CAD / "inspect", "refs", assembly.name, "--facts", "--planes", "--positioning", "--format", "json"])
        for entry in (assembly, *parts):
            run(f"validity:{entry.stem}", [python(), CAD / "inspect", "validate", entry.name])
        run("interference", [python(), CAD / "inspect", "interfere", assembly.name])
        run("bed-fit", [python(), CAD / "check_fit", ".", "--bed", str(BED[0]), str(BED[1]), "--strict", "--json"])
        local_fit = project / "measure/check_fit.py"
        if local_fit.is_file():
            run("source-fit", [python(), local_fit])
        else:
            unmeasured.append("source-fit: measure/check_fit.py is absent")

        for name in missing_motion(brief, motion_path):
            fails.append(f"motion:{name}: declared moving in brief but absent from motion manifest")
        if motion_path is not None:
            run("motion", [python(), CAD / "check_motion", ".", "--manifest", motion_path, "--json"])
        elif isinstance(brief, dict) and brief.get("interfaces"):
            fails.append("motion: brief declares interfaces but no motion manifest exists")

        assembly_step = assembly.with_suffix("")
        run("export:assembly", [python(), CAD / "export", assembly_step, "--glb", "--json"])
        glb = assembly_step.with_suffix(".glb")
        if glb.is_file():
            report["artifacts"]["assembly_glb"] = artifact(glb, source_hash)
        else:
            fails.append("artifact: assembly GLB missing")

        plan = brief.get("print_plan", {}) if isinstance(brief, dict) else {}
        nozzle = float(plan.get("nozzle_mm", 0.4))
        min_wall = float(plan.get("min_wall_mm", 2 * nozzle))
        part_reports = {}
        distinct = {}
        for entry in parts:
            name = entry.name.removeprefix("part_").removesuffix(".step.py")
            step_path = entry.with_suffix("")
            stl = step_path.with_suffix(".stl")
            run(f"export:{name}", [python(), CAD / "export", step_path, "--stl", "--json"])
            run(f"mesh:{name}", [python(), CAD / "check_mesh", stl, "--bed", "246x246x251"])
            run(f"thickness:{name}", [python(), CAD / "check_thickness", stl, "--nozzle", str(nozzle), "--min-wall", str(min_wall)], "15m")
            if not stl.is_file():
                fails.append(f"artifact:{name}: STL missing")
                continue
            report["artifacts"][f"part:{name}"] = artifact(stl, source_hash)
            stats = part_stats(stl)
            part_reports[name] = stats
            if stats["bodies"] != 1:
                fails.append(f"pieces:{name}: {stats['bodies']} disconnected bodies")
            if not stats["watertight"]:
                fails.append(f"watertight:{name}: mesh is not closed")
            if stats["overhang_pct"] > OVERHANG_FAIL_PCT:
                fails.append(f"overhang:{name}: {stats['overhang_pct']}% exceeds {OVERHANG_FAIL_PCT}%")
            if stats["bridge_span_mm"] > BRIDGE_SPAN_MAX_MM:
                fails.append(f"bridge:{name}: {stats['bridge_span_mm']}mm exceeds {BRIDGE_SPAN_MAX_MM}mm")
            distinct.setdefault(f"{stats['volume_mm3']}|{stats['bbox_mm']}", (name, stl))
        report["parts"] = part_reports
        report["distinct_shapes"] = len(distinct)

        slices = {}
        if args.no_slice:
            unmeasured.append("slice: --no-slice, so print time and material are unknown")
        else:
            for name, stl in distinct.values():
                result = slice_stl(stl)
                slices[name] = result
                if result.get("sliced") is False:
                    fails.append(f"slice:{name}: {result.get('error', 'slicer failed')}")
            if slices and any(item.get("sliced") is None for item in slices.values()):
                unmeasured.append("slice: no ORCASLICER_CLI/ORCA_PROFILE configured; print time and material are unknown")
        report["slice"] = slices

        names = assembly_names(project, assembly)
        report["part_count"] = len(names)
        if bill_path is None:
            unmeasured.append("bill: no component bill was supplied")
        else:
            bill = load_bill(bill_path)
            findings, expected = check_bill(bill, names)
            fails.extend(findings)
            report["bill"] = {"expected_total": expected, "actual_total": len(names), "findings": findings}
        for entry in (assembly, *parts):
            step_path = entry.with_suffix("")
            if step_path.is_file():
                report["artifacts"][f"step:{entry.stem}"] = artifact(step_path, source_hash)
            else:
                fails.append(f"artifact:{entry.name}: STEP missing")

    report["budget"] = runner.report()
    report["commands"] = runner.commands
    report["pass"] = not fails
    report["fails"] = fails
    report["unmeasured"] = unmeasured
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary = {"parts": report.get("part_count", 0), "distinct_shapes": report.get("distinct_shapes", 0), "fails": fails}
    if unmeasured:
        summary["unmeasured"] = unmeasured
    print(("GATE PASS " if report["pass"] else "GATE FAIL ") + json.dumps(summary))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
