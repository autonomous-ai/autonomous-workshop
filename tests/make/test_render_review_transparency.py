"""Source opacity survives still review and reconciled motion presentation."""

import hashlib
import io
import json
from pathlib import Path
import runpy
from unittest import mock

import numpy as np
import pytest
from PIL import Image
from build123d import Box, Color, Compound

from tests.make.test_motion_presentation import HELPER, STATES, condition, rebind_test_evidence


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
TOOL = runpy.run_path(str(SCRIPTS / "render_review"))
FRAMING = np.array([[-10, -10, -10], [10, 10, 10]], float)


def plane(z, colour, slope=0, diagonal=False):
    points = np.array([[-10, -10, z - 10*slope], [10, -10, z + 10*slope],
                       [10, 10, z + 10*slope], [-10, 10, z - 10*slope]], float)
    faces = np.array([[0, 1, 3], [1, 2, 3]] if diagonal else [[0, 1, 2], [0, 2, 3]])
    return points, faces, colour


def render(scene, size=128):
    return np.asarray(TOOL["render"](scene, -90, 90, size, .07, framing=FRAMING))


def shade(colour, slope=0):
    light = np.array([.35, -.45, .82]); light /= np.linalg.norm(light)
    return np.array(TOOL["_shade"](colour[:3], np.array([-slope, 0, 1]), light, np.array([0, 0, 1])), float)


def over(front_to_back, background=TOOL["BACKGROUND"]):
    pixel = np.array(background, float)
    for colour, alpha in reversed(front_to_back):
        pixel = colour * alpha + pixel * (1 - alpha)
    return np.rint(pixel).astype(np.uint8)


def test_rgb_and_explicit_opaque_rgba_have_identical_pixels():
    rgb = [plane(-1, (30, 80, 170), slope=.3), plane(1, (220, 70, 30))]
    rgba = [(p, f, (*c, 1.0)) for p, f, c in rgb]
    np.testing.assert_array_equal(render(rgb), render(rgba))


def test_fully_transparent_cover_has_no_occlusion_with_fixed_framing():
    rear = plane(-1, (220, 40, 30))
    np.testing.assert_array_equal(render([rear]), render([rear, plane(4, (40, 100, 220, 0.0))]))


@pytest.mark.parametrize("layers", [2, 3, 12])
def test_every_transparent_layer_composites_in_front_of_opaque_surface(layers):
    rear = (220, 70, 30)
    colours = [(30 + i*5, 90, 190, .18) for i in range(layers)]
    scene = [plane(-2, (10, 250, 10, .7)), plane(-1, rear)]
    scene.extend(plane(i * .2, c) for i, c in enumerate(colours))
    expected = over([(shade(c), c[3]) for c in reversed(colours)], shade(rear))
    np.testing.assert_array_equal(render(scene)[64, 64], expected)


def test_crossing_layers_use_each_pixels_depth_and_ignore_input_order():
    red, blue = (200, 40, 30, .4), (30, 70, 210, .6)
    scene = [plane(0, red, slope=.5), plane(0, blue)]
    actual = render(scene)
    np.testing.assert_array_equal(actual[64, 40], over([(shade(blue), .6), (shade(red, .5), .4)]))
    np.testing.assert_array_equal(actual[64, 88], over([(shade(red, .5), .4), (shade(blue), .6)]))
    reversed_scene = [(p, np.roll(f[::-1], 1, axis=1), c) for p, f, c in reversed(scene)]
    np.testing.assert_array_equal(actual, render(reversed_scene))


def test_shared_edges_do_not_double_opacity_and_tied_occurrences_stay_distinct():
    colour = (30, 80, 180, .3)
    first = plane(0, colour)
    alternate = plane(0, colour, diagonal=True)
    np.testing.assert_array_equal(render([first]), render([alternate]))
    points, faces, _ = first
    center = points.mean(axis=0)
    split_points = np.vstack([points, center])
    split_faces = np.array([[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]])
    np.testing.assert_array_equal(render([first]), render([(split_points, split_faces, colour)]))
    second = plane(0, (180, 60, 30, .5))
    np.testing.assert_array_equal(render([first, second]), render([second, first]))
    expected = over([(shade(second[2]), .5), (shade(colour), .3)])
    np.testing.assert_array_equal(render([first, second])[64, 64], expected)
    np.testing.assert_array_equal(render([first, first])[64, 64], over([(shade(colour), .3)] * 2))


def test_unequal_sloped_triangles_share_one_half_open_edge():
    scale = .86 * 128 / 20
    sample_y = -.5 / scale
    edge_y = sample_y - 1e-10
    xy = np.array([[-10, edge_y], [10, edge_y], [0, edge_y - 10], [0, edge_y + 1e-6]])
    points = np.column_stack([xy, 2 + .4 * xy[:, 0]])
    faces = np.array([[0, 2, 1], [0, 1, 3]])
    colour = (40, 90, 170, .4)
    expected = over([(shade(colour, .4), .4)])
    first = render([(points, faces, colour)])
    np.testing.assert_array_equal(first[64, 64], expected)
    # List order and cyclic corner rotations cannot change edge ownership.
    np.testing.assert_array_equal(first, render([(points, np.roll(faces[::-1], 1, axis=1), colour)]))


@pytest.mark.parametrize("gap", [1e-7, .75e-9])
def test_distinct_thin_surfaces_in_one_occurrence_are_both_visible(gap):
    lower, upper = plane(0, (50, 90, 160, .2)), plane(gap, (50, 90, 160, .2))
    merged = (np.concatenate([lower[0], upper[0]]), np.concatenate([lower[1], upper[1] + 4]), lower[2])
    np.testing.assert_array_equal(render([merged])[64, 64], over([(shade(lower[2]), .2)] * 2))


def test_near_coplanar_depth_rank_order_terminates_and_retains_all_layers():
    # An epsilon depth/rank comparator is nontransitive for these three
    # depths: it can revisit the same layer forever instead of peeling it.
    colours = [(180, 80, 30, .2), (100, 70, 80, .3), (40, 60, 160, .4)]
    scene = [plane(z, colour) for z, colour in zip([0, .75e-9, 1.5e-9], colours)]
    expected = over([(shade(c), c[3]) for c in reversed(colours)])
    # A deterministic test watchdog catches a regression without a hung suite.
    original = np.full
    calls = 0

    def bounded(*args, **kwargs):
        nonlocal calls
        calls += 1
        assert calls < 200, "transparent depth peeling revisited prior layers"
        return original(*args, **kwargs)

    with mock.patch.object(np, "full", side_effect=bounded):
        actual = render(scene)
    np.testing.assert_array_equal(actual[64, 64], expected)


def test_nested_alpha_and_both_shell_surfaces_survive_tessellation():
    cover = Box(10, 10, .4).translate((0, 0, 4))
    cover.label = "cover"
    group = Compound(children=[cover], label="glass")
    group.color = Color(.4, .7, 1, .18)
    root = Compound(children=[group])
    occurrences = TOOL["tessellate_occurrences"](root, .08)
    assert cover._color is None
    assert occurrences[0][2][3] == .18
    light = np.array([.35, -.45, .82]); light /= np.linalg.norm(light)
    rgb = occurrences[0][2][:3]
    front = np.array(TOOL["_shade"](rgb, np.array([0, 0, 1]), light, np.array([0, 0, 1])))
    back = np.array(TOOL["_shade"](rgb, np.array([0, 0, -1]), light, np.array([0, 0, 1])))
    np.testing.assert_array_equal(render(occurrences)[64, 64], over([(front, .18), (back, .18)]))


@pytest.mark.parametrize("alpha", [float("nan"), float("inf"), -.1, 1.1])
def test_invalid_alpha_is_rejected(alpha):
    with pytest.raises(ValueError, match="opacity"):
        render([plane(0, (80, 100, 120, alpha))])
    with pytest.raises(ValueError, match="opacity"):
        TOOL["_colour_channels"]((.2, .4, .6, alpha), 0)


def test_layer_count_does_not_grow_pixel_workspace():
    original = TOOL["_composite_transparent"]
    allocations = []
    numpy_zeros = np.zeros

    def record(shape, *args, **kwargs):
        if isinstance(shape, tuple):
            allocations.append(shape)
        return numpy_zeros(shape, *args, **kwargs)

    def wrapped(*args, **kwargs):
        with mock.patch.object(np, "zeros", side_effect=record):
            return original(*args, **kwargs)

    for count in (2, 16):
        allocations.clear()
        with mock.patch.dict(TOOL["render"].__globals__, {"_composite_transparent": wrapped}):
            render([plane(i, (40, 90, 160, .1)) for i in range(count)], size=128)
        assert allocations
        assert all(shape[0] <= 32 and shape[1] == 128 for shape in allocations)
        assert max(np.prod(shape) for shape in allocations) == 32 * 128 * 3


def test_compositor_allocation_failure_is_not_returned_as_a_partial_image():
    original = TOOL["_composite_transparent"]

    def exhausted(*args, **kwargs):
        with mock.patch.object(np, "full", side_effect=MemoryError("synthetic exhausted workspace")):
            return original(*args, **kwargs)

    with mock.patch.dict(TOOL["render"].__globals__, {"_composite_transparent": exhausted}):
        with pytest.raises(MemoryError, match="exhausted workspace"):
            render([plane(0, (40, 90, 160, .4))])


def transparent_motion_fixture(project):
    (project / "measure").mkdir()
    (project / "model.step.py").write_text('''from build123d import Box, Color, Compound
def gen_step():
    driver = Box(2, 1, 1).translate((4, 0, 0))
    driver.label = "driver"
    driver.color = Color(.9, .02, .01)
    frame = Box(14, 14, .5).translate((0, 0, -3))
    frame.label = "frame"
    frame.color = Color(.15, .2, .3)
    cover = Box(14, 14, .4).translate((0, 0, 3))
    cover.label = "cover"
    hood = Compound(children=[cover], label="hood")
    hood.color = Color(.4, .7, 1, .18)
    return Compound(children=[driver, frame, hood], label="root")
''')
    (project / "measure/motion.json").write_text(json.dumps({"assembly": "model.step.py", "conditions": [condition()]}))
    evidence = HELPER["generate"](project, view="top", size=256)
    signature = {"concept_sha256": "a" * 64, "reviewer": "synthetic-test-critic", "review_rounds": 1}
    review = {"schema_version": 1, **signature,
              "evidence_sha256": hashlib.sha256(HELPER["canonical"](evidence)).hexdigest(),
              "blind_motion_read": "Synthetic fixture: red block moves under the transparent enclosure.",
              "motion_matches_wish": True, "simulation_not_physical_test": True}
    (project / HELPER["REVIEW"]).write_bytes(HELPER["canonical"](review))
    return signature


def test_transparent_motion_gif_generates_and_reconciles_with_full_enclosure(tmp_path):
    signature = transparent_motion_fixture(tmp_path)
    HELPER["validate"](tmp_path, signature)
    manifest = json.loads((tmp_path / "measure/motion.json").read_text())
    _, states = STATES["construct"](tmp_path, manifest, {"turn": [0, 1, 2, 3, 5, 6, 7, 8]})
    assert all(len(occurrences) == 3 and occurrences[-1][2][3] == .18 for _, occurrences in states)
    with Image.open(tmp_path / "snap/motion.gif") as animation:
        assert animation.n_frames >= 3
    source = tmp_path / "model.step.py"
    source.write_text(source.read_text().replace("1, .18", "1, .5"))
    with pytest.raises(ValueError, match="stale CAD sources"):
        HELPER["validate"](tmp_path, signature)


def test_rehashed_replacement_transparent_animation_is_still_rejected(tmp_path):
    signature = transparent_motion_fixture(tmp_path)
    evidence = json.loads((tmp_path / HELPER["EVIDENCE"]).read_bytes())
    frames = [Image.new("RGB", (256, 256), (i*25, 80, 150)) for i in range(8)]
    stream = io.BytesIO()
    frames[0].save(stream, format="GIF", save_all=True, append_images=frames[1:], duration=120, loop=0)
    (tmp_path / "snap/motion.gif").write_bytes(stream.getvalue())
    evidence["animation_sha256"] = hashlib.sha256(stream.getvalue()).hexdigest()
    rebind_test_evidence(tmp_path, evidence)
    with pytest.raises(ValueError, match="differs from its reconciled geometry"):
        HELPER["validate"](tmp_path, signature)
