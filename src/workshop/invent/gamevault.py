"""Live access to the game-design vault served by the panda VM's admindash.

The vault (``github.com/nohope88/gamevault``) is maintained on the VM and
exposed at ``/api/gamevault/*`` behind one bearer token.  The Workshop host
calls it at each phase that needs design knowledge — Invent, Make, Playtest
— and writes what it learned back after a sealed Playtest.  Product runs
never talk to it: the Codex sandbox has no network, so the host hands every
run a per-phase snapshot (:data:`workshop.invent.vault.RUN_VAULT_PATH`) and
the leads it computed from that snapshot.

Configuration is host-only.  ``WORKSHOP_GAMEVAULT_URL`` and
``WORKSHOP_GAMEVAULT_TOKEN`` in the process environment win; otherwise the
private file ``$WORKSHOP_HOME/credentials/gamevault.env`` (``0600`` in a
``0700`` directory, ``NAME=value`` lines) supplies them.  Neither source
reaches a product run's environment.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from workshop.errors import ContractError, WorkshopError
from workshop.invent.vault import MAX_VAULT_NODES, Vault, VaultError, parse_node
from workshop.runtime.credentials import private_credential_values
from workshop.runtime.package_data import default_workshop_home


DEFAULT_GAMEVAULT_URL = "http://178.128.89.39:8090"
GAMEVAULT_URL_NAME = "WORKSHOP_GAMEVAULT_URL"
GAMEVAULT_TOKEN_NAME = "WORKSHOP_GAMEVAULT_TOKEN"
GAMEVAULT_CREDENTIAL_FILE = "gamevault.env"
HTTP_TIMEOUT_SECONDS = 30
WRITE_TIMEOUT_SECONDS = 180
MAX_RESPONSE_BYTES = 32 * 1024 * 1024
MAX_TOKEN_LENGTH = 512
MAX_WRITE_ITEMS = 64
USER_AGENT = "autonomous-workshop-gamevault/1"
_CREDENTIAL_NAME = re.compile(r"^WORKSHOP_GAMEVAULT_(URL|TOKEN)$")
_EXPORT_PATH = "/api/gamevault/export"
_RESOLVE_PATH = "/api/gamevault/resolve"
_CHECK_PATH = "/api/gamevault/check"
_LEADS_PATH = "/api/gamevault/leads"
_EVIDENCE_PATH = "/api/gamevault/evidence"
_REVIEW_PATH = "/api/gamevault/review"


class GameVaultError(WorkshopError):
    """The vault API refused a request or answered with something malformed."""


class GameVaultUnavailable(GameVaultError):
    """The vault API cannot be reached or authorised; fail closed, resume later."""


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    content: bytes


Transport = Callable[[str, str, Mapping[str, str], Optional[bytes], int], HttpResponse]


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def urllib_transport(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: Optional[bytes],
    timeout: int,
) -> HttpResponse:
    request = urllib.request.Request(url, method=method, data=body)
    for name, value in headers.items():
        request.add_header(name, value)
    try:
        opener = urllib.request.build_opener(_NoRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            content = response.read(MAX_RESPONSE_BYTES + 1)
            if len(content) > MAX_RESPONSE_BYTES:
                raise GameVaultError("game vault response exceeds the size limit")
            return HttpResponse(response.status, dict(response.headers), content)
    except urllib.error.HTTPError as exc:
        content = exc.read(MAX_RESPONSE_BYTES + 1)
        return HttpResponse(exc.code, dict(exc.headers or {}), content[:MAX_RESPONSE_BYTES])
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise GameVaultUnavailable("game vault is unreachable: %s" % exc) from exc


# The only test seam: replace outbound HTTP, keep every request and response rule.
_TRANSPORT: Transport = urllib_transport


@dataclass(frozen=True)
class GameVaultConfig:
    url: str
    token: str


def gamevault_credential_file(environment: Optional[Mapping[str, str]] = None) -> Path:
    """The host-only private file that may hold the vault URL and token."""

    return default_workshop_home(environment) / "credentials" / GAMEVAULT_CREDENTIAL_FILE


def gamevault_config(environment: Optional[Mapping[str, str]] = None) -> GameVaultConfig:
    """Resolve the vault URL and token from the environment, then the private file."""

    values = os.environ if environment is None else environment
    url = values.get(GAMEVAULT_URL_NAME) or ""
    token = values.get(GAMEVAULT_TOKEN_NAME) or ""
    path = gamevault_credential_file(values)
    if (not url or not token) and (path.exists() or path.is_symlink()):
        loaded = private_credential_values(path, _CREDENTIAL_NAME, label="game vault")
        url = url or loaded.get(GAMEVAULT_URL_NAME, "")
        token = token or loaded.get(GAMEVAULT_TOKEN_NAME, "")
    url = url or DEFAULT_GAMEVAULT_URL
    if not token:
        raise GameVaultUnavailable(
            "no game vault token: set %s or write %s" % (GAMEVAULT_TOKEN_NAME, path)
        )
    if (
        len(token) > MAX_TOKEN_LENGTH
        or token != token.strip()
        or any(ord(character) < 33 or ord(character) == 127 for character in token)
    ):
        raise ContractError("game vault token is malformed")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.query or parsed.fragment:
        raise ContractError("game vault URL must be an http(s) origin")
    return GameVaultConfig(url.rstrip("/"), token)


class GameVaultClient:
    """Bounded bearer-token client for the vault API."""

    def __init__(
        self,
        config: GameVaultConfig,
        transport: Optional[Transport] = None,
        *,
        timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
    ) -> None:
        if not isinstance(config, GameVaultConfig):
            raise ContractError("game vault client needs a GameVaultConfig")
        if type(timeout_seconds) is not int or timeout_seconds <= 0:
            raise ContractError("game vault timeout must be a positive integer")
        self.config = config
        self.transport = transport
        self.timeout_seconds = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, str]] = None,
        body: Optional[Mapping[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Mapping[str, Any]:
        url = self.config.url + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.config.token,
            "User-Agent": USER_AGENT,
        }
        payload = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        transport = self.transport if self.transport is not None else _TRANSPORT
        try:
            response = transport(method, url, headers, payload, timeout or self.timeout_seconds)
        except (OSError, TimeoutError) as exc:
            raise GameVaultUnavailable("game vault is unreachable: %s" % exc) from exc
        if response.status in (401, 403):
            raise GameVaultUnavailable("game vault token was refused (%d)" % response.status)
        try:
            document = json.loads(response.content.decode("utf-8")) if response.content else {}
        except (UnicodeError, ValueError):
            document = None
        if response.status == 400:
            detail = document.get("error") if isinstance(document, Mapping) else None
            raise GameVaultError("game vault refused the request: %s" % (detail or "bad request"))
        if response.status != 200:
            raise GameVaultUnavailable("game vault answered %d for %s" % (response.status, path))
        if not isinstance(document, Mapping):
            raise GameVaultError("game vault answered with something other than a JSON object")
        return document

    # ---- reads --------------------------------------------------------

    def export(self) -> Vault:
        """Fetch every node and build the graph the host seals into a run."""

        document = self._request("GET", _EXPORT_PATH)
        raw = document.get("nodes")
        if (
            not isinstance(raw, Mapping)
            or not raw
            or len(raw) > MAX_VAULT_NODES
            or document.get("count") != len(raw)
        ):
            raise GameVaultError("game vault export is malformed")
        nodes: dict[str, Mapping[str, Any]] = {}
        for path, text in raw.items():
            if not isinstance(path, str) or not isinstance(text, str):
                raise GameVaultError("game vault export node %r is malformed" % (path,))
            try:
                nodes[path] = parse_node(text)
            except VaultError as exc:
                raise GameVaultError("game vault export node %s: %s" % (path, exc)) from exc
        try:
            return Vault(nodes)
        except VaultError as exc:
            raise GameVaultError("game vault export is not a valid vault: %s" % exc) from exc

    def resolve(self, name: str, folder: str = "mechanisms") -> Optional[str]:
        document = self._request("GET", _RESOLVE_PATH, query={"name": name, "folder": folder})
        path = document.get("path")
        if path is not None and not isinstance(path, str):
            raise GameVaultError("game vault resolve answer is malformed")
        return path

    def check(self, paths: Sequence[str]) -> list[Mapping[str, Any]]:
        document = self._request("GET", _CHECK_PATH, query={"paths": ",".join(paths)})
        return _findings(document)

    def leads(self, concept: Mapping[str, Any]) -> Mapping[str, Any]:
        document = self._request("POST", _LEADS_PATH, body={"concept": dict(concept)})
        _findings(document)
        return document

    # ---- writes -------------------------------------------------------

    def post_evidence(
        self,
        rows: Sequence[Mapping[str, Any]],
        *,
        label: str,
        design: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        """Bank confirmed rows and, when given, the product's own game page."""

        body: dict[str, Any] = {"label": label}
        if rows or design is None:
            body["rows"] = _write_items(rows, "evidence rows")
        if design is not None:
            if not isinstance(design, Mapping) or not design.get("slug"):
                raise ContractError("design must name the product slug")
            body["design"] = dict(design)
        return self._request(
            "POST", _EVIDENCE_PATH, body=body, timeout=WRITE_TIMEOUT_SECONDS
        )

    def post_review(
        self, dismissals: Sequence[Mapping[str, Any]], *, label: str
    ) -> Mapping[str, Any]:
        return self._request(
            "POST",
            _REVIEW_PATH,
            body={"label": label, "dismissals": _write_items(dismissals, "dismissals")},
            timeout=WRITE_TIMEOUT_SECONDS,
        )


def _findings(document: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    findings = document.get("findings")
    if not isinstance(findings, list) or any(
        not isinstance(item, Mapping) or not isinstance(item.get("kind"), str)
        for item in findings
    ):
        raise GameVaultError("game vault findings are malformed")
    return list(findings)


def _write_items(items: Sequence[Mapping[str, Any]], label: str) -> list[dict[str, Any]]:
    if not isinstance(items, (list, tuple)) or not 1 <= len(items) <= MAX_WRITE_ITEMS:
        raise ContractError("%s must hold 1 to %d items" % (label, MAX_WRITE_ITEMS))
    if any(not isinstance(item, Mapping) for item in items):
        raise ContractError("%s must be objects" % label)
    return [dict(item) for item in items]


def default_client(environment: Optional[Mapping[str, str]] = None) -> GameVaultClient:
    """The host's client: resolved configuration over the module transport."""

    return GameVaultClient(gamevault_config(environment))


__all__ = [
    "DEFAULT_GAMEVAULT_URL",
    "GAMEVAULT_TOKEN_NAME",
    "GAMEVAULT_URL_NAME",
    "GameVaultClient",
    "GameVaultConfig",
    "GameVaultError",
    "GameVaultUnavailable",
    "HttpResponse",
    "default_client",
    "gamevault_config",
    "gamevault_credential_file",
    "urllib_transport",
]
