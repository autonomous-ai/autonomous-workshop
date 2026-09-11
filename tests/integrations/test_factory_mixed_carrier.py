"""Host effect identity tests; no network, CAD execution or physical claims."""

import hashlib
import io
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

from tests.integrations import test_factory as fixtures
from workshop.artifacts import build_artifact_manifest, validate_artifact_payload
from workshop.errors import AmbiguousEffectError, ContractError, EffectError, ReceiptError
from workshop.integrations import factory
from workshop.artifacts.factory_carrier import MIXED_CARRIER_FORMAT, validate_mixed_carrier
from workshop.runtime import Receipt


class MixedCarrierFactoryTest(unittest.TestCase):
    setUp = fixtures.FactoryReleaseTest.setUp
    writer = fixtures.FactoryReleaseTest.writer
    use_make_output_release = fixtures.FactoryReleaseTest.use_make_output_release
    _use_public_presentation = fixtures.FactoryReleaseTest._use_public_presentation
    _reseal_product = fixtures.FactoryReleaseTest._reseal_product

    def mixed(self, **kwargs):
        self.anchor = self._use_public_presentation()
        self.transport = fixtures.FactoryTransport(include_thumbnails=False, **kwargs)

    def send(self, method, url, headers, body, timeout):
        if url.endswith("/workshop-release-page.json"):
            return factory.HttpResponse(200, {}, self.anchor)
        return self.transport(method, url, headers, body, timeout)

    def run_writer(self):
        return self.writer(self.send)(self.context, self.release, self.manifest)

    def intent(self):
        return self.ledger.latest("verified-toy", "factory-import")

    def cache_file(self):
        files = list((self.ledger.path.parent / "factory-carriers").glob("*.zip"))
        self.assertEqual(len(files), 1)
        return files[0]

    def upload_bytes(self):
        call = next(call for call in self.transport.calls if call[1].endswith("/designs/import"))
        return fixtures.multipart_parts(call[2], call[3])["file"][0]

    def planned(self):
        with mock.patch.object(self.ledger, "begin", side_effect=RuntimeError("interrupted before sending")):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                self.run_writer()
        self.assertEqual(self.intent().state, "planned")
        self.assertEqual(self.transport.imports, 0)

    def test_exact_public_bytes_private_persistence_and_receipts(self):
        self.mixed()
        original = build_artifact_manifest(self.made.artifact_root, created_at="content-addressed")
        prepare = self.ledger.prepare

        def after_durable_carrier(**kwargs):
            cached = self.cache_file()
            content, digest, artifact = validate_mixed_carrier(cached.read_bytes())
            self.assertEqual(digest, kwargs["pack_sha256"])
            self.assertEqual(artifact, kwargs["handoff_artifact_sha256"])
            return prepare(**kwargs)

        with mock.patch.object(self.ledger, "prepare", side_effect=after_durable_carrier):
            draft = self.run_writer()
        intent = self.intent()
        cache = self.cache_file()
        content = self.upload_bytes()
        self.assertEqual(cache.read_bytes(), content)
        self.assertEqual(cache.name, intent.handoff_artifact_sha256 + ".zip")
        self.assertEqual(cache.stat().st_mode & 0o777, 0o600)
        self.assertEqual(cache.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(intent.request["carrier_format"], MIXED_CARRIER_FORMAT)
        self.assertEqual(draft.details["carrier_format"], MIXED_CARRIER_FORMAT)
        self.assertEqual(draft.payload_sha256, hashlib.sha256(content).hexdigest())
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            self.assertTrue(all(item.compress_type == zipfile.ZIP_DEFLATED for item in archive.infolist()))
            self.assertEqual(archive.read("assembled.step"), archive.read("public/assembled.step"))
            self.assertEqual(archive.read("assembled_review/_assembled.png"), archive.read("public/hero.png"))
            for item in self.page["public_projection"]["files"]:
                self.assertEqual(archive.read(item["path"]), (self.made.artifact_root / item["path"]).read_bytes())
            for path in archive.namelist():
                self.assertNotIn(fixtures.PRIVATE_SENTINEL, archive.read(path))
            self.assertNotIn("internal/manufacturing.json", archive.namelist())
        with self.assertRaises(ContractError):
            validate_artifact_payload(content)  # Canonical Pack was not broadened.
        with mock.patch.object(factory, "build_mixed_carrier", side_effect=AssertionError("never recompress")):
            self.assertEqual(self.run_writer(), draft)
            public = factory.FactoryPublicTransition(self.ledger, factory.FactoryAgentSession(
                factory.FactoryAgentCredentials("alice", "test-secret"), transport=self.send,
            )).publish(draft)
        self.assertTrue(public.is_verified_public)
        self.assertEqual(public.details["carrier_format"], MIXED_CARRIER_FORMAT)
        self.assertEqual(self.ledger.latest("verified-toy", "factory-publish").request["carrier_format"], MIXED_CARRIER_FORMAT)
        self.assertEqual(self.transport.imports, 1)
        self.assertEqual(build_artifact_manifest(self.made.artifact_root, created_at="content-addressed"), original)

    def test_pre_intent_orphan_is_reused_without_recompression(self):
        self.mixed()
        with mock.patch.object(self.ledger, "prepare", side_effect=RuntimeError("interrupted before intent")):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                self.run_writer()
        content = self.cache_file().read_bytes()
        self.assertIsNone(self.intent())
        with mock.patch.object(factory, "build_mixed_carrier", side_effect=AssertionError("new zlib must not replace first bytes")):
            self.run_writer()
        self.assertEqual(self.upload_bytes(), content)

    def test_planned_and_rejected_keep_first_bytes(self):
        self.mixed(import_status=422)
        self.planned()
        content = self.cache_file().read_bytes()
        with mock.patch.object(factory, "build_mixed_carrier", side_effect=AssertionError("no recompression")):
            with self.assertRaises(EffectError):
                self.run_writer()
            self.assertEqual(self.intent().state, "rejected")
            self.transport.import_status = 201
            draft = self.run_writer()
        self.assertTrue(draft.is_verified_draft)
        self.assertEqual(self.upload_bytes(), content)
        self.assertEqual(self.cache_file().read_bytes(), content)

    def test_unknown_outcome_reconciles_only_same_bytes(self):
        self.mixed(fail_get=True)
        with self.assertRaises(AmbiguousEffectError):
            self.run_writer()
        self.assertEqual(self.intent().state, "unknown")
        content = self.cache_file().read_bytes()
        self.transport.fail_get = False
        with mock.patch.object(factory, "build_mixed_carrier", side_effect=AssertionError("no recompression")):
            self.assertTrue(self.run_writer().is_verified_draft)
        self.assertEqual(self.transport.imports, 1)
        self.assertEqual(self.cache_file().read_bytes(), content)

    def test_valid_alternate_compression_cannot_replace_bound_bytes(self):
        self.mixed(fail_get=True)
        with self.assertRaises(AmbiguousEffectError):
            self.run_writer()
        intent = self.intent()
        self.assertEqual(intent.state, "unknown")
        cache = self.cache_file()
        original = cache.read_bytes()
        buffer = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(original)) as source, zipfile.ZipFile(buffer, "w") as target:
            for entry in source.infolist():
                info = zipfile.ZipInfo(entry.filename, entry.date_time)
                info.create_system = entry.create_system
                info.external_attr = entry.external_attr
                target.writestr(info, source.read(entry.filename), compress_type=zipfile.ZIP_DEFLATED, compresslevel=1)
        alternate = buffer.getvalue()
        self.assertNotEqual(alternate, original)
        self.assertEqual(validate_mixed_carrier(alternate)[2], intent.handoff_artifact_sha256)
        cache.write_bytes(alternate)
        self.transport.fail_get = False
        with mock.patch.object(factory, "build_mixed_carrier", side_effect=AssertionError("no recompression")):
            with self.assertRaisesRegex(ContractError, "intent sha256"):
                self.run_writer()
        self.assertEqual(self.transport.imports, 1)
        self.assertEqual(self.intent().state, "unknown")

    def test_missing_changed_symlink_or_public_cache_refuses_before_upload(self):
        for mutation in ("missing", "changed", "symlink", "public-file", "public-directory"):
            with self.subTest(mutation=mutation):
                # A fresh independent saved intent for every failure boundary.
                self.setUp()
                self.mixed()
                self.planned()
                cache = self.cache_file()
                if mutation == "missing":
                    cache.unlink()
                elif mutation == "changed":
                    cache.write_bytes(cache.read_bytes() + b"changed")
                elif mutation == "symlink":
                    real = cache.with_suffix(".saved")
                    cache.rename(real)
                    cache.symlink_to(real)
                elif mutation == "public-file":
                    cache.chmod(0o644)
                else:
                    cache.parent.chmod(0o755)
                with mock.patch.object(factory, "build_mixed_carrier", side_effect=AssertionError("must refuse, never rebuild")):
                    with self.assertRaises(ContractError):
                        self.run_writer()
                self.assertEqual(self.transport.imports, 0)
                self.assertEqual(self.intent().state, "planned")

    def test_resealed_current_handoff_drift_is_refused_before_new_cache(self):
        self.mixed()
        self.planned()
        existing = self.cache_file()
        self.page["summary"] = "Changed customer description."
        self.anchor = fixtures.canonical_json(self.page)
        (self.release / "product.json").write_bytes(self.anchor)
        self.manifest = build_artifact_manifest(self.release, created_at="content-addressed")
        with self.assertRaisesRegex(ContractError, "current handoff"):
            self.run_writer()
        self.assertEqual(self.cache_file(), existing)
        self.assertEqual(self.transport.imports, 0)

    def test_historical_mixed_intent_without_format_stays_stored(self):
        self.mixed()
        # Simulate the host's pre-existing stored selection, then let the real
        # ledger persist/replay the exact resulting historical request.
        historical = SimpleNamespace(request={"import_root_mapping": factory.FACTORY_IMPORT_ROOT_MAPPING})
        with mock.patch.object(self.ledger, "latest", return_value=historical):
            draft = self.run_writer()
        content = self.upload_bytes()
        validate_artifact_payload(content)
        self.assertNotIn("carrier_format", self.intent().request)
        self.assertNotIn("carrier_format", draft.details)
        self.assertFalse((self.ledger.path.parent / "factory-carriers").exists())
        with mock.patch.object(factory, "build_mixed_carrier", side_effect=AssertionError("legacy must remain stored")):
            self.assertEqual(self.run_writer(), draft)
        self.assertEqual(self.transport.imports, 1)

    def test_print_make_output_stays_stored(self):
        self.anchor = self.use_make_output_release()
        self.transport = fixtures.FactoryTransport(include_thumbnails=False)
        draft = self.run_writer()
        validate_artifact_payload(self.upload_bytes())
        self.assertNotIn("carrier_format", draft.details)
        self.assertNotIn("carrier_format", self.intent().request)

    def test_unknown_null_and_nonmixed_formats_fail_before_import(self):
        for value in (None, "zip-deflate", 1, MIXED_CARRIER_FORMAT):
            with self.subTest(value=value):
                self.setUp()
                self.anchor = self.use_make_output_release()  # No mixed projection.
                self.transport = fixtures.FactoryTransport(include_thumbnails=False)
                self.ledger.prepare(kind="factory-import", product_id="verified-toy",
                    request={"carrier_format": value}, pack_sha256="1" * 64,
                    handoff_artifact_sha256="2" * 64, product_artifact_sha256=self.made.artifact_sha256,
                    release_sha256=self.manifest.artifact_sha256, playtest_evidence_sha256="3" * 64)
                with self.assertRaises(ContractError):
                    self.run_writer()
                self.assertEqual(self.transport.imports, 0)

    def test_explicit_format_required_and_receipt_downgrade_refused(self):
        self.mixed()
        draft = self.run_writer()
        content = self.upload_bytes()
        with self.assertRaisesRegex(ContractError, "explicit format"):
            factory._assert_factory_handoff(content)
        factory._assert_factory_handoff(content, carrier_format=MIXED_CARRIER_FORMAT)
        details = dict(draft.details)
        details.pop("carrier_format")
        changed = Receipt.from_dict({**draft.to_dict(), "details": details})
        with self.assertRaises(ReceiptError):
            factory.FactoryReleaseWriter._assert_private_receipt(changed, self.intent())
        transition = factory.FactoryPublicTransition(self.ledger, factory.FactoryAgentSession(
            factory.FactoryAgentCredentials("alice", "test-secret"), transport=self.send))
        with self.assertRaises(ReceiptError):
            transition.publish(changed)
        self.assertIsNone(self.ledger.latest("verified-toy", "factory-publish"))
        self.assertFalse(self.transport.public)

    def test_unknown_codec_on_existing_mixed_intent_is_not_inferred(self):
        self.mixed()
        self.ledger.prepare(kind="factory-import", product_id="verified-toy",
            request={"carrier_format": "future-format"}, pack_sha256="1" * 64,
            handoff_artifact_sha256="2" * 64, product_artifact_sha256=self.made.artifact_sha256,
            release_sha256=self.manifest.artifact_sha256, playtest_evidence_sha256="3" * 64)
        with self.assertRaisesRegex(ContractError, "unsupported"):
            self.run_writer()
        self.assertEqual(self.transport.imports, 0)
        self.assertFalse((self.ledger.path.parent / "factory-carriers").exists())


if __name__ == "__main__":
    unittest.main()
