"""A generated render package must describe the STEP written before it."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
CADGEN_SRC = SCRIPTS / "packages/cadgen/src"
if str(CADGEN_SRC) not in sys.path:
    sys.path.insert(0, str(CADGEN_SRC))

from cadgen._internal import generation
from cadgen._internal.generation_spec import EntrySpec


def sha256(content):
    return hashlib.sha256(content).hexdigest()


class GenerationStepProvenanceTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.step = self.root / "model.step"
        self.source = self.root / "model.step.py"
        self.source.write_text("def gen_step(): pass\n")
        self.shape = object()
        self.scene = SimpleNamespace(
            step_path=self.step, source_compound=self.shape,
            source_kind="python", source_path=self.source.name,
            source_hash="a" * 64, source_closure_hash="b" * 64,
            source_closure_files=[self.source.name], step_hash="",
        )
        self.options = SimpleNamespace(
            linear_deflection=0.1, angular_deflection=0.2, relative=False,
            edge_visibility_classes=("sharp", "boundary"), mesh_resolution=None,
        )
        self.events = []
        self.packages = []

    def generate(self, *, output="canonical", export_error=None, package_error=None):
        target = self.step if output == "canonical" else output
        spec = EntrySpec(
            source_ref=str(self.source), cad_ref=str(self.step), kind="assembly",
            source_path=self.source, display_name="model", source="generated",
            script_path=self.source, step_path=self.step, step_export_path=target,
        )

        def export(shape, path, **kwargs):
            self.assertIs(shape, self.shape)
            self.events.append("export")
            if export_error is not None:
                raise export_error
            path.write_bytes(b"new STEP bytes")
            # Preserve the previous timestamp to make the binding byte-based.
            os.utime(path, ns=(1_000_000_000, 1_000_000_000))
            return sha256(path.read_bytes())

        def package(shape, **kwargs):
            self.assertIs(shape, self.shape)
            self.events.append("package")
            self.packages.append(kwargs)
            if package_error is not None:
                raise package_error
            return {}

        with (
            mock.patch.object(generation, "_assembly_glb_package_current", return_value=False),
            mock.patch.object(generation, "_effective_step_spec_for_scene", return_value=spec),
            mock.patch.object(generation, "_selector_options_for_part", return_value=self.options),
            mock.patch("cadgen.step_export.export_build123d_step_file", side_effect=export),
            mock.patch("cadgen._internal.component_package.build_package_from_compound", side_effect=package),
            mock.patch("cadgen._internal.legacy_artifacts.prune_legacy_artifacts", return_value={"removed": [], "skipped": []}),
        ):
            result = generation._generate_part_outputs(
                spec, entries_by_step_path={}, preloaded_scene=self.scene,
                require_step_file=False, force=True,
            )
        self.assertIs(result.scene, self.scene)
        return self.packages[-1]["provenance"]

    def assert_provenance_preserved(self, provenance):
        self.assertEqual(provenance["sourceKind"], "python")
        self.assertEqual(provenance["sourcePath"], self.source.name)
        self.assertEqual(provenance["sourceHash"], self.scene.source_hash)
        self.assertEqual(provenance["sourceClosureHash"], self.scene.source_closure_hash)
        self.assertEqual(provenance["sourceClosureFiles"], [self.source.name])
        self.assertEqual(provenance["stepPath"], self.step.name)
        self.assertEqual(provenance["entryKind"], "assembly")
        self.assertEqual(provenance["mesh"], {
            "linearDeflection": 0.1, "angularDeflection": 0.2, "relative": False,
        })
        package = self.packages[-1]
        self.assertFalse(package["single_component"])
        self.assertEqual(package["root_name"], "model")
        self.assertEqual(package["linear_deflection"], 0.1)
        self.assertEqual(package["angular_deflection"], 0.2)

    def test_first_step_write_binds_completed_file(self):
        provenance = self.generate()
        self.assertEqual(provenance.get("stepHash"), sha256(self.step.read_bytes()))
        self.assertEqual(self.events, ["export", "package"])
        self.assert_provenance_preserved(provenance)

    def test_replaced_step_binds_new_bytes_even_with_unchanged_timestamp(self):
        self.step.write_bytes(b"old STEP bytes")
        os.utime(self.step, ns=(1_000_000_000, 1_000_000_000))
        before = self.step.stat()
        provenance = self.generate()
        self.assertEqual(self.step.stat().st_mtime_ns, before.st_mtime_ns)
        self.assertEqual(self.step.stat().st_size, before.st_size)
        self.assertEqual(provenance["stepHash"], sha256(self.step.read_bytes()))
        self.assertNotEqual(provenance["stepHash"], sha256(b"old STEP bytes"))
        self.assertEqual(self.events, ["export", "package"])
        self.assert_provenance_preserved(provenance)

    def test_failed_export_does_not_write_a_package(self):
        self.step.write_bytes(b"old STEP bytes")
        with self.assertRaisesRegex(OSError, "export failed"):
            self.generate(export_error=OSError("export failed"))
        self.assertEqual(self.events, ["export"])
        self.assertFalse(self.packages)
        self.assertEqual(self.step.read_bytes(), b"old STEP bytes")

    def test_package_failure_propagates_after_completed_export(self):
        with self.assertRaisesRegex(OSError, "package failed"):
            self.generate(package_error=OSError("package failed"))
        self.assertEqual(self.events, ["export", "package"])
        self.assertEqual(self.packages[-1]["provenance"]["stepHash"], sha256(self.step.read_bytes()))

    def test_alternate_export_keeps_canonical_step_path_and_hash(self):
        self.step.write_bytes(b"canonical STEP bytes")
        alternate = self.root / "delivery.step"
        provenance = self.generate(output=alternate)
        self.assertEqual(provenance["stepHash"], sha256(self.step.read_bytes()))
        self.assertNotEqual(provenance["stepHash"], sha256(alternate.read_bytes()))
        self.assert_provenance_preserved(provenance)

    def test_package_without_export_keeps_existing_step_binding(self):
        self.step.write_bytes(b"canonical STEP bytes")
        provenance = self.generate(output=None)
        self.assertEqual(self.events, ["package"])
        self.assertEqual(provenance["stepHash"], sha256(self.step.read_bytes()))
        self.assert_provenance_preserved(provenance)


class GenerationStepProvenanceCliTest(unittest.TestCase):
    def test_cli_first_write_and_geometry_regeneration_bind_actual_step(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "model.step.py"
            previous_hash = None
            for width in (2, 5):
                source.write_text(
                    "from build123d import Box, Compound, Pos\n"
                    "def gen_step():\n"
                    f"    left = Box({width}, 3, 4)\n"
                    "    left.label = 'left'\n"
                    "    right = Pos(20, 0, 0) * Box(1, 2, 3)\n"
                    "    right.label = 'right'\n"
                    "    return Compound(children=[left, right], label='model')\n"
                )
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / "gen"), str(source),
                     "--write", "--force", "--json"],
                    cwd=root, capture_output=True, text=True, timeout=60,
                    env={**os.environ, "CADGEN_WARM": "0", "PYTHONDONTWRITEBYTECODE": "1",
                         "PYTHONPATH": str(CADGEN_SRC)},
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                step = root / "model.step"
                descriptor = json.loads((root / "__cadgen__/models/model.step.py/assembly.json").read_text())
                current_hash = sha256(step.read_bytes())
                self.assertEqual(descriptor.get("stepHash"), current_hash)
                self.assertNotEqual(current_hash, previous_hash)
                self.assertEqual(descriptor["stepPath"], step.name)
                self.assertEqual(descriptor["sourceKind"], "python")
                self.assertEqual(descriptor["entryKind"], "assembly")
                self.assertEqual({part["name"] for part in descriptor["occurrences"]}, {"left", "right"})
                from build123d import import_step
                restored = import_step(step)
                self.assertTrue(restored.is_valid)
                self.assertAlmostEqual(restored.volume, width * 3 * 4 + 6)
                previous_hash = current_hash


if __name__ == "__main__":
    unittest.main()
