"""Compatibility aliases for abandoned enterprise-style launch names."""

from inventor_workshop.launch import (
    DEFAULT_PORTAL_API,
    HTTP_TIMEOUT_SECONDS,
    HttpResponse,
    Launchpad,
    Portal,
    Transport,
    inspect_publish_packet,
    urllib_transport,
)

DEFAULT_CATALOG_API = DEFAULT_PORTAL_API
CatalogClient = Portal
PublicationCoordinator = Launchpad

__all__ = [
    "CatalogClient",
    "DEFAULT_CATALOG_API",
    "HTTP_TIMEOUT_SECONDS",
    "HttpResponse",
    "PublicationCoordinator",
    "Transport",
    "inspect_publish_packet",
    "urllib_transport",
]
