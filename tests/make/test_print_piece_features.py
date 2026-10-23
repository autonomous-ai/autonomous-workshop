"""ADR 0091 decision 7: a part receives each Print Piece through a
print-details call that reads the contract's sizes, and check_print_pieces
proves the finished part still carries every piece it hosts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.make.test_print_sheets_layout import TOOL as LAYOUT_TOOL

SCRIPTS = LAYOUT_TOOL.parent
LIBRARY = SCRIPTS / "print_details.py"
GATE = SCRIPTS / "check_print_pieces.py"

SECTION = {
    "stocks": {"paper": {"name": "couche", "caliper_mm": 0.1},
               "sticker": {"name": "decal", "caliper_mm": 0.15},
               "card": {"name": "ivory", "caliper_mm": 0.45}},
    "art": [{"file": "print-01-a.png", "shows": "a"}],
    "pieces": [
        {"id": "sky", "art": "print-01-a.png", "stock": "paper", "way": "flat", "on": "panel",
         "where": "top", "size_mm": [20, 30]},
        {"id": "notice", "art": "print-01-a.png", "stock": "sticker", "way": "sticker",
         "on": "panel", "where": "front", "size_mm": [10, 14], "outline": "oval"},
        {"id": "cloud", "art": "print-01-a.png", "stock": "card", "way": "stand", "on": "panel",
         "where": "top slot", "size_mm": [30, 15], "slot_mm": 20},
        {"id": "book", "art": "print-01-a.png", "stock": "paper", "way": "wrap", "on": "panel",
         "where": "book block", "block_mm": [14, 10, 4], "around": "cover"},
        {"id": "globe", "art": "print-01-a.png", "stock": "paper", "way": "sphere", "on": "panel",
         "where": "ball", "diameter_mm": 25, "gores": 12},
        {"id": "pages", "art": "print-01-a.png", "stock": "paper", "way": "fold", "on": "panel",
         "where": "cover board", "page_mm": [12, 16], "pages": 4},
        {"id": "label", "art": "print-01-a.png", "stock": "sticker", "way": "sticker",
         "on": "lid", "where": "lid top", "size_mm": [8, 8]},
    ],
}

PART = '''from build123d import *
from features import print_details
pd = print_details.Details(nozzle=0.4)

def gen_step():
    body = Pos(0, 0, 10) * Box(100, 60, 20)
    body = pd.print_recess(body, "sky", (-30, 0, 20))
    body = pd.print_recess(body, "notice", (0, -30, 10))
    body = pd.print_slot(body, "cloud", (10, 15, 20))
    book = pd.print_block(Pos(10, -10, 27) * Box(BOOK_W, 4, 14), "book")
    ball = pd.print_sphere(Pos(35, 10, 32.4) * Sphere(12.5), "globe")
    board = Pos(35, -18, 21) * Box(30, 20, 2)
    body = body.fuse(book).fuse(ball).fuse(board)
    body = pd.print_fold(body, "pages", (35, -18, 22))
    EXTRA
    return body
'''


class PrintPieceFeatureTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name) / "cad"
        self.project.mkdir()
        self.library(["--install", str(self.project)])
        (self.project / "print").mkdir()
        self.write_pieces(SECTION)

    def library(self, arguments):
        return subprocess.run([sys.executable, str(LIBRARY), *arguments], capture_output=True,
                              text=True, check=False)

    def write_pieces(self, section):
        (self.project / "print" / "pieces.json").write_text(
            json.dumps({"title": "T", "print": section}, indent=2, sort_keys=True))

    def gate(self, extra="", book_width=10):
        source = PART.replace("EXTRA", extra or "pass").replace("BOOK_W", str(book_width))
        (self.project / "part_panel.step.py").write_text(source)
        return subprocess.run([sys.executable, str(GATE), "part_panel.step.py"], cwd=self.project,
                              capture_output=True, text=True, check=False, timeout=600)

    def test_every_way_passes_when_its_feature_is_in_the_part(self):
        done = self.gate()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        for piece in ("sky", "notice", "cloud", "book", "globe", "pages"):
            self.assertIn("PASS %s:" % piece, done.stdout)
        # The lid's label is on another part: this part is not asked for it.
        self.assertNotIn("label", done.stdout)

    def test_a_filled_recess_and_a_missing_piece_fail(self):
        # Fill the sky recess back in, and drop the slot by never calling it.
        done = self.gate(extra="body = body.fuse(Pos(-30, 0, 19.8) * Box(21, 31, 0.6))")
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAIL sky: print-recess at part_panel.step.py:7; its recess is filled again",
                      done.stdout)
        source = PART.replace('    body = pd.print_slot(body, "cloud", (10, 15, 20))\n', "")
        (self.project / "part_panel.step.py").write_text(
            source.replace("EXTRA", "pass").replace("BOOK_W", "10"))
        done = subprocess.run([sys.executable, str(GATE), "part_panel.step.py"], cwd=self.project,
                              capture_output=True, text=True, check=False, timeout=600)
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAIL cloud: part_panel makes no print feature for this stand piece; add it "
                      "with pd.print_slot(...)", done.stdout)

    def test_a_block_of_the_wrong_size_is_refused_where_it_is_made(self):
        done = self.gate(book_width=12)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("print-block book: it measures 4.00 x 12.00 x 14.00 mm", done.stdout + done.stderr)

    def test_sizes_come_from_the_installed_contract_and_tags_carry_its_digest(self):
        done = self.gate()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        # The part is rebuilt against a contract whose sky grew: its recess was
        # cut from the old entry only if the build is reused; a fresh build
        # cuts the new size, so the digest matches again.
        section = json.loads(json.dumps(SECTION))
        section["pieces"][0]["size_mm"] = [22, 30]
        self.write_pieces(section)
        done = self.gate()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        sys.path.insert(0, str(SCRIPTS))
        import check_print_pieces

        tag = {"kind": "print-recess", "name": "print-recess:sky:000000000000", "site": "x:1"}
        self.assertEqual(check_print_pieces.read_tag(tag), ("print-recess", "sky", "000000000000"))
        self.assertIsNone(check_print_pieces.read_tag({"kind": "print-recess", "name": "print-recess-1"}))

    def test_a_piece_the_contract_does_not_have_is_refused_by_the_call(self):
        done = self.gate(extra='body = pd.print_recess(body, "poster", (30, 0, 20))')
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("print piece 'poster' is not in the Design Contract's print section",
                      done.stdout + done.stderr)
        done = self.gate(extra='body = pd.print_recess(body, "book", (30, 0, 20))')
        self.assertIn("print piece 'book' is a wrap piece; this call places flat or sticker pieces",
                      done.stdout + done.stderr)

    def test_a_part_without_pieces_or_an_install_is_skipped(self):
        (self.project / "part_lid.step.py").write_text(
            "from build123d import *\n\ndef gen_step():\n    return Box(10, 10, 2)\n")
        (self.project / "print" / "pieces.json").unlink()
        done = subprocess.run([sys.executable, str(GATE), "part_lid.step.py"], cwd=self.project,
                              capture_output=True, text=True, check=False, timeout=600)
        self.assertEqual(done.returncode, 0)
        self.assertIn("SKIP lid hosts no Print Piece", done.stdout)


class InstallPrintTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "cad"
        self.project.mkdir()
        (self.root / "wish-references").mkdir()
        self.art = b"art bytes"
        (self.root / "wish-references" / "print-01-a.png").write_bytes(self.art)

    def write_wish(self, digest):
        wish = {"references": [{"name": "print-01-a.png", "sha256": digest}],
                "context": {"design_contract": {"title": "T", "print": SECTION}}}
        (self.root / "WISH.json").write_text(json.dumps(wish))

    def install(self):
        return subprocess.run([sys.executable, str(LIBRARY), "--install-print", str(self.project),
                               "--wish", str(self.root / "WISH.json")],
                              capture_output=True, text=True, check=False)

    def test_install_copies_the_section_and_the_sealed_art(self):
        self.write_wish(hashlib.sha256(self.art).hexdigest())
        done = self.install()
        self.assertEqual(done.returncode, 0, done.stderr)
        installed = json.loads((self.project / "print" / "pieces.json").read_text())
        self.assertEqual(installed, {"title": "T", "print": SECTION})
        self.assertEqual((self.project / "print" / "art" / "print-01-a.png").read_bytes(), self.art)
        self.assertEqual(self.install().returncode, 0)  # the same bytes again

    def test_install_refuses_unsealed_art_and_an_edited_install(self):
        self.write_wish("0" * 64)
        done = self.install()
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("not the ones the Wish sealed", done.stderr)
        self.write_wish(hashlib.sha256(self.art).hexdigest())
        self.assertEqual(self.install().returncode, 0)
        (self.project / "print" / "pieces.json").write_text("{}")
        done = self.install()
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("exists with other bytes", done.stderr)


if __name__ == "__main__":
    unittest.main()


MAKE_ROUND = SCRIPTS.parents[1] / "make-round" / "scripts" / "make_round"
VERIFIER = SCRIPTS.parents[1] / "cad" / "scripts" / "verify_project"


class PaperGateWiringTest(unittest.TestCase):
    """make_round runs the paper gate on every hosting part; verify_project
    runs it and lays out the sheets in final verification."""

    @classmethod
    def setUpClass(cls):
        import runpy

        cls.make_round = runpy.run_path(str(MAKE_ROUND))
        cls.verifier = runpy.run_path(str(VERIFIER))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name)
        self.project = self.run_root / "artifacts" / "make" / "r0001" / "product" / "cad"
        self.project.mkdir(parents=True)

    def write_wish(self, section=SECTION):
        wish = {"references": [], "context": {"design_contract": {"title": "T", "print": section}}}
        (self.run_root / "WISH.json").write_text(json.dumps(wish))

    def install(self, section=SECTION):
        (self.project / "print").mkdir(exist_ok=True)
        (self.project / "print" / "pieces.json").write_text(
            json.dumps({"title": "T", "print": section}, indent=2, sort_keys=True))

    def test_the_hosting_parts_come_from_the_sealed_contract(self):
        paper_hosts = self.make_round["paper_hosts"]
        self.assertEqual(paper_hosts(self.project), (set(), None))
        self.write_wish()
        roles, error = paper_hosts(self.project)
        self.assertEqual(roles, {"panel", "lid"})
        self.assertIn("not installed", error)
        changed = json.loads(json.dumps(SECTION))
        changed["pieces"][0]["size_mm"] = [21, 30]
        self.install(changed)
        self.assertIn("not the sealed contract's print section", paper_hosts(self.project)[1])
        self.install()
        self.assertEqual(paper_hosts(self.project), ({"panel", "lid"}, None))
        # Outside a run the installed section stands.
        (self.run_root / "WISH.json").unlink()
        self.assertEqual(paper_hosts(self.project), ({"panel", "lid"}, None))

    def test_a_paper_verdict_reads_every_failing_piece_and_the_summary_shows_it(self):
        parse = self.make_round["parse_paper"]
        self.assertEqual(parse("PASS sky: x\n", 0), {"verdict": "PASS", "failures": []})
        failed = parse("PASS sky: x\nFAIL cloud: part_panel makes no print feature\n", 1)
        self.assertEqual(failed, {"verdict": "FAIL", "failures": ["cloud: part_panel makes no print feature"]})
        self.assertEqual(parse("", 2)["failures"], ["check_print_pieces exit 2"])
        gate = {"verdict": "PASS", "failures": []}
        summary = {"round": 1, "project": "cad", "changed": ["panel"], "parts": ["panel"], "ok": False, "out": "rounds/r0001",
                   "checked": ["panel"], "build": {"panel": {"verdict": "PASS", "failures": []}},
                   "print": {"panel": {"thickness": {**gate, "thinnest_mm": 1.0},
                                       "overhang": {**gate, "overhang_mm2": 0.0},
                                       "mesh": {**gate, "edges": []}, "paper": failed}}}
        text = self.make_round["render_summary"](summary)
        self.assertIn("  paper FAIL panel", text)
        self.assertIn("    cloud: part_panel makes no print feature", text)

    def test_final_verification_gates_the_pieces_and_writes_the_sheets(self):
        from PIL import Image

        self.write_wish()
        subprocess.run([sys.executable, str(LIBRARY), "--install", str(self.project)], check=True,
                       capture_output=True)
        self.install()
        art = self.project / "print" / "art"
        art.mkdir()
        Image.new("RGB", (4000, 4000), "red").save(art / "print-01-a.png")
        (self.project / "part_panel.step.py").write_text(
            PART.replace("EXTRA", "pass").replace("BOOK_W", "10"))
        (self.project / "part_lid.step.py").write_text('''from build123d import *
from features import print_details
pd = print_details.Details(nozzle=0.4)

def gen_step():
    return pd.print_recess(Pos(0, 0, 2) * Box(20, 20, 4), "label", (0, 0, 4))
''')
        runner = self.verifier["Runner"](cwd=self.project, dry_run=False, verbose=False)
        parts = sorted(self.project.glob("part_*.step.py"))
        result = self.verifier["_run_print_sheets"](runner, self.project, parts)
        # One art file serves every piece, so most pieces get the wrong shape:
        # the layout half fails while both parts carry every feature.
        commands = [record["command"] for record in runner.records]
        self.assertEqual(sum("check_print_pieces.py" in c for c in commands), 2)
        self.assertTrue(any("print_sheets.py" in c for c in commands))
        self.assertEqual([r["status"] for r in runner.records][:2], ["rc=0", "rc=0"])
        self.assertEqual(result, 1)
        report = json.loads((self.project / "print" / "sheets" / "print-sheets.json").read_text())
        self.assertIn("is 4000x4000 px, the wrong shape", "\n".join(report["failures"]))
        (self.project / "part_lid.step.py").unlink()
        runner = self.verifier["Runner"](cwd=self.project, dry_run=False, verbose=False)
        self.verifier["_run_print_sheets"](runner, self.project, sorted(self.project.glob("part_*.step.py")))
        self.assertTrue(any("no part_lid.step.py" in r["command"] for r in runner.records))
