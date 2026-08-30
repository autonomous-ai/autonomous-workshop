"""Compatibility facade for the Tier-3 Lantern Menagerie CAD project."""

from params import *  # noqa: F401,F403
from assemblies.product import make_assembly
from parts.reel import make_shadow_reel
from parts.shells import make_front_shell, make_rear_shell
from parts.stand import make_kickstand
from validation import parameter_audit

__all__ = [name for name in globals() if name.isupper()] + [
    "make_assembly",
    "make_front_shell",
    "make_kickstand",
    "make_rear_shell",
    "make_shadow_reel",
    "parameter_audit",
]
