"""Verify Manhattan Nocturne's Factory whole-product renderer handoff."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(
    0,
    str(
        PROJECT.parents[4]
        / "src"
        / "workshop"
        / "make"
        / "skills"
        / "cad"
        / "scripts"
    ),
)

import params as p  # noqa: E402
from meshlib import components, load_stl, weld  # noqa: E402


ASSEMBLED = PROJECT / "assembled.stl"
SIDECAR = PROJECT / "assembled.step.json"
# The combined export and the fine per-part print meshes use different chordal
# tolerances, so a curved silhouette may miss its analytic extreme by a small
# fraction of a millimetre even though its placement is identical.
BOUNDS_TOLERANCE_MM = 0.25


def _expected_occurrences() -> list[tuple[str, str]]:
    occurrences = [("board", "exports/stl/part_board.stl")]
    for side, back_rank_index, pawn_rank_index in (
        ("stone", 0, 1),
        ("steel", 7, 6),
    ):
        for file_index, role in enumerate(p.BACK_RANK):
            file_name = chr(ord("a") + file_index)
            occurrences.extend(
                (
                    (
                        f"{side}_{role}_{file_name}{back_rank_index + 1}",
                        f"exports/stl/part_{side}_{role}.stl",
                    ),
                    (
                        f"{side}_pawn_{file_name}{pawn_rank_index + 1}",
                        f"exports/stl/part_{side}_pawn.stl",
                    ),
                )
            )
    return occurrences


def _mesh_bounds(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    vertices, faces = weld(load_stl(path))
    pairs = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]]))
    vertex_labels = components(len(vertices), pairs)
    face_labels = vertex_labels[faces[:, 0]]
    ordered_labels = sorted(np.unique(face_labels), key=lambda label: np.flatnonzero(face_labels == label)[0])
    bounds = np.array(
        [
            (
                vertices[np.unique(faces[face_labels == label])].min(axis=0),
                vertices[np.unique(faces[face_labels == label])].max(axis=0),
            )
            for label in ordered_labels
        ]
    )
    return vertices, faces, bounds


def _expected_translation(name: str) -> np.ndarray:
    if name == "board":
        return np.zeros(3)
    _side, _role, square = name.split("_")
    file_index = ord(square[0]) - ord("a")
    rank_index = int(square[1:]) - 1
    x, y = p.square_center(file_index, rank_index)
    return np.array((x, y, p.square_top_z(file_index, rank_index)))


def main() -> int:
    assert not (PROJECT / "_panda_artifact.json").exists(), (
        "the verified-family schema requires unique part paths; this repeated-piece "
        "assembly must use Factory's 33-occurrence sidecar contract"
    )
    payload = json.loads(SIDECAR.read_text(encoding="utf-8"))
    assert payload.get("entryKind") == "assembly"
    assert payload.get("primaryPose") == "assembled"

    parts = payload.get("parts")
    assert isinstance(parts, list)
    observed = [(part.get("name"), part.get("stlPath")) for part in parts]
    expected = _expected_occurrences()
    assert observed == expected, "sidecar order must match the assembly source's add order"

    combined_vertices, _combined_faces, component_bounds = _mesh_bounds(ASSEMBLED)
    assert len(component_bounds) == len(expected) == 33

    reference_bounds: dict[str, np.ndarray] = {}
    for index, ((name, relative), observed_bounds) in enumerate(zip(expected, component_bounds)):
        path = (PROJECT / relative).resolve()
        path.relative_to(PROJECT.resolve())
        assert path.is_file(), f"missing canonical part mesh: {relative}"
        reference = reference_bounds.get(relative)
        if reference is None:
            reference_vertices, _reference_faces, _reference_components = _mesh_bounds(path)
            reference = np.array((reference_vertices.min(axis=0), reference_vertices.max(axis=0)))
            reference_bounds[relative] = reference
        translated = reference + _expected_translation(name)
        assert np.allclose(
            observed_bounds,
            translated,
            atol=BOUNDS_TOLERANCE_MM,
            rtol=0.0,
        ), f"component {index} ({name}) is not in its declared assembly pose"

    assert np.allclose(
        combined_vertices.max(axis=0) - combined_vertices.min(axis=0),
        np.array((244.0, 244.0, 83.35)),
        atol=BOUNDS_TOLERANCE_MM,
        rtol=0.0,
    )
    print(
        "check_factory_handoff: ok - Factory primary mesh contains "
        "1 board + 32 correctly ordered and placed pieces"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
