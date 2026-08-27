import hashlib
import io
import json
import os
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
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    InventorRoster,
    InventorRosterEntry,
)
from workshop.playtest.native import NativePlaytestCheck, NativePlaytested
from workshop.product import ToyBlueprint
from workshop.release.native import (
    MAX_NATIVE_RELEASE_MANUAL_BYTES,
    NATIVE_RELEASE_LEGACY_MANUAL_PATH,
    NATIVE_RELEASE_MANUAL_PATH,
    NATIVE_RELEASE_PACKAGE_ROOT,
    NATIVE_RELEASE_PATH,
    NATIVE_RELEASE_PRODUCT_PATH,
    NativeRelease,
    read_native_release,
    validate_release_product,
)
from workshop.release.public_example import materialize_public_example
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
            wish_sha256="a" * 64,
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
        (root / "cad/project/moon.step").write_bytes(b"ISO-10303-21;\n")
        (root / "assembled.stl").write_bytes(assembled)
        (root / "cad/project/moon-body.stl").write_bytes(printable)
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
        with self.assertRaisesRegex(ContractError, "schema_version must be 1 or 2"):
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

        for schema_version in (0, 3, 999, True):
            with self.subTest(schema_version=schema_version), self.assertRaisesRegex(
                ContractError, "schema_version must be 1 or 2"
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
        )
        self.assertEqual(target, repository / "toys/eve-moon-nook")
        self.assertEqual(
            (target / "product.json").read_bytes(),
            (self.run_root / release.package_root / "product.json").read_bytes(),
        )
        publication = json.loads(
            (target / "PUBLICATION.json").read_text(encoding="utf-8")
        )
        self.assertEqual(publication["print_files"][0]["quantity"], 2)
        self.assertEqual(
            publication["print_files"][0]["path"],
            "print/component-001.stl",
        )
        self.assertTrue((target / "print/component-001.stl").is_file())
        self.assertFalse((target / "WISH.json").exists())
        self.assertFalse((target / "AGENTS.md").exists())

        self.assertEqual(
            materialize_public_example(
                repository,
                self.run_root,
                release=release,
                made=self.made,
                inventor_id="eve",
                receipt=receipt,
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
            )

    def test_public_example_copies_exact_pdf_manual_without_cover_or_rich_page_identity(self):
        release = self._release()
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
        self.assertEqual((target / "MANUAL.pdf").read_bytes(), source_manual.read_bytes())
        self.assertFalse((target / "MANUAL.md").exists())
        publication = json.loads(
            (target / "PUBLICATION.json").read_text(encoding="utf-8")
        )
        self.assertEqual(publication["identities"]["manual_path"], "MANUAL.pdf")
        self.assertNotIn("factory_content_sha256", publication["identities"])
        self.assertNotIn("cover_url", publication["publication"])
        self.assertIn("`MANUAL.pdf`", (target / "README.md").read_text())


if __name__ == "__main__":
    unittest.main()
