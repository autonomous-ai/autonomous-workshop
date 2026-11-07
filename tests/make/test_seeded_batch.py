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
        self.assertEqual({step.layer for step in steps}, set(sb.LAYERS))
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
        self.assertEqual(ids, ["project", "shared-helpers", "print-gates", "interface:hinge", "bought-model",
                               "check-power", "check-mount", "check-motion", "final-verification",
                               "package-check"])
        interface = steps[ids.index("interface:hinge")]
        self.assertEqual(interface.argv[2:], ("/run/artifacts/make/r0001/product/cad", "--interface", "hinge",
                                              "--contract", "/run/WISH.json"))
        final = steps[ids.index("final-verification")]
        run_final = next(step for step in self._run_plan() if step.id == "final-verification")
        self.assertEqual([item for item in final.argv if item != "--design"
                          and not item.endswith("design-verification.md")],
                         [item for item in run_final.argv if not item.endswith("verification-pipeline.md")],
                         "the same gates as the run's final verification")
        self.assertIn("--design", final.argv)
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
