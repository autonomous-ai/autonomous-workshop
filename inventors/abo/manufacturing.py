"""ABO's manufacturing measurement: deterministic, bound to what it measured.

`mechanical-test` and `print-test` come from measuring the exact geometry in the
revision — never from looking at a render. Every output is bound to a hash of
the sources it was computed from, so a measurement taken from geometry that has
since changed is detectable rather than merely stale.

The distinction that does the most work here is between a check that ran and
passed, a check that ran and failed, and a check that could not be run at all.
The imported gate already separates hard `fails` from owner-visible
`unmeasured`, and ABO keeps that separation with one added rule: an unmeasured
check is not a pass. A result whose slicer was never configured does not get to
pass on the strength of the checks that did run.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import config

EVALUATOR = "abo-manufacturing-gate"
EVALUATOR_VERSION = "1.0.0"

PASSED = "pass"
FAILED = "fail"
UNMEASURED = "unmeasured"

# A render is a picture of a thing, and a picture cannot settle whether a solid
# is closed, whether two parts foul, or whether a wall survives a nozzle.
IMAGE_SUFFIXES = frozenset((".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".glb"))

# What each result must cover. Naming them here means a check that was never
# even attempted is still reported, rather than quietly absent.
MECHANICAL_CHECKS: Tuple[str, ...] = (
    "solid-validity",
    "mesh-topology",
    "dimensions-against-brief",
    "interference-in-declared-poses",
    "clearance-at-declared-fits",
)
PRINT_CHECKS: Tuple[str, ...] = (
    "bed-fit",
    "minimum-wall-thickness",
    "overhang-and-bridging",
    "slicing-under-a-pinned-profile",
)

# Millimetres of tolerance between a built bounding box and the brief's stated
# dimension before the two are called different.
DIMENSION_TOLERANCE_MM = 0.5


class StaleEvidence(RuntimeError):
    """The geometry changed after this measurement was taken."""


@dataclass(frozen=True)
class Measurement:
    """One check: what it looked at, what it found, and whether it ran."""

    name: str
    status: str
    detail: str
    values: Mapping[str, Any] = field(default_factory=dict)
    parts: Sequence[str] = ()

    def __post_init__(self) -> None:
        if self.status not in (PASSED, FAILED, UNMEASURED):
            raise ValueError("a measurement is a pass, a fail, or unmeasured")

    @property
    def is_pass(self) -> bool:
        return self.status == PASSED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check": self.name,
            "status": self.status,
            "detail": self.detail,
            "values": dict(self.values),
            "parts": list(self.parts),
        }


def _unmeasured(name: str, reason: str) -> Measurement:
    return Measurement(name, UNMEASURED, reason)


# ---------------------------------------------------------------------------
# Binding to the sources
# ---------------------------------------------------------------------------


def cad_sources(made) -> Tuple[Path, ...]:
    """Every file the measurement is computed from, in a stable order."""

    root = Path(made.artifact_root)
    found = []
    for entry in sorted(made.artifact_manifest.entries, key=lambda item: item.path):
        path = root / entry.path
        if path.suffix.casefold() in IMAGE_SUFFIXES:
            # Deliberately excluded. A picture is not a source of a measurement,
            # and including one would let a re-render invalidate real geometry.
            continue
        found.append(path)
    return tuple(found)


def source_closure_sha256(made) -> str:
    """A digest of the exact bytes the measurement was computed from."""

    digest = hashlib.sha256()
    root = Path(made.artifact_root)
    for path in cad_sources(made):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def assert_sources_current(evidence: Mapping[str, Any], made) -> None:
    """Refuse evidence whose sources have since changed."""

    recorded = evidence.get("source_closure_sha256")
    observed = source_closure_sha256(made)
    if recorded != observed:
        raise StaleEvidence(
            "this measurement was computed from a source closure of %s and the "
            "revision now hashes to %s; a number measured from geometry that "
            "has since changed is not evidence about this build"
            % (recorded, observed)
        )


# ---------------------------------------------------------------------------
# The measurements
# ---------------------------------------------------------------------------


def _mesh_toolchain() -> Optional[str]:
    """Why geometry cannot be measured here, or `None` when it can."""

    try:
        import numpy  # noqa: F401
        import trimesh  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        return (
            "the mesh toolchain the locked CAD skill measures through is not "
            "installed (%s); solid validity, topology, dimensions, overhang and "
            "bridging cannot be computed" % exc
        )
    return None


def _part_files(made) -> Dict[str, Dict[str, Path]]:
    root = Path(made.artifact_root)
    built: Dict[str, Dict[str, Path]] = {}
    for key, entry in dict(made.product.get("cad", {})).items():
        files = {}
        for kind in ("source", "step", "mesh", "facts"):
            relative = entry.get(kind)
            if relative:
                files[kind] = root / relative
        built[key] = files
    return built


def measure_mechanical(made, brief) -> List[Measurement]:
    """Solidity, topology, dimensions, interference, and declared clearances."""

    parts = _part_files(made)
    blocked = _mesh_toolchain()
    measurements: List[Measurement] = []

    missing_step = sorted(key for key, files in parts.items() if "step" not in files)
    if missing_step:
        measurements.append(
            Measurement(
                "solid-validity",
                FAILED,
                "no STEP artifact was built for %s, so there is no solid to "
                "check" % ", ".join(missing_step),
                parts=missing_step,
            )
        )
    elif blocked:
        measurements.append(_unmeasured("solid-validity", blocked))
    else:
        measurements.append(_solid_validity(parts))

    if blocked:
        measurements.append(_unmeasured("mesh-topology", blocked))
        measurements.append(_unmeasured("dimensions-against-brief", blocked))
    else:
        measurements.append(_mesh_topology(parts))
        measurements.append(_dimensions(parts, brief))

    measurements.append(_interference(made, brief))
    if brief.fits is None:
        measurements.append(
            _unmeasured(
                "clearance-at-declared-fits",
                "the brief declares no fit, so there is no clearance to measure",
            )
        )
    elif blocked:
        measurements.append(_unmeasured("clearance-at-declared-fits", blocked))
    else:
        measurements.append(_clearance(parts, brief))
    return measurements


def _solid_validity(parts) -> Measurement:
    broken = []
    values = {}
    for key, files in sorted(parts.items()):
        mesh = files.get("mesh")
        if mesh is None or not mesh.is_file():
            broken.append(key)
            continue
        stats = _stats(mesh)
        values[key] = {"watertight": stats["watertight"], "bodies": stats["bodies"]}
        if not stats["watertight"]:
            broken.append(key)
    if broken:
        return Measurement(
            "solid-validity",
            FAILED,
            "not a closed solid: %s" % ", ".join(sorted(broken)),
            values,
            sorted(broken),
        )
    return Measurement(
        "solid-validity", PASSED, "every part is a closed solid", values
    )


def _mesh_topology(parts) -> Measurement:
    multi = []
    values = {}
    for key, files in sorted(parts.items()):
        mesh = files.get("mesh")
        if mesh is None or not mesh.is_file():
            return Measurement(
                "mesh-topology", FAILED, "no mesh was derived for %s" % key, parts=[key]
            )
        stats = _stats(mesh)
        values[key] = {"bodies": stats["bodies"], "volume_mm3": stats["volume_mm3"]}
        if stats["bodies"] > 1:
            multi.append(key)
    if multi:
        return Measurement(
            "mesh-topology",
            FAILED,
            "more than one disconnected body: %s" % ", ".join(sorted(multi)),
            values,
            sorted(multi),
        )
    return Measurement("mesh-topology", PASSED, "one body per part", values)


def _dimensions(parts, brief) -> Measurement:
    wrong = []
    values = {}
    for key, files in sorted(parts.items()):
        mesh = files.get("mesh")
        if mesh is None or not mesh.is_file():
            continue
        stated = list(brief.component(key).dimensions_mm)
        measured = _stats(mesh)["bbox_mm"]
        values[key] = {"stated_mm": stated, "measured_mm": measured}
        if any(
            abs(float(a) - float(b)) > DIMENSION_TOLERANCE_MM
            for a, b in zip(sorted(stated), sorted(measured))
        ):
            wrong.append(key)
    if wrong:
        return Measurement(
            "dimensions-against-brief",
            FAILED,
            "built geometry differs from the brief's millimetres by more than "
            "%.2f mm: %s" % (DIMENSION_TOLERANCE_MM, ", ".join(sorted(wrong))),
            values,
            sorted(wrong),
        )
    return Measurement(
        "dimensions-against-brief",
        PASSED,
        "every part matches the brief's stated dimensions",
        values,
    )


def _interference(made, brief) -> Measurement:
    """Do two parts occupy the same space in a pose the product declares?

    A pose is an axis-aligned placement of each part in one assembled
    arrangement. Where the product declares none there is nothing to measure,
    and that is reported as unmeasured rather than as an absence of
    interference — the parts were never put together to find out.
    """

    poses = dict(made.product.get("poses", {}) or {})
    if not poses:
        return _unmeasured(
            "interference-in-declared-poses",
            "the product declares no assembly pose, so no two parts were ever "
            "placed together; interference is unmeasured, not absent",
        )
    clashes = []
    values: Dict[str, Any] = {}
    for pose_name, placement in sorted(poses.items()):
        boxes = {}
        for key, origin in dict(placement).items():
            size = brief.component(key).dimensions_mm
            boxes[key] = (
                tuple(float(value) for value in origin),
                tuple(float(value) for value in size),
            )
        overlaps = []
        names = sorted(boxes)
        for index, first in enumerate(names):
            for second in names[index + 1 :]:
                if _overlaps(boxes[first], boxes[second]):
                    overlaps.append([first, second])
                    clashes.extend([first, second])
        values[pose_name] = {"parts": names, "overlapping": overlaps}
    if clashes:
        detail = "; ".join(
            "in pose %r: %s" % (name, ", ".join(" and ".join(pair) for pair in entry["overlapping"]))
            for name, entry in sorted(values.items())
            if entry["overlapping"]
        )
        return Measurement(
            "interference-in-declared-poses",
            FAILED,
            "parts occupy the same space where they must not — %s" % detail,
            values,
            sorted(set(clashes)),
        )
    return Measurement(
        "interference-in-declared-poses",
        PASSED,
        "no two parts intersect in any declared pose",
        values,
    )


def _overlaps(first, second) -> bool:
    """Two axis-aligned boxes, touching faces excluded."""

    (origin_a, size_a), (origin_b, size_b) = first, second
    for axis in range(3):
        low_a, high_a = origin_a[axis], origin_a[axis] + size_a[axis]
        low_b, high_b = origin_b[axis], origin_b[axis] + size_b[axis]
        if high_a <= low_b or high_b <= low_a:
            return False
    return True


def _clearance(parts, brief) -> Measurement:
    fits = dict(brief.fits or {})
    return Measurement(
        "clearance-at-declared-fits",
        UNMEASURED,
        "the declared fit (%s, %.2f mm clearance) needs the two mating parts "
        "posed together, and the product declares no pose to measure it in"
        % (fits.get("target"), float(fits.get("clearance_mm", 0.0))),
        {"declared": fits},
    )


def measure_print(made, brief, *, bed_mm: Optional[Sequence[float]] = None) -> List[Measurement]:
    """Bed fit, wall thickness, overhang and bridging, and slicing."""

    parts = _part_files(made)
    blocked = _mesh_toolchain()
    envelope = tuple(bed_mm or config.usable_bed_mm())
    measurements: List[Measurement] = []

    if blocked:
        measurements.append(_unmeasured("bed-fit", blocked))
        measurements.append(_unmeasured("overhang-and-bridging", blocked))
    else:
        measurements.append(_bed_fit(parts, envelope))
        measurements.append(_overhang(parts))

    measurements.append(_wall_thickness(brief))
    measurements.append(_slicing(parts))
    return measurements


def _bed_fit(parts, envelope) -> Measurement:
    oversize = []
    values = {"usable_bed_mm": list(envelope), "printer": config.PRINTER_NAME}
    for key, files in sorted(parts.items()):
        mesh = files.get("mesh")
        if mesh is None or not mesh.is_file():
            continue
        box = sorted(float(value) for value in _stats(mesh)["bbox_mm"])
        allowed = sorted(float(value) for value in envelope)
        values[key] = box
        if any(a > b for a, b in zip(box, allowed)):
            oversize.append(key)
    if oversize:
        return Measurement(
            "bed-fit",
            FAILED,
            "exceeds the %s usable envelope %s and is not declared as tiled: %s"
            % (
                config.PRINTER_NAME,
                " x ".join("%.0f" % value for value in envelope),
                ", ".join(sorted(oversize)),
            ),
            values,
            sorted(oversize),
        )
    return Measurement(
        "bed-fit", PASSED, "every part fits the configured usable envelope", values
    )


def _overhang(parts) -> Measurement:
    gate = config.load_harness("gate")
    bad = []
    values = {}
    for key, files in sorted(parts.items()):
        mesh = files.get("mesh")
        if mesh is None or not mesh.is_file():
            continue
        stats = _stats(mesh)
        values[key] = {
            "print_orientation": stats["print_orientation"],
            "overhang_pct": stats["overhang_pct"],
            "bridge_span_mm": stats["bridge_span_mm"],
        }
        if (
            stats["overhang_pct"] > gate.OVERHANG_FAIL_PCT
            or stats["bridge_span_mm"] > gate.BRIDGE_SPAN_MAX_MM
        ):
            bad.append(key)
    if bad:
        return Measurement(
            "overhang-and-bridging",
            FAILED,
            "unsupported overhang or bridge span beyond the configured limit: %s"
            % ", ".join(sorted(bad)),
            values,
            sorted(bad),
        )
    return Measurement(
        "overhang-and-bridging",
        PASSED,
        "every part prints within the overhang and bridging limits",
        values,
    )


def _wall_thickness(brief) -> Measurement:
    """Measured against the nozzle the profile pins, or reported unmeasured."""

    nozzle = os.environ.get("ABO_NOZZLE_MM", "").strip()
    if not nozzle:
        return _unmeasured(
            "minimum-wall-thickness",
            "no nozzle diameter is configured (ABO_NOZZLE_MM), so the brief's "
            "%.2f mm wall cannot be measured against what will actually print it"
            % brief.wall_mm,
        )
    try:
        diameter = float(nozzle)
    except ValueError:
        return _unmeasured(
            "minimum-wall-thickness", "ABO_NOZZLE_MM is not a number: %r" % nozzle
        )
    required = diameter * 2
    if brief.wall_mm < required:
        return Measurement(
            "minimum-wall-thickness",
            FAILED,
            "the brief's %.2f mm wall is thinner than two %.2f mm extrusions"
            % (brief.wall_mm, diameter),
            {"wall_mm": brief.wall_mm, "nozzle_mm": diameter},
        )
    return Measurement(
        "minimum-wall-thickness",
        PASSED,
        "the brief's %.2f mm wall carries at least two %.2f mm extrusions"
        % (brief.wall_mm, diameter),
        {"wall_mm": brief.wall_mm, "nozzle_mm": diameter},
    )


def _slicing(parts) -> Measurement:
    gate = config.load_harness("gate")
    sliced = {}
    for key, files in sorted(parts.items()):
        mesh = files.get("mesh")
        if mesh is None or not mesh.is_file():
            continue
        outcome = gate.slice_stl(mesh)
        if outcome.get("sliced") is None:
            return _unmeasured(
                "slicing-under-a-pinned-profile",
                "no slicer and profile are pinned (ORCASLICER_CLI, ORCA_PROFILE), "
                "so print time and material are unmeasured; this result does not "
                "pass on the strength of the checks that did run",
            )
        if not outcome.get("sliced"):
            return Measurement(
                "slicing-under-a-pinned-profile",
                FAILED,
                "slicing failed for %s: %s" % (key, outcome.get("error", "")),
                sliced,
                [key],
            )
        sliced[key] = outcome
    if not sliced:
        return _unmeasured(
            "slicing-under-a-pinned-profile", "there was no mesh to slice"
        )
    return Measurement(
        "slicing-under-a-pinned-profile",
        PASSED,
        # The claim is that the meshes sliced under this profile, and nothing
        # more. It is not a claim that anything printed or assembled.
        "every mesh sliced under the pinned printer, material and profile",
        sliced,
    )


def _stats(mesh: Path) -> Dict[str, Any]:
    gate = config.load_harness("gate")
    return gate.part_stats(mesh)


# ---------------------------------------------------------------------------
# The results
# ---------------------------------------------------------------------------


def assemble(
    name: str,
    measurements: Sequence[Measurement],
    *,
    made,
    required: Sequence[str],
) -> Dict[str, Any]:
    """One manufacturing result, and the rule that an unrun check is not a pass."""

    by_name = {item.name: item for item in measurements}
    absent = [check for check in required if check not in by_name]
    entries = [item.to_dict() for item in measurements]
    for check in absent:
        entries.append(
            _unmeasured(check, "this check was never attempted").to_dict()
        )
    failures = [item for item in entries if item["status"] == FAILED]
    unmeasured = [item for item in entries if item["status"] == UNMEASURED]
    return {
        "evidence_class": "ai-simulation",
        "artifact_sha256": made.artifact_sha256,
        "source_closure_sha256": source_closure_sha256(made),
        "source_files": [
            str(path.relative_to(Path(made.artifact_root)))
            for path in cad_sources(made)
        ],
        "checks": entries,
        "failed": [item["check"] for item in failures],
        "unmeasured": [item["check"] for item in unmeasured],
        # An unmeasured check is not a pass. A result whose slicer never ran
        # does not get to pass on the strength of the checks that did.
        "passed": not failures and not unmeasured,
        "printer": config.PRINTER_NAME,
        "usable_bed_mm": list(config.usable_bed_mm()),
        "claim": _claim(name, entries),
        "evaluator": EVALUATOR,
        "evaluator_version": EVALUATOR_VERSION,
    }


def _claim(name: str, entries: Sequence[Mapping[str, Any]]) -> str:
    ran = [item["check"] for item in entries if item["status"] != UNMEASURED]
    if name == "print-test":
        return (
            "These checks ran over the meshes in this revision: %s. Slicing, "
            "where it ran, means the meshes sliced under the pinned profile — "
            "it is not a claim that anything printed or assembled."
            % (", ".join(ran) or "none")
        )
    return (
        "These checks ran over the geometry in this revision: %s. Nothing here "
        "was read from a render." % (", ".join(ran) or "none")
    )


def findings(evidence: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """A failed measurement blocks; an unrun one prevents the pass."""

    found = []
    for entry in evidence.get("checks", ()):
        if entry["status"] == FAILED:
            found.append(
                {
                    "severity": "block",
                    "check": entry["check"],
                    "finding": entry["detail"],
                    "parts": list(entry.get("parts", ())),
                }
            )
        elif entry["status"] == UNMEASURED:
            found.append(
                {
                    "severity": "improve",
                    "check": entry["check"],
                    "finding": "unmeasured: %s" % entry["detail"],
                    "parts": list(entry.get("parts", ())),
                }
            )
    return found


def assert_no_image_evidence(evidence: Mapping[str, Any]) -> None:
    """No render or preview stands behind a geometry claim."""

    blob = json.dumps(evidence, default=str).casefold()
    for suffix in IMAGE_SUFFIXES:
        if suffix in blob:
            raise ValueError(
                "manufacturing evidence cites a %s file; a render is never "
                "offered in support of topology, fit, interference, or "
                "printability" % suffix
            )


__all__ = [
    "DIMENSION_TOLERANCE_MM",
    "EVALUATOR",
    "EVALUATOR_VERSION",
    "FAILED",
    "IMAGE_SUFFIXES",
    "MECHANICAL_CHECKS",
    "PASSED",
    "PRINT_CHECKS",
    "Measurement",
    "StaleEvidence",
    "UNMEASURED",
    "assemble",
    "assert_no_image_evidence",
    "assert_sources_current",
    "cad_sources",
    "findings",
    "measure_mechanical",
    "measure_print",
    "source_closure_sha256",
]
