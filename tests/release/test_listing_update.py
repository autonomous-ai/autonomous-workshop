"""Listing Updates: a version appended to a public design (ADR 0097)."""

import hashlib
import io
import json
import math
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.integrations.test_factory import RootSelectingFactoryTransport, canonical_json
from tests.release.test_direct_publish import (
    INVENTOR,
    PRODUCT_ID,
    STEP,
    TOOL,
    NoNetwork,
    pack_archive,
    reseal,
    write_evidence,
    write_project,
)
from workshop.integrations.factory import HttpResponse
from workshop.integrations.factory_listing import (
    ListingUpdatePlan,
    append_publication_version,
    factory_sale_price_cents,
)
from workshop.runtime import EffectLedger


SLUG = "verified-toy"
OLD_EXTRAS = [{"name": "Old magnet", "price_cents": 300}]


def formula(grams, extras_cents):
    cost = math.ceil(grams * 5.2) + 1500 + extras_cents
    return min(max((cost + 99) // 100 * 100, 100), 1_000_000)


class ListingFactoryTransport(RootSelectingFactoryTransport):
    """A public design whose versions are sliced and repriced as Factory does."""

    def __init__(self):
        super().__init__()
        self.extras = []
        self.weights = {"history-1": 400.0}
        self.next_weight = 180.0
        self.slice_polls = {}
        self.slice_delay = 2
        self.slice_fails = False
        self.measured = 400.0
        self.hand_price = None
        self.infill = 15
        self.author = "owner-alice"
        self.extra_puts = []
        self.drop_extras_write = False
        self.extras_status = 200

    # --- Factory's own state -------------------------------------------------
    def price(self):
        if self.hand_price is not None:
            return self.hand_price
        if self.measured is None:
            return 2400
        return formula(self.measured, sum(item["price_cents"] for item in self.extras))

    def design(self):
        design = super().design()
        design["extra_materials"] = [dict(item) for item in self.extras]
        design["print_settings"] = {"infill_percent": self.infill}
        design["author"] = {"id": self.author}
        design["owner_id"] = self.author
        if design.get("listing"):
            design["listing"]["price_cents"] = self.price()
        return design

    def slice_job(self):
        history = self.history
        remaining = self.slice_polls.setdefault(
            history, 0 if history == "history-1" else self.slice_delay
        )
        if remaining > 0:
            self.slice_polls[history] = remaining - 1
            return {"id": "job-" + history, "history_id": history, "status": "slicing"}
        if self.slice_fails and history != "history-1":
            return {"id": "job-" + history, "history_id": history, "status": "failed",
                    "error": {"stage": "slice"}, "will_retry": False}
        weight = self.weights.setdefault(history, self.next_weight)
        self.measured = weight
        return {"id": "job-" + history, "history_id": history, "status": "done",
                "totals": {"weight_g": weight}}

    def __call__(self, method, url, headers, body, timeout):
        if method == "GET" and url.endswith("/designs/%s/slice" % SLUG):
            self.calls.append((method, url, dict(headers), body, timeout))
            return HttpResponse(200, {}, canonical_json(self.slice_job()))
        if method == "PUT" and url.endswith("/designs/%s/extra-materials" % SLUG):
            self.calls.append((method, url, dict(headers), body, timeout))
            items = json.loads(body.decode())["extra_materials"]
            self.extra_puts.append(items)
            if self.extras_status != 200:
                return HttpResponse(self.extras_status, {}, b'{"error":"no"}')
            if not self.drop_extras_write:
                self.extras = items
            return HttpResponse(200, {}, canonical_json({"extra_materials": self.extras}))
        return super().__call__(method, url, headers, body, timeout)

    def sends(self):
        return [(method, url.rsplit("/", 1)[-1]) for method, url, *_ in self.calls
                if method != "GET" and not url.endswith("/auth/agent/login")]


class Clock:
    def __init__(self):
        self.now = 0.0

    def sleep(self, seconds):
        self.now += seconds

    def __call__(self):
        return self.now


class ListingUpdateTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = write_project(self.root / "widget")
        self.home = self.root / "home"
        self.environment = {"WORKSHOP_HOME": str(self.home)}
        folder = self.home / "credentials" / "inventors"
        folder.mkdir(parents=True)
        os.chmod(folder, 0o700)
        credential = folder / (INVENTOR + ".env")
        credential.write_text(
            "FACTORY_USERNAME=alice\nFACTORY_PASSWORD=test-secret\nFACTORY_INVENTOR_ID=%s\n" % INVENTOR
        )
        os.chmod(credential, 0o600)
        write_evidence(self.project)
        self.transport = ListingFactoryTransport()
        code, out, err = self.tool("--cad-dir", str(self.project), "--product-id", PRODUCT_ID, "--live")
        self.assertEqual((code, err), (0, ""), out)
        self.transport.extras = [dict(item) for item in OLD_EXTRAS]
        self.transport.calls.clear()
        self.archive = self.pack()

    def pack(self, record=None):
        archive = self.root / ("%s-%s" % (INVENTOR, SLUG))
        if archive.exists():
            shutil.rmtree(archive)
        archive.mkdir()
        pack_archive(self.project, archive)
        (archive / "publication").mkdir()
        (archive / "publication" / "PUBLICATION.json").write_text(json.dumps(record or {
            "schema_version": 1,
            "publication": {"adapter": "factory", "status": "public", "slug": SLUG,
                            "page_url": "https://www.autonomous.ai/toys/product/" + SLUG,
                            "listing": {"price_cents": 2400, "currency": "USD"}},
        }))
        reseal(archive)
        return archive

    def tool(self, *arguments, transport=None, clock=None):
        out, err = io.StringIO(), io.StringIO()
        clock = clock or Clock()
        code = TOOL.main(
            [*arguments, "--inventor", INVENTOR],
            environment=self.environment,
            transports={"transport": transport or self.transport, "sleeper": clock.sleep},
            out=out, err=err, sleeper=clock.sleep, clock=clock,
        )
        return code, out.getvalue(), err.getvalue()

    def update(self, *arguments, **options):
        return self.tool("--archive", str(self.archive), "--update-listing", SLUG,
                         "--reason", "reprice", *arguments, **options)

    def predicted(self, grams="180"):
        return ("--predicted-grams", grams, "--predicted-grams-source", "orca test weigh")

    def preview_code(self, *arguments):
        code, out, err = self.update(*self.predicted(), *arguments)
        self.assertEqual((code, err), (0, ""), out)
        match = re.search(r"(?m)^  confirmation: (lu-[0-9a-f]{12})$", out)
        self.assertIsNotNone(match, out)
        return match.group(1), out

    def intents(self):
        ledger = EffectLedger(self.home / "direct-publish" / PRODUCT_ID / "factory-effects.sqlite3")
        return ledger.latest(PRODUCT_ID, "factory-import-version")

    # ------------------------------------------------------------------ preview
    def test_preview_sends_nothing_and_prints_both_prices_and_a_code(self):
        code, out = self.preview_code()
        self.assertEqual(self.transport.sends(), [])
        self.assertEqual(self.transport.versions, 0)
        self.assertIsNone(self.intents())
        self.assertIn("listing update preview: authenticated Factory reads only", out)
        self.assertIn("current:     $39.00, listing active, version history-1", out)
        self.assertIn("measured 400.00 g, extras Old magnet $3.00", out)
        self.assertIn("Factory's formula for that gives $39.00: the price follows the formula", out)
        self.assertIn("live version made from %s (same)" % hashlib.sha256(STEP + b"widget").hexdigest(), out)
        self.assertIn("new extras:  (none) = $0.00", out)
        self.assertIn("predicted:   180.00 g (orca test weigh) -> $25.00", out)
        self.assertIn("to run it: the same command with --live --confirm %s" % code, out)

    def test_preview_without_predicted_grams_gives_no_code(self):
        code, out, err = self.update()
        self.assertEqual((code, err), (0, ""))
        self.assertIn("predicted:   unknown (no --predicted-grams)", out)
        self.assertIn("confirmation: none (the update cannot run)", out)
        self.assertNotIn("--live --confirm", out)

    def test_a_price_off_the_formula_is_flagged_as_possibly_hand_set(self):
        self.transport.hand_price = 9900
        _, out = self.preview_code()
        self.assertIn("the price does NOT follow it; it may have been set by hand", out)

    # --------------------------------------------------------------- live runs
    def test_live_needs_the_code_and_refuses_a_stale_one(self):
        code, _, err = self.update(*self.predicted(), "--live")
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("needs --confirm CODE", err)
        code, _, err = self.update(*self.predicted(), "--live", "--confirm", "lu-000000000000")
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("does not match this update now", err)
        self.assertEqual(self.transport.sends(), [])

    def test_a_reprice_appends_one_version_and_sends_extras_after_the_slice(self):
        confirm, _ = self.preview_code()
        code, out, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(self.transport.versions, 1)
        self.assertEqual(self.transport.sends(), [("POST", "import"), ("PUT", "extra-materials")])
        methods = [(method, url.rsplit("/", 1)[-1]) for method, url, *_ in self.transport.calls]
        post, put = methods.index(("POST", "import")), methods.index(("PUT", "extra-materials"))
        done = max(index for index, call in enumerate(methods) if call == ("GET", "slice")
                   and index < put)
        self.assertLess(post, done)
        self.assertEqual(self.transport.extra_puts, [[]])
        self.assertIn("slug: %s" % SLUG, out)
        self.assertIn("public: https://www.autonomous.ai/toys/product/%s" % SLUG, out)
        self.assertIn("version: history-2 (was history-1)", out)
        self.assertIn("price: $39.00 -> $25.00 (predicted $25.00)", out)
        self.assertNotIn("possibly set by hand", out)
        record = json.loads(re.search(r"(?m)^publication-record: (.*)$", out).group(1))
        self.assertEqual(record["schema_version"], 2)
        self.assertEqual(record["publication"]["slug"], SLUG)
        self.assertEqual(record["publication"]["listing"]["price_cents"], 2500)
        self.assertEqual([entry["history_id"] for entry in record["versions"]], ["history-2"])
        self.assertEqual(record["versions"][0]["reason"], "reprice")
        self.assertEqual(self.intents().state, "succeeded")
        # The same command again reads the receipt back; nothing is sent.
        self.transport.calls.clear()
        code, out, _ = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual(code, 0)
        self.assertEqual(self.transport.sends(), [])
        self.assertEqual(self.transport.versions, 1)

    def test_a_hand_set_price_is_reported_not_failed(self):
        self.transport.hand_price = 9900
        confirm, _ = self.preview_code()
        code, out, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual((code, err), (0, ""), out)
        self.assertIn("price: $99.00 -> $99.00 (predicted $25.00); price not repriced (possibly set by hand)", out)

    def test_a_lost_response_is_reconciled_by_a_rerun_without_a_second_version(self):
        confirm, _ = self.preview_code()
        self.transport.version_failure = "lost-response"
        self.transport.slice_delay = 10_000
        code, _, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual(code, TOOL.EXIT_EFFECT)
        self.assertIn("still slicing", err)
        self.assertEqual(self.transport.versions, 1)
        self.assertEqual(self.intents().state, "unknown")
        self.transport.version_failure = None
        self.transport.slice_polls["history-2"] = 0
        code, out, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(self.transport.versions, 1)
        self.assertEqual(self.intents().state, "succeeded")

    def test_a_send_that_never_landed_is_not_resent(self):
        confirm, _ = self.preview_code()
        self.transport.version_failure = "before-send"
        code, _, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual(code, TOOL.EXIT_EFFECT)
        self.assertIn("still shows the base version history-1", err)
        self.transport.version_failure = None
        code, _, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual(code, TOOL.EXIT_EFFECT)
        self.assertEqual(self.transport.versions, 1)
        # A new update is refused while that one is unresolved.
        self.transport.next_weight = 170.0
        code, _, err = self.update(*self.predicted("170"), "--live", "--confirm", "lu-000000000000")
        self.assertEqual(code, TOOL.EXIT_EFFECT)
        self.assertIn("an earlier Listing Update (code %s) is unresolved" % confirm, err)

    def test_a_refused_version_with_no_change_is_rejected(self):
        confirm, _ = self.preview_code()
        self.transport.version_failure = 409
        code, _, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual(code, TOOL.EXIT_EFFECT)
        self.assertIn("refused the version with HTTP 409; nothing changed", err)
        self.assertEqual(self.intents().state, "rejected")

    def test_a_base_that_moved_is_refused(self):
        confirm, _ = self.preview_code()
        self.transport.history = "history-9"
        self.transport.snapshots["history-9"] = self.transport.snapshots["history-1"]
        self.transport.weights["history-9"] = 410.0
        self.transport.slice_polls["history-9"] = 0
        code, _, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("does not match this update now", err)
        self.assertEqual(self.transport.sends(), [])

    def test_a_draft_or_another_authors_design_is_refused(self):
        self.transport.author = "owner-bob"
        _, out, _ = self.update(*self.predicted())
        self.assertIn("the design's author is not this Inventor's Factory account", out)
        self.transport.author = "owner-alice"
        self.transport.public = False
        _, out, _ = self.update(*self.predicted())
        self.assertIn("the design is draft, not public", out)
        self.assertNotIn("to run it", out)

    def test_a_reprice_of_changed_geometry_is_refused(self):
        (self.project / "widget.step").write_bytes(STEP + b"widget, thicker")
        write_evidence(self.project)
        self.archive = self.pack()
        code, out, _ = self.update(*self.predicted())
        self.assertEqual(code, 0)
        self.assertIn("a reprice must publish the live printed geometry", out)
        self.assertIn("as --reason fix with fresh gate evidence", out)
        self.assertNotIn("to run it", out)

    def test_a_live_infill_override_is_refused(self):
        self.transport.infill = 30
        _, out, _ = self.update(*self.predicted())
        self.assertIn("prints at 30% infill and a new version would drop that override", out)

    def test_a_fix_needs_gate_evidence(self):
        (self.project / "widget.step").write_bytes(STEP + b"widget, thicker")
        self.archive = self.pack()
        code, out, _ = self.tool("--archive", str(self.archive), "--update-listing", SLUG,
                                 "--reason", "fix", *self.predicted())
        self.assertEqual(code, 0)
        self.assertIn("a fix needs gate evidence", out)
        self.assertIn("preview stopped before any Factory read", out)

    def test_a_slice_that_never_lands_resumes_without_resending(self):
        confirm, _ = self.preview_code()
        self.transport.slice_delay = 10_000
        code, _, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual(code, TOOL.EXIT_EFFECT)
        self.assertIn("the extras wait for it", err)
        self.assertEqual(self.transport.extra_puts, [])
        self.transport.slice_polls["history-2"] = 1
        code, out, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(self.transport.versions, 1)
        self.assertEqual(self.transport.extra_puts, [[]])

    def test_a_failed_slice_stops_before_the_extras(self):
        confirm, _ = self.preview_code()
        self.transport.slice_fails = True
        code, _, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual(code, TOOL.EXIT_EFFECT)
        self.assertIn("slice of the new version failed (slice)", err)
        self.assertEqual(self.transport.extra_puts, [])
        self.assertNotIn(("POST", "unpublish"), self.transport.sends())

    def test_extras_that_read_back_different_are_sent_again_by_put_only(self):
        confirm, _ = self.preview_code()
        self.transport.drop_extras_write = True
        code, _, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual(code, TOOL.EXIT_EFFECT)
        self.assertIn("extras read back different", err)
        self.transport.drop_extras_write = False
        code, out, err = self.update(*self.predicted(), "--live", "--confirm", confirm)
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(self.transport.versions, 1)
        self.assertEqual(self.transport.extra_puts, [[], []])

    def test_a_second_update_follows_a_succeeded_one(self):
        confirm, _ = self.preview_code()
        self.assertEqual(self.update(*self.predicted(), "--live", "--confirm", confirm)[0], 0)
        _, out, _ = self.update(*self.predicted())
        record = json.loads(re.search(r"(?m)^publication-record: (.*)$",
                                      self.update(*self.predicted(), "--live", "--confirm", confirm)[1]).group(1))
        self.archive = self.pack(record)
        self.transport.next_weight = 170.0
        second, out = self.preview_code()
        self.assertNotEqual(second, confirm)
        self.assertIn("version history-2", out)
        code, out, err = self.update(*self.predicted(), "--live", "--confirm", second)
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(self.transport.versions, 2)

    def test_without_update_listing_the_archive_is_still_refused(self):
        code, out, _ = self.tool("--archive", str(self.archive))
        self.assertEqual(code, 0)
        self.assertIn("archive already records a publication", out)
        self.assertIn("--update-listing %s --reason fix|reprice" % SLUG, out)

    def test_an_update_needs_a_local_receipt_for_the_slug(self):
        shutil.rmtree(self.home / "direct-publish")
        code, _, err = self.update(*self.predicted(), transport=NoNetwork())
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("no local ledger records publishing %s" % SLUG, err)

    def test_the_slug_must_be_the_archives(self):
        code, _, err = self.tool("--archive", str(self.archive), "--update-listing", "other-toy",
                                 "--reason", "reprice", transport=NoNetwork())
        self.assertEqual(code, TOOL.EXIT_INPUT)
        self.assertIn("does not match the archive's listing %s" % SLUG, err)


class ReconcilePublishTest(unittest.TestCase):
    """--reconcile-publish settles an unknown publish by readback alone."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = write_project(self.root / "widget")
        self.home = self.root / "home"
        self.environment = {"WORKSHOP_HOME": str(self.home)}
        folder = self.home / "credentials" / "inventors"
        folder.mkdir(parents=True)
        os.chmod(folder, 0o700)
        credential = folder / (INVENTOR + ".env")
        credential.write_text(
            "FACTORY_USERNAME=alice\nFACTORY_PASSWORD=test-secret\nFACTORY_INVENTOR_ID=%s\n" % INVENTOR
        )
        os.chmod(credential, 0o600)
        write_evidence(self.project)

    def publish_unknown(self, transport):
        """Publish once while Factory lists the design only after the tool gives up."""

        out, err = io.StringIO(), io.StringIO()
        clock = Clock()
        code = TOOL.main(
            ["--cad-dir", str(self.project), "--product-id", PRODUCT_ID, "--inventor", INVENTOR, "--live"],
            environment=self.environment,
            transports={"transport": transport, "sleeper": clock.sleep},
            out=out, err=err, sleeper=clock.sleep, clock=clock,
        )
        self.assertEqual(code, TOOL.EXIT_EFFECT, out.getvalue() + err.getvalue())
        ledger = EffectLedger(self.home / "direct-publish" / PRODUCT_ID / "factory-effects.sqlite3")
        self.assertEqual(ledger.latest(PRODUCT_ID, "factory-publish").state, "unknown")

    def reconcile(self, transport):
        out, err = io.StringIO(), io.StringIO()
        code = TOOL.main(
            ["--reconcile-publish", PRODUCT_ID, "--inventor", INVENTOR],
            environment=self.environment,
            transports={"transport": transport, "sleeper": Clock().sleep}, out=out, err=err,
        )
        return code, out.getvalue(), err.getvalue()

    def test_an_unknown_publish_settles_from_readback_and_never_sends(self):
        transport = UnlistedTransport()
        self.publish_unknown(transport)
        publishes = transport.publishes
        transport.listed = True
        transport.calls.clear()
        code, out, err = self.reconcile(transport)
        self.assertEqual((code, err), (0, ""), out)
        self.assertIn("publish intent is unknown", out)
        self.assertIn("reconciled:    publish intent is now succeeded", out)
        self.assertIn("listing: $24.00 active", out)
        self.assertEqual([call[0] for call in transport.calls if not call[1].endswith("/login")],
                         ["GET"] * len([call for call in transport.calls if not call[1].endswith("/login")]))
        self.assertEqual(transport.publishes, publishes)
        code, out, _ = self.reconcile(transport)
        self.assertEqual(code, 0)
        self.assertIn("nothing to reconcile", out)

    def test_a_still_unlisted_design_stays_unknown(self):
        transport = UnlistedTransport()
        self.publish_unknown(transport)
        transport.calls.clear()
        code, _, err = self.reconcile(transport)
        self.assertEqual(code, TOOL.EXIT_EFFECT)
        self.assertTrue(all(call[0] == "GET" or call[1].endswith("/login") for call in transport.calls))
        ledger = EffectLedger(self.home / "direct-publish" / PRODUCT_ID / "factory-effects.sqlite3")
        self.assertEqual(ledger.latest(PRODUCT_ID, "factory-publish").state, "unknown")


class UnlistedTransport(RootSelectingFactoryTransport):
    """Factory accepts the publish but shows no listing until ``listed``."""

    def __init__(self):
        super().__init__()
        self.listed = False
        self.publishes = 0

    def design(self):
        design = super().design()
        if self.public and not self.listed:
            design["listing"] = None
        return design

    def __call__(self, method, url, headers, body, timeout):
        if method == "POST" and url.endswith("/publish"):
            self.publishes += 1
        return super().__call__(method, url, headers, body, timeout)


class PlanTest(unittest.TestCase):
    def test_the_price_mirrors_factorys_formula(self):
        self.assertEqual(factory_sale_price_cents(225.49, 0), 2700)
        self.assertEqual(factory_sale_price_cents(494.73, 0), 4100)
        self.assertEqual(factory_sale_price_cents(100.0, 0), 2100)
        self.assertEqual(factory_sale_price_cents(100.0, 1), 2100)
        self.assertEqual(factory_sale_price_cents(100.0, 81), 2200)
        self.assertIsNone(factory_sale_price_cents(None, 500))
        self.assertIsNone(factory_sale_price_cents(0, 500))

    def test_reason_and_prediction_are_checked(self):
        base = dict(slug=SLUG, source_primary_path="a.step", source_primary_sha256="0" * 64,
                    kept_bodies=(), stripped_bodies=(), extra_materials=())
        with self.assertRaisesRegex(Exception, "--reason must be one of fix, reprice"):
            ListingUpdatePlan(reason="rename", **base)
        with self.assertRaisesRegex(Exception, "go together"):
            ListingUpdatePlan(reason="reprice", predicted_weight_g=10.0, **base)
        with self.assertRaisesRegex(Exception, "positive number"):
            ListingUpdatePlan(reason="reprice", predicted_weight_g=-1.0,
                              predicted_weight_source="x", **base)

    def test_a_schema_1_record_gains_versions_once(self):
        record = {"schema_version": 1, "publication": {"slug": SLUG, "listing": {"price_cents": 4100}}}
        version = {"history_id": "h2", "price_after_cents": 2700}
        updated = append_publication_version(record, version)
        self.assertEqual(updated["schema_version"], 2)
        self.assertEqual(updated["versions"], [version])
        self.assertEqual(updated["publication"]["listing"], {"price_cents": 2700, "currency": "USD"})
        self.assertEqual(append_publication_version(updated, version)["versions"], [version])
        self.assertEqual(record["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
