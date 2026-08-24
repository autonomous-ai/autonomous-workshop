import hashlib
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from email.parser import BytesParser
from email.policy import default as email_policy
from pathlib import Path
from unittest import mock

from inventor_workshop.artifacts import build_pack
from inventor_workshop.errors import ContractError, StateConflict
from inventor_workshop.shop import HttpResponse
from inventor_workshop.store import InventorStore
from tools import publish_showcase_products as publisher


def _multipart(headers, body):
    content_type = headers["Content-Type"]
    message = BytesParser(policy=email_policy).parsebytes(
        ("Content-Type: %s\r\nMIME-Version: 1.0\r\n\r\n" % content_type).encode()
        + body
    )
    parts = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        parts.setdefault(name, []).append(
            {
                "filename": part.get_filename(),
                "content_type": part.get_content_type(),
                "content": part.get_payload(decode=True),
            }
        )
    return parts


def _sealed_bytes(bundle):
    result = {}
    for directory in ("artifact", "evidence", "instructions"):
        root = bundle / directory
        for path in sorted(root.rglob("*")):
            if path.is_file():
                result[path.relative_to(bundle).as_posix()] = path.read_bytes()
    return result


class ShowcaseShopTransport:
    def __init__(self, slug, owner_id, *, first_get_status=404):
        self.slug = slug
        self.owner_id = owner_id
        self.first_get_status = first_get_status
        self.calls = []
        self.exists = False
        self.public = False
        self.title = None
        self.description = None
        self.attachments = []
        self.use_case = None
        self.story_blocks = []
        self.upload_index = 0
        self.roles = ("hero", "play", "detail", "parts", "box")
        self.urls = {
            role: "https://cdn.example/showcase/%s.png" % role
            for role in self.roles
        }
        self.imported_pack = None

    def design(self):
        status = "public" if self.public else "draft"
        value = {
            "id": "design-showcase-1",
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "owner_id": self.owner_id,
            "root_id": "design-showcase-1",
            "current_history_id": "history-showcase-1",
            "published_history_id": (
                "history-showcase-1" if self.public else None
            ),
            "status": status,
            "project_url": "https://cdn.autonomous.ai/projects/history-showcase-1/",
            "use_case": self.use_case,
            "story_blocks": self.story_blocks,
        }
        if self.public:
            value["attachments"] = list(self.attachments)
            value["listing"] = {
                "active": True,
                "price_cents": 3500,
                "currency": "usd",
                "sku": "SHOWCASE-001",
            }
        return value

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, body, timeout))
        if headers.get("Authorization") != "Bearer test-token":
            raise AssertionError("publisher omitted authenticated Shop readback")
        if method == "GET" and url.endswith("/designs/%s" % self.slug):
            if not self.exists:
                if self.first_get_status == 404:
                    return HttpResponse(404, {}, b"{}")
                return HttpResponse(
                    self.first_get_status,
                    {},
                    json.dumps({"slug": self.slug}).encode(),
                )
            return HttpResponse(200, {}, json.dumps(self.design()).encode())
        if method == "POST" and url.endswith("/designs/import"):
            parts = _multipart(headers, body)
            self.imported_pack = parts["file"][0]["content"]
            fields = {
                name: values[0]["content"].decode("utf-8")
                for name, values in parts.items()
                if name != "file"
            }
            self.title = fields["title"]
            self.description = fields["description"]
            self.exists = True
            return HttpResponse(201, {}, json.dumps(self.design()).encode())
        if method == "POST" and url.endswith("/uploads"):
            part = _multipart(headers, body)["file"][0]
            content = part["content"]
            role = self.roles[self.upload_index]
            self.upload_index += 1
            return HttpResponse(
                201,
                {},
                json.dumps(
                    {
                        "url": self.urls[role],
                        "ref": "gs://showcase/%s" % part["filename"],
                        "filename": part["filename"],
                        "content_type": part["content_type"],
                        "size": len(content),
                        "sha256": hashlib.sha256(content).hexdigest(),
                    }
                ).encode(),
            )
        if method == "PATCH" and url.endswith("/use-case"):
            self.use_case = json.loads(body.decode("utf-8"))
            return HttpResponse(200, {}, json.dumps(self.design()).encode())
        if method == "PUT" and url.endswith("/story-blocks"):
            self.story_blocks = json.loads(body.decode("utf-8"))["story_blocks"]
            return HttpResponse(200, {}, json.dumps(self.design()).encode())
        if method == "POST" and url.endswith("/publish"):
            request = json.loads(body.decode("utf-8")) if body else {}
            self.attachments = request["attachments"]
            self.public = True
            return HttpResponse(200, {}, json.dumps(self.design()).encode())
        raise AssertionError("unexpected Shop request %s %s" % (method, url))


class PublishShowcaseProductsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "repo"
        self.bundle = (
            self.repo
            / "inventors"
            / "alice"
            / "toys"
            / "five-job-checkers"
        )
        source_inventor = publisher.REPO_ROOT / "inventors" / "alice"
        self.bundle.parent.mkdir(parents=True)
        shutil.copytree(
            source_inventor / "toys" / "five-job-checkers", self.bundle
        )
        shutil.copy2(source_inventor / "TASTE.md", self.repo / "inventors" / "alice")
        shutil.copy2(source_inventor / "profile.py", self.repo / "inventors" / "alice")
        self.state_root = self.root / "state"
        self.spec = publisher.showcase.SPECS[0]

    def test_exact_checked_in_bundle_publishes_once_and_durably_replays(self):
        before = _sealed_bytes(self.bundle)
        expected_pack_path = self.root / "expected.zip"
        build_pack(self.bundle / "artifact", expected_pack_path)
        expected_pack = expected_pack_path.read_bytes()
        transport = ShowcaseShopTransport(self.spec.slug, "owner-1")

        with mock.patch.object(
            publisher.showcase,
            "showcase_make",
            side_effect=AssertionError("publisher must not rerun Make"),
        ), mock.patch.object(
            publisher.showcase,
            "showcase_playtest",
            side_effect=AssertionError("publisher must not rerun Playtest"),
        ), mock.patch.object(
            publisher.showcase,
            "_run_counterorbit_simulator",
            side_effect=AssertionError("publisher must not rerun the simulator"),
        ), mock.patch.object(
            publisher.showcase,
            "_verify_bundle",
            side_effect=AssertionError("publisher must consume seals, not rebuild evidence"),
        ):
            first = publisher.publish_one(
                self.spec,
                token="test-token",
                owner_id="owner-1",
                repo_root=self.repo,
                state_root=self.state_root,
                transport=transport,
            )

        self.assertEqual(first["status"], "published")
        self.assertEqual(transport.imported_pack, expected_pack)
        self.assertTrue(transport.description.endswith("By Alice."))
        self.assertEqual(_sealed_bytes(self.bundle), before)
        with zipfile.ZipFile(io.BytesIO(transport.imported_pack)) as archive:
            self.assertIn("product.json", archive.namelist())
            self.assertEqual(
                json.loads(archive.read("product.json"))["inventor"]["name"],
                "Alice",
            )
        methods_after_first = [call[0] for call in transport.calls]
        self.assertEqual(
            methods_after_first,
            ["GET", "POST", "POST", "POST", "POST", "POST", "POST", "PATCH", "PUT", "POST", "GET"],
        )
        count_after_first = len(transport.calls)

        replay = publisher.publish_one(
            self.spec,
            token="test-token",
            owner_id="owner-1",
            repo_root=self.repo,
            state_root=self.state_root,
            transport=transport,
        )
        self.assertEqual(replay["status"], "replayed")
        self.assertEqual(len(transport.calls), count_after_first)
        self.assertEqual(_sealed_bytes(self.bundle), before)

        verified = publisher.publish_one(
            self.spec,
            token="test-token",
            owner_id="owner-1",
            repo_root=self.repo,
            state_root=self.state_root,
            transport=transport,
            verify_live=True,
        )
        self.assertEqual(len(transport.calls), count_after_first + 1)
        self.assertEqual(
            verified["live_verification"]["status"], "verified-live"
        )
        run = json.loads((self.bundle / "workshop-run.json").read_text())
        customer_page = (
            "https://www.autonomous.ai/factory/product/five-job-checkers"
        )
        self.assertEqual(run["run"]["job"], "deliver")
        self.assertEqual(run["run"]["page_url"], customer_page)
        self.assertEqual(
            run["site_receipt"]["details"]["page_url"], customer_page
        )
        self.assertTrue(
            run["site_receipt"]["project_url"].startswith(
                "https://cdn.autonomous.ai/"
            )
        )
        self.assertNotEqual(
            run["run"]["page_url"], run["site_receipt"]["project_url"]
        )
        database = (
            self.state_root
            / "five-job-checkers"
            / "workshop.sqlite3"
        )
        self.assertTrue(database.is_file())
        store = InventorStore(database)
        self.assertEqual(len(store.events(self.spec.slug)), 1)
        self.assertEqual(store.latest_publish_intent(self.spec.slug)["state"], "live")
        self.assertEqual(
            len(store.shop_effects_for_publish_intent(
                store.latest_publish_intent(self.spec.slug)["id"]
            )),
            7,
        )

    def test_all_five_checked_in_bundles_reconstruct_without_running_jobs(self):
        with mock.patch.object(
            publisher.showcase,
            "showcase_make",
            side_effect=AssertionError("publisher must not rerun Make"),
        ), mock.patch.object(
            publisher.showcase,
            "showcase_playtest",
            side_effect=AssertionError("publisher must not rerun Playtest"),
        ), mock.patch.object(
            publisher.showcase,
            "_run_counterorbit_simulator",
            side_effect=AssertionError("publisher must not rerun the simulator"),
        ):
            sealed = [
                publisher._load_sealed_showcase(spec)
                for spec in publisher.showcase.SPECS
            ]

        self.assertEqual(
            [item.spec.inventor_id for item in sealed],
            ["alice", "bob", "eve", "ivy", "leo"],
        )

    def test_changed_checked_in_bytes_fail_before_state_or_network(self):
        instructions = self.bundle / "instructions" / "INSTRUCTIONS.md"
        instructions.write_text(
            instructions.read_text(encoding="utf-8") + "changed\n",
            encoding="utf-8",
        )
        transport = ShowcaseShopTransport(self.spec.slug, "owner-1")
        with self.assertRaises(ContractError):
            publisher.publish_one(
                self.spec,
                token="test-token",
                owner_id="owner-1",
                repo_root=self.repo,
                state_root=self.state_root,
                transport=transport,
            )
        self.assertEqual(transport.calls, [])
        self.assertFalse(self.state_root.exists())

    def test_first_import_stops_when_canonical_slug_already_exists(self):
        transport = ShowcaseShopTransport(
            self.spec.slug, "owner-1", first_get_status=200
        )
        with self.assertRaisesRegex(StateConflict, "already exists"):
            publisher.publish_one(
                self.spec,
                token="test-token",
                owner_id="owner-1",
                repo_root=self.repo,
                state_root=self.state_root,
                transport=transport,
            )
        self.assertEqual([call[0] for call in transport.calls], ["GET"])
        store = InventorStore(
            self.state_root / self.spec.slug / "workshop.sqlite3"
        )
        self.assertIsNone(store.latest_publish_intent(self.spec.slug))

    def test_cli_credentials_require_both_values(self):
        with self.assertRaises(SystemExit):
            publisher._credentials({})
        with self.assertRaises(SystemExit):
            publisher._credentials({"WORKSHOP_SHOP_TOKEN": "token"})
        self.assertEqual(
            publisher._credentials(
                {
                    "WORKSHOP_SHOP_TOKEN": "token",
                    "WORKSHOP_SHOP_OWNER_ID": "owner",
                }
            ),
            ("token", "owner"),
        )


if __name__ == "__main__":
    unittest.main()
