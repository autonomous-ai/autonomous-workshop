"""``OpenAICompatibleExplodeInspector`` against an injected fake transport.

No test here makes a real network call, and none of them assumes a
particular vendor — the whole point of this adapter is that its base URL,
key, and model are supplied entirely by the caller.
"""

import base64
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop._http import HttpResponse
from inventor_workshop.concept_explode_inspector import (
    CHAT_COMPLETIONS_PATH,
    OpenAICompatibleExplodeInspector,
)
from inventor_workshop.errors import ConceptProviderError, ContractError
from inventor_workshop.jobs import ConceptBrief, ConceptComponent


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGA"
    "hKmMIQAAAABJRU5ErkJggg=="
)


def _sse_chunk(content) -> str:
    return "data: %s\n\n" % json.dumps(
        {"choices": [{"index": 0, "delta": {"content": content}}]}
    )


def _chat_response(answer, *, status: int = 200) -> HttpResponse:
    """Build the SSE stream a real endpoint sends for ``stream: true``.

    Splits the answer across a few chunks (plus an opening role-only chunk
    and a closing empty-delta chunk) so tests exercise real chunk
    accumulation, not just a single-chunk shortcut.
    """

    midpoint = len(answer) // 2
    lines = [
        "data: %s\n\n"
        % json.dumps({"choices": [{"index": 0, "delta": {"role": "assistant"}}]}),
        _sse_chunk(answer[:midpoint]),
        _sse_chunk(answer[midpoint:]),
        "data: %s\n\n"
        % json.dumps({"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}),
        "data: [DONE]\n\n",
    ]
    body = "".join(lines).encode("utf-8")
    return HttpResponse(status, {}, body)


def _brief() -> ConceptBrief:
    return ConceptBrief(
        "a toy",
        "little-worlds",
        (100.0, 80.0, 40.0),
        2.0,
        ("f1",),
        {"orientation": "flat", "supports": False},
        (
            ConceptComponent(
                "body", "Body", "purpose", "form", (10.0, 10.0, 10.0),
                "placement", "interfaces",
            ),
            ConceptComponent(
                "lid", "Lid", "purpose", "form", (10.0, 10.0, 10.0),
                "placement", "interfaces",
            ),
        ),
    )


class RecordingTransport:
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
            }
        )
        return self.responses.pop(0)


class OpenAICompatibleExplodeInspectorTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.brief = _brief()
        self.image = self.root / "exploded.png"
        self.image.write_bytes(PNG_1X1)

    def tearDown(self):
        self.temporary.cleanup()

    # --- construction -----------------------------------------------

    def test_construction_rejects_missing_base_url_key_or_model(self):
        with self.assertRaises(ContractError):
            OpenAICompatibleExplodeInspector("", "key", "model")
        with self.assertRaises(ContractError):
            OpenAICompatibleExplodeInspector("https://x.example", "", "model")
        with self.assertRaises(ContractError):
            OpenAICompatibleExplodeInspector("https://x.example", "key", "")

    def test_two_inspectors_call_only_their_own_configured_endpoint(self):
        transport_a = RecordingTransport([_chat_response(json.dumps(["body"]))])
        transport_b = RecordingTransport([_chat_response(json.dumps(["lid"]))])
        inspector_a = OpenAICompatibleExplodeInspector(
            "https://a.example/v1", "key-a", "model-a", transport=transport_a
        )
        inspector_b = OpenAICompatibleExplodeInspector(
            "https://b.example/v1", "key-b", "model-b", transport=transport_b
        )
        inspector_a(self.image, self.brief)
        inspector_b(self.image, self.brief)
        self.assertTrue(transport_a.calls[0]["url"].startswith("https://a.example"))
        self.assertTrue(transport_b.calls[0]["url"].startswith("https://b.example"))
        self.assertEqual(transport_a.calls[0]["payload"]["model"], "model-a")
        self.assertEqual(transport_b.calls[0]["payload"]["model"], "model-b")

    # --- request shape -----------------------------------------------

    def test_request_names_every_offered_component(self):
        transport = RecordingTransport([_chat_response(json.dumps(["body"]))])
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1", "key", "model", transport=transport
        )
        inspector(self.image, self.brief)
        prompt_text = transport.calls[0]["payload"]["messages"][0]["content"][0][
            "text"
        ]
        self.assertIn("body", prompt_text)
        self.assertIn("lid", prompt_text)

    def test_request_always_asks_for_a_streamed_response(self):
        transport = RecordingTransport([_chat_response(json.dumps(["body"]))])
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1", "key", "model", transport=transport
        )
        inspector(self.image, self.brief)
        self.assertIs(transport.calls[0]["payload"]["stream"], True)

    def test_image_is_sent_inline_not_by_url(self):
        transport = RecordingTransport([_chat_response(json.dumps(["body"]))])
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1", "key", "model", transport=transport
        )
        inspector(self.image, self.brief)
        image_content = transport.calls[0]["payload"]["messages"][0]["content"][1]
        self.assertEqual(image_content["type"], "image_url")
        self.assertTrue(
            image_content["image_url"]["url"].startswith("data:image/png;base64,")
        )

    def test_request_targets_configured_endpoint_model_and_credential(self):
        transport = RecordingTransport([_chat_response(json.dumps(["body"]))])
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1", "secret-key", "vision-model", transport=transport
        )
        inspector(self.image, self.brief)
        call = transport.calls[0]
        self.assertEqual(call["url"], "https://x.example/v1" + CHAT_COMPLETIONS_PATH)
        self.assertEqual(call["payload"]["model"], "vision-model")
        self.assertEqual(call["headers"]["Authorization"], "Bearer secret-key")

    # --- response parsing ------------------------------------------

    def test_well_formed_subset_is_reported_exactly(self):
        transport = RecordingTransport([_chat_response(json.dumps(["body"]))])
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1", "key", "model", transport=transport
        )
        self.assertEqual(inspector(self.image, self.brief), ("body",))

    def test_unparseable_answer_raises_rather_than_reporting_nothing(self):
        transport = RecordingTransport(
            [_chat_response("I can't tell, sorry about that")]
        )
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1", "key", "model", transport=transport
        )
        with self.assertRaises(ConceptProviderError):
            inspector(self.image, self.brief)

    def test_unknown_key_answer_raises_rather_than_passing_through(self):
        transport = RecordingTransport(
            [_chat_response(json.dumps(["body", "not-a-real-component"]))]
        )
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1", "key", "model", transport=transport
        )
        with self.assertRaises(ConceptProviderError):
            inspector(self.image, self.brief)

    def test_malformed_streamed_chunk_raises(self):
        body = b"data: not-json\n\ndata: [DONE]\n\n"
        transport = RecordingTransport([HttpResponse(200, {}, body)])
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1", "key", "model", transport=transport
        )
        with self.assertRaises(ConceptProviderError):
            inspector(self.image, self.brief)

    def test_chunks_are_accumulated_in_order(self):
        body = (
            _sse_chunk("[\"bo")
            + _sse_chunk("dy\"]")
            + "data: [DONE]\n\n"
        ).encode("utf-8")
        transport = RecordingTransport([HttpResponse(200, {}, body)])
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1", "key", "model", transport=transport
        )
        self.assertEqual(inspector(self.image, self.brief), ("body",))

    def test_answer_wrapped_in_prose_is_still_extracted(self):
        transport = RecordingTransport(
            [_chat_response('Sure, here you go: ["body"] -- hope that helps!')]
        )
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1", "key", "model", transport=transport
        )
        self.assertEqual(inspector(self.image, self.brief), ("body",))

    # --- failure handling ------------------------------------------

    def test_client_error_fails_immediately_without_retry(self):
        transport = RecordingTransport([HttpResponse(401, {}, b"{}")])
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1",
            "key",
            "model",
            transport=transport,
            sleep=lambda s: None,
        )
        with self.assertRaises(ConceptProviderError):
            inspector(self.image, self.brief)
        self.assertEqual(len(transport.calls), 1)

    def test_rate_limit_is_retried_then_fails(self):
        transport = RecordingTransport(
            [HttpResponse(429, {}, b"{}"), HttpResponse(429, {}, b"{}")]
        )
        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1",
            "key",
            "model",
            transport=transport,
            sleep=lambda s: None,
            max_attempts=2,
        )
        with self.assertRaises(ConceptProviderError):
            inspector(self.image, self.brief)
        self.assertEqual(len(transport.calls), 2)

    def test_oversized_response_is_rejected(self):
        def oversized_transport(method, url, headers, body, timeout):
            raise ConceptProviderError("response exceeds the configured limit")

        inspector = OpenAICompatibleExplodeInspector(
            "https://x.example/v1", "key", "model", transport=oversized_transport
        )
        with self.assertRaises(ConceptProviderError):
            inspector(self.image, self.brief)


if __name__ == "__main__":
    unittest.main()
