"""Final-geometry proofs for literal CadQuery dimensions and features.

Parameter validation proves that the *inputs* are sensible. This module proves
that the final post-boolean B-rep still has the extents, holes, cuts, and empty
regions the user asked for. Use these helpers only for explicit final
requirements; they complement visual review and engineering checks.
"""

from __future__ import annotations

import math

import cadquery as cq


_AXES = ("x", "y", "z")
_AXIS_FRAME = {
    "x": (0, 1, 2),  # axis, then transverse coordinates (y, z)
    "y": (1, 0, 2),  # axis, then transverse coordinates (x, z)
    "z": (2, 0, 1),  # axis, then transverse coordinates (x, y)
}
_FACE_FRAME = {
    "-X": (0, -1.0),
    "+X": (0, 1.0),
    "-Y": (1, -1.0),
    "+Y": (1, 1.0),
    "-Z": (2, -1.0),
    "+Z": (2, 1.0),
}
_AXIS_FACES = {
    "x": ("-X", "+X"),
    "y": ("-Y", "+Y"),
    "z": ("-Z", "+Z"),
}


def _number(name: str, value: object) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = math.nan
    if isinstance(value, bool) or not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number, got {value!r}")
    return result


def _optional_triple(
    name: str,
    value: tuple[float | None, float | None, float | None] | None,
) -> tuple[float | None, float | None, float | None]:
    if value is None:
        return (None, None, None)
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError(
            f"{name} must be an explicit (x, y, z) triple; use None for "
            "an unspecified axis"
        )
    return tuple(
        None if item is None else _number(f"{name}[{axis}]", item)
        for axis, item in zip(_AXES, value)
    )


def _triple(name: str, value: object) -> tuple[float, float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError(f"{name} must be an explicit (x, y, z) triple")
    return tuple(
        _number(f"{name}[{axis}]", item) for axis, item in zip(_AXES, value)
    )


def _pair(name: str, value: object) -> tuple[float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError(f"{name} must be an explicit pair")
    return (_number(f"{name}[0]", value[0]), _number(f"{name}[1]", value[1]))


def _faces(name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError(f"{name} must be an explicit face sequence")
    result: list[str] = []
    for index, face in enumerate(value):
        if not isinstance(face, str) or face not in _FACE_FRAME:
            raise ValueError(
                f"{name}[{index}] must be one of {sorted(_FACE_FRAME)}, got {face!r}"
            )
        if face in result:
            raise ValueError(f"{name} must not contain duplicate faces")
        result.append(face)
    return tuple(result)


def _solid_bbox(model: cq.Workplane | cq.Shape | cq.Assembly):
    if isinstance(model, cq.Assembly):
        try:
            shape = model.toCompound()
        except Exception as exc:
            raise ValueError("shape assembly is empty or cannot be compounded") from exc
        solids = shape.Solids()
    elif isinstance(model, cq.Workplane):
        solids = model.solids().vals()
        shape = (
            solids[0]
            if len(solids) == 1
            else cq.Compound.makeCompound(solids)
            if solids
            else None
        )
    elif isinstance(model, cq.Shape):
        solids = model.Solids()
        shape = model
    else:
        raise ValueError(
            "shape must be a cq.Workplane, cq.Shape, or cq.Assembly containing solids"
        )

    if not solids or shape is None:
        raise ValueError("shape must contain at least one final solid")
    return shape.BoundingBox()


def _single_solid(part: cq.Workplane | cq.Shape):
    if isinstance(part, cq.Workplane):
        solids = part.solids().vals()
    elif isinstance(part, cq.Shape):
        solids = part.Solids()
    else:
        raise ValueError("part must be a cq.Workplane or cq.Shape")
    if len(solids) != 1:
        raise ValueError(
            "part must contain exactly one final solid for an unambiguous feature proof"
        )
    return solids[0]


def _box_from_bounds(
    low: tuple[float, float, float] | list[float],
    high: tuple[float, float, float] | list[float],
) -> cq.Workplane:
    size = tuple(high[index] - low[index] for index in range(3))
    center = tuple((high[index] + low[index]) / 2 for index in range(3))
    return cq.Workplane("XY").box(*size).translate(center)


def _intersection_volume(solid: cq.Shape, region: cq.Workplane) -> float:
    common = cq.Workplane(obj=solid).intersect(region)
    return float(sum(shape.Volume() for shape in common.solids().vals()))


def _point_on_axis(
    axis_index: int,
    u_index: int,
    v_index: int,
    axis_value: float,
    center: tuple[float, float],
) -> tuple[float, float, float]:
    point = [0.0, 0.0, 0.0]
    point[axis_index] = axis_value
    point[u_index], point[v_index] = center
    return tuple(point)


def _normalize_centers(value: object) -> list[tuple[float, float]]:
    if not isinstance(value, (tuple, list)) or not value:
        raise ValueError("centers must contain at least one explicit (u, v) pair")
    if len(value) > 1024:
        raise ValueError("centers contains too many holes")
    result: list[tuple[float, float]] = []
    for index, center in enumerate(value):
        if not isinstance(center, (tuple, list)) or len(center) != 2:
            raise ValueError(f"centers[{index}] must be an explicit (u, v) pair")
        normalized = (
            _number(f"centers[{index}][0]", center[0]),
            _number(f"centers[{index}][1]", center[1]),
        )
        result.append(normalized)
    return result


def _normalize_scope(value: object) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    if not isinstance(value, (tuple, list)) or len(value) != 4:
        raise ValueError("scope must be an explicit (u_min, v_min, u_max, v_max) tuple")
    scope = tuple(_number(f"scope[{index}]", item) for index, item in enumerate(value))
    if scope[2] <= scope[0] or scope[3] <= scope[1]:
        raise ValueError("scope max values must be greater than min values")
    return scope


def _in_scope(
    center: tuple[float, float],
    scope: tuple[float, float, float, float] | None,
    tolerance: float,
) -> bool:
    if scope is None:
        return True
    return (
        scope[0] - tolerance <= center[0] <= scope[2] + tolerance
        and scope[1] - tolerance <= center[1] <= scope[3] + tolerance
    )


def _candidate_hole_centers(
    solid,
    *,
    axis_index: int,
    u_index: int,
    v_index: int,
    radius: float,
    axis_samples: tuple[float, float, float],
    scope: tuple[float, float, float, float] | None,
    tolerance: float,
) -> list[tuple[float, float]]:
    """Find exact cylindrical voids from final B-rep faces, then prove air."""
    result: list[tuple[float, float]] = []
    for face in solid.Faces():
        if face.geomType() != "CYLINDER":
            continue
        circle_edges = []
        for edge in face.Edges():
            if edge.geomType() != "CIRCLE":
                continue
            try:
                edge_radius = float(edge.radius())
                normal = edge.normal().toTuple()
            except (AttributeError, TypeError, ValueError):
                continue
            if abs(edge_radius - radius) > tolerance / 2:
                continue
            if abs(abs(float(normal[axis_index])) - 1.0) > 1e-5 or any(
                abs(float(normal[index])) > 1e-5
                for index in (u_index, v_index)
            ):
                continue
            circle_edges.append(edge)
        if len(circle_edges) < 2:
            continue

        arc_centers = [edge.arcCenter().toTuple() for edge in circle_edges]
        u_values = [float(center[u_index]) for center in arc_centers]
        v_values = [float(center[v_index]) for center in arc_centers]
        if max(u_values) - min(u_values) > tolerance or (
            max(v_values) - min(v_values) > tolerance
        ):
            continue
        center = (
            sum(u_values) / len(u_values),
            sum(v_values) / len(v_values),
        )
        if not _in_scope(center, scope, tolerance):
            continue
        if any(
            solid.isInside(
                cq.Vector(
                    *_point_on_axis(
                        axis_index, u_index, v_index, axis_value, center
                    )
                ),
                tolerance,
            )
            for axis_value in axis_samples
        ):
            continue
        if any(
            math.dist(center, existing) <= tolerance for existing in result
        ):
            continue
        result.append(center)
    return sorted(result)


def verify_bbox(
    *,
    shape: cq.Workplane | cq.Shape | cq.Assembly,
    expected_size: tuple[float | None, float | None, float | None] | None = None,
    expected_min: tuple[float | None, float | None, float | None] | None = None,
    expected_max: tuple[float | None, float | None, float | None] | None = None,
    tolerance: float = 0.01,
    label: str = "part",
) -> dict[str, list[float] | float]:
    """Measure and enforce literal extents on a final CadQuery B-rep.

    ``expected_size``, ``expected_min``, and ``expected_max`` are world-space
    ``(x, y, z)`` triples in millimetres.  Put ``None`` on any axis the request
    did not constrain.  At least one axis must be specified.  All supplied
    values are checked against the final post-boolean solid inventory, not only
    ``Workplane.val()``; assembly child locations are applied before measuring.

    The default 0.01 mm tolerance absorbs OCCT numerical noise without hiding
    an FDM-significant dimension error.  A mismatch raises ``ValueError`` and
    the returned dictionary is a JSON-safe measurement receipt.

    Example::

        proof = verify_bbox(
            shape=body,
            expected_size=(80, 60, 30),
            expected_min=(-40, -30, -15),
            expected_max=(40, 30, 15),
            label="base",
        )
    """
    tolerance = _number("tolerance", tolerance)
    if tolerance <= 0:
        raise ValueError("tolerance must be > 0")
    if not isinstance(label, str) or not label.strip():
        raise ValueError("label must be a non-empty string")

    expectations = {
        "size": _optional_triple("expected_size", expected_size),
        "min": _optional_triple("expected_min", expected_min),
        "max": _optional_triple("expected_max", expected_max),
    }
    if not any(value is not None for triple in expectations.values() for value in triple):
        raise ValueError("at least one bbox expectation must be specified")

    for axis, size, low, high in zip(
        _AXES, expectations["size"], expectations["min"], expectations["max"]
    ):
        if size is not None and size <= 0:
            raise ValueError(f"expected_size[{axis}] must be > 0")
        if low is not None and high is not None:
            if high <= low:
                raise ValueError(f"expected_max[{axis}] must be > expected_min[{axis}]")
            if size is not None and abs((high - low) - size) > tolerance:
                raise ValueError(
                    f"inconsistent {axis} expectations: max-min is {high - low:.6g} mm "
                    f"but size is {size:.6g} mm"
                )

    bbox = _solid_bbox(shape)
    actual = {
        "size": [float(bbox.xlen), float(bbox.ylen), float(bbox.zlen)],
        "min": [float(bbox.xmin), float(bbox.ymin), float(bbox.zmin)],
        "max": [float(bbox.xmax), float(bbox.ymax), float(bbox.zmax)],
    }
    for field, expected in expectations.items():
        for axis, wanted, measured in zip(_AXES, expected, actual[field]):
            if wanted is None:
                continue
            delta = measured - wanted
            if abs(delta) > tolerance:
                raise ValueError(
                    f"{label} bbox {field}.{axis}: expected {wanted:.6g} mm, "
                    f"got {measured:.6g} mm (delta {delta:+.6g} mm, "
                    f"tolerance +/-{tolerance:.6g} mm); verify the final "
                    "post-boolean geometry"
                )

    return {**actual, "tolerance": tolerance}


def _analytic_surface(face: cq.Face, kind: str):
    adaptor = face._geomAdaptor()
    if kind == "CYLINDER":
        return adaptor.Cylinder()
    if kind == "CONE":
        return adaptor.Cone()
    raise ValueError(f"unsupported analytic surface type {kind!r}")


def _axis_receipt(surface) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    axis = surface.Axis()
    location = axis.Location()
    direction = axis.Direction()
    return (
        (float(location.X()), float(location.Y()), float(location.Z())),
        (float(direction.X()), float(direction.Y()), float(direction.Z())),
    )


def _cross_length(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> float:
    return math.sqrt(
        (left[1] * right[2] - left[2] * right[1]) ** 2
        + (left[2] * right[0] - left[0] * right[2]) ** 2
        + (left[0] * right[1] - left[1] * right[0]) ** 2
    )


def verify_uniform_wall_thickness(
    *,
    outer_face: cq.Face,
    inner_face: cq.Face,
    expected_thickness: float,
    tolerance: float = 0.01,
    label: str = "wall",
) -> dict[str, object]:
    """Prove one final cylindrical or conical wall-face pair is a true offset.

    Merely lofting inner and outer vertices at the same heights does not preserve
    normal thickness when a tapered wall changes slope. This helper therefore
    requires matching analytic surface types, parallel/coaxial axes, matching
    cone angles, and the requested final B-rep face-to-face distance. Call it
    once for every adjacent cylindrical/conical segment of an explicitly
    uniform wall, after the part's last geometry-changing operation.
    """
    if not isinstance(outer_face, cq.Face) or not isinstance(inner_face, cq.Face):
        raise ValueError("outer_face and inner_face must each be one final cq.Face")
    expected_thickness = _number("expected_thickness", expected_thickness)
    tolerance = _number("tolerance", tolerance)
    if expected_thickness <= 0:
        raise ValueError("expected_thickness must be > 0")
    if tolerance <= 0:
        raise ValueError("tolerance must be > 0")
    if not isinstance(label, str) or not label.strip():
        raise ValueError("label must be a non-empty string")

    outer_kind = outer_face.geomType()
    inner_kind = inner_face.geomType()
    supported = {"CYLINDER", "CONE"}
    if outer_kind not in supported or inner_kind not in supported:
        raise ValueError(
            f"{label} requires final CYLINDER or CONE faces, got "
            f"{outer_kind} and {inner_kind}"
        )
    if outer_kind != inner_kind:
        raise ValueError(
            f"{label} is not a uniform analytic offset: outer face is "
            f"{outer_kind}, inner face is {inner_kind}"
        )

    outer_surface = _analytic_surface(outer_face, outer_kind)
    inner_surface = _analytic_surface(inner_face, inner_kind)
    outer_origin, outer_direction = _axis_receipt(outer_surface)
    inner_origin, inner_direction = _axis_receipt(inner_surface)
    direction_cross = _cross_length(outer_direction, inner_direction)
    if direction_cross > 1e-7:
        raise ValueError(f"{label} faces do not have parallel axes")
    origin_delta = tuple(
        inner_origin[index] - outer_origin[index] for index in range(3)
    )
    axis_offset = _cross_length(origin_delta, outer_direction)
    if axis_offset > tolerance:
        raise ValueError(
            f"{label} faces are not coaxial: axis offset {axis_offset:.9g} mm"
        )

    if outer_kind == "CONE":
        outer_angle = abs(float(outer_surface.SemiAngle()))
        inner_angle = abs(float(inner_surface.SemiAngle()))
        if abs(outer_angle - inner_angle) > 1e-7:
            raise ValueError(
                f"{label} cone angles differ: outer {outer_angle:.9g}, "
                f"inner {inner_angle:.9g} radians"
            )
    else:
        radius_delta = abs(
            float(outer_surface.Radius()) - float(inner_surface.Radius())
        )
        if abs(radius_delta - expected_thickness) > tolerance:
            raise ValueError(
                f"{label} cylinder radius difference expected "
                f"{expected_thickness:g} mm, got {radius_delta:.9g} mm"
            )

    actual = float(outer_face.distance(inner_face))
    if abs(actual - expected_thickness) > tolerance:
        raise ValueError(
            f"{label} normal thickness expected {expected_thickness:g} mm, "
            f"got {actual:.9g} mm on final B-rep faces"
        )
    return {
        "surface_type": outer_kind,
        "thickness_mm": actual,
        "expected_thickness_mm": expected_thickness,
        "axis_offset_mm": axis_offset,
        "tolerance": tolerance,
    }


def verify_clearance_box(
    *,
    part: cq.Workplane | cq.Shape,
    expected_min: tuple[float, float, float],
    expected_max: tuple[float, float, float],
    open_faces: tuple[str, ...] | list[str] = (),
    wall_faces: tuple[str, ...] | list[str] | None = None,
    wall_probe: float = 0.2,
    tolerance: float = 0.01,
    volume_tolerance: float = 1e-6,
    label: str = "clearance box",
) -> dict[str, object]:
    """Prove a final axis-aligned rectangular region is unobstructed.

    The expected box is intersected with the final B-rep, so a skin, post,
    divider, or later union anywhere inside it fails even when sparse point
    samples would miss the obstruction. ``open_faces`` must coincide with the
    part's outer bounding face. For every ``wall_faces`` entry, a thin complete
    slab immediately outside the clearance must remain material. When
    ``wall_faces`` is omitted, every non-open face is required.

    This helper intentionally proves a sharp rectangular region. Do not use it
    as a proxy for a rounded, tapered, or freeform cavity.
    """
    low = _triple("expected_min", expected_min)
    high = _triple("expected_max", expected_max)
    tolerance = _number("tolerance", tolerance)
    wall_probe = _number("wall_probe", wall_probe)
    volume_tolerance = _number("volume_tolerance", volume_tolerance)
    if tolerance <= 0:
        raise ValueError("tolerance must be > 0")
    if wall_probe <= 2 * tolerance:
        raise ValueError("wall_probe must be greater than 2*tolerance")
    if volume_tolerance <= 0:
        raise ValueError("volume_tolerance must be > 0")
    if not isinstance(label, str) or not label.strip():
        raise ValueError("label must be a non-empty string")
    for axis, start, end in zip(_AXES, low, high):
        if end - start <= 4 * tolerance:
            raise ValueError(
                f"expected_max[{axis}] - expected_min[{axis}] must exceed "
                "4*tolerance"
            )

    open_faces = _faces("open_faces", open_faces)
    if wall_faces is None:
        wall_faces = tuple(face for face in _FACE_FRAME if face not in open_faces)
    else:
        wall_faces = _faces("wall_faces", wall_faces)
    overlap = sorted(set(open_faces) & set(wall_faces))
    if overlap:
        raise ValueError(f"open_faces and wall_faces overlap: {overlap}")

    solid = _single_solid(part)
    bbox = solid.BoundingBox()
    outer_low = (float(bbox.xmin), float(bbox.ymin), float(bbox.zmin))
    outer_high = (float(bbox.xmax), float(bbox.ymax), float(bbox.zmax))
    for axis, start, end, outer_start, outer_end in zip(
        _AXES, low, high, outer_low, outer_high
    ):
        if start < outer_start - tolerance or end > outer_end + tolerance:
            raise ValueError(
                f"{label} {axis} bounds [{start:.6g}, {end:.6g}] lie outside "
                f"the final part bbox [{outer_start:.6g}, {outer_end:.6g}]"
            )

    for face in open_faces:
        axis_index, sign = _FACE_FRAME[face]
        boundary = high[axis_index] if sign > 0 else low[axis_index]
        outer = outer_high[axis_index] if sign > 0 else outer_low[axis_index]
        if abs(boundary - outer) > tolerance:
            raise ValueError(
                f"{label} open face {face} must coincide with final bbox "
                f"boundary {outer:.6g} mm, got {boundary:.6g} mm"
            )

    for face in wall_faces:
        axis_index, sign = _FACE_FRAME[face]
        available = (
            outer_high[axis_index] - high[axis_index]
            if sign > 0
            else low[axis_index] - outer_low[axis_index]
        )
        if available + tolerance < wall_probe:
            raise ValueError(
                f"{label} has only {available:.6g} mm available outside {face}; "
                f"wall_probe requires {wall_probe:.6g} mm"
            )

    inset_low = [value + tolerance for value in low]
    inset_high = [value - tolerance for value in high]
    clearance_region = _box_from_bounds(inset_low, inset_high)
    blocked_volume = _intersection_volume(solid, clearance_region)
    if blocked_volume > volume_tolerance:
        raise ValueError(
            f"{label} is obstructed on the final solid: intersection volume "
            f"{blocked_volume:.6g} mm^3 exceeds {volume_tolerance:.6g} mm^3"
        )

    missing_by_face: dict[str, float] = {}
    for face in wall_faces:
        axis_index, sign = _FACE_FRAME[face]
        slab_low = list(inset_low)
        slab_high = list(inset_high)
        if sign > 0:
            slab_low[axis_index] = high[axis_index] + tolerance
            slab_high[axis_index] = high[axis_index] + wall_probe
        else:
            slab_low[axis_index] = low[axis_index] - wall_probe
            slab_high[axis_index] = low[axis_index] - tolerance
        wall_region = _box_from_bounds(slab_low, slab_high)
        expected_volume = float(wall_region.val().Volume())
        material_volume = _intersection_volume(solid, wall_region)
        missing_volume = max(0.0, expected_volume - material_volume)
        missing_by_face[face] = missing_volume
        allowed = max(volume_tolerance, expected_volume * 1e-9)
        if missing_volume > allowed:
            raise ValueError(
                f"{label} lacks continuous surrounding material at {face}: "
                f"missing {missing_volume:.6g} mm^3 from the wall probe"
            )

    return {
        "min": [float(value) for value in low],
        "max": [float(value) for value in high],
        "size": [float(high[i] - low[i]) for i in range(3)],
        "open_faces": list(open_faces),
        "wall_faces": list(wall_faces),
        "wall_probe": wall_probe,
        "tolerance": tolerance,
        "blocked_volume_mm3": blocked_volume,
        "wall_missing_volume_mm3": missing_by_face,
    }


def verify_rectangular_through_cut(
    *,
    part: cq.Workplane | cq.Shape,
    axis: str,
    center: tuple[float, float],
    size: tuple[float, float],
    span: tuple[float, float],
    wall_probe: float = 0.2,
    tolerance: float = 0.01,
    volume_tolerance: float = 1e-6,
    label: str = "rectangular through-cut",
) -> dict[str, object]:
    """Prove a sharp rectangular cut traverses the final solid on X, Y, or Z.

    ``center`` and ``size`` use the plane normal to ``axis``: X -> (Y, Z),
    Y -> (X, Z), and Z -> (X, Y). ``span`` is the exact world-space traversal
    and must meet both corresponding outer bbox faces. The full requested
    prism must be air and four surrounding wall slabs must remain material.
    """
    if not isinstance(axis, str) or axis not in _AXIS_FRAME:
        raise ValueError(f"axis must be one of {sorted(_AXIS_FRAME)}, got {axis!r}")
    center = _pair("center", center)
    size = _pair("size", size)
    span = _pair("span", span)
    if min(size) <= 0:
        raise ValueError("size values must be > 0")
    if span[1] <= span[0]:
        raise ValueError("span end must be greater than span start")

    axis_index, u_index, v_index = _AXIS_FRAME[axis]
    low = [0.0, 0.0, 0.0]
    high = [0.0, 0.0, 0.0]
    low[axis_index], high[axis_index] = span
    low[u_index], high[u_index] = center[0] - size[0] / 2, center[0] + size[0] / 2
    low[v_index], high[v_index] = center[1] - size[1] / 2, center[1] + size[1] / 2
    open_faces = _AXIS_FACES[axis]
    wall_faces = tuple(face for face in _FACE_FRAME if face not in open_faces)
    clearance = verify_clearance_box(
        part=part,
        expected_min=tuple(low),
        expected_max=tuple(high),
        open_faces=open_faces,
        wall_faces=wall_faces,
        wall_probe=wall_probe,
        tolerance=tolerance,
        volume_tolerance=volume_tolerance,
        label=label,
    )
    return {
        "axis": axis,
        "center": [float(value) for value in center],
        "size": [float(value) for value in size],
        "span": [float(value) for value in span],
        "wall_probe": clearance["wall_probe"],
        "tolerance": clearance["tolerance"],
        "blocked_volume_mm3": clearance["blocked_volume_mm3"],
        "wall_missing_volume_mm3": clearance["wall_missing_volume_mm3"],
    }


def verify_through_hole_pattern(
    *,
    part: cq.Workplane | cq.Shape,
    axis: str,
    centers: list[tuple[float, float]] | tuple[tuple[float, float], ...],
    diameter: float,
    span: tuple[float, float],
    scope: tuple[float, float, float, float] | None = None,
    tolerance: float = 0.01,
    sample_margin: float = 0.1,
    label: str = "through-hole pattern",
) -> dict[str, object]:
    """Prove an exact axis-aligned cylindrical through-hole pattern.

    The proof combines final B-rep topology with material/air classification.
    It matches cylindrical faces by exact diameter, axis, and transverse center;
    checks air along the requested world-space ``span``; checks material just
    outside every bore; and rejects extra matching through-holes in ``scope``.

    Center coordinates follow the plane normal to ``axis``: ``x -> (y, z)``,
    ``y -> (x, z)``, and ``z -> (x, y)``. ``scope`` uses the same coordinates as
    ``(u_min, v_min, u_max, v_max)``. Omit it to enforce the exact pattern over
    the whole part; provide it only when another legitimate same-diameter hole
    group exists elsewhere on that part.

    Example::

        proof = verify_through_hole_pattern(
            part=plate,
            axis="z",
            centers=[(-20, -12), (20, -12), (-20, 12), (20, 12)],
            diameter=3.4,
            span=(0, p.thickness),
            label="M3 mounting pattern",
        )
    """
    if not isinstance(axis, str) or axis not in _AXIS_FRAME:
        raise ValueError(f"axis must be one of {sorted(_AXIS_FRAME)}, got {axis!r}")
    if not isinstance(span, (tuple, list)) or len(span) != 2:
        raise ValueError("span must be an explicit world-space (start, end) pair")
    start, end = (_number("span[0]", span[0]), _number("span[1]", span[1]))
    if end <= start:
        raise ValueError("span end must be greater than span start")
    diameter = _number("diameter", diameter)
    tolerance = _number("tolerance", tolerance)
    sample_margin = _number("sample_margin", sample_margin)
    if diameter <= 0:
        raise ValueError("diameter must be > 0")
    if tolerance <= 0:
        raise ValueError("tolerance must be > 0")
    if sample_margin <= 2 * tolerance or sample_margin >= diameter / 4:
        raise ValueError(
            "sample_margin must be greater than 2*tolerance and smaller than "
            "one quarter of the diameter"
        )
    if end - start <= 4 * tolerance:
        raise ValueError("span is too short for a stable through-hole proof")
    if not isinstance(label, str) or not label.strip():
        raise ValueError("label must be a non-empty string")

    centers = _normalize_centers(centers)
    scope = _normalize_scope(scope)
    if any(not _in_scope(center, scope, tolerance) for center in centers):
        raise ValueError("every expected center must lie inside scope")
    for index, center in enumerate(centers):
        if any(
            math.dist(center, other) <= tolerance
            for other in centers[:index]
        ):
            raise ValueError("centers must not contain duplicate hole positions")

    solid = _single_solid(part)
    axis_index, u_index, v_index = _AXIS_FRAME[axis]
    axial_inset = min(sample_margin, (end - start) / 4)
    axis_samples = (start + axial_inset, (start + end) / 2, end - axial_inset)
    radius = diameter / 2
    detected = _candidate_hole_centers(
        solid,
        axis_index=axis_index,
        u_index=u_index,
        v_index=v_index,
        radius=radius,
        axis_samples=axis_samples,
        scope=scope,
        tolerance=tolerance,
    )

    missing = [
        center
        for center in centers
        if not any(math.dist(center, found) <= tolerance for found in detected)
    ]
    unexpected = [
        found
        for found in detected
        if not any(math.dist(found, center) <= tolerance for center in centers)
    ]
    if missing or unexpected or len(detected) != len(centers):
        raise ValueError(
            f"{label} does not match the final cylindrical through-hole set: "
            f"missing={missing}, unexpected={unexpected}, detected={detected}, "
            f"expected_diameter={diameter:.6g} mm"
        )

    diagonal = math.sqrt(0.5)
    radial_directions = (
        (1.0, 0.0),
        (-1.0, 0.0),
        (0.0, 1.0),
        (0.0, -1.0),
        (diagonal, diagonal),
        (diagonal, -diagonal),
        (-diagonal, diagonal),
        (-diagonal, -diagonal),
    )

    def radial_point(
        center: tuple[float, float],
        axis_value: float,
        radial_distance: float,
        direction: tuple[float, float],
    ) -> tuple[float, float, float]:
        return _point_on_axis(
            axis_index,
            u_index,
            v_index,
            axis_value,
            (
                center[0] + radial_distance * direction[0],
                center[1] + radial_distance * direction[1],
            ),
        )

    blocked: list[tuple[float, float, float]] = []
    missing_wall: list[tuple[float, float, float]] = []
    inner_radius = radius - sample_margin
    outer_radius = radius + sample_margin
    for center in centers:
        for axis_value in axis_samples:
            centerline = _point_on_axis(
                axis_index, u_index, v_index, axis_value, center
            )
            air_points = [centerline]
            air_points.extend(
                radial_point(center, axis_value, inner_radius, direction)
                for direction in radial_directions
            )
            blocked.extend(
                point
                for point in air_points
                if solid.isInside(cq.Vector(*point), tolerance)
            )
        midpoint = (start + end) / 2
        material_points = [
            radial_point(center, midpoint, outer_radius, direction)
            for direction in radial_directions
        ]
        missing_wall.extend(
            point
            for point in material_points
            if not solid.isInside(cq.Vector(*point), tolerance)
        )

    if blocked:
        raise ValueError(
            f"{label} is blocked or undersized on the final solid at {blocked}"
        )
    if missing_wall:
        raise ValueError(
            f"{label} is oversized, open-sided, or lacks surrounding material at "
            f"{missing_wall}"
        )

    return {
        "axis": axis,
        "centers": [[float(u), float(v)] for u, v in centers],
        "count": len(centers),
        "diameter": diameter,
        "span": [start, end],
        "scope": list(scope) if scope is not None else None,
        "tolerance": tolerance,
        "air_samples": len(centers) * len(axis_samples) * 9,
        "wall_samples": len(centers) * len(radial_directions),
    }
