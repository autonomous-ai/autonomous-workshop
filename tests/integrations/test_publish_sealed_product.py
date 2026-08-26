import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from tools import publish_sealed_product as command


class PublishSealedProductCliTest(unittest.TestCase):
    def test_credentials_are_environment_only(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            command, "publish_sealed_draft"
        ) as publish:
            with self.assertRaisesRegex(SystemExit, "both required"):
                command.main(("sealed.json",))
        publish.assert_not_called()

    def test_main_passes_private_credentials_without_printing_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            descriptor = Path(temporary).resolve() / "sealed.json"
            descriptor.write_text("{}\n", encoding="utf-8")
            output = StringIO()
            result = {
                "product_id": "sealed-product",
                "publication": {"status": "draft"},
            }
            with mock.patch.dict(
                os.environ,
                {
                    "WORKSHOP_SHOP_TOKEN": "private-token-value",
                    "WORKSHOP_SHOP_OWNER_ID": "private-owner-value",
                },
                clear=True,
            ), mock.patch.object(
                command, "publish_sealed_draft", return_value=result
            ) as publish, redirect_stdout(output):
                self.assertEqual(
                    command.main((str(descriptor), "--verify-draft")),
                    0,
                )

            publish.assert_called_once_with(
                descriptor,
                token="private-token-value",
                owner_id="private-owner-value",
                repo_root=command.REPO_ROOT,
                verify_draft=True,
            )
            rendered = output.getvalue()
            self.assertEqual(json.loads(rendered), result)
            self.assertNotIn("private-token-value", rendered)
            self.assertNotIn("private-owner-value", rendered)


if __name__ == "__main__":
    unittest.main()
