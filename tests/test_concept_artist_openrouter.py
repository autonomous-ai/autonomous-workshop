"""``OpenRouterConceptArtist`` against an injected fake transport.

No test here makes a real network call — every scenario drives the artist
through a fake ``Transport`` callable, the same dependency-injection seam
``ShopDoor`` uses for its own tests.
"""

import base64
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop._http import HttpResponse
from inventor_workshop.concept import ConceptImageRequest
from inventor_workshop.concept_artist_openrouter import (
    MAX_INPUT_REFERENCES,
    OPENROUTER_API_BASE,
    OPENROUTER_IMAGE_MODEL,
    OpenRouterConceptArtist,
)
from inventor_workshop.errors import ConceptProviderError, ContractError
from inventor_workshop.jobs import ConceptBrief, ConceptComponent


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGA"
    "hKmMIQAAAABJRU5ErkJggg=="
)


def _image_response(data: bytes = PNG_1X1, *, status: int = 200) -> HttpResponse:
    payload = json.dumps(
        {"data": [{"b64_json": base64.b64encode(data).decode("ascii")}]}
    ).encode("utf-8")
    return HttpResponse(status, {}, payload)


def _brief(components=None) -> ConceptBrief:
    components = components or (
        ConceptComponent(
            "body", "Body", "purpose", "form", (10.0, 10.0, 10.0), "placement",
            "interfaces",
        ),
    )
    return ConceptBrief(
        "a toy",
        "little-worlds",
        (100.0, 80.0, 40.0),
        2.0,
        ("f1",),
        {"orientation": "flat", "supports": False},
        components,
    )


class RecordingTransport:
    """Replays queued responses and records every call it received."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "payload": json.loads(body.decode("utf-8")),
                "timeout": timeout,
            }
        )
        return self.responses.pop(0)


class OpenRouterConceptArtistTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.brief = _brief()

    def tearDown(self):
        self.temporary.cleanup()

    def request(self, *, role="front", references=(), filename="images/front.png"):
        return ConceptImageRequest(
            role=role,
            kind="overall" if role != "body" else "component",
            prompt="draw %s" % role,
            references=references,
            workspace=self.root,
            filename=filename,
            brief=self.brief,
            round=1,
        )

    def reference_file(self, name="ref.png", data=PNG_1X1):
        path = self.root / name
        path.write_bytes(data)
        return path

    # --- construction -----------------------------------------------

    def test_construction_rejects_missing_api_key(self):
        with self.assertRaises(ContractError):
            OpenRouterConceptArtist("")
        with self.assertRaises(ContractError):
            OpenRouterConceptArtist("   ")

    def test_default_api_base_is_the_pinned_openrouter_origin(self):
        self.assertTrue(OPENROUTER_API_BASE.startswith("https://openrouter.ai"))
        transport = RecordingTransport([_image_response()])
        artist = OpenRouterConceptArtist("key", transport=transport)
        artist(self.request())
        self.assertEqual(
            transport.calls[0]["url"], OPENROUTER_API_BASE + "/images"
        )

    def test_construction_rejects_non_https_api_base(self):
        with self.assertRaises(ContractError):
            OpenRouterConceptArtist("key", api_base="http://openrouter.ai/api/v1")

    # --- drawing -------------------------------------------------------

    def test_no_reference_draw_sends_prompt_alone(self):
        transport = RecordingTransport([_image_response()])
        artist = OpenRouterConceptArtist("key", transport=transport)
        result = artist(self.request())
        self.assertEqual(result, "images/front.png")
        self.assertEqual((self.root / result).read_bytes(), PNG_1X1)
        sent = transport.calls[0]["payload"]
        self.assertNotIn("input_references", sent)
        self.assertEqual(sent["prompt"], "draw front")

    def test_reference_attached_draw_encodes_every_reference_in_order(self):
        first = self.reference_file("a.png")
        second = self.reference_file("b.png")
        transport = RecordingTransport([_image_response()])
        artist = OpenRouterConceptArtist("key", transport=transport)
        artist(self.request(references=(first, second), filename="images/top.png"))
        sent = transport.calls[0]["payload"]
        self.assertEqual(len(sent["input_references"]), 2)
        for entry in sent["input_references"]:
            self.assertEqual(entry["type"], "image_url")
            self.assertTrue(
                entry["image_url"]["url"].startswith("data:image/png;base64,")
            )

    def test_every_call_omits_seed_and_temperature_and_requests_one_image(self):
        transport = RecordingTransport([_image_response(), _image_response()])
        artist = OpenRouterConceptArtist("key", transport=transport)
        artist(self.request())
        artist(self.request(role="top", filename="images/top.png"))
        for call in transport.calls:
            self.assertNotIn("seed", call["payload"])
            self.assertNotIn("temperature", call["payload"])
            self.assertEqual(call["payload"]["n"], 1)
            self.assertEqual(call["payload"]["model"], OPENROUTER_IMAGE_MODEL)

    def test_missing_reference_fails_without_calling_transport(self):
        missing = self.root / "does-not-exist.png"

        def unreachable(*args, **kwargs):
            raise AssertionError("transport must not be called")

        artist = OpenRouterConceptArtist("key", transport=unreachable)
        with self.assertRaises(ConceptProviderError):
            artist(self.request(references=(missing,)))

    def test_unrecognized_reference_format_fails_without_calling_transport(self):
        not_an_image = self.reference_file("bad.png", data=b"not an image")

        def unreachable(*args, **kwargs):
            raise AssertionError("transport must not be called")

        artist = OpenRouterConceptArtist("key", transport=unreachable)
        with self.assertRaises(ConceptProviderError):
            artist(self.request(references=(not_an_image,)))

    def test_too_many_references_rejected_without_calling_transport(self):
        references = tuple(
            self.reference_file("r%d.png" % index)
            for index in range(MAX_INPUT_REFERENCES + 1)
        )

        def unreachable(*args, **kwargs):
            raise AssertionError("transport must not be called")

        artist = OpenRouterConceptArtist("key", transport=unreachable)
        with self.assertRaises(ConceptProviderError):
            artist(self.request(references=references))

    # --- failure handling ------------------------------------------

    def test_empty_image_data_fails_naming_the_role(self):
        payload = json.dumps({"data": []}).encode("utf-8")
        transport = RecordingTransport([HttpResponse(200, {}, payload)])
        artist = OpenRouterConceptArtist("key", transport=transport)
        with self.assertRaises(ConceptProviderError) as ctx:
            artist(self.request(role="exploded", filename="images/exploded.png"))
        self.assertIn("exploded", str(ctx.exception))
        self.assertFalse((self.root / "images" / "exploded.png").exists())

    def test_client_error_fails_immediately_without_retry(self):
        transport = RecordingTransport(
            [HttpResponse(400, {}, b'{"error":"bad request"}')]
        )
        artist = OpenRouterConceptArtist("key", transport=transport, sleep=lambda s: None)
        with self.assertRaises(ConceptProviderError):
            artist(self.request())
        self.assertEqual(len(transport.calls), 1)

    def test_rate_limit_is_retried_then_fails(self):
        transport = RecordingTransport(
            [
                HttpResponse(429, {}, b"{}"),
                HttpResponse(429, {}, b"{}"),
                HttpResponse(429, {}, b"{}"),
            ]
        )
        artist = OpenRouterConceptArtist(
            "key", transport=transport, sleep=lambda s: None, max_attempts=3
        )
        with self.assertRaises(ConceptProviderError):
            artist(self.request())
        self.assertEqual(len(transport.calls), 3)

    def test_server_error_eventually_succeeds_within_retry_budget(self):
        transport = RecordingTransport(
            [HttpResponse(503, {}, b"{}"), _image_response()]
        )
        artist = OpenRouterConceptArtist(
            "key", transport=transport, sleep=lambda s: None, max_attempts=3
        )
        result = artist(self.request())
        self.assertEqual(result, "images/front.png")
        self.assertEqual(len(transport.calls), 2)

    def test_malformed_response_fails_clearly(self):
        transport = RecordingTransport([HttpResponse(200, {}, b"not json")])
        artist = OpenRouterConceptArtist("key", transport=transport)
        with self.assertRaises(ConceptProviderError):
            artist(self.request())

    def test_oversized_response_is_rejected(self):
        def oversized_transport(method, url, headers, body, timeout):
            raise ConceptProviderError("response exceeds the configured limit")

        artist = OpenRouterConceptArtist("key", transport=oversized_transport)
        with self.assertRaises(ConceptProviderError):
            artist(self.request())


if __name__ == "__main__":
    unittest.main()
