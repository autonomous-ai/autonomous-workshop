#!/usr/bin/env python3
"""Render deterministic review PNGs from the generated assembly STL."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402


def read_binary_stl(path: Path) -> np.ndarray:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + count * 50
    if len(data) != expected:
        raise ValueError("expected binary STL")
    records = np.frombuffer(data, dtype=np.dtype([
        ("normal", "<f4", (3,)),
        ("vertices", "<f4", (9,)),
        ("attribute", "<u2"),
    ]), offset=84, count=count)
    return records["vertices"].reshape((-1, 3, 3)).astype(float)


def render(triangles: np.ndarray, output: Path, elevation: float, azimuth: float) -> None:
    fig = plt.figure(figsize=(8, 8), dpi=180, facecolor="#f4f0e6")
    axis = fig.add_subplot(111, projection="3d")
    mesh = Poly3DCollection(
        triangles,
        facecolor="#4f7a78",
        edgecolor="#213c3d",
        linewidth=0.06,
        alpha=1.0,
    )
    axis.add_collection3d(mesh)
    mins = triangles.min(axis=(0, 1))
    maxs = triangles.max(axis=(0, 1))
    center = (mins + maxs) / 2.0
    span = max(maxs - mins) * 0.56
    axis.set_xlim(center[0] - span, center[0] + span)
    axis.set_ylim(center[1] - span, center[1] + span)
    axis.set_zlim(max(0.0, center[2] - span), center[2] + span)
    axis.set_box_aspect((1, 1, 0.55))
    axis.view_init(elev=elevation, azim=azimuth)
    axis.set_proj_type("ortho")
    axis.set_axis_off()
    axis.set_title("Rainspell Dial — CAD review", color="#213c3d", pad=12)
    fig.tight_layout(pad=0.5)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stl", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    triangles = read_binary_stl(args.stl)
    render(triangles, args.output_dir / "top.png", 90, -90)
    render(triangles, args.output_dir / "front.png", 0, -90)
    render(triangles, args.output_dir / "isometric.png", 28, -48)
    print(f"rendered {len(triangles)} triangles to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
