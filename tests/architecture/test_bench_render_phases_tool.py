import importlib.util
import unittest
from pathlib import Path


TOOL_PATH = Path(__file__).resolve().parents[2] / "tools" / "bench_render_phases.py"
SPEC = importlib.util.spec_from_file_location("workshop_bench_render_phases", TOOL_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError("cannot load Workshop render-phase benchmark")
BENCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCH)


class BenchRenderPhasesToolTest(unittest.TestCase):
    """Covers only the pure, OCP-free surface of the tool: importing it must
    not require build123d/OCP, since issue #58 asks for a script runnable by
    hand with the CAD skill's interpreter, not one CI can import freely."""

    def test_targets_the_real_companion_assembly_not_a_synthetic_mesh(self):
        self.assertTrue(BENCH.COMPANION_ENTRY.is_file())
        self.assertEqual(BENCH.COMPANION_ENTRY.name, "antisol.step.py")
        self.assertIn("ad-astra-antisol-companion", str(BENCH.COMPANION_ENTRY))

    def test_cache_dir_is_the_occurrence_tessellation_cache_beside_the_entry(self):
        self.assertEqual(
            BENCH.cache_dir(),
            BENCH.COMPANION_ENTRY.parent / "__cadgen__" / "tessellation-v1",
        )

    def test_host_info_reports_core_count_and_load(self):
        info = BENCH.host_info()
        self.assertIn("cores=", info)
        self.assertIn("usable=", info)

    def test_triangle_count_sums_faces_across_occurrences(self):
        occurrences = [
            (None, [1, 2, 3], None),
            (None, [1, 2], None),
        ]
        self.assertEqual(BENCH.triangle_count(occurrences), 5)

    def test_parse_args_defaults_run_every_case(self):
        args = BENCH.parse_args([])
        self.assertFalse(args.skip_multi_camera)
        self.assertFalse(args.skip_multi_state)
        self.assertEqual(args.view, "iso")
        self.assertEqual(args.cameras.split(","), BENCH.CAMERA_VIEWS)

    def test_multi_state_case_covers_the_products_own_three_board_states(self):
        self.assertEqual(BENCH.BOARD_STATES, ["opening", "midgame", "endgame"])

    def test_main_is_not_wired_into_any_test_framework(self):
        # Issue #58: "Not part of CI and asserts no timing." The tool prints
        # numbers for a human to read; it must never import a test framework
        # that could turn one of those numbers into an assertion.
        source = TOOL_PATH.read_text(encoding="utf-8")
        self.assertNotIn("import unittest", source)
        self.assertNotIn("import pytest", source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
