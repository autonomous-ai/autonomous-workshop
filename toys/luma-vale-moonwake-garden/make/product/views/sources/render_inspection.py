#!/usr/bin/env python3
"""Deterministic shaded inspection views from the product CAD builders."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1] / "cad" / "moonwake_garden"
CAD_SCRIPTS = HERE.parents[5] / ".agents" / "skills" / "cad" / "scripts"
sys.path[:0] = [str(CAD_SCRIPTS), str(PROJECT)]

from build123d import Pos, Rot  # noqa: E402
from moonwake_garden_lib import (  # noqa: E402
    FRONT_SEAT_Z,
    ROTOR_SEAT_Z,
    build_front_garden_mask,
    build_rear_chassis,
    build_sector_rotor,
)

OUT = HERE.parent / "inspection"
COLORS = {"rear": "#36566f", "rotor": "#d29b4b", "front": "#668b72"}


def triangles(shape):
    vertices, faces = shape.tessellate(0.12)
    verts = np.array([[v.X, v.Y, v.Z] for v in vertices], dtype=float)
    return verts[np.asarray(faces, dtype=int)]


def render(name, parts, bounds, view=(28, -55)):
    fig = plt.figure(figsize=(7.2, 7.2), dpi=140, facecolor="#f6f1e6")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#f6f1e6")
    for shape, color, alpha in parts:
        mesh = Poly3DCollection(
            triangles(shape),
            facecolor=color,
            edgecolor="#17232d",
            linewidth=0.16,
            alpha=alpha,
        )
        ax.add_collection3d(mesh)
    (xmin, xmax), (ymin, ymax), (zmin, zmax) = bounds
    ax.set(xlim=(xmin, xmax), ylim=(ymin, ymax), zlim=(zmin, zmax))
    ax.set_box_aspect((xmax - xmin, ymax - ymin, max(zmax - zmin, 1.0)))
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_proj_type("ortho")
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.png", facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def main():
    rear = build_rear_chassis()
    rotor = build_sector_rotor()
    front = build_front_garden_mask()
    render(
        "exploded-stack",
        [(rear, COLORS["rear"], 1), (Pos(0, 0, 8) * rotor, COLORS["rotor"], 1), (Pos(0, 0, 12) * front, COLORS["front"], 1)],
        ((-45, 45), (-41, 41), (0, 15)),
    )
    render(
        "rear-optical-path",
        [(rear, COLORS["rear"], 0.94), (Pos(0, 0, 5) * rotor, COLORS["rotor"], 0.88)],
        ((-40, 40), (-40, 40), (0, 7)),
        (62, -55),
    )
    assembled = [
        (rear, COLORS["rear"], 1),
        (Pos(0, 0, ROTOR_SEAT_Z) * rotor, COLORS["rotor"], 1),
        (Pos(0, 0, FRONT_SEAT_Z) * front, COLORS["front"], 1),
    ]
    render("portal-and-trench", assembled, ((24, 43), (-14, 14), (0, 6.2)), (72, -70))
    render("detent-and-notch", assembled[:2], ((8, 34), (-38, -10), (0, 4)), (58, -52))
    render("snap-detail", [(rear, COLORS["rear"], 1)], ((29, 39), (22, 32), (0, 6.3)), (25, -45))
    render("rounded-vine-petals", [(front, COLORS["front"], 1)], ((-22, 22), (8, 28), (0, 2.4)), (68, -65))
    print(f"wrote 6 product-derived inspection renders to {OUT}")


if __name__ == "__main__":
    main()
