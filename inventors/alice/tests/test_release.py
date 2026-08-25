import copy
import hashlib
import unittest
from unittest.mock import patch

from inventor_workshop.pack import pack_artifact as workshop_pack_artifact

from alice.fulfillment import (
    build_manufacturing_spec_from_manifest,
    manufacturing_spec_from_manifest,
)
from alice.release import (
    ArtifactSnapshot,
    ReleaseAssemblyError,
    assess_release,
    build_publication_packet,
    canonical_sha256,
    compute_rules_pdf_sha256,
    validate_blind_kit,
    validate_distinct_manufacturing_receipts,
    validate_manufacturing_receipt,
    validate_production_manifest,
)
from alice.loops import validate_output_semantics


SCORES = {
    "fun_replay": 0.85,
    "clarity": 0.82,
    "depth": 0.80,
    "balance": 0.78,
    "novelty": 0.80,
    "physical_delight_print_yield": 0.82,
    "economics_market": 0.81,
}


def artifact(action, evidence_class, content, *, version=3):
    return ArtifactSnapshot(
        action=action,
        task_id=f"task-{action}",
        candidate_version=version,
        output_sha256=canonical_sha256({"result": content}),
        content_sha256=canonical_sha256(content),
        executor="adapter",
        evidence_class=evidence_class,
        content=content,
    )


def manufacturing_receipt(
    content,
    *,
    job_id,
    run_id,
    sample_count,
    defect_count,
    authority="factory.example",
):
    manifest = content.get("production_manifest")
    if isinstance(manifest, dict):
        manufacturing_spec = manufacturing_spec_from_manifest(manifest)
    else:
        manufacturing_spec = {
            "print_profile_sha256": "b" * 64,
            "material_spec_sha256": "d" * 64,
            "manufacturing_spec_sha256": "e" * 64,
        }
    receipt = {
        "receipt_source": "authenticated_manufacturing_readback",
        "authority": authority,
        "action": content["original_operation"],
        "operation_key": content["effect_operation_key"],
        "task_input_sha256": content["task_input_sha256"],
        "job_id": job_id,
        "run_id": run_id,
        "status": "completed",
        "machine_id": "printer-7",
        "material_lot": "pla-lot-42",
        "profile_sha256": manufacturing_spec["print_profile_sha256"],
        "material_spec_sha256": manufacturing_spec["material_spec_sha256"],
        "manufacturing_spec_sha256": manufacturing_spec[
            "manufacturing_spec_sha256"
        ],
        "sample_count": sample_count,
        "defect_count": defect_count,
        "measured_yield": (sample_count - defect_count) / sample_count,
        "candidate_content_sha256": content["candidate_content_sha256"],
        "rules_sha256": content["rules_sha256"],
        "rules_file_sha256": content["rules_file_sha256"],
        "project_sha256": content["project_sha256"],
        "artifact_hashes": dict(content["artifact_hashes"]),
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    return receipt


def rehash_receipt(receipt):
    result = dict(receipt)
    result.pop("receipt_sha256", None)
    result["receipt_sha256"] = canonical_sha256(result)
    return result


def bind_manufacturing_spec(manifest):
    spec = build_manufacturing_spec_from_manifest(manifest)
    manufacturing = dict(manifest["manufacturing"])
    manufacturing["material_spec_sha256"] = spec["material_spec_sha256"]
    manufacturing["manufacturing_spec_sha256"] = spec[
        "manufacturing_spec_sha256"
    ]
    manifest["manufacturing"] = manufacturing
    return spec


def release_artifacts():
    candidate_hash = "c" * 64
    rules_markdown = "# River Council Rules\n\nBuild routes and score them.\n"
    rules_document = {
        "setup": {"pieces": 12},
        "turn": {"steps": ["place", "score"]},
        "legal_actions": [{"action": "place"}],
        "end": {"rounds": 8},
        "scoring": {"route": 1},
        "ties": {"breaker": "fewest pieces"},
        "rules_markdown": rules_markdown,
    }
    rules_hash = canonical_sha256(rules_document)
    rules_file_hash = "f" * 64
    project_hash = "d" * 64
    artifact_hashes = {"game.stl": "e" * 64, "RULES.md": rules_file_hash}
    pdf_bytes = b"%PDF-1.7 exact River Council rules\n"
    pdf_bytes_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    rules_pdf_readback = {
        "receipt_source": "authenticated_artifact_readback",
        "authority": "external-playtest-lab",
        "artifact_id": "rules-pdf-game-1-v1",
        "media_type": "application/pdf",
        "byte_count": len(pdf_bytes),
        "pdf_bytes_sha256": pdf_bytes_sha256,
        "source_rules_sha256": rules_hash,
    }
    blind_kit = {
        "rules_pdf_readback": rules_pdf_readback,
        "rules_pdf_sha256": compute_rules_pdf_sha256(
            pdf_bytes_sha256=pdf_bytes_sha256,
            source_rules_sha256=rules_hash,
            byte_count=len(pdf_bytes),
        ),
        "observation_sheet": {"version": 1},
        "preregistered_measures": ["teach_without_help", "replay_choice"],
    }
    blind_kit_hash = canonical_sha256(blind_kit)
    group_ids = ["group-a", "group-b", "group-c"]
    consent_provenance = [
        {
            "consent_id": f"consent-{index}",
            "basis": "documented_informed_consent",
            "recorded_at": f"2026-08-{index + 1:02d}T10:00:00Z",
            "custodian": "external-playtest-lab",
        }
        for index in range(1, 7)
    ]
    trial_ids = [f"t{index}" for index in range(1, 7)]
    trial_provenance = [
        {
            "trial_id": trial_id,
            "group_id": group_ids[(index - 1) // 2],
            "consent_id": f"consent-{index}",
            "facilitator_id": f"facilitator-{(index - 1) // 2 + 1}",
            "external_receipt_id": f"blind-receipt-{index}",
            "candidate_content_sha256": candidate_hash,
            "rules_sha256": rules_hash,
            "blind_kit_sha256": blind_kit_hash,
        }
        for index, trial_id in enumerate(trial_ids, 1)
    ]
    simulation_contents = {
        "simulation.optimizer": {
            "candidate_content_sha256": candidate_hash,
            "rules_sha256": rules_hash,
            "seed": 617,
            "games": 100,
            "policies": ["minimax", "mcts"],
            "win_rates": {"minimax": 0.51, "mcts": 0.49},
            "dominant_strategy": False,
            "traces": ["optimizer-trace-1"],
        },
        "simulation.social": {
            "candidate_content_sha256": candidate_hash,
            "rules_sha256": rules_hash,
            "seed": 618,
            "games": 100,
            "policies": ["cooperative", "adversarial"],
            "kingmaking": False,
            "spite_loops": False,
            "traces": ["social-trace-1"],
        },
        "simulation.explorer": {
            "candidate_content_sha256": candidate_hash,
            "rules_sha256": rules_hash,
            "seed": 619,
            "games": 100,
            "edge_cases": [],
            "state_coverage": 0.82,
            "traces": ["explorer-trace-1"],
        },
        "simulation.exploit": {
            "candidate_content_sha256": candidate_hash,
            "rules_sha256": rules_hash,
            "seed": 620,
            "games": 100,
            "critical_exploits": 0,
            "traces": ["exploit-trace-1"],
        },
    }
    human_evidence = {
        "source": "blind_human",
        "scores": SCORES,
        "sample_size": 6,
        "confidence": 0.9,
        "evidence_id": "blind-tables-1",
        "verified": True,
        "surrogate": False,
        "same_model": False,
        "same_model_surrogate": False,
        "evaluator_id": "external-playtest-lab",
        "candidate_model_id": "alice-inventor-model",
    }
    manufacturing_evidence = {
        "source": "manufacturing",
        "scores": SCORES,
        "sample_size": 3,
        "confidence": 0.9,
        "evidence_id": "production-1",
        "verified": True,
        "surrogate": False,
        "same_model": False,
        "same_model_surrogate": False,
        "evaluator_id": "factory-qms",
        "candidate_model_id": "alice-inventor-model",
    }
    market_evidence = {
        "source": "market",
        "scores": SCORES,
        "sample_size": 3,
        "confidence": 0.9,
        "evidence_id": "market-1",
        "verified": True,
        "surrogate": False,
        "same_model": False,
        "same_model_surrogate": False,
        "evaluator_id": "factory-market-readback",
        "candidate_model_id": "alice-inventor-model",
    }
    prototype_content = {
        "candidate_content_sha256": candidate_hash,
        "rules_sha256": rules_hash,
        "rules_file_sha256": rules_file_hash,
        "project_sha256": project_hash,
        "artifact_hashes": artifact_hashes,
        "original_operation": "physical.prototype_print",
        "effect_operation_key": "alice:prototype:game-1:v4",
        "task_input_sha256": "1" * 64,
    }
    prototype_content["receipt"] = manufacturing_receipt(
        prototype_content,
        job_id="prototype-job-1",
        run_id="prototype-run-1",
        sample_count=10,
        defect_count=0,
    )
    production_manifest = {
        "candidate_id": "game-1",
        "candidate_version": 4,
        "candidate_content_sha256": candidate_hash,
        "rules_sha256": rules_hash,
        "customer": {
            "title": "River Council",
            "description": "A complete route-building strategy game for the table.",
            "player_count": {"min": 2, "max": 4},
            "play_time_minutes": {"min": 30, "max": 60},
            "age_min": 12,
            "whats_in_box": ["12 printed route pieces", "Rules"],
        },
        "rules": {
            "rules_sha256": rules_hash,
            "rules_file_sha256": rules_file_hash,
            "rules_markdown": rules_markdown,
        },
        "bom": [
            {
                "part_id": "route-piece-set",
                "name": "Route pieces",
                "quantity": 12,
                "material": "PLA",
                "manufacturing_method": "3d_print",
                "artifact_path": "game.stl",
            }
        ],
        "manufacturing": {
            "process": "3d_print",
            "landed_cost_cents": 4000,
            "print_profile_sha256": "b" * 64,
            "materials": ["PLA"],
            "packing": {"format": "recyclable carton", "component_count": 12},
            "vibe_design": {
                "design_id": "design-1",
                "slug": "river-council",
                "history_id": "history-1",
                "project_url": "https://cdn.example/project/",
                "project_sha256": project_hash,
                "rules_sha256": rules_hash,
                "rules_file_sha256": rules_file_hash,
                "artifact_hashes": artifact_hashes,
            }
        },
        "evidence": {
            "blind_human": {
                "evidence_id": human_evidence["evidence_id"],
                "sample_size": len(trial_ids),
                "blind_kit_sha256": blind_kit_hash,
                "trial_ids_sha256": canonical_sha256(trial_ids),
                "group_ids_sha256": canonical_sha256(group_ids),
                "consent_provenance_sha256": canonical_sha256(consent_provenance),
                "trial_provenance_sha256": canonical_sha256(trial_provenance),
            },
            "simulation": {
                "artifact_content_sha256": {
                    action: canonical_sha256(content)
                    for action, content in simulation_contents.items()
                }
            },
            "prototype": {
                "receipt_sha256": prototype_content["receipt"]["receipt_sha256"]
            },
        },
        "disclosures": [
            "Made to order with visible 3D-print layer lines.",
            "Contains small parts; not for children under 3.",
        ],
        "price": {"price_cents": 9999, "currency": "USD"},
        "listing": {"sku": "ALICE-RIVER-001"},
    }
    bind_manufacturing_spec(production_manifest)
    packet_hash = canonical_sha256(production_manifest)
    production_content = {
        "production_manifest": production_manifest,
        "candidate_content_sha256": candidate_hash,
        "rules_sha256": rules_hash,
        "rules_file_sha256": rules_file_hash,
        "project_sha256": project_hash,
        "artifact_hashes": artifact_hashes,
        "original_operation": "physical.production_run",
        "effect_operation_key": "alice:production:game-1:v4",
        "task_input_sha256": "2" * 64,
        "production_packet_hash": packet_hash,
        "reviewed_packet_hash": packet_hash,
        "print_yield": 0.97,
        "landed_cost": 40.0,
        "landed_cost_cents": 4000,
        "reward_evidence": [manufacturing_evidence],
    }
    production_content["receipt"] = manufacturing_receipt(
        production_content,
        job_id="production-job-1",
        run_id="production-run-1",
        sample_count=100,
        defect_count=3,
    )
    return [
        artifact(
            "candidate.rules",
            "same_model",
            {
                **rules_document,
                "candidate_content_sha256": candidate_hash,
                "rules_sha256": rules_hash,
            },
            version=1,
        ),
        artifact(
            "candidate.safety_ip",
            "independent_model",
            {
                "critical_safety_findings": 0,
                "critical_ip_findings": 0,
                "citations": ["source-1"],
            },
            version=1,
        ),
        artifact(
            "rules.lint",
            "deterministic",
            {
                "rules_complete": True,
                "terminates": True,
                "ambiguities": [],
                "termination_proof": "finite turn bound",
                "candidate_content_sha256": candidate_hash,
                "rules_sha256": rules_hash,
            },
            version=2,
        ),
        artifact(
            "rules.adversary",
            "deterministic",
            {
                "candidate_content_sha256": candidate_hash,
                "rules_sha256": rules_hash,
                "critical_exploits": 0,
                "attacks": [],
                "traces": [],
            },
            version=2,
        ),
        *[
            artifact(
                action,
                "simulation",
                simulation_contents[action],
                version=2,
            )
            for action in (
                "simulation.optimizer",
                "simulation.social",
                "simulation.explorer",
                "simulation.exploit",
            )
        ],
        artifact(
            "human.prepare_blind_kit",
            "same_model",
            {
                **blind_kit,
                "candidate_content_sha256": candidate_hash,
                "rules_sha256": rules_hash,
                "blind_kit_sha256": blind_kit_hash,
            },
            version=3,
        ),
        artifact(
            "human.collect_blind_results",
            "blind_human",
            {
                "trial_ids": trial_ids,
                "candidate_content_sha256": candidate_hash,
                "rules_sha256": rules_hash,
                "blind_kit_sha256": blind_kit_hash,
                "blind_groups": 3,
                "group_ids": group_ids,
                "minimum_games_per_group": 2,
                "designer_hints_required": 0,
                "independent_operator_id": "external-playtest-lab",
                "consent_provenance": consent_provenance,
                "trial_provenance": trial_provenance,
                "reward_evidence": [human_evidence],
            },
            version=3,
        ),
        artifact(
            "physical.create_rich_draft",
            "publishing_pipeline",
            {
                "candidate_id": "game-1",
                "candidate_version": 3,
                "candidate_content_sha256": candidate_hash,
                "rules_sha256": rules_hash,
                "rules_file_sha256": rules_file_hash,
                "status": "draft",
                "design_id": "design-1",
                "slug": "river-council",
                "history_id": "history-1",
                "project_url": "https://cdn.example/project/",
                "project_sha256": project_hash,
                "artifact_hashes": artifact_hashes,
            },
            version=3,
        ),
        artifact(
            "physical.prototype_print",
            "manufacturing",
            prototype_content,
            version=4,
        ),
        artifact(
            "physical.production_run",
            "manufacturing",
            production_content,
            version=4,
        ),
        artifact(
            "market.validate_offer",
            "market",
            {
                "price_cents": 9999,
                "currency": "USD",
                "candidate_content_sha256": candidate_hash,
                "rules_sha256": rules_hash,
                "rules_file_sha256": rules_file_hash,
                "project_sha256": project_hash,
                "artifact_hashes": artifact_hashes,
                "landed_cost_cents": 4000,
                "fees_cents": 500,
                "shipping_subsidy_cents": 0,
                "gross_margin": 0.55,
                "reviewed_packet_hash": packet_hash,
                "factory_capabilities": [],
                "reward_evidence": [market_evidence],
                "receipt": {"run": "market-1"},
            },
            version=4,
        ),
        artifact(
            "market.final_safety_ip",
            "independent_model",
            {
                "critical_safety_findings": 0,
                "critical_ip_findings": 0,
                "candidate_content_sha256": candidate_hash,
                "rules_sha256": rules_hash,
                "reviewed_packet_hash": packet_hash,
                "citations": ["source-2"],
            },
            version=4,
        ),
    ]


CAPABILITIES = {
    "durable_publication_intent",
    "explicit_price",
    "ambiguous_no_retry",
    "page_pipeline_readback",
    "expected_history_cas",
    "exact_sku_currency_binding",
    "server_enrichment_readback",
    "order_to_print_job",
}


class ReleaseAssemblyTests(unittest.TestCase):
    def test_public_manufacturing_receipt_validator_accepts_factory_readbacks(self):
        artifacts = release_artifacts()
        for action in ("physical.prototype_print", "physical.production_run"):
            with self.subTest(action=action):
                content = next(
                    item.content for item in artifacts if item.action == action
                )
                validate_manufacturing_receipt(content, action)

    def test_blind_kit_rejects_a_mutable_pdf_url_without_bytes_readback(self):
        kit = next(
            item.content
            for item in release_artifacts()
            if item.action == "human.prepare_blind_kit"
        )
        changed = dict(kit)
        changed.pop("rules_pdf_readback")
        changed["rules_pdf"] = "https://mutable.example/latest-rules.pdf"

        with self.assertRaisesRegex(ReleaseAssemblyError, "immutable object"):
            validate_blind_kit(changed)

    def test_blind_human_group_and_consent_provenance_cannot_be_empty(self):
        artifacts = release_artifacts()
        human = next(
            item for item in artifacts if item.action == "human.collect_blind_results"
        )
        changed = {**human.content, "consent_provenance": []}
        artifacts[artifacts.index(human)] = artifact(
            human.action, human.evidence_class, changed, version=human.candidate_version
        )

        with self.assertRaisesRegex(ReleaseAssemblyError, "consent_provenance"):
            assess_release(
                artifacts, effect_mode="live", factory_capabilities=CAPABILITIES
            )

    def test_prototype_and_production_receipts_must_be_distinct(self):
        artifacts = release_artifacts()
        prototype = next(
            item.content
            for item in artifacts
            if item.action == "physical.prototype_print"
        )
        production = next(
            item.content
            for item in artifacts
            if item.action == "physical.production_run"
        )
        replayed = {
            **production["receipt"],
            "job_id": prototype["receipt"]["job_id"],
        }
        changed_production = {**production, "receipt": rehash_receipt(replayed)}

        with self.assertRaisesRegex(ReleaseAssemblyError, "reuse job_id"):
            validate_distinct_manufacturing_receipts(prototype, changed_production)

    def test_production_manifest_requires_customer_rules_bom_evidence_and_disclosures(self):
        manifest = next(
            item.content["production_manifest"]
            for item in release_artifacts()
            if item.action == "physical.production_run"
        )
        for section in ("customer", "rules", "bom", "evidence", "disclosures"):
            with self.subTest(section=section):
                changed = dict(manifest)
                changed.pop(section)
                with self.assertRaises(ReleaseAssemblyError):
                    validate_production_manifest(changed)

    def test_production_manifest_recipe_matches_packing_and_printable_artifacts(self):
        manifest = next(
            item.content["production_manifest"]
            for item in release_artifacts()
            if item.action == "physical.production_run"
        )
        wrong_count = copy.deepcopy(manifest)
        wrong_count["manufacturing"]["packing"]["component_count"] = 11
        with self.assertRaisesRegex(ReleaseAssemblyError, "component_count"):
            validate_production_manifest(wrong_count)

        missing_bom_line = copy.deepcopy(manifest)
        missing_bom_line["manufacturing"]["vibe_design"]["artifact_hashes"][
            "bonus.3mf"
        ] = "9" * 64
        with self.assertRaisesRegex(ReleaseAssemblyError, "every and only"):
            validate_production_manifest(missing_bom_line)

    def test_reward_independence_flags_are_preserved_not_overwritten(self):
        artifacts = release_artifacts()
        human = next(
            item for item in artifacts if item.action == "human.collect_blind_results"
        )
        evidence = dict(human.content["reward_evidence"][0])
        evidence["surrogate"] = True
        changed = {**human.content, "reward_evidence": [evidence]}
        artifacts[artifacts.index(human)] = artifact(
            human.action, human.evidence_class, changed, version=human.candidate_version
        )

        decision = assess_release(
            artifacts, effect_mode="live", factory_capabilities=CAPABILITIES
        )
        self.assertFalse(decision["allowed"])
        self.assertGreaterEqual(decision["reward"]["excluded_evidence"], 1)

    def test_zero_game_simulation_is_not_release_evidence(self):
        artifacts = release_artifacts()
        simulation = next(
            item for item in artifacts if item.action == "simulation.optimizer"
        )
        changed = {**simulation.content, "games": 0}
        artifacts[artifacts.index(simulation)] = artifact(
            simulation.action,
            simulation.evidence_class,
            changed,
            version=simulation.candidate_version,
        )

        with self.assertRaisesRegex(ReleaseAssemblyError, "positive integer"):
            assess_release(
                artifacts, effect_mode="live", factory_capabilities=CAPABILITIES
            )

    def test_book_read_requires_legal_access_and_real_citations(self):
        with self.assertRaisesRegex(ValueError, "non-empty citations"):
            validate_output_semantics(
                "library.read",
                {
                    "source_id": "book-1",
                    "access_basis": "owned_copy",
                    "edition": "first edition",
                    "citations": [],
                    "claims": ["A claim"],
                    "unavailable_reason": None,
                },
            )

    def test_release_is_recomputed_and_packet_is_not_regenerated(self):
        decision = assess_release(
            release_artifacts(), effect_mode="live", factory_capabilities=CAPABILITIES
        )
        self.assertTrue(decision["allowed"], decision["failures"])
        decision["candidate_id"] = "game-1"
        decision["candidate_version"] = 4

        with patch(
            "alice.workshop_bridge.pack_artifact",
            wraps=workshop_pack_artifact,
        ) as workshop_packer:
            packet = build_publication_packet(
                candidate_id="game-1",
                candidate_version=5,
                candidate_content_sha256="c" * 64,
                release_decision=decision,
            )

        self.assertEqual(packet["publication_packet"], decision["production_manifest"])
        self.assertEqual(packet["packet_hash"], decision["production_packet_hash"])
        self.assertEqual(
            packet["_workshop_pack"]["source_sha256"],
            decision["production_packet_hash"],
        )
        self.assertEqual(
            packet["_workshop_pack"]["artifact_manifest"]["entries"][0]["sha256"],
            decision["production_packet_hash"],
        )
        self.assertEqual(packet["_workshop_pack"]["pack_entries"], 2)
        workshop_packer.assert_called_once()

    def test_string_manufacturing_receipt_is_rejected(self):
        artifacts = release_artifacts()
        prototype = next(
            item for item in artifacts if item.action == "physical.prototype_print"
        )
        changed = {**prototype.content, "receipt": "prototype-run-1"}
        artifacts[artifacts.index(prototype)] = artifact(
            prototype.action,
            prototype.evidence_class,
            changed,
            version=prototype.candidate_version,
        )

        with self.assertRaisesRegex(ReleaseAssemblyError, "must be an object"):
            assess_release(
                artifacts, effect_mode="live", factory_capabilities=CAPABILITIES
            )

    def test_self_attested_manufacturing_receipt_is_rejected(self):
        artifacts = release_artifacts()
        production = next(
            item for item in artifacts if item.action == "physical.production_run"
        )
        changed_receipt = {
            **production.content["receipt"],
            "authority": "self_attested_by_alice",
        }
        changed = {
            **production.content,
            "receipt": rehash_receipt(changed_receipt),
        }
        artifacts[artifacts.index(production)] = artifact(
            production.action,
            production.evidence_class,
            changed,
            version=production.candidate_version,
        )

        with self.assertRaisesRegex(ReleaseAssemblyError, "external system"):
            assess_release(
                artifacts, effect_mode="live", factory_capabilities=CAPABILITIES
            )

    def test_manufacturing_receipt_is_hash_and_lineage_bound(self):
        production = next(
            item
            for item in release_artifacts()
            if item.action == "physical.production_run"
        )

        tampered = dict(production.content)
        tampered["receipt"] = {
            **production.content["receipt"],
            "material_lot": "different-lot",
        }
        with self.assertRaisesRegex(ReleaseAssemblyError, "receipt_sha256 mismatch"):
            validate_manufacturing_receipt(tampered, production.action)

        wrong_lineage_receipt = {
            **production.content["receipt"],
            "project_sha256": "a" * 64,
        }
        wrong_lineage = {
            **production.content,
            "receipt": rehash_receipt(wrong_lineage_receipt),
        }
        with self.assertRaisesRegex(ReleaseAssemblyError, "lineage mismatch"):
            validate_manufacturing_receipt(wrong_lineage, production.action)

    def test_production_receipt_profile_and_material_match_sold_manifest(self):
        production = next(
            item
            for item in release_artifacts()
            if item.action == "physical.production_run"
        )

        wrong_profile = copy.deepcopy(production.content)
        wrong_profile["production_manifest"]["manufacturing"][
            "print_profile_sha256"
        ] = "9" * 64
        bind_manufacturing_spec(wrong_profile["production_manifest"])
        with self.assertRaisesRegex(ReleaseAssemblyError, "print_profile_sha256"):
            validate_manufacturing_receipt(wrong_profile, production.action)

        wrong_material = copy.deepcopy(production.content)
        wrong_material["production_manifest"]["bom"][0]["material"] = "PETG"
        wrong_material["production_manifest"]["manufacturing"]["materials"] = [
            "PETG"
        ]
        bind_manufacturing_spec(wrong_material["production_manifest"])
        with self.assertRaisesRegex(ReleaseAssemblyError, "material_spec_sha256"):
            validate_manufacturing_receipt(wrong_material, production.action)

    def test_manufacturing_yield_must_match_counts_and_production_claim(self):
        production = next(
            item
            for item in release_artifacts()
            if item.action == "physical.production_run"
        )
        wrong_measurement_receipt = {
            **production.content["receipt"],
            "measured_yield": 0.96,
        }
        wrong_measurement = {
            **production.content,
            "receipt": rehash_receipt(wrong_measurement_receipt),
        }
        with self.assertRaisesRegex(ReleaseAssemblyError, "does not match its counts"):
            validate_manufacturing_receipt(wrong_measurement, production.action)

        wrong_outer_yield = {**production.content, "print_yield": 0.96}
        with self.assertRaisesRegex(ReleaseAssemblyError, "print_yield does not match"):
            validate_manufacturing_receipt(wrong_outer_yield, production.action)

    def test_model_output_cannot_impersonate_human_evidence(self):
        artifacts = release_artifacts()
        human = next(
            item for item in artifacts if item.action == "human.collect_blind_results"
        )
        artifacts[artifacts.index(human)] = ArtifactSnapshot(
            action=human.action,
            task_id=human.task_id,
            candidate_version=human.candidate_version,
            output_sha256=human.output_sha256,
            content_sha256=human.content_sha256,
            executor="agent",
            evidence_class="same_model",
            content=human.content,
        )

        with self.assertRaisesRegex(ReleaseAssemblyError, "blind_human"):
            assess_release(
                artifacts, effect_mode="live", factory_capabilities=CAPABILITIES
            )

    def test_one_changed_manifest_byte_fails_closed(self):
        artifacts = release_artifacts()
        production = next(
            item for item in artifacts if item.action == "physical.production_run"
        )
        changed = dict(production.content)
        changed["production_manifest"] = {
            **changed["production_manifest"],
            "price": {"price_cents": 10000, "currency": "USD"},
        }
        artifacts[artifacts.index(production)] = artifact(
            production.action,
            production.evidence_class,
            changed,
            version=production.candidate_version,
        )

        with self.assertRaisesRegex(ReleaseAssemblyError, "does not match"):
            assess_release(
                artifacts, effect_mode="live", factory_capabilities=CAPABILITIES
            )

    def test_production_must_name_the_exact_rich_draft(self):
        artifacts = release_artifacts()
        production = next(
            item for item in artifacts if item.action == "physical.production_run"
        )
        changed = dict(production.content)
        manifest = dict(changed["production_manifest"])
        manufacturing = dict(manifest["manufacturing"])
        design = dict(manufacturing["vibe_design"])
        design["history_id"] = "unreviewed-history"
        manufacturing["vibe_design"] = design
        manifest["manufacturing"] = manufacturing
        changed["production_manifest"] = manifest
        changed["production_packet_hash"] = canonical_sha256(manifest)
        changed["reviewed_packet_hash"] = changed["production_packet_hash"]
        artifacts[artifacts.index(production)] = artifact(
            production.action,
            production.evidence_class,
            changed,
            version=production.candidate_version,
        )
        for action in ("market.validate_offer", "market.final_safety_ip"):
            original = next(item for item in artifacts if item.action == action)
            content = dict(original.content)
            content["reviewed_packet_hash"] = changed["production_packet_hash"]
            artifacts[artifacts.index(original)] = artifact(
                action,
                original.evidence_class,
                content,
                version=original.candidate_version,
            )

        with self.assertRaisesRegex(ReleaseAssemblyError, "history_id mismatch"):
            assess_release(
                artifacts, effect_mode="live", factory_capabilities=CAPABILITIES
            )


if __name__ == "__main__":
    unittest.main()
