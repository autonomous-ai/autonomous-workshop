#!/usr/bin/env python3
"""Render deterministic CAD previews from Manhattan Nocturne's native GLB.

This is deliberately a CAD-preview renderer, not a concept-art generator and
not evidence of a physical print.  It uses only NumPy, Pillow, and trimesh so
it can run without a display server, GPU, browser, or Blender installation.

The native GLB written by the Workshop CAD tools is Y-up and metre-scaled.
This script restores the authored CAD coordinate convention (XY bed plane,
+Z up, millimetres), applies every occurrence transform, keeps node labels and
material colours, and writes a receipt beside every PNG.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Iterable, Mapping, Sequence

import numpy as np
from PIL import Image, ImageFilter
import trimesh


RENDERER_ID = "manhattan-nocturne-software-cad-preview"
RENDERER_VERSION = 2

ROLE_ORDER = ("pawn", "rook", "knight", "bishop", "queen", "king")
SIDE_ORDER = ("stone", "steel")
NEUTRAL_REVIEW_RGBA = (142, 145, 149, 255)

FALLBACK_COLORS: Mapping[str, tuple[int, int, int, int]] = {
    "board": (27, 32, 40, 255),
    "stone": (215, 204, 183, 255),
    "steel": (23, 28, 37, 255),
    "default": (63, 117, 106, 255),
}


@dataclass(frozen=True)
class ViewRecipe:
    key: str
    filename: str
    semantic_side: str | None
    fallback_direction_cad: tuple[float, float, float]
    projection: str = "orthographic"
    margin_fraction: float = 0.075
    shadow: bool = True
    depth_edges: bool = False
    scene_mode: str = "full"
    material_mode: str = "glb"
    lighting_mode: str = "studio"
    evidence_class: str = "exact-cad-preview"
    product_beauty_render: bool = True


VIEW_RECIPES: Mapping[str, ViewRecipe] = {
    "hero-stone": ViewRecipe(
        key="hero-stone",
        filename="01-hero-stone.png",
        semantic_side="stone",
        fallback_direction_cad=(1.0, -1.2, 0.85),
    ),
    "hero-steel": ViewRecipe(
        key="hero-steel",
        filename="02-hero-steel.png",
        semantic_side="steel",
        fallback_direction_cad=(-1.0, 1.2, 0.85),
    ),
    "top-inventory": ViewRecipe(
        key="top-inventory",
        filename="03-top-inventory.png",
        semantic_side=None,
        fallback_direction_cad=(0.0, 0.0, 1.0),
        margin_fraction=0.045,
        shadow=False,
        depth_edges=True,
        product_beauty_render=False,
    ),
    "rank-lineup": ViewRecipe(
        key="rank-lineup",
        filename="04-rank-lineup.png",
        semantic_side=None,
        fallback_direction_cad=(0.0, -1.0, 0.10),
        margin_fraction=0.045,
        shadow=True,
        scene_mode="rank-lineup",
        material_mode="neutral-review",
        lighting_mode="symmetric-review",
        evidence_class="exact-cad-recognition-input",
        product_beauty_render=False,
    ),
    "side-detail": ViewRecipe(
        key="side-detail",
        filename="05-side-detail.png",
        semantic_side=None,
        fallback_direction_cad=(0.42, -1.0, 0.16),
        margin_fraction=0.055,
        shadow=True,
        scene_mode="side-detail",
        material_mode="neutral-review",
        lighting_mode="symmetric-review",
        evidence_class="exact-cad-recognition-input",
        product_beauty_render=False,
    ),
    "board-inventory-engineering": ViewRecipe(
        key="board-inventory-engineering",
        filename="06-board-inventory-engineering.png",
        semantic_side=None,
        fallback_direction_cad=(0.65, -1.0, 1.10),
        margin_fraction=0.045,
        shadow=True,
        depth_edges=True,
        scene_mode="board-inventory-engineering",
        material_mode="glb",
        lighting_mode="studio",
        evidence_class="exact-cad-engineering-view",
        product_beauty_render=False,
    ),
    "neutral-start-recognition": ViewRecipe(
        key="neutral-start-recognition",
        filename="07-neutral-start-recognition.png",
        semantic_side="stone",
        fallback_direction_cad=(1.0, -1.2, 0.85),
        margin_fraction=0.075,
        shadow=True,
        scene_mode="full",
        material_mode="neutral-review",
        lighting_mode="symmetric-review",
        evidence_class="exact-cad-recognition-input",
        product_beauty_render=False,
    ),
}


@dataclass
class SceneNode:
    label: str
    geometry_name: str
    source_transform_glb: np.ndarray
    review_transform_cad: np.ndarray
    source_bounds_cad_mm: np.ndarray
    vertices_cad_mm: np.ndarray
    faces: np.ndarray
    face_rgba: np.ndarray
    color_source: str
    color_encoding: str
    source_face_rgba: np.ndarray
    source_color_source: str
    source_color_encoding: str
    closed_outward_winding: bool
    roughness: float
    metallic: float

    @property
    def bounds(self) -> np.ndarray:
        return np.vstack(
            (self.vertices_cad_mm.min(axis=0), self.vertices_cad_mm.max(axis=0))
        )

    @property
    def center(self) -> np.ndarray:
        bounds = self.bounds
        return (bounds[0] + bounds[1]) * 0.5


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _portable_path(path: Path, owner: Path) -> str:
    try:
        return os.path.relpath(path.resolve(), owner.resolve().parent).replace(os.sep, "/")
    except ValueError:
        return path.resolve().as_posix()


def _normalize(vector: Sequence[float]) -> np.ndarray:
    value = np.asarray(vector, dtype=np.float64)
    length = float(np.linalg.norm(value))
    if not math.isfinite(length) or length <= 1e-12:
        raise ValueError("cannot normalize a zero or non-finite vector")
    return value / length


def _rgba(value: object, fallback: tuple[int, int, int, int]) -> np.ndarray:
    if value is None:
        return np.asarray(fallback, dtype=np.uint8)
    try:
        raw = np.asarray(value).reshape(-1)
    except Exception:  # noqa: BLE001 - third-party material objects vary
        return np.asarray(fallback, dtype=np.uint8)
    if len(raw) < 3:
        return np.asarray(fallback, dtype=np.uint8)
    raw = raw[:4].astype(np.float64)
    if len(raw) == 3:
        raw = np.append(raw, 1.0 if float(np.max(raw)) <= 1.0 else 255.0)
    if float(np.max(raw)) <= 1.0:
        raw *= 255.0
    return np.clip(np.rint(raw), 0, 255).astype(np.uint8)


def _semantic_fallback(label: str) -> tuple[int, int, int, int]:
    lowered = label.casefold()
    for token in ("board", "stone", "steel"):
        if token in lowered:
            return FALLBACK_COLORS[token]
    return FALLBACK_COLORS["default"]


def _material_colors(
    mesh: trimesh.Trimesh,
    label: str,
) -> tuple[np.ndarray, str, str, float, float]:
    """Return one RGBA value per face without discarding GLB material data."""

    fallback = _semantic_fallback(label)
    visual = mesh.visual

    face_colors = getattr(visual, "face_colors", None)
    visual_kind = getattr(visual, "kind", None)
    if visual_kind == "face" and face_colors is not None and len(face_colors) == len(mesh.faces):
        values = np.asarray(face_colors)
        if values.ndim == 2 and values.shape[1] >= 3:
            if values.shape[1] == 3:
                values = np.column_stack(
                    (values, np.full(len(values), 255, dtype=values.dtype))
                )
            return (
                np.clip(values[:, :4], 0, 255).astype(np.uint8),
                "glb-face-colors",
                "linear-rgb-factor-u8",
                0.55,
                0.0,
            )

    material = getattr(visual, "material", None)
    base = None
    roughness = 0.55
    metallic = 0.0
    if material is not None:
        base = getattr(material, "baseColorFactor", None)
        if base is None:
            base = getattr(material, "main_color", None)
        material_roughness = getattr(material, "roughnessFactor", None)
        material_metallic = getattr(material, "metallicFactor", None)
        if material_roughness is not None:
            roughness = float(np.clip(material_roughness, 0.0, 1.0))
        if material_metallic is not None:
            metallic = float(np.clip(material_metallic, 0.0, 1.0))

    if base is not None:
        color = _rgba(base, fallback)
        return (
            np.repeat(color[None, :], len(mesh.faces), axis=0),
            "glb-material-base-color",
            # glTF baseColorFactor is linear. trimesh exposes it as uint8,
            # but it must not be decoded as sRGB a second time.
            "linear-rgb-factor-u8",
            roughness,
            metallic,
        )

    color = np.asarray(fallback, dtype=np.uint8)
    return (
        np.repeat(color[None, :], len(mesh.faces), axis=0),
        "semantic-fallback",
        "srgb-u8",
        roughness,
        metallic,
    )


def _apply_transform(vertices: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    homogenous = np.column_stack(
        (np.asarray(vertices, dtype=np.float64), np.ones(len(vertices), dtype=np.float64))
    )
    transformed = homogenous @ np.asarray(matrix, dtype=np.float64).T
    weights = transformed[:, 3:4]
    if np.any(np.abs(weights) <= 1e-12):
        raise ValueError("GLB occurrence transform produced a zero homogeneous weight")
    return transformed[:, :3] / weights


def _signed_volume(vertices: np.ndarray, faces: np.ndarray) -> float:
    triangles = vertices[faces]
    return float(
        np.einsum(
            "ij,ij->i",
            triangles[:, 0],
            np.cross(triangles[:, 1], triangles[:, 2]),
        ).sum()
        / 6.0
    )


def load_native_glb(path: Path, unit_scale_to_mm: float = 1000.0) -> list[SceneNode]:
    loaded = trimesh.load(path, force="scene", process=False)
    if isinstance(loaded, trimesh.Trimesh):
        loaded = trimesh.Scene(loaded)
    if not isinstance(loaded, trimesh.Scene):
        raise ValueError(f"trimesh returned unsupported object {type(loaded).__name__}")

    nodes: list[SceneNode] = []
    for node_name in sorted(loaded.graph.nodes_geometry, key=str.casefold):
        transform, geometry_name = loaded.graph[node_name]
        source = loaded.geometry[geometry_name]
        if not isinstance(source, trimesh.Trimesh):
            continue
        if len(source.vertices) == 0 or len(source.faces) == 0:
            continue

        world_glb = _apply_transform(np.asarray(source.vertices), np.asarray(transform))
        # cadgen native GLB: (CAD X, CAD Z, CAD Y) metres. Restore the authored
        # XY bed plane and +Z-up convention in millimetres.
        vertices = np.column_stack((world_glb[:, 0], world_glb[:, 2], world_glb[:, 1]))
        vertices *= float(unit_scale_to_mm)

        # Swapping GLB Y/Z is a reflection. Reverse triangle winding once, then
        # make it outward if a closed solid still reports negative volume.
        faces = np.asarray(source.faces, dtype=np.int64)[:, [0, 2, 1]].copy()
        volume = _signed_volume(vertices, faces)
        closed = bool(getattr(source, "is_watertight", False)) and abs(volume) > 1e-9
        if closed and volume < 0.0:
            faces = faces[:, [0, 2, 1]]

        rgba, color_source, color_encoding, roughness, metallic = _material_colors(
            source, str(node_name)
        )
        source_bounds = np.vstack((vertices.min(axis=0), vertices.max(axis=0)))
        nodes.append(
            SceneNode(
                label=str(node_name),
                geometry_name=str(geometry_name),
                source_transform_glb=np.asarray(transform, dtype=np.float64),
                review_transform_cad=np.eye(4, dtype=np.float64),
                source_bounds_cad_mm=source_bounds,
                vertices_cad_mm=vertices,
                faces=faces,
                face_rgba=rgba,
                color_source=color_source,
                color_encoding=color_encoding,
                source_face_rgba=rgba.copy(),
                source_color_source=color_source,
                source_color_encoding=color_encoding,
                closed_outward_winding=closed,
                roughness=roughness,
                metallic=metallic,
            )
        )

    if not nodes:
        raise ValueError("GLB contains no triangle-bearing scene nodes")
    return nodes


def _scene_bounds(nodes: Iterable[SceneNode]) -> np.ndarray:
    bounds = [node.bounds for node in nodes]
    if not bounds:
        raise ValueError("cannot find bounds of an empty scene")
    return np.vstack(
        (
            np.min([value[0] for value in bounds], axis=0),
            np.max([value[1] for value in bounds], axis=0),
        )
    )


def _transformed_node(
    node: SceneNode,
    matrix_cad: np.ndarray,
    *,
    label: str | None = None,
) -> SceneNode:
    matrix = np.asarray(matrix_cad, dtype=np.float64)
    if matrix.shape != (4, 4):
        raise ValueError("review transform must be a 4x4 matrix")
    vertices = _apply_transform(node.vertices_cad_mm, matrix)
    faces = node.faces.copy()
    closed = node.closed_outward_winding
    if float(np.linalg.det(matrix[:3, :3])) < 0.0:
        faces = faces[:, [0, 2, 1]]
    return SceneNode(
        label=label or node.label,
        geometry_name=node.geometry_name,
        source_transform_glb=node.source_transform_glb.copy(),
        review_transform_cad=matrix @ node.review_transform_cad,
        source_bounds_cad_mm=node.source_bounds_cad_mm.copy(),
        vertices_cad_mm=vertices,
        faces=faces,
        face_rgba=node.face_rgba.copy(),
        color_source=node.color_source,
        color_encoding=node.color_encoding,
        source_face_rgba=node.source_face_rgba.copy(),
        source_color_source=node.source_color_source,
        source_color_encoding=node.source_color_encoding,
        closed_outward_winding=closed,
        roughness=node.roughness,
        metallic=node.metallic,
    )


def _translation(x: float, y: float, z: float) -> np.ndarray:
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, 3] = (x, y, z)
    return matrix


def _place_on_review_floor(
    node: SceneNode,
    target_x: float,
    target_y: float,
) -> SceneNode:
    bounds = node.bounds
    center = (bounds[0] + bounds[1]) * 0.5
    matrix = _translation(
        target_x - float(center[0]),
        target_y - float(center[1]),
        -float(bounds[0, 2]),
    )
    return _transformed_node(node, matrix)


def _representative(
    nodes: Sequence[SceneNode],
    side: str,
    role: str,
) -> SceneNode:
    prefix = f"{side}_{role}_"
    matches = sorted(
        (node for node in nodes if node.label.casefold().startswith(prefix)),
        key=lambda node: node.label.casefold(),
    )
    if not matches:
        raise ValueError(f"GLB is missing a labeled {side} {role} occurrence")
    return matches[0]


def _board_node(nodes: Sequence[SceneNode]) -> SceneNode:
    matches = [node for node in nodes if node.label.casefold() == "board"]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one board node, found {len(matches)}")
    return matches[0]


def _line_layout(
    entries: Sequence[tuple[str, str, SceneNode]],
    *,
    within_pair_gap: float = 7.0,
    between_pair_gap: float = 16.0,
) -> tuple[list[SceneNode], list[Mapping[str, object]]]:
    cursor = 0.0
    planned: list[tuple[str, str, SceneNode, float]] = []
    for index, (side, role, node) in enumerate(entries):
        width = float(node.bounds[1, 0] - node.bounds[0, 0])
        center_x = cursor + width * 0.5
        planned.append((side, role, node, center_x))
        cursor += width
        if index + 1 < len(entries):
            next_role = entries[index + 1][1]
            cursor += within_pair_gap if next_role == role else between_pair_gap

    overall_center = cursor * 0.5
    placed: list[SceneNode] = []
    layout: list[Mapping[str, object]] = []
    for side, role, node, center_x in planned:
        target_x = center_x - overall_center
        result = _place_on_review_floor(node, target_x, 0.0)
        placed.append(result)
        layout.append(
            {
                "source_label": node.label,
                "side": side,
                "role": role,
                "target_base_center_cad_mm": [round(target_x, 6), 0.0, 0.0],
            }
        )
    return placed, layout


def _neutral_material(node: SceneNode) -> SceneNode:
    result = _transformed_node(node, np.eye(4, dtype=np.float64))
    color = np.asarray(NEUTRAL_REVIEW_RGBA, dtype=np.uint8)
    result.face_rgba = np.repeat(color[None, :], len(result.faces), axis=0)
    result.color_source = "neutral-recognition-review-override"
    result.color_encoding = "srgb-u8"
    result.roughness = 0.72
    result.metallic = 0.0
    return result


def _prepare_view_scene(
    source_nodes: Sequence[SceneNode],
    recipe: ViewRecipe,
) -> tuple[list[SceneNode], Mapping[str, object]]:
    layout: list[Mapping[str, object]] = []

    if recipe.scene_mode == "full":
        nodes = [
            _transformed_node(node, np.eye(4, dtype=np.float64))
            for node in source_nodes
        ]
    elif recipe.scene_mode == "rank-lineup":
        entries = [
            (side, role, _representative(source_nodes, side, role))
            for role in ROLE_ORDER
            for side in SIDE_ORDER
        ]
        nodes, layout = _line_layout(entries)
    elif recipe.scene_mode == "side-detail":
        detail_roles = ("bishop", "queen")
        entries = [
            (side, role, _representative(source_nodes, side, role))
            for role in detail_roles
            for side in SIDE_ORDER
        ]
        nodes, layout = _line_layout(
            entries,
            within_pair_gap=9.0,
            between_pair_gap=24.0,
        )
    elif recipe.scene_mode == "board-inventory-engineering":
        board = _place_on_review_floor(_board_node(source_nodes), -145.0, 0.0)
        nodes = [board]
        layout.append(
            {
                "source_label": "board",
                "purpose": "clean one-piece board",
                "target_base_center_cad_mm": [-145.0, 0.0, 0.0],
            }
        )
        first_x = 18.0
        pitch_x = 37.0
        for side_index, side in enumerate(SIDE_ORDER):
            target_y = -39.0 if side_index == 0 else 39.0
            for role_index, role in enumerate(ROLE_ORDER):
                source = _representative(source_nodes, side, role)
                target_x = first_x + pitch_x * role_index
                nodes.append(_place_on_review_floor(source, target_x, target_y))
                layout.append(
                    {
                        "source_label": source.label,
                        "side": side,
                        "role": role,
                        "target_base_center_cad_mm": [
                            round(target_x, 6),
                            round(target_y, 6),
                            0.0,
                        ],
                    }
                )
    else:
        raise ValueError(f"unknown review scene mode {recipe.scene_mode!r}")

    source_material_summary = {
        node.label: {
            "source": node.source_color_source,
            "encoding": node.source_color_encoding,
            "colors": _color_summary_values(node.source_face_rgba),
        }
        for node in nodes
    }
    if recipe.material_mode == "neutral-review":
        nodes = [_neutral_material(node) for node in nodes]
        material_override: Mapping[str, object] | None = {
            "mode": "neutral-recognition-review",
            "rgba_srgb": list(NEUTRAL_REVIEW_RGBA),
            "applies_to": "display only; source GLB materials remain in each node receipt",
        }
    elif recipe.material_mode == "glb":
        material_override = None
    else:
        raise ValueError(f"unknown material mode {recipe.material_mode!r}")

    derivation: Mapping[str, object] = {
        "mode": recipe.scene_mode,
        "source_node_count": len(source_nodes),
        "selected_node_count": len(nodes),
        "selected_source_labels": [node.label for node in nodes],
        "review_layout": layout,
        "material_mode": recipe.material_mode,
        "material_override": material_override,
        "source_material_summary": source_material_summary,
        "geometry_policy": (
            "exact source triangles with deterministic rigid review transforms; "
            "no generated or altered product geometry"
        ),
    }
    return nodes, derivation


def _semantic_direction(
    nodes: Sequence[SceneNode],
    recipe: ViewRecipe,
) -> tuple[np.ndarray, Mapping[str, object], list[str]]:
    fallback = _normalize(recipe.fallback_direction_cad)
    if recipe.semantic_side is None:
        return fallback, {"mode": "fixed", "semantic_side": None}, []

    matching = [
        node for node in nodes if recipe.semantic_side in node.label.casefold()
    ]
    if not matching:
        warning = (
            f"no node label contains {recipe.semantic_side!r}; "
            "used the frozen fallback camera"
        )
        return (
            fallback,
            {
                "mode": "fallback",
                "semantic_side": recipe.semantic_side,
                "matched_nodes": [],
            },
            [warning],
        )

    bounds = _scene_bounds(nodes)
    scene_center = (bounds[0] + bounds[1]) * 0.5
    side_center = np.mean([node.center for node in matching], axis=0)
    horizontal = side_center[:2] - scene_center[:2]
    length = float(np.linalg.norm(horizontal))
    if length <= 1e-6:
        warning = (
            f"{recipe.semantic_side!r} nodes do not define a horizontal side; "
            "used the frozen fallback camera"
        )
        return (
            fallback,
            {
                "mode": "fallback",
                "semantic_side": recipe.semantic_side,
                "matched_nodes": [node.label for node in matching],
            },
            [warning],
        )

    side = horizontal / length
    lateral = np.array((-side[1], side[0]), dtype=np.float64)
    direction = _normalize((
        float(side[0] + 0.55 * lateral[0]),
        float(side[1] + 0.55 * lateral[1]),
        0.78,
    ))
    return (
        direction,
        {
            "mode": "semantic-node-centroid",
            "semantic_side": recipe.semantic_side,
            "matched_nodes": [node.label for node in matching],
            "side_center_cad_mm": np.round(side_center, 6).tolist(),
        },
        [],
    )


def _camera_basis(direction: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    view = _normalize(direction)
    world_up = np.array((0.0, 0.0, 1.0), dtype=np.float64)
    if abs(float(np.dot(view, world_up))) > 0.999:
        return (
            np.array((1.0, 0.0, 0.0), dtype=np.float64),
            np.array((0.0, 1.0, 0.0), dtype=np.float64),
        )
    right = _normalize(np.cross(view, world_up))
    up = _normalize(np.cross(right, view))
    return right, up


def _srgb_to_linear(values: np.ndarray) -> np.ndarray:
    source = np.asarray(values, dtype=np.float64)
    return np.where(
        source <= 0.04045,
        source / 12.92,
        ((source + 0.055) / 1.055) ** 2.4,
    )


def _linear_to_srgb(values: np.ndarray) -> np.ndarray:
    source = np.clip(np.asarray(values, dtype=np.float64), 0.0, 1.0)
    return np.where(
        source <= 0.0031308,
        source * 12.92,
        1.055 * np.power(source, 1.0 / 2.4) - 0.055,
    )


def _shade_faces(
    node: SceneNode,
    camera_direction: np.ndarray,
    lighting_mode: str,
) -> tuple[np.ndarray, np.ndarray]:
    triangles = node.vertices_cad_mm[node.faces]
    normals = np.cross(
        triangles[:, 1] - triangles[:, 0],
        triangles[:, 2] - triangles[:, 0],
    )
    lengths = np.linalg.norm(normals, axis=1)
    valid = lengths > 1e-12
    normals[valid] /= lengths[valid, None]

    camera = _normalize(camera_direction)
    if lighting_mode == "studio":
        key = _normalize((0.42, -0.52, 0.75))
        fill = _normalize((-0.55, 0.28, 0.57))
        key_weight = 0.53
        fill_weight = 0.17
    elif lighting_mode == "symmetric-review":
        right, up = _camera_basis(camera)
        key = _normalize(camera * 0.38 + up * 0.88 + right * 0.18)
        fill = _normalize(camera * 0.38 + up * 0.88 - right * 0.18)
        key_weight = 0.35
        fill_weight = 0.35
    else:
        raise ValueError(f"unknown lighting mode {lighting_mode!r}")

    key_term = np.maximum(normals @ key, 0.0)
    fill_term = np.maximum(normals @ fill, 0.0)
    rim_term = 1.0 - np.clip(np.abs(normals @ camera), 0.0, 1.0)

    # Matte PLA-like preview lighting. The GLB roughness lightly controls the
    # highlight but never turns this into a claim about a physical finish.
    half_vector = _normalize(key + camera)
    specular_power = 18.0 + 46.0 * float(node.roughness)
    specular = np.power(np.maximum(normals @ half_vector, 0.0), specular_power)
    specular_strength = 0.025 + 0.055 * (1.0 - float(node.roughness))
    diffuse = np.clip(
        0.31 + key_weight * key_term + fill_weight * fill_term + 0.045 * rim_term,
        0.20,
        1.05,
    )

    encoded = node.face_rgba[:, :3].astype(np.float64) / 255.0
    if node.color_encoding == "linear-rgb-factor-u8":
        base = encoded
    else:
        base = _srgb_to_linear(encoded)
    lit = np.clip(base * diffuse[:, None] + specular[:, None] * specular_strength, 0.0, 1.0)
    rgb = np.rint(_linear_to_srgb(lit) * 255.0).astype(np.uint8)

    # With outward winding, only faces toward the camera can win the final
    # image. Open meshes skip culling so a malformed preview remains visible
    # rather than silently disappearing.
    visible = (normals @ camera) >= -1e-9 if node.closed_outward_winding else valid
    return rgb, visible & valid


def _background(width: int, height: int) -> np.ndarray:
    top = np.array((240, 237, 230), dtype=np.float64)
    bottom = np.array((228, 222, 211), dtype=np.float64)
    blend = np.linspace(0.0, 1.0, height, dtype=np.float64)[:, None, None]
    pixels = top[None, None, :] * (1.0 - blend) + bottom[None, None, :] * blend
    return np.broadcast_to(pixels, (height, width, 3)).copy().astype(np.uint8)


def _raster_triangle(
    screen_xy: np.ndarray,
    depths: np.ndarray,
    color: np.ndarray,
    image: np.ndarray,
    object_mask: np.ndarray,
    zbuffer: np.ndarray,
) -> None:
    height, width = zbuffer.shape
    min_x = max(int(math.floor(float(screen_xy[:, 0].min()))) - 1, 0)
    max_x = min(int(math.ceil(float(screen_xy[:, 0].max()))) + 2, width)
    min_y = max(int(math.floor(float(screen_xy[:, 1].min()))) - 1, 0)
    max_y = min(int(math.ceil(float(screen_xy[:, 1].max()))) + 2, height)
    if max_x <= min_x or max_y <= min_y:
        return

    x0, y0 = screen_xy[0]
    x1, y1 = screen_xy[1]
    x2, y2 = screen_xy[2]
    denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(float(denominator)) <= 1e-12:
        return

    xs = np.arange(min_x, max_x, dtype=np.float32)[None, :] + 0.5
    ys = np.arange(min_y, max_y, dtype=np.float32)[:, None] + 0.5
    l0 = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / denominator
    l1 = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / denominator
    l2 = 1.0 - l0 - l1
    inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
    if not bool(np.any(inside)):
        return

    depth = l0 * depths[0] + l1 * depths[1] + l2 * depths[2]
    local_z = zbuffer[min_y:max_y, min_x:max_x]
    hit = inside & (depth > local_z)
    if not bool(np.any(hit)):
        return
    local_z[hit] = depth[hit]
    image[min_y:max_y, min_x:max_x][hit] = color
    object_mask[min_y:max_y, min_x:max_x][hit] = 255


def _composite_shadow(
    background: np.ndarray,
    object_pixels: np.ndarray,
    object_mask: np.ndarray,
    supersample: int,
    enabled: bool,
) -> np.ndarray:
    base = background.astype(np.float64)
    if enabled:
        mask_image = Image.fromarray(object_mask, mode="L")
        shifted = Image.new("L", mask_image.size, 0)
        offset = (12 * supersample, 20 * supersample)
        shifted.paste(mask_image, offset)
        blurred = shifted.filter(ImageFilter.GaussianBlur(radius=15 * supersample))
        alpha = np.asarray(blurred, dtype=np.float64)[..., None] / 255.0 * 0.22
        shadow_color = np.array((91.0, 80.0, 67.0), dtype=np.float64)
        base = base * (1.0 - alpha) + shadow_color[None, None, :] * alpha

    opaque = object_mask > 0
    base[opaque] = object_pixels[opaque]
    return np.clip(np.rint(base), 0, 255).astype(np.uint8)


def _apply_depth_edge_lighting(
    object_pixels: np.ndarray,
    object_mask: np.ndarray,
    zbuffer: np.ndarray,
    threshold_mm: float = 0.08,
) -> None:
    """Add a restrained raking-light cue at exact z-buffer discontinuities.

    A top camera otherwise gives two horizontal board faces identical lighting,
    hiding the board's real 0.35 mm square recesses. This operation neither
    changes geometry nor assigns checker colors: it brightens the higher side
    and darkens the lower side of a measured depth step.
    """

    bright = np.zeros(object_mask.shape, dtype=bool)
    dark = np.zeros(object_mask.shape, dtype=bool)

    horizontal_valid = (object_mask[:, :-1] > 0) & (object_mask[:, 1:] > 0)
    horizontal_delta = np.zeros_like(zbuffer[:, 1:])
    np.subtract(
        zbuffer[:, 1:],
        zbuffer[:, :-1],
        out=horizontal_delta,
        where=horizontal_valid,
    )
    horizontal_edge = horizontal_valid & (np.abs(horizontal_delta) >= threshold_mm)
    right_high = horizontal_edge & (horizontal_delta > 0.0)
    left_high = horizontal_edge & (horizontal_delta < 0.0)
    bright[:, 1:] |= right_high
    dark[:, :-1] |= right_high
    bright[:, :-1] |= left_high
    dark[:, 1:] |= left_high

    vertical_valid = (object_mask[:-1, :] > 0) & (object_mask[1:, :] > 0)
    vertical_delta = np.zeros_like(zbuffer[1:, :])
    np.subtract(
        zbuffer[1:, :],
        zbuffer[:-1, :],
        out=vertical_delta,
        where=vertical_valid,
    )
    vertical_edge = vertical_valid & (np.abs(vertical_delta) >= threshold_mm)
    lower_high = vertical_edge & (vertical_delta > 0.0)
    upper_high = vertical_edge & (vertical_delta < 0.0)
    bright[1:, :] |= lower_high
    dark[:-1, :] |= lower_high
    bright[:-1, :] |= upper_high
    dark[1:, :] |= upper_high

    pixels = object_pixels.astype(np.float64)
    pixels[dark] *= 0.63
    pixels[bright] = pixels[bright] * 1.16 + 3.0
    object_pixels[:] = np.clip(np.rint(pixels), 0, 255).astype(np.uint8)


def render_view(
    nodes: Sequence[SceneNode],
    recipe: ViewRecipe,
    width: int,
    height: int,
    supersample: int,
) -> tuple[Image.Image, Mapping[str, object], list[str]]:
    camera_direction, camera_resolution, warnings = _semantic_direction(nodes, recipe)
    right, up = _camera_basis(camera_direction)
    internal_width = width * supersample
    internal_height = height * supersample

    projected_by_node: list[tuple[SceneNode, np.ndarray, np.ndarray]] = []
    all_projected: list[np.ndarray] = []
    for node in nodes:
        vertices = node.vertices_cad_mm
        projected = np.column_stack((vertices @ right, vertices @ up))
        depths = vertices @ camera_direction
        projected_by_node.append((node, projected, depths))
        all_projected.append(projected)

    combined = np.vstack(all_projected)
    low = combined.min(axis=0)
    high = combined.max(axis=0)
    span = np.maximum(high - low, 1e-9)
    margin_x = internal_width * recipe.margin_fraction
    margin_y = internal_height * recipe.margin_fraction
    scale = min(
        (internal_width - 2.0 * margin_x) / span[0],
        (internal_height - 2.0 * margin_y) / span[1],
    )
    center = (low + high) * 0.5

    object_pixels = np.zeros((internal_height, internal_width, 3), dtype=np.uint8)
    object_mask = np.zeros((internal_height, internal_width), dtype=np.uint8)
    zbuffer = np.full((internal_height, internal_width), -np.inf, dtype=np.float32)

    rendered_triangles = 0
    culled_triangles = 0
    for node, projected, depths in projected_by_node:
        screen = (projected - center) * scale
        screen[:, 0] += internal_width * 0.5
        screen[:, 1] = internal_height * 0.5 - screen[:, 1]
        shaded, visible = _shade_faces(
            node,
            camera_direction,
            lighting_mode=recipe.lighting_mode,
        )
        for face_index, face in enumerate(node.faces):
            if not bool(visible[face_index]):
                culled_triangles += 1
                continue
            _raster_triangle(
                screen[face],
                depths[face],
                shaded[face_index],
                object_pixels,
                object_mask,
                zbuffer,
            )
            rendered_triangles += 1

    depth_edge_threshold_mm = 0.08
    if recipe.depth_edges:
        _apply_depth_edge_lighting(
            object_pixels,
            object_mask,
            zbuffer,
            threshold_mm=depth_edge_threshold_mm,
        )

    background = _background(internal_width, internal_height)
    composited = _composite_shadow(
        background,
        object_pixels,
        object_mask,
        supersample,
        enabled=recipe.shadow,
    )
    image = Image.fromarray(composited, mode="RGB")
    if supersample != 1:
        image = image.resize((width, height), Image.Resampling.LANCZOS)

    scene_bounds = _scene_bounds(nodes)
    camera = {
        "projection": recipe.projection,
        "direction_cad": np.round(camera_direction, 9).tolist(),
        "right_cad": np.round(right, 9).tolist(),
        "up_cad": np.round(up, 9).tolist(),
        "resolution": camera_resolution,
        "framed_projected_bounds_cad_mm": np.round(
            np.vstack((low, high)), 6
        ).tolist(),
    }
    stats = {
        "camera": camera,
        "scene_bounds_cad_mm": np.round(scene_bounds, 6).tolist(),
        "output_pixels": [width, height],
        "internal_pixels": [internal_width, internal_height],
        "supersample": supersample,
        "rendered_triangles": rendered_triangles,
        "culled_triangles": culled_triangles,
        "shadow": recipe.shadow,
        "lighting_mode": recipe.lighting_mode,
        "material_mode": recipe.material_mode,
        "depth_edge_emphasis": {
            "enabled": recipe.depth_edges,
            "threshold_mm": depth_edge_threshold_mm,
            "basis": "exact z-buffer discontinuities",
        },
    }
    return image, stats, warnings


def _color_summary_values(values: np.ndarray) -> list[Mapping[str, object]]:
    unique, counts = np.unique(values, axis=0, return_counts=True)
    order = np.argsort(-counts)
    return [
        {"rgba": unique[index].astype(int).tolist(), "faces": int(counts[index])}
        for index in order
    ]


def _color_summary(node: SceneNode) -> list[Mapping[str, object]]:
    return _color_summary_values(node.face_rgba)


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _node_receipt(node: SceneNode) -> Mapping[str, object]:
    payload: dict[str, object] = {
        "label": node.label,
        "geometry": node.geometry_name,
        "source_transform_glb": np.round(node.source_transform_glb, 9).tolist(),
        "review_transform_cad": np.round(node.review_transform_cad, 9).tolist(),
        "source_bounds_cad_mm": np.round(node.source_bounds_cad_mm, 6).tolist(),
        "bounds_cad_mm": np.round(node.bounds, 6).tolist(),
        "vertices": int(len(node.vertices_cad_mm)),
        "triangles": int(len(node.faces)),
        "display_material": {
            "colors": _color_summary(node),
            "source": node.color_source,
            "encoding": node.color_encoding,
        },
        "source_glb_material": {
            "colors": _color_summary_values(node.source_face_rgba),
            "source": node.source_color_source,
            "encoding": node.source_color_encoding,
        },
        "roughness": round(float(node.roughness), 6),
        "metallic": round(float(node.metallic), 6),
    }
    payload["record_sha256"] = _canonical_sha256(payload)
    return payload


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def render_product(
    input_path: Path,
    output_dir: Path,
    view_keys: Sequence[str],
    width: int,
    height: int,
    supersample: int,
    unit_scale_to_mm: float,
) -> Mapping[str, object]:
    source_nodes = load_native_glb(input_path, unit_scale_to_mm=unit_scale_to_mm)
    output_dir.mkdir(parents=True, exist_ok=True)

    script_path = Path(__file__).resolve()
    input_hash = _sha256(input_path)
    script_hash = _sha256(script_path)
    results: list[Mapping[str, object]] = []

    for key in view_keys:
        recipe = VIEW_RECIPES[key]
        nodes, scene_derivation = _prepare_view_scene(source_nodes, recipe)
        node_receipts = [_node_receipt(node) for node in nodes]
        output_path = output_dir / recipe.filename
        image, render_stats, warnings = render_view(
            nodes,
            recipe,
            width=width,
            height=height,
            supersample=supersample,
        )
        image.save(output_path, format="PNG", optimize=True)

        receipt_path = output_path.with_suffix(".render.json")
        receipt: Mapping[str, object] = {
            "schema": "workshop.cad-preview-render.v2",
            "renderer": {"id": RENDERER_ID, "version": RENDERER_VERSION},
            "view": key,
            "input": {
                "path": _portable_path(input_path, receipt_path),
                "sha256": input_hash,
                "format": "native-glb",
                "native_axes": "Y-up",
                "native_units": "metres",
                "restored_axes": "CAD XY bed plane, +Z up",
                "unit_scale_to_mm": unit_scale_to_mm,
            },
            "output": {
                "path": output_path.name,
                "sha256": _sha256(output_path),
                "format": "png",
            },
            "renderer_source": {
                "path": _portable_path(script_path, receipt_path),
                "sha256": script_hash,
            },
            "render": render_stats,
            "scene_derivation": scene_derivation,
            "scene_nodes": node_receipts,
            "scene_nodes_sha256": _canonical_sha256(node_receipts),
            "warnings": warnings,
            "evidence_class": recipe.evidence_class,
            "concept_art": False,
            "product_beauty_render": recipe.product_beauty_render,
            "physical_print": False,
            "printability_proof": False,
        }
        _write_json(receipt_path, receipt)
        results.append(
            {
                "view": key,
                "png": output_path.name,
                "png_sha256": _sha256(output_path),
                "receipt": receipt_path.name,
                "receipt_sha256": _sha256(receipt_path),
                "evidence_class": recipe.evidence_class,
                "product_beauty_render": recipe.product_beauty_render,
                "warnings": warnings,
            }
        )

    manifest_path = output_dir / "render-manifest.json"
    manifest: Mapping[str, object] = {
        "schema": "workshop.cad-preview-render-manifest.v2",
        "renderer": {"id": RENDERER_ID, "version": RENDERER_VERSION},
        "input": {
            "path": _portable_path(input_path, manifest_path),
            "sha256": input_hash,
        },
        "renderer_source_sha256": script_hash,
        "views": results,
        "concept_art": False,
        "physical_print": False,
    }
    _write_json(manifest_path, manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render deterministic, receipt-backed CAD previews from a colored "
            "cadgen native GLB. These images are not physical-print evidence."
        )
    )
    parser.add_argument("--input", required=True, type=Path, help="Colored native GLB")
    parser.add_argument("--out", required=True, type=Path, help="Output directory")
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--supersample", type=int, default=2, choices=(1, 2, 3))
    parser.add_argument(
        "--unit-scale-to-mm",
        type=float,
        default=1000.0,
        help="Native GLB coordinate scale to millimetres (cadgen native GLB: 1000)",
    )
    parser.add_argument(
        "--views",
        nargs="+",
        choices=tuple(VIEW_RECIPES),
        default=tuple(VIEW_RECIPES),
        help="Views to render; defaults to all frozen views",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.width < 64 or args.height < 64:
        parser.error("--width and --height must each be at least 64 pixels")
    if not math.isfinite(args.unit_scale_to_mm) or args.unit_scale_to_mm <= 0.0:
        parser.error("--unit-scale-to-mm must be a positive finite number")

    input_path = args.input.expanduser().resolve()
    output_dir = args.out.expanduser().resolve()
    if not input_path.is_file():
        print(
            f"render_product: input GLB not found: {input_path}\n"
            "Generate the colored native GLB with skills/cad/scripts/export first.",
            file=sys.stderr,
        )
        return 2

    try:
        manifest = render_product(
            input_path=input_path,
            output_dir=output_dir,
            view_keys=args.views,
            width=args.width,
            height=args.height,
            supersample=args.supersample,
            unit_scale_to_mm=args.unit_scale_to_mm,
        )
    except Exception as exc:  # noqa: BLE001 - concise CLI boundary
        print(f"render_product: failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
