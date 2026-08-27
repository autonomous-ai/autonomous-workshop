"""Lean user CLI for the native-agent Autonomous Workshop."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import threading
import time
import unicodedata
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, TextIO

from workshop.artifacts.core import MAX_PACK_BYTES
from workshop.artifacts.pack import bundle_artifact, plan_artifact, seal_artifact
from workshop.artifacts.schema_registry import discover_schemas, resolve_schemas_root
from workshop.contributors import (
    create_inventor,
    discover_inventors,
    inventor_collection,
    load_manifest,
    load_taste,
    load_taste_header,
    manifests_for_target,
    prepare_inventor_collection,
    validate_contribution,
    validate_inventor_collection,
)
from workshop.errors import WorkshopError
from workshop.make.skill_registry import (
    discover_skills,
    fingerprint_skill_tree,
    resolve_skills_root,
)
from workshop.runtime.agent_assets import product_run_agent_assets
from workshop.runtime.execution import codex_subprocess_environment
from workshop.runtime.credentials import (
    factory_credential_environment,
    validate_factory_credential_configuration,
)
from workshop.runtime.codex import (
    MINIMUM_CODEX_NATIVE_RUNTIME_VERSION,
    codex_supports_native_workshop,
)
from workshop.runtime.package_data import (
    packaged_inventors_root,
    product_run_domain_skill_roots,
)
from workshop.wish import Wish, generate_wish_id
from workshop.workflow import native_run_status, resume_native_run, start_native_run


_INVENTOR_ID_PART = re.compile(r"[^a-z0-9]+")
_LIVE_ACTIVE_INTERVAL_SECONDS = 2.0
_LIVE_RUNNING_INTERVAL_SECONDS = 30.0
_LIVE_CHURN_ACTIVITY = frozenset(("reasoning", "tool", "subagent"))
_LIVE_ACTIVITY_MESSAGES = {
    "starting": "Native Codex: starting the current stage.",
    "running": "Native Codex: process is still running.",
    "reasoning": "Native Codex: reasoning about the current stage.",
    "tool": "Native Codex: using a tool for the current stage.",
    "subagent": "Native Codex: coordinating a subagent.",
    "finalizing": "Native Codex: reported progress for the current stage.",
    "completed": "Native Codex: turn complete; Workshop is verifying it.",
    "failed": "Native Codex: turn stopped; Workshop is checking the result.",
}


class _LiveNativeActivity:
    """Render bounded, content-free foreground progress without log churn."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._lock = threading.Lock()
        self._last_non_running: Optional[str] = None
        self._last_active_at: Optional[float] = None
        self._last_running_at: Optional[float] = None

    def __call__(self, activity: str) -> None:
        message = _LIVE_ACTIVITY_MESSAGES.get(activity)
        if message is None:
            return
        now = time.monotonic()
        with self._lock:
            if activity == "running":
                if (
                    self._last_running_at is not None
                    and now - self._last_running_at
                    < _LIVE_RUNNING_INTERVAL_SECONDS
                ):
                    return
                self._last_running_at = now
            else:
                if activity == self._last_non_running:
                    return
                if activity in _LIVE_CHURN_ACTIVITY:
                    if (
                        self._last_active_at is not None
                        and now - self._last_active_at
                        < _LIVE_ACTIVE_INTERVAL_SECONDS
                    ):
                        return
                    self._last_active_at = now
                self._last_non_running = activity
            print(message, file=self._stream, flush=True)


def _shell_command(*parts: Any) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _inventor_id_from_taste(path: Path) -> str:
    requested = Path(path)
    if requested.name != "TASTE.md":
        raise WorkshopError(
            "--taste must name a file called TASTE.md; rename it so its identity is explicit"
        )
    header = load_taste_header(requested.parent)
    ascii_name = unicodedata.normalize("NFKD", header.name).encode(
        "ascii", "ignore"
    ).decode("ascii")
    # ``create_inventor`` appends ``-inventor`` to form a bounded Codex skill.
    inventor_id = _INVENTOR_ID_PART.sub("-", ascii_name.lower()).strip("-")[:54]
    inventor_id = inventor_id.rstrip("-")
    if len(inventor_id) < 2 or not inventor_id[0].isalpha():
        raise WorkshopError(
            "the Taste name cannot produce a safe inventor id; provide one explicitly"
        )
    return inventor_id


def _default_inventor_name(inventor_id: str) -> str:
    return " ".join(part.capitalize() for part in inventor_id.split("-"))


def _looks_like_inventor_source(root: Path) -> bool:
    try:
        resolved = root.resolve(strict=True)
    except OSError:
        return False
    collection = resolved / "inventors" if (resolved / "inventors").is_dir() else resolved
    if collection.is_symlink() or not collection.is_dir():
        return False
    try:
        return any(
            child.is_dir()
            and not child.is_symlink()
            and (child / "inventor.json").is_file()
            and not (child / "inventor.json").is_symlink()
            and (child / "TASTE.md").is_file()
            and not (child / "TASTE.md").is_symlink()
            for child in collection.iterdir()
        )
    except OSError:
        return False


def _inventor_source_root(requested: Optional[Path]) -> Path:
    """Resolve read-only Inventor sources without creating installed state."""

    if requested is not None:
        candidate = Path(requested).resolve(strict=True)
        if not _looks_like_inventor_source(candidate):
            raise WorkshopError("source has no native Inventor bundles: %s" % candidate)
        return candidate

    source_root = Path(__file__).resolve().parents[2]
    if _looks_like_inventor_source(source_root):
        return source_root
    packaged = packaged_inventors_root()
    if packaged is not None and _looks_like_inventor_source(packaged):
        return packaged
    raise WorkshopError(
        "cannot find Inventor sources; provide --root with a Workshop checkout"
    )


def _validated_inventors(root: Path):
    collection = inventor_collection(root)
    validate_inventor_collection(collection)
    return tuple(discover_inventors(collection))


def _inventor_problems(manifests) -> list[str]:
    return [
        problem
        for manifest in manifests
        for problem in validate_contribution(manifest)
    ]


def _native_exit_code(receipt: Mapping[str, Any], *, strict: bool) -> int:
    status = receipt.get("status")
    if status == "failed":
        return 1
    if strict and status == "waiting":
        return 1
    return 0


def _print_native_receipt(receipt: Mapping[str, Any], *, verb: str) -> None:
    product_id = receipt.get("product_id", "unknown")
    status = receipt.get("status", "unknown")
    stage = str(receipt.get("stage", "unknown")).title()
    print("Wish: %s" % product_id)
    print("%s: %s at %s" % (verb, status, stage))
    progress = receipt.get("progress")
    if isinstance(progress, Mapping) and progress.get("status") == "available":
        stage_attempt = progress.get("stage_attempt")
        if isinstance(stage_attempt, Mapping):
            attempt_stage = str(stage_attempt.get("stage", "unknown")).title()
            attempt_number = stage_attempt.get("number", "?")
            activity = progress.get("activity", "unknown")
            elapsed = progress.get("elapsed_seconds", 0)
            last_activity = progress.get("last_activity_at", "unknown")
            print(
                "Progress: %s attempt %s — %s (%ss; last activity %s)"
                % (
                    attempt_stage,
                    attempt_number,
                    activity,
                    elapsed,
                    last_activity,
                )
            )
    publication = receipt.get("publication")
    publication_reason = None
    if isinstance(publication, Mapping):
        page_url = publication.get("page_url")
        if isinstance(page_url, str) and page_url:
            print("Product page: %s (%s)" % (page_url, publication.get("status")))
        else:
            print("Product page: %s" % publication.get("status", "not-created"))
        manual_url = publication.get("manual_url")
        if isinstance(manual_url, str) and manual_url:
            print("Manual PDF: %s (hash-verified)" % manual_url)
        candidate_reason = publication.get("reason")
        if (
            isinstance(candidate_reason, str)
            and candidate_reason
            and (
                publication.get("requested") is True
                or publication.get("status") in ("unknown", "unavailable")
            )
        ):
            publication_reason = candidate_reason
            print("Publication note: %s" % candidate_reason)
    needs = receipt.get("needs")
    if isinstance(needs, (list, tuple)):
        for need in needs:
            if (
                isinstance(need, str)
                and need
                and need != publication_reason
            ):
                print("Need: %s" % need)
    print("Track: %s" % _shell_command("workshop", "status", product_id))
    if status == "waiting":
        print("Resume: %s" % _shell_command("workshop", "resume", product_id))


def _wish(args: argparse.Namespace) -> int:
    wish = Wish.create(
        generate_wish_id(),
        " ".join(args.objective),
        context={"source": "workshop-cli"},
    )
    progress = sys.stderr if args.json else sys.stdout
    print("Wish: %s" % wish.product_id, file=progress, flush=True)
    print("Starting one native Codex session before Match...", file=progress, flush=True)
    if not args.publish:
        print(
            "Publication: not published by default; use --publish for explicit public authority.",
            file=progress,
            flush=True,
        )
    receipt = start_native_run(
        wish,
        publish_requested=args.publish,
        activity_observer=_LiveNativeActivity(progress),
    )
    if args.json:
        _print_json(receipt)
    else:
        _print_native_receipt(receipt, verb="Run")
    return _native_exit_code(receipt, strict=args.strict)


def _status(args: argparse.Namespace) -> int:
    receipt = native_run_status(args.product_id)
    if args.json:
        _print_json(receipt)
    else:
        _print_native_receipt(receipt, verb="Status")
    return 0


def _resume(args: argparse.Namespace) -> int:
    progress = sys.stderr if args.json else sys.stdout
    print(
        "Resuming the exact native Codex session for %s..." % args.product_id,
        file=progress,
        flush=True,
    )
    receipt = resume_native_run(
        args.product_id,
        publish_requested=args.publish,
        activity_observer=_LiveNativeActivity(progress),
    )
    if args.json:
        _print_json(receipt)
    else:
        _print_native_receipt(receipt, verb="Resume")
    return _native_exit_code(receipt, strict=args.strict)


def _check_record(
    name: str,
    status: str,
    detail: str,
    *,
    next_step: Optional[str] = None,
) -> dict[str, str]:
    record = {"name": name, "status": status, "detail": detail}
    if next_step:
        record["next"] = next_step
    return record


def _doctor_catalog(root: Path) -> dict[str, str]:
    try:
        inventors = _validated_inventors(root)
    except (OSError, ValueError, WorkshopError) as exc:
        return _check_record(
            "inventor-catalog",
            "needs-attention",
            str(exc),
            next_step="Repair the schema-v8 Inventor bundles and their declared skill hashes.",
        )
    return _check_record(
        "inventor-catalog",
        "ready",
        "%d native Inventor bundle(s) validated statically" % len(inventors),
    )


def _doctor_codex() -> dict[str, str]:
    binary = os.environ.get("WORKSHOP_CODEX_BIN") or shutil.which("codex")
    if not binary:
        return _check_record(
            "codex",
            "needs-attention",
            "Codex CLI is not installed or on PATH.",
            next_step="Install Codex CLI, then run 'codex login'.",
        )
    environment = codex_subprocess_environment(os.environ)
    try:
        version = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError):
        version = None
    if version is None or version.returncode != 0:
        return _check_record(
            "codex",
            "needs-attention",
            "The configured Codex CLI command could not run.",
            next_step="Check WORKSHOP_CODEX_BIN and the Codex installation.",
        )
    output = version.stdout if isinstance(version.stdout, str) else ""
    version_match = re.search(
        r"\d+(?:\.\d+){2}(?:[-+][A-Za-z0-9.-]+)?", output
    )
    cli_version = version_match.group(0) if version_match else ""
    if not codex_supports_native_workshop(cli_version):
        minimum = ".".join(
            str(part) for part in MINIMUM_CODEX_NATIVE_RUNTIME_VERSION
        )
        return _check_record(
            "codex",
            "needs-attention",
            "The Codex CLI is too old for Workshop goals, subagents, and isolation.",
            next_step="Upgrade Codex CLI to %s or newer." % minimum,
        )
    try:
        login = subprocess.run(
            [binary, "login", "status"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError):
        login = None
    if login is None or login.returncode != 0:
        return _check_record(
            "codex",
            "needs-attention",
            "Codex CLI is installed but is not signed in.",
            next_step="Run 'codex login'; credentials remain owned by Codex.",
        )
    return _check_record("codex", "ready", "Codex CLI is installed and signed in.")


def _doctor_agent_assets() -> dict[str, str]:
    try:
        assets = product_run_agent_assets()
        roots = product_run_domain_skill_roots()
        fingerprints = {
            name: fingerprint_skill_tree(root) for name, root in roots.items()
        }
        verifier = roots["cad"] / "scripts" / "verify_project"
        identity = verifier.lstat()
        if (
            verifier.is_symlink()
            or not stat.S_ISREG(identity.st_mode)
            or not identity.st_mode & stat.S_IXUSR
        ):
            raise WorkshopError("materialized CAD verifier is not a regular executable")
        if not assets.constitution.is_file() or not assets.skill_root.is_dir():
            raise WorkshopError("product-run instructions are incomplete")
    except (KeyError, OSError, ValueError, WorkshopError) as exc:
        return _check_record(
            "agent-assets",
            "needs-attention",
            str(exc),
            next_step="Repair or reinstall the packaged product-run skills.",
        )
    return _check_record(
        "agent-assets",
        "ready",
        "Product-run constitution, workflow skill, CAD verifier, and %d domain skill(s) validated"
        % len(fingerprints),
    )


def _doctor_factory() -> dict[str, str]:
    try:
        credential_environment = factory_credential_environment()
        validate_factory_credential_configuration(credential_environment)
    except WorkshopError as exc:
        return _check_record(
            "factory-credentials",
            "needs-attention",
            str(exc),
            next_step=(
                "Repair the private $WORKSHOP_HOME/credentials/factory.env "
                "file or configure a complete host environment pair."
            ),
        )
    password = bool(credential_environment.get("FACTORY_PASSWORD"))
    generic_username = bool(credential_environment.get("FACTORY_USERNAME"))
    scoped_usernames = tuple(
        name
        for name, value in credential_environment.items()
        if name.startswith("FACTORY_")
        and name.endswith("_USERNAME")
        and name != "FACTORY_USERNAME"
        and bool(value)
    )
    username = generic_username or bool(scoped_usernames)
    if username and password:
        return _check_record(
            "factory-credentials",
            "ready",
            "A complete host-only Factory credential pair is available.",
        )
    if not username and not password:
        return _check_record(
            "factory-credentials",
            "ready",
            (
                "Factory credentials are not configured; local Release remains "
                "available and only an explicitly requested publication needs them."
            ),
        )
    return _check_record(
        "factory-credentials",
        "needs-attention",
        "Factory credentials are only partially configured.",
        next_step="Configure a username and FACTORY_PASSWORD together in the host environment.",
    )


def _doctor(args: argparse.Namespace) -> int:
    root = _inventor_source_root(args.root)
    checks = [
        _doctor_catalog(root),
        _doctor_codex(),
        _doctor_agent_assets(),
        _doctor_factory(),
    ]
    status = (
        "ready"
        if all(item["status"] == "ready" for item in checks)
        else "needs-attention"
    )
    receipt = {
        "schema_version": 1,
        "kind": "workshop-doctor",
        "status": status,
        "root": str(root),
        "checks": checks,
    }
    if args.json:
        _print_json(receipt)
    else:
        for item in checks:
            print("%-21s %s — %s" % (item["name"], item["status"], item["detail"]))
            if item.get("next"):
                print("  Next: %s" % item["next"])
        print("Workshop: %s" % status)
    return 0 if status == "ready" else 1


def _inventors(args: argparse.Namespace) -> int:
    root = _inventor_source_root(args.root)
    manifests = _validated_inventors(root)
    records = []
    for manifest in manifests:
        header = load_taste_header(manifest.path.parent)
        taste = load_taste(manifest.path.parent)
        records.append(
            {
                "id": manifest.inventor_id,
                "status": manifest.status,
                "name": header.name,
                "description": header.description,
                "taste_sha256": taste.sha256,
                "skills": [extension.name for extension in manifest.extensions],
            }
        )
    if args.json:
        _print_json(records)
    else:
        for record in records:
            print(
                "%-12s %-13s %-20s %s"
                % (
                    record["id"],
                    record["status"],
                    record["name"],
                    record["description"],
                )
            )
        print("%d native Inventor bundle(s) valid" % len(records))
    return 0


def _create_inventor(args: argparse.Namespace) -> int:
    collection = prepare_inventor_collection(args.root)
    if args.taste is None and not args.inventor_id:
        raise WorkshopError(
            "inventor_id is required unless --taste supplies a TASTE.md name"
        )
    if args.taste is None and not args.description:
        raise WorkshopError("--description is required unless --taste is supplied")
    inventor_id = args.inventor_id or _inventor_id_from_taste(args.taste)
    name = args.name
    if args.taste is None and name is None:
        name = _default_inventor_name(inventor_id)
    destination = create_inventor(
        collection,
        inventor_id,
        name,
        args.description,
        taste_path=args.taste,
    )
    manifest = load_manifest(destination / "inventor.json")
    taste = load_taste(destination)
    problems = _inventor_problems((manifest,))
    if problems:
        raise WorkshopError("created inventor failed static validation: %s" % "; ".join(problems))
    manifest_sha256 = hashlib.sha256(
        (destination / "inventor.json").read_bytes()
    ).hexdigest()
    receipt = {
        "schema_version": 1,
        "kind": "native-inventor-bundle",
        "status": manifest.status,
        "id": manifest.inventor_id,
        "name": taste.name,
        "description": taste.description,
        "path": str(destination),
        "taste_sha256": taste.sha256,
        "manifest_sha256": manifest_sha256,
        "skills": [extension.to_dict() for extension in manifest.extensions],
        "validation": "static-passed",
    }
    if args.json:
        _print_json(receipt)
    else:
        print("%s joined the Workshop as a native Inventor bundle." % taste.name)
        print("Taste: %s" % (destination / "TASTE.md"))
        print("Skill: %s" % (destination / manifest.extensions[0].path / "SKILL.md"))
        print("Checks: static-passed")
    return 0


def _check_inventor(args: argparse.Namespace) -> int:
    manifests = manifests_for_target(args.target)
    problems = _inventor_problems(manifests)
    receipt = {
        "schema_version": 1,
        "kind": "inventor-static-check",
        "status": "passed" if not problems else "failed",
        "inventors": len(manifests),
        "problems": list(problems),
    }
    if args.json:
        _print_json(receipt)
    elif problems:
        for problem in problems:
            print("error: %s" % problem, file=sys.stderr)
    else:
        print("%d inventor(s): static layout valid" % len(manifests))
    return 1 if problems else 0


def _seal(args: argparse.Namespace) -> int:
    manifest = seal_artifact(args.source, extra_excludes=args.exclude)
    if args.output:
        manifest.write(args.output)
    _print_json(manifest.to_dict())
    return 0


def _pack(args: argparse.Namespace) -> int:
    packed = bundle_artifact(
        args.source,
        args.output,
        extra_excludes=args.exclude,
        maximum_bytes=args.maximum_bytes,
    )
    _print_json(
        {
            "artifact_sha256": packed.artifact_sha256,
            "bytes": packed.bytes,
            "entries": packed.entries,
            "pack_sha256": packed.pack_sha256,
            "path": str(packed.path),
        }
    )
    return 0


def _plan_pack(args: argparse.Namespace) -> int:
    planned = plan_artifact(
        args.source,
        extra_excludes=args.exclude,
        maximum_bytes=args.maximum_bytes,
        largest=args.largest,
    )
    _print_json(planned.to_dict())
    return 0 if planned.fits else 1


def _skills(args: argparse.Namespace) -> int:
    root = resolve_skills_root(args.root)
    if args.action == "path":
        print(str(root))
        return 0
    skills = discover_skills(root)
    if args.json:
        _print_json([skill.to_dict() for skill in skills])
    else:
        for skill in skills:
            print("%-20s %s" % (skill.name, skill.sha256))
    return 0


def _schemas(args: argparse.Namespace) -> int:
    root = resolve_schemas_root(args.root)
    if args.action == "path":
        print(str(root))
        return 0
    paths = discover_schemas(root)
    if args.json:
        _print_json([path.name for path in paths])
    else:
        for path in paths:
            print(path.name)
    return 0


def _add_publication_options(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--publish",
        dest="publish",
        action="store_true",
        help="authorize optional Factory publication of the verified Release",
    )
    command.set_defaults(publish=False)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        prog="workshop",
        description=(
            "Turn one Wish into a product through one native Codex session and "
            "host-verified Workshop gates."
        ),
        epilog=(
            "Start here:\n"
            "  workshop doctor\n"
            "  workshop wish \"a wind-up moon that waddles across my desk\""
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subcommands = command.add_subparsers(
        dest="command", required=True, metavar="COMMAND"
    )

    wish = subcommands.add_parser(
        "wish", help="persist one Wish and start its native Codex session"
    )
    wish.add_argument("objective", nargs="+", metavar="WISH")
    wish.add_argument("--json", action="store_true", help="emit one JSON receipt")
    wish.add_argument("--strict", action="store_true", help="exit 1 when the run waits")
    _add_publication_options(wish)
    wish.set_defaults(handler=_wish)

    status = subcommands.add_parser(
        "status", help="inspect one native Wish checkpoint without running a model"
    )
    status.add_argument("product_id", help="Wish id printed by 'workshop wish'")
    status.add_argument("--json", action="store_true", help="emit one JSON receipt")
    status.set_defaults(handler=_status)

    resume = subcommands.add_parser(
        "resume", help="resume the exact native Codex session for one Wish"
    )
    resume.add_argument("product_id", help="saved Wish id")
    resume.add_argument("--json", action="store_true", help="emit one JSON receipt")
    resume.add_argument("--strict", action="store_true", help="exit 1 when the run waits")
    _add_publication_options(resume)
    resume.set_defaults(handler=_resume)

    doctor = subcommands.add_parser(
        "doctor", help="check native runtime prerequisites without exposing credentials"
    )
    doctor.add_argument("--root", type=Path, help="Workshop checkout or inventor catalog")
    doctor.add_argument("--json", action="store_true", help="emit one JSON receipt")
    doctor.set_defaults(handler=_doctor)

    inventors = subcommands.add_parser(
        "inventors", help="list statically validated schema-v8 Inventor bundles"
    )
    inventors.add_argument("--root", type=Path, help="Workshop checkout or inventor catalog")
    inventors.add_argument("--json", action="store_true")
    inventors.set_defaults(handler=_inventors)

    create = subcommands.add_parser("create", help="create a native Inventor bundle")
    create_commands = create.add_subparsers(
        dest="create_kind", required=True, metavar="THING"
    )
    inventor = create_commands.add_parser(
        "inventor", help="create TASTE.md, a namespaced skill, and a v8 manifest"
    )
    inventor.add_argument("inventor_id", nargs="?")
    inventor.add_argument("--taste", type=Path, help="existing TASTE.md to preserve exactly")
    inventor.add_argument("--name", help="display name for a generated Taste")
    inventor.add_argument(
        "--description",
        help="routing boundary for a generated Taste (required without --taste)",
    )
    inventor.add_argument("--root", type=Path, default=Path.cwd())
    inventor.add_argument("--json", action="store_true")
    inventor.set_defaults(handler=_create_inventor)

    check = subcommands.add_parser(
        "check", help="statically validate native Inventor bundle data"
    )
    check.add_argument("target", type=Path, nargs="?", default=Path.cwd())
    check.add_argument("--json", action="store_true")
    check.set_defaults(handler=_check_inventor)

    seal = subcommands.add_parser("seal", help="seal an artifact tree")
    seal.add_argument("source", type=Path)
    seal.add_argument("--output", type=Path)
    seal.add_argument("--exclude", action="append", default=[])
    seal.set_defaults(handler=_seal)

    pack = subcommands.add_parser("pack", help="build a reproducible immutable Pack")
    pack.add_argument("source", type=Path)
    pack.add_argument("output", type=Path)
    pack.add_argument("--exclude", action="append", default=[])
    pack.add_argument("--maximum-bytes", type=int, default=MAX_PACK_BYTES)
    pack.set_defaults(handler=_pack)

    planned = subcommands.add_parser("plan-pack", help="preview exact Pack size")
    planned.add_argument("source", type=Path)
    planned.add_argument("--exclude", action="append", default=[])
    planned.add_argument("--maximum-bytes", type=int, default=MAX_PACK_BYTES)
    planned.add_argument("--largest", type=int, default=5)
    planned.set_defaults(handler=_plan_pack)

    skills = subcommands.add_parser("skills", help="discover Make-owned domain skills")
    skills.add_argument("action", choices=("list", "path"), nargs="?", default="list")
    skills.add_argument("--root", type=Path, help="absolute skills root")
    skills.add_argument("--json", action="store_true")
    skills.set_defaults(handler=_skills)

    schemas = subcommands.add_parser("schemas", help="discover installed JSON contracts")
    schemas.add_argument("action", choices=("list", "path"), nargs="?", default="list")
    schemas.add_argument("--root", type=Path)
    schemas.add_argument("--json", action="store_true")
    schemas.set_defaults(handler=_schemas)
    return command


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parser().parse_args(argv)
        return int(args.handler(args))
    except (WorkshopError, OSError, ValueError, KeyError) as exc:
        print("workshop: %s" % exc, file=sys.stderr)
        return 2


__all__ = ["main", "parser"]
