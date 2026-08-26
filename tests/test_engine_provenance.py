import copy
import hashlib
import json
import unittest

from inventor_workshop.agent_instructions import RewardedInstructions
from inventor_workshop.agent_invent import CodexInventor, PublicHTTPResearchProvider
from inventor_workshop.agent_make import CodexMaker
from inventor_workshop.agent_playtest import LaneAwarePlaytester
from inventor_workshop.deliver import DefaultDeliver
from inventor_workshop.engine_provenance import (
    DEPENDENCY_KINDS,
    WORKSHOP_STAGES,
    EngineProvenanceManifest,
    PublicDependency,
    StageComponentManifest,
    compare_engine_for_resume,
    describe_effective_engine,
)
from inventor_workshop.errors import ContractError
from inventor_workshop.invented_game import GAME_SIMULATOR_ID


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class Runner:
    def __init__(self, model, effort, version):
        self.model = model
        self.reasoning_effort = effort
        self.cli_version = version


def standard_components(*, deliver=None):
    return {
        "invent": CodexInventor(
            creator=Runner("gpt-5.6-terra", "high", "1.2.3"),
            evaluator=Runner("gpt-5.6-luna", "low", "1.2.3"),
            research_provider=PublicHTTPResearchProvider(transport=lambda request: request),
        ),
        "make": CodexMaker(
            creator=Runner("gpt-5.6-terra", "high", "1.2.3"),
            evaluator=Runner("gpt-5.6-luna", "low", "1.2.3"),
        ),
        "playtest": LaneAwarePlaytester(
            evaluator=Runner("gpt-5.6-terra", "low", "1.2.3")
        ),
        "instructions": RewardedInstructions(
            None,
            creator=Runner("gpt-5.6-terra", "medium", "1.2.3"),
            evaluator=Runner("gpt-5.6-luna", "low", "1.2.3"),
        ),
        "deliver": DefaultDeliver() if deliver is None else deliver,
    }


class EngineProvenanceTest(unittest.TestCase):
    def test_materializes_all_five_known_components_with_public_dependency_groups(self):
        manifest = describe_effective_engine(standard_components())

        self.assertEqual(tuple(item.stage for item in manifest.components), WORKSHOP_STAGES)
        self.assertEqual(len(manifest.informational_engine_sha256), 64)
        self.assertEqual(set(manifest.stage_sha256), set(WORKSHOP_STAGES))
        for component in manifest.components:
            with self.subTest(stage=component.stage):
                self.assertEqual(component.state, "configured")
                self.assertEqual(component.manifest_completeness, "complete")
                self.assertEqual(len(component.stage_sha256), 64)
                self.assertEqual(
                    set(component.to_dict()["dependencies"]), set(DEPENDENCY_KINDS)
                )

        invent = manifest.component("invent")
        self.assertEqual(
            {dependency.kind for dependency in invent.dependencies},
            {"models", "prompts", "rewards", "toolchains", "services"},
        )
        make = manifest.component("make")
        toolchains = {
            dependency.name: dependency.config_sha256
            for dependency in make.dependencies
            if dependency.kind == "toolchains"
        }
        self.assertIn("workshop-locked-step-cad", toolchains)
        self.assertIn("workshop-skill-cad", toolchains)
        self.assertIn("workshop-skill-product-to-cad", toolchains)
        self.assertTrue(all(len(value) == 64 for value in toolchains.values()))
        deliver_services = [
            item
            for item in manifest.component("deliver").dependencies
            if item.kind == "services"
        ]
        self.assertEqual(
            deliver_services,
            [PublicDependency.missing("services", "production-and-shipping")],
        )

    def test_manager_service_dependencies_publish_only_identity_not_live_service(self):
        class SecretService:
            def __repr__(self):
                raise AssertionError("live service repr must never be evaluated")

        secret = SecretService()
        identity = {
            "provider_id": "manager-research",
            "version": "3.2.1",
            "config_sha256": sha("public configuration, not secret"),
        }
        dependency = PublicDependency.from_public_identity("services", identity)
        components = standard_components()
        components["invent"].research_provider = secret
        manifest = describe_effective_engine(
            components, service_dependencies={"invent": (dependency,)}
        )
        encoded = json.dumps(manifest.to_dict(), sort_keys=True)

        self.assertIn("manager-research", encoded)
        self.assertNotIn("SecretService", encoded)
        self.assertNotIn("secret", encoded.casefold())

    def test_missing_and_custom_states_are_explicit_and_content_addressed(self):
        class CustomMake:
            def __call__(self, context):
                return context

        components = standard_components()
        components["invent"] = None
        components["make"] = CustomMake()
        custom_sha = sha("exact custom hook bytes")
        manifest = describe_effective_engine(
            components,
            custom_stages=("make",),
            provider_ids={"make": "inventor-hook.bob.make"},
            configuration_sha256={"make": custom_sha},
        )

        self.assertEqual(manifest.component("invent").state, "missing")
        self.assertEqual(manifest.component("invent").dependencies, ())
        custom = manifest.component("make")
        self.assertEqual(custom.state, "custom")
        self.assertEqual(custom.manifest_completeness, "complete")
        self.assertEqual(custom.configuration_sha256, custom_sha)
        self.assertEqual(custom.provider_id, "inventor-hook.bob.make")

    def test_unknown_configured_provider_is_honestly_opaque_without_public_config(self):
        class SharedWorker:
            def __call__(self, context):
                return context

        components = standard_components()
        components["make"] = SharedWorker()
        opaque = describe_effective_engine(
            components, provider_ids={"make": "operator.shared-make-v7"}
        ).component("make")
        complete = describe_effective_engine(
            components,
            provider_ids={"make": "operator.shared-make-v7"},
            configuration_sha256={"make": sha("operator public make config")},
        ).component("make")

        self.assertEqual(opaque.manifest_completeness, "opaque")
        self.assertEqual(complete.manifest_completeness, "complete")
        self.assertNotEqual(opaque.stage_sha256, complete.stage_sha256)

    def test_playtest_manifest_reports_actual_simulator_and_custom_checker_state(self):
        baseline = describe_effective_engine(standard_components()).component(
            "playtest"
        )
        components = standard_components()
        components["playtest"] = LaneAwarePlaytester(
            evaluator=Runner("gpt-5.6-terra", "low", "1.2.3"),
            game_simulator=None,
            game_count=1_001,
        )
        without_simulator = describe_effective_engine(components).component(
            "playtest"
        )
        simulator = next(
            dependency
            for dependency in without_simulator.dependencies
            if dependency.name == GAME_SIMULATOR_ID
        )
        self.assertEqual(simulator.state, "missing")
        self.assertNotEqual(without_simulator.stage_sha256, baseline.stage_sha256)

        def custom_print_checker(context):
            return context

        components["playtest"] = LaneAwarePlaytester(
            evaluator=Runner("gpt-5.6-terra", "low", "1.2.3"),
            capability_checks={"print-test": custom_print_checker},
        )
        custom = describe_effective_engine(components).component("playtest")
        self.assertEqual(custom.manifest_completeness, "opaque")
        self.assertTrue(
            any(
                dependency.kind == "toolchains"
                and dependency.state == "custom"
                and dependency.name.startswith("playtest-check.print-test.")
                for dependency in custom.dependencies
            )
        )

    def test_round_trip_revalidates_stage_and_informational_digests(self):
        original = describe_effective_engine(standard_components())
        wire = json.loads(json.dumps(original.to_dict(), sort_keys=True))
        rebuilt = EngineProvenanceManifest.from_dict(wire)
        self.assertEqual(rebuilt, original)

        tampered_stage = copy.deepcopy(wire)
        tampered_stage["components"][0]["provider_id"] = "different-provider"
        with self.assertRaisesRegex(ContractError, "stage component manifest digest"):
            EngineProvenanceManifest.from_dict(tampered_stage)

        tampered_engine = copy.deepcopy(wire)
        tampered_engine["informational_engine_sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "informational engine digest"):
            EngineProvenanceManifest.from_dict(tampered_engine)

    def test_provider_addition_at_no_effect_wait_does_not_invalidate_completed_stages(self):
        recorded_components = standard_components()
        recorded_components["deliver"] = None
        recorded = describe_effective_engine(recorded_components)
        delivery_service = PublicDependency.configured(
            "services", "manager-fulfillment", "2.0.0", sha("fulfillment-config")
        )
        current = describe_effective_engine(
            standard_components(deliver=DefaultDeliver(lambda context: context)),
            provider_ids={"deliver": "manager-services.production.deliver.v2"},
            service_dependencies={"deliver": (delivery_service,)},
        )

        decision = compare_engine_for_resume(
            recorded,
            current,
            completed_stages=("invent", "make", "playtest", "instructions"),
        )
        self.assertEqual(decision.changed_stages, ("deliver",))
        self.assertTrue(decision.informational_engine_changed)

    def test_completed_or_effect_started_stage_cannot_change(self):
        recorded = describe_effective_engine(standard_components())
        replacement = PublicDependency.configured(
            "services", "manager-fulfillment", "2.0.0", sha("fulfillment-config")
        )
        current = describe_effective_engine(
            standard_components(deliver=DefaultDeliver(lambda context: context)),
            provider_ids={"deliver": "manager-services.production.deliver.v2"},
            service_dependencies={"deliver": (replacement,)},
        )

        with self.assertRaisesRegex(ContractError, "protected stage.*deliver"):
            compare_engine_for_resume(
                recorded,
                current,
                completed_stages=("invent", "make", "playtest", "instructions"),
                effect_started_stages=("deliver",),
            )

        changed_invent_components = standard_components()
        changed_invent_components["invent"] = CodexInventor(
            creator=Runner("gpt-5.6-terra", "high", "1.2.3"),
            evaluator=Runner("gpt-5.6-luna", "low", "1.2.3"),
            research_provider=None,
            goal=91,
        )
        changed_invent = describe_effective_engine(changed_invent_components)
        with self.assertRaisesRegex(ContractError, "protected stage.*invent"):
            compare_engine_for_resume(
                recorded, changed_invent, completed_stages=("invent",)
            )

    def test_reward_loop_goal_changes_each_stage_identity_and_resume_fence(self):
        recorded_components = standard_components()
        recorded = describe_effective_engine(recorded_components)
        changed_components = (
            (
                "invent",
                85,
                CodexInventor(
                    creator=Runner("gpt-5.6-terra", "high", "1.2.3"),
                    evaluator=Runner("gpt-5.6-luna", "low", "1.2.3"),
                    research_provider=PublicHTTPResearchProvider(
                        transport=lambda request: request
                    ),
                    goal=91,
                ),
            ),
            (
                "make",
                85,
                CodexMaker(
                    creator=Runner("gpt-5.6-terra", "high", "1.2.3"),
                    evaluator=Runner("gpt-5.6-luna", "low", "1.2.3"),
                    goal=91,
                ),
            ),
            (
                "instructions",
                90,
                RewardedInstructions(
                    None,
                    creator=Runner("gpt-5.6-terra", "medium", "1.2.3"),
                    evaluator=Runner("gpt-5.6-luna", "low", "1.2.3"),
                    goal=91,
                ),
            ),
        )

        for stage, recorded_goal, replacement in changed_components:
            with self.subTest(stage=stage):
                self.assertEqual(
                    (recorded_components[stage].goal, replacement.goal),
                    (recorded_goal, 91),
                )
                components = standard_components()
                components[stage] = replacement
                changed = describe_effective_engine(components)
                self.assertNotEqual(
                    recorded.component(stage).configuration_sha256,
                    changed.component(stage).configuration_sha256,
                )
                self.assertNotEqual(
                    recorded.component(stage).stage_sha256,
                    changed.component(stage).stage_sha256,
                )
                with self.assertRaisesRegex(
                    ContractError, "protected stage.*%s" % stage
                ):
                    compare_engine_for_resume(
                        recorded, changed, completed_stages=(stage,)
                    )

    def test_stage_constructor_and_effective_shape_fail_closed(self):
        with self.assertRaisesRegex(ContractError, "missing stage"):
            StageComponentManifest(
                "invent",
                "missing",
                "complete",
                "claimed-provider",
                None,
                None,
            )
        incomplete = standard_components()
        incomplete.pop("deliver")
        with self.assertRaisesRegex(ContractError, "all five stages"):
            describe_effective_engine(incomplete)


if __name__ == "__main__":
    unittest.main()
