#!/usr/bin/env python3
"""Point-source ray projection from the exact four exported part meshes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SOURCE_TO_MASK_MM = 450.0
MASK_TO_WALL_MM = 750.0
PORTAL_D_MM = 44.0
PORTAL_WORLD_Z = 90.0
REEL_Z = 2.7
REAR_Z = 6.2
FRAME_LIFT = 59.0
STAND_HINGE_Y = -30.5
STAND_HINGE_Z = 14.5
STAND_PIN_Y = 5.0
STAND_PIN_Z = 3.0
STAND_DEPLOY_DEG = 108.0
VIEW_MM = 180.0
WORK_SIZE = 480
STATE_SIZE = 960
STATE_NAMES = {0: "rabbit", 120: "fox", 240: "owl"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_stl(path: Path) -> np.ndarray:
    data = path.read_bytes()
    if len(data) >= 84:
        count = struct.unpack_from("<I", data, 80)[0]
        if 84 + count * 50 == len(data):
            dtype = np.dtype([
                ("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")
            ])
            return np.asarray(np.frombuffer(data, dtype=dtype, count=count, offset=84)["vertices"], dtype=float)
    vertices = []
    for line in data.decode("ascii", errors="strict").splitlines():
        fields = line.strip().split()
        if len(fields) == 4 and fields[0] == "vertex":
            vertices.append([float(value) for value in fields[1:]])
    if not vertices or len(vertices) % 3:
        raise ValueError(f"unparseable STL: {path}")
    return np.asarray(vertices, dtype=float).reshape(-1, 3, 3)


def rot_x(points: np.ndarray, degrees: float) -> np.ndarray:
    a = math.radians(degrees)
    matrix = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    return points @ matrix.T


def rot_z(points: np.ndarray, degrees: float) -> np.ndarray:
    a = math.radians(degrees)
    matrix = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    return points @ matrix.T


def upright(points: np.ndarray) -> np.ndarray:
    moved = rot_x(points, 90.0)
    moved[..., 2] += FRAME_LIFT
    return moved


def transform_front(triangles: np.ndarray) -> np.ndarray:
    return upright(triangles)


def transform_rear(triangles: np.ndarray) -> np.ndarray:
    moved = triangles.copy()
    moved[..., 2] += REAR_Z
    return upright(moved)


def transform_reel(triangles: np.ndarray, clockwise_deg: int) -> np.ndarray:
    moved = rot_z(triangles, -clockwise_deg)
    moved[..., 2] += REEL_Z
    return upright(moved)


def transform_stand(triangles: np.ndarray) -> np.ndarray:
    moved = triangles.copy()
    moved[..., 1] -= STAND_PIN_Y
    moved[..., 2] -= STAND_PIN_Z
    moved = rot_x(moved, STAND_DEPLOY_DEG)
    moved[..., 1] += STAND_HINGE_Y
    moved[..., 2] += STAND_HINGE_Z
    return upright(moved)


def source_and_wall() -> tuple[np.ndarray, float]:
    mask_y = -(REEL_Z + 1.6)
    source = np.array([0.0, mask_y - SOURCE_TO_MASK_MM, PORTAL_WORLD_Z])
    wall_y = mask_y + MASK_TO_WALL_MM
    return source, wall_y


def raster_shadow(triangles: np.ndarray, size: int) -> Image.Image:
    source, wall_y = source_and_wall()
    denom = triangles[..., 1] - source[1]
    scale = (wall_y - source[1]) / denom
    projected_x = source[0] + scale * (triangles[..., 0] - source[0])
    projected_z = source[2] + scale * (triangles[..., 2] - source[2])
    px = size / 2 + projected_x * size / VIEW_MM
    py = size / 2 - (projected_z - PORTAL_WORLD_Z) * size / VIEW_MM
    image = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(image)
    for xs, zs in zip(px, py):
        draw.polygon([(float(xs[i]), float(zs[i])) for i in range(3)], fill=255)
    return image


def composite(static_shadow: Image.Image, reel_triangles: np.ndarray, size: int) -> Image.Image:
    reel_shadow = raster_shadow(reel_triangles, size)
    shadow = np.maximum(np.asarray(static_shadow), np.asarray(reel_shadow))
    rgb = np.empty((size, size, 3), dtype=np.uint8)
    rgb[:] = (247, 224, 158)
    rgb[shadow > 0] = (25, 34, 52)
    return Image.fromarray(rgb, "RGB")


def metrics(image: Image.Image) -> dict[str, float]:
    array = np.asarray(image)
    size = image.width
    source, wall_y = source_and_wall()
    magnification = (wall_y - source[1]) / (0.0 - source[1])
    radius_px = PORTAL_D_MM / 2 * magnification * size / VIEW_MM
    yy, xx = np.ogrid[:size, :size]
    circle = (xx - size / 2) ** 2 + (yy - size / 2) ** 2 <= radius_px ** 2
    dark = (array[..., 0] < 100) & circle
    return {
        "dark_fraction_in_front_portal_bound": round(float(dark.sum() / circle.sum()), 6),
        "front_portal_projected_diameter_mm": round(PORTAL_D_MM * magnification, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    project = Path(args.project_dir)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "front_shell": project / "part_front_shell.stl",
        "rear_shell": project / "part_rear_shell.stl",
        "shadow_reel": project / "part_shadow_reel.stl",
        "kickstand": project / "part_kickstand.stl",
    }
    meshes = {name: load_stl(path) for name, path in paths.items()}
    static = np.concatenate([
        transform_front(meshes["front_shell"]),
        transform_rear(meshes["rear_shell"]),
        transform_stand(meshes["kickstand"]),
    ])
    static_work = raster_shadow(static, WORK_SIZE)
    static_state = raster_shadow(static, STATE_SIZE)
    rows = []
    thumbs = []
    for angle in range(0, 360, 5):
        reel = transform_reel(meshes["shadow_reel"], angle)
        image = composite(static_work, reel, WORK_SIZE)
        rows.append({"clockwise_deg": angle, **metrics(image)})
        thumbs.append(image.resize((144, 144), Image.Resampling.LANCZOS))
        if angle in STATE_NAMES:
            state = composite(static_state, transform_reel(meshes["shadow_reel"], angle), STATE_SIZE)
            state.save(output / f"state-{STATE_NAMES[angle]}-{angle:03d}.png")
    sheet = Image.new("RGB", (12 * 144, 6 * 170), (230, 225, 213))
    draw = ImageDraw.Draw(sheet)
    for index, (angle, thumb) in enumerate(zip(range(0, 360, 5), thumbs)):
        x = index % 12 * 144
        y = index // 12 * 170
        sheet.paste(thumb, (x, y))
        draw.text((x + 6, y + 148), f"{angle:03d} deg CW", fill=(20, 25, 35))
    sheet.save(output / "motion-contact-sheet.png")
    source, wall_y = source_and_wall()
    report = {
        "schema_version": 2,
        "kind": "lantern-menagerie.exact-four-mesh-point-source-ray-sweep",
        "evidence_class": "deterministic point-source triangle projection from all four exact exported STL meshes; not a finite-emitter or physical room test",
        "mesh_sha256": {name: sha256(path) for name, path in paths.items()},
        "light_geometry_mm": {
            "source_world_xyz": source.tolist(), "wall_plane_world_y": wall_y,
            "source_to_mask": SOURCE_TO_MASK_MM, "mask_to_wall": MASK_TO_WALL_MM,
            "front_portal_diameter": PORTAL_D_MM,
            "layer_order_world_y": {
                "source": source[1], "rear_shell_inner": -REAR_Z,
                "reel_rear": -(REEL_Z + 3.2), "reel_front": -REEL_Z,
                "front_shell_inner": -2.4, "wall": wall_y,
            },
        },
        "clockwise_angles_deg": list(range(0, 360, 5)),
        "states": {name: angle for angle, name in STATE_NAMES.items()},
        "samples": rows,
        "files": {
            "rabbit": "state-rabbit-000.png", "fox": "state-fox-120.png",
            "owl": "state-owl-240.png", "motion": "motion-contact-sheet.png",
        },
        "limitations": [
            "A point source cannot prove phone-emitter penumbra, brightness, room contrast, or human recognition.",
            "The 5-degree sweep proves the authored eclipse-wipe sequence, not continuous animal recognition between detents.",
        ],
    }
    (output / "shadow-sweep.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": True, "samples": len(rows), "output": output.as_posix()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
