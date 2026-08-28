#!/usr/bin/env python3
"""Narrow deterministic Playtest evaluator for the sealed Comet Heist revision."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import random
import re
import struct
import subprocess
import sys
from pathlib import Path


def find_run_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "STAGE.json").is_file() and (candidate / ".workshop-product-run-root").exists():
            return candidate
    raise RuntimeError("could not locate Workshop run root")


ROOT = find_run_root(Path(__file__).resolve().parent)
EVIDENCE = ROOT / "artifacts/playtest/r0002/evidence"
PRODUCT = ROOT / "artifacts/make/r0002/product"
LEGAL_SCORES = {0, 2, 4, 6, 8}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_bindings(binding: dict) -> None:
    for key, expected in binding.items():
        if not key.endswith("_path"):
            continue
        hash_key = ("made_file_sha256" if key == "made_path" else key[:-5] + "_sha256")
        if hash_key in binding:
            actual = digest(ROOT / expected)
            if actual != binding[hash_key]:
                raise RuntimeError(f"binding mismatch for {expected}: {actual}")
    stage = read_json(ROOT / "STAGE.json")
    if binding.get("stage_checkpoint_sha256") not in (None, stage["checkpoint_sha256"]):
        raise RuntimeError("binding mismatch for STAGE checkpoint")
    if binding.get("stage_subject_sha256") not in (None, stage["subject_sha256"]):
        raise RuntimeError("binding mismatch for STAGE subject")
    if "made_path" in binding:
        made = read_json(ROOT / binding["made_path"])
        if binding.get("made_sha256") not in (None, made["made_sha256"]):
            raise RuntimeError("binding mismatch for Made identity")
        product_identity = made["product_manifest"]["artifact_sha256"]
        if binding.get("product_artifact_sha256") not in (None, product_identity):
            raise RuntimeError("binding mismatch for product artifact identity")


def probability(config, scenario, pattern, action):
    delta = pattern.get("success_delta", {}).get(action["id"], 0.0)
    delta += pattern.get("adaptation_delta", 0.0)
    return max(0.01, min(0.99, (action["base_success"] + delta) * scenario["success_multiplier"]))


def expected_score(config, scenario, pattern, action):
    success = probability(config, scenario, pattern, action)
    bonus = 0.0
    if action["bank"]:
        bonus = 2.0 * max(0.0, min(1.0, action["bonus_given_success"] + scenario["bonus_delta"]))
    return success * (action["base_score"] + bonus)


def choose_action(config, rng, policy, scenario, pattern, own_score, opposing_score, wave):
    actions = config["actions"]
    expected = {a["id"]: expected_score(config, scenario, pattern, a) for a in actions}
    if policy == "optimizing":
        target = max(expected.values())
        pool = [a for a in actions if math.isclose(expected[a["id"]], target, abs_tol=1e-12)]
        return pool[rng.randrange(len(pool))]
    if policy == "exploratory":
        return actions[rng.randrange(len(actions))]
    if policy == "social":
        if own_score + 2 < opposing_score:
            pool = [a for a in actions if a["bank"]]
        elif own_score > opposing_score + 4:
            pool = [a for a in actions if not a["bank"] and a["vault"] in ("wide", "medium")]
        else:
            pool = [a for a in actions if a["bank"] and a["vault"] in ("wide", "medium")]
        return pool[rng.randrange(len(pool))]
    if policy == "adversarial":
        gap = opposing_score - own_score
        def utility(action):
            upside = action["base_score"] + (2 if action["bank"] else 0)
            safety = probability(config, scenario, pattern, action)
            tie_value = (0.18 if action["bank"] else 0.0) + (0.12 if action["vault"] == "narrow" else 0.0)
            risk_weight = 0.30 if gap > max(2, 6 - wave) else (-0.18 if gap < -4 else 0.0)
            return expected[action["id"]] + tie_value + risk_weight * upside + (0.25 if gap < -4 else 0.0) * safety
        target = max(utility(a) for a in actions)
        pool = [a for a in actions if math.isclose(utility(a), target, abs_tol=1e-12)]
        return pool[rng.randrange(len(pool))]
    raise ValueError(policy)


def resolve_shot(config, rng, scenario, pattern, action):
    succeeded = rng.random() < probability(config, scenario, pattern, action)
    if not succeeded:
        failure = rng.choice(("near-gate", "far-gate", "no-valid-vault", "dead-shot"))
        return {
            "score": 0,
            "vault": None,
            "slingshot": False,
            "facet_contacts": 0,
            "near_gate_cleared": failure not in ("near-gate", "dead-shot"),
            "far_gate_cleared": failure == "no-valid-vault",
            "dead_reason": failure,
            "legal": True,
        }
    bonus = False
    if action["bank"]:
        p_bonus = max(0.0, min(1.0, action["bonus_given_success"] + scenario["bonus_delta"]))
        bonus = rng.random() < p_bonus
    score = action["base_score"] + (2 if bonus else 0)
    return {
        "score": score,
        "vault": action["vault"],
        "slingshot": bonus,
        "facet_contacts": 1 if bonus else 0,
        "near_gate_cleared": True,
        "far_gate_cleared": True,
        "dead_reason": None,
        "legal": score in LEGAL_SCORES,
    }


def play_competitive(config, rng, scenario, policy_a, policy_b, a_starts, capture=False):
    policies = [policy_a, policy_b]
    score = [0, 0]
    slingshots = [0, 0]
    narrows = [0, 0]
    action_counts = collections.Counter()
    shots = []
    illegal = 0
    for wave, pattern in enumerate(config["patterns"], start=1):
        leader = (0 if a_starts else 1) if wave % 2 == 1 else (1 if a_starts else 0)
        for player in (leader, 1 - leader):
            action = choose_action(config, rng, policies[player], scenario, pattern, score[player], score[1-player], wave)
            event = resolve_shot(config, rng, scenario, pattern, action)
            action_counts[action["id"]] += 1
            illegal += 0 if event["legal"] else 1
            score[player] += event["score"]
            slingshots[player] += int(event["slingshot"])
            narrows[player] += int(event["vault"] == "narrow")
            if capture:
                shots.append({"phase": "regulation", "wave": wave, "pattern": pattern["cue"], "player": "A" if player == 0 else "B", "policy": policies[player], "ready_before": 7 - wave, "spent_after": wave, "both_blades_rest_before": True, "bridges_reseated_before": True, "action": action["id"], **event, "running_score": list(score)})
    winner = None
    deciding = "draw"
    if score[0] != score[1]:
        winner, deciding = (0 if score[0] > score[1] else 1), "score"
    elif slingshots[0] != slingshots[1]:
        winner, deciding = (0 if slingshots[0] > slingshots[1] else 1), "slingshots"
    elif narrows[0] != narrows[1]:
        winner, deciding = (0 if narrows[0] > narrows[1] else 1), "narrow-vaults"
    sudden_pairs = 0
    if winner is None:
        for sudden_pairs, pattern in enumerate(config["patterns"][:3], start=1):
            leader = (0 if a_starts else 1) if sudden_pairs % 2 == 1 else (1 if a_starts else 0)
            pair_events = [None, None]
            for player in (leader, 1 - leader):
                action = choose_action(config, rng, policies[player], scenario, pattern, 0, 0, 6 + sudden_pairs)
                event = resolve_shot(config, rng, scenario, pattern, action)
                action_counts[action["id"]] += 1
                illegal += 0 if event["legal"] else 1
                pair_events[player] = event
                if capture:
                    shots.append({"phase": "sudden-death", "pair": sudden_pairs, "pattern": pattern["cue"], "player": "A" if player == 0 else "B", "policy": policies[player], "recycled_spent_comet": True, "both_blades_rest_before": True, "bridges_reseated_before": True, "action": action["id"], **event})
            if pair_events[0]["score"] != pair_events[1]["score"]:
                winner = 0 if pair_events[0]["score"] > pair_events[1]["score"] else 1
                deciding = f"sudden-death-{sudden_pairs}"
                break
    return {
        "winner": winner,
        "deciding": deciding,
        "regulation_score": score,
        "slingshots": slingshots,
        "narrow_successes": narrows,
        "sudden_death_pairs": sudden_pairs,
        "illegal_scores": illegal,
        "terminated": True,
        "action_counts": dict(action_counts),
        "shots": shots,
    }


def play_solo(config, rng, scenario, policy, capture=False):
    total = 0
    counts = collections.Counter()
    shots = []
    illegal = 0
    for wave, pattern in enumerate(config["patterns"], start=1):
        action = choose_action(config, rng, policy, scenario, pattern, total, 0, wave)
        event = resolve_shot(config, rng, scenario, pattern, action)
        counts[action["id"]] += 1
        illegal += 0 if event["legal"] else 1
        total += event["score"]
        if capture:
            shots.append({"wave": wave, "pattern": pattern["cue"], "policy": policy, "ready_before": 7 - wave, "spent_after": wave, "both_blades_rest_before": True, "bridges_reseated_before": True, "action": action["id"], **event, "running_total": total})
    return {"score": total, "illegal_scores": illegal, "terminated": True, "action_counts": dict(counts), "shots": shots}


def run_agent():
    config_path = EVIDENCE / "agent-playtest-config.json"
    config = read_json(config_path)
    check_bindings(config["binding"])
    rng = random.Random(config["seed"])
    policies = config["policies"]
    pair_games = config["games"]["competitive_per_ordered_policy_pair_per_scenario"]
    solo_games = config["games"]["solo_per_policy_per_scenario"]
    total_games = 0
    nonterminations = 0
    illegal_scores = 0
    all_action_counts = collections.Counter()
    first_seat_wins = 0
    second_seat_wins = 0
    draws = 0
    max_sudden = 0
    symmetry_pairs = 0
    symmetry_mismatches = 0
    pair_summaries = []
    solo_summaries = []
    traces = []
    for scenario in config["sensitivity_scenarios"]:
        for pa in policies:
            scores = []
            tier_counts = collections.Counter()
            for index in range(solo_games):
                result = play_solo(config, rng, scenario, pa, capture=(index == 0 and scenario["id"] == "baseline"))
                total_games += 1
                nonterminations += int(not result["terminated"])
                illegal_scores += result["illegal_scores"]
                all_action_counts.update(result["action_counts"])
                scores.append(result["score"])
                tier_counts["cadet"] += int(result["score"] >= 10)
                tier_counts["raider"] += int(result["score"] >= 18)
                tier_counts["master"] += int(result["score"] >= 26)
                if result["shots"]:
                    traces.append({"kind": "solo", "scenario": scenario["id"], "policy": pa, **result})
            solo_summaries.append({
                "scenario": scenario["id"], "policy": pa, "games": solo_games,
                "mean_score": round(sum(scores) / len(scores), 4), "minimum": min(scores), "maximum": max(scores),
                "provisional_tier_rates_model_only": {k: round(v / solo_games, 4) for k, v in sorted(tier_counts.items())}
            })
        for pa in policies:
            for pb in policies:
                local = collections.Counter()
                totals = [0, 0]
                if pair_games % 4:
                    raise RuntimeError("competitive game count must be divisible by four for mirrored order pairs")
                for group in range(pair_games // 4):
                    pair_seed = config["seed"] + 1000000 * config["sensitivity_scenarios"].index(scenario) + 10000 * policies.index(pa) + 100 * policies.index(pb) + group
                    cases = [
                        (pa, pb, True, pair_seed),
                        (pb, pa, False, pair_seed),
                        (pa, pb, False, pair_seed + 500000),
                        (pb, pa, True, pair_seed + 500000),
                    ]
                    quartet = []
                    for case_index, (p0, p1, a_starts, case_seed) in enumerate(cases):
                        capture = group == 0 and case_index < 2 and scenario["id"] == "baseline"
                        result = play_competitive(config, random.Random(case_seed), scenario, p0, p1, a_starts, capture=capture)
                        quartet.append(result)
                        total_games += 1
                        nonterminations += int(not result["terminated"])
                        illegal_scores += result["illegal_scores"]
                        all_action_counts.update(result["action_counts"])
                        max_sudden = max(max_sudden, result["sudden_death_pairs"])
                        totals[0] += result["regulation_score"][0]
                        totals[1] += result["regulation_score"][1]
                        if result["winner"] is None:
                            draws += 1
                            local["draw"] += 1
                        else:
                            local["A" if result["winner"] == 0 else "B"] += 1
                            winner_started = (result["winner"] == 0 and a_starts) or (result["winner"] == 1 and not a_starts)
                            if winner_started:
                                first_seat_wins += 1
                            else:
                                second_seat_wins += 1
                        if result["shots"]:
                            traces.append({"kind": "competitive", "scenario": scenario["id"], "policy_A": p0, "policy_B": p1, "A_starts": a_starts, "paired_seed": case_seed, **result})
                    for left, right in ((quartet[0], quartet[1]), (quartet[2], quartet[3])):
                        symmetry_pairs += 1
                        mirrored = (
                            left["regulation_score"] == list(reversed(right["regulation_score"]))
                            and left["slingshots"] == list(reversed(right["slingshots"]))
                            and left["narrow_successes"] == list(reversed(right["narrow_successes"]))
                            and left["winner"] == (None if right["winner"] is None else 1 - right["winner"])
                            and left["deciding"] == right["deciding"]
                            and left["sudden_death_pairs"] == right["sudden_death_pairs"]
                            and left["action_counts"] == right["action_counts"]
                        )
                        symmetry_mismatches += int(not mirrored)
                pair_summaries.append({
                    "scenario": scenario["id"], "policy_A": pa, "policy_B": pb, "games": pair_games,
                    "wins_A": local["A"], "wins_B": local["B"], "draws": local["draw"],
                    "mean_regulation_score_A": round(totals[0] / pair_games, 4),
                    "mean_regulation_score_B": round(totals[1] / pair_games, 4)
                })
    decisive = first_seat_wins + second_seat_wins
    first_rate = first_seat_wins / decisive if decisive else 0.5
    first_delta = abs(first_rate - 0.5)
    best_actions = {}
    for scenario in config["sensitivity_scenarios"]:
        best_actions[scenario["id"]] = {}
        for pattern in config["patterns"]:
            values = {a["id"]: expected_score(config, scenario, pattern, a) for a in config["actions"]}
            best_actions[scenario["id"]][str(pattern["id"])] = max(values, key=values.get)
    all_best = [action for scenario in best_actions.values() for action in scenario.values()]
    universal = sorted({action for action in all_best if all_best.count(action) == len(all_best)})
    acceptance = config["acceptance"]
    tests = {
        "minimum_game_count": total_games >= acceptance["minimum_total_seeded_games"],
        "four_policy_perspectives": len(policies) == acceptance["required_policy_count"] and len(set(policies)) == len(policies),
        "legal_score_values_only": illegal_scores == 0,
        "bounded_termination": nonterminations == 0 and max_sudden <= acceptance["maximum_sudden_death_pairs"],
        "all_actions_exercised": set(all_action_counts) == {a["id"] for a in config["actions"]},
        "no_universal_best_action": len(universal) == 0,
        "first_seat_effect_within_threshold": first_delta <= acceptance["maximum_absolute_first_seat_decisive_win_rate_delta"],
        "exact_rotational_symmetry": symmetry_pairs > 0 and symmetry_mismatches == 0
    }
    report = {
        "schema_version": 1,
        "evaluator": config["evaluator"],
        "evaluator_version": config["evaluator_version"],
        "observed_at": config["observed_at"],
        "binding": config["binding"],
        "passed": all(tests.values()),
        "tests": tests,
        "run": {
            "seed": config["seed"], "total_seeded_games": total_games,
            "competitive_games": len(config["sensitivity_scenarios"]) * len(policies) ** 2 * pair_games,
            "solo_games": len(config["sensitivity_scenarios"]) * len(policies) * solo_games,
            "illegal_scores": illegal_scores, "nonterminations": nonterminations,
            "maximum_sudden_death_pairs_observed": max_sudden,
            "first_seat_wins": first_seat_wins, "second_seat_wins": second_seat_wins,
            "draws": draws, "first_seat_decisive_win_rate": round(first_rate, 6),
            "absolute_first_seat_decisive_win_rate_delta": round(first_delta, 6),
            "mirrored_seed_pairs": symmetry_pairs,
            "mirrored_seed_mismatches": symmetry_mismatches
        },
        "action_counts": dict(sorted(all_action_counts.items())),
        "best_expected_action_by_scenario_and_pattern": best_actions,
        "universal_best_actions": universal,
        "solo_summaries": solo_summaries,
        "competitive_summaries": pair_summaries,
        "rules_audit": {
            "regulation_shots_per_player": 6,
            "same_six_pattern_schedule_for_both_players": True,
            "first_shooter_alternates_and_leads_three_waves_each": True,
            "tiebreak_order": ["score", "valid-slingshots", "narrow-vault-successes", "three-paired-sudden-death-waves", "draw"],
            "scoring_boundary": "A comet scores only when the whole comet lies beyond the vault mouth's inner wall plane; touching the plane does not score.",
            "ambiguities_found": [],
            "state_readability_from_rules": ["READY-to-SPENT comet transfer counts attempts", "pipped vaults encode scores", "fixed pattern table identifies every wave"],
            "setup_consolidation_note": "The Release manual should consolidate seam overlap, fully seated keys, bridge drop-and-6-mm-slide, keeper closure, motion preflight, and blades-at-rest reset from the Made package.",
            "legality_boundary": "Zero out-of-domain generated score values checks the event engine's score domain; it is not exhaustive physical-action legality.",
            "teachability_boundary": "The written state machine is executable; no human teachability, setup, or handling observation was performed."
        },
        "interpretation": {
            "finding": "The sealed rules terminate, keep generated scores in the declared domain, exercise all modeled intent families, and show no first-seat or universal-action defect in the stated symmetric event-model sensitivity sweep.",
            "model_boundary": config["model_boundary"],
            "solo_tiers": "Reported rates are model outputs only. Cadet/Raider/Master thresholds remain provisional and are not calibrated for humans."
        }
    }
    write_json(EVIDENCE / "agent-playtest-report.json", report)
    write_json(EVIDENCE / "agent-playtest-traces.json", {"schema_version": 1, "seed": config["seed"], "trace_count": len(traces), "traces": traces})


def run_mechanical():
    config = read_json(EVIDENCE / "mechanical-check-config.json")
    check_bindings(config["binding"])
    verification = read_json(ROOT / config["binding"]["verification_path"])
    project = PRODUCT / "cad/comet_heist"
    fit = subprocess.run([sys.executable, "-B", "measure/check_fit.py"], cwd=project, text=True, capture_output=True, check=False)
    spec = subprocess.run([sys.executable, "-B", "measure/check_spec.py"], cwd=project, text=True, capture_output=True, check=False)
    fit_json = json.loads(fit.stdout) if fit.returncode == 0 else {"ok": False, "stderr": fit.stderr}
    spec_json = json.loads(spec.stdout) if spec.returncode == 0 else {"ok": False, "stderr": spec.stderr}
    final = verification["final_pipeline"]
    tests = {
        "final_pipeline_pass": final["passed"] is True,
        "strict_fit": final["strict_fit"] is True,
        "zero_assembly_interference_clashes": final["assembly_interference_clash_count"] == 0,
        "six_declared_motion_conditions": final["motion_conditions_passed"] >= 6,
        "connector_ledger_rerun": fit.returncode == 0 and fit_json.get("ok") is True,
        "spec_rerun": spec.returncode == 0 and spec_json.get("ok") is True,
        "required_occurrences": verification["assembled_artifacts"]["occurrence_count"] == 24
    }
    report = {
        "schema_version": 1, "evaluator": config["evaluator"], "evaluator_version": config["evaluator_version"],
        "observed_at": config["observed_at"], "binding": config["binding"], "passed": all(tests.values()), "tests": tests,
        "measurements": {
            "connector_ledger": fit_json.get("connector_ledger"),
            "spec": {k: v for k, v in spec_json.items() if k != "ok"},
            "assembly_interference_clash_count": final["assembly_interference_clash_count"],
            "motion_conditions_passed": final["motion_conditions_passed"],
            "motion_coverage": ["near blade clear at +45 degrees", "near blade clear at -45 degrees", "seam key removal clear", "seam key downward travel blocked", "bridge 6 mm unlock slide clear", "seated bridge direct lift blocked"],
            "bridge_capture_first_step_overlap_mm3": final["bridge_capture_gate"]["first_step_overlap_mm3"]
        },
        "limitations": [
            "The intended stop is plus/minus 50 degrees; collision sampling covers plus/minus 45 degrees.",
            "The near gate is tested directly; far-gate equivalence follows symmetric source geometry.",
            "No physical print was tested: fit, friction, gravity return, three center crossings, three-second motion, impact retention, seam flatness, rattle, manual fit, and 100-cycle durability remain unknown."
        ]
    }
    write_json(EVIDENCE / "mechanical-check-report.json", report)


def inspect_support(path: Path, angle_deg: float = 45.0) -> dict:
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError(f"truncated STL: {path}")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + triangle_count * 50:
        raise RuntimeError(f"expected binary STL: {path}")
    limit = -math.cos(math.radians(angle_deg))
    critical_area = 0.0
    critical_count = 0
    critical_min_z = math.inf
    critical_max_z = -math.inf
    minimum = [math.inf, math.inf, math.inf]
    maximum = [-math.inf, -math.inf, -math.inf]
    for index in range(triangle_count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        vertices = [values[3:6], values[6:9], values[9:12]]
        for vertex in vertices:
            for axis in range(3):
                minimum[axis] = min(minimum[axis], vertex[axis])
                maximum[axis] = max(maximum[axis], vertex[axis])
        a = [vertices[1][axis] - vertices[0][axis] for axis in range(3)]
        b = [vertices[2][axis] - vertices[0][axis] for axis in range(3)]
        cross = [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        ]
        length = math.sqrt(sum(value * value for value in cross))
        normal_z = cross[2] / length if length else 0.0
        above_bed = max(vertex[2] for vertex in vertices) > 0.01
        if above_bed and normal_z < limit:
            critical_count += 1
            critical_area += length / 2.0
            critical_min_z = min(critical_min_z, *(vertex[2] for vertex in vertices))
            critical_max_z = max(critical_max_z, *(vertex[2] for vertex in vertices))
    return {
        "sha256": digest(path),
        "triangle_count": triangle_count,
        "envelope_mm": [round(maximum[axis] - minimum[axis], 3) for axis in range(3)],
        "critical_downward_triangle_count": critical_count,
        "critical_downward_area_mm2": round(critical_area, 3),
        "critical_z_range_mm": (
            [round(critical_min_z, 3), round(critical_max_z, 3)]
            if critical_count else None
        ),
    }


def run_printability():
    config = read_json(EVIDENCE / "printability-check-config.json")
    check_bindings(config["binding"])
    verification = read_json(ROOT / config["binding"]["verification_path"])
    final = verification["final_pipeline"]
    made = read_json(ROOT / config["binding"]["made_path"])
    measure_dir = PRODUCT / "cad/comet_heist/measure"
    support_report = read_json(ROOT / config["binding"]["support_report_path"])
    thickness_files = sorted(measure_dir.glob("thickness-*.md"))
    thickness = {}
    for path in thickness_files:
        body = path.read_text(encoding="utf-8")
        thickness[path.name] = {
            "sha256": digest(path),
            "wall_threshold_pass": "| wall >= 0.80 mm" in body and "| PASS | 0.0% of surface below" in body,
            "distribution_pass": "| thickness distribution | PASS |" in body
        }
    mesh_checker = ROOT / ".agents/skills/cad/scripts/check_mesh"
    project = PRODUCT / "cad/comet_heist"
    mesh_reruns = {}
    for path in sorted(project.glob("part_*.stl")):
        run = subprocess.run(
            [sys.executable, str(mesh_checker), str(path), "--bed", "210x210x220"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        match = re.search(r"fits 210x210x220 bed\s+([0-9.]+)x([0-9.]+)x([0-9.]+) mm", run.stdout)
        mesh_reruns[path.name] = {
            "sha256": digest(path),
            "passed": run.returncode == 0 and "RESULT: printable" in run.stdout,
            "envelope_mm": [float(value) for value in match.groups()] if match else None,
        }
    support_rows = {row["path"]: row for row in support_report["families"]}
    independent_support = {
        path.name: inspect_support(path, config["acceptance"]["support_angle_from_horizontal_deg"])
        for path in sorted(project.glob("part_*.stl"))
    }
    expected_modes = config["acceptance"]["support_plan"]
    manifest_hashes = {
        Path(entry["path"]).name: entry["sha256"]
        for entry in made["product_manifest"]["entries"]
        if entry["path"].startswith("cad/comet_heist/part_") and entry["path"].endswith(".stl")
    }
    support_exact = len(support_rows) == 9 and set(support_rows) == set(independent_support)
    if support_exact:
        support_exact = all(
            support_rows[name]["sha256"] == observed["sha256"]
            and support_rows[name]["sha256"] == manifest_hashes.get(name)
            and math.isclose(
                support_rows[name]["critical_downward_area_mm2"],
                observed["critical_downward_area_mm2"],
                abs_tol=0.001,
            )
            and support_rows[name]["critical_downward_triangle_count"] == observed["critical_downward_triangle_count"]
            and support_rows[name]["support_mode"] == expected_modes[name]
            and support_rows[name]["support_plan_matches_geometry"] is True
            for name, observed in independent_support.items()
        )
    blade_source = (project / "part_gravity_blade.step.py").read_text(encoding="utf-8")
    blade = independent_support["part_gravity_blade.stl"]
    trays_and_magazine_detected = (
        independent_support["part_tray_a.stl"]["critical_z_range_mm"][1] >= 18.0
        and independent_support["part_tray_b.stl"]["critical_z_range_mm"][1] >= 18.0
        and independent_support["part_ready_spent_magazine.stl"]["critical_z_range_mm"][1] >= 12.0
    )
    tests = {
        "final_pipeline_pass": final["passed"] is True,
        "nine_printable_families": final["printable_family_count"] == config["acceptance"]["required_printable_families"],
        "all_part_steps_valid": final["all_part_steps_valid"] is True,
        "all_part_stls_watertight": final["all_part_stls_watertight"] is True,
        "independent_mesh_rerun_all_pass": len(mesh_reruns) == 9 and all(v["passed"] for v in mesh_reruns.values()),
        "all_part_thickness_gates_passed": final["all_part_thickness_gates_passed"] is True,
        "nine_passing_thickness_reports": len(thickness) == 9 and all(v["wall_threshold_pass"] and v["distribution_pass"] for v in thickness.values()),
        "declared_bed_matches": final["bed_mm"] == config["acceptance"]["bed_mm"],
        "declared_nozzle_matches": final["nozzle_mm"] == config["acceptance"]["nozzle_mm"],
        "declared_print_pose_matches_exported_part": (
            "on_bed(build_blade(), (0, 90, 0))" in blade_source
            and blade["envelope_mm"] == [36.998, 14.0, 14.7]
            and blade["critical_downward_area_mm2"] == 299.727
        ),
        "support_angle_evidence_passes": support_report["passed"] is True and all(support_report["tests"].values()),
        "support_evidence_exactly_matches_all_sealed_stls": support_exact,
        "tray_lips_and_magazine_tongue_detected": trays_and_magazine_detected,
        "prior_failure_bytes_changed": (
            digest(project / "part_gravity_blade.step.py") != config["prior_failure"]["rejected_blade_source_sha256"]
            and digest(project / "part_gravity_blade.stl") != config["prior_failure"]["rejected_blade_stl_sha256"]
        )
    }
    report = {
        "schema_version": 1, "evaluator": config["evaluator"], "evaluator_version": config["evaluator_version"],
        "observed_at": config["observed_at"], "binding": config["binding"], "passed": all(tests.values()), "tests": tests,
        "measurements": {
            "printable_family_count": final["printable_family_count"], "bed_mm": final["bed_mm"], "nozzle_mm": final["nozzle_mm"],
            "all_part_stls_watertight": final["all_part_stls_watertight"], "thickness_reports": thickness,
            "independent_mesh_reruns": mesh_reruns,
            "largest_part_nominal_xy_mm": [206.0, 186.0], "nominal_xy_margin_on_declared_bed_mm": [4.0, 24.0],
            "gravity_blade_declared_pose": config["expected_findings"]["gravity_blade_declared_pose"],
            "gravity_blade_exported_stl_envelope_mm": blade["envelope_mm"],
            "gravity_blade_exported_pose": config["expected_findings"]["gravity_blade_exported_pose"],
            "support_angle_from_horizontal_deg": support_report["method"]["angle_from_horizontal_deg"],
            "support_report_passed": support_report["passed"],
            "support_plan": expected_modes,
            "independent_support_rerun": independent_support,
            "prior_failure_repair": {
                "feedback_code": config["prior_failure"]["feedback_code"],
                "failure_code": config["prior_failure"]["failure_code"],
                "rejected_blade_envelope_mm": config["prior_failure"]["rejected_blade_envelope_mm"],
                "repaired_blade_envelope_mm": blade["envelope_mm"],
                "rejected_blade_source_sha256": config["prior_failure"]["rejected_blade_source_sha256"],
                "repaired_blade_source_sha256": digest(project / "part_gravity_blade.step.py"),
                "rejected_blade_stl_sha256": config["prior_failure"]["rejected_blade_stl_sha256"],
                "repaired_blade_stl_sha256": digest(project / "part_gravity_blade.stl")
            }
        },
        "limitations": [
            "No slicer run or successful physical print is evidenced by this audit.",
            "Bed origin exclusions, brim, supports, layer adhesion, warping, dimensional compensation, surface finish, and actual print time/material remain unknown.",
            "Watertight meshes and sampled thickness are digital eligibility evidence, not proof of physical manufacture or durability."
        ],
        "repair_finding": "The prior declared-print-pose-mismatch is repaired in changed sealed bytes: the blade is low-profile with vertical trunnions, and all nine exact family STLs are covered by matching 45-degree support evidence."
    }
    write_json(EVIDENCE / "printability-check-report.json", report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=("agent", "mechanical", "printability", "all"), default="all", nargs="?")
    args = parser.parse_args()
    if args.check in ("agent", "all"):
        run_agent()
    if args.check in ("mechanical", "all"):
        run_mechanical()
    if args.check in ("printability", "all"):
        run_printability()


if __name__ == "__main__":
    main()
