"""Validate exported STL meshes and make deterministic review contact sheets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402


def load_mesh(path):
    loaded = trimesh.load(path, force="mesh", process=True)
    if isinstance(loaded, trimesh.Scene):
        loaded = loaded.to_mesh()
    return loaded


def component_count(mesh):
    """Use the same split topology as the canonical interference gate."""
    return len(mesh.split(only_watertight=False))


def render(meshes, path, elev=28.0, azim=-42.0):
    cols = 3
    rows = (len(meshes) + cols - 1) // cols
    fig = plt.figure(figsize=(12, 4 * rows), facecolor="#efe7d4")
    for i, (name, mesh) in enumerate(meshes, 1):
        ax = fig.add_subplot(rows, cols, i, projection="3d")
        faces = mesh.vertices[mesh.faces]
        poly = Poly3DCollection(
            faces, facecolor="#b45f3b", edgecolor="#4a281c", linewidth=0.08
        )
        ax.add_collection3d(poly)
        mins, maxs = mesh.bounds
        extents = maxs - mins
        margin = np.maximum(extents * 0.08, 0.8)
        ax.set_xlim(mins[0] - margin[0], maxs[0] + margin[0])
        ax.set_ylim(mins[1] - margin[1], maxs[1] + margin[1])
        ax.set_zlim(max(0, mins[2] - margin[2]), maxs[2] + margin[2])
        ax.set_box_aspect(np.maximum(extents, 1.0))
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(name.replace("_", " "), fontsize=9)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory", type=Path)
    ap.add_argument("--png", type=Path)
    ap.add_argument("--elev", type=float, default=28.0)
    ap.add_argument("--azim", type=float, default=-42.0)
    args = ap.parse_args()
    paths = sorted(args.directory.glob("*.stl"))
    meshes = [(path.stem, load_mesh(path)) for path in paths]
    report = []
    for name, mesh in meshes:
        components = mesh.split(only_watertight=False)
        report.append(
            {
                "name": name,
                "watertight": bool(all(component.is_watertight for component in components)),
                "aggregate_watertight": bool(mesh.is_watertight),
                "winding_consistent": bool(mesh.is_winding_consistent),
                "component_count": len(components),
                "faces": int(len(mesh.faces)),
                "extents_mm": np.round(mesh.extents, 3).tolist(),
                "volume_mm3": round(float(mesh.volume), 3),
            }
        )
    out = args.directory / "mesh_validation.json"
    out.write_text(json.dumps({"meshes": report}, indent=2) + "\n")
    render(meshes, args.png or args.directory / "contact-sheet.png", args.elev, args.azim)
    print(json.dumps({"meshes": report}, indent=2))


if __name__ == "__main__":
    main()
