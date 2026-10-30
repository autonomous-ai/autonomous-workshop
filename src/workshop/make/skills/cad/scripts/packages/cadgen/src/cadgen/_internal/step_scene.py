"""One import point for the STEP scene engine split across the ``step_scene_*`` modules.

Re-exports only the names the rest of cadgen imports from here; anything else is imported
from the submodule that defines it.
"""

from __future__ import annotations

from cadgen.selector_types import SelectorBundle, SelectorProfile
from cadgen._internal.step_hash import step_file_hash

from cadgen._internal.step_scene_cache import load_step_scene_cached
from cadgen._internal.step_scene_loader import _located_shape, load_step_scene, load_step_scene_from_xcaf_doc
from cadgen._internal.step_scene_mesh import adaptive_mesh_resolution_for_scene, adaptive_mesh_resolution_from_hints, import_step, mesh_step_scene, occurrence_selector_id, scene_occurrence_shape
from cadgen._internal.step_scene_selectors import extract_selectors_from_scene
from cadgen._internal.step_scene_types import ColorRGBA, LoadedStepScene, OccurrenceNode, SelectorOptions

__all__ = [
    "ColorRGBA",
    "LoadedStepScene",
    "OccurrenceNode",
    "SelectorBundle",
    "SelectorOptions",
    "SelectorProfile",
    "_located_shape",
    "adaptive_mesh_resolution_for_scene",
    "adaptive_mesh_resolution_from_hints",
    "extract_selectors_from_scene",
    "import_step",
    "load_step_scene",
    "load_step_scene_cached",
    "load_step_scene_from_xcaf_doc",
    "mesh_step_scene",
    "occurrence_selector_id",
    "scene_occurrence_shape",
    "step_file_hash",
]
