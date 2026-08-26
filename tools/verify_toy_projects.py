#!/usr/bin/env python3
"""Verify the tracked persistent Codex toy projects.

The normal mode is read-only and is suitable for CI.  The deliberately
explicit ``--write-migration-metadata`` mode exists only to reproduce the
metadata for the one-time legacy import from its immutable Git source tree.
It refuses to bless product changes: every retained product file must still
hash to the source blob before metadata is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from workshop.runtime.agent_assets import inventor_custom_agent_bytes


TOYS_ROOT = ROOT / "toys"
PRODUCT_RUN_SKILL_SOURCE = (
    ROOT / ".agents" / "product-run" / ".agents" / "skills" / "autonomous-workshop"
)
SOURCE_COMMIT = "db92e2b8f75262c9184455f794548909ce149748"
SCHEMA = "autonomous-workshop.toy-project.v1"
MIGRATION_SCHEMA = "autonomous-workshop.legacy-toy-migration.v1"
RUNTIME_TOY_ID = re.compile(r"^wish-[0-9]{8}-[0-9]{6}-[0-9a-f]{8}$")

PROJECTS = (
    ("alice", "blindcap-duel"),
    ("alice", "cone-nine"),
    ("alice", "five-job-checkers"),
    ("alice", "manhattan-nocturne"),
    ("bob", "comet-geneva"),
    ("eve", "rackhaven-night-shift"),
    ("ivy", "montauk-tide-orrery"),
    ("leo", "counterorbit"),
)
INVENTORS = ("alice", "bob", "eve", "ivy", "leo")

SHARED_SKILLS = ("autonomous-workshop", "cad", "product-to-cad", "step-parts")
EXCLUDED_RUNTIME_STATE = re.compile(
    r"^parts/__cadgen__/models/\.[^/]+\.(?:generation|generator)\."
    r"(?:lock|progress\.json)$"
)
EXCLUSION_REASON = (
    "generated cadgen coordination lock/progress state; contains ephemeral "
    "run, process, host, or timing data and is not a product artifact"
)
UNSAFE_NAMES = frozenset((".DS_Store", "panda-auth.json", "portal-auth.json"))
UNSAFE_SUFFIXES = (".bak", ".backup", ".orig", ".rej", ".swp", ".tmp", ".temp")
COGNITIVE_RUNTIME_PATTERNS = (
    re.compile(rb"(?m)^\s*(?:from|import)\s+(?:anthropic|openai)(?:\.|\s|$)"),
    re.compile(rb"(?i)\b(?:codex|claude)\s+(?:exec|resume)\b"),
)


@dataclass(frozen=True)
class FileRecord:
    path: str
    mode: str
    size: int
    sha256: str


def _git(*arguments: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError("git %s failed: %s" % (" ".join(arguments), detail))
    return result.stdout


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _git_mode(path: Path) -> str:
    return "100%03o" % stat.S_IMODE(path.stat().st_mode)


def _is_infrastructure(relative: PurePosixPath) -> bool:
    return (
        relative.as_posix() in ("AGENTS.md", "TOY.json")
        or relative.parts[0] in (".agents", ".codex", "catalog")
    )


def _product_records(project: Path, problems: list[str]) -> list[FileRecord]:
    records = []
    for path in sorted(project.rglob("*")):
        relative = PurePosixPath(path.relative_to(project).as_posix())
        if path.is_symlink():
            problems.append("%s: symlink is forbidden" % path.relative_to(ROOT))
            continue
        if not path.is_file() or _is_infrastructure(relative):
            continue
        if EXCLUDED_RUNTIME_STATE.fullmatch(relative.as_posix()):
            problems.append(
                "%s: excluded legacy runtime state was restored" % path.relative_to(ROOT)
            )
        lowered = path.name.lower()
        if (
            path.name in UNSAFE_NAMES
            or (lowered.startswith(".env") and lowered not in (".env.example", ".env.sample"))
            or lowered.endswith(UNSAFE_SUFFIXES)
            or "~" == path.name[-1:]
            or "__pycache__" in relative.parts
            or lowered.endswith(".pyc")
        ):
            problems.append("%s: unsafe/private runtime path" % path.relative_to(ROOT))
        if lowered.endswith(".py"):
            content = path.read_bytes()
            for pattern in COGNITIVE_RUNTIME_PATTERNS:
                if pattern.search(content):
                    problems.append(
                        "%s: product Python invokes a model-agent runtime; only product "
                        "CAD, simulation, rendering, and validation code belongs here"
                        % path.relative_to(ROOT)
                    )
        records.append(
            FileRecord(
                path=relative.as_posix(),
                mode=_git_mode(path),
                size=path.stat().st_size,
                sha256=_sha256(path),
            )
        )
    return records


def _inventory(records: Iterable[FileRecord]) -> tuple[int, int, str]:
    ordered = sorted(records, key=lambda item: item.path)
    digest = hashlib.sha256()
    byte_count = 0
    for record in ordered:
        byte_count += record.size
        digest.update(
            ("%s\0%d\0%s\0%s\n" % (
                record.mode,
                record.size,
                record.sha256,
                record.path,
            )).encode("utf-8")
        )
    return len(ordered), byte_count, digest.hexdigest()


def _tree_records(root: Path, *, ignore_generated: bool) -> dict[str, FileRecord]:
    records = {}
    for path in sorted(root.rglob("*")):
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if ignore_generated and (
            "__pycache__" in relative.parts or path.name.endswith(".pyc")
        ):
            continue
        if path.is_symlink():
            raise ValueError("symlink is forbidden in materialized source: %s" % path)
        if not path.is_file():
            continue
        records[relative.as_posix()] = FileRecord(
            path=relative.as_posix(),
            mode=_git_mode(path),
            size=path.stat().st_size,
            sha256=_sha256(path),
        )
    return records


def _compare_tree(source: Path, target: Path, label: str, problems: list[str]) -> None:
    if not target.is_dir() or target.is_symlink():
        problems.append("%s: missing regular materialized directory" % label)
        return
    try:
        expected = _tree_records(source, ignore_generated=True)
        observed = _tree_records(target, ignore_generated=False)
    except ValueError as exc:
        problems.append(str(exc))
        return
    if set(expected) != set(observed):
        missing = sorted(set(expected) - set(observed))
        extra = sorted(set(observed) - set(expected))
        problems.append(
            "%s: materialized file set differs (missing=%r extra=%r)"
            % (label, missing, extra)
        )
        return
    for relative in sorted(expected):
        if expected[relative] != observed[relative]:
            problems.append("%s/%s: bytes or executable mode differ" % (label, relative))


def _source_entries(source_path: str) -> list[dict[str, object]]:
    raw = _git("ls-tree", "-l", "-r", "-z", SOURCE_COMMIT, "--", source_path)
    prefix = source_path.rstrip("/") + "/"
    entries = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode, kind, oid, size = metadata.decode("ascii").split()
        path = encoded_path.decode("utf-8")
        if kind != "blob" or not path.startswith(prefix):
            raise RuntimeError("unexpected legacy tree entry: %s" % path)
        entries.append(
            {
                "path": path[len(prefix) :],
                "mode": mode,
                "git_blob_sha1": oid,
                "size": int(size),
            }
        )
    return entries


def _hash_objects(paths: list[Path]) -> list[str]:
    payload = b"".join(
        (path.relative_to(ROOT).as_posix() + "\n").encode("utf-8") for path in paths
    )
    output = _git("hash-object", "--no-filters", "--stdin-paths", input_bytes=payload)
    hashes = output.decode("ascii").splitlines()
    if len(hashes) != len(paths):
        raise RuntimeError("git hash-object returned an incomplete inventory")
    return hashes


def _source_tree_sha1(source_path: str) -> str:
    return _git("rev-parse", "%s:%s" % (SOURCE_COMMIT, source_path)).decode("ascii").strip()


def _declared_inventor_skills(inventor: str) -> tuple[tuple[str, Path], ...]:
    manifest_path = ROOT / "inventors" / inventor / "inventor.json"
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    extensions = document.get("extensions")
    if document.get("id") != inventor or not isinstance(extensions, list):
        raise ValueError("%s: invalid Inventor identity" % manifest_path.relative_to(ROOT))
    skills = []
    for extension in extensions:
        if not isinstance(extension, dict) or extension.get("kind") != "codex-skill":
            raise ValueError("%s: invalid Inventor extension" % manifest_path.relative_to(ROOT))
        name = extension.get("name")
        relative = extension.get("path")
        if (
            not isinstance(name, str)
            or not isinstance(relative, str)
            or PurePosixPath(relative) != PurePosixPath("skills") / name
        ):
            raise ValueError("%s: non-canonical Inventor skill" % manifest_path.relative_to(ROOT))
        source = ROOT / "inventors" / inventor / relative
        if not source.is_dir() or source.is_symlink():
            raise ValueError("%s: declared Inventor skill is missing" % source.relative_to(ROOT))
        skills.append((name, source))
    if not skills or len({name for name, _ in skills}) != len(skills):
        raise ValueError("%s: empty or duplicate Inventor skill inventory" % inventor)
    return tuple(sorted(skills, key=lambda item: item[0]))


def _canonical_custom_agent_bytes(inventor: str) -> bytes:
    skills = _declared_inventor_skills(inventor)
    return inventor_custom_agent_bytes(
        inventor,
        (ROOT / "inventors" / inventor / "TASTE.md").read_bytes(),
        skill_names=tuple(name for name, _ in skills),
    )


def _copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        source,
        target,
        copy_function=shutil.copy2,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


def _sync_project_assets() -> None:
    """Replace only host-materialized Codex assets; never touch product files."""

    for inventor, slug in PROJECTS:
        project = TOYS_ROOT / ("%s-%s" % (inventor, slug))
        if not project.is_dir() or project.is_symlink():
            raise RuntimeError("missing regular migrated project: %s" % project)
        shutil.copy2(ROOT / ".agents" / "product-run" / "AGENTS.md", project / "AGENTS.md")

        skill_root = project / ".agents" / "skills"
        if skill_root.exists():
            shutil.rmtree(skill_root)
        skill_root.mkdir(parents=True)
        _copy_tree(
            PRODUCT_RUN_SKILL_SOURCE,
            skill_root / "autonomous-workshop",
        )
        for shared in ("cad", "product-to-cad", "step-parts"):
            _copy_tree(
                ROOT / "src" / "workshop" / "make" / "skills" / shared,
                skill_root / shared,
            )
        for eligible in INVENTORS:
            for skill_name, source in _declared_inventor_skills(eligible):
                _copy_tree(source, skill_root / skill_name)

        catalog = project / "catalog" / "inventors"
        if catalog.exists():
            shutil.rmtree(catalog)
        for eligible in INVENTORS:
            destination = catalog / eligible
            destination.mkdir(parents=True)
            for filename in ("TASTE.md", "inventor.json"):
                shutil.copy2(ROOT / "inventors" / eligible / filename, destination / filename)

        custom_agents = project / ".codex" / "agents"
        if custom_agents.exists():
            shutil.rmtree(custom_agents)
        custom_agents.mkdir(parents=True)
        for eligible in INVENTORS:
            target = custom_agents / ("%s.toml" % eligible)
            target.write_bytes(_canonical_custom_agent_bytes(eligible))
            target.chmod(0o644)


def _toy_document(
    inventor: str,
    slug: str,
    source_path: str,
    source_tree_sha1: str,
    file_count: int,
    byte_count: int,
    inventory_sha256: str,
) -> dict[str, object]:
    toy_id = "%s-%s" % (inventor, slug)
    return {
        "schema": SCHEMA,
        "kind": "legacy-toy-project",
        "toy_id": toy_id,
        "display_slug": slug,
        "selected_inventor": inventor,
        "codex": {
            "working_directory": ".",
            "manager": "root-codex-session",
            "workflow_skill": ".agents/skills/autonomous-workshop/SKILL.md",
            "eligible_inventor_agents": [
                ".codex/agents/%s.toml" % eligible for eligible in INVENTORS
            ],
            "selected_inventor_subagent_skill": (
                ".agents/skills/%s-inventor/SKILL.md" % inventor
            ),
        },
        "legacy_source": {
            "commit": SOURCE_COMMIT,
            "path": source_path,
            "git_tree_sha1": source_tree_sha1,
        },
        "migration": {
            "status": "migrated-legacy-product",
            "product_file_count": file_count,
            "product_bytes": byte_count,
            "product_inventory_sha256": inventory_sha256,
            "exclusions_manifest": "../legacy-migration.json",
            "native_codex_checkpoint": None,
            "checkpoint_note": (
                "This historical product predates the native Codex run host; no "
                "session id, stage checkpoint, or resumable host state was fabricated."
            ),
        },
    }


def _write_metadata() -> None:
    project_documents = []
    for inventor, slug in PROJECTS:
        toy_id = "%s-%s" % (inventor, slug)
        project = TOYS_ROOT / toy_id
        source_path = "inventors/%s/toys/%s" % (inventor, slug)
        if not project.is_dir():
            raise RuntimeError("missing migrated project: %s" % project)
        source_entries = _source_entries(source_path)
        retained = {
            str(entry["path"]): entry
            for entry in source_entries
            if not EXCLUDED_RUNTIME_STATE.fullmatch(str(entry["path"]))
        }
        exclusions = [
            {
                **entry,
                "reason": EXCLUSION_REASON,
            }
            for entry in source_entries
            if EXCLUDED_RUNTIME_STATE.fullmatch(str(entry["path"]))
        ]
        problems: list[str] = []
        records = _product_records(project, problems)
        observed = {record.path: record for record in records}
        if problems:
            raise RuntimeError("\n".join(problems))
        if set(observed) != set(retained):
            missing = sorted(set(retained) - set(observed))
            extra = sorted(set(observed) - set(retained))
            raise RuntimeError(
                "%s does not preserve the source file set (missing=%r extra=%r)"
                % (toy_id, missing, extra)
            )
        ordered_paths = [project / relative for relative in sorted(retained)]
        object_hashes = _hash_objects(ordered_paths)
        for relative, observed_hash in zip(sorted(retained), object_hashes):
            expected = retained[relative]
            actual = observed[relative]
            if observed_hash != expected["git_blob_sha1"]:
                raise RuntimeError("%s/%s differs from the legacy source blob" % (toy_id, relative))
            if actual.mode != expected["mode"] or actual.size != expected["size"]:
                raise RuntimeError("%s/%s mode or size differs from source" % (toy_id, relative))
        file_count, byte_count, inventory_sha256 = _inventory(records)
        source_tree_sha1 = _source_tree_sha1(source_path)
        toy_document = _toy_document(
            inventor,
            slug,
            source_path,
            source_tree_sha1,
            file_count,
            byte_count,
            inventory_sha256,
        )
        (project / "TOY.json").write_text(
            json.dumps(toy_document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        project_documents.append(
            {
                "toy_id": toy_id,
                "selected_inventor": inventor,
                "display_slug": slug,
                "legacy_source_path": source_path,
                "legacy_source_tree_sha1": source_tree_sha1,
                "migrated_product": {
                    "file_count": file_count,
                    "bytes": byte_count,
                    "inventory_sha256": inventory_sha256,
                },
                "exclusions": exclusions,
            }
        )
    document = {
        "schema": MIGRATION_SCHEMA,
        "kind": "legacy-toy-project-migration",
        "source_commit": SOURCE_COMMIT,
        "exclusion_policy": {
            "path_pattern": (
                "parts/__cadgen__/models/.*.(generation|generator)."
                "(lock|progress.json)"
            ),
            "reason": EXCLUSION_REASON,
        },
        "projects": project_documents,
    }
    (TOYS_ROOT / "legacy-migration.json").write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _load_json(path: Path, problems: list[str]) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        problems.append("%s: invalid JSON: %s" % (path.relative_to(ROOT), exc))
        return None
    if not isinstance(value, dict):
        problems.append("%s: root must be an object" % path.relative_to(ROOT))
        return None
    return value


def _project_set_difference(
    observed_ids: set[str], expected_ids: set[str]
) -> tuple[list[str], list[str]]:
    """Return missing migrations and unexpected non-runtime directories."""

    missing = sorted(expected_ids - observed_ids)
    unexpected = sorted(
        toy_id
        for toy_id in observed_ids - expected_ids
        if RUNTIME_TOY_ID.fullmatch(toy_id) is None
    )
    return missing, unexpected


def verify() -> list[str]:
    problems: list[str] = []
    expected_ids = {"%s-%s" % item for item in PROJECTS}
    observed_ids = {
        path.name
        for path in TOYS_ROOT.iterdir()
        if path.is_dir() and not path.is_symlink()
    } if TOYS_ROOT.is_dir() else set()
    missing_ids, unexpected_ids = _project_set_difference(
        observed_ids, expected_ids
    )
    if missing_ids or unexpected_ids:
        problems.append(
            "toys: project set differs (missing=%r extra=%r)"
            % (missing_ids, unexpected_ids)
        )
    migration = _load_json(TOYS_ROOT / "legacy-migration.json", problems)
    if migration is None:
        return problems
    if migration.get("schema") != MIGRATION_SCHEMA or migration.get("kind") != "legacy-toy-project-migration":
        problems.append("toys/legacy-migration.json: wrong schema or kind")
    if migration.get("source_commit") != SOURCE_COMMIT:
        problems.append("toys/legacy-migration.json: wrong immutable source commit")
    migration_projects = migration.get("projects")
    if not isinstance(migration_projects, list):
        problems.append("toys/legacy-migration.json: projects must be an array")
        return problems
    by_id = {
        item.get("toy_id"): item
        for item in migration_projects
        if isinstance(item, dict) and isinstance(item.get("toy_id"), str)
    }
    if set(by_id) != expected_ids or len(by_id) != len(migration_projects):
        problems.append("toys/legacy-migration.json: project enumeration is not canonical")

    for inventor, slug in PROJECTS:
        toy_id = "%s-%s" % (inventor, slug)
        project = TOYS_ROOT / toy_id
        if not project.is_dir() or project.is_symlink():
            continue
        entry = by_id.get(toy_id)
        if not isinstance(entry, dict):
            continue
        source_path = "inventors/%s/toys/%s" % (inventor, slug)
        migrated = entry.get("migrated_product")
        exclusions = entry.get("exclusions")
        if not isinstance(migrated, dict) or not isinstance(exclusions, list):
            problems.append("%s: malformed migration inventory" % toy_id)
            continue
        if (
            entry.get("selected_inventor") != inventor
            or entry.get("display_slug") != slug
            or entry.get("legacy_source_path") != source_path
            or not isinstance(entry.get("legacy_source_tree_sha1"), str)
        ):
            problems.append("%s: migration identity/source mismatch" % toy_id)
        for exclusion in exclusions:
            if not isinstance(exclusion, dict):
                problems.append("%s: malformed exclusion record" % toy_id)
                continue
            relative = exclusion.get("path")
            if (
                not isinstance(relative, str)
                or not EXCLUDED_RUNTIME_STATE.fullmatch(relative)
                or exclusion.get("reason") != EXCLUSION_REASON
                or exclusion.get("mode") != "100644"
                or not isinstance(exclusion.get("git_blob_sha1"), str)
                or not isinstance(exclusion.get("size"), int)
            ):
                problems.append("%s: invalid exact exclusion record" % toy_id)

        records = _product_records(project, problems)
        file_count, byte_count, inventory_sha256 = _inventory(records)
        observed_summary = {
            "file_count": file_count,
            "bytes": byte_count,
            "inventory_sha256": inventory_sha256,
        }
        if migrated != observed_summary:
            problems.append("%s: preserved product inventory hash/count differs" % toy_id)
        expected_toy = _toy_document(
            inventor,
            slug,
            source_path,
            str(entry.get("legacy_source_tree_sha1")),
            file_count,
            byte_count,
            inventory_sha256,
        )
        observed_toy = _load_json(project / "TOY.json", problems)
        if observed_toy != expected_toy:
            problems.append("%s/TOY.json: non-canonical project metadata" % toy_id)

        agents_source = ROOT / ".agents" / "product-run" / "AGENTS.md"
        agents_target = project / "AGENTS.md"
        if (
            not agents_target.is_file()
            or agents_target.is_symlink()
            or agents_target.read_bytes() != agents_source.read_bytes()
            or _git_mode(agents_target) != _git_mode(agents_source)
        ):
            problems.append("%s/AGENTS.md: not an exact constitution copy" % toy_id)

        skill_root = project / ".agents" / "skills"
        observed_skill_names = {
            path.name for path in skill_root.iterdir() if path.is_dir() and not path.is_symlink()
        } if skill_root.is_dir() else set()
        expected_skill_names = set(SHARED_SKILLS)
        for eligible in INVENTORS:
            expected_skill_names.update(
                name for name, _ in _declared_inventor_skills(eligible)
            )
        if observed_skill_names != expected_skill_names:
            problems.append("%s: skill set is not the complete eligible roster" % toy_id)
        _compare_tree(
            PRODUCT_RUN_SKILL_SOURCE,
            skill_root / "autonomous-workshop",
            "%s/.agents/skills/autonomous-workshop" % toy_id,
            problems,
        )
        for skill in ("cad", "product-to-cad", "step-parts"):
            _compare_tree(
                ROOT / "src" / "workshop" / "make" / "skills" / skill,
                skill_root / skill,
                "%s/.agents/skills/%s" % (toy_id, skill),
                problems,
            )
        for eligible in INVENTORS:
            for skill_name, source in _declared_inventor_skills(eligible):
                _compare_tree(
                    source,
                    skill_root / skill_name,
                    "%s/.agents/skills/%s" % (toy_id, skill_name),
                    problems,
                )

        catalog = project / "catalog" / "inventors"
        observed_inventors = {
            path.name for path in catalog.iterdir() if path.is_dir() and not path.is_symlink()
        } if catalog.is_dir() else set()
        if observed_inventors != set(INVENTORS):
            problems.append("%s: catalog is not the complete eligible Inventor roster" % toy_id)
        for eligible in INVENTORS:
            identity_target = catalog / eligible
            identity_files = {
                path.name for path in identity_target.iterdir() if path.is_file() and not path.is_symlink()
            } if identity_target.is_dir() else set()
            if identity_files != {"TASTE.md", "inventor.json"}:
                problems.append("%s: %s identity set differs" % (toy_id, eligible))
            for filename in ("TASTE.md", "inventor.json"):
                source = ROOT / "inventors" / eligible / filename
                target = identity_target / filename
                if (
                    not target.is_file()
                    or target.is_symlink()
                    or target.read_bytes() != source.read_bytes()
                    or _git_mode(target) != _git_mode(source)
                ):
                    problems.append("%s: %s/%s bytes or mode differ" % (toy_id, eligible, filename))

        custom_agents = project / ".codex" / "agents"
        observed_agent_files = {
            path.name for path in custom_agents.iterdir() if path.is_file() and not path.is_symlink()
        } if custom_agents.is_dir() else set()
        expected_agent_files = {"%s.toml" % eligible for eligible in INVENTORS}
        if observed_agent_files != expected_agent_files:
            problems.append("%s: project-scoped custom agent roster differs" % toy_id)
        for eligible in INVENTORS:
            target = custom_agents / ("%s.toml" % eligible)
            expected_bytes = _canonical_custom_agent_bytes(eligible)
            if (
                not target.is_file()
                or target.is_symlink()
                or target.read_bytes() != expected_bytes
                or _git_mode(target) != "100644"
            ):
                problems.append("%s: .codex/agents/%s.toml is not canonical" % (toy_id, eligible))
                continue
            try:
                parsed = tomllib.loads(target.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
                problems.append("%s: invalid %s custom agent TOML: %s" % (toy_id, eligible, exc))
                continue
            if set(parsed) != {"name", "description", "developer_instructions"}:
                problems.append("%s: %s custom agent has non-canonical fields" % (toy_id, eligible))
            if parsed.get("name") != eligible:
                problems.append("%s: %s custom agent name differs" % (toy_id, eligible))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-migration-metadata",
        action="store_true",
        help="reproduce TOY.json and the exact legacy exclusion manifest",
    )
    parser.add_argument(
        "--sync-project-assets",
        action="store_true",
        help="refresh only materialized AGENTS, skills, roster, and custom-agent files",
    )
    arguments = parser.parse_args()
    if arguments.sync_project_assets:
        _sync_project_assets()
    if arguments.write_migration_metadata:
        _write_metadata()
    problems = verify()
    for problem in problems:
        print("toy-projects: %s" % problem, file=sys.stderr)
    if problems:
        print("toy-projects: %d problem(s)" % len(problems), file=sys.stderr)
        return 1
    print("toy-projects: %d projects verified" % len(PROJECTS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
