import unittest
from pathlib import Path

from alice.evals import run_release_policy_suite


class EvalTests(unittest.TestCase):
    def test_release_policy_regression_suite(self) -> None:
        path = Path(__file__).resolve().parents[1] / "evals" / "release-policy.json"
        result = run_release_policy_suite(path)
        self.assertTrue(result.passed, result.to_dict())
        self.assertGreaterEqual(len(result.cases), 5)


if __name__ == "__main__":
    unittest.main()
