"""What differs between the CAD skill the gate was written against and ours.

The imported gate calls this repository's locked `skills/cad`. That skill is a
pin of `peterat617/text-to-3d`; the upstream repository the gate came from
carries its own pin of the same skill, and the two are not the same tree. Six
files differ.

Design decision D5 records this as a compatibility task rather than an
assumption, and requires any behavioural difference to be answered in ABO's
adapter layer rather than by vendoring a second skill or moving
`skills/LOCK.json`. This module is that answer: it names each difference, says
what it actually does, and states the compensation ABO makes for it. The
characterization check in `tests/` proves the list is still exactly this list,
so a seventh difference appearing in a future skill bump fails rather than
passing unnoticed.

**Direction.** ABO's design text says this repository's skill is the newer pin.
It is not. Reading the two trees settles it: every difference below is
something the upstream tree *has* and the locked tree does not, and the locked
files carry the earlier timestamps. The port therefore runs against the older
of the two skills, which is the conservative direction — nothing ABO builds may
depend on a capability the locked skill does not have.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple

from config import workshop_root


# The one CAD-source idiom the locked skill understands more narrowly than the
# skill the gate was written against. ABO's generated CAD must stay inside it.
SUPPORTED_COMPOUND_CALL = "Compound"
UNSUPPORTED_COMPOUND_CALL = "compound"


DIFFERENCES: Tuple[Dict[str, str], ...] = (
    {
        "path": "scripts/verify_project",
        "difference": (
            "The upstream skill passes --write to `gen` when it verifies a "
            "project; the locked skill does not, so verifying does not itself "
            "write STEP artifacts."
        ),
        "behavioural": "yes",
        "compensation": (
            "ABO never relies on `verify_project` to produce geometry. Make "
            "invokes `gen ... --write` explicitly, exactly as the imported "
            "gate already does, so STEP is written by the call that is "
            "supposed to write it under either skill. The imported gate does "
            "not call `verify_project` at all."
        ),
    },
    {
        "path": "scripts/packages/cadgen/src/cadgen/catalog.py",
        "difference": (
            "The upstream skill skips `.agents`, `.claude`, `.codex` and "
            "`openspec` when it scans a project for CAD sources; the locked "
            "skill does not skip them."
        ),
        "behavioural": "yes",
        "compensation": (
            "This repository has an `openspec/` directory, so the difference "
            "is live rather than theoretical. ABO builds every revision inside "
            "an isolated product tree that contains CAD sources and nothing "
            "else, and runs every CAD call with that tree as the working "
            "directory, so no catalog scan is ever rooted where it could reach "
            "the repository's own `openspec/`."
        ),
    },
    {
        "path": "scripts/packages/cadgen/src/cadgen/metadata.py",
        "difference": (
            "The upstream skill recognizes a lowercase `compound` call — "
            "including the `assembly.compound()` method spelling — as a "
            "multi-body compound; the locked skill recognizes only `Compound`."
        ),
        "behavioural": "yes",
        "observed": (
            "This one is live rather than theoretical, and the imported tree "
            "proves it: `harness/fixtures/cad_project/fixture.step.py` returns "
            "`assembly.compound()`. Under the skill the gate was written "
            "against that is a multi-body compound; under this repository's "
            "locked skill it is not classified as one. The imported fixture "
            "project therefore cannot be used unchanged as a characterization "
            "subject against the locked skill — and it is vendored, so it is "
            "not edited to make it fit."
        ),
        "compensation": (
            "ABO's generated CAD sources use `Compound` and never the "
            "lowercase spelling. `assert_cad_source_supported` enforces it on "
            "every source Make writes, so a source that would build under the "
            "upstream skill and silently mis-classify under ours is refused at "
            "the point it is written rather than discovered as a topology "
            "finding later. ABO's own STEP fixture, not the imported one, is "
            "what its offline manufacturing checks measure."
        ),
    },
    {
        "path": "scripts/packages/cadgen/src/cadgen/step_targets.py",
        "difference": (
            "The upstream skill resolves an explicit `<name>.step.py` target "
            "directly from the path; the locked skill falls back to a catalog "
            "scan of the project."
        ),
        "behavioural": "no",
        "compensation": (
            "Both resolve the same target to the same STEP file for a project "
            "laid out as ABO lays one out — one generator per part, named for "
            "the part, at the project root. The locked skill scans more to get "
            "there, which costs time and nothing else, and the isolated "
            "product tree keeps that scan small."
        ),
    },
    {
        "path": "scripts/inspect/inspect_refs/inspect.py",
        "difference": (
            "The upstream skill threads an already-resolved STEP target into "
            "entry-context loading; the locked skill resolves it again."
        ),
        "behavioural": "no",
        "compensation": (
            "Plumbing downstream of the `step_targets.py` difference. The "
            "resolved target is the same either way; only the number of times "
            "it is computed differs."
        ),
    },
    {
        "path": "requirements.txt",
        "difference": (
            "The upstream skill declares `scipy` explicitly, noting that the "
            "mesh and thickness gates import it while cadgen's own metadata "
            "does not declare it. The locked skill declares only cadgen."
        ),
        "behavioural": "yes",
        "compensation": (
            "ABO declares `scipy` in its own `pyproject.toml`. The locked "
            "skill is not edited and `skills/LOCK.json` is not touched; the "
            "dependency the gate actually needs is declared by the thing that "
            "needs it."
        ),
    },
)

DIFFERING_PATHS: Tuple[str, ...] = tuple(item["path"] for item in DIFFERENCES)


class CadCompatibilityError(RuntimeError):
    """ABO produced CAD the locked skill would read differently."""


def locked_skill_root() -> Path:
    return workshop_root() / "skills" / "cad"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locked_skill_fingerprint() -> Dict[str, str]:
    """The locked skill's digest for each file known to differ.

    Recorded rather than asserted: when the skill is bumped these move, and the
    characterization check says so instead of silently continuing to claim a
    comparison that was made against different bytes.
    """

    root = locked_skill_root()
    fingerprint = {}
    for relative in DIFFERING_PATHS:
        path = root / relative
        fingerprint[relative] = file_sha256(path) if path.is_file() else "absent"
    return fingerprint


def compare_trees(locked: Path, reference: Path) -> Tuple[str, ...]:
    """Every file that differs between two CAD skill trees.

    Generated caches are not source and are excluded; everything else counts,
    including a file present in one tree and absent from the other.
    """

    def inventory(root: Path) -> Dict[str, str]:
        found = {}
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            parts = path.relative_to(root).parts
            if any(part == "__pycache__" for part in parts) or path.suffix == ".pyc":
                continue
            found[path.relative_to(root).as_posix()] = file_sha256(path)
        return found

    ours, theirs = inventory(locked), inventory(reference)
    return tuple(
        sorted(
            name
            for name in set(ours) | set(theirs)
            if ours.get(name) != theirs.get(name)
        )
    )


def assert_cad_source_supported(source: str, label: str) -> None:
    """Refuse CAD source the locked skill would classify differently.

    The lowercase `compound(...)` spelling builds under the skill the gate was
    written against and is not recognized as a compound under ours. A part
    written that way would generate, pass generation, and then be measured as
    something other than what it is — which is exactly the class of difference
    D5 requires the adapter to catch rather than absorb.
    """

    if not isinstance(source, str):
        raise CadCompatibilityError("%s must be CAD source text" % label)
    for line in source.splitlines():
        stripped = line.split("#", 1)[0]
        if UNSUPPORTED_COMPOUND_CALL + "(" in stripped:
            raise CadCompatibilityError(
                "%s calls %s(...), which this repository's locked CAD skill "
                "does not recognize as a compound; write %s(...) instead"
                % (label, UNSUPPORTED_COMPOUND_CALL, SUPPORTED_COMPOUND_CALL)
            )


def characterization(reference_skill: Optional[Path] = None) -> Dict[str, object]:
    """The comparison, run as far as this machine allows.

    Without the upstream tree checked out there is nothing to compare against,
    and this reports the comparison as unmeasured rather than as agreement. An
    unrun check is not a pass here either.
    """

    record: Dict[str, object] = {
        "locked_skill": str(locked_skill_root()),
        "locked_fingerprint": locked_skill_fingerprint(),
        "known_differences": [dict(item) for item in DIFFERENCES],
        "behavioural_differences": [
            item["path"] for item in DIFFERENCES if item["behavioural"] == "yes"
        ],
    }
    if reference_skill is None or not Path(reference_skill).is_dir():
        record["tree_comparison"] = "unmeasured"
        record["tree_comparison_reason"] = (
            "the upstream-pinned CAD skill is not checked out on this machine; "
            "ABO does not vendor a second copy of it to make this check run"
        )
        return record
    observed = compare_trees(locked_skill_root(), Path(reference_skill))
    record["tree_comparison"] = "measured"
    record["observed_differing_paths"] = list(observed)
    record["unexpected_differing_paths"] = [
        name for name in observed if name not in DIFFERING_PATHS
    ]
    record["expected_but_identical_paths"] = [
        name for name in DIFFERING_PATHS if name not in observed
    ]
    return record


__all__ = [
    "CadCompatibilityError",
    "DIFFERENCES",
    "DIFFERING_PATHS",
    "SUPPORTED_COMPOUND_CALL",
    "UNSUPPORTED_COMPOUND_CALL",
    "assert_cad_source_supported",
    "characterization",
    "compare_trees",
    "file_sha256",
    "locked_skill_fingerprint",
    "locked_skill_root",
]
