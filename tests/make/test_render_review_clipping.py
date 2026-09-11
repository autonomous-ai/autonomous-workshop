"""A fixed close-up clips pixel coverage without deleting visible geometry."""

from pathlib import Path
import runpy

import numpy as np
import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
TOOL = runpy.run_path(str(SCRIPTS / "render_review"))
FRAMING = np.array([[-32, -32, 0], [32, 32, 0]], float)
SIDES_AND_CORNERS = [
    (-12, 32), (76, 32), (32, -12), (32, 76),
    (-12, -12), (76, -12), (76, 76), (-12, 76),
]


def occurrence(screen_points, alpha=1., z=0.):
    screen = np.asarray(screen_points, dtype=float)
    points = np.column_stack([screen[:, 0] - 32, 32 - screen[:, 1], np.full(len(screen), z)])
    return points, np.array([[0, 1, 2]]), (190, 70, 40, alpha)


def outside(center, alpha):
    x, y = center
    return occurrence([[x - 5, y - 5], [x + 5, y - 5], [x, y + 5]], alpha)


def render(scene, *, wide=False):
    return np.asarray(TOOL["render"](
        scene, -90, 90, 128 if wide else 64, 0.,
        framing=FRAMING * (2 if wide else 1),
    ))


@pytest.mark.parametrize("center", SIDES_AND_CORNERS)
@pytest.mark.parametrize("alpha", [1., .4, 0.])
def test_wholly_offscreen_triangles_leave_the_image_unchanged(center, alpha):
    scene = [outside(center, alpha)]
    pixels = render(scene)
    np.testing.assert_array_equal(pixels, np.broadcast_to(TOOL["BACKGROUND"], pixels.shape))


@pytest.mark.parametrize("corner", [False, True])
@pytest.mark.parametrize("quarter_turns", range(4))
@pytest.mark.parametrize("alpha", [1., .4])
def test_partially_visible_triangles_match_a_larger_uncropped_raster(corner, quarter_turns, alpha):
    # Both fixtures cross an image boundary with nonzero visible coverage.
    screen = np.array([[-15, -15], [20, -15], [-15, 20]] if corner
                      else [[-20, 10], [20, 32], [-20, 54]], float)
    for _ in range(quarter_turns):
        screen = np.column_stack([64 - screen[:, 1], screen[:, 0]])
    scene = [occurrence(screen, alpha)]
    pixels = render(scene)
    assert np.any(pixels != TOOL["BACKGROUND"])
    np.testing.assert_array_equal(pixels, render(scene, wide=True)[32:96, 32:96])


def test_closeup_of_full_mixed_scene_matches_uncropped_image_and_preserves_input():
    center = occurrence([[15, 15], [49, 15], [32, 49]], z=-1.)
    cover = occurrence([[-10, 5], [70, 5], [32, 70]], alpha=.25, z=1.)
    scene = [center, cover]
    scene.extend(outside(position, alpha) for position in SIDES_AND_CORNERS for alpha in (1., .4))
    original = [(points.copy(), faces.copy(), colour) for points, faces, colour in scene]
    actual = render(scene)
    np.testing.assert_array_equal(actual, render([center, cover]))
    np.testing.assert_array_equal(actual, render(scene, wide=True)[32:96, 32:96])
    for (points, faces, colour), (old_points, old_faces, old_colour) in zip(scene, original):
        np.testing.assert_array_equal(points, old_points)
        np.testing.assert_array_equal(faces, old_faces)
        assert colour == old_colour
