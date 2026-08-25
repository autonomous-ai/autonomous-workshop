"""Credential-safe Factory agent login for the shared Instructions adapter.

The Factory agent credential is used only to mint an in-memory bearer token.
Neither the credential nor the token is written to the Workshop store, passed
on the command line, included in errors, or exposed by ``repr``.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Callable, Mapping, MutableMapping, Optional

from workshop.errors import (
    AmbiguousEffectError,
    ContractError,
    PublishError,
    ReceiptError,
)
from workshop.runtime import Receipt
from workshop.integrations.shop import (
    DEFAULT_SHOP_API,
    HTTP_TIMEOUT_SECONDS,
    MAX_RESPONSE_BYTES,
    SHOP_USER_AGENT,
    PROVEN_NO_EFFECT_STATUSES,
    HttpResponse,
    ShopDoor,
    ShopInstructionsWriter,
    Transport,
    urllib_transport,
    _design_with_normalized_currency,
)
from workshop.runtime import InventorStore


_INVENTOR_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PLACEHOLDER_TOKEN = "factory-agent-session-managed-token"
Sleeper = Callable[[float], None]


class FactoryAuthenticationError(PublishError):
    """Factory could not establish an authenticated agent session."""


class FactoryCredentialRejected(FactoryAuthenticationError):
    """Factory rejected a rotated, disabled, or otherwise invalid credential."""


def _secret_text(value: Any, label: str, limit: int) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > limit
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s is missing or malformed" % label)
    return value


@dataclass(frozen=True, repr=False)
class FactoryAgentCredentials:
    """One inventor's login secret, deliberately opaque in diagnostics."""

    username: str
    password: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "username", _secret_text(self.username, "Factory username", 512)
        )
        object.__setattr__(
            self, "password", _secret_text(self.password, "Factory password", 4096)
        )

    def __repr__(self) -> str:
        return "FactoryAgentCredentials(username=<redacted>, password=<redacted>)"


def factory_credentials_from_environment(
    inventor_id: str,
    environ: Mapping[str, str],
) -> FactoryAgentCredentials:
    """Load a complete pair without ever returning a partial credential.

    Each selected inventor runs in an isolated process whose environment uses
    the backend spec's exact ``FACTORY_USERNAME`` and ``FACTORY_PASSWORD``
    names. No alternative name or file fallback is accepted here.
    """

    if not isinstance(inventor_id, str) or not _INVENTOR_ID.fullmatch(inventor_id):
        raise ContractError("Factory inventor_id must be a canonical slug")
    if not isinstance(environ, Mapping):
        raise ContractError("Factory credential environment must be a mapping")
    generic_names = ("FACTORY_USERNAME", "FACTORY_PASSWORD")
    generic = tuple(environ.get(name) for name in generic_names)
    if any(value is not None for value in generic):
        if not all(isinstance(value, str) and value for value in generic):
            raise ContractError("Factory username/password must be configured together")
        credentials = FactoryAgentCredentials(generic[0], generic[1])  # type: ignore[arg-type]
        if credentials.username.casefold() != inventor_id.casefold():
            raise ContractError(
                "Factory username must exactly match the selected inventor_id"
            )
        return credentials
    raise ContractError("Factory agent credentials are not configured")


@dataclass(frozen=True)
class FactoryAgentIdentity:
    owner_id: str
    username: str
    expires_in: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "owner_id", _secret_text(self.owner_id, "Factory owner identity", 512)
        )
        object.__setattr__(
            self, "username", _secret_text(self.username, "Factory account username", 512)
        )
        if (
            type(self.expires_in) is not int
            or self.expires_in <= 0
            or self.expires_in > 400 * 24 * 60 * 60
        ):
            raise ContractError("Factory token expiry is malformed")


class FactoryAgentSession:
    """Mint and cache a Factory bearer, with the specified one-time 401 retry."""

    def __init__(
        self,
        credentials: FactoryAgentCredentials,
        *,
        api_base: str = DEFAULT_SHOP_API,
        transport: Transport = urllib_transport,
        timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
        sleeper: Sleeper = time.sleep,
        max_login_rate_retries: int = 2,
    ) -> None:
        if not isinstance(credentials, FactoryAgentCredentials):
            raise ContractError("FactoryAgentSession requires typed credentials")
        parsed = urllib.parse.urlsplit(api_base)
        expected = urllib.parse.urlsplit(DEFAULT_SHOP_API)
        if (
            parsed.scheme != "https"
            or parsed.netloc != expected.netloc
            or parsed.path.rstrip("/") != expected.path.rstrip("/")
            or parsed.query
            or parsed.fragment
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ContractError("Factory agent API must use the pinned production origin")
        if not callable(transport) or not callable(sleeper):
            raise ContractError("Factory session transport and sleeper must be callable")
        if (
            type(timeout_seconds) is not int
            or timeout_seconds <= 0
            or type(max_login_rate_retries) is not int
            or not 0 <= max_login_rate_retries <= 5
        ):
            raise ContractError("Factory session retry configuration is malformed")
        self._credentials = credentials
        self._api_base = api_base.rstrip("/")
        self._api_origin = "%s://%s" % (parsed.scheme, parsed.netloc)
        self._transport = transport
        self._timeout_seconds = timeout_seconds
        self._sleeper = sleeper
        self._max_login_rate_retries = max_login_rate_retries
        self._access_token: Optional[str] = None
        self._identity: Optional[FactoryAgentIdentity] = None

    def __repr__(self) -> str:
        return "FactoryAgentSession(authenticated=%s)" % (
            "true" if self._access_token is not None else "false"
        )

    @staticmethod
    def _retry_after(response: HttpResponse) -> float:
        raw = next(
            (
                value
                for name, value in response.headers.items()
                if isinstance(name, str) and name.casefold() == "retry-after"
            ),
            None,
        )
        try:
            delay = float(raw) if raw is not None else 0.0
        except (TypeError, ValueError):
            delay = 0.0
        if not 0.0 <= delay <= 60.0:
            raise FactoryAuthenticationError(
                "Factory login rate limit supplied an unsafe Retry-After"
            )
        return delay

    @staticmethod
    def _login_value(response: HttpResponse) -> tuple[str, FactoryAgentIdentity]:
        if len(response.body) > MAX_RESPONSE_BYTES:
            raise FactoryAuthenticationError("Factory login response exceeded the limit")
        try:
            value = json.loads(response.body.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise FactoryAuthenticationError("Factory login response was malformed") from exc
        if not isinstance(value, Mapping):
            raise FactoryAuthenticationError("Factory login response was malformed")
        try:
            token = _secret_text(value.get("access_token"), "Factory access token", 16_384)
            if value.get("token_type") != "Bearer":
                raise ContractError("Factory token type is malformed")
            expires_in = value.get("expires_in")
            user = value.get("user")
            if not isinstance(user, Mapping):
                raise ContractError("Factory login user is malformed")
            identity = FactoryAgentIdentity(
                user.get("id"), user.get("username"), expires_in
            )
        except ContractError as exc:
            raise FactoryAuthenticationError("Factory login response was malformed") from exc
        return token, identity

    def login(self, *, force: bool = False) -> FactoryAgentIdentity:
        if not force and self._access_token is not None and self._identity is not None:
            return self._identity
        body = json.dumps(
            {
                "username": self._credentials.username,
                "password": self._credentials.password,
            },
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": SHOP_USER_AGENT,
        }
        for attempt in range(self._max_login_rate_retries + 1):
            response = self._transport(
                "POST",
                self._api_base + "/auth/agent/login",
                headers,
                body,
                self._timeout_seconds,
            )
            if response.status == 429 and attempt < self._max_login_rate_retries:
                self._sleeper(self._retry_after(response))
                continue
            if response.status == 401:
                self._access_token = None
                self._identity = None
                raise FactoryCredentialRejected(
                    "Factory rejected the agent credential; rotate or re-issue it"
                )
            if response.status != 200:
                self._access_token = None
                self._identity = None
                raise FactoryAuthenticationError(
                    "Factory agent login returned HTTP %s" % response.status
                )
            token, identity = self._login_value(response)
            self._access_token = token
            self._identity = identity
            return identity
        raise FactoryAuthenticationError("Factory agent login remained rate limited")

    def authenticated_transport(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Optional[bytes],
        timeout: int,
    ) -> HttpResponse:
        parsed = urllib.parse.urlsplit(url)
        if "%s://%s" % (parsed.scheme, parsed.netloc) != self._api_origin:
            raise ContractError("Factory bearer cannot be sent to another origin")
        identity = self.login()
        del identity
        assert self._access_token is not None

        def send() -> HttpResponse:
            safe_headers: MutableMapping[str, str] = {
                name: value
                for name, value in headers.items()
                if isinstance(name, str) and name.casefold() != "authorization"
            }
            safe_headers["Authorization"] = "Bearer %s" % self._access_token
            return self._transport(method, url, safe_headers, body, timeout)

        response = send()
        if response.status != 401:
            return response
        self._access_token = None
        self._identity = None
        self.login(force=True)
        return send()


class FactoryAgentInstructionsWriter:
    """Bind agent login to the existing sealed, private-draft Shop writer."""

    def __init__(
        self,
        store: InventorStore,
        inventor_id: str,
        credentials: FactoryAgentCredentials,
        *,
        transport: Transport = urllib_transport,
        sleeper: Sleeper = time.sleep,
    ) -> None:
        if not isinstance(store, InventorStore):
            raise ContractError("Factory Instructions writer requires an InventorStore")
        if not isinstance(inventor_id, str) or not _INVENTOR_ID.fullmatch(inventor_id):
            raise ContractError("Factory inventor_id must be a canonical slug")
        if credentials.username.casefold() != inventor_id.casefold():
            raise ContractError(
                "Factory username must exactly match the selected inventor_id"
            )
        self.inventor_id = inventor_id
        self._store = store
        self._session = FactoryAgentSession(
            credentials, transport=transport, sleeper=sleeper
        )

    def __repr__(self) -> str:
        return "FactoryAgentInstructionsWriter(inventor_id=%r, credentials=<redacted>)" % self.inventor_id

    def __call__(self, context: Any, sealed_root: Any, sealed_manifest: Any):
        identity = self._session.login()
        if identity.username.casefold() != self.inventor_id.casefold():
            raise ContractError(
                "authenticated Factory account does not match the selected inventor_id"
            )
        door = ShopDoor(
            _PLACEHOLDER_TOKEN,
            transport=self._session.authenticated_transport,
        )
        return ShopInstructionsWriter(
            self._store,
            door,
            identity.owner_id,
        )(context, sealed_root, sealed_manifest)


class FactoryPublicTransition:
    """Explicitly promote one verified private draft, then prove it by GET.

    This is intentionally separate from Instructions. It never supplies a
    price, title, attachment, or other creator-owned page material. Factory may
    apply its default listing policy. A caller must hand in the exact private
    draft Receipt that Instructions authenticated.
    """

    def __init__(self, session: FactoryAgentSession) -> None:
        if not isinstance(session, FactoryAgentSession):
            raise ContractError("Factory public transition requires an agent session")
        self._session = session

    @staticmethod
    def _design(response: HttpResponse) -> Mapping[str, Any]:
        if response.status != 200 or len(response.body) > MAX_RESPONSE_BYTES:
            raise AmbiguousEffectError(
                "authenticated Factory public readback was unavailable"
            )
        try:
            value = json.loads(response.body.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise AmbiguousEffectError(
                "authenticated Factory public readback was malformed"
            ) from exc
        if not isinstance(value, Mapping):
            raise AmbiguousEffectError(
                "authenticated Factory public readback was malformed"
            )
        return value

    @staticmethod
    def _receipt(design: Mapping[str, Any], draft: Receipt, owner_id: str) -> Receipt:
        try:
            receipt = Receipt.from_design(
                _design_with_normalized_currency(design),
                draft.packet_sha256,
                draft.artifact_sha256,
            )
            receipt.assert_owner(owner_id)
            for field in (
                "design_id",
                "slug",
                "root_id",
                "current_history_id",
                "project_url",
            ):
                if getattr(receipt, field) != getattr(draft, field):
                    raise ReceiptError(
                        "Factory public readback changed the exact draft identity"
                    )
            value = receipt.to_dict()
            value["details"] = {**dict(draft.details), **dict(receipt.details)}
            return Receipt.from_dict(value)
        except (ContractError, ReceiptError) as exc:
            raise AmbiguousEffectError(
                "Factory public readback did not identify the exact draft"
            ) from exc

    @staticmethod
    def _is_current_public(receipt: Receipt) -> bool:
        return (
            receipt.status == "public"
            and isinstance(receipt.current_history_id, str)
            and receipt.published_history_id == receipt.current_history_id
        )

    def publish(self, draft: Receipt) -> Receipt:
        if not isinstance(draft, Receipt) or not draft.is_verified_draft:
            raise ContractError(
                "Factory public transition requires a verified private draft Receipt"
            )
        identity = self._session.login()
        draft.assert_owner(identity.owner_id)
        door = ShopDoor(
            _PLACEHOLDER_TOKEN,
            transport=self._session.authenticated_transport,
        )

        before_response = door.get_design(draft.slug)
        before = self._receipt(self._design(before_response), draft, identity.owner_id)
        if self._is_current_public(before):
            return before
        if before.status != "draft" or before.published_history_id is not None:
            raise AmbiguousEffectError(
                "Factory preflight did not prove the exact private draft"
            )

        try:
            response = door.publish(draft.slug)
        except Exception as exc:
            response = None
            publish_error: Optional[Exception] = exc
        else:
            publish_error = None
            if response.status not in (200, 201):
                if response.status in PROVEN_NO_EFFECT_STATUSES:
                    raise PublishError(
                        "Factory rejected the public transition with HTTP %s"
                        % response.status
                    )
                publish_error = AmbiguousEffectError(
                    "Factory public transition returned an ambiguous status"
                )

        try:
            after_response = door.get_design(draft.slug)
            after = self._receipt(
                self._design(after_response), draft, identity.owner_id
            )
        except Exception as exc:
            raise AmbiguousEffectError(
                "Factory public transition lacks authenticated readback"
            ) from (publish_error or exc)
        if not self._is_current_public(after):
            raise AmbiguousEffectError(
                "Factory readback did not prove the current history public"
            ) from publish_error
        return after


__all__ = [
    "FactoryAgentCredentials",
    "FactoryAgentIdentity",
    "FactoryAgentInstructionsWriter",
    "FactoryAgentSession",
    "FactoryPublicTransition",
    "FactoryAuthenticationError",
    "FactoryCredentialRejected",
    "factory_credentials_from_environment",
]
