"""Compatibility name for Bob's Workshop :mod:`harness.send` boundary.

New Bob code imports :mod:`harness.send`.  This module deliberately resolves
to that *same module object* so older operators and tests that monkeypatch a
network seam through ``harness.publish`` cannot create a second authority.
"""

from __future__ import annotations

import sys

from . import send as _send

sys.modules[__name__] = _send
