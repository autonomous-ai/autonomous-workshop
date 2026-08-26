#!/usr/bin/env python3
"""Deterministic GLB preview capture, freezing, and manifest comparison."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw


SCHEMA_VERSION = 1
IMAGE_SIZE = (1000, 760)
VIEWS = (
    {"id": "hero", "role": "hero", "direction": [1.25, -1.5, 1.0], "up": [0, 0, 1]},
    {"id": "front", "role": "orthographic", "direction": [0, -1, 0.12], "up": [0, 0, 1]},
    {"id": "right", "role": "orthographic", "direction": [1, 0, 0.12], "up": [0, 0, 1]},
    {"id": "top", "role": "comparison", "direction": [0, 0, 1], "up": [0, 1, 0]},
)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _unit(vector) -> np.ndarray:
    value = np.asarray(vector, dtype=float)
    norm = np.linalg.norm(value)
    if norm <= 1e-12:
        raise ValueError("camera vector must be non-zero")
    return value / norm


def _mesh_from_glb(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, force="scene")
    if not isinstance(loaded, trimesh.Scene):
        loaded = trimesh.Scene(loaded)
    meshes = [mesh for mesh in loaded.dump(concatenate=False) if isinstance(mesh, trimesh.Trimesh)]
    if not meshes:
        raise ValueError(f"no triangle meshes in {path}")
    return trimesh.util.concatenate(meshes)


def render_view(mesh: trimesh.Trimesh, view: dict, output: Path) -> None:
    direction = _unit(view["direction"])
    up_hint = _unit(view["up"])
    right = _unit(np.cross(direction, up_hint))
    up = _unit(np.cross(right, direction))
    center = (mesh.bounds[0] + mesh.bounds[1]) / 2.0
    vertices = mesh.vertices - center
    projected = np.column_stack((vertices @ right, vertices @ up, vertices @ direction))
    x_span = float(np.ptp(projected[:, 0])) or 1.0
    y_span = float(np.ptp(projected[:, 1])) or 1.0
    scale = min((IMAGE_SIZE[0] - 100) / x_span, (IMAGE_SIZE[1] - 100) / y_span)
    pixels = np.column_stack((
        IMAGE_SIZE[0] / 2 + projected[:, 0] * scale,
        IMAGE_SIZE[1] / 2 - projected[:, 1] * scale,
    ))
    light = _unit([0.45, -0.6, 1.0])
    normals = mesh.face_normals
    order = np.argsort((projected[mesh.faces, 2]).mean(axis=1))
    image = Image.new("RGB", IMAGE_SIZE, (247, 247, 244))
    draw = ImageDraw.Draw(image)
    for face_index in order:
        face = mesh.faces[face_index]
        polygon = [tuple(pixels[index]) for index in face]
        shade = 0.56 + 0.34 * abs(float(np.dot(normals[face_index], light)))
        color = tuple(int(channel * shade) for channel in (92, 145, 174))
        draw.polygon(polygon, fill=color, outline=(39, 55, 64))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=False)


def capture(glb: Path, output_dir: Path, *, source_sha256: str | None = None) -> dict:
    glb = glb.resolve()
    mesh = _mesh_from_glb(glb)
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for view in VIEWS:
        output = output_dir / f"{view['id']}.png"
        render_view(mesh, view, output)
        records.append({
            **view, "projection": "orthographic", "output": output.name,
            "output_sha256": file_hash(output),
        })
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "renderer": "board-game-preview-painter-v1",
        "input": str(glb),
        "input_sha256": file_hash(glb),
        "source_sha256": source_sha256,
        "image_size": list(IMAGE_SIZE),
        "hero": "hero.png",
        "views": records,
    }
    (output_dir / "preview_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def validate_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported preview schema in {path}")
    base = path.parent
    input_path = Path(str(manifest.get("input", "")))
    if input_path.is_file() and file_hash(input_path) != manifest.get("input_sha256"):
        raise ValueError(f"stale preview input: {input_path}")
    for view in manifest.get("views", []):
        output = base / str(view.get("output", ""))
        if not output.is_file() or file_hash(output) != view.get("output_sha256"):
            raise ValueError(f"stale preview output: {output}")
    return manifest


def freeze(manifest_path: Path, reference: Path) -> int:
    manifest = validate_manifest(manifest_path)
    reference.mkdir(parents=True, exist_ok=True)
    for view in manifest["views"]:
        shutil.copy2(manifest_path.parent / view["output"], reference / view["output"])
    frozen = dict(manifest)
    frozen["input"] = str(Path(manifest["input"]).resolve())
    (reference / "preview_manifest.json").write_text(json.dumps(frozen, indent=2), encoding="utf-8")
    validate_manifest(reference / "preview_manifest.json")
    return len(manifest["views"])


def compare(final_path: Path, reference_path: Path) -> dict:
    final = validate_manifest(final_path)
    reference = validate_manifest(reference_path)
    final_cameras = [(row["id"], row["direction"], row["up"], row["projection"]) for row in final["views"]]
    reference_cameras = [(row["id"], row["direction"], row["up"], row["projection"]) for row in reference["views"]]
    if final_cameras != reference_cameras:
        raise ValueError("final and reference preview camera manifests differ")
    return {"ok": True, "views": [row[0] for row in final_cameras], "hero": final["hero"]}


def find_hero(home: Path) -> Path | None:
    """Return a hash-validated declared hero, preferring the final preview."""
    for manifest_path in (
        home / "project" / "preview" / "preview_manifest.json",
        home / "draft" / "preview_manifest.json",
        home / "reference" / "preview_manifest.json",
    ):
        if not manifest_path.is_file():
            continue
        try:
            manifest = validate_manifest(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        hero = manifest_path.parent / str(manifest.get("hero", ""))
        if hero.is_file():
            return hero
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("glb", type=Path)
    capture_parser.add_argument("output", type=Path)
    capture_parser.add_argument("--source-sha256")
    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("manifest", type=Path)
    freeze_parser.add_argument("reference", type=Path)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("final", type=Path)
    compare_parser.add_argument("reference", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "capture":
            result = capture(args.glb, args.output, source_sha256=args.source_sha256)
        elif args.command == "freeze":
            result = {"ok": True, "copied": freeze(args.manifest, args.reference)}
        else:
            result = compare(args.final, args.reference)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
