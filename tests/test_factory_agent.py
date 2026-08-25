import json
import unittest

from inventor_workshop.errors import ContractError
from inventor_workshop.factory_agent import (
    FactoryAgentCredentials,
    FactoryAgentSession,
    FactoryCredentialRejected,
    FactoryPublicTransition,
    factory_credentials_from_environment,
)
from inventor_workshop.models import Receipt
from inventor_workshop.shop import DEFAULT_SHOP_API, HttpResponse


def login_response(number=1):
    return HttpResponse(
        200,
        {"Content-Type": "application/json"},
        json.dumps(
            {
                "access_token": "test-access-%d" % number,
                "token_type": "Bearer",
                "expires_in": 31_536_000,
                "expires_at": "2027-08-25T00:00:00Z",
                "user": {"id": "owner-alice", "username": "alice"},
            }
        ).encode("utf-8"),
    )


class ScriptedTransport:
    def __init__(self, protected_statuses=(200,)):
        self.protected_statuses = list(protected_statuses)
        self.calls = []
        self.logins = 0

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, dict(headers), body, timeout))
        if url.endswith("/auth/agent/login"):
            self.logins += 1
            return login_response(self.logins)
        status = self.protected_statuses.pop(0)
        return HttpResponse(status, {}, b"{}")


class FactoryAgentTest(unittest.TestCase):
    def test_credentials_use_only_the_spec_environment_pair_and_are_redacted(self):
        credentials = factory_credentials_from_environment(
            "alice",
            {"FACTORY_USERNAME": "alice", "FACTORY_PASSWORD": "test-credential"},
        )
        self.assertEqual(credentials.username, "alice")
        self.assertNotIn("test-credential", repr(credentials))
        self.assertNotIn("alice", repr(credentials))
        with self.assertRaisesRegex(ContractError, "configured together"):
            factory_credentials_from_environment(
                "alice", {"FACTORY_USERNAME": "alice"}
            )
        with self.assertRaisesRegex(ContractError, "not configured"):
            factory_credentials_from_environment(
                "alice",
                {
                    "FACTORY_ALICE_USERNAME": "alice",
                    "FACTORY_ALICE_PASSWORD": "ignored-by-contract",
                },
            )
        with self.assertRaisesRegex(ContractError, "selected inventor_id"):
            factory_credentials_from_environment(
                "bob",
                {"FACTORY_USERNAME": "alice", "FACTORY_PASSWORD": "test-credential"},
            )

    def test_login_is_cached_in_memory_and_never_forwards_password(self):
        transport = ScriptedTransport((200, 200))
        session = FactoryAgentSession(
            FactoryAgentCredentials("alice", "test-credential"),
            transport=transport,
        )
        first = session.authenticated_transport(
            "GET", DEFAULT_SHOP_API + "/designs/example", {}, None, 30
        )
        second = session.authenticated_transport(
            "GET", DEFAULT_SHOP_API + "/designs/example", {}, None, 30
        )
        self.assertEqual((first.status, second.status), (200, 200))
        self.assertEqual(transport.logins, 1)
        login = transport.calls[0]
        self.assertNotIn("Authorization", login[2])
        self.assertEqual(
            json.loads(login[3]),
            {"username": "alice", "password": "test-credential"},
        )
        for call in transport.calls[1:]:
            self.assertEqual(call[2]["Authorization"], "Bearer test-access-1")
            self.assertNotIn(b"test-credential", call[3] or b"")
        self.assertNotIn("test-credential", repr(session))
        self.assertNotIn("test-access", repr(session))

    def test_protected_401_relogs_in_and_retries_exactly_once(self):
        transport = ScriptedTransport((401, 200))
        session = FactoryAgentSession(
            FactoryAgentCredentials("alice", "test-credential"),
            transport=transport,
        )
        response = session.authenticated_transport(
            "POST", DEFAULT_SHOP_API + "/designs/import", {}, b"sealed", 120
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(transport.logins, 2)
        protected = [
            call for call in transport.calls if not call[1].endswith("/auth/agent/login")
        ]
        self.assertEqual(len(protected), 2)
        self.assertEqual(protected[0][2]["Authorization"], "Bearer test-access-1")
        self.assertEqual(protected[1][2]["Authorization"], "Bearer test-access-2")
        self.assertEqual(protected[0][3], protected[1][3])

    def test_login_401_reports_rotation_without_echoing_response_or_secret(self):
        def rejected(method, url, headers, body, timeout):
            del method, url, headers, body, timeout
            return HttpResponse(401, {}, b'{"error":"sensitive provider detail"}')

        session = FactoryAgentSession(
            FactoryAgentCredentials("alice", "test-credential"),
            transport=rejected,
        )
        with self.assertRaises(FactoryCredentialRejected) as raised:
            session.login()
        message = str(raised.exception)
        self.assertNotIn("test-credential", message)
        self.assertNotIn("sensitive provider detail", message)

    def test_bearer_is_pinned_to_factory_origin(self):
        session = FactoryAgentSession(
            FactoryAgentCredentials("alice", "test-credential"),
            transport=ScriptedTransport(),
        )
        with self.assertRaisesRegex(ContractError, "another origin"):
            session.authenticated_transport(
                "GET", "https://example.com/api/v1/designs/example", {}, None, 30
            )


class PublicTransitionTransport:
    def __init__(self, designs):
        self.designs = list(designs)
        self.calls = []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, dict(headers), body, timeout))
        if url.endswith("/auth/agent/login"):
            return login_response()
        if method == "GET" and "/designs/" in url:
            return HttpResponse(200, {}, json.dumps(self.designs.pop(0)).encode())
        if method == "POST" and url.endswith("/publish"):
            return HttpResponse(200, {}, b"{}")
        raise AssertionError("unexpected Factory call")


def exact_design(status, *, history="history-1"):
    public = status == "public"
    return {
        "id": "design-pocket-duel",
        "slug": "pocket-duel",
        "owner_id": "owner-alice",
        "root_id": "design-pocket-duel",
        "current_history_id": history,
        "published_history_id": history if public else None,
        "status": status,
        "project_url": "https://cdn.autonomous.ai/projects/history-1/",
        "listing": (
            {
                "active": True,
                "price_cents": 2400,
                "currency": "usd",
                "sku": "PD-001",
            }
            if public
            else None
        ),
    }


def draft_receipt():
    return Receipt.from_design(
        exact_design("draft"),
        "f" * 64,
        "a" * 64,
        observed_at="2026-08-25T12:00:00+00:00",
    )


class FactoryPublicTransitionTest(unittest.TestCase):
    def test_explicit_transition_publishes_without_price_then_proves_current_history(self):
        transport = PublicTransitionTransport(
            [exact_design("draft"), exact_design("public")]
        )
        session = FactoryAgentSession(
            FactoryAgentCredentials("alice", "test-credential"),
            transport=transport,
        )
        receipt = FactoryPublicTransition(session).publish(draft_receipt())
        self.assertEqual(receipt.status, "public")
        self.assertEqual(receipt.published_history_id, receipt.current_history_id)
        self.assertTrue(receipt.is_verified_public)
        publish_calls = [
            call for call in transport.calls if call[1].endswith("/publish")
        ]
        self.assertEqual(len(publish_calls), 1)
        self.assertIsNone(publish_calls[0][3])
        self.assertEqual(
            [call[0] for call in transport.calls], ["POST", "GET", "POST", "GET"]
        )

    def test_already_public_exact_history_is_an_authenticated_replay(self):
        transport = PublicTransitionTransport([exact_design("public")])
        session = FactoryAgentSession(
            FactoryAgentCredentials("alice", "test-credential"),
            transport=transport,
        )
        receipt = FactoryPublicTransition(session).publish(draft_receipt())
        self.assertTrue(receipt.is_verified_public)
        self.assertFalse(any(call[1].endswith("/publish") for call in transport.calls))

    def test_public_readback_must_preserve_the_exact_draft_history(self):
        transport = PublicTransitionTransport(
            [exact_design("draft"), exact_design("public", history="history-2")]
        )
        session = FactoryAgentSession(
            FactoryAgentCredentials("alice", "test-credential"),
            transport=transport,
        )
        with self.assertRaisesRegex(Exception, "exact draft|readback"):
            FactoryPublicTransition(session).publish(draft_receipt())


if __name__ == "__main__":
    unittest.main()
