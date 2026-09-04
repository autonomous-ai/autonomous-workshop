"""PKCE browser authorization for a host-owned Factory credential.

The browser returns only a short-lived, single-use authorization code through a
normal top-level redirect to the loopback listener. Workshop proves possession
of the in-memory PKCE verifier directly to the Factory API; the generated
username/password pair never passes through browser JavaScript or a URL.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import os
import re
import secrets
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Optional

from workshop.errors import WorkshopError


DEFAULT_INVENTOR_LOGIN_URL = "https://www.autonomous.ai/toys/inventor/login"
DEFAULT_CREDENTIAL_EXCHANGE_URL = (
    "https://panda-social-api.autonomous.ai/api/v1/"
    "auth/agent-credentials/exchange"
)
INVENTOR_LOGIN_URL_ENV = "WORKSHOP_INVENTOR_LOGIN_URL"
LOGIN_CALLBACK_PATH = "/callback"
LOGIN_TIMEOUT_SECONDS = 5 * 60
HTTP_TIMEOUT_SECONDS = 30
MAX_EXCHANGE_RESPONSE_BYTES = 64 * 1024
_AUTHORIZATION_CODE = re.compile(r"^[A-Za-z0-9_-]{43}$")
_INVENTOR_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _bounded_secret(value: object, label: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > maximum
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise WorkshopError("%s is missing or malformed" % label)
    return value


@dataclass(frozen=True, repr=False)
class BrowserLoginCredential:
    """Validated Factory values returned directly to Workshop."""

    username: str
    password: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "username",
            _bounded_secret(self.username, "Factory username", 512),
        )
        object.__setattr__(
            self,
            "password",
            _bounded_secret(self.password, "Factory password", 4096),
        )

    def __repr__(self) -> str:
        return "BrowserLoginCredential(<redacted>)"


CodeExchanger = Callable[[str, str], BrowserLoginCredential]
BrowserOpener = Callable[[str], bool]


def _exchange_authorization_code(
    code: str,
    code_verifier: str,
    *,
    exchange_url: str = DEFAULT_CREDENTIAL_EXCHANGE_URL,
) -> BrowserLoginCredential:
    body = json.dumps(
        {"code": code, "code_verifier": code_verifier},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    request = urllib.request.Request(
        exchange_url,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AutonomousWorkshop/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise WorkshopError("Workshop authorization exchange was rejected")
            source = response.read(MAX_EXCHANGE_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise WorkshopError("Workshop authorization exchange was rejected") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise WorkshopError(
            "Workshop could not reach the Autonomous account service"
        ) from exc
    if len(source) > MAX_EXCHANGE_RESPONSE_BYTES:
        raise WorkshopError("Workshop authorization response was too large")
    try:
        value = json.loads(source.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise WorkshopError("Workshop authorization response was malformed") from exc
    if not isinstance(value, dict):
        raise WorkshopError("Workshop authorization response was malformed")
    return BrowserLoginCredential(
        username=value.get("username"),
        password=value.get("password"),
    )


class _LoopbackServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address,
        handler,
        *,
        expected_state: str,
        exchange_code: Callable[[str], BrowserLoginCredential],
    ):
        super().__init__(address, handler)
        self.expected_state = expected_state
        self.exchange_code = exchange_code
        self.credential: Optional[BrowserLoginCredential] = None
        self.failure: Optional[str] = None
        self.claimed = False
        self.completed = threading.Event()
        self.result_lock = threading.Lock()


class _CallbackHandler(BaseHTTPRequestHandler):
    server: _LoopbackServer
    server_version = "AutonomousWorkshop"
    sys_version = ""

    def log_message(self, format: str, *args: object) -> None:
        return

    def _respond(self, status: int, title: str, message: str) -> None:
        status_class = "success" if status < 400 else "error"
        status_icon = "✓" if status < 400 else "!"
        document = (
            '<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width">'
            '<meta http-equiv="Content-Security-Policy" '
            'content="default-src \'none\'; style-src \'unsafe-inline\'">'
            '<meta name="referrer" content="no-referrer">'
            "<title>%s</title>"
            "<style>"
            "*{box-sizing:border-box}body{margin:0;background:#f3f3ef;color:#191a17;"
            "font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}"
            "main{min-height:100vh;display:grid;place-items:center;padding:24px}"
            "section{width:min(460px,100%%);padding:40px;border:1px solid #dcddd7;"
            "border-radius:18px;background:#fffffd;box-shadow:0 24px 70px "
            "rgba(20,22,18,.1);text-align:center}"
            "i{display:grid;width:48px;height:48px;margin:0 auto 20px;"
            "place-items:center;border-radius:50%%;background:#ddf5e8;color:#23734b;"
            "font-size:22px;font-style:normal;font-weight:700}"
            "i.error{background:#fbe4e2;color:#a72d27}"
            "h1{margin:0 0 10px;font-size:30px;letter-spacing:-.03em}"
            "p{margin:0;color:#62645e;line-height:1.55}"
            '</style></head><body><main><section><i class="%s">%s</i>'
            "<h1>%s</h1><p>%s</p>"
            "</section></main></body></html>"
        ) % tuple(
            html.escape(value)
            for value in (title, status_class, status_icon, title, message)
        )
        body = document.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _is_callback_target(self) -> bool:
        expected_host = "127.0.0.1:%d" % self.server.server_address[1]
        parsed = urllib.parse.urlsplit(self.path)
        return (
            parsed.path == LOGIN_CALLBACK_PATH
            and not parsed.fragment
            and self.headers.get("Host") == expected_host
        )

    def _callback_code(self) -> Optional[str]:
        try:
            values = urllib.parse.parse_qs(
                urllib.parse.urlsplit(self.path).query,
                keep_blank_values=True,
                strict_parsing=True,
                max_num_fields=2,
            )
            state = values.get("state", [])
            code = values.get("code", [])
            if (
                set(values) != {"code", "state"}
                or len(state) != 1
                or not hmac.compare_digest(state[0], self.server.expected_state)
                or len(code) != 1
                or _AUTHORIZATION_CODE.fullmatch(code[0]) is None
            ):
                return None
            return code[0]
        except (UnicodeError, ValueError):
            return None

    def do_GET(self) -> None:
        if not self._is_callback_target():
            self._respond(
                404,
                "Connection not found",
                "Return to the terminal and start the connection again.",
            )
            return
        code = self._callback_code()
        if code is None:
            self._respond(
                400,
                "Connection could not be verified",
                "Return to the terminal and start the connection again.",
            )
            return
        with self.server.result_lock:
            if self.server.claimed or self.server.completed.is_set():
                self._respond(
                    409,
                    "Connection already completed",
                    "You can close this tab and continue in the terminal.",
                )
                return
            self.server.claimed = True
        try:
            credential = self.server.exchange_code(code)
        except WorkshopError as exc:
            self.server.failure = str(exc)
            try:
                self._respond(
                    502,
                    "Connection did not finish",
                    "Return to the terminal for details, then try again.",
                )
            finally:
                self.server.completed.set()
            return
        self.server.credential = credential
        try:
            self._respond(
                200,
                "Inventor connected",
                "You're all set. Workshop is continuing in your terminal.",
            )
        finally:
            self.server.completed.set()

    def do_POST(self) -> None:
        self._respond(
            405,
            "Connection method not allowed",
            "Return to the terminal and start the connection again.",
        )

    def do_OPTIONS(self) -> None:
        self._respond(
            405,
            "Connection method not allowed",
            "Return to the terminal and start the connection again.",
        )


class FactoryBrowserLogin:
    """One PKCE browser authorization backed by a loopback callback."""

    def __init__(
        self,
        *,
        inventor_id: str,
        login_url: Optional[str] = None,
        opener: BrowserOpener = webbrowser.open,
        exchanger: CodeExchanger = _exchange_authorization_code,
    ) -> None:
        if (
            not isinstance(inventor_id, str)
            or _INVENTOR_ID.fullmatch(inventor_id) is None
        ):
            raise WorkshopError("Inventor id must be a canonical slug")
        configured_login_url = os.environ.get(INVENTOR_LOGIN_URL_ENV)
        if login_url is None:
            login_url = configured_login_url or DEFAULT_INVENTOR_LOGIN_URL
        parsed = urllib.parse.urlsplit(login_url)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise WorkshopError("Inventor login URL is malformed")
        if parsed.scheme != "https" and parsed.hostname not in (
            "localhost",
            "127.0.0.1",
        ):
            raise WorkshopError("Inventor login URL must use HTTPS")
        if (
            configured_login_url
            and login_url == configured_login_url
            and parsed.hostname not in ("localhost", "127.0.0.1")
        ):
            raise WorkshopError(
                "%s may only target localhost" % INVENTOR_LOGIN_URL_ENV
            )
        self._login_url = login_url
        self._inventor_id = inventor_id
        self._opener = opener
        self._exchanger = exchanger
        self._state = secrets.token_urlsafe(32)
        self._code_verifier = secrets.token_urlsafe(32)
        self._code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(self._code_verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self._server: Optional[_LoopbackServer] = None
        self._thread: Optional[threading.Thread] = None

    def __enter__(self) -> "FactoryBrowserLogin":
        try:
            self._server = _LoopbackServer(
                ("127.0.0.1", 0),
                _CallbackHandler,
                expected_state=self._state,
                exchange_code=lambda code: self._exchanger(
                    code, self._code_verifier
                ),
            )
        except OSError as exc:
            raise WorkshopError(
                "Workshop could not start the local login callback"
            ) from exc
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="workshop-login-callback",
            daemon=True,
        )
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)

    @property
    def authorization_url(self) -> str:
        if self._server is None:
            raise WorkshopError("Workshop login callback is not running")
        callback_url = "http://127.0.0.1:%d%s" % (
            self._server.server_address[1],
            LOGIN_CALLBACK_PATH,
        )
        query = urllib.parse.urlencode(
            {
                "callback_url": callback_url,
                "state": self._state,
                "inventor_id": self._inventor_id,
                "code_challenge": self._code_challenge,
                "code_challenge_method": "S256",
            }
        )
        return self._login_url + "?" + query

    def open_browser(self) -> bool:
        try:
            return bool(self._opener(self.authorization_url))
        except Exception:
            return False

    def wait(
        self, timeout_seconds: int = LOGIN_TIMEOUT_SECONDS
    ) -> BrowserLoginCredential:
        if (
            self._server is None
            or type(timeout_seconds) is not int
            or timeout_seconds <= 0
        ):
            raise WorkshopError("Workshop login wait is not configured")
        if not self._server.completed.wait(timeout_seconds):
            raise WorkshopError(
                "Browser login timed out after %d minutes"
                % (timeout_seconds // 60)
            )
        if self._server.failure is not None:
            raise WorkshopError(self._server.failure)
        if self._server.credential is None:
            raise WorkshopError("Browser login did not return a credential")
        return self._server.credential


__all__ = [
    "BrowserLoginCredential",
    "DEFAULT_CREDENTIAL_EXCHANGE_URL",
    "DEFAULT_INVENTOR_LOGIN_URL",
    "FactoryBrowserLogin",
    "INVENTOR_LOGIN_URL_ENV",
    "LOGIN_TIMEOUT_SECONDS",
]
