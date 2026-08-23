#!/usr/bin/env python3
"""Aggregate CAD reconstruction evaluation reports for improvement loops."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IMPLEMENTED_CHECKS = [
    "assembly_component_count",
    "part_component_count",
    "part_collision",
    "part_clearance",
    "part_contact",
    "linear_motion_collision",
    "linear_motion_clearance",
    "rotation_motion_collision",
    "axis_alignment",
    "relative_pose",
    "opening_presence",
    "vent_opening_proxy",
    "vent_grid_open_area_proxy",
    "feature_count",
    "cylindrical_fit",
    "contact_graph",
    "assembly_sequence",
]

BASIC_PHYSICAL_CHECKS = {"assembly_component_count", "part_component_count", "clear_path_proxy"}

IMPLEMENT_NOW_KEYWORDS = [
    "count",
    "component",
    "instance",
    "axis",
    "alignment",
    "diameter",
    "clearance",
    "distance",
    "slot",
    "opening",
    "hole",
    "path",
    "pose",
    "contact",
]

PROXY_NOW_KEYWORDS = [
    "thread",
    "screw",
    "fastener",
    "load",
    "tipping",
    "support",
    "capacity",
    "container",
    "insertion",
    "snap",
    "press-fit",
]

MISSING_ONLY_KEYWORDS = [
    "fatigue",
    "material",
    "strength",
    "friction",
    "ergonomic",
    "comfort",
    "elastic",
    "deformation",
    "external",
    "proxy missing",
    "not included",
]


def _score_value(section: dict[str, Any], key: str) -> float | None:
    value = section.get(key, {}).get("score")
    return float(value) if isinstance(value, int | float) else None


def _classify_missing_helper(note: str) -> str:
    text = note.lower()
    if any(keyword in text for keyword in MISSING_ONLY_KEYWORDS):
        return "missing_helper"
    if any(keyword in text for keyword in IMPLEMENT_NOW_KEYWORDS):
        return "implement_now"
    if any(keyword in text for keyword in PROXY_NOW_KEYWORDS):
        return "proxy_now"
    return "review"


def _read_reports(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    reports = []
    for path in sorted(root.rglob("evaluation_report.json")):
        try:
            reports.append((path, json.loads(path.read_text())))
        except Exception as exc:
            reports.append((path, {"_load_error": str(exc)}))
    return reports


def _physical_section(report: dict[str, Any]) -> dict[str, Any]:
    top_level = report.get("physical_correctness")
    if not isinstance(top_level, dict):
        top_level = {}
    score_section = report.get("scores", {}).get("physical_correctness")
    if not isinstance(score_section, dict):
        score_section = {}

    if top_level.get("condition_results"):
        physical = dict(top_level)
    elif score_section.get("condition_results"):
        physical = dict(score_section)
    else:
        physical = dict(top_level)

    manifest_summary = report.get("physical_manifest_summary")
    if isinstance(manifest_summary, dict) and "missing_helper_notes" not in physical:
        physical["missing_helper_notes"] = manifest_summary.get("missing_helper_notes", [])
    return physical


def _basic_physical_check_review(project: str, physical: dict[str, Any]) -> dict[str, Any] | None:
    conditions = physical.get("condition_results", [])
    checks = sorted(
        {
            str(condition.get("check", "unknown"))
            for condition in conditions
            if isinstance(condition, dict)
        }
    )
    if not checks or any(check not in BASIC_PHYSICAL_CHECKS for check in checks):
        return None

    condition_ids = [
        str(condition.get("id", "unknown"))
        for condition in conditions
        if isinstance(condition, dict)
    ]
    note = (
        "Physical manifest only used component-count and/or open-path proxy checks. Reopen the "
        "reconstruction, inspect docs/code/renders/component geometry, rebuild the interaction matrix, "
        "and determine whether pairwise contact, clearance, collision, relative-pose, motion, fit, or "
        "feature-count checks should have been added between parts or extracted components."
    )
    return {
        "project": project,
        "checks": checks,
        "condition_count": len(conditions),
        "condition_ids": condition_ids,
        "note": note,
    }


def _collect(root: Path) -> dict[str, Any]:
    reports = _read_reports(root)
    score_rows: list[dict[str, Any]] = []
    used_checks: Counter[str] = Counter()
    failed_checks: Counter[str] = Counter()
    missing_notes: Counter[str] = Counter()
    missing_by_class: dict[str, Counter[str]] = defaultdict(Counter)
    low_score_causes: Counter[str] = Counter()
    count_mismatch_review_signals: Counter[str] = Counter()
    basic_physical_check_reviews: list[dict[str, Any]] = []

    for path, report in reports:
        project = str(path.parent)
        if "_load_error" in report:
            score_rows.append({"project": project, "load_error": report["_load_error"]})
            continue

        scores = report.get("scores", {})
        row = {
            "project": project,
            "printability": _score_value(scores, "printability"),
            "physical_correctness": _score_value(scores, "physical_correctness"),
            "feature_retention": _score_value(scores, "feature_retention"),
        }
        score_rows.append(row)

        for metric in ("printability", "physical_correctness", "feature_retention"):
            score = row.get(metric)
            if isinstance(score, float) and score < 8.0:
                low_score_causes[f"{metric}<8"] += 1

        physical = _physical_section(report)
        basic_review = _basic_physical_check_review(project, physical)
        if basic_review is not None:
            basic_physical_check_reviews.append(basic_review)

        for condition in physical.get("condition_results", []):
            check = condition.get("check", "unknown")
            used_checks[check] += 1
            if condition.get("status") == "fail":
                failed_checks[check] += 1

        for note in physical.get("missing_helper_notes", []):
            text = str(note).strip()
            if not text:
                continue
            category = _classify_missing_helper(text)
            missing_notes[text] += 1
            missing_by_class[category][text] += 1

        for risk in physical.get("risk_factors", []):
            risk_text = str(risk).lower()
            if "connected components" in risk_text and "part files" in risk_text:
                count_mismatch_review_signals["assembly_vs_part_count"] += 1

    unused_checks = [check for check in IMPLEMENTED_CHECKS if check not in used_checks]
    ranked_candidates = []
    for category in ("implement_now", "proxy_now", "review", "missing_helper"):
        for note, count in missing_by_class[category].most_common():
            ranked_candidates.append({"class": category, "count": count, "note": note})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "project_count": len(reports),
        "scores": score_rows,
        "used_checks": dict(used_checks.most_common()),
        "unused_checks": unused_checks,
        "failed_checks": dict(failed_checks.most_common()),
        "missing_helper_notes": dict(missing_notes.most_common()),
        "missing_helper_classes": {
            key: dict(counter.most_common()) for key, counter in missing_by_class.items()
        },
        "ranked_improvement_candidates": ranked_candidates,
        "low_score_causes": dict(low_score_causes.most_common()),
        "count_mismatch_review_signals": dict(count_mismatch_review_signals.most_common()),
        "basic_physical_check_reviews": basic_physical_check_reviews,
        "next_codex_prompt": _next_prompt(root, ranked_candidates, unused_checks, basic_physical_check_reviews),
    }


def _next_prompt(
    root: Path,
    candidates: list[dict[str, Any]],
    unused_checks: list[str],
    basic_physical_check_reviews: list[dict[str, Any]] | None = None,
) -> str:
    top = next((item for item in candidates if item["class"] in {"implement_now", "proxy_now"}), None)
    target = top["note"] if top else "the highest-impact deterministic helper gap in the aggregate report"
    basic_reviews = basic_physical_check_reviews or []
    basic_review_text = ""
    if basic_reviews:
        review_projects = [item["project"] for item in basic_reviews[:10]]
        overflow = len(basic_reviews) - len(review_projects)
        if overflow > 0:
            review_projects.append(f"... and {overflow} more")
        basic_review_text = (
            " The report also lists reconstructions whose physical checks only used "
            "`assembly_component_count`/`part_component_count`/`clear_path_proxy`: "
            f"{review_projects}. Before choosing a helper change, deeply investigate these reports/projects, "
            "rebuild their part interaction matrices from docs/code/renders/components, and add or record "
            "any missed pairwise physical checks between parts. "
        )
    return (
        "Use the evaluate-cad-reconstruction skill. Read the latest loop report. "
        f"Focus on this candidate: {target!r}. "
        f"{basic_review_text}"
        "Decide whether it is implement_now or proxy_now. If feasible, implement one narrow "
        "deterministic helper in cad_reconstruction_eval/physical_correctness_score.py, document it "
        "in references/physical-condition-manifests.md and references/scoring-guide.md, rerun the "
        f"affected reports under {root}, and summarize before/after scores. "
        f"Also explain whether these unused checks are truly unused or just absent from this batch: {unused_checks}."
    )


def _write_markdown(path: Path, data: dict[str, Any]) -> None:
    lines = [
        "# Evaluation Skill Improvement Loop",
        "",
        f"- Generated: `{data['generated_at']}`",
        f"- Root: `{data['root']}`",
        f"- Projects: `{data['project_count']}`",
        "",
        "## Scores",
        "",
        "| Project | Printability | Physical | Feature |",
        "|---|---:|---:|---:|",
    ]
    for row in data["scores"]:
        if "load_error" in row:
            lines.append(f"| `{row['project']}` | load error | load error | load error |")
            continue
        lines.append(
            f"| `{row['project']}` | {row.get('printability')} | "
            f"{row.get('physical_correctness')} | {row.get('feature_retention')} |"
        )

    lines += [
        "",
        "## Check Usage",
        "",
        f"- Used checks: `{', '.join(data['used_checks']) or 'none'}`",
        f"- Unused checks: `{', '.join(data['unused_checks']) or 'none'}`",
        f"- Failed checks: `{json.dumps(data['failed_checks'], sort_keys=True)}`",
        "",
        "## Improvement Candidates",
        "",
    ]
    for item in data["ranked_improvement_candidates"][:20]:
        lines.append(f"- `{item['class']}` x{item['count']}: {item['note']}")

    lines += [
        "",
        "## Low Score Causes",
        "",
        f"`{json.dumps(data['low_score_causes'], sort_keys=True)}`",
        "",
        "## Count Mismatch Review Signals",
        "",
        f"`{json.dumps(data['count_mismatch_review_signals'], sort_keys=True)}`",
        "",
        "## Basic Physical Check Reviews",
        "",
    ]
    basic_reviews = data.get("basic_physical_check_reviews", [])
    if basic_reviews:
        for item in basic_reviews:
            lines.append(
                f"- `{item['project']}`: only `{', '.join(item['checks'])}` "
                f"across {item['condition_count']} condition(s). {item['note']}"
            )
    else:
        lines.append("- none")
    lines.append("")
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Directory containing evaluation_report.json files")
    parser.add_argument("--out-dir", type=Path, default=Path("skills/evaluate-cad-reconstruction/loop_runs/latest"))
    args = parser.parse_args()

    data = _collect(args.root)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "loop_report.json"
    md_path = args.out_dir / "loop_report.md"
    json_path.write_text(json.dumps(data, indent=2))
    _write_markdown(md_path, data)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
