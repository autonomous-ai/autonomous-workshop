"""The Approved Proof a seeded run starts from (ADR 0096).

`design-a-toy`'s `seal_proof.py` writes `APPROVAL.json` into the Contract
Proof's directory when the owner approves it. `workshop wish|fix
--seed-source DIR` hands that directory to the host, which validates it here
before sealing it into the run. Nothing here judges a shape: the host checks
exact bytes against what the approval recorded.

`seed_manifest` is the one definition of which files make up a seed tree;
`seal_proof.py` imports it, so the tree sealed in design and the tree checked
by the host are the same files.

ADR 0098: an approval records every check input its contract needs
(`check_inputs`, approval schema 2), so a seeded run's checks run as one
host batch. `validate_seed` is called only for a new launch (`workshop wish`
or `workshop fix --seed-source`); it refuses an approval sealed before ADR
0098, naming the missing inputs and the re-seal path. `workshop resume`
never calls it, so a run already started keeps its frozen protocol.
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
from workshop.wish.bought_list import strip_bought_block
from workshop.wish.fit_tables import approval_fit_table

APPROVAL_NAME = "APPROVAL.json"
APPROVAL_SCHEMA_VERSION = 4
# ADR 0102's 2026-11-11 amendment: approved assembly renders under
# approved/assembly/, superseded for new seals by ADR 0103's contract images.
ASSEMBLY_RENDERS_SCHEMA_VERSION = 3
# Approvals sealed before ADR 0102's 2026-11-11 amendment: no Approved Proof
# assembly renders; a run seeded from one keeps the reference-image look.
UNRENDERED_APPROVAL_SCHEMA_VERSION = 2
APPROVED_ASSEMBLY_DIR = "approved/assembly"
# Approvals sealed before ADR 0098: refused for a new launch, never read again
# for a run already started from one.
LEGACY_APPROVAL_SCHEMA_VERSION = 1
CRITIC_NAME = "CRITIC.json"
CHECKLIST_NAME = "CONCEPT-CHECKLIST.md"
APPROVED_DIR = "approved"
# ADR 0104 decision 5: the kit Manual the owner approved, shipped byte for byte.
KIT_MANUAL_FILE = APPROVED_DIR + "/kit-manual.pdf"
# Evidence and caches are never part of the seed, nor is the STEP each source
# builds beside itself (its approved copy is under approved/) or a build log.
EXCLUDED_DIRS = frozenset({"measure", "__cadgen__", "__pycache__", "compare", ".cache"})
EXCLUDED_TOP_SUFFIXES = frozenset({".step", ".log"})
# The project audits final verification runs (ADR 0096 pilot, B5): source
# the Proof writes under measure/, so the seed carries them.
SEED_AUDITS = ("measure/check_fit.py", "measure/check_spec.py", "measure/check_landmarks.py")
# The product the Proof writes (ADR 0098 owner decisions 1 and 3): the title
# and summary the owner sees at Stage 4, and the concept and research the
# run's Spark source is composed from.
SEED_PRODUCT = "SEED-PRODUCT.json"
SEED_PRODUCT_FIELDS = frozenset({"schema_version", "kind", "title", "summary", "concept", "research"})
SEED_PRODUCT_KIND = "workshop-seed-product"
CONCEPT_FIELDS = ("title", "summary", "interaction", "envelope_mm", "mechanisms", "components")
RESEAL_HINT = (
    "Re-seal it through design-a-toy: run `seal_proof.py inputs %s --contract CONTRACT.md` to list "
    "what is missing and which design step writes each, produce them in the Proof, then run "
    "`seal_proof.py seal` again. A run already started from this seed is not affected: continue it "
    "with `workshop resume`."
)


@dataclass(frozen=True)
class CheckInput:
    """One file a seeded batch reads that only design can write (ADR 0098
    decision 1)."""

    path: str
    when: str  # "always", "moving" or "powered"
    written_by: str


CHECK_INPUTS = (
    CheckInput(SEED_PRODUCT, "always",
               "the Proof: the product title and summary shown at Stage 4, and the concept and research "
               "(design-a-toy proof-prompt, \"Seed inputs\")"),
    CheckInput("snap/iso.png", "always",
               "the Proof's product render the owner approved at Stage 4"),
    CheckInput("snap/signature.png", "always",
               "the Proof's signature render the owner approved at Stage 4"),
    CheckInput("measure/motion.json", "moving",
               "the Proof's motion manifest, after it passes check_motion"),
    CheckInput("snap/MOTION-EVIDENCE.json", "moving",
               "motion_presentation.py on the Proof"),
    CheckInput("snap/motion.gif", "moving",
               "motion_presentation.py on the Proof"),
    CheckInput("snap/MOTION-REVIEW.json", "moving",
               "the Proof Critic's motion review of that presentation (motion-review-v1)"),
    CheckInput("measure/power.json", "powered",
               "the Proof's power report, after it passes check_power"),
    CheckInput("measure/mounts.json", "powered",
               "the Proof's mount rows, after they pass check_mount"),
    CheckInput("measure/bought-placements.json", "powered",
               "the Proof's Bought Part placements, after bought_model.py --build passes"),
)
# Check inputs under measure/ belong to the seed tree like the audits.
SEED_MEASURE_INPUTS = frozenset(item.path for item in CHECK_INPUTS if item.path.startswith("measure/"))


def contract_is_moving(design_contract: Mapping[str, Any]) -> bool:
    """A contract with a Coupled Interface moves: its motion is checked."""

    return any(isinstance(item, Mapping) and item.get("kind") == "coupled"
               for item in design_contract.get("interfaces") or ())


def contract_is_powered(design_contract: Mapping[str, Any]) -> bool:
    """A schema 10 contract that states its circuit (ADR 0095)."""

    return isinstance(design_contract.get("electrical"), Mapping)


def required_check_inputs(design_contract: Mapping[str, Any]) -> tuple:
    """The check inputs a seed for ``design_contract`` must carry."""

    applies = {"always": True, "moving": contract_is_moving(design_contract),
               "powered": contract_is_powered(design_contract)}
    return tuple(item for item in CHECK_INPUTS if applies[item.when])


def missing_check_inputs(directory: Path, design_contract: Mapping[str, Any]) -> tuple:
    """The required check inputs absent from the Proof at ``directory``."""

    directory = Path(directory)
    return tuple(item for item in required_check_inputs(design_contract)
                 if not (directory / item.path).is_file() or (directory / item.path).is_symlink())


def describe_check_inputs(items) -> str:
    return "; ".join("%s (written by %s)" % (item.path, item.written_by) for item in items)


def check_seed_product(content: bytes) -> Dict[str, Any]:
    """The Proof's SEED-PRODUCT.json, or ContractError naming what is wrong."""

    try:
        document = json.loads(content)
    except ValueError as exc:
        raise ContractError("seed: %s does not parse: %s" % (SEED_PRODUCT, exc)) from exc
    if not isinstance(document, dict) or set(document) != SEED_PRODUCT_FIELDS:
        raise ContractError("seed: %s must have exactly %s" % (SEED_PRODUCT, ", ".join(sorted(SEED_PRODUCT_FIELDS))))
    if document["schema_version"] != 1 or document["kind"] != SEED_PRODUCT_KIND:
        raise ContractError("seed: %s is not a schema 1 %s" % (SEED_PRODUCT, SEED_PRODUCT_KIND))
    for key in ("title", "summary"):
        if not isinstance(document[key], str) or not document[key].strip():
            raise ContractError("seed: %s needs a nonempty %s" % (SEED_PRODUCT, key))
    concept = document["concept"]
    if not isinstance(concept, dict) or set(concept) != set(CONCEPT_FIELDS):
        raise ContractError("seed: %s concept must have exactly %s" % (SEED_PRODUCT, ", ".join(CONCEPT_FIELDS)))
    if not isinstance(document["research"], dict) or not document["research"]:
        raise ContractError("seed: %s needs its research object" % SEED_PRODUCT)
    return document
CRITIC_VERDICTS = ("agree", "differences")


def check_critic_requirements(critic: Any, design_contract: Mapping[str, Any]) -> None:
    """The Proof Critic's per-requirement verdicts, or ContractError naming
    what is wrong. A seeded run carries them as its review's
    ``requirements`` rows, and build-a-toy's DETECT takes one row for each
    contract requirement id (a missing row is a ``requirement:<id>``
    finding). So ``critic["requirements"]`` must be a list of
    ``{id, verdict, note}`` with exactly one row for each contract
    requirement, each verdict ``agree`` or ``differences``."""

    rows = critic.get("requirements") if isinstance(critic, dict) else None
    if not isinstance(rows, list) or any(
        not isinstance(row, dict) or not isinstance(row.get("id"), str) for row in rows
    ):
        raise ContractError(
            "seed: %s has no per-requirement verdicts (`requirements: [{id, verdict, note}]`); "
            "a seeded run's DETECT would report every requirement missing" % CRITIC_NAME)
    expected = [item.get("id") for item in design_contract.get("requirements") or ()
                if isinstance(item, Mapping)]
    ids = [row["id"] for row in rows]
    problems = []
    repeated = sorted({item for item in ids if ids.count(item) > 1})
    if repeated:
        problems.append("repeats %s" % ", ".join(repeated))
    missing = [item for item in expected if item not in ids]
    if missing:
        problems.append("has no verdict for %s" % ", ".join(missing))
    unknown = [item for item in ids if item not in expected]
    if unknown:
        problems.append("names requirements the contract does not have: %s" % ", ".join(unknown))
    invalid = [row["id"] for row in rows if row.get("verdict") not in CRITIC_VERDICTS]
    if invalid:
        problems.append("gives %s a verdict that is not agree or differences" % ", ".join(invalid))
    if problems:
        raise ContractError("seed: %s %s" % (CRITIC_NAME, "; ".join(problems)))


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
    check_inputs: Mapping[str, str]
    # APPROVAL schema 3 (ADR 0102, 2026-11-11 amendment): the Approved Proof's
    # assembly at each assembly Reference Camera; None for a schema 2 seal.
    assembly_renders: Any = None
    # APPROVAL schema 4 (ADR 0103): the contract's Reference and Guide Images,
    # each a render of the approved Proof; None for an older seal.
    contract_images: Any = None
    # ADR 0104 decision 5: ``{file, sha256}`` of the owner-approved kit
    # Manual, or None when the seal carries none.
    kit_manual: Any = None

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
        if not path.is_file() or (any(part in EXCLUDED_DIRS for part in relative.parts[:-1])
                                  and relative.as_posix() not in SEED_AUDITS
                                  and relative.as_posix() not in SEED_MEASURE_INPUTS):
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


def validate_seed(directory: Path, geometry_ids, contract_sha256: str,
                  design_contract: Mapping[str, Any] = None) -> SeedApproval:
    """The Approved Proof at ``directory``, or ContractError naming the first
    reason it cannot seed a new run whose sealed contract hashes to
    ``contract_sha256`` and declares ``geometry_ids``. ``design_contract``,
    the sealed contract dict, decides which check inputs it must carry
    (ADR 0098); without it only the inputs every toy needs are required."""

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
    required = required_check_inputs(design_contract or {})
    if approval.get("schema_version") == LEGACY_APPROVAL_SCHEMA_VERSION:
        missing = missing_check_inputs(directory, design_contract or {}) or required
        raise ContractError(
            "seed: this Approved Proof was sealed before ADR 0098 (%s schema_version 1) and does not "
            "record the check inputs a new seeded run needs: %s. %s"
            % (APPROVAL_NAME, describe_check_inputs(missing), RESEAL_HINT % directory))
    if approval.get("schema_version") not in (UNRENDERED_APPROVAL_SCHEMA_VERSION, ASSEMBLY_RENDERS_SCHEMA_VERSION,
                                              APPROVAL_SCHEMA_VERSION):
        raise ContractError("seed: %s schema_version %r is not %d, %d or %d"
                            % (APPROVAL_NAME, approval.get("schema_version"), UNRENDERED_APPROVAL_SCHEMA_VERSION,
                               ASSEMBLY_RENDERS_SCHEMA_VERSION, APPROVAL_SCHEMA_VERSION))
    if approval.get("contract_sha256") != contract_sha256:
        raise ContractError("seed: the Approved Proof was sealed for another contract "
                            "(contract_sha256 differs from the sealed contract's)")
    try:
        approval_fit_table(approval)
    except ValueError as exc:
        # ADR 0105: a run builds the Proof with the table it was approved
        # with, so one it cannot name cannot seed a run.
        raise ContractError("seed: %s" % exc) from exc

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

    recorded = approval.get("check_inputs")
    if not isinstance(recorded, dict):
        raise ContractError("seed: %s records no check_inputs" % APPROVAL_NAME)
    absent = tuple(item for item in required if item.path not in recorded)
    if absent:
        raise ContractError("seed: the Approved Proof does not record the check inputs its contract needs: %s. %s"
                            % (describe_check_inputs(absent), RESEAL_HINT % directory))
    for name, digest in sorted(recorded.items()):
        if name not in sealed or sealed[name] != digest:
            raise ContractError("seed: check input %s is not in the manifest as sealed" % name)
    check_seed_product((directory / SEED_PRODUCT).read_bytes())
    batch = approval.get("batch")
    if not isinstance(batch, dict) or batch.get("ok") is not True or not isinstance(batch.get("record_sha256"), str):
        raise ContractError("seed: %s records no passing seeded batch dry run; %s"
                            % (APPROVAL_NAME, RESEAL_HINT % directory))

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
    renders = images = None
    if approval["schema_version"] == ASSEMBLY_RENDERS_SCHEMA_VERSION:
        renders = check_assembly_renders(approval.get("assembly_renders"), sealed, design_contract)
    if approval["schema_version"] == APPROVAL_SCHEMA_VERSION:
        images = check_contract_images(approval.get("contract_images"), design_contract)
    manual = check_kit_manual(approval.get("kit_manual"), sealed, design_contract) \
        if "kit_manual" in approval else None
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
        check_inputs=dict(recorded),
        assembly_renders=renders,
        contract_images=images,
        kit_manual=manual,
    )


def check_kit_manual(value: Any, sealed: Mapping[str, str], design_contract: Mapping[str, Any] = None) -> dict:
    """An approval's ``kit_manual`` (ADR 0104 decision 5), or ContractError:
    ``{file, sha256}`` naming the sealed ``approved/kit-manual.pdf`` of a kit
    contract."""

    if not isinstance(value, dict) or set(value) != {"file", "sha256"}:
        raise ContractError("seed: %s kit_manual is not {file, sha256}" % APPROVAL_NAME)
    if value["file"] != KIT_MANUAL_FILE or sealed.get(KIT_MANUAL_FILE) != value["sha256"]:
        raise ContractError("seed: the owner-approved kit Manual is not the sealed %s" % KIT_MANUAL_FILE)
    if design_contract is not None and not isinstance(design_contract.get("assembly_tree"), Mapping):
        raise ContractError("seed: the Approved Proof seals a kit Manual, but its contract is no kit")
    return dict(value)


def check_contract_images(images: Any, design_contract: Mapping[str, Any] = None) -> tuple:
    """A schema 4 approval's ``contract_images`` (ADR 0103), or
    ContractError: one record per Reference Image (``{file, kind:
    "reference", shows, camera, sha256}``) and per Guide Image (``{file,
    kind: "guide", shows, views, sha256}``), and, given the contract,
    exactly its references at their cameras and its guides, in order."""

    if not isinstance(images, list):
        raise ContractError("seed: %s records no contract_images" % APPROVAL_NAME)
    checked = []
    for item in images:
        kind = item.get("kind") if isinstance(item, dict) else None
        extra = "camera" if kind == "reference" else "views" if kind == "guide" else None
        if (extra is None or set(item) != {"file", "kind", "shows", "sha256", extra}
                or not _safe_relative(item["file"]) or "/" in item["file"]
                or not isinstance(item["sha256"], str) or _SHA256.fullmatch(item["sha256"]) is None):
            raise ContractError("seed: %s names an invalid contract image: %r" % (APPROVAL_NAME, item))
        if kind == "reference" and not _camera(item["camera"]):
            raise ContractError("seed: reference %s has no Reference Camera" % item["file"])
        if kind == "guide" and (not isinstance(item["views"], list) or not item["views"]
                                or not all(_camera(view) for view in item["views"])):
            raise ContractError("seed: guide %s records no camera" % item["file"])
        checked.append(dict(item))
    if design_contract is not None:
        wanted = [("reference", r.get("file"), [float(v) for v in r.get("camera") or ()])
                  for r in design_contract.get("references") or () if isinstance(r, Mapping)]
        wanted += [("guide", g.get("file"), None) for g in design_contract.get("guides") or ()
                   if isinstance(g, Mapping)]
        have = [(i["kind"], i["file"], [float(v) for v in i["camera"]] if i["kind"] == "reference" else None)
                for i in checked]
        if have != wanted:
            raise ContractError("seed: the Approved Proof's contract images are not the contract's references "
                                "at their cameras and its guides; re-seal the Proof with seal_proof.py")
    return tuple(checked)


def _camera(value: Any) -> bool:
    return (isinstance(value, list) and len(value) == 2
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value))


def check_launch_images(seed: "SeedApproval", given: Mapping[str, str]) -> None:
    """ADR 0103: a run seeded from a schema 4 seal seals exactly the Proof
    renders the seal recorded as the contract's Reference and Guide Images
    (``given``: file name -> sha256 of each ``--ref``/``--guide`` image).
    ContractError on a missing image or any other bytes, so a design-time AI
    image (archived under ``design-refs/``) never reaches the run."""

    if seed.contract_images is None:
        return
    recorded = {item["file"]: item["sha256"] for item in seed.contract_images}
    missing = sorted(set(recorded) - set(given))
    if missing:
        raise ContractError("seed: the Approved Proof's renders of %s were not passed; pass the contract's "
                            "images as the seal left them" % ", ".join(missing))
    other = sorted(name for name, digest in given.items() if name in recorded and digest != recorded[name])
    if other:
        raise ContractError("seed: %s is not the approved Proof render the seal recorded (sha256 differs); a "
                            "seeded run never reads a design-time image" % ", ".join(other))


def assembly_cameras(design_contract: Mapping[str, Any]) -> list:
    """``[AZ, EL]`` of every assembly reference of the contract, in order and
    once each: where a seal renders the Approved Proof's assembly (ADR 0102,
    2026-11-11 amendment)."""

    cameras = []
    for reference in (design_contract or {}).get("references") or ():
        if not isinstance(reference, Mapping) or reference.get("shows") != "assembly":
            continue
        camera = reference.get("camera")
        if (isinstance(camera, (list, tuple)) and len(camera) == 2
                and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in camera)):
            value = [float(camera[0]), float(camera[1])]
            if value not in cameras:
                cameras.append(value)
    return cameras


def assembly_render_name(camera) -> str:
    """The sealed file of the assembly render at ``camera``: render_review's
    own ``az{:g}_el{:g}.png`` name, under ``approved/assembly/``."""

    return "%s/az%g_el%g.png" % (APPROVED_ASSEMBLY_DIR, float(camera[0]), float(camera[1]))


def check_assembly_renders(renders: Any, sealed: Mapping[str, str],
                           design_contract: Mapping[str, Any] = None) -> tuple:
    """A schema 3 approval's ``assembly_renders``, or ContractError: each
    ``{file, camera, sha256}`` is in the manifest as sealed under its own
    camera's name, and, given the contract, they are its assembly reference
    cameras exactly."""

    if not isinstance(renders, list):
        raise ContractError("seed: %s records no assembly_renders" % APPROVAL_NAME)
    checked = []
    for item in renders:
        camera = item.get("camera") if isinstance(item, dict) else None
        if (not isinstance(item, dict) or set(item) != {"file", "camera", "sha256"} or not isinstance(camera, list)
                or len(camera) != 2 or not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                                               for v in camera)):
            raise ContractError("seed: %s names an invalid assembly render" % APPROVAL_NAME)
        if item["file"] != assembly_render_name(camera):
            raise ContractError("seed: assembly render %r is not named for its camera" % (item["file"],))
        if item["file"] not in sealed or sealed[item["file"]] != item["sha256"]:
            raise ContractError("seed: assembly render %s is not in the manifest as sealed" % item["file"])
        checked.append({"file": item["file"], "camera": [float(v) for v in camera], "sha256": item["sha256"]})
    if design_contract is not None and [item["camera"] for item in checked] != assembly_cameras(design_contract):
        raise ContractError("seed: the Approved Proof's assembly renders are not at the contract's assembly "
                            "Reference Cameras; re-seal the Proof with design-a-toy's seal_proof.py")
    return tuple(checked)


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
    # The Bought Parts block prices the design and changes no shape (ADR
    # 0095, 2026-11-07), so an owner may add it without re-sealing the Proof.
    text = strip_bought_block(text)
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
