import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.errors import ContractError
from inventor_workshop.invented_game import (
    GAME_ANALYSIS_CRITERIA,
    GAME_CONTRACT_PATH,
    GAME_RULES_PATH,
    GAME_SIMULATOR_ID,
    GAME_SIMULATOR_PATH,
    GAME_SIMULATOR_SOURCE,
    GAME_SIMULATOR_VERSION,
    GAME_STYLES,
    canonical_json_bytes,
    game_simulation_plan,
    game_trace_analysis,
    game_rules_document,
    qualify_game_lane_contract,
    replay_action_trace,
    simulate_game_protocol,
    validate_game_lane_contract,
    validate_physical_binding,
)
from inventor_workshop.playtest_release import (
    CapabilityReleaseProof,
    ReleaseProofSource,
    _validate_game,
)


def game_contract():
    return {
        "schema_version": 2,
        "lane": "invented-games",
        "game_protocol": {
            "schema_version": 1,
            "protocol": "workshop.resource-game.v1",
            "players": 2,
            "resources": [
                {"resource_id": "stars", "label": "star stones", "initial": 3},
                {"resource_id": "moons", "label": "moon stones", "initial": 2},
            ],
            "actions": [
                {
                    "action_id": "gather-star",
                    "label": "Gather a star",
                    "removals": [{"resource_id": "stars", "count": 1}],
                    "points": 1,
                },
                {
                    "action_id": "gather-moon",
                    "label": "Gather a moon",
                    "removals": [{"resource_id": "moons", "count": 1}],
                    "points": 2,
                },
                {
                    "action_id": "make-eclipse",
                    "label": "Make an eclipse",
                    "removals": [
                        {"resource_id": "stars", "count": 1},
                        {"resource_id": "moons", "count": 1},
                    ],
                    "points": 4,
                },
            ],
            "ending": {
                "condition": "all-resources-empty",
                "winner": "highest-score",
                "score_tie_break": "last-actor",
            },
        },
        "simulation_gate": {
            "minimum_complete_games": 1_000,
            "fixed_seed_strategy": "artifact-sha256-plus-index",
            "player_policies": list(GAME_STYLES),
        },
    }


def _write_json(path, value):
    payload = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def game_release_fixture(root):
    product_root = root / "product"
    evidence_root = root / "evidence"
    (product_root / "game").mkdir(parents=True)
    evidence_root.mkdir()
    contract = game_contract()
    contract_path = product_root / GAME_CONTRACT_PATH
    contract_path.write_bytes(canonical_json_bytes(contract))
    binding = {
        "enabled": True,
        "resource_part_ids": [
            {
                "resource_id": "stars",
                "part_ids": ["star-1", "star-2", "star-3"],
            },
            {
                "resource_id": "moons",
                "part_ids": ["moon-1", "moon-2"],
            },
        ],
    }
    rules = game_rules_document(
        lane_contract=contract,
        physical_binding=binding,
        title="Pocket Eclipse",
        theme="Gather two kinds of night light.",
    )
    rules_path = product_root / GAME_RULES_PATH
    _write_json(rules_path, rules)
    simulator_path = product_root / GAME_SIMULATOR_PATH
    simulator_path.write_text(GAME_SIMULATOR_SOURCE, encoding="utf-8")
    product_inventory = {
        relative: hashlib.sha256((product_root / relative).read_bytes()).hexdigest()
        for relative in (GAME_CONTRACT_PATH, GAME_RULES_PATH, GAME_SIMULATOR_PATH)
    }
    artifact_sha256 = "a" * 64
    plan = game_simulation_plan(artifact_sha256, 1_000)
    games = []
    for request in plan["games"]:
        game = simulate_game_protocol(contract["game_protocol"], request)
        games.append(
            {
                **game,
                "outcome": json.dumps(
                    game["outcome"], sort_keys=True, separators=(",", ":")
                ),
            }
        )
    replayed = game_trace_analysis(
        contract["game_protocol"], games, requested_games=1_000
    )
    protocol_sha256 = hashlib.sha256(
        canonical_json_bytes(contract["game_protocol"])
    ).hexdigest()
    provenance = {
        "simulator": GAME_SIMULATOR_ID,
        "simulator_version": GAME_SIMULATOR_VERSION,
        "source_path": GAME_SIMULATOR_PATH,
        "source_sha256": product_inventory[GAME_SIMULATOR_PATH],
        "contract_path": GAME_CONTRACT_PATH,
        "contract_sha256": product_inventory[GAME_CONTRACT_PATH],
        "rules_path": GAME_RULES_PATH,
        "rules_sha256": product_inventory[GAME_RULES_PATH],
        "game_protocol_sha256": protocol_sha256,
    }
    trace_document = {
        "schema_version": 1,
        "kind": "workshop-seeded-game-traces",
        "artifact_sha256": artifact_sha256,
        "plan_sha256": hashlib.sha256(canonical_json_bytes(plan)).hexdigest(),
        "provenance": provenance,
        "games": games,
    }
    analysis_document = {
        "schema_version": 1,
        "kind": "workshop-seeded-game-release-analysis",
        "artifact_sha256": artifact_sha256,
        "protocol_binding": {
            "contract_path": GAME_CONTRACT_PATH,
            "contract_sha256": product_inventory[GAME_CONTRACT_PATH],
            "rules_path": GAME_RULES_PATH,
            "rules_sha256": product_inventory[GAME_RULES_PATH],
            "game_protocol_sha256": protocol_sha256,
        },
        "criteria": dict(GAME_ANALYSIS_CRITERIA),
        "seat_wins": replayed["seat_wins"],
        "style_wins": replayed["style_wins"],
        "forced_turns": replayed["forced_turns"],
        "measurements": replayed["measurements"],
    }
    trace_sha256 = _write_json(evidence_root / "traces.json", trace_document)
    analysis_sha256 = _write_json(
        evidence_root / "analysis.json", analysis_document
    )

    def proof(trace_digest, analysis_digest, measurements=None, simulator_digest=None):
        return CapabilityReleaseProof(
            "game-simulation",
            artifact_sha256,
            "seeded-game-analysis-proof",
            (
                ReleaseProofSource(
                    "simulator-source",
                    "product",
                    GAME_SIMULATOR_PATH,
                    simulator_digest or product_inventory[GAME_SIMULATOR_PATH],
                ),
                ReleaseProofSource(
                    "game-rules",
                    "product",
                    GAME_RULES_PATH,
                    product_inventory[GAME_RULES_PATH],
                ),
                ReleaseProofSource(
                    "invent-game-contract",
                    "product",
                    GAME_CONTRACT_PATH,
                    product_inventory[GAME_CONTRACT_PATH],
                ),
                ReleaseProofSource(
                    "game-traces", "playtest", "traces.json", trace_digest
                ),
                ReleaseProofSource(
                    "game-analysis", "playtest", "analysis.json", analysis_digest
                ),
            ),
            replayed["measurements"] if measurements is None else measurements,
        )

    return {
        "product_root": product_root,
        "evidence_root": evidence_root,
        "contract": contract,
        "plan": plan,
        "trace_document": trace_document,
        "analysis_document": analysis_document,
        "trace_sha256": trace_sha256,
        "analysis_sha256": analysis_sha256,
        "proof": proof,
    }


class InventedGameProtocolTests(unittest.TestCase):
    def test_multi_resource_rules_are_executable_and_physically_bound(self):
        contract = game_contract()
        self.assertEqual(validate_game_lane_contract(contract), contract)
        binding = {
            "enabled": True,
            "resource_part_ids": [
                {"resource_id": "stars", "part_ids": ["star-1", "star-2", "star-3"]},
                {"resource_id": "moons", "part_ids": ["moon-1", "moon-2"]},
            ],
        }
        parts = ("base", "star-1", "star-2", "star-3", "moon-1", "moon-2")
        self.assertEqual(
            validate_physical_binding(
                binding, lane_contract=contract, part_ids=parts
            ),
            binding,
        )
        rules = game_rules_document(
            lane_contract=contract,
            physical_binding=binding,
            title="Pocket Eclipse",
            theme="Gather two kinds of night light.",
        )
        self.assertEqual(rules["game_protocol"], contract["game_protocol"])
        self.assertEqual(
            rules["invent_lane_contract"]["sha256"],
            hashlib.sha256(canonical_json_bytes(contract)).hexdigest(),
        )

    def test_reachable_dead_state_is_rejected_before_make(self):
        contract = game_contract()
        contract["game_protocol"]["actions"] = [
            {
                "action_id": "take-two-stars",
                "label": "Take two stars",
                "removals": [{"resource_id": "stars", "count": 2}],
                "points": 2,
            },
            {
                "action_id": "take-two-moons",
                "label": "Take two moons",
                "removals": [{"resource_id": "moons", "count": 2}],
                "points": 2,
            },
        ]
        with self.assertRaisesRegex(ContractError, "reachable dead state"):
            validate_game_lane_contract(contract)

    def test_physical_binding_cannot_substitute_or_reuse_protocol_pieces(self):
        contract = game_contract()
        binding = {
            "enabled": True,
            "resource_part_ids": [
                {"resource_id": "stars", "part_ids": ["star-1", "star-2", "star-3"]},
                {"resource_id": "moons", "part_ids": ["star-3", "moon-2"]},
            ],
        }
        with self.assertRaisesRegex(ContractError, "cover every resource exactly once"):
            validate_physical_binding(
                binding,
                lane_contract=contract,
                part_ids=("star-1", "star-2", "star-3", "moon-2"),
            )

    def test_release_replay_rejects_an_illegal_or_substituted_action_sequence(self):
        protocol = game_contract()["game_protocol"]
        outcome = replay_action_trace(
            protocol,
            ["make-eclipse", "make-eclipse", "gather-star"],
            player_styles=("optimizing", "adversarial"),
        )
        self.assertEqual(outcome["winner"], 0)
        self.assertEqual(outcome["resources"], {"stars": 0, "moons": 0})
        with self.assertRaisesRegex(ContractError, "illegal action"):
            replay_action_trace(
                protocol,
                ["make-eclipse", "make-eclipse", "gather-moon"],
                player_styles=("optimizing", "adversarial"),
            )

    def test_pinned_interpreter_runs_1000_full_traces_from_exact_contract_bytes(self):
        contract = game_contract()
        contract_bytes = canonical_json_bytes(contract)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game_root = root / "game"
            game_root.mkdir()
            (root / GAME_CONTRACT_PATH).write_bytes(contract_bytes)
            simulator = game_root / "simulate.py"
            simulator.write_text(GAME_SIMULATOR_SOURCE, encoding="utf-8")
            request = game_simulation_plan("a" * 64, 1_000)
            request_path = root / "request.json"
            output_path = root / "output.json"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    str(simulator),
                    "--request",
                    str(request_path),
                    "--output",
                    str(output_path),
                ],
                cwd=game_root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(result["completed_games"], 1_000)
        self.assertEqual(result["contract_sha256"], hashlib.sha256(contract_bytes).hexdigest())
        self.assertEqual(len(result["games"]), 1_000)
        self.assertTrue(all(game["completed"] for game in result["games"]))
        self.assertTrue(all(len(game["action_trace"]) == game["turns"] for game in result["games"]))
        self.assertEqual(
            result["games"],
            [
                simulate_game_protocol(contract["game_protocol"], item)
                for item in request["games"]
            ],
        )
        observed_actions = {
            action_id
            for game in result["games"]
            for action_id in game["action_trace"]
        }
        self.assertEqual(
            observed_actions,
            {"gather-star", "gather-moon", "make-eclipse"},
        )

    def test_invent_qualification_rejects_weak_last_actor_and_accepts_revision(self):
        contract = game_contract()
        contract["game_protocol"] = {
            "schema_version": 1,
            "protocol": "workshop.resource-game.v1",
            "players": 2,
            "resources": [
                {"resource_id": "sparks", "label": "spark stones", "initial": 4}
            ],
            "actions": [
                {
                    "action_id": "take-one",
                    "label": "Take one",
                    "removals": [{"resource_id": "sparks", "count": 1}],
                    "points": 0,
                },
                {
                    "action_id": "take-two",
                    "label": "Take two",
                    "removals": [{"resource_id": "sparks", "count": 2}],
                    "points": 0,
                },
                {
                    "action_id": "take-three",
                    "label": "Take three",
                    "removals": [{"resource_id": "sparks", "count": 3}],
                    "points": 0,
                },
            ],
            "ending": {
                "condition": "all-resources-empty",
                "winner": "last-actor",
                "score_tie_break": "last-actor",
            },
        }
        weak = qualify_game_lane_contract(contract)
        self.assertFalse(weak["passed"])
        self.assertEqual(weak["seat_wins"]["0"], 0)
        self.assertEqual(weak["style_wins"]["optimizing"], 0)
        self.assertGreater(weak["meaningful_choice_turns"], 0)

        contract["game_protocol"]["ending"]["winner"] = "next-actor"
        revised = qualify_game_lane_contract(contract)
        self.assertTrue(revised["passed"])
        self.assertTrue(all(revised["seat_wins"].values()))
        self.assertTrue(all(revised["style_wins"].values()))
        self.assertEqual(revised["hard_tensions"], [])

    def test_release_recomputes_the_exact_artifact_seed_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = game_release_fixture(Path(temporary))
            valid = fixture["proof"](
                fixture["trace_sha256"], fixture["analysis_sha256"]
            )
            _validate_game(
                valid,
                product_root=fixture["product_root"],
                evidence_root=fixture["evidence_root"],
            )

            forged_trace = json.loads(json.dumps(fixture["trace_document"]))
            forged_plan = json.loads(json.dumps(fixture["plan"]))
            forged_request = forged_plan["games"][0]
            forged_request["seed"] += 91_337
            forged_game = simulate_game_protocol(
                fixture["contract"]["game_protocol"], forged_request
            )
            forged_trace["games"][0] = {
                **forged_game,
                "outcome": json.dumps(
                    forged_game["outcome"],
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            }
            forged_trace["plan_sha256"] = hashlib.sha256(
                canonical_json_bytes(forged_plan)
            ).hexdigest()
            forged_sha256 = _write_json(
                fixture["evidence_root"] / "traces.json", forged_trace
            )
            forged_proof = fixture["proof"](
                forged_sha256, fixture["analysis_sha256"]
            )
            with self.assertRaisesRegex(ContractError, "requested game|seeded replay"):
                _validate_game(
                    forged_proof,
                    product_root=fixture["product_root"],
                    evidence_root=fixture["evidence_root"],
                )

    def test_release_recomputes_metrics_instead_of_trusting_rehashed_analysis(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = game_release_fixture(Path(temporary))
            forged_measurements = dict(
                fixture["analysis_document"]["measurements"]
            )
            forged_measurements["choice_cases"] += 1
            forged_analysis = json.loads(
                json.dumps(fixture["analysis_document"])
            )
            forged_analysis["measurements"] = forged_measurements
            forged_analysis_sha256 = _write_json(
                fixture["evidence_root"] / "analysis.json", forged_analysis
            )
            forged_proof = fixture["proof"](
                fixture["trace_sha256"],
                forged_analysis_sha256,
                forged_measurements,
            )
            with self.assertRaisesRegex(ContractError, "measurements do not match"):
                _validate_game(
                    forged_proof,
                    product_root=fixture["product_root"],
                    evidence_root=fixture["evidence_root"],
                )

    def test_release_requires_the_canonical_simulator_path_and_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = game_release_fixture(Path(temporary))
            simulator = fixture["product_root"] / GAME_SIMULATOR_PATH
            simulator.write_text(
                GAME_SIMULATOR_SOURCE + "\n# rehashed substitute\n",
                encoding="utf-8",
            )
            substitute_sha256 = hashlib.sha256(simulator.read_bytes()).hexdigest()
            substituted = fixture["proof"](
                fixture["trace_sha256"],
                fixture["analysis_sha256"],
                simulator_digest=substitute_sha256,
            )
            with self.assertRaisesRegex(ContractError, "pinned Workshop interpreter"):
                _validate_game(
                    substituted,
                    product_root=fixture["product_root"],
                    evidence_root=fixture["evidence_root"],
                )


if __name__ == "__main__":
    unittest.main()
    game_trace_analysis,
