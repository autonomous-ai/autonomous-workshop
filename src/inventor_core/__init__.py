"""Compatibility namespace for Workshop 0.1 integrations.

New inventor code imports :mod:`inventor_workshop`. This module is kept only
so existing runtimes can read and reconcile durable work while they migrate.
"""

from __future__ import annotations

import importlib
import sys

import inventor_workshop as _workshop
from inventor_workshop import *  # noqa: F401,F403
from inventor_workshop import __version__
from inventor_workshop.ports import DeliveryPort, LaunchPort
from .panda import PandaClient, PandaPublicationCoordinator
from .publishing import CatalogClient, PublicationCoordinator

FulfillmentPort = DeliveryPort
PublisherPort = LaunchPort

__all__ = tuple(_workshop.__all__) + (
    "CatalogClient",
    "FulfillmentPort",
    "PandaClient",
    "PandaPublicationCoordinator",
    "PublicationCoordinator",
    "PublisherPort",
)


_SUBMODULES = (
    "artifacts",
    "cad",
    "cad.contracts",
    "cli",
    "clockwork",
    "contribution",
    "creation",
    "doors",
    "errors",
    "inspection",
    "launch",
    "lifecycle",
    "make",
    "manifest",
    "models",
    "offline",
    "pack",
    "ports",
    "scaffold",
    "schemas",
    "send",
    "skills",
    "store",
    "taste",
    "workshop",
)
for _name in _SUBMODULES:
    _module = importlib.import_module("inventor_workshop.%s" % _name)
    sys.modules["%s.%s" % (__name__, _name)] = _module
    if "." not in _name:
        setattr(sys.modules[__name__], _name, _module)
