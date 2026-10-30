"""ADR 0092, owner decision 2026-10-28: a kit Component's print gates measure
each printed Part alone in its print stance, from its ``print_parts()``,
never the Component assembled in its Display Pose.

The cabinet pilot (wish-20261028-051153-3f1061cd) gated the assembled
cabinet: its flat top board and shelf failed check_overhang as inner
ceilings (366 and 253 mm2 over air), and a 0.80 web read 0.66 on the larger
model's coarser grid. Each fake below gates the assembled Component as
needing support, so a round that measured it would fail."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import runpy
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.runtime.package_data import product_run_domain_skill_roots
from tests.make.test_kit_tree import sealed_kit
from tests.make.test_make_round import _gate_output, _gate_report, _install_gate_identity, fake_render_review, load_module
from tests.make.test_make_round_kit_tree import report_line

ROOTS = product_run_domain_skill_roots()
TOOL_PATH = ROOTS["make-round"] / "scripts" / "kit_print_parts.py"
VERIFIER = ROOTS["cad"] / "scripts" / "verify_project"
CABINET = ["B01-cabinet-carcass", "B02-cabinet-door", "D01-inkwell"]


def load_tool():
    spec = importlib.util.spec_from_file_location("kit_print_parts_under_test", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL = load_tool()


def described(parts=CABINET, identity="i", bottom=0.0, error=None):
    if error is not None:
        return {"kind": TOOL.KIND, "parts": None, "error": error}
    return {"kind": TOOL.KIND, "error": None,
            "parts": {name: {"identity": "%s-%s" % (identity, name), "bottom_mm": bottom, "solids": 1}
                      for name in parts}}


class FailuresTest(unittest.TestCase):
    """Which print_parts() results a round refuses, each with its repair."""

    def setUp(self):
        self.kit = sealed_kit()

    def test_the_printed_parts_of_a_component_leave_out_bought_parts(self):
        self.assertEqual(TOOL.printed_parts(self.kit, "cabinet"), CABINET)
        self.assertEqual(TOOL.printed_parts(self.kit, "desk"), ["C01-desk-body"])
        self.assertIsNone(TOOL.printed_parts(self.kit, "wheel"))

    def test_every_printed_part_once_on_the_bed_passes(self):
        self.assertEqual(TOOL.failures(self.kit, "cabinet", described()), [])

    def test_each_wrong_set_names_its_repair(self):
        cases = {
            "no print_parts": (described(error="part_cabinet.step.py defines no print_parts()"),
                               "defines no print_parts()"),
            "a missing part": (described(CABINET[:2]), "has no entry for printed Part D01-inkwell"),
            "a bought part": (described(CABINET + ["P01-hinge-pin"]), "P01-hinge-pin is a Bought Part"),
            "a print piece": (described(CABINET + ["M01-spine-strip"]), "M01-spine-strip is a Print Piece"),
            "an unknown part": (described(CABINET + ["X09-mystery"]),
                                "no printed Part of this Component is called X09-mystery"),
            "another component's part": (described(CABINET + ["C01-desk-body"]),
                                         "C01-desk-body is a Part of Component desk"),
            "a copy": (described(CABINET + ["B02-cabinet-door#2"]), "copies are one Part"),
            "off the bed": (described(bottom=12.5), "bottom at Z 12.500 mm, not on the bed"),
            "no describe": (TOOL.parse("Traceback\n", 1), "did not build"),
        }
        for name, (result, words) in cases.items():
            with self.subTest(name):
                lines = TOOL.failures(self.kit, "cabinet", result)
                self.assertTrue(lines)
                self.assertTrue(any(words in line for line in lines), lines)
                self.assertTrue(all(line.startswith("part_cabinet.step.py: ") for line in lines))

    def test_the_gate_entry_returns_one_part_of_the_component(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            component = project / "part_cabinet.step.py"
            component.write_text("def gen_step(): return 'assembled'\n"
                                 "def print_parts(): return {'B01-cabinet-carcass': 'flat carcass'}\n")
            entries = TOOL.write_entries(component, project / "__cadgen__" / "print-parts" / "x" / "cabinet",
                                         ["B01-cabinet-carcass"])
            path = entries["B01-cabinet-carcass"]
            self.assertEqual(path.name, "part_B01-cabinet-carcass.step.py")
            self.assertEqual(runpy.run_path(str(path))["gen_step"](), "flat carcass")
            # Rewritten fresh each time: a Part no longer printed leaves no entry.
            TOOL.write_entries(component, path.parent, ["D01-inkwell"])
            self.assertFalse(path.exists())


class GatedRound:
    """A make_round run on a kit project with every tool faked."""

    def __init__(self, project: Path):
        self.project = project
        self.calls = []
        self.describe = described()
        self.failing = set()          # (Part id, tool) pairs that fail

    def fake_run(self, command, **kwargs):
        tool = Path(command[1]).name
        self.calls.append(command)
        if tool == "gen":
            source = Path(command[2])
            source.with_name(source.name[:-3]).write_bytes(source.read_bytes())
        if tool == "render_review":
            return fake_render_review(command)
        if tool == "kit_tree.py":
            return subprocess.CompletedProcess(command, 0, report_line() + "\n", "")
        if tool == "kit_print_parts.py":
            result = self.describe
            return subprocess.CompletedProcess(command, 0 if result.get("error") is None else 1,
                                               json.dumps(result) + "\n", "")
        if tool in ("check_thickness", "check_overhang", "check_mesh"):
            target = Path(command[2])
            name = target.name.removeprefix("part_").removesuffix(".step.py")
            # The assembled Component always overhangs: its top board is a ceiling.
            fails = "print-parts" not in target.parts or (name, tool) in self.failing
            if tool == "check_mesh":
                stdout, code = ("  FAIL  closed mesh\nRESULT: OPEN MESH\n", 1) if fails else ("RESULT: printable\n", 0)
            else:
                _gate_report(command)
                stdout, code = _gate_output(tool, fails=fails)
            Path(kwargs["log"]).parent.mkdir(parents=True, exist_ok=True)
            Path(kwargs["log"]).write_text(stdout, encoding="utf-8")
            return subprocess.CompletedProcess(command, code, stdout, "")
        return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

    def main(self, module, argv, code):
        with contextlib.redirect_stdout(io.StringIO()) as printed, contextlib.redirect_stderr(io.StringIO()), \
                mock.patch.object(module, "skills_root", return_value=self.project), \
                mock.patch.object(module, "run", side_effect=self.fake_run):
            returned = module.main([str(self.project), *argv])
        if returned != code:
            raise AssertionError("make_round exited %r, not %r:\n%s" % (returned, code, printed.getvalue()))
        return printed.getvalue()

    def gated(self, since=0):
        return [Path(c[2]) for c in self.calls[since:]
                if Path(c[1]).name in ("check_thickness", "check_overhang", "check_mesh")]


class KitRoundTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        (self.project / "toy.step.py").write_text("def gen_step(): pass\n")
        (self.project / "part_cabinet.step.py").write_text("def gen_step(): pass\ndef print_parts(): pass\n")
        _install_gate_identity(self.project)
        (self.project / "tree").mkdir()
        (self.project / "tree" / "kit.json").write_text(json.dumps(sealed_kit()))
        self.round = GatedRound(self.project)

    def assembly(self, code=1):
        module = load_module()
        printed = self.round.main(module, [], code)
        rounds = sorted((self.project / "measure" / "rounds").iterdir())
        return module, json.loads((rounds[-1] / "summary.json").read_text()), printed

    def component(self, code=1):
        module = load_module()
        printed = self.round.main(module, ["--component", "part_cabinet.step.py"], code)
        rounds = sorted((self.project / "measure" / "component-rounds" / "cabinet").iterdir())
        return module, json.loads((rounds[-1] / "summary.json").read_text()), printed

    def test_flat_parts_pass_where_the_assembled_component_overhangs(self):
        module, summary, printed = self.component()
        record = summary["print"]["cabinet"]
        self.assertEqual(record["verdict"], "PASS")
        self.assertEqual(sorted(record["parts"]), CABINET)
        self.assertTrue(summary["checks_ok"])
        self.assertEqual(summary["visual"]["status"], "pending")
        gated = self.round.gated()
        # Three gates per Part, each on its own entry; never the assembled file.
        self.assertEqual(len(gated), 9)
        self.assertNotIn(self.project / "part_cabinet.step.py", gated)
        self.assertEqual(sorted({path.name for path in gated}),
                         ["part_%s.step.py" % name for name in CABINET])
        self.assertTrue(all("__cadgen__" in path.parts for path in gated))
        describe = [c for c in self.round.calls if Path(c[1]).name == "kit_print_parts.py"]
        self.assertEqual([c[2:] for c in describe], [["describe", str(self.project / "part_cabinet.step.py")]])
        out = Path(summary["out"])
        self.assertTrue((out / "overhang-cabinet-B02-cabinet-door.log").is_file())
        self.assertIn("parts PASS cabinet", printed)
        self.assertIn("over  PASS cabinet/B01-cabinet-carcass", printed)
        # The kit tree and the review still read the assembled Component.
        render = next(c for c in self.round.calls if Path(c[1]).name == "render_review")
        self.assertEqual(Path(render[2]).name, "part_cabinet.step.py")

    def test_a_kit_component_hosting_a_print_piece_gates_its_parts_and_its_paper(self):
        # The cabinet pilot (wish-20261028-051153-3f1061cd) crashed here: the paper
        # gate's job has no Part name, and sorting it beside the Part names raised.
        module = load_module()
        with mock.patch.object(module, "paper_hosts", return_value=({"cabinet"}, None)):
            self.round.main(module, ["--component", "part_cabinet.step.py"], 1)
        rounds = sorted((self.project / "measure" / "component-rounds" / "cabinet").iterdir())
        summary = json.loads((rounds[-1] / "summary.json").read_text())
        record = summary["print"]["cabinet"]
        self.assertEqual(record["verdict"], "PASS")
        self.assertEqual(sorted(record["parts"]), CABINET)
        self.assertIn("paper", record)
        self.assertTrue(any(Path(c[1]).name == "check_print_pieces.py" for c in self.round.calls))

    def test_one_failing_part_fails_the_round_and_is_named(self):
        self.round.failing = {("B02-cabinet-door", "check_overhang")}
        module, summary, printed = self.component()
        record = summary["print"]["cabinet"]
        self.assertEqual(record["verdict"], "FAIL")
        self.assertEqual(record["parts"]["B02-cabinet-door"]["verdict"], "FAIL")
        self.assertEqual(record["parts"]["B01-cabinet-carcass"]["verdict"], "PASS")
        self.assertEqual(record["overhang"]["failing_parts"], ["B02-cabinet-door"])
        self.assertTrue(record["overhang"]["failures"][0].startswith("B02-cabinet-door: "))
        self.assertEqual(record["overhang"]["overhang_mm2"], 473.9)
        self.assertFalse(summary["checks_ok"])
        self.assertEqual(summary["visual"]["status"], "not-rendered")
        self.assertIn("over  FAIL cabinet/B02-cabinet-door", printed)

    def test_a_refused_print_parts_fails_the_round_and_gates_nothing(self):
        cases = {
            "missing": described(error="part_cabinet.step.py defines no print_parts()"),
            "a part short": described(CABINET[1:]),
            "a bought part": described(CABINET + ["P02-jar"]),
            "an unknown part": described(CABINET + ["Z01-ghost"]),
        }
        for name, result in cases.items():
            with self.subTest(name):
                self.round.describe = result
                before = len(self.round.calls)
                _, summary, printed = self.assembly()
                record = summary["print"]["cabinet"]
                self.assertEqual(record["verdict"], "FAIL")
                self.assertTrue(record["print_parts"])
                self.assertFalse(summary["checks_ok"])
                self.assertEqual(self.round.gated(before), [])
                self.assertIn("parts FAIL cabinet", printed)
                self.assertIn(record["print_parts"][0], printed)

    def test_reuse_holds_each_part_and_a_changed_part_is_gated_again(self):
        _, first, _ = self.assembly()
        self.assertEqual(first["print"]["cabinet"]["verdict"], "PASS")
        before = len(self.round.calls)
        _, second, _ = self.assembly()
        self.assertEqual(self.round.gated(before), [])
        self.assertIn("cabinet", second["reused"])
        # The assembled Component did not move, but one Part's print stance did.
        self.round.describe = described(identity="i")
        self.round.describe["parts"]["B02-cabinet-door"]["identity"] = "turned-door"
        before = len(self.round.calls)
        _, third, _ = self.assembly()
        self.assertEqual(len(self.round.gated(before)), 9)
        self.assertNotIn("cabinet", third["reused"])
        self.assertEqual(third["print"]["cabinet"]["parts"]["B02-cabinet-door"]["identity"], "turned-door")

    def test_reuse_rules_for_kit_records(self):
        module = load_module()
        log = self.project / "gate.log"
        log.write_text("pass")
        digest = __import__("hashlib").sha256(b"pass").hexdigest()
        passing = {"verdict": "PASS", "failures": []}
        part = {"verdict": "PASS", "identity": "a", "thickness": passing, "overhang": passing, "mesh": passing}
        record = {"verdict": "PASS", "thickness": passing, "overhang": passing, "mesh": passing,
                  "measured_round": 1, "logs": {str(log): digest}, "parts": {"B01-cabinet-carcass": part}}
        self.assertTrue(module.reusable_print(record, {"B01-cabinet-carcass": "a"}))
        self.assertFalse(module.reusable_print(record, {"B01-cabinet-carcass": "b"}))
        self.assertFalse(module.reusable_print(record, {"B01-cabinet-carcass": "a", "B02-cabinet-door": "c"}))
        self.assertFalse(module.reusable_print(record), "a kit record never stands for an ordinary part")
        plain = {key: value for key, value in record.items() if key != "parts"}
        self.assertTrue(module.reusable_print(plain))
        self.assertFalse(module.reusable_print(plain, {"B01-cabinet-carcass": "a"}),
                         "an assembled-model record never stands for a kit Component")


class NonKitRoundTest(unittest.TestCase):
    def test_a_component_without_a_tree_is_gated_as_before(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "toy.step.py").write_text("def gen_step(): pass\n")
            (project / "part_cabinet.step.py").write_text("def gen_step(): pass\n")
            _install_gate_identity(project)
            gated = GatedRound(project)
            module = load_module()
            gated.main(module, [], 1)
            summary = json.loads((project / "measure" / "rounds" / "r0001" / "summary.json").read_text())
            self.assertEqual([path.name for path in gated.gated()], ["part_cabinet.step.py"] * 3)
            self.assertNotIn("kit_print_parts.py", [Path(c[1]).name for c in gated.calls])
            self.assertNotIn("parts", summary["print"]["cabinet"])
            self.assertEqual(summary["print"]["cabinet"]["verdict"], "FAIL")


class RecordingRunner:
    """verify_project's Runner, recording instead of running."""

    def __init__(self, project: Path, describe: dict, failing=()):
        self.cwd = project
        self.dry_run = False
        self.records = []
        self.last_stdout = ""
        self.describe = describe
        self.failing = set(failing)
        self.commands = []
        self.skips = []

    def command(self, argv, **_kwargs):
        args = [str(item) for item in argv]
        self.commands.append(args)
        tool = Path(args[1]).name
        if tool == "kit_print_parts.py":
            self.last_stdout = json.dumps(self.describe) + "\n"
            return 0 if self.describe.get("error") is None else 1
        name = Path(args[2]).name.removeprefix("part_").removesuffix(".step.py")
        return 1 if (name, tool) in self.failing or name == "cabinet" else 0

    def skipped(self, label, _reason):
        self.skips.append(label)

    def gated(self):
        return [(Path(c[1]).name, Path(c[2]).name) for c in self.commands if Path(c[1]).name.startswith("check_")]


class FinalVerificationTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        self.cabinet = self.project / "part_cabinet.step.py"
        self.cabinet.write_text("PRINTABLE = False\ndef gen_step(): pass\ndef print_parts(): pass\n")
        self.verifier = runpy.run_path(str(VERIFIER))

    def gates(self, runner, printables):
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            code = self.verifier["_run_print_gates"](
                runner, self.project, printables, bed=(220.0, 220.0, 220.0), nozzle=0.4,
                skip_thickness=False, overhang_angle=45.0, parts=[self.cabinet])
        return code, printed.getvalue()

    def install(self):
        (self.project / "tree").mkdir()
        (self.project / "tree" / "kit.json").write_text(json.dumps(sealed_kit()))

    def test_each_kit_part_is_gated_alone_even_when_the_component_is_not_printable(self):
        self.install()
        runner = RecordingRunner(self.project, described())
        code, _ = self.gates(runner, [])
        self.assertEqual(code, 0)
        gated = runner.gated()
        self.assertEqual(len(gated), 9)
        self.assertNotIn("part_cabinet.step.py", {name for _, name in gated})
        overhang = [c for c in runner.commands if Path(c[1]).name == "check_overhang"]
        self.assertTrue(any(c[c.index("--report") + 1].endswith("measure/overhang-cabinet-D01-inkwell.md")
                            for c in overhang))

    def test_a_failing_part_fails_final_verification(self):
        self.install()
        runner = RecordingRunner(self.project, described(), failing={("B01-cabinet-carcass", "check_thickness")})
        code, printed = self.gates(runner, [])
        self.assertEqual(code, 1)
        self.assertIn("print gate group: 1 failure(s)", printed)

    def test_a_refused_print_parts_fails_final_verification_and_gates_nothing(self):
        self.install()
        runner = RecordingRunner(self.project, described(CABINET + ["P01-hinge-pin"]))
        code, printed = self.gates(runner, [self.cabinet])
        self.assertEqual(code, 1)
        self.assertEqual(runner.gated(), [])
        self.assertIn("P01-hinge-pin is a Bought Part", printed)
        self.assertTrue(any(record["command"].startswith("print parts  # FAILED") for record in runner.records))

    def test_without_a_tree_the_printable_is_gated_whole_as_before(self):
        runner = RecordingRunner(self.project, described())
        code, _ = self.gates(runner, [self.cabinet])
        self.assertEqual(code, 1)
        self.assertEqual(runner.gated(), [("check_mesh", "part_cabinet.step.py")])
        self.assertNotIn("kit_print_parts.py", [Path(c[1]).name for c in runner.commands])


class RealGeometryTest(unittest.TestCase):
    """The real describe, entry and overhang gate on a small build123d
    cabinet: its top board is a ceiling assembled and flat on the bed."""

    def test_the_top_board_overhangs_assembled_and_prints_flat_alone(self):
        try:
            import build123d  # noqa: F401
        except ImportError:  # pragma: no cover - the CAD runtime is part of the dev environment
            self.skipTest("build123d is not installed")
        import sys

        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            component = project / "part_cabinet.step.py"
            component.write_text(
                "from build123d import Box, Compound, Pos\n\n"
                "def gen_step():\n"
                "    top = Pos(0, 0, 50) * Box(40, 30, 2)\n"
                "    side = Pos(-19, 0, 25) * Box(2, 30, 50)\n"
                "    top.label, side.label = 'B01-cabinet-carcass', 'B02-cabinet-door'\n"
                "    return Compound(children=[top, side])\n\n"
                "def print_parts():\n"
                "    return {'B01-cabinet-carcass': Pos(0, 0, 1) * Box(40, 30, 2),\n"
                "            'B02-cabinet-door': Pos(0, 0, 1) * Box(50, 30, 2)}\n")
            done = subprocess.run([sys.executable, str(TOOL_PATH), "describe", str(component)],
                                  capture_output=True, text=True, timeout=300)
            result = TOOL.parse(done.stdout, done.returncode)
            self.assertIsNone(result["error"], done.stderr)
            self.assertEqual(sorted(result["parts"]), ["B01-cabinet-carcass", "B02-cabinet-door"])
            self.assertEqual(result["parts"]["B01-cabinet-carcass"]["bottom_mm"], 0.0)
            entries = TOOL.write_entries(component, project / "__cadgen__" / "print-parts" / "t" / "cabinet",
                                         ["B01-cabinet-carcass"])
            overhang = ROOTS["cad"] / "scripts" / "check_overhang"
            alone = subprocess.run([sys.executable, str(overhang), str(entries["B01-cabinet-carcass"])],
                                   capture_output=True, text=True, timeout=300)
            assembled = subprocess.run([sys.executable, str(overhang), str(component)],
                                       capture_output=True, text=True, timeout=300)
            self.assertEqual(alone.returncode, 0, alone.stdout + alone.stderr)
            self.assertEqual(assembled.returncode, 1, assembled.stdout + assembled.stderr)
            self.assertIn("NEEDS SUPPORT", assembled.stdout)


if __name__ == "__main__":
    unittest.main()
