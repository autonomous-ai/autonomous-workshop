#!/usr/bin/env python3
"""Resolve a squash conflict confined to the Make skill LOCK.json.

Two branches that each change a reviewed skill tree each update that tree's
fingerprint, so their LOCK.json edits collide even though the code merged
cleanly. The right fingerprint is the one of the merged tree, which neither
side has. This merges the base/ours/theirs lock records field by field,
recomputes every sha256 from the working tree, and stages the result.

It refuses (exit 1, file untouched) when both sides changed the same
non-fingerprint field differently, or the merged skill set does not match the
tree; the caller then falls back to the resolver agent.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOCK = "src/workshop/make/skills/LOCK.json"
sys.path.insert(0, str(REPO / "src"))

from workshop.make.skill_registry import discover_skills  # noqa: E402


def _stage(number: int) -> dict:
    blob = subprocess.run(
        ["git", "show", f":{number}:{LOCK}"],
        cwd=REPO, capture_output=True, text=True,
    )
    return json.loads(blob.stdout) if blob.returncode == 0 else {}


def _merge(base, ours, theirs, where: str):
    if ours == theirs or theirs == base:
        return ours
    if ours == base:
        return theirs
    if isinstance(ours, dict) and isinstance(theirs, dict):
        base = base if isinstance(base, dict) else {}
        merged = {}
        for key in sorted(set(ours) | set(theirs)):
            value = _merge(base.get(key), ours.get(key), theirs.get(key), f"{where}.{key}")
            if value is not None:
                merged[key] = value
        return merged
    raise ValueError(f"both sides changed {where}")


def main() -> int:
    base, ours, theirs = _stage(1), _stage(2), _stage(3)
    if not ours or not theirs:
        print("relock: LOCK.json is not in a two-sided conflict", file=sys.stderr)
        return 1
    for side in (base, ours, theirs):
        for record in side.get("skills", {}).values():
            record.pop("sha256", None)
    try:
        lock = _merge(base, ours, theirs, "lock")
    except ValueError as exc:
        print(f"relock: {exc}", file=sys.stderr)
        return 1

    skills = lock.get("skills", {})
    observed = {skill.name: skill.sha256 for skill in discover_skills((REPO / LOCK).parent)}
    if set(observed) != set(skills):
        print("relock: merged skill names differ from the tree", file=sys.stderr)
        return 1
    for name, sha256 in observed.items():
        skills[name] = {"sha256": sha256, **skills[name]}

    (REPO / LOCK).write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", LOCK], cwd=REPO, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
