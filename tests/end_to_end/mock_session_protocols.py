"""Loopback external protocols for the real-Codex mock-session acceptance run."""

from __future__ import annotations

import base64
from email.parser import BytesParser
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping, Optional

from workshop.integrations.factory import HttpResponse, MAX_RESPONSE_BYTES


_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


class _ProtocolState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.calls: list[tuple[str, str]] = []
        self.username = "mock-inventor"
        self.owner_id = "owner-mock-inventor"
        self.slug = "mock-session-pocket-token"
        self.title = "Mock Session Pocket Token"
        self.description = "A minimal private acceptance artifact."
        self.tags: list[str] = ["acceptance"]
        self.category: Optional[str] = None
        self.use_case: Optional[Mapping[str, Any]] = None
        self.story_blocks: list[Mapping[str, Any]] = []
        self.public = False
        self.concept_requests = 0
        self.run_root: Optional[Path] = None
        self.concept_pre_render_verified = False

    def design(self) -> Mapping[str, Any]:
        return {
            "id": "design-mock-session",
            "slug": self.slug,
            "owner_id": self.owner_id,
            "root_id": "design-mock-session",
            "current_history_id": "history-mock-session-1",
            "published_history_id": "history-mock-session-1" if self.public else None,
            "status": "public" if self.public else "draft",
            "project_url": "https://cdn.example/mock-session-project/",
            "origin": "import",
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
            "category": {"slug": self.category} if self.category else None,
            "author": {"id": self.owner_id},
            "thumbnail_urls": ["https://cdn.example/mock-session-cover.png"],
            "use_case": dict(self.use_case) if self.use_case is not None else None,
            "story_blocks": [dict(value) for value in self.story_blocks],
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


class _Handler(BaseHTTPRequestHandler):
    server_version = "WorkshopMockSession/1"

    @property
    def state(self) -> _ProtocolState:
        return self.server.state  # type: ignore[attr-defined]

    def log_message(self, unused_format: str, *unused_arguments: object) -> None:
        del unused_format, unused_arguments

    def _body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > 64 * 1024 * 1024:
            raise ValueError("mock protocol request exceeds its bound")
        return self.rfile.read(length)

    def _send(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, value: object) -> None:
        self._send(status, _canonical_json(value))

    def _dispatch(self) -> None:
        path = urllib.parse.urlsplit(self.path).path
        with self.state.lock:
            self.state.calls.append((self.command, path))
        body = self._body()
        if path == "/concept-images":
            document = json.loads(body.decode("utf-8"))
            if not isinstance(document, dict) or not isinstance(document.get("prompt"), str):
                self._json(422, {"error": "invalid concept request"})
                return
            with self.state.lock:
                if self.state.run_root is not None and self.state.concept_requests == 0:
                    run_root = self.state.run_root
                    sealed = tuple((run_root / "artifacts/concept").rglob("sealed-concept.json"))
                    images = tuple((run_root / "artifacts/concept").rglob("*.png"))
                    if not (run_root / "agent-outcome.json").is_file() or sealed or images:
                        self._json(409, {"error": "Concept did not cross the pre-render boundary"})
                        return
                    self.state.concept_pre_render_verified = True
                self.state.concept_requests += 1
            self._json(200, {"data": [{"b64_json": base64.b64encode(_PNG).decode()}]})
            return
        if path.endswith("/auth/agent/login"):
            credentials = json.loads(body.decode("utf-8"))
            username = credentials.get("username")
            if not isinstance(username, str) or not username:
                self._json(401, {"error": "rejected"})
                return
            with self.state.lock:
                self.state.username = username
                self.state.owner_id = "owner-" + username
            self._json(
                200,
                {
                    "access_token": "mock-session-access-token",
                    "token_type": "Bearer",
                    "expires_in": 31_536_000,
                    "user": {"id": self.state.owner_id, "username": username},
                },
            )
            return
        if path.endswith("/designs/import"):
            values = _multipart_values(self.headers.get("Content-Type", ""), body)
            with self.state.lock:
                self.state.title = values["title"][0].decode("utf-8")
                self.state.description = values["description"][0].decode("utf-8")
                self.state.tags = [value.decode("utf-8") for value in values.get("tags", []) if value]
                category = values.get("category")
                self.state.category = category[0].decode("utf-8") if category else None
                design = self.state.design()
            self._json(201, design)
            return
        if path.endswith("/use-case") and self.command == "PATCH":
            value = json.loads(body.decode("utf-8"))
            with self.state.lock:
                self.state.use_case = dict(value)
                response = {
                    "use_case": dict(value),
                    "story_blocks": [dict(item) for item in self.state.story_blocks],
                }
            self._json(200, response)
            return
        if path.endswith("/story-blocks") and self.command == "PUT":
            value = json.loads(body.decode("utf-8"))
            with self.state.lock:
                self.state.story_blocks = [dict(item) for item in value["story_blocks"]]
                response = {
                    "use_case": dict(self.state.use_case) if self.state.use_case else None,
                    "story_blocks": [dict(item) for item in self.state.story_blocks],
                }
            self._json(200, response)
            return
        if path.endswith("/publish") and self.command == "POST":
            with self.state.lock:
                self.state.public = True
            self._json(200, {})
            return
        if "/designs/" in path and self.command == "GET":
            with self.state.lock:
                design = self.state.design()
            self._json(200, design)
            return
        self._json(404, {"error": "unknown mock-session endpoint"})

    do_GET = _dispatch
    do_POST = _dispatch
    do_PATCH = _dispatch
    do_PUT = _dispatch


class MockSessionProtocolServer:
    """One loopback server used only through production adapter transports."""

    def __init__(self) -> None:
        self.state = _ProtocolState()
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._server.state = self.state  # type: ignore[attr-defined]
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="workshop-mock-session-protocols",
            daemon=True,
        )

    @property
    def origin(self) -> str:
        host, port = self._server.server_address[:2]
        return "http://%s:%d" % (host, port)

    def __enter__(self) -> "MockSessionProtocolServer":
        self._thread.start()
        return self

    def __exit__(self, unused_type: object, unused_value: object, unused_traceback: object) -> None:
        del unused_type, unused_value, unused_traceback
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    def concept_opener(self, request: urllib.request.Request, *, timeout: float) -> object:
        target = self.origin + "/concept-images"
        remapped = urllib.request.Request(
            target,
            data=request.data,
            headers=dict(request.header_items()),
            method=request.get_method(),
        )
        return urllib.request.urlopen(remapped, timeout=timeout)

    def factory_transport(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Optional[bytes],
        timeout: int,
    ) -> HttpResponse:
        path = urllib.parse.urlsplit(url).path
        request = urllib.request.Request(
            self.origin + path,
            data=body,
            headers=dict(headers),
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content = response.read(MAX_RESPONSE_BYTES + 1)
                return HttpResponse(response.status, dict(response.headers), content)
        except urllib.error.HTTPError as exc:
            return HttpResponse(exc.code, dict(exc.headers or {}), exc.read(MAX_RESPONSE_BYTES + 1))
