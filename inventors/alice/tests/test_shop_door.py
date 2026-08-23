import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from alice.factory import FactoryClient
from alice.shop_door import ShopDoorClient, ShopDoorError, ShopDraftStamp


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class ShopDoorTests(unittest.TestCase):
    def test_old_client_import_is_only_a_shop_door_alias(self) -> None:
        self.assertIs(FactoryClient, ShopDoorClient)

    def test_legacy_token_name_is_read_but_conflicts_fail_closed(self) -> None:
        with patch.dict(
            os.environ,
            {"ALICE_FACTORY_TOKEN": "legacy-token"},
            clear=True,
        ):
            client = ShopDoorClient.from_environment("https://shop.example")
        self.assertNotIn("legacy-token", repr(client))

        with patch.dict(
            os.environ,
            {
                "WORKSHOP_SHOP_TOKEN": "current-token",
                "ALICE_FACTORY_TOKEN": "other-token",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(ShopDoorError, "conflicts"):
                ShopDoorClient.from_environment("https://shop.example")

    def test_authenticated_client_rejects_insecure_or_credentialed_origins(self) -> None:
        for value in (
            "http://shop.example",
            "https://user:secret@shop.example",
            "https://shop.example?redirect=elsewhere",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ShopDoorClient(value, "secret")

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
            client = ShopDoorClient("https://shop.example", "secret")
            with patch.object(
                client._opener, "open", return_value=_Response(response)
            ) as opened:
                receipt = client.create_draft(
                    archive,
                    import_key="key-1",
                    title="River Council",
                    description="A game\n\nBy Alice.",
                    category="games",
                )
            request = opened.call_args.args[0]
            self.assertIn(b'name="status"\r\n\r\ndraft', request.data)
            self.assertIn(
                b'name="description"\r\n\r\nA game\n\nBy Alice.\r\n',
                request.data,
            )
            self.assertEqual(request.headers["Idempotency-key"], "key-1")
            self.assertEqual(receipt.status, "draft")

    def test_create_draft_rejects_inexact_attribution_before_reading_archive(self) -> None:
        client = ShopDoorClient("https://shop.example", "secret")
        missing_archive = Path("/does/not/exist.zip")
        for description in (
            "A game",
            "A game\n\nNote: By Alice.",
            "A game\n\nBy Alice.\n",
        ):
            with self.subTest(description=description):
                with self.assertRaisesRegex(ValueError, "exact attribution"):
                    client.create_draft(
                        missing_archive,
                        import_key="key-1",
                        title="River Council",
                        description=description,
                        category="games",
                    )

    def test_design_readback_requires_exact_alice_attribution(self) -> None:
        client = ShopDoorClient("https://shop.example", "secret")
        with patch.object(
            client._opener,
            "open",
            return_value=_Response(
                {
                    "id": "d1",
                    "description": "A game\n\nNote: By Alice.",
                }
            ),
        ):
            with self.assertRaisesRegex(ShopDoorError, "exact attribution"):
                client.get_design("river-council")

    def test_live_publish_refuses_current_backend_capabilities(self) -> None:
        receipt = ShopDraftStamp("k", "r", "d", "slug", "draft", "h", None, "a", {})
        client = ShopDoorClient("https://shop.example", "secret")
        with patch.object(client, "capabilities", return_value=frozenset({"explicit_price"})):
            with self.assertRaises(ShopDoorError):
                client.publish_live(
                    receipt,
                    packet_hash="a" * 64,
                    policy_hash="b" * 64,
                    price={"currency": "USD", "amount": 29},
                )

    def test_token_does_not_appear_in_dataclass_receipt(self) -> None:
        client = ShopDoorClient("https://shop.example", "top-secret")
        self.assertNotIn("top-secret", repr(client))


if __name__ == "__main__":
    unittest.main()
