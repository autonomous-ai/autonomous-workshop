"""Tests for harness/publish.py — the Layer-1 validator wall-by-wall, the
multipart encoder against golden bytes, idempotency, dry-run, and the flip's
refusals. Zero network: every test monkeypatches publish._http; a test that
lets a real socket open has already failed."""

import json
import io
import os
import shutil
import stat
import tempfile
import unittest
import zipfile
from unittest import mock

from harness import ledger, publish, queue

SLUG = "tower-duel"

GOOD_DESCRIPTION = (
    "A tactical tower-stacking duel for 2-4 players, 30 minutes. "
    + publish.DISCLOSURE_LINE
)
GOOD_TAGS = ["board-game", "3d-print", "cadquery", publish.AI_TAG]


def _fail_http(*args, **kwargs):
    raise AssertionError("_http called — this code path must be offline")


class PublishHome(unittest.TestCase):
    """Temp BOB_HOME + a synthetic, fully-green game dir. Each wall test
    breaks exactly one brick and asserts the validator names it."""

    ENV_KEYS = ("BOB_HOME", "BOB_PUBLISH_DRY_RUN", "BOB_PRICE_OVERRIDE",
                "BOB_TELEGRAM_TOKEN", "BOB_TELEGRAM_CHAT", "BOB_PANDA_API",
                "BOB_PANDA_ALLOWED_ORIGINS", "BOB_CORE_SRC")

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="bob-test-pub-")
        self._env = {}
        for key in self.ENV_KEYS:
            self._env[key] = os.environ.pop(key, None)
        os.environ["BOB_HOME"] = self.home
        self._orig_http = publish._http
        publish._http = _fail_http  # default: offline; tests opt in
        self._orig_entries = publish.MAX_ZIP_ENTRIES
        self._orig_bytes = publish.MAX_ZIP_BYTES

    def tearDown(self):
        publish._http = self._orig_http
        publish.MAX_ZIP_ENTRIES = self._orig_entries
        publish.MAX_ZIP_BYTES = self._orig_bytes
        for key in self.ENV_KEYS:
            if self._env[key] is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = self._env[key]
        shutil.rmtree(self.home, ignore_errors=True)

    # -- fixtures ------------------------------------------------------------

    def gdir(self):
        return os.path.join(self.home, "games", SLUG)

    def make_game(self):
        g = self.gdir()
        os.makedirs(os.path.join(g, "%s_review" % SLUG), exist_ok=True)
        with open(os.path.join(g, "main.py"), "w") as fh:
            fh.write("def gen_step():\n    return None\n")
        with open(os.path.join(g, "assembled.stl"), "wb") as fh:
            fh.write(b"solid tower\nendsolid tower\n")
        with open(os.path.join(g, "%s_review" % SLUG, "_assembled.png"),
                  "wb") as fh:
            fh.write(b"\x89PNG fake bytes")
        with open(os.path.join(g, "RULES.md"), "w") as fh:
            fh.write("# Tower Duel\n\nStack towers. Win.\n")
        self.write_listing()

    def write_listing(self, **overrides):
        listing = {
            "title": "Tower Duel",
            "description": GOOD_DESCRIPTION,
            "tags": list(GOOD_TAGS),
            "category": "toys-games",
            "prompt": "a tower stacking duel",
            "use_case": {"label": "How a round plays",
                         "body": "x" * 200},
            "story_blocks": [{"lead": "Setup", "body": "y" * 200}],
        }
        listing.update(overrides)
        with open(os.path.join(self.gdir(), "listing.json"), "w") as fh:
            json.dump(listing, fh)
        return listing

    def make_auth(self, user_id="b0b" * 8, pinned=None):
        auth = {
            "access_token": "acc-1",
            "refresh_token": "ref-1",
            "user": {"id": user_id, "username": "bob"},
            "bob_user_id": pinned if pinned is not None else user_id,
        }
        path = os.path.join(self.home, "state", publish.AUTH_FILE)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(auth, fh)
        return auth

    def make_queue(self, upto="reviewed"):
        queue.add_game(SLUG, "Tower Duel")
        chain = ["researched", "ruled", "rules_gated", "simulated", "tabled",
                 "briefed", "built", "build_gated", "reviewed", "published"]
        for state in chain:
            if state == upto:
                queue.advance(SLUG, state, "test setup")
                return
            queue.advance(SLUG, state, "test setup")

    def green(self):
        self.make_game()
        self.make_auth()

    def write_dry_projection(self):
        identity = publish._core_packet_identity(publish.build_zip(SLUG))
        record = {
            "dry_run": True,
            "publication_authority": "none",
            "core_artifact_sha256": identity["artifact_sha256"],
            "core_packet_sha256": identity["packet_sha256"],
            "core_contract": "inventor_core.artifacts/v1",
        }
        publish._write_json(os.path.join(self.gdir(), "published.json"), record)
        return record

    def draft_design(self):
        return {
            "id": "d9", "slug": SLUG, "owner_id": "b0b" * 8,
            "root_id": "d9", "current_history_id": "h9",
            "published_history_id": None, "status": "draft",
            "project_url": "https://x/p", "thumbnail_urls":
            ["https://cdn/x.png"],
        }

    def import_core_draft(self):
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"

        def fake(method, url, headers=None, data=None, timeout=None):
            if url.endswith("/auth/refresh"):
                return 200, {}, json.dumps({
                    "access_token": "acc-2", "refresh_token": "ref-2",
                    "user": {"id": "b0b" * 8},
                }).encode()
            if url.endswith("/designs/import"):
                return 201, {}, json.dumps(self.draft_design()).encode()
            raise AssertionError("unexpected setup URL %s" % url)

        publish._http = fake
        return publish.import_draft(SLUG)


class TestValidatorWalls(PublishHome):
    def assert_wall(self, needle):
        problems = publish.validate(SLUG)
        self.assertTrue(any(needle in p for p in problems),
                        "expected a wall mentioning %r, got %r"
                        % (needle, problems))

    def test_green_game_validates_clean(self):
        self.green()
        self.assertEqual(publish.validate(SLUG), [])

    def test_missing_game_dir(self):
        self.assertTrue(publish.validate(SLUG)[0].startswith("game dir"))

    def test_missing_design_source(self):
        self.green()
        os.remove(os.path.join(self.gdir(), "main.py"))
        self.assert_wall("design source")

    def test_project_json_also_satisfies_source(self):
        self.green()
        os.remove(os.path.join(self.gdir(), "main.py"))
        with open(os.path.join(self.gdir(), "project.json"), "w") as fh:
            fh.write("{}")
        self.assertEqual(publish.validate(SLUG), [])

    def test_missing_assembled_stl(self):
        self.green()
        os.remove(os.path.join(self.gdir(), "assembled.stl"))
        self.assert_wall("assembled.stl")

    def test_missing_cover(self):
        self.green()
        os.remove(os.path.join(self.gdir(), "%s_review" % SLUG,
                               "_assembled.png"))
        self.assert_wall("cover")

    def test_empty_rules(self):
        self.green()
        with open(os.path.join(self.gdir(), "RULES.md"), "w"):
            pass
        self.assert_wall("RULES.md")

    def test_description_over_cap(self):
        self.green()
        self.write_listing(description="z" * 900 + publish.DISCLOSURE_LINE)
        self.assert_wall("chars > %d cap" % publish.MAX_DESCRIPTION)

    def test_description_missing_disclosure_line(self):
        self.green()
        self.write_listing(description="A fine game, honest.")
        self.assert_wall("disclosure")

    def test_too_many_tags(self):
        self.green()
        self.write_listing(tags=[publish.AI_TAG] + ["t%d" % i
                                                    for i in range(10)])
        self.assert_wall("tags")

    def test_missing_ai_created_tag(self):
        self.green()
        self.write_listing(tags=["board-game"])
        self.assert_wall(publish.AI_TAG)

    def test_tag_over_40_chars(self):
        self.green()
        self.write_listing(tags=[publish.AI_TAG, "x" * 41])
        self.assert_wall("41 chars")

    def test_zip_entry_cap(self):
        self.green()
        publish.MAX_ZIP_ENTRIES = 1  # synthetic cap; real cap needs 4097 files
        self.assert_wall("entries")

    def test_zip_size_cap(self):
        self.green()
        publish.MAX_ZIP_BYTES = 10
        self.assert_wall("bytes")

    def test_handbuilt_legacy_zip_is_not_a_core_packet(self):
        self.green()
        pp = os.path.join(self.gdir(), "publish_payload")
        os.makedirs(pp, exist_ok=True)
        bad = os.path.join(pp, "%s.zip" % SLUG)
        with zipfile.ZipFile(bad, "w") as zf:
            zf.writestr("%s/RULES.md" % SLUG, "r")
            zf.writestr("other-game/RULES.md", "r")
        with self.assertRaises(publish.PublishError) as ctx:
            publish._core_packet_identity(bad)
        self.assertIn("core rejected", str(ctx.exception))

    def test_auth_missing(self):
        self.make_game()
        self.assert_wall("auth:")

    def test_auth_wrong_account(self):
        self.make_game()
        self.make_auth(user_id="a-human", pinned="the-real-bob")
        self.assert_wall("pinned bob id")


class TestBuildZip(PublishHome):
    def test_strips_secrets_and_process_artifacts(self):
        self.green()
        g = self.gdir()
        os.makedirs(os.path.join(g, "transcripts"))
        with open(os.path.join(g, "transcripts", "chat.json"), "w") as fh:
            fh.write("{}")
        for name in (".env", "secrets.json", "sim.jsonl", "key.pem",
                     "published.json", "listing.json", ".DS_Store"):
            with open(os.path.join(g, name), "w") as fh:
                fh.write("x")
        path = publish.build_zip(SLUG)
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
        self.assertIn("_inventor-artifact.json", names)
        joined = "\n".join(names)
        for banned in ("transcripts", ".env", "secrets", ".jsonl", ".pem",
                       "published.json", "listing.json", ".DS_Store"):
            self.assertNotIn(banned, joined)
        self.assertIn("RULES.md", names)
        self.assertIn("assembled.stl", names)
        self.assertIn("%s_review/_assembled.png" % SLUG, names)
        # remove the published.json we planted so other assertions stay valid
        os.remove(os.path.join(g, "published.json"))

    def test_deterministic_rebuild(self):
        self.green()
        p1 = publish.build_zip(SLUG)
        with open(p1, "rb") as fh:
            first = fh.read()
        p2 = publish.build_zip(SLUG)
        with open(p2, "rb") as fh:
            second = fh.read()
        self.assertEqual(first, second)

    def test_core_unavailable_fails_closed(self):
        self.green()
        os.environ["BOB_CORE_SRC"] = os.path.join(self.home, "missing-core")
        with self.assertRaises(publish.PublishError) as ctx:
            publish.build_zip(SLUG)
        self.assertIn("core", str(ctx.exception).lower())

    def test_core_secret_scan_blocks_publishable_file(self):
        self.green()
        with open(os.path.join(self.gdir(), "notes.txt"), "wb") as fh:
            fh.write(b"accidentally copied ghp_" + b"A" * 24)
        with self.assertRaises(publish.PublishError) as ctx:
            publish.build_zip(SLUG)
        self.assertIn("secret", str(ctx.exception).lower())


class TestMultipartGoldenBytes(unittest.TestCase):
    def test_exact_wire_bytes(self):
        body, ctype = publish._multipart(
            fields=[("a", "1")],
            files=[("file", "f.zip", "application/zip", b"ZZ")],
            boundary="XBOB")
        expected = (
            b"--XBOB\r\n"
            b'Content-Disposition: form-data; name="a"\r\n\r\n'
            b"1\r\n"
            b"--XBOB\r\n"
            b'Content-Disposition: form-data; name="file"; '
            b'filename="f.zip"\r\n'
            b"Content-Type: application/zip\r\n\r\n"
            b"ZZ\r\n"
            b"--XBOB--\r\n"
        )
        self.assertEqual(body, expected)
        self.assertEqual(ctype, "multipart/form-data; boundary=XBOB")

    def test_bad_boundary_refused(self):
        with self.assertRaises(ValueError):
            publish._multipart([], [], boundary="bad\nboundary")


class TestHttpRedirectSafety(unittest.TestCase):
    def test_authenticated_redirect_is_returned_and_never_followed(self):
        calls = []

        class FakeOpener:
            def open(self, request, timeout=None):
                calls.append((request.full_url,
                              request.get_header("Authorization"), timeout))
                raise publish.urllib.error.HTTPError(
                    request.full_url, 302, "moved",
                    {"Location": "https://evil.example/steal"},
                    io.BytesIO(b"redirect refused"),
                )

        built_with = []

        def fake_build_opener(*handlers):
            built_with.extend(handlers)
            return FakeOpener()

        with mock.patch.object(publish.urllib.request, "build_opener",
                               side_effect=fake_build_opener):
            status, headers, body = publish._http(
                "GET", "https://panda.example/designs/one",
                headers={"Authorization": "Bearer secret"}, timeout=7)
        self.assertEqual(status, 302)
        self.assertEqual(body, b"redirect refused")
        self.assertEqual(calls, [("https://panda.example/designs/one",
                                  "Bearer secret", 7)])
        self.assertEqual(len(built_with), 1)
        self.assertIsInstance(built_with[0], publish._NoRedirectHandler)
        self.assertIsNone(built_with[0].redirect_request(
            None, None, 302, "", {}, "https://evil.example/steal"))

    def test_http_error_body_is_bounded_and_closed(self):
        response = io.BytesIO(b"123456789")

        class FakeOpener:
            def open(self, request, timeout=None):
                raise publish.urllib.error.HTTPError(
                    request.full_url, 400, "bad", {}, response,
                )

        with mock.patch.object(publish.urllib.request, "build_opener",
                               return_value=FakeOpener()), \
                mock.patch.object(publish, "MAX_HTTP_RESPONSE_BYTES", 8):
            with self.assertRaises(publish.PublishError) as ctx:
                publish._http("GET", "https://panda.example/designs/one")
        self.assertIn("error response exceeds", str(ctx.exception))
        self.assertTrue(response.closed)

    def test_curl_fallback_bounds_body_and_keeps_bearer_off_argv(self):
        observed = {}

        def fake_run(argv, stdout=None, stderr=None, timeout=None):
            observed["argv"] = list(argv)
            observed["timeout"] = timeout
            output_path = argv[argv.index("--output") + 1]
            header_arg = argv[argv.index("--header") + 1]
            with open(header_arg[1:], encoding="utf-8") as fh:
                observed["headers"] = fh.read()
            with open(output_path, "wb") as fh:
                fh.write(b"response")
            return mock.Mock(returncode=0, stdout=b"201", stderr=b"")

        with mock.patch("subprocess.run", side_effect=fake_run):
            status, headers, body = publish._http_curl(
                "POST", "https://panda.example/designs/import",
                headers={"Authorization": "Bearer secret"}, data=b"packet",
                timeout=7,
            )
        self.assertEqual((status, headers, body), (201, {}, b"response"))
        self.assertIn("Authorization: Bearer secret", observed["headers"])
        self.assertNotIn("Bearer secret", " ".join(observed["argv"]))
        self.assertIn("--max-filesize", observed["argv"])
        self.assertEqual(observed["timeout"], 37)

    def test_curl_fallback_rejects_oversized_body(self):
        def fake_run(argv, stdout=None, stderr=None, timeout=None):
            output_path = argv[argv.index("--output") + 1]
            with open(output_path, "wb") as fh:
                fh.write(b"123456789")
            return mock.Mock(returncode=0, stdout=b"200", stderr=b"")

        with mock.patch("subprocess.run", side_effect=fake_run), \
                mock.patch.object(publish, "MAX_HTTP_RESPONSE_BYTES", 8):
            with self.assertRaises(publish.PublishError) as ctx:
                publish._http_curl("GET", "https://panda.example/designs/one")
        self.assertIn("response exceeds", str(ctx.exception))


class TestCredentialOriginPinning(PublishHome):
    def test_refresh_refuses_unpinned_origin_before_http(self):
        self.green()
        calls = []
        publish._http = lambda *args, **kwargs: calls.append((args, kwargs))
        for api_base in (
            "http://evil.example/api/v1",
            "https://evil.example/api/v1",
        ):
            os.environ["BOB_PANDA_API"] = api_base
            with self.assertRaises(publish.PublishError) as ctx:
                publish.refresh_auth()
            self.assertIn("allowed HTTPS endpoint", str(ctx.exception))
        self.assertEqual(calls, [])

    def test_bearer_call_refuses_unpinned_origin_before_http(self):
        self.green()
        os.environ["BOB_PANDA_API"] = "https://evil.example/api/v1"
        calls = []
        publish._http = lambda *args, **kwargs: calls.append((args, kwargs))
        with self.assertRaises(publish.PublishError) as ctx:
            publish._authed_call(
                "POST", "https://evil.example/api/v1/designs/x", {}
            )
        self.assertIn("allowed HTTPS endpoint", str(ctx.exception))
        self.assertEqual(calls, [])

    def test_explicitly_pinned_staging_origin_can_refresh(self):
        self.green()
        os.environ["BOB_PANDA_API"] = "https://staging.example/api/v1"
        os.environ["BOB_PANDA_ALLOWED_ORIGINS"] = "https://staging.example"
        calls = []

        def fake(method, url, headers=None, data=None, timeout=None):
            calls.append((method, url, json.loads(data.decode("utf-8"))))
            return 200, {}, json.dumps({
                "access_token": "fresh",
                "refresh_token": "rotated",
                "user": {"id": "b0b" * 8},
            }).encode("utf-8")

        publish._http = fake
        publish.refresh_auth()
        self.assertEqual(calls, [(
            "POST",
            "https://staging.example/api/v1/auth/refresh",
            {"refresh_token": "ref-1"},
        )])


class TestDryRun(PublishHome):
    def test_dry_run_writes_manifest_and_never_calls_http(self):
        # BOB_PUBLISH_DRY_RUN unset = default ON; _http is the failing stub.
        self.green()
        self.make_queue("reviewed")
        result = publish.import_draft(SLUG)
        self.assertTrue(result["dry_run"])
        manifest_path = os.path.join(self.gdir(), "publish_payload",
                                     "manifest.json")
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path) as fh:
            manifest = json.load(fh)
        self.assertEqual(manifest["fields"]["status"], "draft")
        self.assertIn(publish.DISCLOSURE_LINE,
                      manifest["fields"]["description"])
        game = queue.load()["games"][SLUG]
        self.assertEqual(game["state"], "published")
        self.assertEqual(game["log"][-1]["note"], "dry-run")

    def test_dry_run_tolerates_missing_auth_as_warning(self):
        self.make_game()  # no auth file at all
        self.make_queue("reviewed")
        result = publish.import_draft(SLUG)
        self.assertTrue(result["dry_run"])
        self.assertTrue(any("auth" in w for w in result["auth_warnings"]))

    def test_dry_run_still_blocks_on_content_walls(self):
        self.green()
        os.remove(os.path.join(self.gdir(), "RULES.md"))
        with self.assertRaises(publish.PublishError):
            publish.import_draft(SLUG)


class TestIdempotency(PublishHome):
    def test_existing_core_bound_published_json_is_hard_noop(self):
        self.green()
        with open(os.path.join(self.gdir(), "published.json"), "w") as fh:
            json.dump({
                "slug": SLUG,
                "design": {"id": "d1"},
                "core_intent_id": "intent-1",
                "core_product_id": "product-1",
                "core_artifact_sha256": "a" * 64,
                "zip_sha256": "b" * 64,
            }, fh)
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        result = publish.import_draft(SLUG)  # _http would raise if touched
        self.assertTrue(result["noop"])
        self.assertEqual(result["published"]["design"]["id"], "d1")

    def test_current_dry_run_keeps_existing_rehearsal_as_noop(self):
        self.green()
        self.write_dry_projection()
        result = publish.import_draft(SLUG)
        self.assertTrue(result["noop"])
        self.assertEqual(result["published"]["publication_authority"], "none")

    def test_legacy_remote_projection_is_stranded_not_adopted(self):
        self.green()
        with open(os.path.join(self.gdir(), "published.json"), "w") as fh:
            json.dump({
                "dry_run": True,
                "publication_authority": "none",
                "design": {
                    "id": "already-remote",
                    "author": {"id": "dee-id", "display_name": "Dee"},
                },
            }, fh)
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        with self.assertRaises(publish.PublishError) as ctx:
            publish.import_draft(SLUG)
        message = str(ctx.exception)
        self.assertIn("legacy pre-core", message)
        self.assertIn("Dee (dee-id)", message)
        self.assertIn("cannot adopt", message)
        self.assertIn("distinct Bob marketplace principal", message)
        self.assertIn("new slug", message)
        self.assertIn("Do not delete", message)


class TestLiveImport(PublishHome):
    def http_mock(self, responses):
        calls = []

        def fake(method, url, headers=None, data=None, timeout=None):
            calls.append({"method": method, "url": url,
                          "headers": headers or {}, "data": data})
            for suffix, resp in responses:
                if url.endswith(suffix):
                    return resp
            raise AssertionError("unexpected URL %s" % url)
        publish._http = fake
        return calls

    def test_import_persists_ledger_and_refreshes_auth_0600(self):
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        self.green()
        self.make_queue("reviewed")
        design = self.draft_design()
        calls = self.http_mock([
            ("/auth/refresh", (200, {}, json.dumps(
                {"access_token": "acc-2", "refresh_token": "ref-2",
                 "user": {"id": "b0b" * 8}}).encode())),
            ("/designs/import", (201, {}, json.dumps(design).encode())),
        ])
        record = publish.import_draft(SLUG)
        self.assertEqual(record["design"]["id"], "d9")
        self.assertEqual(record["status"], "draft")
        self.assertTrue(record["core_intent_id"])
        self.assertEqual(record["draft_receipt"]["artifact_sha256"],
                         record["core_artifact_sha256"])
        self.assertTrue(os.path.exists(os.path.join(
            self.home, "state", publish.CORE_STATE_FILE)))
        # rotated pair persisted, 0600
        auth_path = os.path.join(self.home, "state", publish.AUTH_FILE)
        with open(auth_path) as fh:
            auth = json.load(fh)
        self.assertEqual(auth["access_token"], "acc-2")
        self.assertEqual(auth["refresh_token"], "ref-2")
        mode = stat.S_IMODE(os.stat(auth_path).st_mode)
        self.assertEqual(mode, 0o600)
        # the import call carried the fresh bearer + multipart body
        imp = [c for c in calls if c["url"].endswith("/designs/import")][0]
        self.assertEqual(imp["headers"]["Authorization"], "Bearer acc-2")
        self.assertIn(b'name="status"\r\n\r\ndraft', imp["data"])
        # ledger row + queue advance + idempotency ledger on disk
        self.assertTrue(os.path.exists(
            os.path.join(self.gdir(), "published.json")))
        rows = ledger.rows(slug=SLUG)
        self.assertEqual(rows[-1]["kind"], "publish")
        self.assertEqual(queue.load()["games"][SLUG]["state"], "published")

    def test_real_import_promotes_non_authoritative_dry_projection(self):
        self.green()
        self.make_queue("reviewed")
        dry_record = self.write_dry_projection()
        queue.advance(SLUG, "published", "dry-run rehearsal")
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        calls = self.http_mock([
            ("/auth/refresh", (200, {}, json.dumps({
                "access_token": "fresh", "refresh_token": "rotated",
                "user": {"id": "b0b" * 8},
            }).encode())),
            ("/designs/import", (201, {},
                                 json.dumps(self.draft_design()).encode())),
        ])
        record = publish.import_draft(SLUG)
        self.assertNotIn("noop", record)
        self.assertNotEqual(record, dry_record)
        self.assertTrue(record["core_intent_id"])
        self.assertEqual(record["status"], "draft")
        self.assertNotIn("publication_authority", record)
        self.assertEqual(
            [call["method"] for call in calls
             if call["url"].endswith("/designs/import")],
            ["POST"],
        )
        self.assertEqual(queue.load()["games"][SLUG]["state"], "published")

    def test_ambiguous_promotion_still_posts_only_once(self):
        self.green()
        self.write_dry_projection()
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        imports = []

        def fake(method, url, headers=None, data=None, timeout=None):
            if url.endswith("/auth/refresh"):
                return 200, {}, json.dumps({
                    "access_token": "fresh", "refresh_token": "rotated",
                    "user": {"id": "b0b" * 8},
                }).encode()
            if url.endswith("/designs/import"):
                imports.append(url)
                return 503, {}, b'{"error":"upstream unavailable"}'
            raise AssertionError("unexpected URL %s" % url)

        publish._http = fake
        for _ in range(2):
            with self.assertRaises(publish.PublishError):
                publish.import_draft(SLUG)
        self.assertEqual(len(imports), 1)

    def test_import_rebuilds_a_stale_packet_at_the_effect_boundary(self):
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        self.green()
        stale_path = publish.build_zip(SLUG)
        stale = publish._core_packet_identity(stale_path)
        with open(os.path.join(self.gdir(), "RULES.md"), "a") as fh:
            fh.write("\nA newly clarified turn rule.\n")
        self.http_mock([
            ("/auth/refresh", (200, {}, json.dumps({
                "access_token": "fresh", "refresh_token": "rotated",
                "user": {"id": "b0b" * 8},
            }).encode())),
            ("/designs/import", (201, {},
                                 json.dumps(self.draft_design()).encode())),
        ])
        record = publish.import_draft(SLUG)
        self.assertNotEqual(record["core_artifact_sha256"],
                            stale["artifact_sha256"])

    def test_non_201_raises_actionable(self):
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        self.green()
        self.http_mock([
            ("/auth/refresh", (200, {}, json.dumps(
                {"access_token": "a", "refresh_token": "r",
                 "user": {"id": "b0b" * 8}}).encode())),
            ("/designs/import", (400, {}, b'{"error":"no design found"}')),
        ])
        with self.assertRaises(publish.PublishError) as ctx:
            publish.import_draft(SLUG)
        self.assertIn("no design found", str(ctx.exception))
        self.assertFalse(os.path.exists(
            os.path.join(self.gdir(), "published.json")))

    def test_ambiguous_5xx_is_durable_and_never_posts_again(self):
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        self.green()
        imports = []

        def fake(method, url, headers=None, data=None, timeout=None):
            if url.endswith("/auth/refresh"):
                return 200, {}, json.dumps({
                    "access_token": "fresh", "refresh_token": "rotated",
                    "user": {"id": "b0b" * 8},
                }).encode()
            if url.endswith("/designs/import"):
                imports.append(url)
                return 503, {}, b'{"error":"upstream unavailable"}'
            raise AssertionError("unexpected URL %s" % url)

        publish._http = fake
        for _ in range(2):
            with self.assertRaises(publish.PublishError) as ctx:
                publish.import_draft(SLUG)
            self.assertIn("blocks every retry", str(ctx.exception))
        self.assertEqual(len(imports), 1)
        with open(os.path.join(self.gdir(), "RULES.md"), "a") as fh:
            fh.write("\nchanged after the ambiguous import\n")
        with self.assertRaises(publish.PublishError) as ctx:
            publish.import_draft(SLUG)
        self.assertIn("corrected bytes require a new slug", str(ctx.exception))
        self.assertEqual(len(imports), 1)
        self.assertTrue(os.path.exists(os.path.join(
            self.home, "state", publish.CORE_STATE_FILE)))
        self.assertFalse(os.path.exists(
            os.path.join(self.gdir(), "published.json")))


class TestFlip(PublishHome):
    def setUpFlip(self, state="published"):
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        self.green()
        self.make_queue(state)
        self.import_core_draft()

    def public_design(self, price_cents=5500):
        return {
            "id": "d9", "slug": SLUG, "owner_id": "b0b" * 8,
            "root_id": "d9", "current_history_id": "h9",
            "published_history_id": "h9", "status": "public",
            "project_url": "https://x/p",
            "listing": {"active": True, "price_cents": price_cents,
                        "currency": "USD", "sku": "TOWER-001"},
        }

    def successful_flip_http(self, seen=None):
        requested_price = [5500]

        def fake(method, url, headers=None, data=None, timeout=None):
            if seen is not None:
                seen.append((method, url, data))
            if method == "GET":
                return 200, {}, json.dumps(
                    self.public_design(requested_price[0])).encode()
            if url.endswith("/publish"):
                requested_price[0] = json.loads(
                    data.decode())["listing"]["price_cents"]
            return 200, {}, b"{}"
        return fake

    def test_refuses_outside_price_corner(self):
        self.setUpFlip()
        for price in (3999, 8001, 99, 2000000):
            with self.assertRaises(publish.PublishError):
                publish.flip_public(SLUG, price)

    def test_override_allows_outside_corner_but_not_api_bounds(self):
        self.setUpFlip()
        os.environ["BOB_PRICE_OVERRIDE"] = "1"
        with self.assertRaises(publish.PublishError):
            publish.flip_public(SLUG, 99)  # API bound holds even overridden
        publish._http = self.successful_flip_http()
        record = publish.flip_public(SLUG, 9000)
        self.assertEqual(record["price_cents"], 9000)

    def test_refuses_without_published_json(self):
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        self.green()
        with self.assertRaises(publish.PublishError):
            publish.flip_public(SLUG, 5000)

    def test_refuses_in_dry_run_mode(self):
        self.setUpFlip()
        os.environ["BOB_PUBLISH_DRY_RUN"] = "1"
        with self.assertRaises(publish.PublishError):
            publish.flip_public(SLUG, 5000)

    def test_refuses_dirty_validator(self):
        self.setUpFlip()
        os.remove(os.path.join(self.gdir(), "RULES.md"))
        with self.assertRaises(publish.PublishError) as ctx:
            publish.flip_public(SLUG, 5000)
        self.assertIn("validator dirty", str(ctx.exception))

    def test_refuses_to_flip_if_product_bytes_changed_after_import(self):
        self.setUpFlip()
        with open(os.path.join(self.gdir(), "RULES.md"), "a") as fh:
            fh.write("\nchanged after import\n")
        publish._http = _fail_http
        with self.assertRaises(publish.PublishError) as ctx:
            publish.flip_public(SLUG, 5500)
        self.assertIn("do not match the exact artifact", str(ctx.exception))

    def test_projection_hash_edit_cannot_bypass_artifact_drift(self):
        self.setUpFlip()
        with open(os.path.join(self.gdir(), "RULES.md"), "a") as fh:
            fh.write("\nchanged after import\n")
        new_identity = publish._core_packet_identity(publish.build_zip(SLUG))
        pub_path = os.path.join(self.gdir(), "published.json")
        with open(pub_path) as fh:
            record = json.load(fh)
        record["core_artifact_sha256"] = new_identity["artifact_sha256"]
        with open(pub_path, "w") as fh:
            json.dump(record, fh)
        publish._http = _fail_http
        with self.assertRaises(publish.PublishError) as ctx:
            publish.flip_public(SLUG, 5500)
        self.assertIn("core product", str(ctx.exception))

    def test_projection_cannot_select_another_core_intent(self):
        self.setUpFlip()
        pub_path = os.path.join(self.gdir(), "published.json")
        with open(pub_path) as fh:
            record = json.load(fh)
        record["core_intent_id"] = "forged-other-product-intent"
        with open(pub_path, "w") as fh:
            json.dump(record, fh)
        publish._http = _fail_http
        with self.assertRaises(publish.PublishError) as ctx:
            publish.flip_public(SLUG, 5500)
        self.assertIn("mutable projection", str(ctx.exception))

    def test_happy_flip_updates_record_ledger_queue(self):
        self.setUpFlip()
        seen = []

        publish._http = self.successful_flip_http(seen)
        record = publish.flip_public(SLUG, 5500)
        self.assertEqual(record["status"], "public")
        self.assertEqual(record["price_cents"], 5500)
        self.assertIn("publication_receipt", record)
        self.assertEqual(record["publication_receipt"]["current_history_id"],
                         "h9")
        method, url, data = [call for call in seen if call[0] == "POST"][-1]
        self.assertEqual(method, "POST")
        self.assertTrue(url.endswith("/designs/%s/publish" % SLUG))
        self.assertEqual(json.loads(data.decode())["listing"]["price_cents"],
                         5500)
        self.assertEqual(seen[-1][0], "GET")
        self.assertEqual(queue.load()["games"][SLUG]["state"], "live")
        self.assertEqual(ledger.rows(slug=SLUG)[-1]["stage"], "flip_public")

    def test_ambiguous_readback_does_not_mark_live_or_repost(self):
        self.setUpFlip()
        posts = []

        def fake(method, url, headers=None, data=None, timeout=None):
            if url.endswith("/auth/refresh"):
                return 200, {}, json.dumps({
                    "access_token": "fresh", "refresh_token": "rotated",
                    "user": {"id": "b0b" * 8},
                }).encode()
            if method == "POST":
                posts.append(url)
                return 200, {}, b"{}"
            return 503, {}, b'{"error":"temporarily unavailable"}'

        publish._http = fake
        with self.assertRaises(publish.PublishError) as ctx:
            publish.flip_public(SLUG, 5500)
        self.assertIn("do not POST publish again", str(ctx.exception))
        self.assertEqual(queue.load()["games"][SLUG]["state"], "published")
        with open(os.path.join(self.gdir(), "published.json")) as fh:
            record = json.load(fh)
        self.assertEqual(record["status"], "draft")
        self.assertEqual(record["flip_intent"]["state"], "unknown")
        with self.assertRaises(publish.PublishError):
            publish.flip_public(SLUG, 5500)
        self.assertEqual(len(posts), 1)

    def test_reconcile_public_uses_get_only(self):
        self.setUpFlip()
        def ambiguous(method, url, headers=None, data=None, timeout=None):
            if method == "POST":
                return 200, {}, b"{}"
            return 503, {}, b'{"error":"temporarily unavailable"}'
        publish._http = ambiguous
        with self.assertRaises(publish.PublishError):
            publish.flip_public(SLUG, 5500)
        seen = []
        publish._http = self.successful_flip_http(seen)
        result = publish.reconcile_public(SLUG)
        self.assertEqual(result["status"], "public")
        effect_calls = [call for call in seen
                        if not call[1].endswith("/auth/refresh")]
        self.assertEqual([call[0] for call in effect_calls], ["GET"])
        self.assertEqual(queue.load()["games"][SLUG]["state"], "live")

    def test_reconcile_refuses_changed_current_artifact_even_if_projection_edits(self):
        self.setUpFlip()

        def ambiguous(method, url, headers=None, data=None, timeout=None):
            if method == "POST":
                return 200, {}, b"{}"
            return 503, {}, b'{"error":"temporarily unavailable"}'

        publish._http = ambiguous
        with self.assertRaises(publish.PublishError):
            publish.flip_public(SLUG, 5500)
        with open(os.path.join(self.gdir(), "RULES.md"), "a") as fh:
            fh.write("\nchanged after ambiguous flip\n")
        new_identity = publish._core_packet_identity(publish.build_zip(SLUG))
        pub_path = os.path.join(self.gdir(), "published.json")
        with open(pub_path) as fh:
            record = json.load(fh)
        record["core_artifact_sha256"] = new_identity["artifact_sha256"]
        with open(pub_path, "w") as fh:
            json.dump(record, fh)
        publish._http = _fail_http
        with self.assertRaises(publish.PublishError) as ctx:
            publish.reconcile_public(SLUG)
        self.assertIn("core product", str(ctx.exception))


class TestCurateAndUnpublish(PublishHome):
    def setUpDraft(self):
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        self.green()
        with open(os.path.join(self.gdir(), "published.json"), "w") as fh:
            json.dump({"slug": SLUG, "status": "draft",
                       "design": {"id": "d9", "slug": SLUG,
                                  "thumbnail_urls": ["https://cdn/c.png"]}},
                      fh)

    def test_curate_content_walls(self):
        self.setUpDraft()
        self.write_listing(story_blocks=[{"lead": "", "body": "short"}])
        with self.assertRaises(publish.PublishError) as ctx:
            publish.curate(SLUG)
        self.assertIn("story_blocks[0]", str(ctx.exception))

    def test_curate_rejects_markup(self):
        self.setUpDraft()
        self.write_listing(story_blocks=[
            {"lead": "Setup", "body": "y" * 190 + "<b>bold</b>"}])
        with self.assertRaises(publish.PublishError) as ctx:
            publish.curate(SLUG)
        self.assertIn("'<'", str(ctx.exception))

    def test_curate_happy_path_uses_cover_url(self):
        self.setUpDraft()
        seen = []

        def fake(method, url, headers=None, data=None, timeout=None):
            seen.append((method, url, json.loads(data.decode())))
            return 200, {}, b"{}"
        publish._http = fake
        record = publish.curate(SLUG)
        self.assertIn("curated_at", record)
        patch = [c for c in seen if c[0] == "PATCH"][0]
        self.assertEqual(patch[2]["image"], "https://cdn/c.png")
        put = [c for c in seen if c[0] == "PUT"][0]
        self.assertTrue(put[1].endswith("/story-blocks"))

    def test_curate_requires_import_first(self):
        os.environ["BOB_PUBLISH_DRY_RUN"] = "0"
        self.green()
        with self.assertRaises(publish.PublishError):
            publish.curate(SLUG)

    def test_unpublish_flips_record_back_to_draft(self):
        self.setUpDraft()
        publish._http = lambda m, u, headers=None, data=None, timeout=None: \
            (200, {}, b"{}")
        record = publish.unpublish(SLUG)
        self.assertEqual(record["status"], "draft")
        self.assertIn("unpublished_at", record)


if __name__ == "__main__":
    unittest.main()
