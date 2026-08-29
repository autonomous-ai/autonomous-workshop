import hashlib
import io
import json
import os
import shutil
import tempfile
import unittest
import zlib
from dataclasses import replace
from pathlib import Path
from unittest import mock

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ArtifactError, ContractError, StateConflict
from workshop.invent.native import NativeInvented
from workshop.make.native import NativeMade
from workshop.make.revision import (
    MakeInventRevisionFeedback,
    NativeMakeInventRevision,
)
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    InventorRoster,
    InventorRosterEntry,
)
from workshop.playtest.contracts import Feedback
from workshop.playtest.native import NativePlaytestCheck, NativePlaytested
from workshop.product import ToyBlueprint
from workshop.release.native import (
    NATIVE_RELEASE_PLAYTEST_OMISSION_PATH,
    MAX_NATIVE_RELEASE_MANUAL_BYTES,
    NATIVE_RELEASE_LEGACY_MANUAL_PATH,
    NATIVE_RELEASE_MANUAL_PATH,
    NATIVE_RELEASE_PACKAGE_ROOT,
    NATIVE_RELEASE_PATH,
    NATIVE_RELEASE_PRODUCT_PATH,
    NativeRelease,
    direct_release_claims,
    playtest_omission_record,
    playtest_omission_sha256,
    read_native_release,
    validate_release_product,
)
from workshop.release.public_example import _public_hero_path, materialize_public_example
from workshop.release.public_archive import (
    _redact_public_local_paths,
    build_public_archive_manifest,
)
from workshop.release.verification import (
    DIGITALLY_VERIFIED,
    PHYSICALLY_VERIFIED,
    PRODUCT_VERIFICATION_PATH,
    ProductVerification,
    materialize_digital_verification,
    read_product_verification,
    try_materialize_digital_verification,
)
from workshop.runtime import Receipt


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


def _token_summary():
    return {
        "schema_version": 2,
        "kind": "autonomous-workshop.native-token-summary",
        "status": "measured",
        "turns": {"total": 1, "measured": 1, "unmeasured": 0},
        "input_tokens": 100,
        "output_tokens": 25,
        "stages": {
            name: {
                "status": "measured" if name == "make" else "pending",
                "turns": 1 if name == "make" else 0,
                "measured_turns": 1 if name == "make" else 0,
                "unmeasured_turns": 0,
                "input_tokens": 100 if name == "make" else 0,
                "output_tokens": 25 if name == "make" else 0,
            }
            for name in ("match", "invent", "make", "playtest", "release")
        },
    }


def _manual_pdf(
    *,
    page_count=1,
    declared_page_count=None,
    repeated_page_references=None,
    box=(0, 0, 297, 420),
    text=(
        "Moon Nook field manual. Arrange the rover, inspect every part, "
        "and begin a safe tabletop expedition."
    ),
    catalog_entries=b"",
    page_entries=b"",
    resource_entries=b"",
    content_suffix=b"",
    extra_objects=None,
):
    def pdf_string(value):
        return (
            value.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .encode("ascii")
        )

    objects = {}
    page_ids = [4 + index * 2 for index in range(page_count)]
    kids = page_ids
    if repeated_page_references is not None:
        kids = [page_ids[0]] * repeated_page_references
    declared = page_count if declared_page_count is None else declared_page_count
    objects[1] = (
        b"<< /Type /Catalog /Pages 2 0 R " + catalog_entries + b" >>"
    )
    objects[2] = (
        b"<< /Type /Pages /Count "
        + str(declared).encode("ascii")
        + b" /Kids ["
        + " ".join("%d 0 R" % page_id for page_id in kids).encode("ascii")
        + b"] >>"
    )
    objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    box_bytes = b" ".join(str(value).encode("ascii") for value in box)
    for index, page_id in enumerate(page_ids, start=1):
        content_id = page_id + 1
        page_text = "%s Page %d." % (text, index) if text else ""
        stream = (
            b"BT /F1 12 Tf 24 360 Td ("
            + pdf_string(page_text)
            + b") Tj ET\n"
            + content_suffix
        )
        objects[page_id] = (
            b"<< /Type /Page /Parent 2 0 R /MediaBox ["
            + box_bytes
            + b"] /Resources << /Font << /F1 3 0 R >> "
            + resource_entries
            + b" >> /Contents "
            + str(content_id).encode("ascii")
            + b" 0 R "
            + page_entries
            + b" >>"
        )
        objects[content_id] = (
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"endstream"
        )
    objects.update(extra_objects or {})

    result = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = {0: 0}
    for object_number in range(1, max(objects, default=0) + 1):
        offsets[object_number] = len(result)
        result.extend(("%d 0 obj\n" % object_number).encode("ascii"))
        result.extend(objects[object_number])
        result.extend(b"\nendobj\n")
    xref = len(result)
    result.extend(("xref\n0 %d\n" % len(offsets)).encode("ascii"))
    result.extend(b"0000000000 65535 f \n")
    for object_number in range(1, len(offsets)):
        result.extend(
            ("%010d 00000 n \n" % offsets[object_number]).encode("ascii")
        )
    result.extend(
        (
            "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(offsets), xref)
        ).encode("ascii")
    )
    return bytes(result)


class NativeReleaseTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_root = Path(self.temporary.name).resolve()
        self.blueprint = ToyBlueprint()
        self.wish = {
            "schema_version": 1,
            "product_id": "wish-moon-nook",
            "objective": "Create a tiny lunar observatory toy.",
            "constraints": {},
            "context": {"source": "test"},
        }
        self.wish_bytes = _canonical(self.wish)
        roster = InventorRoster(
            (
                InventorRosterEntry(
                    inventor_id="eve",
                    agent_path=".codex/agents/eve.toml",
                    agent_sha256="b" * 64,
                    source_manifest_sha256="c" * 64,
                    taste_sha256="d" * 64,
                ),
            )
        )
        self.assignment = NativeMatchAssignment(
            wish_sha256=_sha(self.wish_bytes),
            inventor_roster_sha256=roster.roster_sha256,
            selected_inventor_id="eve",
            selected_agent_path=".codex/agents/eve.toml",
            selected_agent_sha256="b" * 64,
            selected_source_manifest_sha256="c" * 64,
            selected_taste_sha256="d" * 64,
            blueprint_sha256=self.blueprint.sha256,
            ranking=(
                MatchRankingEntry(
                    "eve", "The Wish is a specific place made into a tiny world."
                ),
            ),
        )
        self.invented = NativeInvented(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept={
                "title": "Moon Nook",
                "summary": "A tiny lunar observatory.",
                "components": [
                    {"name": "observatory shell"},
                    {"name": "moon rover"},
                ],
            },
            research={
                "sources": [{"url": "https://example.test/moon", "claim": "scale"}]
            },
        )
        self.made = self._make_product()
        self.playtested = self._make_playtest()
        stage_files = {
            "artifacts/wish/wish.json": self.wish_bytes,
            "artifacts/invent/assignment.json": _canonical(
                self.assignment.to_dict()
            ),
            "artifacts/invent/invented.json": _canonical(self.invented.to_dict()),
            "artifacts/make/r0001/made.json": _canonical(self.made.to_dict()),
            "artifacts/playtest/r0001/playtested.json": _canonical(
                self.playtested.to_dict()
            ),
        }
        for relative, content in stage_files.items():
            path = self.run_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def test_public_archive_redacts_host_local_path_prefixes(self):
        source = (
            "run=%s/artifacts/make home=%s/code/workshop relative=make/source\n"
            % (self.run_root, Path.home())
        ).encode("utf-8")

        public, redactions = _redact_public_local_paths(
            source,
            run_root=self.run_root,
        )

        self.assertNotIn(str(self.run_root).encode("utf-8"), public)
        self.assertNotIn(str(Path.home()).encode("utf-8"), public)
        self.assertIn(b"<WORKSHOP_RUN>/artifacts/make", public)
        self.assertIn(b"<HOME>/code/workshop", public)
        self.assertEqual(
            redactions,
            ("workshop-run-root", "home-directory"),
        )

    def _make_product(self):
        root = self.run_root / "artifacts/make/r0001/product"
        (root / "cad/project").mkdir(parents=True)
        (root / "cad/project/snap").mkdir()
        (root / "validation").mkdir()
        (root / "validation/renders").mkdir()
        assembled = b"solid assembled\nendsolid assembled\n"
        printable = b"solid moon-body\nendsolid moon-body\n"
        product = {
            "title": "Moon Nook",
            "summary": "A tiny lunar observatory.",
            "components": ["observatory shell", "moon rover"],
            "instructions": "Arrange the rover and explore the observatory.",
            "limitations": ["AI-simulated playtest only"],
            "cad": {
                "assembled_stl": {
                    "path": "assembled.stl",
                    "bytes": len(assembled),
                    "sha256": _sha(assembled),
                }
            },
            "inventory": {
                "parts": [
                    {
                        "id": "moon-body",
                        "quantity": 2,
                        "stl": {
                            "path": "cad/project/moon-body.stl",
                            "bytes": len(printable),
                            "sha256": _sha(printable),
                        },
                    }
                ]
            },
        }
        product_bytes = _canonical(product)
        receipt = _canonical({"ok": True, "validator": "cad-final"})
        (root / "product.json").write_bytes(product_bytes)
        (root / "cad/project/moon.step.py").write_text("pass\n", encoding="utf-8")
        (root / "cad/project/__init__.py").write_bytes(b"")
        (root / "cad/project/README.md").write_text(
            "# Parametric Moon Nook\n", encoding="utf-8"
        )
        (root / "cad/project/moon.step").write_bytes(b"ISO-10303-21;\n")
        (root / "assembled.stl").write_bytes(assembled)
        (root / "cad/project/moon-body.stl").write_bytes(printable)
        (root / "validation/cad-build.json").write_bytes(receipt)
        (root / "cad/project/snap/iso.png").write_bytes(
            bytes.fromhex(
                "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
                "0000000d49444154789c6360f8cfc000000301010018dd8db10000000049454e44"
                "ae426082"
            )
        )
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
        for check_id in self.blueprint.required_playtest_checks():
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

    def _release(
        self,
        *,
        schema_version=2,
        manual_pdf=None,
        product_overrides=None,
        extra_files=None,
        **overrides,
    ):
        root = self.run_root / NATIVE_RELEASE_PACKAGE_ROOT
        root.mkdir(parents=True, exist_ok=True)
        for obsolete_manual in (
            NATIVE_RELEASE_LEGACY_MANUAL_PATH,
            NATIVE_RELEASE_MANUAL_PATH,
            NATIVE_RELEASE_PLAYTEST_OMISSION_PATH,
        ):
            path = root / obsolete_manual
            if path.exists() or path.is_symlink():
                path.unlink()
        if schema_version == 1:
            manual_path = NATIVE_RELEASE_LEGACY_MANUAL_PATH
            manual = (
                "# Moon Nook\n\n"
                "Arrange the rover and explore the observatory.\n\n"
                "AI-simulated playtest evidence is disclosed in product.json.\n"
            )
            (root / manual_path).write_text(manual, encoding="utf-8")
        else:
            manual_path = NATIVE_RELEASE_MANUAL_PATH
            (root / manual_path).write_bytes(
                _manual_pdf() if manual_pdf is None else manual_pdf
            )
        product = {
            "schema_version": 3,
            "kind": "workshop.release-package",
            "status": "page-ready",
            "title": "Moon Nook",
            "summary": "A tiny lunar observatory.",
            "hero": {
                "headline": "A moon base in the palm of your hand",
                "body": "Arrange the rover beside a tiny lunar observatory.",
                "visual_direction": "Show the exact assembled model from a low lunar angle.",
                "evidence_refs": ["made:product.json"],
            },
            "cinematic": {
                "headline": "The lights are on at Moon Nook",
                "body": "A compact observatory and rover turn a tabletop into a lunar outpost.",
                "visual_direction": "Use the exact model silhouette against a dark moon horizon.",
                "evidence_refs": ["made:product.json"],
            },
            "use_case": {
                "headline": "Set the scene, then explore",
                "body": (
                    "Place the rover beside the observatory, trace a route across the "
                    "tabletop, and invent a new expedition using only the two included "
                    "components. Reset their positions and begin again whenever the crew "
                    "needs a different lunar mission."
                ),
                "visual_direction": "Show both included components without adding accessories.",
                "evidence_refs": ["made:product.json"],
            },
            "story_blocks": [
                {
                    "headline": "Checked before Release",
                    "body": (
                        "This sealed digital revision completed every required automated "
                        "Workshop check. The evidence records the tested files, methods, "
                        "and limits so the page describes only what those exact checks "
                        "support and makes no claim of physical validation."
                    ),
                    "visual_direction": "Pair the exact CAD model with a restrained check motif.",
                    "evidence_refs": [
                        "playtest:%s" % next(iter(self._claims()))
                    ],
                }
            ],
            "what_arrives": ["observatory shell", "moon rover"],
            "limitations": ["AI-simulated playtest only"],
            "product_artifact_sha256": self.made.product_manifest.artifact_sha256,
            "playtest_evidence_artifact_sha256": (
                self.playtested.evidence_manifest.artifact_sha256
            ),
            "claims": self._claims(),
        }
        if schema_version == 2:
            product = {
                "schema_version": 4,
                "kind": "workshop.release-package",
                "status": "manual-ready",
                "title": "Moon Nook",
                "summary": "A tiny lunar observatory.",
                "what_arrives": ["observatory shell", "moon rover"],
                "limitations": [],
                "product_artifact_sha256": (
                    self.made.product_manifest.artifact_sha256
                ),
                "playtest_evidence_artifact_sha256": (
                    self.playtested.evidence_manifest.artifact_sha256
                ),
                "claims": self._claims(),
            }
        elif schema_version == 3:
            omission_sha256 = playtest_omission_sha256()
            product = {
                "schema_version": 5,
                "kind": "workshop.release-package",
                "status": "manual-ready",
                "title": "Moon Nook",
                "summary": "A tiny lunar observatory.",
                "what_arrives": ["observatory shell", "moon rover"],
                "limitations": ["Playtest was not run."],
                "product_artifact_sha256": (
                    self.made.product_manifest.artifact_sha256
                ),
                "playtest_status": "not-run",
                "playtest_evidence_artifact_sha256": omission_sha256,
                "claims": direct_release_claims(),
            }
            (root / NATIVE_RELEASE_PLAYTEST_OMISSION_PATH).write_bytes(
                _canonical(playtest_omission_record())
            )
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
            "manual_path": manual_path,
            "product_json_path": NATIVE_RELEASE_PRODUCT_PATH,
            "product_json_sha256": _sha(product_bytes),
            "product": product,
            "schema_version": schema_version,
        }
        if schema_version == 3:
            values["playtested_sha256"] = playtest_omission_sha256()
            values["playtest_evidence_artifact_sha256"] = (
                playtest_omission_sha256()
            )
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

    def _public_receipt(self, release, *, slug="moon-nook"):
        entries = {
            entry.path: entry for entry in release.package_manifest.entries
        }
        details = {
            "release_sha256": release.package_manifest.artifact_sha256,
            "product_page_sha256": release.product_json_sha256,
            "manual_sha256": entries[release.manual_path].sha256,
            "primary_model_path": "assembled.stl",
            "primary_model_sha256": self.made.product["cad"][
                "assembled_stl"
            ]["sha256"],
            "page_url": "https://www.autonomous.ai/factory/product/%s" % slug,
        }
        if release.schema_version == 1:
            details.update(
                {
                    "factory_content_sha256": "f" * 64,
                    "cover_url": "https://cdn.autonomous.ai/%s.png" % slug,
                }
            )
        else:
            details["manual_path"] = NATIVE_RELEASE_MANUAL_PATH
        return Receipt(
            payload_sha256="1" * 64,
            artifact_sha256=release.product_artifact_sha256,
            adapter="factory",
            status="public",
            observed_at="2026-08-26T00:00:00Z",
            reference="design-%s" % slug,
            details=details,
            design_id="design-%s" % slug,
            slug=slug,
            owner_id="owner-eve",
            root_id="design-%s" % slug,
            current_history_id="history-1",
            published_history_id="history-1",
            project_url="https://cdn.autonomous.ai/projects/%s/" % slug,
            listing_active=True,
            listing_price_cents=2400,
            listing_currency="USD",
            listing_sku=slug.upper(),
        )

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
        self.assertEqual(package.manual_path, "MANUAL.pdf")
        self.assertEqual(package.made.artifact_sha256, release.product_artifact_sha256)
        self.assertTrue(package.playtested.passed)
        self.assertEqual(dict(package.claims), dict(release.claims))
        self.assertEqual(package.product["status"], "manual-ready")
        self.assertNotIn("hero", package.product)
        serialized = json.dumps(release.to_dict(), sort_keys=True)
        for forbidden in ("credentials", "factory_receipt", "site_receipt"):
            self.assertNotIn(forbidden, serialized)

    def test_schema_v1_markdown_round_trips_without_hash_reinterpretation(self):
        release = self._release(schema_version=1)
        sealed = release.to_dict()
        release_sha256 = sealed.pop("release_sha256")

        self.assertEqual(release.manual_path, "MANUAL.md")
        self.assertEqual(release_sha256, _sha(_canonical(sealed)))
        self.assertEqual(NativeRelease.from_mapping(release.to_dict()), release)
        package = release.validate_package_tree(
            self.run_root, self.made, self.playtested
        )
        self.assertEqual(package.manual_path, "MANUAL.md")

    def test_schema_version_binds_the_manual_filename(self):
        release_v2 = self._release()
        with self.assertRaisesRegex(ContractError, "schema_version 2.*MANUAL.pdf"):
            self._rebuild_release(
                release_v2, manual_path=NATIVE_RELEASE_LEGACY_MANUAL_PATH
            )

        release_v1 = self._release(schema_version=1)
        with self.assertRaisesRegex(ContractError, "schema_version 1.*MANUAL.md"):
            self._rebuild_release(release_v1, manual_path=NATIVE_RELEASE_MANUAL_PATH)
        with self.assertRaisesRegex(ContractError, "schema_version 3.*MANUAL.pdf"):
            self._rebuild_release(release_v1, schema_version=3)
        with self.assertRaisesRegex(ContractError, "requires product.json schema_version 4"):
            self._release(product_overrides={"schema_version": 3})
        with self.assertRaisesRegex(ContractError, "requires product.json schema_version 3"):
            self._release(
                schema_version=1,
                product_overrides={"schema_version": 4},
            )

    def test_release_product_validator_rejects_unknown_release_schema_versions(self):
        release = self._release()

        for schema_version in (0, 4, 999, True):
            with self.subTest(schema_version=schema_version), self.assertRaisesRegex(
                ContractError, "schema_version must be 1, 2, or 3"
            ):
                validate_release_product(
                    release.product,
                    release_schema_version=schema_version,
                )

    def test_pdf_manual_accepts_the_bounded_page_limit(self):
        release = self._release(manual_pdf=_manual_pdf(page_count=64))

        package = release.validate_package_tree(
            self.run_root, self.made, self.playtested
        )

        self.assertEqual(package.manual_path, "MANUAL.pdf")

    def test_pdf_manual_rejects_page_count_boxes_and_text_failures(self):
        cases = (
            (_manual_pdf(page_count=0), "1 through 64 pages"),
            (_manual_pdf(page_count=65), "1 through 64 pages"),
            (_manual_pdf(box=(0, 0, 0, 420)), "printable page"),
            (_manual_pdf(text=""), "meaningful extractable text"),
        )
        for manual, message in cases:
            with self.subTest(message=message):
                release = self._release(manual_pdf=manual)
                with self.assertRaisesRegex(ContractError, message):
                    release.validate_package_tree(
                        self.run_root, self.made, self.playtested
                    )

    def test_pdf_manual_rejects_active_and_external_features(self):
        cases = (
            (
                b"/Names << /Dests << /Names [(x) << /S /JavaScript "
                b"/JS (app.alert\\(1\\)) >>] >> >>",
                "active or external",
            ),
            (
                b"/Names << /EmbeddedFiles << /Names [(notes.txt) "
                b"<< /Type /Filespec /F (notes.txt) >>] >> >>",
                "active or external",
            ),
            (
                b"/Names << /Dests << /Names [(x) << /S /Launch "
                b"/Win << /F (program.exe) >> >>] >> >>",
                "forbidden PDF action",
            ),
            (
                b"/Names << /Dests << /Names [(x) << /S /URI "
                b"/URI (https://example.test) >>] >> >>",
                "active or external",
            ),
        )
        for catalog_entries, message in cases:
            with self.subTest(catalog_entries=catalog_entries):
                release = self._release(
                    manual_pdf=_manual_pdf(catalog_entries=catalog_entries)
                )
                with self.assertRaisesRegex(ContractError, message):
                    release.validate_package_tree(
                        self.run_root, self.made, self.playtested
                    )

    def test_pdf_manual_preflights_repeated_page_references_before_flattening(self):
        manual = _manual_pdf(
            page_count=1,
            declared_page_count=1,
            repeated_page_references=10_000,
        )
        release = self._release(manual_pdf=manual)

        with self.assertRaisesRegex(ContractError, "unreadable page tree"):
            release.validate_package_tree(self.run_root, self.made, self.playtested)

    def test_pdf_manual_rejects_sound_annotations_postscript_and_opi(self):
        sound_stream = (
            b"<< /R 8000 /C 1 /B 8 /Length 1 >>\nstream\n\x00\nendstream"
        )
        cases = (
            (
                _manual_pdf(
                    catalog_entries=(
                        b"/Names << /Dests << /Names [(sound) 6 0 R] >> >>"
                    ),
                    extra_objects={
                        6: b"<< /S /Sound /Sound 7 0 R >>",
                        7: sound_stream,
                    },
                ),
                "forbidden PDF action: /Sound",
            ),
            (
                _manual_pdf(
                    page_entries=b"/Annots [6 0 R]",
                    extra_objects={
                        6: (
                            b"<< /Type /Annot /Subtype /Link /Rect [0 0 20 20] "
                            b"/Dest [4 0 R /Fit] >>"
                        )
                    },
                ),
                "forbidden PDF object: /Annot",
            ),
            (
                _manual_pdf(
                    resource_entries=b"/XObject << /PS1 6 0 R >>",
                    extra_objects={
                        6: b"<< /Type /XObject /Subtype /PS /Length 2 >>\n"
                        b"stream\n()\nendstream"
                    },
                ),
                "forbidden PDF subtype: /PS",
            ),
            (
                _manual_pdf(
                    resource_entries=b"/XObject << /Im1 6 0 R >>",
                    extra_objects={
                        6: (
                            b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 "
                            b"/ColorSpace /DeviceGray /BitsPerComponent 8 "
                            b"/OPI << /Type /OPI /Version 1.3 /F (outside.eps) >> "
                            b"/Length 1 >>\nstream\n\x00\nendstream"
                        )
                    },
                ),
                "active or external",
            ),
        )
        for manual, message in cases:
            with self.subTest(message=message):
                release = self._release(manual_pdf=manual)
                with self.assertRaisesRegex(ContractError, message):
                    release.validate_package_tree(
                        self.run_root, self.made, self.playtested
                    )

    def test_pdf_manual_bounds_image_dimensions_and_every_decoded_stream(self):
        expanded = b"x" * (8 * 1024 * 1024 + 1)
        compressed = zlib.compress(expanded, level=9)
        run_length = b"\x81x" * ((8 * 1024 * 1024) // 128 + 1) + b"\x80"
        ascii85 = b"<~" + b"z" * (2 * 1024 * 1024 + 1) + b"~>"
        oversized_jpeg = (
            b"\xff\xd8\xff\xc0\x00\x0b\x08\x23\x28\x23\x28\x01"
            b"\x01\x11\x00\xff\xd9"
        )
        inline_pixels = zlib.compress(b"\x00" * ((9_000 * 9_000 + 7) // 8), level=9)
        inline_form = (
            b"q BI /W 9000 /H 9000 /CS /G /BPC 1 /F /FlateDecode ID "
            + inline_pixels
            + b" EI Q\n"
        )
        cases = (
            (
                _manual_pdf(
                    extra_objects={
                        6: (
                            b"<< /Type /XObject /Subtype /Image /Width 8193 "
                            b"/Height 1 /ColorSpace /DeviceGray /BitsPerComponent 8 "
                            b"/Length 1 >>\nstream\n\x00\nendstream"
                        )
                    }
                ),
                "image Width",
            ),
            (
                _manual_pdf(
                    extra_objects={
                        6: (
                            b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 "
                            b"/ColorSpace /DeviceGray /BitsPerComponent 8 "
                            b"/Filter /DCTDecode /Length "
                            + str(len(oversized_jpeg)).encode("ascii")
                            + b" >>\nstream\n"
                            + oversized_jpeg
                            + b"\nendstream"
                        )
                    }
                ),
                "JPEG dimensions differ",
            ),
            (
                _manual_pdf(
                    resource_entries=b"/XObject << /Fm1 6 0 R >>",
                    content_suffix=b"q /Fm1 Do Q\n",
                    extra_objects={
                        6: (
                            b"<< /Type /XObject /Subtype /Form /BBox [0 0 10 10] "
                            b"/Resources << >> /Length "
                            + str(len(inline_form)).encode("ascii")
                            + b" >>\nstream\n"
                            + inline_form
                            + b"endstream"
                        )
                    },
                ),
                "unsupported inline image",
            ),
            (
                _manual_pdf(
                    extra_objects={
                        6: (
                            b"<< /Filter /FlateDecode /Length "
                            + str(len(compressed)).encode("ascii")
                            + b" >>\nstream\n"
                            + compressed
                            + b"\nendstream"
                        )
                    }
                ),
                "oversized PDF stream|decoded PDF stream",
            ),
            (
                _manual_pdf(
                    extra_objects={
                        6: (
                            b"<< /Filter /RunLengthDecode /Length "
                            + str(len(run_length)).encode("ascii")
                            + b" >>\nstream\n"
                            + run_length
                            + b"\nendstream"
                        )
                    }
                ),
                "oversized PDF stream|decoded PDF stream",
            ),
            (
                _manual_pdf(
                    extra_objects={
                        6: (
                            b"<< /Filter /ASCII85Decode /Length "
                            + str(len(ascii85)).encode("ascii")
                            + b" >>\nstream\n"
                            + ascii85
                            + b"\nendstream"
                        )
                    }
                ),
                "decoded bound is too large",
            ),
        )
        for manual, message in cases:
            with self.subTest(message=message):
                release = self._release(manual_pdf=manual)
                with self.assertRaisesRegex(ContractError, message):
                    release.validate_package_tree(
                        self.run_root, self.made, self.playtested
                    )

    def test_false_lantern_manual_passes_the_isolated_parser_and_renderer(self):
        manual_path = (
            Path(__file__).resolve().parents[2]
            / "toys"
            / "leo-false-lantern"
            / "MANUAL.pdf"
        )
        release = self._release(manual_pdf=manual_path.read_bytes())

        package = release.validate_package_tree(
            self.run_root, self.made, self.playtested
        )

        self.assertEqual(package.manual_path, "MANUAL.pdf")

    def test_pdf_manual_rejects_encryption_and_oversized_bytes(self):
        from pypdf import PdfReader, PdfWriter

        reader = PdfReader(io.BytesIO(_manual_pdf()))
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)
        writer.encrypt("not-for-the-customer")
        encrypted = io.BytesIO()
        writer.write(encrypted)
        release = self._release(manual_pdf=encrypted.getvalue())
        with self.assertRaisesRegex(ContractError, "must be unencrypted"):
            release.validate_package_tree(self.run_root, self.made, self.playtested)

        oversized = _manual_pdf() + b" " * (
            MAX_NATIVE_RELEASE_MANUAL_BYTES - len(_manual_pdf()) + 1
        )
        with self.assertRaisesRegex(ContractError, "at most 16777216 bytes"):
            self._release(manual_pdf=oversized)

    def test_legacy_manual_needs_no_pdf_worker_and_missing_worker_fails_closed(self):
        legacy = self._release(schema_version=1)
        package = legacy.validate_package_tree(
            self.run_root, self.made, self.playtested
        )
        self.assertEqual(package.manual_path, "MANUAL.md")

        release = self._release()
        with mock.patch(
            "workshop.release.native._pdf_validator_asset_path",
            side_effect=ContractError("native Release PDF validator is unavailable"),
        ), self.assertRaisesRegex(ContractError, "validator is unavailable"):
            release.validate_package_tree(
                self.run_root, self.made, self.playtested
            )

    def test_product_run_uses_its_frozen_pdf_worker_without_installed_fallback(self):
        release = self._release()
        worker = (
            self.run_root
            / ".agents/skills/autonomous-workshop/scripts/pdf_validator.py"
        )
        worker.parent.mkdir(parents=True)
        with self.assertRaisesRegex(ContractError, "validator is unavailable"):
            release.validate_package_tree(
                self.run_root, self.made, self.playtested
            )

        source = (
            Path(__file__).resolve().parents[2]
            / ".agents/product-run/.agents/skills/autonomous-workshop/scripts"
            / "pdf_validator.py"
        )
        worker.write_bytes(source.read_bytes())
        worker.chmod(0o400)

        package = release.validate_package_tree(
            self.run_root, self.made, self.playtested
        )
        self.assertEqual(package.manual_path, "MANUAL.pdf")

    def test_host_materializes_strict_public_digital_verification(self):
        release = self._release()

        verification = materialize_digital_verification(
            self.run_root, release, self.made, self.playtested
        )
        path = self.run_root / PRODUCT_VERIFICATION_PATH
        observed = read_product_verification(path)

        self.assertEqual(observed, verification)
        self.assertEqual(observed.level, DIGITALLY_VERIFIED)
        self.assertIsNone(observed.physical_verification)
        self.assertEqual(
            observed.product_artifact_sha256,
            self.made.product_manifest.artifact_sha256,
        )
        self.assertEqual(
            observed.playtest_evidence_artifact_sha256,
            self.playtested.evidence_manifest.artifact_sha256,
        )
        self.assertEqual(
            [check.check_id for check in observed.checks],
            sorted(self.blueprint.required_playtest_checks()),
        )
        self.assertNotIn(
            "VERIFICATION.json",
            {entry.path for entry in release.package_manifest.entries},
        )
        serialized = path.read_text(encoding="utf-8")
        for private in (
            "evidence_ref",
            "observed_at",
            "factory_receipt",
            "site_receipt",
            "transcript",
        ):
            self.assertNotIn(private, serialized)

    def test_host_replaces_stale_verification_after_exact_release_validation(self):
        release = self._release()
        verification_path = self.run_root / PRODUCT_VERIFICATION_PATH
        verification_path.write_text("stale bytes", encoding="utf-8")

        first = materialize_digital_verification(
            self.run_root, release, self.made, self.playtested
        )
        second = materialize_digital_verification(
            self.run_root, release, self.made, self.playtested
        )

        self.assertEqual(first, second)
        self.assertEqual(read_product_verification(verification_path), first)

    def test_schema_v1_cannot_self_declare_physical_verification(self):
        release = self._release()
        verification = materialize_digital_verification(
            self.run_root, release, self.made, self.playtested
        ).to_dict()
        verification.update(
            {
                "level": PHYSICALLY_VERIFIED,
                "label": "Physically Verified",
                "physical_verification": {"receipt_sha256": "f" * 64},
            }
        )

        with self.assertRaisesRegex(ContractError, "cannot claim Physically Verified"):
            ProductVerification.from_mapping(verification)

    def test_optional_verification_failure_does_not_become_a_release_failure(self):
        release = self._release()
        path = self.run_root / PRODUCT_VERIFICATION_PATH
        outside = self.run_root / "outside-verification.json"
        outside.write_text("outside", encoding="utf-8")
        path.symlink_to(outside)

        observed = try_materialize_digital_verification(
            self.run_root, release, self.made, self.playtested
        )

        self.assertIsNone(observed)
        package = release.validate_package_tree(
            self.run_root, self.made, self.playtested
        )
        self.assertTrue(package.playtested.passed)

    def test_rejects_media_symlinks_and_path_escape(self):
        release = self._release()
        with self.assertRaisesRegex(ContractError, "package_root is not canonical"):
            self._rebuild_release(release, package_root="../outside")

        with self.assertRaisesRegex(ContractError, "cannot contain media files"):
            self._release(extra_files={"hero.png": b"not really an image"})
        (self.run_root / NATIVE_RELEASE_PACKAGE_ROOT / "hero.png").unlink()

        release = self._release()
        manual = self.run_root / NATIVE_RELEASE_PACKAGE_ROOT / release.manual_path
        outside = self.run_root / "outside-manual.pdf"
        outside.write_bytes(_manual_pdf())
        manual.unlink()
        manual.symlink_to(outside)
        with self.assertRaisesRegex(ArtifactError, "symlink"):
            release.validate_package_tree(self.run_root, self.made, self.playtested)

        manual.unlink()
        manual.write_bytes(_manual_pdf())
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

    def test_requires_complete_evidence_bound_page_copy(self):
        with self.assertRaisesRegex(ContractError, "fields are invalid"):
            self._release(product_overrides={"factory_enrichment": {"status": "pending"}})

        with self.assertRaisesRegex(ContractError, "fields are invalid"):
            self._release(
                product_overrides={
                    "hero": {
                        "headline": "Unsupported",
                        "body": "This copy cites evidence outside the sealed run.",
                        "visual_direction": "No invented geometry.",
                        "evidence_refs": ["playtest:not-a-check"],
                    }
                }
            )

        with self.assertRaisesRegex(ContractError, "evidence_refs"):
            self._release(
                schema_version=1,
                product_overrides={
                    "hero": {
                        "headline": "Unsupported",
                        "body": "This copy cites evidence outside the sealed run.",
                        "visual_direction": "No invented geometry.",
                        "evidence_refs": ["playtest:not-a-check"],
                    }
                },
            )

    def test_rejects_copy_that_factory_cannot_display_exactly(self):
        use_case = {
            "headline": "Set the scene, then explore",
            "body": "x" * 180,
            "visual_direction": "Show only the exact included components.",
            "evidence_refs": ["made:product.json"],
        }
        story_block = {
            "headline": "Checked before Release",
            "body": "x" * 180,
            "visual_direction": "Show the exact verified revision.",
            "evidence_refs": ["made:product.json"],
        }
        cases = (
            (
                {"use_case": {**use_case, "body": "x" * 179}},
                "use_case body.*180-400",
            ),
            (
                {"story_blocks": [{**story_block, "body": "x" * 401}]},
                r"story_blocks\[0\] body.*180-400",
            ),
            (
                {"use_case": {**use_case, "headline": "x" * 41}},
                "use_case headline.*1-40",
            ),
            (
                {"story_blocks": [dict(story_block) for _ in range(11)]},
                "at most 10",
            ),
        )
        for product_overrides, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ContractError, message):
                    self._release(
                        schema_version=1,
                        product_overrides=product_overrides,
                    )

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
        manual = self.run_root / NATIVE_RELEASE_PACKAGE_ROOT / release.manual_path
        manual.write_bytes(b"%PDF-1.7\nchanged after sealing\n%%EOF\n")
        with self.assertRaisesRegex(ArtifactError, "differs from its manifest"):
            release.validate_package_tree(self.run_root, self.made, self.playtested)

    def test_public_example_uses_sealed_inventory_and_never_overwrites(self):
        release = self._release(schema_version=1)
        self._write_contract(release)
        entries = {
            entry.path: entry for entry in release.package_manifest.entries
        }
        receipt = Receipt(
            payload_sha256="1" * 64,
            artifact_sha256=release.product_artifact_sha256,
            adapter="factory",
            status="public",
            observed_at="2026-08-26T00:00:00Z",
            reference="design-moon-nook",
            details={
                "release_sha256": release.package_manifest.artifact_sha256,
                "product_page_sha256": release.product_json_sha256,
                "manual_sha256": entries[release.manual_path].sha256,
                "factory_content_sha256": "f" * 64,
                "primary_model_path": "assembled.stl",
                "primary_model_sha256": self.made.product["cad"][
                    "assembled_stl"
                ]["sha256"],
                "page_url": "https://www.autonomous.ai/factory/product/moon-nook",
                "cover_url": "https://cdn.autonomous.ai/moon-nook.png",
            },
            design_id="design-moon-nook",
            slug="moon-nook",
            owner_id="owner-eve",
            root_id="design-moon-nook",
            current_history_id="history-1",
            published_history_id="history-1",
            project_url="https://cdn.autonomous.ai/projects/moon-nook/",
            listing_active=True,
            listing_price_cents=2400,
            listing_currency="USD",
            listing_sku="MOON-NOOK-1",
        )
        repository = self.run_root / "repository"
        (repository / "toys").mkdir(parents=True)

        real_mkdir = os.mkdir

        def create_empty_target_before_exclusive_install(
            path, mode=0o777, *, dir_fd=None
        ):
            if path == "eve-moon-nook" and dir_fd is not None:
                real_mkdir(repository / "toys/eve-moon-nook", 0o755)
            return real_mkdir(path, mode, dir_fd=dir_fd)

        with mock.patch(
            "workshop.release.public_example.os.mkdir",
            side_effect=create_empty_target_before_exclusive_install,
        ), self.assertRaisesRegex(StateConflict, "without overwrite"):
            materialize_public_example(
                repository,
                self.run_root,
                release=release,
                made=self.made,
                inventor_id="eve",
                receipt=receipt,
            )
        raced_target = repository / "toys/eve-moon-nook"
        self.assertEqual(list(raced_target.iterdir()), [])
        raced_target.rmdir()

        signed_cover = replace(
            receipt,
            details={
                **receipt.details,
                "cover_url": (
                    "https://cdn.autonomous.ai/moon-nook.png?token=private"
                ),
            },
        )
        with self.assertRaisesRegex(StateConflict, "public cover URL"):
            materialize_public_example(
                repository,
                self.run_root,
                release=release,
                made=self.made,
                inventor_id="eve",
                receipt=signed_cover,
            )
        self.assertFalse((repository / "toys/eve-moon-nook").exists())

        missing_cover = replace(
            receipt,
            details={
                name: value
                for name, value in receipt.details.items()
                if name != "cover_url"
            },
        )
        with self.assertRaisesRegex(StateConflict, "public cover URL"):
            materialize_public_example(
                repository,
                self.run_root,
                release=release,
                made=self.made,
                inventor_id="eve",
                receipt=missing_cover,
            )
        self.assertFalse((repository / "toys/eve-moon-nook").exists())

        target = materialize_public_example(
            repository,
            self.run_root,
            release=release,
            made=self.made,
            inventor_id="eve",
            receipt=receipt,
            token_summary=_token_summary(),
            wish_id="wish-20260825-235959-deadbeef",
        )
        self.assertEqual(target, repository / "toys/eve-moon-nook")
        self.assertEqual(
            (target / "release/product.json").read_bytes(),
            (self.run_root / release.package_root / "product.json").read_bytes(),
        )
        publication = json.loads(
            (target / "publication/PUBLICATION.json").read_text(encoding="utf-8")
        )
        self.assertEqual(publication["print_files"][0]["quantity"], 2)
        self.assertEqual(
            publication["print_files"][0]["path"],
            "make/models/print/component-001.stl",
        )
        self.assertTrue(
            (target / "make/models/print/component-001.stl").is_file()
        )
        wish = json.loads((target / "wish/wish.json").read_text(encoding="utf-8"))
        self.assertEqual(wish["objective_disclosure"], "withheld")
        self.assertNotIn("objective", wish)
        self.assertFalse((target / "AGENTS.md").exists())
        self.assertTrue((target / "match/assignment.json").is_file())
        self.assertTrue((target / "invent/invented.json").is_file())
        self.assertTrue((target / "make/source/cad/moon.step.py").is_file())
        self.assertEqual(
            (target / "make/source/cad/__init__.py").read_bytes(), b""
        )
        self.assertEqual(
            (target / "make/verification/CAD-GATE.json").read_bytes(),
            (self.run_root / self.made.product_root / self.made.cad_verification_path).read_bytes(),
        )
        self.assertTrue((target / "make/made.json").is_file())
        self.assertTrue((target / "playtest/playtested.json").is_file())
        self.assertTrue((target / "release/release.json").is_file())
        self.assertTrue((target / "MANIFEST.json").is_file())
        tokens = json.loads((target / "TOKENS.json").read_text(encoding="utf-8"))
        self.assertEqual(tokens["status"], "measured")
        self.assertEqual(tokens["stages"]["make"]["input_tokens"], 100)
        self.assertEqual(tokens["stages"]["make"]["output_tokens"], 25)
        timing = json.loads((target / "TIMING.json").read_text(encoding="utf-8"))
        self.assertEqual(timing["status"], "measured")
        self.assertEqual(timing["elapsed_seconds"], 1)
        self.assertEqual(timing["completion_boundary"], "authenticated Factory public readback")
        readme = (target / "README.md").read_text(encoding="utf-8")
        self.assertIn("## How this toy was created", readme)
        self.assertIn(
            "**This toy's input:** A tiny lunar observatory.",
            readme,
        )
        self.assertIn(
            "produced **Moon Nook** — A tiny lunar observatory.",
            readme,
        )
        self.assertIn(
            "**Concept parts:** observatory shell, moon rover.",
            readme,
        )
        self.assertIn("1 STEP, 3 STL and 1 product render PNG", readme)
        self.assertIn(
            "verdict **pass** from 3 checks (agent-playtest, mechanical-check, printability-check)",
            readme,
        )
        self.assertIn("[customer manual](release/MANUAL.md)", readme)
        self.assertIn("## Run cost", readme)
        self.assertIn("| Native Manager input tokens | 100 (measured; 1/1 turns measured) |", readme)
        self.assertIn("| Native Manager output tokens | 25 (measured; 1/1 turns measured) |", readme)
        self.assertIn("| Wish to verified publication | 1s", readme)
        self.assertIn("| Make | 100 | 25 | 1 | measured |", readme)
        public_manifest = json.loads(
            (target / "MANIFEST.json").read_text(encoding="utf-8")
        )
        self.assertIn(
            "make/source/cad/README.md",
            {
                entry["path"]
                for entry in public_manifest["artifact_manifest"]["entries"]
            },
        )
        self.assertEqual(
            public_manifest["artifact_manifest"],
            build_public_archive_manifest(target).to_dict(),
        )

        self.assertEqual(
            materialize_public_example(
                repository,
                self.run_root,
                release=release,
                made=self.made,
                inventor_id="eve",
                receipt=receipt,
                token_summary=_token_summary(),
                wish_id="wish-20260825-235959-deadbeef",
            ),
            target,
        )
        (target / "README.md").write_text("collision\n", encoding="utf-8")
        with self.assertRaisesRegex(StateConflict, "different or partial bytes"):
            materialize_public_example(
                repository,
                self.run_root,
                release=release,
                made=self.made,
                inventor_id="eve",
                receipt=receipt,
                token_summary=_token_summary(),
                wish_id="wish-20260825-235959-deadbeef",
            )

    def test_public_example_copies_exact_pdf_manual_without_cover_or_rich_page_identity(self):
        release = self._release()
        self._write_contract(release)
        entries = {
            entry.path: entry for entry in release.package_manifest.entries
        }
        receipt = Receipt(
            payload_sha256="1" * 64,
            artifact_sha256=release.product_artifact_sha256,
            adapter="factory",
            status="public",
            observed_at="2026-08-26T00:00:00Z",
            reference="design-moon-nook-pdf",
            details={
                "release_sha256": release.package_manifest.artifact_sha256,
                "product_page_sha256": release.product_json_sha256,
                "manual_path": "MANUAL.pdf",
                "manual_sha256": entries[release.manual_path].sha256,
                "primary_model_path": "assembled.stl",
                "primary_model_sha256": self.made.product["cad"][
                    "assembled_stl"
                ]["sha256"],
                "page_url": (
                    "https://www.autonomous.ai/factory/product/moon-nook-pdf"
                ),
            },
            design_id="design-moon-nook-pdf",
            slug="moon-nook-pdf",
            owner_id="owner-eve",
            root_id="design-moon-nook-pdf",
            current_history_id="history-1",
            published_history_id="history-1",
            project_url="https://cdn.autonomous.ai/projects/moon-nook-pdf/",
            listing_active=True,
            listing_price_cents=2400,
            listing_currency="USD",
            listing_sku="MOON-NOOK-PDF-1",
        )
        repository = self.run_root / "pdf-repository"
        (repository / "toys").mkdir(parents=True)

        target = materialize_public_example(
            repository,
            self.run_root,
            release=release,
            made=self.made,
            inventor_id="eve",
            receipt=receipt,
        )

        source_manual = self.run_root / release.package_root / release.manual_path
        self.assertEqual(
            (target / "release/MANUAL.pdf").read_bytes(), source_manual.read_bytes()
        )
        self.assertFalse((target / "release/MANUAL.md").exists())
        publication = json.loads(
            (target / "publication/PUBLICATION.json").read_text(encoding="utf-8")
        )
        self.assertEqual(publication["identities"]["manual_path"], "MANUAL.pdf")
        self.assertNotIn("factory_content_sha256", publication["identities"])
        self.assertNotIn("cover_url", publication["publication"])
        readme = (target / "README.md").read_text()
        self.assertIn("`release/MANUAL.pdf`", readme)
        self.assertIn("## Reproduce", readme)
        self.assertIn("--manager codex --effort quest", readme)
        self.assertNotIn("--github", readme)

        github_repository = self.run_root / "github-readme-repository"
        (github_repository / "toys").mkdir(parents=True)
        github_target = materialize_public_example(
            github_repository,
            self.run_root,
            release=release,
            made=self.made,
            inventor_id="eve",
            receipt=self._public_receipt(release, slug="moon-nook-github"),
            github_requested=True,
        )
        self.assertIn(
            "--manager codex --effort quest --github",
            (github_target / "README.md").read_text(),
        )

    def test_public_archive_requires_explicit_exact_wish_disclosure_and_strict_contracts(self):
        release = self._release(schema_version=1)
        self._write_contract(release)
        receipt = self._public_receipt(release, slug="moon-nook-disclosed")
        repository = self.run_root / "disclosure-repository"
        (repository / "toys").mkdir(parents=True)

        target = materialize_public_example(
            repository,
            self.run_root,
            release=release,
            made=self.made,
            inventor_id="eve",
            receipt=receipt,
            disclose_exact_wish=True,
        )

        public_wish = json.loads(
            (target / "wish/wish.json").read_text(encoding="utf-8")
        )
        self.assertEqual(public_wish["objective_disclosure"], "exact")
        self.assertEqual(public_wish["objective"], self.wish["objective"])
        self.assertEqual(public_wish["constraints"], self.wish["constraints"])
        self.assertEqual(public_wish["context"], self.wish["context"])
        disclosed_readme = (target / "README.md").read_text(encoding="utf-8")
        self.assertIn(self.wish["objective"], disclosed_readme)
        self.assertIn("The exact wording was explicitly disclosed", disclosed_readme)

        assignment_path = self.run_root / "artifacts/invent/assignment.json"
        assignment_path.write_bytes(b'{"schema_version":1,"schema_version":1}')
        another_repository = self.run_root / "strict-repository"
        (another_repository / "toys").mkdir(parents=True)
        with self.assertRaisesRegex(StateConflict, "strict UTF-8 JSON"):
            materialize_public_example(
                another_repository,
                self.run_root,
                release=release,
                made=self.made,
                inventor_id="eve",
                receipt=receipt,
            )

    def test_public_archive_records_direct_release_without_playtest_directory(self):
        release = self._release(schema_version=3)
        self._write_contract(release)
        receipt = self._public_receipt(release, slug="moon-nook-direct")
        repository = self.run_root / "direct-repository"
        (repository / "toys").mkdir(parents=True)

        target = materialize_public_example(
            repository,
            self.run_root,
            release=release,
            made=self.made,
            inventor_id="eve",
            receipt=receipt,
        )

        self.assertFalse((target / "playtest").exists())
        self.assertEqual(
            json.loads(
                (target / "release/PLAYTEST-NOT-RUN.json").read_text(
                    encoding="utf-8"
                )
            ),
            playtest_omission_record(),
        )
        self.assertIn(
            "Playtest was not run",
            (target / "README.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "![Moon Nook](make/verification/renders/iso.png)",
            (target / "README.md").read_text(encoding="utf-8"),
        )

    def test_public_hero_ignores_arbitrary_diagnostic_images(self):
        staging = self.run_root / "hero-selection"
        diagnostic = staging / "make/product/cad/review/closed-top.png"
        diagnostic.parent.mkdir(parents=True)
        diagnostic.write_bytes(b"diagnostic silhouette")

        self.assertIsNone(_public_hero_path(staging))

        approved = staging / "make/verification/renders/isometric.png"
        approved.parent.mkdir(parents=True)
        approved.write_bytes(b"approved presentation render")
        self.assertEqual(
            _public_hero_path(staging),
            "make/verification/renders/isometric.png",
        )

    def test_public_archive_does_not_invent_an_invent_stage_for_spark(self):
        spark_inputs = self.run_root / "artifacts/make/r0001"
        for name in ("assignment.json", "invented.json"):
            (self.run_root / "artifacts/invent" / name).rename(
                spark_inputs / name
            )
        (self.run_root / "artifacts/invent").rmdir()
        release = self._release(schema_version=3)
        self._write_contract(release)
        receipt = self._public_receipt(release, slug="moon-nook-spark")
        repository = self.run_root / "spark-repository"
        (repository / "toys").mkdir(parents=True)

        target = materialize_public_example(
            repository,
            self.run_root,
            release=release,
            made=self.made,
            inventor_id="eve",
            receipt=receipt,
        )

        self.assertFalse((target / "invent").exists())
        self.assertTrue((target / "match/assignment.json").is_file())
        self.assertTrue((target / "make/invented.json").is_file())
        readme = (target / "README.md").read_text(encoding="utf-8")
        self.assertIn("Invent was skipped", readme)
        self.assertIn(
            "Spark has no separate Invent Goal; selection and this compact concept were folded into Make.",
            readme,
        )
        self.assertIn(
            "[make/invented.json](make/invented.json)",
            readme,
        )
        self.assertIn("Spark: `Wish -> Make -> Release`", readme)
        self.assertIn("| Match | 1 | accepted (Eve) |", readme)
        self.assertIn("| Invent | skipped | Spark pass-through |", readme)
        self.assertIn("| Make | 1 | accepted |", readme)
        self.assertIn("| Playtest | not run | Spark omission |", readme)
        self.assertIn("| Release | 1 | accepted |", readme)

    def test_public_archive_summarizes_superseded_make_and_playtest_rounds(self):
        first_check = self.playtested.checks[0]
        failed_first = replace(
            first_check,
            passed=False,
            observations={"ok": False},
        )
        failed_playtest = NativePlaytested(
            round=1,
            made_sha256=self.made.made_sha256,
            product_artifact_sha256=self.made.product_manifest.artifact_sha256,
            blueprint_sha256=self.blueprint.sha256,
            evidence_root="artifacts/playtest/r0001/evidence",
            evidence_manifest=self.playtested.evidence_manifest,
            checks=(failed_first,) + self.playtested.checks[1:],
            feedback=(
                Feedback(
                    code="revise-first-check",
                    area="playtest",
                    severity="improve",
                    finding="The first deterministic check failed.",
                    change="Revise Make and rerun the complete Playtest.",
                    evidence_refs=(first_check.evidence_ref,),
                ),
            ),
            verdict="improve",
        )
        (self.run_root / "artifacts/playtest/r0001/playtested.json").write_bytes(
            _canonical(failed_playtest.to_dict())
        )

        second_product = self.run_root / "artifacts/make/r0002/product"
        shutil.copytree(
            self.run_root / self.made.product_root,
            second_product,
        )
        second_made = NativeMade(
            round=2,
            wish_sha256=self.made.wish_sha256,
            assignment_sha256=self.made.assignment_sha256,
            taste_sha256=self.made.taste_sha256,
            blueprint_sha256=self.made.blueprint_sha256,
            invented_sha256=self.made.invented_sha256,
            product_root="artifacts/make/r0002/product",
            cad_project_path=self.made.cad_project_path,
            product_manifest=self.made.product_manifest,
            product=self.made.to_dict()["product"],
            product_json_sha256=self.made.product_json_sha256,
            cad_verification_path=self.made.cad_verification_path,
            cad_verification_sha256=self.made.cad_verification_sha256,
        )
        (self.run_root / "artifacts/make/r0002/made.json").write_bytes(
            _canonical(second_made.to_dict())
        )
        second_evidence = self.run_root / "artifacts/playtest/r0002/evidence"
        shutil.copytree(
            self.run_root / self.playtested.evidence_root,
            second_evidence,
        )
        second_playtest = NativePlaytested(
            round=2,
            made_sha256=second_made.made_sha256,
            product_artifact_sha256=second_made.product_manifest.artifact_sha256,
            blueprint_sha256=self.blueprint.sha256,
            evidence_root="artifacts/playtest/r0002/evidence",
            evidence_manifest=build_artifact_manifest(
                second_evidence,
                created_at="content-addressed",
            ),
            checks=self.playtested.checks,
            feedback=(),
            verdict="pass",
        )
        (self.run_root / "artifacts/playtest/r0002/playtested.json").write_bytes(
            _canonical(second_playtest.to_dict())
        )
        release = self._rebuild_release(
            self._release(),
            round=2,
            made_sha256=second_made.made_sha256,
            playtested_sha256=second_playtest.playtested_sha256,
        )
        self._write_contract(release)
        receipt = self._public_receipt(release, slug="moon-nook-revised")
        repository = self.run_root / "revision-repository"
        (repository / "toys").mkdir(parents=True)

        target = materialize_public_example(
            repository,
            self.run_root,
            release=release,
            made=second_made,
            inventor_id="eve",
            receipt=receipt,
        )

        make_attempts = json.loads(
            (target / "make/ATTEMPTS.json").read_text(encoding="utf-8")
        )["attempts"]
        self.assertEqual(
            [attempt["outcome"] for attempt in make_attempts],
            ["superseded", "accepted"],
        )
        playtest_attempts = json.loads(
            (target / "playtest/ATTEMPTS.json").read_text(encoding="utf-8")
        )["attempts"]
        self.assertEqual(
            [attempt["outcome"] for attempt in playtest_attempts],
            ["revision-requested", "accepted"],
        )
        self.assertEqual(
            playtest_attempts[0]["failed_checks"],
            [first_check.check_id],
        )
        readme = (target / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "Quest: `Wish -> Invent -> Make -> Playtest -> Release`",
            readme,
        )
        self.assertIn("| Make | 2 | round 1 superseded; round 2 accepted |", readme)
        self.assertIn(
            "| Playtest | 2 | round 1 revision-requested (%s); round 2 accepted |"
            % first_check.check_id,
            readme,
        )
        self.assertIn("| Release | 1 | round 2 accepted |", readme)

    def test_public_archive_preserves_make_to_invent_revision_history(self):
        original_playtest_evidence = {
            entry.path: (
                self.run_root
                / self.playtested.evidence_root
                / entry.path
            ).read_bytes()
            for entry in self.playtested.evidence_manifest.entries
        }
        (self.run_root / "artifacts/make/r0001/made.json").unlink()
        shutil.rmtree(self.run_root / "artifacts/playtest/r0001")
        evidence_root = self.run_root / "artifacts/make/r0001/revision-evidence"
        evidence_root.mkdir(parents=True)
        contradiction = _canonical(
            {
                "check": "rotor-web",
                "passed": False,
                "finding": "The sealed web is thinner than its own minimum.",
            }
        )
        (evidence_root / "rotor-web.json").write_bytes(contradiction)
        request = NativeMakeInventRevision(
            round=1,
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            invented_sha256=self.invented.invented_sha256,
            evidence_root="artifacts/make/r0001/revision-evidence",
            evidence_manifest=build_artifact_manifest(
                evidence_root,
                created_at="content-addressed",
            ),
            feedback=(
                MakeInventRevisionFeedback(
                    code="rotor-web-contradiction",
                    area="detent geometry",
                    severity="block",
                    finding="The sealed web is thinner than its own minimum.",
                    change="Increase the rotor diameter while preserving phase.",
                    evidence_refs=("rotor-web.json",),
                ),
            ),
        )
        request_path = (
            self.run_root
            / "artifacts/make/r0001/invent-revision-request.json"
        )
        request_path.write_bytes(_canonical(request.to_dict()))
        authored_source = _canonical(
            {"feedback": [item.to_dict() for item in request.feedback]}
        )
        (
            self.run_root
            / "artifacts/make/r0001/invent-revision-source.json"
        ).write_bytes(authored_source)

        revised_root = self.run_root / "artifacts/invent/r0002"
        revised_root.mkdir(parents=True)
        revised_invented = NativeInvented(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept={
                "title": "Moon Nook",
                "summary": "A repaired tiny lunar observatory.",
            },
            research=self.invented.to_dict()["research"],
        )
        (revised_root / "assignment.json").write_bytes(
            _canonical(self.assignment.to_dict())
        )
        (revised_root / "invented.json").write_bytes(
            _canonical(revised_invented.to_dict())
        )

        second_product = self.run_root / "artifacts/make/r0002/product"
        shutil.copytree(self.run_root / self.made.product_root, second_product)
        second_made = NativeMade(
            round=2,
            wish_sha256=self.made.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.made.taste_sha256,
            blueprint_sha256=self.made.blueprint_sha256,
            invented_sha256=revised_invented.invented_sha256,
            product_root="artifacts/make/r0002/product",
            cad_project_path=self.made.cad_project_path,
            product_manifest=self.made.product_manifest,
            product=self.made.to_dict()["product"],
            product_json_sha256=self.made.product_json_sha256,
            cad_verification_path=self.made.cad_verification_path,
            cad_verification_sha256=self.made.cad_verification_sha256,
        )
        (self.run_root / "artifacts/make/r0002/made.json").write_bytes(
            _canonical(second_made.to_dict())
        )

        second_evidence = self.run_root / "artifacts/playtest/r0002/evidence"
        second_evidence.mkdir(parents=True)
        for relative, content in original_playtest_evidence.items():
            path = second_evidence.joinpath(*relative.split("/"))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        second_playtest = NativePlaytested(
            round=2,
            made_sha256=second_made.made_sha256,
            product_artifact_sha256=second_made.product_manifest.artifact_sha256,
            blueprint_sha256=self.blueprint.sha256,
            evidence_root="artifacts/playtest/r0002/evidence",
            evidence_manifest=build_artifact_manifest(
                second_evidence,
                created_at="content-addressed",
            ),
            checks=self.playtested.checks,
            feedback=(),
            verdict="pass",
        )
        playtested_path = self.run_root / "artifacts/playtest/r0002/playtested.json"
        playtested_path.write_bytes(_canonical(second_playtest.to_dict()))
        release = self._rebuild_release(
            self._release(),
            round=2,
            made_sha256=second_made.made_sha256,
            playtested_sha256=second_playtest.playtested_sha256,
        )
        self._write_contract(release)
        receipt = self._public_receipt(release, slug="moon-nook-invent-revised")
        repository = self.run_root / "invent-revision-repository"
        (repository / "toys").mkdir(parents=True)

        target = materialize_public_example(
            repository,
            self.run_root,
            release=release,
            made=second_made,
            inventor_id="eve",
            receipt=receipt,
        )

        self.assertEqual(
            (target / "invent/invented.json").read_bytes(),
            _canonical(revised_invented.to_dict()),
        )
        self.assertEqual(
            (target / "invent/attempts/r0001/invented.json").read_bytes(),
            _canonical(self.invented.to_dict()),
        )
        self.assertEqual(
            (
                target
                / "make/attempts/r0001/invent-revision-request.json"
            ).read_bytes(),
            request_path.read_bytes(),
        )
        self.assertEqual(
            (
                target
                / "make/attempts/r0001/revision-evidence/rotor-web.json"
            ).read_bytes(),
            contradiction,
        )
        make_attempts = json.loads(
            (target / "make/ATTEMPTS.json").read_text(encoding="utf-8")
        )["attempts"]
        self.assertEqual(
            [attempt["outcome"] for attempt in make_attempts],
            ["invent-revision-requested", "accepted"],
        )
        self.assertFalse((target / "playtest/attempts/r0001").exists())
        self.assertEqual(
            json.loads(
                (target / "MANIFEST.json").read_text(encoding="utf-8")
            )["artifact_manifest"],
            build_public_archive_manifest(target).to_dict(),
        )


if __name__ == "__main__":
    unittest.main()
