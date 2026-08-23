"""Outcome-level eval runner for release-policy regression suites."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .policy import ReleaseFacts, ReleasePolicy
from .reward import Evidence


@dataclass(frozen=True, slots=True)
class EvalCaseResult:
    case_id: str
    passed: bool
    expected_allowed: bool
    actual_allowed: bool
    failures: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvalSuiteResult:
    suite: str
    passed: bool
    cases: tuple[EvalCaseResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "passed": self.passed,
            "cases": [asdict(case) for case in self.cases],
        }


def run_release_policy_suite(path: str | Path) -> EvalSuiteResult:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("cases"), list):
        raise ValueError("eval suite must be an object with a cases array")
    policy = ReleasePolicy()
    results: list[EvalCaseResult] = []
    for case in raw["cases"]:
        facts = ReleaseFacts(**case["facts"])
        evidence = [Evidence(**item) for item in case["evidence"]]
        decision = policy.assess(facts, evidence, effect_mode=case["effect_mode"])
        expected = bool(case["expected_allowed"])
        results.append(
            EvalCaseResult(
                case_id=str(case["id"]),
                passed=decision.allowed is expected,
                expected_allowed=expected,
                actual_allowed=decision.allowed,
                failures=decision.failures,
            )
        )
    return EvalSuiteResult(
        suite=str(raw.get("suite") or Path(path).stem),
        passed=all(result.passed for result in results),
        cases=tuple(results),
    )
