"""make_round --print-gates-only: Make's own build and print gates on a
directory of CAD sources, with no run state (owner, 2026-10-28).

The ADR 0093 cabinet pilot stopped after three component rounds because the
Contract Proof gated each kit Part flat while Make gated the assembled
Component. The Proof now runs this mode, so its gates are a round's gates:
the same jobs, parsers and records, with no nonce, hook, Shared Helper
freeze, round history or Workshop run, writing only inside the directory."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.make.test_kit_print_parts import CABINET, described
from tests.make.test_kit_tree import sealed_block, sealed_kit
from tests.make.test_make_round import _gate_output, load_module
from tests.wish.test_design_contract import _contract_text

GATES = ("check_thickness", "check_overhang", "check_mesh")


class FakeTools:
    """Every tool make_round runs, faked; ``failing`` holds (target, tool)
    pairs, a target being a part role or a kit Part id."""

    def __init__(self):
        self.calls = []
        self.describe = described()
        self.failing = set()
        self.unbuilt = set()

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        tool = Path(command[1]).name
        log = Path(kwargs["log"])
        log.parent.mkdir(parents=True, exist_ok=True)
        stdout, code = '{"ok":true}\n', 0
        if tool == "gen":
            source = Path(command[2])
            role = source.name.removeprefix("part_").removesuffix(".step.py")
            if role in self.unbuilt:
                stdout, code = "", 1
            else:
                source.with_name(source.name[:-3]).write_bytes(source.read_bytes())
        elif tool == "kit_print_parts.py":
            stdout = json.dumps(self.describe) + "\n"
            code = 0 if self.describe.get("error") is None else 1
        elif tool in GATES:
            target = Path(command[2]).name.removeprefix("part_").removesuffix(".step.py")
            fails = (target, tool) in self.failing
            if tool == "check_mesh":
                stdout, code = ("  FAIL  closed mesh\nRESULT: OPEN MESH\n", 1) if fails else ("RESULT: printable\n", 0)
            else:
                stdout, code = _gate_output(tool, fails=fails)
        log.write_text(stdout, encoding="utf-8")
        return subprocess.CompletedProcess(command, code, stdout, "gen failed\n" if code and tool == "gen" else "")

    def gated(self):
        return [Path(command[2]) for command, _ in self.calls if Path(command[1]).name in GATES]


class PrintGatesOnlyTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "proof"
        self.project.mkdir()
        (self.project / "proof.step.py").write_text("PRINTABLE = False\ndef gen_step(): pass\n")
        self.tools = FakeTools()

    def gates(self, *argv, code):
        module = load_module()
        with contextlib.redirect_stdout(io.StringIO()) as printed, \
                contextlib.redirect_stderr(io.StringIO()) as errors, \
                mock.patch.object(module, "skills_root", return_value=self.root / "skills"), \
                mock.patch.object(module, "run", side_effect=self.tools):
            returned = module.main([str(self.project), "--print-gates-only", *argv])
        if returned != code:
            raise AssertionError("make_round exited %r, not %r:\n%s%s"
                                 % (returned, code, printed.getvalue(), errors.getvalue()))
        summary_path = self.project / "measure" / "print-gates" / "summary.json"
        summary = json.loads(summary_path.read_text()) if summary_path.is_file() else None
        return summary, printed.getvalue() + errors.getvalue()

    def part(self, role, text="def gen_step(): pass\n"):
        (self.project / ("part_%s.step.py" % role)).write_text(text)

    def kit(self):
        self.part("cabinet", "def gen_step(): pass\ndef print_parts(): pass\n")
        contract = self.root / "CONTRACT.md"
        contract.write_text(_contract_text(sealed_block()))
        return contract

    def test_a_passing_part_passes_each_gate_and_exits_zero(self):
        self.part("plate")
        summary, printed = self.gates("--nozzle", "0.6", code=0)
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["print"]["plate"]["verdict"], "PASS")
        for line in ("build PASS plate", "wall  PASS plate", "over  PASS plate", "mesh  PASS plate"):
            self.assertIn(line, printed)
        commands = {Path(command[1]).name: command for command, _ in self.tools.calls}
        # The round's own gate commands, at the given nozzle and overhang.
        self.assertEqual(commands["check_thickness"][commands["check_thickness"].index("--nozzle") + 1], "0.6")
        self.assertEqual(commands["check_overhang"][commands["check_overhang"].index("--angle") + 1], "45.0")
        self.assertIn("--bed", commands["check_mesh"])
        self.assertEqual(commands["gen"][3:], ["--write", "--json"])
        # Nothing of a round's state: no rounds, no state, no packet.
        self.assertEqual(sorted(p.name for p in (self.project / "measure").iterdir()), ["print-gates"])

    def test_a_failing_part_names_its_region_and_exits_one(self):
        self.part("plate")
        self.part("shelf")
        self.tools.failing = {("shelf", "check_overhang"), ("shelf", "check_thickness")}
        summary, printed = self.gates(code=1)
        self.assertFalse(summary["ok"])
        self.assertEqual(summary["print"]["plate"]["verdict"], "PASS")
        record = summary["print"]["shelf"]
        self.assertEqual(record["verdict"], "FAIL")
        self.assertEqual(record["overhang"]["overhang_mm2"], 473.9)
        self.assertEqual(record["thickness"]["thinnest_mm"], 0.42)
        self.assertIn("over  FAIL shelf", printed)
        self.assertIn("largest 474 mm2", printed)
        self.assertIn("wall  FAIL shelf", printed)
        self.assertIn("thinnest 0.42 mm", printed)
        self.assertIn("FAIL  reports under", printed)

    def test_a_part_that_does_not_build_fails_every_gate(self):
        self.part("plate")
        self.tools.unbuilt = {"plate"}
        summary, printed = self.gates(code=1)
        self.assertEqual(summary["build"]["plate"]["verdict"], "FAIL")
        self.assertEqual(summary["print"]["plate"]["thickness"]["failures"], ["build failed"])
        self.assertEqual(self.tools.gated(), [])
        self.assertIn("build FAIL plate", printed)

    def test_a_kit_component_is_gated_part_by_part_from_its_contract(self):
        contract = self.kit()
        summary, printed = self.gates("--contract", str(contract), code=0)
        record = summary["print"]["cabinet"]
        self.assertTrue(summary["kit"])
        self.assertEqual(sorted(record["parts"]), CABINET)
        gated = self.tools.gated()
        # Three gates per printed Part, each on its own generated entry; the
        # assembled Component is never gated.
        self.assertEqual(len(gated), 9)
        self.assertNotIn(self.project / "part_cabinet.step.py", gated)
        self.assertEqual(sorted({path.name for path in gated}), ["part_%s.step.py" % name for name in CABINET])
        self.assertTrue(all(path.is_relative_to(self.project / "__cadgen__") for path in gated))
        self.assertIn("parts PASS cabinet", printed)
        self.assertIn("over  PASS cabinet/B01-cabinet-carcass", printed)

    def test_without_a_contract_the_installed_tree_stands(self):
        self.kit()
        (self.project / "tree").mkdir()
        (self.project / "tree" / "kit.json").write_text(json.dumps(sealed_kit()))
        summary, _ = self.gates(code=0)
        self.assertEqual(sorted(summary["print"]["cabinet"]["parts"]), CABINET)
        self.assertEqual(len(self.tools.gated()), 9)

    def test_one_failing_kit_part_fails_and_is_named(self):
        contract = self.kit()
        self.tools.failing = {("B02-cabinet-door", "check_overhang")}
        summary, printed = self.gates("--component", "part_cabinet.step.py", "--contract", str(contract), code=1)
        record = summary["print"]["cabinet"]
        self.assertEqual(record["parts"]["B02-cabinet-door"]["verdict"], "FAIL")
        self.assertEqual(record["parts"]["B01-cabinet-carcass"]["verdict"], "PASS")
        self.assertEqual(record["overhang"]["failing_parts"], ["B02-cabinet-door"])
        self.assertIn("over  FAIL cabinet/B02-cabinet-door", printed)

    def test_a_refused_print_parts_gates_nothing_and_says_why(self):
        contract = self.kit()
        self.tools.describe = described(CABINET + ["P01-hinge-pin"])
        summary, printed = self.gates("--contract", str(contract), code=1)
        self.assertEqual(self.tools.gated(), [])
        self.assertTrue(summary["print"]["cabinet"]["print_parts"])
        self.assertIn("parts FAIL cabinet", printed)
        self.assertIn("P01-hinge-pin is a Bought Part", printed)

    def test_the_same_gate_code_as_a_round(self):
        # The mode builds its jobs and records with the functions a round uses.
        module = load_module()
        self.part("plate")
        calls = []
        real = module.print_gate_jobs

        def spy(*args, **kwargs):
            calls.append(args)
            return real(*args, **kwargs)

        with contextlib.redirect_stdout(io.StringIO()), \
                mock.patch.object(module, "skills_root", return_value=self.root / "skills"), \
                mock.patch.object(module, "run", side_effect=self.tools), \
                mock.patch.object(module, "print_gate_jobs", side_effect=spy):
            self.assertEqual(module.main([str(self.project), "--print-gates-only"]), 0)
        self.assertEqual(len(calls), 1)

    def test_it_needs_no_run_state_and_writes_only_inside_the_directory(self):
        contract = self.kit()
        self.part("plate")
        (self.root / "sibling.txt").write_text("untouched")
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in self.root.rglob("*") if path.is_file()}
        self.tools.failing = {("plate", "check_mesh")}
        self.gates("--component", "part_plate.step.py", "--contract", str(contract), code=1)
        self.gates("--contract", str(contract), code=1)
        after = {path: hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in self.root.rglob("*") if path.is_file()}
        outside = {path for path in set(before) | set(after)
                   if not path.is_relative_to(self.project) and before.get(path) != after.get(path)}
        self.assertEqual(outside, set())
        for command, kwargs in self.tools.calls:
            self.assertEqual(Path(kwargs["cwd"]), self.project)
            self.assertTrue(Path(kwargs["log"]).is_relative_to(self.project))
            self.assertEqual(kwargs["extra_env"]["PYTHONDONTWRITEBYTECODE"], "1")
            if "--report" in command:
                self.assertTrue(Path(command[command.index("--report") + 1]).is_relative_to(self.project))
        self.assertFalse((self.project / "measure" / "rounds").exists())
        self.assertFalse((self.project / "measure" / "component-rounds").exists())

    def test_inside_a_workshop_run_the_gates_run_only_in_a_round(self):
        # In a guarded run a component round needs the guard's nonce; this
        # mode must not become a way around it or around round accounting.
        self.part("plate")
        (self.root / "WISH.json").write_text("{}")
        (self.root / ".agents").mkdir()
        (self.root / ".agents" / "MAKE-ROUND-GUARD.json").write_text("{}")
        summary, printed = self.gates("--component", "part_plate.step.py", code=2)
        self.assertIsNone(summary)
        self.assertEqual(self.tools.calls, [])
        self.assertIn("outside a Workshop run", printed)
        self.assertFalse((self.project / "measure").exists())

    def test_round_options_are_refused(self):
        self.part("plate")
        for extra in (["--all-parts"], ["--out", str(self.project / "x")], ["--record-visual", "f.json"],
                      ["--shared-helpers"], ["--worker-nonce", "0" * 32]):
            with self.subTest(extra), self.assertRaises(SystemExit), \
                    contextlib.redirect_stderr(io.StringIO()):
                load_module().main([str(self.project), "--print-gates-only", *extra])
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            load_module().main([str(self.project), "--contract", "CONTRACT.md"])

    def test_a_contract_without_a_tree_gates_each_part_whole(self):
        self.part("plate")
        contract = self.root / "plain.md"
        contract.write_text("Prose.\n\n```design-contract\n{\"schema_version\": 8}\n```\n")
        summary, _ = self.gates("--contract", str(contract), code=0)
        self.assertFalse(summary["kit"])
        self.assertEqual(self.tools.gated(), [self.project / "part_plate.step.py"] * 3)


if __name__ == "__main__":
    unittest.main()
