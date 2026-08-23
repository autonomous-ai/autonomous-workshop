from __future__ import annotations

import argparse
import contextlib
import io
import importlib.util
import json
import math
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Sequence

from cadpy.analysis import selector_manifest_diff
from cadpy.assembly_composition import (
    AssemblyCompositionError,
    build_linked_assembly_composition,
    build_native_assembly_composition,
    component_name,
)
from cadpy.assembly_spec import REPO_ROOT, assembly_spec_children, read_assembly_spec
from cadpy.assembly_spec import assembly_spec_from_payload
from cadpy.catalog import (
    CAD_ROOT,
    CadSource,
    STEP_SUFFIXES,
    StepImportOptions,
    cad_ref_from_step_path,
    find_source_by_path,
    iter_cad_sources,
    normalize_step_color,
    normalize_cad_ref,
    normalize_source_ref,
    source_from_path,
)
from cadpy.cli_logging import CliLogger
from cadpy.file_metadata import text_to_cad_identity_metadata, write_dxf_text_to_cad_metadata
from cadpy.glb import (
    build_step_topology_index_manifest,
    export_assembly_glb_from_scene,
    export_native_glb_from_scene,
    export_part_glb_from_scene,
)
from cadpy.glb import read_step_topology_manifest_from_glb
from cadpy.glb_topology import (
    STEP_EDGE_VISIBILITY_CLASSES,
    normalize_step_edge_render_visibility_classes,
)
from cadpy.generation_status import GenerationOutput, track_generation_run
from cadpy.metadata import (
    DEFAULT_MESH_ANGULAR_TOLERANCE,
    DEFAULT_MESH_TOLERANCE,
    GeneratorMetadata,
    resolve_mesh_settings,
)
from cadpy.render import (
    native_component_glb_dir,
    part_glb_path,
    relative_to_repo,
)
from cadpy.source_hash import PythonSourceHash, python_source_hash
from cadpy.stl import export_part_stl_from_scene, export_part_stls_from_scene
from cadpy.step_metadata import read_text_to_cad_step_metadata
from cadpy.threemf import export_part_3mf_from_scene
from cadpy.step_scene import (
    ColorRGBA,
    LoadedStepScene,
    SelectorBundle,
    SelectorOptions,
    SelectorProfile,
    adaptive_mesh_resolution_from_hints,
    adaptive_mesh_resolution_for_scene,
    extract_selectors_from_scene,
    load_step_scene,
    mesh_step_scene,
    occurrence_selector_id,
    scene_export_shape,
    scene_leaf_occurrences,
    step_file_hash,
)

GIT_LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"


@dataclass(frozen=True)
class EntrySpec:
    source_ref: str
    cad_ref: str
    kind: str
    source_path: Path
    display_name: str
    source: str
    step_path: Path | None = None
    script_path: Path | None = None
    generator_metadata: GeneratorMetadata | None = None
    dxf_path: Path | None = None
    urdf_path: Path | None = None
    stl_path: Path | None = None
    three_mf_path: Path | None = None
    native_glb_path: Path | None = None
    sdf_path: Path | None = None
    mesh_tolerance: float = DEFAULT_MESH_TOLERANCE
    mesh_angular_tolerance: float = DEFAULT_MESH_ANGULAR_TOLERANCE
    mesh_tolerance_explicit: bool = False
    mesh_angular_tolerance_explicit: bool = False
    color: tuple[float, float, float, float] | None = None


@dataclass
class GeneratedStepResult:
    spec: EntrySpec
    scene: LoadedStepScene | None
    selector_bundle: SelectorBundle | None = None


@dataclass(frozen=True)
class _CliTargetSpec:
    target: str
    output_path: Path | None = None


@dataclass
class _AssemblyArtifactContext:
    spec: EntrySpec
    scene: LoadedStepScene
    entries_by_step_path: dict[Path, EntrySpec]
    _occurrence_colors: dict[str, ColorRGBA] | None = None
    _composition: dict[str, object] | None = None
    _composition_resolved: bool = False

    def occurrence_colors(self) -> dict[str, ColorRGBA]:
        if self._occurrence_colors is None:
            self._occurrence_colors = _generated_assembly_source_occurrence_colors(
                self.spec,
                self.scene,
                entries_by_step_path=self.entries_by_step_path,
            )
        return self._occurrence_colors

    def composition_for_topology(self, topology_manifest: dict[str, object]) -> dict[str, object] | None:
        if not self._composition_resolved:
            self._composition = _assembly_composition_for_spec(
                self.spec,
                entries_by_step_path=self.entries_by_step_path,
                topology_manifest=topology_manifest,
                scene=self.scene,
            )
            self._composition_resolved = True
        return self._composition


class InlineStatusBoard:
    def __init__(self, labels: Sequence[str], *, initial_status: str, stream: object | None = None) -> None:
        self._stream = stream or sys.stdout
        self._is_tty = getattr(self._stream, "isatty", lambda: False)()
        self._labels = list(labels)
        self._statuses = {label: initial_status for label in self._labels}
        self._rendered_rows = 0
        if self._labels and self._is_tty:
            self._render()
        else:
            for label in self._labels:
                print(self._row(label), file=self._stream)

    def set(self, label: str, status: str) -> None:
        previous = self._statuses.get(label)
        if previous == status:
            return
        if label not in self._statuses:
            self._labels.append(label)
        self._statuses[label] = status
        if self._is_tty:
            self._render()
        else:
            print(self._row(label), file=self._stream)

    def _row(self, label: str) -> str:
        width = max(len(item) for item in self._labels)
        return f"{label:<{width}} : {self._statuses.get(label, '')}"

    def _render(self) -> None:
        if not self._labels:
            return
        rows = [self._row(label) for label in self._labels]
        if self._rendered_rows:
            print(f"\x1b[{self._rendered_rows}F", end="", file=self._stream)
        for row in rows:
            print(f"\x1b[2K{row}", file=self._stream)
        if self._rendered_rows > len(rows):
            for _ in range(self._rendered_rows - len(rows)):
                print("\x1b[2K", file=self._stream)
        self._rendered_rows = len(rows)
        self._stream.flush()


def _display_name_for_path(path: Path) -> str:
    return path.stem


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _resolve_cli_output_path(
    raw_output: str | Path | None,
    *,
    expected_suffixes: tuple[str, ...],
    tool_name: str,
    option_label: str = "--output",
) -> Path | None:
    if raw_output is None:
        return None
    value = str(raw_output).strip()
    if not value:
        raise ValueError(f"{tool_name} {option_label} must be a non-empty path")
    if "\\" in value:
        raise ValueError(f"{tool_name} {option_label} must use POSIX '/' separators")
    output_path = Path(value).expanduser()
    resolved = output_path.resolve() if output_path.is_absolute() else (Path.cwd() / output_path).resolve()
    if resolved.suffix.lower() not in expected_suffixes:
        joined = " or ".join(expected_suffixes)
        raise ValueError(f"{tool_name} {option_label} must end in {joined}")
    return resolved


def targets_include_output_pairs(targets: Sequence[str]) -> bool:
    return any("=" in str(target or "") for target in targets)


def _parse_cli_target_specs(
    targets: Sequence[str],
    *,
    expected_suffixes: tuple[str, ...],
    tool_name: str,
) -> list[_CliTargetSpec]:
    specs: list[_CliTargetSpec] = []
    for target in targets:
        target_text = str(target or "").strip()
        if "=" not in target_text:
            specs.append(_CliTargetSpec(target=target_text))
            continue
        raw_source, raw_output = target_text.split("=", 1)
        source = raw_source.strip()
        if not source:
            raise ValueError(f"{tool_name} output pair must use SOURCE=OUTPUT")
        output_path = _resolve_cli_output_path(
            raw_output,
            expected_suffixes=expected_suffixes,
            tool_name=tool_name,
            option_label="output pair",
        )
        if output_path is None:
            raise ValueError(f"{tool_name} output pair must use SOURCE=OUTPUT")
        specs.append(_CliTargetSpec(target=source, output_path=output_path))
    return specs


def _resolve_step_option_output_path(
    raw_output: str,
    *,
    base_step_path: Path,
    expected_suffixes: tuple[str, ...],
    field_name: str,
) -> Path:
    value = str(raw_output or "").strip()
    if not value:
        raise ValueError(f"{field_name} must be a non-empty path")
    if "\\" in value:
        raise ValueError(f"{field_name} must use POSIX '/' separators")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", "."} for part in pure.parts):
        raise ValueError(f"{field_name} must be relative")
    resolved = (base_step_path.resolve().parent / Path(*pure.parts)).resolve()
    if resolved.suffix.lower() not in expected_suffixes:
        joined = " or ".join(expected_suffixes)
        raise ValueError(f"{field_name} must end in {joined}")
    return resolved


def _apply_step_options_to_spec(spec: EntrySpec, step_options: StepImportOptions) -> EntrySpec:
    if not step_options.has_metadata or spec.step_path is None:
        return spec
    stl_path = spec.stl_path
    three_mf_path = spec.three_mf_path
    native_glb_path = spec.native_glb_path
    if step_options.stl is not None:
        stl_path = _resolve_step_option_output_path(
            step_options.stl,
            base_step_path=spec.step_path,
            expected_suffixes=(".stl",),
            field_name="stl",
        )
    if step_options.three_mf is not None:
        three_mf_path = _resolve_step_option_output_path(
            step_options.three_mf,
            base_step_path=spec.step_path,
            expected_suffixes=(".3mf",),
            field_name="3mf",
        )
    if step_options.glb is not None:
        native_glb_path = _resolve_step_option_output_path(
            step_options.glb,
            base_step_path=spec.step_path,
            expected_suffixes=(".glb",),
            field_name="glb",
        )
    return replace(
        spec,
        stl_path=stl_path,
        three_mf_path=three_mf_path,
        native_glb_path=native_glb_path,
        mesh_tolerance=step_options.mesh_tolerance if step_options.mesh_tolerance is not None else spec.mesh_tolerance,
        mesh_angular_tolerance=(
            step_options.mesh_angular_tolerance
            if step_options.mesh_angular_tolerance is not None
            else spec.mesh_angular_tolerance
        ),
        mesh_tolerance_explicit=spec.mesh_tolerance_explicit or step_options.mesh_tolerance is not None,
        mesh_angular_tolerance_explicit=(
            spec.mesh_angular_tolerance_explicit or step_options.mesh_angular_tolerance is not None
        ),
    )


def _spec_output_paths(spec: EntrySpec) -> tuple[Path, ...]:
    paths: list[Path] = []
    if spec.step_path is not None:
        paths.append(spec.step_path)
        paths.append(part_glb_path(spec.step_path))
    for path in (spec.dxf_path, spec.urdf_path, spec.sdf_path, spec.stl_path, spec.three_mf_path, spec.native_glb_path):
        if path is not None:
            paths.append(path)
    return tuple(path.resolve() for path in paths)


def _validate_cli_output_override(
    spec: EntrySpec,
    *,
    output_path: Path,
    all_specs: Sequence[EntrySpec],
    tool_name: str,
) -> None:
    resolved_output = output_path.resolve()
    for candidate in all_specs:
        if candidate.source_ref == spec.source_ref:
            continue
        if resolved_output in _spec_output_paths(candidate):
            raise ValueError(
                f"{tool_name} --output would overwrite another CAD output: "
                f"{_display_path(output_path)} belongs to {candidate.source_ref}"
            )


def _validate_duplicate_cli_output_overrides(
    output_paths: Sequence[Path | None],
    *,
    tool_name: str,
) -> None:
    seen: dict[Path, Path] = {}
    for output_path in output_paths:
        if output_path is None:
            continue
        resolved = output_path.resolve()
        previous = seen.get(resolved)
        if previous is not None:
            raise ValueError(f"{tool_name} output path is used more than once: {_display_path(output_path)}")
        seen[resolved] = output_path


def _apply_step_output_overrides(
    selected_specs: Sequence[EntrySpec],
    *,
    output_paths: Sequence[Path | None],
    all_specs: Sequence[EntrySpec],
    tool_name: str,
) -> list[EntrySpec]:
    if not any(output_path is not None for output_path in output_paths):
        return list(selected_specs)
    if len(output_paths) != len(selected_specs):
        raise ValueError(f"{tool_name} output override count must match target count")
    _validate_duplicate_cli_output_overrides(output_paths, tool_name=tool_name)
    updated_specs: list[EntrySpec] = []
    for spec, output_path in zip(selected_specs, output_paths, strict=True):
        if output_path is None:
            updated_specs.append(spec)
            continue
        if spec.source != "generated":
            raise ValueError(f"{tool_name} output pairs can only be used with generated Python targets")
        _validate_cli_output_override(spec, output_path=output_path, all_specs=all_specs, tool_name=tool_name)
        updated_specs.append(
            replace(
                spec,
                cad_ref=cad_ref_from_step_path(output_path),
                display_name=_display_name_for_path(output_path),
                step_path=output_path,
            )
        )
    return updated_specs


def _apply_step_output_override(
    selected_specs: Sequence[EntrySpec],
    *,
    output_path: Path | None,
    all_specs: Sequence[EntrySpec],
    tool_name: str,
) -> list[EntrySpec]:
    if output_path is None:
        return list(selected_specs)
    if len(selected_specs) != 1:
        raise ValueError(f"{tool_name} --output can only be used with exactly one target")
    spec = selected_specs[0]
    if spec.source != "generated":
        raise ValueError(f"{tool_name} --output can only be used with generated Python targets")
    return _apply_step_output_overrides(
        selected_specs,
        output_paths=[output_path],
        all_specs=all_specs,
        tool_name=tool_name,
    )


def _apply_dxf_output_overrides(
    selected_specs: Sequence[EntrySpec],
    *,
    output_paths: Sequence[Path | None],
    all_specs: Sequence[EntrySpec],
    tool_name: str,
) -> list[EntrySpec]:
    if not any(output_path is not None for output_path in output_paths):
        return list(selected_specs)
    if len(output_paths) != len(selected_specs):
        raise ValueError(f"{tool_name} output override count must match target count")
    _validate_duplicate_cli_output_overrides(output_paths, tool_name=tool_name)
    updated_specs: list[EntrySpec] = []
    for spec, output_path in zip(selected_specs, output_paths, strict=True):
        if output_path is None:
            updated_specs.append(spec)
            continue
        if spec.source != "generated":
            raise ValueError(f"{tool_name} output pairs can only be used with generated Python targets")
        _validate_cli_output_override(spec, output_path=output_path, all_specs=all_specs, tool_name=tool_name)
        updated_specs.append(replace(spec, dxf_path=output_path))
    return updated_specs


def _apply_dxf_output_override(
    selected_specs: Sequence[EntrySpec],
    *,
    output_path: Path | None,
    all_specs: Sequence[EntrySpec],
    tool_name: str,
) -> list[EntrySpec]:
    if output_path is None:
        return list(selected_specs)
    if len(selected_specs) != 1:
        raise ValueError(f"{tool_name} --output can only be used with exactly one target")
    spec = selected_specs[0]
    if spec.source != "generated":
        raise ValueError(f"{tool_name} --output can only be used with generated Python targets")
    return _apply_dxf_output_overrides(
        selected_specs,
        output_paths=[output_path],
        all_specs=all_specs,
        tool_name=tool_name,
    )


def _resolve_discovery_root(root: Path | str) -> Path:
    candidate = Path(root)
    resolved = candidate.resolve() if candidate.is_absolute() else (Path.cwd() / candidate).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"CAD discovery directory does not exist: {relative_to_repo(resolved)}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"CAD discovery path is not a directory: {relative_to_repo(resolved)}")
    return resolved


def list_entry_specs(root: Path | None = None, *, validate: bool = True) -> list[EntrySpec]:
    root = CAD_ROOT if root is None else root
    specs = [_entry_spec_from_source(source) for source in iter_cad_sources(_resolve_discovery_root(root))]
    if validate:
        _validate_part_render_output_paths(specs)
    return sorted(specs, key=lambda spec: spec.source_ref)


def _entry_spec_from_source(source: CadSource) -> EntrySpec:
    generator_metadata = source.generator_metadata
    script_path = source.script_path
    kind = source.kind
    step_path = source.step_path
    mesh_settings = resolve_mesh_settings(
        cad_ref=source.cad_ref,
        generator_metadata=generator_metadata,
        mesh_tolerance=source.mesh_tolerance,
        mesh_angular_tolerance=source.mesh_angular_tolerance,
    )
    display_path = step_path if step_path is not None else source.source_path
    urdf_path = source.urdf_path

    return EntrySpec(
        source_ref=source.source_ref,
        cad_ref=source.cad_ref,
        kind=kind,
        source_path=source.source_path,
        display_name=(
            generator_metadata.display_name
            if generator_metadata is not None and generator_metadata.display_name
            else _display_name_for_path(display_path)
        ),
        source=source.source,
        step_path=step_path,
        script_path=script_path,
        generator_metadata=generator_metadata,
        dxf_path=source.dxf_path,
        urdf_path=urdf_path,
        sdf_path=source.sdf_path,
        stl_path=source.stl_path,
        three_mf_path=source.three_mf_path,
        native_glb_path=source.native_glb_path,
        mesh_tolerance=mesh_settings.tolerance,
        mesh_angular_tolerance=mesh_settings.angular_tolerance,
        mesh_tolerance_explicit=source.mesh_tolerance is not None,
        mesh_angular_tolerance_explicit=source.mesh_angular_tolerance is not None,
        color=source.color,
    )


def _validate_part_render_output_paths(specs: Sequence[EntrySpec]) -> None:
    sources_by_stl_path: dict[Path, str] = {}
    sources_by_3mf_path: dict[Path, str] = {}
    sources_by_native_glb_path: dict[Path, str] = {}
    for spec in specs:
        if spec.kind not in {"part", "assembly"} or spec.step_path is None:
            continue
        if spec.stl_path is not None:
            stl_path = spec.stl_path.resolve()
            existing_source_ref = sources_by_stl_path.get(stl_path)
            if existing_source_ref is not None and existing_source_ref != spec.source_ref:
                raise ValueError(
                    "STL output collision between "
                    f"{existing_source_ref} and {spec.source_ref}: {_display_path(stl_path)}"
                )
            sources_by_stl_path[stl_path] = spec.source_ref
        if spec.three_mf_path is not None:
            three_mf_path = spec.three_mf_path.resolve()
            existing_source_ref = sources_by_3mf_path.get(three_mf_path)
            if existing_source_ref is not None and existing_source_ref != spec.source_ref:
                raise ValueError(
                    "3MF output collision between "
                    f"{existing_source_ref} and {spec.source_ref}: {_display_path(three_mf_path)}"
                )
            sources_by_3mf_path[three_mf_path] = spec.source_ref
        if spec.native_glb_path is not None:
            native_glb_path = spec.native_glb_path.resolve()
            topology_glb_path = part_glb_path(spec.step_path).resolve()
            if native_glb_path == topology_glb_path:
                raise ValueError(
                    "Native GLB output would overwrite the STEP topology GLB artifact for "
                    f"{spec.source_ref}: {_display_path(native_glb_path)}"
                )
            existing_source_ref = sources_by_native_glb_path.get(native_glb_path)
            if existing_source_ref is not None and existing_source_ref != spec.source_ref:
                raise ValueError(
                    "Native GLB output collision between "
                    f"{existing_source_ref} and {spec.source_ref}: {_display_path(native_glb_path)}"
                )
            sources_by_native_glb_path[native_glb_path] = spec.source_ref


def selected_entry_specs(all_specs: Sequence[EntrySpec], source_refs: Sequence[str]) -> list[EntrySpec]:
    if not source_refs:
        raise ValueError("At least one CAD target is required")
    by_source = {spec.source_ref: spec for spec in all_specs}
    by_cad_ref = {spec.cad_ref: spec for spec in all_specs}
    by_step_path = {
        spec.step_path.resolve(): spec
        for spec in all_specs
        if spec.step_path is not None
    }
    selected: list[EntrySpec] = []
    for source_ref in source_refs:
        spec = _spec_for_source_ref(source_ref, by_source=by_source, by_cad_ref=by_cad_ref, by_step_path=by_step_path)
        if spec is None:
            raise FileNotFoundError(f"CAD source not found: {source_ref}")
        selected.append(spec)
    return selected


def _spec_for_source_ref(
    raw_ref: str,
    *,
    by_source: dict[str, EntrySpec],
    by_cad_ref: dict[str, EntrySpec],
    by_step_path: dict[Path, EntrySpec],
) -> EntrySpec | None:
    source_ref = normalize_source_ref(raw_ref)
    if source_ref and source_ref in by_source:
        return by_source[source_ref]
    cad_ref = normalize_cad_ref(raw_ref)
    if cad_ref and cad_ref in by_cad_ref:
        return by_cad_ref[cad_ref]
    candidate = Path(str(raw_ref or "").strip())
    if candidate:
        resolved = candidate.resolve() if candidate.is_absolute() else (
            Path.cwd() / candidate
        )
        resolved = resolved.resolve()
        if resolved in by_step_path:
            return by_step_path[resolved]
        source = find_source_by_path(resolved)
        if source is not None:
            return by_source.get(source.source_ref)
    return None


def _mesh_tolerance_is_explicit(spec: EntrySpec) -> bool:
    return bool(spec.mesh_tolerance_explicit) or not math.isclose(
        float(spec.mesh_tolerance),
        float(DEFAULT_MESH_TOLERANCE),
        rel_tol=1e-12,
        abs_tol=1e-12,
    )


def _mesh_angular_tolerance_is_explicit(spec: EntrySpec) -> bool:
    return bool(spec.mesh_angular_tolerance_explicit) or not math.isclose(
        float(spec.mesh_angular_tolerance),
        float(DEFAULT_MESH_ANGULAR_TOLERANCE),
        rel_tol=1e-12,
        abs_tol=1e-12,
    )


def _selector_options_for_part(spec: EntrySpec, *, scene: LoadedStepScene | None = None) -> SelectorOptions:
    defaults = SelectorOptions()
    linear_deflection = spec.mesh_tolerance
    angular_deflection = spec.mesh_angular_tolerance
    resolution: dict[str, object] = {
        "mode": "explicit",
        "profile": "custom",
        "linearExplicit": True,
        "angularExplicit": True,
    }
    linear_explicit = _mesh_tolerance_is_explicit(spec)
    angular_explicit = _mesh_angular_tolerance_is_explicit(spec)
    edge_visibility_classes = normalize_step_edge_render_visibility_classes(None)
    if isinstance(scene, LoadedStepScene):
        adaptive = adaptive_mesh_resolution_for_scene(scene)
        if not linear_explicit:
            linear_deflection = adaptive.settings.tolerance
        if not angular_explicit:
            angular_deflection = adaptive.settings.angular_tolerance
        edge_visibility_classes = _edge_visibility_classes_for_resolution(adaptive.profile, adaptive.hints)
        resolution = {
            "mode": "auto",
            "profile": adaptive.profile,
            "linearExplicit": linear_explicit,
            "angularExplicit": angular_explicit,
            "hints": adaptive.hints,
        }
    return SelectorOptions(
        linear_deflection=linear_deflection,
        angular_deflection=angular_deflection,
        relative=defaults.relative,
        edge_deflection=defaults.edge_deflection,
        edge_deflection_ratio=defaults.edge_deflection_ratio,
        max_edge_points=defaults.max_edge_points,
        digits=defaults.digits,
        mesh_resolution=resolution,
        edge_visibility_classes=edge_visibility_classes,
    )


def _edge_visibility_classes_for_resolution(profile: str, hints: Mapping[str, object] | None) -> tuple[str, ...]:
    normalized_profile = str(profile or "").strip().lower()
    hint_values = hints if isinstance(hints, Mapping) else {}
    occurrence_edge_count = _hint_int(hint_values.get("occurrenceEdgeCount"))
    feature_only = (
        normalized_profile in {"large-topology", "coarse-assembly"}
        or occurrence_edge_count >= 8000
    )
    if feature_only:
        return (STEP_EDGE_VISIBILITY_CLASSES["FEATURE"],)
    return normalize_step_edge_render_visibility_classes(None)


def _hint_float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _hint_int(value: object) -> int:
    return int(_hint_float(value))


def _load_generator_module(script_path: Path) -> object:
    resolved_script_path = script_path.resolve()
    module_name = (
        "_cad_tool_"
        + _display_path(resolved_script_path).replace("/", "_").replace("\\", "_").replace("-", "_").replace(".", "_")
    )
    module_spec = importlib.util.spec_from_file_location(module_name, resolved_script_path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Failed to load generator module from {_display_path(resolved_script_path)}")

    module = importlib.util.module_from_spec(module_spec)
    original_sys_path = list(sys.path)
    search_paths = [
        str(REPO_ROOT),
        str(CAD_ROOT),
        str(REPO_ROOT / "skills" / "cad" / "scripts"),
        str(resolved_script_path.parent),
    ]
    for parent in resolved_script_path.parents:
        if parent == REPO_ROOT.parent:
            break
        if (
            (parent / "STEP" / "__init__.py").is_file()
            or (parent / "robot_common" / "__init__.py").is_file()
        ):
            search_paths.append(str(parent))
    for candidate in reversed(search_paths):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)

    try:
        sys.modules[module_name] = module
        module_spec.loader.exec_module(module)
    finally:
        sys.path[:] = original_sys_path

    return module


def _normalize_step_payload(
    result: object,
    *,
    script_path: Path,
) -> dict[str, object]:
    """Library-agnostic envelope normalization for `gen_step()` returns.

    See ``docs/panda-interfaces.md`` §1 ("Library-agnostic resolution") for
    the frozen contract. Resolution order:

    1. dict envelope — dispatch on the unique content key.
    2. list — treat as ``{"children": result}``.
    3. has callable ``.val()`` and ``.val().wrapped`` is a TopoDS_Shape →
       ``{"shape": result}`` (CadQuery Workplane).
    4. ``.wrapped`` is a TopoDS_Shape → ``{"shape": result}`` (CadQuery
       Shape, future OCP wrappers).
    5. ``cq.Assembly`` (``.children`` + ``.toCompound()``) →
       ``{"shape": result}``; downstream dispatch walks the tree.
    6. Otherwise raise TypeError.
    """
    # 1. dict envelope.
    if isinstance(result, dict):
        allowed_fields = {"shape", "instances", "children", "step_output", "stl", "3mf", "mesh_tolerance", "mesh_angular_tolerance", "warnings"}
        extra_fields = sorted(str(key) for key in result if key not in allowed_fields)
        if extra_fields:
            joined = ", ".join(extra_fields)
            raise TypeError(f"{_display_path(script_path)} gen_step() envelope has unsupported field(s): {joined}")
        content_fields = [key for key in ("shape", "instances", "children") if key in result]
        if len(content_fields) != 1:
            raise TypeError(
                f"{_display_path(script_path)} gen_step() envelope must define exactly one of "
                "'shape', 'instances', or 'children'"
            )
        # Preserve the content key plus any optional output-control keys
        # (stl, 3mf, mesh_tolerance, mesh_angular_tolerance, step_output).
        # The legacy ``generate_step_targets`` path ignores everything but
        # the content key — that behavior is preserved because that path
        # only dispatches on ``"shape" in envelope`` / ``"instances" in
        # envelope`` / ``"children" in envelope``. The high-level
        # :func:`generate_step` wrapper reads the optional keys.
        return {
            content_fields[0]: result[content_fields[0]],
            **{key: result[key] for key in ("stl", "3mf", "mesh_tolerance", "mesh_angular_tolerance", "step_output", "warnings") if key in result},
        }
    # 2. list → assembly children.
    if isinstance(result, list):
        return {"children": result}
    # 5. cq.Assembly (duck-typed: has both `.children` and `.toCompound()`).
    if _looks_like_cadquery_assembly(result):
        return {"shape": result}
    # 3. cq.Workplane (callable `.val()` returning something with `.wrapped`
    # that is a TopoDS_Shape).
    if _looks_like_topods_workplane(result):
        return {"shape": result}
    # 4. Any other wrapper around a TopoDS_Shape (cq.Shape, future OCP
    # wrappers).
    if _looks_like_topods_wrapper(result):
        return {"shape": result}
    raise TypeError(
        f"{_display_path(script_path)} gen_step() must return a "
        "cq.Workplane, cq.Shape, cq.Assembly, assembly list, or legacy envelope dict "
        f"(got {type(result).__name__})"
    )


def _is_topods_shape(obj: object) -> bool:
    try:
        from OCP.TopoDS import TopoDS_Shape
    except Exception:  # pragma: no cover — defensive
        return False
    return isinstance(obj, TopoDS_Shape)


def _looks_like_topods_wrapper(obj: object) -> bool:
    """True if `obj` has a ``.wrapped`` attribute that is a TopoDS_Shape."""
    wrapped = getattr(obj, "wrapped", None)
    return _is_topods_shape(wrapped)


def _looks_like_topods_workplane(obj: object) -> bool:
    """True if `obj` has a callable ``.val()`` whose result wraps a
    TopoDS_Shape (matches `cq.Workplane`).
    """
    val_fn = getattr(obj, "val", None)
    if not callable(val_fn):
        return False
    try:
        val = val_fn()
    except Exception:
        return False
    return _looks_like_topods_wrapper(val)


def _looks_like_cadquery_assembly(obj: object) -> bool:
    """True if `obj` looks like a `cq.Assembly` (has both ``.children`` and
    a callable ``.toCompound()``).
    """
    if not hasattr(obj, "children"):
        return False
    to_compound = getattr(obj, "toCompound", None)
    return callable(to_compound)


def _normalize_dxf_payload(result: object, *, script_path: Path) -> dict[str, object]:
    if isinstance(result, dict):
        allowed_fields = {"document", "dxf_output"}
        extra_fields = sorted(str(key) for key in result if key not in allowed_fields)
        if extra_fields:
            joined = ", ".join(extra_fields)
            raise TypeError(f"{_display_path(script_path)} gen_dxf() envelope has unsupported field(s): {joined}")
        if "document" not in result:
            raise TypeError(f"{_display_path(script_path)} gen_dxf() envelope must define 'document'")
        return {"document": result["document"]}
    return {"document": result}


def _shape_payload_entry_kind(shape: object, *, fallback: str) -> str:
    if fallback not in {"part", "assembly"}:
        raise RuntimeError(f"Unsupported generated STEP kind: {fallback}")
    if (
        fallback == "assembly"
        or _shape_has_explicit_children(shape)
        or _shape_is_multi_child_compound(shape)
    ):
        return "assembly"
    return "part"


def _shape_has_explicit_children(shape: object) -> bool:
    """True if `shape` is a wrapper with a non-empty ``.children`` iterable.

    Duck-typed: matches `cq.Assembly` (whose ``.children`` is a Python list)
    and any wrapper exposing a ``.children`` iterable. We exclude bare
    CadQuery `Workplane`/
    `Shape` because they don't expose this attribute.
    """
    try:
        children = getattr(shape, "children", None)
    except Exception:
        return False
    if children is None:
        return False
    try:
        return bool(tuple(children or ()))
    except TypeError:
        return False


def _shape_is_multi_child_compound(shape: object) -> bool:
    """True if `shape` wraps an OCCT compound that contains more than one
    direct child.

    Duck-typed on ``.wrapped`` so the rule applies to CadQuery shapes and
    any future OCP wrapper.
    """
    try:
        from OCP.TopAbs import TopAbs_COMPOUND
        from OCP.TopoDS import TopoDS_Iterator
    except Exception:
        return False
    wrapped = getattr(shape, "wrapped", None)
    # Reach through cq.Workplane: .val().wrapped is the actual TopoDS.
    if wrapped is None:
        val_fn = getattr(shape, "val", None)
        if callable(val_fn):
            try:
                val = val_fn()
            except Exception:
                return False
            wrapped = getattr(val, "wrapped", None)
    if not _is_topods_shape(wrapped):
        return False
    try:
        if wrapped.ShapeType() != TopAbs_COMPOUND:
            return False
    except Exception:
        return False
    iterator = TopoDS_Iterator(wrapped)
    count = 0
    while iterator.More():
        count += 1
        if count > 1:
            return True
        iterator.Next()
    return False


def _mark_scene_step_payload(
    scene: LoadedStepScene,
    *,
    entry_kind: str,
    payload_kind: str,
) -> LoadedStepScene:
    if isinstance(scene, LoadedStepScene):
        scene.text_to_cad_entry_kind = entry_kind
        scene.step_payload_kind = payload_kind
    return scene


def _scene_entry_kind(scene: LoadedStepScene | None) -> str | None:
    if scene is None:
        return None
    entry_kind = str(getattr(scene, "text_to_cad_entry_kind", "") or "").strip().lower()
    return entry_kind if entry_kind in {"part", "assembly"} else None


def _effective_step_spec_for_scene(spec: EntrySpec, scene: LoadedStepScene | None) -> EntrySpec:
    entry_kind = _scene_entry_kind(scene)
    if entry_kind is None or entry_kind == spec.kind:
        return spec
    return replace(spec, kind=entry_kind)


def _write_shape_step_payload(
    envelope: dict[str, object],
    *,
    output_path: Path,
    script_path: Path,
    logger: CliLogger,
    entry_kind: str,
    skip_step_write: bool = False,
) -> LoadedStepScene:
    shape = envelope.get("shape")

    # Dispatch on library by inspecting the input — duck-typed per
    # docs/panda-interfaces.md §1. The downstream OCCT/XCAF pipeline is
    # library-agnostic; we only need different "shape → XCAF doc" adapters.
    use_cadquery_path = (
        _looks_like_cadquery_assembly(shape)
        or _looks_like_topods_workplane(shape)
        or _looks_like_topods_wrapper(shape)
    )

    if not use_cadquery_path:
        raise TypeError(
            f"{_display_path(script_path)} gen_step() envelope field 'shape' must be a "
            "cq.Workplane, cq.Shape, or cq.Assembly; "
            f"got {type(shape).__name__}"
        )

    source_identity = python_source_hash(script_path)

    from cadpy.step_export_cadquery import (
        build_cadquery_step_scene,
        export_cadquery_step_scene,
    )

    if skip_step_write:
        scene = build_cadquery_step_scene(
            shape,
            output_path,
            source_kind="python",
            source_hash=source_identity.source_hash,
        )
        _mark_scene_python_backed(scene, source_identity=source_identity, source_path=script_path)
        _mark_scene_step_payload(scene, entry_kind=entry_kind, payload_kind="shape")
        logger.debug(f"built CadQuery STEP scene without writing STEP: {_display_path(output_path)}")
        return scene
    scene = export_cadquery_step_scene(
        shape,
        output_path,
        text_to_cad_entry_kind=entry_kind,
        source_path=relative_to_repo(script_path),
        source_fingerprint=source_identity.source_fingerprint,
        source_hash=source_identity.source_hash,
    )
    _mark_scene_python_backed(scene, source_identity=source_identity, source_path=script_path)
    _mark_scene_step_payload(scene, entry_kind=entry_kind, payload_kind="shape")
    logger.debug(f"wrote STEP (CadQuery): {_display_path(output_path)}")
    return scene


def _mark_scene_python_backed(
    scene: LoadedStepScene,
    *,
    source_identity: PythonSourceHash,
    source_path: Path,
) -> LoadedStepScene:
    if not isinstance(scene, LoadedStepScene):
        return scene
    scene.source_kind = "python"
    scene.source_hash = source_identity.source_hash
    scene.source_fingerprint = source_identity.source_fingerprint
    scene.source_path = relative_to_repo(source_path)
    return scene


def _write_assembly_step_payload(
    envelope: dict[str, object],
    *,
    output_path: Path,
    script_path: Path,
    logger: CliLogger,
    force: bool = False,
    load_current_scene: bool = True,
    skip_step_write: bool = False,
) -> LoadedStepScene | None:
    from .assembly_export import (
        _AssemblyCatalogResolver,
        build_direct_assembly_step_scene,
        export_assembly_step_scene,
    )

    if "instances" not in envelope and "children" not in envelope:
        raise TypeError(
            f"{_display_path(script_path)} gen_step() envelope must define 'instances' or 'children'"
        )
    payload = {key: envelope[key] for key in ("instances", "children") if key in envelope}
    assembly_spec = assembly_spec_from_payload(script_path, payload)
    resolver = _AssemblyCatalogResolver()
    source_identity = python_source_hash(script_path)
    if skip_step_write:
        with logger.timed(f"build assembly scene {relative_to_repo(output_path)}"):
            scene = build_direct_assembly_step_scene(
                assembly_spec,
                output_path=output_path,
                source_kind="python",
                source_hash=source_identity.source_hash,
                resolver=resolver,
                logger=logger,
            )
            _mark_scene_python_backed(scene, source_identity=source_identity, source_path=script_path)
            _mark_scene_step_payload(scene, entry_kind="assembly", payload_kind="assembly_spec")
            return scene
    if not force and output_path.is_file():
        try:
            metadata = read_text_to_cad_step_metadata(output_path)
        except Exception:
            metadata = {}
        if (
            metadata.get("entryKind") == "assembly"
            and metadata.get("sourceFingerprint") == source_identity.source_fingerprint
        ):
            logger.debug(f"reused current STEP: {_display_path(output_path)}")
            if not load_current_scene:
                return None
            scene = load_step_scene(output_path)
            _mark_scene_python_backed(scene, source_identity=source_identity, source_path=script_path)
            _mark_scene_step_payload(scene, entry_kind="assembly", payload_kind="assembly_spec")
            return scene

    with logger.timed(f"write assembly STEP {relative_to_repo(output_path)}"):
        scene = export_assembly_step_scene(
            assembly_spec,
            output_path=output_path,
            text_to_cad_entry_kind="assembly",
            source_path=relative_to_repo(script_path),
            source_fingerprint=source_identity.source_fingerprint,
            source_hash=source_identity.source_hash,
            resolver=resolver,
            logger=logger,
        )
    _mark_scene_python_backed(scene, source_identity=source_identity, source_path=script_path)
    _mark_scene_step_payload(scene, entry_kind="assembly", payload_kind="assembly_spec")
    return scene


def _write_dxf_payload(
    envelope: dict[str, object],
    *,
    output_path: Path,
    script_path: Path,
    logger: CliLogger,
) -> None:
    document = envelope.get("document")
    saveas = getattr(document, "saveas", None)
    if not callable(saveas):
        raise TypeError(
            f"{_display_path(script_path)} gen_dxf() envelope field 'document' must be a DXF document, "
            f"got {type(document).__name__}"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    saveas(str(output_path))
    source_identity = python_source_hash(script_path)
    write_dxf_text_to_cad_metadata(
        output_path,
        text_to_cad_identity_metadata(
            source_path=relative_to_repo(script_path),
            source_hash=source_identity.source_hash,
            source_fingerprint=source_identity.source_fingerprint,
        ),
    )
    logger.debug(f"wrote DXF: {_display_path(output_path)}")


def run_script_generator(
    spec: EntrySpec,
    generator_name: str,
    *,
    logger: CliLogger | None = None,
    force: bool = False,
    load_current_scene: bool = True,
    skip_step_write: bool = False,
) -> LoadedStepScene | None:
    logger = logger or CliLogger("cad")
    if generator_name not in {"gen_step", "gen_dxf"}:
        raise RuntimeError(f"Unsupported generator: {generator_name}")
    if spec.script_path is None or spec.generator_metadata is None:
        raise ValueError(f"{spec.source_ref} is not a generated Python CAD source")
    with _track_spec_generation(spec, generator_name):
        return _run_script_generator_inner(
            spec,
            generator_name,
            logger=logger,
            force=force,
            load_current_scene=load_current_scene,
            skip_step_write=skip_step_write,
        )


def _run_script_generator_inner(
    spec: EntrySpec,
    generator_name: str,
    *,
    logger: CliLogger,
    force: bool = False,
    load_current_scene: bool = True,
    skip_step_write: bool = False,
) -> LoadedStepScene | None:
    generated_scene: LoadedStepScene | None = None
    with logger.timed(f"load generator {spec.source_ref}"):
        module = _load_generator_module(spec.script_path)
    generator = getattr(module, generator_name, None)
    if not callable(generator):
        raise RuntimeError(f"{_display_path(spec.script_path)} does not define callable {generator_name}()")
    with logger.timed(f"run {generator_name} {spec.source_ref}"):
        raw_payload = generator()

    if generator_name == "gen_step":
        envelope = _normalize_step_payload(raw_payload, script_path=spec.script_path)
        if spec.step_path is None:
            raise RuntimeError(f"{spec.source_ref} has no configured STEP output")
        if "shape" in envelope:
            generated_scene = _write_shape_step_payload(
                envelope,
                output_path=spec.step_path,
                script_path=spec.script_path,
                logger=logger,
                entry_kind=_shape_payload_entry_kind(envelope.get("shape"), fallback=spec.kind),
                skip_step_write=skip_step_write,
            )
        elif "instances" in envelope or "children" in envelope:
            generated_scene = _write_assembly_step_payload(
                envelope,
                output_path=spec.step_path,
                script_path=spec.script_path,
                logger=logger,
                force=force,
                load_current_scene=load_current_scene,
                skip_step_write=skip_step_write,
            )
            logger.debug(
                f"ready STEP scene: {_display_path(spec.step_path)}"
                if skip_step_write
                else f"ready STEP: {_display_path(spec.step_path)}"
            )
        else:
            raise RuntimeError(f"{spec.source_ref} has unsupported generated kind: {spec.kind}")
    elif generator_name == "gen_dxf":
        envelope = _normalize_dxf_payload(raw_payload, script_path=spec.script_path)
        if spec.dxf_path is None:
            raise RuntimeError(f"{spec.source_ref} has no configured DXF output")
        _write_dxf_payload(envelope, output_path=spec.dxf_path, script_path=spec.script_path, logger=logger)
    if (
        generator_name == "gen_step"
        and spec.step_path is not None
        and not skip_step_write
        and not spec.step_path.exists()
    ):
        raise RuntimeError(
            f"{_display_path(spec.script_path)} did not write {_display_path(spec.step_path)}"
        )
    if generator_name == "gen_dxf" and spec.dxf_path is not None and not spec.dxf_path.exists():
        raise RuntimeError(
            f"{_display_path(spec.script_path)} did not write {_display_path(spec.dxf_path)}"
        )
    return generated_scene if generator_name == "gen_step" else None


def _is_git_lfs_pointer(step_path: Path) -> bool:
    try:
        with step_path.open("rb") as handle:
            return handle.read(len(GIT_LFS_POINTER_PREFIX)) == GIT_LFS_POINTER_PREFIX
    except OSError:
        return False


def _ensure_step_ready(step_path: Path) -> None:
    if not step_path.exists():
        raise FileNotFoundError(f"STEP file is missing: {_display_path(step_path)}")
    if _is_git_lfs_pointer(step_path):
        raise RuntimeError(
            f"{_display_path(step_path)} is a Git LFS pointer, not the real STEP file.\n"
            "Fetch Git LFS objects before generating CAD artifacts.\n"
            "For Vercel Git deployments, enable Git LFS in Project Settings > Git and redeploy."
        )


def _read_json_payload(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _report_selector_manifest_change(
    spec: EntrySpec,
    previous_manifest: dict[str, object] | None,
    next_manifest: dict[str, object],
    *,
    logger: CliLogger,
) -> None:
    change = selector_manifest_diff(previous_manifest, next_manifest)
    if not bool(change.get("hasPrevious")):
        return
    if bool(change.get("topologyChanged")):
        logger.warning(
            f"{spec.cad_ref} selector topology changed; re-resolve @cad refs before using old face or edge selectors."
        )
        return
    if bool(change.get("geometryChanged")):
        logger.info(
            f"notice: {spec.cad_ref} selector geometry changed; re-check cached geometry facts from older refs."
        )


def _assembly_composition_for_spec(
    spec: EntrySpec,
    *,
    entries_by_step_path: dict[Path, EntrySpec],
    topology_manifest: dict[str, object],
    scene: LoadedStepScene,
) -> dict[str, object] | None:
    if spec.kind != "assembly" or spec.step_path is None:
        return None
    if spec.source == "imported":
        return build_native_assembly_composition(
            cad_ref=spec.cad_ref,
            topology_path=part_glb_path(spec.step_path),
            topology_manifest=topology_manifest,
            mesh_path=part_glb_path(spec.step_path),
        )
    if spec.source == "generated" and getattr(scene, "step_payload_kind", None) == "shape":
        return build_native_assembly_composition(
            cad_ref=spec.cad_ref,
            topology_path=part_glb_path(spec.step_path),
            topology_manifest=topology_manifest,
            mesh_path=part_glb_path(spec.step_path),
        )
    if spec.source_path is None:
        return None
    assembly_spec = read_assembly_spec(spec.source_path)
    return build_linked_assembly_composition(
        cad_ref=spec.cad_ref,
        topology_path=part_glb_path(spec.step_path),
        topology_manifest=topology_manifest,
        assembly_spec=assembly_spec,
        entries_by_step_path=entries_by_step_path,
        read_assembly_spec=read_assembly_spec,
        mesh_path=part_glb_path(spec.step_path),
    )


def _script_step_material_colors(spec: EntrySpec) -> dict[str, ColorRGBA]:
    if spec.script_path is None:
        return {}
    try:
        module = _load_generator_module(spec.script_path)
    except Exception:
        return {}
    raw_materials = getattr(module, "URDF_MATERIALS", {})
    raw_step_materials = getattr(module, "URDF_STEP_MATERIALS", {})
    if not isinstance(raw_materials, Mapping) or not isinstance(raw_step_materials, Mapping):
        return {}
    colors: dict[str, ColorRGBA] = {}
    for raw_step_path, raw_material_name in raw_step_materials.items():
        if not isinstance(raw_step_path, str) or not isinstance(raw_material_name, str):
            continue
        raw_color = raw_materials.get(raw_material_name)
        try:
            color = normalize_step_color(raw_color, base_path=spec.source_path, field_name=f"URDF_MATERIALS.{raw_material_name}")
        except Exception:
            color = None
        if color is not None:
            colors[Path(raw_step_path).as_posix()] = color
    return colors


def _color_key(color: ColorRGBA) -> tuple[int, int, int, int]:
    return tuple(max(0, min(255, int(round(float(channel) * 255)))) for channel in color)


def _uniform_source_step_color(step_path: Path) -> ColorRGBA | None:
    try:
        scene = load_step_scene(step_path)
    except Exception:
        return None
    colors: list[ColorRGBA] = []
    colors.extend(tuple(float(value) for value in color) for color in scene.prototype_colors.values())
    for face_colors in scene.prototype_face_colors.values():
        colors.extend(tuple(float(value) for value in color) for color in face_colors.values())
    colors.extend(
        tuple(float(value) for value in node.color)
        for node in scene_leaf_occurrences(scene)
        if node.color is not None
    )
    by_key = {_color_key(color): color for color in colors}
    if len(by_key) == 1:
        return next(iter(by_key.values()))
    return None


def _uniform_scene_node_color(scene: LoadedStepScene, node: object | None) -> tuple[bool, ColorRGBA | None]:
    if node is None:
        return False, None
    colors_by_key: dict[tuple[int, int, int, int], ColorRGBA] = {}

    def add_color(raw_color: object) -> None:
        if raw_color is None:
            return
        try:
            color = tuple(float(value) for value in raw_color)
        except (TypeError, ValueError):
            return
        if len(color) != 4:
            return
        colors_by_key[_color_key(color)] = color

    def collect(current: object) -> None:
        add_color(getattr(current, "color", None))
        prototype_key = getattr(current, "prototype_key", None)
        if prototype_key is not None:
            add_color(scene.prototype_colors.get(int(prototype_key)))
            for face_color in scene.prototype_face_colors.get(int(prototype_key), {}).values():
                add_color(face_color)
        for child in getattr(current, "children", []) or []:
            collect(child)

    collect(node)
    if not colors_by_key:
        return False, None
    if len(colors_by_key) == 1:
        return True, next(iter(colors_by_key.values()))
    return True, None


def _generated_assembly_source_occurrence_colors(
    spec: EntrySpec,
    scene: LoadedStepScene,
    *,
    entries_by_step_path: dict[Path, EntrySpec],
) -> dict[str, ColorRGBA]:
    if spec.kind != "assembly" or spec.source != "generated" or spec.step_path is None or spec.source_path is None:
        return {}

    try:
        assembly_spec = read_assembly_spec(spec.source_path)
    except Exception:
        return {}

    step_root = spec.step_path.parent.resolve()
    script_step_colors = _script_step_material_colors(spec)
    source_color_cache: dict[Path, ColorRGBA | None] = {}
    occurrence_colors: dict[str, ColorRGBA] = {}

    def color_for_source(
        source_path: Path | None,
        *,
        use_source_colors: bool,
        scene_node: object | None,
    ) -> ColorRGBA | None:
        if not use_source_colors or source_path is None:
            return None
        resolved = Path(source_path).resolve()
        try:
            step_key = resolved.relative_to(step_root).as_posix()
        except ValueError:
            step_key = resolved.as_posix()
        material_color = script_step_colors.get(step_key)
        if material_color is not None:
            return material_color
        scene_has_colors, scene_color = _uniform_scene_node_color(scene, scene_node)
        if scene_has_colors:
            return scene_color
        if resolved not in source_color_cache:
            source_color_cache[resolved] = _uniform_source_step_color(resolved)
        return source_color_cache[resolved]

    def source_spec_for(source_path: Path | None) -> EntrySpec | None:
        if source_path is None:
            return None
        return entries_by_step_path.get(Path(source_path).resolve())

    def candidate_scene_roots() -> list[object]:
        roots = list(getattr(scene, "roots", []) or [])
        if len(roots) == 1 and getattr(roots[0], "prototype_key", None) is None and getattr(roots[0], "children", None):
            return list(roots[0].children)
        return roots

    def match_scene_node(candidates: Sequence[object], instance_path: tuple[str, ...], index: int) -> object | None:
        expected_name = component_name(instance_path)
        for candidate in candidates:
            if getattr(candidate, "name", None) == expected_name or getattr(candidate, "source_name", None) == expected_name:
                return candidate
        if 0 <= index < len(candidates):
            return candidates[index]
        return None

    def collect(
        spec_nodes: Sequence[object],
        scene_nodes: Sequence[object],
        *,
        instance_path: tuple[str, ...],
        parent_use_source_colors: bool,
        stack: tuple[str, ...],
    ) -> None:
        for index, node_spec in enumerate(spec_nodes):
            node_instance_id = str(getattr(node_spec, "instance_id", "") or getattr(node_spec, "name", "") or index + 1)
            node_path = (*instance_path, node_instance_id)
            scene_node = match_scene_node(scene_nodes, node_path, index)
            use_source_colors = parent_use_source_colors and bool(getattr(node_spec, "use_source_colors", True))
            node_children = tuple(getattr(node_spec, "children", ()) or ())
            child_scene_nodes = list(getattr(scene_node, "children", []) or []) if scene_node is not None else []
            if node_children:
                collect(
                    node_children,
                    child_scene_nodes,
                    instance_path=node_path,
                    parent_use_source_colors=use_source_colors,
                    stack=stack,
                )
                continue

            source_path = getattr(node_spec, "source_path", None)
            source_spec = source_spec_for(source_path)
            if source_spec is not None and source_spec.kind == "assembly" and source_spec.source_path is not None:
                stack_key = Path(source_spec.source_path).resolve().as_posix()
                if stack_key in stack:
                    continue
                try:
                    child_spec = read_assembly_spec(source_spec.source_path)
                except Exception:
                    child_spec = None
                if child_spec is not None:
                    collect(
                        assembly_spec_children(child_spec),
                        child_scene_nodes,
                        instance_path=node_path,
                        parent_use_source_colors=use_source_colors,
                        stack=(*stack, stack_key),
                    )
                    continue

            color = color_for_source(
                Path(source_path) if source_path is not None else None,
                use_source_colors=use_source_colors,
                scene_node=scene_node,
            )
            if color is not None and scene_node is not None:
                occurrence_colors[occurrence_selector_id(scene_node)] = color

    collect(
        assembly_spec_children(assembly_spec),
        candidate_scene_roots(),
        instance_path=(),
        parent_use_source_colors=True,
        stack=(assembly_spec.assembly_path.resolve().as_posix(),),
    )
    return occurrence_colors


@dataclass(frozen=True)
class _ArtifactJob:
    name: str
    run: Callable[[], object]


def _run_artifact_jobs(
    jobs: Sequence[_ArtifactJob],
    *,
    logger: CliLogger | None = None,
) -> dict[str, object]:
    results: dict[str, object] = {}
    for job in jobs:
        if logger is not None:
            with logger.timed(f"write {job.name}"):
                results[job.name] = job.run()
        else:
            results[job.name] = job.run()
    return results


def _mesh_values_match(
    mesh: Mapping[str, object],
    *,
    linear_deflection: float,
    angular_deflection: float,
    relative: bool,
) -> bool:
    try:
        artifact_linear = float(mesh.get("linearDeflection"))
        artifact_angular = float(mesh.get("angularDeflection"))
    except (TypeError, ValueError):
        return False
    return (
        math.isclose(artifact_linear, float(linear_deflection), rel_tol=1e-9, abs_tol=1e-12)
        and math.isclose(artifact_angular, float(angular_deflection), rel_tol=1e-9, abs_tol=1e-12)
        and bool(mesh.get("relative", True)) == bool(relative)
    )


def _selector_options_from_topology_manifest(spec: EntrySpec, manifest: Mapping[str, object]) -> SelectorOptions | None:
    mesh = manifest.get("mesh")
    if not isinstance(mesh, Mapping):
        return None

    defaults = SelectorOptions()
    linear_explicit = _mesh_tolerance_is_explicit(spec)
    angular_explicit = _mesh_angular_tolerance_is_explicit(spec)
    linear_deflection = spec.mesh_tolerance
    angular_deflection = spec.mesh_angular_tolerance

    if not linear_explicit or not angular_explicit:
        resolution = mesh.get("resolution")
        hints = resolution.get("hints") if isinstance(resolution, Mapping) else None
        if not isinstance(hints, dict):
            return None
        adaptive = adaptive_mesh_resolution_from_hints(hints)
        if not linear_explicit:
            linear_deflection = adaptive.settings.tolerance
        if not angular_explicit:
            angular_deflection = adaptive.settings.angular_tolerance

    return SelectorOptions(
        linear_deflection=linear_deflection,
        angular_deflection=angular_deflection,
        relative=bool(mesh.get("relative", defaults.relative)),
        edge_deflection=defaults.edge_deflection,
        edge_deflection_ratio=defaults.edge_deflection_ratio,
        max_edge_points=defaults.max_edge_points,
        digits=defaults.digits,
        mesh_resolution=mesh.get("resolution") if isinstance(mesh.get("resolution"), dict) else None,
        edge_visibility_classes=_edge_visibility_classes_from_topology_manifest(manifest),
    )


def _edge_visibility_classes_from_topology_manifest(manifest: Mapping[str, object]) -> tuple[str, ...]:
    edge_rendering = manifest.get("edgeRendering")
    if isinstance(edge_rendering, Mapping):
        classes = edge_rendering.get("visibilityClasses")
        if classes is not None:
            return normalize_step_edge_render_visibility_classes(classes)
    mesh = manifest.get("mesh")
    resolution = mesh.get("resolution") if isinstance(mesh, Mapping) else None
    hints = resolution.get("hints") if isinstance(resolution, Mapping) else None
    profile = resolution.get("profile") if isinstance(resolution, Mapping) else ""
    if isinstance(hints, Mapping):
        return _edge_visibility_classes_for_resolution(str(profile or ""), hints)
    return normalize_step_edge_render_visibility_classes(None)


def _edge_visibility_classes_match_manifest(
    manifest: Mapping[str, object],
    selector_options: SelectorOptions,
) -> bool:
    edge_rendering = manifest.get("edgeRendering")
    if not isinstance(edge_rendering, Mapping):
        return False
    return tuple(edge_rendering.get("visibilityClasses") or ()) == tuple(selector_options.edge_visibility_classes)


def _artifact_source_kind_matches_spec(spec: EntrySpec, manifest: Mapping[str, object]) -> bool:
    source_kind = str(manifest.get("sourceKind") or "step").strip().lower()
    expected = "python" if spec.source == "generated" and spec.script_path is not None else "step"
    return source_kind == expected


def _artifact_source_identity_matches_spec(spec: EntrySpec, manifest: Mapping[str, object]) -> bool:
    if spec.source == "generated" and spec.script_path is not None:
        expected = python_source_hash(spec.script_path)
        artifact_fingerprint = str(manifest.get("sourceFingerprint") or "").strip()
        return artifact_fingerprint == expected.source_fingerprint
    if spec.step_path is None or not spec.step_path.is_file():
        return False
    expected_hash = step_file_hash(spec.step_path)
    return str(manifest.get("stepHash") or "").strip() == expected_hash


def _existing_topology_artifact_matches_spec_without_scene(
    spec: EntrySpec,
    *,
    require_selector: bool = True,
) -> bool:
    if spec.step_path is None or spec.kind not in {"part", "assembly"}:
        return False
    from cadpy.step_targets import (
        ResolvedStepTarget,
        StepTopologyArtifactError,
        validate_step_topology_artifact,
    )

    try:
        artifact = validate_step_topology_artifact(
            ResolvedStepTarget(
                cad_path=spec.cad_ref,
                kind=spec.kind,
                source_path=spec.source_path,
                step_path=spec.step_path,
            ),
            glb_path=part_glb_path(spec.step_path),
            require_selector=require_selector,
        )
    except StepTopologyArtifactError:
        return False
    if not _artifact_source_kind_matches_spec(spec, artifact.manifest):
        return False
    if not _artifact_source_identity_matches_spec(spec, artifact.manifest):
        return False
    mesh = artifact.manifest.get("mesh")
    if not isinstance(mesh, Mapping):
        return False
    selector_options = _selector_options_from_topology_manifest(spec, artifact.manifest)
    if selector_options is None:
        return False
    return (
        _mesh_values_match(
            mesh,
            linear_deflection=selector_options.linear_deflection,
            angular_deflection=selector_options.angular_deflection,
            relative=selector_options.relative,
        )
        and _edge_visibility_classes_match_manifest(artifact.manifest, selector_options)
    )


def _existing_topology_artifact_matches_options(spec: EntrySpec, selector_options: SelectorOptions) -> bool:
    if spec.step_path is None or spec.kind not in {"part", "assembly"}:
        return False
    from cadpy.step_targets import (
        ResolvedStepTarget,
        StepTopologyArtifactError,
        validate_step_topology_artifact,
    )

    try:
        artifact = validate_step_topology_artifact(
            ResolvedStepTarget(
                cad_path=spec.cad_ref,
                kind=spec.kind,
                source_path=spec.source_path,
                step_path=spec.step_path,
            ),
            glb_path=part_glb_path(spec.step_path),
            require_selector=False,
        )
    except StepTopologyArtifactError:
        return False
    if not _artifact_source_kind_matches_spec(spec, artifact.manifest):
        return False
    if not _artifact_source_identity_matches_spec(spec, artifact.manifest):
        return False
    mesh = artifact.manifest.get("mesh")
    if not isinstance(mesh, Mapping):
        return False
    return (
        _mesh_values_match(
            mesh,
            linear_deflection=selector_options.linear_deflection,
            angular_deflection=selector_options.angular_deflection,
            relative=selector_options.relative,
        )
        and _edge_visibility_classes_match_manifest(artifact.manifest, selector_options)
    )


def _reset_step_artifact_dir(step_path: Path) -> None:
    part_glb_path(step_path).unlink(missing_ok=True)
    legacy_artifact_dir = native_component_glb_dir(step_path).parent
    if legacy_artifact_dir.is_dir():
        shutil.rmtree(legacy_artifact_dir)


def _generate_part_outputs(
    spec: EntrySpec,
    *,
    entries_by_step_path: dict[Path, EntrySpec],
    preloaded_scene: LoadedStepScene | None = None,
    require_step_file: bool = True,
    force: bool = False,
    logger: CliLogger | None = None,
) -> GeneratedStepResult:
    logger = logger or CliLogger("cad")
    if spec.kind not in {"part", "assembly"} or spec.step_path is None:
        return GeneratedStepResult(spec=spec, scene=None)
    if require_step_file:
        _ensure_step_ready(spec.step_path)
    if preloaded_scene is not None:
        if preloaded_scene.step_path != spec.step_path.expanduser().resolve():
            raise RuntimeError(
                f"Preloaded STEP scene path {preloaded_scene.step_path} does not match {_display_path(spec.step_path)}"
            )

    has_mesh_sidecars = any(
        path is not None
        for path in (spec.stl_path, spec.three_mf_path, spec.native_glb_path)
    )
    if (
        preloaded_scene is None
        and not has_mesh_sidecars
        and not force
        and _existing_topology_artifact_matches_spec_without_scene(spec)
    ):
        logger.debug(f"reused current GLB/topology: {_display_path(part_glb_path(spec.step_path))}")
        return GeneratedStepResult(spec=spec, scene=None)

    if preloaded_scene is not None:
        scene = preloaded_scene
    else:
        with logger.timed(f"load STEP {spec.cad_ref}"):
            scene = load_step_scene(spec.step_path)
        if spec.source == "generated" and spec.script_path is not None:
            _mark_scene_python_backed(
                scene,
                source_identity=python_source_hash(spec.script_path),
                source_path=spec.script_path,
            )
    spec = _effective_step_spec_for_scene(spec, scene)
    entries_by_step_path = {
        **entries_by_step_path,
        spec.step_path.resolve(): spec,
    }
    selector_options = _selector_options_for_part(spec, scene=scene)
    if (
        not has_mesh_sidecars
        and not force
        and _existing_topology_artifact_matches_options(spec, selector_options)
    ):
        logger.debug(f"reused current GLB/topology: {_display_path(part_glb_path(spec.step_path))}")
        return GeneratedStepResult(spec=spec, scene=scene)

    glb_path = part_glb_path(spec.step_path)
    previous_manifest: dict[str, object] | None = read_step_topology_manifest_from_glb(glb_path) if glb_path.exists() else None

    with logger.timed(f"mesh STEP {spec.cad_ref}"):
        mesh_step_scene(
            scene,
            linear_deflection=selector_options.linear_deflection,
            angular_deflection=selector_options.angular_deflection,
            relative=selector_options.relative,
        )
        scene_export_shape(scene)
    _reset_step_artifact_dir(spec.step_path)
    assembly_context = (
        _AssemblyArtifactContext(spec=spec, scene=scene, entries_by_step_path=entries_by_step_path)
        if spec.kind == "assembly"
        else None
    )

    jobs: list[_ArtifactJob] = []

    def export_glb(selector_bundle: SelectorBundle | None = None) -> Path:
        if spec.kind == "assembly":
            occurrence_colors = assembly_context.occurrence_colors() if assembly_context is not None else None
            exported_glb_path = export_assembly_glb_from_scene(
                spec.step_path,
                scene,
                linear_deflection=selector_options.linear_deflection,
                angular_deflection=selector_options.angular_deflection,
                color=spec.color,
                occurrence_colors=occurrence_colors,
                selector_bundle=selector_bundle,
                include_selector_topology=selector_bundle is not None,
            )
            stale_components_dir = native_component_glb_dir(spec.step_path)
            if stale_components_dir.is_dir():
                shutil.rmtree(stale_components_dir)
            return exported_glb_path
        return export_part_glb_from_scene(
            spec.step_path,
            scene,
            linear_deflection=selector_options.linear_deflection,
            angular_deflection=selector_options.angular_deflection,
            color=spec.color,
            selector_bundle=selector_bundle,
            include_selector_topology=selector_bundle is not None,
        )

    artifact_results: dict[str, object] = {}

    if spec.stl_path is not None:
        def stl_sidecar_job() -> Path:
            return export_part_stl_from_scene(spec.step_path, scene, target_path=spec.stl_path)

        jobs.append(_ArtifactJob("STL", stl_sidecar_job))

    if spec.three_mf_path is not None:
        def three_mf_sidecar_job() -> Path:
            kwargs: dict[str, object] = {
                "target_path": spec.three_mf_path,
                "color": spec.color,
            }
            if assembly_context is not None:
                kwargs["occurrence_colors"] = assembly_context.occurrence_colors()
            return export_part_3mf_from_scene(spec.step_path, scene, **kwargs)

        jobs.append(_ArtifactJob("3MF", three_mf_sidecar_job))

    if spec.native_glb_path is not None:
        def native_glb_sidecar_job() -> Path:
            kwargs: dict[str, object] = {
                "target_path": spec.native_glb_path,
                "linear_deflection": selector_options.linear_deflection,
                "angular_deflection": selector_options.angular_deflection,
                "color": spec.color,
            }
            if assembly_context is not None:
                kwargs["occurrence_colors"] = assembly_context.occurrence_colors()
            return export_native_glb_from_scene(spec.step_path, scene, **kwargs)

        jobs.append(_ArtifactJob("native GLB", native_glb_sidecar_job))

    def export_glb_with_topology() -> SelectorBundle:
        occurrence_colors = assembly_context.occurrence_colors() if assembly_context is not None else {}
        bundle = extract_selectors_from_scene(
            scene,
            cad_ref=spec.cad_ref,
            profile=SelectorProfile.ARTIFACT,
            options=selector_options,
            color=spec.color,
            occurrence_colors=occurrence_colors,
        )
        assembly_composition: dict[str, object] | None = None
        if assembly_context is not None:
            try:
                assembly_composition = assembly_context.composition_for_topology(bundle.manifest)
            except AssemblyCompositionError:
                raise
            except Exception as exc:
                raise RuntimeError(f"Failed to build assembly composition for {spec.source_ref}") from exc
            if assembly_composition is not None:
                bundle.manifest["assembly"] = assembly_composition
        next_manifest = build_step_topology_index_manifest(bundle.manifest, entry_kind=spec.kind)
        export_glb(bundle)
        _report_selector_manifest_change(spec, previous_manifest, next_manifest, logger=logger)
        return bundle

    jobs.append(_ArtifactJob("GLB/topology", export_glb_with_topology))

    artifact_results.update(_run_artifact_jobs(jobs, logger=logger))
    selector_bundle = next(
        (result for result in artifact_results.values() if isinstance(result, SelectorBundle)),
        None,
    )
    return GeneratedStepResult(spec=spec, scene=scene, selector_bundle=selector_bundle)


def _generate_step_outputs(
    spec: EntrySpec,
    *,
    entries_by_step_path: dict[Path, EntrySpec],
    skip_step_write: bool = False,
    force: bool = False,
    logger: CliLogger | None = None,
) -> GeneratedStepResult:
    preloaded_scene: LoadedStepScene | None = None
    has_mesh_sidecars = any(
        path is not None
        for path in (spec.stl_path, spec.three_mf_path, spec.native_glb_path)
    )
    if (
        spec.source == "generated"
        and skip_step_write
        and not force
        and not has_mesh_sidecars
        and _existing_topology_artifact_matches_spec_without_scene(spec)
    ):
        if logger is not None:
            logger.debug(f"reused current GLB/topology: {_display_path(part_glb_path(spec.step_path))}")
        return GeneratedStepResult(spec=spec, scene=None)
    if spec.source == "generated":
        preloaded_scene = run_script_generator(
            spec,
            "gen_step",
            logger=logger,
            force=force,
            load_current_scene=False,
            skip_step_write=skip_step_write,
        )
        spec = _effective_step_spec_for_scene(spec, preloaded_scene)
        if spec.step_path is not None:
            entries_by_step_path = {
                **entries_by_step_path,
                spec.step_path.resolve(): spec,
            }
        output_kwargs: dict[str, object] = {
            "entries_by_step_path": entries_by_step_path,
            "preloaded_scene": preloaded_scene,
            "force": force,
        }
        if skip_step_write:
            output_kwargs["require_step_file"] = False
        if logger is not None:
            output_kwargs["logger"] = logger
        return _generate_part_outputs(spec, **output_kwargs)


def _generate_step_outputs_for_cli(
    spec: EntrySpec,
    *,
    entries_by_step_path: dict[Path, EntrySpec],
    logger: CliLogger,
    skip_step_write: bool = False,
    force: bool = False,
) -> GeneratedStepResult:
    kwargs: dict[str, object] = {
        "entries_by_step_path": entries_by_step_path,
    }
    if skip_step_write:
        kwargs["skip_step_write"] = True
    if force:
        kwargs["force"] = True
    if logger.verbose:
        kwargs["logger"] = logger
    return _generate_step_outputs(spec, **kwargs)


def _selected_specs_for_targets(
    targets: Sequence[str],
    *,
    direct_step_kind: str = "part",
    step_options: StepImportOptions | None = None,
    expected_output_suffixes: tuple[str, ...] | None = None,
    tool_name: str = "CAD",
    include_output_paths: bool = False,
) -> tuple[list[EntrySpec], list[EntrySpec]] | tuple[list[EntrySpec], list[EntrySpec], list[Path | None]]:
    step_options = step_options or StepImportOptions()
    target_specs = (
        _parse_cli_target_specs(
            targets,
            expected_suffixes=expected_output_suffixes,
            tool_name=tool_name,
        )
        if expected_output_suffixes is not None
        else [_CliTargetSpec(target=str(target or "").strip()) for target in targets]
    )
    explicit_specs: list[EntrySpec] = []
    output_paths: list[Path | None] = []
    unresolved_targets: list[str] = []
    for target_spec in target_specs:
        target_text = target_spec.target
        target_path = Path(target_text)
        resolved = target_path.resolve() if target_path.is_absolute() else (Path.cwd() / target_path).resolve()
        source = (
            source_from_path(
                resolved,
                step_kind=direct_step_kind,
                step_options=step_options,
            )
            if resolved.exists()
            else None
        )
        if source is None:
            unresolved_targets.append(target_text)
            continue
        explicit_specs.append(_apply_step_options_to_spec(_entry_spec_from_source(source), step_options))
        output_paths.append(target_spec.output_path)

    if not unresolved_targets:
        expanded_specs = _expand_specs_with_file_dependencies(explicit_specs)
        if include_output_paths:
            return expanded_specs, explicit_specs, output_paths
        return expanded_specs, explicit_specs

    unresolved = ", ".join(unresolved_targets)
    raise FileNotFoundError(
        "CAD target path not found or not a supported source file: "
        f"{unresolved}. Pass a Python generator or STEP/STP file path."
    )


def _expand_specs_with_file_dependencies(specs: Sequence[EntrySpec]) -> list[EntrySpec]:
    expanded: list[EntrySpec] = list(specs)
    seen_step_paths = {
        spec.step_path.resolve()
        for spec in expanded
        if spec.step_path is not None
    }
    seen_source_refs = {spec.source_ref for spec in expanded}
    queue = list(expanded)
    source_cache: dict[Path, CadSource | None] = {}
    discovered_sources_by_path: dict[Path, CadSource] | None = None

    def source_for_path(path: Path) -> CadSource | None:
        nonlocal discovered_sources_by_path
        resolved = path.resolve()
        if resolved in source_cache:
            return source_cache[resolved]
        if discovered_sources_by_path is None:
            discovered_sources_by_path = _source_lookup_by_path()
        source = discovered_sources_by_path.get(resolved)
        if source is None:
            source = source_from_path(resolved)
        source_cache[resolved] = source
        return source

    while queue:
        spec = queue.pop(0)
        if spec.kind != "assembly" or spec.source_path is None:
            continue
        try:
            assembly_spec = read_assembly_spec(spec.source_path)
        except Exception:
            continue
        for instance in assembly_spec_children(assembly_spec):
            if instance.source_path.resolve() in seen_step_paths:
                continue
            source = source_for_path(instance.source_path)
            if source is None:
                continue
            child_spec = _entry_spec_from_source(source)
            if child_spec.source_ref in seen_source_refs:
                continue
            expanded.append(child_spec)
            queue.append(child_spec)
            seen_source_refs.add(child_spec.source_ref)
            if child_spec.step_path is not None:
                seen_step_paths.add(child_spec.step_path.resolve())
    return expanded


def _source_lookup_by_path() -> dict[Path, CadSource]:
    sources_by_path: dict[Path, CadSource] = {}
    for source in iter_cad_sources():
        candidates = [
            source.source_path,
            source.origin_path,
            source.script_path,
            source.step_path,
            source.dxf_path,
            source.urdf_path,
            source.sdf_path,
            source.stl_path,
            source.three_mf_path,
            source.native_glb_path,
            *source.generated_paths,
        ]
        for candidate in candidates:
            if candidate is not None:
                sources_by_path.setdefault(candidate.resolve(), source)
    return sources_by_path


def _entries_by_step_path(specs: Sequence[EntrySpec]) -> dict[Path, EntrySpec]:
    return {
        spec.step_path.resolve(): spec
        for spec in specs
        if spec.step_path is not None
    }


def _refreshed_selected_specs(selected_specs: Sequence[EntrySpec]) -> list[EntrySpec]:
    refreshed: list[EntrySpec] = []
    for spec in selected_specs:
        if spec.source == "imported":
            refreshed.append(spec)
            continue
        source_path = spec.script_path or spec.source_path
        source = source_from_path(source_path) if source_path is not None and source_path.exists() else None
        refreshed.append(_entry_spec_from_source(source) if source is not None else spec)
    return refreshed


def _validate_step_target(
    spec: EntrySpec,
    *,
    direct_step_kind: str | None,
    tool_name: str,
) -> None:
    if spec.step_path is None:
        raise ValueError(f"{tool_name} target has no STEP path: {spec.source_ref}")
    if spec.source == "generated":
        metadata = spec.generator_metadata
        if metadata is None or not metadata.has_gen_step:
            raise ValueError(f"{tool_name} target does not define gen_step(): {spec.source_ref}")
        return
    if direct_step_kind is None:
        raise ValueError(f"{tool_name} --kind is required for direct STEP/STP targets: {spec.source_ref}")


def _existing_direct_step_targets(targets: Sequence[str]) -> list[str]:
    direct_targets: list[str] = []
    for target in targets:
        target_text = str(target or "").strip()
        if "=" in target_text:
            target_text = target_text.split("=", 1)[0].strip()
        target_path = Path(target_text)
        resolved = target_path.resolve() if target_path.is_absolute() else (Path.cwd() / target_path).resolve()
        if resolved.exists() and resolved.suffix.lower() in STEP_SUFFIXES:
            direct_targets.append(target_text)
    return direct_targets


def _validate_dxf_target(spec: EntrySpec) -> None:
    metadata = spec.generator_metadata
    if spec.source != "generated" or spec.script_path is None or metadata is None:
        raise ValueError(f"dxf expected a generated Python source target: {spec.source_ref}")
    if not metadata.has_gen_dxf:
        raise ValueError(f"dxf target does not define gen_dxf(): {spec.source_ref}")
    if spec.dxf_path is None:
        raise ValueError(f"dxf target has no configured DXF output: {spec.source_ref}")


def _generated_output_summary(spec: EntrySpec) -> str:
    if spec.step_path is not None:
        return f"generated {spec.kind} STEP: {_display_path(spec.step_path)}"
    return f"processed: {spec.source_ref}"


def _generated_python_glb_summary(spec: EntrySpec) -> str:
    if spec.step_path is not None:
        return f"generated {spec.kind} GLB/topology artifact: {_display_path(part_glb_path(spec.step_path))}"
    return f"processed: {spec.source_ref}"


def _generated_dxf_summary(spec: EntrySpec) -> str:
    if spec.dxf_path is not None:
        return f"generated DXF: {_display_path(spec.dxf_path)}"
    return f"processed: {spec.source_ref}"


def _generation_outputs_for_spec(spec: EntrySpec, generator_name: str) -> tuple[GenerationOutput, ...]:
    outputs: list[GenerationOutput] = []
    if generator_name == "gen_step" and spec.step_path is not None:
        outputs.append(GenerationOutput(spec.step_path, "step"))
        outputs.append(GenerationOutput(part_glb_path(spec.step_path), "glb"))
        if spec.stl_path is not None:
            outputs.append(GenerationOutput(spec.stl_path, "stl"))
        if spec.three_mf_path is not None:
            outputs.append(GenerationOutput(spec.three_mf_path, "3mf"))
        if spec.native_glb_path is not None:
            outputs.append(GenerationOutput(spec.native_glb_path, "glb"))
    elif generator_name == "gen_dxf" and spec.dxf_path is not None:
        outputs.append(GenerationOutput(spec.dxf_path, "dxf"))
    return tuple(outputs)


def _track_spec_generation(spec: EntrySpec, generator_name: str) -> contextlib.AbstractContextManager[None]:
    return track_generation_run(
        source_path=spec.script_path or spec.source_path,
        generator=generator_name,
        outputs=_generation_outputs_for_spec(spec, generator_name),
        repo_root=REPO_ROOT,
    )


def _run_with_spec_generation_status(
    spec: EntrySpec,
    generator_name: str,
    action: Callable[[EntrySpec], object],
) -> object:
    with _track_spec_generation(spec, generator_name):
        return action(spec)


def _run_selected_specs(
    selected_specs: Sequence[EntrySpec],
    *,
    initial_status: str = "Queued",
    action_status: str = "Generating...",
    done_status: str = "Generated",
    action: Callable[[EntrySpec], object],
    quiet: bool = False,
    status_stream: object | None = None,
    action_stdout: object | None = None,
    logger: CliLogger | None = None,
    success_message: Callable[[EntrySpec], str] | None = _generated_output_summary,
) -> list[object]:
    results: list[object] = []
    if quiet:
        for spec in selected_specs:
            with contextlib.redirect_stdout(io.StringIO()):
                results.append(action(spec))
        return results
    if logger is not None:
        for spec in selected_specs:
            logger.debug(f"{action_status} {spec.source_ref}")
            stdout_target = (
                (action_stdout if action_stdout is not None else logger.stream)
                if logger.verbose
                else io.StringIO()
            )
            with logger.timed(f"{done_status.lower()} {spec.source_ref}"):
                if stdout_target is None:
                    result = action(spec)
                else:
                    with contextlib.redirect_stdout(stdout_target):
                        result = action(spec)
            results.append(result)
            if success_message is not None:
                message_spec = result.spec if isinstance(result, GeneratedStepResult) else spec
                logger.info(success_message(message_spec))
        return results
    status_board = InlineStatusBoard(
        [spec.source_ref for spec in selected_specs],
        initial_status=initial_status,
        stream=status_stream,
    )
    for spec in selected_specs:
        status_board.set(spec.source_ref, action_status)
        if action_stdout is None:
            result = action(spec)
        else:
            with contextlib.redirect_stdout(action_stdout):
                result = action(spec)
        results.append(result)
        status_board.set(spec.source_ref, done_status)
    return results


def generate_step_targets(
    targets: Sequence[str],
    *,
    direct_step_kind: str | None = None,
    step_options: StepImportOptions | None = None,
    output: str | Path | None = None,
    skip_step_write: bool = False,
    force: bool = False,
    verbose: bool = False,
) -> int:
    tool_name = "scripts/step"
    if direct_step_kind is not None and direct_step_kind not in {"part", "assembly"}:
        raise ValueError(f"{tool_name} --kind must be 'part' or 'assembly'")
    if direct_step_kind is None:
        direct_targets = _existing_direct_step_targets(targets)
        if direct_targets:
            joined = ", ".join(direct_targets)
            raise ValueError(f"{tool_name} --kind is required for direct STEP/STP targets: {joined}")
    logger = CliLogger("scripts/step", verbose=verbose)
    if output is not None and targets_include_output_pairs(targets):
        raise ValueError(f"{tool_name} --output cannot be combined with SOURCE=OUTPUT targets")
    output_path = _resolve_cli_output_path(output, expected_suffixes=(".step",), tool_name=tool_name)
    all_specs, selected_specs, target_output_paths = _selected_specs_for_targets(
        targets,
        direct_step_kind=direct_step_kind or "part",
        step_options=step_options,
        expected_output_suffixes=(".step",),
        tool_name=tool_name,
        include_output_paths=True,
    )
    for spec in selected_specs:
        _validate_step_target(spec, direct_step_kind=direct_step_kind, tool_name=tool_name)
    selected_specs = _apply_step_output_override(
        selected_specs,
        output_path=output_path,
        all_specs=all_specs,
        tool_name=tool_name,
    )
    selected_specs = _apply_step_output_overrides(
        selected_specs,
        output_paths=target_output_paths,
        all_specs=all_specs,
        tool_name=tool_name,
    )
    if skip_step_write:
        if output_path is not None or any(path is not None for path in target_output_paths):
            raise ValueError(f"{tool_name} --skip-step-write cannot be combined with STEP output overrides")
        invalid_specs = [
            spec.source_ref
            for spec in selected_specs
            if spec.source != "generated" or spec.script_path is None
        ]
        if invalid_specs:
            joined = ", ".join(invalid_specs)
            raise ValueError(f"{tool_name} --skip-step-write is valid only for Python gen_step() targets: {joined}")
    if step_options is not None and step_options.has_metadata:
        selected_specs = [_apply_step_options_to_spec(spec, step_options) for spec in selected_specs]
    _validate_part_render_output_paths([*all_specs, *selected_specs])
    entries_by_step_path = _entries_by_step_path([*all_specs, *selected_specs])
    def generate_step(spec: EntrySpec) -> object:
        return _run_with_spec_generation_status(
            spec,
            "gen_step",
            lambda tracked_spec: _generate_step_outputs_for_cli(
                tracked_spec,
                entries_by_step_path=entries_by_step_path,
                logger=logger,
                skip_step_write=skip_step_write,
                force=force,
            ),
        )

    _run_selected_specs(
        selected_specs,
        action=generate_step,
        logger=logger,
        success_message=_generated_python_glb_summary if skip_step_write else _generated_output_summary,
    )
    logger.total()
    return 0


def generate_dxf_targets(
    targets: Sequence[str],
    *,
    output: str | Path | None = None,
    verbose: bool = False,
) -> int:
    tool_name = "dxf"
    logger = CliLogger("scripts/dxf", verbose=verbose)
    if output is not None and targets_include_output_pairs(targets):
        raise ValueError(f"{tool_name} --output cannot be combined with SOURCE=OUTPUT targets")
    output_path = _resolve_cli_output_path(output, expected_suffixes=(".dxf",), tool_name=tool_name)
    all_specs, selected_specs, target_output_paths = _selected_specs_for_targets(
        targets,
        expected_output_suffixes=(".dxf",),
        tool_name=tool_name,
        include_output_paths=True,
    )
    for spec in selected_specs:
        _validate_dxf_target(spec)
    selected_specs = _apply_dxf_output_override(
        selected_specs,
        output_path=output_path,
        all_specs=all_specs,
        tool_name=tool_name,
    )
    selected_specs = _apply_dxf_output_overrides(
        selected_specs,
        output_paths=target_output_paths,
        all_specs=all_specs,
        tool_name=tool_name,
    )
    _run_selected_specs(
        selected_specs,
        action=lambda spec: _run_with_spec_generation_status(
            spec,
            "gen_dxf",
            lambda tracked_spec: run_script_generator(tracked_spec, "gen_dxf", logger=logger),
        ),
        logger=logger,
        success_message=_generated_dxf_summary,
    )
    logger.total()
    return 0


def run_tool_cli(
    argv: Sequence[str] | None,
    *,
    prog: str,
    description: str,
    action: Callable[..., int],
    target_help: str | None = None,
    output_help: str | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument(
        "targets",
        nargs="+",
        help=target_help or "Explicit Python generator or STEP/STP file path to generate.",
    )
    if output_help is not None:
        parser.add_argument("-o", "--output", metavar="PATH", help=output_help)
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress and timing information.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    if output_help is not None:
        if args.output is not None:
            if targets_include_output_pairs(args.targets):
                parser.error("--output cannot be combined with SOURCE=OUTPUT targets")
            if len(args.targets) != 1:
                parser.error("--output can only be used with exactly one target")
        return action(args.targets, output=args.output, verbose=bool(args.verbose))
    return action(args.targets, verbose=bool(args.verbose))


class GenerationError(Exception):
    """Base error for the high-level :func:`generate_step` wrapper.

    The frozen contract (`docs/panda-interfaces.md` §1) requires every
    error raised by ``generate_step`` to subclass this type, so callers
    such as the cadcode skill runner can map them to JSON error codes.

    Internal helpers (`_load_generator_module`, `_normalize_step_payload`,
    `_write_shape_step_payload`) still raise generic `TypeError` /
    `RuntimeError` / `ValueError` — the wrapper wraps those in the
    matching subclass below.
    """


class ProjectShapeError(GenerationError):
    """The project directory is missing ``main.py`` or has an unsupported
    layout."""


class GeneratorRuntimeError(GenerationError):
    """The user's ``gen_step()`` (or legacy ``result =``) raised, or the
    module failed to load."""


class ShapeValidationError(GenerationError):
    """``gen_step()`` returned a value that the duck-typed envelope
    resolver could not classify (see contract §1)."""


class ExportError(GenerationError):
    """STEP / GLB / sidecar export failed after the user's gen_step() ran
    cleanly."""


def _bbox_dict_from_shape(shape: object) -> dict[str, list[float]]:
    """Return ``{"min": [x,y,z], "max": [x,y,z]}`` for an OCCT shape.

    Uses the existing ``_bbox_from_shape`` helper (which returns the
    richer ``{min, max, center, size, diag}`` dict) and strips it down to
    the contract §3 shape.
    """
    from cadpy.step_scene import _bbox_from_shape

    full = _bbox_from_shape(shape)
    return {
        "min": [float(v) for v in full["min"]],
        "max": [float(v) for v in full["max"]],
    }


def _volume_mm3_from_shape(shape: object) -> float:
    """Compute the volume (mm^3) of an OCCT shape via ``BRepGProp``."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps

    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return float(props.Mass())


def _is_solid_shape(shape: object) -> bool:
    """True if the OCCT shape contains at least one TopAbs_SOLID."""
    from OCP.TopAbs import TopAbs_SOLID
    from OCP.TopExp import TopExp
    from OCP.TopTools import TopTools_IndexedMapOfShape

    solid_map = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(shape, TopAbs_SOLID, solid_map)
    return solid_map.Extent() > 0


def _resolve_envelope_for_project(
    project_dir: Path,
    *,
    script_path: Path,
) -> dict[str, object]:
    """Load ``main.py``, run ``gen_step()`` (or pick up legacy ``result``),
    and return the normalized envelope.

    The runtime contract requires:
      * a callable module-level ``gen_step()`` — preferred path,
      * OR a module-level ``result = <shape>`` binding — back-compat path.

    Wraps the lower-level normalizer so all failures land as
    ``GenerationError`` subclasses.
    """
    if not project_dir.is_dir():
        raise ProjectShapeError(f"project_dir is not a directory: {project_dir}")
    if not script_path.is_file():
        raise ProjectShapeError(f"main.py not found in project: {project_dir}")

    try:
        module = _load_generator_module(script_path)
    except (SyntaxError, ImportError) as exc:
        # Propagate so the runner's code-mapping branch can see the type.
        raise
    except Exception as exc:
        raise GeneratorRuntimeError(
            f"failed to load {script_path.name}: {type(exc).__name__}: {exc}"
        ) from exc

    generator = getattr(module, "gen_step", None)
    if callable(generator):
        try:
            raw = generator()
        except (SyntaxError, ImportError):
            raise
        except GenerationError:
            raise
        except AssertionError as exc:
            # A project's validate_params()/functional asserts use `assert` to
            # hard-block impossible fits. Surface the assert message cleanly as a
            # validation failure (ProjectShapeError → code VALIDATION_FAILED) so
            # the build turn sees "back wall 1.2 mm < 2.0 mm", not a buried
            # AssertionError traceback.
            raise ProjectShapeError(
                f"design validation failed: {exc}" if str(exc) else "design validation failed"
            ) from exc
        except Exception as exc:
            raise GeneratorRuntimeError(
                f"gen_step() raised {type(exc).__name__}: {exc}"
            ) from exc
    elif hasattr(module, "result"):
        # Legacy single-file form — the module-level `result` IS the shape.
        raw = getattr(module, "result")
    else:
        raise ProjectShapeError(
            f"{script_path.name} defines neither gen_step() nor a module-level `result`"
        )

    try:
        return _normalize_step_payload(raw, script_path=script_path)
    except TypeError as exc:
        raise ShapeValidationError(str(exc)) from exc


def _build_synthetic_spec_for_wrapper(
    *,
    script_path: Path,
    output_path: Path,
    mesh_tolerance: float,
    mesh_angular_tolerance: float,
    envelope: dict[str, object],
) -> EntrySpec:
    """Construct an ``EntrySpec`` matching what catalog discovery would
    produce, but for a project that may live anywhere on disk.

    Used only inside :func:`generate_step` — keeps the dispatch types
    compatible with ``_write_shape_step_payload`` /
    ``_write_assembly_step_payload``.
    """
    kind = "part"
    if "instances" in envelope or "children" in envelope:
        kind = "assembly"
    elif "shape" in envelope:
        kind = _shape_payload_entry_kind(envelope.get("shape"), fallback="part")

    return EntrySpec(
        source_ref=str(script_path),
        cad_ref=output_path.stem,
        kind=kind,
        source_path=script_path,
        display_name=output_path.stem,
        source="generated",
        step_path=output_path,
        script_path=script_path,
        mesh_tolerance=float(mesh_tolerance),
        mesh_angular_tolerance=float(mesh_angular_tolerance),
        mesh_tolerance_explicit=True,
        mesh_angular_tolerance_explicit=True,
    )


def _resolve_stl_path(envelope: dict[str, object], *, stem: str, parent: Path) -> Path | None:
    """Honor envelope[\"stl\"] = True | <path> per contract §1."""
    raw = envelope.get("stl")
    if raw is None or raw is False:
        return None
    if raw is True:
        return parent / f"{stem}.stl"
    candidate = Path(str(raw)).expanduser()
    if not candidate.is_absolute():
        candidate = parent / candidate
    return candidate


def _resolve_3mf_path(envelope: dict[str, object], *, stem: str, parent: Path) -> Path | None:
    """Honor envelope[\"3mf\"] = True | <path> per contract §1."""
    raw = envelope.get("3mf")
    if raw is None or raw is False:
        return None
    if raw is True:
        return parent / f"{stem}.3mf"
    candidate = Path(str(raw)).expanduser()
    if not candidate.is_absolute():
        candidate = parent / candidate
    return candidate


def _write_topology_artifacts(
    *,
    scene: LoadedStepScene,
    spec: EntrySpec,
    glb_target_path: Path,
    topology_json_path: Path,
) -> dict[str, object]:
    """Write the topology-embedded GLB to ``glb_target_path`` and a
    parallel JSON manifest to ``topology_json_path``. Returns the manifest
    dict (the post-`build_step_topology_index_manifest` form).
    """
    from cadpy.glb import _HierarchicalGlbWriter

    selector_options = _selector_options_for_part(spec, scene=scene)
    mesh_step_scene(
        scene,
        linear_deflection=selector_options.linear_deflection,
        angular_deflection=selector_options.angular_deflection,
        relative=selector_options.relative,
    )
    scene_export_shape(scene)

    bundle = extract_selectors_from_scene(
        scene,
        cad_ref=spec.cad_ref,
        profile=SelectorProfile.ARTIFACT,
        options=selector_options,
        color=spec.color,
    )
    index_manifest = build_step_topology_index_manifest(bundle.manifest, entry_kind=spec.kind)

    glb_target_path.parent.mkdir(parents=True, exist_ok=True)
    _HierarchicalGlbWriter(scene, color=spec.color).write(
        glb_target_path,
        selector_bundle=bundle,
        include_selector_topology=True,
        entry_kind=spec.kind,
    )

    topology_json_path.parent.mkdir(parents=True, exist_ok=True)
    topology_json_path.write_text(
        json.dumps(index_manifest, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    return index_manifest


def _write_metadata_sidecar(
    *,
    metadata_path: Path,
    script_path: Path,
    step_path: Path,
    spec: EntrySpec,
    is_solid: bool,
    volume_mm3: float,
    bbox: dict[str, list[float]],
    mesh_tolerance: float,
    mesh_angular_tolerance: float,
    parts: list[dict[str, str]] | None = None,
    warnings: list[dict[str, str]] | None = None,
) -> None:
    """Write ``<stem>.step.json`` — source hash + generator info +
    validation summary, per contract §1.

    When ``parts`` is given (assemblies with per-part STLs), each entry is
    ``{"name", "stlPath"}`` with ``stlPath`` relative to this sidecar's
    directory; the viewer groups these under the integrated model.

    ``warnings`` (when non-empty) lists deterministic geometry problems found
    after generation (floating bodies, slivers, invalid B-reps), recorded under
    ``validation.warnings``.
    """
    identity = python_source_hash(script_path)
    payload: dict[str, object] = {
        "generator": "cadpy",
        "entryKind": spec.kind,
        "source": {
            "kind": "python",
            "path": str(script_path),
            "hash": identity.source_hash,
            "fingerprint": identity.source_fingerprint,
        },
        "step": {
            "path": step_path.name,
        },
        "mesh": {
            "tolerance": float(mesh_tolerance),
            "angularTolerance": float(mesh_angular_tolerance),
        },
        "validation": {
            "isSolid": bool(is_solid),
            "volumeMm3": float(volume_mm3),
            "bbox": bbox,
        },
    }
    if warnings:
        payload["validation"]["warnings"] = warnings
    if parts:
        payload["parts"] = parts
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


def _write_shape_step_payload_with_source(
    envelope: dict[str, object],
    *,
    output_path: Path,
    script_path: Path,
    source_path_for_metadata: str,
    logger: CliLogger,
    entry_kind: str,
) -> LoadedStepScene:
    """Variant of ``_write_shape_step_payload`` that takes an explicit
    ``source_path_for_metadata`` instead of computing one via
    ``relative_to_repo(script_path)``.

    This is needed because the high-level :func:`generate_step` wrapper
    accepts projects from anywhere on disk; the STEP metadata writer
    rejects absolute paths (see ``step_metadata.normalize_text_to_cad_source_path``).

    Mirrors the library-dispatch + scene-tagging logic of
    ``_write_shape_step_payload`` exactly, just with the source path
    plumbed in.
    """
    shape = envelope.get("shape")

    use_cadquery_path = (
        _looks_like_cadquery_assembly(shape)
        or _looks_like_topods_workplane(shape)
        or _looks_like_topods_wrapper(shape)
    )

    if not use_cadquery_path:
        raise TypeError(
            f"{_display_path(script_path)} gen_step() envelope field 'shape' must be a "
            "cq.Workplane, cq.Shape, or cq.Assembly; "
            f"got {type(shape).__name__}"
        )

    source_identity = python_source_hash(script_path)

    from cadpy.step_export_cadquery import export_cadquery_step_scene

    scene = export_cadquery_step_scene(
        shape,
        output_path,
        text_to_cad_entry_kind=entry_kind,
        source_path=source_path_for_metadata,
        source_fingerprint=source_identity.source_fingerprint,
        source_hash=source_identity.source_hash,
    )

    # Tag the scene as python-backed without going through
    # ``_mark_scene_python_backed`` (which also calls ``relative_to_repo``
    # on the script path). We set the same fields directly.
    if isinstance(scene, LoadedStepScene):
        scene.source_kind = "python"
        scene.source_hash = source_identity.source_hash
        scene.source_fingerprint = source_identity.source_fingerprint
        scene.source_path = source_path_for_metadata
    _mark_scene_step_payload(scene, entry_kind=entry_kind, payload_kind="shape")
    logger.debug(f"wrote STEP: {_display_path(output_path)}")
    return scene


def _coerce_project_warnings(raw: object) -> list[dict[str, str]]:
    """Normalize a project-declared envelope ``warnings`` list into the
    ``validation.warnings`` entry shape, dropping malformed items.

    A project's ``gen_step()`` may return ``{"shape": ..., "warnings": [...]}``
    to declare its own (typically ``kind:"functional"``) checks alongside the
    deterministic geometry checks. Each entry must be a mapping with non-empty
    string ``kind`` and ``detail``; ``part`` defaults to ``"model"`` and
    ``severity`` to ``"warning"`` (blocking). Never raises — a malformed
    declaration must not break generation.
    """
    if not isinstance(raw, (list, tuple)):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        detail = item.get("detail")
        if not isinstance(kind, str) or not kind.strip():
            continue
        if not isinstance(detail, str) or not detail.strip():
            continue
        part = item.get("part")
        severity = item.get("severity")
        out.append(
            {
                "part": part if isinstance(part, str) and part else "model",
                "kind": kind,
                "detail": detail,
                "severity": severity
                if isinstance(severity, str) and severity
                else "warning",
            }
        )
    return out


def generate_step(
    project_dir: Path | str,
    output_path: Path | str,
    *,
    mesh_tolerance: float = DEFAULT_MESH_TOLERANCE,
    mesh_angular_tolerance: float = DEFAULT_MESH_ANGULAR_TOLERANCE,
) -> dict[str, object]:
    """High-level wrapper used by the cadcode skill runner.

    Loads ``<project_dir>/main.py``, calls its ``gen_step()`` (or picks
    up a legacy module-level ``result``), and writes the artifact set
    defined in ``docs/panda-interfaces.md`` §1 — all sibling to
    ``output_path``:

      * ``<stem>.step``       — B-rep with XCAF labels + metadata
      * ``<stem>.stl``        — printable mesh + the viewer's preview mesh
      * ``<stem>.step.json``  — source hash, generator, validation

    Returns the dict consumed by the runner's
    ``_build_success_payload`` — see contract §3.

    All raised errors subclass :class:`GenerationError`; library-level
    ``SyntaxError`` / ``ImportError`` propagate untouched so the runner's
    error-code mapping can recognise them.
    """
    project_dir_p = Path(project_dir).expanduser().resolve()
    output_path_p = Path(output_path).expanduser().resolve()
    if output_path_p.suffix.lower() != ".step":
        raise ProjectShapeError(
            f"output_path must end in .step (got {output_path_p.name})"
        )

    script_path = project_dir_p / "main.py"
    envelope = _resolve_envelope_for_project(project_dir_p, script_path=script_path)

    # Project-declared warnings (e.g. functional/assembly checks) ride on the
    # envelope; pop them out before the spec/shape writers see the envelope, and
    # merge them with the deterministic geometry warnings below.
    project_warnings = _coerce_project_warnings(envelope.pop("warnings", None))

    spec = _build_synthetic_spec_for_wrapper(
        script_path=script_path,
        output_path=output_path_p,
        mesh_tolerance=mesh_tolerance,
        mesh_angular_tolerance=mesh_angular_tolerance,
        envelope=envelope,
    )

    logger = CliLogger("cadpy.generate_step")

    # Resolve a "source path" string that satisfies the STEP metadata
    # writer's relative-path rule (see ``step_metadata.normalize_text_to_cad_source_path``).
    # The existing ``_write_shape_step_payload`` calls ``relative_to_repo()``
    # which returns an absolute path when the project lives outside the
    # process REPO_ROOT (cwd). For Panda workspaces that's the common case
    # (~/Library/Application Support/Panda/projects/<id>/), so we
    # bypass the helper and pass a project-relative source path directly.
    source_path_for_metadata = f"{project_dir_p.name}/{script_path.name}"

    try:
        if "shape" in envelope:
            scene = _write_shape_step_payload_with_source(
                envelope,
                output_path=output_path_p,
                script_path=script_path,
                source_path_for_metadata=source_path_for_metadata,
                logger=logger,
                entry_kind=spec.kind,
            )
        elif "instances" in envelope or "children" in envelope:
            # Reference-assembly envelopes (list/instances/children of
            # catalog parts); plain cq.Assembly returns are normalized to the
            # "shape" branch earlier. If a future caller produces a
            # list/instances envelope from outside REPO_ROOT we'll need to
            # extend the assembly writer too — flag it loudly until then.
            scene = _write_assembly_step_payload(
                envelope,
                output_path=output_path_p,
                script_path=script_path,
                logger=logger,
                force=True,
                load_current_scene=True,
            )
            if scene is None:
                # _write_assembly_step_payload only returns None when
                # load_current_scene=False; we forced True above.
                raise ExportError("assembly STEP writer returned no scene")
        else:  # pragma: no cover — _normalize_step_payload guarantees one of the above
            raise ShapeValidationError(
                "envelope must define exactly one of 'shape', 'instances', or 'children'"
            )
    except GenerationError:
        raise
    except Exception as exc:
        raise ExportError(
            f"failed to write STEP {output_path_p.name}: {type(exc).__name__}: {exc}"
        ) from exc

    # Sibling artifact paths per contract §1 (STEP + STL + metadata).
    parent = output_path_p.parent
    stem = output_path_p.stem
    stl_path = parent / f"{stem}.stl"
    metadata_path = parent / f"{stem}.step.json"

    # Mesh the scene so the STL writer has triangulated geometry, then merge
    # the occurrences into a single export shape.
    try:
        selector_options = _selector_options_for_part(spec, scene=scene)
        mesh_step_scene(
            scene,
            linear_deflection=selector_options.linear_deflection,
            angular_deflection=selector_options.angular_deflection,
            relative=selector_options.relative,
        )
        export_shape = scene_export_shape(scene)
    except Exception as exc:
        raise ExportError(
            f"failed to mesh {output_path_p.name}: {type(exc).__name__}: {exc}"
        ) from exc

    try:
        is_solid = _is_solid_shape(export_shape)
        volume_mm3 = _volume_mm3_from_shape(export_shape)
        bbox = _bbox_dict_from_shape(export_shape)
    except Exception as exc:
        raise ExportError(
            f"failed to compute geometry facts for {output_path_p.name}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    # Assemblies (more than one leaf occurrence) also get one STL per named
    # part — each at its own build origin, ready to review/print individually
    # alongside the assembled <stem>.stl. Single-solid projects skip this.
    parts_dir = parent / f"{stem}_parts"
    part_outputs: list[tuple[str, Path]] = []
    try:
        if len(scene_leaf_occurrences(scene)) > 1:
            part_outputs = export_part_stls_from_scene(scene, parts_dir)
    except Exception as exc:
        raise ExportError(
            f"failed to write per-part STLs for {output_path_p.name}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    # Paths in metadata/payload are relative to the sidecar directory so the
    # catalog can resolve them regardless of where the workspace lives.
    parts_meta = [
        {"name": name, "stlPath": f"{parts_dir.name}/{path.name}"}
        for name, path in part_outputs
    ]

    # Deterministic geometry sanity checks (floating bodies, slivers, invalid
    # B-reps). Advisory — never fails generation; surfaced for the skill loop
    # and harness Review phase to act on.
    try:
        from cadpy.checks import collect_scene_warnings

        warnings = collect_scene_warnings(export_shape, scene)
    except Exception:
        warnings = []

    # Merge the project's own declared warnings (functional/assembly checks)
    # after the deterministic geometry checks, so both reach validation.warnings.
    warnings = list(warnings) + project_warnings

    try:
        _write_metadata_sidecar(
            metadata_path=metadata_path,
            script_path=script_path,
            step_path=output_path_p,
            spec=spec,
            is_solid=is_solid,
            volume_mm3=volume_mm3,
            bbox=bbox,
            mesh_tolerance=mesh_tolerance,
            mesh_angular_tolerance=mesh_angular_tolerance,
            parts=parts_meta,
            warnings=warnings,
        )
    except Exception as exc:
        raise ExportError(
            f"failed to write metadata sidecar: {type(exc).__name__}: {exc}"
        ) from exc

    # STL is always written — it is the printable deliverable and the viewer's
    # preview mesh.
    try:
        export_part_stl_from_scene(output_path_p, scene, target_path=stl_path)
    except Exception as exc:
        raise ExportError(
            f"failed to write STL {stl_path.name}: {type(exc).__name__}: {exc}"
        ) from exc

    return {
        "step_path": str(output_path_p),
        "stl_path": str(stl_path),
        "metadata_path": str(metadata_path),
        "is_solid": bool(is_solid),
        "volume_mm3": float(volume_mm3),
        "bbox": bbox,
        "mesh_tolerance": float(mesh_tolerance),
        "mesh_angular_tolerance": float(mesh_angular_tolerance),
        "parts": [
            {"name": name, "stl_path": str(path)} for name, path in part_outputs
        ],
        "warnings": warnings,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CAD generation support library.")
    parser.parse_args(list(argv) if argv is not None else None)
    parser.error("common.generation is a library module.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
