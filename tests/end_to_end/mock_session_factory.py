"""Loopback Factory protocol used only by live-Codex acceptance."""

from __future__ import annotations

from email.parser import BytesParser
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from typing import Any, Mapping

from workshop.integrations.factory import (
    FACTORY_PROJECT_PDF_MANUAL_FILENAME,
    FACTORY_TOY_CATEGORY_SLUG,
    FactoryProjectFileResponse,
    HttpResponse,
    MAX_RESPONSE_BYTES,
)

from tests.end_to_end.mock_session_evidence import (
    FIXTURE_SECRETS,
    canonical_json,
    sha256_bytes,
)


def _multipart_values(content_type: str, body: bytes) -> Mapping[str, list[bytes]]:
    message = BytesParser(policy=email_policy).parsebytes(
        ("Content-Type: %s\r\nMIME-Version: 1.0\r\n\r\n" % content_type).encode()
        + body
    )
    result: dict[str, list[bytes]] = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if isinstance(name, str):
            result.setdefault(name, []).append(part.get_payload(decode=True))
    return result


class _FactoryState:
    def __init__(self, product_id: str) -> None:
        self.lock = threading.Lock()
        self.product_id = product_id
        self.logical_calls: list[tuple[str, str]] = []
        self.loopback_calls: list[tuple[str, str]] = []
        self.imports = 0
        self.promotions = 0
        self.public = False
        self.username = "mock-session"
        self.owner_id = "owner-mock-session"
        self.title = "Mock Session Acceptance Product"
        self.description = "A minimal context-and-integration acceptance artifact."
        self.tags = ["toy", "acceptance"]
        self.category: str | None = None
        self.manual = b""
        self.archive_hashes: dict[str, str] = {}
        self.import_has_cad = False
        self.import_has_manual = False
        self.override_public_manual: bytes | None = None

    def design(self) -> Mapping[str, Any]:
        return {
            "id": "design-mock-session",
            "slug": self.product_id,
            "owner_id": self.owner_id,
            "root_id": "design-mock-session",
            "current_history_id": "history-mock-session-1",
            "published_history_id": (
                "history-mock-session-1" if self.public else None
            ),
            "status": "public" if self.public else "draft",
            "project_url": (
                "https://cdn.autonomous.ai/projects/history-mock-session-1/"
            ),
            "origin": "import",
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
            "category": {"slug": self.category} if self.category else None,
            "author": {"id": self.owner_id},
            "use_case": None,
            "story_blocks": [],
            "thumbnail_urls": ["https://cdn.autonomous.ai/mock-session.webp"],
            "listing": (
                {
                    "active": True,
                    "price_cents": 100,
                    "currency": "usd",
                    "sku": "MOCK-SESSION-001",
                }
                if self.public
                else None
            ),
        }


class _Handler(BaseHTTPRequestHandler):
    server_version = "WorkshopMockFactory/2"

    @property
    def state(self) -> _FactoryState:
        return self.server.state  # type: ignore[attr-defined]

    def log_message(self, unused_format: str, *unused_arguments: object) -> None:
        del unused_format, unused_arguments

    def _body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > 64 * 1024 * 1024:
            raise ValueError("mock Factory request exceeds its bound")
        return self.rfile.read(length)

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, value: object) -> None:
        self._send(status, canonical_json(value), "application/json")

    def _authenticated(self) -> bool:
        return self.headers.get("Authorization") == (
            "Bearer " + FIXTURE_SECRETS[1]
        )

    def _dispatch(self) -> None:
        path = urllib.parse.urlsplit(self.path).path
        with self.state.lock:
            self.state.loopback_calls.append((self.command, path))
        body = self._body()
        if path == "/api/v1/auth/agent/login" and self.command == "POST":
            try:
                credentials = json.loads(body.decode("utf-8"))
            except (UnicodeError, ValueError):
                self._json(400, {"error": "malformed login"})
                return
            if (
                not isinstance(credentials, Mapping)
                or credentials.get("password") != FIXTURE_SECRETS[0]
                or not isinstance(credentials.get("username"), str)
            ):
                self._json(401, {"error": "rejected"})
                return
            with self.state.lock:
                self.state.username = credentials["username"]
                self.state.owner_id = "owner-" + credentials["username"]
            self._json(
                200,
                {
                    "access_token": FIXTURE_SECRETS[1],
                    "token_type": "Bearer",
                    "expires_in": 31_536_000,
                    "user": {
                        "id": self.state.owner_id,
                        "username": self.state.username,
                    },
                },
            )
            return
        if path == "/project-file" and self.command == "GET":
            # The immutable imported archive is available for exact private
            # draft reconciliation before listing promotion, and the same URL
            # remains the public manual readback afterward. It must never carry
            # the Factory bearer.
            with self.state.lock:
                if self.state.imports != 1 or not self.state.manual:
                    self._json(404, {"error": "not imported"})
                    return
                manual = (
                    self.state.override_public_manual
                    if self.state.override_public_manual is not None
                    else self.state.manual
                )
            self._send(200, manual, "application/pdf")
            return
        if not self._authenticated():
            self._json(401, {"error": "missing fixture authentication"})
            return
        if path == "/api/v1/designs/import" and self.command == "POST":
            with self.state.lock:
                if self.state.imports:
                    self._json(409, {"error": "duplicate import"})
                    return
            values = _multipart_values(self.headers.get("Content-Type", ""), body)
            files = values.get("file", [])
            if len(files) != 1:
                self._json(422, {"error": "one import archive is required"})
                return
            try:
                with zipfile.ZipFile(BytesIO(files[0])) as archive:
                    names = archive.namelist()
                    hashes = {
                        name: sha256_bytes(archive.read(name))
                        for name in names
                        if not name.endswith("/")
                    }
                    manual = archive.read("MANUAL.pdf")
            except (KeyError, OSError, zipfile.BadZipFile):
                self._json(422, {"error": "invalid release archive"})
                return
            with self.state.lock:
                self.state.imports += 1
                self.state.archive_hashes = hashes
                self.state.manual = manual
                self.state.import_has_manual = bool(manual)
                self.state.import_has_cad = any(
                    name.casefold().endswith((".step", ".stl")) for name in hashes
                )
                title = values.get("title")
                description = values.get("description")
                tags = values.get("tags", [])
                category = values.get("category")
                if title:
                    self.state.title = title[0].decode("utf-8")
                if description:
                    self.state.description = description[0].decode("utf-8")
                self.state.tags = [value.decode("utf-8") for value in tags if value]
                self.state.category = (
                    category[0].decode("utf-8") if category else None
                )
                design = self.state.design()
            self._json(201, design)
            return
        if path.endswith("/publish") and self.command == "POST":
            with self.state.lock:
                if self.state.promotions:
                    self._json(409, {"error": "duplicate publication"})
                    return
                self.state.promotions += 1
                self.state.public = True
            self._json(200, {})
            return
        if "/api/v1/designs/" in path and self.command == "GET":
            with self.state.lock:
                design = self.state.design()
            self._json(200, design)
            return
        self._json(404, {"error": "unexpected mock Factory endpoint"})

    do_GET = _dispatch
    do_POST = _dispatch


class MockSessionFactoryServer:
    """One loopback server reached only by production Factory transports."""

    def __init__(self, product_id: str) -> None:
        self.state = _FactoryState(product_id)
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._server.state = self.state  # type: ignore[attr-defined]
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="workshop-mock-session-factory",
            daemon=True,
        )

    @property
    def origin(self) -> str:
        host, port = self._server.server_address[:2]
        return "http://%s:%d" % (host, port)

    def __enter__(self) -> "MockSessionFactoryServer":
        self._thread.start()
        return self

    def __exit__(
        self,
        unused_type: object,
        unused_value: object,
        unused_traceback: object,
    ) -> None:
        del unused_type, unused_value, unused_traceback
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    def _request(
        self,
        method: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: int,
    ) -> tuple[int, Mapping[str, str], bytes]:
        if not self.origin.startswith("http://127.0.0.1:"):
            raise AssertionError("mock Factory transport is not loopback")
        request = urllib.request.Request(
            self.origin + path,
            data=body,
            headers=dict(headers),
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content = response.read(MAX_RESPONSE_BYTES + 1)
                return response.status, dict(response.headers), content
        except urllib.error.HTTPError as exc:
            return (
                exc.code,
                dict(exc.headers or {}),
                exc.read(MAX_RESPONSE_BYTES + 1),
            )

    def transport(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: int,
    ) -> HttpResponse:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise AssertionError("unexpected Factory logical destination")
        with self.state.lock:
            self.state.logical_calls.append((method, parsed.path))
        status, response_headers, content = self._request(
            method, parsed.path, headers, body, timeout
        )
        return HttpResponse(status, response_headers, content)

    def project_file_transport(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: int,
    ) -> FactoryProjectFileResponse:
        parsed = urllib.parse.urlsplit(url)
        if (
            method != "GET"
            or parsed.scheme != "https"
            or parsed.hostname != "cdn.autonomous.ai"
            or not parsed.path.endswith("/" + FACTORY_PROJECT_PDF_MANUAL_FILENAME)
            or body is not None
        ):
            raise AssertionError("unexpected Factory project-file request")
        with self.state.lock:
            self.state.logical_calls.append((method, parsed.path))
        status, response_headers, content = self._request(
            "GET", "/project-file", headers, None, timeout
        )
        return FactoryProjectFileResponse(status, response_headers, content)

    def assert_complete(self) -> None:
        if self.state.imports != 1 or self.state.promotions != 1:
            raise AssertionError("Factory fixture did not observe one import and publication")
        if not self.state.public:
            raise AssertionError("Factory fixture did not reach public state")
        if self.state.category != FACTORY_TOY_CATEGORY_SLUG:
            raise AssertionError("Factory fixture received the wrong category")
        if not self.state.import_has_cad or not self.state.import_has_manual:
            raise AssertionError("Factory fixture did not receive CAD and MANUAL.pdf")
        if not any(path == "/project-file" for unused_method, path in self.state.loopback_calls):
            raise AssertionError("Factory fixture received no public manual readback")


__all__ = ["MockSessionFactoryServer"]
