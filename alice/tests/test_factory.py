import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from alice.factory import FactoryClient, FactoryDraftReceipt, FactoryError


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class FactoryTests(unittest.TestCase):
    def test_authenticated_client_rejects_insecure_or_credentialed_origins(self) -> None:
        for value in (
            "http://factory.example",
            "https://user:secret@factory.example",
            "https://factory.example?redirect=elsewhere",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    FactoryClient(value, "secret")

    def test_create_draft_forces_draft_and_validates_receipt(self) -> None:
        response = {
            "id": "d1",
            "slug": "river-council",
            "status": "draft",
            "current_history_id": "h1",
            "published_history_id": None,
            "project_url": "https://cdn/project.zip",
        }
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "game.zip"
            archive.write_bytes(b"PK-fixture")
            client = FactoryClient("https://factory.example", "secret")
            with patch.object(
                client._opener, "open", return_value=_Response(response)
            ) as opened:
                receipt = client.create_draft(
                    archive,
                    import_key="key-1",
                    title="River Council",
                    description="A game",
                    category="games",
                )
            request = opened.call_args.args[0]
            self.assertIn(b'name="status"\r\n\r\ndraft', request.data)
            self.assertEqual(request.headers["Idempotency-key"], "key-1")
            self.assertEqual(receipt.status, "draft")

    def test_live_publish_refuses_current_backend_capabilities(self) -> None:
        receipt = FactoryDraftReceipt("k", "r", "d", "slug", "draft", "h", None, "a", {})
        client = FactoryClient("https://factory.example", "secret")
        with patch.object(client, "capabilities", return_value=frozenset({"explicit_price"})):
            with self.assertRaises(FactoryError):
                client.publish_live(
                    receipt,
                    packet_hash="a" * 64,
                    policy_hash="b" * 64,
                    price={"currency": "USD", "amount": 29},
                )

    def test_token_does_not_appear_in_dataclass_receipt(self) -> None:
        client = FactoryClient("https://factory.example", "top-secret")
        self.assertNotIn("top-secret", repr(client))


if __name__ == "__main__":
    unittest.main()
