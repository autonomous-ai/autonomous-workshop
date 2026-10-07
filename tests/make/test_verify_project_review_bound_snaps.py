"""Issue #109: final verification never writes a file a review or the
finalizer binds.

The image-derived final run renders its orthogonal views with render_views.
They used to land in ``snap/``, overwriting the composed Hero ``snap/iso.png``
that the signature review binds by hash, so the next run refused in preflight
with ``signature review is stale for snap/iso.png``.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import runpy
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"

# Every snap file a review or the Make finalizer binds.
REVIEW_BOUND = ("iso.png", "signature.png", "SIGNATURE-REVIEW.json", "motion.gif",
                "MOTION-EVIDENCE.json", "MOTION-REVIEW.json")


class ImageDerivedFinalKeepsReviewBoundSnapsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name).resolve() / "cad"
        (self.project / "snap").mkdir(parents=True)
        (self.project / "measure").mkdir()
        (self.project / "toy.step.py").write_text("PRINTABLE = False\ndef gen_step(): return None\n")
        for name in REVIEW_BOUND:
            (self.project / "snap" / name).write_bytes(("composed " + name).encode())
        self.verifier = runpy.run_path(str(SCRIPTS / "verify_project"))

    def _final(self):
        verifier = self.verifier
        rendered = []

        class FakeRunner(verifier["Runner"]):
            """Stands in for the tools only: render_views writes its views where
            its -o argument says, exactly as the real tool does."""

            def command(self, argv, **_kwargs):
                args = [str(item) for item in argv]
                if Path(args[1]).name == "render_views.py":
                    out = Path(args[args.index("-o") + 1])
                    if not out.is_absolute():
                        out = self.cwd / out
                    out.mkdir(parents=True, exist_ok=True)
                    views = [args[i + 1] for i, arg in enumerate(args) if arg == "--view"]
                    for view in views:
                        (out / (view + ".png")).write_bytes(b"silhouette " + view.encode())
                    rendered.append(out)
                return 0

            def inspect_batch(self, requests):
                return 0

        runner = FakeRunner(cwd=self.project, dry_run=False, verbose=False)
        before = {name: hashlib.sha256((self.project / "snap" / name).read_bytes()).hexdigest()
                  for name in REVIEW_BOUND}
        with contextlib.redirect_stdout(io.StringIO()):
            code = verifier["_final"](
                runner, self.project, self.project / "toy.step.py", [], [],
                motion_manifest=None, check_motion=False, strict_fit=False, strict_mount=False,
                print_gates=False, bed=(256.0, 256.0, 256.0), nozzle=0.4, skip_thickness=False,
                overhang_angle=45.0, image_derived=True, skip_gen=True)
        after = {name: hashlib.sha256((self.project / "snap" / name).read_bytes()).hexdigest()
                 for name in REVIEW_BOUND}
        return code, before, after, rendered

    def test_the_image_derived_path_leaves_every_review_bound_snap_byte_identical(self):
        code, before, after, rendered = self._final()
        self.assertEqual(code, 0)
        self.assertEqual(len(rendered), 1)
        self.assertEqual(after, before)
        # The silhouettes go to their own verification directory instead.
        out = rendered[0]
        self.assertEqual(out, self.project / "measure" / "verification-views")
        self.assertEqual(sorted(p.name for p in out.iterdir()),
                         ["front.png", "iso.png", "right.png", "top.png"])
        self.assertEqual(sorted(p.name for p in (self.project / "snap").iterdir()), sorted(REVIEW_BOUND))

    def test_the_signature_review_stays_current_and_still_refuses_a_changed_hero(self):
        self.project = self.verifier["_sc_project"](self.project.parent)
        (self.project / "toy.step.py").write_text("PRINTABLE = False\ndef gen_step(): return None\n")
        required = self.verifier["_required_signature_review"]
        bound = required(self.project)
        code, before, after, _rendered = self._final_on_fixture()
        self.assertEqual(code, 0)
        self.assertEqual(after, before)
        # The next run's preflight finds the review current.
        self.assertEqual(required(self.project), bound)
        (self.project / "snap/iso.png").write_bytes(b"a different hero")
        with self.assertRaisesRegex(ValueError, "stale for snap/iso.png"):
            required(self.project)

    def _final_on_fixture(self):
        for name in REVIEW_BOUND:
            path = self.project / "snap" / name
            if not path.exists():
                path.write_bytes(("composed " + name).encode())
        return self._final()

if __name__ == "__main__":
    unittest.main()
