"""Build the workflow-shaped, sanitized public archive for one toy.

The private run remains authoritative.  This module only projects bytes that
are transitively bound to the accepted Made and Release contracts.  It never
copies native-agent transcripts, prompts, host state, credentials, raw effect
receipts, or arbitrary work-directory notes.
"""

from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

from workshop.artifacts import ArtifactEntry, ArtifactManifest, MAX_ENTRIES
from workshop.errors import ContractError, StateConflict
from workshop.invent.native import NativeInvented
from workshop.make.native import NativeMade
from workshop.match.native import NativeMatchAssignment
from workshop.playtest.native import NativePlaytested
from workshop.release.native import NativeRelease
from workshop.wish.contracts import Wish


PUBLIC_ARCHIVE_SCHEMA_VERSION = 2
_MAX_BOUND_FILE_BYTES = 128 * 1024 * 1024
_GENERATED_DIRECTORIES = frozenset(("__cadgen__", "__pycache__"))
_MODEL_SUFFIXES = frozenset((".3mf", ".glb", ".obj", ".step", ".stl"))

PublicWriter = Callable[[str, bytes], None]
_ROOT_MANIFEST_EXCLUDES = frozenset(("MANIFEST.json", "README.md"))


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
        raise ContractError("public archive values must be finite JSON") from exc


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError("non-finite JSON constant %s" % value)


def _strict_json(content: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeError, ValueError, RecursionError, json.JSONDecodeError) as exc:
        raise StateConflict("%s is not strict UTF-8 JSON" % label) from exc
    if not isinstance(value, dict):
        raise StateConflict("%s must contain one JSON object" % label)
    return value


def _stable_file(path: Path, label: str, *, allow_empty: bool = False) -> bytes:
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
        or len(content) > _MAX_BOUND_FILE_BYTES
        or (not content and not allow_empty)
    ):
        raise StateConflict("%s changed or is not a bounded regular file" % label)
    return content


def build_public_archive_manifest(root: Path) -> ArtifactManifest:
    """Hash every regular archive file except the two exact root metadata files."""

    root = Path(root).resolve(strict=True)
    entries = []
    try:
        paths = sorted(root.rglob("*"), key=lambda item: item.as_posix())
    except OSError as exc:
        raise StateConflict("public archive cannot be inventoried") from exc
    for path in paths:
        relative = path.relative_to(root).as_posix()
        try:
            before = path.lstat()
        except OSError as exc:
            raise StateConflict("public archive changed while inventorying") from exc
        if path.is_symlink():
            raise StateConflict("public archive may not contain symlinks")
        if stat.S_ISDIR(before.st_mode):
            continue
        if not stat.S_ISREG(before.st_mode):
            raise StateConflict("public archive contains a special file")
        if relative in _ROOT_MANIFEST_EXCLUDES:
            continue
        content = _stable_file(
            path,
            "public archive file %s" % relative,
            allow_empty=True,
        )
        try:
            after = path.lstat()
        except OSError as exc:
            raise StateConflict("public archive changed while inventorying") from exc
        if (
            before.st_dev,
            before.st_ino,
            before.st_mtime_ns,
            before.st_size,
            before.st_mode,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_mtime_ns,
            after.st_size,
            after.st_mode,
        ):
            raise StateConflict("public archive changed while inventorying")
        entries.append(
            ArtifactEntry(
                path=relative,
                bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                executable=bool(after.st_mode & stat.S_IXUSR),
            )
        )
    if not entries or len(entries) > MAX_ENTRIES:
        raise StateConflict("public archive file count is outside its bound")
    identity = [
        {
            "path": entry.path,
            "bytes": entry.bytes,
            "sha256": entry.sha256,
            "executable": entry.executable,
        }
        for entry in entries
    ]
    identity_bytes = json.dumps(
        identity,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return ArtifactManifest(
        schema_version=1,
        artifact_sha256=hashlib.sha256(identity_bytes).hexdigest(),
        entries=tuple(entries),
        total_bytes=sum(entry.bytes for entry in entries),
        created_at="content-addressed",
    )


def _artifact_file(run_root: Path, relative: str, label: str) -> bytes:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != relative:
        raise ContractError("%s path is invalid" % label)
    return _stable_file(run_root.joinpath(*pure.parts), label)


def _assert_bound_entries(
    root: Path,
    entries: Sequence[ArtifactEntry],
    *,
    label: str,
) -> None:
    """Verify every sealed historical byte while ignoring later unbound caches."""

    for entry in entries:
        content = _stable_file(
            root.joinpath(*PurePosixPath(entry.path).parts),
            "%s file %s" % (label, entry.path),
            allow_empty=True,
        )
        if (
            len(content) != entry.bytes
            or hashlib.sha256(content).hexdigest() != entry.sha256
        ):
            raise StateConflict("%s differs from its sealed manifest" % label)


def _write_contract(
    writer: PublicWriter,
    run_root: Path,
    source: str,
    destination: str,
    expected: Mapping[str, Any],
    label: str,
) -> bytes:
    content = _artifact_file(run_root, source, label)
    if _strict_json(content, label) != dict(expected):
        raise StateConflict("%s differs from the accepted contract" % label)
    writer(destination, content)
    return content


def _attempts_document(stage: str, attempts: list[dict[str, Any]]) -> bytes:
    return _canonical_json(
        {
            "schema_version": 1,
            "kind": "autonomous-workshop.public-stage-attempts",
            "stage": stage,
            "attempts": attempts,
            "privacy": (
                "Only sanitized content-addressed lifecycle outcomes are public. "
                "Provider events, prompts, transcripts, reasoning, and private "
                "host rejection receipts are intentionally excluded."
            ),
        }
    )


def _accepted_attempt(stage: str, identity: str, round_number: int) -> bytes:
    return _attempts_document(
        stage,
        [
            {
                "outcome": "accepted",
                "round": round_number,
                "subject_sha256": identity,
            }
        ],
    )


def _public_wish(
    writer: PublicWriter,
    wish: Wish,
    wish_sha256: str,
    *,
    title: str,
    summary: str,
    disclose_exact_wish: bool,
) -> None:
    objective_sha256 = hashlib.sha256(wish.objective.encode("utf-8")).hexdigest()
    public = {
        "schema_version": 1,
        "kind": "autonomous-workshop.public-wish-binding",
        "product_id": wish.product_id,
        "wish_sha256": wish_sha256,
        "objective_sha256": objective_sha256,
        "objective_disclosure": "exact" if disclose_exact_wish else "withheld",
        "public_title": title,
        "public_summary": summary,
    }
    if disclose_exact_wish:
        public["objective"] = wish.objective
        public["constraints"] = dict(wish.constraints)
        public["context"] = dict(wish.context)
    writer("wish/wish.json", _canonical_json(public))
    description = wish.objective if disclose_exact_wish else summary
    writer(
        "wish/WISH.md",
        ((
            "# Wish\n\n%s\n\n"
            "- Exact Wish SHA-256: `%s`\n"
            "- Objective disclosure: `%s`\n"
        )
        % (description, wish_sha256, public["objective_disclosure"])).encode("utf-8"),
    )


def _copy_made_tree(
    writer: PublicWriter,
    run_root: Path,
    made: NativeMade,
) -> None:
    product_root = run_root.joinpath(*PurePosixPath(made.product_root).parts)
    entries = {entry.path: entry for entry in made.product_manifest.entries}
    cad_prefix = PurePosixPath(made.cad_project_path)
    for relative, entry in sorted(entries.items()):
        source = product_root.joinpath(*PurePosixPath(relative).parts)
        content = _stable_file(
            source,
            "sealed Made file %s" % relative,
            allow_empty=True,
        )
        if len(content) != entry.bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
            raise StateConflict("sealed Made file differs from its manifest")
        pure = PurePosixPath(relative)
        if relative == "product.json":
            writer("make/product.json", content)
            continue
        if relative == made.cad_verification_path:
            writer("make/verification/CAD-GATE.json", content)
            continue
        try:
            cad_relative = pure.relative_to(cad_prefix)
        except ValueError:
            if pure.suffix.casefold() not in _MODEL_SUFFIXES:
                writer("make/product/%s" % pure.as_posix(), content)
            continue
        if any(part in _GENERATED_DIRECTORIES for part in cad_relative.parts):
            continue
        if not cad_relative.parts:
            continue
        if cad_relative.parts[0] == "measure":
            destination = "make/verification/reports/%s" % PurePosixPath(
                *cad_relative.parts[1:]
            ).as_posix()
        elif cad_relative.parts[0] == "snap":
            destination = "make/verification/renders/%s" % PurePosixPath(
                *cad_relative.parts[1:]
            ).as_posix()
        elif cad_relative.suffix.casefold() in _MODEL_SUFFIXES:
            destination = "make/models/cad/%s" % cad_relative.as_posix()
        else:
            destination = "make/source/cad/%s" % cad_relative.as_posix()
        writer(destination, content)


def _made_attempts(
    run_root: Path,
    *,
    made: NativeMade,
    assignment: NativeMatchAssignment,
    invented: NativeInvented,
) -> tuple[dict[int, NativeMade], bytes]:
    attempts = []
    proposals: dict[int, NativeMade] = {}
    for round_number in range(1, made.round + 1):
        source = "artifacts/make/r%04d/made.json" % round_number
        content = _artifact_file(
            run_root,
            source,
            "accepted Make round %d contract" % round_number,
        )
        proposal = NativeMade.from_mapping(
            _strict_json(content, "Make round %d contract" % round_number)
        )
        proposal.assert_context(
            assignment,
            invented,
            expected_round=round_number,
        )
        if round_number == made.round:
            proposal.validate_product_tree(run_root)
        else:
            product_root = run_root.joinpath(
                *PurePosixPath(proposal.product_root).parts
            )
            _assert_bound_entries(
                product_root,
                proposal.product_manifest.entries,
                label="historical Make round %d" % round_number,
            )
        proposals[round_number] = proposal
        attempts.append(
            {
                "outcome": (
                    "accepted" if round_number == made.round else "superseded"
                ),
                "round": round_number,
                "subject_sha256": proposal.made_sha256,
                "product_artifact_sha256": (
                    proposal.product_manifest.artifact_sha256
                ),
            }
        )
    if proposals.get(made.round) != made:
        raise StateConflict("accepted Made contract differs from its round history")
    return proposals, _attempts_document("make", attempts)


def _copy_playtest(
    writer: PublicWriter,
    run_root: Path,
    release: NativeRelease,
    made: NativeMade,
    made_attempts: Mapping[int, NativeMade],
) -> None:
    if release.schema_version == 3:
        return
    attempts = []
    playtested = None
    content = None
    for round_number in range(1, release.round + 1):
        source = "artifacts/playtest/r%04d/playtested.json" % round_number
        candidate_content = _artifact_file(
            run_root,
            source,
            "Playtested round %d contract" % round_number,
        )
        candidate = NativePlaytested.from_mapping(
            _strict_json(
                candidate_content,
                "Playtested round %d contract" % round_number,
            )
        )
        candidate_made = made_attempts.get(round_number)
        if candidate_made is None:
            raise StateConflict("Playtested history lacks its Made round")
        if (
            candidate.round != round_number
            or candidate.made_sha256 != candidate_made.made_sha256
            or candidate.product_artifact_sha256
            != candidate_made.product_manifest.artifact_sha256
            or candidate.blueprint_sha256 != candidate_made.blueprint_sha256
        ):
            raise StateConflict("Playtested history belongs to different Make inputs")
        if round_number == release.round:
            candidate.validate_evidence_tree(run_root, candidate_made)
        else:
            evidence_root = run_root.joinpath(
                *PurePosixPath(candidate.evidence_root).parts
            )
            _assert_bound_entries(
                evidence_root,
                candidate.evidence_manifest.entries,
                label="historical Playtest round %d" % round_number,
            )
        if round_number == release.round:
            playtested = candidate
            content = candidate_content
        failed_checks = sorted(
            check.check_id for check in candidate.checks if not check.passed
        )
        attempts.append(
            {
                "outcome": (
                    "accepted"
                    if round_number == release.round and candidate.verdict == "pass"
                    else (
                        "revision-requested"
                        if candidate.verdict != "pass"
                        else "superseded"
                    )
                ),
                "round": round_number,
                "subject_sha256": candidate.playtested_sha256,
                "verdict": candidate.verdict,
                "failed_checks": failed_checks,
            }
        )
    if playtested is None or content is None:
        raise StateConflict("accepted Playtested contract is unavailable")
    if (
        playtested.playtested_sha256 != release.playtested_sha256
        or playtested.made_sha256 != made.made_sha256
        or playtested.product_artifact_sha256 != made.product_manifest.artifact_sha256
    ):
        raise StateConflict("Playtested contract belongs to different Release inputs")
    playtested.validate_evidence_tree(run_root, made)
    writer("playtest/playtested.json", content)
    evidence_root = run_root.joinpath(*PurePosixPath(playtested.evidence_root).parts)
    for entry in playtested.evidence_manifest.entries:
        evidence = _stable_file(
            evidence_root.joinpath(*PurePosixPath(entry.path).parts),
            "sealed Playtest evidence %s" % entry.path,
            allow_empty=True,
        )
        if len(evidence) != entry.bytes or hashlib.sha256(evidence).hexdigest() != entry.sha256:
            raise StateConflict("Playtest evidence differs from its manifest")
        writer("playtest/evidence/%s" % entry.path, evidence)
    writer(
        "playtest/ATTEMPTS.json",
        _attempts_document("playtest", attempts),
    )


def write_public_workflow_archive(
    staging: Path,
    run_root: Path,
    *,
    made: NativeMade,
    release: NativeRelease,
    title: str,
    summary: str,
    publication: Mapping[str, Any],
    writer: PublicWriter,
    disclose_exact_wish: bool = False,
) -> None:
    """Write every workflow-shaped file except root README and MANIFEST."""

    wish_content = _artifact_file(
        run_root, "artifacts/wish/wish.json", "accepted Wish"
    )
    if hashlib.sha256(wish_content).hexdigest() != made.wish_sha256:
        raise StateConflict("Wish bytes differ from the Made binding")
    wish_document = _strict_json(wish_content, "Wish")
    wish = Wish(**wish_document)
    _public_wish(
        writer,
        wish,
        made.wish_sha256,
        title=title,
        summary=summary,
        disclose_exact_wish=disclose_exact_wish,
    )

    invent_root = run_root / "artifacts/invent"
    explicit_invent = (
        (invent_root / "assignment.json").exists()
        or (invent_root / "assignment.json").is_symlink()
        or (invent_root / "invented.json").exists()
        or (invent_root / "invented.json").is_symlink()
    )
    stage_root = (
        "artifacts/invent"
        if explicit_invent
        else "artifacts/make/r%04d" % made.round
    )
    assignment_content = _artifact_file(
        run_root,
        "%s/assignment.json" % stage_root,
        "accepted Match assignment",
    )
    assignment = NativeMatchAssignment.from_mapping(
        _strict_json(assignment_content, "Match assignment")
    )
    invented_content = _artifact_file(
        run_root,
        "%s/invented.json" % stage_root,
        "accepted Invented contract",
    )
    invented = NativeInvented.from_mapping(
        _strict_json(invented_content, "Invented contract")
    )
    invented.assert_context(assignment)
    made.assert_context(assignment, invented, expected_round=made.round)
    writer("match/assignment.json", assignment_content)
    writer(
        "match/ATTEMPTS.json",
        _accepted_attempt("match", assignment.assignment_sha256, 1),
    )
    if explicit_invent:
        writer("invent/invented.json", invented_content)
        writer(
            "invent/ATTEMPTS.json",
            _accepted_attempt("invent", invented.invented_sha256, 1),
        )
    else:
        # Spark intentionally has no Invent Goal.  Its compact concept is an
        # input sealed by the Make proposal, so preserve it under Make rather
        # than inventing a lifecycle stage that did not run.
        writer("make/invented.json", invented_content)

    made_attempts, make_attempts_document = _made_attempts(
        run_root,
        made=made,
        assignment=assignment,
        invented=invented,
    )
    writer(
        "make/made.json",
        _artifact_file(
            run_root,
            "artifacts/make/r%04d/made.json" % made.round,
            "accepted Made contract",
        ),
    )
    _copy_made_tree(writer, run_root, made)
    writer("make/ATTEMPTS.json", make_attempts_document)
    _copy_playtest(writer, run_root, release, made, made_attempts)

    _write_contract(
        writer,
        run_root,
        "artifacts/release/release.json",
        "release/release.json",
        release.to_dict(),
        "accepted Release contract",
    )
    package_root = run_root.joinpath(*PurePosixPath(release.package_root).parts)
    for entry in release.package_manifest.entries:
        content = _stable_file(
            package_root.joinpath(*PurePosixPath(entry.path).parts),
            "sealed Release file %s" % entry.path,
            allow_empty=True,
        )
        if len(content) != entry.bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
            raise StateConflict("Release file differs from its manifest")
        writer("release/%s" % entry.path, content)
    writer(
        "release/ATTEMPTS.json",
        _accepted_attempt("release", release.release_sha256, release.round),
    )
    writer("publication/PUBLICATION.json", _canonical_json(publication))

    # The root manifest deliberately excludes itself.  Its exact scope is
    # explicit, so every other byte remains content-addressed without a
    # recursive self-hash problem.
    manifest = build_public_archive_manifest(staging)
    writer(
        "MANIFEST.json",
        _canonical_json(
            {
                "schema_version": PUBLIC_ARCHIVE_SCHEMA_VERSION,
                "kind": "autonomous-workshop.public-toy-archive",
                "scope": "all files except MANIFEST.json and README.md",
                "artifact_manifest": manifest.to_dict(),
            }
        ),
    )


__all__ = [
    "PUBLIC_ARCHIVE_SCHEMA_VERSION",
    "build_public_archive_manifest",
    "write_public_workflow_archive",
]
