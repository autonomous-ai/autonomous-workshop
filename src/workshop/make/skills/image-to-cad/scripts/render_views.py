#!/usr/bin/env python3
"""Silhouette renderer: the producer `check_likeness.py` lost.

`check_likeness` has been inert since the Playwright/three.js snapshot renderer
was removed -- the script still worked, but nothing in the toolchain wrote a
`<render>.png` for it to read. So the only gate that asks whether an
image-derived model *looks like its reference* could not run, and every
remaining gate answered soundness instead.

This is that producer, rebuilt on what is already installed. It tessellates the
shape once, projects the triangles, and fills them. The union of a closed
solid's projected triangles **is** its silhouette, so no shading, no lighting,
no GL context and no browser are involved:

    import STEP                     0.32 s
    tessellate (11,716 triangles)   1.65 s
    each view after that            0.04 s

Measured on a 63-occurrence assembly. Nothing is imported that build123d,
numpy and Pillow do not already bring.

Two properties the removed renderer had, that CLAUDE.md requires any
replacement to keep, are structural here rather than optional:

  no burnt-in view label   nothing is drawn but the object. A view chip is
                           opaque to any threshold and stretched the first
                           run's front view to IoU 0.10.
  the same camera          every pose written is recorded in `poses.json` and
                           can be replayed with --poses-from, so a re-render
                           after an edit is the same camera and the IoU delta
                           is the shape's, not the viewpoint's.

WHAT MAKES 0.90 REACHABLE

A reference photograph has an unknown azimuth, elevation and focal length. An
orthographic render compared against a photo taken 15 deg off will not reach
IoU 0.90 even when the model is right, so a bare render turns the gate into a
measure of how well you guessed the camera. `--match` removes that: it searches
the pose space, scoring with `check_likeness`'s own `normalise` and `compare`,
and keeps the best. What the gate then reports is the disagreement in *shape*.

    render_views.py <src> --view front --view iso -o snap/
    render_views.py <src> --match ref/03-side.png --label side -o snap/
    render_views.py <src> --poses-from snap/poses.json          # replay
    render_views.py <src> --compare-step                        # stale STEP?

`--compare-step` restores the other thing that died with the renderer: it
builds the source in memory, imports the sibling `.step`, renders both from the
front, right and top, and compares. A picture is what caught output/boeing-737-v2,
where every deterministic check passed against a STEP that no longer matched its
source; since then `rm -rf __cadgen__` has been the only defence.

Three orthogonal silhouettes do not see everything, and it is worth knowing
what they miss before trusting a clean report. Shortening a pocket that opens
downward moved the front view to IoU 0.948 and left right and top at exactly
1.0000, because material outside the pocket still spans those two outlines. An
internal change with no effect on any of the three reads as "same". Clean here
means no drift was *seen*, and `rm -rf __cadgen__` after editing a `*_lib.py`
is still the discipline.

WHAT IT DELIBERATELY DOES NOT DO

It draws a silhouette, not a picture. Interior edges, colour and material are
absent, because the gate downstream is blind to all three -- rendering them
would cost time and change no number. Read a passing IoU as a floor on the
disagreement, never as a ceiling on the quality: a correct outline in one flat
colour scores the same as the real thing.

It also does not decide the pose is *right*. A search that lands at IoU 0.93 on
a nonsense elevation has found the best available lie about a wrong shape; the
recovered pose is printed for exactly that reason, and a pose far from the one
the photograph plainly shows is a finding, not a pass.

    --self-check   run the fixtures and exit

Exit 0 when everything asked for succeeded, 1 when a --match fell below --min
or a --compare-step found drift, 2 on bad usage.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import math
import shlex
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SCRIPTS_DIR = Path(__file__).resolve().parent
CAD_SCRIPTS_DIR = SCRIPTS_DIR.parents[1] / "cad" / "scripts"
for _runtime_path in (SCRIPTS_DIR, CAD_SCRIPTS_DIR, CAD_SCRIPTS_DIR / "packages",
                      CAD_SCRIPTS_DIR / "packages" / "cadgen" / "src"):
    _text = str(_runtime_path)
    if _runtime_path.is_dir() and _text not in sys.path:
        sys.path.insert(0, _text)

from check_likeness import (  # noqa: E402
    clipped_edges,
    compare,
    normalise,
    require_complete_reference,
    silhouette,
)
from measure_image import _flood_components, _open_mask  # noqa: E402

# Built at runtime for the same reason as check_fit's: cadgen's discovery scan
# treats any worktree file carrying these bytes as a generator candidate.
GEN_FUNC = "gen_" + "step"
ENTRY_SUFFIX = ".step.py"

DEFAULT_SIZE = 480
DEFAULT_TOLERANCE = 0.1
DEFAULT_PAD = 0.04
SEARCH_SIZE = 240
STALE_MIN_IOU = 0.999
# Two references that the search hands the SAME camera must look the same. When
# they do not, the reference mask is lying and every IoU in the run is about the
# mask rather than the shape -- see `mask_contradictions`.
SAME_CAMERA_DEG = 20.0
DIFFERENT_SILHOUETTE_IOU = 0.85

# Z-up, right-handed. Azimuth is measured from +X toward +Y; elevation from the
# XY plane. "front" looks from -Y, which puts +X to the right and +Z up -- the
# convention every CAD front view uses.
NAMED_VIEWS = {
    "front":  (-90.0, 0.0),
    "back":   (90.0, 0.0),
    "right":  (0.0, 0.0),
    "side":   (0.0, 0.0),
    "left":   (180.0, 0.0),
    "top":    (-90.0, 90.0),
    "bottom": (-90.0, -90.0),
    "iso":    (-45.0, 35.264),
}


# --------------------------------------------------------------------------
# building the shape


def load_entry(path: Path):
    """Import one generator with its project directory on sys.path."""
    module_name = f"_render_{path.name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    project = str(path.parent)
    if project not in sys.path:
        sys.path.insert(0, project)
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def resolve_source(source: Path) -> Path:
    """A directory means its combined entry -- the one no part_ prefix claims."""
    if not source.is_dir():
        return source
    entries = [p for p in sorted(source.glob("*" + ENTRY_SUFFIX))
               if not p.name.startswith("part_")]
    if not entries:
        entries = sorted(source.glob("*" + ENTRY_SUFFIX))
    if not entries:
        raise ValueError(f"{source} holds no {ENTRY_SUFFIX} entry")
    return entries[0]


def build_shape(source: Path):
    """The built shape, from a generator (in memory) or from a .step file.

    Building from source is the point: it is what makes the render answerable
    to the code rather than to an artifact that may predate it.
    """
    if source.name.endswith(ENTRY_SUFFIX):
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            module = load_entry(source)
            builder = getattr(module, GEN_FUNC, None)
            if builder is None:
                raise AttributeError(f"{source.name} defines no {GEN_FUNC}()")
            shape = builder()
        if shape is None:
            raise ValueError(f"{source.name} {GEN_FUNC}() returned None")
        return shape
    if source.suffix.lower() in {".step", ".stp"}:
        from build123d import import_step
        return import_step(str(source))
    raise ValueError(f"{source} is neither a {ENTRY_SUFFIX} entry nor a .step")


def tessellate(shape, tolerance: float = DEFAULT_TOLERANCE):
    """Vertices and triangles, once. Every pose after this is pure arithmetic.

    Silhouette error from tessellation is about `tolerance` in model units: on
    a 100 mm object rendered 480 px tall, 0.1 mm is 0.5 px. The pose search
    below moves the outline by more than that, so refining it further buys
    nothing the gate can see.

    OCCT occasionally leaves one valid planar face with null triangulation on
    a source-built fused solid. build123d's compound tessellator then crashes
    while the same B-rep, after a STEP round-trip, triangulates normally. The
    fallback is still source-derived geometry; it only asks OCCT to rebuild the
    face representation before meshing it.
    """
    try:
        verts, tris = shape.tessellate(tolerance)
    except Exception as direct_error:  # noqa: BLE001 - retry one OCCT failure path
        import tempfile
        from build123d import export_step, import_step

        try:
            with tempfile.TemporaryDirectory(prefix="render-views-") as tmp:
                step_path = Path(tmp) / "source-roundtrip.step"
                if not export_step(shape, step_path):
                    raise RuntimeError("temporary STEP export returned false")
                restored = import_step(step_path)
                verts, tris = restored.tessellate(tolerance)
        except Exception as fallback_error:  # noqa: BLE001 - preserve both causes
            raise RuntimeError(
                "tessellation failed directly "
                f"({type(direct_error).__name__}: {direct_error}) and after a "
                "temporary STEP round-trip "
                f"({type(fallback_error).__name__}: {fallback_error})"
            ) from fallback_error
        print(
            "render_views: direct tessellation failed; recovered through a "
            "temporary STEP round-trip",
            file=sys.stderr,
        )
    points = np.array([[v.X, v.Y, v.Z] for v in verts], dtype=float)
    faces = np.array(tris, dtype=int)
    if len(points) == 0 or len(faces) == 0:
        raise ValueError("tessellation produced no triangles")
    return points, faces


# --------------------------------------------------------------------------
# camera and projection


def camera_basis(az: float, el: float, roll: float = 0.0):
    """(toward-viewer, right, up) for an azimuth/elevation camera, Z up.

    At the poles `z x c` vanishes and the roll reference has to come from the
    azimuth instead. The fallback is chosen to agree with the limit approached
    from below, so a search that walks up to el=90 does not jump 90 degrees in
    roll at the last step.
    """
    a, e = math.radians(az), math.radians(el)
    c = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    r = np.cross(np.array([0.0, 0.0, 1.0]), c)
    norm = float(np.linalg.norm(r))
    if norm < 1e-9:
        r = np.array([-math.sin(a), math.cos(a), 0.0])
    else:
        r = r / norm
    u = np.cross(c, r)
    if roll:
        t = math.radians(roll)
        r, u = math.cos(t) * r + math.sin(t) * u, -math.sin(t) * r + math.cos(t) * u
    return c, r, u


def project(points: np.ndarray, az: float, el: float, roll: float, fov: float):
    """Screen-space X/Y, orthographic when fov is 0 and perspective otherwise.

    The frame is fitted to the projection afterwards, so the focal length
    cancels and `fov` controls one thing only: how much the near side of the
    object is enlarged relative to the far side. That is the whole of what a
    photograph adds over an orthographic view, and the only part worth
    searching over.
    """
    c, r, u = camera_basis(az, el, roll)
    if fov <= 0:
        return points @ r, points @ u
    centre = (points.max(axis=0) + points.min(axis=0)) / 2
    radius = float(np.linalg.norm(points - centre, axis=1).max())
    distance = radius / math.sin(math.radians(fov) / 2) * 1.05
    cam = centre + c * distance
    rel = points - cam
    depth = -(rel @ c)
    depth = np.maximum(depth, 1e-6)
    return (rel @ r) / depth, (rel @ u) / depth


def rasterise(points: np.ndarray, faces: np.ndarray, az: float, el: float,
              roll: float = 0.0, fov: float = 0.0, size: int = DEFAULT_SIZE,
              pad: float = DEFAULT_PAD) -> np.ndarray:
    """A boolean silhouette mask: True where the object covers the frame."""
    sx, sy = project(points, az, el, roll, fov)
    width, height = sx.max() - sx.min(), sy.max() - sy.min()
    span = max(width, height)
    if span <= 0:
        raise ValueError("the projection is degenerate")
    scale = (1 - 2 * pad) * size / span
    px = (sx - sx.min()) * scale + (size - width * scale) / 2
    py = size - ((sy - sy.min()) * scale + (size - height * scale) / 2)

    return gate_mask(fill_triangles(px, py, faces, size))


def fill_triangles(px, py, faces: np.ndarray, size: int) -> np.ndarray:
    """The union of the projected triangles, by vectorised scanline fill.

    The obvious implementation is one `ImageDraw.polygon` per triangle, and it
    is what the first version did. It costs about 5 us per call, which nobody
    notices on a single render and which decides how usable the pose search is:
    58 ms a pose on a 11,716-triangle assembly, so a 585-pose search takes 45
    seconds. Doing the same work as array arithmetic:

        size 240   numpy  3.2-6.6 ms   PIL  56-57 ms
        size 480   numpy  6.2-9.8 ms   PIL  55-58 ms

    Every triangle contributes one span per scanline it crosses; the spans go
    into a difference array and one cumulative sum along X unions them all.

    A pixel is filled when its **centre** lies in the triangle. That rule is
    what makes the union seamless: two triangles sharing an edge compute the
    identical span endpoint from it, so neither a gap nor a double-count
    appears along the seam -- verified at 0 interior hole pixels on the front
    view of that assembly. PIL instead includes boundary pixels, which dilates
    every outline by about half a pixel; the two agree to IoU 0.985-0.996 and
    the whole disagreement is that rim.
    """
    x, y = px[faces], py[faces]
    first = np.clip(np.ceil(y.min(axis=1) - 0.5), 0, size - 1).astype(np.int64)
    last = np.clip(np.floor(y.max(axis=1) - 0.5), 0, size - 1).astype(np.int64)
    counts = np.maximum(last - first + 1, 0)
    total = int(counts.sum())
    if total == 0:
        return np.zeros((size, size), dtype=bool)

    tri = np.repeat(np.arange(len(faces)), counts)
    starts = np.repeat(np.cumsum(counts) - counts, counts)
    rows = np.repeat(first, counts) + (np.arange(total) - starts)
    centres = rows + 0.5

    far = 1e18
    lo = np.full(total, far)
    hi = np.full(total, -far)
    tx, ty = x[tri], y[tri]
    for a, b in ((0, 1), (1, 2), (0, 2)):
        xa, ya, xb, yb = tx[:, a], ty[:, a], tx[:, b], ty[:, b]
        drop = yb - ya
        flat = np.abs(drop) < 1e-9
        t = (centres - ya) / np.where(flat, 1.0, drop)
        crosses = (~flat) & (t >= 0.0) & (t <= 1.0)
        cut = xa + t * (xb - xa)
        lo = np.minimum(lo, np.where(crosses, cut, far))
        hi = np.maximum(hi, np.where(crosses, cut, -far))
        # A horizontal edge never "crosses" a scanline, but when the scanline
        # lands on it the triangle's slice is the whole edge. Dropping this
        # case leaves a one-pixel notch on every flat-bottomed triangle.
        on = flat & (np.abs(centres - ya) <= 0.5)
        lo = np.minimum(lo, np.where(on, np.minimum(xa, xb), far))
        hi = np.maximum(hi, np.where(on, np.maximum(xa, xb), -far))

    left = np.ceil(lo - 0.5)
    right = np.floor(hi - 0.5)
    live = (hi >= lo) & (right >= left) & (right >= 0) & (left <= size - 1)
    left = np.clip(left, 0, size - 1).astype(np.int64)[live]
    right = np.clip(right, 0, size - 1).astype(np.int64)[live]
    rows = rows[live]

    stride = size + 1
    diff = np.bincount(rows * stride + left, minlength=size * stride).astype(np.int64)
    diff -= np.bincount(rows * stride + right + 1, minlength=size * stride)
    return np.cumsum(diff.reshape(size, stride)[:, :size], axis=1) > 0


def gate_mask(mask: np.ndarray) -> np.ndarray:
    """Put a rendered mask through exactly what the gate's reader will do to it.

    `object_mask` ends with a morphological opening, and `check_likeness` then
    keeps the largest blob. Both matter here, and skipping them is not a
    cosmetic difference: a triangle seen edge-on rasterises to a one-pixel
    spike, the opening erases it, and because `normalise` crops to the bounding
    box, a single pixel the gate drops and the search keeps rescales the whole
    silhouette. Measured on the fixture -- **two** pixels out of 58,572, both
    at the extreme rows -- cost 1.3 points of IoU between the mask the search
    scored and the PNG the gate read.

    So the search would have been optimising a silhouette the gate never sees.
    Running the same two operations here is what keeps them one instrument.
    """
    mask = _open_mask(mask)
    if not mask.any():
        return mask
    labels, count = _flood_components(mask)
    if count <= 1:
        return mask
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    return labels == int(sizes.argmax())


def save_mask(mask: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8)).save(path)


# --------------------------------------------------------------------------
# shaded review render
#
# The silhouette is the right picture for the likeness gate and the wrong one
# for a person: a machine's identity is in its interior -- slots, pockets,
# flutes, the pin standing on its arm -- and a filled outline shows none of it.
# A mechanism review off silhouettes reads every assembly as one blob.
#
# This adds a second, separate image: z-buffered flat shading, one colour per
# labelled part, with an outline wherever the part or the depth changes. It is
# written beside the mask and never replaces it, so nothing the gate consumes
# moves.

PART_PALETTE = (
    (0.72, 0.74, 0.78), (0.85, 0.45, 0.28), (0.44, 0.56, 0.72),
    (0.83, 0.71, 0.36), (0.55, 0.67, 0.52), (0.68, 0.55, 0.71),
)


def part_colour(node, index: int):
    """A part's own colour when the source set one, else a stable palette."""
    colour = getattr(node, "color", None)
    if colour is not None:
        with contextlib.suppress(TypeError, ValueError):
            values = tuple(float(channel) for channel in tuple(colour))[:3]
            if len(values) == 3:
                return values
    return PART_PALETTE[index % len(PART_PALETTE)]


def tessellate_parts(shape, tolerance: float = DEFAULT_TOLERANCE):
    """One mesh per labelled child, carrying a colour and an id per triangle."""
    nodes = list(getattr(shape, "children", None) or []) or [shape]
    points, faces, colours, ids = [], [], [], []
    offset = 0
    for index, node in enumerate(nodes):
        node_points, node_faces = tessellate(node, tolerance)
        points.append(node_points)
        faces.append(node_faces + offset)
        colours.append(np.tile(part_colour(node, index), (len(node_faces), 1)))
        ids.append(np.full(len(node_faces), index, dtype=int))
        offset += len(node_points)
    return (np.concatenate(points), np.concatenate(faces),
            np.concatenate(colours), np.concatenate(ids))


def project_depth(points: np.ndarray, az: float, el: float, roll: float, fov: float):
    """`project`, plus a depth that grows away from the camera."""
    c, r, u = camera_basis(az, el, roll)
    if fov <= 0:
        return points @ r, points @ u, -(points @ c)
    centre = (points.max(axis=0) + points.min(axis=0)) / 2
    radius = float(np.linalg.norm(points - centre, axis=1).max())
    distance = radius / math.sin(math.radians(fov) / 2) * 1.05
    cam = centre + c * distance
    rel = points - cam
    depth = np.maximum(-(rel @ c), 1e-6)
    return (rel @ r) / depth, (rel @ u) / depth, depth


def shade_view(mesh, az: float, el: float, roll: float = 0.0, fov: float = 0.0,
               size: int = DEFAULT_SIZE, pad: float = DEFAULT_PAD) -> np.ndarray:
    """A shaded RGB image of the mesh, framed exactly like `rasterise`."""
    points, faces, colours, ids = mesh
    sx, sy, depth = project_depth(points, az, el, roll, fov)
    width, height = sx.max() - sx.min(), sy.max() - sy.min()
    span = max(width, height)
    if span <= 0:
        raise ValueError("the projection is degenerate")
    scale = (1 - 2 * pad) * size / span
    px = (sx - sx.min()) * scale + (size - width * scale) / 2
    py = size - ((sy - sy.min()) * scale + (size - height * scale) / 2)

    corners = points[faces]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, lengths, out=np.zeros_like(normals), where=lengths > 0)
    camera, right, up = camera_basis(az, el, roll)
    # Winding is not guaranteed across a fused solid, and a lit render must not
    # depend on it: turn every normal toward the camera before shading.
    facing = np.sign(normals @ camera)[:, None]
    normals = normals * np.where(facing == 0, 1.0, facing)
    light = camera * 0.55 + right * 0.45 + up * 0.70
    light = light / np.linalg.norm(light)
    shade = 0.32 + 0.68 * np.clip(normals @ light, 0.0, 1.0)

    image = np.full((size, size, 3), 0.965)
    zbuf = np.full((size, size), np.inf)
    partbuf = np.full((size, size), -1, dtype=int)
    for face in range(len(faces)):
        a, b, c = faces[face]
        x0, x1, x2 = px[a], px[b], px[c]
        y0, y1, y2 = py[a], py[b], py[c]
        lo_x, hi_x = int(math.floor(min(x0, x1, x2))), int(math.ceil(max(x0, x1, x2)))
        lo_y, hi_y = int(math.floor(min(y0, y1, y2))), int(math.ceil(max(y0, y1, y2)))
        lo_x, lo_y = max(lo_x, 0), max(lo_y, 0)
        hi_x, hi_y = min(hi_x, size - 1), min(hi_y, size - 1)
        if lo_x > hi_x or lo_y > hi_y:
            continue
        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denom) < 1e-12:
            continue
        gx = np.arange(lo_x, hi_x + 1)[None, :] + 0.5
        gy = np.arange(lo_y, hi_y + 1)[:, None] + 0.5
        w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / denom
        w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / denom
        w2 = 1.0 - w0 - w1
        covered = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not covered.any():
            continue
        z = w0 * depth[a] + w1 * depth[b] + w2 * depth[c]
        window = zbuf[lo_y:hi_y + 1, lo_x:hi_x + 1]
        win = covered & (z < window)
        if not win.any():
            continue
        window[win] = z[win]
        image[lo_y:hi_y + 1, lo_x:hi_x + 1][win] = colours[face] * shade[face]
        partbuf[lo_y:hi_y + 1, lo_x:hi_x + 1][win] = ids[face]

    drawn = np.isfinite(zbuf)
    if drawn.any():
        jump = 0.015 * float(np.ptp(zbuf[drawn])) if drawn.sum() > 1 else 0.0
        edge = np.zeros((size, size), dtype=bool)
        for axis in (0, 1):
            other_part = np.roll(partbuf, 1, axis=axis)
            other_z = np.roll(zbuf, 1, axis=axis)
            pair = drawn | np.isfinite(other_z)
            # np.where evaluates both branches, and inf - inf is a nan warning
            # on every background pixel; subtract only where both are real.
            step = np.zeros((size, size))
            np.subtract(zbuf, other_z, out=step, where=drawn & np.isfinite(other_z))
            step = np.abs(step)
            edge |= pair & ((partbuf != other_part) | (jump > 0) & (step > jump))
        # An outline that only darkens disappears on a dark part -- a 3 mm relief
        # on a black plate renders as black on black, and the feature the review
        # is looking for is simply not there. Push away from the local tone
        # instead: darken what is light, lighten what is dark.
        if edge.any():
            lit = image[edge]
            tone = lit.mean(axis=1, keepdims=True)
            image[edge] = np.where(tone < 0.32, lit * 0.5 + 0.30, lit * 0.42)
    return image


def save_image(image: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(image * 255.0, 0, 255).astype(np.uint8)).save(path)


# --------------------------------------------------------------------------
# pose search


def search_pose(points: np.ndarray, faces: np.ndarray, reference: np.ndarray,
                az_range: tuple[float, float, float],
                el_range: tuple[float, float, float],
                fovs: list[float], roll: float, refine: int,
                size: int = SEARCH_SIZE) -> dict:
    """The pose whose silhouette best matches `reference`, coarse then local.

    Scored with check_likeness's own `normalise`/`compare`, not with a private
    metric, so the pose this keeps is the pose that maximises the number the
    gate will print. A second, differently-computed answer here would be the
    kind of quiet disagreement the toolchain has been bitten by before.
    """
    def score(az, el, rl, fov):
        mask = rasterise(points, faces, az, el, rl, fov, size=size)
        if not mask.any():
            return 0.0
        return compare(normalise(mask), reference)["iou"]

    az_lo, az_hi, az_step = az_range
    el_lo, el_hi, el_step = el_range
    best = {"iou": -1.0, "az": 0.0, "el": 0.0, "roll": roll, "fov": fovs[0]}
    tried = 0
    az_values = np.arange(az_lo, az_hi + 1e-9, az_step)
    el_values = np.arange(el_lo, el_hi + 1e-9, el_step)
    for fov in fovs:
        for az in az_values:
            for el in el_values:
                iou = score(float(az), float(el), roll, fov)
                tried += 1
                if iou > best["iou"]:
                    best = {"iou": iou, "az": float(az), "el": float(el),
                            "roll": roll, "fov": fov}

    step_az, step_el, step_roll = az_step, el_step, 8.0
    for _ in range(refine):
        step_az, step_el, step_roll = step_az / 2, step_el / 2, step_roll / 2
        centre = dict(best)
        for d_az in (-step_az, 0.0, step_az):
            for d_el in (-step_el, 0.0, step_el):
                for d_roll in (-step_roll, 0.0, step_roll):
                    az = centre["az"] + d_az
                    el = max(-90.0, min(90.0, centre["el"] + d_el))
                    rl = centre["roll"] + d_roll
                    iou = score(az, el, rl, centre["fov"])
                    tried += 1
                    if iou > best["iou"]:
                        best = {"iou": iou, "az": az, "el": el, "roll": rl,
                                "fov": centre["fov"]}
    best["poses_tried"] = tried
    return best


# --------------------------------------------------------------------------
# command


def parse_view(text: str) -> tuple[str, float, float]:
    if text in NAMED_VIEWS:
        az, el = NAMED_VIEWS[text]
        return text, az, el
    parts = text.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(
            f"--view takes a name {sorted(NAMED_VIEWS)} or AZ,EL, not {text!r}")
    try:
        az, el = float(parts[0]), float(parts[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"bad --view {text!r}: {exc}") from exc
    return f"az{az:g}_el{el:g}", az, el


def parse_range(text: str, what: str) -> tuple[float, float, float]:
    parts = text.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(f"--{what} takes LO,HI,STEP not {text!r}")
    lo, hi, step = (float(p) for p in parts)
    if step <= 0:
        raise argparse.ArgumentTypeError(f"--{what} step must be positive")
    return lo, hi, step


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", type=Path,
                    help="a *.step.py entry, a .step file, or a project directory")
    ap.add_argument("-o", "--out", type=Path, help="where to write the PNGs "
                    "(default <project>/snap)")
    ap.add_argument("--view", action="append", default=None,
                    help="a named view or AZ,EL; repeatable")
    ap.add_argument("--match", action="append", type=Path, default=None,
                    help="a reference image to search a pose against; repeatable")
    ap.add_argument("--label", action="append", default=None,
                    help="name for each --match, in order")
    ap.add_argument("--min", type=float, default=0.90,
                    help="minimum IoU per matched view (default 0.90)")
    ap.add_argument("--size", type=int, default=DEFAULT_SIZE)
    ap.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    ap.add_argument("--fov", type=float, default=0.0,
                    help="perspective field of view in degrees; 0 is orthographic")
    ap.add_argument("--roll", type=float, default=0.0)
    # argparse eats a value that starts with "-", so a negative start needs the
    # "=" form: --search-el=-30,60,15 works, --search-el -30,60,15 prints usage.
    ap.add_argument("--search-az", default="-180,175,15",
                    help="LO,HI,STEP degrees; a negative LO needs the "
                         "--search-az=-180,175,15 form")
    ap.add_argument("--search-el", default="-30,60,15",
                    help="LO,HI,STEP degrees; a negative LO needs the "
                         "--search-el=-30,60,15 form")
    ap.add_argument("--search-fov", default="0",
                    help="comma-separated FOVs to search; a photo is rarely "
                         "orthographic, so try 0,25,40")
    ap.add_argument("--refine", type=int, default=3,
                    help="local halving rounds after the coarse grid")
    ap.add_argument("--poses-from", type=Path,
                    help="replay the cameras in this poses.json. Combine it "
                         "with --match to score a reference WITHOUT searching: "
                         "one command line for the whole sweep loop")
    ap.add_argument("--compare-step", action="store_true",
                    help="render the source and its sibling .step and compare")
    ap.add_argument("--threshold", type=float, default=28.0,
                    help="silhouette threshold for reference images")
    ap.add_argument("--allow-clipped-reference", action="store_true",
                    help="allow a matched reference silhouette that touches the image "
                         "boundary; only valid for a partial-feature comparison")
    ap.add_argument("--shaded", action="store_true",
                    help="also write <label>-shaded.png: a lit, part-coloured "
                         "review render. The masks the likeness gate reads are "
                         "unchanged; this is the picture a person reads.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)

    if args.self_check:
        return self_check()
    if args.source is None:
        ap.error("a source is required (or --self-check)")

    source = resolve_source(args.source)
    if not source.exists():
        print(f"no such source: {source}", file=sys.stderr)
        return 2
    out_dir = args.out or (source.parent / "snap")

    # Reject unusable references before importing build123d or building the
    # source. A crop is an input error; it should cost milliseconds, not a full
    # tessellation and pose search.
    matches = args.match or []
    prepared_references: list[np.ndarray] = []
    for ref_path in matches:
        try:
            reference_mask = silhouette(ref_path, args.threshold)
            if not args.allow_clipped_reference:
                require_complete_reference(reference_mask, ref_path)
            prepared_references.append(normalise(reference_mask))
        except (OSError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 2

    shape = build_shape(source)
    points, faces = tessellate(shape, args.tolerance)
    review_mesh = tessellate_parts(shape, args.tolerance) if args.shaded else None

    poses: dict[str, dict] = {}
    results: list[dict] = []
    failed = False

    stored: dict[str, dict] = {}
    if args.poses_from:
        stored = json.loads(args.poses_from.read_text()).get("poses", {})

    for view in (args.view or []):
        try:
            label, az, el = parse_view(view)
        except argparse.ArgumentTypeError as exc:
            print(exc, file=sys.stderr)
            return 2
        mask = rasterise(points, faces, az, el, args.roll, args.fov, size=args.size)
        save_mask(mask, out_dir / f"{label}.png")
        if review_mesh is not None:
            save_image(shade_view(review_mesh, az, el, args.roll, args.fov, args.size),
                       out_dir / f"{label}-shaded.png")
        pose = {"az": az, "el": el, "roll": args.roll, "fov": args.fov}
        poses[label] = pose
        results.append({"label": label, "kind": "view", **pose})

    labels = args.label or []
    try:
        az_range = parse_range(args.search_az, "search-az")
        el_range = parse_range(args.search_el, "search-el")
        fovs = [float(f) for f in args.search_fov.split(",")]
    except (argparse.ArgumentTypeError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    pairs: list[tuple[str, Path]] = []
    matched: list[dict] = []
    for i, (ref_path, reference) in enumerate(zip(matches, prepared_references)):
        label = labels[i] if i < len(labels) else ref_path.stem
        # --poses-from turns a match into a REPLAY: same camera, so the IoU
        # delta between two runs belongs to the shape, and the search -- which
        # is nearly all of this command's cost -- is skipped. Re-search once at
        # the end, and whenever the shape has moved far enough that the best
        # pose would have moved with it.
        replayed = stored.get(label) if args.poses_from else None
        if replayed:
            best = {"az": replayed["az"], "el": replayed["el"],
                    "roll": replayed.get("roll", 0.0),
                    "fov": replayed.get("fov", 0.0), "poses_tried": 0}
        else:
            best = search_pose(points, faces, reference, az_range, el_range,
                               fovs, args.roll, args.refine)
        mask = rasterise(points, faces, best["az"], best["el"], best["roll"],
                         best["fov"], size=args.size)
        render_path = out_dir / f"{label}.png"
        save_mask(mask, render_path)
        if review_mesh is not None:
            save_image(shade_view(review_mesh, best["az"], best["el"], best["roll"],
                                  best["fov"], args.size),
                       out_dir / f"{label}-shaded.png")
        final = compare(normalise(mask), reference)
        pose = {"az": round(best["az"], 3), "el": round(best["el"], 3),
                "roll": round(best["roll"], 3), "fov": best["fov"]}
        poses[label] = pose
        ok = final["iou"] >= args.min
        failed = failed or not ok
        results.append({"label": label,
                        "kind": "replay-match" if replayed else "match",
                        "reference": str(ref_path),
                        "iou": final["iou"], "aspect_delta": final["aspect_delta"],
                        "poses_tried": best["poses_tried"], "ok": ok, **pose})
        pairs.append((label, ref_path))
        matched.append({"label": label, "az": pose["az"], "el": pose["el"],
                        "mask": reference})

    # Two references handed the same camera must look alike. When they do not,
    # the reference mask is what the search fitted, and every IoU above is
    # about the mask rather than the shape.
    suspect = mask_contradictions(matched)
    failed = failed or bool(suspect)

    # any stored pose no --view or --match claimed is replayed as a plain view
    for label, pose in stored.items():
        if label in poses:
            continue
        mask = rasterise(points, faces, pose["az"], pose["el"],
                         pose.get("roll", 0.0), pose.get("fov", 0.0),
                         size=args.size)
        save_mask(mask, out_dir / f"{label}.png")
        if review_mesh is not None:
            save_image(shade_view(review_mesh, pose["az"], pose["el"],
                                  pose.get("roll", 0.0), pose.get("fov", 0.0), args.size),
                       out_dir / f"{label}-shaded.png")
        poses[label] = pose
        results.append({"label": label, "kind": "replay", **pose})

    drift: list[dict] = []
    if args.compare_step:
        step_path = source.parent / (source.name[:-len(ENTRY_SUFFIX)] + ".step") \
            if source.name.endswith(ENTRY_SUFFIX) else None
        if step_path is None or not step_path.exists():
            print(f"--compare-step: no sibling .step for {source.name}", file=sys.stderr)
            return 2
        step_points, step_faces = tessellate(build_shape(step_path), args.tolerance)
        for label in ("front", "right", "top"):
            az, el = NAMED_VIEWS[label]
            a = normalise(rasterise(points, faces, az, el, size=args.size))
            b = normalise(rasterise(step_points, step_faces, az, el, size=args.size))
            iou = compare(a, b)["iou"]
            entry = {"view": label, "iou": iou, "ok": iou >= STALE_MIN_IOU}
            failed = failed or not entry["ok"]
            drift.append(entry)

    payload = {"source": str(source), "out": str(out_dir), "poses": poses,
               "views": results, "step_drift": drift,
               "mask_contradictions": suspect, "ok": not failed,
               "tolerance": args.tolerance, "size": args.size}
    if poses:
        (out_dir / "poses.json").write_text(json.dumps(
            {"source": str(source), "size": args.size,
             "tolerance": args.tolerance, "poses": poses}, indent=2))

    if args.json:
        print(json.dumps(payload, indent=2))
        return 1 if failed else 0

    print(f"{len(faces)} triangles from {source.name}")
    for r in results:
        pose = f"az {r['az']:>8.2f}  el {r['el']:>7.2f}  roll {r['roll']:>6.2f}  fov {r['fov']:>4g}"
        if r["kind"] in ("match", "replay-match"):
            flag = " " if r["ok"] else "!"
            how = (f"({r['poses_tried']} poses)" if r["kind"] == "match"
                   else "(replayed camera -- not searched)")
            print(f"{r['label']:<14}{r['iou']:>7.3f} {flag} {pose}  {how}")
        else:
            print(f"{r['label']:<14}{'':>9}{pose}")
    if suspect:
        print()
        print("MASK SUSPECT -- these references were handed the same camera but "
              "do not look alike:", file=sys.stderr)
        for c in suspect:
            print(f"  {c['a']} and {c['b']}: cameras agree to "
                  f"{c['camera_delta_deg']} deg, yet their own silhouettes score "
                  f"IoU {c['reference_iou']}", file=sys.stderr)
        print("  The search is fitting the reference MASK, not the shape. Every "
              "IoU above is about the mask.", file=sys.stderr)
        print("  Fix the references first:", file=sys.stderr)
        print("      ref_silhouette.py <project>/ref/*.png", file=sys.stderr)

    if drift:
        print()
        for d in drift:
            state = "same" if d["ok"] else "DRIFT -- the .step is stale"
            print(f"source vs .step  {d['view']:<8}IoU {d['iou']:.4f}  {state}")
    if pairs:
        print()
        print("now run the gate:")
        likeness_tool = shlex.quote(str(SCRIPTS_DIR / "check_likeness.py"))
        cmd = [f"  python {likeness_tool}"]
        for label, ref_path in pairs:
            cmd.append(f"      --pair {out_dir / (label + '.png')} {ref_path} --label {label}")
        cmd.append(f"      --min {args.min:g} --report {source.parent / 'measure' / 'likeness.md'}")
        print(" \\\n".join(cmd))
    if poses:
        print()
        print(f"wrote {len(poses)} view(s) to {out_dir}, and recorded their "
              "cameras in poses.json")
    return 1 if failed else 0


# --------------------------------------------------------------------------
# fixtures


def mask_contradictions(matched: list[dict]) -> list[dict]:
    """References given the same camera whose own silhouettes disagree.

    This is the cheapest tell that the reference MASK, not the model, is what
    the gate is measuring. `--match` searches for the camera that maximises
    IoU; when the mask has punched holes in several references, the search
    fits the holes and lands on nearly the same pose for viewpoints that are
    plainly different. That happened on a real project and cost an hour of
    sweeping shape parameters that were never wrong: three references recovered
    az -71, -75 and -77 degrees, and after the masks were fixed the same search
    returned -86, -73 and -118.

    A pair is a contradiction when the cameras agree to `SAME_CAMERA_DEG` but
    the two reference silhouettes are further apart than
    `DIFFERENT_SILHOUETTE_IOU`. Genuinely similar viewpoints share a camera AND
    a silhouette, so they do not fire.
    """
    out = []
    for i, a in enumerate(matched):
        for b in matched[i + 1:]:
            if (abs(a["az"] - b["az"]) > SAME_CAMERA_DEG
                    or abs(a["el"] - b["el"]) > SAME_CAMERA_DEG):
                continue
            iou = compare(a["mask"], b["mask"])["iou"]
            if iou < DIFFERENT_SILHOUETTE_IOU:
                out.append({"a": a["label"], "b": b["label"],
                            "camera_delta_deg": round(
                                max(abs(a["az"] - b["az"]),
                                    abs(a["el"] - b["el"])), 2),
                            "reference_iou": round(iou, 4)})
    return out


def self_check() -> int:
    """Fixtures that assert numbers, not that the code runs.

    Each one is a way the renderer could be wrong while still producing a
    plausible picture: axes swapped, the frame fitted to the wrong extent, the
    PNG round-trip disagreeing with the mask the search scored, perspective
    silently doing nothing, or the search reporting a high IoU at a pose it
    never actually found.
    """
    from build123d import Box, Location, Pos

    failures: list[str] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        print(f"{'ok  ' if condition else 'FAIL'} {name}{'  ' + detail if detail else ''}")
        if not condition:
            failures.append(name)

    # An L, not a box: a box is symmetric enough that a wrong pose can score
    # 1.0. The notch runs the full depth on purpose -- a blind pocket is
    # invisible in a silhouette, and a fixture that cannot fail is not one.
    shape = Location((0, 0, 0)) * (Box(10, 20, 30) - Pos(3, 0, 9) * Box(10, 30, 16))
    points, faces = tessellate(shape, 0.05)

    def aspect(mask: np.ndarray) -> float:
        ys, xs = np.nonzero(mask)
        return (xs.max() - xs.min() + 1) / (ys.max() - ys.min() + 1)

    front = rasterise(points, faces, *NAMED_VIEWS["front"], size=400)
    right = rasterise(points, faces, *NAMED_VIEWS["right"], size=400)
    top = rasterise(points, faces, *NAMED_VIEWS["top"], size=400)
    check("front view is X wide by Z tall", abs(aspect(front) - 10 / 30) < 0.02,
          f"aspect {aspect(front):.3f} vs {10 / 30:.3f}")
    check("right view is Y wide by Z tall", abs(aspect(right) - 20 / 30) < 0.02,
          f"aspect {aspect(right):.3f} vs {20 / 30:.3f}")
    check("top view is X wide by Y tall", abs(aspect(top) - 10 / 20) < 0.02,
          f"aspect {aspect(top):.3f} vs {10 / 20:.3f}")

    # A solid box fills its own bounding box; the notch is what stops this
    # passing on a renderer that fills the box and ignores the geometry.
    box_points, box_faces = tessellate(Box(10, 20, 30), 0.05)
    box_front = rasterise(box_points, box_faces, *NAMED_VIEWS["front"], size=400)
    ys, xs = np.nonzero(box_front)
    fill = box_front.sum() / ((xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1))
    check("a box fills its own box", fill > 0.995, f"fill {fill:.4f}")
    n_ys, n_xs = np.nonzero(front)
    notch_fill = front.sum() / ((np.ptp(n_xs) + 1) * (np.ptp(n_ys) + 1))
    check("the notch is not filled in", notch_fill < 0.95, f"fill {notch_fill:.4f}")

    # The scanline fill against an independent implementation. PIL's polygon
    # includes boundary pixels and this one samples centres, so they differ by
    # a half-pixel rim on purpose; what must not differ is the interior, and a
    # seam between two triangles sharing an edge is exactly the failure a fast
    # rasteriser produces while still looking right.
    sx, sy = project(points, -45.0, 25.0, 0.0, 0.0)
    span = max(sx.max() - sx.min(), sy.max() - sy.min())
    scale = (1 - 2 * DEFAULT_PAD) * 400 / span
    fx = (sx - sx.min()) * scale + (400 - (sx.max() - sx.min()) * scale) / 2
    fy = 400 - ((sy - sy.min()) * scale + (400 - (sy.max() - sy.min()) * scale) / 2)
    ours = fill_triangles(fx, fy, faces, 400)
    canvas = Image.new("L", (400, 400), 255)
    pen = ImageDraw.Draw(canvas)
    xy = np.stack([fx, fy], axis=1)
    for face in faces:
        pen.polygon([tuple(xy[i]) for i in face], fill=0)
    theirs = np.asarray(canvas) < 128
    agree = (ours & theirs).sum() / (ours | theirs).sum()
    check("the scanline fill agrees with PIL", agree > 0.98, f"IoU {agree:.4f}")
    inner = np.zeros_like(ours)
    inner[1:-1, 1:-1] = (ours[:-2, 1:-1] & ours[2:, 1:-1]
                         & ours[1:-1, :-2] & ours[1:-1, 2:])
    seams = int((~ours & inner).sum())
    check("and leaves no seam between triangles", seams == 0, f"{seams} hole px")

    # The mask the search scores and the PNG the gate reads must be the same
    # silhouette, or the pose that wins here is not the pose that scores there.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "iso.png"
        iso = rasterise(points, faces, *NAMED_VIEWS["iso"], size=400)
        save_mask(iso, png)
        round_trip = compare(normalise(iso), normalise(silhouette(png, 28.0)))["iou"]
    check("PNG round-trips through the gate's own reader", round_trip > 0.999,
          f"IoU {round_trip:.4f}")

    complete = np.zeros((20, 20), dtype=bool)
    complete[2:-2, 3:-3] = True
    clipped = complete.copy()
    clipped[:3, 8:12] = True
    check("a complete reference has no border contacts",
          clipped_edges(complete) == [], str(clipped_edges(complete)))
    check("a clipped reference names the touched border",
          clipped_edges(clipped) == ["top"], str(clipped_edges(clipped)))
    try:
        require_complete_reference(clipped, Path("clipped.png"))
    except ValueError as exc:
        check("a clipped reference is refused", "touches the image boundary" in str(exc),
              str(exc))
    else:
        check("a clipped reference is refused", False, "no error")

    # Perspective has to change the outline, or --fov is decoration.
    ortho = normalise(rasterise(points, faces, -45, 25, 0, 0, size=400))
    persp = normalise(rasterise(points, faces, -45, 25, 0, 45, size=400))
    fov_iou = compare(ortho, persp)["iou"]
    check("perspective changes the silhouette", fov_iou < 0.99, f"IoU {fov_iou:.4f}")

    # Pose recovery: hide a known camera, then see whether the search finds it.
    truth = {"az": 37.0, "el": 22.0}
    target = normalise(rasterise(points, faces, truth["az"], truth["el"], size=400))
    best = search_pose(points, faces, target, (-180, 175, 15), (-30, 60, 15),
                       [0.0], 0.0, refine=3)
    check("the search recovers a hidden pose", best["iou"] > 0.98,
          f"IoU {best['iou']:.4f} at az {best['az']:.1f} el {best['el']:.1f} "
          f"(truth az {truth['az']:.0f} el {truth['el']:.0f}, "
          f"{best['poses_tried']} poses)")
    check("and lands near it", abs(best["az"] - truth["az"]) < 6
          and abs(best["el"] - truth["el"]) < 6,
          f"off by az {best['az'] - truth['az']:+.1f} el {best['el'] - truth['el']:+.1f}")

    # --poses-from composed with --match must reproduce the searched number
    # exactly. The sweep loop exists to make an IoU delta between two runs
    # belong to the SHAPE; if replay scored even slightly differently, the loop
    # would be attributing a camera difference to the geometry. End to end
    # through main(), because the branch being tested lives there.
    import tempfile
    with tempfile.TemporaryDirectory() as tmpname:
        tmp = Path(tmpname)
        (tmp / "fixture.step.py").write_text(
            "from build123d import Box, Pos\n"
            "def gen_step():\n"
            "    return Box(10, 20, 30) - Pos(3, 0, 9) * Box(10, 30, 16)\n")
        save_mask(rasterise(points, faces, -60.0, 20.0, 0.0, 0.0, size=400),
                  tmp / "ref.png")
        base = [str(tmp / "fixture.step.py"), "--match", str(tmp / "ref.png"),
                "--label", "probe", "--min", "0", "--json"]

        def run(extra):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                main(base + extra)
            return json.loads(buf.getvalue())["views"][0]

        a = run(["-o", str(tmp / "one")])
        b = run(["-o", str(tmp / "two"), "--poses-from", str(tmp / "one" / "poses.json")])
    check("a replayed camera scores exactly what the search scored",
          a["iou"] == b["iou"] and b["poses_tried"] == 0
          and (a["az"], a["el"], a["fov"]) == (b["az"], b["el"], b["fov"]),
          f"searched {a['iou']:.6f} over {a['poses_tried']} poses, "
          f"replayed {b['iou']:.6f} over {b['poses_tried']}")

    # The mask-contradiction detector. It must fire when two references share a
    # camera but not a silhouette, and stay silent when they share both --
    # otherwise it either cries wolf on genuinely similar viewpoints or misses
    # the one tell that the reference mask is lying.
    tall = np.zeros((60, 60), bool); tall[5:55, 24:36] = True
    wide = np.zeros((60, 60), bool); wide[24:36, 5:55] = True
    same = tall.copy()
    fires = mask_contradictions([
        {"label": "a", "az": -71.0, "el": 5.0, "mask": normalise(tall)},
        {"label": "b", "az": -75.0, "el": 6.0, "mask": normalise(wide)}])
    quiet = mask_contradictions([
        {"label": "a", "az": -71.0, "el": 5.0, "mask": normalise(tall)},
        {"label": "b", "az": -75.0, "el": 6.0, "mask": normalise(same)}])
    apart = mask_contradictions([
        {"label": "a", "az": -71.0, "el": 5.0, "mask": normalise(tall)},
        {"label": "b", "az": 40.0, "el": 6.0, "mask": normalise(wide)}])
    check("same camera + different silhouettes is flagged", len(fires) == 1,
          f"{fires}")
    check("same camera + same silhouette is not", quiet == [], f"{quiet}")
    check("different cameras are never flagged", apart == [], f"{apart}")

    print()
    if failures:
        print(f"{len(failures)} failure(s): {', '.join(failures)}")
        return 1
    print("all fixtures pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
