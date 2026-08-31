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
from workshop.concept import SealedConcept
from workshop.errors import ContractError, StateConflict
from workshop.invent.native import NativeInvented
from workshop.make.native import NativeMade
from workshop.make.revision import NativeMakeInventRevision
from workshop.match.native import NativeMatchAssignment
from workshop.playtest.native import NativePlaytested
from workshop.release.native import NativeRelease
from workshop.wish.contracts import Wish


PUBLIC_ARCHIVE_SCHEMA_VERSION = 4
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


def _public_concept_effect(value: Mapping[str, Any]) -> Mapping[str, Any]:
    expected = {
        "schema_version", "kind", "pre_render_concept_sha256",
        "sealed_concept_sha256", "profile_id", "profile_sha256", "roles",
        "concept_effect_sha256",
    }
    if set(value) != expected or value.get("schema_version") != 1 or value.get(
        "kind"
    ) != "autonomous-workshop.concept-image-effect":
        raise StateConflict("Concept effect fields are invalid")
    identity = {key: value[key] for key in expected - {"concept_effect_sha256"}}
    observed = hashlib.sha256(_canonical_json(identity)[:-1]).hexdigest()
    if value.get("concept_effect_sha256") != observed:
        raise StateConflict("Concept effect identity is invalid")
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


def _redact_public_local_paths(
    content: bytes,
    *,
    run_root: Path,
) -> tuple[bytes, tuple[str, ...]]:
    """Replace host-local absolute prefixes without interpreting artifact prose."""

    replacements = []
    candidates = (
        (
            str(Path(run_root).resolve(strict=True)).encode("utf-8"),
            b"<WORKSHOP_RUN>",
            "workshop-run-root",
        ),
        (
            str(Path.home().resolve()).encode("utf-8"),
            b"<HOME>",
            "home-directory",
        ),
    )
    public = content
    for private, placeholder, label in candidates:
        if private and private in public:
            public = public.replace(private, placeholder)
            replacements.append(label)
    return public, tuple(replacements)


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
    *,
    destination_root: str = "make",
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
            writer("%s/product.json" % destination_root, content)
            continue
        if relative == made.cad_verification_path:
            writer("%s/verification/CAD-GATE.json" % destination_root, content)
            continue
        try:
            cad_relative = pure.relative_to(cad_prefix)
        except ValueError:
            if pure.suffix.casefold() not in _MODEL_SUFFIXES:
                writer(
                    "%s/product/%s" % (destination_root, pure.as_posix()),
                    content,
                )
            continue
        if any(part in _GENERATED_DIRECTORIES for part in cad_relative.parts):
            continue
        if not cad_relative.parts:
            continue
        if cad_relative.parts[0] == "measure":
            destination = "%s/verification/reports/%s" % (
                destination_root,
                PurePosixPath(*cad_relative.parts[1:]).as_posix(),
            )
        elif cad_relative.parts[0] == "snap":
            destination = "%s/verification/renders/%s" % (
                destination_root,
                PurePosixPath(*cad_relative.parts[1:]).as_posix(),
            )
        elif cad_relative.suffix.casefold() in _MODEL_SUFFIXES:
            destination = "%s/models/cad/%s" % (
                destination_root,
                cad_relative.as_posix(),
            )
        else:
            destination = "%s/source/cad/%s" % (
                destination_root,
                cad_relative.as_posix(),
            )
        writer(destination, content)


def _resolve_concept_binding(
    run_root: Path,
    *,
    concept_sha256: str,
    concept_effect_sha256: str,
) -> tuple[Path, bytes, SealedConcept, bytes, Mapping[str, Any]]:
    candidates = []
    for path in sorted(
        (run_root / "artifacts/concept").glob(
            "r[0-9][0-9][0-9][0-9]/sealed.json"
        )
    ):
        content = _stable_file(path, "candidate sealed Concept")
        document = _strict_json(content, "candidate sealed Concept")
        if document.get("concept_sha256") == concept_sha256:
            candidates.append((path.parent, content, document))
    if len(candidates) != 1:
        raise StateConflict("public archive cannot resolve the Made Concept")
    concept_directory, sealed_content, sealed_document = candidates[0]
    sealed = SealedConcept.from_mapping(
        sealed_document,
        root=concept_directory / "concept",
    )
    sealed.validate_tree()
    effect_path = concept_directory / "effect.json"
    effect_content = _stable_file(effect_path, "accepted Concept effect")
    effect = _public_concept_effect(_strict_json(effect_content, "Concept effect"))
    if (
        sealed.concept_sha256 != concept_sha256
        or effect["concept_effect_sha256"] != concept_effect_sha256
        or effect["sealed_concept_sha256"] != sealed.concept_sha256
    ):
        raise StateConflict("public Concept differs from the Made binding")
    return concept_directory, sealed_content, sealed, effect_content, effect


def _invent_attempts(
    writer: PublicWriter,
    run_root: Path,
    *,
    made: NativeMade,
) -> tuple[
    dict[int, tuple[NativeMatchAssignment, NativeInvented]],
    bytes,
]:
    """Validate and preserve every sealed Invent attempt through Made's round."""

    attempts = []
    proposals: dict[int, tuple[NativeMatchAssignment, NativeInvented]] = {}
    contents: dict[int, tuple[bytes, bytes]] = {}
    sources: dict[int, bytes] = {}
    for round_number in range(1, made.round + 1):
        root = (
            "artifacts/invent"
            if round_number == 1
            else "artifacts/invent/r%04d" % round_number
        )
        assignment_path = "%s/assignment.json" % root
        invented_path = "%s/invented.json" % root
        assignment_file = run_root.joinpath(*PurePosixPath(assignment_path).parts)
        invented_file = run_root.joinpath(*PurePosixPath(invented_path).parts)
        present = (
            assignment_file.exists()
            or assignment_file.is_symlink()
            or invented_file.exists()
            or invented_file.is_symlink()
        )
        if not present:
            continue
        assignment_content = _artifact_file(
            run_root,
            assignment_path,
            "Invent round %d assignment" % round_number,
        )
        assignment = NativeMatchAssignment.from_mapping(
            _strict_json(
                assignment_content,
                "Invent round %d assignment" % round_number,
            )
        )
        invented_content = _artifact_file(
            run_root,
            invented_path,
            "Invent round %d contract" % round_number,
        )
        invented = NativeInvented.from_mapping(
            _strict_json(
                invented_content,
                "Invent round %d contract" % round_number,
            )
        )
        invented.assert_context(assignment)
        if assignment.wish_sha256 != made.wish_sha256:
            raise StateConflict("Invent history belongs to a different Wish")
        source_path = "%s/source.json" % root
        source_file = run_root.joinpath(*PurePosixPath(source_path).parts)
        if source_file.exists() or source_file.is_symlink():
            source_content = _artifact_file(
                run_root,
                source_path,
                "Invent round %d authored source" % round_number,
            )
            source = _strict_json(
                source_content,
                "Invent round %d authored source" % round_number,
            )
            invented_document = invented.to_dict()
            if (
                set(source)
                != {"selected_inventor_id", "ranking", "research", "concept"}
                or source["selected_inventor_id"]
                != assignment.selected_inventor_id
                or source["ranking"]
                != [item.to_dict() for item in assignment.ranking]
                or source["research"] != invented_document["research"]
                or source["concept"] != invented_document["concept"]
            ):
                raise StateConflict(
                    "Invent round %d authored source differs from its contracts"
                    % round_number
                )
            sources[round_number] = source_content
        proposals[round_number] = (assignment, invented)
        contents[round_number] = (assignment_content, invented_content)

    if not proposals:
        raise StateConflict("accepted Invent history is unavailable")
    accepted_round = max(proposals)
    accepted_assignment, accepted_invented = proposals[accepted_round]
    made.assert_context(
        accepted_assignment,
        accepted_invented,
        expected_round=made.round,
        expected_concept_sha256=made.concept_sha256,
        expected_concept_effect_sha256=made.concept_effect_sha256,
    )
    for round_number in sorted(proposals):
        assignment, invented = proposals[round_number]
        assignment_content, invented_content = contents[round_number]
        outcome = "accepted" if round_number == accepted_round else "superseded"
        attempts.append(
            {
                "outcome": outcome,
                "round": round_number,
                "assignment_sha256": assignment.assignment_sha256,
                "subject_sha256": invented.invented_sha256,
            }
        )
        if round_number != accepted_round:
            prefix = "invent/attempts/r%04d" % round_number
            writer("%s/assignment.json" % prefix, assignment_content)
            writer("%s/invented.json" % prefix, invented_content)
            if round_number in sources:
                writer("%s/source.json" % prefix, sources[round_number])
    assignment_content, invented_content = contents[accepted_round]
    writer("match/assignment.json", assignment_content)
    writer("invent/invented.json", invented_content)
    if accepted_round in sources:
        writer("invent/source.json", sources[accepted_round])
    return proposals, _attempts_document("invent", attempts)


def _made_attempts(
    run_root: Path,
    *,
    writer: PublicWriter,
    made: NativeMade,
    invent_attempts: Mapping[
        int, tuple[NativeMatchAssignment, NativeInvented]
    ],
) -> tuple[dict[int, NativeMade], bytes]:
    attempts = []
    proposals: dict[int, NativeMade] = {}
    for round_number in range(1, made.round + 1):
        available_invent_rounds = [
            candidate for candidate in invent_attempts if candidate <= round_number
        ]
        if not available_invent_rounds:
            raise StateConflict("Make history lacks its Invent inputs")
        assignment, invented = invent_attempts[max(available_invent_rounds)]
        source = "artifacts/make/r%04d/made.json" % round_number
        source_file = run_root.joinpath(*PurePosixPath(source).parts)
        revision_source = (
            "artifacts/make/r%04d/invent-revision-request.json" % round_number
        )
        revision_file = run_root.joinpath(*PurePosixPath(revision_source).parts)
        made_present = source_file.exists() or source_file.is_symlink()
        revision_present = revision_file.exists() or revision_file.is_symlink()
        if made_present == revision_present:
            raise StateConflict(
                "Make round %d must contain exactly one sealed outcome"
                % round_number
            )
        if revision_present:
            content = _artifact_file(
                run_root,
                revision_source,
                "Make round %d Invent-revision request" % round_number,
            )
            revision = NativeMakeInventRevision.from_mapping(
                _strict_json(
                    content,
                    "Make round %d Invent-revision request" % round_number,
                )
            )
            revision.assert_context(
                assignment,
                invented,
                expected_round=round_number,
            )
            revision.validate_evidence_tree(run_root)
            prefix = "make/attempts/r%04d" % round_number
            writer("%s/invent-revision-request.json" % prefix, content)
            evidence_root = run_root.joinpath(
                *PurePosixPath(revision.evidence_root).parts
            )
            for entry in revision.evidence_manifest.entries:
                evidence = _stable_file(
                    evidence_root.joinpath(*PurePosixPath(entry.path).parts),
                    "Make Invent-revision evidence %s" % entry.path,
                    allow_empty=True,
                )
                if (
                    len(evidence) != entry.bytes
                    or hashlib.sha256(evidence).hexdigest() != entry.sha256
                ):
                    raise StateConflict(
                        "Make Invent-revision evidence differs from its manifest"
                    )
                writer("%s/revision-evidence/%s" % (prefix, entry.path), evidence)
            authored_source = (
                "artifacts/make/r%04d/invent-revision-source.json"
                % round_number
            )
            authored_file = run_root.joinpath(*PurePosixPath(authored_source).parts)
            if authored_file.exists() or authored_file.is_symlink():
                authored = _artifact_file(
                    run_root,
                    authored_source,
                    "Make round %d Invent-revision authored source"
                    % round_number,
                )
                if _strict_json(authored, "Make Invent-revision authored source") != {
                    "feedback": [item.to_dict() for item in revision.feedback]
                }:
                    raise StateConflict(
                        "Make Invent-revision authored source differs from its request"
                    )
                writer("%s/invent-revision-source.json" % prefix, authored)
            attempts.append(
                {
                    "outcome": "invent-revision-requested",
                    "round": round_number,
                    "subject_sha256": revision.revision_request_sha256,
                    "evidence_artifact_sha256": (
                        revision.evidence_manifest.artifact_sha256
                    ),
                    "feedback_codes": sorted(
                        item.code for item in revision.feedback
                    ),
                }
            )
            continue
        content = _artifact_file(
            run_root,
            source,
            "accepted Make round %d contract" % round_number,
        )
        proposal = NativeMade.from_mapping(
            _strict_json(content, "Make round %d contract" % round_number)
        )
        if proposal.schema_version == 2:
            _resolve_concept_binding(
                run_root,
                concept_sha256=proposal.concept_sha256,
                concept_effect_sha256=proposal.concept_effect_sha256,
            )
        proposal.assert_context(
            assignment,
            invented,
            expected_round=round_number,
            expected_concept_sha256=proposal.concept_sha256,
            expected_concept_effect_sha256=proposal.concept_effect_sha256,
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
            prefix = "make/attempts/r%04d" % round_number
            writer("%s/made.json" % prefix, content)
            _copy_made_tree(
                writer,
                run_root,
                proposal,
                destination_root=prefix,
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
        source_file = run_root.joinpath(*PurePosixPath(source).parts)
        if not source_file.exists() and not source_file.is_symlink():
            continue
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
        else:
            prefix = "playtest/attempts/r%04d" % round_number
            writer("%s/playtested.json" % prefix, candidate_content)
            evidence_root = run_root.joinpath(
                *PurePosixPath(candidate.evidence_root).parts
            )
            for entry in candidate.evidence_manifest.entries:
                evidence = _stable_file(
                    evidence_root.joinpath(*PurePosixPath(entry.path).parts),
                    "historical Playtest evidence %s" % entry.path,
                    allow_empty=True,
                )
                if (
                    len(evidence) != entry.bytes
                    or hashlib.sha256(evidence).hexdigest() != entry.sha256
                ):
                    raise StateConflict(
                        "historical Playtest evidence differs from its manifest"
                    )
                writer("%s/evidence/%s" % (prefix, entry.path), evidence)
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

    raw_writer = writer
    sanitizations: list[dict[str, Any]] = []

    def writer(relative: str, content: bytes) -> None:
        public, replacements = _redact_public_local_paths(
            content,
            run_root=run_root,
        )
        if replacements:
            sanitizations.append(
                {
                    "path": relative,
                    "source_sha256": hashlib.sha256(content).hexdigest(),
                    "public_sha256": hashlib.sha256(public).hexdigest(),
                    "redactions": list(replacements),
                }
            )
        raw_writer(relative, public)

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
    if explicit_invent:
        invent_attempts, invent_attempts_document = _invent_attempts(
            writer,
            run_root,
            made=made,
        )
        accepted_invent_round = max(invent_attempts)
        assignment, invented = invent_attempts[accepted_invent_round]
        writer("invent/ATTEMPTS.json", invent_attempts_document)
    else:
        # Spark intentionally has no Invent Goal.  Its compact concept is an
        # input sealed by the Make proposal, so preserve it under Make rather
        # than inventing a lifecycle stage that did not run.
        stage_root = "artifacts/make/r%04d" % made.round
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
        made.assert_context(
            assignment,
            invented,
            expected_round=made.round,
            expected_concept_sha256=made.concept_sha256,
            expected_concept_effect_sha256=made.concept_effect_sha256,
        )
        writer("match/assignment.json", assignment_content)
        writer("make/invented.json", invented_content)
        invent_attempts = {made.round: (assignment, invented)}

    writer(
        "match/ATTEMPTS.json",
        _accepted_attempt(
            "match",
            assignment.assignment_sha256,
            max(invent_attempts),
        ),
    )

    if made.schema_version == 2:
        (
            concept_directory,
            sealed_content,
            sealed,
            effect_content,
            effect,
        ) = _resolve_concept_binding(
            run_root,
            concept_sha256=made.concept_sha256,
            concept_effect_sha256=made.concept_effect_sha256,
        )
        concept_prefix = concept_directory.relative_to(run_root).as_posix()
        copied = bool(disclose_exact_wish)
        writer(
            "concept/BINDING.json",
            _canonical_json(
                {
                    "schema_version": 1,
                    "kind": "autonomous-workshop.public-concept-binding",
                    "concept_sha256": sealed.concept_sha256,
                    "concept_effect_sha256": effect["concept_effect_sha256"],
                    "exact_source_and_images_copied": copied,
                    "claims": (
                        "Byte identity and role completeness only; no aesthetic, "
                        "buildability, Playtest, manufacture, or delivery claim."
                    ),
                }
            ),
        )
        if copied:
            writer("concept/pre-render.json", _artifact_file(
                run_root, "%s/pre-render.json" % concept_prefix,
                "accepted pre-render Concept",
            ))
            writer("concept/sealed.json", sealed_content)
            writer("concept/effect.json", effect_content)
            for entry in sealed.source.source_manifest.entries:
                writer(
                    "concept/source/%s" % entry.path,
                    _stable_file(
                        sealed.root.joinpath(*PurePosixPath(entry.path).parts),
                        "Concept source %s" % entry.path,
                    ),
                )
            for entry in sealed.image_manifest.entries:
                writer(
                    "concept/images/%s" % entry.path,
                    _stable_file(
                        sealed.root.joinpath(*PurePosixPath(entry.path).parts),
                        "Concept image %s" % entry.path,
                    ),
                )

    made_attempts, make_attempts_document = _made_attempts(
        run_root,
        writer=writer,
        made=made,
        invent_attempts=invent_attempts,
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

    if sanitizations:
        raw_writer(
            "SANITIZATION.json",
            _canonical_json(
                {
                    "schema_version": 1,
                    "kind": "autonomous-workshop.public-archive-sanitization",
                    "files": sanitizations,
                    "policy": (
                        "Host-local absolute path prefixes are replaced with "
                        "stable placeholders. Source and public hashes preserve "
                        "an auditable one-way projection without disclosing the "
                        "operator machine layout."
                    ),
                }
            ),
        )

    # The root manifest deliberately excludes itself.  Its exact scope is
    # explicit, so every other byte remains content-addressed without a
    # recursive self-hash problem.
    manifest = build_public_archive_manifest(staging)
    raw_writer(
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
