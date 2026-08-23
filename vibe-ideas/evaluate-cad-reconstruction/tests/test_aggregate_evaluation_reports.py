import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "aggregate_evaluation_reports.py"
)
SPEC = importlib.util.spec_from_file_location("aggregate_evaluation_reports", SCRIPT_PATH)
aggregate_evaluation_reports = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(aggregate_evaluation_reports)


def _write_report(project: Path, conditions: list[dict], *, nested_physical: bool = False) -> None:
    project.mkdir()
    physical = {
        "condition_results": conditions,
        "missing_helper_notes": [],
        "risk_factors": [],
    }
    report = {
        "scores": {
            "printability": {"score": 10.0},
            "physical_correctness": {"score": 10.0},
            "feature_retention": {"score": 10.0},
        },
        "physical_correctness": physical,
    }
    if nested_physical:
        report["scores"]["physical_correctness"] = {"score": 10.0, **physical}
        report.pop("physical_correctness")
    (project / "evaluation_report.json").write_text(
        json.dumps(report)
    )


class AggregateEvaluationReportTests(unittest.TestCase):
    def test_collect_flags_reports_with_only_component_count_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_report(
                root / "basic-only",
                [
                    {"id": "assembly_count", "check": "assembly_component_count", "status": "pass"},
                    {"id": "part_count", "check": "part_component_count", "status": "pass"},
                ],
            )
            _write_report(
                root / "pairwise-checked",
                [
                    {"id": "assembly_count", "check": "assembly_component_count", "status": "pass"},
                    {"id": "parts_touch", "check": "part_contact", "status": "pass"},
                ],
            )

            data = aggregate_evaluation_reports._collect(root)

            reviews = data["basic_physical_check_reviews"]
            self.assertEqual(len(reviews), 1)
            self.assertTrue(reviews[0]["project"].endswith("basic-only"))
            self.assertEqual(reviews[0]["checks"], ["assembly_component_count", "part_component_count"])
            self.assertIn("deeply investigate", data["next_codex_prompt"])
            self.assertIn("basic-only", data["next_codex_prompt"])

    def test_collect_flags_reports_with_only_component_count_and_clear_path_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_report(
                root / "basic-plus-clear-path",
                [
                    {"id": "assembly_count", "check": "assembly_component_count", "status": "pass"},
                    {"id": "path_1", "check": "clear_path_proxy", "status": "pass"},
                    {"id": "path_2", "check": "clear_path_proxy", "status": "pass"},
                ],
            )
            _write_report(
                root / "clear-path-plus-pairwise",
                [
                    {"id": "assembly_count", "check": "assembly_component_count", "status": "pass"},
                    {"id": "path_1", "check": "clear_path_proxy", "status": "pass"},
                    {"id": "parts_touch", "check": "part_contact", "status": "pass"},
                ],
            )

            data = aggregate_evaluation_reports._collect(root)

            reviews = data["basic_physical_check_reviews"]
            self.assertEqual(len(reviews), 1)
            self.assertTrue(reviews[0]["project"].endswith("basic-plus-clear-path"))
            self.assertEqual(
                reviews[0]["checks"],
                ["assembly_component_count", "clear_path_proxy"],
            )

    def test_collect_flags_nested_score_physical_conditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_report(
                root / "nested-basic-only",
                [{"id": "assembly_count", "check": "assembly_component_count", "status": "pass"}],
                nested_physical=True,
            )

            data = aggregate_evaluation_reports._collect(root)

            reviews = data["basic_physical_check_reviews"]
            self.assertEqual(len(reviews), 1)
            self.assertTrue(reviews[0]["project"].endswith("nested-basic-only"))

    def test_collect_does_not_flag_reports_without_physical_conditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_report(root / "empty", [])

            data = aggregate_evaluation_reports._collect(root)

            self.assertEqual(data["basic_physical_check_reviews"], [])


if __name__ == "__main__":
    unittest.main()
