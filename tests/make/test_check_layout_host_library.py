"""check_layout does not count a host-installed library as project code (#103)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2] / "src" / "workshop" / "make" / "skills"
CHECK_LAYOUT = SKILLS / "cad" / "scripts" / "check_layout"
PRINT_DETAILS = SKILLS / "print-details" / "scripts" / "print_details.py"


def run_layout(project: Path) -> dict:
    done = subprocess.run(
        [sys.executable, str(CHECK_LAYOUT), str(project), "--json"],
        capture_output=True, text=True, check=False,
    )
    return {"returncode": done.returncode, "report": json.loads(done.stdout)}


def oversized(result: dict) -> list:
    report = result["report"]
    findings = report.get("findings", report) if isinstance(report, dict) else report
    return [item for item in findings if item.get("rule") == "oversized-library"]


class HostLibraryTest(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.project)
        (self.project / "features").mkdir()
        (self.project / "features" / "__init__.py").write_text("")
        (self.project / "part_a.step.py").write_text("def gen_step():\n    return None\n")
        (self.project / "toy.step.py").write_text("def gen_step():\n    return None\n")

    def test_installed_library_is_not_counted(self):
        self.assertGreater(len(PRINT_DETAILS.read_text().splitlines()), 400)
        shutil.copyfile(PRINT_DETAILS, self.project / "features" / "print_details.py")
        result = run_layout(self.project)
        self.assertEqual(oversized(result), [])
        self.assertEqual(result["returncode"], 0)

    def test_modified_copy_is_still_counted(self):
        text = PRINT_DETAILS.read_text() + "\nEXTRA = 1\n"
        (self.project / "features" / "print_details.py").write_text(text)
        result = run_layout(self.project)
        self.assertEqual(
            [item["path"] for item in oversized(result)], ["features/print_details.py"]
        )
        self.assertEqual(result["returncode"], 1)

    def test_own_oversized_module_is_still_counted(self):
        body = "".join("VALUE_%d = %d\n" % (n, n) for n in range(450))
        (self.project / "features" / "mine.py").write_text(body)
        shutil.copyfile(PRINT_DETAILS, self.project / "features" / "print_details.py")
        result = run_layout(self.project)
        self.assertEqual([item["path"] for item in oversized(result)], ["features/mine.py"])


if __name__ == "__main__":
    unittest.main()
