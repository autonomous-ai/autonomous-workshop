"""Pure, deterministic STL topology checks shared by every inventor.

The topology algorithm is adapted from ``skills/cad/scripts/check_mesh`` at
upstream commit ``f18aebe4698d92ffccf07d94e2d624b08d30e667``.  It deliberately
uses only the Python standard library so Workshop and its inventors get the
same fail-closed result on every supported Python version.

An STL topology pass is a narrow claim.  It does not establish CAD-kernel
solidness, wall thickness, overhangs, slicer success, manufacturability, or
physical fit.  A separate, source-bound kernel observation is required when a
caller wants to assert a CAD body count.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import struct
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


UPSTREAM_SOURCE_COMMIT = "f18aebe4698d92ffccf07d94e2d624b08d30e667"
UPSTREAM_SOURCE_PATHS = ("skills/cad/scripts/check_mesh",)
UPSTREAM_MIT_NOTICE = """MIT License

Copyright (c) 2026 Thompson Labs LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# These version strings preserve Alice's existing receipt contract while its
# public symbols move to Workshop.  Changing them would invalidate durable
# evidence already written by Alice.
STL_INSPECTION_RECEIPT_VERSION = "alice.stl-topology-receipt.v1"
KERNEL_BODY_OBSERVATION_VERSION = "alice.kernel-body-observation.v1"

_HEX = frozenset("0123456789abcdef")
_STL_LIMITATIONS = (
    "stl_topology_only_not_cad_kernel_solidness",
    "does_not_measure_wall_thickness_overhang_slicer_success_or_physical_fit",
)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _finite_number(value: object, field: str) -> float:
    if not _is_number(value):
        raise TypeError("%s must be a finite number" % field)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % field)
    return result


def _positive_number(value: object, field: str) -> float:
    result = _finite_number(value, field)
    if result <= 0:
        raise ValueError("%s must be > 0" % field)
    return result


def _nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % field)
    result = value.strip()
    if any(ord(character) < 32 for character in result):
        raise ValueError("%s must not contain control characters" % field)
    return result


def _sha256(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value.lower() != value
        or any(character not in _HEX for character in value)
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % field)
    return value


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class StlInspectionLimits:
    """Resource and numeric bounds for one pure in-memory inspection."""

    max_source_bytes: int = 32 * 1024 * 1024
    max_triangles: int = 250_000
    weld_tolerance_mm: float = 1e-6
    degenerate_area_epsilon_mm2: float = 1e-18
    zero_volume_epsilon_mm3: float = 1e-12
    max_abs_coordinate_mm: float = 1_000_000.0

    def __post_init__(self) -> None:
        for field in ("max_source_bytes", "max_triangles"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError("%s must be a positive integer" % field)
        for field in ("weld_tolerance_mm", "max_abs_coordinate_mm"):
            object.__setattr__(self, field, _positive_number(getattr(self, field), field))
        for field in ("degenerate_area_epsilon_mm2", "zero_volume_epsilon_mm3"):
            value = _finite_number(getattr(self, field), field)
            if value < 0:
                raise ValueError("%s must be >= 0" % field)
            object.__setattr__(self, field, value)

    def to_dict(self) -> Dict[str, object]:
        return {
            "max_source_bytes": self.max_source_bytes,
            "max_triangles": self.max_triangles,
            "weld_tolerance_mm": self.weld_tolerance_mm,
            "degenerate_area_epsilon_mm2": self.degenerate_area_epsilon_mm2,
            "zero_volume_epsilon_mm3": self.zero_volume_epsilon_mm3,
            "max_abs_coordinate_mm": self.max_abs_coordinate_mm,
        }

    @property
    def limits_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


@dataclass(frozen=True)
class KernelBodyObservation:
    """Optional external CAD-kernel body count bound to the same STL bytes."""

    source_sha256: str
    evaluator_id: str
    status: str
    body_count: Optional[int]
    evidence_sha256: Optional[str]
    schema_version: str = KERNEL_BODY_OBSERVATION_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != KERNEL_BODY_OBSERVATION_VERSION:
            raise ValueError("unsupported kernel body observation version")
        object.__setattr__(self, "source_sha256", _sha256(self.source_sha256, "source_sha256"))
        object.__setattr__(self, "evaluator_id", _nonempty_string(self.evaluator_id, "evaluator_id"))
        if self.status not in {"completed", "inconclusive", "error"}:
            raise ValueError("kernel body status must be completed, inconclusive, or error")
        if self.status == "completed":
            if (
                isinstance(self.body_count, bool)
                or not isinstance(self.body_count, int)
                or self.body_count < 0
            ):
                raise ValueError("completed kernel body count must be a non-negative integer")
            object.__setattr__(
                self,
                "evidence_sha256",
                _sha256(self.evidence_sha256, "evidence_sha256"),
            )
        else:
            if self.body_count is not None:
                raise ValueError("inconclusive/error kernel observation cannot assert a body count")
            if self.evidence_sha256 is not None:
                object.__setattr__(
                    self,
                    "evidence_sha256",
                    _sha256(self.evidence_sha256, "evidence_sha256"),
                )

    @classmethod
    def from_mapping(cls, raw: Mapping) -> "KernelBodyObservation":
        """Load a JSON-shaped observation without accepting unknown fields."""

        if not isinstance(raw, Mapping):
            raise TypeError("kernel body observation must be an object")
        allowed = {
            "schema_version",
            "source_sha256",
            "evaluator_id",
            "status",
            "body_count",
            "evidence_sha256",
        }
        unknown = sorted(set(raw) - allowed)
        if unknown:
            raise ValueError(
                "unknown kernel body observation fields: %s" % ", ".join(unknown)
            )
        return cls(
            schema_version=raw.get(
                "schema_version", KERNEL_BODY_OBSERVATION_VERSION
            ),
            source_sha256=raw.get("source_sha256"),
            evaluator_id=raw.get("evaluator_id"),
            status=raw.get("status"),
            body_count=raw.get("body_count"),
            evidence_sha256=raw.get("evidence_sha256"),
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_sha256": self.source_sha256,
            "evaluator_id": self.evaluator_id,
            "status": self.status,
            "body_count": self.body_count,
            "evidence_sha256": self.evidence_sha256,
        }

    @property
    def observation_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


@dataclass(frozen=True)
class StlTopologyReceipt:
    schema_version: str
    status: str
    source_sha256: str
    source_bytes: int
    limits_sha256: str
    stl_format: Optional[str]
    source_triangle_count: Optional[int]
    validated_triangle_count: Optional[int]
    welded_vertex_count: Optional[int]
    degenerate_triangle_count: Optional[int]
    boundary_edge_count: Optional[int]
    nonmanifold_edge_count: Optional[int]
    inconsistent_winding_edge_count: Optional[int]
    observed_shell_count: Optional[int]
    expected_shell_count: int
    shell_signed_volumes_mm3: Tuple[float, ...]
    bounds_min_mm: Optional[Tuple[float, float, float]]
    bounds_max_mm: Optional[Tuple[float, float, float]]
    expected_body_count: Optional[int]
    observed_kernel_body_count: Optional[int]
    kernel_status: str
    failure_reasons: Tuple[str, ...]
    hold_reasons: Tuple[str, ...]
    limitations: Tuple[str, ...] = _STL_LIMITATIONS

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "source_sha256": self.source_sha256,
            "source_bytes": self.source_bytes,
            "limits_sha256": self.limits_sha256,
            "stl_format": self.stl_format,
            "source_triangle_count": self.source_triangle_count,
            "validated_triangle_count": self.validated_triangle_count,
            "welded_vertex_count": self.welded_vertex_count,
            "degenerate_triangle_count": self.degenerate_triangle_count,
            "boundary_edge_count": self.boundary_edge_count,
            "nonmanifold_edge_count": self.nonmanifold_edge_count,
            "inconsistent_winding_edge_count": self.inconsistent_winding_edge_count,
            "observed_shell_count": self.observed_shell_count,
            "expected_shell_count": self.expected_shell_count,
            "shell_signed_volumes_mm3": list(self.shell_signed_volumes_mm3),
            "bounds_min_mm": None if self.bounds_min_mm is None else list(self.bounds_min_mm),
            "bounds_max_mm": None if self.bounds_max_mm is None else list(self.bounds_max_mm),
            "expected_body_count": self.expected_body_count,
            "observed_kernel_body_count": self.observed_kernel_body_count,
            "kernel_status": self.kernel_status,
            "failure_reasons": list(self.failure_reasons),
            "hold_reasons": list(self.hold_reasons),
            "limitations": list(self.limitations),
        }

    @property
    def receipt_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


class _StlParseError(ValueError):
    def __init__(self, code: str, definite_failure: bool = False) -> None:
        self.code = code
        self.definite_failure = definite_failure
        super().__init__(code)


class StlPathInspectionError(OSError):
    """A path could not be read as one stable, bounded regular file."""

    def __init__(self, code: str, path: object) -> None:
        self.code = code
        self.path = os.fspath(path)
        super().__init__("%s: %r" % (code, self.path))


Point = Tuple[float, float, float]
Triangle = Tuple[Point, Point, Point]


def _checked_float(token: object, code: str) -> float:
    try:
        value = float(token)
    except (TypeError, ValueError) as error:
        raise _StlParseError("malformed_numeric_token") from error
    if not math.isfinite(value):
        raise _StlParseError(code, definite_failure=True)
    return value


def _check_coordinate(value: float, limits: StlInspectionLimits) -> float:
    if abs(value) > limits.max_abs_coordinate_mm:
        raise _StlParseError("coordinate_safety_limit_exceeded")
    return value


def _parse_binary_stl(source: bytes, limits: StlInspectionLimits) -> List[Triangle]:
    if len(source) < 84:
        raise _StlParseError("truncated_binary_header")
    count = struct.unpack_from("<I", source, 80)[0]
    if count > limits.max_triangles:
        raise _StlParseError("triangle_limit_exceeded")
    expected = 84 + count * 50
    if len(source) != expected:
        raise _StlParseError("binary_size_mismatch")
    if count == 0:
        raise _StlParseError("empty_stl", definite_failure=True)
    triangles = []
    offset = 84
    for _ in range(count):
        values = struct.unpack_from("<12fH", source, offset)
        offset += 50
        if any(not math.isfinite(value) for value in values[:12]):
            raise _StlParseError("nonfinite_binary_float", definite_failure=True)
        vertices = []
        for start in (3, 6, 9):
            vertices.append(
                tuple(
                    _check_coordinate(float(values[index]), limits)
                    for index in range(start, start + 3)
                )
            )
        triangles.append((vertices[0], vertices[1], vertices[2]))
    return triangles


def _parse_ascii_stl(source: bytes, limits: StlInspectionLimits) -> List[Triangle]:
    try:
        text = source.decode("ascii")
    except UnicodeDecodeError as error:
        raise _StlParseError("ascii_decode_error") from error
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise _StlParseError("truncated_ascii_stl")
    first = lines[0].split(maxsplit=1)
    if first[0].lower() != "solid":
        raise _StlParseError("missing_ascii_solid")
    solid_name = first[1] if len(first) == 2 else ""
    triangles = []
    index = 1
    ended = False
    while index < len(lines):
        tokens = lines[index].split()
        if tokens and tokens[0].lower() == "endsolid":
            if index != len(lines) - 1:
                raise _StlParseError("ascii_trailing_content")
            end_name = " ".join(tokens[1:])
            if solid_name and end_name and end_name != solid_name:
                raise _StlParseError("ascii_solid_name_mismatch")
            ended = True
            break
        if len(tokens) != 5 or [token.lower() for token in tokens[:2]] != [
            "facet",
            "normal",
        ]:
            raise _StlParseError("malformed_ascii_facet")
        for token in tokens[2:]:
            _checked_float(token, "nonfinite_ascii_normal")
        index += 1
        if index >= len(lines) or [token.lower() for token in lines[index].split()] != [
            "outer",
            "loop",
        ]:
            raise _StlParseError("missing_ascii_outer_loop")
        index += 1
        vertices = []
        for _ in range(3):
            if index >= len(lines):
                raise _StlParseError("truncated_ascii_vertex")
            vertex_tokens = lines[index].split()
            if len(vertex_tokens) != 4 or vertex_tokens[0].lower() != "vertex":
                raise _StlParseError("malformed_ascii_vertex")
            vertex = tuple(
                _check_coordinate(
                    _checked_float(token, "nonfinite_ascii_coordinate"), limits
                )
                for token in vertex_tokens[1:]
            )
            vertices.append(vertex)
            index += 1
        if index >= len(lines) or lines[index].lower() != "endloop":
            raise _StlParseError("missing_ascii_endloop")
        index += 1
        if index >= len(lines) or lines[index].lower() != "endfacet":
            raise _StlParseError("missing_ascii_endfacet")
        index += 1
        triangles.append((vertices[0], vertices[1], vertices[2]))
        if len(triangles) > limits.max_triangles:
            raise _StlParseError("triangle_limit_exceeded")
    if not ended:
        raise _StlParseError("missing_ascii_endsolid")
    if not triangles:
        raise _StlParseError("empty_stl", definite_failure=True)
    return triangles


def _parse_stl(source: bytes, limits: StlInspectionLimits) -> Tuple[str, List[Triangle]]:
    if len(source) >= 84:
        count = struct.unpack_from("<I", source, 80)[0]
        if 84 + count * 50 == len(source):
            return "binary", _parse_binary_stl(source, limits)
    if source.lstrip().lower().startswith(b"solid"):
        return "ascii", _parse_ascii_stl(source, limits)
    return "binary", _parse_binary_stl(source, limits)


class _UnionFind:
    def __init__(self, count: int) -> None:
        self.parent = list(range(count))

    def find(self, item: int) -> int:
        parent = self.parent
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self.parent[root_right] = root_left


def _empty_stl_receipt(
    status: str,
    source_sha256: str,
    source_bytes: int,
    limits: StlInspectionLimits,
    stl_format: Optional[str],
    expected_shell_count: int,
    expected_body_count: Optional[int],
    failure_reasons: Sequence = (),
    hold_reasons: Sequence = (),
) -> StlTopologyReceipt:
    return StlTopologyReceipt(
        schema_version=STL_INSPECTION_RECEIPT_VERSION,
        status=status,
        source_sha256=source_sha256,
        source_bytes=source_bytes,
        limits_sha256=limits.limits_sha256,
        stl_format=stl_format,
        source_triangle_count=None,
        validated_triangle_count=None,
        welded_vertex_count=None,
        degenerate_triangle_count=None,
        boundary_edge_count=None,
        nonmanifold_edge_count=None,
        inconsistent_winding_edge_count=None,
        observed_shell_count=None,
        expected_shell_count=expected_shell_count,
        shell_signed_volumes_mm3=(),
        bounds_min_mm=None,
        bounds_max_mm=None,
        expected_body_count=expected_body_count,
        observed_kernel_body_count=None,
        kernel_status=(
            "not_evaluated" if expected_body_count is not None else "not_required"
        ),
        failure_reasons=tuple(failure_reasons),
        hold_reasons=tuple(hold_reasons),
    )


def inspect_stl_topology(
    source: Union[bytes, bytearray, memoryview],
    *,
    expected_shell_count: int,
    expected_body_count: Optional[int] = None,
    kernel_body_observation: Optional[KernelBodyObservation] = None,
    expected_source_sha256: Optional[str] = None,
    expected_source_bytes: Optional[int] = None,
    limits: Optional[StlInspectionLimits] = None,
) -> StlTopologyReceipt:
    """Inspect exact STL bytes and return a deterministic fail-closed receipt."""

    if not isinstance(source, (bytes, bytearray, memoryview)):
        raise TypeError("source must be bytes-like")
    raw = bytes(source)
    limits = limits or StlInspectionLimits()
    if (
        isinstance(expected_shell_count, bool)
        or not isinstance(expected_shell_count, int)
        or expected_shell_count < 1
    ):
        raise ValueError("expected_shell_count must be a positive integer")
    if expected_body_count is not None and (
        isinstance(expected_body_count, bool)
        or not isinstance(expected_body_count, int)
        or expected_body_count < 1
    ):
        raise ValueError("expected_body_count must be a positive integer")
    if expected_source_sha256 is not None:
        expected_source_sha256 = _sha256(
            expected_source_sha256, "expected_source_sha256"
        )
    if expected_source_bytes is not None and (
        isinstance(expected_source_bytes, bool)
        or not isinstance(expected_source_bytes, int)
        or expected_source_bytes < 0
    ):
        raise ValueError("expected_source_bytes must be a non-negative integer")

    actual_sha256 = hashlib.sha256(raw).hexdigest()
    hold_reasons = []
    if expected_source_sha256 is not None and expected_source_sha256 != actual_sha256:
        hold_reasons.append("source_sha256_mismatch")
    if expected_source_bytes is not None and expected_source_bytes != len(raw):
        hold_reasons.append("source_byte_count_mismatch")
    if len(raw) > limits.max_source_bytes:
        hold_reasons.append("source_byte_limit_exceeded")
        return _empty_stl_receipt(
            "held",
            actual_sha256,
            len(raw),
            limits,
            None,
            expected_shell_count,
            expected_body_count,
            hold_reasons=hold_reasons,
        )

    stl_format = "ascii" if raw.lstrip().lower().startswith(b"solid") else "binary"
    if len(raw) >= 84:
        declared_count = struct.unpack_from("<I", raw, 80)[0]
        if 84 + declared_count * 50 == len(raw):
            stl_format = "binary"
    try:
        stl_format, triangles = _parse_stl(raw, limits)
    except _StlParseError as error:
        if error.definite_failure and not hold_reasons:
            return _empty_stl_receipt(
                "failed",
                actual_sha256,
                len(raw),
                limits,
                stl_format,
                expected_shell_count,
                expected_body_count,
                failure_reasons=(error.code,),
            )
        hold_reasons.append(error.code)
        return _empty_stl_receipt(
            "held",
            actual_sha256,
            len(raw),
            limits,
            stl_format,
            expected_shell_count,
            expected_body_count,
            hold_reasons=hold_reasons,
        )

    vertices = []
    vertex_by_key = {}
    faces = []
    degenerate = 0
    tolerance = limits.weld_tolerance_mm
    for triangle in triangles:
        face_indices = []
        for vertex in triangle:
            try:
                scaled = tuple(component / tolerance for component in vertex)
                if any(not math.isfinite(component) for component in scaled):
                    raise OverflowError
                key = tuple(round(component) for component in scaled)
            except (OverflowError, ValueError):
                hold_reasons.append("weld_quantization_inconclusive")
                return _empty_stl_receipt(
                    "held",
                    actual_sha256,
                    len(raw),
                    limits,
                    stl_format,
                    expected_shell_count,
                    expected_body_count,
                    hold_reasons=hold_reasons,
                )
            vertex_index = vertex_by_key.get(key)
            if vertex_index is None:
                vertex_index = len(vertices)
                vertex_by_key[key] = vertex_index
                vertices.append(vertex)
            face_indices.append(vertex_index)
        a, b, c = face_indices
        if len({a, b, c}) != 3:
            degenerate += 1
            continue
        va, vb, vc = vertices[a], vertices[b], vertices[c]
        edge1 = (vb[0] - va[0], vb[1] - va[1], vb[2] - va[2])
        edge2 = (vc[0] - va[0], vc[1] - va[1], vc[2] - va[2])
        cross = (
            edge1[1] * edge2[2] - edge1[2] * edge2[1],
            edge1[2] * edge2[0] - edge1[0] * edge2[2],
            edge1[0] * edge2[1] - edge1[1] * edge2[0],
        )
        area = 0.5 * math.sqrt(sum(component * component for component in cross))
        if not math.isfinite(area) or area <= limits.degenerate_area_epsilon_mm2:
            degenerate += 1
            continue
        faces.append((a, b, c))

    failures = []
    if degenerate:
        failures.append("degenerate_triangles")
    if not faces:
        failures.append("no_valid_triangles")
        return StlTopologyReceipt(
            schema_version=STL_INSPECTION_RECEIPT_VERSION,
            status="held" if hold_reasons else "failed",
            source_sha256=actual_sha256,
            source_bytes=len(raw),
            limits_sha256=limits.limits_sha256,
            stl_format=stl_format,
            source_triangle_count=len(triangles),
            validated_triangle_count=0,
            welded_vertex_count=len(vertices),
            degenerate_triangle_count=degenerate,
            boundary_edge_count=None,
            nonmanifold_edge_count=None,
            inconsistent_winding_edge_count=None,
            observed_shell_count=0,
            expected_shell_count=expected_shell_count,
            shell_signed_volumes_mm3=(),
            bounds_min_mm=None,
            bounds_max_mm=None,
            expected_body_count=expected_body_count,
            observed_kernel_body_count=None,
            kernel_status=(
                "not_evaluated"
                if expected_body_count is not None
                else "not_required"
            ),
            failure_reasons=tuple(failures),
            hold_reasons=tuple(hold_reasons),
        )

    union = _UnionFind(len(faces))
    edge_data = {}
    for face_index, (a, b, c) in enumerate(faces):
        for left, right in ((a, b), (b, c), (c, a)):
            key = (left, right) if left < right else (right, left)
            direction = 1 if left < right else -1
            existing = edge_data.get(key)
            if existing is None:
                edge_data[key] = [1, direction, face_index]
            else:
                existing[0] += 1
                existing[1] += direction
                union.union(existing[2], face_index)
    boundary = sum(1 for count, _, _ in edge_data.values() if count == 1)
    nonmanifold = sum(1 for count, _, _ in edge_data.values() if count > 2)
    inconsistent = sum(
        1
        for count, direction, _ in edge_data.values()
        if count == 2 and direction != 0
    )
    if boundary:
        failures.append("boundary_edges")
    if nonmanifold:
        failures.append("nonmanifold_edges")
    if inconsistent:
        failures.append("inconsistent_winding")

    shell_faces = {}
    for face_index, face in enumerate(faces):
        shell_faces.setdefault(union.find(face_index), []).append(face)
    observed_shell_count = len(shell_faces)
    if observed_shell_count != expected_shell_count:
        failures.append("unexpected_shell_count")

    shell_volumes = []
    for root in sorted(shell_faces):
        shell = shell_faces[root]
        reference = vertices[shell[0][0]]
        terms = []
        for a, b, c in shell:
            va = tuple(vertices[a][axis] - reference[axis] for axis in range(3))
            vb = tuple(vertices[b][axis] - reference[axis] for axis in range(3))
            vc = tuple(vertices[c][axis] - reference[axis] for axis in range(3))
            cross = (
                vb[1] * vc[2] - vb[2] * vc[1],
                vb[2] * vc[0] - vb[0] * vc[2],
                vb[0] * vc[1] - vb[1] * vc[0],
            )
            terms.append(
                (va[0] * cross[0] + va[1] * cross[1] + va[2] * cross[2])
                / 6.0
            )
        try:
            volume = math.fsum(terms)
        except (OverflowError, ValueError):
            volume = math.nan
        shell_volumes.append(volume)
        if not math.isfinite(volume) or abs(volume) <= limits.zero_volume_epsilon_mm3:
            failures.append("zero_or_nonfinite_shell_volume")
        elif volume < 0:
            failures.append("inward_shell_winding")

    bounds_min = tuple(min(vertex[axis] for vertex in vertices) for axis in range(3))
    bounds_max = tuple(max(vertex[axis] for vertex in vertices) for axis in range(3))

    kernel_status = "not_required"
    observed_body_count = None
    if expected_body_count is not None:
        if kernel_body_observation is None:
            kernel_status = "not_evaluated"
            hold_reasons.append("kernel_body_count_not_evaluated")
        elif kernel_body_observation.source_sha256 != actual_sha256:
            kernel_status = "source_mismatch"
            hold_reasons.append("kernel_body_source_sha256_mismatch")
        elif kernel_body_observation.status != "completed":
            kernel_status = kernel_body_observation.status
            hold_reasons.append("kernel_body_%s" % kernel_body_observation.status)
        else:
            kernel_status = "completed"
            observed_body_count = kernel_body_observation.body_count
            if observed_body_count != expected_body_count:
                failures.append("unexpected_kernel_body_count")
    elif kernel_body_observation is not None:
        kernel_status = kernel_body_observation.status
        if kernel_body_observation.source_sha256 != actual_sha256:
            hold_reasons.append("kernel_body_source_sha256_mismatch")

    failures = list(dict.fromkeys(failures))
    hold_reasons = list(dict.fromkeys(hold_reasons))
    status = "held" if hold_reasons else ("failed" if failures else "passed")
    return StlTopologyReceipt(
        schema_version=STL_INSPECTION_RECEIPT_VERSION,
        status=status,
        source_sha256=actual_sha256,
        source_bytes=len(raw),
        limits_sha256=limits.limits_sha256,
        stl_format=stl_format,
        source_triangle_count=len(triangles),
        validated_triangle_count=len(faces),
        welded_vertex_count=len(vertices),
        degenerate_triangle_count=degenerate,
        boundary_edge_count=boundary,
        nonmanifold_edge_count=nonmanifold,
        inconsistent_winding_edge_count=inconsistent,
        observed_shell_count=observed_shell_count,
        expected_shell_count=expected_shell_count,
        shell_signed_volumes_mm3=tuple(shell_volumes),
        bounds_min_mm=bounds_min,
        bounds_max_mm=bounds_max,
        expected_body_count=expected_body_count,
        observed_kernel_body_count=observed_body_count,
        kernel_status=kernel_status,
        failure_reasons=tuple(failures),
        hold_reasons=tuple(hold_reasons),
    )


def _stat_fingerprint(value: os.stat_result) -> Tuple[int, ...]:
    """Return metadata that changes when an opened file is replaced or edited."""

    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        getattr(value, "st_mtime_ns", int(value.st_mtime * 1_000_000_000)),
        getattr(value, "st_ctime_ns", int(value.st_ctime * 1_000_000_000)),
    )


def inspect_stl_path(
    path: Union[str, os.PathLike],
    *,
    expected_shell_count: int,
    expected_body_count: Optional[int] = None,
    kernel_body_observation: Optional[KernelBodyObservation] = None,
    expected_source_sha256: Optional[str] = None,
    expected_source_bytes: Optional[int] = None,
    limits: Optional[StlInspectionLimits] = None,
) -> StlTopologyReceipt:
    """Safely read and inspect one stable STL regular file.

    The leaf is opened with ``O_NOFOLLOW`` where the platform provides it.
    Pre-open, opened-descriptor, post-read, and final-path metadata must all
    describe the same regular file.  Its declared size is checked before a
    bounded descriptor read, and one extra byte is probed so a concurrent
    append cannot be silently excluded from the receipt.  Only those exact
    held-descriptor bytes are passed to :func:`inspect_stl_topology`.

    Unsafe, oversized, or changing paths raise
    :class:`StlPathInspectionError`; callers must treat that as a failed gate.
    """

    source_path = os.fspath(path)
    active_limits = limits or StlInspectionLimits()
    before = os.lstat(source_path)
    if stat.S_ISLNK(before.st_mode):
        raise StlPathInspectionError("path_is_symlink", source_path)
    if not stat.S_ISREG(before.st_mode):
        raise StlPathInspectionError("path_is_not_regular_file", source_path)
    if before.st_size > active_limits.max_source_bytes:
        raise StlPathInspectionError("source_byte_limit_exceeded", source_path)

    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_BINARY", 0)
    )
    descriptor = None
    try:
        descriptor = os.open(source_path, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise StlPathInspectionError("opened_path_is_not_regular_file", source_path)
        if _stat_fingerprint(opened) != _stat_fingerprint(before):
            raise StlPathInspectionError("path_changed_while_opening", source_path)
        if opened.st_size > active_limits.max_source_bytes:
            raise StlPathInspectionError("source_byte_limit_exceeded", source_path)

        remaining = opened.st_size
        chunks = []
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                raise StlPathInspectionError("source_changed_while_reading", source_path)
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise StlPathInspectionError("source_changed_while_reading", source_path)

        after = os.fstat(descriptor)
        try:
            final_path = os.lstat(source_path)
        except OSError as error:
            raise StlPathInspectionError(
                "path_changed_while_reading", source_path
            ) from error
        if (
            _stat_fingerprint(after) != _stat_fingerprint(opened)
            or _stat_fingerprint(final_path) != _stat_fingerprint(opened)
            or not stat.S_ISREG(final_path.st_mode)
        ):
            raise StlPathInspectionError("path_changed_while_reading", source_path)
        raw = b"".join(chunks)
    finally:
        if descriptor is not None:
            os.close(descriptor)

    return inspect_stl_topology(
        raw,
        expected_shell_count=expected_shell_count,
        expected_body_count=expected_body_count,
        kernel_body_observation=kernel_body_observation,
        expected_source_sha256=expected_source_sha256,
        expected_source_bytes=expected_source_bytes,
        limits=active_limits,
    )


def fits_bed_envelope(
    bounds_min_mm: Sequence,
    bounds_max_mm: Sequence,
    bed_mm: Sequence,
    *,
    allow_xy_rotation: bool = True,
) -> bool:
    """Return whether exact bounds fit a positive printer envelope.

    The check keeps Z upright.  X/Y may be swapped and, when requested, any
    in-plane rotation of the XY bounding rectangle is considered exactly.
    It is only an envelope check; it makes no print-orientation or support
    claim.
    """

    if not isinstance(allow_xy_rotation, bool):
        raise TypeError("allow_xy_rotation must be a boolean")
    for label, values in (
        ("bounds_min_mm", bounds_min_mm),
        ("bounds_max_mm", bounds_max_mm),
        ("bed_mm", bed_mm),
    ):
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise TypeError("%s must be a three-number sequence" % label)
        if len(values) != 3:
            raise ValueError("%s must contain exactly three numbers" % label)
    minimum = tuple(_finite_number(value, "bounds_min_mm") for value in bounds_min_mm)
    maximum = tuple(_finite_number(value, "bounds_max_mm") for value in bounds_max_mm)
    bed = tuple(_positive_number(value, "bed_mm") for value in bed_mm)
    extents = tuple(maximum[index] - minimum[index] for index in range(3))
    if any(extent <= 0 or not math.isfinite(extent) for extent in extents):
        return False
    x, y, z = extents
    bed_x, bed_y, bed_z = bed
    if z > bed_z:
        return False
    if (x <= bed_x and y <= bed_y) or (x <= bed_y and y <= bed_x):
        return True
    if not allow_xy_rotation:
        return False

    # A rectangle rotated by theta occupies
    #   x*cos(theta) + y*sin(theta) by x*sin(theta) + y*cos(theta).
    # Each dimension is a cosine hump over [0, pi/2].  Its <= limit set is
    # therefore the union of at most two closed intervals near the endpoints.
    # Intersecting the two unions gives exact rectangular-bed feasibility,
    # including useful angles that are neither axis-aligned nor 45 degrees.
    diagonal = math.hypot(x, y)

    def sublevel_intervals(
        phase: float, limit: float
    ) -> Tuple[Tuple[float, float], ...]:
        half_pi = math.pi / 2.0
        tolerance = 1e-12 * max(1.0, diagonal, limit)
        if limit + tolerance >= diagonal:
            return ((0.0, half_pi),)
        alpha = math.acos(max(0.0, min(1.0, limit / diagonal)))
        intervals = []
        left_end = phase - alpha
        right_start = phase + alpha
        if left_end >= -1e-12:
            intervals.append((0.0, min(half_pi, max(0.0, left_end))))
        if right_start <= half_pi + 1e-12:
            intervals.append((max(0.0, min(half_pi, right_start)), half_pi))
        return tuple(intervals)

    width_intervals = sublevel_intervals(math.atan2(y, x), bed_x)
    depth_intervals = sublevel_intervals(math.atan2(x, y), bed_y)
    return any(
        max(width_low, depth_low) <= min(width_high, depth_high) + 1e-12
        for width_low, width_high in width_intervals
        for depth_low, depth_high in depth_intervals
    )


__all__ = [
    "KERNEL_BODY_OBSERVATION_VERSION",
    "STL_INSPECTION_RECEIPT_VERSION",
    "UPSTREAM_MIT_NOTICE",
    "UPSTREAM_SOURCE_COMMIT",
    "UPSTREAM_SOURCE_PATHS",
    "KernelBodyObservation",
    "StlPathInspectionError",
    "StlInspectionLimits",
    "StlTopologyReceipt",
    "fits_bed_envelope",
    "inspect_stl_path",
    "inspect_stl_topology",
]
