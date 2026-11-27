"""ADR 0098: a seeded Make's checks as one deterministic batch.

Contract: steps run in the fixed layer order whatever order they are given;
every step of a layer runs and every failure in it is reported; the layers
after a failed one are skipped and named; exit 0 is a pass, exit 1 without a
traceback a check failure, and a signal, another exit, a timeout, a
traceback or a tool that cannot start a harness failure; a pass is reused
while its command, tool and input bytes are unchanged, a failure never is;
a component round's seed nonce is issued when it runs and is never part of
its key; the failure packet carries each failing step in its own words,
bounded, the passed steps by key and the repair rules; the run plan holds
every layer and the design plan only those that need no run state; the
Spark source and concept hash are composed, not authored."""

from __future__ import annotations

import importlib.util
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.make import seeded_batch as sb
from workshop.make.seeded_batch import RunResult, Step

ROOT = Path(__file__).resolve().parents[2]


class FakeRunner:
    def __init__(self, results=None):
        self.results = results or {}
        self.calls = []

    def __call__(self, argv, cwd, timeout):
        self.calls.append((list(argv), timeout))
        for fragment, result in self.results.items():
            if fragment in argv:
                return result
        return RunResult(0, "ok", duration_s=0.5)


class BatchEngineTest(unittest.TestCase):
    def setUp(self):
        self.project = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (self.project / "params.py").write_text("A = 1\n")
        (self.project / "part_a.step.py").write_text("a\n")
        (self.project / "part_b.step.py").write_text("b\n")

    def _steps(self):
        return [
            Step("final", "final", ("verify", "final")),
            Step("component:a", "components", ("round", "a"), inputs=("params.py", "part_a.step.py")),
            Step("component:b", "components", ("round", "b"), inputs=("params.py", "part_b.step.py")),
            Step("project", "project", ("project",)),
            Step("interface:x", "interfaces", ("interface", "x")),
        ]

    def test_layers_run_in_their_fixed_order(self):
        runner = FakeRunner()
        record = sb.run_batch(self._steps(), self.project, runner=runner)
        self.assertEqual([call[0][0] for call in runner.calls], ["project", "round", "round", "interface", "verify"])
        self.assertEqual(record["status"], sb.PASS)
        self.assertIsNone(record["failed_layer"])

    def test_every_failure_in_a_layer_is_reported_and_later_layers_skip(self):
        runner = FakeRunner({"a": RunResult(1, "a: wall 0.6 under 0.8"), "b": RunResult(1, "b: overhang 52 deg")})
        record = sb.run_batch(self._steps(), self.project, runner=runner)
        by_id = {item["id"]: item for item in record["steps"]}
        self.assertEqual(record["status"], sb.CHECK_FAILURE)
        self.assertEqual(record["failed_layer"], "components")
        self.assertEqual((by_id["component:a"]["status"], by_id["component:b"]["status"]),
                         (sb.CHECK_FAILURE, sb.CHECK_FAILURE))
        for later in ("interface:x", "final"):
            self.assertEqual(by_id[later]["status"], sb.SKIPPED)
            self.assertEqual(by_id[later]["reason"], "layer components failed")
        self.assertNotIn(["interface", "x"], [call[0] for call in runner.calls])

    def test_exit_classification(self):
        cases = {
            "pass": (RunResult(0, ""), sb.PASS, None),
            "check": (RunResult(1, "fails: lead hole"), sb.CHECK_FAILURE, None),
            "traceback": (RunResult(1, "Traceback (most recent call last):\n ImportError"), sb.HARNESS_FAILURE,
                          "uncaught exception"),
            "signal": (RunResult(-9, ""), sb.HARNESS_FAILURE, "SIGKILL"),
            "exit 2": (RunResult(2, "usage"), sb.HARNESS_FAILURE, "exit 2"),
            "timeout": (RunResult(None, "", timed_out=True), sb.HARNESS_FAILURE, "timed out"),
            "no tool": (RunResult(None, "", start_error="FileNotFoundError: x"), sb.HARNESS_FAILURE, "could not start"),
        }
        for name, (result, status, reason) in cases.items():
            with self.subTest(name):
                got, why = sb.classify(result)
                self.assertEqual(got, status)
                if reason is None:
                    self.assertIsNone(why)
                else:
                    self.assertIn(reason, why)

    def test_a_harness_failure_outranks_a_check_failure(self):
        runner = FakeRunner({"a": RunResult(1, "a fails"), "b": RunResult(-9, "")})
        record = sb.run_batch(self._steps(), self.project, runner=runner)
        self.assertEqual(record["status"], sb.HARNESS_FAILURE)
        self.assertEqual([item["id"] for item in sb.harness_failures(record)], ["component:b"])

    def test_a_pass_is_reused_until_its_inputs_change_and_a_failure_never_is(self):
        first = sb.run_batch(self._steps(), self.project, runner=FakeRunner({"b": RunResult(1, "b fails")}))
        runner = FakeRunner()
        second = sb.run_batch(self._steps(), self.project, runner=runner, previous=first)
        statuses = {item["id"]: item["status"] for item in second["steps"]}
        self.assertEqual(statuses["project"], sb.REUSED)
        self.assertEqual(statuses["component:a"], sb.REUSED)
        self.assertEqual(statuses["component:b"], sb.PASS, "a failure is rerun")
        (self.project / "part_a.step.py").write_text("a changed\n")
        third = sb.run_batch(self._steps(), self.project, runner=FakeRunner(), previous=second)
        statuses = {item["id"]: item["status"] for item in third["steps"]}
        self.assertEqual(statuses["component:a"], sb.PASS)
        self.assertEqual(statuses["component:b"], sb.REUSED)
        (self.project / "params.py").write_text("A = 2\n")
        fourth = sb.run_batch(self._steps(), self.project, runner=FakeRunner(), previous=third)
        self.assertEqual({item["id"]: item["status"] for item in fourth["steps"]}["component:b"], sb.PASS)

    def test_a_tool_change_invalidates_its_reuse(self):
        tool = self.project / "tool.py"
        tool.write_text("v1")
        steps = [Step("t", "project", (sys.executable, str(tool)))]
        first = sb.run_batch(steps, self.project, runner=FakeRunner())
        tool.write_text("v2")
        second = sb.run_batch(steps, self.project, runner=FakeRunner(), previous=first)
        self.assertEqual(second["steps"][0]["status"], sb.PASS)

    def test_a_seed_nonce_is_issued_when_the_round_runs_and_is_not_keyed(self):
        issued = []
        steps = [Step("component:a", "components", ("round", "a"), nonce_component="a")]
        runner = FakeRunner()

        def issue(component):
            issued.append(component)
            return "n%d" % len(issued)

        first = sb.run_batch(steps, self.project, runner=runner, issue_nonce=issue)
        self.assertEqual(runner.calls[0][0], ["round", "a", "--seed-nonce", "n1"])
        self.assertNotIn("--seed-nonce", first["steps"][0]["argv"])
        second = sb.run_batch(steps, self.project, runner=runner, issue_nonce=issue, previous=first)
        self.assertEqual(second["steps"][0]["status"], sb.REUSED)
        self.assertEqual(issued, ["a"], "a reused round takes no nonce")
        with self.assertRaises(ValueError):
            sb.run_batch(steps, self.project, runner=runner)

    def test_an_exit_0_final_counts_only_its_reports_pass(self):
        """Issue #241: verify_project exits 0 when its shared geometry
        allowance is spent and records the unfinished analyses UNVERIFIED; the
        batch reads the report's Result and never counts that as a pass."""
        report = "measure/verification-pipeline.md"
        for written, status, reason in (
            ("- Result: **PASS** (exit 0)\n", sb.PASS, None),
            ("- Result: **UNVERIFIED** (exit 0)\n", sb.HARNESS_FAILURE, "records UNVERIFIED: a geometry check"),
            ("- Result: **FAIL** (exit 0)\n", sb.HARNESS_FAILURE, "records FAIL"),
            ("no verdict here\n", sb.HARNESS_FAILURE, "records no Result line"),
            (None, sb.HARNESS_FAILURE, "records no Result line"),
        ):
            with self.subTest(written):
                path = self.project / report
                path.unlink(missing_ok=True)
                if written is not None:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("# Verification\n" + written)
                record = sb.run_batch([Step("final-verification", "final", ("verify",), verdict_report=report)],
                                      self.project, runner=FakeRunner())
                step = record["steps"][0]
                self.assertEqual((record["status"], step["status"]), (status, status))
                if reason is None:
                    self.assertIsNone(step.get("reason"))
                else:
                    self.assertIn(reason, step["reason"])

    def _round_summary(self, summary, *, age_s=0.0):
        import os
        out = self.project / "measure/rounds/r0001"
        out.mkdir(parents=True, exist_ok=True)
        (out / "summary.json").write_text(json.dumps(summary))
        (self.project / "measure/make-round-state.json").write_text(json.dumps({"round": 1, "last_out": str(out)}))
        if age_s:
            stamp = (out / "summary.json").stat().st_mtime - age_s
            os.utime(out / "summary.json", (stamp, stamp))

    def test_an_assembly_round_that_ran_out_of_time_is_a_harness_failure(self):
        """Issue #244: the round's check_motion took 773 s against 600 s and
        reported motion unverified. Whatever its exit, that is never a pass,
        and no model repair finishes an analysis that ran out of time."""
        step = Step("assembly-round", "assembly", ("round",), round_summary=True)
        for summary, code, status, reason in (
            ({"ok": True, "motion_status": "pass"}, 0, sb.PASS, None),
            ({"ok": False, "motion_status": "unverified", "geometry_status": "unverified"}, 1, sb.HARNESS_FAILURE,
             "check_motion did not finish"),
            ({"ok": True, "motion_status": "unverified", "geometry_status": "unverified"}, 0, sb.HARNESS_FAILURE,
             "check_motion did not finish"),
            ({"ok": False, "motion_status": "pass", "geometry_status": "unverified"}, 1, sb.HARNESS_FAILURE,
             "geometry check unfinished"),
            ({"ok": False, "motion_status": "fail"}, 1, sb.CHECK_FAILURE, None),
        ):
            with self.subTest(summary=summary):
                self._round_summary(summary)
                record = sb.run_batch([step], self.project,
                                      runner=FakeRunner({"round": RunResult(code, "out", duration_s=1.0)}))
                entry = record["steps"][0]
                self.assertEqual(entry["status"], status)
                if reason is not None:
                    self.assertIn(reason, entry["reason"])

    def test_an_earlier_rounds_summary_does_not_judge_this_one(self):
        """A round that failed before writing its summary leaves the last
        one in place; an unverified earlier round is not this round's."""
        self._round_summary({"ok": False, "motion_status": "unverified"}, age_s=600)
        record = sb.run_batch([Step("assembly-round", "assembly", ("round",), round_summary=True)], self.project,
                              runner=FakeRunner({"round": RunResult(1, "refused", duration_s=1.0)}))
        self.assertEqual(record["steps"][0]["status"], sb.CHECK_FAILURE)

    def test_a_step_without_a_verdict_report_is_judged_by_its_exit(self):
        record = sb.run_batch([Step("check-power", "power", ("power",))], self.project, runner=FakeRunner())
        self.assertEqual(record["status"], sb.PASS)

    def test_each_layer_keeps_its_own_deadline(self):
        runner = FakeRunner()
        sb.run_batch([Step("m", "motion", ("m",)), Step("f", "final", ("f",), deadline_s=12.0)], self.project,
                     runner=runner)
        self.assertEqual([call[1] for call in runner.calls], [sb.DEFAULT_DEADLINES["motion"], 12.0])

    def test_the_record_is_written_and_the_packet_is_bounded(self):
        path = self.project / sb.RECORD
        long = "x" * 5000 + " the drive-frame lead hole meets the switch wire"
        record = sb.run_batch(self._steps(), self.project, runner=FakeRunner({"a": RunResult(1, long)}),
                              record_path=path)
        self.assertEqual(json.loads(path.read_text()), record)
        digest = sb._sha256_bytes(path.read_bytes())
        packet = sb.failure_packet(record, digest)
        self.assertEqual(packet["record_sha256"], digest)
        self.assertEqual([item["id"] for item in packet["failing"]], ["component:a"])
        excerpt = packet["failing"][0]["excerpt"]
        self.assertTrue(excerpt.endswith("meets the switch wire"))
        self.assertLessEqual(len(excerpt.encode()), sb.PACKET_EXCERPT_BYTES + 3)
        self.assertEqual([item["id"] for item in packet["passed"]], ["project", "component:b"])
        self.assertEqual(packet["skipped"], ["interface:x", "final"])
        self.assertEqual(packet["rules"], list(sb.REPAIR_RULES))
        with self.assertRaises(ValueError):
            sb.failure_packet(dict(record, status=sb.HARNESS_FAILURE), digest)

    def test_steps_must_be_well_formed(self):
        with self.assertRaises(ValueError):
            Step("x", "nowhere", ("x",))
        with self.assertRaises(ValueError):
            sb.run_batch([Step("x", "project", ("a",)), Step("x", "final", ("b",))], self.project,
                         runner=FakeRunner())

    def test_the_real_runner_classifies_real_processes(self):
        ok = sb.subprocess_runner([sys.executable, "-c", "print('fine')"], self.project, 30)
        self.assertEqual((ok.returncode, ok.output.strip()), (0, "fine"))
        bad = sb.subprocess_runner([sys.executable, "-c", "raise SystemExit(1)"], self.project, 30)
        self.assertEqual(sb.classify(bad)[0], sb.CHECK_FAILURE)
        crash = sb.subprocess_runner([sys.executable, "-c", "import nowhere_module"], self.project, 30)
        self.assertEqual(sb.classify(crash)[0], sb.HARNESS_FAILURE)
        slow = sb.subprocess_runner([sys.executable, "-c", "import time; time.sleep(5)"], self.project, 0.5)
        self.assertEqual(sb.classify(slow), (sb.HARNESS_FAILURE, "timed out"))
        missing = sb.subprocess_runner(["/nonexistent/tool"], self.project, 5)
        self.assertEqual(sb.classify(missing)[0], sb.HARNESS_FAILURE)
        env = sb.environment_runner({"PATH": "/usr/bin:/bin", "ONLY": "this"})(
            [sys.executable, "-c", "import os; print(sorted(k for k in os.environ if k in ('ONLY', 'HOME')))"],
            self.project, 30)
        self.assertEqual(env.output.strip(), "['ONLY']", "a host step sees only the environment it is given")

    def test_the_first_step_starts_in_a_project_that_does_not_exist_yet(self):
        project = self.project / "artifacts" / "make" / "r0001" / "product" / "cad"
        steps = [Step("prepare", "project", (sys.executable, "-c",
                                             "import os; open('made', 'w').write(os.getcwd())"))]
        record = sb.run_batch(steps, project)
        self.assertEqual(record["status"], sb.PASS, record["steps"][0].get("reason"))
        self.assertEqual(Path((project / "made").read_text()).resolve(), project.resolve())


class PlanTest(unittest.TestCase):
    def _inputs(self, **changes):
        base = dict(project=Path("/run/artifacts/make/r0001/product/cad"), python="/py",
                    skills_root=Path("/run/.agents/skills"), contract_path=Path("/run/WISH.json"),
                    roles=("body", "lid"), nozzle=0.4, coupled_interfaces=("hinge",), powered=True, moving=True,
                    concept_sha256="c" * 64, finalizer=("/py", "stage_proposal.py", "make"))
        base.update(changes)
        return sb.PlanInputs(**base)

    def _run_plan(self, **changes):
        return sb.run_plan(self._inputs(**changes), run_root=Path("/run"),
                           product_root=Path("/run/artifacts/make/r0001/product"),
                           source=Path("/run/work/seeded/spark-source.json"))

    def test_the_run_plan_holds_every_layer_in_order(self):
        steps = self._run_plan()
        self.assertEqual([step.layer for step in steps], sorted((step.layer for step in steps),
                                                                key=sb.LAYERS.index))
        self.assertEqual({step.layer for step in steps}, set(sb.LAYERS) - {"preflight"},
                         "the cheap gates layer is the design plan's; the run's final verification runs them")
        ids = [step.id for step in steps]
        for expected in ("prepare", "project", "shared-helpers", "component:body", "component:lid",
                         "interface:hinge", "bought-model", "check-power", "check-mount", "check-motion",
                         "assembly-round", "carry-assembly-review", "final-verification", "product", "parts",
                         "finalizer"):
            self.assertIn(expected, ids)
        self.assertLess(ids.index("product"), ids.index("parts"))
        parts = next(step for step in steps if step.id == "parts")
        self.assertEqual(parts.layer, "parts")
        self.assertIn("/run/artifacts/make/r0001/product/assembled.step.json", parts.inputs)
        # A repair that reruns final verification rewrites its report, so the
        # product step is never reused over a stale package.
        product = next(step for step in steps if step.id == "product")
        self.assertIn("measure/verification-pipeline.md", product.inputs)
        self.assertIn("/run/seed", product.inputs)
        self.assertEqual(ids[-1], "finalizer")
        rounds = [step for step in steps if step.layer == "components"]
        self.assertEqual([step.nonce_component for step in rounds], ["body", "lid"])
        final = next(step for step in steps if step.id == "final-verification")
        self.assertIn("--powered", final.argv)
        self.assertEqual(final.argv[final.argv.index("--check-motion") + 1], "true")
        carry = next(step for step in steps if step.id == "carry-assembly-review")
        self.assertEqual(carry.argv[-2:], ("--concept-sha256", "c" * 64))
        shared = next(step for step in steps if step.id == "shared-helpers")
        self.assertNotIn("--contract", shared.argv, "inside a run make_round reads the sealed contract")

    def test_the_assembly_round_has_at_least_the_motion_steps_allowance(self):
        """Issue #244: the round's check_motion and print gates share one
        geometry allowance, which make_round otherwise sets at 600 s."""
        for deadlines in ({}, {"assembly": 2400.0}):
            with self.subTest(deadlines=deadlines):
                steps = self._run_plan(deadlines=deadlines)
                round_step = next(step for step in steps if step.id == "assembly-round")
                self.assertTrue(round_step.round_summary)
                geometry = float(round_step.argv[round_step.argv.index("--geometry-seconds") + 1])
                deadline = round_step.deadline_s or sb.DEFAULT_DEADLINES["assembly"]
                self.assertEqual(geometry, deadline - sb.FINAL_REPORT_MARGIN_S)
        default = next(step for step in self._run_plan() if step.id == "assembly-round")
        geometry = float(default.argv[default.argv.index("--geometry-seconds") + 1])
        self.assertGreaterEqual(geometry, sb.DEFAULT_DEADLINES["motion"])

    def test_a_static_unpowered_toy_has_no_power_or_motion_steps(self):
        steps = self._run_plan(powered=False, moving=False, coupled_interfaces=())
        layers = {step.layer for step in steps}
        self.assertFalse({"power", "motion", "interfaces"} & layers)
        final = next(step for step in steps if step.id == "final-verification")
        self.assertIn("--unpowered", final.argv)
        self.assertEqual(final.argv[final.argv.index("--check-motion") + 1], "false")

    def test_a_run_plan_needs_its_finalizer_and_concept(self):
        with self.assertRaises(ValueError):
            self._run_plan(finalizer=())
        with self.assertRaises(ValueError):
            self._run_plan(concept_sha256=None)

    def test_the_design_plan_needs_no_run_state(self):
        steps = sb.design_plan(self._inputs())
        text = [" ".join(step.argv) for step in steps]
        for absent in ("--component", "--seed-nonce", "--carry-assembly-review", "stage_proposal",
                       "seeded_package product", "seeded_package parts", "--require-component-passes",
                       "SIGNATURE-REVIEW"):
            self.assertFalse(any(absent in line for line in text), absent)
        self.assertTrue(any("--print-gates-only" in line for line in text))
        shared = next(step for step in steps if step.id == "shared-helpers")
        self.assertIn("--contract", shared.argv, "outside a run make_round reads --contract")
        self.assertFalse(any(step.nonce_component for step in steps))

    def test_the_design_plan_covers_the_runs_whole_batch(self):
        """ADR 0098: interfaces, final verification and packaging run at the
        seal with the run's own tools, in the run's layer order."""
        steps = sb.design_plan(self._inputs())
        ids = [step.id for step in steps]
        self.assertEqual(ids, ["project", "shared-helpers", "preflight", "print-gates", "interface:hinge",
                               "bought-model", "check-power", "check-mount", "check-motion",
                               "final-verification", "package-check"])
        interface = steps[ids.index("interface:hinge")]
        self.assertEqual(interface.argv[2:], ("/run/artifacts/make/r0001/product/cad", "--interface", "hinge",
                                              "--contract", "/run/WISH.json"))
        final = steps[ids.index("final-verification")]
        run_final = next(step for step in self._run_plan() if step.id == "final-verification")
        design_only = {"--design", "--contract", "/run/WISH.json"}
        self.assertEqual([item for item in final.argv if item not in design_only
                          and not item.endswith("design-verification.md")],
                         [item for item in run_final.argv if not item.endswith("verification-pipeline.md")],
                         "the same gates as the run's final verification")
        self.assertIn("--design", final.argv)
        self.assertEqual(final.argv[final.argv.index("--contract") + 1], "/run/WISH.json",
                         "issue #241: the Bought Parts model reads the contract outside a run")
        self.assertEqual(final.argv[final.argv.index("--geometry-seconds") + 1], "3300",
                         "the analyses get the final layer's deadline less the report margin")
        self.assertEqual(final.verdict_report, sb.DESIGN_REPORT)
        self.assertEqual(run_final.verdict_report, "measure/verification-pipeline.md")
        bought = steps[ids.index("bought-model")]
        self.assertEqual(bought.argv[2:], ("/run/artifacts/make/r0001/product/cad", "--build",
                                           "--contract", "/run/WISH.json"))
        run_bought = next(step for step in self._run_plan() if step.id == "bought-model")
        self.assertNotIn("--contract", run_bought.argv, "in a run WISH.json gives the circuit")
        self.assertEqual(final.reports, (sb.DESIGN_REPORT,))
        self.assertNotIn("snap/SIGNATURE-REVIEW.json", final.inputs)
        package = steps[ids.index("package-check")]
        self.assertEqual(package.argv[1:], ("-m", "workshop.make.seeded_package", "check", "--project",
                                            "/run/artifacts/make/r0001/product/cad"))
        self.assertIn(sb.DESIGN_REPORT, package.inputs)

    def test_an_unpowered_final_names_unpowered_only_when_image_derived(self):
        for image_derived, flags in ((True, ["--image-derived", "--unpowered"]), (False, [])):
            with self.subTest(image_derived=image_derived):
                final = next(step for step in self._run_plan(powered=False, image_derived=image_derived)
                             if step.id == "final-verification")
                self.assertEqual([item for item in final.argv if item in
                                  ("--image-derived", "--unpowered", "--powered")], flags)

    def test_the_contracts_coupled_interfaces_in_order(self):
        contract = {"interfaces": [{"id": "a", "kind": "coupled"}, {"id": "b", "kind": "static"},
                                   {"id": "c", "kind": "coupled"}, "junk"]}
        self.assertEqual(sb.coupled_interface_ids(contract), ("a", "c"))
        self.assertEqual(sb.coupled_interface_ids({}), ())

    def test_deadlines_override_by_layer(self):
        steps = sb.design_plan(self._inputs(deadlines={"motion": 42.0}))
        self.assertEqual(next(step for step in steps if step.layer == "motion").deadline_s, 42.0)

    def _flag(self, step):
        return float(step.argv[step.argv.index("--geometry-seconds") + 1]) if "--geometry-seconds" in step.argv else None

    def test_a_toy_that_is_no_kit_keeps_its_print_gate_commands(self):
        """A pass recorded before kit allowances existed is still reused."""
        run = {step.id: step for step in self._run_plan()}
        design = {step.id: step for step in sb.design_plan(self._inputs())}
        for step in (run["component:body"], run["component:lid"], design["print-gates"]):
            self.assertIsNone(self._flag(step))
            self.assertIsNone(step.deadline_s)
        self.assertEqual(self._flag(run["final-verification"]), 3300.0)
        self.assertIsNone(run["final-verification"].deadline_s)

    def test_a_kit_component_round_gets_time_for_every_printed_part(self):
        """The Amsterdam kit's 20-Part canal base ran out of make_round's
        600 s allowance and the layer's 900 s deadline at its seal."""
        run = {step.id: step for step in self._run_plan(printed_parts={"body": 20, "lid": 1})}
        body, lid = run["component:body"], run["component:lid"]
        self.assertEqual(self._flag(body), 20 * sb.KIT_PART_GEOMETRY_S)
        # and its tree check's time (#392 follow-up), here an empty tree's
        self.assertEqual(body.deadline_s, 20 * sb.KIT_PART_GEOMETRY_S + sb.FINAL_REPORT_MARGIN_S + sb.TREE_MIN_S)
        self.assertEqual(body.argv[-1], "--json")
        # A one-Part Component never gets less than a toy that is no kit.
        self.assertEqual(self._flag(lid), sb.DEFAULT_GEOMETRY_S)
        self.assertEqual(lid.deadline_s, sb.DEFAULT_DEADLINES["components"] + sb.TREE_MIN_S)

    def test_the_design_print_gates_share_one_allowance_for_every_kit_part(self):
        gates = next(step for step in sb.design_plan(self._inputs(printed_parts={"body": 20, "lid": 30}))
                     if step.id == "print-gates")
        self.assertEqual(self._flag(gates), 50 * sb.KIT_PART_GEOMETRY_S)
        self.assertEqual(gates.deadline_s, 50 * sb.KIT_PART_GEOMETRY_S + sb.FINAL_REPORT_MARGIN_S)

    def test_the_whole_build_steps_cover_every_kit_part(self):
        kit = {"body": 20, "lid": 30}
        for plan in (self._run_plan(printed_parts=kit), sb.design_plan(self._inputs(printed_parts=kit))):
            final = next(step for step in plan if step.id == "final-verification")
            self.assertEqual(self._flag(final), 50 * sb.KIT_PART_GEOMETRY_S)
            self.assertEqual(final.deadline_s, 50 * sb.KIT_PART_GEOMETRY_S + sb.FINAL_REPORT_MARGIN_S)
        round_step = next(step for step in self._run_plan(printed_parts=kit) if step.id == "assembly-round")
        self.assertEqual(self._flag(round_step), 50 * sb.KIT_PART_GEOMETRY_S)
        self.assertEqual(round_step.deadline_s, 50 * sb.KIT_PART_GEOMETRY_S + sb.FINAL_REPORT_MARGIN_S)
        # A small kit keeps the layer's larger allowance.
        small = next(step for step in self._run_plan(printed_parts={"body": 2}) if step.id == "final-verification")
        self.assertEqual(self._flag(small), 3300.0)
        self.assertIsNone(small.deadline_s)

    def test_a_kit_exports_no_parts_and_checks_no_package(self):
        """ADR 0104 decision 4: a kit's print layout is the only STEP it
        ships, so neither the run nor the seal exports or checks
        per-occurrence parts (the Amsterdam kit's seal failed its
        package-check on Part names the Factory path never reads)."""
        kit = {"body": 20, "lid": 1}
        run = [step.id for step in self._run_plan(printed_parts=kit)]
        self.assertNotIn("parts", run)
        self.assertEqual(run[-3:], ["final-verification", "product", "finalizer"])
        design = [step.id for step in sb.design_plan(self._inputs(printed_parts=kit))]
        self.assertNotIn("package-check", design)
        self.assertEqual(design[-1], "final-verification")
        # A toy that is no kit keeps both.
        self.assertIn("parts", [step.id for step in self._run_plan()])
        self.assertIn("package-check", [step.id for step in sb.design_plan(self._inputs())])

    def test_a_layer_override_never_cuts_a_kit_steps_time(self):
        steps = self._run_plan(printed_parts={"body": 20}, deadlines={"components": 100.0})
        body = next(step for step in steps if step.id == "component:body")
        lid = next(step for step in steps if step.id == "component:lid")
        self.assertEqual(body.deadline_s, 20 * sb.KIT_PART_GEOMETRY_S + sb.FINAL_REPORT_MARGIN_S + sb.TREE_MIN_S)
        self.assertEqual(lid.deadline_s, 100.0)

    def test_final_verification_gets_time_for_every_component_of_a_toy_that_is_no_kit(self):
        """The Kyoto tray's 75 Components took 4302 s in final verification
        and its seal ran out of the final layer's 3600 s deadline."""
        roles = tuple("c%02d" % index for index in range(75))
        need = 75 * sb.FINAL_COMPONENT_S
        run = {step.id: step for step in self._run_plan(roles=roles)}
        design = {step.id: step for step in sb.design_plan(self._inputs(roles=roles))}
        for step in (run["final-verification"], design["final-verification"], design["preflight"]):
            with self.subTest(step=step.id):
                self.assertEqual(self._flag(step), need)
                self.assertEqual(step.deadline_s, need + sb.FINAL_REPORT_MARGIN_S)
                self.assertGreater(step.deadline_s, 4302.0, "Kyoto's measured final verification fits")
        # The run's assembly round works through the whole build too.
        self.assertEqual(self._flag(run["assembly-round"]), need)
        self.assertEqual(run["assembly-round"].deadline_s, need + sb.FINAL_REPORT_MARGIN_S)
        # Only the whole-build steps grow: a toy that is no kit keeps its
        # component rounds and print gates as they were.
        for step in (run["component:c00"], design["print-gates"]):
            self.assertIsNone(self._flag(step))
            self.assertIsNone(step.deadline_s)

    def test_a_small_toy_keeps_the_final_layers_own_deadline(self):
        """22 Components fit the layer's 3300 s; the command and its reuse
        key stay as they were."""
        roles = tuple("c%02d" % index for index in range(int(3300.0 // sb.FINAL_COMPONENT_S)))
        plan = {step.id: step for step in self._run_plan(roles=roles)}
        for step in (plan["final-verification"], plan["assembly-round"]):
            self.assertEqual(self._flag(step), 3300.0)
            self.assertIsNone(step.deadline_s)
        bigger = next(step for step in self._run_plan(roles=roles + ("extra",)) if step.id == "final-verification")
        self.assertEqual(bigger.deadline_s, (len(roles) + 1) * sb.FINAL_COMPONENT_S + sb.FINAL_REPORT_MARGIN_S)

    def test_a_kit_final_gets_the_larger_of_its_parts_and_its_components(self):
        roles = tuple("c%02d" % index for index in range(30))
        few_parts = next(step for step in self._run_plan(roles=roles, printed_parts={"c00": 2})
                         if step.id == "final-verification")
        self.assertEqual(self._flag(few_parts), 30 * sb.FINAL_COMPONENT_S)
        many_parts = next(step for step in self._run_plan(roles=roles, printed_parts={"c00": 40})
                          if step.id == "final-verification")
        self.assertEqual(self._flag(many_parts), 40 * sb.KIT_PART_GEOMETRY_S)
        round_step = next(step for step in self._run_plan(roles=roles, printed_parts={"c00": 2})
                          if step.id == "assembly-round")
        self.assertEqual(self._flag(round_step), 30 * sb.FINAL_COMPONENT_S)

    def test_a_final_layer_override_never_cuts_the_components_time_and_may_raise_it(self):
        roles = tuple("c%02d" % index for index in range(75))
        need = 75 * sb.FINAL_COMPONENT_S + sb.FINAL_REPORT_MARGIN_S
        low = {step.id: step for step in self._run_plan(roles=roles, deadlines={"final": 600.0, "assembly": 600.0})}
        self.assertEqual(low["final-verification"].deadline_s, need)
        self.assertEqual(low["assembly-round"].deadline_s, need)
        high = next(step for step in self._run_plan(roles=roles, deadlines={"final": 20000.0})
                    if step.id == "final-verification")
        self.assertEqual(high.deadline_s, 20000.0)
        self.assertEqual(self._flag(high), 20000.0 - sb.FINAL_REPORT_MARGIN_S)

    def test_the_kit_printed_parts_come_from_the_assembly_tree(self):
        tree = {"parts": [{"id": "A", "filament": "navy"}, {"id": "B", "filament": "red"},
                          {"id": "P", "bought": "pin-1.5"}],
                "components": [{"geometry": "base", "parts": ["A", "B", "P"]}, {"geometry": "lid", "parts": ["P"]}],
                "steps": []}
        self.assertEqual(sb.kit_printed_parts({"schema_version": 11, "assembly_tree": tree}), {"base": 2, "lid": 0})
        self.assertEqual(sb.kit_printed_parts({"schema_version": 6, "assembly_tree": tree}), {})
        self.assertEqual(sb.kit_printed_parts({"schema_version": 11}), {})


class DesignTreeStepsTest(unittest.TestCase):
    """The seal and its preflight run each kit Component's own Assembly Tree
    steps, as the run's component rounds do (the Miami kit sealed, then
    every component round failed steps S20-S64 the seal never ran)."""

    KIT = {"body": 3, "lid": 1}

    def _inputs(self, **changes):
        base = dict(project=Path("/proof"), python="/py", skills_root=ROOT / "src/workshop/make/skills",
                    contract_path=Path("/proof/CONTRACT.md"), roles=("body", "lid"), nozzle=0.4,
                    coupled_interfaces=(), powered=False, moving=False, printed_parts=self.KIT)
        base.update(changes)
        return sb.PlanInputs(**base)

    def test_a_kit_seal_runs_every_components_tree_steps_in_the_cheap_layer(self):
        steps = sb.design_plan(self._inputs())
        ids = [step.id for step in steps]
        self.assertEqual(ids, ["project", "shared-helpers", "preflight", "tree:body", "tree:lid", "print-gates",
                               "final-verification"])
        for role in ("body", "lid"):
            step = steps[ids.index("tree:%s" % role)]
            self.assertEqual(step.layer, "preflight")
            self.assertIn(step.layer, sb.PREFLIGHT_LAYERS, "seal_proof preflight runs it too")
            self.assertEqual(step.argv[2:], ("/proof", "--component", role, "--nozzle", "0.4", "--json"))
            self.assertIn("part_%s.step.py" % role, step.inputs)
            self.assertIn(sb.sources_of(role), step.inputs)
            self.assertIn("tree", step.inputs, "the installed tree joins the reuse key")
            self.assertEqual(step.env_keys, sb.PRINT_GATES_ENV, "its builds read the fit table")

    TREE = {
        "kind": "workshop-kit-tree", "schema_version": 11, "pieces": [],
        "geometries": [{"id": "body", "count": 2, "wall_min_mm": 1.2}, {"id": "lid", "count": 1, "wall_min_mm": 1.2}],
        "catalogue": {"filaments": {"oak": {"hex": "#b5834f"}}, "bought_parts": {}},
        "assembly_tree": {
            "parts": [{"id": "A01-base", "name": "Base", "filament": "oak"},
                      {"id": "A02-peg", "name": "Peg", "filament": "oak"},
                      {"id": "A03-cap", "name": "Cap", "filament": "oak"},
                      {"id": "B01-lid", "name": "Lid", "filament": "oak"}],
            "steps": [
                {"id": "S01-pegs", "output": "Pegged", "count": 1, "joint": "peg-socket", "text": "Pegs in.",
                 "inputs": [{"id": "A01-base"}, {"id": "A02-peg", "count": 2, "direction": [0, 0, -1],
                                                 "press_mm": 0.1}]},
                {"id": "S02-cap", "output": "Body", "count": 2, "joint": "glue", "text": "Cap on.",
                 "inputs": [{"id": "S01-pegs"}, {"id": "A03-cap", "direction": [0, 0, -1]}]},
                {"id": "S03-lid", "output": "Box", "count": 1, "joint": "peg-socket", "text": "Lid on.",
                 "inputs": [{"id": "S02-cap", "count": 2}, {"id": "B01-lid", "direction": [0, 0, -1],
                                                             "press_mm": 0.1}]}],
            "components": [{"geometry": "body", "parts": ["A01-base", "A02-peg", "A03-cap"]},
                           {"geometry": "lid", "parts": ["B01-lid"]}],
        },
    }

    def test_the_host_counts_each_components_tree_as_kit_tree_does(self):
        """The batch's deadline is the run-local tool's own: the same
        insertions and press insertions, the same seconds."""
        tool = runpy.run_path(str(ROOT / "src/workshop/make/skills/make-round/scripts/kit_tree.py"))
        loads = sb.kit_tree_loads(self.TREE)
        plan = tool["Plan"](self.TREE)
        self.assertEqual(loads, {role: tool["tree_load"](plan, role) for role in ("body", "lid")})
        # two bodies, each two pressed pegs and a cap; the lid's step spans Components
        self.assertEqual(loads, {"body": {"insertions": 6, "presses": 4}, "lid": {"insertions": 0, "presses": 0}})
        self.assertEqual(tool["tree_load"](plan, None), {"insertions": 1, "presses": 1})
        for name in ("TREE_MIN_S", "TREE_INSERTION_S", "TREE_PRESS_S"):
            self.assertEqual(getattr(sb, name), tool[name], name)
        inputs = self._inputs(tree_loads=loads)
        self.assertEqual(sb.tree_seconds(inputs, "body"), tool["tree_seconds"](loads["body"]))
        self.assertEqual(sb.kit_tree_loads({"schema_version": 6, "assembly_tree": self.TREE["assembly_tree"]}), {})

    def test_a_tree_steps_deadline_grows_with_its_insertions_and_presses(self):
        """Kyoto's tree, 188 insertions of which 128 press, took about
        13,900 s: past the preflight layer's flat hour."""
        kyoto = {"body": {"insertions": 188, "presses": 128}, "lid": {"insertions": 0, "presses": 0}}
        steps = {step.id: step for step in sb.tree_steps(self._inputs(tree_loads=kyoto))}
        need = sb.TREE_MIN_S + 188 * sb.TREE_INSERTION_S + 128 * sb.TREE_PRESS_S + sb.FINAL_REPORT_MARGIN_S
        self.assertEqual(steps["tree:body"].deadline_s, need)
        self.assertGreater(need, 2 * 13900.0, "headroom over Kyoto's measured time")
        self.assertEqual(steps["tree:lid"].deadline_s, sb.TREE_MIN_S + sb.FINAL_REPORT_MARGIN_S)
        self.assertGreaterEqual(steps["tree:lid"].deadline_s, sb.DEFAULT_DEADLINES["preflight"])
        # the seal and its preflight run these very steps
        design = {step.id: step for step in sb.design_plan(self._inputs(tree_loads=kyoto))}
        self.assertEqual(design["tree:body"].deadline_s, need)

    def test_a_kit_component_rounds_deadline_holds_its_tree_check(self):
        kyoto = {"body": {"insertions": 188, "presses": 128}, "lid": {"insertions": 2, "presses": 0}}
        inputs = dict(project=Path("/run/artifacts/make/r0001/product/cad"), python="/py",
                      skills_root=Path("/run/.agents/skills"), contract_path=Path("/run/WISH.json"),
                      roles=("body", "lid"), nozzle=0.4, concept_sha256="c" * 64,
                      finalizer=("/py", "stage_proposal.py", "make"), printed_parts=self.KIT, tree_loads=kyoto)
        steps = {step.id: step for step in sb.run_plan(sb.PlanInputs(**inputs), run_root=Path("/run"),
                                                        product_root=Path("/run/artifacts/make/r0001/product"),
                                                        source=Path("/run/work/seeded/spark-source.json"))}
        tree = sb.TREE_MIN_S + 188 * sb.TREE_INSERTION_S + 128 * sb.TREE_PRESS_S
        gates = max(sb.DEFAULT_DEADLINES["components"],
                    max(sb.DEFAULT_GEOMETRY_S, 3 * sb.KIT_PART_GEOMETRY_S) + sb.FINAL_REPORT_MARGIN_S)
        self.assertEqual(steps["component:body"].deadline_s, gates + tree)
        self.assertEqual(steps["component:lid"].deadline_s,
                         sb.DEFAULT_DEADLINES["components"] + sb.TREE_MIN_S + 2 * sb.TREE_INSERTION_S)

    def test_make_rounds_tree_job_takes_kit_trees_allowance(self):
        make_round = runpy.run_path(str(ROOT / "src/workshop/make/skills/make-round/scripts/make_round"))
        tool = runpy.run_path(str(ROOT / "src/workshop/make/skills/make-round/scripts/kit_tree.py"))
        plan = tool["Plan"](self.TREE)
        job = make_round["tree_job"](Path("/proof"), Path("/out"), 0.4, "body", self.TREE)
        self.assertEqual(job["timeout"], max(make_round["FULL_TIMEOUT_SECONDS"],
                                             tool["tree_seconds"](tool["tree_load"](plan, "body"))))
        across = make_round["tree_job"](Path("/proof"), Path("/out"), 0.4, None, self.TREE)
        self.assertEqual(across["timeout"], tool["tree_seconds"](tool["tree_load"](plan, None)))
        # a tree it cannot plan keeps the round's own timeout; kit_tree says why
        self.assertEqual(make_round["tree_job"](Path("/proof"), Path("/out"), 0.4, "body")["timeout"],
                         make_round["FULL_TIMEOUT_SECONDS"])

    def test_a_toy_that_is_no_kit_has_no_tree_steps(self):
        self.assertEqual(sb.tree_steps(self._inputs(printed_parts={})), [])
        ids = [step.id for step in sb.design_plan(self._inputs(printed_parts={}))]
        self.assertFalse([item for item in ids if item.startswith("tree:")])

    def test_the_tree_step_is_make_rounds_own_component_round_command(self):
        """No second copy of the check: the same script with make_round's
        tree_job arguments, less the round's manifest file."""
        make_round = runpy.run_path(str(ROOT / "src/workshop/make/skills/make-round/scripts/make_round"))
        for role in ("body", "lid"):
            job = make_round["tree_job"](Path("/proof"), Path("/out"), 0.4, role)
            command = [str(item) for item in job["command"]]
            at = command.index("--manifest")
            del command[at:at + 2]
            step = next(item for item in sb.tree_steps(self._inputs()) if item.id == "tree:%s" % role)
            self.assertEqual(Path(step.argv[1]).resolve(), Path(command[1]).resolve())
            self.assertEqual(list(step.argv[2:]), command[2:])

    def test_a_failing_tree_step_refuses_the_preflight_and_skips_the_print_gates(self):
        project = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (project / "params.py").write_text("A = 1\n")
        (project / "measure").mkdir()
        for report in (sb.PREFLIGHT_REPORT, sb.DESIGN_REPORT):
            (project / report).write_text("- Result: **PASS**\n")
        failing = RunResult(1, "tree: S20-loungers-slots: T11-lounger#1 cannot go in alone along [0, 0, -12]")
        plan = sb.design_plan(self._inputs(project=project))
        preflight = sb.run_batch(plan, project, runner=FakeRunner({"body": failing}),
                                 record_path=project / "measure/seal-preflight.json", layers=sb.PREFLIGHT_LAYERS)
        by_id = {item["id"]: item for item in preflight["steps"]}
        self.assertEqual(preflight["status"], sb.CHECK_FAILURE)
        self.assertEqual(preflight["failed_layer"], "preflight")
        self.assertEqual(by_id["tree:body"]["status"], sb.CHECK_FAILURE)
        self.assertIn("cannot go in alone", by_id["tree:body"]["excerpt"])
        self.assertEqual(by_id["tree:lid"]["status"], sb.PASS)
        runner = FakeRunner({"body": failing})
        seal = sb.run_batch(plan, project, runner=runner, record_path=project / sb.RECORD)
        by_id = {item["id"]: item for item in seal["steps"]}
        self.assertEqual(seal["status"], sb.CHECK_FAILURE)
        for later in ("print-gates", "final-verification"):
            self.assertEqual(by_id[later]["status"], sb.SKIPPED)
        self.assertFalse(any("--print-gates-only" in call[0] for call in runner.calls))


class ComposedSourceTest(unittest.TestCase):
    def test_the_concept_hash_is_the_finalizers(self):
        spec = importlib.util.spec_from_file_location(
            "stage_proposal_for_batch",
            ROOT / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        concept = {"title": "Lamp", "summary": "Glows — softly.", "interaction": "Slide", "envelope_mm": [1, 2, 3],
                   "mechanisms": ["slider"], "components": [{"id": "body"}]}
        self.assertEqual(sb.concept_sha256(concept), module.json_sha256(concept))

    def test_the_spark_source_copies_the_assignment_and_the_sealed_concept(self):
        product = {"concept": {"title": "Lamp"}, "research": {"notes": "x"}}
        assignment = {"selected_inventor_id": "rowan-vale", "ranking": [{"inventor_id": "rowan-vale"}],
                      "assignment_sha256": "a" * 64}
        self.assertEqual(sb.compose_spark_source(product, assignment), {
            "selected_inventor_id": "rowan-vale", "ranking": [{"inventor_id": "rowan-vale"}],
            "concept": {"title": "Lamp"}, "research": {"notes": "x"}})


if __name__ == "__main__":
    unittest.main()


class PrintGateReuseKeyTest(unittest.TestCase):
    """ADR 0098 amendment 2026-11-17: the print-gates key binds every source a
    part file reaches, a module loaded by name included, and its fit table;
    a recorded pass is reused only while its summary passed outright."""

    def setUp(self):
        from workshop.make import batch_sources

        self.closure = batch_sources.source_closure
        self.project = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.write("params.py", "A = 1\n")
        self.write("part_a.step.py", "from params import A\n")
        self.write("unused.py", "B = 2\n")
        self.write("kitmap.json", "{}")
        self.write("toy_spec.md", "# spec\n")
        self.write("measure/report.json", "{}")
        self.write("snap/iso.png", "png")
        self.write("part_a.step", "STEP")

    def write(self, name, text):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_a_static_closure_binds_imports_and_data_but_no_output(self):
        self.assertEqual(set(self.closure(self.project, "a")), {"part_a.step.py", "params.py", "kitmap.json"})

    def test_a_module_loaded_by_name_binds_every_project_module(self):
        self.write("part_a.step.py", "import kitparts\n")
        self.write("kitparts.py", "import importlib\nM = importlib.import_module('base4')\n")
        self.write("base4.py", "X = 1\n")
        self.write("published/part_q.py", "Q = 1\n")
        self.write("measure/check_spec.py", "pass\n")
        bound = set(self.closure(self.project, "a"))
        self.assertTrue({"kitparts.py", "base4.py", "published/part_q.py", "unused.py"} <= bound)
        self.assertNotIn("measure/check_spec.py", bound)

    def test_an_unreadable_module_binds_every_project_module(self):
        self.write("part_a.step.py", "import broken\n")
        self.write("broken.py", "def (:\n")
        self.assertIn("unused.py", self.closure(self.project, "a"))

    def _gates(self):
        return Step("print-gates", "components", ("round", "--print-gates-only"),
                    inputs=(sb.sources_of(),), reports=("measure/print-gates/summary.json",),
                    env_keys=("WORKSHOP_FIT_TABLE",), gates_summary="measure/print-gates/summary.json")

    def test_the_key_changes_with_a_kit_module_and_the_fit_table_only(self):
        from unittest import mock

        self.write("part_a.step.py", "import kitparts\n")
        self.write("kitparts.py", "import importlib\nM = importlib.import_module('base4')\n")
        self.write("base4.py", "X = 1\n")
        step = self._gates()
        key = sb.step_key(step, self.project)
        self.write("toy_spec.md", "# reworded\n")
        self.write("measure/report.json", '{"a": 1}')
        self.assertEqual(sb.step_key(step, self.project), key)
        self.write("base4.py", "X = 2\n")
        changed = sb.step_key(step, self.project)
        self.assertNotEqual(changed, key)
        with mock.patch.dict("os.environ", {"WORKSHOP_FIT_TABLE": "other"}):
            self.assertNotEqual(sb.step_key(step, self.project), changed)

    def _summary(self, **change):
        document = {"ok": True, "build": {"a": {"verdict": "PASS"}},
                    "print": {"a": {"verdict": "PASS", "final": {"check_overhang": {"verdict": "PASS"}}}},
                    "sheets": {"verdict": "PASS"}, "interference": {"verdict": "pass"}}
        document.update(change)
        self.write("measure/print-gates/summary.json", json.dumps(document))

    def test_only_an_outright_pass_counts(self):
        name = "measure/print-gates/summary.json"
        self._summary()
        self.assertTrue(sb.gates_summary_passed(self.project, name))
        failing = {
            "not ok": {"ok": False},
            "a build fails": {"build": {"a": {"verdict": "FAIL"}}},
            "a final check is unverified": {
                "print": {"a": {"verdict": "PASS", "final": {"check_thickness": {"verdict": "UNVERIFIED"}}}}},
            "sheets fail": {"sheets": {"verdict": "FAIL"}},
            "interference unverified": {"interference": {"verdict": "unverified"}},
            "nothing gated": {"print": {}},
        }
        for name_, change in failing.items():
            with self.subTest(name_):
                self._summary(**change)
                self.assertFalse(sb.gates_summary_passed(self.project, name))
        (self.project / name).write_text("not json")
        self.assertFalse(sb.gates_summary_passed(self.project, name))

    def test_a_pass_is_reused_only_on_its_key_and_its_summary(self):
        step = self._gates()

        def run(summary):
            def runner(argv, cwd, timeout):
                self._summary(**summary)
                return RunResult(0, "ok", duration_s=1.0)
            return runner

        first = sb.run_batch([step], self.project, runner=run({}))
        self.assertEqual(first["steps"][0]["status"], sb.PASS)
        never = lambda argv, cwd, timeout: self.fail("a reusable pass ran again")
        second = sb.run_batch([step], self.project, runner=never, previous=first)
        self.assertEqual(second["steps"][0]["status"], sb.REUSED)
        reran = []
        again = lambda argv, cwd, timeout: reran.append(argv) or RunResult(0, "ok")
        self._summary(note="rewritten by a standalone run")
        sb.run_batch([step], self.project, runner=again, previous=second)
        self.assertEqual(len(reran), 1, "a summary that is not the recorded bytes reruns")
        unverified = sb.run_batch([step], self.project, runner=run({"interference": {"verdict": "unverified"}}))
        sb.run_batch([step], self.project, runner=again, previous=unverified)
        self.assertEqual(len(reran), 2, "an unverified summary is never reused")
        failed = sb.run_batch([step], self.project, runner=lambda *a: RunResult(1, "FAIL overhang"))
        sb.run_batch([step], self.project, runner=again, previous=failed)
        self.assertEqual(len(reran), 3, "a failure is never reused")
