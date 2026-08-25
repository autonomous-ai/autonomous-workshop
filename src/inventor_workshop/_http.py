"""Shared stdlib-``urllib`` HTTP transport.

Extracted from the Shop Door (``shop.py``) so any Workshop integration that
calls an external HTTPS API — Shop, and now the real Concept image
providers — reads a bounded, non-redirecting response the same way: an
injectable ``Transport`` callable for tests, and a stdlib-only default that
refuses to follow a redirect (a bearer credential must never travel to a
different host than the caller pinned) and caps how many bytes it will read
into memory.

The response-size cap is a policy choice per integration, not a property of
an HTTP response in general, so it lives on the transport
(:func:`make_urllib_transport`) rather than on :class:`HttpResponse` itself.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Type

from .errors import ContractError


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes

    def __post_init__(self) -> None:
        if (
            not isinstance(self.status, int)
            or isinstance(self.status, bool)
            or not 100 <= self.status <= 599
        ):
            raise ContractError("HTTP response status must be an integer from 100 to 599")
        if not isinstance(self.headers, Mapping):
            raise ContractError("HTTP response headers must be a mapping")
        if not isinstance(self.body, bytes):
            raise ContractError("HTTP response body must be bytes")


Transport = Callable[[str, str, Mapping[str, str], Optional[bytes], int], HttpResponse]


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """A caller pins an exact origin; a redirect must never move a request
    (or the bearer credential on it) to a different host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def make_urllib_transport(
    max_response_bytes: int,
    *,
    oversize_error: Type[Exception] = ContractError,
) -> Transport:
    """Build a stdlib-``urllib`` transport capped at ``max_response_bytes``.

    ``oversize_error`` lets a caller preserve its own exception vocabulary
    (Shop Door raises its historical ``PublishError`` on an oversized
    response) while every other integration can accept the generic default.
    """

    if (
        not isinstance(max_response_bytes, int)
        or isinstance(max_response_bytes, bool)
        or max_response_bytes <= 0
    ):
        raise ContractError("transport max_response_bytes must be a positive integer")

    def transport(
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
                content = response.read(max_response_bytes + 1)
                if len(content) > max_response_bytes:
                    raise oversize_error(
                        "response exceeds the %d-byte limit" % max_response_bytes
                    )
                return HttpResponse(response.status, dict(response.headers), content)
        except urllib.error.HTTPError as exc:
            content = exc.read(max_response_bytes + 1)
            if len(content) > max_response_bytes:
                raise oversize_error(
                    "error response exceeds the %d-byte limit" % max_response_bytes
                )
            return HttpResponse(exc.code, dict(exc.headers or {}), content)

    return transport


__all__ = [
    "HttpResponse",
    "Transport",
    "make_urllib_transport",
]
