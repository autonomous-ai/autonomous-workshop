#!/usr/bin/env python3
"""Run an agentic Codex improvement loop for the CAD evaluation skill.

The loop is intentionally conservative:
1. aggregate existing evaluation reports;
2. read the generated next Codex prompt;
3. optionally invoke `codex exec` once for that prompt;
4. repeat.

By default this script only aggregates and prints the prompt. Pass
`--run-codex` to execute Codex non-interactively.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_LOOP_ROOT = Path("skills/evaluate-cad-reconstruction/loop_runs")
AGGREGATOR = Path("skills/evaluate-cad-reconstruction/scripts/aggregate_evaluation_reports.py")


def _next_iteration(loop_root: Path) -> int:
    existing = []
    for path in loop_root.glob("iteration_*"):
        suffix = path.name.removeprefix("iteration_")
        if suffix.isdigit():
            existing.append(int(suffix))
    return max(existing, default=0) + 1


def _run_aggregate(projects_root: Path, out_dir: Path) -> dict:
    subprocess.run(
        [
            "python3",
            str(AGGREGATOR),
            str(projects_root),
            "--out-dir",
            str(out_dir),
        ],
        check=True,
    )
    return json.loads((out_dir / "loop_report.json").read_text())


def _read_project_names(path: Path | None) -> set[str]:
    if path is None:
        return set()
    names: set[str] = set()
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        names.add(Path(text).name)
    return names


def _project_has_report(project: Path) -> bool:
    return (project / "evaluation_report.json").exists()


def _select_batch(
    projects_root: Path,
    batch_size: int | None,
    excluded_names: set[str],
    completed_names: set[str],
) -> list[Path]:
    projects = sorted([path for path in projects_root.iterdir() if path.is_dir()], key=lambda path: path.name)
    selected: list[Path] = []
    for project in projects:
        if project.name in excluded_names or project.name in completed_names:
            continue
        if _project_has_report(project):
            continue
        selected.append(project)
        if batch_size is not None and len(selected) >= batch_size:
            break
    return selected


def _read_completed_batches(loop_root: Path) -> set[str]:
    completed: set[str] = set()
    for batch_path in loop_root.glob("iteration_*/batch_projects.json"):
        try:
            data = json.loads(batch_path.read_text())
        except Exception:
            continue
        if data.get("codex_returncode") != 0:
            continue
        for item in data.get("projects", []):
            completed.add(Path(str(item)).name)
    return completed


def _batch_prompt(batch_projects: list[Path]) -> str:
    lines = [f"- `{project}`" for project in batch_projects]
    return "\n".join(lines)


def _codex_prompt(
    base_prompt: str,
    iteration: int,
    out_dir: Path,
    projects_root: Path,
    batch_projects: list[Path] | None,
) -> str:
    batch_text = ""
    if batch_projects is not None:
        batch_text = f"""
This is a batched iteration. Evaluate exactly these reconstruction projects before choosing improvements:
{_batch_prompt(batch_projects)}

For each project in the batch:
- use the evaluate-cad-reconstruction skill workflow;
- write only the final `<project>/evaluation_report.json` as the persistent project artifact;
- clean temporary evaluation files before finishing.
- before finalizing, audit the physical manifest: if the only checks are `assembly_component_count`,
  `part_component_count`, and/or `clear_path_proxy`, do not stop there. Reopen the reconstruction docs/code/renders and
  any extracted components, rebuild the interaction matrix, and deeply investigate whether measurable
  pairwise checks between parts/components should be added (`part_contact`, `part_clearance`,
  `part_collision`, `relative_pose`, fit checks, motion-path checks, or feature counts). If no such
  checks are possible, record the concrete reason in the report.

After the batch reports exist, aggregate this batch mentally/from the reports and apply at most one evaluator improvement suggested by the batch. If an improvement changes scoring/check behavior, rerun the affected batch project reports plus any small regression set that is necessary.
"""
    return f"""You are running an automatic improvement iteration for the repo-local evaluate-cad-reconstruction skill.

Iteration: {iteration}
Loop report: {out_dir / "loop_report.md"}
Projects root: {projects_root}
{batch_text}

Use the loop prompt below as the improvement instruction. Keep the iteration narrow:
- implement at most one helper/proxy/scoring-policy change;
- update docs/tests when code changes;
- rerun affected project reports plus a small regression set when feasible;
- preserve the artifact policy: delete temp evaluation artifacts and leave final reports only;
- summarize before/after scores and residual risks.

Do not use destructive git commands. Do not commit unless explicitly instructed.

Loop prompt:
{base_prompt}
"""


def _run_codex(prompt: str, out_dir: Path, model: str | None) -> int:
    final_path = out_dir / "codex_final.txt"
    stdout_path = out_dir / "codex_stdout.txt"
    stderr_path = out_dir / "codex_stderr.txt"
    cmd = [
        "codex",
        "exec",
        "-C",
        str(Path.cwd()),
        "-s",
        "workspace-write",
        "-o",
        str(final_path),
    ]
    if model:
        cmd.extend(["-m", model])
    cmd.append(prompt)

    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(cmd, text=True, capture_output=True, stdin=subprocess.DEVNULL)
    stdout_path.write_text(result.stdout)
    stderr_path.write_text(result.stderr)
    (out_dir / "codex_run.json").write_text(
        json.dumps(
            {
                "started_at": started,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "returncode": result.returncode,
                "command": cmd[:-1] + ["<prompt>"],
                "final_message_path": str(final_path),
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
            },
            indent=2,
        )
    )
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("projects_root", type=Path, help="Root containing evaluation_report.json files")
    parser.add_argument("--loop-root", type=Path, default=DEFAULT_LOOP_ROOT)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--run-codex", action="store_true", help="Actually invoke codex exec")
    parser.add_argument("--model", help="Optional model passed to codex exec")
    parser.add_argument("--batch-size", type=int, help="Select this many projects without evaluation_report.json per iteration")
    parser.add_argument("--exclude-projects-file", type=Path, help="Text file of project names or paths to skip")
    args = parser.parse_args()

    if args.iterations < 1:
        raise SystemExit("--iterations must be >= 1")

    args.loop_root.mkdir(parents=True, exist_ok=True)
    iteration = _next_iteration(args.loop_root)
    excluded_names = _read_project_names(args.exclude_projects_file)
    for offset in range(args.iterations):
        current = iteration + offset
        out_dir = args.loop_root / f"iteration_{current:03d}"
        batch_projects: list[Path] | None = None
        if args.batch_size is not None:
            if args.batch_size < 1:
                raise SystemExit("--batch-size must be >= 1")
            completed_names = _read_completed_batches(args.loop_root)
            batch_projects = _select_batch(args.projects_root, args.batch_size, excluded_names, completed_names)
            batch_data: dict[str, Any] = {
                "iteration": current,
                "projects_root": str(args.projects_root),
                "batch_size": args.batch_size,
                "projects": [str(path) for path in batch_projects],
                "excluded_project_names": sorted(excluded_names),
            }
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "batch_projects.json").write_text(json.dumps(batch_data, indent=2))
            if not batch_projects:
                print(f"iteration {current}: no remaining projects selected")
                break

        data = _run_aggregate(args.projects_root, out_dir)
        if batch_projects is not None:
            data["next_codex_prompt"] = (
                "Use the evaluate-cad-reconstruction skill. First evaluate the explicit batch projects "
                "listed in this prompt and write one final evaluation_report.json per project. Generate "
                "thorough physical manifests from rendered visual context. If a physical manifest only "
                "uses assembly_component_count/part_component_count/clear_path_proxy, treat that reconstruction as a "
                "deep-investigation target: inspect docs/code/renders/components for missed pairwise "
                "relationships and add runnable checks or report why none are measurable. Implement a narrow helper if "
                "the batch exposes a local deterministic missing-helper gap, then summarize batch scores, "
                "helper usage, remaining missing helpers, and before/after changes."
            )
            (out_dir / "loop_report.json").write_text(json.dumps(data, indent=2))
        prompt = _codex_prompt(data["next_codex_prompt"], current, out_dir, args.projects_root, batch_projects)
        (out_dir / "codex_prompt.txt").write_text(prompt)
        print(f"iteration {current}: wrote {out_dir / 'loop_report.md'}")
        print(f"iteration {current}: wrote {out_dir / 'codex_prompt.txt'}")

        if not args.run_codex:
            print("dry run only; pass --run-codex to execute the prompt")
            continue

        rc = _run_codex(prompt, out_dir, args.model)
        if batch_projects is not None:
            batch_path = out_dir / "batch_projects.json"
            batch_data = json.loads(batch_path.read_text())
            batch_data["codex_returncode"] = rc
            batch_path.write_text(json.dumps(batch_data, indent=2))
        print(f"iteration {current}: codex exec returncode {rc}")
        if rc != 0:
            return rc

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
