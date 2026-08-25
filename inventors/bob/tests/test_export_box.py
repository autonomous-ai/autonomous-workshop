"""Bob may inspect the old text2game payload locally, never publish it."""

import json
import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr
from types import SimpleNamespace
from unittest import mock

import bob
from harness import export_box


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="bob-export-")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        os.environ["BOB_HOME"] = self.home
        self.addCleanup(os.environ.pop, "BOB_HOME", None)
        self.slug = "crank"
        self.gdir = os.path.join(self.home, "toys", self.slug)
        os.makedirs(os.path.join(self.gdir, "parts", "renders"))

    def _write(self, rel, data=b"x"):
        path = os.path.join(self.gdir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        mode = "wb" if isinstance(data, bytes) else "w"
        with open(path, mode) as handle:
            handle.write(data)

    def _full_game(self):
        self._write("parts/assembled.stl", b"solid a\nendsolid a\n")
        self._write("parts/hub.stl", b"solid h\nendsolid h\n")
        self._write("parts/crank_arm.stl", b"solid c\nendsolid c\n")
        self._write("parts/part_colors.json", json.dumps({"hub": "#ff0000"}))
        self._write("parts/renders/assembled.png", b"\x89PNG fake")
        self._write("rules.md", "# Rules\nTurn: crank three clicks.")
        self._write("listing.json", json.dumps({
            "description": "Three clicks resolve the whole table."}))
        self._write("idea.json", json.dumps({
            "title": "Crank", "mechanism": "shared planetary crank"}))

    def test_complete_export_matches_contract(self):
        self._full_game()
        m = export_box.export_text2game(self.slug)
        self.assertTrue(m["complete"], m["missing"])
        out = m["export_dir"]
        for rel in ("discover.md", "seed.md", "assembled.stl",
                    "fe_parts/hub.stl", "fe_parts/crank_arm.stl",
                    "part_colors.json", "renders/assembled.png",
                    "rulebook.md"):
            self.assertTrue(os.path.isfile(os.path.join(out, rel)), rel)
        # assembled.stl must NOT be duplicated into fe_parts
        self.assertFalse(os.path.exists(
            os.path.join(out, "fe_parts", "assembled.stl")))
        instructions = " ".join(m["instructions"])
        self.assertNotIn("rsync", instructions)
        self.assertNotIn("ssh", instructions.lower())
        self.assertIn("Workshop", instructions)

    def test_disclosure_leads_the_pitch(self):
        # text2game's fit_desc trims the TAIL — a trailing disclosure dies
        # under truncation, a leading one survives every cut.
        self._full_game()
        m = export_box.export_text2game(self.slug)
        with open(os.path.join(m["export_dir"], "discover.md")) as handle:
            text = handle.read()
        lines = [l for l in text.splitlines() if l.strip()]
        self.assertEqual(lines[0], "WINNER: %s" % self.slug)
        self.assertTrue(lines[1].startswith(export_box.DISCLOSURE_LINE))
        self.assertEqual(text.count(export_box.DISCLOSURE_LINE), 1)

    def test_never_fabricates_slice_report(self):
        self._full_game()
        m = export_box.export_text2game(self.slug)
        self.assertFalse(os.path.exists(
            os.path.join(m["export_dir"], "slice_report.json")))
        self.assertNotIn("slice_report.json (measured)", m["copied"])

    def test_incomplete_export_lists_missing_never_raises(self):
        self._write("idea.json", json.dumps({"title": "Bare"}))
        m = export_box.export_text2game(self.slug)
        self.assertFalse(m["complete"])
        joined = " ".join(m["missing"])
        self.assertIn("assembled.stl", joined)
        self.assertIn("renders/assembled.png", joined)
        # manifest written next to the payload for the operator
        self.assertTrue(os.path.isfile(os.path.join(
            self.gdir, "export_text2game", "export_manifest.json")))

    def test_push_box_unconfigured_fails_closed(self):
        os.environ.pop("BOB_BOX_SSH", None)
        with self.assertRaisesRegex(RuntimeError, "push_box is retired"):
            export_box.push_box(self.slug)

    def test_push_box_refuses_incomplete_export(self):
        self._write("idea.json", json.dumps({"title": "Bare"}))
        export_box.export_text2game(self.slug)
        os.environ["BOB_BOX_SSH"] = "panda-box"
        self.addCleanup(os.environ.pop, "BOB_BOX_SSH", None)
        with self.assertRaisesRegex(RuntimeError, "push_box is retired"):
            export_box.push_box(self.slug)

    def test_push_box_never_runs_rsync_or_ssh_for_complete_export(self):
        self._full_game()
        export_box.export_text2game(self.slug)
        os.environ["BOB_BOX_SSH"] = "panda-box"
        self.addCleanup(os.environ.pop, "BOB_BOX_SSH", None)
        with mock.patch(
            "subprocess.run",
            side_effect=AssertionError("retired box publisher spawned a process"),
        ) as run:
            with self.assertRaisesRegex(RuntimeError, "local inspection only"):
                export_box.push_box(self.slug)
        run.assert_not_called()
        self.assertFalse(os.path.exists(os.path.join(self.gdir, "send.json")))
        self.assertFalse(os.path.exists(os.path.join(self.gdir, "launch.json")))
        self.assertFalse(os.path.exists(os.path.join(self.gdir, "published.json")))

    def test_obsolete_mark_published_refuses_without_mutating_state(self):
        errors = io.StringIO()
        with redirect_stderr(errors):
            result = bob.cmd_mark_published(SimpleNamespace(
                slug=self.slug, design_id="legacy-design"
            ))
        self.assertEqual(result, 2)
        self.assertIn("REFUSING", errors.getvalue())
        self.assertIn("durable Sender intent", errors.getvalue())
        self.assertFalse(os.path.exists(os.path.join(self.gdir, "send.json")))
        self.assertFalse(os.path.exists(os.path.join(self.gdir, "launch.json")))
        self.assertFalse(os.path.exists(os.path.join(self.gdir, "published.json")))


if __name__ == "__main__":
    unittest.main()
