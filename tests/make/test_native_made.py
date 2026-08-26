import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import NativeInvented
from workshop.make.native import NativeMade
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    InventorRoster,
    InventorRosterEntry,
)
from workshop.product import ToyBlueprint


def _sha(value):
    return hashlib.sha256(value).hexdigest()


class NativeMadeTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_root = Path(self.temporary.name).resolve()
        self.wish_sha256 = "a" * 64
        self.roster = InventorRoster(
            (
                InventorRosterEntry(
                    "eve",
                    ".codex/agents/eve.toml",
                    "b" * 64,
                    "c" * 64,
                    "d" * 64,
                ),
            )
        )
        self.assignment = NativeMatchAssignment(
            wish_sha256=self.wish_sha256,
            inventor_roster_sha256=self.roster.roster_sha256,
            selected_inventor_id="eve",
            selected_agent_path=".codex/agents/eve.toml",
            selected_agent_sha256="b" * 64,
            selected_source_manifest_sha256="c" * 64,
            selected_taste_sha256="d" * 64,
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=(
                MatchRankingEntry(
                    "eve", "The Wish is a specific place made into a tiny world."
                ),
            ),
        )
        self.invented = NativeInvented(
            wish_sha256=self.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept={"title": "Moon Nook", "summary": "A tiny lunar observatory."},
            research={"sources": [{"url": "https://example.test/moon", "claim": "scale"}]},
        )

    def _made(self):
        product_root = self.run_root / "artifacts/make/r0001/product"
        project = product_root / "cad/project"
        validation = product_root / "validation"
        project.mkdir(parents=True)
        validation.mkdir()
        product = {
            "title": "Moon Nook",
            "summary": "A tiny lunar observatory.",
            "components": ["observatory"],
            "instructions": "Place it on a desk and explore the craters.",
            "limitations": ["Digital checks only"],
        }
        product_bytes = (
            json.dumps(product, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        (product_root / "product.json").write_bytes(product_bytes)
        (project / "moon.step.py").write_text("def gen_step():\n    return None\n")
        (project / "moon.step").write_bytes(b"ISO-10303-21;\n")
        (project / "moon.stl").write_bytes(b"solid moon\nendsolid moon\n")
        verification = b'{"ok":true,"validator":"cad-final"}\n'
        (validation / "cad-build.json").write_bytes(verification)
        manifest = build_artifact_manifest(
            product_root, created_at="content-addressed"
        )
        made = NativeMade(
            round=1,
            wish_sha256=self.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            invented_sha256=self.invented.invented_sha256,
            product_root="artifacts/make/r0001/product",
            cad_project_path="cad/project",
            product_manifest=manifest,
            product=product,
            product_json_sha256=_sha(product_bytes),
            cad_verification_path="validation/cad-build.json",
            cad_verification_sha256=_sha(verification),
        )
        return made, product_root

    def test_round_trip_rehashes_tree_and_binds_upstream(self):
        made, product_root = self._made()

        rebuilt = NativeMade.from_mapping(made.to_dict())
        rebuilt.assert_context(self.assignment, self.invented, expected_round=1)
        canonical = rebuilt.validate_product_tree(self.run_root)

        self.assertEqual(canonical.artifact_root, product_root)
        self.assertEqual(canonical.artifact_sha256, made.product_manifest.artifact_sha256)
        self.assertEqual(canonical.product["title"], "Moon Nook")

    def test_tampered_tree_or_context_fails_closed(self):
        made, product_root = self._made()
        (product_root / "cad/project/moon.stl").write_bytes(b"changed")
        with self.assertRaisesRegex(ArtifactError, "differs from its manifest"):
            made.validate_product_tree(self.run_root)
        with self.assertRaisesRegex(ContractError, "different Workshop inputs"):
            made.assert_context(self.assignment, self.invented, expected_round=2)


if __name__ == "__main__":
    unittest.main()
