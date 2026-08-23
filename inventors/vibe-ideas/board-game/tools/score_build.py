#!/usr/bin/env python3
"""score_build.py — run the DETERMINISTIC half of a build's fidelity check.

Given a captured build stage (see cad_session.py capture) and the idea's
ranked `must_survive` list, this:

  1. finds the assembled STL and part STLs in the downloaded CAD project;
  2. splits the assembly into connected-component bodies
     (evaluate-cad-reconstruction's extract_placed_instances) — this is what
     detects fusion, the failure mode that destroyed turns 11-13;
  3. compiles a `physical_conditions.json` from every `must_survive` entry
     that declared a `geometric` check;
  4. runs the printability and physical-correctness scorers;
  5. renders orthographic/iso views of each STEP for the visual check;
  6. writes `evaluation_report.json` — rank-weighted geometric fidelity plus
     the raw scorer output.

Why this is a script and not part of the evaluator agent: whoever produces a
number must not be the one who reports it. The evaluator consumes this file;
it cannot fabricate a component count. Everything here is reproducible from
the frozen artifacts, so an archived turn can be re-scored later against a
changed rubric — which is the whole reason full projects are archived.

The printability score here is DELIBERATELY a second opinion, independent of
the pipeline's own `review_fix.printability`. That number gave a fused,
featureless blob 8.97/10 in turn 13, because a single solid really is
trivially printable. A high printability score next to a failed component
count is not a contradiction — it is the fusion signature.

Usage:
    python3 board-game/tools/score_build.py --turn 14 --idea-id 1 --stage first-shot
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKILL_ROOT = REPO_ROOT / "evaluate-cad-reconstruction"
_WORKER_SERVICE = "worker"
_WORKER_INDEX = 1  # pin every compose call to one replica (see generate_cad_builds.py)

# Rank 1 is the feature whose loss makes the object pointless; rank 5 is the
# least load-bearing. Weights are linear rather than steep on purpose: a
# steeper curve would make it profitable to bury a risky feature at rank 5.
_RANK_WEIGHT = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}
_STATUS_CREDIT = {"pass": 1.0, "inconclusive": 0.5, "fail": 0.0}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run(args: list[str], timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


# --------------------------------------------------------------------------
# Locating geometry in the downloaded project


def find_geometry(project_dir: Path) -> tuple[Path | None, list[Path], list[Path]]:
    """Return (assembly_stl, part_stls, step_files).

    Snapshots vary in layout, so this prefers explicit naming and falls back
    to "the biggest STL is the assembly" rather than guessing a fixed path."""
    stls = sorted(p for p in project_dir.rglob("*.stl") if p.is_file())
    steps = sorted(p for p in project_dir.rglob("*.ste*p") if p.is_file())
    if not stls:
        return None, [], steps

    named = [p for p in stls if p.stem.lower() in {"main", "assembly", "assembled"}]
    if not named:
        named = [p for p in stls if "assembl" in p.stem.lower()]
    assembly = named[0] if named else max(stls, key=lambda p: p.stat().st_size)
    parts = [p for p in stls if p != assembly]
    return assembly, parts, steps


# --------------------------------------------------------------------------
# Condition manifest


def compile_conditions(must_survive: list[dict], bindings: dict, assembly_rel: str) -> tuple[dict, list[dict]]:
    """Turn the ideator's ranked `must_survive` list into a runnable condition
    manifest. Each entry that declared a `geometric` block becomes one
    condition, id'd `ms<rank>` so results map straight back to the ranking.

    Entries whose geometric inputs name a part we could not bind to real
    geometry are recorded as unbindable rather than silently dropped — a part
    with no matching body in the build is itself a finding (that is exactly
    what "the trick tray is entirely absent" looks like from here)."""
    conditions: list[dict] = []
    unbindable: list[dict] = []
    part_names = set(bindings)

    for entry in must_survive:
        geometric = entry.get("geometric")
        rank = entry.get("rank")
        if not geometric:
            continue
        inputs = geometric.get("inputs") or {}
        # Part references appear under several input key spellings across the
        # check vocabulary — part_a/part_b, moving_part/obstacle_part, part.
        # `part_name_prefix` is not one of these: it is a prefix pattern that
        # _check_feature_count matches against bindings with startswith(), so
        # it is never itself a literal binding key and must not be checked
        # for exact membership the way part_a/part_b are.
        referenced = {
            v for k, v in inputs.items()
            if isinstance(v, str) and "part" in k and k != "part_name_prefix"
        }
        missing = sorted(referenced - part_names)
        prefix = inputs.get("part_name_prefix")
        if prefix and not any(name.startswith(prefix) for name in part_names):
            missing.append(prefix)
        if missing:
            unbindable.append({"rank": rank, "feature": entry.get("feature"), "missing_parts": sorted(missing)})
            continue
        conditions.append(
            {
                "id": f"ms{rank}",
                "category": geometric.get("category", "separation_correctness"),
                "severity": geometric.get("severity", "major"),
                "check": geometric["check"],
                "description": entry.get("feature", ""),
                "inputs": geometric.get("inputs", {}),
                "thresholds": geometric.get("thresholds", {}),
            }
        )

    manifest = {"assembly": assembly_rel, "parts": bindings, "conditions": conditions}
    return manifest, unbindable


# --------------------------------------------------------------------------
# Renders (best effort)


def render_steps(steps: list[Path], out_dir: Path, compose_file: Path | None) -> tuple[list[str], str | None]:
    """Render each STEP to 6 iso + 6 ortho views for the visual check.

    render_views.py needs a working cadquery+VTK. The host's cadquery import
    is currently broken (nptyping touches numpy.bool8, removed in numpy 2.x),
    so this shells into the worker container — the same trick
    generate_cad_builds.py uses for ai_thumbnail. Entirely best-effort: the
    pipeline's own qa.png already provides multi-angle views, so a render
    failure degrades the visual check's resolution rather than blocking it.

    Note the renders are monochrome grey by construction. That is fine — this
    pipeline has no colour assignment step at all, so nothing downstream
    judges colour."""
    script = DEFAULT_SKILL_ROOT / "scripts" / "render_views.py"
    if not script.exists():
        return [], f"render_views.py not found at {script}"
    if not steps:
        return [], "no STEP files in the project snapshot"

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    local = _run([sys.executable, "-c", "import cadquery"], timeout=120)
    if local.returncode == 0:
        for step in steps:
            prefix = out_dir / step.stem
            proc = _run([sys.executable, str(script), str(step), str(prefix)], timeout=900)
            if proc.returncode != 0:
                return written, f"render_views failed on {step.name}: {(proc.stderr or proc.stdout)[:300]}"
            written.extend(sorted(p.name for p in out_dir.glob(f"{step.stem}_*.png")))
        return written, None

    if not compose_file or not compose_file.exists():
        return [], ("cadquery unusable on this host and no docker compose file found — "
                    "pass --compose-file to render inside the worker container")

    def _compose(*args: str) -> list[str]:
        return ["docker", "compose", "-f", str(compose_file), *args]

    cp = _run(_compose("cp", "--index", str(_WORKER_INDEX), str(script), f"{_WORKER_SERVICE}:/tmp/render_views.py"))
    if cp.returncode != 0:
        return [], f"docker cp (render_views.py) failed: {cp.stderr[:300]}"

    for step in steps:
        remote_step = f"/tmp/{step.name}"
        remote_prefix = f"/tmp/render-{step.stem}"
        if _run(_compose("cp", "--index", str(_WORKER_INDEX), str(step), f"{_WORKER_SERVICE}:{remote_step}")).returncode != 0:
            return written, f"docker cp (step in) failed for {step.name}"
        proc = _run(
            _compose("exec", "-T", "--index", str(_WORKER_INDEX), _WORKER_SERVICE,
                     "python", "/tmp/render_views.py", remote_step, remote_prefix),
            timeout=900,
        )
        if proc.returncode != 0:
            return written, f"render_views failed in container on {step.name}: {(proc.stderr or proc.stdout)[:300]}"
        listing = _run(_compose("exec", "-T", "--index", str(_WORKER_INDEX), _WORKER_SERVICE,
                                "sh", "-c", f"ls {remote_prefix}_*.png 2>/dev/null"))
        for remote in [line.strip() for line in listing.stdout.splitlines() if line.strip()]:
            dest = out_dir / Path(remote).name
            if _run(_compose("cp", "--index", str(_WORKER_INDEX), f"{_WORKER_SERVICE}:{remote}", str(dest))).returncode == 0:
                written.append(dest.name)
    return written, None


# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--turn", type=int, required=True)
    parser.add_argument("--idea-id", type=int, required=True)
    parser.add_argument("--stage", choices=["first-shot", "repaired"], default="first-shot")
    parser.add_argument("--ideas-file", default="board-game/IDEAS.json")
    parser.add_argument("--history-root", default="board-game/history")
    parser.add_argument("--skill-root", default=str(DEFAULT_SKILL_ROOT))
    parser.add_argument("--compose-file", default=None,
                        help="panda-social-cc-agent's docker-compose.local-worker.yml, for container-side renders")
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()

    skill_root = Path(args.skill_root)
    scripts = skill_root / "scripts"
    builds = Path(args.history_root) / f"turn-{args.turn}" / "builds"
    matches = sorted(builds.glob(f"idea-{args.idea_id:02d}-*"))
    if not matches:
        print(f"no build directory for idea {args.idea_id} under {builds}", file=sys.stderr)
        return 2
    bdir = matches[0]
    stage_dir = bdir / args.stage
    project_dir = stage_dir / "project"
    if not project_dir.exists():
        print(f"{project_dir} does not exist — run `cad_session.py capture` first", file=sys.stderr)
        return 2

    ideas = json.loads(Path(args.ideas_file).read_text())
    idea = next((i for i in ideas.get("ideas", []) if i.get("id") == args.idea_id), None)
    if idea is None:
        print(f"idea {args.idea_id} not found in {args.ideas_file}", file=sys.stderr)
        return 2
    must_survive = idea.get("must_survive") or []

    work = stage_dir / ".eval"
    work.mkdir(parents=True, exist_ok=True)

    assembly, parts, steps = find_geometry(project_dir)
    if assembly is None:
        report = {
            "turn": args.turn, "idea_id": args.idea_id, "stage": args.stage, "scored_at": _now(),
            "fatal": "no STL files in the captured project — nothing to measure",
            "geometric_fidelity": 0.0,
        }
        (stage_dir / "evaluation_report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return 1

    # 1. split the assembly into physical bodies
    instances_dir = work / "instances_stl"
    instances_json = instances_dir / "instances.json"
    extract = _run([sys.executable, str(scripts / "extract_placed_instances.py"),
                    str(assembly), str(instances_dir), "--json-out", str(instances_json)])
    instances = {}
    if instances_json.exists():
        try:
            instances = json.loads(instances_json.read_text())
        except ValueError:
            pass

    # 2. bind semantic part names to real geometry. The pilot writes
    #    bindings.json after looking at the renders and the CadQuery source;
    #    without it only assembly-level checks can run.
    bindings_path = stage_dir / "bindings.json"
    bindings: dict[str, str] = {}
    bindings_attempted = bindings_path.exists()
    if bindings_attempted:
        raw = json.loads(bindings_path.read_text())
        for name, rel in raw.items():
            candidate = (stage_dir / rel) if not Path(rel).is_absolute() else Path(rel)
            if candidate.exists():
                bindings[name] = str(candidate.resolve())

    manifest, unbindable = compile_conditions(must_survive, bindings, str(assembly.resolve()))
    manifest_path = work / "physical_conditions.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    # 3. printability — an independent second opinion on review_fix
    print_json = work / "printability.json"
    printability = _run([sys.executable, str(scripts / "score_printability.py"),
                         "--assembly", str(assembly),
                         *(["--parts", *[str(p) for p in parts]] if parts else []),
                         "--json-out", str(print_json)])
    printability_report = json.loads(print_json.read_text()) if print_json.exists() else {
        "error": (printability.stderr or printability.stdout)[:400]
    }

    # 4. physical correctness — the must_survive conditions
    phys_json = work / "physical_correctness.json"
    physical_report: dict = {}
    if manifest["conditions"]:
        phys = _run([sys.executable, str(scripts / "score_physical_correctness.py"),
                     "--condition-manifest", str(manifest_path), "--json-out", str(phys_json)])
        physical_report = json.loads(phys_json.read_text()) if phys_json.exists() else {
            "error": (phys.stderr or phys.stdout)[:400]
        }

    # 5. renders for the visual check
    renders: list[str] = []
    render_error: str | None = "skipped (--no-render)"
    if not args.no_render:
        compose = Path(args.compose_file) if args.compose_file else None
        renders, render_error = render_steps(steps, stage_dir / "renders", compose)

    # 6. rank-weighted geometric fidelity
    results = {r.get("id"): r for r in (physical_report.get("condition_results") or [])}
    per_feature = []
    weighted_total = 0.0
    weighted_max = 0.0
    for entry in must_survive:
        rank = entry.get("rank")
        weight = _RANK_WEIGHT.get(rank, 1)
        row = {
            "rank": rank,
            "feature": entry.get("feature"),
            "weight": weight,
            "has_geometric": bool(entry.get("geometric")),
            "has_visual": bool(entry.get("visual")),
            "visual_instruction": entry.get("visual"),
        }
        if entry.get("geometric"):
            result = results.get(f"ms{rank}")
            if result:
                row["status"] = result.get("status")
                row["detail"] = result.get("detail")
                row["measurements"] = result.get("measurements")
            elif any(u["rank"] == rank for u in unbindable):
                # A named part with no geometry behind it means the component
                # is absent from the build — but only once the pilot has
                # actually attempted the mapping. Before bindings.json exists,
                # nobody has looked yet, and scoring that as a failure would
                # penalise an idea for a step of our own process not having
                # run.
                if bindings_attempted:
                    row["status"] = "fail"
                    row["detail"] = "no geometry could be bound to the named part(s) — component appears absent"
                else:
                    row["status"] = "inconclusive"
                    row["detail"] = "bindings.json not written yet — rerun after the pilot maps part names to bodies"
            else:
                row["status"] = "inconclusive"
                row["detail"] = "condition did not run"
            weighted_total += weight * _STATUS_CREDIT.get(row["status"], 0.0)
            weighted_max += weight
        per_feature.append(row)

    report = {
        "turn": args.turn,
        "idea_id": args.idea_id,
        "title": idea.get("title"),
        "stage": args.stage,
        "scored_at": _now(),
        "geometry": {
            "assembly_stl": str(assembly.relative_to(stage_dir)),
            "part_stl_count": len(parts),
            "step_files": [str(s.relative_to(stage_dir)) for s in steps],
            "assembly_connected_components": (instances.get("component_count")
                                              or len(instances.get("parts") or {}) or None),
            "extract_error": (extract.stderr or "")[:300] or None,
        },
        "printability": {
            "score_0_10": printability_report.get("score"),
            "class": printability_report.get("class"),
            "raw": printability_report,
        },
        "physical_correctness": {
            "score_0_10": physical_report.get("score"),
            "condition_results": physical_report.get("condition_results"),
            "hard_failures": physical_report.get("hard_failures"),
        },
        "must_survive": per_feature,
        "unbindable": unbindable,
        "bindings_attempted": bindings_attempted,
        # Deterministic half only. The visual half of Vision Fidelity is
        # judged by board-game-evaluator over renders/ and qa.png and merged
        # in SCORES.md — this file never contains an LLM judgment.
        "geometric_fidelity": round(weighted_total / weighted_max, 4) if weighted_max else None,
        "geometric_weight_covered": weighted_max,
        "visual_pending": [r["rank"] for r in per_feature if r["has_visual"]],
        "renders": renders,
        "render_error": render_error,
    }
    (stage_dir / "evaluation_report.json").write_text(json.dumps(report, indent=2, default=str))

    covered = f"{weighted_max}/{sum(_RANK_WEIGHT.get(e.get('rank'), 1) for e in must_survive)}"
    print(json.dumps({
        "stage": args.stage,
        "geometric_fidelity": report["geometric_fidelity"],
        "weight_covered_geometrically": covered,
        "printability_0_10": report["printability"]["score_0_10"],
        "physical_0_10": report["physical_correctness"]["score_0_10"],
        "connected_components": report["geometry"]["assembly_connected_components"],
        "renders": len(renders),
        "render_error": render_error,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
