"""Construct review states with the exact rigid poses used by check_motion."""
from __future__ import annotations

import functools
import io
import math
import runpy
import struct
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parent
TOLERANCE = 0.08
MAX_STATES = 48


@functools.lru_cache(maxsize=1)
def helpers():
    return (runpy.run_path(str(SCRIPTS / "check_motion")),
            runpy.run_path(str(SCRIPTS / "render_review")))


def coupled_conditions(manifest):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("conditions"), list):
        raise ValueError("motion manifest needs a conditions list")
    check, _ = helpers()
    conditions = [c for c in check["flatten_conditions"](manifest["conditions"])
                  if c.get("check") == "coupled_motion_collision"]
    identifiers = [c.get("id") for c in conditions]
    if any(not isinstance(i, str) or not i.strip() or len(i) > 128 for i in identifiers):
        raise ValueError("every coupled motion condition needs a nonempty id")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("coupled motion condition ids must be unique")
    return conditions


def sample_indices(condition, requested=None, frames=8):
    steps = condition.get("inputs", {}).get("steps", helpers()[0]["DEFAULT_STEPS"])
    if type(steps) is not int or not 1 <= steps <= 10000:
        raise ValueError("motion steps must be an integer between 1 and 10000")
    if requested is None:
        if type(frames) is not int or not 8 <= frames <= MAX_STATES:
            raise ValueError("frames must be an integer from 8 to 48")
        requested = [round(steps * i / (frames - 1)) for i in range(frames)]
    if (not isinstance(requested, list) or not 8 <= len(requested) <= MAX_STATES
            or any(type(i) is not int or not 0 <= i <= steps for i in requested)
            or requested != sorted(set(requested))):
        raise ValueError(f"{condition['id']} needs 8 to 48 increasing, distinct sample indices within 0..{steps}")
    return requested


def _finite(value):
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    return not isinstance(value, (float, int)) or math.isfinite(value)


def posed_occurrences(shape, condition, indices):
    """Move each leaf once, including leaves of a named moving group."""
    check, renderer = helpers()
    parts = check["index_parts"](shape)
    inputs = condition.get("inputs", {})
    steps = inputs.get("steps", check["DEFAULT_STEPS"])
    movers = inputs.get("movers")
    if not isinstance(movers, list) or not movers or not _finite(movers):
        raise ValueError("coupled motion needs finite mover specifications")
    transforms = []
    try:
        for index, spec in enumerate(movers):
            if not isinstance(spec, dict) or not isinstance(spec.get("part"), str):
                raise ValueError("every mover needs a part name")
            name = check["resolve_parts"](spec["part"], parts, "mover")[0][0]
            key = parts["__node_keys__"][name]
            if any(key[:len(prior)] == prior or prior[:len(key)] == key
                   for prior, _ in transforms):
                raise ValueError("moving selections overlap; name each occurrence only once")
            transforms.append((key, check["_pose_table"](spec, steps, f"movers[{index}]")))
    except check["ManifestError"] as exc:
        raise ValueError(str(exc)) from exc
    for sample in indices:
        occurrences = []
        for index, (key, leaf, colour) in enumerate(parts["__leaf_nodes__"]):
            moved = leaf
            for ancestor, place in transforms:
                if key[:len(ancestor)] == ancestor:
                    moved = place(leaf, sample)
                    break
            vertices, triangles = moved.tessellate(TOLERANCE)
            points = np.asarray([[v.X, v.Y, v.Z] for v in vertices], dtype=float)
            faces = np.asarray(triangles, dtype=np.int64)
            if not len(points) or not len(faces) or not np.isfinite(points).all():
                raise ValueError("motion occurrence has no finite triangulated geometry")
            if colour is None:
                rgb = renderer["FALLBACK_COLOURS"][index % len(renderer["FALLBACK_COLOURS"])]
            else:
                rgb = tuple(renderer["_linear_to_srgb"](float(c)) for c in tuple(colour)[:3])
            occurrences.append((points, faces, rgb))
        if not occurrences:
            raise ValueError("motion assembly has no drawable leaves")
        yield sample, occurrences


def stl_bytes(occurrences):
    """Stable binary STL: retain winding, normalize triangle ordering."""
    triangles = np.concatenate([p[f] for p, f, _ in occurrences]).astype("<f4")
    if not np.isfinite(triangles).all():
        raise ValueError("motion triangles are not finite")
    triangles[triangles == 0] = 0  # normalize negative zero
    starts = np.lexsort((triangles[:, :, 2], triangles[:, :, 1], triangles[:, :, 0]), axis=1)[:, 0]
    indices = (starts[:, None] + np.arange(3)) % 3
    triangles = np.take_along_axis(triangles, indices[:, :, None], axis=1)
    flat = triangles.reshape(-1, 9)
    triangles = triangles[np.lexsort(tuple(flat[:, i] for i in range(8, -1, -1)))]
    records = np.zeros(len(triangles), dtype=[("normal", "<f4", 3), ("points", "<f4", (3, 3)), ("attribute", "<u2")])
    normals = np.cross(triangles[:, 1].astype(float) - triangles[:, 0],
                       triangles[:, 2].astype(float) - triangles[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    valid = lengths > 0
    normals[valid] /= lengths[valid, None]
    records["normal"] = normals
    records["points"] = triangles
    return b"Workshop declared motion state v2".ljust(80, b"\0") + struct.pack("<I", len(records)) + records.tobytes()


def validate_render(settings):
    if not isinstance(settings, dict) or set(settings) != {"azimuth", "elevation", "size"}:
        raise ValueError("invalid motion render settings")
    if type(settings["size"]) is not int or not 256 <= settings["size"] <= 1024:
        raise ValueError("motion render size must be 256 to 1024")
    for key in ("azimuth", "elevation"):
        if type(settings[key]) not in (int, float) or not math.isfinite(settings[key]) or abs(settings[key]) > 360:
            raise ValueError("motion camera angles must be finite and within +/-360 degrees")


def animation_bytes(states, settings):
    validate_render(settings)
    _, renderer = helpers()
    framing = np.concatenate([p for _, occurrences in states for p, _, _ in occurrences])
    frames = [renderer["render"](occurrences, settings["azimuth"], settings["elevation"],
                                 settings["size"], .07, framing=framing)
              for _, occurrences in states]
    stream = io.BytesIO()
    frames[0].save(stream, format="GIF", save_all=True, append_images=frames[1:], duration=120, loop=0, disposal=2)
    return stream.getvalue()


def construct(project, manifest, selections):
    """Return the source entry and all selected states in manifest order."""
    check, _ = helpers()
    conditions = coupled_conditions(manifest)
    if not conditions or set(selections) != {c["id"] for c in conditions}:
        raise ValueError("motion presentation must cover every coupled condition exactly once")
    indices_by_id = {c["id"]: sample_indices(c, selections[c["id"]]) for c in conditions}
    if sum(map(len, indices_by_id.values())) > MAX_STATES:
        raise ValueError("motion presentation exceeds 48 states across its coupled conditions")
    entry = check["find_assembly_entry"](project, manifest.get("assembly"))
    try:
        relative = entry.relative_to(project).as_posix()
    except ValueError as exc:
        raise ValueError("motion assembly entry must be inside the project") from exc
    target = project
    for component in Path(relative).parts:
        target = target / component
        if target.is_symlink():
            raise ValueError("linked motion assembly entry is forbidden")
    if not entry.resolve().is_relative_to(project.resolve()):
        raise ValueError("motion assembly entry must resolve inside the project")
    try:
        shape = check["build_assembly"](entry)
    except Exception as exc:
        raise ValueError(f"cannot build motion assembly: {type(exc).__name__}: {exc}") from exc
    states = []
    for condition in conditions:
        indices = indices_by_id[condition["id"]]
        states.extend(({"condition_id": condition["id"], "sample_index": sample}, occurrences)
                      for sample, occurrences in posed_occurrences(shape, condition, indices))
    if not 8 <= len(states) <= MAX_STATES:
        raise ValueError("motion presentation needs 8 to 48 states across its coupled conditions")
    return relative, states
