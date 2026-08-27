"""Render four deterministic orthographic review views from the assembled STL."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
PROJECT = HERE.parents[1]
WORKSPACE = HERE.parents[7]
sys.path.insert(0, str(WORKSPACE / ".agents/skills/cad/scripts"))

from meshlib import load_stl  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402


def main() -> None:
    triangles = load_stl(PROJECT / "moon_relay.stl")
    lo = triangles.reshape(-1, 3).min(axis=0)
    hi = triangles.reshape(-1, 3).max(axis=0)
    center = (lo + hi) / 2.0
    radius = float((hi - lo).max() / 2.0) * 1.08

    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, lengths, out=np.zeros_like(normals), where=lengths > 0)
    light = np.array([0.35, -0.45, 0.82])
    shade = np.clip(0.35 + 0.65 * np.abs(normals @ light), 0.0, 1.0)
    base = np.array([0.56, 0.66, 0.78])
    colors = np.clip(base[None, :] * shade[:, None] + 0.10, 0.0, 1.0)

    views = (
        ("isometric", 24, -58),
        ("front", 10, -90),
        ("side / axle", 10, 0),
        ("top", 90, -90),
    )
    fig = plt.figure(figsize=(12, 10), facecolor="#10151f")
    for index, (title, elev, azim) in enumerate(views, start=1):
        ax = fig.add_subplot(2, 2, index, projection="3d")
        mesh = Poly3DCollection(
            triangles,
            facecolors=colors,
            edgecolors=(0.08, 0.10, 0.14, 0.28),
            linewidths=0.12,
        )
        ax.add_collection3d(mesh)
        ax.set_xlim(center[0] - radius, center[0] + radius)
        ax.set_ylim(center[1] - radius, center[1] + radius)
        ax.set_zlim(max(0.0, center[2] - radius), center[2] + radius)
        ax.set_box_aspect((1, 1, 0.7))
        ax.view_init(elev=elev, azim=azim)
        ax.set_proj_type("ortho")
        ax.set_title(title, color="white", fontsize=12, pad=8)
        ax.set_axis_off()
        ax.set_facecolor("#10151f")
    fig.suptitle("Lunar Relay — exact assembled STL review", color="white", fontsize=16)
    fig.tight_layout()
    output = PROJECT / "measure" / "render-review.png"
    fig.savefig(output, dpi=170, facecolor=fig.get_facecolor())
    print(output)


if __name__ == "__main__":
    main()
