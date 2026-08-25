#!/usr/bin/env python3
"""Verify reviewed Workshop skill fingerprints without network access."""

from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSHOP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSHOP_ROOT / "src"))

from workshop.make.skill_registry import discover_skills  # noqa: E402


def main() -> int:
    skills_root = WORKSHOP_ROOT / "src" / "workshop" / "make" / "skills"
    lock_path = skills_root / "LOCK.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        if (
            not isinstance(lock, dict)
            or lock.get("schema_version") != 1
            or lock.get("algorithm") != "canonical-skill-tree-v1"
            or not isinstance(lock.get("skills"), dict)
        ):
            raise ValueError("unsupported skill lock contract")
        expected = lock["skills"]
        observed = {
            skill.name: skill.sha256
            for skill in discover_skills(skills_root)
        }
        if set(expected) != set(observed):
            raise ValueError(
                "skill lock names differ: expected %s, observed %s"
                % (sorted(expected), sorted(observed))
            )
        drift = []
        for name, actual in sorted(observed.items()):
            record = expected[name]
            if not isinstance(record, dict) or record.get("sha256") != actual:
                drift.append(name)
        if drift:
            print(
                "skill-lock: drift in %s; review the skill update and refresh LOCK.json"
                % ", ".join(drift),
                file=sys.stderr,
            )
            return 1
        print("skill-lock: %d reviewed skill trees match" % len(observed))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("skill-lock: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
