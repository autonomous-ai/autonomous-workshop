import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import NativeInvented
from workshop.playtest import Feedback
from workshop.make.native import NativeMade
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    InventorRoster,
    InventorRosterEntry,
)
from workshop.playtest.native import (
    NativePlaytestCheck,
    NativePlaytested,
    score_summary,
    validate_vault_lead_answers,
)
from workshop.product import ToyBlueprint


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


LEAD_A = {"id": "a" * 16, "kind": "risk", "nodes": ["mechanisms/x", "anti-patterns/y"]}
LEAD_B = {"id": "b" * 16, "kind": "risk", "nodes": ["mechanisms/x", "anti-patterns/z"]}
FEEDBACK = [{"code": "fix-y", "severity": "improve"}]


def _check(answers=None, check_id="agent-playtest"):
    observations = {"ok": True}
    if answers is not None:
        observations["vault_leads"] = answers
    return {"check_id": check_id, "observations": observations}


def _answer(lead, verdict="dismissed", why="Not exposed here.", feedback_code=None):
    return {"lead": lead["id"], "verdict": verdict, "why": why, "feedback_code": feedback_code}


DIMS = ("wish_fit", "play")


def _read(reader, wish_fit=8, play=7, one_change="Deepen the recess."):
    return {"reader": reader, "scores": {"wish_fit": wish_fit, "play": play}, "one_change": one_change}


def _scored_checks(reads):
    return [{"check_id": "agent-playtest", "observations": {"reads": reads}}]


# (name, reads, expected summary or error pattern) — shared with the finalizer suite.
SCORE_CASES = (
    (
        "three-agree",
        _scored_checks([_read("a"), _read("b"), _read("c")]),
        {"reads": 3, "median": {"wish_fit": 8.0, "play": 7.0}, "spread": {"wish_fit": 0, "play": 0}, "one_change": ["Deepen the recess."] * 3},
    ),
    (
        "even-count-median-and-spread",
        _scored_checks([_read("a", 2, 4), _read("b", 4, 7), _read("c", 7, 7), _read("d", 9, 9)]),
        {"reads": 4, "median": {"wish_fit": 5.5, "play": 7.0}, "spread": {"wish_fit": 7, "play": 5}, "one_change": ["Deepen the recess."] * 4},
    ),
    ("no-reads-key", [{"check_id": "agent-playtest", "observations": {"ok": True}}], "carry a reads list"),
    ("no-agent-playtest", [{"check_id": "mechanical-check", "observations": {"reads": []}}], "carry a reads list"),
    ("too-few", _scored_checks([_read("a"), _read("b")]), "needs 3 to 16"),
    ("too-many", _scored_checks([_read("r%d" % i) for i in range(17)]), "needs 3 to 16"),
    ("bad-shape", _scored_checks([{"reader": "a"}, _read("b"), _read("c")]), "exactly reader, scores"),
    ("blank-reader", _scored_checks([_read(" "), _read("b"), _read("c")]), "distinct non-empty reader"),
    ("duplicate-reader", _scored_checks([_read("a"), _read("a"), _read("c")]), "distinct non-empty reader"),
    ("wrong-dimensions", _scored_checks([{"reader": "a", "scores": {"wish_fit": 8}, "one_change": "x"}, _read("b"), _read("c")]), "exactly the issued dimensions"),
    ("score-out-of-range", _scored_checks([_read("a", 11), _read("b"), _read("c")]), "outside 0..10"),
    ("score-bool", _scored_checks([_read("a", True), _read("b"), _read("c")]), "outside 0..10"),
    ("score-float", _scored_checks([_read("a", 7.5), _read("b"), _read("c")]), "outside 0..10"),
    ("blank-one-change", _scored_checks([_read("a", one_change=" "), _read("b"), _read("c")]), "non-empty one_change"),
    ("long-one-change", _scored_checks([_read("a", one_change="x" * 1001), _read("b"), _read("c")]), "non-empty one_change"),
)


# (name, leads, checks, feedback, expected result or error pattern) — shared with the
# finalizer suite so the run-local mirror and the host stay identical.
LEAD_ANSWER_CASES = (
    ("no-leads-no-answers", [], [_check()], [], {"answered": 0, "confirmed": 0, "dismissed": 0}),
    ("no-leads-empty-list", [], [_check([])], [], {"answered": 0, "confirmed": 0, "dismissed": 0}),
    ("no-leads-but-answers", [], [_check([_answer(LEAD_A)])], [], "never issued"),
    (
        "all-dismissed",
        [LEAD_A, LEAD_B],
        [_check([_answer(LEAD_A), _answer(LEAD_B)]), _check(None, "mechanical-check")],
        [],
        {"answered": 2, "confirmed": 0, "dismissed": 2},
    ),
    (
        "one-confirmed",
        [LEAD_A, LEAD_B],
        [_check([_answer(LEAD_A, "confirmed", "Seen in round 1.", "fix-y"), _answer(LEAD_B)])],
        FEEDBACK,
        {"answered": 2, "confirmed": 1, "dismissed": 1},
    ),
    ("bad-issued-id", [{"id": "nope"}], [_check([])], [], "lead id is invalid"),
    ("answers-not-list", [LEAD_A], [_check("x")], [], "must be a list"),
    ("unanswered", [LEAD_A, LEAD_B], [_check([_answer(LEAD_A)])], [], "unanswered: " + "b" * 16),
    ("missing-observation-key", [LEAD_A], [_check()], [], "unanswered"),
    ("no-agent-playtest-check", [LEAD_A], [_check([_answer(LEAD_A)], "mechanical-check")], [], "unanswered"),
    ("unknown-lead", [LEAD_A], [_check([_answer(LEAD_A), _answer(LEAD_B)])], [], "not issued"),
    ("duplicate", [LEAD_A], [_check([_answer(LEAD_A), _answer(LEAD_A)])], [], "more than once"),
    ("bad-shape", [LEAD_A], [_check([{"lead": "a" * 16}])], [], "exactly lead, verdict"),
    ("bad-verdict", [LEAD_A], [_check([_answer(LEAD_A, "maybe")])], [], "confirmed or dismissed"),
    ("blank-why", [LEAD_A], [_check([_answer(LEAD_A, why="   ")])], [], "non-empty why"),
    ("long-why", [LEAD_A], [_check([_answer(LEAD_A, why="x" * 1001)])], [], "non-empty why"),
    ("confirmed-no-code", [LEAD_A], [_check([_answer(LEAD_A, "confirmed", "Seen.")])], FEEDBACK, "existing feedback code"),
    ("confirmed-unknown-code", [LEAD_A], [_check([_answer(LEAD_A, "confirmed", "Seen.", "other")])], FEEDBACK, "existing feedback code"),
    ("dismissed-with-code", [LEAD_A], [_check([_answer(LEAD_A, feedback_code="fix-y")])], FEEDBACK, "must not name feedback"),
)


class NativePlaytestedTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_root = Path(self.temporary.name).resolve()
        self.blueprint = ToyBlueprint()
        roster = InventorRoster(
            (
                InventorRosterEntry(
                    "eve",
                    ".codex/agents/eve.toml",
                    "b" * 64,
                    "c" * 64,
                    "d" * 64,
                ),
            )
        )
        self.assignment = NativeMatchAssignment(
            wish_sha256="a" * 64,
            inventor_roster_sha256=roster.roster_sha256,
            selected_inventor_id="eve",
            selected_agent_path=".codex/agents/eve.toml",
            selected_agent_sha256="b" * 64,
            selected_source_manifest_sha256="c" * 64,
            selected_taste_sha256="d" * 64,
            blueprint_sha256=self.blueprint.sha256,
            ranking=(
                MatchRankingEntry(
                    "eve", "The Wish is a specific place made into a tiny world."
                ),
            ),
        )
        self.invented = NativeInvented(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept={"title": "Moon Nook", "summary": "A tiny lunar observatory."},
            research={
                "sources": [
                    {"url": "https://example.test/moon", "claim": "scale"}
                ]
            },
        )
        self.made = self._make_product()

    def _make_product(self) -> NativeMade:
        product_root = self.run_root / "artifacts/make/r0001/product"
        (product_root / "cad/project").mkdir(parents=True)
        (product_root / "validation").mkdir()
        product = {
            "title": "Moon Nook",
            "summary": "A tiny lunar observatory.",
        }
        product_bytes = (
            json.dumps(product, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        receipt = b'{"ok":true,"validator":"cad-final"}\n'
        (product_root / "product.json").write_bytes(product_bytes)
        (product_root / "cad/project/moon.step.py").write_text("pass\n")
        (product_root / "cad/project/moon.step").write_bytes(b"ISO-10303-21;\n")
        (product_root / "cad/project/moon.stl").write_bytes(
            b"solid moon\nendsolid moon\n"
        )
        (product_root / "validation/cad-build.json").write_bytes(receipt)
        return NativeMade(
            round=1,
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            invented_sha256=self.invented.invented_sha256,
            product_root="artifacts/make/r0001/product",
            cad_project_path="cad/project",
            product_manifest=build_artifact_manifest(
                product_root, created_at="content-addressed"
            ),
            product=product,
            product_json_sha256=_sha(product_bytes),
            cad_verification_path="validation/cad-build.json",
            cad_verification_sha256=_sha(receipt),
        )

    def _playtested(self, *, verdict="pass", failed=None) -> NativePlaytested:
        evidence_root = self.run_root / "artifacts/playtest/r0001/evidence"
        evidence_root.mkdir(parents=True, exist_ok=True)
        checks = []
        for check_id in self.blueprint.required_playtest_checks():
            content = (json.dumps({"check": check_id, "ok": check_id != failed}) + "\n").encode()
            path = "%s.json" % check_id
            (evidence_root / path).write_bytes(content)
            checks.append(
                NativePlaytestCheck(
                    check_id=check_id,
                    passed=check_id != failed,
                    evaluator="workshop-host",
                    evaluator_version="1.0.0",
                    config_sha256="d" * 64,
                    evidence_ref=path,
                    evidence_sha256=_sha(content),
                    observed_at="2026-08-26T00:00:00Z",
                    observations={"ok": check_id != failed},
                )
            )
        feedback = ()
        if failed is not None:
            feedback = (
                Feedback(
                    code="fix-%s" % failed,
                    area="playtest",
                    severity="improve",
                    finding="The check failed.",
                    change="Revise the product and rerun the check.",
                    evidence_refs=("%s.json" % failed,),
                ),
            )
        return NativePlaytested(
            round=1,
            made_sha256=self.made.made_sha256,
            product_artifact_sha256=self.made.product_manifest.artifact_sha256,
            blueprint_sha256=self.blueprint.sha256,
            evidence_root="artifacts/playtest/r0001/evidence",
            evidence_manifest=build_artifact_manifest(
                evidence_root, created_at="content-addressed"
            ),
            checks=tuple(checks),
            feedback=feedback,
            verdict=verdict,
        )

    def test_vault_lead_answers_are_validated_exactly(self):
        for name, leads, checks, feedback, expected in LEAD_ANSWER_CASES:
            with self.subTest(case=name):
                if isinstance(expected, dict):
                    self.assertEqual(validate_vault_lead_answers(leads, checks, feedback), expected)
                else:
                    with self.assertRaisesRegex(ContractError, expected):
                        validate_vault_lead_answers(leads, checks, feedback)

    def test_score_summary_cases(self):
        for name, checks, expected in SCORE_CASES:
            with self.subTest(case=name):
                if isinstance(expected, dict):
                    self.assertEqual(score_summary(DIMS, checks, minimum_reads=3), expected)
                else:
                    with self.assertRaisesRegex(ContractError, expected):
                        score_summary(DIMS, checks, minimum_reads=3)
        with self.assertRaisesRegex(ContractError, "unique and non-empty"):
            score_summary(("a", "a"), SCORE_CASES[0][1], minimum_reads=3)

    def test_contract_scores_and_floors_a_pass(self):
        with self.assertRaisesRegex(ContractError, "carry a reads list"):
            self._playtested().assert_scored(DIMS, floor=5, minimum_reads=3)
        playtested = self._playtested()
        scored = NativePlaytested(
            **{
                **{key: getattr(playtested, key) for key in (
                    "round", "made_sha256", "product_artifact_sha256", "blueprint_sha256",
                    "evidence_root", "evidence_manifest", "feedback", "verdict",
                )},
                "checks": tuple(
                    NativePlaytestCheck(
                        **{
                            **check.to_dict(),
                            "observations": {
                                **check.to_dict()["observations"],
                                "reads": [_read("a", 4, 7), _read("b", 4, 7), _read("c", 5, 8)],
                            },
                        }
                    )
                    if check.check_id == "agent-playtest"
                    else check
                    for check in playtested.checks
                ),
            }
        )
        with self.assertRaisesRegex(ContractError, "below the floor of 5: wish_fit"):
            scored.assert_scored(DIMS, floor=5, minimum_reads=3)
        summary = scored.assert_scored(DIMS, floor=4, minimum_reads=3)
        self.assertEqual(summary["median"], {"wish_fit": 4.0, "play": 7.0})

    def test_contract_answers_leads_through_its_checks_and_feedback(self):
        playtested = self._playtested()
        self.assertEqual(
            playtested.assert_vault_leads_answered([]),
            {"answered": 0, "confirmed": 0, "dismissed": 0},
        )
        with self.assertRaisesRegex(ContractError, "unanswered"):
            playtested.assert_vault_leads_answered([LEAD_A])

    def test_round_trip_covers_blueprint_and_rehashes_evidence(self):
        playtested = self._playtested()

        rebuilt = NativePlaytested.from_mapping(playtested.to_dict())
        rebuilt.assert_context(self.made, self.blueprint)
        canonical = rebuilt.validate_evidence_tree(self.run_root, self.made)

        self.assertTrue(canonical.passed)
        self.assertEqual(
            {item.playtest_id for item in canonical.evidence.results},
            set(self.blueprint.required_playtest_checks()),
        )

    def test_tamper_missing_check_and_false_pass_fail_closed(self):
        playtested = self._playtested()
        evidence = self.run_root / "artifacts/playtest/r0001/evidence/agent-playtest.json"
        evidence.write_text('{"changed":true}\n')
        with self.assertRaisesRegex(ArtifactError, "differs from its manifest"):
            playtested.validate_evidence_tree(self.run_root, self.made)

        with self.assertRaisesRegex(ContractError, "incomplete inputs"):
            NativePlaytested(
                round=1,
                made_sha256=self.made.made_sha256,
                product_artifact_sha256=self.made.product_manifest.artifact_sha256,
                blueprint_sha256=self.blueprint.sha256,
                evidence_root=playtested.evidence_root,
                evidence_manifest=playtested.evidence_manifest,
                checks=playtested.checks[:-1],
                feedback=(),
                verdict="pass",
            ).assert_context(self.made, self.blueprint)

        with self.assertRaisesRegex(ContractError, "cannot contain failures"):
            self._playtested(verdict="pass", failed="agent-playtest")

    def test_host_reads_make_targeted_feedback_but_rejects_upstream_stages(self):
        accepted = Feedback(
            code="repair-snap",
            area="make",
            severity="improve",
            finding="The snap geometry failed Playtest.",
            change="Revise the snap in the next Make attempt.",
            evidence_refs=("mechanical-check.json",),
            invalidates=("make", "playtest", "release"),
        )

        self.assertEqual(
            accepted.invalidates,
            ("make", "playtest", "release"),
        )
        with self.assertRaisesRegex(ContractError, "outside the Make repair loop"):
            Feedback(
                code="restart-invent",
                area="invent",
                severity="block",
                finding="The concept should be replaced.",
                change="Return to Invent.",
                invalidates=("invent",),
            )


if __name__ == "__main__":
    unittest.main()
