"""A detailed assembly's motion states are bound by hash, never by a byte cap (#93).

The motion animation is a presentation artifact. It must never refuse a
detailed assembly and push the run into changing locked, contract-required
geometry just to fit, and it must still refuse a state that differs from the
declared poses.
"""
import hashlib
import json
import runpy
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
OLD_LIMIT = 20 * 1024 * 1024

# 56 round rivets: a sphere tessellates to about 8,000 triangles at any size,
# so this frame alone is about 448k triangles, above the ~419k the old 20 MiB
# state limit allowed.
MODEL = '''from build123d import Box, Compound, Sphere
def gen_step():
    driver = Box(2, 1, 1).translate((4, 0, 0))
    driver.label = "driver"
    driver.color = (0.8, 0.05, 0.01)
    rivets = Compound([Sphere(0.5).translate((i * 1.2, j * 1.2, -3))
                       for i in range(8) for j in range(7)])
    rivets.label = "frame"
    rivets.color = (0.01, 0.1, 0.8)
    return Compound(children=[driver, rivets], label="root")
'''

CONDITION = {"id": "turn", "check": "coupled_motion_collision", "inputs": {
    "steps": 8, "movers": [{"part": "driver", "rotation": {
        "axis_point": [0, 0, 0], "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": 90}}],
    "obstacle_parts": ["frame"]}}

SIGNATURE = {"concept_sha256": "a" * 64, "reviewer": "synthetic-test-critic", "review_rounds": 1}


class DetailedMotionStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = runpy.run_path(str(TOOLS / "motion_presentation.py"))
        cls.tool = cls.helper["state_tool"]()
        cls.root = Path(tempfile.mkdtemp())
        cls.project = cls.root / "generated"
        (cls.project / "measure").mkdir(parents=True)
        (cls.project / "model.step.py").write_text(MODEL)
        (cls.project / "measure/motion.json").write_text(
            json.dumps({"assembly": "model.step.py", "conditions": [CONDITION]}))
        sizes = []
        encode = cls.tool["state_bytes"]

        def measured(occurrences):
            data = encode(occurrences)
            sizes.append(len(data))
            return data

        with mock.patch.dict(cls.tool, {"state_bytes": measured}):
            cls.evidence = cls.helper["generate"](cls.project, size=256)
        cls.sizes = sizes
        cls.review(cls.project, cls.evidence)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    @classmethod
    def review(cls, project, evidence):
        raw = cls.helper["canonical"](evidence)
        (project / cls.helper["EVIDENCE"]).write_bytes(raw)
        review = {"schema_version": 1, **SIGNATURE, "evidence_sha256": hashlib.sha256(raw).hexdigest(),
                  "blind_motion_read": "Synthetic fixture: the block turns above a riveted plate.",
                  "motion_matches_wish": True, "simulation_not_physical_test": True}
        (project / cls.helper["REVIEW"]).write_bytes(cls.helper["canonical"](review))

    def copy(self, name):
        target = self.root / name
        shutil.copytree(self.project, target)
        return target

    def test_state_over_the_old_limit_generates_and_validates(self):
        self.assertEqual(len(self.sizes), 8)
        self.assertGreater(min(self.sizes), OLD_LIMIT)
        self.assertEqual(len(self.evidence["states"]), 8)
        self.helper["validate"](self.copy("valid"), SIGNATURE)

    def test_changed_state_still_fails_the_hash_binding(self):
        project = self.copy("changed")
        evidence = json.loads((project / self.helper["EVIDENCE"]).read_bytes())
        state = evidence["states"][3]
        state["sha256"] = hashlib.sha256(bytes.fromhex(state["sha256"]) + b"changed").hexdigest()
        self.review(project, evidence)
        with self.assertRaisesRegex(ValueError, r"motion state turn\[\d+\] differs from the checked poses"):
            self.helper["validate"](project, SIGNATURE)


if __name__ == "__main__":
    unittest.main()
