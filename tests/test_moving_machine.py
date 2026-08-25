import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.agent_make import LockedCadSkillBuilder
from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.errors import ContractError
from inventor_workshop.jobs import Made, Playtested, WaitingFor
from inventor_workshop.models import PlaytestResult
from inventor_workshop.moving_machine import (
    MOVING_MACHINE_BINDING_KIND,
    WorkshopMovingMachineVerifier,
    _part_by_id,
)
from inventor_workshop.playtest import Playtest
from inventor_workshop.playtest_release import playtest_release_needs
from inventor_workshop.toys import ToyBlueprint


def json_sha256(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


class PassingMotionBuilder:
    def __init__(self):
        self.manifests = []

    def check_motion(self, root, manifest, *, command_id):
        self.manifests.append((Path(root), manifest, command_id))
        results = []
        for condition in manifest["conditions"]:
            results.append(
                {
                    "id": condition["id"],
                    "check": condition["check"],
                    "status": "pass",
                    "clear": True,
                    "steps": condition["inputs"]["steps"],
                }
            )
        return {
            "returncode": 0,
            "result": {
                "ok": True,
                "assembly": "product.step.py",
                "results": results,
            },
        }


class InconclusiveMotionBuilder(PassingMotionBuilder):
    def check_motion(self, root, manifest, *, command_id):
        value = super().check_motion(root, manifest, command_id=command_id)
        value["result"]["results"][1]["status"] = "inconclusive"
        return value


class WorkshopMovingMachineVerifierTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.product_root = self.root / "product"
        self.evidence_root = self.root / "evidence"
        self.product_root.mkdir()
        self.evidence_root.mkdir()
        self.action = self.action_fixture()
        self.contract = self.contract_fixture()
        self.write_product()
        self.made = Made.from_root(
            self.product_root,
            {
                "title": "Orbit Bloom",
                "summary": "A hand-turned rigid kinetic desk sculpture.",
                "lane": "moving-machines",
            },
        )
        self.inventory = {
            entry.path: entry.sha256 for entry in self.made.artifact_manifest.entries
        }

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def part(part_id, shape, size, assembly_center):
        return {
            "part_id": part_id,
            "name": part_id.replace("-", " ").title(),
            "purpose": "An exact primitive in the shared moving assembly.",
            "shape": shape,
            "size_mm": dict(zip(("x", "y", "z"), size)),
            "print_center_mm": {"x": 30.0, "y": 30.0},
            "print_rotation_deg": 0.0,
            "assembly_center_mm": dict(zip(("x", "y", "z"), assembly_center)),
            "assembly_rotation_deg": 0.0,
            "material": "PLA",
        }

    @classmethod
    def action_fixture(cls):
        return {
            "title": "Orbit Bloom",
            "summary": "A broad arm turns above a grounded thrust support.",
            "interaction": "Turn the arm through a half revolution.",
            "mechanical_principle": "One rigid body rotates about its centered Z axis.",
            "assembly": ["Place the rotor on the base beneath the distant guard."],
            "instructions": "Turn gently by hand.",
            "parts": [
                cls.part("base", "cylinder", (20.0, 20.0, 5.0), (0.0, 0.0, 0.0)),
                cls.part("guard", "box", (4.0, 4.0, 10.0), (30.0, 0.0, 0.0)),
                cls.part("rotor", "box", (20.0, 4.0, 3.0), (0.0, 0.0, 5.0)),
            ],
            "classic_spec": {
                "enabled": False,
                "known_game": "none",
                "rules_reference": "not a classic game",
                "rules_unchanged": True,
            },
            "game_spec": {
                "enabled": False,
                "title": "not a game",
                "starting_tokens": 7,
                "max_take": 2,
                "last_take_wins": True,
                "theme": "not applicable",
                "token_part_ids": [],
            },
            "motion_spec": {
                "enabled": True,
                "moving_part_id": "rotor",
                "axis": "z",
                "sweep_degrees": 180,
                "minimum_aabb_clearance_mm": 5.0,
            },
            "design_limitations": [
                "Digital rigid-body evidence does not prove physical retention or safety."
            ],
        }

    @staticmethod
    def contract_fixture():
        return {
            "schema_version": 1,
            "lane": "moving-machines",
            "kinematic_model": {
                "input_motion": "A person turns the rotor by hand.",
                "transmission": ["The rigid rotor turns directly about the Z axis."],
                "output_motion": "The arm sweeps through a half revolution.",
                "degrees_of_freedom": 1,
            },
            "tolerances_mm": [
                {
                    "interface": "Rotor swept envelope beside the guard",
                    "nominal_clearance_mm": 0.3,
                    "tolerance_mm": 0.1,
                }
            ],
            "load_assumptions": [
                {
                    "case": "A user stalls the rotor by hand.",
                    "force_n": 8.0,
                    "safety_factor": 2.0,
                    "basis": "A bounded concept-stage hand-force assumption.",
                }
            ],
            "failure_modes": [
                {
                    "mode": "Rotor section shear or clearance stall",
                    "cause": "The hand load exceeds the section or the rotor reaches the guard.",
                    "effect": "The motion stops or the rotor section fails.",
                    "mitigation": "Size the section and preserve the exact swept clearance.",
                }
            ],
        }

    def binding_fixture(self, design_sha256):
        return {
            "schema_version": 1,
            "kind": MOVING_MACHINE_BINDING_KIND,
            "cad_design_sha256": design_sha256,
            "invent_lane_contract_sha256": json_sha256(self.contract),
            "joint": {
                "joint_id": "primary-rotor",
                "kind": "rigid-revolute-z",
                "moving_part_id": "rotor",
                "support_part_ids": ["base"],
                "obstacle_part_ids": ["guard"],
                "axis_point_mm": [0.0, 0.0, 5.0],
                "axis_direction": [0.0, 0.0, 1.0],
                "start_deg": 0.0,
                "end_deg": 180.0,
                "steps": 72,
            },
            "tolerance_bindings": [
                {
                    "contract_index": 0,
                    "moving_part_id": "rotor",
                    "stationary_part_ids": ["guard"],
                    "verification": "continuous-swept-envelope",
                }
            ],
            "load_bindings": [
                {
                    "contract_index": 0,
                    "loaded_part_id": "rotor",
                    "support_part_ids": ["base"],
                    "section_axis": "z",
                    "verification_modes": ["bulk-compression", "direct-shear"],
                }
            ],
            "failure_bindings": [
                {
                    "contract_index": 0,
                    "part_ids": ["rotor", "base", "guard"],
                    "load_case_indices": [0],
                    "verification_modes": [
                        "direct-shear",
                        "continuous-clearance",
                        "reverse-sweep",
                        "stall-envelope",
                    ],
                }
            ],
            "wear_model": {
                "kind": "workshop-pinned-digital-clearance-budget",
                "model_version": "1.0.0",
                "cycles": 1_000,
                "cumulative_allowance_mm": 0.2,
                "basis": (
                    "The 1,000-cycle value is a pinned digital model horizon used with a "
                    "fixed 0.2 mm cumulative clearance erosion budget. No physical cycles "
                    "are simulated or claimed."
                ),
            },
            "misuse_cases": ["reverse-sweep", "stall-load-envelope"],
        }

    @staticmethod
    def write_json(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def write_product(self):
        design = {
            "schema_version": 1,
            "kind": "workshop-step-first-parametric-design",
            "action": self.action,
        }
        self.write_json(self.product_root / "cad" / "design.json", design)
        design_sha256 = hashlib.sha256(
            (self.product_root / "cad" / "design.json").read_bytes()
        ).hexdigest()
        for relative, source in LockedCadSkillBuilder._project_sources(self.action).items():
            path = self.product_root / "cad" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
        (self.product_root / "cad" / "product.step").write_text(
            "ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8"
        )
        (self.product_root / "assembled.step").write_text(
            "ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8"
        )
        self.write_json(
            self.product_root / "playtest" / "mechanical.json",
            {
                "schema_version": 2,
                "kind": "workshop.locked-cad-mechanical-declaration",
                "digital_test_plan": {
                    "invent_lane_contract": self.contract,
                    "invent_lane_contract_sha256": json_sha256(self.contract),
                },
            },
        )
        self.write_json(
            self.product_root / "playtest" / "moving-machine-binding.json",
            self.binding_fixture(design_sha256),
        )
        self.write_json(
            self.product_root / "validation" / "cad-build.json",
            {
                "schema_version": 2,
                "passed": True,
                "checks": {
                    "brep": {"status": "passed", "measurements": {"valid_solids": 3}},
                    "interference": {
                        "status": "passed",
                        "measurements": {
                            "poses_tested": 2,
                            "forbidden_intersections": 0,
                        },
                    },
                },
            },
        )

    def verifier(self, builder=None):
        return WorkshopMovingMachineVerifier(
            cad_builder=builder if builder is not None else PassingMotionBuilder()
        )

    def run_verifier(self, builder=None):
        return self.verifier(builder).run(
            artifact_sha256=self.made.artifact_sha256,
            product_root=self.product_root,
            product_inventory=self.inventory,
        )

    def result_for(self, capability, proof):
        evidence = {
            "evidence_class": "ai-simulation",
            "artifact_sha256": self.made.artifact_sha256,
            "agent_roles": ["mechanism-player", "adversarial-breaker"],
            "release_proof": proof.to_dict(),
        }
        relative = "results/%s.json" % capability
        payload = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
        path = self.evidence_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
        return PlaytestResult.create(
            capability,
            True,
            self.made.artifact_sha256,
            evidence,
            "workshop-primitive-moving-machine",
            "1.0.0",
            "f" * 64,
            relative,
            hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        )

    def test_pass_emits_receipts_and_proofs_accepted_by_core_release_policy(self):
        prepared = self.run_verifier()

        self.assertTrue(prepared.passed)
        self.assertFalse(prepared.sealed)
        self.assertIsNone(prepared.mechanical_proof)
        self.assertFalse(any(self.evidence_root.iterdir()))
        verification = prepared.seal(self.evidence_root)
        self.assertTrue(verification.sealed)
        self.assertIsNotNone(verification.mechanical_proof)
        self.assertIsNotNone(verification.motion_proof)
        self.assertEqual(
            set(verification.receipt_sha256),
            {
                WorkshopMovingMachineVerifier.MECHANICAL_RECEIPT_REF,
                WorkshopMovingMachineVerifier.MOTION_RECEIPT_REF,
            },
        )
        results = (
            self.result_for("mechanical-test", verification.mechanical_proof),
            self.result_for("motion-test", verification.motion_proof),
        )
        playtested = Playtested(
            Playtest(
                self.made.artifact_manifest,
                results,
                evidence_manifest=build_artifact_manifest(
                    self.evidence_root, created_at="content-addressed"
                ),
            )
        )

        needs = playtest_release_needs(
            ToyBlueprint.for_lane("moving-machines"),
            self.made,
            playtested,
            self.evidence_root,
        )

        self.assertEqual(
            {need.capability for need in needs}, {"agent-playtest", "print-test"}
        )
        mechanical = verification.mechanical_proof.measurements
        motion = verification.motion_proof.measurements
        self.assertEqual(mechanical["unresolved_critical_failures"], 0)
        self.assertTrue(motion["continuous_sweep"])
        self.assertEqual(motion["wear_cycles"], 1_000)
        self.assertEqual(motion["orientations_tested"], 1)
        motion_receipt = json.loads(
            (
                self.evidence_root
                / WorkshopMovingMachineVerifier.MOTION_RECEIPT_REF
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            len(motion_receipt["payload"]["orientation_cases"]),
            motion["orientations_tested"],
        )
        self.assertTrue(motion_receipt["payload"]["wear_cases"])
        self.assertIn(
            "does not count physically simulated",
            motion_receipt["payload"]["wear_measurement_scope"],
        )
        self.assertTrue(
            all(
                row["model_kind"]
                == "workshop-pinned-digital-clearance-budget"
                for row in motion_receipt["payload"]["wear_cases"]
            )
        )

    def test_manifest_uses_exact_bound_parts_and_both_motion_directions(self):
        builder = PassingMotionBuilder()

        verification = self.run_verifier(builder)

        self.assertTrue(verification.passed)
        self.assertEqual(len(builder.manifests), 1)
        unused_root, manifest, command_id = builder.manifests[0]
        del unused_root
        self.assertEqual(command_id, "moving-machine-motion")
        self.assertEqual(
            [condition["id"] for condition in manifest["conditions"]],
            [
                "moving-machine-assembly-path",
                "moving-machine-forward-sweep",
                "moving-machine-reverse-sweep",
            ],
        )
        self.assertEqual(
            manifest["conditions"][1]["inputs"]["moving_part"], "rotor"
        )
        self.assertEqual(
            set(manifest["conditions"][1]["inputs"]["obstacle_parts"]),
            {"base", "guard"},
        )

    def test_multi_degree_or_unmapped_failure_waits_for_shared_provider(self):
        declaration_path = self.product_root / "playtest" / "mechanical.json"
        declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
        declaration["digital_test_plan"]["invent_lane_contract"]["kinematic_model"][
            "degrees_of_freedom"
        ] = 2
        declaration["digital_test_plan"]["invent_lane_contract_sha256"] = json_sha256(
            declaration["digital_test_plan"]["invent_lane_contract"]
        )
        self.write_json(declaration_path, declaration)
        remade = Made.from_root(self.product_root, self.made.product)
        inventory = {entry.path: entry.sha256 for entry in remade.artifact_manifest.entries}

        with self.assertRaises(WaitingFor) as raised:
            self.verifier().run(
                artifact_sha256=remade.artifact_sha256,
                product_root=self.product_root,
                product_inventory=inventory,
            )

        self.assertEqual(raised.exception.needs[0].capability, "motion-test")
        self.assertIn("Workshop", raised.exception.needs[0].instructions)

    def test_one_part_machine_returns_typed_need_not_argument_error(self):
        action = dict(self.action)
        action["parts"] = [self.action["parts"][0]]

        with self.assertRaises(WaitingFor) as raised:
            _part_by_id(action)

        self.assertEqual(raised.exception.needs[0].capability, "mechanical-test")
        self.assertIn("at least two exact CAD parts", raised.exception.needs[0].reason)

    def test_inconclusive_kernel_condition_is_typed_wait_not_pass(self):
        with self.assertRaises(WaitingFor) as raised:
            self.run_verifier(InconclusiveMotionBuilder())

        self.assertEqual(raised.exception.needs[0].capability, "motion-test")
        self.assertFalse(any(self.evidence_root.rglob("*.json")))

    def test_unsupported_failure_solver_waits_for_workshop_not_inventor(self):
        binding_path = self.product_root / "playtest" / "moving-machine-binding.json"
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding["failure_bindings"][0]["verification_modes"] = [
            "physical-safety-certification"
        ]
        self.write_json(binding_path, binding)
        remade = Made.from_root(self.product_root, self.made.product)
        inventory = {entry.path: entry.sha256 for entry in remade.artifact_manifest.entries}

        with self.assertRaises(WaitingFor) as raised:
            self.verifier().run(
                artifact_sha256=remade.artifact_sha256,
                product_root=self.product_root,
                product_inventory=inventory,
            )

        self.assertEqual(raised.exception.needs[0].capability, "mechanical-test")
        self.assertIn("Workshop solver", raised.exception.needs[0].instructions)
        self.assertFalse(any(self.evidence_root.rglob("*.json")))

    def test_arbitrary_wear_cycles_cannot_be_relabelled_as_pinned_evidence(self):
        binding_path = self.product_root / "playtest" / "moving-machine-binding.json"
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding["wear_model"]["cycles"] = 50_000
        self.write_json(binding_path, binding)
        remade = Made.from_root(self.product_root, self.made.product)
        inventory = {entry.path: entry.sha256 for entry in remade.artifact_manifest.entries}

        with self.assertRaises(WaitingFor) as raised:
            self.verifier().run(
                artifact_sha256=remade.artifact_sha256,
                product_root=self.product_root,
                product_inventory=inventory,
            )

        self.assertEqual(raised.exception.needs[0].capability, "motion-test")
        self.assertIn("arbitrary cycle count", raised.exception.needs[0].instructions)
        self.assertFalse(any(self.evidence_root.iterdir()))

    def test_pinch_hazard_cannot_be_relabelled_as_clearance_or_shear(self):
        declaration_path = self.product_root / "playtest" / "mechanical.json"
        declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
        contract = declaration["digital_test_plan"]["invent_lane_contract"]
        contract["failure_modes"][0] = {
            "mode": "Finger pinch injury",
            "cause": "A finger enters the rotor clearance while it turns.",
            "effect": "The moving arm causes a crush injury.",
            "mitigation": "Guard the pinch point and perform a physical safety evaluation.",
        }
        contract_sha256 = json_sha256(contract)
        declaration["digital_test_plan"]["invent_lane_contract_sha256"] = contract_sha256
        self.write_json(declaration_path, declaration)
        binding_path = self.product_root / "playtest" / "moving-machine-binding.json"
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding["invent_lane_contract_sha256"] = contract_sha256
        self.write_json(binding_path, binding)
        remade = Made.from_root(self.product_root, self.made.product)
        inventory = {entry.path: entry.sha256 for entry in remade.artifact_manifest.entries}

        with self.assertRaises(WaitingFor) as raised:
            self.verifier().run(
                artifact_sha256=remade.artifact_sha256,
                product_root=self.product_root,
                product_inventory=inventory,
            )

        self.assertEqual(
            raised.exception.needs[0].capability, "mechanical-safety-test"
        )
        self.assertIn("do not relabel", raised.exception.needs[0].instructions)
        self.assertFalse(any(self.evidence_root.iterdir()))

    def test_fatigue_failure_cannot_use_generic_section_load_calculation(self):
        declaration_path = self.product_root / "playtest" / "mechanical.json"
        declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
        contract = declaration["digital_test_plan"]["invent_lane_contract"]
        contract["failure_modes"][0] = {
            "mode": "Rotor fatigue fracture",
            "cause": "Repeated cycles initiate a fatigue crack.",
            "effect": "The rotor eventually separates.",
            "mitigation": "Use a source-bound fatigue model and physical cycle testing.",
        }
        contract_sha256 = json_sha256(contract)
        declaration["digital_test_plan"]["invent_lane_contract_sha256"] = contract_sha256
        self.write_json(declaration_path, declaration)
        binding_path = self.product_root / "playtest" / "moving-machine-binding.json"
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding["invent_lane_contract_sha256"] = contract_sha256
        self.write_json(binding_path, binding)
        remade = Made.from_root(self.product_root, self.made.product)
        inventory = {entry.path: entry.sha256 for entry in remade.artifact_manifest.entries}

        with self.assertRaises(WaitingFor) as raised:
            self.verifier().run(
                artifact_sha256=remade.artifact_sha256,
                product_root=self.product_root,
                product_inventory=inventory,
            )

        self.assertEqual(raised.exception.needs[0].capability, "mechanical-test")
        self.assertIn("exact failure physics", raised.exception.needs[0].instructions)
        self.assertFalse(any(self.evidence_root.iterdir()))

    def test_custom_executable_cannot_masquerade_as_locked_shared_cad(self):
        (self.product_root / "cad" / "inventor_worker.py").write_text(
            "raise RuntimeError('must never execute')\n", encoding="utf-8"
        )
        remade = Made.from_root(self.product_root, self.made.product)
        inventory = {entry.path: entry.sha256 for entry in remade.artifact_manifest.entries}

        with self.assertRaisesRegex(ContractError, "executable CAD differs"):
            self.verifier().run(
                artifact_sha256=remade.artifact_sha256,
                product_root=self.product_root,
                product_inventory=inventory,
            )

        self.assertFalse(any(self.evidence_root.rglob("*.json")))

    def test_failed_exact_load_returns_feedback_checks_without_release_proofs(self):
        declaration_path = self.product_root / "playtest" / "mechanical.json"
        declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
        contract = declaration["digital_test_plan"]["invent_lane_contract"]
        contract["load_assumptions"][0]["force_n"] = 10_000.0
        contract["load_assumptions"][0]["safety_factor"] = 20.0
        declaration["digital_test_plan"]["invent_lane_contract_sha256"] = json_sha256(
            contract
        )
        self.write_json(declaration_path, declaration)
        binding_path = self.product_root / "playtest" / "moving-machine-binding.json"
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding["invent_lane_contract_sha256"] = json_sha256(contract)
        self.write_json(binding_path, binding)
        remade = Made.from_root(self.product_root, self.made.product)
        inventory = {entry.path: entry.sha256 for entry in remade.artifact_manifest.entries}

        verification = self.verifier().run(
            artifact_sha256=remade.artifact_sha256,
            product_root=self.product_root,
            product_inventory=inventory,
        )

        self.assertFalse(verification.passed)
        self.assertIsNone(verification.mechanical_proof)
        self.assertIsNone(verification.motion_proof)
        self.assertGreater(verification.mechanical_check["metrics"]["load_failures"], 0)
        self.assertTrue(verification.mechanical_check["findings"])
        self.assertFalse(any(self.evidence_root.rglob("*.json")))


if __name__ == "__main__":
    unittest.main()
