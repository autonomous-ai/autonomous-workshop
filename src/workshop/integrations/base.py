"""Compatibility import for the runtime-owned external-effect port.

An adapter is deliberately not a Workshop lifecycle concept.  It is simply
the implementation supplied to :class:`~workshop.runtime.effects.Runtime`
when work must cross a process or service boundary.
"""

from workshop.runtime import Adapter


__all__ = ["Adapter"]
