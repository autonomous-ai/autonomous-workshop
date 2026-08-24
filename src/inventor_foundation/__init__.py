"""Compatibility namespace for the former Foundation 0.2 package.

All behavior comes directly from :mod:`inventor_workshop`; no second runtime
or state authority exists here.
"""

from __future__ import annotations

import importlib
import sys

import inventor_workshop as _workshop
from inventor_workshop import *  # noqa: F401,F403
from inventor_workshop import __version__

__all__ = tuple(_workshop.__all__)

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
