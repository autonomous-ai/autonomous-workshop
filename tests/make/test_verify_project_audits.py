"""Local CAD audits must retain access to the same bundled tools as generators."""
from __future__ import annotations

import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


class VerifyProjectAuditEnvironmentTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / "project with spaces"
        (self.project / "measure").mkdir(parents=True)
        self.verifier = runpy.run_path(str(SCRIPTS / "verify_project"))

    def run_audit(self, source, *, verifier=None, pythonpath=""):
        audit = self.project / "measure/check_fit.py"
        audit.write_text(source, encoding="utf-8")
        env = dict(os.environ, PYTHONPATH=pythonpath, PYTHONDONTWRITEBYTECODE="1")
        with mock.patch.dict(os.environ, env, clear=True):
            env.update((verifier or self.verifier)["_audit_env"](self.project))
        return subprocess.run(
            [sys.executable, str(audit)], cwd=self.root, env=env,
            capture_output=True, text=True, timeout=10, check=False,
        )

    def test_nested_audit_imports_project_module_and_bundled_fit_helper(self):
        (self.project / "dimensions.py").write_text("PIN_DIAMETER = 4.0\n")
        result = self.run_audit(
            "from dimensions import PIN_DIAMETER\n"
            "import cadfits\n"
            "assert cadfits.slot_for(PIN_DIAMETER, 'slip') == 4.4\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_relocated_verifier_uses_its_own_materialized_helper(self):
        scripts = self.root / "isolated run/.agents/skills/cad/scripts"
        scripts.mkdir(parents=True)
        for name in ("verify_project", "cadfits.py"):
            shutil.copy2(SCRIPTS / name, scripts / name)
        verifier = runpy.run_path(str(scripts / "verify_project"))
        result = self.run_audit(
            "from pathlib import Path\n"
            "import cadfits\n"
            f"assert Path(cadfits.__file__).resolve() == Path({str(scripts / 'cadfits.py')!r})\n",
            verifier=verifier,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bundled_helper_precedes_a_project_module_with_the_same_name(self):
        (self.project / "cadfits.py").write_text("raise RuntimeError('shadow helper')\n")
        result = self.run_audit("import cadfits\nassert cadfits.slot_for(4, 'slip') == 4.4\n")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_fit_still_fails_after_successful_import(self):
        result = self.run_audit("import cadfits\ncadfits.slot_for(4, 'not-a-fit')\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown fit class", result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_existing_pythonpath_dependencies_remain_available(self):
        dependency = self.root / "existing dependency"
        dependency.mkdir()
        (dependency / "audit_dependency.py").write_text("EXPECTED = 4.4\n")
        result = self.run_audit(
            "import cadfits, audit_dependency\n"
            "assert cadfits.slot_for(4, 'slip') == audit_dependency.EXPECTED\n",
            pythonpath=str(dependency),
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
