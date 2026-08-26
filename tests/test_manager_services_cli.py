import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from inventor_workshop.cli import (
    _configured_world_reference_service,
    _factory_credentials_for,
    _run_inventor,
    main,
)
from inventor_workshop.factory_agent import FactoryAgentCredentials
from inventor_workshop.manager_services import (
    ManagerProviderIdentity,
    ManagerServiceBinding,
    ManagerServices,
)


class _OpaqueDeliver:
    def preflight(self, context):
        raise AssertionError("composition test must not preflight Deliver")

    def fulfill(self, context):
        raise AssertionError("composition test must not perform Deliver")

    def reconcile(self, context):
        raise AssertionError("composition test must not reconcile Deliver")

    def __repr__(self):
        return "secret-deliver-client"


class _Broker:
    def __init__(self):
        self.calls = []

    def credentials_for(self, inventor_id):
        self.calls.append(inventor_id)
        return FactoryAgentCredentials(
            inventor_id, "secret-for-%s" % inventor_id
        )


class _WorldReference:
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
        del wish, personalization_map, expected_reviewer_id, provider_id
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


def _binding(service, provider_id):
    return ManagerServiceBinding(
        ManagerProviderIdentity(provider_id, "1.0.0", "a" * 64),
        service,
    )


class ManagerServicesCliTest(unittest.TestCase):
    def test_authoritative_run_receives_only_the_registered_shared_engine(self):
        services = ManagerServices(
            "production",
            deliver=_binding(_OpaqueDeliver(), "production-fulfiller"),
        )
        observed = {}

        def execute(assignment, **kwargs):
            observed["assignment"] = assignment
            observed.update(kwargs)
            return {"status": "waiting"}

        assignment = object()
        with mock.patch(
            "inventor_workshop.cli._selected_manager_services",
            return_value=services,
        ), mock.patch(
            "inventor_workshop.manager_execution.execute_manager_workshop",
            side_effect=execute,
        ):
            result = _run_inventor(
                assignment,
                state_validator=lambda selected, value: {
                    **value,
                    "selected": selected is assignment,
                },
            )

        self.assertTrue(result["selected"])
        engine = observed["trusted_engine"]
        self.assertIs(engine.tools.deliver.fulfiller._binding.service.__class__, _OpaqueDeliver)
        self.assertIn("production-fulfiller", dict(engine.provider_ids)["deliver"])
        self.assertNotIn("secret-deliver-client", repr(engine))

    def test_factory_broker_selects_distinct_accounts_without_environment_secrets(self):
        broker = _Broker()
        services = ManagerServices(
            "production",
            factory_credentials=_binding(broker, "factory-broker"),
        )
        with mock.patch(
            "inventor_workshop.cli._selected_manager_services",
            return_value=services,
        ), mock.patch.dict("os.environ", {}, clear=True):
            alice = _factory_credentials_for("alice")
            bob = _factory_credentials_for("bob")

        self.assertEqual((alice.username, bob.username), ("alice", "bob"))
        self.assertEqual(broker.calls, ["alice", "bob"])
        self.assertNotIn("secret-for", repr(alice))
        self.assertNotIn("secret-for", repr(bob))

    def test_world_reference_service_is_selected_only_in_the_manager(self):
        world = _WorldReference()
        services = ManagerServices(
            "production",
            world_reference=_binding(world, "world-reference-provider"),
        )
        with mock.patch(
            "inventor_workshop.cli._selected_manager_services",
            return_value=services,
        ):
            configured = _configured_world_reference_service(object())
        self.assertIs(configured[0], world)
        self.assertEqual(configured[1].provider_id, "world-reference-provider")

    def test_doctor_prints_only_public_provider_identity(self):
        services = ManagerServices(
            "production",
            deliver=_binding(_OpaqueDeliver(), "production-fulfiller"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            # Doctor may report the empty catalog, but it must still return a
            # complete, secret-free Manager service check.
            output = StringIO()
            with mock.patch(
                "inventor_workshop.cli._selected_manager_services",
                return_value=services,
            ), mock.patch.dict("os.environ", {}, clear=True), redirect_stdout(output):
                self.assertEqual(
                    main(("doctor", "--root", str(root), "--json")), 1
                )
        serialized = output.getvalue()
        receipt = json.loads(serialized)
        manager = next(
            item
            for item in receipt["checks"]
            if item["name"] == "manager-services"
        )
        delivery = next(
            item
            for item in receipt["checks"]
            if item["name"] == "physical-delivery"
        )
        self.assertEqual(manager["status"], "ready")
        self.assertEqual(delivery["status"], "ready")
        self.assertIn("production-fulfiller", serialized)
        self.assertNotIn("secret-deliver-client", serialized)


if __name__ == "__main__":
    unittest.main()
