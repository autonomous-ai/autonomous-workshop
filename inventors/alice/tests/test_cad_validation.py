from __future__ import annotations

import hashlib
import math
import struct
import unittest

from alice.cad_validation import (
    CALIBRATION_PROFILE_VERSION,
    UPSTREAM_MIT_NOTICE,
    UPSTREAM_SOURCE_COMMIT,
    AssembledFitCalibration,
    KernelBodyObservation,
    MotionCondition,
    MotionEvaluatorOutcome,
    PrintInPlaceFitCalibration,
    PrinterCalibrationProfile,
    PrinterTarget,
    StlInspectionLimits,
    StlPathInspectionError,
    derive_assembled_fit,
    derive_print_in_place_fit,
    evaluate_motion_condition,
    inspect_stl_path,
    inspect_stl_topology,
    self_check_calibration_profile,
    validate_motion_outcome,
    validate_profile_binding,
)


Point = tuple[float, float, float]
Triangle = tuple[Point, Point, Point]


def tetrahedron(*, offset: Point = (0.0, 0.0, 0.0), scale: float = 1.0) -> list[Triangle]:
    ox, oy, oz = offset

    def point(x: float, y: float, z: float) -> Point:
        return (ox + x * scale, oy + y * scale, oz + z * scale)

    a = point(0, 0, 0)
    b = point(1, 0, 0)
    c = point(0, 1, 0)
    d = point(0, 0, 1)
    # Each face is wound outwards, so the signed volume is positive.
    return [(a, c, b), (a, b, d), (a, d, c), (b, c, d)]


def binary_stl(triangles: list[Triangle], *, header: bytes = b"alice-test") -> bytes:
    prefix = header[:80].ljust(80, b"\0") + struct.pack("<I", len(triangles))
    records: list[bytes] = []
    for triangle in triangles:
        flat = [coordinate for vertex in triangle for coordinate in vertex]
        records.append(struct.pack("<12fH", 0.0, 0.0, 0.0, *flat, 0))
    return prefix + b"".join(records)


def ascii_stl(triangles: list[Triangle]) -> bytes:
    lines = ["solid alice"]
    for triangle in triangles:
        lines.extend(("  facet normal 0 0 0", "    outer loop"))
        lines.extend(f"      vertex {x:.17g} {y:.17g} {z:.17g}" for x, y, z in triangle)
        lines.extend(("    endloop", "  endfacet"))
    lines.append("endsolid alice")
    return ("\n".join(lines) + "\n").encode("ascii")


def profile() -> PrinterCalibrationProfile:
    return PrinterCalibrationProfile(
        profile_id="mk4-pla-calibration",
        revision=3,
        printer_id="printer-mk4-07",
        nozzle_diameter_mm=0.4,
        layer_height_mm=0.2,
        material="PLA:vendor-a:black",
        calibration_evidence_sha256="a" * 64,
        assembled_fits=(
            AssembledFitCalibration("slip", 0.2),
            AssembledFitCalibration("press", -0.05),
        ),
        print_in_place_fits=(
            PrintInPlaceFitCalibration("sliding", 0.3, 0.5, 0.45),
            PrintInPlaceFitCalibration("loose", 0.4, 0.65, 0.5),
        ),
    )


def target(**changes: object) -> PrinterTarget:
    values: dict[str, object] = {
        "profile_id": "mk4-pla-calibration",
        "profile_revision": 3,
        "printer_id": "printer-mk4-07",
        "nozzle_diameter_mm": 0.4,
        "layer_height_mm": 0.2,
        "material": "PLA:vendor-a:black",
    }
    values.update(changes)
    return PrinterTarget(**values)  # type: ignore[arg-type]


def linear_condition(*, expect: str = "clear") -> MotionCondition:
    return MotionCondition(
        condition_id=f"insert-{expect}",
        check="linear_motion_collision",
        expect=expect,
        description="The insert follows the declared axis.",
        inputs={
            "moving_part": "insert",
            "obstacle_parts": ["receiver"],
            "translation": [0, 0, -40],
            "steps": 14,
            "allow_seated_contact": True,
        },
        thresholds={"maxOverlapMm3": 0.001},
    )


def completed_outcome(condition: MotionCondition, clear: bool) -> MotionEvaluatorOutcome:
    return MotionEvaluatorOutcome(
        condition_sha256=condition.condition_sha256,
        evaluator_id="exact-kernel-sweep-v2",
        status="completed",
        clear=clear,
        evidence_sha256="e" * 64,
        detail_code="sweep_completed",
    )


class PrinterCalibrationTests(unittest.TestCase):
    def test_profile_is_versioned_hash_bound_and_preserves_mit_provenance(self) -> None:
        calibrated = profile()

        self.assertEqual(calibrated.schema_version, CALIBRATION_PROFILE_VERSION)
        self.assertEqual(len(calibrated.profile_sha256), 64)
        self.assertEqual(
            PrinterCalibrationProfile.from_mapping(calibrated.to_dict()).profile_sha256,
            calibrated.profile_sha256,
        )
        self.assertEqual(PrinterTarget.from_mapping(target().to_dict()), target())
        self.assertEqual(
            calibrated.profile_sha256,
            PrinterCalibrationProfile(
                **{
                    **calibrated.to_dict(),
                    "assembled_fits": tuple(reversed(calibrated.assembled_fits)),
                    "print_in_place_fits": tuple(reversed(calibrated.print_in_place_fits)),
                }
            ).profile_sha256,
        )
        self.assertEqual(UPSTREAM_SOURCE_COMMIT, "f18aebe4698d92ffccf07d94e2d624b08d30e667")
        self.assertIn("MIT License", UPSTREAM_MIT_NOTICE)
        self.assertIn("Thompson Labs LLC", UPSTREAM_MIT_NOTICE)

    def test_assembled_mates_derive_from_one_owned_dimension_and_round_trip(self) -> None:
        female = derive_assembled_fit(
            profile(), target(), fit_class="slip", owned_side="male", owned_dimension_mm=4.0
        )
        self.assertEqual(female.status, "passed")
        self.assertAlmostEqual(female.derived_dimension_mm or 0.0, 4.4)
        male = derive_assembled_fit(
            profile(),
            target(),
            fit_class="slip",
            owned_side="female",
            owned_dimension_mm=female.derived_dimension_mm or 0.0,
        )
        self.assertEqual(male.status, "passed")
        self.assertAlmostEqual(male.derived_dimension_mm or 0.0, 4.0)
        self.assertIn("not_physical_fit_evidence", male.limitations)

    def test_print_in_place_uses_exact_profile_values_not_a_material_heuristic(self) -> None:
        receipt = derive_print_in_place_fit(profile(), target(), fit_class="sliding")

        self.assertEqual(receipt.status, "passed")
        self.assertEqual((receipt.xy_gap_mm, receipt.z_gap_mm, receipt.bottom_relief_mm), (0.3, 0.5, 0.45))
        self.assertIn("not_physical_fit_evidence", receipt.limitations)

    def test_profile_nozzle_layer_material_and_revision_mismatches_hold_derivation(self) -> None:
        mismatches = (
            ({"profile_revision": 4}, "profile_revision_mismatch"),
            ({"nozzle_diameter_mm": 0.6}, "nozzle_diameter_mismatch"),
            ({"layer_height_mm": 0.15}, "layer_height_mismatch"),
            ({"material": "PETG:vendor-a:black"}, "material_mismatch"),
        )
        for change, reason in mismatches:
            with self.subTest(reason=reason):
                binding = validate_profile_binding(profile(), target(**change))
                self.assertEqual(binding.status, "held")
                self.assertIn(reason, binding.mismatches)
                assembled = derive_assembled_fit(
                    profile(),
                    target(**change),
                    fit_class="slip",
                    owned_side="male",
                    owned_dimension_mm=4.0,
                )
                self.assertEqual(assembled.status, "held")
                self.assertIsNone(assembled.derived_dimension_mm)
                pip = derive_print_in_place_fit(
                    profile(), target(**change), fit_class="sliding"
                )
                self.assertEqual(pip.status, "held")
                self.assertIsNone(pip.xy_gap_mm)

    def test_unknown_fit_and_nonpositive_derived_dimension_do_not_pass(self) -> None:
        unknown = derive_assembled_fit(
            profile(), target(), fit_class="unmeasured", owned_side="male", owned_dimension_mm=4.0
        )
        self.assertEqual(unknown.status, "held")
        self.assertEqual(unknown.reasons, ("unknown_fit_class",))

        too_small = derive_assembled_fit(
            profile(), target(), fit_class="slip", owned_side="female", owned_dimension_mm=0.2
        )
        self.assertEqual(too_small.status, "failed")
        self.assertIsNone(too_small.derived_dimension_mm)

    def test_profile_schema_and_numeric_self_checks_fail_closed(self) -> None:
        self.assertEqual(self_check_calibration_profile(profile()).status, "passed")
        with self.assertRaises(ValueError):
            PrintInPlaceFitCalibration("bad", 0.3, 0.3, 0.5)
        with self.assertRaises(ValueError):
            AssembledFitCalibration("bad", math.nan)
        with self.assertRaises(ValueError):
            PrinterCalibrationProfile(
                profile_id="bad",
                revision=1,
                printer_id="printer",
                nozzle_diameter_mm=0.4,
                layer_height_mm=0.2,
                material="PLA",
                calibration_evidence_sha256="a" * 64,
                assembled_fits=(AssembledFitCalibration("same", 0.1),),
                print_in_place_fits=(PrintInPlaceFitCalibration("pip", 0.2, 0.4, 0.5),),
                schema_version="unversioned",
            )


class StlTopologyTests(unittest.TestCase):
    def test_alice_public_topology_surface_is_the_shared_workshop(self) -> None:
        from workshop.make.cad import (
            KernelBodyObservation as WorkshopKernelBodyObservation,
            StlInspectionLimits as WorkshopStlInspectionLimits,
            StlPathInspectionError as WorkshopStlPathInspectionError,
            StlTopologyReceipt as WorkshopStlTopologyReceipt,
            inspect_stl_path as workshop_inspect_stl_path,
            inspect_stl_topology as workshop_inspect_stl_topology,
        )

        self.assertIs(KernelBodyObservation, WorkshopKernelBodyObservation)
        self.assertIs(StlInspectionLimits, WorkshopStlInspectionLimits)
        self.assertIs(StlPathInspectionError, WorkshopStlPathInspectionError)
        self.assertIs(inspect_stl_path, workshop_inspect_stl_path)
        self.assertIs(inspect_stl_topology, workshop_inspect_stl_topology)
        self.assertIs(
            type(inspect_stl_topology(binary_stl(tetrahedron()), expected_shell_count=1)),
            WorkshopStlTopologyReceipt,
        )

    def test_binary_tetrahedron_passes_declared_topology_and_binds_exact_source(self) -> None:
        source = binary_stl(tetrahedron(), header=b"solid binary-header-is-valid")
        receipt = inspect_stl_topology(
            source,
            expected_shell_count=1,
            expected_source_sha256=hashlib.sha256(source).hexdigest(),
            expected_source_bytes=len(source),
        )

        self.assertEqual(receipt.status, "passed")
        self.assertEqual(receipt.stl_format, "binary")
        self.assertEqual(receipt.source_sha256, hashlib.sha256(source).hexdigest())
        self.assertEqual(receipt.source_bytes, len(source))
        self.assertEqual(receipt.source_triangle_count, 4)
        self.assertEqual(receipt.validated_triangle_count, 4)
        self.assertEqual(receipt.welded_vertex_count, 4)
        self.assertEqual(receipt.observed_shell_count, 1)
        self.assertAlmostEqual(receipt.shell_signed_volumes_mm3[0], 1.0 / 6.0)
        self.assertEqual(receipt.failure_reasons, ())
        self.assertEqual(receipt.hold_reasons, ())
        self.assertEqual(receipt.receipt_sha256, inspect_stl_topology(source, expected_shell_count=1).receipt_sha256)
        self.assertIn("stl_topology_only_not_cad_kernel_solidness", receipt.limitations)

    def test_ascii_tetrahedron_passes_without_numpy_or_a_kernel(self) -> None:
        source = ascii_stl(tetrahedron())
        receipt = inspect_stl_topology(source, expected_shell_count=1)

        self.assertEqual(receipt.status, "passed")
        self.assertEqual(receipt.stl_format, "ascii")
        self.assertEqual(receipt.boundary_edge_count, 0)
        self.assertEqual(receipt.nonmanifold_edge_count, 0)
        self.assertEqual(receipt.inconsistent_winding_edge_count, 0)

    def test_malformed_binary_is_held_and_never_loses_source_binding(self) -> None:
        source = binary_stl(tetrahedron())[:-7]
        receipt = inspect_stl_topology(source, expected_shell_count=1)

        self.assertEqual(receipt.status, "held")
        self.assertIn("binary_size_mismatch", receipt.hold_reasons)
        self.assertEqual(receipt.source_sha256, hashlib.sha256(source).hexdigest())
        self.assertEqual(receipt.source_bytes, len(source))

        trailing = binary_stl(tetrahedron()) + b"unexpected"
        trailing_receipt = inspect_stl_topology(trailing, expected_shell_count=1)
        self.assertEqual(trailing_receipt.status, "held")
        self.assertIn("binary_size_mismatch", trailing_receipt.hold_reasons)

    def test_nonfinite_binary_and_ascii_coordinates_are_rejected(self) -> None:
        bad_triangle = tetrahedron()
        first = bad_triangle[0]
        bad_triangle[0] = ((math.nan, 0.0, 0.0), first[1], first[2])
        binary_receipt = inspect_stl_topology(binary_stl(bad_triangle), expected_shell_count=1)
        self.assertEqual(binary_receipt.status, "failed")
        self.assertIn("nonfinite_binary_float", binary_receipt.failure_reasons)

        ascii_source = ascii_stl(tetrahedron()).replace(b"vertex 0 0 0", b"vertex nan 0 0", 1)
        ascii_receipt = inspect_stl_topology(ascii_source, expected_shell_count=1)
        self.assertEqual(ascii_receipt.status, "failed")
        self.assertIn("nonfinite_ascii_coordinate", ascii_receipt.failure_reasons)

    def test_nonmanifold_boundary_and_inconsistent_winding_are_hard_failures(self) -> None:
        base = tetrahedron()
        nonmanifold = inspect_stl_topology(binary_stl(base + [base[0]]), expected_shell_count=1)
        self.assertEqual(nonmanifold.status, "failed")
        self.assertIn("nonmanifold_edges", nonmanifold.failure_reasons)

        boundary = inspect_stl_topology(binary_stl(base[:-1]), expected_shell_count=1)
        self.assertEqual(boundary.status, "failed")
        self.assertIn("boundary_edges", boundary.failure_reasons)

        flipped = list(base)
        a, b, c = flipped[0]
        flipped[0] = (a, c, b)
        winding = inspect_stl_topology(binary_stl(flipped), expected_shell_count=1)
        self.assertEqual(winding.status, "failed")
        self.assertIn("inconsistent_winding", winding.failure_reasons)

    def test_expected_shell_count_is_enforced(self) -> None:
        two_shells = tetrahedron() + tetrahedron(offset=(5.0, 0.0, 0.0))
        unexpected = inspect_stl_topology(binary_stl(two_shells), expected_shell_count=1)
        self.assertEqual(unexpected.status, "failed")
        self.assertEqual(unexpected.observed_shell_count, 2)
        self.assertIn("unexpected_shell_count", unexpected.failure_reasons)

        expected = inspect_stl_topology(binary_stl(two_shells), expected_shell_count=2)
        self.assertEqual(expected.status, "passed")

    def test_zero_volume_and_degenerate_geometry_never_pass(self) -> None:
        tiny_limits = StlInspectionLimits(
            weld_tolerance_mm=1e-7,
            degenerate_area_epsilon_mm2=0.0,
            zero_volume_epsilon_mm3=1e-12,
        )
        tiny = inspect_stl_topology(
            binary_stl(tetrahedron(scale=1e-4)),
            expected_shell_count=1,
            limits=tiny_limits,
        )
        self.assertEqual(tiny.status, "failed")
        self.assertIn("zero_or_nonfinite_shell_volume", tiny.failure_reasons)

        degenerate_triangles = tetrahedron() + [((0, 0, 0), (0, 0, 0), (0, 0, 0))]
        degenerate = inspect_stl_topology(binary_stl(degenerate_triangles), expected_shell_count=1)
        self.assertEqual(degenerate.status, "failed")
        self.assertIn("degenerate_triangles", degenerate.failure_reasons)

    def test_source_and_resource_mismatches_hold_instead_of_passing(self) -> None:
        source = binary_stl(tetrahedron())
        wrong_source = inspect_stl_topology(
            source,
            expected_shell_count=1,
            expected_source_sha256="0" * 64,
            expected_source_bytes=len(source) + 1,
        )
        self.assertEqual(wrong_source.status, "held")
        self.assertIn("source_sha256_mismatch", wrong_source.hold_reasons)
        self.assertIn("source_byte_count_mismatch", wrong_source.hold_reasons)

        bounded = inspect_stl_topology(
            source,
            expected_shell_count=1,
            limits=StlInspectionLimits(max_source_bytes=10),
        )
        self.assertEqual(bounded.status, "held")
        self.assertEqual(bounded.hold_reasons, ("source_byte_limit_exceeded",))

        triangle_bounded = inspect_stl_topology(
            source,
            expected_shell_count=1,
            limits=StlInspectionLimits(max_triangles=3),
        )
        self.assertEqual(triangle_bounded.status, "held")
        self.assertEqual(triangle_bounded.hold_reasons, ("triangle_limit_exceeded",))

    def test_kernel_body_claim_requires_completed_source_bound_evidence(self) -> None:
        source = binary_stl(tetrahedron())
        digest = hashlib.sha256(source).hexdigest()

        absent = inspect_stl_topology(source, expected_shell_count=1, expected_body_count=1)
        self.assertEqual(absent.status, "held")
        self.assertIn("kernel_body_count_not_evaluated", absent.hold_reasons)

        inconclusive = KernelBodyObservation(
            source_sha256=digest,
            evaluator_id="kernel-v1",
            status="inconclusive",
            body_count=None,
            evidence_sha256=None,
        )
        held = inspect_stl_topology(
            source,
            expected_shell_count=1,
            expected_body_count=1,
            kernel_body_observation=inconclusive,
        )
        self.assertEqual(held.status, "held")
        self.assertIn("kernel_body_inconclusive", held.hold_reasons)

        wrong_count = KernelBodyObservation(
            source_sha256=digest,
            evaluator_id="kernel-v1",
            status="completed",
            body_count=2,
            evidence_sha256="b" * 64,
        )
        failed = inspect_stl_topology(
            source,
            expected_shell_count=1,
            expected_body_count=1,
            kernel_body_observation=wrong_count,
        )
        self.assertEqual(failed.status, "failed")
        self.assertIn("unexpected_kernel_body_count", failed.failure_reasons)

        matching = KernelBodyObservation(
            source_sha256=digest,
            evaluator_id="kernel-v1",
            status="completed",
            body_count=1,
            evidence_sha256="b" * 64,
        )
        passed = inspect_stl_topology(
            source,
            expected_shell_count=1,
            expected_body_count=1,
            kernel_body_observation=matching,
        )
        self.assertEqual(passed.status, "passed")
        self.assertEqual(passed.observed_kernel_body_count, 1)

    def test_malformed_expectations_are_rejected_at_the_api_boundary(self) -> None:
        source = binary_stl(tetrahedron())
        with self.assertRaises(ValueError):
            inspect_stl_topology(source, expected_shell_count=True)
        with self.assertRaises(ValueError):
            inspect_stl_topology(source, expected_shell_count=1, expected_body_count=0)


class MotionValidationTests(unittest.TestCase):
    def test_conclusive_exact_boolean_can_satisfy_clear_or_blocked(self) -> None:
        clear = linear_condition(expect="clear")
        clear_receipt = validate_motion_outcome(clear, completed_outcome(clear, True))
        self.assertEqual(clear_receipt.status, "passed")
        self.assertIs(clear_receipt.observed_clear, True)

        blocked = linear_condition(expect="blocked")
        blocked_receipt = validate_motion_outcome(blocked, completed_outcome(blocked, False))
        self.assertEqual(blocked_receipt.status, "passed")
        self.assertIs(blocked_receipt.observed_clear, False)
        self.assertIn("sampled_rigid_body_evidence_only", blocked_receipt.limitations)

    def test_conclusive_opposite_result_is_failed_not_held(self) -> None:
        condition = linear_condition(expect="blocked")
        receipt = validate_motion_outcome(condition, completed_outcome(condition, True))

        self.assertEqual(receipt.status, "failed")
        self.assertEqual(receipt.reasons, ("motion_expectation_not_met",))

    def test_evaluator_exception_can_never_satisfy_clear_or_blocked(self) -> None:
        def broken(_: MotionCondition) -> MotionEvaluatorOutcome:
            raise RuntimeError("kernel boolean failed")

        for expectation in ("clear", "blocked"):
            with self.subTest(expectation=expectation):
                receipt = evaluate_motion_condition(linear_condition(expect=expectation), broken)
                self.assertEqual(receipt.status, "held")
                self.assertEqual(receipt.evaluator_status, "error")
                self.assertEqual(receipt.reasons, ("evaluator_exception:RuntimeError",))
                self.assertIsNone(receipt.observed_clear)

    def test_inconclusive_or_error_outcome_can_never_satisfy_blocked(self) -> None:
        condition = linear_condition(expect="blocked")
        for status in ("inconclusive", "error"):
            with self.subTest(status=status):
                outcome = MotionEvaluatorOutcome(
                    condition_sha256=condition.condition_sha256,
                    evaluator_id="kernel-v2",
                    status=status,
                    clear=None,
                    evidence_sha256=None,
                    detail_code=f"kernel_{status}",
                )
                receipt = validate_motion_outcome(condition, outcome)
                self.assertEqual(receipt.status, "held")
                self.assertEqual(receipt.reasons, (f"evaluator_{status}",))
                self.assertIsNone(receipt.observed_clear)

    def test_missing_none_or_integer_clear_is_malformed_not_false(self) -> None:
        condition = linear_condition(expect="blocked")
        base = {
            "condition_sha256": condition.condition_sha256,
            "evaluator_id": "kernel-v2",
            "status": "completed",
            "evidence_sha256": "e" * 64,
            "detail_code": "completed",
        }
        for value in (None, 0, 1, "false"):
            with self.subTest(value=value):
                raw = dict(base)
                if value is not None:
                    raw["clear"] = value
                receipt = evaluate_motion_condition(condition, lambda _: raw)
                self.assertEqual(receipt.status, "held")
                self.assertEqual(receipt.reasons, ("malformed_evaluator_outcome",))

    def test_condition_digest_mismatch_is_held(self) -> None:
        condition = linear_condition(expect="clear")
        outcome = MotionEvaluatorOutcome(
            condition_sha256="0" * 64,
            evaluator_id="kernel-v2",
            status="completed",
            clear=True,
            evidence_sha256="e" * 64,
            detail_code="completed",
        )
        receipt = validate_motion_outcome(condition, outcome)

        self.assertEqual(receipt.status, "held")
        self.assertEqual(receipt.reasons, ("condition_sha256_mismatch",))

    def test_peter_style_schema_requires_explicit_expect_and_bounded_finite_inputs(self) -> None:
        raw = linear_condition().to_dict()
        reconstructed = MotionCondition.from_mapping(raw)
        self.assertEqual(reconstructed.condition_sha256, linear_condition().condition_sha256)

        missing_expect = dict(raw)
        missing_expect.pop("expect")
        with self.assertRaises(ValueError):
            MotionCondition.from_mapping(missing_expect)

        bad_steps = dict(raw)
        bad_steps["inputs"] = {**raw["inputs"], "steps": 0}  # type: ignore[dict-item]
        with self.assertRaises(ValueError):
            MotionCondition.from_mapping(bad_steps)

        bad_threshold = dict(raw)
        bad_threshold["thresholds"] = {"maxOverlapMm3": math.nan}
        with self.assertRaises(ValueError):
            MotionCondition.from_mapping(bad_threshold)

    def test_assembly_sequence_is_recursively_normalized_and_hash_bound(self) -> None:
        step = linear_condition().to_dict()
        sequence = MotionCondition(
            condition_id="assembly-order",
            check="assembly_sequence",
            expect="clear",
            inputs={"steps": [step]},
            thresholds={},
        )

        self.assertEqual(sequence.inputs["steps"][0]["id"], step["id"])
        self.assertEqual(sequence.inputs["steps"][0]["schema_version"], step["schema_version"])
        self.assertEqual(len(sequence.condition_sha256), 64)

        implicit_expect = dict(step)
        implicit_expect.pop("expect")
        with self.assertRaises(ValueError):
            MotionCondition(
                condition_id="unsafe-default",
                check="assembly_sequence",
                expect="clear",
                inputs={"steps": [implicit_expect]},
            )


if __name__ == "__main__":
    unittest.main()
