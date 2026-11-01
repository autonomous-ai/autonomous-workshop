from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PACKAGE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cadgen._internal import generation as generation_module
from cadgen._internal.generation import GeneratedStepResult, generate_step_targets
from cadgen._internal.generation_spec import EntrySpec
from cadgen._internal.source_hash import closure_for_files, python_source_hash
from cadgen._internal.step_metadata import inject_text_to_cad_step_metadata


# A hand-written, kernel-free STEP document: just enough entities for
# inject_text_to_cad_step_metadata's regexes (SHAPE_DEFINITION_REPRESENTATION ->
# PRODUCT_DEFINITION_SHAPE, and ADVANCED_BREP_SHAPE_REPRESENTATION) to find their
# insertion point, so these tests exercise real STEP-metadata read/write without
# build123d/OCP.
_MINIMAL_STEP_TEXT = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION((''),'2;1');
FILE_NAME('demo','1970-01-01T00:00:00',('Author'),('Org'),'proc','cadgen','Unknown');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));
ENDSEC;
DATA;
#1 = APPLICATION_CONTEXT('core data');
#2 = PRODUCT_DEFINITION_CONTEXT('part definition',#1,'design');
#3 = PRODUCT_CONTEXT('',#1,'mechanical');
#4 = ( GEOMETRIC_REPRESENTATION_CONTEXT(3)
GLOBAL_UNIT_ASSIGNED_CONTEXT((#5)) REPRESENTATION_CONTEXT('',''));
#5 = ( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) );
#10 = SHAPE_DEFINITION_REPRESENTATION(#11,#15);
#11 = PRODUCT_DEFINITION_SHAPE('','',#12);
#12 = PRODUCT_DEFINITION('design','',#13,#2);
#13 = PRODUCT_DEFINITION_FORMATION('','',#14);
#14 = PRODUCT('part','part','',(#3));
#15 = ADVANCED_BREP_SHAPE_REPRESENTATION('',(#16),#4);
#16 = MANIFOLD_SOLID_BREP('',#17);
#17 = CLOSED_SHELL('',());
ENDSEC;
END-ISO-10303-21;
"""

# ast-parsed only (never executed), so it needs no build123d import: a bare Call
# return that isn't Compound(...) resolves to kind="part".
_GENERATOR_SOURCE = "def gen_step():\n    return object()\n"


def _last_json_line(text: str) -> dict:
    return json.loads(text.strip().splitlines()[-1])


def _write_generator(root: Path) -> Path:
    script_path = root / "entry.step.py"
    script_path.write_text(_GENERATOR_SOURCE)
    return script_path


def _write_step(step_path: Path, *, source_hash: str) -> None:
    step_path.write_text(_MINIMAL_STEP_TEXT)
    inject_text_to_cad_step_metadata(step_path, entry_kind="part", source_hash=source_hash)


def _write_current_step(step_path: Path, *, script_path: Path) -> None:
    _write_step(step_path, source_hash=python_source_hash(script_path).source_hash)


_TOOLCHAIN = {"build123d": "0.11.1", "cadquery_ocp": "7.9.3.1.1"}
_IDENTITY = "b" * 64


def _write_colours(root: Path, colour: str = "mint") -> Path:
    colours = root / "colours.py"
    colours.write_text(f'"""Filament choices."""\nHEAD = ("{colour}", "catalogue")\n')
    return colours


def _record_export(spec: EntrySpec, *, identity: str = _IDENTITY, extra: tuple[Path, ...] = ()) -> None:
    """Record ``spec``'s on-disk export the way ``gen --write`` does after
    exporting a build of ``identity`` whose closure is the entry plus ``extra``."""
    closure = closure_for_files(spec.script_path, list(extra), base=spec.step_export_path.parent)
    scene = SimpleNamespace(
        source_compound=SimpleNamespace(wrapped=object()),
        source_closure_hash=closure.closure_hash,
        source_closure_files=closure.files,
    )
    with patch("cadgen.inspection_runtime.shape_identity", return_value=identity), \
        patch.object(generation_module, "_installed_toolchain_versions", return_value=_TOOLCHAIN):
        generation_module._write_step_export_record(spec, scene)


def _entry_spec(script_path: Path, step_export_path: Path | None) -> EntrySpec:
    return EntrySpec(
        source_ref="entry",
        cad_ref="entry",
        kind="part",
        source_path=script_path,
        display_name="entry",
        source="generated",
        script_path=script_path,
        step_export_path=step_export_path,
    )


class StepExportIsCurrentTest(unittest.TestCase):
    """Unit coverage for the new predicate, independent of the CLI seam below."""

    def test_missing_step_export_path_is_not_current(self) -> None:
        spec = _entry_spec(Path("entry.step.py"), step_export_path=None)
        self.assertFalse(generation_module._step_export_is_current(spec))

    def test_missing_step_file_is_not_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = _entry_spec(_write_generator(root), step_export_path=root / "entry.step")
            self.assertFalse(generation_module._step_export_is_current(spec))

    def _is_current(self, spec: EntrySpec) -> bool:
        with patch.object(generation_module, "_installed_toolchain_versions", return_value=_TOOLCHAIN):
            return generation_module._step_export_is_current(spec)

    def test_recorded_export_of_an_unchanged_closure_is_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            colours = _write_colours(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)
            spec = _entry_spec(script_path, step_export_path=step_path)
            _record_export(spec, extra=(colours,))
            self.assertTrue(self._is_current(spec))
            with patch.object(generation_module, "_installed_toolchain_versions", return_value=_TOOLCHAIN):
                record = generation_module._current_step_export_record(spec)
            self.assertEqual(record["identitySha256"], _IDENTITY)
            self.assertEqual(record["toolchainVersions"], _TOOLCHAIN)

    def test_an_export_with_only_its_embedded_source_hash_is_not_current(self) -> None:
        # Issue #165: the embedded hash names the entry file alone, and the
        # render package can be recomposed without rewriting the export.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)
            spec = _entry_spec(script_path, step_export_path=step_path)
            self.assertFalse(self._is_current(spec))

    def test_a_recolour_leaves_the_export_not_current(self) -> None:
        # Issue #165: the Colour Module is in the closure, not the entry file.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            colours = _write_colours(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)
            spec = _entry_spec(script_path, step_export_path=step_path)
            _record_export(spec, extra=(colours,))
            _write_colours(root, colour="green")
            self.assertFalse(self._is_current(spec))

    def test_other_bytes_at_the_export_path_are_not_current(self) -> None:
        # A STEP put back or restored from elsewhere is not the recorded export.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)
            spec = _entry_spec(script_path, step_export_path=step_path)
            _record_export(spec)
            step_path.write_text(step_path.read_text().replace("'demo'", "'other'"))
            self.assertFalse(self._is_current(spec))

    def test_an_export_recorded_under_another_toolchain_is_not_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)
            spec = _entry_spec(script_path, step_export_path=step_path)
            _record_export(spec)
            with patch.object(generation_module, "_installed_toolchain_versions",
                              return_value={**_TOOLCHAIN, "build123d": "0.12.0"}):
                self.assertFalse(generation_module._step_export_is_current(spec))

    def test_an_unreadable_or_foreign_record_is_not_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)
            spec = _entry_spec(script_path, step_export_path=step_path)
            _record_export(spec)
            record_path = generation_module._step_export_record_path(spec)
            for content in ("{not json", json.dumps({"schemaVersion": 99}), "[]"):
                record_path.write_text(content)
                self.assertFalse(self._is_current(spec), content)

    def test_a_build_with_no_fresh_shape_removes_the_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)
            spec = _entry_spec(script_path, step_export_path=step_path)
            _record_export(spec)
            record_path = generation_module._step_export_record_path(spec)
            self.assertTrue(record_path.is_file())
            self.assertEqual(record_path.parent.name, "step-exports")
            self.assertEqual(record_path.parent.parent.name, "__cadgen__")
            generation_module._write_step_export_record(spec, SimpleNamespace(source_compound=None))
            self.assertFalse(record_path.exists())
            self.assertFalse(self._is_current(spec))

    def test_step_with_stale_recorded_hash_is_not_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"
            _write_step(step_path, source_hash="not-the-current-script-hash")
            spec = _entry_spec(script_path, step_export_path=step_path)
            self.assertFalse(generation_module._step_export_is_current(spec))


class GenWriteSkipsCurrentEntryTest(unittest.TestCase):
    """Seam coverage for ``scripts/gen --write``: :func:`generate_step_targets`
    must take the existing 'current' fast path when the closure and the STEP it
    would write are both already current, and must not otherwise."""

    def _run_gen_write(
        self,
        script_path: Path,
        step_path: Path,
        *,
        closure_current: bool,
        force: bool = False,
    ) -> tuple[int, str, list[EntrySpec]]:
        """Run ``generate_step_targets`` for one ``script=step`` target with the
        closure check stubbed; returns the exit code, the last JSON outcome, and
        every spec the (stubbed) build was asked to produce."""
        exit_code, line, built = self._run_gen_write_line(
            script_path, step_path, closure_current=closure_current, force=force
        )
        return exit_code, line["outcome"], built

    def _run_gen_write_line(
        self,
        script_path: Path,
        step_path: Path,
        *,
        closure_current: bool,
        force: bool = False,
        stub_build=None,
    ) -> tuple[int, dict, list[EntrySpec]]:
        built: list[EntrySpec] = []

        def _stub_build(spec, **kwargs):
            built.append(spec)
            if stub_build is not None:
                return stub_build(spec)
            return GeneratedStepResult(spec=spec, scene=None)

        with patch.object(generation_module, "_assembly_is_current", return_value=closure_current), \
            patch.object(generation_module, "_assembly_glb_package_current", return_value=True), \
            patch.object(generation_module, "_generate_step_outputs_for_cli", side_effect=_stub_build), \
            patch.object(generation_module, "_installed_toolchain_versions", return_value=_TOOLCHAIN), \
            redirect_stdout(StringIO()) as out:
            exit_code = generate_step_targets(
                [f"{script_path}={step_path}"], force=force, json_output=True
            )
        return exit_code, _last_json_line(out.getvalue()), built

    def _recorded(self, script_path: Path, step_path: Path, **kwargs) -> None:
        _record_export(_entry_spec(script_path, step_export_path=step_path), **kwargs)

    def test_unchanged_closure_and_current_step_reports_current_and_leaves_step_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)
            self._recorded(script_path, step_path)
            original_bytes = step_path.read_bytes()

            exit_code, line, built = self._run_gen_write_line(script_path, step_path, closure_current=True)

            self.assertEqual(exit_code, 0)
            self.assertEqual(line["outcome"], "current")
            self.assertEqual(built, [])
            self.assertEqual(step_path.read_bytes(), original_bytes)
            # Issue #166: a current export still reports the B-rep identity of
            # the shape it was built from, never leaving only its bytes to hash.
            self.assertEqual(line["identitySha256"], _IDENTITY)
            self.assertEqual(line["toolchainVersions"], _TOOLCHAIN)

    def test_a_re_export_of_the_same_shape_reports_the_same_identity_when_current(self) -> None:
        # Issue #166: `gen --write --force` rewrites the export's bytes; the
        # next current run reports the identity of the shape, not the bytes.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)
            self._recorded(script_path, step_path)
            first = self._run_gen_write_line(script_path, step_path, closure_current=True)[1]
            step_path.write_text(step_path.read_text().replace("1970-01-01T00:00:00", "2026-10-31T15:00:00"))
            self._recorded(script_path, step_path)
            second = self._run_gen_write_line(script_path, step_path, closure_current=True)[1]
            self.assertEqual((first["outcome"], second["outcome"]), ("current", "current"))
            self.assertEqual(first["identitySha256"], second["identitySha256"])

    def test_a_recolour_rebuilds_the_export_although_the_package_is_current(self) -> None:
        # Issue #165: the render package was recomposed in the new colour, so
        # its closure is current; the export was not, so --write builds again.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            colours = _write_colours(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)
            self._recorded(script_path, step_path, extra=(colours,))
            _write_colours(root, colour="green")

            def rebuilt(spec):
                scene = SimpleNamespace(source_compound=SimpleNamespace(wrapped=object()))
                return GeneratedStepResult(spec=spec, scene=scene)

            with patch("cadgen.inspection_runtime.shape_identity", return_value=_IDENTITY):
                exit_code, line, built = self._run_gen_write_line(
                    script_path, step_path, closure_current=True, stub_build=rebuilt
                )
            self.assertEqual(exit_code, 0)
            self.assertEqual(len(built), 1)
            self.assertEqual(line["outcome"], "built")
            self.assertEqual(line["identitySha256"], _IDENTITY)

    def test_changed_closure_regenerates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)

            exit_code, outcome, built = self._run_gen_write(script_path, step_path, closure_current=False)

            self.assertEqual(exit_code, 0)
            self.assertEqual(len(built), 1)
            self.assertEqual(outcome, "built")

    def test_force_regenerates_even_when_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"
            _write_current_step(step_path, script_path=script_path)

            exit_code, outcome, built = self._run_gen_write(
                script_path, step_path, closure_current=True, force=True
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(len(built), 1)
            self.assertEqual(outcome, "built")

    def test_missing_step_regenerates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"  # never written

            exit_code, outcome, built = self._run_gen_write(script_path, step_path, closure_current=True)

            self.assertEqual(exit_code, 0)
            self.assertEqual(len(built), 1)
            self.assertEqual(outcome, "built")

    def test_stale_step_regenerates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = _write_generator(root)
            step_path = root / "entry.step"
            _write_step(step_path, source_hash="stale-hash-from-a-prior-script")

            exit_code, outcome, built = self._run_gen_write(script_path, step_path, closure_current=True)

            self.assertEqual(exit_code, 0)
            self.assertEqual(len(built), 1)
            self.assertEqual(outcome, "built")


if __name__ == "__main__":
    unittest.main()
