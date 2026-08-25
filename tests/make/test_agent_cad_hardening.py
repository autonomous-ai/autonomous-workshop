import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.make.agent import (
    CAD_RUNTIME_PROBE_TIMEOUT_SECONDS,
    LockedCadSkillBuilder,
    MAKE_GENERATOR_VERSION,
)
from workshop.playtest.agent import (
    PRUSASLICER_VERSION,
    PrusaSlicerPrintCheck,
    WorkshopMechanicalVerifier,
    _recheck_locked_cad,
    _validate_digital_check,
    default_mechanical_check,
    default_motion_check,
    default_print_check,
)
from workshop.make.contracts import Made
from workshop.playtest.contracts import PlaytestContext
from workshop.outcomes import WaitingFor
from workshop.wish import Wish
from workshop.contributors.taste import load_taste
from workshop.product.blueprints import ToyBlueprint
from tests.make.test_agent_make import make_action


class FakeCadCommandRunner:
    def __init__(self, action):
        self.action = action
        self.calls = []
        self.sizes = {
            "part_%s.step" % part["part_id"].replace("-", "_"): [
                float(part["size_mm"][axis]) for axis in ("x", "y", "z")
            ]
            for part in action["parts"]
        }

    def __call__(
        self,
        command,
        *,
        cwd,
        input,
        capture_output,
        text,
        check,
        timeout,
        env,
    ):
        del capture_output, text, check, timeout
        cwd = Path(cwd)
        self.calls.append((list(command), cwd, input, dict(env)))
        if len(command) > 1 and command[1] == "-c":
            return subprocess.CompletedProcess(command, 0, "workshop-cad-runtime-ok\n", "")
        tool = Path(command[1]).name
        if tool == "check_layout":
            return subprocess.CompletedProcess(
                command, 0, json.dumps({"ok": True, "findings": []}), ""
            )
        if tool == "gen":
            for entry in command:
                if str(entry).endswith(".step.py"):
                    (cwd / str(entry)[:-3]).write_bytes(
                        ("ISO-10303-21;\n%s\nEND-ISO-10303-21;\n" % entry).encode()
                    )
            return subprocess.CompletedProcess(command, 0, "{}\n", "")
        if tool == "export":
            output = command[command.index("--stl") + 1]
            (cwd / output).write_bytes(
                ("solid %s\nendsolid %s\n" % (output, output)).encode()
            )
            return subprocess.CompletedProcess(command, 0, json.dumps({"ok": True}), "")
        if tool == "inspect":
            responses = []
            for line in str(input).splitlines():
                request = json.loads(line)
                operation, target = request["argv"][:2]
                if operation == "refs":
                    size = self.sizes.get(target, [200.0, 100.0, 20.0])
                    result = {
                        "ok": True,
                        "tokens": [
                            {
                                "entryFacts": {
                                    "size": size,
                                    "center": [110.0, 110.0, float(size[2]) / 2.0],
                                }
                            }
                        ],
                    }
                elif operation == "validate":
                    result = {
                        "ok": True,
                        "entry": target,
                        "occurrenceCount": 1,
                        "failureCount": 0,
                        "parts": [],
                        "errors": [],
                    }
                elif operation == "diff":
                    result = {
                        "ok": True,
                        "diff": {
                            "topologyChanged": False,
                            "geometryChanged": False,
                            "bboxChanged": False,
                            "kindChanged": False,
                        },
                    }
                else:
                    result = {
                        "ok": True,
                        "entry": target,
                        "clashCount": 0,
                        "clashes": [],
                        "errors": [],
                    }
                responses.append(
                    json.dumps(
                        {
                            "id": request["id"],
                            "ok": True,
                            "exitCode": 0,
                            "result": result,
                        },
                        separators=(",", ":"),
                    )
                )
            return subprocess.CompletedProcess(command, 0, "\n".join(responses) + "\n", "")
        if tool == "check_fit":
            rows = [
                {
                    "path": "part_%s.step.py" % part["part_id"].replace("-", "_"),
                    "bed": [220.0, 220.0],
                    "minZ": 0.0,
                    "sizeX": float(part["size_mm"]["x"]),
                    "sizeY": float(part["size_mm"]["y"]),
                    "sizeZ": float(part["size_mm"]["z"]),
                    "volume": 100.0,
                    "solids": 1,
                    "bodies": 1,
                }
                for part in self.action["parts"]
            ]
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(
                    {
                        "ok": True,
                        "root": str(cwd),
                        "bed": [220.0, 220.0],
                        "parts": rows,
                        "findings": [],
                        "notes": [],
                    }
                ),
                "",
            )
        if tool == "check_mesh":
            return subprocess.CompletedProcess(
                command,
                0,
                "part: 12 triangles\n  PASS  watertight (no open edges) 0 boundary edges\n"
                "  PASS  manifold edges 0 edges shared by >2 faces\nRESULT: printable\n",
                "",
            )
        if tool == "check_thickness":
            return subprocess.CompletedProcess(
                command,
                0,
                "part: 1.00 cm3 solid, grid 0.400 mm\n"
                "  PASS  wall >= 0.80 mm 0% below\nRESULT: printable at this wall\n",
                "",
            )
        raise AssertionError("unexpected command %r" % command)


class FakePrusaRunner:
    def __init__(self, version=PRUSASLICER_VERSION):
        self.version = version
        self.calls = []

    def __call__(
        self,
        command,
        *,
        cwd,
        input,
        capture_output,
        text,
        check,
        timeout,
        env,
    ):
        del input, capture_output, text, check, timeout
        self.calls.append((list(command), dict(env)))
        if "--help" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                "PrusaSlicer-%s based on Slic3r...\n" % self.version,
                "",
            )
        output = Path(command[command.index("--output") + 1])
        output.write_text(
            "; generated by PrusaSlicer %s on a fixed fixture\n" % self.version
            + "; estimated printing time (normal mode) = 4m 12s\n"
            + "; filament used [mm] = 120.50\n"
            + "; filament used [g] = 0.36\n"
            + "G1 X1 Y1 E0.1\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "sliced\n", "")


class FakeMechanicalCadBuilder:
    def __init__(self):
        self.calls = []

    def check_motion(self, root, manifest, *, command_id):
        self.calls.append((Path(root), manifest, command_id))
        return {
            "returncode": 0,
            "result": {
                "ok": True,
                "project": ".",
                "assembly": "product.step.py",
                "results": [
                    {
                        "id": condition["id"],
                        "check": condition["check"],
                        "status": "pass",
                        "expect": "clear",
                        "clear": True,
                        "steps": condition["inputs"]["steps"],
                        "detail": "clear across the exact rigid sweep",
                    }
                    for condition in manifest["conditions"]
                ],
            },
        }


class AgentCadHardeningTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        inventor = self.root / "inventor"
        inventor.mkdir()
        (inventor / "TASTE.md").write_text(
            "---\nname: Test Inventor\ndescription: Exact mechanical toys.\n---\n"
            "# Taste\n\nNever promote digital evidence into physical proof.\n",
            encoding="utf-8",
        )
        self.taste = load_taste(inventor)

    def tearDown(self):
        self.temporary.cleanup()

    def playtest_context(self, lane="little-worlds"):
        artifact = self.root / ("artifact-" + lane)
        (artifact / "cad").mkdir(parents=True)
        action = make_action()
        (artifact / "cad" / "design.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "kind": "workshop-step-first-parametric-design",
                    "generator": {
                        "id": "workshop-locked-step-cad",
                        "version": MAKE_GENERATOR_VERSION,
                    },
                    "action": action,
                }
            ),
            encoding="utf-8",
        )
        for relative, source in LockedCadSkillBuilder._project_sources(action).items():
            (artifact / "cad" / relative).write_text(source, encoding="utf-8")
        for name in ("part_base.stl", "part_token.stl"):
            (artifact / "cad" / name).write_text(
                "solid %s\nendsolid %s\n" % (name, name), encoding="utf-8"
            )
        (artifact / "cad" / "print_plate.stl").write_text(
            "solid plate\nendsolid plate\n", encoding="utf-8"
        )
        (artifact / "assembled.step").write_text(
            "ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8"
        )
        (artifact / "assembled.stl").write_text(
            "solid product\nendsolid product\n", encoding="utf-8"
        )
        print_sha = hashlib.sha256(
            (artifact / "cad" / "print_plate.stl").read_bytes()
        ).hexdigest()
        assembled_step_sha = hashlib.sha256(
            (artifact / "assembled.step").read_bytes()
        ).hexdigest()
        assembled_stl_sha = hashlib.sha256(
            (artifact / "assembled.stl").read_bytes()
        ).hexdigest()
        (artifact / "playtest").mkdir()
        (artifact / "validation").mkdir()
        (artifact / "validation" / "cad-build.json").write_text(
            json.dumps({"schema_version": 2, "passed": True}), encoding="utf-8"
        )
        (artifact / "playtest" / "mechanical.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "kind": "workshop.locked-cad-mechanical-declaration",
                    "status": "digital-cad-checks-passed",
                    "assembled": {
                        "step_path": "assembled.step",
                        "step_sha256": assembled_step_sha,
                        "stl_path": "assembled.stl",
                        "stl_sha256": assembled_stl_sha,
                    },
                    "digital_test_plan": {
                        "schema_version": 2,
                        "supported_geometry": "rigid-box-cylinder-primitives",
                        "dimension_tolerance_mm": 0.2,
                        "invent_lane_contract": {
                            "schema_version": 1,
                            "lane": lane,
                            "fixture": "sealed typed Invent handoff",
                        },
                        "assembly_path": {
                            "kind": "vertical-rigid-body-disassembly-reversed-for-assembly",
                            "minimum_steps": 12,
                            "maximum_overlap_mm3": 0.001,
                        },
                        "material_model": {
                            "name": "generic-PLA-digital-screening-assumption",
                            "density_g_per_mm3": 0.00124,
                            "allowable_compression_mpa": 5.0,
                            "allowable_shear_mpa": 3.0,
                        },
                        "load_model": {
                            "kind": "workshop-conservative-handling-v1",
                            "force_n": 20.0,
                            "torque_n_mm": 250.0,
                            "safety_factor": 2.0,
                            "load_direction": "normal and tangential to each primitive's assembly z cross-section",
                            "failure_modes": [
                                "bulk compression under bounded handling force",
                                "direct shear under bounded handling force",
                                "bulk torsional shear under bounded handling torque",
                            ],
                        },
                        "not_proven": ["physical fit"],
                    },
                }
            ),
            encoding="utf-8",
        )
        (artifact / "playtest" / "print.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "kind": "workshop.digital-print-preflight",
                    "status": "preflight-passed-slicer-held",
                    "print_plate": {
                        "path": "cad/print_plate.stl",
                        "sha256": print_sha,
                    },
                    "slicer": {"status": "held"},
                }
            ),
            encoding="utf-8",
        )
        (artifact / "playtest" / "motion.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "kind": "workshop.motion-evidence-gap",
                    "status": "held",
                    "declared_motion": {"axis": "z", "sweep_degrees": 180},
                }
            ),
            encoding="utf-8",
        )
        declaration_path = artifact / "playtest" / "mechanical.json"
        declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
        lane_contract = declaration["digital_test_plan"]["invent_lane_contract"]
        declaration["digital_test_plan"]["invent_lane_contract_sha256"] = hashlib.sha256(
            json.dumps(
                lane_contract,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        declaration_path.write_text(json.dumps(declaration), encoding="utf-8")
        made = Made.from_root(
            artifact,
            {
                "title": "Exact Fixture",
                "summary": "A fixture for exact digital gates.",
                "lane": lane,
                "components": ["base", "token"],
            },
        )
        wish = Wish.create("exact-fixture", "Make an exact mechanical fixture")
        return PlaytestContext(
            wish,
            self.taste,
            ToyBlueprint.for_lane(lane),
            1,
            made,
            (self.root / ("playtest-" + lane)).absolute(),
            2,
        )

    @staticmethod
    def reseal_context(context):
        made = Made.from_root(context.made.artifact_root, context.made.product)
        return PlaytestContext(
            context.wish,
            context.taste,
            context.blueprint,
            context.round,
            made,
            context.workspace,
            context.playtest_rounds,
        )

    @staticmethod
    def passing_preflight():
        return {
            "passed": True,
            "checks": {
                check_id: {"status": "passed"}
                for check_id in (
                    "manifest",
                    "bed-packing",
                    "mesh-topology",
                    "thickness",
                )
            },
        }

    @staticmethod
    def passing_mechanical_preflight():
        return {
            "passed": True,
            "generator": {"id": "fixture", "version": "2.0.0"},
            "skills": {"cad": "a" * 64, "product-to-cad": "b" * 64},
            "checks": {
                "manifest": {"status": "passed"},
                "source-step-identity": {"status": "passed"},
                "brep": {"status": "passed"},
                "dimensions": {"status": "passed"},
                "interference": {
                    "status": "passed",
                    "measurements": {
                        "poses_tested": 2,
                        "forbidden_intersections": 0,
                    },
                },
            },
        }

    def test_locked_builder_uses_step_first_source_and_every_pinned_gate(self):
        action = make_action()
        runner = FakeCadCommandRunner(action)
        builder = LockedCadSkillBuilder(command_runner=runner)
        build = builder.build(
            action, lane="moving-machines", root=self.root / "cad-attempt"
        )
        self.assertTrue(build.observation["passed"])
        self.assertFalse(build.observation["release_ready"])
        self.assertEqual(build.observation["checks"]["brep"]["status"], "passed")
        self.assertEqual(
            build.observation["checks"]["interference"]["measurements"]["poses_tested"],
            2,
        )
        self.assertTrue((build.root / "product.step.py").is_file())
        self.assertTrue((build.root / "product.step").is_file())
        self.assertTrue((build.root / "product.stl").is_file())
        self.assertTrue((build.root / "part_base.step.py").is_file())
        self.assertTrue((build.root / "part_base.step").is_file())
        self.assertTrue((build.root / "part_base.stl").is_file())
        sealed_evidence = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((build.root / "verification").rglob("*.json"))
        )
        self.assertNotIn(str(build.root), sealed_evidence)
        self.assertNotIn(str(builder.skills_root), sealed_evidence)
        for source_path in build.root.glob("*.py"):
            compile(
                source_path.read_text(encoding="utf-8"),
                str(source_path),
                "exec",
            )
        source = (build.root / "parts.py").read_text(encoding="utf-8")
        self.assertIn("from build123d import", source)
        tools = [Path(call[0][1]).name if call[0][1] != "-c" else "probe" for call in runner.calls]
        for tool in (
            "gen",
            "export",
            "inspect",
            "check_fit",
            "check_mesh",
            "check_thickness",
        ):
            self.assertIn(tool, tools)
        for unused_command, unused_cwd, unused_input, environment in runner.calls:
            self.assertEqual(
                set(environment),
                {"PATH", "LANG", "LC_ALL", "PYTHONHASHSEED", "PYTHONDONTWRITEBYTECODE"},
            )
            self.assertNotIn("FACTORY_PASSWORD", environment)
        self.assertIn("slicer-profile", " ".join(build.observation["release_blockers"]))

    def test_circle_bounds_tolerance_covers_only_locked_inspector_sampling_error(self):
        cylinder_action = make_action()
        cylinder_action["parts"][1]["size_mm"] = {"x": 120, "y": 120, "z": 6}
        cylinder_runner = FakeCadCommandRunner(cylinder_action)
        cylinder_runner.sizes["part_index-wheel.step"] = [
            119.925415,
            119.962702,
            6.0,
        ]
        cylinder_build = LockedCadSkillBuilder(
            command_runner=cylinder_runner
        ).build(
            cylinder_action,
            lane="moving-machines",
            root=self.root / "sampled-cylinder",
        )
        self.assertEqual(
            cylinder_build.observation["checks"]["dimensions"]["status"],
            "passed",
        )
        cylinder_row = cylinder_build.observation["checks"]["dimensions"][
            "measurements"
        ]["parts"][1]
        self.assertEqual(cylinder_row["effective_tolerance_mm"], [0.078, 0.078, 0.05])

        box_action = make_action()
        box_action["parts"][0]["size_mm"]["x"] = 120
        box_runner = FakeCadCommandRunner(box_action)
        box_runner.sizes["part_base.step"] = [119.925415, 36.0, 5.0]
        box_build = LockedCadSkillBuilder(command_runner=box_runner).build(
            box_action,
            lane="moving-machines",
            root=self.root / "same-delta-box",
        )
        self.assertEqual(
            box_build.observation["checks"]["dimensions"]["status"],
            "failed",
        )
        box_row = box_build.observation["checks"]["dimensions"][
            "measurements"
        ]["parts"][0]
        self.assertEqual(box_row["effective_tolerance_mm"], [0.05, 0.05, 0.05])

    def test_playtest_rejects_changed_locked_source_before_any_cad_process(self):
        context = self.playtest_context()
        source = context.made.artifact_root / "cad" / "parts.py"
        source.write_text(
            source.read_text(encoding="utf-8")
            + "\nraise RuntimeError('forged custom Make source ran')\n",
            encoding="utf-8",
        )
        forged = self.reseal_context(context)
        with mock.patch("workshop.make.agent.subprocess.run") as launched:
            with self.assertRaisesRegex(ValueError, "source differs"):
                _recheck_locked_cad(forged, groups=("print",))
        launched.assert_not_called()

    def test_playtest_converts_forged_make_action_failure_before_execution(self):
        context = self.playtest_context()
        design_path = context.made.artifact_root / "cad" / "design.json"
        design = json.loads(design_path.read_text(encoding="utf-8"))
        design["action"]["parts"] = design["action"]["parts"][:1]
        design_path.write_text(json.dumps(design), encoding="utf-8")
        forged = self.reseal_context(context)
        with mock.patch("workshop.make.agent.subprocess.run") as launched:
            with self.assertRaisesRegex(ValueError, "invalid locked"):
                _recheck_locked_cad(forged, groups=("print",))
        launched.assert_not_called()

    def test_playtest_rejects_every_extra_importable_cad_file_before_execution(self):
        context = self.playtest_context()
        cad_root = context.made.artifact_root / "cad"
        for index, suffix in enumerate((".py", ".pyc", ".pyo", ".so", ".dylib", ".pyd", ".pth")):
            with self.subTest(suffix=suffix):
                extra = cad_root / ("forged-%d%s" % (index, suffix))
                extra.write_bytes(b"forged custom Make executable bytes")
                forged = self.reseal_context(context)
                with mock.patch("workshop.make.agent.subprocess.run") as launched:
                    with self.assertRaisesRegex(ValueError, "executable inventory"):
                        _recheck_locked_cad(forged, groups=("mechanical",))
                launched.assert_not_called()
                extra.unlink()
                context.made.assert_current()

    def test_locked_builder_missing_runtime_is_a_make_wait(self):
        builder = LockedCadSkillBuilder(
            python_executable="/missing/workshop-cad-python"
        )
        with self.assertRaises(WaitingFor) as caught:
            builder.ensure_available()
        self.assertEqual(caught.exception.needs[0].job, "make")
        self.assertEqual(caught.exception.needs[0].capability, "cad-skill-runtime")

    def test_locked_builder_allows_a_realistic_cold_cad_import(self):
        observed = {}

        def runner(command, **kwargs):
            observed["command"] = list(command)
            observed["timeout"] = kwargs["timeout"]
            return subprocess.CompletedProcess(
                command, 0, "workshop-cad-runtime-ok\n", ""
            )

        builder = LockedCadSkillBuilder(command_runner=runner)
        builder.ensure_available()
        self.assertEqual(observed["command"][1], "-c")
        self.assertEqual(
            observed["timeout"], CAD_RUNTIME_PROBE_TIMEOUT_SECONDS
        )
        self.assertGreaterEqual(CAD_RUNTIME_PROBE_TIMEOUT_SECONDS, 180)

    @unittest.skipUnless(
        importlib.util.find_spec("build123d") is not None,
        "real locked CAD runtime is not installed",
    )
    def test_locked_builder_runs_the_real_step_first_toolchain(self):
        action = make_action()
        action["parts"][0]["top_grooves_mm"] = [
            {"center_x": -8, "width": 2, "depth": 1},
            {"center_x": 8, "width": 2, "depth": 1},
        ]
        builder = LockedCadSkillBuilder()
        build = builder.build(
            action, lane="moving-machines", root=self.root / "real-cad-attempt"
        )
        self.assertTrue(build.observation["passed"], build.observation["issues"])
        from build123d import import_step

        grooved_base = import_step(build.root / "part_base.step")
        self.assertAlmostEqual(
            grooved_base.volume,
            48.0 * 36.0 * 5.0 - 2.0 * (2.0 * 36.0 * 1.0),
            places=3,
        )
        self.assertEqual(
            {
                check_id: check["status"]
                for check_id, check in build.observation["checks"].items()
            },
            {
                "manifest": "passed",
                "source-step-identity": "passed",
                "brep": "passed",
                "dimensions": "passed",
                "interference": "passed",
                "bed-packing": "passed",
                "mesh-topology": "passed",
                "thickness": "passed",
            },
        )
        motion = builder.check_motion(
            build.root,
            WorkshopMechanicalVerifier._motion_manifest(action["parts"]),
            command_id="real-mechanical-assembly-path",
        )
        self.assertEqual(motion["returncode"], 0, motion)
        self.assertTrue(
            all(row["status"] == "pass" for row in motion["result"]["results"]),
            motion,
        )

    def test_prusaslicer_adapter_hashes_profiles_and_every_gcode(self):
        context = self.playtest_context()
        profiles = {}
        for role in ("printer", "process", "filament"):
            path = self.root / (role + ".ini")
            path.write_text("[%s]\nfixture=1\n" % role, encoding="utf-8")
            profiles[role] = path
        runner = FakePrusaRunner()
        adapter = PrusaSlicerPrintCheck(
            binary="prusa-slicer",
            printer_profile=profiles["printer"],
            process_profile=profiles["process"],
            filament_profile=profiles["filament"],
            command_runner=runner,
        )
        raw = adapter.run(context, preflight=self.passing_preflight())
        checked = _validate_digital_check(context, "print-test", raw)
        self.assertTrue(checked["passed"])
        self.assertEqual(checked["metrics"]["profiles_checked"], 3)
        self.assertEqual(checked["metrics"]["parts_sliced"], 2)
        self.assertEqual(checked["metrics"]["slicer_errors"], 0)
        receipt = checked["metrics"]["slicer_receipt"]
        self.assertEqual(len(receipt["parts"]), 2)
        self.assertTrue(all(row["gcode_sha256"] for row in receipt["parts"]))
        self.assertTrue(
            all(profile["sha256"] for profile in receipt["profiles"].values())
        )
        self.assertEqual(len(runner.calls), 3)
        for unused_command, environment in runner.calls:
            self.assertEqual(
                set(environment),
                {"PATH", "LANG", "LC_ALL", "PYTHONHASHSEED", "PYTHONDONTWRITEBYTECODE"},
            )

    def test_prusaslicer_version_mismatch_is_a_typed_wait(self):
        context = self.playtest_context()
        profiles = []
        for index in range(3):
            path = self.root / ("profile-%d.ini" % index)
            path.write_text("fixture=1\n", encoding="utf-8")
            profiles.append(path)
        adapter = PrusaSlicerPrintCheck(
            binary="prusa-slicer",
            printer_profile=profiles[0],
            process_profile=profiles[1],
            filament_profile=profiles[2],
            command_runner=FakePrusaRunner("2.9.5"),
        )
        with self.assertRaises(WaitingFor) as caught:
            adapter.run(context, preflight=self.passing_preflight())
        self.assertEqual(caught.exception.needs[0].capability, "print-test")

    def test_prusaslicer_auto_discovery_uses_pinned_workshop_profiles(self):
        context = self.playtest_context()
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            PrusaSlicerPrintCheck,
            "_discover_binary",
            return_value="/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer",
        ):
            adapter = PrusaSlicerPrintCheck.from_environment()
        self.assertIsNotNone(adapter)
        assert adapter is not None
        adapter.command_runner = FakePrusaRunner()
        raw = adapter.run(context, preflight=self.passing_preflight())
        checked = _validate_digital_check(context, "print-test", raw)
        self.assertTrue(checked["passed"])
        self.assertEqual(
            {
                profile["origin"]
                for profile in checked["metrics"]["slicer_receipt"]["profiles"].values()
            },
            {"workshop-bundled-v1"},
        )

    def test_prusaslicer_prefers_fixed_application_before_ambient_path(self):
        fixed = self.root / "PrusaSlicer"
        fixed.write_text("fixture", encoding="utf-8")
        fixed.chmod(0o700)
        with mock.patch.object(
            PrusaSlicerPrintCheck,
            "_fixed_binary_candidates",
            return_value=(fixed,),
        ), mock.patch(
            "workshop.playtest.agent.shutil.which",
            return_value="/ambient/impersonating-prusa-slicer",
        ) as ambient:
            self.assertEqual(PrusaSlicerPrintCheck._discover_binary(), str(fixed))
        ambient.assert_not_called()

    @unittest.skipUnless(
        PrusaSlicerPrintCheck._discover_binary() is not None,
        "real pinned PrusaSlicer runtime is not installed",
    )
    def test_pinned_profiles_produce_real_gcode_for_a_sealed_part(self):
        fixture = (
            Path(__file__).resolve().parents[2]
            / "inventors"
            / "ivy"
            / "toys"
            / "montauk-tide-orrery"
            / "artifact"
            / "cad"
            / "parts"
            / "earth-hub.stl"
        )
        if not fixture.is_file():
            self.skipTest("the checked-in exact STL fixture is unavailable")
        artifact = self.root / "real-slicer-artifact"
        (artifact / "cad").mkdir(parents=True)
        shutil.copyfile(fixture, artifact / "cad" / "part_earth_hub.stl")
        made = Made.from_root(
            artifact,
            {
                "title": "Real slicer fixture",
                "summary": "One sealed checked-in STEP-derived part.",
                "lane": "little-worlds",
                "components": ["earth hub"],
            },
        )
        context = PlaytestContext(
            Wish.create("real-slicer-fixture", "Slice the exact sealed fixture"),
            self.taste,
            ToyBlueprint.for_lane("little-worlds"),
            1,
            made,
            (self.root / "real-slicer-playtest").absolute(),
            2,
        )
        with mock.patch.dict(os.environ, {}, clear=True):
            adapter = PrusaSlicerPrintCheck.from_environment()
        self.assertIsNotNone(adapter)
        assert adapter is not None
        checked = _validate_digital_check(
            context,
            "print-test",
            adapter.run(context, preflight=self.passing_preflight()),
        )
        self.assertTrue(checked["passed"], checked)
        receipt = checked["metrics"]["slicer_receipt"]
        self.assertGreater(receipt["parts"][0]["gcode_bytes"], 0)

    def test_default_print_waits_without_all_slicer_configuration(self):
        context = self.playtest_context()
        with mock.patch(
            "workshop.playtest.agent._recheck_locked_cad",
            return_value=self.passing_preflight(),
        ), mock.patch.object(
            PrusaSlicerPrintCheck, "_discover_binary", return_value=None
        ), mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(WaitingFor) as caught:
                default_print_check(context)
        self.assertEqual(caught.exception.needs[0].capability, "print-test")
        self.assertIn("no exact", caught.exception.needs[0].reason.casefold())

    def test_default_mechanical_dispatches_to_shared_verifier_after_preflight(self):
        context = self.playtest_context()
        expected = {"capability": "mechanical-test", "passed": True}
        with mock.patch(
            "workshop.playtest.agent._recheck_locked_cad",
            return_value=self.passing_mechanical_preflight(),
        ), mock.patch.object(
            WorkshopMechanicalVerifier, "run", return_value=expected
        ) as run:
            self.assertEqual(default_mechanical_check(context), expected)
        run.assert_called_once()

    def test_shared_mechanical_verifier_seals_exact_digital_assumptions(self):
        context = self.playtest_context()
        declaration = json.loads(
            (context.made.artifact_root / "playtest" / "mechanical.json").read_text(
                encoding="utf-8"
            )
        )
        cad_builder = FakeMechanicalCadBuilder()
        raw = WorkshopMechanicalVerifier(cad_builder=cad_builder).run(
            context,
            preflight=self.passing_mechanical_preflight(),
            declaration=declaration,
        )
        checked = _validate_digital_check(context, "mechanical-test", raw)
        self.assertTrue(checked["passed"])
        self.assertEqual(checked["metrics"]["assembly_paths_tested"], 2)
        self.assertEqual(checked["metrics"]["fit_cases"], 3)
        self.assertEqual(checked["metrics"]["load_cases"], 9)
        self.assertIn(
            "never physical fit",
            checked["metrics"]["mechanical_receipt"]["claim_scope"],
        )
        self.assertEqual(len(cad_builder.calls[0][1]["conditions"]), 2)

    def test_custom_mechanical_label_cannot_bypass_receipt_semantics(self):
        context = self.playtest_context()
        inventory = {
            entry.path: entry.sha256 for entry in context.made.artifact_manifest.entries
        }
        raw = {
            "artifact_sha256": context.made.artifact_sha256,
            "capability": "mechanical-test",
            "passed": True,
            "checker": "custom-inventor-checker",
            "checker_version": "1.0.0",
            "config_sha256": "c" * 64,
            "method_class": "deterministic-digital-check",
            "source_refs": ["assembled.step", "assembled.stl"],
            "observations": ["A custom worker called the static files mechanically sound."],
            "metrics": {
                "parts_checked": 2,
                "failures": 0,
                "assembled_step_sha256": inventory["assembled.step"],
            },
            "findings": [],
        }
        with self.assertRaisesRegex(ValueError, "tolerance/assembly/load"):
            _validate_digital_check(context, "mechanical-test", raw)

    def test_default_motion_never_promotes_static_aabb_or_held_declaration(self):
        context = self.playtest_context("moving-machines")
        with self.assertRaises(WaitingFor) as caught:
            default_motion_check(context)
        self.assertEqual(caught.exception.needs[0].capability, "motion-test")
        self.assertIn("no real kinematic", caught.exception.needs[0].reason)


if __name__ == "__main__":
    unittest.main()
