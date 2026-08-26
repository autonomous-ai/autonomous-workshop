import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import InventedV2
from workshop.make.native import NativeMade
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    PersonaCatalog,
    PersonaCatalogEntry,
)
from workshop.playtest.native import NativePlaytestCheck, NativePlaytested
from workshop.product import ToyBlueprint
from workshop.release.native import (
    NATIVE_RELEASE_MANUAL_PATH,
    NATIVE_RELEASE_PACKAGE_ROOT,
    NATIVE_RELEASE_PATH,
    NATIVE_RELEASE_PRODUCT_PATH,
    NativeRelease,
    read_native_release,
)


def _canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


class NativeReleaseTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_root = Path(self.temporary.name).resolve()
        self.blueprint = ToyBlueprint.for_lane("little-worlds")
        catalog = PersonaCatalog(
            (PersonaCatalogEntry("eve", "little-worlds", "b" * 64, "c" * 64),)
        )
        self.assignment = NativeMatchAssignment(
            wish_sha256="a" * 64,
            persona_catalog_sha256=catalog.catalog_sha256,
            selected_inventor_id="eve",
            selected_lane="little-worlds",
            selected_manifest_sha256="b" * 64,
            selected_taste_sha256="c" * 64,
            blueprint_sha256=self.blueprint.sha256,
            ranking=(
                MatchRankingEntry(
                    "eve", "The Wish is a specific place made into a tiny world."
                ),
            ),
        )
        self.invented = InventedV2(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            lane="little-worlds",
            concept={"title": "Moon Nook", "summary": "A tiny lunar observatory."},
            research={
                "sources": [{"url": "https://example.test/moon", "claim": "scale"}]
            },
        )
        self.made = self._make_product()
        self.playtested = self._make_playtest()

    def _make_product(self):
        root = self.run_root / "artifacts/make/r0001/product"
        (root / "cad/project").mkdir(parents=True)
        (root / "validation").mkdir()
        product = {
            "title": "Moon Nook",
            "summary": "A tiny lunar observatory.",
            "lane": "little-worlds",
            "components": ["observatory shell", "moon rover"],
            "instructions": "Arrange the rover and explore the observatory.",
            "limitations": ["AI-simulated playtest only"],
        }
        product_bytes = _canonical(product)
        receipt = _canonical({"ok": True, "validator": "cad-final"})
        (root / "product.json").write_bytes(product_bytes)
        (root / "cad/project/moon.step.py").write_text("pass\n", encoding="utf-8")
        (root / "cad/project/moon.step").write_bytes(b"ISO-10303-21;\n")
        (root / "cad/project/moon.stl").write_bytes(
            b"solid moon\nendsolid moon\n"
        )
        (root / "validation/cad-build.json").write_bytes(receipt)
        return NativeMade(
            round=1,
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            invented_sha256=self.invented.invented_sha256,
            product_root="artifacts/make/r0001/product",
            cad_project_path="cad/project",
            product_manifest=build_artifact_manifest(
                root, created_at="content-addressed"
            ),
            product=product,
            product_json_sha256=_sha(product_bytes),
            cad_verification_path="validation/cad-build.json",
            cad_verification_sha256=_sha(receipt),
        )

    def _make_playtest(self):
        root = self.run_root / "artifacts/playtest/r0001/evidence"
        root.mkdir(parents=True)
        checks = []
        for check_id in self.blueprint.required_capabilities("playtest"):
            evidence = _canonical({"check": check_id, "ok": True})
            path = "%s.json" % check_id
            (root / path).write_bytes(evidence)
            checks.append(
                NativePlaytestCheck(
                    check_id=check_id,
                    passed=True,
                    evaluator="workshop-host",
                    evaluator_version="1.0.0",
                    config_sha256="d" * 64,
                    evidence_ref=path,
                    evidence_sha256=_sha(evidence),
                    observed_at="2026-08-26T00:00:00Z",
                    observations={
                        "ok": True,
                        "evidence_class": "ai-simulation",
                        "claims": ["%s passed." % check_id],
                    },
                )
            )
        return NativePlaytested(
            round=1,
            made_sha256=self.made.made_sha256,
            product_artifact_sha256=self.made.product_manifest.artifact_sha256,
            blueprint_sha256=self.blueprint.sha256,
            evidence_root="artifacts/playtest/r0001/evidence",
            evidence_manifest=build_artifact_manifest(
                root, created_at="content-addressed"
            ),
            checks=tuple(checks),
            feedback=(),
            verdict="pass",
        )

    def _claims(self):
        return {
            check.check_id: {
                "passed": check.passed,
                "evidence_class": check.observations["evidence_class"],
                "claims": list(check.observations["claims"]),
                "evidence_ref": check.evidence_ref,
                "evidence_sha256": check.evidence_sha256,
                "evaluator": check.evaluator,
                "evaluator_version": check.evaluator_version,
            }
            for check in self.playtested.checks
        }

    def _release(self, *, product_overrides=None, extra_files=None, **overrides):
        root = self.run_root / NATIVE_RELEASE_PACKAGE_ROOT
        root.mkdir(parents=True, exist_ok=True)
        manual = (
            "# Moon Nook\n\n"
            "Arrange the rover and explore the observatory.\n\n"
            "AI-simulated playtest evidence is disclosed in product.json.\n"
        )
        (root / NATIVE_RELEASE_MANUAL_PATH).write_text(manual, encoding="utf-8")
        product = {
            "schema_version": 2,
            "kind": "workshop.release-package",
            "status": "facts-ready",
            "title": "Moon Nook",
            "summary": "A tiny lunar observatory.",
            "lane": "little-worlds",
            "what_arrives": ["observatory shell", "moon rover"],
            "limitations": ["AI-simulated playtest only"],
            "product_artifact_sha256": self.made.product_manifest.artifact_sha256,
            "playtest_evidence_artifact_sha256": (
                self.playtested.evidence_manifest.artifact_sha256
            ),
            "claims": self._claims(),
            "factory_enrichment": {
                "copy_owner": "factory",
                "media_owner": "factory",
                "status": "pending",
            },
        }
        product.update(product_overrides or {})
        product_bytes = _canonical(product)
        (root / NATIVE_RELEASE_PRODUCT_PATH).write_bytes(product_bytes)
        for path, content in (extra_files or {}).items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        values = {
            "round": 1,
            "made_sha256": self.made.made_sha256,
            "playtested_sha256": self.playtested.playtested_sha256,
            "product_artifact_sha256": (
                self.made.product_manifest.artifact_sha256
            ),
            "playtest_evidence_artifact_sha256": (
                self.playtested.evidence_manifest.artifact_sha256
            ),
            "package_root": NATIVE_RELEASE_PACKAGE_ROOT,
            "package_manifest": build_artifact_manifest(
                root, created_at="content-addressed"
            ),
            "manual_path": NATIVE_RELEASE_MANUAL_PATH,
            "product_json_path": NATIVE_RELEASE_PRODUCT_PATH,
            "product_json_sha256": _sha(product_bytes),
            "product": product,
        }
        values.update(overrides)
        return NativeRelease(**values)

    def _write_contract(self, release, content=None):
        path = self.run_root / NATIVE_RELEASE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_canonical(release.to_dict()) if content is None else content)
        return path

    def _rebuild_release(self, release, **overrides):
        values = release.to_dict()
        values.pop("release_sha256")
        values["package_manifest"] = release.package_manifest
        values.update(overrides)
        return NativeRelease(**values)

    def test_round_trip_rehashes_full_tree_and_exposes_host_inputs(self):
        release = self._release(
            extra_files={"attribution.json": _canonical({"sources": ["creator"]})}
        )
        self._write_contract(release)

        loaded = read_native_release(self.run_root)
        package = loaded.validate_package_tree(
            self.run_root, self.made, self.playtested
        )

        self.assertEqual(loaded, NativeRelease.from_mapping(release.to_dict()))
        self.assertEqual(package.root, self.run_root / NATIVE_RELEASE_PACKAGE_ROOT)
        self.assertEqual(package.manifest, release.package_manifest)
        self.assertEqual(package.manual_path, "MANUAL.md")
        self.assertEqual(package.made.artifact_sha256, release.product_artifact_sha256)
        self.assertTrue(package.playtested.passed)
        self.assertEqual(dict(package.claims), dict(release.claims))
        self.assertEqual(
            dict(package.factory_enrichment),
            {"copy_owner": "factory", "media_owner": "factory", "status": "pending"},
        )
        serialized = json.dumps(release.to_dict(), sort_keys=True)
        for forbidden in ("credentials", "factory_receipt", "site_receipt"):
            self.assertNotIn(forbidden, serialized)

    def test_rejects_media_symlinks_and_path_escape(self):
        release = self._release()
        with self.assertRaisesRegex(ContractError, "package_root is not canonical"):
            self._rebuild_release(release, package_root="../outside")

        with self.assertRaisesRegex(ContractError, "cannot contain media files"):
            self._release(extra_files={"hero.png": b"not really an image"})
        (self.run_root / NATIVE_RELEASE_PACKAGE_ROOT / "hero.png").unlink()

        release = self._release()
        manual = self.run_root / NATIVE_RELEASE_PACKAGE_ROOT / "MANUAL.md"
        outside = self.run_root / "outside-manual.md"
        outside.write_text("outside\n", encoding="utf-8")
        manual.unlink()
        manual.symlink_to(outside)
        with self.assertRaisesRegex(ArtifactError, "symlink"):
            release.validate_package_tree(self.run_root, self.made, self.playtested)

        manual.unlink()
        manual.write_text("restored\n", encoding="utf-8")
        contract = self._write_contract(release)
        external_contract = self.run_root / "outside-release.json"
        external_contract.write_bytes(_canonical(release.to_dict()))
        contract.unlink()
        contract.symlink_to(external_contract)
        with self.assertRaisesRegex(ArtifactError, "regular file"):
            read_native_release(self.run_root)

    def test_rejects_mismatched_product_and_playtest_bindings(self):
        release = self._release()
        with self.assertRaisesRegex(ContractError, "different Workshop inputs"):
            self._rebuild_release(release, made_sha256="0" * 64).assert_context(
                self.made, self.playtested
            )
        with self.assertRaisesRegex(ContractError, "identifies another product"):
            self._rebuild_release(release, product_artifact_sha256="1" * 64)
        with self.assertRaisesRegex(ContractError, "other Playtest evidence"):
            self._rebuild_release(
                release, playtest_evidence_artifact_sha256="2" * 64
            )

        other_playtest = replace(
            self.playtested,
            checks=tuple(
                replace(check, config_sha256="e" * 64)
                for check in self.playtested.checks
            ),
        )
        with self.assertRaisesRegex(ContractError, "different Workshop inputs"):
            release.assert_context(self.made, other_playtest)

    def test_rejects_noncanonical_invalid_json_and_changed_bytes(self):
        release = self._release(
            extra_files={"notes.json": b'{\n  "note": "pretty"\n}\n'}
        )
        with self.assertRaisesRegex(ContractError, "canonical JSON encoding"):
            release.validate_package_tree(self.run_root, self.made, self.playtested)

        release = self._release()
        contract = self._write_contract(
            release,
            (json.dumps(release.to_dict(), indent=2, sort_keys=True) + "\n").encode(),
        )
        with self.assertRaisesRegex(ContractError, "canonical JSON encoding"):
            read_native_release(self.run_root)

        value = release.to_dict()
        duplicate = (
            '{"kind":"%s","kind":"%s"}'
            % (value["kind"], value["kind"])
        ).encode()
        contract.write_bytes(duplicate)
        with self.assertRaisesRegex(ContractError, "strict UTF-8 JSON"):
            read_native_release(self.run_root)

        self._write_contract(release)
        manual = self.run_root / NATIVE_RELEASE_PACKAGE_ROOT / "MANUAL.md"
        manual.write_text("# changed after sealing\n", encoding="utf-8")
        with self.assertRaisesRegex(ArtifactError, "differs from its manifest"):
            release.validate_package_tree(self.run_root, self.made, self.playtested)


if __name__ == "__main__":
    unittest.main()
