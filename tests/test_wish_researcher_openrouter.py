"""The real wish researcher, against a fake transport. No network is touched.

What matters here is that the adapter never quietly invents: a missing fact, an
unparseable answer, or a citation the endpoint returned no material for all
fail loudly rather than becoming a breakdown with nothing decided.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop._http import HttpResponse
from inventor_workshop.concept import WishResearchRequest
from inventor_workshop.errors import ConceptProviderError, ContractError
from inventor_workshop.make import Wish
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint
from inventor_workshop.wish_researcher_openrouter import (
    CHAT_COMPLETIONS_PATH,
    ENV_WISH_RESEARCHER_API_KEY,
    ENV_WISH_RESEARCHER_BASE_URL,
    ENV_WISH_RESEARCHER_MODEL,
    WEB_SEARCH_PLUGIN_ID,
    OpenAICompatibleWishResearcher,
)


ANSWER = {
    "object": "a skyline chess set",
    "category": "a printed edition of a known game",
    "envelope_mm": [420.0, 420.0, 95.0],
    "wall_mm": 2.2,
    "features": [
        "each piece is a recognisable Manhattan tower rather than a classical form"
    ],
    "print": {"orientation": "flat on its largest face", "supports": False},
    "fits": None,
    "components": [
        {
            "key": "board",
            "name": "Board",
            "purpose": "Carries the sixty-four squares.",
            "form": "a flat tiled panel with a raised border",
            "dimensions_mm": [420.0, 420.0, 8.0],
            "placement": "the base of the set, resting on the table",
            "interfaces": "its squares seat the pieces; nothing sits below it",
        },
        {
            "key": "king",
            "name": "King",
            "purpose": "The piece the game is won and lost on.",
            "form": "a stepped setback tower with a spire",
            "dimensions_mm": [40.0, 40.0, 95.0],
            "placement": "one per side, on the board's back rank",
            "interfaces": "its round base sits within one square",
        },
    ],
    "findings": [
        {"claim": "The set is a skyline chess set.", "field": "object",
         "decided_because": "the Wish names it"},
        {"claim": "It is a printed edition of a known game.", "field": "category",
         "decided_because": "the lane says so"},
        {"claim": "A tournament board is 420 mm across.", "field": "envelope_mm",
         "sources": ["https://example.invalid/standards"]},
        {"claim": "A 2.2 mm wall prints cleanly at this scale.", "field": "wall_mm",
         "decided_because": "no source stated a wall for this object"},
        {"claim": "Each piece reads as a tower.", "field": "features",
         "decided_because": "the Taste asked for it"},
        {"claim": "It prints flat, without supports.", "field": "print",
         "decided_because": "no source stated a print stance"},
        {"claim": "A chess set is a board plus six piece types.",
         "field": "components",
         "sources": ["https://example.invalid/standards"]},
    ],
}

ANNOTATIONS = [
    {
        "type": "url_citation",
        "url_citation": {
            "url": "https://example.invalid/standards",
            "title": "Tournament equipment standards",
            "content": (
                "A tournament board measures 420 mm across, with a king of "
                "95 mm on a 40 mm base."
            ),
        },
    }
]


def completion(answer=None, annotations=None, *, content=None):
    message = {
        "role": "assistant",
        "content": (
            content
            if content is not None
            else json.dumps(answer if answer is not None else ANSWER)
        ),
    }
    if annotations is not None:
        message["annotations"] = annotations
    return json.dumps({"choices": [{"message": message}]}).encode("utf-8")


class RecordingTransport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "body": json.loads(body.decode("utf-8")),
                "timeout": timeout,
            }
        )
        response = self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]
        return response


def ok(body):
    return HttpResponse(200, {"Content-Type": "application/json"}, body)


class WishResearcherTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        inventor = self.root / "inventor"
        inventor.mkdir()
        (inventor / "TASTE.md").write_text(
            "---\n"
            "name: Test Inventor\n"
            "description: Architectural desk objects, never twee.\n"
            "---\n"
            "# Taste\n\nArchitectural desk objects.\n",
            encoding="utf-8",
        )
        self.taste = load_taste(inventor)
        self.blueprint = ToyBlueprint.for_lane("classics-made-yours")
        self.wish = Wish.create(
            "skyline-chess",
            "A really cool chess set with NYC building style",
            constraints={"audience": "grown-ups"},
        )

    def tearDown(self):
        self.temporary.cleanup()

    def request(self):
        return WishResearchRequest(self.wish, self.taste, self.blueprint, 1)

    def researcher(self, transport, **overrides):
        options = {
            "transport": transport,
            "sleep": lambda seconds: None,
            "clock": lambda: "2026-08-25T00:00:00Z",
        }
        options.update(overrides)
        return OpenAICompatibleWishResearcher(
            "https://research.example/v1", "key", "research-model", **options
        )


class ConstructionTest(WishResearcherTestCase):
    def test_a_missing_base_url_key_or_model_is_refused(self):
        for arguments in (
            ("", "key", "model"),
            ("https://research.example/v1", "", "model"),
            ("https://research.example/v1", "key", ""),
            ("   ", "key", "model"),
        ):
            with self.subTest(arguments=arguments), self.assertRaises(ContractError):
                OpenAICompatibleWishResearcher(*arguments)

    def test_a_base_url_that_is_not_http_is_refused(self):
        with self.assertRaises(ContractError):
            OpenAICompatibleWishResearcher("research.example", "key", "model")

    def test_bounds_must_be_positive_integers(self):
        for overrides in ({"timeout_seconds": 0}, {"max_attempts": 0}):
            with self.subTest(overrides=overrides), self.assertRaises(ContractError):
                OpenAICompatibleWishResearcher(
                    "https://research.example/v1", "key", "model", **overrides
                )

    def test_two_researchers_call_only_their_own_endpoint(self):
        first = RecordingTransport(ok(completion(annotations=ANNOTATIONS)))
        second = RecordingTransport(ok(completion(annotations=ANNOTATIONS)))
        self.researcher(first)(self.request())
        OpenAICompatibleWishResearcher(
            "https://other.example/v2",
            "other-key",
            "other-model",
            transport=second,
            clock=lambda: "2026-08-25T00:00:00Z",
        )(self.request())
        self.assertEqual(
            first.calls[0]["url"], "https://research.example/v1" + CHAT_COMPLETIONS_PATH
        )
        self.assertEqual(first.calls[0]["body"]["model"], "research-model")
        self.assertEqual(
            second.calls[0]["url"], "https://other.example/v2" + CHAT_COMPLETIONS_PATH
        )
        self.assertEqual(second.calls[0]["body"]["model"], "other-model")

    def test_from_env_requires_every_binding(self):
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch(
            "inventor_workshop.wish_researcher_openrouter.load_dotenv"
        ):
            with self.assertRaises(ContractError):
                OpenAICompatibleWishResearcher.from_env()

    def test_from_env_reads_the_three_documented_variables(self):
        environment = {
            ENV_WISH_RESEARCHER_BASE_URL: "https://env.example/v1",
            ENV_WISH_RESEARCHER_API_KEY: "env-key",
            ENV_WISH_RESEARCHER_MODEL: "env-model",
        }
        transport = RecordingTransport(ok(completion(annotations=ANNOTATIONS)))
        with mock.patch.dict("os.environ", environment, clear=True), mock.patch(
            "inventor_workshop.wish_researcher_openrouter.load_dotenv"
        ) as loader:
            researcher = OpenAICompatibleWishResearcher.from_env(
                transport=transport, clock=lambda: "2026-08-25T00:00:00Z"
            )
        loader.assert_called_once()
        researcher(self.request())
        self.assertEqual(
            transport.calls[0]["url"], "https://env.example/v1" + CHAT_COMPLETIONS_PATH
        )
        self.assertEqual(
            transport.calls[0]["headers"]["Authorization"], "Bearer env-key"
        )


class RequestShapeTest(WishResearcherTestCase):
    def setUp(self):
        super().setUp()
        self.transport = RecordingTransport(ok(completion(annotations=ANNOTATIONS)))
        self.researcher(self.transport)(self.request())
        self.call = self.transport.calls[0]

    def test_the_request_states_what_is_being_researched(self):
        prompt = self.call["body"]["messages"][0]["content"]
        self.assertIn(self.wish.objective, prompt)
        self.assertIn("grown-ups", prompt)
        self.assertIn(self.taste.description, prompt)
        self.assertIn("classics-made-yours", prompt)

    def test_the_request_asks_for_sourced_facts(self):
        prompt = self.call["body"]["messages"][0]["content"]
        self.assertIn("ATTRIBUTION IS REQUIRED", prompt)
        self.assertIn("decided_because", prompt)
        self.assertIn("no source", prompt)

    def test_web_search_is_requested(self):
        self.assertEqual(
            self.call["body"]["plugins"], [{"id": WEB_SEARCH_PLUGIN_ID}]
        )

    def test_the_request_carries_the_configured_credential(self):
        self.assertEqual(self.call["headers"]["Authorization"], "Bearer key")
        self.assertEqual(self.call["method"], "POST")

    def test_a_request_needs_a_wish_research_request(self):
        with self.assertRaises(ContractError):
            self.researcher(RecordingTransport(ok(completion())))("not a request")


class ParsingTest(WishResearcherTestCase):
    def test_a_well_formed_answer_becomes_a_breakdown(self):
        research = self.researcher(
            RecordingTransport(ok(completion(annotations=ANNOTATIONS)))
        )(self.request())
        self.assertEqual(research.object, "a skyline chess set")
        self.assertEqual(research.envelope_mm, (420.0, 420.0, 95.0))
        self.assertEqual(research.wall_mm, 2.2)
        self.assertEqual(
            tuple(item.key for item in research.components), ("board", "king")
        )
        self.assertEqual(len(research.sources), 1)
        source = research.sources[0]
        self.assertEqual(source.origin, "https://example.invalid/standards")
        self.assertEqual(source.retrieved_at, "2026-08-25T00:00:00Z")
        sourced = research.findings_for("envelope_mm")[0]
        self.assertEqual(sourced.source_ids, (source.id,))
        self.assertIsNone(sourced.decided_because)

    def test_an_answer_wrapped_in_prose_is_still_parsed(self):
        content = "Here is the breakdown:\n%s\nThat is all." % json.dumps(ANSWER)
        research = self.researcher(
            RecordingTransport(ok(completion(content=content, annotations=ANNOTATIONS)))
        )(self.request())
        self.assertEqual(research.category, "a printed edition of a known game")

    def test_an_unparseable_answer_fails_rather_than_returning_nothing(self):
        transport = RecordingTransport(
            ok(completion(content="I could not research this.", annotations=[]))
        )
        with self.assertRaisesRegex(ConceptProviderError, "could not be parsed"):
            self.researcher(transport)(self.request())

    def test_a_missing_field_fails_rather_than_being_defaulted(self):
        for name in ("object", "envelope_mm", "wall_mm", "components", "findings"):
            answer = dict(ANSWER)
            answer.pop(name)
            with self.subTest(name=name):
                transport = RecordingTransport(
                    ok(completion(answer, annotations=ANNOTATIONS))
                )
                with self.assertRaisesRegex(ConceptProviderError, name):
                    self.researcher(transport)(self.request())

    def test_a_cited_source_with_no_returned_material_fails(self):
        transport = RecordingTransport(ok(completion(annotations=[])))
        with self.assertRaisesRegex(
            ConceptProviderError, "returned no origin or excerpt"
        ):
            self.researcher(transport)(self.request())

    def test_a_citation_without_an_excerpt_is_not_recorded_as_a_source(self):
        annotations = [
            {
                "type": "url_citation",
                "url_citation": {
                    "url": "https://example.invalid/standards",
                    "title": "Tournament equipment standards",
                },
            }
        ]
        transport = RecordingTransport(ok(completion(annotations=annotations)))
        with self.assertRaisesRegex(
            ConceptProviderError, "returned no origin or excerpt"
        ):
            self.researcher(transport)(self.request())

    def test_an_underspecified_component_fails(self):
        answer = json.loads(json.dumps(ANSWER))
        del answer["components"][1]["interfaces"]
        transport = RecordingTransport(ok(completion(answer, annotations=ANNOTATIONS)))
        with self.assertRaisesRegex(ConceptProviderError, "states no interfaces"):
            self.researcher(transport)(self.request())

    def test_a_finding_with_both_a_source_and_a_decision_fails(self):
        answer = json.loads(json.dumps(ANSWER))
        answer["findings"][3]["sources"] = ["https://example.invalid/standards"]
        transport = RecordingTransport(ok(completion(answer, annotations=ANNOTATIONS)))
        with self.assertRaisesRegex(ConceptProviderError, "is unusable"):
            self.researcher(transport)(self.request())

    def test_a_breakdown_leaving_a_field_unattributed_fails(self):
        answer = json.loads(json.dumps(ANSWER))
        answer["findings"] = [
            item for item in answer["findings"] if item["field"] != "wall_mm"
        ]
        transport = RecordingTransport(ok(completion(answer, annotations=ANNOTATIONS)))
        with self.assertRaisesRegex(ConceptProviderError, "not a usable breakdown"):
            self.researcher(transport)(self.request())

    def test_a_response_that_is_not_a_completion_fails(self):
        for body in (
            b"not json",
            json.dumps({"choices": []}).encode("utf-8"),
            json.dumps({"choices": [{"message": {}}]}).encode("utf-8"),
        ):
            with self.subTest(body=body[:20]), self.assertRaises(ConceptProviderError):
                self.researcher(RecordingTransport(ok(body)))(self.request())


class FailureTest(WishResearcherTestCase):
    def test_a_non_retryable_client_error_fails_immediately(self):
        transport = RecordingTransport(HttpResponse(401, {}, b"no"))
        with self.assertRaisesRegex(ConceptProviderError, "HTTP 401"):
            self.researcher(transport)(self.request())
        self.assertEqual(len(transport.calls), 1)

    def test_a_rate_limit_is_retried_then_fails(self):
        transport = RecordingTransport(HttpResponse(429, {}, b"slow down"))
        with self.assertRaisesRegex(ConceptProviderError, "HTTP 429"):
            self.researcher(transport, max_attempts=3)(self.request())
        self.assertEqual(len(transport.calls), 3)

    def test_a_server_error_is_retried_then_succeeds(self):
        transport = RecordingTransport(
            HttpResponse(503, {}, b"unavailable"),
            ok(completion(annotations=ANNOTATIONS)),
        )
        research = self.researcher(transport, max_attempts=3)(self.request())
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(research.object, "a skyline chess set")

    def test_an_oversized_response_is_rejected(self):
        def oversized(method, url, headers, body, timeout):
            raise ConceptProviderError("response exceeds the 16-byte limit")

        with self.assertRaisesRegex(ConceptProviderError, "exceeds"):
            self.researcher(oversized)(self.request())


class NotWiredInTest(WishResearcherTestCase):
    def test_importing_the_adapter_installs_nothing(self):
        from inventor_workshop.concept import DefaultConcept
        from inventor_workshop.jobs import ConceptContext, WaitingFor

        context = ConceptContext(
            self.wish,
            self.taste,
            self.blueprint,
            1,
            (self.root / "concept").absolute(),
            (),
            1,
        )
        with self.assertRaises(WaitingFor) as caught:
            DefaultConcept()(context)
        self.assertIn(
            "wish-research", [need.capability for need in caught.exception.needs]
        )


if __name__ == "__main__":
    unittest.main()
