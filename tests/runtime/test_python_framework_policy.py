import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.runtime import codex as runtime


class PythonFrameworkPolicyTest(unittest.TestCase):
    def test_framework_install_name_uses_framework_prefix_not_libdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "Python.framework/Versions/3.14/Python"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"framework")
            config = {"PYTHONFRAMEWORK": "Python", "PYTHONFRAMEWORKPREFIX": str(root),
                      "INSTSONAME": "Python.framework/Versions/3.14/Python"}
            with mock.patch.object(runtime.sysconfig, "get_config_var", side_effect=config.get):
                self.assertEqual(runtime._python_framework_library(), binary.resolve())
                binary.unlink()
                with self.assertRaisesRegex(runtime.CodexInvocationError, "unavailable"):
                    runtime._python_framework_library()

    def test_launcher_walk_tracks_alias_directories_without_granting_formula_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            venv = root / "venv/bin"
            formula = root / "Cellar/python/1"
            opt = root / "opt"
            for path in (venv, formula / "bin", formula / "framework/bin", opt):
                path.mkdir(parents=True)
            executable = formula / "framework/bin/python"
            executable.write_bytes(b"python")
            (formula / "bin/python").symlink_to("../framework/bin/python")
            (opt / "python").symlink_to(formula, target_is_directory=True)
            (venv / "python").symlink_to(opt / "python/bin/python")
            with mock.patch.object(runtime.sys, "executable", str(venv / "python")), mock.patch.object(
                runtime.sysconfig, "get_config_var", return_value="Python"
            ):
                paths = set(runtime._python_framework_launcher_directories())
            self.assertEqual(paths, {opt, formula / "bin"})
            self.assertNotIn(formula, paths)
            self.assertNotIn(root, paths)

    def test_linked_library_closure_is_bounded_and_credential_free(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            stdlib = root / "stdlib"
            (stdlib / "lib-dynload").mkdir(parents=True)
            (stdlib / "lib-dynload/_sqlite3.so").write_bytes(b"extension")
            library = root / "sqlite/lib/libsqlite3.dylib"
            library.parent.mkdir(parents=True)
            library.write_bytes(b"library")
            output = f"\t{library} (compatibility version 1.0.0)\n\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0)\n"
            with mock.patch.object(runtime.sys, "platform", "darwin"), mock.patch.object(
                runtime.sysconfig, "get_config_var", return_value="Python"
            ), mock.patch.object(runtime.sysconfig, "get_path", return_value=str(stdlib)), mock.patch.object(
                runtime, "_python_framework_library", return_value=None
            ), mock.patch.object(runtime.subprocess, "run", return_value=mock.Mock(stdout=output)) as run:
                self.assertEqual(set(runtime._python_framework_dependencies()), {library, library.parent})
                self.assertEqual(run.call_count, 2)
                self.assertNotIn("FACTORY_PASSWORD", run.call_args.kwargs["env"])
                run.side_effect = subprocess.TimeoutExpired("otool", 10)
                with self.assertRaisesRegex(runtime.CodexInvocationError, "Cannot inspect"):
                    runtime._python_framework_dependencies()

    def test_non_framework_python_needs_no_macho_discovery(self):
        with mock.patch.object(runtime.sysconfig, "get_config_var", return_value=None), mock.patch.object(
            runtime.subprocess, "run"
        ) as run:
            self.assertIsNone(runtime._python_framework_library())
            self.assertEqual(runtime._python_framework_launcher_directories(), ())
            self.assertEqual(runtime._python_framework_dependencies(), ())
        run.assert_not_called()

    @unittest.skipUnless(os.environ.get("WORKSHOP_SANDBOX_TEST_BIN"), "explicit local Codex sandbox probe")
    def test_real_sandbox_cad_and_finalizer(self):
        binary = os.environ["WORKSHOP_SANDBOX_TEST_BIN"]
        with tempfile.TemporaryDirectory(prefix="workshop-sandbox-test-") as tmp:
            root = Path(tmp).resolve()
            (root / runtime.PRODUCT_RUN_ROOT_MARKER).write_text("probe")
            (root / ".env.probe").write_text("test-only")
            source = Path(__file__).resolve().parents[2] / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py"
            shutil.copyfile(source, root / "stage_proposal.py")
            policy = runtime._codex_run_policy(root, binary)
            env = runtime._codex_run_environment(root, policy)
            script = """
import sys, ssl, sqlite3, ctypes, subprocess
from pathlib import Path
from build123d import Box, export_step
export_step(Box(2, 3, 4), "probe.step")
assert Path("probe.step").stat().st_size > 100
subprocess.run([sys.executable, "stage_proposal.py", "--help"], check=True)
try:
    Path(".env.probe").read_text()
except PermissionError:
    print("SANDBOX_CAD_FINALIZER_ISOLATION_OK")
else:
    raise AssertionError("secret file was readable")
"""
            result = subprocess.run(
                [binary, "sandbox", "-P", runtime.CODEX_PERMISSION_PROFILE,
                 "-C", str(root), *policy.permission_config_arguments,
                 "--", env["WORKSHOP_PYTHON"], "-c", script],
                env=env, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SANDBOX_CAD_FINALIZER_ISOLATION_OK", result.stdout)
