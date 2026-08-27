"""Focused tests for the host-side concept-image transport."""

import base64
import json
import unittest

from workshop.integrations.concept_images import (
    ConceptImagesAdapter,
    ConceptImagesConfig,
)


class _Response:
    status = 200

    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self, maximum: int) -> bytes:
        return self._body[:maximum]


class ConceptImagesAdapterTest(unittest.TestCase):
    def test_provider_timeout_is_passed_as_keyword(self):
        image = b"concept-image"
        body = json.dumps(
            {"image_base64": base64.b64encode(image).decode("ascii")}
        ).encode("utf-8")
        calls = []

        def opener(request, *, timeout):
            calls.append((request, timeout))
            return _Response(body)

        adapter = ConceptImagesAdapter(
            ConceptImagesConfig(
                endpoint="https://provider.example/images",
                api_key="secret",
                model="image-model",
                timeout_seconds=17.5,
            ),
            opener=opener,
        )

        drawn = adapter._draw_one("front", "draw the object", ())

        self.assertEqual(drawn, image)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], 17.5)

    def test_openrouter_image_request_and_response_are_supported(self):
        image = b"openrouter-image"
        body = json.dumps(
            {
                "data": [
                    {
                        "b64_json": base64.b64encode(image).decode("ascii"),
                        "media_type": "image/png",
                    }
                ]
            }
        ).encode("utf-8")
        requests = []

        def opener(request, *, timeout):
            requests.append(request)
            return _Response(body)

        adapter = ConceptImagesAdapter(
            ConceptImagesConfig(
                endpoint="https://openrouter.ai/api/v1/images",
                api_key="secret",
                model="image-model",
            ),
            opener=opener,
        )

        drawn = adapter._draw_one(
            "top", "draw the same object from above", (b"front-reference",)
        )

        self.assertEqual(drawn, image)
        payload = json.loads(requests[0].data.decode("utf-8"))
        self.assertEqual(payload["model"], "image-model")
        self.assertEqual(payload["prompt"], "draw the same object from above")
        self.assertEqual(
            payload["input_references"],
            [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,%s"
                        % base64.b64encode(b"front-reference").decode("ascii")
                    },
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
