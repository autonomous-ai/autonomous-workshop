"""``DefaultConcept`` driven by the real adapters, against faked HTTP transports.

Mirrors ``tests/test_concept_pipeline.py``'s fixture-based coverage, but
proves the ``ConceptArtist``/``ExplodeInspector`` callable contracts are
satisfied by ``OpenRouterConceptArtist`` and
``OpenAICompatibleExplodeInspector`` themselves rather than by the swatch
fixture — with a faked HTTP layer standing in for the network, never a real
call.
"""

import base64
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop._http import HttpResponse
from inventor_workshop.concept import DefaultConcept
from inventor_workshop.errors import ContractError
from inventor_workshop.concept_artist_openrouter import OpenRouterConceptArtist
from inventor_workshop.concept_explode_inspector import (
    OpenAICompatibleExplodeInspector,
)
from inventor_workshop.jobs import CONCEPT_OVERALL_ROLES, ConceptContext
from inventor_workshop.make import Wish
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint
from tools.wish_research_fixture import FixtureWishResearcher


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGA"
    "hKmMIQAAAABJRU5ErkJggg=="
)

COMPONENTS = [
    {
        "key": "body",
        "name": "Body",
        "purpose": "Holds the mechanism.",
        "form": "a rounded shell with one flat base",
        "dimensions_mm": [60.0, 60.0, 18.0],
        "placement": "the base of the assembly",
        "interfaces": "receives the cap on its upper rim",
    },
    {
        "key": "cap",
        "name": "Cap",
        "purpose": "Closes the body.",
        "form": "a shallow dome with a knurled rim",
        "dimensions_mm": [58.0, 58.0, 9.0],
        "placement": "on top of the body",
        "interfaces": "snaps onto the body rim",
    },
]


def _image_transport(method, url, headers, body, timeout):
    payload = json.dumps(
        {"data": [{"b64_json": base64.b64encode(PNG_1X1).decode("ascii")}]}
    ).encode("utf-8")
    return HttpResponse(200, {}, payload)


def _all_components_visible_transport(component_keys):
    def transport(method, url, headers, body, timeout):
        answer = json.dumps(list(component_keys))
        chunk = json.dumps({"choices": [{"index": 0, "delta": {"content": answer}}]})
        payload = ("data: %s\n\ndata: [DONE]\n\n" % chunk).encode("utf-8")
        return HttpResponse(200, {}, payload)

    return transport


class RealProvidersConceptPipelineTest(unittest.TestCase):
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
        self.blueprint = ToyBlueprint.for_lane("moving-machines")
        self.wish = Wish.create(
            "rhythm-top",
            "A delightful desk spinner that reveals a changing beat",
            constraints={
                "envelope_mm": [60.0, 60.0, 30.0],
                "wall_mm": 2.0,
                "components": COMPONENTS,
            },
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_default_concept_produces_a_sealed_concept_through_real_adapters(self):
        artist = OpenRouterConceptArtist("key", transport=_image_transport)
        component_keys = [item["key"] for item in COMPONENTS]
        inspector = OpenAICompatibleExplodeInspector(
            "https://vision.example/v1",
            "key",
            "vision-model",
            transport=_all_components_visible_transport(component_keys),
        )
        job = DefaultConcept(
            artist, inspector, wish_researcher=FixtureWishResearcher()
        )
        context = ConceptContext(
            self.wish,
            self.taste,
            self.blueprint,
            1,
            (self.root / "concept").absolute(),
            (),
            1,
            None,
            0,
        )

        concept = job(context)

        for role in CONCEPT_OVERALL_ROLES:
            self.assertIn(role, concept.overall)
            self.assertTrue((concept.root / concept.overall[role]).is_file())
        self.assertEqual(set(concept.components), set(component_keys))
        for key in component_keys:
            self.assertTrue((concept.root / concept.components[key]).is_file())
        self.assertTrue(concept.concept_sha256)

    def test_incomplete_exploded_view_regenerates_then_fails(self):
        artist = OpenRouterConceptArtist("key", transport=_image_transport)
        # Only "body" is ever reported visible, so "cap" never clears the
        # completeness check even after the one allowed regeneration.
        inspector = OpenAICompatibleExplodeInspector(
            "https://vision.example/v1",
            "key",
            "vision-model",
            transport=_all_components_visible_transport(["body"]),
        )
        job = DefaultConcept(
            artist, inspector, wish_researcher=FixtureWishResearcher()
        )
        context = ConceptContext(
            self.wish,
            self.taste,
            self.blueprint,
            1,
            (self.root / "concept").absolute(),
            (),
            1,
            None,
            0,
        )

        with self.assertRaises(ContractError):
            job(context)


if __name__ == "__main__":
    unittest.main()
