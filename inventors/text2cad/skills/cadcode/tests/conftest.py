"""pytest fixtures for the cadcode skill.

The real ``cadpy.generation.generate_step`` wrapper (Track A follow-up,
see ``packages/cadpy/src/cadpy/generation.py``) is now in place and works
end-to-end. This conftest still injects a lightweight stub via
``CADCODE_TEST_CADPY_PATH`` so the skill's 51 tests don't pay the OCCT
STEP export cost on every iteration. Tests that need the real artifact
pipeline live in ``packages/cadpy/tests/test_generate_step_wrapper.py``.

The stub:

  * Provides a bare ``cadpy.generation.generate_step`` callable that
    matches the frozen contract §1 signature.
  * Writes the contract §3 artifact set (``<stem>.step``,
    ``<stem>.step.json``) plus a real STL produced by CadQuery from the
    project's ``gen_step()`` shape — that keeps
    ``test_recipe_produces_stl`` honest without simulating the full
    cadpy pipeline.
  * Exposes ``cadpy.generation.GenerationError`` so the runner's
    error-mapping branches still type-check.

The stub is injected via the ``CADCODE_TEST_CADPY_PATH`` env var; the
runner picks it up and shoves it on ``sys.path`` before importing cadpy.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path
from textwrap import dedent

import pytest


def _build_stub_cadpy(stub_root: Path) -> None:
    """Materialize a tiny ``cadpy`` package at ``stub_root/cadpy/``."""
    pkg = stub_root / "cadpy"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text(dedent('''
        """Test stub for cadpy. See tests/conftest.py for the why."""
        from . import generation  # noqa: F401
    ''').lstrip())

    (pkg / "generation.py").write_text(dedent('''
        """Stub cadpy.generation that mirrors contract §1's generate_step.

        Behavior:
          * Loads <project_dir>/main.py as a module, with project_dir on
            sys.path so sibling modules resolve.
          * Calls gen_step() if present; else picks up module-level `result`
            (back-compat path).
          * Writes the canonical artifact set to output_path's parent.
          * Returns a dict matching the production return shape so the
            caller's payload normalizer stays exercised.
        """
        from __future__ import annotations

        import hashlib
        import importlib.util
        import json
        from pathlib import Path
        from typing import Any


        class GenerationError(Exception):
            """Base error type per contract §1."""


        class ValidationError(GenerationError):
            pass


        class ExportError(GenerationError):
            pass


        def _load_main(project_dir: Path) -> Any:
            main_py = project_dir / "main.py"
            if not main_py.exists():
                raise ValidationError(f"no main.py in {project_dir}")
            # Run the file in a synthetic module named after our convention so
            # the runner's import hook recognizes user code.
            mod_name = "__cadcode_model__"
            spec = importlib.util.spec_from_file_location(mod_name, str(main_py))
            if spec is None or spec.loader is None:
                raise ExportError(f"could not load spec for {main_py}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            return module


        def _resolve_shape_or_envelope(module: Any) -> dict:
            """Mirror contract §1: gen_step() takes precedence; legacy
            module-level `result` is back-compat."""
            if hasattr(module, "gen_step") and callable(module.gen_step):
                payload = module.gen_step()
            elif hasattr(module, "result"):
                payload = module.result
            else:
                raise ValidationError(
                    "main.py defines neither gen_step() nor a `result` module-level variable"
                )

            if isinstance(payload, dict):
                envelope = payload
            else:
                envelope = {"shape": payload}
            return envelope


        def _to_shape(obj: Any) -> Any:
            """Match contract §1 duck-typing rules at a stub level."""
            if hasattr(obj, "val") and callable(obj.val):
                shape = obj.val()
                if hasattr(shape, "wrapped"):
                    return shape
            if hasattr(obj, "wrapped"):
                return obj
            raise ValidationError(f"unsupported shape type: {type(obj).__name__}")


        def _sha256(path: Path) -> str:
            h = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(1 << 16), b""):
                    h.update(chunk)
            return h.hexdigest()


        def generate_step(
            project_dir,
            output_path,
            *,
            mesh_tolerance: float = 0.05,
            mesh_angular_tolerance: float = 3.0,
        ) -> dict:
            """Stub of cadpy.generation.generate_step per contract §1.

            Writes the STEP + STL + metadata artifact set; only the STL is
            real (built from the gen_step() shape) so existing "STL exists
            and is >1000 bytes" assertions stay meaningful.
            """
            project_dir = Path(project_dir)
            output_path = Path(output_path)
            out_dir = output_path.parent
            stem = output_path.stem
            out_dir.mkdir(parents=True, exist_ok=True)

            module = _load_main(project_dir)
            envelope = _resolve_shape_or_envelope(module)
            shape_obj = envelope.get("shape")
            if shape_obj is None:
                # `children` / `instances` not exercised by the stub — pick
                # the first item if present.
                children = envelope.get("children") or envelope.get("instances") or []
                if not children:
                    raise ValidationError("envelope is empty")
                shape_obj = children[0]
            shape = _to_shape(shape_obj)

            # Geometry facts: use OCCT-level attributes that work for both
            # cadquery.Shape and cadquery.Workplane via _to_shape() above.
            is_solid = bool(shape.isValid())
            volume_mm3 = float(shape.Volume()) if is_solid else 0.0
            bb = shape.BoundingBox()
            bbox = {
                "min": (bb.xmin, bb.ymin, bb.zmin),
                "max": (bb.xmax, bb.ymax, bb.zmax),
            }

            # --- Write the artifact set (STEP + STL + metadata) ---
            step_path = out_dir / f"{stem}.step"
            metadata_path = out_dir / f"{stem}.step.json"

            # Stub STEP: empty-but-present (real geometry is cadpy's job).
            step_path.write_bytes(b"")
            metadata_path.write_text(json.dumps({
                "source_hash": "stub",
                "generator": "cadpy-stub",
                "validation": {"is_solid": is_solid, "volume_mm3": volume_mm3},
                "mesh_tolerance": mesh_tolerance,
                "mesh_angular_tolerance": mesh_angular_tolerance,
                "_stub": True,
            }))

            # Real STL: always written (printable + preview mesh). Keep
            # "STL > 1000 bytes" assertions meaningful by exporting the
            # CadQuery shape directly. cadpy proper meshes via OCCT; for the
            # stub we go straight through cadquery.
            stl_path = out_dir / f"{stem}.stl"
            import cadquery as cq
            cq.exporters.export(
                shape_obj, str(stl_path),
                exportType="STL",
                tolerance=mesh_tolerance,
                angularTolerance=mesh_angular_tolerance,
            )

            return {
                "step_path": step_path,
                "metadata_path": metadata_path,
                "stl_path": stl_path,
                "is_solid": is_solid,
                "volume_mm3": volume_mm3,
                "bbox": bbox,
                "mesh_tolerance": mesh_tolerance,
                "mesh_angular_tolerance": mesh_angular_tolerance,
            }
    ''').lstrip())


# Build the stub once per session and expose it to the subprocess runner
# via CADCODE_TEST_CADPY_PATH (recognized by common/runner.py).
@pytest.fixture(scope="session", autouse=True)
def _cadpy_stub() -> Path:
    stub_root = Path(tempfile.mkdtemp(prefix="cadcode-cadpy-stub-"))
    _build_stub_cadpy(stub_root)
    prev = os.environ.get("CADCODE_TEST_CADPY_PATH")
    os.environ["CADCODE_TEST_CADPY_PATH"] = str(stub_root)
    # Also make it visible to in-process imports (test_skill helper code).
    sys.path.insert(0, str(stub_root))
    try:
        yield stub_root
    finally:
        if prev is None:
            os.environ.pop("CADCODE_TEST_CADPY_PATH", None)
        else:
            os.environ["CADCODE_TEST_CADPY_PATH"] = prev
        if str(stub_root) in sys.path:
            sys.path.remove(str(stub_root))
        shutil.rmtree(stub_root, ignore_errors=True)
