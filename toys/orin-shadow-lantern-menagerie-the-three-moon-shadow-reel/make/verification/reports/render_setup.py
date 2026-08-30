#!/usr/bin/env python3
"""Render exact-mesh setup cues in their assembled wall-side relationship."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REEL_Z = 2.7
REAR_Z = 6.2


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_stl(path: Path) -> np.ndarray:
    data = path.read_bytes()
    if len(data) >= 84:
        count = struct.unpack_from("<I", data, 80)[0]
        if 84 + count * 50 == len(data):
            dtype = np.dtype([
                ("normal", "<f4", (3,)),
                ("vertices", "<f4", (3, 3)),
                ("attribute", "<u2"),
            ])
            rows = np.frombuffer(data, dtype=dtype, count=count, offset=84)
            return np.asarray(rows["vertices"], dtype=float)
    vertices = []
    for line in data.decode("ascii", errors="strict").splitlines():
        fields = line.strip().split()
        if len(fields) == 4 and fields[0] == "vertex":
            vertices.append([float(value) for value in fields[1:]])
    if not vertices or len(vertices) % 3:
        raise ValueError(f"unparseable STL: {path}")
    return np.asarray(vertices, dtype=float).reshape(-1, 3, 3)


def font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("output_png")
    parser.add_argument("--report")
    args = parser.parse_args()
    project = Path(args.project_dir)
    output = Path(args.output_png)
    paths = {
        "front_shell": project / "part_front_shell.stl",
        "shadow_reel": project / "part_shadow_reel.stl",
        "rear_shell": project / "part_rear_shell.stl",
    }
    meshes = {name: load_stl(path) for name, path in paths.items()}
    meshes["shadow_reel"][..., 2] += REEL_Z
    meshes["rear_shell"][..., 2] += REAR_Z

    image = Image.new("RGB", (1400, 1400), (255, 248, 233))
    draw = ImageDraw.Draw(image)
    scale, center_x, center_y = 6.7, 475.0, 720.0

    def xy(points: np.ndarray):
        return [
            (int(round(center_x + x * scale)), int(round(center_y - y * scale)))
            for x, y in points
        ]

    # Camera is on the wall side, looking from -Z toward +Z.  Draw farthest
    # part first and only its outward-facing planar triangles, so all portal,
    # pointer, and reel-mark openings remain exact rather than artist-redrawn.
    palette = {
        "rear_shell": (238, 225, 188),
        "shadow_reel": (34, 80, 102),
        "front_shell": (232, 169, 64),
    }
    for name in ("rear_shell", "shadow_reel", "front_shell"):
        triangles = meshes[name]
        normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        facing = normals[:, 2] < -1e-8
        for triangle in triangles[facing]:
            draw.polygon(xy(triangle[:, :2]), fill=palette[name])

    # Main-view outline and cue close-up.
    draw.rounded_rectangle((62, 270, 880, 1140), radius=30, outline=(36, 54, 68), width=5)
    crop_box = (
        int(center_x + 37.0 * scale),
        int(center_y - 10.0 * scale),
        int(center_x + 59.5 * scale),
        int(center_y + 10.0 * scale),
    )
    closeup = image.crop(crop_box).resize((430, 430), Image.Resampling.NEAREST)
    image.paste(closeup, (920, 300))
    draw.rounded_rectangle((908, 288, 1362, 742), radius=22, outline=(36, 54, 68), width=7)
    marker = (194, 62, 66)
    draw.ellipse((1148, 483, 1204, 539), outline=marker, width=7)
    draw.text((1165, 494), "1", fill=marker, font=font(24))
    draw.ellipse((1263, 363, 1305, 405), outline=marker, width=7)
    draw.ellipse((1263, 634, 1305, 676), outline=marker, width=7)
    draw.text((1276, 372), "2", fill=marker, font=font(20))
    draw.text((1276, 643), "2", fill=marker, font=font(20))
    draw.text((920, 180), "RABBIT / RESET - WALL SIDE", fill=(27, 43, 58), font=font(30))
    draw.text((930, 770), "1  fixed shell pointer", fill=(27, 43, 58), font=font(25))
    draw.text((930, 815), "2  reel double-V home mark", fill=(27, 43, 58), font=font(25))
    draw.text((930, 885), "Exact assembled STL geometry", fill=(27, 43, 58), font=font(23))
    draw.text((930, 925), "Color separates the three parts.", fill=(27, 43, 58), font=font(23))
    draw.text((78, 210), "WALL-FACING SHELL + HOME REEL", fill=(27, 43, 58), font=font(30))

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    report_path = Path(args.report) if args.report else output.with_suffix(".json")
    report = {
        "schema_version": 1,
        "kind": "lantern-menagerie.exact-mesh-wall-side-setup-render",
        "mesh_sha256": {name: sha256(path) for name, path in paths.items()},
        "assembly_offsets_mm": {"front_shell_z": 0.0, "shadow_reel_z": REEL_Z, "rear_shell_z": REAR_Z},
        "reel_state_deg": 0,
        "view": "orthographic wall side from negative Z",
        "output": output.as_posix(),
        "limitations": "Digital exact-mesh view; colors are explanatory and do not claim a multicolor print or human cue discovery.",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": True, "output": output.as_posix(), "report": report_path.as_posix()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
