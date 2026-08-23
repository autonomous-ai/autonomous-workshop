"""Headless STL → PNG renderer for QA review of generated parts.

Uses matplotlib's Agg backend with a 3D ``Poly3DCollection`` built straight from
the STL triangle mesh — no GL context, so it runs reliably headless (CI, the
bundled python sidecar, a packaged `.app`). The render is deliberately matte and
multi-view so a human-or-model reviewer can spot the defects geometry counting
misses: a strut poking through a plate, a part floating disconnected, wrong
proportions.

Two primitives:
- ``render_stl_to_png`` renders one STL from the default exterior viewpoints
  (a 3/4 isometric plus all six axis-aligned faces), laid out as a grid.
- ``render_stl_section_to_png`` cuts the mesh with an axis-aligned plane and
  renders the capped half so *interior* engagement reads — a peg seated in a
  socket, a tooth sitting on solid disc, a lip inside its groove. Exterior views
  cannot show these.

Orchestration (which parts/sections to render for a generated project) lives in
`skills/cadcode/scripts/review`.
"""

from __future__ import annotations

from pathlib import Path

# Default viewpoints: a 3/4 isometric (reveals protrusions and depth) plus the
# six axis-aligned faces (top/bottom/front/back/left/right) so a part is checked
# from every direction — a defect that hides behind the body on one view (a spike
# under the floor, a feature off the back face) shows on another. Laid out as a
# grid by ``_render_tris``.
DEFAULT_VIEWS = (
    ("iso", 24.0, -58.0),
    ("top", 89.0, -90.0),
    ("bottom", -89.0, -90.0),
    ("front", 0.0, -90.0),
    ("back", 0.0, 90.0),
    ("right", 0.0, 0.0),
    ("left", 0.0, 180.0),
)

# Cut-plane normals and the view that looks roughly down each normal so the
# exposed cross-section face dominates the frame (a small elev tilt keeps depth
# readable). Keyed by axis letter.
_AXIS_INDEX = {"x": 0, "y": 1, "z": 2}
_SECTION_VIEWS = {
    "x": ("section: X-cut", 12.0, 0.0),
    "y": ("section: Y-cut", 12.0, -90.0),
    "z": ("section: Z-cut", 89.0, -90.0),
}

# Drawing per-triangle edges is the slow part of mplot3d; skip it above this
# face count (the matte shading alone still reads clearly on dense meshes).
_EDGE_FACE_LIMIT = 4000


def _render_tris(tris, png_path, *, views, size: int, base_color=None, bg=None, zoom: float = 1.0,
                 ambient: float = 0.0):
    """Shade and render a triangle array ``(F, 3, 3)`` to a multi-view PNG.

    ``zoom`` scales the part within each panel (mplot3d leaves a wide default
    margin, so a part reads small at ``zoom=1``); >1 enlarges it without changing
    the data limits, so nothing clips. Defaults to 1.0 → QA sheets are unchanged.

    Returns the PNG path, or ``None`` if there is nothing to draw. May raise on a
    matplotlib failure — callers wrap this so QA rendering never breaks a build.
    """
    import matplotlib

    matplotlib.use("Agg")  # headless, no display/GL — must precede pyplot
    import numpy as np
    from matplotlib import pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    tris = np.asarray(tris, dtype=float)
    if tris.size == 0:
        return None
    png_path = Path(png_path)

    # Lambert shading from a fixed light so faceted detail and protrusions read
    # clearly instead of flattening into one silhouette.
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    nlen = np.linalg.norm(normals, axis=1, keepdims=True)
    nlen[nlen == 0] = 1.0
    normals = normals / nlen
    light = np.array([0.3, 0.4, 0.85])
    light = light / np.linalg.norm(light)
    shade = np.clip(np.abs(normals @ light), 0.18, 1.0)
    if ambient:  # lift the shading floor so dark materials stay readable
        shade = ambient + (1.0 - ambient) * shade
    base = np.array(base_color if base_color is not None else (0.55, 0.62, 0.72), dtype=float)
    if base.ndim == 1:  # single material color -> broadcast; (F,3) = per-face color
        base = base[None, :]
    rgb = np.clip(shade[:, None] * base, 0.0, 1.0)
    facecolors = np.concatenate([rgb, np.ones((len(rgb), 1))], axis=1)

    draw_edges = len(tris) <= _EDGE_FACE_LIMIT

    pts = tris.reshape(-1, 3)
    lo = pts.min(axis=0)
    hi = pts.max(axis=0)
    center = (lo + hi) / 2.0
    half = (float((hi - lo).max()) or 1.0) * 0.55

    n = len(views)
    # Lay the views out in a near-square grid rather than one wide strip, so a
    # 7-view montage stays readable instead of becoming an ultra-wide band.
    cols = int(np.ceil(np.sqrt(n)))
    rows = int(np.ceil(n / cols))
    fig = plt.figure(figsize=(size / 100.0 * cols, size / 100.0 * rows), dpi=100)
    for i, (label, elev, azim) in enumerate(views):
        ax = fig.add_subplot(rows, cols, i + 1, projection="3d")
        if bg is not None:  # let the backdrop show through the panels
            ax.patch.set_alpha(0.0)
        # Backface-cull per view: mplot3d has no z-buffer, so faces on the far
        # side and inside cavities (and their edge lines) otherwise paint over
        # the exterior and the solid reads translucent/x-rayed. For a closed
        # mesh every sightline inside the silhouette exits through a
        # camera-facing face, so dropping dot(normal, view) <= 0 faces changes
        # nothing a real occluding renderer would show.
        er, ar = np.radians(elev), np.radians(azim)
        view_dir = np.array([np.cos(er) * np.cos(ar), np.cos(er) * np.sin(ar), np.sin(er)])
        front = (normals @ view_dir) > 0.0
        # Without an explicit edge overlay, each triangle's edge is drawn in
        # its own face color at a hairline width: antialiasing otherwise lets
        # the background bleed through the seams between adjacent triangles,
        # which reads as stipple on curves, scratches on big flat faces, and a
        # pinwheel on end caps — reviewers mistake it for transparency or a
        # surface defect.
        coll = Poly3DCollection(
            tris[front],
            facecolors=facecolors[front],
            edgecolors=(0, 0, 0, 0.10) if draw_edges else facecolors[front],
            linewidths=0.2 if draw_edges else 0.3,
        )
        ax.add_collection3d(coll)
        ax.set_xlim(center[0] - half, center[0] + half)
        ax.set_ylim(center[1] - half, center[1] + half)
        ax.set_zlim(center[2] - half, center[2] + half)
        ax.set_box_aspect((1, 1, 1), zoom=zoom)
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(label, fontsize=9)
        ax.set_axis_off()
    fig.tight_layout()

    # Optional backdrop (default None → plain white, so QA sheets are unchanged).
    # A solid ``(r,g,b)`` tint, or a vertical gradient ``((top_rgb, bottom_rgb))``
    # drawn as a full-figure axes behind the transparent panels.
    pad_color = "white"
    if bg is not None:
        if isinstance(bg[0], (tuple, list)):  # gradient
            top = np.array(bg[0], dtype=float)
            bot = np.array(bg[1], dtype=float)
            ramp = np.linspace(0.0, 1.0, 256)[:, None]
            grad = (top[None, :] * (1 - ramp) + bot[None, :] * ramp)[:, None, :]
            bax = fig.add_axes((0, 0, 1, 1), zorder=-10)
            bax.imshow(grad, aspect="auto", extent=(0, 1, 0, 1), interpolation="bilinear")
            bax.set_axis_off()
            pad_color = tuple(bot)
        else:  # solid tint
            pad_color = tuple(bg)

    png_path.parent.mkdir(parents=True, exist_ok=True)
    # A backdrop must bleed to the edge — any pad band would frame it with a solid
    # strip that mismatches the gradient. Plain white QA sheets keep their margin.
    pad_inches = 0.0 if bg is not None else 0.1
    fig.savefig(str(png_path), facecolor=pad_color, bbox_inches="tight", pad_inches=pad_inches)
    plt.close(fig)
    return png_path


def render_stl_to_png(
    stl_path: str | Path,
    png_path: str | Path,
    *,
    views=DEFAULT_VIEWS,
    size: int = 760,
    base_color=None,
    bg=None,
    zoom: float = 1.0,
) -> Path | None:
    """Render an STL mesh to a multi-view PNG. Returns the PNG path, or ``None``
    if rendering failed (never raises — QA rendering must not break a build).

    ``base_color`` overrides the fully-lit material RGB (0..1 triple); ``bg`` sets a
    backdrop (solid ``(r,g,b)`` or vertical gradient ``(top_rgb, bottom_rgb)``); ``zoom``
    enlarges the part within the frame (>1 fills more of the panel). All three
    default to the slate-blue-on-white QA look so review sheets are unchanged."""
    try:
        import numpy as np
        import trimesh

        mesh = trimesh.load(str(stl_path), force="mesh")
        verts = np.asarray(mesh.vertices, dtype=float)
        faces = np.asarray(mesh.faces, dtype=int)
        if verts.size == 0 or faces.size == 0:
            return None
        return _render_tris(verts[faces], png_path, views=views, size=size,
                            base_color=base_color, bg=bg, zoom=zoom)
    except Exception:
        return None


def render_stls_to_png(
    items,
    png_path: str | Path,
    *,
    views=DEFAULT_VIEWS,
    size: int = 760,
    bg=None,
    zoom: float = 1.0,
    ambient: float = 0.35,
) -> Path | None:
    """Render several STLs COMPOSED in one scene, each in its own color.

    ``items`` is a sequence of ``(stl_path, base_color)`` pairs (color = 0..1 RGB
    triple). All meshes go into ONE triangle array so mplot3d depth-sorts across
    parts — separate collections would paint in insertion order and parts would
    read through each other. Meshes must share a coordinate frame (assembled
    pose). Returns the PNG path, or ``None`` on failure (never raises)."""
    try:
        import numpy as np
        import trimesh

        tris_all, colors_all = [], []
        for stl_path, color in items:
            mesh = trimesh.load(str(stl_path), force="mesh")
            verts = np.asarray(mesh.vertices, dtype=float)
            faces = np.asarray(mesh.faces, dtype=int)
            if verts.size == 0 or faces.size == 0:
                continue
            tris = verts[faces]
            tris_all.append(tris)
            colors_all.append(np.tile(np.asarray(color, dtype=float), (len(tris), 1)))
        if not tris_all:
            return None
        return _render_tris(
            np.concatenate(tris_all), png_path, views=views, size=size,
            base_color=np.concatenate(colors_all), bg=bg, zoom=zoom, ambient=ambient)
    except Exception:
        return None


def render_stl_section_to_png(
    stl_path: str | Path,
    png_path: str | Path,
    *,
    axis: str = "x",
    offset: float | None = None,
    size: int = 760,
) -> Path | None:
    """Render an *interior* cross-section of an STL.

    Cuts the mesh with the axis-aligned plane ``coord[axis] = offset`` (default:
    the bounding-box center), keeps the capped half on the lower side, and views
    it straight onto the exposed cut face — so interior engagement is visible
    (peg seated in a socket, tooth on solid material, lip inside its groove).

    Returns the PNG path, or ``None`` on any failure (never raises)."""
    try:
        import numpy as np
        import trimesh
        from trimesh.intersections import slice_faces_plane

        axis = str(axis).lower()
        if axis not in _AXIS_INDEX:
            return None

        mesh = trimesh.load(str(stl_path), force="mesh")
        if getattr(mesh, "faces", None) is None or len(mesh.faces) == 0:
            return None

        ai = _AXIS_INDEX[axis]
        if offset is None:
            offset = float(mesh.bounds.mean(axis=0)[ai])  # bbox center on this axis
        origin = np.zeros(3)
        origin[ai] = float(offset)
        normal = np.zeros(3)
        normal[ai] = 1.0

        # Keep the lower half (coord <= offset) and view it from the +normal side
        # so the open cut faces the camera and we look straight into the cavity.
        # `slice_faces_plane` is the shapely-free primitive (no cap, which is what
        # we want — an open section reads the interior). Keeps the side the normal
        # points TO, so pass -normal. Fall back to the other half if the offset
        # landed outside the body.
        verts, faces = slice_faces_plane(
            mesh.vertices, mesh.faces, plane_normal=-normal, plane_origin=origin
        )[:2]
        if len(faces) == 0:
            verts, faces = slice_faces_plane(
                mesh.vertices, mesh.faces, plane_normal=normal, plane_origin=origin
            )[:2]
        verts = np.asarray(verts, dtype=float)
        faces = np.asarray(faces, dtype=int)
        if verts.size == 0 or faces.size == 0:
            return None
        return _render_tris(
            verts[faces], png_path, views=(_SECTION_VIEWS[axis],), size=size
        )
    except Exception:
        return None
