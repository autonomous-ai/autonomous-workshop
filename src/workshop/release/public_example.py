"""Materialize one sanitized, public Git example from sealed Release bytes.

The private product-run workspace remains the lifecycle authority.  This
module writes only an allowlisted, content-addressed workflow projection after
authenticated Factory readback proves that the exact Release is public.  It
may publish an explicitly disclosed Wish and sealed product evidence, but
never copies agent configuration, prompts, transcripts, host state,
credentials, or a raw effect receipt.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional

try:
    import fcntl
except ImportError:  # pragma: no cover - current Workshop hosts are POSIX
    fcntl = None  # type: ignore[assignment]

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ArtifactError, ContractError, StateConflict
from workshop.make.native import NativeMade
from workshop.release.native import (
    NATIVE_RELEASE_LEGACY_MANUAL_PATH,
    NATIVE_RELEASE_MANUAL_PATH,
    NativeRelease,
)
from workshop.release.public_archive import write_public_workflow_archive
from workshop.runtime import Receipt
from workshop.runtime.managers import (
    DEFAULT_MANAGER_ID,
    manager_spec,
)


_PUBLIC_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PUBLIC_INVENTOR = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_MAX_PUBLIC_NAME = 100
_TOKEN_SUMMARY_KIND = "autonomous-workshop.native-token-summary"
_TOKEN_STAGES = ("match", "invent", "make", "playtest", "release")
_TIMING_SUMMARY_KIND = "autonomous-workshop.run-timing"
_CLI_WISH_ID = re.compile(
    r"^wish-(?P<date>[0-9]{8})-(?P<time>[0-9]{6})-[0-9a-f]{8}$"
)


def _canonical_json(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("public example values must be finite JSON") from exc


def _real_directory(path: Path, label: str) -> Path:
    try:
        identity = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if (
        path.is_symlink()
        or not stat.S_ISDIR(identity.st_mode)
        or resolved != path
    ):
        raise StateConflict("%s must be a canonical real directory" % label)
    return resolved


def _https_public_url(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise StateConflict("%s is not a bounded HTTPS URL" % label)
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError as exc:
        raise StateConflict("%s is not a bounded HTTPS URL" % label) from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or bool(parsed.query)
        or bool(parsed.fragment)
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise StateConflict("%s is not a bounded HTTPS URL" % label)
    return value


def _bound_bytes(
    root: Path,
    entries: Mapping[str, Any],
    relative: str,
    *,
    label: str,
) -> bytes:
    entry = entries.get(relative)
    pure = PurePosixPath(relative)
    if entry is None or pure.is_absolute() or ".." in pure.parts:
        raise StateConflict("%s is not bound to the sealed artifact" % label)
    path = root.joinpath(*pure.parts)
    try:
        before = path.lstat()
        content = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(before.st_mode)
        or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
        or len(content) != entry.bytes
        or hashlib.sha256(content).hexdigest() != entry.sha256
    ):
        raise StateConflict("%s differs from its sealed artifact binding" % label)
    return content


def _write_public_file(root: Path, relative: str, content: bytes) -> None:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != relative:
        raise ContractError("public example output path is invalid")
    target = root.joinpath(*pure.parts)
    target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    try:
        descriptor = os.open(
            str(target),
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o644,
        )
    except OSError as exc:
        raise StateConflict("public example output could not be created") from exc
    try:
        written = 0
        while written < len(content):
            written += os.write(descriptor, content[written:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.chmod(target, 0o644)


def _install_staging_exclusively(
    staging: Path,
    *,
    parent_descriptor: int,
    target_name: str,
    target: Path,
) -> None:
    """Install a validated tree without replacing any concurrent path.

    POSIX ``rename`` may replace an empty destination directory, even after an
    absence check.  Reserve the public directory with an exclusive ``mkdir``
    and populate it through no-follow directory descriptors plus ``O_EXCL``
    files instead.  A crash can leave a partial directory, which intentionally
    becomes a hard collision for later review; no existing byte is overwritten.
    """

    os.mkdir(target_name, mode=0o755, dir_fd=parent_descriptor)
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    root_descriptor = os.open(
        target_name,
        directory_flags,
        dir_fd=parent_descriptor,
    )
    root_identity = os.fstat(root_descriptor)
    opened: dict[tuple[str, ...], int] = {(): root_descriptor}
    try:
        files, directories = _tree_inventory(staging)
        for relative in sorted(
            directories,
            key=lambda value: (len(PurePosixPath(value).parts), value),
        ):
            pure = PurePosixPath(relative)
            parent_parts = pure.parts[:-1]
            parent = opened.get(parent_parts)
            if parent is None:
                raise StateConflict("public example directory order is invalid")
            os.mkdir(pure.name, mode=0o755, dir_fd=parent)
            opened[pure.parts] = os.open(
                pure.name,
                directory_flags,
                dir_fd=parent,
            )

        for relative in files:
            pure = PurePosixPath(relative)
            parent = opened.get(pure.parts[:-1])
            if parent is None:
                raise StateConflict("public example file parent is invalid")
            source = staging.joinpath(*pure.parts)
            try:
                before = source.lstat()
                content = source.read_bytes()
                after = source.lstat()
            except OSError as exc:
                raise StateConflict(
                    "public example staging file is unavailable"
                ) from exc
            if (
                source.is_symlink()
                or not stat.S_ISREG(before.st_mode)
                or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
                != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
            ):
                raise StateConflict("public example staging file changed")
            descriptor = os.open(
                pure.name,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0),
                0o644,
                dir_fd=parent,
            )
            try:
                written = 0
                while written < len(content):
                    written += os.write(descriptor, content[written:])
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

        for parts, descriptor in sorted(
            opened.items(), key=lambda item: len(item[0]), reverse=True
        ):
            del parts
            os.fsync(descriptor)
        os.fsync(parent_descriptor)
    finally:
        for descriptor in set(opened.values()):
            try:
                os.close(descriptor)
            except OSError:
                pass

    try:
        installed = target.lstat()
    except OSError as exc:
        raise StateConflict("public example installation disappeared") from exc
    if (
        target.is_symlink()
        or not stat.S_ISDIR(installed.st_mode)
        or (installed.st_dev, installed.st_ino)
        != (root_identity.st_dev, root_identity.st_ino)
        or not _trees_are_identical(target, staging)
    ):
        raise StateConflict("public example installation changed concurrently")


def _tree_inventory(root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    files = []
    directories = []
    try:
        entries = sorted(root.rglob("*"), key=lambda item: item.as_posix())
    except OSError as exc:
        raise StateConflict("public example tree cannot be inventoried") from exc
    for entry in entries:
        relative = entry.relative_to(root).as_posix()
        try:
            identity = entry.lstat()
        except OSError as exc:
            raise StateConflict("public example tree changed while reading") from exc
        if entry.is_symlink():
            raise StateConflict("public example tree may not contain symlinks")
        if stat.S_ISDIR(identity.st_mode):
            directories.append(relative)
        elif stat.S_ISREG(identity.st_mode):
            files.append(relative)
        else:
            raise StateConflict("public example tree contains a special file")
    return tuple(files), tuple(directories)


def _trees_are_identical(left: Path, right: Path) -> bool:
    left_files, left_directories = _tree_inventory(left)
    right_files, right_directories = _tree_inventory(right)
    if left_files != right_files or left_directories != right_directories:
        return False
    for relative in left_files:
        left_path = left.joinpath(*PurePosixPath(relative).parts)
        right_path = right.joinpath(*PurePosixPath(relative).parts)
        if left_path.read_bytes() != right_path.read_bytes():
            return False
    return True


def _read_json_object(path: Path) -> Optional[dict[str, Any]]:
    if not path.is_file() or path.is_symlink():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _attempt_count_and_outcome(payload: Mapping[str, Any]) -> tuple[str, str]:
    attempts = payload.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        return "0", "missing"
    summaries: list[str] = []
    for item in attempts:
        if not isinstance(item, Mapping):
            continue
        outcome = item.get("outcome")
        if not isinstance(outcome, str) or not outcome:
            continue
        failed = item.get("failed_checks")
        if isinstance(failed, list) and failed:
            names = ", ".join(
                str(check) for check in failed if isinstance(check, str) and check
            )
            if names:
                outcome = "%s (%s)" % (outcome, names)
        round_number = item.get("round")
        if len(attempts) > 1 or (isinstance(round_number, int) and round_number != 1):
            summaries.append("round %s %s" % (round_number, outcome))
        else:
            summaries.append(outcome)
    if not summaries:
        return "0", "missing"
    return str(len(summaries)), "; ".join(summaries)


def _display_inventor_id(value: Any) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None
    return " ".join(part.capitalize() for part in value.split("-") if part)


def _workflow_overview_markdown(staging: Path) -> str:
    """Summarize public ATTEMPTS.json counts for the snapshot README."""

    explicit_invent = (staging / "invent").is_dir()
    explicit_playtest = (staging / "playtest").is_dir()
    if explicit_playtest:
        effort = "Quest"
        route = "Wish -> Invent -> Make -> Playtest -> Release"
        first_creative = "Invent"
        omitted = "Quest"
    elif explicit_invent:
        effort = "Forge"
        route = "Wish -> Invent -> Make -> Release"
        first_creative = "Invent"
        omitted = "Forge"
    else:
        effort = "Spark"
        route = "Wish -> Make -> Release"
        first_creative = "Make"
        omitted = "Spark"

    match_payload = _read_json_object(staging / "match" / "ATTEMPTS.json")
    invent_payload = _read_json_object(staging / "invent" / "ATTEMPTS.json")
    make_payload = _read_json_object(staging / "make" / "ATTEMPTS.json")
    playtest_payload = _read_json_object(staging / "playtest" / "ATTEMPTS.json")
    release_payload = _read_json_object(staging / "release" / "ATTEMPTS.json")
    assignment = _read_json_object(staging / "match" / "assignment.json")
    publication = _read_json_object(staging / "publication" / "PUBLICATION.json")
    inventor = _display_inventor_id(
        None if assignment is None else assignment.get("selected_inventor_id")
    )
    match_count, match_outcome = (
        ("1", "accepted")
        if match_payload is None
        else _attempt_count_and_outcome(match_payload)
    )
    if inventor is not None and "accepted" in match_outcome:
        match_outcome = "%s (%s)" % (match_outcome, inventor)
    make_count, make_outcome = (
        ("1", "accepted")
        if make_payload is None
        else _attempt_count_and_outcome(make_payload)
    )
    release_count, release_outcome = (
        ("1", "accepted")
        if release_payload is None
        else _attempt_count_and_outcome(release_payload)
    )
    if explicit_invent:
        invent_count, invent_outcome = (
            ("1", "accepted")
            if invent_payload is None
            else _attempt_count_and_outcome(invent_payload)
        )
    else:
        invent_count, invent_outcome = "skipped", "%s pass-through" % omitted
    if explicit_playtest:
        playtest_count, playtest_outcome = (
            ("1", "accepted")
            if playtest_payload is None
            else _attempt_count_and_outcome(playtest_payload)
        )
    else:
        playtest_count, playtest_outcome = "not run", "%s omission" % omitted
    publication_status = "public"
    if publication is not None:
        nested = publication.get("publication")
        status = nested.get("status") if isinstance(nested, Mapping) else None
        if isinstance(status, str) and status:
            publication_status = status

    rows = (
        ("Wish", "host", "frozen"),
        ("Match", match_count, match_outcome),
        ("Invent", invent_count, invent_outcome),
        ("Make", make_count, make_outcome),
        ("Playtest", playtest_count, playtest_outcome),
        ("Release", release_count, release_outcome),
        ("Publication", "host", publication_status),
    )
    table = "\n".join(
        ["| Stage | Attempts | Outcome |", "|---|---|---|"]
        + ["| %s | %s | %s |" % row for row in rows]
    )
    return (
        "## Workflow\n\n"
        "%s: `%s`. Inventor selection is folded into %s.\n\n"
        "%s\n\n"
        "Counts come from each stage's public `ATTEMPTS.json`. Skipped stages "
        "created no turn, artifact, or gate. Private host rejections and native "
        "session resumes are not public.\n"
        % (effort, route, first_creative, table)
    )


def _public_token_summary(value: Any) -> dict[str, Any]:
    unavailable = {
        "schema_version": 1,
        "kind": _TOKEN_SUMMARY_KIND,
        "status": "unavailable",
    }
    if value is None or (
        isinstance(value, Mapping) and value.get("status") == "unavailable"
    ):
        return unavailable
    if (
        not isinstance(value, Mapping)
        or value.get("schema_version") != 1
        or value.get("kind") != _TOKEN_SUMMARY_KIND
        or value.get("status") not in ("measured", "partial")
        or not isinstance(value.get("turns"), Mapping)
        or not isinstance(value.get("stages"), Mapping)
        or set(value["stages"]) != set(_TOKEN_STAGES)
    ):
        raise ContractError("public native token summary is invalid")
    turns = value["turns"]
    if (
        set(turns) != {"total", "measured", "unmeasured"}
        or any(
            type(count) is not int or not 0 <= count <= 100_000
            for count in turns.values()
        )
        or turns["measured"] + turns["unmeasured"] != turns["total"]
    ):
        raise ContractError("public native token turn counts are invalid")
    total_tokens = value.get("total_tokens")
    if type(total_tokens) is not int or not 0 <= total_tokens <= 10**18:
        raise ContractError("public native token total is invalid")
    rebuilt_stages = {}
    for name in _TOKEN_STAGES:
        stage = value["stages"][name]
        if not isinstance(stage, Mapping):
            raise ContractError("public native token stage is invalid")
        status = stage.get("status")
        stage_turns = stage.get("turns")
        tokens = stage.get("tokens")
        if status not in {
            "measured", "partial", "pending", "folded", "skipped", "not-run"
        } or type(stage_turns) is not int or not 0 <= stage_turns <= 100_000:
            raise ContractError("public native token stage status is invalid")
        if type(tokens) is not int or not 0 <= tokens <= 10**18:
            raise ContractError("public native token stage total is invalid")
        rebuilt_stages[name] = {
            "status": status,
            "turns": stage_turns,
            "tokens": tokens,
        }
    return {
        "schema_version": 1,
        "kind": _TOKEN_SUMMARY_KIND,
        "status": value["status"],
        "turns": dict(turns),
        "total_tokens": total_tokens,
        "stages": rebuilt_stages,
    }


def _public_timing_summary(wish_id: Optional[str], completed_at: str) -> dict[str, Any]:
    """Derive CLI Wish-to-publication time without adding private host state.

    The generated CLI Wish id contains its UTC intake second. The completion
    boundary is the authenticated Factory public-readback receipt, not the
    native agent's prose or its final turn. Programmatic and historical ids do
    not necessarily carry time, so they remain explicitly unavailable.
    """

    unavailable = {
        "schema_version": 1,
        "kind": _TIMING_SUMMARY_KIND,
        "status": "unavailable",
        "reason": "Wish intake time is unavailable for this run.",
    }
    match = _CLI_WISH_ID.fullmatch(wish_id) if isinstance(wish_id, str) else None
    if match is None:
        return unavailable
    try:
        started = datetime.strptime(
            match.group("date") + match.group("time"), "%Y%m%d%H%M%S"
        ).replace(tzinfo=timezone.utc)
        completed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return unavailable
    if (
        completed.tzinfo is None
        or completed.utcoffset() != timezone.utc.utcoffset(completed)
    ):
        return unavailable
    elapsed_seconds = int((completed - started).total_seconds())
    if elapsed_seconds < 0:
        return unavailable
    return {
        "schema_version": 1,
        "kind": _TIMING_SUMMARY_KIND,
        "status": "measured",
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "completed_at": completed_at,
        "elapsed_seconds": elapsed_seconds,
        "completion_boundary": "authenticated Factory public readback",
    }


def _format_elapsed_seconds(value: int) -> str:
    days, remainder = divmod(value, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append("%dd" % days)
    if hours or days:
        parts.append("%dh" % hours)
    if minutes or hours or days:
        parts.append("%dm" % minutes)
    parts.append("%ds" % seconds)
    return " ".join(parts)


def _run_cost_markdown(
    token_summary: Mapping[str, Any], timing_summary: Mapping[str, Any]
) -> str:
    token_status = token_summary["status"]
    if token_status in ("measured", "partial"):
        turns = token_summary["turns"]
        token_value = "%s (%s; %s/%s turns measured)" % (
            format(token_summary["total_tokens"], ",d"),
            token_status,
            turns["measured"],
            turns["total"],
        )
        stage_rows = [
            "| %s | %s | %s | %s |"
            % (
                name.capitalize(),
                format(stage["tokens"], ",d"),
                stage["turns"],
                stage["status"],
            )
            for name, stage in token_summary["stages"].items()
        ]
        stage_table = (
            "\n\n| Stage | Tokens | Turns | Coverage |\n"
            "|---|---:|---:|---|\n"
            + "\n".join(stage_rows)
        )
    else:
        token_value = "unavailable (the Manager did not report token usage)"
        stage_table = ""
    if timing_summary["status"] == "measured":
        elapsed_value = "%s (%s to %s)" % (
            _format_elapsed_seconds(timing_summary["elapsed_seconds"]),
            timing_summary["started_at"],
            timing_summary["completed_at"],
        )
    else:
        elapsed_value = "unavailable (Wish intake time was not recorded)"
    return (
        "## Run cost\n\n"
        "| Measure | Value |\n"
        "|---|---|\n"
        "| Native Manager tokens | %s |\n"
        "| Wish to verified publication | %s |"
        "%s\n\n"
        "Tokens are best-effort input-plus-output counts reported by the native "
        "Manager; no dollar cost is inferred. Elapsed time ends only after "
        "authenticated Factory public readback.\n"
        % (token_value, elapsed_value, stage_table)
    )


def _snapshot_effort(staging: Path) -> str:
    if (staging / "playtest").is_dir():
        return "quest"
    if (staging / "invent").is_dir():
        return "forge"
    return "spark"


def _public_hero_path(staging: Path) -> Optional[str]:
    candidates = (
        "make/verification/renders/iso.png",
        "make/verification/renders/front.png",
        "make/verification/renders/top.png",
        "make/verification/renders/right.png",
    )
    for relative in candidates:
        if (staging / relative).is_file():
            return relative
    product = staging / "make" / "product"
    if product.is_dir():
        for image in sorted(product.rglob("*")):
            if image.is_file() and image.suffix.casefold() in (".png", ".jpg", ".jpeg"):
                return image.relative_to(staging).as_posix()
    return None


def _reproduce_markdown(
    staging: Path,
    *,
    summary: str,
    manager_id: str,
    effort: str,
    github_requested: bool,
) -> str:
    wish = _read_json_object(staging / "wish" / "wish.json") or {}
    exact = wish.get("objective")
    objective = exact if isinstance(exact, str) and exact.strip() else summary
    disclosure = "exact original Wish" if exact else "public product summary"
    arguments = [
        "uv",
        "run",
        "workshop",
        "wish",
        "--manager",
        manager_id,
        "--effort",
        effort,
    ]
    if github_requested:
        arguments.append("--github")
    arguments.append(objective)
    command = " ".join(shlex.quote(part) for part in arguments)
    return (
        "## Reproduce\n\n"
        "From a checkout of this repository, verify the host and run the same "
        "Manager and effort route. This command uses the %s; a later run follows "
        "the same route but does not replay these exact CAD bytes.\n\n"
        "```bash\n"
        "uv run workshop doctor\n"
        "%s\n"
        "```\n\n"
        "If a native turn stops before Release, continue the same Wish with "
        "`uv run workshop resume <wish-id>`.\n"
        % (disclosure, command)
    )


def _copy_model(
    *,
    product_root: Path,
    product_entries: Mapping[str, Any],
    source: str,
    destination: str,
    staging: Path,
) -> dict[str, Any]:
    content = _bound_bytes(
        product_root,
        product_entries,
        source,
        label="public model %s" % source,
    )
    _write_public_file(staging, destination, content)
    return {
        "path": destination,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def materialize_public_example(
    repository_root: Path,
    run_root: Path,
    *,
    release: NativeRelease,
    made: NativeMade,
    inventor_id: str,
    receipt: Receipt,
    disclose_exact_wish: bool = False,
    manager_id: str = DEFAULT_MANAGER_ID,
    effort: Optional[str] = None,
    github_requested: bool = False,
    token_summary: Optional[Mapping[str, Any]] = None,
    wish_id: Optional[str] = None,
) -> Path:
    """Create ``toys/<inventor>-<slug>`` from exact public Release bytes.

    Repeating the operation with identical bytes is idempotent.  An existing
    symlink, partial directory, or different snapshot is a hard collision; no
    public example is overwritten or merged.
    """

    # Imported at effect-composition time so the Release component does not
    # create a module-load cycle through workflow -> integrations -> release.
    from workshop.workflow.effort import workshop_effort

    if not isinstance(release, NativeRelease) or not isinstance(made, NativeMade):
        raise ContractError("public example requires typed Made and Release inputs")
    if type(disclose_exact_wish) is not bool:
        raise ContractError("public example Wish disclosure must be boolean")
    manager = manager_spec(manager_id)
    if effort is not None:
        selected_effort = workshop_effort(effort)
    else:
        selected_effort = None
    if type(github_requested) is not bool:
        raise ContractError("public example GitHub request must be boolean")
    if not isinstance(receipt, Receipt) or not receipt.is_verified_public:
        raise StateConflict("public example requires verified public Factory readback")
    if (
        not isinstance(inventor_id, str)
        or len(inventor_id) > _MAX_PUBLIC_NAME
        or _PUBLIC_INVENTOR.fullmatch(inventor_id) is None
    ):
        raise ContractError("public example Inventor id is not a canonical slug")
    slug = receipt.slug
    if (
        not isinstance(slug, str)
        or len(slug) > _MAX_PUBLIC_NAME
        or _PUBLIC_SLUG.fullmatch(slug) is None
    ):
        raise StateConflict("public Factory slug is not safe for a repository path")
    receipt.assert_artifact(release.product_artifact_sha256)
    details = receipt.details
    pdf_first = release.manual_path == NATIVE_RELEASE_MANUAL_PATH
    for field in (
        "manual_sha256",
        "primary_model_sha256",
        "product_page_sha256",
        "release_sha256",
    ):
        if (
            not isinstance(details.get(field), str)
            or re.fullmatch(r"[0-9a-f]{64}", details[field]) is None
        ):
            raise StateConflict("public Factory receipt lacks exact byte identities")
    if pdf_first:
        if details.get("manual_path") != NATIVE_RELEASE_MANUAL_PATH:
            raise StateConflict("public Factory receipt belongs to a different manual path")
    elif (
        release.manual_path != NATIVE_RELEASE_LEGACY_MANUAL_PATH
        or not isinstance(details.get("factory_content_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", details["factory_content_sha256"])
        is None
    ):
        raise StateConflict("public Factory receipt lacks exact byte identities")
    if (
        release.made_sha256 != made.made_sha256
        or release.product_artifact_sha256
        != made.product_manifest.artifact_sha256
        or details.get("release_sha256")
        != release.package_manifest.artifact_sha256
        or details.get("product_page_sha256") != release.product_json_sha256
    ):
        raise StateConflict("public Factory receipt belongs to different Release bytes")

    repository = _real_directory(Path(repository_root), "Workshop repository")
    run = _real_directory(Path(run_root), "private run workspace")
    toys = _real_directory(repository / "toys", "public examples directory")
    package_root = _real_directory(
        run.joinpath(*PurePosixPath(release.package_root).parts),
        "sealed Release package",
    )
    if build_artifact_manifest(
        package_root, created_at=release.package_manifest.created_at
    ).to_dict() != release.package_manifest.to_dict():
        raise StateConflict("sealed Release package differs from its manifest")
    made_product = made.validate_product_tree(run)
    product_root = _real_directory(
        made_product.artifact_root, "sealed Made product"
    )
    package_entries = {
        entry.path: entry for entry in release.package_manifest.entries
    }
    product_entries = {
        entry.path: entry for entry in made.product_manifest.entries
    }
    manual = _bound_bytes(
        package_root,
        package_entries,
        release.manual_path,
        label="public %s" % release.manual_path,
    )
    product_json = _bound_bytes(
        package_root,
        package_entries,
        release.product_json_path,
        label="public product.json",
    )
    manual_entry = package_entries[release.manual_path]
    if details.get("manual_sha256") != manual_entry.sha256:
        raise StateConflict("public Factory receipt belongs to different manual bytes")

    target = toys / (inventor_id + "-" + slug)
    staging = Path(
        tempfile.mkdtemp(prefix=".public-example-", dir=str(toys))
    ).resolve(strict=True)
    try:
        print_files = []
        primary_model = None
        primary_path = details.get("primary_model_path")
        primary_sha256 = details.get("primary_model_sha256")
        cad = made.product.get("cad")
        assembled_reference = (
            cad.get("assembled_stl") if isinstance(cad, Mapping) else None
        )
        if isinstance(assembled_reference, Mapping):
            if (
                assembled_reference.get("path") != primary_path
                or assembled_reference.get("sha256") != primary_sha256
            ):
                raise StateConflict(
                    "public Factory primary model differs from Made product facts"
                )
        if (
            isinstance(primary_path, str)
            and PurePosixPath(primary_path).suffix.casefold() == ".stl"
        ):
            entry = product_entries.get(primary_path)
            if entry is None or entry.sha256 != primary_sha256:
                raise StateConflict(
                    "public Factory primary model differs from sealed Made bytes"
                )
            destination = "make/models/assembled.stl"
            primary_model = _copy_model(
                product_root=product_root,
                product_entries=product_entries,
                source=primary_path,
                destination=destination,
                staging=staging,
            )

        inventory = made.product.get("inventory")
        inventory_parts = (
            inventory.get("parts") if isinstance(inventory, Mapping) else None
        )
        if inventory_parts is not None and (
            not isinstance(inventory_parts, (list, tuple))
            or not inventory_parts
        ):
            raise StateConflict("Made product print inventory is malformed")
        for index, part in enumerate(inventory_parts or (), start=1):
            if not isinstance(part, Mapping):
                raise StateConflict("Made product print inventory is malformed")
            reference = part.get("stl")
            quantity = part.get("quantity")
            if (
                not isinstance(reference, Mapping)
                or type(quantity) is not int
                or not 1 <= quantity <= 10_000
            ):
                raise StateConflict("Made product print inventory is malformed")
            source = reference.get("path")
            if not isinstance(source, str):
                raise StateConflict("Made product print inventory is malformed")
            pure = PurePosixPath(source)
            entry = product_entries.get(source)
            if (
                pure.is_absolute()
                or pure.suffix.casefold() != ".stl"
                or ".." in pure.parts
                or entry is None
                or reference.get("bytes") != entry.bytes
                or reference.get("sha256") != entry.sha256
            ):
                raise StateConflict(
                    "Made product print inventory differs from sealed model bytes"
                )
            destination = "make/models/print/component-%03d.stl" % index
            copied = _copy_model(
                product_root=product_root,
                product_entries=product_entries,
                source=source,
                destination=destination,
                staging=staging,
            )
            copied["quantity"] = quantity
            print_files.append(copied)

        page_url = _https_public_url(details.get("page_url"), "public page URL")
        cover_url = (
            None
            if pdf_first
            else _https_public_url(details.get("cover_url"), "public cover URL")
        )
        title = str(release.product["title"])
        summary = str(release.product["summary"])
        identities = {
            "native_release_sha256": release.release_sha256,
            "package_artifact_sha256": release.package_manifest.artifact_sha256,
            "product_artifact_sha256": release.product_artifact_sha256,
            "playtest_evidence_sha256": (
                release.playtest_evidence_artifact_sha256
            ),
            "product_page_sha256": release.product_json_sha256,
            "manual_sha256": manual_entry.sha256,
            "primary_model_sha256": primary_sha256,
        }
        if pdf_first:
            identities["manual_path"] = release.manual_path
        else:
            identities["factory_content_sha256"] = details.get(
                "factory_content_sha256"
            )
        publication_details = {
            "adapter": "factory",
            "status": "public",
            "slug": slug,
            "page_url": page_url,
            "observed_at": receipt.observed_at,
            "listing": {
                "price_cents": receipt.listing_price_cents,
                "currency": receipt.listing_currency,
            },
        }
        if cover_url is not None:
            publication_details["cover_url"] = cover_url
        publication = {
            "schema_version": 2,
            "kind": "autonomous-workshop.public-toy-snapshot",
            "title": title,
            "inventor": {"id": inventor_id},
            "publication": publication_details,
            "identities": identities,
            "primary_model": primary_model,
            "print_files": print_files,
        }
        public_token_summary = _public_token_summary(token_summary)
        public_timing_summary = _public_timing_summary(wish_id, receipt.observed_at)
        _write_public_file(
            staging,
            "TOKENS.json",
            _canonical_json(public_token_summary),
        )
        _write_public_file(
            staging,
            "TIMING.json",
            _canonical_json(public_timing_summary),
        )
        write_public_workflow_archive(
            staging,
            run,
            made=made,
            release=release,
            title=title,
            summary=summary,
            publication=publication,
            writer=lambda relative, content: _write_public_file(
                staging,
                relative,
                content.encode("utf-8") if isinstance(content, str) else content,
            ),
            disclose_exact_wish=disclose_exact_wish,
        )
        resolved_effort = (
            selected_effort.name
            if selected_effort is not None
            else _snapshot_effort(staging)
        )
        hero_path = _public_hero_path(staging)
        heading = " ".join(title.split())
        product_description = (
            "the exact sealed Release facts"
            if pdf_first
            else "the exact sealed public Release page contract"
        )
        manual_description = (
            "the exact sealed printable in-box manual"
            if pdf_first
            else "the exact sealed public manual"
        )
        readme = (
            "# %s\n\n"
            "%s"
            "%s\n\n"
            "[View the verified public product page](%s)\n\n"
            "| Frozen on this run | Value |\n"
            "|---|---|\n"
            "| Manager | %s (`--manager %s`) |\n"
            "| Effort | %s (`--effort %s`) |\n"
            "| Inventor | [%s](../../inventors/%s/) |\n"
            "| Factory | %s |\n\n"
            "%s\n"
            "%s\n"
            "%s\n"
            "## Snapshot contents\n\n"
            "- `wish/` — sanitized Wish binding (exact text only with explicit consent).\n"
            "- `match/` — accepted Match assignment.\n"
            "%s"
            "- `make/` — %s, exact CAD source, models, product renders, verification, and sealed prior attempts.\n"
            "- `release/%s` — %s.\n"
            "- `release/` — accepted Release contract and exact package bytes.\n"
            "- `publication/PUBLICATION.json` — sanitized public readback identities.\n"
            "- `TOKENS.json` — Manager-reported total tokens by stage; no dollar estimate.\n"
            "- `TIMING.json` — Wish intake to authenticated public-readback elapsed time.\n"
            "- `MANIFEST.json` — hashes every workflow file except itself and this README.\n"
            "%s"
            "%s\n"
            "This archive contains no agent session, prompt, transcript, chain of "
            "thought, host state, credentials, or raw effect receipt. Publication is "
            "not proof of physical manufacture, fit, durability, or delivery.\n"
        ) % (
            heading,
            (
                "![%s](%s)\n\n" % (heading, hero_path)
                if hero_path is not None
                else ""
            ),
            summary,
            page_url,
            manager.display_name,
            manager.manager_id,
            workshop_effort(resolved_effort).title,
            resolved_effort,
            _display_inventor_id(inventor_id) or inventor_id,
            inventor_id,
            page_url,
            _workflow_overview_markdown(staging),
            _run_cost_markdown(public_token_summary, public_timing_summary),
            _reproduce_markdown(
                staging,
                summary=summary,
                manager_id=manager.manager_id,
                effort=resolved_effort,
                github_requested=github_requested,
            ),
            (
                "- `invent/` — accepted Invent contract/source and sealed superseded attempts.\n"
                if (staging / "invent").is_dir()
                else "- Invent was skipped by this effort route; its sealed compact concept is under `make/`.\n"
            ),
            product_description,
            release.manual_path,
            manual_description,
            (
                "- `SANITIZATION.json` — source/public hashes for host-local path prefixes replaced by stable placeholders.\n"
                if (staging / "SANITIZATION.json").is_file()
                else ""
            ),
            (
                "- `playtest/` — accepted Playtest contract/evidence and sealed superseded attempts.\n"
                if release.schema_version != 3
                else "- Playtest was not run; Release records that omission explicitly.\n"
            ),
        )
        _write_public_file(staging, "README.md", readme.encode("utf-8"))
        for directory in sorted(
            (entry for entry in staging.rglob("*") if entry.is_dir()),
            key=lambda item: len(item.parts),
            reverse=True,
        ):
            os.chmod(directory, 0o755)
        os.chmod(staging, 0o755)

        if fcntl is None:
            raise StateConflict("public example publication requires POSIX locking")
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        directory_descriptor = os.open(str(toys), flags)
        try:
            fcntl.flock(directory_descriptor, fcntl.LOCK_EX)
            if target.exists() or target.is_symlink():
                existing = _real_directory(target, "existing public example")
                if _trees_are_identical(existing, staging):
                    return existing
                raise StateConflict(
                    "public example already exists with different or partial bytes"
                )
            try:
                _install_staging_exclusively(
                    staging,
                    parent_descriptor=directory_descriptor,
                    target_name=target.name,
                    target=target,
                )
            except OSError as exc:
                raise StateConflict(
                    "public example could not be installed without overwrite"
                ) from exc
        finally:
            try:
                fcntl.flock(directory_descriptor, fcntl.LOCK_UN)
            finally:
                os.close(directory_descriptor)
        return target
    except (ArtifactError, OSError) as exc:
        raise StateConflict("public example materialization failed") from exc
    finally:
        if staging.exists() and staging != target:
            try:
                shutil.rmtree(staging)
            except OSError:
                pass


def materialize_public_example_if_source_checkout(
    repository_root: Optional[Path],
    run_root: Path,
    *,
    release: NativeRelease,
    made: NativeMade,
    inventor_id: str,
    receipt: Receipt,
    disclose_exact_wish: bool = False,
    manager_id: str = DEFAULT_MANAGER_ID,
    effort: Optional[str] = None,
    github_requested: bool = False,
    token_summary: Optional[Mapping[str, Any]] = None,
    wish_id: Optional[str] = None,
) -> Optional[Path]:
    """Materialize a public example when the host is running from a checkout."""

    if repository_root is None:
        return None
    return materialize_public_example(
        repository_root,
        run_root,
        release=release,
        made=made,
        inventor_id=inventor_id,
        receipt=receipt,
        disclose_exact_wish=disclose_exact_wish,
        manager_id=manager_id,
        effort=effort,
        github_requested=github_requested,
        token_summary=token_summary,
        wish_id=wish_id,
    )


__all__ = [
    "materialize_public_example",
    "materialize_public_example_if_source_checkout",
]
