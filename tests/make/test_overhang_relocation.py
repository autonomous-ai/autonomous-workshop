import importlib.machinery
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "src/workshop/make/skills/cad/scripts/check_overhang"


class OverhangRelocationTest(unittest.TestCase):
    def test_report_survives_relocation_but_binds_geometry_and_parameters(self):
        sys.path.insert(0, str(SCRIPT.parent))
        self.addCleanup(sys.path.remove, str(SCRIPT.parent))
        loader = importlib.machinery.SourceFileLoader("overhang_relocation", str(SCRIPT))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            reports = []
            for folder, size, angle in (("product/sword", 10, 45), ("project", 10, 45),
                                        ("changed", 12, 45), ("profile", 10, 30)):
                target = base / folder
                target.mkdir(parents=True)
                triangles = module._box(0, 0, 0, size, 10, 10)
                text = "solid cube\n"
                for triangle in triangles:
                    text += "facet normal 0 0 0\nouter loop\n"
                    for vertex in triangle:
                        text += "vertex %s %s %s\n" % tuple(vertex)
                    text += "endloop\nendfacet\n"
                (target / "part.stl").write_text(text + "endsolid cube\n")
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), folder + "/part.stl", "--angle", str(angle),
                     "--report", folder + "/report.md"], cwd=base,
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                reports.append((target / "report.md").read_bytes())
            self.assertEqual(reports[0], reports[1])
            self.assertNotEqual(reports[1], reports[2])
            self.assertNotEqual(reports[1], reports[3])
