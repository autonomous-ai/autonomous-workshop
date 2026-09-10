"""Export one CAD model to a standalone STEP file.

STEP is the only format this module writes. The mesh exporters it used to offer —
STL, 3MF and a user-facing native GLB — are gone: this repository delivers
validated CAD geometry and nothing downstream of it, so there is no supported
path from a model to a print or view mesh, from this module or from any CLI.

Its one caller is the CAD Viewer's "Export model" backend — one format to an
arbitrary ``--out`` destination picked from a native Save dialog, via ``main()``/
:func:`export_model_to_path`. A Viewer that asks for any other format now gets a
refusal rather than a mesh.

It accepts an imported ``.step``/``.stp`` or a generated ``gen_step()`` Python
source, and always builds from source, so an export can never be stale.

It is deliberately distinct from :mod:`cadgen.step_artifact_cli`, which (re)builds
the per-folder ``__cadgen__`` viewer GLB/topology package beside the source. That
package is the viewer's and ``inspect``'s internal working format, not a
deliverable; this module produces a standalone file and writes **no** package or
beside-source artifacts.

Emits a single final JSON line on stdout: ``{"ok": true, "path": ..., "filename": ...}``
or ``{"ok": false, "error": ...}`` (the Node spawner parses the last stdout JSON line).
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import replace
from pathlib import Path

from cadgen.catalog import source_from_path
from cadgen.cli_logging import CliLogger
from cadgen._internal.generation import (
    EntrySpec,
    _entry_spec_from_source,
    _selector_options_for_part,
    run_script_generator,
)
from cadgen.metadata import normalize_mesh_numeric
from cadgen.step_artifact_cli import _build_entry_spec, _cad_ref_for_step, infer_entry_kind
from cadgen.step_export import export_build123d_step_file
from cadgen._internal.step_scene import (
    LoadedStepScene,
    load_step_scene,
    mesh_step_scene,
    scene_export_shape,
)

# Logical format name -> conventional file suffix (informational; the caller owns `--out`).
# STEP only. No mesh format is offered anywhere in this repository.
FORMAT_SUFFIX = {"step": ".step"}


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
    reset_runtime_closure: bool = False,
    logger: CliLogger,
) -> tuple[EntrySpec, LoadedStepScene]:
    """Build the entry spec + an in-memory scene for the model.

    Generated model (``--source-path`` given): run ``gen_step()`` in-process to build the
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
        # Align the logical STEP path/name when the caller passed an explicit --step that the
        # generator does not itself resolve to (mirrors cadgen.step_artifact_cli).
        if step_path is not None and spec.step_path.resolve() != step_path.resolve():
            spec = replace(
                spec,
                cad_ref=_cad_ref_for_step(repo_root, step_path),
                display_name=step_path.stem,
                step_path=step_path,
            )
        spec = _apply_mesh_overrides(spec, mesh_tolerance, mesh_angular_tolerance)
        # An export runs the generator but writes the render package NOTHING -- its output
        # is a STEP/STL/3MF/GLB file somewhere else entirely. Claiming the writer lock here
        # made a fully-current model report `generating` with an empty bar for the whole
        # length of the export.
        scene = run_script_generator(
            spec,
            "gen_step",
            logger=logger,
            force=True,
            reset_runtime_closure=reset_runtime_closure,
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


def _export_scene(
    fmt: str,
    spec: EntrySpec,
    scene: LoadedStepScene,
    out: Path,
    selector_options,
) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "step":
        # gen_step writes no STEP, so serialize the generator's in-memory compound; an
        # imported source already has a text STEP on disk, so copy it to the destination.
        source_compound = getattr(scene, "source_compound", None)
        if source_compound is not None:
            export_build123d_step_file(
                source_compound,
                out,
                text_to_cad_entry_kind=spec.kind,
                source_path=(str(getattr(scene, "source_path", "") or "") or None),
                source_hash=(str(getattr(scene, "source_hash", "") or "") or None),
            )
            return out
        if spec.step_path is not None and spec.step_path.is_file():
            if spec.step_path.resolve() != out.resolve():
                shutil.copyfile(spec.step_path, out)
            return out
        raise RuntimeError("No STEP geometry available to export")

    raise ValueError(
        f"Unsupported export format: {fmt}. This repository exports STEP only; "
        "no STL, 3MF or GLB export exists."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m cadgen.step_export_target",
        description="Export one CAD model to STEP at an explicit destination path.",
    )
    parser.add_argument("--repo-root", required=True, help="Repository/workspace root for relative metadata.")
    parser.add_argument("--step", required=True, help="Logical STEP path (generated) or on-disk STEP/STP (imported).")
    parser.add_argument("--source-path", help="Python gen_step() generator (.step.py) for a generated model.")
    parser.add_argument("--format", required=True, choices=tuple(FORMAT_SUFFIX), help="Output format.")
    parser.add_argument("--out", required=True, help="Destination file path for the exported model.")
    parser.add_argument("--mesh-tolerance", type=float, help="Override automatic mesh linear deflection.")
    parser.add_argument("--mesh-angular-tolerance", type=float, help="Override automatic mesh angular deflection.")
    parser.add_argument("--verbose", action="store_true", help="Show detailed timing on stderr.")
    return parser


def export_model_to_path(
    *,
    repo_root: Path,
    step: Path,
    fmt: str,
    out: Path,
    source_path: Path | None = None,
    mesh_tolerance: float | None = None,
    mesh_angular_tolerance: float | None = None,
    reset_runtime_closure: bool = False,
    logger: CliLogger | None = None,
) -> dict[str, object]:
    """Export one CAD model to STEP at ``out`` and RETURN
    {ok, path, filename, format}. Single source of truth, callable in-process by a
    warm-OCCT worker AND wrapped by main(); it RAISES on error so callers map their
    own protocol (the CLI shell keeps the {ok:false,error} JSON envelope).

    ``reset_runtime_closure`` (default-off) is for warm worker processes — see
    :func:`cadgen.generation.run_script_generator`."""
    if logger is None:
        logger = CliLogger("step-export", verbose=False)
    repo_root = Path(repo_root).expanduser().resolve()
    step_path = Path(step).expanduser().resolve()
    source_path = Path(source_path).expanduser().resolve() if source_path else None
    out = Path(out).expanduser().resolve()
    mesh_tolerance = normalize_mesh_numeric(mesh_tolerance, field_name="mesh_tolerance")
    mesh_angular_tolerance = normalize_mesh_numeric(mesh_angular_tolerance, field_name="mesh_angular_tolerance")
    spec, scene = _resolve_spec_and_scene(
        repo_root,
        step_path,
        source_path,
        mesh_tolerance=mesh_tolerance,
        mesh_angular_tolerance=mesh_angular_tolerance,
        reset_runtime_closure=reset_runtime_closure,
        logger=logger,
    )
    selector_options = _selector_options_for_part(spec, scene=scene)
    written = _export_scene(fmt, spec, scene, out, selector_options)
    return {"ok": True, "path": str(written), "filename": written.name, "format": fmt}


def _is_step_suffix(path: Path) -> bool:
    return path.suffix.lower() in {".step", ".stp"}


def run_cli_payload(
    argv: list[str] | None = None,
    *,
    reset_runtime_closure: bool = False,
) -> dict[str, object]:
    """Parse CLI ``argv`` and run :func:`export_model_to_path`, RETURNING its
    ``{ok:true,...}`` payload (no printing). RAISES on error — callers own the error
    envelope. The in-process primitive shared by ``main()`` and the CAD Viewer's warm
    worker (which passes ``reset_runtime_closure=True`` to keep the warm interpreter's
    generator-module state clean between builds)."""
    args = build_parser().parse_args(argv)
    logger = CliLogger("step-export", verbose=bool(args.verbose))
    payload = export_model_to_path(
        repo_root=Path(args.repo_root),
        step=Path(args.step),
        fmt=args.format,
        out=Path(args.out),
        source_path=Path(args.source_path) if args.source_path else None,
        mesh_tolerance=args.mesh_tolerance,
        mesh_angular_tolerance=args.mesh_angular_tolerance,
        reset_runtime_closure=reset_runtime_closure,
        logger=logger,
    )
    logger.total()
    return payload


def main(argv: list[str] | None = None) -> int:
    try:
        payload = run_cli_payload(argv)
    except Exception as exc:  # noqa: BLE001 — surface a clean JSON error to the CLI caller.
        print(json.dumps({"ok": False, "error": str(exc)}, separators=(",", ":")))
        return 1
    print(json.dumps(payload, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
