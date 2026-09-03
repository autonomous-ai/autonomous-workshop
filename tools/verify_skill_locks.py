#!/usr/bin/env python3
"""Verify reviewed Workshop skill fingerprints without network access."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

WORKSHOP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSHOP_ROOT / "src"))

from workshop.make.skill_registry import discover_skills  # noqa: E402


def _canonical(requirement: str) -> tuple[str, str]:
    """Split a requirement into its PEP 503 name and its space-free specifier."""
    cut = len(requirement)
    for index, character in enumerate(requirement):
        if character in "<>=!~[; ":
            cut = index
            break
    name = re.sub(r"[-_.]+", "-", requirement[:cut]).lower()
    return name, "".join(requirement[cut:].split())


def _verify_skill_requirements(skills_root: Path) -> None:
    vendored = tomllib.loads(
        (
            skills_root
            / "cad"
            / "scripts"
            / "packages"
            / "cadgen"
            / "pyproject.toml"
        ).read_text(encoding="utf-8")
    )
    project = vendored.get("project")
    if not isinstance(project, dict) or project.get("name") != "cadgen":
        raise ValueError("vendored cadgen metadata is invalid")
    version = project.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("vendored cadgen version is invalid")
    expected = "cadgen==%s" % version

    root_document = tomllib.loads(
        (WORKSHOP_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    root_project = root_document.get("project")
    dependencies = (
        root_project.get("dependencies") if isinstance(root_project, dict) else None
    )
    if not isinstance(dependencies, list):
        raise ValueError("Workshop dependencies are invalid")
    declared = dict(
        _canonical(item) for item in dependencies if isinstance(item, str)
    )

    requirements = [
        line.strip()
        for line in (skills_root / "cad" / "requirements.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if expected not in requirements:
        raise ValueError("CAD skill requirements must pin %s" % expected)
    # The skill runs inside the Workshop environment, so every dependency it
    # declares has to be the one the Workshop installs -- upper bound included.
    for requirement in requirements:
        name, specifier = _canonical(requirement)
        if declared.get(name) != specifier:
            raise ValueError(
                "Workshop dependency must pin %s exactly as the CAD skill does"
                % requirement
            )


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
        _verify_skill_requirements(skills_root)
        print("skill-lock: %d reviewed skill trees match" % len(observed))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("skill-lock: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
