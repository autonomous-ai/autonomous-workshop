"""An entry that imports an older installed cadgen must still render.

A run's interpreter puts the project virtualenv on PYTHONPATH, and that
virtualenv carries the published cadgen, which lacks the skill's own
`cadgen.inspection_runtime`. When a component entry imported cadgen before the
renderer put the skill's copy first, every review render of that component
crashed (wish-20260928-101512-dff4cebe: 12 of 13 component rounds).
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


RENDERER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/render_review"


class CadgenShadowTest(unittest.TestCase):
    def render(self, entry_source: str, shadow: Path, project: Path):
        entry = project / "part_block.step.py"
        entry.write_text(entry_source, encoding="utf-8")
        environment = dict(os.environ)
        environment["PYTHONPATH"] = os.pathsep.join(
            [str(shadow), *filter(None, [environment.get("PYTHONPATH")])]
        )
        return subprocess.run(
            [sys.executable, str(RENDERER), str(entry), "--view", "iso", "--size", "160",
             "-o", str(project / "out")],
            capture_output=True, text=True, env=environment, timeout=300,
        )

    def test_entry_importing_cadgen_renders_with_the_skill_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            shadow = root / "site"
            (shadow / "cadgen").mkdir(parents=True)
            (shadow / "cadgen" / "__init__.py").write_text("SHADOW = True\n", encoding="utf-8")
            project = root / "cad"
            project.mkdir()
            done = self.render(
                "import cadgen\n"
                "from build123d import Box\n"
                "assert not getattr(cadgen, 'SHADOW', False), 'the installed cadgen won'\n"
                "def gen_step():\n"
                "    return Box(4, 3, 2)\n",
                shadow, project,
            )
            self.assertEqual(done.returncode, 0, done.stderr[-800:])
            self.assertTrue((project / "out" / "iso.png").is_file())


if __name__ == "__main__":
    unittest.main()
