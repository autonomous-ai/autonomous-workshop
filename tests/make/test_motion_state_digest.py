"""Canonical state compatibility and large synthetic presentation contracts."""
import hashlib
import io
import json
import runpy
import struct
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
STATES = runpy.run_path(str(TOOLS / "motion_states.py"))
PRESENTATION = runpy.run_path(str(TOOLS / "motion_presentation.py"))
FACETS_ABOVE_OLD_LIMIT = 419_429


def mixed_occurrences():
    points = np.array([
        [-0., 0., 0.], [1.125, 0., 0.], [0., 1.5, 0.], [0., 0., 2.25],
        [-2., 3., 4.], [.123456789, -.4, 1.8], [1e-40, 0., 0.],
    ])
    faces = np.array([[4, 3, 5], [0, 1, 2], [2, 1, 0], [6, 6, 6], [0, 3, 1]])
    return points, faces, (80, 90, 100, 120)


@pytest.mark.parametrize("reverse,expected", [
    (False, "e20e31fce4484c173f5827e2c6bafcffd6048535770eae0a50f00a2e31e067c1"),
    (True, "8583891c43ffb3cf47358f29b67ef3821abc125397942078e2cfeb0590c6e47f"),
])
def test_digest_matches_pre_streaming_encoding(reverse, expected):
    # Hashes captured from the preceding encoder, including float32 rounding,
    # non-axis normals, negative zero, opposite winding and a degenerate face.
    points, faces, color = mixed_occurrences()
    if reverse:
        faces = faces[:, ::-1]
    original_points, original_faces = points.copy(), faces.copy()
    occurrence = [(points, faces, color)]
    assert STATES["state_digest"](occurrence) == expected
    assert hashlib.sha256(STATES["state_bytes"](occurrence)).hexdigest() == expected
    shuffled = np.roll(faces[::-1], 1, axis=1)
    split = [(points, shuffled[:2], color), (points, shuffled[2:], color)]
    assert STATES["state_digest"](split) == expected
    assert points.tobytes() == original_points.tobytes()
    assert faces.tobytes() == original_faces.tobytes()


def repeated_triangle(x=0.):
    points = np.array([[x, 0., 0.], [x + 1., 0., 0.], [x, 1., 0.]])
    faces = np.broadcast_to(np.array([0, 1, 2]), (FACETS_ABOVE_OLD_LIMIT, 3))
    return [(points, faces, (80, 90, 100, 120))]


def test_large_digest_streams_every_record_without_full_encoding(monkeypatch):
    globals_ = STATES["state_digest"].__globals__
    original_chunks = globals_["_state_chunks"]
    sizes = []

    def trace(occurrences):
        for chunk in original_chunks(occurrences):
            sizes.append(len(chunk))
            yield chunk

    monkeypatch.setitem(globals_, "_state_chunks", trace)
    actual = STATES["state_digest"](repeated_triangle())
    header = b"Workshop declared motion state v2".ljust(80, b"\0") + struct.pack("<I", FACETS_ABOVE_OLD_LIMIT)
    # The preceding binary encoding: +Z normal, canonical cyclic start,
    # three vertices, and a zero attribute word. Every repeated facet remains.
    record = struct.pack("<12fH", 0., 0., 1., 0., 0., 0., 1., 0., 0., 0., 1., 0., 0)
    expected = hashlib.sha256(header)
    for start in range(0, FACETS_ABOVE_OLD_LIMIT, 65536):
        expected.update(record * min(65536, FACETS_ABOVE_OLD_LIMIT - start))
    assert actual == expected.hexdigest()
    assert sizes[0] == 84
    assert sum(sizes) == 84 + 50 * FACETS_ABOVE_OLD_LIMIT > 20 * 1024 * 1024
    assert max(sizes) <= 65536 * 50
    assert len(sizes) > 2


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_state_still_fails_without_mutating_input(value):
    points, faces, color = mixed_occurrences()
    points[0, 0] = value
    before = points.tobytes()
    for encode in (STATES["state_digest"], STATES["state_bytes"]):
        with pytest.raises(ValueError, match="motion triangles are not finite"):
            encode([(points, faces, color)])
        assert points.tobytes() == before


def test_eight_large_states_generate_and_reconcile_without_state_bytes(tmp_path, monkeypatch):
    (tmp_path / "measure").mkdir()
    (tmp_path / "model.step.py").write_text("# synthetic geometry supplied by the fixture\n")
    condition = {"id": "turn", "check": "coupled_motion_collision", "inputs": {"steps": 7}}
    manifest = {"assembly": "model.step.py", "conditions": [condition]}
    (tmp_path / "measure/motion.json").write_text(json.dumps(manifest))
    states = [({"condition_id": "turn", "sample_index": i}, repeated_triangle(i / 8)) for i in range(8)]
    constructions = []
    encoded = []

    def construct(project, observed, selections):
        assert project == tmp_path and observed == manifest
        assert selections == {"turn": list(range(8))}
        constructions.append(selections)
        return "model.step.py", states

    def animation(observed, settings):
        assert observed is states and settings == {"azimuth": 0., "elevation": 0., "size": 256}
        assert all(occurrences[0][2] == (80, 90, 100, 120) for _, occurrences in observed)
        frames = [Image.new("RGB", (256, 256), (int(occurrences[0][0][0, 0] * 160), 100, 200))
                  for _, occurrences in observed]
        stream = io.BytesIO()
        frames[0].save(stream, format="GIF", save_all=True, append_images=frames[1:], duration=120, loop=0, disposal=2)
        return stream.getvalue()

    def digest(occurrences):
        result = STATES["state_digest"](occurrences)
        encoded.append(result)
        return result

    def forbidden_bytes(_):
        pytest.fail("presentation must hash full states without allocating state_bytes")

    tools = {**STATES, "construct": construct, "animation_bytes": animation,
             "coupled_conditions": lambda _: [condition], "state_digest": digest,
             "state_bytes": forbidden_bytes,
             "helpers": lambda: ({}, {"parse_view": lambda _: ("iso", 0., 0.)})}
    monkeypatch.setitem(PRESENTATION["generate"].__globals__, "state_tool", lambda: tools)
    evidence = PRESENTATION["generate"](tmp_path, size=256)
    assert len(encoded) == len(set(encoded)) == len(evidence["states"]) == 8
    assert all(row["sha256"] == expected for row, expected in zip(evidence["states"], encoded))
    signature = {"concept_sha256": "a" * 64, "reviewer": "synthetic-test-critic", "review_rounds": 1}
    review = {"schema_version": 1, **signature,
              "evidence_sha256": hashlib.sha256(PRESENTATION["canonical"](evidence)).hexdigest(),
              "blind_motion_read": "Synthetic fixture: eight translated states.",
              "motion_matches_wish": True, "simulation_not_physical_test": True}
    (tmp_path / PRESENTATION["REVIEW"]).write_bytes(PRESENTATION["canonical"](review))
    PRESENTATION["validate"](tmp_path, signature)
    assert len(constructions) == 2 and encoded[:8] == encoded[8:]
    assert not list(tmp_path.rglob("*.stl")) and not list(tmp_path.rglob("*.3mf"))
    # Same files and reviewed evidence, different reconstructed geometry: fail.
    states[0] = (states[0][0], repeated_triangle(2.))
    with pytest.raises(ValueError, match="differs from the checked poses"):
        PRESENTATION["validate"](tmp_path, signature)
