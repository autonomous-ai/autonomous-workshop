"""Architecture proof that pure Concept code cannot acquire host authority."""

import ast
import copy
import hashlib
import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.concept.native import ConceptTree, DerivedWish
from workshop.concept.native_gate import evaluate_concept_brief
from workshop.wish import Wish


REPOSITORY = Path(__file__).resolve().parents[2]
CONCEPT_ROOT = REPOSITORY / "src/workshop/concept"
FORBIDDEN_PREFIXES = (
    "workshop.workflow",
    "workshop.runtime",
    "workshop.integrations",
)


def forbidden_imports(source):
    tree = ast.parse(source)
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return tuple(
        name for name in names if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
    )


class ConceptArchitectureTest(unittest.TestCase):
    def test_static_dependency_boundary_rejects_representative_host_imports(self):
        self.assertEqual(
            forbidden_imports(
                "from workshop.workflow import native_run\n"
                "import workshop.runtime.credentials\n"
                "from workshop.integrations.factory import Factory\n"
            ),
            (
                "workshop.workflow",
                "workshop.runtime.credentials",
                "workshop.integrations.factory",
            ),
        )
        for path in sorted(CONCEPT_ROOT.glob("*.py")):
            with self.subTest(path=path.name):
                self.assertEqual(forbidden_imports(path.read_text(encoding="utf-8")), ())

    def test_evaluator_has_no_network_credential_or_write_side_effect(self):
        wish = Wish.create("p1", "a tactile moon lamp")
        brief = {
            "object": "moon lamp",
            "category": "lighting",
            "envelope_mm": {"length_mm": 10, "width_mm": 10, "height_mm": 10},
            "wall_thickness_mm": 1,
            "print_stance": {
                "orientation": "upright",
                "supports_required": False,
                "support_notes": "none",
            },
            "features": [{"id": "crater", "text": "tactile crater"}],
            "fit_target": None,
            "components": [{
                "key": "dome", "name": "Dome", "purpose": "cover",
                "form": "shell",
                "dimensions_mm": {"length_mm": 10, "width_mm": 10, "height_mm": 10},
                "placement": "centered", "interfaces": "rests on base",
            }],
            "facts": [
                {"field": name, "source_id": None, "assumption_reason": "authored decision"}
                for name in (
                    "object", "category", "envelope_mm", "wall_thickness_mm",
                    "print_stance", "features.crater", "components.dome",
                )
            ],
        }
        excerpt = "bounded source"
        research = {
            "sources": [{
                "id": "s1", "origin": "https://example.test",
                "excerpt": excerpt,
                "excerpt_sha256": hashlib.sha256(
                    json.dumps(excerpt, separators=(",", ":")).encode()
                ).hexdigest(),
                "retrieved_at": "2026-08-30T00:00:00+00:00",
            }],
            "findings": [{"finding": "bounded", "source_ids": ["s1"]}],
        }
        prompts = {
            "front": {"instruction": "front", "references": []},
            "top": {"instruction": "top", "references": ["front"]},
            "bottom": {"instruction": "bottom", "references": ["front"]},
            "exploded": {
                "instruction": "Dome separated", "references": ["front", "top", "bottom"]
            },
            "components": {"dome": {"instruction": "Dome", "references": ["front"]}},
        }
        descriptor = {
            "front": {"path": "images/front.png"},
            "top": {"path": "images/top.png"},
            "bottom": {"path": "images/bottom.png"},
            "exploded": {"path": "images/exploded.png"},
            "components": {"dome": {"path": "images/components/dome.png"}},
        }
        derived = DerivedWish(
            wish_sha256="0" * 64,
            product_id=wish.product_id,
            objective=wish.objective,
            context={},
            constraints={"bounded": True},
        )
        tree = ConceptTree(
            root=Path("unused"), manifest=None, brief=brief, research=research,
            drawing_instructions=prompts, descriptor=descriptor, derived_wish=derived,
        )
        before = copy.deepcopy((brief, research, prompts, descriptor))
        with mock.patch.object(socket, "create_connection", side_effect=AssertionError("network")), \
             mock.patch("os.getenv", side_effect=AssertionError("credential")), \
             mock.patch.object(Path, "write_bytes", side_effect=AssertionError("write")), \
             mock.patch.object(Path, "write_text", side_effect=AssertionError("write")):
            evidence = evaluate_concept_brief(tree, wish=wish)
        self.assertEqual(evidence["checks_kind"], "concept-structure-v1")
        self.assertEqual((brief, research, prompts, descriptor), before)
        self.assertNotIn("gate", evidence)
        self.assertNotIn("transition", evidence)


if __name__ == "__main__":
    unittest.main()
