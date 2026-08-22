"""Tests for harness/reward.py — the frozen evaluator core.

These tests pin the CONTRACT (gate semantics, weights summing to 100,
the 70/40% publish bar) so that any drift in reward.py fails loudly in
CI as well as in the integrity hash check.
"""

import unittest

from harness import reward


class TestHardGates(unittest.TestCase):
    def all_pass_evidence(self):
        return {
            "lint_pass": True,
            "lane": "invention",
            "sim_report": {"integrity_pass": True, "degeneracy_pass": True},
            "novelty_verdict": {"pass": True, "evidence_url": None},
            "safety_pass": True,
            "build_gate": True,
        }

    def test_empty_evidence_seeds_fail_except_build(self):
        # Absent verdict = FAIL (one-way-newsreel lesson) — except g6,
        # where absent means "no parts yet" and the gate is vacuous.
        gates = reward.hard_gates({})
        self.assertEqual(set(gates), set(reward.HARD_GATES))
        for gid in ("g1_completeness", "g2_sim_integrity", "g3_degeneracy",
                    "g4_novelty", "g5_safety"):
            self.assertFalse(gates[gid], gid)
        self.assertTrue(gates["g6_buildable"])

    def test_all_pass(self):
        gates = reward.hard_gates(self.all_pass_evidence())
        self.assertTrue(all(gates.values()), gates)

    def test_sim_report_booleans(self):
        ev = self.all_pass_evidence()
        ev["sim_report"] = {"integrity_pass": True, "degeneracy_pass": False}
        gates = reward.hard_gates(ev)
        self.assertTrue(gates["g2_sim_integrity"])
        self.assertFalse(gates["g3_degeneracy"])
        # Non-boolean truthiness must not pass a gate.
        ev["sim_report"] = {"integrity_pass": "yes", "degeneracy_pass": 1}
        gates = reward.hard_gates(ev)
        self.assertFalse(gates["g2_sim_integrity"])
        self.assertFalse(gates["g3_degeneracy"])

    def test_edition_lane_skips_sim_gates(self):
        # The classic proved itself over centuries: no engine, no sim,
        # g2/g3 must not be able to block an edition.
        gates = reward.hard_gates({"lane": "edition"})
        self.assertTrue(gates["g2_sim_integrity"])
        self.assertTrue(gates["g3_degeneracy"])
        # Other gates still seeded FAIL for editions.
        self.assertFalse(gates["g1_completeness"])
        self.assertFalse(gates["g4_novelty"])

    def test_novelty_verdict(self):
        gates = reward.hard_gates({"novelty_verdict": {"pass": True}})
        self.assertTrue(gates["g4_novelty"])
        gates = reward.hard_gates(
            {"novelty_verdict": {"pass": False,
                                 "evidence_url": "https://boardgamegeek.com/x"}})
        self.assertFalse(gates["g4_novelty"])
        gates = reward.hard_gates({"novelty_verdict": "looks fine"})
        self.assertFalse(gates["g4_novelty"])

    def test_build_gate_tristate(self):
        self.assertTrue(reward.hard_gates({"build_gate": None})["g6_buildable"])
        self.assertTrue(reward.hard_gates({})["g6_buildable"])
        self.assertFalse(reward.hard_gates({"build_gate": False})["g6_buildable"])
        self.assertTrue(reward.hard_gates({"build_gate": True})["g6_buildable"])

    def test_non_dict_evidence_refused(self):
        with self.assertRaises(ValueError):
            reward.hard_gates(None)


class TestScore(unittest.TestCase):
    def test_weights_sum_to_100_both_lanes(self):
        for lane, w in reward.WEIGHTS.items():
            self.assertAlmostEqual(sum(w.values()), 100.0, msg=lane)

    def test_full_marks(self):
        full = dict(reward.WEIGHTS["invention"])
        self.assertAlmostEqual(reward.score(full), 100.0)
        full_e = dict(reward.WEIGHTS["edition"])
        self.assertAlmostEqual(reward.score(full_e, lane="edition"), 100.0)

    def test_clamping(self):
        # Over-max is a judge bug: clamp, never let one lens buy the bar.
        self.assertAlmostEqual(
            reward.score({"fun_sim": 999.0, "physical_hook": -5.0}), 20.0)

    def test_missing_keys_are_zero(self):
        self.assertAlmostEqual(reward.score({}), 0.0)
        self.assertAlmostEqual(reward.score({"clarity": 10.0}), 10.0)

    def test_unknown_key_refused(self):
        with self.assertRaises(ValueError) as ctx:
            reward.score({"fun_sim": 5.0, "vibes": 99.0})
        self.assertIn("vibes", str(ctx.exception))

    def test_unknown_lane_refused(self):
        with self.assertRaises(ValueError):
            reward.score({}, lane="moonshot")

    def test_edition_reweights(self):
        # fun_sim/depth carry zero weight in the edition lane.
        self.assertAlmostEqual(
            reward.score({"fun_sim": 20.0, "depth": 15.0}, lane="edition"), 0.0)
        self.assertAlmostEqual(
            reward.score({"physical_hook": 35.0, "novelty_margin": 30.0},
                         lane="edition"), 65.0)


class TestPublishEligible(unittest.TestCase):
    def all_gates(self, value=True):
        return {gid: value for gid in reward.HARD_GATES}

    def test_exactly_at_bar(self):
        # Every component at 70% of max sums to exactly 70.0 — and >= is
        # the contract ("R >= 70"), so exactly-70 publishes.
        comps = {k: 0.7 * w for k, w in reward.WEIGHTS["invention"].items()}
        self.assertAlmostEqual(reward.score(comps), 70.0)
        self.assertTrue(reward.publish_eligible(self.all_gates(), comps))

    def test_just_below_threshold(self):
        comps = {k: 0.7 * w for k, w in reward.WEIGHTS["invention"].items()}
        comps["fun_sim"] -= 0.01
        self.assertFalse(reward.publish_eligible(self.all_gates(), comps))

    def test_component_floor_exactly_40pct(self):
        # One component at exactly 40%, the rest maxed: eligible (>=).
        comps = dict(reward.WEIGHTS["invention"])
        comps["fun_sim"] = 0.4 * reward.WEIGHTS["invention"]["fun_sim"]
        self.assertTrue(reward.publish_eligible(self.all_gates(), comps))

    def test_component_below_floor_blocks_despite_high_score(self):
        # 87.9 total but fun_sim under 40% of its max: no component may
        # buy its way past another.
        comps = dict(reward.WEIGHTS["invention"])
        comps["fun_sim"] = 7.9  # floor is 8.0
        self.assertGreater(reward.score(comps), reward.PUBLISH_THRESHOLD)
        self.assertFalse(reward.publish_eligible(self.all_gates(), comps))

    def test_any_failed_gate_blocks(self):
        comps = dict(reward.WEIGHTS["invention"])  # perfect 100
        for gid in reward.HARD_GATES:
            gates = self.all_gates()
            gates[gid] = False
            self.assertFalse(reward.publish_eligible(gates, comps), gid)

    def test_missing_gate_counts_as_fail(self):
        comps = dict(reward.WEIGHTS["invention"])
        gates = self.all_gates()
        del gates["g4_novelty"]
        self.assertFalse(reward.publish_eligible(gates, comps))

    def test_edition_zero_weight_components_exempt_from_floor(self):
        # Edition lane: fun_sim/depth have max 0 — absent is fine.
        comps = {"fun_table": 15.0, "clarity": 20.0,
                 "novelty_margin": 30.0, "physical_hook": 35.0}
        self.assertTrue(
            reward.publish_eligible(self.all_gates(), comps, lane="edition"))

    def test_constants(self):
        self.assertEqual(reward.PUBLISH_THRESHOLD, 70.0)
        self.assertEqual(reward.MIN_COMPONENT_FRACTION, 0.4)
        self.assertEqual(reward.MIN_DELTA, 2.0)
        self.assertEqual(len(reward.HARD_GATES), 6)


if __name__ == "__main__":
    unittest.main()
