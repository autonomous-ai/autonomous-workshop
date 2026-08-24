"""Compatibility aliases for the legacy Panda-named launch API."""

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

DEFAULT_API = DEFAULT_PORTAL_API
PandaClient = Portal
PandaPublicationCoordinator = Launchpad

__all__ = [
    "DEFAULT_API",
    "HTTP_TIMEOUT_SECONDS",
    "HttpResponse",
    "PandaClient",
    "PandaPublicationCoordinator",
    "Transport",
    "inspect_publish_packet",
    "urllib_transport",
]
