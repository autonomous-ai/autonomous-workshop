import json
import tempfile
import unittest
from pathlib import Path

from cad_reconstruction_eval.physical_correctness_score import (
    score_condition_manifest,
    score_physical_correctness_project,
)
from cad_reconstruction_eval.instance_extraction import extract_component_stls
from tests.test_printability_score import _cube_triangles, _write_ascii_stl


def _translated(triangles, offset):
    ox, oy, oz = offset
    return [
        tuple((x + ox, y + oy, z + oz) for x, y, z in tri)
        for tri in triangles
    ]


class PhysicalCorrectnessScoreTests(unittest.TestCase):
    def test_bbox_overlap_condition_is_unsupported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = root / "body.stl"
            lid = root / "lid.stl"
            assembly = root / "assembly.stl"
            _write_ascii_stl(body, _cube_triangles(size=10.0))
            _write_ascii_stl(lid, _translated(_cube_triangles(size=10.0), (5.0, 0.0, 0.0)))
            _write_ascii_stl(
                assembly,
                _cube_triangles(size=10.0)
                + _translated(_cube_triangles(size=10.0), (5.0, 0.0, 0.0)),
            )
            manifest = {
                "assembly": "assembly.stl",
                "parts": {"body": "body.stl", "lid": "lid.stl"},
                "conditions": [
                    {
                        "id": "body_lid_do_not_overlap",
                        "category": "interference_collision",
                        "severity": "critical",
                        "description": "Body and lid must not overlap substantially.",
                        "check": "part_bbox_overlap",
                        "inputs": {"part_a": "body", "part_b": "lid"},
                        "thresholds": {"max_overlap_ratio": 0.01},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            self.assertEqual(report["condition_results"][0]["status"], "inconclusive")
            self.assertIn("unsupported check: part_bbox_overlap", report["condition_results"][0]["detail"])
            self.assertIn("condition inconclusive: body_lid_do_not_overlap", report["risk_factors"])
            self.assertGreater(report["score"], 4.0)

    def test_missing_part_condition_is_inconclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = root / "body.stl"
            _write_ascii_stl(body, _cube_triangles(size=10.0))
            manifest = {
                "parts": {"body": "body.stl"},
                "conditions": [
                    {
                        "id": "missing_lid_clearance",
                        "category": "fit_clearance",
                        "severity": "major",
                        "description": "Body and lid should have clearance.",
                        "check": "part_bbox_overlap",
                        "inputs": {"part_a": "body", "part_b": "lid"},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            self.assertEqual(report["condition_results"][0]["status"], "inconclusive")
            self.assertIn("unsupported check: part_bbox_overlap", report["condition_results"][0]["detail"])
            self.assertIn("condition inconclusive: missing_lid_clearance", report["risk_factors"])
            self.assertGreater(report["score"], 4.0)

    def test_default_project_score_keeps_layer_one_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.stl"
            b = root / "b.stl"
            assembly = root / "assembly.stl"
            _write_ascii_stl(a, _cube_triangles(size=10.0))
            _write_ascii_stl(b, _translated(_cube_triangles(size=10.0), (20.0, 0.0, 0.0)))
            _write_ascii_stl(
                assembly,
                _cube_triangles(size=10.0)
                + _translated(_cube_triangles(size=10.0), (20.0, 0.0, 0.0)),
            )

            report = score_physical_correctness_project(assembly=assembly, parts=[a, b])

            self.assertEqual(report["class"], "easy")
            self.assertEqual(report["metrics"]["part_count"], 2)
            self.assertEqual(report["condition_results"], [])

    def test_whole_assembly_proxy_part_does_not_trigger_count_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assembly = root / "assembly.stl"
            _write_ascii_stl(
                assembly,
                _cube_triangles(size=4.0)
                + _translated(_cube_triangles(size=4.0), (10.0, 0.0, 0.0)),
            )
            manifest = {
                "assembly": "assembly.stl",
                "parts": {"body": "assembly.stl"},
                "conditions": [
                    {
                        "id": "two_components_expected",
                        "category": "separation_correctness",
                        "severity": "critical",
                        "check": "assembly_component_count",
                        "thresholds": {"expected_components": 2},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            self.assertEqual(report["score"], 10.0)
            self.assertEqual(report["condition_results"][0]["status"], "pass")
            self.assertNotIn(
                "assembly has 2 connected components but 1 part files were supplied",
                report["risk_factors"],
            )

    def test_part_collision_condition_fails_for_intersecting_meshes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = root / "body.stl"
            lid = root / "lid.stl"
            _write_ascii_stl(body, _cube_triangles(size=10.0))
            _write_ascii_stl(lid, _translated(_cube_triangles(size=10.0), (5.0, 0.0, 0.0)))
            manifest = {
                "parts": {"body": "body.stl", "lid": "lid.stl"},
                "conditions": [
                    {
                        "id": "no_body_lid_collision",
                        "category": "interference_collision",
                        "severity": "critical",
                        "check": "part_collision",
                        "inputs": {"part_a": "body", "part_b": "lid"},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            self.assertEqual(report["condition_results"][0]["status"], "fail")
            self.assertTrue(report["condition_results"][0]["measurements"]["collides"])
            self.assertIn("critical condition failed: no_body_lid_collision", report["hard_failures"])

    def test_part_clearance_condition_uses_mesh_distance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            peg = root / "peg.stl"
            socket = root / "socket.stl"
            _write_ascii_stl(peg, _cube_triangles(size=10.0))
            _write_ascii_stl(socket, _translated(_cube_triangles(size=10.0), (10.6, 0.0, 0.0)))
            manifest = {
                "parts": {"peg": "peg.stl", "socket": "socket.stl"},
                "conditions": [
                    {
                        "id": "peg_socket_clearance",
                        "category": "fit_clearance",
                        "severity": "major",
                        "check": "part_clearance",
                        "inputs": {"part_a": "peg", "part_b": "socket"},
                        "thresholds": {"min_clearance_mm": 0.4, "max_clearance_mm": 0.8},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertAlmostEqual(result["measurements"]["min_distance_mm"], 0.6, places=5)

    def test_extracted_components_can_drive_part_clearance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assembly = root / "assembly.stl"
            _write_ascii_stl(
                assembly,
                _cube_triangles(size=4.0)
                + _translated(_cube_triangles(size=4.0), (10.0, 0.0, 0.0)),
            )

            extraction = extract_component_stls(assembly, root / "components")
            self.assertEqual(extraction["component_count"], 2)
            parts = {
                name: str(Path(path).relative_to(root))
                for name, path in extraction["parts"].items()
            }
            manifest = {
                "assembly": "assembly.stl",
                "parts": parts,
                "conditions": [
                    {
                        "id": "extracted_components_have_expected_gap",
                        "category": "fit_clearance",
                        "severity": "major",
                        "check": "part_clearance",
                        "inputs": {"part_a": "component_000", "part_b": "component_001"},
                        "thresholds": {"min_clearance_mm": 5.9, "max_clearance_mm": 6.1},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertAlmostEqual(result["measurements"]["min_distance_mm"], 6.0, places=5)

    def test_part_contact_condition_requires_near_touch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.stl"
            cap = root / "cap.stl"
            _write_ascii_stl(base, _cube_triangles(size=10.0))
            _write_ascii_stl(cap, _translated(_cube_triangles(size=10.0), (0.0, 0.0, 10.05)))
            manifest = {
                "parts": {"base": "base.stl", "cap": "cap.stl"},
                "conditions": [
                    {
                        "id": "cap_seats_on_base",
                        "category": "contact_engagement",
                        "severity": "major",
                        "check": "part_contact",
                        "inputs": {"part_a": "base", "part_b": "cap"},
                        "thresholds": {"max_contact_distance_mm": 0.1},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertAlmostEqual(result["measurements"]["min_distance_mm"], 0.05, places=5)

    def test_spherical_fit_allows_explicit_snap_interference_range(self):
        report = score_physical_correctness_project(
            conditions=[
                {
                    "id": "ball_socket_radius_compatible",
                    "category": "fit_clearance",
                    "severity": "major",
                    "check": "spherical_fit",
                    "inputs": {"ball_radius_mm": 3.0, "socket_radius_mm": 2.9},
                    "thresholds": {"min_radial_clearance_mm": -0.2, "max_radial_clearance_mm": 0.15},
                }
            ]
        )

        result = report["condition_results"][0]
        self.assertEqual(result["status"], "pass")
        self.assertAlmostEqual(result["measurements"]["radial_clearance_mm"], -0.1, places=5)

    def test_spherical_fit_fails_outside_clearance_range(self):
        report = score_physical_correctness_project(
            conditions=[
                {
                    "id": "ball_socket_too_loose",
                    "category": "fit_clearance",
                    "severity": "major",
                    "check": "spherical_fit",
                    "inputs": {"ball_diameter_mm": 5.0, "socket_diameter_mm": 6.0},
                    "thresholds": {"min_radial_clearance_mm": -0.05, "max_radial_clearance_mm": 0.2},
                }
            ]
        )

        result = report["condition_results"][0]
        self.assertEqual(result["status"], "fail")
        self.assertAlmostEqual(result["measurements"]["radial_clearance_mm"], 0.5, places=5)

    def test_linear_motion_collision_samples_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slider = root / "slider.stl"
            stop = root / "stop.stl"
            _write_ascii_stl(slider, _cube_triangles(size=4.0))
            _write_ascii_stl(stop, _translated(_cube_triangles(size=4.0), (8.0, 0.0, 0.0)))
            manifest = {
                "parts": {"slider": "slider.stl", "stop": "stop.stl"},
                "conditions": [
                    {
                        "id": "slider_path_clear",
                        "category": "motion_path",
                        "severity": "critical",
                        "check": "linear_motion_collision",
                        "inputs": {
                            "moving_part": "slider",
                            "obstacle_part": "stop",
                            "translation": [8.0, 0.0, 0.0],
                            "steps": 5,
                        },
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "fail")
            self.assertTrue(result["measurements"]["collides"])
            self.assertEqual(result["measurements"]["first_collision_step"], 3)

    def test_part_component_count_detects_disconnected_part(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            broken = root / "broken.stl"
            _write_ascii_stl(
                broken,
                _cube_triangles(size=4.0)
                + _translated(_cube_triangles(size=4.0), (10.0, 0.0, 0.0)),
            )
            manifest = {
                "parts": {"broken": "broken.stl"},
                "conditions": [
                    {
                        "id": "part_is_one_component",
                        "category": "separation_correctness",
                        "severity": "major",
                        "check": "part_component_count",
                        "inputs": {"part": "broken"},
                        "thresholds": {"expected_components": 1},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["measurements"]["actual_components"], 2)

    def test_clear_path_proxy_counts_unobstructed_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = root / "body.stl"
            _write_ascii_stl(body, _cube_triangles(size=10.0))
            manifest = {
                "parts": {"body": "body.stl"},
                "conditions": [
                    {
                        "id": "sampled_paths_are_clear",
                        "category": "functional_feature_preservation",
                        "severity": "minor",
                        "check": "clear_path_proxy",
                        "inputs": {
                            "part": "body",
                            "paths": [
                                {"start": [20.0, 0.0, 5.0], "end": [20.0, 10.0, 5.0]},
                                {"start": [5.1, -1.0, 5.3], "end": [5.1, 11.0, 5.3]},
                            ],
                        },
                        "thresholds": {
                            "min_clear_paths": 1,
                            "max_intersections_per_clear_path": 0,
                        },
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["measurements"]["clear_path_count"], 1)
            self.assertEqual(result["measurements"]["total_paths"], 2)
            self.assertEqual(result["measurements"]["total_triangle_count"], 12)
            self.assertLess(result["measurements"]["candidate_triangle_count_min"], 12)

    def test_clear_path_proxy_fails_when_required_paths_hit_mesh(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = root / "body.stl"
            _write_ascii_stl(body, _cube_triangles(size=10.0))
            manifest = {
                "parts": {"body": "body.stl"},
                "conditions": [
                    {
                        "id": "hole_axis_should_be_clear",
                        "category": "fit_clearance",
                        "severity": "major",
                        "check": "clear_path_proxy",
                        "inputs": {
                            "part": "body",
                            "paths": [
                                {"start": [5.1, -1.0, 5.3], "end": [5.1, 11.0, 5.3]}
                            ],
                        },
                        "thresholds": {"min_clear_fraction": 1.0},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["measurements"]["clear_path_count"], 0)
            self.assertLessEqual(result["measurements"]["candidate_triangle_count_max"], 12)
            self.assertIn("major condition failed: hole_axis_should_be_clear", report["risk_factors"])

    def test_linear_motion_clearance_checks_minimum_clearance_along_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slider = root / "slider.stl"
            wall = root / "wall.stl"
            _write_ascii_stl(slider, _cube_triangles(size=4.0))
            _write_ascii_stl(wall, _translated(_cube_triangles(size=4.0), (6.0, 0.0, 0.0)))
            manifest = {
                "parts": {"slider": "slider.stl", "wall": "wall.stl"},
                "conditions": [
                    {
                        "id": "slider_keeps_clearance",
                        "category": "motion_path",
                        "severity": "major",
                        "check": "linear_motion_clearance",
                        "inputs": {
                            "moving_part": "slider",
                            "obstacle_part": "wall",
                            "translation": [1.0, 0.0, 0.0],
                            "steps": 1,
                        },
                        "thresholds": {"min_clearance_mm": 1.5},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "fail")
            self.assertAlmostEqual(result["measurements"]["minimum_path_clearance_mm"], 1.0, places=5)

    def test_rotation_motion_collision_samples_angular_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            arm = root / "arm.stl"
            stop = root / "stop.stl"
            _write_ascii_stl(arm, _translated(_cube_triangles(size=4.0), (1.0, 0.0, 0.0)))
            _write_ascii_stl(stop, _translated(_cube_triangles(size=4.0), (-5.0, 0.0, 0.0)))
            manifest = {
                "parts": {"arm": "arm.stl", "stop": "stop.stl"},
                "conditions": [
                    {
                        "id": "arm_swing_clear",
                        "category": "motion_path",
                        "severity": "critical",
                        "check": "rotation_motion_collision",
                        "inputs": {
                            "moving_part": "arm",
                            "obstacle_part": "stop",
                            "axis_point": [0.0, 0.0, 0.0],
                            "axis_direction": [0.0, 0.0, 1.0],
                            "angle_start_deg": 0.0,
                            "angle_end_deg": 90.0,
                            "steps": 2,
                        },
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "fail")
            self.assertTrue(result["measurements"]["collides"])
            self.assertGreaterEqual(result["measurements"]["first_collision_step"], 1)

    def test_axis_alignment_uses_explicit_axes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {
                "conditions": [
                    {
                        "id": "hinge_axes_align",
                        "category": "contact_engagement",
                        "severity": "major",
                        "check": "axis_alignment",
                        "inputs": {
                            "axis_a": {"point": [0.0, 0.0, 0.0], "direction": [0.0, 0.0, 1.0]},
                            "axis_b": {"point": [0.2, 0.0, 5.0], "direction": [0.0, 0.0, 1.0]},
                        },
                        "thresholds": {"max_axis_offset_mm": 0.5, "max_angle_deg": 1.0},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertAlmostEqual(result["measurements"]["axis_offset_mm"], 0.2, places=5)

    def test_relative_pose_uses_part_centroids_along_axis(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.stl"
            cap = root / "cap.stl"
            _write_ascii_stl(base, _cube_triangles(size=10.0))
            _write_ascii_stl(cap, _translated(_cube_triangles(size=10.0), (0.0, 0.0, 12.0)))
            manifest = {
                "parts": {"base": "base.stl", "cap": "cap.stl"},
                "conditions": [
                    {
                        "id": "cap_above_base",
                        "category": "assembly_layout",
                        "severity": "major",
                        "check": "relative_pose",
                        "inputs": {"part_a": "base", "part_b": "cap", "axis": [0.0, 0.0, 1.0]},
                        "thresholds": {"min_delta_mm": 10.0, "max_delta_mm": 14.0},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertAlmostEqual(result["measurements"]["centroid_delta_along_axis_mm"], 12.0, places=5)

    def test_opening_presence_checks_clear_line_segment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = root / "frame.stl"
            _write_ascii_stl(
                frame,
                _cube_triangles(size=4.0)
                + _translated(_cube_triangles(size=4.0), (8.0, 0.0, 0.0)),
            )
            manifest = {
                "parts": {"frame": "frame.stl"},
                "conditions": [
                    {
                        "id": "center_slot_open",
                        "category": "functional_feature_preservation",
                        "severity": "critical",
                        "check": "opening_presence",
                        "inputs": {
                            "part": "frame",
                            "segment_start": [4.5, 2.0, 2.0],
                            "segment_end": [7.5, 2.0, 2.0],
                            "samples": 5,
                        },
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["measurements"]["inside_sample_count"], 0)

    def test_vent_opening_proxy_counts_clear_sample_rays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            grille = root / "grille.stl"
            _write_ascii_stl(
                grille,
                _cube_triangles(size=4.0)
                + _translated(_cube_triangles(size=4.0), (8.0, 0.0, 0.0)),
            )
            manifest = {
                "parts": {"grille": "grille.stl"},
                "conditions": [
                    {
                        "id": "grille_has_open_slots",
                        "category": "functional_feature_preservation",
                        "severity": "minor",
                        "check": "vent_opening_proxy",
                        "inputs": {
                            "part": "grille",
                            "rays": [
                                {"start": [4.5, 1.0, 1.0], "end": [7.5, 1.0, 1.0]},
                                {"start": [4.5, 3.0, 3.0], "end": [7.5, 3.0, 3.0]},
                            ],
                        },
                        "thresholds": {"min_clear_rays": 2},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["measurements"]["clear_ray_count"], 2)
            self.assertEqual(result["measurements"]["total_rays"], 2)

    def test_vent_opening_proxy_fails_when_sample_rays_hit_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocked = root / "blocked.stl"
            _write_ascii_stl(blocked, _translated(_cube_triangles(size=4.0), (4.0, 0.0, 0.0)))
            manifest = {
                "parts": {"blocked": "blocked.stl"},
                "conditions": [
                    {
                        "id": "blocked_grille_has_open_slots",
                        "category": "functional_feature_preservation",
                        "severity": "minor",
                        "check": "vent_opening_proxy",
                        "inputs": {
                            "part": "blocked",
                            "rays": [
                                {"start": [3.5, 1.0, 2.0], "end": [8.5, 1.0, 2.0]},
                                {"start": [3.5, 3.0, 1.0], "end": [8.5, 3.0, 1.0]},
                            ],
                        },
                        "thresholds": {"min_clear_fraction": 0.5},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["measurements"]["clear_ray_count"], 0)

    def test_vent_grid_open_area_proxy_samples_rectangular_vent_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            grille = root / "grille.stl"
            _write_ascii_stl(
                grille,
                _cube_triangles(size=2.0)
                + _translated(_cube_triangles(size=2.0), (4.0, 0.0, 0.0))
                + _translated(_cube_triangles(size=2.0), (8.0, 0.0, 0.0)),
            )
            manifest = {
                "parts": {"grille": "grille.stl"},
                "conditions": [
                    {
                        "id": "grille_grid_has_open_paths",
                        "category": "functional_feature_preservation",
                        "severity": "minor",
                        "check": "vent_grid_open_area_proxy",
                        "inputs": {
                            "part": "grille",
                            "grid_origin": [0.5, 1.0, 1.0],
                            "u_vector": [8.0, 0.0, 0.0],
                            "v_vector": [0.0, 0.0, 0.0],
                            "ray_direction": [0.0, 1.0, 0.0],
                            "ray_length_mm": 4.0,
                            "rows": 1,
                            "cols": 5,
                        },
                        "thresholds": {"min_clear_fraction": 0.4},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["measurements"]["clear_ray_count"], 2)
            self.assertEqual(result["measurements"]["total_rays"], 5)

    def test_vent_grid_open_area_proxy_fails_solid_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            solid = root / "solid.stl"
            _write_ascii_stl(solid, _cube_triangles(size=10.0))
            manifest = {
                "parts": {"solid": "solid.stl"},
                "conditions": [
                    {
                        "id": "solid_grid_has_open_paths",
                        "category": "functional_feature_preservation",
                        "severity": "minor",
                        "check": "vent_grid_open_area_proxy",
                        "inputs": {
                            "part": "solid",
                            "grid_origin": [1.3, -1.0, 5.1],
                            "u_vector": [7.4, 0.0, 0.0],
                            "v_vector": [0.0, 0.0, 0.0],
                            "ray_direction": [0.0, 1.0, 0.0],
                            "ray_length_mm": 12.0,
                            "rows": 1,
                            "cols": 5,
                        },
                        "thresholds": {"min_clear_fraction": 0.2},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["measurements"]["clear_ray_count"], 0)

    def test_feature_count_counts_named_parts_by_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("post_0", "post_1", "post_2", "base"):
                _write_ascii_stl(root / f"{name}.stl", _cube_triangles(size=2.0))
            manifest = {
                "parts": {
                    "post_0": "post_0.stl",
                    "post_1": "post_1.stl",
                    "post_2": "post_2.stl",
                    "base": "base.stl",
                },
                "conditions": [
                    {
                        "id": "three_posts_present",
                        "category": "functional_feature_preservation",
                        "severity": "major",
                        "check": "feature_count",
                        "inputs": {"part_name_prefix": "post_"},
                        "thresholds": {"expected_count": 3},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["measurements"]["actual_count"], 3)

    def test_cylindrical_fit_checks_diameter_clearance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {
                "conditions": [
                    {
                        "id": "pin_fits_hole",
                        "category": "fit_clearance",
                        "severity": "major",
                        "check": "cylindrical_fit",
                        "inputs": {"pin_diameter_mm": 2.0, "hole_diameter_mm": 2.4},
                        "thresholds": {"min_diameter_clearance_mm": 0.2, "max_diameter_clearance_mm": 0.6},
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertAlmostEqual(result["measurements"]["diameter_clearance_mm"], 0.4, places=5)

    def test_contact_graph_checks_expected_and_forbidden_contacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.stl"
            cap = root / "cap.stl"
            loose = root / "loose.stl"
            _write_ascii_stl(base, _cube_triangles(size=4.0))
            _write_ascii_stl(cap, _translated(_cube_triangles(size=4.0), (0.0, 0.0, 4.05)))
            _write_ascii_stl(loose, _translated(_cube_triangles(size=4.0), (20.0, 0.0, 0.0)))
            manifest = {
                "parts": {"base": "base.stl", "cap": "cap.stl", "loose": "loose.stl"},
                "conditions": [
                    {
                        "id": "expected_contact_graph",
                        "category": "contact_engagement",
                        "severity": "major",
                        "check": "contact_graph",
                        "inputs": {
                            "expected_contacts": [["base", "cap"]],
                            "forbidden_contacts": [["base", "loose"]],
                        },
                        "thresholds": {
                            "max_contact_distance_mm": 0.1,
                            "min_forbidden_clearance_mm": 1.0,
                        },
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["measurements"]["failed_edges"], [])

    def test_assembly_sequence_runs_ordered_subchecks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slider = root / "slider.stl"
            wall = root / "wall.stl"
            _write_ascii_stl(slider, _cube_triangles(size=4.0))
            _write_ascii_stl(wall, _translated(_cube_triangles(size=4.0), (10.0, 0.0, 0.0)))
            manifest = {
                "parts": {"slider": "slider.stl", "wall": "wall.stl"},
                "conditions": [
                    {
                        "id": "insert_slider_then_clearance",
                        "category": "motion_path",
                        "severity": "critical",
                        "check": "assembly_sequence",
                        "inputs": {
                            "steps": [
                                {
                                    "id": "slide_in",
                                    "check": "linear_motion_collision",
                                    "inputs": {
                                        "moving_part": "slider",
                                        "obstacle_part": "wall",
                                        "translation": [2.0, 0.0, 0.0],
                                        "steps": 2,
                                    },
                                },
                                {
                                    "id": "keep_clearance",
                                    "check": "linear_motion_clearance",
                                    "inputs": {
                                        "moving_part": "slider",
                                        "obstacle_part": "wall",
                                        "translation": [2.0, 0.0, 0.0],
                                        "steps": 2,
                                    },
                                    "thresholds": {"min_clearance_mm": 3.0},
                                },
                            ]
                        },
                    }
                ],
            }
            manifest_path = root / "physical_conditions.json"
            manifest_path.write_text(json.dumps(manifest))

            report = score_condition_manifest(manifest_path)

            result = report["condition_results"][0]
            self.assertEqual(result["status"], "pass")
            self.assertEqual(len(result["measurements"]["step_results"]), 2)


if __name__ == "__main__":
    unittest.main()
