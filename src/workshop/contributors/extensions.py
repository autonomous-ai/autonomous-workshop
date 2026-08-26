"""Static, content-addressed extension bundles for native Inventors.

An extension is data made available to the native coding-agent runtime.  It is
not an entrypoint, hook, stage worker, or permission grant.  The contributor
contract only identifies exact skill bytes; the product-run host decides when
the selected Inventor may read or invoke them and independently verifies every
stage outcome.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence, TYPE_CHECKING

from workshop.artifacts import ArtifactEntry, ArtifactManifest, assert_packable_content
from workshop.errors import ArtifactError, ManifestError

if TYPE_CHECKING:  # pragma: no cover - import cycle guard for type checkers
    from workshop.contributors.manifest import InventorManifest


INVENTOR_EXTENSION_KIND = "codex-skill"
MAX_INVENTOR_EXTENSIONS = 8
MAX_EXTENSION_FILES = 256
MAX_EXTENSION_FILE_BYTES = 4 * 1024 * 1024
MAX_EXTENSION_BYTES = 16 * 1024 * 1024
MAX_EXTENSION_SKILL_BYTES = 256 * 1024

_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ROOT_DIRECTORIES = frozenset(("assets", "references", "scripts"))
_ROOT_FILES = frozenset(
    ("SKILL.md", "README.md", "LICENSE", "LICENSE.md", "NOTICE", "NOTICE.md")
)
_FORBIDDEN_NAMES = frozenset(
    ("agents.md", "claude.md", "stage.json", "agent-outcome.json")
)
_RESERVED_SKILL_NAMES = frozenset(
    ("autonomous-workshop", "cad", "product-to-cad", "step-parts")
)


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ManifestError("Inventor extension values must be finite JSON") from exc


def _safe_name(value: Any, label: str) -> str:
    if not isinstance(value, str) or _NAME.fullmatch(value) is None:
        raise ManifestError("%s must match %s" % (label, _NAME.pattern))
    return value


def _safe_path(value: Any, label: str) -> PurePosixPath:
    candidate = PurePosixPath(value) if isinstance(value, str) else PurePosixPath(".")
    if (
        not isinstance(value, str)
        or not value
        or value in (".", "..")
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.as_posix() != value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ManifestError("%s must be a safe relative POSIX path" % label)
    return candidate


@dataclass(frozen=True)
class InventorExtension:
    """One exact Codex skill declared by a schema-v7 Inventor."""

    kind: str
    name: str
    path: str
    artifact_sha256: str

    def __post_init__(self) -> None:
        if self.kind != INVENTOR_EXTENSION_KIND:
            raise ManifestError(
                "Inventor extension kind must be %s" % INVENTOR_EXTENSION_KIND
            )
        _safe_name(self.name, "Inventor extension name")
        relative = _safe_path(self.path, "Inventor extension path")
        if relative.as_posix() != "skills/%s" % self.name:
            raise ManifestError(
                "Inventor extension path must be skills/<extension-name>"
            )
        if not isinstance(self.artifact_sha256, str) or _SHA256.fullmatch(
            self.artifact_sha256
        ) is None:
            raise ManifestError("Inventor extension artifact_sha256 is invalid")

    @classmethod
    def from_mapping(
        cls, value: Any, *, inventor_id: str
    ) -> "InventorExtension":
        expected = {"kind", "name", "path", "artifact_sha256"}
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ManifestError("Inventor extension fields are invalid")
        extension = cls(**dict(value))
        prefix = "%s-" % inventor_id
        if not extension.name.startswith(prefix) or extension.name == prefix:
            raise ManifestError(
                "Inventor extension name must begin with %s" % prefix
            )
        if extension.name in _RESERVED_SKILL_NAMES:
            raise ManifestError(
                "Inventor extension name collides with a Workshop skill"
            )
        return extension

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "name": self.name,
            "path": self.path,
            "artifact_sha256": self.artifact_sha256,
        }


def parse_inventor_extensions(
    value: Any, *, inventor_id: str
) -> tuple[InventorExtension, ...]:
    """Parse schema-v7 descriptors without inspecting or executing their trees."""

    if (
        not isinstance(value, list)
        or not 1 <= len(value) <= MAX_INVENTOR_EXTENSIONS
    ):
        raise ManifestError(
            "schema_version 7 extensions must contain 1 to %d records"
            % MAX_INVENTOR_EXTENSIONS
        )
    extensions = tuple(
        InventorExtension.from_mapping(item, inventor_id=inventor_id)
        for item in value
    )
    names = [item.name for item in extensions]
    paths = [item.path for item in extensions]
    if len(names) != len(set(names)) or len(paths) != len(set(paths)):
        raise ManifestError("Inventor extensions must have unique names and paths")
    if names != sorted(names):
        raise ManifestError("Inventor extensions must be sorted by name")
    return extensions


def _read_regular(path: Path, relative: PurePosixPath) -> tuple[bytes, os.stat_result]:
    try:
        expected = path.lstat()
    except OSError as exc:
        raise ManifestError(
            "cannot inspect Inventor extension file %s" % relative.as_posix()
        ) from exc
    if path.is_symlink() or not stat.S_ISREG(expected.st_mode):
        raise ManifestError(
            "Inventor extension entry must be a regular file: %s"
            % relative.as_posix()
        )
    if not 0 <= expected.st_size <= MAX_EXTENSION_FILE_BYTES:
        raise ManifestError(
            "Inventor extension file exceeds %d bytes: %s"
            % (MAX_EXTENSION_FILE_BYTES, relative.as_posix())
        )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ManifestError(
            "cannot safely open Inventor extension file %s" % relative.as_posix()
        ) from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
        ) != (expected.st_dev, expected.st_ino):
            raise ManifestError(
                "Inventor extension file changed while opening: %s"
                % relative.as_posix()
            )
        chunks = []
        observed = 0
        while True:
            chunk = os.read(
                descriptor,
                min(64 * 1024, MAX_EXTENSION_FILE_BYTES + 1 - observed),
            )
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > MAX_EXTENSION_FILE_BYTES:
                raise ManifestError(
                    "Inventor extension file exceeds its byte limit: %s"
                    % relative.as_posix()
                )
        after = os.fstat(descriptor)
        if (
            observed != opened.st_size
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ManifestError(
                "Inventor extension file changed while reading: %s"
                % relative.as_posix()
            )
        return b"".join(chunks), after
    finally:
        os.close(descriptor)


def _skill_frontmatter(content: bytes, *, expected_name: str) -> None:
    if not 1 <= len(content) <= MAX_EXTENSION_SKILL_BYTES:
        raise ManifestError(
            "Inventor extension SKILL.md must contain 1 to %d bytes"
            % MAX_EXTENSION_SKILL_BYTES
        )
    try:
        text = content.decode("utf-8")
    except UnicodeError as exc:
        raise ManifestError("Inventor extension SKILL.md must be UTF-8") from exc
    lines = text.splitlines()
    if len(lines) < 5 or lines[0] != "---":
        raise ManifestError(
            "Inventor extension SKILL.md requires strict name/description frontmatter"
        )
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ManifestError(
            "Inventor extension SKILL.md has no closing frontmatter delimiter"
        ) from exc
    if closing != 3:
        raise ManifestError(
            "Inventor extension SKILL.md frontmatter allows exactly name and description"
        )
    fields: dict[str, str] = {}
    for line in lines[1:closing]:
        if ":" not in line:
            raise ManifestError("Inventor extension SKILL.md frontmatter is invalid")
        key, raw = line.split(":", 1)
        value = raw.strip()
        if key not in ("name", "description") or key in fields or not value:
            raise ManifestError("Inventor extension SKILL.md frontmatter is invalid")
        if (
            len(value) > (127 if key == "name" else 1024)
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            raise ManifestError(
                "Inventor extension SKILL.md %s is not bounded text" % key
            )
        fields[key] = value
    if tuple(fields) != ("name", "description") or fields["name"] != expected_name:
        raise ManifestError(
            "Inventor extension SKILL.md name must match its manifest descriptor"
        )
    if not "\n".join(lines[closing + 1 :]).strip():
        raise ManifestError("Inventor extension SKILL.md requires instructions")


def fingerprint_extension_skill(
    skill_root: Path, *, expected_name: str
) -> ArtifactManifest:
    """Hash an exact skill tree without importing or executing contributor code."""

    _safe_name(expected_name, "Inventor extension skill name")
    requested = Path(skill_root)
    if not requested.is_absolute() or requested.is_symlink():
        raise ManifestError("Inventor extension skill root must be absolute and real")
    try:
        identity = requested.lstat()
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise ManifestError("Inventor extension skill root is unavailable") from exc
    if requested != root or not stat.S_ISDIR(identity.st_mode):
        raise ManifestError("Inventor extension skill root must be canonical")
    if root.name != expected_name:
        raise ManifestError("Inventor extension directory must match its skill name")

    relatives: list[PurePosixPath] = []
    for directory, dirnames, filenames in os.walk(str(root), followlinks=False):
        base = Path(directory)
        relative_base = base.relative_to(root)
        kept: list[str] = []
        for dirname in sorted(dirnames):
            child = base / dirname
            relative = PurePosixPath((relative_base / dirname).as_posix())
            if child.is_symlink() or not child.is_dir():
                raise ManifestError(
                    "Inventor extension contains a linked or special directory: %s"
                    % relative.as_posix()
                )
            if (
                dirname.startswith(".")
                or dirname.casefold() == "__pycache__"
                or any(ord(character) < 32 or ord(character) == 127 for character in dirname)
            ):
                raise ManifestError(
                    "Inventor extension contains a reserved directory: %s"
                    % relative.as_posix()
                )
            if relative_base == Path(".") and dirname not in _ROOT_DIRECTORIES:
                raise ManifestError(
                    "Inventor extension root directories must be assets, references, or scripts"
                )
            kept.append(dirname)
        dirnames[:] = kept
        for filename in sorted(filenames):
            absolute = base / filename
            relative = PurePosixPath((relative_base / filename).as_posix())
            if filename.startswith(".") or filename.casefold() in _FORBIDDEN_NAMES:
                raise ManifestError(
                    "Inventor extension contains a reserved file: %s"
                    % relative.as_posix()
                )
            if relative_base == Path(".") and filename not in _ROOT_FILES:
                raise ManifestError(
                    "Inventor extension root files are limited to SKILL.md and concise metadata"
                )
            try:
                file_identity = absolute.lstat()
            except OSError as exc:
                raise ManifestError(
                    "cannot inspect Inventor extension entry: %s" % relative.as_posix()
                ) from exc
            if absolute.is_symlink() or not stat.S_ISREG(file_identity.st_mode):
                raise ManifestError(
                    "Inventor extension entry must be a regular file: %s"
                    % relative.as_posix()
                )
            relatives.append(relative)
    relatives.sort(key=lambda item: item.as_posix())
    if not relatives or len(relatives) > MAX_EXTENSION_FILES:
        raise ManifestError(
            "Inventor extension must contain 1 to %d files" % MAX_EXTENSION_FILES
        )
    if PurePosixPath("SKILL.md") not in relatives:
        raise ManifestError("Inventor extension requires a root SKILL.md")

    entries = []
    contents: dict[str, bytes] = {}
    total_bytes = 0
    for relative in relatives:
        content, file_identity = _read_regular(
            root.joinpath(*relative.parts), relative
        )
        try:
            assert_packable_content(relative.as_posix(), content)
        except ArtifactError as exc:
            raise ManifestError(
                "Inventor extension contains excluded or credential-shaped content: %s"
                % relative.as_posix()
            ) from exc
        executable = bool(
            file_identity.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        )
        if executable and relative.parts[0] != "scripts":
            raise ManifestError(
                "only Inventor extension scripts may be executable: %s"
                % relative.as_posix()
            )
        total_bytes += len(content)
        if total_bytes > MAX_EXTENSION_BYTES:
            raise ManifestError(
                "Inventor extension exceeds %d total bytes" % MAX_EXTENSION_BYTES
            )
        entries.append(
            ArtifactEntry(
                path=relative.as_posix(),
                bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                executable=executable,
            )
        )
        contents[relative.as_posix()] = content
    _skill_frontmatter(contents["SKILL.md"], expected_name=expected_name)
    artifact_sha256 = hashlib.sha256(
        _canonical_json([asdict(entry) for entry in entries])
    ).hexdigest()
    return ArtifactManifest(
        schema_version=1,
        artifact_sha256=artifact_sha256,
        entries=tuple(entries),
        total_bytes=total_bytes,
        created_at="content-addressed",
    )


@dataclass(frozen=True)
class InventorExtensionBundle:
    """A descriptor paired with the exact, statically verified source tree."""

    extension: InventorExtension
    root: Path
    manifest: ArtifactManifest

    def __post_init__(self) -> None:
        if not isinstance(self.extension, InventorExtension):
            raise ManifestError("Inventor extension bundle requires a descriptor")
        requested = Path(self.root)
        if not requested.is_absolute() or requested.is_symlink() or not requested.is_dir():
            raise ManifestError("Inventor extension bundle root must be absolute and real")
        if not isinstance(self.manifest, ArtifactManifest):
            raise ManifestError("Inventor extension bundle requires an artifact manifest")
        if self.manifest.artifact_sha256 != self.extension.artifact_sha256:
            raise ManifestError("Inventor extension tree differs from its declared hash")
        object.__setattr__(self, "root", requested.resolve(strict=True))

    def to_binding(self) -> dict[str, Any]:
        return {
            **self.extension.to_dict(),
            "manifest": self.manifest.to_dict(),
        }


def load_inventor_extension_bundles(
    manifest: "InventorManifest",
) -> tuple[InventorExtensionBundle, ...]:
    """Rehash every declared extension and reject undeclared skill siblings."""

    extensions = tuple(getattr(manifest, "extensions", ()))
    if not extensions:
        return ()
    try:
        inventor_root = manifest.path.parent.resolve(strict=True)
    except OSError as exc:
        raise ManifestError("Inventor extension root is unavailable") from exc
    skills_root = inventor_root / "skills"
    if skills_root.is_symlink() or not skills_root.is_dir():
        raise ManifestError("schema_version 7 Inventor requires a real skills directory")
    try:
        children = tuple(sorted(skills_root.iterdir(), key=lambda item: item.name))
    except OSError as exc:
        raise ManifestError("cannot list Inventor extension skills") from exc
    expected = {item.name for item in extensions}
    observed = set()
    for child in children:
        if child.is_symlink() or not child.is_dir():
            raise ManifestError(
                "Inventor skills directory may contain only declared skill directories"
            )
        observed.add(child.name)
    if observed != expected:
        raise ManifestError(
            "Inventor skills directory differs from the declared extension inventory"
        )

    bundles = []
    for extension in extensions:
        skill_root = inventor_root.joinpath(*PurePosixPath(extension.path).parts)
        fingerprint = fingerprint_extension_skill(
            skill_root, expected_name=extension.name
        )
        bundles.append(InventorExtensionBundle(extension, skill_root, fingerprint))
    return tuple(bundles)


__all__ = [
    "INVENTOR_EXTENSION_KIND",
    "MAX_EXTENSION_BYTES",
    "MAX_EXTENSION_FILE_BYTES",
    "MAX_EXTENSION_FILES",
    "MAX_INVENTOR_EXTENSIONS",
    "InventorExtension",
    "InventorExtensionBundle",
    "fingerprint_extension_skill",
    "load_inventor_extension_bundles",
    "parse_inventor_extensions",
]
