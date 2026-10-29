"""Build one CAD model's in-memory scene straight from its source.

``inspect validate`` and ``inspect interfere`` check the geometry the generator produces
now, not a package or STEP written earlier, so they come through here: a generated
``gen_step()`` source is run in-process, and an imported ``.step``/``.stp`` is loaded.
Nothing is written -- no package, no STEP.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from cadgen.catalog import source_from_path
from cadgen.cli_logging import CliLogger
from cadgen._internal.generation import (
    EntrySpec,
    _entry_spec_from_source,
    run_script_generator,
)
from cadgen.step_artifact_cli import _build_entry_spec, _cad_ref_for_step, infer_entry_kind
from cadgen._internal.step_scene import LoadedStepScene, load_step_scene


def _apply_mesh_overrides(
    spec: EntrySpec,
    mesh_tolerance: float | None,
    mesh_angular_tolerance: float | None,
) -> EntrySpec:
    if mesh_tolerance is None and mesh_angular_tolerance is None:
        return spec
    return replace(
        spec,
        mesh_tolerance=mesh_tolerance if mesh_tolerance is not None else spec.mesh_tolerance,
        mesh_angular_tolerance=(
            mesh_angular_tolerance
            if mesh_angular_tolerance is not None
            else spec.mesh_angular_tolerance
        ),
        mesh_tolerance_explicit=mesh_tolerance is not None or spec.mesh_tolerance_explicit,
        mesh_angular_tolerance_explicit=(
            mesh_angular_tolerance is not None or spec.mesh_angular_tolerance_explicit
        ),
    )


def _resolve_spec_and_scene(
    repo_root: Path,
    step_path: Path | None,
    source_path: Path | None,
    *,
    mesh_tolerance: float | None,
    mesh_angular_tolerance: float | None,
    logger: CliLogger,
) -> tuple[EntrySpec, LoadedStepScene]:
    """Build the entry spec + an in-memory scene for the model.

    Generated model (``source_path`` given): run ``gen_step()`` in-process to build the
    scene — generated models keep no on-disk STEP. Imported model: load the existing STEP
    and classify it via :func:`cadgen.step_artifact_cli.infer_entry_kind`.
    """
    if source_path is not None:
        source = source_from_path(source_path)
        if source is None:
            raise RuntimeError(f"Python generator is not a gen_step() CAD source: {source_path}")
        spec = _entry_spec_from_source(source)
        if spec.step_path is None:
            raise RuntimeError(f"Generator defines no STEP output: {source_path}")
        # Align the logical STEP path/name when the caller passed a step path that the
        # generator does not itself resolve to (mirrors cadgen.step_artifact_cli).
        if step_path is not None and spec.step_path.resolve() != step_path.resolve():
            spec = replace(
                spec,
                cad_ref=_cad_ref_for_step(repo_root, step_path),
                display_name=step_path.stem,
                step_path=step_path,
            )
        spec = _apply_mesh_overrides(spec, mesh_tolerance, mesh_angular_tolerance)
        # This runs the generator but writes the render package NOTHING, so it takes the
        # generator lock, not the writer lock: claiming the writer lock made a fully-current
        # model report `generating` for the whole length of the run.
        scene = run_script_generator(
            spec,
            "gen_step",
            logger=logger,
            force=True,
            lock_intent="generate",
        )
        if scene is None:
            raise RuntimeError(f"Generator did not produce a STEP scene: {spec.source_ref}")
        return spec, scene

    if step_path is None:
        raise ValueError("step_path is required for imported STEP/STP models")
    if not step_path.is_file():
        raise FileNotFoundError(f"STEP file does not exist: {step_path}")
    with logger.timed(f"load STEP {step_path.name}"):
        scene = load_step_scene(step_path)
    spec = _build_entry_spec(
        repo_root,
        step_path,
        scene,
        kind=infer_entry_kind(step_path, scene),
        mesh_tolerance=mesh_tolerance,
        mesh_angular_tolerance=mesh_angular_tolerance,
    )
    return spec, scene
