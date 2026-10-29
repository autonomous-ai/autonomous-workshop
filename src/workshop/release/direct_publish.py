"""Stage a CAD project built outside Workshop as a Spark-shaped publication.

A direct publication applies only the host-owned Factory effect of Release to
a project that never ran Wish, Make or Release. This module is the
deterministic half: it reads a CAD project directory or a packed public toy
archive, and writes the same Made tree shape and schema-4 Release carrier that
Spark publishes (ADR 0061), so the unchanged Factory adapter can import,
publish and read it back. It runs no gate, authors no copy beyond what the
caller supplies, and records that no Workshop lifecycle ran. See
``docs/PUBLISH_DIRECT.md``.
"""

from __future__ import annotations

import hashlib
import json
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional, Sequence

from workshop.artifacts import ArtifactManifest, build_artifact_manifest
from workshop.contributors.manifest import load_manifest
from workshop.contributors.taste import load_taste_header
from workshop.errors import ContractError
from workshop.make.contracts import Made
from workshop.release.native import (
    NATIVE_RELEASE_PLAYTEST_OMISSION_PATH,
    NATIVE_RELEASE_PRODUCT_PATH,
    make_output_release_product,
    playtest_omission_record,
)
from workshop.release.public_archive import (
    PUBLIC_ARCHIVE_SCHEMA_VERSION,
    build_public_archive_manifest,
)


DIRECT_PUBLISH_KIND = "workshop.direct-publish"
PUBLIC_TOY_ARCHIVE_KIND = "autonomous-workshop.public-toy-archive"
PUBLIC_TOY_ARCHIVE_SCOPE = "all files except MANIFEST.json and README.md"
# Factory's importer ranks this conventional root name above part solids,
# and the adapter keeps exactly one root STEP in the handoff.
MADE_PRIMARY_PATH = "assembled.step"
MADE_CAD_ROOT = "cad"
MAX_TITLE_CHARACTERS = 300
# The inverse of the toy archive's Made-tree projection.
_ARCHIVE_LAYOUT = (
    ("make/source/cad/", ""),
    ("make/models/cad/", ""),
    ("make/verification/reports/", "measure/"),
    ("make/verification/renders/", "snap/"),
)
_ARCHIVE_METADATA = frozenset(("MANIFEST.json", "README.md", "SANITIZATION.json"))
_WORKSHOP_RUN_MARKERS = ("wish", "match", "invent", "release", "make/made.json", "make/product")
# Reference and concept images are the owner's working material, not a
# listing asset; the Spark carrier likewise never ships Wish references.
_DROPPED_TOP_DIRECTORIES = {"ref": "reference material is not published"}
# The owner's request, agent transcripts and whatever was studied alongside
# them (another designer's model, comparison scripts). The toy-archive packer
# drops them before staging, so they are never published and never part of
# the bytes gate evidence binds.
_WORKING_DIRECTORIES = frozenset(("inputs", "transcripts"))
_WORKING_MATERIAL = "working material is not published"
_DROPPED_DIRECTORIES = frozenset(("__cadgen__", "__pycache__"))
# ADR 0062: STEP is the only geometry format Workshop ships.
_MESH_SUFFIXES = frozenset(
    (".stl", ".3mf", ".glb", ".gltf", ".obj", ".ply", ".amf", ".gcode", ".bgcode")
)
_PRODUCT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PRINTABLE = re.compile(r"^PRINTABLE\s*=\s*True\s*$", re.MULTILINE)
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_HOST_PATH = re.compile(rb"(?:/Users|/home)/[^/\s\"'<>`)]+/")
_TEXT_SUFFIXES = frozenset((".py", ".md", ".txt", ".json", ".csv", ".toml", ".yaml", ".yml"))
_STEP_SIGNATURE = b"ISO-10303-21"
# A likeness mask from an image-derived verify_project measures 1.0 here and
# a shaded render 0.00-0.18; the toy-archive publish wrapper uses the same line.
MAX_COVER_NEUTRAL_FRACTION = 0.9


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def cover_neutral_fraction(content: bytes) -> float:
    """Share of the cover's pixels that are neutral grey, black or white."""

    import io

    from PIL import Image, ImageChops

    with Image.open(io.BytesIO(content)) as image:
        red, green, blue = image.convert("RGB").split()
    spread = ImageChops.subtract(
        ImageChops.lighter(ImageChops.lighter(red, green), blue),
        ImageChops.darker(ImageChops.darker(red, green), blue),
    )
    histogram = spread.histogram()
    return sum(histogram[:4]) / sum(histogram)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def readme_summary(content: bytes) -> tuple[Optional[str], Optional[str]]:
    """Return a README's first ``#`` heading and its first prose paragraph."""

    title: Optional[str] = None
    paragraph: list[str] = []
    for line in content.decode("utf-8", "replace").splitlines():
        stripped = line.strip()
        if title is None and stripped.startswith("# "):
            title = stripped[2:].strip()
            continue
        if stripped.startswith("#") or stripped.startswith("!["):
            if paragraph:
                break
            continue
        if not stripped:
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    return title, " ".join(paragraph) or None


@dataclass(frozen=True)
class DirectSource:
    """One project's publishable files, keyed by their CAD-project path."""

    kind: str
    root: Path
    files: Mapping[str, Path]
    dropped: tuple[tuple[str, str], ...]
    readme: Optional[bytes]
    archive_sha256: Optional[str] = None
    publication: Optional[Mapping[str, Any]] = None
    # Every project file the build reads, including ones that stay local
    # (``ref/``); derived caches and working material are left out.
    inputs: Mapping[str, Path] = field(default_factory=dict)

    def host_path_files(self) -> list[str]:
        """Text files that still name a machine's home directory."""

        return [
            path for path, source in sorted(self.files.items())
            if PurePosixPath(path).suffix.casefold() in _TEXT_SUFFIXES
            and _HOST_PATH.search(source.read_bytes())
        ]

    def entry_step(self) -> str:
        """Name the one ``PRINTABLE = True`` entry's STEP, or refuse."""

        printable = sorted(
            path[: -len(".py")]
            for path, source in self.files.items()
            if "/" not in path
            and path.endswith(".step.py")
            and _PRINTABLE.search(source.read_text(encoding="utf-8", errors="replace"))
        )
        if len(printable) != 1:
            raise ContractError(
                "pass --primary-step: %d top-level entries declare PRINTABLE = True (%s)"
                % (len(printable), ", ".join(printable) or "none")
            )
        return printable[0]


def _classify(relative: str) -> Optional[str]:
    """Return why a CAD-project file stays local, or None to keep it."""

    pure = PurePosixPath(relative)
    # A cache is dropped whole, lock files and all, before anything else.
    if _DROPPED_DIRECTORIES & {part.casefold() for part in pure.parts[:-1]}:
        return "derived cache"
    if len(pure.parts) > 1 and pure.parts[0] in _WORKING_DIRECTORIES:
        return _WORKING_MATERIAL
    if any(part.startswith(".") for part in pure.parts):
        raise ContractError("hidden file in the project: %s" % relative)
    if pure.suffix.casefold() in _MESH_SUFFIXES:
        raise ContractError(
            "mesh output is not publishable (STEP only, ADR 0062): %s" % relative
        )
    if len(pure.parts) > 1 and pure.parts[0] in _DROPPED_TOP_DIRECTORIES:
        return _DROPPED_TOP_DIRECTORIES[pure.parts[0]]
    return None


def _regular_files(root: Path) -> list[tuple[str, Path]]:
    files = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ContractError("symlink in the project: %s" % relative)
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ContractError("special file in the project: %s" % relative)
        files.append((relative, path))
    return files


def _select(
    pairs: Sequence[tuple[str, Path]],
) -> tuple[dict[str, Path], list[tuple[str, str]], dict[str, Path]]:
    kept: dict[str, Path] = {}
    dropped: list[tuple[str, str]] = []
    inputs: dict[str, Path] = {}
    for relative, path in pairs:
        if relative in inputs:
            raise ContractError("two archive files map to one project path: %s" % relative)
        reason = _classify(relative)
        if reason not in ("derived cache", _WORKING_MATERIAL):
            inputs[relative] = path
        if reason is not None:
            dropped.append((relative, reason))
        else:
            kept[relative] = path
    return kept, dropped, inputs


def load_cad_project(root: Path) -> DirectSource:
    """Read a CAD project in its own layout (``snap/``, ``measure/``, sources)."""

    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ContractError("--cad-dir must be a directory")
    files, dropped, inputs = _select(_regular_files(root))
    readme = files.get("README.md")
    return DirectSource(
        kind="cad-project",
        root=root,
        files=files,
        dropped=tuple(dropped),
        readme=readme.read_bytes() if readme is not None else None,
        inputs=inputs,
    )


def load_public_toy_archive(root: Path) -> DirectSource:
    """Verify a packed toy archive against its manifest and map it back.

    Only the ``make/`` projection a CAD-project pack writes is accepted; an
    archive projected from a Workshop run already has its own Release and is
    published through ``workshop publish``, not here.
    """

    root = Path(root).resolve(strict=True)
    try:
        document = json.loads((root / "MANIFEST.json").read_bytes())
    except (OSError, ValueError) as exc:
        raise ContractError("archive MANIFEST.json is unreadable") from exc
    if (
        not isinstance(document, Mapping)
        or document.get("kind") != PUBLIC_TOY_ARCHIVE_KIND
        or document.get("schema_version") != PUBLIC_ARCHIVE_SCHEMA_VERSION
        or document.get("scope") != PUBLIC_TOY_ARCHIVE_SCOPE
    ):
        raise ContractError("not a schema 4 public toy archive")
    observed = build_public_archive_manifest(root).to_dict()
    if observed != document.get("artifact_manifest"):
        recorded = {
            entry.get("path"): entry
            for entry in (document.get("artifact_manifest") or {}).get("entries", [])
            if isinstance(entry, Mapping)
        }
        current = {entry["path"]: entry for entry in observed["entries"]}
        changed = sorted(
            path for path in recorded.keys() | current.keys()
            if recorded.get(path) != current.get(path)
        )
        raise ContractError(
            "archive differs from its MANIFEST.json: %s" % ", ".join(map(str, changed[:20]))
        )
    for marker in _WORKSHOP_RUN_MARKERS:
        if (root / marker).exists():
            raise ContractError(
                "archive was projected from a Workshop run (%s); publish it with "
                "`workshop publish`" % marker
            )
    publication = None
    pairs: list[tuple[str, Path]] = []
    for entry in observed["entries"]:
        path = entry["path"]
        if path in _ARCHIVE_METADATA:
            continue
        if path == "publication/PUBLICATION.json":
            try:
                publication = json.loads((root / path).read_bytes())
            except ValueError as exc:
                raise ContractError("archive publication record is malformed") from exc
            continue
        mapped = next(
            (target + path[len(prefix):] for prefix, target in _ARCHIVE_LAYOUT if path.startswith(prefix)),
            None,
        )
        if mapped is None:
            raise ContractError("archive file outside the CAD projection: %s" % path)
        pairs.append((mapped, root / path))
    files, dropped, inputs = _select(sorted(pairs))
    readme = files.get("README.md")
    return DirectSource(
        kind="public-toy-archive",
        root=root,
        files=files,
        dropped=tuple(dropped),
        readme=readme.read_bytes() if readme is not None else None,
        archive_sha256=observed["artifact_sha256"],
        publication=publication if isinstance(publication, Mapping) else None,
        inputs=inputs,
    )


# --------------------------------------------------------------------- evidence
#
# A direct publication needs a fresh passing print-gate run of the exact bytes
# it publishes. autonomous-product-to-cad's ``verify_project --fresh
# --print-gates`` writes STEP (with a wall-clock header) and a Markdown record
# that binds no bytes, so the publish tool runs it, parses the record it just
# wrote, and binds the result to the hashes of every source and STEP file in
# this evidence file. The file travels in ``measure/``, so a packed archive
# carries it, and any later change to a source or STEP makes it stale.

EVIDENCE_PATH = "measure/direct-publish-evidence.json"
EVIDENCE_KIND = "workshop.direct-publish-evidence"
PIPELINE_RECORD_PATH = "measure/verification-pipeline.md"
VERIFY_ARGUMENTS = ("--fresh", "--print-gates")
PRINT_GATES = ("check_mesh", "check_overhang", "check_thickness")
_SUBJECT_SUFFIXES = frozenset((".py", ".step", ".stp"))
_RECORD_ROW = re.compile(r"^\|\s*\d+\s*\|\s*`(?P<command>.*)`\s*\|\s*(?P<status>[^|]+?)\s*\|")
_GATE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]{0,127}$")


def evidence_subject(source: DirectSource) -> dict[str, Any]:
    """Hash every source and STEP file the build reads, renders and reports aside.

    ``measure/*.json`` manifests (mounts, motion, power) are gate inputs and
    count; the evidence file itself does not.
    """

    files = []
    for path, location in sorted(source.inputs.items()):
        pure = PurePosixPath(path)
        if pure.parts[0] == "snap" or path == EVIDENCE_PATH:
            continue
        suffix = pure.suffix.casefold()
        manifest = pure.parts[0] == "measure" and suffix == ".json"
        if suffix not in _SUBJECT_SUFFIXES and not manifest:
            continue
        files.append({"path": path, "sha256": hashlib.sha256(location.read_bytes()).hexdigest()})
    if not any(entry["path"].endswith((".step", ".stp")) for entry in files):
        raise ContractError("the project has no STEP to bind evidence to")
    return {"sha256": hashlib.sha256(_canonical_json(files)).hexdigest(), "files": files}


def parse_pipeline_record(text: str) -> list[dict[str, Any]]:
    """Read the newest run's rows from ``verification-pipeline.md``.

    Each row becomes its gate (the script's name, or ``measure/<audit>`` for a
    local audit), the entry it measured, and ``pass``, ``fail`` or
    ``skipped``. Anything but ``rc=0`` or ``skipped`` is a failure: a refusal,
    an interrupted gate, or an ``accepted-fail`` the verifier let through.
    """

    newest = text.split("\n---\n", 1)[0]
    rows = []
    for line in newest.splitlines():
        match = _RECORD_ROW.match(line.strip())
        if match is None:
            continue
        command, status = match.group("command"), match.group("status").strip()
        words = command.split("  #", 1)[0].split()
        gate, target = None, None
        if command.startswith("delete cache "):
            gate = "delete-cache"
        elif len(words) == 1 or "#" in command:
            gate = words[0] if words else "unknown"
        else:
            for index, word in enumerate(words):
                name = PurePosixPath(word).name
                if "python" in name and index + 1 < len(words):
                    continue
                parent = PurePosixPath(word).parent.name
                gate = ("measure/" + name) if parent == "measure" else name
                target = next(
                    (PurePosixPath(rest).name for rest in words[index + 1:] if rest.endswith(".step.py")),
                    None,
                )
                break
        result = "pass" if status == "rc=0" else "skipped" if status == "skipped" else "fail"
        rows.append({"gate": gate or "unknown", "target": target, "status": status, "result": result})
    if not rows:
        raise ContractError("the verification record has no gate rows")
    return rows


def build_evidence(
    source: DirectSource,
    *,
    record: bytes,
    exit_code: int,
    arguments: Sequence[str],
    verifier_sha256: str,
    recorded_at: str,
) -> dict[str, Any]:
    """The evidence document for one verifier run on ``source``'s current bytes."""

    return {
        "schema_version": 1,
        "kind": EVIDENCE_KIND,
        "verifier": {
            "name": "autonomous-product-to-cad skills/cad/scripts/verify_project",
            "sha256": verifier_sha256,
        },
        "arguments": list(arguments),
        "exit_code": int(exit_code),
        "recorded_at": recorded_at,
        "record_sha256": hashlib.sha256(record).hexdigest(),
        "gates": parse_pipeline_record(record.decode("utf-8", "replace")),
        "subject": evidence_subject(source),
    }


@dataclass(frozen=True)
class KnownGateFailure:
    """One owner-declared gate failure that may not stop publication."""

    gate: str
    reason: str

    @classmethod
    def parse(cls, value: str) -> "KnownGateFailure":
        gate, separator, reason = value.partition(":")
        gate, reason = gate.strip(), reason.strip()
        if not separator or not _GATE.fullmatch(gate) or not reason:
            raise ContractError("--known-gate-failure must be GATE:REASON, e.g. check_thickness:<why>")
        return cls(gate, reason)

    def to_dict(self) -> dict[str, str]:
        return {"gate": self.gate, "reason": self.reason}


@dataclass(frozen=True)
class EvidenceStatus:
    """Whether the publication's exact bytes carry acceptable gate evidence."""

    state: str  # "pass", "missing", "stale" or "fail"
    problems: tuple[str, ...]
    declared: tuple[KnownGateFailure, ...]
    document: Optional[Mapping[str, Any]]

    @property
    def acceptable(self) -> bool:
        return self.state == "pass"

    def summary(self) -> Optional[dict[str, Any]]:
        """What the publication records about its evidence."""

        if self.document is None or not self.acceptable:
            return None
        return {
            "kind": EVIDENCE_KIND,
            "subject_sha256": self.document["subject"]["sha256"],
            "verifier_sha256": self.document["verifier"]["sha256"],
            "arguments": list(self.document["arguments"]),
            "recorded_at": self.document["recorded_at"],
            "exit_code": self.document["exit_code"],
            "known_gate_failures": [failure.to_dict() for failure in self.declared],
        }


def evaluate_evidence(
    source: DirectSource, known_failures: Sequence[KnownGateFailure] = ()
) -> EvidenceStatus:
    """Accept only a fresh run of both flags whose every failure is declared."""

    declared = tuple(known_failures)
    if len({failure.gate for failure in declared}) != len(declared):
        raise ContractError("declare each known gate failure once")
    location = source.files.get(EVIDENCE_PATH)
    if location is None:
        return EvidenceStatus("missing", ("no %s; run with --verify" % EVIDENCE_PATH,), declared, None)
    try:
        document = json.loads(location.read_bytes())
        if document.get("kind") != EVIDENCE_KIND or document.get("schema_version") != 1:
            raise ValueError("kind")
        recorded = document["subject"]
        gates = list(document["gates"])
        arguments = list(document["arguments"])
        exit_code = document["exit_code"]
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ContractError("%s is malformed" % EVIDENCE_PATH) from exc
    current = evidence_subject(source)
    if recorded.get("sha256") != current["sha256"]:
        before = {entry["path"]: entry["sha256"] for entry in recorded.get("files", [])}
        after = {entry["path"]: entry["sha256"] for entry in current["files"]}
        changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
        return EvidenceStatus(
            "stale",
            ("sources or STEPs changed since verification: %s" % ", ".join(changed[:12]),),
            declared,
            document,
        )
    problems = []
    for flag in VERIFY_ARGUMENTS:
        if flag not in arguments:
            problems.append("verification ran without %s" % flag)
    ran = {row["gate"] for row in gates if row.get("result") != "skipped"}
    for gate in PRINT_GATES:
        if gate not in ran:
            problems.append("print gate %s did not run" % gate)
    failed = sorted({row["gate"] for row in gates if row.get("result") == "fail"})
    names = {failure.gate for failure in declared}
    for gate in failed:
        if gate not in names:
            problems.append("undeclared gate failure: %s" % gate)
    for gate in sorted(names - set(failed)):
        problems.append("declared failure %s did not fail; remove it" % gate)
    if exit_code != 0 and not failed:
        problems.append("verifier exited %s without a failing gate row" % exit_code)
    return EvidenceStatus("fail" if problems else "pass", tuple(problems), declared, document)


def inventor_name(inventors_root: Path, inventor_id: str) -> str:
    """Resolve a roster Inventor's display name; the id must exist."""

    if not isinstance(inventor_id, str) or _PRODUCT_ID.fullmatch(inventor_id) is None:
        raise ContractError("--inventor must be a canonical inventor id")
    folder = Path(inventors_root) / inventor_id
    if not (folder / "inventor.json").is_file():
        raise ContractError("no Inventor %r under %s" % (inventor_id, inventors_root))
    if load_manifest(folder / "inventor.json").inventor_id != inventor_id:
        raise ContractError("inventor.json id differs from its folder %s" % inventor_id)
    return load_taste_header(folder).name


@dataclass(frozen=True)
class DirectPublishProvenance:
    """Stands where a Wish would: what was published, and that nothing ran.

    ``FactoryReleaseWriter`` records ``to_dict()`` as the ``wish`` member of
    ``workshop-product-facts.json``. A direct publication has no Wish, so the
    record says so instead of inventing one.
    """

    product_id: str
    source_kind: str
    source_name: str
    source_artifact_sha256: Optional[str]
    evidence: Optional[Mapping[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": DIRECT_PUBLISH_KIND,
            "product_id": self.product_id,
            "wish": None,
            "workshop_lifecycle": "not-run",
            "source": {
                "kind": self.source_kind,
                "name": self.source_name,
                "artifact_sha256": self.source_artifact_sha256,
            },
            "evidence": None if self.evidence is None else dict(self.evidence),
        }


@dataclass(frozen=True)
class _InventorName:
    name: str


@dataclass(frozen=True)
class DirectPublishContext:
    """The context ``FactoryReleaseWriter`` reads, for a direct publication."""

    made: Made
    wish: DirectPublishProvenance
    taste: _InventorName
    public_title: Optional[str] = None
    token_usage: Optional[Mapping[str, Any]] = None
    cover_render: Optional[bytes] = None

    def assert_current(self) -> None:
        self.made.assert_current()


@dataclass(frozen=True)
class DirectPublication:
    """A staged Made tree and sealed Release carrier, ready for the adapter."""

    context: DirectPublishContext
    release_root: Path
    release_manifest: ArtifactManifest
    page: Mapping[str, Any]
    primary_source: str
    cover_path: str


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
    path.chmod(0o644)


def _text_list(values: Sequence[str], label: str) -> list[str]:
    result = []
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ContractError("%s entries must be non-empty trimmed text" % label)
        result.append(value)
    return result


def stage_direct_publication(
    source: DirectSource,
    workspace: Path,
    *,
    product_id: str,
    inventor_display_name: str,
    primary_step: str,
    title: str,
    summary: str,
    what_arrives: Sequence[str] = (),
    limitations: Sequence[str] = (),
    evidence: Optional[Mapping[str, Any]] = None,
) -> DirectPublication:
    """Write ``made/`` and ``release/`` under an empty private ``workspace``.

    The Made tree is ``product.json`` (title, summary and any owner-supplied
    lists), the primary STEP as ``assembled.step`` and every kept project file
    under ``cad/``. The carrier is derived exactly as Spark derives it.
    """

    workspace = Path(workspace)
    if not workspace.is_absolute() or not workspace.is_dir() or any(workspace.iterdir()):
        raise ContractError("direct publication workspace must be an empty absolute directory")
    if _PRODUCT_ID.fullmatch(product_id or "") is None:
        raise ContractError("--product-id must be a lowercase kebab-case slug")
    for label, value in (("title", title), ("summary", summary)):
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ContractError("%s must be non-empty trimmed text" % label)
    if len(title) > MAX_TITLE_CHARACTERS:
        raise ContractError("title exceeds %d characters" % MAX_TITLE_CHARACTERS)
    if "/" in primary_step or not primary_step.endswith(".step"):
        raise ContractError("--primary-step must name a top-level .step file")
    primary = source.files.get(primary_step)
    if primary is None:
        raise ContractError("primary model %s is not in the project" % primary_step)
    primary_content = primary.read_bytes()
    if not primary_content.startswith(_STEP_SIGNATURE):
        raise ContractError("primary model %s is not a STEP file" % primary_step)
    cover = source.files.get("snap/iso.png")
    cover_content = cover.read_bytes() if cover is not None else b""
    if not cover_content.startswith(_PNG_SIGNATURE):
        raise ContractError("Factory needs snap/iso.png as the cover, and it must be a PNG")
    neutral = cover_neutral_fraction(cover_content)
    if neutral > MAX_COVER_NEUTRAL_FRACTION:
        raise ContractError(
            "snap/iso.png is a black-and-white likeness mask (%.0f%% neutral grey), "
            "not a shaded hero; render the cover again" % (neutral * 100)
        )
    covers = [path for path in source.files if PurePosixPath(path).parts[-2:] == ("snap", "iso.png")]
    if covers != ["snap/iso.png"]:
        raise ContractError("exactly one snap/iso.png may ship; found %s" % ", ".join(covers))

    facts: dict[str, Any] = {"title": title, "summary": summary}
    for name, values in (("what_arrives", what_arrives), ("limitations", limitations)):
        if values:
            facts[name] = _text_list(values, name)
    made_root = workspace / "made"
    made_root.mkdir()
    _write(made_root / "product.json", _canonical_json(facts) + b"\n")
    _write(made_root / MADE_PRIMARY_PATH, primary_content)
    for relative, path in sorted(source.files.items()):
        _write(made_root / MADE_CAD_ROOT / relative, path.read_bytes())
    made = Made.from_root(made_root, facts)

    entries = made.artifact_manifest.entries
    readmes = sorted(
        (entry for entry in entries if entry.bytes > 0 and PurePosixPath(entry.path).name == "README.md"),
        key=lambda entry: (entry.path != "README.md", entry.path),
    )
    document = readmes[0] if readmes else None
    page = make_output_release_product(
        facts,
        product_artifact_sha256=made.artifact_sha256,
        source_document=None if document is None else {
            "source_path": document.path, "sha256": document.sha256,
        },
    )
    release_root = workspace / "release"
    release_root.mkdir()
    _write(release_root / NATIVE_RELEASE_PRODUCT_PATH, _canonical_json(page))
    _write(
        release_root / NATIVE_RELEASE_PLAYTEST_OMISSION_PATH,
        _canonical_json(playtest_omission_record()),
    )
    if document is not None:
        content = (made_root / document.path).read_bytes()
        if hashlib.sha256(content).hexdigest() != document.sha256:
            raise ContractError("Made README changed while staging")
        _write(release_root / "README.md", content)

    context = DirectPublishContext(
        made=made,
        wish=DirectPublishProvenance(
            product_id=product_id,
            source_kind=source.kind,
            source_name=source.root.name,
            source_artifact_sha256=source.archive_sha256,
            evidence=evidence,
        ),
        taste=_InventorName(inventor_display_name),
    )
    return DirectPublication(
        context=context,
        release_root=release_root.resolve(strict=True),
        release_manifest=build_artifact_manifest(release_root, created_at="content-addressed"),
        page=page,
        primary_source=primary_step,
        cover_path=MADE_CAD_ROOT + "/snap/iso.png",
    )


__all__ = [
    "DIRECT_PUBLISH_KIND",
    "EVIDENCE_PATH",
    "EvidenceStatus",
    "KnownGateFailure",
    "PIPELINE_RECORD_PATH",
    "VERIFY_ARGUMENTS",
    "build_evidence",
    "evaluate_evidence",
    "evidence_subject",
    "parse_pipeline_record",
    "DirectPublication",
    "DirectPublishContext",
    "DirectPublishProvenance",
    "DirectSource",
    "MAX_COVER_NEUTRAL_FRACTION",
    "cover_neutral_fraction",
    "inventor_name",
    "load_cad_project",
    "load_public_toy_archive",
    "readme_summary",
    "slugify",
    "stage_direct_publication",
]
