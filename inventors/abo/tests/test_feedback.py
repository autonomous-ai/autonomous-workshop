"""Findings become feedback: the severity rule, and where each finding goes.

Design decision D6. A defect in how the game functions, or a failed
manufacturing measurement, blocks. An ambiguity or an incompleteness in the
rules is an improvement. Both send the game back through the loop; only the
wording of the fix differs, and only one of them sends the *design* back.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

INVENTOR_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = INVENTOR_ROOT.parents[1]
for candidate in (INVENTOR_ROOT, WORKSHOP_ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import feedback as FB  # noqa: E402
import manufacturing as MF  # noqa: E402
from inventor_workshop.jobs import Feedback  # noqa: E402


DOMINANT_LINE = {
    "findings": [],
    "seat_advantage": {"best_seat": 0, "best_seat_rate": 0.62, "edge": 0.08},
    "skill_ladder": [
        {"rung": "optimizing-vs-greedy", "win_rate": 0.30, "edge": -0.12, "games": 20}
    ],
    "assumption_readings": [],
}

SILENT_RULE = {
    "findings": [
        "assumptions: locked-socket-counts changed the outcome (worst delta "
        "0.1500 under the baseline policy); rule win[1] has to say which "
        "reading is meant",
    ],
    "seat_advantage": {},
    "skill_ladder": [],
    "assumption_readings": [{"id": "locked-socket-counts", "rule": "win[1]"}],
}


class SeverityTest(unittest.TestCase):
    def test_a_dominant_line_blocks_and_names_the_rule(self):
        found = FB.simulation_feedback(DOMINANT_LINE)
        seat = next(item for item in found if item.code == "sim-seat-advantage")
        self.assertEqual(seat.severity, "block")
        self.assertEqual(seat.area, FB.AREA_GAME)
        self.assertIn("win[1]", seat.finding)
        self.assertTrue(seat.change.strip())

    def test_a_shallow_position_blocks_and_names_the_rule(self):
        found = FB.simulation_feedback(DOMINANT_LINE)
        ladder = next(item for item in found if item.code == "sim-skill-ladder")
        self.assertEqual(ladder.severity, "block")
        self.assertIn("win[1]", ladder.finding)
        self.assertIn("another action type", ladder.change)

    def test_a_rules_ambiguity_is_an_improvement_and_still_returns_the_game(self):
        found = FB.simulation_feedback(SILENT_RULE)
        entry = found[0]
        self.assertEqual(entry.severity, "improve")
        self.assertEqual(entry.area, FB.AREA_RULES)
        # It still sends the game back through the loop.
        self.assertIn("concept", entry.invalidates)
        self.assertIn("win[1]", entry.finding)

    def test_a_fake_decision_blocks(self):
        evidence = {
            "findings": [
                "contract: declared move kind 'spend_lock' was legal but never "
                "chosen by any style; a choice nobody takes is not a choice"
            ],
            "seat_advantage": {},
            "skill_ladder": [],
        }
        entry = FB.simulation_feedback(evidence)[0]
        self.assertEqual(entry.severity, "block")
        self.assertEqual(entry.area, FB.AREA_GAME)

    def test_non_termination_blocks(self):
        evidence = {
            "findings": [
                "termination: 4 game(s) did not reach a terminal state within 40 turns"
            ],
            "seat_advantage": {},
            "skill_ladder": [],
        }
        entry = FB.simulation_feedback(evidence)[0]
        self.assertEqual(entry.severity, "block")
        self.assertIn("end[1]", entry.change)

    def test_a_failed_manufacturing_measurement_blocks(self):
        evidence = {
            "checks": [
                {"check": "bed-fit", "status": MF.FAILED,
                 "detail": "exceeds the usable envelope", "values": {},
                 "parts": ["board-frame"]}
            ]
        }
        entry = FB.manufacturing_feedback("print-test", evidence)[0]
        self.assertEqual(entry.severity, "block")
        self.assertEqual(entry.area, FB.AREA_MANUFACTURING)
        self.assertIn("board-frame", entry.finding)
        self.assertIn("tiled", entry.change)

    def test_an_unmeasured_check_is_an_improvement(self):
        evidence = {
            "checks": [
                {"check": "slicing-under-a-pinned-profile", "status": MF.UNMEASURED,
                 "detail": "no profile pinned", "values": {}, "parts": []}
            ]
        }
        entry = FB.manufacturing_feedback("print-test", evidence)[0]
        self.assertEqual(entry.severity, "improve")
        self.assertIn("never counts as a pass", entry.change)


class RoutingTest(unittest.TestCase):
    def test_a_design_fault_is_answered_in_the_design(self):
        found = FB.simulation_feedback(DOMINANT_LINE)
        design = FB.design_feedback(found)
        self.assertTrue(design)
        for item in design:
            self.assertIn("concept", item.invalidates)
            self.assertIn(item.area, FB.DESIGN_AREAS)

    def test_a_geometry_fault_leaves_the_design_standing(self):
        evidence = {
            "checks": [
                {"check": "bed-fit", "status": MF.FAILED, "detail": "too big",
                 "values": {}, "parts": ["board-frame"]}
            ]
        }
        found = FB.manufacturing_feedback("print-test", evidence)
        # Redrawing the concept for a geometry fault would be the drift the
        # loop exists to prevent.
        self.assertEqual(FB.design_feedback(found), ())
        self.assertEqual(len(FB.build_feedback(found)), 1)
        self.assertNotIn("concept", found[0].invalidates)
        self.assertIn("make", found[0].invalidates)


class FindingShapeTest(unittest.TestCase):
    def test_every_finding_names_area_evidence_severity_and_a_change(self):
        found = FB.collect(
            simulation_evidence=DOMINANT_LINE,
            seat_evidence={
                "seat_reports": [
                    "decision-free turns: 12 of 40 turns were reported by the "
                    "seat taking them as forced, arbitrary, or obvious"
                ]
            },
            manufacturing_evidence={
                "print-test": {
                    "checks": [
                        {"check": "bed-fit", "status": MF.FAILED, "detail": "too big",
                         "values": {}, "parts": ["board-frame"]}
                    ]
                }
            },
        )
        self.assertTrue(found)
        for item in found:
            self.assertIsInstance(item, Feedback)
            self.assertTrue(item.area.strip())
            self.assertTrue(item.finding.strip())
            self.assertTrue(item.change.strip())
            self.assertIn(item.severity, ("note", "improve", "block"))
            self.assertTrue(item.evidence_refs)

    def test_a_finding_about_the_game_names_the_rule_it_is_about(self):
        found = FB.collect(simulation_evidence=DOMINANT_LINE)
        for item in found:
            if item.area in FB.DESIGN_AREAS:
                self.assertTrue(
                    FB.rule_named_in(item.finding),
                    "a finding addressed to the game must name its rule: %s"
                    % item.finding,
                )

    def test_codes_are_unique_so_one_round_carries_them_all(self):
        found = FB.collect(
            simulation_evidence=DOMINANT_LINE,
            manufacturing_evidence={
                "print-test": {
                    "checks": [
                        {"check": "bed-fit", "status": MF.FAILED, "detail": "a",
                         "values": {}, "parts": []},
                        {"check": "overhang-and-bridging", "status": MF.FAILED,
                         "detail": "b", "values": {}, "parts": []},
                    ]
                },
                "mechanical-test": {
                    "checks": [
                        {"check": "solid-validity", "status": MF.FAILED, "detail": "c",
                         "values": {}, "parts": []}
                    ]
                },
            },
        )
        codes = [item.code for item in found]
        self.assertEqual(len(codes), len(set(codes)))


class SeatReportTest(unittest.TestCase):
    def test_a_seat_report_is_a_finding_about_the_game(self):
        found = FB.seat_feedback(
            {
                "seat_reports": [
                    "the game got smaller: seat 0 reported at turn 6 — you can "
                    "see the whole run after three placements"
                ]
            }
        )
        entry = found[0]
        self.assertEqual(entry.area, FB.AREA_GAME)
        self.assertEqual(entry.severity, "block")
        self.assertIn("depth", entry.change)

    def test_a_rules_question_from_a_seat_is_an_improvement(self):
        found = FB.seat_feedback(
            {"seat_reports": ["rules question raised in play: seat 1 at turn 4 — may I lock twice?"]}
        )
        self.assertEqual(found[0].severity, "improve")
        self.assertEqual(found[0].area, FB.AREA_RULES)

    def test_no_seat_report_becomes_a_claim_about_enjoyment(self):
        found = FB.seat_feedback(
            {"seat_reports": ["decision-free turns: 12 of 40 turns held no decision"]}
        )
        for item in found:
            for word in ("enjoy", "fun", "boring", "liked"):
                self.assertNotIn(word, item.finding.casefold())


class BudgetTest(unittest.TestCase):
    """`playtest_rounds` is the only budget: D6 keeps no other counter."""

    def test_no_repair_rework_or_clarification_counter_survives(self):
        import inspect

        for module_name in ("feedback", "playtest_job", "simulation", "manufacturing"):
            module = __import__(module_name)
            source = inspect.getsource(module)
            for banned in ("repair_budget", "rework_budget", "clarify_budget",
                           "REPAIR_BUDGET", "REWORK_BUDGET", "CLARIFY_BUDGET"):
                self.assertNotIn(banned, source, "%s in %s" % (banned, module_name))

    def test_the_only_severities_are_the_workshops_own(self):
        found = FB.collect(simulation_evidence=DOMINANT_LINE)
        for item in found:
            # Not `clarify` and not `rework`: the upstream disposition survives
            # as severity and area, and nothing else came across.
            self.assertIn(item.severity, ("note", "improve", "block"))


if __name__ == "__main__":
    unittest.main()
