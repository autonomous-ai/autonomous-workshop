"""The Approved Proof a seeded run starts from (ADR 0096).

`design-a-toy`'s `seal_proof.py` writes `APPROVAL.json` into the Contract
Proof's directory when the owner approves it. `workshop wish|fix
--seed-source DIR` hands that directory to the host, which validates it here
before sealing it into the run. Nothing here judges a shape: the host checks
exact bytes against what the approval recorded.

`seed_manifest` is the one definition of which files make up a seed tree;
`seal_proof.py` imports it, so the tree sealed in design and the tree checked
by the host are the same files.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping

from workshop.errors import ContractError

APPROVAL_NAME = "APPROVAL.json"
APPROVAL_SCHEMA_VERSION = 1
CRITIC_NAME = "CRITIC.json"
CHECKLIST_NAME = "CONCEPT-CHECKLIST.md"
APPROVED_DIR = "approved"
# Evidence and caches are never part of the seed, nor is the STEP each source
# builds beside itself (its approved copy is under approved/) or a build log.
EXCLUDED_DIRS = frozenset({"measure", "__cadgen__", "__pycache__", "compare", ".cache"})
EXCLUDED_TOP_SUFFIXES = frozenset({".step", ".log"})
MAX_APPROVAL_BYTES = 4 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class SeedApproval:
    """A validated Approved Proof."""

    approval_sha256: str
    manifest_sha256: str
    approved_by: str
    date: str
    files: Mapping[str, str]
    components: Mapping[str, Mapping[str, Any]]
    assembly_identity: str

    def frozen(self) -> Dict[str, str]:
        """What `MAKE-OPTIONS.json` schema 3 freezes."""

        return {"approval_sha256": self.approval_sha256, "manifest_sha256": self.manifest_sha256}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_manifest(root: Path) -> Dict[str, str]:
    """Relative path -> sha256 of every file of the seed tree under ``root``.
    ContractError on a symlink anywhere in the tree."""

    root = Path(root)
    files: Dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise ContractError("seed: %s is a symlink; the seed tree holds only plain files"
                                % relative.as_posix())
        if not path.is_file() or any(part in EXCLUDED_DIRS for part in relative.parts[:-1]):
            continue
        if relative.as_posix() == APPROVAL_NAME:
            continue
        if len(relative.parts) == 1 and path.suffix in EXCLUDED_TOP_SUFFIXES:
            continue
        files[relative.as_posix()] = _sha256(path)
    return files


def manifest_sha256(files: Mapping[str, str]) -> str:
    return hashlib.sha256(json.dumps(dict(files), sort_keys=True).encode()).hexdigest()


def _safe_relative(name: Any) -> bool:
    if not isinstance(name, str) or not name or "\\" in name:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and path.as_posix() == name


def validate_seed(directory: Path, geometry_ids, contract_sha256: str) -> SeedApproval:
    """The Approved Proof at ``directory``, or ContractError naming the first
    reason it cannot seed a run whose sealed contract hashes to
    ``contract_sha256`` and declares ``geometry_ids``."""

    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ContractError("seed: %s is not a directory" % directory)
    approval_path = directory / APPROVAL_NAME
    if approval_path.is_symlink() or not approval_path.is_file():
        raise ContractError("seed: %s has no %s; seal the Approved Proof with design-a-toy's "
                            "seal_proof.py first" % (directory, APPROVAL_NAME))
    raw = approval_path.read_bytes()
    if len(raw) > MAX_APPROVAL_BYTES:
        raise ContractError("seed: %s is too large" % APPROVAL_NAME)
    try:
        approval = json.loads(raw)
    except ValueError as exc:
        raise ContractError("seed: %s does not parse: %s" % (APPROVAL_NAME, exc)) from exc
    if not isinstance(approval, dict):
        raise ContractError("seed: %s must be a JSON object" % APPROVAL_NAME)
    if approval.get("schema_version") != APPROVAL_SCHEMA_VERSION:
        raise ContractError("seed: %s schema_version %r is not %d"
                            % (APPROVAL_NAME, approval.get("schema_version"), APPROVAL_SCHEMA_VERSION))
    if approval.get("contract_sha256") != contract_sha256:
        raise ContractError("seed: the Approved Proof was sealed for another contract "
                            "(contract_sha256 differs from the sealed contract's)")

    sealed = approval.get("manifest")
    if not isinstance(sealed, dict) or not sealed:
        raise ContractError("seed: %s has no manifest" % APPROVAL_NAME)
    for name, digest in sealed.items():
        if not _safe_relative(name) or name == APPROVAL_NAME:
            raise ContractError("seed: manifest path %r is outside the seed directory" % (name,))
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise ContractError("seed: manifest entry %s has no sha256" % name)
    if manifest_sha256(sealed) != approval.get("manifest_sha256"):
        raise ContractError("seed: the manifest does not hash to manifest_sha256")
    current = seed_manifest(directory)
    missing = sorted(set(sealed) - set(current))
    extra = sorted(set(current) - set(sealed))
    changed = sorted(name for name in set(sealed) & set(current) if sealed[name] != current[name])
    for label, names in (("missing", missing), ("extra", extra), ("changed", changed)):
        if names:
            raise ContractError("seed: %s file(s) against the approval's manifest: %s"
                                % (label, ", ".join(names[:8])))

    critic = approval.get("critic")
    for name, digest in ((CRITIC_NAME, critic.get("sha256") if isinstance(critic, dict) else None),
                         (CHECKLIST_NAME, approval.get("checklist_sha256"))):
        if name not in sealed:
            raise ContractError("seed: the Approved Proof has no %s" % name)
        if sealed[name] != digest:
            raise ContractError("seed: %s is not the one the owner approved" % name)

    components = approval.get("components")
    if not isinstance(components, dict) or not components:
        raise ContractError("seed: %s has no components" % APPROVAL_NAME)
    ids = set(geometry_ids)
    absent = sorted(ids - set(components))
    if absent:
        raise ContractError("seed: the contract's geometries have no approved Component: %s" % ", ".join(absent))
    unknown = sorted(set(components) - ids)
    if unknown:
        raise ContractError("seed: approved Components the contract does not declare: %s" % ", ".join(unknown))
    for role, component in sorted(components.items()):
        if not isinstance(component, dict):
            raise ContractError("seed: component %s is not an object" % role)
        for key in ("identity", "carry_key", "contract_rows"):
            if not isinstance(component.get(key), str) or not component[key]:
                raise ContractError("seed: component %s has no %s" % (role, key))
        step = component.get("approved_step")
        if step != "%s/part_%s.step" % (APPROVED_DIR, role) or step not in sealed:
            raise ContractError("seed: component %s has no approved STEP in the manifest" % role)
        if sealed[step] != component.get("step_sha256"):
            raise ContractError("seed: component %s's approved STEP is not the one sealed" % role)
    if not isinstance(approval.get("assembly_identity"), str) or not approval["assembly_identity"]:
        raise ContractError("seed: %s has no assembly_identity" % APPROVAL_NAME)
    approved_by = approval.get("approved_by")
    if not isinstance(approved_by, str) or not approved_by.strip():
        raise ContractError("seed: %s names no approved_by" % APPROVAL_NAME)
    date = approval.get("date")
    try:
        datetime.date.fromisoformat(date)
    except (TypeError, ValueError) as exc:
        raise ContractError("seed: %s date %r is not YYYY-MM-DD" % (APPROVAL_NAME, date)) from exc
    return SeedApproval(
        approval_sha256=hashlib.sha256(raw).hexdigest(),
        manifest_sha256=approval["manifest_sha256"],
        approved_by=approved_by,
        date=date,
        files=dict(sealed),
        components={role: dict(item) for role, item in components.items()},
        assembly_identity=approval["assembly_identity"],
    )


def copy_seed(seed: SeedApproval, source: Path, destination: Path) -> None:
    """Copy the approval and exactly its manifest's files from ``source`` into
    the new directory ``destination``, checking every copied byte."""

    destination = Path(destination)
    if destination.exists():
        raise ContractError("seed: %s already exists" % destination)
    destination.mkdir(parents=True)
    shutil.copyfile(Path(source) / APPROVAL_NAME, destination / APPROVAL_NAME)
    if _sha256(destination / APPROVAL_NAME) != seed.approval_sha256:
        raise ContractError("seed: %s changed while it was copied" % APPROVAL_NAME)
    for name, digest in sorted(seed.files.items()):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(source) / name, target)
        if _sha256(target) != digest:
            raise ContractError("seed: %s changed while it was copied" % name)


# Kept in step with ``NAME_LINE`` in ``workshop.make.contract_amendments``:
# build-a-toy prepends this line to the contract file a round seals.
NAME_LINE = re.compile(r"Name this (?:toy|revision) exactly: [^\n]*")


def seed_contract_sha256(text: str) -> str:
    """The sha256 the Approved Proof binds for a contract text: the bytes
    design sealed, without a leading build-a-toy name line (and the blank
    lines after it), which names a build, not its shape."""

    first, _, rest = text.partition("\n")
    if NAME_LINE.fullmatch(first):
        text = rest.lstrip("\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def seed_context(seed: SeedApproval, contract_sha256: str) -> Dict[str, str]:
    """What the Wish context records of its seed: the hashes the host binds
    and who approved it when, for the receipt and status."""

    return {"approval_sha256": seed.approval_sha256, "manifest_sha256": seed.manifest_sha256,
            "contract_sha256": contract_sha256, "approved_by": seed.approved_by, "date": seed.date}


def contract_geometry_ids(design_contract: Mapping[str, Any]):
    """The Unique Geometry ids of a sealed Design Contract dict."""

    return tuple(item.get("id") for item in design_contract.get("geometries") or ()
                 if isinstance(item, Mapping) and isinstance(item.get("id"), str))


def seed_files(seed: SeedApproval, directory: Path) -> Dict[str, bytes]:
    """The approval and its manifest's files, read and checked again, for
    the run's immutable seed/ input."""

    directory = Path(directory)
    files = {APPROVAL_NAME: (directory / APPROVAL_NAME).read_bytes()}
    if hashlib.sha256(files[APPROVAL_NAME]).hexdigest() != seed.approval_sha256:
        raise ContractError("seed: %s changed after it was validated" % APPROVAL_NAME)
    for name, digest in sorted(seed.files.items()):
        content = (directory / name).read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ContractError("seed: %s changed after it was validated" % name)
        files[name] = content
    return files
