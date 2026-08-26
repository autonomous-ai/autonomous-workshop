import json
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.agent_invent import (
    InventResearch,
    InventResearchSource,
    InventResearchUnavailable,
)
from inventor_workshop.deliver import DefaultDeliver
from inventor_workshop.errors import AmbiguousEffectError, ContractError
from inventor_workshop.factory_agent import FactoryAgentCredentials
from inventor_workshop.jobs import InventContext, Need, PlaytestContext, WaitingFor
from inventor_workshop.manager_services import (
    MANAGER_SERVICES_ENTRY_POINT_GROUP,
    ManagerProviderIdentity,
    ManagerServiceBinding,
    ManagerServices,
    configured_manager_services,
    discover_manager_service_configurations,
    load_manager_services,
    manager_service_forbidden_read_paths,
)
from inventor_workshop.make import Wish
from inventor_workshop.reward_loop import json_sha256
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint


CONFIG_SHA256 = "a" * 64


class _SecretService:
    def __repr__(self):
        return "do-not-print-this-secret"


class _ResearchService(_SecretService):
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def research(self, wish, context):
        self.calls.append((wish, context))
        return self.result


class _ClassicRegistry(_SecretService):
    def provider_for(self, wish, context):
        del wish, context
        return object()


class _WorldReferenceService(_SecretService):
    def descriptors(self, wish):
        del wish
        return ()

    def verify_admission(self, admission, wish, *, expected_reference_id):
        del admission, wish, expected_reference_id

    def authorized_provider_inputs(
        self,
        wish,
        personalization_map,
        *,
        expected_reviewer_id,
        provider_id,
    ):
        del (
            wish,
            personalization_map,
            expected_reviewer_id,
            provider_id,
        )
        return ()

    def verify_authorization(
        self,
        authorization,
        wish,
        personalization_map,
        *,
        expected_reviewer_id,
        provider_id,
    ):
        del (
            authorization,
            wish,
            personalization_map,
            expected_reviewer_id,
            provider_id,
        )


class _WorldPlaytestService(_SecretService):
    def evaluate(self, wish, artifact_sha256, personalization_map, invent_inputs):
        del wish, artifact_sha256, personalization_map, invent_inputs

    def verify(
        self,
        evidence,
        wish,
        artifact_sha256,
        personalization_map,
        invent_inputs,
    ):
        del (
            evidence,
            wish,
            artifact_sha256,
            personalization_map,
            invent_inputs,
        )


class _CredentialBroker(_SecretService):
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def credentials_for(self, inventor_id):
        self.calls.append(inventor_id)
        return self.result


class _DeliverService(_SecretService):
    def preflight(self, context):
        del context

    def fulfill(self, context):
        del context

    def reconcile(self, context):
        del context
        return None


class _EntryPoint:
    def __init__(
        self,
        name,
        target,
        *,
        group=MANAGER_SERVICES_ENTRY_POINT_GROUP,
        module=None,
        distribution=None,
    ):
        self.name = name
        self.group = group
        self.target = target
        self.loads = 0
        if module is not None:
            self.module = module
        if distribution is not None:
            self.dist = distribution

    def load(self):
        self.loads += 1
        return self.target


class _Distribution:
    def __init__(self, root, files):
        self.root = Path(root)
        self.files = tuple(Path(item) for item in files)

    def locate_file(self, relative):
        return self.root / str(relative)


def _identity(provider_id="trusted-provider"):
    return ManagerProviderIdentity(provider_id, "1.2.3", CONFIG_SHA256)


def _binding(service, provider_id="trusted-provider"):
    return ManagerServiceBinding(_identity(provider_id), service)


def _services(configuration_id="production"):
    return ManagerServices(
        configuration_id,
        research=_binding(_ResearchService()),
    )


class ManagerServicesTest(unittest.TestCase):
    def test_provider_identity_is_bounded_and_world_compatible(self):
        identity = _identity()
        self.assertEqual(
            identity.to_dict(),
            {
                "provider_id": "trusted-provider",
                "version": "1.2.3",
                "config_sha256": CONFIG_SHA256,
            },
        )
        self.assertEqual(identity.world_identity().provider_id, "trusted-provider")
        with self.assertRaisesRegex(ContractError, "provider_id"):
            ManagerProviderIdentity("BAD PROVIDER", "1.0.0", CONFIG_SHA256)
        with self.assertRaisesRegex(ContractError, "provider_id"):
            ManagerProviderIdentity("x", "1.0.0", CONFIG_SHA256)
        with self.assertRaisesRegex(ContractError, "exact, non-floating"):
            ManagerProviderIdentity("provider", "latest", CONFIG_SHA256)
        with self.assertRaisesRegex(ContractError, "64 lowercase"):
            ManagerProviderIdentity("provider", "1.0.0", "not-a-digest")

    def test_composition_accepts_every_typed_capability_without_serializing_services(self):
        secret = "do-not-print-this-secret"
        services = ManagerServices(
            "production",
            research=_binding(_ResearchService()),
            classic_rules=_binding(_ClassicRegistry()),
            world_reference=_binding(_WorldReferenceService()),
            world_playtest=_binding(_WorldPlaytestService()),
            factory_credentials=_binding(_CredentialBroker()),
            deliver=_binding(_DeliverService()),
        )

        self.assertEqual(
            services.capabilities,
            (
                "research",
                "classic_rules",
                "world_reference",
                "world_playtest",
                "factory_credentials",
                "deliver",
            ),
        )
        public_json = json.dumps(services.public_summary(), sort_keys=True)
        self.assertNotIn(secret, public_json)
        self.assertNotIn(secret, repr(services))
        self.assertNotIn(secret, repr(services.binding("factory_credentials")))
        self.assertEqual(
            set(services.public_summary()["capabilities"]),
            set(services.capabilities),
        )
        with self.assertRaisesRegex(TypeError, "cannot be serialized"):
            pickle.dumps(services)
        with self.assertRaisesRegex(TypeError, "cannot be serialized"):
            pickle.dumps(services.binding("factory_credentials"))

    def test_composition_rejects_empty_raw_and_structurally_malformed_services(self):
        with self.assertRaisesRegex(ContractError, "at least one capability"):
            ManagerServices("production")
        with self.assertRaisesRegex(ContractError, "typed binding"):
            ManagerServices("production", research=_ResearchService())
        with self.assertRaisesRegex(ContractError, "research service is malformed"):
            ManagerServices("production", research=_binding(object()))
        with self.assertRaisesRegex(ContractError, "world_reference service is malformed"):
            ManagerServices(
                "production", world_reference=_binding(_ResearchService())
            )
        with self.assertRaisesRegex(ContractError, "deliver service is malformed"):
            ManagerServices("production", deliver=_binding(object()))

        class LegacyEffectOnlyDeliver:
            def preflight(self, context):
                del context

            def fulfill(self, context):
                del context

        with self.assertRaisesRegex(ContractError, "deliver service is malformed"):
            ManagerServices(
                "production", deliver=_binding(LegacyEffectOnlyDeliver())
            )

    def test_research_adapter_is_wish_aware_typed_context_bound_and_identity_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "TASTE.md").write_text(
                "---\n"
                "name: Test Inventor\n"
                "description: Turns science into tactile play.\n"
                "---\n"
                "# Taste\n\nMake relationships visible and playable.\n",
                encoding="utf-8",
            )
            wish = Wish.create("light-waves", "I wish I could hold a wave.")
            taste = load_taste(root)
            blueprint = ToyBlueprint.for_lane("holdable-science")
            context = InventContext(wish, taste, blueprint, root)
            source = InventResearchSource(
                "source-one",
                "Observed source",
                "Independent Lab",
                "https://example.org/source",
                "2026-08-26T00:00:00+00:00",
                "Prior art, safety boundaries, and use context were observed.",
                ("prior-art", "safety", "use-context"),
            )
            result = InventResearch(
                json_sha256(wish.to_dict()),
                taste.sha256,
                blueprint.sha256,
                blueprint.lane,
                "trusted-provider",
                "1.2.3",
                CONFIG_SHA256,
                (source,),
            )
            service = _ResearchService(result)
            services = ManagerServices("production", research=_binding(service))

            observed = services.invent_research_provider(context)

        self.assertIs(observed, result)
        self.assertEqual(service.calls, [(wish, context)])

    def test_research_adapter_rejects_provider_identity_substitution(self):
        service = _ResearchService()
        services = ManagerServices("production", research=_binding(service))
        with self.assertRaisesRegex(ContractError, "InventContext"):
            services.invent_research_provider(object())

    def test_factory_broker_returns_only_typed_matching_inventor_credentials(self):
        broker = _CredentialBroker(FactoryAgentCredentials("alice", "secret"))
        services = ManagerServices(
            "production", factory_credentials=_binding(broker)
        )
        credentials = services.factory_credentials_for("alice")
        self.assertEqual(credentials.username, "alice")
        self.assertEqual(broker.calls, ["alice"])
        self.assertNotIn("secret", repr(credentials))

        broker.result = FactoryAgentCredentials("bob", "another-secret")
        with self.assertRaisesRegex(ContractError, "different inventor account"):
            services.factory_credentials_for("alice")
        broker.result = {"username": "alice", "password": "secret"}
        with self.assertRaisesRegex(ContractError, "untyped secret"):
            services.factory_credentials_for("alice")
        broker.result = None
        self.assertIsNone(services.factory_credentials_for("alice"))

    def test_entry_point_discovery_is_injected_bounded_and_does_not_load(self):
        alpha = _EntryPoint("alpha", lambda: _services("alpha"))
        beta = _EntryPoint("beta", lambda: _services("beta"))
        observed_groups = []

        def resolver(group):
            observed_groups.append(group)
            return (beta, alpha)

        self.assertEqual(
            discover_manager_service_configurations(resolver=resolver),
            ("alpha", "beta"),
        )
        self.assertEqual(observed_groups, [MANAGER_SERVICES_ENTRY_POINT_GROUP])
        self.assertEqual((alpha.loads, beta.loads), (0, 0))

    def test_custom_isolation_resolves_provider_code_and_metadata_without_loading(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            provider = root / "trusted_provider"
            metadata = root / "trusted_provider-1.0.0.dist-info"
            provider.mkdir()
            metadata.mkdir()
            (provider / "__init__.py").write_text(
                "raise AssertionError('provider code must not run')\n",
                encoding="utf-8",
            )
            (provider / "services.py").write_text(
                "raise AssertionError('provider factory code must not run')\n",
                encoding="utf-8",
            )
            credentials = provider / "credentials.py"
            credentials.write_text(
                "SECRET = 'do-not-expose-provider-credentials'\n",
                encoding="utf-8",
            )
            provider_data = provider / "private-config.json"
            provider_data.write_text('{"token":"do-not-expose"}\n', encoding="utf-8")
            startup = root / "trusted_provider_startup.pth"
            startup.write_text(
                "import trusted_provider.credentials\n", encoding="utf-8"
            )
            (metadata / "entry_points.txt").write_text(
                "[autonomous_workshop.manager_services]\n"
                "production = trusted_provider:services\n",
                encoding="utf-8",
            )
            distribution = _Distribution(
                root,
                (
                    "trusted_provider/__init__.py",
                    "trusted_provider/credentials.py",
                    "trusted_provider/private-config.json",
                    "trusted_provider/services.py",
                    "trusted_provider_startup.pth",
                    "trusted_provider-1.0.0.dist-info/entry_points.txt",
                ),
            )
            entry = _EntryPoint(
                "production",
                lambda: _services("production"),
                module="trusted_provider.services",
                distribution=distribution,
            )

            paths = manager_service_forbidden_read_paths(
                resolver=lambda unused_group: (entry,)
            )

        self.assertEqual(
            paths,
            tuple(
                sorted(
                    (provider, metadata, startup),
                    key=str,
                )
            ),
        )
        self.assertTrue(any(path in credentials.parents for path in paths))
        self.assertTrue(any(path in provider_data.parents for path in paths))
        self.assertEqual(entry.loads, 0)

    def test_custom_isolation_fails_closed_when_provider_paths_are_unresolvable(self):
        entry = _EntryPoint(
            "production",
            lambda: _services("production"),
            module="trusted_provider",
        )
        with self.assertRaisesRegex(ContractError, "metadata is unavailable"):
            manager_service_forbidden_read_paths(
                resolver=lambda unused_group: (entry,)
            )
        self.assertEqual(entry.loads, 0)

    def test_loader_selects_exactly_one_factory_and_checks_configuration_identity(self):
        alpha = _EntryPoint("alpha", lambda: _services("alpha"))
        beta = _EntryPoint("beta", lambda: _services("beta"))
        loaded = load_manager_services(
            "beta", resolver=lambda unused_group: (alpha, beta)
        )
        self.assertEqual(loaded.configuration_id, "beta")
        self.assertEqual((alpha.loads, beta.loads), (0, 1))

        mismatch = _EntryPoint("alpha", lambda: _services("not-alpha"))
        with self.assertRaisesRegex(ContractError, "another configuration"):
            load_manager_services(
                "alpha", resolver=lambda unused_group: (mismatch,)
            )

    def test_loader_fails_closed_on_duplicate_missing_and_malformed_entry_points(self):
        one = _EntryPoint("alpha", lambda: _services("alpha"))
        duplicate = _EntryPoint("alpha", lambda: _services("alpha"))
        with self.assertRaisesRegex(ContractError, "duplicate"):
            load_manager_services(
                "alpha", resolver=lambda unused_group: (one, duplicate)
            )
        with self.assertRaisesRegex(ContractError, "not installed"):
            load_manager_services("alpha", resolver=lambda unused_group: ())
        malformed_name = _EntryPoint("Alpha!", lambda: _services("alpha"))
        with self.assertRaisesRegex(ContractError, "canonical lowercase"):
            discover_manager_service_configurations(
                resolver=lambda unused_group: (malformed_name,)
            )
        wrong_group = _EntryPoint(
            "alpha", lambda: _services("alpha"), group="untrusted.group"
        )
        with self.assertRaisesRegex(ContractError, "malformed"):
            discover_manager_service_configurations(
                resolver=lambda unused_group: (wrong_group,)
            )
        malformed_target = _EntryPoint("alpha", lambda: object())
        with self.assertRaisesRegex(ContractError, "must return ManagerServices"):
            load_manager_services(
                "alpha", resolver=lambda unused_group: (malformed_target,)
            )

    def test_loader_suppresses_provider_factory_exception_text(self):
        def broken_factory():
            raise RuntimeError("credential=do-not-leak")

        entry = _EntryPoint("alpha", broken_factory)
        with self.assertRaises(ContractError) as raised:
            load_manager_services(
                "alpha", resolver=lambda unused_group: (entry,)
            )
        self.assertEqual(
            str(raised.exception),
            "Manager service configuration failed to load",
        )
        self.assertNotIn("credential", str(raised.exception))

    def test_environment_selection_is_explicit_and_missing_is_inert(self):
        entry = _EntryPoint("production", lambda: _services("production"))
        resolver = lambda unused_group: (entry,)
        self.assertIsNone(configured_manager_services({}, resolver=resolver))
        selected = configured_manager_services(
            {"WORKSHOP_MANAGER_SERVICES": "production"}, resolver=resolver
        )
        self.assertEqual(selected.configuration_id, "production")
        with self.assertRaisesRegex(ContractError, "must name"):
            configured_manager_services(
                {"WORKSHOP_MANAGER_SERVICES": ""}, resolver=resolver
            )

    def test_composition_builds_a_trusted_shared_engine_without_exposing_service(self):
        services = ManagerServices(
            "production",
            deliver=_binding(_DeliverService(), "fulfillment-provider"),
        )
        engine = services.trusted_workshop_engine()
        self.assertIsInstance(engine.tools.deliver, DefaultDeliver)
        self.assertTrue(
            all(
                callable(getattr(engine.tools, stage))
                for stage in ("invent", "make", "playtest", "instructions", "deliver")
            )
        )
        providers = dict(engine.provider_ids)
        self.assertEqual(
            providers["instructions"],
            "workshop.rewarded-instructions-v1",
        )
        self.assertIn("fulfillment-provider", providers["deliver"])
        self.assertEqual(
            tuple(item.stage for item in engine.provenance.components),
            ("invent", "make", "playtest", "instructions", "deliver"),
        )
        deliver_services = [
            item.name
            for item in engine.provenance.component("deliver").dependencies
            if item.kind == "services"
        ]
        self.assertEqual(deliver_services, ["deliver.fulfillment-provider"])
        self.assertNotIn("do-not-print-this-secret", repr(engine))

    def test_live_provider_failures_do_not_leak_exception_text(self):
        class BrokenResearch(_ResearchService):
            def research(self, wish, context):
                del wish, context
                raise RuntimeError("token=do-not-print-this-secret")

        class BrokenBroker(_CredentialBroker):
            def credentials_for(self, inventor_id):
                del inventor_id
                raise RuntimeError("password=do-not-print-this-secret")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "TASTE.md").write_text(
                "---\nname: Test\ndescription: Tactile science.\n---\n# Taste\n",
                encoding="utf-8",
            )
            context = InventContext(
                Wish.create("safe-failure", "A safe science Wish"),
                load_taste(root),
                ToyBlueprint.for_lane("holdable-science"),
                root,
            )
            research = ManagerServices(
                "production", research=_binding(BrokenResearch())
            )
            with self.assertRaises(InventResearchUnavailable) as raised:
                research.invent_research_provider(context)
            self.assertNotIn("token", str(raised.exception))

        broker = ManagerServices(
            "production", factory_credentials=_binding(BrokenBroker())
        )
        with self.assertRaises(ContractError) as raised:
            broker.factory_credentials_for("alice")
        self.assertNotIn("password", str(raised.exception))

        class BrokenWorldReference(_WorldReferenceService):
            def descriptors(self, wish):
                del wish
                raise RuntimeError("private-reference=do-not-print-this-secret")

        world = ManagerServices(
            "production",
            world_reference=_binding(BrokenWorldReference()),
        )
        with self.assertRaises(ContractError) as raised:
            world.prepare_world_inputs(
                Wish.create("safe-world-failure", "A tiny private world")
            )
        self.assertEqual(
            str(raised.exception), "Manager world reference service failed"
        )
        self.assertNotIn("private-reference", str(raised.exception))

        class BrokenWorldPlaytest(_WorldPlaytestService):
            def evaluate(self, *args):
                del args
                raise RuntimeError("world-token=do-not-print-this-secret")

        world_playtest = ManagerServices(
            "production",
            world_playtest=_binding(BrokenWorldPlaytest()),
        )
        with self.assertRaises(ContractError) as raised:
            world_playtest.prepare_world_evidence(
                Wish.create("safe-world-proof-failure", "A tiny private world"),
                "f" * 64,
                {},
                object(),
            )
        self.assertEqual(
            str(raised.exception), "Manager world Playtest service failed"
        )
        self.assertNotIn("world-token", str(raised.exception))

        class BrokenDeliver(_DeliverService):
            def fulfill(self, context):
                del context
                raise RuntimeError("carrier-token=do-not-print-this-secret")

        class FakeDeliverContext:
            def assert_current(self):
                return None

        deliver = ManagerServices(
            "production", deliver=_binding(BrokenDeliver())
        )
        with mock.patch(
            "inventor_workshop.manager_services.DeliverContext",
            FakeDeliverContext,
        ), self.assertRaises(AmbiguousEffectError) as raised:
            deliver.deliver_fulfiller(FakeDeliverContext())
        self.assertIn("unknown outcome", str(raised.exception))
        self.assertNotIn("carrier-token", str(raised.exception))

        class WaitingPreflight(_DeliverService):
            def preflight(self, context):
                del context
                raise WaitingFor(
                    Need(
                        "deliver",
                        "provider-secret",
                        "preflight-token=do-not-print-this-secret",
                        "preflight-password=do-not-print-this-secret",
                    )
                )

            def fulfill(self, context):
                raise AssertionError("failed preflight must not enter fulfill")

        preflight = ManagerServices(
            "production", deliver=_binding(WaitingPreflight())
        )
        with mock.patch(
            "inventor_workshop.manager_services.DeliverContext",
            FakeDeliverContext,
        ), self.assertRaises(WaitingFor) as raised:
            preflight.deliver_fulfiller(FakeDeliverContext())
        self.assertEqual(
            raised.exception.needs[0].capability,
            "production-and-shipping",
        )
        self.assertNotIn(
            "do-not-print-this-secret",
            repr(raised.exception.needs[0].to_dict()),
        )

        class WaitingFulfill(_DeliverService):
            def fulfill(self, context):
                del context
                raise WaitingFor(
                    Need(
                        "deliver",
                        "provider-secret",
                        "effect-token=do-not-print-this-secret",
                        "effect-password=do-not-print-this-secret",
                    )
                )

        effect = ManagerServices(
            "production", deliver=_binding(WaitingFulfill())
        )
        with mock.patch(
            "inventor_workshop.manager_services.DeliverContext",
            FakeDeliverContext,
        ), self.assertRaises(AmbiguousEffectError) as raised:
            effect.deliver_fulfiller(FakeDeliverContext())
        self.assertIn("unknown outcome", str(raised.exception))
        self.assertNotIn("do-not-print-this-secret", str(raised.exception))

        class ReconciliationService(_DeliverService):
            def __init__(self, failure=None):
                self.failure = failure
                self.preflight_calls = 0
                self.fulfill_calls = 0
                self.reconcile_calls = 0

            def preflight(self, context):
                del context
                self.preflight_calls += 1

            def fulfill(self, context):
                del context
                self.fulfill_calls += 1

            def reconcile(self, context):
                del context
                self.reconcile_calls += 1
                if self.failure is not None:
                    raise self.failure
                return None

        readback_service = ReconciliationService()
        readback = ManagerServices(
            "production", deliver=_binding(readback_service)
        ).deliver_fulfiller
        with mock.patch(
            "inventor_workshop.manager_services.DeliverContext",
            FakeDeliverContext,
        ):
            self.assertIsNone(readback.reconcile(FakeDeliverContext()))
        self.assertEqual(
            (
                readback_service.preflight_calls,
                readback_service.fulfill_calls,
                readback_service.reconcile_calls,
            ),
            (0, 0, 1),
        )

        failed_service = ReconciliationService(
            RuntimeError("readback-token=do-not-print-this-secret")
        )
        failed_readback = ManagerServices(
            "production", deliver=_binding(failed_service)
        ).deliver_fulfiller
        with mock.patch(
            "inventor_workshop.manager_services.DeliverContext",
            FakeDeliverContext,
        ), self.assertRaises(AmbiguousEffectError) as raised:
            failed_readback.reconcile(FakeDeliverContext())
        self.assertIn("retry reconciliation", str(raised.exception))
        self.assertNotIn("readback-token", str(raised.exception))
        self.assertEqual(
            (failed_service.preflight_calls, failed_service.fulfill_calls),
            (0, 0),
        )

    def test_classic_provider_need_and_exception_text_are_replaced(self):
        class BrokenClassicRegistry(_ClassicRegistry):
            def __init__(self, failure):
                self.failure = failure

            def provider_for(self, wish, context):
                del wish, context
                raise self.failure

        context = object.__new__(PlaytestContext)
        object.__setattr__(
            context,
            "wish",
            Wish.create("safe-classic-provider", "A personalized public classic"),
        )
        failures = (
            WaitingFor(
                Need(
                    "playtest",
                    "classic-rules-test",
                    "provider-token=do-not-print-this-secret",
                    "carrier-password=do-not-print-this-secret",
                )
            ),
            RuntimeError("provider-secret=do-not-print-this-secret"),
        )
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                services = ManagerServices(
                    "production",
                    classic_rules=_binding(BrokenClassicRegistry(failure)),
                )
                with self.assertRaises(WaitingFor) as raised:
                    services.classic_evidence_provider.prepare(context)
                need = raised.exception.needs[0]
                self.assertEqual(
                    (need.job, need.capability),
                    ("playtest", "classic-rules-test"),
                )
                self.assertIn("shared classic provider", need.reason)
                self.assertNotIn("do-not-print-this-secret", repr(need.to_dict()))


if __name__ == "__main__":
    unittest.main()
